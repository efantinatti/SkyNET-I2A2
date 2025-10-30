#!/bin/bash
# 🚀 Script de Configuração Automática do SkyNET-I2A2
# Sistema de Processamento Fiscal Inteligente

echo "🚀 Configurando SkyNET-I2A2 - Processamento Fiscal Inteligente"
echo "=================================================================="

# Verificar se Python está instalado
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 não encontrado. Instale Python 3.11+ primeiro."
    exit 1
fi

echo "✅ Python 3 encontrado: $(python3 --version)"

# Verificar se estamos no diretório correto
if [ ! -f "requirements.txt" ]; then
    echo "❌ requirements.txt não encontrado. Execute no diretório raiz do projeto."
    exit 1
fi

echo "📁 Diretório do projeto: $(pwd)"

# Criar ambiente virtual
echo ""
echo "🔧 Criando ambiente virtual..."
python3 -m venv venv

# Ativar ambiente virtual
echo "✅ Ambiente virtual criado"
echo "🔄 Ativando ambiente virtual..."
source venv/bin/activate

# Instalar dependências
echo ""
echo "📦 Instalando dependências..."
pip install --upgrade pip
pip install -r requirements.txt

echo ""
echo "✅ Dependências instaladas com sucesso!"

# Verificar se PostgreSQL está disponível
echo ""
echo "🗄️ Verificando PostgreSQL..."
if command -v psql &> /dev/null; then
    echo "✅ PostgreSQL encontrado: $(psql --version)"
    echo "💡 Para configurar PostgreSQL:"
    echo "   1. sudo -u postgres createuser -P skynet_user"
    echo "   2. sudo -u postgres createdb -O skynet_user skynet_db"
    echo "   3. Configure .streamlit/secrets.toml com as credenciais"
else
    echo "⚠️ PostgreSQL não encontrado. Usando modo local."
    echo "💡 Para instalar PostgreSQL:"
    echo "   Ubuntu/Debian: sudo apt install postgresql postgresql-contrib"
    echo "   macOS: brew install postgresql"
    echo "   Windows: https://postgresql.org/download/windows/"
fi

# Configurar Tesseract
echo ""
echo "🔍 Verificando Tesseract OCR..."
if command -v tesseract &> /dev/null; then
    echo "✅ Tesseract encontrado: $(tesseract --version | head -1)"
else
    echo "⚠️ Tesseract não encontrado. Instalação necessária para OCR."
    echo "💡 Para instalar:"
    echo "   Ubuntu/Debian: sudo apt install tesseract-ocr tesseract-ocr-por"
    echo "   macOS: brew install tesseract"
    echo "   Windows: choco install tesseract"
fi

# Executar migrações se PostgreSQL estiver disponível
echo ""
echo "🗄️ Executando migrações..."
if command -v psql &> /dev/null && [ -f "scripts/run_migration.py" ]; then
    echo "📋 Executando migrações do banco de dados..."
    python scripts/run_migration.py --help

    echo ""
    echo "💡 Para executar migrações:"
    echo "   python scripts/run_migration.py"
    echo "   # ou apenas uma migração específica:"
    echo "   python scripts/run_migration.py --single 014-add_recipient_columns.sql"
else
    echo "📋 Migrações adiadas. Configure PostgreSQL primeiro."
fi

# Executar testes
echo ""
echo "🧪 Executando testes de validação..."
echo "💡 Para executar todos os testes:"
echo "   pytest"
echo ""
echo "💡 Para executar testes específicos:"
echo "   pytest tests/test_date_conversion.py -v"
echo "   pytest tests/test_postgresql_storage.py -v"
echo "   pytest tests/test_recipient_fields.py -v"
echo "   pytest tests/test_fiscal_validator.py -v"

# Configuração final
echo ""
echo "🎉 Configuração concluída com sucesso!"
echo ""
echo "🚀 Para iniciar a aplicação:"
echo "   streamlit run app.py"
echo ""
echo "📚 Documentação completa:"
echo "   - README.md - Guia completo"
echo "   - docs/READY_TO_USE.md - Guia rápido"
echo "   - docs/UPLOAD_FIXES_README.md - Correções implementadas"
echo ""
echo "🆘 Problemas? Consulte:"
echo "   - Seção 'Solução de Problemas' no README.md"
echo "   - Execute: python scripts/run_migration.py --help"
echo "   - Verifique logs em logs/app.log"
echo ""
echo "✅ SkyNET-I2A2 está pronto para uso!"
echo "🎊 Sistema atualizado com PostgreSQL nativo e conversão de data automática!"
