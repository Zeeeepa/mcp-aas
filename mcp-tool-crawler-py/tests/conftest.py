"""Pytest configuration file."""
import os
import sys
import pytest
import tempfile
import sqlite3
from pathlib import Path

# Add the src directory to the path so we can import modules directly
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Define fixtures that can be used by tests
@pytest.fixture
def test_source_data():
    """Return test data for a Source."""
    return {
        "url": "https://github.com/awesome-mcp/awesome-list",
        "name": "Awesome MCP List",
        "type": "github_awesome_list",
        "active": True
    }

@pytest.fixture
def test_mcp_tool_data():
    """Return test data for an MCPTool."""
    return {
        "name": "Example MCP Tool",
        "url": "https://github.com/example/mcp-tool",
        "description": "An example MCP tool",
        "source_url": "https://github.com/awesome-mcp/awesome-list",
        "tags": ["ai", "test"]
    }

@pytest.fixture
def test_crawler_strategy_data():
    """Return test data for a CrawlerStrategy."""
    return {
        "name": "Example Strategy",
        "source_type": "website",
        "code": "def extract_tools(content):\n    return []",
        "version": "1.0.0"
    }

@pytest.fixture
def temp_db_path():
    """Create a temporary SQLite database file."""
    fd, path = tempfile.mkstemp(suffix='.db')
    os.close(fd)
    yield path
    os.unlink(path)

@pytest.fixture
def temp_file_path():
    """Create a temporary file."""
    fd, path = tempfile.mkstemp(suffix='.json')
    os.close(fd)
    yield path
    os.unlink(path)

@pytest.fixture
def temp_dir_path():
    """Create a temporary directory."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield temp_dir

@pytest.fixture
def sqlite_connection(temp_db_path):
    """Create a SQLite connection to a temporary database."""
    conn = sqlite3.connect(temp_db_path)
    yield conn
    conn.close()

@pytest.fixture
def sqlite_storage(temp_db_path):
    """Create a SQLiteStorage instance with a temporary database."""
    from src.storage.sqlite_storage import SQLiteStorage
    storage = SQLiteStorage(db_path=temp_db_path)
    return storage

@pytest.fixture
def local_storage(temp_file_path):
    """Create a LocalStorage instance with a temporary file."""
    from src.storage.local_storage import LocalStorage
    storage = LocalStorage(file_path=temp_file_path)
    return storage

@pytest.fixture
def source_manager(temp_db_path):
    """Create a SourceManager instance with a temporary database."""
    from src.services.source_manager_sqlite import SourceManager
    manager = SourceManager(db_path=temp_db_path)
    return manager
