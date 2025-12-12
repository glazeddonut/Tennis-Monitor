# Tennis Monitor PWA

Progressive Web App for Tennis Monitor - realtime monitoring of tennis court availability.

## Features

- 📱 **Mobile-optimized** - Responsive design for iPhone, Android, and tablets
- 🔌 **Offline support** - Service Worker caches data for offline access
- 🚀 **Installable** - Add to home screen like a native app
- ⚡ **Fast** - Instant loading with service worker caching
- 🔄 **Auto-refresh** - Live status updates every 5 seconds
- 🎾 **Court preferences** - Configure courts and time slots
- 📊 **Live logs** - View monitor logs in real-time
- 🔐 **API key storage** - Browser storage for persistent authentication

## Installation

The PWA is served automatically from the Tennis Monitor API server at `/pwa`.

### On iPhone:
1. Open Safari
2. Navigate to `http://your-nas-ip:8000/pwa` (or `http://localhost:8000/pwa` if local)
3. Tap **Share** → **Add to Home Screen**
4. Enter a name (e.g., "Tennis Monitor")
5. Tap **Add**

The app is now on your home screen and can be opened like a native app!

### On Android:
1. Open Chrome
2. Navigate to `http://your-nas-ip:8000/pwa`
3. Tap **⋮** (menu) → **Install app** → **Install**
4. The app appears on your home screen

## Accessing the PWA

- **Full URL**: `http://your-nas-ip:8000/pwa`
- **API endpoint**: `/api/status`, `/api/config`, etc. (requires API_KEY header)

## Configuration

### API Key
1. Open the PWA in your browser
2. Go to **Settings** tab
3. Enter your API_KEY (from Tennis Monitor `.env` file)
4. Tap **Save API Key**
5. The key is stored in your browser's localStorage and persists across sessions

## Tabs Overview

### 📊 Status
- Real-time monitor status (🟢 Running / 🔴 Stopped)
- Checks performed today
- Slots found today
- Start/Stop controls
- Auto-refresh toggle

### ⚙️ Preferences
- Configure preferred courts (comma-separated)
- Configure preferred time slots (comma-separated)
- Set check interval (seconds)
- Save changes to server

### 📋 Logs
- Real-time log viewer
- Last 50 log entries
- Color-coded log levels (DEBUG, INFO, WARNING, ERROR)

### 🔐 Settings
- API Key management
- App information
- Server connection status

## Service Worker

The PWA uses a Service Worker for:
- **Offline caching** - Serves cached content when offline
- **Network-first for API calls** - Uses network when available, falls back to cache
- **Cache-first for static assets** - Serves static files from cache first
- **Push notifications** - Receives and displays push notifications

## Offline Functionality

When offline:
- The PWA continues to work with cached data
- API calls use cached responses from your last online session
- All UI is available, but real-time updates won't work
- Connection is automatically restored when network is available

## Browser Support

- ✅ iPhone/iPad (iOS 12.2+) - Safari
- ✅ Android (Android 5+) - Chrome, Firefox
- ✅ Desktop - All modern browsers (Chrome, Firefox, Safari, Edge)

### Note on iOS PWA Limitations

iOS PWAs have some limitations:
- No background sync
- Limited storage (usually ~50MB)
- Push notifications not supported (use ntfy.sh app instead)
- Limited to 5 concurrent open windows per app

## Storage & Privacy

- **API Key**: Stored in browser's localStorage, not sent to server
- **Cache**: Stored locally, can be cleared from browser settings
- **Logs**: Only stored on server, streamed to PWA

To clear all app data:
1. iPhone: Settings → Safari → Clear History and Website Data
2. Android: Chrome Settings → Site settings → Clear all data

## Development

The PWA consists of:
- `index.html` - Main HTML structure
- `styles.css` - Responsive styling
- `app.js` - Application logic and API communication
- `service-worker.js` - Offline support and caching
- `manifest.json` - PWA configuration

All files are served from `/src/tennis_monitor/web/` directory.

## Troubleshooting

### PWA won't install
- Make sure you're using HTTPS (or localhost for testing)
- Check browser console for Service Worker errors
- Try clearing cache and reloading

### API Key not working
- Verify the key matches your Tennis Monitor `.env` API_KEY
- Check browser console for authentication errors
- Try re-entering the key in Settings

### Offline mode not working
- Check that Service Worker is registered (browser console)
- Ensure you've visited the PWA online first
- Try offline with a page you've previously viewed

### Slow performance
- Clear browser cache
- Check internet connection (5G/WiFi)
- Monitor API server performance
- Check device storage space
