
-- Create atomic toggle_like function to prevent race conditions
CREATE OR REPLACE FUNCTION public.toggle_photo_like(
    p_user_id UUID,
    p_photo_id UUID
)
RETURNS TABLE (
    liked BOOLEAN,
    likes_count INTEGER
)
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
    v_photo_exists BOOLEAN;
    v_already_liked BOOLEAN;
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
    
    -- Check if already liked
    SELECT EXISTS(
        SELECT 1 FROM photo_likes 
        WHERE user_id = p_user_id AND photo_id = p_photo_id
    ) INTO v_already_liked;
    
    IF v_already_liked THEN
        -- Unlike: Delete the like (trigger will handle count)
        DELETE FROM photo_likes 
        WHERE user_id = p_user_id AND photo_id = p_photo_id;
        
        liked := FALSE;
    ELSE
        -- Like: Insert the like (trigger will handle count)
        INSERT INTO photo_likes (user_id, photo_id)
        VALUES (p_user_id, p_photo_id);
        
        liked := TRUE;
    END IF;
    
    -- Get updated count
    SELECT cp.likes_count INTO v_new_count
    FROM cat_photos cp
    WHERE cp.id = p_photo_id;
    
    likes_count := COALESCE(v_new_count, 0);
    
    RETURN NEXT;
END;
$$;

-- Grant execute permission to authenticated users
GRANT EXECUTE ON FUNCTION public.toggle_photo_like(UUID, UUID) TO authenticated;
GRANT EXECUTE ON FUNCTION public.toggle_photo_like(UUID, UUID) TO service_role;

-- Add comment for documentation
COMMENT ON FUNCTION public.toggle_photo_like IS 'Atomically toggles a like on a photo. Returns the new liked status and updated count.';

