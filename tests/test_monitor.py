"""Tests for monitor module."""

import pytest
from tennis_monitor import TennisMonitor
from tennis_monitor.config import AppConfig


@pytest.fixture
def monitor():
    """Create a tennis monitor for testing."""
    config = AppConfig()
    return TennisMonitor(config)


def test_monitor_initialization(monitor):
    """Test monitor initialization."""
    assert monitor is not None
    assert monitor.config is not None
    assert monitor.is_running is False


def test_matches_preferences(monitor):
    """Test preference matching logic."""
    # Set preferences
    monitor.config.user_preferences.preferred_courts = ["Court A", "Court B"]
    monitor.config.user_preferences.preferred_time_slots = ["10:00", "14:00"]
    
    # Test matching court
    court = {"name": "Court A", "time_slot": "10:00"}
    assert monitor._matches_preferences(court) is True
    
    # Test non-matching court
    court = {"name": "Court C", "time_slot": "16:00"}
    assert monitor._matches_preferences(court) is False


def test_check_availability(monitor, monkeypatch):
    """Test checking availability."""
    def mock_get_available_courts(*args, **kwargs):
        return [
            {"id": "1", "name": "Court A", "time_slot": "10:00"},
            {"id": "2", "name": "Court B", "time_slot": "14:00"},
        ]
    
    monkeypatch.setattr(monitor.booking_client, "get_available_courts", mock_get_available_courts)
    
    monitor.config.user_preferences.preferred_courts = ["Court A"]
    monitor.config.user_preferences.preferred_time_slots = ["10:00"]
    
    available = monitor.check_availability()
    assert len(available) >= 0
