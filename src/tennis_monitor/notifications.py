"""Notification system for tennis court alerts with logging."""

import logging
import os
import requests
from typing import Dict, Optional
from .config import NotificationConfig


logger = logging.getLogger(__name__)


class NotificationManager:
    """Manage notifications for court availability."""

    def __init__(self, config: NotificationConfig):
        """Initialize notification manager.
        
        Args:
            config: Notification configuration
        """
        self.config = config
        # Push notification settings
        self.push_service = os.getenv("PUSH_SERVICE", "ntfy")  # "ntfy" or "pushbullet"
        self.ntfy_topic = os.getenv("NTFY_TOPIC", "")  # e.g., "mytennistracker123"
        self.pushbullet_key = os.getenv("PUSHBULLET_API_KEY", "")

    def notify_available(self, court: Dict) -> None:
        """Send notification for available court.
        
        Args:
            court: Court information dictionary
        """
        message = self._format_message(court, "Available")

        try:
            if self.config.enable_email_alerts:
                self._send_email(message, court)

            if self.config.enable_push_notifications:
                self._send_push_notification(message, court)

            logger.info("Availability alert: %s", message)
        except Exception:
            logger.exception("Failed to send availability notification")

    def notify_booked(self, court: Dict) -> None:
        """Send notification for successful booking.
        
        Args:
            court: Court information dictionary
        """
        message = self._format_message(court, "Booked")

        try:
            if self.config.enable_email_alerts:
                self._send_email(message, court)

            if self.config.enable_push_notifications:
                self._send_push_notification(message, court)

            logger.info("Booking success: %s", message)
        except Exception:
            logger.exception("Failed to send booked notification")

    def notify_alert(self, title: str, message: str) -> None:
        """Send a critical alert notification (e.g., unexpected court structure).
        
        Args:
            title: Alert title
            message: Alert message
        """
        try:
            full_message = f"{title}: {message}"
            self._send_push_notification(full_message, None, is_alert=True)
            logger.warning("Alert sent: %s", full_message)
        except Exception:
            logger.exception("Failed to send alert notification")

    def _format_message(self, court: Dict, status: str) -> str:
        """Format a notification message.

        Args:
            court: Court information
            status: Status message (e.g., "Available", "Booked")
            
        Returns:
            Formatted message string
        """
        court_name = court.get("name", "Unknown")
        time_slot = court.get("time_slot", "Unknown")
        return f"Court {court_name} - {time_slot}: {status}"

    def _send_email(self, message: str, court: Dict) -> None:
        """Send email notification.

        Args:
            message: Message to send
            court: Court information
        """
        if not self.config.email_recipient:
            logger.debug("Email recipient not configured; skipping email")
            return

        # TODO: Implement email sending
        logger.info("[EMAIL] Would send to %s: %s", self.config.email_recipient, message)

    def _send_push_notification(self, message: str, court: Optional[Dict] = None, is_alert: bool = False) -> None:
        """Send push notification via configured service.

        Args:
            message: Message to send
            court: Court information (optional)
            is_alert: If True, marks as a critical alert
        """
        if self.push_service == "ntfy":
            self._send_ntfy(message, is_alert)
        elif self.push_service == "pushbullet":
            self._send_pushbullet(message, is_alert)
        else:
            logger.info("[PUSH] Would send push notification: %s", message)

    def _send_ntfy(self, message: str, is_alert: bool = False) -> None:
        """Send notification via ntfy.sh service.
        
        Args:
            message: Message to send
            is_alert: If True, uses higher priority
        """
        if not self.ntfy_topic:
            logger.warning("NTFY_TOPIC not configured; push notifications disabled")
            return

        try:
            url = f"https://ntfy.sh/{self.ntfy_topic}"
            headers = {
                "Title": "Tennis Court Alert" if is_alert else "Tennis Court Availability",
                "Priority": "high" if is_alert else "default",
            }
            response = requests.post(url, data=message, headers=headers, timeout=5)
            if response.status_code == 200:
                logger.debug("ntfy.sh notification sent successfully")
            else:
                logger.warning("ntfy.sh notification failed with status %d", response.status_code)
        except Exception:
            logger.exception("Failed to send ntfy.sh notification")

    def _send_pushbullet(self, message: str, is_alert: bool = False) -> None:
        """Send notification via Pushbullet service.
        
        Args:
            message: Message to send
            is_alert: If True, marks as alert (future use)
        """
        if not self.pushbullet_key:
            logger.warning("PUSHBULLET_API_KEY not configured; push notifications disabled")
            return

        try:
            url = "https://api.pushbullet.com/v2/pushes"
            headers = {
                "Access-Token": self.pushbullet_key,
                "Content-Type": "application/json",
            }
            data = {
                "type": "note",
                "title": "Tennis Court Alert" if is_alert else "Court Available",
                "body": message,
            }
            response = requests.post(url, json=data, headers=headers, timeout=5)
            if response.status_code == 200:
                logger.debug("Pushbullet notification sent successfully")
            else:
                logger.warning("Pushbullet notification failed with status %d", response.status_code)
        except Exception:
            logger.exception("Failed to send Pushbullet notification")

