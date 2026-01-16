-- Migration: 003_enable_postgis.sql
-- Description: Enable PostGIS extension and convert location storage to efficient Geography type

-- 1. Enable PostGIS extension
CREATE EXTENSION IF NOT EXISTS postgis;

-- 2. Add geography column to cat_photos (using SRID 4326 for GPS coords)
ALTER TABLE cat_photos 
ADD COLUMN IF NOT EXISTS location GEOGRAPHY(POINT, 4326);

-- 3. Populate location column from existing lat/long data
-- Only update rows where location is null
UPDATE cat_photos 
SET location = ST_SetSRID(ST_MakePoint(longitude, latitude), 4326)
WHERE location IS NULL AND longitude IS NOT NULL AND latitude IS NOT NULL;

-- 4. Create GIST index for high-performance spatial queries
CREATE INDEX IF NOT EXISTS idx_cat_photos_location_gist 
ON cat_photos USING GIST(location);

-- 5. Add trigger to automatically keep location in sync when lat/long changes
CREATE OR REPLACE FUNCTION sync_cat_photos_location()
RETURNS TRIGGER AS $$
BEGIN
    NEW.location := ST_SetSRID(ST_MakePoint(NEW.longitude, NEW.latitude), 4326);
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_sync_cat_photos_location ON cat_photos;

CREATE TRIGGER trg_sync_cat_photos_location
BEFORE INSERT OR UPDATE OF latitude, longitude ON cat_photos
FOR EACH ROW
EXECUTE FUNCTION sync_cat_photos_location();

-- 6. Create RPC function for nearby photo search (used by backend)
CREATE OR REPLACE FUNCTION search_nearby_photos(
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
        ST_Distance(
            cp.location::geography,
            ST_SetSRID(ST_MakePoint(lng, lat), 4326)::geography
        ) AS distance_meters
    FROM cat_photos cp
    WHERE ST_DWithin(
        cp.location::geography,
        ST_SetSRID(ST_MakePoint(lng, lat), 4326)::geography,
        radius_meters
    )
    ORDER BY distance_meters ASC
    LIMIT result_limit;
END;
$$ LANGUAGE plpgsql;

