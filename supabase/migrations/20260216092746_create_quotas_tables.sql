CREATE TABLE IF NOT EXISTS user_daily_quotas (
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    date DATE DEFAULT CURRENT_DATE,
    upload_count INTEGER DEFAULT 0,
    PRIMARY KEY (user_id, date)
);
CREATE INDEX IF NOT EXISTS idx_user_daily_quotas_date ON user_daily_quotas(date);

CREATE TABLE IF NOT EXISTS system_daily_stats (
    date DATE PRIMARY KEY DEFAULT CURRENT_DATE,
    total_uploads INTEGER DEFAULT 0
);
