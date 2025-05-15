"""
Tests for the WorkflowOrchestrator implementation.
"""
import pytest
import asyncio
from unittest.mock import MagicMock, patch, AsyncMock

from src.models import Source, MCPTool, CrawlerStrategy, CrawlResult, SourceType
from src.workflow.orchestrator import WorkflowOrchestrator


class TestWorkflowOrchestrator:
    """Test the WorkflowOrchestrator implementation."""
    
    @pytest.fixture
    def orchestrator(self):
        """Create a WorkflowOrchestrator instance."""
        return WorkflowOrchestrator()
    
    @pytest.fixture
    def mock_source(self):
        """Create a mock source."""
        return Source(
            id="test-source-id",
            url="https://example.com",
            name="Test Source",
            type=SourceType.WEBSITE,
            has_known_crawler=True
        )
    
    @pytest.fixture
    def mock_tools(self):
        """Create mock tools."""
        return [
            MCPTool(
                id=f"test-tool-{i}",
                name=f"Test Tool {i}",
                description=f"Description for Test Tool {i}",
                url=f"https://example.com/tool{i}",
                source_url="https://example.com"
            )
            for i in range(3)
        ]
    
    @pytest.fixture
    def mock_strategy(self):
        """Create a mock crawler strategy."""
        return CrawlerStrategy(
            id="test-strategy-id",
            source_id="test-source-id",
            source_type=SourceType.WEBSITE,
            implementation="def discover_tools(): pass",
            description="Test crawler strategy"
        )
    
    @pytest.mark.asyncio
    async def test_run_crawler_workflow_success(self, orchestrator, mock_source, mock_tools):
        """Test running a crawler workflow successfully."""
        # Create mock functions
        mock_crawler_func = AsyncMock(return_value=mock_tools)
        mock_storage_func = AsyncMock(return_value=True)
        mock_update_source_func = AsyncMock(return_value=True)
        
        # Run the workflow
        result = await orchestrator.run_crawler_workflow(
            source=mock_source,
            crawler_func=mock_crawler_func,
            storage_func=mock_storage_func,
            update_source_func=mock_update_source_func
        )
        
        # Check that the functions were called
        mock_crawler_func.assert_called_once_with(mock_source)
        mock_storage_func.assert_called_once_with(mock_tools)
        mock_update_source_func.assert_called_once_with(mock_source.id, True)
        
        # Check the result
        assert result.source_id == mock_source.id
        assert result.success is True
        assert result.tools_discovered == 3
        assert result.new_tools == 3
        assert result.updated_tools == 0
        assert result.error is None
    
    @pytest.mark.asyncio
    async def test_run_crawler_workflow_no_tools(self, orchestrator, mock_source):
        """Test running a crawler workflow with no tools discovered."""
        # Create mock functions
        mock_crawler_func = AsyncMock(return_value=[])
        mock_storage_func = AsyncMock(return_value=True)
        mock_update_source_func = AsyncMock(return_value=True)
        
        # Run the workflow
        result = await orchestrator.run_crawler_workflow(
            source=mock_source,
            crawler_func=mock_crawler_func,
            storage_func=mock_storage_func,
            update_source_func=mock_update_source_func
        )
        
        # Check that the functions were called
        mock_crawler_func.assert_called_once_with(mock_source)
        mock_storage_func.assert_not_called()
        mock_update_source_func.assert_called_once_with(mock_source.id, True)
        
        # Check the result
        assert result.source_id == mock_source.id
        assert result.success is True
        assert result.tools_discovered == 0
        assert result.new_tools == 0
        assert result.updated_tools == 0
        assert result.error is None
    
    @pytest.mark.asyncio
    async def test_run_crawler_workflow_storage_failure(self, orchestrator, mock_source, mock_tools):
        """Test running a crawler workflow with storage failure."""
        # Create mock functions
        mock_crawler_func = AsyncMock(return_value=mock_tools)
        mock_storage_func = AsyncMock(return_value=False)
        mock_update_source_func = AsyncMock(return_value=True)
        
        # Run the workflow
        result = await orchestrator.run_crawler_workflow(
            source=mock_source,
            crawler_func=mock_crawler_func,
            storage_func=mock_storage_func,
            update_source_func=mock_update_source_func
        )
        
        # Check that the functions were called
        mock_crawler_func.assert_called_once_with(mock_source)
        mock_storage_func.assert_called_once_with(mock_tools)
        mock_update_source_func.assert_called_once_with(mock_source.id, False)
        
        # Check the result
        assert result.source_id == mock_source.id
        assert result.success is False
        assert result.tools_discovered == 3
        assert result.new_tools == 0
        assert result.updated_tools == 0
        assert result.error == "Failed to store tools"
    
    @pytest.mark.asyncio
    async def test_run_crawler_workflow_crawler_exception(self, orchestrator, mock_source):
        """Test running a crawler workflow with an exception in the crawler."""
        # Create mock functions
        mock_crawler_func = AsyncMock(side_effect=Exception("Test error"))
        mock_storage_func = AsyncMock(return_value=True)
        mock_update_source_func = AsyncMock(return_value=True)
        
        # Run the workflow
        result = await orchestrator.run_crawler_workflow(
            source=mock_source,
            crawler_func=mock_crawler_func,
            storage_func=mock_storage_func,
            update_source_func=mock_update_source_func
        )
        
        # Check that the functions were called
        mock_crawler_func.assert_called_once_with(mock_source)
        mock_storage_func.assert_not_called()
        mock_update_source_func.assert_called_once_with(mock_source.id, False)
        
        # Check the result
        assert result.source_id == mock_source.id
        assert result.success is False
        assert result.tools_discovered == 0
        assert result.new_tools == 0
        assert result.updated_tools == 0
        assert result.error == "Test error"
    
    @pytest.mark.asyncio
    async def test_run_crawler_generator_workflow_success(self, orchestrator, mock_source, mock_strategy):
        """Test running a crawler generator workflow successfully."""
        # Create mock functions
        mock_generator_func = AsyncMock(return_value=mock_strategy)
        mock_storage_func = AsyncMock(return_value=True)
        mock_update_source_func = AsyncMock(return_value=True)
        
        # Run the workflow
        result = await orchestrator.run_crawler_generator_workflow(
            source=mock_source,
            generator_func=mock_generator_func,
            storage_func=mock_storage_func,
            update_source_func=mock_update_source_func
        )
        
        # Check that the functions were called
        mock_generator_func.assert_called_once_with(mock_source)
        mock_storage_func.assert_called_once_with(mock_strategy)
        mock_update_source_func.assert_called_once_with(mock_source.id, mock_strategy.id)
        
        # Check the result
        assert result == mock_strategy
    
    @pytest.mark.asyncio
    async def test_run_crawler_generator_workflow_failure(self, orchestrator, mock_source):
        """Test running a crawler generator workflow with a failure."""
        # Create mock functions
        mock_generator_func = AsyncMock(return_value=None)
        mock_storage_func = AsyncMock(return_value=True)
        mock_update_source_func = AsyncMock(return_value=True)
        
        # Run the workflow
        result = await orchestrator.run_crawler_generator_workflow(
            source=mock_source,
            generator_func=mock_generator_func,
            storage_func=mock_storage_func,
            update_source_func=mock_update_source_func
        )
        
        # Check that the functions were called
        mock_generator_func.assert_called_once_with(mock_source)
        mock_storage_func.assert_not_called()
        mock_update_source_func.assert_not_called()
        
        # Check the result
        assert result is None
    
    @pytest.mark.asyncio
    async def test_run_batch_crawler_workflow(self, orchestrator, mock_source, mock_tools, mock_strategy):
        """Test running a batch crawler workflow."""
        # Create multiple sources
        sources = [
            Source(
                id=f"test-source-{i}",
                url=f"https://example{i}.com",
                name=f"Test Source {i}",
                type=SourceType.WEBSITE,
                has_known_crawler=True
            )
            for i in range(3)
        ]
        
        # Create mock functions
        mock_get_crawler_func = AsyncMock(return_value=mock_strategy)
        mock_crawler_func = AsyncMock(return_value=mock_tools)
        mock_storage_func = AsyncMock(return_value=True)
        mock_update_source_func = AsyncMock(return_value=True)
        mock_save_result_func = AsyncMock(return_value=True)
        
        # Run the workflow
        results = await orchestrator.run_batch_crawler_workflow(
            sources=sources,
            get_crawler_func=mock_get_crawler_func,
            crawler_func=mock_crawler_func,
            storage_func=mock_storage_func,
            update_source_func=mock_update_source_func,
            save_result_func=mock_save_result_func,
            max_concurrent=2
        )
        
        # Check that the functions were called for each source
        assert mock_get_crawler_func.call_count == 3
        assert mock_crawler_func.call_count == 3
        assert mock_storage_func.call_count == 3
        assert mock_update_source_func.call_count == 3
        assert mock_save_result_func.call_count == 3
        
        # Check the results
        assert len(results) == 3
        for result in results:
            assert result.success is True
            assert result.tools_discovered == 3
            assert result.new_tools == 3
            assert result.updated_tools == 0
            assert result.error is None
    
    @pytest.mark.asyncio
    async def test_run_batch_crawler_workflow_no_crawler(self, orchestrator, mock_source):
        """Test running a batch crawler workflow with no crawler found."""
        # Create mock functions
        mock_get_crawler_func = AsyncMock(return_value=None)
        mock_crawler_func = AsyncMock()
        mock_storage_func = AsyncMock()
        mock_update_source_func = AsyncMock()
        mock_save_result_func = AsyncMock()
        
        # Run the workflow
        results = await orchestrator.run_batch_crawler_workflow(
            sources=[mock_source],
            get_crawler_func=mock_get_crawler_func,
            crawler_func=mock_crawler_func,
            storage_func=mock_storage_func,
            update_source_func=mock_update_source_func,
            save_result_func=mock_save_result_func
        )
        
        # Check that the get_crawler_func was called
        mock_get_crawler_func.assert_called_once_with(mock_source.id)
        
        # Check that the other functions were not called
        mock_crawler_func.assert_not_called()
        mock_storage_func.assert_not_called()
        mock_update_source_func.assert_not_called()
        mock_save_result_func.assert_not_called()
        
        # Check the results
        assert len(results) == 0

