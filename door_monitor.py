#!/usr/bin/env python3
"""
Door status monitor service that sends notifications when door status changes.
This service runs independently and continuously monitors the door status.
"""
import time
import sys
import os
import logging
from dotenv import load_dotenv
from notification_service import NotificationService

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def get_door_status():
    """
    Get the current door status from the Automation HAT sensor.
    
    Returns:
        str: 'open', 'closed', or 'unknown'
    """
    try:
        import automationhat
        
        if automationhat.is_automation_hat():
            input_one_state = automationhat.input.one.read()
            if input_one_state > 0:
                return 'closed'
            else:
                return 'open'
        else:
            logger.warning('Automation HAT not found')
            return 'unknown'
    except Exception as e:
        logger.error(f'Failed to read door sensor: {e}')
        return 'unknown'


def main():
    """Main monitoring loop."""
    # Load environment variables
    load_dotenv()
    
    # Initialize notification service
    notification_service = NotificationService()
    
    # Check interval in seconds
    check_interval = int(os.getenv('DOOR_MONITOR_INTERVAL', '5'))
    
    logger.info("Door status monitor started")
    logger.info(f"Check interval: {check_interval} seconds")
    
    # Track previous status to detect changes
    previous_status = None
    
    try:
        while True:
            # Get current door status
            current_status = get_door_status()
            
            # Check if status changed
            if current_status != 'unknown' and current_status != previous_status:
                if previous_status is not None:
                    # Status changed - send notification
                    logger.info(f"Door status changed: {previous_status} -> {current_status}")
                    notification_service.send_door_status_notification(current_status)
                else:
                    # First reading
                    logger.info(f"Initial door status: {current_status}")
                
                previous_status = current_status
            
            # Wait before next check
            time.sleep(check_interval)
            
    except KeyboardInterrupt:
        logger.info("Door status monitor stopped by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Door status monitor error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
