-- Drop duplicate indexes on treats_transactions
DROP INDEX IF EXISTS idx_treats_from;
DROP INDEX IF EXISTS idx_treats_to;

-- Drop confirmed unused indexes (as reported by pg_stat_user_indexes via linter)
DROP INDEX IF EXISTS idx_users_username;
DROP INDEX IF EXISTS idx_reports_updated_at;
DROP INDEX IF EXISTS idx_audit_logs_user_id;
DROP INDEX IF EXISTS idx_audit_logs_action;
DROP INDEX IF EXISTS idx_saved_spots_user;
DROP INDEX IF EXISTS idx_vision_cache_timestamp;
DROP INDEX IF EXISTS idx_user_daily_quotas_date;
DROP INDEX IF EXISTS idx_reports_comment_id;

