const express = require("express");
const cors = require("cors");
const WebSocket = require("ws");

const app = express();
const port = process.env.PORT || 3001;

app.use(cors());
app.use(express.json());

// Create WebSocket server
const wss = new WebSocket.Server({ noServer: true });

// WebSocket connection handling
wss.on("connection", (ws) => {
  console.log("New client connected");

  ws.on("message", (message) => {
    console.log("Received:", message.toString());
    // Echo the message back
    ws.send(`Server received: ${message}`);
  });

  ws.on("close", () => {
    console.log("Client disconnected");
  });
});

// HTTP endpoints
app.get("/api/status", (req, res) => {
  res.json({ status: "ok", connections: wss.clients.size });
});

const server = app.listen(port, () => {
  console.log(`Server running on port ${port}`);
});

// Attach WebSocket server to HTTP server
server.on("upgrade", (request, socket, head) => {
  wss.handleUpgrade(request, socket, head, (ws) => {
    wss.emit("connection", ws, request);
  });
});
