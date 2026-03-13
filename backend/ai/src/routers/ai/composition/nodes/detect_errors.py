from typing import Dict, Any
from src.routers.ai.composition.essay_state import EssayState
from src.routers.ai.composition.chains.error_detector import chain, ErrorDetectionResult
def detect_errors(state: EssayState) -> Dict[str, Any]:
    result: ErrorDetectionResult = chain.invoke({
        "exam_type": state["exam_type"],
        "task_type": state["task_type"],
        "band_score": state.get("band_score", 0.0),
        "essay_text": state["essay_text"],
    })
    errors = [
        {
            "type": e.type,
            "original": e.original,
            "suggestion": e.suggestion,
            "reason": e.reason,
            "severity": e.severity,
        }
        for e in result.errors
    ]
    # 给前端高亮用（你 state 里叫 highlight_improvements）
    highlight_improvements = [
        {"original": e["original"], "suggestion": e["suggestion"], "reason": e["reason"]}
        for e in errors
    ]
    return {
        "errors": errors,
        "highlight_improvements": highlight_improvements,
        "current_step": "errors_detected",
    }