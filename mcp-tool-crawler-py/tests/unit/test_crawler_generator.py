"""
Unit tests for the crawler generator agent.
"""
import os
import json
import pytest
from unittest.mock import patch, MagicMock, ANY

from src.models import Source, SourceType, CrawlerStrategy
from src.agents.crawler_generator import (
    build_graph,
    fetch_website,
    analyze_website,
    identify_patterns,
    generate_crawler_code,
    test_crawler_code,
    finalize_strategy,
    CrawlerGeneratorState,
    call_llm
)

# This prevents pytest from treating the imported test_crawler_code function as a test
pytestmark = pytest.mark.filterwarnings("ignore::pytest.PytestCollectionWarning")


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


@pytest.fixture
def mock_testing_results():
    """Mock testing results."""
    return {
        "has_errors": False,
        "issues": [],
        "suggested_improvements": [
            "Add timeout to requests.get call",
            "Add more thorough error handling"
        ],
        "security_score": 8,
        "efficiency_score": 9,
        "overall_assessment": "Good implementation with minor improvement opportunities"
    }


def test_fetch_website(mock_source, mock_html_content):
    """Test fetching website content."""
    # Create initial state
    initial_state = CrawlerGeneratorState(
        source=mock_source.model_dump()
    )
    
    # Mock requests.get
    with patch('src.agents.crawler_generator.fetch_website_content', return_value=mock_html_content):
        # Call the function
        result = fetch_website(initial_state)
        
        # Check result
        assert result.html_content == mock_html_content
        assert not result.error
        assert not result.finished


def test_fetch_website_error(mock_source):
    """Test fetching website with error."""
    # Create initial state
    initial_state = CrawlerGeneratorState(
        source=mock_source.model_dump()
    )
    
    # Mock requests.get to raise an exception
    with patch('src.agents.crawler_generator.fetch_website_content', side_effect=Exception("Connection error")):
        # Call the function
        result = fetch_website(initial_state)
        
        # Check result
        assert result.error is not None
        assert "error" in result.error.lower()
        assert result.finished


def test_analyze_website(mock_source, mock_html_content, mock_website_analysis):
    """Test analyzing website."""
    # Create initial state
    initial_state = CrawlerGeneratorState(
        source=mock_source.model_dump(),
        html_content=mock_html_content
    )
    
    # Mock call_llm
    with patch('src.agents.crawler_generator.call_llm', return_value=json.dumps(mock_website_analysis)):
        # Call the function
        result = analyze_website(initial_state)
        
        # Check result
        assert result.website_analysis == mock_website_analysis
        assert not result.error
        assert not result.finished


def test_analyze_website_error(mock_source, mock_html_content):
    """Test analyzing website with error."""
    # Create initial state
    initial_state = CrawlerGeneratorState(
        source=mock_source.model_dump(),
        html_content=mock_html_content
    )
    
    # Mock call_llm to return invalid JSON
    with patch('src.agents.crawler_generator.call_llm', return_value="Invalid JSON"):
        # Call the function
        result = analyze_website(initial_state)
        
        # Check result
        assert result.error is not None
        assert result.finished


def test_identify_patterns(mock_source, mock_html_content, mock_website_analysis):
    """Test identifying patterns."""
    # Create initial state
    initial_state = CrawlerGeneratorState(
        source=mock_source.model_dump(),
        html_content=mock_html_content,
        website_analysis=mock_website_analysis
    )
    
    # Call the function
    result = identify_patterns(initial_state)
    
    # Check result
    assert result.identified_patterns is not None
    assert len(result.identified_patterns) > 0
    assert not result.error
    assert not result.finished


def test_generate_crawler_code(mock_source, mock_html_content, mock_website_analysis, mock_crawler_code):
    """Test generating crawler code."""
    # Create initial state
    initial_state = CrawlerGeneratorState(
        source=mock_source.model_dump(),
        html_content=mock_html_content,
        website_analysis=mock_website_analysis,
        identified_patterns=mock_website_analysis["key_patterns"]
    )
    
    # Mock call_llm
    with patch('src.agents.crawler_generator.call_llm', return_value=f"```python\n{mock_crawler_code}\n```"):
        # Call the function
        result = generate_crawler_code(initial_state)
        
        # Check result
        assert result.crawler_code is not None
        assert "BaseCrawler" in result.crawler_code
        assert "discover_tools" in result.crawler_code
        assert not result.error
        assert not result.finished


def test_crawler_testing_function(mock_source, mock_html_content, mock_website_analysis, mock_crawler_code, mock_testing_results):
    """Test the crawler code testing function - renamed to avoid collision with node function."""
    # Create initial state
    initial_state = CrawlerGeneratorState(
        source=mock_source.model_dump(),
        html_content=mock_html_content,
        website_analysis=mock_website_analysis,
        identified_patterns=mock_website_analysis["key_patterns"],
        crawler_code=mock_crawler_code
    )
    
    # Mock call_llm
    with patch('src.agents.crawler_generator.call_llm', return_value=json.dumps(mock_testing_results)):
        # Call the function
        result = test_crawler_code(initial_state)
        
        # Check result
        assert result.testing_results is not None
        assert not result.error
        assert not result.finished


def test_finalize_strategy(mock_source, mock_html_content, mock_website_analysis, mock_crawler_code, mock_testing_results):
    """Test finalizing strategy."""
    # Create initial state
    initial_state = CrawlerGeneratorState(
        source=mock_source.model_dump(),
        html_content=mock_html_content,
        website_analysis=mock_website_analysis,
        identified_patterns=mock_website_analysis["key_patterns"],
        crawler_code=mock_crawler_code,
        testing_results=mock_testing_results
    )
    
    # Mock call_llm
    with patch('src.agents.crawler_generator.call_llm', return_value="This crawler extracts MCP tools from Example.com by parsing tool cards."):
        # Call the function
        result = finalize_strategy(initial_state)
        
        # Check result
        assert result.crawler_strategy is not None
        assert result.crawler_strategy["implementation"] == mock_crawler_code
        assert result.crawler_strategy["source_id"] == mock_source.id
        assert result.finished


def test_build_graph():
    """Test building the LangGraph."""
    # Build the graph
    graph = build_graph()
    
    # Check that it built successfully
    assert graph is not None


@patch('src.agents.crawler_generator.build_graph')
@patch('src.agents.crawler_generator.CrawlerGeneratorState')
def test_generate_crawler(mock_state, mock_build_graph, mock_source):
    """Test the generate_crawler function."""
    # Mock the graph
    mock_graph = MagicMock()
    mock_build_graph.return_value = mock_graph
    
    # Mock the result
    mock_result = MagicMock()
    mock_result.error = None
    mock_result.crawler_strategy = {
        "id": "crawler-123",
        "source_id": mock_source.id,
        "source_type": mock_source.type,
        "implementation": "def discover_tools(): pass",
        "description": "Test crawler",
        "created": "2025-03-11T12:00:00Z",
        "last_modified": "2025-03-11T12:00:00Z"
    }
    mock_graph.invoke.return_value = mock_result
    
    # Call the function
    from src.agents.crawler_generator import generate_crawler
    result = generate_crawler(mock_source)
    
    # Check the result
    assert result is not None
    assert result.source_id == mock_source.id
    assert result.implementation == mock_result.crawler_strategy["implementation"]


@patch('src.agents.crawler_generator.generate_crawler')
def test_handler(mock_generate_crawler, mock_source):
    """Test the Lambda handler."""
    # Mock generate_crawler
    mock_strategy = CrawlerStrategy(
        id="crawler-123",
        source_id=mock_source.id,
        source_type=mock_source.type,
        implementation="def discover_tools(): pass",
        description="Test crawler",
        created="2025-03-11T12:00:00Z",
        last_modified="2025-03-11T12:00:00Z"
    )
    mock_generate_crawler.return_value = mock_strategy
    
    # Create mock event
    event = {
        "source_id": mock_source.id,
        "url": mock_source.url,
        "name": mock_source.name,
        "source_type": mock_source.type
    }
    
    # Call the handler
    from src.agents.crawler_generator import handler
    result = handler(event, None)
    
    # Check the result
    assert result["status"] == "success"
    assert result["source_id"] == mock_source.id
    assert result["crawler_id"] == mock_strategy.id
    assert "crawler_strategy" in result