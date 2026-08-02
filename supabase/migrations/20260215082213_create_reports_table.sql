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
