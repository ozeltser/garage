# RBAC (Role-Based Access Control) Implementation Guide

## Overview

The Garage App now implements Role-Based Access Control (RBAC) with two user roles:

1. **Admin** - Full system access
2. **Regular User** - Limited access to own profile and door operations

## User Roles and Permissions

### Admin Role
Admins have full access to all system features:
- ✅ Operate garage door
- ✅ View and edit own profile
- ✅ Change own password
- ✅ **Create new users** (both admin and regular)
- ✅ **Delete users** (except their own account and the last admin)
- ✅ **Change any user's password**
- ✅ **View all users** in the system

### Regular User Role
Regular users have limited access:
- ✅ Operate garage door
- ✅ View and edit own profile
- ✅ Change own password
- ❌ Cannot create users
- ❌ Cannot delete users
- ❌ Cannot change other users' passwords
- ❌ Cannot access admin panel

## Database Schema Changes

The RBAC implementation adds a new `role` column to the `users` table:

```sql
ALTER TABLE users 
ADD COLUMN role VARCHAR(50) NOT NULL DEFAULT 'regular'
AFTER password_hash;
```

Valid roles:
- `admin` - Administrator with full access
- `regular` - Regular user with limited access

## Migration for Existing Installations

If you have an existing installation, you need to run the migration script to add the role column:

### Automatic Migration (Recommended)

```bash
# As the garage user
cd /opt/garage/app
source venv/bin/activate
python migrate_rbac.py
deactivate
```

The script will:
1. Check if the `role` column already exists
2. Add the column if missing (with default value 'regular')
3. Set the initial admin user (from `DEFAULT_USERNAME` env var) to have 'admin' role
4. Preserve all existing user data

### Manual Migration

If you prefer to migrate manually using SQL:

```bash
mysql -u garage_user -p garage_app
```

```sql
-- Add role column
ALTER TABLE users 
ADD COLUMN role VARCHAR(50) NOT NULL DEFAULT 'regular'
AFTER password_hash;

-- Set admin role for the default admin user
UPDATE users SET role = 'admin' WHERE username = 'admin';
-- Or use your custom admin username from .env
UPDATE users SET role = 'admin' WHERE username = 'your_admin_username';
```

## New Installation

For fresh installations, no migration is needed. The database setup script (`init_db.py`) or the `DatabaseManager` initialization will automatically:
1. Create the `users` table with the `role` column
2. Create an initial admin user with the admin role

## Admin Panel Access

Once logged in as an admin user, you'll see an "Admin Panel" link in the navigation bar.

### Admin Panel Features

#### User Management Dashboard (`/admin`)
- View all users in the system
- See user roles, names, emails, and creation dates
- Quick access to user management actions

#### Create New User (`/admin/create_user`)
- Username (required)
- Password (required)
- Confirm Password (required)
- Role selection (Admin or Regular User)

#### Change User Password (`/admin/change_password/<username>`)
- Admins can change any user's password
- No need to know the current password
- Useful for password resets

#### Delete User (`/admin/delete_user/<username>`)
- Remove users from the system
- Safety checks:
  - Cannot delete your own account
  - Cannot delete the last admin user (to prevent lockout)

## Security Features

### Access Control
- All admin routes are protected with `@admin_required` decorator
- Regular users attempting to access admin routes are redirected with an error message
- User role is verified on every request

### Safety Measures
1. **Last Admin Protection**: The system prevents deletion of the last admin user
2. **Self-Deletion Prevention**: Admins cannot delete their own accounts
3. **Password Validation**: All password changes require confirmation
4. **Role Validation**: Only valid roles ('admin', 'regular') are accepted

## API Changes

### Updated Methods

#### `database.py`

```python
# Updated to support roles
create_user(username: str, password: str, role: str = 'regular') -> bool

# New admin methods
get_all_users() -> list
delete_user(username: str) -> bool
update_user_password_by_admin(username: str, new_password: str) -> bool
```

#### `app.py`

```python
# Updated User class
class User(UserMixin):
    def __init__(self, username, user_id=None, role='regular'):
        self.role = role
    
    def is_admin(self):
        return self.role == 'admin'

# New decorator
@admin_required
```

### New Routes

- `GET /admin` - Admin dashboard
- `GET/POST /admin/create_user` - Create new user form
- `POST /admin/delete_user/<username>` - Delete user
- `GET/POST /admin/change_password/<username>` - Change user password

## Configuration

No changes to `.env` configuration are needed. The existing `DEFAULT_USERNAME` and `DEFAULT_PASSWORD` variables are used to create the initial admin user.

## Troubleshooting

### "Access denied. Admin privileges required."
- You are logged in as a regular user trying to access admin features
- Contact an administrator to upgrade your account or create an admin account

### Cannot delete user
- Check if you're trying to delete your own account (not allowed)
- Check if you're trying to delete the last admin user (not allowed)

### Migration fails
- Ensure database credentials in `.env` are correct
- Verify the database user has ALTER TABLE permissions
- Check MySQL error logs for details

### "User not found" after migration
- The migration script only updates existing users
- New users are created with the appropriate role when added

## Best Practices

1. **Create at least two admin users** to prevent lockout scenarios
2. **Use strong passwords** for admin accounts
3. **Regularly review user access** in the admin panel
4. **Document role assignments** for your organization
5. **Back up the database** before running migrations

## Rollback Procedure

If you need to revert the RBAC changes:

```sql
-- Remove the role column
ALTER TABLE users DROP COLUMN role;

-- Restore application files from backup
cd /opt/garage
sudo su - garage -s /bin/bash
rm -rf app
mv app.backup.YYYYMMDD app
```

Note: After rollback, all RBAC features will be removed and all users will have equal access.
