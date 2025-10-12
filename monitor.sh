#!/bin/bash
# Garage App System Monitor Script
# Place in /opt/garage/monitor.sh
# Schedule with cron: */5 * * * * /opt/garage/monitor.sh

LOG_FILE="/var/log/garage-monitor.log"
EMAIL=""  # Set your email address for alerts (optional)

log_message() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> $LOG_FILE
}

send_alert() {
    local subject="$1"
    local message="$2"
    
    log_message "ALERT: $message"
    
    # Send email if configured
    if [ -n "$EMAIL" ] && command -v mail &> /dev/null; then
        echo "$message" | mail -s "$subject" $EMAIL
    fi
    
    # Log to syslog
    logger -t garage-monitor "$message"
}

# Check garage service
if ! systemctl is-active --quiet garage.service; then
    send_alert "Garage Service Down" "Garage service is not running. Attempting restart..."
    systemctl restart garage.service
    sleep 3
    
    if systemctl is-active --quiet garage.service; then
        log_message "Garage service restarted successfully"
    else
        send_alert "Garage Service Failed" "Failed to restart garage service. Manual intervention required."
    fi
else
    # Service is running, check if it's responding
    if timeout 5 curl -sf http://127.0.0.1:5000/login > /dev/null 2>&1; then
        : # Service is responding, all good
    else
        send_alert "Garage Service Unresponsive" "Garage service is running but not responding. Restarting..."
        systemctl restart garage.service
    fi
fi

# Check nginx
if ! systemctl is-active --quiet nginx; then
    send_alert "Nginx Down" "Nginx is not running. Attempting restart..."
    systemctl restart nginx
    sleep 2
    
    if systemctl is-active --quiet nginx; then
        log_message "Nginx restarted successfully"
    else
        send_alert "Nginx Failed" "Failed to restart nginx. Manual intervention required."
    fi
fi

# Check MariaDB
if ! systemctl is-active --quiet mariadb; then
    send_alert "Database Down" "MariaDB is not running. Attempting restart..."
    systemctl restart mariadb
    sleep 3
    
    if systemctl is-active --quiet mariadb; then
        log_message "MariaDB restarted successfully"
    else
        send_alert "Database Failed" "Failed to restart MariaDB. Manual intervention required."
    fi
fi

# Check disk space
DISK_USAGE=$(df -h / | awk 'NR==2 {print $5}' | sed 's/%//')
if [ $DISK_USAGE -gt 90 ]; then
    send_alert "Disk Space Warning" "Disk usage is at ${DISK_USAGE}%. Please free up space."
elif [ $DISK_USAGE -gt 80 ]; then
    log_message "Warning: Disk usage is at ${DISK_USAGE}%"
fi

# Check memory usage
MEMORY_USAGE=$(free | grep Mem | awk '{printf("%.0f", $3/$2 * 100)}')
if [ $MEMORY_USAGE -gt 90 ]; then
    send_alert "Memory Warning" "Memory usage is at ${MEMORY_USAGE}%"
    log_message "Warning: High memory usage at ${MEMORY_USAGE}%"
fi

# Check CPU temperature (Raspberry Pi specific)
if command -v vcgencmd &> /dev/null; then
    TEMP=$(vcgencmd measure_temp | sed 's/temp=//' | sed 's/°C//')
    TEMP_INT=${TEMP%.*}
    
    if [ $TEMP_INT -gt 80 ]; then
        send_alert "Temperature Warning" "CPU temperature is ${TEMP}°C. Check cooling."
    elif [ $TEMP_INT -gt 70 ]; then
        log_message "Warning: CPU temperature is ${TEMP}°C"
    fi
fi

# Cleanup old logs (keep last 1000 lines)
if [ -f "$LOG_FILE" ]; then
    LINE_COUNT=$(wc -l < $LOG_FILE)
    if [ $LINE_COUNT -gt 1000 ]; then
        tail -n 1000 $LOG_FILE > $LOG_FILE.tmp
        mv $LOG_FILE.tmp $LOG_FILE
    fi
fi
