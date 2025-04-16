import React from "react";
import { Box, Flex, Link, Heading } from "@chakra-ui/react";
import { Link as RouterLink } from "react-router-dom";

const Layout = ({ children }) => {
  return (
    <Box minH="100vh">
      <Flex
        as="nav"
        align="center"
        justify="space-between"
        wrap="wrap"
        padding="1.5rem"
        bg="teal.500"
        color="white"
      >
        <Heading as="h1" size="lg">
          MCP-AAS
        </Heading>
        <Box>
          <Link as={RouterLink} to="/" mr={4}>
            Dashboard
          </Link>
          <Link as={RouterLink} to="/client" mr={4}>
            MCP Client
          </Link>
          <Link as={RouterLink} to="/settings">
            Settings
          </Link>
        </Box>
      </Flex>
      <Box p={4}>{children}</Box>
    </Box>
  );
};

export default Layout;
