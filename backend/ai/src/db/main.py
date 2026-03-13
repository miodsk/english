from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from src.config.config import Config


async_engine = create_async_engine(
    Config.ASYNC_DATABASE_URL,
    echo=False,  # 生产环境建议设为 False，避免日志被 SQL 刷屏
    future=True
)

AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False
)

async def get_session():
    async with AsyncSessionLocal() as session:
        yield session