import React, { useState } from 'react';
import {
  VStack,
  Input,
  Button,
  FormControl,
  FormLabel,
  Switch,
  useToast,
  Select,
  Textarea,
  Checkbox,
  HStack,
} from '@chakra-ui/react';

const Testing: React.FC = () => {
  const [testConfig, setTestConfig] = useState({
    testType: 'unit',
    testFiles: '',
    parallel: true,
    watch: false,
    coverage: true,
    verbose: true,
    saveResults: true,
    environment: 'development',
  });
  const toast = useToast();

  const handleTest = () => {
    toast({
      title: 'Testing Started',
      description: 'Test suite execution has been initiated',
      status: 'success',
      duration: 3000,
    });
  };

  return (
    <VStack spacing={4} align="stretch">
      <FormControl>
        <FormLabel>Test Type</FormLabel>
        <Select
          value={testConfig.testType}
          onChange={(e) => setTestConfig({...testConfig, testType: e.target.value})}
        >
          <option value="unit">Unit Tests</option>
          <option value="integration">Integration Tests</option>
          <option value="e2e">End-to-End Tests</option>
          <option value="performance">Performance Tests</option>
        </Select>
      </FormControl>

      <FormControl>
        <FormLabel>Test Files (glob patterns, one per line)</FormLabel>
        <Textarea
          value={testConfig.testFiles}
          onChange={(e) => setTestConfig({...testConfig, testFiles: e.target.value})}
          placeholder="Enter test file patterns"
          rows={4}
        />
      </FormControl>

      <FormControl>
        <FormLabel>Environment</FormLabel>
        <Select
          value={testConfig.environment}
          onChange={(e) => setTestConfig({...testConfig, environment: e.target.value})}
        >
          <option value="development">Development</option>
          <option value="staging">Staging</option>
          <option value="production">Production</option>
        </Select>
      </FormControl>

      <HStack spacing={8}>
        <FormControl display="flex" alignItems="center">
          <FormLabel mb="0">Parallel</FormLabel>
          <Switch
            isChecked={testConfig.parallel}
            onChange={(e) => setTestConfig({...testConfig, parallel: e.target.checked})}
          />
        </FormControl>

        <FormControl display="flex" alignItems="center">
          <FormLabel mb="0">Watch Mode</FormLabel>
          <Switch
            isChecked={testConfig.watch}
            onChange={(e) => setTestConfig({...testConfig, watch: e.target.checked})}
          />
        </FormControl>
      </HStack>

      <HStack spacing={8}>
        <FormControl display="flex" alignItems="center">
          <FormLabel mb="0">Coverage</FormLabel>
          <Switch
            isChecked={testConfig.coverage}
            onChange={(e) => setTestConfig({...testConfig, coverage: e.target.checked})}
          />
        </FormControl>

        <FormControl display="flex" alignItems="center">
          <FormLabel mb="0">Verbose</FormLabel>
          <Switch
            isChecked={testConfig.verbose}
            onChange={(e) => setTestConfig({...testConfig, verbose: e.target.checked})}
          />
        </FormControl>
      </HStack>

      <FormControl display="flex" alignItems="center">
        <FormLabel mb="0">Save Results</FormLabel>
        <Switch
          isChecked={testConfig.saveResults}
          onChange={(e) => setTestConfig({...testConfig, saveResults: e.target.checked})}
        />
      </FormControl>

      <Button colorScheme="blue" onClick={handleTest}>
        Run Tests
      </Button>
    </VStack>
  );
};

export default Testing;
