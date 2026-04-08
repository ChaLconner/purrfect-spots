-- Migration: Admin Dashboard Performance Indexes
-- Description: Adds missing indexes for columns frequently used in filtering and aggregation to ensure sub-second latency.

-- 1. Treat Transactions filtering and sorting
CREATE INDEX IF NOT EXISTS idx_treats_transactions_type ON treats_transactions(transaction_type);
CREATE INDEX IF NOT EXISTS idx_treats_transactions_created_at ON treats_transactions(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_treats_transactions_from_user ON treats_transactions(from_user_id) WHERE from_user_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_treats_transactions_to_user ON treats_transactions(to_user_id) WHERE to_user_id IS NOT NULL;

-- 2. Reports correlation with comments
CREATE INDEX IF NOT EXISTS idx_reports_comment_id ON reports(comment_id) WHERE comment_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_reports_status_created ON reports(status, created_at DESC);

-- 3. System Config History
CREATE INDEX IF NOT EXISTS idx_config_history_key ON config_history(config_key);
CREATE INDEX IF NOT EXISTS idx_pending_config_status ON pending_config_changes(status);

-- 4. User and Photo Comments optimization (redundant with FKeys but good for explicit performance targeting)
CREATE INDEX IF NOT EXISTS idx_photo_comments_created_at ON photo_comments(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_users_banned_at ON users(banned_at) WHERE banned_at IS NOT NULL;
