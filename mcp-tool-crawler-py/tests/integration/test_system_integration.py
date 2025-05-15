"""
Integration tests for the complete MCP Tool Crawler system.
"""
import os
import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch, AsyncMock, MagicMock

from src.models import Source, MCPTool, CrawlerStrategy, SourceType
from src.storage.sqlite_storage import SQLiteStorage
from src.storage.local_storage import LocalStorage
from src.services.source_manager_sqlite import SourceManager
from src.workflow.orchestrator import WorkflowOrchestrator


class TestSystemIntegration:
    """Integration tests for the complete system."""
    
    @pytest.fixture
    def temp_db_path(self):
        """Create a temporary SQLite database file."""
        fd, path = tempfile.mkstemp(suffix='.db')
        os.close(fd)
        yield path
        os.unlink(path)
    
    @pytest.fixture
    def temp_tools_path(self):
        """Create a temporary tools file."""
        fd, path = tempfile.mkstemp(suffix='.json')
        os.close(fd)
        yield path
        os.unlink(path)
    
    @pytest.fixture
    def temp_sources_path(self):
        """Create a temporary sources file."""
        fd, path = tempfile.mkstemp(suffix='.yaml')
        os.close(fd)
        yield path
        os.unlink(path)
    
    @pytest.fixture
    def sqlite_storage(self, temp_db_path):
        """Create a SQLiteStorage instance."""
        return SQLiteStorage(db_path=temp_db_path)
    
    @pytest.fixture
    def local_storage(self, temp_tools_path):
        """Create a LocalStorage instance."""
        return LocalStorage(file_path=temp_tools_path)
    
    @pytest.fixture
    def source_manager(self, temp_db_path):
        """Create a SourceManager instance."""
        return SourceManager(db_path=temp_db_path)
    
    @pytest.fixture
    def orchestrator(self):
        """Create a WorkflowOrchestrator instance."""
        return WorkflowOrchestrator()
    
    @pytest.fixture
    def mock_source(self):
        """Create a mock source."""
        return Source(
            id="test-source-id",
            url="https://github.com/awesome-mcp/awesome-list",
            name="Awesome MCP List",
            type=SourceType.GITHUB_AWESOME_LIST,
            has_known_crawler=True
        )
    
    @pytest.fixture
    def mock_tools(self):
        """Create mock tools."""
        return [
            MCPTool(
                id=f"test-tool-{i}",
                name=f"Test Tool {i}",
                description=f"Description for Test Tool {i}",
                url=f"https://example.com/tool{i}",
                source_url="https://github.com/awesome-mcp/awesome-list"
            )
            for i in range(3)
        ]
    
    @pytest.fixture
    def mock_strategy(self, mock_source):
        """Create a mock crawler strategy."""
        return CrawlerStrategy(
            id="test-strategy-id",
            source_id=mock_source.id,
            source_type=mock_source.type,
            implementation="def discover_tools(): pass",
            description="Test crawler strategy"
        )
    
    @pytest.mark.asyncio
    async def test_source_management_workflow(self, source_manager, sqlite_storage):
        """Test the source management workflow."""
        # Add a source
        source = Source(
            url="https://github.com/awesome-mcp/awesome-list",
            name="Awesome MCP List",
            type=SourceType.GITHUB_AWESOME_LIST,
            has_known_crawler=True
        )
        
        added_source = await source_manager.add_source(source)
        
        # Check that the source was added
        assert added_source.id is not None
        
        # Get all sources
        sources = await source_manager.get_all_sources()
        
        # Check that the source is in the list
        assert len(sources) == 1
        assert sources[0].id == added_source.id
        
        # Update the source's last crawl information
        result = await source_manager.update_source_last_crawl(added_source.id, True)
        assert result is True
        
        # Get the updated source
        updated_sources = await source_manager.get_all_sources()
        updated_source = updated_sources[0]
        
        # Check that the last crawl information was updated
        assert updated_source.last_crawled is not None
        assert updated_source.last_crawl_status == "success"
        
        # Get sources to crawl (should be empty since we just crawled)
        sources_to_crawl = await source_manager.get_sources_to_crawl(time_threshold_hours=24)
        assert len(sources_to_crawl) == 0
    
    @pytest.mark.asyncio
    async def test_tool_storage_workflow(self, local_storage, mock_tools):
        """Test the tool storage workflow."""
        # Save tools
        result = await local_storage.save_tools(mock_tools)
        assert result is True
        
        # Load tools
        loaded_tools = await local_storage.load_tools()
        
        # Check that all tools were loaded
        assert len(loaded_tools) == len(mock_tools)
        
        # Check that the tools match
        tool_ids = [tool.id for tool in mock_tools]
        loaded_ids = [tool.id for tool in loaded_tools]
        
        for tool_id in tool_ids:
            assert tool_id in loaded_ids
    
    @pytest.mark.asyncio
    async def test_crawler_strategy_workflow(self, sqlite_storage, mock_strategy):
        """Test the crawler strategy workflow."""
        # Save the strategy
        result = await sqlite_storage.save_crawler_strategy(mock_strategy)
        assert result is True
        
        # Get the strategy by ID
        retrieved_strategy = await sqlite_storage.get_crawler_strategy(mock_strategy.id)
        
        # Check that the strategy matches
        assert retrieved_strategy is not None
        assert retrieved_strategy.id == mock_strategy.id
        assert retrieved_strategy.source_id == mock_strategy.source_id
        assert retrieved_strategy.source_type == mock_strategy.source_type
        assert retrieved_strategy.implementation == mock_strategy.implementation
        
        # Get the strategy by source ID
        retrieved_by_source = await sqlite_storage.get_crawler_strategy_by_source(mock_strategy.source_id)
        
        # Check that the strategy matches
        assert retrieved_by_source is not None
        assert retrieved_by_source.id == mock_strategy.id
    
    @pytest.mark.asyncio
    async def test_crawler_workflow(self, orchestrator, mock_source, mock_tools, sqlite_storage, local_storage):
        """Test the crawler workflow."""
        # Mock the crawler function
        async def mock_crawler_func(source):
            assert source.id == mock_source.id
            return mock_tools
        
        # Save the source
        await sqlite_storage.save_source(mock_source)
        
        # Run the crawler workflow
        result = await orchestrator.run_crawler_workflow(
            source=mock_source,
            crawler_func=mock_crawler_func,
            storage_func=local_storage.save_tools,
            update_source_func=sqlite_storage.update_source_last_crawl
        )
        
        # Check the result
        assert result.source_id == mock_source.id
        assert result.success is True
        assert result.tools_discovered == len(mock_tools)
        assert result.new_tools == len(mock_tools)
        
        # Check that the tools were saved
        loaded_tools = await local_storage.load_tools()
        assert len(loaded_tools) == len(mock_tools)
        
        # Check that the source was updated
        updated_source = await sqlite_storage.get_source(mock_source.id)
        assert updated_source.last_crawled is not None
        assert updated_source.last_crawl_status == "success"
    
    @pytest.mark.asyncio
    async def test_end_to_end_workflow(self, source_manager, sqlite_storage, local_storage, orchestrator, mock_strategy):
        """Test the end-to-end workflow."""
        # Add a source
        source = Source(
            url="https://github.com/awesome-mcp/awesome-list",
            name="Awesome MCP List",
            type=SourceType.GITHUB_AWESOME_LIST,
            has_known_crawler=True
        )
        
        added_source = await source_manager.add_source(source)
        
        # Save a crawler strategy for the source
        strategy = CrawlerStrategy(
            id="test-strategy-id",
            source_id=added_source.id,
            source_type=added_source.type,
            implementation="def discover_tools(): pass",
            description="Test crawler strategy"
        )
        
        await sqlite_storage.save_crawler_strategy(strategy)
        
        # Update the source with the crawler ID
        await sqlite_storage.save_source(Source(
            id=added_source.id,
            url=added_source.url,
            name=added_source.name,
            type=added_source.type,
            has_known_crawler=added_source.has_known_crawler,
            crawler_id=strategy.id
        ))
        
        # Mock the crawler function
        async def mock_crawler_func(source, strategy):
            assert source.id == added_source.id
            assert strategy.id == "test-strategy-id"
            return [
                MCPTool(
                    id="test-tool-1",
                    name="Test Tool 1",
                    description="Description for Test Tool 1",
                    url="https://example.com/tool1",
                    source_url=source.url
                )
            ]
        
        # Run the batch crawler workflow
        results = await orchestrator.run_batch_crawler_workflow(
            sources=[added_source],
            get_crawler_func=sqlite_storage.get_crawler_strategy_by_source,
            crawler_func=mock_crawler_func,
            storage_func=local_storage.save_tools,
            update_source_func=sqlite_storage.update_source_last_crawl,
            save_result_func=sqlite_storage.save_crawl_result
        )
        
        # Check the results
        assert len(results) == 1
        assert results[0].source_id == added_source.id
        assert results[0].success is True
        assert results[0].tools_discovered == 1
        
        # Check that the tools were saved
        loaded_tools = await local_storage.load_tools()
        assert len(loaded_tools) == 1
        assert loaded_tools[0].name == "Test Tool 1"
        
        # Check that the source was updated
        updated_source = await sqlite_storage.get_source(added_source.id)
        assert updated_source.last_crawled is not None
        assert updated_source.last_crawl_status == "success"
        
        # Check that the crawl result was saved
        crawl_results = await sqlite_storage.get_crawl_results(added_source.id)
        assert len(crawl_results) == 1
        assert crawl_results[0].source_id == added_source.id
        assert crawl_results[0].success is True
        assert crawl_results[0].tools_discovered == 1

