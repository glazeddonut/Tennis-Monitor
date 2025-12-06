#!/usr/bin/env python3
"""Utility to discover and print court ID to name mapping from Halbooking.

This script fetches all available slots and extracts the numeric court IDs
from the mdsende payload, then displays what the scraped court names are.
Useful for setting up PW_COURT_MAP in your .env file.

Usage:
  python map_courts.py
"""

import sys
import os
import logging
from pathlib import Path
from collections import defaultdict

# Ensure src is in path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)
logger = logging.getLogger(__name__)

# Import config and scraper
from tennis_monitor.config import get_config
from tennis_monitor.scraper import PlaywrightBookingClient


def main() -> int:
    """Fetch all availability and extract court mappings."""
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
        
        logger.info("Fetching all available courts (without filtering)...")
        # Temporarily disable the court map so we see the raw court_num
        original_court_map = client.court_map
        client.court_map = {}  # Empty mapping to see raw IDs
        
        all_courts = client.get_available_courts()
        
        # Restore the original court map
        client.court_map = original_court_map
        
        logger.info("Found %d total availability entries\n", len(all_courts))
        
        # Show detailed info about each entry to help identify court names
        logger.info("=== Detailed Availability ===")
        for i, court in enumerate(all_courts[:20], 1):  # Show first 20
            logger.info(
                "[%d] ID=%s court_num=%s name=%s time=%s text='%s'",
                i,
                court.get("id"),
                court.get("court_num"),
                court.get("name"),
                court.get("time_slot"),
                court.get("text"),
            )
        
        logger.info("\n")
        
        # Build a mapping of court_num -> set of names seen
        court_mapping = defaultdict(set)
        for court in all_courts:
            court_num = court.get("court_num", "unknown")
            # Since we disabled court_map, the name should be like "court-9"
            # But let's also check the mdsende payload for the actual numeric ID
            if court_num and court_num != "":
                # Try to figure out what the friendly name should be
                # by looking at patterns in the data
                court_mapping[court_num].add(court.get("name", "unknown"))
        
        logger.info("=== Court ID Mapping ===")
        logger.info("Add this to your .env as PW_COURT_MAP (adjust names as needed):\n")
        
        mapping_entries = []
        for court_num in sorted(court_mapping.keys()):
            names = list(court_mapping[court_num])
            # The fallback name is like "court-9", so extract the number
            # but the actual court name you see on the website might be different
            logger.info("Court ID %s: seen as %s", court_num, ", ".join(names))
            
            # Suggest a mapping entry (user will need to customize the right-hand side)
            mapping_entries.append(f"{court_num}:Court{court_num}")
        
        suggested_map = ",".join(mapping_entries)
        logger.info("\nSuggested PW_COURT_MAP (edit the court names to match your site):")
        logger.info("PW_COURT_MAP=%s\n", suggested_map)
        
        # Now re-fetch WITH a simple mapping to show what names would be returned
        logger.info("=== Sample with simple mapping ===")
        simple_map = {cid: f"Court{cid}" for cid in court_mapping.keys()}
        client.court_map = simple_map
        
        filtered_courts = client.get_available_courts()
        
        logger.info("With simple mapping (Court{id}), found %d entries:", len(filtered_courts))
        unique_courts = set(c.get("name") for c in filtered_courts)
        for court_name in sorted(unique_courts):
            count = len([c for c in filtered_courts if c.get("name") == court_name])
            logger.info("  %s: %d slots", court_name, count)
        
        return 0
    
    except Exception:
        logger.exception("Error discovering court mapping")
        return 1


if __name__ == "__main__":
    sys.exit(main())
