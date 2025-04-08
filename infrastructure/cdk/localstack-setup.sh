#!/bin/bash

# Create a directory for LocalStack data
mkdir -p .localstack

# Create a docker-compose file for LocalStack
cat > docker-compose.localstack.yml << 'EOL'
version: '3.8'

services:
  localstack:
    container_name: localstack-mcp-aas
    image: localstack/localstack:latest
    ports:
      - "4566:4566"            # LocalStack Gateway
      - "4510-4559:4510-4559"  # external services port range
    environment:
      - DEBUG=1
      - DOCKER_HOST=unix:///var/run/docker.sock
      - HOSTNAME_EXTERNAL=localstack
      - SERVICES=s3,lambda,dynamodb,apigateway,iam,cognito,stepfunctions,events,cloudformation
      - DEFAULT_REGION=us-east-1
      - AWS_DEFAULT_REGION=us-east-1
      - AWS_ACCESS_KEY_ID=test
      - AWS_SECRET_ACCESS_KEY=test
    volumes:
      - "${PWD}/.localstack:/var/lib/localstack"
      - "/var/run/docker.sock:/var/run/docker.sock"

networks:
  default:
    name: localstack-network
EOL

# Create a .env file for local development
cat > .env.local << 'EOL'
CDK_DEFAULT_ACCOUNT=000000000000
CDK_DEFAULT_REGION=us-east-1
AWS_ACCESS_KEY_ID=test
AWS_SECRET_ACCESS_KEY=test
AWS_DEFAULT_REGION=us-east-1
LOCALSTACK_HOSTNAME=localhost
EOL

# Create a script to deploy to LocalStack
cat > deploy-to-localstack.sh << 'EOL'
#!/bin/bash

# Load environment variables
source .env.local

# Set LocalStack endpoint
export LOCALSTACK_HOSTNAME=localhost
export AWS_ENDPOINT_URL=http://localhost:4566

# Deploy CDK to LocalStack
npx cdk deploy --all --context use-local=true --require-approval never
EOL

chmod +x deploy-to-localstack.sh

echo "LocalStack setup complete!"
echo "To start LocalStack, run: docker-compose -f docker-compose.localstack.yml up -d"
echo "To deploy to LocalStack, run: ./deploy-to-localstack.sh"
