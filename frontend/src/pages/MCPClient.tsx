import React, { useState } from "react";
import {
  Box,
  Button,
  FormControl,
  FormLabel,
  Input,
  VStack,
  Heading,
  Textarea,
  useToast,
} from "@chakra-ui/react";

const MCPClient = () => {
  const [serverUrl, setServerUrl] = useState("");
  const [message, setMessage] = useState("");
  const [response, setResponse] = useState("");
  const toast = useToast();

  const handleConnect = () => {
    // WebSocket connection logic here
    toast({
      title: "Connected",
      description: "Successfully connected to MCP server",
      status: "success",
      duration: 3000,
      isClosable: true,
    });
  };

  const handleSend = () => {
    // Message sending logic here
    setResponse("Response from server will appear here");
  };

  return (
    <Box>
      <Heading mb={6}>MCP Client</Heading>
      <VStack spacing={4} align="stretch">
        <FormControl>
          <FormLabel>Server URL</FormLabel>
          <Input
            value={serverUrl}
            onChange={(e) => setServerUrl(e.target.value)}
            placeholder="ws://localhost:3001"
          />
        </FormControl>
        <Button onClick={handleConnect} colorScheme="teal">
          Connect
        </Button>
        <FormControl>
          <FormLabel>Message</FormLabel>
          <Textarea
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            placeholder="Enter your message here"
          />
        </FormControl>
        <Button onClick={handleSend} colorScheme="blue">
          Send
        </Button>
        <FormControl>
          <FormLabel>Response</FormLabel>
          <Textarea value={response} isReadOnly height="200px" />
        </FormControl>
      </VStack>
    </Box>
  );
};

export default MCPClient;
