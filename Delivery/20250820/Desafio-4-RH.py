# %%
import pandas as pd
import numpy as np
from typing import Dict, List, Any
import configparser
import os
import requests
import json
from Libs.email_library import send_process_completion_email

# %%
# Carrega configurações do arquivo INI
def load_config():
    config = configparser.ConfigParser()
    config_path = os.path.join(os.path.dirname(__file__), 'Config', 'config.ini')
    
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Arquivo de configuração não encontrado: {config_path}")
    
    config.read(config_path)
    return config

# %%
# Configuração do Gemini
try:
    config = load_config()
    GEMINI_API_KEY = config['gemini']['api_key']
except Exception as e:
    print(f"Erro ao carregar configuração: {e}")
    raise

def call_gemini_api(prompt: str) -> Dict:
    """
    Faz uma chamada direta à API do Gemini
    """
    url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"
    
    headers = {
        'Content-Type': 'application/json',
        'X-goog-api-key': GEMINI_API_KEY
    }
    
    data = {
        "contents": [
            {
                "parts": [
                    {
                        "text": prompt + "\n\nPor favor, responda APENAS com o JSON solicitado, sem texto adicional."
                    }
                ]
            }
        ],
        "generationConfig": {
            "temperature": 0.1,
            "topP": 0.1,
            "topK": 1
        }
    }
    
    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()  # Levanta exceção para erros HTTP
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Erro na chamada da API: {e}")
        return None

def validate_with_llm(data: Dict[str, Any], rules: List[str]) -> Dict[str, Any]:
    """
    Utiliza o Gemini LLM para validar e corrigir dados conforme regras específicas
    """
    prompt = f"""
    Sistema: Você é um validador especializado em dados de RH e folha de pagamento.
    
    Contexto: Analisando dados de benefícios (VR) com as seguintes regras:
    {rules}
    
    Dados recebidos:
    {data}
    
    Por favor, analise e retorne:
    1. Inconsistências encontradas
    2. Correções sugeridas
    3. Validação de regras de negócio
    4. Alertas sobre possíveis problemas
    
    Formato da resposta:
    {{
        "inconsistencias": [],
        "correcoes": [],
        "validacoes": [],
        "alertas": []
    }}
    """
    
    try:
        response = call_gemini_api(prompt)
        if response and 'candidates' in response:
            # Tenta converter a resposta em um dicionário válido
            text_response = response['candidates'][0]['content']['parts'][0]['text']
            
            # Remove possíveis caracteres especiais e formatação
            text_response = text_response.strip()
            if text_response.startswith('```json'):
                text_response = text_response[7:]
            if text_response.endswith('```'):
                text_response = text_response[:-3]
            
            try:
                # Tenta usar json.loads em vez de eval
                result = json.loads(text_response)
                return result
            except json.JSONDecodeError:
                print(f"Erro ao decodificar JSON. Resposta recebida: {text_response}")
                return {
                    "inconsistencias": [],
                    "correcoes": [],
                    "validacoes": [],
                    "alertas": ["Erro ao processar resposta do LLM"]
                }
        else:
            print(f"Resposta inesperada da API: {response}")
            raise ValueError("Resposta da API inválida")
    except Exception as e:
        print(f"Erro na validação LLM: {e}")
        return {
            "inconsistencias": [],
            "correcoes": [],
            "validacoes": [],
            "alertas": [f"Erro na validação LLM: {str(e)}"]
        }


# %%
def executar_automacao_vr():
    """
    Função principal que encapsula todo o processo de automação
    para o cálculo e geração do arquivo de compra de VR.
    """
    try:
        # --- 0. Carregamento de Todos os Arquivos de Dados ---
        # Carrega as bases de dados e o template final.
        print("Iniciando o carregamento dos arquivos...")
        
        # Regras de validação para o LLM
        validation_rules = [
            "Datas devem estar em formato válido (YYYY-MM-DD)",
            "Campos obrigatórios não podem estar vazios",
            "Férias não podem exceder 30 dias",
            "Feriados estaduais e municipais devem ter UF válida",
            "Datas de admissão e demissão devem ser coerentes",
            "Valores monetários devem ser positivos"
        ]

        # Carrega e valida cada DataFrame
        df_ativos = pd.read_excel('Import/ATIVOS.xlsx', sheet_name='ATIVOS')
        validation_result = validate_with_llm(df_ativos.head().to_dict(), validation_rules)
        print("\nValidação df_ativos:", validation_result['alertas'])

        df_dias_uteis = pd.read_excel('Import/Base dias uteis.xlsx', sheet_name='Planilha1')
        validation_result = validate_with_llm(df_dias_uteis.head().to_dict(), [
            "Feriados devem ter data válida",
            "Cada estado deve ter seus feriados específicos",
            "Dias úteis devem ser coerentes com feriados"
        ])
        print("\nValidação df_dias_uteis:", validation_result['alertas'])

        df_sindicato_valor = pd.read_excel('Import/Base sindicato x valor.xlsx', sheet_name='Planilha1')
        df_desligados = pd.read_excel('Import/DESLIGADOS.xlsx', sheet_name='DESLIGADOS ')
        validation_result = validate_with_llm(df_desligados.head().to_dict(), [
            "Datas de demissão devem ser válidas",
            "Status de comunicado deve estar preenchido"
        ])
        print("\nValidação df_desligados:", validation_result['alertas'])

        df_estagio = pd.read_excel('Import/ESTÁGIO.xlsx', sheet_name='Planilha1')
        df_exterior = pd.read_excel('Import/EXTERIOR.xlsx', sheet_name='Planilha1', header=None)
        
        df_ferias = pd.read_excel('Import/FÉRIAS.xlsx', sheet_name='Planilha1')
        validation_result = validate_with_llm(df_ferias.head().to_dict(), [
            "Dias de férias devem estar entre 0 e 30",
            "Períodos de férias não podem se sobrepor",
            "Matrícula deve existir na base de ativos"
        ])
        print("\nValidação df_ferias:", validation_result['alertas'])

        df_admissao_abril = pd.read_excel('Import/ADMISSÃO ABRIL.xlsx', sheet_name='Planilha1')
        validation_result = validate_with_llm(df_admissao_abril.head().to_dict(), [
            "Data de admissão deve ser válida",
            "Não pode haver duplicidade de matrícula"
        ])
        print("\nValidação df_admissao_abril:", validation_result['alertas'])

        df_afastamentos = pd.read_excel('Import/AFASTAMENTOS.xlsx', sheet_name='Planilha1')
        df_aprendiz = pd.read_excel('Import/APRENDIZ.xlsx', sheet_name='Planilha1')
        df_template = pd.read_excel('Import/VR MENSAL 05.2025.xlsx', sheet_name='VR MENSAL 05.2025')

        # Aplicando correções baseadas no Pandas 2.0
        print("\nAplicando correções automáticas...")
        
        # Correção de datas
        date_columns = {
            'df_desligados': ['DATA DEMISSÃO'],
            'df_admissao_abril': ['Admissão'],
            'df_ferias': ['DATA_INICIO', 'DATA_FIM']
        }

        for df_name, columns in date_columns.items():
            df = locals()[df_name]
            for col in columns:
                if col in df.columns:
                    df[col] = pd.to_datetime(df[col], errors='coerce')

        # Correção de valores numéricos
        df_ferias['DIAS DE FÉRIAS'] = df_ferias['DIAS DE FÉRIAS'].clip(0, 30)  # Limita entre 0 e 30 dias
        print("Arquivos carregados com sucesso.")

        # --- 1. Limpeza e Preparação Robusta dos Dados ---
        print("Iniciando limpeza e preparação dos dados...")
        
        # Função para remover espaços em branco dos nomes das colunas
        def clean_all_columns(df):
            df.columns = df.columns.str.strip()
            return df

        # Aplica a limpeza de colunas em todas as planilhas
        dataframes = [df_ativos, df_dias_uteis, df_sindicato_valor, df_desligados,
                      df_estagio, df_ferias, df_admissao_abril, df_afastamentos,
                      df_aprendiz, df_template]
        for df in dataframes:
            clean_all_columns(df)

        # Renomeia manualmente colunas com nomes incorretos ou ausentes
        df_exterior.columns = ['MATRICULA', 'VALOR_EXTERIOR', 'STATUS_EXTERIOR']
        df_sindicato_valor.columns = ['ESTADO', 'VALOR']
        df_dias_uteis.columns = ['SINDICATO', 'DIAS_UTEIS']

        # Executa outras tarefas de limpeza (remove linhas vazias, converte datas)
        df_sindicato_valor.dropna(how='all', inplace=True)
        df_desligados['DATA DEMISSÃO'] = pd.to_datetime(df_desligados['DATA DEMISSÃO'])
        df_admissao_abril['Admissão'] = pd.to_datetime(df_admissao_abril['Admissão'])
        print("Limpeza de dados concluída.")

        # --- 2. Consolidação dos Dados e Aplicação das Regras de Negócio ---
        print("Consolidando bases e aplicando regras de negócio...")

        # Cria uma lista única de matrículas a serem excluídas do cálculo
        ids_para_excluir = set(
            df_estagio['MATRICULA'].tolist() +
            df_exterior['MATRICULA'].tolist() +
            df_afastamentos['MATRICULA'].tolist() +
            df_aprendiz['MATRICULA'].tolist()
        )

        # Extrai o estado (UF) do nome do sindicato para criar uma chave de junção
        def get_state_from_sindicato(sindicato_string):
            if 'SP' in sindicato_string: return 'São Paulo'
            if 'RS' in sindicato_string: return 'Rio Grande do Sul'
            if 'RJ' in sindicato_string: return 'Rio de Janeiro'
            if 'PR' in sindicato_string: return 'Paraná'

            return 'N/A'

        df_ativos['ESTADO'] = df_ativos['Sindicato'].apply(get_state_from_sindicato)
        df_dias_uteis['ESTADO'] = df_dias_uteis['SINDICATO'].apply(get_state_from_sindicato)

        # Junta todas as informações em uma única tabela (DataFrame)
        df_merged = pd.merge(df_ativos, df_sindicato_valor, on='ESTADO', how='left')
        df_merged = pd.merge(df_merged, df_dias_uteis[['DIAS_UTEIS', 'ESTADO']], on='ESTADO', how='left')
        
        # Filtra a base, mantendo apenas os colaboradores elegíveis
        df_elegiveis = df_merged[~df_merged['MATRICULA'].isin(ids_para_excluir)].copy()

        # Adiciona os dados de férias, desligamentos e admissões à base de elegíveis
        df_final = pd.merge(df_elegiveis, df_ferias[['MATRICULA', 'DIAS DE FÉRIAS']], on='MATRICULA', how='left')
        df_final['DIAS DE FÉRIAS'] = df_final['DIAS DE FÉRIAS'].fillna(0)  # Fixed inplace warning
        df_final = pd.merge(df_final, df_desligados, on='MATRICULA', how='left')
        df_final = pd.merge(df_final, df_admissao_abril[['MATRICULA', 'Admissão']], on='MATRICULA', how='left')

        # --- 3. Lógica de Cálculo do Benefício ---
        print("Calculando valores do benefício...")
        # Use current year and month with day 15
        current_date = pd.Timestamp.now()
        termination_cutoff_date = pd.Timestamp(year=current_date.year, month=current_date.month, day=15)
        dias_a_pagar = []

        for index, row in df_final.iterrows():
            dias_base = row['DIAS_UTEIS']
            dias_ferias = row['DIAS DE FÉRIAS']
            dias_trabalhados = dias_base - dias_ferias

            # Regra para admissões no mês (cálculo proporcional)
            if pd.notna(row['Admissão']) and row['Admissão'].month == 5 and row['Admissão'].year == current_date.year:
                dias_no_mes = row['DIAS_UTEIS']
                dias_desde_admissao = dias_no_mes - (row['Admissão'].day - 1)
                proporcao = dias_desde_admissao / dias_no_mes
                dias_trabalhados = np.floor(dias_base * proporcao)
            
            # Regra para desligamentos
            if pd.notna(row['DATA DEMISSÃO']):
                if row['COMUNICADO DE DESLIGAMENTO'] == 'OK' and row['DATA DEMISSÃO'] <= termination_cutoff_date:
                    dias_trabalhados = 0 # Não recebe se comunicado até dia 15
                else:
                    # Proporcional se comunicado após dia 15
                    dias_uteis_ate_demissao = row['DATA DEMISSÃO'].day * (dias_base / 31)
                    dias_trabalhados = np.floor(dias_uteis_ate_demissao)
            
            dias_a_pagar.append(max(0, dias_trabalhados))

        df_final['DIAS_A_PAGAR'] = dias_a_pagar
        df_final['VALOR_TOTAL_VR'] = df_final['DIAS_A_PAGAR'] * df_final['VALOR']
        df_final['CUSTO_EMPRESA'] = df_final['VALOR_TOTAL_VR'] * 0.80 #CUSTO PARA EMPRESA
        df_final['CUSTO_PROFISSIONAL'] = df_final['VALOR_TOTAL_VR'] * 0.20 #CUSTO PROFISSIONAL
        print("Cálculos finalizados.")

        # --- 4. Validação e Formatação Final ---
        print("Aplicando validações e formatando o arquivo de saída...")
        
        # Aplica a regra de validação: valor total do benefício deve ser maior que zero
        df_validated = df_final[df_final['VALOR_TOTAL_VR'] > 0].copy()

        # Constrói o DataFrame final mapeando os dados calculados para as colunas do template
        output_df = pd.DataFrame()
        output_df['Matricula'] = df_validated['MATRICULA']
        output_df['Admissão'] = df_validated['Admissão'].dt.strftime('%d/%m/%Y')
        output_df['Sindicato do Colaborador'] = df_validated['Sindicato']
        output_df['Competência'] = '05/2025'
        output_df['Dias'] = df_validated['DIAS_A_PAGAR']
        output_df['VALOR DIÁRIO VR'] = df_validated['VALOR']
        output_df['TOTAL'] = df_validated['VALOR_TOTAL_VR']
        output_df['Custo empresa'] = df_validated['CUSTO_EMPRESA']
        output_df['Desconto profissional'] = df_validated['CUSTO_PROFISSIONAL']
        output_df['OBS GERAL'] = ''

        # Garante que a ordem final das colunas seja idêntica à do template
        final_columns_order = df_template.columns.tolist()
        output_df = output_df[final_columns_order]

        # --- 5. Geração do Arquivo de Saída ---
        output_filename = 'Output/VR_MENSAL_05_2025_FINAL.csv'
        output_df.to_csv(output_filename, index=False, decimal=',', sep=';')
        
        print("-" * 50)
        print("PROCESSO CONCLUÍDO COM SUCESSO!")
        print(f"Arquivo '{output_filename}' gerado, contendo {len(output_df)} registros válidos.")
        print("-" * 50)
        
        # --- 6. Envio de Notificação por Email ---
        print("Enviando notificação por email...")
        try:
            email_sent = send_process_completion_email(
                filename=output_filename,
                attach_file=True
            )
            if email_sent:
                print("✅ Email de notificação enviado com sucesso!")
            else:
                print("⚠️ Falha ao enviar email de notificação.")
        except Exception as e:
            print(f"⚠️ Erro ao enviar email: {e}")
        
        return output_filename

    except FileNotFoundError as e:
        print(f"\nERRO: Arquivo não encontrado - {e.filename}. Verifique se todos os arquivos Excel estão na pasta 'Import/' e se as pastas 'Import/' e 'Output/' existem.")
        return None
    except Exception as e:
        print(f"\nERRO INESPERADO: Ocorreu um erro durante a execução do agente. Detalhes: {e}")
        return None

# Executa a função principal do agente
if __name__ == "__main__":
    executar_automacao_vr()