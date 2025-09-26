import mysql.connector
from mysql.connector import Error
import os
from dotenv import load_dotenv

load_dotenv()

class DatabaseManager:
    def __init__(self):
        self.host = os.getenv('DB_HOST')
        self.user = os.getenv('DB_USER')
        self.password = os.getenv('DB_PASSWORD')
        self.database = os.getenv('DB_NAME')
        self.port = int(os.getenv('DB_PORT', 3306))
        
    def get_connection(self):
        """Create and return a database connection"""
        try:
            connection = mysql.connector.connect(
                host=self.host,
                user=self.user,
                password=self.password,
                database=self.database,
                port=self.port,
                ssl_disabled=False,
                ssl_verify_cert=True,
                autocommit=True
            )
            return connection
        except Error as e:
            print(f"Error connecting to MySQL: {e}")
            return None
    
    def create_users_table(self):
        """Create the users table if it doesn't exist"""
        connection = self.get_connection()
        if connection:
            try:
                cursor = connection.cursor()
                create_table_query = """
                CREATE TABLE IF NOT EXISTS users (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    username VARCHAR(50) UNIQUE NOT NULL,
                    password_hash VARCHAR(255) NOT NULL,
                    email VARCHAR(100),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_active BOOLEAN DEFAULT TRUE
                )
                """
                cursor.execute(create_table_query)
                print("Users table created successfully")
                cursor.close()
            except Error as e:
                print(f"Error creating users table: {e}")
            finally:
                connection.close()
    
    def create_user(self, username, password_hash, email=None):
        """Create a new user in the database"""
        connection = self.get_connection()
        if connection:
            try:
                cursor = connection.cursor()
                insert_query = """
                INSERT INTO users (username, password_hash, email)
                VALUES (%s, %s, %s)
                """
                cursor.execute(insert_query, (username, password_hash, email))
                print(f"User {username} created successfully")
                cursor.close()
                return True
            except Error as e:
                print(f"Error creating user: {e}")
                return False
            finally:
                connection.close()
        return False
    
    def get_user(self, username):
        """Get user by username"""
        connection = self.get_connection()
        if connection:
            try:
                cursor = connection.cursor(dictionary=True)
                select_query = "SELECT * FROM users WHERE username = %s AND is_active = TRUE"
                cursor.execute(select_query, (username,))
                user = cursor.fetchone()
                cursor.close()
                return user
            except Error as e:
                print(f"Error fetching user: {e}")
                return None
            finally:
                connection.close()
        return None
    
    def update_user_password(self, username, new_password_hash):
        """Update user password"""
        connection = self.get_connection()
        if connection:
            try:
                cursor = connection.cursor()
                update_query = "UPDATE users SET password_hash = %s WHERE username = %s"
                cursor.execute(update_query, (new_password_hash, username))
                cursor.close()
                return True
            except Error as e:
                print(f"Error updating password: {e}")
                return False
            finally:
                connection.close()
        return False
    
    def deactivate_user(self, username):
        """Deactivate a user (soft delete)"""
        connection = self.get_connection()
        if connection:
            try:
                cursor = connection.cursor()
                update_query = "UPDATE users SET is_active = FALSE WHERE username = %s"
                cursor.execute(update_query, (username,))
                cursor.close()
                return True
            except Error as e:
                print(f"Error deactivating user: {e}")
                return False
            finally:
                connection.close()
        return False
