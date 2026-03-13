from typing import Dict, Any
from src.routers.ai.composition.essay_state import EssayState
from src.routers.ai.composition.chains.suggestion_provider import chain, SuggestionResult
def _format_scores(scores: Dict[str, float]) -> str:
    if not scores:
        return "No dimension scores."
    return "\n".join([f"- {k}: {v}" for k, v in scores.items()])
def _format_errors(errors: list[dict], max_items: int = 12) -> str:
    if not errors:
        return "No detected errors."
    lines = []
    for e in errors[:max_items]:
        lines.append(
            f"- type={e.get('type','unknown')} | "
            f"original={e.get('original','')} | "
            f"suggestion={e.get('suggestion','')} | "
            f"reason={e.get('reason','')} | "
            f"severity={e.get('severity','medium')}"
        )
    return "\n".join(lines)


def _compute_needs_revision(band_score: float, errors: list[dict]) -> bool:
    """
    根据分数与错误严重度判断是否需要继续修改。

    规则（可后续按业务调优）：
    - band_score >= 7.0 且无 high 错误，且 medium <= 1 -> 不需要强制修改
    - band_score >= 6.5 且无 high 错误，且总错误数 <= 2 -> 不需要强制修改
    - 其他情况 -> 需要继续修改
    """
    high_count = sum(1 for e in errors if e.get("severity") == "high")
    medium_count = sum(1 for e in errors if e.get("severity") == "medium")
    if band_score >= 7.0 and high_count == 0 and medium_count <= 1:
        return False
    if band_score >= 6.5 and high_count == 0 and len(errors) <= 2:
        return False
    return True

def generate_suggestions(state: EssayState) -> Dict[str, Any]:
    band_score = float(state.get("band_score", 0.0))
    errors = state.get("errors", [])

    result: SuggestionResult = chain.invoke({
        "exam_type": state["exam_type"],
        "task_type": state["task_type"],
        "topic": state.get("topic", ""),
        "essay_text": state["essay_text"],
        "band_score": band_score,
        "scores_text": _format_scores(state.get("scores", {})),
        "score_explanation": state.get("score_explanation", ""),
        "errors_text": _format_errors(errors),
    })
    # 你当前 EssayState 只有 suggestions 字段；其余放进说明里避免丢信息
    merged_suggestions = list(result.suggestions)
    if result.revision_plan:
        merged_suggestions.append("【Revision Plan】")
        merged_suggestions.extend([f"- {x}" for x in result.revision_plan])
    if result.focus_areas:
        merged_suggestions.append("【Focus Areas】" + ", ".join(result.focus_areas))
    return {
        "suggestions": merged_suggestions,
        "current_step": "suggestions_generated",
        "needs_revision": _compute_needs_revision(band_score, errors),
    }
