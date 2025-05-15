"""
SQLite storage service for MCP tools and sources.
"""

import json
import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Any, Optional, Union

from ..models import MCPTool, Source, SourceType
from ..utils.logging import get_logger

logger = get_logger(__name__)


class SQLiteStorage:
    """
    SQLite storage service for MCP tools and sources.
    """
    
    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize the SQLite storage service.
        
        Args:
            db_path: Path to the SQLite database file. If None, uses the default path.
        """
        if db_path:
            self.db_path = Path(db_path)
        else:
            self.db_path = Path(__file__).parents[3] / 'data' / 'mcp_crawler.db'
        
        # Ensure data directory exists
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize database
        self._init_db()
    
    def _init_db(self):
        """
        Initialize the database schema if it doesn't exist.
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create tools table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS tools (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            description TEXT,
            url TEXT,
            source_url TEXT,
            source_id TEXT,
            created_at TEXT,
            updated_at TEXT,
            metadata TEXT
        )
        ''')
        
        # Create sources table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS sources (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            url TEXT NOT NULL,
            type TEXT NOT NULL,
            has_known_crawler INTEGER,
            last_crawled TEXT,
            last_crawl_status TEXT,
            created_at TEXT,
            updated_at TEXT,
            metadata TEXT
        )
        ''')
        
        conn.commit()
        conn.close()
        
        logger.info(f"Initialized SQLite database at {self.db_path}")
    
    async def save_tools(self, tools: List[MCPTool]) -> bool:
        """
        Save tools to the SQLite database.
        
        Args:
            tools: List of tools to save.
            
        Returns:
            True if successful, False otherwise.
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Prepare data for batch insert/update
            for tool in tools:
                tool_dict = tool.dict()
                
                # Convert metadata to JSON string
                if tool_dict.get('metadata'):
                    tool_dict['metadata'] = json.dumps(tool_dict['metadata'])
                
                # Check if tool exists
                cursor.execute('SELECT id FROM tools WHERE id = ?', (tool_dict['id'],))
                exists = cursor.fetchone()
                
                if exists:
                    # Update existing tool
                    tool_dict['updated_at'] = datetime.now(timezone.utc).isoformat()
                    
                    cursor.execute('''
                    UPDATE tools SET
                        name = ?,
                        description = ?,
                        url = ?,
                        source_url = ?,
                        source_id = ?,
                        updated_at = ?,
                        metadata = ?
                    WHERE id = ?
                    ''', (
                        tool_dict['name'],
                        tool_dict.get('description', ''),
                        tool_dict.get('url', ''),
                        tool_dict.get('source_url', ''),
                        tool_dict.get('source_id', ''),
                        tool_dict['updated_at'],
                        tool_dict.get('metadata', ''),
                        tool_dict['id']
                    ))
                else:
                    # Insert new tool
                    tool_dict['created_at'] = datetime.now(timezone.utc).isoformat()
                    tool_dict['updated_at'] = tool_dict['created_at']
                    
                    cursor.execute('''
                    INSERT INTO tools (
                        id, name, description, url, source_url, source_id,
                        created_at, updated_at, metadata
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        tool_dict['id'],
                        tool_dict['name'],
                        tool_dict.get('description', ''),
                        tool_dict.get('url', ''),
                        tool_dict.get('source_url', ''),
                        tool_dict.get('source_id', ''),
                        tool_dict['created_at'],
                        tool_dict['updated_at'],
                        tool_dict.get('metadata', '')
                    ))
            
            conn.commit()
            conn.close()
            
            logger.info(f"Saved {len(tools)} tools to SQLite database")
            return True
        except Exception as e:
            logger.error(f"Error saving tools to SQLite database: {str(e)}")
            return False
    
    async def load_tools(self) -> List[MCPTool]:
        """
        Load tools from the SQLite database.
        
        Returns:
            List of tools loaded from the database.
        """
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('SELECT * FROM tools')
            rows = cursor.fetchall()
            
            tools = []
            for row in rows:
                tool_dict = dict(row)
                
                # Parse metadata JSON
                if tool_dict.get('metadata'):
                    try:
                        tool_dict['metadata'] = json.loads(tool_dict['metadata'])
                    except:
                        tool_dict['metadata'] = {}
                
                tools.append(MCPTool(**tool_dict))
            
            conn.close()
            
            logger.info(f"Loaded {len(tools)} tools from SQLite database")
            return tools
        except Exception as e:
            logger.error(f"Error loading tools from SQLite database: {str(e)}")
            return []
    
    async def save_sources(self, sources: List[Source]) -> bool:
        """
        Save sources to the SQLite database.
        
        Args:
            sources: List of sources to save.
            
        Returns:
            True if successful, False otherwise.
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Prepare data for batch insert/update
            for source in sources:
                source_dict = source.dict()
                
                # Convert type to string
                source_dict['type'] = source_dict['type'].value
                
                # Convert boolean to integer
                source_dict['has_known_crawler'] = 1 if source_dict.get('has_known_crawler') else 0
                
                # Convert metadata to JSON string
                if source_dict.get('metadata'):
                    source_dict['metadata'] = json.dumps(source_dict['metadata'])
                
                # Check if source exists
                cursor.execute('SELECT id FROM sources WHERE id = ?', (source_dict['id'],))
                exists = cursor.fetchone()
                
                if exists:
                    # Update existing source
                    source_dict['updated_at'] = datetime.now(timezone.utc).isoformat()
                    
                    cursor.execute('''
                    UPDATE sources SET
                        name = ?,
                        url = ?,
                        type = ?,
                        has_known_crawler = ?,
                        last_crawled = ?,
                        last_crawl_status = ?,
                        updated_at = ?,
                        metadata = ?
                    WHERE id = ?
                    ''', (
                        source_dict['name'],
                        source_dict['url'],
                        source_dict['type'],
                        source_dict['has_known_crawler'],
                        source_dict.get('last_crawled', ''),
                        source_dict.get('last_crawl_status', ''),
                        source_dict['updated_at'],
                        source_dict.get('metadata', ''),
                        source_dict['id']
                    ))
                else:
                    # Insert new source
                    source_dict['created_at'] = datetime.now(timezone.utc).isoformat()
                    source_dict['updated_at'] = source_dict['created_at']
                    
                    cursor.execute('''
                    INSERT INTO sources (
                        id, name, url, type, has_known_crawler, last_crawled,
                        last_crawl_status, created_at, updated_at, metadata
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        source_dict['id'],
                        source_dict['name'],
                        source_dict['url'],
                        source_dict['type'],
                        source_dict['has_known_crawler'],
                        source_dict.get('last_crawled', ''),
                        source_dict.get('last_crawl_status', ''),
                        source_dict['created_at'],
                        source_dict['updated_at'],
                        source_dict.get('metadata', '')
                    ))
            
            conn.commit()
            conn.close()
            
            logger.info(f"Saved {len(sources)} sources to SQLite database")
            return True
        except Exception as e:
            logger.error(f"Error saving sources to SQLite database: {str(e)}")
            return False
    
    async def load_sources(self) -> List[Source]:
        """
        Load sources from the SQLite database.
        
        Returns:
            List of sources loaded from the database.
        """
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('SELECT * FROM sources')
            rows = cursor.fetchall()
            
            sources = []
            for row in rows:
                source_dict = dict(row)
                
                # Convert string to enum
                source_dict['type'] = SourceType(source_dict['type'])
                
                # Convert integer to boolean
                source_dict['has_known_crawler'] = bool(source_dict['has_known_crawler'])
                
                # Parse metadata JSON
                if source_dict.get('metadata'):
                    try:
                        source_dict['metadata'] = json.loads(source_dict['metadata'])
                    except:
                        source_dict['metadata'] = {}
                
                sources.append(Source(**source_dict))
            
            conn.close()
            
            logger.info(f"Loaded {len(sources)} sources from SQLite database")
            return sources
        except Exception as e:
            logger.error(f"Error loading sources from SQLite database: {str(e)}")
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
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Calculate threshold timestamp
            threshold_time = (datetime.now(timezone.utc) - 
                             timedelta(hours=time_threshold_hours)).isoformat()
            
            # Get sources that have never been crawled or were crawled before the threshold
            cursor.execute('''
            SELECT * FROM sources 
            WHERE last_crawled IS NULL OR last_crawled < ?
            ''', (threshold_time,))
            
            rows = cursor.fetchall()
            
            sources = []
            for row in rows:
                source_dict = dict(row)
                
                # Convert string to enum
                source_dict['type'] = SourceType(source_dict['type'])
                
                # Convert integer to boolean
                source_dict['has_known_crawler'] = bool(source_dict['has_known_crawler'])
                
                # Parse metadata JSON
                if source_dict.get('metadata'):
                    try:
                        source_dict['metadata'] = json.loads(source_dict['metadata'])
                    except:
                        source_dict['metadata'] = {}
                
                sources.append(Source(**source_dict))
            
            conn.close()
            
            logger.info(f"Found {len(sources)} sources to crawl")
            return sources
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
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Update source
            cursor.execute('''
            UPDATE sources SET
                last_crawled = ?,
                last_crawl_status = ?
            WHERE id = ?
            ''', (
                datetime.now(timezone.utc).isoformat(),
                'success' if success else 'failed',
                source_id
            ))
            
            conn.commit()
            conn.close()
            
            logger.info(f"Updated last crawl for source {source_id}")
            return True
        except Exception as e:
            logger.error(f"Error updating source last crawl: {str(e)}")
            return False

