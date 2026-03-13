from pydantic import BaseModel, Field
from typing import Optional, List, Literal


class TTSRequest(BaseModel):
    """TTS请求"""

    text: str
    voice: Optional[str] = None
    model: Optional[str] = None


class TTSStreamRequest(BaseModel):
    """流式TTS请求"""

    text_chunks: List[str]
    voice: Optional[str] = None
    model: Optional[str] = None


class ChatRequest(BaseModel):
    """聊天请求"""

    message: str


class CompositionGradeRequest(BaseModel):
    """作文批改请求"""

    essay_text: str
    exam_type: Literal["ielts", "cet-4", "cet-6", "kaoyan"]
    task_type: Literal[
        "data_graph",
        "image_drawing",
        "process_map",
        "opinion_essay",
        "letter",
        "notice",
    ]
    topic: str
    user_id: str
    thread_id: Optional[str] = None
    session_id: Optional[str] = None


class CompositionGradeResponse(BaseModel):
    """作文批改响应"""

    thread_id: str
    scores: dict[str, float]
    band_score: float
    score_explanation: Optional[str] = None
    errors: list[dict] = Field(default_factory=list)
    suggestions: list[str] = Field(default_factory=list)
    current_step: Optional[str] = None
    needs_revision: bool = False


class CompositionReviseRequest(BaseModel):
    """作文改稿请求"""

    revised_essay: str
    thread_id: str
    session_id: Optional[str] = None
    user_id: Optional[str] = None
    topic: Optional[str] = None
    exam_type: Optional[Literal["ielts", "cet-4", "cet-6", "kaoyan"]] = None
    task_type: Optional[
        Literal[
            "data_graph",
            "image_drawing",
            "process_map",
            "opinion_essay",
            "letter",
            "notice",
        ]
    ] = None


class CompositionReviseResponse(CompositionGradeResponse):
    """作文改稿响应"""

    previous_band_score: float = 0.0
    delta: float = 0.0
    improved: bool = False


class CompositionHistoryMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str
    created_at: str


class CompositionHistoryThread(BaseModel):
    thread_id: str
    session_id: Optional[str] = None
    topic: Optional[str] = None
    exam_type: Optional[Literal["ielts", "cet-4", "cet-6", "kaoyan"]] = None
    task_type: Optional[
        Literal[
            "data_graph",
            "image_drawing",
            "process_map",
            "opinion_essay",
            "letter",
            "notice",
        ]
    ] = None
    last_band_score: Optional[float] = None
    updated_at: str
    preview: Optional[str] = None


class CompositionHistoryListResponse(BaseModel):
    threads: list[CompositionHistoryThread] = Field(default_factory=list)


class CompositionHistoryDetailResponse(BaseModel):
    thread_id: str
    session_id: Optional[str] = None
    topic: Optional[str] = None
    exam_type: Optional[Literal["ielts", "cet-4", "cet-6", "kaoyan"]] = None
    task_type: Optional[
        Literal[
            "data_graph",
            "image_drawing",
            "process_map",
            "opinion_essay",
            "letter",
            "notice",
        ]
    ] = None
    messages: list[CompositionHistoryMessage] = Field(default_factory=list)


class SpeakHistoryMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str
    created_at: str


class SpeakHistoryThread(BaseModel):
    thread_id: str
    session_id: Optional[str] = None
    topic: Optional[str] = None
    updated_at: str
    preview: Optional[str] = None


class SpeakHistoryListResponse(BaseModel):
    threads: list[SpeakHistoryThread] = Field(default_factory=list)


class SpeakHistoryDetailResponse(BaseModel):
    thread_id: str
    session_id: Optional[str] = None
    topic: Optional[str] = None
    messages: list[SpeakHistoryMessage] = Field(default_factory=list)


class NormalChatRequest(BaseModel):
    message: str
    mode: Literal["daily", "reasoning"] = "daily"
    enable_search: bool = False
    search_queries: Optional[list[str]] = None


class NormalChatResponse(BaseModel):
    mode: Literal["daily", "reasoning"]
    enable_search: bool
    search_context: str
    answer: str


class NormalHistoryMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str
    created_at: str


class NormalHistoryThread(BaseModel):
    thread_id: str
    session_id: Optional[str] = None
    mode: Literal["daily", "reasoning"]
    updated_at: str
    preview: Optional[str] = None


class NormalHistoryListResponse(BaseModel):
    threads: list[NormalHistoryThread] = Field(default_factory=list)


class NormalHistoryDetailResponse(BaseModel):
    thread_id: str
    session_id: Optional[str] = None
    mode: Literal["daily", "reasoning"]
    messages: list[NormalHistoryMessage] = Field(default_factory=list)
