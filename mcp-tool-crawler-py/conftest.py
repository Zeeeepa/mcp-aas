"""
pytest configuration file
"""
import pytest

def pytest_collection_modifyitems(items):
    """Remove the imported node function from test collection."""
    for item in list(items):
        if item.name == 'test_crawler_code' and str(item.parent.module.__file__).endswith(('test_crawler_generator.py', 'test_langgraph_workflow.py')):
            items.remove(item)