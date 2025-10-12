# Static IP Configuration Examples

## For Ethernet (eth0)

Edit `/etc/dhcpcd.conf`:

```bash
sudo nano /etc/dhcpcd.conf
```

Add at the end:

```conf
# Static IP configuration for Ethernet
interface eth0
static ip_address=192.168.1.100/24
static routers=192.168.1.1
static domain_name_servers=192.168.1.1 8.8.8.8
```

Apply changes:
```bash
sudo systemctl restart dhcpcd
```

## For WiFi (wlan0)

```conf
# Static IP configuration for WiFi
interface wlan0
static ip_address=192.168.1.100/24
static routers=192.168.1.1
static domain_name_servers=192.168.1.1 8.8.8.8
```

## Verify Configuration

After applying changes:

```bash
# Check IP address
ip addr show eth0

# Check routing
ip route

# Test connectivity
ping -c 4 8.8.8.8
```
