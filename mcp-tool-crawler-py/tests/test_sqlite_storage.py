"""
Unit tests for SQLite storage implementation.
"""

import os
import pytest
import tempfile
from pathlib import Path
from datetime import datetime

from src.models import MCPTool, Source, SourceType, CrawlerStrategy, CrawlResult
from src.storage.sqlite_storage import SQLiteStorage


@pytest.fixture
def temp_db_path():
    """Create a temporary database file path."""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
        tmp_path = tmp.name
    
    yield tmp_path
    
    # Clean up the temporary file after the test
    if os.path.exists(tmp_path):
        os.unlink(tmp_path)


@pytest.fixture
async def sqlite_storage(temp_db_path):
    """Create a SQLiteStorage instance with a temporary database."""
    storage = SQLiteStorage(temp_db_path)
    yield storage


@pytest.mark.asyncio
async def test_save_and_load_tools(sqlite_storage):
    """Test saving and loading tools."""
    # Create test tools
    tools = [
        MCPTool(
            name="Test Tool 1",
            description="A test tool",
            url="https://example.com/tool1",
            source_url="https://example.com/source",
        ),
        MCPTool(
            name="Test Tool 2",
            description="Another test tool",
            url="https://example.com/tool2",
            source_url="https://example.com/source",
        ),
    ]
    
    # Save tools
    result = await sqlite_storage.save_tools(tools)
    assert result is True
    
    # Load tools
    loaded_tools = await sqlite_storage.load_tools()
    assert len(loaded_tools) == 2
    
    # Verify tool data
    assert loaded_tools[0].name == "Test Tool 1"
    assert loaded_tools[0].url == "https://example.com/tool1"
    assert loaded_tools[1].name == "Test Tool 2"
    assert loaded_tools[1].url == "https://example.com/tool2"


@pytest.mark.asyncio
async def test_save_and_get_source(sqlite_storage):
    """Test saving and retrieving a source."""
    # Create test source
    source = Source(
        url="https://github.com/example/awesome-mcp",
        name="Awesome MCP",
        type=SourceType.GITHUB_AWESOME_LIST,
        has_known_crawler=True,
    )
    
    # Save source
    result = await sqlite_storage.save_source(source)
    assert result is True
    
    # Get source by ID
    retrieved_source = await sqlite_storage.get_source(source.id)
    assert retrieved_source is not None
    assert retrieved_source.url == source.url
    assert retrieved_source.name == source.name
    assert retrieved_source.type == source.type
    
    # Get source by URL
    retrieved_source_by_url = await sqlite_storage.get_source_by_url(source.url)
    assert retrieved_source_by_url is not None
    assert retrieved_source_by_url.id == source.id


@pytest.mark.asyncio
async def test_update_source(sqlite_storage):
    """Test updating a source."""
    # Create and save test source
    source = Source(
        url="https://github.com/example/awesome-mcp",
        name="Awesome MCP",
        type=SourceType.GITHUB_AWESOME_LIST,
        has_known_crawler=True,
    )
    await sqlite_storage.save_source(source)
    
    # Update source
    source.name = "Updated Awesome MCP"
    source.last_crawled = datetime.utcnow().isoformat()
    source.last_crawl_status = "success"
    
    result = await sqlite_storage.save_source(source)
    assert result is True
    
    # Get updated source
    updated_source = await sqlite_storage.get_source(source.id)
    assert updated_source is not None
    assert updated_source.name == "Updated Awesome MCP"
    assert updated_source.last_crawled == source.last_crawled
    assert updated_source.last_crawl_status == "success"


@pytest.mark.asyncio
async def test_get_all_sources(sqlite_storage):
    """Test getting all sources."""
    # Create and save test sources
    sources = [
        Source(
            url="https://github.com/example/awesome-mcp",
            name="Awesome MCP",
            type=SourceType.GITHUB_AWESOME_LIST,
            has_known_crawler=True,
        ),
        Source(
            url="https://github.com/example/mcp-tools",
            name="MCP Tools",
            type=SourceType.GITHUB_REPOSITORY,
            has_known_crawler=True,
        ),
    ]
    
    for source in sources:
        await sqlite_storage.save_source(source)
    
    # Get all sources
    all_sources = await sqlite_storage.get_all_sources()
    assert len(all_sources) == 2


@pytest.mark.asyncio
async def test_get_sources_to_crawl(sqlite_storage):
    """Test getting sources to crawl."""
    # Create sources with different last_crawled times
    old_time = "2020-01-01T00:00:00"
    new_time = datetime.utcnow().isoformat()
    
    sources = [
        Source(
            url="https://github.com/example/awesome-mcp",
            name="Awesome MCP",
            type=SourceType.GITHUB_AWESOME_LIST,
            has_known_crawler=True,
            last_crawled=old_time,
        ),
        Source(
            url="https://github.com/example/mcp-tools",
            name="MCP Tools",
            type=SourceType.GITHUB_REPOSITORY,
            has_known_crawler=True,
            last_crawled=new_time,
        ),
        Source(
            url="https://github.com/example/new-repo",
            name="New Repo",
            type=SourceType.GITHUB_REPOSITORY,
            has_known_crawler=True,
        ),
    ]
    
    for source in sources:
        await sqlite_storage.save_source(source)
    
    # Get sources to crawl with threshold between old_time and new_time
    threshold_time = "2022-01-01T00:00:00"
    sources_to_crawl = await sqlite_storage.get_sources_to_crawl(threshold_time)
    
    # Should return the source with old_time and the source with no last_crawled
    assert len(sources_to_crawl) == 2
    urls = [s.url for s in sources_to_crawl]
    assert "https://github.com/example/awesome-mcp" in urls
    assert "https://github.com/example/new-repo" in urls


@pytest.mark.asyncio
async def test_update_source_last_crawl(sqlite_storage):
    """Test updating a source's last crawl information."""
    # Create and save test source
    source = Source(
        url="https://github.com/example/awesome-mcp",
        name="Awesome MCP",
        type=SourceType.GITHUB_AWESOME_LIST,
        has_known_crawler=True,
    )
    await sqlite_storage.save_source(source)
    
    # Update last crawl
    result = await sqlite_storage.update_source_last_crawl(source.id, True)
    assert result is True
    
    # Get updated source
    updated_source = await sqlite_storage.get_source(source.id)
    assert updated_source is not None
    assert updated_source.last_crawled is not None
    assert updated_source.last_crawl_status == "success"
    
    # Update with failure
    result = await sqlite_storage.update_source_last_crawl(source.id, False)
    assert result is True
    
    # Get updated source
    updated_source = await sqlite_storage.get_source(source.id)
    assert updated_source.last_crawl_status == "failed"


@pytest.mark.asyncio
async def test_delete_source(sqlite_storage):
    """Test deleting a source."""
    # Create and save test source
    source = Source(
        url="https://github.com/example/awesome-mcp",
        name="Awesome MCP",
        type=SourceType.GITHUB_AWESOME_LIST,
        has_known_crawler=True,
    )
    await sqlite_storage.save_source(source)
    
    # Delete source
    result = await sqlite_storage.delete_source(source.id)
    assert result is True
    
    # Try to get deleted source
    deleted_source = await sqlite_storage.get_source(source.id)
    assert deleted_source is None


@pytest.mark.asyncio
async def test_save_and_get_crawler_strategy(sqlite_storage):
    """Test saving and retrieving a crawler strategy."""
    # Create and save test source first
    source = Source(
        url="https://github.com/example/awesome-mcp",
        name="Awesome MCP",
        type=SourceType.GITHUB_AWESOME_LIST,
        has_known_crawler=True,
    )
    await sqlite_storage.save_source(source)
    
    # Create test crawler strategy
    strategy = CrawlerStrategy(
        source_id=source.id,
        source_type=SourceType.GITHUB_AWESOME_LIST,
        implementation="def crawl(): pass",
        description="A test crawler",
    )
    
    # Save strategy
    result = await sqlite_storage.save_crawler_strategy(strategy)
    assert result is True
    
    # Get strategy by ID
    retrieved_strategy = await sqlite_storage.get_crawler_strategy(strategy.id)
    assert retrieved_strategy is not None
    assert retrieved_strategy.source_id == source.id
    assert retrieved_strategy.implementation == "def crawl(): pass"
    
    # Get strategy by source ID
    retrieved_strategy_by_source = await sqlite_storage.get_crawler_strategy_by_source_id(source.id)
    assert retrieved_strategy_by_source is not None
    assert retrieved_strategy_by_source.id == strategy.id


@pytest.mark.asyncio
async def test_save_and_get_crawl_result(sqlite_storage):
    """Test saving and retrieving crawl results."""
    # Create and save test source first
    source = Source(
        url="https://github.com/example/awesome-mcp",
        name="Awesome MCP",
        type=SourceType.GITHUB_AWESOME_LIST,
        has_known_crawler=True,
    )
    await sqlite_storage.save_source(source)
    
    # Create test crawl result
    result = CrawlResult(
        source_id=source.id,
        success=True,
        tools_discovered=10,
        new_tools=5,
        updated_tools=2,
        duration=1000,
    )
    
    # Save result
    save_success = await sqlite_storage.save_crawl_result(result)
    assert save_success is True
    
    # Get results by source ID
    retrieved_results = await sqlite_storage.get_crawl_results_by_source_id(source.id)
    assert len(retrieved_results) == 1
    assert retrieved_results[0].source_id == source.id
    assert retrieved_results[0].tools_discovered == 10
    
    # Get latest result
    latest_result = await sqlite_storage.get_latest_crawl_result_by_source_id(source.id)
    assert latest_result is not None
    assert latest_result.source_id == source.id
    assert latest_result.success is True
    
    # Add another result
    another_result = CrawlResult(
        source_id=source.id,
        success=False,
        tools_discovered=0,
        new_tools=0,
        updated_tools=0,
        duration=500,
        error="Test error",
    )
    await sqlite_storage.save_crawl_result(another_result)
    
    # Get latest result again (should be the new one)
    latest_result = await sqlite_storage.get_latest_crawl_result_by_source_id(source.id)
    assert latest_result is not None
    assert latest_result.success is False
    assert latest_result.error == "Test error"

