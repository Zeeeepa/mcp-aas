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

# Local Storage Configuration
DATA_DIR = os.getenv('DATA_DIR', str(Path(__file__).parents[3] / 'data'))
TOOLS_FILE = os.getenv('TOOLS_FILE', 'tools.json')
SOURCES_FILE = os.getenv('SOURCES_FILE', 'sources.yaml')
SQLITE_DB_FILE = os.getenv('SQLITE_DB_FILE', 'mcp_crawler.db')

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
        "local": {
            "data_dir": DATA_DIR,
            "tools_file": os.path.join(DATA_DIR, TOOLS_FILE),
            "source_list_path": os.path.join(DATA_DIR, SOURCES_FILE),
            "sqlite_db_file": os.path.join(DATA_DIR, SQLITE_DB_FILE),
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
        },
    }

