#!/usr/bin/env python3
"""
인덱스 매핑 확인 스크립트
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

def check_index_mapping(client, index_name='azure_index'):
    """인덱스 매핑 상세 확인"""
    try:
        logger.info(f"=== Checking mapping for index: {index_name} ===")
        
        # 인덱스 매핑 조회
        mapping_response = client.indices.get_mapping(index=index_name)
        
        if index_name in mapping_response:
            mappings = mapping_response[index_name]['mappings']
            logger.info(f"Full mapping: {json.dumps(mappings, indent=2)}")
            
            properties = mappings.get('properties', {})
            logger.info(f"\n=== Field Properties ===")
            
            for field_name, field_def in properties.items():
                logger.info(f"Field: {field_name}")
                logger.info(f"  Type: {field_def.get('type', 'unknown')}")
                
                if field_name == 'content_vector':
                    logger.info(f"  VECTOR FIELD DETAILS:")
                    logger.info(f"    Dimension: {field_def.get('dimension', 'unknown')}")
                    logger.info(f"    All properties: {field_def}")
                
                logger.info("")
        
        # 인덱스 설정도 확인
        settings_response = client.indices.get_settings(index=index_name)
        if index_name in settings_response:
            settings = settings_response[index_name]['settings']
            logger.info(f"Index settings: {json.dumps(settings, indent=2)}")
            
            # KNN 설정 확인
            index_settings = settings.get('index', {})
            if 'knn' in index_settings:
                logger.info(f"KNN enabled: {index_settings['knn']}")
            else:
                logger.warning("KNN setting not found in index settings")
                
    except Exception as e:
        logger.error(f"Error checking index mapping: {e}")

def test_simple_vector_query(client, index_name='azure_index'):
    """간단한 벡터 쿼리 테스트"""
    try:
        logger.info(f"\n=== Testing simple vector queries ===")
        
        # 테스트 1: script_score 쿼리
        logger.info("Testing script_score query...")
        script_query = {
            "query": {
                "script_score": {
                    "query": {"match_all": {}},
                    "script": {
                        "source": "cosineSimilarity(params.query_vector, doc['content_vector']) + 1.0",
                        "params": {
                            "query_vector": [0.1, 0.2, 0.3, 0.4, 0.5, 0.1, 0.1, 0.1, 0.1, 0.1]
                        }
                    }
                }
            },
            "size": 3
        }
        
        try:
            response = client.search(index=index_name, body=script_query)
            logger.info(f"Script_score query succeeded: {response['hits']['total']['value']} hits")
            for hit in response['hits']['hits']:
                logger.info(f"  Doc {hit['_source']['id']}: score={hit['_score']}")
        except Exception as e:
            logger.error(f"Script_score query failed: {e}")
        
        # 테스트 2: KNN 쿼리 (만약 지원된다면)
        logger.info("\nTesting KNN query...")
        knn_query = {
            "knn": {
                "content_vector": {
                    "vector": [0.1, 0.2, 0.3, 0.4, 0.5, 0.1, 0.1, 0.1, 0.1, 0.1],
                    "k": 3
                }
            },
            "size": 3
        }
        
        try:
            response = client.search(index=index_name, body=knn_query)
            logger.info(f"KNN query succeeded: {response['hits']['total']['value']} hits")
            for hit in response['hits']['hits']:
                logger.info(f"  Doc {hit['_source']['id']}: score={hit['_score']}")
        except Exception as e:
            logger.error(f"KNN query failed: {e}")
        
        # 테스트 3: 가장 기본적인 match_all
        logger.info("\nTesting basic match_all...")
        basic_query = {
            "query": {"match_all": {}},
            "size": 2
        }
        
        try:
            response = client.search(index=index_name, body=basic_query)
            logger.info(f"Basic query succeeded: {response['hits']['total']['value']} hits")
            for hit in response['hits']['hits']:
                vector = hit['_source'].get('content_vector', [])
                logger.info(f"  Doc {hit['_source']['id']}: vector_len={len(vector)}")
        except Exception as e:
            logger.error(f"Basic query failed: {e}")
            
    except Exception as e:
        logger.error(f"Vector query test failed: {e}")

def main():
    """메인 함수"""
    if not DEPS_AVAILABLE:
        logger.error("Cannot run: missing dependencies")
        return
    
    try:
        client = create_opensearch_client()
        check_index_mapping(client)
        test_simple_vector_query(client)
        
    except Exception as e:
        logger.error(f"Failed to check mapping: {e}")

if __name__ == '__main__':
    main()