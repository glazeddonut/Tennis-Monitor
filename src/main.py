"""Main entry point for Tennis Monitor."""

import sys
import os
import logging
import time
from datetime import datetime, timezone
from tennis_monitor import TennisMonitor
from tennis_monitor.config import get_config


class LocalTimeFormatter(logging.Formatter):
    """Custom formatter that converts UTC timestamps to local time."""
    
    converter = time.localtime
    
    def formatTime(self, record, datefmt=None):
        """Convert record timestamp to local time."""
        ct = self.converter(record.created)
        if datefmt:
            s = time.strftime(datefmt, ct)
        else:
            t = time.strftime(self.default_time_format, ct)
            s = self.default_msec_format % (t, record.msecs)
        return s


# Read LOG_LEVEL from environment (defaults to INFO for standard runs)
log_level = os.getenv("LOG_LEVEL", "INFO").upper()
try:
    level = getattr(logging, log_level)
except AttributeError:
    level = logging.INFO

# Ensure logs directory exists
log_dir = os.path.join(os.path.dirname(__file__), "..", "logs")
os.makedirs(log_dir, exist_ok=True)

# Configure logging: both console and file
log_file = os.path.join(log_dir, "tennis_monitor.log")
log_format = "%(asctime)s %(levelname)s [%(name)s] %(message)s"

# Create formatters and handlers with local time
formatter = LocalTimeFormatter(log_format)

# Console handler (stdout)
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(level)
console_handler.setFormatter(formatter)

# File handler (persistent log file)
file_handler = logging.FileHandler(log_file, mode="a")
file_handler.setLevel(level)
file_handler.setFormatter(formatter)

# Configure root logger
root_logger = logging.getLogger()
root_logger.setLevel(level)
root_logger.addHandler(console_handler)
root_logger.addHandler(file_handler)

logger = logging.getLogger(__name__)
logger.info(f"Logging initialized. Log file: {log_file}")


def main() -> int:
    """Run the tennis monitor.
    
    Returns:
        Exit code
    """
    try:
        config = get_config()

        # Validate configuration
        if not config.booking_system.url:
            logger.error("BOOKING_SYSTEM_URL not configured")
            return 1

        monitor = TennisMonitor(config)
        logger.info("Starting Tennis Court Monitor...")
        logger.info("Check interval: %s seconds", config.monitoring.check_interval_seconds)
        logger.info("Auto-booking enabled: %s", config.monitoring.auto_book_enabled)
        logger.info("Preferred courts: %s", ", ".join(config.user_preferences.preferred_courts))
        logger.info("Preferred times: %s", ", ".join(config.user_preferences.preferred_time_slots))
        logger.info("Press Ctrl+C to stop the monitor.")

        monitor.run()
        return 0
    except Exception as e:
        logger.exception("Unhandled error running Tennis Monitor")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
