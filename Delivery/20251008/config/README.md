# 📁 Pasta de Configurações

Esta pasta contém arquivos de configuração da aplicação InsightAgent EDA.

## 📄 Arquivos

### `theme.py`
**Configuração de tema e interface da aplicação**

Responsável por:
- Configurar o layout da página (wide mode)
- Definir título e ícone da página
- Carregar estilos CSS personalizados
- Aplicar temas visuais

```python
from config.theme import init_ui

# Inicializa a interface
init_ui()
```

---

### `fantinatti_config.py`
**Configurações personalizadas do Ernani Fantinatti**

Contém:
- Informações do desenvolvedor
- Configurações da aplicação personalizada
- Mensagens customizadas
- Temas e cores
- Links e referências

```python
from config.fantinatti_config import get_developer_info, get_welcome_message

# Obtém informações do desenvolvedor
dev_info = get_developer_info()
print(dev_info['name'])  # "Ernani Fantinatti"

# Obtém mensagem de boas-vindas
welcome = get_welcome_message()
```

**Configurações disponíveis:**

#### Informações do Desenvolvedor
```python
DEVELOPER_INFO = {
    "name": "Ernani Fantinatti",
    "github": "efantinatti",
    "repository": "https://github.com/efantinatti/SkyNET-I2A2",
    "project": "SkyNET-I2A2 - Delivery/Fantinatti",
    "version": "1.0.0-fantinatti",
    "year": "2025"
}
```

#### Configurações da Aplicação
```python
APP_CONFIG = {
    "title": "InsightAgent EDA - Ernani Fantinatti",
    "subtitle": "Seu Assistente de Análise de Dados com IA",
    "icon": "📊",
    "description": "Desenvolvido por Ernani Fantinatti para o projeto I2A2"
}
```

#### Tema Personalizado
```python
THEME = {
    "primary_color": "#4f46e5",
    "background_color": "#ffffff",
    "secondary_background": "#f8fafc",
    "text_color": "#1f2937",
    "font": "sans serif"
}
```

---

## 🎨 Personalização

### Como Alterar as Cores

Edite o arquivo `fantinatti_config.py`:

```python
THEME = {
    "primary_color": "#sua-cor-aqui",  # Cor primária
    "background_color": "#sua-cor-aqui",  # Fundo
    "secondary_background": "#sua-cor-aqui",  # Fundo secundário
    "text_color": "#sua-cor-aqui",  # Cor do texto
    "font": "sua-fonte"  # Fonte
}
```

### Como Alterar Mensagens

Edite o arquivo `fantinatti_config.py`:

```python
MESSAGES = {
    "welcome": """
    Sua mensagem de boas-vindas personalizada aqui!
    """,
    "no_data": """
    Sua mensagem quando não há dados carregados
    """,
    "footer": """
    Seu rodapé personalizado
    """
}
```

### Como Alterar o Título da Página

Edite o arquivo `theme.py`:

```python
st.set_page_config(
    page_title="Seu Título Aqui",  # Aparece na aba do navegador
    page_icon="🎯",  # Ícone da aba
)
```

---

## 🔧 Funções Auxiliares

### `get_developer_info()`
Retorna um dicionário com informações do desenvolvedor.

```python
info = get_developer_info()
# {'name': 'Ernani Fantinatti', 'github': 'efantinatti', ...}
```

### `get_app_config()`
Retorna configurações da aplicação.

```python
config = get_app_config()
# {'title': 'InsightAgent EDA - Ernani Fantinatti', ...}
```

### `get_welcome_message()`
Retorna a mensagem de boas-vindas personalizada.

```python
message = get_welcome_message()
# String com a mensagem formatada
```

### `get_theme()`
Retorna configurações de tema.

```python
theme = get_theme()
# {'primary_color': '#4f46e5', ...}
```

---

## 📚 Uso nos Outros Arquivos

### No `app.py`
```python
from config.theme import init_ui
from config.fantinatti_config import get_developer_info

# Inicializa a interface
init_ui()

# Usa informações personalizadas
dev_info = get_developer_info()
st.sidebar.caption(f"Desenvolvido por {dev_info['name']}")
```

### Nos componentes
```python
from config.fantinatti_config import get_welcome_message

# Exibe mensagem personalizada
welcome = get_welcome_message()
st.markdown(welcome)
```

---

## 🎯 Boas Práticas

### Separação de Responsabilidades
- **`theme.py`**: Configurações visuais e de layout
- **`fantinatti_config.py`**: Informações personalizadas e mensagens

### Centralização
- Mantenha todas as configurações nesta pasta
- Facilita manutenção e personalização
- Evita duplicação de código

### Versionamento
- Sempre atualize a versão ao fazer mudanças
- Documente as alterações no `VERSAO.md`

---

## 🔄 Adicionando Novas Configurações

### Passo 1: Adicionar ao arquivo
Edite `fantinatti_config.py`:

```python
# Nova configuração
NOVA_CONFIG = {
    "parametro1": "valor1",
    "parametro2": "valor2"
}
```

### Passo 2: Criar função auxiliar
```python
def get_nova_config():
    """Retorna nova configuração"""
    return NOVA_CONFIG
```

### Passo 3: Documentar
Adicione à documentação e aos comentários do código.

### Passo 4: Usar no código
```python
from config.fantinatti_config import get_nova_config

config = get_nova_config()
```

---

## 📖 Documentação Relacionada

- [README.md](../README.md) - Documentação principal
- [PERSONALIZACAO.md](../PERSONALIZACAO.md) - Guia de personalização
- [VERSAO.md](../VERSAO.md) - Histórico de versões

---

## 🆘 Problemas Comuns

### Erro ao importar configurações
```python
# ❌ Errado
from fantinatti_config import DEVELOPER_INFO

# ✅ Correto
from config.fantinatti_config import DEVELOPER_INFO
```

### Configuração não sendo aplicada
1. Verifique se a função está sendo chamada
2. Confirme que o arquivo foi salvo
3. Reinicie a aplicação (Ctrl+C e execute novamente)

### Erro de sintaxe
- Verifique vírgulas e aspas
- Use um editor com syntax highlighting
- Teste as mudanças localmente

---

Desenvolvido por Ernani Fantinatti

[GitHub](https://github.com/efantinatti) | [Voltar](../README.md)
