# MCP Tool Crawler

A crawler for discovering and cataloging MCP (Model Context Protocol) tools.

## Overview

The MCP Tool Crawler is a system for discovering, cataloging, and maintaining a database of MCP tools from various sources. It can crawl GitHub repositories, awesome lists, websites, and other sources to find and catalog MCP tools.

## Features

- Crawl various sources for MCP tools
- Store tools in a local SQLite database
- Generate crawlers for new sources
- Command-line interface for managing sources and crawling
- Extensible architecture for adding new crawler types

## Installation

```bash
# Clone the repository
git clone https://github.com/Zeeeepa/mcp-aas.git
cd mcp-aas/mcp-tool-crawler-py

# Install dependencies
pip install -e .
```

## Usage

```bash
# Initialize sources
python -m src.cli init

# List sources
python -m src.cli list

# Add a new source
python -m src.cli add https://github.com/example/awesome-mcp-tools --name "Example Awesome List" --type github_awesome_list

# Crawl a specific source
python -m src.cli crawl --id <source_id>

# Crawl all sources
python -m src.cli crawl --all

# Force crawl all sources
python -m src.cli crawl --all --force
```

## Configuration

Configuration is loaded from environment variables and `.env` file. See `src/utils/config.py` for available configuration options.

## Architecture

The MCP Tool Crawler consists of the following components:

- **Source Manager**: Manages sources for crawling
- **Crawler Service**: Orchestrates the crawling process
- **Storage**: Stores tools and sources in a SQLite database
- **Crawlers**: Implementations for different source types
- **CLI**: Command-line interface for interacting with the system

## Development

### Running Tests

```bash
# Run unit tests
pytest tests/unit

# Run integration tests
pytest tests/integration

# Run all tests
pytest
```

### Adding a New Crawler Type

1. Add a new value to the `SourceType` enum in `src/models.py`
2. Implement a crawler for the new source type in `src/crawlers/`
3. Update the `get_crawler_for_source` function in `src/crawlers/__init__.py`
4. Add a generator for the new source type in `src/lambda_functions/crawler_generator.py`

## License

See the [LICENSE](../LICENSE) file for details.

