from typing import List, Dict
from pydantic import BaseModel, Field
from langchain_deepseek import ChatDeepSeek
from langchain_core.prompts import ChatPromptTemplate
from src.config.config import Config
class SuggestionResult(BaseModel):
    suggestions: List[str] = Field(description="按优先级排序的改进建议，3-6条")
    revision_plan: List[str] = Field(description="分步骤修改方案，3-5步")
    focus_areas: List[str] = Field(description="改进重点维度标签，如Grammar/Coherence/Task Response")
llm = ChatDeepSeek(
    api_key=Config.DEEPSEEK_API_KEY,
    model="deepseek-chat",
    temperature=0.2,
    max_tokens=2048,
).with_structured_output(SuggestionResult)
prompt = ChatPromptTemplate.from_messages([
    (
        "system",
        "You are an expert English writing coach for exam preparation.\n"
        "Generate practical, high-impact revision suggestions.\n"
        "Prioritize suggestions by expected score improvement.\n"
        "Avoid vague advice. Each suggestion must be actionable.\n"
        "Return structured output only."
    ),
    (
        "human",
        "Exam Type: {exam_type}\n"
        "Task Type: {task_type}\n\n"
        "Essay Topic:\n{topic}\n\n"
        "Essay Text:\n{essay_text}\n\n"
        "Current Overall Score:\n{band_score}\n\n"
        "Dimension Scores:\n{scores_text}\n\n"
        "Score Explanation:\n{score_explanation}\n\n"
        "Detected Errors:\n{errors_text}\n\n"
        "Please provide:\n"
        "1) 3-6 prioritized revision suggestions\n"
        "2) a short step-by-step revision plan\n"
        "3) key focus areas"
    ),
])
chain = prompt | llm