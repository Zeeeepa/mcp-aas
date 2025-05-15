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
    
    Uses SQLiteStorage for both production and development environments.
    
    Returns:
        A storage service instance.
    """
    return SQLiteStorage()

