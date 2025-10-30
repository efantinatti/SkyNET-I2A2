-- 013-add_updated_at_column.sql
-- Add updated_at column to fiscal_documents table

SELECT 'Starting updated_at column migration...' as migration_status;

-- Add updated_at column to fiscal_documents table
ALTER TABLE fiscal_documents
ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ DEFAULT now();

-- Create index for updated_at for better query performance
CREATE INDEX IF NOT EXISTS idx_fiscal_documents_updated_at ON fiscal_documents (updated_at);

-- Update existing records to have updated_at set to created_at
UPDATE fiscal_documents
SET updated_at = created_at
WHERE updated_at IS NULL;

SELECT 'Updated_at column migration completed successfully' as migration_status;
