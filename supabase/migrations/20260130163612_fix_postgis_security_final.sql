-- Migration: Move PostGIS to extensions schema to fix security linter issues

-- 1. Create the extensions schema
CREATE SCHEMA IF NOT EXISTS extensions;

-- 2. Drop dependent objects
DROP TRIGGER IF EXISTS trg_sync_cat_photos_location ON public.cat_photos;
DROP FUNCTION IF EXISTS public.search_nearby_photos;
DROP FUNCTION IF EXISTS public.sync_cat_photos_location;
ALTER TABLE public.cat_photos DROP COLUMN IF EXISTS location CASCADE;

-- 3. Move extension
DROP EXTENSION IF EXISTS postgis CASCADE;
CREATE EXTENSION postgis WITH SCHEMA extensions;

-- 4. Restore column
ALTER TABLE public.cat_photos 
ADD COLUMN location extensions.geography(POINT, 4326);

-- 5. Repopulate
UPDATE public.cat_photos 
SET location = extensions.ST_SetSRID(extensions.ST_MakePoint(longitude, latitude), 4326)
WHERE longitude IS NOT NULL AND latitude IS NOT NULL;

-- 6. Index
CREATE INDEX idx_cat_photos_location_gist 
ON public.cat_photos USING GIST(location);

-- 7. Trigger Function
CREATE OR REPLACE FUNCTION public.sync_cat_photos_location()
RETURNS TRIGGER AS $$
BEGIN
    NEW.location := extensions.ST_SetSRID(extensions.ST_MakePoint(NEW.longitude, NEW.latitude), 4326);
    RETURN NEW;
END;
$$ LANGUAGE plpgsql
SET search_path TO public, extensions;

-- 8. Trigger
CREATE TRIGGER trg_sync_cat_photos_location
BEFORE INSERT OR UPDATE OF latitude, longitude ON public.cat_photos
FOR EACH ROW
EXECUTE FUNCTION public.sync_cat_photos_location();

-- 9. Search Function
CREATE OR REPLACE FUNCTION public.search_nearby_photos(
    lat DOUBLE PRECISION,
    lng DOUBLE PRECISION,
    radius_meters DOUBLE PRECISION DEFAULT 5000,
    result_limit INTEGER DEFAULT 50
)
RETURNS TABLE (
    id UUID,
    user_id UUID,
    location_name VARCHAR(255),
    description TEXT,
    latitude DECIMAL(10,7),
    longitude DECIMAL(11,7),
    image_url TEXT,
    tags TEXT[],
    uploaded_at TIMESTAMPTZ,
    distance_meters DOUBLE PRECISION
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        cp.id,
        cp.user_id,
        cp.location_name,
        cp.description,
        cp.latitude,
        cp.longitude,
        cp.image_url,
        cp.tags,
        cp.uploaded_at,
        extensions.ST_Distance(
            cp.location,
            extensions.ST_SetSRID(extensions.ST_MakePoint(lng, lat), 4326)::extensions.geography
        ) AS distance_meters
    FROM public.cat_photos cp
    WHERE extensions.ST_DWithin(
        cp.location,
        extensions.ST_SetSRID(extensions.ST_MakePoint(lng, lat), 4326)::extensions.geography,
        radius_meters
    )
    ORDER BY distance_meters ASC
    LIMIT result_limit;
END;
$$ LANGUAGE plpgsql
SET search_path TO public, extensions;

