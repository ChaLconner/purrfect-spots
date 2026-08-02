CREATE OR REPLACE FUNCTION get_admin_trends(days_back int DEFAULT 30)
RETURNS JSONB
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public, pg_temp
AS $$
DECLARE
    result JSONB;
    start_dt DATE := (CURRENT_DATE - (days_back || ' days')::interval)::DATE;
BEGIN
    WITH RECURSIVE date_series AS (
        SELECT start_dt AS d
        UNION ALL
        SELECT (d + 1)::DATE
        FROM date_series
        WHERE d < CURRENT_DATE
    )
    SELECT jsonb_build_object(
        'users', (
            SELECT jsonb_agg(jsonb_build_object('date', ds.d, 'count', COALESCE(s.new_users, 0)))
            FROM date_series ds
            LEFT JOIN system_daily_stats s ON s.date = ds.d
            ORDER BY ds.d ASC
        ),
        'photos', (
            SELECT jsonb_agg(jsonb_build_object('date', ds.d, 'count', COALESCE(s.total_uploads, 0)))
            FROM date_series ds
            LEFT JOIN system_daily_stats s ON s.date = ds.d
            ORDER BY ds.d ASC
        ),
        'reports', (
            SELECT jsonb_agg(jsonb_build_object('date', ds.d, 'count', COALESCE(s.new_reports, 0)))
            FROM date_series ds
            LEFT JOIN system_daily_stats s ON s.date = ds.d
            ORDER BY ds.d ASC
        )
    ) INTO result;

    RETURN result;
END;
$$;
