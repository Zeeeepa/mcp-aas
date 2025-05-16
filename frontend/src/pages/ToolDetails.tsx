import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { Tool } from '../types';
import PageLayout from '../components/layout/PageLayout';

const ToolDetails: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const [tool, setTool] = useState<Tool | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    const fetchToolDetails = async () => {
      try {
        // Simulate API call
        await new Promise(resolve => setTimeout(resolve, 800));
        
        // Mock data based on ID
        const mockTools: Record<string, Tool> = {
          'tool-1': {
            id: 'tool-1',
            name: 'MCP Code Assistant',
            description: 'AI-powered code assistant that helps you write, review, and refactor code. Supports multiple programming languages and integrates with popular IDEs.',
            category: 'developer',
            icon: 'code-icon.png',
            version: '1.0.0',
            status: 'active'
          },
          'tool-2': {
            id: 'tool-2',
            name: 'MCP Chat',
            description: 'AI chat interface for natural language interactions. Supports context-aware conversations and can be customized for different domains.',
            category: 'communication',
            icon: 'chat-icon.png',
            version: '1.0.0',
            status: 'active'
          },
          'tool-3': {
            id: 'tool-3',
            name: 'MCP Data Analyzer',
            description: 'Data analysis and visualization tool that helps you understand complex datasets. Supports various data formats and provides interactive visualizations.',
            category: 'analytics',
            icon: 'data-icon.png',
            version: '1.0.0',
            status: 'active'
          }
        };
        
        if (id && mockTools[id]) {
          setTool(mockTools[id]);
        } else {
          setError('Tool not found');
        }
      } catch (err) {
        console.error('Error fetching tool details:', err);
        setError('Failed to load tool details. Please try again.');
      } finally {
        setLoading(false);
      }
    };
    
    fetchToolDetails();
  }, [id]);
  
  const handleLaunchTool = () => {
    if (tool) {
      console.log(`Launching tool: ${tool.id}`);
      window.alert(`Tool ${tool.name} launched! In a real app, this would connect to the tool.`);
    }
  };
  
  return (
    <PageLayout>
      <div className="container">
        <div style={{ marginBottom: '20px' }}>
          <Link to="/dashboard" style={{ textDecoration: 'none', color: 'var(--primary-color)' }}>
            &larr; Back to Dashboard
          </Link>
        </div>
        
        {loading ? (
          <div style={{ textAlign: 'center', marginTop: '40px' }}>
            <p>Loading tool details...</p>
          </div>
        ) : error ? (
          <div style={{ backgroundColor: '#ffebee', padding: '20px', marginTop: '20px', borderRadius: '4px', color: 'var(--error-color)' }}>
            {error}
          </div>
        ) : tool ? (
          <div>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
              <h1>{tool.name}</h1>
              <span style={{ 
                padding: '4px 8px', 
                borderRadius: '4px', 
                backgroundColor: tool.status === 'active' ? '#e8f5e9' : tool.status === 'inactive' ? '#fff3e0' : '#ffebee',
                color: tool.status === 'active' ? '#2e7d32' : tool.status === 'inactive' ? '#ef6c00' : '#c62828'
              }}>
                {tool.status.charAt(0).toUpperCase() + tool.status.slice(1)}
              </span>
            </div>
            
            <div style={{ marginBottom: '20px' }}>
              <p style={{ fontSize: '1.1rem' }}>{tool.description}</p>
              <p style={{ fontSize: '0.9rem', color: '#666', marginTop: '10px' }}>
                <strong>Category:</strong> {tool.category.charAt(0).toUpperCase() + tool.category.slice(1)}
              </p>
              <p style={{ fontSize: '0.9rem', color: '#666' }}>
                <strong>Version:</strong> {tool.version}
              </p>
            </div>
            
            <div style={{ marginTop: '30px' }}>
              <button 
                onClick={handleLaunchTool}
                style={{ padding: '10px 20px', fontSize: '1.1rem' }}
              >
                Launch Tool
              </button>
            </div>
            
            <div style={{ marginTop: '40px', padding: '20px', backgroundColor: '#f5f5f5', borderRadius: '4px' }}>
              <h2>Usage Instructions</h2>
              <p>This is a local version of the tool that runs entirely on your machine. No authentication or cloud services are required.</p>
              <ol>
                <li>Click the "Launch Tool" button above to start the tool</li>
                <li>The tool will open in a new window or tab</li>
                <li>You can use the tool as long as you need</li>
                <li>Close the tool window when you're done</li>
              </ol>
            </div>
          </div>
        ) : (
          <div style={{ textAlign: 'center', marginTop: '40px' }}>
            <p>Tool not found</p>
          </div>
        )}
      </div>
    </PageLayout>
  );
};

export default ToolDetails;

