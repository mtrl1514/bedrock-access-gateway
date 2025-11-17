import time
from typing import Iterable, Literal

from pydantic import BaseModel, Field

from api.setting import DEFAULT_MODEL


class Model(BaseModel):
    id: str
    created: int = Field(default_factory=lambda: int(time.time()))
    object: str | None = "model"
    owned_by: str | None = "bedrock"


class Models(BaseModel):
    object: str | None = "list"
    data: list[Model] = []


class ResponseFunction(BaseModel):
    name: str | None = None
    arguments: str


class ToolCall(BaseModel):
    index: int | None = None
    id: str | None = None
    type: Literal["function"] = "function"
    function: ResponseFunction


class TextContent(BaseModel):
    type: Literal["text"] = "text"
    text: str


class ImageUrl(BaseModel):
    url: str
    detail: str | None = "auto"


class ImageContent(BaseModel):
    type: Literal["image_url"] = "image"
    image_url: ImageUrl


class SystemMessage(BaseModel):
    name: str | None = None
    role: Literal["system"] = "system"
    content: str


class UserMessage(BaseModel):
    name: str | None = None
    role: Literal["user"] = "user"
    content: str | list[TextContent | ImageContent]


class AssistantMessage(BaseModel):
    name: str | None = None
    role: Literal["assistant"] = "assistant"
    content: str | list[TextContent | ImageContent] | None = None
    tool_calls: list[ToolCall] | None = None


class ToolMessage(BaseModel):
    role: Literal["tool"] = "tool"
    content: str
    tool_call_id: str


class Function(BaseModel):
    name: str
    description: str | None = None
    parameters: object


class Tool(BaseModel):
    type: Literal["function"] = "function"
    function: Function


class StreamOptions(BaseModel):
    include_usage: bool = True


class ChatRequest(BaseModel):
    messages: list[SystemMessage | UserMessage | AssistantMessage | ToolMessage]
    model: str = DEFAULT_MODEL
    frequency_penalty: float | None = Field(default=0.0, le=2.0, ge=-2.0)  # Not used
    presence_penalty: float | None = Field(default=0.0, le=2.0, ge=-2.0)  # Not used
    stream: bool | None = False
    stream_options: StreamOptions | None = None
    temperature: float | None = Field(default=1.0, le=2.0, ge=0.0)
    top_p: float | None = Field(default=1.0, le=1.0, ge=0.0)
    user: str | None = None  # Not used
    max_tokens: int | None = 2048
    max_completion_tokens: int | None = None
    reasoning_effort: Literal["low", "medium", "high"] | None = None
    n: int | None = 1  # Not used
    tools: list[Tool] | None = None
    tool_choice: str | object = "auto"
    stop: list[str] | str | None = None


class Usage(BaseModel):
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


class ChatResponseMessage(BaseModel):
    # tool_calls
    role: Literal["assistant"] | None = None
    content: str | None = None
    tool_calls: list[ToolCall] | None = None
    reasoning_content: str | None = None


class BaseChoice(BaseModel):
    index: int | None = 0
    finish_reason: str | None = None
    logprobs: dict | None = None


class Choice(BaseChoice):
    message: ChatResponseMessage


class ChoiceDelta(BaseChoice):
    delta: ChatResponseMessage


class BaseChatResponse(BaseModel):
    # id: str = Field(default_factory=lambda: "chatcmpl-" + str(uuid.uuid4())[:8])
    id: str
    created: int = Field(default_factory=lambda: int(time.time()))
    model: str
    system_fingerprint: str = "fp"


class ChatResponse(BaseChatResponse):
    choices: list[Choice]
    object: Literal["chat.completion"] = "chat.completion"
    usage: Usage


class ChatStreamResponse(BaseChatResponse):
    choices: list[ChoiceDelta]
    object: Literal["chat.completion.chunk"] = "chat.completion.chunk"
    usage: Usage | None = None


class EmbeddingsRequest(BaseModel):
    input: str | list[str] | Iterable[int | Iterable[int]]
    model: str
    encoding_format: Literal["float", "base64"] = "float"
    dimensions: int | None = None  # not used.
    user: str | None = None  # not used.


class Embedding(BaseModel):
    object: Literal["embedding"] = "embedding"
    embedding: list[float] | bytes
    index: int


class EmbeddingsUsage(BaseModel):
    prompt_tokens: int
    total_tokens: int


class EmbeddingsResponse(BaseModel):
    object: Literal["list"] = "list"
    data: list[Embedding]
    model: str
    usage: EmbeddingsUsage


class ErrorMessage(BaseModel):
    message: str


class Error(BaseModel):
    error: ErrorMessage


# =============================================================================
# Azure AI Search 호환 스키마
# =============================================================================

class SearchField(BaseModel):
    """검색 인덱스 필드"""
    name: str
    type: str
    key: bool = False
    searchable: bool = False
    filterable: bool = False
    sortable: bool = False
    facetable: bool = False
    retrievable: bool = True
    analyzer: str | None = None
    # 벡터 검색 지원 - 여러 필드명 지원
    dimensions: int | None = None  # JSON에서 직접 사용
    vector_search_dimensions: int | None = Field(None, alias="vectorSearchDimensions")
    vector_search_profile: str | None = Field(None, alias="vectorSearchProfile")
    vector_search_profile_name: str | None = Field(None, alias="vectorSearchProfileName")


class VectorSearchAlgorithmConfig(BaseModel):
    """벡터 검색 알고리즘 설정"""
    name: str
    kind: Literal["hnsw"] = "hnsw"
    hnsw_parameters: dict | None = Field(None, alias="hnswParameters")


class VectorSearchProfile(BaseModel):
    """벡터 검색 프로필"""
    name: str
    algorithm_configuration_name: str = Field(alias="algorithmConfigurationName")
    vectorizer: str | None = None


class VectorSearch(BaseModel):
    """벡터 검색 설정"""
    algorithms: list[VectorSearchAlgorithmConfig] | None = None
    profiles: list[VectorSearchProfile] | None = None


class SearchIndex(BaseModel):
    """검색 인덱스"""
    name: str
    fields: list[SearchField]
    vector_search: VectorSearch | None = Field(None, alias="vectorSearch")
    e_tag: str | None = Field(None, alias="@odata.etag")


class IndexAction(BaseModel):
    """문서 인덱싱 액션"""
    search_action: Literal["upload", "merge", "mergeOrUpload", "delete"] = Field(alias="@search.action")
    
    class Config:
        extra = "allow"  # 동적 필드 허용


class IndexBatch(BaseModel):
    """배치 인덱싱 요청"""
    value: list[IndexAction]


class IndexingResult(BaseModel):
    """인덱싱 결과"""
    key: str
    status: bool
    error_message: str | None = Field(None, alias="errorMessage")
    status_code: int = Field(alias="statusCode")


class IndexBatchResult(BaseModel):
    """배치 인덱싱 결과"""
    value: list[IndexingResult]


class VectorizedQuery(BaseModel):
    """벡터 쿼리"""
    vector: list[float] = Field(alias="value")
    k_nearest_neighbors: int = Field(alias="k")
    fields: str


class SearchRequest(BaseModel):
    """검색 요청"""
    search: str | None = None
    search_fields: str | None = Field(None, alias="searchFields")
    select: str | None = None
    filter: str | None = None
    order_by: str | None = Field(None, alias="orderby")
    top: int | None = None
    skip: int | None = None
    include_total_count: bool | None = Field(None, alias="includeTotalCount")
    vectors: list[VectorizedQuery] | None = None  # JSON과 매칭
    vector_queries: list[VectorizedQuery] | None = Field(None, alias="vectorQueries")


class SearchResult(BaseModel):
    """검색 결과"""
    search_score: float | None = Field(None, alias="@search.score")
    
    class Config:
        extra = "allow"  # 동적 필드 허용


class SearchResponse(BaseModel):
    """검색 응답"""
    odata_context: str = Field(alias="@odata.context")
    odata_count: int | None = Field(None, alias="@odata.count")
    value: list[SearchResult]
