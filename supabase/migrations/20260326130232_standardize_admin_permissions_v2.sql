-- Add missing permissions if they don't exist
INSERT INTO permissions (code, "group", description)
SELECT 'content:write', 'content_management', 'Update photo details'
WHERE NOT EXISTS (SELECT 1 FROM permissions WHERE code = 'content:write');

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
