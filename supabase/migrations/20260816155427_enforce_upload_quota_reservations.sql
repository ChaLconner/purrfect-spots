-- Serialize upload admission across workers and keep expensive processing inside
-- an authoritative quota reservation window.

CREATE TABLE IF NOT EXISTS public.upload_quota_reservations (
    reservation_id UUID PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    status TEXT NOT NULL DEFAULT 'reserved'
        CHECK (status IN ('reserved', 'consumed', 'released')),
    expires_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp(),
    consumed_at TIMESTAMPTZ,
    released_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_upload_quota_reservations_active_expiry
    ON public.upload_quota_reservations (expires_at)
    WHERE status = 'reserved';

CREATE INDEX IF NOT EXISTS idx_upload_quota_reservations_user_active
    ON public.upload_quota_reservations (user_id, expires_at)
    WHERE status = 'reserved';

ALTER TABLE public.upload_quota_reservations ENABLE ROW LEVEL SECURITY;
CREATE POLICY upload_quota_reservations_service_role_only
    ON public.upload_quota_reservations
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);
REVOKE ALL ON TABLE public.upload_quota_reservations FROM PUBLIC, anon, authenticated;
GRANT ALL ON TABLE public.upload_quota_reservations TO service_role;

CREATE OR REPLACE FUNCTION public.reserve_upload_quota(
    p_reservation_id UUID,
    p_user_id UUID,
    p_user_limit INTEGER,
    p_global_limit INTEGER,
    p_expires_at TIMESTAMPTZ
)
RETURNS BOOLEAN
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = ''
AS $$
DECLARE
    v_now TIMESTAMPTZ := clock_timestamp();
    v_system_total INTEGER := 0;
    v_active_reservations INTEGER := 0;
    v_user_uploads INTEGER := 0;
    v_user_reservations INTEGER := 0;
    v_inserted INTEGER := 0;
BEGIN
    IF p_reservation_id IS NULL
       OR p_user_id IS NULL
       OR p_user_limit <= 0
       OR p_global_limit <= 0
       OR p_expires_at <= v_now
       OR p_expires_at > v_now + INTERVAL '1 hour' THEN
        RETURN FALSE;
    END IF;

    -- This row lock serializes every admission decision, including global and
    -- per-user reservations, across all API workers.
    INSERT INTO public.system_daily_stats (date, total_uploads)
    VALUES (CURRENT_DATE, 0)
    ON CONFLICT (date) DO NOTHING;

    SELECT COALESCE(s.total_uploads, 0)
    INTO v_system_total
    FROM public.system_daily_stats AS s
    WHERE s.date = CURRENT_DATE
    FOR UPDATE;

    DELETE FROM public.upload_quota_reservations AS r
    WHERE r.status = 'reserved'
      AND r.expires_at <= v_now;

    SELECT count(*)::INTEGER
    INTO v_active_reservations
    FROM public.upload_quota_reservations AS r
    WHERE r.status = 'reserved'
      AND r.expires_at > v_now;

    IF v_system_total + v_active_reservations >= p_global_limit THEN
        RETURN FALSE;
    END IF;

    SELECT count(*)::INTEGER
    INTO v_user_uploads
    FROM public.cat_photos AS p
    WHERE p.user_id = p_user_id
      AND p.deleted_at IS NULL
      AND p.uploaded_at > v_now - INTERVAL '24 hours';

    SELECT count(*)::INTEGER
    INTO v_user_reservations
    FROM public.upload_quota_reservations AS r
    WHERE r.user_id = p_user_id
      AND r.status = 'reserved'
      AND r.expires_at > v_now;

    IF v_user_uploads + v_user_reservations >= p_user_limit THEN
        RETURN FALSE;
    END IF;

    INSERT INTO public.upload_quota_reservations (reservation_id, user_id, expires_at)
    VALUES (p_reservation_id, p_user_id, p_expires_at)
    ON CONFLICT (reservation_id) DO NOTHING;

    GET DIAGNOSTICS v_inserted = ROW_COUNT;
    RETURN v_inserted = 1;
END;
$$;

CREATE OR REPLACE FUNCTION public.complete_upload_quota(p_reservation_id UUID)
RETURNS BOOLEAN
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = ''
AS $$
DECLARE
    v_updated INTEGER := 0;
BEGIN
    -- Completion is allowed after the nominal expiry because the upload row
    -- has already been persisted and the database trigger owns the real count.
    UPDATE public.upload_quota_reservations
    SET status = 'consumed', consumed_at = clock_timestamp()
    WHERE reservation_id = p_reservation_id
      AND status = 'reserved';

    GET DIAGNOSTICS v_updated = ROW_COUNT;
    RETURN v_updated = 1;
END;
$$;

CREATE OR REPLACE FUNCTION public.renew_upload_quota(
    p_reservation_id UUID,
    p_expires_at TIMESTAMPTZ
)
RETURNS BOOLEAN
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = ''
AS $$
DECLARE
    v_updated INTEGER := 0;
BEGIN
    IF p_expires_at <= clock_timestamp()
       OR p_expires_at > clock_timestamp() + INTERVAL '1 hour' THEN
        RETURN FALSE;
    END IF;

    UPDATE public.upload_quota_reservations
    SET expires_at = p_expires_at
    WHERE reservation_id = p_reservation_id
      AND status = 'reserved'
      AND expires_at > clock_timestamp();

    GET DIAGNOSTICS v_updated = ROW_COUNT;
    RETURN v_updated = 1;
END;
$$;

CREATE OR REPLACE FUNCTION public.release_upload_quota(p_reservation_id UUID)
RETURNS BOOLEAN
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = ''
AS $$
DECLARE
    v_updated INTEGER := 0;
BEGIN
    UPDATE public.upload_quota_reservations
    SET status = 'released', released_at = clock_timestamp()
    WHERE reservation_id = p_reservation_id
      AND status = 'reserved';

    GET DIAGNOSTICS v_updated = ROW_COUNT;
    RETURN v_updated = 1;
END;
$$;

-- system_daily_stats.total_uploads is maintained by the cat_photos trigger.
-- Keep this legacy analytics RPC from incrementing the same counter twice.
-- The deployed function historically returned INTEGER, so drop the old
-- signature before recreating it as a VOID service-role RPC.
DROP FUNCTION IF EXISTS public.increment_usage(uuid, date);

CREATE OR REPLACE FUNCTION public.increment_usage(p_user_id UUID, p_date DATE)
RETURNS VOID
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = ''
AS $$
BEGIN
    INSERT INTO public.user_daily_quotas (user_id, date, upload_count)
    VALUES (p_user_id, p_date, 1)
    ON CONFLICT (user_id, date) DO UPDATE
    SET upload_count = public.user_daily_quotas.upload_count + 1;
END;
$$;

REVOKE EXECUTE ON FUNCTION public.reserve_upload_quota(uuid, uuid, integer, integer, timestamptz)
    FROM PUBLIC, anon, authenticated;
REVOKE EXECUTE ON FUNCTION public.complete_upload_quota(uuid)
    FROM PUBLIC, anon, authenticated;
REVOKE EXECUTE ON FUNCTION public.renew_upload_quota(uuid, timestamptz)
    FROM PUBLIC, anon, authenticated;
REVOKE EXECUTE ON FUNCTION public.release_upload_quota(uuid)
    FROM PUBLIC, anon, authenticated;
REVOKE EXECUTE ON FUNCTION public.increment_usage(uuid, date)
    FROM PUBLIC, anon, authenticated;

GRANT EXECUTE ON FUNCTION public.reserve_upload_quota(uuid, uuid, integer, integer, timestamptz)
    TO service_role;
GRANT EXECUTE ON FUNCTION public.complete_upload_quota(uuid)
    TO service_role;
GRANT EXECUTE ON FUNCTION public.renew_upload_quota(uuid, timestamptz)
    TO service_role;
GRANT EXECUTE ON FUNCTION public.release_upload_quota(uuid)
    TO service_role;
GRANT EXECUTE ON FUNCTION public.increment_usage(uuid, date)
    TO service_role;
