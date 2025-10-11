# Database Migration Guide

This guide explains how to migrate your existing Garage App database to support the new user profile features.

## Overview

The user profile feature adds four new columns to the `users` table:
- `first_name` (VARCHAR 255) - User's first name
- `last_name` (VARCHAR 255) - User's last name
- `email` (VARCHAR 255) - User's email address
- `phone` (VARCHAR 50) - User's phone number

All new columns are nullable to maintain backward compatibility with existing user records.

## Prerequisites

Before running the migration, ensure you have:
1. Python 3.7 or higher installed
2. All required Python packages installed (`pip install -r requirements.txt`)
3. A valid `.env` file with database credentials configured
4. Database backup (recommended)

## Migration Methods

You have two options to migrate your database:

### Option 1: Automatic Migration (Recommended)

The easiest method is to use the provided migration script.

#### Steps:

1. **Backup your database** (highly recommended):
   ```bash
   mysqldump -u [username] -p garage_app > backup_$(date +%Y%m%d_%H%M%S).sql
   ```

2. **Run the migration script**:
   ```bash
   python migrate_db.py
   ```

3. **Verify the migration**:
   The script will:
   - Check which columns need to be added
   - Display current schema status
   - Add missing columns
   - Provide a summary of changes
   - Preserve all existing user data

#### Expected Output:

```
============================================================
Database Migration: Adding User Profile Fields
============================================================

Connecting to MySQL database...
✓ Database connection successful

Checking current schema...
  - Column 'first_name' is missing
  - Column 'last_name' is missing
  - Column 'email' is missing
  - Column 'phone' is missing

Migrating database - adding 4 column(s)...
  Adding column 'first_name' (VARCHAR(255))...
  ✓ Column 'first_name' added successfully
  Adding column 'last_name' (VARCHAR(255))...
  ✓ Column 'last_name' added successfully
  Adding column 'email' (VARCHAR(255))...
  ✓ Column 'email' added successfully
  Adding column 'phone' (VARCHAR(50))...
  ✓ Column 'phone' added successfully

============================================================
Migration completed successfully!
============================================================

Summary:
  - Added 4 new column(s) to 'users' table
  - Existing user data preserved
  - New columns are nullable (NULL by default)

Users can now update their profile information through the /profile page.
```

### Option 2: Manual SQL Migration

If you prefer to run the SQL commands directly:

1. **Backup your database**:
   ```bash
   mysqldump -u [username] -p garage_app > backup_$(date +%Y%m%d_%H%M%S).sql
   ```

2. **Connect to MySQL**:
   ```bash
   mysql -u [username] -p garage_app
   ```

3. **Run the following SQL commands**:
   ```sql
   -- Add first_name column
   ALTER TABLE users ADD COLUMN first_name VARCHAR(255) AFTER password_hash;
   
   -- Add last_name column
   ALTER TABLE users ADD COLUMN last_name VARCHAR(255) AFTER first_name;
   
   -- Add email column
   ALTER TABLE users ADD COLUMN email VARCHAR(255) AFTER last_name;
   
   -- Add phone column
   ALTER TABLE users ADD COLUMN phone VARCHAR(50) AFTER email;
   ```

4. **Verify the changes**:
   ```sql
   DESCRIBE users;
   ```

   Expected output should show the new columns:
   ```
   +---------------+--------------+------+-----+-------------------+-------+
   | Field         | Type         | Null | Key | Default           | Extra |
   +---------------+--------------+------+-----+-------------------+-------+
   | id            | int          | NO   | PRI | NULL              | auto_increment |
   | username      | varchar(255) | NO   | UNI | NULL              |       |
   | password_hash | varchar(255) | NO   |     | NULL              |       |
   | first_name    | varchar(255) | YES  |     | NULL              |       |
   | last_name     | varchar(255) | YES  |     | NULL              |       |
   | email         | varchar(255) | YES  |     | NULL              |       |
   | phone         | varchar(50)  | YES  |     | NULL              |       |
   | created_at    | timestamp    | YES  |     | CURRENT_TIMESTAMP |       |
   | updated_at    | timestamp    | YES  |     | CURRENT_TIMESTAMP |       |
   | is_active     | tinyint(1)   | YES  |     | 1                 |       |
   +---------------+--------------+------+-----+-------------------+-------+
   ```

## New Database Installations

If you're setting up a fresh database, you don't need to run this migration. Simply run:

```bash
python init_db.py
```

This will create the users table with all the required columns from the start.

## Rollback (if needed)

If you need to rollback the migration:

### Using SQL:
```sql
ALTER TABLE users DROP COLUMN first_name;
ALTER TABLE users DROP COLUMN last_name;
ALTER TABLE users DROP COLUMN email;
ALTER TABLE users DROP COLUMN phone;
```

### Using backup:
```bash
mysql -u [username] -p garage_app < backup_YYYYMMDD_HHMMSS.sql
```

## Troubleshooting

### Migration script fails with connection error
- Verify your `.env` file has correct database credentials
- Ensure MySQL server is running
- Check that the database user has ALTER TABLE permissions

### "Column already exists" error
- The migration script checks for existing columns and skips them
- If running manual SQL, you can check existing columns with: `DESCRIBE users;`

### Permission denied error
- Ensure the database user has ALTER TABLE privileges:
  ```sql
  GRANT ALTER ON garage_app.* TO 'garage_user'@'localhost';
  FLUSH PRIVILEGES;
  ```

## Post-Migration

After successful migration:
1. Restart your Flask application
2. Existing users will have NULL values for new profile fields
3. Users can update their profile by visiting the `/profile` page
4. All profile fields are optional and can be left blank

## Support

For issues or questions about the migration, please check:
- The application logs for detailed error messages
- MySQL error logs: Usually in `/var/log/mysql/error.log`
- Ensure all prerequisites are met before running the migration
