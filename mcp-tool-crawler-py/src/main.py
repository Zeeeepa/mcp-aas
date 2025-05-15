"""
Main entry point for the MCP Tool Crawler application.
"""

import asyncio
import argparse
import json
import logging
import sys
from typing import Dict, Any, List, Optional

from .services.crawler.crawler_manager import CrawlerManager
from .services.crawler.crawler_generator import CrawlerGenerator
from .services.crawler.crawler_executor import CrawlerExecutor
from .services.source_initializer import SourceInitializer
from .utils.logging import setup_logging
from .utils.config import get_config

# Setup logging
logger = setup_logging(__name__)
config = get_config()

async def initialize_sources(source_file_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Initialize sources from configuration or storage.
    
    Args:
        source_file_path: Optional path to a source file to load.
                         If None, uses the default configuration.
        
    Returns:
        Dictionary with the result of the operation.
    """
    source_initializer = SourceInitializer()
    return await source_initializer.initialize_sources(source_file_path)

async def get_sources_to_crawl(time_threshold_hours: int = 24) -> Dict[str, Any]:
    """
    Get sources that need to be crawled.
    
    Args:
        time_threshold_hours: Time threshold in hours. Sources that haven't been
                              crawled in this period will be returned.
        
    Returns:
        Dictionary with status code and list of sources to crawl.
    """
    crawler_manager = CrawlerManager()
    return await crawler_manager.get_sources_to_crawl(time_threshold_hours)

async def crawl_source(source_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Crawl a specific source.
    
    Args:
        source_data: Dictionary containing source information.
        
    Returns:
        Dictionary with status code and crawl results.
    """
    crawler_manager = CrawlerManager()
    return await crawler_manager.crawl_source(source_data)

async def crawl_all_sources(force: bool = False, concurrency: Optional[int] = None) -> Dict[str, Any]:
    """
    Crawl all sources that need to be crawled.
    
    Args:
        force: If True, crawl all sources regardless of when they were last crawled.
        concurrency: Maximum number of sources to crawl concurrently.
                     If None, uses the value from configuration.
                     
    Returns:
        Dictionary with status code and crawl results.
    """
    crawler_manager = CrawlerManager()
    return await crawler_manager.crawl_all_sources(force, concurrency)

async def generate_crawler(source_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate a crawler strategy for a source.
    
    Args:
        source_data: Dictionary containing source information.
        
    Returns:
        Dictionary with status code and crawler strategy.
    """
    crawler_generator = CrawlerGenerator()
    return crawler_generator.process_source(source_data)

async def run_crawler(source_data: Dict[str, Any], strategy_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Run a crawler strategy for a source.
    
    Args:
        source_data: Dictionary containing source information.
        strategy_data: Dictionary containing crawler strategy information.
        
    Returns:
        Dictionary with status code and discovered tools.
    """
    crawler_executor = CrawlerExecutor()
    return crawler_executor.process_crawler_execution(source_data, strategy_data)

def parse_args():
    """
    Parse command line arguments.
    
    Returns:
        Parsed arguments.
    """
    parser = argparse.ArgumentParser(description='MCP Tool Crawler')
    
    # Create subparsers for different commands
    subparsers = parser.add_subparsers(dest='command', help='Command to run')
    
    # Initialize sources command
    init_parser = subparsers.add_parser('init', help='Initialize sources')
    init_parser.add_argument('--source-file', help='Path to source file')
    
    # Get sources to crawl command
    get_sources_parser = subparsers.add_parser('get-sources', help='Get sources to crawl')
    get_sources_parser.add_argument('--threshold', type=int, default=24, help='Time threshold in hours')
    
    # Crawl source command
    crawl_source_parser = subparsers.add_parser('crawl-source', help='Crawl a specific source')
    crawl_source_parser.add_argument('--source-id', required=True, help='ID of the source to crawl')
    crawl_source_parser.add_argument('--source-url', required=True, help='URL of the source to crawl')
    crawl_source_parser.add_argument('--source-name', required=True, help='Name of the source to crawl')
    crawl_source_parser.add_argument('--source-type', required=True, help='Type of the source to crawl')
    
    # Crawl all sources command
    crawl_all_parser = subparsers.add_parser('crawl-all', help='Crawl all sources')
    crawl_all_parser.add_argument('--force', action='store_true', help='Force crawl all sources')
    crawl_all_parser.add_argument('--concurrency', type=int, help='Maximum number of sources to crawl concurrently')
    
    # Generate crawler command
    generate_parser = subparsers.add_parser('generate', help='Generate a crawler strategy')
    generate_parser.add_argument('--source-id', required=True, help='ID of the source to generate a crawler for')
    generate_parser.add_argument('--source-url', required=True, help='URL of the source to generate a crawler for')
    generate_parser.add_argument('--source-name', required=True, help='Name of the source to generate a crawler for')
    generate_parser.add_argument('--source-type', required=True, help='Type of the source to generate a crawler for')
    
    # Run crawler command
    run_parser = subparsers.add_parser('run', help='Run a crawler strategy')
    run_parser.add_argument('--source-id', required=True, help='ID of the source to crawl')
    run_parser.add_argument('--source-url', required=True, help='URL of the source to crawl')
    run_parser.add_argument('--source-name', required=True, help='Name of the source to crawl')
    run_parser.add_argument('--source-type', required=True, help='Type of the source to crawl')
    run_parser.add_argument('--strategy-id', required=True, help='ID of the crawler strategy to run')
    run_parser.add_argument('--strategy-file', required=True, help='Path to the crawler strategy file')
    
    return parser.parse_args()

async def main():
    """
    Main entry point for the application.
    """
    args = parse_args()
    
    if args.command == 'init':
        result = await initialize_sources(args.source_file)
        print(json.dumps(result, indent=2))
    
    elif args.command == 'get-sources':
        result = await get_sources_to_crawl(args.threshold)
        print(json.dumps(result, indent=2))
    
    elif args.command == 'crawl-source':
        source_data = {
            'id': args.source_id,
            'url': args.source_url,
            'name': args.source_name,
            'type': args.source_type,
        }
        result = await crawl_source(source_data)
        print(json.dumps(result, indent=2))
    
    elif args.command == 'crawl-all':
        result = await crawl_all_sources(args.force, args.concurrency)
        print(json.dumps(result, indent=2))
    
    elif args.command == 'generate':
        source_data = {
            'id': args.source_id,
            'url': args.source_url,
            'name': args.source_name,
            'type': args.source_type,
        }
        result = await generate_crawler(source_data)
        print(json.dumps(result, indent=2))
    
    elif args.command == 'run':
        source_data = {
            'id': args.source_id,
            'url': args.source_url,
            'name': args.source_name,
            'type': args.source_type,
        }
        
        # Load strategy from file
        with open(args.strategy_file, 'r') as f:
            strategy_data = json.load(f)
        
        result = await run_crawler(source_data, strategy_data)
        print(json.dumps(result, indent=2))
    
    else:
        print("No command specified. Use --help for usage information.")
        sys.exit(1)

if __name__ == '__main__':
    asyncio.run(main())

