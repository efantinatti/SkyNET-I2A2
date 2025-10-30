#!/usr/bin/env python3
"""
Script para debugar o problema específico de documento não sendo encontrado.
"""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

def debug_document_issue():
    """Debuga o problema específico de documento não sendo encontrado."""
    print("🔍 Debugando problema de documento não encontrado...")

    try:
        from backend.database.postgresql_storage import PostgreSQLStorage

        storage = PostgreSQLStorage()
        print("✅ PostgreSQL storage inicializado")

        # Teste 1: Verificar se há documentos no banco
        count_query = "SELECT COUNT(*) as count FROM fiscal_documents"
        count_result = storage._execute_query(count_query, fetch="one")
        print(f"📊 Total de documentos no banco: {count_result['count'] if count_result else 0}")

        # Teste 2: Listar os últimos documentos
        docs_query = "SELECT id, file_name, created_at FROM fiscal_documents ORDER BY created_at DESC LIMIT 5"
        docs_result = storage._execute_query(docs_query, fetch="all")

        print("📄 Últimos documentos:")
        for doc in docs_result or []:
            print(f"   - ID: {doc['id']}, File: {doc.get('file_name', 'N/A')}, Created: {doc.get('created_at', 'N/A')}")

        # Teste 3: Tentar salvar um documento de teste
        test_doc = {
            'file_name': 'debug_test.pdf',
            'document_type': 'NFe',
            'document_number': 'DEBUG123',
            'issuer_cnpj': '12345678000199',
            'extracted_data': {'total': '1000.00'},
            'validation_status': 'validated'
        }

        print("💾 Tentando salvar documento de teste...")
        saved_doc = storage.save_fiscal_document(test_doc)

        if saved_doc and 'id' in saved_doc:
            test_id = saved_doc['id']
            print(f"✅ Documento salvo com ID: {test_id}")

            # Teste 4: Tentar recuperar o documento imediatamente
            print("🔍 Tentando recuperar documento...")
            retrieved_doc = storage.get_fiscal_document(test_id)

            if retrieved_doc:
                print("✅ Documento recuperado com sucesso!"                print(f"   ID: {retrieved_doc['id']}")
                print(f"   File: {retrieved_doc.get('file_name', 'N/A')}")
                return True
            else:
                print("❌ Documento NÃO encontrado após salvar")

                # Teste 5: Verificar se existe no banco diretamente
                direct_query = "SELECT id FROM fiscal_documents WHERE id = %s"
                direct_result = storage._execute_query(direct_query, (test_id,), "one")

                if direct_result:
                    print("✅ Documento existe no banco (query direta)")
                else:
                    print("❌ Documento NÃO existe no banco (query direta)")

                return False
        else:
            print("❌ Falha ao salvar documento")
            return False

    except Exception as e:
        print(f"❌ Erro no debug: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("🚀 DEBUG DO PROBLEMA DE DOCUMENTO NÃO ENCONTRADO")
    print("=" * 60)

    if debug_document_issue():
        print("\n✅ Debug concluído com sucesso!")
    else:
        print("\n❌ Debug revelou problemas!")

if __name__ == "__main__":
    main()
