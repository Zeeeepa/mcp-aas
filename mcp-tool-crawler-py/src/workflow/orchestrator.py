"""
Local workflow orchestrator to replace AWS Step Functions.
"""

import asyncio
import time
from typing import List, Dict, Any, Optional, Callable, Awaitable
from datetime import datetime

from ..models import Source, MCPTool, CrawlerStrategy, CrawlResult
from ..utils.logging import get_logger

logger = get_logger(__name__)


class WorkflowOrchestrator:
    """
    Local workflow orchestrator to replace AWS Step Functions.
    
    This class orchestrates the execution of crawler workflows without
    relying on AWS Step Functions.
    """
    
    def __init__(self):
        """Initialize the workflow orchestrator."""
        self.tasks = {}
        self.results = {}
    
    async def run_crawler_workflow(
        self,
        source: Source,
        crawler_func: Callable[[Source], Awaitable[List[MCPTool]]],
        storage_func: Callable[[List[MCPTool]], Awaitable[bool]],
        update_source_func: Callable[[str, bool], Awaitable[bool]]
    ) -> CrawlResult:
        """
        Run a crawler workflow for a source.
        
        Args:
            source: Source to crawl.
            crawler_func: Function to call to crawl the source.
            storage_func: Function to call to store the discovered tools.
            update_source_func: Function to call to update the source's last crawl information.
            
        Returns:
            CrawlResult object with the results of the crawl.
        """
        logger.info(f"Starting crawler workflow for source: {source.name} ({source.id})")
        
        start_time = time.time()
        tools_discovered = 0
        new_tools = 0
        updated_tools = 0
        error = None
        success = False
        
        try:
            # Run the crawler
            tools = await crawler_func(source)
            tools_discovered = len(tools)
            
            if tools:
                # Store the tools
                storage_result = await storage_func(tools)
                
                if storage_result:
                    # For now, we're assuming all tools are new
                    # In a real implementation, we would compare with existing tools
                    new_tools = tools_discovered
                    success = True
                else:
                    error = "Failed to store tools"
            else:
                # No tools discovered, but not an error
                success = True
        except Exception as e:
            error = str(e)
            logger.error(f"Error in crawler workflow for source {source.id}: {error}")
        
        # Calculate duration in milliseconds
        duration = int((time.time() - start_time) * 1000)
        
        # Create crawl result
        result = CrawlResult(
            source_id=source.id,
            timestamp=datetime.now().isoformat(),
            success=success,
            tools_discovered=tools_discovered,
            new_tools=new_tools,
            updated_tools=updated_tools,
            duration=duration,
            error=error
        )
        
        # Update source's last crawl information
        await update_source_func(source.id, success)
        
        logger.info(f"Completed crawler workflow for source {source.id}: "
                   f"discovered={tools_discovered}, new={new_tools}, "
                   f"updated={updated_tools}, duration={duration}ms, "
                   f"success={success}")
        
        return result
    
    async def run_crawler_generator_workflow(
        self,
        source: Source,
        generator_func: Callable[[Source], Awaitable[CrawlerStrategy]],
        storage_func: Callable[[CrawlerStrategy], Awaitable[bool]],
        update_source_func: Callable[[str, str], Awaitable[bool]]
    ) -> CrawlerStrategy:
        """
        Run a crawler generator workflow for a source.
        
        Args:
            source: Source to generate a crawler for.
            generator_func: Function to call to generate the crawler.
            storage_func: Function to call to store the generated crawler.
            update_source_func: Function to call to update the source with the crawler ID.
            
        Returns:
            CrawlerStrategy object with the generated crawler.
        """
        logger.info(f"Starting crawler generator workflow for source: {source.name} ({source.id})")
        
        try:
            # Generate the crawler
            strategy = await generator_func(source)
            
            if strategy:
                # Store the crawler
                storage_result = await storage_func(strategy)
                
                if storage_result:
                    # Update the source with the crawler ID
                    await update_source_func(source.id, strategy.id)
                    
                    logger.info(f"Completed crawler generator workflow for source {source.id}: "
                               f"crawler_id={strategy.id}")
                    
                    return strategy
                else:
                    logger.error(f"Failed to store crawler strategy for source {source.id}")
            else:
                logger.error(f"Failed to generate crawler for source {source.id}")
        except Exception as e:
            logger.error(f"Error in crawler generator workflow for source {source.id}: {str(e)}")
        
        return None
    
    async def run_batch_crawler_workflow(
        self,
        sources: List[Source],
        get_crawler_func: Callable[[str], Awaitable[Optional[CrawlerStrategy]]],
        crawler_func: Callable[[Source, CrawlerStrategy], Awaitable[List[MCPTool]]],
        storage_func: Callable[[List[MCPTool]], Awaitable[bool]],
        update_source_func: Callable[[str, bool], Awaitable[bool]],
        save_result_func: Callable[[CrawlResult], Awaitable[bool]],
        max_concurrent: int = 5
    ) -> List[CrawlResult]:
        """
        Run crawler workflows for multiple sources concurrently.
        
        Args:
            sources: List of sources to crawl.
            get_crawler_func: Function to call to get the crawler for a source.
            crawler_func: Function to call to crawl a source with a crawler.
            storage_func: Function to call to store the discovered tools.
            update_source_func: Function to call to update a source's last crawl information.
            save_result_func: Function to call to save a crawl result.
            max_concurrent: Maximum number of concurrent crawls.
            
        Returns:
            List of CrawlResult objects with the results of the crawls.
        """
        logger.info(f"Starting batch crawler workflow for {len(sources)} sources")
        
        results = []
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def process_source(source: Source):
            async with semaphore:
                # Get the crawler for this source
                strategy = await get_crawler_func(source.id)
                
                if not strategy:
                    logger.warning(f"No crawler found for source {source.id}, skipping")
                    return None
                
                # Define a crawler function that uses the strategy
                async def run_crawler(src: Source):
                    return await crawler_func(src, strategy)
                
                # Run the crawler workflow
                result = await self.run_crawler_workflow(
                    source=source,
                    crawler_func=run_crawler,
                    storage_func=storage_func,
                    update_source_func=update_source_func
                )
                
                # Save the result
                await save_result_func(result)
                
                return result
        
        # Create tasks for each source
        tasks = [process_source(source) for source in sources]
        
        # Wait for all tasks to complete
        for task in asyncio.as_completed(tasks):
            result = await task
            if result:
                results.append(result)
        
        logger.info(f"Completed batch crawler workflow: {len(results)} sources processed")
        
        return results

