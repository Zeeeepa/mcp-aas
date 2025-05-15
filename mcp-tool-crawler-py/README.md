# MCP Tool Crawler

A tool for crawling and cataloging MCP (Model Context Protocol) tools from various sources.

## Overview

The MCP Tool Crawler discovers and catalogs tools that implement the Model Context Protocol from various sources, including GitHub repositories, awesome lists, and websites. It stores the discovered tools in a local SQLite database and provides a command-line interface for managing the crawling process.

## Features

- Crawl GitHub awesome lists for MCP tools
- Crawl websites for MCP tools
- Store tools in a local SQLite database
- Export tools to JSON format
- Command-line interface for managing the crawling process

## Installation

1. Clone the repository:

```bash
git clone https://github.com/Zeeeepa/mcp-aas.git
cd mcp-aas/mcp-tool-crawler-py
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

## Configuration

The MCP Tool Crawler can be configured using environment variables or a `.env` file. See the [configuration documentation](./docs/configuration.md) for details.

## Usage

### Command-line Interface

The MCP Tool Crawler provides a command-line interface for managing the crawling process:

```bash
# Initialize sources
python -m src.cli init-sources

# Crawl all sources
python -m src.cli crawl-all

# Crawl a specific source
python -m src.cli crawl-source --url https://github.com/example/awesome-list

# Add a new source
python -m src.cli add-source --url https://github.com/example/awesome-list --name "Example Awesome List"

# Export tools to JSON
python -m src.cli export-tools --output tools.json
```

### Python API

The MCP Tool Crawler can also be used as a Python library:

```python
import asyncio
from src.services.source_manager import SourceManager
from src.services.crawler_service import CrawlerService

async def main():
    # Initialize sources
    source_manager = SourceManager()
    sources = await source_manager.initialize_sources()
    
    # Crawl sources
    crawler_service = CrawlerService()
    results = await crawler_service.crawl_all_sources()
    
    print(f"Crawled {len(results)} sources")

if __name__ == "__main__":
    asyncio.run(main())
```

## Storage

The MCP Tool Crawler supports two storage options:

1. **SQLite Storage** (default): Uses a SQLite database to store tools and sources.
2. **Local File Storage**: Uses JSON and YAML files to store tools and sources.

You can switch between these options by setting the `USE_SQLITE` environment variable to `true` or `false`.

## Development

### Running Tests

```bash
pytest
```

### Code Style

```bash
flake8 src tests
```

## License

[MIT](LICENSE)

