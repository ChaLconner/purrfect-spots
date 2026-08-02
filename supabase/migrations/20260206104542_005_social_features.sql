-- Add counters to cat_photos
ALTER TABLE cat_photos 
ADD COLUMN IF NOT EXISTS likes_count INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS comments_count INTEGER DEFAULT 0;

-- Create photo_likes table
CREATE TABLE IF NOT EXISTS photo_likes (
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    photo_id UUID REFERENCES cat_photos(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ DEFAULT now(),
    PRIMARY KEY (user_id, photo_id)
);

-- Create photo_comments table
CREATE TABLE IF NOT EXISTS photo_comments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    photo_id UUID REFERENCES cat_photos(id) ON DELETE CASCADE,
    content TEXT NOT NULL CHECK (length(content) > 0),
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ
);

-- RLS for Likes
ALTER TABLE photo_likes ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Likes are public" 
ON photo_likes FOR SELECT USING (true);

CREATE POLICY "Authenticated users can like" 
ON photo_likes FOR INSERT TO authenticated 
WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can unlike" 
ON photo_likes FOR DELETE TO authenticated 
USING (auth.uid() = user_id);

-- RLS for Comments
ALTER TABLE photo_comments ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Comments are public" 
ON photo_comments FOR SELECT USING (true);

CREATE POLICY "Authenticated users can comment" 
ON photo_comments FOR INSERT TO authenticated 
WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own comments" 
ON photo_comments FOR UPDATE TO authenticated 
USING (auth.uid() = user_id);

CREATE POLICY "Users can delete own comments" 
ON photo_comments FOR DELETE TO authenticated 
USING (auth.uid() = user_id);

-- Indexes
CREATE INDEX idx_photo_likes_photo_id ON photo_likes(photo_id);
CREATE INDEX idx_photo_comments_photo_id ON photo_comments(photo_id, created_at DESC);

-- Functions to update counts
CREATE OR REPLACE FUNCTION update_likes_count()
RETURNS TRIGGER AS $$
BEGIN
    IF (TG_OP = 'INSERT') THEN
        UPDATE cat_photos SET likes_count = likes_count + 1 WHERE id = NEW.photo_id;
        RETURN NEW;
    ELSIF (TG_OP = 'DELETE') THEN
        UPDATE cat_photos SET likes_count = likes_count - 1 WHERE id = OLD.photo_id;
        RETURN OLD;
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION update_comments_count()
RETURNS TRIGGER AS $$
BEGIN
    IF (TG_OP = 'INSERT') THEN
        UPDATE cat_photos SET comments_count = comments_count + 1 WHERE id = NEW.photo_id;
        RETURN NEW;
    ELSIF (TG_OP = 'DELETE') THEN
        UPDATE cat_photos SET comments_count = comments_count - 1 WHERE id = OLD.photo_id;
        RETURN OLD;
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- Triggers
DROP TRIGGER IF EXISTS trigger_update_likes_count ON photo_likes;
CREATE TRIGGER trigger_update_likes_count
AFTER INSERT OR DELETE ON photo_likes
FOR EACH ROW EXECUTE FUNCTION update_likes_count();

DROP TRIGGER IF EXISTS trigger_update_comments_count ON photo_comments;
CREATE TRIGGER trigger_update_comments_count
AFTER INSERT OR DELETE ON photo_comments
FOR EACH ROW EXECUTE FUNCTION update_comments_count();
