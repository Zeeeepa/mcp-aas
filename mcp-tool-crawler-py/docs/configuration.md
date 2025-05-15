# MCP Tool Crawler Configuration

This document describes the configuration options for the MCP Tool Crawler after the removal of AWS dependencies.

## Environment Variables

The following environment variables can be set to configure the MCP Tool Crawler:

### Storage Configuration

| Variable | Description | Default Value |
|----------|-------------|---------------|
| `DATA_DIR` | Directory where data files are stored | `./data` |
| `SQLITE_DB_PATH` | Path to the SQLite database file | `./data/mcp_tools.db` |
| `TOOLS_FILE_PATH` | Path to the JSON file for tools (used as fallback) | `./data/tools.json` |
| `SOURCES_FILE_PATH` | Path to the YAML file for sources | `./data/sources.yaml` |
| `USE_SQLITE` | Whether to use SQLite storage (true) or simple file storage (false) | `true` |

### OpenAI Configuration

| Variable | Description | Default Value |
|----------|-------------|---------------|
| `OPENAI_API_KEY` | OpenAI API key | `''` |
| `OPENAI_MODEL` | OpenAI model to use | `gpt-4` |

### Crawler Settings

| Variable | Description | Default Value |
|----------|-------------|---------------|
| `CRAWLER_TIMEOUT` | Crawler timeout in milliseconds | `30000` |
| `CRAWLER_USER_AGENT` | User agent string for the crawler | `MCP-Tool-Crawler/1.0` |
| `CRAWLER_CONCURRENCY_LIMIT` | Maximum number of concurrent crawls | `5` |

### GitHub API

| Variable | Description | Default Value |
|----------|-------------|---------------|
| `GITHUB_TOKEN` | GitHub API token | `''` |

### Logging

| Variable | Description | Default Value |
|----------|-------------|---------------|
| `LOG_LEVEL` | Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL) | `INFO` |
| `LOG_FILE_PATH` | Path to the log file | `./logs/mcp_tool_crawler.log` |

## Configuration File

You can also create a `.env` file in the root directory of the project to set these environment variables. For example:

```
DATA_DIR=./my_data
SQLITE_DB_PATH=./my_data/my_database.db
OPENAI_API_KEY=your-openai-api-key
GITHUB_TOKEN=your-github-token
LOG_LEVEL=DEBUG
```

## Storage Options

The MCP Tool Crawler now supports two storage options:

1. **SQLite Storage** (default): Uses a SQLite database to store tools and sources. This is the recommended option for most use cases.

2. **Local File Storage**: Uses JSON and YAML files to store tools and sources. This is a simpler option that doesn't require a database.

You can switch between these options by setting the `USE_SQLITE` environment variable to `true` or `false`.

## Directory Structure

The default directory structure for data files is:

```
data/
  ├── mcp_tools.db     # SQLite database
  ├── tools.json       # Tools JSON file (fallback)
  └── sources.yaml     # Sources YAML file
logs/
  └── mcp_tool_crawler.log  # Log file
```

You can customize these paths using the environment variables described above.

