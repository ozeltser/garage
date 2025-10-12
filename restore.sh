#!/bin/bash
# Garage App Restore Script
# Usage: sudo bash restore.sh <backup_date>
# Example: sudo bash restore.sh 20231201_020000

BACKUP_DIR="/opt/garage/backups"

if [ "$EUID" -ne 0 ]; then 
    echo "Error: Please run as root (use sudo)"
    exit 1
fi

if [ -z "$1" ]; then
    echo "Usage: $0 <backup_date>"
    echo ""
    echo "Available backups:"
    ls -1 $BACKUP_DIR/db_backup_*.sql 2>/dev/null | sed 's/.*db_backup_/  /' | sed 's/.sql$//'
    exit 1
fi

BACKUP_DATE="$1"
DB_BACKUP="$BACKUP_DIR/db_backup_$BACKUP_DATE.sql"
APP_BACKUP="$BACKUP_DIR/app_backup_$BACKUP_DATE.tar.gz"

# Check if backup files exist
if [ ! -f "$DB_BACKUP" ]; then
    echo "Error: Database backup not found: $DB_BACKUP"
    exit 1
fi

if [ ! -f "$APP_BACKUP" ]; then
    echo "Warning: Application backup not found: $APP_BACKUP"
    read -p "Continue with database restore only? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

echo "This will restore backups from: $BACKUP_DATE"
echo "Database backup: $DB_BACKUP"
if [ -f "$APP_BACKUP" ]; then
    echo "Application backup: $APP_BACKUP"
fi
echo ""
echo "WARNING: This will overwrite current data!"
read -p "Continue? (y/n) " -n 1 -r
echo

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Restore cancelled"
    exit 1
fi

# Read database credentials from .env
if [ -f "/opt/garage/app/.env" ]; then
    DB_NAME=$(grep DB_NAME /opt/garage/app/.env | cut -d '=' -f2)
    DB_USER=$(grep DB_USER /opt/garage/app/.env | cut -d '=' -f2)
    DB_PASS=$(grep DB_PASSWORD /opt/garage/app/.env | cut -d '=' -f2)
else
    echo "Error: .env file not found"
    exit 1
fi

echo "Stopping garage service..."
systemctl stop garage.service

# Restore database
echo "Restoring database..."
if mysql -u $DB_USER -p$DB_PASS $DB_NAME < $DB_BACKUP; then
    echo "Database restored successfully"
else
    echo "Error: Database restore failed"
    systemctl start garage.service
    exit 1
fi

# Restore application files if available
if [ -f "$APP_BACKUP" ]; then
    echo "Restoring application files..."
    
    # Backup current .env just in case
    cp /opt/garage/app/.env /tmp/.env.backup
    
    # Extract application files (excluding .env to keep current config)
    if tar -xzf $APP_BACKUP -C /opt/garage/app --exclude=.env; then
        echo "Application files restored successfully"
        
        # Restore .env
        mv /tmp/.env.backup /opt/garage/app/.env
    else
        echo "Error: Application restore failed"
        systemctl start garage.service
        exit 1
    fi
    
    # Fix permissions
    chown -R garage:garage /opt/garage/app
    chmod 600 /opt/garage/app/.env
fi

echo "Starting garage service..."
systemctl start garage.service

# Check service status
sleep 2
if systemctl is-active --quiet garage.service; then
    echo ""
    echo "Restore completed successfully!"
    echo "Service is running normally"
else
    echo ""
    echo "Warning: Service may have issues starting"
    echo "Check logs with: sudo journalctl -u garage.service -n 50"
fi
