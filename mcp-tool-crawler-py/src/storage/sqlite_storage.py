"""
SQLite storage service for MCP tools and sources.
"""

import json
import sqlite3
import os
from pathlib import Path
from typing import List, Dict, Any, Optional, Union
from datetime import datetime

from ..models import MCPTool, Source, SourceType, CrawlerStrategy, CrawlResult
from ..utils.logging import get_logger
from ..utils.config import get_config

logger = get_logger(__name__)
config = get_config()

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
    
    def _initialize_db(self):
        """
        Initialize the SQLite database with the required tables.
        """
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
        
        # Create crawlers table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS crawlers (
            id TEXT PRIMARY KEY,
            source_id TEXT NOT NULL,
            source_type TEXT NOT NULL,
            implementation TEXT NOT NULL,
            description TEXT NOT NULL,
            created TEXT NOT NULL,
            last_modified TEXT NOT NULL
        )
        ''')
        
        # Create crawl_results table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS crawl_results (
            id TEXT PRIMARY KEY,
            source_id TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            success INTEGER NOT NULL,
            tools_discovered INTEGER NOT NULL,
            new_tools INTEGER NOT NULL,
            updated_tools INTEGER NOT NULL,
            duration INTEGER NOT NULL,
            error TEXT
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
            
            for tool in tools:
                # Check if tool already exists
                cursor.execute("SELECT id FROM tools WHERE id = ?", (tool.id,))
                existing_tool = cursor.fetchone()
                
                if existing_tool:
                    # Update existing tool
                    cursor.execute('''
                    UPDATE tools
                    SET name = ?, description = ?, url = ?, source_url = ?,
                        last_updated = ?, metadata = ?
                    WHERE id = ?
                    ''', (
                        tool.name,
                        tool.description,
                        tool.url,
                        tool.source_url,
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
            
            cursor.execute("SELECT * FROM tools")
            rows = cursor.fetchall()
            
            tools = []
            for row in rows:
                tool = MCPTool(
                    id=row['id'],
                    name=row['name'],
                    description=row['description'],
                    url=row['url'],
                    source_url=row['source_url'],
                    first_discovered=row['first_discovered'],
                    last_updated=row['last_updated'],
                    metadata=json.loads(row['metadata']) if row['metadata'] else {}
                )
                tools.append(tool)
            
            conn.close()
            
            logger.info(f"Loaded {len(tools)} tools from SQLite database")
            return tools
        except Exception as e:
            logger.error(f"Error loading tools from SQLite database: {str(e)}")
            return []
    
    async def save_source(self, source: Source) -> bool:
        """
        Save a source to the SQLite database.
        
        Args:
            source: Source to save.
            
        Returns:
            True if successful, False otherwise.
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Check if source already exists
            cursor.execute("SELECT id FROM sources WHERE id = ?", (source.id,))
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
                    source.type,
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
                    source.type,
                    1 if source.has_known_crawler else 0,
                    source.crawler_id,
                    source.last_crawled,
                    source.last_crawl_status,
                    json.dumps(source.metadata)
                ))
            
            conn.commit()
            conn.close()
            
            logger.info(f"Saved source {source.name} to SQLite database")
            return True
        except Exception as e:
            logger.error(f"Error saving source to SQLite database: {str(e)}")
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
            
            cursor.execute("SELECT * FROM sources")
            rows = cursor.fetchall()
            
            sources = []
            for row in rows:
                source = Source(
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
                sources.append(source)
            
            conn.close()
            
            logger.info(f"Loaded {len(sources)} sources from SQLite database")
            return sources
        except Exception as e:
            logger.error(f"Error loading sources from SQLite database: {str(e)}")
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
            logger.error(f"Error updating source last crawl: {str(e)}")
            return False
    
    async def save_crawler_strategy(self, strategy: CrawlerStrategy) -> bool:
        """
        Save a crawler strategy to the SQLite database.
        
        Args:
            strategy: Crawler strategy to save.
            
        Returns:
            True if successful, False otherwise.
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Check if strategy already exists
            cursor.execute("SELECT id FROM crawlers WHERE id = ?", (strategy.id,))
            existing_strategy = cursor.fetchone()
            
            if existing_strategy:
                # Update existing strategy
                cursor.execute('''
                UPDATE crawlers
                SET source_id = ?, source_type = ?, implementation = ?,
                    description = ?, last_modified = ?
                WHERE id = ?
                ''', (
                    strategy.source_id,
                    strategy.source_type,
                    strategy.implementation,
                    strategy.description,
                    strategy.last_modified,
                    strategy.id
                ))
            else:
                # Insert new strategy
                cursor.execute('''
                INSERT INTO crawlers (id, source_id, source_type, implementation,
                                     description, created, last_modified)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    strategy.id,
                    strategy.source_id,
                    strategy.source_type,
                    strategy.implementation,
                    strategy.description,
                    strategy.created,
                    strategy.last_modified
                ))
            
            conn.commit()
            conn.close()
            
            logger.info(f"Saved crawler strategy {strategy.id} to SQLite database")
            return True
        except Exception as e:
            logger.error(f"Error saving crawler strategy to SQLite database: {str(e)}")
            return False
    
    async def load_crawler_strategy(self, strategy_id: str) -> Optional[CrawlerStrategy]:
        """
        Load a crawler strategy from the SQLite database.
        
        Args:
            strategy_id: ID of the crawler strategy to load.
            
        Returns:
            Crawler strategy if found, None otherwise.
        """
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute("SELECT * FROM crawlers WHERE id = ?", (strategy_id,))
            row = cursor.fetchone()
            
            if not row:
                logger.warning(f"No crawler strategy found with ID {strategy_id}")
                return None
            
            strategy = CrawlerStrategy(
                id=row['id'],
                source_id=row['source_id'],
                source_type=SourceType(row['source_type']),
                implementation=row['implementation'],
                description=row['description'],
                created=row['created'],
                last_modified=row['last_modified']
            )
            
            conn.close()
            
            logger.info(f"Loaded crawler strategy {strategy_id} from SQLite database")
            return strategy
        except Exception as e:
            logger.error(f"Error loading crawler strategy from SQLite database: {str(e)}")
            return None
    
    async def save_crawl_result(self, result: CrawlResult) -> bool:
        """
        Save a crawl result to the SQLite database.
        
        Args:
            result: Crawl result to save.
            
        Returns:
            True if successful, False otherwise.
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Generate a unique ID for the crawl result
            result_id = f"result-{datetime.now().strftime('%Y%m%d%H%M%S')}-{result.source_id}"
            
            # Insert new crawl result
            cursor.execute('''
            INSERT INTO crawl_results (id, source_id, timestamp, success,
                                      tools_discovered, new_tools, updated_tools,
                                      duration, error)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                result_id,
                result.source_id,
                result.timestamp,
                1 if result.success else 0,
                result.tools_discovered,
                result.new_tools,
                result.updated_tools,
                result.duration,
                result.error
            ))
            
            conn.commit()
            conn.close()
            
            logger.info(f"Saved crawl result {result_id} to SQLite database")
            return True
        except Exception as e:
            logger.error(f"Error saving crawl result to SQLite database: {str(e)}")
            return False

