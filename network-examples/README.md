# Network Configuration Examples

This directory contains network configuration examples for various deployment scenarios.

## Available Guides

- **[static-ip.md](static-ip.md)** - Configure static IP address for Raspberry Pi
- **[port-forwarding.md](port-forwarding.md)** - Set up remote access via port forwarding

## Quick Reference

### Static IP Setup
```bash
sudo nano /etc/dhcpcd.conf
# Add configuration, then:
sudo systemctl restart dhcpcd
```

### Port Forwarding
1. Set static IP on Raspberry Pi
2. Configure router port forwarding (443/80)
3. Access via public IP or DDNS domain

## Security Reminders

- Always use HTTPS for external access
- Enable firewall (ufw)
- Use strong passwords
- Monitor access logs
- Keep system updated

For complete production setup, see [PRODUCTION.md](../PRODUCTION.md)
