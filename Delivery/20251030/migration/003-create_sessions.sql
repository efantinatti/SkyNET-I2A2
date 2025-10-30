-- 003-create_sessions.sql
-- Create sessions table to track usage and quick stats

CREATE TABLE IF NOT EXISTS sessions (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  documents_processed INT DEFAULT 0,
  analyses_run INT DEFAULT 0,
  created_at TIMESTAMPTZ DEFAULT now()
);

-- Optionally insert an initial session row
INSERT INTO sessions (documents_processed, analyses_run) VALUES (0,0) ON CONFLICT DO NOTHING;
