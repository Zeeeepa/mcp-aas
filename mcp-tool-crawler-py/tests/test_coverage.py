"""
Test coverage measurement and reporting.
"""
import os
import sys
import pytest
import coverage
import subprocess
from pathlib import Path


def test_coverage():
    """
    Run tests with coverage and generate a report.
    
    This test is meant to be run manually to generate a coverage report.
    It will not be run as part of the normal test suite.
    
    Usage:
        pytest -xvs tests/test_coverage.py
    """
    # Skip this test when running the normal test suite
    if os.environ.get('SKIP_COVERAGE_TEST', 'true').lower() == 'true':
        pytest.skip("Skipping coverage test in normal test run")
    
    # Create a coverage object
    cov = coverage.Coverage(
        source=['src'],
        omit=[
            '*/tests/*',
            '*/venv/*',
            '*/site-packages/*',
            '*/__pycache__/*',
            '*/__init__.py',
        ]
    )
    
    # Start coverage measurement
    cov.start()
    
    try:
        # Run the tests
        result = pytest.main(['-xvs', 'tests', '--ignore=tests/test_coverage.py'])
        
        # Check that the tests passed
        assert result == 0, "Tests failed"
    finally:
        # Stop coverage measurement
        cov.stop()
        
        # Save coverage data
        cov.save()
        
        # Generate reports
        cov.report()
        cov.html_report(directory='coverage_html')
        
        print("\nCoverage report generated in coverage_html/index.html")


if __name__ == '__main__':
    # Run the coverage test directly
    os.environ['SKIP_COVERAGE_TEST'] = 'false'
    test_coverage()

