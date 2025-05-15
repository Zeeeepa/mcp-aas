"""
Tests for the LocalStorage implementation.
"""
import os
import json
import pytest
from pathlib import Path

from src.models import MCPTool
from src.storage.local_storage import LocalStorage


class TestLocalStorage:
    """Test the LocalStorage implementation."""
    
    @pytest.mark.asyncio
    async def test_initialization(self, temp_file_path):
        """Test initializing the LocalStorage."""
        # Create storage with a specific file path
        storage = LocalStorage(file_path=temp_file_path)
        
        # Check that the directory was created
        assert os.path.exists(os.path.dirname(temp_file_path))
        
        # The file itself should not exist until we save something
        assert not os.path.exists(temp_file_path)
    
    @pytest.mark.asyncio
    async def test_save_and_load_tools(self, temp_file_path):
        """Test saving and loading tools."""
        # Create storage
        storage = LocalStorage(file_path=temp_file_path)
        
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
        result = await storage.save_tools(tools)
        assert result is True
        
        # Check that the file was created
        assert os.path.exists(temp_file_path)
        
        # Load tools
        loaded_tools = await storage.load_tools()
        
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
    async def test_load_tools_nonexistent_file(self, temp_dir_path):
        """Test loading tools from a nonexistent file."""
        # Create a path to a file that doesn't exist
        file_path = os.path.join(temp_dir_path, "nonexistent.json")
        
        # Create storage
        storage = LocalStorage(file_path=file_path)
        
        # Load tools
        loaded_tools = await storage.load_tools()
        
        # Check that an empty list was returned
        assert loaded_tools == []
    
    @pytest.mark.asyncio
    async def test_load_tools_invalid_json(self, temp_file_path):
        """Test loading tools from a file with invalid JSON."""
        # Create a file with invalid JSON
        with open(temp_file_path, "w") as f:
            f.write("This is not valid JSON")
        
        # Create storage
        storage = LocalStorage(file_path=temp_file_path)
        
        # Load tools
        loaded_tools = await storage.load_tools()
        
        # Check that an empty list was returned
        assert loaded_tools == []
    
    @pytest.mark.asyncio
    async def test_save_tools_directory_creation(self, temp_dir_path):
        """Test that saving tools creates the directory if it doesn't exist."""
        # Create a path to a file in a subdirectory that doesn't exist
        subdir = os.path.join(temp_dir_path, "subdir")
        file_path = os.path.join(subdir, "tools.json")
        
        # Create storage
        storage = LocalStorage(file_path=file_path)
        
        # Create a tool
        tool = MCPTool(
            id="test-tool",
            name="Test Tool",
            description="Test Description",
            url="https://example.com/tool",
            source_url="https://example.com"
        )
        
        # Save the tool
        result = await storage.save_tools([tool])
        assert result is True
        
        # Check that the directory was created
        assert os.path.exists(subdir)
        
        # Check that the file was created
        assert os.path.exists(file_path)
    
    @pytest.mark.asyncio
    async def test_save_tools_file_content(self, temp_file_path):
        """Test the content of the file after saving tools."""
        # Create storage
        storage = LocalStorage(file_path=temp_file_path)
        
        # Create a tool with specific values
        tool = MCPTool(
            id="test-tool-id",
            name="Test Tool",
            description="Test Description",
            url="https://example.com/tool",
            source_url="https://example.com",
            metadata={"tags": ["test", "example"]}
        )
        
        # Save the tool
        await storage.save_tools([tool])
        
        # Read the file content
        with open(temp_file_path, "r") as f:
            content = json.load(f)
        
        # Check that the content is correct
        assert len(content) == 1
        assert content[0]["id"] == "test-tool-id"
        assert content[0]["name"] == "Test Tool"
        assert content[0]["description"] == "Test Description"
        assert content[0]["url"] == "https://example.com/tool"
        assert content[0]["source_url"] == "https://example.com"
        assert content[0]["metadata"]["tags"] == ["test", "example"]

