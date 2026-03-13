from typing import Dict, List
from pydantic import BaseModel, Field
from langchain_deepseek import ChatDeepSeek
from langchain_core.prompts import ChatPromptTemplate
from src.config.config import Config


class DimensionScore(BaseModel):
    dimension: str = Field(description="评分维度名称")
    score: float = Field(description="维度分数")
    comment: str = Field(description="该维度评分理由")


class EssayScoreResult(BaseModel):
    scores: List[DimensionScore] = Field(description="各维度评分")
    band_score: float = Field(description="总分")
    overall_comment: str = Field(description="整体评价")
    strengths: List[str] = Field(default_factory=list, description="优点")
    weaknesses: List[str] = Field(default_factory=list, description="不足")


score_llm = ChatDeepSeek(
    api_key=Config.DEEPSEEK_API_KEY, model="deepseek-chat", temperature=0.2
).with_structured_output(EssayScoreResult)


def _format_rubrics(rubrics: List[Dict]) -> str:
    if not rubrics:
        return "No rubrics found."
    lines = []
    for r in rubrics:
        lines.append(
            f"- [{r.get('dimension', 'unknown')}] "
            f"{r.get('band_score', 0)}: {r.get('description', '')}"
        )
    return "\n".join(lines)


def _format_samples(samples: List[Dict], top_k: int = 2) -> str:
    if not samples:
        return "No reference samples."
    chunks = []
    for i, s in enumerate(samples[:top_k], 1):
        chunks.append(
            f"[Sample {i}] topic={s.get('topic', '')}, "
            f"band={s.get('band_score', 0)}\n{s.get('essay_text', '')[:500]}"
        )
    return "\n\n".join(chunks)


prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are an expert English writing examiner.\n"
            "Score strictly by provided rubrics.\n"
            "Return structured result only.",
        ),
        (
            "human",
            "Exam Type: {exam_type}\n"
            "Task Type: {task_type}\n\n"
            "Previous Review Summary:\n{previous_summary}\n\n"
            "Topic:\n{topic}\n\n"
            "Essay:\n{essay_text}\n\n"
            "Rubrics:\n{rubrics_text}\n\n"
            "Reference Samples:\n{samples_text}\n\n"
            "If previous summary is not 'N/A', explicitly evaluate improvement against previous weaknesses.",
        ),
    ]
)
chain = prompt | score_llm
