"""
Workflow orchestration service for MCP tool crawler.

This module replaces AWS Step Functions with a local workflow orchestration mechanism.
"""

import asyncio
import json
import logging
import os
import sqlite3
import time
import uuid
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Union

from ..models import CrawlResult, CrawlerStrategy, Source, SourceType
from ..services.crawler_service import CrawlerService
from ..services.source_manager import SourceManager
from ..utils.config import get_config
from ..utils.logging import get_logger

logger = get_logger(__name__)
config = get_config()


class WorkflowStatus(str, Enum):
    """Enum for workflow execution status."""
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    ABORTED = "ABORTED"


class StepStatus(str, Enum):
    """Enum for step execution status."""
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"


class WorkflowStep:
    """Class representing a step in a workflow."""
    
    def __init__(
        self, 
        name: str, 
        function: Callable, 
        retry_config: Optional[Dict[str, Any]] = None,
        catch_config: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize a workflow step.
        
        Args:
            name: Name of the step.
            function: Function to execute for this step.
            retry_config: Configuration for retries.
            catch_config: Configuration for error handling.
        """
        self.name = name
        self.function = function
        self.retry_config = retry_config or {
            "max_attempts": 3,
            "interval_seconds": 2,
            "backoff_rate": 2
        }
        self.catch_config = catch_config or {
            "error_path": "$.error"
        }
        self.status = StepStatus.PENDING
        self.result = None
        self.error = None
        self.start_time = None
        self.end_time = None
        self.attempts = 0
    
    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the step function.
        
        Args:
            input_data: Input data for the step.
            
        Returns:
            The result of the step execution.
        """
        self.status = StepStatus.RUNNING
        self.start_time = datetime.now(timezone.utc).isoformat()
        self.attempts = 0
        
        try:
            # Execute the function with retries
            while True:
                self.attempts += 1
                
                try:
                    # Execute the function
                    if asyncio.iscoroutinefunction(self.function):
                        self.result = await self.function(input_data)
                    else:
                        self.result = self.function(input_data)
                    
                    # If successful, break the retry loop
                    self.status = StepStatus.SUCCEEDED
                    break
                    
                except Exception as e:
                    logger.error(f"Error executing step {self.name}: {str(e)}")
                    self.error = str(e)
                    
                    # Check if we should retry
                    if self.attempts < self.retry_config["max_attempts"]:
                        # Calculate backoff time
                        backoff_time = self.retry_config["interval_seconds"] * (
                            self.retry_config["backoff_rate"] ** (self.attempts - 1)
                        )
                        
                        logger.info(f"Retrying step {self.name} in {backoff_time} seconds (attempt {self.attempts}/{self.retry_config['max_attempts']})")
                        
                        # Wait for backoff time
                        await asyncio.sleep(backoff_time)
                    else:
                        # Max retries reached, mark as failed
                        self.status = StepStatus.FAILED
                        
                        # Check if we have a catch configuration
                        if self.catch_config:
                            # Set the error in the output
                            error_path = self.catch_config.get("error_path", "$.error")
                            if error_path.startswith("$."):
                                error_path = error_path[2:]
                            
                            # Create a result with the error
                            self.result = {error_path: str(e)}
                        
                        # Re-raise the exception
                        raise
            
            self.end_time = datetime.now(timezone.utc).isoformat()
            return self.result
            
        except Exception as e:
            self.status = StepStatus.FAILED
            self.end_time = datetime.now(timezone.utc).isoformat()
            raise
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the step to a dictionary.
        
        Returns:
            Dictionary representation of the step.
        """
        return {
            "name": self.name,
            "status": self.status,
            "result": self.result,
            "error": self.error,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "attempts": self.attempts
        }


class WorkflowExecution:
    """Class representing a workflow execution."""
    
    def __init__(self, workflow_id: str, workflow_name: str, input_data: Dict[str, Any]):
        """
        Initialize a workflow execution.
        
        Args:
            workflow_id: ID of the workflow.
            workflow_name: Name of the workflow.
            input_data: Input data for the workflow.
        """
        self.id = workflow_id
        self.workflow_name = workflow_name
        self.input_data = input_data
        self.status = WorkflowStatus.PENDING
        self.steps = []
        self.current_step_index = 0
        self.start_time = None
        self.end_time = None
        self.output = {}
    
    def add_step(self, step: WorkflowStep) -> None:
        """
        Add a step to the workflow.
        
        Args:
            step: Step to add.
        """
        self.steps.append(step)
    
    async def execute(self) -> Dict[str, Any]:
        """
        Execute the workflow.
        
        Returns:
            The result of the workflow execution.
        """
        self.status = WorkflowStatus.RUNNING
        self.start_time = datetime.now(timezone.utc).isoformat()
        
        # Initialize the workflow state
        state = self.input_data.copy()
        
        try:
            # Execute each step in sequence
            for i, step in enumerate(self.steps):
                self.current_step_index = i
                
                logger.info(f"Executing step {step.name} ({i+1}/{len(self.steps)})")
                
                try:
                    # Execute the step
                    step_result = await step.execute(state)
                    
                    # Update the state with the step result
                    if step_result is not None:
                        if isinstance(step_result, dict):
                            state.update(step_result)
                        else:
                            # If the result is not a dict, store it under the step name
                            state[step.name] = step_result
                    
                except Exception as e:
                    logger.error(f"Error executing step {step.name}: {str(e)}")
                    
                    # If the step has a catch configuration, continue with the next step
                    if step.catch_config:
                        # Update the state with the error
                        if step.result is not None:
                            state.update(step.result)
                        
                        # Continue with the next step
                        continue
                    else:
                        # No catch configuration, fail the workflow
                        self.status = WorkflowStatus.FAILED
                        self.end_time = datetime.now(timezone.utc).isoformat()
                        raise
            
            # All steps completed successfully
            self.status = WorkflowStatus.SUCCEEDED
            self.end_time = datetime.now(timezone.utc).isoformat()
            self.output = state
            
            return self.output
            
        except Exception as e:
            self.status = WorkflowStatus.FAILED
            self.end_time = datetime.now(timezone.utc).isoformat()
            raise
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the workflow execution to a dictionary.
        
        Returns:
            Dictionary representation of the workflow execution.
        """
        return {
            "id": self.id,
            "workflow_name": self.workflow_name,
            "status": self.status,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "steps": [step.to_dict() for step in self.steps],
            "current_step_index": self.current_step_index,
            "input": self.input_data,
            "output": self.output
        }


class WorkflowOrchestrator:
    """
    Service for orchestrating workflows locally.
    
    This class replaces AWS Step Functions with a local workflow orchestration mechanism.
    """
    
    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize the workflow orchestrator.
        
        Args:
            db_path: Path to the SQLite database file. If None, uses the default path.
        """
        # Set up the database path
        if db_path:
            self.db_path = db_path
        else:
            data_dir = Path(__file__).parents[3] / 'data'
            data_dir.mkdir(parents=True, exist_ok=True)
            self.db_path = str(data_dir / 'workflows.db')
        
        # Initialize the database
        self._init_db()
        
        # Initialize services
        self.source_manager = SourceManager()
        self.crawler_service = CrawlerService()
    
    def _init_db(self) -> None:
        """Initialize the SQLite database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create tables if they don't exist
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS workflow_executions (
            id TEXT PRIMARY KEY,
            workflow_name TEXT NOT NULL,
            status TEXT NOT NULL,
            start_time TEXT,
            end_time TEXT,
            input TEXT,
            output TEXT,
            current_step_index INTEGER DEFAULT 0
        )
        ''')
        
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS workflow_steps (
            id TEXT PRIMARY KEY,
            workflow_id TEXT NOT NULL,
            step_index INTEGER NOT NULL,
            name TEXT NOT NULL,
            status TEXT NOT NULL,
            start_time TEXT,
            end_time TEXT,
            result TEXT,
            error TEXT,
            attempts INTEGER DEFAULT 0,
            FOREIGN KEY (workflow_id) REFERENCES workflow_executions(id)
        )
        ''')
        
        conn.commit()
        conn.close()
    
    def _save_execution(self, execution: WorkflowExecution) -> None:
        """
        Save a workflow execution to the database.
        
        Args:
            execution: Workflow execution to save.
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Save the workflow execution
        cursor.execute(
            '''
            INSERT OR REPLACE INTO workflow_executions
            (id, workflow_name, status, start_time, end_time, input, output, current_step_index)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''',
            (
                execution.id,
                execution.workflow_name,
                execution.status,
                execution.start_time,
                execution.end_time,
                json.dumps(execution.input_data),
                json.dumps(execution.output),
                execution.current_step_index
            )
        )
        
        # Save the workflow steps
        for i, step in enumerate(execution.steps):
            cursor.execute(
                '''
                INSERT OR REPLACE INTO workflow_steps
                (id, workflow_id, step_index, name, status, start_time, end_time, result, error, attempts)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''',
                (
                    f"{execution.id}-step-{i}",
                    execution.id,
                    i,
                    step.name,
                    step.status,
                    step.start_time,
                    step.end_time,
                    json.dumps(step.result) if step.result is not None else None,
                    step.error,
                    step.attempts
                )
            )
        
        conn.commit()
        conn.close()
    
    def _load_execution(self, execution_id: str) -> Optional[Dict[str, Any]]:
        """
        Load a workflow execution from the database.
        
        Args:
            execution_id: ID of the workflow execution to load.
            
        Returns:
            Dictionary representation of the workflow execution, or None if not found.
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Get the workflow execution
        cursor.execute(
            'SELECT * FROM workflow_executions WHERE id = ?',
            (execution_id,)
        )
        execution_row = cursor.fetchone()
        
        if not execution_row:
            conn.close()
            return None
        
        # Get the workflow steps
        cursor.execute(
            'SELECT * FROM workflow_steps WHERE workflow_id = ? ORDER BY step_index',
            (execution_id,)
        )
        step_rows = cursor.fetchall()
        
        # Convert to dictionary
        execution_dict = dict(execution_row)
        execution_dict['input'] = json.loads(execution_dict['input'])
        execution_dict['output'] = json.loads(execution_dict['output']) if execution_dict['output'] else {}
        
        steps = []
        for step_row in step_rows:
            step_dict = dict(step_row)
            step_dict['result'] = json.loads(step_dict['result']) if step_dict['result'] else None
            steps.append(step_dict)
        
        execution_dict['steps'] = steps
        
        conn.close()
        return execution_dict
    
    def get_execution(self, execution_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a workflow execution by ID.
        
        Args:
            execution_id: ID of the workflow execution to get.
            
        Returns:
            Dictionary representation of the workflow execution, or None if not found.
        """
        return self._load_execution(execution_id)
    
    def list_executions(
        self, 
        status: Optional[WorkflowStatus] = None, 
        limit: int = 10, 
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        List workflow executions.
        
        Args:
            status: Filter by status.
            limit: Maximum number of executions to return.
            offset: Offset for pagination.
            
        Returns:
            List of workflow executions.
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Build the query
        query = 'SELECT * FROM workflow_executions'
        params = []
        
        if status:
            query += ' WHERE status = ?'
            params.append(status)
        
        query += ' ORDER BY start_time DESC LIMIT ? OFFSET ?'
        params.extend([limit, offset])
        
        # Execute the query
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        # Convert to dictionaries
        executions = []
        for row in rows:
            execution_dict = dict(row)
            execution_dict['input'] = json.loads(execution_dict['input'])
            execution_dict['output'] = json.loads(execution_dict['output']) if execution_dict['output'] else {}
            executions.append(execution_dict)
        
        conn.close()
        return executions
    
    async def start_execution(
        self, 
        workflow_name: str, 
        input_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Start a new workflow execution.
        
        Args:
            workflow_name: Name of the workflow to execute.
            input_data: Input data for the workflow.
            
        Returns:
            Dictionary with the execution ID and status.
        """
        # Generate a unique ID for the execution
        execution_id = f"execution-{uuid.uuid4()}"
        
        # Create the workflow execution
        execution = WorkflowExecution(execution_id, workflow_name, input_data)
        
        # Add steps based on the workflow name
        if workflow_name == "mcp-tool-crawler":
            self._create_mcp_tool_crawler_workflow(execution)
        else:
            raise ValueError(f"Unknown workflow: {workflow_name}")
        
        # Save the initial state
        self._save_execution(execution)
        
        # Execute the workflow asynchronously
        asyncio.create_task(self._execute_workflow(execution))
        
        return {
            "executionId": execution_id,
            "status": execution.status
        }
    
    async def _execute_workflow(self, execution: WorkflowExecution) -> None:
        """
        Execute a workflow and save the results.
        
        Args:
            execution: Workflow execution to execute.
        """
        try:
            # Execute the workflow
            await execution.execute()
        except Exception as e:
            logger.error(f"Error executing workflow {execution.workflow_name}: {str(e)}")
        finally:
            # Save the final state
            self._save_execution(execution)
    
    def _create_mcp_tool_crawler_workflow(self, execution: WorkflowExecution) -> None:
        """
        Create the MCP tool crawler workflow.
        
        Args:
            execution: Workflow execution to configure.
        """
        # Step 1: Initialize Sources
        execution.add_step(WorkflowStep(
            name="InitializeSources",
            function=self._initialize_sources,
            retry_config={
                "max_attempts": 3,
                "interval_seconds": 2,
                "backoff_rate": 2
            }
        ))
        
        # Step 2: Get Sources to Crawl
        execution.add_step(WorkflowStep(
            name="GetSourcesToCrawl",
            function=self._get_sources_to_crawl,
            retry_config={
                "max_attempts": 3,
                "interval_seconds": 2,
                "backoff_rate": 2
            }
        ))
        
        # Step 3: Check if Sources Exist
        execution.add_step(WorkflowStep(
            name="CheckSourcesExist",
            function=self._check_sources_exist
        ))
        
        # Step 4: Map Sources to Process (if sources exist)
        execution.add_step(WorkflowStep(
            name="MapSourcesToProcess",
            function=self._map_sources_to_process,
            retry_config={
                "max_attempts": 3,
                "interval_seconds": 2,
                "backoff_rate": 2
            }
        ))
        
        # Step 5: Process Catalog
        execution.add_step(WorkflowStep(
            name="ProcessCatalog",
            function=self._process_catalog,
            retry_config={
                "max_attempts": 3,
                "interval_seconds": 2,
                "backoff_rate": 2
            }
        ))
        
        # Step 6: Notify Crawl Complete
        execution.add_step(WorkflowStep(
            name="NotifyCrawlComplete",
            function=self._notify_crawl_complete
        ))
    
    async def _initialize_sources(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Initialize sources from configuration or S3.
        
        Args:
            input_data: Input data for the step.
            
        Returns:
            Dictionary with the result of the operation.
        """
        logger.info("Initializing sources")
        
        # Get S3 bucket and key from the input if available
        s3_bucket_name = input_data.get('s3BucketName')
        s3_source_list_key = input_data.get('s3SourceListKey')
        
        if s3_bucket_name and s3_source_list_key:
            logger.info(f"Initializing sources from S3: s3://{s3_bucket_name}/{s3_source_list_key}")
            # These will be used by the source manager to determine where to load sources from
            os.environ['S3_BUCKET_NAME'] = s3_bucket_name
            os.environ['S3_SOURCE_LIST_KEY'] = s3_source_list_key
        else:
            logger.info("No S3 information provided, using default configuration")
        
        # Initialize sources
        sources = await self.source_manager.initialize_sources()
        
        return {
            "sourceCount": len(sources),
            "message": f"Initialized {len(sources)} sources successfully"
        }
    
    async def _get_sources_to_crawl(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get sources that need to be crawled.
        
        Args:
            input_data: Input data for the step.
            
        Returns:
            Dictionary with the sources to crawl.
        """
        logger.info("Getting sources to crawl")
        
        # Get time threshold from input or use default
        time_threshold_hours = input_data.get('timeThreshold', 24)
        
        # Get sources to crawl
        sources = await self.source_manager.get_sources_to_crawl(time_threshold_hours)
        
        # Convert to JSON-serializable format
        sources_json = [source.dict() for source in sources]
        
        logger.info(f"Found {len(sources)} sources to crawl")
        
        return {
            "sources": sources_json
        }
    
    async def _check_sources_exist(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Check if sources exist.
        
        Args:
            input_data: Input data for the step.
            
        Returns:
            Dictionary with the result of the check.
        """
        logger.info("Checking if sources exist")
        
        # Get sources from input
        sources = input_data.get('sources', [])
        
        if not sources:
            logger.info("No sources to process")
            return {
                "sourcesExist": False,
                "message": "No sources to crawl"
            }
        
        logger.info(f"Found {len(sources)} sources to process")
        return {
            "sourcesExist": True
        }
    
    async def _map_sources_to_process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process each source.
        
        Args:
            input_data: Input data for the step.
            
        Returns:
            Dictionary with the results of processing each source.
        """
        logger.info("Processing sources")
        
        # Check if sources exist
        if not input_data.get('sourcesExist', False):
            logger.info("No sources to process, skipping")
            return {
                "crawlResults": []
            }
        
        # Get sources from input
        sources_data = input_data.get('sources', [])
        
        if not sources_data:
            logger.info("No sources to process")
            return {
                "crawlResults": []
            }
        
        # Convert to Source objects
        sources = [Source(**source_data) for source_data in sources_data]
        
        # Process each source concurrently with limited concurrency
        concurrency = config.get('crawler', {}).get('concurrency_limit', 5)
        logger.info(f"Processing {len(sources)} sources with concurrency {concurrency}")
        
        # Create tasks for each source
        tasks = []
        semaphore = asyncio.Semaphore(concurrency)
        
        async def process_source_with_semaphore(source):
            async with semaphore:
                return await self._process_source(source)
        
        for source in sources:
            tasks.append(process_source_with_semaphore(source))
        
        # Run all tasks concurrently with limited concurrency
        results = await asyncio.gather(*tasks)
        
        # Convert to JSON-serializable format
        results_json = [result.dict() for result in results]
        
        return {
            "crawlResults": results_json
        }
    
    async def _process_source(self, source: Source) -> CrawlResult:
        """
        Process a single source.
        
        Args:
            source: Source to process.
            
        Returns:
            CrawlResult object with the result of processing the source.
        """
        logger.info(f"Processing source: {source.name} ({source.url})")
        
        # Check if the source has a known crawler
        if source.has_known_crawler:
            # Use the known crawler
            return await self._run_known_crawler(source)
        else:
            # Generate a crawler strategy
            strategy = await self._generate_crawler_strategy(source)
            
            # Save the crawler strategy
            await self._save_crawler_strategy(source, strategy)
            
            # Run the generated crawler
            return await self._run_generated_crawler(source, strategy)
    
    async def _generate_crawler_strategy(self, source: Source) -> CrawlerStrategy:
        """
        Generate a crawler strategy for a source.
        
        Args:
            source: Source to generate a crawler strategy for.
            
        Returns:
            CrawlerStrategy object.
        """
        logger.info(f"Generating crawler strategy for source: {source.name} ({source.url})")
        
        # This would normally call the crawler generator service
        # For now, we'll just create a dummy strategy
        timestamp = datetime.now(timezone.utc).isoformat()
        
        strategy = CrawlerStrategy(
            id=f"crawler-{uuid.uuid4()}",
            source_id=source.id,
            source_type=source.type,
            implementation="def extract_tools(html):\n    return []",
            description=f"Generated crawler for {source.name}",
            created=timestamp,
            last_modified=timestamp
        )
        
        return strategy
    
    async def _save_crawler_strategy(self, source: Source, strategy: CrawlerStrategy) -> None:
        """
        Save a crawler strategy.
        
        Args:
            source: Source the strategy is for.
            strategy: CrawlerStrategy to save.
        """
        logger.info(f"Saving crawler strategy for source: {source.name} ({source.url})")
        
        # This would normally save the strategy to storage
        # For now, we'll just log it
        logger.info(f"Saved crawler strategy: {strategy.id}")
    
    async def _run_known_crawler(self, source: Source) -> CrawlResult:
        """
        Run a known crawler for a source.
        
        Args:
            source: Source to crawl.
            
        Returns:
            CrawlResult object with the result of crawling the source.
        """
        logger.info(f"Running known crawler for source: {source.name} ({source.url})")
        
        # Use the crawler service to crawl the source
        return await self.crawler_service.crawl_source(source)
    
    async def _run_generated_crawler(self, source: Source, strategy: CrawlerStrategy) -> CrawlResult:
        """
        Run a generated crawler for a source.
        
        Args:
            source: Source to crawl.
            strategy: CrawlerStrategy to use.
            
        Returns:
            CrawlResult object with the result of crawling the source.
        """
        logger.info(f"Running generated crawler for source: {source.name} ({source.url})")
        
        # This would normally run the generated crawler
        # For now, we'll just return a dummy result
        return CrawlResult(
            source_id=source.id,
            success=True,
            tools_discovered=0,
            new_tools=0,
            updated_tools=0,
            duration=0
        )
    
    async def _process_catalog(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process the catalog after crawling.
        
        Args:
            input_data: Input data for the step.
            
        Returns:
            Dictionary with the result of processing the catalog.
        """
        logger.info("Processing catalog")
        
        # Get crawl results from input
        crawl_results = input_data.get('crawlResults', [])
        
        if not crawl_results:
            logger.info("No crawl results to process")
            return {
                "catalogProcessed": False,
                "message": "No crawl results to process"
            }
        
        # Calculate totals
        total_tools = sum(result.get('tools_discovered', 0) for result in crawl_results if result.get('success', False))
        total_new_tools = sum(result.get('new_tools', 0) for result in crawl_results if result.get('success', False))
        total_updated_tools = sum(result.get('updated_tools', 0) for result in crawl_results if result.get('success', False))
        success_count = sum(1 for result in crawl_results if result.get('success', False))
        
        logger.info(f"Processed catalog with {len(crawl_results)} crawl results:")
        logger.info(f"- Success: {success_count}")
        logger.info(f"- Failed: {len(crawl_results) - success_count}")
        logger.info(f"- Total tools discovered: {total_tools}")
        logger.info(f"- New tools: {total_new_tools}")
        logger.info(f"- Updated tools: {total_updated_tools}")
        
        return {
            "catalogProcessed": True,
            "summary": {
                "total_sources": len(crawl_results),
                "success_count": success_count,
                "failure_count": len(crawl_results) - success_count,
                "total_tools": total_tools,
                "new_tools": total_new_tools,
                "updated_tools": total_updated_tools
            }
        }
    
    async def _notify_crawl_complete(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Notify that the crawl is complete.
        
        Args:
            input_data: Input data for the step.
            
        Returns:
            Dictionary with the notification result.
        """
        logger.info("Notifying crawl complete")
        
        # Get summary from input
        summary = input_data.get('summary', {})
        
        # Log the summary
        logger.info(f"Crawl complete: {summary}")
        
        return {
            "notified": True,
            "message": "MCP Tool Crawler completed",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

