import React, { useState } from 'react';
import {
  Box,
  VStack,
  Button,
  Text,
  NumberInput,
  NumberInputField,
  NumberInputStepper,
  NumberIncrementStepper,
  NumberDecrementStepper,
  Switch,
  FormControl,
  FormLabel,
  Select,
  Progress,
  Code,
} from '@chakra-ui/react';

interface TestConfig {
  testTimeout: number;
  autoRefresh: boolean;
}

interface MCPTestProps {
  config: TestConfig;
  onConfigChange: (config: Partial<TestConfig>) => void;
}

export const MCPTest: React.FC<MCPTestProps> = ({ config, onConfigChange }) => {
  const [testType, setTestType] = useState<'unit' | 'integration' | 'e2e'>('unit');
  const [isTesting, setIsTesting] = useState(false);
  const [progress, setProgress] = useState(0);
  const [results, setResults] = useState<string[]>([]);

  const runTest = async () => {
    setIsTesting(true);
    setProgress(0);
    setResults([]);

    try {
      // Simulate test execution
      for (let i = 0; i <= 100; i += 10) {
        await new Promise(resolve => setTimeout(resolve, 500));
        setProgress(i);
        if (i % 20 === 0) {
          setResults(prev => [...prev, `${testType} test ${i}% complete`]);
        }
      }
    } finally {
      setIsTesting(false);
      setResults(prev => [...prev, `${testType} tests completed successfully`]);
    }
  };

  return (
    <VStack spacing={4} align="stretch">
      <FormControl>
        <FormLabel>Test Type</FormLabel>
        <Select
          value={testType}
          onChange={(e) => setTestType(e.target.value as 'unit' | 'integration' | 'e2e')}
        >
          <option value="unit">Unit Tests</option>
          <option value="integration">Integration Tests</option>
          <option value="e2e">End-to-End Tests</option>
        </Select>
      </FormControl>

      <FormControl>
        <FormLabel>Test Timeout (ms)</FormLabel>
        <NumberInput
          value={config.testTimeout}
          onChange={(_, value) => onConfigChange({ testTimeout: value })}
          min={5000}
          max={300000}
          step={5000}
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
        onClick={runTest}
        isLoading={isTesting}
      >
        Run Tests
      </Button>

      {isTesting && (
        <Box>
          <Text mb={2}>Progress:</Text>
          <Progress value={progress} size="sm" colorScheme="blue" />
        </Box>
      )}

      <Box
        mt={4}
        p={4}
        borderWidth={1}
        borderRadius="md"
        maxHeight="300px"
        overflowY="auto"
      >
        <Text mb={2} fontWeight="bold">Test Results:</Text>
        {results.map((result, index) => (
          <Code key={index} display="block" mb={2}>
            {result}
          </Code>
        ))}
      </Box>
    </VStack>
  );
};

export default MCPTest;
