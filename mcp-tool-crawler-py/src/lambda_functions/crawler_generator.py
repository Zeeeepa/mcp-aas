"""
Crawler generator module for MCP tool crawler.

This module generates crawlers for sources that don't have a known crawler.
"""

import json
import os
import time
from typing import Dict, Any, List, Optional

from ..models import Source, SourceType
from ..utils.logging import get_logger
from ..utils.config import get_config

logger = get_logger(__name__)
config = get_config()


def generate_crawler_for_source(source: Source) -> Optional[str]:
    """
    Generate a crawler for a source.
    
    Args:
        source: Source to generate a crawler for.
        
    Returns:
        Generated crawler code as a string, or None if generation failed.
    """
    logger.info(f"Generating crawler for source: {source.name} ({source.url})")
    
    # This is a placeholder for the actual crawler generation logic
    # In a real implementation, this would use OpenAI or another LLM to generate the crawler
    
    # For now, return a simple template crawler
    if source.type == SourceType.GITHUB_AWESOME_LIST:
        return _generate_github_awesome_list_crawler(source)
    elif source.type == SourceType.GITHUB_REPOSITORY:
        return _generate_github_repository_crawler(source)
    elif source.type == SourceType.WEBSITE:
        return _generate_website_crawler(source)
    else:
        logger.warning(f"Unsupported source type for crawler generation: {source.type}")
        return None


def _generate_github_awesome_list_crawler(source: Source) -> str:
    """
    Generate a crawler for a GitHub awesome list.
    
    Args:
        source: Source to generate a crawler for.
        
    Returns:
        Generated crawler code as a string.
    """
    return f"""
import re
import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Any

def crawl() -> List[Dict[str, Any]]:
    \"\"\"
    Crawl the GitHub awesome list at {source.url} and extract MCP tools.
    
    Returns:
        List of MCP tools.
    \"\"\"
    # Fetch the page
    response = requests.get("{source.url}")
    response.raise_for_status()
    
    # Parse the HTML
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Find all links in the README
    tools = []
    
    # Find the README content
    readme = soup.find('article', class_='markdown-body')
    if not readme:
        return []
    
    # Find all links in the README
    for link in readme.find_all('a'):
        # Skip links without href
        if not link.get('href'):
            continue
        
        # Skip relative links
        href = link.get('href')
        if not href.startswith('http'):
            continue
        
        # Skip links to GitHub itself
        if href.startswith('https://github.com/') and '//' in href[19:]:
            continue
        
        # Get the link text
        name = link.text.strip()
        if not name:
            continue
        
        # Get the description (text after the link until the next tag)
        description = ''
        next_node = link.next_sibling
        while next_node and not (hasattr(next_node, 'name') and next_node.name in ['a', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
            if hasattr(next_node, 'strip'):
                description += next_node.strip()
            next_node = next_node.next_sibling
        
        # Clean up description
        description = re.sub(r'^[\\s\\-:]+', '', description).strip()
        
        # Add the tool
        tools.append({{
            'name': name,
            'description': description,
            'url': href,
            'source_url': "{source.url}",
        }})
    
    return tools
"""


def _generate_github_repository_crawler(source: Source) -> str:
    """
    Generate a crawler for a GitHub repository.
    
    Args:
        source: Source to generate a crawler for.
        
    Returns:
        Generated crawler code as a string.
    """
    return f"""
import requests
from typing import List, Dict, Any

def crawl() -> List[Dict[str, Any]]:
    \"\"\"
    Crawl the GitHub repository at {source.url} and extract MCP tools.
    
    Returns:
        List of MCP tools.
    \"\"\"
    # This is a simple crawler that just returns the repository itself as a tool
    # In a real implementation, this would analyze the repository to find MCP tools
    
    # Extract owner and repo from URL
    parts = "{source.url}".split('/')
    owner = parts[-2]
    repo = parts[-1]
    
    # Fetch repository information from GitHub API
    api_url = f"https://api.github.com/repos/{{owner}}/{{repo}}"
    headers = {{"Accept": "application/vnd.github.v3+json"}}
    
    # Add GitHub token if available
    github_token = "{config['github']['token']}"
    if github_token:
        headers["Authorization"] = f"token {{github_token}}"
    
    response = requests.get(api_url, headers=headers)
    response.raise_for_status()
    
    repo_data = response.json()
    
    # Create a tool from the repository
    return [{{
        'name': repo_data['name'],
        'description': repo_data['description'] or '',
        'url': repo_data['html_url'],
        'source_url': "{source.url}",
    }}]
"""


def _generate_website_crawler(source: Source) -> str:
    """
    Generate a crawler for a website.
    
    Args:
        source: Source to generate a crawler for.
        
    Returns:
        Generated crawler code as a string.
    """
    return f"""
import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Any

def crawl() -> List[Dict[str, Any]]:
    \"\"\"
    Crawl the website at {source.url} and extract MCP tools.
    
    Returns:
        List of MCP tools.
    \"\"\"
    # Fetch the page
    response = requests.get("{source.url}")
    response.raise_for_status()
    
    # Parse the HTML
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Find all links
    tools = []
    for link in soup.find_all('a'):
        # Skip links without href
        if not link.get('href'):
            continue
        
        # Get the link text
        name = link.text.strip()
        if not name:
            continue
        
        # Get the href
        href = link.get('href')
        
        # Make absolute URL if relative
        if not href.startswith('http'):
            if href.startswith('/'):
                href = "{source.url.rstrip('/')}" + href
            else:
                href = "{source.url.rstrip('/')}/" + href
        
        # Add the tool
        tools.append({{
            'name': name,
            'description': '',  # No description available
            'url': href,
            'source_url': "{source.url}",
        }})
    
    return tools
"""


def save_crawler_to_file(source_id: str, crawler_code: str) -> str:
    """
    Save a crawler to a file.
    
    Args:
        source_id: ID of the source.
        crawler_code: Crawler code to save.
        
    Returns:
        Path to the saved crawler file.
    """
    # Create crawlers directory if it doesn't exist
    crawlers_dir = os.path.join(config['local']['data_dir'], 'crawlers')
    os.makedirs(crawlers_dir, exist_ok=True)
    
    # Save crawler to file
    crawler_path = os.path.join(crawlers_dir, f"{source_id}.py")
    with open(crawler_path, 'w', encoding='utf-8') as f:
        f.write(crawler_code)
    
    logger.info(f"Saved crawler for source {source_id} to {crawler_path}")
    return crawler_path


def load_crawler_from_file(source_id: str) -> Optional[str]:
    """
    Load a crawler from a file.
    
    Args:
        source_id: ID of the source.
        
    Returns:
        Crawler code as a string, or None if the crawler doesn't exist.
    """
    crawler_path = os.path.join(config['local']['data_dir'], 'crawlers', f"{source_id}.py")
    
    if not os.path.exists(crawler_path):
        logger.warning(f"No crawler found for source {source_id}")
        return None
    
    with open(crawler_path, 'r', encoding='utf-8') as f:
        crawler_code = f.read()
    
    logger.info(f"Loaded crawler for source {source_id} from {crawler_path}")
    return crawler_code

