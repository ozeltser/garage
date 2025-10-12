# Production Deployment Guide for Raspberry Pi

This guide provides detailed instructions for deploying the Garage Web App on a Raspberry Pi in a production environment.

## Table of Contents

1. [Hardware Requirements](#hardware-requirements)
2. [Raspberry Pi Setup](#raspberry-pi-setup)
3. [Software Installation](#software-installation)
4. [Database Setup](#database-setup)
5. [Application Configuration](#application-configuration)
6. [Systemd Service Setup](#systemd-service-setup)
7. [Nginx Reverse Proxy (HTTPS)](#nginx-reverse-proxy-https)
8. [Automation HAT Configuration](#automation-hat-configuration)
9. [Security Hardening](#security-hardening)
10. [Backup and Restore](#backup-and-restore)
11. [Monitoring and Maintenance](#monitoring-and-maintenance)
12. [Troubleshooting](#troubleshooting)
13. [Updates and Upgrades](#updates-and-upgrades)

---

## Hardware Requirements

### Required Hardware
- **Raspberry Pi 3 Model B+ or newer** (Raspberry Pi 4 recommended for better performance)
- **Pimoroni Automation HAT** (for relay and sensor control)
- **MicroSD Card** - 16GB or larger (Class 10 recommended)
- **Power Supply** - Official Raspberry Pi power supply (5V 3A for Pi 4, 5V 2.5A for Pi 3)
- **Ethernet cable or WiFi connection**

### Optional Hardware
- **Case with cooling** (recommended for 24/7 operation)
- **UPS/Battery backup** (for reliable operation during power outages)
- **External storage** (USB drive for backups)

### Network Requirements
- **Static IP address** (recommended for production)
- **Port access** (443 for HTTPS, 3306 for MySQL if remote)
- **Internet access** (for initial setup and updates)

---

## Raspberry Pi Setup

### 1. Install Raspberry Pi OS

1. Download **Raspberry Pi OS Lite (64-bit)** from [https://www.raspberrypi.com/software/](https://www.raspberrypi.com/software/)
2. Use Raspberry Pi Imager to write the image to your microSD card
3. Enable SSH before first boot:
   - Create an empty file named `ssh` in the boot partition
   - Or use Raspberry Pi Imager's advanced options (Ctrl+Shift+X)

### 2. Initial Configuration

Boot the Raspberry Pi and connect via SSH:

```bash
# Default credentials (change immediately!)
# Username: pi
# Password: raspberry

ssh pi@raspberrypi.local
# or
ssh pi@<raspberry-pi-ip-address>
```

Run the configuration tool:

```bash
sudo raspi-config
```

**Recommended configurations:**
- Change default password (System Options → Password)
- Set hostname (System Options → Hostname)
- Configure WiFi if needed (System Options → Wireless LAN)
- Set timezone (Localisation Options → Timezone)
- Expand filesystem (Advanced Options → Expand Filesystem)
- Enable I2C for Automation HAT (Interface Options → I2C)
- Enable SPI for Automation HAT (Interface Options → SPI)

### 3. Update System

```bash
sudo apt update
sudo apt upgrade -y
sudo apt autoremove -y
sudo reboot
```

### 4. Set Static IP Address (Recommended)

Edit the dhcpcd configuration:

```bash
sudo nano /etc/dhcpcd.conf
```

Add at the end (adjust for your network):

```conf
# Static IP configuration
interface eth0
static ip_address=192.168.1.100/24
static routers=192.168.1.1
static domain_name_servers=192.168.1.1 8.8.8.8

# For WiFi, use wlan0 instead
# interface wlan0
# static ip_address=192.168.1.100/24
# static routers=192.168.1.1
# static domain_name_servers=192.168.1.1 8.8.8.8
```

Restart networking:

```bash
sudo systemctl restart dhcpcd
```

---

## Software Installation

### 1. Install System Dependencies

```bash
# Install Python 3 and pip
sudo apt install -y python3 python3-pip python3-venv

# Install MySQL/MariaDB server
sudo apt install -y mariadb-server mariadb-client

# Install Nginx (reverse proxy for HTTPS)
sudo apt install -y nginx

# Install git
sudo apt install -y git

# Install system libraries for Python packages
sudo apt install -y python3-dev build-essential libssl-dev libffi-dev

# Install I2C and SPI tools for Automation HAT
sudo apt install -y i2c-tools python3-smbus python3-spidev

# Install certbot for Let's Encrypt SSL (optional)
sudo apt install -y certbot python3-certbot-nginx
```

### 2. Create Application User

Create a dedicated user for running the application:

```bash
sudo adduser --system --group --home /opt/garage garage
sudo usermod -a -G gpio,i2c,spi garage  # Add to hardware access groups
```

### 3. Clone the Application

```bash
# Switch to the garage user
sudo su - garage

# Clone the repository
cd /opt/garage
git clone https://github.com/ozeltser/garage.git app
cd app

# Or if already cloned elsewhere, copy files
# sudo cp -r /path/to/garage /opt/garage/app
# sudo chown -R garage:garage /opt/garage/app
```

### 4. Create Python Virtual Environment

```bash
# As garage user
cd /opt/garage/app
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Exit back to your regular user
exit
```

---

## Database Setup

### 1. Secure MySQL Installation

```bash
sudo mysql_secure_installation
```

Answer the prompts:
- Set root password: **Yes** (choose a strong password)
- Remove anonymous users: **Yes**
- Disallow root login remotely: **Yes**
- Remove test database: **Yes**
- Reload privilege tables: **Yes**

### 2. Create Application Database and User

```bash
sudo mysql -u root -p
```

Run these SQL commands:

```sql
-- Create database
CREATE DATABASE garage_app CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- Create user (use a strong password)
CREATE USER 'garage_user'@'localhost' IDENTIFIED BY 'YOUR-STRONG-PASSWORD-HERE';

-- Grant privileges
GRANT SELECT, INSERT, UPDATE, DELETE ON garage_app.* TO 'garage_user'@'localhost';
FLUSH PRIVILEGES;

-- Exit MySQL
EXIT;
```

### 3. Optimize MySQL for Raspberry Pi

Edit MySQL configuration:

```bash
sudo nano /etc/mysql/mariadb.conf.d/50-server.cnf
```

Add/modify these settings in the `[mysqld]` section:

```ini
[mysqld]
# Optimize for low memory (Raspberry Pi)
max_connections = 20
innodb_buffer_pool_size = 128M
innodb_log_file_size = 32M
query_cache_size = 8M
query_cache_limit = 1M

# Bind to localhost only (for security)
bind-address = 127.0.0.1
```

Restart MySQL:

```bash
sudo systemctl restart mariadb
```

---

## Application Configuration

### 1. Create Environment File

```bash
sudo su - garage
cd /opt/garage/app

# Copy example and edit
cp .env.example .env
nano .env
```

Configure the `.env` file:

```bash
# Flask configuration
SECRET_KEY=GENERATE-A-STRONG-SECRET-KEY-HERE-USE-RANDOM-STRING
FLASK_ENV=production
FLASK_DEBUG=False

# Application settings
APP_HOST=127.0.0.1  # Only localhost, nginx will handle external access
APP_PORT=5000

# MySQL Database Configuration
DB_HOST=localhost
DB_PORT=3306
DB_NAME=garage_app
DB_USER=garage_user
DB_PASSWORD=YOUR-STRONG-PASSWORD-HERE

# Default admin credentials (for initial setup only)
DEFAULT_USERNAME=admin
DEFAULT_PASSWORD=CHANGE-THIS-SECURE-PASSWORD
```

**Generate a strong SECRET_KEY:**

```bash
python3 -c 'import secrets; print(secrets.token_hex(32))'
```

### 2. Initialize Database

```bash
# As garage user
cd /opt/garage/app
source venv/bin/activate
python init_db.py
deactivate
exit
```

### 3. Set Proper Permissions

```bash
# Ensure files are owned by garage user
sudo chown -R garage:garage /opt/garage/app

# Protect sensitive files
sudo chmod 600 /opt/garage/app/.env
sudo chmod 755 /opt/garage/app/*.py
```

### 4. Test Application

```bash
sudo su - garage
cd /opt/garage/app
source venv/bin/activate
python app.py
```

Access from another computer: `http://<raspberry-pi-ip>:5000`

If it works, stop it (Ctrl+C) and exit:

```bash
deactivate
exit
```

---

## Systemd Service Setup

### 1. Create Systemd Service File

```bash
sudo nano /etc/systemd/system/garage.service
```

Add the following content:

```ini
[Unit]
Description=Garage Web Application
After=network.target mariadb.service
Wants=mariadb.service

[Service]
Type=simple
User=garage
Group=garage
WorkingDirectory=/opt/garage/app
Environment="PATH=/opt/garage/app/venv/bin"
ExecStart=/opt/garage/app/venv/bin/python /opt/garage/app/app.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier=garage-app

# Security hardening
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/opt/garage/app
ProtectKernelTunables=true
ProtectControlGroups=true

[Install]
WantedBy=multi-user.target
```

### 2. Enable and Start Service

```bash
# Reload systemd to recognize new service
sudo systemctl daemon-reload

# Enable service to start on boot
sudo systemctl enable garage.service

# Start the service
sudo systemctl start garage.service

# Check status
sudo systemctl status garage.service
```

### 3. Manage the Service

```bash
# Start service
sudo systemctl start garage.service

# Stop service
sudo systemctl stop garage.service

# Restart service
sudo systemctl restart garage.service

# View logs
sudo journalctl -u garage.service -f

# View last 100 lines
sudo journalctl -u garage.service -n 100
```

---

## Nginx Reverse Proxy (HTTPS)

### 1. Create Nginx Configuration

```bash
sudo nano /etc/nginx/sites-available/garage
```

Add this configuration:

```nginx
# HTTP server - redirect to HTTPS
server {
    listen 80;
    server_name garage.yourdomain.com;  # Change to your domain or IP

    # For Let's Encrypt certificate generation
    location /.well-known/acme-challenge/ {
        root /var/www/html;
    }

    # Redirect all other traffic to HTTPS
    location / {
        return 301 https://$server_name$request_uri;
    }
}

# HTTPS server
server {
    listen 443 ssl http2;
    server_name garage.yourdomain.com;  # Change to your domain or IP

    # SSL certificate paths (update after obtaining certificates)
    ssl_certificate /etc/letsencrypt/live/garage.yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/garage.yourdomain.com/privkey.pem;

    # SSL configuration
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;

    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # Logging
    access_log /var/log/nginx/garage_access.log;
    error_log /var/log/nginx/garage_error.log;

    # Proxy settings
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket support (if needed in future)
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # Static files (optional, for performance)
    location /static {
        alias /opt/garage/app/static;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
}
```

### 2. Enable Nginx Configuration

```bash
# Create symbolic link to enable site
sudo ln -s /etc/nginx/sites-available/garage /etc/nginx/sites-enabled/

# Remove default site (optional)
sudo rm /etc/nginx/sites-enabled/default

# Test nginx configuration
sudo nginx -t

# Restart nginx
sudo systemctl restart nginx
```

### 3. Obtain SSL Certificate (Let's Encrypt)

**For domain-based setup:**

```bash
# Make sure your domain points to your Raspberry Pi's public IP
# Then run:
sudo certbot --nginx -d garage.yourdomain.com
```

**For local network / self-signed certificate:**

```bash
# Generate self-signed certificate (for local network use)
sudo mkdir -p /etc/nginx/ssl
sudo openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout /etc/nginx/ssl/garage.key \
  -out /etc/nginx/ssl/garage.crt

# Update nginx config to use these certificates instead
sudo nano /etc/nginx/sites-available/garage
```

For self-signed, update the SSL certificate paths in nginx config:

```nginx
ssl_certificate /etc/nginx/ssl/garage.crt;
ssl_certificate_key /etc/nginx/ssl/garage.key;
```

### 4. Configure Firewall (Optional but Recommended)

```bash
# Install ufw if not installed
sudo apt install -y ufw

# Allow SSH (important - don't lock yourself out!)
sudo ufw allow 22/tcp

# Allow HTTP and HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Enable firewall
sudo ufw enable

# Check status
sudo ufw status
```

---

## Automation HAT Configuration

### 1. Verify Automation HAT Installation

```bash
# Check I2C devices
sudo i2cdetect -y 1

# Should show devices at addresses like 0x54, 0x48, etc.
```

### 2. Test Automation HAT

```bash
sudo su - garage
cd /opt/garage/app
source venv/bin/activate

# Test relay script
python relay.py

# Test door status script
python doorStatus.py

deactivate
exit
```

### 3. Configure GPIO Permissions

The garage user should already have access via the gpio, i2c, and spi groups.
Verify with:

```bash
groups garage
# Should show: garage gpio i2c spi
```

If not, add the user to required groups:

```bash
sudo usermod -a -G gpio,i2c,spi garage
```

### 4. Hardware Wiring Guide

**Automation HAT Connections:**

- **Relay 1**: Connect to garage door opener (normally-open contacts)
  - COM (Common) → Garage door opener terminal 1
  - NO (Normally Open) → Garage door opener terminal 2
  
- **Input 1**: Connect to garage door sensor (for status monitoring)
  - 5V → Door sensor positive
  - Input 1 → Door sensor signal
  - GND → Door sensor ground

**Safety Notes:**
- Always disconnect power before wiring
- Use appropriate voltage levels (Automation HAT is 5V/3.3V)
- Test connections with a multimeter before applying power
- Ensure proper grounding to prevent damage

---

## Security Hardening

### 1. System Security

```bash
# Disable root SSH login
sudo nano /etc/ssh/sshd_config
# Set: PermitRootLogin no
# Set: PasswordAuthentication no  # If using SSH keys
sudo systemctl restart ssh

# Keep system updated
sudo apt update && sudo apt upgrade -y

# Install fail2ban to prevent brute force attacks
sudo apt install -y fail2ban
sudo systemctl enable fail2ban
sudo systemctl start fail2ban
```

### 2. Application Security

**Update .env file:**
- Use strong, unique passwords
- Generate strong SECRET_KEY
- Set FLASK_DEBUG=False
- Restrict APP_HOST to 127.0.0.1

**Database Security:**
- Regular backups (see Backup section)
- Strong database passwords
- Limit database user privileges
- Keep MariaDB updated

**Network Security:**
- Use HTTPS only (enforce with nginx)
- Configure firewall (ufw)
- Use static IP with MAC filtering on router
- Consider VPN for remote access

### 3. Monitoring and Alerts

Create a simple monitoring script:

```bash
sudo nano /opt/garage/monitor.sh
```

Add:

```bash
#!/bin/bash
# Simple monitoring script

# Check if garage service is running
if ! systemctl is-active --quiet garage.service; then
    echo "Garage service is down!" | mail -s "ALERT: Garage Service Down" your-email@example.com
    systemctl restart garage.service
fi

# Check if nginx is running
if ! systemctl is-active --quiet nginx; then
    echo "Nginx is down!" | mail -s "ALERT: Nginx Down" your-email@example.com
    systemctl restart nginx
fi

# Check if database is running
if ! systemctl is-active --quiet mariadb; then
    echo "Database is down!" | mail -s "ALERT: Database Down" your-email@example.com
    systemctl restart mariadb
fi
```

Make executable and add to cron:

```bash
sudo chmod +x /opt/garage/monitor.sh
sudo crontab -e
# Add: */5 * * * * /opt/garage/monitor.sh
```

---

## Backup and Restore

### 1. Database Backup Script

Create backup script:

```bash
sudo nano /opt/garage/backup.sh
```

Add:

```bash
#!/bin/bash
# Garage App Backup Script

BACKUP_DIR="/opt/garage/backups"
DATE=$(date +%Y%m%d_%H%M%S)
DB_NAME="garage_app"
DB_USER="garage_user"
DB_PASS="YOUR-DB-PASSWORD"  # Or read from .env

# Create backup directory
mkdir -p $BACKUP_DIR

# Backup database
mysqldump -u $DB_USER -p$DB_PASS $DB_NAME > $BACKUP_DIR/db_backup_$DATE.sql

# Backup application files and configuration
tar -czf $BACKUP_DIR/app_backup_$DATE.tar.gz -C /opt/garage/app .env *.py templates/ static/

# Keep only last 7 days of backups
find $BACKUP_DIR -name "*.sql" -mtime +7 -delete
find $BACKUP_DIR -name "*.tar.gz" -mtime +7 -delete

# Optional: Copy to external USB drive or network storage
# cp $BACKUP_DIR/*_$DATE.* /media/usb/garage_backups/

echo "Backup completed: $DATE"
```

Make executable:

```bash
sudo chmod +x /opt/garage/backup.sh
sudo chown garage:garage /opt/garage/backup.sh
```

Schedule daily backups:

```bash
sudo crontab -e -u garage
# Add: 0 2 * * * /opt/garage/backup.sh >> /opt/garage/backup.log 2>&1
```

### 2. Restore from Backup

```bash
#!/bin/bash
# Restore script

BACKUP_FILE="$1"

if [ -z "$BACKUP_FILE" ]; then
    echo "Usage: $0 <backup_file.sql>"
    exit 1
fi

# Stop service
sudo systemctl stop garage.service

# Restore database
mysql -u garage_user -p garage_app < $BACKUP_FILE

# Restart service
sudo systemctl start garage.service

echo "Restore completed"
```

---

## Monitoring and Maintenance

### 1. View Application Logs

```bash
# Real-time logs
sudo journalctl -u garage.service -f

# Last 100 lines
sudo journalctl -u garage.service -n 100

# Logs from today
sudo journalctl -u garage.service --since today

# Logs with errors only
sudo journalctl -u garage.service -p err
```

### 2. Monitor System Resources

```bash
# Check memory usage
free -h

# Check disk usage
df -h

# Check CPU temperature
vcgencmd measure_temp

# Check running processes
htop
# or
top
```

### 3. Database Maintenance

```bash
# Optimize database tables
mysql -u garage_user -p garage_app -e "OPTIMIZE TABLE users;"

# Check database size
mysql -u root -p -e "SELECT table_schema AS 'Database', ROUND(SUM(data_length + index_length) / 1024 / 1024, 2) AS 'Size (MB)' FROM information_schema.TABLES WHERE table_schema = 'garage_app' GROUP BY table_schema;"
```

### 4. Regular Maintenance Tasks

**Daily:**
- Check service status
- Review logs for errors

**Weekly:**
- Check disk space
- Review backup status
- Update system packages: `sudo apt update && sudo apt upgrade`

**Monthly:**
- Review security logs
- Test backup restoration
- Check SSL certificate expiration
- Update application dependencies if needed

---

## Troubleshooting

### Service Won't Start

```bash
# Check service status
sudo systemctl status garage.service

# View detailed logs
sudo journalctl -u garage.service -n 50

# Common issues:
# 1. Database not running
sudo systemctl status mariadb

# 2. Permission issues
sudo chown -R garage:garage /opt/garage/app
sudo chmod 600 /opt/garage/app/.env

# 3. Port already in use
sudo netstat -tlnp | grep :5000
```

### Database Connection Issues

```bash
# Test database connection
mysql -u garage_user -p garage_app

# Check MySQL is running
sudo systemctl status mariadb

# Restart MySQL
sudo systemctl restart mariadb

# Check MySQL logs
sudo journalctl -u mariadb -n 50
```

### Nginx Issues

```bash
# Test nginx configuration
sudo nginx -t

# Check nginx status
sudo systemctl status nginx

# View nginx error logs
sudo tail -f /var/log/nginx/garage_error.log

# Restart nginx
sudo systemctl restart nginx
```

### Automation HAT Not Detected

```bash
# Check I2C is enabled
sudo raspi-config
# Interface Options → I2C → Enable

# Check I2C devices
sudo i2cdetect -y 1

# Check user groups
groups garage

# Reinstall automationhat library
sudo su - garage
cd /opt/garage/app
source venv/bin/activate
pip install --upgrade automationhat
deactivate
exit
```

### High CPU or Memory Usage

```bash
# Check processes
htop

# Restart service to clear memory
sudo systemctl restart garage.service

# Check for memory leaks in logs
sudo journalctl -u garage.service | grep -i memory

# Optimize database
mysql -u garage_user -p garage_app -e "OPTIMIZE TABLE users;"
```

### SSL Certificate Issues

```bash
# Renew Let's Encrypt certificate
sudo certbot renew

# Test certificate renewal
sudo certbot renew --dry-run

# Check certificate expiration
sudo certbot certificates

# For self-signed certificates, regenerate if expired
sudo openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout /etc/nginx/ssl/garage.key \
  -out /etc/nginx/ssl/garage.crt
```

---

## Updates and Upgrades

### 1. Update Application Code

```bash
# Stop service
sudo systemctl stop garage.service

# Backup current version
sudo su - garage
cd /opt/garage
cp -r app app.backup.$(date +%Y%m%d)

# Pull latest code
cd app
git pull origin main

# Update dependencies
source venv/bin/activate
pip install --upgrade -r requirements.txt
deactivate

# Run any database migrations if needed
source venv/bin/activate
python migrate_db.py
deactivate

exit

# Restart service
sudo systemctl start garage.service
sudo systemctl status garage.service
```

### 2. Update System Packages

```bash
# Update package list
sudo apt update

# Upgrade packages
sudo apt upgrade -y

# Upgrade distribution (major updates)
sudo apt dist-upgrade -y

# Clean up
sudo apt autoremove -y
sudo apt autoclean

# Reboot if kernel was updated
sudo reboot
```

### 3. Update Python Dependencies

```bash
sudo su - garage
cd /opt/garage/app
source venv/bin/activate

# Update all packages
pip list --outdated
pip install --upgrade -r requirements.txt

# Or update specific packages
pip install --upgrade Flask Flask-Login

deactivate
exit

# Restart service
sudo systemctl restart garage.service
```

### 4. Rollback Procedure

If an update causes issues:

```bash
# Stop service
sudo systemctl stop garage.service

# Restore from backup
sudo su - garage
cd /opt/garage
rm -rf app
mv app.backup.YYYYMMDD app

# Restore database if needed
mysql -u garage_user -p garage_app < backups/db_backup_YYYYMMDD_HHMMSS.sql

exit

# Restart service
sudo systemctl start garage.service
```

---

## Quick Reference Commands

### Service Management
```bash
sudo systemctl start garage.service      # Start service
sudo systemctl stop garage.service       # Stop service
sudo systemctl restart garage.service    # Restart service
sudo systemctl status garage.service     # Check status
sudo journalctl -u garage.service -f     # View logs
```

### Database
```bash
mysql -u garage_user -p garage_app       # Connect to database
sudo systemctl restart mariadb           # Restart database
mysqldump -u garage_user -p garage_app > backup.sql  # Backup
```

### Nginx
```bash
sudo nginx -t                            # Test configuration
sudo systemctl restart nginx             # Restart nginx
sudo tail -f /var/log/nginx/garage_error.log  # View logs
```

### System
```bash
sudo reboot                              # Reboot system
sudo shutdown -h now                     # Shutdown system
vcgencmd measure_temp                    # Check CPU temperature
df -h                                    # Check disk space
free -h                                  # Check memory usage
```

---

## Additional Resources

### Documentation
- [Flask Documentation](https://flask.palletsprojects.com/)
- [Raspberry Pi Documentation](https://www.raspberrypi.com/documentation/)
- [Automation HAT Documentation](https://pinout.xyz/pinout/automation_hat)
- [Nginx Documentation](https://nginx.org/en/docs/)
- [MariaDB Documentation](https://mariadb.org/documentation/)

### Support
- Check application logs: `sudo journalctl -u garage.service`
- Review system logs: `sudo journalctl -xe`
- Check hardware compatibility
- Verify network connectivity

### Security Updates
- Subscribe to Raspberry Pi security announcements
- Monitor CVE databases for Python/Flask vulnerabilities
- Keep all software updated
- Regular security audits

---

## Appendix: Automated Installation Script

See the included `install_production.sh` script for automated installation on a fresh Raspberry Pi.

## Appendix: Network Configuration Examples

See the `network-examples/` directory for various network configuration scenarios:
- Port forwarding for remote access
- VPN setup for secure remote access
- Dynamic DNS configuration
- Multiple Raspberry Pi setups
