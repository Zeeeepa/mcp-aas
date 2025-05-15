"""
End-to-end integration test for the MCP Tool Crawler.
"""

import asyncio
import os
import shutil
import time
from pathlib import Path

import pytest

from src.models import Source, SourceType
from src.services.source_manager import SourceManager
from src.services.crawler_service import CrawlerService
from src.storage.sqlite_storage import SQLiteStorage
from src.utils.logging import get_logger

logger = get_logger(__name__)


@pytest.fixture
def test_data_dir():
    """Create a temporary test data directory."""
    test_dir = Path(__file__).parents[2] / 'data' / 'test'
    
    # Create test directory
    test_dir.mkdir(parents=True, exist_ok=True)
    
    # Create subdirectories
    (test_dir / 'crawlers').mkdir(exist_ok=True)
    
    # Set environment variables
    os.environ['DATA_DIR'] = str(test_dir)
    os.environ['SQLITE_DB_FILE'] = 'test_crawler.db'
    
    yield test_dir
    
    # Clean up
    try:
        shutil.rmtree(test_dir)
    except Exception as e:
        logger.warning(f"Error cleaning up test directory: {str(e)}")


@pytest.mark.asyncio
async def test_end_to_end(test_data_dir):
    """Test the entire system end-to-end."""
    # Initialize storage
    storage = SQLiteStorage(db_path=str(test_data_dir / 'test_crawler.db'))
    
    # Create a test source
    source = Source(
        url="https://github.com/jpmcb/awesome-machine-context-protocol",
        name="Test Awesome List",
        type=SourceType.GITHUB_AWESOME_LIST,
        has_known_crawler=True,
    )
    
    # Initialize source manager
    source_manager = SourceManager()
    
    # Add the source
    await source_manager.add_source(source)
    
    # Verify source was added
    sources = await source_manager.get_all_sources()
    assert len(sources) == 1
    assert sources[0].url == source.url
    
    # Initialize crawler service
    crawler_service = CrawlerService()
    
    # Crawl the source
    result = await crawler_service.crawl_source(sources[0])
    
    # Verify crawl was successful
    assert result.success
    assert result.tools_discovered > 0
    
    # Load tools from storage
    tools = await storage.load_tools()
    
    # Verify tools were saved
    assert len(tools) > 0
    assert tools[0].source_id == sources[0].id
    
    # Verify source last crawl was updated
    updated_sources = await source_manager.get_all_sources()
    assert updated_sources[0].last_crawled is not None
    assert updated_sources[0].last_crawl_status == 'success'
    
    # Test crawl all sources
    results = await crawler_service.crawl_all_sources(force=True)
    
    # Verify all crawls were successful
    assert len(results) == 1
    assert results[0].success


@pytest.mark.asyncio
async def test_performance_comparison(test_data_dir):
    """Test performance comparison between SQLite and AWS implementations."""
    # This is a placeholder for a real performance comparison test
    # In a real implementation, this would compare the performance of
    # the SQLite implementation with the AWS implementation
    
    # Initialize storage
    storage = SQLiteStorage(db_path=str(test_data_dir / 'test_crawler.db'))
    
    # Create a test source
    source = Source(
        url="https://github.com/jpmcb/awesome-machine-context-protocol",
        name="Test Awesome List",
        type=SourceType.GITHUB_AWESOME_LIST,
        has_known_crawler=True,
    )
    
    # Initialize source manager
    source_manager = SourceManager()
    
    # Add the source
    start_time = time.time()
    await source_manager.add_source(source)
    add_source_time = time.time() - start_time
    
    # Verify source was added
    start_time = time.time()
    sources = await source_manager.get_all_sources()
    get_sources_time = time.time() - start_time
    
    # Initialize crawler service
    crawler_service = CrawlerService()
    
    # Crawl the source
    start_time = time.time()
    result = await crawler_service.crawl_source(sources[0])
    crawl_time = time.time() - start_time
    
    # Load tools from storage
    start_time = time.time()
    tools = await storage.load_tools()
    load_tools_time = time.time() - start_time
    
    # Print performance metrics
    logger.info("Performance Metrics (SQLite Implementation):")
    logger.info(f"- Add Source: {add_source_time:.4f} seconds")
    logger.info(f"- Get Sources: {get_sources_time:.4f} seconds")
    logger.info(f"- Crawl Source: {crawl_time:.4f} seconds")
    logger.info(f"- Load Tools: {load_tools_time:.4f} seconds")
    
    # In a real implementation, this would compare with AWS metrics
    # For now, just assert that the operations completed in a reasonable time
    assert add_source_time < 1.0
    assert get_sources_time < 1.0
    assert load_tools_time < 1.0

