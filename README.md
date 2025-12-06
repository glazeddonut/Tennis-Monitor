# Tennis Court Booking Monitor

A Python-based system for monitoring tennis court booking systems to automatically book available courts as they become available on the same day.

> **📢 Latest Update (Dec 6, 2025)**: Fixed critical bug where monitor was hanging after scraping availability. Now uses persistent browser session for reliable continuous monitoring. See [MONITOR_FIX_COMPLETE.md](MONITOR_FIX_COMPLETE.md) for details.

## Features

- **Real-time Monitoring**: Continuously monitor tennis court availability
- **Automated Booking**: Automatically book courts when they become available
- **Same-day Alerts**: Get notified immediately when preferred courts are available
- **Configurable Preferences**: Set preferred courts and time slots
- **Multiple Notification Methods**: Email and push notifications
- **Web Scraping/API Integration**: Support for various booking systems

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

```bash
python -m tennis_monitor
```

The monitor will start checking for available courts based on your configured preferences and notify you when courts become available.

## Configuration

Edit `.env` file to configure:
- Booking system URL and credentials
- Preferred courts and time slots
- Notification preferences (email, push notifications)
- Monitoring check interval
- Auto-booking settings

## Contributing

Contributions are welcome! Please ensure all tests pass and code is properly formatted before submitting.

## License

MIT License
