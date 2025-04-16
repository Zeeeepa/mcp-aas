# MCP-AAS (Model Context Protocol as a Service)

A lightweight, local-first implementation of the Model Context Protocol (MCP) server.

## Features

- Real-time WebSocket communication
- Simple dashboard for monitoring
- MCP client interface
- Configurable settings
- No authentication required (dev mode)

## Getting Started

1. Install dependencies:
```bash
npm install
```

2. Start the development server:
```bash
npm start
```

This will start both the frontend (port 3000) and backend (port 3001) servers.

## Project Structure

- `frontend/`: React frontend application
  - `src/components/`: Reusable UI components
  - `src/pages/`: Main application pages
  - `src/services/`: API and WebSocket services
- `backend/`: Express.js backend server
  - `src/`: Server implementation
- `shared/`: Shared types and utilities

## Development

The application runs in development mode without authentication. All features are
accessible through the UI without any login requirements.

## Available Scripts

- `npm start`: Start both frontend and backend servers
- `npm run start:frontend`: Start only the frontend
- `npm run start:backend`: Start only the backend
