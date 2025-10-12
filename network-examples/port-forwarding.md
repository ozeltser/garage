# Port Forwarding Configuration for Remote Access

## Overview

To access your Garage Web App from outside your local network, you need to configure port forwarding on your router.

**Security Warning**: Exposing your application to the internet comes with security risks. Always use HTTPS and strong passwords.

## Requirements

- Router with port forwarding capability
- Static local IP for Raspberry Pi
- Strong passwords for all accounts
- HTTPS configured (SSL certificate)
- Firewall enabled

## Step 1: Set Static IP for Raspberry Pi

Set a static IP (e.g., 192.168.1.100) - see static-ip.md

## Step 2: Configure Router Port Forwarding

The exact steps vary by router manufacturer, but generally:

### Create Port Forwarding Rule

**For HTTPS Access (Recommended):**

- **Service Name**: Garage Web App HTTPS
- **External Port**: 443
- **Internal IP**: 192.168.1.100 (your Raspberry Pi)
- **Internal Port**: 443
- **Protocol**: TCP
- **Enabled**: Yes

**For HTTP (if needed for Let's Encrypt):**

- **Service Name**: Garage Web App HTTP
- **External Port**: 80
- **Internal IP**: 192.168.1.100
- **Internal Port**: 80
- **Protocol**: TCP
- **Enabled**: Yes

## Step 3: Find Your Public IP Address

```bash
curl ifconfig.me
```

## Step 4: Configure Dynamic DNS (Optional)

### Example: DuckDNS Setup

1. Visit https://www.duckdns.org
2. Create a subdomain (e.g., `mygarage.duckdns.org`)
3. Install DuckDNS client on Raspberry Pi

## Security Best Practices

1. Use HTTPS Only
2. Enable Fail2Ban
3. Use Strong Passwords
4. Monitor Access Logs
5. Regular Updates

## Troubleshooting

1. Verify port forwarding is active
2. Check firewall on Raspberry Pi
3. Verify nginx is listening
4. Test from internal network first
