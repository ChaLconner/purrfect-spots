-- Migration: Optimize Gallery and Add Soft Deletes
-- Run this in Supabase SQL Editor
-- Created: 2026-01-30

-- =====================================================
-- SECTION 1: Extensions & Schema Changes (DO FIRST)
-- =====================================================

-- Enable pg_trgm for fast partial match searches (ILIKE)
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- Add deleted_at column (Must be done before creating indexes on it)
ALTER TABLE cat_photos 
ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMPTZ DEFAULT NULL;

-- =====================================================
-- SECTION 2: Performance Indexes
-- =====================================================

-- Index for location_name using GIN (Trigram) for ILIKE performance
-- Requires pg_trgm extension
CREATE INDEX IF NOT EXISTS idx_cat_photos_location_name_trgm 
ON cat_photos USING GIN (location_name gin_trgm_ops);

-- Index for description using GIN (Trigram)
CREATE INDEX IF NOT EXISTS idx_cat_photos_description_trgm 
ON cat_photos USING GIN (description gin_trgm_ops);

-- Map specific index (lightweight queries)
-- Using include to allow index-only scans for map markers
CREATE INDEX IF NOT EXISTS idx_cat_photos_map_optimized
ON cat_photos (latitude, longitude, id, location_name, image_url)
WHERE deleted_at IS NULL;

-- Index for excluding deleted items (crucial for performance)
CREATE INDEX IF NOT EXISTS idx_cat_photos_not_deleted
ON cat_photos (uploaded_at DESC)
WHERE deleted_at IS NULL;
