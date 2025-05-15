# MCP Tool Crawler Tests

This directory contains tests for the MCP Tool Crawler system.

## Test Structure

The tests are organized as follows:

- `models/`: Tests for the data models
- `storage/`: Tests for the storage implementations (SQLite, local file storage)
- `services/`: Tests for the service implementations (SourceManager, etc.)
- `modules/`: Tests for the module implementations (converted Lambda functions)
- `workflow/`: Tests for the workflow orchestrator
- `integration/`: Integration tests for the complete system

## Running Tests

To run all tests:

```bash
cd mcp-tool-crawler-py
pytest
```

To run a specific test file:

```bash
pytest tests/storage/test_sqlite_storage.py
```

To run tests with verbose output:

```bash
pytest -v
```

## Test Coverage

To measure test coverage and generate a report:

```bash
cd mcp-tool-crawler-py
pytest -xvs tests/test_coverage.py
```

This will run all tests and generate a coverage report in `coverage_html/index.html`.

## Test Fixtures

The test fixtures are defined in `conftest.py`. These include:

- `temp_db_path`: Creates a temporary SQLite database file
- `temp_file_path`: Creates a temporary file
- `temp_dir_path`: Creates a temporary directory
- `sqlite_connection`: Creates a SQLite connection to a temporary database
- `sqlite_storage`: Creates a SQLiteStorage instance with a temporary database
- `local_storage`: Creates a LocalStorage instance with a temporary file
- `source_manager`: Creates a SourceManager instance with a temporary database

## Adding New Tests

When adding new tests:

1. Create a new test file in the appropriate directory
2. Import the necessary modules and fixtures
3. Create test classes and methods
4. Use pytest fixtures for setup and teardown
5. Use pytest.mark.asyncio for async tests

Example:

```python
import pytest
from src.models import Source, SourceType

class TestMyFeature:
    @pytest.mark.asyncio
    async def test_my_async_function(self, sqlite_storage):
        # Test code here
        pass
```

