"""Configuration management for Tennis Monitor."""

import os
from typing import List, Optional
from dotenv import load_dotenv
from pydantic import BaseModel, Field

# Store .env file path for later updates
ENV_FILE = os.path.join(os.path.dirname(__file__), "..", "..", ".env")
load_dotenv(ENV_FILE)


class BookingSystemConfig(BaseModel):
    """Configuration for booking system connection."""
    url: str = Field(default_factory=lambda: os.getenv("BOOKING_SYSTEM_URL", ""))
    api_key: Optional[str] = Field(default_factory=lambda: os.getenv("BOOKING_SYSTEM_API_KEY"))
    username: Optional[str] = Field(default_factory=lambda: os.getenv("BOOKING_USERNAME"))
    password: Optional[str] = Field(default_factory=lambda: os.getenv("BOOKING_PASSWORD"))


class UserPreferencesConfig(BaseModel):
    """User preferences for booking monitoring."""
    preferred_courts: List[str] = Field(
        default_factory=lambda: os.getenv("PREFERRED_COURTS", "").split(",")
    )
    preferred_time_slots: List[str] = Field(
        default_factory=lambda: os.getenv("PREFERRED_TIME_SLOTS", "").split(",")
    )


class NotificationConfig(BaseModel):
    """Configuration for notifications."""
    enable_email_alerts: bool = Field(
        default_factory=lambda: os.getenv("ENABLE_EMAIL_ALERTS", "true").lower() == "true"
    )
    email_recipient: Optional[str] = Field(default_factory=lambda: os.getenv("EMAIL_RECIPIENT"))
    enable_push_notifications: bool = Field(
        default_factory=lambda: os.getenv("ENABLE_PUSH_NOTIFICATIONS", "false").lower() == "true"
    )


class MonitoringConfig(BaseModel):
    """Configuration for monitoring behavior."""
    check_interval_seconds: int = Field(
        default_factory=lambda: int(os.getenv("CHECK_INTERVAL_SECONDS", "300"))
    )
    auto_book_enabled: bool = Field(
        default_factory=lambda: os.getenv("AUTO_BOOK_ENABLED", "false").lower() == "true"
    )
    alive_check_enabled: bool = Field(
        default_factory=lambda: os.getenv("ALIVE_CHECK_ENABLED", "true").lower() == "true"
    )
    alive_check_hour: int = Field(
        default_factory=lambda: int(os.getenv("ALIVE_CHECK_HOUR", "10"))
    )


class AppConfig(BaseModel):
    """Main application configuration."""
    booking_system: BookingSystemConfig = Field(default_factory=BookingSystemConfig)
    user_preferences: UserPreferencesConfig = Field(default_factory=UserPreferencesConfig)
    notifications: NotificationConfig = Field(default_factory=NotificationConfig)
    monitoring: MonitoringConfig = Field(default_factory=MonitoringConfig)

    @classmethod
    def from_env(cls) -> "AppConfig":
        """Load configuration from environment variables."""
        return cls(
            booking_system=BookingSystemConfig(),
            user_preferences=UserPreferencesConfig(),
            notifications=NotificationConfig(),
            monitoring=MonitoringConfig(),
        )


def update_env_file(updates: dict[str, str]) -> bool:
    """Update environment variables in .env file.
    
    Args:
        updates: Dictionary of environment variable names and values to update
        
    Returns:
        True if successful, False otherwise
    """
    if not os.path.exists(ENV_FILE):
        return False
    
    try:
        # Read existing .env file
        with open(ENV_FILE, "r") as f:
            lines = f.readlines()
        
        # Create a dictionary to track which keys were updated
        updated_keys = set()
        new_lines = []
        
        # Update existing lines
        for line in lines:
            key = line.split("=")[0].strip() if "=" in line else ""
            
            if key in updates:
                # Update this line
                new_lines.append(f"{key}={updates[key]}\n")
                updated_keys.add(key)
            else:
                # Keep original line
                new_lines.append(line)
        
        # Add any new keys that weren't in the file
        for key, value in updates.items():
            if key not in updated_keys:
                new_lines.append(f"{key}={value}\n")
        
        # Write back to .env file
        with open(ENV_FILE, "w") as f:
            f.writelines(new_lines)
        
        # Reload environment
        load_dotenv(ENV_FILE, override=True)
        
        return True
    except Exception as e:
        print(f"Error updating .env file: {e}")
        return False


def get_config() -> AppConfig:
    """Get application configuration."""
    return AppConfig.from_env()
