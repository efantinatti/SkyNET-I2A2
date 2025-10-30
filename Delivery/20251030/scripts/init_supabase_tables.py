"""
Initialize Supabase tables for the SkyNET-I2A2 application.

This script checks if the required tables exist in your Supabase database
and creates them if they don't exist.
"""
import os
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from supabase import create_client, Client
from config import SUPABASE_URL, SUPABASE_KEY, DB_USER, DB_PASSWORD, DB_HOST, DB_PORT, DATABASE

def check_and_create_tables():
    """Check if required tables exist and create them if they don't."""
    try:
        # Initialize Supabase client
        print("Connecting to Supabase...")
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        
        # Check if fiscal_documents table exists
        print("Checking if tables exist...")
        try:
            # Try to query the table
            result = supabase.table('fiscal_documents').select('*', count='exact').limit(1).execute()
            print("✅ fiscal_documents table exists")
        except Exception as e:
            if "relation \"fiscal_documents\" does not exist" in str(e):
                print("❌ fiscal_documents table does not exist")
                create_tables(supabase)
            else:
                raise
                
    except Exception as e:
        print(f"❌ Error initializing Supabase: {str(e)}")
        sys.exit(1)

def create_tables(supabase: Client):
    """Create the required tables in Supabase."""
    print("Creating tables...")
    
    # SQL to create the tables
    sql_commands = """
    -- Enable the pgcrypto extension for UUID generation
    CREATE EXTENSION IF NOT EXISTS pgcrypto;

    -- Fiscal Documents Table
    CREATE TABLE IF NOT EXISTS fiscal_documents (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        filename TEXT NOT NULL,
        file_type TEXT,
        file_size INTEGER,
        content_type TEXT,
        upload_date TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
        status TEXT DEFAULT 'pending',
        metadata JSONB,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
    );

    -- Document Analyses Table
    CREATE TABLE IF NOT EXISTS document_analyses (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        document_id UUID REFERENCES fiscal_documents(id) ON DELETE CASCADE,
        analysis_type TEXT NOT NULL,
        status TEXT DEFAULT 'pending',
        result JSONB,
        error_message TEXT,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
    );

    -- Create indexes for better performance
    CREATE INDEX IF NOT EXISTS idx_fiscal_documents_status ON fiscal_documents(status);
    CREATE INDEX IF NOT EXISTS idx_document_analyses_document_id ON document_analyses(document_id);
    CREATE INDEX IF NOT EXISTS idx_document_analyses_status ON document_analyses(status);

    -- Set up Row Level Security (RLS) policies
    ALTER TABLE fiscal_documents ENABLE ROW LEVEL SECURITY;
    ALTER TABLE document_analyses ENABLE ROW LEVEL SECURITY;

    -- Create policies to allow public read access (adjust according to your security requirements)
    CREATE POLICY "Enable read access for all users" ON public.fiscal_documents
        FOR SELECT USING (true);
        
    CREATE POLICY "Enable read access for all users" ON public.document_analyses
        FOR SELECT USING (true);
    
    -- Create policies to allow insert/update/delete for authenticated users (adjust as needed)
    CREATE POLICY "Enable insert for authenticated users" ON public.fiscal_documents
        FOR INSERT TO authenticated WITH CHECK (true);
        
    CREATE POLICY "Enable update for authenticated users" ON public.fiscal_documents
        FOR UPDATE TO authenticated USING (true) WITH CHECK (true);
        
    CREATE POLICY "Enable delete for authenticated users" ON public.fiscal_documents
        FOR DELETE TO authenticated USING (true);
    
    -- Add a comment to the tables
    COMMENT ON TABLE fiscal_documents IS 'Stores metadata about uploaded fiscal documents';
    COMMENT ON TABLE document_analyses IS 'Stores analysis results for fiscal documents';
    """
    
    try:
        # Execute the SQL commands
        result = supabase.rpc('pg_execute', {'query': sql_commands}).execute()
        print("✅ Successfully created tables and set up permissions")
    except Exception as e:
        print(f"❌ Error creating tables: {str(e)}")
        raise

if __name__ == "__main__":
    print("=== SkyNET-I2A2 Supabase Table Initialization ===\n")
    
    # Verify Supabase connection details
    print("Verifying configuration...")
    if not all([SUPABASE_URL, SUPABASE_KEY]):
        print("❌ Error: SUPABASE_URL and SUPABASE_KEY must be set in .env or .streamlit/secrets.toml")
        sys.exit(1)
        
    print(f"Supabase URL: {SUPABASE_URL}")
    print(f"Supabase Key: {'*' * 8}{SUPABASE_KEY[-4:] if SUPABASE_KEY else 'None'}")
    print(f"Database: {DATABASE}@{DB_HOST}:{DB_PORT}")
    
    check_and_create_tables()
    print("\n✅ Initialization complete!")
