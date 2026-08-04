-- Migration 037: Fix Live Database Schema Issues
-- 1. Standardize account_deletion_requests FK to public.users(id)
ALTER TABLE public.account_deletion_requests
  DROP CONSTRAINT IF EXISTS account_deletion_requests_user_id_fkey;

ALTER TABLE public.account_deletion_requests
  ADD CONSTRAINT account_deletion_requests_user_id_fkey
  FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;

-- 2. GIST Index & Location Trigger for cat_photos PostGIS spatial queries
CREATE INDEX IF NOT EXISTS idx_cat_photos_location_gist 
  ON public.cat_photos USING GIST (location);

-- Function and trigger to keep location updated from latitude/longitude
CREATE OR REPLACE FUNCTION trg_cat_photos_update_location()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.latitude IS NOT NULL AND NEW.longitude IS NOT NULL THEN
        NEW.location := ST_SetSRID(ST_MakePoint(NEW.longitude::double precision, NEW.latitude::double precision), 4326)::geography;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS set_cat_photos_location ON public.cat_photos;
CREATE TRIGGER set_cat_photos_location
    BEFORE INSERT OR UPDATE OF latitude, longitude ON public.cat_photos
    FOR EACH ROW
    EXECUTE FUNCTION trg_cat_photos_update_location();

-- Backfill existing NULL location rows
UPDATE public.cat_photos
SET location = ST_SetSRID(ST_MakePoint(longitude::double precision, latitude::double precision), 4326)::geography
WHERE location IS NULL AND latitude IS NOT NULL AND longitude IS NOT NULL;

-- 3. Optimize search_nearby_photos using p.location PostGIS geography column
CREATE OR REPLACE FUNCTION search_nearby_photos(
    lat DOUBLE PRECISION,
    lng DOUBLE PRECISION,
    radius_meters DOUBLE PRECISION,
    result_limit INTEGER DEFAULT 50
)
RETURNS TABLE (
    id UUID,
    user_id UUID,
    image_url TEXT,
    location_name TEXT,
    description TEXT,
    latitude DOUBLE PRECISION,
    longitude DOUBLE PRECISION,
    uploaded_at TIMESTAMPTZ,
    tags TEXT[],
    distance_meters DOUBLE PRECISION
) AS $$
DECLARE
    search_geo GEOGRAPHY;
BEGIN
    search_geo := ST_SetSRID(ST_MakePoint(lng, lat), 4326)::geography;
    
    RETURN QUERY
    SELECT 
        p.id,
        p.user_id,
        p.image_url,
        p.location_name,
        p.description,
        p.latitude,
        p.longitude,
        p.uploaded_at,
        p.tags,
        ST_Distance(
            COALESCE(p.location, ST_SetSRID(ST_MakePoint(p.longitude::double precision, p.latitude::double precision), 4326)::geography),
            search_geo
        ) as distance_meters
    FROM cat_photos p
    WHERE p.deleted_at IS NULL
      AND ST_DWithin(
            COALESCE(p.location, ST_SetSRID(ST_MakePoint(p.longitude::double precision, p.latitude::double precision), 4326)::geography),
            search_geo,
            radius_meters
        )
    ORDER BY distance_meters ASC, p.uploaded_at DESC
    LIMIT result_limit;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- 4. User status validation guard on give_treat_atomic RPC
-- Keeps the 3-param signature expected by the backend service, returns JSON
-- with success/error/to_user_id/new_balance, and adds banned/deleted guards.
CREATE OR REPLACE FUNCTION give_treat_atomic(
    p_from_user_id UUID,
    p_photo_id UUID,
    p_amount INTEGER DEFAULT 1
)
RETURNS JSON AS $$
DECLARE
    v_to_user_id UUID;
    v_sender_balance INTEGER;
    v_sender_banned TIMESTAMPTZ;
    v_sender_deleted TIMESTAMPTZ;
    v_receiver_banned TIMESTAMPTZ;
    v_receiver_deleted TIMESTAMPTZ;
BEGIN
    IF p_amount <= 0 THEN
        RETURN json_build_object('success', false, 'error', 'Amount must be greater than zero');
    END IF;

    -- Resolve photo owner
    SELECT user_id INTO v_to_user_id FROM public.cat_photos WHERE id = p_photo_id;
    IF v_to_user_id IS NULL THEN
        RETURN json_build_object('success', false, 'error', 'Photo not found');
    END IF;

    -- Self-treat guard
    IF p_from_user_id = v_to_user_id THEN
        RETURN json_build_object('success', false, 'error', 'Cannot give treats to yourself');
    END IF;

    -- Check sender status and balance
    SELECT treat_balance, banned_at, deleted_at
    INTO v_sender_balance, v_sender_banned, v_sender_deleted
    FROM public.users
    WHERE id = p_from_user_id FOR UPDATE;

    IF v_sender_balance IS NULL THEN
        RETURN json_build_object('success', false, 'error', 'Sender user not found');
    END IF;

    IF v_sender_banned IS NOT NULL OR v_sender_deleted IS NOT NULL THEN
        RETURN json_build_object('success', false, 'error', 'Sender account is inactive or banned');
    END IF;

    IF v_sender_balance < p_amount THEN
        RETURN json_build_object('success', false, 'error', 'Insufficient treats balance');
    END IF;

    -- Check receiver status
    SELECT banned_at, deleted_at
    INTO v_receiver_banned, v_receiver_deleted
    FROM public.users
    WHERE id = v_to_user_id FOR UPDATE;

    IF v_receiver_banned IS NOT NULL OR v_receiver_deleted IS NOT NULL THEN
        RETURN json_build_object('success', false, 'error', 'Receiver account is inactive or banned');
    END IF;

    -- Deduct sender balance & update stats
    UPDATE public.users
    SET treat_balance = treat_balance - p_amount,
        total_treats_given = COALESCE(total_treats_given, 0) + p_amount,
        updated_at = NOW()
    WHERE id = p_from_user_id;

    -- Add receiver balance & update stats
    UPDATE public.users
    SET treat_balance = treat_balance + p_amount,
        total_treats_received = COALESCE(total_treats_received, 0) + p_amount,
        updated_at = NOW()
    WHERE id = v_to_user_id;

    -- Record transaction
    INSERT INTO public.treats_transactions (
        from_user_id,
        to_user_id,
        photo_id,
        amount,
        transaction_type,
        description
    ) VALUES (
        p_from_user_id,
        v_to_user_id,
        p_photo_id,
        p_amount,
        'give',
        'Gave treats to photo'
    );

    RETURN json_build_object(
        'success', true,
        'new_balance', v_sender_balance - p_amount,
        'to_user_id', v_to_user_id
    );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;
