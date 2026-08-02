-- Migration 038: Optimize table access paths, RLS evaluation, and ephemeral data retention.

BEGIN;

-- Evaluate the caller identity once per statement, not once per row.
DROP POLICY IF EXISTS "Admins can manage incidents" ON public.security_incidents;
CREATE POLICY "Admins can manage incidents"
    ON public.security_incidents
    FOR ALL
    TO authenticated
    USING (
        EXISTS (
            SELECT 1
            FROM public.users AS app_user
            JOIN public.roles AS app_role ON app_user.role_id = app_role.id
            WHERE app_user.id = (SELECT auth.uid())
              AND app_role.name IN ('admin', 'super_admin')
        )
    );

DROP POLICY IF EXISTS "Admins can manage incident affected users" ON public.incident_affected_users;
CREATE POLICY "Admins can manage incident affected users"
    ON public.incident_affected_users
    FOR ALL
    TO authenticated
    USING (
        EXISTS (
            SELECT 1
            FROM public.users AS app_user
            JOIN public.roles AS app_role ON app_user.role_id = app_role.id
            WHERE app_user.id = (SELECT auth.uid())
              AND app_role.name IN ('admin', 'super_admin')
        )
    );

DROP POLICY IF EXISTS "Admins can manage incident timeline" ON public.incident_timeline;
CREATE POLICY "Admins can manage incident timeline"
    ON public.incident_timeline
    FOR ALL
    TO authenticated
    USING (
        EXISTS (
            SELECT 1
            FROM public.users AS app_user
            JOIN public.roles AS app_role ON app_user.role_id = app_role.id
            WHERE app_user.id = (SELECT auth.uid())
              AND app_role.name IN ('admin', 'super_admin')
        )
    );

-- Blacklist rows contain security-sensitive token identifiers. Backend access
-- uses trusted SQL or service_role; browser roles must not read this table.
DROP POLICY IF EXISTS "Public can view blacklisted tokens" ON public.token_blacklist;

-- Remove an obsolete four-argument RPC overload. Current backend code uses the
-- three-argument overload through a trusted database session or service_role.
REVOKE EXECUTE ON FUNCTION public.give_treat_atomic(uuid, uuid, uuid, integer)
    FROM PUBLIC, anon, authenticated;
GRANT EXECUTE ON FUNCTION public.give_treat_atomic(uuid, uuid, uuid, integer)
    TO service_role;

-- Delete auth artifacts after they can no longer affect authorization.
CREATE OR REPLACE FUNCTION public.cleanup_expired_auth_artifacts()
RETURNS TABLE (
    token_blacklist_deleted BIGINT,
    email_verifications_deleted BIGINT,
    password_resets_deleted BIGINT
)
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = ''
AS $$
DECLARE
    deleted_blacklist BIGINT;
    deleted_verifications BIGINT;
    deleted_resets BIGINT;
BEGIN
    DELETE FROM public.token_blacklist
    WHERE expires_at <= pg_catalog.now();
    GET DIAGNOSTICS deleted_blacklist = ROW_COUNT;

    DELETE FROM public.email_verifications
    WHERE expires_at <= pg_catalog.now();
    GET DIAGNOSTICS deleted_verifications = ROW_COUNT;

    DELETE FROM public.password_resets
    WHERE expires_at <= pg_catalog.now()
       OR is_used IS TRUE;
    GET DIAGNOSTICS deleted_resets = ROW_COUNT;

    RETURN QUERY
    SELECT deleted_blacklist, deleted_verifications, deleted_resets;
END;
$$;

REVOKE ALL ON FUNCTION public.cleanup_expired_auth_artifacts()
    FROM PUBLIC, anon, authenticated;
GRANT EXECUTE ON FUNCTION public.cleanup_expired_auth_artifacts()
    TO service_role;

-- Initial cleanup: 866 expired blacklist rows and 11 expired verification rows
-- existed at audit time. The predicate remains authoritative if counts change.
SELECT * FROM public.cleanup_expired_auth_artifacts();

-- Keep one active row per JWT ID, then enforce idempotent persistence.
WITH ranked_blacklist AS (
    SELECT
        id,
        ROW_NUMBER() OVER (
            PARTITION BY token_jti
            ORDER BY expires_at DESC, revoked_at DESC NULLS LAST, id
        ) AS duplicate_rank
    FROM public.token_blacklist
)
DELETE FROM public.token_blacklist AS blacklist
USING ranked_blacklist AS ranked
WHERE blacklist.id = ranked.id
  AND ranked.duplicate_rank > 1;

DROP INDEX IF EXISTS public.idx_token_blacklist_jti;
CREATE UNIQUE INDEX token_blacklist_token_jti_key
    ON public.token_blacklist (token_jti);

-- Existing composite indexes cover these left-prefix access paths.
CREATE INDEX IF NOT EXISTS idx_cat_photos_user_uploaded
    ON public.cat_photos (user_id, uploaded_at DESC);
DROP INDEX IF EXISTS public.idx_cat_photos_user_id;
DROP INDEX IF EXISTS public.idx_role_permissions_role_id;

-- Prevent expired auth artifacts from accumulating again.
CREATE EXTENSION IF NOT EXISTS pg_cron WITH SCHEMA pg_catalog;
SELECT cron.schedule(
    'cleanup-expired-auth-artifacts',
    '17 3 * * *',
    'SELECT public.cleanup_expired_auth_artifacts();'
);

REINDEX TABLE public.token_blacklist;
ANALYZE public.token_blacklist;
ANALYZE public.email_verifications;
ANALYZE public.password_resets;

COMMIT;


