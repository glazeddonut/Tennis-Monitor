"""REST API for Tennis Monitor."""

import logging
import os
from datetime import datetime
from typing import Optional, Dict, Any
from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.responses import JSONResponse, HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from .monitor import TennisMonitor
from .config import AppConfig, update_env_file


logger = logging.getLogger(__name__)


# Pydantic models for API
class ConfigResponse(BaseModel):
    """Current configuration."""
    booking_system_url: str
    preferred_courts: list[str]
    preferred_time_slots: list[str]
    check_interval_seconds: int
    auto_book_enabled: bool
    alive_check_enabled: bool
    alive_check_hour: int


class StatusResponse(BaseModel):
    """Monitor status."""
    is_running: bool
    checks_performed_today: int
    slots_found_today: int
    last_check_time: str
    last_update: str
    available_slots: list[Dict[str, Any]] = []


class PreferencesUpdate(BaseModel):
    """Update user preferences."""
    preferred_courts: Optional[list[str]] = None
    preferred_time_slots: Optional[list[str]] = None
    check_interval_seconds: Optional[int] = None
    alive_check_hour: Optional[int] = None


class BookingRequest(BaseModel):
    """Request to book a court."""
    court_name: str
    time_slot: str


class BookingResponse(BaseModel):
    """Booking result."""
    success: bool
    message: str


class APIKey:
    """API Key authentication."""
    
    def __init__(self):
        self.valid_key = os.getenv("API_KEY", "tennis-monitor-default-key")
    
    def __call__(self, x_token: str = Header(...)) -> str:
        if x_token != self.valid_key:
            raise HTTPException(status_code=403, detail="Invalid API key")
        return x_token


def create_api(monitor: TennisMonitor, config: AppConfig) -> FastAPI:
    """Create and configure FastAPI application.
    
    Args:
        monitor: TennisMonitor instance
        config: Application configuration
    
    Returns:
        Configured FastAPI app
    """
    app = FastAPI(
        title="Tennis Monitor API",
        description="REST API for Tennis Court Monitoring",
        version="1.0.0"
    )
    
    # Mount PWA static files
    web_dir = os.path.join(os.path.dirname(__file__), "web")
    if os.path.exists(web_dir):
        app.mount("/pwa", StaticFiles(directory=web_dir, html=True), name="pwa")
    
    api_key = APIKey()
    
    @app.get("/", tags=["Health"])
    async def root():
        """Health check endpoint."""
        return {
            "status": "ok",
            "service": "Tennis Monitor API",
            "version": "1.0.0"
        }
    
    @app.get("/health", tags=["Health"])
    async def health():
        """Health check with detailed status."""
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "monitor_running": monitor.is_running
        }
    
    @app.get("/api/status", tags=["Monitor"], response_model=StatusResponse)
    async def get_status(token: str = Depends(api_key)):
        """Get current monitor status.
        
        Returns:
            Current status including checks performed and slots found today
        """
        return StatusResponse(
            is_running=monitor.is_running,
            checks_performed_today=monitor.checks_performed_today,
            slots_found_today=monitor.slots_found_today,
            last_check_time=datetime.now().isoformat(),
            last_update=datetime.now().isoformat(),
            available_slots=monitor.last_found_slots
        )
    
    @app.get("/api/config", tags=["Configuration"], response_model=ConfigResponse)
    async def get_config(token: str = Depends(api_key)):
        """Get current configuration.
        
        Returns:
            Current monitor configuration
        """
        return ConfigResponse(
            booking_system_url=config.booking_system.url,
            preferred_courts=config.user_preferences.preferred_courts,
            preferred_time_slots=config.user_preferences.preferred_time_slots,
            check_interval_seconds=config.monitoring.check_interval_seconds,
            auto_book_enabled=config.monitoring.auto_book_enabled,
            alive_check_enabled=config.monitoring.alive_check_enabled,
            alive_check_hour=config.monitoring.alive_check_hour
        )
    
    @app.post("/api/config/preferences", tags=["Configuration"])
    async def update_preferences(
        preferences: PreferencesUpdate,
        token: str = Depends(api_key)
    ):
        """Update user preferences.
        
        Args:
            preferences: New preferences to apply
        
        Returns:
            Updated configuration
        """
        # Build updates dictionary for .env file
        updates = {}
        
        if preferences.preferred_courts:
            config.user_preferences.preferred_courts = preferences.preferred_courts
            updates["PREFERRED_COURTS"] = ",".join(preferences.preferred_courts)
        
        if preferences.preferred_time_slots:
            config.user_preferences.preferred_time_slots = preferences.preferred_time_slots
            updates["PREFERRED_TIME_SLOTS"] = ",".join(preferences.preferred_time_slots)
        
        if preferences.check_interval_seconds:
            config.monitoring.check_interval_seconds = preferences.check_interval_seconds
            updates["CHECK_INTERVAL_SECONDS"] = str(preferences.check_interval_seconds)
        
        if preferences.alive_check_hour is not None:
            config.monitoring.alive_check_hour = preferences.alive_check_hour
            updates["ALIVE_CHECK_HOUR"] = str(preferences.alive_check_hour)
        
        # Write to .env file
        if updates:
            success = update_env_file(updates)
            if not success:
                logger.warning("Failed to update .env file, but config updated in memory")
        
        logger.info("Configuration updated via API")
        
        return {
            "status": "updated",
            "config": ConfigResponse(
                booking_system_url=config.booking_system.url,
                preferred_courts=config.user_preferences.preferred_courts,
                preferred_time_slots=config.user_preferences.preferred_time_slots,
                check_interval_seconds=config.monitoring.check_interval_seconds,
                auto_book_enabled=config.monitoring.auto_book_enabled,
                alive_check_enabled=config.monitoring.alive_check_enabled,
                alive_check_hour=config.monitoring.alive_check_hour
            )
        }
    
    @app.post("/api/monitor/start", tags=["Monitor Control"])
    async def start_monitor(token: str = Depends(api_key)):
        """Start the monitor."""
        if monitor.is_running:
            return {"status": "already_running"}
        
        monitor.is_running = True
        logger.info("Monitor started via API")
        return {"status": "started"}
    
    @app.post("/api/monitor/stop", tags=["Monitor Control"])
    async def stop_monitor(token: str = Depends(api_key)):
        """Stop the monitor."""
        if not monitor.is_running:
            return {"status": "already_stopped"}
        
        monitor.is_running = False
        logger.info("Monitor stopped via API")
        return {"status": "stopped"}
    
    @app.post("/api/monitor/book", tags=["Booking"], response_model=BookingResponse)
    async def book_court(request: BookingRequest, token: str = Depends(api_key)):
        """Queue a booking request to be processed by the monitor thread.
        
        The booking is queued and will be processed during the next monitor cycle.
        This ensures thread safety by letting the monitor thread (which owns the
        Playwright browser) execute the actual booking.
        
        Args:
            request: Booking request with court_name and time_slot
            
        Returns:
            Response indicating the booking was queued
        """
        try:
            logger.info("Queueing booking request: %s at %s", request.court_name, request.time_slot)
            
            # Queue the booking for processing by the monitor thread
            monitor.pending_bookings.append({
                "court_name": request.court_name,
                "time_slot": request.time_slot
            })
            
            message = f"Booking queued for {request.court_name} at {request.time_slot} - will be processed next check"
            logger.info(message)
            return BookingResponse(success=True, message=message)
        except Exception as e:
            message = f"Error queueing booking: {str(e)}"
            logger.exception(message)
            return BookingResponse(success=False, message=message)
    
    @app.get("/api/monitor/logs", tags=["Logs"])
    async def get_logs(
        lines: int = 50,
        token: str = Depends(api_key)
    ):
        """Get recent log entries.
        
        Args:
            lines: Number of recent log lines to return
        
        Returns:
            List of recent log entries
        """
        log_file = "logs/tennis_monitor.log"
        
        if not os.path.exists(log_file):
            return {"logs": [], "error": "Log file not found"}
        
        try:
            with open(log_file, "r") as f:
                all_lines = f.readlines()
                recent_lines = all_lines[-lines:] if len(all_lines) > lines else all_lines
                return {
                    "logs": recent_lines,
                    "total_lines": len(all_lines),
                    "returned_lines": len(recent_lines)
                }
        except Exception as e:
            logger.exception("Error reading log file")
            return {"logs": [], "error": str(e)}
    
    # Dashboard HTML
    dashboard_html = _get_dashboard_html()
    
    @app.get("/dashboard", response_class=HTMLResponse, tags=["Web UI"])
    async def get_dashboard():
        """Serve web dashboard."""
        return dashboard_html
    
    @app.get("/", response_class=HTMLResponse, tags=["Web UI"])
    async def root():
        """Redirect to PWA."""
        return """
        <html>
            <head>
                <meta http-equiv="refresh" content="0; url=/pwa" />
            </head>
            <body>
                Redirecting to Tennis Monitor PWA...
            </body>
        </html>
        """
    
    return app


def _get_dashboard_html() -> str:
    """Get dashboard HTML content."""
    return """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Tennis Monitor</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        .container { max-width: 1000px; margin: 0 auto; }
        .header { color: white; text-align: center; margin-bottom: 40px; }
        .header h1 { font-size: 2.5em; margin-bottom: 10px; }
        .cards {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 20px;
        }
        .card {
            background: white;
            border-radius: 12px;
            padding: 20px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        }
        .card h2 {
            color: #667eea;
            font-size: 0.9em;
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-bottom: 15px;
        }
        .card .value {
            font-size: 2.5em;
            font-weight: bold;
            color: #333;
            margin-bottom: 10px;
        }
        .status-badge {
            display: inline-block;
            padding: 8px 16px;
            border-radius: 20px;
            font-size: 0.9em;
            font-weight: bold;
            margin-bottom: 10px;
        }
        .status-running { background: #4caf50; color: white; }
        .status-stopped { background: #f44336; color: white; }
        .preferences {
            background: white;
            border-radius: 12px;
            padding: 25px;
            margin-bottom: 20px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        }
        .preferences h2 {
            color: #333;
            margin-bottom: 20px;
            border-bottom: 2px solid #667eea;
            padding-bottom: 10px;
        }
        .pref-group { margin-bottom: 20px; }
        .pref-group label {
            display: block;
            color: #333;
            font-weight: bold;
            margin-bottom: 8px;
        }
        .pref-group input, .pref-group textarea {
            width: 100%;
            padding: 10px;
            border: 1px solid #ddd;
            border-radius: 6px;
            font-size: 1em;
            font-family: inherit;
        }
        .button-group { display: flex; gap: 10px; margin-top: 20px; }
        button {
            flex: 1;
            padding: 12px 20px;
            border: none;
            border-radius: 6px;
            font-size: 1em;
            font-weight: bold;
            cursor: pointer;
        }
        .btn-primary { background: #667eea; color: white; }
        .btn-primary:hover { background: #5568d3; }
        .btn-success { background: #4caf50; color: white; }
        .btn-danger { background: #f44336; color: white; }
        .message {
            padding: 15px;
            border-radius: 6px;
            margin-bottom: 15px;
            display: none;
        }
        .message.success {
            background: #d4edda;
            color: #155724;
            border: 1px solid #c3e6cb;
            display: block;
        }
        .logs {
            background: white;
            border-radius: 12px;
            padding: 25px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        }
        .log-content {
            background: #1e1e1e;
            color: #0f0;
            padding: 15px;
            border-radius: 6px;
            font-family: 'Courier New', monospace;
            font-size: 0.85em;
            overflow-y: auto;
            max-height: 400px;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎾 Tennis Monitor</h1>
            <p>Real-time Tennis Court Availability Monitoring</p>
        </div>
        
        <div class="cards">
            <div class="card">
                <h2>Status</h2>
                <div id="status-badge" class="status-badge status-stopped">Loading...</div>
            </div>
            <div class="card">
                <h2>Checks Today</h2>
                <div class="value" id="checks-count">0</div>
            </div>
            <div class="card">
                <h2>Slots Found</h2>
                <div class="value" id="slots-count">0</div>
            </div>
        </div>
        
        <div class="preferences">
            <h2>Configuration</h2>
            <div id="message" class="message"></div>
            <div class="pref-group">
                <label>API Key:</label>
                <div style="display: flex; gap: 10px;">
                    <input type="password" id="api-key" placeholder="Enter API Key" style="flex: 1;">
                    <button class="btn-primary" onclick="clearApiKey(); document.getElementById('api-key').value=''; showMessage('API Key cleared', 'success');" style="width: auto; flex: 0;">Clear</button>
                </div>
                <small style="color: #999; display: block; margin-top: 5px;">Saved in browser - won't be sent to server</small>
            </div>
            <div class="pref-group">
                <label for="courts">Preferred Courts</label>
                <input type="text" id="courts" placeholder="Court11, Court12">
            </div>
            <div class="pref-group">
                <label for="times">Preferred Times</label>
                <input type="text" id="times" placeholder="18:00, 19:00, 20:00">
            </div>
            <div class="button-group">
                <button class="btn-primary" onclick="updatePreferences()">Save</button>
                <button class="btn-success" onclick="startMonitor()">Start</button>
                <button class="btn-danger" onclick="stopMonitor()">Stop</button>
            </div>
        </div>
        
        <div class="logs">
            <h2>Recent Logs</h2>
            <button class="btn-primary" onclick="refreshLogs()" style="margin-bottom: 15px; width: auto;">Refresh</button>
            <div class="log-content" id="logs">Loading logs...</div>
        </div>
    </div>
    
    <script>
        // API Key storage management
        const API_KEY_STORAGE = "tennis-monitor-api-key";
        
        function saveApiKey(key) {
            localStorage.setItem(API_KEY_STORAGE, key);
        }
        
        function loadApiKey() {
            return localStorage.getItem(API_KEY_STORAGE) || "";
        }
        
        function clearApiKey() {
            localStorage.removeItem(API_KEY_STORAGE);
        }
        
        function showMessage(msg, type = "success") {
            const msgDiv = document.getElementById("message");
            msgDiv.textContent = msg;
            msgDiv.className = "message " + type;
            setTimeout(() => msgDiv.className = "message", 5000);
        }
        
        async function apiCall(endpoint, method = "GET", data = null) {
            const apiKey = document.getElementById("api-key").value;
            if (!apiKey) {
                showMessage("Please enter API Key", "error");
                return null;
            }
            
            try {
                const options = {
                    method,
                    headers: { "X-Token": apiKey, "Content-Type": "application/json" }
                };
                if (data) options.body = JSON.stringify(data);
                
                const response = await fetch(endpoint, options);
                if (!response.ok) throw new Error(`HTTP ${response.status}`);
                return await response.json();
            } catch (error) {
                showMessage("Error: " + error.message, "error");
                return null;
            }
        }
        
        // Save API key when it changes
        document.getElementById("api-key").addEventListener("change", function() {
            if (this.value) {
                saveApiKey(this.value);
                showMessage("API Key saved to browser", "success");
            }
        });
        
        // Load saved API key on page load
        window.addEventListener("load", function() {
            const savedKey = loadApiKey();
            if (savedKey) {
                document.getElementById("api-key").value = savedKey;
            }
        });
        
        async function loadStatus() {
            const data = await apiCall("/api/status");
            if (data) {
                document.getElementById("status-badge").textContent = data.is_running ? "🟢 RUNNING" : "🔴 STOPPED";
                document.getElementById("checks-count").textContent = data.checks_performed_today;
                document.getElementById("slots-count").textContent = data.slots_found_today;
            }
        }
        
        async function loadConfig() {
            const data = await apiCall("/api/config");
            if (data) {
                document.getElementById("courts").value = data.preferred_courts.join(", ");
                document.getElementById("times").value = data.preferred_time_slots.join(", ");
            }
        }
        
        async function updatePreferences() {
            const data = {
                preferred_courts: document.getElementById("courts").value.split(",").map(s => s.trim()),
                preferred_time_slots: document.getElementById("times").value.split(",").map(s => s.trim())
            };
            const result = await apiCall("/api/config/preferences", "POST", data);
            if (result) showMessage("Settings saved!", "success");
        }
        
        async function startMonitor() {
            const result = await apiCall("/api/monitor/start", "POST");
            if (result) { showMessage("Started!", "success"); setTimeout(loadStatus, 1000); }
        }
        
        async function stopMonitor() {
            const result = await apiCall("/api/monitor/stop", "POST");
            if (result) { showMessage("Stopped!", "success"); setTimeout(loadStatus, 1000); }
        }
        
        async function refreshLogs() {
            const data = await apiCall("/api/monitor/logs?lines=50");
            if (data) document.getElementById("logs").textContent = data.logs.join("");
        }
        
        loadStatus();
        loadConfig();
        refreshLogs();
        setInterval(loadStatus, 10000);
    </script>
</body>
</html>"""
