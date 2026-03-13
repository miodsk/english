from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )
    DATABASE_URL: str
    DASHSCOPE_API_KEY:str
    SAKIKO_VOICE_ID:str
    ZHIPU_API_KEY:str
    MILVUS_URI:str
    MILVUS_DB_NAME:str
    DEEPSEEK_API_KEY:str
    TAVILY_API_KEY:str

    @property
    def ASYNC_DATABASE_URL(self) -> str:
        """将同步数据库URL转换为异步URL"""
        url = self.DATABASE_URL
        if url.startswith("postgresql://"):
            return url.replace("postgresql://", "postgresql+asyncpg://", 1)
        return url

Config = Settings()