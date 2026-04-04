-- Migration: 031_audit_log_integrity.sql
-- Description: เพิ่ม hash chain สำหรับ audit logs เพื่อป้องกันการแก้ไข
-- และเพิ่ม audit log retention policy

-- ==========================================
-- 1. เพิ่ม columns สำหรับ hash chain
-- ==========================================
ALTER TABLE audit_logs
    ADD COLUMN IF NOT EXISTS previous_hash VARCHAR(64),
    ADD COLUMN IF NOT EXISTS entry_hash VARCHAR(64),
    ADD COLUMN IF NOT EXISTS is_locked BOOLEAN DEFAULT FALSE;

-- สร้าง index สำหรับ hash lookups
CREATE INDEX IF NOT EXISTS idx_audit_logs_entry_hash ON audit_logs(entry_hash);
CREATE INDEX IF NOT EXISTS idx_audit_logs_previous_hash ON audit_logs(previous_hash);

-- ==========================================
-- 2. สร้าง function สำหรับ hash chain
-- ==========================================
CREATE OR REPLACE FUNCTION generate_audit_hash(
    p_id UUID,
    p_user_id UUID,
    p_action VARCHAR,
    p_resource VARCHAR,
    p_changes JSONB,
    p_created_at TIMESTAMPTZ
) RETURNS VARCHAR AS $$
DECLARE
    hash_input TEXT;
BEGIN
    hash_input := p_id::TEXT || '|' || 
                  COALESCE(p_user_id::TEXT, '') || '|' || 
                  p_action || '|' || 
                  p_resource || '|' || 
                  COALESCE(p_changes::TEXT, '') || '|' || 
                  p_created_at::TEXT;
    RETURN encode(sha256(hash_input::bytea), 'hex');
END;
$$ LANGUAGE plpgsql;

-- ==========================================
-- 3. สร้าง trigger สำหรับ auto-generate hash
-- ==========================================
CREATE OR REPLACE FUNCTION audit_log_hash_trigger() RETURNS TRIGGER AS $$
DECLARE
    prev_hash VARCHAR(64);
BEGIN
    -- หา hash ของ record ก่อนหน้า (เรียงตาม created_at)
    SELECT entry_hash INTO prev_hash
    FROM audit_logs
    WHERE id != NEW.id
    ORDER BY created_at DESC, id DESC
    LIMIT 1;

    -- ถ้าไม่มี record ก่อนหน้า ใช้ genesis hash
    IF prev_hash IS NULL THEN
        prev_hash := encode(sha256('genesis'::bytea), 'hex');
    END IF;

    NEW.previous_hash := prev_hash;
    NEW.entry_hash := generate_audit_hash(
        NEW.id, NEW.user_id, NEW.action, NEW.resource, NEW.changes, NEW.created_at
    );

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- ลบ trigger เก่าถ้ามี
DROP TRIGGER IF EXISTS trg_audit_log_hash ON audit_logs;

-- สร้าง trigger ใหม่
CREATE TRIGGER trg_audit_log_hash
    BEFORE INSERT ON audit_logs
    FOR EACH ROW
    EXECUTE FUNCTION audit_log_hash_trigger();

-- ==========================================
-- 4. ป้องกันการแก้ไข audit logs (immutable)
-- ==========================================
CREATE OR REPLACE FUNCTION prevent_audit_log_update() RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'UPDATE' THEN
        -- อนุญาตให้แก้ไขเฉพาะ is_locked flag เท่านั้น
        IF OLD.id != NEW.id OR 
           OLD.user_id IS DISTINCT FROM NEW.user_id OR
           OLD.action != NEW.action OR
           OLD.resource != NEW.resource OR
           OLD.changes IS DISTINCT FROM NEW.changes OR
           OLD.ip_address IS DISTINCT FROM NEW.ip_address OR
           OLD.user_agent IS DISTINCT FROM NEW.user_agent OR
           OLD.created_at != NEW.created_at OR
           OLD.entry_hash != NEW.entry_hash OR
           OLD.previous_hash != NEW.previous_hash THEN
            RAISE EXCEPTION 'Audit logs are immutable. Cannot modify core fields.';
        END IF;
    END IF;
    
    IF TG_OP = 'DELETE' THEN
        RAISE EXCEPTION 'Audit logs cannot be deleted.';
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_prevent_audit_update ON audit_logs;
CREATE TRIGGER trg_prevent_audit_update
    BEFORE UPDATE OR DELETE ON audit_logs
    FOR EACH ROW
    EXECUTE FUNCTION prevent_audit_log_update();

-- ==========================================
-- 5. สร้าง function สำหรับ verify hash chain
-- ==========================================
CREATE OR REPLACE FUNCTION verify_audit_log_integrity()
RETURNS TABLE(
    id UUID,
    is_valid BOOLEAN,
    expected_hash VARCHAR,
    actual_hash VARCHAR,
    chain_valid BOOLEAN
) AS $$
DECLARE
    rec RECORD;
    prev_hash VARCHAR(64);
    expected_entry_hash VARCHAR(64);
    chain_broken BOOLEAN := FALSE;
BEGIN
    FOR rec IN SELECT * FROM audit_logs ORDER BY created_at ASC, id ASC LOOP
        -- ตรวจสอบ hash ของ entry
        expected_entry_hash := generate_audit_hash(
            rec.id, rec.user_id, rec.action, rec.resource, rec.changes, rec.created_at
        );
        
        -- ตรวจสอบ previous hash chain
        IF prev_hash IS NOT NULL AND rec.previous_hash != prev_hash THEN
            chain_broken := TRUE;
        END IF;
        
        RETURN QUERY SELECT 
            rec.id,
            rec.entry_hash = expected_entry_hash,
            expected_entry_hash,
            rec.entry_hash,
            NOT chain_broken;
        
        prev_hash := rec.entry_hash;
    END LOOP;
END;
$$ LANGUAGE plpgsql;

-- ==========================================
-- 6. Audit Log Retention Policy
-- ==========================================
-- สร้าง function สำหรับลบ audit logs เก่า (เก็บไว้ 1 ปี)
-- หมายเหตุ: ต้องปลดล็อก is_locked ก่อนลบ หรือลบเฉพาะที่ unlock แล้ว
CREATE OR REPLACE FUNCTION cleanup_old_audit_logs(
    retention_days INTEGER DEFAULT 365
) RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
    cutoff_date TIMESTAMPTZ;
BEGIN
    cutoff_date := NOW() - (retention_days || ' days')::INTERVAL;
    
    -- ลบเฉพาะ audit logs ที่ไม่ได้ lock ไว้และเก่ากว่า retention period
    DELETE FROM audit_logs 
    WHERE created_at < cutoff_date 
    AND (is_locked IS NULL OR is_locked = FALSE);
    
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- ==========================================
-- หมายเหตุสำคัญ:
-- ==========================================
-- 1. Hash chain ทำให้สามารถตรวจจับการแก้ไข audit logs ได้
-- 2. Trigger trg_prevent_audit_update ป้องกันการแก้ไข core fields
-- 3. Function verify_audit_log_integrity() ใช้ตรวจสอบความสมบูรณ์ของ logs
-- 4. Function cleanup_old_audit_logs() ใช้ลบ logs เก่าตาม retention policy
-- 5. ควรเรียก verify_audit_log_integrity() เป็นประจำ (เช่น ทุกวัน)
