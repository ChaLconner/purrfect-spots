-- PHASE 2: RLS POLICY REFINEMENT (InitPlan optimization & Consolidation)

-- 1. cat_photos: Consolidate and optimize
DROP POLICY IF EXISTS "Users can delete own cat photos" ON public.cat_photos;
DROP POLICY IF EXISTS "Users can update own cat photos" ON public.cat_photos;
DROP POLICY IF EXISTS "Users can insert own cat photos" ON public.cat_photos;
DROP POLICY IF EXISTS "Users can upload their own photos" ON public.cat_photos;
DROP POLICY IF EXISTS "Users can update their own photos" ON public.cat_photos;
DROP POLICY IF EXISTS "Users can delete their own photos" ON public.cat_photos;
DROP POLICY IF EXISTS "Public can view all non-deleted photos" ON public.cat_photos;
DROP POLICY IF EXISTS "Public read access" ON public.cat_photos;

CREATE POLICY "Users can insert own cat photos" ON public.cat_photos 
    FOR INSERT TO authenticated WITH CHECK ((SELECT auth.uid()) = user_id);
CREATE POLICY "Users can update own cat photos" ON public.cat_photos 
    FOR UPDATE TO authenticated USING ((SELECT auth.uid()) = user_id);
CREATE POLICY "Users can delete own cat photos" ON public.cat_photos 
    FOR DELETE TO authenticated USING ((SELECT auth.uid()) = user_id);
CREATE POLICY "Public read non-deleted photos" ON public.cat_photos 
    FOR SELECT TO public USING (deleted_at IS NULL);

-- 2. notifications: Consolidate and optimize
DROP POLICY IF EXISTS "Users can view own notifications" ON public.notifications;
DROP POLICY IF EXISTS "Users can update own notifications" ON public.notifications;
DROP POLICY IF EXISTS "Users can view their own notifications" ON public.notifications;
DROP POLICY IF EXISTS "Users can update their own notifications" ON public.notifications;

CREATE POLICY "Users can view own notifications" ON public.notifications 
    FOR SELECT TO authenticated USING ((SELECT auth.uid()) = user_id);
CREATE POLICY "Users can update own notifications" ON public.notifications 
    FOR UPDATE TO authenticated USING ((SELECT auth.uid()) = user_id);

-- 3. saved_spots: Optimize
DROP POLICY IF EXISTS "Users can manage own saved spots" ON public.saved_spots;
CREATE POLICY "Users can manage own saved spots" ON public.saved_spots 
    FOR ALL TO authenticated USING ((SELECT auth.uid()) = user_id);

-- 4. photo_likes: Consolidate and optimize
DROP POLICY IF EXISTS "Authenticated users can like" ON public.photo_likes;
DROP POLICY IF EXISTS "Users can unlike" ON public.photo_likes;
DROP POLICY IF EXISTS "Likes are public" ON public.photo_likes;
DROP POLICY IF EXISTS "Public can view likes" ON public.photo_likes;
DROP POLICY IF EXISTS "Users can like photos" ON public.photo_likes;
DROP POLICY IF EXISTS "Users can unlike photos" ON public.photo_likes;

CREATE POLICY "Likes are public" ON public.photo_likes 
    FOR SELECT TO public USING (true);
CREATE POLICY "Users can insert likes" ON public.photo_likes 
    FOR INSERT TO authenticated WITH CHECK ((SELECT auth.uid()) = user_id);
CREATE POLICY "Users can delete likes" ON public.photo_likes 
    FOR DELETE TO authenticated USING ((SELECT auth.uid()) = user_id);

-- 5. photo_comments: Consolidate and optimize
DROP POLICY IF EXISTS "Authenticated users can comment" ON public.photo_comments;
DROP POLICY IF EXISTS "Users can update own comments" ON public.photo_comments;
DROP POLICY IF EXISTS "Users can delete own comments" ON public.photo_comments;
DROP POLICY IF EXISTS "Comments are public" ON public.photo_comments;
DROP POLICY IF EXISTS "Public can view comments" ON public.photo_comments;
DROP POLICY IF EXISTS "Users can post comments" ON public.photo_comments;
DROP POLICY IF EXISTS "Users can update their own comments" ON public.photo_comments;
DROP POLICY IF EXISTS "Users can delete their own comments" ON public.photo_comments;

CREATE POLICY "Comments are public" ON public.photo_comments 
    FOR SELECT TO public USING (true);
CREATE POLICY "Users can insert comments" ON public.photo_comments 
    FOR INSERT TO authenticated WITH CHECK ((SELECT auth.uid()) = user_id);
CREATE POLICY "Users can update own comments" ON public.photo_comments 
    FOR UPDATE TO authenticated USING ((SELECT auth.uid()) = user_id);
CREATE POLICY "Users can delete own comments" ON public.photo_comments 
    FOR DELETE TO authenticated USING ((SELECT auth.uid()) = user_id);

-- 6. treats_transactions: Consolidate and optimize
DROP POLICY IF EXISTS "Users can view own transactions" ON public.treats_transactions;
DROP POLICY IF EXISTS "Users can see their own transactions" ON public.treats_transactions;

CREATE POLICY "Users can view own transactions" ON public.treats_transactions 
    FOR SELECT TO authenticated USING (((SELECT auth.uid()) = from_user_id) OR ((SELECT auth.uid()) = to_user_id));

-- 7. reports: Optimize
DROP POLICY IF EXISTS "Users can view their own reports" ON public.reports;
DROP POLICY IF EXISTS "Users can create reports" ON public.reports;

CREATE POLICY "Users can view own reports" ON public.reports 
    FOR SELECT TO authenticated USING ((SELECT auth.uid()) = reporter_id);
CREATE POLICY "Users can create reports" ON public.reports 
    FOR INSERT TO authenticated WITH CHECK ((SELECT auth.uid()) = reporter_id);

-- 8. profile_table(users): Optimize
-- Note: 'users' table policies 'Users can read own profile' etc. 
-- Already seem to use Select auth.uid() in the pg_policies list but let's re-apply to be sure.
DROP POLICY IF EXISTS "Users can read own profile" ON public.users;
DROP POLICY IF EXISTS "Users can update own profile" ON public.users;
DROP POLICY IF EXISTS "Users can update their own data" ON public.users;
DROP POLICY IF EXISTS "Public users can view all users" ON public.users;

CREATE POLICY "Users can read own profile" ON public.users 
    FOR SELECT TO authenticated USING ((SELECT auth.uid()) = id);
CREATE POLICY "Users can update own profile" ON public.users 
    FOR UPDATE TO authenticated USING ((SELECT auth.uid()) = id);
CREATE POLICY "Public users can view all users" ON public.users 
    FOR SELECT TO public USING (true);

