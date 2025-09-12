#!/bin/bash

# Deploy script for NioChat to Portainer
# This script updates the Portainer stack with new images

set -e

# Configuration
PORTAINER_URL="https://portainer.niochat.com.br"
STACK_NAME="niochat"
BACKEND_IMAGE="ghcr.io/juniorssilvaa/niochat-backend:latest"
FRONTEND_IMAGE="ghcr.io/juniorssilvaa/niochat-frontend:latest"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 Deploying NioChat to Portainer...${NC}"

# Check if required environment variables are set
if [ -z "$PORTAINER_API_KEY" ]; then
    echo -e "${RED}❌ Error: PORTAINER_API_KEY environment variable is not set${NC}"
    echo "Please set your Portainer API key:"
    echo "export PORTAINER_API_KEY=your-api-key-here"
    exit 1
fi

# Function to make API calls to Portainer
portainer_api() {
    local method=$1
    local endpoint=$2
    local data=$3
    
    if [ -n "$data" ]; then
        curl -s -X "$method" \
            "$PORTAINER_URL/api$endpoint" \
            -H "X-API-Key: $PORTAINER_API_KEY" \
            -H "Content-Type: application/json" \
            -d "$data"
    else
        curl -s -X "$method" \
            "$PORTAINER_URL/api$endpoint" \
            -H "X-API-Key: $PORTAINER_API_KEY" \
            -H "Content-Type: application/json"
    fi
}

# Get stack information
echo -e "${YELLOW}📋 Getting stack information...${NC}"
STACK_INFO=$(portainer_api "GET" "/stacks")

# Extract stack ID (assuming we have one stack named niochat)
STACK_ID=$(echo "$STACK_INFO" | jq -r '.[] | select(.Name == "'$STACK_NAME'") | .Id')

if [ -z "$STACK_ID" ] || [ "$STACK_ID" = "null" ]; then
    echo -e "${RED}❌ Error: Stack '$STACK_NAME' not found in Portainer${NC}"
    echo "Available stacks:"
    echo "$STACK_INFO" | jq -r '.[].Name'
    exit 1
fi

echo -e "${GREEN}✅ Found stack: $STACK_NAME (ID: $STACK_ID)${NC}"

# Get current stack configuration
echo -e "${YELLOW}📥 Getting current stack configuration...${NC}"
CURRENT_STACK=$(portainer_api "GET" "/stacks/$STACK_ID")

# Update the stack with new images
echo -e "${YELLOW}🔄 Updating stack with new images...${NC}"

# Create updated stack configuration
UPDATED_STACK=$(echo "$CURRENT_STACK" | jq --arg backend "$BACKEND_IMAGE" --arg frontend "$FRONTEND_IMAGE" '
    .StackFileContent = (.StackFileContent | 
        gsub("ghcr\\.io/juniorssilvaa/niochat-backend:[^\\s]+"; $backend) |
        gsub("ghcr\\.io/juniorssilvaa/niochat-frontend:[^\\s]+"; $frontend)
    )
')

# Deploy the updated stack
echo -e "${YELLOW}🚀 Deploying updated stack...${NC}"
DEPLOY_RESULT=$(portainer_api "PUT" "/stacks/$STACK_ID" "$UPDATED_STACK")

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Stack updated successfully!${NC}"
    echo -e "${GREEN}🌐 Frontend: https://app.niochat.com.br${NC}"
    echo -e "${GREEN}🔧 API: https://api.niochat.com.br${NC}"
    echo -e "${GREEN}⚙️ Admin: https://admin.niochat.com.br${NC}"
    
    # Wait a moment and check stack status
    echo -e "${YELLOW}⏳ Waiting for deployment to complete...${NC}"
    sleep 10
    
    # Check if stack is running
    STACK_STATUS=$(portainer_api "GET" "/stacks/$STACK_ID")
    STATUS=$(echo "$STACK_STATUS" | jq -r '.Status')
    
    if [ "$STATUS" = "1" ]; then
        echo -e "${GREEN}✅ Stack is running successfully!${NC}"
    else
        echo -e "${YELLOW}⚠️ Stack status: $STATUS${NC}"
    fi
else
    echo -e "${RED}❌ Error: Failed to update stack${NC}"
    echo "$DEPLOY_RESULT"
    exit 1
fi

echo -e "${GREEN}🎉 Deployment completed!${NC}"
