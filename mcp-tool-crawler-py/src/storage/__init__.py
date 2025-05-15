"""
Storage services for MCP tools.
"""

import os
from typing import List, Union

from ..models import MCPTool, Source
from .local_storage import LocalStorage, LocalSourceStorage


def get_storage():
    """
    Get the appropriate storage service based on the environment.
    
    Now that S3Storage is being replaced, this always returns LocalStorage.
    
    Returns:
        A storage service instance.
    """
    return LocalStorage()

def get_source_storage():
    """
    Get the appropriate source storage service.
    
    Returns:
        A source storage service instance.
    """
    return LocalSourceStorage()

