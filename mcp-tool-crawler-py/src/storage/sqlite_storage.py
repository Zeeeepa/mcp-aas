"""
SQLite storage service for MCP tools and sources.
"""

import json
import sqlite3
import uuid
import yaml
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Any, Optional, Union, Tuple

from ..models import MCPTool, Source, SourceType
from ..utils.logging import get_logger
from ..utils.config import get_config
from ..utils.helpers import is_github_repo, extract_domain

logger = get_logger(__name__)
config = get_config()

class SQLiteStorage:
    """
    Base SQLite storage service.
    """
    
    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize the SQLite storage service.
        
        Args:
            db_path: Path to the SQLite database file. If None, uses the value from config.
        """
        self.db_path = db_path or config.get('sqlite', {}).get('db_path', './data/mcp_crawler.db')
        
        # Ensure data directory exists
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize database if it doesn't exist
        self._initialize_db()
    
    def _initialize_db(self) -> None:
        """
        Initialize the SQLite database with the required tables.
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # Check if the database has been initialized
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='sources'")
            if cursor.fetchone() is None:
                logger.info(f"Initializing SQLite database at {self.db_path}")
                
                # Create sources table
                cursor.execute("""
                CREATE TABLE sources (
                    id TEXT PRIMARY KEY,
                    url TEXT NOT NULL,
                    name TEXT NOT NULL,
                    type TEXT NOT NULL,
                    has_known_crawler BOOLEAN NOT NULL DEFAULT 0,
                    last_crawled TEXT,
                    last_crawl_status TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """)
                
                # Create indexes for sources table
                cursor.execute("CREATE INDEX idx_sources_url ON sources(url)")
                cursor.execute("CREATE INDEX idx_sources_type ON sources(type)")
                cursor.execute("CREATE INDEX idx_sources_last_crawled ON sources(last_crawled)")
                
                # Create crawlers table
                cursor.execute("""
                CREATE TABLE crawlers (
                    id TEXT PRIMARY KEY,
                    source_id TEXT NOT NULL,
                    strategy_type TEXT NOT NULL,
                    strategy_code TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    FOREIGN KEY (source_id) REFERENCES sources (id)
                )
                """)
                
                # Create index for crawlers table
                cursor.execute("CREATE INDEX idx_crawlers_source_id ON crawlers(source_id)")
                
                # Create crawl_results table
                cursor.execute("""
                CREATE TABLE crawl_results (
                    id TEXT PRIMARY KEY,
                    source_id TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    status TEXT NOT NULL,
                    tools_found INTEGER NOT NULL DEFAULT 0,
                    error_message TEXT,
                    FOREIGN KEY (source_id) REFERENCES sources (id)
                )
                """)
                
                # Create indexes for crawl_results table
                cursor.execute("CREATE INDEX idx_crawl_results_source_id ON crawl_results(source_id)")
                cursor.execute("CREATE INDEX idx_crawl_results_timestamp ON crawl_results(timestamp)")
                
                # Create tools table
                cursor.execute("""
                CREATE TABLE tools (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT,
                    url TEXT NOT NULL,
                    source_id TEXT NOT NULL,
                    tool_type TEXT,
                    github_stars INTEGER,
                    last_updated TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    FOREIGN KEY (source_id) REFERENCES sources (id)
                )
                """)
                
                # Create indexes for tools table
                cursor.execute("CREATE INDEX idx_tools_name ON tools(name)")
                cursor.execute("CREATE INDEX idx_tools_url ON tools(url)")
                cursor.execute("CREATE INDEX idx_tools_source_id ON tools(source_id)")
                cursor.execute("CREATE INDEX idx_tools_tool_type ON tools(tool_type)")
                
                conn.commit()
                logger.info("SQLite database initialized successfully")
            
            conn.close()
        except Exception as e:
            logger.error(f"Error initializing SQLite database: {str(e)}")
            raise
    
    def _get_connection(self) -> sqlite3.Connection:
        """
        Get a connection to the SQLite database.
        
        Returns:
            SQLite connection object.
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # This enables column access by name
        return conn
    
    def _now(self) -> str:
        """
        Get the current timestamp in ISO 8601 format.
        
        Returns:
            Current timestamp as string.
        """
        return datetime.now(timezone.utc).isoformat()


class SQLiteSourceStorage(SQLiteStorage):
    """
    SQLite storage service for sources.
    """
    
    async def save_source(self, source: Source) -> bool:
        """
        Save a source to the SQLite database.
        
        Args:
            source: Source to save.
            
        Returns:
            True if successful, False otherwise.
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # Check if source already exists
            cursor.execute("SELECT id FROM sources WHERE id = ?", (source.id,))
            existing = cursor.fetchone()
            
            now = self._now()
            
            if existing:
                # Update existing source
                cursor.execute("""
                UPDATE sources
                SET url = ?, name = ?, type = ?, has_known_crawler = ?, updated_at = ?
                WHERE id = ?
                """, (
                    source.url,
                    source.name,
                    source.type.value,
                    1 if source.has_known_crawler else 0,
                    now,
                    source.id
                ))
                logger.info(f"Updated source: {source.name} ({source.url})")
            else:
                # Insert new source
                cursor.execute("""
                INSERT INTO sources (id, url, name, type, has_known_crawler, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    source.id,
                    source.url,
                    source.name,
                    source.type.value,
                    1 if source.has_known_crawler else 0,
                    now,
                    now
                ))
                logger.info(f"Added source: {source.name} ({source.url})")
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"Error saving source: {str(e)}")
            return False
    
    async def get_source_by_id(self, source_id: str) -> Optional[Source]:
        """
        Get a source by its ID.
        
        Args:
            source_id: ID of the source to get.
            
        Returns:
            Source if found, None otherwise.
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute("SELECT * FROM sources WHERE id = ?", (source_id,))
            row = cursor.fetchone()
            
            conn.close()
            
            if row:
                return Source(
                    id=row['id'],
                    url=row['url'],
                    name=row['name'],
                    type=SourceType(row['type']),
                    has_known_crawler=bool(row['has_known_crawler']),
                    last_crawled=row['last_crawled'],
                    last_crawl_status=row['last_crawl_status']
                )
            
            return None
        except Exception as e:
            logger.error(f"Error getting source by ID: {str(e)}")
            return None
    
    async def get_all_sources(self) -> List[Source]:
        """
        Get all sources from the SQLite database.
        
        Returns:
            List of all sources.
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute("SELECT * FROM sources")
            rows = cursor.fetchall()
            
            conn.close()
            
            sources = []
            for row in rows:
                source = Source(
                    id=row['id'],
                    url=row['url'],
                    name=row['name'],
                    type=SourceType(row['type']),
                    has_known_crawler=bool(row['has_known_crawler']),
                    last_crawled=row['last_crawled'],
                    last_crawl_status=row['last_crawl_status']
                )
                sources.append(source)
            
            logger.info(f"Retrieved {len(sources)} sources from SQLite")
            return sources
        except Exception as e:
            logger.error(f"Error retrieving sources: {str(e)}")
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
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # Calculate threshold timestamp
            threshold_time = (datetime.now(timezone.utc) - 
                             timedelta(hours=time_threshold_hours)).isoformat()
            
            # Get sources that have never been crawled or were crawled before the threshold
            cursor.execute("""
            SELECT * FROM sources
            WHERE last_crawled IS NULL OR last_crawled < ?
            """, (threshold_time,))
            
            rows = cursor.fetchall()
            
            conn.close()
            
            sources = []
            for row in rows:
                source = Source(
                    id=row['id'],
                    url=row['url'],
                    name=row['name'],
                    type=SourceType(row['type']),
                    has_known_crawler=bool(row['has_known_crawler']),
                    last_crawled=row['last_crawled'],
                    last_crawl_status=row['last_crawl_status']
                )
                sources.append(source)
            
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
            conn = self._get_connection()
            cursor = conn.cursor()
            
            now = self._now()
            
            cursor.execute("""
            UPDATE sources
            SET last_crawled = ?, last_crawl_status = ?, updated_at = ?
            WHERE id = ?
            """, (
                now,
                'success' if success else 'failed',
                now,
                source_id
            ))
            
            conn.commit()
            conn.close()
            
            logger.info(f"Updated last crawl for source {source_id}")
            return True
        except Exception as e:
            logger.error(f"Error updating source last crawl: {str(e)}")
            return False
    
    async def load_sources_from_yaml(self, file_path: Optional[str] = None) -> List[Source]:
        """
        Load sources from a YAML file.
        
        Args:
            file_path: Path to the YAML file. If None, uses the default path.
            
        Returns:
            List of Source objects loaded from the YAML file.
        """
        try:
            if file_path:
                yaml_path = Path(file_path)
            else:
                yaml_path = Path(config.get('local_storage', {}).get('path', './data')) / 'sources.yaml'
            
            # Check if file exists
            if not yaml_path.exists():
                logger.warning(f"No source list found at {yaml_path}")
                return []
            
            # Read file
            with open(yaml_path, 'r', encoding='utf-8') as f:
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
                    id=str(uuid.uuid4()),
                    url=url,
                    name=name,
                    type=source_type,
                    has_known_crawler=source_type in [SourceType.GITHUB_AWESOME_LIST, SourceType.GITHUB_REPOSITORY],
                )
                
                sources.append(source)
            
            logger.info(f"Loaded {len(sources)} sources from {yaml_path}")
            return sources
        except Exception as e:
            logger.error(f"Error loading sources from YAML: {str(e)}")
            return []


class SQLiteToolStorage(SQLiteStorage):
    """
    SQLite storage service for MCP tools.
    """
    
    async def save_tools(self, tools: List[MCPTool]) -> bool:
        """
        Save tools to the SQLite database.
        
        Args:
            tools: List of tools to save.
            
        Returns:
            True if successful, False otherwise.
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            now = self._now()
            
            # Begin transaction
            conn.execute("BEGIN TRANSACTION")
            
            for tool in tools:
                # Check if tool already exists
                cursor.execute("SELECT id FROM tools WHERE url = ?", (tool.url,))
                existing = cursor.fetchone()
                
                if existing:
                    # Update existing tool
                    cursor.execute("""
                    UPDATE tools
                    SET name = ?, description = ?, source_id = ?, tool_type = ?,
                        github_stars = ?, last_updated = ?, updated_at = ?
                    WHERE id = ?
                    """, (
                        tool.name,
                        tool.description,
                        tool.source_id,
                        tool.tool_type,
                        tool.github_stars,
                        tool.last_updated,
                        now,
                        existing['id']
                    ))
                else:
                    # Insert new tool
                    tool_id = str(uuid.uuid4())
                    cursor.execute("""
                    INSERT INTO tools (id, name, description, url, source_id, tool_type,
                                      github_stars, last_updated, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        tool_id,
                        tool.name,
                        tool.description,
                        tool.url,
                        tool.source_id,
                        tool.tool_type,
                        tool.github_stars,
                        tool.last_updated,
                        now,
                        now
                    ))
            
            # Commit transaction
            conn.commit()
            conn.close()
            
            logger.info(f"Saved {len(tools)} tools to SQLite")
            
            # Also save to local file for compatibility
            await self._save_tools_to_file(tools)
            
            return True
        except Exception as e:
            logger.error(f"Error saving tools to SQLite: {str(e)}")
            return False
    
    async def load_tools(self) -> List[MCPTool]:
        """
        Load tools from the SQLite database.
        
        Returns:
            List of tools loaded from the database.
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute("SELECT * FROM tools")
            rows = cursor.fetchall()
            
            conn.close()
            
            tools = []
            for row in rows:
                tool = MCPTool(
                    id=row['id'],
                    name=row['name'],
                    description=row['description'],
                    url=row['url'],
                    source_id=row['source_id'],
                    tool_type=row['tool_type'],
                    github_stars=row['github_stars'],
                    last_updated=row['last_updated']
                )
                tools.append(tool)
            
            logger.info(f"Loaded {len(tools)} tools from SQLite")
            return tools
        except Exception as e:
            logger.error(f"Error loading tools from SQLite: {str(e)}")
            
            # Try to load from file as fallback
            return await self._load_tools_from_file()
    
    async def _save_tools_to_file(self, tools: List[MCPTool]) -> bool:
        """
        Save tools to a local file (for compatibility).
        
        Args:
            tools: List of tools to save.
            
        Returns:
            True if successful, False otherwise.
        """
        try:
            file_path = Path(config.get('local_storage', {}).get('path', './data')) / 'tools.json'
            
            # Ensure directory exists
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Convert tools to JSON
            tools_json = [tool.dict() for tool in tools]
            
            # Write to file
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(tools_json, f, indent=2)
            
            logger.info(f"Saved {len(tools)} tools to {file_path}")
            return True
        except Exception as e:
            logger.error(f"Error saving tools to local file: {str(e)}")
            return False
    
    async def _load_tools_from_file(self) -> List[MCPTool]:
        """
        Load tools from a local file (fallback method).
        
        Returns:
            List of tools loaded from the file.
        """
        try:
            file_path = Path(config.get('local_storage', {}).get('path', './data')) / 'tools.json'
            
            # Check if file exists
            if not file_path.exists():
                logger.warning(f"No tool catalog found at {file_path}")
                return []
            
            # Read file
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Convert to MCPTool objects
            tools = [MCPTool(**item) for item in data]
            
            logger.info(f"Loaded {len(tools)} tools from {file_path}")
            return tools
        except Exception as e:
            logger.error(f"Error loading tools from local file: {str(e)}")
            return []


class SQLiteCrawlerStorage(SQLiteStorage):
    """
    SQLite storage service for crawler strategies.
    """
    
    async def save_crawler_strategy(self, source_id: str, strategy_type: str, strategy_code: str) -> bool:
        """
        Save a crawler strategy to the SQLite database.
        
        Args:
            source_id: ID of the source this crawler is for.
            strategy_type: Type of crawler strategy (built_in, generated).
            strategy_code: Python code for the crawler strategy.
            
        Returns:
            True if successful, False otherwise.
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # Check if crawler already exists for this source
            cursor.execute("SELECT id FROM crawlers WHERE source_id = ?", (source_id,))
            existing = cursor.fetchone()
            
            now = self._now()
            
            if existing:
                # Update existing crawler
                cursor.execute("""
                UPDATE crawlers
                SET strategy_type = ?, strategy_code = ?, updated_at = ?
                WHERE id = ?
                """, (
                    strategy_type,
                    strategy_code,
                    now,
                    existing['id']
                ))
                logger.info(f"Updated crawler strategy for source {source_id}")
            else:
                # Insert new crawler
                crawler_id = str(uuid.uuid4())
                cursor.execute("""
                INSERT INTO crawlers (id, source_id, strategy_type, strategy_code, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    crawler_id,
                    source_id,
                    strategy_type,
                    strategy_code,
                    now,
                    now
                ))
                logger.info(f"Added crawler strategy for source {source_id}")
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"Error saving crawler strategy: {str(e)}")
            return False
    
    async def get_crawler_strategy(self, source_id: str) -> Optional[Tuple[str, str]]:
        """
        Get a crawler strategy for a source.
        
        Args:
            source_id: ID of the source to get the crawler for.
            
        Returns:
            Tuple of (strategy_type, strategy_code) if found, None otherwise.
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
            SELECT strategy_type, strategy_code FROM crawlers
            WHERE source_id = ?
            """, (source_id,))
            
            row = cursor.fetchone()
            
            conn.close()
            
            if row:
                return (row['strategy_type'], row['strategy_code'])
            
            return None
        except Exception as e:
            logger.error(f"Error getting crawler strategy: {str(e)}")
            return None


class SQLiteCrawlResultStorage(SQLiteStorage):
    """
    SQLite storage service for crawl results.
    """
    
    async def record_crawl_result(self, source_id: str, status: str, tools_found: int = 0, error_message: Optional[str] = None) -> bool:
        """
        Record a crawl result in the SQLite database.
        
        Args:
            source_id: ID of the source that was crawled.
            status: Status of the crawl (success, failed).
            tools_found: Number of tools found during the crawl.
            error_message: Error message if the crawl failed.
            
        Returns:
            True if successful, False otherwise.
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            now = self._now()
            result_id = str(uuid.uuid4())
            
            cursor.execute("""
            INSERT INTO crawl_results (id, source_id, timestamp, status, tools_found, error_message)
            VALUES (?, ?, ?, ?, ?, ?)
            """, (
                result_id,
                source_id,
                now,
                status,
                tools_found,
                error_message
            ))
            
            conn.commit()
            conn.close()
            
            logger.info(f"Recorded crawl result for source {source_id}: {status}")
            return True
        except Exception as e:
            logger.error(f"Error recording crawl result: {str(e)}")
            return False
    
    async def get_crawl_results(self, source_id: Optional[str] = None, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get crawl results from the SQLite database.
        
        Args:
            source_id: Optional ID of the source to get results for. If None, gets results for all sources.
            limit: Maximum number of results to return.
            
        Returns:
            List of crawl results.
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            if source_id:
                cursor.execute("""
                SELECT * FROM crawl_results
                WHERE source_id = ?
                ORDER BY timestamp DESC
                LIMIT ?
                """, (source_id, limit))
            else:
                cursor.execute("""
                SELECT * FROM crawl_results
                ORDER BY timestamp DESC
                LIMIT ?
                """, (limit,))
            
            rows = cursor.fetchall()
            
            conn.close()
            
            results = []
            for row in rows:
                result = dict(row)
                results.append(result)
            
            return results
        except Exception as e:
            logger.error(f"Error getting crawl results: {str(e)}")
            return []

