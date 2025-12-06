# Quick Start: Push Notifications + Structure Validation

## 1-Minute Setup

### Option A: ntfy.sh (Recommended - Free)

```bash
# 1. Update .env (copy from .env.example if needed)
PUSH_SERVICE=ntfy
NTFY_TOPIC=mytennismonitor42          # Choose any unique name
ENABLE_PUSH_NOTIFICATIONS=true

# 2. Install app on iPhone
# Open App Store → Search "ntfy" → Install

# 3. Subscribe in app
# Open ntfy app → Add (+) → Enter topic: mytennismonitor42 → Subscribe

# 4. Test
python test_notifications.py

# 5. Run monitor
python -m main
```

### Option B: Pushbullet

```bash
# 1. Sign up at https://www.pushbullet.com
# 2. Get API key from https://www.pushbullet.com/account/settings
# 3. Install Pushbullet app on iPhone

# 4. Update .env
PUSH_SERVICE=pushbullet
PUSHBULLET_API_KEY=your_api_key_here
ENABLE_PUSH_NOTIFICATIONS=true

# 5. Test
python test_notifications.py

# 6. Run monitor
python -m main
```

## What You'll Get

### ✅ Court Availability Alerts
When a court matching your preferences is available:
```
📱 Push notification: "Court Court11 - 18:00-19:00: Available"
```

### ✅ Structure Change Alert
If the booking system adds unexpected courts:
```
📱 Push notification: "Booking System Structure Changed: Unknown court IDs detected: 25, 26"
```
Then:
- Monitor stops automatically
- Run: `python map_courts.py`
- Update `PW_COURT_MAP` in `.env`
- Restart monitor

## Configuration

Edit your `.env` file (or `.env.example` → `.env`):

```bash
# Booking system
BOOKING_SYSTEM_URL=https://example-tennis-club.dk
BOOKING_USERNAME=your_username
BOOKING_PASSWORD=your_password

# Court preferences
PREFERRED_COURTS=Court11,Court12
PREFERRED_TIME_SLOTS=18:00,19:00,20:00

# Push notifications (choose one)
PUSH_SERVICE=ntfy                    # or "pushbullet"
NTFY_TOPIC=your_topic                # for ntfy.sh
# PUSHBULLET_API_KEY=...              # for Pushbullet
ENABLE_PUSH_NOTIFICATIONS=true

# Structure validation (REQUIRED if PW_COURT_MAP is set)
PW_COURT_MAP=9:Court11,10:Court12,14:Court4,20:Court5

# Monitoring
CHECK_INTERVAL_SECONDS=300

# For debugging (optional)
LOG_LEVEL=INFO
```

## Running the Monitor

```bash
# Normal mode
python -m main

# Debug mode (verbose logging)
LOG_LEVEL=DEBUG python -m main

# Test without push notifications
ENABLE_PUSH_NOTIFICATIONS=false python -m main
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Not receiving alerts | Run `python test_notifications.py` |
| Monitor stopped with structure change | Run `python map_courts.py` to update court mapping |
| Wrong courts being found | Check `PW_COURT_MAP` has all court IDs |
| Can't find login form | Run `LOG_LEVEL=DEBUG python -m main` to see selectors |

## Key Files

- `PUSH_NOTIFICATIONS.md` - Complete setup guide
- `IMPLEMENTATION.md` - Technical implementation details
- `test_notifications.py` - Verify your push setup
- `map_courts.py` - Discover court ID mappings
- `.env.example` - All configuration options

## How It Works

1. **Availability Check:** Monitor runs every `CHECK_INTERVAL_SECONDS`
2. **Court Validation:** Each court checked against `PW_COURT_MAP`
3. **Unknown Courts?** Monitor stops, sends alert via push service, exits
4. **Match Preferences?** If court matches your preferences → push notification
5. **You get:** Instant iPhone alert with court details

## Need Help?

See full documentation in `PUSH_NOTIFICATIONS.md` for:
- Detailed setup steps
- How structure validation works
- Troubleshooting guide
- Advanced configuration
