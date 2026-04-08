-- Migration: 030_enforce_admin_rls_policies.sql
-- Description: สร้าง RLS Policies ที่เข้มงวดสำหรับตาราง admin ทั้งหมด
-- เพื่อป้องกันการเข้าถึงข้อมูลโดยตรงผ่าน Supabase client

-- ==========================================
-- 1. ROLES TABLE POLICIES
-- ==========================================
-- ลบ policy เก่าที่อนุญาต authenticated users อ่านได้ทั้งหมด
DROP POLICY IF EXISTS "Allow read access to roles for authenticated users" ON roles;

-- อนุญาตเฉพาะ users ที่มี role_id เป็น admin หรือ super_admin เท่านั้น
CREATE POLICY "Admin users can read roles"
ON roles FOR SELECT
USING (
    EXISTS (
        SELECT 1 FROM users u
        JOIN roles r ON u.role_id = r.id
        WHERE u.id = auth.uid()
        AND r.name IN ('admin', 'super_admin')
    )
    OR
    EXISTS (
        SELECT 1 FROM users u
        WHERE u.id = auth.uid()
        AND u.role IN ('admin', 'super_admin')
    )
);

-- อนุญาตเฉพาะ super_admin ในการแก้ไข roles
CREATE POLICY "Super admins can manage roles"
ON roles FOR ALL
USING (
    EXISTS (
        SELECT 1 FROM users u
        JOIN roles r ON u.role_id = r.id
        WHERE u.id = auth.uid()
        AND r.name = 'super_admin'
    )
    OR
    EXISTS (
        SELECT 1 FROM users u
        WHERE u.id = auth.uid()
        AND u.role = 'super_admin'
    )
);

-- ==========================================
-- 2. PERMISSIONS TABLE POLICIES
-- ==========================================
DROP POLICY IF EXISTS "Allow read access to permissions for authenticated users" ON permissions;

-- อนุญาตเฉพาะ admin users อ่าน permissions
CREATE POLICY "Admin users can read permissions"
ON permissions FOR SELECT
USING (
    EXISTS (
        SELECT 1 FROM users u
        JOIN roles r ON u.role_id = r.id
        WHERE u.id = auth.uid()
        AND r.name IN ('admin', 'super_admin')
    )
    OR
    EXISTS (
        SELECT 1 FROM users u
        WHERE u.id = auth.uid()
        AND u.role IN ('admin', 'super_admin')
    )
);

-- อนุญาตเฉพาะ super_admin ในการแก้ไข permissions
CREATE POLICY "Super admins can manage permissions"
ON permissions FOR ALL
USING (
    EXISTS (
        SELECT 1 FROM users u
        JOIN roles r ON u.role_id = r.id
        WHERE u.id = auth.uid()
        AND r.name = 'super_admin'
    )
    OR
    EXISTS (
        SELECT 1 FROM users u
        WHERE u.id = auth.uid()
        AND u.role = 'super_admin'
    )
);

-- ==========================================
-- 3. ROLE_PERMISSIONS TABLE POLICIES
-- ==========================================
-- อนุญาตเฉพาะ admin users อ่าน role_permissions
CREATE POLICY "Admin users can read role_permissions"
ON role_permissions FOR SELECT
USING (
    EXISTS (
        SELECT 1 FROM users u
        JOIN roles r ON u.role_id = r.id
        WHERE u.id = auth.uid()
        AND r.name IN ('admin', 'super_admin')
    )
    OR
    EXISTS (
        SELECT 1 FROM users u
        WHERE u.id = auth.uid()
        AND u.role IN ('admin', 'super_admin')
    )
);

-- อนุญาตเฉพาะ super_admin ในการแก้ไข role_permissions
CREATE POLICY "Super admins can manage role_permissions"
ON role_permissions FOR ALL
USING (
    EXISTS (
        SELECT 1 FROM users u
        JOIN roles r ON u.role_id = r.id
        WHERE u.id = auth.uid()
        AND r.name = 'super_admin'
    )
    OR
    EXISTS (
        SELECT 1 FROM users u
        WHERE u.id = auth.uid()
        AND u.role = 'super_admin'
    )
);

-- ==========================================
-- 4. AUDIT_LOGS TABLE POLICIES
-- ==========================================
-- อนุญาตเฉพาะ admin users อ่าน audit logs
CREATE POLICY "Admin users can read audit_logs"
ON audit_logs FOR SELECT
USING (
    EXISTS (
        SELECT 1 FROM users u
        JOIN roles r ON u.role_id = r.id
        WHERE u.id = auth.uid()
        AND r.name IN ('admin', 'super_admin')
    )
    OR
    EXISTS (
        SELECT 1 FROM users u
        WHERE u.id = auth.uid()
        AND u.role IN ('admin', 'super_admin')
    )
);

-- อนุญาตเฉพาะ service role ในการเขียน audit logs (ผ่าน backend)
-- ไม่อนุญาตให้ user ใดเขียนโดยตรง
CREATE POLICY "Service role can insert audit_logs"
ON audit_logs FOR INSERT
TO service_role
WITH CHECK (true);

-- ห้ามแก้ไขหรือลบบันทึก audit logs (immutable)
-- ไม่มี policy สำหรับ UPDATE/DELETE สำหรับ authenticated users

-- ==========================================
-- 5. SYSTEM_CONFIGS TABLE POLICIES
-- ==========================================
-- อนุญาตเฉพาะ admin users อ่าน system configs
CREATE POLICY "Admin users can read system_configs"
ON system_configs FOR SELECT
USING (
    EXISTS (
        SELECT 1 FROM users u
        JOIN roles r ON u.role_id = r.id
        WHERE u.id = auth.uid()
        AND r.name IN ('admin', 'super_admin')
    )
    OR
    EXISTS (
        SELECT 1 FROM users u
        WHERE u.id = auth.uid()
        AND u.role IN ('admin', 'super_admin')
    )
);

-- อนุญาตเฉพาะ admin users แก้ไข system configs
CREATE POLICY "Admin users can update system_configs"
ON system_configs FOR UPDATE
USING (
    EXISTS (
        SELECT 1 FROM users u
        JOIN roles r ON u.role_id = r.id
        WHERE u.id = auth.uid()
        AND r.name IN ('admin', 'super_admin')
    )
    OR
    EXISTS (
        SELECT 1 FROM users u
        WHERE u.id = auth.uid()
        AND u.role IN ('admin', 'super_admin')
    )
);

-- อนุญาตเฉพาะ service role ในการเพิ่ม system configs
CREATE POLICY "Service role can insert system_configs"
ON system_configs FOR INSERT
TO service_role
WITH CHECK (true);

-- ==========================================
-- 6. CONFIG_HISTORY TABLE POLICIES
-- ==========================================
-- อนุญาตเฉพาะ admin users อ่าน config history
CREATE POLICY "Admin users can read config_history"
ON config_history FOR SELECT
USING (
    EXISTS (
        SELECT 1 FROM users u
        JOIN roles r ON u.role_id = r.id
        WHERE u.id = auth.uid()
        AND r.name IN ('admin', 'super_admin')
    )
    OR
    EXISTS (
        SELECT 1 FROM users u
        WHERE u.id = auth.uid()
        AND u.role IN ('admin', 'super_admin')
    )
);

-- อนุญาตเฉพาะ service role ในการเขียน config history
CREATE POLICY "Service role can insert config_history"
ON config_history FOR INSERT
TO service_role
WITH CHECK (true);

-- ==========================================
-- 7. PENDING_CONFIG_CHANGES TABLE POLICIES
-- ==========================================
-- อนุญาตเฉพาะ admin users อ่าน pending config changes
CREATE POLICY "Admin users can read pending_config_changes"
ON pending_config_changes FOR SELECT
USING (
    EXISTS (
        SELECT 1 FROM users u
        JOIN roles r ON u.role_id = r.id
        WHERE u.id = auth.uid()
        AND r.name IN ('admin', 'super_admin')
    )
    OR
    EXISTS (
        SELECT 1 FROM users u
        WHERE u.id = auth.uid()
        AND u.role IN ('admin', 'super_admin')
    )
);

-- อนุญาตเฉพาะ admin users สร้าง pending config changes
CREATE POLICY "Admin users can create pending_config_changes"
ON pending_config_changes FOR INSERT
WITH CHECK (
    EXISTS (
        SELECT 1 FROM users u
        JOIN roles r ON u.role_id = r.id
        WHERE u.id = auth.uid()
        AND r.name IN ('admin', 'super_admin')
    )
    OR
    EXISTS (
        SELECT 1 FROM users u
        WHERE u.id = auth.uid()
        AND u.role IN ('admin', 'super_admin')
    )
);

-- อนุญาตเฉพาะ admin users อัปเดต pending config changes (approve/reject)
CREATE POLICY "Admin users can update pending_config_changes"
ON pending_config_changes FOR UPDATE
USING (
    EXISTS (
        SELECT 1 FROM users u
        JOIN roles r ON u.role_id = r.id
        WHERE u.id = auth.uid()
        AND r.name IN ('admin', 'super_admin')
    )
    OR
    EXISTS (
        SELECT 1 FROM users u
        WHERE u.id = auth.uid()
        AND u.role IN ('admin', 'super_admin')
    )
);

-- ==========================================
-- 8. INDEXES สำหรับประสิทธิภาพ
-- ==========================================
-- เพิ่ม index สำหรับ role-based access checks
CREATE INDEX IF NOT EXISTS idx_users_role_id ON users(role_id);
CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);

-- เพิ่ม index สำหรับ pending_config_changes
CREATE INDEX IF NOT EXISTS idx_pending_config_requester ON pending_config_changes(requester_id);
CREATE INDEX IF NOT EXISTS idx_pending_config_approver ON pending_config_changes(approver_id);
CREATE INDEX IF NOT EXISTS idx_pending_config_created_at ON pending_config_changes(created_at);

-- ==========================================
-- หมายเหตุสำคัญ:
-- ==========================================
-- 1. Policies เหล่านี้ใช้ทั้ง role_id (FK) และ role (legacy string column)
--    เพื่อรองรับการ migrate แบบ gradual
-- 2. Audit logs เป็น immutable - ไม่มี UPDATE/DELETE policy สำหรับ authenticated users
-- 3. Backend ใช้ service_role ซึ่ง bypass RLS policies เหล่านี้
-- 4. ควรทดสอบ policies เหล่านี้ใน staging environment ก่อน deploy ไป production
