# Quick Start Guide - RBAC Features

## For Existing Installations

### Step 1: Run the Migration
```bash
cd /opt/garage/app
source venv/bin/activate
python migrate_rbac.py
deactivate
```

### Step 2: Restart the Application
```bash
sudo systemctl restart garage.service
```

### Step 3: Login as Admin
- Username: Your `DEFAULT_USERNAME` from .env (default: `admin`)
- Password: Your `DEFAULT_PASSWORD` from .env
- You should now see "Admin Panel" link in the navigation bar

## For New Installations

No special steps needed! The role column is automatically created and the initial admin user is set up with admin privileges.

## Using Admin Features

### Access the Admin Panel
1. Login as an admin user
2. Click "Admin Panel" in the navigation bar
3. You'll see a list of all users

### Create a New User
1. Go to Admin Panel
2. Click "Create New User" button
3. Fill in:
   - Username (required)
   - Password (required)
   - Confirm Password (required)
   - Role (select "Regular User" or "Admin")
4. Click "Create User"

### Change a User's Password
1. Go to Admin Panel
2. Find the user in the list
3. Click the key icon (🔑) next to their name
4. Enter new password
5. Confirm password
6. Click "Update Password"

### Delete a User
1. Go to Admin Panel
2. Find the user in the list
3. Click the trash icon (🗑️) next to their name
4. Confirm deletion
5. User will be permanently deleted

**Note:** You cannot delete:
- Your own account
- The last admin user (to prevent lockout)

## For Regular Users

### Change Your Own Password
1. Click "Profile" in the navigation bar
2. Scroll to "Change Password" section
3. Enter current password
4. Enter new password
5. Confirm new password
6. Click "Update Profile"

### Update Your Profile
1. Click "Profile" in the navigation bar
2. Update your information:
   - First Name
   - Last Name
   - Email
   - Phone
3. Click "Update Profile"

## Troubleshooting

### "Access denied. Admin privileges required."
- You're logged in as a regular user
- Contact an admin to upgrade your account

### Can't See Admin Panel Link
- Your account doesn't have admin role
- Contact an admin to upgrade your account
- Or check the database: `SELECT username, role FROM users;`

### Migration Issues
1. Check database credentials in `.env`
2. Ensure database user has ALTER TABLE permission
3. Check MySQL logs: `sudo tail -f /var/log/mysql/error.log`

### Need to Promote a User to Admin
Connect to MySQL and run:
```sql
UPDATE users SET role = 'admin' WHERE username = 'username_here';
```

## Best Practices

1. **Create Multiple Admins**: Don't rely on a single admin account
2. **Use Strong Passwords**: Especially for admin accounts
3. **Regular Audits**: Periodically review user list in Admin Panel
4. **Document Roles**: Keep track of who has admin access
5. **Backup Regularly**: Before making user management changes

## Default Credentials

⚠️ **IMPORTANT**: Change the default admin password immediately after first login!

Default admin username: Set in `.env` file (`DEFAULT_USERNAME`)
Default admin password: Set in `.env` file (`DEFAULT_PASSWORD`)

## Command Reference

```bash
# Run migration
python migrate_rbac.py

# Check database schema
mysql -u garage_user -p garage_app -e "DESCRIBE users;"

# List all users and their roles
mysql -u garage_user -p garage_app -e "SELECT username, role FROM users;"

# Promote user to admin (via MySQL)
mysql -u garage_user -p garage_app -e "UPDATE users SET role = 'admin' WHERE username = 'username';"

# Demote admin to regular user (via MySQL)
mysql -u garage_user -p garage_app -e "UPDATE users SET role = 'regular' WHERE username = 'username';"
```

## Need Help?

- See full documentation: `RBAC.md`
- See permission matrix: `RBAC_MATRIX.md`
- See implementation details: `RBAC_SUMMARY.md`
- Run tests: `python test_rbac.py`
