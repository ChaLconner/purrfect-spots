-- Migration: Backfill tracked admin settings workflow schema
-- Description: Ensures the admin settings approval tables and columns exist for
-- both fresh databases and environments that already applied older migrations.

ALTER TABLE system_configs
    ADD COLUMN IF NOT EXISTS category VARCHAR(50) DEFAULT 'general',
    ADD COLUMN IF NOT EXISTS is_encrypted BOOLEAN DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS requires_approval BOOLEAN DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS updated_by UUID REFERENCES users(id) ON DELETE SET NULL;

UPDATE system_configs SET category = 'general' WHERE category IS NULL;
UPDATE system_configs SET is_encrypted = FALSE WHERE is_encrypted IS NULL;
UPDATE system_configs SET requires_approval = FALSE WHERE requires_approval IS NULL;

ALTER TABLE system_configs ALTER COLUMN category SET DEFAULT 'general';
ALTER TABLE system_configs ALTER COLUMN category SET NOT NULL;
ALTER TABLE system_configs ALTER COLUMN is_encrypted SET DEFAULT FALSE;
ALTER TABLE system_configs ALTER COLUMN is_encrypted SET NOT NULL;
ALTER TABLE system_configs ALTER COLUMN requires_approval SET DEFAULT FALSE;
ALTER TABLE system_configs ALTER COLUMN requires_approval SET NOT NULL;

CREATE TABLE IF NOT EXISTS config_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    config_key VARCHAR(100) NOT NULL REFERENCES system_configs(key) ON DELETE CASCADE,
    old_value JSONB,
    new_value JSONB,
    changed_by UUID REFERENCES users(id) ON DELETE SET NULL,
    change_reason TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS pending_config_changes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    config_key VARCHAR(100) NOT NULL REFERENCES system_configs(key) ON DELETE CASCADE,
    proposed_value JSONB NOT NULL,
    requester_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    approver_id UUID REFERENCES users(id) ON DELETE SET NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'approved', 'rejected')),
    rejection_reason TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE config_history ENABLE ROW LEVEL SECURITY;
ALTER TABLE pending_config_changes ENABLE ROW LEVEL SECURITY;

CREATE INDEX IF NOT EXISTS idx_config_history_key ON config_history(config_key);
CREATE INDEX IF NOT EXISTS idx_pending_config_status ON pending_config_changes(status);
