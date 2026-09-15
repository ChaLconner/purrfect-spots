BEGIN;

ALTER TABLE public.email_verifications
    ADD COLUMN IF NOT EXISTS locked_until timestamptz;

-- Abort on ambiguous identities rather than merge or delete accounts.
CREATE UNIQUE INDEX IF NOT EXISTS users_email_normalized_key
    ON public.users (lower(email));

DROP POLICY IF EXISTS "Users can update own profile" ON public.users;
CREATE POLICY "Users can update own profile"
    ON public.users FOR UPDATE TO authenticated
    USING ((SELECT auth.uid()) = id)
    WITH CHECK ((SELECT auth.uid()) = id);

-- Browser clients only need public/profile and subscription-display fields.
-- Keep credentials, provider IDs, billing IDs, roles, bans, and revocation
-- timestamps behind the backend service role.
REVOKE SELECT ON public.users FROM authenticated;
GRANT SELECT (
    id, email, name, username, picture, bio, treat_balance,
    total_treats_received, total_treats_given, is_pro,
    subscription_end_date, cancel_at_period_end, created_at, updated_at
) ON public.users TO authenticated;

-- OTP storage changed from an unkeyed digest to an application-keyed HMAC.
-- Old pending challenges cannot be verified safely, so require a resend.
UPDATE public.email_verifications
SET verified_at = now()
WHERE verified_at IS NULL;

CREATE UNIQUE INDEX IF NOT EXISTS email_verifications_pending_email_key
    ON public.email_verifications (lower(email)) WHERE verified_at IS NULL;

-- Unconfirmed identities deliberately do not exist in public.users. This narrow
-- backend-only lookup avoids listing all Auth users or exposing auth.users.
CREATE OR REPLACE FUNCTION public.get_auth_user_by_email(p_email text)
RETURNS TABLE (id uuid, email text, name text, picture text, created_at timestamptz, email_confirmed_at timestamptz)
LANGUAGE sql STABLE SECURITY DEFINER
SET search_path = pg_catalog, pg_temp
AS $$
    SELECT u.id, u.email,
           coalesce(u.raw_user_meta_data->>'name', u.raw_user_meta_data->>'full_name', ''),
           coalesce(u.raw_user_meta_data->>'avatar_url', u.raw_user_meta_data->>'picture', ''),
           u.created_at, u.email_confirmed_at
    FROM auth.users AS u
    WHERE lower(u.email) = lower(trim(p_email))
      AND u.deleted_at IS NULL
    LIMIT 1
$$;

REVOKE ALL ON FUNCTION public.get_auth_user_by_email(text) FROM PUBLIC, anon, authenticated;
GRANT EXECUTE ON FUNCTION public.get_auth_user_by_email(text) TO service_role;

COMMIT;
