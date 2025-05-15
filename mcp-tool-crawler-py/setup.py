from setuptools import setup, find_packages

setup(
    name="mcp-tool-crawler",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "requests>=2.31.0",
        "beautifulsoup4>=4.12.2",
        "openai>=1.3.0",
        "python-dotenv>=1.0.0",
        "pydantic>=2.4.2",
        "RestrictedPython>=6.2",
        "pyyaml>=6.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.4.3",
            "pytest-mock>=3.12.0",
            "pytest-asyncio>=0.21.1",
            "coverage>=7.3.2",
            "pytest-cov>=4.1.0",
            "black>=23.10.1",
            "isort>=5.12.0",
            "mypy>=1.6.1",
            "flake8>=6.1.0",
        ],
        "aws": [
            "boto3>=1.29.0",
            "aws-lambda-powertools>=2.26.0",
        ],
    },
    python_requires=">=3.8",
)
