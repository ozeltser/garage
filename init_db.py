#!/usr/bin/env python3
"""
Database initialization script for Garage Web App.
This script helps set up the MySQL database and create an initial admin user.
"""
import os
import sys
import getpass
from dotenv import load_dotenv
from database import DatabaseManager

def main():
    """Initialize database and create admin user."""
    print("Garage Web App - Database Initialization")
    print("=" * 40)
    
    # Load environment variables
    load_dotenv()
    
    # Check if required environment variables are set
    required_vars = ['DB_HOST', 'DB_USER', 'DB_PASSWORD', 'DB_NAME']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print("ERROR: Missing required environment variables:")
        for var in missing_vars:
            print(f"  - {var}")
        print("\nPlease copy .env.example to .env and configure your database settings.")
        sys.exit(1)
    
    try:
        # Initialize database manager
        print("Connecting to MySQL database...")
        db_manager = DatabaseManager()
        print("✓ Database connection successful")
        print("✓ Users table created/verified")
        
        # Check if admin user already exists
        admin_username = os.getenv('DEFAULT_USERNAME', 'admin')
        existing_user = db_manager.get_user_by_username(admin_username)
        
        if existing_user:
            print(f"✓ Admin user '{admin_username}' already exists")
            
            # Offer to update password
            update_password = input(f"Would you like to update the password for '{admin_username}'? (y/N): ").lower()
            if update_password == 'y':
                new_password = getpass.getpass("Enter new password: ")
                confirm_password = getpass.getpass("Confirm new password: ")
                
                if new_password != confirm_password:
                    print("ERROR: Passwords do not match")
                    sys.exit(1)
                
                if db_manager.update_password(admin_username, new_password):
                    print(f"✓ Password updated for user '{admin_username}'")
                else:
                    print("ERROR: Failed to update password")
                    sys.exit(1)
        else:
            print(f"✓ Initial admin user '{admin_username}' created with default password")
            print(f"  Note: Default password was set from DEFAULT_PASSWORD environment variable")
        
        print("\nDatabase initialization completed successfully!")
        print(f"You can now log in to the application with username: {admin_username}")
        
    except Exception as e:
        print(f"ERROR: Database initialization failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()