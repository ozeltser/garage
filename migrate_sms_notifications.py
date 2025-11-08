#!/usr/bin/env python3
"""
Database migration script for adding SMS notification opt-in field.
This script adds sms_notifications_enabled column to the users table.
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
    cursor.execute(f"""
        SELECT COUNT(*) as count
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = DATABASE()
        AND TABLE_NAME = %s
        AND COLUMN_NAME = %s
    """, (table_name, column_name))
    result = cursor.fetchone()
    return result['count'] > 0


def migrate_database():
    """Migrate the database to add SMS notification opt-in field."""
    print("=" * 60)
    print("Database Migration: Adding SMS Notification Opt-In")
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
                
                # Check if the column needs to be added
                column_name = 'sms_notifications_enabled'
                
                if check_column_exists(cursor, 'users', column_name):
                    print(f"  ✓ Column '{column_name}' already exists")
                    print("\n✓ Database schema is already up to date!")
                    print("  No migration needed.")
                    return
                
                print(f"  - Column '{column_name}' is missing")
                
                # Perform migration
                print(f"\nMigrating database - adding '{column_name}' column...")
                cursor.execute("""
                    ALTER TABLE users
                    ADD COLUMN sms_notifications_enabled BOOLEAN DEFAULT FALSE AFTER phone
                """)
                print(f"  ✓ Column '{column_name}' added successfully")
                
                print("\n" + "=" * 60)
                print("Migration completed successfully!")
                print("=" * 60)
                print("\nSummary:")
                print(f"  - Added 'sms_notifications_enabled' column to 'users' table")
                print("  - Default value is FALSE (notifications disabled by default)")
                print("  - Existing user data preserved")
                print("\nUsers can now opt-in for SMS notifications through the /profile page.")
                
    except Exception as e:
        print(f"\nERROR: Migration failed: {str(e)}")
        logger.error(f"Migration error: {str(e)}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    migrate_database()
