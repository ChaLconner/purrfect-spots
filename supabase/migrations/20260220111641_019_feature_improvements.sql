-- Migration 019: Feature Improvements (Soft Delete, Privacy, AI Fallback Status)

ALTER TABLE public.cat_photos ADD COLUMN IF NOT EXISTS status TEXT DEFAULT 'approved';
ALTER TABLE public.cat_photos ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMPTZ DEFAULT NULL;
ALTER TABLE public.cat_photos ADD COLUMN IF NOT EXISTS location_blurred BOOLEAN DEFAULT FALSE;

-- Update RLS policies to respect deleted_at and status
DROP POLICY IF EXISTS "Public read access" ON public.cat_photos;

CREATE POLICY "Public read access" ON public.cat_photos
    FOR SELECT
    USING (deleted_at IS NULL AND (status = 'approved' OR user_id = auth.uid()));
