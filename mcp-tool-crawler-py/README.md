# MCP Tool Crawler

A Python-based service for discovering, crawling, and cataloging Machine Context Protocol (MCP) tools from various sources.

## Overview

The MCP Tool Crawler discovers and catalogs tools that implement the Model Context Protocol from various sources, including GitHub repositories, awesome lists, and websites. It stores the discovered tools in a local database and provides a command-line interface for managing the crawling process.

## Features

- Crawl GitHub awesome lists for MCP tools
- Crawl websites for MCP tools
- Store tools in a local database
- Export tools to JSON format
- Command-line interface for managing the crawling process

## Storage Options

The MCP Tool Crawler supports multiple storage backends:

1. **SQLite Storage** (default): Local SQLite database for storing tools, sources, and crawler data
2. **Local Storage**: Simple JSON file-based storage for tools
3. **S3 Storage**: AWS S3-based storage for production environments

See [SQLite Storage Documentation](SQLITE_STORAGE.md) for details on the SQLite implementation.

## Source List Management

Sources to crawl are managed in a YAML file (`sample-sources.yaml`) which can be loaded automatically.

### YAML Format

The source list YAML has the following format:

```yaml
sources:
  - url: https://github.com/user/awesome-repo
    name: Awesome Repository
    type: github_awesome_list
  - url: https://example.com/tools
    name: Example Tools
    type: website
```

Fields:
- `url`: The URL of the source to crawl (required)
- `name`: A friendly name for the source (optional, will be auto-generated if not provided)
- `type`: The source type (optional, will be auto-detected if not provided):
  - `github_awesome_list`: GitHub awesome list
  - `github_repository`: GitHub repository
  - `website`: Generic website
  - `rss_feed`: RSS feed
  - `manually_added`: Manually added source

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

The MCP Tool Crawler can be configured using environment variables or a `.env` file:

- `ENVIRONMENT`: Set to `development` (default) to use SQLite storage, or `production` to use S3 storage
- `STORAGE_TYPE`: Set to `sqlite` (default) to use SQLite storage, `local` to use local JSON storage, or `s3` to use S3 storage

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

## Security Considerations

- **Input Validation**: All user inputs and API responses are validated
- **Rate Limiting**: API throttling for external dependencies
- **Logging & Monitoring**: Comprehensive logging and monitoring

## Future Enhancements

- **Advanced Deduplication**: ML-based similarity detection for tools
- **Web UI**: Management interface for sources and tools
- **Additional Sources**: Support for more types of sources
- **Enhanced Metadata**: Extract and normalize more tool metadata
- **CI/CD Pipeline**: Automated testing and deployment

