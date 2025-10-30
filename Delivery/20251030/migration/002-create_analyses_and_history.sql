-- 002-create_analyses_and_history.sql
-- Create analyses and document_history tables

CREATE TABLE IF NOT EXISTS analyses (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  csv_file_name VARCHAR,
  analysis_data JSONB,
  charts JSONB,
  created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS document_history (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  fiscal_document_id UUID REFERENCES fiscal_documents(id) ON DELETE CASCADE,
  event_type VARCHAR, -- e.g. 'created', 'validated', 'classified', 'updated'
  event_data JSONB,
  created_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_analyses_created_at ON analyses (created_at);
CREATE INDEX IF NOT EXISTS idx_document_history_fiscal_id ON document_history (fiscal_document_id);
