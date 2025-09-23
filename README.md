# Garage Web App

A Python Flask web application that provides a secure login interface and allows authenticated users to execute Python scripts on the server. The application is designed to be responsive and work well on both mobile and desktop browsers.

## Features

- 🔐 **Secure Authentication**: User login system with session management
- 📱 **Responsive Design**: Optimized for both mobile and desktop browsers
- 🖥️ **Script Execution**: Execute Python scripts on the server with a simple button click
- 🎨 **Modern UI**: Clean, Bootstrap-based interface with smooth animations
- ⚡ **Real-time Feedback**: AJAX-based script execution with loading indicators
- 📊 **Output Display**: View script output and errors in real-time

## Quick Start

### Prerequisites

- Python 3.7 or higher
- pip (Python package installer)

### Installation

1. Clone this repository:
   ```bash
   git clone <repository-url>
   cd garage
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run the application:
   ```bash
   python app.py
   ```

4. Open your browser and navigate to:
   ```
   http://localhost:5000
   ```

### Default Credentials

- **Username**: `admin`
- **Password**: `password`

## Project Structure

```
garage/
├── app.py                 # Main Flask application
├── requirements.txt       # Python dependencies
├── sample_script.py       # Example Python script to execute
├── templates/
│   ├── base.html         # Base template with common layout
│   ├── login.html        # Login page template
│   └── dashboard.html    # Dashboard template
└── static/
    ├── css/
    │   └── style.css     # Custom styles for responsive design
    └── js/
        └── app.js        # JavaScript for AJAX and interactions
```

## Configuration

### Security
- Change the `SECRET_KEY` in `app.py` for production use
- Update the default credentials in the `users` dictionary
- Consider using a proper database for user management in production

### Script Customization
- Edit `sample_script.py` to customize what runs when the button is clicked
- The script output (stdout) and errors (stderr) are displayed in the web interface
- Scripts have a 30-second timeout limit

## Responsive Design

The application uses Bootstrap 5 and custom CSS to provide:
- **Mobile-first approach**: Optimized for smartphones and tablets
- **Flexible layouts**: Adapts to different screen sizes
- **Touch-friendly controls**: Large buttons and touch interactions
- **Readable typography**: Proper font sizing for all devices

## Technology Stack

- **Backend**: Flask (Python web framework)
- **Frontend**: HTML5, CSS3, JavaScript, Bootstrap 5
- **Authentication**: Flask-Login
- **Security**: Werkzeug password hashing

## API Endpoints

- `GET /`: Home page (redirects to login if not authenticated)
- `GET /login`: Login page
- `POST /login`: Process login credentials
- `GET /logout`: Logout and redirect to login
- `POST /run_script`: Execute the Python script (requires authentication)

## Development

### Running in Debug Mode
The application runs in debug mode by default. For production:

```python
app.run(debug=False, host='0.0.0.0', port=5000)
```

### Adding New Scripts
1. Create your Python script in the project directory
2. Update the `run_script()` function in `app.py` to execute your script
3. Ensure proper error handling and timeout management

## Security Considerations

- This is a development/demo application
- In production, use proper HTTPS
- Implement proper user management with a database
- Add CSRF protection
- Validate and sanitize all inputs
- Use environment variables for sensitive configuration

## License

This project is open source and available under the MIT License.