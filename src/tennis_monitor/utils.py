"""Utility functions for Tennis Monitor."""

from datetime import datetime
from typing import Optional


def parse_time(time_str: str) -> Optional[int]:
    """Parse time string to minutes since midnight.
    
    Args:
        time_str: Time in HH:MM format
        
    Returns:
        Minutes since midnight or None if invalid
    """
    try:
        time_obj = datetime.strptime(time_str, "%H:%M").time()
        return int(time_obj.hour * 60 + time_obj.minute)
    except ValueError:
        return None


def format_time(minutes: int) -> str:
    """Convert minutes since midnight to HH:MM format.
    
    Args:
        minutes: Minutes since midnight
        
    Returns:
        Time string in HH:MM format
    """
    hours = minutes // 60
    mins = minutes % 60
    return f"{hours:02d}:{mins:02d}"


def is_same_day(date1: str, date2: str) -> bool:
    """Check if two dates are the same day.
    
    Args:
        date1: Date string in YYYY-MM-DD format
        date2: Date string in YYYY-MM-DD format
        
    Returns:
        True if dates are the same day
    """
    try:
        d1 = datetime.strptime(date1, "%Y-%m-%d").date()
        d2 = datetime.strptime(date2, "%Y-%m-%d").date()
        return d1 == d2
    except ValueError:
        return False
