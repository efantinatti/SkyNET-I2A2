#!/usr/bin/env python3
"""
Script de teste para validar instalação e imports do SkyNET-I2A2
"""

import sys
import os
from datetime import datetime

# Adiciona o diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Testa todos os imports principais"""
    tests = []
    
    # Core imports
    try:
        from backend.config import settings
        tests.append(("✅", "Config importado com sucesso"))
    except Exception as e:
        tests.append(("❌", f"Erro no import Config: {e}"))
    
    try:
        from backend.core.llm import LLMOrchestrator
        tests.append(("✅", "LLM importado com sucesso"))
    except Exception as e:
        tests.append(("❌", f"Erro no import LLM: {e}"))
    
    try:
        from backend.core.agents.coordinator import CoordinatorAgent
        tests.append(("✅", "CoordinatorAgent importado com sucesso"))
    except Exception as e:
        tests.append(("❌", f"Erro no import CoordinatorAgent: {e}"))
    
    # Frontend imports
    try:
        import streamlit as st
        tests.append(("✅", "Streamlit importado com sucesso"))
    except Exception as e:
        tests.append(("❌", f"Erro no import Streamlit: {e}"))
    
    # Data science imports
    try:
        import pandas as pd
        import numpy as np
        import plotly.graph_objects as go
        tests.append(("✅", "Bibliotecas de Data Science importadas"))
    except Exception as e:
        tests.append(("❌", f"Erro nas bibliotecas de Data Science: {e}"))
    
    # API imports
    try:
        from fastapi import FastAPI
        tests.append(("✅", "FastAPI importado com sucesso"))
    except Exception as e:
        tests.append(("❌", f"Erro no import FastAPI: {e}"))
    
    return tests

def test_configuration():
    """Testa se as configurações básicas estão corretas"""
    tests = []
    
    try:
        from backend.config import settings
        
        # Testa campos obrigatórios
        required_fields = [
            'supabase_url', 'supabase_key', 'jwt_secret_key', 'google_api_key'
        ]
        
        for field in required_fields:
            value = getattr(settings, field, None)
            if value and value != f"example_{field}":
                tests.append(("⚠️", f"{field}: Configurado (valor de exemplo)"))
            else:
                tests.append(("⚠️", f"{field}: Precisa ser configurado"))
        
        tests.append(("✅", f"Ambiente: {settings.environment}"))
        tests.append(("✅", f"Debug: {settings.debug}"))
        
    except Exception as e:
        tests.append(("❌", f"Erro ao testar configuração: {e}"))
    
    return tests

def main():
    """Função principal de teste"""
    print("🔧 SkyNET-I2A2 - Teste de Instalação")
    print("=" * 50)
    print(f"Data/Hora: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    print(f"Python: {sys.version}")
    print()
    
    # Teste de imports
    print("📦 Testando Imports:")
    import_tests = test_imports()
    for status, message in import_tests:
        print(f"  {status} {message}")
    print()
    
    # Teste de configuração
    print("⚙️ Testando Configurações:")
    config_tests = test_configuration()
    for status, message in config_tests:
        print(f"  {status} {message}")
    print()
    
    # Resumo
    success_count = len([t for t in import_tests + config_tests if t[0] == "✅"])
    warning_count = len([t for t in import_tests + config_tests if t[0] == "⚠️"])
    error_count = len([t for t in import_tests + config_tests if t[0] == "❌"])
    
    print("📊 Resumo:")
    print(f"  ✅ Sucessos: {success_count}")
    print(f"  ⚠️ Avisos: {warning_count}")
    print(f"  ❌ Erros: {error_count}")
    print()
    
    if error_count == 0:
        print("🎉 Instalação básica OK! Você pode prosseguir.")
        if warning_count > 0:
            print("💡 Lembre-se de configurar as chaves de API no arquivo .env")
    else:
        print("🚨 Há erros que precisam ser corrigidos.")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())