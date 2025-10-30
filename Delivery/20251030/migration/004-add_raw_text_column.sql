-- 004-add_raw_text_column.sql
-- Add raw_text column to fiscal_documents table

ALTER TABLE fiscal_documents 
ADD COLUMN IF NOT EXISTS raw_text TEXT;