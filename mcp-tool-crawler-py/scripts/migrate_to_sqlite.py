#!/usr/bin/env python3
"""
Migration script to move data from DynamoDB to SQLite.

This script migrates all data from DynamoDB tables to a SQLite database.
It requires both AWS credentials and the SQLite database path.

Usage:
    python migrate_to_sqlite.py [--db-path DB_PATH]

Options:
    --db-path DB_PATH    Path to the SQLite database file. If not provided,
                         uses the default path.
"""

import argparse
import asyncio
import boto3
import os
import sys
from pathlib import Path

# Add the parent directory to the Python path
sys.path.append(str(Path(__file__).parent.parent))

from src.models import Source, MCPTool, CrawlerStrategy, CrawlResult
from src.storage.sqlite_storage import SQLiteStorage
from src.utils.logging import get_logger
from src.utils.config import get_config

logger = get_logger(__name__)
config = get_config()


async def migrate_sources(dynamodb, sqlite_storage):
    """
    Migrate sources from DynamoDB to SQLite.
    
    Args:
        dynamodb: DynamoDB resource.
        sqlite_storage: SQLiteStorage instance.
        
    Returns:
        Number of sources migrated.
    """
    table_name = config['aws']['dynamodb_tables']['sources']
    table = dynamodb.Table(table_name)
    
    logger.info(f"Migrating sources from DynamoDB table: {table_name}")
    
    # Scan the DynamoDB table
    response = table.scan()
    items = response.get('Items', [])
    
    # Get all items if there are more (pagination)
    while 'LastEvaluatedKey' in response:
        response = table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
        items.extend(response.get('Items', []))
    
    logger.info(f"Found {len(items)} sources in DynamoDB")
    
    # Convert items to Source objects and save to SQLite
    count = 0
    for item in items:
        try:
            source = Source(**item)
            success = await sqlite_storage.save_source(source)
            if success:
                count += 1
        except Exception as e:
            logger.error(f"Error migrating source: {str(e)}")
    
    logger.info(f"Migrated {count} sources to SQLite")
    return count


async def migrate_tools(dynamodb, sqlite_storage):
    """
    Migrate tools from DynamoDB to SQLite.
    
    Args:
        dynamodb: DynamoDB resource.
        sqlite_storage: SQLiteStorage instance.
        
    Returns:
        Number of tools migrated.
    """
    table_name = config['aws']['dynamodb_tables']['tools']
    table = dynamodb.Table(table_name)
    
    logger.info(f"Migrating tools from DynamoDB table: {table_name}")
    
    # Scan the DynamoDB table
    response = table.scan()
    items = response.get('Items', [])
    
    # Get all items if there are more (pagination)
    while 'LastEvaluatedKey' in response:
        response = table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
        items.extend(response.get('Items', []))
    
    logger.info(f"Found {len(items)} tools in DynamoDB")
    
    # Convert items to MCPTool objects
    tools = []
    for item in items:
        try:
            tool = MCPTool(**item)
            tools.append(tool)
        except Exception as e:
            logger.error(f"Error converting tool: {str(e)}")
    
    # Save tools to SQLite
    if tools:
        success = await sqlite_storage.save_tools(tools)
        if success:
            logger.info(f"Migrated {len(tools)} tools to SQLite")
            return len(tools)
    
    logger.info("No tools migrated")
    return 0


async def migrate_crawler_strategies(dynamodb, sqlite_storage):
    """
    Migrate crawler strategies from DynamoDB to SQLite.
    
    Args:
        dynamodb: DynamoDB resource.
        sqlite_storage: SQLiteStorage instance.
        
    Returns:
        Number of crawler strategies migrated.
    """
    table_name = config['aws']['dynamodb_tables']['crawlers']
    table = dynamodb.Table(table_name)
    
    logger.info(f"Migrating crawler strategies from DynamoDB table: {table_name}")
    
    # Scan the DynamoDB table
    response = table.scan()
    items = response.get('Items', [])
    
    # Get all items if there are more (pagination)
    while 'LastEvaluatedKey' in response:
        response = table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
        items.extend(response.get('Items', []))
    
    logger.info(f"Found {len(items)} crawler strategies in DynamoDB")
    
    # Convert items to CrawlerStrategy objects and save to SQLite
    count = 0
    for item in items:
        try:
            strategy = CrawlerStrategy(**item)
            success = await sqlite_storage.save_crawler_strategy(strategy)
            if success:
                count += 1
        except Exception as e:
            logger.error(f"Error migrating crawler strategy: {str(e)}")
    
    logger.info(f"Migrated {count} crawler strategies to SQLite")
    return count


async def migrate_crawl_results(dynamodb, sqlite_storage):
    """
    Migrate crawl results from DynamoDB to SQLite.
    
    Args:
        dynamodb: DynamoDB resource.
        sqlite_storage: SQLiteStorage instance.
        
    Returns:
        Number of crawl results migrated.
    """
    table_name = config['aws']['dynamodb_tables']['crawl_results']
    table = dynamodb.Table(table_name)
    
    logger.info(f"Migrating crawl results from DynamoDB table: {table_name}")
    
    # Scan the DynamoDB table
    response = table.scan()
    items = response.get('Items', [])
    
    # Get all items if there are more (pagination)
    while 'LastEvaluatedKey' in response:
        response = table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
        items.extend(response.get('Items', []))
    
    logger.info(f"Found {len(items)} crawl results in DynamoDB")
    
    # Convert items to CrawlResult objects and save to SQLite
    count = 0
    for item in items:
        try:
            result = CrawlResult(**item)
            success = await sqlite_storage.save_crawl_result(result)
            if success:
                count += 1
        except Exception as e:
            logger.error(f"Error migrating crawl result: {str(e)}")
    
    logger.info(f"Migrated {count} crawl results to SQLite")
    return count


async def main():
    """Main migration function."""
    parser = argparse.ArgumentParser(description="Migrate data from DynamoDB to SQLite")
    parser.add_argument("--db-path", help="Path to the SQLite database file")
    args = parser.parse_args()
    
    # Initialize SQLite storage
    sqlite_storage = SQLiteStorage(args.db_path)
    
    # Initialize DynamoDB resource
    dynamodb = boto3.resource('dynamodb', region_name=config['aws']['region'])
    
    logger.info("Starting migration from DynamoDB to SQLite")
    
    # Migrate data
    sources_count = await migrate_sources(dynamodb, sqlite_storage)
    tools_count = await migrate_tools(dynamodb, sqlite_storage)
    strategies_count = await migrate_crawler_strategies(dynamodb, sqlite_storage)
    results_count = await migrate_crawl_results(dynamodb, sqlite_storage)
    
    logger.info("Migration completed")
    logger.info(f"Migrated {sources_count} sources")
    logger.info(f"Migrated {tools_count} tools")
    logger.info(f"Migrated {strategies_count} crawler strategies")
    logger.info(f"Migrated {results_count} crawl results")


if __name__ == "__main__":
    asyncio.run(main())

