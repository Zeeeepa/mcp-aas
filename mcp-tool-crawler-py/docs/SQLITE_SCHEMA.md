# SQLite Database Schema

This document describes the SQLite database schema used by the MCP Tool Crawler for local storage.

## Overview

The MCP Tool Crawler uses SQLite as its primary database for storing:
- Sources to crawl
- Crawler strategies
- Crawl results
- Tool metadata

## Database Location

By default, the SQLite database is stored at:
```
./data/mcp_crawler.db
```

This location can be configured using the `SQLITE_DB_PATH` environment variable.

## Tables

### Sources

The `sources` table stores information about sources to crawl.

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

CREATE INDEX idx_sources_url ON sources(url);
CREATE INDEX idx_sources_type ON sources(type);
CREATE INDEX idx_sources_last_crawled ON sources(last_crawled);
```

#### Columns

| Column | Type | Description |
|--------|------|-------------|
| id | TEXT | Unique identifier for the source (UUID) |
| url | TEXT | URL of the source |
| name | TEXT | Human-readable name of the source |
| type | TEXT | Type of source (github_awesome_list, github_repository, website, rss_feed, manually_added) |
| has_known_crawler | BOOLEAN | Whether the source has a known crawler strategy |
| last_crawled | TEXT | ISO 8601 timestamp of the last crawl |
| last_crawl_status | TEXT | Status of the last crawl (success, failed) |
| created_at | TEXT | ISO 8601 timestamp of when the source was created |
| updated_at | TEXT | ISO 8601 timestamp of when the source was last updated |

### Crawlers

The `crawlers` table stores crawler strategies for different sources.

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

CREATE INDEX idx_crawlers_source_id ON crawlers(source_id);
```

#### Columns

| Column | Type | Description |
|--------|------|-------------|
| id | TEXT | Unique identifier for the crawler (UUID) |
| source_id | TEXT | ID of the source this crawler is for |
| strategy_type | TEXT | Type of crawler strategy (built_in, generated) |
| strategy_code | TEXT | Python code for the crawler strategy |
| created_at | TEXT | ISO 8601 timestamp of when the crawler was created |
| updated_at | TEXT | ISO 8601 timestamp of when the crawler was last updated |

### Crawl Results

The `crawl_results` table stores results from crawler runs.

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

CREATE INDEX idx_crawl_results_source_id ON crawl_results(source_id);
CREATE INDEX idx_crawl_results_timestamp ON crawl_results(timestamp);
```

#### Columns

| Column | Type | Description |
|--------|------|-------------|
| id | TEXT | Unique identifier for the crawl result (UUID) |
| source_id | TEXT | ID of the source that was crawled |
| timestamp | TEXT | ISO 8601 timestamp of when the crawl occurred |
| status | TEXT | Status of the crawl (success, failed) |
| tools_found | INTEGER | Number of tools found during the crawl |
| error_message | TEXT | Error message if the crawl failed |

### Tools

The `tools` table stores information about MCP tools discovered by the crawler.

```sql
CREATE TABLE tools (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    url TEXT NOT NULL,
    source_id TEXT NOT NULL,
    tool_type TEXT,
    github_stars INTEGER,
    last_updated TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (source_id) REFERENCES sources (id)
);

CREATE INDEX idx_tools_name ON tools(name);
CREATE INDEX idx_tools_url ON tools(url);
CREATE INDEX idx_tools_source_id ON tools(source_id);
CREATE INDEX idx_tools_tool_type ON tools(tool_type);
```

#### Columns

| Column | Type | Description |
|--------|------|-------------|
| id | TEXT | Unique identifier for the tool (UUID) |
| name | TEXT | Name of the tool |
| description | TEXT | Description of the tool |
| url | TEXT | URL of the tool |
| source_id | TEXT | ID of the source where the tool was found |
| tool_type | TEXT | Type of tool (library, application, service, etc.) |
| github_stars | INTEGER | Number of GitHub stars (if applicable) |
| last_updated | TEXT | ISO 8601 timestamp of when the tool was last updated |
| created_at | TEXT | ISO 8601 timestamp of when the tool was created in the database |
| updated_at | TEXT | ISO 8601 timestamp of when the tool was last updated in the database |

## Migrations

The database schema is managed using a simple migration system. Migration scripts are stored in the `src/storage/migrations` directory and are executed in order when the database is initialized.

### Creating a New Migration

To create a new migration, add a new SQL file to the `src/storage/migrations` directory with a name in the format `YYYYMMDD_description.sql`. For example:

```sql
-- 20230101_add_tags_table.sql
CREATE TABLE tags (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE tool_tags (
    tool_id TEXT NOT NULL,
    tag_id TEXT NOT NULL,
    PRIMARY KEY (tool_id, tag_id),
    FOREIGN KEY (tool_id) REFERENCES tools (id),
    FOREIGN KEY (tag_id) REFERENCES tags (id)
);
```

## Example Queries

### Get All Sources

```sql
SELECT * FROM sources ORDER BY name;
```

### Get Sources That Need Crawling

```sql
SELECT * FROM sources 
WHERE last_crawled IS NULL 
   OR datetime(last_crawled) < datetime('now', '-24 hours');
```

### Get Tools from a Specific Source

```sql
SELECT t.* FROM tools t
JOIN sources s ON t.source_id = s.id
WHERE s.url = 'https://github.com/example/awesome-mcp-tools';
```

### Get Recent Crawl Results

```sql
SELECT cr.*, s.name as source_name
FROM crawl_results cr
JOIN sources s ON cr.source_id = s.id
ORDER BY cr.timestamp DESC
LIMIT 10;
```

### Get Tools with the Most GitHub Stars

```sql
SELECT * FROM tools
WHERE github_stars IS NOT NULL
ORDER BY github_stars DESC
LIMIT 10;
```

