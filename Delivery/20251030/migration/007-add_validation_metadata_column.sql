-- 007-add_validation_metadata_column.sql
-- Adiciona a coluna validation_metadata para armazenar metadados de validação

-- Adiciona a coluna validation_metadata à tabela fiscal_documents
ALTER TABLE fiscal_documents 
ADD COLUMN IF NOT EXISTS validation_metadata JSONB DEFAULT '{}'::jsonb;

-- Comentário para documentação
COMMENT ON COLUMN fiscal_documents.validation_metadata IS 'Armazena metadados sobre o processo de validação do documento, incluindo data da validação, versão do validador e outras informações técnicas.';
