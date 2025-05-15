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
    
    async def save_sources(self, sources: List[Source]) -> bool:
        """
        Save sources to a local YAML file.
        
        Args:
            sources: List of sources to save.
            
        Returns:
            True if successful, False otherwise.
        """
        try:
            # Convert sources to dict
            sources_dict = [source.dict() for source in sources]
            
            # Convert enum values to strings
            for source in sources_dict:
                source['type'] = source['type'].value
            
            # Write to file
            with open(self.source_list_path, 'w', encoding='utf-8') as f:
                yaml.dump(sources_dict, f, default_flow_style=False)
            
            logger.info(f"Saved {len(sources)} sources to {self.source_list_path}")
            return True
        except Exception as e:
            logger.error(f"Error saving sources to local file: {str(e)}")
            return False
    
    async def load_sources(self) -> List[Source]:
        """
        Load sources from a local YAML file.
        
        Returns:
            List of sources loaded from the file.
        """
        try:
            # Check if file exists
            if not self.source_list_path.exists():
                logger.warning(f"No source list found at {self.source_list_path}")
                return []
            
            # Read file
            with open(self.source_list_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
            
            if not data:
                return []
            
            # Convert to Source objects
            sources = []
            for item in data:
                # Convert string to enum
                if 'type' in item and isinstance(item['type'], str):
                    item['type'] = SourceType(item['type'])
                
                sources.append(Source(**item))
            
            logger.info(f"Loaded {len(sources)} sources from {self.source_list_path}")
            return sources
        except Exception as e:
            logger.error(f"Error loading sources from local file: {str(e)}")
            return []

