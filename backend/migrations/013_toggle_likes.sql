-- Migration: Add toggle_photo_like function and supporting structures

-- 1. Create photo_likes table if it doesn't exist
CREATE TABLE IF NOT EXISTS photo_likes (
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    photo_id UUID NOT NULL REFERENCES cat_photos(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    PRIMARY KEY (user_id, photo_id)
);

-- 2. Add likes_count column to cat_photos if it doesn't exist
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'cat_photos' AND column_name = 'likes_count') THEN
        ALTER TABLE cat_photos ADD COLUMN likes_count INTEGER DEFAULT 0;
    END IF;
END $$;

-- 3. Create trigger function to maintain likes_count
CREATE OR REPLACE FUNCTION update_photo_likes_count()
RETURNS TRIGGER AS $$
BEGIN
    IF (TG_OP = 'INSERT') THEN
        UPDATE cat_photos
        SET likes_count = likes_count + 1
        WHERE id = NEW.photo_id;
        RETURN NEW;
    ELSIF (TG_OP = 'DELETE') THEN
        UPDATE cat_photos
        SET likes_count = GREATEST(likes_count - 1, 0)
        WHERE id = OLD.photo_id;
        RETURN OLD;
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- 4. Create trigger
DROP TRIGGER IF EXISTS trg_update_photo_likes_count ON photo_likes;
CREATE TRIGGER trg_update_photo_likes_count
AFTER INSERT OR DELETE ON photo_likes
FOR EACH ROW
EXECUTE FUNCTION update_photo_likes_count();

-- 5. Create the toggle_photo_like function
CREATE OR REPLACE FUNCTION toggle_photo_like(
    p_user_id UUID,
    p_photo_id UUID
)
RETURNS TABLE (
    liked BOOLEAN,
    likes_count INTEGER
) AS $$
DECLARE
    v_exists BOOLEAN;
    v_liked BOOLEAN;
    v_new_count INTEGER;
BEGIN
    -- Check if photo exists
    IF NOT EXISTS (SELECT 1 FROM cat_photos WHERE id = p_photo_id) THEN
        RAISE EXCEPTION 'Photo not found';
    END IF;

    -- Check if user already liked the photo
    SELECT EXISTS (
        SELECT 1 FROM photo_likes
        WHERE user_id = p_user_id AND photo_id = p_photo_id
    ) INTO v_exists;

    IF v_exists THEN
        -- Unlike
        DELETE FROM photo_likes
        WHERE user_id = p_user_id AND photo_id = p_photo_id;
        v_liked := FALSE;
    ELSE
        -- Like
        INSERT INTO photo_likes (user_id, photo_id)
        VALUES (p_user_id, p_photo_id);
        v_liked := TRUE;
    END IF;

    -- Get updated count
    SELECT c.likes_count INTO v_new_count
    FROM cat_photos c
    WHERE id = p_photo_id;

    RETURN QUERY SELECT v_liked, v_new_count;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- 6. Sync existing likes count (optional, but good for consistency)
UPDATE cat_photos p
SET likes_count = (
    SELECT COUNT(*) 
    FROM photo_likes l 
    WHERE l.photo_id = p.id
);
