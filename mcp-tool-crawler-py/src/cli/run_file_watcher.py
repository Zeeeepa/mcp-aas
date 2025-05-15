#!/usr/bin/env python3
"""
CLI script to run the file watcher service.

This script starts a file watcher service that monitors for changes to the source list file
and triggers the crawler workflow when changes are detected.
"""

import argparse
import asyncio
import logging
import os
import sys
from pathlib import Path

# Add the parent directory to sys.path to import from the src directory
sys.path.append(str(Path(__file__).parents[2]))

from src.services.file_watcher import FileWatcher
from src.utils.logging import setup_logging

# Setup logging
logger = setup_logging(__name__)


async def run_file_watcher(watch_dir=None, source_list_filename=None):
    """
    Run the file watcher service.
    
    Args:
        watch_dir: Directory to watch for changes. If None, uses the default path.
        source_list_filename: Name of the source list file to watch. If None, uses the default name.
    """
    logger.info("Starting file watcher service")
    
    # Create the file watcher
    file_watcher = FileWatcher(
        watch_dir=watch_dir,
        source_list_filename=source_list_filename
    )
    
    # Start the file watcher
    file_watcher.start()
    
    try:
        # Keep the service running
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        # Stop the file watcher on keyboard interrupt
        file_watcher.stop()
        logger.info("File watcher service stopped")


def main():
    """Main entry point for the CLI script."""
    parser = argparse.ArgumentParser(description="Run the file watcher service")
    parser.add_argument(
        "--watch-dir",
        help="Directory to watch for changes. If not provided, uses the default path."
    )
    parser.add_argument(
        "--source-list-filename",
        default="sources.yaml",
        help="Name of the source list file to watch. Default: sources.yaml"
    )
    
    args = parser.parse_args()
    
    # Run the file watcher
    try:
        asyncio.run(run_file_watcher(args.watch_dir, args.source_list_filename))
        return 0
    except KeyboardInterrupt:
        logger.info("File watcher service stopped")
        return 0
    except Exception as e:
        logger.error(f"Error running file watcher service: {str(e)}")
        return 1


if __name__ == "__main__":
    sys.exit(main())

