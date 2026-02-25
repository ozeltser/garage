# Garage Web App

A Python Flask web application for controlling a garage door via a Raspberry Pi with a Pimoroni Automation HAT. The app provides secure MySQL-backed authentication, role-based access control (RBAC), real-time door status monitoring over WebSocket, and a responsive UI that works well on both mobile and desktop browsers.

The hardware used is Raspberry Pi 3 and Pimoroni [Automation HAT for Raspberry Pi](https://www.adafruit.com/product/3289).

## Documentation

- **[QUICKSTART.md](QUICKSTART.md)** - Quick start guide for production deployment
- **[PRODUCTION.md](PRODUCTION.md)** - Complete production deployment guide for Raspberry Pi
- **[SECURITY.md](SECURITY.md)** - Security implementation details
- **[RBAC.md](RBAC.md)** - Complete RBAC documentation
- **[RBAC_QUICKSTART.md](RBAC_QUICKSTART.md)** - Quick guide for RBAC features
- **[RBAC_SUMMARY.md](RBAC_SUMMARY.md)** - RBAC summary
- **[RBAC_MATRIX.md](RBAC_MATRIX.md)** - RBAC permissions matrix
- **[MIGRATION.md](MIGRATION.md)** - Database migration guide
- **[DEPLOYMENT_SUMMARY.md](DEPLOYMENT_SUMMARY.md)** - Deployment documentation summary
- **[DEPLOYMENT_CHECKLIST.md](DEPLOYMENT_CHECKLIST.md)** - Pre-deployment checklist
- **[TROUBLESHOOTING.md](TROUBLESHOOTING.md)** - Quick reference for common issues
- **[network-examples/](network-examples/)** - Network configuration examples

## Features

- **Secure MySQL Authentication** - Database-backed user login with encrypted password storage
- **Role-Based Access Control (RBAC)** - Admin and Regular user roles with different permissions
- **Real-time Door Status** - Server-side scheduling with WebSocket (Socket.IO) push notifications
- **Admin Panel** - Create, delete users and manage passwords (Admin only)
- **User Profile Management** - Edit personal information, change passwords, generate API keys, toggle SMS notifications
- **REST API** - API key-authenticated endpoint for door status
- **Responsive Design** - Mobile-friendly Bootstrap 5 UI with dark/light theme toggle
- **Script Execution** - Execute the garage door relay script with real-time output display
- **Automation HAT Support** - Control relays and read sensors on Raspberry Pi
- **Environment-based Configuration** - Secure configuration using environment variables
- **SSL Support** - Optional SSL/TLS connections to MySQL database
- **Privacy & Terms Pages** - Built-in privacy policy and terms of service pages

## Quick Start (Development)

### Prerequisites

- Python 3.7 or higher
- pip (Python package installer)
- MySQL 5.7+ or MariaDB 10.2+

### Development Installation

1. Clone this repository:
   ```bash
   git clone https://github.com/ozeltser/garage.git
   cd garage
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Set up database and configure `.env` (see [Installation](#installation) section below)

4. Initialize database:
   ```bash
   python init_db.py
   ```

5. Run the application:
   ```bash
   python app.py
   ```

6. Open your browser and navigate to:
   ```
   http://localhost:5000
   ```

## Installation

### 1. Clone the repository
```bash
git clone https://github.com/ozeltser/garage.git
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

Edit `.env` with your configuration:
```bash
# Flask configuration
SECRET_KEY=your-unique-secret-key-generate-a-strong-one
FLASK_ENV=development
FLASK_DEBUG=True

# Application settings
APP_HOST=0.0.0.0
APP_PORT=5000

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

# Initial admin user (used for first-time setup)
DEFAULT_USERNAME=admin
DEFAULT_PASSWORD=your-secure-admin-password

# Door status refresh interval in seconds
DOOR_STATUS_REFRESH_INTERVAL=10

# CORS allowed origins for WebSocket (comma-separated; use "*" for dev only)
# CORS_ALLOWED_ORIGINS=https://yourdomain.com
```

**Important Security Notes:**
- Generate a strong, unique `SECRET_KEY` for production using: `python3 -c 'import secrets; print(secrets.token_hex(32))'`
- Use strong, unique passwords for both database and admin user
- Never commit the `.env` file to version control
- Consider using SSL connections for production deployments
- Change the default admin username to something unique (not 'admin')

### 5. Initialize the Database

Run the database initialization script to set up tables and create the initial admin user:
```bash
python init_db.py
```

This script will:
- Create the necessary database tables (including RBAC columns)
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

### Adding New Users (Admin Panel)
Admin users can create and manage users through the web-based Admin Panel:

1. Log in with an admin account
2. Navigate to the **Admin** panel from the navigation menu
3. Click **Create User** to add a new user
4. Assign a role (`admin` or `regular`) during creation

Admins can also delete users and reset passwords from the Admin Panel.

### User Profile Management
All users can manage their own profile by clicking "Profile" in the dashboard:
- Update first name, last name, email, and phone number
- Toggle SMS notifications
- Change password (requires current password verification)
- Generate an API key for programmatic access

All profile fields are optional and can be updated independently.

### Programmatic User Management
Users can also be managed via Python scripts:

```python
from database import DatabaseManager
from dotenv import load_dotenv

load_dotenv()
db_manager = DatabaseManager()

# Create a new user with a specific role
db_manager.create_user('newuser', 'secure-password', 'regular')

# Update a password
db_manager.update_password('username', 'new-secure-password')
```

## Project Structure

```
garage/
├── app.py                          # Main Flask application
├── database.py                     # MySQL database manager
├── user_roles.py                   # RBAC role definitions (admin, regular)
├── doorStatus.py                   # Door sensor reader (Automation HAT)
├── relay.py                        # Garage door relay control (Automation HAT)
├── init_db.py                      # Database initialization script
├── migrate_db.py                   # Database schema migration
├── migrate_rbac.py                 # RBAC migration for existing installs
├── migrate_api_key.py              # API key column migration
├── migrate_sms_notifications.py    # SMS notifications migration
├── validate_security.py            # Security validation tool
├── requirements.txt                # Python dependencies
├── .env.example                    # Environment variables template
├── .gitignore                      # Git ignore rules
├── garage.service                  # Systemd service file
├── nginx-garage.conf               # Nginx reverse proxy configuration
├── install_production.sh           # Automated production installer
├── backup.sh                       # Database backup script
├── restore.sh                      # Restore from backup
├── health_check.sh                 # System health monitoring
├── monitor.sh                      # Automated service monitoring
├── templates/
│   ├── base.html                   # Base template layout
│   ├── login.html                  # Login page
│   ├── dashboard.html              # Main control dashboard
│   ├── profile.html                # User profile management
│   ├── admin.html                  # Admin user management panel
│   ├── create_user.html            # Create new user form
│   ├── change_password.html        # Admin password change form
│   ├── privacy_policy.html         # Privacy policy page
│   └── terms_and_conditions.html   # Terms and conditions page
├── static/
│   ├── css/
│   │   └── style.css               # Custom CSS with dark mode support
│   └── js/
│       └── app.js                  # Frontend JavaScript logic
├── network-examples/               # Network configuration guides
│   ├── README.md
│   ├── static-ip.md
│   └── port-forwarding.md
└── tests/
    ├── test_rbac.py                # RBAC functionality tests
    ├── test_api_key.py             # API key generation tests
    ├── test_api_keys.py            # API key management tests
    ├── test_sms_notifications.py   # SMS notification tests
    ├── test_socketio.py            # WebSocket tests
    └── test_terms.py               # Terms acceptance tests
```

## Configuration

### Environment Variables
All sensitive configuration is managed through environment variables in `.env`:

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `SECRET_KEY` | Flask secret key for sessions | Yes | — |
| `FLASK_ENV` | Flask environment (`development` or `production`) | No | `development` |
| `FLASK_DEBUG` | Enable debug mode | No | `True` |
| `APP_HOST` | Application bind address | No | `0.0.0.0` |
| `APP_PORT` | Application port | No | `5000` |
| `DB_HOST` | MySQL server hostname | No | `localhost` |
| `DB_PORT` | MySQL server port | No | `3306` |
| `DB_NAME` | Database name | Yes | — |
| `DB_USER` | Database username | Yes | — |
| `DB_PASSWORD` | Database password | Yes | — |
| `DB_SSL_CA` | SSL CA certificate path | No | — |
| `DB_SSL_CERT` | SSL client certificate path | No | — |
| `DB_SSL_KEY` | SSL client key path | No | — |
| `DEFAULT_USERNAME` | Initial admin username | No | `admin` |
| `DEFAULT_PASSWORD` | Initial admin password | No | `admin` |
| `DOOR_STATUS_REFRESH_INTERVAL` | Door status polling interval in seconds | No | `10` |
| `CORS_ALLOWED_ORIGINS` | Allowed WebSocket origins (comma-separated) | No | `*` |

### Security Features
- **MySQL Database Authentication** - No hardcoded passwords
- **Environment Variable Configuration** - Secrets stored outside code
- **Password Hashing** - Uses Werkzeug's secure password hashing with salt
- **Role-Based Access Control** - Admin and Regular roles with route-level enforcement
- **API Key Authentication** - SHA-256 hashed API keys stored in database
- **Parameterized SQL Queries** - Prevents SQL injection
- **Optional SSL/TLS** - Secure database connections
- **Security Event Logging** - Login attempts and admin actions are logged

## Technology Stack

- **Backend**: Python 3.7+, Flask 3.0, Flask-Login 0.6
- **Real-time**: Flask-SocketIO 5.3 with Socket.IO for WebSocket communication
- **Scheduling**: APScheduler 3.10 for background door status polling
- **Database**: MySQL/MariaDB with PyMySQL driver
- **Frontend**: HTML5, CSS3, JavaScript, Bootstrap 5.1
- **Authentication**: Flask-Login with MySQL backend, Werkzeug password hashing
- **Hardware**: Pimoroni automationhat library for Raspberry Pi Automation HAT
- **Configuration**: python-dotenv for environment management
- **Deployment**: Nginx (reverse proxy), systemd (service management)

## Routes and API Endpoints

### Web Routes

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/` | Yes | Home / Dashboard (redirects to login if unauthenticated) |
| GET/POST | `/login` | No | Login page and credential processing |
| GET | `/logout` | Yes | Logout and redirect to login |
| GET/POST | `/profile` | Yes | User profile management |
| POST | `/run_script` | Yes | Execute the garage door relay script |
| GET | `/door_status` | Yes | Get current door status (web UI) |
| POST | `/generate_api_key` | Yes | Generate a new API key for current user |
| GET | `/admin` | Admin | Admin panel - list all users |
| GET/POST | `/admin/create_user` | Admin | Create a new user |
| POST | `/admin/delete_user/<username>` | Admin | Delete a user |
| GET/POST | `/admin/change_password/<username>` | Admin | Change a user's password |
| GET | `/privacy-policy` | No | Privacy policy page |
| GET | `/terms-and-conditions` | No | Terms and conditions page |

### REST API

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/api/door_status` | API Key | Get door status via API |

### WebSocket Events

| Event | Direction | Description |
|-------|-----------|-------------|
| `connect` | Client -> Server | Client connects; triggers scheduler initialization |
| `disconnect` | Client -> Server | Client disconnects |
| `request_status` | Client -> Server | Client requests current door status |
| `door_status_update` | Server -> Client | Server pushes door status changes |

### API Authentication

The `/api/door_status` endpoint requires API key authentication.

#### Obtaining an API Key

1. Log in to the application
2. Navigate to your Profile page (click on your username or go to `/profile`)
3. Click the "Generate API Key" button
4. Copy the generated API key immediately - it will only be shown once

#### Using the API

**Required Header:**
```
X-API-Key: your-api-key-here
```

**Example Request:**
```bash
curl -H "X-API-Key: your-api-key-here" http://localhost:5000/api/door_status
```

**Example Success Response:**
```json
{
  "success": true,
  "status": "closed",
  "raw_output": "Door Closed",
  "error": null
}
```

**Example Error Response (HTTP 401 Unauthorized):**
```json
{
  "error": "Invalid API key"
}
```

**Possible Status Values:**
- `closed` - Door is closed
- `open` - Door is open
- `unknown` - Status could not be determined

## Development

### Running in Development Mode
Set `FLASK_DEBUG=True` in your `.env` file for development features:
- Automatic reload on code changes
- Detailed error pages
- Debug logging

For production, set `FLASK_DEBUG=False`.

### Running Tests
```bash
python test_rbac.py
python test_api_keys.py
python test_socketio.py
python test_sms_notifications.py
python test_terms.py
```

### Database Management
The `database.py` module provides secure methods for:
- User creation and authentication
- Password updates and profile management
- API key generation and validation
- Role-based user retrieval
- User account activation/deactivation

## Production Deployment

For detailed instructions on deploying this application in a production environment on a Raspberry Pi, see **[PRODUCTION.md](PRODUCTION.md)**.

The production guide includes:
- Complete Raspberry Pi setup and configuration
- Automated installation script (`install_production.sh`)
- Systemd service configuration for auto-start (`garage.service`)
- Nginx reverse proxy setup with HTTPS (`nginx-garage.conf`)
- Database optimization for Raspberry Pi
- Automated backup (`backup.sh`) and restore (`restore.sh`) procedures
- System monitoring (`health_check.sh`, `monitor.sh`) and health checks
- Security hardening recommendations

### Quick Production Installation

```bash
# Clone the repository
git clone https://github.com/ozeltser/garage.git
cd garage

# Run automated installation (Raspberry Pi)
sudo bash install_production.sh
```

## Security Considerations

### Production Deployment Checklist
- **Use HTTPS** - Deploy behind a reverse proxy with SSL/TLS
- **Strong Passwords** - Generate secure passwords for all accounts
- **SSL Database Connections** - Enable SSL/TLS for database connections
- **Environment Variables** - Never commit `.env` files to version control
- **Database Security** - Use dedicated database user with minimal privileges
- **Network Security** - Restrict database access to application servers only
- **Regular Updates** - Keep dependencies updated
- **Monitoring** - Monitor logs for security events
- **Set CORS Origins** - Configure `CORS_ALLOWED_ORIGINS` for production (do not use `*`)

### Additional Security Measures
Consider implementing for production:
- Rate limiting for login attempts
- Two-factor authentication
- Session timeout configuration
- Regular security audits
- Database encryption at rest

## Troubleshooting

For detailed troubleshooting information, see **[TROUBLESHOOTING.md](TROUBLESHOOTING.md)**.

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
