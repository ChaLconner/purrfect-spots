-- Standardize permission codes to match frontend constants
UPDATE permissions SET code = 'audit:read' WHERE code = 'system:audit_logs';
UPDATE permissions SET code = 'system:settings' WHERE code = 'system:config';

-- Add missing permissions if they don't exist
INSERT INTO permissions (code, "group", description)
SELECT 'reports:read', 'moderation', 'Manage and view reports'
WHERE NOT EXISTS (SELECT 1 FROM permissions WHERE code = 'reports:read');

INSERT INTO permissions (code, "group", description)
SELECT 'reports:update', 'moderation', 'Update/Resolve reports'
WHERE NOT EXISTS (SELECT 1 FROM permissions WHERE code = 'reports:update');

INSERT INTO permissions (code, "group", description)
SELECT 'system:stats', 'dashboard', 'View system statistics'
WHERE NOT EXISTS (SELECT 1 FROM permissions WHERE code = 'system:stats');

INSERT INTO permissions (code, "group", description)
SELECT 'access:admin', 'general', 'Basic access to admin panel'
WHERE NOT EXISTS (SELECT 1 FROM permissions WHERE code = 'access:admin');

-- Also add users:write if missing (matches PERMISSIONS.USERS_WRITE)
INSERT INTO permissions (code, "group", description)
SELECT 'users:write', 'user_management', 'Create/write user data'
WHERE NOT EXISTS (SELECT 1 FROM permissions WHERE code = 'users:write');

-- Ensure admin role has all permissions
DO $$
DECLARE
    admin_role_id UUID;
BEGIN
    SELECT id INTO admin_role_id FROM roles WHERE name = 'admin' LIMIT 1;
    
    INSERT INTO role_permissions (role_id, permission_id)
    SELECT admin_role_id, id FROM permissions
    ON CONFLICT (role_id, permission_id) DO NOTHING;
END $$;
