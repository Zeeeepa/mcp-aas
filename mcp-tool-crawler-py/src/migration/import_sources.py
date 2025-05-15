"""
Import sources from a local JSON file to SQLite.
"""

import json
import os
import asyncio
from pathlib import Path
from typing import List, Dict, Any

from ..models import Source, SourceType
from ..storage.sqlite_storage import SQLiteSourceStorage
from ..utils.logging import get_logger
from ..utils.config import get_config

logger = get_logger(__name__)
config = get_config()

async def import_sources() -> bool:
    """
    Import sources from a local JSON file to SQLite.
    
    Returns:
        True if successful, False otherwise.
    """
    try:
        # Create SQLite source storage
        source_storage = SQLiteSourceStorage()
        
        # Check if migration file exists
        migration_file = Path(config['local_storage']['path']) / 'migration' / 'sources.json'
        if not migration_file.exists():
            logger.warning(f"No sources migration file found at {migration_file}")
            return False
        
        # Read file
        with open(migration_file, 'r', encoding='utf-8') as f:
            items = json.load(f)
        
        # Convert to Source objects and save to SQLite
        for item in items:
            source = Source(
                id=item.get('id'),
                url=item.get('url'),
                name=item.get('name'),
                type=SourceType(item.get('type')),
                has_known_crawler=item.get('has_known_crawler', False),
                last_crawled=item.get('last_crawled'),
                last_crawl_status=item.get('last_crawl_status')
            )
            
            await source_storage.save_source(source)
        
        logger.info(f"Imported {len(items)} sources to SQLite")
        return True
    except Exception as e:
        logger.error(f"Error importing sources: {str(e)}")
        return False

async def main():
    """Main entry point for the script."""
    success = await import_sources()
    if success:
        print("Sources imported successfully.")
    else:
        print("Failed to import sources.")

if __name__ == "__main__":
    asyncio.run(main())

