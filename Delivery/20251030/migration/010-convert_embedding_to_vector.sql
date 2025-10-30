-- 010-convert_embedding_to_vector.sql
-- Versão corrigida para lidar com strings vazias e tipos de dados

-- 1. Verificar se a extensão vector está disponível
SELECT 'Verificando se a extensão vector está disponível...' as status;

-- Verificação simples
SELECT 
    CASE 
        WHEN NOT EXISTS (SELECT 1 FROM pg_extension WHERE extname = 'vector') 
        THEN 'ERRO: A extensão vector não está disponível. Execute a migração 009 primeiro.'
        WHEN NOT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'document_summaries')
        THEN 'AVISO: Tabela document_summaries não existe. Nada para fazer.'
        WHEN NOT EXISTS (SELECT 1 FROM information_schema.columns 
                        WHERE table_name = 'document_summaries' 
                        AND column_name = 'embedding_vector')
        THEN 'AVISO: Coluna embedding_vector não existe. Nada para fazer.'
        WHEN EXISTS (SELECT 1 FROM information_schema.columns 
                    WHERE table_name = 'document_summaries' 
                    AND column_name = 'embedding_vector' 
                    AND data_type = 'USER-DEFINED')
        THEN 'AVISO: A coluna já está no formato VECTOR. Nada para fazer.'
        ELSE 'OK: Pronto para converter de TEXT para VECTOR'
    END as status;

-- 2. Criar backup dos dados existentes
SELECT 'Criando backup da tabela document_summaries...' as status;
CREATE TABLE IF NOT EXISTS document_summaries_backup AS
SELECT * FROM document_summaries;

-- 3. Adicionar nova coluna VECTOR
SELECT 'Adicionando nova coluna VECTOR...' as status;
ALTER TABLE document_summaries 
ADD COLUMN IF NOT EXISTS embedding_vector_new VECTOR(768);

-- 4. Converter dados existentes
SELECT 'Convertendo dados existentes...' as status;
UPDATE document_summaries
SET embedding_vector_new = 
    CASE 
        WHEN embedding_vector IS NOT NULL 
             AND CAST(embedding_vector AS TEXT) != ''
             AND CAST(embedding_vector AS TEXT) != 'null'
             AND CAST(embedding_vector AS TEXT) LIKE '%"embedding"%'
        THEN 
            CASE 
                WHEN (CAST(embedding_vector AS TEXT)::jsonb->>'embedding') IS NOT NULL
                THEN (CAST(embedding_vector AS TEXT)::jsonb->>'embedding')::vector
                ELSE NULL
            END
        ELSE NULL
    END
WHERE embedding_vector IS NOT NULL;

-- 5. Verificar resultados da conversão
SELECT 'Verificando resultados da conversão...' as status;
SELECT 
    'Resultados da conversão:' as info,
    COUNT(*) as total_linhas,
    COUNT(embedding_vector) as com_dados_originais,
    COUNT(embedding_vector_new) as convertidos_com_sucesso,
    COUNT(CASE WHEN embedding_vector IS NOT NULL AND embedding_vector_new IS NULL THEN 1 END) as falhas_conversao
FROM document_summaries;

-- 6. Remover a restrição de chave estrangeira se existir
SELECT 'Removendo restrição de chave estrangeira...' as status;
ALTER TABLE document_summaries 
DROP CONSTRAINT IF EXISTS document_summaries_fiscal_document_id_fkey;

-- 7. Remover a coluna antiga
SELECT 'Removendo coluna antiga...' as status;
ALTER TABLE document_summaries 
DROP COLUMN IF EXISTS embedding_vector;

-- 8. Renomear a nova coluna
SELECT 'Renomeando coluna...' as status;
ALTER TABLE document_summaries 
RENAME COLUMN embedding_vector_new TO embedding_vector;

-- 9. Adicionar comentário à coluna
COMMENT ON COLUMN document_summaries.embedding_vector IS 'Vector embedding para busca semântica (768 dimensões)';

-- 10. Recriar a restrição de chave estrangeira
SELECT 'Recriando restrição de chave estrangeira...' as status;
ALTER TABLE document_summaries
ADD CONSTRAINT document_summaries_fiscal_document_id_fkey 
FOREIGN KEY (fiscal_document_id) 
REFERENCES fiscal_documents(id) 
ON DELETE CASCADE;

SELECT 'Migração 010 concluída com sucesso!' as status;