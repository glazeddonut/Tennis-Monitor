# Push Notifications Setup Guide

The Tennis Monitor now supports **push notifications to your iPhone** via ntfy.sh or Pushbullet, plus **automatic detection of booking system structure changes** with alerts.

## Features

✅ **Real-time Push Notifications**
- Get alerts when courts matching your preferences become available
- Receive alerts when unexpected structure changes are detected
- Choose between ntfy.sh (free) or Pushbullet

✅ **Structure Validation**
- Automatically detects when new/unknown courts appear in the booking system
- Sends you a push notification alert before stopping
- Prevents the monitor from booking the wrong courts

## Quick Setup (ntfy.sh - Recommended)

### Step 1: Install ntfy app on iPhone
1. Open App Store on your iPhone
2. Search for **"ntfy"** (by ntfy.sh)
3. Install the app

### Step 2: Choose a unique topic name
Pick any unique string, e.g., `mytennismonitor42` or `tennis-alerts-12345`

**Important:** Keep this secret! Anyone who knows your topic name can send messages to it.

### Step 3: Update `.env` file
```bash
PUSH_SERVICE=ntfy
NTFY_TOPIC=your_chosen_topic_name
ENABLE_PUSH_NOTIFICATIONS=true
```

### Step 4: Subscribe to topic in ntfy app
1. Open the ntfy app on your iPhone
2. Tap the "+" button to add a new subscription
3. Enter your topic name (must match `NTFY_TOPIC` in `.env`)
4. Tap "Subscribe"

### Step 5: Test (optional)
```bash
python test_notifications.py
```

You should see:
```
✓ NTFY_TOPIC is configured: your_topic_name
  Alert will be sent to: https://ntfy.sh/your_topic_name
✓ Test alert sent successfully!
```

And receive a test alert on your iPhone!

## Alternative: Pushbullet Setup

### Step 1: Sign up for Pushbullet
1. Go to https://www.pushbullet.com
2. Create a free account
3. Install the Pushbullet app on your iPhone

### Step 2: Get your API key
1. Log in to https://www.pushbullet.com
2. Go to Settings: https://www.pushbullet.com/account/settings
3. Copy your "Access Token" (this is your API key)

### Step 3: Update `.env` file
```bash
PUSH_SERVICE=pushbullet
PUSHBULLET_API_KEY=your_access_token_here
ENABLE_PUSH_NOTIFICATIONS=true
```

### Step 4: Test (optional)
```bash
python test_notifications.py
```

## What Alerts Will You Receive?

### 1. Court Availability Alerts
When a court matching your preferences becomes available:
```
Court Court11 - 18:00-19:00: Available
```

### 2. Structure Change Alert (IMPORTANT)
If the booking system adds new courts not in your `PW_COURT_MAP`:
```
Booking System Structure Changed: Unknown court IDs detected: 25, 26
Current court map: {'9': 'Court11', '10': 'Court12', '14': 'Court4', '20': 'Court5'}
Please update PW_COURT_MAP environment variable.
```

When this happens:
1. You'll receive a push notification
2. The monitor will **stop automatically**
3. You need to update `PW_COURT_MAP` in `.env` with the new court mapping
4. Restart the monitor

Use `python map_courts.py` to discover the new court IDs:
```bash
python map_courts.py
```

## Configuration Summary

### Notification Settings
```bash
# Enable/disable push notifications
ENABLE_PUSH_NOTIFICATIONS=true

# Push service: "ntfy" or "pushbullet"
PUSH_SERVICE=ntfy

# ntfy.sh settings
NTFY_TOPIC=your_topic_name

# Pushbullet settings (alternative)
# PUSHBULLET_API_KEY=your_api_key_here
```

### Court Mapping (Structure Validation)
```bash
# Map court IDs to friendly names
# If unknown court IDs are detected, monitor stops and alerts you
PW_COURT_MAP=9:Court11,10:Court12,14:Court4,20:Court5
```

### Other Monitoring Settings
```bash
# How often to check for available courts (seconds)
CHECK_INTERVAL_SECONDS=300

# Court preferences
PREFERRED_COURTS=Court11,Court12
PREFERRED_TIME_SLOTS=18:00,19:00,20:00
```

## Troubleshooting

### I'm not receiving notifications

**For ntfy.sh:**
1. Check that `NTFY_TOPIC` is set in `.env`
2. Check that you subscribed to the correct topic in the ntfy app
3. Check that `ENABLE_PUSH_NOTIFICATIONS=true`
4. Run `python test_notifications.py` to verify setup

**For Pushbullet:**
1. Check that `PUSHBULLET_API_KEY` is set correctly in `.env`
2. Check that Pushbullet app is installed on iPhone
3. Check that `ENABLE_PUSH_NOTIFICATIONS=true`
4. Run `python test_notifications.py` to verify setup

### Monitor stopped with structure change alert

This is **expected behavior** and means the booking system has new courts.

1. Check the alert message for unknown court IDs
2. Run `python map_courts.py` to discover the mapping
3. Update `PW_COURT_MAP` in `.env`
4. Restart the monitor

Example:
```bash
# Run discovery
python map_courts.py

# Check output for new court IDs and their counts
# Found 4 court IDs: Court11 (6 slots), Court12 (5 slots), Court4 (3 slots), Court5 (2 slots)

# Update .env with the complete mapping
PW_COURT_MAP=9:Court11,10:Court12,14:Court4,20:Court5

# Restart monitor
python -m main
```

### Testing without notifications

To test the monitor without setting up push notifications:
```bash
ENABLE_PUSH_NOTIFICATIONS=false python -m main
```

## How Structure Validation Works

The scraper automatically validates that all available courts are in your configured `PW_COURT_MAP`:

1. When checking availability, the scraper fetches all court slots
2. For each slot, it checks if the `court_num` exists in `PW_COURT_MAP`
3. If unknown court IDs are found:
   - A detailed error message is logged
   - A push notification is sent (if enabled)
   - The monitor stops (exit code 1)
4. You then update `PW_COURT_MAP` and restart

This prevents the monitor from accidentally booking courts you don't want!

## Advanced: Testing Structure Validation

To test the alert without modifying the booking system, you can edit `scraper.py` and temporarily add a validation check:

```python
# In src/tennis_monitor/scraper.py, after parsing slots:
if unknown_courts:
    msg = f"Unknown court IDs detected: {', '.join(sorted(unknown_courts))}"
    raise ValueError(msg)
```

Run `python debug_run.py` - if there are unknown courts, you'll see the error message.

## Questions?

Refer to:
- `test_notifications.py` - Test script for push notification setup
- `map_courts.py` - Discover court ID mappings
- `.env.example` - Complete configuration reference
