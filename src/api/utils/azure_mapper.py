import base64
import requests
from typing import List

class AzureAPIVersionHandler:
    """Azure API-version을 Bedrock 설정으로 매핑"""
    VERSION_MAPPING = {
        "2023-05-15": {
            "models": {
                "gpt-35-turbo": "apac.anthropic.claude-3-sonnet-20240229-v1:0",
                "gpt-4": "global.anthropic.claude-sonnet-4-5-20250929-v1:0",
                "text-embedding-ada-002": "amazon.titan-embed-text-v1",
            },
            "anthropic_version": "bedrock-2023-05-31",
            "features": ["chat", "streaming", "embedding"]
        },
        "2023-12-01-preview": {
            "models": {
                "gpt-35-turbo": "apac.anthropic.claude-3-sonnet-20240229-v1:0",
                "gpt-4": "global.anthropic.claude-sonnet-4-5-20250929-v1:0",
                "gpt-4-vision-preview": "apac.anthropic.claude-3-opus-20240229-v1:0",
                "text-embedding-ada-002": "amazon.titan-embed-text-v1",
                "vision-embedding": "twelvelabs.marengo-embed-3-0-v1:0",
            },
            "anthropic_version": "bedrock-2023-05-31",
            "features": ["chat", "streaming", "vision", "embedding"]
        },
        "2024-02-15-preview": {
            "models": {
                "gpt-35-turbo": "apac.anthropic.claude-3-sonnet-20240229-v1:0",
                "gpt-4": "apac.anthropic.claude-sonnet-4-20250514-v1:0",
                "gpt-4-vision-preview": "apac.anthropic.claude-3-opus-20240229-v1:0",
                "text-embedding-ada-002": "amazon.titan-embed-text-v1",
                "vision-embedding": "twelvelabs.marengo-embed-3-0-v1:0",
            },
            "anthropic_version": "bedrock-2023-05-31",
            "features": ["chat", "streaming", "vision", "tools", "embedding"]
        },
        "2024-05-01-preview": {
            "models": {
                "gpt-35-turbo": "apac.anthropic.claude-3-sonnet-20240229-v1:0",
                "gpt-4": "global.anthropic.claude-sonnet-4-5-20250929-v1:0",
                "gpt-4-vision-preview": "apac.anthropic.claude-3-opus-20240229-v1:0",
                "text-embedding-ada-002": "amazon.titan-embed-text-v1",
                "vision-embedding": "amazon.titan-embed-image-v1",
            },
            "anthropic_version": "bedrock-2023-05-31",
            "features": ["chat", "streaming", "vision", "tools", "enhanced_streaming", "embedding"]
        }
    }

    def get_azure_models(self, api_version: str) -> List[str]:
        """주어진 API 버전에 대한 Azure 모델 목록 반환"""
        config = self.VERSION_MAPPING.get(api_version, {})
        return list(config.get("models", {}).keys())

    def get_bedrock_config(self, api_version: str, model: str) -> dict:
        """Azure API-version과 모델을 Bedrock 설정으로 변환"""
        if api_version not in self.VERSION_MAPPING:
            # 기본값 사용
            api_version = "2024-02-15-preview"
        
        config = self.VERSION_MAPPING[api_version]
        
        if model not in config["models"]:
            raise ValueError(f"Unsupported model: {model} for API version: {api_version}")
        
        bedrock_model_id = config["models"][model]
        
        return {
            "model_id": bedrock_model_id,
            "anthropic_version": config["anthropic_version"],
            "features": config["features"]
        }

    def transform_request(self, azure_request: dict, api_version: str, model: str) -> tuple:
        """API 버전과 모델에 따라 요청 변환"""
        try:
            config = self.get_bedrock_config(api_version, model)
            
            bedrock_request = {
                "max_tokens": azure_request.get("max_tokens", 4096),
                "temperature": azure_request.get("temperature", 1.0),
                "top_p": azure_request.get("top_p") if azure_request.get("top_p") is not None else 1.0
            }

            # 요청 유형에 따른 처리
            if config["model_id"].startswith("anthropic.") or config["model_id"].startswith("apac.anthropic.") or config["model_id"].startswith("global.anthropic."):
                # Chat 모델 - 메시지 처리
                messages = azure_request.get("messages", [])
                if not messages:
                    raise ValueError("Messages field is required for chat models")
                bedrock_request["messages"] = messages
            elif config["model_id"].startswith("amazon.titan-embed-image"):
                # Titan 이미지 임베딩 모델
                input_data = azure_request.get("input", "")
                if not input_data:
                    raise ValueError("Input field is required for image embedding models")
                bedrock_request["input"] = self.prepare_image_input(input_data)
            elif config["model_id"].startswith("twelvelabs"):
                # TwelveLabs 이미지 임베딩 모델
                input_data = azure_request.get("input", "")
                if not input_data:
                    raise ValueError("Input field is required for image embedding models")
                bedrock_request["input"] = self.prepare_image_input(input_data)
            elif config["model_id"].startswith("amazon.titan-embed"):
                # Titan 텍스트 임베딩 모델
                input_data = azure_request.get("input", "")
                if not input_data:
                    raise ValueError("Input field is required for embedding models")
                bedrock_request["input"] = input_data
            elif config["model_id"].startswith("cohere.embed"):
                # Cohere 임베딩 모델
                input_data = azure_request.get("input", "")
                if not input_data:
                    raise ValueError("Input field is required for embedding models")
                if "image" in config["model_id"]:
                    # 이미지 임베딩 모델 - 이미지 데이터 처리
                    bedrock_request["input"] = self.prepare_image_input(input_data)
                else:
                    # 텍스트 임베딩 모델 - 텍스트 데이터 처리
                    bedrock_request["input"] = input_data

            # API 버전별 기능 지원
            if "tools" in config["features"] and "tools" in azure_request and azure_request["tools"]:
                bedrock_request["tools"] = self.convert_tools(azure_request["tools"])
            
            if "vision" in config["features"] and (config["model_id"].startswith("anthropic.") or config["model_id"].startswith("apac.anthropic.") or config["model_id"].startswith("global.anthropic.")):
                # Vision 메시지 처리 (Claude 모델용)
                bedrock_request["messages"] = self.convert_vision_messages(messages)

            return bedrock_request, config["model_id"]
        except Exception as e:
            raise ValueError(f"Failed to transform request: {str(e)}")

    def prepare_image_input(self, input_data):
        """이미지 입력 데이터 준비"""
        if isinstance(input_data, str):
            if input_data.startswith('http'):
                # URL에서 이미지 다운로드
                try:
                    response = requests.get(input_data, timeout=10)
                    response.raise_for_status()
                    return base64.b64encode(response.content).decode()
                except Exception as e:
                    raise ValueError(f"Failed to download image from URL: {str(e)}")
            elif input_data.startswith('data:image'):
                # data:image/jpeg;base64,... 형식 처리
                try:
                    # data: prefix 제거하고 base64 데이터만 추출
                    base64_data = input_data.split(',')[1]
                    # 유효한 base64인지 확인
                    base64.b64decode(base64_data)
                    return base64_data
                except Exception as e:
                    raise ValueError(f"Invalid base64 image data: {str(e)}")
            else:
                # 이미 base64 인코딩된 문자열로 가정
                try:
                    base64.b64decode(input_data)
                    return input_data
                except Exception as e:
                    raise ValueError(f"Invalid base64 string: {str(e)}")
        elif isinstance(input_data, bytes):
            # 바이트 데이터를 base64로 인코딩
            return base64.b64encode(input_data).decode()
        else:
            raise ValueError(f"Unsupported input type for image embedding: {type(input_data)}")

    def convert_tools(self, azure_tools: list) -> list:
        """Azure Function Calling을 Bedrock Tools로 변환"""
        bedrock_tools = []
        for tool in azure_tools:
            if tool.get("type") == "function":
                bedrock_tools.append({
                    "name": tool["function"]["name"],
                    "description": tool["function"]["description"],
                    "input_schema": tool["function"]["parameters"]
                })
        return bedrock_tools

    def convert_vision_messages(self, messages: list) -> list:
        """Vision 메시지 형식 변환"""
        converted = []
        for msg in messages:
            if isinstance(msg.get("content"), list):
                # Multi-modal content
                content_blocks = []
                for item in msg["content"]:
                    if item["type"] == "text":
                        content_blocks.append({
                            "type": "text",
                            "text": item["text"]
                        })
                    elif item["type"] == "image_url":
                        # Azure 이미지 URL을 Bedrock 형식으로 변환
                        image_url = item["image_url"]["url"]
                        if image_url.startswith("data:"):
                            # Base64 이미지
                            image_data = image_url.split(",")[1]
                        else:
                            # URL에서 이미지 다운로드
                            response = requests.get(image_url)
                            image_data = base64.b64encode(response.content).decode()
                        content_blocks.append({
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/jpeg",
                                "data": image_data
                            }
                        })
                converted.append({
                    "role": msg["role"],
                    "content": content_blocks
                })
            else:
                # 일반 텍스트 메시지
                converted.append(msg)
        return converted