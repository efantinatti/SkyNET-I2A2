-- SkyNET-I2A2 - Schema Inicial
-- Extensões necessárias para Supabase

-- Habilitar extensões do PostgreSQL
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "vector";  -- Para embeddings

-- Função para atualizar updated_at automaticamente
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Tipos ENUM para melhor consistência
CREATE TYPE user_industry_type AS ENUM ('Indústria', 'Comércio', 'Agronegócio', 'Serviços', 'Tecnologia', 'Outros');
CREATE TYPE document_type AS ENUM ('NFe', 'NFCe', 'CTe', 'PDF', 'XML');
CREATE TYPE classification_type AS ENUM ('compra', 'venda', 'serviço', 'devolução', 'transferência');
CREATE TYPE validation_status_type AS ENUM ('success', 'warning', 'error', 'pending');
CREATE TYPE analysis_type AS ENUM ('eda', 'correlation', 'outlier', 'time_series', 'classification');
CREATE TYPE process_status_type AS ENUM ('pending', 'processing', 'completed', 'error');
CREATE TYPE email_type AS ENUM ('welcome', 'report', 'alert', 'password_reset', 'confirmation');
CREATE TYPE email_status_type AS ENUM ('sent', 'failed', 'pending', 'delivered', 'bounced');