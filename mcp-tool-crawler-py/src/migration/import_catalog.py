"""
Import tool catalog from a local JSON file to SQLite.
"""

import json
import os
import asyncio
from pathlib import Path
from typing import List, Dict, Any

from ..models import MCPTool
from ..storage.sqlite_storage import SQLiteToolStorage
from ..utils.logging import get_logger
from ..utils.config import get_config

logger = get_logger(__name__)
config = get_config()

async def import_catalog() -> bool:
    """
    Import tool catalog from a local JSON file to SQLite.
    
    Returns:
        True if successful, False otherwise.
    """
    try:
        # Create SQLite tool storage
        tool_storage = SQLiteToolStorage()
        
        # Check if migration file exists
        migration_file = Path(config['local_storage']['path']) / 'migration' / 'tools.json'
        if not migration_file.exists():
            logger.warning(f"No tool catalog migration file found at {migration_file}")
            return False
        
        # Read file
        with open(migration_file, 'r', encoding='utf-8') as f:
            items = json.load(f)
        
        # Convert to MCPTool objects
        tools = [MCPTool(**item) for item in items]
        
        # Save to SQLite
        success = await tool_storage.save_tools(tools)
        
        if success:
            logger.info(f"Imported {len(tools)} tools to SQLite")
        
        return success
    except Exception as e:
        logger.error(f"Error importing tool catalog: {str(e)}")
        return False

async def main():
    """Main entry point for the script."""
    success = await import_catalog()
    if success:
        print("Tool catalog imported successfully.")
    else:
        print("Failed to import tool catalog.")

if __name__ == "__main__":
    asyncio.run(main())

