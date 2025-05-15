"""
Export sources from DynamoDB to a local JSON file.
"""

import json
import os
import asyncio
from pathlib import Path
from typing import List, Dict, Any

import boto3
from boto3.dynamodb.conditions import Key, Attr

from ..utils.logging import get_logger
from ..utils.config import get_config

logger = get_logger(__name__)
config = get_config()

async def export_sources() -> bool:
    """
    Export sources from DynamoDB to a local JSON file.
    
    Returns:
        True if successful, False otherwise.
    """
    try:
        # Initialize DynamoDB client
        dynamodb = boto3.resource('dynamodb', region_name=config['aws']['region'])
        table_name = config['aws']['dynamodb_tables']['sources']
        table = dynamodb.Table(table_name)
        
        # Scan the table
        response = table.scan()
        items = response.get('Items', [])
        
        # Continue scanning if we have more items
        while 'LastEvaluatedKey' in response:
            response = table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
            items.extend(response.get('Items', []))
        
        # Create migration directory if it doesn't exist
        migration_dir = Path(config['local_storage']['path']) / 'migration'
        migration_dir.mkdir(parents=True, exist_ok=True)
        
        # Write to file
        output_file = migration_dir / 'sources.json'
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(items, f, indent=2)
        
        logger.info(f"Exported {len(items)} sources to {output_file}")
        return True
    except Exception as e:
        logger.error(f"Error exporting sources: {str(e)}")
        return False

async def main():
    """Main entry point for the script."""
    success = await export_sources()
    if success:
        print("Sources exported successfully.")
    else:
        print("Failed to export sources.")

if __name__ == "__main__":
    asyncio.run(main())

