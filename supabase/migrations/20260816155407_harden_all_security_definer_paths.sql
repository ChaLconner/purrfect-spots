-- Harden every currently deployed SECURITY DEFINER function, including
-- functions created by migrations that predate the search_path policy.

BEGIN;

DO $$
DECLARE
    function_record RECORD;
BEGIN
    FOR function_record IN
        SELECT
            namespace.nspname AS schema_name,
            procedure.proname AS function_name,
            pg_get_function_identity_arguments(procedure.oid) AS identity_arguments,
            -- Preserve an explicitly empty search_path, which is the strongest
            -- policy for functions whose object references are fully qualified.
            NOT EXISTS (
                SELECT 1
                FROM unnest(COALESCE(procedure.proconfig, ARRAY[]::text[])) AS setting
                WHERE setting = 'search_path='
            ) AS needs_search_path_hardening
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

        -- Normalize missing and legacy non-empty paths, including paths that
        -- leave temporary schemas ahead of trusted application objects.
        IF function_record.needs_search_path_hardening THEN
            EXECUTE format(
                'ALTER FUNCTION %I.%I(%s) SET search_path TO pg_catalog, public, extensions, pg_temp',
                function_record.schema_name,
                function_record.function_name,
                function_record.identity_arguments
            );
        END IF;
    END LOOP;
END
$$;

COMMIT;
