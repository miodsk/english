import json

from fastapi import WebSocket
from starlette.websockets import WebSocketDisconnect

from .history_store import upsert_speak_thread_and_append_messages
from .schemas import SpeakWSOutput
from .service import SpeakService


async def handle_speak_websocket(websocket: WebSocket) -> None:
    """口语实时对话 WS：接收文本，返回流式文本+音频。"""
    await websocket.accept()
    speak_service = SpeakService()

    try:
        while True:
            raw_message = await websocket.receive_text()
            message = speak_service.parse_user_message(raw_message)
            user_message = message.text

            if not user_message:
                continue

            assistant_text_parts: list[str] = []

            async for item in speak_service.ai_service.get_chat_stream(user_message):
                chunk = SpeakWSOutput.from_dict(item)
                if chunk.text:
                    assistant_text_parts.append(chunk.text)
                await websocket.send_text(
                    json.dumps(chunk.model_dump(), ensure_ascii=False)
                )

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
        print("speak websocket client disconnected")
    except Exception as e:
        print(f"speak websocket error: {e}")
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
        await speak_service.cleanup()
