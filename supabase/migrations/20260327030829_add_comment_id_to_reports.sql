ALTER TABLE reports ADD COLUMN comment_id UUID REFERENCES photo_comments(id) ON DELETE CASCADE;
CREATE INDEX idx_reports_comment_id ON reports(comment_id);

-- Update status check with comment_id logic
ALTER TABLE reports DROP CONSTRAINT IF EXISTS reports_status_check;
ALTER TABLE reports ADD CONSTRAINT reports_status_check 
CHECK (status = ANY (ARRAY['pending', 'resolved', 'dismissed']));

