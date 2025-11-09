from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Optional, Union
from api.models.azure_bedrock import azure_bedrock_model
from api.schema import ChatRequest, EmbeddingsRequest, Model, Models
from api.utils.azure_mapper import AzureAPIVersionHandler
from api.auth import azure_api_key_auth

router = APIRouter(
    dependencies=[Depends(azure_api_key_auth)],
)
azure_handler = AzureAPIVersionHandler()

class Message(BaseModel):
    role: str
    content: str

class ChatCompletionRequest(BaseModel):
    messages: List[Message]
    max_tokens: Optional[int] = None
    temperature: Optional[float] = None
    top_p: Optional[float] = None
    tools: Optional[List[dict]] = None

class AzureEmbeddingRequest(BaseModel):
    input: Union[str, List[str]]

@router.post("/openai/deployments/{model}/chat/completions")
async def azure_style_chat_completion(
    model: str,
    request: ChatCompletionRequest,
    api_version: str = Query("2024-02-15-preview", alias="api-version"),
    stream: bool = Query(False, description="If true, return a streaming response")
):
    """Azure-style chat completion endpoint.

    Uses a single route for both streaming and non-streaming behavior. Clients can
    set the query param `stream=true` to get a streaming response.
    """
    chat_request = ChatRequest(**request.dict(), model=model, stream=stream)

    if stream:
        return StreamingResponse(
            content=azure_bedrock_model.azure_chat_stream(model, chat_request, api_version),
            media_type="text/event-stream"
        )
    return await azure_bedrock_model.azure_chat(model, chat_request, api_version)

@router.post("/openai/deployments/{model}/embeddings")
async def azure_style_embeddings(
    model: str,
    request: AzureEmbeddingRequest,
    api_version: str = Query("2024-02-15-preview", alias="api-version")
):
    # request.dict()에서 model 필드를 제거하고 URL에서 가져온 model을 사용
    request_dict = request.dict()
    request_dict['model'] = model  # URL에서 가져온 모델로 대체
    embedding_request = EmbeddingsRequest(**request_dict)
    return azure_bedrock_model.azure_embed(model, embedding_request, api_version)

@router.get("/openai/deployments", response_model=Models)
async def list_azure_deployments(
    api_version: str = Query(..., alias="api-version")
):
    azure_models = azure_handler.get_azure_models(api_version)
    model_list = [Model(id=model_id) for model_id in azure_models]
    return Models(data=model_list)

@router.get("/openai/deployments/{model_id}", response_model=Model)
async def get_azure_deployment(
    model_id: str,
    api_version: str = Query(..., alias="api-version")
):
    try:
        azure_handler.get_bedrock_config(api_version, model_id)
        return Model(id=model_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Model not found")