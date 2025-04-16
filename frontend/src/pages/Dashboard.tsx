import React from "react";
import {
  Box,
  Heading,
  SimpleGrid,
  Stat,
  StatLabel,
  StatNumber,
  StatHelpText,
} from "@chakra-ui/react";

const Dashboard = () => {
  return (
    <Box>
      <Heading mb={6}>Dashboard</Heading>
      <SimpleGrid columns={[1, 2, 3]} spacing={6}>
        <Stat p={4} shadow="md" border="1px" borderColor="gray.200" borderRadius="md">
          <StatLabel>Active Connections</StatLabel>
          <StatNumber>0</StatNumber>
          <StatHelpText>Current WebSocket connections</StatHelpText>
        </Stat>
        <Stat p={4} shadow="md" border="1px" borderColor="gray.200" borderRadius="md">
          <StatLabel>Messages Processed</StatLabel>
          <StatNumber>0</StatNumber>
          <StatHelpText>Total messages handled</StatHelpText>
        </Stat>
        <Stat p={4} shadow="md" border="1px" borderColor="gray.200" borderRadius="md">
          <StatLabel>Server Status</StatLabel>
          <StatNumber>Online</StatNumber>
          <StatHelpText>System operational</StatHelpText>
        </Stat>
      </SimpleGrid>
    </Box>
  );
};

export default Dashboard;
