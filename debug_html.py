#!/usr/bin/env python
"""Debug script to see the actual HTML structure of slots."""

import sys
import os

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
    
    print("Inspecting slot HTML structure...")
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
            # Get the outer HTML
            outer_html = slot.evaluate("el => el.outerHTML")
            inner_html = slot.evaluate("el => el.innerHTML")
            text = slot.inner_text().strip()
            
            print(f"\n{'='*80}")
            print(f"Slot {i}: {text}")
            print(f"{'='*80}")
            print(f"outerHTML:\n{outer_html}\n")
            print(f"innerHTML:\n{inner_html}\n")
        
        page.close()
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
