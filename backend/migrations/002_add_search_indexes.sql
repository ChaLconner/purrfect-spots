-- Migration: Add search indexes for improved query performance
-- Run this in Supabase SQL Editor
-- Created: 2026-01-09

-- =====================================================
-- SECTION 1: Basic Indexes for Common Queries
-- =====================================================

-- Index for location name searches (case-insensitive pattern matching)
CREATE INDEX IF NOT EXISTS idx_cat_photos_location_name
ON cat_photos (location_name);

-- Composite index for user photos sorted by upload date
CREATE INDEX IF NOT EXISTS idx_cat_photos_user_uploaded
ON cat_photos (user_id, uploaded_at DESC);

-- Index for geospatial queries (bounding box searches)
CREATE INDEX IF NOT EXISTS idx_cat_photos_geo
ON cat_photos (latitude, longitude);

-- =====================================================
-- SECTION 2: Full-Text Search Setup
-- =====================================================

-- Step 1: Add a tsvector column for full-text search
ALTER TABLE cat_photos 
ADD COLUMN IF NOT EXISTS search_vector tsvector;

-- Step 2: Create GIN index for full-text search (much faster than LIKE)
CREATE INDEX IF NOT EXISTS idx_cat_photos_search_vector
ON cat_photos USING GIN (search_vector);

-- Step 3: Create a function to generate the search vector
CREATE OR REPLACE FUNCTION cat_photos_search_vector_trigger()
RETURNS trigger AS $$
BEGIN
    NEW.search_vector :=
        setweight(to_tsvector('english', COALESCE(NEW.location_name, '')), 'A') ||
        setweight(to_tsvector('english', COALESCE(NEW.description, '')), 'B') ||
        setweight(to_tsvector('english', COALESCE(array_to_string(NEW.tags, ' '), '')), 'C');
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Step 4: Create trigger to auto-update search vector on insert/update
DROP TRIGGER IF EXISTS cat_photos_search_vector_update ON cat_photos;
CREATE TRIGGER cat_photos_search_vector_update
BEFORE INSERT OR UPDATE ON cat_photos
FOR EACH ROW
EXECUTE FUNCTION cat_photos_search_vector_trigger();

-- Step 5: Populate search_vector for existing data
UPDATE cat_photos
SET search_vector = 
    setweight(to_tsvector('english', COALESCE(location_name, '')), 'A') ||
    setweight(to_tsvector('english', COALESCE(description, '')), 'B') ||
    setweight(to_tsvector('english', COALESCE(array_to_string(tags, ' '), '')), 'C')
WHERE search_vector IS NULL;

-- =====================================================
-- SECTION 3: Add Comments for Documentation
-- =====================================================

COMMENT ON COLUMN cat_photos.search_vector IS 
'Full-text search vector combining location_name (weight A), description (weight B), and tags (weight C)';

COMMENT ON INDEX idx_cat_photos_search_vector IS 
'GIN index for fast full-text search queries';

COMMENT ON INDEX idx_cat_photos_location_name IS 
'B-tree index for location name pattern matching';

COMMENT ON INDEX idx_cat_photos_user_uploaded IS 
'Composite index for efficient user photo queries with date sorting';

COMMENT ON INDEX idx_cat_photos_geo IS 
'Composite index for geospatial bounding box queries';

-- =====================================================
-- SECTION 4: Create Full-Text Search Function
-- =====================================================

-- Create a helper function for full-text search with ranking
CREATE OR REPLACE FUNCTION search_cat_photos(
    search_query TEXT,
    result_limit INTEGER DEFAULT 100
)
RETURNS TABLE (
    id UUID,
    user_id UUID,
    location_name VARCHAR,
    description TEXT,
    latitude DECIMAL,
    longitude DECIMAL,
    image_url TEXT,
    tags TEXT[],
    uploaded_at TIMESTAMPTZ,
    search_rank REAL
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        cp.id,
        cp.user_id,
        cp.location_name,
        cp.description,
        cp.latitude,
        cp.longitude,
        cp.image_url,
        cp.tags,
        cp.uploaded_at,
        ts_rank(cp.search_vector, websearch_to_tsquery('english', search_query)) AS search_rank
    FROM cat_photos cp
    WHERE cp.search_vector @@ websearch_to_tsquery('english', search_query)
    ORDER BY search_rank DESC, cp.uploaded_at DESC
    LIMIT result_limit;
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- SECTION 5: Verification Queries (Run Separately)
-- =====================================================

-- Check indexes are created:
-- SELECT indexname, indexdef FROM pg_indexes WHERE tablename = 'cat_photos';

-- Test full-text search:
-- SELECT * FROM search_cat_photos('cat park', 10);

-- Check search vector content:
-- SELECT id, location_name, search_vector FROM cat_photos LIMIT 5;

-- Analyze query performance:
-- EXPLAIN ANALYZE SELECT * FROM cat_photos WHERE search_vector @@ to_tsquery('english', 'cat');
