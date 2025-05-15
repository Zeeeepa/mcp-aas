"""
Tests for the SQLiteStorage implementation.
"""
import os
import pytest
import json
import sqlite3
from datetime import datetime, timedelta

from src.models import Source, MCPTool, CrawlerStrategy, CrawlResult, SourceType
from src.storage.sqlite_storage import SQLiteStorage


class TestSQLiteStorage:
    """Test the SQLiteStorage implementation."""
    
    def test_initialization(self, temp_db_path):
        """Test initializing the SQLiteStorage."""
        # Create storage
        storage = SQLiteStorage(db_path=temp_db_path)
        
        # Check that the database file was created
        assert os.path.exists(temp_db_path)
        
        # Check that the tables were created
        conn = sqlite3.connect(temp_db_path)
        cursor = conn.cursor()
        
        # Get list of tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [row[0] for row in cursor.fetchall()]
        
        # Check that all expected tables exist
        assert "sources" in tables
        assert "tools" in tables
        assert "crawler_strategies" in tables
        assert "crawl_results" in tables
        
        conn.close()
    
    @pytest.mark.asyncio
    async def test_save_and_get_source(self, sqlite_storage):
        """Test saving and retrieving a source."""
        # Create a source
        source = Source(
            id="test-source-id",
            url="https://example.com",
            name="Test Source",
            type=SourceType.WEBSITE,
            has_known_crawler=False,
            metadata={"key": "value"}
        )
        
        # Save the source
        result = await sqlite_storage.save_source(source)
        assert result is True
        
        # Retrieve the source
        retrieved_source = await sqlite_storage.get_source(source.id)
        
        # Check that the retrieved source matches the original
        assert retrieved_source is not None
        assert retrieved_source.id == source.id
        assert retrieved_source.url == source.url
        assert retrieved_source.name == source.name
        assert retrieved_source.type == source.type
        assert retrieved_source.has_known_crawler == source.has_known_crawler
        assert retrieved_source.metadata == source.metadata
    
    @pytest.mark.asyncio
    async def test_get_all_sources(self, sqlite_storage):
        """Test retrieving all sources."""
        # Create and save multiple sources
        sources = [
            Source(
                id=f"test-source-{i}",
                url=f"https://example{i}.com",
                name=f"Test Source {i}",
                type=SourceType.WEBSITE,
                has_known_crawler=False
            )
            for i in range(3)
        ]
        
        for source in sources:
            await sqlite_storage.save_source(source)
        
        # Retrieve all sources
        retrieved_sources = await sqlite_storage.get_all_sources()
        
        # Check that all sources were retrieved
        assert len(retrieved_sources) == 3
        
        # Check that the sources match
        source_ids = [source.id for source in sources]
        retrieved_ids = [source.id for source in retrieved_sources]
        
        for source_id in source_ids:
            assert source_id in retrieved_ids
    
    @pytest.mark.asyncio
    async def test_update_source_last_crawl(self, sqlite_storage):
        """Test updating a source's last crawl information."""
        # Create and save a source
        source = Source(
            id="test-source-id",
            url="https://example.com",
            name="Test Source",
            type=SourceType.WEBSITE,
            has_known_crawler=False
        )
        
        await sqlite_storage.save_source(source)
        
        # Update the source's last crawl information
        result = await sqlite_storage.update_source_last_crawl(source.id, True)
        assert result is True
        
        # Retrieve the updated source
        updated_source = await sqlite_storage.get_source(source.id)
        
        # Check that the last crawl information was updated
        assert updated_source is not None
        assert updated_source.last_crawled is not None
        assert updated_source.last_crawl_status == "success"
        
        # Test with failure status
        result = await sqlite_storage.update_source_last_crawl(source.id, False)
        assert result is True
        
        # Retrieve the updated source
        updated_source = await sqlite_storage.get_source(source.id)
        
        # Check that the last crawl information was updated
        assert updated_source is not None
        assert updated_source.last_crawled is not None
        assert updated_source.last_crawl_status == "failed"
    
    @pytest.mark.asyncio
    async def test_save_and_load_tools(self, sqlite_storage):
        """Test saving and loading tools."""
        # Create tools
        tools = [
            MCPTool(
                id=f"test-tool-{i}",
                name=f"Test Tool {i}",
                description=f"Description for Test Tool {i}",
                url=f"https://example.com/tool{i}",
                source_url="https://example.com",
                metadata={"tags": [f"tag{i}"]}
            )
            for i in range(3)
        ]
        
        # Save tools
        result = await sqlite_storage.save_tools(tools)
        assert result is True
        
        # Load tools
        loaded_tools = await sqlite_storage.load_tools()
        
        # Check that all tools were loaded
        assert len(loaded_tools) == 3
        
        # Check that the tools match
        tool_ids = [tool.id for tool in tools]
        loaded_ids = [tool.id for tool in loaded_tools]
        
        for tool_id in tool_ids:
            assert tool_id in loaded_ids
        
        # Check that the metadata was preserved
        for tool in loaded_tools:
            assert "tags" in tool.metadata
    
    @pytest.mark.asyncio
    async def test_save_and_get_crawler_strategy(self, sqlite_storage):
        """Test saving and retrieving a crawler strategy."""
        # Create a crawler strategy
        strategy = CrawlerStrategy(
            id="test-strategy-id",
            source_id="test-source-id",
            source_type=SourceType.WEBSITE,
            implementation="def discover_tools(): pass",
            description="Test crawler strategy"
        )
        
        # Save the strategy
        result = await sqlite_storage.save_crawler_strategy(strategy)
        assert result is True
        
        # Retrieve the strategy
        retrieved_strategy = await sqlite_storage.get_crawler_strategy(strategy.id)
        
        # Check that the retrieved strategy matches the original
        assert retrieved_strategy is not None
        assert retrieved_strategy.id == strategy.id
        assert retrieved_strategy.source_id == strategy.source_id
        assert retrieved_strategy.source_type == strategy.source_type
        assert retrieved_strategy.implementation == strategy.implementation
        assert retrieved_strategy.description == strategy.description
    
    @pytest.mark.asyncio
    async def test_get_crawler_strategy_by_source(self, sqlite_storage):
        """Test retrieving a crawler strategy by source ID."""
        # Create a crawler strategy
        source_id = "test-source-id"
        strategy = CrawlerStrategy(
            id="test-strategy-id",
            source_id=source_id,
            source_type=SourceType.WEBSITE,
            implementation="def discover_tools(): pass",
            description="Test crawler strategy"
        )
        
        # Save the strategy
        await sqlite_storage.save_crawler_strategy(strategy)
        
        # Retrieve the strategy by source ID
        retrieved_strategy = await sqlite_storage.get_crawler_strategy_by_source(source_id)
        
        # Check that the retrieved strategy matches the original
        assert retrieved_strategy is not None
        assert retrieved_strategy.id == strategy.id
        assert retrieved_strategy.source_id == strategy.source_id
    
    @pytest.mark.asyncio
    async def test_save_and_get_crawl_results(self, sqlite_storage):
        """Test saving and retrieving crawl results."""
        # Create crawl results
        source_id = "test-source-id"
        results = [
            CrawlResult(
                source_id=source_id,
                timestamp=datetime.now().isoformat(),
                success=True,
                tools_discovered=10,
                new_tools=5,
                updated_tools=2,
                duration=1500
            ),
            CrawlResult(
                source_id=source_id,
                timestamp=(datetime.now() - timedelta(hours=1)).isoformat(),
                success=False,
                tools_discovered=8,
                new_tools=3,
                updated_tools=1,
                duration=1200,
                error="Test error"
            )
        ]
        
        # Save the results
        for result in results:
            await sqlite_storage.save_crawl_result(result)
        
        # Retrieve the results
        retrieved_results = await sqlite_storage.get_crawl_results(source_id)
        
        # Check that the results were retrieved
        assert len(retrieved_results) == 2
        
        # Check that the results are ordered by timestamp (most recent first)
        assert retrieved_results[0].timestamp > retrieved_results[1].timestamp
        
        # Check that the first result matches
        assert retrieved_results[0].source_id == source_id
        assert retrieved_results[0].success is True
        assert retrieved_results[0].tools_discovered == 10
        assert retrieved_results[0].new_tools == 5
        assert retrieved_results[0].updated_tools == 2
        assert retrieved_results[0].duration == 1500
        assert retrieved_results[0].error is None
        
        # Check that the second result matches
        assert retrieved_results[1].source_id == source_id
        assert retrieved_results[1].success is False
        assert retrieved_results[1].tools_discovered == 8
        assert retrieved_results[1].new_tools == 3
        assert retrieved_results[1].updated_tools == 1
        assert retrieved_results[1].duration == 1200
        assert retrieved_results[1].error == "Test error"
    
    @pytest.mark.asyncio
    async def test_get_crawl_results_limit(self, sqlite_storage):
        """Test retrieving crawl results with a limit."""
        # Create multiple crawl results
        source_id = "test-source-id"
        for i in range(5):
            result = CrawlResult(
                source_id=source_id,
                timestamp=(datetime.now() - timedelta(hours=i)).isoformat(),
                success=True,
                tools_discovered=10,
                new_tools=5,
                updated_tools=2,
                duration=1500
            )
            await sqlite_storage.save_crawl_result(result)
        
        # Retrieve with limit
        retrieved_results = await sqlite_storage.get_crawl_results(source_id, limit=3)
        
        # Check that only the specified number of results were retrieved
        assert len(retrieved_results) == 3
        
        # Check that they are ordered by timestamp (most recent first)
        for i in range(len(retrieved_results) - 1):
            assert retrieved_results[i].timestamp > retrieved_results[i + 1].timestamp

