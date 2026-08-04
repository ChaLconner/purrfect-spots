-- 1. Alter Table
ALTER TABLE system_daily_stats ADD COLUMN IF NOT EXISTS new_users INTEGER DEFAULT 0;
ALTER TABLE system_daily_stats ADD COLUMN IF NOT EXISTS new_reports INTEGER DEFAULT 0;
ALTER TABLE system_daily_stats ADD COLUMN IF NOT EXISTS resolved_reports INTEGER DEFAULT 0;

-- 2. Trigger Function
CREATE OR REPLACE FUNCTION update_system_daily_stats() 
RETURNS TRIGGER AS $$
DECLARE
    today DATE := CURRENT_DATE;
BEGIN
    -- Ensure today's row exists
    INSERT INTO system_daily_stats (date) 
    VALUES (today) 
    ON CONFLICT (date) DO NOTHING;

    -- Update based on table and action
    IF TG_TABLE_NAME = 'users' THEN
        IF TG_OP = 'INSERT' THEN
            UPDATE system_daily_stats SET new_users = new_users + 1 WHERE date = today;
        ELSIF TG_OP = 'DELETE' THEN
            UPDATE system_daily_stats SET new_users = GREATEST(0, new_users - 1) WHERE date = today;
        END IF;
    ELSIF TG_TABLE_NAME = 'cat_photos' THEN
        IF TG_OP = 'INSERT' THEN
            UPDATE system_daily_stats SET total_uploads = total_uploads + 1 WHERE date = today;
        ELSIF TG_OP = 'DELETE' THEN
            UPDATE system_daily_stats SET total_uploads = GREATEST(0, total_uploads - 1) WHERE date = today;
        END IF;
    ELSIF TG_TABLE_NAME = 'reports' THEN
        IF TG_OP = 'INSERT' THEN
            UPDATE system_daily_stats SET new_reports = new_reports + 1 WHERE date = today;
            IF NEW.status = 'resolved' THEN
                UPDATE system_daily_stats SET resolved_reports = resolved_reports + 1 WHERE date = today;
            END IF;
        ELSIF TG_OP = 'UPDATE' THEN
            IF OLD.status != 'resolved' AND NEW.status = 'resolved' THEN
                UPDATE system_daily_stats SET resolved_reports = resolved_reports + 1 WHERE date = today;
            ELSIF OLD.status = 'resolved' AND NEW.status != 'resolved' THEN
                UPDATE system_daily_stats SET resolved_reports = GREATEST(0, resolved_reports - 1) WHERE date = today;
            END IF;
        ELSIF TG_OP = 'DELETE' THEN
            UPDATE system_daily_stats SET new_reports = GREATEST(0, new_reports - 1) WHERE date = today;
            IF OLD.status = 'resolved' THEN
                UPDATE system_daily_stats SET resolved_reports = GREATEST(0, resolved_reports - 1) WHERE date = today;
            END IF;
        END IF;
    END IF;
    
    RETURN NULL;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER SET search_path = public, pg_temp;

-- 3. Triggers
DROP TRIGGER IF EXISTS trg_update_stats_users ON users;
CREATE TRIGGER trg_update_stats_users AFTER INSERT OR DELETE ON users FOR EACH ROW EXECUTE FUNCTION update_system_daily_stats();

DROP TRIGGER IF EXISTS trg_update_stats_photos ON cat_photos;
CREATE TRIGGER trg_update_stats_photos AFTER INSERT OR DELETE ON cat_photos FOR EACH ROW EXECUTE FUNCTION update_system_daily_stats();

DROP TRIGGER IF EXISTS trg_update_stats_reports ON reports;
CREATE TRIGGER trg_update_stats_reports AFTER INSERT OR UPDATE OR DELETE ON reports FOR EACH ROW EXECUTE FUNCTION update_system_daily_stats();

-- 4. Initial Backfill (Last 90 days)
INSERT INTO system_daily_stats (date, new_users, total_uploads, new_reports, resolved_reports)
SELECT 
    d::date as date,
    (SELECT count(*) FROM users WHERE created_at::date = d::date) as new_users,
    (SELECT count(*) FROM cat_photos WHERE uploaded_at::date = d::date) as total_uploads,
    (SELECT count(*) FROM reports WHERE created_at::date = d::date) as new_reports,
    (SELECT count(*) FROM reports WHERE updated_at::date = d::date AND status = 'resolved') as resolved_reports
FROM generate_series(CURRENT_DATE - INTERVAL '90 days', CURRENT_DATE, INTERVAL '1 day') d
ON CONFLICT (date) DO UPDATE SET 
    new_users = EXCLUDED.new_users,
    total_uploads = EXCLUDED.total_uploads,
    new_reports = EXCLUDED.new_reports,
    resolved_reports = EXCLUDED.resolved_reports;
