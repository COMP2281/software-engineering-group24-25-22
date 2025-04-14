#!/bin/bash

# Receipt Scanner API Testing Script
# This script provides curl commands for testing the Receipt Scanner API
#
# It was really useful to have this to test the API Endpoints.

# Base URL
API_URL="http://localhost:8000/api"

# Colors for better readability
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Authentication helpers
function login() {
  echo -e "${BLUE}Logging in to get authentication tokens...${NC}"
  
  # Set up curl command
  HEADERS=("-H" "Content-Type: application/json")
  
  # JSON data with proper escaping for both bash and zsh
  JSON_DATA='{"email":"'$1'","password":"'$2'"}'

  echo curl -s -X POST $API_URL/auth/login/ "${HEADERS[@]}" -d "$JSON_DATA"
  
  # Execute the curl command
  LOGIN_RESPONSE=$(curl -s -X POST $API_URL/auth/login/ "${HEADERS[@]}" -d "$JSON_DATA")
  
  # Extract tokens
  ACCESS_TOKEN=$(echo "$LOGIN_RESPONSE" | grep -o '"access":"[^"]*' | cut -d'"' -f4)
  REFRESH_TOKEN=$(echo "$LOGIN_RESPONSE" | grep -o '"refresh":"[^"]*' | cut -d'"' -f4)
  
  if [ -z "$ACCESS_TOKEN" ] || [ "$ACCESS_TOKEN" = "null" ]; then
    echo -e "${RED}Login failed. Check your credentials.${NC}"
    echo "Response: $LOGIN_RESPONSE"
    return 1
  fi
  
  echo -e "${GREEN}Login successful!${NC}"
  echo "Access Token: $ACCESS_TOKEN"
  echo "Refresh Token: $REFRESH_TOKEN"
  
  # Save tokens to environment variables
  export ACCESS_TOKEN=$ACCESS_TOKEN
  export REFRESH_TOKEN=$REFRESH_TOKEN
  
  return 0
}

function refresh_token() {
  echo -e "${BLUE}Refreshing access token...${NC}"
  
  # Set up curl command
  HEADERS=("-H" "Content-Type: application/json")
  
  # JSON data with proper escaping for both bash and zsh
  JSON_DATA='{"refresh":"'$REFRESH_TOKEN'"}'
  
  # Execute the curl command
  REFRESH_RESPONSE=$(curl -s -X POST $API_URL/auth/refresh/ "${HEADERS[@]}" -d "$JSON_DATA")
  
  # Extract new tokens
  NEW_ACCESS_TOKEN=$(echo "$REFRESH_RESPONSE" | grep -o '"access":"[^"]*' | cut -d'"' -f4)
  NEW_REFRESH_TOKEN=$(echo "$REFRESH_RESPONSE" | grep -o '"refresh":"[^"]*' | cut -d'"' -f4)
  
  if [ -z "$NEW_ACCESS_TOKEN" ] || [ "$NEW_ACCESS_TOKEN" = "null" ]; then
    echo -e "${RED}Token refresh failed.${NC}"
    echo "Response: $REFRESH_RESPONSE"
    return 1
  fi
  
  echo -e "${GREEN}Token refresh successful!${NC}"
  echo "New Access Token: $NEW_ACCESS_TOKEN"
  
  # Check if refresh token changed (token rotation)
  if [ "$REFRESH_TOKEN" != "$NEW_REFRESH_TOKEN" ] && [ -n "$NEW_REFRESH_TOKEN" ]; then
    echo "New Refresh Token: $NEW_REFRESH_TOKEN"
    export REFRESH_TOKEN=$NEW_REFRESH_TOKEN
  fi
  
  export ACCESS_TOKEN=$NEW_ACCESS_TOKEN
  
  return 0
}

# ================================
# RECEIPT ENDPOINTS
# ================================

# List all receipts
function list_receipts() {
  echo -e "${BLUE}Listing all receipts...${NC}"
  
  curl -s -X GET "$API_URL/receipts/" \
    -H "Authorization: Bearer $ACCESS_TOKEN" \
    -H "Content-Type: application/json" | jq
}

# Get a single receipt by ID
function get_receipt() {
  if [ -z "$1" ]; then
    echo -e "${RED}Receipt ID is required${NC}"
    return 1
  fi
  
  echo -e "${BLUE}Getting receipt with ID $1...${NC}"
  
  curl -s -X GET "$API_URL/receipts/$1/" \
    -H "Authorization: Bearer $ACCESS_TOKEN" \
    -H "Content-Type: application/json" | jq
}

# Create a new receipt manually
function create_receipt() {
  echo -e "${BLUE}Creating a new receipt...${NC}"
  
  CURRENT_DATE=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
  
  curl -s -X POST "$API_URL/receipts/" \
    -H "Authorization: Bearer $ACCESS_TOKEN" \
    -H "Content-Type: application/json" \
    -d '{
      "merchant_name": "Test Store",
      "transaction_time": "'"$CURRENT_DATE"'",
      "category": "Groceries",
      "description": "Week shopping",
      "total_amount": 45.75,
      "tax_amount": 4.25,
      "currency": "GBP",
      "status": "pending",
	  "file_id": "FileID",
	  "file_type": "jpeg",
	  "original_filename": "yeah"
    }' | jq
}

# Update a receipt
function update_receipt() {
  if [ -z "$1" ]; then
    echo -e "${RED}Receipt ID is required${NC}"
    return 1
  fi
  
  echo -e "${BLUE}Updating receipt with ID $1...${NC}"
  
  curl -s -X PATCH "$API_URL/receipts/$1/" \
    -H "Authorization: Bearer $ACCESS_TOKEN" \
    -H "Content-Type: application/json" \
    -d '{
      "category": "Office Supplies",
      "description": "Updated description",
      "status": "approved",
	  "merchant_address": "Coool st."
    }' | jq
}

# Delete a receipt
function delete_receipt() {
  if [ -z "$1" ]; then
    echo -e "${RED}Receipt ID is required${NC}"
    return 1
  fi
  
  echo -e "${BLUE}Deleting receipt with ID $1...${NC}"
  
  curl -s -X DELETE "$API_URL/receipts/$1/" \
    -H "Authorization: Bearer $ACCESS_TOKEN" \
    -H "Content-Type: application/json"
  
  echo -e "${GREEN}Receipt deleted (if it existed and belonged to you)${NC}"
}

# Export receipts
function export_receipts() {
  FORMAT=${1:-"json"} # Default to JSON if not specified
  
  echo -e "${BLUE}Exporting receipts in $FORMAT format...${NC}"
  
  curl -s -X GET "$API_URL/receipts/export/?format=$FORMAT" \
    -H "Authorization: Bearer $ACCESS_TOKEN" \
    -H "Content-Type: application/json" \
    -o "receipts_export.$FORMAT"
  
  echo -e "${GREEN}Receipts exported to receipts_export.$FORMAT${NC}"
}

# ================================
# RECEIPT PARSER ENDPOINTS
# ================================

# Upload a receipt for parsing
function upload_receipt() {
  if [ -z "$1" ]; then
    echo -e "${RED}File path is required${NC}"
    return 1
  fi
  
  echo -e "${BLUE}Uploading receipt for parsing: $1...${NC}"
  
  # Get content type based on file extension
  CONTENT_TYPE=""
  if [[ "$1" == *.jpg ]] || [[ "$1" == *.jpeg ]]; then
    CONTENT_TYPE="image/jpeg"
  elif [[ "$1" == *.png ]]; then
    CONTENT_TYPE="image/png"
  elif [[ "$1" == *.pdf ]]; then
    CONTENT_TYPE="application/pdf"
  elif [[ "$1" == *.tiff ]] || [[ "$1" == *.tif ]]; then
    CONTENT_TYPE="image/tiff"
  else
    echo -e "${RED}Unsupported file type. Please use JPG, PNG, PDF, or TIFF.${NC}"
    return 1
  fi
  
  # Upload the file
  UPLOAD_RESPONSE=$(curl -s -X POST "$API_URL/parser/parse/" \
    -H "Authorization: Bearer $ACCESS_TOKEN" \
    -H "Content-Type: multipart/form-data" \
    -F "file=@$1;type=$CONTENT_TYPE")

  echo "$UPLOAD_RESPONSE"
  
  echo "$UPLOAD_RESPONSE" | jq
  
  # Extract job ID
  JOB_ID=$(echo "$UPLOAD_RESPONSE" | grep -o '"id":"[^"]*' | cut -d'"' -f4)
  
  if [ -n "$JOB_ID" ]; then
    echo -e "${GREEN}Upload successful! Job ID: $JOB_ID${NC}"
    export JOB_ID=$JOB_ID
  else
    echo -e "${RED}Upload failed or couldn't extract job ID${NC}"
  fi
}

# Check job status
function check_job_status() {
  JOB_ID=${1:-$JOB_ID}
  
  if [ -z "$JOB_ID" ]; then
    echo -e "${RED}Job ID is required${NC}"
    return 1
  fi
  
  echo -e "${BLUE}Checking status of job $JOB_ID...${NC}"
  
  curl -s -X GET "$API_URL/parser/status/$JOB_ID/" \
    -H "Authorization: Bearer $ACCESS_TOKEN" \
    -H "Content-Type: application/json" | jq
}

# Confirm parsed receipt data
function confirm_job() {
  JOB_ID=${1:-$JOB_ID}
  
  if [ -z "$JOB_ID" ]; then
    echo -e "${RED}Job ID is required${NC}"
    return 1
  fi
  
  echo -e "${BLUE}Confirming job $JOB_ID...${NC}"
  
  curl -s -X POST "$API_URL/parser/confirm/$JOB_ID/" \
    -H "Authorization: Bearer $ACCESS_TOKEN" \
    -H "Content-Type: application/json" | jq
}

# Edit parsed receipt data before confirming
function edit_job_data() {
  JOB_ID=${1:-$JOB_ID}
  
  if [ -z "$JOB_ID" ]; then
    echo -e "${RED}Job ID is required${NC}"
    return 1
  fi
  
  echo -e "${BLUE}Editing data for job $JOB_ID...${NC}"
  
  curl -s -X PUT "$API_URL/parser/edit/$JOB_ID/" \
    -H "Authorization: Bearer $ACCESS_TOKEN" \
    -H "Content-Type: application/json" \
    -d '{
      "merchant_name": "Corrected Store Name",
      "total_amount": 99.99,
      "cost_items": [
        {
          "item_name": "Item 1",
          "unit_price": 49.99,
          "quantity": 2
        }
      ]
    }' | jq
}

# Discard a parsing job
function discard_job() {
  JOB_ID=${1:-$JOB_ID}
  
  if [ -z "$JOB_ID" ]; then
    echo -e "${RED}Job ID is required${NC}"
    return 1
  fi
  
  echo -e "${BLUE}Discarding job $JOB_ID...${NC}"
  
  curl -s -X POST "$API_URL/parser/discard/$JOB_ID/" \
    -H "Authorization: Bearer $ACCESS_TOKEN" \
    -H "Content-Type: application/json" | jq
}

# Register a new user with all required fields
function register() {
  # Check for required parameters
  if [ -z "$1" ] || [ -z "$2" ]; then
    echo -e "${RED}Email and password are required${NC}"
    echo "Usage: register EMAIL PASSWORD [FIRST_NAME] [LAST_NAME] [DEPARTMENT] [POSITION] [MANAGER_EMAIL]"
    return 1
  fi
  
  # Check if user is already logged in
  if [ -n "$ACCESS_TOKEN" ]; then
    echo -e "${YELLOW}Warning: You are already logged in with a valid token.${NC}"
    echo -e "Proceeding will log you out of your current session."
    echo -n "Continue with registration? (y/n): "
    read -r CONTINUE
    # Make this work for both bash and zsh
    if [[ "$CONTINUE" != "y" && "$CONTINUE" != "Y" ]]; then
      echo -e "${BLUE}Registration cancelled.${NC}"
      return 0
    fi
    echo -e "${BLUE}Continuing with registration. Your current session will be terminated.${NC}"
  fi
  
  # Set optional parameters with defaults
  EMAIL=$1
  PASSWORD=$2
  FIRST_NAME=${3:-"Test"}
  LAST_NAME=${4:-"User"}
  DEPARTMENT=${5:-"Testing"}
  POSITION=${6:-"Tester"}
  MANAGER=${7:-""}
  
  # Build the manager JSON field only if provided
  MANAGER_JSON=""
  if [ -n "$MANAGER" ]; then
    MANAGER_JSON='"manager": "'$MANAGER'",'
  fi
  
  echo -e "${BLUE}Registering a new user: $EMAIL...${NC}"
  
  # Set up curl command and headers
  HEADERS=("-H" "Content-Type: application/json")
  
  # Add authorization header if already logged in
  if [ -n "$ACCESS_TOKEN" ]; then
    HEADERS+=("-H" "Authorization: Bearer $ACCESS_TOKEN")
  fi
  
  # JSON data with proper escaping for both bash and zsh
  JSON_DATA='{
    "email": "'$EMAIL'",
    "password": "'$PASSWORD'",
    "password2": "'$PASSWORD'",
    "first_name": "'$FIRST_NAME'",
    "last_name": "'$LAST_NAME'",
    "department": "'$DEPARTMENT'",
    "position": "'$POSITION'",
    '$MANAGER_JSON'
    "action": "register"
  }'

  echo curl -s -X POST $API_URL/auth/login/ "${HEADERS[@]}" -d "$JSON_DATA"
  
  # Execute the curl command
  REGISTER_RESPONSE=$(curl -s -X POST $API_URL/auth/register/ "${HEADERS[@]}" -d "$JSON_DATA")
  
  # Extract tokens if registration successful
  ACCESS_TOKEN=$(echo "$REGISTER_RESPONSE" | grep -o '"access":"[^"]*' | cut -d'"' -f4)
  REFRESH_TOKEN=$(echo "$REGISTER_RESPONSE" | grep -o '"refresh":"[^"]*' | cut -d'"' -f4)
  
  if [ -z "$ACCESS_TOKEN" ] || [ "$ACCESS_TOKEN" = "null" ]; then
    echo -e "${RED}Registration failed.${NC}"
    echo "Response: $REGISTER_RESPONSE"
    return 1
  fi
  
  echo -e "${GREEN}Registration successful!${NC}"
  echo "User $EMAIL created"
  echo "Access Token: $ACCESS_TOKEN"
  echo "Refresh Token: $REFRESH_TOKEN"
  
  # Save tokens to environment variables
  export ACCESS_TOKEN=$ACCESS_TOKEN
  export REFRESH_TOKEN=$REFRESH_TOKEN
  
  return 0
}

# ================================
# USAGE EXAMPLES
# ================================

echo -e "${YELLOW}Available commands:${NC}"
echo "login EMAIL PASSWORD - Get authentication tokens"
echo "register EMAIL PASSWORD [FIRST_NAME] [LAST_NAME] [DEPARTMENT] [POSITION] [MANAGER_EMAIL] - Register a new user"
echo "refresh_token - Refresh the access token"
echo "list_receipts - Show all your receipts"
echo "get_receipt ID - Show a specific receipt"
echo "create_receipt - Create a new receipt"
echo "update_receipt ID - Update a receipt"
echo "delete_receipt ID - Delete a receipt"
echo "export_receipts [FORMAT] - Export receipts (json or csv)"
echo "upload_receipt FILE_PATH - Upload and parse a receipt"
echo "check_job_status [JOB_ID] - Check status of parsing job"
echo "edit_job_data [JOB_ID] - Edit data before confirming"
echo "confirm_job [JOB_ID] - Confirm parsed data"
echo "discard_job [JOB_ID] - Discard a parsing job"

# To use this script, source it first:
# For bash: source ./curl.sh
# For zsh:  source ./curl.sh  OR  . ./curl.sh
# 
# Then run the commands:
# login "your@email.com" "your_password"
# list_receipts
# etc.

