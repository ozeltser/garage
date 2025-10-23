# SMS Notifications Guide

This guide explains how to set up and use SMS notifications for the Garage Door application. The system will automatically send text messages whenever the garage door opens or closes.

## Features

- 🔔 **Automatic Notifications**: Receive SMS when door opens or closes
- 📱 **Multi-User Support**: Send notifications to multiple phone numbers
- 🔧 **Easy Configuration**: Simple environment variable setup
- 🎯 **Reliable Delivery**: Powered by Twilio's robust SMS infrastructure
- 🔒 **Secure**: Credentials stored in environment variables
- 🚀 **Background Service**: Runs independently of the web application

## Prerequisites

Before setting up SMS notifications, you'll need:

1. **A Twilio Account**: Sign up at [https://www.twilio.com](https://www.twilio.com)
   - Get a free trial account with $15 credit
   - Or set up a paid account for production use

2. **A Twilio Phone Number**: Purchase or configure a phone number capable of sending SMS
   - Available through the Twilio Console
   - Ensure it supports SMS in your country

3. **Twilio Credentials**: From your [Twilio Console](https://www.twilio.com/console):
   - Account SID
   - Auth Token

## Installation

### 1. Install Dependencies

The Twilio library is already included in `requirements.txt`. If you need to install it separately:

```bash
pip install twilio==9.0.0
```

Or install all dependencies:

```bash
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Edit your `.env` file and add the following SMS notification settings:

```bash
# SMS Notification Configuration (via Twilio)
# Get these from your Twilio account: https://www.twilio.com/console
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=your_auth_token_here
TWILIO_FROM_PHONE=+15551234567
# Comma-separated list of phone numbers to notify (E.164 format: +1234567890)
TWILIO_TO_PHONES=+15559876543,+15551112222

# Door Monitor Configuration
# How often to check door status (in seconds)
DOOR_MONITOR_INTERVAL=5
```

#### Configuration Details:

- **TWILIO_ACCOUNT_SID**: Your Twilio Account SID from the console
- **TWILIO_AUTH_TOKEN**: Your Twilio Auth Token (keep this secret!)
- **TWILIO_FROM_PHONE**: The Twilio phone number that will send messages (E.164 format)
- **TWILIO_TO_PHONES**: Comma-separated list of recipient phone numbers (E.164 format)
- **DOOR_MONITOR_INTERVAL**: How often to check the door status, in seconds (default: 5)

**Important Notes:**
- All phone numbers must be in E.164 format: `+[country code][number]`
  - US example: `+15551234567`
  - UK example: `+447911123456`
- If using a Twilio trial account, you must verify recipient phone numbers first
- Keep your Auth Token secure - never commit it to version control!

### 3. Set Up the Door Monitor Service

The door monitor runs as a background service to continuously check the door status and send notifications.

#### For Raspberry Pi (systemd):

```bash
# Copy the service file to systemd
sudo cp garage-door-monitor.service /etc/systemd/system/

# Edit the service file if your paths are different
sudo nano /etc/systemd/system/garage-door-monitor.service

# Reload systemd
sudo systemctl daemon-reload

# Enable the service to start on boot
sudo systemctl enable garage-door-monitor.service

# Start the service
sudo systemctl start garage-door-monitor.service

# Check status
sudo systemctl status garage-door-monitor.service
```

#### Manual Start (for testing):

```bash
# Run in foreground
python3 door_monitor.py

# Run in background
nohup python3 door_monitor.py > door_monitor.log 2>&1 &
```

## Usage

Once configured and running, the system will automatically:

1. Monitor the door sensor every 5 seconds (or your configured interval)
2. Detect when the door status changes (open ↔ closed)
3. Send an SMS notification to all configured phone numbers

### Example Notifications

When the door opens:
```
🚗 Garage door OPEN
```

When the door closes:
```
🚗 Garage door CLOSED
```

## Testing

### 1. Test the Notification Service

Run the test suite to verify the notification service works correctly:

```bash
python3 test_notifications.py
```

All tests should pass.

### 2. Test SMS Sending

Create a simple test script to verify Twilio integration:

```python
from dotenv import load_dotenv
from notification_service import NotificationService

load_dotenv()
service = NotificationService()

if service.enabled:
    print("SMS notifications enabled!")
    service.send_door_status_notification('open')
    print("Test notification sent!")
else:
    print("SMS notifications not configured")
```

### 3. Monitor the Service

Check the door monitor service logs:

```bash
# For systemd service
sudo journalctl -u garage-door-monitor -f

# For manual run
tail -f door_monitor.log
```

## Troubleshooting

### No Notifications Received

1. **Check Configuration**:
   ```bash
   # Verify environment variables are set
   grep TWILIO .env
   ```

2. **Check Service Status**:
   ```bash
   sudo systemctl status garage-door-monitor.service
   ```

3. **Check Logs**:
   ```bash
   sudo journalctl -u garage-door-monitor -n 50
   ```

4. **Verify Twilio Credentials**:
   - Log in to [Twilio Console](https://www.twilio.com/console)
   - Verify Account SID and Auth Token are correct
   - Check your account balance (if using paid account)
   - Verify phone numbers are verified (if using trial account)

### Service Not Starting

1. **Check Python Path**:
   ```bash
   which python3
   # Update service file if needed
   ```

2. **Check File Permissions**:
   ```bash
   ls -l /home/pi/garage/door_monitor.py
   # Should be executable
   chmod +x /home/pi/garage/door_monitor.py
   ```

3. **Check Dependencies**:
   ```bash
   python3 -c "import twilio; print('Twilio installed')"
   ```

### Invalid Phone Number Format

Phone numbers must be in E.164 format:
- ✅ Correct: `+15551234567`
- ❌ Wrong: `555-123-4567`, `5551234567`, `1-555-123-4567`

### Twilio Trial Account Limitations

If using a Twilio trial account:
- Only verified phone numbers can receive messages
- Messages include trial account disclaimer
- Limited to $15 credit (usually ~500 messages)
- Upgrade to paid account for production use

## Cost Considerations

### Twilio Pricing (as of 2024)
- **SMS Messages**: ~$0.0075 - $0.01 per message (US)
- **Phone Number**: ~$1/month for a US number
- **Free Trial**: $15 credit for new accounts

### Example Costs
- 100 notifications/month: ~$1
- 500 notifications/month: ~$4-5
- 1000 notifications/month: ~$8-10

*Prices vary by country. Check [Twilio Pricing](https://www.twilio.com/sms/pricing) for details.*

## Disabling Notifications

To temporarily disable SMS notifications without stopping the door monitor:

1. **Comment out environment variables** in `.env`:
   ```bash
   # TWILIO_ACCOUNT_SID=ACxxxxxxxx
   # TWILIO_AUTH_TOKEN=xxxxxxxx
   # TWILIO_FROM_PHONE=+15551234567
   # TWILIO_TO_PHONES=+15559876543
   ```

2. **Restart the door monitor**:
   ```bash
   sudo systemctl restart garage-door-monitor.service
   ```

The service will continue monitoring but won't send notifications.

## Security Best Practices

1. **Never commit `.env` file** to version control
2. **Use environment-specific configurations** for different environments
3. **Rotate Twilio Auth Token** periodically
4. **Monitor Twilio usage** to detect unauthorized access
5. **Use IP whitelist** in Twilio settings if available
6. **Enable two-factor authentication** on your Twilio account

## Advanced Configuration

### Custom Messages

Edit `notification_service.py` to customize message format:

```python
def send_door_status_notification(self, status: str) -> bool:
    # Customize this line
    message_text = f"🚗 Garage door {status.upper()}"
    # Add timestamp, location, or other info
    # message_text = f"Alert: Garage door {status.upper()} at {datetime.now()}"
    return self.send_sms(message_text)
```

### Different Check Intervals

Adjust `DOOR_MONITOR_INTERVAL` in `.env`:
- Faster checks: `DOOR_MONITOR_INTERVAL=2` (every 2 seconds)
- Slower checks: `DOOR_MONITOR_INTERVAL=10` (every 10 seconds)
- Battery-friendly: `DOOR_MONITOR_INTERVAL=30` (every 30 seconds)

### Multiple Notification Services

The architecture supports adding more notification methods. You could extend it to include:
- Email notifications
- Push notifications
- Webhook calls
- Slack/Discord messages

## Support

For issues:
1. Check the [Troubleshooting](#troubleshooting) section above
2. Review Twilio documentation: https://www.twilio.com/docs/sms
3. Check application logs: `sudo journalctl -u garage-door-monitor`
4. Open an issue on GitHub with relevant log snippets

## License

This SMS notification feature is part of the Garage Web App and is available under the same MIT License.
