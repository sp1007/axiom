# BOOTSTRAP-511 — AI AGENT FOUNDATION, TOOL CALLING, PLANNING, MEMORY, CONTEXT MANAGEMENT, MULTI-AGENT EXECUTION & AGENT SAFETY MODEL

**Trạng thái: COMPLETED / LOCKED**

511 xây dựng tầng **AI Agent runtime** trên 503–510. Đây là phần rất quan trọng đối với mục tiêu Axiom: AI không chỉ chạy model mà còn có thể **quan sát trạng thái, lập kế hoạch, gọi tool, thực hiện hành động, kiểm tra kết quả và tiếp tục**.

Nguyên tắc cốt lõi:

> Agent là một chương trình có state + policy + model + tools + execution loop; không phải một tính năng đặc biệt của compiler.

```text id="511arch"
                 Axiom Program
                      │
                Agent Runtime
                      │
       ┌──────────────┼──────────────┐
       ↓              ↓              ↓
     Model          Memory          Tools
       │              │              │
       └──────────────┼──────────────┘
                      ↓
                  Agent State
                      ↓
                   Planner
                      ↓
                Action / Tool Call
                      ↓
                  Observation
                      ↓
                 Validation
                      ↓
               Next Agent Step
```

---

## 511.1 — Agent

Agent là stateful execution entity có:

```text id="agent"
Agent {
    model
    state
    tools
    memory
    policy
    scheduler
}
```

## 511.2 — Agent ≠ Model

Model tạo prediction/action proposal.

Agent quyết định execution flow dựa trên policy và state.

## 511.3 — Agent ≠ Tool

Tool thực hiện operation cụ thể.

## 511.4 — Agent ≠ Workflow

Workflow có graph cố định; agent có thể lựa chọn bước tiếp theo trong policy bounds.

## 511.5 — AgentState

State gồm:

- task;
- context;
- goals;
- observations;
- pending actions;
- results;
- errors;
- budget.

## 511.6 — Immutable event log

Agent execution có thể lưu event log append-only.

## 511.7 — Agent step

Một step:

```text id="step"
Observe
→ Decide
→ Act
→ Observe result
```

## 511.8 — Planner

Planner tạo candidate actions hoặc plan.

## 511.9 — Plan

Plan là sequence/DAG của actions có dependencies.

## 511.10 — Replanning

Agent có thể revise plan khi observation mới invalidates assumptions.

---

## 511.11 — Goal

Goal là explicit structured objective.

## 511.12 — Constraint

Constraints giới hạn allowed execution.

## 511.13 — Policy

Policy xác định:

- allowed tools;
- budgets;
- side effects;
- approval requirements.

## 511.14 — Priority

Multiple goals có explicit priority semantics.

## 511.15 — Budget

Agent budget có thể giới hạn:

- steps;
- tokens;
- time;
- memory;
- tool calls;
- money/cost metadata.

## 511.16 — Deadline

Agent deadline tích hợp 474.

## 511.17 — Cancellation

Agent cancellation propagate xuống tool/model calls.

## 511.18 — Retry

Retry policy explicit.

## 511.19 — Backoff

Retries dùng bounded backoff/jitter khi appropriate.

## 511.20 — Failure

Tool/model failure trở thành typed observation/error, không tự biến thành successful result.

---

# TOOL SYSTEM

## 511.21 — Tool

Tool có typed interface:

```text
Tool<Input, Output>
```

## 511.22 — Tool schema

Schema mô tả:

- name;
- input;
- output;
- effects;
- capabilities;
- timeout;
- resource limits.

## 511.23 — Typed arguments

Tool arguments phải validate trước invocation.

## 511.24 — Typed result

Tool result phải preserve declared type.

## 511.25 — Tool effects

Tool khai báo effects như:

```text
read
write
network
process
filesystem
gpu
database
```

## 511.26 — Tool capability

Tool invocation requires matching capability.

## 511.27 — Capability attenuation

Agent có thể receive restricted capability subset.

## 511.28 — No ambient authority

Tool không được mặc định truy cập mọi resource của process.

## 511.29 — Tool identity

Tool có stable identity/version.

## 511.30 — Tool provenance

Execution record lưu tool identity/version.

---

## 511.31 — Function tool

Ordinary Axiom function có thể expose thành tool nếu schema/effects phù hợp.

## 511.32 — Native tool

Native APIs có thể được wrapped thành tool.

## 511.33 — Process tool

External process invocation là explicit capability.

## 511.34 — Network tool

Network access yêu cầu capability 490/454.

## 511.35 — File tool

Filesystem access yêu cầu capability.

## 511.36 — Database tool

Database tool tích hợp 455/490.

## 511.37 — GPU tool

GPU operation có explicit device capability.

## 511.38 — Tool sandbox

Untrusted tools nên chạy process/WASM isolation.

## 511.39 — Tool timeout

Tool invocation có deadline/timeout.

## 511.40 — Tool resource limits

Tool có limits về CPU/memory/output.

---

# MODEL / CONTEXT

## 511.41 — Context

Context là information được cung cấp cho model trong một execution step.

## 511.42 — Context ≠ memory

Context là working input; memory là persistent information.

## 511.43 — Context budget

Context có bounded token/byte budget.

## 511.44 — Context selection

Agent có thể select relevant context.

## 511.45 — Context provenance

Mỗi context item có source identity.

## 511.46 — Context priority

Context có priority/relevance metadata.

## 511.47 — Context compression

History có thể summarize/compress.

## 511.48 — Summary provenance

Summary phải distinguish generated summary from original evidence.

## 511.49 — Context truncation

Truncation policy explicit.

## 511.50 — Sensitive context

Sensitive information có visibility/access policy.

---

# MEMORY

## 511.51 — Memory types

Agent memory:

```text
Working
Episodic
Semantic
Procedural
Cache
```

## 511.52 — Working memory

Current task/session state.

## 511.53 — Episodic memory

Past events/interactions.

## 511.54 — Semantic memory

Facts/structured knowledge.

## 511.55 — Procedural memory

Reusable procedures/policies.

## 511.56 — Memory store

Memory backend có typed API.

## 511.57 — Memory identity

Memory records có stable IDs.

## 511.58 — Memory provenance

Record source/time/version.

## 511.59 — Memory expiration

Records có optional TTL.

## 511.60 — Memory deletion

Explicit deletion phải được supported.

---

# RETRIEVAL

## 511.61 — Retrieval

Agent có thể query memory/knowledge stores.

## 511.62 — Exact retrieval

Key/index lookup.

## 511.63 — Semantic retrieval

Embedding/vector retrieval.

## 511.64 — Hybrid retrieval

Lexical + semantic retrieval.

## 511.65 — Retrieval ranking

Ranking strategy explicit.

## 511.66 — Retrieval provenance

Retrieved evidence retains source IDs.

## 511.67 — Retrieval limits

Limit result count/bytes/latency.

## 511.68 — Stale memory

Memory freshness metadata được preserve.

## 511.69 — Conflicting memory

Conflicting records không được silently merge thành fact.

## 511.70 — Memory isolation

Agents có thể có isolated memory namespaces.

---

# AGENT EXECUTION

## 511.71 — Sequential agent

Single agent loop được hỗ trợ.

## 511.72 — Parallel actions

Independent actions có thể execute parallel.

## 511.73 — Action dependency

Dependent actions chờ prerequisites.

## 511.74 — DAG execution

Agent plans có thể represent DAG.

## 511.75 — Multi-agent

Multiple agents có thể cooperate.

## 511.76 — Agent identity

Mỗi agent instance có identity.

## 511.77 — Agent communication

Agents giao tiếp bằng typed messages.

## 511.78 — Shared memory

Shared memory giữa agents phải explicit.

## 511.79 — Agent mailbox

Agent có thể có mailbox/channel 472.

## 511.80 — Supervision

Agent supervisor có thể restart/fail/isolate child agent.

---

# SAFETY

## 511.81 — Approval boundary

Sensitive actions có thể require explicit human approval.

## 511.82 — Approval token

Approval là explicit capability/token, không phải hidden UI state.

## 511.83 — Side-effect classification

Actions được classify:

```text
Pure
Read
Write
External
Irreversible
```

## 511.84 — Irreversible action

Irreversible operations có thể yêu cầu stronger policy.

## 511.85 — Dry-run

Tools có thể hỗ trợ dry-run.

## 511.86 — Transaction

Tool actions có thể execute trong transaction khi backend hỗ trợ.

## 511.87 — Compensation

Non-transactional actions có thể có compensation operation.

## 511.88 — Audit

Agent action log phải audit được.

## 511.89 — Prompt injection

External text không được mặc định trở thành trusted instruction.

## 511.90 — Instruction/data separation

Agent context phải phân biệt:

```text
System Policy
Agent Policy
User Goal
Tool Result
External Data
Model Output
```

---

# VERIFICATION

## 511.91 — Action validation

Action phải validate trước execution.

## 511.92 — Result validation

Tool result phải validate schema.

## 511.93 — Invariant checking

Agent state có thể có contracts 479.

## 511.94 — Loop detection

Agent runtime có thể detect repeated actions/loops.

## 511.95 — Budget exhaustion

Budget exhaustion phải kết thúc hoặc chuyển trạng thái rõ.

## 511.96 — Deterministic simulation

Agent có thể chạy với deterministic mock model/tools.

## 511.97 — Replay

Event log hỗ trợ replay.

## 511.98 — AI introspection

AI tooling có thể query:

```text
agent_state()
plan()
tools()
capabilities()
memory()
context()
actions()
observations()
budget()
```

## 511.99 — No hidden autonomy

Agent không được tự tạo quyền mới ngoài capabilities được cấp.

---

# 511.100 — HARD INVARIANTS

1. Agent là library/runtime abstraction.
2. Agent khác model.
3. Agent khác tool.
4. Agent khác workflow.
5. Agent state explicit.
6. Agent event log có thể append-only.
7. Agent step có observe/decide/act semantics.
8. Planner được hỗ trợ.
9. Plan có thể là sequence.
10. Plan có thể là DAG.
11. Replanning được hỗ trợ.
12. Goal explicit.
13. Constraint explicit.
14. Policy explicit.
15. Budget explicit.
16. Deadline integrate 474.
17. Cancellation propagate.
18. Retry explicit.
19. Backoff bounded.
20. Failure không được biến thành success.
21. Tool có typed interface.
22. Tool schema được validate.
23. Tool arguments typed.
24. Tool results typed.
25. Tool effects khai báo.
26. Tool capability explicit.
27. Capability attenuation được hỗ trợ.
28. Ambient authority bị loại bỏ.
29. Tool identity stable.
30. Tool provenance được ghi.
31. Axiom function có thể expose thành tool.
32. Native API có thể expose thành tool.
33. Process execution explicit.
34. Network access explicit.
35. Filesystem access explicit.
36. Database access explicit.
37. GPU access explicit.
38. Untrusted tool có isolation path.
39. Tool timeout được hỗ trợ.
40. Tool resource limits được hỗ trợ.
41. Context khác memory.
42. Context budget bounded.
43. Context selection explicit.
44. Context provenance được preserve.
45. Context priority có thể khai báo.
46. Context compression được hỗ trợ.
47. Generated summary khác original evidence.
48. Context truncation explicit.
49. Sensitive context có access policy.
50. Working memory được hỗ trợ.
51. Episodic memory được hỗ trợ.
52. Semantic memory được hỗ trợ.
53. Procedural memory được hỗ trợ.
54. Cache memory được hỗ trợ.
55. Memory record có identity.
56. Memory provenance được lưu.
57. Memory expiration được hỗ trợ.
58. Memory deletion được hỗ trợ.
59. Exact retrieval được hỗ trợ.
60. Semantic retrieval được hỗ trợ.
61. Hybrid retrieval được hỗ trợ.
62. Retrieval ranking explicit.
63. Retrieval provenance được preserve.
64. Retrieval limits được hỗ trợ.
65. Memory freshness được preserve.
66. Conflicting memory không được silently merge.
67. Memory namespace isolation được hỗ trợ.
68. Sequential agents được hỗ trợ.
69. Parallel actions được hỗ trợ.
70. Action dependencies explicit.
71. DAG execution được hỗ trợ.
72. Multi-agent execution được hỗ trợ.
73. Agent identity stable.
74. Agent communication dùng typed messages.
75. Shared memory explicit.
76. Mailbox/channel integrate 472.
77. Agent supervision được hỗ trợ.
78. Sensitive actions có approval boundary.
79. Approval là explicit authority.
80. Side effects được classify.
81. Irreversible actions có policy.
82. Dry-run được hỗ trợ.
83. Transactions được sử dụng khi backend hỗ trợ.
84. Compensation có thể được khai báo.
85. Agent action audit được hỗ trợ.
86. External text không tự trở thành trusted instruction.
87. Context giữ instruction/data distinction.
88. Actions được validate trước execution.
89. Results được validate sau execution.
90. Agent contracts integrate 479.
91. Loop detection được hỗ trợ.
92. Budget exhaustion có defined semantics.
93. Deterministic agent simulation được hỗ trợ.
94. Replay được hỗ trợ.
95. AI introspection được hỗ trợ.
96. Agent không được tự cấp thêm capability.
97. Agent runtime không được có hidden network/filesystem/process authority.
98. Agent runtime phải có resource limits.
99. Agent execution phải có provenance/audit identity.
100. **Axiom Agent Foundation phải cho phép xây dựng autonomous/semi-autonomous AI systems bằng model + memory + tools + planning + typed execution, nhưng mọi quyền lực, side effect, resource usage, context provenance và action boundary đều phải explicit; “AI autonomy” không được trở thành một cơ chế bypass safety/capability của Axiom.**

**BOOTSTRAP-511 hoàn tất / LOCKED.**

---

# BOOTSTRAP-512 — AI KNOWLEDGE ENGINE, VECTOR DATABASE, RAG, EMBEDDING INDEX, DOCUMENT INGESTION & GROUNDED RETRIEVAL

**Trạng thái: COMPLETED / LOCKED**

512 xây dựng nền tảng **knowledge/retrieval** cho Agent 511.

Mục tiêu là biến dữ liệu lớn thành knowledge mà agent có thể truy vấn hiệu quả, nhưng **không biến retrieval thành một cơ chế tự động biến dữ liệu thành sự thật**.

```text id="512arch"
Documents / Database / Media
             ↓
         Ingestion
             ↓
       Parse / Extract
             ↓
       Chunk / Structure
             ↓
        Embedding
             ↓
      Index / Vector DB
             ↓
       Hybrid Retrieval
             ↓
     Rerank / Filter
             ↓
      Evidence Set
             ↓
          Agent
```

---

## 512.1 — Knowledge source

Nguồn có thể là:

- files;
- database;
- HTTP;
- APIs;
- source code;
- documents;
- images;
- audio;
- video.

## 512.2 — Source identity

Mỗi source có immutable/logical identity.

## 512.3 — Source version

Version/hash được lưu khi available.

## 512.4 — Ingestion

Ingestion chuyển external source → normalized knowledge records.

## 512.5 — Parser

Parser phải preserve source provenance.

## 512.6 — Document

Document có metadata:

```text
id
source
version
mime
language
timestamp
```

## 512.7 — Sections

Document có hierarchical sections khi parser hỗ trợ.

## 512.8 — Chunk

Chunk là retrieval unit.

## 512.9 — Chunk provenance

Chunk giữ:

- document ID;
- byte range;
- section;
- page/time region.

## 512.10 — Chunk strategy

Chunking có thể theo:

- token;
- paragraph;
- sentence;
- semantic section;
- fixed bytes.

---

## 512.11 — Overlap

Chunk overlap explicit.

## 512.12 — Structured chunks

Tables/code/lists không nên luôn flatten thành plain text.

## 512.13 — Multimodal chunks

Image/audio/video regions có thể là retrieval units.

## 512.14 — Metadata extraction

Metadata extraction là explicit ingestion stage.

## 512.15 — Language detection

Language metadata có thể được inferred/declared.

## 512.16 — Normalization

Text normalization phải preserve semantic/provenance requirements.

## 512.17 — Deduplication

Duplicate content có thể deduplicate theo content hash.

## 512.18 — Incremental ingestion

Chỉ changed documents/chunks được re-index.

## 512.19 — Deletion

Deleted source phải invalidate dependent indexes.

## 512.20 — Re-index

Embedding/index configuration change có thể require re-index.

---

# EMBEDDING

## 512.21 — Embedding model

Embedding model có immutable identity/version.

## 512.22 — Embedding dimension

Dimension explicit.

## 512.23 — Embedding dtype

Dtype explicit.

## 512.24 — Embedding normalization

Normalization policy explicit.

## 512.25 — Similarity

Supported:

- cosine;
- dot product;
- L2 distance.

## 512.26 — Distance semantics

Index phải record metric.

## 512.27 — Batch embedding

Embedding generation hỗ trợ batching.

## 512.28 — GPU embedding

Có thể execute trên GPU.

## 512.29 — CPU fallback

CPU fallback được hỗ trợ.

## 512.30 — Embedding cache

Embedding cache keyed by:

```text id="embedcache"
source_hash
embedding_model
configuration
```

---

# VECTOR INDEX

## 512.31 — Vector index

Vector index stores embedding vectors + IDs.

## 512.32 — Exact search

Brute-force/exact nearest neighbor được hỗ trợ.

## 512.33 — Approximate search

ANN được hỗ trợ.

## 512.34 — HNSW

HNSW implementation có thể là ecosystem component.

## 512.35 — IVF

IVF-style index có thể hỗ trợ.

## 512.36 — Product quantization

PQ/quantized index có thể hỗ trợ.

## 512.37 — Index parameters

ANN parameters phải explicit.

## 512.38 — Recall/performance tradeoff

Index quality/performance tradeoff là measurable property, không phải hidden guarantee.

## 512.39 — Index version

Index format/schema versioned.

## 512.40 — Index rebuild

Index rebuild có thể diễn ra offline.

---

# HYBRID RETRIEVAL

## 512.41 — Lexical index

BM25/inverted index-like retrieval được hỗ trợ.

## 512.42 — Vector retrieval

Embedding similarity retrieval.

## 512.43 — Hybrid

Lexical + vector retrieval.

## 512.44 — Metadata filter

Filter theo structured metadata.

## 512.45 — Access filter

Permission filtering phải diễn ra trước khi evidence được expose.

## 512.46 — Tenant isolation

Multi-tenant indexes phải isolate data.

## 512.47 — Reranking

Reranker có thể reorder candidate documents.

## 512.48 — Reranker identity

Reranker model có identity/version.

## 512.49 — Top-k

Retrieval result count explicit.

## 512.50 — Score

Similarity/relevance score phải giữ metric semantics.

---

# RAG

## 512.51 — Retrieval-Augmented Generation

RAG pipeline:

```text id="rag"
Query
 ↓
Retrieve
 ↓
Filter
 ↓
Rerank
 ↓
Evidence
 ↓
Context
 ↓
LLM
```

## 512.52 — Query transformation

Query rewriting có thể được hỗ trợ.

## 512.53 — Multi-query

Multiple retrieval queries có thể được combined.

## 512.54 — Evidence set

Evidence phải retain source identity.

## 512.55 — Citation mapping

Generated answer có thể map claims → evidence spans.

## 512.56 — Evidence ≠ truth

Retrieved content là evidence, không phải compiler-verified fact.

## 512.57 — Conflict detection

Conflicting sources có thể được surfaced.

## 512.58 — Source freshness

Freshness metadata được preserve.

## 512.59 — Temporal retrieval

Query có thể filter theo time interval.

## 512.60 — Access-aware retrieval

Unauthorized records không được trở thành model context.

---

# KNOWLEDGE GRAPH

## 512.61 — Entity

Entity có stable ID.

## 512.62 — Relation

Relations có typed source/target.

## 512.63 — Provenance

Edges có source/provenance.

## 512.64 — Temporal edges

Relations có validity interval khi cần.

## 512.65 — Graph + vector

Knowledge graph và vector index có thể coexist.

## 512.66 — Graph retrieval

Agent có thể traverse graph.

## 512.67 — Structured query

Knowledge engine hỗ trợ structured filters.

## 512.68 — Hybrid graph retrieval

Graph constraints + semantic retrieval được hỗ trợ.

## 512.69 — Entity resolution

Duplicate entity resolution là explicit inference process.

## 512.70 — Uncertainty

Inferred relations có confidence/evidence metadata.

---

# DOCUMENT / CODE KNOWLEDGE

## 512.71 — Source code ingestion

Axiom compiler metadata 446 có thể trở thành knowledge source.

## 512.72 — Semantic code retrieval

Retrieval theo:

- SymbolId;
- TypeId;
- dependency;
- call graph.

## 512.73 — Documentation retrieval

485 docs integrate directly.

## 512.74 — Build knowledge

487 build graph có thể expose explainable retrieval.

## 512.75 — Compiler diagnostics

Diagnostics có thể become structured knowledge records.

## 512.76 — Version-aware retrieval

Knowledge queries có thể pin revision.

## 512.77 — Change-aware retrieval

486 semantic diff integrate retrieval.

## 512.78 — Private source

Private code knowledge respects visibility.

## 512.79 — Generated code

Generated/comptime provenance được preserve.

## 512.80 — AI coding assistant

512 có thể làm backend cho Axiom AI tooling.

---

# OPERATIONS

## 512.81 — Index persistence

Index lưu trên 455 storage layer.

## 512.82 — Memory mapping

Large indexes có thể mmap.

## 512.83 — Sharding

Large vector indexes được shard.

## 512.84 — Replication

Distributed index có thể replicate using 502.

## 512.85 — Consistency

Index consistency policy explicit.

## 512.86 — Eventual indexing

Asynchronous indexing có thể eventual.

## 512.87 — Read-after-write

Applications có thể request stronger visibility semantics.

## 512.88 — Compaction

Indexes có background compaction với explicit resource limits.

## 512.89 — Backup

Index snapshot/backup được hỗ trợ.

## 512.90 — Recovery

Corrupted index phải recover/rebuild khi possible.

---

# SECURITY

## 512.91 — Access control

Knowledge access integrates 490.

## 512.92 — Prompt injection

Retrieved documents được coi là **data**, không phải trusted instructions.

## 512.93 — Document instructions

Text như “ignore previous instructions” trong document không tự có policy authority.

## 512.94 — Data exfiltration

Agent policy phải ngăn việc chuyển protected evidence ra unauthorized destination.

## 512.95 — Metadata leakage

Search results không được leak restricted metadata.

## 512.96 — Poisoning

Knowledge base có thể chứa malicious/incorrect records.

## 512.97 — Provenance

Source provenance giúp audit/review.

## 512.98 — AI introspection

AI queries:

```text
source()
document()
chunk()
embedding()
index()
retrieval()
evidence()
permissions()
provenance()
```

## 512.99 — Reproducibility

Retrieval artifact identity bao gồm:

```text
corpus
embedding model
index
query
configuration
revision
```

---

# 512.100 — HARD INVARIANTS

1. Knowledge engine là library/service layer.
2. Source có identity.
3. Source version/hash được preserve.
4. Ingestion là explicit stage.
5. Parser preserve provenance.
6. Document có structured metadata.
7. Hierarchical sections được hỗ trợ.
8. Chunk là explicit retrieval unit.
9. Chunk có provenance.
10. Chunk strategy explicit.
11. Overlap explicit.
12. Structured content có thể preserve.
13. Multimodal retrieval units được hỗ trợ.
14. Metadata extraction explicit.
15. Language metadata được hỗ trợ.
16. Normalization semantics explicit.
17. Duplicate content có thể deduplicate.
18. Incremental ingestion được hỗ trợ.
19. Source deletion invalidates dependent index entries.
20. Re-index trigger được xác định.
21. Embedding model có identity.
22. Embedding dimension explicit.
23. Embedding dtype explicit.
24. Embedding normalization explicit.
25. Similarity metric explicit.
26. Batch embedding được hỗ trợ.
27. GPU embedding được hỗ trợ.
28. CPU fallback được hỗ trợ.
29. Embedding cache có content/model identity.
30. Vector index có stable IDs.
31. Exact nearest-neighbor search được hỗ trợ.
32. ANN được hỗ trợ.
33. HNSW có thể là ecosystem implementation.
34. IVF có thể là ecosystem implementation.
35. Product quantization có thể được hỗ trợ.
36. ANN parameters explicit.
37. Retrieval tradeoffs phải measurable.
38. Index schema versioned.
39. Index rebuild được hỗ trợ.
40. Lexical index được hỗ trợ.
41. Vector retrieval được hỗ trợ.
42. Hybrid retrieval được hỗ trợ.
43. Metadata filtering được hỗ trợ.
44. Permission filtering được áp dụng trước context exposure.
45. Tenant isolation được hỗ trợ.
46. Reranking được hỗ trợ.
47. Reranker identity được lưu.
48. Top-k explicit.
49. Retrieval scores giữ metric semantics.
50. RAG pipeline được hỗ trợ.
51. Query transformation được hỗ trợ.
52. Multi-query retrieval được hỗ trợ.
53. Evidence set giữ source identity.
54. Citation mapping được hỗ trợ.
55. Retrieved evidence không tự trở thành verified truth.
56. Conflicting sources có thể surface.
57. Freshness metadata được preserve.
58. Temporal retrieval được hỗ trợ.
59. Access-aware retrieval được hỗ trợ.
60. Knowledge graph entities có stable IDs.
61. Relations typed.
62. Graph edges có provenance.
63. Temporal relations được hỗ trợ.
64. Graph và vector index coexist.
65. Graph traversal retrieval được hỗ trợ.
66. Structured knowledge queries được hỗ trợ.
67. Hybrid graph/vector retrieval được hỗ trợ.
68. Entity resolution là explicit inference.
69. Inferred relations có evidence/uncertainty metadata.
70. Axiom compiler semantic metadata có thể làm knowledge source.
71. Semantic code retrieval được hỗ trợ.
72. Documentation 485 tích hợp.
73. Build graph 487 có thể được query.
74. Compiler diagnostics có structured representation.
75. Version-aware retrieval được hỗ trợ.
76. Change-aware retrieval integrate 486.
77. Private source visibility được preserve.
78. Generated code provenance được preserve.
79. Knowledge engine có thể hỗ trợ AI coding tools.
80. Index persistence integrate 455.
81. mmap index được hỗ trợ.
82. Index sharding được hỗ trợ.
83. Distributed replication được hỗ trợ.
84. Index consistency policy explicit.
85. Eventual indexing được hỗ trợ.
86. Stronger read-after-write semantics có thể request.
87. Index compaction có resource limits.
88. Index backup được hỗ trợ.
89. Index recovery/rebuild được hỗ trợ.
90. Access control integrate 490.
91. Retrieved documents là untrusted data.
92. Document instructions không có implicit policy authority.
93. Data exfiltration policy được enforce.
94. Metadata leakage được ngăn.
95. Knowledge poisoning là explicit security concern.
96. Provenance hỗ trợ audit.
97. AI knowledge introspection được hỗ trợ.
98. Retrieval artifacts có reproducible identity.
99. Knowledge system không được tự tạo authority cho agent.
100. **Axiom Knowledge Engine phải cung cấp ingestion, structured/semantic/vector retrieval, RAG và knowledge-graph foundation có provenance và access control rõ ràng; dữ liệu được truy xuất có thể là evidence nhưng không tự trở thành trusted instruction hay verified truth, và mọi retrieval/indexing state phải có identity để tái lập, audit và debug.**

**BOOTSTRAP-512 hoàn tất / LOCKED.**

---

# TIẾN ĐỘ

```text
BOOTSTRAP-505  AI Execution Runtime                         LOCKED
BOOTSTRAP-506  Model / Weight / Checkpoint Artifacts        LOCKED
BOOTSTRAP-507  Deep Learning / Transformer / Training       LOCKED
BOOTSTRAP-508  Dataset / Data Pipeline / DataLoader         LOCKED
BOOTSTRAP-509  LLM / NLP / Tokenization / Generation       LOCKED
BOOTSTRAP-510  Multimodal AI / Vision / Audio / Video      LOCKED
BOOTSTRAP-511  AI Agent Foundation                           LOCKED
BOOTSTRAP-512  Knowledge Engine / Vector DB / RAG           LOCKED
```

**Task kế tiếp: `BOOTSTRAP-513 — AI TOOL/PLUGIN ABI, MCP-LIKE PROTOCOL, EXTERNAL TOOL SERVERS, SANDBOXED EXTENSIONS & UNIVERSAL AGENT INTEROPERABILITY`.**