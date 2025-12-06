"""Booking system interaction module using Playwright scraping."""

import os
import logging
from typing import Dict, List, Optional
from datetime import datetime
from .scraper import PlaywrightBookingClient


logger = logging.getLogger(__name__)


class StructureValidationError(Exception):
    """Raised when booking system structure validation fails (e.g., unknown courts detected)."""
    pass


class BookingSystemClient:
    """Client for interacting with booking systems via web scraping (Playwright).
    
    This client uses Playwright to scrape booking availability and perform
    bookings on systems like Halbooking that do not expose a public API.
    """

    def __init__(self, base_url: str, username: Optional[str] = None, password: Optional[str] = None, preferred_courts: Optional[List[str]] = None):
        """Initialize booking system client.
        
        Args:
            base_url: Base URL of the booking system (e.g., https://example.halbooking.dk)
            username: Optional username for login (defaults to BOOKING_USERNAME env var)
            password: Optional password for login (defaults to BOOKING_PASSWORD env var)
            preferred_courts: Optional list of preferred court names to filter results
        """
        self.base_url = base_url
        self.username = username or os.getenv("BOOKING_USERNAME")
        self.password = password or os.getenv("BOOKING_PASSWORD")
        self.preferred_courts = preferred_courts or []
        self.scraper = PlaywrightBookingClient(base_url, self.username, self.password)

    def get_available_courts(self, date: Optional[str] = None) -> List[Dict]:
        """Fetch available courts for a specific date via scraping.
        
        Filters results to only include preferred courts if specified.
        
        Args:
            date: Date to check (YYYY-MM-DD format). Defaults to today.
            
        Returns:
            List of available court information dictionaries matching preferences
            
        Raises:
            StructureValidationError: If booking system structure validation fails
                (e.g., unknown courts detected when using PW_COURT_MAP)
        """
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")
        
        try:
            all_courts = self.scraper.get_available_courts(date=date)
            
            # Filter by preferred courts if configured
            if self.preferred_courts:
                filtered = [c for c in all_courts if c.get("name") in self.preferred_courts]
                return filtered
            
            return all_courts
        except ValueError as e:
            # Structure validation error from scraper (e.g., unknown court IDs)
            logger.error("Booking system structure validation failed: %s", e)
            raise StructureValidationError(str(e)) from e
        except Exception as e:
            logger.exception("Error fetching available courts: %s", e)
            return []

    def book_court(self, court_id: str, time_slot: str) -> bool:
        """Book a specific court for a time slot via scraping.
        
        Args:
            court_id: ID of the court to book
            time_slot: Time slot in HH:MM format
            
        Returns:
            True if booking was successful, False otherwise
        """
        try:
            return self.scraper.book_court(court_id, time_slot)
        except Exception as e:
            logger.exception("Error booking court: %s", e)
            return False
