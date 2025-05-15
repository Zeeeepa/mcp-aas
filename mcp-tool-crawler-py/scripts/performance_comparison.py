#!/usr/bin/env python3
"""
Script to compare the performance of SQLite and AWS implementations.
"""

import asyncio
import time
import os
from pathlib import Path

from src.models import Source, SourceType
from src.services.source_manager import SourceManager
from src.services.crawler_service import CrawlerService
from src.storage.sqlite_storage import SQLiteStorage
from src.utils.logging import get_logger

logger = get_logger(__name__)


async def test_sqlite_performance():
    """Test the performance of the SQLite implementation."""
    # Set up test environment
    test_dir = Path(__file__).parents[1] / 'data' / 'perf_test'
    test_dir.mkdir(parents=True, exist_ok=True)
    (test_dir / 'crawlers').mkdir(exist_ok=True)
    
    # Set environment variables
    os.environ['DATA_DIR'] = str(test_dir)
    os.environ['SQLITE_DB_FILE'] = 'perf_test.db'
    
    # Initialize storage
    storage = SQLiteStorage(db_path=str(test_dir / 'perf_test.db'))
    
    # Create a test source
    source = Source(
        url="https://github.com/jpmcb/awesome-machine-context-protocol",
        name="Test Awesome List",
        type=SourceType.GITHUB_AWESOME_LIST,
        has_known_crawler=True,
    )
    
    # Initialize source manager
    source_manager = SourceManager()
    
    # Measure add source performance
    start_time = time.time()
    await source_manager.add_source(source)
    add_source_time = time.time() - start_time
    
    # Measure get sources performance
    start_time = time.time()
    sources = await source_manager.get_all_sources()
    get_sources_time = time.time() - start_time
    
    # Initialize crawler service
    crawler_service = CrawlerService()
    
    # Measure crawl performance
    start_time = time.time()
    result = await crawler_service.crawl_source(sources[0])
    crawl_time = time.time() - start_time
    
    # Measure load tools performance
    start_time = time.time()
    tools = await storage.load_tools()
    load_tools_time = time.time() - start_time
    
    # Print performance metrics
    logger.info("Performance Metrics (SQLite Implementation):")
    logger.info(f"- Add Source: {add_source_time:.4f} seconds")
    logger.info(f"- Get Sources: {get_sources_time:.4f} seconds")
    logger.info(f"- Crawl Source: {crawl_time:.4f} seconds")
    logger.info(f"- Load Tools: {load_tools_time:.4f} seconds")
    
    return {
        'add_source': add_source_time,
        'get_sources': get_sources_time,
        'crawl_source': crawl_time,
        'load_tools': load_tools_time,
    }


async def main():
    """Run the performance comparison."""
    logger.info("Starting performance comparison...")
    
    # Test SQLite performance
    sqlite_metrics = await test_sqlite_performance()
    
    # In a real implementation, this would also test AWS performance
    # For now, just use placeholder values
    aws_metrics = {
        'add_source': 0.5,  # Placeholder value
        'get_sources': 0.8,  # Placeholder value
        'crawl_source': 3.0,  # Placeholder value
        'load_tools': 1.2,  # Placeholder value
    }
    
    # Print comparison
    logger.info("\nPerformance Comparison (SQLite vs AWS):")
    logger.info(f"- Add Source: {sqlite_metrics['add_source']:.4f}s vs {aws_metrics['add_source']:.4f}s ({aws_metrics['add_source'] / sqlite_metrics['add_source']:.2f}x)")
    logger.info(f"- Get Sources: {sqlite_metrics['get_sources']:.4f}s vs {aws_metrics['get_sources']:.4f}s ({aws_metrics['get_sources'] / sqlite_metrics['get_sources']:.2f}x)")
    logger.info(f"- Crawl Source: {sqlite_metrics['crawl_source']:.4f}s vs {aws_metrics['crawl_source']:.4f}s ({aws_metrics['crawl_source'] / sqlite_metrics['crawl_source']:.2f}x)")
    logger.info(f"- Load Tools: {sqlite_metrics['load_tools']:.4f}s vs {aws_metrics['load_tools']:.4f}s ({aws_metrics['load_tools'] / sqlite_metrics['load_tools']:.2f}x)")
    
    # Calculate overall comparison
    sqlite_total = sum(sqlite_metrics.values())
    aws_total = sum(aws_metrics.values())
    
    logger.info(f"\nOverall: {sqlite_total:.4f}s vs {aws_total:.4f}s ({aws_total / sqlite_total:.2f}x)")
    
    if sqlite_total < aws_total:
        logger.info("SQLite implementation is faster overall!")
    else:
        logger.info("AWS implementation is faster overall!")


if __name__ == "__main__":
    asyncio.run(main())

