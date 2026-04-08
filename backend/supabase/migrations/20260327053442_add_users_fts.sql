-- Migration: Add Admin Dashboard RPC Functions
-- Description: Create RPC functions for generating dashboard analytics and trends
-- Migration ID: 20260327090000_admin_dashboard_rpc

-- 1. Create monthly stats function
CREATE OR REPLACE FUNCTION get_monthly_report(report_year INTEGER DEFAULT EXTRACT(YEAR FROM NOW())::INTEGER)
RETURNS TABLE (
    month_timestamp TIMESTAMPTZ,
    new_users BIGINT,
    new_photos BIGINT,
    resolved_reports BIGINT,
    points_earned BIGINT
) AS $$
BEGIN
    RETURN QUERY
    WITH months AS (
        SELECT generate_series(
            make_timestamptz(report_year, 1, 1, 0, 0, 0),
            make_timestamptz(report_year, 12, 1, 0, 0, 0),
            interval '1 month'
        ) AS m
    )
    SELECT 
        m.m AS month_timestamp,
        (SELECT count(*) FROM users u WHERE date_trunc('month', u.created_at) = m.m) AS new_users,
        (SELECT count(*) FROM cat_photos cp WHERE date_trunc('month', cp.uploaded_at) = m.m) AS new_photos,
        (SELECT count(*) FROM reports r WHERE date_trunc('month', r.updated_at) = m.m AND r.status = 'resolved') AS resolved_reports,
        (SELECT COALESCE(sum(amount), 0)::BIGINT FROM treat_transactions tt WHERE date_trunc('month', tt.created_at) = m.m AND tt.type = 'EARN') AS points_earned
    FROM months m
    ORDER BY m.m;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- 2. Create get_admin_trends function
CREATE OR REPLACE FUNCTION get_admin_trends(days_back INTEGER DEFAULT 30)
RETURNS JSONB AS $$
DECLARE
    result JSONB;
BEGIN
    WITH date_series AS (
        SELECT generate_series(
            date_trunc('day', NOW() - (days_back || ' days')::interval),
            date_trunc('day', NOW()),
            interval '1 day'
        ) AS d
    ),
    user_trends AS (
        SELECT 
            d.d::date as date,
            (SELECT count(*) FROM users u WHERE date_trunc('day', u.created_at) = d.d) as count
        FROM date_series d
    ),
    photo_trends AS (
        SELECT 
            d.d::date as date,
            (SELECT count(*) FROM cat_photos cp WHERE date_trunc('day', cp.uploaded_at) = d.d) as count
        FROM date_series d
    ),
    report_trends AS (
        SELECT 
            d.d::date as date,
            (SELECT count(*) FROM reports r WHERE date_trunc('day', r.created_at) = d.d) as count
        FROM date_series d
    )
    SELECT jsonb_build_object(
        'users', (SELECT jsonb_agg(user_trends) FROM user_trends),
        'photos', (SELECT jsonb_agg(photo_trends) FROM photo_trends),
        'reports', (SELECT jsonb_agg(report_trends) FROM report_trends)
    ) INTO result;

    RETURN result;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;
