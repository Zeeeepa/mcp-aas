"""
Source management service for MCP tool crawler.
"""

import time
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Optional

from ..models import Source, SourceType
from ..utils.logging import get_logger
from ..utils.config import get_config
from ..utils.helpers import is_github_repo, extract_domain
from ..storage.sqlite_storage import SQLiteSourceManager

logger = get_logger(__name__)
config = get_config()


class SourceManager:
    """
    Service for managing sources in the crawler.
    """
    
    def __init__(self):
        """
        Initialize the source manager.
        """
        # Initialize SQLite source manager
        self.source_manager = SQLiteSourceManager()
    
    async def initialize_sources(self) -> List[Source]:
        """
        Initialize sources from the configuration and source list file.
        
        This loads sources from:
        1. The source list file if available
        2. Predefined sources from configuration (as fallback)
        
        Sources are added to SQLite storage for tracking.
        
        Returns:
            List of all sources (existing + newly added).
        """
        logger.info("Initializing sources")
        
        # Use the SQLite source manager to initialize sources
        return await self.source_manager.initialize_sources()
    
    async def add_source(self, source: Source) -> Source:
        """
        Add a new source to the crawler.
        
        Args:
            source: Source to add.
            
        Returns:
            The added source.
        """
        try:
            # Save to SQLite
            return await self.source_manager.add_source(source)
        except Exception as e:
            logger.error(f"Error adding source: {str(e)}")
            raise
    
    async def add_source_by_url(self, url: str, name: Optional[str] = None, 
                               source_type: Optional[SourceType] = None) -> Source:
        """
        Add a new source to the crawler by URL.
        
        Args:
            url: URL of the source.
            name: Optional name for the source. If not provided, will be generated.
            source_type: Optional source type. If not provided, will be detected.
            
        Returns:
            The added source.
        """
        # Detect source type if not provided
        if not source_type:
            if is_github_repo(url):
                # Check if it looks like an awesome list (has "awesome" in the URL)
                if 'awesome' in url.lower():
                    source_type = SourceType.GITHUB_AWESOME_LIST
                else:
                    source_type = SourceType.GITHUB_REPOSITORY
            else:
                source_type = SourceType.WEBSITE
        
        # Generate name if not provided
        if not name:
            domain = extract_domain(url)
            name = f"MCP Tools ({domain})"
        
        # Create source
        source = Source(
            url=url,
            name=name,
            type=source_type,
            has_known_crawler=source_type in [SourceType.GITHUB_AWESOME_LIST, SourceType.GITHUB_REPOSITORY],
        )
        
        # Add to storage
        return await self.add_source(source)
    
    async def get_all_sources(self) -> List[Source]:
        """
        Get all sources from storage.
        
        Returns:
            List of all sources.
        """
        try:
            # Get sources from SQLite
            return await self.source_manager.get_all_sources()
        except Exception as e:
            logger.error(f"Error retrieving sources: {str(e)}")
            return []
    
    async def get_sources_to_crawl(self, time_threshold_hours: int = 24) -> List[Source]:
        """
        Get sources that need to be crawled.
        
        Args:
            time_threshold_hours: Time threshold in hours. Sources that haven't been
                                  crawled in this period will be returned.
            
        Returns:
            List of sources to crawl.
        """
        try:
            # Get sources to crawl from SQLite
            return await self.source_manager.get_sources_to_crawl(time_threshold_hours)
        except Exception as e:
            logger.error(f"Error getting sources to crawl: {str(e)}")
            return []
    
    async def update_source_last_crawl(self, source_id: str, success: bool) -> bool:
        """
        Update a source's last crawl information.
        
        Args:
            source_id: ID of the source to update.
            success: Whether the crawl was successful.
            
        Returns:
            True if successful, False otherwise.
        """
        try:
            # Update source in SQLite
            return await self.source_manager.update_source_last_crawl(source_id, success)
        except Exception as e:
            logger.error(f"Error updating source last crawl: {str(e)}")
            return False

