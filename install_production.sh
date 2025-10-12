#!/bin/bash
# Automated Production Installation Script for Garage Web App on Raspberry Pi
# Run this script on a fresh Raspberry Pi OS installation
# Usage: sudo bash install_production.sh

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Functions
print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_root() {
    if [ "$EUID" -ne 0 ]; then 
        print_error "Please run as root (use sudo)"
        exit 1
    fi
}

# Check if running as root
check_root

print_info "Starting Garage Web App Production Installation"
print_info "This script will install and configure the application on Raspberry Pi"

# Prompt for configuration
print_warning "You will be prompted for configuration details..."
read -p "Continue? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    print_error "Installation cancelled"
    exit 1
fi

# Get configuration from user
read -p "Enter your domain name (or IP address): " DOMAIN_NAME
read -p "Enter database name [garage_app]: " DB_NAME
DB_NAME=${DB_NAME:-garage_app}
read -p "Enter database user [garage_user]: " DB_USER
DB_USER=${DB_USER:-garage_user}
read -sp "Enter database password: " DB_PASSWORD
echo
read -sp "Confirm database password: " DB_PASSWORD_CONFIRM
echo

if [ "$DB_PASSWORD" != "$DB_PASSWORD_CONFIRM" ]; then
    print_error "Passwords do not match"
    exit 1
fi

read -p "Enter admin username [admin]: " ADMIN_USER
ADMIN_USER=${ADMIN_USER:-admin}
read -sp "Enter admin password: " ADMIN_PASSWORD
echo
read -sp "Confirm admin password: " ADMIN_PASSWORD_CONFIRM
echo

if [ "$ADMIN_PASSWORD" != "$ADMIN_PASSWORD_CONFIRM" ]; then
    print_error "Passwords do not match"
    exit 1
fi

# Generate secret key
SECRET_KEY=$(python3 -c 'import secrets; print(secrets.token_hex(32))')

print_info "Configuration collected, starting installation..."

# Update system
print_info "Updating system packages..."
apt update
apt upgrade -y

# Install dependencies
print_info "Installing system dependencies..."
apt install -y python3 python3-pip python3-venv git mariadb-server nginx \
    python3-dev build-essential libssl-dev libffi-dev \
    i2c-tools python3-smbus python3-spidev certbot python3-certbot-nginx \
    fail2ban ufw

# Enable I2C and SPI
print_info "Enabling I2C and SPI interfaces..."
raspi-config nonint do_i2c 0
raspi-config nonint do_spi 0

# Create garage user
print_info "Creating garage user..."
if ! id -u garage > /dev/null 2>&1; then
    adduser --system --group --home /opt/garage garage
    usermod -a -G gpio,i2c,spi garage
fi

# Clone or copy application
print_info "Setting up application directory..."
if [ ! -d "/opt/garage/app" ]; then
    # Check if we're running from the repo
    if [ -f "./app.py" ] && [ -f "./requirements.txt" ]; then
        mkdir -p /opt/garage
        cp -r . /opt/garage/app
        print_info "Copied application files from current directory"
    else
        # Try to clone from git
        read -p "Enter git repository URL (or press Enter to skip): " GIT_REPO
        if [ -n "$GIT_REPO" ]; then
            su - garage -c "git clone $GIT_REPO /opt/garage/app"
        else
            print_error "No application files found. Please manually copy files to /opt/garage/app"
            exit 1
        fi
    fi
fi

cd /opt/garage/app
chown -R garage:garage /opt/garage/app

# Create Python virtual environment
print_info "Creating Python virtual environment..."
su - garage -c "cd /opt/garage/app && python3 -m venv venv"
su - garage -c "cd /opt/garage/app && source venv/bin/activate && pip install --upgrade pip && pip install -r requirements.txt"

# Setup MySQL
print_info "Configuring MySQL/MariaDB..."
systemctl start mariadb
systemctl enable mariadb

# Secure MySQL installation (automated)
mysql -e "UPDATE mysql.user SET Password=PASSWORD('$(openssl rand -base64 32)') WHERE User='root';"
mysql -e "DELETE FROM mysql.user WHERE User='';"
mysql -e "DELETE FROM mysql.user WHERE User='root' AND Host NOT IN ('localhost', '127.0.0.1', '::1');"
mysql -e "DROP DATABASE IF EXISTS test;"
mysql -e "DELETE FROM mysql.db WHERE Db='test' OR Db='test\\_%';"
mysql -e "FLUSH PRIVILEGES;"

# Create database and user
print_info "Creating database and user..."
mysql -e "CREATE DATABASE IF NOT EXISTS $DB_NAME CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
mysql -e "CREATE USER IF NOT EXISTS '$DB_USER'@'localhost' IDENTIFIED BY '$DB_PASSWORD';"
mysql -e "GRANT SELECT, INSERT, UPDATE, DELETE ON $DB_NAME.* TO '$DB_USER'@'localhost';"
mysql -e "FLUSH PRIVILEGES;"

# Optimize MySQL for Raspberry Pi
print_info "Optimizing MySQL configuration..."
cat >> /etc/mysql/mariadb.conf.d/50-server.cnf << EOF

# Optimizations for Raspberry Pi
max_connections = 20
innodb_buffer_pool_size = 128M
innodb_log_file_size = 32M
query_cache_size = 8M
query_cache_limit = 1M
bind-address = 127.0.0.1
EOF

systemctl restart mariadb

# Create .env file
print_info "Creating environment configuration..."
cat > /opt/garage/app/.env << EOF
# Flask configuration
SECRET_KEY=$SECRET_KEY
FLASK_ENV=production
FLASK_DEBUG=False

# Application settings
APP_HOST=127.0.0.1
APP_PORT=5000

# MySQL Database Configuration
DB_HOST=localhost
DB_PORT=3306
DB_NAME=$DB_NAME
DB_USER=$DB_USER
DB_PASSWORD=$DB_PASSWORD

# Default admin credentials
DEFAULT_USERNAME=$ADMIN_USER
DEFAULT_PASSWORD=$ADMIN_PASSWORD
EOF

chmod 600 /opt/garage/app/.env
chown garage:garage /opt/garage/app/.env

# Initialize database
print_info "Initializing database..."
su - garage -c "cd /opt/garage/app && source venv/bin/activate && python init_db.py"

# Setup systemd service
print_info "Setting up systemd service..."
cp /opt/garage/app/garage.service /etc/systemd/system/garage.service
systemctl daemon-reload
systemctl enable garage.service
systemctl start garage.service

# Setup Nginx
print_info "Configuring Nginx..."
cp /opt/garage/app/nginx-garage.conf /etc/nginx/sites-available/garage

# Update domain name in nginx config
sed -i "s/garage.yourdomain.com/$DOMAIN_NAME/g" /etc/nginx/sites-available/garage

ln -sf /etc/nginx/sites-available/garage /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

# Test nginx configuration
nginx -t

# For self-signed certificate (local network)
print_info "Generating self-signed SSL certificate..."
mkdir -p /etc/nginx/ssl
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout /etc/nginx/ssl/garage.key \
  -out /etc/nginx/ssl/garage.crt \
  -subj "/C=US/ST=State/L=City/O=Organization/CN=$DOMAIN_NAME"

# Update nginx to use self-signed cert
sed -i 's|ssl_certificate /etc/letsencrypt.*|ssl_certificate /etc/nginx/ssl/garage.crt;|' /etc/nginx/sites-available/garage
sed -i 's|ssl_certificate_key /etc/letsencrypt.*|ssl_certificate_key /etc/nginx/ssl/garage.key;|' /etc/nginx/sites-available/garage

systemctl restart nginx

# Setup firewall
print_info "Configuring firewall..."
ufw allow 22/tcp  # SSH
ufw allow 80/tcp  # HTTP
ufw allow 443/tcp # HTTPS
ufw --force enable

# Setup fail2ban
print_info "Configuring fail2ban..."
systemctl enable fail2ban
systemctl start fail2ban

# Create backup script
print_info "Creating backup script..."
cat > /opt/garage/backup.sh << 'EOFBACKUP'
#!/bin/bash
BACKUP_DIR="/opt/garage/backups"
DATE=$(date +%Y%m%d_%H%M%S)
DB_NAME="garage_app"
DB_USER="garage_user"

# Read DB password from .env
DB_PASS=$(grep DB_PASSWORD /opt/garage/app/.env | cut -d '=' -f2)

mkdir -p $BACKUP_DIR
mysqldump -u $DB_USER -p$DB_PASS $DB_NAME > $BACKUP_DIR/db_backup_$DATE.sql
tar -czf $BACKUP_DIR/app_backup_$DATE.tar.gz -C /opt/garage/app .env *.py templates/ static/
find $BACKUP_DIR -name "*.sql" -mtime +7 -delete
find $BACKUP_DIR -name "*.tar.gz" -mtime +7 -delete
echo "Backup completed: $DATE"
EOFBACKUP

chmod +x /opt/garage/backup.sh
chown garage:garage /opt/garage/backup.sh

# Setup daily backup cron job
print_info "Setting up automated backups..."
(crontab -l -u garage 2>/dev/null; echo "0 2 * * * /opt/garage/backup.sh >> /opt/garage/backup.log 2>&1") | crontab -u garage -

# Create monitoring script
print_info "Creating monitoring script..."
cat > /opt/garage/monitor.sh << 'EOFMONITOR'
#!/bin/bash
if ! systemctl is-active --quiet garage.service; then
    systemctl restart garage.service
    logger "Garage service was down and has been restarted"
fi
if ! systemctl is-active --quiet nginx; then
    systemctl restart nginx
    logger "Nginx was down and has been restarted"
fi
if ! systemctl is-active --quiet mariadb; then
    systemctl restart mariadb
    logger "MariaDB was down and has been restarted"
fi
EOFMONITOR

chmod +x /opt/garage/monitor.sh

# Setup monitoring cron job
(crontab -l 2>/dev/null; echo "*/5 * * * * /opt/garage/monitor.sh") | crontab -

# Print completion message
print_info ""
print_info "============================================"
print_info "Installation Complete!"
print_info "============================================"
print_info ""
print_info "Application URL: https://$DOMAIN_NAME"
print_info "Admin Username: $ADMIN_USER"
print_info "Admin Password: [as configured]"
print_info ""
print_info "Service Management:"
print_info "  sudo systemctl status garage.service"
print_info "  sudo systemctl restart garage.service"
print_info "  sudo journalctl -u garage.service -f"
print_info ""
print_info "Backups: /opt/garage/backups (daily at 2 AM)"
print_info "Logs: sudo journalctl -u garage.service"
print_info ""
print_warning "Note: Self-signed SSL certificate is being used."
print_warning "For production with domain, run: sudo certbot --nginx -d $DOMAIN_NAME"
print_info ""
print_info "Please reboot the Raspberry Pi to ensure all settings take effect:"
print_info "  sudo reboot"
print_info ""

# Ask if user wants to reboot now
read -p "Reboot now? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    print_info "Rebooting..."
    reboot
fi
