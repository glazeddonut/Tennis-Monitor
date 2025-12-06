#!/usr/bin/env python
"""Debug script to check if we're actually logged in."""

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
    
    print("Checking login status...")
    print("=" * 80)
    
    scraper._ensure_browser()
    
    try:
        page = scraper.browser.new_page()
        
        # Navigate to the base URL first
        print("Navigating to base URL...")
        page.goto(scraper.base_url, timeout=15000)
        page.wait_for_timeout(1000)
        
        # Check for login link
        login_link = page.query_selector("a[data-toggle='modal'][data-target='#loginModal']")
        if login_link:
            print("✓ Found login link - user NOT logged in yet")
        else:
            print("✓ No login link found - probably logged in")
        
        # Check for logout button
        logout_btn = page.query_selector("a[href*='logout'], button[href*='logout']")
        if logout_btn:
            print("✓ Found logout button - user IS logged in")
        else:
            print("✗ No logout button found")
        
        # Look for any user-related elements
        page_html = page.evaluate("() => document.body.outerHTML")
        if "logout" in page_html.lower():
            print("✓ Page contains 'logout' - likely logged in")
        elif "login" in page_html.lower():
            print("✗ Page contains 'login' - probably not logged in")
        
        # Now do the login
        print("\nAttempting login...")
        scraper.login(page)
        page.wait_for_timeout(2000)
        
        print("After login - checking status...")
        login_link = page.query_selector("a[data-toggle='modal'][data-target='#loginModal']")
        if login_link:
            print("✗ Login link still visible - login may have FAILED")
        else:
            print("✓ Login link gone - login probably succeeded")
        
        # Navigate to available courts page
        print("\nNavigating to Book baner page...")
        baner_url = "https://example-tennis-club.dk/newlook/proc_baner.asp"
        page.goto(baner_url, timeout=10000)
        page.wait_for_timeout(1500)
        
        # Check if we see the "login to book" message or actual bookable slots
        page_text = page.evaluate("() => document.body.innerText")
        
        if "login" in page_text.lower():
            print("✗ Page mentions 'login' - might not be authenticated")
        
        if "skal logge ind" in page_text.lower():
            print("✗ Danish 'skal logge ind' (must log in) found - NOT logged in!")
        
        # Get first slot and check what it shows
        slots = page.query_selector_all("span.banefelt.btn_ledig")
        if slots:
            first_slot = slots[0]
            onclick = first_slot.get_attribute("onclick") or ""
            data_toggle = first_slot.get_attribute("data-toggle") or ""
            
            print(f"\nFirst available slot:")
            print(f"  onclick: {onclick if onclick else '(empty)'}")
            print(f"  data-toggle: {data_toggle if data_toggle else '(empty)'}")
            
            if not onclick and data_toggle == "modal":
                print("\n✗ PROBLEM: Slots show login modal - user is NOT authenticated!")
                print("  Need to investigate the login process")
            else:
                print("\n✓ Slots have onclick - user is authenticated")
        
        page.close()
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
