// AWS Configuration Setup Script for CDK Deployment
// This script creates a .env file with AWS credentials for CDK deployment

const fs = require('fs');
const path = require('path');
const readline = require('readline');

const rl = readline.createInterface({
  input: process.stdin,
  output: process.stdout
});

console.log('AWS Configuration Setup for CDK Deployment');
console.log('==========================================');
console.log('This script will help you set up your AWS credentials for CDK deployment.');
console.log('You will need your AWS account ID and preferred region.');
console.log('');

// Get AWS account ID and region from user
rl.question('Enter your AWS account ID: ', (accountId) => {
  if (!accountId) {
    console.error('AWS account ID is required.');
    rl.close();
    return;
  }

  rl.question('Enter your preferred AWS region (default: us-east-1): ', (region) => {
    const awsRegion = region || 'us-east-1';
    
    // Create .env file content
    const envContent = `# AWS Configuration for CDK Deployment
# Generated on ${new Date().toISOString()}
CDK_DEFAULT_ACCOUNT=${accountId}
CDK_DEFAULT_REGION=${awsRegion}
`;

    // Write .env file
    const envFilePath = path.join(__dirname, '.env');
    fs.writeFileSync(envFilePath, envContent);
    
    console.log('\nAWS configuration has been saved to:', envFilePath);
    console.log('\nTo deploy your CDK stacks, run:');
    console.log('1. cd infrastructure/cdk');
    console.log('2. npx cdk deploy --all');
    
    // Check if AWS CLI is configured
    console.log('\nIMPORTANT: Make sure you have AWS CLI configured with valid credentials.');
    console.log('If not, you can configure it by running:');
    console.log('aws configure');
    console.log('\nOr manually create/edit the following files:');
    console.log('~/.aws/credentials:');
    console.log('[default]');
    console.log('aws_access_key_id = YOUR_ACCESS_KEY');
    console.log('aws_secret_access_key = YOUR_SECRET_KEY');
    console.log('\n~/.aws/config:');
    console.log('[default]');
    console.log(`region = ${awsRegion}`);
    console.log('output = json');
    
    rl.close();
  });
});