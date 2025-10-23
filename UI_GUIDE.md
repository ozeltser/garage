# RBAC UI Flow and Screenshots Guide

## User Experience Overview

### For Regular Users

#### Login Screen
- Standard login form
- Username and password fields
- No visual differences from before

#### Dashboard (Regular User View)
```
┌─────────────────────────────────────────────────────┐
│ [☾] Garage Dashboard        Profile | john | Logout│
├─────────────────────────────────────────────────────┤
│                                                     │
│              Garage Control Panel                   │
│                                                     │
│         ┌─────────────────────────┐                │
│         │  Garage Door Status     │                │
│         │  🏠 CLOSED              │                │
│         └─────────────────────────┘                │
│                                                     │
│         [Open/Close Garage Door]                    │
│                                                     │
└─────────────────────────────────────────────────────┘
```

#### Profile Page (Regular User View)
```
┌─────────────────────────────────────────────────────┐
│ [☾] User Profile    Dashboard | john | Logout      │
├─────────────────────────────────────────────────────┤
│                                                     │
│              Edit Profile                           │
│                                                     │
│  Username:     [john        ] (disabled)            │
│  First Name:   [John        ]                       │
│  Last Name:    [Doe         ]                       │
│  Email:        [john@example]                       │
│  Phone:        [555-1234    ]                       │
│                                                     │
│  ─────── Change Password ───────                    │
│                                                     │
│  Current Password:  [********]                      │
│  New Password:      [********]                      │
│  Confirm Password:  [********]                      │
│                                                     │
│  [Update Profile]  [Cancel]                         │
│                                                     │
└─────────────────────────────────────────────────────┘
```

---

### For Admin Users

#### Dashboard (Admin User View)
```
┌──────────────────────────────────────────────────────┐
│ [☾] Garage Dashboard   Admin Panel | Profile | admin | Logout│
│                        ^^^^^^^^^^^ (NEW!)            │
├──────────────────────────────────────────────────────┤
│                                                      │
│              Garage Control Panel                    │
│                                                      │
│         ┌─────────────────────────┐                 │
│         │  Garage Door Status     │                 │
│         │  🏠 CLOSED              │                 │
│         └─────────────────────────┘                 │
│                                                      │
│         [Open/Close Garage Door]                     │
│                                                      │
└──────────────────────────────────────────────────────┘
```

#### Admin Panel (Main Dashboard)
```
┌──────────────────────────────────────────────────────┐
│ [☾] Admin Panel    Dashboard | Profile | admin | Logout│
├──────────────────────────────────────────────────────┤
│                                                      │
│              User Management                         │
│                                                      │
│  [+ Create New User]                                 │
│                                                      │
│  ┌────────────────────────────────────────────────┐ │
│  │ Username │ Role    │ Name      │ Email   │ Actions│
│  ├──────────┼─────────┼───────────┼─────────┼────────│
│  │ admin    │ [Admin] │ -         │ -       │ 🔑    │
│  │ john_doe │ [Reg.]  │ John Doe  │ j@ex.com│ 🔑 🗑️ │
│  │ jane     │ [Admin] │ Jane Smith│ jane@ex │ 🔑 🗑️ │
│  │ bob      │ [Reg.]  │ Bob Jones │ -       │ 🔑 🗑️ │
│  └────────────────────────────────────────────────┘ │
│                                                      │
│  Legend: 🔑 = Change Password, 🗑️ = Delete User    │
│                                                      │
└──────────────────────────────────────────────────────┘
```

#### Create User Page
```
┌──────────────────────────────────────────────────────┐
│ [☾] Create New User   Admin Panel | Dashboard | admin | Logout│
├──────────────────────────────────────────────────────┤
│                                                      │
│              Create New User                         │
│                                                      │
│  Username *        [____________]                    │
│                                                      │
│  Password *        [************]                    │
│                                                      │
│  Confirm Password *[************]                    │
│                                                      │
│  Role *            [Regular User ▼]                  │
│                    - Regular User                    │
│                    - Admin                           │
│                                                      │
│  ℹ️ Regular users can operate the door and          │
│     manage their own profile.                        │
│     Admins can also create/delete users and          │
│     change any user's password.                      │
│                                                      │
│  [Create User]  [Cancel]                             │
│                                                      │
└──────────────────────────────────────────────────────┘
```

#### Change User Password Page
```
┌──────────────────────────────────────────────────────┐
│ [☾] Change Password   Admin Panel | Dashboard | admin | Logout│
├──────────────────────────────────────────────────────┤
│                                                      │
│              Change Password                         │
│                                                      │
│  Changing password for user: john_doe                │
│                                                      │
│  New Password *        [************]                │
│                                                      │
│  Confirm New Password *[************]                │
│                                                      │
│  [Update Password]  [Cancel]                         │
│                                                      │
└──────────────────────────────────────────────────────┘
```

---

## Navigation Flow

### Regular User Flow
```
┌────────┐
│ Login  │
└───┬────┘
    │
    ▼
┌──────────┐
│Dashboard │◄─────┐
└────┬─────┘      │
     │            │
     │  ┌─────────┴──┐
     └─►│  Profile   │
        └────────────┘
```

### Admin User Flow
```
┌────────┐
│ Login  │
└───┬────┘
    │
    ▼
┌──────────┐
│Dashboard │◄────────────┐
└────┬─────┘             │
     │                   │
     │  ┌────────────┐   │
     ├─►│  Profile   │───┤
     │  └────────────┘   │
     │                   │
     │  ┌────────────┐   │
     └─►│Admin Panel │───┤
        └─────┬──────┘   │
              │          │
        ┌─────┴─────┐    │
        │           │    │
    ┌───▼────┐ ┌───▼────▼────┐
    │ Create │ │Change/Delete│
    │  User  │ │    User     │
    └───┬────┘ └─────┬───────┘
        │            │
        └────────────┴────────┘
```

---

## UI Elements and Badges

### Role Badges
- **Admin**: Red badge with "Admin" text
  ```html
  <span class="badge bg-danger">Admin</span>
  ```

- **Regular User**: Blue badge with "Regular" text
  ```html
  <span class="badge bg-primary">Regular</span>
  ```

### Action Buttons
- **Change Password**: Yellow/Warning button with key icon (🔑)
- **Delete User**: Red/Danger button with trash icon (🗑️)
- **Create User**: Green/Primary button with plus icon

### Conditional Elements
```jinja2
{% if current_user.is_admin() %}
    <a class="nav-link" href="{{ url_for('admin') }}">Admin Panel</a>
{% endif %}
```

---

## Responsive Design

### Mobile View (< 768px)
- Navigation collapses into hamburger menu
- Tables become scrollable horizontally
- Buttons stack vertically
- Form fields take full width

### Tablet View (768px - 1024px)
- Side-by-side layout for form fields
- Table shows all columns
- Navigation bar remains horizontal

### Desktop View (> 1024px)
- Full table display with all columns
- Multiple columns for forms
- Optimized spacing and margins

---

## Color Scheme

### Theme Support
The application supports light and dark themes via the theme toggle button (◐)

#### Light Theme
- Background: White (#ffffff)
- Text: Dark gray (#212529)
- Primary: Blue (#0d6efd)
- Danger: Red (#dc3545)
- Warning: Yellow (#ffc107)

#### Dark Theme
- Background: Dark gray (#212529)
- Text: White (#ffffff)
- Primary: Light blue (#0dcaf0)
- Danger: Pink (#f8d7da)
- Warning: Orange (#ffc107)

---

## Access Control Indicators

### Visual Feedback for Access Denial
When a regular user tries to access admin routes:
```
┌──────────────────────────────────────┐
│  ⚠️ Access denied. Admin privileges │
│     required.                        │
└──────────────────────────────────────┘
```

### Success Messages
```
┌──────────────────────────────────────┐
│  ✓ User created successfully         │
└──────────────────────────────────────┘

┌──────────────────────────────────────┐
│  ✓ Password updated successfully     │
└──────────────────────────────────────┘

┌──────────────────────────────────────┐
│  ✓ User deleted successfully         │
└──────────────────────────────────────┘
```

---

## Interactive Features

### Delete Confirmation
JavaScript confirmation dialog before user deletion:
```javascript
Are you sure you want to delete user 'john_doe'?
[Cancel] [OK]
```

### Form Validation
- Required fields marked with asterisk (*)
- Password confirmation must match
- Role must be valid ('admin' or 'regular')
- Username must be unique

### Real-time Feedback
- Loading spinners during operations
- Success/error messages via Flask flash
- Smooth animations and transitions

---

## Accessibility

### ARIA Labels
- All buttons have descriptive titles
- Form fields have associated labels
- Tables have proper headers

### Keyboard Navigation
- All interactive elements accessible via Tab
- Forms can be submitted with Enter
- Buttons activated with Space/Enter

### Screen Reader Support
- Semantic HTML structure
- Descriptive alt text for icons
- Proper heading hierarchy

---

## Security Visual Indicators

### Password Fields
- Always masked (type="password")
- Confirmation fields for changes
- No password shown in UI

### User Status
- Active users shown in table
- Inactive users hidden from view
- Role clearly displayed with badges

### Admin Actions
- Destructive actions use red color
- Confirmation required for deletion
- Cannot delete self or last admin

---

This UI guide provides a comprehensive overview of how users interact with the RBAC features. All screens are responsive, accessible, and provide clear visual feedback for all actions.
