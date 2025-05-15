"""
Consolidated storage module for MCP tools.
Combines functionality from multiple storage modules into a single file.
"""

import os
import json
import sqlite3
import yaml
from typing import List, Dict, Any, Optional
from pathlib import Path
from datetime import datetime

from .models import MCPTool, Source, SourceType
from .utils.logging import get_logger

logger = get_logger(__name__)


class BaseStorage:
    """Base class for all storage implementations."""
    
    def save_tool(self, tool: MCPTool) -> bool:
        """
        Save a tool to storage.
        
        Args:
            tool: The tool to save.
            
        Returns:
            True if the tool was saved successfully, False otherwise.
        """
        raise NotImplementedError("Subclasses must implement save_tool()")
    
    def get_tool(self, tool_id: str) -> Optional[MCPTool]:
        """
        Get a tool by ID.
        
        Args:
            tool_id: The ID of the tool to get.
            
        Returns:
            The tool if found, None otherwise.
        """
        raise NotImplementedError("Subclasses must implement get_tool()")
    
    def get_all_tools(self) -> List[MCPTool]:
        """
        Get all tools.
        
        Returns:
            A list of all tools.
        """
        raise NotImplementedError("Subclasses must implement get_all_tools()")
    
    def save_source(self, source: Source) -> bool:
        """
        Save a source to storage.
        
        Args:
            source: The source to save.
            
        Returns:
            True if the source was saved successfully, False otherwise.
        """
        raise NotImplementedError("Subclasses must implement save_source()")
    
    def get_source(self, source_id: str) -> Optional[Source]:
        """
        Get a source by ID.
        
        Args:
            source_id: The ID of the source to get.
            
        Returns:
            The source if found, None otherwise.
        """
        raise NotImplementedError("Subclasses must implement get_source()")
    
    def get_all_sources(self) -> List[Source]:
        """
        Get all sources.
        
        Returns:
            A list of all sources.
        """
        raise NotImplementedError("Subclasses must implement get_all_sources()")


class LocalStorage(BaseStorage):
    """Storage implementation using local JSON files."""
    
    def __init__(self, tools_file_path: str, sources_file_path: str):
        self.tools_file_path = Path(tools_file_path)
        self.sources_file_path = Path(sources_file_path)
        
        # Create parent directories if they don't exist
        self.tools_file_path.parent.mkdir(parents=True, exist_ok=True)
        self.sources_file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize files if they don't exist
        if not self.tools_file_path.exists():
            with open(self.tools_file_path, 'w') as f:
                json.dump([], f)
        
        if not self.sources_file_path.exists():
            with open(self.sources_file_path, 'w') as f:
                yaml.dump([], f)
    
    def save_tool(self, tool: MCPTool) -> bool:
        """
        Save a tool to the local JSON file.
        
        Args:
            tool: The tool to save.
            
        Returns:
            True if the tool was saved successfully, False otherwise.
        """
        try:
            # Load existing tools
            tools = self.get_all_tools()
            
            # Check if tool already exists
            existing_tool_index = next((i for i, t in enumerate(tools) if t.id == tool.id), None)
            
            if existing_tool_index is not None:
                # Update existing tool
                tools[existing_tool_index] = tool
            else:
                # Add new tool
                tools.append(tool)
            
            # Save tools
            with open(self.tools_file_path, 'w') as f:
                json.dump([t.model_dump() for t in tools], f, indent=2)
            
            return True
        except Exception as e:
            logger.error(f"Error saving tool: {str(e)}")
            return False
    
    def get_tool(self, tool_id: str) -> Optional[MCPTool]:
        """
        Get a tool by ID from the local JSON file.
        
        Args:
            tool_id: The ID of the tool to get.
            
        Returns:
            The tool if found, None otherwise.
        """
        tools = self.get_all_tools()
        return next((t for t in tools if t.id == tool_id), None)
    
    def get_all_tools(self) -> List[MCPTool]:
        """
        Get all tools from the local JSON file.
        
        Returns:
            A list of all tools.
        """
        try:
            with open(self.tools_file_path, 'r') as f:
                tools_data = json.load(f)
            
            return [MCPTool(**tool_data) for tool_data in tools_data]
        except Exception as e:
            logger.error(f"Error loading tools: {str(e)}")
            return []
    
    def save_source(self, source: Source) -> bool:
        """
        Save a source to the local YAML file.
        
        Args:
            source: The source to save.
            
        Returns:
            True if the source was saved successfully, False otherwise.
        """
        try:
            # Load existing sources
            sources = self.get_all_sources()
            
            # Check if source already exists
            existing_source_index = next((i for i, s in enumerate(sources) if s.id == source.id), None)
            
            if existing_source_index is not None:
                # Update existing source
                sources[existing_source_index] = source
            else:
                # Add new source
                sources.append(source)
            
            # Save sources
            with open(self.sources_file_path, 'w') as f:
                yaml.dump([s.model_dump() for s in sources], f)
            
            return True
        except Exception as e:
            logger.error(f"Error saving source: {str(e)}")
            return False
    
    def get_source(self, source_id: str) -> Optional[Source]:
        """
        Get a source by ID from the local YAML file.
        
        Args:
            source_id: The ID of the source to get.
            
        Returns:
            The source if found, None otherwise.
        """
        sources = self.get_all_sources()
        return next((s for s in sources if s.id == source_id), None)
    
    def get_all_sources(self) -> List[Source]:
        """
        Get all sources from the local YAML file.
        
        Returns:
            A list of all sources.
        """
        try:
            with open(self.sources_file_path, 'r') as f:
                sources_data = yaml.safe_load(f) or []
            
            return [Source(**source_data) for source_data in sources_data]
        except Exception as e:
            logger.error(f"Error loading sources: {str(e)}")
            return []


class SQLiteStorage(BaseStorage):
    """Storage implementation using SQLite database."""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        
        # Create parent directory if it doesn't exist
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize database
        self._init_db()
    
    def _init_db(self):
        """Initialize the database schema."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create tools table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS tools (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            description TEXT NOT NULL,
            url TEXT NOT NULL,
            source_url TEXT NOT NULL,
            first_discovered TEXT NOT NULL,
            last_updated TEXT NOT NULL,
            metadata TEXT
        )
        ''')
        
        # Create sources table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS sources (
            id TEXT PRIMARY KEY,
            url TEXT NOT NULL,
            name TEXT NOT NULL,
            type TEXT NOT NULL,
            has_known_crawler INTEGER NOT NULL,
            crawler_id TEXT,
            last_crawled TEXT,
            last_crawl_status TEXT,
            metadata TEXT
        )
        ''')
        
        conn.commit()
        conn.close()
    
    def save_tool(self, tool: MCPTool) -> bool:
        """
        Save a tool to the SQLite database.
        
        Args:
            tool: The tool to save.
            
        Returns:
            True if the tool was saved successfully, False otherwise.
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Check if tool already exists
            cursor.execute('SELECT id FROM tools WHERE id = ?', (tool.id,))
            existing_tool = cursor.fetchone()
            
            if existing_tool:
                # Update existing tool
                cursor.execute('''
                UPDATE tools
                SET name = ?, description = ?, url = ?, source_url = ?,
                    first_discovered = ?, last_updated = ?, metadata = ?
                WHERE id = ?
                ''', (
                    tool.name,
                    tool.description,
                    tool.url,
                    tool.source_url,
                    tool.first_discovered,
                    tool.last_updated,
                    json.dumps(tool.metadata),
                    tool.id
                ))
            else:
                # Insert new tool
                cursor.execute('''
                INSERT INTO tools (id, name, description, url, source_url,
                                  first_discovered, last_updated, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    tool.id,
                    tool.name,
                    tool.description,
                    tool.url,
                    tool.source_url,
                    tool.first_discovered,
                    tool.last_updated,
                    json.dumps(tool.metadata)
                ))
            
            conn.commit()
            conn.close()
            
            return True
        except Exception as e:
            logger.error(f"Error saving tool to SQLite: {str(e)}")
            return False
    
    def get_tool(self, tool_id: str) -> Optional[MCPTool]:
        """
        Get a tool by ID from the SQLite database.
        
        Args:
            tool_id: The ID of the tool to get.
            
        Returns:
            The tool if found, None otherwise.
        """
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('SELECT * FROM tools WHERE id = ?', (tool_id,))
            row = cursor.fetchone()
            
            conn.close()
            
            if row:
                return MCPTool(
                    id=row['id'],
                    name=row['name'],
                    description=row['description'],
                    url=row['url'],
                    source_url=row['source_url'],
                    first_discovered=row['first_discovered'],
                    last_updated=row['last_updated'],
                    metadata=json.loads(row['metadata']) if row['metadata'] else {}
                )
            
            return None
        except Exception as e:
            logger.error(f"Error getting tool from SQLite: {str(e)}")
            return None
    
    def get_all_tools(self) -> List[MCPTool]:
        """
        Get all tools from the SQLite database.
        
        Returns:
            A list of all tools.
        """
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('SELECT * FROM tools')
            rows = cursor.fetchall()
            
            conn.close()
            
            return [
                MCPTool(
                    id=row['id'],
                    name=row['name'],
                    description=row['description'],
                    url=row['url'],
                    source_url=row['source_url'],
                    first_discovered=row['first_discovered'],
                    last_updated=row['last_updated'],
                    metadata=json.loads(row['metadata']) if row['metadata'] else {}
                )
                for row in rows
            ]
        except Exception as e:
            logger.error(f"Error getting all tools from SQLite: {str(e)}")
            return []
    
    def save_source(self, source: Source) -> bool:
        """
        Save a source to the SQLite database.
        
        Args:
            source: The source to save.
            
        Returns:
            True if the source was saved successfully, False otherwise.
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Check if source already exists
            cursor.execute('SELECT id FROM sources WHERE id = ?', (source.id,))
            existing_source = cursor.fetchone()
            
            if existing_source:
                # Update existing source
                cursor.execute('''
                UPDATE sources
                SET url = ?, name = ?, type = ?, has_known_crawler = ?,
                    crawler_id = ?, last_crawled = ?, last_crawl_status = ?, metadata = ?
                WHERE id = ?
                ''', (
                    source.url,
                    source.name,
                    source.type.value,
                    1 if source.has_known_crawler else 0,
                    source.crawler_id,
                    source.last_crawled,
                    source.last_crawl_status,
                    json.dumps(source.metadata),
                    source.id
                ))
            else:
                # Insert new source
                cursor.execute('''
                INSERT INTO sources (id, url, name, type, has_known_crawler,
                                    crawler_id, last_crawled, last_crawl_status, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    source.id,
                    source.url,
                    source.name,
                    source.type.value,
                    1 if source.has_known_crawler else 0,
                    source.crawler_id,
                    source.last_crawled,
                    source.last_crawl_status,
                    json.dumps(source.metadata)
                ))
            
            conn.commit()
            conn.close()
            
            return True
        except Exception as e:
            logger.error(f"Error saving source to SQLite: {str(e)}")
            return False
    
    def get_source(self, source_id: str) -> Optional[Source]:
        """
        Get a source by ID from the SQLite database.
        
        Args:
            source_id: The ID of the source to get.
            
        Returns:
            The source if found, None otherwise.
        """
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('SELECT * FROM sources WHERE id = ?', (source_id,))
            row = cursor.fetchone()
            
            conn.close()
            
            if row:
                return Source(
                    id=row['id'],
                    url=row['url'],
                    name=row['name'],
                    type=SourceType(row['type']),
                    has_known_crawler=bool(row['has_known_crawler']),
                    crawler_id=row['crawler_id'],
                    last_crawled=row['last_crawled'],
                    last_crawl_status=row['last_crawl_status'],
                    metadata=json.loads(row['metadata']) if row['metadata'] else {}
                )
            
            return None
        except Exception as e:
            logger.error(f"Error getting source from SQLite: {str(e)}")
            return None
    
    def get_all_sources(self) -> List[Source]:
        """
        Get all sources from the SQLite database.
        
        Returns:
            A list of all sources.
        """
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('SELECT * FROM sources')
            rows = cursor.fetchall()
            
            conn.close()
            
            return [
                Source(
                    id=row['id'],
                    url=row['url'],
                    name=row['name'],
                    type=SourceType(row['type']),
                    has_known_crawler=bool(row['has_known_crawler']),
                    crawler_id=row['crawler_id'],
                    last_crawled=row['last_crawled'],
                    last_crawl_status=row['last_crawl_status'],
                    metadata=json.loads(row['metadata']) if row['metadata'] else {}
                )
                for row in rows
            ]
        except Exception as e:
            logger.error(f"Error getting all sources from SQLite: {str(e)}")
            return []


class StorageFactory:
    """Factory for creating storage instances."""
    
    @staticmethod
    def create_storage(storage_type: str, **kwargs) -> BaseStorage:
        """
        Create a storage instance.
        
        Args:
            storage_type: The type of storage to create.
            **kwargs: Additional arguments to pass to the storage constructor.
            
        Returns:
            A storage instance.
            
        Raises:
            ValueError: If the storage type is not supported.
        """
        if storage_type == "local":
            return LocalStorage(
                tools_file_path=kwargs.get("tools_file_path"),
                sources_file_path=kwargs.get("sources_file_path")
            )
        elif storage_type == "sqlite":
            return SQLiteStorage(db_path=kwargs.get("db_path"))
        else:
            raise ValueError(f"Unsupported storage type: {storage_type}")

