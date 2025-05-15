"""
Source management service for MCP tool crawler.
"""

import time
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Optional

import boto3
from boto3.dynamodb.conditions import Key, Attr

from ..models import Source, SourceType
from ..utils.logging import get_logger
from ..utils.config import get_config
from ..utils.helpers import is_github_repo, extract_domain
from ..storage import get_source_storage

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
        # Initialize DynamoDB client
        self.dynamodb = boto3.resource('dynamodb')
        self.table_name = config['aws']['dynamodb_tables']['sources']
        self.table = self.dynamodb.Table(self.table_name)
    
    async def initialize_sources(self) -> List[Source]:
        """
        Initialize sources from the configuration and local source list.
        
        This loads sources from:
        1. The local source list file if available
        2. Predefined sources from configuration (as fallback)
        
        Sources are added to DynamoDB storage for tracking.
        
        Returns:
            List of all sources (existing + newly added).
        """
        logger.info("Initializing sources")
        
        # Get existing sources
        existing_sources = await self.get_all_sources()
        existing_urls = {source.url for source in existing_sources}
        
        # Try to load sources from local storage first
        try:
            source_storage = get_source_storage()
            local_sources = await source_storage.load_sources()
            
            if local_sources:
                logger.info(f"Loaded {len(local_sources)} sources from local storage")
                
                # Add sources from local storage that don't already exist
                for source in local_sources:
                    if source.url not in existing_urls:
                        await self.add_source(source)
                        existing_sources.append(source)
                        existing_urls.add(source.url)
                        
                        logger.info(f"Added new source from local storage: {source.name} ({source.url})")
                
                return existing_sources
        except Exception as e:
            logger.warning(f"Error loading sources from local storage, falling back to config: {str(e)}")
        
        # If no sources from local storage or error occurred, fall back to config
        logger.info("Using predefined sources from configuration")
        
        # Add awesome lists from config
        for url in config['sources']['awesome_lists']:
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
        for website in config['sources']['websites']:
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
            # Save to DynamoDB
            self.table.put_item(Item=source.dict())
            logger.info(f"Added source: {source.name} ({source.url})")
            return source
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
            # In a real implementation, this would use paginator for large numbers of sources
            response = self.table.scan()
            
            sources = [Source(**item) for item in response.get('Items', [])]
            logger.info(f"Retrieved {len(sources)} sources from DynamoDB")
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
            threshold_time = (datetime.now(timezone.utc) - 
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
            # Update source
            self.table.update_item(
                Key={'id': source_id},
                UpdateExpression='SET last_crawled = :timestamp, last_crawl_status = :status',
                ExpressionAttributeValues={
                    ':timestamp': datetime.now(timezone.utc).isoformat(),
                    ':status': 'success' if success else 'failed',
                },
            )
            
            logger.info(f"Updated last crawl for source {source_id}")
            return True
        except Exception as e:
            logger.error(f"Error updating source last crawl: {str(e)}")
            return False
