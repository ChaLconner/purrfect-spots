-- A CHECK expression that evaluates to NULL passes in PostgreSQL. Require both
-- values explicitly so a partial coordinate pair cannot bypass range checks.
ALTER TABLE public.cat_photos
    DROP CONSTRAINT cat_photos_coordinates_valid,
    ADD CONSTRAINT cat_photos_coordinates_valid CHECK (
        (latitude IS NULL AND longitude IS NULL)
        OR (
            latitude IS NOT NULL
            AND longitude IS NOT NULL
            AND latitude BETWEEN -90 AND 90
            AND longitude BETWEEN -180 AND 180
        )
    );
