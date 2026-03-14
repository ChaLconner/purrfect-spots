-- Migration: Enable Row Level Security (RLS) for all remaining public tables
-- Following Purrfect Spots Security Best Practices

-- 1. Enable RLS on all tables
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE cat_photos ENABLE ROW LEVEL SECURITY;
ALTER TABLE photo_likes ENABLE ROW LEVEL SECURITY;
ALTER TABLE photo_comments ENABLE ROW LEVEL SECURITY;
ALTER TABLE treats_transactions ENABLE ROW LEVEL SECURITY;
ALTER TABLE treat_packages ENABLE ROW LEVEL SECURITY;
ALTER TABLE notifications ENABLE ROW LEVEL SECURITY;
ALTER TABLE password_resets ENABLE ROW LEVEL SECURITY;
ALTER TABLE token_blacklist ENABLE ROW LEVEL SECURITY;

-- 2. Define Policies

-- USERS
DROP POLICY IF EXISTS "Public users can view all users" ON users;
CREATE POLICY "Public users can view all users" ON users FOR SELECT USING (true);

DROP POLICY IF EXISTS "Users can update their own data" ON users;
CREATE POLICY "Users can update their own data" ON users FOR UPDATE USING (auth.uid() = id);

-- CAT PHOTOS
DROP POLICY IF EXISTS "Public can view all non-deleted photos" ON cat_photos;
CREATE POLICY "Public can view all non-deleted photos" ON cat_photos FOR SELECT 
USING (deleted_at IS NULL);

DROP POLICY IF EXISTS "Users can upload their own photos" ON cat_photos;
CREATE POLICY "Users can upload their own photos" ON cat_photos FOR INSERT 
WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can update their own photos" ON cat_photos;
CREATE POLICY "Users can update their own photos" ON cat_photos FOR UPDATE 
USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can delete their own photos" ON cat_photos;
CREATE POLICY "Users can delete their own photos" ON cat_photos FOR DELETE 
USING (auth.uid() = user_id);

-- PHOTO LIKES
DROP POLICY IF EXISTS "Public can view likes" ON photo_likes;
CREATE POLICY "Public can view likes" ON photo_likes FOR SELECT USING (true);

DROP POLICY IF EXISTS "Users can like photos" ON photo_likes;
CREATE POLICY "Users can like photos" ON photo_likes FOR INSERT 
WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can unlike photos" ON photo_likes;
CREATE POLICY "Users can unlike photos" ON photo_likes FOR DELETE 
USING (auth.uid() = user_id);

-- PHOTO COMMENTS
DROP POLICY IF EXISTS "Public can view comments" ON photo_comments;
CREATE POLICY "Public can view comments" ON photo_comments FOR SELECT USING (true);

DROP POLICY IF EXISTS "Users can post comments" ON photo_comments;
CREATE POLICY "Users can post comments" ON photo_comments FOR INSERT 
WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can update their own comments" ON photo_comments;
CREATE POLICY "Users can update their own comments" ON photo_comments FOR UPDATE 
USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can delete their own comments" ON photo_comments;
CREATE POLICY "Users can delete their own comments" ON photo_comments FOR DELETE 
USING (auth.uid() = user_id);

-- TREATS TRANSACTIONS
DROP POLICY IF EXISTS "Users can see their own transactions" ON treats_transactions;
CREATE POLICY "Users can see their own transactions" ON treats_transactions FOR SELECT 
USING (auth.uid() = from_user_id OR auth.uid() = to_user_id);

-- TREAT PACKAGES
DROP POLICY IF EXISTS "Everyone can view active packages" ON treat_packages;
CREATE POLICY "Everyone can view active packages" ON treat_packages FOR SELECT 
USING (is_active = true);

-- NOTIFICATIONS
DROP POLICY IF EXISTS "Users can view their own notifications" ON notifications;
CREATE POLICY "Users can view their own notifications" ON notifications FOR SELECT 
USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can update their own notifications" ON notifications;
CREATE POLICY "Users can update their own notifications" ON notifications FOR UPDATE 
USING (auth.uid() = user_id);

-- PASSWORD RESETS
-- Strictly system-level (service role), no public access allowed by default after ENABLE RLS
-- But we can add an explicit deny if we want to be paranoid, or just let default RLS handle it (deny all).

-- TOKEN BLACKLIST
DROP POLICY IF EXISTS "Public can view blacklisted tokens" ON token_blacklist;
CREATE POLICY "Public can view blacklisted tokens" ON token_blacklist FOR SELECT USING (true);
