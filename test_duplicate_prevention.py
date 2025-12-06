#!/usr/bin/env python
"""Test that duplicate notifications are not sent."""

import sys
import os
import logging

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from tennis_monitor.config import get_config
from tennis_monitor.monitor import TennisMonitor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)

logger = logging.getLogger(__name__)

def main():
    logger.info("=" * 70)
    logger.info("Testing duplicate notification prevention")
    logger.info("=" * 70)
    
    try:
        config = get_config()
        monitor = TennisMonitor(config)
        
        # First check - should send notifications
        logger.info("\n[CHECK 1] First availability check...")
        available = monitor.check_availability()
        logger.info("Found %d courts", len(available))
        
        notification_count_1 = 0
        for court in available:
            if monitor._should_notify(court):
                notification_count_1 += 1
                logger.info("  → Would notify: %s at %s", court.get("name"), court.get("time_slot"))
            else:
                logger.info("  ✗ Already notified: %s at %s", court.get("name"), court.get("time_slot"))
        
        logger.info(f"Notifications sent: {notification_count_1}")
        logger.info(f"Notified slots tracked: {len(monitor.notified_slots)}")
        
        # Second check - should NOT send notifications (same day, same slots)
        logger.info("\n[CHECK 2] Second availability check (same day)...")
        available = monitor.check_availability()
        logger.info("Found %d courts", len(available))
        
        notification_count_2 = 0
        for court in available:
            if monitor._should_notify(court):
                notification_count_2 += 1
                logger.info("  → Would notify: %s at %s", court.get("name"), court.get("time_slot"))
            else:
                logger.info("  ✓ Already notified (no duplicate): %s at %s", court.get("name"), court.get("time_slot"))
        
        logger.info(f"Notifications sent: {notification_count_2}")
        logger.info(f"Notified slots tracked: {len(monitor.notified_slots)}")
        
        logger.info("\n" + "=" * 70)
        if notification_count_1 > 0 and notification_count_2 == 0:
            logger.info("✓ SUCCESS: Duplicate prevention is working!")
            logger.info(f"  First check: {notification_count_1} notifications")
            logger.info(f"  Second check: {notification_count_2} notifications (prevented {notification_count_1} duplicates)")
        else:
            logger.warning("✗ PROBLEM: Expected no notifications on second check")
        logger.info("=" * 70)
        
        return 0
        
    except Exception as e:
        logger.exception("Error during test")
        return 1

if __name__ == "__main__":
    sys.exit(main())
