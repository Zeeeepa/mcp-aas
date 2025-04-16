import React from 'react';
import { Box, Container, Flex, Heading, Button, Link as ChakraLink } from '@chakra-ui/react';
import { Link, useNavigate } from 'react-router-dom';
import ToolDiscovery from '../components/MCPFeatures/ToolDiscovery';

const Dashboard: React.FC = () => {
  const navigate = useNavigate();

  return (
    <Container maxW="container.xl" py={8}>
      <Flex justifyContent="space-between" alignItems="center" mb={8}>
        <Heading>MCP Dashboard</Heading>
        
        <Box>
          <Button
            as={Link}
            to="/settings"
            colorScheme="gray"
            mr={4}
          >
            Settings
          </Button>
        </Box>
      </Flex>

      <ToolDiscovery />

      <Box mt={8}>
        <ChakraLink as={Link} to="/" color="blue.500">
          Back to Home
        </ChakraLink>
      </Box>
    </Container>
  );
};

export default Dashboard;
