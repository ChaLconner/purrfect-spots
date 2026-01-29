-- Enable Row Level Security
ALTER TABLE public.cat_photos ENABLE ROW LEVEL SECURITY;

-- Policy: Allow public read access to all photos
DROP POLICY IF EXISTS "Public read access" ON public.cat_photos;
CREATE POLICY "Public read access"
ON public.cat_photos
FOR SELECT
USING (true);

-- Policy: Allow authenticated users to upload their own photos
DROP POLICY IF EXISTS "Users can upload their own photos" ON public.cat_photos;
CREATE POLICY "Users can upload their own photos"
ON public.cat_photos
FOR INSERT
WITH CHECK (auth.uid() = user_id);

-- Policy: Allow users to update their own photos
DROP POLICY IF EXISTS "Users can update their own photos" ON public.cat_photos;
CREATE POLICY "Users can update their own photos"
ON public.cat_photos
FOR UPDATE
USING (auth.uid() = user_id);

-- Policy: Allow users to delete their own photos
DROP POLICY IF EXISTS "Users can delete their own photos" ON public.cat_photos;
CREATE POLICY "Users can delete their own photos"
ON public.cat_photos
FOR DELETE
USING (auth.uid() = user_id);

-- Ensure users table also has RLS (usually enabled by default but good to ensure)
ALTER TABLE public.users ENABLE ROW LEVEL SECURITY;

-- Users can read their own profile (or public profiles if strictly needed, but let's say public can read basic info if we had public profiles)
-- For now, allow users to read their own data
DROP POLICY IF EXISTS "Users can read own profile" ON public.users;
CREATE POLICY "Users can read own profile"
ON public.users
FOR SELECT
USING (auth.uid() = id);

-- Users can update their own profile
DROP POLICY IF EXISTS "Users can update own profile" ON public.users;
CREATE POLICY "Users can update own profile"
ON public.users
FOR UPDATE
USING (auth.uid() = id);
