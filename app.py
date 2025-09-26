from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import subprocess
import os
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
from database import DatabaseManager

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your-secret-key-change-in-production')

# Initialize database manager
db_manager = DatabaseManager()

# Flask-Login setup
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

class User(UserMixin):
    def __init__(self, username, email=None, user_id=None):
        self.id = username
        self.username = username
        self.email = email
        self.user_id = user_id

@login_manager.user_loader
def load_user(user_id):
    user_data = db_manager.get_user(user_id)
    if user_data:
        return User(
            username=user_data['username'], 
            email=user_data.get('email'),
            user_id=user_data['id']
        )
    return None

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
        
        user_data = db_manager.get_user(username)
        if user_data and check_password_hash(user_data['password_hash'], password):
            user = User(
                username=user_data['username'], 
                email=user_data.get('email'),
                user_id=user_data['id']
            )
            login_user(user)
            return redirect(url_for('home'))
        else:
            flash('Invalid username or password')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/init_db')
def init_db():
    """Initialize the database and create default admin user"""
    try:
        # Create users table
        db_manager.create_users_table()
        
        # Check if admin user exists, if not create it
        admin_user = db_manager.get_user('admin')
        if not admin_user:
            admin_password_hash = generate_password_hash('mypassword')
            db_manager.create_user('admin', admin_password_hash, 'admin@garage.com')
            flash('Database initialized and admin user created successfully!')
        else:
            flash('Database already initialized!')
        
        return redirect(url_for('login'))
    except Exception as e:
        flash(f'Error initializing database: {str(e)}')
        return redirect(url_for('login'))

@app.route('/create_user', methods=['POST'])
@login_required
def create_user():
    """Create a new user (admin only functionality)"""
    if current_user.username != 'admin':
        flash('Only admin can create new users')
        return redirect(url_for('home'))
    
    username = request.form.get('username')
    password = request.form.get('password')
    email = request.form.get('email')
    
    if username and password:
        password_hash = generate_password_hash(password)
        if db_manager.create_user(username, password_hash, email):
            flash(f'User {username} created successfully!')
        else:
            flash('Error creating user')
    else:
        flash('Username and password are required')
    
    return redirect(url_for('home'))

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

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)