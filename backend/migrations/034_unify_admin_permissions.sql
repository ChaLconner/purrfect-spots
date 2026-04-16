-- Migration: unify canonical admin permissions and map legacy aliases

BEGIN;

INSERT INTO permissions (code, "group", description)
VALUES
    ('users:read', 'User Management', 'View user list and details'),
    ('users:write', 'User Management', 'Edit user profile details'),
    ('users:update', 'User Management', 'Update user roles and moderation state'),
    ('users:delete', 'User Management', 'Delete or anonymize user accounts'),
    ('content:read', 'Content Management', 'View all uploaded content'),
    ('content:write', 'Content Management', 'Edit uploaded content metadata'),
    ('content:delete', 'Content Management', 'Delete uploaded content'),
    ('reports:read', 'Moderation', 'View user reports'),
    ('reports:update', 'Moderation', 'Resolve or dismiss reports'),
    ('system:stats', 'System', 'View dashboard and security statistics'),
    ('system:settings', 'System', 'Manage system settings'),
    ('audit:read', 'System', 'View audit logs'),
    ('treats:manage', 'Treats', 'Manage treats balances and transactions'),
    ('comments:manage', 'Moderation', 'Manage comments'),
    ('roles:read', 'Role Management', 'View roles'),
    ('roles:manage', 'Role Management', 'Manage role permissions'),
    ('access:admin', 'Access Control', 'Full admin shell access bypass')
ON CONFLICT (code) DO UPDATE
SET
    "group" = EXCLUDED."group",
    description = EXCLUDED.description;

WITH legacy AS (
    SELECT id FROM permissions WHERE code = 'admin_access'
),
canonical AS (
    SELECT id FROM permissions WHERE code = 'access:admin'
)
INSERT INTO role_permissions (role_id, permission_id)
SELECT rp.role_id, canonical.id
FROM role_permissions rp
CROSS JOIN canonical
WHERE rp.permission_id IN (SELECT id FROM legacy)
ON CONFLICT DO NOTHING;

DELETE FROM role_permissions
WHERE permission_id IN (SELECT id FROM permissions WHERE code = 'admin_access');

DELETE FROM permissions WHERE code = 'admin_access';

WITH legacy AS (
    SELECT id FROM permissions WHERE code = 'system:audit_logs'
),
canonical AS (
    SELECT id FROM permissions WHERE code = 'audit:read'
)
INSERT INTO role_permissions (role_id, permission_id)
SELECT rp.role_id, canonical.id
FROM role_permissions rp
CROSS JOIN canonical
WHERE rp.permission_id IN (SELECT id FROM legacy)
ON CONFLICT DO NOTHING;

DELETE FROM role_permissions
WHERE permission_id IN (SELECT id FROM permissions WHERE code = 'system:audit_logs');

DELETE FROM permissions WHERE code = 'system:audit_logs';

WITH legacy AS (
    SELECT id FROM permissions WHERE code = 'system:config'
),
canonical AS (
    SELECT id FROM permissions WHERE code = 'system:settings'
)
INSERT INTO role_permissions (role_id, permission_id)
SELECT rp.role_id, canonical.id
FROM role_permissions rp
CROSS JOIN canonical
WHERE rp.permission_id IN (SELECT id FROM legacy)
ON CONFLICT DO NOTHING;

DELETE FROM role_permissions
WHERE permission_id IN (SELECT id FROM permissions WHERE code = 'system:config');

DELETE FROM permissions WHERE code = 'system:config';

WITH legacy AS (
    SELECT id FROM permissions WHERE code = 'users:create'
),
canonical AS (
    SELECT id FROM permissions WHERE code = 'users:write'
)
INSERT INTO role_permissions (role_id, permission_id)
SELECT rp.role_id, canonical.id
FROM role_permissions rp
CROSS JOIN canonical
WHERE rp.permission_id IN (SELECT id FROM legacy)
ON CONFLICT DO NOTHING;

DELETE FROM role_permissions
WHERE permission_id IN (SELECT id FROM permissions WHERE code = 'users:create');

DELETE FROM permissions WHERE code = 'users:create';

WITH legacy AS (
    SELECT id FROM permissions WHERE code = 'users:ban'
),
canonical AS (
    SELECT id FROM permissions WHERE code = 'users:update'
)
INSERT INTO role_permissions (role_id, permission_id)
SELECT rp.role_id, canonical.id
FROM role_permissions rp
CROSS JOIN canonical
WHERE rp.permission_id IN (SELECT id FROM legacy)
ON CONFLICT DO NOTHING;

DELETE FROM role_permissions
WHERE permission_id IN (SELECT id FROM permissions WHERE code = 'users:ban');

DELETE FROM permissions WHERE code = 'users:ban';

WITH admin_roles AS (
    SELECT id FROM roles WHERE name IN ('admin', 'super_admin')
),
admin_permissions AS (
    SELECT id FROM permissions
    WHERE code IN (
        'users:read',
        'users:write',
        'users:update',
        'users:delete',
        'content:read',
        'content:write',
        'content:delete',
        'reports:read',
        'reports:update',
        'system:stats',
        'system:settings',
        'audit:read',
        'treats:manage',
        'comments:manage',
        'roles:read',
        'roles:manage',
        'access:admin'
    )
)
INSERT INTO role_permissions (role_id, permission_id)
SELECT admin_roles.id, admin_permissions.id
FROM admin_roles
CROSS JOIN admin_permissions
ON CONFLICT DO NOTHING;

WITH moderator_roles AS (
    SELECT id FROM roles WHERE name = 'moderator'
),
moderator_permissions AS (
    SELECT id FROM permissions
    WHERE code IN (
        'content:read',
        'content:write',
        'content:delete',
        'reports:read',
        'reports:update',
        'comments:manage'
    )
)
INSERT INTO role_permissions (role_id, permission_id)
SELECT moderator_roles.id, moderator_permissions.id
FROM moderator_roles
CROSS JOIN moderator_permissions
ON CONFLICT DO NOTHING;

COMMIT;
