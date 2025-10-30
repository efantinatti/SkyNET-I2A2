-- 008-create_chat_system.sql
-- Create tables for chat system with LLM support

-- Chat sessions table
CREATE TABLE IF NOT EXISTS chat_sessions (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  session_name VARCHAR,
  user_id VARCHAR, -- Optional: for multi-user support
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now(),
  is_active BOOLEAN DEFAULT true
);

-- Chat messages table
CREATE TABLE IF NOT EXISTS chat_messages (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  session_id UUID REFERENCES chat_sessions(id) ON DELETE CASCADE,
  message_type VARCHAR NOT NULL CHECK (message_type IN ('user', 'assistant', 'system')),
  content TEXT NOT NULL,
  metadata JSONB DEFAULT '{}', -- Store tokens, model info, etc.
  created_at TIMESTAMPTZ DEFAULT now()
);

-- Analysis cache table - stores LLM responses to avoid redundant calls
CREATE TABLE IF NOT EXISTS analysis_cache (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  cache_key VARCHAR UNIQUE NOT NULL, -- Hash of query + context
  query_type VARCHAR NOT NULL, -- 'document_analysis', 'csv_analysis', 'general'
  query_text TEXT NOT NULL,
  context_data JSONB, -- Document IDs, CSV summary, etc.
  response_content TEXT NOT NULL,
  response_metadata JSONB DEFAULT '{}', -- Tokens used, model, timestamp
  created_at TIMESTAMPTZ DEFAULT now(),
  expires_at TIMESTAMPTZ DEFAULT (now() + interval '7 days')
);

-- Document embeddings/summaries for efficient retrieval
CREATE TABLE IF NOT EXISTS document_summaries (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  fiscal_document_id UUID REFERENCES fiscal_documents(id) ON DELETE CASCADE,
  summary_text TEXT,
  key_insights JSONB, -- Extracted insights as structured data
  embedding_vector TEXT, -- Store as JSON string for now, will be converted to VECTOR later
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

-- Analysis insights table - stores structured insights from documents
CREATE TABLE IF NOT EXISTS analysis_insights (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  fiscal_document_id UUID REFERENCES fiscal_documents(id) ON DELETE CASCADE,
  analysis_id UUID REFERENCES analyses(id) ON DELETE SET NULL,
  insight_type VARCHAR NOT NULL, -- 'financial', 'tax', 'operational', 'trend'
  insight_category VARCHAR, -- 'revenue', 'expenses', 'tax_credits', 'irregularities'
  insight_text TEXT NOT NULL,
  confidence_score DECIMAL(3,2), -- 0.00 to 1.00
  metadata JSONB DEFAULT '{}',
  created_at TIMESTAMPTZ DEFAULT now()
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_chat_sessions_user_id ON chat_sessions (user_id);
CREATE INDEX IF NOT EXISTS idx_chat_sessions_created_at ON chat_sessions (created_at);
CREATE INDEX IF NOT EXISTS idx_chat_messages_session_id ON chat_messages (session_id);
CREATE INDEX IF NOT EXISTS idx_chat_messages_created_at ON chat_messages (created_at);
CREATE INDEX IF NOT EXISTS idx_chat_messages_type ON chat_messages (message_type);
CREATE INDEX IF NOT EXISTS idx_analysis_cache_key ON analysis_cache (cache_key);
CREATE INDEX IF NOT EXISTS idx_analysis_cache_query_type ON analysis_cache (query_type);
CREATE INDEX IF NOT EXISTS idx_analysis_cache_expires_at ON analysis_cache (expires_at);
CREATE INDEX IF NOT EXISTS idx_document_summaries_fiscal_id ON document_summaries (fiscal_document_id);
CREATE INDEX IF NOT EXISTS idx_analysis_insights_document_id ON analysis_insights (fiscal_document_id);
CREATE INDEX IF NOT EXISTS idx_analysis_insights_type_category ON analysis_insights (insight_type, insight_category);
