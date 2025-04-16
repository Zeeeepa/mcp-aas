# MCP-AAS CDK Deployment Guide

This guide will help you set up and deploy the AWS CDK stacks for the MCP-AAS project.

## Prerequisites

- [Node.js](https://nodejs.org/) (v14 or later)
- [AWS CLI](https://aws.amazon.com/cli/) installed and configured
- AWS account with appropriate permissions

## Setup AWS Configuration

Before deploying the CDK stacks, you need to configure your AWS account and region. You can do this in one of the following ways:

### Option 1: Using the Setup Script (Windows)

1. Navigate to the `infrastructure/cdk` directory:
   ```
   cd infrastructure/cdk
   ```

2. Run the setup script:
   ```
   setup-aws-config.bat
   ```

3. Follow the prompts to enter your AWS account ID and preferred region.

### Option 2: Using the Setup Script (Node.js)

1. Navigate to the `infrastructure/cdk` directory:
   ```
   cd infrastructure/cdk
   ```

2. Run the setup script:
   ```
   node setup-aws-config.js
   ```

3. Follow the prompts to enter your AWS account ID and preferred region.

### Option 3: Manual Configuration

1. Create a `.env` file in the `infrastructure/cdk` directory with the following content:
   ```
   CDK_DEFAULT_ACCOUNT=your-aws-account-id
   CDK_DEFAULT_REGION=your-preferred-region
   ```

2. Replace `your-aws-account-id` with your AWS account ID and `your-preferred-region` with your preferred AWS region (e.g., `us-east-1`).

## AWS CLI Configuration

Make sure your AWS CLI is configured with valid credentials. You can configure it by running:

```
aws configure
```

Or manually create/edit the following files:

### For Windows:

```
%USERPROFILE%\.aws\credentials:
[default]
aws_access_key_id = YOUR_ACCESS_KEY
aws_secret_access_key = YOUR_SECRET_KEY

%USERPROFILE%\.aws\config:
[default]
region = your-preferred-region
output = json
```

### For Linux/Mac:

```
~/.aws/credentials:
[default]
aws_access_key_id = YOUR_ACCESS_KEY
aws_secret_access_key = YOUR_SECRET_KEY

~/.aws/config:
[default]
region = your-preferred-region
output = json
```

## Deploy CDK Stacks

Once you have configured your AWS account and region, you can deploy the CDK stacks:

1. Navigate to the `infrastructure/cdk` directory:
   ```
   cd infrastructure/cdk
   ```

2. Install dependencies (if not already installed):
   ```
   npm install
   ```

3. Deploy all stacks:
   ```
   npx cdk deploy --all
   ```

## Troubleshooting

### Error: Unable to resolve AWS account to use

If you encounter the error "Unable to resolve AWS account to use", make sure:

1. You have created a `.env` file with the correct AWS account ID and region.
2. You have configured the AWS CLI with valid credentials.
3. You are in the correct directory (`infrastructure/cdk`) when running the deployment command.

### Error: AWS credentials not found

If you encounter an error related to AWS credentials, make sure:

1. You have installed and configured the AWS CLI.
2. You have valid AWS credentials in the appropriate location.
3. Your AWS credentials have the necessary permissions to deploy CDK stacks.

## Additional Resources

- [AWS CDK Documentation](https://docs.aws.amazon.com/cdk/latest/guide/home.html)
- [AWS CLI Documentation](https://docs.aws.amazon.com/cli/latest/userguide/cli-chap-welcome.html)
