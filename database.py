import mysql.connector
from mysql.connector import Error, pooling
import os
from dotenv import load_dotenv
import threading

load_dotenv()

class DatabaseManager:
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        """Singleton pattern to ensure only one instance of DatabaseManager"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(DatabaseManager, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        # Only initialize once
        if hasattr(self, 'initialized'):
            return
            
        self.host = os.getenv('DB_HOST')
        self.user = os.getenv('DB_USER')
        self.password = os.getenv('DB_PASSWORD')
        self.database = os.getenv('DB_NAME')
        self.port = int(os.getenv('DB_PORT', 3306))
        
        # Connection pool configuration
        self.pool_name = "garage_pool"
        self.pool_size = int(os.getenv('DB_POOL_SIZE', 5))
        self.pool_reset_session = True
        
        # Initialize connection pool
        self._initialize_pool()
        self.initialized = True
    
    def _initialize_pool(self):
        """Initialize the MySQL connection pool"""
        try:
            pool_config = {
                'pool_name': self.pool_name,
                'pool_size': self.pool_size,
                'pool_reset_session': self.pool_reset_session,
                'host': self.host,
                'user': self.user,
                'password': self.password,
                'database': self.database,
                'port': self.port,
                'ssl_disabled': False,
                'ssl_verify_cert': True,
                'autocommit': True,
                'charset': 'utf8mb4',
                'collation': 'utf8mb4_unicode_ci'
            }
            
            self.connection_pool = pooling.MySQLConnectionPool(**pool_config)
            print(f"Connection pool '{self.pool_name}' initialized with {self.pool_size} connections")
            
        except Error as e:
            print(f"Error creating connection pool: {e}")
            self.connection_pool = None
    
    def get_connection(self):
        """Get a connection from the pool"""
        try:
            if self.connection_pool:
                connection = self.connection_pool.get_connection()
                return connection
            else:
                # Fallback to direct connection if pool fails
                print("Warning: Using direct connection (pool not available)")
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
            print(f"Error getting connection: {e}")
            return None
    
    def get_pool_info(self):
        """Get information about the connection pool"""
        if self.connection_pool:
            try:
                return {
                    'pool_name': self.connection_pool.pool_name,
                    'pool_size': self.connection_pool.pool_size,
                    'connections_in_use': len([conn for conn in self.connection_pool._cnx_queue._queue if conn.is_connected()]),
                    'total_connections': self.connection_pool.pool_size
                }
            except:
                return {'error': 'Unable to get pool information'}
        return {'error': 'Connection pool not available'}
    
    def close_pool(self):
        """Close all connections in the pool"""
        if hasattr(self, 'connection_pool') and self.connection_pool:
            try:
                # Close all connections in the pool
                while True:
                    try:
                        conn = self.connection_pool.get_connection()
                        conn.close()
                    except:
                        break
                print("Connection pool closed")
            except Exception as e:
                print(f"Error closing connection pool: {e}")
    
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
