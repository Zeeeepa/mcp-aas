"""
Unit tests for the SQLite storage module.
"""

import os
import pytest
import tempfile
import sqlite3
from pathlib import Path

from src.models import MCPTool, Source, SourceType
from src.storage.sqlite_storage import SQLiteStorage, SQLiteSourceStorage


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
def sample_tools():
    """Create sample tools for testing."""
    return [
        MCPTool(
            name="Test Tool 1",
            description="A test tool",
            url="https://example.com/tool1",
            source_url="https://github.com/example/awesome-list",
        ),
        MCPTool(
            name="Test Tool 2",
            description="Another test tool",
            url="https://example.com/tool2",
            source_url="https://github.com/example/awesome-list",
        ),
    ]


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


@pytest.mark.asyncio
async def test_sqlite_storage_save_and_load_tools(temp_db_path, sample_tools):
    """Test saving and loading tools with SQLite storage."""
    # Initialize storage
    storage = SQLiteStorage(db_path=temp_db_path)
    
    # Save tools
    result = await storage.save_tools(sample_tools)
    assert result is True
    
    # Load tools
    loaded_tools = await storage.load_tools()
    assert len(loaded_tools) == len(sample_tools)
    
    # Check that the tools were saved correctly
    for i, tool in enumerate(loaded_tools):
        assert tool.name == sample_tools[i].name
        assert tool.description == sample_tools[i].description
        assert tool.url == sample_tools[i].url
        assert tool.source_url == sample_tools[i].source_url


@pytest.mark.asyncio
async def test_sqlite_source_storage_save_and_load_sources(temp_db_path, temp_sources_file_path, sample_sources):
    """Test saving and loading sources with SQLite source storage."""
    # Initialize storage
    storage = SQLiteSourceStorage(db_path=temp_db_path, sources_file_path=temp_sources_file_path)
    
    # Save sources
    result = await storage.save_sources(sample_sources)
    assert result is True
    
    # Load sources
    loaded_sources = await storage.load_sources()
    assert len(loaded_sources) == len(sample_sources)
    
    # Check that the sources were saved correctly
    for i, source in enumerate(loaded_sources):
        assert source.url == sample_sources[i].url
        assert source.name == sample_sources[i].name
        assert source.type == sample_sources[i].type
        assert source.has_known_crawler == sample_sources[i].has_known_crawler


@pytest.mark.asyncio
async def test_sqlite_storage_update_existing_tool(temp_db_path, sample_tools):
    """Test updating an existing tool with SQLite storage."""
    # Initialize storage
    storage = SQLiteStorage(db_path=temp_db_path)
    
    # Save tools
    await storage.save_tools(sample_tools)
    
    # Modify a tool
    modified_tool = sample_tools[0]
    modified_tool.description = "Updated description"
    
    # Save the modified tool
    await storage.save_tools([modified_tool])
    
    # Load tools
    loaded_tools = await storage.load_tools()
    
    # Check that the tool was updated
    updated_tool = next((t for t in loaded_tools if t.id == modified_tool.id), None)
    assert updated_tool is not None
    assert updated_tool.description == "Updated description"


@pytest.mark.asyncio
async def test_sqlite_source_storage_update_existing_source(temp_db_path, sample_sources):
    """Test updating an existing source with SQLite source storage."""
    # Initialize storage
    storage = SQLiteSourceStorage(db_path=temp_db_path)
    
    # Save sources
    await storage.save_sources(sample_sources)
    
    # Modify a source
    modified_source = sample_sources[0]
    modified_source.name = "Updated Name"
    
    # Save the modified source
    await storage.save_sources([modified_source])
    
    # Load sources
    loaded_sources = await storage.load_sources()
    
    # Check that the source was updated
    updated_source = next((s for s in loaded_sources if s.id == modified_source.id), None)
    assert updated_source is not None
    assert updated_source.name == "Updated Name"
"""

