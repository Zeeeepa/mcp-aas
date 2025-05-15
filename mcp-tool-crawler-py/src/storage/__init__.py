"""
Storage services for MCP tools.
"""

import os
from typing import List, Union

from .s3_storage import S3Storage
from .sqlite_storage import SQLiteStorage
from ..models import MCPTool, Source
from .local_storage import LocalStorage, LocalSourceStorage


def get_storage():
    """
    Get the appropriate storage service based on the environment.
    
    In production, uses S3Storage, in development, uses SQLiteStorage.
    Now that S3Storage is being replaced, this always returns LocalStorage.
    
    Returns:
        A storage service instance.
    """
    env = os.environ.get('ENVIRONMENT', 'development')
    storage_type = os.environ.get('STORAGE_TYPE', 'sqlite')
    
    if env == 'production' and storage_type == 's3':
        return S3Storage()
    elif storage_type == 'local':
        return LocalStorage()
    else:
        return SQLiteStorage()
    return LocalStorage()

def get_source_storage():
    """
    Get the appropriate source storage service.
    
    Returns:
        A source storage service instance.
    """
    return LocalSourceStorage()

