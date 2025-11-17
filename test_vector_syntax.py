#!/usr/bin/env python3
"""
OpenSearch Serverless 벡터 검색 구문 테스트
"""
import os
import json
import logging
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    from opensearchpy import OpenSearch, RequestsHttpConnection
    from requests_aws4auth import AWS4Auth
    import boto3
    DEPS_AVAILABLE = True
except ImportError as e:
    logger.error(f"Required dependencies not available: {e}")
    DEPS_AVAILABLE = False

def create_opensearch_client():
    endpoint = os.getenv('OPENSEARCH_ENDPOINT')
    region = os.getenv('AWS_REGION', 'ap-northeast-2')
    
    session = boto3.Session()
    credentials = session.get_credentials()
    
    auth = AWS4Auth(
        credentials.access_key,
        credentials.secret_key,
        region,
        'aoss',
        session_token=credentials.token
    )
    
    host = endpoint.replace('https://', '').replace('http://', '')
    
    return OpenSearch(
        hosts=[{'host': host, 'port': 443}],
        http_auth=auth,
        use_ssl=True,
        verify_certs=True,
        connection_class=RequestsHttpConnection,
        timeout=30
    )

def test_vector_queries(client, index_name='azure_index'):
    """다양한 벡터 검색 구문 테스트"""
    
    test_vector = [0.1, 0.2, 0.3, 0.4, 0.5, 0.1, 0.1, 0.1, 0.1, 0.1]
    
    queries_to_test = [
        # 1. Neural search (OpenSearch 2.x)
        {
            "name": "Neural Search Query",
            "query": {
                "size": 3,
                "query": {
                    "neural": {
                        "content_vector": {
                            "query_text": "",
                            "k": 3
                        }
                    }
                }
            }
        },
        
        # 2. KNN query (different syntax)
        {
            "name": "KNN Query v2",
            "query": {
                "size": 3,
                "query": {
                    "knn": {
                        "content_vector": {
                            "vector": test_vector,
                            "k": 3
                        }
                    }
                }
            }
        },
        
        # 3. Function score with cosine similarity
        {
            "name": "Function Score Query",
            "query": {
                "size": 3,
                "query": {
                    "function_score": {
                        "query": {"match_all": {}},
                        "functions": [
                            {
                                "filter": {"match_all": {}},
                                "script_score": {
                                    "script": "1.0"
                                }
                            }
                        ]
                    }
                }
            }
        },
        
        # 4. Boolean query with term matching (fallback)
        {
            "name": "Boolean Fallback",
            "query": {
                "size": 3,
                "query": {
                    "bool": {
                        "must": [
                            {"exists": {"field": "content_vector"}}
                        ]
                    }
                }
            }
        }
    ]
    
    for test_case in queries_to_test:
        logger.info(f"\n=== Testing: {test_case['name']} ===")
        logger.info(f"Query: {json.dumps(test_case['query'], indent=2)}")
        
        try:
            response = client.search(index=index_name, body=test_case['query'])
            hits = response['hits']['hits']
            logger.info(f"✅ SUCCESS: Found {len(hits)} results")
            
            for i, hit in enumerate(hits):
                score = hit['_score']
                doc_id = hit['_source'].get('id', 'unknown')
                logger.info(f"  {i+1}. Doc {doc_id}: score={score}")
                
        except Exception as e:
            logger.error(f"❌ FAILED: {e}")

def main():
    if not DEPS_AVAILABLE:
        logger.error("Cannot run: missing dependencies")
        return
    
    try:
        client = create_opensearch_client()
        test_vector_queries(client)
        
    except Exception as e:
        logger.error(f"Failed to test vector queries: {e}")

if __name__ == '__main__':
    main()