"""
Unit tests for the SQLite storage service.
"""

import asyncio
import os
import tempfile
import unittest
from datetime import datetime, timezone

from src.models import MCPTool, Source, SourceType, CrawlerStrategy
from src.storage.sqlite_storage import SQLiteStorage, SQLiteSourceManager, SQLiteCrawlerStrategyStorage


class TestSQLiteStorage(unittest.TestCase):
    """Test cases for the SQLiteStorage class."""
    
    def setUp(self):
        """Set up the test environment."""
        # Create a temporary database file
        self.temp_db = tempfile.NamedTemporaryFile(delete=False)
        self.temp_db.close()
        
        # Create the SQLite storage with the temporary database
        self.storage = SQLiteStorage(db_path=self.temp_db.name)
    
    def tearDown(self):
        """Clean up the test environment."""
        # Remove the temporary database file
        os.unlink(self.temp_db.name)
    
    def test_init_db(self):
        """Test that the database is initialized correctly."""
        # The database should have been initialized in setUp
        # We can verify by checking that the tables exist
        import sqlite3
        conn = sqlite3.connect(self.temp_db.name)
        cursor = conn.cursor()
        
        # Check if the tools table exists
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='tools'"
        )
        self.assertIsNotNone(cursor.fetchone())
        
        # Check if the sources table exists
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='sources'"
        )
        self.assertIsNotNone(cursor.fetchone())
        
        # Check if the crawler_strategies table exists
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='crawler_strategies'"
        )
        self.assertIsNotNone(cursor.fetchone())
        
        conn.close()
    
    def test_save_and_load_tools(self):
        """Test saving and loading tools."""
        # Create some test tools
        tools = [
            MCPTool(
                id="tool-1",
                name="Test Tool 1",
                description="A test tool",
                url="https://example.com/tool1",
                source_url="https://example.com/source",
                first_discovered=datetime.now(timezone.utc).isoformat(),
                last_updated=datetime.now(timezone.utc).isoformat(),
                metadata={"tags": ["test", "tool"]}
            ),
            MCPTool(
                id="tool-2",
                name="Test Tool 2",
                description="Another test tool",
                url="https://example.com/tool2",
                source_url="https://example.com/source",
                first_discovered=datetime.now(timezone.utc).isoformat(),
                last_updated=datetime.now(timezone.utc).isoformat(),
                metadata={"tags": ["test", "tool"]}
            )
        ]
        
        # Save the tools
        result = asyncio.run(self.storage.save_tools(tools))
        
        # Check that the save was successful
        self.assertTrue(result)
        
        # Load the tools
        loaded_tools = asyncio.run(self.storage.load_tools())
        
        # Check that the loaded tools match the original tools
        self.assertEqual(len(loaded_tools), 2)
        self.assertEqual(loaded_tools[0].id, "tool-1")
        self.assertEqual(loaded_tools[0].name, "Test Tool 1")
        self.assertEqual(loaded_tools[1].id, "tool-2")
        self.assertEqual(loaded_tools[1].name, "Test Tool 2")


class TestSQLiteSourceManager(unittest.TestCase):
    """Test cases for the SQLiteSourceManager class."""
    
    def setUp(self):
        """Set up the test environment."""
        # Create a temporary database file
        self.temp_db = tempfile.NamedTemporaryFile(delete=False)
        self.temp_db.close()
        
        # Create the SQLite source manager with the temporary database
        self.source_manager = SQLiteSourceManager(db_path=self.temp_db.name)
    
    def tearDown(self):
        """Clean up the test environment."""
        # Remove the temporary database file
        os.unlink(self.temp_db.name)
    
    def test_add_and_get_source(self):
        """Test adding and getting a source."""
        # Create a test source
        source = Source(
            id="source-1",
            url="https://example.com/source",
            name="Test Source",
            type=SourceType.WEBSITE,
            has_known_crawler=False
        )
        
        # Add the source
        added_source = asyncio.run(self.source_manager.add_source(source))
        
        # Check that the add was successful
        self.assertEqual(added_source.id, "source-1")
        
        # Get all sources
        sources = asyncio.run(self.source_manager.get_all_sources())
        
        # Check that the source was retrieved
        self.assertEqual(len(sources), 1)
        self.assertEqual(sources[0].id, "source-1")
        self.assertEqual(sources[0].url, "https://example.com/source")
        self.assertEqual(sources[0].name, "Test Source")
        self.assertEqual(sources[0].type, SourceType.WEBSITE)
        self.assertEqual(sources[0].has_known_crawler, False)
    
    def test_update_source_last_crawl(self):
        """Test updating a source's last crawl information."""
        # Create a test source
        source = Source(
            id="source-1",
            url="https://example.com/source",
            name="Test Source",
            type=SourceType.WEBSITE,
            has_known_crawler=False
        )
        
        # Add the source
        asyncio.run(self.source_manager.add_source(source))
        
        # Update the source's last crawl information
        result = asyncio.run(self.source_manager.update_source_last_crawl("source-1", True))
        
        # Check that the update was successful
        self.assertTrue(result)
        
        # Get the source
        sources = asyncio.run(self.source_manager.get_all_sources())
        
        # Check that the source was updated
        self.assertEqual(len(sources), 1)
        self.assertEqual(sources[0].id, "source-1")
        self.assertIsNotNone(sources[0].last_crawled)
        self.assertEqual(sources[0].last_crawl_status, "success")


class TestSQLiteCrawlerStrategyStorage(unittest.TestCase):
    """Test cases for the SQLiteCrawlerStrategyStorage class."""
    
    def setUp(self):
        """Set up the test environment."""
        # Create a temporary database file
        self.temp_db = tempfile.NamedTemporaryFile(delete=False)
        self.temp_db.close()
        
        # Create the SQLite crawler strategy storage with the temporary database
        self.strategy_storage = SQLiteCrawlerStrategyStorage(db_path=self.temp_db.name)
    
    def tearDown(self):
        """Clean up the test environment."""
        # Remove the temporary database file
        os.unlink(self.temp_db.name)
    
    def test_save_and_get_strategy(self):
        """Test saving and getting a crawler strategy."""
        # Create a test strategy
        strategy = CrawlerStrategy(
            id="strategy-1",
            source_id="source-1",
            source_type=SourceType.WEBSITE,
            implementation="def extract_tools(html):\n    return []",
            description="Test Strategy",
            created=datetime.now(timezone.utc).isoformat(),
            last_modified=datetime.now(timezone.utc).isoformat()
        )
        
        # Save the strategy
        saved_strategy = asyncio.run(self.strategy_storage.save_strategy(strategy))
        
        # Check that the save was successful
        self.assertEqual(saved_strategy.id, "strategy-1")
        
        # Get the strategy
        loaded_strategy = asyncio.run(self.strategy_storage.get_strategy("strategy-1"))
        
        # Check that the loaded strategy matches the original strategy
        self.assertIsNotNone(loaded_strategy)
        self.assertEqual(loaded_strategy.id, "strategy-1")
        self.assertEqual(loaded_strategy.source_id, "source-1")
        self.assertEqual(loaded_strategy.source_type, SourceType.WEBSITE)
        self.assertEqual(loaded_strategy.implementation, "def extract_tools(html):\n    return []")
        self.assertEqual(loaded_strategy.description, "Test Strategy")
    
    def test_get_strategy_for_source(self):
        """Test getting a crawler strategy for a source."""
        # Create a test strategy
        strategy = CrawlerStrategy(
            id="strategy-1",
            source_id="source-1",
            source_type=SourceType.WEBSITE,
            implementation="def extract_tools(html):\n    return []",
            description="Test Strategy",
            created=datetime.now(timezone.utc).isoformat(),
            last_modified=datetime.now(timezone.utc).isoformat()
        )
        
        # Save the strategy
        asyncio.run(self.strategy_storage.save_strategy(strategy))
        
        # Get the strategy for the source
        loaded_strategy = asyncio.run(self.strategy_storage.get_strategy_for_source("source-1"))
        
        # Check that the loaded strategy matches the original strategy
        self.assertIsNotNone(loaded_strategy)
        self.assertEqual(loaded_strategy.id, "strategy-1")
        self.assertEqual(loaded_strategy.source_id, "source-1")
        
        # Try to get a strategy for a non-existent source
        loaded_strategy = asyncio.run(self.strategy_storage.get_strategy_for_source("source-2"))
        
        # Check that no strategy was found
        self.assertIsNone(loaded_strategy)


if __name__ == "__main__":
    unittest.main()

