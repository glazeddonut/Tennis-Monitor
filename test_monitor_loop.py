#!/usr/bin/env python
"""Test the full monitor loop for a few cycles."""

import sys
import os
import time
import logging

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from tennis_monitor.config import get_config
from tennis_monitor.monitor import TennisMonitor

# Configure detailed logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)

logger = logging.getLogger(__name__)

def main():
    logger.info("=" * 60)
    logger.info("Testing monitor loop (5 cycles, 10s intervals)")
    logger.info("=" * 60)
    
    try:
        config = get_config()
        # Override check interval for testing
        config.monitoring.check_interval_seconds = 10
        
        monitor = TennisMonitor(config)
        
        # Run 5 check cycles manually
        for cycle in range(1, 6):
            logger.info("=" * 60)
            logger.info("Cycle %d of 5", cycle)
            logger.info("=" * 60)
            
            try:
                available = monitor.check_availability()
                logger.info("Cycle %d result: %d courts match preferences", cycle, len(available))
                if available:
                    for court in available:
                        logger.info("  → %s at %s", court.get("name"), court.get("time_slot"))
                        # Send notification
                        monitor.notification_manager.notify_available(court)
            except Exception as e:
                logger.exception("Error in cycle %d: %s", cycle, e)
            
            if cycle < 5:
                logger.info("Waiting 10 seconds before next cycle...")
                time.sleep(10)
        
        logger.info("=" * 60)
        logger.info("Test completed successfully")
        logger.info("=" * 60)
        
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
    except Exception as e:
        logger.exception("Error during test")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
