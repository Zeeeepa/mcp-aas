"""
Unit tests for the file watcher service.
"""

import asyncio
import os
import tempfile
import unittest
from unittest.mock import patch, MagicMock

from src.services.file_watcher import FileWatcher, SourceListEventHandler


class TestSourceListEventHandler(unittest.TestCase):
    """Test cases for the SourceListEventHandler class."""
    
    def setUp(self):
        """Set up the test environment."""
        # Create a mock callback function
        self.mock_callback = MagicMock()
        
        # Create the event handler
        self.handler = SourceListEventHandler(
            callback=self.mock_callback,
            source_list_filename="sources.yaml"
        )
    
    def test_on_modified_matching_file(self):
        """Test handling a modified event for the source list file."""
        # Create a mock event
        mock_event = MagicMock()
        mock_event.is_directory = False
        mock_event.src_path = "/path/to/sources.yaml"
        
        # Handle the event
        self.handler.on_modified(mock_event)
        
        # Check that the callback was called
        self.mock_callback.assert_called_once_with("/path/to/sources.yaml")
    
    def test_on_modified_non_matching_file(self):
        """Test handling a modified event for a non-matching file."""
        # Create a mock event
        mock_event = MagicMock()
        mock_event.is_directory = False
        mock_event.src_path = "/path/to/other.yaml"
        
        # Handle the event
        self.handler.on_modified(mock_event)
        
        # Check that the callback was not called
        self.mock_callback.assert_not_called()
    
    def test_on_modified_directory(self):
        """Test handling a modified event for a directory."""
        # Create a mock event
        mock_event = MagicMock()
        mock_event.is_directory = True
        mock_event.src_path = "/path/to/sources.yaml"
        
        # Handle the event
        self.handler.on_modified(mock_event)
        
        # Check that the callback was not called
        self.mock_callback.assert_not_called()
    
    def test_on_created_matching_file(self):
        """Test handling a created event for the source list file."""
        # Create a mock event
        mock_event = MagicMock()
        mock_event.is_directory = False
        mock_event.src_path = "/path/to/sources.yaml"
        
        # Handle the event
        self.handler.on_created(mock_event)
        
        # Check that the callback was called
        self.mock_callback.assert_called_once_with("/path/to/sources.yaml")
    
    def test_on_created_non_matching_file(self):
        """Test handling a created event for a non-matching file."""
        # Create a mock event
        mock_event = MagicMock()
        mock_event.is_directory = False
        mock_event.src_path = "/path/to/other.yaml"
        
        # Handle the event
        self.handler.on_created(mock_event)
        
        # Check that the callback was not called
        self.mock_callback.assert_not_called()
    
    def test_on_created_directory(self):
        """Test handling a created event for a directory."""
        # Create a mock event
        mock_event = MagicMock()
        mock_event.is_directory = True
        mock_event.src_path = "/path/to/sources.yaml"
        
        # Handle the event
        self.handler.on_created(mock_event)
        
        # Check that the callback was not called
        self.mock_callback.assert_not_called()
    
    def test_debounce(self):
        """Test that events are debounced."""
        # Create a mock event
        mock_event = MagicMock()
        mock_event.is_directory = False
        mock_event.src_path = "/path/to/sources.yaml"
        
        # Handle the event twice in quick succession
        self.handler.on_modified(mock_event)
        self.handler.on_modified(mock_event)
        
        # Check that the callback was only called once
        self.mock_callback.assert_called_once_with("/path/to/sources.yaml")


class TestFileWatcher(unittest.TestCase):
    """Test cases for the FileWatcher class."""
    
    def setUp(self):
        """Set up the test environment."""
        # Create a temporary directory
        self.temp_dir = tempfile.TemporaryDirectory()
        
        # Create a mock workflow orchestrator
        self.mock_orchestrator = MagicMock()
        
        # Create the file watcher
        self.file_watcher = FileWatcher(
            watch_dir=self.temp_dir.name,
            source_list_filename="sources.yaml",
            workflow_orchestrator=self.mock_orchestrator
        )
    
    def tearDown(self):
        """Clean up the test environment."""
        # Clean up the temporary directory
        self.temp_dir.cleanup()
    
    @patch('src.services.file_watcher.Observer')
    def test_start(self, mock_observer_class):
        """Test starting the file watcher."""
        # Create a mock observer
        mock_observer = MagicMock()
        mock_observer_class.return_value = mock_observer
        
        # Start the file watcher
        self.file_watcher.start()
        
        # Check that the observer was started
        mock_observer.start.assert_called_once()
    
    @patch('src.services.file_watcher.Observer')
    def test_stop(self, mock_observer_class):
        """Test stopping the file watcher."""
        # Create a mock observer
        mock_observer = MagicMock()
        mock_observer_class.return_value = mock_observer
        
        # Start and then stop the file watcher
        self.file_watcher.start()
        self.file_watcher.stop()
        
        # Check that the observer was stopped
        mock_observer.stop.assert_called_once()
        mock_observer.join.assert_called_once()
    
    @patch('src.services.file_watcher.Observer')
    async def test_handle_source_list_change(self, mock_observer_class):
        """Test handling a change to the source list file."""
        # Create a mock observer
        mock_observer = MagicMock()
        mock_observer_class.return_value = mock_observer
        
        # Mock the workflow orchestrator's start_execution method
        self.mock_orchestrator.start_execution.return_value = {"executionId": "test-execution-id"}
        
        # Handle a change to the source list file
        await self.file_watcher._handle_source_list_change("/path/to/sources.yaml")
        
        # Check that the workflow orchestrator was called
        self.mock_orchestrator.start_execution.assert_called_once_with(
            workflow_name="mcp-tool-crawler",
            input_data={
                'sourceListPath': "/path/to/sources.yaml",
                'timeThreshold': 24
            }
        )


if __name__ == "__main__":
    unittest.main()

