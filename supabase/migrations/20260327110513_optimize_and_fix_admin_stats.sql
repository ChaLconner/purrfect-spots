-- Migration: Fix and Optimize Admin Dashboard RPCs
-- Description: Correct table name for treats transactions and optimize query performance with indices and grouping.

-- 1. Create indices for performance
CREATE INDEX IF NOT EXISTS idx_users_created_at ON users(created_at);
CREATE INDEX IF NOT EXISTS idx_cat_photos_uploaded_at ON cat_photos(uploaded_at);
CREATE INDEX IF NOT EXISTS idx_reports_updated_at ON reports(updated_at);
CREATE INDEX IF NOT EXISTS idx_reports_created_at ON reports(created_at);
CREATE INDEX IF NOT EXISTS idx_treats_transactions_created_at ON treats_transactions(created_at);
CREATE INDEX IF NOT EXISTS idx_treats_transactions_type ON treats_transactions(transaction_type);

-- 2. Refined monthly stats function (optimized range queries)
CREATE OR REPLACE FUNCTION get_monthly_report(report_year INTEGER DEFAULT EXTRACT(YEAR FROM NOW())::INTEGER)
RETURNS TABLE (
    month_timestamp TIMESTAMPTZ,
    new_users BIGINT,
    new_photos BIGINT,
    resolved_reports BIGINT,
    points_earned BIGINT
) AS $$
DECLARE
    start_date TIMESTAMPTZ := make_timestamptz(report_year, 1, 1, 0, 0, 0);
    end_date TIMESTAMPTZ := make_timestamptz(report_year, 12, 31, 23, 59, 59);
BEGIN
    RETURN QUERY
    WITH RECURSIVE months AS (
        SELECT start_date AS m
        UNION ALL
        SELECT m + interval '1 month'
        FROM months
        WHERE m < make_timestamptz(report_year, 12, 1, 0, 0, 0)
    ),
    user_counts AS (
        SELECT date_trunc('month', created_at) as month, count(*) as count
        FROM users
        WHERE created_at >= start_date AND created_at <= end_date
        GROUP BY 1
    ),
    photo_counts AS (
        SELECT date_trunc('month', uploaded_at) as month, count(*) as count
        FROM cat_photos
        WHERE uploaded_at >= start_date AND uploaded_at <= end_date
        GROUP BY 1
    ),
    report_counts AS (
        SELECT date_trunc('month', updated_at) as month, count(*) as count
        FROM reports
        WHERE updated_at >= start_date AND updated_at <= end_date AND status = 'resolved'
        GROUP BY 1
    ),
    earned_points AS (
        SELECT date_trunc('month', created_at) as month, sum(amount)::BIGINT as count
        FROM treats_transactions
        WHERE created_at >= start_date AND created_at <= end_date AND transaction_type = 'EARN'
        GROUP BY 1
    )
    SELECT 
        m.m AS month_timestamp,
        COALESCE(u.count, 0) AS new_users,
        COALESCE(p.count, 0) AS new_photos,
        COALESCE(r.count, 0) AS resolved_reports,
        COALESCE(e.count, 0) AS points_earned
    FROM months m
    LEFT JOIN user_counts u ON u.month = m.m
    LEFT JOIN photo_counts p ON p.month = m.m
    LEFT JOIN report_counts r ON r.month = m.m
    LEFT JOIN earned_points e ON e.month = m.m
    ORDER BY m.m;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- 3. Refined get_admin_trends function (optimized range queries)
CREATE OR REPLACE FUNCTION get_admin_trends(days_back INTEGER DEFAULT 30)
RETURNS JSONB AS $$
DECLARE
    result JSONB;
    start_dt TIMESTAMPTZ := date_trunc('day', NOW() - (days_back || ' days')::interval);
BEGIN
    WITH RECURSIVE date_series AS (
        SELECT start_dt AS d
        UNION ALL
        SELECT d + interval '1 day'
        FROM date_series
        WHERE d < date_trunc('day', NOW())
    ),
    user_counts AS (
        SELECT date_trunc('day', created_at) as day, count(*) as count
        FROM users
        WHERE created_at >= start_dt
        GROUP BY 1
    ),
    photo_counts AS (
        SELECT date_trunc('day', uploaded_at) as day, count(*) as count
        FROM cat_photos
        WHERE uploaded_at >= start_dt
        GROUP BY 1
    ),
    report_counts AS (
        SELECT date_trunc('day', created_at) as day, count(*) as count
        FROM reports
        WHERE created_at >= start_dt
        GROUP BY 1
    )
    SELECT jsonb_build_object(
        'users', (
            SELECT jsonb_agg(jsonb_build_object('date', d.d::date, 'count', COALESCE(u.count, 0)))
            FROM date_series d
            LEFT JOIN user_counts u ON u.day = d.d
        ),
        'photos', (
            SELECT jsonb_agg(jsonb_build_object('date', d.d::date, 'count', COALESCE(p.count, 0)))
            FROM date_series d
            LEFT JOIN photo_counts p ON p.day = d.d
        ),
        'reports', (
            SELECT jsonb_agg(jsonb_build_object('date', d.d::date, 'count', COALESCE(r.count, 0)))
            FROM date_series d
            LEFT JOIN report_counts r ON r.day = d.d
        )
    ) INTO result;

    RETURN result;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

