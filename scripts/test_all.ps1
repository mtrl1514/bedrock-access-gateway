# PowerShell Test Script for Bedrock Access Gateway
# Usage: .\scripts\test_all.ps1

Write-Host "🚀 Starting Bedrock Access Gateway Tests..." -ForegroundColor Green

$BASE_URL = "http://localhost:8000"
$API_KEY = "bedrock"

# Test results tracking
$PassCount = 0
$FailCount = 0
$TotalCount = 0

function Test-API {
    param(
        [string]$TestName,
        [string]$Url,
        [string]$Method = "GET",
        [string]$DataFile = $null
    )
    
    Write-Host "`n📋 Testing: $TestName" -ForegroundColor Yellow
    $script:TotalCount++
    
    try {
        $startTime = Get-Date
        
        if ($Method -eq "GET") {
            $response = curl.exe -s -X GET "$Url" -H "api-key: $API_KEY"
        } else {
            $response = curl.exe -s -X POST "$Url" -H "Content-Type: application/json" -H "api-key: $API_KEY" --data-binary "@$DataFile"
        }
        
        $endTime = Get-Date
        $duration = ($endTime - $startTime).TotalMilliseconds
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ PASS - $TestName ($([math]::Round($duration))ms)" -ForegroundColor Green
            $script:PassCount++
        } else {
            Write-Host "❌ FAIL - $TestName" -ForegroundColor Red
            Write-Host "   Response: $response" -ForegroundColor Gray
            $script:FailCount++
        }
    }
    catch {
        Write-Host "❌ ERROR - $TestName" -ForegroundColor Red
        Write-Host "   Error: $($_.Exception.Message)" -ForegroundColor Gray
        $script:FailCount++
    }
}

# Check if test files exist
if (-not (Test-Path "test\test_chat.json")) {
    Write-Host "❌ Test file 'test\test_chat.json' not found!" -ForegroundColor Red
    exit 1
}
if (-not (Test-Path "test\test_text_embedding.json")) {
    Write-Host "❌ Test file 'test\test_text_embedding.json' not found!" -ForegroundColor Red
    exit 1
}
if (-not (Test-Path "test\test_image_embedding.json")) {
    Write-Host "❌ Test file 'test\test_image_embedding.json' not found!" -ForegroundColor Red
    exit 1
}

Write-Host "📂 Using test directory: test\" -ForegroundColor Cyan
Write-Host "🌐 API Base URL: $BASE_URL" -ForegroundColor Cyan

# Test 1: Health Check
Test-API -TestName "Health Check" -Url "$BASE_URL/health"

# Test 2: Chat API (GPT-4)
Test-API -TestName "Chat API (GPT-4)" -Url "$BASE_URL/openai/deployments/gpt-4/chat/completions?api-version=2024-02-15-preview" -Method "POST" -DataFile "test\test_chat.json"

# Test 3: Text Embedding (Azure Style)
Test-API -TestName "Text Embedding (Azure)" -Url "$BASE_URL/openai/deployments/text-embedding-ada-002/embeddings?api-version=2024-02-15-preview" -Method "POST" -DataFile "test\test_text_embedding.json"

# Test 4: Image Embedding (Titan)
Test-API -TestName "Image Embedding (Titan)" -Url "$BASE_URL/openai/deployments/vision-embedding/embeddings?api-version=2024-05-01-preview" -Method "POST" -DataFile "test\test_image_embedding.json"

# Test 5: Model List
Test-API -TestName "Model List" -Url "$BASE_URL/v1/models"

# Summary
Write-Host "`n📊 Test Summary:" -ForegroundColor Cyan
Write-Host "================" -ForegroundColor Cyan
Write-Host "✅ Passed: $PassCount" -ForegroundColor Green
Write-Host "❌ Failed: $FailCount" -ForegroundColor Red
Write-Host "📝 Total: $TotalCount" -ForegroundColor White

# Final result
if ($FailCount -eq 0) {
    Write-Host "`n🎉 All tests passed!" -ForegroundColor Green
    exit 0
} else {
    Write-Host "`n❌ Some tests failed!" -ForegroundColor Red
    exit 1
}