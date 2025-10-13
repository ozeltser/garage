# Security Improvements Implementation Guide

This document provides step-by-step instructions for implementing the security improvements recommended in the Security Audit 2025.

## Quick Start - Critical Improvements

These improvements should be implemented immediately for production deployments.

### 1. Add Security Headers (Flask-Talisman)

**Priority**: CRITICAL  
**Effort**: Low (30 minutes)  
**Impact**: High

#### Installation

```bash
pip install flask-talisman
```

#### Update requirements.txt

```text
Flask==3.0.0
Flask-Login==0.6.3
Flask-Talisman==1.1.0
Werkzeug==3.0.1
pymysql==1.1.0
python-dotenv==1.0.0
automationhat==1.0.0
```

#### Update app.py

Add after Flask app initialization (around line 12):

```python
from flask_talisman import Talisman

# Configure security headers
Talisman(app,
    force_https=False,  # Set to True if using HTTPS
    strict_transport_security=True,
    strict_transport_security_max_age=31536000,  # 1 year
    content_security_policy={
        'default-src': "'self'",
        'script-src': ["'self'", "'unsafe-inline'"],  # jQuery/inline scripts
        'style-src': ["'self'", "'unsafe-inline'"],   # Bootstrap/inline styles
        'img-src': ["'self'", "data:"],
        'font-src': "'self'"
    },
    content_security_policy_nonce_in=['script-src'],
    feature_policy={
        'geolocation': "'none'",
        'camera': "'none'",
        'microphone': "'none'"
    }
)
```

**For production with HTTPS**, set `force_https=True`.

---

### 2. Add CSRF Protection (Flask-WTF)

**Priority**: CRITICAL  
**Effort**: Medium (2 hours)  
**Impact**: High

#### Installation

```bash
pip install flask-wtf
```

#### Update requirements.txt

```text
Flask==3.0.0
Flask-Login==0.6.3
Flask-Talisman==1.1.0
Flask-WTF==1.2.1
Werkzeug==3.0.1
pymysql==1.1.0
python-dotenv==1.0.0
automationhat==1.0.0
```

#### Update app.py

Add after Flask app initialization:

```python
from flask_wtf.csrf import CSRFProtect

# Enable CSRF protection
csrf = CSRFProtect(app)
```

#### Update templates

Add CSRF token to all forms:

**templates/login.html**
```html
<form method="post">
    <input type="hidden" name="csrf_token" value="{{ csrf_token() }}"/>
    <!-- existing form fields -->
</form>
```

**templates/profile.html**
```html
<form method="post">
    <input type="hidden" name="csrf_token" value="{{ csrf_token() }}"/>
    <!-- existing form fields -->
</form>
```

#### Update JavaScript AJAX calls

For AJAX requests (like run_script), add CSRF token:

**templates/dashboard.html** (update script section):
```javascript
function runScript() {
    fetch('/run_script', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': '{{ csrf_token() }}'
        }
    })
    .then(response => response.json())
    .then(data => {
        // handle response
    });
}
```

---

### 3. Add Rate Limiting

**Priority**: HIGH  
**Effort**: Medium (1 hour)  
**Impact**: High

#### Installation

```bash
pip install flask-limiter
```

#### Update requirements.txt

```text
Flask==3.0.0
Flask-Login==0.6.3
Flask-Talisman==1.1.0
Flask-WTF==1.2.1
Flask-Limiter==3.5.0
Werkzeug==3.0.1
pymysql==1.1.0
python-dotenv==1.0.0
automationhat==1.0.0
```

#### Update app.py

Add after Flask app initialization:

```python
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

# Configure rate limiting
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://"  # Use Redis in production: "redis://localhost:6379"
)
```

Apply rate limits to sensitive endpoints:

```python
@app.route('/login', methods=['GET', 'POST'])
@limiter.limit("5 per 15 minutes")  # Prevent brute force
def login():
    # existing code
    
@app.route('/run_script', methods=['POST'])
@login_required
@limiter.limit("10 per minute")  # Prevent abuse
def run_script():
    # existing code
```

---

### 4. Secure Session Configuration

**Priority**: HIGH  
**Effort**: Low (15 minutes)  
**Impact**: Medium

#### Update app.py

Add after app configuration:

```python
from datetime import timedelta

# Secure session configuration
app.config['SESSION_COOKIE_SECURE'] = True  # HTTPS only (set False for dev)
app.config['SESSION_COOKIE_HTTPONLY'] = True  # Prevent JavaScript access
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'  # CSRF protection
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=24)
app.config['SESSION_COOKIE_NAME'] = '__Host-session'  # Requires HTTPS
```

**For development (HTTP)**, use:
```python
app.config['SESSION_COOKIE_SECURE'] = False
app.config['SESSION_COOKIE_NAME'] = 'session'  # Remove __Host- prefix
```

---

## Additional Improvements

### 5. Input Validation for Profile Fields

**Priority**: MEDIUM  
**Effort**: Low (30 minutes)

#### Update app.py

Add validation functions:

```python
import re

def validate_email(email):
    """Validate email format."""
    if not email:
        return True  # Allow empty
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_phone(phone):
    """Validate phone format."""
    if not phone:
        return True  # Allow empty
    # Accept various formats: +1-234-567-8900, (234) 567-8900, 234-567-8900
    pattern = r'^[\d\s\-\+\(\)]+$'
    if not re.match(pattern, phone):
        return False
    # Check reasonable length
    digits = re.sub(r'\D', '', phone)
    return 10 <= len(digits) <= 15
```

Update profile route:

```python
@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        try:
            email = request.form.get('email', '').strip()
            phone = request.form.get('phone', '').strip()
            
            # Validate input
            if email and not validate_email(email):
                flash('Invalid email format', 'error')
                return redirect(url_for('profile'))
            
            if phone and not validate_phone(phone):
                flash('Invalid phone format', 'error')
                return redirect(url_for('profile'))
            
            # Continue with existing logic
            # ...
```

---

### 6. Custom Error Pages

**Priority**: MEDIUM  
**Effort**: Medium (1 hour)

#### Create error templates

**templates/error.html**
```html
<!DOCTYPE html>
<html>
<head>
    <title>Error {{ error_code }}</title>
    <link rel="stylesheet" href="{{ url_for('static', filename='css/style.css') }}">
</head>
<body>
    <div class="error-container">
        <h1>{{ error_code }}</h1>
        <h2>{{ error_message }}</h2>
        <p>{{ error_description }}</p>
        <a href="{{ url_for('home') }}">Return to Home</a>
    </div>
</body>
</html>
```

#### Update app.py

Add error handlers:

```python
@app.errorhandler(400)
def bad_request(e):
    return render_template('error.html', 
        error_code=400,
        error_message='Bad Request',
        error_description='The server could not understand your request.'
    ), 400

@app.errorhandler(403)
def forbidden(e):
    return render_template('error.html',
        error_code=403,
        error_message='Forbidden',
        error_description='You do not have permission to access this resource.'
    ), 403

@app.errorhandler(404)
def not_found(e):
    return render_template('error.html',
        error_code=404,
        error_message='Page Not Found',
        error_description='The page you are looking for does not exist.'
    ), 404

@app.errorhandler(500)
def internal_error(e):
    logger.error(f"Internal server error: {str(e)}")
    return render_template('error.html',
        error_code=500,
        error_message='Internal Server Error',
        error_description='An unexpected error occurred. Please try again later.'
    ), 500
```

---

### 7. Dependency Vulnerability Scanning

**Priority**: MEDIUM  
**Effort**: Low (15 minutes)

#### Manual Dependency Scanning

For manual dependency vulnerability scanning, you can use tools like:

```bash
# Install safety for Python dependency checking
pip install safety

# Check for known vulnerabilities
safety check --file requirements.txt
```

#### Optional: Enable GitHub Security Features

If your repository is public or you have GitHub Advanced Security, you can optionally enable:

1. **GitHub Secret Scanning**
   - Go to repository Settings → Code security and analysis
   - Enable "Secret scanning" (if available)
   - Enable "Push protection" (if available)

2. **GitHub Dependabot**
   - Go to repository Settings → Code security and analysis
   - Enable "Dependabot alerts"
   - Enable "Dependabot security updates"

Note: These features may require specific GitHub plans or repository visibility settings.

---

### 8. Security Testing Script

**Priority**: MEDIUM  
**Effort**: Low (30 minutes)

Create `test_security.sh`:

```bash
#!/bin/bash
# Security testing script

echo "Running security tests..."

# Check for Bandit (Python security linter)
echo "1. Running Bandit security scan..."
if ! command -v bandit &> /dev/null; then
    echo "Installing Bandit..."
    pip install bandit
fi
bandit -r . -f json -o bandit-report.json -x ./venv,./env || true

# Check dependencies for known vulnerabilities
echo "2. Checking dependencies..."
if ! command -v safety &> /dev/null; then
    echo "Installing Safety..."
    pip install safety
fi
safety check --file requirements.txt || true

# Run existing security validation
echo "3. Running security validation..."
python validate_security.py

echo "Security tests complete!"
echo "Review bandit-report.json for detailed findings"
```

Make it executable:
```bash
chmod +x test_security.sh
```

---

## Testing Your Changes

### 1. Test Security Headers

```bash
# Start the application
python app.py

# In another terminal, check headers
curl -I http://localhost:5000/
```

Expected headers:
- `Strict-Transport-Security`
- `X-Content-Type-Options`
- `X-Frame-Options`
- `Content-Security-Policy`

### 2. Test CSRF Protection

Try submitting a form without CSRF token - should be rejected with 400 error.

### 3. Test Rate Limiting

```bash
# Try to login more than 5 times in 15 minutes
for i in {1..6}; do
    curl -X POST http://localhost:5000/login \
         -d "username=test&password=test"
done
```

Should see rate limit error on 6th attempt.

### 4. Verify Session Security

```python
# In Python console
from app import app
print(app.config['SESSION_COOKIE_SECURE'])  # Should be True
print(app.config['SESSION_COOKIE_HTTPONLY'])  # Should be True
```

---

## Production Deployment Checklist

Before deploying these changes to production:

- [ ] Update requirements.txt with new dependencies
- [ ] Install new dependencies: `pip install -r requirements.txt`
- [ ] Update all templates with CSRF tokens
- [ ] Test CSRF protection on all forms
- [ ] Configure rate limiting storage (Redis recommended)
- [ ] Set SESSION_COOKIE_SECURE=True (requires HTTPS)
- [ ] Test all endpoints after changes
- [ ] Run security validation: `python validate_security.py`
- [ ] Run security tests: `./test_security.sh`
- [ ] Enable GitHub security features (Dependabot, Code Scanning)
- [ ] Update documentation
- [ ] Train users on any changes

---

## Monitoring & Maintenance

### Regular Security Tasks

**Daily:**
- Monitor logs for failed login attempts
- Review security alerts

**Weekly:**
- Review security logs
- Check for security updates

**Monthly:**
- Update dependencies
- Review access controls
- Security patch testing

**Quarterly:**
- Full security audit
- Penetration testing
- Review and update security policies

---

## Rollback Plan

If issues occur after implementing these changes:

1. **Security Headers**: Comment out Talisman configuration in app.py
2. **CSRF Protection**: Disable CSRFProtect in app.py
3. **Rate Limiting**: Comment out Limiter configuration
4. **Session Security**: Revert session config to defaults

Keep previous working version available for quick rollback if needed.

---

## Support & Resources

- **Flask Security**: https://flask.palletsprojects.com/en/latest/security/
- **OWASP Top 10**: https://owasp.org/www-project-top-ten/
- **Flask-Talisman**: https://github.com/GoogleCloudPlatform/flask-talisman
- **Flask-WTF**: https://flask-wtf.readthedocs.io/
- **Flask-Limiter**: https://flask-limiter.readthedocs.io/

For questions or issues, create an issue in the repository.
