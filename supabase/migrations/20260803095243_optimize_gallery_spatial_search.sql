-- Optimize the optional PostGIS viewport path.
-- The 20260730000000 function calculated a fallback point for every row and
-- omitted moderation status, so the GIST index was not reliably usable and
-- the API had to fall back to the bounding-box query.

DROP FUNCTION IF EXISTS public.search_nearby_photos(double precision, double precision, double precision, integer);

CREATE FUNCTION public.search_nearby_photos(
    lat double precision,
    lng double precision,
    radius_meters double precision,
    result_limit integer DEFAULT 50
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
    status text,
    distance_meters double precision
)
LANGUAGE sql
STABLE
SECURITY INVOKER
SET search_path = pg_catalog, public, extensions
AS $function$
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
        photo.status,
        ST_Distance(photo.location, search_point.point) AS distance_meters
    FROM public.cat_photos AS photo
    CROSS JOIN LATERAL (
        SELECT ST_SetSRID(ST_MakePoint(lng, lat), 4326)::geography AS point
    ) AS search_point
    WHERE photo.deleted_at IS NULL
      AND photo.status = 'approved'
      AND photo.location IS NOT NULL
      AND ST_DWithin(
          photo.location,
          search_point.point,
          greatest(radius_meters, 0)
      )
    ORDER BY distance_meters ASC, photo.uploaded_at DESC
    LIMIT greatest(1, least(result_limit, 500));
$function$;

REVOKE EXECUTE ON FUNCTION public.search_nearby_photos(double precision, double precision, double precision, integer)
    FROM PUBLIC;
GRANT EXECUTE ON FUNCTION public.search_nearby_photos(double precision, double precision, double precision, integer)
    TO anon, authenticated, service_role;
