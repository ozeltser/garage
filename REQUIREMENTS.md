# Requirements Documentation

This document explains the dependency structure for the Garage Web Application.

## Requirements Files Overview

### `requirements.txt` (Main)
The primary requirements file that includes core application dependencies. Use this for standard installations.

### `requirements-core.txt`
Contains all essential packages needed to run the web application:
- **Flask 3.0.0**: Web framework
- **Flask-Login 0.6.3**: User authentication management
- **Werkzeug 3.0.1**: WSGI toolkit (Flask dependency)
- **mysql-connector-python 8.2.0**: MySQL database connector
- **python-dotenv 1.0.0**: Environment variable management
- **Jinja2, MarkupSafe, itsdangerous, click, blinker**: Flask dependencies

### `requirements-hardware.txt`
Hardware-specific dependencies for Raspberry Pi:
- **automationhat 3.4**: Raspberry Pi Automation HAT library

### `requirements-dev.txt`
Development and testing tools:
- **pytest**: Testing framework
- **pytest-flask**: Flask testing utilities
- **black**: Code formatter
- **flake8**: Code linter
- **mypy**: Type checker

## Installation Instructions

### Standard Web Application
```bash
pip install -r requirements.txt
```

### Raspberry Pi with Hardware Control
```bash
pip install -r requirements.txt -r requirements-hardware.txt
```

### Development Environment
```bash
pip install -r requirements-dev.txt
```

## Dependency Analysis

### Core Dependencies
All core dependencies are properly specified with exact versions for reproducibility.

### Optional Dependencies
Hardware-specific packages are separated to avoid installation issues on non-Raspberry Pi systems.

### Version Pinning Strategy
- **Exact versions** for core packages to ensure stability
- **Minimum versions** (>=) for Flask dependencies to allow compatible updates
- **Latest stable versions** as of the implementation date

## Environment Compatibility

### Python Version
- **Minimum**: Python 3.7
- **Recommended**: Python 3.11+
- **Tested**: Python 3.11.9

### Operating Systems
- **Windows**: Fully supported
- **Linux**: Fully supported (including Raspberry Pi OS)
- **macOS**: Fully supported

### Database Support
- **MySQL 8.0+**: Primary target (Azure MySQL)
- **MariaDB 10.3+**: Compatible
- **MySQL 5.7+**: Should work but not recommended

## Security Considerations

### Package Sources
All packages are installed from PyPI (Python Package Index).

### Version Security
- Regular security updates should be applied
- Monitor for security advisories for all dependencies
- Consider using tools like `safety` for vulnerability scanning

### Production Recommendations
1. Use virtual environments
2. Pin exact versions in production
3. Regularly update dependencies
4. Scan for vulnerabilities
5. Use requirement freezing: `pip freeze > requirements-frozen.txt`

## Troubleshooting

### Common Issues

**Import Error for automationhat**
- Solution: Install hardware requirements or run on Raspberry Pi
- Workaround: Comment out automationhat import if not using hardware

**MySQL Connection Issues**
- Ensure mysql-connector-python is installed
- Check Azure MySQL firewall settings
- Verify SSL certificate configuration

**Flask Import Errors**
- Ensure all Flask dependencies are installed
- Try reinstalling with: `pip install --force-reinstall Flask`

### Verification Commands

Check installed packages:
```bash
pip list
```

Verify specific package:
```bash
pip show Flask
```

Test imports:
```bash
python -c "import flask, flask_login, mysql.connector, dotenv; print('All imports successful')"
```

## Maintenance

### Regular Updates
Review and update dependencies quarterly or when security updates are available.

### Testing Updates
Always test dependency updates in a development environment before production deployment.

### Documentation
Keep this documentation updated when adding or removing dependencies.
