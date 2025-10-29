# Troubleshooting Quick Reference

Quick reference for common issues and their solutions.

## Service Issues

### Service Won't Start
```bash
# Check status and errors
sudo systemctl status garage.service
sudo journalctl -u garage.service -n 50

# Common fixes
sudo systemctl restart mariadb      # Restart database first
sudo systemctl restart garage.service
```

### Service Keeps Restarting
```bash
# Check recent logs
sudo journalctl -u garage.service --since "5 minutes ago"

# Common causes:
# - Database connection failed (check .env credentials)
# - Port 5000 already in use (check: sudo netstat -tlnp | grep 5000)
# - Permission issues (check: ls -l /opt/garage/app/.env)
```

## Web Access Issues

### Can't Access via Browser
```bash
# 1. Check if service is running
sudo systemctl status garage.service

# 2. Check if nginx is running
sudo systemctl status nginx

# 3. Test local connection
curl http://127.0.0.1:5000/login

# 4. Check firewall
sudo ufw status

# 5. Check nginx logs
sudo tail -f /var/log/nginx/garage_error.log
```

### SSL Certificate Errors
```bash
# For self-signed certificates, regenerate
sudo openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout /etc/nginx/ssl/garage.key \
  -out /etc/nginx/ssl/garage.crt

sudo systemctl restart nginx
```

### "502 Bad Gateway"
```bash
# Application not responding
sudo systemctl restart garage.service

# Wait a few seconds
sleep 5

# Test again
curl http://127.0.0.1:5000/login
```

### WebSocket/Socket.IO Connection Issues
```bash
# 1. Check if real-time updates are working
# Open browser console and look for WebSocket errors

# 2. Verify nginx configuration has WebSocket support
sudo nginx -t
sudo grep -A 5 "WebSocket" /etc/nginx/sites-available/garage

# 3. Check that Socket.IO is configured with correct path
# Should see: socketio = SocketIO(app, ..., path='/socket.io/')
grep "path=" /opt/garage/app/app.py

# 4. Restart services to apply configuration
sudo systemctl restart garage.service nginx

# 5. Test WebSocket connection
# Browser console should show: "Client connected" in network tab

# Common causes:
# - nginx missing WebSocket upgrade headers
# - Socket.IO path not configured
# - CORS issues (check CORS_ALLOWED_ORIGINS in .env)
# - Firewall blocking WebSocket connections
```

## Database Issues

### Can't Connect to Database
```bash
# 1. Check if MySQL is running
sudo systemctl status mariadb

# 2. Try to connect manually
mysql -u garage_user -p garage_app

# 3. Check credentials in .env
cat /opt/garage/app/.env | grep DB_

# 4. Verify user exists
sudo mysql -e "SELECT User, Host FROM mysql.user WHERE User='garage_user';"
```

### "Too Many Connections"
```bash
# Check current connections
sudo mysql -e "SHOW PROCESSLIST;"

# Restart MySQL
sudo systemctl restart mariadb
sudo systemctl restart garage.service
```

## Hardware Issues

### Automation HAT Not Detected
```bash
# 1. Verify I2C is enabled
sudo raspi-config
# Interface Options → I2C → Enable

# 2. Reboot
sudo reboot

# 3. After reboot, check for devices
sudo i2cdetect -y 1
# Should show devices at 0x48, 0x54, etc.

# 4. Check user permissions
groups garage
# Should include: gpio i2c spi
```

### Relay Not Working
```bash
# Test as garage user
sudo su - garage
cd /opt/garage/app
source venv/bin/activate
python relay.py
# Should trigger relay for 5 seconds

# If error about automationhat not found:
pip install --upgrade automationhat
```

## Performance Issues

### High CPU Usage
```bash
# Check what's using CPU
htop
# Press F5 to view tree, F10 to quit

# Check temperature
vcgencmd measure_temp

# If overheating, check cooling
```

### High Memory Usage
```bash
# Check memory
free -h

# Restart service to free memory
sudo systemctl restart garage.service

# Optimize database
mysql -u garage_user -p garage_app -e "OPTIMIZE TABLE users;"
```

### Slow Response
```bash
# Check disk I/O
sudo iotop

# Check disk space
df -h

# Clean up old logs
sudo journalctl --vacuum-time=7d

# Check nginx performance
sudo tail -f /var/log/nginx/garage_access.log
```

## Backup/Restore Issues

### Backup Failed
```bash
# Check backup script logs
cat /opt/garage/backup.log

# Run manually to see errors
sudo -u garage /opt/garage/backup.sh

# Common issues:
# - Disk full (df -h)
# - Database password wrong (check .env)
# - Permission issues (check ownership)
```

### Restore Failed
```bash
# Check if backup file exists
ls -lh /opt/garage/backups/

# Ensure service is stopped during restore
sudo systemctl stop garage.service

# Restore manually
mysql -u garage_user -p garage_app < /opt/garage/backups/db_backup_YYYYMMDD_HHMMSS.sql

# Start service
sudo systemctl start garage.service
```

## Network Issues

### Can't Access Remotely
```bash
# 1. Test local access first
curl -k https://192.168.1.100

# 2. Check port forwarding on router

# 3. Check public IP
curl ifconfig.me

# 4. Check firewall
sudo ufw status
sudo ufw allow 443/tcp
sudo ufw allow 80/tcp
```

### DNS Issues
```bash
# Test DNS resolution
nslookup mygarage.duckdns.org

# Check /etc/hosts
cat /etc/hosts

# Update DNS (if using DuckDNS)
/home/pi/duckdns/duck.sh
```

## Update Issues

### Update Failed
```bash
# Check git status
cd /opt/garage/app
git status

# Discard local changes if needed
git stash

# Pull updates
git pull origin main

# Apply stashed changes if needed
git stash pop
```

### Dependencies Won't Install
```bash
# Update pip first
sudo -u garage bash -c "cd /opt/garage/app && source venv/bin/activate && pip install --upgrade pip"

# Clear pip cache
sudo -u garage bash -c "cd /opt/garage/app && source venv/bin/activate && pip cache purge"

# Reinstall
sudo -u garage bash -c "cd /opt/garage/app && source venv/bin/activate && pip install -r requirements.txt"
```

## Emergency Recovery

### Complete Service Reset
```bash
# Stop everything
sudo systemctl stop garage.service
sudo systemctl stop nginx

# Restart database
sudo systemctl restart mariadb

# Start services
sudo systemctl start garage.service
sudo systemctl start nginx

# Check status
sudo systemctl status garage.service
sudo systemctl status nginx
```

### System Unresponsive
```bash
# Soft reboot
sudo reboot

# If SSH not responding, use physical access to:
# - Unplug power
# - Wait 10 seconds
# - Plug back in
```

### Database Corrupted
```bash
# Stop service
sudo systemctl stop garage.service

# Restore from latest backup
ls -lt /opt/garage/backups/db_backup_*.sql | head -1

# Restore
mysql -u garage_user -p garage_app < /opt/garage/backups/db_backup_LATEST.sql

# Start service
sudo systemctl start garage.service
```

## Useful Commands

### Logs
```bash
# Application logs (real-time)
sudo journalctl -u garage.service -f

# Nginx access log
sudo tail -f /var/log/nginx/garage_access.log

# Nginx error log
sudo tail -f /var/log/nginx/garage_error.log

# System log
sudo journalctl -xe
```

### Status Checks
```bash
# Quick health check
sudo bash /opt/garage/app/health_check.sh

# All services
sudo systemctl status garage.service nginx mariadb

# Network connections
sudo netstat -tlnp

# Disk usage
df -h

# Memory usage
free -h

# Temperature
vcgencmd measure_temp
```

### Quick Fixes
```bash
# Restart everything
sudo systemctl restart mariadb garage.service nginx

# Clear logs
sudo journalctl --vacuum-time=7d

# Fix permissions
sudo chown -R garage:garage /opt/garage/app
sudo chmod 600 /opt/garage/app/.env

# Test database connection
mysql -u garage_user -p garage_app -e "SELECT COUNT(*) FROM users;"
```

## Getting Help

If none of these solutions work:

1. **Check full logs**: `sudo journalctl -u garage.service -n 100`
2. **Review documentation**: See [PRODUCTION.md](PRODUCTION.md)
3. **Verify system requirements**: Raspberry Pi 3B+ or newer, sufficient power supply
4. **Check GitHub issues**: Look for similar problems
5. **Collect system info** for reporting:
   ```bash
   sudo bash /opt/garage/app/health_check.sh > system-info.txt
   sudo journalctl -u garage.service -n 100 >> system-info.txt
   ```

## Prevention

To avoid issues:

- ✅ Regular backups (automated daily)
- ✅ Monitor disk space (weekly)
- ✅ Keep system updated (monthly)
- ✅ Review logs (weekly)
- ✅ Test backups (monthly)
- ✅ Monitor temperature (continuous via monitoring script)
- ✅ Use UPS for power stability
- ✅ Keep documentation current
