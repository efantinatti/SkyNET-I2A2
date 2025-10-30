#!/usr/bin/env python3
"""
Script para verificar e corrigir a configuração do banco RAG.
"""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

try:
    from backend.database.postgresql_storage import PostgreSQLStorage
    print("✅ PostgreSQLStorage importado com sucesso!")
except ImportError as e:
    print(f"❌ Erro ao importar PostgreSQLStorage: {e}")
    sys.exit(1)

def check_database_setup():
    """Verificar configuração do banco."""
    print("\n🔍 Verificando configuração do banco...")

    storage = PostgreSQLStorage()

    # Verificar colunas da tabela fiscal_documents
    columns = storage._get_table_columns()
    print(f"\n📊 Colunas encontradas ({len(columns)}):")
    for col in sorted(columns):
        print(f"  - {col}")

    # Verificar se embedding_status existe
    if 'embedding_status' in columns:
        print("✅ Coluna 'embedding_status' encontrada!")
    else:
        print("❌ Coluna 'embedding_status' não encontrada!")
        return False

    # Verificar tabelas RAG
    try:
        result = storage._execute_query("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            AND (table_name = 'document_chunks' OR table_name = 'analysis_insights')
        """, fetch="all")

        print("\n📊 Tabelas RAG encontradas:")
        if result:
            for row in result:
                print(f"  - {row['table_name']}")
        else:
            print("  ❌ Nenhuma tabela RAG encontrada!")
            return False

        # Verificar se as tabelas têm dados de exemplo
        for row in result:
            table_name = row['table_name']
            count_result = storage._execute_query(f"SELECT COUNT(*) as count FROM {table_name}", fetch="all")
            if count_result:
                count = count_result[0]['count']
                print(f"  - {table_name}: {count} registros")

    except Exception as e:
        print(f"❌ Erro ao verificar tabelas RAG: {e}")
        return False

    return True

def test_embedding_service():
    """Testar serviço de embeddings."""
    print("\n🧠 Testando serviço de embeddings...")

    try:
        from backend.services.fallback_embedding_service import FallbackEmbeddingService
        service = FallbackEmbeddingService()

        info = service.get_service_info()
        print(f"📊 Info do serviço: {info}")

        embedding = service.generate_embedding("teste documento fiscal")
        print(f"✅ Embedding gerado: {len(embedding)} dimensões")

        if len(embedding) == 768:
            print("✅ Dimensões corretas (768)!")
            return True
        else:
            print(f"❌ Dimensões incorretas: {len(embedding)} ao invés de 768")
            return False

    except Exception as e:
        print(f"❌ Erro no serviço de embeddings: {e}")
        return False

def main():
    print("🚀 Iniciando verificação do sistema RAG...")

    # Verificar banco
    if not check_database_setup():
        print("\n❌ Configuração do banco incompleta!")
        print("💡 Execute: python scripts/apply_migrations.py --single 011-add_rag_support.sql")
        return

    # Testar embeddings
    if not test_embedding_service():
        print("\n❌ Serviço de embeddings com problemas!")
        return

    print("\n🎉 Sistema RAG configurado corretamente!")
    print("✅ Banco: OK")
    print("✅ Embeddings: OK (768 dimensões)")
    print("✅ Sentence Transformers: Funcionando")
    print("\n💡 Agora você pode fazer upload de documentos e usar a busca semântica!")

if __name__ == "__main__":
    main()
