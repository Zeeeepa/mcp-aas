"""
Local file storage service for MCP tools.
"""

import json
import os
import yaml
from pathlib import Path
from typing import List, Dict, Any, Optional

from ..models import MCPTool, Source, SourceType
from ..utils.logging import get_logger
from ..utils.helpers import is_github_repo, extract_domain

logger = get_logger(__name__)


class LocalStorage:
    """
    Local file storage service for MCP tools.
    """
    
    def __init__(self, file_path: Optional[str] = None, source_list_path: Optional[str] = None):
        """
        Initialize the local storage service.
        
        Args:
            file_path: Path to the file to store tools in. If None, uses the default path.
            source_list_path: Path to the file to store sources in. If None, uses the default path.
        """
        if file_path:
            self.file_path = Path(file_path)
        else:
            self.file_path = Path(__file__).parents[3] / 'data' / 'tools.json'
        
        if source_list_path:
            self.source_list_path = Path(source_list_path)
        else:
            self.source_list_path = Path(__file__).parents[3] / 'data' / 'sources.yaml'
        
        # Ensure data directory exists
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
    
    async def save_tools(self, tools: List[MCPTool]) -> bool:
        """
        Save tools to a local file.
        
        Args:
            tools: List of tools to save.
            
        Returns:
            True if successful, False otherwise.
        """
        try:
            # Convert tools to JSON
            tools_json = [tool.dict() for tool in tools]
            
            # Write to file
            with open(self.file_path, 'w', encoding='utf-8') as f:
                json.dump(tools_json, f, indent=2)
            
            logger.info(f"Saved {len(tools)} tools to {self.file_path}")
            return True
        except Exception as e:
            logger.error(f"Error saving tools to local file: {str(e)}")
            return False
    
    async def load_tools(self) -> List[MCPTool]:
        """
        Load tools from a local file.
        
        Returns:
            List of tools loaded from the file.
        """
        try:
            # Check if file exists
            if not self.file_path.exists():
                logger.warning(f"No tool catalog found at {self.file_path}")
                return []
            
            # Read file
            with open(self.file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Convert to MCPTool objects
            tools = [MCPTool(**item) for item in data]
            
            logger.info(f"Loaded {len(tools)} tools from {self.file_path}")
            return tools
        except Exception as e:
            logger.error(f"Error loading tools from local file: {str(e)}")
            return []
    
    async def load_sources(self) -> List[Source]:
        """
        Load sources from a local YAML file.
        
        Returns:
            List of Source objects loaded from the file.
        """
        try:
            # Check if file exists
            if not self.source_list_path.exists():
                logger.warning(f"No source list found at {self.source_list_path}")
                return []
            
            # Read file
            with open(self.source_list_path, 'r', encoding='utf-8') as f:
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
            
            logger.info(f"Loaded {len(sources)} sources from {self.source_list_path}")
            return sources
        except Exception as e:
            logger.error(f"Error loading sources from local file: {str(e)}")
            return []
