# MCP as a Service (MCP-aaS)

A platform that allows users to launch and use Model Context Protocol (MCP) tools without installing them locally.

## Project Overview

MCP-aaS is a cloud-based platform that provides:
- On-demand access to MCP tools
- User authentication and tool management
- WebSocket connections to tools
- Simple interface for discovering and launching tools

## Repository Structure

This monorepo contains:
- `frontend/`: React-based frontend code
- `backend/`: Node.js/Express backend services
- `infrastructure/`: AWS CDK code for infrastructure deployment
- `shared/`: Shared libraries and utilities
- `mcp-tool-crawler-py/`: Python tool for crawling and cataloging MCP tools

## Key Features

### Authentication System

The platform uses AWS Cognito for authentication:
- User registration with email verification
- Secure login with JWT tokens
- Password reset functionality
- User profile management

Authentication is implemented using:
- AWS Cognito User Pools and Identity Pools
- AWS Amplify on the frontend
- AWS SDK on the backend
- Serverless infrastructure managed with AWS CDK

## Development

### Prerequisites
- Node.js 18+
- Docker
- AWS CLI (for deployment)
- AWS CDK CLI (for infrastructure deployment)

### Setup
1. Clone the repository
2. Install dependencies
```bash
# Install root dependencies
npm install

# Install frontend dependencies
cd frontend && npm install

# Install backend dependencies
cd backend && npm install
```

### Configuration
Create environment variables for both frontend and backend:

**Frontend (.env)**
```
REACT_APP_COGNITO_REGION=us-east-1
REACT_APP_COGNITO_USER_POOL_ID=your-user-pool-id
REACT_APP_COGNITO_USER_POOL_WEB_CLIENT_ID=your-client-id
REACT_APP_COGNITO_IDENTITY_POOL_ID=your-identity-pool-id
```

**Backend (.env)**
```
PORT=4000
AWS_REGION=us-east-1
COGNITO_USER_POOL_ID=your-user-pool-id
COGNITO_CLIENT_ID=your-client-id
```

### Infrastructure Deployment
1. Navigate to the infrastructure/cdk directory
2. Install dependencies
```bash
npm install
```
3. Deploy the AWS resources
```bash
npx cdk deploy --all
```

### Running Locally
There are two ways to run the application locally:

#### Using npm scripts
```bash
# Start all services
npm start

# Start only the frontend
npm run start:frontend

# Start only the backend
npm run start:backend
```

#### Using Docker Compose
```bash
# Start all services
docker-compose up

# Start in detached mode
docker-compose up -d

# Stop services
docker-compose down
```

## Deployment
See the documentation in the `infrastructure/` directory for detailed deployment instructions.

The application is deployed using:
- GitHub Actions for CI/CD
- Docker containers
- AWS ECS (Elastic Container Service)
- AWS CDK for infrastructure as code

## Contributing
Please see the [CONTRIBUTING.md](CONTRIBUTING.md) file for guidelines.

## License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
