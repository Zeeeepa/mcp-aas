"""
Consolidated crawler module for MCP tools.
Combines functionality from multiple crawler modules into a single file.
"""

import re
import os
import requests
import asyncio
from typing import List, Dict, Any, Optional
from enum import Enum
from datetime import datetime
from uuid import uuid4
from urllib.parse import urlparse

from .models import MCPTool, Source, SourceType, CrawlResult
from .utils.logging import get_logger
from .utils.helpers import extract_github_repo_info

logger = get_logger(__name__)


class BaseCrawler:
    """Base class for all crawlers."""
    
    def __init__(self, source: Source, user_agent: str = "MCP-Tool-Crawler/1.0"):
        self.source = source
        self.user_agent = user_agent
    
    async def crawl(self) -> CrawlResult:
        """
        Crawl the source and return the result.
        
        Returns:
            CrawlResult: The result of the crawl operation.
        """
        start_time = datetime.now()
        
        try:
            tools = self.discover_tools()
            
            # Calculate duration in milliseconds
            duration = int((datetime.now() - start_time).total_seconds() * 1000)
            
            return CrawlResult(
                source_id=self.source.id,
                success=True,
                tools_discovered=len(tools),
                new_tools=len(tools),  # Simplified - in a real app, we'd check against existing tools
                updated_tools=0,
                duration=duration
            )
        except Exception as e:
            # Calculate duration in milliseconds
            duration = int((datetime.now() - start_time).total_seconds() * 1000)
            
            logger.error(f"Error crawling source {self.source.url}: {str(e)}")
            
            return CrawlResult(
                source_id=self.source.id,
                success=False,
                tools_discovered=0,
                new_tools=0,
                updated_tools=0,
                duration=duration,
                error=str(e)
            )
    
    def discover_tools(self) -> List[MCPTool]:
        """
        Discover MCP tools from the source.
        
        Returns:
            A list of MCPTool objects.
        """
        raise NotImplementedError("Subclasses must implement discover_tools()")
    
    def is_mcp_tool(self, name: str, description: str) -> bool:
        """
        Determine if a tool is an MCP tool based on its name and description.
        
        Args:
            name: Tool name.
            description: Tool description.
            
        Returns:
            True if the tool is an MCP tool, False otherwise.
        """
        # Simple heuristic - check if name or description contains MCP-related keywords
        keywords = ["mcp", "model context protocol", "context protocol", "cursor", "code editor"]
        
        name_lower = name.lower()
        desc_lower = description.lower()
        
        for keyword in keywords:
            if keyword in name_lower or keyword in desc_lower:
                return True
        
        return False
    
    def extract_tags(self, name: str, description: str) -> List[str]:
        """
        Extract tags from a tool's name and description.
        
        Args:
            name: Tool name.
            description: Tool description.
            
        Returns:
            A list of tags.
        """
        tags = []
        
        # Extract tags based on common patterns
        tag_patterns = {
            "client": ["client", "app", "application"],
            "server": ["server", "backend", "api"],
            "library": ["library", "sdk", "package"],
            "plugin": ["plugin", "extension", "addon"],
            "tool": ["tool", "utility", "cli"],
        }
        
        text = f"{name} {description}".lower()
        
        for tag, patterns in tag_patterns.items():
            for pattern in patterns:
                if pattern in text:
                    tags.append(tag)
                    break
        
        return tags


class GitHubAwesomeListCrawler(BaseCrawler):
    """Crawler for GitHub Awesome Lists"""
    
    def discover_tools(self) -> List[MCPTool]:
        """
        Discover MCP tools from a GitHub awesome list.
        
        Returns:
            A list of MCPTool objects.
            
        Raises:
            ValueError: If the URL is not a valid GitHub repository.
        """
        # Extract repo info from URL
        repo_info = extract_github_repo_info(self.source.url)
        
        if not repo_info:
            raise ValueError(f"Invalid GitHub repository URL: {self.source.url}")
        
        owner, repo = repo_info['owner'], repo_info['repo']
        
        # Fetch README content
        readme_content = self._fetch_readme(owner, repo)
        
        # Extract tools from README
        tools = self._extract_tools_from_readme(readme_content)
        
        logger.info(f"Extracted {len(tools)} tools from {self.source.url}")
        return tools
    
    def _fetch_readme(self, owner: str, repo: str) -> str:
        """
        Fetch the README.md content from a GitHub repository.
        
        Args:
            owner: Repository owner.
            repo: Repository name.
            
        Returns:
            README content as a string.
            
        Raises:
            ValueError: If the README cannot be fetched.
        """
        # Add GitHub token if available (optional)
        headers = {
            "User-Agent": self.user_agent,
        }
        
        github_token = os.environ.get("GITHUB_TOKEN")
        if github_token:
            headers["Authorization"] = f"token {github_token}"
        
        # Try main branch first
        main_url = f"https://raw.githubusercontent.com/{owner}/{repo}/main/README.md"
        
        try:
            response = requests.get(main_url, headers=headers, timeout=30)
            response.raise_for_status()
            return response.text
        except requests.RequestException:
            # Try master branch as fallback
            master_url = f"https://raw.githubusercontent.com/{owner}/{repo}/master/README.md"
            
            try:
                response = requests.get(master_url, headers=headers, timeout=30)
                response.raise_for_status()
                return response.text
            except requests.RequestException as e:
                raise ValueError(f"Failed to fetch README from GitHub repo: {e}")
    
    def _extract_tools_from_readme(self, content: str) -> List[MCPTool]:
        """
        Extract MCP tools from README markdown content.
        
        Args:
            content: README markdown content.
            
        Returns:
            A list of MCPTool objects.
        """
        tools = []
        
        # Pattern 1: Markdown links in lists (most common format)
        # Example: "- [Tool Name](https://tool-url.com) - Tool description"
        list_pattern = r'^\s*[-*+]\s*\[([^\]]+)\]\(([^)]+)\)(.*?)$'
        
        for line in content.split('\n'):
            match = re.match(list_pattern, line)
            if match:
                name = match.group(1).strip()
                url = match.group(2).strip()
                description = match.group(3).strip()
                
                # If description starts with a dash or other separators, remove it
                description = re.sub(r'^[:-]\s*', '', description)
                
                if name and url and self.is_mcp_tool(name, description):
                    tools.append(MCPTool(
                        name=name,
                        description=description or name,
                        url=url,
                        source_url=self.source.url,
                        metadata={
                            "tags": self.extract_tags(name, description)
                        }
                    ))
        
        # Pattern 2: Tables (used in some awesome lists)
        table_pattern = r'^\s*\|\s*\[([^\]]+)\]\(([^)]+)\)\s*\|\s*([^|]+)'
        
        for line in content.split('\n'):
            match = re.match(table_pattern, line)
            if match:
                name = match.group(1).strip()
                url = match.group(2).strip()
                description = match.group(3).strip()
                
                if name and url and self.is_mcp_tool(name, description):
                    tools.append(MCPTool(
                        name=name,
                        description=description,
                        url=url,
                        source_url=self.source.url,
                        metadata={
                            "tags": self.extract_tags(name, description)
                        }
                    ))
        
        return tools


class CrawlerFactory:
    """Factory for creating crawlers based on source type."""
    
    @staticmethod
    def create_crawler(source: Source, user_agent: str = "MCP-Tool-Crawler/1.0") -> BaseCrawler:
        """
        Create a crawler for the given source.
        
        Args:
            source: The source to crawl.
            user_agent: User agent string to use for HTTP requests.
            
        Returns:
            A crawler instance.
            
        Raises:
            ValueError: If the source type is not supported.
        """
        if source.type == SourceType.GITHUB_AWESOME_LIST:
            return GitHubAwesomeListCrawler(source, user_agent)
        else:
            raise ValueError(f"Unsupported source type: {source.type}")


class CrawlerService:
    """Service for crawling sources."""
    
    def __init__(self, user_agent: str = "MCP-Tool-Crawler/1.0", concurrency_limit: int = 5):
        self.user_agent = user_agent
        self.concurrency_limit = concurrency_limit
    
    async def crawl_source(self, source: Source) -> CrawlResult:
        """
        Crawl a single source.
        
        Args:
            source: The source to crawl.
            
        Returns:
            The result of the crawl operation.
        """
        try:
            crawler = CrawlerFactory.create_crawler(source, self.user_agent)
            return await crawler.crawl()
        except Exception as e:
            logger.error(f"Error creating crawler for source {source.url}: {str(e)}")
            return CrawlResult(
                source_id=source.id,
                success=False,
                tools_discovered=0,
                new_tools=0,
                updated_tools=0,
                duration=0,
                error=str(e)
            )
    
    async def crawl_all_sources(self, sources: List[Source], force: bool = False) -> List[CrawlResult]:
        """
        Crawl multiple sources concurrently.
        
        Args:
            sources: The sources to crawl.
            force: Whether to force crawl all sources, ignoring last crawl time.
            
        Returns:
            A list of crawl results.
        """
        # Filter sources that need to be crawled
        if not force:
            # In a real app, we'd filter based on last crawl time
            # For simplicity, we'll crawl all sources
            sources_to_crawl = sources
        else:
            sources_to_crawl = sources
        
        if not sources_to_crawl:
            return []
        
        # Create tasks for each source
        tasks = []
        semaphore = asyncio.Semaphore(self.concurrency_limit)
        
        async def crawl_with_semaphore(source):
            async with semaphore:
                return await self.crawl_source(source)
        
        for source in sources_to_crawl:
            tasks.append(crawl_with_semaphore(source))
        
        # Run tasks concurrently
        results = await asyncio.gather(*tasks)
        
        return results

