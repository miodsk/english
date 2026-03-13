from typing import Any

from sqlalchemy import text

from src.db.main import AsyncSessionLocal, async_engine


async def ensure_normal_history_tables() -> None:
    create_threads_sql = text(
        """
        CREATE TABLE IF NOT EXISTS normal_history_threads (
            user_id TEXT NOT NULL,
            thread_id TEXT NOT NULL,
            session_id TEXT,
            mode TEXT,
            preview TEXT,
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            PRIMARY KEY (user_id, thread_id)
        );
        """
    )

    create_messages_sql = text(
        """
        CREATE TABLE IF NOT EXISTS normal_history_messages (
            id BIGSERIAL PRIMARY KEY,
            user_id TEXT NOT NULL,
            thread_id TEXT NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            CONSTRAINT fk_normal_history_thread
                FOREIGN KEY (user_id, thread_id)
                REFERENCES normal_history_threads(user_id, thread_id)
                ON DELETE CASCADE
        );
        """
    )

    create_threads_idx_sql = text(
        """
        CREATE INDEX IF NOT EXISTS idx_normal_history_threads_updated
            ON normal_history_threads (user_id, updated_at DESC);
        """
    )

    create_messages_idx_sql = text(
        """
        CREATE INDEX IF NOT EXISTS idx_normal_history_messages_thread
            ON normal_history_messages (user_id, thread_id, created_at ASC);
        """
    )

    async with async_engine.begin() as conn:
        await conn.execute(create_threads_sql)
        await conn.execute(create_messages_sql)
        await conn.execute(create_threads_idx_sql)
        await conn.execute(create_messages_idx_sql)


async def upsert_normal_thread_and_append_messages(
    *,
    user_id: str,
    thread_id: str,
    session_id: str | None,
    mode: str,
    user_content: str,
    assistant_content: str,
    preview: str,
) -> None:
    upsert_sql = text(
        """
        INSERT INTO normal_history_threads
            (user_id, thread_id, session_id, mode, preview, updated_at)
        VALUES
            (:user_id, :thread_id, :session_id, :mode, :preview, NOW())
        ON CONFLICT (user_id, thread_id)
        DO UPDATE SET
            session_id = COALESCE(EXCLUDED.session_id, normal_history_threads.session_id),
            mode = EXCLUDED.mode,
            preview = EXCLUDED.preview,
            updated_at = NOW();
        """
    )

    insert_message_sql = text(
        """
        INSERT INTO normal_history_messages (user_id, thread_id, role, content)
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
                "mode": mode,
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


async def list_normal_threads(user_id: str) -> list[dict[str, Any]]:
    sql = text(
        """
        SELECT thread_id, session_id, mode, preview, updated_at
        FROM normal_history_threads
        WHERE user_id = :user_id
        ORDER BY updated_at DESC;
        """
    )

    async with AsyncSessionLocal() as session:
        result = await session.execute(sql, {"user_id": user_id})
        return [dict(row) for row in result.mappings().all()]


async def get_normal_thread_detail(
    user_id: str, thread_id: str
) -> dict[str, Any] | None:
    thread_sql = text(
        """
        SELECT thread_id, session_id, mode
        FROM normal_history_threads
        WHERE user_id = :user_id AND thread_id = :thread_id
        LIMIT 1;
        """
    )

    message_sql = text(
        """
        SELECT role, content, created_at
        FROM normal_history_messages
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
        detail = dict(thread)
        detail["messages"] = [dict(row) for row in message_result.mappings().all()]
        return detail
