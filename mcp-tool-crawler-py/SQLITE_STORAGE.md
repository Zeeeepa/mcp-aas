# SQLite Storage Implementation

This document describes the SQLite storage implementation for the MCP Tool Crawler, which replaces the DynamoDB-based storage.

## Overview

The SQLite storage implementation provides a local database solution for storing MCP Tool Crawler data, eliminating the need for AWS DynamoDB. This makes the crawler more portable and easier to run in local environments without cloud dependencies.

## Database Schema

The SQLite database consists of the following tables:

### Sources Table

Stores information about sources of MCP tools.

```sql
CREATE TABLE sources (
    id TEXT PRIMARY KEY,
    url TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    type TEXT NOT NULL,
    has_known_crawler BOOLEAN NOT NULL,
    crawler_id TEXT,
    last_crawled TEXT,
    last_crawl_status TEXT,
    metadata TEXT
)
```

### Tools Table

Stores information about MCP tools discovered by the crawler.

```sql
CREATE TABLE tools (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT NOT NULL,
    url TEXT NOT NULL UNIQUE,
    source_url TEXT NOT NULL,
    first_discovered TEXT NOT NULL,
    last_updated TEXT NOT NULL,
    metadata TEXT
)
```

### Crawler Strategies Table

Stores crawler strategies for specific sources.

```sql
CREATE TABLE crawler_strategies (
    id TEXT PRIMARY KEY,
    source_id TEXT NOT NULL,
    source_type TEXT NOT NULL,
    implementation TEXT NOT NULL,
    description TEXT NOT NULL,
    created TEXT NOT NULL,
    last_modified TEXT NOT NULL,
    FOREIGN KEY (source_id) REFERENCES sources(id) ON DELETE CASCADE
)
```

### Crawl Results Table

Stores results of crawl operations.

```sql
CREATE TABLE crawl_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_id TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    success BOOLEAN NOT NULL,
    tools_discovered INTEGER NOT NULL,
    new_tools INTEGER NOT NULL,
    updated_tools INTEGER NOT NULL,
    duration INTEGER NOT NULL,
    error TEXT,
    FOREIGN KEY (source_id) REFERENCES sources(id) ON DELETE CASCADE
)
```

## Indexes

The following indexes are created to optimize common queries:

```sql
CREATE INDEX idx_sources_url ON sources(url)
CREATE INDEX idx_tools_url ON tools(url)
CREATE INDEX idx_tools_source_url ON tools(source_url)
CREATE INDEX idx_crawler_strategies_source_id ON crawler_strategies(source_id)
CREATE INDEX idx_crawl_results_source_id ON crawl_results(source_id)
CREATE INDEX idx_crawl_results_timestamp ON crawl_results(timestamp)
```

## Usage

### Configuration

The SQLite storage is configured through environment variables:

- `ENVIRONMENT`: Set to `development` (default) to use SQLite storage, or `production` to use S3 storage
- `STORAGE_TYPE`: Set to `sqlite` (default) to use SQLite storage, `local` to use local JSON storage, or `s3` to use S3 storage

### Default Database Location

By default, the SQLite database is stored at:

```
<project_root>/data/mcp_crawler.db
```

You can specify a custom location by passing the `db_path` parameter to the `SQLiteStorage` constructor.

### Migrating from DynamoDB

A migration script is provided to help migrate data from DynamoDB to SQLite:

```bash
python scripts/migrate_to_sqlite.py [--db-path DB_PATH]
```

This script will:
1. Connect to DynamoDB using your AWS credentials
2. Retrieve all data from the DynamoDB tables
3. Convert the data to the appropriate model objects
4. Save the data to the SQLite database

## Concurrency Handling

SQLite has limitations when it comes to concurrent write operations. The implementation uses the following strategies to handle concurrency:

1. **Thread-local connections**: Each thread gets its own SQLite connection to prevent conflicts
2. **Connection pooling**: Connections are reused within the same thread
3. **Transaction management**: All operations are wrapped in transactions to ensure data consistency

For high-concurrency scenarios, consider using a more robust database like PostgreSQL.

## Error Handling

The SQLite storage implementation includes comprehensive error handling:

1. **Connection errors**: Handled gracefully with appropriate logging
2. **Transaction rollback**: If an error occurs during a transaction, changes are rolled back
3. **Retry logic**: Not implemented by default, but can be added for specific operations

## Performance Considerations

SQLite is designed for moderate workloads and may not be suitable for high-volume production environments. Consider the following:

1. **Database size**: SQLite works well for databases up to a few GB in size
2. **Query complexity**: Complex queries may be slower than in dedicated database servers
3. **Write concurrency**: SQLite uses file-level locking, which can limit write concurrency

For larger deployments, consider using a client-server database like PostgreSQL or MySQL.

