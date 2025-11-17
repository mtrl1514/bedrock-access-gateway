# Azure AI Search API 개별 테스트 명령어

## 🔧 기본 설정

```bash
# 환경 변수 설정
BASE_URL="http://localhost:8000"
API_KEY="bedrock"
API_VERSION="2024-07-01"
INDEX_NAME="azure_index"
```

## 1. ⚕️ Health Check

```bash
curl -X GET "$BASE_URL/health"
```

**PowerShell:**
```powershell
Invoke-RestMethod -Uri "http://localhost:8000/health" -Method GET
```

---

## 2. 📋 인덱스 관리

### 2.1 인덱스 생성

```bash
curl -X POST "http://localhost:8000/search/indexes/azure_index?api-version=2024-07-01" \
  -H "Content-Type: application/json" \
  -H "api-key: bedrock" \
  -d @test/azure_search_create_index.json
```

**PowerShell:**
```powershell
$headers = @{
    "Content-Type" = "application/json"
    "api-key" = "bedrock"
}
$body = Get-Content "test/azure_search_create_index.json" -Raw
Invoke-RestMethod -Uri "http://localhost:8000/search/indexes/azure_index?api-version=2024-07-01" -Method POST -Headers $headers -Body $body
```

### 2.2 인덱스 목록 조회

```bash
curl -X GET "http://localhost:8000/search/indexes?api-version=2024-07-01" \
  -H "api-key: bedrock"
```

**PowerShell:**
```powershell
$headers = @{ "api-key" = "bedrock" }
Invoke-RestMethod -Uri "http://localhost:8000/search/indexes?api-version=2024-07-01" -Method GET -Headers $headers
```

### 2.3 특정 인덱스 조회

```bash
curl -X GET "http://localhost:8000/search/indexes/azure_index?api-version=2024-07-01" \
  -H "api-key: bedrock"
```

**PowerShell:**
```powershell
$headers = @{ "api-key" = "bedrock" }
Invoke-RestMethod -Uri "http://localhost:8000/search/indexes/azure_index?api-version=2024-07-01" -Method GET -Headers $headers
```

### 2.4 인덱스 삭제

```bash
curl -X DELETE "http://localhost:8000/search/indexes/azure_index?api-version=2024-07-01" \
  -H "api-key: bedrock"
```

**PowerShell:**
```powershell
$headers = @{ "api-key" = "bedrock" }
Invoke-RestMethod -Uri "http://localhost:8000/search/indexes/azure_index?api-version=2024-07-01" -Method DELETE -Headers $headers
```

---

## 3. 📄 문서 관리

### 3.1 문서 인덱싱

```bash
curl -X POST "http://localhost:8000/search/indexes/azure_index/docs/index?api-version=2024-07-01" \
  -H "Content-Type: application/json" \
  -H "api-key: bedrock" \
  -d @test/azure_search_index_documents.json
```

**PowerShell:**
```powershell
$headers = @{
    "Content-Type" = "application/json"
    "api-key" = "bedrock"
}
$body = Get-Content "test/azure_search_index_documents.json" -Raw
Invoke-RestMethod -Uri "http://localhost:8000/search/indexes/azure_index/docs/index?api-version=2024-07-01" -Method POST -Headers $headers -Body $body
```

### 3.2 문서 개수 조회

```bash
curl -X GET "http://localhost:8000/search/indexes/azure_index/docs/\$count?api-version=2024-07-01" \
  -H "api-key: bedrock"
```

**PowerShell:**
```powershell
$headers = @{ "api-key" = "bedrock" }
Invoke-RestMethod -Uri "http://localhost:8000/search/indexes/azure_index/docs/`$count?api-version=2024-07-01" -Method GET -Headers $headers
```

---

## 4. 🔍 검색 테스트

### 4.1 간단한 텍스트 검색 (POST)

```bash
curl -X POST "http://localhost:8000/search/indexes/azure_index/docs/search?api-version=2024-07-01" \
  -H "Content-Type: application/json" \
  -H "api-key: bedrock" \
  -d @test/azure_search_simple_query.json
```

**PowerShell:**
```powershell
$headers = @{
    "Content-Type" = "application/json"
    "api-key" = "bedrock"
}
$body = Get-Content "test/azure_search_simple_query.json" -Raw
Invoke-RestMethod -Uri "http://localhost:8000/search/indexes/azure_index/docs/search?api-version=2024-07-01" -Method POST -Headers $headers -Body $body
```

### 4.2 간단한 텍스트 검색 (GET)

```bash
curl -X GET "http://localhost:8000/search/indexes/azure_index/docs/search?api-version=2024-07-01&search=AI&top=5" \
  -H "api-key: bedrock"
```

**PowerShell:**
```powershell
$headers = @{ "api-key" = "bedrock" }
Invoke-RestMethod -Uri "http://localhost:8000/search/indexes/azure_index/docs/search?api-version=2024-07-01&search=AI&top=5" -Method GET -Headers $headers
```

### 4.3 필터링된 검색

```bash
curl -X POST "http://localhost:8000/search/indexes/azure_index/docs/search?api-version=2024-07-01" \
  -H "Content-Type: application/json" \
  -H "api-key: bedrock" \
  -d @test/azure_search_filtered_query.json
```

**PowerShell:**
```powershell
$headers = @{
    "Content-Type" = "application/json"
    "api-key" = "bedrock"
}
$body = Get-Content "test/azure_search_filtered_query.json" -Raw
Invoke-RestMethod -Uri "http://localhost:8000/search/indexes/azure_index/docs/search?api-version=2024-07-01" -Method POST -Headers $headers -Body $body
```

### 4.4 벡터 검색

```bash
curl -X POST "http://localhost:8000/search/indexes/azure_index/docs/search?api-version=2024-07-01" \
  -H "Content-Type: application/json" \
  -H "api-key: bedrock" \
  -d @test/azure_search_vector_query.json
```

**PowerShell:**
```powershell
$headers = @{
    "Content-Type" = "application/json"
    "api-key" = "bedrock"
}
$body = Get-Content "test/azure_search_vector_query.json" -Raw
Invoke-RestMethod -Uri "http://localhost:8000/search/indexes/azure_index/docs/search?api-version=2024-07-01" -Method POST -Headers $headers -Body $body
```

### 4.5 하이브리드 검색 (텍스트 + 벡터)

```bash
curl -X POST "http://localhost:8000/search/indexes/azure_index/docs/search?api-version=2024-07-01" \
  -H "Content-Type: application/json" \
  -H "api-key: bedrock" \
  -d @test/azure_search_hybrid_query.json
```

**PowerShell:**
```powershell
$headers = @{
    "Content-Type" = "application/json"
    "api-key" = "bedrock"
}
$body = Get-Content "test/azure_search_hybrid_query.json" -Raw
Invoke-RestMethod -Uri "http://localhost:8000/search/indexes/azure_index/docs/search?api-version=2024-07-01" -Method POST -Headers $headers -Body $body
```

---

## 5. 🧪 직접 테스트용 간단한 명령어

### 5.1 최소한의 검색 (인라인 JSON)

```bash
curl -X POST "http://localhost:8000/search/indexes/azure_index/docs/search?api-version=2024-07-01" \
  -H "Content-Type: application/json" \
  -H "api-key: bedrock" \
  -d '{"search": "AI", "top": 3}'
```

**PowerShell:**
```powershell
$headers = @{
    "Content-Type" = "application/json"
    "api-key" = "bedrock"
}
$body = '{"search": "AI", "top": 3}'
Invoke-RestMethod -Uri "http://localhost:8000/search/indexes/azure_index/docs/search?api-version=2024-07-01" -Method POST -Headers $headers -Body $body
```

### 5.2 전체 문서 조회

```bash
curl -X POST "http://localhost:8000/search/indexes/azure_index/docs/search?api-version=2024-07-01" \
  -H "Content-Type: application/json" \
  -H "api-key: bedrock" \
  -d '{"search": "*", "top": 10}'
```

**PowerShell:**
```powershell
$headers = @{
    "Content-Type" = "application/json"
    "api-key" = "bedrock"
}
$body = '{"search": "*", "top": 10}'
Invoke-RestMethod -Uri "http://localhost:8000/search/indexes/azure_index/docs/search?api-version=2024-07-01" -Method POST -Headers $headers -Body $body
```

### 5.3 특정 필드만 조회

```bash
curl -X POST "http://localhost:8000/search/indexes/azure_index/docs/search?api-version=2024-07-01" \
  -H "Content-Type: application/json" \
  -H "api-key: bedrock" \
  -d '{"search": "*", "select": "id,content", "top": 5}'
```

**PowerShell:**
```powershell
$headers = @{
    "Content-Type" = "application/json"
    "api-key" = "bedrock"
}
$body = '{"search": "*", "select": "id,content", "top": 5}'
Invoke-RestMethod -Uri "http://localhost:8000/search/indexes/azure_index/docs/search?api-version=2024-07-01" -Method POST -Headers $headers -Body $body
```

---

## 6. 🔧 디버깅용 명령어

### 6.1 서버 로그에서 에러 확인

서버 터미널에서 실시간 로그를 확인하면서 위 명령어들을 실행하세요.

### 6.2 응답 헤더 포함해서 확인

```bash
curl -i -X GET "http://localhost:8000/search/indexes/azure_index/docs/\$count?api-version=2024-07-01" \
  -H "api-key: bedrock"
```

### 6.3 상세한 에러 정보 확인

```bash
curl -X POST "http://localhost:8000/search/indexes/azure_index/docs/search?api-version=2024-07-01" \
  -H "Content-Type: application/json" \
  -H "api-key: bedrock" \
  -d '{"search": "AI", "top": 3}' \
  -w "\nHTTP Status: %{http_code}\nResponse Time: %{time_total}s\n"
```

---

## 7. 📝 일괄 테스트 스크립트 (Bash)

```bash
#!/bin/bash
# 전체 테스트 스크립트

BASE_URL="http://localhost:8000"
API_KEY="bedrock"  
API_VERSION="2024-07-01"
INDEX_NAME="azure_index"

echo "=== 1. Health Check ==="
curl -s -X GET "$BASE_URL/health" | jq .

echo -e "\n=== 2. Index Creation ==="
curl -s -X POST "$BASE_URL/search/indexes/$INDEX_NAME?api-version=$API_VERSION" \
  -H "Content-Type: application/json" \
  -H "api-key: $API_KEY" \
  -d @test/azure_search_create_index.json | jq .

echo -e "\n=== 3. Document Indexing ==="  
curl -s -X POST "$BASE_URL/search/indexes/$INDEX_NAME/docs/index?api-version=$API_VERSION" \
  -H "Content-Type: application/json" \
  -H "api-key: $API_KEY" \
  -d @test/azure_search_index_documents.json | jq .

echo -e "\n=== 4. Document Count ==="
curl -s -X GET "$BASE_URL/search/indexes/$INDEX_NAME/docs/\$count?api-version=$API_VERSION" \
  -H "api-key: $API_KEY"

echo -e "\n=== 5. Simple Search ==="
curl -s -X POST "$BASE_URL/search/indexes/$INDEX_NAME/docs/search?api-version=$API_VERSION" \
  -H "Content-Type: application/json" \
  -H "api-key: $API_KEY" \
  -d '{"search": "AI", "top": 3}' | jq .
```

---

## 8. 📝 일괄 테스트 스크립트 (PowerShell)

```powershell
# 전체 테스트 스크립트

$BaseUrl = "http://localhost:8000"
$ApiKey = "bedrock"
$ApiVersion = "2024-07-01"
$IndexName = "azure_index"

$headers = @{
    "Content-Type" = "application/json"
    "api-key" = $ApiKey
}

Write-Host "=== 1. Health Check ===" -ForegroundColor Yellow
try {
    $result = Invoke-RestMethod -Uri "$BaseUrl/health" -Method GET
    Write-Host ($result | ConvertTo-Json) -ForegroundColor Green
} catch {
    Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host "`n=== 2. Document Count ===" -ForegroundColor Yellow
try {
    $result = Invoke-RestMethod -Uri "$BaseUrl/search/indexes/$IndexName/docs/`$count?api-version=$ApiVersion" -Method GET -Headers @{"api-key"=$ApiKey}
    Write-Host "Document Count: $result" -ForegroundColor Green
} catch {
    Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host "`n=== 3. Simple Search ===" -ForegroundColor Yellow
try {
    $body = '{"search": "AI", "top": 3}'
    $result = Invoke-RestMethod -Uri "$BaseUrl/search/indexes/$IndexName/docs/search?api-version=$ApiVersion" -Method POST -Headers $headers -Body $body
    Write-Host ($result | ConvertTo-Json -Depth 5) -ForegroundColor Green
} catch {
    Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Red
}
```

이제 각 기능을 개별적으로 테스트할 수 있습니다! 🚀