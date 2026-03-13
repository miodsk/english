from typing import Dict, Any, List
from pydantic import BaseModel, Field
from langchain_deepseek import ChatDeepSeek
from langchain_core.prompts import ChatPromptTemplate
from src.config.config import Config
from ..essay_state import EssayState
# 1) 结构化输出模型
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

llm = ChatDeepSeek(
    model="deepseek-reasoner",
    api_key=Config.DEEPSEEK_API_KEY,
    temperature=0.2,
).with_structured_output(EssayScoreResult)
