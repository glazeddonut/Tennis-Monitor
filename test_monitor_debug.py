#!/usr/bin/env python
"""Debug script to trace monitor execution."""

import sys
import os
import logging

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from tennis_monitor.config import get_config
from tennis_monitor.monitor import TennisMonitor

# Configure detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)

logger = logging.getLogger(__name__)

def main():
    logger.info("=" * 60)
    logger.info("Starting debug monitor test")
    logger.info("=" * 60)
    
    try:
        logger.info("Loading config...")
        config = get_config()
        logger.info("Config loaded successfully")
        logger.info(f"  Booking URL: {config.booking_system.url}")
        logger.info(f"  Check interval: {config.monitoring.check_interval_seconds}s")
        logger.info(f"  Preferred courts: {config.user_preferences.preferred_courts}")
        logger.info(f"  Preferred times: {config.user_preferences.preferred_time_slots}")
        
        logger.info("Creating monitor...")
        monitor = TennisMonitor(config)
        logger.info("Monitor created successfully")
        
        logger.info("Running one check cycle (not full monitor loop)...")
        logger.info("Calling check_availability()...")
        available = monitor.check_availability()
        logger.info(f"check_availability() returned {len(available)} courts")
        for court in available:
            logger.info(f"  - {court}")
        
        logger.info("=" * 60)
        logger.info("Debug test completed successfully")
        logger.info("=" * 60)
        
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
    except Exception as e:
        logger.exception("Error during debug test")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
