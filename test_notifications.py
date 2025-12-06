#!/usr/bin/env python3
"""Test push notification integration."""

import os
import sys
from dotenv import load_dotenv

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from tennis_monitor.notifications import NotificationManager
from tennis_monitor.config import NotificationConfig

def test_ntfy_setup():
    """Test ntfy.sh push notification setup."""
    load_dotenv()
    
    config = NotificationConfig(
        enable_email_alerts=False,
        enable_push_notifications=True,
        email_recipient="test@example.com"
    )
    
    manager = NotificationManager(config)
    
    print(f"Push Service: {manager.push_service}")
    print(f"NTFY Topic: {manager.ntfy_topic}")
    print(f"Pushbullet Key: {'***' if manager.pushbullet_key else 'Not set'}")
    
    # Test alert notification
    try:
        test_message = "This is a test alert from Tennis Monitor"
        print(f"\nSending test alert to {manager.push_service}...")
        
        if manager.push_service == "ntfy":
            if manager.ntfy_topic:
                print(f"✓ NTFY_TOPIC is configured: {manager.ntfy_topic}")
                print(f"  Alert will be sent to: https://ntfy.sh/{manager.ntfy_topic}")
                manager._send_ntfy(test_message, is_alert=True)
                print("✓ Test alert sent successfully!")
            else:
                print("⚠ NTFY_TOPIC not configured")
                print("  To use ntfy.sh:")
                print("  1. Install ntfy app on iPhone: https://apps.apple.com/us/app/ntfy/id1665873820")
                print("  2. Choose a unique topic name (e.g., 'mytennismonitor42')")
                print("  3. Add to .env: NTFY_TOPIC=your_topic_name")
                print("  4. Subscribe to the topic in the ntfy app")
        
        elif manager.push_service == "pushbullet":
            if manager.pushbullet_key:
                print(f"✓ Pushbullet API key is configured")
                manager._send_pushbullet(test_message, is_alert=True)
                print("✓ Test alert sent successfully!")
            else:
                print("⚠ Pushbullet API key not configured")
                print("  To use Pushbullet:")
                print("  1. Sign up at https://www.pushbullet.com")
                print("  2. Get API key from https://www.pushbullet.com/account/settings")
                print("  3. Add to .env: PUSHBULLET_API_KEY=your_api_key")
    
    except Exception as e:
        print(f"✗ Error: {e}")
        return False
    
    return True

def test_court_availability_alert():
    """Test court availability notification."""
    load_dotenv()
    
    config = NotificationConfig(
        enable_email_alerts=False,
        enable_push_notifications=True,
        email_recipient="test@example.com"
    )
    
    manager = NotificationManager(config)
    
    test_court = {
        "name": "Court11",
        "time_slot": "18:00-19:00"
    }
    
    print("\nTesting court availability alert...")
    try:
        manager.notify_available(test_court)
        print("✓ Court availability notification sent")
    except Exception as e:
        print(f"✗ Error: {e}")
        return False
    
    return True

if __name__ == "__main__":
    print("=" * 60)
    print("Tennis Monitor - Push Notification Test")
    print("=" * 60)
    
    success = test_ntfy_setup()
    if success:
        test_court_availability_alert()
    
    print("\n" + "=" * 60)
    print("Setup Instructions:")
    print("=" * 60)
    print("\n1. Choose your push notification service:")
    print("   - ntfy.sh (free, recommended): PUSH_SERVICE=ntfy")
    print("   - Pushbullet (requires signup): PUSH_SERVICE=pushbullet")
    print("\n2. Update .env with the required settings")
    print("\n3. The monitor will send alerts on:")
    print("   - Court availability matching your preferences")
    print("   - Unexpected court structure changes (new unknown courts)")
    print("\n4. If structure changes are detected:")
    print("   - You'll receive a push notification")
    print("   - The monitor will stop and you'll need to update PW_COURT_MAP")
    print("=" * 60)
