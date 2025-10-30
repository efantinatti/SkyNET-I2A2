-- Ativar extensão de vetores
CREATE EXTENSION IF NOT EXISTS vector;

-- Tabela para armazenar pedaços de documentos
CREATE TABLE IF NOT EXISTS document_chunks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    fiscal_document_id UUID NOT NULL REFERENCES fiscal_documents(id) ON DELETE CASCADE,
    chunk_number INTEGER NOT NULL,
    content_text TEXT NOT NULL,
    embedding VECTOR(768),
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(fiscal_document_id, chunk_number)
);

-- Tabela para armazenar insights extraídos
CREATE TABLE IF NOT EXISTS analysis_insights (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    fiscal_document_id UUID NOT NULL REFERENCES fiscal_documents(id) ON DELETE CASCADE,
    insight_type VARCHAR NOT NULL,
    insight_category VARCHAR,
    insight_text TEXT NOT NULL,
    confidence_score DECIMAL(3,2) CHECK (confidence_score >= 0 AND confidence_score <= 1),
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Adicionar colunas à tabela de documentos
ALTER TABLE fiscal_documents
ADD COLUMN IF NOT EXISTS document_type VARCHAR,
ADD COLUMN IF NOT EXISTS document_data JSONB,
ADD COLUMN IF NOT EXISTS embedding_status VARCHAR DEFAULT 'pending',
ADD COLUMN IF NOT EXISTS last_embedding_update TIMESTAMPTZ;

-- Criar índices para performance
CREATE INDEX IF NOT EXISTS idx_document_chunks_fiscal_document_id ON document_chunks(fiscal_document_id);
CREATE INDEX IF NOT EXISTS idx_analysis_insights_document_id ON analysis_insights(fiscal_document_id);
CREATE INDEX IF NOT EXISTS idx_fiscal_documents_embedding_status ON fiscal_documents(embedding_status);
