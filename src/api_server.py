"""API server for Tennis Monitor with monitoring in background."""

import sys
import os
import logging
import threading
from tennis_monitor import TennisMonitor
from tennis_monitor.config import get_config
from tennis_monitor.api import create_api
import uvicorn


# Configure logging before anything else
log_level = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(level=log_level)
logger = logging.getLogger(__name__)


def run_monitor_in_background(monitor: TennisMonitor):
    """Run monitor in a background thread."""
    try:
        monitor.run()
    except Exception:
        logger.exception("Error in background monitor thread")


def main():
    """Start API server with background monitor."""
    # Load configuration
    config = get_config()
    
    # Create monitor
    monitor = TennisMonitor(config)
    
    # Create FastAPI app
    app = create_api(monitor, config)
    
    # Start monitor in background thread
    logger.info("Starting monitor in background thread...")
    monitor.is_running = True
    monitor_thread = threading.Thread(
        target=run_monitor_in_background,
        args=(monitor,),
        daemon=True
    )
    monitor_thread.start()
    
    # Get API settings from environment
    api_host = os.getenv("API_HOST", "0.0.0.0")
    api_port = int(os.getenv("API_PORT", "8000"))
    api_reload = os.getenv("API_RELOAD", "false").lower() == "true"
    
    logger.info("Starting API server on %s:%d", api_host, api_port)
    logger.info("Visit http://localhost:%d/dashboard to access the web interface", api_port)
    
    # Start API server
    uvicorn.run(
        app,
        host=api_host,
        port=api_port,
        reload=api_reload,
        log_level="info"
    )


if __name__ == "__main__":
    sys.exit(main())
