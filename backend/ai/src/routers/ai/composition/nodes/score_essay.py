from src.routers.ai.composition.chains.score_grader import (
    chain,
    EssayScoreResult,
    _format_rubrics,
    _format_samples,
)
from src.routers.ai.composition.essay_state import EssayState
from typing import Dict, Any


def score_essay(state: EssayState) -> Dict[str, Any]:
    essay_text = state["essay_text"]
    topic = state.get("topic", "")
    exam_type = state["exam_type"]
    task_type = state["task_type"]
    rubrics = state.get("retrieved_rubrics", [])
    samples = state.get("retrieved_samples", [])
    previous_summary = state.get("previous_summary", "N/A") or "N/A"
    result: EssayScoreResult = chain.invoke(
        {
            "exam_type": exam_type,
            "task_type": task_type,
            "previous_summary": previous_summary,
            "topic": topic,
            "essay_text": essay_text,
            "rubrics_text": _format_rubrics(rubrics),
            "samples_text": _format_samples(samples),
        }
    )
    # 转为你 EssayState 当前字段结构
    scores_dict = {item.dimension: float(item.score) for item in result.scores}
    explanation = result.overall_comment
    if result.strengths:
        explanation += "\n\n优点:\n" + "\n".join([f"- {x}" for x in result.strengths])
    if result.weaknesses:
        explanation += "\n\n不足:\n" + "\n".join([f"- {x}" for x in result.weaknesses])
    return {
        "scores": scores_dict,
        "band_score": float(result.band_score),
        "score_explanation": explanation,
        "current_step": "scored",
    }
