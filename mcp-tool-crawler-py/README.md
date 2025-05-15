# MCP Tool Crawler

A Python tool for discovering and crawling MCP (Model Context Protocol) tools from various sources.

## Features

- Discover MCP tools from GitHub awesome lists
- Store tool information locally in SQLite or JSON files
- Simple command-line interface
- No authentication required for basic usage

## Installation

1. Clone the repository:
```bash
git clone https://github.com/Zeeeepa/mcp-aas.git
cd mcp-aas/mcp-tool-crawler-py
```

2. Install the package:
```bash
pip install -e .
```

## Usage

### Initialize Sources

Initialize the crawler with predefined sources:

```bash
python -m src.cli init
```

### List Sources

List all available sources:

```bash
python -m src.cli list
```

### Add a Source

Add a new source:

```bash
python -m src.cli add https://github.com/username/repo
```

You can also specify a name and type:

```bash
python -m src.cli add https://github.com/username/repo --name "My Awesome List" --type github_awesome_list
```

### Crawl Sources

Crawl a specific source by ID:

```bash
python -m src.cli crawl --id source-12345678
```

Crawl all sources:

```bash
python -m src.cli crawl --all
```

Force crawl all sources (ignoring last crawl time):

```bash
python -m src.cli crawl --all --force
```

Limit concurrency:

```bash
python -m src.cli crawl --all --concurrency 3
```

## Configuration

The crawler can be configured using environment variables or a `.env` file in the project root:

```
# Data storage paths
DATA_DIR=./data
SQLITE_DB_PATH=./data/mcp_tools.db
TOOLS_FILE_PATH=./data/tools.json
SOURCES_FILE_PATH=./data/sources.yaml

# GitHub API (optional)
GITHUB_TOKEN=your_github_token

# Crawler Settings
CRAWLER_TIMEOUT=30000
CRAWLER_USER_AGENT=MCP-Tool-Crawler/1.0
CRAWLER_CONCURRENCY_LIMIT=5

# Logging
LOG_LEVEL=INFO
LOG_FILE_PATH=./logs/mcp_tool_crawler.log
```

Note: The GitHub token is optional but recommended to avoid rate limiting when crawling GitHub repositories.

## Storage Options

The crawler supports two storage options:

1. **SQLite**: Default storage option, stores data in a SQLite database.
2. **Local**: Stores data in JSON and YAML files.

You can switch between storage options by modifying the `storage_type` parameter in the `SourceManager` constructor in `src/source_manager.py`.

## Development

### Running Tests

```bash
pytest
```

### Adding a New Crawler

To add a new crawler for a different source type:

1. Create a new crawler class that extends `BaseCrawler` in `src/crawler.py`
2. Implement the `discover_tools` method
3. Add the new source type to the `SourceType` enum in `src/models.py`
4. Update the `CrawlerFactory.create_crawler` method to support the new source type

