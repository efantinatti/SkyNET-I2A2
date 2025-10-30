"""
Exemplo de uso do FiscalValidatorAgent com configuração do config.py
"""
import asyncio
import logging
from pathlib import Path
import sys

# Adiciona o diretório raiz ao path para importar os módulos
sys.path.append(str(Path(__file__).parent.parent))

from config import FISCAL_VALIDATOR_CONFIG, GOOGLE_API_KEY
from backend.agents.fiscal_validator_agent import create_fiscal_validator

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def main():
    # Cria uma instância do validador fiscal usando as configurações do config.py
    validator = create_fiscal_validator(
        api_key=GOOGLE_API_KEY,  # Usando a chave da API do Google
        cache_enabled=FISCAL_VALIDATOR_CONFIG['cache_enabled'],
        cache_dir=FISCAL_VALIDATOR_CONFIG['cache_dir']
    )
    
    if not validator:
        logger.error("Falha ao criar o validador fiscal. Verifique as configurações.")
        return
    
    # Exemplo de dados fiscais para validação
    fiscal_data = {
        'cfop': '5102',
        'cst_icms': '00',
        'ncm': '22030010',
        'cst_pis': '01',
        'cst_cofins': '01'
    }
    
    logger.info("Validando dados fiscais...")
    logger.info(f"Dados de entrada: {fiscal_data}")
    
    try:
        # Valida os dados fiscais
        result = await validator.validate_document(fiscal_data)
        
        # Exibe o resultado
        if result.get('status') == 'success':
            logger.info("Validação realizada com sucesso!")
            for field, validation in result.get('validation', {}).items():
                logger.info(f"\n{field.upper()}:")
                logger.info(f"  Válido: {validation.get('is_valid', False)}")
                logger.info(f"  Código: {validation.get('normalized_code', 'N/A')}")
                logger.info(f"  Descrição: {validation.get('description', 'N/A')}")
                logger.info(f"  Confiança: {validation.get('confidence', 0):.2f}")
        else:
            logger.error(f"Erro na validação: {result.get('message', 'Erro desconhecido')}")
            
    except Exception as e:
        logger.error(f"Erro durante a validação: {e}", exc_info=True)

if __name__ == "__main__":
    asyncio.run(main())
