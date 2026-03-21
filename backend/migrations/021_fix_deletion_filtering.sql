-- Migration 020: Fix deletion filtering in RPC functions
-- Update search and nearby functions to respect soft delete (deleted_at IS NULL)

-- Drop existing functions to avoid parameter/return type conflicts
DROP FUNCTION IF EXISTS search_cat_photos(text, integer);
DROP FUNCTION IF EXISTS search_cat_photos(text, integer, integer);
DROP FUNCTION IF EXISTS search_nearby_photos(double precision, double precision, double precision, integer);

-- 1. Update search_cat_photos to include deleted_at filter and support offset
CREATE OR REPLACE FUNCTION search_cat_photos(
    search_query TEXT,
    result_limit INTEGER DEFAULT 100,
    result_offset INTEGER DEFAULT 0
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
    WHERE cp.deleted_at IS NULL
      AND cp.search_vector @@ websearch_to_tsquery('english', search_query)
    ORDER BY search_rank DESC, cp.uploaded_at DESC
    LIMIT result_limit
    OFFSET result_offset;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- 2. Update search_nearby_photos to include deleted_at filter
-- Note: Using GEOGRAPHY for accurate meter measurements
CREATE OR REPLACE FUNCTION search_nearby_photos(
    lat DOUBLE PRECISION,
    lng DOUBLE PRECISION,
    radius_meters DOUBLE PRECISION,
    result_limit INTEGER DEFAULT 50
)
RETURNS TABLE (
    id UUID,
    user_id UUID,
    image_url TEXT,
    location_name TEXT,
    description TEXT,
    latitude DOUBLE PRECISION,
    longitude DOUBLE PRECISION,
    uploaded_at TIMESTAMPTZ,
    tags TEXT[],
    distance_meters DOUBLE PRECISION
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        p.id,
        p.user_id,
        p.image_url,
        p.location_name,
        p.description,
        p.latitude,
        p.longitude,
        p.uploaded_at,
        p.tags,
        ST_Distance(
            ST_SetSRID(ST_MakePoint(p.longitude, p.latitude), 4326)::geography,
            ST_SetSRID(ST_MakePoint(lng, lat), 4326)::geography
        ) as distance_meters
    FROM cat_photos p
    WHERE p.deleted_at IS NULL
      AND ST_DWithin(
            ST_SetSRID(ST_MakePoint(p.longitude, p.latitude), 4326)::geography,
            ST_SetSRID(ST_MakePoint(lng, lat), 4326)::geography,
            radius_meters
        )
    ORDER BY distance_meters ASC, p.uploaded_at DESC
    LIMIT result_limit;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- 3. Double check get_gallery_photos_with_likes (from 011)
CREATE OR REPLACE FUNCTION get_gallery_photos_with_likes(
  p_user_id UUID DEFAULT NULL,
  p_limit INTEGER DEFAULT 20,
  p_offset INTEGER DEFAULT 0
)
RETURNS TABLE (
  id UUID,
  user_id UUID,
  image_url TEXT,
  location_name TEXT,
  description TEXT,
  latitude DOUBLE PRECISION,
  longitude DOUBLE PRECISION,
  uploaded_at TIMESTAMP WITH TIME ZONE,
  tags TEXT[],
  likes_count INTEGER,
  liked BOOLEAN
) AS $$
BEGIN
  RETURN QUERY
  SELECT
    p.id,
    p.user_id,
    p.image_url,
    p.location_name,
    p.description,
    p.latitude,
    p.longitude,
    p.uploaded_at,
    p.tags,
    p.likes_count,
    CASE
      WHEN p_user_id IS NULL THEN FALSE
      ELSE EXISTS (
        SELECT 1 FROM photo_likes l
        WHERE l.photo_id = p.id AND l.user_id = p_user_id
      )
    END as liked
  FROM cat_photos p
  WHERE p.deleted_at IS NULL
  ORDER BY p.uploaded_at DESC
  LIMIT p_limit OFFSET p_offset;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;
