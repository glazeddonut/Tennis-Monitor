#!/usr/bin/env python3
"""Quick debug runner for testing PlaywrightBookingClient.get_available_courts() directly.

This script sets up DEBUG logging and calls the scraper's availability method
to help iterate and debug the Halbooking integration without running the full monitor loop.

Usage:
  python debug_run.py
  
or from VS Code: F5 with "Debug debug_run.py" configuration.
"""

import sys
import os
import logging
from pathlib import Path

# Ensure src is in path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Set up DEBUG logging before importing anything else
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)
logger = logging.getLogger(__name__)

# Import config and scraper
from tennis_monitor.config import get_config
from tennis_monitor.scraper import PlaywrightBookingClient


def main() -> int:
    """Run the scraper's get_available_courts method and print results."""
    try:
        logger.info("Loading configuration...")
        config = get_config()
        
        if not config.booking_system.url:
            logger.error("BOOKING_SYSTEM_URL not configured")
            return 1
        
        logger.info("Creating PlaywrightBookingClient for: %s", config.booking_system.url)
        client = PlaywrightBookingClient(
            base_url=config.booking_system.url,
            username=config.booking_system.username,
            password=config.booking_system.password,
            headless=os.getenv("BOOKING_HEADLESS", "true").lower() != "false",
        )
        
        logger.info("Scraper created. Starting get_available_courts()...")
        courts = client.get_available_courts()
        
        logger.info("Found %d available courts/slots:", len(courts))
        for idx, court in enumerate(courts, 1):
            logger.info(
                "  [%d] id=%s name=%s date=%s time_slot=%s court_num=%s",
                idx,
                court.get("id"),
                court.get("name"),
                court.get("date"),
                court.get("time_slot"),
                court.get("court_num"),
            )
        
        if courts:
            logger.info("\n=== First court entry (full details) ===")
            import json
            logger.info(json.dumps(courts[0], indent=2))
        
        return 0
    
    except Exception:
        logger.exception("Error in debug_run")
        return 1


if __name__ == "__main__":
    sys.exit(main())
