"""
Exemplo de uso do FiscalDocumentProcessor para processar documentos fiscais.

Este script demonstra como usar a classe FiscalDocumentProcessor para extrair texto e dados estruturados
de documentos fiscais em diferentes formatos (PDF, imagens, etc.).

Uso:
    python -m examples.process_document <caminho_do_arquivo> [--output <arquivo_saida.json>]

Exemplo:
    python -m examples.process_document documentos/nota_fiscal.pdf --output resultado.json
"""
import os
import sys
import json
import argparse
from pathlib import Path

# Adiciona o diretório raiz ao path para importar os módulos
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.tools.fiscal_document_processor import FiscalDocumentProcessor

def main():
    # Configura o parser de argumentos
    parser = argparse.ArgumentParser(description='Processa documentos fiscais e extrai dados estruturados.')
    parser.add_argument('file_path', help='Caminho para o arquivo do documento fiscal')
    parser.add_argument('--output', '-o', help='Arquivo de saída para salvar os resultados (opcional)')
    
    # Parseia os argumentos
    args = parser.parse_args()
    
    # Verifica se o arquivo existe
    file_path = Path(args.file_path)
    if not file_path.exists():
        print(f"Erro: Arquivo não encontrado: {file_path}")
        return 1
    
    try:
        # Cria o processador de documentos
        print(f"Processando documento: {file_path}")
        processor = FiscalDocumentProcessor()
        
        # Processa o documento
        result = processor.process_document(file_path)
        
        # Exibe os resultados
        print("\n=== Resultado do Processamento ===")
        print(f"Sucesso: {result.get('success', False)}")
        
        if not result.get('success'):
            print(f"Erro: {result.get('error', 'Erro desconhecido')}")
            return 1
        
        print(f"\nTipo de documento: {result.get('document_type', 'desconhecido').upper()}")
        
        # Exibe informações básicas
        print("\n=== Informações Básicas ===")
        print(f"Número: {result.get('numero', 'Não informado')}")
        print(f"Data de Emissão: {result.get('data_emissao', 'Não informada')}")
        print(f"Valor Total: R$ {float(result.get('valor_total', '0.00')):.2f}")
        
        # Exibe informações do emitente
        emitente = result.get('emitente', {})
        print("\n=== Emitente ===")
        print(f"Razão Social: {emitente.get('razao_social', 'Não informada')}")
        print(f"CNPJ: {emitente.get('cnpj', 'Não informado')}")
        print(f"Inscrição Estadual: {emitente.get('inscricao_estadual', 'Não informada')}")
        
        # Exibe informações do destinatário
        destinatario = result.get('destinatario', {})
        print("\n=== Destinatário ===")
        print(f"Nome/Razão Social: {destinatario.get('razao_social', 'Não informado')}")
        if 'cnpj' in destinatario:
            print(f"CNPJ: {destinatario['cnpj']}")
        elif 'cpf' in destinatario:
            print(f"CPF: {destinatario['cpf']}")
        else:
            print("CPF/CNPJ: Não informado")
        
        # Exibe os itens
        itens = result.get('itens', [])
        if itens:
            print("\n=== Itens ===")
            print(f"{'Código':<10} {'Descrição':<40} {'Qtd':>8} {'Vl. Unit.':>15} {'Vl. Total':>15}")
            print("-" * 90)
            for item in itens:
                print(f"{item.get('codigo', ''):<10} {item.get('descricao', '')[:35]:<40} "
                      f"{item.get('quantidade', 0):>8.2f} {item.get('valor_unitario', 0):>15.2f} "
                      f"{item.get('valor_total', 0):>15.2f}")
        
        # Exibe os impostos
        impostos = result.get('impostos', {})
        if impostos:
            print("\n=== Impostos ===")
            for imposto, valor in impostos.items():
                print(f"{imposto.upper()}: R$ {valor:.2f}")
        
        # Exibe informações adicionais
        print("\n=== Informações Adicionais ===")
        if 'chave_acesso' in result:
            print(f"Chave de Acesso: {result['chave_acesso']}")
        if 'protocolo_autorizacao' in result:
            print(f"Protocolo de Autorização: {result['protocolo_autorizacao']}")
        
        # Salva o resultado em um arquivo, se solicitado
        if args.output:
            output_path = Path(args.output)
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            print(f"\nResultado salvo em: {output_path.absolute()}")
        
        return 0
    
    except Exception as e:
        print(f"\nErro ao processar o documento: {str(e)}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
