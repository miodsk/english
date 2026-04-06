import json
from typing import Optional
from uuid import uuid4

from src.services.langchain.llm import AIService
from .prompt import SAKIKO_SYSTEM_PROMPT
from .schemas import SpeakWSInput


class SpeakService:
    """口语实时对话服务：文本入，流式文本+音频出。"""

    def __init__(self, ai_service: Optional[AIService] = None):
        # 统一注入口语场景 system prompt，保证回复风格稳定
        self.ai_service = ai_service or AIService(system_prompt=SAKIKO_SYSTEM_PROMPT)

    @staticmethod
    def parse_user_message(raw_message: str) -> SpeakWSInput:
        """兼容纯文本和 JSON 两种入站格式。"""
        # 默认按纯文本处理；若能解析成 JSON 再覆盖字段
        user_message = raw_message.strip()
        payload_dict: dict = {"text": user_message}
        try:
            payload = json.loads(raw_message)
            if isinstance(payload, dict):
                payload_dict = payload
                user_message = str(payload.get("text", "")).strip()
        except json.JSONDecodeError:
            user_message = raw_message.strip()

        return SpeakWSInput(
            # 前端可仅传 text，其余字段均由后端兜底
            text=user_message,
            user_id=str(payload_dict.get("user_id") or "speak-demo-user"),
            session_id=(
                str(payload_dict.get("session_id"))
                if payload_dict.get("session_id")
                else None
            ),
            thread_id=(
                # 未传 thread_id 时自动生成，方便首轮直接可用
                str(payload_dict.get("thread_id"))
                if payload_dict.get("thread_id")
                else str(uuid4())
            ),
            topic=(
                str(payload_dict.get("topic")) if payload_dict.get("topic") else None
            ),
        )

    async def cleanup(self) -> None:
        # WS 连接结束后释放 TTS 等资源
        await self.ai_service.cleanup()
