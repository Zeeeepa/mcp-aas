"""
Tests for the CrawlerModule implementation.
"""
import pytest
from unittest.mock import patch, AsyncMock, MagicMock

from src.models import Source, MCPTool, CrawlerStrategy, SourceType
from src.modules.crawler_module import CrawlerModule


class TestCrawlerModule:
    """Test the CrawlerModule implementation."""
    
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
    def mock_strategy(self):
        """Create a mock crawler strategy."""
        return CrawlerStrategy(
            id="test-strategy-id",
            source_id="test-source-id",
            source_type=SourceType.WEBSITE,
            implementation="""
from typing import List
from ..models import MCPTool, Source

class TestCrawler(BaseCrawler):
    async def discover_tools(self) -> List[MCPTool]:
        return [
            MCPTool(
                name="Test Tool",
                description="A test tool",
                url="https://example.com/tool",
                source_url=self.source.url
            )
        ]
""",
            description="Test crawler strategy"
        )
    
    @pytest.mark.asyncio
    async def test_run_crawler_with_strategy(self, mock_source, mock_strategy):
        """Test running a crawler with a strategy."""
        # Run the crawler
        tools = await CrawlerModule.run_crawler(mock_source, mock_strategy)
        
        # Check the result
        assert len(tools) == 1
        assert tools[0].name == "Test Tool"
        assert tools[0].description == "A test tool"
        assert tools[0].url == "https://example.com/tool"
        assert tools[0].source_url == mock_source.url
    
    @pytest.mark.asyncio
    async def test_run_crawler_with_invalid_strategy(self, mock_source):
        """Test running a crawler with an invalid strategy."""
        # Create an invalid strategy
        invalid_strategy = CrawlerStrategy(
            id="invalid-strategy-id",
            source_id="test-source-id",
            source_type=SourceType.WEBSITE,
            implementation="This is not valid Python code",
            description="Invalid crawler strategy"
        )
        
        # Run the crawler
        tools = await CrawlerModule.run_crawler(mock_source, invalid_strategy)
        
        # Check that no tools were returned
        assert len(tools) == 0
    
    @pytest.mark.asyncio
    async def test_run_crawler_with_strategy_no_crawler_class(self, mock_source):
        """Test running a crawler with a strategy that doesn't define a crawler class."""
        # Create a strategy without a crawler class
        no_class_strategy = CrawlerStrategy(
            id="no-class-strategy-id",
            source_id="test-source-id",
            source_type=SourceType.WEBSITE,
            implementation="def some_function(): pass",
            description="Strategy without crawler class"
        )
        
        # Run the crawler
        tools = await CrawlerModule.run_crawler(mock_source, no_class_strategy)
        
        # Check that no tools were returned
        assert len(tools) == 0
    
    @pytest.mark.asyncio
    async def test_run_builtin_crawler_github_awesome_list(self, mock_source):
        """Test running a built-in GitHub awesome list crawler."""
        # Mock the GitHubAwesomeListCrawler
        mock_crawler = AsyncMock()
        mock_crawler.discover_tools = AsyncMock(return_value=[
            MCPTool(
                name="Test Tool",
                description="A test tool",
                url="https://example.com/tool",
                source_url=mock_source.url
            )
        ])
        
        # Mock the crawler class
        mock_crawler_class = MagicMock(return_value=mock_crawler)
        
        # Patch the import
        with patch('src.modules.crawler_module.GitHubAwesomeListCrawler', mock_crawler_class):
            # Run the crawler
            tools = await CrawlerModule._run_builtin_crawler(mock_source)
            
            # Check that the crawler was created with the source
            mock_crawler_class.assert_called_once_with(mock_source)
            
            # Check that discover_tools was called
            mock_crawler.discover_tools.assert_called_once()
            
            # Check the result
            assert len(tools) == 1
            assert tools[0].name == "Test Tool"
    
    @pytest.mark.asyncio
    async def test_run_builtin_crawler_unsupported_type(self):
        """Test running a built-in crawler with an unsupported source type."""
        # Create a source with an unsupported type
        source = Source(
            id="test-source-id",
            url="https://example.com",
            name="Test Source",
            type=SourceType.MANUALLY_ADDED,
            has_known_crawler=False
        )
        
        # Run the crawler
        tools = await CrawlerModule._run_builtin_crawler(source)
        
        # Check that no tools were returned
        assert len(tools) == 0
    
    @pytest.mark.asyncio
    async def test_run_crawler_exception_handling(self, mock_source):
        """Test that exceptions in the crawler are handled properly."""
        # Mock the _run_builtin_crawler method to raise an exception
        with patch('src.modules.crawler_module.CrawlerModule._run_builtin_crawler', 
                  side_effect=Exception("Test error")):
            # Run the crawler
            tools = await CrawlerModule.run_crawler(mock_source)
            
            # Check that no tools were returned
            assert len(tools) == 0

