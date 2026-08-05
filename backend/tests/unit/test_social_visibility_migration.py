from pathlib import Path

MIGRATION_PATH = (
    Path(__file__).resolve().parents[3]
    / "supabase"
    / "migrations"
    / "20260802103000_fix_toggle_photo_like_ambiguity.sql"
)


def test_toggle_photo_like_migration_qualifies_photo_columns() -> None:
    migration = MIGRATION_PATH.read_text(encoding="utf-8")

    assert "from public.cat_photos as photo" in migration
    assert "select photo.id" in migration
    assert "photo.deleted_at is null" in migration
    assert "photo.status = 'approved'" in migration
    assert "coalesce(photo.likes_count, 0)" in migration
