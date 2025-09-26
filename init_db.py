#!/usr/bin/env python3
"""
Database initialization script for the garage application.
Run this script to set up the MySQL database and create the default admin user.
"""

from database import DatabaseManager
from werkzeug.security import generate_password_hash
from dotenv import load_dotenv
import os
import sys

# Load environment variables
load_dotenv()

def main():
    print("Initializing garage application database...")
    
    # Initialize database manager
    db_manager = DatabaseManager()
    
    try:
        # Create users table
        print("Creating users table...")
        db_manager.create_users_table()
        
        # Get admin credentials from environment variables
        admin_username = os.getenv('ADMIN_USERNAME', 'admin')
        admin_password = os.getenv('ADMIN_PASSWORD')
        admin_email = os.getenv('ADMIN_EMAIL', 'admin@garage.com')
        
        if not admin_password:
            print("✗ ADMIN_PASSWORD not found in environment variables!")
            print("Please set ADMIN_PASSWORD in your .env file")
            sys.exit(1)
        
        # Check if admin user exists
        admin_user = db_manager.get_user(admin_username)
        if not admin_user:
            print("Creating default admin user...")
            admin_password_hash = generate_password_hash(admin_password)
            success = db_manager.create_user(admin_username, admin_password_hash, admin_email)
            if success:
                print("✓ Admin user created successfully!")
                print(f"  Username: {admin_username}")
                print(f"  Email: {admin_email}")
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
        print("\nPlease check your configuration in the .env file:")
        print("Database configuration:")
        print("- DB_HOST: Your Azure MySQL server hostname")
        print("- DB_USER: Your MySQL username")
        print("- DB_PASSWORD: Your MySQL password")
        print("- DB_NAME: Your database name")
        print("- DB_PORT: MySQL port (usually 3306)")
        print("\nAdmin user configuration:")
        print("- ADMIN_USERNAME: Admin username (default: admin)")
        print("- ADMIN_PASSWORD: Secure password for admin user")
        print("- ADMIN_EMAIL: Admin email address")
        sys.exit(1)

if __name__ == "__main__":
    main()
