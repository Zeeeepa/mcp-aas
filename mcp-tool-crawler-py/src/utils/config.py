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

# Storage Configuration
STORAGE_TYPE = os.getenv('STORAGE_TYPE', 'sqlite')  # 'sqlite' or 'aws'
SQLITE_DB_PATH = os.getenv('SQLITE_DB_PATH', './data/mcp_crawler.db')
LOCAL_STORAGE_PATH = os.getenv('LOCAL_STORAGE_PATH', './data')

# AWS Configuration (legacy)
AWS_REGION = os.getenv('AWS_REGION', 'us-west-2')
AWS_PROFILE = os.getenv('AWS_PROFILE', 'default')

# AWS Resources (legacy)
S3_BUCKET_NAME = os.getenv('S3_BUCKET_NAME', 'mcp-tool-catalog')
DYNAMODB_TOOLS_TABLE = os.getenv('DYNAMODB_TOOLS_TABLE', 'mcp-tools')
DYNAMODB_SOURCES_TABLE = os.getenv('DYNAMODB_SOURCES_TABLE', 'mcp-sources')
DYNAMODB_CRAWLERS_TABLE = os.getenv('DYNAMODB_CRAWLERS_TABLE', 'mcp-crawlers')
DYNAMODB_CRAWL_RESULTS_TABLE = os.getenv('DYNAMODB_CRAWL_RESULTS_TABLE', 'mcp-crawl-results')

# S3 Source List Configuration (legacy)
S3_SOURCE_LIST_KEY = os.getenv('S3_SOURCE_LIST_KEY', 'sources.yaml')

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
    config = {
        "storage_type": STORAGE_TYPE,
        "sqlite": {
            "db_path": SQLITE_DB_PATH,
        },
        "local_storage": {
            "path": LOCAL_STORAGE_PATH,
        },
        "aws": {
            "region": AWS_REGION,
            "profile": AWS_PROFILE,
            "dynamodb_tables": {
                "tools": DYNAMODB_TOOLS_TABLE,
                "sources": DYNAMODB_SOURCES_TABLE,
                "crawlers": DYNAMODB_CRAWLERS_TABLE,
                "crawl_results": DYNAMODB_CRAWL_RESULTS_TABLE,
            },
            "s3": {
                "bucket_name": S3_BUCKET_NAME,
                "tool_catalog_key": "tools.json",
                "source_list_key": S3_SOURCE_LIST_KEY,
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
        },
    }
    
    return config
