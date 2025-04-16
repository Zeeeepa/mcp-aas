# MCP as a Service (Development Mode)

A simplified development version of MCP as a Service without AWS dependencies.

## Setup

1. Install dependencies:
```bash
npm install
```

2. Start the development environment:
```bash
docker-compose up
```

The server will be available at http://localhost:3000.

## Development

- The application uses MongoDB for data storage
- Hot reloading is enabled for development
- No authentication required in development mode

## Environment Variables

Create a `.env` file with:
```
PORT=3000
MONGODB_URI=mongodb://localhost:27017/mcp
NODE_ENV=development
```
