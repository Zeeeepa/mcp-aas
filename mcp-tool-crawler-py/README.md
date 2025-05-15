# MCP Tool Crawler

A tool for crawling and cataloging MCP (Machine Context Protocol) tools from various sources.

## Overview

The MCP Tool Crawler is a Python application that discovers, catalogs, and maintains a database of MCP tools from various sources such as GitHub repositories, awesome lists, and websites.

## Features

- Crawl multiple sources for MCP tools
- Generate crawler strategies using AI for new websites
- Store tool information in a local SQLite database
- Command-line interface for managing the crawler

## Installation

```bash
# Clone the repository
git clone https://github.com/Zeeeepa/mcp-aas.git
cd mcp-aas/mcp-tool-crawler-py

# Install dependencies
pip install -r requirements.txt
```

## Usage

### Command-line Interface

The crawler provides a command-line interface for various operations:

```bash
# Initialize sources
python -m src.cli init

# Get sources that need to be crawled
python -m src.cli get-sources --threshold 24

# Crawl a specific source
python -m src.cli crawl-source --source-id <id> --source-url <url> --source-name <name> --source-type <type>

# Crawl all sources
python -m src.cli crawl-all --force

# Generate a crawler strategy for a website
python -m src.cli generate --source-id <id> --source-url <url> --source-name <name> --source-type <type>

# Run a generated crawler
python -m src.cli run --source-id <id> --source-url <url> --source-name <name> --source-type <type> --strategy-id <id> --strategy-file <file>
```

### Environment Variables

The crawler can be configured using environment variables:

- `ENVIRONMENT`: Environment to run in (`local`, `development`, `production`)
- `STORAGE_TYPE`: Storage type to use (`sqlite`, `aws`)
- `OPENAI_API_KEY`: OpenAI API key for generating crawler strategies
- `OPENAI_MODEL`: OpenAI model to use (default: `gpt-4`)
- `CRAWLER_TIMEOUT`: Timeout for crawler operations in milliseconds (default: `30000`)
- `CRAWLER_USER_AGENT`: User agent to use for HTTP requests (default: `MCP-Tool-Crawler/1.0`)
- `CRAWLER_CONCURRENCY_LIMIT`: Maximum number of sources to crawl concurrently (default: `5`)

## Architecture

The crawler is designed with a modular architecture:

- **Models**: Data structures for sources, tools, crawler strategies, and crawl results
- **Services**: Business logic for managing sources, generating crawlers, and executing crawls
- **Storage**: Storage implementations for SQLite and AWS (S3, DynamoDB)
- **Utils**: Utility functions for logging, configuration, and helpers

## Development

### Project Structure

```
mcp-tool-crawler-py/
├── data/                  # Data directory for SQLite database and local files
├── src/
│   ├── crawlers/          # Crawler implementations for different source types
│   ├── lambda_functions/  # Legacy AWS Lambda functions (deprecated)
│   ├── models.py          # Data models
│   ├── services/          # Business logic services
│   │   ├── crawler/       # Crawler services
│   │   │   ├── crawler_generator.py  # AI-based crawler generation
│   │   │   ├── crawler_executor.py   # Crawler execution
│   │   │   └── crawler_manager.py    # Crawler orchestration
│   │   ├── source_manager.py         # Source management
│   │   └── source_initializer.py     # Source initialization
│   ├── storage/           # Storage implementations
│   │   ├── local_storage.py          # Local file storage
│   │   ├── s3_storage.py             # AWS S3 storage
│   │   └── sqlite_storage.py         # SQLite storage
│   ├── utils/             # Utility functions
│   ├── cli.py             # Command-line interface
│   └── main.py            # Main entry point
└── tests/                 # Tests
```

### Adding a New Source Type

To add a new source type:

1. Add the new type to the `SourceType` enum in `models.py`
2. Create a new crawler implementation in the `crawlers` directory
3. Update the `get_crawler_for_source` function in `crawlers/__init__.py`

### Adding a New Storage Backend

To add a new storage backend:

1. Create a new storage implementation in the `storage` directory
2. Update the `get_storage` function in `storage/__init__.py`

## License

[MIT License](LICENSE)

