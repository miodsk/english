from langchain_deepseek import ChatDeepSeek
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

from src.config.config import Config

reasoning_llm = ChatDeepSeek(
    api_key=Config.DEEPSEEK_API_KEY,
    model="deepseek-reasoner",
    temperature=0.7,
)

reasoning_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "你是一个擅长深度推理与复杂问题分析的助手。"
            "你的回答要结构化、分步骤、给出结论与依据。"
            "当存在搜索上下文时，优先基于上下文推理，不要凭空编造。",
        ),
        (
            "human",
            "问题:\n{message}\n\n"
            "搜索上下文(可能为空):\n{search_context}\n\n"
            "请按以下结构回答:\n"
            "1) 问题拆解\n"
            "2) 关键分析\n"
            "3) 结论\n"
            "4) 可执行建议(如适用)",
        ),
    ]
)

reasoning_chain = reasoning_prompt | reasoning_llm | StrOutputParser()
