#!/bin/bash
# Health Check Script for Garage Web App
# Usage: bash health_check.sh

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

print_status() {
    if [ $1 -eq 0 ]; then
        echo -e "${GREEN}✓${NC} $2"
    else
        echo -e "${RED}✗${NC} $2"
    fi
}

print_header() {
    echo ""
    echo "========================================"
    echo "$1"
    echo "========================================"
}

# System Information
print_header "System Information"
echo "Hostname: $(hostname)"
echo "IP Address: $(hostname -I | awk '{print $1}')"
echo "Uptime: $(uptime -p)"

if command -v vcgencmd &> /dev/null; then
    echo "CPU Temp: $(vcgencmd measure_temp)"
fi

# Disk and Memory
print_header "Resource Usage"
echo "Disk Usage:"
df -h / | tail -n 1 | awk '{printf "  %s used of %s (%s)\n", $3, $2, $5}'

echo "Memory Usage:"
free -h | grep Mem | awk '{printf "  %s used of %s\n", $3, $2}'

# Service Status
print_header "Service Status"

# Check garage service
if systemctl is-active --quiet garage.service; then
    print_status 0 "Garage Service: Running"
    
    # Check if responding
    if timeout 5 curl -sf http://127.0.0.1:5000/login > /dev/null 2>&1; then
        print_status 0 "  Application: Responding"
    else
        print_status 1 "  Application: Not responding"
    fi
else
    print_status 1 "Garage Service: Not running"
fi

# Check nginx
if systemctl is-active --quiet nginx; then
    print_status 0 "Nginx: Running"
    
    # Check if nginx is responding
    if timeout 5 curl -sf -k https://127.0.0.1 > /dev/null 2>&1; then
        print_status 0 "  HTTPS: Responding"
    else
        print_status 1 "  HTTPS: Not responding"
    fi
else
    print_status 1 "Nginx: Not running"
fi

# Check MariaDB
if systemctl is-active --quiet mariadb; then
    print_status 0 "MariaDB: Running"
else
    print_status 1 "MariaDB: Not running"
fi

# Database connectivity
print_header "Database Status"
if [ -f "/opt/garage/app/.env" ]; then
    DB_USER=$(grep DB_USER /opt/garage/app/.env | cut -d '=' -f2)
    DB_NAME=$(grep DB_NAME /opt/garage/app/.env | cut -d '=' -f2)
    DB_PASS=$(grep DB_PASSWORD /opt/garage/app/.env | cut -d '=' -f2)
    
    if mysql -u $DB_USER -p$DB_PASS -e "USE $DB_NAME; SELECT COUNT(*) FROM users;" &> /dev/null; then
        USER_COUNT=$(mysql -u $DB_USER -p$DB_PASS -s -N -e "USE $DB_NAME; SELECT COUNT(*) FROM users;")
        print_status 0 "Database Connection: OK"
        echo "  Users: $USER_COUNT"
    else
        print_status 1 "Database Connection: Failed"
    fi
else
    print_status 1 "Configuration file not found"
fi

# Automation HAT
print_header "Hardware Status"
if command -v i2cdetect &> /dev/null; then
    if i2cdetect -y 1 2>/dev/null | grep -q "54\|48"; then
        print_status 0 "Automation HAT: Detected"
    else
        print_status 1 "Automation HAT: Not detected"
    fi
else
    echo "  i2c-tools not installed"
fi

# Network
print_header "Network Status"
if ping -c 1 -W 2 8.8.8.8 &> /dev/null; then
    print_status 0 "Internet: Connected"
else
    print_status 1 "Internet: Not connected"
fi

# Firewall
if command -v ufw &> /dev/null; then
    if ufw status | grep -q "Status: active"; then
        print_status 0 "Firewall: Active"
    else
        print_status 1 "Firewall: Inactive"
    fi
fi

# Recent Logs
print_header "Recent Logs (Last 5 Lines)"
if systemctl is-active --quiet garage.service; then
    journalctl -u garage.service -n 5 --no-pager | sed 's/^/  /'
else
    echo "  Service not running"
fi

# Backup Status
print_header "Backup Status"
if [ -d "/opt/garage/backups" ]; then
    BACKUP_COUNT=$(ls -1 /opt/garage/backups/*.sql 2>/dev/null | wc -l)
    if [ $BACKUP_COUNT -gt 0 ]; then
        LATEST_BACKUP=$(ls -t /opt/garage/backups/db_backup_*.sql 2>/dev/null | head -n 1)
        BACKUP_DATE=$(basename $LATEST_BACKUP | sed 's/db_backup_//' | sed 's/.sql//')
        BACKUP_AGE=$(stat -c %Y $LATEST_BACKUP)
        NOW=$(date +%s)
        AGE_HOURS=$(( ($NOW - $BACKUP_AGE) / 3600 ))
        
        echo "  Total backups: $BACKUP_COUNT"
        echo "  Latest backup: $BACKUP_DATE ($AGE_HOURS hours ago)"
        
        if [ $AGE_HOURS -lt 48 ]; then
            print_status 0 "  Backup status: Current"
        else
            print_status 1 "  Backup status: Outdated (>48 hours)"
        fi
    else
        print_status 1 "No backups found"
    fi
else
    print_status 1 "Backup directory not found"
fi

# SSL Certificate
print_header "SSL Certificate Status"
if [ -f "/etc/letsencrypt/live/garage.*/fullchain.pem" ]; then
    CERT_FILE=$(ls /etc/letsencrypt/live/garage.*/fullchain.pem 2>/dev/null | head -n 1)
    EXPIRY=$(openssl x509 -enddate -noout -in $CERT_FILE | cut -d= -f2)
    echo "  Expires: $EXPIRY"
elif [ -f "/etc/nginx/ssl/garage.crt" ]; then
    EXPIRY=$(openssl x509 -enddate -noout -in /etc/nginx/ssl/garage.crt | cut -d= -f2)
    echo "  Self-signed certificate"
    echo "  Expires: $EXPIRY"
else
    print_status 1 "No SSL certificate found"
fi

echo ""
echo "========================================"
echo "Health check complete"
echo "========================================"
echo ""
