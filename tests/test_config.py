"""Tests for configuration module."""

import os
import pytest
from tennis_monitor.config import AppConfig, get_config


def test_config_loading():
    """Test that configuration loads successfully."""
    config = get_config()
    assert config is not None
    assert isinstance(config, AppConfig)


def test_config_defaults():
    """Test default configuration values."""
    config = AppConfig()
    assert config.monitoring.check_interval_seconds == 300
    assert config.monitoring.auto_book_enabled is False


@pytest.mark.parametrize("env_var,expected", [
    ("CHECK_INTERVAL_SECONDS", "600"),
    ("AUTO_BOOK_ENABLED", "true"),
])
def test_config_from_env(env_var, expected, monkeypatch):
    """Test configuration from environment variables."""
    monkeypatch.setenv(env_var, expected)
    config = AppConfig.from_env()
    
    if env_var == "CHECK_INTERVAL_SECONDS":
        assert config.monitoring.check_interval_seconds == 600
    elif env_var == "AUTO_BOOK_ENABLED":
        assert config.monitoring.auto_book_enabled is True
