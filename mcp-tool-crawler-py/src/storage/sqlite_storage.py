"""
SQLite storage service for MCP tools and sources.
"""

import json
import os
import sqlite3
import threading
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional, Union, Tuple

from ..models import MCPTool, Source, SourceType, CrawlerStrategy, CrawlResult
from ..utils.logging import get_logger
from ..utils.config import get_config

logger = get_logger(__name__)
config = get_config()

# Thread-local storage for SQLite connections
local = threading.local()


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
        self._initialize_db()
    
    @contextmanager
    def get_connection(self):
        """
        Get a SQLite connection from the connection pool.
        
        This uses thread-local storage to ensure each thread has its own connection.
        
        Yields:
            A SQLite connection.
        """
        # Check if this thread already has a connection
        if not hasattr(local, 'sqlite_conn'):
            # Create a new connection for this thread
            local.sqlite_conn = sqlite3.connect(
                str(self.db_path),
                detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES
            )
            # Enable foreign keys
            local.sqlite_conn.execute("PRAGMA foreign_keys = ON")
            # Use Row as row factory for better column access
            local.sqlite_conn.row_factory = sqlite3.Row
        
        try:
            # Yield the connection for use
            yield local.sqlite_conn
        except Exception as e:
            # If an error occurs, rollback any changes
            local.sqlite_conn.rollback()
            raise e
    
    def _initialize_db(self):
        """
        Initialize the SQLite database with the required tables.
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Create sources table
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS sources (
                id TEXT PRIMARY KEY,
                url TEXT NOT NULL UNIQUE,
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
                url TEXT NOT NULL UNIQUE,
                source_url TEXT NOT NULL,
                first_discovered TEXT NOT NULL,
                last_updated TEXT NOT NULL,
                metadata TEXT
            )
            ''')
            
            # Create crawler_strategies table
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS crawler_strategies (
                id TEXT PRIMARY KEY,
                source_id TEXT NOT NULL,
                source_type TEXT NOT NULL,
                implementation TEXT NOT NULL,
                description TEXT NOT NULL,
                created TEXT NOT NULL,
                last_modified TEXT NOT NULL,
                FOREIGN KEY (source_id) REFERENCES sources(id) ON DELETE CASCADE
            )
            ''')
            
            # Create crawl_results table
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
                error TEXT,
                FOREIGN KEY (source_id) REFERENCES sources(id) ON DELETE CASCADE
            )
            ''')
            
            # Create indexes for common queries
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_sources_url ON sources(url)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_tools_url ON tools(url)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_tools_source_url ON tools(source_url)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_crawler_strategies_source_id ON crawler_strategies(source_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_crawl_results_source_id ON crawl_results(source_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_crawl_results_timestamp ON crawl_results(timestamp)')
            
            conn.commit()
            logger.info(f"Initialized SQLite database at {self.db_path}")
    
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
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Convert metadata to JSON string
                metadata_json = json.dumps(source.metadata) if source.metadata else '{}'
                
                # Check if source already exists
                cursor.execute('SELECT id FROM sources WHERE id = ?', (source.id,))
                exists = cursor.fetchone() is not None
                
                if exists:
                    # Update existing source
                    cursor.execute('''
                    UPDATE sources
                    SET url = ?, name = ?, type = ?, has_known_crawler = ?,
                        crawler_id = ?, last_crawled = ?, last_crawl_status = ?, metadata = ?
                    WHERE id = ?
                    ''', (
                        source.url, source.name, source.type.value, source.has_known_crawler,
                        source.crawler_id, source.last_crawled, source.last_crawl_status, metadata_json,
                        source.id
                    ))
                else:
                    # Insert new source
                    cursor.execute('''
                    INSERT INTO sources (id, url, name, type, has_known_crawler, crawler_id, last_crawled, last_crawl_status, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        source.id, source.url, source.name, source.type.value, source.has_known_crawler,
                        source.crawler_id, source.last_crawled, source.last_crawl_status, metadata_json
                    ))
                
                conn.commit()
                logger.info(f"{'Updated' if exists else 'Saved'} source: {source.name} ({source.url})")
                return True
        except Exception as e:
            logger.error(f"Error saving source: {str(e)}")
            return False
    
    async def get_source(self, source_id: str) -> Optional[Source]:
        """
        Get a source by ID.
        
        Args:
            source_id: ID of the source to get.
            
        Returns:
            Source if found, None otherwise.
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute('SELECT * FROM sources WHERE id = ?', (source_id,))
                row = cursor.fetchone()
                
                if row:
                    # Convert row to dict
                    source_dict = dict(row)
                    
                    # Parse metadata JSON
                    source_dict['metadata'] = json.loads(source_dict['metadata']) if source_dict['metadata'] else {}
                    
                    # Convert type string to enum
                    source_dict['type'] = SourceType(source_dict['type'])
                    
                    return Source(**source_dict)
                
                return None
        except Exception as e:
            logger.error(f"Error getting source: {str(e)}")
            return None
    
    async def get_source_by_url(self, url: str) -> Optional[Source]:
        """
        Get a source by URL.
        
        Args:
            url: URL of the source to get.
            
        Returns:
            Source if found, None otherwise.
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute('SELECT * FROM sources WHERE url = ?', (url,))
                row = cursor.fetchone()
                
                if row:
                    # Convert row to dict
                    source_dict = dict(row)
                    
                    # Parse metadata JSON
                    source_dict['metadata'] = json.loads(source_dict['metadata']) if source_dict['metadata'] else {}
                    
                    # Convert type string to enum
                    source_dict['type'] = SourceType(source_dict['type'])
                    
                    return Source(**source_dict)
                
                return None
        except Exception as e:
            logger.error(f"Error getting source by URL: {str(e)}")
            return None
    
    async def get_all_sources(self) -> List[Source]:
        """
        Get all sources from the database.
        
        Returns:
            List of all sources.
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute('SELECT * FROM sources')
                rows = cursor.fetchall()
                
                sources = []
                for row in rows:
                    # Convert row to dict
                    source_dict = dict(row)
                    
                    # Parse metadata JSON
                    source_dict['metadata'] = json.loads(source_dict['metadata']) if source_dict['metadata'] else {}
                    
                    # Convert type string to enum
                    source_dict['type'] = SourceType(source_dict['type'])
                    
                    sources.append(Source(**source_dict))
                
                logger.info(f"Retrieved {len(sources)} sources from SQLite")
                return sources
        except Exception as e:
            logger.error(f"Error getting all sources: {str(e)}")
            return []
    
    async def get_sources_to_crawl(self, time_threshold: str) -> List[Source]:
        """
        Get sources that need to be crawled.
        
        Args:
            time_threshold: ISO format timestamp. Sources that haven't been
                           crawled since this time will be returned.
            
        Returns:
            List of sources to crawl.
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Get sources that have never been crawled or were crawled before the threshold
                cursor.execute('''
                SELECT * FROM sources
                WHERE last_crawled IS NULL OR last_crawled < ?
                ''', (time_threshold,))
                
                rows = cursor.fetchall()
                
                sources = []
                for row in rows:
                    # Convert row to dict
                    source_dict = dict(row)
                    
                    # Parse metadata JSON
                    source_dict['metadata'] = json.loads(source_dict['metadata']) if source_dict['metadata'] else {}
                    
                    # Convert type string to enum
                    source_dict['type'] = SourceType(source_dict['type'])
                    
                    sources.append(Source(**source_dict))
                
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
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                timestamp = datetime.utcnow().isoformat()
                status = 'success' if success else 'failed'
                
                cursor.execute('''
                UPDATE sources
                SET last_crawled = ?, last_crawl_status = ?
                WHERE id = ?
                ''', (timestamp, status, source_id))
                
                conn.commit()
                
                if cursor.rowcount == 0:
                    logger.warning(f"No source found with ID {source_id} to update last crawl")
                    return False
                
                logger.info(f"Updated last crawl for source {source_id}")
                return True
        except Exception as e:
            logger.error(f"Error updating source last crawl: {str(e)}")
            return False
    
    async def delete_source(self, source_id: str) -> bool:
        """
        Delete a source from the database.
        
        Args:
            source_id: ID of the source to delete.
            
        Returns:
            True if successful, False otherwise.
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute('DELETE FROM sources WHERE id = ?', (source_id,))
                conn.commit()
                
                if cursor.rowcount == 0:
                    logger.warning(f"No source found with ID {source_id} to delete")
                    return False
                
                logger.info(f"Deleted source with ID {source_id}")
                return True
        except Exception as e:
            logger.error(f"Error deleting source: {str(e)}")
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
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                for tool in tools:
                    # Convert metadata to JSON string
                    metadata_json = json.dumps(tool.metadata) if tool.metadata else '{}'
                    
                    # Check if tool already exists
                    cursor.execute('SELECT id FROM tools WHERE id = ?', (tool.id,))
                    exists = cursor.fetchone() is not None
                    
                    if exists:
                        # Update existing tool
                        cursor.execute('''
                        UPDATE tools
                        SET name = ?, description = ?, url = ?, source_url = ?,
                            first_discovered = ?, last_updated = ?, metadata = ?
                        WHERE id = ?
                        ''', (
                            tool.name, tool.description, tool.url, tool.source_url,
                            tool.first_discovered, tool.last_updated, metadata_json,
                            tool.id
                        ))
                    else:
                        # Insert new tool
                        cursor.execute('''
                        INSERT INTO tools (id, name, description, url, source_url, first_discovered, last_updated, metadata)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        ''', (
                            tool.id, tool.name, tool.description, tool.url, tool.source_url,
                            tool.first_discovered, tool.last_updated, metadata_json
                        ))
                
                conn.commit()
                logger.info(f"Saved {len(tools)} tools to SQLite")
                return True
        except Exception as e:
            logger.error(f"Error saving tools to SQLite: {str(e)}")
            return False
    
    async def load_tools(self) -> List[MCPTool]:
        """
        Load all tools from the database.
        
        Returns:
            List of tools loaded from the database.
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute('SELECT * FROM tools')
                rows = cursor.fetchall()
                
                tools = []
                for row in rows:
                    # Convert row to dict
                    tool_dict = dict(row)
                    
                    # Parse metadata JSON
                    tool_dict['metadata'] = json.loads(tool_dict['metadata']) if tool_dict['metadata'] else {}
                    
                    tools.append(MCPTool(**tool_dict))
                
                logger.info(f"Loaded {len(tools)} tools from SQLite")
                return tools
        except Exception as e:
            logger.error(f"Error loading tools from SQLite: {str(e)}")
            return []
    
    async def get_tool(self, tool_id: str) -> Optional[MCPTool]:
        """
        Get a tool by ID.
        
        Args:
            tool_id: ID of the tool to get.
            
        Returns:
            Tool if found, None otherwise.
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute('SELECT * FROM tools WHERE id = ?', (tool_id,))
                row = cursor.fetchone()
                
                if row:
                    # Convert row to dict
                    tool_dict = dict(row)
                    
                    # Parse metadata JSON
                    tool_dict['metadata'] = json.loads(tool_dict['metadata']) if tool_dict['metadata'] else {}
                    
                    return MCPTool(**tool_dict)
                
                return None
        except Exception as e:
            logger.error(f"Error getting tool: {str(e)}")
            return None
    
    async def get_tool_by_url(self, url: str) -> Optional[MCPTool]:
        """
        Get a tool by URL.
        
        Args:
            url: URL of the tool to get.
            
        Returns:
            Tool if found, None otherwise.
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute('SELECT * FROM tools WHERE url = ?', (url,))
                row = cursor.fetchone()
                
                if row:
                    # Convert row to dict
                    tool_dict = dict(row)
                    
                    # Parse metadata JSON
                    tool_dict['metadata'] = json.loads(tool_dict['metadata']) if tool_dict['metadata'] else {}
                    
                    return MCPTool(**tool_dict)
                
                return None
        except Exception as e:
            logger.error(f"Error getting tool by URL: {str(e)}")
            return None
    
    async def get_tools_by_source_url(self, source_url: str) -> List[MCPTool]:
        """
        Get tools by source URL.
        
        Args:
            source_url: Source URL to filter by.
            
        Returns:
            List of tools from the specified source.
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute('SELECT * FROM tools WHERE source_url = ?', (source_url,))
                rows = cursor.fetchall()
                
                tools = []
                for row in rows:
                    # Convert row to dict
                    tool_dict = dict(row)
                    
                    # Parse metadata JSON
                    tool_dict['metadata'] = json.loads(tool_dict['metadata']) if tool_dict['metadata'] else {}
                    
                    tools.append(MCPTool(**tool_dict))
                
                logger.info(f"Retrieved {len(tools)} tools from source URL: {source_url}")
                return tools
        except Exception as e:
            logger.error(f"Error getting tools by source URL: {str(e)}")
            return []
    
    async def delete_tool(self, tool_id: str) -> bool:
        """
        Delete a tool from the database.
        
        Args:
            tool_id: ID of the tool to delete.
            
        Returns:
            True if successful, False otherwise.
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute('DELETE FROM tools WHERE id = ?', (tool_id,))
                conn.commit()
                
                if cursor.rowcount == 0:
                    logger.warning(f"No tool found with ID {tool_id} to delete")
                    return False
                
                logger.info(f"Deleted tool with ID {tool_id}")
                return True
        except Exception as e:
            logger.error(f"Error deleting tool: {str(e)}")
            return False
    
    # Crawler strategy methods
    
    async def save_crawler_strategy(self, strategy: CrawlerStrategy) -> bool:
        """
        Save a crawler strategy to the database.
        
        Args:
            strategy: Crawler strategy to save.
            
        Returns:
            True if successful, False otherwise.
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Check if strategy already exists
                cursor.execute('SELECT id FROM crawler_strategies WHERE id = ?', (strategy.id,))
                exists = cursor.fetchone() is not None
                
                if exists:
                    # Update existing strategy
                    cursor.execute('''
                    UPDATE crawler_strategies
                    SET source_id = ?, source_type = ?, implementation = ?,
                        description = ?, created = ?, last_modified = ?
                    WHERE id = ?
                    ''', (
                        strategy.source_id, strategy.source_type.value, strategy.implementation,
                        strategy.description, strategy.created, strategy.last_modified,
                        strategy.id
                    ))
                else:
                    # Insert new strategy
                    cursor.execute('''
                    INSERT INTO crawler_strategies (id, source_id, source_type, implementation, description, created, last_modified)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        strategy.id, strategy.source_id, strategy.source_type.value, strategy.implementation,
                        strategy.description, strategy.created, strategy.last_modified
                    ))
                
                conn.commit()
                logger.info(f"{'Updated' if exists else 'Saved'} crawler strategy for source ID: {strategy.source_id}")
                return True
        except Exception as e:
            logger.error(f"Error saving crawler strategy: {str(e)}")
            return False
    
    async def get_crawler_strategy(self, strategy_id: str) -> Optional[CrawlerStrategy]:
        """
        Get a crawler strategy by ID.
        
        Args:
            strategy_id: ID of the crawler strategy to get.
            
        Returns:
            Crawler strategy if found, None otherwise.
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute('SELECT * FROM crawler_strategies WHERE id = ?', (strategy_id,))
                row = cursor.fetchone()
                
                if row:
                    # Convert row to dict
                    strategy_dict = dict(row)
                    
                    # Convert source_type string to enum
                    strategy_dict['source_type'] = SourceType(strategy_dict['source_type'])
                    
                    return CrawlerStrategy(**strategy_dict)
                
                return None
        except Exception as e:
            logger.error(f"Error getting crawler strategy: {str(e)}")
            return None
    
    async def get_crawler_strategy_by_source_id(self, source_id: str) -> Optional[CrawlerStrategy]:
        """
        Get a crawler strategy by source ID.
        
        Args:
            source_id: ID of the source to get the crawler strategy for.
            
        Returns:
            Crawler strategy if found, None otherwise.
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute('SELECT * FROM crawler_strategies WHERE source_id = ?', (source_id,))
                row = cursor.fetchone()
                
                if row:
                    # Convert row to dict
                    strategy_dict = dict(row)
                    
                    # Convert source_type string to enum
                    strategy_dict['source_type'] = SourceType(strategy_dict['source_type'])
                    
                    return CrawlerStrategy(**strategy_dict)
                
                return None
        except Exception as e:
            logger.error(f"Error getting crawler strategy by source ID: {str(e)}")
            return None
    
    async def delete_crawler_strategy(self, strategy_id: str) -> bool:
        """
        Delete a crawler strategy from the database.
        
        Args:
            strategy_id: ID of the crawler strategy to delete.
            
        Returns:
            True if successful, False otherwise.
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute('DELETE FROM crawler_strategies WHERE id = ?', (strategy_id,))
                conn.commit()
                
                if cursor.rowcount == 0:
                    logger.warning(f"No crawler strategy found with ID {strategy_id} to delete")
                    return False
                
                logger.info(f"Deleted crawler strategy with ID {strategy_id}")
                return True
        except Exception as e:
            logger.error(f"Error deleting crawler strategy: {str(e)}")
            return False
    
    # Crawl result methods
    
    async def save_crawl_result(self, result: CrawlResult) -> bool:
        """
        Save a crawl result to the database.
        
        Args:
            result: Crawl result to save.
            
        Returns:
            True if successful, False otherwise.
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                INSERT INTO crawl_results (source_id, timestamp, success, tools_discovered, new_tools, updated_tools, duration, error)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    result.source_id, result.timestamp, result.success, result.tools_discovered,
                    result.new_tools, result.updated_tools, result.duration, result.error
                ))
                
                conn.commit()
                logger.info(f"Saved crawl result for source ID: {result.source_id}")
                return True
        except Exception as e:
            logger.error(f"Error saving crawl result: {str(e)}")
            return False
    
    async def get_crawl_results_by_source_id(self, source_id: str, limit: int = 10) -> List[CrawlResult]:
        """
        Get crawl results by source ID.
        
        Args:
            source_id: ID of the source to get crawl results for.
            limit: Maximum number of results to return.
            
        Returns:
            List of crawl results for the specified source.
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                SELECT * FROM crawl_results
                WHERE source_id = ?
                ORDER BY timestamp DESC
                LIMIT ?
                ''', (source_id, limit))
                
                rows = cursor.fetchall()
                
                results = []
                for row in rows:
                    # Convert row to dict
                    result_dict = dict(row)
                    
                    # Remove the auto-generated ID
                    if 'id' in result_dict:
                        del result_dict['id']
                    
                    results.append(CrawlResult(**result_dict))
                
                logger.info(f"Retrieved {len(results)} crawl results for source ID: {source_id}")
                return results
        except Exception as e:
            logger.error(f"Error getting crawl results by source ID: {str(e)}")
            return []
    
    async def get_latest_crawl_result_by_source_id(self, source_id: str) -> Optional[CrawlResult]:
        """
        Get the latest crawl result for a source.
        
        Args:
            source_id: ID of the source to get the latest crawl result for.
            
        Returns:
            Latest crawl result if found, None otherwise.
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                SELECT * FROM crawl_results
                WHERE source_id = ?
                ORDER BY timestamp DESC
                LIMIT 1
                ''', (source_id,))
                
                row = cursor.fetchone()
                
                if row:
                    # Convert row to dict
                    result_dict = dict(row)
                    
                    # Remove the auto-generated ID
                    if 'id' in result_dict:
                        del result_dict['id']
                    
                    return CrawlResult(**result_dict)
                
                return None
        except Exception as e:
            logger.error(f"Error getting latest crawl result by source ID: {str(e)}")
            return None

