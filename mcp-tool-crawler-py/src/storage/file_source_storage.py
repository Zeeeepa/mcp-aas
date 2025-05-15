"""
File-based source storage service for MCP tool crawler.

This module replaces S3 source storage with a local file-based storage.
"""

import yaml
import json
from pathlib import Path
from typing import List, Dict, Any, Optional

from ..models import Source, SourceType
from ..utils.logging import get_logger
from ..utils.config import get_config
from ..utils.helpers import is_github_repo, extract_domain

logger = get_logger(__name__)
config = get_config()


class FileSourceStorage:
    """
    File-based storage service for source lists.
    
    This class replaces S3 source storage with a local file-based storage.
    """
    
    def __init__(self, file_path: Optional[str] = None):
        """
        Initialize the file source storage service.
        
        Args:
            file_path: Path to the source list file. If None, uses the default path.
        """
        if file_path:
            self.file_path = Path(file_path)
        else:
            self.file_path = Path(__file__).parents[3] / 'data' / 'sources.yaml'
        
        # Ensure data directory exists
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
    
    async def load_sources(self) -> List[Source]:
        """
        Load sources from a YAML file.
        
        Returns:
            List of Source objects loaded from the file.
        """
        try:
            # Check if file exists
            if not self.file_path.exists():
                logger.warning(f"No source list found at {self.file_path}")
                return []
            
            # Read file
            with open(self.file_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
            
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
            
            logger.info(f"Loaded {len(sources)} sources from {self.file_path}")
            return sources
        except Exception as e:
            logger.error(f"Error loading sources from file: {str(e)}")
            return []
    
    async def save_sources(self, sources: List[Source]) -> bool:
        """
        Save sources to a YAML file.
        
        Args:
            sources: List of sources to save.
            
        Returns:
            True if successful, False otherwise.
        """
        try:
            # Convert sources to YAML-compatible format
            sources_data = []
            for source in sources:
                source_data = {
                    'url': source.url,
                    'name': source.name,
                    'type': source.type
                }
                sources_data.append(source_data)
            
            # Create YAML data
            data = {
                'sources': sources_data
            }
            
            # Write to file
            with open(self.file_path, 'w', encoding='utf-8') as f:
                yaml.dump(data, f, default_flow_style=False)
            
            logger.info(f"Saved {len(sources)} sources to {self.file_path}")
            return True
        except Exception as e:
            logger.error(f"Error saving sources to file: {str(e)}")
            return False

