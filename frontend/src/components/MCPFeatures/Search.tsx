import React, { useState } from 'react';
import {
  Box,
  Input,
  Button,
  VStack,
  HStack,
  Text,
  NumberInput,
  NumberInputField,
  NumberInputStepper,
  NumberIncrementStepper,
  NumberDecrementStepper,
  Switch,
  FormControl,
  FormLabel,
} from '@chakra-ui/react';

interface SearchConfig {
  searchDepth: number;
  autoRefresh: boolean;
}

interface MCPSearchProps {
  config: SearchConfig;
  onConfigChange: (config: Partial<SearchConfig>) => void;
}

export const MCPSearch: React.FC<MCPSearchProps> = ({ config, onConfigChange }) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [isSearching, setIsSearching] = useState(false);

  const handleSearch = async () => {
    setIsSearching(true);
    try {
      // Implement search logic here
      await new Promise(resolve => setTimeout(resolve, 1000));
    } finally {
      setIsSearching(false);
    }
  };

  return (
    <VStack spacing={4} align="stretch">
      <FormControl>
        <FormLabel>Search Query</FormLabel>
        <Input
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          placeholder="Enter search query..."
        />
      </FormControl>

      <FormControl>
        <FormLabel>Search Depth</FormLabel>
        <NumberInput
          value={config.searchDepth}
          onChange={(_, value) => onConfigChange({ searchDepth: value })}
          min={1}
          max={10}
        >
          <NumberInputField />
          <NumberInputStepper>
            <NumberIncrementStepper />
            <NumberDecrementStepper />
          </NumberInputStepper>
        </NumberInput>
      </FormControl>

      <FormControl display="flex" alignItems="center">
        <FormLabel mb="0">Auto Refresh</FormLabel>
        <Switch
          isChecked={config.autoRefresh}
          onChange={(e) => onConfigChange({ autoRefresh: e.target.checked })}
        />
      </FormControl>

      <Button
        colorScheme="blue"
        onClick={handleSearch}
        isLoading={isSearching}
      >
        Search
      </Button>
    </VStack>
  );
};

export default MCPSearch;
