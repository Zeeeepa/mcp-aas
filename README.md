# MCP-aaS Local

This is a simplified, locally hostable version of the MCP-aaS application. It has been consolidated to remove authentication, AWS services, and other cloud dependencies.

## Project Structure

- `frontend/`: React frontend application
  - Simple UI for managing MCP tools
  - No authentication required
  - Local development server

## Getting Started

### Frontend

1. Navigate to the frontend directory:

```bash
cd frontend
```

2. Install dependencies:

```bash
npm install
```

3. Start the development server:

```bash
npm run dev
```

This will start both the React application and the local API server.

4. Open [http://localhost:3000](http://localhost:3000) to view the application in your browser.

## Features

- Simple, locally hostable application
- No authentication required
- No AWS or cloud dependencies
- Basic MCP tool management

