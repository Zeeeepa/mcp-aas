const express = require('express');
const cors = require('cors');
const http = require('http');
const WebSocket = require('ws');

const app = express();
const server = http.createServer(app);
const wss = new WebSocket.Server({ server });

// Enable CORS
app.use(cors());
app.use(express.json());

// Mock tools data
const tools = [
  {
    id: 'tool-1',
    name: 'MCP Code Assistant',
    description: 'AI-powered code assistant',
    category: 'developer',
    icon: 'code-icon.png',
    version: '1.0.0',
    status: 'active'
  },
  {
    id: 'tool-2',
    name: 'MCP Chat',
    description: 'AI chat interface',
    category: 'communication',
    icon: 'chat-icon.png',
    version: '1.0.0',
    status: 'active'
  },
  {
    id: 'tool-3',
    name: 'MCP Data Analyzer',
    description: 'Data analysis and visualization',
    category: 'analytics',
    icon: 'data-icon.png',
    version: '1.0.0',
    status: 'active'
  }
];

// API routes
app.get('/api/tools', (req, res) => {
  res.json(tools);
});

app.get('/api/tools/:id', (req, res) => {
  const tool = tools.find(t => t.id === req.params.id);
  if (tool) {
    res.json(tool);
  } else {
    res.status(404).json({ error: 'Tool not found' });
  }
});

app.post('/api/tools/:id/launch', (req, res) => {
  const tool = tools.find(t => t.id === req.params.id);
  if (tool) {
    res.json({
      success: true,
      data: {
        connectionUrl: `ws://localhost:3001/ws/${tool.id}`
      }
    });
  } else {
    res.status(404).json({ 
      success: false,
      error: {
        message: 'Tool not found',
        code: 'TOOL_NOT_FOUND'
      }
    });
  }
});

// WebSocket handling
wss.on('connection', (ws) => {
  console.log('Client connected');
  
  ws.on('message', (message) => {
    console.log('Received:', message);
    
    // Echo the message back
    ws.send(JSON.stringify({
      type: 'response',
      data: `Received: ${message}`
    }));
  });
  
  ws.on('close', () => {
    console.log('Client disconnected');
  });
});

// Start server
const PORT = process.env.PORT || 3001;
server.listen(PORT, () => {
  console.log(`Server running on port ${PORT}`);
});

