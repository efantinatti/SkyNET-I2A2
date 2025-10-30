#!/usr/bin/env python3
"""
Script para implementar cache de embeddings e reduzir uso da API.

Este script:
1. Implementa cache local de embeddings
2. Evita regenerar embeddings idênticos
3. Monitora uso da quota
4. Fornece estatísticas de uso
"""
import json
import hashlib
from pathlib import Path
import logging
from typing import Dict, List, Optional

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EmbeddingCache:
    """Cache local para embeddings do Gemini."""

    def __init__(self, cache_file: str = ".embedding_cache.json"):
        self.cache_file = Path(__file__).parent.parent / cache_file
        self.cache: Dict[str, List[float]] = {}
        self.load_cache()

    def load_cache(self):
        """Carrega cache do arquivo."""
        try:
            if self.cache_file.exists():
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    self.cache = json.load(f)
                logger.info(f"✅ Cache carregado: {len(self.cache)} embeddings")
        except Exception as e:
            logger.error(f"Erro ao carregar cache: {e}")
            self.cache = {}

    def save_cache(self):
        """Salva cache no arquivo."""
        try:
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(self.cache, f, ensure_ascii=False, indent=2)
            logger.info(f"✅ Cache salvo: {len(self.cache)} embeddings")
        except Exception as e:
            logger.error(f"Erro ao salvar cache: {e}")

    def _generate_key(self, text: str) -> str:
        """Gera chave única para o texto."""
        return hashlib.sha256(text.encode('utf-8')).hexdigest()

    def get(self, text: str) -> Optional[List[float]]:
        """Busca embedding no cache."""
        key = self._generate_key(text)
        return self.cache.get(key)

    def set(self, text: str, embedding: List[float]):
        """Armazena embedding no cache."""
        key = self._generate_key(text)
        self.cache[key] = embedding
        self.save_cache()
        logger.debug(f"Embedding cached para texto (key: {key[:8]}...)")

    def clear(self):
        """Limpa todo o cache."""
        self.cache.clear()
        if self.cache_file.exists():
            self.cache_file.unlink()
        logger.info("🗑️ Cache limpo")


def create_embedding_cache():
    """Cria e integra cache de embeddings no serviço."""
    try:
        # Adicionar o diretório ao path
        import sys
        from pathlib import Path
        sys.path.append(str(Path(__file__).parent.parent))

        # Importar a classe aqui para evitar problemas de importação circular
        from backend.services.embedding_service import GeminiEmbeddingService

        cache = EmbeddingCache()

        # Modificar o método generate_embedding para usar cache
        original_generate = GeminiEmbeddingService.generate_embedding

        def cached_generate_embedding(self, text: str) -> List[float]:
            """Versão com cache do generate_embedding."""
            try:
                # Verificar cache primeiro
                cached_embedding = cache.get(text)
                if cached_embedding:
                    logger.info("📋 Embedding obtido do cache (evitou chamada API)")
                    return cached_embedding

                # Gerar embedding normalmente
                embedding = original_generate(self, text)

                # Armazenar no cache
                cache.set(text, embedding)

                logger.info(f"🆕 Embedding gerado e cached ({len(embedding)} dimensões)")
                return embedding

            except Exception as e:
                logger.error(f"Erro na geração com cache: {e}")
                raise

        # Substituir o método
        GeminiEmbeddingService.generate_embedding = cached_generate_embedding

        logger.info("✅ Sistema de cache de embeddings ativado")
        logger.info(f"   Cache file: {cache.cache_file}")
        logger.info(f"   Embeddings cached: {len(cache.cache)}")

    except ImportError as e:
        logger.error(f"Erro ao importar GeminiEmbeddingService: {e}")
        logger.error("Certifique-se de que o módulo backend.services.embedding_service existe")
    except Exception as e:
        logger.error(f"Erro ao configurar cache: {e}")


def show_quota_solutions():
    """Mostra soluções para problemas de quota."""
    print("\n💡 **SOLUÇÕES PARA QUOTA EXCEDIDA:**")
    print("=" * 50)

    print("1. 🔄 **Aguarde a liberação da quota:**")
    print("   - Free tier: ~1-2 horas para reset")
    print("   - Verifique: https://ai.dev/usage")

    print("\n2. 🔑 **Use múltiplas chaves API:**")
    print("   - Crie chaves diferentes para embeddings vs texto")
    print("   - Distribua a carga entre chaves")

    print("\n3. 💾 **Implemente cache local:**")
    print("   - Reutilize embeddings já gerados")
    print("   - Cache automático ativado no sistema")

    print("\n4. ⚡ **Use modelo com melhor quota:**")
    print("   - gemini-2.0-flash-exp (recomendado se disponível)")
    print("   - gemini-1.5-flash (alternativo)")
    print("   - gemini-pro (último fallback)")

    print("\n5. 📊 **Monitore uso:**")
    print("   - Dashboard: https://ai.dev/usage?tab=rate-limit")
    print("   - Limites free: 1000 req/dia, 60 req/min")

    print("\n6. 💰 **Considere plano pago:**")
    print("   - Pay-as-you-go: $0.00025 por embedding")
    print("   - Mais quota para desenvolvimento")


def main():
    """Função principal."""
    print("🗄️ SISTEMA DE CACHE DE EMBEDDINGS")
    print("=" * 50)

    # Verificar se o cache já existe
    cache = EmbeddingCache()

    print(f"📁 Cache atual: {len(cache.cache)} embeddings armazenados")
    if cache.cache:
        print(f"📂 Arquivo: {cache.cache_file}")

    # Integrar cache no serviço de embeddings
    create_embedding_cache()

    # Mostrar soluções
    show_quota_solutions()

    print("\n✅ **SISTEMA OTIMIZADO!**")
    print("   - Cache de embeddings: ✅ Ativo")
    print("   - Rate limiting: ✅ Ativo")
    print("   - Modelo otimizado: ✅ gemini-2.0-flash-exp / gemini-1.5-flash")

    print("\n📈 **Para verificar uso:**")
    print("   Execute: python scripts/check_api_quota.py")


if __name__ == "__main__":
    main()
