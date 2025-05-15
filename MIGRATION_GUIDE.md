# Migration Guide: AWS to Local Storage

This guide provides step-by-step instructions for migrating the MCP Tool Crawler from AWS-based storage to local storage with SQLite.

## Overview of Changes

The MCP Tool Crawler has been updated to remove AWS dependencies and use local storage alternatives:

| AWS Service | Local Alternative |
|-------------|-------------------|
| DynamoDB | SQLite |
| S3 | Local File System |
| Lambda | Local Python Functions |
| Step Functions | Direct Function Calls |

## Prerequisites

- Python 3.8 or higher
- SQLite 3.x (included with Python)
- Git (for cloning the repository)

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/Zeeeepa/mcp-aas.git
   cd mcp-aas
   ```

2. Install dependencies:
   ```bash
   # Using pip
   pip install -e .
   
   # Or using Poetry
   poetry install
   ```

## Configuration

### 1. Create a Configuration File

Create a `.env` file in the root directory with the following settings:

```
# Storage Configuration
STORAGE_TYPE=sqlite
SQLITE_DB_PATH=./data/mcp_crawler.db
LOCAL_STORAGE_PATH=./data

# Crawler Settings
CRAWLER_TIMEOUT=30000
CRAWLER_USER_AGENT=MCP-Tool-Crawler/1.0
CRAWLER_CONCURRENCY_LIMIT=5

# GitHub API (optional, for crawling GitHub repositories)
GITHUB_TOKEN=your_github_token

# OpenAI Configuration (optional, for AI-powered crawler generation)
OPENAI_API_KEY=your_openai_api_key
OPENAI_MODEL=gpt-4

# Logging
LOG_LEVEL=INFO
```

### 2. Initialize the Database

Run the initialization script to create the SQLite database and tables:

```bash
python -m mcp_tool_crawler.cli init
```

## Migrating Data from AWS

If you have existing data in AWS that you want to migrate to the local storage:

### 1. Export Data from AWS

```bash
# Export sources from DynamoDB
python -m mcp_tool_crawler.migration.export_sources

# Export tool catalog from S3
python -m mcp_tool_crawler.migration.export_catalog
```

This will create JSON files in the `./data/migration` directory.

### 2. Import Data to Local Storage

```bash
# Import sources to SQLite
python -m mcp_tool_crawler.migration.import_sources

# Import tool catalog to local storage
python -m mcp_tool_crawler.migration.import_catalog
```

## Running the Crawler

The crawler can now be run locally without AWS services:

```bash
# List all sources
python -m mcp_tool_crawler.cli list

# Add a new source
python -m mcp_tool_crawler.cli add "https://github.com/example/awesome-mcp-tools" --name "Example Tools"

# Crawl a specific source
python -m mcp_tool_crawler.cli crawl --id "source-123456"

# Crawl all sources
python -m mcp_tool_crawler.cli crawl --all
```

## SQLite Database Schema

The SQLite database includes the following tables:

### Sources Table

Stores information about sources to crawl.

```sql
CREATE TABLE sources (
    id TEXT PRIMARY KEY,
    url TEXT NOT NULL,
    name TEXT NOT NULL,
    type TEXT NOT NULL,
    has_known_crawler BOOLEAN NOT NULL DEFAULT 0,
    last_crawled TEXT,
    last_crawl_status TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
```

### Crawlers Table

Stores crawler strategies for different sources.

```sql
CREATE TABLE crawlers (
    id TEXT PRIMARY KEY,
    source_id TEXT NOT NULL,
    strategy_type TEXT NOT NULL,
    strategy_code TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (source_id) REFERENCES sources (id)
);
```

### Crawl Results Table

Stores results from crawler runs.

```sql
CREATE TABLE crawl_results (
    id TEXT PRIMARY KEY,
    source_id TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    status TEXT NOT NULL,
    tools_found INTEGER NOT NULL DEFAULT 0,
    error_message TEXT,
    FOREIGN KEY (source_id) REFERENCES sources (id)
);
```

## File Storage Structure

Local files are organized in the following directory structure:

```
data/
├── mcp_crawler.db       # SQLite database
├── sources.yaml         # Source list (equivalent to S3 sources.yaml)
├── tools.json           # Tool catalog (equivalent to S3 tools.json)
└── migration/           # Migration data (if applicable)
    ├── sources.json     # Exported sources from DynamoDB
    └── tools.json       # Exported tools from S3
```

## Troubleshooting

### Database Issues

If you encounter database issues:

1. Check that SQLite is properly installed:
   ```bash
   python -c "import sqlite3; print(sqlite3.sqlite_version)"
   ```

2. Verify database permissions:
   ```bash
   ls -la ./data/mcp_crawler.db
   ```

3. Reset the database (caution: this will delete all data):
   ```bash
   rm ./data/mcp_crawler.db
   python -m mcp_tool_crawler.cli init
   ```

### File Storage Issues

If you encounter file storage issues:

1. Check directory permissions:
   ```bash
   ls -la ./data
   ```

2. Ensure the data directory exists:
   ```bash
   mkdir -p ./data
   ```

## Differences from AWS Version

### Performance Considerations

- **Concurrency**: The local version doesn't have the same parallel processing capabilities as AWS Lambda and Step Functions. For large crawls, processing may take longer.
- **Storage Limits**: SQLite has different performance characteristics than DynamoDB, especially for very large datasets.

### Feature Differences

- **Event-Driven Processing**: The AWS version used S3 events to trigger the crawler. The local version requires manual triggering or scheduling.
- **Monitoring**: AWS CloudWatch monitoring is not available in the local version.

## Additional Resources

- [SQLite Documentation](https://www.sqlite.org/docs.html)
- [Python SQLite3 Documentation](https://docs.python.org/3/library/sqlite3.html)

