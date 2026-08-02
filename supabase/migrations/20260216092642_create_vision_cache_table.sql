CREATE TABLE IF NOT EXISTS vision_analysis_cache (
    image_hash TEXT PRIMARY KEY,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    response JSONB NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_vision_cache_timestamp ON vision_analysis_cache(timestamp);
