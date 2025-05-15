# Storage Module

This module provides storage services for MCP tools and sources.

## Overview

The storage module includes two main classes:

1. `LocalStorage`: For storing and retrieving MCP tools in JSON format
2. `LocalSourceStorage`: For storing and retrieving sources in YAML format

Both classes provide file locking for concurrent access, versioned backups, and automatic recovery from corrupted files.

## Features

- **File Locking**: Uses `fcntl` to provide exclusive locks for writing and shared locks for reading
- **Versioned Backups**: Creates timestamped backups before overwriting files
- **Atomic File Operations**: Uses temporary files and atomic replacements to prevent data corruption
- **Error Recovery**: Automatically recovers from corrupted files by using the most recent backup
- **Consistent Interface**: Provides the same interface as the previous S3-based storage

## Usage

```python
from src.storage import get_storage, get_source_storage

# Get storage instances
tool_storage = get_storage()
source_storage = get_source_storage()

# Save tools
tools = [...]  # List of MCPTool objects
await tool_storage.save_tools(tools)

# Load tools
loaded_tools = await tool_storage.load_tools()

# Load sources
sources = await source_storage.load_sources()

# Save sources
await source_storage.save_sources(sources)
```

## File Structure

- Tools are stored in JSON format at `data/tools.json`
- Sources are stored in YAML format at `data/sources.yaml` (or as configured)
- Backups are stored in:
  - `data/backups/tools/tools_<timestamp>.json`
  - `data/backups/sources/sources_<timestamp>.yaml`

