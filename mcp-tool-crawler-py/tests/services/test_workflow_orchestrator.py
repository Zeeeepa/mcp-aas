"""
Unit tests for the workflow orchestrator.
"""

import asyncio
import os
import tempfile
import unittest
from unittest.mock import patch, MagicMock

from src.services.workflow_orchestrator import (
    WorkflowOrchestrator,
    WorkflowExecution,
    WorkflowStep,
    WorkflowStatus,
    StepStatus
)


class TestWorkflowOrchestrator(unittest.TestCase):
    """Test cases for the WorkflowOrchestrator class."""
    
    def setUp(self):
        """Set up the test environment."""
        # Create a temporary database file
        self.temp_db = tempfile.NamedTemporaryFile(delete=False)
        self.temp_db.close()
        
        # Create the workflow orchestrator with the temporary database
        self.orchestrator = WorkflowOrchestrator(db_path=self.temp_db.name)
    
    def tearDown(self):
        """Clean up the test environment."""
        # Remove the temporary database file
        os.unlink(self.temp_db.name)
    
    def test_init_db(self):
        """Test that the database is initialized correctly."""
        # The database should have been initialized in setUp
        # We can verify by checking that the tables exist
        import sqlite3
        conn = sqlite3.connect(self.temp_db.name)
        cursor = conn.cursor()
        
        # Check if the workflow_executions table exists
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='workflow_executions'"
        )
        self.assertIsNotNone(cursor.fetchone())
        
        # Check if the workflow_steps table exists
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='workflow_steps'"
        )
        self.assertIsNotNone(cursor.fetchone())
        
        conn.close()
    
    @patch('src.services.workflow_orchestrator.WorkflowExecution')
    def test_start_execution(self, mock_execution):
        """Test starting a workflow execution."""
        # Mock the WorkflowExecution class
        mock_execution_instance = MagicMock()
        mock_execution_instance.id = "test-execution-id"
        mock_execution_instance.status = WorkflowStatus.PENDING
        mock_execution.return_value = mock_execution_instance
        
        # Start a workflow execution
        result = asyncio.run(self.orchestrator.start_execution(
            workflow_name="mcp-tool-crawler",
            input_data={"test": "data"}
        ))
        
        # Check that the execution was created
        self.assertEqual(result["executionId"], "test-execution-id")
        self.assertEqual(result["status"], WorkflowStatus.PENDING)
        
        # Check that the _create_mcp_tool_crawler_workflow method was called
        mock_execution_instance._create_mcp_tool_crawler_workflow.assert_called_once()
        
        # Check that the execution was saved
        self.orchestrator._save_execution.assert_called_once_with(mock_execution_instance)
    
    def test_get_execution(self):
        """Test getting a workflow execution."""
        # Mock the _load_execution method
        self.orchestrator._load_execution = MagicMock(return_value={"id": "test-execution-id"})
        
        # Get an execution
        execution = self.orchestrator.get_execution("test-execution-id")
        
        # Check that the execution was loaded
        self.assertEqual(execution["id"], "test-execution-id")
        self.orchestrator._load_execution.assert_called_once_with("test-execution-id")
    
    def test_list_executions(self):
        """Test listing workflow executions."""
        # Create a test database with some executions
        import sqlite3
        conn = sqlite3.connect(self.temp_db.name)
        cursor = conn.cursor()
        
        # Insert some test executions
        cursor.execute(
            '''
            INSERT INTO workflow_executions
            (id, workflow_name, status, start_time, end_time, input, output, current_step_index)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''',
            (
                "test-execution-1",
                "mcp-tool-crawler",
                WorkflowStatus.SUCCEEDED,
                "2021-01-01T00:00:00Z",
                "2021-01-01T00:01:00Z",
                '{"test": "data"}',
                '{"result": "success"}',
                0
            )
        )
        
        cursor.execute(
            '''
            INSERT INTO workflow_executions
            (id, workflow_name, status, start_time, end_time, input, output, current_step_index)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''',
            (
                "test-execution-2",
                "mcp-tool-crawler",
                WorkflowStatus.FAILED,
                "2021-01-01T00:02:00Z",
                "2021-01-01T00:03:00Z",
                '{"test": "data"}',
                '{"error": "failure"}',
                0
            )
        )
        
        conn.commit()
        conn.close()
        
        # List all executions
        executions = self.orchestrator.list_executions()
        
        # Check that both executions were returned
        self.assertEqual(len(executions), 2)
        
        # List only succeeded executions
        executions = self.orchestrator.list_executions(status=WorkflowStatus.SUCCEEDED)
        
        # Check that only the succeeded execution was returned
        self.assertEqual(len(executions), 1)
        self.assertEqual(executions[0]["id"], "test-execution-1")
        
        # List only failed executions
        executions = self.orchestrator.list_executions(status=WorkflowStatus.FAILED)
        
        # Check that only the failed execution was returned
        self.assertEqual(len(executions), 1)
        self.assertEqual(executions[0]["id"], "test-execution-2")


class TestWorkflowExecution(unittest.TestCase):
    """Test cases for the WorkflowExecution class."""
    
    def test_add_step(self):
        """Test adding a step to a workflow execution."""
        # Create a workflow execution
        execution = WorkflowExecution(
            workflow_id="test-execution-id",
            workflow_name="test-workflow",
            input_data={"test": "data"}
        )
        
        # Create a step
        step = WorkflowStep(
            name="test-step",
            function=lambda x: {"result": "success"}
        )
        
        # Add the step to the execution
        execution.add_step(step)
        
        # Check that the step was added
        self.assertEqual(len(execution.steps), 1)
        self.assertEqual(execution.steps[0], step)
    
    async def _test_step_function(self, input_data):
        """Test step function that returns a result."""
        return {"result": "success"}
    
    async def _test_step_function_error(self, input_data):
        """Test step function that raises an error."""
        raise ValueError("Test error")
    
    def test_execute_success(self):
        """Test executing a workflow with successful steps."""
        # Create a workflow execution
        execution = WorkflowExecution(
            workflow_id="test-execution-id",
            workflow_name="test-workflow",
            input_data={"test": "data"}
        )
        
        # Add a step
        execution.add_step(WorkflowStep(
            name="test-step",
            function=self._test_step_function
        ))
        
        # Execute the workflow
        result = asyncio.run(execution.execute())
        
        # Check that the workflow executed successfully
        self.assertEqual(execution.status, WorkflowStatus.SUCCEEDED)
        self.assertEqual(result["result"], "success")
        self.assertEqual(execution.steps[0].status, StepStatus.SUCCEEDED)
    
    def test_execute_error(self):
        """Test executing a workflow with a failing step."""
        # Create a workflow execution
        execution = WorkflowExecution(
            workflow_id="test-execution-id",
            workflow_name="test-workflow",
            input_data={"test": "data"}
        )
        
        # Add a step that will fail
        execution.add_step(WorkflowStep(
            name="test-step",
            function=self._test_step_function_error
        ))
        
        # Execute the workflow
        with self.assertRaises(ValueError):
            asyncio.run(execution.execute())
        
        # Check that the workflow failed
        self.assertEqual(execution.status, WorkflowStatus.FAILED)
        self.assertEqual(execution.steps[0].status, StepStatus.FAILED)
    
    def test_execute_error_with_catch(self):
        """Test executing a workflow with a failing step that has a catch configuration."""
        # Create a workflow execution
        execution = WorkflowExecution(
            workflow_id="test-execution-id",
            workflow_name="test-workflow",
            input_data={"test": "data"}
        )
        
        # Add a step that will fail but has a catch configuration
        execution.add_step(WorkflowStep(
            name="test-step",
            function=self._test_step_function_error,
            catch_config={"error_path": "$.error"}
        ))
        
        # Add a second step that will succeed
        execution.add_step(WorkflowStep(
            name="test-step-2",
            function=self._test_step_function
        ))
        
        # Execute the workflow
        result = asyncio.run(execution.execute())
        
        # Check that the workflow executed successfully despite the first step failing
        self.assertEqual(execution.status, WorkflowStatus.SUCCEEDED)
        self.assertEqual(execution.steps[0].status, StepStatus.FAILED)
        self.assertEqual(execution.steps[1].status, StepStatus.SUCCEEDED)
        self.assertEqual(result["error"], "Test error")
        self.assertEqual(result["result"], "success")


class TestWorkflowStep(unittest.TestCase):
    """Test cases for the WorkflowStep class."""
    
    async def _test_function(self, input_data):
        """Test function that returns a result."""
        return {"result": "success"}
    
    async def _test_function_error(self, input_data):
        """Test function that raises an error."""
        raise ValueError("Test error")
    
    def test_execute_success(self):
        """Test executing a step successfully."""
        # Create a step
        step = WorkflowStep(
            name="test-step",
            function=self._test_function
        )
        
        # Execute the step
        result = asyncio.run(step.execute({"test": "data"}))
        
        # Check that the step executed successfully
        self.assertEqual(step.status, StepStatus.SUCCEEDED)
        self.assertEqual(result["result"], "success")
    
    def test_execute_error(self):
        """Test executing a step that raises an error."""
        # Create a step
        step = WorkflowStep(
            name="test-step",
            function=self._test_function_error
        )
        
        # Execute the step
        with self.assertRaises(ValueError):
            asyncio.run(step.execute({"test": "data"}))
        
        # Check that the step failed
        self.assertEqual(step.status, StepStatus.FAILED)
        self.assertEqual(step.error, "Test error")
    
    def test_execute_retry(self):
        """Test executing a step with retries."""
        # Create a mock function that fails the first time but succeeds the second time
        mock_function = MagicMock(side_effect=[ValueError("Test error"), {"result": "success"}])
        
        # Create a step with retry configuration
        step = WorkflowStep(
            name="test-step",
            function=mock_function,
            retry_config={
                "max_attempts": 2,
                "interval_seconds": 0,  # No delay for testing
                "backoff_rate": 1
            }
        )
        
        # Execute the step
        result = asyncio.run(step.execute({"test": "data"}))
        
        # Check that the step executed successfully after retrying
        self.assertEqual(step.status, StepStatus.SUCCEEDED)
        self.assertEqual(result["result"], "success")
        self.assertEqual(step.attempts, 2)
        
        # Check that the function was called twice
        self.assertEqual(mock_function.call_count, 2)
    
    def test_execute_max_retries(self):
        """Test executing a step that fails after max retries."""
        # Create a mock function that always fails
        mock_function = MagicMock(side_effect=ValueError("Test error"))
        
        # Create a step with retry configuration
        step = WorkflowStep(
            name="test-step",
            function=mock_function,
            retry_config={
                "max_attempts": 3,
                "interval_seconds": 0,  # No delay for testing
                "backoff_rate": 1
            }
        )
        
        # Execute the step
        with self.assertRaises(ValueError):
            asyncio.run(step.execute({"test": "data"}))
        
        # Check that the step failed after max retries
        self.assertEqual(step.status, StepStatus.FAILED)
        self.assertEqual(step.error, "Test error")
        self.assertEqual(step.attempts, 3)
        
        # Check that the function was called three times
        self.assertEqual(mock_function.call_count, 3)


if __name__ == "__main__":
    unittest.main()

