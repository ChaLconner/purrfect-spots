-- Missing indexes for foreign keys
CREATE INDEX IF NOT EXISTS idx_config_history_changed_by ON public.config_history(changed_by);
CREATE INDEX IF NOT EXISTS idx_config_history_config_key ON public.config_history(config_key);
CREATE INDEX IF NOT EXISTS idx_notifications_actor_id ON public.notifications(actor_id);
CREATE INDEX IF NOT EXISTS idx_pending_config_changes_approver_id ON public.pending_config_changes(approver_id);
CREATE INDEX IF NOT EXISTS idx_pending_config_changes_config_key ON public.pending_config_changes(config_key);
CREATE INDEX IF NOT EXISTS idx_pending_config_changes_requester_id ON public.pending_config_changes(requester_id);
CREATE INDEX IF NOT EXISTS idx_photo_comments_user_id ON public.photo_comments(user_id);
CREATE INDEX IF NOT EXISTS idx_reports_reporter_id ON public.reports(reporter_id);
CREATE INDEX IF NOT EXISTS idx_reports_resolved_by ON public.reports(resolved_by);
CREATE INDEX IF NOT EXISTS idx_role_permissions_permission_id ON public.role_permissions(permission_id);
CREATE INDEX IF NOT EXISTS idx_saved_spots_photo_id ON public.saved_spots(photo_id);
CREATE INDEX IF NOT EXISTS idx_system_configs_updated_by ON public.system_configs(updated_by);
CREATE INDEX IF NOT EXISTS idx_treats_transactions_photo_id ON public.treats_transactions(photo_id);
CREATE INDEX IF NOT EXISTS idx_users_role_id ON public.users(role_id);

