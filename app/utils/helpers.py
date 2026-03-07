"""
Helper utility functions
"""

import uuid
import re
from datetime import datetime
from typing import List, Any, Optional
import html


def generate_session_id() -> str:
    """Generate a unique session ID"""
    return str(uuid.uuid4())


def sanitize_input(text: str, max_length: int = 5000) -> str:
    """
    Sanitize user input
    
    Args:
        text: Input text to sanitize
        max_length: Maximum allowed length
        
    Returns:
        Sanitized text
    """
    if not text:
        return ""
    
    # Only escape < and > to prevent HTML injection
    # Don't escape quotes/apostrophes as they're normal text
    text = text.replace('<', '&lt;').replace('>', '&gt;')
    
    # Trim whitespace
    text = text.strip()
    
    # Limit length
    if len(text) > max_length:
        text = text[:max_length]
    
    return text


def validate_audio_chunk(chunk: bytes, is_final: bool = False) -> bool:
    """
    Validate audio chunk data
    
    Args:
        chunk: Audio data bytes
        is_final: Whether this is the final chunk
        
    Returns:
        True if valid, False otherwise
    """
    if not chunk:
        return False
    
    if not isinstance(chunk, (bytes, bytearray)):
        return False
    
    # Accept any non-empty chunk
    # The accumulated buffer will be validated during processing
    if len(chunk) < 1:
        return False
    
    return True


def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """
    Truncate text to maximum length
    
    Args:
        text: Text to truncate
        max_length: Maximum length
        suffix: Suffix to add if truncated
        
    Returns:
        Truncated text
    """
    if not text or len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)] + suffix


def format_timestamp(date: Optional[datetime] = None) -> str:
    """
    Format timestamp to ISO string
    
    Args:
        date: Datetime object (defaults to now)
        
    Returns:
        ISO formatted timestamp
    """
    if date is None:
        date = datetime.utcnow()
    
    return date.isoformat() + 'Z'


def chunk_array(array: List[Any], size: int) -> List[List[Any]]:
    """
    Split array into chunks
    
    Args:
        array: Array to chunk
        size: Chunk size
        
    Returns:
        List of chunks
    """
    return [array[i:i + size] for i in range(0, len(array), size)]


def extract_location_from_text(text: str) -> Optional[str]:
    """
    Extract location from text
    
    Args:
        text: Input text
        
    Returns:
        Extracted location or None
    """
    # Common patterns for location
    patterns = [
        r'in\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
        r'at\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
        r'for\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
        r'weather\s+(?:in|at|for)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return match.group(1)
    
    return None


def parse_audio_format(audio_data: bytes) -> dict:
    """
    Parse audio format information
    
    Args:
        audio_data: Raw audio bytes
        
    Returns:
        Dictionary with format info
    """
    # Basic format detection
    format_info = {
        'size': len(audio_data),
        'format': 'unknown'
    }
    
    # Check for WAV header
    if audio_data[:4] == b'RIFF':
        format_info['format'] = 'wav'
    # Check for WebM header
    elif audio_data[:4] == b'\x1a\x45\xdf\xa3':
        format_info['format'] = 'webm'
    # Check for MP3 header
    elif audio_data[:3] == b'ID3' or audio_data[:2] == b'\xff\xfb':
        format_info['format'] = 'mp3'
    
    return format_info


def calculate_audio_duration(audio_size: int, sample_rate: int = 16000, channels: int = 1, bit_depth: int = 16) -> float:
    """
    Calculate audio duration from size
    
    Args:
        audio_size: Size in bytes
        sample_rate: Sample rate in Hz
        channels: Number of channels
        bit_depth: Bit depth
        
    Returns:
        Duration in seconds
    """
    bytes_per_sample = (bit_depth / 8) * channels
    num_samples = audio_size / bytes_per_sample
    duration = num_samples / sample_rate
    
    return duration
