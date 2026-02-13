-- Migration: Add database trigger for Like notifications
-- This moves notification logic to the database for atomicity and performance

-- 1. Create the trigger function
CREATE OR REPLACE FUNCTION notify_on_photo_like()
RETURNS TRIGGER AS $$
DECLARE
    v_owner_id UUID;
    v_actor_name TEXT;
    v_location_name TEXT;
    v_existing_id UUID;
BEGIN
    -- Handle INSERT (Like)
    IF (TG_OP = 'INSERT') THEN
        -- Get photo owner and location
        SELECT user_id, location_name INTO v_owner_id, v_location_name
        FROM cat_photos
        WHERE id = NEW.photo_id;

        -- Don't notify if user likes their own photo
        IF v_owner_id = NEW.user_id THEN
            RETURN NEW;
        END IF;

        -- Get actor name (Liker)
        SELECT name INTO v_actor_name
        FROM users
        WHERE id = NEW.user_id;
        
        -- Fallback if name is missing
        IF v_actor_name IS NULL THEN
            v_actor_name := 'Someone';
        END IF;

        -- Check for existing unread notification to prevent spam
        -- If an unread notification exists for this like, we don't need another one.
        -- If it's read, we create a new one.
        SELECT id INTO v_existing_id
        FROM notifications
        WHERE user_id = v_owner_id
          AND actor_id = NEW.user_id
          AND resource_id = NEW.photo_id
          AND type = 'like'
          AND is_read = FALSE;

        IF v_existing_id IS NOT NULL THEN
            -- Optionally update created_at to bump it? 
            -- UPDATE notifications SET created_at = NOW() WHERE id = v_existing_id;
            -- Let's just do nothing to be less intrusive.
            RETURN NEW;
        END IF;

        -- Create Notification
        INSERT INTO notifications (
            user_id,
            actor_id,
            type,
            title,
            message,
            resource_id,
            resource_type
        ) VALUES (
            v_owner_id,
            NEW.user_id,
            'like',
            'New Like',
            v_actor_name || ' liked your photo' || CASE WHEN v_location_name IS NOT NULL AND v_location_name != '' THEN ' at ' || v_location_name ELSE '' END,
            NEW.photo_id,
            'photo'
        );

    -- Handle DELETE (Unlike)
    ELSIF (TG_OP = 'DELETE') THEN
        -- Remove the notification if the user unlikes
        DELETE FROM notifications
        WHERE actor_id = OLD.user_id
          AND resource_id = OLD.photo_id
          AND type = 'like';
          
        RETURN OLD;
    END IF;

    RETURN NULL;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- 2. Create the trigger
DROP TRIGGER IF EXISTS trg_notify_on_photo_like ON photo_likes;

CREATE TRIGGER trg_notify_on_photo_like
AFTER INSERT OR DELETE ON photo_likes
FOR EACH ROW
EXECUTE FUNCTION notify_on_photo_like();
