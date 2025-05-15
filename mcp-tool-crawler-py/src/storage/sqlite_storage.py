"""
SQLite storage service for MCP tools and sources.
"""

import json
import yaml
import sqlite3
import os
from pathlib import Path
from typing import List, Dict, Any, Optional, Union
from datetime import datetime

from ..models import MCPTool, Source, SourceType
from ..utils.logging import get_logger
from ..utils.config import get_config
from ..utils.helpers import is_github_repo, extract_domain

logger = get_logger(__name__)
config = get_config()


class SQLiteStorage:
    """
    SQLite storage service for MCP tools.
    """
    
    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize the SQLite storage service.
        
        Args:
            db_path: Path to the SQLite database file. If None, uses the value from config.
        """
        self.db_path = db_path or config['storage']['sqlite']['db_path']
        self._ensure_db_exists()
    
    def _ensure_db_exists(self):
        """
        Ensure the database file and tables exist.
        """
        # Ensure directory exists
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        # Connect to database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create tools table if it doesn't exist
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS tools (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            description TEXT NOT NULL,
            url TEXT NOT NULL,
            source_url TEXT NOT NULL,
            first_discovered TEXT NOT NULL,
            last_updated TEXT NOT NULL,
            metadata TEXT NOT NULL
        )
        ''')
        
        conn.commit()
        conn.close()
        
        logger.info(f"Ensured SQLite database exists at {self.db_path}")
    
    async def save_tools(self, tools: List[MCPTool]) -> bool:
        """
        Save tools to SQLite.
        
        Args:
            tools: List of tools to save.
            
        Returns:
            True if successful, False otherwise.
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            for tool in tools:
                tool_dict = tool.dict()
                metadata_json = json.dumps(tool_dict.get('metadata', {}))
                
                # Check if tool already exists
                cursor.execute('SELECT id FROM tools WHERE id = ?', (tool.id,))
                existing = cursor.fetchone()
                
                if existing:
                    # Update existing tool
                    cursor.execute('''
                    UPDATE tools
                    SET name = ?, description = ?, url = ?, source_url = ?,
                        last_updated = ?, metadata = ?
                    WHERE id = ?
                    ''', (
                        tool.name, tool.description, tool.url, tool.source_url,
                        tool.last_updated, metadata_json, tool.id
                    ))
                else:
                    # Insert new tool
                    cursor.execute('''
                    INSERT INTO tools (id, name, description, url, source_url,
                                      first_discovered, last_updated, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        tool.id, tool.name, tool.description, tool.url, tool.source_url,
                        tool.first_discovered, tool.last_updated, metadata_json
                    ))
            
            conn.commit()
            conn.close()
            
            logger.info(f"Saved {len(tools)} tools to SQLite database")
            return True
        except Exception as e:
            logger.error(f"Error saving tools to SQLite: {str(e)}")
            return False
    
    async def load_tools(self) -> List[MCPTool]:
        """
        Load tools from SQLite.
        
        Returns:
            List of tools loaded from SQLite.
        """
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('SELECT * FROM tools')
            rows = cursor.fetchall()
            
            tools = []
            for row in rows:
                row_dict = dict(row)
                # Parse metadata JSON
                row_dict['metadata'] = json.loads(row_dict['metadata'])
                tools.append(MCPTool(**row_dict))
            
            conn.close()
            
            logger.info(f"Loaded {len(tools)} tools from SQLite database")
            return tools
        except Exception as e:
            logger.error(f"Error loading tools from SQLite: {str(e)}")
            return []


class SQLiteSourceStorage:
    """
    SQLite storage service for source lists.
    """
    
    def __init__(self, db_path: Optional[str] = None, sources_file_path: Optional[str] = None):
        """
        Initialize the SQLite source storage service.
        
        Args:
            db_path: Path to the SQLite database file. If None, uses the value from config.
            sources_file_path: Path to the sources YAML file. If None, uses the value from config.
        """
        self.db_path = db_path or config['storage']['sqlite']['db_path']
        self.sources_file_path = sources_file_path or config['storage']['local']['sources_file_path']
        self._ensure_db_exists()
    
    def _ensure_db_exists(self):
        """
        Ensure the database file and tables exist.
        """
        # Ensure directory exists
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        # Connect to database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create sources table if it doesn't exist
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
            metadata TEXT NOT NULL
        )
        ''')
        
        conn.commit()
        conn.close()
        
        logger.info(f"Ensured SQLite database exists at {self.db_path}")
    
    async def save_sources(self, sources: List[Source]) -> bool:
        """
        Save sources to SQLite and optionally to a YAML file.
        
        Args:
            sources: List of sources to save.
            
        Returns:
            True if successful, False otherwise.
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            for source in sources:
                source_dict = source.dict()
                metadata_json = json.dumps(source_dict.get('metadata', {}))
                
                # Check if source already exists
                cursor.execute('SELECT id FROM sources WHERE id = ?', (source.id,))
                existing = cursor.fetchone()
                
                if existing:
                    # Update existing source
                    cursor.execute('''
                    UPDATE sources
                    SET url = ?, name = ?, type = ?, has_known_crawler = ?,
                        crawler_id = ?, last_crawled = ?, last_crawl_status = ?, metadata = ?
                    WHERE id = ?
                    ''', (
                        source.url, source.name, source.type.value, 
                        1 if source.has_known_crawler else 0,
                        source.crawler_id, source.last_crawled, source.last_crawl_status,
                        metadata_json, source.id
                    ))
                else:
                    # Insert new source
                    cursor.execute('''
                    INSERT INTO sources (id, url, name, type, has_known_crawler,
                                        crawler_id, last_crawled, last_crawl_status, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        source.id, source.url, source.name, source.type.value,
                        1 if source.has_known_crawler else 0,
                        source.crawler_id, source.last_crawled, source.last_crawl_status,
                        metadata_json
                    ))
            
            conn.commit()
            conn.close()
            
            # Also save to YAML file if configured
            if self.sources_file_path:
                # Ensure directory exists
                os.makedirs(os.path.dirname(self.sources_file_path), exist_ok=True)
                
                # Convert sources to dict for YAML
                sources_data = {
                    'sources': [
                        {
                            'url': source.url,
                            'name': source.name,
                            'type': source.type.value
                        }
                        for source in sources
                    ]
                }
                
                # Write to YAML file
                with open(self.sources_file_path, 'w', encoding='utf-8') as f:
                    yaml.dump(sources_data, f, default_flow_style=False)
                
                logger.info(f"Saved {len(sources)} sources to YAML file: {self.sources_file_path}")
            
            logger.info(f"Saved {len(sources)} sources to SQLite database")
            return True
        except Exception as e:
            logger.error(f"Error saving sources to SQLite: {str(e)}")
            return False
    
    async def load_sources(self) -> List[Source]:
        """
        Load sources from SQLite or YAML file.
        
        Returns:
            List of Source objects.
        """
        # Try loading from SQLite first
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('SELECT * FROM sources')
            rows = cursor.fetchall()
            
            if rows:
                sources = []
                for row in rows:
                    row_dict = dict(row)
                    # Convert has_known_crawler from integer to boolean
                    row_dict['has_known_crawler'] = bool(row_dict['has_known_crawler'])
                    # Parse metadata JSON
                    row_dict['metadata'] = json.loads(row_dict['metadata'])
                    # Convert type string to enum
                    row_dict['type'] = SourceType(row_dict['type'])
                    sources.append(Source(**row_dict))
                
                conn.close()
                logger.info(f"Loaded {len(sources)} sources from SQLite database")
                return sources
        except Exception as e:
            logger.warning(f"Error loading sources from SQLite: {str(e)}")
        
        # If SQLite failed or returned no sources, try loading from YAML file
        try:
            if os.path.exists(self.sources_file_path):
                with open(self.sources_file_path, 'r', encoding='utf-8') as f:
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
                
                logger.info(f"Loaded {len(sources)} sources from YAML file: {self.sources_file_path}")
                
                # Save to SQLite for future use
                await self.save_sources(sources)
                
                return sources
        except Exception as e:
            logger.error(f"Error loading sources from YAML file: {str(e)}")
        
        # If all else fails, return empty list
        return []
"""

