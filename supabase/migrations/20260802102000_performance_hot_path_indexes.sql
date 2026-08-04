-- Performance indexes and RPC for gallery/search hot paths.
-- Safe to apply repeatedly; verify with pg_stat_user_indexes after deployment.

CREATE EXTENSION IF NOT EXISTS pg_trgm;

CREATE INDEX IF NOT EXISTS idx_cat_photos_public_uploaded
    ON public.cat_photos (uploaded_at DESC)
    WHERE deleted_at IS NULL AND status = 'approved';

CREATE INDEX IF NOT EXISTS idx_cat_photos_user_uploaded_public
    ON public.cat_photos (user_id, uploaded_at DESC)
    WHERE deleted_at IS NULL;

CREATE INDEX IF NOT EXISTS idx_cat_photos_user_uploaded_approved
    ON public.cat_photos (user_id, uploaded_at DESC)
    WHERE deleted_at IS NULL AND status = 'approved';

CREATE INDEX IF NOT EXISTS idx_cat_photos_tags_gin
    ON public.cat_photos USING gin (tags)
    WHERE deleted_at IS NULL AND status = 'approved';

CREATE INDEX IF NOT EXISTS idx_cat_photos_location_trgm_public
    ON public.cat_photos USING gin (location_name gin_trgm_ops)
    WHERE deleted_at IS NULL AND status = 'approved';

CREATE INDEX IF NOT EXISTS idx_cat_photos_description_trgm_public
    ON public.cat_photos USING gin (description gin_trgm_ops)
    WHERE deleted_at IS NULL AND status = 'approved';

CREATE INDEX IF NOT EXISTS idx_cat_photos_uploaded_at
    ON public.cat_photos (uploaded_at DESC);

CREATE INDEX IF NOT EXISTS idx_users_created_at
    ON public.users (created_at DESC);

CREATE INDEX IF NOT EXISTS idx_reports_created_at
    ON public.reports (created_at DESC);

CREATE INDEX IF NOT EXISTS idx_photo_likes_photo_user
    ON public.photo_likes (photo_id, user_id);

CREATE INDEX IF NOT EXISTS idx_notifications_user_created
    ON public.notifications (user_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_notifications_user_unread
    ON public.notifications (user_id, is_read)
    WHERE is_read = false;

CREATE INDEX IF NOT EXISTS idx_reports_status_created
    ON public.reports (status, created_at DESC);

CREATE OR REPLACE FUNCTION public.get_popular_tags(result_limit integer DEFAULT 20)
RETURNS TABLE(tag text, count bigint)
LANGUAGE sql
STABLE
SECURITY INVOKER
SET search_path = pg_catalog, public
AS $$
    SELECT lower(tag) AS tag, count(*) AS count
    FROM public.cat_photos AS photo
    CROSS JOIN LATERAL unnest(photo.tags) AS tag
    WHERE photo.deleted_at IS NULL
      AND photo.status = 'approved'
    GROUP BY lower(tag)
    ORDER BY count(*) DESC, lower(tag)
    LIMIT greatest(1, least(result_limit, 100));
$$;

REVOKE EXECUTE ON FUNCTION public.get_popular_tags(integer) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION public.get_popular_tags(integer) TO anon, authenticated, service_role;
