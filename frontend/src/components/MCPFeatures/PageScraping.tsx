import React, { useState } from 'react';
import {
  VStack,
  Input,
  Button,
  FormControl,
  FormLabel,
  Switch,
  useToast,
  Textarea,
  Select,
  NumberInput,
  NumberInputField,
  NumberInputStepper,
  NumberIncrementStepper,
  NumberDecrementStepper,
} from '@chakra-ui/react';

const PageScraping: React.FC = () => {
  const [scrapingConfig, setScrapingConfig] = useState({
    urls: '',
    selector: '',
    depth: 1,
    interval: 60,
    autoScrape: false,
    saveResults: true,
    format: 'json',
    maxPages: 10,
  });
  const toast = useToast();

  const handleScrape = () => {
    toast({
      title: 'Scraping Started',
      description: 'Page scraping has been initiated',
      status: 'success',
      duration: 3000,
    });
  };

  return (
    <VStack spacing={4} align="stretch">
      <FormControl>
        <FormLabel>URLs (one per line)</FormLabel>
        <Textarea
          value={scrapingConfig.urls}
          onChange={(e) => setScrapingConfig({...scrapingConfig, urls: e.target.value})}
          placeholder="Enter URLs to scrape"
          rows={4}
        />
      </FormControl>

      <FormControl>
        <FormLabel>CSS Selector</FormLabel>
        <Input
          value={scrapingConfig.selector}
          onChange={(e) => setScrapingConfig({...scrapingConfig, selector: e.target.value})}
          placeholder="Enter CSS selector"
        />
      </FormControl>

      <FormControl>
        <FormLabel>Crawl Depth</FormLabel>
        <NumberInput
          value={scrapingConfig.depth}
          onChange={(value) => setScrapingConfig({...scrapingConfig, depth: parseInt(value)})}
          min={1}
          max={5}
        >
          <NumberInputField />
          <NumberInputStepper>
            <NumberIncrementStepper />
            <NumberDecrementStepper />
          </NumberInputStepper>
        </NumberInput>
      </FormControl>

      <FormControl>
        <FormLabel>Max Pages</FormLabel>
        <NumberInput
          value={scrapingConfig.maxPages}
          onChange={(value) => setScrapingConfig({...scrapingConfig, maxPages: parseInt(value)})}
          min={1}
          max={100}
        >
          <NumberInputField />
          <NumberInputStepper>
            <NumberIncrementStepper />
            <NumberDecrementStepper />
          </NumberInputStepper>
        </NumberInput>
      </FormControl>

      <FormControl>
        <FormLabel>Output Format</FormLabel>
        <Select
          value={scrapingConfig.format}
          onChange={(e) => setScrapingConfig({...scrapingConfig, format: e.target.value})}
        >
          <option value="json">JSON</option>
          <option value="csv">CSV</option>
          <option value="xml">XML</option>
          <option value="txt">Plain Text</option>
        </Select>
      </FormControl>

      <FormControl display="flex" alignItems="center">
        <FormLabel mb="0">Auto Scrape</FormLabel>
        <Switch
          isChecked={scrapingConfig.autoScrape}
          onChange={(e) => setScrapingConfig({...scrapingConfig, autoScrape: e.target.checked})}
        />
      </FormControl>

      <FormControl>
        <FormLabel>Scrape Interval (seconds)</FormLabel>
        <Input
          type="number"
          value={scrapingConfig.interval}
          onChange={(e) => setScrapingConfig({...scrapingConfig, interval: parseInt(e.target.value)})}
          isDisabled={!scrapingConfig.autoScrape}
        />
      </FormControl>

      <FormControl display="flex" alignItems="center">
        <FormLabel mb="0">Save Results</FormLabel>
        <Switch
          isChecked={scrapingConfig.saveResults}
          onChange={(e) => setScrapingConfig({...scrapingConfig, saveResults: e.target.checked})}
        />
      </FormControl>

      <Button colorScheme="blue" onClick={handleScrape}>
        Start Scraping
      </Button>
    </VStack>
  );
};

export default PageScraping;
