import json

from fastapi import WebSocket
from starlette.websockets import WebSocketDisconnect

from .history_store import upsert_speak_thread_and_append_messages
from .schemas import SpeakWSOutput
from .service import SpeakService


async def handle_speak_websocket(websocket: WebSocket) -> None:
    """口语实时对话 WS：接收文本，返回流式文本+音频。"""
    # 建立 WS 连接并创建每连接独立的服务实例
    await websocket.accept()
    speak_service = SpeakService()

    try:
        while True:
            # 入站消息格式：纯文本或 JSON（包含 text/user_id/thread_id 等）
            raw_message = await websocket.receive_text()
            message = speak_service.parse_user_message(raw_message)
            user_message = message.text

            if not user_message:
                continue

            assistant_text_parts: list[str] = []

            # 逐条转发流式 chunk 给前端：可能是文本包，也可能是音频包
            async for item in speak_service.ai_service.get_chat_stream(user_message):
                chunk = SpeakWSOutput.from_dict(item)
                if chunk.text:
                    # 仅拼接文本片段用于落库；音频不入库
                    assistant_text_parts.append(chunk.text)
                await websocket.send_text(
                    json.dumps(chunk.model_dump(), ensure_ascii=False)
                )

            # 一轮结束后，保存用户文本 + 助手完整文本，便于历史回看
            assistant_full_text = "".join(assistant_text_parts).strip()
            if assistant_full_text:
                preview = assistant_full_text[:160]
                await upsert_speak_thread_and_append_messages(
                    user_id=str(message.user_id or "speak-demo-user"),
                    thread_id=str(message.thread_id),
                    session_id=message.session_id,
                    topic=message.topic,
                    user_content=user_message,
                    assistant_content=assistant_full_text,
                    preview=preview,
                )

    except WebSocketDisconnect:
        # 客户端主动断开是正常场景
        print("speak websocket client disconnected")
    except Exception as e:
        print(f"speak websocket error: {e}")
        # 发生异常时发送统一错误结束包，前端可立刻结束本轮状态
        error_msg = SpeakWSOutput(
            id=-1,
            text="",
            audio="",
            is_end=True,
            error=str(e),
        )
        await websocket.send_text(
            json.dumps(error_msg.model_dump(), ensure_ascii=False)
        )
    finally:
        # 无论正常结束还是异常，都执行资源清理
        await speak_service.cleanup()
