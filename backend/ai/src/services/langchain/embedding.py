from langchain_community.embeddings import ZhipuAIEmbeddings
from src.config.config import Config
# 全局单例，所有模块共享
zhipu_embeddings = ZhipuAIEmbeddings(
    api_key=Config.ZHIPU_API_KEY,
    model="embedding-3",
    dimensions=2048
)