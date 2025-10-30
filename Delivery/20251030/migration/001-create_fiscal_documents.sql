-- 001-create_fiscal_documents.sql
-- Create fiscal_documents table

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE TABLE IF NOT EXISTS fiscal_documents (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  file_name VARCHAR,
  document_type VARCHAR,
  document_number VARCHAR,
  issuer_cnpj VARCHAR,
  extracted_data JSONB,
  validation_status VARCHAR,
  classification JSONB,
  created_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_fiscal_documents_issuer_cnpj ON fiscal_documents (issuer_cnpj);
CREATE INDEX IF NOT EXISTS idx_fiscal_documents_document_number ON fiscal_documents (document_number);
