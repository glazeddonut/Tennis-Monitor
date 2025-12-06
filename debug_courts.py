#!/usr/bin/env python
"""Debug script to see what courts are being scraped."""

import sys
import os
import json

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from tennis_monitor.config import get_config
from tennis_monitor.booking import BookingSystemClient

def main():
    config = get_config()
    
    # Create booking client without filtering
    client = BookingSystemClient(
        config.booking_system.url,
        config.booking_system.username,
        config.booking_system.password,
        preferred_courts=None  # Don't filter yet
    )
    
    print("Fetching ALL available courts (no filtering)...")
    print("=" * 70)
    
    all_courts = client.scraper.get_available_courts()
    
    print(f"Total courts scraped: {len(all_courts)}\n")
    
    # Group by court name and time
    courts_by_name = {}
    for court in all_courts:
        name = court.get("name", "UNKNOWN")
        time_slot = court.get("time_slot", "UNKNOWN")
        court_num = court.get("court_num")
        
        if name not in courts_by_name:
            courts_by_name[name] = []
        courts_by_name[name].append(time_slot)
    
    print("Courts grouped by name and available times:")
    print("-" * 70)
    for name in sorted(courts_by_name.keys()):
        times = sorted(set(courts_by_name[name]))
        print(f"{name:15} → {', '.join(times)}")
    
    print("\n" + "=" * 70)
    print("Raw court data:")
    print("=" * 70)
    for i, court in enumerate(all_courts, 1):
        print(f"{i:2}. {court.get('name'):15} {court.get('time_slot')}  (court_num={court.get('court_num')})")
    
    print("\n" + "=" * 70)
    print("Now checking what matches YOUR preferences:")
    print(f"PREFERRED_COURTS: {config.user_preferences.preferred_courts}")
    print(f"PREFERRED_TIME_SLOTS: {config.user_preferences.preferred_time_slots}")
    print("=" * 70)
    
    matching = [
        court for court in all_courts
        if court.get("name") in config.user_preferences.preferred_courts
        and court.get("time_slot") in config.user_preferences.preferred_time_slots
    ]
    
    print(f"Matching courts: {len(matching)}\n")
    for court in matching:
        print(f"  ✓ {court.get('name')} at {court.get('time_slot')}")
    
    if not matching:
        print("  (No matches)")
        print("\nPossible issues:")
        print("1. Court names don't match (check capitalization, spaces)")
        print("2. Time slots don't match (check format HH:MM)")
        print("3. Check if court_num mapping is correct")

if __name__ == "__main__":
    main()
