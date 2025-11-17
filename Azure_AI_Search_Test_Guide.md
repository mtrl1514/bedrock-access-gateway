# Azure AI Search API 테스트 가이드

이 가이드는 AWS OpenSearch Serverless를 백엔드로 사용하는 Azure AI Search 호환 API를 테스트하는 방법을 설명합니다.

## 🚀 빠른 시작

### 1. 환경 설정

```bash
# OpenSearch 패키지 설치
pip install opensearch-py requests-aws4auth

# 환경 변수 설정 (필수)
export OPENSEARCH_ENDPOINT="https://your-collection-id.us-east-1.aoss.amazonaws.com"
export OPENSEARCH_COLLECTION_NAME="bedrock-search"
export AWS_REGION="us-east-1"

# AWS 자격 증명 설정
export AWS_ACCESS_KEY_ID="your-access-key"
export AWS_SECRET_ACCESS_KEY="your-secret-key"
```

### 2. 서버 시작

```bash
cd src
uvicorn api.app:app --host 0.0.0.0 --port 8000 --reload
```

### 3. PowerShell 테스트 실행

```powershell
# 기본 테스트
.\scripts\test_search.ps1

# 사용자 정의 설정
.\scripts\test_search.ps1 -BaseUrl "http://localhost:8000" -ApiKey "bedrock" -IndexName "my-test"
```

## 📋 지원되는 API 엔드포인트

### 인덱스 관리

| 메서드 | 엔드포인트 | 설명 |
|--------|------------|------|
| POST | `/search/indexes/{index-name}?api-version=2024-07-01` | 인덱스 생성 |
| GET | `/search/indexes/{index-name}?api-version=2024-07-01` | 인덱스 조회 |
| GET | `/search/indexes?api-version=2024-07-01` | 인덱스 목록 |
| DELETE | `/search/indexes/{index-name}?api-version=2024-07-01` | 인덱스 삭제 |

### 문서 관리

| 메서드 | 엔드포인트 | 설명 |
|--------|------------|------|
| POST | `/search/indexes/{index-name}/docs/index?api-version=2024-07-01` | 문서 인덱싱 |
| GET | `/search/indexes/{index-name}/docs/$count?api-version=2024-07-01` | 문서 개수 |

### 검색

| 메서드 | 엔드포인트 | 설명 |
|--------|------------|------|
| POST | `/search/indexes/{index-name}/docs/search?api-version=2024-07-01` | 검색 (POST) |
| GET | `/search/indexes/{index-name}/docs/search?api-version=2024-07-01` | 검색 (GET) |

## 📋 테스트 JSON 파일

다음 JSON 파일들이 `test/` 폴더에 준비되어 있습니다:

- `azure_search_create_index.json` - 인덱스 생성용 (벡터 필드 포함)
- `azure_search_index_documents.json` - 문서 인덱싱용 (샘플 데이터)
- `azure_search_simple_query.json` - 기본 텍스트 검색
- `azure_search_filtered_query.json` - 필터 및 정렬이 있는 검색
- `azure_search_vector_query.json` - 벡터 검색
- `azure_search_hybrid_query.json` - 하이브리드 검색 (텍스트 + 벡터)

## 🧪 curl 테스트 명령어

### 1. Health Check

```bash
curl -X GET "http://localhost:8000/health"
```

### 2. 인덱스 생성

```bash
curl -X POST "http://localhost:8000/search/indexes/sample-index?api-version=2024-07-01" \
  -H "Content-Type: application/json" \
  -H "api-key: bedrock" \
  -d @test/azure_search_create_index.json
```

### 3. 인덱스 목록 조회

```bash
curl -X GET "http://localhost:8000/search/indexes?api-version=2024-07-01" \
  -H "api-key: bedrock"
```

### 4. 문서 인덱싱

```bash
curl -X POST "http://localhost:8000/search/indexes/sample-index/docs/index?api-version=2024-07-01" \
  -H "Content-Type: application/json" \
  -H "api-key: bedrock" \
  -d @test/azure_search_index_documents.json
```

### 5. 문서 개수 조회

```bash
curl -X GET "http://localhost:8000/search/indexes/sample-index/docs/\$count?api-version=2024-07-01" \
  -H "api-key: bedrock"
```

### 6. 간단한 텍스트 검색 (POST)

```bash
curl -X POST "http://localhost:8000/search/indexes/sample-index/docs/search?api-version=2024-07-01" \
  -H "Content-Type: application/json" \
  -H "api-key: bedrock" \
  -d @test/azure_search_simple_query.json
```

### 7. 필터링된 검색

```bash
curl -X POST "http://localhost:8000/search/indexes/sample-index/docs/search?api-version=2024-07-01" \
  -H "Content-Type: application/json" \
  -H "api-key: bedrock" \
  -d @test/azure_search_filtered_query.json
```

### 8. 벡터 검색

```bash
curl -X POST "http://localhost:8000/search/indexes/sample-index/docs/search?api-version=2024-07-01" \
  -H "Content-Type: application/json" \
  -H "api-key: bedrock" \
  -d @test/azure_search_vector_query.json
```

### 9. 하이브리드 검색 (텍스트 + 벡터)

```bash
curl -X POST "http://localhost:8000/search/indexes/sample-index/docs/search?api-version=2024-07-01" \
  -H "Content-Type: application/json" \
  -H "api-key: bedrock" \
  -d @test/azure_search_hybrid_query.json
```

### 10. 인덱스 삭제

```bash
curl -X DELETE "http://localhost:8000/search/indexes/sample-index?api-version=2024-07-01" \
  -H "api-key: bedrock"
```

## 📊 예상 응답 형식

### 검색 응답 예시

```json
{
  "@odata.context": "#docs",
  "@odata.count": 2,
  "value": [
    {
      "id": "1",
      "title": "Introduction to AI",
      "content": "Artificial Intelligence is revolutionizing how we work and live. This comprehensive guide covers the basics of AI technology.",
      "category": "Technology",
      "rating": 4.5,
      "@search.score": 1.2345
    },
    {
      "id": "2",
      "title": "Machine Learning Fundamentals",
      "content": "Learn the core concepts of machine learning including supervised and unsupervised learning algorithms.",
      "category": "Education",
      "rating": 4.8,
      "@search.score": 0.9876
    }
  ]
}
```

### 인덱싱 응답 예시

```json
{
  "value": [
    {
      "key": "1",
      "status": true,
      "errorMessage": null,
      "statusCode": 201
    },
    {
      "key": "2", 
      "status": true,
      "errorMessage": null,
      "statusCode": 201
    }
  ]
}
```

## 🔧 트러블슈팅

### OpenSearch 연결 오류

```bash
# 1. OpenSearch 엔드포인트 확인
curl -X GET "$OPENSEARCH_ENDPOINT/_cluster/health"

# 2. AWS 자격 증명 확인
aws sts get-caller-identity

# 3. OpenSearch Serverless 정책 확인
aws opensearchserverless get-access-policy --name your-policy-name
```

### 일반적인 오류

1. **503 Service Unavailable**: OpenSearch 의존성 미설치
   ```bash
   pip install opensearch-py requests-aws4auth
   ```

2. **401 Unauthorized**: API 키 불일치
   - Header: `api-key: bedrock` 확인

3. **404 Not Found**: 인덱스가 존재하지 않음
   - 인덱스 생성 후 테스트

4. **400 Bad Request**: 잘못된 요청 형식
   - JSON 형식 및 필드명 확인

## 🚀 고급 기능

### 1. 벡터 검색 인덱스 생성

```json
{
  "name": "hotels-vector",
  "fields": [
    {
      "name": "hotelId",
      "type": "Edm.String", 
      "key": true
    },
    {
      "name": "description",
      "type": "Edm.String",
      "searchable": true
    },
    {
      "name": "descriptionVector",
      "type": "Collection(Edm.Single)",
      "searchable": true,
      "vectorSearchDimensions": 1536,
      "vectorSearchProfileName": "my-vector-config"
    }
  ],
  "vectorSearch": {
    "algorithms": [
      {
        "name": "my-algorithms-config",
        "kind": "hnsw"
      }
    ],
    "profiles": [
      {
        "name": "my-vector-config",
        "algorithmConfigurationName": "my-algorithms-config"
      }
    ]
  }
}
```

### 2. 복합 검색 (텍스트 + 벡터)

```json
{
  "search": "luxury hotel",
  "vectorQueries": [
    {
      "vector": [0.1, 0.2, 0.3],
      "kNearestNeighbors": 5,
      "fields": "descriptionVector"
    }
  ],
  "top": 10
}
```

## 📈 성능 최적화

1. **인덱스 설정 최적화**
   - 불필요한 필드의 `searchable` 속성 비활성화
   - 적절한 `analyzer` 선택

2. **검색 쿼리 최적화** 
   - `searchFields`로 검색 범위 제한
   - `select`로 반환 필드 제한
   - `top` 값 적절히 설정

3. **벡터 검색 최적화**
   - 적절한 `kNearestNeighbors` 값 설정
   - 벡터 차원 수 최적화

## 🔗 관련 링크

- [Azure AI Search REST API 문서](https://docs.microsoft.com/rest/api/searchservice/)
- [AWS OpenSearch Serverless 문서](https://docs.aws.amazon.com/opensearch-service/latest/developerguide/serverless.html)
- [OpenSearch Python 클라이언트](https://opensearch.org/docs/latest/clients/python/)

---

💡 **팁**: PowerShell 스크립트를 사용하면 모든 테스트를 자동으로 실행할 수 있습니다!