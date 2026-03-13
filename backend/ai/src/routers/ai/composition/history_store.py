from typing import Any

from sqlalchemy import text

from src.db.main import AsyncSessionLocal, async_engine


async def ensure_history_tables() -> None:
    """初始化作文历史相关表（幂等）。"""
    create_threads_sql = text(
        """
        CREATE TABLE IF NOT EXISTS composition_history_threads (
            user_id TEXT NOT NULL,
            thread_id TEXT NOT NULL,
            session_id TEXT,
            topic TEXT,
            exam_type TEXT,
            task_type TEXT,
            last_band_score DOUBLE PRECISION,
            preview TEXT,
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            PRIMARY KEY (user_id, thread_id)
        );
        """
    )

    create_messages_sql = text(
        """
        CREATE TABLE IF NOT EXISTS composition_history_messages (
            id BIGSERIAL PRIMARY KEY,
            user_id TEXT NOT NULL,
            thread_id TEXT NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            CONSTRAINT fk_composition_history_thread
                FOREIGN KEY (user_id, thread_id)
                REFERENCES composition_history_threads(user_id, thread_id)
                ON DELETE CASCADE
        );
        """
    )

    create_threads_idx_sql = text(
        """
        CREATE INDEX IF NOT EXISTS idx_composition_history_threads_updated
            ON composition_history_threads (user_id, updated_at DESC);
        """
    )

    create_messages_idx_sql = text(
        """
        CREATE INDEX IF NOT EXISTS idx_composition_history_messages_thread
            ON composition_history_messages (user_id, thread_id, created_at ASC);
        """
    )

    async with async_engine.begin() as conn:
        await conn.execute(create_threads_sql)
        await conn.execute(create_messages_sql)
        await conn.execute(create_threads_idx_sql)
        await conn.execute(create_messages_idx_sql)


async def upsert_thread_and_append_messages(
    *,
    user_id: str,
    thread_id: str,
    session_id: str | None,
    topic: str | None,
    exam_type: str | None,
    task_type: str | None,
    user_content: str,
    assistant_content: str,
    last_band_score: float,
    preview: str,
) -> None:
    """写入/更新线程元数据，并追加本轮 user/assistant 消息。"""
    upsert_sql = text(
        """
        INSERT INTO composition_history_threads
            (user_id, thread_id, session_id, topic, exam_type, task_type, last_band_score, preview, updated_at)
        VALUES
            (:user_id, :thread_id, :session_id, :topic, :exam_type, :task_type, :last_band_score, :preview, NOW())
        ON CONFLICT (user_id, thread_id)
        DO UPDATE SET
            session_id = COALESCE(EXCLUDED.session_id, composition_history_threads.session_id),
            topic = COALESCE(EXCLUDED.topic, composition_history_threads.topic),
            exam_type = COALESCE(EXCLUDED.exam_type, composition_history_threads.exam_type),
            task_type = COALESCE(EXCLUDED.task_type, composition_history_threads.task_type),
            last_band_score = EXCLUDED.last_band_score,
            preview = EXCLUDED.preview,
            updated_at = NOW();
        """
    )

    insert_message_sql = text(
        """
        INSERT INTO composition_history_messages (user_id, thread_id, role, content)
        VALUES (:user_id, :thread_id, :role, :content);
        """
    )

    async with AsyncSessionLocal() as session:
        await session.execute(
            upsert_sql,
            {
                "user_id": user_id,
                "thread_id": thread_id,
                "session_id": session_id,
                "topic": topic,
                "exam_type": exam_type,
                "task_type": task_type,
                "last_band_score": last_band_score,
                "preview": preview,
            },
        )
        await session.execute(
            insert_message_sql,
            {
                "user_id": user_id,
                "thread_id": thread_id,
                "role": "user",
                "content": user_content,
            },
        )
        await session.execute(
            insert_message_sql,
            {
                "user_id": user_id,
                "thread_id": thread_id,
                "role": "assistant",
                "content": assistant_content,
            },
        )
        await session.commit()


async def list_threads(user_id: str) -> list[dict[str, Any]]:
    sql = text(
        """
        SELECT thread_id, session_id, topic, exam_type, task_type, last_band_score, updated_at, preview
        FROM composition_history_threads
        WHERE user_id = :user_id
        ORDER BY updated_at DESC;
        """
    )

    async with AsyncSessionLocal() as session:
        result = await session.execute(sql, {"user_id": user_id})
        rows = result.mappings().all()
        return [dict(row) for row in rows]


async def get_thread_detail(user_id: str, thread_id: str) -> dict[str, Any] | None:
    thread_sql = text(
        """
        SELECT thread_id, session_id, topic, exam_type, task_type
        FROM composition_history_threads
        WHERE user_id = :user_id AND thread_id = :thread_id
        LIMIT 1;
        """
    )

    message_sql = text(
        """
        SELECT role, content, created_at
        FROM composition_history_messages
        WHERE user_id = :user_id AND thread_id = :thread_id
        ORDER BY created_at ASC, id ASC;
        """
    )

    async with AsyncSessionLocal() as session:
        thread_result = await session.execute(
            thread_sql,
            {"user_id": user_id, "thread_id": thread_id},
        )
        thread = thread_result.mappings().first()
        if thread is None:
            return None

        message_result = await session.execute(
            message_sql,
            {"user_id": user_id, "thread_id": thread_id},
        )
        messages = [dict(row) for row in message_result.mappings().all()]

        detail = dict(thread)
        detail["messages"] = messages
        return detail
