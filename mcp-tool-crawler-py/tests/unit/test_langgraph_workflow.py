"""
Tests for the LangGraph crawler generator workflow.
"""
import os
import json
import pytest
from unittest.mock import patch, MagicMock, ANY
import sys
from typing import Dict, Any, cast

from src.models import Source, SourceType, CrawlerStrategy

# This prevents pytest from treating the imported test_crawler_code function as a test
pytestmark = pytest.mark.filterwarnings("ignore::pytest.PytestCollectionWarning")

from src.agents.crawler_generator import (
    CrawlerGeneratorState,
    fetch_website,
    analyze_website,
    identify_patterns,
    generate_crawler_code,
    test_crawler_code,
    finalize_strategy,
    build_graph
)
from langgraph.graph import StateGraph, END


@pytest.fixture
def mock_source():
    """Create a mock source for testing."""
    return Source(
        id="test-source-id",
        url="https://example.com",
        name="Test Website",
        type=SourceType.WEBSITE,
        has_known_crawler=False,
    )


@pytest.fixture
def mock_html_content():
    """Mock HTML content for testing."""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Example MCP Tools</title>
    </head>
    <body>
        <h1>MCP Tools Directory</h1>
        <div class="tool-card">
            <h2>RAG Framework</h2>
            <p>A retrieval augmented generation framework for LLMs</p>
            <a href="/tools/rag-framework">Learn more</a>
            <div class="tags"><span class="tag">rag</span><span class="tag">llm</span></div>
        </div>
        <div class="tool-card">
            <h2>Vector Explorer</h2>
            <p>Tool for exploring vector embeddings</p>
            <a href="/tools/vector-explorer">Learn more</a>
            <div class="tags"><span class="tag">vector</span><span class="tag">embedding</span></div>
        </div>
    </body>
    </html>
    """


@pytest.fixture
def mock_website_analysis():
    """Mock website analysis result."""
    return {
        "site_type": "directory",
        "technologies": ["html", "css"],
        "has_anti_bot": False,
        "navigation_structure": "Simple directory listing",
        "key_patterns": [
            {
                "selector": ".tool-card",
                "pattern_type": "list",
                "content_type": "tool",
                "sample_text": "RAG Framework",
                "extraction_strategy": "Extract name from h2, description from p, and URL from a href"
            }
        ],
        "challenges": ["No pagination"],
        "recommended_approach": "Simple scraping with BeautifulSoup"
    }


@pytest.fixture
def mock_crawler_code():
    """Mock generated crawler code."""
    return """
import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Any

from .base import BaseCrawler
from ..models import MCPTool, Source
from ..utils.logging import get_logger

logger = get_logger(__name__)

class ExampleComCrawler(BaseCrawler):
    \"\"\"Crawler for Example.com\"\"\"
    
    def discover_tools(self) -> List[MCPTool]:
        \"\"\"Discover MCP tools from the website.\"\"\"
        tools = []
        try:
            # Fetch the main page
            response = requests.get(self.source.url, headers={"User-Agent": self.user_agent})
            response.raise_for_status()
            
            # Parse the HTML
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract tools
            tool_cards = soup.select('.tool-card')
            for card in tool_cards:
                name_elem = card.find('h2')
                desc_elem = card.find('p')
                link_elem = card.find('a')
                
                if name_elem and desc_elem and link_elem:
                    name = name_elem.text.strip()
                    description = desc_elem.text.strip()
                    
                    # Get the URL
                    url = link_elem['href']
                    if not url.startswith(('http://', 'https://')):
                        url = f"https://example.com{url}"
                    
                    # Check if it's an MCP tool
                    if self.is_mcp_tool(name, description):
                        # Extract tags
                        tag_elems = card.select('.tag')
                        tags = [tag.text.strip() for tag in tag_elems]
                        
                        # If no tags found in HTML, extract from name/description
                        if not tags:
                            tags = self.extract_tags(name, description)
                        
                        tools.append(MCPTool(
                            name=name,
                            description=description,
                            url=url,
                            source_url=self.source.url,
                            metadata={
                                "tags": tags
                            }
                        ))
            
            logger.info(f"Discovered {len(tools)} tools from {self.source.url}")
            return tools
            
        except Exception as e:
            logger.error(f"Error crawling {self.source.name}: {str(e)}")
            return tools
    """


def test_node_function_fetch_website(mock_source):
    """Test the fetch_website node function directly."""
    # Create initial state
    state = CrawlerGeneratorState(
        source=mock_source.model_dump()
    )
    
    # Mock fetch_website_content
    with patch('src.agents.crawler_generator.fetch_website_content') as mock_fetch:
        # Configure the mock
        mock_fetch.return_value = "<html><body>Test HTML</body></html>"
        
        # Call the function directly
        result = fetch_website(state)
        
        # Check the result
        assert result.html_content is not None
        assert "Test HTML" in result.html_content
        assert not result.error
        assert not result.finished


def test_node_function_analyze_website(mock_source, mock_html_content, mock_website_analysis):
    """Test the analyze_website node function directly."""
    # Create initial state
    state = CrawlerGeneratorState(
        source=mock_source.model_dump(),
        html_content=mock_html_content
    )
    
    # Mock call_llm
    with patch('src.agents.crawler_generator.call_llm') as mock_call_llm:
        # Configure the mock
        mock_call_llm.return_value = json.dumps(mock_website_analysis)
        
        # Call the function directly
        result = analyze_website(state)
        
        # Check the result
        assert result.website_analysis is not None
        assert result.website_analysis == mock_website_analysis
        assert not result.error
        assert not result.finished


def test_node_function_identify_patterns(mock_source, mock_html_content, mock_website_analysis):
    """Test the identify_patterns node function directly."""
    # Create initial state
    state = CrawlerGeneratorState(
        source=mock_source.model_dump(),
        html_content=mock_html_content,
        website_analysis=mock_website_analysis
    )
    
    # Call the function directly
    with patch('src.agents.crawler_generator.BeautifulSoup'):
        result = identify_patterns(state)
        
        # Check the result
        assert result.identified_patterns is not None
        assert not result.error
        assert not result.finished


def test_node_function_generate_crawler_code(mock_source, mock_html_content, mock_website_analysis, mock_crawler_code):
    """Test the generate_crawler_code node function directly."""
    # Create initial state
    state = CrawlerGeneratorState(
        source=mock_source.model_dump(),
        html_content=mock_html_content,
        website_analysis=mock_website_analysis,
        identified_patterns=mock_website_analysis["key_patterns"]
    )
    
    # Mock call_llm
    with patch('src.agents.crawler_generator.call_llm') as mock_call_llm:
        # Configure the mock
        mock_call_llm.return_value = f"```python\n{mock_crawler_code}\n```"
        
        # Call the function directly
        result = generate_crawler_code(state)
        
        # Check the result
        assert result.crawler_code is not None
        assert "BaseCrawler" in result.crawler_code
        assert not result.error
        assert not result.finished


def test_node_function_finalize_strategy(mock_source, mock_html_content, mock_website_analysis, mock_crawler_code):
    """Test the finalize_strategy node function directly."""
    # Create initial state
    state = CrawlerGeneratorState(
        source=mock_source.model_dump(),
        html_content=mock_html_content,
        website_analysis=mock_website_analysis,
        identified_patterns=mock_website_analysis["key_patterns"],
        crawler_code=mock_crawler_code,
        testing_results={"has_errors": False}
    )
    
    # Mock call_llm
    with patch('src.agents.crawler_generator.call_llm') as mock_call_llm, \
         patch('uuid.uuid4') as mock_uuid:
        # Configure the mocks
        mock_call_llm.return_value = "This crawler extracts MCP tools from the website."
        mock_uuid.return_value = "test-uuid"
        
        # Call the function directly
        result = finalize_strategy(state)
        
        # Check the result
        assert result.crawler_strategy is not None
        assert result.crawler_strategy["implementation"] == mock_crawler_code
        assert result.crawler_strategy["source_id"] == mock_source.id
        assert "test-uuid" in result.crawler_strategy["id"]
        assert result.finished


def test_node_function_test_crawler_code_node(mock_source, mock_crawler_code):
    """Test the test_crawler_code node function directly."""
    # Create initial state - renamed to avoid collision with actual test_crawler_code function
    state = CrawlerGeneratorState(
        source=mock_source.model_dump(),
        crawler_code=mock_crawler_code
    )
    
    # Mock call_llm
    with patch('src.agents.crawler_generator.call_llm') as mock_call_llm:
        # Configure the mock
        mock_call_llm.return_value = json.dumps({
            "has_errors": False,
            "issues": [],
            "suggested_improvements": ["Add timeout", "Improve error handling"],
            "security_score": 8,
            "efficiency_score": 9,
            "overall_assessment": "Good implementation"
        })
        
        # Call the function directly
        result = test_crawler_code(state)
        
        # Check the result
        assert result.testing_results is not None
        assert result.testing_results["has_errors"] is False
        assert len(result.testing_results["suggested_improvements"]) == 2
        assert result.crawler_code == mock_crawler_code  # Code should be unchanged
        assert not result.error