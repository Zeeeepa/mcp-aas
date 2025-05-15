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
    
    In production, uses SQLiteStorage, in development, uses LocalStorage.
    
    Returns:
        A storage service instance.
    """
    if os.environ.get('USE_LOCAL_STORAGE', 'false').lower() == 'true':
        return LocalStorage()
    else:
        return SQLiteStorage()

