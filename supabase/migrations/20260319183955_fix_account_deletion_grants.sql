
-- Grant access to account_deletion_requests for service_role (used by admin client in backend)
GRANT ALL ON TABLE public.account_deletion_requests TO service_role;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO service_role;

-- Ensure the table is accessible via PostgREST schema cache
-- Grant SELECT/INSERT/UPDATE to authenticated users (RLS will still enforce row-level access)
GRANT SELECT, INSERT, UPDATE ON TABLE public.account_deletion_requests TO authenticated;

-- Ensure deleted_at column exists on users (in case migration 023 wasn't fully applied)
ALTER TABLE public.users ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMPTZ DEFAULT NULL;

-- Reload PostgREST schema cache
NOTIFY pgrst, 'reload schema';

