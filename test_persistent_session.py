#!/usr/bin/env python
"""Test if the persistent browser approach maintains login."""

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
    
    print("Testing persistent browser login session...")
    print("=" * 80)
    
    scraper._ensure_browser()
    
    try:
        # Page 1: Login
        print("\n1. Creating page 1 and logging in...")
        page1 = scraper.browser.new_page()
        page1.goto(scraper.base_url, timeout=15000)
        page1.wait_for_timeout(1000)
        
        scraper.login(page1)
        print("   ✓ Login completed on page 1")
        
        # Check login status on page 1
        login_link = page1.query_selector("a[data-toggle='modal'][data-target='#loginModal']")
        if login_link:
            print("   ✗ Login link still visible on page 1")
        else:
            print("   ✓ Login link gone on page 1")
        
        page1.close()
        
        # Page 2: Navigate to baner without explicit login
        print("\n2. Creating page 2 and navigating to baner (WITHOUT logging in again)...")
        page2 = scraper.browser.new_page()
        page2.goto("https://example-tennis-club.dk/newlook/proc_baner.asp", timeout=10000)
        page2.wait_for_timeout(1500)
        
        # Check if slots have onclick
        slots = page2.query_selector_all("span.banefelt.btn_ledig")
        if slots:
            first_slot = slots[0]
            onclick = first_slot.get_attribute("onclick") or ""
            
            if onclick and "mdsende" in onclick:
                print(f"   ✓ GOOD! Slots have mdsende onclick - session persisted!")
                print(f"     onclick: {onclick[:80]}...")
            elif first_slot.get_attribute("data-toggle") == "modal":
                print("   ✗ BAD! Slots show login modal - session LOST!")
            else:
                print(f"   ? Unclear state. onclick='{onclick}'")
        
        page2.close()
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
