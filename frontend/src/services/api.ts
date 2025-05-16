import axios from 'axios';
import { config } from '../config/local';
import { Tool, ApiResponse } from '../types';

const api = axios.create({
  baseURL: config.apiUrl,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const getTools = async (): Promise<Tool[]> => {
  // For local development, return mock data
  return [
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
};

export const getTool = async (id: string): Promise<Tool | null> => {
  // For local development, return mock data
  const tools = await getTools();
  return tools.find(tool => tool.id === id) || null;
};

export const launchTool = async (id: string): Promise<ApiResponse<{ connectionUrl: string }>> => {
  // For local development, return mock data
  return {
    success: true,
    data: {
      connectionUrl: `${config.wsUrl}/${id}`
    }
  };
};

