"""
Script para executar migrações SQL no PostgreSQL/Supabase.

Uso:
  python scripts/apply_migrations.py              # Executa todas as migrações
  python scripts/apply_migrations.py --single NOME # Executa apenas uma migração específica
  python scripts/apply_migrations.py --help       # Mostra esta ajuda
"""
import os
import sys
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from pathlib import Path

# Adiciona o diretório raiz ao path para importar o config
sys.path.append(str(Path(__file__).parent.parent))

try:
    from config import DATABASE_CONFIG
    print("✅ Configurações carregadas com sucesso do config.py")
except ImportError as e:
    print(f"❌ Erro ao importar configurações: {e}")
    print("Certifique-se de que o arquivo config.py existe no diretório raiz do projeto.")
    sys.exit(1)

def load_migration_file(migration_file: str) -> str:
    """Carrega o conteúdo de um arquivo de migração."""
    try:
        with open(migration_file, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        print(f"Erro ao ler o arquivo de migração {migration_file}: {e}")
        sys.exit(1)

def run_migration(conn, migration_sql: str):
    """Executa uma migração SQL."""
    try:
        with conn.cursor() as cur:
            # Executa cada comando separadamente
            for command in migration_sql.split(';'):
                command = command.strip()
                if command:
                    print(f"Executando: {command[:100]}...")
                    cur.execute(command)
        conn.commit()
        print("✅ Migração executada com sucesso!")
    except Exception as e:
        conn.rollback()
        print(f"❌ Erro ao executar migração: {e}")
        sys.exit(1)


def main():
    # Verifica argumentos de linha de comando
    if len(sys.argv) > 1:
        if sys.argv[1] == '--single' and len(sys.argv) > 2:
            # Modo single migration
            migration_name = sys.argv[2]
            run_single_migration(migration_name)
            return
        elif sys.argv[1] in ['--help', '-h']:
            print("Uso:")
            print("  python scripts/apply_migrations.py              # Executa todas as migrações")
            print("  python scripts/apply_migrations.py --single NOME # Executa apenas uma migração específica")
            print("  python scripts/apply_migrations.py --help       # Mostra esta ajuda")
            sys.exit(0)

    # Modo padrão: executa todas as migrações
    run_all_migrations()


def run_single_migration(migration_name: str):
    """Executa uma migração específica."""
    db_config = {
        **DATABASE_CONFIG,
        'connect_timeout': '10'  # Timeout de conexão de 10 segundos
    }

    # Verifica se as credenciais necessárias estão presentes
    required = ['dbname', 'user', 'password', 'host', 'port']
    missing = [key for key in required if not db_config.get(key)]
    if missing:
        print(f"❌ Erro: Configurações ausentes no config.py: {', '.join(missing)}")
        sys.exit(1)

    # Imprime as configurações (sem a senha) para depuração
    print("🔑 Configurações de conexão:")
    for key, value in db_config.items():
        if key != 'password':
            print(f"   {key}: {value}")

    print("🔗 Conectando ao banco de dados...")

    # Conecta ao banco de dados
    try:
        conn = psycopg2.connect(**db_config)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        print("✅ Conexão com o banco de dados estabelecida com sucesso!")
    except Exception as e:
        print(f"❌ Erro ao conectar ao banco de dados: {e}")
        print("\nDicas de solução de problemas:")
        print("1. Verifique se o seu IP está na lista de permissões do Supabase")
        print("2. Verifique se as credenciais estão corretas")
        print("3. Tente desativar temporariamente o firewall ou VPN, se estiver usando")
        sys.exit(1)

    # Encontra o arquivo de migração específico
    migrations_dir = Path(__file__).parent.parent / 'migration'
    migration_file = migrations_dir / migration_name

    if not migration_file.exists():
        print(f"❌ Arquivo de migração não encontrado: {migration_name}")
        print(f"📂 Arquivos disponíveis em {migrations_dir}:")
        for f in migrations_dir.glob('*.sql'):
            if f.name != '000_template.sql':
                print(f"   {f.name}")
        sys.exit(1)

    print(f"\n🚀 Executando migração específica: {migration_name}")
    migration_sql = load_migration_file(migration_file)
    run_migration(conn, migration_sql)

    conn.close()
    print(f"\n✨ Migração {migration_name} concluída com sucesso!")


def run_all_migrations():
    """Executa todas as migrações em ordem."""
    db_config = {
        **DATABASE_CONFIG,
        'connect_timeout': '10'  # Timeout de conexão de 10 segundos
    }

    # Verifica se as credenciais necessárias estão presentes
    required = ['dbname', 'user', 'password', 'host', 'port']
    missing = [key for key in required if not db_config.get(key)]
    if missing:
        print(f"❌ Erro: Configurações ausentes no config.py: {', '.join(missing)}")
        sys.exit(1)

    # Imprime as configurações (sem a senha) para depuração
    print("🔑 Configurações de conexão:")
    for key, value in db_config.items():
        if key != 'password':
            print(f"   {key}: {value}")

    print("🔗 Conectando ao banco de dados...")

    # Conecta ao banco de dados
    try:
        conn = psycopg2.connect(**db_config)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        print("✅ Conexão com o banco de dados estabelecida com sucesso!")
    except Exception as e:
        print(f"❌ Erro ao conectar ao banco de dados: {e}")
        print("\nDicas de solução de problemas:")
        print("1. Verifique se o seu IP está na lista de permissões do Supabase")
        print("2. Verifique se as credenciais estão corretas")
        print("3. Tente desativar temporariamente o firewall ou VPN, se estiver usando")
        print("4. Verifique se você pode se conectar ao host: aws-1-us-east-1.pooler.supabase.com na porta 5432")
        sys.exit(1)

    # Encontra o arquivo de migração mais recente
    migrations_dir = Path(__file__).parent.parent / 'migration'
    migration_files = sorted([f for f in migrations_dir.glob('*.sql') if f.name != '000_template.sql'])

    if not migration_files:
        print("ℹ️  Nenhum arquivo de migração encontrado.")
        sys.exit(0)

    print("\n📋 Migrações encontradas:")
    for i, file in enumerate(migration_files, 1):
        print(f"  {i}. {file.name}")

    # Pede confirmação ao usuário
    print("\n⚠️  Deseja executar as migrações listadas acima? (s/n)")
    if input().lower() != 's':
        print("🚫 Migração cancelada pelo usuário.")
        sys.exit(0)

    # Executa cada migração
    for migration_file in migration_files:
        print(f"\n🚀 Executando migração: {migration_file.name}")
        migration_sql = load_migration_file(migration_file)
        run_migration(conn, migration_sql)

    conn.close()
    print("\n✨ Todas as migrações foram concluídas com sucesso!")


if __name__ == "__main__":
    main()
