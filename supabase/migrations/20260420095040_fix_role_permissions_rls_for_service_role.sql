
-- The role_permissions RLS policy currently only allows reads when the JWT
-- has user_role='admin' as a claim. This blocks the service role client from
-- reading role_permissions during nested PostgREST joins (used in auth middleware).
-- Fix: add a policy that allows the service role (and authenticated users) to 
-- SELECT from role_permissions, and keep write access admin-only.

-- Drop the overly restrictive ALL-commands policy
DROP POLICY IF EXISTS "role_permissions_admin_only" ON public.role_permissions;

-- Allow all authenticated users (and service role) to read role_permissions
-- This is safe because role_permissions only contains role<->permission mappings (no sensitive data)
CREATE POLICY "role_permissions_read_authenticated"
  ON public.role_permissions
  FOR SELECT
  TO authenticated
  USING (true);

-- Restrict write operations (INSERT, UPDATE, DELETE) to service role only
-- Service role bypasses RLS, so this policy targets authenticated users only
CREATE POLICY "role_permissions_write_admin_only"
  ON public.role_permissions
  FOR ALL
  TO authenticated
  USING (
    (SELECT auth.jwt() ->> 'user_role') = 'admin'
  )
  WITH CHECK (
    (SELECT auth.jwt() ->> 'user_role') = 'admin'
  );

