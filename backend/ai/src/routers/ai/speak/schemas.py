from typing import Any

from pydantic import BaseModel


class SpeakWSInput(BaseModel):
    """口语 WS 入站消息。"""

    text: str
    user_id: str | None = None
    session_id: str | None = None
    thread_id: str | None = None
    topic: str | None = None


class SpeakWSOutput(BaseModel):
    """口语 WS 出站消息（与前端约定协议保持一致）。"""

    id: int
    text: str
    audio: str
    is_end: bool
    audio_pending: bool | None = None
    error: str | None = None

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "SpeakWSOutput":
        return cls(
            id=int(payload.get("id", 0)),
            text=str(payload.get("text", "")),
            audio=str(payload.get("audio", "")),
            is_end=bool(payload.get("is_end", False)),
            audio_pending=payload.get("audio_pending"),
            error=payload.get("error"),
        )
