# AI 对话存储详解

> 本文档面向新手，从零开始讲解项目中的两种存储机制：History Store 和 LangGraph Checkpoint

---

## 目录

1. [为什么要存储？](#一为什么要存储)
2. [History Store 详解](#二history-store-详解)
3. [LangGraph Checkpoint 详解](#三langgraph-checkpoint-详解)
4. [两者的区别与联系](#四两者的区别与联系)
5. [实战：数据如何流转](#五实战数据如何流转)
6. [总结](#六总结)

---

## 一、为什么要存储？

### 1.1 问题场景

想象你正在使用一个 AI 作文批改应用：

```
用户: 请帮我批改这篇作文...
AI: 好的，这篇作文得分 6.5 分，主要问题是...

（过了一会儿）

用户: 我修改了，再帮我批改一次
AI: ??? （如果不存储，AI 不记得之前批改过什么）
```

### 1.2 需要存储的内容

| 需求 | 存储内容 | 谁来处理 |
|------|----------|----------|
| 用户查看历史记录 | 用户消息 + AI回复 | **History Store** |
| AI 记住上下文 | 工作流的完整状态 | **Checkpoint** |
| 作文改稿对比 | 上次的分数、错误、建议 | **Checkpoint** |

### 1.3 两种存储的关系

```
┌─────────────────────────────────────────────────────────────┐
│                      用户视角                                │
│  "我想看我的历史对话记录"                                    │
│                          ↓                                  │
│                   History Store                             │
│              （存储用户消息 + AI回复）                        │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                      AI 视角                                 │
│  "我需要记住上次的工作状态，才能继续工作"                    │
│                          ↓                                  │
│                    Checkpoint                               │
│          （存储工作流的完整状态：分数、错误、建议...）        │
└─────────────────────────────────────────────────────────────┘
```

---

## 二、History Store 详解

### 2.1 是什么？

**History Store = 对话历史存储**

类比：微信聊天记录。你可以随时翻看历史消息。

### 2.2 存什么？

```
┌─────────────────────────────────────────┐
│           History Store 内容             │
├─────────────────────────────────────────┤
│  线程元数据 (threads 表)                 │
│  - thread_id: 会话ID                     │
│  - user_id: 用户ID                       │
│  - topic: 话题/题目                      │
│  - preview: 预览文本                      │
│  - updated_at: 更新时间                  │
├─────────────────────────────────────────┤
│  消息内容 (messages 表)                  │
│  - role: "user" 或 "assistant"          │
│  - content: 消息内容                     │
│  - created_at: 创建时间                  │
└─────────────────────────────────────────┘
```

### 2.3 数据库表结构

#### threads 表（线程表）

```sql
CREATE TABLE composition_history_threads (
    -- 主键：用户ID + 线程ID
    user_id TEXT NOT NULL,
    thread_id TEXT NOT NULL,
    
    -- 元数据
    session_id TEXT,              -- 会话ID（可选）
    topic TEXT,                   -- 作文题目
    exam_type TEXT,               -- 考试类型 (ielts/cet-4...)
    task_type TEXT,               -- 任务类型
    last_band_score DOUBLE,       -- 上次分数
    preview TEXT,                 -- 预览文本
    
    -- 时间戳
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    PRIMARY KEY (user_id, thread_id)
);
```

**类比**：threads 表就像「聊天列表」，每个线程是一条聊天记录。

#### messages 表（消息表）

```sql
CREATE TABLE composition_history_messages (
    id BIGSERIAL PRIMARY KEY,     -- 自增ID
    
    -- 关联线程
    user_id TEXT NOT NULL,
    thread_id TEXT NOT NULL,
    
    -- 消息内容
    role TEXT NOT NULL,           -- "user" 或 "assistant"
    content TEXT NOT NULL,        -- 消息文本
    created_at TIMESTAMPTZ DEFAULT NOW(),
    
    -- 外键：删除线程时级联删除消息
    FOREIGN KEY (user_id, thread_id)
        REFERENCES composition_history_threads
        ON DELETE CASCADE
);
```

**类比**：messages 表就像「聊天详情」，每条消息是具体的对话。

### 2.4 核心操作

#### 操作 1：写入对话

```python
async def upsert_thread_and_append_messages(
    user_id: str,           # 用户ID
    thread_id: str,         # 线程ID
    user_content: str,      # 用户消息（作文文本）
    assistant_content: str, # AI回复（批改结果）
    preview: str,           # 预览文本
):
    """
    写入一轮对话：
    1. 创建或更新线程元数据
    2. 插入用户消息
    3. 插入AI消息
    """
```

**数据流：**

```
用户提交作文 "Environmental protection is important..."
              │
              ▼
┌─────────────────────────────────────────────────────┐
│  Step 1: UPSERT 线程                                │
│  INSERT INTO threads (thread_id, topic, ...)       │
│  ON CONFLICT DO UPDATE  -- 如果存在就更新           │
└─────────────────────────────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────────────────┐
│  Step 2: INSERT 用户消息                            │
│  role="user", content="Environmental..."            │
└─────────────────────────────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────────────────┐
│  Step 3: INSERT AI回复                              │
│  role="assistant", content="得分6.5分..."           │
└─────────────────────────────────────────────────────┘
```

#### 操作 2：查询历史列表

```python
async def list_threads(user_id: str) -> list[dict]:
    """获取用户所有线程，按时间倒序"""
```

**返回示例：**
```json
[
  {
    "thread_id": "abc-123",
    "topic": "环境保护",
    "last_band_score": 6.5,
    "preview": "本次得分: 6.5，主要问题是语法...",
    "updated_at": "2026-03-13T10:30:00Z"
  },
  {
    "thread_id": "def-456",
    "topic": "科技发展",
    "last_band_score": 7.0,
    "preview": "本次得分: 7.0，进步明显！",
    "updated_at": "2026-03-12T15:20:00Z"
  }
]
```

#### 操作 3：查询线程详情

```python
async def get_thread_detail(user_id: str, thread_id: str) -> dict:
    """获取线程的所有消息"""
```

**返回示例：**
```json
{
  "thread_id": "abc-123",
  "topic": "环境保护",
  "messages": [
    {
      "role": "user",
      "content": "Environmental protection is important...",
      "created_at": "2026-03-13T10:00:00Z"
    },
    {
      "role": "assistant",
      "content": "得分：6.5分\n问题：语法错误较多...",
      "created_at": "2026-03-13T10:00:05Z"
    },
    {
      "role": "user",
      "content": "我修改了，请再批改一次",
      "created_at": "2026-03-13T10:05:00Z"
    },
    {
      "role": "assistant",
      "content": "得分：7.0分\n进步：语法改进明显！",
      "created_at": "2026-03-13T10:05:05Z"
    }
  ]
}
```

---

## 三、LangGraph Checkpoint 详解

### 3.1 是什么？

**Checkpoint = 工作流状态快照**

类比：游戏存档。你可以在任何时候保存进度，下次从存档点继续。

### 3.2 为什么需要？

**问题场景：作文改稿**

```
第一次提交作文：
┌─────────────────────────────────────────────┐
│  State (工作流状态)                          │
│  - essay_text: "第一版作文..."              │
│  - band_score: 6.5                          │
│  - errors: ["语法错误1", "语法错误2"]        │
│  - suggestions: ["建议1", "建议2"]           │
└─────────────────────────────────────────────┘

用户修改后再次提交：
┌─────────────────────────────────────────────┐
│  问题：AI 需要知道上次的状态！              │
│  - 上次分数是多少？                         │
│  - 哪些错误被修正了？                       │
│  - 如何对比进步？                           │
└─────────────────────────────────────────────┘

有了 Checkpoint：
┌─────────────────────────────────────────────┐
│  1. 从存档恢复上次状态                       │
│  2. 对比新旧作文                            │
│  3. 计算分数变化                            │
│  4. 生成进步报告                            │
└─────────────────────────────────────────────┘
```

### 3.3 存什么？

**State（状态）= 工作流的所有数据**

```python
class EssayState(TypedDict):
    # ========== 用户输入 ==========
    essay_text: str              # 作文文本
    exam_type: str               # 考试类型
    task_type: str               # 任务类型
    topic: str                   # 题目
    user_id: str                 # 用户ID
    
    # ========== 中间结果 ==========
    topic_embedding: list[float] # 题目向量
    retrieved_samples: list      # 检索到的范文
    retrieved_rubrics: list      # 检索到的评分标准
    
    # ========== 最终结果 ==========
    scores: dict                 # 各维度分数
    band_score: float            # 总分
    score_explanation: str       # 分数解释
    errors: list                 # 错误列表
    suggestions: list            # 建议列表
    
    # ========== 控制信息 ==========
    thread_id: str               # 线程ID
    current_step: str            # 当前步骤
    is_complete: bool            # 是否完成
    iteration: int               # 迭代次数
```

### 3.4 Checkpoint 如何工作？

#### 工作流定义

```python
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.postgres import PostgresSaver

# 1. 创建工作流
builder = StateGraph(EssayState)
builder.add_node("analyze_topic", analyze_topic)
builder.add_node("score_essay", score_essay)
builder.add_node("detect_errors", detect_errors)
...

# 2. 创建 Checkpointer（存档器）
checkpointer = PostgresSaver.from_conn_string(DATABASE_URL)

# 3. 编译工作流，绑定 Checkpointer
workflow = builder.compile(checkpointer=checkpointer)
```

#### 执行时保存状态

```python
# 第一次执行
config = {"configurable": {"thread_id": "abc-123"}}
result = workflow.invoke(initial_state, config)

# 此时 Checkpoint 自动保存：
# - 当前 State 的完整快照
# - 执行到哪个节点
# - 下一步该做什么
```

#### 恢复状态

```python
# 用户提交改稿
config = {"configurable": {"thread_id": "abc-123"}}

# 获取上次的状态
previous_state = workflow.get_state(config)

# previous_state 包含：
# - 上次的作文
# - 上次的分数
# - 上次的错误列表
# - ...

# 基于上次状态继续执行
result = workflow.invoke(new_state, config)
```

### 3.5 Checkpoint 数据库表

LangGraph 自动创建这些表：

```sql
-- 存储检查点元数据
CREATE TABLE checkpoints (
    thread_id TEXT NOT NULL,
    checkpoint_ns TEXT NOT NULL,
    checkpoint_id TEXT NOT NULL,
    parent_checkpoint_id TEXT,
    type TEXT,
    checkpoint JSONB NOT NULL,
    metadata JSONB,
    PRIMARY KEY (thread_id, checkpoint_ns, checkpoint_id)
);

-- 存储状态数据
CREATE TABLE checkpoint_blobs (
    thread_id TEXT NOT NULL,
    checkpoint_ns TEXT NOT NULL,
    channel TEXT NOT NULL,
    version TEXT NOT NULL,
    type TEXT NOT NULL,
    blob BYTEA,
    PRIMARY KEY (thread_id, checkpoint_ns, channel, version)
);

-- 存储写入操作
CREATE TABLE checkpoint_writes (
    thread_id TEXT NOT NULL,
    checkpoint_ns TEXT NOT NULL,
    checkpoint_id TEXT NOT NULL,
    task_id TEXT NOT NULL,
    idx INTEGER NOT NULL,
    channel TEXT NOT NULL,
    type TEXT,
    blob BYTEA,
    PRIMARY KEY (thread_id, checkpoint_ns, checkpoint_id, task_id, idx)
);
```

**你不需要手动操作这些表，LangGraph 自动管理。**

### 3.6 代码实现

```python
# checkpoint.py

from langgraph.checkpoint.postgres import PostgresSaver
from src.config.config import Config

_checkpointer = None

def get_checkpointer():
    """获取 Checkpointer 实例（懒加载）"""
    global _checkpointer
    if _checkpointer is None:
        # 连接数据库
        _checkpointer = PostgresSaver.from_conn_string(Config.DATABASE_URL)
    return _checkpointer

def setup_checkpoint():
    """初始化 Checkpoint 表"""
    checkpointer = get_checkpointer()
    checkpointer.setup()  # 创建表结构

def close_checkpoint():
    """关闭连接"""
    global _checkpointer
    _checkpointer = None
```

---

## 四、两者的区别与联系

### 4.1 对比表格

| 特性 | History Store | Checkpoint |
|------|---------------|------------|
| **目的** | 用户查看历史记录 | AI 记住工作状态 |
| **存储内容** | 用户消息 + AI回复 | 完整的 State 对象 |
| **谁来创建** | 开发者手动实现 | LangGraph 自动管理 |
| **表结构** | threads + messages | checkpoints + blobs + writes |
| **查询方式** | REST API 暴露给前端 | 内部 API，工作流使用 |
| **典型场景** | 查看聊天历史 | 作文改稿、状态恢复 |
| **数据格式** | 文本消息 | JSON 对象、二进制 |

### 4.2 形象比喻

```
History Store = 聊天记录截图
┌────────────────────────────────┐
│ 用户: 帮我批改作文            │
│ AI: 好的，得分6.5分...        │
│ 用户: 我修改了再批改          │
│ AI: 进步了！得分7.0分...      │
└────────────────────────────────┘
→ 用户可以随时翻看

Checkpoint = 游戏存档
┌────────────────────────────────┐
│ 存档点: score_essay 节点      │
│ 状态:                         │
│   - 当前分数: 6.5             │
│   - 错误列表: [...]           │
│   - 下一步: detect_errors     │
└────────────────────────────────┘
→ AI 可以从存档点继续
```

### 4.3 何时各用哪个？

| 场景 | 使用 | 原因 |
|------|------|------|
| 显示历史记录列表 | History Store | 需要预览、排序 |
| 点击查看对话详情 | History Store | 需要消息列表 |
| 作文改稿对比 | Checkpoint | 需要上次分数、错误 |
| 工作流断点续传 | Checkpoint | 需要完整状态 |
| 用户删除数据 | 都需要 | 两者独立存储 |

---

## 五、实战：数据如何流转

### 5.1 第一次提交作文

```
用户提交作文
     │
     ▼
┌─────────────────────────────────────────────────────────────┐
│ route.py: grade_composition()                               │
│                                                             │
│ 1. 生成 thread_id = "abc-123"                               │
│ 2. 创建初始 State                                           │
│    state = {                                                │
│      essay_text: "Environmental...",                        │
│      thread_id: "abc-123",                                  │
│      ...                                                    │
│    }                                                        │
└─────────────────────────────────────────────────────────────┘
     │
     ▼
┌─────────────────────────────────────────────────────────────┐
│ workflow.invoke(state, config)                              │
│                                                             │
│ 执行流程:                                                    │
│   analyze_topic → retrieve_samples → score_essay → ...      │
│                                                             │
│ Checkpoint 自动保存:                                         │
│   ✓ 每个节点执行后的 State                                   │
│   ✓ 当前位置、下一步                                         │
└─────────────────────────────────────────────────────────────┘
     │
     ▼
┌─────────────────────────────────────────────────────────────┐
│ History Store 写入:                                         │
│                                                             │
│ threads 表:                                                 │
│   thread_id="abc-123", topic="环境", score=6.5             │
│                                                             │
│ messages 表:                                                │
│   [user] "Environmental..."                                 │
│   [assistant] "得分6.5，问题..."                            │
└─────────────────────────────────────────────────────────────┘
```

### 5.2 提交改稿

```
用户提交改稿 (thread_id="abc-123")
     │
     ▼
┌─────────────────────────────────────────────────────────────┐
│ route.py: revise_composition()                              │
│                                                             │
│ 1. 从 Checkpoint 获取上次状态                                │
│    previous_state = workflow.get_state(config)              │
│                                                             │
│    previous_state 包含:                                     │
│      - band_score: 6.5                                      │
│      - errors: ["语法错误1", ...]                           │
│      - suggestions: ["建议1", ...]                          │
│                                                             │
│ 2. 创建新 State，包含 previous_summary                      │
│    state = {                                                │
│      essay_text: "修改后的作文...",                          │
│      previous_summary: "上次得分6.5，错误...",               │
│      ...                                                    │
│    }                                                        │
└─────────────────────────────────────────────────────────────┘
     │
     ▼
┌─────────────────────────────────────────────────────────────┐
│ workflow.invoke(state, config)                              │
│                                                             │
│ Checkpoint 更新:                                            │
│   - 新的分数: 7.0                                           │
│   - 新的错误列表                                             │
│   - 迭代次数 +1                                              │
└─────────────────────────────────────────────────────────────┘
     │
     ▼
┌─────────────────────────────────────────────────────────────┐
│ History Store 追加:                                         │
│                                                             │
│ messages 表新增:                                            │
│   [user] "修改后的作文..."                                   │
│   [assistant] "得分7.0，进步了！"                            │
│                                                             │
│ threads 表更新:                                             │
│   last_band_score: 7.0                                      │
│   preview: "得分7.0，进步了！"                               │
└─────────────────────────────────────────────────────────────┘
```

### 5.3 完整数据流图

```
┌──────────────────────────────────────────────────────────────────┐
│                           用户请求                                │
│              POST /ai/composition/grade                          │
│              { essay_text: "...", exam_type: "ielts" }           │
└──────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌──────────────────────────────────────────────────────────────────┐
│                        route.py                                   │
│                                                                   │
│  ┌─────────────────┐    ┌─────────────────┐                      │
│  │ 生成 thread_id  │    │ 创建初始 State  │                      │
│  │  (UUID)         │    │                 │                      │
│  └─────────────────┘    └─────────────────┘                      │
└──────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌──────────────────────────────────────────────────────────────────┐
│                    workflow.invoke()                              │
│                                                                   │
│  ┌─────────────────────────────────────────────────────────┐     │
│  │              LangGraph 工作流                            │     │
│  │                                                          │     │
│  │  START → analyze_topic → retrieve_samples → score_essay │     │
│  │                        ↘ retrieve_rubrics ↗              │     │
│  │                                                          │     │
│  │  → detect_errors → generate_suggestions → END           │     │
│  └─────────────────────────────────────────────────────────┘     │
│                                                                   │
│  ┌─────────────────────────────────────────────────────────┐     │
│  │              Checkpoint (自动)                           │     │
│  │                                                          │     │
│  │  每个节点执行后自动保存 State 到 PostgreSQL              │     │
│  │  - checkpoints 表                                        │     │
│  │  - checkpoint_blobs 表                                   │     │
│  └─────────────────────────────────────────────────────────┘     │
└──────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌──────────────────────────────────────────────────────────────────┐
│                    history_store.py                               │
│                                                                   │
│  ┌─────────────────────────────────────────────────────────┐     │
│  │  upsert_thread_and_append_messages()                     │     │
│  │                                                          │     │
│  │  ┌───────────────┐  ┌───────────────┐  ┌───────────────┐│     │
│  │  │ UPSERT        │  │ INSERT        │  │ INSERT        ││     │
│  │  │ threads 表    │→ │ user 消息     │→ │ assistant消息 ││     │
│  │  │ (元数据)      │  │               │  │               ││     │
│  │  └───────────────┘  └───────────────┘  └───────────────┘│     │
│  └─────────────────────────────────────────────────────────┘     │
└──────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌──────────────────────────────────────────────────────────────────┐
│                      PostgreSQL                                   │
│                                                                   │
│  ┌─────────────────────────┐  ┌─────────────────────────┐        │
│  │ composition_history_    │  │ composition_history_    │        │
│  │ threads                 │  │ messages                │        │
│  │ (History Store)         │  │ (History Store)         │        │
│  └─────────────────────────┘  └─────────────────────────┘        │
│                                                                   │
│  ┌─────────────────────────┐  ┌─────────────────────────┐        │
│  │ checkpoints             │  │ checkpoint_blobs        │        │
│  │ (LangGraph Checkpoint)  │  │ (LangGraph Checkpoint)  │        │
│  └─────────────────────────┘  └─────────────────────────┘        │
└──────────────────────────────────────────────────────────────────┘
```

---

## 六、总结

### 核心概念

| 概念 | 一句话解释 |
|------|-----------|
| **History Store** | 存储用户可见的对话历史，像聊天记录 |
| **Checkpoint** | 存储工作流内部状态，像游戏存档 |
| **State** | 工作流的所有数据，包括输入、中间结果、输出 |
| **Thread** | 一次完整的对话会话，用 thread_id 标识 |

### 记忆口诀

```
History Store 存给用户看，
Checkpoint 存给 AI 用。
一个是聊天记录截图，
一个是游戏进度存档。
```

### 何时用什么？

```
需要显示历史记录？ → History Store
需要恢复工作状态？ → Checkpoint
两者都要？ → 两个都用！
```

### 文件位置速查

| 功能 | 文件位置 |
|------|----------|
| History Store (作文) | `src/routers/ai/composition/history_store.py` |
| History Store (口语) | `src/routers/ai/speak/history_store.py` |
| History Store (日常) | `src/routers/ai/normal/history_store.py` |
| Checkpoint | `src/routers/ai/composition/checkpoint.py` |
| State 定义 | `src/routers/ai/composition/essay_state.py` |
| 工作流 | `src/routers/ai/composition/workflow.py` |

---

## 七、最小 Demo（教学版，不要求你现在运行）

下面给你一个精简版 Demo，用来帮助你在脑子里建立模型：

- 只保留一个 `grade`（首次评分）
- 只保留一个 `revise`（改稿）
- 同时写入 `History Store` 和 `Checkpoint`

### 7.1 目录结构（示意）

```text
demo/
├── checkpoint.py        # 管理 LangGraph checkpointer
├── history_store.py     # 管理对话历史表
├── state.py             # 定义 State
├── workflow.py          # 定义工作流节点
└── app.py               # 两个接口：/grade, /revise
```

### 7.2 state.py（定义工作流状态）

```python
from typing import TypedDict, Optional


class DemoState(TypedDict):
    essay_text: str
    thread_id: str
    user_id: str
    band_score: float
    score_explanation: Optional[str]
    previous_summary: Optional[str]
    current_step: str
```

每个字段都代表“AI执行过程中的记忆”：

- `essay_text`: 当前作文内容
- `thread_id`: 同一轮会话的唯一标识
- `user_id`: 属于哪个用户
- `band_score`: 当前计算出的总分
- `score_explanation`: 评分说明
- `previous_summary`: 改稿时，上一次结果的摘要
- `current_step`: 执行到哪个节点

### 7.3 checkpoint.py（管理 LangGraph 存档）

```python
from langgraph.checkpoint.postgres import PostgresSaver

CHECKPOINTER = None


def get_checkpointer(database_url: str):
    global CHECKPOINTER
    if CHECKPOINTER is None:
        resource = PostgresSaver.from_conn_string(database_url)
        CHECKPOINTER = resource.__enter__() if hasattr(resource, "__enter__") else resource
    return CHECKPOINTER


def setup_checkpoint(database_url: str):
    cp = get_checkpointer(database_url)
    cp.setup()
```

这段代码做了两件事：

1. **懒加载**：第一次调用才真正连数据库，避免应用启动慢
2. **幂等初始化**：`setup()` 可以重复调用，不会重复建表报错

### 7.4 history_store.py（管理用户可见历史）

```python
from sqlalchemy import text


CREATE_THREADS_SQL = text("""
CREATE TABLE IF NOT EXISTS demo_threads (
  user_id TEXT NOT NULL,
  thread_id TEXT NOT NULL,
  preview TEXT,
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  PRIMARY KEY (user_id, thread_id)
);
""")


CREATE_MESSAGES_SQL = text("""
CREATE TABLE IF NOT EXISTS demo_messages (
  id BIGSERIAL PRIMARY KEY,
  user_id TEXT NOT NULL,
  thread_id TEXT NOT NULL,
  role TEXT NOT NULL,
  content TEXT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
""")
```

这里你只要抓住一个核心：

- `demo_threads`: 放“会话列表信息”（预览、更新时间）
- `demo_messages`: 放“每一条消息内容”（user/assistant）

### 7.5 workflow.py（用 LangGraph 执行评分）

```python
from langgraph.graph import StateGraph, START, END
from .state import DemoState


def score_node(state: DemoState) -> DemoState:
    text_len = len(state["essay_text"])
    score = 5.0 if text_len < 120 else 6.5 if text_len < 250 else 7.0
    return {
        **state,
        "band_score": score,
        "score_explanation": f"Demo规则评分，字数={text_len}",
        "current_step": "scored",
    }


def build_workflow(checkpointer):
    builder = StateGraph(DemoState)
    builder.add_node("score", score_node)
    builder.add_edge(START, "score")
    builder.add_edge("score", END)
    return builder.compile(checkpointer=checkpointer)
```

这个工作流非常简单：

`START -> score -> END`

但足够说明 checkpoint 的意义：

- 每次执行后，状态会和 `thread_id` 绑定保存
- 下一次可通过 `thread_id` 读回

### 7.6 app.py（两个接口：grade + revise）

```python
from uuid import uuid4
from fastapi import FastAPI


@app.post("/grade")
async def grade(payload: dict):
    thread_id = payload.get("thread_id") or str(uuid4())
    state = {
        "essay_text": payload["essay_text"],
        "thread_id": thread_id,
        "user_id": payload["user_id"],
        "band_score": 0.0,
        "score_explanation": None,
        "previous_summary": "N/A",
        "current_step": "init",
    }
    config = {"configurable": {"thread_id": thread_id}}
    result = workflow.invoke(state, config)

    # 写 History Store（用户可见）
    save_round(
        user_id=payload["user_id"],
        thread_id=thread_id,
        user_content=payload["essay_text"],
        assistant_content=f"得分 {result['band_score']}",
        preview=f"得分 {result['band_score']}",
    )
    return {"thread_id": thread_id, "result": result}


@app.post("/revise")
async def revise(payload: dict):
    thread_id = payload["thread_id"]
    config = {"configurable": {"thread_id": thread_id}}

    # 从 Checkpoint 读回上一轮状态
    prev = workflow.get_state(config)
    prev_score = float(prev.values.get("band_score", 0.0))
    prev_summary = f"上次得分={prev_score}"

    new_state = {
        "essay_text": payload["revised_essay"],
        "thread_id": thread_id,
        "user_id": payload["user_id"],
        "band_score": 0.0,
        "score_explanation": None,
        "previous_summary": prev_summary,
        "current_step": "init",
    }
    result = workflow.invoke(new_state, config)
    delta = float(result["band_score"]) - prev_score

    # 再写一轮 History Store
    save_round(
        user_id=payload["user_id"],
        thread_id=thread_id,
        user_content=payload["revised_essay"],
        assistant_content=f"新得分 {result['band_score']}，提升 {delta}",
        preview=f"新得分 {result['band_score']}，提升 {delta}",
    )
    return {"thread_id": thread_id, "delta": delta, "result": result}
```

你会看到非常关键的一点：

- `/grade`：创建线程 + 执行工作流 + 记历史
- `/revise`：**先从 checkpoint 读上一次状态**，再执行新评分，再记历史

---

## 八、逐行讲解（基于你项目真实代码）

下面不是“泛泛解释”，而是对你仓库里关键函数按执行顺序解释。

### 8.1 `checkpoint.py` 逐行讲解

文件：`src/routers/ai/composition/checkpoint.py`

```python
from langgraph.checkpoint.postgres import PostgresSaver
from src.config.config import Config
```

- 导入 LangGraph 官方的 Postgres 持久化器
- 读取项目配置里的 `DATABASE_URL`

```python
_checkpointer_resource = None
_checkpointer = None
```

- 两个全局变量用于缓存资源
- 避免每次请求都新建连接

```python
def get_checkpointer():
```

- 统一入口：谁需要 checkpoint 就调它

```python
    if _checkpointer is not None:
        return _checkpointer
```

- 如果已经创建过，直接复用

```python
    resource = PostgresSaver.from_conn_string(Config.DATABASE_URL)
```

- 根据数据库连接串构建底层资源

```python
    if hasattr(resource, "__enter__"):
        _checkpointer = resource.__enter__()
    else:
        _checkpointer = resource
```

- 兼容两种返回形式：
  - 有些版本返回上下文管理器
  - 有些版本直接返回实例

```python
def setup_checkpoint() -> None:
    checkpointer = get_checkpointer()
    checkpointer.setup()
```

- 初始化表结构（幂等）
- 一般在应用启动时调用一次

```python
def close_checkpoint() -> None:
```

- 应用关闭时释放资源，防止连接泄漏

### 8.2 `history_store.py` 逐行讲解（以 composition 为例）

文件：`src/routers/ai/composition/history_store.py`

```python
async def ensure_history_tables() -> None:
```

- 启动时建表/建索引
- `IF NOT EXISTS` 保证重复执行安全

```python
CREATE TABLE IF NOT EXISTS composition_history_threads (...)
```

- 线程主表，主键 `(user_id, thread_id)`
- 存元数据：题目、考试类型、预览、分数

```python
CREATE TABLE IF NOT EXISTS composition_history_messages (...)
```

- 消息子表，一条消息一行
- 通过 `(user_id, thread_id)` 外键关联线程

```python
ON DELETE CASCADE
```

- 删除线程时，自动删除该线程下所有消息

```python
CREATE INDEX ... (user_id, updated_at DESC)
CREATE INDEX ... (user_id, thread_id, created_at ASC)
```

- 第一个索引优化“历史列表”
- 第二个索引优化“会话详情按时间顺序查询”

```python
async def upsert_thread_and_append_messages(...):
```

- 每一轮对话都调用它
- 1次函数完成3件事：更新线程、写用户消息、写AI消息

```python
INSERT ... ON CONFLICT (user_id, thread_id) DO UPDATE
```

- 首轮对话：插入新线程
- 后续对话：更新同一线程（更新时间、预览、分数）

```python
session_id = COALESCE(EXCLUDED.session_id, composition_history_threads.session_id)
```

- 新值如果是 `NULL`，就保留旧值
- 防止把已有字段误覆盖为空

```python
await session.execute(insert_message_sql, {"role": "user", ...})
await session.execute(insert_message_sql, {"role": "assistant", ...})
await session.commit()
```

- 固定写两条消息：用户一条、助手一条
- 最后统一 commit，保证一致性

```python
async def list_threads(user_id: str) -> list[dict[str, Any]]:
```

- 给“历史列表页”使用
- 只查线程元数据，不查具体消息

```python
async def get_thread_detail(user_id: str, thread_id: str) -> dict[str, Any] | None:
```

- 给“会话详情页”使用
- 先查 thread，再查 messages，最后拼成一个对象返回

### 8.3 `route.py` 的 `grade/revise` 为什么这样设计

文件：`src/routers/ai/route.py`

#### `grade_composition()`

```python
thread_id = payload.thread_id or str(uuid4())
```

- 如果前端没传线程ID，后端自动创建

```python
initial_state = create_initial_state(..., thread_id=thread_id, ...)
config = {"configurable": {"thread_id": thread_id}}
```

- `initial_state` 是工作流输入
- `config.thread_id` 是 checkpoint 关联键（非常关键）

```python
result = await run_in_threadpool(workflow.invoke, initial_state, config)
```

- 因为 `workflow.invoke` 是同步调用，这里丢进线程池避免阻塞事件循环

```python
await upsert_thread_and_append_messages(...)
```

- 工作流产出后，写入 History Store
- 这样前端就能立刻看到这轮对话

#### `revise_composition()`

```python
previous_raw_state = await run_in_threadpool(workflow.get_state, config)
previous_state = _extract_state_values(previous_raw_state)
```

- 从 checkpoint 读取上一轮状态
- 提取出 `values` 作为可用字典

```python
previous_band_score = float(previous_state.get("band_score", 0.0))
previous_summary = _build_previous_summary(previous_state)
```

- 读取上次总分
- 生成“上次结果摘要”喂给模型，帮助做对比评估

```python
result = await run_in_threadpool(workflow.invoke, initial_state, config)
delta = round(new_band_score - previous_band_score, 2)
```

- 执行新一轮评分
- 计算分数变化 `delta`

```python
await upsert_thread_and_append_messages(...)
```

- 再写一轮历史
- 所以同一个 thread 里会越来越长

---

## 九、常见误区（新手高频）

### 误区 1：History Store 和 Checkpoint 是一回事

不是。

- History Store 面向前端展示
- Checkpoint 面向工作流恢复

### 误区 2：有了 History Store 就不需要 Checkpoint

不对。History Store 通常只存“文本结果”，没有完整中间状态。

### 误区 3：Checkpoint 可以直接给前端展示

不建议。Checkpoint 结构偏底层，字段复杂，也不稳定。

### 误区 4：thread_id 只用于前端

不对。它同时是：

- 历史会话的主键
- checkpoint 恢复状态的关键索引

---

## 十、你可以先掌握的最小心智模型

把它记住就够了：

1. 请求进来后，工作流执行并自动 checkpoint
2. 工作流结果再写 history_store
3. 改稿时先用 `thread_id` 从 checkpoint 恢复，再继续跑

一句话版：

`Checkpoint 负责“让 AI 记得过程”，History Store 负责“让用户看到记录”。`
