
-- 1. Improve toggle_photo_like to use INSERT ON CONFLICT for atomicity
CREATE OR REPLACE FUNCTION public.toggle_photo_like(p_user_id uuid, p_photo_id uuid)
 RETURNS TABLE(liked boolean, likes_count integer)
 LANGUAGE plpgsql
 SECURITY DEFINER
AS $function$
DECLARE
    v_photo_exists BOOLEAN;
    v_row_count INTEGER;
    v_new_count INTEGER;
BEGIN
    -- Check if photo exists
    SELECT EXISTS(
        SELECT 1 FROM cat_photos 
        WHERE id = p_photo_id AND deleted_at IS NULL
    ) INTO v_photo_exists;
    
    IF NOT v_photo_exists THEN
        RAISE EXCEPTION 'Photo not found' USING ERRCODE = 'P0002';
    END IF;
    
    -- Atomic attempt: try to INSERT, ON CONFLICT means already liked
    INSERT INTO photo_likes (user_id, photo_id)
    VALUES (p_user_id, p_photo_id)
    ON CONFLICT (user_id, photo_id) DO NOTHING;
    
    GET DIAGNOSTICS v_row_count = ROW_COUNT;
    
    IF v_row_count = 0 THEN
        -- Already liked → unlike (delete)
        DELETE FROM photo_likes 
        WHERE user_id = p_user_id AND photo_id = p_photo_id;
        
        liked := FALSE;
    ELSE
        -- Successfully inserted → liked
        liked := TRUE;
    END IF;
    
    -- Get updated count (trigger has already fired)
    SELECT cp.likes_count INTO v_new_count
    FROM cat_photos cp
    WHERE cp.id = p_photo_id;
    
    likes_count := COALESCE(v_new_count, 0);
    
    RETURN NEXT;
END;
$function$;

-- 2. Harden update_likes_count trigger to prevent negative counts
CREATE OR REPLACE FUNCTION public.update_likes_count()
 RETURNS trigger
 LANGUAGE plpgsql
AS $function$
BEGIN
    IF (TG_OP = 'INSERT') THEN
        UPDATE cat_photos SET likes_count = likes_count + 1 WHERE id = NEW.photo_id;
        RETURN NEW;
    ELSIF (TG_OP = 'DELETE') THEN
        UPDATE cat_photos SET likes_count = GREATEST(0, likes_count - 1) WHERE id = OLD.photo_id;
        RETURN OLD;
    END IF;
    RETURN NULL;
END;
$function$;

COMMENT ON FUNCTION toggle_photo_like IS 'Atomically toggle like status using INSERT ON CONFLICT pattern to prevent race conditions';
COMMENT ON FUNCTION update_likes_count IS 'Trigger function to maintain denormalized likes_count with GREATEST(0) safety';

