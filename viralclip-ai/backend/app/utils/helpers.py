"""
Utility Functions for ViralClip AI
Common utilities used across the application
"""
import re
from typing import List, Dict, Any


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename by removing invalid characters
    
    Args:
        filename: Original filename
        
    Returns:
        Sanitized filename safe for all platforms
    """
    # Remove invalid characters
    sanitized = re.sub(r'[<>:"/\\|?*]', '', filename)
    # Replace spaces with underscores
    sanitized = sanitized.replace(' ', '_')
    # Limit length
    return sanitized[:200]


def format_duration(seconds: float) -> str:
    """
    Format duration in human-readable format
    
    Args:
        seconds: Duration in seconds
        
    Returns:
        Formatted string (e.g., "1:30" or "2:15:45")
    """
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    
    if hours > 0:
        return f"{hours}:{minutes:02d}:{secs:02d}"
    else:
        return f"{minutes}:{secs:02d}"


def extract_hashtags(text: str) -> List[str]:
    """
    Extract hashtags from text
    
    Args:
        text: Input text
        
    Returns:
        List of hashtags without # symbol
    """
    pattern = r'#(\w+)'
    matches = re.findall(pattern, text)
    return [match.lower() for match in matches]


def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """
    Truncate text to maximum length
    
    Args:
        text: Input text
        max_length: Maximum length
        suffix: Suffix to add when truncated
        
    Returns:
        Truncated text
    """
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix


def calculate_reading_speed(words: int, duration_seconds: float) -> float:
    """
    Calculate reading speed in words per minute
    
    Args:
        words: Number of words
        duration_seconds: Duration in seconds
        
    Returns:
        Words per minute
    """
    if duration_seconds <= 0:
        return 0.0
    return (words / duration_seconds) * 60


def is_optimal_reading_speed(wpm: float, min_wpm: float = 130, max_wpm: float = 180) -> bool:
    """
    Check if reading speed is optimal for captions
    
    Args:
        wpm: Words per minute
        min_wpm: Minimum optimal WPM
        max_wpm: Maximum optimal WPM
        
    Returns:
        True if within optimal range
    """
    return min_wpm <= wpm <= max_wpm
