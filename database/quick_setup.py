#!/usr/bin/env python3
"""
Quick Database Setup for Resume Customizer
Fast PostgreSQL database creation and initialization
"""

import os
import sys
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def create_env_file():
    """Create .env file with database configuration."""
    env_content = """# Resume Customizer Database Configuration
# PostgreSQL Database Settings

# For local PostgreSQL
DB_HOST=localhost
DB_PORT=5432
DB_NAME=resume_customizer
DB_USER=postgres
DB_PASSWORD=your_password_here

# For cloud databases (Neon, Supabase, etc.)
# DATABASE_URL=postgresql://username:password@host:port/database

# Application Settings
STREAMLIT_SERVER_PORT=8501
LOG_LEVEL=INFO
"""
    
    try:
        with open('.env', 'w') as f:
            f.write(env_content)
        print("✅ Created .env file")
        print("📝 Please edit .env file with your PostgreSQL credentials")
        return True
    except Exception as e:
        print(f"❌ Failed to create .env file: {e}")
        return False

def install_dependencies():
    """Install required PostgreSQL dependencies."""
    try:
        import subprocess
        import sys
        
        print("📦 Installing PostgreSQL dependencies...")
        
        dependencies = [
            "psycopg2-binary>=2.9.0",
            "sqlalchemy>=2.0.0",
            "alembic>=1.12.0"
        ]
        
        for dep in dependencies:
            print(f"Installing {dep}...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", dep])
        
        print("✅ Dependencies installed successfully")
        return True
        
    except Exception as e:
        print(f"❌ Failed to install dependencies: {e}")
        return False

def create_database():
    """Create the PostgreSQL database if it doesn't exist."""
    try:
        import psycopg2
        from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
        
        # Get connection parameters
        host = os.getenv('DB_HOST', 'localhost')
        port = os.getenv('DB_PORT', '5432')
        user = os.getenv('DB_USER', 'postgres')
        password = os.getenv('DB_PASSWORD', 'password')
        database = os.getenv('DB_NAME', 'resume_customizer')
        
        # Connect to PostgreSQL server (not specific database)
        conn = psycopg2.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            database='postgres'  # Connect to default postgres database
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        
        cursor = conn.cursor()
        
        # Check if database exists
        cursor.execute("SELECT 1 FROM pg_database WHERE datname = %s", (database,))
        exists = cursor.fetchone()
        
        if not exists:
            # Create database
            cursor.execute(f'CREATE DATABASE "{database}"')
            print(f"✅ Created database: {database}")
        else:
            print(f"✅ Database already exists: {database}")
        
        cursor.close()
        conn.close()
        return True
        
    except ImportError:
        print("❌ psycopg2 not available. Please install it first.")
        return False
    except Exception as e:
        print(f"❌ Failed to create database: {e}")
        return False

def initialize_schema():
    """Initialize database schema with tables and indexes."""
    try:
        # Add current directory to path
        sys.path.insert(0, str(Path(__file__).parent.parent))
        
        from database import initialize_database, initialize_database_schema
        
        print("🔄 Initializing database connection...")
        if not initialize_database():
            print("❌ Failed to initialize database connection")
            return False
        
        print("🏗️ Creating database schema...")
        if not initialize_database_schema():
            print("❌ Failed to create database schema")
            return False
        
        print("✅ Database schema initialized successfully")
        return True
        
    except ImportError as e:
        print(f"❌ Database modules not available: {e}")
        return False
    except Exception as e:
        print(f"❌ Schema initialization failed: {e}")
        return False

def test_connection():
    """Test database connection."""
    try:
        sys.path.insert(0, str(Path(__file__).parent.parent))
        from database import database_health_check
        
        print("🔍 Testing database connection...")
        health = database_health_check()
        
        if health.get('connected'):
            print("✅ Database connection successful")
            print(f"📊 Response time: {health.get('response_time_ms', 'N/A')} ms")
            return True
        else:
            print("❌ Database connection failed")
            if health.get('errors'):
                for error in health['errors']:
                    print(f"   ❌ {error}")
            return False
            
    except Exception as e:
        print(f"❌ Connection test failed: {e}")
        return False

def quick_setup():
    """Run complete quick setup."""
    print("🚀 Resume Customizer - Quick Database Setup")
    print("=" * 50)
    
    # Step 1: Check if .env exists
    if not Path('.env').exists():
        print("\n1️⃣ Creating environment configuration...")
        if not create_env_file():
            return False
        print("⚠️ Please edit .env file with your PostgreSQL credentials before continuing")
        return False
    
    # Step 2: Load environment variables
    try:
        from dotenv import load_dotenv
        load_dotenv()
        print("✅ Environment variables loaded")
    except ImportError:
        print("⚠️ python-dotenv not available, using system environment variables")
    
    # Step 3: Install dependencies
    print("\n2️⃣ Checking dependencies...")
    try:
        import psycopg2
        import sqlalchemy
        print("✅ PostgreSQL dependencies available")
    except ImportError:
        print("📦 Installing PostgreSQL dependencies...")
        if not install_dependencies():
            return False
    
    # Step 4: Create database
    print("\n3️⃣ Creating database...")
    if not create_database():
        return False
    
    # Step 5: Initialize schema
    print("\n4️⃣ Initializing schema...")
    if not initialize_schema():
        return False
    
    # Step 6: Test connection
    print("\n5️⃣ Testing connection...")
    if not test_connection():
        return False
    
    print("\n🎉 Quick setup completed successfully!")
    print("🚀 Your Resume Customizer is now ready with PostgreSQL database!")
    print("\n📋 Next steps:")
    print("  1. Run: streamlit run app.py")
    print("  2. Navigate to the Requirements tab")
    print("  3. Start creating and managing requirements")
    
    return True

if __name__ == "__main__":
    try:
        success = quick_setup()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⏹️ Setup interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)