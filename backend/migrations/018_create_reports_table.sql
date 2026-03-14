-- Migration: Create Reports Table for Content Moderation

CREATE TABLE IF NOT EXISTS reports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    photo_id UUID REFERENCES cat_photos(id) ON DELETE CASCADE NOT NULL,
    reporter_id UUID REFERENCES users(id) ON DELETE SET NULL, -- Nullable if user is deleted later
    reason VARCHAR(50) NOT NULL, -- e.g., 'spam', 'nudity', 'not_a_cat'
    details TEXT,
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'resolved', 'dismissed')),
    resolution_notes TEXT,
    resolved_by UUID REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    resolved_at TIMESTAMPTZ
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_reports_photo_id ON reports(photo_id);
CREATE INDEX IF NOT EXISTS idx_reports_status ON reports(status);
CREATE INDEX IF NOT EXISTS idx_reports_created_at ON reports(created_at);

-- RLS
ALTER TABLE reports ENABLE ROW LEVEL SECURITY;

-- Policies
-- 1. Reporters can view their own reports
CREATE POLICY "Users can view their own reports" ON reports
    FOR SELECT TO authenticated
    USING (auth.uid() = reporter_id);

-- 2. Reporters can create reports
CREATE POLICY "Users can create reports" ON reports
    FOR INSERT TO authenticated
    WITH CHECK (auth.uid() = reporter_id);
    
-- 3. Admins (Service Role or specific admin implementation) have full access
-- Note: Supabase Service Role bypasses RLS, so this is mainly for application users.
-- We might need a policy for 'admin' role if we use RLS for admins, but currently admins use the same auth context.
-- For now, our admin API uses `get_supabase_admin_client` (Service Role) which bypasses RLS, so we don't strictly need an RLS policy for admins unless we want them to use the client-side SDK.
