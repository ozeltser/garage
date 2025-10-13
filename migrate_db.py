#!/usr/bin/env python3
"""
Database migration script for adding user profile fields.
This script adds first_name, last_name, email, and phone columns to the users table.
"""
import os
import sys
from dotenv import load_dotenv
from database import DatabaseManager
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def check_column_exists(cursor, table_name, column_name):
    """Check if a column exists in a table."""
    cursor.execute("""
        SELECT COUNT(*) as count
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = DATABASE()
        AND TABLE_NAME = %s
        AND COLUMN_NAME = %s
    """, (table_name, column_name))
    result = cursor.fetchone()
    return result['count'] > 0


def migrate_database():
    """Migrate the database to add user profile fields."""
    print("=" * 60)
    print("Database Migration: Adding User Profile Fields")
    print("=" * 60)
    
    # Load environment variables
    load_dotenv()
    
    # Check if required environment variables are set
    required_vars = ['DB_HOST', 'DB_USER', 'DB_PASSWORD', 'DB_NAME']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print("\nERROR: Missing required environment variables:")
        for var in missing_vars:
            print(f"  - {var}")
        print("\nPlease ensure your .env file is configured with database settings.")
        sys.exit(1)
    
    try:
        # Initialize database manager
        print("\nConnecting to MySQL database...")
        db_manager = DatabaseManager()
        print("✓ Database connection successful")
        
        with db_manager.get_connection() as connection:
            with connection.cursor() as cursor:
                print("\nChecking current schema...")
                
                # Check which columns need to be added
                columns_to_add = []
                column_definitions = {
                    'first_name': 'VARCHAR(255)',
                    'last_name': 'VARCHAR(255)',
                    'email': 'VARCHAR(255)',
                    'phone': 'VARCHAR(50)'
                }
                
                for column_name, column_type in column_definitions.items():
                    if not check_column_exists(cursor, 'users', column_name):
                        columns_to_add.append((column_name, column_type))
                        print(f"  - Column '{column_name}' is missing")
                    else:
                        print(f"  ✓ Column '{column_name}' already exists")
                
                if not columns_to_add:
                    print("\n✓ Database schema is already up to date!")
                    print("  No migration needed.")
                    return
                
                # Perform migration
                print(f"\nMigrating database - adding {len(columns_to_add)} column(s)...")
                
                for column_name, column_type in columns_to_add:
                    print(f"  Adding column '{column_name}' ({column_type})...")
                    # Validate column name to prevent SQL injection
                    if not column_name.replace('_', '').isalnum():
                        raise ValueError(f"Invalid column name: {column_name}")
                    if column_name not in column_definitions:
                        raise ValueError(f"Unknown column: {column_name}")
                    # Use string formatting only with validated whitelist values
                    cursor.execute(f"""
                        ALTER TABLE users
                        ADD COLUMN {column_name} {column_type} AFTER password_hash
                    """)
                    print(f"  ✓ Column '{column_name}' added successfully")
                
                print("\n" + "=" * 60)
                print("Migration completed successfully!")
                print("=" * 60)
                print("\nSummary:")
                print(f"  - Added {len(columns_to_add)} new column(s) to 'users' table")
                print("  - Existing user data preserved")
                print("  - New columns are nullable (NULL by default)")
                print("\nUsers can now update their profile information through the /profile page.")
                
    except Exception as e:
        print(f"\nERROR: Migration failed: {str(e)}")
        logger.error(f"Migration error: {str(e)}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    migrate_database()
