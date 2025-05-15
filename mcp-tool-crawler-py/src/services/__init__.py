"""
MCP Tool Crawler services package.
"""

import os

def get_source_manager():
    """
    Get the appropriate source manager based on the environment.
    
    In production with S3 storage, uses DynamoDB SourceManager,
    otherwise uses SQLiteSourceManager.
    
    Returns:
        A source manager instance.
    """
    env = os.environ.get('ENVIRONMENT', 'development')
    storage_type = os.environ.get('STORAGE_TYPE', 'sqlite')
    
    if env == 'production' and storage_type == 's3':
        from .source_manager import SourceManager
        return SourceManager()
    else:
        from .sqlite_source_manager import SQLiteSourceManager
        return SQLiteSourceManager()
