from pathlib import Path

MIGRATION_PATH = (
    Path(__file__).resolve().parents[3] / "supabase" / "migrations" / "20260729100925_harden_database_security.sql"
)


def test_security_migration_revokes_client_execution() -> None:
    migration = MIGRATION_PATH.read_text(encoding="utf-8")

    assert "WHERE namespace.nspname = 'public'" in migration
    assert "AND procedure.prosecdef" in migration
    assert "FROM PUBLIC, anon, authenticated" in migration
    assert "GRANT EXECUTE ON FUNCTION" in migration
    assert "TO service_role" in migration


def test_security_migration_fixes_database_advisor_findings() -> None:
    migration = MIGRATION_PATH.read_text(encoding="utf-8")

    assert "security_invoker = true" in migration
    assert "SET search_path TO pg_catalog, public, pg_temp" in migration
    assert "idx_audit_logs_user_id" in migration
    assert "idx_incident_affected_users_user_id" in migration
    assert "idx_incident_timeline_incident_id" in migration
    assert "idx_reports_comment_id" in migration
    assert "idx_reports_photo_id" in migration
    assert "idx_reports_reporter_id" in migration
    assert "idx_reports_resolved_by" in migration


def test_latest_security_definer_migration_hardens_functions_created_later() -> None:
    migration_path = (
        Path(__file__).resolve().parents[3]
        / "supabase"
        / "migrations"
        / "20260816155407_harden_all_security_definer_paths.sql"
    )
    migration = migration_path.read_text(encoding="utf-8")

    assert "procedure.prosecdef" in migration
    assert "procedure.proconfig" in migration
    assert "WHERE setting = 'search_path='" in migration
    assert "needs_search_path_hardening" in migration
    assert "REVOKE EXECUTE ON FUNCTION" in migration
    assert "TO service_role" in migration
    assert "SET search_path TO pg_catalog, public, extensions, pg_temp" in migration


def test_upload_quota_reservation_migration_is_atomic_and_service_only() -> None:
    migration_path = (
        Path(__file__).resolve().parents[3]
        / "supabase"
        / "migrations"
        / "20260816155427_enforce_upload_quota_reservations.sql"
    )
    migration = migration_path.read_text(encoding="utf-8")

    assert "CREATE TABLE IF NOT EXISTS public.upload_quota_reservations" in migration
    assert "FOR UPDATE" in migration
    assert "status = 'reserved'" in migration
    assert "ENABLE ROW LEVEL SECURITY" in migration
    assert "SET search_path = ''" in migration
    assert "FROM PUBLIC, anon, authenticated" in migration
    assert "TO service_role" in migration
    assert "system_daily_stats.total_uploads" in migration
    assert "renew_upload_quota" in migration
    assert "AND expires_at > clock_timestamp()" in migration
    assert "DROP FUNCTION IF EXISTS public.increment_usage(uuid, date)" in migration
