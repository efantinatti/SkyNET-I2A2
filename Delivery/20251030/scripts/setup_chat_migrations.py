"""
Migration helper script for chat system.

This script helps apply migrations in the correct order for the chat system,
with special handling for the vector extension requirement.
"""
import subprocess
import sys
from pathlib import Path

def run_migration_script():
    """Run the migration script with proper error handling."""

    print("🔧 Chat System Migration Helper")
    print("=" * 40)

    print("\n📋 Migration Order:")
    print("1. 001-007: Basic tables (already applied)")
    print("2. 008: Chat system tables")
    print("3. 009: Vector extension (requires manual step)")
    print("4. 010: Vector column conversion")

    print("\n⚠️  IMPORTANT: Vector Extension Setup")
    print("The vector extension needs to be enabled manually in Supabase.")
    print("Please follow these steps:")

    print("\n1️⃣  Go to your Supabase Dashboard")
    print("2️⃣  Navigate to SQL Editor")
    print("3️⃣  Run this command:")
    print("   CREATE EXTENSION vector;")

    response = input("\n❓ Have you enabled the vector extension in Supabase? (y/n): ").lower().strip()

    if response == 'y':
        print("\n✅ Great! Vector extension is enabled.")
        print("Running migrations 008, 009, and 010...")

        try:
            # Run the migration script
            result = subprocess.run([
                sys.executable, "scripts/run_migration.py"
            ], cwd=Path(__file__).parent, capture_output=True, text=True)

            print("📊 Migration Output:")
            print(result.stdout)

            if result.stderr:
                print("⚠️  Warnings/Errors:")
                print(result.stderr)

            if result.returncode == 0:
                print("\n🎉 All migrations completed successfully!")
                print("\n✅ What's now available:")
                print("   - Chat sessions and messages tables")
                print("   - Analysis cache for token optimization")
                print("   - Document summaries and insights")
                print("   - Vector embeddings (if extension enabled)")

                print("\n🚀 Next steps:")
                print("   1. Set GOOGLE_API_KEY in .streamlit/secrets.toml")
                print("   2. Run: streamlit run app.py")
                print("   3. Go to 'Chat IA' tab to start chatting!")
            else:
                print(f"\n❌ Migration failed with return code: {result.returncode}")
                print("Check the error messages above.")

        except Exception as e:
            print(f"\n❌ Error running migration script: {e}")

    else:
        print("\n⏸️  Please enable the vector extension first.")
        print("\n📝 Steps to enable vector extension:")
        print("1. Go to https://supabase.com/dashboard")
        print("2. Select your project")
        print("3. Go to SQL Editor")
        print("4. Run: CREATE EXTENSION vector;")
        print("5. Come back and run this script again")

        print("\n💡 Note: The chat system will work without vector support,")
        print("   but advanced semantic search features will be limited.")

if __name__ == "__main__":
    run_migration_script()
