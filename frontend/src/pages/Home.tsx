import React from 'react';
import { Link } from 'react-router-dom';
import PageLayout from '../components/layout/PageLayout';

const Home: React.FC = () => {
  return (
    <PageLayout>
      <header style={{ textAlign: 'center', marginBottom: '40px' }}>
        <h1 style={{ fontSize: '2.5rem' }}>MCP as a Service - Local</h1>
        <p style={{ fontSize: '1.2rem' }}>
          Launch and use Model Context Protocol tools locally
        </p>
      </header>

      <div style={{ display: 'flex', justifyContent: 'center', marginBottom: '40px' }}>
        <Link to="/dashboard">
          <button>Go to Dashboard</button>
        </Link>
      </div>

      <div style={{ display: 'flex', flexWrap: 'wrap', justifyContent: 'space-between' }}>
        <div className="card" style={{ flex: '1 1 300px', margin: '10px' }}>
          <h2>Local Tools</h2>
          <p>Access powerful MCP tools without any cloud dependencies</p>
        </div>

        <div className="card" style={{ flex: '1 1 300px', margin: '10px' }}>
          <h2>Easy Management</h2>
          <p>Start, stop, and manage your tools from a simple dashboard</p>
        </div>

        <div className="card" style={{ flex: '1 1 300px', margin: '10px' }}>
          <h2>WebSocket Connections</h2>
          <p>Fast, reliable connections to your tools through WebSockets</p>
        </div>
      </div>

      <footer style={{ textAlign: 'center', marginTop: '40px', padding: '20px', borderTop: '1px solid var(--border-color)' }}>
        <p>&copy; 2025 MCP-aaS Local</p>
      </footer>
    </PageLayout>
  );
};

export default Home;

