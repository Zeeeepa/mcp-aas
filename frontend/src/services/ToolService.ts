import { Tool, ToolConfig, ToolLaunchOptions } from '../types/tool';

class ToolService {
  private baseUrl = process.env.REACT_APP_API_URL || 'http://localhost:3001';

  async discoverTools(): Promise<Tool[]> {
    const response = await fetch(`${this.baseUrl}/api/tools/discover`);
    if (!response.ok) {
      throw new Error('Failed to discover tools');
    }
    return response.json();
  }

  async getToolConfig(toolId: string): Promise<ToolConfig> {
    const response = await fetch(`${this.baseUrl}/api/tools/${toolId}/config`);
    if (!response.ok) {
      throw new Error('Failed to get tool config');
    }
    return response.json();
  }

  async launchTool(options: ToolLaunchOptions): Promise<void> {
    const response = await fetch(`${this.baseUrl}/api/tools/${options.toolId}/launch`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(options),
    });
    if (!response.ok) {
      throw new Error('Failed to launch tool');
    }
  }

  async updateToolConfig(toolId: string, config: Partial<ToolConfig>): Promise<ToolConfig> {
    const response = await fetch(`${this.baseUrl}/api/tools/${toolId}/config`, {
      method: 'PATCH',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(config),
    });
    if (!response.ok) {
      throw new Error('Failed to update tool config');
    }
    return response.json();
  }

  async getToolStatus(toolId: string): Promise<Tool> {
    const response = await fetch(`${this.baseUrl}/api/tools/${toolId}/status`);
    if (!response.ok) {
      throw new Error('Failed to get tool status');
    }
    return response.json();
  }
}

export const toolService = new ToolService();
