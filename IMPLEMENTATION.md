# Push Notifications & Structure Validation - Implementation Summary

## Overview
Implemented push notifications (ntfy.sh and Pushbullet) and automatic structure validation that detects unknown courts and alerts before stopping.

## Changes Made

### 1. Push Notification Support (`src/tennis_monitor/notifications.py`)

**Added Methods:**
- `notify_alert(title, message)` - Send critical alerts (e.g., structure changes)
- `_send_ntfy(message, is_alert)` - Send push via ntfy.sh
- `_send_pushbullet(message, is_alert)` - Send push via Pushbullet
- `_send_push_notification(message, court, is_alert)` - Router to correct service

**Features:**
- Support for two push services: ntfy.sh (free) and Pushbullet
- Service selection via `PUSH_SERVICE` environment variable
- Alert priority differentiation (high for critical alerts, default for availability)
- Requests library for HTTP POST to push services

**Environment Variables:**
```bash
PUSH_SERVICE=ntfy                    # "ntfy" or "pushbullet"
NTFY_TOPIC=your_topic_name           # for ntfy.sh
PUSHBULLET_API_KEY=your_api_key      # for Pushbullet
ENABLE_PUSH_NOTIFICATIONS=true       # enable/disable push
```

### 2. Structure Validation (`src/tennis_monitor/scraper.py`)

**Added Validation Logic in `get_available_courts()`:**
- Track unknown court IDs during slot parsing
- Validate that all found `court_num` values exist in `court_map` (if configured)
- Raise `ValueError` with detailed error message listing unknown courts
- Error includes current court map for debugging

**Example Error:**
```
Unknown court IDs detected: 25, 26. Current court map: {'9': 'Court11', '10': 'Court12', '14': 'Court4', '20': 'Court5'}. Please update PW_COURT_MAP environment variable.
```

### 3. Error Handling (`src/tennis_monitor/booking.py`)

**New Exception Class:**
```python
class StructureValidationError(Exception):
    """Raised when booking system structure validation fails"""
```

**Enhanced `get_available_courts()`:**
- Catches `ValueError` from scraper (structure validation failures)
- Converts to `StructureValidationError` for consistent error handling
- Logs detailed error information
- Allows parent (monitor) to handle gracefully

### 4. Monitor Alert Flow (`src/tennis_monitor/monitor.py`)

**Enhanced Both `run()` and `run_async()` Methods:**
- Wrap `check_availability()` in try-except
- Catch `StructureValidationError`
- Call `notify_alert()` with error details
- Stop gracefully with `sys.exit(1)`
- Added logging throughout error path

**Alert Message Format:**
```
Title: "Booking System Structure Changed"
Body: [Full error message from scraper]
```

### 5. Configuration (`src/tennis_monitor/config.py`)

**No changes needed** - Already supports:
- `enable_push_notifications` boolean flag
- `enable_email_alerts` boolean flag
- Flexible environment variable loading via pydantic

### 6. Documentation

**New Files:**
- `PUSH_NOTIFICATIONS.md` - Complete user guide with setup instructions
- Updated `test_notifications.py` - Enhanced test script for push verification
- Updated `.env.example` - Added push notification configuration

**Key Guides:**
- Step-by-step ntfy.sh setup (recommended, free)
- Step-by-step Pushbullet setup (alternative)
- Troubleshooting section
- How structure validation works

## Alert Types

### 1. Availability Alerts
```
Triggered when: Court matching preferences becomes available
Format: "Court Court11 - 18:00-19:00: Available"
Service: Configured push service with default priority
```

### 2. Structure Change Alert
```
Triggered when: New unknown courts detected in booking system
Format: "Booking System Structure Changed: Unknown court IDs detected: 25, 26..."
Service: Configured push service with high priority
Behavior: Monitor stops, sends alert, exits with code 1
```

### 3. Booked Alert (Future)
```
Format: "Court Court11 - 18:00-19:00: Booked"
Note: Auto-booking currently disabled, will be implemented later
```

## Validation Flow

```
1. Monitor.run() calls check_availability()
   ↓
2. BookingSystemClient.get_available_courts()
   ↓
3. PlaywrightBookingClient.get_available_courts()
   - Fetches all slots from Halbooking
   - Tracks unknown_courts = set()
   - For each slot: if court_num not in court_map → add to unknown_courts
   - If unknown_courts not empty → raise ValueError
   ↓
4. Caught in BookingSystemClient: ValueError → StructureValidationError
   ↓
5. Caught in TennisMonitor.run(): StructureValidationError
   - Call notify_alert() with error details
   - Set is_running = False
   - sys.exit(1)
   ↓
6. iPhone receives push notification with full error details
```

## Testing

**Run the test script:**
```bash
python test_notifications.py
```

**Expected output:**
- Shows configured push service and topic/API key status
- Tests notification sending
- Provides setup instructions if not configured
- Guide for subscribing in ntfy app or configuring Pushbullet

**Test manual alert:**
```python
from tennis_monitor.notifications import NotificationManager
from tennis_monitor.config import NotificationConfig

config = NotificationConfig(enable_push_notifications=True)
mgr = NotificationManager(config)
mgr.notify_alert("Test Alert", "This is a test message")
```

## Environment Variables Summary

```bash
# Push notifications
PUSH_SERVICE=ntfy                          # or "pushbullet"
NTFY_TOPIC=mytennismonitor42               # for ntfy
PUSHBULLET_API_KEY=...                     # for Pushbullet
ENABLE_PUSH_NOTIFICATIONS=true

# Structure validation
PW_COURT_MAP=9:Court11,10:Court12,14:Court4,20:Court5

# Monitoring
CHECK_INTERVAL_SECONDS=300
ENABLE_EMAIL_ALERTS=false
ENABLE_PUSH_NOTIFICATIONS=true

# Court preferences
PREFERRED_COURTS=Court11,Court12
PREFERRED_TIME_SLOTS=18:00,19:00,20:00
```

## Backward Compatibility

✅ **Fully backward compatible:**
- Push notifications default to disabled (`ENABLE_PUSH_NOTIFICATIONS=false`)
- If `NTFY_TOPIC` not set, ntfy notifications are silently skipped with warning log
- If `PUSHBULLET_API_KEY` not set, Pushbullet notifications are silently skipped
- Structure validation only runs if `PW_COURT_MAP` is configured
- Auto-booking still disabled (unchanged from previous implementation)

## Known Limitations

1. **ntfy.sh security:** Topic names are not truly private (anyone knowing the topic name can send messages)
   - Solution: Use a long random string as topic name
   - Alternative: Use Pushbullet for full privacy

2. **Email notifications:** Still stub implementation (ready for SMTP integration)

3. **Auto-booking:** Still disabled, deferred for future implementation

4. **Notification retries:** No retry logic if push service is temporarily unavailable
   - Monitor continues running even if alert can't be sent
   - Failed sends are logged for debugging

## Files Modified

1. `src/tennis_monitor/notifications.py` - Added push service implementations
2. `src/tennis_monitor/scraper.py` - Added structure validation
3. `src/tennis_monitor/booking.py` - Added StructureValidationError, error handling
4. `src/tennis_monitor/monitor.py` - Added alert flow, error handling
5. `.env.example` - Added push notification configuration
6. `test_notifications.py` - Enhanced test script
7. `PUSH_NOTIFICATIONS.md` - New comprehensive guide

## Next Steps

1. **User Actions:**
   - Choose push service (ntfy.sh recommended)
   - Set PUSH_SERVICE and NTFY_TOPIC (or PUSHBULLET_API_KEY) in .env
   - Run `python test_notifications.py` to verify setup
   - Subscribe to topic in ntfy app (or install Pushbullet)

2. **Future Enhancements:**
   - Email notifications (SMTP integration)
   - Auto-booking implementation
   - Notification history/log
   - Multiple push services simultaneously
   - Custom alert templates
   - Pushover support

## Validation Checklist

- ✅ Push notifications sent via ntfy.sh (HTTPS POST)
- ✅ Push notifications sent via Pushbullet (with API key)
- ✅ Structure validation detects unknown courts
- ✅ Alert sent before monitor stops
- ✅ Monitor exits with code 1 on structure error
- ✅ Error messages logged and sent to phone
- ✅ Test script verifies configuration
- ✅ Documentation complete
- ✅ Backward compatible (notifications default to disabled)
