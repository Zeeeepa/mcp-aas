import React, { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Tool, ToolConfig } from '../../types/tool';
import { toolService } from '../../services/ToolService';

const Dashboard: React.FC = () => {
  const [tools, setTools] = useState<Tool[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const navigate = useNavigate();

  useEffect(() => {
    fetchTools();
  }, []);

  const fetchTools = async () => {
    try {
      setLoading(true);
      const discoveredTools = await toolService.discoverTools();
      setTools(discoveredTools);
    } catch (err) {
      console.error('Error fetching tools:', err);
      setError('Failed to load tools. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleLaunchTool = async (toolId: string) => {
    try {
      await toolService.launchTool({ toolId });
      // Refresh tool status after launch
      const updatedTool = await toolService.getToolStatus(toolId);
      setTools(tools.map(tool => 
        tool.id === toolId ? updatedTool : tool
      ));
    } catch (error) {
      console.error('Error launching tool:', error);
      setError(`Failed to launch tool ${toolId}. Please try again.`);
    }
  };

  const handleConfigureTool = async (toolId: string) => {
    try {
      const config = await toolService.getToolConfig(toolId);
      navigate(`/tools/${toolId}/config`, { state: { config } });
    } catch (error) {
      console.error('Error getting tool config:', error);
      setError(`Failed to get configuration for tool ${toolId}`);
    }
  };

  const getStatusColor = (status: Tool['status']) => {
    switch (status) {
      case 'active':
        return '#4CAF50';
      case 'inactive':
        return '#9E9E9E';
      case 'error':
        return '#F44336';
      case 'configuring':
        return '#2196F3';
      default:
        return '#9E9E9E';
    }
  };

  return (
    <div className="container">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h1>MCP Tools Dashboard</h1>
      </div>

      {loading ? (
        <div style={{ textAlign: 'center', marginTop: '40px' }}>
          <p>Loading tools...</p>
        </div>
      ) : error ? (
        <div style={{ backgroundColor: '#FFEBEE', padding: '20px', marginTop: '20px', borderRadius: '4px', color: '#D32F2F' }}>
          {error}
        </div>
      ) : (
        <div style={{ marginTop: '20px' }}>
          <h2>Available Tools</h2>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: '20px', marginTop: '20px' }}>
            {tools.map(tool => (
              <div key={tool.id} className="card" style={{ padding: '20px', border: '1px solid #ddd', borderRadius: '8px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <h3>{tool.name}</h3>
                  <span style={{ 
                    width: '12px', 
                    height: '12px', 
                    borderRadius: '50%', 
                    backgroundColor: getStatusColor(tool.status),
                    display: 'inline-block'
                  }} />
                </div>
                
                <p>{tool.description}</p>
                <p style={{ fontSize: '0.9rem', color: '#666' }}>Version: {tool.version}</p>
                
                <div style={{ marginTop: '10px' }}>
                  <h4>Capabilities:</h4>
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px', marginTop: '8px' }}>
                    {tool.capabilities.map(capability => (
                      <span key={capability} style={{
                        padding: '4px 8px',
                        backgroundColor: '#E3F2FD',
                        borderRadius: '4px',
                        fontSize: '0.8rem'
                      }}>
                        {capability.replace('_', ' ')}
                      </span>
                    ))}
                  </div>
                </div>

                <div style={{ marginTop: '20px', display: 'flex', justifyContent: 'space-between' }}>
                  <button 
                    onClick={() => handleLaunchTool(tool.id)}
                    disabled={tool.status === 'error' || tool.status === 'configuring'}
                    style={{
                      padding: '8px 16px',
                      backgroundColor: tool.status === 'active' ? '#4CAF50' : '#9E9E9E',
                      color: 'white',
                      border: 'none',
                      borderRadius: '4px',
                      cursor: tool.status === 'active' ? 'pointer' : 'not-allowed'
                    }}
                  >
                    Launch
                  </button>

                  <button 
                    onClick={() => handleConfigureTool(tool.id)}
                    style={{
                      padding: '8px 16px',
                      backgroundColor: 'transparent',
                      color: '#2196F3',
                      border: '1px solid #2196F3',
                      borderRadius: '4px',
                      cursor: 'pointer'
                    }}
                  >
                    Configure
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default Dashboard;
