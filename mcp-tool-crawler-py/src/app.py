"""
Main application module for MCP tool crawler.
Provides a simplified interface for running the crawler locally.
"""

import asyncio
import argparse
import sys
from typing import List, Dict, Any, Optional

from .models import Source, SourceType
from .crawler import CrawlerService
from .source_manager import SourceManager
from .utils.logging import get_logger

logger = get_logger(__name__)


async def list_sources():
    """List all sources."""
    source_manager = SourceManager()
    sources = await source_manager.get_all_sources()
    
    if not sources:
        print("No sources found")
        return
    
    print("\nAvailable Sources:")
    print("-" * 80)
    print(f"{'ID':<36} {'Name':<30} {'Type':<20} {'URL'}")
    print("-" * 80)
    
    for source in sources:
        print(f"{source.id:<36} {source.name:<30} {source.type.value:<20} {source.url}")
    
    print("-" * 80)
    print(f"Total: {len(sources)} sources")


async def add_source(url, name=None, source_type=None):
    """Add a new source."""
    source_manager = SourceManager()
    
    # Convert string source type to enum if provided
    if source_type and isinstance(source_type, str):
        try:
            source_type = SourceType(source_type.lower())
        except ValueError:
            valid_types = ", ".join([t.value for t in SourceType])
            print(f"Invalid source type: {source_type}")
            print(f"Valid types: {valid_types}")
            return
    
    # Add the source
    source = await source_manager.add_source_by_url(url, name, source_type)
    if source:
        print(f"Added source: {source.name} ({source.url}) with ID {source.id}")
    else:
        print(f"Failed to add source: {url}")
    return source


async def crawl_source(source_id):
    """Crawl a specific source by ID."""
    source_manager = SourceManager()
    crawler_service = CrawlerService()
    
    # Get all sources
    sources = await source_manager.get_all_sources()
    
    # Find the source by ID
    source = next((s for s in sources if s.id == source_id), None)
    
    if not source:
        print(f"Source with ID {source_id} not found")
        return
    
    print(f"Crawling source: {source.name} ({source.url})")
    
    # Crawl the source
    result = await crawler_service.crawl_source(source)
    
    if result.success:
        print(f"Crawl completed successfully:")
        print(f"- Tools discovered: {result.tools_discovered}")
        print(f"- New tools: {result.new_tools}")
        print(f"- Updated tools: {result.updated_tools}")
        print(f"- Duration: {result.duration} ms")
    else:
        print(f"Crawl failed: {result.error}")


async def crawl_all(force=False, concurrency=None):
    """Crawl all sources that need to be crawled."""
    source_manager = SourceManager()
    crawler_service = CrawlerService()
    
    # Initialize sources
    sources = await source_manager.initialize_sources()
    
    # Crawl all sources
    print(f"Crawling all sources (force={force}, concurrency={concurrency or 'default'})")
    results = await crawler_service.crawl_all_sources(sources, force)
    
    if not results:
        print("No sources crawled")
        return
    
    # Calculate summary
    success_count = sum(1 for result in results if result.success)
    failure_count = len(results) - success_count
    total_tools = sum(result.tools_discovered for result in results if result.success)
    new_tools = sum(result.new_tools for result in results if result.success)
    updated_tools = sum(result.updated_tools for result in results if result.success)
    
    print("\nCrawl Summary:")
    print("-" * 80)
    print(f"Total sources: {len(results)}")
    print(f"Successful: {success_count}")
    print(f"Failed: {failure_count}")
    print(f"Total tools discovered: {total_tools}")
    print(f"New tools: {new_tools}")
    print(f"Updated tools: {updated_tools}")
    print("-" * 80)
    
    if failure_count > 0:
        print("\nFailed Sources:")
        for result in results:
            if not result.success:
                source = next((s for s in sources if s.id == result.source_id), None)
                if source:
                    print(f"- {source.name} ({source.url}): {result.error}")


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="MCP Tool Crawler")
    
    # Create subparsers for commands
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Initialize command
    init_parser = subparsers.add_parser("init", help="Initialize sources")
    
    # List command
    list_parser = subparsers.add_parser("list", help="List all sources")
    
    # Add command
    add_parser = subparsers.add_parser("add", help="Add a new source")
    add_parser.add_argument("url", help="URL of the source")
    add_parser.add_argument("--name", help="Name of the source")
    add_parser.add_argument("--type", help="Type of the source (github_awesome_list, github_repository, website, rss_feed, manually_added)")
    
    # Crawl command
    crawl_parser = subparsers.add_parser("crawl", help="Crawl sources")
    crawl_parser.add_argument("--id", help="ID of the source to crawl")
    crawl_parser.add_argument("--all", action="store_true", help="Crawl all sources")
    crawl_parser.add_argument("--force", action="store_true", help="Force crawl all sources")
    crawl_parser.add_argument("--concurrency", type=int, help="Maximum number of sources to crawl concurrently")
    
    return parser.parse_args()


async def main_async():
    """Async entry point for the application."""
    args = parse_args()
    
    if args.command == "init":
        source_manager = SourceManager()
        sources = await source_manager.initialize_sources()
        print(f"Initialized {len(sources)} sources")
    elif args.command == "list":
        await list_sources()
    elif args.command == "add":
        await add_source(args.url, args.name, args.type)
    elif args.command == "crawl":
        if args.id:
            await crawl_source(args.id)
        elif args.all:
            await crawl_all(args.force, args.concurrency)
        else:
            print("Please specify either --id or --all")
    else:
        print("Please specify a command")


def main():
    """Entry point for the application."""
    asyncio.run(main_async())


if __name__ == "__main__":
    main()

