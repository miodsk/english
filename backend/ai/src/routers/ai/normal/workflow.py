from typing import Optional, List

from .chains.daily_chain import daily_chain
from .chains.reasoning_chain import reasoning_chain
from .state import NormalMode
from src.routers.ai.tools.tavily_tool import search


def _resolve_search_queries(
    message: str, search_queries: Optional[List[str]]
) -> List[str]:
    if search_queries:
        return [q for q in search_queries if q and q.strip()]
    return [message]


def _build_search_context(
    message: str, enable_search: bool, search_queries: Optional[List[str]]
) -> str:
    if not enable_search:
        return ""

    queries = _resolve_search_queries(message, search_queries)
    if not queries:
        return ""

    return search(queries)


def run_normal_chat(
    *,
    message: str,
    mode: NormalMode = "daily",
    enable_search: bool = False,
    search_queries: Optional[List[str]] = None,
) -> dict:
    search_context = _build_search_context(message, enable_search, search_queries)

    selected_chain = reasoning_chain if mode == "reasoning" else daily_chain
    answer = selected_chain.invoke(
        {
            "message": message,
            "search_context": search_context,
        }
    )

    return {
        "mode": mode,
        "enable_search": enable_search,
        "search_context": search_context,
        "answer": answer,
    }


def build_normal_stream_context(
    *,
    message: str,
    mode: NormalMode = "daily",
    enable_search: bool = False,
    search_queries: Optional[List[str]] = None,
) -> dict:
    search_context = _build_search_context(message, enable_search, search_queries)

    if mode == "reasoning":
        from .chains.reasoning_chain import reasoning_prompt, reasoning_llm

        prompt = reasoning_prompt
        llm = reasoning_llm
    else:
        from .chains.daily_chain import daily_prompt, daily_llm

        prompt = daily_prompt
        llm = daily_llm

    messages = prompt.format_messages(
        message=message,
        search_context=search_context,
    )

    return {
        "mode": mode,
        "search_context": search_context,
        "messages": messages,
        "llm": llm,
    }
