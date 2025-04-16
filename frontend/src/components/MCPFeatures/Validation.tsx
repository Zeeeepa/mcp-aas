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
  HStack,
  NumberInput,
  NumberInputField,
  NumberInputStepper,
  NumberIncrementStepper,
  NumberDecrementStepper,
} from '@chakra-ui/react';

const Validation: React.FC = () => {
  const [validationConfig, setValidationConfig] = useState({
    validationType: 'code',
    targetFiles: '',
    rules: '',
    autoFix: true,
    strict: false,
    saveResults: true,
    maxIssues: 100,
    severity: 'error',
  });
  const toast = useToast();

  const handleValidate = () => {
    toast({
      title: 'Validation Started',
      description: 'Code validation has been initiated',
      status: 'success',
      duration: 3000,
    });
  };

  return (
    <VStack spacing={4} align="stretch">
      <FormControl>
        <FormLabel>Validation Type</FormLabel>
        <Select
          value={validationConfig.validationType}
          onChange={(e) => setValidationConfig({...validationConfig, validationType: e.target.value})}
        >
          <option value="code">Code Style</option>
          <option value="security">Security</option>
          <option value="performance">Performance</option>
          <option value="accessibility">Accessibility</option>
          <option value="custom">Custom Rules</option>
        </Select>
      </FormControl>

      <FormControl>
        <FormLabel>Target Files (glob patterns, one per line)</FormLabel>
        <Textarea
          value={validationConfig.targetFiles}
          onChange={(e) => setValidationConfig({...validationConfig, targetFiles: e.target.value})}
          placeholder="Enter file patterns to validate"
          rows={4}
        />
      </FormControl>

      <FormControl>
        <FormLabel>Custom Rules (JSON format)</FormLabel>
        <Textarea
          value={validationConfig.rules}
          onChange={(e) => setValidationConfig({...validationConfig, rules: e.target.value})}
          placeholder="Enter custom validation rules"
          rows={4}
        />
      </FormControl>

      <FormControl>
        <FormLabel>Max Issues</FormLabel>
        <NumberInput
          value={validationConfig.maxIssues}
          onChange={(value) => setValidationConfig({...validationConfig, maxIssues: parseInt(value)})}
          min={1}
          max={1000}
        >
          <NumberInputField />
          <NumberInputStepper>
            <NumberIncrementStepper />
            <NumberDecrementStepper />
          </NumberInputStepper>
        </NumberInput>
      </FormControl>

      <FormControl>
        <FormLabel>Minimum Severity</FormLabel>
        <Select
          value={validationConfig.severity}
          onChange={(e) => setValidationConfig({...validationConfig, severity: e.target.value})}
        >
          <option value="info">Info</option>
          <option value="warning">Warning</option>
          <option value="error">Error</option>
          <option value="critical">Critical</option>
        </Select>
      </FormControl>

      <HStack spacing={8}>
        <FormControl display="flex" alignItems="center">
          <FormLabel mb="0">Auto Fix</FormLabel>
          <Switch
            isChecked={validationConfig.autoFix}
            onChange={(e) => setValidationConfig({...validationConfig, autoFix: e.target.checked})}
          />
        </FormControl>

        <FormControl display="flex" alignItems="center">
          <FormLabel mb="0">Strict Mode</FormLabel>
          <Switch
            isChecked={validationConfig.strict}
            onChange={(e) => setValidationConfig({...validationConfig, strict: e.target.checked})}
          />
        </FormControl>
      </HStack>

      <FormControl display="flex" alignItems="center">
        <FormLabel mb="0">Save Results</FormLabel>
        <Switch
          isChecked={validationConfig.saveResults}
          onChange={(e) => setValidationConfig({...validationConfig, saveResults: e.target.checked})}
        />
      </FormControl>

      <Button colorScheme="blue" onClick={handleValidate}>
        Start Validation
      </Button>
    </VStack>
  );
};

export default Validation;
