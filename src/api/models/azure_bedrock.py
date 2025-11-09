import logging
from fastapi import HTTPException
from api.utils.azure_mapper import AzureAPIVersionHandler
from api.schema import ChatRequest, ChatResponse, ChatStreamResponse, EmbeddingsRequest, EmbeddingsResponse
from api.models.bedrock import BedrockModel, get_embeddings_model
from typing import AsyncIterable

logger = logging.getLogger(__name__)

class AzureBedrockModel:
    def __init__(self):
        self.azure_handler = AzureAPIVersionHandler()
        self.bedrock_model = BedrockModel()

    async def azure_chat(self, model: str, chat_request: ChatRequest, api_version: str) -> ChatResponse:
        try:
            logger.info(f"Processing Azure chat request - model: {model}, api_version: {api_version}")
            logger.info(f"Original chat_request: {chat_request.dict()}")
            
            transform_result = self.azure_handler.transform_request(
                chat_request.dict(), api_version, model
            )
            
            if not transform_result or len(transform_result) != 2:
                raise ValueError(f"Invalid transform result: {transform_result}")
                
            bedrock_request, bedrock_model_id = transform_result
            logger.info(f"Transform result - bedrock_request: {bedrock_request}, model_id: {bedrock_model_id}")
            
            if not bedrock_model_id:
                raise ValueError("Bedrock model ID is None or empty")
                
            logger.info(f"Azure model '{model}' mapped to Bedrock model '{bedrock_model_id}'")
            
            # 기존 chat_request의 값들을 유지하면서 변환된 값들로 업데이트
            chat_dict = chat_request.dict()
            if bedrock_request:
                chat_dict.update(bedrock_request)
            chat_dict['model'] = bedrock_model_id
            
            # None 값들을 제거하거나 기본값으로 설정
            if chat_dict.get('top_p') is None:
                chat_dict['top_p'] = 1.0
            if chat_dict.get('temperature') is None:
                chat_dict['temperature'] = 1.0
            
            logger.info(f"Final chat_dict: {chat_dict}")
            
            bedrock_chat_request = ChatRequest(**chat_dict)
            return await self.bedrock_model.chat(bedrock_chat_request)
        except ValueError as e:
            logger.error(f"Model mapping error: {str(e)}")
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            logger.error(f"Bedrock API error: {str(e)}", exc_info=True)
            raise HTTPException(status_code=500, detail=str(e))

    async def azure_chat_stream(self, model: str, chat_request: ChatRequest, api_version: str) -> AsyncIterable[bytes]:
        try:
            bedrock_request, bedrock_model_id = self.azure_handler.transform_request(
                chat_request.dict(), api_version, model
            )
            
            # 기존 chat_request의 값들을 유지하면서 변환된 값들로 업데이트
            chat_dict = chat_request.dict()
            chat_dict.update(bedrock_request)
            chat_dict['model'] = bedrock_model_id
            
            bedrock_chat_request = ChatRequest(**chat_dict)
            async for chunk in self.bedrock_model.chat_stream(bedrock_chat_request):
                yield chunk
        except ValueError as e:
            error_event = self.create_error_response(str(e))
            yield self.bedrock_model.stream_response_to_bytes(error_event)

    def create_error_response(self, error_message: str) -> ChatStreamResponse:
        return ChatStreamResponse(
            id="error",
            object="chat.completion.chunk",
            created=0,
            model="error",
            choices=[
                {
                    "delta": {"content": error_message},
                    "index": 0,
                    "finish_reason": "error"
                }
            ]
        )

    def azure_embed(self, model: str, embeddings_request: EmbeddingsRequest, api_version: str) -> EmbeddingsResponse:
        try:
            logger.info(f"Processing Azure embedding request - model: {model}, api_version: {api_version}")
            logger.info(f"Original embeddings_request: {embeddings_request.dict()}")
            
            transform_result = self.azure_handler.transform_request(
                embeddings_request.dict(), api_version, model
            )
            
            if not transform_result or len(transform_result) != 2:
                raise ValueError(f"Invalid transform result: {transform_result}")
                
            bedrock_request, bedrock_model_id = transform_result
            logger.info(f"Transform result - bedrock_request: {bedrock_request}, model_id: {bedrock_model_id}")
            
            if not bedrock_model_id:
                raise ValueError("Bedrock model ID is None or empty")
                
            logger.info(f"Azure model '{model}' mapped to Bedrock model '{bedrock_model_id}'")
            
            # 기존 embeddings_request의 값들을 유지하면서 변환된 값들로 업데이트
            embed_dict = embeddings_request.dict()
            if bedrock_request:
                embed_dict.update(bedrock_request)
            embed_dict['model'] = bedrock_model_id
            
            logger.info(f"Final embed_dict: {embed_dict}")
            
            bedrock_embeddings_request = EmbeddingsRequest(**embed_dict)
            embeddings_model = get_embeddings_model(bedrock_model_id)
            return embeddings_model.embed(bedrock_embeddings_request)
        except ValueError as e:
            logger.error(f"Model mapping error: {str(e)}")
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            logger.error(f"Bedrock API error: {str(e)}", exc_info=True)
            raise HTTPException(status_code=500, detail=str(e))

azure_bedrock_model = AzureBedrockModel()