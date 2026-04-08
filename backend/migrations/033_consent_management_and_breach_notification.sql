-- Migration: 033_consent_management_and_breach_notification.sql
-- Description: สร้างตารางสำหรับ Consent Management และ Breach Notification Systems
-- เพื่อปฏิบัติตาม PDPA/GDPR requirements

-- ==========================================
-- 1. CONSENT MANAGEMENT TABLES
-- ==========================================

-- Consent policy versions table
CREATE TABLE IF NOT EXISTS consent_versions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    consent_type VARCHAR(50) NOT NULL,
    version VARCHAR(20) NOT NULL,
    content_hash VARCHAR(64),
    effective_date TIMESTAMPTZ NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(consent_type, version)
);

-- User consent records table
CREATE TABLE IF NOT EXISTS user_consents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    consent_type VARCHAR(50) NOT NULL,
    granted BOOLEAN NOT NULL,
    granted_at TIMESTAMPTZ DEFAULT NOW(),
    ip_address INET,
    user_agent TEXT,
    version VARCHAR(20),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ==========================================
-- 2. USERS TABLE EXTENSIONS FOR CONSENT
-- ==========================================
ALTER TABLE users
    ADD COLUMN IF NOT EXISTS tos_accepted BOOLEAN DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS privacy_accepted BOOLEAN DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS marketing_opt_in BOOLEAN DEFAULT FALSE;

-- ==========================================
-- 3. BREACH NOTIFICATION / INCIDENT TABLES
-- ==========================================

-- Security incidents table
CREATE TABLE IF NOT EXISTS security_incidents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    incident_type VARCHAR(50) NOT NULL,
    severity VARCHAR(20) NOT NULL CHECK (severity IN ('low', 'medium', 'high', 'critical')),
    description TEXT NOT NULL,
    reported_by UUID REFERENCES users(id) ON DELETE SET NULL,
    status VARCHAR(30) NOT NULL DEFAULT 'investigating' CHECK (status IN ('investigating', 'contained', 'resolved', 'false_positive')),
    detected_at TIMESTAMPTZ DEFAULT NOW(),
    resolved_at TIMESTAMPTZ,
    resolved_by UUID REFERENCES users(id) ON DELETE SET NULL,
    ip_address INET,
    affected_user_count INTEGER DEFAULT 0,
    sla_breached BOOLEAN DEFAULT FALSE,
    sla_breached_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Incident affected users (many-to-many)
CREATE TABLE IF NOT EXISTS incident_affected_users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    incident_id UUID REFERENCES security_incidents(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    notified BOOLEAN DEFAULT FALSE,
    notified_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(incident_id, user_id)
);

-- Incident timeline
CREATE TABLE IF NOT EXISTS incident_timeline (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    incident_id UUID REFERENCES security_incidents(id) ON DELETE CASCADE,
    action VARCHAR(255) NOT NULL,
    notes TEXT,
    updated_by UUID REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ==========================================
-- 4. INDEXES
-- ==========================================
CREATE INDEX IF NOT EXISTS idx_user_consents_user_id ON user_consents(user_id);
CREATE INDEX IF NOT EXISTS idx_user_consents_type ON user_consents(consent_type);
CREATE INDEX IF NOT EXISTS idx_user_consents_granted_at ON user_consents(granted_at DESC);

CREATE INDEX IF NOT EXISTS idx_consent_versions_type_active ON consent_versions(consent_type, is_active);

CREATE INDEX IF NOT EXISTS idx_security_incidents_status ON security_incidents(status);
CREATE INDEX IF NOT EXISTS idx_security_incidents_severity ON security_incidents(severity);
CREATE INDEX IF NOT EXISTS idx_security_incidents_detected ON security_incidents(detected_at DESC);
CREATE INDEX IF NOT EXISTS idx_security_incidents_sla ON security_incidents(sla_breached) WHERE sla_breached = FALSE;

CREATE INDEX IF NOT EXISTS idx_incident_affected_incident ON incident_affected_users(incident_id);
CREATE INDEX IF NOT EXISTS idx_incident_affected_user ON incident_affected_users(user_id);

CREATE INDEX IF NOT EXISTS idx_incident_timeline_incident ON incident_timeline(incident_id);

-- ==========================================
-- 5. RLS POLICIES
-- ==========================================
ALTER TABLE consent_versions ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_consents ENABLE ROW LEVEL SECURITY;
ALTER TABLE security_incidents ENABLE ROW LEVEL SECURITY;
ALTER TABLE incident_affected_users ENABLE ROW LEVEL SECURITY;
ALTER TABLE incident_timeline ENABLE ROW LEVEL SECURITY;

-- Consent versions: publicly readable
CREATE POLICY "Consent versions are publicly readable"
ON consent_versions FOR SELECT USING (true);

-- User consents: users can read their own
CREATE POLICY "Users can read own consents"
ON user_consents FOR SELECT USING (auth.uid() = user_id);

-- User consents: users can insert their own
CREATE POLICY "Users can insert own consents"
ON user_consents FOR INSERT WITH CHECK (auth.uid() = user_id);

-- User consents: admin can read all
CREATE POLICY "Admins can read all consents"
ON user_consents FOR SELECT USING (
    EXISTS (
        SELECT 1 FROM users u
        WHERE u.id = auth.uid()
        AND u.role IN ('admin', 'super_admin')
    )
);

-- Security incidents: admin only
CREATE POLICY "Admins can manage incidents"
ON security_incidents FOR ALL USING (
    EXISTS (
        SELECT 1 FROM users u
        WHERE u.id = auth.uid()
        AND u.role IN ('admin', 'super_admin')
    )
);

-- Incident affected users: admin only
CREATE POLICY "Admins can manage incident affected users"
ON incident_affected_users FOR ALL USING (
    EXISTS (
        SELECT 1 FROM users u
        WHERE u.id = auth.uid()
        AND u.role IN ('admin', 'super_admin')
    )
);

-- Incident timeline: admin only
CREATE POLICY "Admins can manage incident timeline"
ON incident_timeline FOR ALL USING (
    EXISTS (
        SELECT 1 FROM users u
        WHERE u.id = auth.uid()
        AND u.role IN ('admin', 'super_admin')
    )
);

-- ==========================================
-- 6. FUNCTIONS
-- ==========================================

-- Check incident SLA breaches
CREATE OR REPLACE FUNCTION check_incident_sla_breaches()
RETURNS TABLE(
    incident_id UUID,
    incident_type VARCHAR,
    severity VARCHAR,
    detected_at TIMESTAMPTZ,
    hours_elapsed NUMERIC,
    response_time_hours INTEGER,
    is_breached BOOLEAN
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        si.id,
        si.incident_type,
        si.severity,
        si.detected_at,
        EXTRACT(EPOCH FROM (NOW() - si.detected_at)) / 3600 AS hours_elapsed,
        CASE si.severity
            WHEN 'critical' THEN 1
            WHEN 'high' THEN 24
            WHEN 'medium' THEN 48
            WHEN 'low' THEN 72
            ELSE 72
        END AS response_time_hours,
        CASE 
            WHEN si.status = 'resolved' THEN FALSE
            WHEN si.severity = 'critical' AND EXTRACT(EPOCH FROM (NOW() - si.detected_at)) / 3600 > 1 THEN TRUE
            WHEN si.severity = 'high' AND EXTRACT(EPOCH FROM (NOW() - si.detected_at)) / 3600 > 24 THEN TRUE
            WHEN si.severity = 'medium' AND EXTRACT(EPOCH FROM (NOW() - si.detected_at)) / 3600 > 48 THEN TRUE
            WHEN si.severity = 'low' AND EXTRACT(EPOCH FROM (NOW() - si.detected_at)) / 3600 > 72 THEN TRUE
            ELSE FALSE
        END AS is_breached
    FROM security_incidents si
    WHERE si.status != 'resolved'
    ORDER BY si.severity ASC, si.detected_at ASC;
END;
$$ LANGUAGE plpgsql;

-- Auto-update SLA breach status
CREATE OR REPLACE FUNCTION update_incident_sla_status() RETURNS TRIGGER AS $$
BEGIN
    UPDATE security_incidents
    SET 
        sla_breached = TRUE,
        sla_breached_at = NOW()
    WHERE status != 'resolved'
    AND sla_breached = FALSE
    AND (
        (severity = 'critical' AND NOW() - detected_at > INTERVAL '1 hour') OR
        (severity = 'high' AND NOW() - detected_at > INTERVAL '24 hours') OR
        (severity = 'medium' AND NOW() - detected_at > INTERVAL '48 hours') OR
        (severity = 'low' AND NOW() - detected_at > INTERVAL '72 hours')
    );
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_update_incident_sla ON security_incidents;
CREATE TRIGGER trg_update_incident_sla
    AFTER INSERT OR UPDATE ON security_incidents
    FOR EACH STATEMENT
    EXECUTE FUNCTION update_incident_sla_status();

-- ==========================================
-- 7. SEED DATA - Default consent versions
-- ==========================================
INSERT INTO consent_versions (consent_type, version, effective_date, is_active)
VALUES 
    ('tos', '1.0', NOW(), TRUE),
    ('privacy', '1.0', NOW(), TRUE),
    ('marketing', '1.0', NOW(), TRUE),
    ('data_processing', '1.0', NOW(), TRUE),
    ('cookies', '1.0', NOW(), TRUE)
ON CONFLICT (consent_type, version) DO NOTHING;

-- ==========================================
-- หมายเหตุสำคัญ:
-- ==========================================
-- 1. Consent Management ติดตามการยินยอมของผู้ใช้ตาม PDPA/GDPR
-- 2. Breach Notification จัดการ incident และแจ้งเตือนตาม severity
-- 3. SLA response times: critical=1h, high=24h, medium=48h, low=72h
-- 4. Function check_incident_sla_breaches() ใช้ตรวจสอบ SLA violations
-- 5. RLS policies ป้องกันการเข้าถึงข้อมูล consent และ incident โดยไม่ได้รับอนุญาต
