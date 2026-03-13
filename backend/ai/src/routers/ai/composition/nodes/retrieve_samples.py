from src.config.config import Config
from src.db.milvus_client import milvus_client
from src.services.langchain.embedding import zhipu_embeddings
from src.db.milvus_client import milvus_client
from ..essay_state import EssayState

# 获取 Milvus 客户端
client = milvus_client.get_client()
COLLECTION_NAME = "sample_essays"


def retrieve_samples(state: EssayState) -> dict:
    """
    检索相似范文节点

    职责：
    1. 用 topic_embedding 在 Milvus 中检索相似范文
    2. 根据 exam_type 和 task_type 过滤
    3. 返回 top-k 相似范文

    Args:
        state: 当前状态（必须包含 topic_embedding）

    Returns:
        dict: 包含 retrieved_samples 列表
    """
    # 1. 获取 embedding（由 analyze_topic 生成）
    topic_embedding = state["topic_embedding"]

    # 2. 构建过滤条件
    exam_type = state["exam_type"]
    task_type = state["task_type"]

    # Milvus 过滤表达式
    filter_expr = f'exam_type == "{exam_type}" and task_type == "{task_type}"'

    # 3. 执行向量检索
    results = client.search(
        collection_name=COLLECTION_NAME,
        data=[topic_embedding],
        anns_field="topic_embedding",
        search_params={"metric_type": "L2", "params": {"ef": 64}},
        limit=5,
        filter=filter_expr,
        output_fields=["topic", "essay_text", "band_score", "tags"]
    )
    # 4. 解析结果
    samples = []
    for hits in results:
        for hit in hits:
            samples.append({
                "id": hit["id"],
                "topic": hit["entity"].get("topic", ""),
                "essay_text": hit["entity"].get("essay_text", ""),
                "band_score": hit["entity"].get("band_score", 0),
                "tags": hit["entity"].get("tags", []),
                "distance": hit["distance"]  # 相似度距离
            })
    # 5. 返回状态更新
    return {
        "retrieved_samples": samples,
        "current_step": "samples_retrieved"
    }

