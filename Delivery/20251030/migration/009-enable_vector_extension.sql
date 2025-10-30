-- 009-enable_vector_extension.sql
-- Enable pgvector extension for vector embeddings support

-- Try to enable the pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Simple check to verify extension status
SELECT 
    CASE 
        WHEN extname = 'vector' 
        THEN 'VECTOR_EXTENSION_ENABLED' 
        ELSE 'VECTOR_EXTENSION_NOT_AVAILABLE'
    END AS vector_status
FROM pg_extension 
WHERE extname = 'vector';