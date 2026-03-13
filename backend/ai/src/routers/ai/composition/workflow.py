from langgraph.graph import StateGraph, START, END

from .essay_state import EssayState
from .checkpoint import get_checkpointer
from .nodes.analyze_topic import analyze_topic
from .nodes.retrieve_samples import retrieve_samples
from .nodes.retrieve_rubric import retrieve_rubric
from .nodes.score_essay import score_essay
from .nodes.detect_errors import detect_errors
from .nodes.generate_suggestions import generate_suggestions


_workflow = None


def build_workflow():
    """
    构建作文批改工作流。

    流程：
    START -> analyze_topic
      -> retrieve_samples
      -> retrieve_rubric
      -> score_essay
      -> detect_errors
      -> generate_suggestions
      -> END
    """
    builder = StateGraph(EssayState)

    builder.add_node("analyze_topic", analyze_topic)
    builder.add_node("retrieve_samples", retrieve_samples)
    builder.add_node("retrieve_rubric", retrieve_rubric)
    builder.add_node("score_essay", score_essay)
    builder.add_node("detect_errors", detect_errors)
    builder.add_node("generate_suggestions", generate_suggestions)

    builder.add_edge(START, "analyze_topic")

    # analyze_topic 后并行检索范文与评分标准
    builder.add_edge("analyze_topic", "retrieve_samples")
    builder.add_edge("analyze_topic", "retrieve_rubric")

    builder.add_edge("retrieve_samples", "score_essay")
    builder.add_edge("retrieve_rubric", "score_essay")
    builder.add_edge("score_essay", "detect_errors")
    builder.add_edge("detect_errors", "generate_suggestions")
    builder.add_edge("generate_suggestions", END)
    checkpointer = get_checkpointer()
    return builder.compile(checkpointer=checkpointer)


def get_workflow():
    """获取可执行工作流（懒加载，避免导入阶段触发连接）。"""
    global _workflow
    if _workflow is None:
        _workflow = build_workflow()
    return _workflow


def draw_mermaid() -> str:
    """导出 Mermaid 文本，便于可视化流程图。"""
    return get_workflow().get_graph().draw_mermaid()
