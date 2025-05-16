import React, { useState } from 'react';

export const MCPFeatures: React.FC = () => {
  const [activeTab, setActiveTab] = useState(0);

  const tabs = [
    { name: 'Continuity Search', content: 'Continuity search feature allows you to search for content across multiple pages.' },
    { name: 'Page Scraping', content: 'Page scraping feature allows you to extract content from web pages.' },
    { name: 'Testing', content: 'Testing feature allows you to test your MCP tools.' },
    { name: 'Validation', content: 'Validation feature allows you to validate your MCP tools.' }
  ];

  return (
    <div style={{ padding: '16px' }}>
      <div style={{ display: 'flex', borderBottom: '1px solid #ccc' }}>
        {tabs.map((tab, index) => (
          <button
            key={index}
            onClick={() => setActiveTab(index)}
            style={{
              padding: '8px 16px',
              backgroundColor: activeTab === index ? '#f0f0f0' : 'transparent',
              border: 'none',
              borderBottom: activeTab === index ? '2px solid #3182ce' : 'none',
              cursor: 'pointer'
            }}
          >
            {tab.name}
          </button>
        ))}
      </div>

      <div style={{ padding: '16px' }}>
        {tabs[activeTab].content}
      </div>
    </div>
  );
};

export default MCPFeatures;

