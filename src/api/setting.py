import os
from pathlib import Path

# .env 파일 로드
try:
    from dotenv import load_dotenv
    # src 폴더의 .env 파일 찾기
    env_path = Path(__file__).parent.parent / '.env'
    print(f"Looking for .env file at: {env_path}")
    print(f".env file exists: {env_path.exists()}")
    
    if env_path.exists():
        result = load_dotenv(dotenv_path=env_path)
        print(f"dotenv load result: {result}")
        print(f"OPENSEARCH_ENDPOINT after load: {os.environ.get('OPENSEARCH_ENDPOINT')}")
    else:
        print("Trying to load .env from current directory")
        load_dotenv()
except ImportError as e:
    print(f"python-dotenv not installed: {e}")

DEFAULT_API_KEYS = "bedrock"

API_ROUTE_PREFIX = os.environ.get("API_ROUTE_PREFIX", "/api/v1")

TITLE = "Amazon Bedrock Proxy APIs"
SUMMARY = "OpenAI-Compatible RESTful APIs for Amazon Bedrock"
VERSION = "0.1.0"
DESCRIPTION = """
Use OpenAI-Compatible RESTful APIs for Amazon Bedrock models.
"""

DEBUG = os.environ.get("DEBUG", "false").lower() != "false"
AWS_REGION = os.environ.get("AWS_REGION", "ap-northeast-1")
AWS_REGION_VISION = os.environ.get("AWS_REGION_VISION", "us-east-1")
DEFAULT_MODEL = os.environ.get("DEFAULT_MODEL", "apac.anthropic.claude-sonnet-4-20250514-v1:0")
DEFAULT_EMBEDDING_MODEL = os.environ.get("DEFAULT_EMBEDDING_MODEL", "amazon.titan-embed-text-v2:0")
ENABLE_CROSS_REGION_INFERENCE = os.environ.get("ENABLE_CROSS_REGION_INFERENCE", "true").lower() != "false"

# OpenSearch Serverless 설정
OPENSEARCH_ENDPOINT = os.environ.get("OPENSEARCH_ENDPOINT")
OPENSEARCH_COLLECTION_NAME = os.environ.get("OPENSEARCH_COLLECTION_NAME", "bedrock-search")
DEFAULT_SEARCH_INDEX = os.environ.get("DEFAULT_SEARCH_INDEX", "documents")
OPENSEARCH_ROLE_ARN = os.environ.get("OPENSEARCH_ROLE_ARN")
USE_DIRECT_USER_CREDENTIALS = os.environ.get("USE_DIRECT_USER_CREDENTIALS", "false").lower() == "true"
