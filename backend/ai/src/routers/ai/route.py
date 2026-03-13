from uuid import uuid4
import json

from fastapi import APIRouter, HTTPException, WebSocket, status
from fastapi.concurrency import run_in_threadpool

from src.routers.ai.composition.essay_state import create_initial_state
from src.routers.ai.composition.history_store import (
    get_thread_detail,
    list_threads,
    upsert_thread_and_append_messages,
)
from src.routers.ai.normal.workflow import run_normal_chat
from src.routers.ai.normal.workflow import build_normal_stream_context
from src.routers.ai.normal.history_store import (
    list_normal_threads,
    get_normal_thread_detail,
    upsert_normal_thread_and_append_messages,
)
from src.routers.ai.composition.workflow import get_workflow
from src.routers.ai.speak.history_store import (
    get_speak_thread_detail,
    list_speak_threads,
)
from src.routers.ai.speak.workflow import handle_speak_websocket
from src.routers.ai.schemas import (
    CompositionGradeRequest,
    CompositionGradeResponse,
    CompositionHistoryDetailResponse,
    CompositionHistoryListResponse,
    CompositionHistoryMessage,
    CompositionHistoryThread,
    CompositionReviseRequest,
    CompositionReviseResponse,
    SpeakHistoryDetailResponse,
    SpeakHistoryListResponse,
    SpeakHistoryMessage,
    SpeakHistoryThread,
    NormalChatRequest,
    NormalChatResponse,
    NormalHistoryDetailResponse,
    NormalHistoryListResponse,
    NormalHistoryMessage,
    NormalHistoryThread,
)

ai_router = APIRouter()


def _extract_state_values(raw_state: object) -> dict:
    """兼容 LangGraph state snapshot / dict 两种返回形式。"""
    if raw_state is None:
        return {}

    if isinstance(raw_state, dict):
        values = raw_state.get("values")
        return values if isinstance(values, dict) else raw_state

    values = getattr(raw_state, "values", None)
    if isinstance(values, dict):
        return values

    return {}


def _build_previous_summary(previous_state: dict) -> str:
    """把上轮评分结果压缩成给模型可读的摘要。"""
    if not previous_state:
        return "N/A"

    band_score = previous_state.get("band_score", 0.0)
    scores = previous_state.get("scores", {}) or {}
    errors = previous_state.get("errors", []) or []
    suggestions = previous_state.get("suggestions", []) or []

    score_text = ", ".join([f"{k}: {v}" for k, v in scores.items()]) or "N/A"

    key_errors = []
    for e in errors:
        severity = e.get("severity", "medium")
        if severity in {"high", "medium"}:
            key_errors.append(f"{e.get('type', 'unknown')}: {e.get('reason', '')}")
        if len(key_errors) >= 3:
            break

    key_suggestions = [s for s in suggestions[:3] if isinstance(s, str)]

    parts = [
        f"Previous overall score: {band_score}",
        f"Previous dimension scores: {score_text}",
        "Key previous errors:",
    ]
    if key_errors:
        parts.extend([f"- {item}" for item in key_errors])
    else:
        parts.append("- N/A")

    parts.append("Previous key suggestions:")
    if key_suggestions:
        parts.extend([f"- {item}" for item in key_suggestions])
    else:
        parts.append("- N/A")

    return "\n".join(parts)


def _build_assistant_preview(result: dict) -> str:
    score = result.get("band_score", 0.0)
    explanation = str(result.get("score_explanation") or "")
    suggestions = result.get("suggestions", []) or []
    first_suggestion = suggestions[0] if suggestions else ""
    return (
        f"本次得分: {score}\n{explanation[:160]}\n建议: {str(first_suggestion)[:120]}"
    ).strip()


def _build_normal_preview(answer: str) -> str:
    return (answer or "").strip()[:180]


@ai_router.websocket("/ws")
async def chat_websocket(websocket: WebSocket):
    await handle_speak_websocket(websocket)


@ai_router.websocket("/speak/ws")
async def speak_websocket(websocket: WebSocket):
    """口语专用 WS 路由（功能与 /ws 相同，语义更明确）。"""
    await handle_speak_websocket(websocket)


@ai_router.websocket("/normal/ws")
async def normal_websocket(websocket: WebSocket):
    """日常对话 WS：支持 daily/reasoning 模式与搜索增强，流式输出文本。"""
    await websocket.accept()

    try:
        while True:
            raw_message = await websocket.receive_text()
            payload = json.loads(raw_message)

            message = str(payload.get("message", "")).strip()
            if not message:
                await websocket.send_text(
                    json.dumps(
                        {
                            "id": -1,
                            "text": "",
                            "is_end": True,
                            "error": "message 不能为空",
                        },
                        ensure_ascii=False,
                    )
                )
                continue

            mode = str(payload.get("mode", "daily"))
            if mode not in {"daily", "reasoning"}:
                mode = "daily"

            enable_search = bool(payload.get("enable_search", False))
            search_queries = payload.get("search_queries")
            if not isinstance(search_queries, list):
                search_queries = None

            user_id = str(payload.get("user_id") or "normal-demo-user")
            session_id = payload.get("session_id")
            session_id = str(session_id) if session_id else None
            thread_id = str(payload.get("thread_id") or str(uuid4()))

            context = await run_in_threadpool(
                build_normal_stream_context,
                message=message,
                mode=mode,
                enable_search=enable_search,
                search_queries=search_queries,
            )

            seq = 0
            answer_parts: list[str] = []

            # 可选先发一条上下文包，便于前端调试
            await websocket.send_text(
                json.dumps(
                    {
                        "id": seq,
                        "text": "",
                        "is_end": False,
                        "meta": {
                            "mode": context["mode"],
                            "search_context": context["search_context"],
                            "thread_id": thread_id,
                        },
                    },
                    ensure_ascii=False,
                )
            )

            async for chunk in context["llm"].astream(context["messages"]):
                text = getattr(chunk, "content", "")
                if not text:
                    continue
                seq += 1
                answer_parts.append(text)
                await websocket.send_text(
                    json.dumps(
                        {
                            "id": seq,
                            "text": text,
                            "is_end": False,
                        },
                        ensure_ascii=False,
                    )
                )

            final_answer = "".join(answer_parts).strip()
            if final_answer:
                await upsert_normal_thread_and_append_messages(
                    user_id=user_id,
                    thread_id=thread_id,
                    session_id=session_id,
                    mode=context["mode"],
                    user_content=message,
                    assistant_content=final_answer,
                    preview=_build_normal_preview(final_answer),
                )

            seq += 1
            await websocket.send_text(
                json.dumps(
                    {
                        "id": seq,
                        "text": "",
                        "is_end": True,
                        "thread_id": thread_id,
                    },
                    ensure_ascii=False,
                )
            )

    except Exception as e:
        await websocket.send_text(
            json.dumps(
                {"id": -1, "text": "", "is_end": True, "error": str(e)},
                ensure_ascii=False,
            )
        )


@ai_router.post(
    "/composition/grade",
    response_model=CompositionGradeResponse,
    status_code=status.HTTP_200_OK,
)
async def grade_composition(payload: CompositionGradeRequest):
    """执行作文批改工作流（LangGraph）。"""
    try:
        thread_id = payload.thread_id or str(uuid4())
        initial_state = create_initial_state(
            essay_text=payload.essay_text,
            exam_type=payload.exam_type,
            task_type=payload.task_type,
            topic=payload.topic,
            user_id=payload.user_id,
            thread_id=thread_id,
            session_id=payload.session_id,
            previous_summary="N/A",
        )
        config = {"configurable": {"thread_id": thread_id}}
        workflow = get_workflow()
        result = await run_in_threadpool(workflow.invoke, initial_state, config)

        assistant_preview = _build_assistant_preview(result)
        await upsert_thread_and_append_messages(
            user_id=payload.user_id,
            thread_id=thread_id,
            session_id=payload.session_id,
            topic=payload.topic,
            exam_type=payload.exam_type,
            task_type=payload.task_type,
            user_content=payload.essay_text,
            assistant_content=assistant_preview,
            last_band_score=float(result.get("band_score", 0.0)),
            preview=assistant_preview,
        )

        return CompositionGradeResponse(
            thread_id=thread_id,
            scores=result.get("scores", {}),
            band_score=float(result.get("band_score", 0.0)),
            score_explanation=result.get("score_explanation"),
            errors=result.get("errors", []),
            suggestions=result.get("suggestions", []),
            current_step=result.get("current_step"),
            needs_revision=bool(result.get("needs_revision", False)),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"作文批改失败: {str(e)}",
        )


@ai_router.post(
    "/composition/revise",
    response_model=CompositionReviseResponse,
    status_code=status.HTTP_200_OK,
)
async def revise_composition(payload: CompositionReviseRequest):
    """基于同一个 thread_id 提交修改稿，进行二次评分。"""
    try:
        config = {"configurable": {"thread_id": payload.thread_id}}
        workflow = get_workflow()

        previous_raw_state = await run_in_threadpool(workflow.get_state, config)
        previous_state = _extract_state_values(previous_raw_state)

        previous_band_score = float(previous_state.get("band_score", 0.0))
        previous_summary = _build_previous_summary(previous_state)

        exam_type = payload.exam_type or previous_state.get("exam_type")
        task_type = payload.task_type or previous_state.get("task_type")
        if not exam_type or not task_type:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="缺少 exam_type/task_type，且无法从 thread 历史状态恢复。",
            )

        topic = (
            payload.topic if payload.topic is not None else previous_state.get("topic")
        )
        user_id = (
            payload.user_id
            if payload.user_id is not None
            else previous_state.get("user_id")
        )
        session_id = (
            payload.session_id
            if payload.session_id is not None
            else previous_state.get("session_id")
        )

        initial_state = create_initial_state(
            essay_text=payload.revised_essay,
            exam_type=exam_type,
            task_type=task_type,
            topic=topic,
            user_id=user_id,
            thread_id=payload.thread_id,
            session_id=session_id,
            revised_essay=payload.revised_essay,
            previous_summary=previous_summary,
        )

        result = await run_in_threadpool(workflow.invoke, initial_state, config)

        new_band_score = float(result.get("band_score", 0.0))
        delta = round(new_band_score - previous_band_score, 2)

        owner_user_id = str(user_id or "")
        assistant_preview = _build_assistant_preview(result)
        await upsert_thread_and_append_messages(
            user_id=owner_user_id,
            thread_id=payload.thread_id,
            session_id=session_id,
            topic=topic,
            exam_type=exam_type,
            task_type=task_type,
            user_content=payload.revised_essay,
            assistant_content=assistant_preview,
            last_band_score=new_band_score,
            preview=assistant_preview,
        )

        return CompositionReviseResponse(
            thread_id=payload.thread_id,
            scores=result.get("scores", {}),
            band_score=new_band_score,
            score_explanation=result.get("score_explanation"),
            errors=result.get("errors", []),
            suggestions=result.get("suggestions", []),
            current_step=result.get("current_step"),
            needs_revision=bool(result.get("needs_revision", False)),
            previous_band_score=previous_band_score,
            delta=delta,
            improved=delta > 0,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"作文改稿失败: {str(e)}",
        )


@ai_router.get(
    "/composition/history",
    response_model=CompositionHistoryListResponse,
    status_code=status.HTTP_200_OK,
)
async def list_composition_history(user_id: str):
    """获取某个用户的作文线程历史列表。"""
    rows = await list_threads(user_id)
    threads = [
        CompositionHistoryThread(
            thread_id=str(row["thread_id"]),
            session_id=row.get("session_id"),
            topic=row.get("topic"),
            exam_type=row.get("exam_type"),
            task_type=row.get("task_type"),
            last_band_score=row.get("last_band_score"),
            updated_at=row["updated_at"].isoformat(),
            preview=row.get("preview"),
        )
        for row in rows
    ]
    return CompositionHistoryListResponse(threads=threads)


@ai_router.get(
    "/composition/history/{thread_id}",
    response_model=CompositionHistoryDetailResponse,
    status_code=status.HTTP_200_OK,
)
async def get_composition_history_detail(thread_id: str, user_id: str):
    """获取某个线程的历史消息明细。"""
    detail = await get_thread_detail(user_id, thread_id)
    if detail is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="未找到该线程历史"
        )

    messages = [
        CompositionHistoryMessage(
            role=str(msg["role"]),
            content=str(msg["content"]),
            created_at=msg["created_at"].isoformat(),
        )
        for msg in detail.get("messages", [])
    ]

    return CompositionHistoryDetailResponse(
        thread_id=thread_id,
        session_id=detail.get("session_id"),
        topic=detail.get("topic"),
        exam_type=detail.get("exam_type"),
        task_type=detail.get("task_type"),
        messages=messages,
    )


@ai_router.get(
    "/speak/history",
    response_model=SpeakHistoryListResponse,
    status_code=status.HTTP_200_OK,
)
async def list_speak_history(user_id: str):
    rows = await list_speak_threads(user_id)
    threads = [
        SpeakHistoryThread(
            thread_id=str(row["thread_id"]),
            session_id=row.get("session_id"),
            topic=row.get("topic"),
            updated_at=row["updated_at"].isoformat(),
            preview=row.get("preview"),
        )
        for row in rows
    ]
    return SpeakHistoryListResponse(threads=threads)


@ai_router.get(
    "/speak/history/{thread_id}",
    response_model=SpeakHistoryDetailResponse,
    status_code=status.HTTP_200_OK,
)
async def get_speak_history_detail(thread_id: str, user_id: str):
    detail = await get_speak_thread_detail(user_id, thread_id)
    if detail is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="未找到该口语线程历史",
        )

    messages = [
        SpeakHistoryMessage(
            role=str(msg["role"]),
            content=str(msg["content"]),
            created_at=msg["created_at"].isoformat(),
        )
        for msg in detail.get("messages", [])
    ]

    return SpeakHistoryDetailResponse(
        thread_id=thread_id,
        session_id=detail.get("session_id"),
        topic=detail.get("topic"),
        messages=messages,
    )


@ai_router.post(
    "/normal/chat",
    response_model=NormalChatResponse,
    status_code=status.HTTP_200_OK,
)
async def normal_chat(payload: NormalChatRequest):
    """日常对话：支持 daily/reasoning 两种模式，可选搜索增强。"""
    try:
        result = await run_in_threadpool(
            run_normal_chat,
            message=payload.message,
            mode=payload.mode,
            enable_search=payload.enable_search,
            search_queries=payload.search_queries,
        )
        return NormalChatResponse(
            mode=result["mode"],
            enable_search=bool(result["enable_search"]),
            search_context=result["search_context"],
            answer=result["answer"],
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"日常对话失败: {str(e)}",
        )


@ai_router.get(
    "/normal/history",
    response_model=NormalHistoryListResponse,
    status_code=status.HTTP_200_OK,
)
async def list_normal_history(user_id: str):
    rows = await list_normal_threads(user_id)
    threads = [
        NormalHistoryThread(
            thread_id=str(row["thread_id"]),
            session_id=row.get("session_id"),
            mode=str(row.get("mode") or "daily"),
            updated_at=row["updated_at"].isoformat(),
            preview=row.get("preview"),
        )
        for row in rows
    ]
    return NormalHistoryListResponse(threads=threads)


@ai_router.get(
    "/normal/history/{thread_id}",
    response_model=NormalHistoryDetailResponse,
    status_code=status.HTTP_200_OK,
)
async def get_normal_history_detail(thread_id: str, user_id: str):
    detail = await get_normal_thread_detail(user_id, thread_id)
    if detail is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="未找到该日常对话线程历史"
        )

    messages = [
        NormalHistoryMessage(
            role=str(msg["role"]),
            content=str(msg["content"]),
            created_at=msg["created_at"].isoformat(),
        )
        for msg in detail.get("messages", [])
    ]

    return NormalHistoryDetailResponse(
        thread_id=thread_id,
        session_id=detail.get("session_id"),
        mode=str(detail.get("mode") or "daily"),
        messages=messages,
    )
