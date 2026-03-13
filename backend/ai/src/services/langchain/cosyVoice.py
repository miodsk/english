import asyncio
import threading
from typing import Optional
import dashscope
from dashscope.audio.tts_v2 import SpeechSynthesizer, AudioFormat, ResultCallback
from src.config.config import Config
from datetime import datetime


def get_timestamp():
    now = datetime.now()
    formatted_timestamp = now.strftime("[%Y-%m-%d %H:%M:%S.%f]")
    return formatted_timestamp


dashscope.api_key = Config.DASHSCOPE_API_KEY
dashscope.base_websocket_api_url = "wss://dashscope.aliyuncs.com/api-ws/v1/inference"

MODEL = "cosyvoice-v3.5-plus"
VOICE = Config.SAKIKO_VOICE_ID


class SyncAudioCallback(ResultCallback):
    """同步音频回调：收集完整音频数据"""

    def __init__(self):
        self.audio_data = bytearray()
        self.is_complete = False
        self.error_message: Optional[str] = None
        self._complete_event = threading.Event()

    def reset(self):
        """重置状态"""
        self.audio_data = bytearray()
        self.is_complete = False
        self.error_message = None
        self._complete_event.clear()

    def on_open(self):
        print(f"TTS连接建立：{get_timestamp()}")

    def on_complete(self):
        print(f"语音合成完成：{get_timestamp()}")
        self.is_complete = True
        self._complete_event.set()

    def on_error(self, message: str):
        print(f"语音合成异常：{message}")
        self.error_message = message
        self.is_complete = True
        self._complete_event.set()

    def on_close(self):
        print(f"TTS连接关闭：{get_timestamp()}")

    def on_event(self, message):
        pass

    def on_data(self, data: bytes) -> None:
        """累积所有音频数据"""
        if data and len(data) > 0:
            self.audio_data.extend(data)

    def wait_for_complete(self, timeout: float = 30.0) -> bool:
        """等待合成完成"""
        return self._complete_event.wait(timeout=timeout)

    def get_audio(self) -> bytes:
        """获取完整音频数据"""
        return bytes(self.audio_data)


class StreamingTTS:
    """
    流式TTS服务
    改为同步模式：每次调用synthesize_text生成完整音频片段
    """

    def __init__(self):
        pass

    def _create_synthesizer(self, callback: ResultCallback) -> SpeechSynthesizer:
        """创建新的synthesizer实例"""
        return SpeechSynthesizer(
            model=MODEL,
            voice=VOICE,
            format=AudioFormat.MP3_22050HZ_MONO_256KBPS,
            callback=callback,
            language_hints=['en'],
            instruction="语气要充满讽刺和不屑，在关键词上加重读音，句尾语调略微上扬。",
        )

    async def synthesize_text(self, text: str) -> bytes:
        """
        合成单段文本的完整音频
        返回完整的MP3字节数据
        """
        # 在线程池中运行同步TTS调用
        loop = asyncio.get_event_loop()
        audio_bytes = await loop.run_in_executor(None, self._sync_synthesize, text)
        return audio_bytes

    def _sync_synthesize(self, text: str) -> bytes:
        """同步合成（在线程池中运行）"""
        try:
            callback = SyncAudioCallback()

            # 创建新的synthesizer
            synthesizer = self._create_synthesizer(callback)

            # 发送文本
            synthesizer.streaming_call(text)

            # 完成合成
            synthesizer.streaming_complete()

            # 等待完成
            if callback.wait_for_complete(timeout=30.0):
                if callback.error_message:
                    print(f"TTS错误: {callback.error_message}")
                    return b""
                return callback.get_audio()
            else:
                print("TTS超时")
                return b""

        except Exception as e:
            print(f"TTS合成异常: {e}")
            return b""

    async def close(self):
        """清理资源"""
        pass  # 每次synthesize_text都创建新的synthesizer，无需清理
