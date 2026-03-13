from dotenv import load_dotenv
import os
from tavily import TavilyClient
from src.config.config import Config
from langchain_core.tools import StructuredTool
from langgraph.prebuilt import ToolNode
from typing import List

load_dotenv()

tavily_client = TavilyClient(api_key=Config.TAVILY_API_KEY)


def search(search_queries: List[str], **_kwargs) -> str:
    """使用Tavily搜索多个关键词，返回合并结果"""
    all_text = []
    for q in search_queries:
        try:
            res = tavily_client.search(query=q, max_results=2)
            for r in res.get('results', []):
                all_text.append(f"来源: {r['url']}\n内容: {r['content']}")
        except Exception as e:
            all_text.append(f"搜索 '{q}' 时发生错误: {str(e)}")
    return "\n\n".join(all_text)
