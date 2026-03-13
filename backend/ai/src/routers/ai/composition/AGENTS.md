# Composition Module - Essay Grading

**Parent:** `src/routers/ai/`

## OVERVIEW

IELTS essay grading workflow using LangGraph StateGraph. Multi-node pipeline: topic analysis → sample retrieval → rubric retrieval → scoring → error detection → suggestions.

## STRUCTURE

```
composition/
├── workflow.py          # StateGraph definition (START → nodes → END)
├── essay_state.py       # TypedDict state + create_initial_state()
├── checkpoint.py        # PostgreSQL checkpointer for LangGraph
├── history_store.py     # Thread persistence (composition_threads, composition_messages)
├── nodes/               # Async node functions
│   ├── analyze_topic.py
│   ├── retrieve_samples.py   # Milvus vector search
│   ├── retrieve_rubric.py    # Milvus vector search
│   ├── score_essay.py
│   ├── detect_errors.py
│   └── generate_suggestions.py
├── chains/              # LangChain chains for each node
│   ├── score_grader.py
│   ├── error_detector.py
│   └── suggestion_provider.py
└── ingestion/           # Data pipeline for Milvus
    ├── create_essay_rubrics.py
    └── insert_ielts_sample_essays.py
```

## WHERE TO LOOK

| Task | Location |
|------|----------|
| Add scoring dimension | `nodes/score_essay.py` + `chains/score_grader.py` |
| Modify retrieval | `nodes/retrieve_*.py` - uses `milvus_client` |
| Change state shape | `essay_state.py` - EssayState TypedDict |
| Add new node | `nodes/` → register in `workflow.py:build_workflow()` |
| Data ingestion | `ingestion/` scripts for Milvus |

## CONVENTIONS

### Node Pattern
```python
# nodes/*.py - Each node is an async function
async def node_name(state: EssayState) -> EssayState:
    # Process state
    return {**state, "new_key": value}
```

### Chain Pattern
```python
# chains/*.py - LangChain chains for LLM calls
chain = prompt | llm | parser
result = chain.invoke({"input": ...})
```

### Parallel Execution
After `analyze_topic`, both `retrieve_samples` and `retrieve_rubric` run in parallel before `score_essay`.

## ANTI-PATTERNS

- **Don't** modify `essay_state.py` without updating all nodes
- **Don't** skip `checkpoint.py` - required for state persistence across revisions
- **Don't** use sync Milvus calls in async nodes

## NOTES

- **Milvus Collections**: `essay_samples`, `essay_rubrics`
- **Revision Support**: `revise_composition()` reuses thread_id to access previous state
- **Scoring**: Band score 0-9 with dimension scores (task_response, coherence, lexical, grammar)