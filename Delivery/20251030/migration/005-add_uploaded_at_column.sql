-- 005-add_uploaded_at_column.sql
-- Add uploaded_at column to fiscal_documents table with default current timestamp

ALTER TABLE fiscal_documents 
ADD COLUMN IF NOT EXISTS uploaded_at TIMESTAMP WITH TIME ZONE DEFAULT now();
