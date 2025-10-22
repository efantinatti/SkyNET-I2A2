-- SkyNET-I2A2 - Tabelas de Cache, Documentos e Análises

-- 5. Documentos fiscais processados
CREATE TABLE IF NOT EXISTS fiscal_documents (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  file_name VARCHAR(255),
  file_path TEXT,
  file_size_bytes BIGINT,
  file_type document_type,
  document_number VARCHAR(50),
  document_key VARCHAR(44),  -- Chave de acesso NFe (44 dígitos)
  issuer_name VARCHAR(255),
  issuer_cnpj VARCHAR(20),
  recipient_name VARCHAR(255),
  recipient_cnpj VARCHAR(20),
  document_date DATE,
  document_value NUMERIC(15, 2),
  tax_value NUMERIC(15, 2),
  classification classification_type,
  sector VARCHAR(100),
  cfop VARCHAR(10),
  ncm VARCHAR(20),
  extracted_data JSONB,  -- Dados estruturados completos
  validation_status validation_status_type DEFAULT 'pending',
  validation_notes TEXT,
  processing_time_ms INT,
  agent_used VARCHAR(50),  -- Qual agente processou
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

-- 6. Análises exploratórias (EDA)
CREATE TABLE IF NOT EXISTS analyses (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  session_id UUID REFERENCES sessions(id) ON DELETE CASCADE,
  csv_file_name VARCHAR(255),
  csv_file_path TEXT,
  csv_file_size_bytes BIGINT,
  csv_rows_count INT,
  csv_columns_count INT,
  analysis_type analysis_type,
  analysis_data JSONB,  -- Estatísticas, correlações, etc.
  charts JSONB,  -- Array de Plotly JSON specs
  insights TEXT,  -- Texto gerado pelo LLM
  code_generated TEXT,  -- Código Python gerado
  status process_status_type DEFAULT 'pending',
  error_message TEXT,
  processing_time_ms INT,
  agent_used VARCHAR(50),
  created_at TIMESTAMP DEFAULT NOW(),
  completed_at TIMESTAMP,
  updated_at TIMESTAMP DEFAULT NOW()
);

-- 7. Conversas (Chat com agentes)
CREATE TABLE IF NOT EXISTS conversations (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  session_id UUID REFERENCES sessions(id) ON DELETE CASCADE,
  analysis_id UUID REFERENCES analyses(id) ON DELETE SET NULL,
  document_id UUID REFERENCES fiscal_documents(id) ON DELETE SET NULL,
  user_message TEXT,
  agent_response TEXT,
  agent_name VARCHAR(50),  -- coordinator, analyst, consultant, etc.
  reasoning JSONB,  -- Raciocínio do agente (para debug)
  tokens_used INT,
  response_time_ms INT,
  created_at TIMESTAMP DEFAULT NOW()
);

-- 8. Cache de tokens (Gemini API)
CREATE TABLE IF NOT EXISTS token_cache (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  cache_key VARCHAR(500) UNIQUE,  -- Hash do prompt/context
  prompt_hash VARCHAR(64),  -- SHA-256 do prompt
  cached_embedding VECTOR(768),  -- Embedding cached (Google)
  api_response JSONB,  -- Resposta completa Gemini
  tokens_used INT,
  model_used VARCHAR(50),
  hit_count INT DEFAULT 0,  -- Quantas vezes foi reutilizado
  created_at TIMESTAMP DEFAULT NOW(),
  expires_at TIMESTAMP DEFAULT NOW() + INTERVAL '24 hours',
  last_used TIMESTAMP DEFAULT NOW()
);

-- 9. Histórico de emails enviados
CREATE TABLE IF NOT EXISTS email_log (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  recipient_email VARCHAR(255),
  subject VARCHAR(500),
  email_type email_type,
  template_used VARCHAR(100),
  status email_status_type DEFAULT 'pending',
  sendgrid_message_id VARCHAR(255),
  error_message TEXT,
  sent_at TIMESTAMP,
  delivered_at TIMESTAMP,
  opened_at TIMESTAMP,
  clicked_at TIMESTAMP,
  created_at TIMESTAMP DEFAULT NOW()
);

-- 10. Auditoria de ações (conformidade)
CREATE TABLE IF NOT EXISTS audit_log (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  action VARCHAR(100),  -- upload, process, analyze, etc.
  resource_type VARCHAR(50),  -- document, analysis, user
  resource_id VARCHAR(100),
  old_values JSONB,  -- Estado anterior
  new_values JSONB,  -- Estado novo
  details JSONB,
  ip_address INET,
  user_agent TEXT,
  created_at TIMESTAMP DEFAULT NOW()
);

-- 11. Snippets de código gerados
CREATE TABLE IF NOT EXISTS code_snippets (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  title VARCHAR(255),
  description TEXT,
  code TEXT,
  language VARCHAR(50) DEFAULT 'python',
  category VARCHAR(100),  -- fiscal, analysis, etc.
  is_validated BOOLEAN DEFAULT FALSE,
  validation_result JSONB,
  usage_count INT DEFAULT 0,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

-- Triggers para updated_at
CREATE TRIGGER update_fiscal_documents_updated_at BEFORE UPDATE ON fiscal_documents 
  FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_analyses_updated_at BEFORE UPDATE ON analyses 
  FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_code_snippets_updated_at BEFORE UPDATE ON code_snippets 
  FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Trigger para atualizar last_used no cache
CREATE OR REPLACE FUNCTION update_cache_last_used()
RETURNS TRIGGER AS $$
BEGIN
    NEW.last_used = NOW();
    NEW.hit_count = OLD.hit_count + 1;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_token_cache_last_used BEFORE UPDATE ON token_cache 
  FOR EACH ROW EXECUTE FUNCTION update_cache_last_used();

-- Índices para performance
CREATE INDEX idx_fiscal_documents_user ON fiscal_documents(user_id);
CREATE INDEX idx_fiscal_documents_type ON fiscal_documents(file_type);
CREATE INDEX idx_fiscal_documents_date ON fiscal_documents(document_date);
CREATE INDEX idx_fiscal_documents_status ON fiscal_documents(validation_status);
CREATE INDEX idx_fiscal_documents_cnpj ON fiscal_documents(issuer_cnpj, recipient_cnpj);

CREATE INDEX idx_analyses_user ON analyses(user_id);
CREATE INDEX idx_analyses_session ON analyses(session_id);
CREATE INDEX idx_analyses_type ON analyses(analysis_type);
CREATE INDEX idx_analyses_status ON analyses(status);

CREATE INDEX idx_conversations_session ON conversations(session_id);
CREATE INDEX idx_conversations_user ON conversations(user_id);
CREATE INDEX idx_conversations_analysis ON conversations(analysis_id);
CREATE INDEX idx_conversations_document ON conversations(document_id);

CREATE INDEX idx_token_cache_key ON token_cache(cache_key);
CREATE INDEX idx_token_cache_hash ON token_cache(prompt_hash);
CREATE INDEX idx_token_cache_user ON token_cache(user_id);
CREATE INDEX idx_token_cache_expires ON token_cache(expires_at);

CREATE INDEX idx_email_log_user ON email_log(user_id);
CREATE INDEX idx_email_log_type ON email_log(email_type);
CREATE INDEX idx_email_log_status ON email_log(status);

CREATE INDEX idx_audit_log_user ON audit_log(user_id);
CREATE INDEX idx_audit_log_resource ON audit_log(resource_type, resource_id);
CREATE INDEX idx_audit_log_action ON audit_log(action);

CREATE INDEX idx_code_snippets_user ON code_snippets(user_id);
CREATE INDEX idx_code_snippets_category ON code_snippets(category);

-- RLS Policies
ALTER TABLE fiscal_documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE analyses ENABLE ROW LEVEL SECURITY;
ALTER TABLE conversations ENABLE ROW LEVEL SECURITY;
ALTER TABLE token_cache ENABLE ROW LEVEL SECURITY;
ALTER TABLE email_log ENABLE ROW LEVEL SECURITY;
ALTER TABLE audit_log ENABLE ROW LEVEL SECURITY;
ALTER TABLE code_snippets ENABLE ROW LEVEL SECURITY;

-- Políticas RLS (usuários só veem seus próprios dados)
CREATE POLICY "Users can manage own documents" ON fiscal_documents FOR ALL USING (auth.uid() = user_id);
CREATE POLICY "Users can manage own analyses" ON analyses FOR ALL USING (auth.uid() = user_id);
CREATE POLICY "Users can manage own conversations" ON conversations FOR ALL USING (auth.uid() = user_id);
CREATE POLICY "Users can manage own cache" ON token_cache FOR ALL USING (auth.uid() = user_id);
CREATE POLICY "Users can view own emails" ON email_log FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Users can view own audit" ON audit_log FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Users can manage own code" ON code_snippets FOR ALL USING (auth.uid() = user_id);

-- Função para limpeza automática de cache expirado
CREATE OR REPLACE FUNCTION cleanup_expired_cache()
RETURNS void AS $$
BEGIN
    DELETE FROM token_cache WHERE expires_at < NOW();
    DELETE FROM password_reset_tokens WHERE expires_at < NOW();
    DELETE FROM sessions WHERE expires_at < NOW() AND is_active = false;
END;
$$ LANGUAGE plpgsql;

-- View para estatísticas por usuário
CREATE VIEW user_stats AS
SELECT 
    u.id,
    u.email,
    u.company_name,
    u.industry,
    COUNT(DISTINCT fd.id) as total_documents,
    COUNT(DISTINCT a.id) as total_analyses,
    COUNT(DISTINCT c.id) as total_conversations,
    COALESCE(SUM(fd.document_value), 0) as total_document_value,
    u.created_at,
    u.last_login
FROM users u
LEFT JOIN fiscal_documents fd ON u.id = fd.user_id
LEFT JOIN analyses a ON u.id = a.user_id  
LEFT JOIN conversations c ON u.id = c.user_id
GROUP BY u.id, u.email, u.company_name, u.industry, u.created_at, u.last_login;