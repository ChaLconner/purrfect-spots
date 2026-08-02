ALTER TABLE public.users ADD COLUMN last_token_revocation_at TIMESTAMP WITH TIME ZONE;
COMMENT ON COLUMN public.users.last_token_revocation_at IS 'Timestamp used to invalidate all tokens issued before this date for security events or password changes.';

