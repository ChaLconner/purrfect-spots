-- FINAL PERFORMANCE & RLS CLEANUP

-- 1. Fix remaining InitPlan policies
DROP POLICY IF EXISTS "role_permissions_admin_only" ON public.role_permissions;
CREATE POLICY "role_permissions_admin_only" ON public.role_permissions 
    FOR ALL TO authenticated USING (((SELECT auth.jwt()) ->> 'user_role'::text) = 'admin'::text);

DROP POLICY IF EXISTS "Users can insert their own deletion requests" ON public.account_deletion_requests;
DROP POLICY IF EXISTS "Users can view their own deletion requests" ON public.account_deletion_requests;
DROP POLICY IF EXISTS "Users can update their own deletion requests" ON public.account_deletion_requests;

CREATE POLICY "Users can manage own deletion requests" ON public.account_deletion_requests 
    FOR ALL TO authenticated USING ((SELECT auth.uid()) = user_id);

DROP POLICY IF EXISTS "Users can insert their own audit logs" ON public.audit_logs;
CREATE POLICY "Users can insert own audit logs" ON public.audit_logs 
    FOR INSERT TO authenticated WITH CHECK ((SELECT auth.uid()) = user_id);

DROP POLICY IF EXISTS "audit_logs_select_owner" ON public.audit_logs;
CREATE POLICY "Users can view own audit logs" ON public.audit_logs 
    FOR SELECT TO authenticated USING ((SELECT auth.uid()) = user_id);

-- 2. Resolve Multiple Permissive Policies
-- system_configs
DROP POLICY IF EXISTS "system_configs_select_public" ON public.system_configs;
DROP POLICY IF EXISTS "system_configs_no_public_mods" ON public.system_configs;
CREATE POLICY "system_configs_read_public" ON public.system_configs 
    FOR SELECT TO public USING (is_public = true);

-- treat_packages
DROP POLICY IF EXISTS "Allow read access for all" ON public.treat_packages;
DROP POLICY IF EXISTS "Everyone can view active packages" ON public.treat_packages;
CREATE POLICY "View active treat packages" ON public.treat_packages 
    FOR SELECT TO public USING (is_active = true);

-- users
DROP POLICY IF EXISTS "Public users can view all users" ON public.users;
DROP POLICY IF EXISTS "Users can read own profile" ON public.users;
CREATE POLICY "Allow public user discovery" ON public.users 
    FOR SELECT TO public USING (true);

-- 3. Re-add foreign key indexes to clear linter warnings (even if currently 'unused', they are good practice for data integrity/deletes)
CREATE INDEX IF NOT EXISTS idx_audit_logs_user_id ON public.audit_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_reports_comment_id ON public.reports(comment_id);

