# 面向 LangGraph 使用者的存储实战指南

> 目标读者：你已经会 LangGraph（节点、状态、工作流），但不熟数据库与持久化。

---

## 0. 先说结论（你最该先知道的）

在这个项目里，AI 对话相关的“存储”有两条线：

1. **History Store（业务历史）**
   - 用途：给前端展示“历史会话列表”和“会话详情”。
   - 你能看到：用户消息、助手消息、预览、更新时间。
2. **LangGraph Checkpoint（工作流存档）**
   - 用途：让 LangGraph 能恢复上一轮状态（比如改稿对比）。
   - 你能得到：上一轮完整 `State`，不只是文本消息。

一句话：

**History Store 是给“人”看的记录，Checkpoint 是给“图”恢复执行状态的记录。**

---

## 1. 存储基础（只讲你这项目会遇到的）

如果你从没系统学过数据库，先掌握这 10 个词：

1. **数据库（Database）**：一个数据仓库（这里是 PostgreSQL）。
2. **表（Table）**：像 Excel 表，一个主题一张表。
3. **行（Row）**：一条记录。
4. **列（Column）**：字段，如 `user_id`、`thread_id`。
5. **主键（Primary Key）**：唯一标识一条记录，不能重复。
6. **外键（Foreign Key）**：表与表的关联约束。
7. **索引（Index）**：加速查询的数据结构。
8. **事务（Transaction）**：一组操作要么都成功，要么都失败。
9. **UPSERT**：不存在就插入，存在就更新。
10. **幂等（Idempotent）**：多次执行结果一致（如建表 `IF NOT EXISTS`）。

你只要有这 10 个概念，就能看懂本项目的存储代码。

---

## 2. 这个项目到底把数据存到了哪里

### 2.1 启动时做了哪些“存储初始化”

文件：`src/main.py`

应用启动生命周期里做了四件事：

1. `setup_checkpoint()`：初始化 LangGraph checkpoint 相关表。
2. `ensure_history_tables()`：初始化作文历史表。
3. `ensure_normal_history_tables()`：初始化日常聊天历史表。
4. `ensure_speak_history_tables()`：初始化口语历史表。

这意味着：

- 你第一次启动服务时，会自动建好所需表结构。
- 不需要你手动执行 SQL。

### 2.2 数据库连接是如何配置的

文件：`src/config/config.py`、`src/db/main.py`

关键点：

- `.env` 里是 `DATABASE_URL`
- 代码里自动转换成异步驱动 URL：
  - `postgresql://...` -> `postgresql+asyncpg://...`
- 所有异步数据库操作都通过 `AsyncSessionLocal` 完成。

这套是标准 async SQLAlchemy/SQLModel 写法。

---

## 3. History Store：从 0 到 1 看懂

下面以作文模块为例（另外两个模块结构几乎一样）。

文件：`src/routers/ai/composition/history_store.py`

---

### 3.1 为什么是两张表，而不是一张表

该模块用两张表：

1. `composition_history_threads`：会话级元信息
2. `composition_history_messages`：具体消息内容

这是非常常见的“主表 + 明细表”模型。

原因：

- 历史列表页只需要 thread 元信息，查询轻。
- 点开详情才查 messages，不拖慢列表。
- 一个 thread 里有很多消息，天然一对多。

---

### 3.2 `composition_history_threads` 表字段含义

核心字段：

- `user_id`：用户 ID。
- `thread_id`：会话线程 ID。
- `session_id`：可选会话 ID。
- `topic`：作文题目。
- `exam_type`、`task_type`：作文类型元数据。
- `last_band_score`：该线程最近一次评分。
- `preview`：历史列表的预览文本。
- `updated_at`：最后更新时间。
- `PRIMARY KEY (user_id, thread_id)`：同一用户下线程唯一。

为什么主键是复合键而不是只用 `thread_id`？

- 这样可天然隔离用户，避免线程碰撞导致串数据。

---

### 3.3 `composition_history_messages` 表字段含义

核心字段：

- `id BIGSERIAL`：消息自增主键。
- `user_id` + `thread_id`：归属哪个会话。
- `role`：`user` 或 `assistant`。
- `content`：文本内容。
- `created_at`：消息时间。
- 外键约束到 `threads`，并 `ON DELETE CASCADE`。

`ON DELETE CASCADE` 的价值：

- 删除线程时，消息自动删干净，不会残留垃圾数据。

---

### 3.4 为什么要建索引

这个文件里建了两个索引：

1. `(user_id, updated_at DESC)`：
   - 用在“历史列表”查询，按最近更新时间排序。
2. `(user_id, thread_id, created_at ASC)`：
   - 用在“会话详情”查询，按时间顺序取消息。

没有索引也能查，但数据量上去后会明显慢。

---

### 3.5 `upsert_thread_and_append_messages` 为什么是关键函数

这是“写历史”的核心函数。每一轮对话都调用它。

它做 3 步：

1. `UPSERT` 线程元数据。
2. 插入一条 user 消息。
3. 插入一条 assistant 消息。

最后 `commit` 一次提交事务。

你可以把它理解为：

**“把这一轮对话（问+答）完整落库”**。

---

### 3.6 为什么要 UPSERT 而不是 INSERT

同一个 `thread_id` 会多轮追加（尤其改稿）。

- 首次：线程不存在 -> 插入。
- 后续：线程已存在 -> 更新 `preview/score/updated_at`。

这样前端历史列表永远展示线程最新状态。

SQL 里的 `COALESCE(EXCLUDED.xxx, old.xxx)` 是为了：

- 如果新值为空，保留旧值，避免把已有信息覆盖成空。

---

### 3.7 查询函数怎么对应前端页面

1. `list_threads(user_id)`
   - 返回会话列表（不含全文消息）。
2. `get_thread_detail(user_id, thread_id)`
   - 返回该会话全部消息。

对应路由（`src/routers/ai/route.py`）：

- `/composition/history`
- `/composition/history/{thread_id}`

同理还有 `speak` / `normal` 的历史接口。

---

## 4. Checkpoint：你会 LangGraph，这里讲“存储视角”

文件：`src/routers/ai/composition/checkpoint.py`

---

### 4.1 Checkpoint 在数据库里存什么

它存的是“图执行状态”，不是聊天文本。

状态来源是 `EssayState`（`src/routers/ai/composition/essay_state.py`）。

你在 State 里定义的字段，checkpoint 都可能存下来，比如：

- `scores`, `band_score`, `errors`, `suggestions`
- `current_step`, `needs_revision`
- `retrieved_rubrics`, `retrieved_samples`

这就是为什么改稿时可以拿到上一次完整结果，而不只是一段字符串。

---

### 4.2 为什么要 `thread_id` 放到 `configurable`

在 `route.py` 里：

```python
config = {"configurable": {"thread_id": thread_id}}
```

这行非常关键：

- 对 checkpoint 来说，它是“状态分区键”。
- 没有它，就无法正确区分/恢复某个线程状态。

你可以把它当作：

**LangGraph 侧的“会话主键”。**

---

### 4.3 `workflow.invoke` 和 `workflow.get_state` 的分工

在这个项目里：

- `workflow.invoke(...)`：执行工作流并推进状态（会触发 checkpoint 写入）。
- `workflow.get_state(config)`：按线程读取最近状态（用于改稿前取上轮结果）。

改稿接口里就是先 `get_state`，再 `invoke`。

---

### 4.4 为什么还要 `setup_checkpoint` 和 `close_checkpoint`

`setup_checkpoint()`

- 初始化 checkpoint 表。
- 启动时执行一次，确保环境就绪。

`close_checkpoint()`

- 关闭资源，避免连接泄漏。
- 在服务关闭生命周期执行。

---

## 5. 首次评分 vs 改稿：把两条链路串起来

### 5.1 首次评分（`/composition/grade`）

流程：

1. 生成/接收 `thread_id`。
2. `create_initial_state(...)` 构造 State。
3. `workflow.invoke(state, config)` 执行图。
4. 取结果生成 `assistant_preview`。
5. `upsert_thread_and_append_messages(...)` 写入 History。
6. 返回 response。

这里已经发生了两次存储：

- Checkpoint（自动）
- History（手动）

### 5.2 改稿（`/composition/revise`）

流程：

1. `workflow.get_state(config)` 读取上次状态。
2. 从上次状态提取 `previous_band_score`、生成 `previous_summary`。
3. 用改稿文本构造新的 `initial_state`。
4. `workflow.invoke(new_state, config)` 得到新结果。
5. 计算 `delta = new - old`。
6. 再写一轮 History（问+答）。

这就是“可对比改稿”的根本原因：

- **不是靠 history 文本解析**
- **而是直接读取 checkpoint 状态**

---

## 6. 一个教学 Demo（不要求你运行）

你说“不用运行”，这里给“读得懂就行”的最小伪代码。

```python
# 1) 首次评分
thread_id = "t-001"
config = {"configurable": {"thread_id": thread_id}}

state = {
    "essay_text": "first draft...",
    "thread_id": thread_id,
    "user_id": "u-001",
    "previous_summary": "N/A",
    "band_score": 0.0,
    "current_step": "init",
}

result = workflow.invoke(state, config)   # Checkpoint 自动更新

save_history(
    user_id="u-001",
    thread_id=thread_id,
    user_content="first draft...",
    assistant_content=f"score={result['band_score']}",
    preview=f"score={result['band_score']}"
)


# 2) 改稿
prev = workflow.get_state(config)          # 从 Checkpoint 读上次状态
old_score = float(prev.values.get("band_score", 0.0))

new_state = {
    "essay_text": "revised draft...",
    "thread_id": thread_id,
    "user_id": "u-001",
    "previous_summary": f"old_score={old_score}",
    "band_score": 0.0,
    "current_step": "init",
}

new_result = workflow.invoke(new_state, config)
delta = float(new_result["band_score"]) - old_score

save_history(
    user_id="u-001",
    thread_id=thread_id,
    user_content="revised draft...",
    assistant_content=f"score={new_result['band_score']} delta={delta}",
    preview=f"score={new_result['band_score']} delta={delta}"
)
```

看这个 Demo 你只需抓住：

- `invoke`：推进图 + 存档状态
- `get_state`：拿上轮状态
- `save_history`：追加用户可见历史

---

## 7. 为什么项目里有 3 套 history_store

你可能会问：为什么不共用一个？

当前做法是每个业务模块独立：

- composition：多了 `exam_type/task_type/last_band_score`
- speak：多了 `topic`
- normal：多了 `mode`

优点：

- 业务边界清晰，改字段互不影响。

代价：

- 代码有重复（后续可抽象）。

对新手来说，先接受这个设计更容易理解。

---

## 8. 新手最容易踩的坑

1. **以为 History 就能做改稿对比**
   - 不能稳定做。因为缺很多结构化中间状态。
2. **忘记传 `thread_id` 到 configurable**
   - 会导致状态恢复错乱或恢复不到。
3. **只写 messages，不更新 threads**
   - 历史列表会没有最新预览/时间。
4. **不建索引就上线**
   - 数据量一大，列表/详情查询会明显变慢。
5. **把数据库异常当作模型异常**
   - 排查时要区分：网络/连接层 vs 业务解析层。

---

## 9. 你现在可以怎么练（建议顺序）

1. 先只读：`composition/history_store.py`
   - 把建表 SQL 和 4 个函数看懂。
2. 再看：`composition/checkpoint.py` + `composition/workflow.py`
   - 明白 checkpoint 是如何挂到 graph 上。
3. 最后看：`route.py` 的 `grade_composition` / `revise_composition`
   - 贯通“请求 -> 执行 -> 双写存储”。

你完成这三步，就已经具备“能自己做存储改造”的能力。

---

## 10. 终极记忆卡片

```text
前端历史展示：读 History Store
改稿恢复状态：读 Checkpoint

每次 invoke：Checkpoint 自动更新
每轮对话落库：History 手动写入

thread_id = 两个世界的共同锚点
```
