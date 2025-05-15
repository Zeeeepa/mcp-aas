"""
Storage services for MCP tools.
"""

import os
from typing import List, Union

from ..models import MCPTool
from .local_storage import LocalStorage
from .sqlite_storage import SQLiteStorage


def get_storage():
    """
    Get the appropriate storage service based on the environment.
    
    Uses SQLiteStorage by default, falls back to LocalStorage for simple file-based storage.
    
    Returns:
        A storage service instance.
    """
    use_sqlite = os.environ.get('USE_SQLITE', 'true').lower() in ('true', '1', 'yes')
    
    if use_sqlite:
        return SQLiteStorage()
    else:
        return LocalStorage()
"""

