#!/bin/bash

# Run end-to-end tests for the MCP Tool Crawler

# Set up environment
export DATA_DIR="$(pwd)/data/test"
export SQLITE_DB_FILE="test_crawler.db"

# Create test data directory
mkdir -p "$DATA_DIR/crawlers"

# Run tests
echo "Running end-to-end tests..."
cd "$(dirname "$0")/.."
python -m pytest tests/integration/test_end_to_end.py -v

# Clean up
echo "Cleaning up..."
rm -rf "$DATA_DIR"

echo "Done!"

