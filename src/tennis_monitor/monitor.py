"""Main monitoring logic for tennis court availability."""

import asyncio
import logging
import time
import sys
from collections import deque
from typing import List, Dict, Optional, Set
from datetime import datetime, date
from apscheduler.schedulers.background import BackgroundScheduler
from .config import AppConfig, get_config
from .booking import BookingSystemClient, StructureValidationError
from .notifications import NotificationManager


logger = logging.getLogger(__name__)


class TennisMonitor:
    """Monitor tennis court availability and trigger bookings."""

    def __init__(self, config: Optional[AppConfig] = None):
        """Initialize the tennis monitor.
        
        Args:
            config: Application configuration. Defaults to loading from environment.
        """
        self.config = config or get_config()
        # Don't filter by preferred courts in booking client; let monitor handle full filtering
        self.booking_client = BookingSystemClient(
            self.config.booking_system.url,
            self.config.booking_system.api_key,
            preferred_courts=None,  # Don't filter here; monitor will filter by both court and time
        )
        self.notification_manager = NotificationManager(self.config.notifications)
        self.is_running = False
        
        # Track which slots we've already notified about (reset daily)
        self.notified_slots: Set[str] = set()
        self.notification_date: Optional[date] = None
        
        # Track monitoring stats for alive check
        self.checks_performed_today: int = 0
        self.slots_found_today: int = 0
        self.last_alive_check_date: Optional[date] = None
        
        # Store last found slots for PWA to display booking buttons
        self.last_found_slots: List[Dict] = []
        
        # Queue for pending bookings (user-requested via API)
        self.pending_bookings: deque = deque()
        
        # Scheduler for daily alive check
        self.scheduler: Optional[BackgroundScheduler] = None

    def check_availability(self) -> List[Dict]:
        """Check for available courts matching preferences.
        
        Returns:
            List of available courts matching user preferences
            
        Raises:
            StructureValidationError: If booking system structure validation fails
        """
        logger.debug("Calling booking_client.get_available_courts()...")
        available_courts = self.booking_client.get_available_courts()
        logger.info("Got %d total available courts from booking system", len(available_courts))
        
        # Filter by preferred courts and times
        logger.debug("Filtering by preferences: courts=%s, times=%s", 
                    self.config.user_preferences.preferred_courts,
                    self.config.user_preferences.preferred_time_slots)
        matching_courts = [
            court for court in available_courts
            if self._matches_preferences(court)
        ]
        
        logger.info("After filtering: %d courts match preferences", len(matching_courts))
        if matching_courts:
            for court in matching_courts:
                logger.info("Matching court: %s at %s", court.get("name"), court.get("time_slot"))
        
        return matching_courts

    def _matches_preferences(self, court: Dict) -> bool:
        """Check if a court matches user preferences.
        
        Args:
            court: Court information dictionary
            
        Returns:
            True if court matches preferences, False otherwise
        """
        preferred_courts = self.config.user_preferences.preferred_courts
        preferred_times = self.config.user_preferences.preferred_time_slots
        
        # Check if court name is in preferences
        court_name = court.get("name", "")
        if preferred_courts and court_name not in preferred_courts:
            return False
        
        # Check if time slot is in preferences
        # Time slot may be "18:00-19:00", extract start time "18:00"
        time_slot = court.get("time_slot", "")
        if preferred_times:
            # Extract start time from range (e.g., "18:00-19:00" -> "18:00")
            start_time = time_slot.split("-")[0] if time_slot else ""
            if start_time not in preferred_times:
                return False
        
        return True

    def _reset_daily_notification_tracking(self) -> None:
        """Reset notification tracking at the start of each new day."""
        today = date.today()
        if self.notification_date != today:
            self.notification_date = today
            self.notified_slots.clear()
            self.checks_performed_today = 0
            self.slots_found_today = 0
            logger.info("Daily notification tracking reset (date changed to %s)", today)

    def _send_alive_check(self) -> None:
        """Send daily 'I'm alive' notification."""
        try:
            if self.config.monitoring.alive_check_enabled:
                self.notification_manager.notify_alive(
                    self.checks_performed_today,
                    self.slots_found_today
                )
        except Exception:
            logger.exception("Error sending alive check notification")

    def _setup_alive_check_scheduler(self) -> None:
        """Setup the background scheduler for daily alive checks."""
        if not self.config.monitoring.alive_check_enabled:
            return
        
        try:
            self.scheduler = BackgroundScheduler()
            # Schedule alive check at specified hour (default 10:00)
            self.scheduler.add_job(
                self._send_alive_check,
                'cron',
                hour=self.config.monitoring.alive_check_hour,
                minute=0,
                second=0
            )
            self.scheduler.start()
            logger.info(
                "Alive check scheduler started (daily at %02d:00:00)",
                self.config.monitoring.alive_check_hour
            )
        except Exception:
            logger.exception("Failed to setup alive check scheduler")
            self.scheduler = None

    def _shutdown_alive_check_scheduler(self) -> None:
        """Shutdown the background scheduler."""
        if self.scheduler:
            try:
                self.scheduler.shutdown()
                logger.info("Alive check scheduler stopped")
            except Exception:
                logger.exception("Error shutting down alive check scheduler")

    def _get_slot_id(self, court: Dict) -> str:
        """Get a unique identifier for a court slot.
        
        Args:
            court: Court information dictionary
            
        Returns:
            Unique slot identifier (e.g., "Court11:18:00-19:00:2025-12-06")
        """
        return f"{court.get('name')}:{court.get('time_slot')}:{court.get('date')}"

    def _should_notify(self, court: Dict) -> bool:
        """Check if we should notify about this court slot.
        
        Args:
            court: Court information dictionary
            
        Returns:
            True if this is a new slot we haven't notified about, False if already notified
        """
        slot_id = self._get_slot_id(court)
        if slot_id in self.notified_slots:
            return False
        
        # Mark as notified
        self.notified_slots.add(slot_id)
        return True

    def process_pending_bookings(self) -> None:
        """Process any pending booking requests from the API.
        
        This runs during the monitoring loop, so the monitor thread
        (which owns the browser) can safely execute bookings.
        """
        while self.pending_bookings:
            booking_request = self.pending_bookings.popleft()
            court_name = booking_request.get("court_name")
            time_slot = booking_request.get("time_slot")
            
            logger.info("Processing pending booking: %s at %s", court_name, time_slot)
            
            try:
                success = self.booking_client.book_court(court_name, time_slot)
                
                if success:
                    logger.info("Successfully booked %s at %s", court_name, time_slot)
                    self.notification_manager.notify_booked({
                        "name": court_name,
                        "time_slot": time_slot
                    })
                else:
                    logger.warning("Failed to book %s at %s", court_name, time_slot)
                    self.notification_manager.notify_alert(
                        "Booking Failed",
                        f"Could not book {court_name} at {time_slot}"
                    )
            except Exception as e:
                logger.exception("Error processing booking request: %s", e)
                self.notification_manager.notify_alert(
                    "Booking Error",
                    f"Error booking {court_name}: {str(e)}"
                )

    def attempt_booking(self, court: Dict) -> bool:
        """Attempt to book a court if auto-booking is enabled.
        
        Args:
            court: Court information to book
            
        Returns:
            True if booking was successful, False otherwise
        """
        if not self.config.monitoring.auto_book_enabled:
            return False
        
        court_id = court.get("id")
        time_slot = court.get("time_slot")
        
        if not court_id or not time_slot:
            return False
        
        success = self.booking_client.book_court(court_id, time_slot)
        return success

    async def run_async(self) -> None:
        """Run the monitor asynchronously."""
        self.is_running = True
        try:
            while self.is_running:
                try:
                    available = self.check_availability()
                    
                    if available:
                        for court in available:
                            # Send notification
                            self.notification_manager.notify_available(court)
                            
                            # Attempt booking if enabled
                            if self.config.monitoring.auto_book_enabled:
                                if self.attempt_booking(court):
                                    self.notification_manager.notify_booked(court)
                except StructureValidationError as e:
                    logger.error("Structure validation error: %s", e)
                    # Send alert notification before stopping
                    self.notification_manager.notify_alert(
                        "Booking System Structure Changed",
                        str(e)
                    )
                    self.is_running = False
                    sys.exit(1)
                
                # Wait before next check
                await asyncio.sleep(self.config.monitoring.check_interval_seconds)
        except KeyboardInterrupt:
            self.is_running = False
            logger.info("Monitor stopped by user.")
        except Exception:
            logger.exception("Unexpected error in async monitor")
            raise

    def run(self) -> None:
        """Run the monitor (blocking call)."""
        self.is_running = True
        self._setup_alive_check_scheduler()
        
        try:
            while self.is_running:
                try:
                    # Process any pending booking requests from the API (queue-based)
                    if self.pending_bookings:
                        logger.debug("Processing %d pending booking requests", len(self.pending_bookings))
                        self.process_pending_bookings()
                    
                    # Reset daily notification tracking if needed
                    self._reset_daily_notification_tracking()
                    
                    logger.debug("Checking availability...")
                    available = self.check_availability()
                    logger.info("Found %d courts matching preferences", len(available))
                    
                    # Store last found slots (max 3 for PWA display)
                    self.last_found_slots = available[:3]
                    
                    # Track stats for alive check
                    self.checks_performed_today += 1
                    self.slots_found_today += len(available)
                    
                    if available:
                        for court in available:
                            # Only send notification if this is a NEW slot (not already notified)
                            if self._should_notify(court):
                                self.notification_manager.notify_available(court)
                                
                                # Attempt booking if enabled
                                if self.config.monitoring.auto_book_enabled:
                                    if self.attempt_booking(court):
                                        self.notification_manager.notify_booked(court)
                            else:
                                logger.debug("Already notified about %s at %s", 
                                           court.get("name"), court.get("time_slot"))
                    else:
                        logger.debug("No courts matching preferences found")
                        
                except StructureValidationError as e:
                    logger.error("Structure validation error: %s", e)
                    # Send alert notification before stopping
                    self.notification_manager.notify_alert(
                        "Booking System Structure Changed",
                        str(e)
                    )
                    self.is_running = False
                    sys.exit(1)
                except Exception as e:
                    logger.exception("Error during availability check (will retry): %s", e)
                    # Don't exit; just log and continue to next check
                
                # Wait before next check
                logger.debug("Waiting %d seconds before next check", self.config.monitoring.check_interval_seconds)
                time.sleep(self.config.monitoring.check_interval_seconds)
        except KeyboardInterrupt:
            self.is_running = False
            logger.info("Monitor stopped by user.")
        except Exception:
            logger.exception("Unexpected error in monitor")
            raise
        finally:
            self._shutdown_alive_check_scheduler()

    def stop(self) -> None:
        """Stop the monitor."""
        self.is_running = False
        self._shutdown_alive_check_scheduler()
