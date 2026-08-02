
CREATE OR REPLACE FUNCTION get_admin_trends(days_back int DEFAULT 30)
RETURNS json AS $$
DECLARE
    result json;
BEGIN
    WITH date_series AS (
        SELECT generate_series(
            current_date - (days_back || ' days')::interval,
            current_date,
            '1 day'::interval
        )::date AS day
    ),
    user_counts AS (
        SELECT created_at::date AS day, count(*) as count
        FROM users
        WHERE created_at >= (current_date - (days_back || ' days')::interval)
        GROUP BY 1
    ),
    photo_counts AS (
        SELECT uploaded_at::date AS day, count(*) as count
        FROM cat_photos
        WHERE uploaded_at >= (current_date - (days_back || ' days')::interval)
        GROUP BY 1
    ),
    report_counts AS (
        SELECT created_at::date AS day, count(*) as count
        FROM reports
        WHERE created_at >= (current_date - (days_back || ' days')::interval)
        GROUP BY 1
    )
    SELECT json_build_object(
        'users', (
            SELECT json_agg(json_build_object('date', ds.day, 'count', COALESCE(uc.count, 0)))
            FROM date_series ds
            LEFT JOIN user_counts uc ON ds.day = uc.day
        ),
        'photos', (
            SELECT json_agg(json_build_object('date', ds.day, 'count', COALESCE(pc.count, 0)))
            FROM date_series ds
            LEFT JOIN photo_counts pc ON ds.day = pc.day
        ),
        'reports', (
            SELECT json_agg(json_build_object('date', ds.day, 'count', COALESCE(rc.count, 0)))
            FROM date_series ds
            LEFT JOIN report_counts rc ON ds.day = rc.day
        ),
        'generated_at', now()
    ) INTO result;

    RETURN result;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

