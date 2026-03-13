from typing import Optional, TypedDict, Literal, List


NormalMode = Literal["daily", "reasoning"]


class NormalChatState(TypedDict):
    message: str
    mode: NormalMode
    enable_search: bool
    search_queries: Optional[List[str]]
    search_context: str
    answer: str
