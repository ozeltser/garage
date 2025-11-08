#!/usr/bin/env python3
"""
Test script for SMS notification functionality.
"""
import sys
import os
import unittest
from unittest.mock import patch, MagicMock

# Add the parent directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


class TestNotificationService(unittest.TestCase):
    """Test cases for NotificationService."""
    
    def test_notification_service_disabled_without_config(self):
        """Test that notification service is disabled without configuration."""
        from notification_service import NotificationService
        
        with patch.dict(os.environ, {}, clear=True):
            service = NotificationService()
            self.assertFalse(service.enabled)
            self.assertIsNone(service.client)
    
    def test_notification_service_enabled_with_config(self):
        """Test that notification service is enabled with proper configuration."""
        from notification_service import NotificationService
        
        test_env = {
            'TWILIO_ACCOUNT_SID': 'test_sid',
            'TWILIO_AUTH_TOKEN': 'test_token',
            'TWILIO_FROM_PHONE': '+1234567890',
            'TWILIO_TO_PHONES': '+0987654321'
        }
        
        with patch.dict(os.environ, test_env, clear=True):
            with patch('twilio.rest.Client') as mock_client:
                service = NotificationService()
                self.assertTrue(service.enabled)
                self.assertIsNotNone(service.client)
                mock_client.assert_called_once_with('test_sid', 'test_token')
    
    def test_send_door_status_notification_disabled(self):
        """Test sending notification when service is disabled."""
        from notification_service import NotificationService
        
        with patch.dict(os.environ, {}, clear=True):
            service = NotificationService()
            result = service.send_door_status_notification('open')
            self.assertFalse(result)
    
    def test_send_door_status_notification_success(self):
        """Test sending notification successfully."""
        from notification_service import NotificationService
        
        test_env = {
            'TWILIO_ACCOUNT_SID': 'test_sid',
            'TWILIO_AUTH_TOKEN': 'test_token',
            'TWILIO_FROM_PHONE': '+1234567890',
            'TWILIO_TO_PHONES': '+0987654321,+1111111111'
        }
        
        with patch.dict(os.environ, test_env, clear=True):
            with patch('twilio.rest.Client') as mock_client:
                # Setup mock
                mock_message = MagicMock()
                mock_message.sid = 'test_message_sid'
                mock_client.return_value.messages.create.return_value = mock_message
                
                service = NotificationService()
                result = service.send_door_status_notification('open')
                
                self.assertTrue(result)
                # Should be called twice (2 phone numbers)
                self.assertEqual(mock_client.return_value.messages.create.call_count, 2)
    
    def test_send_door_status_invalid_status(self):
        """Test sending notification with invalid status."""
        from notification_service import NotificationService
        
        test_env = {
            'TWILIO_ACCOUNT_SID': 'test_sid',
            'TWILIO_AUTH_TOKEN': 'test_token',
            'TWILIO_FROM_PHONE': '+1234567890',
            'TWILIO_TO_PHONES': '+0987654321'
        }
        
        with patch.dict(os.environ, test_env, clear=True):
            with patch('twilio.rest.Client'):
                service = NotificationService()
                result = service.send_door_status_notification('invalid')
                self.assertFalse(result)
    
    def test_multiple_phone_numbers(self):
        """Test that notifications are sent to multiple phone numbers."""
        from notification_service import NotificationService
        
        test_env = {
            'TWILIO_ACCOUNT_SID': 'test_sid',
            'TWILIO_AUTH_TOKEN': 'test_token',
            'TWILIO_FROM_PHONE': '+1234567890',
            'TWILIO_TO_PHONES': '+0987654321, +1111111111, +2222222222'
        }
        
        with patch.dict(os.environ, test_env, clear=True):
            service = NotificationService()
            self.assertEqual(len(service.to_phones), 3)
            self.assertEqual(service.to_phones[0], '+0987654321')
            self.assertEqual(service.to_phones[1], '+1111111111')
            self.assertEqual(service.to_phones[2], '+2222222222')


class TestDoorMonitor(unittest.TestCase):
    """Test cases for door monitor functions."""
    
    def test_get_door_status_closed(self):
        """Test getting door status when closed."""
        # Mock automationhat module before it's imported
        mock_automationhat = MagicMock()
        mock_automationhat.is_automation_hat.return_value = True
        mock_automationhat.input.one.read.return_value = 1
        
        with patch.dict('sys.modules', {'automationhat': mock_automationhat}):
            # Import after mocking
            import importlib
            import door_monitor
            importlib.reload(door_monitor)
            
            status = door_monitor.get_door_status()
            self.assertEqual(status, 'closed')
    
    def test_get_door_status_open(self):
        """Test getting door status when open."""
        # Mock automationhat module before it's imported
        mock_automationhat = MagicMock()
        mock_automationhat.is_automation_hat.return_value = True
        mock_automationhat.input.one.read.return_value = 0
        
        with patch.dict('sys.modules', {'automationhat': mock_automationhat}):
            # Import after mocking
            import importlib
            import door_monitor
            importlib.reload(door_monitor)
            
            status = door_monitor.get_door_status()
            self.assertEqual(status, 'open')
    
    def test_get_door_status_no_hat(self):
        """Test getting door status when Automation HAT is not present."""
        # Mock automationhat module before it's imported
        mock_automationhat = MagicMock()
        mock_automationhat.is_automation_hat.return_value = False
        
        with patch.dict('sys.modules', {'automationhat': mock_automationhat}):
            # Import after mocking
            import importlib
            import door_monitor
            importlib.reload(door_monitor)
            
            status = door_monitor.get_door_status()
            self.assertEqual(status, 'unknown')


def main():
    """Run tests."""
    print("=" * 60)
    print("SMS Notification Tests")
    print("=" * 60)
    
    # Run tests
    suite = unittest.TestLoader().loadTestsFromModule(sys.modules[__name__])
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    print("\n" + "=" * 60)
    print("Test Results")
    print("=" * 60)
    
    if result.wasSuccessful():
        print("\n✓ All tests passed!")
        return 0
    else:
        print(f"\n✗ {len(result.failures)} test(s) failed")
        return 1


if __name__ == '__main__':
    sys.exit(main())
