"""
File system watcher service for MCP tool crawler.

This module replaces the S3 event handler with a local file system watcher.
"""

import asyncio
import os
import time
from pathlib import Path
from typing import Callable, Dict, List, Optional, Set, Any
import logging
import json

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileSystemEvent

from ..utils.logging import get_logger
from ..utils.config import get_config
from .workflow_orchestrator import WorkflowOrchestrator

logger = get_logger(__name__)
config = get_config()


class SourceListEventHandler(FileSystemEventHandler):
    """Event handler for source list file changes."""
    
    def __init__(self, callback: Callable[[str], None], source_list_filename: str):
        """
        Initialize the event handler.
        
        Args:
            callback: Function to call when the source list file changes.
            source_list_filename: Name of the source list file to watch.
        """
        self.callback = callback
        self.source_list_filename = source_list_filename
        self.last_modified_time = 0
        self.debounce_seconds = 2  # Debounce time to avoid multiple events
    
    def on_modified(self, event: FileSystemEvent) -> None:
        """
        Handle file modification events.
        
        Args:
            event: File system event.
        """
        if not event.is_directory and Path(event.src_path).name == self.source_list_filename:
            # Check if enough time has passed since the last event
            current_time = time.time()
            if current_time - self.last_modified_time > self.debounce_seconds:
                self.last_modified_time = current_time
                logger.info(f"Source list file modified: {event.src_path}")
                self.callback(event.src_path)
    
    def on_created(self, event: FileSystemEvent) -> None:
        """
        Handle file creation events.
        
        Args:
            event: File system event.
        """
        if not event.is_directory and Path(event.src_path).name == self.source_list_filename:
            # Check if enough time has passed since the last event
            current_time = time.time()
            if current_time - self.last_modified_time > self.debounce_seconds:
                self.last_modified_time = current_time
                logger.info(f"Source list file created: {event.src_path}")
                self.callback(event.src_path)


class FileWatcher:
    """
    Service for watching file system changes.
    
    This class replaces the S3 event handler with a local file system watcher.
    """
    
    def __init__(
        self, 
        watch_dir: Optional[str] = None,
        source_list_filename: Optional[str] = None,
        workflow_orchestrator: Optional[WorkflowOrchestrator] = None
    ):
        """
        Initialize the file watcher.
        
        Args:
            watch_dir: Directory to watch for changes. If None, uses the default path.
            source_list_filename: Name of the source list file to watch. If None, uses the default name.
            workflow_orchestrator: WorkflowOrchestrator instance to use. If None, creates a new instance.
        """
        # Set up the watch directory
        if watch_dir:
            self.watch_dir = Path(watch_dir)
        else:
            self.watch_dir = Path(__file__).parents[3] / 'data'
        
        # Ensure the watch directory exists
        self.watch_dir.mkdir(parents=True, exist_ok=True)
        
        # Set up the source list filename
        self.source_list_filename = source_list_filename or 'sources.yaml'
        
        # Set up the workflow orchestrator
        self.workflow_orchestrator = workflow_orchestrator or WorkflowOrchestrator()
        
        # Set up the observer
        self.observer = Observer()
        self.event_handler = SourceListEventHandler(
            callback=self._handle_source_list_change,
            source_list_filename=self.source_list_filename
        )
    
    def start(self) -> None:
        """Start watching for file changes."""
        logger.info(f"Starting file watcher for {self.watch_dir}")
        
        # Schedule the event handler
        self.observer.schedule(self.event_handler, str(self.watch_dir), recursive=False)
        
        # Start the observer
        self.observer.start()
        
        logger.info(f"File watcher started, watching for changes to {self.source_list_filename}")
    
    def stop(self) -> None:
        """Stop watching for file changes."""
        logger.info("Stopping file watcher")
        
        # Stop the observer
        self.observer.stop()
        self.observer.join()
        
        logger.info("File watcher stopped")
    
    async def _handle_source_list_change(self, file_path: str) -> None:
        """
        Handle changes to the source list file.
        
        Args:
            file_path: Path to the changed file.
        """
        logger.info(f"Handling change to source list file: {file_path}")
        
        try:
            # Start a workflow execution
            input_data = {
                'sourceListPath': file_path,
                'timeThreshold': 24  # Default time threshold in hours
            }
            
            result = await self.workflow_orchestrator.start_execution(
                workflow_name="mcp-tool-crawler",
                input_data=input_data
            )
            
            logger.info(f"Started workflow execution: {result['executionId']}")
            
        except Exception as e:
            logger.error(f"Error handling source list change: {str(e)}")


async def run_file_watcher() -> None:
    """Run the file watcher as a standalone service."""
    # Create the file watcher
    file_watcher = FileWatcher()
    
    # Start the file watcher
    file_watcher.start()
    
    try:
        # Keep the service running
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        # Stop the file watcher on keyboard interrupt
        file_watcher.stop()


if __name__ == "__main__":
    # Run the file watcher
    asyncio.run(run_file_watcher())

