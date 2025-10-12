# Quick Start Guide for Production Deployment

This is a condensed version of the [complete production guide](PRODUCTION.md). For detailed instructions, troubleshooting, and advanced configuration, please refer to the full guide.

## Prerequisites

- Raspberry Pi 3B+ or newer with Raspberry Pi OS Lite installed
- Pimoroni Automation HAT
- Network connection (Ethernet recommended)
- SSH access enabled

## Automated Installation (Recommended)

### Option 1: One-Command Installation

```bash
# SSH into your Raspberry Pi
ssh pi@raspberrypi.local

# Clone repository and run installer
git clone https://github.com/ozeltser/garage.git
cd garage
sudo bash install_production.sh
```

The installer will:
- Install all dependencies (Python, MySQL, Nginx)
- Create application user and directories
- Configure database
- Set up systemd service for auto-start
- Configure Nginx with HTTPS (self-signed certificate)
- Set up automated backups
- Configure system monitoring

**Installation prompts:**
- Domain name or IP address
- Database credentials
- Admin username and password

After installation completes, reboot:
```bash
sudo reboot
```

## Manual Installation

If you prefer step-by-step installation or need to customize the setup:

### 1. Update System

```bash
sudo apt update && sudo apt upgrade -y
sudo raspi-config
# Enable I2C and SPI interfaces
```

### 2. Install Dependencies

```bash
sudo apt install -y python3 python3-pip python3-venv git \
    mariadb-server nginx i2c-tools python3-smbus
```

### 3. Clone Repository

```bash
sudo mkdir -p /opt/garage
sudo git clone https://github.com/ozeltser/garage.git /opt/garage/app
```

### 4. Create Application User

```bash
sudo adduser --system --group --home /opt/garage garage
sudo usermod -a -G gpio,i2c,spi garage
sudo chown -R garage:garage /opt/garage/app
```

### 5. Install Python Dependencies

```bash
sudo su - garage
cd /opt/garage/app
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
exit
```

### 6. Configure Database

```bash
sudo mysql
```

```sql
CREATE DATABASE garage_app CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'garage_user'@'localhost' IDENTIFIED BY 'YOUR_PASSWORD';
GRANT SELECT, INSERT, UPDATE, DELETE ON garage_app.* TO 'garage_user'@'localhost';
FLUSH PRIVILEGES;
EXIT;
```

### 7. Configure Application

```bash
cd /opt/garage/app
sudo cp .env.example .env
sudo nano .env
# Edit database credentials and generate SECRET_KEY
```

### 8. Initialize Database

```bash
sudo su - garage
cd /opt/garage/app
source venv/bin/activate
python init_db.py
exit
```

### 9. Install Systemd Service

```bash
sudo cp /opt/garage/app/garage.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable garage.service
sudo systemctl start garage.service
```

### 10. Configure Nginx

```bash
sudo cp /opt/garage/app/nginx-garage.conf /etc/nginx/sites-available/garage
sudo ln -s /etc/nginx/sites-available/garage /etc/nginx/sites-enabled/
sudo rm /etc/nginx/sites-enabled/default

# Generate self-signed certificate
sudo mkdir -p /etc/nginx/ssl
sudo openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout /etc/nginx/ssl/garage.key \
  -out /etc/nginx/ssl/garage.crt

# Update nginx config with correct domain and certificate paths
sudo nano /etc/nginx/sites-available/garage

sudo nginx -t
sudo systemctl restart nginx
```

## Post-Installation

### Access Your Application

Open a web browser and navigate to:
```
https://<your-raspberry-pi-ip>
```

**Default login:**
- Username: admin (or as configured in .env)
- Password: (as configured in .env)

**Important:** Change the default admin password immediately via the Profile page.

### Verify Installation

Run the health check script:
```bash
sudo bash /opt/garage/app/health_check.sh
```

### Check Service Status

```bash
# Check all services
sudo systemctl status garage.service
sudo systemctl status nginx
sudo systemctl status mariadb

# View application logs
sudo journalctl -u garage.service -f
```

## Essential Commands

### Service Management

```bash
# Start/Stop/Restart service
sudo systemctl start garage.service
sudo systemctl stop garage.service
sudo systemctl restart garage.service

# View logs
sudo journalctl -u garage.service -f
```

### Backup

```bash
# Manual backup
sudo /opt/garage/backup.sh

# View backups
ls -lh /opt/garage/backups/
```

### Restore

```bash
# List available backups
sudo bash /opt/garage/app/restore.sh

# Restore specific backup
sudo bash /opt/garage/app/restore.sh 20231201_020000
```

### System Monitoring

```bash
# Health check
sudo bash /opt/garage/app/health_check.sh

# Resource usage
htop
df -h
free -h

# Temperature (Raspberry Pi)
vcgencmd measure_temp
```

## Security Setup

### 1. Configure Firewall

```bash
sudo apt install -y ufw
sudo ufw allow 22/tcp   # SSH
sudo ufw allow 80/tcp   # HTTP
sudo ufw allow 443/tcp  # HTTPS
sudo ufw enable
```

### 2. Install Fail2Ban

```bash
sudo apt install -y fail2ban
sudo systemctl enable fail2ban
sudo systemctl start fail2ban
```

### 3. Change Default Passwords

- Change Raspberry Pi password: `passwd`
- Change admin password: Login to web app → Profile → Change Password

### 4. Set Static IP (Recommended)

Edit `/etc/dhcpcd.conf`:
```bash
sudo nano /etc/dhcpcd.conf
```

Add:
```
interface eth0
static ip_address=192.168.1.100/24
static routers=192.168.1.1
static domain_name_servers=192.168.1.1 8.8.8.8
```

Restart:
```bash
sudo systemctl restart dhcpcd
```

## Hardware Setup

### Automation HAT Connections

**Relay 1 (Garage Door):**
- Connect COM and NO terminals to garage door opener
- Triggers door open/close mechanism

**Input 1 (Door Sensor - Optional):**
- Connect door sensor to Input 1
- Used for door status monitoring

**Verify Hardware:**
```bash
# Check I2C devices
sudo i2cdetect -y 1

# Test relay
sudo su - garage
cd /opt/garage/app
source venv/bin/activate
python relay.py
```

## Automated Tasks

Automated tasks are set up by the installer:

- **Daily backups** at 2:00 AM → `/opt/garage/backups/`
- **Health monitoring** every 5 minutes
- **Auto-restart** services if they fail

View cron jobs:
```bash
sudo crontab -l        # System monitoring
sudo crontab -l -u garage  # Backups
```

## Troubleshooting

### Service Won't Start

```bash
sudo systemctl status garage.service
sudo journalctl -u garage.service -n 50
```

### Can't Access Web Interface

```bash
# Check nginx
sudo systemctl status nginx
sudo nginx -t

# Check firewall
sudo ufw status
```

### Database Issues

```bash
sudo systemctl status mariadb
mysql -u garage_user -p garage_app
```

### Hardware Not Detected

```bash
# Verify I2C enabled
sudo raspi-config
# Interface Options → I2C → Enable

# Check devices
sudo i2cdetect -y 1

# Check groups
groups garage
```

## Updates

### Update Application

```bash
cd /opt/garage/app
sudo systemctl stop garage.service
sudo -u garage git pull origin main
sudo -u garage bash -c "source venv/bin/activate && pip install -r requirements.txt"
sudo systemctl start garage.service
```

### Update System

```bash
sudo apt update && sudo apt upgrade -y
sudo reboot
```

## Getting Help

- **Full Documentation**: [PRODUCTION.md](PRODUCTION.md)
- **Security Guide**: [SECURITY.md](SECURITY.md)
- **Main README**: [README.md](README.md)
- **Check Logs**: `sudo journalctl -u garage.service -f`
- **Health Check**: `sudo bash /opt/garage/app/health_check.sh`

## Next Steps

1. ✅ Change default passwords
2. ✅ Configure static IP address
3. ✅ Test backup and restore
4. ✅ Verify hardware connections
5. ✅ Set up remote access (if needed)
6. ✅ Configure monitoring alerts
7. ✅ Test garage door operation
8. ✅ Enable SSL with Let's Encrypt (if using domain)

For detailed instructions on any of these topics, see [PRODUCTION.md](PRODUCTION.md).
