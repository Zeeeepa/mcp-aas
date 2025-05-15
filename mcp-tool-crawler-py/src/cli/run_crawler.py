#!/usr/bin/env python3
"""
CLI script to run the MCP tool crawler.

This script replaces the S3 event handler with a local CLI command.
"""

import argparse
import asyncio
import logging
import os
import sys
from pathlib import Path

# Add the parent directory to sys.path to import from the src directory
sys.path.append(str(Path(__file__).parents[2]))

from src.services.workflow_orchestrator import WorkflowOrchestrator
from src.utils.logging import setup_logging

# Setup logging
logger = setup_logging(__name__)


async def run_crawler(source_list_path=None, time_threshold=24):
    """
    Run the MCP tool crawler.
    
    Args:
        source_list_path: Path to the source list file. If None, uses the default path.
        time_threshold: Time threshold in hours. Sources that haven't been crawled
                        in this period will be crawled.
    """
    logger.info("Starting MCP tool crawler")
    
    # Create the workflow orchestrator
    orchestrator = WorkflowOrchestrator()
    
    # Set up the input data
    input_data = {
        'timeThreshold': time_threshold
    }
    
    if source_list_path:
        input_data['sourceListPath'] = source_list_path
    
    # Start the workflow execution
    result = await orchestrator.start_execution(
        workflow_name="mcp-tool-crawler",
        input_data=input_data
    )
    
    logger.info(f"Started workflow execution: {result['executionId']}")
    
    # Wait for the workflow to complete
    while True:
        # Get the execution status
        execution = orchestrator.get_execution(result['executionId'])
        
        if execution['status'] in ['SUCCEEDED', 'FAILED', 'ABORTED']:
            logger.info(f"Workflow execution completed with status: {execution['status']}")
            
            if execution['status'] == 'SUCCEEDED':
                logger.info("Crawler completed successfully")
                return 0
            else:
                logger.error(f"Crawler failed: {execution.get('error', 'Unknown error')}")
                return 1
        
        # Wait before checking again
        await asyncio.sleep(1)


def main():
    """Main entry point for the CLI script."""
    parser = argparse.ArgumentParser(description="Run the MCP tool crawler")
    parser.add_argument(
        "--source-list",
        help="Path to the source list file. If not provided, uses the default path."
    )
    parser.add_argument(
        "--time-threshold",
        type=int,
        default=24,
        help="Time threshold in hours. Sources that haven't been crawled in this period will be crawled."
    )
    
    args = parser.parse_args()
    
    # Run the crawler
    return asyncio.run(run_crawler(args.source_list, args.time_threshold))


if __name__ == "__main__":
    sys.exit(main())

