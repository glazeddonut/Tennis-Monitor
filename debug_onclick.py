#!/usr/bin/env python
"""Debug script to see the actual onclick payloads - full."""

import sys
import os
import re

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from tennis_monitor.scraper import PlaywrightBookingClient
from tennis_monitor.config import get_config

def main():
    config = get_config()
    
    scraper = PlaywrightBookingClient(
        config.booking_system.url,
        config.booking_system.username,
        config.booking_system.password,
    )
    
    print("Fetching slots to inspect onclick payloads...")
    print("=" * 80)
    
    scraper._ensure_browser()
    
    try:
        page = scraper.browser.new_page()
        baner_url = "https://example-tennis-club.dk/newlook/proc_baner.asp"
        
        page.goto(baner_url, timeout=10000)
        page.wait_for_timeout(1500)
        
        # Get all available slots
        slots = page.query_selector_all("span.banefelt.btn_ledig")
        
        print(f"Found {len(slots)} available slots\n")
        
        for i, slot in enumerate(slots[:3]):  # Show first 3
            onclick = slot.get_attribute("onclick") or ""
            title = slot.get_attribute("title") or ""
            text = slot.inner_text().strip() or ""
            
            print(f"\nSlot {i}:")
            print(f"  text: {text}")
            print(f"  title: '{title}'")
            print(f"  onclick length: {len(onclick)} chars")
            print(f"  onclick: {onclick}")
            
            # Try parsing
            quoted = re.findall(r"'(.*?)'", onclick)
            print(f"  quoted strings count: {len(quoted)}")
            for j, q in enumerate(quoted):
                print(f"    [{j}]: {q[:100]}...")
            
            if len(quoted) >= 3:
                third = quoted[2]
                parts = third.split(";")
                print(f"  parsed parts from quoted[2]: {len(parts)} parts")
                for j, p in enumerate(parts[:6]):
                    print(f"    [{j}]: {p}")
            
        page.close()
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
