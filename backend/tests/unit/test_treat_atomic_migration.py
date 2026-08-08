from pathlib import Path

MIGRATION_PATH = (
    Path(__file__).resolve().parents[3]
    / "supabase"
    / "migrations"
    / "20260809100000_drop_legacy_give_treat_atomic_overload.sql"
)


def test_treat_atomic_migration_drops_ambiguous_legacy_overload() -> None:
    migration = MIGRATION_PATH.read_text(encoding="utf-8")

    assert "drop function if exists public.give_treat_atomic(uuid, uuid, uuid, integer);" in migration
