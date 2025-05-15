"""
Tests for the SourceManager implementation using SQLite storage.
"""
import os
import pytest
import yaml
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

from src.models import Source, SourceType
from src.services.source_manager_sqlite import SourceManager


class TestSourceManager:
    """Test the SourceManager implementation."""
    
    @pytest.mark.asyncio
    async def test_initialization(self, temp_db_path):
        """Test initializing the SourceManager."""
        # Create manager
        manager = SourceManager(db_path=temp_db_path)
        
        # Check that the database file was created
        assert os.path.exists(temp_db_path)
    
    @pytest.mark.asyncio
    async def test_add_source(self, source_manager):
        """Test adding a source."""
        # Create a source
        source = Source(
            id="test-source-id",
            url="https://example.com",
            name="Test Source",
            type=SourceType.WEBSITE,
            has_known_crawler=False
        )
        
        # Add the source
        added_source = await source_manager.add_source(source)
        
        # Check that the source was added
        assert added_source.id == source.id
        assert added_source.url == source.url
        assert added_source.name == source.name
        assert added_source.type == source.type
        assert added_source.has_known_crawler == source.has_known_crawler
        
        # Check that the source can be retrieved
        sources = await source_manager.get_all_sources()
        assert len(sources) == 1
        assert sources[0].id == source.id
    
    @pytest.mark.asyncio
    async def test_add_source_by_url(self, source_manager):
        """Test adding a source by URL."""
        # Add a source by URL
        url = "https://example.com"
        name = "Test Source"
        source_type = SourceType.WEBSITE
        
        added_source = await source_manager.add_source_by_url(url, name, source_type)
        
        # Check that the source was added
        assert added_source.url == url
        assert added_source.name == name
        assert added_source.type == source_type
        
        # Check that the source can be retrieved
        sources = await source_manager.get_all_sources()
        assert len(sources) == 1
        assert sources[0].url == url
    
    @pytest.mark.asyncio
    async def test_add_source_by_url_auto_detect(self, source_manager):
        """Test adding a source by URL with auto-detection of type and name."""
        # Add a source by URL only
        url = "https://github.com/awesome-mcp/awesome-list"
        
        added_source = await source_manager.add_source_by_url(url)
        
        # Check that the source was added with auto-detected type and name
        assert added_source.url == url
        assert added_source.type == SourceType.GITHUB_AWESOME_LIST
        assert "github.com" in added_source.name.lower()
        
        # Add a regular GitHub repo
        url = "https://github.com/example/repo"
        
        added_source = await source_manager.add_source_by_url(url)
        
        # Check that the source was added with auto-detected type
        assert added_source.url == url
        assert added_source.type == SourceType.GITHUB_REPOSITORY
        
        # Add a website
        url = "https://example.com"
        
        added_source = await source_manager.add_source_by_url(url)
        
        # Check that the source was added with auto-detected type
        assert added_source.url == url
        assert added_source.type == SourceType.WEBSITE
    
    @pytest.mark.asyncio
    async def test_get_all_sources(self, source_manager):
        """Test retrieving all sources."""
        # Add multiple sources
        sources = [
            Source(
                id=f"test-source-{i}",
                url=f"https://example{i}.com",
                name=f"Test Source {i}",
                type=SourceType.WEBSITE,
                has_known_crawler=False
            )
            for i in range(3)
        ]
        
        for source in sources:
            await source_manager.add_source(source)
        
        # Retrieve all sources
        retrieved_sources = await source_manager.get_all_sources()
        
        # Check that all sources were retrieved
        assert len(retrieved_sources) == 3
        
        # Check that the sources match
        source_ids = [source.id for source in sources]
        retrieved_ids = [source.id for source in retrieved_sources]
        
        for source_id in source_ids:
            assert source_id in retrieved_ids
    
    @pytest.mark.asyncio
    async def test_get_sources_to_crawl(self, source_manager):
        """Test retrieving sources to crawl."""
        # Add sources with different last_crawled values
        now = datetime.now()
        
        # Source crawled recently
        source1 = Source(
            id="test-source-1",
            url="https://example1.com",
            name="Test Source 1",
            type=SourceType.WEBSITE,
            has_known_crawler=False,
            last_crawled=now.isoformat(),
            last_crawl_status="success"
        )
        
        # Source crawled a long time ago
        source2 = Source(
            id="test-source-2",
            url="https://example2.com",
            name="Test Source 2",
            type=SourceType.WEBSITE,
            has_known_crawler=False,
            last_crawled=(now - timedelta(hours=48)).isoformat(),
            last_crawl_status="success"
        )
        
        # Source never crawled
        source3 = Source(
            id="test-source-3",
            url="https://example3.com",
            name="Test Source 3",
            type=SourceType.WEBSITE,
            has_known_crawler=False
        )
        
        await source_manager.add_source(source1)
        await source_manager.add_source(source2)
        await source_manager.add_source(source3)
        
        # Get sources to crawl with 24-hour threshold
        sources_to_crawl = await source_manager.get_sources_to_crawl(time_threshold_hours=24)
        
        # Check that only the sources that need to be crawled were returned
        assert len(sources_to_crawl) == 2
        
        crawl_ids = [source.id for source in sources_to_crawl]
        assert "test-source-2" in crawl_ids  # Crawled a long time ago
        assert "test-source-3" in crawl_ids  # Never crawled
        assert "test-source-1" not in crawl_ids  # Crawled recently
    
    @pytest.mark.asyncio
    async def test_update_source_last_crawl(self, source_manager):
        """Test updating a source's last crawl information."""
        # Add a source
        source = Source(
            id="test-source-id",
            url="https://example.com",
            name="Test Source",
            type=SourceType.WEBSITE,
            has_known_crawler=False
        )
        
        await source_manager.add_source(source)
        
        # Update the source's last crawl information
        result = await source_manager.update_source_last_crawl(source.id, True)
        assert result is True
        
        # Get the updated source
        sources = await source_manager.get_all_sources()
        updated_source = next((s for s in sources if s.id == source.id), None)
        
        # Check that the last crawl information was updated
        assert updated_source is not None
        assert updated_source.last_crawled is not None
        assert updated_source.last_crawl_status == "success"
        
        # Update with failure status
        result = await source_manager.update_source_last_crawl(source.id, False)
        assert result is True
        
        # Get the updated source
        sources = await source_manager.get_all_sources()
        updated_source = next((s for s in sources if s.id == source.id), None)
        
        # Check that the last crawl information was updated
        assert updated_source is not None
        assert updated_source.last_crawled is not None
        assert updated_source.last_crawl_status == "failed"
    
    @pytest.mark.asyncio
    async def test_initialize_sources_from_config(self, source_manager, temp_dir_path):
        """Test initializing sources from configuration."""
        # Mock the config
        config = {
            'sources': {
                'awesome_lists': [
                    'https://github.com/awesome-mcp/list1',
                    'https://github.com/awesome-mcp/list2'
                ],
                'websites': [
                    {
                        'url': 'https://example.com',
                        'name': 'Example Website'
                    },
                    {
                        'url': 'https://test.com',
                        'name': 'Test Website'
                    }
                ]
            }
        }
        
        # Patch the get_config function
        with patch('src.services.source_manager_sqlite.config', config):
            # Initialize sources
            sources = await source_manager.initialize_sources()
            
            # Check that all sources were added
            assert len(sources) == 4
            
            # Check that the awesome lists were added
            awesome_list_urls = [
                'https://github.com/awesome-mcp/list1',
                'https://github.com/awesome-mcp/list2'
            ]
            
            for source in sources:
                if source.url in awesome_list_urls:
                    assert source.type == SourceType.GITHUB_AWESOME_LIST
                    assert source.has_known_crawler is True
            
            # Check that the websites were added
            website_urls = ['https://example.com', 'https://test.com']
            website_names = ['Example Website', 'Test Website']
            
            for source in sources:
                if source.url in website_urls:
                    assert source.type == SourceType.WEBSITE
                    assert source.has_known_crawler is False
                    assert source.name in website_names
    
    @pytest.mark.asyncio
    async def test_initialize_sources_from_local_file(self, source_manager, temp_dir_path):
        """Test initializing sources from a local file."""
        # Create a sources.yaml file
        sources_path = os.path.join(temp_dir_path, "sources.yaml")
        sources_data = {
            'sources': [
                {
                    'url': 'https://github.com/awesome-mcp/list1',
                    'name': 'Awesome MCP List 1',
                    'type': 'github_awesome_list'
                },
                {
                    'url': 'https://example.com',
                    'name': 'Example Website',
                    'type': 'website'
                }
            ]
        }
        
        with open(sources_path, 'w') as f:
            yaml.dump(sources_data, f)
        
        # Mock the config
        config = {
            'local': {
                'sources_path': sources_path
            }
        }
        
        # Patch the get_config function
        with patch('src.services.source_manager_sqlite.config', config):
            # Initialize sources
            sources = await source_manager.initialize_sources()
            
            # Check that all sources were added
            assert len(sources) == 2
            
            # Check that the sources match
            source_urls = [source.url for source in sources]
            assert 'https://github.com/awesome-mcp/list1' in source_urls
            assert 'https://example.com' in source_urls
            
            # Check that the types match
            for source in sources:
                if source.url == 'https://github.com/awesome-mcp/list1':
                    assert source.type == SourceType.GITHUB_AWESOME_LIST
                    assert source.name == 'Awesome MCP List 1'
                elif source.url == 'https://example.com':
                    assert source.type == SourceType.WEBSITE
                    assert source.name == 'Example Website'

