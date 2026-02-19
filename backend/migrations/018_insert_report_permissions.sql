-- Migration: Add Report Permissions for Moderation

-- 1. Insert new permissions into the permissions table
INSERT INTO permissions (code, "group", description)
VALUES 
    ('reports:read', 'Moderation', 'Can view user reports'),
    ('reports:update', 'Moderation', 'Can resolve or dismiss reports')
ON CONFLICT (code) DO NOTHING;

-- 2. Retrieve Role IDs for 'admin', 'moderator', and 'super_admin'
-- Assign permissions to roles
DO $$
DECLARE
    role_admin UUID;
    role_mod UUID;
    role_super UUID;
    perm_read UUID;
    perm_update UUID;
BEGIN
    -- Get Role IDs
    SELECT id INTO role_admin FROM roles WHERE name = 'admin';
    SELECT id INTO role_mod FROM roles WHERE name = 'moderator';
    SELECT id INTO role_super FROM roles WHERE name = 'super_admin';

    -- Get Permission IDs
    SELECT id INTO perm_read FROM permissions WHERE code = 'reports:read';
    SELECT id INTO perm_update FROM permissions WHERE code = 'reports:update';

    -- Assign 'reports:read' to admin, moderator, super_admin
    IF perm_read IS NOT NULL THEN
        RAISE NOTICE 'Assigning reports:read permission...';
        
        IF role_admin IS NOT NULL THEN
            INSERT INTO role_permissions (role_id, permission_id) VALUES (role_admin, perm_read) ON CONFLICT DO NOTHING;
        END IF;
        
        IF role_mod IS NOT NULL THEN
             INSERT INTO role_permissions (role_id, permission_id) VALUES (role_mod, perm_read) ON CONFLICT DO NOTHING;
        END IF;

        IF role_super IS NOT NULL THEN
             INSERT INTO role_permissions (role_id, permission_id) VALUES (role_super, perm_read) ON CONFLICT DO NOTHING;
        END IF;
    END IF;

    -- Assign 'reports:update' to admin, moderator, super_admin
    IF perm_update IS NOT NULL THEN
        RAISE NOTICE 'Assigning reports:update permission...';

        IF role_admin IS NOT NULL THEN
            INSERT INTO role_permissions (role_id, permission_id) VALUES (role_admin, perm_update) ON CONFLICT DO NOTHING;
        END IF;
        
         IF role_mod IS NOT NULL THEN
            INSERT INTO role_permissions (role_id, permission_id) VALUES (role_mod, perm_update) ON CONFLICT DO NOTHING;
        END IF;

        IF role_super IS NOT NULL THEN
            INSERT INTO role_permissions (role_id, permission_id) VALUES (role_super, perm_update) ON CONFLICT DO NOTHING;
        END IF;
    END IF;

END $$;
