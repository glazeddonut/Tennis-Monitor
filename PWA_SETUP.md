# Tennis Monitor PWA Setup Guide

## What's New

A **Progressive Web App (PWA)** has been added to Tennis Monitor! This allows you to:
- 📱 Access the monitor from your iPhone over VPN as a standalone app
- 🔌 Work offline with cached data
- 🚀 Install on home screen
- 🔄 Get live status updates every 5 seconds
- ⚙️ Configure preferences directly from the PWA

## Quick Start

### 1. Start the Tennis Monitor API Server
```bash
cd ~/Documents/Tennis\ Monitor\ Workspace
source venv/bin/activate
python src/api_server.py
```

Server will start at `http://localhost:8000`

### 2. Access PWA Locally (Testing)
- Open browser: `http://localhost:8000/pwa`
- Settings tab → Enter your API_KEY from `.env`
- Test all functionality

### 3. Access from iPhone (Over VPN)
1. Connect to VPN
2. Open Safari
3. Navigate to `http://<your-nas-ip>:8000/pwa` (e.g., `http://192.168.1.50:8000/pwa`)
4. Tap **Share** → **Add to Home Screen**
5. Name it "Tennis Monitor" → **Add**

App now on your home screen!

## PWA Structure

```
src/tennis_monitor/web/
├── index.html           # Main app structure
├── app.js              # Application logic & API calls
├── styles.css          # Responsive styling
├── service-worker.js   # Offline support & caching
├── manifest.json       # PWA configuration
└── README.md          # Detailed PWA documentation
```

## Features

### Status Tab (📊)
- Real-time monitor status (🟢 Running / 🔴 Stopped)
- Today's statistics (checks performed, slots found)
- Start/Stop controls
- Auto-refresh toggle

### Preferences Tab (⚙️)
- Configure preferred courts (e.g., `Court11,Court12`)
- Configure preferred time slots (e.g., `18:00,19:00,20:00`)
- Set check interval in seconds
- Changes persist on server

### Logs Tab (📋)
- Last 50 log entries
- Color-coded by level (DEBUG, INFO, WARNING, ERROR)
- Real-time updates
- Refresh button for manual updates

### Settings Tab (🔐)
- API Key management
- Browser storage (won't be sent to server)
- App information
- Server status

## How It Works

### API Communication
```
PWA (browser)
    ↓ HTTP requests with X-Token header
Tennis Monitor API Server (port 8000)
    ↓ Serves /pwa/* files + /api/* endpoints
```

### Service Worker (Offline Support)
- **Static files** (HTML, CSS, JS): Cached first, network fallback
- **API calls** (status, logs): Network first, cached fallback
- **Automatic caching** of all visited pages and API responses

### Authentication
- API Key stored in **browser localStorage** 
- Only sent with API requests (header: `X-Token`)
- Not saved on server
- Persists across browser sessions and page reloads

## Configuration

### Environment Variables (Optional)
```bash
# In .env file:
API_HOST=0.0.0.0         # Server listens on all interfaces
API_PORT=8000            # Port for web server
API_KEY=your-secret-key  # API authentication key
```

### Firewall / Port Forwarding
If accessing from outside your network:
- Ensure port 8000 is open
- Or use VPN (recommended for security)

## Troubleshooting

### "API Key invalid" Error
- Verify key matches `.env` API_KEY value
- Check browser console (F12) for errors
- Try re-entering the key in Settings

### Service Worker Not Registering
- Must use HTTPS or localhost
- Check browser console for SW errors
- Force refresh: `Ctrl+Shift+R` (or `Cmd+Shift+R` on Mac)

### Offline Mode Not Working
- You must visit the PWA online first
- Service Worker needs to cache files
- Check browser storage (DevTools → Application → Cache Storage)

### Slow on iPhone
- Check cellular/WiFi signal
- Reduce check interval if API is slow
- Safari on iOS caches aggressively

## API Endpoints Used

```
GET    /api/status              # Get monitor status
GET    /api/config              # Get configuration
POST   /api/config/preferences  # Update preferences
POST   /api/monitor/start       # Start monitoring
POST   /api/monitor/stop        # Stop monitoring
GET    /api/monitor/logs        # Get recent logs
```

All endpoints require `X-Token: <API_KEY>` header.

## Browser Compatibility

| Platform | Browser | Support |
|----------|---------|---------|
| iOS | Safari | ✅ Yes (iOS 12.2+) |
| Android | Chrome | ✅ Yes (Android 5+) |
| Android | Firefox | ✅ Yes |
| Desktop | Chrome | ✅ Yes |
| Desktop | Firefox | ✅ Yes |
| Desktop | Safari | ✅ Yes |
| Desktop | Edge | ✅ Yes |

## Next Steps

1. **Start server**: `python src/api_server.py`
2. **Test locally**: Visit `http://localhost:8000/pwa`
3. **Add to home screen**: Use browser's add to home screen feature
4. **Configure API key**: Enter in Settings tab
5. **Adjust preferences**: Set courts and times in Preferences tab
6. **Monitor**: Watch status updates in real-time

## Files Changed

- **New**: `src/tennis_monitor/web/` directory with 6 files
- **Modified**: `src/tennis_monitor/api.py` (added PWA serving)
- **Status**: All tests still passing ✅

## Support

For PWA-specific issues, check:
- Browser console (F12 → Console)
- Service Worker status (DevTools → Application → Service Workers)
- Cache storage (DevTools → Application → Cache Storage)

For Tennis Monitor issues, check:
- `logs/tennis_monitor.log`
- Monitor status via `/api/status`
- Error alerts via ntfy.sh
