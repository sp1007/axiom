# BOOTSTRAP-515 — AI MEMORY & PERSONALIZATION ENGINE, LONG-TERM MEMORY, USER/AGENT PROFILE, LEARNING, MEMORY CONSOLIDATION & FORGETTING SEMANTICS

**Trạng thái: COMPLETED / LOCKED**

515 xây dựng tầng memory dài hạn phía trên 511–514. Điểm quan trọng là Axiom phải phân biệt rõ:

```text
Context ≠ Memory ≠ Knowledge ≠ Profile ≠ Model Parameters
```

Memory không được trở thành một “database thần bí” mà agent tự ghi mọi thứ vào. Mọi memory phải có **identity, provenance, scope, confidence, lifecycle và deletion semantics**.

```text id="515arch"
                    AI Agent 511
                         │
                  Memory Controller
                         │
        ┌────────────────┼────────────────┐
        ↓                ↓                ↓
   Working Memory   Long-Term Memory   Profile
        │                │                │
        └────────────────┼────────────────┘
                         ↓
                 Memory Consolidation
                         ↓
             ┌───────────┼───────────┐
             ↓           ↓           ↓
          Store       Update       Forget
             │           │           │
             └───────────┼───────────┘
                         ↓
                  Retrieval 512
                         ↓
                  Context 514
```

---

# 515.1 — Memory taxonomy

Axiom memory gồm:

```text
Working
Episodic
Semantic
Procedural
Preference
Profile
Task
Relationship
Cache
```

Không loại memory nào được tự động xem là authoritative.

## 515.2 — Working memory

Thông tin cần cho task hiện tại.

## 515.3 — Episodic memory

Sự kiện/interactions cụ thể.

Ví dụ:

```text
User asked X
Agent executed Y
Tool returned Z
```

## 515.4 — Semantic memory

Thông tin đã được tổng hợp thành knowledge record.

## 515.5 — Procedural memory

Procedure/workflow đã được lưu.

## 515.6 — Preference memory

Preference có thể được lưu khi policy cho phép.

## 515.7 — Profile

Profile là tập thuộc tính có cấu trúc, khác với conversation history.

## 515.8 — Task memory

Thông tin phục vụ một task/project cụ thể.

## 515.9 — Relationship memory

Quan hệ giữa entities/agents/projects có provenance.

## 515.10 — Cache memory

Temporary optimization state; không phải long-term knowledge.

---

# MEMORY RECORD

## 515.11 — MemoryRecord

Canonical representation:

```text id="memrec"
MemoryRecord {
    id
    kind
    subject
    content
    source
    scope
    created_at
    updated_at
    valid_from
    valid_until
    confidence
    provenance
    sensitivity
    status
}
```

## 515.12 — Stable identity

Memory ID không được thay đổi khi content được update.

## 515.13 — Content version

Mỗi update có version/generation.

## 515.14 — Provenance

Record phải chỉ ra nguồn:

```text
conversation
document
tool
user
agent
inference
import
```

## 515.15 — Direct vs inferred

Memory phải distinguish:

```text
Observed
Declared
Imported
Inferred
Derived
```

## 515.16 — Confidence

Inference có thể có confidence/uncertainty metadata.

Confidence không phải proof.

## 515.17 — Scope

Memory scope có thể là:

```text
message
session
task
project
agent
user
organization
global
```

## 515.18 — Scope inheritance

Child scope không tự động được quyền ghi parent scope.

## 515.19 — Memory ownership

Memory record có owner/controller identity.

## 515.20 — Memory sensitivity

Có classification:

```text
public
internal
private
sensitive
secret
```

---

# PROFILE

## 515.21 — Profile ≠ Memory

Profile chứa structured attributes.

Memory chứa historical/semantic records.

## 515.22 — Profile schema

Profile fields có explicit schema.

## 515.23 — Profile source

Mỗi profile attribute có provenance.

## 515.24 — Profile update

Update phải qua policy.

## 515.25 — Conflict

Conflicting profile values không được silently overwrite.

## 515.26 — Temporal profile

Profile values có thể có validity interval.

Ví dụ:

```text
Preference A
valid: 2026-01 → 2026-06

Preference B
valid: 2026-06 → present
```

## 515.27 — Confidence

Inferred profile fields phải distinguish khỏi explicitly declared values.

## 515.28 — User-controlled fields

Ứng dụng có thể đánh dấu field chỉ user mới được sửa.

## 515.29 — Agent-controlled fields

Một số operational fields có thể do agent quản lý.

## 515.30 — Immutable attributes

Một số attributes có thể immutable trong một scope.

---

# MEMORY WRITE

## 515.31 — Explicit write

Memory write là operation có policy.

## 515.32 — Auto-memory

Automatic extraction có thể được hỗ trợ nhưng phải bật bằng policy.

## 515.33 — Write filter

Policy có thể chặn categories không được lưu.

## 515.34 — Importance

Memory có importance metadata.

## 515.35 — TTL

Memory có optional TTL.

## 515.36 — Expiration

Expired memory không được retrieve bình thường.

## 515.37 — Pin

Memory có thể pin để tránh automatic eviction.

## 515.38 — Unpin

Unpin explicit.

## 515.39 — Memory budget

Memory store có storage budget.

## 515.40 — Write failure

Memory failure không được silently alter agent result semantics.

---

# MEMORY CONSOLIDATION

## 515.41 — Consolidation

Nhiều episodic records có thể được consolidate thành semantic memory.

```text id="consolidate"
Events
   ↓
Cluster
   ↓
Summarize
   ↓
Extract facts
   ↓
Semantic Memory
```

## 515.42 — Provenance preservation

Semantic memory phải reference source events.

## 515.43 — Lossy consolidation

Consolidation có thể mất chi tiết.

## 515.44 — Original preservation

Original records có thể được giữ để audit/recovery.

## 515.45 — Contradiction detection

Conflicting records phải được detect hoặc retain as alternatives.

## 515.46 — Supersession

New memory có thể supersede old memory.

## 515.47 — No silent history rewrite

Consolidation không được giả vờ rằng historical record ban đầu chưa từng tồn tại.

## 515.48 — Consolidation model

LLM/model dùng để consolidate phải có identity/version.

## 515.49 — Consolidation reproducibility

Consolidated artifact nên record configuration/model identity.

## 515.50 — Human review

Sensitive/high-impact consolidation có thể yêu cầu review.

---

# MEMORY RETRIEVAL

## 515.51 — Retrieval

Integrate 512.

## 515.52 — Exact lookup

ID/key lookup.

## 515.53 — Semantic retrieval

Vector retrieval.

## 515.54 — Temporal retrieval

Query theo validity/time.

## 515.55 — Scope filter

Retrieve theo scope.

## 515.56 — Sensitivity filter

Access control trước retrieval exposure.

## 515.57 — Recency

Recent memory có thể được ưu tiên.

## 515.58 — Importance

Important memory có thể được ưu tiên.

## 515.59 — Relevance

Semantic relevance có thể influence ranking.

## 515.60 — Conflict-aware retrieval

Conflicting memories có thể được trả về cùng metadata thay vì silently selecting one.

---

# FORGETTING

## 515.61 — Forgetting

Forgetting là explicit lifecycle operation.

## 515.62 — User deletion

User có thể request memory deletion khi policy hỗ trợ.

## 515.63 — Scope deletion

Delete có thể áp dụng:

- record;
- category;
- session;
- project;
- profile field.

## 515.64 — Tombstone

Deleted records có thể leave tombstone để ngăn accidental recreation trong replicated systems.

## 515.65 — Derived data

Derived summaries/indexes có deletion/invalidation policy.

## 515.66 — Embedding deletion

Corresponding embedding/index entries phải invalidate.

## 515.67 — Cache deletion

Related caches phải invalidate theo policy.

## 515.68 — Replicated deletion

Distributed stores integrate 502.

## 515.69 — Backup semantics

Deletion khỏi active store không nhất thiết đồng nghĩa backup vật lý đã biến mất ngay; retention policy phải explicit.

## 515.70 — Legal/compliance layer

Compliance-specific deletion policy thuộc application/platform layer, không hard-code vào language core.

---

# MEMORY UPDATE / LEARNING

## 515.71 — Parameter learning ≠ memory learning

Updating model parameters khác updating external memory.

## 515.72 — Memory learning

Agent có thể learn/update external records without retraining model.

## 515.73 — Model fine-tuning

Fine-tuning là separate training operation 507.

## 515.74 — Preference learning

Preference records có thể influence future policy/context.

## 515.75 — No implicit behavior change

Memory update không được silently modify executable agent policy.

## 515.76 — Policy boundary

Memory có thể inform policy nhưng policy authority remains explicit.

## 515.77 — Feedback

Feedback records có source/time/provenance.

## 515.78 — Correction

User correction có thể supersede inferred memory.

## 515.79 — Reversal

Incorrect memory có thể revert/supersede.

## 515.80 — Audit trail

Important memory mutations được audit.

---

# PROJECT MEMORY

## 515.81 — Project namespace

Memory có thể bind với project identity.

## 515.82 — Project history

Decisions/architecture/tasks có thể được stored.

## 515.83 — Semantic project memory

Compiler 446/486 metadata có thể integrate.

## 515.84 — Task continuity

Agent mới có thể recover task state từ project memory.

## 515.85 — Decision provenance

Architecture decisions reference original source/evidence.

## 515.86 — Stale decisions

Old decisions có status/version.

## 515.87 — Task completion

Completed task memory có explicit status.

## 515.88 — Dependency

Task memory có thể reference dependent tasks.

## 515.89 — Knowledge graph

Project memory integrate 512 graph.

## 515.90 — Context generation

514 có thể generate context từ project memory.

---

# MULTI-AGENT MEMORY

## 515.91 — Private memory

Agent có private namespace.

## 515.92 — Shared memory

Shared memory requires explicit authority.

## 515.93 — Memory delegation

Agent có thể grant read/write capability.

## 515.94 — Conflict resolution

Concurrent memory updates cần version/CAS/transaction semantics.

## 515.95 — Distributed storage

502 replication semantics apply.

## 515.96 — Memory consistency

Memory consistency level explicit.

## 515.97 — Memory event stream

Changes có thể publish thành events.

## 515.98 — AI introspection

Queries:

```text id="memquery"
memory()
profile()
provenance()
history()
conflicts()
expiration()
deletions()
consolidation()
```

## 515.99 — Privacy boundary

Agent không được đọc memory ngoài capability scope.

---

# 515.100 — HARD INVARIANTS

1. Context khác memory.
2. Memory khác knowledge.
3. Memory khác profile.
4. Profile khác model parameters.
5. Working memory được hỗ trợ.
6. Episodic memory được hỗ trợ.
7. Semantic memory được hỗ trợ.
8. Procedural memory được hỗ trợ.
9. Preference memory được hỗ trợ.
10. Profile được hỗ trợ.
11. Task memory được hỗ trợ.
12. Relationship memory được hỗ trợ.
13. Cache memory được phân biệt.
14. MemoryRecord có stable identity.
15. Memory version/generation được lưu.
16. Memory provenance được lưu.
17. Direct/inferred status được phân biệt.
18. Confidence không phải proof.
19. Scope được lưu.
20. Child scope không tự cấp quyền parent.
21. Memory ownership explicit.
22. Sensitivity classification được hỗ trợ.
23. Profile có schema.
24. Profile attributes có provenance.
25. Profile update qua policy.
26. Conflicting profile values không silently overwrite.
27. Profile hỗ trợ temporal validity.
28. Inferred profile khác declared profile.
29. User-controlled fields được hỗ trợ.
30. Agent-controlled fields được phân biệt.
31. Immutable fields được hỗ trợ.
32. Memory write là policy-controlled operation.
33. Automatic memory extraction là opt-in.
34. Write filter được hỗ trợ.
35. Importance metadata được hỗ trợ.
36. TTL được hỗ trợ.
37. Expiration có defined semantics.
38. Pin được hỗ trợ.
39. Unpin được hỗ trợ.
40. Memory budget được hỗ trợ.
41. Memory write failure không silently change task semantics.
42. Consolidation được hỗ trợ.
43. Consolidated memory giữ provenance.
44. Consolidation có thể lossy.
45. Original records có thể preserve.
46. Contradictions được detect hoặc preserve.
47. Supersession được hỗ trợ.
48. History không bị silently rewritten.
49. Consolidation model có identity/version.
50. Consolidation configuration có thể record.
51. Sensitive consolidation có thể require review.
52. Exact memory retrieval được hỗ trợ.
53. Semantic retrieval được hỗ trợ.
54. Temporal retrieval được hỗ trợ.
55. Scope filtering được hỗ trợ.
56. Sensitivity filtering được enforce.
57. Recency có thể influence retrieval.
58. Importance có thể influence retrieval.
59. Relevance có thể influence retrieval.
60. Conflict-aware retrieval được hỗ trợ.
61. Forgetting là explicit lifecycle operation.
62. User deletion được hỗ trợ theo policy.
63. Scoped deletion được hỗ trợ.
64. Tombstones có thể được sử dụng.
65. Derived data invalidation được định nghĩa.
66. Embedding entries phải invalidate khi required.
67. Caches phải invalidate khi required.
68. Distributed deletion integrate 502.
69. Backup retention semantics explicit.
70. Compliance policy không hard-code vào language core.
71. Parameter learning khác memory learning.
72. External memory có thể update mà không retrain model.
73. Fine-tuning là separate operation.
74. Preference learning được hỗ trợ.
75. Memory không tự thay đổi executable policy.
76. Policy authority remains explicit.
77. Feedback có provenance.
78. User corrections có thể supersede inferred memory.
79. Memory reversal được hỗ trợ.
80. Important mutations có audit trail.
81. Project memory namespace được hỗ trợ.
82. Project history được lưu.
83. Semantic project metadata integrate 446/486.
84. Agent có thể recover project task state.
85. Architecture decisions có provenance.
86. Stale decisions có version/status.
87. Task completion có explicit status.
88. Task dependencies có thể được lưu.
89. Project memory integrate knowledge graph 512.
90. Project memory integrate context engine 514.
91. Agent private memory được hỗ trợ.
92. Shared memory cần explicit authority.
93. Memory delegation được hỗ trợ.
94. Concurrent writes có version/CAS/transaction semantics.
95. Distributed memory integrate 502.
96. Memory consistency policy explicit.
97. Memory changes có thể publish thành events.
98. AI introspection được hỗ trợ.
99. Memory access không vượt capability scope.
100. **Axiom Memory Engine phải cung cấp long-term memory có provenance, scope, version, confidence, lifecycle, consolidation và forgetting semantics; memory có thể giúp agent duy trì continuity và personalization nhưng không được tự biến thành policy authority, không được che giấu nguồn gốc, và không được âm thầm thay đổi hành vi thực thi của agent.**

**BOOTSTRAP-515 hoàn tất / LOCKED.**

---

# BOOTSTRAP-516 — AI EVALUATION, TESTING, BENCHMARKING, MODEL QUALITY, AGENT EVAL, SAFETY EVAL & REPRODUCIBLE AI EXPERIMENTS

**Trạng thái: COMPLETED / LOCKED**

516 tạo một framework thống nhất để kiểm thử AI/Agent. Điểm cốt lõi:

```text
AI Output
   ≠
Compiler Correctness
   ≠
Benchmark Score
   ≠
Safety Guarantee
```

Không dùng một “AI score” duy nhất để đại diện cho chất lượng.

```text id="516arch"
                   AI System
                       │
        ┌──────────────┼──────────────┐
        ↓              ↓              ↓
     Model Eval     Agent Eval      Tool Eval
        │              │              │
        └──────────────┼──────────────┘
                       ↓
                    Dataset
                       ↓
                  Evaluation
                       ↓
             Metrics / Evidence
                       ↓
              Regression Analysis
                       ↓
             Reproducible Report
```

---

## 516.1 — Evaluation

Evaluation là controlled measurement của AI behavior.

## 516.2 — Test

Test xác minh expected behavior cụ thể.

## 516.3 — Benchmark

Benchmark đo performance/quality trên workload xác định.

## 516.4 — Safety evaluation

Safety evaluation kiểm tra violation scenarios.

## 516.5 — No aggregate score

Không có universal AI quality score.

## 516.6 — Evaluation case

```text id="evalcase"
EvaluationCase {
    input
    expected
    constraints
    evaluator
    metadata
}
```

## 516.7 — Dataset

Dataset có version/hash.

## 516.8 — Dataset provenance

Nguồn dữ liệu được lưu.

## 516.9 — Split

Dataset có thể chia:

- train;
- validation;
- test;
- challenge.

## 516.10 — Leakage

Train/test contamination phải được detect khi possible.

---

# MODEL EVALUATION

## 516.11 — Accuracy

Task-specific correctness metric.

## 516.12 — Exact match

String/structured exact matching.

## 516.13 — Structured evaluation

JSON/schema/AST/result comparison.

## 516.14 — Semantic evaluation

Embedding/model/human-based semantic comparison.

## 516.15 — Human evaluation

Human labels có annotator metadata.

## 516.16 — Pairwise evaluation

Có thể compare outputs without turning result into universal ranking.

## 516.17 — Rubric

Task-specific rubric được versioned.

## 516.18 — LLM judge

LLM-as-judge là evaluator có uncertainty/bias limitations.

## 516.19 — Reference answer

Reference có provenance/version.

## 516.20 — Multiple references

Multiple acceptable outputs được hỗ trợ.

---

# AGENT EVALUATION

## 516.21 — Agent trajectory

Agent trajectory:

```text
Goal
→ Context
→ Action
→ Observation
→ Action
→ Result
```

## 516.22 — Tool correctness

Tool call schema/effects được kiểm tra.

## 516.23 — Plan quality

Plan properties có thể measure:

- unnecessary steps;
- failures;
- latency;
- resource usage.

Không biến chúng thành universal score.

## 516.24 — Completion

Task completion có explicit success criteria.

## 516.25 — Partial success

Partial completion được biểu diễn.

## 516.26 — Failure attribution

Failure có category:

```text
model
retrieval
tool
environment
policy
data
timeout
```

## 516.27 — Tool misuse

Invalid/unauthorized tool calls được record.

## 516.28 — Recovery

Agent recovery after failure được test.

## 516.29 — Replanning

Replanning scenarios được test.

## 516.30 — Long-horizon

Multi-step tasks được hỗ trợ.

---

# SAFETY EVALUATION

## 516.31 — Policy test

Policy compliance được test.

## 516.32 — Capability test

Agent không được vượt capability boundary.

## 516.33 — Prompt injection test

Injected instructions trong external data được test.

## 516.34 — Tool injection test

Malicious tool results được test.

## 516.35 — Data exfiltration test

Protected data transfer scenarios.

## 516.36 — Sandbox escape test

Sandbox isolation được test.

## 516.37 — Resource exhaustion

Memory/CPU/tool-call exhaustion scenarios.

## 516.38 — Privilege escalation

Unauthorized capability acquisition tests.

## 516.39 — Secret handling

Secret exposure tests.

## 516.40 — Audit completeness

Required action provenance được kiểm tra.

---

# REPRODUCIBILITY

## 516.41 — Evaluation identity

Evaluation artifact identity gồm:

```text id="evidentity"
model
model_revision
dataset
dataset_revision
prompt
tools
tool_versions
compiler
runtime
target
configuration
```

## 516.42 — Random seed

Seed được lưu khi deterministic/randomized evaluation sử dụng seed.

## 516.43 — Temperature

Generation parameters được lưu.

## 516.44 — Sampling

Sampling strategy/version được lưu.

## 516.45 — Hardware

Hardware/backend được record.

## 516.46 — Environment

Relevant environment được record.

## 516.47 — Nondeterminism

Known nondeterminism được annotate.

## 516.48 — Re-run

Evaluation có thể replay khi artifacts còn available.

## 516.49 — Artifact retention

Input/output/evaluator artifacts retention explicit.

## 516.50 — Comparison

Regression comparison chỉ meaningful khi configurations comparable.

---

# PERFORMANCE

## 516.51 — Latency

Record:

- first-token latency;
- total latency;
- tool latency;
- retrieval latency.

## 516.52 — Throughput

Requests/tokens/samples per second.

## 516.53 — Memory

Peak/live allocation.

## 516.54 — GPU

GPU memory/utilization/kernel metrics khi available.

## 516.55 — Cost

Resource/cost metadata nếu environment expose được.

## 516.56 — Batch

Batch size recorded.

## 516.57 — Concurrency

Concurrency level recorded.

## 516.58 — Cold start

Cold/warm distinction.

## 516.59 — Cache

Cache state recorded.

## 516.60 — Percentiles

Latency distributions support percentile analysis.

---

# REGRESSION

## 516.61 — Baseline

Baseline evaluation artifact.

## 516.62 — Regression

Difference relative to baseline.

## 516.63 — Improvement

Improvement có thể report nhưng không universal rank.

## 516.64 — Statistical uncertainty

Variance/confidence intervals khi methodology supports.

## 516.65 — Repeated runs

Repeated trials được hỗ trợ.

## 516.66 — Seed sweep

Multiple seeds được hỗ trợ.

## 516.67 — Dataset drift

Changed dataset/version được detect.

## 516.68 — Model drift

Model revision changes được detect.

## 516.69 — Tool drift

Tool/version changes được detect.

## 516.70 — Environment drift

Hardware/runtime changes được record.

---

# FUZZING / ADVERSARIAL

## 516.71 — Input fuzzing

AI input mutation được hỗ trợ.

## 516.72 — Prompt mutation

Prompt variants.

## 516.73 — Tool-result mutation

Malformed/malicious results.

## 516.74 — Retrieval poisoning

Poisoned knowledge cases.

## 516.75 — Long-context stress

Context overflow/truncation scenarios.

## 516.76 — Memory corruption

Memory store consistency tests.

## 516.77 — Tool timeout

Timeout/failure injection.

## 516.78 — Network fault

Network 454/501 faults.

## 516.79 — Storage fault

Storage 455/502 faults.

## 516.80 — Deterministic replay

Fault scenarios replayable.

---

# AI-SPECIFIC QUALITY

## 516.81 — Hallucination evaluation

Factuality/grounding tests are task-specific.

## 516.82 — Grounding

Claims can be checked against evidence.

## 516.83 — Citation correctness

Citation points must map to actual evidence.

## 516.84 — Retrieval quality

Recall/precision-like metrics can be measured.

## 516.85 — Context efficiency

Useful information per token can be measured.

## 516.86 — Memory quality

Memory retrieval/consolidation can be evaluated.

## 516.87 — Agent reliability

Repeated task success/failure distribution.

## 516.88 — Calibration

Confidence calibration can be measured where model emits meaningful confidence.

## 516.89 — Abstention

Agent can be evaluated on whether it appropriately declines unsupported claims/actions.

## 516.90 — Uncertainty

Evaluator preserves uncertainty rather than forcing binary truth where inappropriate.

---

# AI TOOLING

## 516.91 — Evaluation CLI

```text
axiom ai eval
axiom ai benchmark
axiom ai replay
axiom ai compare
axiom ai report
```

## 516.92 — Machine-readable report

Structured JSON artifact.

## 516.93 — Human report

Readable HTML/Markdown/text.

## 516.94 — Semantic metadata

Evaluation references 446 metadata.

## 516.95 — Build integration

Evaluation graph integrates 487.

## 516.96 — Profiling

Runtime performance integrates 481/476.

## 516.97 — Coverage

Agent/tool tests integrate 477.

## 516.98 — Sanitizer

Native tool/runtime testing integrates 480.

## 516.99 — AI introspection

Queries:

```text
eval()
case()
dataset()
trajectory()
failure()
regression()
reproduction()
```

---

# 516.100 — HARD INVARIANTS

1. Evaluation khác test.
2. Evaluation khác benchmark.
3. Safety evaluation khác functional correctness.
4. Không có universal AI score.
5. Evaluation case có structured identity.
6. Dataset có version/hash.
7. Dataset provenance được lưu.
8. Dataset splits được hỗ trợ.
9. Leakage detection được hỗ trợ.
10. Exact-match evaluation được hỗ trợ.
11. Structured evaluation được hỗ trợ.
12. Semantic evaluation được hỗ trợ.
13. Human evaluation được hỗ trợ.
14. Pairwise evaluation được hỗ trợ.
15. Rubric được version.
16. LLM judge có limitations metadata.
17. Reference answer có provenance.
18. Multiple valid references được hỗ trợ.
19. Agent trajectory được record.
20. Tool correctness được kiểm tra.
21. Plan behavior có thể đo.
22. Task completion có explicit criteria.
23. Partial success được biểu diễn.
24. Failure attribution được hỗ trợ.
25. Tool misuse được record.
26. Recovery được test.
27. Replanning được test.
28. Long-horizon tasks được hỗ trợ.
29. Policy compliance được test.
30. Capability boundary được test.
31. Prompt injection được test.
32. Tool injection được test.
33. Data exfiltration được test.
34. Sandbox isolation được test.
35. Resource exhaustion được test.
36. Privilege escalation được test.
37. Secret handling được test.
38. Audit completeness được test.
39. Evaluation identity đầy đủ.
40. Model revision được record.
41. Dataset revision được record.
42. Prompt/configuration được record.
43. Tool versions được record.
44. Compiler/runtime được record.
45. Target được record.
46. Random seed được record khi applicable.
47. Generation parameters được record.
48. Sampling strategy được record.
49. Hardware/backend được record.
50. Nondeterminism được annotate.
51. Evaluation replay được hỗ trợ.
52. Artifact retention policy explicit.
53. Comparisons require comparable configurations.
54. First-token latency được đo.
55. Total latency được đo.
56. Tool/retrieval latency có thể đo.
57. Throughput được đo.
58. Memory usage được đo.
59. GPU metrics có thể đo.
60. Resource cost có thể record.
61. Batch size được record.
62. Concurrency được record.
63. Cold/warm state được distinguish.
64. Cache state được record.
65. Latency distributions được hỗ trợ.
66. Baselines được hỗ trợ.
67. Regression được định nghĩa relative baseline.
68. Variance được report.
69. Repeated runs được hỗ trợ.
70. Seed sweeps được hỗ trợ.
71. Dataset drift được detect.
72. Model drift được detect.
73. Tool drift được detect.
74. Environment drift được detect.
75. Input fuzzing được hỗ trợ.
76. Prompt mutation được hỗ trợ.
77. Tool-result mutation được hỗ trợ.
78. Retrieval poisoning tests được hỗ trợ.
79. Long-context stress tests được hỗ trợ.
80. Memory consistency tests được hỗ trợ.
81. Tool timeout fault injection được hỗ trợ.
82. Network fault injection được hỗ trợ.
83. Storage fault injection được hỗ trợ.
84. Deterministic replay được hỗ trợ.
85. Grounding evaluation được hỗ trợ.
86. Citation correctness được kiểm tra.
87. Retrieval quality có thể đo.
88. Context efficiency có thể đo.
89. Memory quality có thể đo.
90. Agent reliability có thể đo.
91. Calibration có thể đo khi meaningful.
92. Abstention behavior có thể đánh giá.
93. Uncertainty không bị ép thành binary khi methodology không phù hợp.
94. Evaluation CLI được hỗ trợ.
95. Machine-readable report được hỗ trợ.
96. Human-readable report được hỗ trợ.
97. Evaluation integrate semantic metadata.
98. Evaluation integrate build/profiling/coverage/sanitizer systems.
99. Evaluation artifact có provenance đầy đủ.
100. **Axiom AI Evaluation phải biến mọi tuyên bố về chất lượng, độ tin cậy, hiệu năng hoặc safety của model/agent/tool thành các phép đo có dataset, configuration, provenance và uncertainty rõ ràng; không được biến một benchmark hay một con số đơn lẻ thành “chất lượng AI tổng thể”.**

**BOOTSTRAP-516 hoàn tất / LOCKED.**

---

## Tiến độ mới

```text
BOOTSTRAP-511  AI Agent Foundation                         LOCKED
BOOTSTRAP-512  Knowledge Engine / RAG                     LOCKED
BOOTSTRAP-513  AI Tool / Plugin ABI                       LOCKED
BOOTSTRAP-514  AI Context Engine                          LOCKED
BOOTSTRAP-515  AI Memory / Personalization                LOCKED
BOOTSTRAP-516  AI Evaluation / Testing / Benchmarking      LOCKED
```

**Task kế tiếp: `BOOTSTRAP-517 — AI MODEL SERVING, INFERENCE SERVER, BATCHING, KV-CACHE POOL, MULTI-MODEL SCHEDULING, GPU SHARING & PRODUCTION AI DEPLOYMENT`.**