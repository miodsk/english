import json
from typing import Optional
from uuid import uuid4

from src.services.langchain.llm import AIService
from .prompt import SAKIKO_SYSTEM_PROMPT
from .schemas import SpeakWSInput

class SpeakService:
    """口语实时对话服务：文本入，流式文本+音频出。"""

    def __init__(self, ai_service: Optional[AIService] = None):
        self.ai_service = ai_service or AIService(system_prompt=SAKIKO_SYSTEM_PROMPT)

    @staticmethod
    def parse_user_message(raw_message: str) -> SpeakWSInput:
        """兼容纯文本和 JSON 两种入站格式。"""
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
            text=user_message,
            user_id=str(payload_dict.get("user_id") or "speak-demo-user"),
            session_id=(
                str(payload_dict.get("session_id"))
                if payload_dict.get("session_id")
                else None
            ),
            thread_id=(
                str(payload_dict.get("thread_id"))
                if payload_dict.get("thread_id")
                else str(uuid4())
            ),
            topic=(
                str(payload_dict.get("topic")) if payload_dict.get("topic") else None
            ),
        )

    async def cleanup(self) -> None:
        await self.ai_service.cleanup()
