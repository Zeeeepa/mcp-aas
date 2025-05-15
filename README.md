# MCP as a Service (MCP-aaS)

A platform that allows users to launch and use Model Context Protocol (MCP) tools without installing them locally.

## Project Overview

MCP-aaS is a platform that provides:
- On-demand access to MCP tools
- User authentication and tool management
- WebSocket connections to tools
- Simple interface for discovering and launching tools

## Repository Structure

This monorepo contains:
- `frontend/`: React-based frontend code
- `backend/`: Node.js/Express backend services
- `infrastructure/`: Infrastructure deployment code
- `shared/`: Shared libraries and utilities
- `mcp-tool-crawler-py/`: Python-based tool for discovering and cataloging MCP tools

## Key Features

### Authentication System

The platform uses authentication for:
- User registration with email verification
- Secure login with JWT tokens
- Password reset functionality
- User profile management

Authentication is implemented using:
- JWT tokens
- Secure password hashing
- User profile management in SQLite database

## Development

### Prerequisites
- Node.js 18+
- Docker
- Python 3.8+ (for MCP Tool Crawler)
- SQLite 3.x (included with Python)

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

# Install MCP Tool Crawler dependencies
cd mcp-tool-crawler-py && pip install -e .
```

### Configuration
Create environment variables for both frontend and backend:

**Frontend (.env)**
```
REACT_APP_API_URL=http://localhost:4000
REACT_APP_WS_URL=ws://localhost:4000
```

**Backend (.env)**
```
PORT=4000
JWT_SECRET=your-jwt-secret
SQLITE_DB_PATH=./data/mcp_aas.db
```

**MCP Tool Crawler (.env)**
```
STORAGE_TYPE=sqlite
SQLITE_DB_PATH=./data/mcp_crawler.db
LOCAL_STORAGE_PATH=./data
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
See the documentation in the `deployment/` directory for detailed deployment instructions.

The application can be deployed using:
- Docker containers
- Manual deployment to a server
- GitHub Actions for CI/CD

## Migration from AWS
If you're migrating from the AWS-based version to the local storage version, please see the [Migration Guide](MIGRATION_GUIDE.md) for detailed instructions.

## Contributing
Please see the [CONTRIBUTING.md](CONTRIBUTING.md) file for guidelines.

## License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
