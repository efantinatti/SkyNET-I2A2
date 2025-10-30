"""Tesseract OCR helper and PDF->image conversion using pdf2image.

Includes OCR-to-structure mappers:
1. Simple heuristic mapper for MVP (regex-based field extraction)
2. Optional LLM-assisted mapper using Google's generative model
"""
from typing import List, Dict, Any, Optional
import pytesseract
from pdf2image import convert_from_path
from pdf2image.exceptions import PDFInfoNotInstalledError
from pypdf import PdfReader
from PIL import Image
import os
import re
import logging
import shutil
from typing import Optional, List, Union, Tuple
from pathlib import Path
from config import TESSERACT_PATH

# Configure Tesseract path and TESSDATA_PREFIX
try:
    # Get TESSDATA_PREFIX from environment or use default
    TESSDATA_PREFIX = os.getenv('TESSDATA_PREFIX', '')
    
    # Set TESSDATA_PREFIX as environment variable if not already set
    if TESSDATA_PREFIX and 'TESSDATA_PREFIX' not in os.environ:
        os.environ['TESSDATA_PREFIX'] = TESSDATA_PREFIX
    
    # Try to use the configured path
    if TESSERACT_PATH:
        pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH
        
    # If Tesseract is in the system PATH, we don't need to set the path
    elif not shutil.which('tesseract'):
        # Last resort: try common paths
        common_paths = [
            'C:\\Program Files\\Tesseract-OCR\\tesseract.exe',
            'C:\\Program Files (x86)\\Tesseract-OCR\\tesseract.exe',
            '/usr/bin/tesseract',
            '/usr/local/bin/tesseract',
            '/app/.apt/usr/bin/tesseract',
            '/home/appuser/streamlit-app/tesseract/tesseract',
            '/usr/bin/tesseract-ocr',
            '/usr/local/bin/tesseract-ocr'
        ]
        for path in common_paths:
            if os.path.isfile(path) and os.access(path, os.X_OK):
                pytesseract.pytesseract.tesseract_cmd = path
                break
except Exception as e:
    logging.warning(f"Could not configure Tesseract path: {e}. Will try to use 'tesseract' from PATH.")
    # Fall back to 'tesseract' command in PATH
    pytesseract.pytesseract.tesseract_cmd = 'tesseract'

try:
    from .llm_ocr_mapper import LLMOCRMapper
    _llm_mapper = None
except ImportError:
    _llm_mapper = None


def preprocess_image(image: Image.Image) -> Image.Image:
    """Pré-processa a imagem para melhorar resultados do OCR"""
    # Converte para escala de cinza
    if image.mode != 'L':
        image = image.convert('L')
    
    # Aumenta o contraste
    from PIL import ImageEnhance
    enhancer = ImageEnhance.Contrast(image)
    image = enhancer.enhance(2.0)
    
    # Redimensiona se a imagem for muito pequena
    if image.size[0] < 1000 or image.size[1] < 1000:
        ratio = 1000.0 / min(image.size)
        new_size = tuple(int(dim * ratio) for dim in image.size)
        image = image.resize(new_size, Image.Resampling.LANCZOS)
    
    return image

def image_to_text(image: Image.Image, lang: str = 'por') -> str:
    # Aplica pré-processamento
    processed_img = preprocess_image(image)
    
    # Configura o OCR para melhor precisão
    custom_config = r'--oem 3 --psm 3 -c preserve_interword_spaces=1'
    
    try:
        # Executa OCR com configurações otimizadas
        result = pytesseract.image_to_string(
            processed_img,
            lang=lang,
            config=custom_config
        )
        return result
    except pytesseract.TesseractNotFoundError as e:
        # Tesseract não está instalado
        raise Exception(f"Tesseract OCR não está instalado ou não foi encontrado no PATH: {str(e)}")
    except Exception as e:
        # Se falhar com português, tenta com inglês
        error_str = str(e).lower()
        if 'por' in error_str or 'language' in error_str or 'tessdata' in error_str:
            logging.warning(f"Falha ao usar language pack português: {str(e)}. Tentando com inglês...")
            try:
                result = pytesseract.image_to_string(
                    processed_img,
                    lang='eng',
                    config=custom_config
                )
                return result
            except Exception as e2:
                raise Exception(f"Erro ao executar OCR (português e inglês falharam): {str(e2)}")
        else:
            raise Exception(f"Erro ao executar OCR: {str(e)}")


def pdf_to_images(pdf_path: str, dpi: int = 300) -> List[Image.Image]:
    # pdf2image requires poppler on PATH in Windows; user must install poppler
    try:
        images = convert_from_path(pdf_path, dpi=dpi)
        return images
    except (PDFInfoNotInstalledError, FileNotFoundError, OSError):
        # Poppler not installed or executable not found: return empty list to let caller fallback
        return []
    except Exception:
        # Any other error: return empty list and let caller decide
        return []


def pdf_to_text(pdf_path: str, lang: str = 'por') -> str:
    imgs = pdf_to_images(pdf_path)
    if imgs:
        texts = [image_to_text(img, lang=lang) for img in imgs]
        return "\n".join(texts)

    # Fallback: try to extract text using pypdf (works if PDF contains selectable text)
    try:
        reader = PdfReader(pdf_path)
        pages_text = []
        for page in reader.pages:
            text = page.extract_text() or ""
            pages_text.append(text)
        return "\n\n".join(pages_text)
    except Exception:
        # final fallback: empty string
        return ''


def ocr_text_to_document(text: str, use_llm: bool = False) -> Dict[str, Any]:
    """Map OCR text to document structure using heuristics or LLM.
    
    Args:
        text: The OCR text to parse
        use_llm: If True, attempts to use LLM mapper first;
                falls back to heuristics if LLM fails or is not available
    
    Returns:
        Dict with extracted fields (numero, emitente, destinatario, etc.)
        Always returns a dictionary with at least 'tipo_documento' and 'raw_text' keys
    """
    # Inicializa um documento vazio com valores padrão
    doc: Dict[str, Any] = {
        'tipo_documento': 'MDF',  # Assume MDF por padrão para documentos não identificados
        'raw_text': text,
        'emitente': {},
        'destinatario': {},
        'itens': [],  # MDF-e geralmente não tem itens
        'impostos': {},
        'total': None,
        'chave_acesso': None,
        'data_emissao': None,
        'numero': None
    }
    
    # Se não houver texto, retorna o documento vazio
    if not text or not text.strip():
        return doc
        
    # Tenta identificar o tipo de documento
    text_upper = text.upper()
    if 'MDF' in text_upper or 'MANIFESTO' in text_upper:
        doc['tipo_documento'] = 'MDF'
    elif 'CTE' in text_upper or 'CONHECIMENTO' in text_upper:
        doc['tipo_documento'] = 'CTE'
    elif 'NFS' in text_upper or 'NOTA FISCAL' in text_upper:
        doc['tipo_documento'] = 'NFE'
    
    # Se for MDF ou CTE, não tenta extrair itens
    if doc['tipo_documento'] in ['MDF', 'CTE']:
        return doc
        
    # Para outros tipos de documento, tenta extrair informações estruturadas
    try:
        # Try LLM first if requested
        if use_llm:
            global _llm_mapper
            try:
                if _llm_mapper is None:
                    _llm_mapper = LLMOCRMapper()
                return {**doc, **_llm_mapper.map_ocr_text(text)}  # Mescla com os valores padrão
            except Exception as e:
                print(f"LLM mapping failed, falling back to heuristics: {e}")
                # fall through to heuristics
        
        # Se chegou aqui, usa heurísticas para extrair informações
        lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
        
        # Expressões regulares para extração de dados
        cnpj_re = re.compile(r"(\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}|\d{14})")
        cpf_re = re.compile(r"(\d{3}\.\d{3}\.\d{3}-\d{2}|\d{11})")
        money_re = re.compile(r"([\d.,]+)\s*$")
        date_re = re.compile(r"(\d{2}/\d{2}/\d{4})")
        # Match variants: N°, Nº, No, N, Nº:, Numero, num
        num_re = re.compile(r"(?:\bN(?:\s|\s*[º°º\.]\s*)?|no|nº|n°|numero|num)\s*[:\-\.]?\s*(\d{1,10})", re.IGNORECASE)
        
        for ln in lines:
            # CNPJ
            m = cnpj_re.search(ln)
            if m and not doc['emitente'].get('cnpj'):
                doc['emitente']['cnpj'] = re.sub(r"\D", "", m.group(1))
                continue

            # CPF fallback for destinatario
            m = cpf_re.search(ln)
            if m and not doc['destinatario'].get('cnpj_cpf'):
                doc['destinatario']['cnpj_cpf'] = re.sub(r"\D", "", m.group(1))
                continue

            # document number
            m = num_re.search(ln)
            if m and not doc.get('numero'):
                doc['numero'] = m.group(1)
                continue
                
            # fallback: line that is 'N 123' or '234' following 'N°' was not captured
            if not doc.get('numero') and ln.strip().isdigit() and len(ln.strip()) <= 10:
                # small heuristic: if line is all digits and not an item total, treat as número
                doc['numero'] = ln.strip()
                continue

            # date
            m = date_re.search(ln)
            if m and not doc.get('data_emissao'):
                doc['data_emissao'] = m.group(1)
                continue

            # totals (look for 'TOTAL' or 'Valor Total')
            if 'total' in ln.lower() or 'valor' in ln.lower():
                m = money_re.search(ln)
                if m:
                    candidate = m.group(1).replace('.', '').replace(',', '.')
                    try:
                        doc['total'] = float(candidate)
                    except Exception:
                        pass
                    continue

            # item-like line heuristic: description qty unit_value total
            # e.g. '1x Parafuso 2,00 4,00' or 'Parafuso 2 2,00 4,00'
            parts = ln.split()
            if len(parts) >= 3:
                m = money_re.search(parts[-1])
                m2 = money_re.search(parts[-2]) if len(parts) > 1 else None
                if m and m2:
                    # assume last is total, second-last is unit or qty
                    descricao = ' '.join(parts[:-2])
                    try:
                        valor_total = float(parts[-1].replace('.', '').replace(',', '.'))
                    except Exception:
                        valor_total = None
                    try:
                        quantidade = float(parts[-2].replace(',', '.'))
                    except Exception:
                        quantidade = None
                    doc['itens'].append({
                        'descricao': descricao, 
                        'quantidade': quantidade, 
                        'valor_unitario': None, 
                        'valor_total': valor_total
                    })
        
        return doc
        
    except Exception as e:
        print(f"Error processing OCR text: {e}")
        # Retorna o documento com as informações básicas mesmo em caso de erro
        return doc

    # Código removido para evitar duplicação - já processado no bloco try acima
    pass
