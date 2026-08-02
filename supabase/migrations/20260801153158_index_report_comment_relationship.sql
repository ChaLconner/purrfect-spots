-- Cover the composite reports -> photo_comments foreign key so parent-row
-- deletes and integrity checks do not scan the reports table.
CREATE INDEX idx_reports_comment_photo
ON public.reports (comment_id, photo_id)
WHERE comment_id IS NOT NULL;


