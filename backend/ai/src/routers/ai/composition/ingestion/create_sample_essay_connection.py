from pymilvus import DataType
from enum import Enum
from langchain_community.embeddings import ZhipuAIEmbeddings
from src.config.config import Config
# 1. 导入你封装好的实例
from src.db.milvus_client import milvus_client


# --- 1. 定义枚举 ---
class TaskType(str, Enum):
    DATA_GRAPH = "data_graph"
    IMAGE_DRAWING = "image_drawing"
    PROCESS_MAP = "process_map"
    OPINION_ESSAY = "opinion_essay"
    LETTER = "letter"
    NOTICE = "notice"


class ExamType(str, Enum):
    IELTS = "ielts"
    CET4 = "cet-4"
    CET6 = "cet-6"
    KAOYAN = "kaoyan"


# --- 2. 初始化嵌入模型 ---
embeddings = ZhipuAIEmbeddings(
    api_key=Config.ZHIPU_API_KEY,
    model='embedding-3',
    dimensions=2048
)

# --- 3. 获取 Client 并执行逻辑 ---
client = milvus_client.get_client()
collection_name = "sample_essays"

# 🔑 核心逻辑：如果有集合，就什么都不做
if client.has_collection(collection_name):
    print(f"ℹ️ 集合 '{collection_name}' 已存在，跳过创建步骤。")
else:
    print(f"🚀 集合 '{collection_name}' 不存在，正在初始化...")

    # A. 创建 Schema
    schema = client.create_schema(
        auto_id=True,
        enable_dynamic_field=True
    )

    # B. 添加字段 (注意：此处必须使用 dim 参数)
    schema.add_field(field_name="id", datatype=DataType.INT64, is_primary=True)
    schema.add_field(field_name="topic", datatype=DataType.VARCHAR, max_length=1024)
    schema.add_field(field_name="essay_text", datatype=DataType.VARCHAR, max_length=65535)
    schema.add_field(field_name="exam_type", datatype=DataType.VARCHAR, max_length=20)
    schema.add_field(field_name="task_type", datatype=DataType.VARCHAR, max_length=50)
    schema.add_field(field_name="band_score", datatype=DataType.FLOAT)
    schema.add_field(field_name="tags", datatype=DataType.JSON)

    # 向量字段：dim=2048
    schema.add_field(field_name="topic_embedding", datatype=DataType.FLOAT_VECTOR, dim=2048)
    schema.add_field(field_name="essay_embedding", datatype=DataType.FLOAT_VECTOR, dim=2048)

    # C. 配置索引参数
    index_params = client.prepare_index_params()

    index_params.add_index(
        field_name="topic_embedding",
        index_type="HNSW",
        metric_type="L2",
        params={"M": 16, "efConstruction": 64}
    )
    index_params.add_index(
        field_name="essay_embedding",
        index_type="HNSW",
        metric_type="L2",
        params={"M": 16, "efConstruction": 64}
    )

    # D. 执行创建
    client.create_collection(
        collection_name=collection_name,
        schema=schema,
        index_params=index_params
    )

    # E. 加载集合
    client.load_collection(collection_name)
    print(f"✅ 集合 '{collection_name}' 创建并加载成功！")

# 后续代码可以直接开始使用 client 进行查询或插入...