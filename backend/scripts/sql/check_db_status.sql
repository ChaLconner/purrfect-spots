-- ============================================================================
-- MIGRATION STATUS CHECKER
-- Run this script in your Supabase SQL Editor to see what has been applied.
-- ============================================================================

WITH status_check AS (
    -- 001_add_tags_column
    SELECT '001_add_tags_column' as migration_file, 'Column: cat_photos.tags' as item, 
    EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'cat_photos' AND column_name = 'tags') as is_installed
    UNION ALL
    SELECT '001_add_tags_column', 'Index: idx_cat_photos_tags', 
    EXISTS (SELECT 1 FROM pg_indexes WHERE indexname = 'idx_cat_photos_tags')

    -- 002_add_search_indexes
    UNION ALL
    SELECT '002_add_search_indexes', 'Column: cat_photos.search_vector', 
    EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'cat_photos' AND column_name = 'search_vector')
    UNION ALL
    SELECT '002_add_search_indexes', 'Index: idx_cat_photos_location_name', 
    EXISTS (SELECT 1 FROM pg_indexes WHERE indexname = 'idx_cat_photos_location_name')
    UNION ALL
    SELECT '002_add_search_indexes', 'Index: idx_cat_photos_search_vector', 
    EXISTS (SELECT 1 FROM pg_indexes WHERE indexname = 'idx_cat_photos_search_vector')
    UNION ALL
    SELECT '002_add_search_indexes', 'Function: search_cat_photos', 
    EXISTS (SELECT 1 FROM pg_proc WHERE proname = 'search_cat_photos')

    -- 003_create_password_resets
    UNION ALL
    SELECT '003_create_password_resets', 'Table: password_resets', 
    EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'password_resets')

    -- 003_enable_postgis
    UNION ALL
    SELECT '003_enable_postgis', 'Extension: postgis', 
    EXISTS (SELECT 1 FROM pg_extension WHERE extname = 'postgis')
    UNION ALL
    SELECT '003_enable_postgis', 'Column: cat_photos.location', 
    EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'cat_photos' AND column_name = 'location')
    UNION ALL
    SELECT '003_enable_postgis', 'Function: search_nearby_photos', 
    EXISTS (SELECT 1 FROM pg_proc WHERE proname = 'search_nearby_photos')

    -- 004_add_performance_indexes
    UNION ALL
    SELECT '004_add_performance_indexes', 'Extension: pg_trgm', 
    EXISTS (SELECT 1 FROM pg_extension WHERE extname = 'pg_trgm')
    UNION ALL
    SELECT '004_add_performance_indexes', 'Index: idx_cat_photos_location_name_trgm', 
    EXISTS (SELECT 1 FROM pg_indexes WHERE indexname = 'idx_cat_photos_location_name_trgm')
    UNION ALL
    SELECT '004_add_performance_indexes', 'Index: idx_password_resets_token', 
    EXISTS (SELECT 1 FROM pg_indexes WHERE indexname = 'idx_password_resets_token')

    -- 006_create_token_blacklist
    UNION ALL
    SELECT '006_create_token_blacklist', 'Table: token_blacklist', 
    EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'token_blacklist')
)
SELECT 
    migration_file,
    item,
    CASE WHEN is_installed THEN '✅ INSTALLED' ELSE '❌ MISSING' END as status
FROM status_check
ORDER BY migration_file, item;
