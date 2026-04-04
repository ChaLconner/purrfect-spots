-- Migration: 032_pending_config_sla_and_indexes.sql
-- Description: เพิ่ม SLA tracking สำหรับ Maker-Checker workflow และ performance indexes

-- ==========================================
-- 1. เพิ่ม columns สำหรับ SLA tracking
-- ==========================================
ALTER TABLE pending_config_changes
    ADD COLUMN IF NOT EXISTS sla_deadline TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS sla_breached BOOLEAN DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS sla_breached_at TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS priority VARCHAR(20) DEFAULT 'normal' CHECK (priority IN ('low', 'normal', 'high', 'critical'));

-- ==========================================
-- 2. สร้าง function สำหรับคำนวณ SLA deadline
-- ==========================================
CREATE OR REPLACE FUNCTION calculate_sla_deadline(
    p_priority VARCHAR,
    p_created_at TIMESTAMPTZ DEFAULT NOW()
) RETURNS TIMESTAMPTZ AS $$
BEGIN
    RETURN CASE p_priority
        WHEN 'critical' THEN p_created_at + INTERVAL '1 hour'
        WHEN 'high' THEN p_created_at + INTERVAL '4 hours'
        WHEN 'normal' THEN p_created_at + INTERVAL '24 hours'
        WHEN 'low' THEN p_created_at + INTERVAL '72 hours'
        ELSE p_created_at + INTERVAL '24 hours'
    END;
END;
$$ LANGUAGE plpgsql;

-- ==========================================
-- 3. สร้าง trigger สำหรับ auto-set SLA deadline
-- ==========================================
CREATE OR REPLACE FUNCTION pending_config_sla_trigger() RETURNS TRIGGER AS $$
BEGIN
    -- Set SLA deadline based on priority
    NEW.sla_deadline := calculate_sla_deadline(
        COALESCE(NEW.priority, 'normal'),
        COALESCE(NEW.created_at, NOW())
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_pending_config_sla ON pending_config_changes;
CREATE TRIGGER trg_pending_config_sla
    BEFORE INSERT OR UPDATE OF priority ON pending_config_changes
    FOR EACH ROW
    EXECUTE FUNCTION pending_config_sla_trigger();

-- ==========================================
-- 4. สร้าง function สำหรับตรวจสอบ SLA breach
-- ==========================================
CREATE OR REPLACE FUNCTION check_sla_breaches()
RETURNS TABLE(
    change_id UUID,
    config_key VARCHAR,
    priority VARCHAR,
    sla_deadline TIMESTAMPTZ,
    hours_overdue NUMERIC,
    requester_email VARCHAR
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        pc.id,
        pc.config_key,
        pc.priority,
        pc.sla_deadline,
        EXTRACT(EPOCH FROM (NOW() - pc.sla_deadline)) / 3600 AS hours_overdue,
        u.email AS requester_email
    FROM pending_config_changes pc
    JOIN users u ON pc.requester_id = u.id
    WHERE pc.status = 'pending'
    AND pc.sla_deadline < NOW()
    ORDER BY pc.sla_deadline ASC;
END;
$$ LANGUAGE plpgsql;

-- ==========================================
-- 5. สร้าง function สำหรับอัปเดต SLA breach status
-- ==========================================
CREATE OR REPLACE FUNCTION update_sla_breach_status() RETURNS VOID AS $$
BEGIN
    UPDATE pending_config_changes
    SET 
        sla_breached = TRUE,
        sla_breached_at = NOW()
    WHERE status = 'pending'
    AND sla_deadline < NOW()
    AND (sla_breached IS NULL OR sla_breached = FALSE);
END;
$$ LANGUAGE plpgsql;

-- ==========================================
-- 6. Performance Indexes สำหรับ admin queries
-- ==========================================
-- Audit logs composite indexes
CREATE INDEX IF NOT EXISTS idx_audit_logs_user_action ON audit_logs(user_id, action);
CREATE INDEX IF NOT EXISTS idx_audit_logs_resource_action ON audit_logs(resource, action);
CREATE INDEX IF NOT EXISTS idx_audit_logs_created_desc ON audit_logs(created_at DESC);

-- Reports indexes
CREATE INDEX IF NOT EXISTS idx_reports_status_created ON reports(status, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_reports_photo_id ON reports(photo_id);
CREATE INDEX IF NOT EXISTS idx_reports_comment_id ON reports(comment_id);
CREATE INDEX IF NOT EXISTS idx_reports_reporter_id ON reports(reporter_id);

-- Cat_photos indexes
CREATE INDEX IF NOT EXISTS idx_cat_photos_user_id_desc ON cat_photos(user_id, uploaded_at DESC);

-- Treats transactions indexes
CREATE INDEX IF NOT EXISTS idx_treats_transactions_type ON treats_transactions(transaction_type);
CREATE INDEX IF NOT EXISTS idx_treats_transactions_created ON treats_transactions(created_at DESC);

-- Users indexes
CREATE INDEX IF NOT EXISTS idx_users_banned_at ON users(banned_at) WHERE banned_at IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_users_is_pro ON users(is_pro);

-- ==========================================
-- 7. View สำหรับ admin dashboard monitoring
-- ==========================================
CREATE OR REPLACE VIEW admin_security_dashboard AS
SELECT 
    (SELECT COUNT(*) FROM users) AS total_users,
    (SELECT COUNT(*) FROM users WHERE banned_at IS NOT NULL) AS banned_users,
    (SELECT COUNT(*) FROM cat_photos) AS total_photos,
    (SELECT COUNT(*) FROM reports WHERE status = 'pending') AS pending_reports,
    (SELECT COUNT(*) FROM reports WHERE status = 'resolved') AS resolved_reports,
    (SELECT COUNT(*) FROM reports WHERE status = 'dismissed') AS dismissed_reports,
    (SELECT COUNT(*) FROM pending_config_changes WHERE status = 'pending') AS pending_config_changes,
    (SELECT COUNT(*) FROM pending_config_changes WHERE sla_breached = TRUE) AS breached_sla_changes,
    (SELECT COUNT(*) FROM audit_logs WHERE created_at > NOW() - INTERVAL '24 hours') AS audit_logs_24h,
    (SELECT COUNT(*) FROM users WHERE created_at > NOW() - INTERVAL '24 hours') AS new_users_24h,
    (SELECT COUNT(*) FROM cat_photos WHERE uploaded_at > NOW() - INTERVAL '24 hours') AS new_photos_24h;

-- ==========================================
-- หมายเหตุสำคัญ:
-- ==========================================
-- 1. SLA deadlines คำนวณอัตโนมัติตาม priority
-- 2. Function check_sla_breaches() ใช้ตรวจสอบการละเมิด SLA
-- 3. Function update_sla_breach_status() ใช้อัปเดต status เป็น breached
-- 4. View admin_security_dashboard ใช้สำหรับ monitoring
-- 5. ควรเรียก update_sla_breach_status() ทุกชั่วโมงผ่าน cron job
