"""
Unit tests for the local storage module.
"""

import os
import json
import yaml
import shutil
import tempfile
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from src.storage.local_storage import LocalStorage, LocalSourceStorage
from src.models import MCPTool, Source, SourceType


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def mock_tool():
    """Create a mock MCPTool for testing."""
    return MCPTool(
        id="tool-123",
        name="Test Tool",
        description="A test tool",
        url="https://example.com/tool",
        source_url="https://example.com/source"
    )


@pytest.fixture
def mock_source():
    """Create a mock Source for testing."""
    return Source(
        id="source-123",
        url="https://github.com/example/awesome-mcp",
        name="Test Source",
        type=SourceType.GITHUB_AWESOME_LIST,
        has_known_crawler=True
    )


class TestLocalStorage:
    """Tests for the LocalStorage class."""

    @pytest.mark.asyncio
    async def test_save_and_load_tools(self, temp_dir, mock_tool):
        """Test saving and loading tools."""
        # Create a storage instance with a temporary file
        file_path = os.path.join(temp_dir, "tools.json")
        storage = LocalStorage(file_path)
        
        # Save a tool
        result = await storage.save_tools([mock_tool])
        assert result is True
        
        # Verify the file exists
        assert os.path.exists(file_path)
        
        # Load the tools
        loaded_tools = await storage.load_tools()
        
        # Verify the loaded tool matches the original
        assert len(loaded_tools) == 1
        assert loaded_tools[0].id == mock_tool.id
        assert loaded_tools[0].name == mock_tool.name
        assert loaded_tools[0].description == mock_tool.description
        assert loaded_tools[0].url == mock_tool.url
        assert loaded_tools[0].source_url == mock_tool.source_url

    @pytest.mark.asyncio
    async def test_backup_creation(self, temp_dir, mock_tool):
        """Test that backups are created when saving tools."""
        # Create a storage instance with a temporary file
        file_path = os.path.join(temp_dir, "tools.json")
        storage = LocalStorage(file_path)
        
        # Save a tool
        await storage.save_tools([mock_tool])
        
        # Save again to trigger backup
        await storage.save_tools([mock_tool])
        
        # Check if backup directory exists and contains a file
        backup_dir = Path(file_path).parent / 'backups' / 'tools'
        assert backup_dir.exists()
        backup_files = list(backup_dir.glob("tools_*.json"))
        assert len(backup_files) > 0

    @pytest.mark.asyncio
    async def test_recovery_from_backup(self, temp_dir, mock_tool):
        """Test recovery from backup when the main file is corrupted."""
        # Create a storage instance with a temporary file
        file_path = os.path.join(temp_dir, "tools.json")
        storage = LocalStorage(file_path)
        
        # Save a tool
        await storage.save_tools([mock_tool])
        
        # Create a backup manually
        backup_dir = Path(file_path).parent / 'backups' / 'tools'
        backup_dir.mkdir(parents=True, exist_ok=True)
        backup_path = backup_dir / "tools_12345.json"
        shutil.copy2(file_path, backup_path)
        
        # Corrupt the main file
        with open(file_path, 'w') as f:
            f.write("This is not valid JSON")
        
        # Load tools should recover from backup
        with patch('src.storage.local_storage.logger') as mock_logger:
            loaded_tools = await storage.load_tools()
            
            # Verify recovery was attempted
            mock_logger.error.assert_called()
            mock_logger.info.assert_any_call(f"Attempting recovery from backup: {backup_path}")
        
        # Verify the loaded tool matches the original
        assert len(loaded_tools) == 1
        assert loaded_tools[0].id == mock_tool.id


class TestLocalSourceStorage:
    """Tests for the LocalSourceStorage class."""

    @pytest.mark.asyncio
    async def test_save_and_load_sources(self, temp_dir, mock_source):
        """Test saving and loading sources."""
        # Create a storage instance with a temporary file
        file_path = os.path.join(temp_dir, "sources.yaml")
        
        # Mock the config
        with patch('src.storage.local_storage.config', {
            'aws': {'s3': {'source_list_key': 'sources.yaml'}}
        }):
            storage = LocalSourceStorage(file_path)
        
        # Save a source
        result = await storage.save_sources([mock_source])
        assert result is True
        
        # Verify the file exists
        assert os.path.exists(file_path)
        
        # Load the sources
        loaded_sources = await storage.load_sources()
        
        # Verify the loaded source matches the original
        assert len(loaded_sources) == 1
        assert loaded_sources[0].id == mock_source.id
        assert loaded_sources[0].url == mock_source.url
        assert loaded_sources[0].name == mock_source.name
        assert loaded_sources[0].type == mock_source.type
        assert loaded_sources[0].has_known_crawler == mock_source.has_known_crawler

    @pytest.mark.asyncio
    async def test_backup_creation_for_sources(self, temp_dir, mock_source):
        """Test that backups are created when saving sources."""
        # Create a storage instance with a temporary file
        file_path = os.path.join(temp_dir, "sources.yaml")
        
        # Mock the config
        with patch('src.storage.local_storage.config', {
            'aws': {'s3': {'source_list_key': 'sources.yaml'}}
        }):
            storage = LocalSourceStorage(file_path)
        
        # Save a source
        await storage.save_sources([mock_source])
        
        # Save again to trigger backup
        await storage.save_sources([mock_source])
        
        # Check if backup directory exists and contains a file
        backup_dir = Path(file_path).parent / 'backups' / 'sources'
        assert backup_dir.exists()
        backup_files = list(backup_dir.glob("sources_*.yaml"))
        assert len(backup_files) > 0

    @pytest.mark.asyncio
    async def test_recovery_from_backup_for_sources(self, temp_dir, mock_source):
        """Test recovery from backup when the main file is corrupted."""
        # Create a storage instance with a temporary file
        file_path = os.path.join(temp_dir, "sources.yaml")
        
        # Mock the config
        with patch('src.storage.local_storage.config', {
            'aws': {'s3': {'source_list_key': 'sources.yaml'}}
        }):
            storage = LocalSourceStorage(file_path)
        
        # Save a source
        await storage.save_sources([mock_source])
        
        # Create a backup manually
        backup_dir = Path(file_path).parent / 'backups' / 'sources'
        backup_dir.mkdir(parents=True, exist_ok=True)
        backup_path = backup_dir / "sources_12345.yaml"
        shutil.copy2(file_path, backup_path)
        
        # Corrupt the main file
        with open(file_path, 'w') as f:
            f.write("This is not valid YAML: :")
        
        # Load sources should recover from backup
        with patch('src.storage.local_storage.logger') as mock_logger:
            loaded_sources = await storage.load_sources()
            
            # Verify recovery was attempted
            mock_logger.error.assert_called()
            mock_logger.info.assert_any_call(f"Attempting recovery from backup: {backup_path}")
        
        # Verify the loaded source matches the original
        assert len(loaded_sources) == 1
        assert loaded_sources[0].id == mock_source.id

