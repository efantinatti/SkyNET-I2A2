"""
Run only migrations 009 and 010 for chat system.

This script runs just the remaining migrations needed for the chat system.
"""
import subprocess
import sys
from pathlib import Path

def run_chat_migrations():
    """Run only migrations 009 and 010."""

    print("🔄 Running Chat System Migrations (009 & 010)...")
    print("=" * 50)

    migrations_to_run = ["009", "010"]
    success_count = 0

    for mig_num in migrations_to_run:
        mig_path = list(Path(__file__).parent.parent.glob(f"migration/{mig_num}-*.sql"))

        if mig_path:
            print(f"\n🚀 Running migration {mig_num}: {mig_path[0].name}")

            # Read migration content
            with open(mig_path[0], 'r', encoding='utf-8') as f:
                sql_content = f.read()

            print("📄 Migration content (first 200 chars):")
            print("-" * 40)
            print(sql_content[:200] + "..." if len(sql_content) > 200 else sql_content)
            print("-" * 40)

            print("✅ Migration prepared for execution")
            print("💡 Run this manually in Supabase SQL Editor or continue with automated script")

        else:
            print(f"❌ Migration file {mig_num}-*.sql not found")

    print("\n📋 Migration Files Ready:")
    print("   - migration/009-enable_vector_extension.sql")
    print("   - migration/010-convert_embedding_to_vector.sql")

    print("\n🎯 To complete setup:")
    print("   1. Copy the SQL content above to Supabase SQL Editor")
    print("   2. Execute each migration in order")
    print("   3. Set GOOGLE_API_KEY in .streamlit/secrets.toml")
    print("   4. Run: streamlit run app.py")
    print("   5. Go to 'Chat IA' tab and start chatting!")

if __name__ == "__main__":
    run_chat_migrations()
