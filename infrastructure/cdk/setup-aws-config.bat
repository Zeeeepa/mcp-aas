@echo off
echo AWS Configuration Setup for CDK Deployment
echo ==========================================
echo This script will help you set up your AWS credentials for CDK deployment.
echo You will need your AWS account ID and preferred region.
echo.

set /p AWS_ACCOUNT_ID="Enter your AWS account ID: "
if "%AWS_ACCOUNT_ID%"=="" (
    echo AWS account ID is required.
    exit /b 1
)

set /p AWS_REGION="Enter your preferred AWS region (default: us-east-1): "
if "%AWS_REGION%"=="" set AWS_REGION=us-east-1

echo.
echo Creating .env file...

(
    echo # AWS Configuration for CDK Deployment
    echo # Generated on %date% %time%
    echo CDK_DEFAULT_ACCOUNT=%AWS_ACCOUNT_ID%
    echo CDK_DEFAULT_REGION=%AWS_REGION%
) > .env

echo.
echo AWS configuration has been saved to: %CD%\.env
echo.
echo To deploy your CDK stacks, run:
echo 1. cd infrastructure\cdk
echo 2. npx cdk deploy --all
echo.
echo IMPORTANT: Make sure you have AWS CLI configured with valid credentials.
echo If not, you can configure it by running:
echo aws configure
echo.
echo Or manually create/edit the following files:
echo %%USERPROFILE%%\.aws\credentials:
echo [default]
echo aws_access_key_id = YOUR_ACCESS_KEY
echo aws_secret_access_key = YOUR_SECRET_KEY
echo.
echo %%USERPROFILE%%\.aws\config:
echo [default]
echo region = %AWS_REGION%
echo output = json

pause