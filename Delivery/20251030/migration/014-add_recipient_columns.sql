-- 014-add_recipient_columns.sql
-- Add recipient columns to fiscal_documents table

SELECT 'Starting recipient columns migration...' as migration_status;

-- Add recipient columns to fiscal_documents table
ALTER TABLE fiscal_documents
ADD COLUMN IF NOT EXISTS recipient_cnpj VARCHAR,
ADD COLUMN IF NOT EXISTS recipient_name VARCHAR;

-- Create indexes for recipient columns for better query performance
CREATE INDEX IF NOT EXISTS idx_fiscal_documents_recipient_cnpj ON fiscal_documents (recipient_cnpj);
CREATE INDEX IF NOT EXISTS idx_fiscal_documents_recipient_name ON fiscal_documents (recipient_name);

SELECT 'Recipient columns migration completed successfully' as migration_status;
