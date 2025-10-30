# Configuração para Streamlit Cloud

Este documento descreve como configurar e fazer deploy da aplicação no Streamlit Cloud com suporte a OCR de imagens.

## Pré-requisitos

1. Conta no [Streamlit Cloud](https://streamlit.io/cloud)
2. Repositório GitHub com o código da aplicação
3. Arquivo `.streamlit/secrets.toml` com credenciais (não fazer commit!)

## Arquivos Necessários

### 1. `packages.txt` (Raiz do Projeto)

Este arquivo instala dependências do sistema operacional no Streamlit Cloud:

```
tesseract-ocr
tesseract-ocr-por
poppler-utils
```

**O que cada pacote faz:**
- `tesseract-ocr`: Binário do Tesseract OCR
- `tesseract-ocr-por`: Language pack para português
- `poppler-utils`: Necessário para converter PDFs em imagens

### 2. `requirements.txt` (Raiz do Projeto)

Deve conter:
```
pytesseract==0.3.13
pdf2image==1.17.0
pillow==10.4.0
# ... outras dependências
```

### 3. `.streamlit/secrets.toml` (Não fazer commit!)

Exemplo:
```toml
# Google APIs
GOOGLE_API_KEY = "sua_chave_aqui"

# Supabase
SUPABASE_URL = "sua_url_aqui"
SUPABASE_KEY = "sua_chave_aqui"

# Tesseract (para Linux/Cloud)
TESSERACT_PATH = "/usr/bin/tesseract"
```

### 4. `.streamlit/config.toml` (Opcional)

Configurações da aplicação Streamlit.

## Deploy no Streamlit Cloud

### Passo 1: Preparar o Repositório

```bash
# Certifique-se de que os arquivos estão no repositório
git add packages.txt requirements.txt .streamlit/
git commit -m "Add Streamlit Cloud configuration"
git push
```

### Passo 2: Deploy

1. Acesse [Streamlit Cloud](https://share.streamlit.io/)
2. Clique em "New app"
3. Selecione seu repositório GitHub
4. Escolha a branch (geralmente `main`)
5. Defina o caminho do arquivo principal: `app.py`
6. Clique em "Deploy"

### Passo 3: Configurar Secrets

1. Na página da aplicação, clique em "Manage app"
2. Vá para "Secrets"
3. Cole o conteúdo do `.streamlit/secrets.toml`
4. Clique em "Save"

## Troubleshooting

### Erro: "tesseract is not installed"

**Solução**: Certifique-se de que `packages.txt` está na raiz do projeto com:
```
tesseract-ocr
tesseract-ocr-por
```

### Erro: "Failed loading language 'por'"

**Solução**: O language pack português pode não estar instalado. Adicione a `packages.txt`:
```
tesseract-ocr-por
```

### Erro: "Poppler not found"

**Solução**: Para processar PDFs, adicione a `packages.txt`:
```
poppler-utils
```

### Aplicação lenta ao processar imagens

**Solução**: Streamlit Cloud tem recursos limitados. Considere:
- Reduzir resolução das imagens
- Limitar tamanho máximo de upload
- Usar cache do Streamlit

```python
@st.cache_data
def process_image(image_path):
    # seu código aqui
    pass
```

## Variáveis de Ambiente

No Streamlit Cloud, use `.streamlit/secrets.toml` para variáveis sensíveis:

```toml
# Será acessível como st.secrets["GOOGLE_API_KEY"]
GOOGLE_API_KEY = "sua_chave"
SUPABASE_URL = "sua_url"
SUPABASE_KEY = "sua_chave"
```

## Monitoramento

Após o deploy:

1. Acesse a aplicação via URL fornecida
2. Verifique os logs em "Manage app" → "Logs"
3. Teste o upload de imagens para OCR
4. Monitore o uso de recursos

## Recursos Úteis

- [Documentação Streamlit Cloud](https://docs.streamlit.io/streamlit-cloud/get-started)
- [Tesseract OCR](https://github.com/UB-Mannheim/tesseract/wiki)
- [Streamlit Secrets Management](https://docs.streamlit.io/streamlit-cloud/get-started/deploy-an-app/connect-to-data-sources/secrets-management)

## Notas Importantes

1. **Não fazer commit de `.streamlit/secrets.toml`** - Use o gerenciador de secrets do Streamlit Cloud
2. **`packages.txt` é obrigatório** - Sem ele, Tesseract não será instalado
3. **Limite de upload** - Streamlit Cloud tem limite de 200MB por padrão
4. **Timeout** - Processos longos podem sofrer timeout (máx 1 hora)

## Exemplo de Configuração Completa

Estrutura do projeto:
```
skynet-I2A2-nf-final-v2/
├── app.py
├── requirements.txt
├── packages.txt                 ← NOVO
├── .streamlit/
│   ├── config.toml             ← NOVO
│   └── secrets.toml            ← NÃO fazer commit
├── frontend/
├── backend/
└── ...
```

Com essa configuração, o Streamlit Cloud instalará automaticamente:
- Tesseract OCR
- Language pack português
- Poppler (para PDFs)
- Todas as dependências Python

E sua aplicação terá suporte completo a OCR de imagens! 🎉
