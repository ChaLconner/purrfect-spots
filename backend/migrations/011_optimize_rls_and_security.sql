-- 1. Clean up cat_photos policies (Performance: Remove duplicates and optimize subqueries)
DROP POLICY IF EXISTS "Anyone can read cat photos" ON public.cat_photos;
DROP POLICY IF EXISTS "Public read access" ON public.cat_photos;
DROP POLICY IF EXISTS "Users can insert own cat photos" ON public.cat_photos;
DROP POLICY IF EXISTS "Users can upload their own photos" ON public.cat_photos;
DROP POLICY IF EXISTS "Users can update own cat photos" ON public.cat_photos;
DROP POLICY IF EXISTS "Users can update their own photos" ON public.cat_photos;
DROP POLICY IF EXISTS "Users can delete own cat photos" ON public.cat_photos;
DROP POLICY IF EXISTS "Users can delete their own photos" ON public.cat_photos;

CREATE POLICY "Public read access" ON public.cat_photos
FOR SELECT TO public USING (true);

CREATE POLICY "Users can insert own cat photos" ON public.cat_photos
FOR INSERT TO authenticated WITH CHECK ((SELECT auth.uid()) = user_id);

CREATE POLICY "Users can update own cat photos" ON public.cat_photos
FOR UPDATE TO authenticated USING ((SELECT auth.uid()) = user_id);

CREATE POLICY "Users can delete own cat photos" ON public.cat_photos
FOR DELETE TO authenticated USING ((SELECT auth.uid()) = user_id);

-- 2. Clean up users policies (Performance: Remove duplicates and optimize subqueries)
DROP POLICY IF EXISTS "users_read_own" ON public.users;
DROP POLICY IF EXISTS "Users can read own profile" ON public.users;
DROP POLICY IF EXISTS "users_update_own" ON public.users;
DROP POLICY IF EXISTS "Users can update own profile" ON public.users;
DROP POLICY IF EXISTS "users_insert_own" ON public.users;

CREATE POLICY "Users can read own profile" ON public.users
FOR SELECT TO authenticated USING ((SELECT auth.uid()) = id);

CREATE POLICY "Users can update own profile" ON public.users
FOR UPDATE TO authenticated USING ((SELECT auth.uid()) = id);

CREATE POLICY "Users can insert own profile" ON public.users
FOR INSERT TO authenticated WITH CHECK ((SELECT auth.uid()) = id);

-- 3. Fix password_resets (Security: Add policy for RLS-enabled table)
DROP POLICY IF EXISTS "Service role full access" ON public.password_resets;
CREATE POLICY "Service role full access" ON public.password_resets
FOR ALL TO service_role USING (true);

-- 4. Fix token_blacklist (Security: Add policy for RLS-enabled table)
DROP POLICY IF EXISTS "Service role full access" ON public.token_blacklist;
CREATE POLICY "Service role full access" ON public.token_blacklist
FOR ALL TO service_role USING (true);

-- 5. Optimize email_verifications
DROP POLICY IF EXISTS "Service role full access" ON public.email_verifications;
CREATE POLICY "Service role full access" ON public.email_verifications
FOR ALL TO service_role USING (true);
