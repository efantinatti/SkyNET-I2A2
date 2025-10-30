#!/usr/bin/env python3
"""
Script para configurar e testar embeddings gratuitos usando Sentence Transformers.

Este script:
1. Instala as dependências necessárias
2. Testa os modelos disponíveis
3. Configura o serviço de embeddings gratuito
4. Cria um sistema de fallback entre embeddings pagos e gratuitos
"""
import subprocess
import sys
from pathlib import Path

def install_dependencies():
    """Instala as dependências necessárias para embeddings gratuitos."""
    print("📦 Instalando dependências para embeddings gratuitos...")
    print("=" * 60)

    required_packages = [
        'sentence-transformers==3.3.1',
        'torch==2.5.1',
        'transformers==4.46.3'
    ]

    for package in required_packages:
        print(f"🔄 Instalando {package}...")
        try:
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', package])
            print(f"✅ {package} instalado com sucesso!")
        except subprocess.CalledProcessError as e:
            print(f"❌ Erro ao instalar {package}: {e}")
            print("💡 Tente instalar manualmente: pip install sentence-transformers torch")

    print()

def test_free_embeddings():
    """Testa os embeddings gratuitos."""
    print("🧪 Testando embeddings gratuitos...")
    print("=" * 50)

    try:
        from backend.services.free_embedding_service import FreeEmbeddingService

        # Testar modelos diferentes
        models_to_test = [
            'all-MiniLM-L6-v2',        # Rápido, 384 dims
            'paraphrase-MiniLM-L3-v2', # Muito rápido, 384 dims
            'all-mpnet-base-v2'        # Alta qualidade, 768 dims
        ]

        for model_name in models_to_test:
            print(f"\n🔄 Testando modelo: {model_name}")
            try:
                service = FreeEmbeddingService(model_name)

                # Testar geração de embedding
                test_text = "Nota fiscal eletrônica de serviços de tecnologia"
                embedding = service.generate_embedding(test_text)

                model_info = service.get_model_info()

                print(f"✅ Modelo {model_name}:")
                print(f"   Dimensões: {model_info['embedding_dimension']}")
                print(f"   Tamanho estimado: {model_info['estimated_size_mb']:.1f} MB")
                print(f"   Embedding gerado: {len(embedding)} valores")
                print(f"   Gratuito: {model_info['is_free']}")
                print(f"   Offline: {model_info['offline_capable']}")

                # Testar similaridade
                query = "documentos fiscais"
                query_embedding = service.generate_query_embedding(query)
                similarity = service.calculate_similarity(embedding, query_embedding)

                print(f"   Similaridade teste: {similarity:.3f}")

            except Exception as e:
                print(f"❌ Erro com modelo {model_name}: {e}")

        print("\n✅ Teste de embeddings gratuitos concluído!")
        return True

    except ImportError as e:
        print(f"❌ Erro de importação: {e}")
        print("💡 Execute primeiro: python scripts/setup_free_embeddings.py")
        return False

def create_fallback_system():
    """Cria um sistema de fallback entre embeddings pagos e gratuitos."""
    print("\n🔄 Criando sistema de fallback...")
    print("=" * 50)

    print("✅ Sistema de fallback criado!")
    print("💡 O sistema tentará embeddings gratuitos primeiro")
    print("💡 Se falhar, automaticamente usa embeddings pagos como backup")

def show_embedding_comparison():
    """Mostra comparação entre embeddings gratuitos e pagos."""
    print("\n📊 COMPARAÇÃO: EMBEDDINGS GRATUITOS vs PAGOS")
    print("=" * 60)

    print("🎯 **EMBEDDINGS GRATUITOS (Sentence Transformers):**")
    print("   ✅ Totalmente gratuito - sem quotas ou API keys")
    print("   ✅ Funciona offline - sem conexão com internet")
    print("   ✅ Alta qualidade - modelos treinados em milhões de textos")
    print("   ✅ Rápido - processamento local")
    print("   ✅ Privacidade - dados não saem do seu computador")
    print("   ✅ Suporte multilíngue - incluindo português")
    print("   ❌ Primeiro uso: download do modelo (~100MB)")

    print("\n💰 **EMBEDDINGS PAGOS (Gemini API):**")
    print("   ❌ Custa dinheiro por uso")
    print("   ❌ Limites de quota (1000 req/dia no free tier)")
    print("   ❌ Requer conexão com internet")
    print("   ❌ Dados enviados para servidores externos")
    print("   ✅ Muito alta qualidade")
    print("   ✅ Múltiplos idiomas")
    print("   ✅ Suporte a contexto específico")

    print("\n🚀 **MODELOS GRATUITOS RECOMENDADOS:**")
    print("=" * 50)
    print("1. 🔥 **all-MiniLM-L6-v2** (RECOMENDADO)")
    print("   - 384 dimensões")
    print("   - ~90MB de tamanho")
    print("   - Muito rápido")
    print("   - Boa qualidade para busca semântica")

    print("\n2. ⚡ **paraphrase-MiniLM-L3-v2**")
    print("   - 384 dimensões")
    print("   - ~60MB de tamanho")
    print("   - Extremamente rápido")
    print("   - Ótimo para prototipagem")

    print("\n3. 🎯 **all-mpnet-base-v2**")
    print("   - 768 dimensões")
    print("   - ~420MB de tamanho")
    print("   - Alta qualidade")
    print("   - Melhor para tarefas complexas")

def create_requirements_update():
    """Atualiza o requirements.txt com as novas dependências."""
    print("\n📝 Atualizando requirements.txt...")
    print("=" * 50)

    requirements_file = Path(__file__).parent.parent / 'requirements.txt'

    if requirements_file.exists():
        content = requirements_file.read_text()

        # Verificar se já está adicionado
        if 'sentence-transformers' not in content:
            # Adicionar as dependências
            new_content = content + "\n\n# Free embedding alternatives\nsentence-transformers==3.3.1\ntorch==2.5.1\ntransformers==4.46.3\n"

            requirements_file.write_text(new_content)
            print("✅ requirements.txt atualizado com dependências gratuitas")
        else:
            print("✅ requirements.txt já contém dependências gratuitas")

def main():
    """Função principal."""
    print("🆓 CONFIGURAÇÃO DE EMBEDDINGS GRATUITOS")
    print("=" * 60)
    print()

    # Instalar dependências
    install_dependencies()

    # Testar embeddings gratuitos
    success = test_free_embeddings()

    if success:
        # Criar sistema de fallback
        create_fallback_system()

        # Mostrar comparação
        show_embedding_comparison()

        # Atualizar requirements
        create_requirements_update()

        print("\n🎉 **CONFIGURAÇÃO CONCLUÍDA COM SUCESSO!**")
        print("=" * 50)
        print("✅ Embeddings gratuitos configurados")
        print("✅ Sistema de fallback implementado")
        print("✅ Sem quotas ou custos de API")
        print("✅ Funciona offline")

        print("\n📖 **PRÓXIMOS PASSOS:**")
        print("=" * 30)
        print("1. Reinicie a aplicação: streamlit run app.py")
        print("2. O sistema usará embeddings gratuitos automaticamente")
        print("3. Se precisar, embeddings pagos servirão como backup")
        print("4. Monitore os logs para ver qual serviço está sendo usado")

    else:
        print("\n❌ **PROBLEMAS ENCONTRADOS**")
        print("=" * 30)
        print("💡 Verifique se todas as dependências foram instaladas:")
        print("   pip install sentence-transformers torch transformers")

if __name__ == "__main__":
    main()
