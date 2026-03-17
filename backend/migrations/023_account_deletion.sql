-- 1. Add Soft Delete field to users table
ALTER TABLE users ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMPTZ DEFAULT NULL;

-- 2. Create account_deletion_requests table
CREATE TABLE IF NOT EXISTS account_deletion_requests (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    requested_at TIMESTAMPTZ DEFAULT NOW(),
    scheduled_deletion_at TIMESTAMPTZ NOT NULL,
    status VARCHAR(20) DEFAULT 'pending',
    client_ip VARCHAR(45),
    UNIQUE(user_id, status)
);

-- Ensure RLS on the new table
ALTER TABLE account_deletion_requests ENABLE ROW LEVEL SECURITY;

-- Policies for account_deletion_requests
CREATE POLICY "Users can insert their own deletion requests" 
ON account_deletion_requests FOR INSERT 
WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can view their own deletion requests" 
ON account_deletion_requests FOR SELECT 
USING (auth.uid() = user_id);

CREATE POLICY "Users can update their own deletion requests" 
ON account_deletion_requests FOR UPDATE 
USING (auth.uid() = user_id);

-- Policies for audit_logs (Existing table)
-- Allow users to insert logs for their own account actions
CREATE POLICY "Users can insert their own audit logs"
ON audit_logs FOR INSERT
WITH CHECK (auth.uid() = user_id);

