import React, { useState } from 'react';
import { Box, Flex, Button, VStack, useToast } from '@chakra-ui/react';
import { MCPSearch } from './Search';
import { MCPWatch } from './Watch';
import { MCPTest } from './Test';

// Core MCP feature configuration
interface MCPConfig {
  searchDepth: number;
  watchInterval: number;
  testTimeout: number;
  autoRefresh: boolean;
}

const defaultConfig: MCPConfig = {
  searchDepth: 3,
  watchInterval: 5000,
  testTimeout: 30000,
  autoRefresh: true
};

export const MCPFeatures: React.FC = () => {
  const [config, setConfig] = useState<MCPConfig>(defaultConfig);
  const [activeTab, setActiveTab] = useState<'search' | 'watch' | 'test'>('search');
  const toast = useToast();

  // Handle config updates
  const updateConfig = (updates: Partial<MCPConfig>) => {
    setConfig(prev => ({ ...prev, ...updates }));
    toast({
      title: 'Configuration updated',
      status: 'success',
      duration: 2000,
    });
  };

  // Render active feature
  const renderFeature = () => {
    switch (activeTab) {
      case 'search':
        return <MCPSearch config={config} onConfigChange={updateConfig} />;
      case 'watch':
        return <MCPWatch config={config} onConfigChange={updateConfig} />;
      case 'test':
        return <MCPTest config={config} onConfigChange={updateConfig} />;
    }
  };

  return (
    <Box p={4}>
      <Flex mb={4}>
        <Button
          onClick={() => setActiveTab('search')}
          colorScheme={activeTab === 'search' ? 'blue' : 'gray'}
          mr={2}
        >
          Search
        </Button>
        <Button
          onClick={() => setActiveTab('watch')}
          colorScheme={activeTab === 'watch' ? 'blue' : 'gray'}
          mr={2}
        >
          Watch
        </Button>
        <Button
          onClick={() => setActiveTab('test')}
          colorScheme={activeTab === 'test' ? 'blue' : 'gray'}
        >
          Test
        </Button>
      </Flex>
      <Box>{renderFeature()}</Box>
    </Box>
  );
};

export default MCPFeatures;
