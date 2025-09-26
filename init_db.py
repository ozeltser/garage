#!/usr/bin/env python3
"""
Database initialization script for the garage application.
Run this script to set up the MySQL database and create the default admin user.
"""

from database import DatabaseManager
from werkzeug.security import generate_password_hash
import sys

def main():
    print("Initializing garage application database...")
    
    # Initialize database manager
    db_manager = DatabaseManager()
    
    try:
        # Create users table
        print("Creating users table...")
        db_manager.create_users_table()
        
        # Check if admin user exists
        admin_user = db_manager.get_user('admin')
        if not admin_user:
            print("Creating default admin user...")
            admin_password_hash = generate_password_hash('mypassword')
            success = db_manager.create_user('admin', admin_password_hash, 'admin@garage.com')
            if success:
                print("✓ Admin user created successfully!")
                print("  Username: admin")
                print("  Password: mypassword")
                print("  Email: admin@garage.com")
                print("\n⚠️  IMPORTANT: Change the admin password after first login!")
            else:
                print("✗ Failed to create admin user")
                sys.exit(1)
        else:
            print("✓ Admin user already exists")
        
        print("\n✓ Database initialization completed successfully!")
        print("\nYou can now start the application with: python app.py")
        
    except Exception as e:
        print(f"✗ Error during database initialization: {e}")
        print("\nPlease check your database configuration in the .env file:")
        print("- DB_HOST: Your Azure MySQL server hostname")
        print("- DB_USER: Your MySQL username")
        print("- DB_PASSWORD: Your MySQL password")
        print("- DB_NAME: Your database name")
        print("- DB_PORT: MySQL port (usually 3306)")
        sys.exit(1)

if __name__ == "__main__":
    main()
