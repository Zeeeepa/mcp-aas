"""
Storage services for MCP tools.
"""

import os
from typing import List, Union

from ..models import MCPTool
from .local_storage import LocalStorage
from .s3_storage import S3Storage
from .sqlite_storage import SQLiteStorage


def get_storage():
    """
    Get the appropriate storage service based on the environment.
    
    In production with AWS, uses S3Storage.
    In development with AWS, uses LocalStorage.
    In local mode (default), uses SQLiteStorage.
    
    Returns:
        A storage service instance.
    """
    env = os.environ.get('ENVIRONMENT', 'local')
    storage_type = os.environ.get('STORAGE_TYPE', 'sqlite')
    
    if env == 'production' and storage_type == 'aws':
        return S3Storage()
    elif env == 'development' and storage_type == 'aws':
        return LocalStorage()
    else:
        return SQLiteStorage()
