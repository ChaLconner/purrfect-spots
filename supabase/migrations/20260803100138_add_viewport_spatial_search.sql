-- Use the PostGIS GIST index for exact viewport bounds.
-- This keeps map results complete while avoiding the circle-vs-viewport
-- mismatch from routing a bounding box through search_nearby_photos.

CREATE FUNCTION public.search_viewport_photos(
    north double precision,
    south double precision,
    east double precision,
    west double precision,
    result_limit integer DEFAULT 100
)
RETURNS TABLE (
    id uuid,
    user_id uuid,
    image_url text,
    location_name text,
    description text,
    latitude double precision,
    longitude double precision,
    uploaded_at timestamptz,
    tags text[],
    status text
)
LANGUAGE sql
STABLE
SECURITY INVOKER
SET search_path = pg_catalog, public, extensions
AS $function$
    WITH viewport AS (
        SELECT ST_MakeEnvelope(
            least(west, east),
            least(south, north),
            greatest(west, east),
            greatest(south, north),
            4326
        )::geography AS bounds
    )
    SELECT
        photo.id,
        photo.user_id,
        photo.image_url,
        photo.location_name,
        photo.description,
        photo.latitude,
        photo.longitude,
        photo.uploaded_at,
        photo.tags,
        photo.status
    FROM public.cat_photos AS photo
    CROSS JOIN viewport
    WHERE photo.deleted_at IS NULL
      AND photo.status = 'approved'
      AND photo.location IS NOT NULL
      AND ST_Intersects(photo.location, viewport.bounds)
    ORDER BY photo.uploaded_at DESC
    LIMIT greatest(1, least(result_limit, 500));
$function$;

REVOKE EXECUTE ON FUNCTION public.search_viewport_photos(
    double precision,
    double precision,
    double precision,
    double precision,
    integer
)
    FROM PUBLIC;
GRANT EXECUTE ON FUNCTION public.search_viewport_photos(
    double precision,
    double precision,
    double precision,
    double precision,
    integer
)
    TO anon, authenticated, service_role;
