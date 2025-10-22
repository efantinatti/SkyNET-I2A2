-- SkyNET-I2A2 - Dados Iniciais para Testes

-- Usuário administrador de teste
INSERT INTO users (
    id,
    email, 
    password_hash, 
    full_name, 
    company_name, 
    industry,
    is_active,
    is_verified
) VALUES (
    '550e8400-e29b-41d4-a716-446655440000',
    'admin@skynet-i2a2.com',
    '$2b$12$LQv3c1yqBwkVsvGOcOvz.O9.A8xEOjcv8ZeWMBiMJ.UZoaKKOdqGC',  -- password: admin123
    'Administrador SkyNET',
    'SkyNET-I2A2 Labs',
    'Tecnologia',
    true,
    true
) ON CONFLICT (email) DO NOTHING;

-- Usuário de teste para demonstração
INSERT INTO users (
    id,
    email, 
    password_hash, 
    full_name, 
    company_name, 
    industry,
    is_active,
    is_verified
) VALUES (
    '550e8400-e29b-41d4-a716-446655440001',
    'demo@empresa.com',
    '$2b$12$LQv3c1yqBwkVsvGOcOvz.O9.A8xEOjcv8ZeWMBiMJ.UZoaKKOdqGC',  -- password: demo123
    'João Silva',
    'Empresa Demo Ltda',
    'Comércio',
    true,
    true
) ON CONFLICT (email) DO NOTHING;

-- Snippets de código pré-definidos para acelerar demonstrações
INSERT INTO code_snippets (
    user_id,
    title,
    description,
    code,
    language,
    category,
    is_validated
) VALUES 
(
    '550e8400-e29b-41d4-a716-446655440000',
    'Cálculo de IPI',
    'Função para calcular IPI baseado na tabela do governo',
    'def calcular_ipi(valor_produtos, aliquota_ipi):\n    """Calcula IPI baseado no valor dos produtos"""\n    return valor_produtos * (aliquota_ipi / 100)',
    'python',
    'fiscal',
    true
),
(
    '550e8400-e29b-41d4-a716-446655440000',
    'Validação de CNPJ',
    'Função para validar formato e dígitos verificadores do CNPJ',
    'import re\n\ndef validar_cnpj(cnpj):\n    """Valida CNPJ brasileiro"""\n    cnpj = re.sub(r"[^0-9]", "", cnpj)\n    if len(cnpj) != 14:\n        return False\n    # Lógica de validação dos dígitos...\n    return True',
    'python',
    'fiscal',
    true
),
(
    '550e8400-e29b-41d4-a716-446655440000',
    'Análise de Outliers',
    'Detecta outliers usando método IQR',
    'def detectar_outliers_iqr(dados):\n    """Detecta outliers usando método IQR"""\n    Q1 = dados.quantile(0.25)\n    Q3 = dados.quantile(0.75)\n    IQR = Q3 - Q1\n    limite_inferior = Q1 - 1.5 * IQR\n    limite_superior = Q3 + 1.5 * IQR\n    return dados[(dados < limite_inferior) | (dados > limite_superior)]',
    'python',
    'analysis',
    true
);

-- Configurações do sistema (como uma tabela de settings)
CREATE TABLE IF NOT EXISTS system_settings (
    key VARCHAR(100) PRIMARY KEY,
    value TEXT,
    description TEXT,
    updated_at TIMESTAMP DEFAULT NOW()
);

INSERT INTO system_settings (key, value, description) VALUES
('app_version', '1.0.0', 'Versão atual da aplicação'),
('maintenance_mode', 'false', 'Modo manutenção ativado/desativado'),
('max_file_size_mb', '10', 'Tamanho máximo de arquivo em MB'),
('default_cache_ttl_hours', '24', 'TTL padrão do cache em horas'),
('email_enabled', 'true', 'Envio de emails habilitado'),
('audit_enabled', 'true', 'Log de auditoria habilitado'),
('rate_limit_per_minute', '60', 'Limite de requests por minuto'),
('gemini_model', 'gemini-pro', 'Modelo Gemini padrão'),
('openai_model', 'gpt-4o', 'Modelo OpenAI padrão'),
('supported_languages', 'pt-BR,en-US', 'Idiomas suportados'),
('company_name', 'SkyNET-I2A2', 'Nome da empresa'),
('support_email', 'support@skynet-i2a2.com', 'Email de suporte'),
('docs_url', 'https://docs.skynet-i2a2.com', 'URL da documentação');

-- Templates de email pré-definidos
CREATE TABLE IF NOT EXISTS email_templates (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) UNIQUE NOT NULL,
    subject VARCHAR(500),
    html_content TEXT,
    text_content TEXT,
    variables JSONB,  -- Variáveis disponíveis no template
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

INSERT INTO email_templates (name, subject, html_content, text_content, variables) VALUES
(
    'welcome',
    'Bem-vindo ao SkyNET-I2A2! 🚀',
    '<h1>Bem-vindo, {{full_name}}!</h1><p>Sua conta foi criada com sucesso. Agora você pode processar documentos fiscais e realizar análises exploratórias com IA.</p>',
    'Bem-vindo, {{full_name}}! Sua conta foi criada com sucesso.',
    '["full_name", "company_name"]'
),
(
    'analysis_completed',
    'Análise Concluída - {{analysis_type}}',
    '<h2>Sua análise foi concluída!</h2><p>Tipo: {{analysis_type}}</p><p>{{insights}}</p><p>Acesse seus resultados no sistema.</p>',
    'Sua análise {{analysis_type}} foi concluída. {{insights}}',
    '["analysis_type", "insights", "charts_count"]'
),
(
    'password_reset',
    'Redefinir sua senha - SkyNET-I2A2',
    '<h2>Redefinir Senha</h2><p>Clique no link para redefinir: {{reset_link}}</p><p>Este link expira em 1 hora.</p>',
    'Redefinir senha: {{reset_link}} (expira em 1 hora)',
    '["reset_link", "expires_at"]'
);

-- Dados de exemplo para demonstração (CFOPs comuns)
CREATE TABLE IF NOT EXISTS cfop_reference (
    code VARCHAR(10) PRIMARY KEY,
    description TEXT,
    type VARCHAR(50),  -- entrada, saída, etc.
    industry_applicable TEXT[],  -- Array de indústrias aplicáveis
    created_at TIMESTAMP DEFAULT NOW()
);

INSERT INTO cfop_reference (code, description, type, industry_applicable) VALUES
('1102', 'Compra para comercialização', 'entrada', '{"Comércio"}'),
('1403', 'Compra para industrialização', 'entrada', '{"Indústria"}'),
('2102', 'Compra para comercialização', 'entrada', '{"Comércio"}'),
('5102', 'Venda de mercadoria adquirida ou recebida de terceiros', 'saída', '{"Comércio"}'),
('5109', 'Venda de mercadoria adquirida ou recebida de terceiros, destinada à Zona Franca', 'saída', '{"Comércio"}'),
('5401', 'Venda de mercadoria de produção própria', 'saída', '{"Indústria"}'),
('6102', 'Venda de mercadoria adquirida ou recebida de terceiros', 'saída', '{"Comércio"}'),
('6401', 'Venda de mercadoria de produção própria', 'saída', '{"Indústria"}');

-- NCMs mais comuns por setor
CREATE TABLE IF NOT EXISTS ncm_reference (
    code VARCHAR(20) PRIMARY KEY,
    description TEXT,
    tax_rate NUMERIC(5,2),  -- Alíquota padrão
    industry_applicable TEXT[],
    created_at TIMESTAMP DEFAULT NOW()
);

INSERT INTO ncm_reference (code, description, tax_rate, industry_applicable) VALUES
('8471.30.12', 'Computadores portáteis', 0.00, '{"Tecnologia", "Comércio"}'),
('8517.12.31', 'Telefones celulares', 12.00, '{"Tecnologia", "Comércio"}'),
('1001.90.91', 'Trigo comum', 0.00, '{"Agronegócio"}'),
('1005.90.11', 'Milho em grão', 0.00, '{"Agronegócio"}'),
('2710.12.10', 'Gasolina comum', 25.00, '{"Energia"}'),
('3004.90.99', 'Medicamentos diversos', 0.00, '{"Farmacêutica"}')