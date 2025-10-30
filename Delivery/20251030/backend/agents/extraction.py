from ..tools import xml_parser, ocr_processor
from ..models.document import FiscalDocument, Emitente, Destinatario, Item, Impostos
from typing import Dict, Any
import os


def extract_from_file(path: str) -> Dict[str, Any]:
    _, ext = os.path.splitext(path.lower())
    if ext == '.xml':
        parsed = xml_parser.parse_xml_file(path)
        # Ensure consistent structure with raw_text
        if isinstance(parsed, dict):
            raw_text = parsed.get('raw_text', '')
            if isinstance(raw_text, str):
                detected_type = parsed.get('tipo_documento') or parsed.get('document_type')
                if isinstance(detected_type, str):
                    parsed['document_type'] = detected_type
                else:
                    parsed['document_type'] = 'unknown'
                return parsed
        # Return error structure if parsing failed
        return {'error': 'xml_parse_error', 'message': 'Failed to parse XML', 'raw_text': '', 'document_type': 'unknown'}
    elif ext in ['.pdf']:
        try:
            text = ocr_processor.pdf_to_text(path)
            if not text:
                return {'error': 'empty_ocr', 'message': 'PDF could not be converted to images (Poppler missing) and no selectable text found.'}
            return {'raw_text': text, 'document_type': 'unknown'}
        except Exception as e:
            return {'error': 'ocr_failed', 'message': str(e)}
    else:
        # try to read as image
        try:
            from PIL import Image
            img = Image.open(path)
            text = ocr_processor.image_to_text(img)
            if not text or not text.strip():
                return {'error': 'empty_ocr', 'message': 'Nenhum texto foi extraído da imagem. Verifique se a imagem contém texto legível.'}
            return {'raw_text': text, 'document_type': 'unknown'}
        except FileNotFoundError:
            return {'error': 'file_not_found', 'message': f'Arquivo não encontrado: {path}'}
        except Exception as e:
            error_str = str(e).lower()
            
            # Detecta erros específicos do Tesseract
            if 'tesseract' in error_str and ('not installed' in error_str or 'not in your path' in error_str):
                return {
                    'error': 'tesseract_not_installed',
                    'message': 'Tesseract OCR não está instalado ou não foi encontrado no PATH. Por favor, instale o Tesseract-OCR para processar imagens.'
                }
            
            # Detecta erros de tipo de arquivo
            if 'cannot identify image file' in error_str or 'unrecognized image format' in error_str:
                return {
                    'error': 'invalid_image_format',
                    'message': f'Formato de imagem não reconhecido. Suportados: JPG, PNG, BMP, TIFF.'
                }
            
            # Erro genérico
            return {
                'error': 'unsupported_file_type',
                'message': f'Tipo de arquivo não suportado ou erro ao processar: {str(e)}'
            }
