# Tennis Court Booking Monitor

A Python-based system for monitoring tennis court booking systems to automatically book available courts as they become available on the same day.

> **📢 Latest Update (Dec 6, 2025)**: Fixed critical bug where monitor was hanging after scraping availability. Now uses persistent browser session for reliable continuous monitoring. See [MONITOR_FIX_COMPLETE.md](MONITOR_FIX_COMPLETE.md) for details.

## Features

- **Real-time Monitoring**: Continuously monitor tennis court availability
- **Automated Booking**: Automatically book courts when they become available
- **Same-day Alerts**: Get notified immediately when preferred courts are available
- **Duplicate Prevention**: Smart notification deduplication with daily reset
- **Health Checks**: Daily "I'm alive" notifications to verify the monitor is running
- **Configurable Preferences**: Set preferred courts and time slots
- **Multiple Notification Methods**: Email and push notifications (ntfy.sh, Pushbullet)
- **Web Scraping**: Playwright-based scraper for various booking systems

## Project Structure

```
tennis-monitor/
├── src/
│   ├── tennis_monitor/
│   │   ├── __init__.py
│   │   ├── config.py          # Configuration management
│   │   ├── booking.py         # Booking system interactions
│   │   ├── monitor.py         # Monitoring logic
│   │   ├── notifications.py   # Alert notifications
│   │   └── utils.py           # Utility functions
│   └── main.py                # Entry point
├── tests/
│   ├── __init__.py
│   ├── test_config.py
│   ├── test_booking.py
│   └── test_monitor.py
├── .github/
│   └── copilot-instructions.md
├── .vscode/
│   └── tasks.json            # VS Code tasks
├── .env.example              # Example environment variables
├── pyproject.toml            # Project metadata and dependencies
├── requirements.txt          # Production dependencies
├── requirements-dev.txt      # Development dependencies
└── README.md
```

## Setup

1. **Clone or navigate to the project directory**

2. **Create a virtual environment**:
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**:
   ```bash
   cp .env.example .env
   # Edit .env with your booking system credentials and preferences
   ```

## Development

Install development dependencies:
```bash
pip install -r requirements-dev.txt
```

### Running Tests
```bash
pytest
```

### Code Quality
```bash
# Format code
black src/ tests/

# Lint
flake8 src/ tests/

# Type checking
mypy src/
```

## Usage

### Running the Monitor

```bash
# Using Python module
python -m main

# Or directly
python src/main.py
```

The monitor will:
1. Log in to your booking system
2. Check for available courts matching your preferences
3. Send notifications for new available slots
4. Prevent duplicate notifications (resets daily)
5. Send a daily health check notification at your configured time
6. Continue checking indefinitely until stopped (Ctrl+C)

### Push Notifications

#### ntfy.sh (Recommended - Free)

1. Install the ntfy app on iPhone: [ntfy on App Store](https://apps.apple.com/us/app/ntfy/id1665873820)
2. Choose a unique topic name in your `.env`:
   ```
   PUSH_SERVICE=ntfy
   NTFY_TOPIC=mytennismonitor42
   ENABLE_PUSH_NOTIFICATIONS=true
   ```
3. Open the ntfy app and subscribe to your topic
4. Run the monitor - notifications will arrive on your iPhone

#### Pushbullet (Alternative)

1. Sign up at [Pushbullet.com](https://www.pushbullet.com)
2. Get your API key from Account Settings
3. Install the Pushbullet app on iPhone
4. Configure in `.env`:
   ```
   PUSH_SERVICE=pushbullet
   PUSHBULLET_API_KEY=your_api_key_here
   ENABLE_PUSH_NOTIFICATIONS=true
   ```

## Configuration

Edit `.env` file to configure:

### Required Settings
- `BOOKING_SYSTEM_URL` - URL to your booking system
- `BOOKING_USERNAME` - Username for login
- `BOOKING_PASSWORD` - Password for login
- `PREFERRED_COURTS` - Comma-separated court names (e.g., `Court11,Court12`)
- `PREFERRED_TIME_SLOTS` - Comma-separated preferred times (e.g., `18:00,19:00,20:00`)

### Notification Settings
- `ENABLE_PUSH_NOTIFICATIONS` - Enable push notifications (true/false)
- `PUSH_SERVICE` - Service to use: `ntfy` (recommended) or `pushbullet`
- `NTFY_TOPIC` - Your unique ntfy topic (for ntfy.sh service)
- `PUSHBULLET_API_KEY` - Your Pushbullet API key (if using Pushbullet)

### Monitoring Settings
- `CHECK_INTERVAL_SECONDS` - How often to check for availability (default: 300)
- `AUTO_BOOK_ENABLED` - Automatically book courts (true/false, default: false)
- `ALIVE_CHECK_ENABLED` - Send daily health check notification (default: true)
- `ALIVE_CHECK_HOUR` - Hour of day for health check (0-23, default: 10 for 10:00 AM)

See `.env.example` for all available options.

## Contributing

Contributions are welcome! Please ensure all tests pass and code is properly formatted before submitting.

## License

MIT License
