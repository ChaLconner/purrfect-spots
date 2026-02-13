-- Migration: Add RPC for fetching gallery photos with user "liked" status
-- This avoids N+1 query patterns and improves performance

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

COMMENT ON FUNCTION get_gallery_photos_with_likes IS 'Get gallery photos enriched with liked status for the specific user';
