"""
SQLite storage implementation for MCP tools and sources.
"""

import json
import sqlite3
import os
from pathlib import Path
from typing import List, Dict, Any, Optional, Union
from datetime import datetime

from ..models import MCPTool, Source, SourceType, CrawlerStrategy, CrawlResult
from ..utils.logging import get_logger

logger = get_logger(__name__)


class SQLiteStorage:
    """
    SQLite storage service for MCP tools, sources, and crawler strategies.
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
        self._initialize_db()
    
    def _initialize_db(self):
        """
        Initialize the SQLite database with required tables.
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Create sources table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS sources (
            id TEXT PRIMARY KEY,
            url TEXT NOT NULL,
            name TEXT NOT NULL,
            type TEXT NOT NULL,
            has_known_crawler BOOLEAN NOT NULL,
            crawler_id TEXT,
            last_crawled TEXT,
            last_crawl_status TEXT,
            metadata TEXT
        )
        ''')
        
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
        
        # Create crawler strategies table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS crawler_strategies (
            id TEXT PRIMARY KEY,
            source_id TEXT NOT NULL,
            source_type TEXT NOT NULL,
            implementation TEXT NOT NULL,
            description TEXT NOT NULL,
            created TEXT NOT NULL,
            last_modified TEXT NOT NULL
        )
        ''')
        
        # Create crawl results table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS crawl_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_id TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            success BOOLEAN NOT NULL,
            tools_discovered INTEGER NOT NULL,
            new_tools INTEGER NOT NULL,
            updated_tools INTEGER NOT NULL,
            duration INTEGER NOT NULL,
            error TEXT
        )
        ''')
        
        conn.commit()
        conn.close()
    
    def _get_connection(self):
        """
        Get a connection to the SQLite database.
        
        Returns:
            SQLite connection object.
        """
        return sqlite3.connect(self.db_path)
    
    # Source methods
    
    async def save_source(self, source: Source) -> bool:
        """
        Save a source to the database.
        
        Args:
            source: Source to save.
            
        Returns:
            True if successful, False otherwise.
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # Convert metadata to JSON string
            metadata_json = json.dumps(source.metadata) if source.metadata else '{}'
            
            # Insert or replace source
            cursor.execute('''
            INSERT OR REPLACE INTO sources
            (id, url, name, type, has_known_crawler, crawler_id, last_crawled, last_crawl_status, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                source.id,
                source.url,
                source.name,
                source.type.value,
                source.has_known_crawler,
                source.crawler_id,
                source.last_crawled,
                source.last_crawl_status,
                metadata_json
            ))
            
            conn.commit()
            conn.close()
            
            logger.info(f"Saved source to SQLite: {source.name} ({source.id})")
            return True
        except Exception as e:
            logger.error(f"Error saving source to SQLite: {str(e)}")
            return False
    
    async def get_source(self, source_id: str) -> Optional[Source]:
        """
        Get a source by ID.
        
        Args:
            source_id: ID of the source to get.
            
        Returns:
            Source object if found, None otherwise.
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute('SELECT * FROM sources WHERE id = ?', (source_id,))
            row = cursor.fetchone()
            
            if not row:
                return None
            
            # Convert row to Source object
            column_names = [description[0] for description in cursor.description]
            source_dict = dict(zip(column_names, row))
            
            # Parse metadata JSON
            if source_dict['metadata']:
                source_dict['metadata'] = json.loads(source_dict['metadata'])
            else:
                source_dict['metadata'] = {}
            
            # Convert type string to enum
            source_dict['type'] = SourceType(source_dict['type'])
            
            conn.close()
            
            return Source(**source_dict)
        except Exception as e:
            logger.error(f"Error getting source from SQLite: {str(e)}")
            return None
    
    async def get_all_sources(self) -> List[Source]:
        """
        Get all sources from the database.
        
        Returns:
            List of Source objects.
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute('SELECT * FROM sources')
            rows = cursor.fetchall()
            
            sources = []
            column_names = [description[0] for description in cursor.description]
            
            for row in rows:
                source_dict = dict(zip(column_names, row))
                
                # Parse metadata JSON
                if source_dict['metadata']:
                    source_dict['metadata'] = json.loads(source_dict['metadata'])
                else:
                    source_dict['metadata'] = {}
                
                # Convert type string to enum
                source_dict['type'] = SourceType(source_dict['type'])
                
                sources.append(Source(**source_dict))
            
            conn.close()
            
            logger.info(f"Retrieved {len(sources)} sources from SQLite")
            return sources
        except Exception as e:
            logger.error(f"Error getting sources from SQLite: {str(e)}")
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
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # Update source
            cursor.execute('''
            UPDATE sources
            SET last_crawled = ?, last_crawl_status = ?
            WHERE id = ?
            ''', (
                datetime.now().isoformat(),
                'success' if success else 'failed',
                source_id
            ))
            
            conn.commit()
            conn.close()
            
            logger.info(f"Updated last crawl for source {source_id}")
            return True
        except Exception as e:
            logger.error(f"Error updating source last crawl in SQLite: {str(e)}")
            return False
    
    # Tool methods
    
    async def save_tools(self, tools: List[MCPTool]) -> bool:
        """
        Save tools to the database.
        
        Args:
            tools: List of tools to save.
            
        Returns:
            True if successful, False otherwise.
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            for tool in tools:
                # Convert metadata to JSON string
                metadata_json = json.dumps(tool.metadata) if tool.metadata else '{}'
                
                # Insert or replace tool
                cursor.execute('''
                INSERT OR REPLACE INTO tools
                (id, name, description, url, source_url, first_discovered, last_updated, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    tool.id,
                    tool.name,
                    tool.description,
                    tool.url,
                    tool.source_url,
                    tool.first_discovered,
                    tool.last_updated,
                    metadata_json
                ))
            
            conn.commit()
            conn.close()
            
            logger.info(f"Saved {len(tools)} tools to SQLite")
            return True
        except Exception as e:
            logger.error(f"Error saving tools to SQLite: {str(e)}")
            return False
    
    async def load_tools(self) -> List[MCPTool]:
        """
        Load all tools from the database.
        
        Returns:
            List of MCPTool objects.
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute('SELECT * FROM tools')
            rows = cursor.fetchall()
            
            tools = []
            column_names = [description[0] for description in cursor.description]
            
            for row in rows:
                tool_dict = dict(zip(column_names, row))
                
                # Parse metadata JSON
                if tool_dict['metadata']:
                    tool_dict['metadata'] = json.loads(tool_dict['metadata'])
                else:
                    tool_dict['metadata'] = {}
                
                tools.append(MCPTool(**tool_dict))
            
            conn.close()
            
            logger.info(f"Loaded {len(tools)} tools from SQLite")
            return tools
        except Exception as e:
            logger.error(f"Error loading tools from SQLite: {str(e)}")
            return []
    
    # Crawler strategy methods
    
    async def save_crawler_strategy(self, strategy: CrawlerStrategy) -> bool:
        """
        Save a crawler strategy to the database.
        
        Args:
            strategy: CrawlerStrategy to save.
            
        Returns:
            True if successful, False otherwise.
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # Insert or replace strategy
            cursor.execute('''
            INSERT OR REPLACE INTO crawler_strategies
            (id, source_id, source_type, implementation, description, created, last_modified)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                strategy.id,
                strategy.source_id,
                strategy.source_type.value,
                strategy.implementation,
                strategy.description,
                strategy.created,
                strategy.last_modified
            ))
            
            conn.commit()
            conn.close()
            
            logger.info(f"Saved crawler strategy to SQLite: {strategy.id}")
            return True
        except Exception as e:
            logger.error(f"Error saving crawler strategy to SQLite: {str(e)}")
            return False
    
    async def get_crawler_strategy(self, strategy_id: str) -> Optional[CrawlerStrategy]:
        """
        Get a crawler strategy by ID.
        
        Args:
            strategy_id: ID of the strategy to get.
            
        Returns:
            CrawlerStrategy object if found, None otherwise.
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute('SELECT * FROM crawler_strategies WHERE id = ?', (strategy_id,))
            row = cursor.fetchone()
            
            if not row:
                return None
            
            # Convert row to CrawlerStrategy object
            column_names = [description[0] for description in cursor.description]
            strategy_dict = dict(zip(column_names, row))
            
            # Convert source_type string to enum
            strategy_dict['source_type'] = SourceType(strategy_dict['source_type'])
            
            conn.close()
            
            return CrawlerStrategy(**strategy_dict)
        except Exception as e:
            logger.error(f"Error getting crawler strategy from SQLite: {str(e)}")
            return None
    
    async def get_crawler_strategy_by_source(self, source_id: str) -> Optional[CrawlerStrategy]:
        """
        Get a crawler strategy by source ID.
        
        Args:
            source_id: ID of the source to get the strategy for.
            
        Returns:
            CrawlerStrategy object if found, None otherwise.
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute('SELECT * FROM crawler_strategies WHERE source_id = ?', (source_id,))
            row = cursor.fetchone()
            
            if not row:
                return None
            
            # Convert row to CrawlerStrategy object
            column_names = [description[0] for description in cursor.description]
            strategy_dict = dict(zip(column_names, row))
            
            # Convert source_type string to enum
            strategy_dict['source_type'] = SourceType(strategy_dict['source_type'])
            
            conn.close()
            
            return CrawlerStrategy(**strategy_dict)
        except Exception as e:
            logger.error(f"Error getting crawler strategy from SQLite: {str(e)}")
            return None
    
    # Crawl result methods
    
    async def save_crawl_result(self, result: CrawlResult) -> bool:
        """
        Save a crawl result to the database.
        
        Args:
            result: CrawlResult to save.
            
        Returns:
            True if successful, False otherwise.
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # Insert crawl result
            cursor.execute('''
            INSERT INTO crawl_results
            (source_id, timestamp, success, tools_discovered, new_tools, updated_tools, duration, error)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                result.source_id,
                result.timestamp,
                result.success,
                result.tools_discovered,
                result.new_tools,
                result.updated_tools,
                result.duration,
                result.error
            ))
            
            conn.commit()
            conn.close()
            
            logger.info(f"Saved crawl result to SQLite for source {result.source_id}")
            return True
        except Exception as e:
            logger.error(f"Error saving crawl result to SQLite: {str(e)}")
            return False
    
    async def get_crawl_results(self, source_id: Optional[str] = None, limit: int = 10) -> List[CrawlResult]:
        """
        Get crawl results from the database.
        
        Args:
            source_id: Optional ID of the source to get results for.
            limit: Maximum number of results to return.
            
        Returns:
            List of CrawlResult objects.
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            if source_id:
                cursor.execute(
                    'SELECT * FROM crawl_results WHERE source_id = ? ORDER BY timestamp DESC LIMIT ?',
                    (source_id, limit)
                )
            else:
                cursor.execute(
                    'SELECT * FROM crawl_results ORDER BY timestamp DESC LIMIT ?',
                    (limit,)
                )
            
            rows = cursor.fetchall()
            
            results = []
            column_names = [description[0] for description in cursor.description]
            
            for row in rows:
                result_dict = dict(zip(column_names, row))
                
                # Remove the 'id' field as it's not in the CrawlResult model
                if 'id' in result_dict:
                    del result_dict['id']
                
                results.append(CrawlResult(**result_dict))
            
            conn.close()
            
            return results
        except Exception as e:
            logger.error(f"Error getting crawl results from SQLite: {str(e)}")
            return []

