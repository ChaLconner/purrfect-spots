-- Migration: 036_gallery_visibility_performance_index.sql
-- Description: Add a partial index on cat_photos for public visibility queries to speed up loading as the gallery grows
-- Created: 2026-05-24

CREATE INDEX IF NOT EXISTS idx_cat_photos_active_uploaded 
ON public.cat_photos(uploaded_at DESC) 
WHERE deleted_at IS NULL AND status = 'approved';
