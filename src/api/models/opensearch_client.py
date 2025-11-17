"""Amazon OpenSearch Serverless 클라이언트"""
import json
import logging
from typing import Any, Dict, List
import boto3
from botocore.exceptions import ClientError
from fastapi import HTTPException

from api.setting import AWS_REGION, OPENSEARCH_ENDPOINT, OPENSEARCH_COLLECTION_NAME, OPENSEARCH_ROLE_ARN, USE_DIRECT_USER_CREDENTIALS
from api.schema import SearchIndex, SearchField, SearchRequest, SearchResponse, SearchResult

logger = logging.getLogger(__name__)

# OpenSearch 클라이언트 (선택적 import)
try:
    from opensearchpy import OpenSearch, RequestsHttpConnection
    from requests_aws4auth import AWS4Auth
    OPENSEARCH_AVAILABLE = True
except ImportError:
    OPENSEARCH_AVAILABLE = False
    logger.warning("OpenSearch dependencies not available. Please install: pip install opensearch-py requests-aws4auth")


class OpenSearchServerlessClient:
    """Amazon OpenSearch Serverless 클라이언트"""
    
    def __init__(self):
        if not OPENSEARCH_AVAILABLE:
            raise ImportError(
                "OpenSearch dependencies not installed. "
                "Run: pip install opensearch-py requests-aws4auth"
            )
        
        if not OPENSEARCH_ENDPOINT:
            raise ValueError("OPENSEARCH_ENDPOINT environment variable is required")
        
        self.client = self._create_client()
        self.collection_name = OPENSEARCH_COLLECTION_NAME
    
    def _get_credentials(self):
        """
        AWS 자격 증명 얻기 - 2가지 방식 지원
        1. OPENSEARCH_ROLE_ARN이 설정된 경우: IAM Role Assume
        2. 기본 방식: 현재 세션의 credentials 사용
        """
        try:
            if USE_DIRECT_USER_CREDENTIALS:
                # 방식 1: 직접 User Credentials 사용
                logger.info("Using direct user credentials (no role assume)")
                session = boto3.Session()
                credentials = session.get_credentials()
                
                if not credentials:
                    raise ValueError("No AWS credentials found")
                
                return credentials
            elif OPENSEARCH_ROLE_ARN:
                # 방식 2: IAM Role Assume
                logger.info(f"Assuming IAM Role: {OPENSEARCH_ROLE_ARN}")
                sts_client = boto3.client('sts', region_name=AWS_REGION)
                
                response = sts_client.assume_role(
                    RoleArn=OPENSEARCH_ROLE_ARN,
                    RoleSessionName='opensearch-serverless-session'
                )
                
                assumed_credentials = response['Credentials']
                
                # Credentials 객체 생성
                from botocore.credentials import Credentials
                return Credentials(
                    access_key=assumed_credentials['AccessKeyId'],
                    secret_key=assumed_credentials['SecretAccessKey'],
                    token=assumed_credentials['SessionToken']
                )
            else:
                # 방식 3: 기본 세션 credentials
                logger.info("Using default session credentials")
                session = boto3.Session()
                credentials = session.get_credentials()
                
                if not credentials:
                    raise ValueError("No AWS credentials found")
                
                return credentials
                
        except Exception as e:
            logger.error(f"Failed to get AWS credentials: {str(e)}")
            raise
    
    def _create_client(self) -> OpenSearch:
        """OpenSearch Serverless 클라이언트 생성"""
        try:
            # AWS 자격 증명 얻기 (2가지 방식 지원)
            credentials = self._get_credentials()
            auth = AWS4Auth(
                credentials.access_key,
                credentials.secret_key,
                AWS_REGION,
                'aoss',  # OpenSearch Serverless 서비스명
                session_token=credentials.token
            )
            
            # 엔드포인트에서 호스트 추출
            host = OPENSEARCH_ENDPOINT.replace('https://', '').replace('http://', '')
            
            client = OpenSearch(
                hosts=[{'host': host, 'port': 443}],
                http_auth=auth,
                use_ssl=True,
                verify_certs=True,
                connection_class=RequestsHttpConnection,
                pool_maxsize=20,
                timeout=30
            )
            
            # 인증 방식 로깅
            if USE_DIRECT_USER_CREDENTIALS:
                auth_method = "Direct User Credentials"
            elif OPENSEARCH_ROLE_ARN:
                auth_method = "IAM Role Assume"
            else:
                auth_method = "Default Session"
                logger.info(f"OpenSearch Serverless client created for: {host} (Auth: {auth_method})")
            return client
            
        except Exception as e:
            logger.error(f"Failed to create OpenSearch client: {str(e)}")
            raise
    
    def create_index(self, index_name: str, index_definition: SearchIndex) -> bool:
        """인덱스 생성"""
        try:
            # Azure 인덱스 정의를 OpenSearch 매핑으로 변환
            mapping = self._azure_index_to_opensearch_mapping(index_definition)
            
            # 디버깅을 위한 매핑 로깅
            logger.info(f"Creating index with mapping: {json.dumps(mapping, indent=2)}")
            
            response = self.client.indices.create(
                index=index_name,
                body=mapping
            )
            
            logger.info(f"Index '{index_name}' created successfully")
            return response.get('acknowledged', False)
            
        except Exception as e:
            logger.error(f"Failed to create index '{index_name}': {str(e)}")
            raise HTTPException(status_code=400, detail=f"Failed to create index: {str(e)}")
    
    def get_index(self, index_name: str) -> Dict[str, Any]:
        """인덱스 정보 조회"""
        try:
            response = self.client.indices.get(index=index_name)
            opensearch_index = response.get(index_name, {})
            
            # OpenSearch 스키마를 Azure AI Search 형식으로 변환
            azure_index = {
                '@odata.context': f"#indexes('{index_name}')",
                '@odata.etag': f'W/"{index_name}"',
                'name': index_name,
                'fields': self._opensearch_mapping_to_azure_fields(opensearch_index.get('mappings', {}).get('properties', {}))
            }
            
            return azure_index
            
        except Exception as e:
            logger.error(f"Failed to get index '{index_name}': {str(e)}")
            raise HTTPException(status_code=404, detail=f"Index not found: {index_name}")
    
    def list_indices(self) -> List[str]:
        """인덱스 목록 조회"""
        try:
            response = self.client.cat.indices(format='json')
            return [idx['index'] for idx in response if not idx['index'].startswith('.')]
        except Exception as e:
            logger.error(f"Failed to list indices: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to list indices: {str(e)}")
    
    def delete_index(self, index_name: str) -> bool:
        """인덱스 삭제"""
        try:
            response = self.client.indices.delete(index=index_name)
            logger.info(f"Index '{index_name}' deleted successfully")
            return response.get('acknowledged', False)
        except Exception as e:
            logger.error(f"Failed to delete index '{index_name}': {str(e)}")
            raise HTTPException(status_code=400, detail=f"Failed to delete index: {str(e)}")
    
    def index_documents(self, index_name: str, documents: List[Dict[str, Any]]) -> Dict[str, Any]:
        """문서 배치 인덱싱"""
        try:
            logger.info(f"Starting document indexing for index: {index_name}")
            logger.info(f"Received {len(documents)} documents")
            
            body = []
            for i, doc in enumerate(documents):
                action = doc.get('@search.action', 'upload')
                doc_copy = {k: v for k, v in doc.items() if not k.startswith('@')}
                
                # 문서 ID 결정 및 처리
                doc_id = doc_copy.get('id') or doc_copy.get('hotelId') or str(hash(str(doc_copy)))
                
                logger.info(f"Processing document {i+1}: ID={doc_id}, action={action}")
                logger.info(f"Document fields: {list(doc_copy.keys())}")
                
                # OpenSearch Serverless에서 ID 충돌 방지
                # 방법 1: _id를 사용하지 않고 자동 생성되도록 함
                if action == 'upload':
                    body.append({'index': {'_index': index_name}})
                    body.append(doc_copy)
                elif action == 'delete':
                    # 삭제는 ID가 필요하므로 별도 처리 필요
                    body.append({'delete': {'_index': index_name, '_id': doc_id}})
                elif action in ['merge', 'mergeOrUpload']:
                    # 업데이트도 ID가 필요하므로 별도 처리 필요
                    body.append({'update': {'_index': index_name, '_id': doc_id}})
                    body.append({'doc': doc_copy, 'doc_as_upsert': action == 'mergeOrUpload'})
            
            if not body:
                logger.warning("No documents to index")
                return {'value': []}
            
            logger.info(f"Sending bulk request with {len(body)} items")
            # OpenSearch Serverless는 refresh=True를 지원하지 않음
            response = self.client.bulk(body=body)
            
            logger.info(f"OpenSearch bulk response: {json.dumps(response, indent=2)}")
            
            # OpenSearch 응답을 Azure 형식으로 변환
            azure_response = {'value': []}
            
            if 'items' in response:
                for item in response['items']:
                    for action, result in item.items():
                        has_error = 'error' in result
                        doc_result = {
                            'key': result.get('_id', '') or f"auto_generated_{len(azure_response['value'])}",
                            'status': not has_error and result.get('result') in ['created', 'updated'],
                            'errorMessage': result.get('error', {}).get('reason') if has_error else None,
                            'statusCode': result.get('status', 200)
                        }
                        azure_response['value'].append(doc_result)
                        
                        if has_error:
                            logger.error(f"Document indexing error: {result.get('error')}")
                        else:
                            logger.info(f"Document {result.get('_id')} indexed successfully: {result.get('result')}")
            
            success_count = sum(1 for item in azure_response['value'] if item['status'])
            failure_count = len(azure_response['value']) - success_count
            logger.info(f"Indexing completed: {success_count} success, {failure_count} failures")
            
            return azure_response
            
        except Exception as e:
            logger.error(f"Failed to index documents: {str(e)}")
            raise HTTPException(status_code=400, detail=f"Failed to index documents: {str(e)}")
    
    def search(self, index_name: str, search_request: SearchRequest) -> SearchResponse:
        """문서 검색"""
        try:
            # Azure 검색 요청을 OpenSearch 쿼리로 변환
            query = self._azure_search_to_opensearch_query(search_request)
            
            response = self.client.search(
                index=index_name,
                body=query
            )
            
            # OpenSearch 응답을 Azure 형식으로 변환
            return self._opensearch_response_to_azure(response, search_request)
            
        except Exception as e:
            logger.error(f"Search failed: {str(e)}")
            raise HTTPException(status_code=400, detail=f"Search failed: {str(e)}")
    
    def count_documents(self, index_name: str) -> int:
        """문서 개수 조회"""
        try:
            response = self.client.count(index=index_name)
            return response.get('count', 0)
        except Exception as e:
            logger.error(f"Failed to count documents: {str(e)}")
            raise HTTPException(status_code=400, detail=f"Failed to count documents: {str(e)}")
    
    def get_all_documents(self, index_name: str, size: int = 100) -> Dict[str, Any]:
        """인덱스의 모든 문서 조회 (디버깅용)"""
        try:
            response = self.client.search(
                index=index_name,
                body={
                    'query': {'match_all': {}},
                    'size': size,
                    'track_total_hits': True
                }
            )
            
            logger.info(f"Found {response['hits']['total']['value']} documents in index {index_name}")
            return response
            
        except Exception as e:
            logger.error(f"Failed to get documents from {index_name}: {str(e)}")
            raise HTTPException(status_code=400, detail=f"Failed to get documents: {str(e)}")
    
    def _azure_index_to_opensearch_mapping(self, azure_index: SearchIndex) -> Dict[str, Any]:
        """Azure 인덱스 정의를 OpenSearch 매핑으로 변환"""
        mapping = {
            'settings': {
                'index': {
                    'knn': True
                }
            },
            'mappings': {
                'properties': {}
            }
        }
        
        logger.info(f"Processing {len(azure_index.fields)} fields for index mapping")
        logger.info(f"Azure index object type: {type(azure_index)}")
        logger.info(f"Azure index fields type: {type(azure_index.fields)}")
        
        if not azure_index.fields:
            logger.error("No fields found in azure_index!")
            return mapping
        
        for i, field in enumerate(azure_index.fields):
            logger.info(f"Processing field {i+1}/{len(azure_index.fields)}: {field.name} (type: {field.type})")
            try:
                field_mapping = self._azure_field_to_opensearch_property(field)
                mapping['mappings']['properties'][field.name] = field_mapping
                logger.info(f"Field {field.name} mapped to: {field_mapping}")
            except Exception as e:
                logger.error(f"Failed to process field {field.name}: {str(e)}")
                raise
        
        logger.info(f"Final mapping properties: {list(mapping['mappings']['properties'].keys())}")
        
        if not mapping['mappings']['properties']:
            logger.error("No properties were mapped! Something is wrong with field processing.")
        
        return mapping
    
    def _azure_field_to_opensearch_property(self, field: SearchField) -> Dict[str, Any]:
        """Azure 필드를 OpenSearch 프로퍼티로 변환"""
        
        logger.info(f"Processing field: {field.name}, type: {field.type}")
        logger.info(f"Field object type: {type(field)}")
        logger.info(f"Field object dict: {field.__dict__ if hasattr(field, '__dict__') else 'No __dict__'}")
        logger.info(f"Field object attributes: {[attr for attr in dir(field) if not attr.startswith('_')]}")
        
        # 기본 속성 체크
        try:
            logger.info(f"field.name: {field.name}")
            logger.info(f"field.type: {field.type}")
        except Exception as e:
            logger.error(f"Cannot access basic field attributes: {e}")
        
        # 벡터 필드 우선 처리
        if field.type == 'Collection(Edm.Single)':
            logger.info(f"Creating vector field: {field.name}")
            # dimensions 속성 체크
            dimensions = None
            if hasattr(field, 'dimensions') and field.dimensions:
                dimensions = field.dimensions
                logger.info(f"Found dimensions attribute: {dimensions}")
            elif hasattr(field, 'vector_search_dimensions') and field.vector_search_dimensions:
                dimensions = field.vector_search_dimensions
                logger.info(f"Found vector_search_dimensions attribute: {dimensions}")
            else:
                dimensions = 1536
                logger.info(f"Using default dimensions: {dimensions}")
                
            return {
                'type': 'knn_vector',
                'dimension': dimensions
            }
        
        # Collection(Edm.String) 처리
        if field.type == 'Collection(Edm.String)':
            logger.info(f"Creating string array field: {field.name}")
            return {'type': 'keyword'}
        
        # 기본 타입 매핑
        type_mapping = {
            'Edm.String': 'text',
            'Edm.Int32': 'integer',
            'Edm.Int64': 'long',
            'Edm.Double': 'double',
            'Edm.Boolean': 'boolean',
            'Edm.DateTimeOffset': 'date'
        }
        
        opensearch_type = type_mapping.get(field.type, 'text')
        logger.info(f"Mapped {field.name} ({field.type}) to OpenSearch type: {opensearch_type}")
        
        if opensearch_type == 'text':
            # 텍스트 필드
            prop = {'type': 'text'}
            
            if field.analyzer:
                # Azure analyzer를 OpenSearch analyzer로 매핑
                analyzer_mapping = {
                    'standard.lucene': 'standard',
                    'keyword.lucene': 'keyword',
                    'simple.lucene': 'simple',
                    'whitespace.lucene': 'whitespace'
                }
                prop['analyzer'] = analyzer_mapping.get(field.analyzer, field.analyzer)
            
            # 필터링/정렬을 위한 keyword 서브필드
            if field.filterable or field.sortable:
                prop['fields'] = {
                    'keyword': {
                        'type': 'keyword',
                        'ignore_above': 256
                    }
                }
            
            return prop
        else:
            # 숫자, 날짜 등 기본 타입
            return {'type': opensearch_type}
    
    def _azure_search_to_opensearch_query(self, search_request: SearchRequest) -> Dict[str, Any]:
        """Azure 검색 요청을 OpenSearch 쿼리로 변환"""
        logger.info(f"Converting Azure search to OpenSearch query: {search_request.__dict__}")
        
        query = {
            'size': search_request.top or 10,
            'from': search_request.skip or 0
        }
        
        # Bool 쿼리 기반으로 구성
        bool_query = {
            'must': [],
            'filter': []
        }
        
        # 기본 텍스트 검색
        if search_request.search and search_request.search != '*':
            if search_request.search_fields:
                # 특정 필드에서 검색
                fields = [f.strip() for f in search_request.search_fields.split(',')]
                bool_query['must'].append({
                    'multi_match': {
                        'query': search_request.search,
                        'fields': fields
                    }
                })
            else:
                # 전체 검색
                bool_query['must'].append({
                    'query_string': {
                        'query': search_request.search
                    }
                })
        
        # 필터 처리
        if search_request.filter:
            try:
                filter_query = self._parse_azure_filter(search_request.filter)
                if filter_query:
                    bool_query['filter'].append(filter_query)
                    logger.info(f"Added filter: {filter_query}")
            except Exception as e:
                logger.error(f"Failed to parse filter '{search_request.filter}': {e}")
                raise HTTPException(status_code=400, detail=f"Invalid filter syntax: {search_request.filter}")
        
        # 벡터 검색 처리
        vector_queries = getattr(search_request, 'vector_queries', None) or getattr(search_request, 'vectors', None)
        if vector_queries:
            logger.info(f"Processing vector queries: {len(vector_queries)} vectors")
            vector_query = vector_queries[0]  # 첫 번째 벡터 쿼리만 사용
            
            vector_field = getattr(vector_query, 'fields', None)
            vector_value = getattr(vector_query, 'vector', None) or getattr(vector_query, 'value', None)
            vector_k = getattr(vector_query, 'k_nearest_neighbors', None) or getattr(vector_query, 'k', None)
            
            logger.info(f"Vector query - field: {vector_field}, k: {vector_k}, vector_len: {len(vector_value) if vector_value else 0}")
            
            if vector_field and vector_value and vector_k:
                if bool_query['must'] or bool_query['filter']:
                    # 하이브리드 검색 (텍스트 + 벡터)
                    # OpenSearch Serverless에서는 벡터 검색을 우선하고 텍스트 필터를 post_filter에 적용
                    logger.info("Creating hybrid search (vector primary + text filter)")
                    query['query'] = {
                        'knn': {
                            vector_field: {
                                'vector': vector_value,
                                'k': vector_k
                            }
                        }
                    }
                    # 텍스트 검색 조건을 post_filter로 처리
                    if bool_query['must'] or bool_query['filter']:
                        post_filter = {'bool': {}}
                        if bool_query['must']:
                            post_filter['bool']['must'] = bool_query['must']
                        if bool_query['filter']:
                            post_filter['bool']['filter'] = bool_query['filter']
                        query['post_filter'] = post_filter
                        logger.info(f"Added post_filter: {post_filter}")
                else:
                    # 벡터 검색만 - 올바른 KNN 쿼리 구문 사용
                    logger.info("Creating vector-only search with KNN query")
                    query['query'] = {
                        'knn': {
                            vector_field: {
                                'vector': vector_value,
                                'k': vector_k
                            }
                        }
                    }
            else:
                logger.error(f"Invalid vector query parameters - field: {vector_field}, value: {vector_value}, k: {vector_k}")
                raise HTTPException(status_code=400, detail="Invalid vector query parameters")
        
        # 벡터 검색이 없는 경우에만 일반 bool 쿼리 사용
        if not vector_queries:
            if bool_query['must'] or bool_query['filter']:
                query['query'] = {'bool': bool_query}
            else:
                query['query'] = {'match_all': {}}
        
        # 정렬
        if search_request.order_by:
            sort_fields = []
            for field_spec in search_request.order_by.split(','):
                field_spec = field_spec.strip()
                if field_spec.endswith(' desc'):
                    field_name = field_spec[:-5].strip()
                    # text 필드의 경우 .keyword 서브필드 사용
                    if field_name in ['owning_object', 'owning_user', 'owning_group', 'owning_file', 'content']:
                        sort_fields.append({f"{field_name}.keyword": {'order': 'desc'}})
                    else:
                        sort_fields.append({field_name: {'order': 'desc'}})
                else:
                    field_name = field_spec.replace(' asc', '').strip()
                    if field_name in ['owning_object', 'owning_user', 'owning_group', 'owning_file', 'content']:
                        sort_fields.append({f"{field_name}.keyword": {'order': 'asc'}})
                    else:
                        sort_fields.append({field_name: {'order': 'asc'}})
            query['sort'] = sort_fields
        
        # 필드 선택
        if search_request.select:
            query['_source'] = [f.strip() for f in search_request.select.split(',')]
        
        # 총 개수 추적
        if search_request.include_total_count:
            query['track_total_hits'] = True
        
        logger.info(f"Final OpenSearch query: {json.dumps(query, indent=2)}")
        return query
    
    def _opensearch_response_to_azure(self, opensearch_response: Dict[str, Any], 
                                    original_request: SearchRequest) -> SearchResponse:
        """OpenSearch 응답을 Azure 형식으로 변환"""
        hits = opensearch_response.get('hits', {})
        
        # 검색 결과 변환
        results = []
        for hit in hits.get('hits', []):
            result_data = hit.get('_source', {})
            result_data['@search.score'] = hit.get('_score', 0.0)
            results.append(SearchResult(**result_data))
        
        # 응답 구성
        response_data = {
            '@odata.context': f"#docs",
            'value': results
        }
        
        # 총 개수 추가
        if original_request.include_total_count:
            total = hits.get('total', {})
            if isinstance(total, dict):
                response_data['@odata.count'] = total.get('value', 0)
            else:
                response_data['@odata.count'] = total
        
        return SearchResponse(**response_data)
    
    def _opensearch_mapping_to_azure_fields(self, properties: Dict[str, Any]) -> List[Dict[str, Any]]:
        """OpenSearch 매핑을 Azure AI Search 필드로 변환"""
        azure_fields = []
        
        for field_name, field_props in properties.items():
            field_type = field_props.get('type', 'text')
            
            # OpenSearch 타입을 Azure 타입으로 매핑
            type_mapping = {
                'text': 'Edm.String',
                'keyword': 'Edm.String',
                'integer': 'Edm.Int32',
                'long': 'Edm.Int64',
                'double': 'Edm.Double',
                'boolean': 'Edm.Boolean',
                'date': 'Edm.DateTimeOffset',
                'knn_vector': 'Collection(Edm.Single)'
            }
            
            azure_type = type_mapping.get(field_type, 'Edm.String')
            
            azure_field = {
                'name': field_name,
                'type': azure_type,
                'searchable': field_type in ['text'],
                'filterable': field_type in ['keyword', 'integer', 'long', 'double', 'boolean', 'date'],
                'sortable': field_type in ['keyword', 'integer', 'long', 'double', 'date'],
                'facetable': False,
                'retrievable': True,
                'key': False  # 기본값, 실제로는 더 정교한 설정 필요
            }
            
            # 벡터 필드 추가 정보
            if field_type == 'knn_vector':
                azure_field['dimensions'] = field_props.get('dimension', 1536)
                azure_field['vectorSearchProfile'] = 'default-vector-profile'
            
            azure_fields.append(azure_field)
        
        return azure_fields
    
    def _parse_azure_filter(self, filter_str: str) -> Dict[str, Any]:
        """Azure 필터 구문을 OpenSearch 쿼리로 변환"""
        logger.info(f"Parsing Azure filter: {filter_str}")
        
        # 간단한 Azure OData 필터 파싱
        # 예: "owning_user eq 'admin@company.com'"
        # 예: "rating gt 4.0"
        # 예: "category eq 'Education' and rating gt 4.0"
        
        if not filter_str:
            return None
        
        # AND 연산자로 분할
        conditions = []
        parts = filter_str.split(' and ')
        
        for part in parts:
            part = part.strip()
            condition = self._parse_single_filter_condition(part)
            if condition:
                conditions.append(condition)
        
        if not conditions:
            return None
        elif len(conditions) == 1:
            return conditions[0]
        else:
            return {
                'bool': {
                    'must': conditions
                }
            }
    
    def _parse_single_filter_condition(self, condition: str) -> Dict[str, Any]:
        """단일 필터 조건을 OpenSearch 쿼리로 변환"""
        condition = condition.strip()
        
        # eq (equals) 처리
        if ' eq ' in condition:
            parts = condition.split(' eq ', 1)
            field = parts[0].strip()
            value = parts[1].strip().strip("'\"")
            
            # text 필드는 .keyword 서브필드 사용
            if field in ['owning_object', 'owning_user', 'owning_group', 'owning_file', 'content']:
                field = f"{field}.keyword"
            
            return {
                'term': {
                    field: value
                }
            }
        
        # gt (greater than) 처리
        elif ' gt ' in condition:
            parts = condition.split(' gt ', 1)
            field = parts[0].strip()
            value = float(parts[1].strip())
            
            return {
                'range': {
                    field: {
                        'gt': value
                    }
                }
            }
        
        # lt (less than) 처리
        elif ' lt ' in condition:
            parts = condition.split(' lt ', 1)
            field = parts[0].strip()
            value = float(parts[1].strip())
            
            return {
                'range': {
                    field: {
                        'lt': value
                    }
                }
            }
        
        # ge (greater than or equal) 처리
        elif ' ge ' in condition:
            parts = condition.split(' ge ', 1)
            field = parts[0].strip()
            value = float(parts[1].strip())
            
            return {
                'range': {
                    field: {
                        'gte': value
                    }
                }
            }
        
        # le (less than or equal) 처리
        elif ' le ' in condition:
            parts = condition.split(' le ', 1)
            field = parts[0].strip()
            value = float(parts[1].strip())
            
            return {
                'range': {
                    field: {
                        'lte': value
                    }
                }
            }
        
        else:
            logger.warning(f"Unsupported filter condition: {condition}")
            return None
