import React, { useState, useEffect } from 'react';
import {
  Box,
  VStack,
  HStack,
  Text,
  Button,
  NumberInput,
  NumberInputField,
  NumberInputStepper,
  NumberIncrementStepper,
  NumberDecrementStepper,
  Switch,
  FormControl,
  FormLabel,
  Code,
} from '@chakra-ui/react';

interface WatchConfig {
  watchInterval: number;
  autoRefresh: boolean;
}

interface MCPWatchProps {
  config: WatchConfig;
  onConfigChange: (config: Partial<WatchConfig>) => void;
}

export const MCPWatch: React.FC<MCPWatchProps> = ({ config, onConfigChange }) => {
  const [isWatching, setIsWatching] = useState(false);
  const [events, setEvents] = useState<string[]>([]);

  useEffect(() => {
    let watchInterval: NodeJS.Timeout;

    if (isWatching) {
      watchInterval = setInterval(() => {
        // Implement watch logic here
        setEvents(prev => [...prev, `Event detected at ${new Date().toISOString()}`]);
      }, config.watchInterval);
    }

    return () => {
      if (watchInterval) {
        clearInterval(watchInterval);
      }
    };
  }, [isWatching, config.watchInterval]);

  const toggleWatch = () => {
    setIsWatching(!isWatching);
    if (!isWatching) {
      setEvents([]);
    }
  };

  return (
    <VStack spacing={4} align="stretch">
      <FormControl>
        <FormLabel>Watch Interval (ms)</FormLabel>
        <NumberInput
          value={config.watchInterval}
          onChange={(_, value) => onConfigChange({ watchInterval: value })}
          min={1000}
          max={60000}
          step={1000}
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
        colorScheme={isWatching ? 'red' : 'blue'}
        onClick={toggleWatch}
      >
        {isWatching ? 'Stop Watching' : 'Start Watching'}
      </Button>

      <Box
        mt={4}
        p={4}
        borderWidth={1}
        borderRadius="md"
        maxHeight="300px"
        overflowY="auto"
      >
        <Text mb={2} fontWeight="bold">Events:</Text>
        {events.map((event, index) => (
          <Code key={index} display="block" mb={2}>
            {event}
          </Code>
        ))}
      </Box>
    </VStack>
  );
};

export default MCPWatch;
