#!/usr/bin/env python3
"""Debug script to inspect co-player page structure."""

import os
from playwright.sync_api import sync_playwright

base_url = "https://halbooking.dk/Admin/Booking.asp"
username = os.getenv("BOOKING_USERNAME")
password = os.getenv("BOOKING_PASSWORD")

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    page = browser.new_page()
    
    # Go to booking page
    page.goto(base_url)
    page.wait_for_load_state("networkidle")
    
    # Try to login if needed
    username_field = page.query_selector("input[name='username']")
    if username_field:
        print("Logging in...")
        username_field.fill(username)
        password_field = page.query_selector("input[name='password']")
        password_field.fill(password)
        page.click("input[type='submit']")
        page.wait_for_load_state("networkidle")
    
    # Navigate to booking page
    page.wait_for_timeout(2000)
    menu_btn = page.query_selector("[class*='dropdown']")
    if menu_btn:
        menu_btn.hover()
        page.wait_for_timeout(500)
    
    # Click on a court if available
    slots = page.query_selector_all("span.banefelt.btn_ledig")
    if slots:
        print(f"Found {len(slots)} slots, clicking first one...")
        slots[0].click()
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(2000)
        
        # Now we should be on the co-player selection page
        print("\n=== CO-PLAYER PAGE STRUCTURE ===")
        
        # Get the page HTML
        html = page.inner_html("body")
        
        # Find all table rows with player names
        rows = page.query_selector_all("tr")
        print(f"\nFound {len(rows)} table rows:")
        for i, row in enumerate(rows[:10]):  # First 10 rows
            text = row.inner_text()
            if text and len(text) > 0:
                print(f"\nRow {i}:")
                print(f"  Text: {text[:100]}")
                
                # Check for different button classes
                btn = row.query_selector("button")
                if btn:
                    print(f"  Button class: {btn.get_attribute('class')}")
                    print(f"  Button text: {btn.inner_text()}")
                
                senmedbtn = row.query_selector(".senmedbtn")
                if senmedbtn:
                    print(f"  Found .senmedbtn: {senmedbtn.inner_text()}")
                
                # Check for onclick
                onclick_elem = row.query_selector("[onclick]")
                if onclick_elem:
                    print(f"  Found onclick: {onclick_elem.get_attribute('onclick')[:80]}")
        
        # Look for buttons with "Vælg" text
        print("\n=== BUTTONS WITH 'Vælg' ===")
        buttons = page.query_selector_all("button, input[type='button'], span[onclick]")
        for btn in buttons:
            text = btn.inner_text()
            if "Vælg" in text:
                print(f"Found: {text} - class: {btn.get_attribute('class')}")
        
        input("Press Enter to close browser...")
    
    browser.close()
