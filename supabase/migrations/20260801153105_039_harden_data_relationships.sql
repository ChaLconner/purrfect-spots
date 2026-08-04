BEGIN;

-- The application writes through the FastAPI service-role boundary. Keep the
-- Data API read-only for client roles so a future RLS mistake cannot mutate
-- moderation, billing, quota, or role fields directly.
REVOKE INSERT, UPDATE, DELETE, TRUNCATE, REFERENCES, TRIGGER
ON ALL TABLES IN SCHEMA public
FROM anon, authenticated;

ALTER DEFAULT PRIVILEGES IN SCHEMA public
REVOKE INSERT, UPDATE, DELETE, TRUNCATE, REFERENCES, TRIGGER
ON TABLES
FROM anon, authenticated;

-- public.users contains credentials and billing/auth metadata. Public profile
-- discovery is served by the sanitized FastAPI endpoint, not the base table.
DROP POLICY IF EXISTS "Allow public user discovery" ON public.users;
DROP POLICY IF EXISTS users_select_own ON public.users;
CREATE POLICY users_select_own
ON public.users
FOR SELECT
TO authenticated
USING ((SELECT auth.uid()) = id);

REVOKE SELECT ON TABLE public.users FROM anon;
REVOKE ALL PRIVILEGES ON TABLE public.admin_comment_list FROM anon, authenticated;

-- Never expose pending/rejected/deleted moderation content through Data API or
-- Realtime. Child rows inherit the visibility of their parent photo.
DROP POLICY IF EXISTS "Public read non-deleted photos" ON public.cat_photos;
CREATE POLICY cat_photos_public_read_approved
ON public.cat_photos
FOR SELECT
TO public
USING (deleted_at IS NULL AND status = 'approved');

DROP POLICY IF EXISTS "Comments are public" ON public.photo_comments;
CREATE POLICY photo_comments_public_read_visible
ON public.photo_comments
FOR SELECT
TO public
USING (
    EXISTS (
        SELECT 1
        FROM public.cat_photos photo
        WHERE photo.id = photo_comments.photo_id
          AND photo.deleted_at IS NULL
          AND photo.status = 'approved'
    )
);

DROP POLICY IF EXISTS "Likes are public" ON public.photo_likes;
CREATE POLICY photo_likes_public_read_visible
ON public.photo_likes
FOR SELECT
TO public
USING (
    EXISTS (
        SELECT 1
        FROM public.cat_photos photo
        WHERE photo.id = photo_likes.photo_id
          AND photo.deleted_at IS NULL
          AND photo.status = 'approved'
    )
);

-- These routines are internal implementation details, not public RPCs.
REVOKE EXECUTE ON FUNCTION public.increment_usage(uuid, date) FROM PUBLIC, anon, authenticated;
REVOKE EXECUTE ON FUNCTION public.check_incident_sla_breaches() FROM PUBLIC, anon, authenticated;
REVOKE EXECUTE ON FUNCTION public.cat_photos_search_vector_trigger() FROM PUBLIC, anon, authenticated;
REVOKE EXECUTE ON FUNCTION public.sync_cat_photos_location() FROM PUBLIC, anon, authenticated;
REVOKE EXECUTE ON FUNCTION public.trg_cat_photos_update_location() FROM PUBLIC, anon, authenticated;
REVOKE EXECUTE ON FUNCTION public.update_comments_count() FROM PUBLIC, anon, authenticated;
REVOKE EXECUTE ON FUNCTION public.update_incident_sla_status() FROM PUBLIC, anon, authenticated;
REVOKE EXECUTE ON FUNCTION public.update_likes_count() FROM PUBLIC, anon, authenticated;
REVOKE EXECUTE ON FUNCTION public.update_updated_at_column() FROM PUBLIC, anon, authenticated;
REVOKE EXECUTE ON FUNCTION public.users_search_vector_trigger() FROM PUBLIC, anon, authenticated;

GRANT EXECUTE ON FUNCTION public.increment_usage(uuid, date) TO service_role;
GRANT EXECUTE ON FUNCTION public.check_incident_sla_breaches() TO service_role;

-- Make latent business invariants enforceable at the database boundary.
ALTER TABLE public.users
    ALTER COLUMN treat_balance SET DEFAULT 0,
    ALTER COLUMN treat_balance SET NOT NULL,
    ALTER COLUMN total_treats_received SET DEFAULT 0,
    ALTER COLUMN total_treats_received SET NOT NULL,
    ALTER COLUMN total_treats_given SET DEFAULT 0,
    ALTER COLUMN total_treats_given SET NOT NULL,
    ADD CONSTRAINT users_treat_balance_nonnegative CHECK (treat_balance >= 0),
    ADD CONSTRAINT users_total_treats_received_nonnegative CHECK (total_treats_received >= 0),
    ADD CONSTRAINT users_total_treats_given_nonnegative CHECK (total_treats_given >= 0);

ALTER TABLE public.cat_photos
    ALTER COLUMN user_id SET NOT NULL,
    ALTER COLUMN status SET DEFAULT 'approved',
    ALTER COLUMN status SET NOT NULL,
    ALTER COLUMN likes_count SET DEFAULT 0,
    ALTER COLUMN likes_count SET NOT NULL,
    ALTER COLUMN comments_count SET DEFAULT 0,
    ALTER COLUMN comments_count SET NOT NULL,
    ADD CONSTRAINT cat_photos_status_valid CHECK (status IN ('pending', 'approved', 'rejected')),
    ADD CONSTRAINT cat_photos_likes_count_nonnegative CHECK (likes_count >= 0),
    ADD CONSTRAINT cat_photos_comments_count_nonnegative CHECK (comments_count >= 0),
    ADD CONSTRAINT cat_photos_image_url_not_blank CHECK (btrim(image_url) <> ''),
    ADD CONSTRAINT cat_photos_coordinates_valid CHECK (
        (latitude IS NULL AND longitude IS NULL)
        OR (
            latitude IS NOT NULL
            AND longitude IS NOT NULL
            AND
            latitude BETWEEN -90 AND 90
            AND longitude BETWEEN -180 AND 180
        )
    );

ALTER TABLE public.photo_comments
    ALTER COLUMN user_id SET NOT NULL,
    ALTER COLUMN photo_id SET NOT NULL,
    DROP CONSTRAINT photo_comments_content_check,
    ADD CONSTRAINT photo_comments_content_check CHECK (btrim(content) <> '');

ALTER TABLE public.saved_spots
    ALTER COLUMN user_id SET NOT NULL,
    ALTER COLUMN photo_id SET NOT NULL;

ALTER TABLE public.email_verifications
    ALTER COLUMN attempts SET DEFAULT 0,
    ALTER COLUMN attempts SET NOT NULL,
    ALTER COLUMN max_attempts SET DEFAULT 5,
    ALTER COLUMN max_attempts SET NOT NULL,
    DROP CONSTRAINT email_verifications_attempts_check,
    ADD CONSTRAINT email_verifications_attempts_check
        CHECK (attempts >= 0 AND max_attempts > 0 AND attempts <= max_attempts);

ALTER TABLE public.treats_transactions
    ADD CONSTRAINT treats_transactions_amount_positive CHECK (amount > 0);

ALTER TABLE public.reports
    ALTER COLUMN status SET DEFAULT 'pending',
    ALTER COLUMN status SET NOT NULL,
    ADD CONSTRAINT reports_reason_not_blank CHECK (btrim(reason) <> ''),
    ADD CONSTRAINT reports_resolution_consistent CHECK (
        (status = 'pending' AND resolved_at IS NULL AND resolved_by IS NULL)
        OR (status IN ('resolved', 'dismissed') AND resolved_at IS NOT NULL)
    );

-- If a report targets a comment, its photo_id must identify that comment's
-- parent photo. This prevents contradictory moderation records.
ALTER TABLE public.photo_comments
    ADD CONSTRAINT photo_comments_id_photo_id_key UNIQUE (id, photo_id);

ALTER TABLE public.reports
    DROP CONSTRAINT reports_comment_id_fkey,
    ADD CONSTRAINT reports_comment_photo_fkey
        FOREIGN KEY (comment_id, photo_id)
        REFERENCES public.photo_comments (id, photo_id)
        ON DELETE CASCADE;

CREATE UNIQUE INDEX reports_one_pending_photo_per_reporter
ON public.reports (reporter_id, photo_id)
WHERE status = 'pending' AND reporter_id IS NOT NULL AND comment_id IS NULL;

CREATE UNIQUE INDEX reports_one_pending_comment_per_reporter
ON public.reports (reporter_id, comment_id)
WHERE status = 'pending' AND reporter_id IS NOT NULL AND comment_id IS NOT NULL;

-- Replace two competing coordinate triggers with one null-safe source of truth.
DROP TRIGGER IF EXISTS set_cat_photos_location ON public.cat_photos;
DROP FUNCTION IF EXISTS public.trg_cat_photos_update_location();

CREATE OR REPLACE FUNCTION public.sync_cat_photos_location()
RETURNS trigger
LANGUAGE plpgsql
SET search_path = public, extensions, pg_temp
AS $$
BEGIN
    IF NEW.latitude IS NULL AND NEW.longitude IS NULL THEN
        NEW.location := NULL;
    ELSIF NEW.latitude IS NOT NULL AND NEW.longitude IS NOT NULL THEN
        NEW.location := extensions.ST_SetSRID(
            extensions.ST_MakePoint(NEW.longitude, NEW.latitude),
            4326
        )::geography;
    END IF;
    RETURN NEW;
END;
$$;

REVOKE EXECUTE ON FUNCTION public.sync_cat_photos_location() FROM PUBLIC, anon, authenticated;
GRANT EXECUTE ON FUNCTION public.sync_cat_photos_location() TO service_role;

CREATE OR REPLACE FUNCTION public.update_comments_count()
RETURNS trigger
LANGUAGE plpgsql
SET search_path = public, pg_temp
AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        UPDATE public.cat_photos
        SET comments_count = COALESCE(comments_count, 0) + 1
        WHERE id = NEW.photo_id;
        RETURN NEW;
    ELSIF TG_OP = 'DELETE' THEN
        UPDATE public.cat_photos
        SET comments_count = GREATEST(COALESCE(comments_count, 0) - 1, 0)
        WHERE id = OLD.photo_id;
        RETURN OLD;
    END IF;
    RETURN NULL;
END;
$$;

REVOKE EXECUTE ON FUNCTION public.update_comments_count() FROM PUBLIC, anon, authenticated;
GRANT EXECUTE ON FUNCTION public.update_comments_count() TO service_role;

CREATE OR REPLACE FUNCTION public.update_photo_likes_count()
RETURNS trigger
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public, pg_temp
AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        UPDATE public.cat_photos
        SET likes_count = COALESCE(likes_count, 0) + 1
        WHERE id = NEW.photo_id;
        RETURN NEW;
    ELSIF TG_OP = 'DELETE' THEN
        UPDATE public.cat_photos
        SET likes_count = GREATEST(COALESCE(likes_count, 0) - 1, 0)
        WHERE id = OLD.photo_id;
        RETURN OLD;
    END IF;
    RETURN NULL;
END;
$$;

REVOKE EXECUTE ON FUNCTION public.update_photo_likes_count() FROM PUBLIC, anon, authenticated;
GRANT EXECUTE ON FUNCTION public.update_photo_likes_count() TO service_role;

-- Service-only RPC: validate both accounts and visible content, then lock users
-- in deterministic order to avoid reciprocal-transfer deadlocks.
CREATE OR REPLACE FUNCTION public.give_treat_atomic(
    p_from_user_id uuid,
    p_photo_id uuid,
    p_amount integer
)
RETURNS json
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public, extensions, pg_temp
AS $$
DECLARE
    v_to_user_id uuid;
    v_sender_balance integer;
    v_sender_banned timestamptz;
    v_sender_deleted timestamptz;
    v_receiver_banned timestamptz;
    v_receiver_deleted timestamptz;
BEGIN
    IF p_amount <= 0 THEN
        RETURN json_build_object('success', false, 'error', 'Amount must be greater than zero');
    END IF;

    SELECT photo.user_id
    INTO v_to_user_id
    FROM public.cat_photos photo
    WHERE photo.id = p_photo_id
      AND photo.deleted_at IS NULL
      AND photo.status = 'approved';

    IF v_to_user_id IS NULL THEN
        RETURN json_build_object('success', false, 'error', 'Photo not found or unavailable');
    END IF;

    IF p_from_user_id = v_to_user_id THEN
        RETURN json_build_object('success', false, 'error', 'Cannot give treats to yourself');
    END IF;

    PERFORM 1
    FROM public.users account
    WHERE account.id IN (p_from_user_id, v_to_user_id)
    ORDER BY account.id
    FOR UPDATE;

    SELECT account.treat_balance, account.banned_at, account.deleted_at
    INTO v_sender_balance, v_sender_banned, v_sender_deleted
    FROM public.users account
    WHERE account.id = p_from_user_id;

    IF v_sender_balance IS NULL THEN
        RETURN json_build_object('success', false, 'error', 'Sender user not found');
    END IF;
    IF v_sender_banned IS NOT NULL OR v_sender_deleted IS NOT NULL THEN
        RETURN json_build_object('success', false, 'error', 'Sender account is inactive or banned');
    END IF;
    IF v_sender_balance < p_amount THEN
        RETURN json_build_object('success', false, 'error', 'Insufficient treats balance');
    END IF;

    SELECT account.banned_at, account.deleted_at
    INTO v_receiver_banned, v_receiver_deleted
    FROM public.users account
    WHERE account.id = v_to_user_id;

    IF NOT FOUND THEN
        RETURN json_build_object('success', false, 'error', 'Receiver user not found');
    END IF;
    IF v_receiver_banned IS NOT NULL OR v_receiver_deleted IS NOT NULL THEN
        RETURN json_build_object('success', false, 'error', 'Receiver account is inactive or banned');
    END IF;

    UPDATE public.users
    SET treat_balance = treat_balance - p_amount,
        total_treats_given = total_treats_given + p_amount,
        updated_at = now()
    WHERE id = p_from_user_id;

    UPDATE public.users
    SET treat_balance = treat_balance + p_amount,
        total_treats_received = total_treats_received + p_amount,
        updated_at = now()
    WHERE id = v_to_user_id;

    INSERT INTO public.treats_transactions (
        from_user_id, to_user_id, photo_id, amount, transaction_type, description
    ) VALUES (
        p_from_user_id, v_to_user_id, p_photo_id, p_amount, 'give', 'Gave treats to photo'
    );

    RETURN json_build_object(
        'success', true,
        'new_balance', v_sender_balance - p_amount,
        'to_user_id', v_to_user_id
    );
END;
$$;

REVOKE ALL ON FUNCTION public.give_treat_atomic(uuid, uuid, integer) FROM PUBLIC, anon, authenticated;
GRANT EXECUTE ON FUNCTION public.give_treat_atomic(uuid, uuid, integer) TO service_role;

CREATE OR REPLACE FUNCTION public.purchase_treats_atomic(
    p_user_id uuid,
    p_amount integer,
    p_description text,
    p_stripe_session_id text
)
RETURNS json
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public, pg_temp
AS $$
DECLARE
    v_new_balance integer;
    v_transaction_id uuid;
    v_banned_at timestamptz;
    v_deleted_at timestamptz;
BEGIN
    IF p_amount <= 0 THEN
        RETURN json_build_object('success', false, 'error', 'Amount must be greater than zero');
    END IF;
    IF p_stripe_session_id IS NULL OR btrim(p_stripe_session_id) = '' THEN
        RETURN json_build_object('success', false, 'error', 'Stripe session ID is required');
    END IF;

    SELECT account.banned_at, account.deleted_at
    INTO v_banned_at, v_deleted_at
    FROM public.users account
    WHERE account.id = p_user_id
    FOR UPDATE;

    IF NOT FOUND THEN
        RETURN json_build_object('success', false, 'error', 'User not found');
    END IF;
    IF v_banned_at IS NOT NULL OR v_deleted_at IS NOT NULL THEN
        RETURN json_build_object('success', false, 'error', 'User account is inactive or banned');
    END IF;

    INSERT INTO public.treats_transactions (
        to_user_id, amount, transaction_type, description, stripe_session_id
    ) VALUES (
        p_user_id, p_amount, 'purchase', p_description, p_stripe_session_id
    )
    ON CONFLICT (stripe_session_id) DO NOTHING
    RETURNING id INTO v_transaction_id;

    IF v_transaction_id IS NULL THEN
        RETURN json_build_object('success', true, 'message', 'Transaction already processed', 'duplicate', true);
    END IF;

    UPDATE public.users
    SET treat_balance = treat_balance + p_amount,
        updated_at = now()
    WHERE id = p_user_id
    RETURNING treat_balance INTO v_new_balance;

    RETURN json_build_object('success', true, 'new_balance', v_new_balance, 'duplicate', false);
EXCEPTION WHEN OTHERS THEN
    RETURN json_build_object('success', false, 'error', SQLERRM);
END;
$$;

REVOKE ALL ON FUNCTION public.purchase_treats_atomic(uuid, integer, text, text) FROM PUBLIC, anon, authenticated;
GRANT EXECUTE ON FUNCTION public.purchase_treats_atomic(uuid, integer, text, text) TO service_role;

COMMIT;
