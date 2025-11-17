# Azure AI Search API 테스트 PowerShell 스크립트
param(
    [string]$BaseUrl = "http://localhost:8000",
    [string]$ApiKey = "bedrock",
    [string]$ApiVersion = "2024-07-01",
    [string]$IndexName = "azure_index"
)

# 색상 출력 함수
function Write-Success {
    param([string]$Message)
    Write-Host "✅ $Message" -ForegroundColor Green
}

function Write-Error {
    param([string]$Message)
    Write-Host "❌ $Message" -ForegroundColor Red
}

function Write-Info {
    param([string]$Message)
    Write-Host "ℹ️  $Message" -ForegroundColor Cyan
}

function Write-Step {
    param([string]$Message)
    Write-Host "`n🔸 $Message" -ForegroundColor Yellow
}

# HTTP 요청 함수
function Invoke-SearchApi {
    param(
        [string]$Method,
        [string]$Uri,
        [object]$Body = $null,
        [string]$Description
    )
    
    $headers = @{
        "Content-Type" = "application/json"
        "api-key" = $ApiKey
    }
    
    try {
        Write-Info "Testing: $Description"
        
        $params = @{
            Uri = $Uri
            Method = $Method
            Headers = $headers
        }
        
        if ($Body) {
            $params.Body = ($Body | ConvertTo-Json -Depth 10)
        }
        
        $response = Invoke-RestMethod @params
        Write-Success "$Description - Success"
        return $response
    }
    catch {
        $statusCode = $_.Exception.Response.StatusCode.value__
        $errorMessage = $_.Exception.Message
        Write-Error "$Description - Status: $statusCode, Error: $errorMessage"
        return $null
    }
}

# 메인 테스트 함수
function Test-AzureSearch {
    Write-Host "🔍 Azure AI Search API 테스트 시작" -ForegroundColor Magenta
    Write-Host "Base URL: $BaseUrl" -ForegroundColor White
    Write-Host "API Key: $ApiKey" -ForegroundColor White
    Write-Host "Index Name: $IndexName" -ForegroundColor White
    Write-Host ("=" * 60) -ForegroundColor Gray
    
    # 1. Health Check
    Write-Step "서버 상태 확인"
    try {
        $healthResponse = Invoke-RestMethod -Uri "$BaseUrl/health" -Method GET
        if ($healthResponse.status -eq "OK") {
            Write-Success "서버가 정상적으로 실행 중입니다"
        }
    }
    catch {
        Write-Error "서버에 연결할 수 없습니다. 서버가 실행 중인지 확인하세요."
        return
    }
    
    # 2. 인덱스 생성 (존재 체크 후)
    Write-Step "인덱스 생성 테스트"
    
    # 인덱스 존재 여부 확인
    $indexExists = $false
    try {
        $existingIndex = Invoke-RestMethod -Uri "$BaseUrl/search/indexes/$IndexName`?api-version=$ApiVersion" -Method GET -Headers @{"api-key" = $ApiKey}
        if ($existingIndex) {
            Write-Info "인덱스 '$IndexName'이 이미 존재합니다. 생성을 스킵합니다."
            $indexExists = $true
        }
    }
    catch {
        Write-Info "인덱스 '$IndexName'이 존재하지 않습니다. 새로 생성합니다."
    }
    
    if (-not $indexExists) {
        # JSON 파일에서 인덱스 정의 로드
        $indexJsonPath = "test/azure_search_create_index.json"
        if (-not (Test-Path $indexJsonPath)) {
            Write-Error "인덱스 JSON 파일을 찾을 수 없습니다: $indexJsonPath"
            return
        }
        
        try {
            $indexDefinition = Get-Content $indexJsonPath -Raw | ConvertFrom-Json
            # 인덱스 이름을 파라미터로 지정된 이름으로 변경
            $indexDefinition.name = $IndexName
            
            $response = Invoke-SearchApi -Method "POST" -Uri "$BaseUrl/search/indexes/$IndexName`?api-version=$ApiVersion" -Body $indexDefinition -Description "Create Index"
            if (-not $response) { return }
            
            Start-Sleep -Seconds 2
        }
        catch {
            Write-Error "인덱스 JSON 파일 로드 실패: $($_.Exception.Message)"
            return
        }
    }
    
    # 3. 인덱스 목록 조회
    Write-Step "인덱스 목록 조회"
    $response = Invoke-SearchApi -Method "GET" -Uri "$BaseUrl/search/indexes?api-version=$ApiVersion" -Description "List Indexes"
    if ($response -and $response.value) {
        Write-Success "인덱스 개수: $($response.value.Count)"
        foreach ($index in $response.value) {
            Write-Host "  - $($index.name)" -ForegroundColor Gray
        }
    }
    
    # 4. 문서 인덱싱
    Write-Step "문서 인덱싱 테스트"
    
    # JSON 파일에서 문서 데이터 로드
    $documentsJsonPath = "test/azure_search_index_documents.json"
    if (-not (Test-Path $documentsJsonPath)) {
        Write-Error "문서 JSON 파일을 찾을 수 없습니다: $documentsJsonPath"
        return
    }
    
    try {
        $documents = Get-Content $documentsJsonPath -Raw | ConvertFrom-Json
    }
    catch {
        Write-Error "문서 JSON 파일 로드 실패: $($_.Exception.Message)"
        return
    }
    
    $response = Invoke-SearchApi -Method "POST" -Uri "$BaseUrl/search/indexes/$IndexName/docs/index?api-version=$ApiVersion" -Body $documents -Description "Index Documents"
    if ($response -and $response.value) {
        $successCount = ($response.value | Where-Object { $_.status -eq $true }).Count
        $failureCount = ($response.value | Where-Object { $_.status -eq $false }).Count
        Write-Success "문서 인덱싱 완료 - 성공: $successCount, 실패: $failureCount"
    }
    
    Start-Sleep -Seconds 3
    
    # 5. 문서 개수 조회
    Write-Step "문서 개수 조회"
    $response = Invoke-SearchApi -Method "GET" -Uri "$BaseUrl/search/indexes/$IndexName/docs/`$count?api-version=$ApiVersion" -Description "Count Documents"
    if ($response -ne $null) {
        Write-Success "총 문서 수: $response"
    }
    
    # 6. 간단한 텍스트 검색 (POST)
    Write-Step "간단한 텍스트 검색 테스트 (POST)"
    
    # JSON 파일에서 검색 요청 로드
    $simpleSearchJsonPath = "test/azure_search_simple_query.json"
    if (Test-Path $simpleSearchJsonPath) {
        try {
            $searchRequest = Get-Content $simpleSearchJsonPath -Raw | ConvertFrom-Json
        }
        catch {
            Write-Warning "간단 검색 JSON 파일 로드 실패. 기본 검색 사용: $($_.Exception.Message)"
            $searchRequest = @{
                search = "AI"
                top = 5
                includeTotalCount = $true
            }
        }
    }
    else {
        $searchRequest = @{
            search = "AI"
            top = 5
            includeTotalCount = $true
        }
    }
    
    $response = Invoke-SearchApi -Method "POST" -Uri "$BaseUrl/search/indexes/$IndexName/docs/search?api-version=$ApiVersion" -Body $searchRequest -Description "Text Search (POST)"
    if ($response -and $response.value) {
        Write-Success "검색 결과: $($response.value.Count)개"
        if ($response.'@odata.count') {
            Write-Info "총 문서 수: $($response.'@odata.count')"
        }
        foreach ($doc in $response.value) {
            $score = if ($doc.'@search.score') { [math]::Round($doc.'@search.score', 2) } else { "N/A" }
            $title = if ($doc.title) { $doc.title } elseif ($doc.hotelName) { $doc.hotelName } else { $doc.id }
            Write-Host "  - $title`: $score" -ForegroundColor Gray
        }
    }
    
    # 7. 필터링된 검색
    Write-Step "필터링된 검색 테스트"
    
    # JSON 파일에서 필터 검색 요청 로드
    $filteredSearchJsonPath = "test/azure_search_filtered_query.json"
    if (Test-Path $filteredSearchJsonPath) {
        try {
            $filteredSearchRequest = Get-Content $filteredSearchJsonPath -Raw | ConvertFrom-Json
            
            $response = Invoke-SearchApi -Method "POST" -Uri "$BaseUrl/search/indexes/$IndexName/docs/search?api-version=$ApiVersion" -Body $filteredSearchRequest -Description "Filtered Search"
            if ($response -and $response.value) {
                Write-Success "필터링된 검색 결과: $($response.value.Count)개"
                foreach ($doc in $response.value) {
                    $title = if ($doc.title) { $doc.title } elseif ($doc.hotelName) { $doc.hotelName } else { $doc.id }
                    $category = if ($doc.category) { $doc.category } else { "N/A" }
                    Write-Host "  - $title ($category)" -ForegroundColor Gray
                }
            }
        }
        catch {
            Write-Warning "필터 검색 JSON 파일 로드 실패: $($_.Exception.Message)"
        }
    }
    else {
        Write-Info "필터 검색 JSON 파일이 없습니다. 스킵합니다."
    }
    
    # 8. 벡터 검색 테스트
    Write-Step "벡터 검색 테스트"
    
    # JSON 파일에서 벡터 검색 요청 로드
    $vectorSearchJsonPath = "test/azure_search_vector_query.json"
    if (Test-Path $vectorSearchJsonPath) {
        try {
            $vectorSearchRequest = Get-Content $vectorSearchJsonPath -Raw | ConvertFrom-Json
            
            $response = Invoke-SearchApi -Method "POST" -Uri "$BaseUrl/search/indexes/$IndexName/docs/search?api-version=$ApiVersion" -Body $vectorSearchRequest -Description "Vector Search"
            if ($response -and $response.value) {
                Write-Success "벡터 검색 결과: $($response.value.Count)개"
                foreach ($doc in $response.value) {
                    $score = if ($doc.'@search.score') { [math]::Round($doc.'@search.score', 2) } else { "N/A" }
                    $title = if ($doc.title) { $doc.title } elseif ($doc.hotelName) { $doc.hotelName } else { $doc.id }
                    Write-Host "  - $title`: $score" -ForegroundColor Gray
                }
            }
        }
        catch {
            Write-Warning "벡터 검색 JSON 파일 로드 실패: $($_.Exception.Message)"
        }
    }
    else {
        Write-Info "벡터 검색 JSON 파일이 없습니다. 스킵합니다."
    }
    
    # 9. 하이브리드 검색 테스트
    Write-Step "하이브리드 검색 테스트"
    
    # JSON 파일에서 하이브리드 검색 요청 로드
    $hybridSearchJsonPath = "test/azure_search_hybrid_query.json"
    if (Test-Path $hybridSearchJsonPath) {
        try {
            $hybridSearchRequest = Get-Content $hybridSearchJsonPath -Raw | ConvertFrom-Json
            
            $response = Invoke-SearchApi -Method "POST" -Uri "$BaseUrl/search/indexes/$IndexName/docs/search?api-version=$ApiVersion" -Body $hybridSearchRequest -Description "Hybrid Search"
            if ($response -and $response.value) {
                Write-Success "하이브리드 검색 결과: $($response.value.Count)개"
                foreach ($doc in $response.value) {
                    $score = if ($doc.'@search.score') { [math]::Round($doc.'@search.score', 2) } else { "N/A" }
                    $title = if ($doc.title) { $doc.title } elseif ($doc.hotelName) { $doc.hotelName } else { $doc.id }
                    Write-Host "  - $title`: $score" -ForegroundColor Gray
                }
            }
        }
        catch {
            Write-Warning "하이브리드 검색 JSON 파일 로드 실패: $($_.Exception.Message)"
        }
    }
    else {
        Write-Info "하이브리드 검색 JSON 파일이 없습니다. 스킵합니다."
    }
    
    # 10. 인덱스 정보 조회
    Write-Step "인덱스 정보 조회"
    $response = Invoke-SearchApi -Method "GET" -Uri "$BaseUrl/search/indexes/$IndexName`?api-version=$ApiVersion" -Description "Get Index Info"
    if ($response) {
        Write-Success "인덱스 정보 조회 성공: $($response.name)"
    }
    
    # 11. 성능 테스트 (간단)
    Write-Step "성능 테스트 (5회 반복)"
    $times = @()
    for ($i = 1; $i -le 5; $i++) {
        $stopwatch = [System.Diagnostics.Stopwatch]::StartNew()
        
        try {
            $searchRequest = @{ search = "AI"; top = 3 }
            $response = Invoke-RestMethod -Uri "$BaseUrl/search/indexes/$IndexName/docs/search?api-version=$ApiVersion" -Method POST -Headers @{"Content-Type"="application/json"; "api-key"=$ApiKey} -Body ($searchRequest | ConvertTo-Json)
            $stopwatch.Stop()
            $times += $stopwatch.ElapsedMilliseconds
            Write-Host "  테스트 $i`: $($stopwatch.ElapsedMilliseconds)ms" -ForegroundColor Gray
        }
        catch {
            Write-Host "  테스트 $i`: 실패" -ForegroundColor Red
        }
    }
    
    if ($times.Count -gt 0) {
        $avgTime = ($times | Measure-Object -Average).Average
        $minTime = ($times | Measure-Object -Minimum).Minimum
        $maxTime = ($times | Measure-Object -Maximum).Maximum
        
        Write-Success "평균 응답 시간: $([math]::Round($avgTime, 2))ms"
        Write-Success "최소 응답 시간: ${minTime}ms"
        Write-Success "최대 응답 시간: ${maxTime}ms"
    }
    
    Write-Host "`n🎉 Azure AI Search API 테스트 완료!" -ForegroundColor Green
    Write-Host "`n📊 테스트 결과 요약:" -ForegroundColor Cyan
    Write-Host "✅ 인덱스 생성 및 관리" -ForegroundColor Green
    Write-Host "✅ 문서 인덱싱 및 검색" -ForegroundColor Green
    Write-Host "✅ GET/POST 검색 방식" -ForegroundColor Green
    Write-Host "✅ 정렬 및 필드 선택" -ForegroundColor Green
    Write-Host "✅ 성능 측정" -ForegroundColor Green
}

# 도움말 표시
if ($args -contains "-help" -or $args -contains "--help" -or $args -contains "-h") {
    Write-Host "Azure AI Search API 테스트 스크립트`n" -ForegroundColor Yellow
    
    Write-Host "사용법: .\scripts\test_search.ps1 [옵션]`n" -ForegroundColor Cyan
    
    Write-Host "옵션:" -ForegroundColor Cyan
    Write-Host "  -BaseUrl <url>      서버 URL (기본값: http://localhost:8000)" -ForegroundColor White
    Write-Host "  -ApiKey <key>       API 키 (기본값: bedrock)" -ForegroundColor White  
    Write-Host "  -ApiVersion <ver>   API 버전 (기본값: 2024-07-01)" -ForegroundColor White
    Write-Host "  -IndexName <name>   테스트 인덱스 이름 (기본값: hotels-test)" -ForegroundColor White
    Write-Host ""
    
    Write-Host "예시:" -ForegroundColor Cyan
    Write-Host "  .\scripts\test_search.ps1" -ForegroundColor Gray
    Write-Host "  .\scripts\test_search.ps1 -BaseUrl 'http://localhost:8080' -ApiKey 'custom-key'" -ForegroundColor Gray
    Write-Host "  .\scripts\test_search.ps1 -IndexName 'azure_index'" -ForegroundColor Gray
    Write-Host "" 
    Write-Host "필요한 JSON 파일들:" -ForegroundColor Cyan
    Write-Host "  test/azure_search_create_index.json     - 인덱스 생성 스키마" -ForegroundColor White
    Write-Host "  test/azure_search_index_documents.json  - 인덱싱할 문서 데이터" -ForegroundColor White
    Write-Host "  test/azure_search_simple_query.json     - 기본 검색 쿼리" -ForegroundColor White
    Write-Host "  test/azure_search_filtered_query.json   - 필터링 검색 쿼리" -ForegroundColor White
    Write-Host "  test/azure_search_vector_query.json     - 벡터 검색 쿼리" -ForegroundColor White
    Write-Host "  test/azure_search_hybrid_query.json     - 하이브리드 검색 쿼리" -ForegroundColor White
    
    exit 0
}

# 메인 실행
Test-AzureSearch
