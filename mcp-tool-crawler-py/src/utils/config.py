"""
Configuration module for the MCP Tool Crawler.
Loads environment variables and sets default values.
"""

import os
from pathlib import Path
from typing import Dict, List, Optional, Any

from dotenv import load_dotenv

# Load .env file if it exists
dotenv_path = Path(__file__).parents[2] / '.env'
if dotenv_path.exists():
    load_dotenv(dotenv_path)

# Data storage paths
DATA_DIR = os.getenv('DATA_DIR', str(Path(__file__).parents[3] / 'data'))
SQLITE_DB_PATH = os.getenv('SQLITE_DB_PATH', str(Path(DATA_DIR) / 'mcp_tools.db'))
TOOLS_FILE_PATH = os.getenv('TOOLS_FILE_PATH', str(Path(DATA_DIR) / 'tools.json'))
SOURCES_FILE_PATH = os.getenv('SOURCES_FILE_PATH', str(Path(DATA_DIR) / 'sources.yaml'))

# OpenAI Configuration
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '')
OPENAI_MODEL = os.getenv('OPENAI_MODEL', 'gpt-4')

# Crawler Settings
CRAWLER_TIMEOUT = int(os.getenv('CRAWLER_TIMEOUT', '30000'))
CRAWLER_USER_AGENT = os.getenv('CRAWLER_USER_AGENT', 'MCP-Tool-Crawler/1.0')
CRAWLER_CONCURRENCY_LIMIT = int(os.getenv('CRAWLER_CONCURRENCY_LIMIT', '5'))

# GitHub API
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN', '')

# Logging
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
LOG_FILE_PATH = os.getenv('LOG_FILE_PATH', str(Path(__file__).parents[3] / 'logs' / 'mcp_tool_crawler.log'))

# Pre-defined sources
PREDEFINED_SOURCES = {
    "awesome_lists": [
        "https://github.com/jpmcb/awesome-machine-context-protocol",
        "https://github.com/continuedev/awesome-continue",
        "https://github.com/wong2/awesome-mcp-servers",
    ],
    "websites": [
        {
            "url": "https://mcp-api.org/tools",
            "name": "MCP API.org Tools Directory"
        },
    ]
}

def get_config() -> Dict[str, Any]:
    """Return the configuration as a dictionary."""
    return {
        "storage": {
            "sqlite": {
                "db_path": SQLITE_DB_PATH,
            },
            "local": {
                "tools_file_path": TOOLS_FILE_PATH,
                "sources_file_path": SOURCES_FILE_PATH,
                "data_dir": DATA_DIR,
            },
        },
        "openai": {
            "api_key": OPENAI_API_KEY,
            "model": OPENAI_MODEL,
        },
        "crawler": {
            "timeout": CRAWLER_TIMEOUT,
            "user_agent": CRAWLER_USER_AGENT,
            "concurrency_limit": CRAWLER_CONCURRENCY_LIMIT,
        },
        "github": {
            "token": GITHUB_TOKEN,
        },
        "sources": PREDEFINED_SOURCES,
        "logging": {
            "level": LOG_LEVEL,
            "file_path": LOG_FILE_PATH,
        },
    }
"""

