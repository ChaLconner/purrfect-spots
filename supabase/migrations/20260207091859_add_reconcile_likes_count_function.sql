
-- Create function to reconcile likes_count with actual photo_likes table
-- This should be run periodically (e.g., via cron job) to fix any count drift
CREATE OR REPLACE FUNCTION public.reconcile_likes_counts()
RETURNS TABLE (
    photo_id UUID,
    old_count INTEGER,
    new_count INTEGER
)
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
BEGIN
    -- Find and fix any mismatched counts
    RETURN QUERY
    WITH actual_counts AS (
        SELECT 
            pl.photo_id,
            COUNT(*)::INTEGER as actual_count
        FROM photo_likes pl
        GROUP BY pl.photo_id
    ),
    mismatched AS (
        SELECT 
            cp.id as photo_id,
            cp.likes_count as old_count,
            COALESCE(ac.actual_count, 0) as new_count
        FROM cat_photos cp
        LEFT JOIN actual_counts ac ON ac.photo_id = cp.id
        WHERE cp.likes_count != COALESCE(ac.actual_count, 0)
    )
    UPDATE cat_photos cp
    SET likes_count = m.new_count
    FROM mismatched m
    WHERE cp.id = m.photo_id
    RETURNING cp.id, m.old_count, m.new_count;
END;
$$;

-- Grant execute permission
GRANT EXECUTE ON FUNCTION public.reconcile_likes_counts() TO service_role;

-- Add comment for documentation
COMMENT ON FUNCTION public.reconcile_likes_counts IS 'Reconciles likes_count in cat_photos with actual counts from photo_likes table. Returns list of fixed records.';

