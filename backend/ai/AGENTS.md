# PROJECT KNOWLEDGE BASE

**Generated:** 2026-03-13
**Project:** English Learning AI Backend

## OVERVIEW

FastAPI backend for English learning platform. Powers AI-driven essay grading (composition), oral practice (speak), and daily chat (normal) using LangChain/LangGraph with multiple LLM providers (Dashscope/Qwen, DeepSeek, Zhipu).

## STRUCTURE

```
src/
├── main.py              # FastAPI app entry (lifespan: checkpoint + history tables)
├── config/              # Pydantic Settings (env vars)
├── db/                  # Async SQLAlchemy + Milvus vector DB
├── models/              # SQLModel ORM definitions
├── routers/
│   ├── user/            # User auth/profile endpoints
│   └── ai/
│       ├── route.py     # Main AI router (577 lines) - WebSocket + REST
│       ├── composition/ # Essay grading workflow (LangGraph)
│       ├── speak/       # Oral practice w/ TTS streaming
│       ├── normal/      # Daily chat (daily/reasoning modes)
│       └── tools/       # External tools (Tavily search)
└── services/
    └── langchain/       # LLM clients, embeddings, TTS (CosyVoice)
```

## WHERE TO LOOK

| Task | Location |
|------|----------|
| Add new AI feature | `src/routers/ai/` - create new subdirectory or extend existing |
| Modify essay grading | `src/routers/ai/composition/` - nodes/, chains/, workflow.py |
| Change LLM provider | `src/services/langchain/llm.py` - shared_llm instance |
| Add database model | `src/models/models.py` |
| Configure environment | `.env` + `src/config/config.py` |
| WebSocket endpoints | `src/routers/ai/route.py:121-248` (normal), `speak/workflow.py` |
| History persistence | `*_history_store.py` in each ai submodule |

## CONVENTIONS

### Workflow Pattern (LangGraph)
```python
# Each AI module follows this pattern:
workflow.py      # StateGraph definition, node orchestration
nodes/           # Async node functions (state -> state)
chains/          # LangChain chains for LLM calls
state.py         # TypedDict state definition
history_store.py # PostgreSQL persistence via asyncpg
```

### Router Organization
- `route.py` at each level = FastAPI router
- WebSocket handlers delegate to `workflow.py`
- History stores are module-local (not shared)

### Async Patterns
- `run_in_threadpool()` wraps sync LangGraph invoke
- AsyncSession for SQLAlchemy
- Streaming: `async for chunk in llm.astream()`

### History Store Pattern
Each module has its own `history_store.py` with:
- `ensure_*_history_tables()` - CREATE TABLE IF NOT EXISTS
- `upsert_*_thread_and_append_messages()` - Insert/update
- `list_*_threads()`, `get_*_thread_detail()` - Queries

## ANTI-PATTERNS (THIS PROJECT)

- **Don't rename** `src/db/main.py` (shared as db session factory despite name)
- **Don't share** history_store between modules - each has own table schema
- **Don't use sync** database calls in async context

## COMMANDS

```bash
# Run dev server
uvicorn src.main:app --reload

# Run with FastAPI CLI
fastapi dev src/main.py

# Install deps
uv sync
```

## NOTES

- **Checkpoint**: LangGraph PostgreSQL checkpointer for state persistence
- **TTS**: CosyVoice streaming via Dashscope
- **Milvus**: Vector DB for essay samples/rubrics retrieval
- **Three AI modes**: composition (essay), speak (oral), normal (chat)
- **No tests framework**: Only `test_streaming.py` with unittest.mock
- **No CI/CD**: Manual deployment