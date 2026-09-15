-- Remove only indexes confirmed by the Supabase Performance Advisor to be
-- exact duplicates of higher-traffic indexes. Keep all other indexes until
-- production query-plan evidence justifies their removal.

DROP INDEX IF EXISTS public.idx_cat_photos_uploaded_at;
DROP INDEX IF EXISTS public.idx_cat_photos_public_uploaded;
DROP INDEX IF EXISTS public.idx_users_created_at;
