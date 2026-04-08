-- Migration: Refactor Admin Dashboard RPC for Performance
-- Description: Replaces inefficient correlated subqueries with JOIN/GROUP BY in dashboard functions.

-- 1. Optimized get_monthly_report
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
            make_timestamptz(report_year, 1, 1, 0, 0, 0, 'UTC'),
            make_timestamptz(report_year, 12, 1, 0, 0, 0, 'UTC'),
            interval '1 month'
        ) AS m
    ),
    u_counts AS (
        SELECT date_trunc('month', created_at) as m, count(*) as cnt 
        FROM users 
        WHERE extract(year from created_at) = report_year
        GROUP BY 1
    ),
    p_counts AS (
        SELECT date_trunc('month', uploaded_at) as m, count(*) as cnt
        FROM cat_photos
        WHERE extract(year from uploaded_at) = report_year
        GROUP BY 1
    ),
    r_counts AS (
        SELECT date_trunc('month', updated_at) as m, count(*) as cnt
        FROM reports
        WHERE extract(year from updated_at) = report_year AND status = 'resolved'
        GROUP BY 1
    ),
    t_sums AS (
        SELECT date_trunc('month', created_at) as m, sum(amount)::BIGINT as total
        FROM treats_transactions
        WHERE extract(year from created_at) = report_year AND transaction_type = 'PURCHASE'
        GROUP BY 1
    )
    SELECT 
        m.m AS month_timestamp,
        COALESCE(u.cnt, 0)::BIGINT,
        COALESCE(p.cnt, 0)::BIGINT,
        COALESCE(r.cnt, 0)::BIGINT,
        COALESCE(t.total, 0)::BIGINT
    FROM months m
    LEFT JOIN u_counts u ON u.m = m.m
    LEFT JOIN p_counts p ON p.m = m.m
    LEFT JOIN r_counts r ON r.m = m.m
    LEFT JOIN t_sums t ON t.m = m.m
    ORDER BY m.m;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- 2. Optimized get_admin_trends
CREATE OR REPLACE FUNCTION get_admin_trends(days_back INTEGER DEFAULT 30)
RETURNS JSONB AS $$
DECLARE
    result JSONB;
BEGIN
    WITH date_series AS (
        SELECT d::date as date
        FROM generate_series(
            current_date - (days_back || ' days')::interval,
            current_date,
            interval '1 day'
        ) AS d
    ),
    user_counts AS (
        SELECT created_at::date as date, count(*) as cnt
        FROM users
        WHERE created_at >= (current_date - (days_back || ' days')::interval)
        GROUP BY 1
    ),
    photo_counts AS (
        SELECT uploaded_at::date as date, count(*) as cnt
        FROM cat_photos
        WHERE uploaded_at >= (current_date - (days_back || ' days')::interval)
        GROUP BY 1
    ),
    report_counts AS (
        SELECT created_at::date as date, count(*) as cnt
        FROM reports
        WHERE created_at >= (current_date - (days_back || ' days')::interval)
        GROUP BY 1
    ),
    user_trends AS (
        SELECT d.date, COALESCE(u.cnt, 0) as count
        FROM date_series d
        LEFT JOIN user_counts u ON u.date = d.date
    ),
    photo_trends AS (
        SELECT d.date, COALESCE(p.cnt, 0) as count
        FROM date_series d
        LEFT JOIN photo_counts p ON p.date = d.date
    ),
    report_trends AS (
        SELECT d.date, COALESCE(r.cnt, 0) as count
        FROM date_series d
        LEFT JOIN report_counts r ON r.date = d.date
    )
    SELECT jsonb_build_object(
        'users', (SELECT jsonb_agg(user_trends) FROM user_trends),
        'photos', (SELECT jsonb_agg(photo_trends) FROM photo_trends),
        'reports', (SELECT jsonb_agg(report_trends) FROM report_trends)
    ) INTO result;

    RETURN result;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;
