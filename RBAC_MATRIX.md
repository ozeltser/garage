# RBAC Permission Matrix

## Permission Comparison Table

| Feature / Permission | Regular User | Admin User |
|---------------------|--------------|------------|
| **Door Operations** |
| Operate garage door | ✅ Yes | ✅ Yes |
| Check door status | ✅ Yes | ✅ Yes |
| **Profile Management** |
| View own profile | ✅ Yes | ✅ Yes |
| Edit own profile | ✅ Yes | ✅ Yes |
| Change own password | ✅ Yes | ✅ Yes |
| **User Management** |
| View all users | ❌ No | ✅ Yes |
| Create new users | ❌ No | ✅ Yes |
| Delete users | ❌ No | ✅ Yes |
| Change other users' passwords | ❌ No | ✅ Yes |
| **Admin Panel** |
| Access admin panel | ❌ No | ✅ Yes |
| View admin menu link | ❌ No | ✅ Yes |

## Access Control Flow

```
┌─────────────────┐
│   User Login    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Authentication │
│   & Load Role   │
└────────┬────────┘
         │
    ┌────┴────┐
    │         │
    ▼         ▼
┌───────┐ ┌───────┐
│Regular│ │ Admin │
│ User  │ │ User  │
└───┬───┘ └───┬───┘
    │         │
    │         ├─────────────┐
    │         │             │
    ▼         ▼             ▼
┌─────────┐ ┌─────────┐ ┌──────────┐
│Dashboard│ │Dashboard│ │  Admin   │
│  Door   │ │  Door   │ │  Panel   │
│ Profile │ │ Profile │ │User Mgmt │
└─────────┘ └─────────┘ └──────────┘
```

## Route Protection

### Public Routes (No Login Required)
- `/login` - Login page

### Authenticated Routes (All Users)
- `/` - Home/Dashboard
- `/profile` - User profile management
- `/run_script` - Operate garage door
- `/door_status` - Check door status
- `/logout` - Logout

### Admin-Only Routes (Admin Users)
- `/admin` - Admin dashboard
- `/admin/create_user` - Create new users
- `/admin/delete_user/<username>` - Delete users
- `/admin/change_password/<username>` - Change user passwords

## Database Schema

### Before RBAC
```sql
CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    first_name VARCHAR(255),
    last_name VARCHAR(255),
    email VARCHAR(255),
    phone VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
);
```

### After RBAC
```sql
CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL DEFAULT 'regular',  -- ⭐ NEW
    first_name VARCHAR(255),
    last_name VARCHAR(255),
    email VARCHAR(255),
    phone VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
);
```

## Code Examples

### Checking User Role in Templates
```jinja2
{% if current_user.is_admin() %}
    <a class="nav-link" href="{{ url_for('admin') }}">Admin Panel</a>
{% endif %}
```

### Protecting Routes
```python
@app.route('/admin')
@login_required
@admin_required  # ⭐ NEW
def admin():
    """Admin dashboard."""
    users = db_manager.get_all_users()
    return render_template('admin.html', users=users)
```

### Creating Users with Roles
```python
# Create regular user (default)
db_manager.create_user('john_doe', 'password123')

# Create admin user
db_manager.create_user('jane_admin', 'password456', role='admin')
```

## Security Considerations

### Password Management
- **Regular users**: Can only change their own password via profile page
- **Admin users**: Can change any user's password without knowing current password

### User Deletion
- **Protection against lockout**: Cannot delete the last admin user
- **Protection against self-deletion**: Admins cannot delete their own account
- **Confirmation required**: JavaScript confirmation before deletion

### Role Assignment
- **Role validation**: Only 'admin' and 'regular' roles are valid
- **Default role**: New users default to 'regular' role
- **Initial admin**: First user (from DEFAULT_USERNAME env var) is set as admin

## Migration Strategy

### Existing Installations
1. Back up database
2. Run migration script: `python migrate_rbac.py`
3. Verify admin user has admin role
4. Restart application

### New Installations
1. Set up environment variables (including DEFAULT_USERNAME)
2. Run application
3. Database automatically creates with role column
4. Initial admin user created with admin role

## Testing Checklist

- [x] Regular user cannot access admin routes
- [x] Admin user can access admin routes
- [x] Regular user sees no admin menu link
- [x] Admin user sees admin menu link
- [x] Admin can create users with both roles
- [x] Admin can delete users (except self and last admin)
- [x] Admin can change any user's password
- [x] Regular user can change own password
- [x] All existing functionality works for both roles
