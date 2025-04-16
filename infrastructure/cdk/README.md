# MCP-AAS Local Development with LocalStack

This guide will help you set up and run the MCP-AAS application locally without requiring an AWS account by using LocalStack.

## Prerequisites

- Docker and Docker Compose
- Node.js and npm
- Git

## Setup LocalStack

1. Run the LocalStack setup script:

```bash
cd infrastructure/cdk
chmod +x localstack-setup.sh
./localstack-setup.sh
```

This script will:
- Create a docker-compose file for LocalStack
- Create a .env.local file with mock AWS credentials
- Create a deploy-to-localstack.sh script

2. Start LocalStack:

```bash
docker-compose -f docker-compose.localstack.yml up -d
```

3. Deploy the CDK stacks to LocalStack:

```bash
chmod +x deploy-to-localstack.sh
./deploy-to-localstack.sh
```

## Running the Application Locally

Once you have LocalStack running and the CDK stacks deployed, you can run the application locally:

1. Start the backend and frontend:

```bash
docker-compose up -d
```

2. Access the application at http://localhost:3000

## Troubleshooting

If you encounter any issues:

1. Check if LocalStack is running:

```bash
docker ps | grep localstack
```

2. Check LocalStack logs:

```bash
docker logs localstack-mcp-aas
```

3. Verify the CDK deployment:

```bash
AWS_ENDPOINT_URL=http://localhost:4566 aws cloudformation list-stacks
```

## Notes

- This setup is for local development only and does not require an AWS account
- All AWS services are mocked by LocalStack
- The application will use a local MongoDB instance for data storage
