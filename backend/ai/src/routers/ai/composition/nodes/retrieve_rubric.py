from src.services.langchain.embedding import zhipu_embeddings
from src.config.config import Config
from src.db.milvus_client import milvus_client
from src.routers.ai.composition.essay_state import EssayState
from src.db.milvus_client import milvus_client
from ..essay_state import EssayState
COLLECTION_NAME = "essay_rubrics"

client = milvus_client.get_client()
def retrieve_rubric(state: EssayState) -> dict:
    """
    检索评分标准节点

    职责：
    1. 根据 exam_type 和 task_type 精确过滤
    2. 返回所有相关的评分标准（各维度、各分数段）

    Args:
        state: 当前状态

    Returns:
        dict: 包含 retrieved_rubrics 列表
    """
    # 1. 获取过滤条件
    exam_type = state["exam_type"]
    task_type = state["task_type"]

    # 2. 构建过滤表达式
    filter_expr = f'exam_type == "{exam_type}" and task_type == "{task_type}"'

    # 3. 执行查询（非向量检索，直接条件查询）
    results = client.query(
        collection_name=COLLECTION_NAME,
        filter=filter_expr,
        output_fields=["dimension", "band_score", "description"],
        limit=100  # 确保获取所有评分标准
    )

    # 4. 按维度和分数段组织结果（可选优化）
    rubrics_by_dimension = {}
    for rubric in results:
        dimension = rubric.get("dimension", "unknown")
        if dimension not in rubrics_by_dimension:
            rubrics_by_dimension[dimension] = []
        rubrics_by_dimension[dimension].append({
            "band_score": rubric.get("band_score"),
            "description": rubric.get("description")
        })

    # 5. 返回状态更新
    return {
        "retrieved_rubrics": results,  # 原始列表，供 LLM 使用
        "current_step": "rubrics_retrieved"
    }