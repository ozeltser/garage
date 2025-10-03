from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import subprocess
import os
import logging
from dotenv import load_dotenv
from database import DatabaseManager

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
    def __init__(self, username, user_id=None):
        self.id = username
        self.user_id = user_id

@login_manager.user_loader
def load_user(user_id):
    """Load user from database by username."""
    user_data = db_manager.get_user_by_username(user_id)
    if user_data:
        return User(user_data['username'], user_data['id'])
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
        
        try:
            if db_manager.verify_password(username, password):
                user_data = db_manager.get_user_by_username(username)
                if user_data:
                    user = User(user_data['username'], user_data['id'])
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
    host = os.getenv('APP_HOST', '0.0.0.0')
    port = int(os.getenv('APP_PORT', 5000))
    debug = os.getenv('FLASK_DEBUG', 'True').lower() == 'true'
    
    logger.info(f"Starting Garage Web App on {host}:{port} (debug={debug})")
    app.run(debug=debug, host=host, port=port)