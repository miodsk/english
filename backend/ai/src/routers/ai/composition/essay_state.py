from typing import TypedDict, Annotated, List, Dict, Optional, Literal
from langgraph.graph import add_messages
from langchain_core.messages import BaseMessage

# 定义字面量类型，方便类型检查
TaskTypeLiteral = Literal[
    "data_graph", "image_drawing", "process_map", "opinion_essay", "letter", "notice"
]
ExamTypeLiteral = Literal["ielts", "cet-4", "cet-6", "kaoyan"]


def take_latest_step(current: Optional[str], new_value: Optional[str]) -> Optional[str]:
    """并发分支更新 current_step 时，保留最新非空值。"""
    return new_value if new_value is not None else current


class EssayState(TypedDict):
    """
    作文批改 Agent 状态
    """

    # ========== 输入数据 ==========
    essay_text: str
    """用户提交的作文文本"""

    exam_type: ExamTypeLiteral
    """考试类型：ielts/cet-4/cet-6/kaoyan"""

    task_type: TaskTypeLiteral
    """
    任务类型：
    - ielts: data_graph(小作文图表), letter(G类小作文), opinion_essay(大作文议论文)
    - cet/kaoyan: opinion_essay, notice, letter 等
    """

    topic: str
    """作文题目"""

    user_id: str
    """用户ID"""

    # ========== 检索结果 ==========
    topic_embedding: Optional[List[float]]
    """题目向量"""

    essay_embedding: Optional[List[float]]
    """正文向量"""

    retrieved_samples: List[Dict]
    """
    检索到的相似范文
    检索时会用到：filter="exam_type == essay_type and task_type == task_type"
    """

    retrieved_rubrics: List[Dict]
    """
    检索到的评分标准 (Scoring Standards)
    用于给 LLM 提供打分依据
    """

    # ========== 评分结果 ==========
    scores: Dict[str, float]
    band_score: float
    score_explanation: Optional[str]

    # ========== 错误分析与改进 ==========
    errors: List[Dict]
    suggestions: List[str]
    highlight_improvements: Optional[List[Dict]]

    # ========== 对话历史与控制 ==========
    messages: Annotated[List[BaseMessage], add_messages]
    iteration: int
    max_iterations: int
    revised_essay: Optional[str]
    previous_summary: Optional[str]

    # ========== 会话管理与状态 ==========
    thread_id: Optional[str]
    session_id: Optional[str]
    current_step: Annotated[Optional[str], take_latest_step]
    is_complete: bool
    needs_revision: bool


# ========== 更新后的初始状态工厂函数 ==========


def create_initial_state(
    essay_text: str,
    exam_type: ExamTypeLiteral,
    task_type: TaskTypeLiteral,
    topic: Optional[str] = None,
    user_id: Optional[str] = None,
    thread_id: Optional[str] = None,
    session_id: Optional[str] = None,
    revised_essay: Optional[str] = None,
    previous_summary: Optional[str] = None,
) -> EssayState:
    """
    创建初始状态
    """
    return EssayState(
        essay_text=essay_text,
        exam_type=exam_type,
        task_type=task_type,
        topic=topic,
        user_id=user_id,
        # 检索
        topic_embedding=None,
        essay_embedding=None,
        retrieved_samples=[],
        retrieved_rubrics=[],
        # 评分
        scores={},
        band_score=0.0,
        score_explanation=None,
        # 错误与建议
        errors=[],
        suggestions=[],
        highlight_improvements=None,
        # 对话与迭代
        messages=[],
        iteration=0,
        max_iterations=3,
        revised_essay=revised_essay,
        previous_summary=previous_summary,
        # 会话与状态
        thread_id=thread_id,
        session_id=session_id,
        current_step="initializing",
        is_complete=False,
        needs_revision=False,
    )
