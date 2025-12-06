#!/usr/bin/env python
"""Test that notification tracking resets daily."""

import sys
import os
import logging
from datetime import date, timedelta
from unittest.mock import patch

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
    logger.info("Testing daily reset of notification tracking")
    logger.info("=" * 70)
    
    try:
        config = get_config()
        monitor = TennisMonitor(config)
        
        # Simulate day 1
        logger.info("\n[DAY 1] First availability check...")
        with patch('tennis_monitor.monitor.date') as mock_date:
            mock_date.today.return_value = date(2025, 12, 6)
            mock_date.side_effect = lambda *args, **kw: date(*args, **kw)
            
            monitor._reset_daily_notification_tracking()
            available = monitor.check_availability()
            
            notification_count_1 = 0
            for court in available:
                if monitor._should_notify(court):
                    notification_count_1 += 1
            
            logger.info(f"Notifications sent on Day 1: {notification_count_1}")
            logger.info(f"Notified slots tracked: {len(monitor.notified_slots)}")
            day1_notified = len(monitor.notified_slots)
        
        # Simulate day 2 - should reset
        logger.info("\n[DAY 2] Next day availability check...")
        with patch('tennis_monitor.monitor.date') as mock_date:
            mock_date.today.return_value = date(2025, 12, 7)  # Next day
            mock_date.side_effect = lambda *args, **kw: date(*args, **kw)
            
            monitor._reset_daily_notification_tracking()
            available = monitor.check_availability()
            
            notification_count_2 = 0
            for court in available:
                if monitor._should_notify(court):
                    notification_count_2 += 1
            
            logger.info(f"Notifications sent on Day 2: {notification_count_2}")
            logger.info(f"Notified slots tracked: {len(monitor.notified_slots)}")
            day2_notified = len(monitor.notified_slots)
        
        logger.info("\n" + "=" * 70)
        if notification_count_1 > 0 and notification_count_2 > 0 and day2_notified > 0:
            logger.info("✓ SUCCESS: Daily reset is working!")
            logger.info(f"  Day 1: {notification_count_1} notifications, tracked {day1_notified} slots")
            logger.info(f"  Day 2: {notification_count_2} notifications, tracked {day2_notified} slots (reset occurred)")
        else:
            logger.warning("✗ PROBLEM: Expected notifications on both days")
        logger.info("=" * 70)
        
        return 0
        
    except Exception as e:
        logger.exception("Error during test")
        return 1

if __name__ == "__main__":
    sys.exit(main())
