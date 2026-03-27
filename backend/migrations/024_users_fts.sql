-- Migration: Add Full-Text Search for Users
-- Description: Adds a tsvector column for fast name and email searching

-- 1. Add tsvector column
ALTER TABLE users 
ADD COLUMN IF NOT EXISTS search_vector tsvector;

-- 2. Create GIN index
CREATE INDEX IF NOT EXISTS idx_users_search_vector
ON users USING GIN (search_vector);

-- 3. Trigger function to update search_vector
CREATE OR REPLACE FUNCTION users_search_vector_trigger()
RETURNS trigger AS $$
BEGIN
    NEW.search_vector :=
        setweight(to_tsvector('english', COALESCE(NEW.name, '')), 'A') ||
        setweight(to_tsvector('english', COALESCE(NEW.email, '')), 'B') ||
        setweight(to_tsvector('english', COALESCE(NEW.username, '')), 'C');
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 4. Create trigger
DROP TRIGGER IF EXISTS users_search_vector_update ON users;
CREATE TRIGGER users_search_vector_update
BEFORE INSERT OR UPDATE ON users
FOR EACH ROW
EXECUTE FUNCTION users_search_vector_trigger();

-- 5. Populate existing data
UPDATE users
SET search_vector = 
    setweight(to_tsvector('english', COALESCE(name, '')), 'A') ||
    setweight(to_tsvector('english', COALESCE(email, '')), 'B') ||
    setweight(to_tsvector('english', COALESCE(username, '')), 'C')
WHERE search_vector IS NULL;
