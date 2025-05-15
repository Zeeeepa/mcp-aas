# MCP Tool Crawler

A Python-based service for discovering, crawling, and cataloging Machine Context Protocol (MCP) tools from various sources. The crawler leverages AWS Step Functions and AI-powered code generation to automatically extract MCP tools from diverse sources.

## Storage Options

The MCP Tool Crawler supports multiple storage backends:

1. **SQLite Storage** (default): Local SQLite database for storing tools, sources, and crawler data
2. **Local Storage**: Simple JSON file-based storage for tools
3. **S3 Storage**: AWS S3-based storage for production environments

See [SQLite Storage Documentation](SQLITE_STORAGE.md) for details on the SQLite implementation.

## Source List Management

Sources to crawl are managed in a YAML file (`sample-sources.yaml`) which is uploaded to S3 when changes are pushed to GitHub.

### YAML Format

The source list YAML has the following format:

```yaml
sources:
  - url: https://github.com/user/awesome-repo
    name: Awesome Repository
    type: github_awesome_list
  - url: https://example.com/tools
    name: Example Tools
    type: website
```

Fields:
- `url`: The URL of the source to crawl (required)
- `name`: A friendly name for the source (optional, will be auto-generated if not provided)
- `type`: The source type (optional, will be auto-detected if not provided):
  - `github_awesome_list`: GitHub awesome list
  - `github_repository`: GitHub repository
  - `website`: Generic website
  - `rss_feed`: RSS feed
  - `manually_added`: Manually added source

### Workflow

1. Edit the `sample-sources.yaml` file with the sources you want to crawl
2. Commit and push the changes to the `main` branch
3. GitHub Actions workflow will upload the file to S3
4. S3 event will trigger the Step Function
5. Step Function will process the sources and discover tools

## GitHub Actions Setup

To enable the GitHub Actions workflow for uploading the source list:

1. Add the following secrets to your GitHub repository:
   - `AWS_ACCESS_KEY_ID`: AWS access key ID
   - `AWS_SECRET_ACCESS_KEY`: AWS secret access key
   - `S3_BUCKET_NAME`: Name of the S3 bucket to store the source list

## AsyncAPI Specification

The Step Function execution can be triggered via S3 events. Below is an AsyncAPI specification describing this event-driven API:

```yaml
asyncapi: 2.6.0
info:
  title: MCP Tool Crawler API
  version: 1.0.0
  description: Async API for the MCP Tool Crawler service

channels:
  s3/sourceListUpdated:
    publish:
      summary: Event published when a source list is updated in S3
      operationId: sourceListUpdated
      message:
        $ref: '#/components/messages/SourceListUpdated'
  
  stepFunctions/workflowCompleted:
    subscribe:
      summary: Event published when a crawler workflow is completed
      operationId: workflowCompleted
      message:
        $ref: '#/components/messages/WorkflowCompleted'

components:
  messages:
    SourceListUpdated:
      name: sourceListUpdated
      title: Source List Updated
      summary: Indicates that a source list was updated in S3
      contentType: application/json
      payload:
        type: object
        properties:
          s3BucketName:
            type: string
            description: Name of the S3 bucket containing the updated source list
          s3SourceListKey:
            type: string
            description: Key of the source list file in S3
          timestamp:
            type: string
            format: date-time
            description: Time when the update occurred
    
    WorkflowCompleted:
      name: workflowCompleted
      title: Workflow Completed
      summary: Sent when a step function workflow completes
      contentType: application/json
      payload:
        type: object
        properties:
          executionArn:
            type: string
            description: ARN of the Step Function execution
          status:
            type: string
            enum: [SUCCEEDED, FAILED, TIMED_OUT, ABORTED]
            description: Status of the execution
          startDate:
            type: string
            format: date-time
            description: Start time of the execution
          stopDate:
            type: string
            format: date-time
            description: End time of the execution
          input:
            type: object
            description: Input provided to the Step Function
          output:
            type: object
            description: Output from the Step Function
```

## Project Overview

The MCP Tool Crawler aims to build a comprehensive catalog of Machine Context Protocol (MCP) tools by automatically discovering and extracting information from various sources including GitHub repositories, awesome lists, and websites.

Key features:
- Automated crawling of GitHub awesome lists and repositories
- AI-powered crawler generation for unknown websites
- Deduplication and standardization of tool information
- Persistent storage in S3 for accessibility
- Step Functions workflow for reliability and monitoring

## Architecture

The system uses a serverless architecture with the following components:

![MCP Tool Crawler Architecture](docs/images/architecture.png)

1. **AWS Step Functions**: Orchestrates the entire workflow
2. **Lambda Functions**: Executes each step of the workflow
3. **DynamoDB**: Stores sources, crawler strategies, and metadata
4. **S3**: Stores the consolidated tool catalog
5. **OpenAI**: Generates custom crawlers for unknown websites

### Detailed Component Diagram

```mermaid
flowchart TD
    SF[AWS Step Functions] --> SM & CL & CP
    SM[Source Management Lambda] --> DB[(DynamoDB\nSources & Crawlers)]
    CL[Crawler Lambda] --> OAI[OpenAI API]
    CP[Catalog Processing Lambda] --> S3[(S3\nTool Catalog)]
```

### Workflow Overview

The system follows a multi-step workflow managed by AWS Step Functions:

![MCP Tool Crawler Workflow](docs/images/workflow.png)

```mermaid
flowchart TD
    IS[Initialize Sources] --> GS[Get Sources To Crawl]
    GS --> MS[Map Sources To Process]
    MS --> CS[Check Crawler Strategy]
    CS --> KC[Known Crawler] & GC[Generate Crawler] & EC[Execute Crawler]
    KC --> EC
    GC --> EC
    EC --> RR[Record Result]
    
    subgraph Finalization
        PC[Process Catalog] --> N[Notification]
    end
    
    RR --> PC
    note[After all sources processed] -.- PC
```

### AI Crawler Generation Process

For websites without a predefined crawler:

1. The system analyzes the website structure using OpenAI
2. A custom Python crawler is dynamically generated 
3. The generated code is executed in a secure sandbox
4. Results are processed and added to the catalog

![AI Crawler Generation](docs/images/ai-crawler-generation.png)

```mermaid
flowchart LR
    FW[Fetch Website Content] --> GC[Generate Crawler with AI]
    GC --> VG[Validate Generated Code]
    VG --> ES[Execute in Sandbox]
    ES --> CF[Clean & Filter Data]
    CF --> EM[Extract MCP Tools]
    EM --> PR[Process Results] 
    PR --> SC[Save to Catalog]
    
    style GC fill:#f9f,stroke:#333,stroke-width:2px
    style ES fill:#bbf,stroke:#333,stroke-width:2px
```

## Components

### Sources & Crawlers

- **Sources**: Represent locations where MCP tools can be found (GitHub repos, websites, etc.)
- **Crawlers**: Components responsible for extracting tools from sources
- **Crawler Strategies**: AI-generated code to extract tools from specific websites

### Lambda Functions

| Function | Description |
|----------|-------------|
| Source Manager | Initializes and manages sources in DynamoDB |
| Crawler Generator | Uses OpenAI to generate custom crawlers |
| Known Crawler Runner | Runs built-in crawlers (GitHub, RSS, etc.) |
| Generated Crawler Runner | Safely executes AI-generated crawlers |
| Catalog Processor | Deduplicates and updates the master catalog |

### Crawler Types

1. **GitHub Awesome List Crawler**: Extracts tools from markdown-based awesome lists
2. **GitHub Repository Crawler**: Extracts information about MCP-related GitHub repos
3. **AI-Generated Crawler**: Dynamic crawlers for websites without a predefined crawler
4. **RSS Feed Crawler**: Extracts tools from RSS feeds (planned)

## Development

### Setting Up Development Environment

```bash
# Clone the repository
git clone https://github.com/your-org/mcp-tool-crawler.git
cd mcp-tool-crawler

# Using Poetry (recommended)
# Install Poetry if you don't have it
curl -sSL https://install.python-poetry.org | python3 -

# Install dependencies
poetry install

# Activate the virtual environment
poetry shell

# Alternative: Using pip with venv
# Create a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment variables
cp .env.example .env
# Edit .env file with your settings
```

### Running Locally

```bash
# With Poetry (recommended)
# Initialize sources
poetry run mcp-crawler init

# List all sources
poetry run mcp-crawler list

# Add a new source
poetry run mcp-crawler add "https://github.com/example/awesome-mcp-tools" --name "Example Tools"

# Crawl a specific source
poetry run mcp-crawler crawl --id "source-123456"

# Crawl all sources
poetry run mcp-crawler crawl --all

# Alternative: Using Python module directly
python -m src.cli init
python -m src.cli list
python -m src.cli add "https://github.com/example/awesome-mcp-tools" --name "Example Tools"
python -m src.cli crawl --all --concurrency 3
```

### Running Tests

```bash
# With Poetry (recommended)
# Run all tests
poetry run pytest

# Run specific test file
poetry run pytest tests/test_github_crawler.py

# Run with coverage
poetry run pytest --cov=src

# With venv/pip
pytest
pytest tests/test_github_crawler.py
pytest --cov=src
```

## Deployment

### Packaging Lambda Functions

```bash
# Package Lambda functions with Poetry
poetry run ./scripts/package_lambda.sh

# Traditional method
./scripts/package_lambda.sh
```

### Deploying with Terraform

```bash
# Initialize Terraform
cd infrastructure/terraform
terraform init

# Plan the deployment
terraform plan -var-file=environments/dev.tfvars

# Apply the deployment
terraform apply -var-file=environments/dev.tfvars
```

## Security Considerations

- **Sandboxing**: AI-generated code is executed in a restricted sandbox using RestrictedPython
- **Input Validation**: All user inputs and API responses are validated
- **IAM Best Practices**: Least privilege access for all AWS services
- **Rate Limiting**: API throttling for external dependencies
- **Logging & Monitoring**: Comprehensive logging and monitoring

## Future Enhancements

- **Advanced Deduplication**: ML-based similarity detection for tools
- **Web UI**: Management interface for sources and tools
- **Additional Sources**: Support for more types of sources
- **Enhanced Metadata**: Extract and normalize more tool metadata
- **CI/CD Pipeline**: Automated testing and deployment
