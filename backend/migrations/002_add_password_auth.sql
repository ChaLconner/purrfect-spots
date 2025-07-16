-- Add password authentication support to users table
-- Migration: Add password_hash column and make google_id optional

-- Add password_hash column
ALTER TABLE users ADD COLUMN IF NOT EXISTS password_hash VARCHAR(255);

-- Make google_id optional by dropping NOT NULL constraint
ALTER TABLE users ALTER COLUMN google_id DROP NOT NULL;

-- Make google_id unique constraint conditional (only when not null)
DROP INDEX IF EXISTS idx_users_google_id;
CREATE UNIQUE INDEX IF NOT EXISTS idx_users_google_id_unique ON users(google_id) WHERE google_id IS NOT NULL;

-- Add unique constraint on email
ALTER TABLE users ADD CONSTRAINT users_email_unique UNIQUE (email);

-- Create index on email for better performance
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);

-- Update RLS policies to handle both OAuth and password auth
DROP POLICY IF EXISTS "Users can read own data" ON users;
DROP POLICY IF EXISTS "Users can update own data" ON users;

-- New policy: Users can read their own data
CREATE POLICY "Users can read own data" 
ON users FOR SELECT 
USING (auth.uid()::text = id::text);

-- New policy: Users can update their own data
CREATE POLICY "Users can update own data" 
ON users FOR UPDATE 
USING (auth.uid()::text = id::text);

-- Policy: Allow service role to insert users (for password registration)
CREATE POLICY "Service can insert users"
ON users FOR INSERT
WITH CHECK (true);

-- Policy: Allow service role to select users (for authentication)
CREATE POLICY "Service can select users"
ON users FOR SELECT
USING (true);
