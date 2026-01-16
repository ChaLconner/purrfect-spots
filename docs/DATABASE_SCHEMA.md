# 📊 Database Schema Documentation

## Overview

Purrfect Spots uses **Supabase** (PostgreSQL) as the database backend. This document describes the database schema, relationships, and Row Level Security (RLS) policies.

## Entity Relationship Diagram

```
┌─────────────────────┐         ┌─────────────────────┐
│       users         │         │     cat_photos      │
├─────────────────────┤         ├─────────────────────┤
│ id (PK, UUID)       │◄───────┤│ user_id (FK)        │
│ email               │    1:N  │ id (PK, UUID)       │
│ name                │         │ location_name       │
│ picture             │         │ description         │
│ bio                 │         │ latitude            │
│ password_hash       │         │ longitude           │
│ auth_provider       │         │ image_url           │
│ created_at          │         │ tags[]              │
│ updated_at          │         │ uploaded_at         │
└─────────────────────┘         └─────────────────────┘
```

---

## Tables

### 1. `users` Table

Stores user account information for both Google OAuth and email/password authentication.

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `id` | UUID | No | `gen_random_uuid()` | Primary key, unique identifier |
| `email` | VARCHAR(255) | No | - | User's email address (unique) |
| `name` | VARCHAR(255) | Yes | - | Display name |
| `picture` | TEXT | Yes | - | Profile picture URL |
| `bio` | TEXT | Yes | - | User biography |
| `password_hash` | TEXT | Yes | - | Bcrypt hashed password (null for OAuth users) |
| `auth_provider` | VARCHAR(50) | Yes | `'email'` | Authentication provider (`'email'`, `'google'`) |
| `created_at` | TIMESTAMPTZ | No | `now()` | Account creation timestamp |
| `updated_at` | TIMESTAMPTZ | Yes | - | Last update timestamp |

#### Indexes
- `users_pkey` - Primary key on `id`
- `users_email_key` - Unique constraint on `email`

#### SQL Definition
```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255),
    picture TEXT,
    bio TEXT,
    password_hash TEXT,
    auth_provider VARCHAR(50) DEFAULT 'email',
    created_at TIMESTAMPTZ DEFAULT now() NOT NULL,
    updated_at TIMESTAMPTZ
);

-- Index for faster email lookups
CREATE INDEX idx_users_email ON users(email);
```

---

### 2. `cat_photos` Table

Stores uploaded cat photos with location information.

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `id` | UUID | No | `gen_random_uuid()` | Primary key |
| `user_id` | UUID | No | - | Foreign key to `users.id` |
| `location_name` | VARCHAR(255) | No | - | Name of the location |
| `description` | TEXT | Yes | - | Photo description |
| `latitude` | DECIMAL(10,7) | No | - | Location latitude (-90 to 90) |
| `longitude` | DECIMAL(11,7) | No | - | Location longitude (-180 to 180) |
| `image_url` | TEXT | No | - | S3 URL of the uploaded image |
| `tags` | TEXT[] | Yes | `'{}'` | Array of tags for categorization |
| `uploaded_at` | TIMESTAMPTZ | No | `now()` | Upload timestamp |

#### Indexes
- `cat_photos_pkey` - Primary key on `id`
- `idx_cat_photos_user_id` - Index on `user_id`
- `idx_cat_photos_uploaded_at` - Index on `uploaded_at` (DESC)
- `idx_cat_photos_location` - Composite index on `(latitude, longitude)`
- `idx_cat_photos_tags` - GIN index on `tags` array
- `idx_cat_photos_location_name` - B-tree index on `location_name` for pattern matching
- `idx_cat_photos_user_uploaded` - Composite index on `(user_id, uploaded_at DESC)`
- `idx_cat_photos_geo` - Composite index for geospatial queries
- `idx_cat_photos_search_vector` - GIN index on `search_vector` for full-text search
- `idx_cat_photos_location_gist` - GIST index on `location` geography column (PostGIS)

#### SQL Definition
```sql
CREATE TABLE cat_photos (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    location_name VARCHAR(255) NOT NULL,
    description TEXT,
    latitude DECIMAL(10,7) NOT NULL CHECK (latitude >= -90 AND latitude <= 90),
    longitude DECIMAL(11,7) NOT NULL CHECK (longitude >= -180 AND longitude <= 180),
    image_url TEXT NOT NULL,
    tags TEXT[] DEFAULT '{}',
    search_vector tsvector,  -- Full-text search vector
    location GEOGRAPHY(POINT, 4326),  -- PostGIS geography column for accurate distance queries
    uploaded_at TIMESTAMPTZ DEFAULT now() NOT NULL
);

-- Basic indexes for performance
CREATE INDEX idx_cat_photos_user_id ON cat_photos(user_id);
CREATE INDEX idx_cat_photos_uploaded_at ON cat_photos(uploaded_at DESC);
CREATE INDEX idx_cat_photos_location ON cat_photos(latitude, longitude);
CREATE INDEX idx_cat_photos_tags ON cat_photos USING GIN(tags);

-- Additional search indexes (see migration 002)
CREATE INDEX idx_cat_photos_location_name ON cat_photos(location_name);
CREATE INDEX idx_cat_photos_user_uploaded ON cat_photos(user_id, uploaded_at DESC);
CREATE INDEX idx_cat_photos_geo ON cat_photos(latitude, longitude);
CREATE INDEX idx_cat_photos_search_vector ON cat_photos USING GIN(search_vector);
```

---

## Row Level Security (RLS) Policies

### `users` Table Policies

```sql
-- Enable RLS
ALTER TABLE users ENABLE ROW LEVEL SECURITY;

-- Users can read their own data
CREATE POLICY "Users can view own profile"
ON users FOR SELECT
USING (auth.uid() = id);

-- Users can update their own data
CREATE POLICY "Users can update own profile"
ON users FOR UPDATE
USING (auth.uid() = id);

-- Service role can insert new users
CREATE POLICY "Service role can insert users"
ON users FOR INSERT
TO service_role
WITH CHECK (true);
```

### `cat_photos` Table Policies

```sql
-- Enable RLS
ALTER TABLE cat_photos ENABLE ROW LEVEL SECURITY;

-- Anyone can view photos (public gallery)
CREATE POLICY "Photos are publicly viewable"
ON cat_photos FOR SELECT
USING (true);

-- Authenticated users can insert photos
CREATE POLICY "Authenticated users can insert photos"
ON cat_photos FOR INSERT
TO authenticated
WITH CHECK (auth.uid() = user_id);

-- Users can update their own photos
CREATE POLICY "Users can update own photos"
ON cat_photos FOR UPDATE
USING (auth.uid() = user_id);

-- Users can delete their own photos
CREATE POLICY "Users can delete own photos"
ON cat_photos FOR DELETE
USING (auth.uid() = user_id);
```

---

## Storage Buckets

### `cat-images` Bucket

AWS S3 bucket for storing cat images.

| Property | Value |
|----------|-------|
| Bucket Name | `purrfect-spots-images` (configurable) |
| Region | `ap-southeast-2` (configurable) |
| Access | Private (presigned URLs for access) |
| Max File Size | 10 MB |
| Allowed Types | `image/jpeg`, `image/png`, `image/gif`, `image/webp` |

#### Naming Convention
```
cat_photos/{uuid}.{extension}
```

---

## Migrations

### Initial Schema (v1.0.0)

```sql
-- Migration: 001_initial_schema.sql
-- Description: Create initial database schema

-- Create users table
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255),
    picture TEXT,
    bio TEXT,
    password_hash TEXT,
    auth_provider VARCHAR(50) DEFAULT 'email',
    created_at TIMESTAMPTZ DEFAULT now() NOT NULL,
    updated_at TIMESTAMPTZ
);

-- Create cat_photos table
CREATE TABLE IF NOT EXISTS cat_photos (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    location_name VARCHAR(255) NOT NULL,
    description TEXT,
    latitude DECIMAL(10,7) NOT NULL,
    longitude DECIMAL(11,7) NOT NULL,
    image_url TEXT NOT NULL,
    tags TEXT[] DEFAULT '{}',
    uploaded_at TIMESTAMPTZ DEFAULT now() NOT NULL
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_cat_photos_user_id ON cat_photos(user_id);
CREATE INDEX IF NOT EXISTS idx_cat_photos_uploaded_at ON cat_photos(uploaded_at DESC);
CREATE INDEX IF NOT EXISTS idx_cat_photos_tags ON cat_photos USING GIN(tags);
```

### Add Tags Column Migration

```sql
-- Migration: 002_add_tags.sql
-- Description: Add tags array column to cat_photos

ALTER TABLE cat_photos 
ADD COLUMN IF NOT EXISTS tags TEXT[] DEFAULT '{}';

CREATE INDEX IF NOT EXISTS idx_cat_photos_tags 
ON cat_photos USING GIN(tags);
```

---

## Query Examples

### Get all photos with pagination
```sql
SELECT * FROM cat_photos
ORDER BY uploaded_at DESC
LIMIT 20 OFFSET 0;
```

### Get photos by tag
```sql
SELECT * FROM cat_photos
WHERE tags @> ARRAY['orange']
ORDER BY uploaded_at DESC;
```

### Get popular tags
```sql
SELECT tag, COUNT(*) as count
FROM cat_photos, UNNEST(tags) as tag
GROUP BY tag
ORDER BY count DESC
LIMIT 10;
```

### Search photos
```sql
SELECT * FROM cat_photos
WHERE location_name ILIKE '%park%'
   OR description ILIKE '%park%'
ORDER BY uploaded_at DESC;
```

### Get user's photos
```sql
SELECT * FROM cat_photos
WHERE user_id = $1
ORDER BY uploaded_at DESC;
```

---

## Performance Considerations

1. **Pagination**: Always use `LIMIT` and `OFFSET` or cursor-based pagination
2. **Tag searches**: GIN index enables efficient array containment queries
3. **Location queries**: PostGIS extension enabled with `ST_DWithin` for accurate radius searches
4. **Image storage**: Images stored in S3, only URLs in database
5. **PostGIS**: Use `search_nearby_photos()` RPC function for efficient nearby queries

---

## Backup & Recovery

- Supabase provides automatic daily backups
- Point-in-time recovery available on Pro plan
- Export functionality via Supabase dashboard

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2024-01-01 | Initial schema creation |
| 1.1.0 | 2024-06-01 | Added tags array column |
| 1.2.0 | 2024-12-01 | Added GIN index for tags |
| 1.3.0 | 2026-01-15 | Added PostGIS extension, geography column, and `search_nearby_photos` RPC |
