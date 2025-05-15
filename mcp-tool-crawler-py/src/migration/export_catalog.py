"""
Export tool catalog from S3 to a local JSON file.
"""

import json
import os
import asyncio
from pathlib import Path
from typing import List, Dict, Any

import boto3

from ..utils.logging import get_logger
from ..utils.config import get_config

logger = get_logger(__name__)
config = get_config()

async def export_catalog() -> bool:
    """
    Export tool catalog from S3 to a local JSON file.
    
    Returns:
        True if successful, False otherwise.
    """
    try:
        # Initialize S3 client
        s3_client = boto3.client('s3', region_name=config['aws']['region'])
        bucket_name = config['aws']['s3']['bucket_name']
        key = config['aws']['s3']['tool_catalog_key']
        
        # Check if object exists
        try:
            s3_client.head_object(
                Bucket=bucket_name,
                Key=key
            )
        except Exception:
            logger.warning(f"No tool catalog found in S3 bucket: {bucket_name}/{key}")
            return False
        
        # Get object from S3
        response = s3_client.get_object(
            Bucket=bucket_name,
            Key=key
        )
        
        # Parse JSON
        data = json.loads(response['Body'].read().decode('utf-8'))
        
        # Create migration directory if it doesn't exist
        migration_dir = Path(config['local_storage']['path']) / 'migration'
        migration_dir.mkdir(parents=True, exist_ok=True)
        
        # Write to file
        output_file = migration_dir / 'tools.json'
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        
        logger.info(f"Exported tool catalog to {output_file}")
        return True
    except Exception as e:
        logger.error(f"Error exporting tool catalog: {str(e)}")
        return False

async def main():
    """Main entry point for the script."""
    success = await export_catalog()
    if success:
        print("Tool catalog exported successfully.")
    else:
        print("Failed to export tool catalog.")

if __name__ == "__main__":
    asyncio.run(main())

