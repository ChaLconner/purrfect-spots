-- Add indexes for common query patterns to improve performance
-- NOTE: Many indexes here were redundant with 004_add_performance_indexes.sql and have been commented out.
-- Removed CONCURRENTLY keyword to ensure compatibility with Supabase SQL Editor transaction blocks.

-- Users lookups by email (Auth)
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);

-- Cat photos by user (Profile page)
-- Redundant: 'idx_cat_photos_user_id' created in 004_add_performance_indexes.sql
-- CREATE INDEX IF NOT EXISTS idx_cat_photos_user_id ON cat_photos(user_id);

-- Cat photos feed (Gallery by date)
-- Redundant: 'idx_cat_photos_uploaded_at_desc' created in 004_add_performance_indexes.sql
-- CREATE INDEX IF NOT EXISTS idx_cat_photos_created_at ON cat_photos(uploaded_at DESC);

-- Geospatial lookups (Map view) - Composite index for lat/lng queries
-- Redundant: 'idx_cat_photos_geo' created in 002_add_search_indexes.sql
-- CREATE INDEX IF NOT EXISTS idx_cat_photos_location ON cat_photos(latitude, longitude);

-- Optional: Index for tags if we had a dedicated tags table, but currently tags are JSONB or array in PostgreSQL
-- Assuming 'tags' column exists and is JSONB/Array. If we query tags often:
-- CREATE INDEX IF NOT EXISTS idx_cat_photos_tags ON cat_photos USING GIN (tags);
