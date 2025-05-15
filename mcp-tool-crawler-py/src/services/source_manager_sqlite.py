"""
Source management service for MCP tool crawler using SQLite storage.
"""

import time
from datetime import datetime, timedelta
from typing import List, Dict, Optional

from ..models import Source, SourceType
from ..storage.sqlite_storage import SQLiteStorage
from ..storage.local_storage import LocalStorage
from ..utils.logging import get_logger
from ..utils.config import get_config
from ..utils.helpers import is_github_repo, extract_domain

logger = get_logger(__name__)
config = get_config()


class SourceManager:
    """
    Service for managing sources in the crawler using SQLite storage.
    """
    
    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize the source manager.
        
        Args:
            db_path: Optional path to the SQLite database file.
        """
        # Initialize SQLite storage
        self.storage = SQLiteStorage(db_path)
    
    async def initialize_sources(self) -> List[Source]:
        """
        Initialize sources from the configuration and local source list.
        
        This loads sources from:
        1. The local source list file if available
        2. Predefined sources from configuration (as fallback)
        
        Sources are added to SQLite storage for tracking.
        
        Returns:
            List of all sources (existing + newly added).
        """
        logger.info("Initializing sources")
        
        # Get existing sources
        existing_sources = await self.get_all_sources()
        existing_urls = {source.url for source in existing_sources}
        
        # Try to load sources from local file first
        try:
            # Define path to sources.yaml
            sources_path = config.get('local', {}).get('sources_path')
            
            if sources_path:
                from yaml import safe_load
                import os
                
                if os.path.exists(sources_path):
                    with open(sources_path, 'r') as f:
                        data = safe_load(f)
                        sources_data = data.get('sources', [])
                    
                    sources = []
                    for item in sources_data:
                        url = item.get('url', '').strip()
                        if not url:
                            continue
                        
                        name = item.get('name', '').strip()
                        source_type_str = item.get('type', '').strip().lower()
                        
                        # Determine source type
                        if source_type_str:
                            try:
                                source_type = SourceType(source_type_str)
                            except ValueError:
                                # Default to GITHUB_AWESOME_LIST if we can't parse the type
                                source_type = SourceType.GITHUB_AWESOME_LIST if is_github_repo(url) else SourceType.WEBSITE
                        else:
                            # Auto-detect source type
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
                        
                        sources.append(source)
                    
                    if sources:
                        logger.info(f"Loaded {len(sources)} sources from local file")
                        
                        # Add sources from local file that don't already exist
                        for source in sources:
                            if source.url not in existing_urls:
                                await self.add_source(source)
                                existing_sources.append(source)
                                existing_urls.add(source.url)
                                
                                logger.info(f"Added new source from local file: {source.name} ({source.url})")
                        
                        return existing_sources
        except Exception as e:
            logger.warning(f"Error loading sources from local file, falling back to config: {str(e)}")
        
        # If no sources from local file or error occurred, fall back to config
        logger.info("Using predefined sources from configuration")
        
        # Add awesome lists from config
        for url in config.get('sources', {}).get('awesome_lists', []):
            if url not in existing_urls:
                domain = extract_domain(url)
                name = f"Awesome MCP Tools ({domain})"
                
                source = Source(
                    url=url,
                    name=name,
                    type=SourceType.GITHUB_AWESOME_LIST,
                    has_known_crawler=True,
                )
                
                await self.add_source(source)
                existing_sources.append(source)
                existing_urls.add(url)
                
                logger.info(f"Added new source from config: {name} ({url})")
        
        # Add websites from config
        for website in config.get('sources', {}).get('websites', []):
            if website['url'] not in existing_urls:
                source = Source(
                    url=website['url'],
                    name=website['name'],
                    type=SourceType.WEBSITE,
                    has_known_crawler=False,
                )
                
                await self.add_source(source)
                existing_sources.append(source)
                existing_urls.add(website['url'])
                
                logger.info(f"Added new source from config: {website['name']} ({website['url']})")
        
        return existing_sources
    
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
            success = await self.storage.save_source(source)
            if success:
                logger.info(f"Added source: {source.name} ({source.url})")
                return source
            else:
                raise Exception("Failed to save source to SQLite")
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
            sources = await self.storage.get_all_sources()
            logger.info(f"Retrieved {len(sources)} sources from SQLite")
            return sources
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
            # Get all sources
            all_sources = await self.get_all_sources()
            
            # Calculate threshold timestamp
            threshold_time = (datetime.now() - 
                             timedelta(hours=time_threshold_hours)).isoformat()
            
            # Filter sources
            sources_to_crawl = []
            
            for source in all_sources:
                # If the source has never been crawled, or was crawled before the threshold
                if not source.last_crawled or source.last_crawled < threshold_time:
                    sources_to_crawl.append(source)
            
            logger.info(f"Found {len(sources_to_crawl)} sources to crawl")
            return sources_to_crawl
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
            result = await self.storage.update_source_last_crawl(source_id, success)
            
            if result:
                logger.info(f"Updated last crawl for source {source_id}")
            else:
                logger.warning(f"Failed to update last crawl for source {source_id}")
                
            return result
        except Exception as e:
            logger.error(f"Error updating source last crawl: {str(e)}")
            return False

