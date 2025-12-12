// Tennis Monitor PWA - Main Application
// Communicates with Tennis Monitor REST API

class TennisMonitorApp {
  constructor() {
    this.apiKey = localStorage.getItem('tennis-monitor-api-key') || '';
    this.apiUrl = this.getApiUrl();
    this.statusRefreshInterval = null;
    this.autoRefreshEnabled = true;

    this.init();
  }

  getApiUrl() {
    // PWA is served from same origin as API
    const protocol = window.location.protocol;
    const host = window.location.hostname;
    const port = window.location.port || (protocol === 'https:' ? 443 : 80);
    return `${protocol}//${host}${port !== 80 && port !== 443 ? ':' + port : ''}`;
  }

  async init() {
    this.setupEventListeners();
    this.registerServiceWorker();
    await this.loadStatus();
    await this.loadServerInfo();
    this.startAutoRefresh();
  }

  // Register Service Worker for offline support
  async registerServiceWorker() {
    if ('serviceWorker' in navigator) {
      try {
        await navigator.serviceWorker.register('/pwa/service-worker.js', {
          scope: '/pwa'
        });
        console.log('[PWA] Service Worker registered');
      } catch (error) {
        console.error('[PWA] Service Worker registration failed:', error);
      }
    }
  }

  // API Methods
  async apiCall(endpoint, options = {}) {
    const url = `${this.apiUrl}${endpoint}`;
    const headers = {
      'Content-Type': 'application/json',
      'X-Token': this.apiKey,
      ...options.headers
    };

    try {
      const response = await fetch(url, {
        ...options,
        headers
      });

      if (response.status === 401) {
        this.showError('API Key invalid. Please check your configuration.');
        return null;
      }

      if (!response.ok) {
        throw new Error(`API Error: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('[API Error]', error);
      this.showError(`API Error: ${error.message}`);
      return null;
    }
  }

  async loadStatus() {
    const data = await this.apiCall('/api/status');
    if (data) {
      this.updateStatusDisplay(data);
    }
  }

  async loadConfig() {
    const data = await this.apiCall('/api/config');
    if (data) {
      this.updateConfigDisplay(data);
    }
  }

  async loadServerInfo() {
    try {
      const serverUrl = this.apiUrl;
      document.getElementById('server-info').textContent = `${serverUrl} ✓`;
    } catch (e) {
      document.getElementById('server-info').textContent = 'Unknown';
    }
  }

  async loadLogs() {
    const data = await this.apiCall('/api/monitor/logs');
    if (data) {
      this.updateLogsDisplay(data);
    }
  }

  async startMonitor() {
    const result = await this.apiCall('/api/monitor/start', { method: 'POST' });
    if (result) {
      this.showSuccess('Monitor started');
      await this.loadStatus();
    }
  }

  async stopMonitor() {
    const result = await this.apiCall('/api/monitor/stop', { method: 'POST' });
    if (result) {
      this.showSuccess('Monitor stopped');
      await this.loadStatus();
    }
  }

  async updatePreferences() {
    const courts = document.getElementById('courts-input').value;
    const times = document.getElementById('times-input').value;
    const interval = document.getElementById('interval-input').value;

    const preferences = {
      preferred_courts: courts,
      preferred_time_slots: times,
      check_interval_seconds: interval
    };

    const result = await this.apiCall('/api/config/preferences', {
      method: 'POST',
      body: JSON.stringify(preferences)
    });

    if (result) {
      this.showSuccess('Preferences updated');
      await this.loadConfig();
    }
  }

  async saveApiKey() {
    const key = document.getElementById('api-key-input').value;
    if (key) {
      this.apiKey = key;
      localStorage.setItem('tennis-monitor-api-key', key);
      this.showSuccess('API Key saved');
      // Test the connection
      const status = await this.apiCall('/api/status');
      if (status) {
        this.showSuccess('API connection verified ✓');
      }
    }
  }

  // UI Updates
  updateStatusDisplay(data) {
    const isRunning = data.is_running;
    const statusIcon = document.getElementById('status-icon');
    const statusText = document.getElementById('status-text');
    const checksText = document.getElementById('checks-text');
    const slotsText = document.getElementById('slots-text');
    const startBtn = document.getElementById('start-btn');
    const stopBtn = document.getElementById('stop-btn');

    if (isRunning) {
      statusIcon.textContent = '🟢';
      statusText.textContent = 'RUNNING';
      statusIcon.className = 'status-icon running';
      startBtn.disabled = true;
      stopBtn.disabled = false;
    } else {
      statusIcon.textContent = '🔴';
      statusText.textContent = 'STOPPED';
      statusIcon.className = 'status-icon stopped';
      startBtn.disabled = false;
      stopBtn.disabled = true;
    }

    checksText.textContent = data.checks_performed_today || 0;
    slotsText.textContent = data.slots_found_today || 0;
    
    // Format last check time
    let lastCheckText = 'Never checked';
    if (data.last_check_time) {
      try {
        const date = new Date(data.last_check_time);
        if (!isNaN(date.getTime())) {
          lastCheckText = date.toLocaleString();
        }
      } catch (e) {
        lastCheckText = 'Time unknown';
      }
    }
    document.getElementById('last-check').textContent = lastCheckText;
  }

  updateConfigDisplay(data) {
    document.getElementById('courts-input').value = data.preferred_courts || '';
    document.getElementById('times-input').value = data.preferred_time_slots || '';
    document.getElementById('interval-input').value = data.check_interval_seconds || 30;
  }

  updateLogsDisplay(data) {
    const logsList = document.getElementById('logs-list');
    logsList.innerHTML = '';

    // Handle both array of strings and object with logs array
    let logs = [];
    if (Array.isArray(data)) {
      logs = data;
    } else if (data && data.logs) {
      logs = data.logs;
    }

    if (logs.length === 0) {
      logsList.innerHTML = '<div style="color: #9ca3af; text-align: center; padding: 20px;">No logs available</div>';
      return;
    }

    logs.slice(0, 50).forEach((logLine) => {
      const logItem = document.createElement('div');
      logItem.className = 'log-item';
      
      // Parse log line if it's a string
      let logHtml = '';
      if (typeof logLine === 'string') {
        // Extract timestamp if present (format: "YYYY-MM-DD HH:MM:SS,mmm")
        const timestampMatch = logLine.match(/^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})/);
        const timestamp = timestampMatch ? timestampMatch[1] : '';
        
        // Extract log level
        const levelMatch = logLine.match(/(DEBUG|INFO|WARNING|ERROR|CRITICAL)/);
        const level = levelMatch ? levelMatch[1] : 'INFO';
        
        // Get the message (everything after the level indicator)
        const message = logLine.replace(/^.*?(DEBUG|INFO|WARNING|ERROR|CRITICAL):/, '').trim();
        
        logHtml = `
          <span class="log-time">${timestamp}</span>
          <span class="log-level log-${level.toLowerCase()}">${level}</span>
          <span class="log-message">${this.escapeHtml(message)}</span>
        `;
      } else if (typeof logLine === 'object') {
        // Handle structured log objects
        const timestamp = logLine.timestamp ? new Date(logLine.timestamp).toLocaleTimeString() : '';
        const level = logLine.level || 'INFO';
        const message = logLine.message || JSON.stringify(logLine);
        
        logHtml = `
          <span class="log-time">${timestamp}</span>
          <span class="log-level log-${level.toLowerCase()}">${level}</span>
          <span class="log-message">${this.escapeHtml(message)}</span>
        `;
      }
      
      logItem.innerHTML = logHtml;
      logsList.appendChild(logItem);
    });
  }

  // Event Listeners
  setupEventListeners() {
    document.getElementById('start-btn')?.addEventListener('click', () => this.startMonitor());
    document.getElementById('stop-btn')?.addEventListener('click', () => this.stopMonitor());
    document.getElementById('update-prefs-btn')?.addEventListener('click', () => this.updatePreferences());
    document.getElementById('save-api-key-btn')?.addEventListener('click', () => this.saveApiKey());
    document.getElementById('refresh-logs-btn')?.addEventListener('click', () => this.loadLogs());
    document.getElementById('refresh-status-btn')?.addEventListener('click', () => this.loadStatus());

    // Tab switching
    document.querySelectorAll('[data-tab]').forEach((btn) => {
      btn.addEventListener('click', (e) => this.switchTab(e.target.dataset.tab));
    });

    // Auto-refresh toggle
    document.getElementById('auto-refresh')?.addEventListener('change', (e) => {
      this.autoRefreshEnabled = e.target.checked;
      if (this.autoRefreshEnabled) {
        this.startAutoRefresh();
      } else {
        this.stopAutoRefresh();
      }
    });
  }

  switchTab(tabName) {
    // Hide all tabs
    document.querySelectorAll('.tab-content').forEach((tab) => {
      tab.style.display = 'none';
    });

    // Deactivate all buttons
    document.querySelectorAll('[data-tab]').forEach((btn) => {
      btn.classList.remove('active');
    });

    // Show selected tab
    const tab = document.getElementById(`tab-${tabName}`);
    if (tab) {
      tab.style.display = 'block';
    }

    // Activate button
    const btn = document.querySelector(`[data-tab="${tabName}"]`);
    if (btn) {
      btn.classList.add('active');
    }

    // Load data for specific tabs
    if (tabName === 'preferences') {
      this.loadConfig();
    } else if (tabName === 'logs') {
      this.loadLogs();
    } else if (tabName === 'settings') {
      this.loadServerInfo();
    }
  }

  startAutoRefresh() {
    if (this.statusRefreshInterval) return;
    this.statusRefreshInterval = setInterval(() => {
      this.loadStatus();
    }, 5000); // Refresh every 5 seconds
  }

  stopAutoRefresh() {
    if (this.statusRefreshInterval) {
      clearInterval(this.statusRefreshInterval);
      this.statusRefreshInterval = null;
    }
  }

  // Utility Methods
  showSuccess(message) {
    this.showNotification(message, 'success');
  }

  showError(message) {
    this.showNotification(message, 'error');
  }

  showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.textContent = message;
    document.body.appendChild(notification);

    setTimeout(() => {
      notification.classList.add('show');
    }, 100);

    setTimeout(() => {
      notification.classList.remove('show');
      setTimeout(() => notification.remove(), 300);
    }, 3000);
  }

  escapeHtml(text) {
    const map = {
      '&': '&amp;',
      '<': '&lt;',
      '>': '&gt;',
      '"': '&quot;',
      "'": '&#039;'
    };
    return text.replace(/[&<>"']/g, (m) => map[m]);
  }
}

// Initialize app when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
  window.app = new TennisMonitorApp();
});
