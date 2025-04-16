import React, { useState } from 'react';
import {
  Box,
  VStack,
  Input,
  Button,
  FormControl,
  FormLabel,
  Switch,
  Text,
  useToast,
  Code,
  Select,
} from '@chakra-ui/react';

const ContinuitySearch: React.FC = () => {
  const [searchConfig, setSearchConfig] = useState({
    query: '',
    searchType: 'code',
    autoRefresh: false,
    interval: 60,
    saveResults: false,
    contextDepth: 2,
  });
  const toast = useToast();

  const handleSearch = () => {
    toast({
      title: 'Search Started',
      description: 'Continuous search has been initiated',
      status: 'success',
      duration: 3000,
    });
  };

  return (
    <VStack spacing={4} align="stretch">
      <FormControl>
        <FormLabel>Search Query</FormLabel>
        <Input
          value={searchConfig.query}
          onChange={(e) => setSearchConfig({...searchConfig, query: e.target.value})}
          placeholder="Enter search query"
        />
      </FormControl>

      <FormControl>
        <FormLabel>Search Type</FormLabel>
        <Select
          value={searchConfig.searchType}
          onChange={(e) => setSearchConfig({...searchConfig, searchType: e.target.value})}
        >
          <option value="code">Code Search</option>
          <option value="semantic">Semantic Search</option>
          <option value="dependency">Dependency Search</option>
          <option value="pattern">Pattern Search</option>
        </Select>
      </FormControl>

      <FormControl>
        <FormLabel>Context Depth</FormLabel>
        <Input
          type="number"
          value={searchConfig.contextDepth}
          onChange={(e) => setSearchConfig({...searchConfig, contextDepth: parseInt(e.target.value)})}
          min={1}
          max={5}
        />
      </FormControl>

      <FormControl display="flex" alignItems="center">
        <FormLabel mb="0">Auto Refresh</FormLabel>
        <Switch
          isChecked={searchConfig.autoRefresh}
          onChange={(e) => setSearchConfig({...searchConfig, autoRefresh: e.target.checked})}
        />
      </FormControl>

      <FormControl>
        <FormLabel>Refresh Interval (seconds)</FormLabel>
        <Input
          type="number"
          value={searchConfig.interval}
          onChange={(e) => setSearchConfig({...searchConfig, interval: parseInt(e.target.value)})}
          isDisabled={!searchConfig.autoRefresh}
        />
      </FormControl>

      <FormControl display="flex" alignItems="center">
        <FormLabel mb="0">Save Results</FormLabel>
        <Switch
          isChecked={searchConfig.saveResults}
          onChange={(e) => setSearchConfig({...searchConfig, saveResults: e.target.checked})}
        />
      </FormControl>

      <Button colorScheme="blue" onClick={handleSearch}>
        Start Search
      </Button>
    </VStack>
  );
};

export default ContinuitySearch;
