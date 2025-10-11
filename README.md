# Garage Web App

A Python Flask web application that provides a secure login interface and allows authenticated users to execute Python scripts on the server. The application is designed to be responsive and work well on both mobile and desktop browsers.

## Features

- 🔐 **Secure Authentication**: User login system with session management
- 📱 **Responsive Design**: Optimized for both mobile and desktop browsers
- 🖥️ **Script Execution**: Execute Python scripts on the server with a simple button click
- 🎨 **Modern UI**: Clean, Bootstrap-based interface with smooth animations
- ⚡ **Real-time Feedback**: AJAX-based script execution with loading indicators
- 📊 **Output Display**: View script output and errors in real-time

## Quick Start

### Prerequisites

- Python 3.7 or higher
- pip (Python package installer)

### Installation

1. Clone this repository:
   ```bash
   git clone <repository-url>
   cd garage
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run the application:
   ```bash
   python app.py
   ```

4. Open your browser and navigate to:
   ```
   http://localhost:5000
   ```

# Garage Web App

A Python Flask web application that provides secure MySQL-based authentication and allows authenticated users to execute Python scripts on the server. The application is designed to be responsive and work well on both mobile and desktop browsers.

## Features

- 🔐 **Secure MySQL Authentication**: Database-backed user login system with encrypted password storage
- 📱 **Responsive Design**: Optimized for both mobile and desktop browsers
- 🖥️ **Script Execution**: Execute Python scripts on the server with a simple button click
- 🎨 **Modern UI**: Clean, Bootstrap-based interface with smooth animations
- ⚡ **Real-time Feedback**: AJAX-based script execution with loading indicators
- 📊 **Output Display**: View script output and errors in real-time
- 🔒 **Environment-based Configuration**: Secure configuration using environment variables
- 🛡️ **SSL Support**: Optional SSL/TLS connection to MySQL database
- 🔄 **Connection Pooling**: Efficient database connection pooling for improved performance and resource management

## Prerequisites

- Python 3.7 or higher
- pip (Python package installer)
- MySQL 5.7+ or MariaDB 10.2+

## Installation

### 1. Clone the repository
```bash
git clone <repository-url>
cd garage
```

### 2. Install Python dependencies
```bash
pip install -r requirements.txt
```

### 3. Set up MySQL Database

#### Create Database and User
Connect to your MySQL server and run:
```sql
-- Create database
CREATE DATABASE garage_app CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- Create user with limited privileges
CREATE USER 'garage_user'@'localhost' IDENTIFIED BY 'your-secure-password';

-- Grant necessary privileges
GRANT SELECT, INSERT, UPDATE, DELETE ON garage_app.* TO 'garage_user'@'localhost';
FLUSH PRIVILEGES;
```

#### For SSL connections (recommended for production):
```sql
-- Create user with SSL requirement
CREATE USER 'garage_user'@'%' IDENTIFIED BY 'your-secure-password' REQUIRE SSL;
GRANT SELECT, INSERT, UPDATE, DELETE ON garage_app.* TO 'garage_user'@'%';
FLUSH PRIVILEGES;
```

### 4. Configure Environment Variables

Copy the example environment file and customize it:
```bash
cp .env.example .env
```

Edit `.env` with your database configuration:
```bash
# Flask configuration
SECRET_KEY=your-unique-secret-key-generate-a-strong-one

# MySQL Database Configuration
DB_HOST=localhost
DB_PORT=3306
DB_NAME=garage_app
DB_USER=garage_user
DB_PASSWORD=your-secure-database-password

# For SSL connections (optional but recommended)
DB_SSL_CA=/path/to/ca-cert.pem
DB_SSL_CERT=/path/to/client-cert.pem
DB_SSL_KEY=/path/to/client-key.pem

# Database Connection Pool Settings (optional)
# Minimum number of idle connections to keep in pool
DB_POOL_MIN_SIZE=1
# Maximum number of connections in pool
DB_POOL_MAX_SIZE=10
# Maximum idle time for connections in seconds (default: 300 = 5 minutes)
DB_POOL_MAX_IDLE=300
# Maximum number of times a connection can be reused (0 = unlimited)
DB_POOL_MAX_USAGE=0

# Initial admin user (used for first-time setup)
DEFAULT_USERNAME=admin
DEFAULT_PASSWORD=your-secure-admin-password
```

**Important Security Notes:**
- Generate a strong, unique `SECRET_KEY` for production
- Use strong passwords for both database and admin user
- Never commit the `.env` file to version control
- Consider using SSL connections for production deployments

### 5. Initialize the Database

Run the database initialization script to set up tables and create the initial admin user:
```bash
python init_db.py
```

This script will:
- Create the necessary database tables
- Set up the initial admin user with credentials from your `.env` file
- Verify database connectivity

**For existing installations**: If you're upgrading from a previous version, see the [Database Migration Guide](MIGRATION.md) for instructions on migrating your existing database schema.

### 6. Run the Application

```bash
python app.py
```

The application will start on `http://localhost:5000` (or the host/port specified in your `.env` file).

## User Management

### Initial Admin Login
After running `init_db.py`, you can log in with:
- **Username**: Value of `DEFAULT_USERNAME` from your `.env` file (default: `admin`)
- **Password**: Value of `DEFAULT_PASSWORD` from your `.env` file

### User Profile Management
Users can manage their profile information by clicking the "Profile" link in the dashboard:
- Update first name and last name
- Update email address
- Update phone number
- Change password (requires current password verification)

All profile fields are optional and can be updated independently.

### Adding New Users
Currently, new users must be added directly to the database. You can use the database manager:

```python
from database import DatabaseManager
from dotenv import load_dotenv

load_dotenv()
db_manager = DatabaseManager()

# Create a new user
db_manager.create_user('newuser', 'secure-password')
```

### Password Management
To update a user's password:
```python
# Update password
db_manager.update_password('username', 'new-secure-password')
```

## Project Structure

```
garage/
├── app.py                 # Main Flask application with MySQL authentication
├── database.py            # Database manager for secure MySQL operations
├── init_db.py            # Database initialization script
├── migrate_db.py         # Database migration script for schema updates
├── requirements.txt       # Python dependencies
├── relay.py              # Example Python script to execute
├── .env.example          # Environment variables template
├── .gitignore           # Git ignore file (excludes .env)
├── MIGRATION.md          # Database migration guide
├── templates/
│   ├── base.html         # Base template with common layout
│   ├── login.html        # Login page template
│   ├── dashboard.html    # Dashboard template
│   └── profile.html      # User profile page template
└── static/
    ├── css/
    │   └── style.css     # Custom styles for responsive design
    └── js/
        └── app.js        # JavaScript for AJAX and interactions
```

## Configuration

### Security Features
- ✅ **MySQL Database Authentication**: No more hardcoded passwords
- ✅ **Environment Variable Configuration**: Secrets stored securely outside code
- ✅ **Password Hashing**: Uses Werkzeug's secure password hashing
- ✅ **Optional SSL/TLS**: Secure database connections
- ✅ **Logging**: Security events and errors are logged
- ✅ **Input Validation**: Database queries use parameterized statements

### Environment Variables
All sensitive configuration is managed through environment variables in `.env`:

| Variable | Description | Required |
|----------|-------------|----------|
| `SECRET_KEY` | Flask secret key for sessions | Yes |
| `DB_HOST` | MySQL server hostname | Yes |
| `DB_PORT` | MySQL server port | No (default: 3306) |
| `DB_NAME` | Database name | Yes |
| `DB_USER` | Database username | Yes |
| `DB_PASSWORD` | Database password | Yes |
| `DB_SSL_CA` | SSL CA certificate path | No |
| `DB_SSL_CERT` | SSL client certificate path | No |
| `DB_SSL_KEY` | SSL client key path | No |
| `DB_POOL_MIN_SIZE` | Minimum connections in pool | No (default: 1) |
| `DB_POOL_MAX_SIZE` | Maximum connections in pool | No (default: 10) |
| `DB_POOL_MAX_IDLE` | Max idle time for connections (seconds) | No (default: 300) |
| `DB_POOL_MAX_USAGE` | Max times connection can be reused | No (default: 0=unlimited) |
| `DEFAULT_USERNAME` | Initial admin username | No (default: admin) |
| `DEFAULT_PASSWORD` | Initial admin password | No (default: admin) |

### Script Customization
- Edit `relay.py` to customize what runs when the button is clicked
- The script output (stdout) and errors (stderr) are displayed in the web interface
- Scripts have a 30-second timeout limit

## Technology Stack

- **Backend**: Flask (Python web framework)
- **Database**: MySQL/MariaDB with PyMySQL driver and DBUtils connection pooling
- **Frontend**: HTML5, CSS3, JavaScript, Bootstrap 5
- **Authentication**: Flask-Login with MySQL backend
- **Security**: Werkzeug password hashing, SSL/TLS support
- **Configuration**: python-dotenv for environment management

## API Endpoints

- `GET /`: Home page (redirects to login if not authenticated)
- `GET /login`: Login page
- `POST /login`: Process login credentials against MySQL database
- `GET /logout`: Logout and redirect to login
- `GET /profile`: User profile page (requires authentication)
- `POST /profile`: Update user profile and password (requires authentication)
- `POST /run_script`: Execute the Python script (requires authentication)

## Development

### Running in Development Mode
Set `FLASK_DEBUG=True` in your `.env` file for development features:
- Automatic reload on code changes
- Detailed error pages
- Debug logging

For production, set `FLASK_DEBUG=False`.

### Adding New Users
Use the database manager to add users programmatically:
```python
from database import DatabaseManager
from dotenv import load_dotenv

load_dotenv()
db_manager = DatabaseManager()
db_manager.create_user('newuser', 'secure-password')
```

### Database Management
The `database.py` module provides secure methods for:
- User creation and authentication
- Password updates
- User account management
- Secure database connections

## Security Considerations

### Production Deployment Checklist
- ✅ **Use HTTPS**: Deploy behind a reverse proxy with SSL/TLS
- ✅ **Strong Passwords**: Generate secure passwords for all accounts
- ✅ **SSL Database Connections**: Enable SSL/TLS for database connections
- ✅ **Environment Variables**: Never commit `.env` files to version control
- ✅ **Database Security**: Use dedicated database user with minimal privileges
- ✅ **Network Security**: Restrict database access to application servers only
- ✅ **Regular Updates**: Keep dependencies updated
- ✅ **Monitoring**: Monitor logs for security events

### Additional Security Measures
Consider implementing for production:
- CSRF protection
- Rate limiting for login attempts
- Two-factor authentication
- Session timeout
- Regular security audits
- Database backups and encryption at rest

## Troubleshooting

### Database Connection Issues
1. Verify MySQL server is running and accessible
2. Check database credentials in `.env` file
3. Ensure database and user exist with proper permissions
4. Check network connectivity and firewall settings
5. Review application logs for detailed error messages

### SSL Connection Issues
1. Verify SSL certificate paths are correct
2. Ensure certificates have proper permissions
3. Check MySQL server SSL configuration
4. Test SSL connection with MySQL client

## License

This project is open source and available under the MIT License.