
ALTER TABLE user_daily_quotas DROP CONSTRAINT IF EXISTS user_daily_quotas_user_id_fkey;
ALTER TABLE user_daily_quotas ADD CONSTRAINT user_daily_quotas_user_id_fkey FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;

