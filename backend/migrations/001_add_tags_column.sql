-- Migration: Add tags column to cat_photos table
-- Run this in Supabase SQL Editor

-- Step 1: Add tags column as TEXT array
ALTER TABLE cat_photos 
ADD COLUMN IF NOT EXISTS tags TEXT[] DEFAULT '{}';

-- Step 2: Create GIN index for fast array search
CREATE INDEX IF NOT EXISTS idx_cat_photos_tags 
ON cat_photos USING GIN (tags);

-- Step 3: Extract existing hashtags from descriptions and populate tags column
-- This migrates existing data
UPDATE cat_photos 
SET tags = (
    SELECT ARRAY(
        SELECT DISTINCT LOWER(TRIM(BOTH '#' FROM match[1]))
        FROM regexp_matches(description, '#([a-zA-Z0-9_]+)', 'g') AS match
        WHERE match[1] IS NOT NULL
    )
)
WHERE description LIKE '%#%' AND (tags IS NULL OR tags = '{}');

-- Step 4: Add comment for documentation
COMMENT ON COLUMN cat_photos.tags IS 'Array of hashtags associated with the photo';

-- Verification query (run separately to check results)
-- SELECT id, location_name, tags, description FROM cat_photos WHERE array_length(tags, 1) > 0;
