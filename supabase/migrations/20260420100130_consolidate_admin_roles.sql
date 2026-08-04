-- 1. Remove 'super_admin' role if it exists (as requested)
-- First, move any users from 'super_admin' to 'admin'
DO $$
DECLARE
    admin_id UUID;
    super_admin_id UUID;
BEGIN
    SELECT id INTO admin_id FROM public.roles WHERE name = 'admin' LIMIT 1;
    SELECT id INTO super_admin_id FROM public.roles WHERE name = 'super_admin' LIMIT 1;

    IF super_admin_id IS NOT NULL AND admin_id IS NOT NULL THEN
        -- Move users
        UPDATE public.users SET role_id = admin_id WHERE role_id = super_admin_id;
        -- Move permissions (avoid duplicates)
        INSERT INTO public.role_permissions (role_id, permission_id)
        SELECT admin_id, permission_id FROM public.role_permissions WHERE role_id = super_admin_id
        ON CONFLICT DO NOTHING;
        -- Delete super_admin role
        DELETE FROM public.role_permissions WHERE role_id = super_admin_id;
        DELETE FROM public.roles WHERE id = super_admin_id;
    ELSIF super_admin_id IS NOT NULL THEN
        -- If only super_admin exists, rename it to admin
        UPDATE public.roles SET name = 'admin' WHERE id = super_admin_id;
    END IF;
END $$;

-- 2. Consolidate duplicate roles by name (keep one, move users/permissions)
DO $$
DECLARE
    r RECORD;
    target_id UUID;
BEGIN
    FOR r IN (SELECT name FROM public.roles GROUP BY name HAVING COUNT(*) > 1) LOOP
        -- Pick the 'system' one or the oldest one as target
        SELECT id INTO target_id FROM public.roles WHERE name = r.name ORDER BY is_system DESC, created_at ASC LIMIT 1;
        
        -- Move users
        UPDATE public.users SET role_id = target_id WHERE role_id IN (SELECT id FROM public.roles WHERE name = r.name AND id != target_id);
        
        -- Move permissions
        INSERT INTO public.role_permissions (role_id, permission_id)
        SELECT target_id, permission_id FROM public.role_permissions 
        WHERE role_id IN (SELECT id FROM public.roles WHERE name = r.name AND id != target_id)
        ON CONFLICT DO NOTHING;
        
        -- Delete old role permissions and roles
        DELETE FROM public.role_permissions WHERE role_id IN (SELECT id FROM public.roles WHERE name = r.name AND id != target_id);
        DELETE FROM public.roles WHERE name = r.name AND id != target_id;
    END LOOP;
END $$;

-- 3. Cleanup duplicate permissions for any role
DELETE FROM public.role_permissions a
USING public.role_permissions b
WHERE a.ctid > b.ctid 
  AND a.role_id = b.role_id 
  AND a.permission_id = b.permission_id;

-- 4. Ensure admin role has all permissions
DO $$
DECLARE
    admin_id UUID;
    perm_id UUID;
BEGIN
    SELECT id INTO admin_id FROM public.roles WHERE name = 'admin' LIMIT 1;
    IF admin_id IS NOT NULL THEN
        FOR perm_id IN (SELECT id FROM public.permissions) LOOP
            INSERT INTO public.role_permissions (role_id, permission_id)
            VALUES (admin_id, perm_id)
            ON CONFLICT DO NOTHING;
        END LOOP;
    END IF;
END $$;

