"""Azure AI Search 호환 API 라우터"""
import logging
from typing import Dict, Any, List
from fastapi import APIRouter, Depends, HTTPException, Query, Body, Path
from fastapi.responses import JSONResponse

from api.auth import azure_api_key_auth
from api.models.opensearch_client import OpenSearchServerlessClient
from api.schema import (
    SearchIndex, SearchRequest, SearchResponse, IndexBatch, IndexBatchResult,
    IndexingResult
)

logger = logging.getLogger(__name__)

router = APIRouter(
    dependencies=[Depends(azure_api_key_auth)],
    tags=["Azure AI Search Compatible"]
)

# OpenSearch 클라이언트 초기화
def get_opensearch_client():
    """OpenSearch 클라이언트 의존성"""
    try:
        return OpenSearchServerlessClient()
    except ImportError:
        raise HTTPException(
            status_code=503,
            detail={
                "error": "OpenSearch dependencies not available",
                "message": "Please install: pip install opensearch-py requests-aws4auth",
                "setup": "Configure OPENSEARCH_ENDPOINT environment variable"
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail={
                "error": "OpenSearch service unavailable", 
                "message": str(e)
            }
        )


# 인덱스 관리 API
@router.post("/search/indexes/{index_name}")
async def create_or_update_index(
    index_name: str = Path(..., description="인덱스 이름"),
    index_definition: SearchIndex = Body(..., description="인덱스 정의"),
    api_version: str = Query("2024-07-01", alias="api-version"),
    client: OpenSearchServerlessClient = Depends(get_opensearch_client)
):
    """인덱스 생성 또는 업데이트"""
    try:
        success = client.create_index(index_name, index_definition)
        
        if success:
            return JSONResponse(
                content={
                    "@odata.context": f"#indexes('{index_name}')",
                    "@odata.etag": f'W/"{index_name}"',
                    "name": index_name,
                    "fields": [field.dict() for field in index_definition.fields],
                },
                status_code=201
            )
        else:
            raise HTTPException(status_code=400, detail="Failed to create index")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create index '{index_name}': {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/search/indexes/{index_name}")
async def get_index(
    index_name: str = Path(..., description="인덱스 이름"),
    api_version: str = Query("2024-07-01", alias="api-version"),
    client: OpenSearchServerlessClient = Depends(get_opensearch_client)
):
    """인덱스 정보 조회"""
    try:
        index_info = client.get_index(index_name)
        
        return {
            "@odata.context": f"#indexes('{index_name}')",
            "@odata.etag": f'W/"{index_name}"',
            "name": index_name,
            "fields": [],  # 실제 매핑에서 추출 필요시 구현
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get index '{index_name}': {str(e)}")
        raise HTTPException(status_code=404, detail=f"Index '{index_name}' not found")


@router.get("/search/indexes")
async def list_indexes(
    api_version: str = Query("2024-07-01", alias="api-version"),
    client: OpenSearchServerlessClient = Depends(get_opensearch_client)
):
    """인덱스 목록 조회"""
    try:
        indices = client.list_indices()
        
        return {
            "@odata.context": "#indexes",
            "value": [
                {
                    "@odata.etag": f'W/"{idx}"',
                    "name": idx,
                    "fields": []
                }
                for idx in indices
            ]
        }
    except Exception as e:
        logger.error(f"Failed to list indexes: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/search/indexes/{index_name}")
async def delete_index(
    index_name: str = Path(..., description="인덱스 이름"),
    api_version: str = Query("2024-07-01", alias="api-version"),
    client: OpenSearchServerlessClient = Depends(get_opensearch_client)
):
    """인덱스 삭제"""
    try:
        success = client.delete_index(index_name)
        if success:
            return JSONResponse(status_code=204, content=None)
        else:
            raise HTTPException(status_code=400, detail="Failed to delete index")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete index '{index_name}': {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


# 문서 작업 API
@router.post("/search/indexes/{index_name}/docs/index")
async def index_documents(
    index_name: str = Path(..., description="인덱스 이름"),
    batch: IndexBatch = Body(..., description="인덱싱할 문서 배치"),
    api_version: str = Query("2024-07-01", alias="api-version"),
    client: OpenSearchServerlessClient = Depends(get_opensearch_client)
):
    """문서 배치 인덱싱"""
    try:
        # 문서 인덱싱
        result = client.index_documents(index_name, [doc.dict() for doc in batch.value])
        
        # 결과 변환
        index_results = []
        for item in result.get('items', []):
            for action, details in item.items():
                status_code = details.get('status', 200)
                index_results.append(IndexingResult(
                    key=details.get('_id', ''),
                    status=status_code < 300,
                    error_message=details.get('error', {}).get('reason') if 'error' in details else None,
                    status_code=status_code
                ))
        
        return IndexBatchResult(value=index_results).dict(by_alias=True)
        
    except Exception as e:
        logger.error(f"Failed to index documents: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/search/indexes/{index_name}/docs/$count")
async def count_documents(
    index_name: str = Path(..., description="인덱스 이름"),
    api_version: str = Query("2024-07-01", alias="api-version"),
    client: OpenSearchServerlessClient = Depends(get_opensearch_client)
):
    """문서 개수 조회"""
    try:
        count = client.count_documents(index_name)
        return count
    except Exception as e:
        logger.error(f"Failed to count documents: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


# 검색 API
@router.post("/search/indexes/{index_name}/docs/search")
async def search_documents(
    index_name: str = Path(..., description="인덱스 이름"),
    search_request: SearchRequest = Body(..., description="검색 요청"),
    api_version: str = Query("2024-07-01", alias="api-version"),
    client: OpenSearchServerlessClient = Depends(get_opensearch_client)
):
    """문서 검색"""
    try:
        response = client.search(index_name, search_request)
        return response.dict(by_alias=True)
        
    except Exception as e:
        logger.error(f"Search failed: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/search/indexes/{index_name}/docs/search")
async def search_documents_get(
    index_name: str = Path(..., description="인덱스 이름"),
    api_version: str = Query("2024-07-01", alias="api-version"),
    search: str = Query(None, description="검색 쿼리"),
    searchFields: str = Query(None, description="검색 대상 필드"),
    select: str = Query(None, description="선택할 필드"),
    filter: str = Query(None, description="필터 조건"),
    orderby: str = Query(None, description="정렬 조건"),
    top: int = Query(10, description="반환할 결과 수"),
    skip: int = Query(0, description="건너뛸 결과 수"),
    includeTotalCount: bool = Query(False, description="총 개수 포함 여부"),
    client: OpenSearchServerlessClient = Depends(get_opensearch_client)
):
    """GET 방식 문서 검색"""
    try:
        # GET 파라미터를 SearchRequest로 변환
        search_request = SearchRequest(
            search=search,
            search_fields=searchFields,
            select=select,
            filter=filter,
            order_by=orderby,
            top=top,
            skip=skip,
            include_total_count=includeTotalCount
        )
        
        response = client.search(index_name, search_request)
        return response.dict(by_alias=True)
        
    except Exception as e:
        logger.error(f"Search failed: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))