"""Tests for booking system module."""

import pytest
from tennis_monitor.booking import BookingSystemClient


@pytest.fixture
def booking_client():
    """Create a booking client for testing."""
    return BookingSystemClient("http://localhost:8000", username="testuser", password="testpass")


def test_booking_client_initialization(booking_client):
    """Test booking client initialization."""
    assert booking_client.base_url == "http://localhost:8000"
    assert booking_client.username == "testuser"
    assert booking_client.password == "testpass"


def test_get_available_courts(booking_client, monkeypatch):
    """Test fetching available courts."""
    # Mock the scraper to avoid actual browser calls
    def mock_get_available_courts(*args, **kwargs):
        return [
            {"id": "1", "name": "Court A", "time_slot": "10:00"},
            {"id": "2", "name": "Court B", "time_slot": "14:00"},
        ]
    
    monkeypatch.setattr(booking_client.scraper, "get_available_courts", mock_get_available_courts)
    courts = booking_client.get_available_courts()
    
    assert len(courts) == 2
    assert courts[0]["name"] == "Court A"
