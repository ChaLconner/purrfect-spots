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
    WITH date_series AS (
        SELECT (start_dt + i)::DATE as d
        FROM generate_series(0, days_back) i
    )
    SELECT jsonb_build_object(
        'users', (
            SELECT jsonb_agg(jsonb_build_object('date', ds.d, 'count', COALESCE(s.new_users, 0)) ORDER BY ds.d ASC)
            FROM date_series ds
            LEFT JOIN system_daily_stats s ON s.date = ds.d
        ),
        'photos', (
            SELECT jsonb_agg(jsonb_build_object('date', ds.d, 'count', COALESCE(s.total_uploads, 0)) ORDER BY ds.d ASC)
            FROM date_series ds
            LEFT JOIN system_daily_stats s ON s.date = ds.d
        ),
        'reports', (
            SELECT jsonb_agg(jsonb_build_object('date', ds.d, 'count', COALESCE(s.new_reports, 0)) ORDER BY ds.d ASC)
            FROM date_series ds
            LEFT JOIN system_daily_stats s ON s.date = ds.d
        )
    ) INTO result;

    RETURN result;
END;
$$;
