-- Migration: 004_add_performance_indexes.sql
-- Description: Add indexes for frequently queried columns to improve performance
-- Created: 2026-01-10

-- =====================================================
-- INDEX FOR USER'S PHOTOS QUERY
-- Speeds up: SELECT * FROM cat_photos WHERE user_id = ?
-- =====================================================
CREATE INDEX IF NOT EXISTS idx_cat_photos_user_id 
ON cat_photos(user_id);

-- =====================================================
-- INDEX FOR SORTING BY UPLOAD DATE
-- Speeds up: SELECT * FROM cat_photos ORDER BY uploaded_at DESC
-- =====================================================
CREATE INDEX IF NOT EXISTS idx_cat_photos_uploaded_at_desc 
ON cat_photos(uploaded_at DESC);

-- =====================================================
-- COMPOSITE INDEX FOR USER + DATE QUERIES
-- Speeds up: SELECT * FROM cat_photos WHERE user_id = ? ORDER BY uploaded_at DESC
-- =====================================================
CREATE INDEX IF NOT EXISTS idx_cat_photos_user_uploaded 
ON cat_photos(user_id, uploaded_at DESC);

-- =====================================================
-- INDEX FOR LOCATION-BASED QUERIES
-- Speeds up: Nearby location searches (bounding box)
-- =====================================================
CREATE INDEX IF NOT EXISTS idx_cat_photos_latitude 
ON cat_photos(latitude);

CREATE INDEX IF NOT EXISTS idx_cat_photos_longitude 
ON cat_photos(longitude);

-- Composite index for location + date (common query pattern)
CREATE INDEX IF NOT EXISTS idx_cat_photos_location_date 
ON cat_photos(latitude, longitude, uploaded_at DESC);

-- =====================================================
-- INDEX FOR LOCATION NAME SEARCH
-- Speeds up: ILIKE searches on location_name
-- =====================================================
-- Enable pg_trgm extension for GIN index
CREATE EXTENSION IF NOT EXISTS pg_trgm;

CREATE INDEX IF NOT EXISTS idx_cat_photos_location_name_trgm 
ON cat_photos USING gin (location_name gin_trgm_ops);

-- =====================================================
-- PARTIAL INDEX FOR NON-NULL TAGS
-- Speeds up: Queries filtering on tags array
-- =====================================================
CREATE INDEX IF NOT EXISTS idx_cat_photos_tags 
ON cat_photos USING gin (tags) 
WHERE tags IS NOT NULL AND array_length(tags, 1) > 0;

-- =====================================================
-- INDEX FOR PASSWORD RESET TOKENS
-- Speeds up: Token lookup for password reset flow
-- =====================================================
CREATE INDEX IF NOT EXISTS idx_password_resets_token 
ON password_resets(token) 
WHERE used = false AND expires_at > NOW();

CREATE INDEX IF NOT EXISTS idx_password_resets_email 
ON password_resets(email);

-- =====================================================
-- ANALYZE TABLES TO UPDATE STATISTICS
-- =====================================================
ANALYZE cat_photos;
ANALYZE password_resets;

-- =====================================================
-- NOTES:
-- 1. Run this migration in Supabase SQL Editor
-- 2. gin_trgm_ops requires pg_trgm extension:
--    CREATE EXTENSION IF NOT EXISTS pg_trgm;
-- 3. Monitor query performance with: EXPLAIN ANALYZE
-- =====================================================
