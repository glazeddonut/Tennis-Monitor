# Tennis Court Booking Monitor

A Python-based system for monitoring tennis court booking systems with automated booking and a modern PWA interface for instant booking.

> **📢 Latest Update (Dec 12, 2025)**: Added instant quick booking feature with REST API and PWA web interface! Book courts one-click from your phone with real-time availability updates.

## Features

### Core Monitoring
- **Real-time Monitoring**: Continuously monitor tennis court availability (every 30 seconds)
- **Automated Booking**: Automatically book courts when they become available
- **Same-day Alerts**: Get notified immediately when preferred courts are available
- **Duplicate Prevention**: Smart notification deduplication with daily reset
- **Health Checks**: Daily "I'm alive" notifications to verify the monitor is running
- **Persistent Sessions**: Browser session survives network interruptions

### Quick Booking (NEW! 🎾)
- **One-Click Booking**: Click "Book" button in PWA to instantly book a court
- **Instant Execution**: Books within seconds, not waiting for next monitor cycle
- **5-Step Halbooking Flow**: Full automated booking including co-player selection
- **Real-time Feedback**: Button shows "⏳ Booking..." → "✅ Booked!"

### API & Web Interface (NEW!)
- **REST API**: Full-featured API to control monitor from external apps
- **Progressive Web App (PWA)**: Modern responsive web interface
- **Real-time Status**: View available courts, check preferences, see logs
- **Mobile-Friendly**: Works great on iPhone, iPad, Android

### Notifications
- **Push Notifications**: ntfy.sh, Pushbullet, email alerts
- **Booking Confirmation**: Get notified when a court is successfully booked
- **Error Alerts**: Know immediately if something goes wrong

### Configuration
- **Flexible Preferences**: Set preferred courts and time slots
- **Dynamic Court Mapping**: Map internal court IDs to display names
- **Multiple Notification Methods**: Email, push (ntfy.sh, Pushbullet)

## Quick Start

### Local Development

1. **Clone and setup**:
   ```bash
   git clone <repo>
   cd Tennis-Monitor
   python3 -m venv venv
   source venv/bin/activate
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure**:
   ```bash
   cp .env.example .env
   # Edit .env with your credentials
   ```

4. **Run API + Monitor**:
   ```bash
   python -m api_server
   ```
   
   Then visit: **http://localhost:8000/pwa**

### Docker

```bash
docker-compose up
```

Access the PWA at: **http://192.168.86.248:8000/pwa** (adjust IP for your network)

## API Endpoints

All endpoints require `?token=YOUR_API_KEY` (set `API_KEY` in .env)

### Status & Control
- `GET /api/status` - Get monitor status and available slots
- `GET /api/config` - Get current configuration
- `POST /api/monitor/start` - Start monitoring
- `POST /api/monitor/stop` - Stop monitoring

### Booking
- `POST /api/monitor/book` - Queue instant booking
  ```json
  {
    "court_name": "Court11",
    "time_slot": "20:00-21:00"
  }
  ```

### Preferences
- `POST /api/config/preferences` - Update preferences
- `GET /api/monitor/logs` - Get recent logs

### Web Interface
- `GET /pwa/` - Progressive Web App (dashboard)

## Configuration

### Required Settings (.env)
```bash
# Booking System
BOOKING_SYSTEM_URL=https://example.halbooking.dk
BOOKING_USERNAME=your_username
BOOKING_PASSWORD=your_password

# Court Preferences
PREFERRED_COURTS=Court11,Court12
PREFERRED_TIME_SLOTS=18:00,19:00,20:00

# Quick Booking
BOOKING_CO_PLAYER=Aksel Mahler Tolborg  # Name of co-player for bookings

# Court Mapping (internal ID to display name)
PW_COURT_MAP=9:Court11,10:Court12,14:Court4,20:Court5
```

### Notifications
```bash
# Push Notifications (ntfy.sh recommended)
ENABLE_PUSH_NOTIFICATIONS=true
PUSH_SERVICE=ntfy
NTFY_TOPIC=my_unique_topic_name

# Daily Health Check
ALIVE_CHECK_ENABLED=true
ALIVE_CHECK_HOUR=10  # 10 AM

# API Access
API_KEY=your_secret_api_key
```

### Monitoring
```bash
CHECK_INTERVAL_SECONDS=30        # Check availability every 30 sec
AUTO_BOOK_ENABLED=false          # Manual booking only
LOG_LEVEL=INFO                   # DEBUG for verbose logs
BOOKING_HEADLESS=true            # false to see browser window
```

See `.env.example` for all options.

## Development

### Project Structure
```
src/
├── main.py                    # CLI entry point (monitor only)
├── api_server.py              # API + Monitor (recommended)
└── tennis_monitor/
    ├── __init__.py
    ├── config.py              # Configuration & environment vars
    ├── monitor.py             # Monitor core logic
    ├── scraper.py             # Playwright-based scraper
    ├── booking.py             # Booking client wrapper
    ├── notifications.py       # Notification managers
    ├── api.py                 # FastAPI REST endpoints
    ├── utils.py               # Utility functions
    └── web/                   # PWA files
        ├── app.js             # PWA app logic
        ├── index.html         # PWA interface
        ├── manifest.json      # PWA manifest
        └── service-worker.js  # Offline support
```

### Running Locally

**Monitor + API + PWA**:
```bash
python -m api_server
```

**Monitor only** (no API/PWA):
```bash
python -m main
```

### Development Setup

```bash
# Install dev dependencies
pip install -r requirements-dev.txt

# Run tests
pytest -v

# Format code
black src/ tests/

# Lint
flake8 src/ tests/

# Type check
mypy src/
```

## Architecture

### Monitor Thread
- Runs continuously in background
- Checks availability every 30 seconds
- Processes queued bookings immediately when signaled via `threading.Event`
- Owns the persistent Playwright browser session (thread-safe)

### API Thread
- FastAPI server on port 8000
- Handles HTTP requests from PWA and external clients
- Queues booking requests and signals monitor to process them
- Thread-safe communication via queue + event

### PWA Interface
- Modern responsive web app (works on mobile!)
- 4 tabs: Status, Preferences, Logs, Settings
- Shows up to 3 available slots with one-click booking buttons
- Real-time status updates (auto-refresh every 5 seconds)
- Progressive Web App - works offline!

## Booking Flow (5 Steps)

When you click "Book" in the PWA:

1. **API receives request** → returns immediately "⏳ Booking..."
2. **Monitor wakes up** → signals event to stop sleeping
3. **STEP 1**: Find and click matching slot on booking page
4. **STEP 2**: Select co-player from list (Aksel Mahler Tolborg)
5. **STEP 3**: Add to cart ("Læg i kurv")
6. **STEP 4**: Accept terms checkbox
7. **STEP 5**: Confirm booking ("Bekræft booking")
8. **STEP 6**: Verify receipt → sends "✅ Booked!" notification

Total time: Usually 2-5 seconds from click to confirmation!

## Notifications

### ntfy.sh (Recommended - Free)

1. Install [ntfy app](https://apps.apple.com/us/app/ntfy/id1665873820) on iPhone
2. Configure .env:
   ```bash
   ENABLE_PUSH_NOTIFICATIONS=true
   PUSH_SERVICE=ntfy
   NTFY_TOPIC=my_unique_topic_name
   ```
3. Open ntfy app → subscribe to your topic
4. You'll get real-time notifications for:
   - Court availability
   - Booking confirmations
   - Errors & alerts
   - Daily health checks

### Other Services
- **Pushbullet**: Alternative push service
- **Email**: For server alerts (optional)

## Troubleshooting

### "Booking receipt not found"
Check that the booking system page structure matches. Update `PW_COURT_MAP` with your court IDs.

### Notifications not arriving
- Verify NTFY_TOPIC matches exactly in .env and ntfy app
- Check internet connection
- Ensure ENABLE_PUSH_NOTIFICATIONS=true

### Monitor not starting bookings
- Check BOOKING_CO_PLAYER is set correctly
- Verify PREFERRED_COURTS and PREFERRED_TIME_SLOTS in .env
- Check logs: `tail -f logs/tennis_monitor.log`

## Contributing

Contributions welcome! Please ensure tests pass:
```bash
pytest
black src/ tests/
flake8 src/ tests/
mypy src/
```

## License

MIT
