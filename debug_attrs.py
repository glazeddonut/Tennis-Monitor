#!/usr/bin/env python
"""Debug script to check parent elements and data attributes."""

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
    
    print("Inspecting slot structure and parents...")
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
        
        for i, slot in enumerate(slots[:2]):  # Show first 2
            text = slot.inner_text().strip()
            
            print(f"\nSlot {i}: {text}")
            print("-" * 80)
            
            # Check all attributes on this element
            attributes = slot.evaluate("el => Object.fromEntries(Array.from(el.attributes, a => [a.name, a.value]))")
            print(f"Attributes on slot:")
            for key, value in attributes.items():
                print(f"  {key}: {value}")
            
            # Check parent
            parent_html = slot.evaluate("el => el.parentElement.outerHTML.substring(0, 300)")
            print(f"\nParent HTML (first 300 chars):\n{parent_html}")
            
            # Check for data attributes on parent
            parent_attrs = slot.evaluate("el => Object.fromEntries(Array.from(el.parentElement.attributes, a => [a.name, a.value]))")
            print(f"\nParent attributes:")
            for key, value in parent_attrs.items():
                print(f"  {key}: {value[:100] if len(value) > 100 else value}")
            
            # Check siblings
            sibling_html = slot.evaluate("el => el.previousElementSibling ? el.previousElementSibling.outerHTML.substring(0, 200) : 'no previous sibling'")
            print(f"\nPrevious sibling: {sibling_html}")
        
        page.close()
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
