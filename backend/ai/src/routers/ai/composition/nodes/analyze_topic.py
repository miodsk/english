from langchain_community.embeddings import ZhipuAIEmbeddings
from src.config.config import Config
from ..essay_state import EssayState
from src.services.langchain.embedding import zhipu_embeddings


def analyze_topic(state: EssayState) -> dict:
    """
    分析题目节点 - Graph 的入口节点

    职责：
    1. 确保 topic 存在（如果用户没提供，从作文中提取）
    2. 生成 topic_embedding（用于检索相似范文/评分标准）
    3. 生成 essay_embedding（用于语义分析）

    Args:
        state: 当前 EssayState

    Returns:
        dict: 状态更新，包含 topic、两个 embedding、current_step
    """
    # 1. 获取或生成 topic
    topic = state.get("topic")
    if not topic:
        # 没有题目时，取作文前 200 字符作为"伪题目"
        topic = state["essay_text"][:200]

    # 2. 生成 embedding
    topic_embedding = zhipu_embeddings.embed_query(topic)
    essay_embedding = zhipu_embeddings.embed_query(state["essay_text"])

    # 3. 返回状态更新
    return {
        "topic": topic,
        "topic_embedding": topic_embedding,
        "essay_embedding": essay_embedding,
        "current_step": "topic_analyzed"
    }