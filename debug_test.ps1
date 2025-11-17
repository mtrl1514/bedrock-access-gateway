# Azure AI Search Debug Test Script

param(
    [string]$BaseUrl = "http://localhost:8000",
    [string]$ApiKey = "bedrock",
    [string]$IndexName = "azure_index"
)

$headers = @{
    "Content-Type" = "application/json"
    "api-key" = $ApiKey
}

Write-Host "🔍 Azure AI Search Debug Test" -ForegroundColor Magenta
Write-Host "Server: $BaseUrl" -ForegroundColor Gray
Write-Host "Index: $IndexName" -ForegroundColor Gray
Write-Host ("=" * 50) -ForegroundColor Gray

# Step 1: Health Check
Write-Host "`n1️⃣ Health Check" -ForegroundColor Yellow
try {
    $health = Invoke-RestMethod -Uri "$BaseUrl/health" -Method GET
    if ($health.status -eq "OK") {
        Write-Host "✅ Server is running" -ForegroundColor Green
    } else {
        Write-Host "⚠️ Server status: $($health.status)" -ForegroundColor Yellow
    }
} catch {
    Write-Host "❌ Server not accessible: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# Step 2: Clean slate - delete index
Write-Host "`n2️⃣ Delete existing index" -ForegroundColor Yellow
try {
    Invoke-RestMethod -Uri "$BaseUrl/search/indexes/$IndexName?api-version=2024-07-01" -Method DELETE -Headers @{"api-key"=$ApiKey}
    Write-Host "✅ Index deleted" -ForegroundColor Green
} catch {
    Write-Host "ℹ️ Index didn't exist or delete failed" -ForegroundColor Gray
}

# Step 3: Create index
Write-Host "`n3️⃣ Create new index" -ForegroundColor Yellow
Write-Host "📋 Watch server console for detailed field processing logs..." -ForegroundColor Cyan

try {
    $jsonBody = Get-Content "test/azure_search_create_index.json" -Raw
    $createResult = Invoke-RestMethod -Uri "$BaseUrl/search/indexes/$IndexName?api-version=2024-07-01" -Method POST -Headers $headers -Body $jsonBody
    
    Write-Host "✅ Index created successfully" -ForegroundColor Green
    Write-Host "Response: $($createResult | ConvertTo-Json -Compress)" -ForegroundColor Gray
    
} catch {
    Write-Host "❌ Index creation failed!" -ForegroundColor Red
    Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Red
    
    if ($_.Exception.Response) {
        $reader = New-Object System.IO.StreamReader($_.Exception.Response.GetResponseStream())
        $responseBody = $reader.ReadToEnd()
        Write-Host "Response body: $responseBody" -ForegroundColor Yellow
    }
    exit 1
}

# Step 4: Verify index structure
Write-Host "`n4️⃣ Verify index structure" -ForegroundColor Yellow
Start-Sleep -Seconds 2

try {
    $indexInfo = Invoke-RestMethod -Uri "$BaseUrl/search/indexes/$IndexName?api-version=2024-07-01" -Method GET -Headers @{"api-key"=$ApiKey}
    
    Write-Host "📊 Index Information:" -ForegroundColor Cyan
    Write-Host "  Name: $($indexInfo.name)" -ForegroundColor White
    Write-Host "  Field Count: $($indexInfo.fields.Count)" -ForegroundColor $(if($indexInfo.fields.Count -gt 0) {"Green"} else {"Red"})
    
    if ($indexInfo.fields.Count -eq 0) {
        Write-Host "`n❌ CRITICAL: No fields found in index!" -ForegroundColor Red
        Write-Host "   This means field mapping failed during index creation." -ForegroundColor Red
        Write-Host "   Check the server logs for field processing errors." -ForegroundColor Yellow
        Write-Host "`n🔍 Expected logs should show:" -ForegroundColor Cyan
        Write-Host "   - 'Processing 11 fields for index mapping'" -ForegroundColor Gray
        Write-Host "   - 'Processing field 1/11: id (type: Edm.String)'" -ForegroundColor Gray
        Write-Host "   - 'Field id mapped to: {...}'" -ForegroundColor Gray
        exit 1
    }
    
    Write-Host "`n📋 Fields:" -ForegroundColor Cyan
    foreach ($field in $indexInfo.fields) {
        $typeColor = switch ($field.type) {
            "Collection(Edm.Single)" { "Magenta" }
            "Edm.String" { "Blue" }
            "Edm.Int64" { "Green" }
            "Edm.Double" { "Yellow" }
            default { "Gray" }
        }
        Write-Host "  • $($field.name)" -NoNewline -ForegroundColor White
        Write-Host " ($($field.type))" -ForegroundColor $typeColor
        
        if ($field.type -eq "Collection(Edm.Single)") {
            Write-Host "    Dimensions: $($field.dimensions)" -ForegroundColor Gray
        }
    }
    
} catch {
    Write-Host "❌ Failed to get index info: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# Step 5: Test document indexing
Write-Host "`n5️⃣ Test document indexing" -ForegroundColor Yellow

$testDoc = @{
    "value" = @(
        @{
            "@search.action" = "upload"
            "id" = "debug_test_001"
            "content" = "This is a debug test document"
            "metadata" = "debug test"
            "owning_object" = "test_service"
            "owning_user" = "debug@test.com"
            "owning_group" = "debug_team"
            "section_index" = 999
            "knowledge_bases" = @("debug", "test")
            "owning_file" = "debug_test.txt"
            "last_modified_date" = "2024-01-01T12:00:00Z"
        }
    )
} | ConvertTo-Json -Depth 4

try {
    Write-Host "📝 Indexing test document..." -ForegroundColor Cyan
    $docResult = Invoke-RestMethod -Uri "$BaseUrl/search/indexes/$IndexName/docs/index?api-version=2024-07-01" -Method POST -Headers $headers -Body $testDoc
    
    if ($docResult.value -and $docResult.value.Count -gt 0) {
        $doc = $docResult.value[0]
        if ($doc.status) {
            Write-Host "✅ Document indexed successfully!" -ForegroundColor Green
            Write-Host "  Document ID: $($doc.key)" -ForegroundColor Gray
            Write-Host "  Status Code: $($doc.statusCode)" -ForegroundColor Gray
        } else {
            Write-Host "❌ Document indexing failed!" -ForegroundColor Red
            Write-Host "  Error: $($doc.errorMessage)" -ForegroundColor Red
            Write-Host "  Status Code: $($doc.statusCode)" -ForegroundColor Red
        }
    } else {
        Write-Host "⚠️ Empty response from document indexing" -ForegroundColor Yellow
        Write-Host "Response: $($docResult | ConvertTo-Json -Depth 3)" -ForegroundColor Gray
    }
    
} catch {
    Write-Host "❌ Document indexing request failed: $($_.Exception.Message)" -ForegroundColor Red
}

# Step 6: Test search
Write-Host "`n6️⃣ Test search functionality" -ForegroundColor Yellow

try {
    $searchDoc = @{
        "search" = "*"
        "top" = 5
    } | ConvertTo-Json

    $searchResult = Invoke-RestMethod -Uri "$BaseUrl/search/indexes/$IndexName/docs/search?api-version=2024-07-01" -Method POST -Headers $headers -Body $searchDoc
    
    if ($searchResult.value -and $searchResult.value.Count -gt 0) {
        Write-Host "✅ Search successful! Found $($searchResult.value.Count) documents" -ForegroundColor Green
        foreach ($doc in $searchResult.value) {
            Write-Host "  • $($doc.id): $($doc.content.Substring(0, [Math]::Min(50, $doc.content.Length)))..." -ForegroundColor Gray
        }
    } else {
        Write-Host "ℹ️ Search returned no results (this is normal if no documents were indexed)" -ForegroundColor Gray
    }
    
} catch {
    Write-Host "❌ Search failed: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host "`n🎉 Debug test complete!" -ForegroundColor Magenta
Write-Host "📋 Summary:" -ForegroundColor Cyan
Write-Host "  - Server: $(if($health.status -eq 'OK') {'✅ Running'} else {'❌ Issues'})" -ForegroundColor White
Write-Host "  - Index: $(if($indexInfo.fields.Count -gt 0) {'✅ Created with ' + $indexInfo.fields.Count + ' fields'} else {'❌ No fields'})" -ForegroundColor White
Write-Host "  - Documents: $(if($docResult.value[0].status) {'✅ Indexing works'} else {'❌ Indexing failed'})" -ForegroundColor White
Write-Host "`n💡 If issues persist, check server console logs for detailed error information." -ForegroundColor Yellow