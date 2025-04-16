import React, { useState } from "react";
import {
  Box,
  Button,
  FormControl,
  FormLabel,
  Input,
  VStack,
  Heading,
  Switch,
  useToast,
} from "@chakra-ui/react";

const Settings = () => {
  const [settings, setSettings] = useState({
    port: "3001",
    maxConnections: "100",
    enableLogging: true,
    enableMetrics: true,
  });
  const toast = useToast();

  const handleSave = () => {
    // Save settings logic here
    toast({
      title: "Settings Saved",
      description: "Your settings have been updated successfully",
      status: "success",
      duration: 3000,
      isClosable: true,
    });
  };

  return (
    <Box>
      <Heading mb={6}>Settings</Heading>
      <VStack spacing={4} align="stretch">
        <FormControl>
          <FormLabel>Server Port</FormLabel>
          <Input
            value={settings.port}
            onChange={(e) => setSettings({ ...settings, port: e.target.value })}
            type="number"
          />
        </FormControl>
        <FormControl>
          <FormLabel>Max Connections</FormLabel>
          <Input
            value={settings.maxConnections}
            onChange={(e) =>
              setSettings({ ...settings, maxConnections: e.target.value })
            }
            type="number"
          />
        </FormControl>
        <FormControl display="flex" alignItems="center">
          <FormLabel mb="0">Enable Logging</FormLabel>
          <Switch
            isChecked={settings.enableLogging}
            onChange={(e) =>
              setSettings({ ...settings, enableLogging: e.target.checked })
            }
          />
        </FormControl>
        <FormControl display="flex" alignItems="center">
          <FormLabel mb="0">Enable Metrics</FormLabel>
          <Switch
            isChecked={settings.enableMetrics}
            onChange={(e) =>
              setSettings({ ...settings, enableMetrics: e.target.checked })
            }
          />
        </FormControl>
        <Button onClick={handleSave} colorScheme="teal">
          Save Settings
        </Button>
      </VStack>
    </Box>
  );
};

export default Settings;
