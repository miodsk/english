architecture
英语 AI 学习平台架构设计
目录
• 概述
• 整体架构
• 功能模块设计
  • 1. 作文批改
  • 2. 词汇学习
  • 3. 口语练习
• 技术栈
• 数据模型
• API 设计
• 部署架构
---
概述
基于 LangGraph + Milvus + PostgreSQL 构建的英语学习平台，提供作文批改、词汇学习、口语练习三大核心功能。
核心特性
• 多轮对话持久化 - 通过 Checkpoint 实现学习进度保存
• 向量检索增强 - 基于知识库的智能内容推荐
• 个性化学习 - 根据用户历史数据定制学习路径
---
整体架构
┌─────────────────────────────────────────────────────────────────┐
│                         客户端层                                  │
│         (Web App / Mobile App / WeChat Mini Program)            │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                         API Gateway                              │
│                    (认证 / 限流 / 路由)                           │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                      业务服务层                                   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │  作文批改服务  │  │  词汇学习服务  │  │  口语练习服务  │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                      LangGraph Agent 层                          │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                    StateGraph Orchestrator                │   │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────┐         │   │
│  │  │ Essay Node │  │ Vocab Node │  │ Speaking   │         │   │
│  │  │            │  │            │  │ Node       │         │   │
│  │  └────────────┘  └────────────┘  └────────────┘         │   │
│  └──────────────────────────────────────────────────────────┘   │
│                              │                                   │
│                    ┌─────────┴─────────┐                        │
│                    │                   │                        │
│                    ▼                   ▼                        │
│           ┌──────────────┐   ┌──────────────┐                  │
│           │   Milvus     │   │  PostgreSQL  │                  │
│           │  (向量存储)   │   │ (Checkpoint) │                  │
│           └──────────────┘   └──────────────┘                  │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                        基础设施层                                 │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐       │
│  │   LLM    │  │  Whisper │  │   Redis  │  │  对象存储  │       │
│  │ (DeepSeek)│  │  (语音)   │  │  (缓存)  │  │  (录音等) │       │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘       │
└─────────────────────────────────────────────────────────────────┘
---
功能模块设计
1. 作文批改
1.1 业务流程
┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐
│ 提交作文 │───▶│ 评分    │───▶│ 错误标注 │───▶│ 改进建议 │───▶│ 用户修改 │
└─────────┘    └─────────┘    └─────────┘    └─────────┘    └─────────┘
                                                                  │
                    ┌─────────────────────────────────────────────┘
                    │
                    ▼
              ┌─────────┐    ┌─────────┐
              │ 再评分   │───▶│ 归档    │
              └─────────┘    └─────────┘
1.2 Agent StateGraph 设计
from typing import TypedDict, Annotated, List, Dict, Optional, Literal
from langgraph.graph import add_messages
from langchain_core.messages import BaseMessage

# 定义字面量类型，方便类型检查
TaskTypeLiteral = Literal["data_graph", "image_drawing", "process_map", "opinion_essay", "letter", "notice"]
ExamTypeLiteral = Literal["ielts", "cet-4", "cet-6", "kaoyan"]


class EssayState(TypedDict):
    """
    作文批改 Agent 状态
    """

    # ========== 输入数据 ==========
    essay_text: str
    """用户提交的作文文本"""

    essay_type: ExamTypeLiteral
    """考试类型：ielts/cet-4/cet-6/kaoyan"""

    task_type: TaskTypeLiteral
    """
    任务类型：
    - ielts: data_graph(小作文图表), letter(G类小作文), opinion_essay(大作文议论文)
    - cet/kaoyan: opinion_essay, notice, letter 等
    """

    topic: Optional[str]
    """作文题目"""

    user_id: Optional[str]
    """用户ID"""

    # ========== 检索结果 ==========
    topic_embedding: Optional[List[float]]
    """题目向量"""

    essay_embedding: Optional[List[float]]
    """正文向量"""

    retrieved_samples: List[Dict]
    """
    检索到的相似范文
    检索时会用到：filter="exam_type == essay_type and task_type == task_type"
    """

    retrieved_rubrics: List[Dict]
    """
    检索到的评分标准 (Scoring Standards)
    用于给 LLM 提供打分依据
    """

    # ========== 评分结果 ==========
    scores: Dict[str, float]
    band_score: float
    score_explanation: Optional[str]

    # ========== 错误分析与改进 ==========
    errors: List[Dict]
    suggestions: List[str]
    highlight_improvements: Optional[List[Dict]]

    # ========== 对话历史与控制 ==========
    messages: Annotated[List[BaseMessage], add_messages]
    iteration: int
    max_iterations: int
    revised_essay: Optional[str]

    # ========== 会话管理与状态 ==========
    thread_id: Optional[str]
    session_id: Optional[str]
    current_step: Optional[str]
    is_complete: bool
    needs_revision: bool


# ========== 更新后的初始状态工厂函数 ==========

def create_initial_state(
        essay_text: str,
        essay_type: ExamTypeLiteral,
        task_type: TaskTypeLiteral,
        topic: Optional[str] = None,
        user_id: Optional[str] = None,
        thread_id: Optional[str] = None,
        session_id: Optional[str] = None
) -> EssayState:
    """
    创建初始状态
    """
    return EssayState(
        essay_text=essay_text,
        essay_type=essay_type,
        task_type=task_type,
        topic=topic,
        user_id=user_id,

        # 检索
        topic_embedding=None,
        essay_embedding=None,
        retrieved_samples=[],
        retrieved_rubrics=[],

        # 评分
        scores={},
        band_score=0.0,
        score_explanation=None,

        # 错误与建议
        errors=[],
        suggestions=[],
        highlight_improvements=None,

        # 对话与迭代
        messages=[],
        iteration=0,
        max_iterations=3,
        revised_essay=None,

        # 会话与状态
        thread_id=thread_id,
        session_id=session_id,
        current_step="initializing",
        is_complete=False,
        needs_revision=False
    )
from typing import TypedDict, Annotated
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.postgres import PostgresSaver


# 节点定义
def analyze_topic(state: EssayState) -> EssayState:
    """分析题目要求"""
    pass

def retrieve_rubric(state: EssayState) -> EssayState:
    """从 Milvus 检索评分标准"""
    pass

def retrieve_samples(state: EssayState) -> EssayState:
    """从 Milvus 检索相似范文"""
    pass

def score_essay(state: EssayState) -> EssayState:
    """多维评分"""
    # IELTS: Task Response, Coherence, Lexical Resource, Grammar
    # 考研: 内容, 语言, 结构
    pass

def detect_errors(state: EssayState) -> EssayState:
    """错误检测与标注"""
    # 语法错误、词汇错误、逻辑问题
    pass

def generate_suggestions(state: EssayState) -> EssayState:
    """生成改进建议"""
    pass

def compare_with_history(state: EssayState) -> EssayState:
    """与历史作文对比，展示进步"""
    pass

def should_continue(state: EssayState) -> str:
    """判断是否继续修改"""
    if state["iteration"] >= 3:
        return "end"
    if state["revised_essay"]:
        return "rescore"
    return "wait"  # 等待用户输入

# 图构建
builder = StateGraph(EssayState)
builder.add_node("analyze_topic", analyze_topic)
builder.add_node("retrieve_rubric", retrieve_rubric)
builder.add_node("retrieve_samples", retrieve_samples)
builder.add_node("score_essay", score_essay)
builder.add_node("detect_errors", detect_errors)
builder.add_node("generate_suggestions", generate_suggestions)
builder.add_node("compare_with_history", compare_with_history)

builder.add_edge(START, "analyze_topic")
builder.add_edge("analyze_topic", "retrieve_rubric")
builder.add_edge("analyze_topic", "retrieve_samples")
builder.add_edge(["retrieve_rubric", "retrieve_samples"], "score_essay")
builder.add_edge("score_essay", "detect_errors")
builder.add_edge("detect_errors", "generate_suggestions")
builder.add_edge("generate_suggestions", "compare_with_history")
builder.add_conditional_edges("compare_with_history", should_continue, {
    "rescore": "score_essay",
    "end": END,
    "wait": END
})

# 编译
checkpointer = PostgresSaver.from_conn_string(DB_URI)
graph = builder.compile(checkpointer=checkpointer)
1.3 向量库数据设计
Collection: essay_rubrics (评分标准)
字段	类型	说明
id	str	唯一标识
exam_type	str	ielts_task1 / ielts_task2 / kaoyan
band_level	int	分数等级 (5-9)
criterion	str	评分维度
description	str	评分描述
embedding	float[1024]	向量
Collection: sample_essays (范文库)
class TaskType(str, Enum):
# 1. 描述类 (Descriptive)
DATA_GRAPH = "data_graph"  # 柱/线/饼/表 (雅思T1, 考研二)
IMAGE_DRAWING = "image_drawing"  # 漫画/图片 (考研一, 四六级)
PROCESS_MAP = "process_map"  # 流程图/地图 (雅思T1)

    # 2. 议论类 (Argumentative)
OPINION_ESSAY = "opinion_essay"  # 观点论证 (雅思T2, 四六级, 考研大作文)

    # 3. 应用类 (Practical)
LETTER = "letter"  # 书信 (考研小作文, 雅思G类)
NOTICE = "notice"  # 通知/告示 (考研小作文, 四六级)


class ExamType(str, Enum):
IELTS = "ielts"
CET4 = "cet-4"
CET6 = "cet-6"
KAOYAN = "kaoyan"
字段名	类型	说明	修改建议
id	int64 / varchar	唯一标识	Milvus 建议主键用 int64 (可自增) 或 varchar。
topic	varchar	题目文本	建议增加长度限制（如 512）。
topic_embedding	float[1024]	题目向量	保留。用于“找相似题目”。
essay_embedding	float[1024]	范文向量	新增。用户搜“环境描写”时，搜范文比搜题目更准。
essay_text	varchar	范文正文	建议使用长文本存储。
exam_type	varchar	考试类型	原 essay_type，建议存 ielts, cet4 等。
task_type	varchar	任务类型	必增。存我们刚才整理的 data_graph, opinion_essay 等。
band_score	float	分数	保留。
tags	json / array	话题标签	Milvus 2.x 支持 JSON 或 Array，方便存 ["env", "tech"]。
Environment (环境、污染、全球变暖)
Education (教育、学校、课程)
Technology (人工智能、互联网、社交媒体)
Society (社会问题、人口、城市化)
Culture & Tradition (文化遗产、语言、旅游)
Government & Economy (政府职能、税收、全球化)
Health (运动、饮食、医疗)
Family & Children (家庭教育、青少年犯罪)
Work & Employment (职场、远程办公、退休)

Collection: error_patterns (错误模式)
字段	类型	说明
id	str	唯一标识
error_type	str	错误类型
error_pattern	str	错误模式描述
correction	str	修正建议
embedding	float[1024]	向量
Collection: user_essays (用户作文)
字段	类型	说明
id	str	唯一标识
user_id	str	用户ID
topic	str	题目
essay_text	str	作文内容
scores	dict	分数
errors	list	错误列表
created_at	datetime	创建时间
---
2. 词汇学习
2.1 业务流程
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│  选择词库    │───▶│  学习/测试   │───▶│  结果反馈    │
└─────────────┘    └─────────────┘    └─────────────┘
                          │
                          ▼
              ┌───────────────────────┐
              │  错词归档 → 复习提醒    │
              └───────────────────────┘
2.2 Agent StateGraph 设计
from typing import TypedDict, Literal
from langgraph.graph import StateGraph, START, END

class VocabState(TypedDict):
    user_id: str
    mode: Literal["learn", "test", "review"]
    word_list: list[str]  # 当前学习的词汇列表
    current_word: str  # 当前词汇
    context_sentences: list[str]  # 语境例句
    user_answer: str  # 用户答案
    is_correct: bool  # 是否正确
    wrong_words: list[dict]  # 错词列表
    mastered_words: list[str]  # 已掌握词汇
    review_schedule: dict  # 复习计划

# 节点定义
def select_words(state: VocabState) -> VocabState:
    """根据用户水平和历史选择词汇"""
    # 从 Milvus 检索适合的词汇
    pass

def retrieve_word_info(state: VocabState) -> VocabState:
    """获取词汇详细信息"""
    # 从 Milvus 检索释义、例句、搭配
    pass

def generate_context(state: VocabState) -> VocabState:
    """生成语境例句"""
    # LLM 生成个性化例句
    pass

def create_test_question(state: VocabState) -> VocabState:
    """生成测试题目"""
    # 选择题、填空题、翻译题
    pass

def evaluate_answer(state: VocabState) -> VocabState:
    """评估答案"""
    pass

def update_progress(state: VocabState) -> VocabState:
    """更新学习进度"""
    # 更新向量库中的用户词汇记录
    pass

def schedule_review(state: VocabState) -> VocabState:
    """安排复习计划（艾宾浩斯遗忘曲线）"""
    pass

# 图构建
builder = StateGraph(VocabState)
builder.add_node("select_words", select_words)
builder.add_node("retrieve_word_info", retrieve_word_info)
builder.add_node("generate_context", generate_context)
builder.add_node("create_test_question", create_test_question)
builder.add_node("evaluate_answer", evaluate_answer)
builder.add_node("update_progress", update_progress)
builder.add_node("schedule_review", schedule_review)

# 学习模式
builder.add_edge(START, "select_words")
builder.add_edge("select_words", "retrieve_word_info")
builder.add_edge("retrieve_word_info", "generate_context")
builder.add_edge("generate_context", END)

# 测试模式
# builder.add_edge("select_words", "create_test_question")
# builder.add_edge("create_test_question", "evaluate_answer")
# builder.add_edge("evaluate_answer", "update_progress")
# builder.add_edge("update_progress", "schedule_review")

graph = builder.compile(checkpointer=checkpointer)
2.3 向量库数据设计
Collection: vocabulary (词汇库)
字段	类型	说明
id	str	唯一标识
word	str	单词
word_embedding	float[1024]	单词向量
phonetic	str	音标
definitions	list[dict]	释义列表 [{pos, meaning, examples}]
collocations	list[str]	搭配
synonyms	list[str]	同义词
antonyms	list[str]	反义词
difficulty	int	难度等级 (1-5)
exam_frequency	dict	考试频率 {ielts: high, kaoyan: medium}
Collection: user_vocabulary_progress (用户词汇进度)
字段	类型	说明
id	str	唯一标识
user_id	str	用户ID
word	str	单词
status	str	learning / mastered / reviewing
correct_count	int	正确次数
wrong_count	int	错误次数
last_review_at	datetime	上次复习时间
next_review_at	datetime	下次复习时间
ease_factor	float	遗忘曲线因子
Collection: word_contexts (词汇语境)
字段	类型	说明
id	str	唯一标识
word	str	单词
sentence	str	例句
source	str	来源 (新闻/电影/考试真题)
difficulty	int	难度
embedding	float[1024]	句子向量
---
3. 口语练习
3.1 业务流程
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│  选择话题    │───▶│ AI对话练习  │───▶│ 语音分析    │───▶│ 反馈报告    │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
                         │
                         ▼
              ┌───────────────────────┐
              │  对话历史持久化         │
              └───────────────────────┘
3.2 Agent StateGraph 设计
from typing import TypedDict, Literal
from langgraph.graph import StateGraph, START, END
from langchain_core.messages import HumanMessage, AIMessage

class SpeakingState(TypedDict):
    user_id: str
    topic: str  # 话题
    topic_type: Literal["ielts_part1", "ielts_part2", "ielts_part3", "daily"]
    examiner_persona: dict  # 考官人设
    conversation_history: list  # 对话历史
    current_question: str  # 当前问题
    user_response_audio: bytes  # 用户录音
    user_response_text: str  # 转写文本
    grammar_errors: list  # 语法错误
    pronunciation_issues: list  # 发音问题
    fluency_score: float  # 流利度分数
    feedback: str  # 反馈

# 节点定义
def select_topic(state: SpeakingState) -> SpeakingState:
    """从 Milvus 检索话题"""
    pass

def load_examiner_persona(state: SpeakingState) -> SpeakingState:
    """加载考官人设"""
    # 从向量库检索考官风格
    pass

def generate_question(state: SpeakingState) -> SpeakingState:
    """生成下一个问题"""
    # 基于话题和对话历史
    pass

def transcribe_audio(state: SpeakingState) -> SpeakingState:
    """语音转文字"""
    # 调用 Whisper API
    pass

def analyze_grammar(state: SpeakingState) -> SpeakingState:
    """语法分析"""
    pass

def analyze_pronunciation(state: SpeakingState) -> SpeakingState:
    """发音分析"""
    # 需要对比音素
    pass

def evaluate_fluency(state: SpeakingState) -> SpeakingState:
    """评估流利度"""
    # 语速、停顿、填充词
    pass

def generate_feedback(state: SpeakingState) -> SpeakingState:
    """生成综合反馈"""
    pass

def decide_continue(state: SpeakingState) -> str:
    """决定是否继续对话"""
    # 根据对话轮数或用户意图
    pass

# 图构建
builder = StateGraph(SpeakingState)
builder.add_node("select_topic", select_topic)
builder.add_node("load_examiner_persona", load_examiner_persona)
builder.add_node("generate_question", generate_question)
builder.add_node("transcribe_audio", transcribe_audio)
builder.add_node("analyze_grammar", analyze_grammar)
builder.add_node("analyze_pronunciation", analyze_pronunciation)
builder.add_node("evaluate_fluency", evaluate_fluency)
builder.add_node("generate_feedback", generate_feedback)

builder.add_edge(START, "select_topic")
builder.add_edge("select_topic", "load_examiner_persona")
builder.add_edge("load_examiner_persona", "generate_question")
builder.add_edge("generate_question", END)  # 等待用户响应

# 用户响应后
builder.add_edge("transcribe_audio", "analyze_grammar")
builder.add_edge("analyze_grammar", "analyze_pronunciation")
builder.add_edge("analyze_pronunciation", "evaluate_fluency")
builder.add_edge("evaluate_fluency", "generate_feedback")
builder.add_conditional_edges("generate_feedback", decide_continue, {
    "continue": "generate_question",
    "end": END
})

graph = builder.compile(checkpointer=checkpointer)
3.3 向量库数据设计
Collection: speaking_topics (口语话题库)
字段	类型	说明
id	str	唯一标识
topic	str	话题内容
topic_type	str	ielts_part1 / ielts_part2 / ielts_part3 / daily
questions	list[str]	相关问题列表
keywords	list[str]	关键词
difficulty	int	难度等级
embedding	float[1024]	话题向量
Collection: examiner_personas (考官人设)
字段	类型	说明
id	str	唯一标识
name	str	考官名称
style	str	风格描述 (friendly/strict/professional)
question_patterns	list[str]	提问模式
follow_up_strategies	list[str]	追问策略
system_prompt	str	系统提示词
Collection: speaking_expressions (口语表达库)
字段	类型	说明
id	str	唯一标识
expression	str	表达
category	str	类别 (opening/opinion/agreement/etc)
formality	str	正式程度
example_context	str	使用场景
embedding	float[1024]	向量
Collection: user_speaking_history (口语历史)
字段	类型	说明
id	str	唯一标识
user_id	str	用户ID
session_id	str	会话ID
topic	str	话题
conversation	list[dict]	对话记录
feedback	dict	反馈详情
scores	dict	分数
created_at	datetime	创建时间
---
技术栈
后端
组件	技术选型	说明
框架	FastAPI	Python 异步 Web 框架
Agent 框架	LangGraph	多状态工作流编排
LLM	DeepSeek / GPT-4o	主模型
Embedding	text-embedding-3-small	文本向量化
向量数据库	Milvus	向量检索
关系数据库	PostgreSQL	Checkpoint + 元数据
缓存	Redis	会话缓存、限流
语音识别	Whisper API	语音转文字
对象存储	MinIO / OSS	录音文件存储
前端
组件	技术选型
框架	Next.js / React
UI	Tailwind CSS + shadcn/ui
状态管理	Zustand
音频处理	Web Audio API
---
数据模型
PostgreSQL 核心表
-- 用户表
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(100),
    level VARCHAR(50),  -- 英语水平
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 学习会话表
CREATE TABLE learning_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    session_type VARCHAR(50),  -- essay/vocab/speaking
    status VARCHAR(50),  -- active/completed
    thread_id VARCHAR(255),  -- LangGraph thread_id
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ended_at TIMESTAMP
);

-- 用户进度表
CREATE TABLE user_progress (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    skill_type VARCHAR(50),  -- writing/vocabulary/speaking
    total_sessions INT DEFAULT 0,
    total_time_minutes INT DEFAULT 0,
    improvement_score FLOAT,
    last_practice_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
---
API 设计
作文批改
POST /api/essay/submit
Request: { essay_text, essay_type, topic? }
Response: { session_id, thread_id }

GET /api/essay/result/{session_id}
Response: { scores, errors, suggestions, sample_essays }

POST /api/essay/revise/{session_id}
Request: { revised_essay }
Response: { new_scores, improvements }
词汇学习
POST /api/vocab/start
Request: { mode, word_list?, difficulty? }
Response: { session_id, words, current_word }

POST /api/vocab/answer
Request: { session_id, word, answer }
Response: { is_correct, explanation, next_word? }

GET /api/vocab/progress
Response: { mastered_count, learning_count, review_due }
口语练习
POST /api/speaking/start
Request: { topic_type, topic? }
Response: { session_id, first_question }

POST /api/speaking/respond
Request: { session_id, audio_data }
Response: { transcription, feedback, next_question? }

GET /api/speaking/report/{session_id}
Response: { grammar_errors, pronunciation_issues, fluency_score, suggestions }
---
部署架构
┌─────────────────────────────────────────────────────────────┐
│                        Kubernetes Cluster                    │
│  ┌──────────────────────────────────────────────────────┐   │
│  │                    Ingress Controller                 │   │
│  └──────────────────────────────────────────────────────┘   │
│                            │                                 │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │ API Service │  │ API Service │  │ API Service │         │
│  │   (Pod 1)   │  │   (Pod 2)   │  │   (Pod 3)   │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
│                            │                                 │
│  ┌──────────────────────────────────────────────────────┐   │
│  │                   Service Layer                       │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  │   │
│  │  │ Milvus     │  │ PostgreSQL  │  │   Redis     │  │   │
│  │  │ Cluster    │  │ Cluster     │  │ Cluster     │  │   │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
---
下一步计划
1. Phase 1: 作文批改 MVP
  • 实现基础评分流程
  • 导入 IELTS 评分标准到 Milvus
  • 集成 Checkpoint 持久化
2. Phase 2: 词汇学习
  • 构建词汇向量库
  • 实现艾宾浩斯复习算法
  • 错词本功能
3. Phase 3: 口语练习
  • Whisper 集成
  • 对话流程实现
  • 发音分析（可选）
---
参考资源
• LangGraph Documentation
• Milvus Documentation
• LangChain Checkpoint PostgreSQL