"""
Crawler module to replace Lambda functions.
"""

import importlib
import inspect
import sys
from typing import List, Dict, Any, Optional, Type

from ..models import Source, MCPTool, CrawlerStrategy, SourceType
from ..utils.logging import get_logger
from ..crawlers.base import BaseCrawler

logger = get_logger(__name__)


class CrawlerModule:
    """
    Module for running crawlers without AWS Lambda.
    """
    
    @staticmethod
    async def run_crawler(source: Source, strategy: Optional[CrawlerStrategy] = None) -> List[MCPTool]:
        """
        Run a crawler for a source.
        
        Args:
            source: Source to crawl.
            strategy: Optional crawler strategy to use. If None, uses a built-in crawler.
            
        Returns:
            List of discovered tools.
        """
        logger.info(f"Running crawler for source: {source.name} ({source.id})")
        
        try:
            # If a strategy is provided, use it
            if strategy:
                return await CrawlerModule._run_dynamic_crawler(source, strategy)
            
            # Otherwise, use a built-in crawler based on the source type
            return await CrawlerModule._run_builtin_crawler(source)
        except Exception as e:
            logger.error(f"Error running crawler for source {source.id}: {str(e)}")
            return []
    
    @staticmethod
    async def _run_dynamic_crawler(source: Source, strategy: CrawlerStrategy) -> List[MCPTool]:
        """
        Run a dynamically generated crawler using a strategy.
        
        Args:
            source: Source to crawl.
            strategy: Crawler strategy to use.
            
        Returns:
            List of discovered tools.
        """
        try:
            # Create a namespace for the crawler code
            namespace = {
                'BaseCrawler': BaseCrawler,
                'Source': Source,
                'MCPTool': MCPTool,
                'SourceType': SourceType,
                'logger': logger
            }
            
            # Execute the strategy implementation in the namespace
            exec(strategy.implementation, namespace)
            
            # Find the crawler class in the namespace
            crawler_class = None
            for name, obj in namespace.items():
                if (inspect.isclass(obj) and 
                    issubclass(obj, BaseCrawler) and 
                    obj != BaseCrawler):
                    crawler_class = obj
                    break
            
            if not crawler_class:
                logger.error(f"No crawler class found in strategy for source {source.id}")
                return []
            
            # Create an instance of the crawler
            crawler = crawler_class(source)
            
            # Run the crawler
            tools = await crawler.discover_tools()
            
            logger.info(f"Dynamic crawler discovered {len(tools)} tools for source {source.id}")
            return tools
        except Exception as e:
            logger.error(f"Error running dynamic crawler for source {source.id}: {str(e)}")
            return []
    
    @staticmethod
    async def _run_builtin_crawler(source: Source) -> List[MCPTool]:
        """
        Run a built-in crawler based on the source type.
        
        Args:
            source: Source to crawl.
            
        Returns:
            List of discovered tools.
        """
        try:
            # Import the appropriate crawler based on the source type
            if source.type == SourceType.GITHUB_AWESOME_LIST:
                from ..crawlers.github_awesome_list import GitHubAwesomeListCrawler
                crawler_class = GitHubAwesomeListCrawler
            elif source.type == SourceType.GITHUB_REPOSITORY:
                # TODO: Implement GitHub repository crawler
                logger.warning(f"GitHub repository crawler not implemented yet for source {source.id}")
                return []
            elif source.type == SourceType.WEBSITE:
                # TODO: Implement website crawler
                logger.warning(f"Website crawler not implemented yet for source {source.id}")
                return []
            elif source.type == SourceType.RSS_FEED:
                # TODO: Implement RSS feed crawler
                logger.warning(f"RSS feed crawler not implemented yet for source {source.id}")
                return []
            else:
                logger.error(f"Unsupported source type for source {source.id}: {source.type}")
                return []
            
            # Create an instance of the crawler
            crawler = crawler_class(source)
            
            # Run the crawler
            tools = await crawler.discover_tools()
            
            logger.info(f"Built-in crawler discovered {len(tools)} tools for source {source.id}")
            return tools
        except Exception as e:
            logger.error(f"Error running built-in crawler for source {source.id}: {str(e)}")
            return []

