#!/bin/bash
# Bash Test Script for Bedrock Access Gateway
# Usage: ./scripts/test_all.sh

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
BASE_URL="http://localhost:8000"
API_KEY="bedrock"
TEST_DIR="test"

# Test counters
PASS_COUNT=0
FAIL_COUNT=0
TOTAL_COUNT=0

echo -e "${GREEN}🚀 Starting Bedrock Access Gateway Tests...${NC}"

# Function to run a test
run_test() {
    local test_name="$1"
    local method="$2"
    local url="$3"
    local data_file="$4"
    local headers="$5"
    
    echo -e "\n${YELLOW}📋 Testing: $test_name${NC}"
    ((TOTAL_COUNT++))
    
    local start_time=$(date +%s%N)
    local exit_code=0
    
    if [ "$method" = "GET" ]; then
        response=$(curl -s -w "\n%{http_code}" $headers "$url" 2>/dev/null) || exit_code=$?
    else
        response=$(curl -s -w "\n%{http_code}" -X POST $headers --data-binary "@$data_file" "$url" 2>/dev/null) || exit_code=$?
    fi
    
    local end_time=$(date +%s%N)
    local duration=$(( (end_time - start_time) / 1000000 )) # Convert to milliseconds
    
    # Extract HTTP status code from response
    local http_code=$(echo "$response" | tail -n1)
    local response_body=$(echo "$response" | head -n -1)
    
    if [ $exit_code -eq 0 ] && [[ "$http_code" =~ ^2[0-9][0-9]$ ]]; then
        echo -e "${GREEN}✅ PASS - $test_name (${duration}ms)${NC}"
        ((PASS_COUNT++))
    else
        echo -e "${RED}❌ FAIL - $test_name (HTTP: $http_code)${NC}"
        echo -e "${RED}   Response: $response_body${NC}"
        ((FAIL_COUNT++))
    fi
}

# Check if test directory exists
if [ ! -d "$TEST_DIR" ]; then
    echo -e "${RED}❌ Test directory '$TEST_DIR' not found!${NC}"
    exit 1
fi

# Check if test files exist
for file in "$TEST_DIR/test_chat.json" "$TEST_DIR/test_text_embedding.json" "$TEST_DIR/test_image_embedding.json"; do
    if [ ! -f "$file" ]; then
        echo -e "${RED}❌ Test file '$file' not found!${NC}"
        exit 1
    fi
done

echo -e "${CYAN}📂 Using test directory: $TEST_DIR${NC}"
echo -e "${CYAN}🌐 API Base URL: $BASE_URL${NC}"

# Test 1: Health Check
run_test "Health Check" "GET" "$BASE_URL/health" "" ""

# Test 2: Chat API (GPT-4)
run_test "Chat API (GPT-4)" "POST" \
    "$BASE_URL/openai/deployments/gpt-4/chat/completions?api-version=2024-02-15-preview" \
    "$TEST_DIR/test_chat.json" \
    "-H 'Content-Type: application/json' -H 'api-key: $API_KEY'"

# Test 3: Chat API (GPT-3.5)
run_test "Chat API (GPT-3.5)" "POST" \
    "$BASE_URL/openai/deployments/gpt-35-turbo/chat/completions?api-version=2024-02-15-preview" \
    "$TEST_DIR/test_chat.json" \
    "-H 'Content-Type: application/json' -H 'api-key: $API_KEY'"

# Test 4: Text Embedding (Azure Style)
run_test "Text Embedding (Azure)" "POST" \
    "$BASE_URL/openai/deployments/text-embedding-ada-002/embeddings?api-version=2024-02-15-preview" \
    "$TEST_DIR/test_text_embedding.json" \
    "-H 'Content-Type: application/json' -H 'api-key: $API_KEY'"

# Test 5: Image Embedding (Titan)
run_test "Image Embedding (Titan)" "POST" \
    "$BASE_URL/openai/deployments/vision-embedding/embeddings?api-version=2024-05-01-preview" \
    "$TEST_DIR/test_image_embedding.json" \
    "-H 'Content-Type: application/json' -H 'api-key: $API_KEY'"

# Test 6: Image Embedding (TwelveLabs)
run_test "Image Embedding (TwelveLabs)" "POST" \
    "$BASE_URL/openai/deployments/vision-embedding/embeddings?api-version=2024-02-15-preview" \
    "$TEST_DIR/test_image_embedding.json" \
    "-H 'Content-Type: application/json' -H 'api-key: $API_KEY'"

# Test 7: Model List
run_test "Model List" "GET" \
    "$BASE_URL/v1/models" \
    "" \
    "-H 'api-key: $API_KEY'"

# Test 8: Direct Bedrock Model
run_test "Direct Bedrock Chat" "POST" \
    "$BASE_URL/api/v1/chat/completions" \
    "$TEST_DIR/test_chat.json" \
    "-H 'Content-Type: application/json' -H 'Authorization: Bearer $API_KEY'"

# Summary
echo -e "\n${CYAN}📊 Test Summary:${NC}"
echo -e "${CYAN}================${NC}"
echo -e "${GREEN}✅ Passed: $PASS_COUNT${NC}"
echo -e "${RED}❌ Failed: $FAIL_COUNT${NC}"
echo -e "${BLUE}📝 Total: $TOTAL_COUNT${NC}"

# Final result
if [ $FAIL_COUNT -eq 0 ]; then
    echo -e "\n${GREEN}🎉 All tests passed!${NC}"
    exit 0
else
    echo -e "\n${RED}❌ Some tests failed!${NC}"
    exit 1
fi