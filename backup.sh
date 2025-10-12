#!/bin/bash
# Garage App Database and Configuration Backup Script
# Place in /opt/garage/backup.sh
# Schedule with cron: 0 2 * * * /opt/garage/backup.sh >> /opt/garage/backup.log 2>&1

BACKUP_DIR="/opt/garage/backups"
DATE=$(date +%Y%m%d_%H%M%S)
DB_NAME="garage_app"
DB_USER="garage_user"

# Read database password from .env file
if [ -f "/opt/garage/app/.env" ]; then
    DB_PASS=$(grep DB_PASSWORD /opt/garage/app/.env | cut -d '=' -f2)
else
    echo "Error: .env file not found"
    exit 1
fi

# Create backup directory if it doesn't exist
mkdir -p $BACKUP_DIR

echo "Starting backup at $(date)"

# Backup database
echo "Backing up database..."
if mysqldump -u $DB_USER -p$DB_PASS $DB_NAME > $BACKUP_DIR/db_backup_$DATE.sql; then
    echo "Database backup completed: db_backup_$DATE.sql"
else
    echo "Error: Database backup failed"
    exit 1
fi

# Backup application files and configuration
echo "Backing up application files..."
if tar -czf $BACKUP_DIR/app_backup_$DATE.tar.gz -C /opt/garage/app .env *.py templates/ static/ 2>/dev/null; then
    echo "Application backup completed: app_backup_$DATE.tar.gz"
else
    echo "Error: Application backup failed"
    exit 1
fi

# Calculate backup sizes
DB_SIZE=$(du -h $BACKUP_DIR/db_backup_$DATE.sql | cut -f1)
APP_SIZE=$(du -h $BACKUP_DIR/app_backup_$DATE.tar.gz | cut -f1)

echo "Backup sizes - Database: $DB_SIZE, Application: $APP_SIZE"

# Remove old backups (older than 7 days)
echo "Cleaning up old backups..."
find $BACKUP_DIR -name "db_backup_*.sql" -mtime +7 -delete
find $BACKUP_DIR -name "app_backup_*.tar.gz" -mtime +7 -delete

# Optional: Copy to external storage (uncomment and configure as needed)
# EXTERNAL_BACKUP="/media/usb/garage_backups"
# if [ -d "$EXTERNAL_BACKUP" ]; then
#     echo "Copying to external storage..."
#     cp $BACKUP_DIR/db_backup_$DATE.sql $EXTERNAL_BACKUP/
#     cp $BACKUP_DIR/app_backup_$DATE.tar.gz $EXTERNAL_BACKUP/
#     echo "External backup completed"
# fi

# List current backups
BACKUP_COUNT=$(ls -1 $BACKUP_DIR/*.sql 2>/dev/null | wc -l)
echo "Total backups retained: $BACKUP_COUNT"

echo "Backup completed successfully at $(date)"
echo "---"
