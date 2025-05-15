# MCP Tool Crawler

A crawler for discovering and cataloging MCP (Model Context Protocol) tools.

## Overview

The MCP Tool Crawler is a service that crawls various sources (websites, GitHub repositories, etc.) to discover and catalog MCP tools. It uses a workflow orchestration mechanism to coordinate the crawling process.

## Local Workflow Orchestration

This implementation uses a local workflow orchestration mechanism instead of AWS Step Functions. The workflow is managed by the `WorkflowOrchestrator` class, which uses SQLite for state management and persistence.

### Key Components

- **WorkflowOrchestrator**: Manages workflow execution, state, and persistence
- **FileWatcher**: Monitors the file system for changes to the source list file
- **SQLiteStorage**: Stores tools, sources, and crawler strategies in a SQLite database
- **CLI Scripts**: Run the crawler and file watcher from the command line

## Getting Started

### Prerequisites

- Python 3.8 or higher
- pip

### Installation

1. Clone the repository:
   ```
   git clone https://github.com/Zeeeepa/mcp-aas.git
   cd mcp-aas/mcp-tool-crawler-py
   ```

2. Install the dependencies:
   ```
   pip install -r requirements.txt
   ```

### Usage

#### Running the Crawler

To run the crawler manually:

```
python -m src.cli.run_crawler
```

Optional arguments:
- `--source-list`: Path to the source list file
- `--time-threshold`: Time threshold in hours (default: 24)

#### Running the File Watcher

To start the file watcher service:

```
python -m src.cli.run_file_watcher
```

Optional arguments:
- `--watch-dir`: Directory to watch for changes
- `--source-list-filename`: Name of the source list file (default: sources.yaml)

### Configuration

The crawler can be configured using environment variables or a configuration file.

#### Environment Variables

- `USE_LOCAL_STORAGE`: Set to "true" to use local storage instead of SQLite (default: "false")
- `LOG_LEVEL`: Set the logging level (default: "INFO")

#### Source List File

The source list file is a YAML file that defines the sources to crawl. Example:

```yaml
sources:
  - url: https://example.com/mcp-tools
    name: Example MCP Tools
    type: WEBSITE
  - url: https://github.com/example/awesome-mcp
    name: Awesome MCP
    type: GITHUB_AWESOME_LIST
```

## Development

### Running Tests

To run the tests:

```
pytest
```

### Code Style

This project uses:
- black for code formatting
- isort for import sorting
- flake8 for linting
- mypy for type checking

To format the code:

```
black .
isort .
```

To check the code:

```
flake8
mypy .
```

