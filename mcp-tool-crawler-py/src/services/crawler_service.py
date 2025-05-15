"""
Crawler orchestration service for MCP tool crawler.
"""

import asyncio
from typing import List, Dict, Any, Optional

from ..models import Source, MCPTool, CrawlResult
from ..crawlers import get_crawler_for_source
from ..utils.logging import get_logger
from ..utils.config import get_config
from . import get_source_manager
from ..storage import get_storage

logger = get_logger(__name__)
config = get_config()


class CrawlerService:
    """
    Service for orchestrating the crawling process.
    """
    
    def __init__(self):
        """
        Initialize the crawler service.
        """
        self.source_manager = get_source_manager()
        self.storage = get_storage()
    
    async def crawl_source(self, source: Source) -> CrawlResult:
        """
        Crawl a specific source.
        
        Args:
            source: Source to crawl.
            
        Returns:
            A CrawlResult object.
        """
        logger.info(f"Crawling source: {source.name} ({source.url})")
        
        try:
            # Get the appropriate crawler for this source
            crawler = get_crawler_for_source(source)
            
            # Execute the crawler
            result = crawler.execute()
            
            # Update the source's last crawl time
            await self.source_manager.update_source_last_crawl(source.id, result.success)
            
            return result
        except Exception as e:
            logger.error(f"Error crawling source {source.name}: {str(e)}")
            
            # Update the source's last crawl time
            await self.source_manager.update_source_last_crawl(source.id, False)
            
            # Return a failure result
            return CrawlResult(
                source_id=source.id,
                success=False,
                tools_discovered=0,
                new_tools=0,
                updated_tools=0,
                duration=0,
                error=str(e)
            )
    
    async def crawl_all_sources(self, force: bool = False, 
                               concurrency: int = None) -> List[CrawlResult]:
        """
        Crawl all sources that need to be crawled.
        
        Args:
            force: If True, crawl all sources regardless of when they were last crawled.
            concurrency: Maximum number of sources to crawl concurrently.
                         If None, uses the value from configuration.
                         
        Returns:
            List of CrawlResult objects.
        """
        # Use concurrency limit from config if not specified
        if concurrency is None:
            concurrency = config['crawler']['concurrency_limit']
        
        # Get sources to crawl
        sources = await self.source_manager.get_all_sources() if force else await self.source_manager.get_sources_to_crawl()
        
        if not sources:
            logger.info("No sources to crawl")
            return []
        
        logger.info(f"Crawling {len(sources)} sources with concurrency {concurrency}")
        
        # Create tasks for each source
        tasks = []
        semaphore = asyncio.Semaphore(concurrency)
        
        async def crawl_with_semaphore(source):
            async with semaphore:
                return await self.crawl_source(source)
        
        for source in sources:
            tasks.append(crawl_with_semaphore(source))
        
        # Run all tasks concurrently with limited concurrency
        results = await asyncio.gather(*tasks)
        
        # Calculate totals
        total_tools = sum(result.tools_discovered for result in results if result.success)
        total_new_tools = sum(result.new_tools for result in results if result.success)
        total_updated_tools = sum(result.updated_tools for result in results if result.success)
        success_count = sum(1 for result in results if result.success)
        
        logger.info(f"Completed crawling {len(sources)} sources:")
        logger.info(f"- Success: {success_count}")
        logger.info(f"- Failed: {len(sources) - success_count}")
        logger.info(f"- Total tools discovered: {total_tools}")
        logger.info(f"- New tools: {total_new_tools}")
        logger.info(f"- Updated tools: {total_updated_tools}")
        
        return results
