"""
SQLite storage service for MCP tools and sources.

This module replaces DynamoDB with a local SQLite database.
"""

import json
import sqlite3
import yaml
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Any, Optional, Union

from ..models import MCPTool, Source, SourceType, CrawlerStrategy
from ..utils.logging import get_logger
from ..utils.config import get_config
from ..utils.helpers import is_github_repo, extract_domain

logger = get_logger(__name__)
config = get_config()


class SQLiteStorage:
    """
    SQLite storage service for MCP tools.
    
    This class replaces DynamoDB with a local SQLite database.
    """
    
    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize the SQLite storage service.
        
        Args:
            db_path: Path to the SQLite database file. If None, uses the default path.
        """
        # Set up the database path
        if db_path:
            self.db_path = db_path
        else:
            data_dir = Path(__file__).parents[3] / 'data'
            data_dir.mkdir(parents=True, exist_ok=True)
            self.db_path = str(data_dir / 'mcp_tools.db')
        
        # Initialize the database
        self._init_db()
    
    def _init_db(self) -> None:
        """Initialize the SQLite database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create tables if they don't exist
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
        
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS crawler_strategies (
            id TEXT PRIMARY KEY,
            source_id TEXT NOT NULL,
            source_type TEXT NOT NULL,
            implementation TEXT NOT NULL,
            description TEXT NOT NULL,
            created TEXT NOT NULL,
            last_modified TEXT NOT NULL,
            FOREIGN KEY (source_id) REFERENCES sources(id)
        )
        ''')
        
        conn.commit()
        conn.close()
    
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
            
            # Insert or update each tool
            for tool in tools:
                cursor.execute(
                    '''
                    INSERT OR REPLACE INTO tools
                    (id, name, description, url, source_url, first_discovered, last_updated, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ''',
                    (
                        tool.id,
                        tool.name,
                        tool.description,
                        tool.url,
                        tool.source_url,
                        tool.first_discovered,
                        tool.last_updated,
                        json.dumps(tool.metadata)
                    )
                )
            
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
            
            # Get all tools
            cursor.execute('SELECT * FROM tools')
            rows = cursor.fetchall()
            
            # Convert to MCPTool objects
            tools = []
            for row in rows:
                metadata = json.loads(row['metadata']) if row['metadata'] else {}
                
                tool = MCPTool(
                    id=row['id'],
                    name=row['name'],
                    description=row['description'],
                    url=row['url'],
                    source_url=row['source_url'],
                    first_discovered=row['first_discovered'],
                    last_updated=row['last_updated'],
                    metadata=metadata
                )
                
                tools.append(tool)
            
            conn.close()
            
            logger.info(f"Loaded {len(tools)} tools from SQLite database")
            return tools
        except Exception as e:
            logger.error(f"Error loading tools from SQLite database: {str(e)}")
            return []


class SQLiteSourceManager:
    """
    SQLite storage service for sources.
    
    This class replaces DynamoDB with a local SQLite database for source management.
    """
    
    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize the SQLite source manager.
        
        Args:
            db_path: Path to the SQLite database file. If None, uses the default path.
        """
        # Set up the database path
        if db_path:
            self.db_path = db_path
        else:
            data_dir = Path(__file__).parents[3] / 'data'
            data_dir.mkdir(parents=True, exist_ok=True)
            self.db_path = str(data_dir / 'mcp_tools.db')
        
        # Initialize the database
        self._init_db()
    
    def _init_db(self) -> None:
        """Initialize the SQLite database."""
        # Use the same initialization as SQLiteStorage
        storage = SQLiteStorage(self.db_path)
    
    async def add_source(self, source: Source) -> Source:
        """
        Add a new source to the database.
        
        Args:
            source: Source to add.
            
        Returns:
            The added source.
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Insert the source
            cursor.execute(
                '''
                INSERT OR REPLACE INTO sources
                (id, url, name, type, has_known_crawler, crawler_id, last_crawled, last_crawl_status, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''',
                (
                    source.id,
                    source.url,
                    source.name,
                    source.type,
                    1 if source.has_known_crawler else 0,
                    source.crawler_id,
                    source.last_crawled,
                    source.last_crawl_status,
                    json.dumps(source.metadata)
                )
            )
            
            conn.commit()
            conn.close()
            
            logger.info(f"Added source to SQLite database: {source.name} ({source.url})")
            return source
        except Exception as e:
            logger.error(f"Error adding source to SQLite database: {str(e)}")
            raise
    
    async def get_all_sources(self) -> List[Source]:
        """
        Get all sources from the database.
        
        Returns:
            List of all sources.
        """
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Get all sources
            cursor.execute('SELECT * FROM sources')
            rows = cursor.fetchall()
            
            # Convert to Source objects
            sources = []
            for row in rows:
                metadata = json.loads(row['metadata']) if row['metadata'] else {}
                
                source = Source(
                    id=row['id'],
                    url=row['url'],
                    name=row['name'],
                    type=SourceType(row['type']),
                    has_known_crawler=bool(row['has_known_crawler']),
                    crawler_id=row['crawler_id'],
                    last_crawled=row['last_crawled'],
                    last_crawl_status=row['last_crawl_status'],
                    metadata=metadata
                )
                
                sources.append(source)
            
            conn.close()
            
            logger.info(f"Retrieved {len(sources)} sources from SQLite database")
            return sources
        except Exception as e:
            logger.error(f"Error retrieving sources from SQLite database: {str(e)}")
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
            # Get all sources
            all_sources = await self.get_all_sources()
            
            # Calculate threshold timestamp
            threshold_time = (datetime.now(timezone.utc) - 
                             timedelta(hours=time_threshold_hours)).isoformat()
            
            # Filter sources
            sources_to_crawl = []
            
            for source in all_sources:
                # If the source has never been crawled, or was crawled before the threshold
                if not source.last_crawled or source.last_crawled < threshold_time:
                    sources_to_crawl.append(source)
            
            logger.info(f"Found {len(sources_to_crawl)} sources to crawl")
            return sources_to_crawl
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
            
            # Update the source
            cursor.execute(
                '''
                UPDATE sources
                SET last_crawled = ?, last_crawl_status = ?
                WHERE id = ?
                ''',
                (
                    datetime.now(timezone.utc).isoformat(),
                    'success' if success else 'failed',
                    source_id
                )
            )
            
            conn.commit()
            conn.close()
            
            logger.info(f"Updated last crawl for source {source_id}")
            return True
        except Exception as e:
            logger.error(f"Error updating source last crawl: {str(e)}")
            return False
    
    async def initialize_sources(self) -> List[Source]:
        """
        Initialize sources from the configuration and source list file.
        
        This loads sources from:
        1. The source list file if available
        2. Predefined sources from configuration (as fallback)
        
        Sources are added to the database for tracking.
        
        Returns:
            List of all sources (existing + newly added).
        """
        logger.info("Initializing sources")
        
        # Get existing sources
        existing_sources = await self.get_all_sources()
        existing_urls = {source.url for source in existing_sources}
        
        # Try to load sources from file first
        try:
            from ..storage.file_source_storage import FileSourceStorage
            file_source_storage = FileSourceStorage()
            file_sources = await file_source_storage.load_sources()
            
            if file_sources:
                logger.info(f"Loaded {len(file_sources)} sources from file")
                
                # Add sources from file that don't already exist
                for source in file_sources:
                    if source.url not in existing_urls:
                        await self.add_source(source)
                        existing_sources.append(source)
                        existing_urls.add(source.url)
                        
                        logger.info(f"Added new source from file: {source.name} ({source.url})")
                
                return existing_sources
        except Exception as e:
            logger.warning(f"Error loading sources from file, falling back to config: {str(e)}")
        
        # If no sources from file or error occurred, fall back to config
        logger.info("Using predefined sources from configuration")
        
        # Add awesome lists from config
        for url in config['sources']['awesome_lists']:
            if url not in existing_urls:
                domain = extract_domain(url)
                name = f"Awesome MCP Tools ({domain})"
                
                source = Source(
                    url=url,
                    name=name,
                    type=SourceType.GITHUB_AWESOME_LIST,
                    has_known_crawler=True,
                )
                
                await self.add_source(source)
                existing_sources.append(source)
                existing_urls.add(url)
                
                logger.info(f"Added new source from config: {name} ({url})")
        
        # Add websites from config
        for website in config['sources']['websites']:
            if website['url'] not in existing_urls:
                source = Source(
                    url=website['url'],
                    name=website['name'],
                    type=SourceType.WEBSITE,
                    has_known_crawler=False,
                )
                
                await self.add_source(source)
                existing_sources.append(source)
                existing_urls.add(website['url'])
                
                logger.info(f"Added new source from config: {website['name']} ({website['url']})")
        
        return existing_sources


class SQLiteCrawlerStrategyStorage:
    """
    SQLite storage service for crawler strategies.
    
    This class replaces DynamoDB with a local SQLite database for crawler strategy management.
    """
    
    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize the SQLite crawler strategy storage.
        
        Args:
            db_path: Path to the SQLite database file. If None, uses the default path.
        """
        # Set up the database path
        if db_path:
            self.db_path = db_path
        else:
            data_dir = Path(__file__).parents[3] / 'data'
            data_dir.mkdir(parents=True, exist_ok=True)
            self.db_path = str(data_dir / 'mcp_tools.db')
        
        # Initialize the database
        self._init_db()
    
    def _init_db(self) -> None:
        """Initialize the SQLite database."""
        # Use the same initialization as SQLiteStorage
        storage = SQLiteStorage(self.db_path)
    
    async def save_strategy(self, strategy: CrawlerStrategy) -> CrawlerStrategy:
        """
        Save a crawler strategy to the database.
        
        Args:
            strategy: CrawlerStrategy to save.
            
        Returns:
            The saved strategy.
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Insert the strategy
            cursor.execute(
                '''
                INSERT OR REPLACE INTO crawler_strategies
                (id, source_id, source_type, implementation, description, created, last_modified)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ''',
                (
                    strategy.id,
                    strategy.source_id,
                    strategy.source_type,
                    strategy.implementation,
                    strategy.description,
                    strategy.created,
                    strategy.last_modified
                )
            )
            
            conn.commit()
            conn.close()
            
            logger.info(f"Saved crawler strategy to SQLite database: {strategy.id}")
            return strategy
        except Exception as e:
            logger.error(f"Error saving crawler strategy to SQLite database: {str(e)}")
            raise
    
    async def get_strategy(self, strategy_id: str) -> Optional[CrawlerStrategy]:
        """
        Get a crawler strategy from the database.
        
        Args:
            strategy_id: ID of the strategy to get.
            
        Returns:
            The crawler strategy, or None if not found.
        """
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Get the strategy
            cursor.execute(
                'SELECT * FROM crawler_strategies WHERE id = ?',
                (strategy_id,)
            )
            row = cursor.fetchone()
            
            if not row:
                return None
            
            # Convert to CrawlerStrategy object
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
            
            return strategy
        except Exception as e:
            logger.error(f"Error getting crawler strategy from SQLite database: {str(e)}")
            return None
    
    async def get_strategy_for_source(self, source_id: str) -> Optional[CrawlerStrategy]:
        """
        Get a crawler strategy for a source from the database.
        
        Args:
            source_id: ID of the source to get the strategy for.
            
        Returns:
            The crawler strategy, or None if not found.
        """
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Get the strategy
            cursor.execute(
                'SELECT * FROM crawler_strategies WHERE source_id = ?',
                (source_id,)
            )
            row = cursor.fetchone()
            
            if not row:
                return None
            
            # Convert to CrawlerStrategy object
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
            
            return strategy
        except Exception as e:
            logger.error(f"Error getting crawler strategy for source from SQLite database: {str(e)}")
            return None

