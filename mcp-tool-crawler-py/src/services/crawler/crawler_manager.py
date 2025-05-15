"""
Crawler manager service for MCP tool crawler.
Manages the crawling process for sources.
"""

import json
import asyncio
from typing import Dict, Any, List, Optional

from ...models import Source, SourceType, CrawlResult
from ...services.crawler_service import CrawlerService
from ...services.source_manager import SourceManager
from ...utils.logging import get_logger

logger = get_logger(__name__)

class CrawlerManager:
    """
    Service for managing the crawling process.
    """
    
    def __init__(self):
        """
        Initialize the crawler manager.
        """
        self.source_manager = SourceManager()
        self.crawler_service = CrawlerService()
    
    async def initialize_sources(self) -> List[Dict[str, Any]]:
        """
        Initialize sources from configuration or storage.
        
        This is a replacement for the initialize_sources_handler Lambda function.
        
        Returns:
            List of initialized sources as dictionaries.
        """
        logger.info("Initializing sources")
        
        try:
            # Initialize sources
            sources = await self.source_manager.initialize_sources()
            
            # Convert to JSON-serializable format
            sources_json = [source.dict() for source in sources]
            
            logger.info(f"Initialized {len(sources)} sources")
            
            return {
                'statusCode': 200,
                'body': sources_json,
            }
        except Exception as e:
            logger.error(f"Error initializing sources: {str(e)}")
            return {
                'statusCode': 500,
                'body': {
                    'error': str(e),
                },
            }
    
    async def get_sources_to_crawl(self, time_threshold_hours: int = 24) -> Dict[str, Any]:
        """
        Get sources that need to be crawled.
        
        This is a replacement for the get_sources_to_crawl_handler Lambda function.
        
        Args:
            time_threshold_hours: Time threshold in hours. Sources that haven't been
                                  crawled in this period will be returned.
            
        Returns:
            Dictionary with status code and list of sources to crawl.
        """
        logger.info("Getting sources to crawl")
        
        try:
            # Get sources to crawl
            sources = await self.source_manager.get_sources_to_crawl(time_threshold_hours)
            
            # Convert to JSON-serializable format
            sources_json = [source.dict() for source in sources]
            
            logger.info(f"Found {len(sources)} sources to crawl")
            
            return {
                'statusCode': 200,
                'body': sources_json,
            }
        except Exception as e:
            logger.error(f"Error getting sources to crawl: {str(e)}")
            return {
                'statusCode': 500,
                'body': {
                    'error': str(e),
                },
            }
    
    async def crawl_source(self, source_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Crawl a specific source.
        
        This is a replacement for the crawl_source_handler Lambda function.
        
        Args:
            source_data: Dictionary containing source information.
            
        Returns:
            Dictionary with status code and crawl results.
        """
        logger.info("Crawling source")
        
        try:
            # Parse source from data
            source = Source(**source_data)
            
            # Crawl the source
            result = await self.crawler_service.crawl_source(source)
            
            # Convert to JSON-serializable format
            result_json = result.dict()
            
            logger.info(f"Crawl completed for source {source.name}: {result.tools_discovered} tools discovered")
            
            return {
                'statusCode': 200,
                'body': result_json,
            }
        except Exception as e:
            logger.error(f"Error crawling source: {str(e)}")
            return {
                'statusCode': 500,
                'body': {
                    'error': str(e),
                },
            }
    
    async def crawl_all_sources(self, force: bool = False, concurrency: Optional[int] = None) -> Dict[str, Any]:
        """
        Crawl all sources that need to be crawled.
        
        This is a replacement for the crawl_all_sources_handler Lambda function.
        
        Args:
            force: If True, crawl all sources regardless of when they were last crawled.
            concurrency: Maximum number of sources to crawl concurrently.
                         If None, uses the value from configuration.
                         
        Returns:
            Dictionary with status code and crawl results.
        """
        logger.info("Crawling all sources")
        
        try:
            # Initialize sources
            await self.source_manager.initialize_sources()
            
            # Crawl all sources
            results = await self.crawler_service.crawl_all_sources(force, concurrency)
            
            # Convert to JSON-serializable format
            results_json = [result.dict() for result in results]
            
            # Calculate summary
            success_count = sum(1 for result in results if result.success)
            total_tools = sum(result.tools_discovered for result in results if result.success)
            new_tools = sum(result.new_tools for result in results if result.success)
            updated_tools = sum(result.updated_tools for result in results if result.success)
            
            logger.info(f"Crawl all sources completed: {success_count}/{len(results)} successful")
            
            return {
                'statusCode': 200,
                'body': {
                    'results': results_json,
                    'summary': {
                        'total_sources': len(results),
                        'success_count': success_count,
                        'failure_count': len(results) - success_count,
                        'total_tools': total_tools,
                        'new_tools': new_tools,
                        'updated_tools': updated_tools,
                    },
                },
            }
        except Exception as e:
            logger.error(f"Error crawling all sources: {str(e)}")
            return {
                'statusCode': 500,
                'body': {
                    'error': str(e),
                },
            }

