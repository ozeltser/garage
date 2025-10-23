"""
Notification service for sending SMS alerts via Twilio.
"""
import os
import logging
from typing import List

logger = logging.getLogger(__name__)


class NotificationService:
    """Service for sending SMS notifications about door status changes."""
    
    def __init__(self):
        """Initialize the notification service with Twilio credentials from environment."""
        self.account_sid = os.getenv('TWILIO_ACCOUNT_SID', '').strip()
        self.auth_token = os.getenv('TWILIO_AUTH_TOKEN', '').strip()
        self.from_phone = os.getenv('TWILIO_FROM_PHONE', '').strip()
        to_phones = os.getenv('TWILIO_TO_PHONES', '').strip()
        self.to_phones = [p.strip() for p in to_phones.split(',') if p.strip()]
        
        self.enabled = bool(self.account_sid and self.auth_token and 
                          self.from_phone and self.to_phones)
        
        if self.enabled:
            try:
                from twilio.rest import Client
                self.client = Client(self.account_sid, self.auth_token)
                logger.info("SMS notifications enabled")
            except ImportError:
                logger.warning("Twilio library not installed. SMS notifications disabled.")
                self.enabled = False
            except Exception as e:
                logger.error(f"Failed to initialize Twilio client: {str(e)}")
                self.enabled = False
        else:
            logger.info("SMS notifications disabled (missing configuration)")
            self.client = None
    
    def send_door_status_notification(self, status: str) -> bool:
        """
        Send SMS notification about door status change.
        
        Args:
            status: Door status ('open' or 'closed')
            
        Returns:
            bool: True if notification was sent successfully, False otherwise
        """
        if not self.enabled:
            logger.debug("SMS notifications not enabled, skipping")
            return False
        
        if status not in ['open', 'closed']:
            logger.warning(f"Invalid door status: {status}")
            return False
        
        message_text = f"🚗 Garage door {status.upper()}"
        
        return self.send_sms(message_text)
    
    def send_sms(self, message: str) -> bool:
        """
        Send SMS to all configured phone numbers.
        
        Args:
            message: Text message to send
            
        Returns:
            bool: True if at least one message was sent successfully, False otherwise
        """
        if not self.enabled:
            return False
        
        success = False
        for to_phone in self.to_phones:
            try:
                msg = self.client.messages.create(
                    body=message,
                    from_=self.from_phone,
                    to=to_phone
                )
                logger.info(f"SMS sent to {to_phone}: {msg.sid}")
                success = True
            except Exception as e:
                logger.error(f"Failed to send SMS to {to_phone}: {str(e)}")
        
        return success
