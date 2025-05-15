"""
Unit tests for the SourceManager class.
"""

import os
import pytest
import tempfile
from datetime import datetime, timezone, timedelta
from pathlib import Path

from src.models import Source, SourceType
from src.services.source_manager import SourceManager
from src.storage.sqlite_storage import SQLiteSourceStorage


@pytest.fixture
def temp_db_path():
    """Create a temporary database file path."""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = f.name
    
    yield db_path
    
    # Clean up
    if os.path.exists(db_path):
        os.unlink(db_path)


@pytest.fixture
def temp_sources_file_path():
    """Create a temporary sources file path."""
    with tempfile.NamedTemporaryFile(suffix='.yaml', delete=False) as f:
        file_path = f.name
    
    yield file_path
    
    # Clean up
    if os.path.exists(file_path):
        os.unlink(file_path)


@pytest.fixture
def sample_sources():
    """Create sample sources for testing."""
    return [
        Source(
            url="https://github.com/example/awesome-list",
            name="Example Awesome List",
            type=SourceType.GITHUB_AWESOME_LIST,
            has_known_crawler=True,
        ),
        Source(
            url="https://example.com/tools",
            name="Example Tools Directory",
            type=SourceType.WEBSITE,
            has_known_crawler=False,
        ),
    ]


@pytest.fixture
def mock_source_manager(monkeypatch, temp_db_path, temp_sources_file_path):
    """Create a mock SourceManager with a temporary database."""
    # Mock the SQLiteSourceStorage to use our temporary paths
    def mock_init(self):
        self.db_path = temp_db_path
        self.sources_file_path = temp_sources_file_path
        self._ensure_db_exists()
    
    monkeypatch.setattr(SQLiteSourceStorage, "__init__", mock_init)
    
    # Return a SourceManager instance
    return SourceManager()


@pytest.mark.asyncio
async def test_add_source(mock_source_manager, sample_sources):
    """Test adding a source."""
    # Add a source
    source = sample_sources[0]
    added_source = await mock_source_manager.add_source(source)
    
    # Check that the source was added correctly
    assert added_source.id == source.id
    assert added_source.url == source.url
    assert added_source.name == source.name
    assert added_source.type == source.type
    
    # Get all sources and check that our source is there
    all_sources = await mock_source_manager.get_all_sources()
    assert len(all_sources) == 1
    assert all_sources[0].id == source.id


@pytest.mark.asyncio
async def test_add_source_by_url(mock_source_manager):
    """Test adding a source by URL."""
    # Add a source by URL
    url = "https://github.com/example/awesome-list"
    name = "Test Source"
    source_type = SourceType.GITHUB_AWESOME_LIST
    
    added_source = await mock_source_manager.add_source_by_url(
        url=url,
        name=name,
        source_type=source_type
    )
    
    # Check that the source was added correctly
    assert added_source.url == url
    assert added_source.name == name
    assert added_source.type == source_type
    
    # Get all sources and check that our source is there
    all_sources = await mock_source_manager.get_all_sources()
    assert len(all_sources) == 1
    assert all_sources[0].url == url


@pytest.mark.asyncio
async def test_get_sources_to_crawl(mock_source_manager, sample_sources):
    """Test getting sources to crawl."""
    # Add sources
    for source in sample_sources:
        await mock_source_manager.add_source(source)
    
    # Set last_crawled for one source to be recent
    sources = await mock_source_manager.get_all_sources()
    sources[0].last_crawled = datetime.now(timezone.utc).isoformat()
    await mock_source_manager.storage.save_sources(sources)
    
    # Set last_crawled for another source to be old
    sources = await mock_source_manager.get_all_sources()
    old_time = (datetime.now(timezone.utc) - timedelta(hours=48)).isoformat()
    sources[1].last_crawled = old_time
    await mock_source_manager.storage.save_sources(sources)
    
    # Get sources to crawl with a 24-hour threshold
    sources_to_crawl = await mock_source_manager.get_sources_to_crawl(time_threshold_hours=24)
    
    # Should only return the source with the old last_crawled time
    assert len(sources_to_crawl) == 1
    assert sources_to_crawl[0].id == sources[1].id


@pytest.mark.asyncio
async def test_update_source_last_crawl(mock_source_manager, sample_sources):
    """Test updating a source's last crawl information."""
    # Add a source
    source = sample_sources[0]
    await mock_source_manager.add_source(source)
    
    # Get the source ID
    sources = await mock_source_manager.get_all_sources()
    source_id = sources[0].id
    
    # Update the source's last crawl information
    result = await mock_source_manager.update_source_last_crawl(source_id, success=True)
    assert result is True
    
    # Check that the source was updated
    updated_sources = await mock_source_manager.get_all_sources()
    updated_source = updated_sources[0]
    assert updated_source.last_crawled is not None
    assert updated_source.last_crawl_status == "success"
    
    # Try updating a non-existent source
    result = await mock_source_manager.update_source_last_crawl("non-existent-id", success=True)
    assert result is False


@pytest.mark.asyncio
async def test_initialize_sources(mock_source_manager, sample_sources, monkeypatch):
    """Test initializing sources."""
    # Mock the storage.load_sources method to return our sample sources
    async def mock_load_sources(self):
        return sample_sources
    
    monkeypatch.setattr(SQLiteSourceStorage, "load_sources", mock_load_sources)
    
    # Initialize sources
    initialized_sources = await mock_source_manager.initialize_sources()
    
    # Check that the sources were initialized correctly
    assert len(initialized_sources) == len(sample_sources)
    for i, source in enumerate(initialized_sources):
        assert source.url == sample_sources[i].url
        assert source.name == sample_sources[i].name
        assert source.type == sample_sources[i].type
"""

