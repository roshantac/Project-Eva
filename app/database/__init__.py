"""
Database abstraction layer
Supports both MongoDB and file-based storage
"""

from .file_db import FileDatabase, connect_file_db, disconnect_file_db, get_file_db

__all__ = [
    'FileDatabase',
    'connect_file_db',
    'disconnect_file_db',
    'get_file_db'
]
