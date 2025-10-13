#!/usr/bin/env python3
"""
Database Migration: Add role column to users table for RBAC
"""
import os
import sys
import pymysql
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def get_connection():
    """Get database connection."""
    return pymysql.connect(
        host=os.getenv('DB_HOST', 'localhost'),
        port=int(os.getenv('DB_PORT', 3306)),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD'),
        database=os.getenv('DB_NAME'),
        charset='utf8mb4',
        autocommit=True,
        cursorclass=pymysql.cursors.DictCursor
    )

def main():
    print("=" * 60)
    print("Database Migration: Adding RBAC Role Column")
    print("=" * 60)
    print()
    
    try:
        print("Connecting to MySQL database...")
        with get_connection() as connection:
            with connection.cursor() as cursor:
                print("✓ Database connection successful")
                print()
                
                # Check if role column exists
                cursor.execute("DESCRIBE users")
                columns = cursor.fetchall()
                column_names = [col['Field'] for col in columns]
                
                if 'role' in column_names:
                    print("✓ Role column already exists")
                    print()
                    
                    # Check if admin user exists and set role
                    cursor.execute("SELECT username, role FROM users WHERE username = 'admin' OR username = %s", 
                                 (os.getenv('DEFAULT_USERNAME', 'admin'),))
                    admin_user = cursor.fetchone()
                    
                    if admin_user and admin_user['role'] != 'admin':
                        print(f"Updating admin user '{admin_user['username']}' role to 'admin'...")
                        cursor.execute("UPDATE users SET role = 'admin' WHERE username = %s", 
                                     (admin_user['username'],))
                        print(f"✓ Admin user role updated")
                    elif admin_user:
                        print(f"✓ Admin user '{admin_user['username']}' already has admin role")
                    
                    print()
                    print("=" * 60)
                    print("Migration check completed - no changes needed!")
                    print("=" * 60)
                else:
                    print("Adding role column to users table...")
                    cursor.execute("""
                        ALTER TABLE users 
                        ADD COLUMN role VARCHAR(50) NOT NULL DEFAULT 'regular'
                        AFTER password_hash
                    """)
                    print("✓ Role column added successfully")
                    print()
                    
                    # Set the first admin user to have admin role
                    admin_username = os.getenv('DEFAULT_USERNAME', 'admin')
                    cursor.execute("UPDATE users SET role = 'admin' WHERE username = %s", (admin_username,))
                    print(f"✓ Admin user '{admin_username}' role set to 'admin'")
                    print()
                    
                    print("=" * 60)
                    print("Migration completed successfully!")
                    print("=" * 60)
                    print()
                    print("Summary:")
                    print("  - Added 'role' column to 'users' table")
                    print("  - Set default role to 'regular' for new users")
                    print(f"  - Set admin role for user '{admin_username}'")
                    print()
                
    except Exception as e:
        print(f"✗ Migration failed: {str(e)}")
        sys.exit(1)

if __name__ == '__main__':
    main()
