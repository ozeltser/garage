#!/usr/bin/env python3
"""
Integration test to demonstrate the SMS notification functionality.
This script simulates door status changes and shows how notifications would be sent.
"""
import sys
from dotenv import load_dotenv
from notification_service import NotificationService

def main():
    print("=" * 60)
    print("SMS Notification Integration Test")
    print("=" * 60)
    
    # Load environment variables
    load_dotenv()
    
    # Initialize notification service
    notification_service = NotificationService()
    
    print("\nChecking configuration...")
    if notification_service.enabled:
        print("✓ SMS notifications are ENABLED")
        print(f"  - From phone: {notification_service.from_phone}")
        print(f"  - To phones: {', '.join(notification_service.to_phones)}")
    else:
        print("✗ SMS notifications are DISABLED")
        print("\nTo enable SMS notifications:")
        print("1. Sign up for a Twilio account at https://www.twilio.com")
        print("2. Get your Account SID, Auth Token, and a phone number")
        print("3. Add the following to your .env file:")
        print("   TWILIO_ACCOUNT_SID=your_account_sid")
        print("   TWILIO_AUTH_TOKEN=your_auth_token")
        print("   TWILIO_FROM_PHONE=+15551234567")
        print("   TWILIO_TO_PHONES=+15559876543,+15551112222")
        print("\nFor complete setup instructions, see SMS_NOTIFICATIONS.md")
        return 1
    
    # Simulate door status changes
    print("\n" + "-" * 60)
    print("Simulating door status changes...")
    print("-" * 60)
    
    # Test 1: Door opened
    print("\n[TEST 1] Simulating door OPENED event...")
    result1 = notification_service.send_door_status_notification('open')
    if result1:
        print("✓ Notification sent successfully for door OPEN")
    else:
        print("✗ Failed to send notification for door OPEN")
    
    # Test 2: Door closed
    print("\n[TEST 2] Simulating door CLOSED event...")
    result2 = notification_service.send_door_status_notification('closed')
    if result2:
        print("✓ Notification sent successfully for door CLOSED")
    else:
        print("✗ Failed to send notification for door CLOSED")
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    if result1 and result2:
        print("✓ All notifications sent successfully!")
        print("\nCheck your phone(s) for the test messages.")
        print("You should have received 2 messages:")
        print("  1. 🚗 Garage door OPEN")
        print("  2. 🚗 Garage door CLOSED")
        return 0
    else:
        print("✗ Some notifications failed to send")
        print("\nPlease check:")
        print("  - Your Twilio credentials are correct")
        print("  - Your Twilio account has sufficient balance")
        print("  - Phone numbers are verified (for trial accounts)")
        print("  - Phone numbers are in E.164 format (+1234567890)")
        return 1

if __name__ == '__main__':
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
