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
