import React from 'react';
import { Link } from 'react-router-dom';

const MainNav: React.FC = () => {
  return (
    <nav style={{ 
      padding: '15px 20px', 
      backgroundColor: '#f5f5f5', 
      boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
      marginBottom: '20px',
      borderRadius: '4px'
    }}>
      <div style={{ 
        display: 'flex', 
        justifyContent: 'space-between', 
        alignItems: 'center'
      }}>
        <div>
          <Link to="/" style={{ 
            fontSize: '1.2rem', 
            fontWeight: 'bold', 
            textDecoration: 'none', 
            color: '#333'
          }}>
            MCP-aaS Local
          </Link>
        </div>
        
        <div style={{ display: 'flex', alignItems: 'center', gap: '20px' }}>
          <Link to="/dashboard" style={{ textDecoration: 'none', color: '#333' }}>Dashboard</Link>
          <Link to="/tools" style={{ textDecoration: 'none', color: '#333' }}>Tools</Link>
        </div>
      </div>
    </nav>
  );
};

export default MainNav;

