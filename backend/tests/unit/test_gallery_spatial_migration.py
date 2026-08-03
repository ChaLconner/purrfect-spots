from pathlib import Path

MIGRATION_PATH = (
    Path(__file__).resolve().parents[3]
    / "supabase"
    / "migrations"
    / "20260803095243_optimize_gallery_spatial_search.sql"
)
VIEWPORT_MIGRATION_PATH = (
    Path(__file__).resolve().parents[3] / "supabase" / "migrations" / "20260803100138_add_viewport_spatial_search.sql"
)


def test_spatial_search_migration_keeps_public_results_indexable() -> None:
    migration = MIGRATION_PATH.read_text(encoding="utf-8")

    assert "DROP FUNCTION IF EXISTS public.search_nearby_photos" in migration
    assert "status text" in migration
    assert "photo.status = 'approved'" in migration
    assert "photo.location IS NOT NULL" in migration
    assert "SET search_path = pg_catalog, public, extensions" in migration
    assert "TO anon, authenticated, service_role" in migration


def test_viewport_spatial_migration_preserves_exact_bounds() -> None:
    migration = VIEWPORT_MIGRATION_PATH.read_text(encoding="utf-8")

    assert "CREATE FUNCTION public.search_viewport_photos" in migration
    assert "ST_Intersects(photo.location, viewport.bounds)" in migration
    assert "photo.status = 'approved'" in migration
    assert "photo.location IS NOT NULL" in migration
    assert "SET search_path = pg_catalog, public, extensions" in migration
    assert "TO anon, authenticated, service_role" in migration
