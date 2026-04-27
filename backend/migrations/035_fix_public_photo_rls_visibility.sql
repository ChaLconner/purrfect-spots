-- Migration: restore approved-only public photo visibility
--
-- Migration 020 limited public reads to approved photos (or the owner).
-- Migration 022 later recreated the policy with only deleted_at filtering,
-- which exposed pending/rejected rows to direct Supabase anon/authenticated reads.

BEGIN;

DROP POLICY IF EXISTS "Public can view all non-deleted photos" ON public.cat_photos;

CREATE POLICY "Public can view approved non-deleted photos"
ON public.cat_photos
FOR SELECT
USING (
    deleted_at IS NULL
    AND (
        status = 'approved'
        OR user_id = auth.uid()
    )
);

COMMIT;
