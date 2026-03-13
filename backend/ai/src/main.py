from fastapi import FastAPI, Header, HTTPException, status
from pydantic import BaseModel
from typing import Optional, List
from src.routers.user.route import user_router
from src.routers.ai.route import ai_router
from src.routers.ai.composition.checkpoint import setup_checkpoint, close_checkpoint
from src.routers.ai.composition.history_store import ensure_history_tables
from src.routers.ai.normal.history_store import ensure_normal_history_tables
from src.routers.ai.speak.history_store import ensure_speak_history_tables
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

# 1. 先定义 lifespan 异步函数
origins = [
    "http://localhost:5173",  # Vite 默认端口
    "http://127.0.0.1:5173",
    "http://localhost:3000",  # 如果你用了其他端口
    "http://127.0.0.1:3000",
    "http://localhost:8080",
]


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_checkpoint()
    await ensure_history_tables()
    await ensure_normal_history_tables()
    await ensure_speak_history_tables()
    print("🚀 服务器正在启动...")
    yield
    close_checkpoint()
    print("🛑 服务器正在关闭...")


version = "0.1.0"

# 2. 在实例化时将 lifespan 传入
app = FastAPI(
    version=version,
    title="FastAPI Demo",
    description="This is a demo of FastAPI",
    lifespan=lifespan,  # <--- 关键就在这里！
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(user_router, prefix="/user", tags=["users"])
app.include_router(ai_router, prefix="/ai", tags=["ai"])
