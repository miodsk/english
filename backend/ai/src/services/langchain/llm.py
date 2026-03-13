import asyncio
import re
import base64
from typing import AsyncGenerator, Dict, Any, List, Optional
from langchain_community.chat_models.tongyi import ChatTongyi
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from src.config.config import Config
from .cosyVoice import StreamingTTS

# 共享的LLM实例（只读，线程安全）
shared_llm = ChatTongyi(
    model="qwen-plus", api_key=Config.DASHSCOPE_API_KEY, streaming=True
)


class TextSlicer:
    """文本切片器：按标点符号切片聚合LLM输出"""

    # 触发切片的标点符号
    PUNCTUATION = r"[，。！？；,\.!\?;]"
    # 避免长句无标点时一直不下发，影响实时性
    MAX_SLICE_LENGTH = 32

    def __init__(self):
        self._buffer = ""

    def add_text(self, text: str) -> list[str]:
        """
        添加文本，返回可以发送的切片列表
        每个切片以标点符号结尾，形成完整的语义单元
        """
        self._buffer += text
        slices = []

        # 查找所有标点符号位置
        while True:
            match = re.search(self.PUNCTUATION, self._buffer)
            if match:
                # 切片到标点符号位置（包含标点）
                end_pos = match.end()
                slice_text = self._buffer[:end_pos].strip()
                if slice_text:
                    slices.append(slice_text)
                self._buffer = self._buffer[end_pos:]
            else:
                break

        # 如果迟迟没有标点，按固定长度兜底切片，避免前端长时间无响应
        while len(self._buffer) >= self.MAX_SLICE_LENGTH:
            slice_text = self._buffer[: self.MAX_SLICE_LENGTH].strip()
            if slice_text:
                slices.append(slice_text)
            self._buffer = self._buffer[self.MAX_SLICE_LENGTH :]

        return slices

    def flush(self) -> str | None:
        """刷新剩余缓冲区内容"""
        remaining = self._buffer.strip()
        self._buffer = ""
        return remaining if remaining else None


class AIService:
    def __init__(self, llm=None, system_prompt: Optional[str] = None):
        self.llm = llm or shared_llm
        self.tts = None
        self.messages: List = [SystemMessage(content=system_prompt or "你好")]
        self._sequence_id = 0  # 序列ID计数器

    def _next_sequence_id(self) -> int:
        """获取下一个序列ID"""
        self._sequence_id += 1
        return self._sequence_id

    def _reset_sequence(self):
        """重置序列ID（每次对话开始时）"""
        self._sequence_id = 0

    async def initialize_tts(self):
        """初始化TTS服务"""
        if self.tts is None:
            self.tts = StreamingTTS()

    async def cleanup(self):
        """清理资源"""
        if self.tts:
            await self.tts.close()
            self.tts = None

    async def _synthesize_slice(self, text: str, seq_id: int) -> Dict[str, Any]:
        """
        合成单个文本切片的音频（仅音频消息）
        返回格式: { "id": N, "text": "", "audio": "base64...", "is_end": false }
        """
        try:
            # 调用TTS合成音频
            audio_bytes = await self.tts.synthesize_text(text)

            # 转换为base64
            audio_base64 = (
                base64.b64encode(audio_bytes).decode("utf-8") if audio_bytes else ""
            )

            return {"id": seq_id, "text": "", "audio": audio_base64, "is_end": False}
        except Exception as e:
            print(f"TTS合成错误 (id={seq_id}): {e}")
            return {
                "id": seq_id,
                "text": "",
                "audio": "",
                "is_end": False,
                "error": str(e),
            }

    async def get_chat_stream(
        self, message: str
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        流式返回文本和语音数据
        消息格式: { "id": N, "text": "...", "audio": "base64...", "is_end": false }
        """
        # 重置序列ID
        self._reset_sequence()

        # 用户消息加入历史
        self.messages.append(HumanMessage(content=message))
        full_response = ""

        # 初始化TTS
        await self.initialize_tts()

        # 创建文本切片器
        slicer = TextSlicer()
        pending_tasks: list[asyncio.Task[Dict[str, Any]]] = []

        try:
            # 流式生成AI回复
            async for chunk in self.llm.astream(self.messages):
                if chunk.content:
                    full_response += chunk.content

                    # 尝试切片
                    slices = slicer.add_text(chunk.content)

                    # 为每个切片生成音频并发送
                    for slice_text in slices:
                        seq_id = self._next_sequence_id()

                        # 文本立即下发，避免被TTS阻塞
                        yield {
                            "id": seq_id,
                            "text": slice_text,
                            "audio": "",
                            "is_end": False,
                            "audio_pending": True,
                        }

                        pending_tasks.append(
                            asyncio.create_task(
                                self._synthesize_slice(slice_text, seq_id)
                            )
                        )

                        # 非阻塞地下发已完成音频任务
                        ready_tasks = [task for task in pending_tasks if task.done()]
                        for ready_task in ready_tasks:
                            pending_tasks.remove(ready_task)
                            result = await ready_task
                            yield result

            # 处理剩余的缓冲区内容
            remaining = slicer.flush()
            if remaining:
                seq_id = self._next_sequence_id()
                yield {
                    "id": seq_id,
                    "text": remaining,
                    "audio": "",
                    "is_end": False,
                    "audio_pending": True,
                }
                pending_tasks.append(
                    asyncio.create_task(self._synthesize_slice(remaining, seq_id))
                )

            # 继续下发剩余音频任务（按完成顺序）
            while pending_tasks:
                done_tasks, pending = await asyncio.wait(
                    pending_tasks, return_when=asyncio.FIRST_COMPLETED
                )
                pending_tasks = list(pending)
                for done_task in done_tasks:
                    result = await done_task
                    yield result

            # 发送结束标记
            yield {
                "id": self._next_sequence_id(),
                "text": "",
                "audio": "",
                "is_end": True,
            }

        except Exception as e:
            print(f"LLM流处理错误: {e}")

            for task in pending_tasks:
                if not task.done():
                    task.cancel()

            if pending_tasks:
                await asyncio.gather(*pending_tasks, return_exceptions=True)

            # 发送错误结束标记
            yield {
                "id": self._next_sequence_id(),
                "text": "",
                "audio": "",
                "is_end": True,
                "error": str(e),
            }

        # AI回复加入历史（限制历史长度避免内存泄漏）
        self.messages.append(AIMessage(content=full_response))
        if len(self.messages) > 10:
            system_msg = self.messages[0]
            recent_messages = self.messages[-9:]
            self.messages = [system_msg] + recent_messages
