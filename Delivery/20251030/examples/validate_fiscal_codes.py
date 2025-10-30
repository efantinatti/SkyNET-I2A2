"""
Exemplo de uso do FiscalValidatorAgent para validação de códigos fiscais.

Este script demonstra como usar o FiscalValidatorAgent para validar códigos fiscais
de um documento, incluindo CFOP, CST ICMS, CST PIS/COFINS e NCM.
"""
import asyncio
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Adiciona o diretório raiz ao path para importar os módulos
sys.path.append(str(Path(__file__).parent.parent))

# Carrega as variáveis de ambiente
load_dotenv()

# Dados de exemplo de um documento fiscal
SAMPLE_DOCUMENT = {
    "document": {
        "cfop": "5102",
        "cst_icms": "00",
        "cst_pis": "01",
        "cst_cofins": "01"
    },
    "items": [
        {
            "ncm": "22030010",
            "description": "Cerveja de malte",
            "quantity": 12,
            "unit_price": 4.99
        }
    ]
}

async def main():
    """Função principal que demonstra o uso do FiscalValidatorAgent."""
    from backend.agents.fiscal_validator_agent import create_fiscal_validator
    from backend.agents.document_agent import DocumentAgent
    
    print("=== Validação de Códigos Fiscais com LLM ===\n")
    
    # Cria uma instância do DocumentAgent (que já inclui o FiscalValidatorAgent)
    document_agent = DocumentAgent()
    
    # Verifica se o validador fiscal está disponível
    if not hasattr(document_agent, 'fiscal_validator') or not document_agent.fiscal_validator:
        print("Erro: Validador fiscal não está disponível. Verifique se a chave da API do Google AI está configurada.")
        return
    
    # Extrai os dados fiscais do documento de exemplo
    fiscal_data = {}
    
    # Dados do documento principal
    doc_data = SAMPLE_DOCUMENT.get('document', {})
    fiscal_data.update({
        'cfop': doc_data.get('cfop', ''),
        'cst_icms': doc_data.get('cst_icms', ''),
        'cst_pis': doc_data.get('cst_pis', ''),
        'cst_cofins': doc_data.get('cst_cofins', '')
    })
    
    # NCM do primeiro item (se existir)
    items = SAMPLE_DOCUMENT.get('items', [])
    if items and 'ncm' in items[0]:
        fiscal_data['ncm'] = items[0]['ncm']
    
    print("Dados fiscais para validação:")
    for key, value in fiscal_data.items():
        print(f"- {key.upper()}: {value}")
    
    print("\nValidando códigos com o LLM...\n")
    
    try:
        # Valida os códigos fiscais
        validation_result = await document_agent._validate_fiscal_codes(fiscal_data)
        
        # Exibe os resultados
        if validation_result.get('status') == 'success':
            print("✅ Validação concluída com sucesso!\n")
            
            validations = validation_result.get('validations', {})
            for code_type, validation in validations.items():
                status = "✅ VÁLIDO" if validation.get('is_valid') else "❌ INVÁLIDO"
                print(f"{code_type.upper()}: {status}")
                print(f"  Código: {validation.get('normalized_code')}")
                print(f"  Descrição: {validation.get('description')}")
                print(f"  Confiança: {validation.get('confidence')*100:.1f}%")
                print()
        else:
            print(f"❌ Erro na validação: {validation_result.get('message')}")
            
    except Exception as e:
        print(f"❌ Erro ao validar códigos fiscais: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main())
