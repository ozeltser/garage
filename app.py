from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from functools import wraps
import subprocess
import os
import logging
from dotenv import load_dotenv
from database import DatabaseManager
from user_roles import UserRole

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your-secret-key-change-in-production')

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize database manager
try:
    db_manager = DatabaseManager()
except Exception as e:
    logger.error(f"Failed to initialize database: {str(e)}")
    raise

# Flask-Login setup
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

class User(UserMixin):
    def __init__(self, username, user_id=None, role=None):
        self.id = username
        self.user_id = user_id
        self.role = role if role else UserRole.REGULAR.value
    
    def is_admin(self):
        return self.role == UserRole.ADMIN.value

@login_manager.user_loader
def load_user(user_id):
    """Load user from database by username."""
    user_data = db_manager.get_user_by_username(user_id)
    if user_data:
        return User(user_data['username'], user_data['id'], user_data.get('role', UserRole.REGULAR.value))
    return None

def admin_required(f):
    """Decorator to require admin role for a route."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin():
            flash('Access denied. Admin privileges required.', 'error')
            return redirect(url_for('home'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def home():
    if current_user.is_authenticated:
        return render_template('dashboard.html')
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        try:
            if db_manager.verify_password(username, password):
                user_data = db_manager.get_user_by_username(username)
                if user_data:
                    user = User(user_data['username'], user_data['id'], user_data.get('role', UserRole.REGULAR.value))
                    login_user(user)
                    logger.info(f"User '{username}' logged in successfully")
                    return redirect(url_for('home'))
            
            logger.warning(f"Failed login attempt for username: {username}")
            flash('Invalid username or password')
        except Exception as e:
            logger.error(f"Login error for user {username}: {str(e)}")
            flash('An error occurred during login. Please try again.')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        try:
            # Get form data
            first_name = request.form.get('first_name', '').strip()
            last_name = request.form.get('last_name', '').strip()
            email = request.form.get('email', '').strip()
            phone = request.form.get('phone', '').strip()
            
            # Update profile
            if db_manager.update_user_profile(
                current_user.id, 
                first_name if first_name else None,
                last_name if last_name else None,
                email if email else None,
                phone if phone else None
            ):
                flash('Profile updated successfully', 'success')
                
                # Handle password change if provided
                current_password = request.form.get('current_password', '').strip()
                new_password = request.form.get('new_password', '').strip()
                confirm_password = request.form.get('confirm_password', '').strip()
                
                if new_password:
                    if not current_password:
                        flash('Current password is required to change password', 'error')
                    elif new_password != confirm_password:
                        flash('New passwords do not match', 'error')
                    elif not db_manager.verify_password(current_user.id, current_password):
                        flash('Current password is incorrect', 'error')
                    else:
                        if db_manager.update_password(current_user.id, new_password):
                            flash('Password updated successfully', 'success')
                        else:
                            flash('Failed to update password', 'error')
            else:
                flash('Failed to update profile', 'error')
                
        except Exception as e:
            logger.error(f"Profile update error for user {current_user.id}: {str(e)}")
            flash('An error occurred while updating profile. Please try again.', 'error')
        
        return redirect(url_for('profile'))
    
    # GET request - display profile form
    user_data = db_manager.get_user_by_username(current_user.id)
    return render_template('profile.html', user=user_data)

@app.route('/run_script', methods=['POST'])
@login_required
def run_script():
    try:
        # Run the sample Python script using an absolute, whitelisted path
        script_dir = os.path.dirname(os.path.abspath(__file__))
        script_path = os.path.join(script_dir, 'relay.py')
        result = subprocess.run(['python', script_path],
                              capture_output=True, text=True, timeout=30)
        return jsonify({
            'success': True,
            'output': result.stdout,
            'error': result.stderr
        })
    except subprocess.TimeoutExpired:
        return jsonify({
            'success': False,
            'error': 'Script execution timed out'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/door_status', methods=['GET'])
@login_required
def door_status():
    try:
        # Run the doorStatus.py script to get current door status
        script_dir = os.path.dirname(os.path.abspath(__file__))
        script_path = os.path.join(script_dir, 'doorStatus.py')
        result = subprocess.run(['python', script_path],
                              capture_output=True, text=True, timeout=10)
        
        # Parse the output to determine door status
        output = result.stdout.strip()
        error_output = result.stderr.strip()
        
        if 'Door Closed' in output:
            status = 'closed'
        elif 'Door Opened' in output:
            status = 'open'
        else:
            # Default to unknown if we can't determine status
            status = 'unknown'
        
        return jsonify({
            'success': True,
            'status': status,
            'raw_output': output,
            'error': error_output if error_output else None
        })
    except subprocess.TimeoutExpired:
        return jsonify({
            'success': False,
            'error': 'Door status check timed out'
        })
    except Exception as e:
        logger.error(f"Error checking door status: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/admin')
@login_required
@admin_required
def admin():
    """Admin dashboard."""
    users = db_manager.get_all_users()
    return render_template('admin.html', users=users)

@app.route('/admin/create_user', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_create_user():
    """Create a new user (admin only)."""
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        confirm_password = request.form.get('confirm_password', '').strip()
        role = request.form.get('role', UserRole.REGULAR.value)
        
        if not username or not password:
            flash('Username and password are required', 'error')
        elif password != confirm_password:
            flash('Passwords do not match', 'error')
        elif not UserRole.is_valid(role):
            flash('Invalid role specified', 'error')
        else:
            if db_manager.create_user(username, password, role):
                flash(f'User {username} created successfully', 'success')
                return redirect(url_for('admin'))
            else:
                flash(f'Failed to create user {username}. Username may already exist.', 'error')
    
    return render_template('create_user.html')

@app.route('/admin/delete_user/<username>', methods=['POST'])
@login_required
@admin_required
def admin_delete_user(username):
    """Delete a user (admin only)."""
    if username == current_user.id:
        flash('You cannot delete your own account', 'error')
    elif db_manager.delete_user(username):
        flash(f'User {username} deleted successfully', 'success')
    else:
        flash(f'Failed to delete user {username}', 'error')
    
    return redirect(url_for('admin'))

@app.route('/admin/change_password/<username>', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_change_password(username):
    """Change a user's password (admin only)."""
    if request.method == 'POST':
        new_password = request.form.get('new_password', '').strip()
        confirm_password = request.form.get('confirm_password', '').strip()
        
        if not new_password:
            flash('Password is required', 'error')
        elif new_password != confirm_password:
            flash('Passwords do not match', 'error')
        else:
            if db_manager.update_user_password_by_admin(username, new_password):
                flash(f'Password updated successfully for user {username}', 'success')
                return redirect(url_for('admin'))
            else:
                flash(f'Failed to update password for user {username}', 'error')
    
    user_data = db_manager.get_user_by_username(username)
    if not user_data:
        flash(f'User {username} not found', 'error')
        return redirect(url_for('admin'))
    
    return render_template('change_password.html', user=user_data)

if __name__ == '__main__':
    host = os.getenv('APP_HOST', '0.0.0.0')
    port = int(os.getenv('APP_PORT', 5000))
    debug = os.getenv('FLASK_DEBUG', 'True').lower() == 'true'
    
    logger.info(f"Starting Garage Web App on {host}:{port} (debug={debug})")
    app.run(debug=debug, host=host, port=port)