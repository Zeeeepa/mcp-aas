import React, { useState } from 'react';
import {
  Box,
  VStack,
  Tabs,
  TabList,
  TabPanels,
  Tab,
  TabPanel,
  useToast,
} from '@chakra-ui/react';
import ContinuitySearch from './ContinuitySearch';
import PageScraping from './PageScraping';
import Testing from './Testing';
import Validation from './Validation';

export const MCPFeatures: React.FC = () => {
  const toast = useToast();
  const [activeTab, setActiveTab] = useState(0);

  return (
    <Box p={4}>
      <Tabs 
        variant="enclosed" 
        colorScheme="blue" 
        onChange={(index) => setActiveTab(index)}
      >
        <TabList>
          <Tab>Continuity Search</Tab>
          <Tab>Page Scraping</Tab>
          <Tab>Testing</Tab>
          <Tab>Validation</Tab>
        </TabList>

        <TabPanels>
          <TabPanel>
            <ContinuitySearch />
          </TabPanel>
          <TabPanel>
            <PageScraping />
          </TabPanel>
          <TabPanel>
            <Testing />
          </TabPanel>
          <TabPanel>
            <Validation />
          </TabPanel>
        </TabPanels>
      </Tabs>
    </Box>
  );
};

export default MCPFeatures;
