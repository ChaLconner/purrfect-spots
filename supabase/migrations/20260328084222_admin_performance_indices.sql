-- Optimize Users table for role-based filtering and sorting by join date
CREATE INDEX IF NOT EXISTS idx_users_role_id ON public.users(role_id);
CREATE INDEX IF NOT EXISTS idx_users_created_at_desc ON public.users(created_at DESC);

-- Optimize Reports table for status and reason filtering
CREATE INDEX IF NOT EXISTS idx_reports_status ON public.reports(status);
CREATE INDEX IF NOT EXISTS idx_reports_reason ON public.reports(reason);
CREATE INDEX IF NOT EXISTS idx_reports_created_at_desc ON public.reports(created_at DESC);

-- Optimize Audit Logs table (often the largest)
CREATE INDEX IF NOT EXISTS idx_audit_logs_action ON public.audit_logs(action);
CREATE INDEX IF NOT EXISTS idx_audit_logs_resource ON public.audit_logs(resource);
CREATE INDEX IF NOT EXISTS idx_audit_logs_user_id ON public.audit_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_created_at_desc ON public.audit_logs(created_at DESC);

-- Optimize Cat Photos for moderation status
CREATE INDEX IF NOT EXISTS idx_cat_photos_status ON public.cat_photos(status);
CREATE INDEX IF NOT EXISTS idx_cat_photos_uploaded_at_desc ON public.cat_photos(uploaded_at DESC);

