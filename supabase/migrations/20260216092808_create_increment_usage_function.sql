CREATE OR REPLACE FUNCTION increment_usage(p_user_id UUID, p_date DATE)
RETURNS VOID AS $$
BEGIN
    -- Update user quota
    INSERT INTO user_daily_quotas (user_id, date, upload_count)
    VALUES (p_user_id, p_date, 1)
    ON CONFLICT (user_id, date) DO UPDATE
    SET upload_count = user_daily_quotas.upload_count + 1;

    -- Update system global stats
    INSERT INTO system_daily_stats (date, total_uploads)
    VALUES (p_date, 1)
    ON CONFLICT (date) DO UPDATE
    SET total_uploads = system_daily_stats.total_uploads + 1;
END;
$$ LANGUAGE plpgsql;
