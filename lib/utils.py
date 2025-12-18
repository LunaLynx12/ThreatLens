"""
Utility functions for Discord bot operations.
"""

from typing import List
import os
from lib.config import EMBED_FIELD_VALUE_MAX


def truncate_text(text: str, max_length: int, suffix: str = "...") -> str:
    """
    Safely truncate text to max length.
    
    Args:
        text: The text to truncate
        max_length: Maximum allowed length
        suffix: Suffix to add when truncating (default: "...")
    
    Returns:
        Truncated text with suffix if needed
    """
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix


def truncate_list_to_field(items: List[str], max_length: int = EMBED_FIELD_VALUE_MAX) -> str:
    """
    Convert list to bullet points, truncating if needed.
    
    Args:
        items: List of items to format
        max_length: Maximum length for the field value
    
    Returns:
        Formatted string with bullet points
    """
    if not items:
        return "None specified"
    
    result = []
    current_length = 0
    prefix = "• "
    suffix = "\n"
    
    for item in items:
        item_text = f"{prefix}{item}{suffix}"
        if current_length + len(item_text) > max_length - 10:
            result.append("...")
            break
        result.append(item_text)
        current_length += len(item_text)
    
    return "".join(result).strip()


def get_error_color(error_message: str) -> int:
    """
    Determine embed color based on error message type.
    
    Args:
        error_message: The error message string
    
    Returns:
        Color code (hex integer)
    """
    from lib.config import COLOR_WARNING, COLOR_ERROR
    
    if "⚠️" in error_message:
        return COLOR_WARNING
    elif "❌" in error_message:
        return COLOR_ERROR
    else:
        return COLOR_ERROR


def get_allowed_implement_users() -> List[int]:
    """
    Get list of user IDs allowed to mark ideas as implemented.
    Loads from environment variable or returns empty list (only owner).
    
    Returns:
        List of user IDs
    """
    env_users = os.getenv('ALLOWED_IMPLEMENT_USERS', '')
    if env_users:
        try:
            return [int(uid.strip()) for uid in env_users.split(',') if uid.strip()]
        except ValueError:
            return []
    return []


def can_mark_implemented(user_id: int, user_roles: List[str] = None) -> bool:
    """
    Check if a user can mark ideas as implemented.
    
    Args:
        user_id: Discord user ID
        user_roles: List of role names the user has (optional)
    
    Returns:
        True if user can mark ideas as implemented
    """
    allowed_users = get_allowed_implement_users()
    if allowed_users and user_id in allowed_users:
        return True
    
    if user_roles:
        from lib.config import ALLOWED_IMPLEMENT_ROLES
        if ALLOWED_IMPLEMENT_ROLES:
            for role in user_roles:
                if role in ALLOWED_IMPLEMENT_ROLES:
                    return True
    
    return False
