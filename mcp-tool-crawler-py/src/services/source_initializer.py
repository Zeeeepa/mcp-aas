"""
Source initializer service for MCP tool crawler.
Initializes sources from configuration or storage.
"""

import json
import logging
import asyncio
import sys
import os
from pathlib import Path
from typing import Dict, Any, List, Optional

from ..models import Source
from ..services.source_manager import SourceManager
from ..utils.logging import get_logger

logger = get_logger(__name__)

class SourceInitializer:
    """
    Service for initializing sources from configuration or storage.
    """
    
    def __init__(self):
        """
        Initialize the source initializer service.
        """
        self.source_manager = SourceManager()
    
    async def initialize_sources(self, source_file_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Initialize sources from configuration or storage.
        
        This is a replacement for the Lambda handler function.
        
        Args:
            source_file_path: Optional path to a source file to load.
                             If None, uses the default configuration.
            
        Returns:
            Dictionary with the result of the operation.
        """
        try:
            # Set environment variables if source_file_path is provided
            if source_file_path:
                logger.info(f"Initializing sources from file: {source_file_path}")
                # These will be used by the source manager to determine where to load sources from
                os.environ['SOURCE_FILE_PATH'] = source_file_path
            else:
                logger.info("No source file path provided, using default configuration")
            
            # Initialize sources
            sources = await self.source_manager.initialize_sources()
            
            return {
                'sourceCount': len(sources),
                'message': f"Initialized {len(sources)} sources successfully"
            }
            
        except Exception as e:
            logger.error(f"Error initializing sources: {str(e)}")
            raise
    
    def process_initialization(self, source_file_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Process a source initialization request.
        
        This is a replacement for the Lambda handler function.
        
        Args:
            source_file_path: Optional path to a source file to load.
                             If None, uses the default configuration.
            
        Returns:
            Dictionary with the result of the operation.
        """
        logger.info(f"Processing source initialization with file path: {source_file_path}")
        
        try:
            # Run the async function
            result = asyncio.run(self.initialize_sources(source_file_path))
            
            logger.info(f"Initialization complete: {json.dumps(result)}")
            return result
            
        except Exception as e:
            logger.error(f"Error in process_initialization: {str(e)}")
            return {
                'error': str(e),
                'message': "Failed to initialize sources"
            }

