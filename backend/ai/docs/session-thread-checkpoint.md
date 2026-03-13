# 会话模型设计指南：session_id、thread_id、checkpoint（重构版）

> 适用场景：一个用户可与多个 Agent（作文/口语/单词）对话，且每个 Agent 下可发起多次会话和多轮改稿。

---

## 1. 先给结论（TL;DR）

- `session_id`：业务会话 ID（一次学习活动）
- `thread_id`：执行线程 ID（同一篇内容的连续链）
- `checkpoint`：LangGraph 的状态快照存档机制（按 `thread_id` 续跑）

一句话关系：

> `thread_id` 决定 checkpoint 读写哪条链；`session_id` 决定这条链属于哪次业务会话。

---

## 2. 三个概念的职责边界

## 2.1 session_id（业务会话）

- 粒度：会话级（较大）
- 作用：聚合同一学习场景下的多条线程
- 典型用法：
  - 学习记录页按 `session_id` 展示
  - 做“本次学习总结”
  - 前端页面生命周期内复用

---

## 2.2 thread_id（执行线程）

- 粒度：单条连续对话/改稿链（较小）
- 作用：标识同一篇作文（或同一口语题）的多轮迭代
- 典型用法：
  - 首改、二改、三改共用同一个 `thread_id`
  - 通过同一个 `thread_id` 从 checkpoint 续跑

---

## 2.3 checkpoint（状态快照）

- 本质：LangGraph 在每个节点后保存 state 快照
- 存储：通常放 PostgreSQL（`langgraph-checkpoint-postgres`）
- 价值：
  - 断点恢复
  - 历史追踪
  - 多轮对话连续性

---

## 3. 关系模型（多用户 × 多 Agent × 多会话）

推荐四层隔离键：

1. `user_id`（权限边界）
2. `agent_type`（能力边界：composition/speaking/vocab）
3. `session_id`（业务会话边界）
4. `thread_id`（执行线程边界）

关系图：

```text
user_id
  ├─ agent_type=composition
  │    ├─ session_id=S1
  │    │    ├─ thread_id=T1
  │    │    └─ thread_id=T2
  │    └─ session_id=S2
  │         └─ thread_id=T3
  └─ agent_type=speaking
       └─ session_id=S3
            └─ thread_id=T4
```

---

## 4. 路由调用与状态续跑（关键）

## 4.1 首次调用（grade）

```python
config = {"configurable": {"thread_id": payload.thread_id}}
result = workflow.invoke(initial_state, config=config)
```

## 4.2 二次改稿（revise）

- 必须复用同一个 `thread_id`
- 替换 `essay_text = revised_essay`
- 再次 invoke 同一 workflow

若更换 `thread_id`，系统会当成新链路，无法继承上次状态。

---

## 5. 安全隔离与权限校验（服务端必须做）

每次请求都需要校验 thread 归属，不能只信前端参数：

- `thread.user_id == current_user_id`
- `thread.agent_type == current_agent_type`
- （可选）`thread.session_id == payload.session_id`

失败直接返回 403/404。

> 原则：checkpoint 解决“续跑”，业务表解决“归属与权限”。

---

## 6. 推荐数据表（业务层）

> checkpoint 表由 LangGraph 插件管理；以下是你自己的业务表。

## 6.1 ai_sessions（会话）

- `id` (uuid)
- `user_id`
- `agent_type`
- `title`
- `status` (active/closed)
- `started_at` / `ended_at`
- `metadata` (jsonb)

## 6.2 ai_threads（线程）

- `id` (uuid)
- `thread_id` (unique)
- `session_id` (fk)
- `user_id`
- `agent_type`
- `topic`
- `turn_count`
- `status`
- `created_at` / `updated_at`
- `metadata` (jsonb)

## 6.3 ai_runs（每次执行）

- `id` (uuid)
- `thread_id` (fk)
- `session_id` (fk)
- `user_id`
- `agent_type`
- `run_type` (grade/revise)
- `iteration`
- `request_payload` / `response_payload` (jsonb)
- `band_score`
- `needs_revision`
- `created_at`

## 6.4 composition_artifacts（作文结构化产物，可选）

- `run_id` (fk)
- `scores` (jsonb)
- `errors` (jsonb)
- `suggestions` (jsonb)
- `highlight_improvements` (jsonb)
- `score_explanation`

---

## 7. 前端 ID 生成与复用规则

## session_id

- 复用：同一学习会话
- 新建：新学习会话/新任务周期

## thread_id

- 复用：同一篇内容的多轮迭代
- 新建：新题目或新作文

建议：

- `session_id` 存 localStorage（会话周期）
- `thread_id` 在“新建作文”时生成

---

## 8. 常见错误清单

1. 只用 `thread_id` 不做 `user_id` 校验（越权风险）
2. 二改时重建 `thread_id`（无法续跑）
3. 混用 `session_id` 与 `thread_id`（统计混乱）
4. 把 checkpoint 当业务审计表（职责错位）

---

## 9. 实施顺序（推荐）

1. 接入 checkpoint（按 `thread_id`）
2. 路由强制归属校验（user/agent/session）
3. 实现 revise 接口（同 thread_id 续跑）
4. 再做业务结果落库与分析看板

---

## 10. 最小请求示例

```json
{
  "essay_text": "...",
  "exam_type": "ielts",
  "task_type": "opinion_essay",
  "topic": "...",
  "user_id": "user_001",
  "session_id": "sess_xxx",
  "thread_id": "thr_xxx"
}
```
