# MySQL Database Setup Guide for Garage Application

This guide will help you connect your Flask application to an Azure MySQL database.

## Prerequisites

1. An Azure MySQL server instance
2. Python 3.7 or higher
3. Access to your Azure MySQL server

## Step 1: Configure Your Azure MySQL Database

### 1.1 Create a Database
Connect to your Azure MySQL server and create a database for the application:
```sql
CREATE DATABASE garage_db;
```

### 1.2 Configure Firewall Rules
Make sure your Azure MySQL server allows connections from your application. In the Azure portal:
1. Go to your MySQL server
2. Select "Connection security"
3. Add your client IP or enable "Allow access to Azure services"

## Step 2: Configure Environment Variables

Edit the `.env` file with your Azure MySQL connection details:

```env
# Azure MySQL Database Configuration
DB_HOST=your-server-name.mysql.database.azure.com
DB_USER=your-username@your-server-name
DB_PASSWORD=your-password
DB_NAME=garage_db
DB_PORT=3306

# Flask Configuration
SECRET_KEY=your-secret-key-change-in-production
```

**Important:** Replace the placeholder values with your actual Azure MySQL credentials:
- `your-server-name`: Your Azure MySQL server name
- `your-username`: Your MySQL username
- `your-password`: Your MySQL password

## Step 3: Install Dependencies

Install the required Python packages:

```bash
pip install -r requirements.txt
```

## Step 4: Initialize the Database

Run the database initialization script:

```bash
python init_db.py
```

This will:
- Create the `users` table
- Create a default admin user (username: `admin`, password: `mypassword`)

## Step 5: Start the Application

```bash
python app.py
```

The application will be available at `http://localhost:5000`

## Step 6: First Login

1. Navigate to `http://localhost:5000`
2. Login with:
   - Username: `admin`
   - Password: `mypassword`
3. **Important:** Change the admin password after first login

## Database Schema

The application creates a `users` table with the following structure:

```sql
CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    email VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
);
```

## Security Considerations

1. **Change Default Password:** Immediately change the default admin password
2. **Environment Variables:** Never commit the `.env` file to version control
3. **SSL Connection:** The application is configured to use SSL for database connections
4. **Password Hashing:** Passwords are stored using Werkzeug's secure password hashing

## Troubleshooting

### Connection Issues
- Verify your Azure MySQL server is running
- Check firewall rules in Azure portal
- Ensure your connection string is correct
- Verify SSL settings

### Authentication Issues
- Make sure the username format includes the server name: `username@servername`
- Check if your user has the necessary permissions on the database

### Common Error Messages

**"Access denied for user"**
- Check username and password
- Verify the user exists and has access to the database

**"Can't connect to MySQL server"**
- Check the hostname and port
- Verify firewall settings
- Ensure the server is running

## Admin Features

When logged in as admin, you can:
- Create new users through the web interface
- Access the admin panel on the dashboard
- Manage user accounts

## API Endpoints

- `GET /` - Home page (redirects to dashboard if authenticated)
- `GET /login` - Login page
- `POST /login` - Process login
- `GET /logout` - Logout
- `GET /init_db` - Initialize database (for setup only)
- `POST /create_user` - Create new user (admin only)
- `POST /run_script` - Execute Python script (authenticated users)

## Adding More Users

You can add users in two ways:

1. **Through the web interface (recommended):**
   - Login as admin
   - Use the "Create New User" form on the dashboard

2. **Directly in the database:**
   ```sql
   INSERT INTO users (username, password_hash, email) 
   VALUES ('newuser', '<hashed_password>', 'user@example.com');
   ```

## Maintenance

### Backup
Regularly backup your Azure MySQL database using Azure's backup features.

### User Management
- Deactivate users instead of deleting them (sets `is_active = FALSE`)
- Monitor user activity through the database logs

### Updates
When updating the application:
1. Backup the database
2. Test in a development environment first
3. Update dependencies carefully
