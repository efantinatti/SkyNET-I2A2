-- 006-add_validation_columns.sql
-- Adiciona colunas para suporte à validação de documentos

-- Adiciona colunas à tabela fiscal_documents
ALTER TABLE fiscal_documents 
ADD COLUMN IF NOT EXISTS cfop VARCHAR,
ADD COLUMN IF NOT EXISTS issuer_name VARCHAR,
ADD COLUMN IF NOT EXISTS issue_date TIMESTAMPTZ,
ADD COLUMN IF NOT EXISTS total_value DECIMAL(10, 2) DEFAULT 0.0,
ADD COLUMN IF NOT EXISTS processed_at TIMESTAMPTZ,
ADD COLUMN IF NOT EXISTS validation_details JSONB DEFAULT '{}'::jsonb,
ADD COLUMN IF NOT EXISTS raw_text TEXT;

-- Atualiza a coluna raw_text para extrair do extracted_data se estiver vazia
UPDATE fiscal_documents 
SET raw_text = extracted_data->>'raw_text'
WHERE raw_text IS NULL AND extracted_data ? 'raw_text';

-- Remove raw_text do extracted_data para evitar duplicação
UPDATE fiscal_documents 
SET extracted_data = extracted_data - 'raw_text'
WHERE extracted_data ? 'raw_text';

-- Cria índices para melhorar consultas comuns
CREATE INDEX IF NOT EXISTS idx_fiscal_documents_cfop ON fiscal_documents (cfop);
CREATE INDEX IF NOT EXISTS idx_fiscal_documents_validation_status ON fiscal_documents (validation_status);
CREATE INDEX IF NOT EXISTS idx_fiscal_documents_issue_date ON fiscal_documents (issue_date);
