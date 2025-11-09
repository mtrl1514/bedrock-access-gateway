# Testing Guide

This document provides comprehensive testing instructions for the Bedrock Access Gateway.

## Quick Test Commands

All test JSON files are located in the `test/` directory.

### Health Check
```bash
curl http://localhost:8000/health
```

## Chat API Testing

### Azure API Style (Recommended)
```bash
# GPT-4 → Claude 4.5 Sonnet (ap-northeast-1)
curl -X POST "http://localhost:8000/openai/deployments/gpt-4/chat/completions?api-version=2024-02-15-preview" \
  -H "Content-Type: application/json" \
  -H "api-key: bedrock" \
  --data-binary "@test/test_chat.json"

# GPT-3.5 → Claude 3 Sonnet (ap-northeast-1)
curl -X POST "http://localhost:8000/openai/deployments/gpt-35-turbo/chat/completions?api-version=2024-02-15-preview" \
  -H "Content-Type: application/json" \
  -H "api-key: bedrock" \
  --data-binary "@test/test_chat.json"
```

### Direct Bedrock Models
```bash
# Claude 3.5 Sonnet
curl -X POST "http://localhost:8000/api/v1/chat/completions" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer bedrock" \
  --data-binary "@test/test_chat.json"
```

### Streaming Chat
```bash
# Add stream=true parameter
curl -X POST "http://localhost:8000/openai/deployments/gpt-4/chat/completions?api-version=2024-02-15-preview&stream=true" \
  -H "Content-Type: application/json" \
  -H "api-key: bedrock" \
  --data-binary "@test/test_chat.json"
```

## Text Embeddings Testing

### Azure API Style
```bash
# text-embedding-ada-002 → Amazon Titan Text (ap-northeast-1)
curl -X POST "http://localhost:8000/openai/deployments/text-embedding-ada-002/embeddings?api-version=2024-02-15-preview" \
  -H "Content-Type: application/json" \
  -H "api-key: bedrock" \
  --data-binary "@test/test_text_embedding.json"
```

### Direct Bedrock Models
```bash
# Amazon Titan Text Embeddings V1
curl -X POST "http://localhost:8000/api/v1/embeddings" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer bedrock" \
  --data-binary "@test/test_text_embedding.json"

# Cohere English Embeddings
curl -X POST "http://localhost:8000/openai/deployments/cohere.embed-english-v3/embeddings" \
  -H "Content-Type: application/json" \
  -H "api-key: bedrock" \
  --data-binary "@test/test_text_embedding.json"
```

## Vision Embeddings Testing

### Azure API Style
```bash
# Amazon Titan Image Embeddings (us-east-1)
curl -X POST "http://localhost:8000/openai/deployments/vision-embedding/embeddings?api-version=2024-05-01-preview" \
  -H "Content-Type: application/json" \
  -H "api-key: bedrock" \
  --data-binary "@test/test_image_embedding.json"

# TwelveLabs Marengo Embeddings (us-east-1)
curl -X POST "http://localhost:8000/openai/deployments/vision-embedding/embeddings?api-version=2024-02-15-preview" \
  -H "Content-Type: application/json" \
  -H "api-key: bedrock" \
  --data-binary "@test/test_image_embedding.json"
```

### Direct Bedrock Models
```bash
# Amazon Titan Image Embeddings
curl -X POST "http://localhost:8000/openai/deployments/amazon.titan-embed-image-v1/embeddings" \
  -H "Content-Type: application/json" \
  -H "api-key: bedrock" \
  --data-binary "@test/test_image_embedding.json"

# TwelveLabs Marengo
curl -X POST "http://localhost:8000/openai/deployments/twelvelabs.marengo-embed-3-0-v1:0/embeddings" \
  -H "Content-Type: application/json" \
  -H "api-key: bedrock" \
  --data-binary "@test/test_image_embedding.json"
```

## Model Information

### List Available Models
```bash
# Original API
curl -X GET "http://localhost:8000/v1/models" \
  -H "api-key: bedrock"

# Azure style
curl -X GET "http://localhost:8000/openai/deployments?api-version=2024-02-15-preview" \
  -H "api-key: bedrock"
```

## Test Data Files

### test/test_chat.json
```json
{
  "messages": [
    {"role": "user", "content": "Hello! Can you tell me what is AWS Bedrock?"}
  ],
  "max_tokens": 150,
  "temperature": 0.7
}
```

### test/test_text_embedding.json
```json
{
  "input": "Hello world, this is a test sentence for text embedding."
}
```

### test/test_image_embedding.json
```json
{
  "input": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="
}
```

## Model Mapping Reference

| Azure Model | Bedrock Model | Region | Type |
|-------------|---------------|---------|------|
| gpt-4 | global.anthropic.claude-sonnet-4-5-20250929-v1:0 | ap-northeast-1 | Chat |
| gpt-35-turbo | apac.anthropic.claude-3-sonnet-20240229-v1:0 | ap-northeast-1 | Chat |
| text-embedding-ada-002 | amazon.titan-embed-text-v1 | ap-northeast-1 | Text Embedding |
| vision-embedding (2024-05-01) | amazon.titan-embed-image-v1 | us-east-1 | Image Embedding |
| vision-embedding (2024-02-15) | twelvelabs.marengo-embed-3-0-v1:0 | us-east-1 | Image Embedding |

## Environment Configuration

### Required Environment Variables
```bash
export AWS_REGION=ap-northeast-1           # Default region for chat/text
export AWS_REGION_VISION=us-east-1         # Region for vision embeddings
export DEBUG=true                          # Enable debug logging
```

### AWS Permissions Required
```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "bedrock:InvokeModel",
                "bedrock:InvokeModelWithResponseStream",
                "bedrock:ListFoundationModels",
                "bedrock:GetFoundationModel"
            ],
            "Resource": [
                "arn:aws:bedrock:*::foundation-model/anthropic.*",
                "arn:aws:bedrock:*::foundation-model/amazon.*",
                "arn:aws:bedrock:*::foundation-model/cohere.*",
                "arn:aws:bedrock:*::foundation-model/twelvelabs.*"
            ]
        },
        {
            "Effect": "Allow",
            "Action": [
                "aws-marketplace:ViewSubscriptions"
            ],
            "Resource": "*"
        }
    ]
}
```

## Expected Responses

### Successful Chat Response
```json
{
  "id": "chatcmpl-8032b091",
  "created": 1762662143,
  "model": "apac.anthropic.claude-sonnet-4-20250514-v1:0",
  "choices": [{
    "index": 0,
    "finish_reason": "length",
    "message": {
      "role": "assistant",
      "content": "Hello! AWS Bedrock is Amazon's fully managed service..."
    }
  }],
  "usage": {
    "prompt_tokens": 20,
    "completion_tokens": 150,
    "total_tokens": 170
  }
}
```

### Successful Embedding Response
```json
{
  "object": "list",
  "data": [{
    "object": "embedding",
    "embedding": [0.1923828125, -0.0615234375, ...],
    "index": 0
  }],
  "model": "amazon.titan-embed-text-v1",
  "usage": {
    "prompt_tokens": 12,
    "total_tokens": 12
  }
}
```

## Troubleshooting

### Common Issues

1. **403 Access Denied**: Check AWS permissions and model access in Bedrock console
2. **Invalid model identifier**: Ensure model is available in the specified region
3. **Timeout errors**: Check network connectivity and region settings
4. **JSON decode errors**: Verify test file paths and JSON formatting

### Debug Tips

1. **Enable Debug Logging**:
   ```bash
   export DEBUG=true
   ```

2. **Check Logs**: Monitor server logs for detailed error information

3. **Verify Model Access**: Use AWS CLI to confirm model availability:
   ```bash
   aws bedrock list-foundation-models --region ap-northeast-1
   aws bedrock list-foundation-models --region us-east-1
   ```

4. **Test AWS Credentials**:
   ```bash
   aws sts get-caller-identity
   ```

## Automated Testing

### PowerShell Script (Windows)
```powershell
# test_all.ps1
Write-Host "Testing Bedrock Access Gateway..."

# Health check
Write-Host "1. Health Check..."
curl.exe -X GET "http://localhost:8000/health"

# Chat API
Write-Host "2. Chat API..."
curl.exe -X POST "http://localhost:8000/openai/deployments/gpt-4/chat/completions?api-version=2024-02-15-preview" -H "Content-Type: application/json" -H "api-key: bedrock" --data-binary "@test/test_chat.json"

# Text Embedding
Write-Host "3. Text Embedding..."
curl.exe -X POST "http://localhost:8000/openai/deployments/text-embedding-ada-002/embeddings?api-version=2024-02-15-preview" -H "Content-Type: application/json" -H "api-key: bedrock" --data-binary "@test/test_text_embedding.json"

# Image Embedding
Write-Host "4. Image Embedding..."
curl.exe -X POST "http://localhost:8000/openai/deployments/vision-embedding/embeddings?api-version=2024-05-01-preview" -H "Content-Type: application/json" -H "api-key: bedrock" --data-binary "@test/test_image_embedding.json"

Write-Host "Testing completed!"
```

### Bash Script (Linux/Mac)
```bash
#!/bin/bash
# test_all.sh

echo "Testing Bedrock Access Gateway..."

BASE_URL="http://localhost:8000"

echo "1. Health Check..."
curl -X GET "$BASE_URL/health"

echo -e "\n2. Chat API..."
curl -X POST "$BASE_URL/openai/deployments/gpt-4/chat/completions?api-version=2024-02-15-preview" \
  -H "Content-Type: application/json" \
  -H "api-key: bedrock" \
  --data-binary "@test/test_chat.json"

echo -e "\n3. Text Embedding..."
curl -X POST "$BASE_URL/openai/deployments/text-embedding-ada-002/embeddings?api-version=2024-02-15-preview" \
  -H "Content-Type: application/json" \
  -H "api-key: bedrock" \
  --data-binary "@test/test_text_embedding.json"

echo -e "\n4. Image Embedding..."
curl -X POST "$BASE_URL/openai/deployments/vision-embedding/embeddings?api-version=2024-05-01-preview" \
  -H "Content-Type: application/json" \
  -H "api-key: bedrock" \
  --data-binary "@test/test_image_embedding.json"

echo -e "\nTesting completed!"
```

## Performance Testing

### Load Testing with curl
```bash
# Simple load test
for i in {1..10}; do
  echo "Request $i"
  curl -X POST "http://localhost:8000/openai/deployments/gpt-4/chat/completions?api-version=2024-02-15-preview" \
    -H "Content-Type: application/json" \
    -H "api-key: bedrock" \
    --data-binary "@test/test_chat.json" &
done
wait
```

### Using Python for Testing
```python
import asyncio
import aiohttp
import time

async def test_api():
    async with aiohttp.ClientSession() as session:
        start_time = time.time()
        
        async with session.post(
            'http://localhost:8000/openai/deployments/gpt-4/chat/completions?api-version=2024-02-15-preview',
            headers={
                'Content-Type': 'application/json',
                'api-key': 'bedrock'
            },
            json={
                'messages': [{'role': 'user', 'content': 'Hello!'}],
                'max_tokens': 50
            }
        ) as response:
            result = await response.json()
            end_time = time.time()
            
            print(f"Response time: {end_time - start_time:.2f}s")
            print(f"Status: {response.status}")
            return result

# Run test
asyncio.run(test_api())
```