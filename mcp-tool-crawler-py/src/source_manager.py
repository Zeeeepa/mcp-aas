"""
Consolidated source manager module for MCP tools.
Combines functionality from multiple source manager modules into a single file.
"""

import os
import yaml
from typing import List, Dict, Any, Optional
from urllib.parse import urlparse

from .models import Source, SourceType
from .storage import StorageFactory
from .utils.config import get_config
from .utils.logging import get_logger

logger = get_logger(__name__)


class SourceManager:
    """Manager for MCP tool sources."""
    
    def __init__(self, storage_type: str = "sqlite"):
        """
        Initialize the source manager.
        
        Args:
            storage_type: The type of storage to use.
        """
        self.config = get_config()
        
        if storage_type == "sqlite":
            self.storage = StorageFactory.create_storage(
                "sqlite",
                db_path=self.config["storage"]["sqlite"]["db_path"]
            )
        else:
            self.storage = StorageFactory.create_storage(
                "local",
                tools_file_path=self.config["storage"]["local"]["tools_file_path"],
                sources_file_path=self.config["storage"]["local"]["sources_file_path"]
            )
    
    async def initialize_sources(self) -> List[Source]:
        """
        Initialize sources from predefined sources.
        
        Returns:
            A list of initialized sources.
        """
        # Get existing sources
        existing_sources = await self.get_all_sources()
        
        # Check if we already have sources
        if existing_sources:
            logger.info(f"Found {len(existing_sources)} existing sources")
            return existing_sources
        
        # Initialize from predefined sources
        sources = []
        
        # Add awesome lists
        for url in self.config["sources"]["awesome_lists"]:
            source = await self.add_source_by_url(url)
            if source:
                sources.append(source)
        
        # Add websites
        for website in self.config["sources"]["websites"]:
            source = await self.add_source_by_url(
                website["url"],
                website.get("name")
            )
            if source:
                sources.append(source)
        
        logger.info(f"Initialized {len(sources)} sources")
        return sources
    
    async def get_all_sources(self) -> List[Source]:
        """
        Get all sources.
        
        Returns:
            A list of all sources.
        """
        return self.storage.get_all_sources()
    
    async def get_source(self, source_id: str) -> Optional[Source]:
        """
        Get a source by ID.
        
        Args:
            source_id: The ID of the source to get.
            
        Returns:
            The source if found, None otherwise.
        """
        return self.storage.get_source(source_id)
    
    async def add_source_by_url(self, url: str, name: Optional[str] = None, source_type: Optional[SourceType] = None) -> Optional[Source]:
        """
        Add a new source by URL.
        
        Args:
            url: The URL of the source.
            name: Optional name for the source.
            source_type: Optional type for the source.
            
        Returns:
            The added source if successful, None otherwise.
        """
        # Parse URL to determine source type if not provided
        if not source_type:
            source_type = self._determine_source_type(url)
        
        # Generate name if not provided
        if not name:
            name = self._generate_source_name(url, source_type)
        
        # Create source
        source = Source(
            url=url,
            name=name,
            type=source_type,
            has_known_crawler=self._has_known_crawler(source_type)
        )
        
        # Save source
        if self.storage.save_source(source):
            logger.info(f"Added source: {source.name} ({source.url})")
            return source
        else:
            logger.error(f"Failed to add source: {url}")
            return None
    
    def _determine_source_type(self, url: str) -> SourceType:
        """
        Determine the type of a source based on its URL.
        
        Args:
            url: The URL of the source.
            
        Returns:
            The determined source type.
        """
        parsed_url = urlparse(url)
        
        if parsed_url.netloc == "github.com":
            # Check if it's an awesome list
            path_parts = parsed_url.path.strip("/").split("/")
            if len(path_parts) == 2:
                repo_name = path_parts[1].lower()
                if "awesome" in repo_name:
                    return SourceType.GITHUB_AWESOME_LIST
            
            return SourceType.GITHUB_REPOSITORY
        
        return SourceType.WEBSITE
    
    def _generate_source_name(self, url: str, source_type: SourceType) -> str:
        """
        Generate a name for a source based on its URL and type.
        
        Args:
            url: The URL of the source.
            source_type: The type of the source.
            
        Returns:
            A generated name for the source.
        """
        parsed_url = urlparse(url)
        
        if source_type == SourceType.GITHUB_AWESOME_LIST or source_type == SourceType.GITHUB_REPOSITORY:
            path_parts = parsed_url.path.strip("/").split("/")
            if len(path_parts) >= 2:
                return f"{path_parts[0]}/{path_parts[1]}"
        
        return parsed_url.netloc
    
    def _has_known_crawler(self, source_type: SourceType) -> bool:
        """
        Determine if a source type has a known crawler.
        
        Args:
            source_type: The type of the source.
            
        Returns:
            True if the source type has a known crawler, False otherwise.
        """
        return source_type in [SourceType.GITHUB_AWESOME_LIST]

