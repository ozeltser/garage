# Production Deployment Checklist

Use this checklist to ensure a successful production deployment of the Garage Web App on Raspberry Pi.

## Pre-Deployment

### Hardware Preparation
- [ ] Raspberry Pi 3B+ or newer with power supply
- [ ] Pimoroni Automation HAT installed
- [ ] MicroSD card (16GB+) with Raspberry Pi OS Lite
- [ ] Network connection (Ethernet cable or WiFi configured)
- [ ] SSH enabled on Raspberry Pi
- [ ] Optional: Case with cooling, UPS backup

### Initial Setup
- [ ] Raspberry Pi OS installed and updated
- [ ] SSH access verified
- [ ] I2C and SPI interfaces enabled (via `raspi-config`)
- [ ] Hostname configured
- [ ] Timezone set correctly
- [ ] Default password changed

### Planning
- [ ] Decided on domain name or using IP address
- [ ] Chosen strong passwords for:
  - [ ] Database user
  - [ ] Admin account
  - [ ] MySQL root (if applicable)
- [ ] Network configuration planned:
  - [ ] Static IP address determined
  - [ ] Port forwarding requirements identified
  - [ ] Remote access method chosen (port forward, VPN, local only)

## Deployment

### Automated Installation (Recommended)
- [ ] Repository cloned to Raspberry Pi
- [ ] Reviewed `install_production.sh` script
- [ ] Run `sudo bash install_production.sh`
- [ ] Provided all required information during prompts:
  - [ ] Domain name or IP address
  - [ ] Database credentials
  - [ ] Admin credentials
- [ ] Installation completed without errors
- [ ] System rebooted after installation

### OR Manual Installation
- [ ] System dependencies installed
- [ ] Application user created with proper groups
- [ ] Repository cloned to `/opt/garage/app`
- [ ] Python virtual environment created
- [ ] Dependencies installed via pip
- [ ] MySQL database created
- [ ] Database user created with privileges
- [ ] `.env` file configured with all settings
- [ ] Database initialized with `init_db.py`
- [ ] Systemd service installed and enabled
- [ ] Nginx configured and enabled
- [ ] SSL certificate generated or obtained
- [ ] Firewall configured (ufw)
- [ ] Fail2ban installed and configured

## Post-Deployment Verification

### Service Status
- [ ] Garage service running: `sudo systemctl status garage.service`
- [ ] Nginx running: `sudo systemctl status nginx`
- [ ] MariaDB running: `sudo systemctl status mariadb`
- [ ] All services enabled for auto-start

### Application Access
- [ ] Can access application via local IP: `https://<ip-address>`
- [ ] Login page loads correctly
- [ ] Can login with admin credentials
- [ ] Dashboard loads after login
- [ ] Profile page accessible

### Hardware Integration
- [ ] Automation HAT detected: `sudo i2cdetect -y 1`
- [ ] Relay test successful: `python relay.py`
- [ ] Door status sensor working (if installed): `python doorStatus.py`
- [ ] Garage door operation tested from web interface

### Database
- [ ] Database connection successful
- [ ] Admin user exists in database
- [ ] Can update profile information
- [ ] Can change password

### Security
- [ ] HTTPS working (no certificate errors expected for self-signed)
- [ ] HTTP redirects to HTTPS
- [ ] Firewall active: `sudo ufw status`
- [ ] Only required ports open (22, 80, 443)
- [ ] Fail2ban active: `sudo systemctl status fail2ban`
- [ ] Default passwords changed

## Configuration

### Network
- [ ] Static IP configured (if required)
- [ ] Static IP working after reboot
- [ ] Port forwarding configured (if remote access needed)
- [ ] Dynamic DNS configured (if using)
- [ ] DNS records updated (if using domain)
- [ ] Remote access tested (if applicable)

### SSL/TLS
- [ ] SSL certificate installed
- [ ] Certificate paths correct in nginx config
- [ ] Certificate not expired
- [ ] HTTPS working from browser
- [ ] Security headers present

### Backups
- [ ] Backup script tested: `sudo /opt/garage/backup.sh`
- [ ] Backup created successfully in `/opt/garage/backups/`
- [ ] Backup cron job scheduled: `sudo crontab -l -u garage`
- [ ] Backup retention working (7 days)
- [ ] External backup location configured (optional)

### Monitoring
- [ ] Monitoring script tested: `sudo /opt/garage/monitor.sh`
- [ ] Monitoring cron job scheduled: `sudo crontab -l`
- [ ] Health check working: `sudo bash health_check.sh`
- [ ] Email alerts configured (optional)

## Security Hardening

### System Security
- [ ] Root login disabled in SSH
- [ ] SSH password authentication disabled (if using keys)
- [ ] Fail2ban configured and active
- [ ] Firewall enabled with minimal ports
- [ ] System packages updated
- [ ] Automatic security updates configured (optional)

### Application Security
- [ ] Strong SECRET_KEY in .env (32+ characters)
- [ ] Strong database password (32+ characters)
- [ ] Strong admin password (16+ characters)
- [ ] FLASK_DEBUG=False in production
- [ ] .env file permissions: 600
- [ ] Application files owned by garage user

### Network Security
- [ ] HTTPS enforced
- [ ] Security headers configured in nginx
- [ ] Rate limiting configured (optional)
- [ ] Geographic restrictions configured (optional)
- [ ] VPN configured for remote access (recommended)

## Testing

### Functionality
- [ ] Login/logout working
- [ ] Garage door opens/closes via web interface
- [ ] Script output displayed correctly
- [ ] Errors displayed appropriately
- [ ] Profile updates working
- [ ] Password changes working

### Reliability
- [ ] Service survives reboot
- [ ] Service auto-restarts on failure
- [ ] Monitoring detects and restarts failed services
- [ ] Application handles database disconnection
- [ ] Nginx handles application downtime

### Performance
- [ ] Page load times acceptable (<3 seconds)
- [ ] CPU temperature within limits (<70°C idle)
- [ ] Memory usage acceptable (<60% with all services)
- [ ] Disk space sufficient (>30% free)

### Recovery
- [ ] Backup can be restored: `sudo bash restore.sh`
- [ ] Service recovers after restore
- [ ] Data preserved after restore
- [ ] Application functional after restore

## Documentation

### User Documentation
- [ ] README.md reviewed
- [ ] PRODUCTION.md bookmarked
- [ ] QUICKSTART.md reviewed
- [ ] TROUBLESHOOTING.md accessible
- [ ] Network examples reviewed if needed

### Operational Notes
- [ ] Admin credentials documented (securely)
- [ ] Static IP address documented
- [ ] Port forwarding details documented
- [ ] Custom configurations documented
- [ ] Hardware connections documented

## Maintenance Setup

### Scheduled Tasks
- [ ] Daily backups scheduled (2 AM)
- [ ] Monitoring checks scheduled (every 5 minutes)
- [ ] Log rotation configured
- [ ] Certificate renewal reminder set (if Let's Encrypt)

### Maintenance Calendar
- [ ] Weekly tasks scheduled:
  - [ ] Check logs for errors
  - [ ] Review disk space
  - [ ] Verify backups
- [ ] Monthly tasks scheduled:
  - [ ] Test backup restore
  - [ ] Update system packages
  - [ ] Review security logs
- [ ] Quarterly tasks scheduled:
  - [ ] Security audit
  - [ ] Certificate renewal (if needed)
  - [ ] Hardware inspection

## Remote Access (If Applicable)

### Port Forwarding
- [ ] Router port forwarding configured (80, 443)
- [ ] Public IP address known
- [ ] DDNS service configured and working
- [ ] External access tested from mobile data

### VPN (Recommended Alternative)
- [ ] VPN server installed (optional)
- [ ] VPN client configured on devices
- [ ] VPN access tested
- [ ] Access via VPN working

## Final Verification

### Health Check
- [ ] Run full health check: `sudo bash health_check.sh`
- [ ] All checks passing
- [ ] No errors in logs
- [ ] All services running optimally

### Load Testing
- [ ] Multiple login attempts successful
- [ ] Rapid door operations working
- [ ] Concurrent access tested
- [ ] No performance degradation

### User Acceptance
- [ ] End user training completed
- [ ] User can login successfully
- [ ] User can operate garage door
- [ ] User knows how to check status
- [ ] User has emergency contact info

## Go-Live Checklist

### Before Going Live
- [ ] All above items completed
- [ ] Backup verified and tested
- [ ] Monitoring confirmed working
- [ ] Security audit completed
- [ ] Documentation accessible

### Going Live
- [ ] Announce to users (if applicable)
- [ ] Monitor logs closely for first 24 hours
- [ ] Test from multiple devices
- [ ] Verify automated tasks running

### Post Go-Live
- [ ] Monitor for 1 week closely
- [ ] Review and tune performance
- [ ] Document any issues encountered
- [ ] Update documentation as needed
- [ ] Create runbook for common operations

## Emergency Contacts

Document these for quick reference:

- [ ] Repository URL: ________________________________
- [ ] Public IP Address: ________________________________
- [ ] DDNS Domain: ________________________________
- [ ] Admin Username: ________________________________
- [ ] Database Name: ________________________________
- [ ] Backup Location: ________________________________

## Support Resources

Keep these bookmarked:

- [ ] PRODUCTION.md - Production guide
- [ ] TROUBLESHOOTING.md - Quick reference
- [ ] GitHub Issues - Report problems
- [ ] Raspberry Pi forums - Hardware help

## Notes

Use this section for deployment-specific notes:

```
Date deployed: ________________
Deployed by: ________________
Special configurations: ________________
Known issues: ________________
Next review date: ________________
```

---

## Completion

- [ ] All critical items checked
- [ ] All desired optional items checked
- [ ] Documentation updated
- [ ] Deployment logged
- [ ] System ready for production use

**Deployment Status:** ☐ Ready ☐ Needs Work ☐ Blocked

**Sign-off:** ________________ **Date:** ________________
