from typing import Any

from pydantic import BaseModel


class SpeakWSInput(BaseModel):
    """口语 WS 入站消息。"""

    # 用户输入文本（前端 ASR 结果或手动输入）
    text: str
    # 业务上下文字段：用于历史归档与会话关联
    user_id: str | None = None
    session_id: str | None = None
    thread_id: str | None = None
    topic: str | None = None


class SpeakWSOutput(BaseModel):
    """口语 WS 出站消息（与前端约定协议保持一致）。"""

    # 递增序号：同一 id 的 text 包与 audio 包可在前端配对
    id: int
    # 文本分片内容；音频包通常为空字符串
    text: str
    # base64 音频数据；文本包通常为空字符串
    audio: str
    # 本轮是否结束
    is_end: bool
    # 标记该 text 对应的音频仍在合成中
    audio_pending: bool | None = None
    # 错误信息（仅异常场景）
    error: str | None = None

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "SpeakWSOutput":
        # 对下游字典做一次类型归一化，避免字段类型漂移
        return cls(
            id=int(payload.get("id", 0)),
            text=str(payload.get("text", "")),
            audio=str(payload.get("audio", "")),
            is_end=bool(payload.get("is_end", False)),
            audio_pending=payload.get("audio_pending"),
            error=payload.get("error"),
        )
