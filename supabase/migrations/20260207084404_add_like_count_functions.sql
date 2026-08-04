CREATE OR REPLACE FUNCTION increment_likes_count(row_id UUID)
RETURNS void AS $$
BEGIN
  UPDATE cat_photos
  SET likes_count = COALESCE(likes_count, 0) + 1
  WHERE id = row_id;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

CREATE OR REPLACE FUNCTION decrement_likes_count(row_id UUID)
RETURNS void AS $$
BEGIN
  UPDATE cat_photos
  SET likes_count = GREATEST(0, COALESCE(likes_count, 0) - 1)
  WHERE id = row_id;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;
