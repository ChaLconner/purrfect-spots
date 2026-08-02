-- Production migration 20260729100925.
-- Harden exposed database functions, remove unsafe RLS overlaps, and add
-- indexes required by foreign-key access paths.

BEGIN;

-- Prevent untrusted roles from creating objects that can shadow names used by
-- SECURITY DEFINER functions.
REVOKE CREATE ON SCHEMA public FROM PUBLIC, anon, authenticated;

-- PostgreSQL grants EXECUTE on new functions to PUBLIC by default. Make future
-- functions service-only unless a later migration grants narrower access.
ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA public
    REVOKE EXECUTE ON FUNCTIONS FROM PUBLIC;
ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA public
    GRANT EXECUTE ON FUNCTIONS TO service_role;

-- No browser client in this repository calls public RPCs directly. All
-- SECURITY DEFINER RPCs are reached through the backend service role or by
-- trusted database sessions, so remove anonymous/authenticated execution.
DO $$
DECLARE
    function_record RECORD;
BEGIN
    FOR function_record IN
        SELECT
            namespace.nspname AS schema_name,
            procedure.proname AS function_name,
            pg_get_function_identity_arguments(procedure.oid) AS identity_arguments
        FROM pg_proc AS procedure
        JOIN pg_namespace AS namespace ON namespace.oid = procedure.pronamespace
        WHERE namespace.nspname = 'public'
          AND procedure.prosecdef
    LOOP
        EXECUTE format(
            'REVOKE EXECUTE ON FUNCTION %I.%I(%s) FROM PUBLIC, anon, authenticated',
            function_record.schema_name,
            function_record.function_name,
            function_record.identity_arguments
        );
        EXECUTE format(
            'GRANT EXECUTE ON FUNCTION %I.%I(%s) TO service_role',
            function_record.schema_name,
            function_record.function_name,
            function_record.identity_arguments
        );
    END LOOP;
END
$$;

-- These admin RPCs are not all SECURITY DEFINER, but they expose aggregate or
-- administrative data and must still be backend-only.
REVOKE EXECUTE ON FUNCTION public.get_treat_admin_stats()
    FROM PUBLIC, anon, authenticated;
GRANT EXECUTE ON FUNCTION public.get_treat_admin_stats() TO service_role;

-- Fix mutable search paths reported by the Supabase database linter. pg_temp is
-- kept last so temporary objects cannot shadow catalog or application objects.
ALTER FUNCTION public.admin_grant_treats(uuid, integer)
    SET search_path TO pg_catalog, public, pg_temp;
ALTER FUNCTION public.get_treat_admin_stats()
    SET search_path TO pg_catalog, public, pg_temp;
ALTER FUNCTION public.get_admin_trends(integer)
    SET search_path TO pg_catalog, public, pg_temp;
ALTER FUNCTION public.get_monthly_report(integer)
    SET search_path TO pg_catalog, public, pg_temp;
ALTER FUNCTION public.update_incident_sla_status()
    SET search_path TO pg_catalog, public, pg_temp;
ALTER FUNCTION public.check_incident_sla_breaches()
    SET search_path TO pg_catalog, public, pg_temp;

-- Execute the view with the querying role's permissions and RLS context.
ALTER VIEW public.admin_comment_list SET (security_invoker = true);

-- Replace overlapping role_permissions policies. Reads remain available to
-- authenticated sessions; all writes continue through the backend service role.
DROP POLICY IF EXISTS role_permissions_read_authenticated ON public.role_permissions;
DROP POLICY IF EXISTS role_permissions_write_admin_only ON public.role_permissions;
CREATE POLICY role_permissions_read_authenticated
    ON public.role_permissions
    FOR SELECT
    TO authenticated
    USING (true);

-- Combine overlapping SELECT policies into one policy and evaluate auth.uid()
-- once per statement.
DROP POLICY IF EXISTS "Admins can read all consents" ON public.user_consents;
DROP POLICY IF EXISTS "Users can read own consents" ON public.user_consents;
DROP POLICY IF EXISTS "Users can insert own consents" ON public.user_consents;
CREATE POLICY user_consents_read_own_or_admin
    ON public.user_consents
    FOR SELECT
    TO authenticated
    USING (
        user_id = (SELECT auth.uid())
        OR EXISTS (
            SELECT 1
            FROM public.users AS app_user
            JOIN public.roles AS app_role ON app_user.role_id = app_role.id
            WHERE app_user.id = (SELECT auth.uid())
              AND app_role.name IN ('admin', 'super_admin')
        )
    );
CREATE POLICY user_consents_insert_own
    ON public.user_consents
    FOR INSERT
    TO authenticated
    WITH CHECK (user_id = (SELECT auth.uid()));

-- These tables are backend-managed. Explicit service-role policies document the
-- intent and keep RLS enabled even though service_role bypasses RLS by design.
CREATE POLICY config_history_service_role
    ON public.config_history
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);
CREATE POLICY pending_config_changes_service_role
    ON public.pending_config_changes
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

-- Foreign-key indexes reported by the production performance advisor.
CREATE INDEX IF NOT EXISTS idx_audit_logs_user_id
    ON public.audit_logs (user_id);
CREATE INDEX IF NOT EXISTS idx_incident_affected_users_user_id
    ON public.incident_affected_users (user_id);
CREATE INDEX IF NOT EXISTS idx_incident_timeline_incident_id
    ON public.incident_timeline (incident_id);
CREATE INDEX IF NOT EXISTS idx_reports_comment_id
    ON public.reports (comment_id);
CREATE INDEX IF NOT EXISTS idx_reports_photo_id
    ON public.reports (photo_id);
CREATE INDEX IF NOT EXISTS idx_reports_reporter_id
    ON public.reports (reporter_id);
CREATE INDEX IF NOT EXISTS idx_reports_resolved_by
    ON public.reports (resolved_by);

COMMIT;
