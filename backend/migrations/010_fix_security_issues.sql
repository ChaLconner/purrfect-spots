-- Create a specific schema for extensions to improve security
CREATE SCHEMA IF NOT EXISTS "extensions";

-- Grant usage on the new schema to standard Supabase roles
GRANT USAGE ON SCHEMA "extensions" TO postgres, anon, authenticated, service_role;

-- Move pg_trgm to the new schema
ALTER EXTENSION pg_trgm SET SCHEMA "extensions";

-- Note: PostGIS often does not support SET SCHEMA. 
-- We skip moving it to avoid the error previously encountered.

-- Update the search_path for the database roles
-- We include 'extensions' in the path so they can still find postgis if it stays in public, 
-- or find pg_trgm in the new schema.
ALTER ROLE postgres SET search_path = public, extensions;
ALTER ROLE authenticated SET search_path = public, extensions;
ALTER ROLE anon SET search_path = public, extensions;
ALTER ROLE service_role SET search_path = public, extensions;
ALTER DATABASE postgres SET search_path = public, extensions;

-- Fix "Function Search Path Mutable" warnings by explicitly setting search_path on functions
ALTER FUNCTION public.cat_photos_search_vector_trigger() SET search_path = public, extensions;
ALTER FUNCTION public.cleanup_expired_otps() SET search_path = public, extensions;
ALTER FUNCTION public.search_cat_photos(text, integer) SET search_path = public, extensions;
ALTER FUNCTION public.search_nearby_photos(double precision, double precision, double precision, integer) SET search_path = public, extensions;
ALTER FUNCTION public.sync_cat_photos_location() SET search_path = public, extensions;
ALTER FUNCTION public.update_updated_at_column() SET search_path = public, extensions;
