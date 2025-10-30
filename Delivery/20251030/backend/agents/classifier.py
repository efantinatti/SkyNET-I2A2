import logging
from ..tools import fiscal_validator
from typing import Dict, Any, Union, List, Tuple


def classify_document(parsed: Dict[str, Any]) -> Dict[str, Any]:
    """Classify a fiscal document based on its parsed data."""
    if not isinstance(parsed, dict):
        return {
            'tipo': 'unknown',
            'setor': 'unknown',
            'perfil_emitente': 'unknown',
            'validacao': {
                'status': 'error',
                'issues': ['Documento inválido'],
                'calculated_sum': 0.0
            }
        }

    # Inicializa o tipo como 'unknown' por padrão
    tipo = 'unknown'
    
    try:
        # Tenta identificar o tipo de documento
        doc_type = (str(parsed.get('tipo_documento', '')).strip() or '').upper()
        
        # Se for MDF-e ou CT-e, define o tipo diretamente
        if doc_type in ['MDF', 'MDFE']:
            tipo = 'mdfe'
        elif doc_type == 'CTE':
            tipo = 'cte'
        else:
            # Para outros tipos, tenta obter o CFOP
            cfop = None
            
            # Primeiro tenta obter o CFOP diretamente do documento
            cfop = parsed.get('cfop')
            
            # Se não encontrou, tenta obter do primeiro item
            if not cfop:
                itens = parsed.get('itens', [])
                # Verifica se itens é uma lista e não está vazia
                if isinstance(itens, (list, tuple)) and itens and isinstance(itens[0], dict):
                    cfop = itens[0].get('cfop')
            
            if cfop:
                tipo = fiscal_validator.cfop_type(cfop)
    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.warning(f'Erro ao classificar documento: {str(e)}')
        # Mantém o valor padrão 'unknown' em caso de erro

    # Simple issuer profile: if issuer has cnpj and company-like name -> fornecedor
    emit = parsed.get('emitente') or {}
    cnpj = emit.get('cnpj')
    perfil = 'fornecedor' if cnpj else 'cliente'

    # Sector rules (very naive)
    setor = 'servicos'
    total = parsed.get('total', 0.0)
    
    # Ensure total is a float for comparison
    try:
        total_float = float(total) if total is not None else 0.0
    except (ValueError, TypeError):
        total_float = 0.0
    
    if total_float > 10000.0:
        setor = 'industria'
    elif total_float > 0.0:
        setor = 'comercio'

    validation = fiscal_validator.validate_document(parsed)

    return {
        'tipo': tipo,
        'setor': setor,
        'perfil_emitente': perfil,
        'validacao': validation
    }
