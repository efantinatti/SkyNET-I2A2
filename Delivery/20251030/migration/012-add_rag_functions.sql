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
CREATE INDEX IF NOT EXISTS idx_document_chunks_metadata ON document_chunks USING GIN (metadata);
CREATE INDEX IF NOT EXISTS idx_document_chunks_embedding_hnsw ON document_chunks USING hnsw (embedding vector_cosine_ops);
CREATE INDEX IF NOT EXISTS idx_document_chunks_content_gin ON document_chunks USING GIN (to_tsvector('portuguese', content_text));
CREATE INDEX IF NOT EXISTS idx_analysis_insights_document_id ON analysis_insights(fiscal_document_id);
CREATE INDEX IF NOT EXISTS idx_analysis_insights_type_category ON analysis_insights(insight_type, insight_category);
CREATE INDEX IF NOT EXISTS idx_analysis_insights_confidence ON analysis_insights(confidence_score DESC);
CREATE INDEX IF NOT EXISTS idx_fiscal_documents_document_type ON fiscal_documents(document_type);
CREATE INDEX IF NOT EXISTS idx_fiscal_documents_embedding_status ON fiscal_documents(embedding_status);
CREATE INDEX IF NOT EXISTS idx_fiscal_documents_issuer_cnpj ON fiscal_documents(issuer_cnpj);

-- View para acessar chunks com informações dos documentos
CREATE OR REPLACE VIEW document_chunks_with_docs AS
SELECT
    dc.id,
    dc.fiscal_document_id,
    dc.chunk_number,
    dc.content_text,
    dc.embedding,
    dc.metadata,
    dc.created_at,
    fd.file_name,
    fd.document_type,
    fd.document_number,
    fd.issuer_cnpj,
    fd.extracted_data,
    fd.validation_status,
    fd.classification
FROM document_chunks dc
JOIN fiscal_documents fd ON dc.fiscal_document_id = fd.id;

-- Permissões
GRANT SELECT ON document_chunks_with_docs TO authenticated;
GRANT SELECT ON document_chunks TO authenticated;
GRANT SELECT ON analysis_insights TO authenticated;
GRANT INSERT, UPDATE ON document_chunks TO authenticated;
GRANT INSERT ON analysis_insights TO authenticated;

-- Comentários
COMMENT ON TABLE document_chunks IS 'Armazena chunks de documentos com embeddings para busca semântica';
COMMENT ON TABLE analysis_insights IS 'Armazena insights estruturados extraídos de documentos fiscais';
COMMENT ON COLUMN document_chunks.embedding IS 'Vector embedding 768-dimensional para busca semântica';
COMMENT ON COLUMN document_chunks.metadata IS 'Metadados adicionais para filtros e contexto';