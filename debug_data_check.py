#!/usr/bin/env python3
"""
OpenSearch Serverless 데이터 직접 확인 스크립트
"""
import os
import json
import logging
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 필요한 라이브러리 확인
try:
    from opensearchpy import OpenSearch, RequestsHttpConnection
    from requests_aws4auth import AWS4Auth
    import boto3
    DEPS_AVAILABLE = True
except ImportError as e:
    logger.error(f"Required dependencies not available: {e}")
    DEPS_AVAILABLE = False

def create_opensearch_client():
    """OpenSearch 클라이언트 생성"""
    if not DEPS_AVAILABLE:
        raise ImportError("Required dependencies not installed")
    
    # 환경 변수에서 설정 읽기
    endpoint = os.getenv('OPENSEARCH_ENDPOINT')
    region = os.getenv('AWS_REGION', 'ap-northeast-2')
    
    if not endpoint:
        raise ValueError("OPENSEARCH_ENDPOINT environment variable is required")
    
    # AWS 자격 증명
    session = boto3.Session()
    credentials = session.get_credentials()
    
    if not credentials:
        raise ValueError("No AWS credentials found")
    
    auth = AWS4Auth(
        credentials.access_key,
        credentials.secret_key,
        region,
        'aoss',
        session_token=credentials.token
    )
    
    # 호스트 추출
    host = endpoint.replace('https://', '').replace('http://', '')
    
    client = OpenSearch(
        hosts=[{'host': host, 'port': 443}],
        http_auth=auth,
        use_ssl=True,
        verify_certs=True,
        connection_class=RequestsHttpConnection,
        timeout=30
    )
    
    return client

def check_index_data(client, index_name='azure_index'):
    """인덱스 데이터 확인"""
    try:
        logger.info(f"=== Checking index: {index_name} ===")
        
        # 1. 인덱스 존재 확인
        try:
            index_exists = client.indices.exists(index=index_name)
            logger.info(f"Index exists: {index_exists}")
            
            if not index_exists:
                logger.error(f"Index '{index_name}' does not exist!")
                return
        except Exception as e:
            logger.error(f"Error checking index existence: {e}")
            return
        
        # 2. 인덱스 정보 조회
        try:
            index_info = client.indices.get(index=index_name)
            logger.info(f"Index info keys: {list(index_info.keys())}")
            
            if index_name in index_info:
                mappings = index_info[index_name].get('mappings', {})
                properties = mappings.get('properties', {})
                logger.info(f"Index properties: {list(properties.keys())}")
        except Exception as e:
            logger.error(f"Error getting index info: {e}")
        
        # 3. 문서 개수 확인
        try:
            count_response = client.count(index=index_name)
            doc_count = count_response.get('count', 0)
            logger.info(f"Document count: {doc_count}")
            
            if doc_count == 0:
                logger.warning("No documents found in index!")
        except Exception as e:
            logger.error(f"Error counting documents: {e}")
        
        # 4. 샘플 문서 조회 (match_all)
        try:
            search_response = client.search(
                index=index_name,
                body={
                    "query": {"match_all": {}},
                    "size": 3
                }
            )
            
            hits = search_response.get('hits', {})
            total_hits = hits.get('total', {})
            
            if isinstance(total_hits, dict):
                total_count = total_hits.get('value', 0)
            else:
                total_count = total_hits
                
            logger.info(f"Search total hits: {total_count}")
            
            documents = hits.get('hits', [])
            logger.info(f"Retrieved {len(documents)} sample documents")
            
            for i, doc in enumerate(documents):
                logger.info(f"Document {i+1}:")
                logger.info(f"  ID: {doc.get('_id')}")
                logger.info(f"  Score: {doc.get('_score')}")
                source = doc.get('_source', {})
                logger.info(f"  Fields: {list(source.keys())}")
                
                # 주요 필드 값 출력
                for key in ['id', 'content', 'content_vector']:
                    if key in source:
                        value = source[key]
                        if key == 'content_vector' and isinstance(value, list):
                            logger.info(f"  {key}: [vector with {len(value)} dimensions]")
                        else:
                            logger.info(f"  {key}: {str(value)[:100]}...")
                            
        except Exception as e:
            logger.error(f"Error searching documents: {e}")
        
        # 5. 클러스터 상태 확인
        try:
            cluster_health = client.cluster.health()
            logger.info(f"Cluster status: {cluster_health.get('status')}")
            logger.info(f"Number of nodes: {cluster_health.get('number_of_nodes')}")
        except Exception as e:
            logger.error(f"Error getting cluster health: {e}")
            
    except Exception as e:
        logger.error(f"Unexpected error: {e}")

def main():
    """메인 함수"""
    if not DEPS_AVAILABLE:
        logger.error("Cannot run: missing dependencies")
        logger.info("Install with: pip install opensearch-py requests-aws4auth boto3 python-dotenv")
        return
    
    try:
        client = create_opensearch_client()
        check_index_data(client)
        
    except Exception as e:
        logger.error(f"Failed to check data: {e}")

if __name__ == '__main__':
    main()