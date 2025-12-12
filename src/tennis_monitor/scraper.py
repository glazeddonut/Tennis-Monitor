"""Playwright-based scraper adapter for booking systems without an API.

This module provides a `PlaywrightBookingClient` with the same high-level
methods as the `BookingSystemClient` so it can be used as a drop-in
adapter when a public API is not available.

Notes:
- The exact page structure for the booking site is unknown, so this file
  contains configurable CSS selectors (via environment variables) and
  clear TODOs where site-specific selectors must be supplied.
- The implementation uses Playwright's synchronous API to keep the
  booking client interface synchronous.
"""

import os
import logging
from typing import Dict, List, Optional
import re
from datetime import datetime

from playwright.sync_api import sync_playwright, Page, Browser, TimeoutError as PWTimeout


class PlaywrightBookingClient:
    """Scraper-based booking client using Playwright (synchronous API).

    Args:
        base_url: Base URL of the booking website (landing/login page).
        username: Optional username for login (if required by site).
        password: Optional password for login (if required).
        headless: Run browser headless (default True).
    """

    def __init__(
        self,
        base_url: str,
        username: Optional[str] = None,
        password: Optional[str] = None,
        headless: bool = True,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.username = username or os.getenv("BOOKING_USERNAME")
        self.password = password or os.getenv("BOOKING_PASSWORD")
        self.headless = headless
        
        # Browser session (persistent across calls, started lazily)
        self.browser = None
        self.playwright_obj = None
        self.page = None  # Persistent page to maintain session

        # Selectors that should be customized for the target booking site.
        # Provide these via environment variables or override after init.
        # Examples (site-specific):
        # - a selector for the login username input
        # - a selector for the login password input
        # - a selector that lists available courts on the availability page
        self.selector_login_username = os.getenv("PW_SELECTOR_LOGIN_USERNAME", "input#loginname")
        self.selector_login_password = os.getenv("PW_SELECTOR_LOGIN_PASSWORD", "input#password")
        self.selector_login_submit = os.getenv("PW_SELECTOR_LOGIN_SUBMIT", "span#sub")
        self.selector_availability_page = os.getenv("PW_SELECTOR_AVAILABILITY_PAGE", f"{self.base_url}/availability")
        self.selector_court_rows = os.getenv("PW_SELECTOR_COURT_ROWS", ".court-row")
        self.selector_court_name = os.getenv("PW_SELECTOR_COURT_NAME", ".court-name")
        self.selector_time_slot = os.getenv("PW_SELECTOR_TIME_SLOT", ".time-slot")
        self.selector_book_button = os.getenv("PW_SELECTOR_BOOK_BUTTON", ".book-button")
        # Halbooking-specific selectors
        self.selector_book_baner = os.getenv("PW_SELECTOR_BOOK_BANER", "div[title='Book baner']")
        self.selector_available_slot = os.getenv("PW_SELECTOR_AVAILABLE_SLOT", "span.banefelt.btn_ledig")
        # Optional mapping like "9:Court11,10:Court12"
        self.court_map = self._parse_court_map(os.getenv("PW_COURT_MAP", ""))
        self.logger = logging.getLogger(__name__)

    def _ensure_browser(self) -> None:
        """Lazily initialize and start the browser if not already running."""
        if self.browser is None or self.playwright_obj is None:
            self.logger.debug("Starting persistent browser session...")
            self.playwright_obj = sync_playwright().start()
            self.browser = self.playwright_obj.chromium.launch(headless=self.headless)
            self.logger.debug("Browser session started")
        
        # Create persistent page if needed
        if self.page is None:
            self.logger.debug("Creating persistent page...")
            self.page = self.browser.new_page()
            self.logger.debug("Persistent page created")
    
    def _close_browser(self) -> None:
        """Close the persistent browser session."""
        if self.page is not None:
            try:
                self.logger.debug("Closing persistent page...")
                self.page.close()
            except Exception as e:
                self.logger.warning("Error closing page: %s", e)
            finally:
                self.page = None
        
        if self.browser is not None:
            try:
                self.logger.debug("Closing browser session...")
                self.browser.close()
            except Exception as e:
                self.logger.warning("Error closing browser: %s", e)
            finally:
                self.browser = None
        
        if self.playwright_obj is not None:
            try:
                self.playwright_obj.stop()
            except Exception as e:
                self.logger.warning("Error stopping Playwright: %s", e)
            finally:
                self.playwright_obj = None
    
    def __del__(self):
        """Ensure browser is closed when object is destroyed."""
        self._close_browser()

    def login(self, page: Page) -> None:
        """Perform login on Halbooking systems (Bootstrap modal-based).
        
        Halbooking uses a Bootstrap modal for login. This method:
        1. Clicks the Login link (identified by data-toggle="modal")
        2. Waits for the modal (#loginModal) to appear
        3. Fills in username/password in the form
        4. Submits and waits for login to complete
        
        Login credentials are taken from `self.username` and `self.password`.
        If either is missing, login is skipped.
        
        Works in both headless and headful modes.
        """
        if not self.username or not self.password:
            return

        try:
            # Step 1: Click the Login link (Halbooking uses data-toggle="modal")
            login_link_selectors = [
                'a[data-toggle="modal"][data-target="#loginModal"]',
                'a[data-toggle="modal"]',
                "a:has-text('Login')",
                "button:has-text('Login')",
            ]
            
            login_clicked = False
            for selector in login_link_selectors:
                try:
                    link = page.query_selector(selector)
                    if link:
                        link.click()
                        login_clicked = True
                        break
                except Exception:
                    continue
            
            if not login_clicked:
                # No login link found - check if already logged in by looking for logout link
                logout_link = page.query_selector("span[onclick*='logud']")
                if logout_link:
                    self.logger.info("No login link found but logout link detected. Already logged in.")
                    return
                else:
                    # Neither login nor logout link found - this is a fatal error
                    error_msg = (
                        "Could not find login or logout link on the page. "
                        "Page structure may have changed or we're on the wrong page."
                    )
                    self.logger.error("FATAL: %s", error_msg)
                    # Try to send alert via notification
                    try:
                        from .notifications import NotificationManager
                        from .config import get_config
                        config = get_config()
                        notif_mgr = NotificationManager(config.notifications)
                        notif_mgr.notify_alert("Tennis Monitor Error", error_msg)
                    except Exception as e:
                        self.logger.warning("Could not send error notification: %s", e)
                    # Raise error so the caller knows something is wrong
                    raise RuntimeError(f"FATAL: {error_msg}")
            
            # Step 2: Wait for modal to appear (look for username input in the modal)
            try:
                page.wait_for_selector(self.selector_login_username, timeout=5000)
            except PWTimeout:
                self.logger.warning(
                    "Login modal did not appear in time. Waited for selector: %s",
                    self.selector_login_username,
                )
                return
            
            # Step 3: Fill in credentials
            page.fill(self.selector_login_username, self.username)
            page.fill(self.selector_login_password, self.password)
            
            # Step 4: Submit login form
            # Halbooking uses a <span> with onclick handler instead of a button
            submit_el = page.query_selector(self.selector_login_submit)
            if submit_el:
                submit_el.click()
            else:
                self.logger.warning(
                    "Could not find submit button with selector: %s",
                    self.selector_login_submit,
                )
            
            # Step 5: Wait for login to complete (longer timeout for network operations)
            try:
                page.wait_for_load_state("networkidle", timeout=10000)
            except PWTimeout:
                self.logger.debug("Network idle timeout (expected in some headless setups)")
            
            # Step 5.5: Close the login modal if it's still open (sometimes modal stays open)
            try:
                # Try to close modal by pressing Escape or clicking backdrop
                page.keyboard.press("Escape")
                page.wait_for_timeout(500)
                self.logger.debug("Modal close attempt (Escape key)")
            except Exception:
                pass
            
            # Step 6: Add a small delay to ensure page has settled
            page.wait_for_timeout(1000)

            # Step 7: Detect login success (works in headless and headful modes)
            # Strategy: Look for the "Log ud" (logout) link to confirm login succeeded
            logged_in = False
            try:
                # Look for the logout link as confirmation of login
                logout_link = page.query_selector("span[onclick*='logud']")
                if logout_link:
                    self.logger.debug("Found logout link")
                    logged_in = True
                else:
                    self.logger.debug("No logout link found")
            except Exception as e:
                self.logger.debug("Error checking for logout link: %s", e)
            
            # Fallback: check if login form is hidden
            if not logged_in:
                try:
                    username_input = page.query_selector(self.selector_login_username)
                    if not username_input:
                        self.logger.debug("Login form not found on page - likely logged in")
                        logged_in = True
                    elif not username_input.is_visible():
                        self.logger.info("Login form hidden - login likely succeeded")
                        # Wait a moment for page to fully load, then recheck for logout link
                        page.wait_for_timeout(1000)
                        try:
                            logout_link_recheck = page.query_selector("span[onclick*='logud']")
                            if logout_link_recheck:
                                self.logger.debug("Found logout link on recheck - confirming login")
                                logged_in = True
                            else:
                                self.logger.debug("Logout link still not found after recheck")
                                logged_in = True  # Assume logged in if form is hidden
                        except Exception:
                            logged_in = True  # Assume logged in if form is hidden
                    else:
                        self.logger.warning("Login form still visible - login may have failed")
                except Exception as e:
                    self.logger.debug("Error checking login form visibility: %s", e)
            
            # Additional fallback: check for other logged-in indicators
            if not logged_in:
                logged_in_selectors = [
                    "a:has-text('Log out')",
                    "a:has-text('Logout')",
                    "a#logout",
                    "button:has-text('Logout')",
                ]
                for sel in logged_in_selectors:
                    try:
                        el = page.query_selector(sel)
                        if el:
                            self.logger.info("Detected logged-in indicator: %s", sel)
                            logged_in = True
                            break
                    except Exception:
                        continue
            
            if logged_in:
                self.logger.info("Login confirmed successful")
            else:
                self.logger.warning("Could not confirm login success, but proceeding anyway (works in headless mode)")
            
        except Exception:
            self.logger.exception("Login error")

    def _parse_court_map(self, raw: str) -> Dict[str, str]:
        """Parse PW_COURT_MAP env var into a mapping of court_num->name.

        Example: "9:Court11,10:Court12"
        """
        mapping: Dict[str, str] = {}
        if not raw:
            return mapping
        pairs = [p.strip() for p in raw.split(",") if p.strip()]
        for pair in pairs:
            if ":" in pair:
                k, v = pair.split(":", 1)
                mapping[k.strip()] = v.strip()
        return mapping

    def _inspect_page(self, page: Page, label: str = "Page Inspection") -> None:
        """Inspect and log the current page state (for debugging selector mismatches).
        
        This method logs details about what's on the page to help diagnose
        why selectors are not matching.
        """
        self.logger.debug("=== %s ===", label)
        self.logger.debug("Current URL: %s", page.url)
        
        # Try to find Book baner (exact match)
        baner_count = len(page.query_selector_all(self.selector_book_baner))
        self.logger.debug("Found %d element(s) matching Book baner selector: %s", baner_count, self.selector_book_baner)
        
        # Try to find slots
        slot_count = len(page.query_selector_all(self.selector_available_slot))
        self.logger.debug("Found %d element(s) matching slot selector: %s", slot_count, self.selector_available_slot)
        
        # Try to find any span with banefelt class (more lenient)
        try:
            banefelt_spans = page.query_selector_all("span.banefelt")
            self.logger.debug("Found %d span.banefelt elements (any state)", len(banefelt_spans))
            for i, span in enumerate(banefelt_spans[:3]):  # log first 3
                classes = span.get_attribute("class") or ""
                onclick = span.get_attribute("onclick") or ""
                self.logger.debug(
                    "  [%d] class=%s onclick=%s",
                    i,
                    classes,
                    onclick[:50] + "..." if len(onclick) > 50 else onclick,
                )
        except Exception as e:
            self.logger.debug("Could not inspect span.banefelt: %s", e)
        
        # Try to find all divs with title attribute (case-insensitive check for Book baner specifically)
        try:
            all_divs_with_title = page.query_selector_all("div[title]")
            self.logger.debug("Found %d div[title] elements total; checking titles:", len(all_divs_with_title))
            for i, div in enumerate(all_divs_with_title[:10]):  # log first 10
                title = div.get_attribute("title") or ""
                if "book" in title.lower():  # only log divs that mention "book"
                    self.logger.debug("  [%d] title='%s'", i, title)
        except Exception as e:
            self.logger.debug("Could not inspect div[title]: %s", e)
        
        self.logger.debug("=== End Inspection ===")



    def _parse_mdsende(self, onclick: str) -> Optional[tuple]:
        """Parse the mdsende onclick and extract (date, court_num, start, end).

        Returns None if parsing fails.
        """
        if not onclick:
            return None
        # Find quoted strings inside the function call
        quoted = re.findall(r"'(.*?)'", onclick)
        if len(quoted) < 3:
            return None
        third = quoted[2]
        parts = third.split(";")
        # Expected parts: [date_dd-mm-YYYY, '2', court_num, start, end, ...]
        if len(parts) < 5:
            return None
        date_ddmmy = parts[0]
        try:
            day, month, year = date_ddmmy.split("-")
            date_iso = f"{year}-{month}-{day}"
        except Exception:
            date_iso = date_ddmmy
        court_num = parts[2]
        start = parts[3]
        end = parts[4]
        return (date_iso, court_num, start, end)

    def get_available_courts(self, date: Optional[str] = None) -> List[Dict]:
        """Scrape the booking site for available courts on the given date.

        Returns a list of dicts: {"id": str, "name": str, "time_slot": str}
        """
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")

        self._ensure_browser()  # Initialize persistent browser and page if needed
        results: List[Dict] = []
        try:
            page = self.page  # Use persistent page
            
            # Navigate to base or availability page
            try:
                page.goto(self.selector_availability_page, timeout=15000)
            except Exception:
                # fallback to base url
                page.goto(self.base_url, timeout=15000)

            # Attempt login if necessary
            self.login(page)
            
            # First try Halbooking-specific flow: click the "Book baner"
            # and collect `span.banefelt.btn_ledig` elements that contain
            # an `onclick="mdsende(...)"` payload. Parse those payloads
            # with `_parse_mdsende` to return structured availability.
            try:
                # Check if we're already logged in (no "Book baner" button visible)
                # In that case, we need to invoke the "Banebooking" menu item instead
                self.logger.info("Checking for login status...")
                baner_btn = page.query_selector(self.selector_book_baner)
                
                if baner_btn:
                    # Not logged in yet, "Book baner" button is visible
                    self.logger.debug("Book baner element found; attempting navigation to: %s", f"{self.base_url}/newlook/proc_baner.asp")
                else:
                    # Already logged in, look for "Banebooking" menu item and invoke it
                    self.logger.info("No Book baner button found; checking for Banebooking menu item (already logged in)")
                    
                    # First, hover over the "Menu" dropdown to reveal menu items
                    menu_toggle = page.query_selector("a.dropdown-toggle")
                    if menu_toggle:
                        self.logger.info("Found Menu dropdown toggle; hovering to reveal menu items")
                        try:
                            menu_toggle.hover()
                            page.wait_for_timeout(500)  # Give dropdown time to appear
                            self.logger.debug("Menu dropdown hovered")
                        except Exception as e:
                            self.logger.warning("Failed to hover Menu toggle: %s", e)
                    
                    # Now find and invoke the "Banebooking" menu item's onclick directly
                    # This will navigate to proc_baner.asp with all slots ready
                    menu_items = page.query_selector_all("li.nobr.menu_ny_li a.menu_ny")
                    if menu_items:
                        for menu_item in menu_items:
                            text = menu_item.inner_text().strip().upper()
                            if "BANEBOOKING" in text:
                                self.logger.info("Found Banebooking menu item; invoking onclick handler")
                                try:
                                    # Get the onclick attribute and execute it directly via JavaScript
                                    onclick = menu_item.get_attribute("onclick") or ""
                                    if onclick:
                                        self.logger.debug("Executing onclick: %s", onclick)
                                        page.evaluate(onclick)
                                        page.wait_for_timeout(2000)  # Give page time to load
                                        self.logger.debug("Banebooking onclick executed; proc_baner.asp page should now be loaded")
                                    else:
                                        self.logger.warning("No onclick attribute found on Banebooking menu item")
                                except Exception as e:
                                    self.logger.warning("Failed to execute Banebooking onclick: %s", e)
                                break
                    else:
                        self.logger.warning("No Banebooking menu items found; trying direct navigation to proc_baner.asp")
                        try:
                            baner_url = os.getenv("PW_BANER_URL", f"{self.base_url}/newlook/proc_baner.asp")
                            page.goto(baner_url, timeout=10000)
                            page.wait_for_timeout(1500)
                            self.logger.debug("Direct navigation to proc_baner.asp completed")
                        except Exception as e:
                            self.logger.warning("Direct navigation failed: %s", e)
                
                # For the "Book baner" flow (when not logged in), navigate to the page
                if baner_btn:
                    baner_url = os.getenv("PW_BANER_URL", f"{self.base_url}/newlook/proc_baner.asp")
                    try:
                        self.logger.info("Navigating to Book baner page: %s", baner_url)
                        page.goto(baner_url, timeout=10000)
                        page.wait_for_timeout(1500)
                        self.logger.debug("Book baner page loaded")
                    except Exception as e:
                        self.logger.warning(
                            "Direct navigation to Book baner failed (%s); "
                            "continuing to search for slots",
                            type(e).__name__,
                        )

                # Wait briefly for available slot elements
                self.logger.debug("Waiting for slot elements with selector: %s", self.selector_available_slot)
                try:
                    page.wait_for_selector(self.selector_available_slot, timeout=2500)
                    self.logger.debug("Slot elements appeared")
                except PWTimeout:
                    # No halbooking slot elements found in time
                    self.logger.warning(
                        "No Halbooking slot elements found within 2.5s using selector: %s",
                        self.selector_available_slot,
                    )
                    # Inspect the page to help diagnose the issue
                    self._inspect_page(page, "After waiting for slots (none found)")


                slots = page.query_selector_all(self.selector_available_slot)
                self.logger.info(
                    "Found %d candidate slot elements using selector: %s",
                    len(slots),
                    self.selector_available_slot,
                )
                
                # Track unknown courts for validation
                unknown_courts = set()
                
                for idx, el in enumerate(slots):
                    try:
                        onclick = el.get_attribute("onclick") or ""
                        parsed = self._parse_mdsende(onclick)
                        title = el.get_attribute("title") or ""
                        text = el.inner_text().strip() or title or ""

                        if parsed:
                            date_iso, court_num, start, end = parsed
                            
                            # VALIDATION: Check if court_num is in the configured map
                            if self.court_map and court_num not in self.court_map:
                                unknown_courts.add(court_num)
                            
                            name = self.court_map.get(court_num, f"court-{court_num}")
                            rec_id = f"{court_num}:{date_iso}:{start}"
                            time_slot = f"{start}-{end}"
                            results.append({
                                "id": rec_id,
                                "name": name,
                                "date": date_iso,
                                "time_slot": time_slot,
                                "court_num": court_num,
                                "onclick": onclick,
                                "title": title,
                                "text": text,
                            })
                        else:
                            # fallback generic entry
                            rec_id = f"slot-{idx}"
                            results.append({
                                "id": rec_id,
                                "name": title or f"slot-{idx}",
                                "date": date,
                                "time_slot": text,
                                "court_num": "",
                                "onclick": onclick,
                                "title": title,
                                "text": text,
                            })
                    except Exception:
                        self.logger.exception("Error parsing slot element at index %d", idx)
                        continue
                
                # If unknown courts were detected, raise an exception
                if unknown_courts:
                    msg = f"Unknown court IDs detected: {', '.join(sorted(unknown_courts))}. " \
                          f"Current court map: {self.court_map}. " \
                          f"Please update PW_COURT_MAP environment variable."
                    self.logger.error(msg)
                    raise ValueError(msg)

                # If we found any Halbooking-style slots, return them.
                if results:
                    self.logger.info("Returning %d Halbooking-style availability entries", len(results))
                    return results
                else:
                    self.logger.info("No Halbooking-style slots found; will try availability URL template/fallback")
            except Exception:
                # If anything in the Halbooking path fails, fall back
                # to the more generic availability flow below.
                self.logger.exception("Unexpected error during Halbooking availability parsing; falling back")
                pass

            # Fallback site-specific navigation to reach availability for `date`.
            # For many systems you might need to select a date, or append a
            # query param like ?date=YYYY-MM-DD. Allow that via env var.
            availability_url_template = os.getenv("PW_AVAILABILITY_URL_TEMPLATE")
            if availability_url_template:
                url = availability_url_template.format(date=date)
                try:
                    page.goto(url, timeout=15000)
                except Exception:
                    pass

                # Give the page a moment to load interactive content
                try:
                    page.wait_for_load_state("networkidle", timeout=5000)
                except PWTimeout:
                    pass

                # Find court rows using configured selector and extract name/time
                rows = page.query_selector_all(self.selector_court_rows)
                for idx, row in enumerate(rows):
                    try:
                        name_el = row.query_selector(self.selector_court_name)
                        time_el = row.query_selector(self.selector_time_slot)
                        book_el = row.query_selector(self.selector_book_button)

                        name = name_el.inner_text().strip() if name_el else f"court-{idx}"
                        time_slot = time_el.inner_text().strip() if time_el else ""
                        court_id = row.get_attribute("data-id") or name

                        # Only include if has a time slot available (site-dependent)
                        if time_slot:
                            results.append({"id": court_id, "name": name, "time_slot": time_slot})
                    except Exception:
                        continue

            return results
        finally:
            pass  # Don't close page; keep it persistent for next check

    def book_court(self, court_id: str, time_slot: str) -> bool:
        """Execute complete Halbooking booking flow (5 steps).
        
        Step 1: Click available slot → Navigate to "Opret booking" page
        Step 2: Select co-player (Aksel Mahler Tolborg) → Click "Vælg"
        Step 3: Add to cart → Click "Læg i kurv"
        Step 4: Accept terms → Check "Jeg har læst og accepterer betingelserne"
        Step 5: Confirm booking → Click "Bekræft booking"
        
        Args:
            court_id: Court ID or name (e.g., "9" or "Court11")
            time_slot: Time slot in HH:MM-HH:MM format (e.g., "20:00-21:00")
            
        Returns:
            True if booking completed successfully, False otherwise
        """
        self._ensure_browser()
        page = self.page
        co_player_name = os.getenv("BOOKING_CO_PLAYER", "Aksel Mahler Tolborg")
        
        try:
            # Ensure we're on the booking page
            if "proc_baner.asp" not in page.url:
                page.goto(self.base_url, timeout=15000)
                self.login(page)
                # Navigate to Book baner
                book_baner = page.query_selector(self.selector_book_baner)
                if book_baner:
                    book_baner.click()
                    page.wait_for_load_state("networkidle", timeout=5000)
            
            # STEP 1: Find and click the available slot matching our court + time
            self.logger.info("STEP 1: Finding and clicking available slot for %s at %s", court_id, time_slot)
            slot_elements = page.query_selector_all(self.selector_available_slot)
            
            slot_clicked = False
            for slot_elem in slot_elements:
                try:
                    elem_text = slot_elem.inner_text()
                    
                    # Match by court ID or name and time
                    if (court_id in elem_text or str(court_id).replace("Court", "") in elem_text) and time_slot in elem_text:
                        self.logger.info("Found matching slot, clicking...")
                        slot_elem.click()
                        page.wait_for_load_state("networkidle", timeout=5000)
                        slot_clicked = True
                        break
                except Exception as e:
                    self.logger.debug("Error checking slot: %s", e)
                    continue
            
            if not slot_clicked:
                self.logger.warning("Could not find matching slot to click")
                return False
            
            # STEP 2: Select co-player
            self.logger.info("STEP 2: Selecting co-player: %s", co_player_name)
            try:
                # Find the row with the co-player name
                co_player_rows = page.query_selector_all("tr")
                co_player_btn = None
                
                for row in co_player_rows:
                    if co_player_name in row.inner_text():
                        # Find the "Vælg" button in this row
                        co_player_btn = row.query_selector(".senmedbtn")
                        if co_player_btn:
                            self.logger.info("Found co-player button, clicking...")
                            co_player_btn.click()
                            page.wait_for_load_state("networkidle", timeout=5000)
                            break
                
                if not co_player_btn:
                    self.logger.warning("Could not find co-player button for %s", co_player_name)
                    return False
            except Exception as e:
                self.logger.exception("Error selecting co-player: %s", e)
                return False
            
            # STEP 3: Add to cart
            self.logger.info("STEP 3: Adding booking to cart")
            try:
                # Find the "Læg i kurv" button - it should have onclick with "add_booking"
                add_to_cart_btn = page.query_selector(".btn:has-text('Læg i kurv')")
                if not add_to_cart_btn:
                    # Alternative: search by onclick attribute
                    all_buttons = page.query_selector_all(".btn")
                    for btn in all_buttons:
                        if "add_booking" in (btn.get_attribute("onclick") or ""):
                            add_to_cart_btn = btn
                            break
                
                if add_to_cart_btn:
                    self.logger.info("Found 'Læg i kurv' button, clicking...")
                    add_to_cart_btn.click()
                    page.wait_for_load_state("networkidle", timeout=5000)
                else:
                    self.logger.warning("Could not find 'Læg i kurv' button")
                    return False
            except Exception as e:
                self.logger.exception("Error adding to cart: %s", e)
                return False
            
            # STEP 4: Accept terms
            self.logger.info("STEP 4: Accepting terms and conditions")
            try:
                # Find and click the checkbox for accepting terms
                terms_checkbox = page.query_selector("input#acc_beting")
                if terms_checkbox:
                    # Check if already checked
                    is_checked = terms_checkbox.get_attribute("checked")
                    if not is_checked:
                        self.logger.info("Checking terms checkbox...")
                        terms_checkbox.click()
                        page.wait_for_timeout(500)
                else:
                    self.logger.warning("Could not find terms checkbox")
                    return False
            except Exception as e:
                self.logger.exception("Error accepting terms: %s", e)
                return False
            
            # STEP 5: Confirm booking
            self.logger.info("STEP 5: Confirming booking")
            try:
                # Find the "Bekræft booking" button
                confirm_btn = page.query_selector(".btn:has-text('Bekræft booking')")
                if not confirm_btn:
                    # Alternative: search for button with 'checkud' in onclick
                    all_buttons = page.query_selector_all(".btn")
                    for btn in all_buttons:
                        onclick = btn.get_attribute("onclick") or ""
                        if "checkud" in onclick:
                            confirm_btn = btn
                            break
                
                if confirm_btn:
                    self.logger.info("Found 'Bekræft booking' button, clicking...")
                    confirm_btn.click()
                    page.wait_for_load_state("networkidle", timeout=5000)
                else:
                    self.logger.warning("Could not find 'Bekræft booking' button")
                    return False
            except Exception as e:
                self.logger.exception("Error confirming booking: %s", e)
                return False
            
            # Verify booking was successful by looking for receipt page
            self.logger.info("STEP 6: Verifying booking success")
            try:
                # Look for receipt/confirmation element
                receipt = page.query_selector(".strong:has-text('Booking')")
                if receipt:
                    self.logger.info("Booking receipt found - booking successful!")
                    return True
                
                # Fallback: check if page contains booking confirmation text
                page_text = page.inner_text()
                if "Din kvittering" in page_text or "Booking:" in page_text:
                    self.logger.info("Booking confirmation detected - booking successful!")
                    return True
                
                self.logger.warning("Could not verify booking success")
                return False
            except Exception as e:
                self.logger.exception("Error verifying booking: %s", e)
                # Even if verification fails, booking might have gone through
                return False
                
        except Exception as e:
            self.logger.exception("Unexpected error during booking: %s", e)
            return False
        finally:
            pass  # Keep persistent page
