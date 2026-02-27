"""
Database module for secure MySQL connectivity and user management.
"""
import hashlib
import os
import pymysql
import logging
from typing import Optional, Dict, Any
from werkzeug.security import generate_password_hash, check_password_hash
from user_roles import UserRole
import secrets

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DatabaseManager:
    """Manages secure MySQL database connections and user operations."""
    
    def __init__(self):
        """Initialize database manager with secure connection parameters."""
        self.connection_params = self._get_connection_params()
        self._ensure_database_setup()
    
    def _get_connection_params(self) -> Dict[str, Any]:
        """Get secure MySQL connection parameters from environment variables."""
        params = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'port': int(os.getenv('DB_PORT', 3306)),
            'user': os.getenv('DB_USER'),
            'password': os.getenv('DB_PASSWORD'),
            'database': os.getenv('DB_NAME'),
            'charset': 'utf8mb4',
            'autocommit': True,
            'cursorclass': pymysql.cursors.DictCursor
        }
        
        # Add SSL configuration if provided
        ssl_ca = os.getenv('DB_SSL_CA')
        ssl_cert = os.getenv('DB_SSL_CERT') 
        ssl_key = os.getenv('DB_SSL_KEY')
        
        if ssl_ca:
            ssl_config = {'ca': ssl_ca}
            if ssl_cert:
                ssl_config['cert'] = ssl_cert
            if ssl_key:
                ssl_config['key'] = ssl_key
            params['ssl'] = ssl_config
        
        # Validate required parameters
        required_params = ['user', 'password', 'database']
        missing_params = [param for param in required_params if not params.get(param)]
        if missing_params:
            raise ValueError(f"Missing required database configuration: {', '.join(missing_params)}")
        
        return params
    
    def get_connection(self):
        """Get a secure database connection."""
        try:
            connection = pymysql.connect(**self.connection_params)
            logger.info("Database connection established successfully")
            return connection
        except Exception as e:
            logger.error(f"Failed to connect to database: {str(e)}")
            raise
    
    def _ensure_database_setup(self):
        """Ensure the users table exists with the latest schema and create initial admin user if needed."""
        try:
            with self.get_connection() as connection:
                with connection.cursor() as cursor:
                    # Create users table if it doesn't exist (full current schema for fresh installs)
                    cursor.execute(f"""
                        CREATE TABLE IF NOT EXISTS users (
                            id INT AUTO_INCREMENT PRIMARY KEY,
                            username VARCHAR(255) UNIQUE NOT NULL,
                            password_hash VARCHAR(255) NOT NULL,
                            role VARCHAR(50) NOT NULL DEFAULT '{UserRole.REGULAR.value}',
                            first_name VARCHAR(255),
                            last_name VARCHAR(255),
                            email VARCHAR(255),
                            phone VARCHAR(50),
                            sms_notifications_enabled BOOLEAN DEFAULT FALSE,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                            is_active BOOLEAN DEFAULT TRUE,
                            api_key_hash VARCHAR(255) UNIQUE
                        )
                    """)

                    # Bring existing tables up to the latest schema
                    self._apply_schema_migrations(cursor)

                    # Check if admin user exists
                    default_username = os.getenv('DEFAULT_USERNAME', 'admin')
                    cursor.execute("SELECT COUNT(*) as count FROM users WHERE username = %s", (default_username,))
                    result = cursor.fetchone()

                    if result['count'] == 0:
                        # Create initial admin user
                        default_password = os.getenv('DEFAULT_PASSWORD', 'admin')
                        password_hash = generate_password_hash(default_password)

                        cursor.execute(
                            "INSERT INTO users (username, password_hash, role) VALUES (%s, %s, %s)",
                            (default_username, password_hash, UserRole.ADMIN.value)
                        )
                        logger.info(f"Initial admin user '{default_username}' created successfully")

        except Exception as e:
            logger.error(f"Failed to setup database: {str(e)}")
            raise

    def _apply_schema_migrations(self, cursor):
        """Add any columns missing from existing tables to bring them to the latest schema."""
        # Ordered list of (column_name, ALTER TABLE SQL) matching the current CREATE TABLE definition
        migrations = [
            ('role', f"ALTER TABLE users ADD COLUMN role VARCHAR(50) NOT NULL DEFAULT '{UserRole.REGULAR.value}' AFTER password_hash"),
            ('first_name', "ALTER TABLE users ADD COLUMN first_name VARCHAR(255) AFTER role"),
            ('last_name', "ALTER TABLE users ADD COLUMN last_name VARCHAR(255) AFTER first_name"),
            ('email', "ALTER TABLE users ADD COLUMN email VARCHAR(255) AFTER last_name"),
            ('phone', "ALTER TABLE users ADD COLUMN phone VARCHAR(50) AFTER email"),
            ('sms_notifications_enabled', "ALTER TABLE users ADD COLUMN sms_notifications_enabled BOOLEAN DEFAULT FALSE AFTER phone"),
            ('created_at', "ALTER TABLE users ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP"),
            ('updated_at', "ALTER TABLE users ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"),
            ('is_active', "ALTER TABLE users ADD COLUMN is_active BOOLEAN DEFAULT TRUE"),
            ('api_key_hash', "ALTER TABLE users ADD COLUMN api_key_hash VARCHAR(255) UNIQUE"),
        ]

        for column_name, alter_sql in migrations:
            cursor.execute("""
                SELECT COUNT(*) as count FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'users' AND COLUMN_NAME = %s
            """, (column_name,))
            if cursor.fetchone()['count'] == 0:
                cursor.execute(alter_sql)
                logger.info(f"Schema migration applied: added column '{column_name}' to users table")

    def get_user_by_api_key(self, api_key: str) -> Optional[Dict[str, Any]]:
        """Retrieve user by API key from the database."""
        try:
            with self.get_connection() as connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        "SELECT id, username, role, is_active FROM users WHERE api_key_hash = %s AND is_active = TRUE",
                        (hashlib.sha256(api_key.encode()).hexdigest(),)
                    )
                    return cursor.fetchone()
        except Exception as e:
            logger.error(f"Failed to retrieve user by API key: {str(e)}")
            return None

    def generate_api_key(self, username: str) -> Optional[str]:
        """Generate and save a new API key for a user."""
        try:
            api_key = secrets.token_hex(32)
            api_key_hash = hashlib.sha256(api_key.encode()).hexdigest()
            with self.get_connection() as connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        "UPDATE users SET api_key_hash = %s WHERE username = %s AND is_active = TRUE",
                        (api_key_hash, username)
                    )
                    if cursor.rowcount > 0:
                        logger.info(f"Generated new API key for user '{username}'")
                        return api_key
                    else:
                        logger.warning(f"User '{username}' not found or inactive")
                        return None
        except Exception as e:
            logger.error(f"Failed to generate API key for user {username}: {str(e)}")
            return None

    def get_user_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """Retrieve user by username from the database."""
        try:
            with self.get_connection() as connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        "SELECT id, username, password_hash, role, first_name, last_name, email, phone, sms_notifications_enabled, is_active, api_key_hash FROM users WHERE username = %s AND is_active = TRUE",
                        (username,)
                    )
                    return cursor.fetchone()
        except Exception as e:
            logger.error(f"Failed to retrieve user {username}: {str(e)}")
            return None
    
    def verify_password(self, username: str, password: str) -> bool:
        """Verify user password against stored hash."""
        user = self.get_user_by_username(username)
        if not user:
            return False
        
        return check_password_hash(user['password_hash'], password)
    
    def create_user(self, username: str, password: str, role: str = None) -> bool:
        """Create a new user with hashed password."""
        if role is None:
            role = UserRole.REGULAR.value
        
        try:
            password_hash = generate_password_hash(password)
            with self.get_connection() as connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        "INSERT INTO users (username, password_hash, role) VALUES (%s, %s, %s)",
                        (username, password_hash, role)
                    )
                    logger.info(f"User '{username}' created successfully with role '{role}'")
                    return True
        except pymysql.IntegrityError:
            logger.warning(f"User '{username}' already exists")
            return False
        except Exception as e:
            logger.error(f"Failed to create user {username}: {str(e)}")
            return False
    
    def update_password(self, username: str, new_password: str) -> bool:
        """Update user password."""
        try:
            password_hash = generate_password_hash(new_password)
            with self.get_connection() as connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        "UPDATE users SET password_hash = %s, updated_at = CURRENT_TIMESTAMP WHERE username = %s AND is_active = TRUE",
                        (password_hash, username)
                    )
                    if cursor.rowcount > 0:
                        logger.info(f"Password updated for user '{username}'")
                        return True
                    else:
                        logger.warning(f"User '{username}' not found or inactive")
                        return False
        except Exception as e:
            logger.error(f"Failed to update password for user {username}: {str(e)}")
            return False
    
    def update_user_profile(self, username: str, first_name: str = None, last_name: str = None, 
                           email: str = None, phone: str = None, sms_notifications_enabled: bool = False) -> bool:
        """Update user profile information."""
        try:
            with self.get_connection() as connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        """UPDATE users SET 
                           first_name = %s, 
                           last_name = %s, 
                           email = %s, 
                           phone = %s, 
                           sms_notifications_enabled = %s,
                           updated_at = CURRENT_TIMESTAMP 
                           WHERE username = %s AND is_active = TRUE""",
                        (first_name, last_name, email, phone, sms_notifications_enabled, username)
                    )
                    if cursor.rowcount > 0:
                        logger.info(f"Profile updated for user '{username}'")
                        return True
                    else:
                        logger.warning(f"User '{username}' not found or inactive")
                        return False
        except Exception as e:
            logger.error(f"Failed to update profile for user {username}: {str(e)}")
            return False
    
    def deactivate_user(self, username: str) -> bool:
        """Deactivate a user account."""
        try:
            with self.get_connection() as connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        "UPDATE users SET is_active = FALSE, updated_at = CURRENT_TIMESTAMP WHERE username = %s",
                        (username,)
                    )
                    if cursor.rowcount > 0:
                        logger.info(f"User '{username}' deactivated")
                        return True
                    else:
                        logger.warning(f"User '{username}' not found")
                        return False
        except Exception as e:
            logger.error(f"Failed to deactivate user {username}: {str(e)}")
            return False
    
    def get_all_users(self) -> list:
        """Get all active users (admin function)."""
        try:
            with self.get_connection() as connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        "SELECT id, username, role, first_name, last_name, email, phone, sms_notifications_enabled, created_at FROM users WHERE is_active = TRUE ORDER BY created_at DESC"
                    )
                    return cursor.fetchall()
        except Exception as e:
            logger.error(f"Failed to retrieve all users: {str(e)}")
            return []
    
    def delete_user(self, username: str) -> bool:
        """Delete a user account (admin function)."""
        try:
            with self.get_connection() as connection:
                with connection.cursor() as cursor:
                    # Prevent deleting the last admin user
                    cursor.execute(f"SELECT COUNT(*) as count FROM users WHERE role = %s AND is_active = TRUE", (UserRole.ADMIN.value,))
                    admin_count = cursor.fetchone()['count']
                    
                    cursor.execute("SELECT role FROM users WHERE username = %s AND is_active = TRUE", (username,))
                    user = cursor.fetchone()
                    
                    if user and user['role'] == UserRole.ADMIN.value and admin_count <= 1:
                        logger.warning(f"Cannot delete the last admin user '{username}'")
                        return False
                    
                    cursor.execute(
                        "DELETE FROM users WHERE username = %s",
                        (username,)
                    )
                    if cursor.rowcount > 0:
                        logger.info(f"User '{username}' deleted")
                        return True
                    else:
                        logger.warning(f"User '{username}' not found")
                        return False
        except Exception as e:
            logger.error(f"Failed to delete user {username}: {str(e)}")
            return False
    
    def update_user_password_by_admin(self, username: str, new_password: str) -> bool:
        """Update user password by admin (admin function)."""
        try:
            password_hash = generate_password_hash(new_password)
            with self.get_connection() as connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        "UPDATE users SET password_hash = %s, updated_at = CURRENT_TIMESTAMP WHERE username = %s AND is_active = TRUE",
                        (password_hash, username)
                    )
                    if cursor.rowcount > 0:
                        logger.info(f"Password updated for user '{username}' by admin")
                        return True
                    else:
                        logger.warning(f"User '{username}' not found or inactive")
                        return False
        except Exception as e:
            logger.error(f"Failed to update password for user {username}: {str(e)}")
            return False