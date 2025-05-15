"""
Module for running generated crawlers.
"""

import importlib.util
import os
import sys
import time
import uuid
from typing import Dict, Any, List, Optional

from ..models import Source, MCPTool, CrawlResult
from ..utils.logging import get_logger
from ..utils.config import get_config
from .crawler_generator import load_crawler_from_file, generate_crawler_for_source, save_crawler_to_file

logger = get_logger(__name__)
config = get_config()


async def run_crawler(source: Source) -> CrawlResult:
    """
    Run a crawler for a source.
    
    Args:
        source: Source to run the crawler for.
        
    Returns:
        CrawlResult object with the results of the crawl.
    """
    logger.info(f"Running crawler for source: {source.name} ({source.url})")
    
    start_time = time.time()
    
    try:
        # Load existing crawler or generate a new one
        crawler_code = load_crawler_from_file(source.id)
        
        if not crawler_code:
            # Generate a new crawler
            crawler_code = generate_crawler_for_source(source)
            
            if not crawler_code:
                return CrawlResult(
                    source_id=source.id,
                    success=False,
                    tools_discovered=0,
                    new_tools=0,
                    updated_tools=0,
                    duration=int((time.time() - start_time) * 1000),
                    error="Failed to generate crawler"
                )
            
            # Save the crawler
            save_crawler_to_file(source.id, crawler_code)
        
        # Create a temporary module for the crawler
        spec = importlib.util.spec_from_loader(
            f"crawler_{source.id}",
            loader=importlib.machinery.SourceFileLoader(
                f"crawler_{source.id}",
                os.path.join(config['local']['data_dir'], 'crawlers', f"{source.id}.py")
            )
        )
        
        crawler_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(crawler_module)
        
        # Run the crawler
        raw_tools = crawler_module.crawl()
        
        # Convert raw tools to MCPTool objects
        tools = []
        for raw_tool in raw_tools:
            # Generate a unique ID for the tool
            tool_id = str(uuid.uuid4())
            
            # Create MCPTool object
            tool = MCPTool(
                id=tool_id,
                name=raw_tool['name'],
                description=raw_tool.get('description', ''),
                url=raw_tool['url'],
                source_url=raw_tool['source_url'],
                source_id=source.id,
            )
            
            tools.append(tool)
        
        # Save tools to storage
        from ..storage import get_storage
        storage = get_storage()
        
        # Load existing tools
        existing_tools = await storage.load_tools()
        existing_tool_urls = {tool.url: tool for tool in existing_tools}
        
        # Count new and updated tools
        new_tools = 0
        updated_tools = 0
        
        for tool in tools:
            if tool.url in existing_tool_urls:
                # Update existing tool
                existing_tool = existing_tool_urls[tool.url]
                tool.id = existing_tool.id  # Keep the same ID
                updated_tools += 1
            else:
                # New tool
                new_tools += 1
        
        # Save tools
        await storage.save_tools(tools)
        
        # Return result
        return CrawlResult(
            source_id=source.id,
            success=True,
            tools_discovered=len(tools),
            new_tools=new_tools,
            updated_tools=updated_tools,
            duration=int((time.time() - start_time) * 1000),
        )
    except Exception as e:
        logger.error(f"Error running crawler for source {source.name}: {str(e)}")
        
        # Return failure result
        return CrawlResult(
            source_id=source.id,
            success=False,
            tools_discovered=0,
            new_tools=0,
            updated_tools=0,
            duration=int((time.time() - start_time) * 1000),
            error=str(e)
        )

