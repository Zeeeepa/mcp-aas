"""
Local file storage service for MCP tools and sources.
"""

import json
import os
import yaml
import shutil
import time
import fcntl
from pathlib import Path
from typing import List, Dict, Any, Optional, Union

from ..models import MCPTool, Source, SourceType
from ..utils.logging import get_logger
from ..utils.config import get_config
from ..utils.helpers import is_github_repo, extract_domain

logger = get_logger(__name__)
config = get_config()


class LocalStorage:
    """
    Local file storage service for MCP tools.
    Provides functionality similar to S3Storage but using the local filesystem.
    """
    
    def __init__(self, file_path: Optional[str] = None):
        """
        Initialize the local storage service.
        
        Args:
            file_path: Path to the file to store tools in. If None, uses the default path.
        """
        if file_path:
            self.file_path = Path(file_path)
        else:
            self.file_path = Path(__file__).parents[3] / 'data' / 'tools.json'
        
        # Ensure data directory exists
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Directory for versioned backups
        self.backup_dir = self.file_path.parent / 'backups' / 'tools'
        self.backup_dir.mkdir(parents=True, exist_ok=True)
    
    async def save_tools(self, tools: List[MCPTool]) -> bool:
        """
        Save tools to a local file with file locking for concurrent access.
        Also creates a versioned backup.
        
        Args:
            tools: List of tools to save.
            
        Returns:
            True if successful, False otherwise.
        """
        try:
            # Convert tools to JSON
            tools_json = [tool.dict() for tool in tools]
            
            # Create a temporary file
            temp_file = self.file_path.with_suffix('.tmp')
            
            # Write to temporary file
            with open(temp_file, 'w', encoding='utf-8') as f:
                # Acquire an exclusive lock
                fcntl.flock(f, fcntl.LOCK_EX)
                try:
                    json.dump(tools_json, f, indent=2)
                    f.flush()
                    os.fsync(f.fileno())  # Ensure data is written to disk
                finally:
                    # Release the lock
                    fcntl.flock(f, fcntl.LOCK_UN)
            
            # Create a backup before replacing the file
            if self.file_path.exists():
                timestamp = int(time.time())
                backup_path = self.backup_dir / f"tools_{timestamp}.json"
                shutil.copy2(self.file_path, backup_path)
                logger.debug(f"Created backup at {backup_path}")
            
            # Atomically replace the original file
            os.replace(temp_file, self.file_path)
            
            logger.info(f"Saved {len(tools)} tools to {self.file_path}")
            return True
        except Exception as e:
            logger.error(f"Error saving tools to local file: {str(e)}")
            # Clean up temporary file if it exists
            if 'temp_file' in locals() and temp_file.exists():
                temp_file.unlink()
            return False
    
    async def load_tools(self) -> List[MCPTool]:
        """
        Load tools from a local file with file locking for concurrent access.
        
        Returns:
            List of tools loaded from the file.
        """
        try:
            # Check if file exists
            if not self.file_path.exists():
                logger.warning(f"No tool catalog found at {self.file_path}")
                return []
            
            # Read file with shared lock
            with open(self.file_path, 'r', encoding='utf-8') as f:
                # Acquire a shared lock
                fcntl.flock(f, fcntl.LOCK_SH)
                try:
                    data = json.load(f)
                finally:
                    # Release the lock
                    fcntl.flock(f, fcntl.LOCK_UN)
            
            # Convert to MCPTool objects
            tools = [MCPTool(**item) for item in data]
            
            logger.info(f"Loaded {len(tools)} tools from {self.file_path}")
            return tools
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error loading tools from {self.file_path}: {str(e)}")
            # Try to recover from backup
            return await self._recover_from_backup()
        except Exception as e:
            logger.error(f"Error loading tools from local file: {str(e)}")
            return []
    
    async def _recover_from_backup(self) -> List[MCPTool]:
        """
        Attempt to recover tools from the most recent backup.
        
        Returns:
            List of tools loaded from the backup, or empty list if recovery failed.
        """
        try:
            # Find the most recent backup
            backup_files = list(self.backup_dir.glob("tools_*.json"))
            if not backup_files:
                logger.warning("No backup files found for recovery")
                return []
            
            # Sort by modification time (most recent first)
            backup_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
            latest_backup = backup_files[0]
            
            logger.info(f"Attempting recovery from backup: {latest_backup}")
            
            # Read the backup file
            with open(latest_backup, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Convert to MCPTool objects
            tools = [MCPTool(**item) for item in data]
            
            # Restore the backup to the main file
            shutil.copy2(latest_backup, self.file_path)
            
            logger.info(f"Successfully recovered {len(tools)} tools from backup")
            return tools
        except Exception as e:
            logger.error(f"Error recovering from backup: {str(e)}")
            return []


class LocalSourceStorage:
    """
    Local storage service for source lists.
    Provides functionality similar to S3SourceStorage but using the local filesystem.
    """
    
    def __init__(self, file_path: Optional[str] = None):
        """
        Initialize the local source storage service.
        
        Args:
            file_path: Path to the file to store sources in. If None, uses the default path.
        """
        if file_path:
            self.file_path = Path(file_path)
        else:
            sources_key = config['aws']['s3']['source_list_key']
            self.file_path = Path(__file__).parents[3] / 'data' / sources_key
        
        # Ensure data directory exists
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Directory for versioned backups
        self.backup_dir = self.file_path.parent / 'backups' / 'sources'
        self.backup_dir.mkdir(parents=True, exist_ok=True)
    
    async def load_sources(self) -> List[Source]:
        """
        Load sources from local YAML file.
        
        Returns:
            List of Source objects loaded from the file.
        """
        try:
            # Check if file exists
            if not self.file_path.exists():
                logger.warning(f"No source list found at {self.file_path}")
                return []
            
            # Read file with shared lock
            with open(self.file_path, 'r', encoding='utf-8') as f:
                # Acquire a shared lock
                fcntl.flock(f, fcntl.LOCK_SH)
                try:
                    content = f.read()
                finally:
                    # Release the lock
                    fcntl.flock(f, fcntl.LOCK_UN)
            
            # Parse YAML
            data = yaml.safe_load(content)
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
        except yaml.YAMLError as e:
            logger.error(f"YAML parse error loading sources from {self.file_path}: {str(e)}")
            # Try to recover from backup
            return await self._recover_from_backup()
        except Exception as e:
            logger.error(f"Error loading sources from local file: {str(e)}")
            return []
    
    async def save_sources(self, sources: List[Source]) -> bool:
        """
        Save sources to a local YAML file with file locking for concurrent access.
        Also creates a versioned backup.
        
        Args:
            sources: List of sources to save.
            
        Returns:
            True if successful, False otherwise.
        """
        try:
            # Convert sources to dict for YAML
            sources_data = [source.dict() for source in sources]
            yaml_data = {'sources': sources_data}
            
            # Create a temporary file
            temp_file = self.file_path.with_suffix('.tmp')
            
            # Write to temporary file
            with open(temp_file, 'w', encoding='utf-8') as f:
                # Acquire an exclusive lock
                fcntl.flock(f, fcntl.LOCK_EX)
                try:
                    yaml.dump(yaml_data, f, default_flow_style=False)
                    f.flush()
                    os.fsync(f.fileno())  # Ensure data is written to disk
                finally:
                    # Release the lock
                    fcntl.flock(f, fcntl.LOCK_UN)
            
            # Create a backup before replacing the file
            if self.file_path.exists():
                timestamp = int(time.time())
                backup_path = self.backup_dir / f"sources_{timestamp}.yaml"
                shutil.copy2(self.file_path, backup_path)
                logger.debug(f"Created backup at {backup_path}")
            
            # Atomically replace the original file
            os.replace(temp_file, self.file_path)
            
            logger.info(f"Saved {len(sources)} sources to {self.file_path}")
            return True
        except Exception as e:
            logger.error(f"Error saving sources to local file: {str(e)}")
            # Clean up temporary file if it exists
            if 'temp_file' in locals() and temp_file.exists():
                temp_file.unlink()
            return False
    
    async def _recover_from_backup(self) -> List[Source]:
        """
        Attempt to recover sources from the most recent backup.
        
        Returns:
            List of sources loaded from the backup, or empty list if recovery failed.
        """
        try:
            # Find the most recent backup
            backup_files = list(self.backup_dir.glob("sources_*.yaml"))
            if not backup_files:
                logger.warning("No backup files found for recovery")
                return []
            
            # Sort by modification time (most recent first)
            backup_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
            latest_backup = backup_files[0]
            
            logger.info(f"Attempting recovery from backup: {latest_backup}")
            
            # Read the backup file
            with open(latest_backup, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
            
            sources_data = data.get('sources', [])
            sources = [Source(**item) for item in sources_data]
            
            # Restore the backup to the main file
            shutil.copy2(latest_backup, self.file_path)
            
            logger.info(f"Successfully recovered {len(sources)} sources from backup")
            return sources
        except Exception as e:
            logger.error(f"Error recovering from backup: {str(e)}")
            return []
