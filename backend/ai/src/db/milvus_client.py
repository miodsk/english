# 注意：现在直接从 pymilvus 导入 MilvusClient
from pymilvus import MilvusClient
from src.config.config import Config

class MyMilvusWrapper:
    """封装官网推荐的 MilvusClient"""

    def __init__(self):
        # 使用官网推荐的初始化方式
        self.client = MilvusClient(
            uri=Config.MILVUS_URI,  # 必须是 "http://localhost:19530"
            db_name=Config.MILVUS_DB_NAME
        )
    def get_client(self ):
         return self.client
    def list_collections(self):
        # 新版接口列出集合非常简单
        return self.client.list_collections()

    def has_collection(self, collection_name: str):
        return self.client.has_collection(collection_name)

    def drop_collection(self, collection_name: str):
        if self.has_collection(collection_name):
            self.client.drop_collection(collection_name)
            print(f"🗑️ 已删除集合: {collection_name}")


# 实例化
milvus_client = MyMilvusWrapper()