from typing import List, Literal
from pydantic import BaseModel, Field
from langchain_deepseek import ChatDeepSeek
from langchain_core.prompts import ChatPromptTemplate
from src.config.config import Config
class ErrorItem(BaseModel):
    type: Literal["grammar", "spelling", "word_choice", "cohesion", "task_response"]
    original: str = Field(description="原始有问题片段")
    suggestion: str = Field(description="建议替换片段")
    reason: str = Field(description="错误原因")
    severity: Literal["low", "medium", "high"] = "medium"
class ErrorDetectionResult(BaseModel):
    errors: List[ErrorItem] = Field(default_factory=list)
    summary: str = Field(description="整体错误概览")
llm = ChatDeepSeek(
    api_key=Config.DEEPSEEK_API_KEY,
    model="deepseek-chat",
    temperature=0.1,
    max_tokens=2048,
)
structured_llm = llm.with_structured_output(ErrorDetectionResult)
prompt = ChatPromptTemplate.from_messages([
    ("system",
     "You are an expert English writing proofreader.\n"
     "Detect concrete errors and provide actionable corrections.\n"
     "Return structured output only."),
    ("human",
     "Exam Type: {exam_type}\n"
     "Task Type: {task_type}\n"
     "Band Score: {band_score}\n\n"
     "Essay:\n{essay_text}\n")
])
chain = prompt | structured_llm