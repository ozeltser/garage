"""
Database migration script for adding the api_key column to the users table.
"""
import os
import sys
import pymysql
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def get_connection_params():
    """Get secure MySQL connection parameters from environment variables."""
    params = {
        'host': os.getenv('DB_HOST', 'localhost'),
        'port': int(os.getenv('DB_PORT', 3306)),
        'user': os.getenv('DB_USER'),
        'password': os.getenv('DB_PASSWORD'),
        'database': os.getenv('DB_NAME'),
        'charset': 'utf8mb4',
        'cursorclass': pymysql.cursors.DictCursor
    }
    
    ssl_ca = os.getenv('DB_SSL_CA')
    if ssl_ca:
        params['ssl'] = {'ca': ssl_ca}
    
    required = ['user', 'password', 'database']
    if any(not params.get(p) for p in required):
        print("❌ Missing required database configuration in .env file.")
        sys.exit(1)
        
    return params

def check_and_add_column(cursor, table, column, definition):
    """Check if a column exists and add it if it doesn't."""
    try:
        cursor.execute(f"SELECT `{column}` FROM `{table}` LIMIT 1;")
        print(f"  - Column '{column}' already exists.")
        return False
    except pymysql.err.OperationalError as e:
        if e.args[0] == 1054: # Unknown column
            print(f"  - Column '{column}' is missing.")
            print(f"  Adding column '{column}' ({definition})...")
            cursor.execute(f"ALTER TABLE `{table}` ADD COLUMN `{column}` {definition};")
            print(f"  ✓ Column '{column}' added successfully.")
            return True
        else:
            raise

def main():
    """Main migration function."""
    print("============================================================")
    print("Database Migration: Adding API Key Support")
    print("============================================================")
    
    try:
        connection_params = get_connection_params()
        connection = pymysql.connect(**connection_params)
        print("\nConnecting to MySQL database...")
        print("✓ Database connection successful")
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        sys.exit(1)

    added_columns = 0
    
    try:
        with connection.cursor() as cursor:
            print("\nChecking current schema...")
            
            if check_and_add_column(cursor, 'users', 'api_key_hash', 'VARCHAR(255) UNIQUE AFTER is_active'):
                added_columns += 1
        
        connection.commit()

    except Exception as e:
        connection.rollback()
        print(f"\n❌ An error occurred during migration: {e}")
        sys.exit(1)
    finally:
        connection.close()

    print("\n============================================================")
    if added_columns > 0:
        print("Migration completed successfully!")
    else:
        print("No migration needed. Database is already up to date.")
    print("============================================================")

    if added_columns > 0:
        print("\nSummary:")
        print(f"  - Added {added_columns} new column(s) to 'users' table.")
        print("  - Existing user data preserved.")
        print("\nUsers can now generate API keys from their profile page.")

if __name__ == "__main__":
    main()
