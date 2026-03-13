# 作文批改 + 语音对话流程说明（函数级详细版）

本文基于当前代码实现，逐文件、逐函数说明两条主流程：

1. 作文批改（Composition）
2. 语音对话（Speak，ASR -> WS -> LLM -> TTS）

---

## 0. 入口与启动流程

## 0.1 `src/main.py`

### `lifespan(app: FastAPI)`

作用：应用启动/关闭时的资源初始化与释放。

执行顺序：

1. `setup_checkpoint()`
   - 初始化 LangGraph 的 Postgres checkpoint 表。
2. `await ensure_history_tables()`
   - 初始化作文历史表（`composition_history_threads/messages`）。
3. `await ensure_speak_history_tables()`
   - 初始化口语历史表（`speak_history_threads/messages`）。
4. 服务运行。
5. 关闭阶段执行 `close_checkpoint()`。

---

## 0.2 `src/routers/ai/route.py`

`ai_router` 提供所有 `/ai/*` 路由：

- WebSocket：
  - `/ai/ws`（兼容入口，转 speak handler）
  - `/ai/speak/ws`（语义化入口）
- Composition HTTP：
  - `/ai/composition/grade`
  - `/ai/composition/revise`
  - `/ai/composition/history`
  - `/ai/composition/history/{thread_id}`
- Speak HTTP：
  - `/ai/speak/history`
  - `/ai/speak/history/{thread_id}`

---

## 1. 作文批改（Composition）

## 1.1 状态定义：`src/routers/ai/composition/essay_state.py`

### `take_latest_step(current, new_value)`

作用：并发分支写 `current_step` 时的 reducer。

- `retrieve_samples` 与 `retrieve_rubric` 并行执行，会同时写 `current_step`
- LangGraph 默认不允许并发写同键
- 该函数实现“取最新非空值”，避免 `INVALID_CONCURRENT_GRAPH_UPDATE`

### `class EssayState(TypedDict)`

作用：定义图状态，包含：

- 输入字段：`essay_text, exam_type, task_type, topic, user_id`
- 检索字段：`topic_embedding, essay_embedding, retrieved_samples, retrieved_rubrics`
- 评分字段：`scores, band_score, score_explanation`
- 错误与建议：`errors, suggestions, highlight_improvements`
- 对话/迭代：`messages, iteration, max_iterations, revised_essay, previous_summary`
- 会话/控制：`thread_id, session_id, current_step, is_complete, needs_revision`

### `create_initial_state(...)`

作用：创建图初始状态。

关键点：

- 初始化所有列表/字典，避免节点取值空指针
- `current_step` 初始为 `initializing`
- 首次评分时 `previous_summary="N/A"`
- 改稿评分时传入 `revised_essay` 与 `previous_summary`

---

## 1.2 图编排：`src/routers/ai/composition/workflow.py`

### `build_workflow()`

作用：构建 LangGraph 状态图并挂载 checkpoint。

图结构：

1. `START -> analyze_topic`
2. `analyze_topic -> retrieve_samples`（并行分支 A）
3. `analyze_topic -> retrieve_rubric`（并行分支 B）
4. `retrieve_samples -> score_essay`
5. `retrieve_rubric -> score_essay`
6. `score_essay -> detect_errors`
7. `detect_errors -> generate_suggestions`
8. `generate_suggestions -> END`

并在 `builder.compile(checkpointer=get_checkpointer())` 时启用持久化。

### `get_workflow()`

作用：懒加载单例 workflow，避免导入阶段触发数据库连接。

### `draw_mermaid()`

作用：导出 Mermaid 文本，便于画流程图/调试。

---

## 1.3 Checkpoint：`src/routers/ai/composition/checkpoint.py`

### `get_checkpointer()`

作用：懒加载 `PostgresSaver`，兼容上下文管理器实现。

### `setup_checkpoint()`

作用：初始化 checkpoint 表（幂等）。

### `close_checkpoint()`

作用：关闭 checkpointer 资源。

---

## 1.4 节点函数（Nodes）

## `nodes/analyze_topic.py`

### `analyze_topic(state)`

职责：

1. 保证 `topic` 存在（缺失则用作文前 200 字兜底）
2. 生成 `topic_embedding`
3. 生成 `essay_embedding`
4. 返回 `current_step="topic_analyzed"`

---

## `nodes/retrieve_samples.py`

### `retrieve_samples(state)`

职责：

1. 使用 `topic_embedding` 在 Milvus 检索范文
2. 用 `exam_type + task_type` 过滤
3. 返回 top-k（当前 limit=5）范文
4. 映射输出字段：`topic, essay_text, band_score, tags, distance`
5. 返回 `current_step="samples_retrieved"`

---

## `nodes/retrieve_rubric.py`

### `retrieve_rubric(state)`

职责：

1. 用 `exam_type + task_type` 精确过滤 rubric
2. 调 Milvus `query`（非向量检索）
3. 输出 `dimension, band_score, description`
4. 返回 `current_step="rubrics_retrieved"`

---

## `nodes/score_essay.py`

### `score_essay(state)`

职责：

1. 取输入：作文、题目、检索结果、`previous_summary`
2. 调 `chain.invoke(...)`（DeepSeek structured output）
3. 解析 `EssayScoreResult` 为 state 字段：
   - `scores`
   - `band_score`
   - `score_explanation`（拼接优点/不足）
4. 返回 `current_step="scored"`

---

## `nodes/detect_errors.py`

### `detect_errors(state)`

职责：

1. 调错误检测链
2. 生成结构化 `errors`（type/original/suggestion/reason/severity）
3. 生成前端高亮字段 `highlight_improvements`
4. 返回 `current_step="errors_detected"`

---

## `nodes/generate_suggestions.py`

### `_format_scores(scores)`

作用：把维度分数字典格式化成 prompt 文本。

### `_format_errors(errors, max_items=12)`

作用：把错误列表格式化成 prompt 文本，限制条数避免 prompt 过长。

### `_compute_needs_revision(band_score, errors)`

作用：按分数+错误严重度计算是否建议继续改稿。

当前规则：

- `band>=7.0` 且 `high=0` 且 `medium<=1` -> `False`
- `band>=6.5` 且 `high=0` 且 `errors<=2` -> `False`
- 否则 `True`

### `generate_suggestions(state)`

职责：

1. 调建议链
2. 合并 `suggestions + revision_plan + focus_areas`
3. 设置 `needs_revision`
4. 返回 `current_step="suggestions_generated"`

---

## 1.5 链函数（Chains）

## `chains/score_grader.py`

### `class DimensionScore`

单维度评分结构：`dimension, score, comment`。

### `class EssayScoreResult`

整体评分结构：`scores, band_score, overall_comment, strengths, weaknesses`。

### `_format_rubrics(rubrics)`

将 rubric 列表转成 LLM 可读文本。

### `_format_samples(samples, top_k=2)`

将检索范文压缩成 prompt 文本。

### `score_llm`

DeepSeek 聊天模型 + `with_structured_output(EssayScoreResult)`。

### `prompt`

评分提示词模板，支持 `previous_summary`（改稿场景）。

### `chain`

`prompt | score_llm` 可执行链。

---

## `chains/error_detector.py`

### `class ErrorItem`

错误条目结构：
`type, original, suggestion, reason, severity`。

### `class ErrorDetectionResult`

整体结构：`errors, summary`。

### `structured_llm / prompt / chain`

错误检测链，输入作文+上下文，输出结构化错误集合。

---

## `chains/suggestion_provider.py`

### `class SuggestionResult`

输出结构：
`suggestions, revision_plan, focus_areas`。

### `llm / prompt / chain`

建议链，输入分数解释+错误文本，输出可执行建议。

---

## 1.6 作文历史存储：`composition/history_store.py`

### `ensure_history_tables()`

初始化两张表与索引：

- `composition_history_threads`
- `composition_history_messages`

### `upsert_thread_and_append_messages(...)`

一轮写入：

1. upsert 线程元信息（topic/exam/task/last score/preview）
2. 插入 user 消息
3. 插入 assistant 消息

### `list_threads(user_id)`

按更新时间倒序返回某用户线程列表。

### `get_thread_detail(user_id, thread_id)`

返回线程元信息 + 全量消息明细。

---

## 1.7 Composition 路由函数（`ai/route.py`）

### `_extract_state_values(raw_state)`

兼容 `workflow.get_state()` 多种返回格式（dict / snapshot）。

### `_build_previous_summary(previous_state)`

将上轮分数、错误、建议压缩成改稿评分 prompt 摘要。

### `_build_assistant_preview(result)`

将本轮评分结果压缩成历史列表预览文本。

### `grade_composition(payload)`

流程：

1. 生成/复用 `thread_id`
2. 构建初始 state（`previous_summary="N/A"`）
3. `workflow.invoke(..., config={thread_id})`
4. 写入历史表
5. 返回评分结果

### `revise_composition(payload)`

流程：

1. 通过 `thread_id` 读取 checkpoint state
2. 生成 `previous_summary`
3. 用 `revised_essay` 构建 state 再执行 workflow
4. 计算 `delta/improved`
5. 写入历史表
6. 返回改稿结果

### `list_composition_history(user_id)`

返回作文线程列表。

### `get_composition_history_detail(thread_id, user_id)`

返回作文线程消息明细。

---

## 2. 语音对话（Speak）

## 2.1 人设与提示词：`speak/prompt.py`

### `SAKIKO_SYSTEM_PROMPT`

作用：定义口语助手系统提示词。

当前包含：

- 角色身份（丰川祥子）
- 性格与语气
- 关系语义
- 口语教练任务
- 输出结构
- 纠错策略
- 安全边界

---

## 2.2 Speak 数据结构：`speak/schemas.py`

### `class SpeakWSInput`

WS 入站消息结构：

- `text`
- `user_id/session_id/thread_id/topic`

### `class SpeakWSOutput`

WS 出站结构：

- `id, text, audio, is_end, audio_pending, error`

### `SpeakWSOutput.from_dict(payload)`

将底层 dict 统一转换为强类型输出对象。

---

## 2.3 Speak 服务层：`speak/service.py`

### `class SpeakService`

封装口语对话基础能力。

### `__init__(ai_service=None)`

默认创建 `AIService(system_prompt=SAKIKO_SYSTEM_PROMPT)`。

### `parse_user_message(raw_message)`

兼容：

- 纯文本 WS 消息
- JSON WS 消息

并补齐默认值：

- `user_id` 默认 `speak-demo-user`
- `thread_id` 缺失时自动生成 UUID

### `cleanup()`

释放底层 TTS/模型资源。

---

## 2.4 Speak 工作流：`speak/workflow.py`

### `handle_speak_websocket(websocket)`

口语实时主流程：

1. `websocket.accept()`
2. 接收前端消息
3. `parse_user_message` 解析上下文
4. 调 `ai_service.get_chat_stream(text)` 获取流式 chunk
5. chunk 转 `SpeakWSOutput` 并回发前端
6. 聚合 AI 文本写入 speak 历史表
7. 异常返回 `is_end=true + error`
8. finally 执行 `cleanup`

---

## 2.5 Speak 历史存储：`speak/history_store.py`

### `ensure_speak_history_tables()`

初始化：

- `speak_history_threads`
- `speak_history_messages`

### `upsert_speak_thread_and_append_messages(...)`

一轮口语对话写入：

1. upsert 线程
2. 插入 user 消息
3. 插入 assistant 消息

### `list_speak_threads(user_id)`

返回该用户口语线程列表（按更新时间倒序）。

### `get_speak_thread_detail(user_id, thread_id)`

返回线程元信息 + 消息明细。

---

## 2.6 语音核心流式引擎：`src/services/langchain/llm.py`

## `class TextSlicer`

### `add_text(text)`

把 LLM 增量文本按标点切片；无标点时按长度兜底切片，保证前端实时性。

### `flush()`

输出缓冲区剩余文本。

## `class AIService`

### `__init__(llm=None, system_prompt=None)`

初始化：

- 模型实例
- TTS 客户端占位
- 对话消息历史（首条系统提示）
- 序列号计数器

### `_next_sequence_id()` / `_reset_sequence()`

维护流式片段顺序 id。

### `initialize_tts()`

惰性初始化 `StreamingTTS`。

### `cleanup()`

关闭 TTS 连接。

### `_synthesize_slice(text, seq_id)`

将单片文本转 base64 音频。

### `get_chat_stream(message)`

核心流：

1. 记录用户消息
2. 调用 LLM 流式生成文本
3. 文本切片后先下发 `audio_pending=true` 文本包
4. 异步并发 TTS，音频完成后再下发音频包
5. 最后发送 `is_end=true`
6. 异常时发送错误结束包
7. 维护有限消息历史（避免内存增长）

---

## 2.7 Speak 路由函数（`ai/route.py`）

### `chat_websocket(websocket)`

兼容入口，直接转发到 `handle_speak_websocket`。

### `speak_websocket(websocket)`

语义化入口，同样转发到 `handle_speak_websocket`。

### `list_speak_history(user_id)`

返回口语线程列表。

### `get_speak_history_detail(thread_id, user_id)`

返回口语线程消息明细。

---

## 3. 端到端流程图（文字版）

## 3.1 作文批改

```text
POST /ai/composition/grade
  -> create_initial_state
  -> workflow.invoke(thread_id)
      analyze_topic
      -> retrieve_samples (并行)
      -> retrieve_rubric (并行)
      -> score_essay
      -> detect_errors
      -> generate_suggestions
  -> upsert composition history
  -> return grade response
```

```text
POST /ai/composition/revise
  -> workflow.get_state(thread_id)
  -> _build_previous_summary
  -> create_initial_state(revised_essay + previous_summary)
  -> workflow.invoke(thread_id)
  -> compute delta/improved
  -> upsert composition history
  -> return revise response
```

## 3.2 语音对话

```text
WS /ai/speak/ws
  -> handle_speak_websocket
      receive text/json
      -> parse_user_message
      -> ai_service.get_chat_stream
          (LLM stream -> text slice -> async TTS -> ordered chunks)
      -> send stream chunks to frontend
      -> upsert speak history
```

---

## 4. 当前实现注意点（与代码一致）

1. Composition 若未提供 `thread_id`，由后端生成。
2. Speak 若未提供 `thread_id`，`parse_user_message` 自动生成。
3. Speak 历史落库依赖前端 WS 消息里携带 `user_id/session_id/thread_id/topic`。
4. `AIService` 是通用流式引擎；speak 通过 `system_prompt` 注入角色人设，不影响 composition graph。
5. `current_step` 使用 reducer 解决并发写冲突。

---

## 5. 建议后续文档拆分

当前文档是总览+函数级说明。若继续扩展，建议拆为：

- `composition-architecture.md`（图与状态）
- `composition-api.md`（请求/响应/示例）
- `speak-realtime-protocol.md`（WS 包协议与时序）
- `history-schema.md`（history 表结构与索引）
