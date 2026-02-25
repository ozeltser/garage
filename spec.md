# Garage Web App - Technical Specification

## 1. Overview

The Garage Web App is a Python Flask application that provides secure, web-based control of a garage door using a Raspberry Pi equipped with a Pimoroni Automation HAT. The application features MySQL-backed authentication, role-based access control, real-time door status monitoring via WebSocket, and a REST API for programmatic access.

### 1.1 Target Platform

- **Production**: Raspberry Pi 3B+ or newer with Pimoroni Automation HAT
- **Development**: Any system running Python 3.7+ with MySQL/MariaDB

### 1.2 Key Design Goals

- Secure remote garage door control over HTTPS
- Real-time door state awareness without manual polling
- Multi-user support with role-based permissions
- Mobile-first responsive UI
- Production-ready with automated deployment for Raspberry Pi

## 2. Architecture

### 2.1 High-Level Architecture

```
 Browser/Client        Nginx (reverse proxy)        Flask App         MySQL
 ┌────────────┐       ┌──────────────────┐       ┌───────────┐     ┌───────┐
 │  HTML/CSS  │──────>│  HTTPS termination│──────>│  app.py   │────>│ users │
 │  JS        │<──────│  Static caching   │<──────│           │<────│ table │
 │  Socket.IO │  WS   │  Security headers │  WS   │  SocketIO │     └───────┘
 └────────────┘       └──────────────────┘       └─────┬─────┘
                                                       │
                                                       v
                                               ┌──────────────┐
                                               │ Automation   │
                                               │ HAT (GPIO)   │
                                               │  - relay.py  │
                                               │  - doorStatus│
                                               └──────────────┘
```

### 2.2 Component Breakdown

| Component | File | Purpose |
|-----------|------|---------|
| Web Application | `app.py` | Flask routes, authentication, WebSocket handling, scheduler |
| Database Layer | `database.py` | MySQL connection management, user CRUD, API key management |
| Role Definitions | `user_roles.py` | RBAC role enumeration (`admin`, `regular`) |
| Door Sensor | `doorStatus.py` | Reads door open/closed state from Automation HAT input |
| Relay Control | `relay.py` | Activates garage door relay for 5 seconds via Automation HAT |
| DB Initialization | `init_db.py` | Creates tables and initial admin user |
| Migrations | `migrate_*.py` | Schema migration scripts for upgrades |

### 2.3 Request Flow

1. Client sends HTTPS request to Nginx
2. Nginx terminates TLS and proxies to Flask (port 5000)
3. Flask-Login validates session cookie
4. Route handler processes request (with RBAC check for admin routes)
5. Database queries use parameterized statements via PyMySQL
6. Hardware control scripts are invoked via `subprocess.run()` with timeout

## 3. Technology Stack

### 3.1 Backend Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| Flask | 3.0.0 | Web framework |
| Flask-Login | 0.6.3 | Session-based authentication |
| Flask-SocketIO | 5.3.6 | WebSocket support (Socket.IO protocol) |
| Werkzeug | 3.0.1 | Password hashing (scrypt/pbkdf2), HTTP utilities |
| PyMySQL | 1.1.0 | MySQL database driver |
| python-dotenv | 1.0.0 | Environment variable loading from `.env` |
| APScheduler | 3.10.4 | Background task scheduling |
| automationhat | 1.0.0 | Pimoroni Automation HAT hardware interface |

### 3.2 Frontend

| Technology | Version | Purpose |
|------------|---------|---------|
| Bootstrap | 5.1.3 | Responsive CSS framework |
| Bootstrap Icons | (bundled) | Icon library |
| Socket.IO Client | (CDN) | WebSocket client for real-time updates |
| Vanilla JavaScript | ES6+ | Frontend logic and AJAX |

### 3.3 Infrastructure

| Component | Purpose |
|-----------|---------|
| Nginx | HTTPS termination, reverse proxy, static file serving, security headers |
| systemd | Process management, auto-restart on failure, boot-time start |
| MySQL 5.7+ / MariaDB 10.2+ | Persistent data storage |

## 4. Database Schema

### 4.1 `users` Table

```sql
CREATE TABLE users (
    id                       INT AUTO_INCREMENT PRIMARY KEY,
    username                 VARCHAR(255) UNIQUE NOT NULL,
    password_hash            VARCHAR(255) NOT NULL,
    role                     VARCHAR(50) NOT NULL DEFAULT 'regular',
    first_name               VARCHAR(255),
    last_name                VARCHAR(255),
    email                    VARCHAR(255),
    phone                    VARCHAR(50),
    sms_notifications_enabled BOOLEAN DEFAULT FALSE,
    created_at               TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at               TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    is_active                BOOLEAN DEFAULT TRUE,
    api_key_hash             VARCHAR(255) UNIQUE
);
```

### 4.2 Field Details

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `id` | INT | PK, AUTO_INCREMENT | Unique user identifier |
| `username` | VARCHAR(255) | UNIQUE, NOT NULL | Login username |
| `password_hash` | VARCHAR(255) | NOT NULL | Werkzeug-generated password hash |
| `role` | VARCHAR(50) | NOT NULL, DEFAULT 'regular' | User role: `admin` or `regular` |
| `first_name` | VARCHAR(255) | Nullable | User's first name |
| `last_name` | VARCHAR(255) | Nullable | User's last name |
| `email` | VARCHAR(255) | Nullable | User's email address |
| `phone` | VARCHAR(50) | Nullable | User's phone number |
| `sms_notifications_enabled` | BOOLEAN | DEFAULT FALSE | SMS notification opt-in |
| `created_at` | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | Account creation time |
| `updated_at` | TIMESTAMP | Auto-updated on change | Last modification time |
| `is_active` | BOOLEAN | DEFAULT TRUE | Soft-delete flag |
| `api_key_hash` | VARCHAR(255) | UNIQUE, Nullable | SHA-256 hash of user's API key |

### 4.3 Character Set

- Database: `utf8mb4` with `utf8mb4_unicode_ci` collation
- Supports full Unicode including emoji

## 5. Authentication and Authorization

### 5.1 Session Authentication (Web UI)

- **Library**: Flask-Login
- **Password Storage**: Werkzeug `generate_password_hash()` / `check_password_hash()`
- **Session Management**: Flask secure cookies with configurable `SECRET_KEY`
- **Login Flow**: Username/password form -> verify against MySQL -> create session

### 5.2 API Key Authentication (REST API)

- **Key Generation**: `secrets.token_hex(32)` (64-character hex string)
- **Storage**: SHA-256 hash stored in `api_key_hash` column (plain-text key is never stored)
- **Header**: `X-API-Key: <key>`
- **One-time Display**: The plain-text key is shown only once at generation time

### 5.3 Role-Based Access Control (RBAC)

| Role | Permissions |
|------|-------------|
| `admin` | Full access: user management (create, delete, change passwords), admin panel, all regular user capabilities |
| `regular` | Dashboard access, door control, own profile management, API key generation |

- Enforced via `@admin_required` decorator on admin routes
- Role stored in `users.role` column
- System prevents deletion of the last admin user

## 6. Routes and Endpoints

### 6.1 Public Routes (No Authentication)

| Method | Path | Description |
|--------|------|-------------|
| GET/POST | `/login` | Login page and credential processing |
| GET | `/privacy-policy` | Privacy policy page |
| GET | `/terms-and-conditions` | Terms and conditions page |

### 6.2 Authenticated Routes (Any Logged-in User)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/` | Dashboard (redirects to `/login` if unauthenticated) |
| GET | `/logout` | Log out and redirect to login |
| GET/POST | `/profile` | View and update user profile |
| POST | `/run_script` | Execute `relay.py` (toggle garage door) |
| GET | `/door_status` | Get current door status as JSON |
| POST | `/generate_api_key` | Generate a new API key |

### 6.3 Admin Routes (Admin Role Required)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/admin` | Admin panel listing all users |
| GET/POST | `/admin/create_user` | Create a new user with role assignment |
| POST | `/admin/delete_user/<username>` | Delete a user account |
| GET/POST | `/admin/change_password/<username>` | Change a user's password |

### 6.4 REST API

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/api/door_status` | API Key (`X-API-Key` header) | Returns door status as JSON |

**Response format:**
```json
{
  "success": true,
  "status": "closed",
  "raw_output": "Door Closed",
  "error": null
}
```

Status values: `closed`, `open`, `unknown`

### 6.5 WebSocket Events (Socket.IO)

| Event | Direction | Payload | Description |
|-------|-----------|---------|-------------|
| `connect` | Client -> Server | — | Triggers scheduler initialization and sends current status |
| `disconnect` | Client -> Server | — | Client disconnection handling |
| `request_status` | Client -> Server | — | Explicit status request from client |
| `door_status_update` | Server -> Client | `{status, oldStatus, timestamp}` | Pushed when door status changes |

## 7. Hardware Interface

### 7.1 Door Status Sensor (`doorStatus.py`)

- Reads `automationhat.input.one`
- Value > 0: Door is **closed**
- Value = 0: Door is **open**
- Output: Prints `"Door Closed"` or `"Door Opened"` to stdout
- Timeout: 10-second subprocess limit

### 7.2 Relay Control (`relay.py`)

- Activates `automationhat.relay.one` for **5 seconds**
- Turns on power indicator LED during activation
- Relay is always turned off in a `finally` block to ensure safety
- Timeout: 30-second subprocess limit for the web UI call

### 7.3 Required Hardware

- Raspberry Pi 3B+ or newer
- Pimoroni Automation HAT
- Magnetic door sensor connected to Input 1
- Garage door opener connected to Relay 1

## 8. Real-time Door Status Monitoring

### 8.1 Architecture

- **Scheduler**: APScheduler `BackgroundScheduler` with `IntervalTrigger`
- **Default Interval**: 10 seconds (configurable via `DOOR_STATUS_REFRESH_INTERVAL`)
- **Protocol**: Socket.IO (WebSocket with long-polling fallback)

### 8.2 Behavior

1. Scheduler is initialized on the first WebSocket client connection
2. Every N seconds, `check_door_status_and_notify()` runs `doorStatus.py`
3. If the status has changed from the last known value, a `door_status_update` event is emitted to all connected clients
4. Newly connecting clients immediately receive the current known status
5. Scheduler shuts down cleanly via `atexit` handler

## 9. Frontend

### 9.1 Templates (Jinja2)

| Template | Description |
|----------|-------------|
| `base.html` | Shared layout: navigation bar, footer, Bootstrap/Socket.IO includes, dark mode toggle |
| `login.html` | Username/password login form |
| `dashboard.html` | Main control page: door control button, real-time status display |
| `profile.html` | User profile editing form, API key generation |
| `admin.html` | User management table with delete/change-password actions |
| `create_user.html` | New user creation form with role selection |
| `change_password.html` | Admin password reset form for a specific user |
| `privacy_policy.html` | Privacy policy content |
| `terms_and_conditions.html` | Terms of service content |

### 9.2 Theming

- Dark and light themes using CSS custom properties
- Theme toggle button in the navigation bar
- User preference auto-detected from system settings
- Theme selection persisted in browser local storage

### 9.3 JavaScript (`app.js`)

- AJAX-based script execution with loading indicators
- Socket.IO client for real-time door status updates
- Theme toggle logic
- Form validation and interaction handling

## 10. Deployment

### 10.1 systemd Service (`garage.service`)

- Runs the Flask app as a dedicated `garage` user
- Working directory: `/opt/garage/app`
- Auto-restart on failure
- Starts after `network-online.target` and `mysql.service`

### 10.2 Nginx Configuration (`nginx-garage.conf`)

- HTTP to HTTPS redirection
- TLS termination with configurable certificate paths
- WebSocket proxy support for Socket.IO (at `/socket.io/`)
- Security headers: HSTS, X-Frame-Options, X-Content-Type-Options, X-XSS-Protection
- Static file caching with 30-day expiry

### 10.3 Automated Installer (`install_production.sh`)

One-command setup for Raspberry Pi:
```bash
sudo bash install_production.sh
```

Performs:
- System package installation
- Python virtual environment setup
- MySQL database and user creation
- Application file deployment to `/opt/garage/app`
- systemd service installation and enablement
- Nginx configuration and SSL certificate generation
- Cron job setup for automated backups and monitoring

### 10.4 Operational Scripts

| Script | Purpose |
|--------|---------|
| `backup.sh` | Automated MySQL database backup (daily at 2 AM, 7-day retention) |
| `restore.sh` | Restore database from a backup file |
| `health_check.sh` | Monitor system health: service status, CPU temperature, disk/memory usage |
| `monitor.sh` | Service monitoring with automatic restart on failure |

## 11. Security

### 11.1 Implemented Security Measures

| Measure | Implementation |
|---------|---------------|
| Password Hashing | Werkzeug scrypt/pbkdf2 with unique salt per user |
| SQL Injection Prevention | All queries use parameterized statements (`%s` placeholders) |
| Session Security | Flask signed cookies with configurable SECRET_KEY |
| API Key Security | SHA-256 hashed keys; plain-text never stored |
| Environment Secrets | All credentials loaded from `.env` (not in source code) |
| Database User Isolation | Dedicated MySQL user with SELECT/INSERT/UPDATE/DELETE only |
| HTTPS | Nginx handles TLS termination |
| Security Headers | HSTS, X-Frame-Options, X-Content-Type-Options via Nginx |
| RBAC Enforcement | `@admin_required` decorator on admin routes |
| Soft Delete | Users are deactivated (not hard-deleted) via `is_active` flag |
| Last Admin Protection | System prevents deletion of the last admin user |
| CORS Configuration | Configurable allowed origins for WebSocket connections |

### 11.2 Security Validation

The `validate_security.py` script checks for common security issues in the deployment.

### 11.3 Recommendations for Production

- Enable SSL/TLS for MySQL connections
- Set specific `CORS_ALLOWED_ORIGINS` (do not use `*`)
- Configure rate limiting for login attempts
- Implement session timeout
- Enable log monitoring and alerting
- Regularly update dependencies
- Consider two-factor authentication for admin users

## 12. Configuration Reference

All configuration is via environment variables in `.env`:

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `SECRET_KEY` | Yes | — | Flask session signing key |
| `FLASK_ENV` | No | `development` | Flask environment mode |
| `FLASK_DEBUG` | No | `True` | Enable Flask debug mode |
| `APP_HOST` | No | `0.0.0.0` | Application bind address |
| `APP_PORT` | No | `5000` | Application listen port |
| `DB_HOST` | No | `localhost` | MySQL server hostname |
| `DB_PORT` | No | `3306` | MySQL server port |
| `DB_NAME` | Yes | — | MySQL database name |
| `DB_USER` | Yes | — | MySQL username |
| `DB_PASSWORD` | Yes | — | MySQL password |
| `DB_SSL_CA` | No | — | Path to SSL CA certificate |
| `DB_SSL_CERT` | No | — | Path to SSL client certificate |
| `DB_SSL_KEY` | No | — | Path to SSL client key |
| `DEFAULT_USERNAME` | No | `admin` | Initial admin username |
| `DEFAULT_PASSWORD` | No | `admin` | Initial admin password |
| `DOOR_STATUS_REFRESH_INTERVAL` | No | `10` | Seconds between door status checks |
| `CORS_ALLOWED_ORIGINS` | No | `*` | Comma-separated list of allowed WebSocket origins |

## 13. Testing

### 13.1 Test Files

| File | Coverage |
|------|----------|
| `test_rbac.py` | Role-based access control: role validation, admin decorator, route permissions |
| `test_api_key.py` | API key generation and validation |
| `test_api_keys.py` | API key management lifecycle |
| `test_sms_notifications.py` | SMS notification opt-in/opt-out |
| `test_socketio.py` | WebSocket connection and event handling |
| `test_terms.py` | Terms and conditions acceptance |

### 13.2 Running Tests

```bash
python test_rbac.py
python test_api_keys.py
python test_socketio.py
python test_sms_notifications.py
python test_terms.py
```

## 14. Database Migrations

Migration scripts handle schema changes for upgrades from older versions:

| Script | Purpose |
|--------|---------|
| `migrate_db.py` | General schema migration |
| `migrate_rbac.py` | Adds `role` column to existing `users` table |
| `migrate_api_key.py` | Adds `api_key_hash` column to existing `users` table |
| `migrate_sms_notifications.py` | Adds `sms_notifications_enabled` column to existing `users` table |

Always back up the database before running migrations. See [MIGRATION.md](MIGRATION.md) for detailed instructions.
