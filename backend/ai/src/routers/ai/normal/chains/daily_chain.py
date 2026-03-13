from langchain_deepseek import ChatDeepSeek
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

from src.config.config import Config

daily_llm = ChatDeepSeek(
    api_key=Config.DEEPSEEK_API_KEY,
    model="deepseek-chat",
    temperature=0.7,
)

daily_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "你是一个自然、友好、实用的日常对话助手。"
            "当存在搜索上下文时，优先使用上下文回答，并在不确定时明确说明。",
        ),
        (
            "human",
            "用户消息:\n{message}\n\n"
            "搜索上下文(可能为空):\n{search_context}\n\n"
            "请给出清晰、简洁、可执行的回答。",
        ),
    ]
)

daily_chain = daily_prompt | daily_llm | StrOutputParser()
