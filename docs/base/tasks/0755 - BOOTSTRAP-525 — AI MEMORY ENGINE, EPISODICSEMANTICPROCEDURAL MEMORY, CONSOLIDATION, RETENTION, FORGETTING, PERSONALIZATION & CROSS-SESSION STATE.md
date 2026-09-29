# BOOTSTRAP-525 — AI MEMORY ENGINE, EPISODIC/SEMANTIC/PROCEDURAL MEMORY, CONSOLIDATION, RETENTION, FORGETTING, PERSONALIZATION & CROSS-SESSION STATE

**Trạng thái: COMPLETED / LOCKED**

525 hoàn thiện tầng **Memory Engine** cho 511/512/515/524. Mục tiêu là biến memory thành một hệ thống state có identity, provenance, lifecycle, access control và semantics rõ ràng — không biến memory thành một “database bí ẩn” mà model tự ý ghi/đọc.

```text id="525arch"
                    Agent / Application
                           │
                    Memory Interface
                           │
          ┌────────────────┼────────────────┐
          ↓                ↓                ↓
      Working          Episodic         Semantic
       Memory           Memory           Memory
          │                │                │
          └────────────────┼────────────────┘
                           ↓
                     Memory Engine
                           │
              ┌────────────┼────────────┐
              ↓            ↓            ↓
         Retrieval     Consolidation   Policy
              │            │            │
              └────────────┼────────────┘
                           ↓
                    Persistent Store
                           │
                  Vector / KV / Graph
                           │
                         512
```

---

# 525.1 — Memory ≠ Context

Memory là information được giữ qua thời gian.

Context là snapshot được đưa vào một model execution.

```text
Memory
   ↓ selection
Context
   ↓ model execution
Output
   ↓ optional write
Memory
```

## 525.2 — Memory item

```text
MemoryItem {
    id
    type
    content
    source
    owner
    scope
    timestamp
    confidence
    importance
    sensitivity
    provenance
    expiration
}
```

## 525.3 — Memory identity

Mỗi memory item có stable `MemoryId`.

## 525.4 — Memory version

Mutation tạo version mới hoặc revision rõ ràng.

## 525.5 — Provenance

Memory phải reference nguồn tạo ra nó.

## 525.6 — Confidence

Confidence là metadata, không phải proof.

## 525.7 — Importance

Importance là policy/application signal.

## 525.8 — Sensitivity

Memory có thể mang sensitivity label.

## 525.9 — Scope

Scope có thể:

```text
Process
Agent
Session
User
Project
Workspace
Tenant
Global
```

## 525.10 — Isolation

Scope boundaries phải được enforce.

---

# MEMORY TYPES

## 525.11 — Working Memory

Thông tin ngắn hạn phục vụ task hiện tại.

## 525.12 — Episodic Memory

Record về sự kiện/trải nghiệm:

```text
event
time
participants
context
result
```

## 525.13 — Semantic Memory

Facts/knowledge đã được trừu tượng hóa.

## 525.14 — Procedural Memory

Knowledge về cách thực hiện task/workflow.

## 525.15 — Preference Memory

User/application preferences khi được phép lưu.

## 525.16 — Resource Memory

References tới files, models, tools, projects hoặc external resources.

## 525.17 — Derived Memory

Memory được suy ra từ các memory khác.

## 525.18 — Generated Memory

Memory do model tạo ra.

## 525.19 — Observed Memory

Memory dựa trên directly observed data.

## 525.20 — Explicit Memory

Memory được user/application yêu cầu lưu.

---

# MEMORY WRITE

## 525.21 — Explicit write

Application có thể gọi:

```text
memory.store(item)
```

## 525.22 — Automatic write

Agent có thể đề xuất automatic memory write nhưng policy quyết định có commit hay không.

## 525.23 — Write policy

```text
Disabled
ExplicitOnly
Suggest
Automatic
```

## 525.24 — Candidate memory

Model-generated memory trước khi commit là `MemoryCandidate`.

## 525.25 — Validation

Candidate có thể require validation.

## 525.26 — Duplicate detection

Memory engine có thể detect duplicate.

## 525.27 — Conflict detection

Conflicting memories được distinguish.

## 525.28 — Update

Memory update không được silently overwrite provenance.

## 525.29 — Merge

Merge tạo provenance chain.

## 525.30 — Atomic write

Memory write có transactional semantics khi backend hỗ trợ.

---

# RETRIEVAL

## 525.31 — Exact retrieval

ID/key lookup.

## 525.32 — Semantic retrieval

Embedding retrieval qua 512.

## 525.33 — Lexical retrieval

Keyword/full-text retrieval.

## 525.34 — Graph retrieval

Entity/relation traversal.

## 525.35 — Hybrid retrieval

Có thể combine nhiều phương pháp.

## 525.36 — Scope filtering

Retrieval phải filter scope trước khi expose data.

## 525.37 — Access control

ACL/capability được áp dụng.

## 525.38 — Freshness

Memory có freshness metadata.

## 525.39 — Expiration

Memory có thể expire.

## 525.40 — Ranking

Ranking signals có thể gồm:

- relevance;
- recency;
- importance;
- confidence;
- frequency;
- task relevance.

Không có universal weighting.

---

# CONSOLIDATION

## 525.41 — Consolidation

Nhiều episodic memories có thể được consolidate thành semantic memory.

```text
Episodes
   ↓
Cluster
   ↓
Summarize / Extract
   ↓
Semantic Memory
```

## 525.42 — Source preservation

Semantic memory phải reference episodes nguồn.

## 525.43 — Conflict handling

Conflicting episodes không được silently collapse.

## 525.44 — Temporal facts

Facts có thể có validity interval.

## 525.45 — Versioned facts

Fact thay đổi theo thời gian phải preserve history.

## 525.46 — Confidence propagation

Derived confidence phải identify derivation method.

## 525.47 — Loss metadata

Consolidation có thể lose detail và phải record.

## 525.48 — Reversible consolidation

Original episodic records có thể giữ lại.

## 525.49 — Rebuild

Semantic memory có thể rebuild từ source records.

## 525.50 — Determinism

Deterministic consolidation có thể replay.

---

# FORGETTING

## 525.51 — Explicit deletion

User/application có thể delete memory.

## 525.52 — Expiration

TTL-based expiration.

## 525.53 — Retention policy

Retention policy explicit.

## 525.54 — Forgetting

Forgetting không chỉ là xoá khỏi vector index.

## 525.55 — Derived data

Deletion policy phải xác định xử lý:

- embeddings;
- summaries;
- graph nodes;
- caches;
- derived memories.

## 525.56 — Tombstone

Distributed memory backend có thể dùng tombstone.

## 525.57 — Replication

Delete phải propagate theo backend consistency semantics.

## 525.58 — Backup

Retention/deletion semantics phải address backups.

## 525.59 — Cache

Deleted memory không được tiếp tục được serve từ stale cache ngoài policy.

## 525.60 — Audit

Sensitive deletion có thể audit.

---

# PERSONALIZATION

## 525.61 — Preference

Preference là explicit memory category.

## 525.62 — Preference provenance

Preference reference nguồn.

## 525.63 — User control

User/application có thể inspect/edit/delete allowed memories.

## 525.64 — Session override

Temporary preference có thể override persistent preference.

## 525.65 — No silent inference

Model-generated assumption không tự động trở thành permanent preference.

## 525.66 — Preference confidence

Inferred preference có confidence/evidence.

## 525.67 — Conflict

New preference có thể conflict với old preference.

## 525.68 — Resolution

Resolution policy explicit.

## 525.69 — Scope

Preference scope explicit.

## 525.70 — Isolation

User memories không leak sang user khác.

---

# PROCEDURAL MEMORY

## 525.71 — Procedure

Procedure memory có thể lưu:

```text
Goal
Preconditions
Steps
Tools
Expected outputs
Failure handling
```

## 525.72 — Tool references

Procedures reference tool identity/version.

## 525.73 — Workflow version

Workflow changes tạo version.

## 525.74 — Execution evidence

Procedure memory có thể reference successful/failed executions.

## 525.75 — No automatic trust

Successful execution không tự động chứng minh procedure luôn đúng.

## 525.76 — Safety

Procedure có dangerous actions phải integrate 522/490.

## 525.77 — Dry-run

Procedure testing hỗ trợ dry-run.

## 525.78 — Parameterization

Procedures có thể có typed parameters.

## 525.79 — Preconditions

Procedures có explicit preconditions.

## 525.80 — Postconditions

Procedures có explicit postconditions.

---

# MEMORY CONSISTENCY

## 525.81 — Stale memory

Memory có thể stale.

## 525.82 — Freshness check

Application có thể require freshness threshold.

## 525.83 — Conflict set

Conflicting facts có thể coexist.

## 525.84 — Authority

Source authority metadata được preserve.

## 525.85 — Truth ≠ Memory

Memory existence không chứng minh fact correctness.

## 525.86 — Verification

Critical memories có thể require external verification.

## 525.87 — Verification status

```text
Unverified
Observed
Verified
Contradicted
Unknown
```

## 525.88 — Temporal validity

Fact validity có start/end.

## 525.89 — Source replacement

Updated source có thể supersede old memory.

## 525.90 — Historical queries

Engine hỗ trợ query “as of time T”.

---

# MEMORY SECURITY

## 525.91 — Access control

Memory store phải enforce ACL/capability.

## 525.92 — Encryption

Backend có thể encrypt sensitive memories.

## 525.93 — Secret memory

Secrets phải distinguish khỏi ordinary memory.

## 525.94 — Tool access

Tool không tự động có quyền đọc all memory.

## 525.95 — Agent isolation

Agents không share memory ngoài explicit scope.

## 525.96 — Prompt injection

Memory content không tự động trở thành instruction.

## 525.97 — Memory poisoning

Untrusted memory writes có provenance.

## 525.98 — Provenance validation

Memory ingestion có thể require trusted source.

## 525.99 — Exfiltration

Memory → tool/network transfer phải qua capability/policy.

## 525.100 — Sensitive retrieval

Sensitive retrieval có thể require explicit authorization.

---

# MEMORY PERFORMANCE

## 525.101 — Storage backends

Có thể dùng:

- in-memory;
- KV;
- relational;
- vector;
- graph;
- mmap;
- distributed.

## 525.102 — Tiering

Memory có thể tier:

```text
Hot
Warm
Cold
Archive
```

## 525.103 — Cache

Frequently accessed memory có thể cache.

## 525.104 — Prefetch

Task-aware prefetch có thể được hỗ trợ.

## 525.105 — Batch retrieval

Multiple retrieval requests có thể batch.

## 525.106 — Streaming

Large memories/results có thể stream.

## 525.107 — Compression

Memory representation có thể compress.

## 525.108 — Index rebuild

Indexes có thể rebuild từ canonical store.

## 525.109 — Replication

Distributed memory có thể replicate.

## 525.110 — Failure recovery

Memory backend có recovery semantics.

---

# AI INTROSPECTION

## 525.111 — Why retrieved?

```text
why_retrieved(memory_id)
```

## 525.112 — Why stored?

```text
why_stored(memory_id)
```

## 525.113 — Provenance

```text
memory_provenance(memory_id)
```

## 525.114 — Conflicts

```text
memory_conflicts(memory_id)
```

## 525.115 — Freshness

```text
memory_freshness(memory_id)
```

## 525.116 — Scope

```text
memory_scope(memory_id)
```

## 525.117 — Deletion impact

```text
memory_delete_impact(memory_id)
```

## 525.118 — Consolidation lineage

```text
memory_sources(memory_id)
memory_derived(memory_id)
```

## 525.119 — Context integration

Memory item → context item provenance từ 524.

## 525.120 — Machine-readable

Tất cả memory metadata queryable.

---

# 525.121 — HARD INVARIANTS

1. Memory khác context.
2. Memory item có identity.
3. Memory có version/revision semantics.
4. Provenance được preserve.
5. Confidence là metadata.
6. Importance là policy signal.
7. Sensitivity được hỗ trợ.
8. Scope được hỗ trợ.
9. Scope isolation được enforce.
10. Working memory được hỗ trợ.
11. Episodic memory được hỗ trợ.
12. Semantic memory được hỗ trợ.
13. Procedural memory được hỗ trợ.
14. Preference memory được hỗ trợ.
15. Resource memory được hỗ trợ.
16. Derived memory được distinguish.
17. Generated memory được distinguish.
18. Observed memory được distinguish.
19. Explicit memory được distinguish.
20. Explicit write được hỗ trợ.
21. Automatic write là policy.
22. Candidate memory được distinguish.
23. Candidate có thể validate.
24. Duplicate detection được hỗ trợ.
25. Conflict detection được hỗ trợ.
26. Update không được mất provenance.
27. Merge preserve lineage.
28. Atomic write được hỗ trợ.
29. Exact retrieval được hỗ trợ.
30. Semantic retrieval được hỗ trợ.
31. Lexical retrieval được hỗ trợ.
32. Graph retrieval được hỗ trợ.
33. Hybrid retrieval được hỗ trợ.
34. Scope filtering trước exposure.
35. ACL/capability được enforce.
36. Freshness metadata được hỗ trợ.
37. Expiration được hỗ trợ.
38. Ranking signals explicit.
39. Không có universal ranking weights.
40. Consolidation được hỗ trợ.
41. Consolidation preserve source lineage.
42. Conflicting episodes không silently collapse.
43. Temporal validity được hỗ trợ.
44. Versioned facts được hỗ trợ.
45. Derived confidence có provenance.
46. Information loss có thể được record.
47. Source records có thể được giữ.
48. Semantic memory có thể rebuild.
49. Deterministic consolidation có thể replay.
50. Explicit deletion được hỗ trợ.
51. TTL được hỗ trợ.
52. Retention policy explicit.
53. Forgetting xử lý derived artifacts.
54. Tombstones được hỗ trợ khi cần.
55. Replicated deletion semantics explicit.
56. Backup deletion semantics được định nghĩa.
57. Deleted memory không được serve từ stale cache ngoài policy.
58. Sensitive deletion có thể audit.
59. Preference là explicit category.
60. Preference có provenance.
61. User/application control được hỗ trợ.
62. Session override được hỗ trợ.
63. Inferred preference không tự động trở thành permanent memory.
64. Inferred preference có evidence.
65. Preference conflict được detect.
66. Preference resolution explicit.
67. Preference scope explicit.
68. Cross-user isolation được enforce.
69. Procedural memory được hỗ trợ.
70. Procedure có goal.
71. Procedure có preconditions.
72. Procedure có steps.
73. Procedure có tool identity.
74. Procedure có expected outputs.
75. Procedure có failure semantics.
76. Procedure versioned.
77. Execution evidence có thể attach.
78. Successful execution không phải universal proof.
79. Dangerous procedure integrate safety/security.
80. Dry-run được hỗ trợ.
81. Procedure parameters có thể typed.
82. Memory có thể stale.
83. Freshness requirements được hỗ trợ.
84. Conflicting facts được preserve.
85. Authority metadata được preserve.
86. Memory không tự chứng minh truth.
87. Verification được hỗ trợ.
88. Verification status explicit.
89. Temporal queries được hỗ trợ.
90. Source replacement được hỗ trợ.
91. ACL được enforce.
92. Sensitive memory encryption được hỗ trợ.
93. Secrets được distinguish.
94. Tool memory access explicit.
95. Agent memory isolation explicit.
96. Memory instructions không gain authority.
97. Memory poisoning provenance được preserve.
98. Memory ingestion có thể require trusted source.
99. Memory exfiltration qua capability.
100. Sensitive retrieval có thể require authorization.
101. Multiple storage backends được hỗ trợ.
102. Memory tiering được hỗ trợ.
103. Cache được hỗ trợ.
104. Prefetch được hỗ trợ.
105. Batch retrieval được hỗ trợ.
106. Streaming được hỗ trợ.
107. Compression được hỗ trợ.
108. Index rebuild được hỗ trợ.
109. Replication được hỗ trợ.
110. Failure recovery được hỗ trợ.
111. `why_retrieved` được hỗ trợ.
112. `why_stored` được hỗ trợ.
113. Provenance query được hỗ trợ.
114. Conflict query được hỗ trợ.
115. Freshness query được hỗ trợ.
116. Scope query được hỗ trợ.
117. Delete-impact query được hỗ trợ.
118. Consolidation lineage query được hỗ trợ.
119. Memory→context provenance được preserve.
120. **Axiom Memory Engine phải cung cấp memory lâu dài có type, scope, provenance, lifecycle, consistency, security và deletion semantics rõ ràng; model không được tự động biến mọi inference thành memory, memory không được tự động trở thành instruction, và việc “nhớ” phải luôn có thể truy nguyên, kiểm soát và xóa theo policy.**

**BOOTSTRAP-525 hoàn tất / LOCKED.**

---

# BOOTSTRAP-526 — AI AGENT WORKFLOW ENGINE, PLAN GRAPH, STATE MACHINE, HUMAN-IN-THE-LOOP, CHECKPOINT, RECOVERY & LONG-RUNNING AUTONOMOUS EXECUTION

**Trạng thái: COMPLETED / LOCKED**

526 nâng 511 từ một Agent Runtime thành **workflow execution engine** đủ mạnh cho những tác vụ kéo dài hàng giờ/ngày, có nhiều bước, nhiều agent, tool calls, checkpoint và recovery.

Đây là tầng đặc biệt quan trọng đối với mục tiêu Axiom: agent có thể tự nghiên cứu → lập kế hoạch → thực hiện → kiểm tra → sửa → tiếp tục mà không phải giữ toàn bộ trạng thái trong prompt.

```text id="526arch"
                       Goal
                        │
                  Constraint Set
                        │
                    Plan Graph
                        │
          ┌─────────────┼─────────────┐
          ↓             ↓             ↓
        Step A         Step B        Step C
          │             │             │
        Tool          Agent         Compute
          │             │             │
          └─────────────┼─────────────┘
                        ↓
                    Validation
                        │
              ┌─────────┴─────────┐
              ↓                   ↓
           Success              Failure
              │                   │
              ↓                   ↓
          Checkpoint          Recovery
              │                   │
              └─────────┬─────────┘
                        ↓
                    Next Step
                        │
                 Human Approval
                        │
                       Done
```

---

# 526.1 — Workflow ≠ Agent

Agent là autonomous decision-maker.

Workflow là execution structure.

Một workflow có thể:

- không có AI;
- có một agent;
- có nhiều agents;
- có deterministic tasks;
- có human steps.

## 526.2 — Workflow identity

```text
WorkflowId
Version
DefinitionHash
```

## 526.3 — Execution identity

```text
WorkflowRunId
ParentRunId?
AttemptId
```

## 526.4 — Step identity

Mỗi step có stable logical identity.

## 526.5 — Step attempt

Retry tạo attempt mới, không overwrite history.

## 526.6 — State machine

Workflow states:

```text
Created
Running
Waiting
Paused
Blocked
Succeeded
Failed
Cancelled
Expired
```

## 526.7 — Step states

```text
Pending
Ready
Running
Waiting
Succeeded
Failed
Skipped
Cancelled
```

## 526.8 — Persistent state

Long-running workflow state phải persistent nếu configured.

## 526.9 — In-memory workflow

Short workflow có thể chạy hoàn toàn memory-only.

## 526.10 — Deterministic identity

Run identity không được phụ thuộc randomness khi deterministic mode.

---

# PLAN GRAPH

## 526.11 — DAG

Workflow mặc định dùng DAG khi dependencies acyclic.

## 526.12 — Dependencies

Step dependency explicit.

## 526.13 — Parallel branches

Independent steps có thể chạy parallel.

## 526.14 — Join

Join step chờ dependency conditions.

## 526.15 — Conditional branch

Branch condition explicit.

## 526.16 — Loop

Loops được hỗ trợ nhưng phải có termination/resource policy.

## 526.17 — Dynamic plan

Agent có thể modify plan.

## 526.18 — Plan revision

Plan change tạo revision.

## 526.19 — Plan provenance

Executed step reference plan revision.

## 526.20 — Cycle

Unexpected dependency cycle là validation error.

---

# STEP TYPES

## 526.21 — Compute step

Deterministic/local computation.

## 526.22 — Tool step

External tool call.

## 526.23 — Agent step

Delegated agent execution.

## 526.24 — Human step

Human approval/input.

## 526.25 — Wait step

Wait tới event/deadline.

## 526.26 — Condition step

Evaluate predicate.

## 526.27 — Transform step

Transform data.

## 526.28 — Retrieval step

Query knowledge/memory.

## 526.29 — Validation step

Validate artifact/result.

## 526.30 — Compensation step

Rollback/compensating action.

---

# INPUT/OUTPUT

## 526.31 — Typed input

Step inputs có schema.

## 526.32 — Typed output

Step outputs có schema.

## 526.33 — Artifact reference

Large data dùng artifact references thay vì nhúng vào workflow state.

## 526.34 — Serialization

Persistent state phải serializable.

## 526.35 — Versioning

State schema có version.

## 526.36 — Schema migration

Workflow upgrade có migration.

## 526.37 — Secret values

Secrets không được serialize vào ordinary state.

## 526.38 — Redaction

State export có redaction.

## 526.39 — Provenance

Output reference producing step.

## 526.40 — Immutable outputs

Completed step outputs immutable theo mặc định.

---

# CHECKPOINT

## 526.41 — Checkpoint

Workflow có thể checkpoint.

## 526.42 — Checkpoint contents

Có thể chứa:

```text
workflow state
plan revision
completed steps
outputs
pending steps
memory references
tool state references
policy state
```

## 526.43 — Atomic checkpoint

Checkpoint write phải atomic.

## 526.44 — Checkpoint identity

```text
CheckpointId
RunId
Sequence
StateHash
```

## 526.45 — Recovery

Restart từ latest valid checkpoint.

## 526.46 — Corrupt checkpoint

Corrupt checkpoint không được restore silently.

## 526.47 — Checkpoint retention

Retention policy explicit.

## 526.48 — Incremental checkpoint

Chỉ changed state có thể checkpoint.

## 526.49 — Full checkpoint

Full snapshot được hỗ trợ.

## 526.50 — Remote checkpoint

Checkpoint có thể lưu remote storage nếu capability cho phép.

---

# RETRY & RECOVERY

## 526.51 — Retry policy

```text
None
Fixed
Exponential
ExponentialJitter
Custom
```

## 526.52 — Retryable errors

Error classification explicit.

## 526.53 — Non-retryable

Permanent failure không retry vô hạn.

## 526.54 — Retry budget

Retry count/time budget.

## 526.55 — Idempotency

Side-effecting step cần idempotency strategy nếu retry.

## 526.56 — Idempotency key

External operations có thể dùng stable key.

## 526.57 — Duplicate execution

Duplicate side effect phải được detect/mitigate khi provider hỗ trợ.

## 526.58 — Compensation

Non-idempotent operations có compensation.

## 526.59 — Partial failure

Workflow có thể finish partially.

## 526.60 — Recovery policy

```text
Retry
Compensate
Skip
Pause
Fail
Escalate
```

---

# HUMAN-IN-THE-LOOP

## 526.61 — Approval step

Human approval là first-class step.

## 526.62 — Approval token

Approval tạo token/reference.

## 526.63 — Scope

Approval chỉ authorize declared action scope.

## 526.64 — Expiration

Approval có expiration.

## 526.65 — Reuse

Approval token không được reuse ngoài declared scope.

## 526.66 — Rejection

Human rejection là explicit state.

## 526.67 — Request clarification

Workflow có thể pause để hỏi human.

## 526.68 — Timeout

Approval timeout policy explicit.

## 526.69 — Audit

Approval event được audit.

## 526.70 — Identity

Human actor identity được record khi platform hỗ trợ.

---

# AGENT ORCHESTRATION

## 526.71 — Agent pool

Multiple agents có thể được orchestrate.

## 526.72 — Role

Agent role/capability explicit.

## 526.73 — Delegation

Parent agent delegates bounded task.

## 526.74 — Shared context

Shared context phải explicit.

## 526.75 — Shared memory

Shared memory scope explicit.

## 526.76 — Agent communication

Channel/message integration 472.

## 526.77 — Agent supervision

Supervisor có thể monitor child agent.

## 526.78 — Child failure

Failure policy explicit.

## 526.79 — Cancellation

Parent cancellation propagate theo declared semantics.

## 526.80 — Budget propagation

Child agent nhận bounded resource budget.

---

# LONG-RUNNING EXECUTION

## 526.81 — Pause

Workflow có thể pause.

## 526.82 — Resume

Resume từ checkpoint.

## 526.83 — Process restart

Workflow không phụ thuộc process lifetime nếu persistent.

## 526.84 — Machine restart

Persistent workflow có thể resume sau machine restart khi backend đảm bảo durability.

## 526.85 — Lease

Workers có execution lease.

## 526.86 — Worker crash

Expired lease cho phép recovery.

## 526.87 — Duplicate workers

Concurrent execution protection.

## 526.88 — Distributed execution

Workflow có thể chạy trên nhiều workers.

## 526.89 — Scheduling

Integrate 471.

## 526.90 — Deadline

Integrate 474.

---

# EVENT-DRIVEN WORKFLOW

## 526.91 — External event

Workflow có thể wait event.

## 526.92 — Event identity

Event có unique identity khi provider hỗ trợ.

## 526.93 — Deduplication

Duplicate events có thể deduplicate.

## 526.94 — Ordering

Event ordering semantics explicit.

## 526.95 — Event timeout

Wait có deadline.

## 526.96 — Event replay

Events có thể replay nếu retained.

## 526.97 — Event sourcing

Optional workflow state reconstruction từ event log.

## 526.98 — Event log

Append-only event history optional.

## 526.99 — Event compaction

Compaction không được mất semantic recovery information.

## 526.100 — Backpressure

Event-driven workflows respect 472/473 backpressure.

---

# SAFETY & SECURITY

## 526.101 — Capability

Workflow steps execute only with declared capabilities.

## 526.102 — Side-effect class

Integrate 511/522.

## 526.103 — Policy check

Sensitive step passes policy before execution.

## 526.104 — Tool trust

Tool trust boundary 490/513.

## 526.105 — Prompt injection

External data cannot rewrite workflow policy.

## 526.106 — State injection

Untrusted tool output cannot mutate privileged workflow state without validation.

## 526.107 — Secret isolation

Secrets scoped to steps that need them.

## 526.108 — Resource limits

CPU/memory/network/tool/token budgets.

## 526.109 — Infinite loop

Loop execution has limits.

## 526.110 — Audit trail

Side effects have audit provenance.

---

# WORKFLOW VERSIONING

## 526.111 — Definition version

Workflow definition versioned.

## 526.112 — Running workflow

Running workflow pins definition revision.

## 526.113 — Upgrade

Live upgrade requires explicit migration.

## 526.114 — State migration

State schema migration validated.

## 526.115 — Compatibility

New definition must declare compatibility with old state.

## 526.116 — Tool version

Tool version/capability changes are recorded.

## 526.117 — Model version

Agent/model version recorded.

## 526.118 — Policy version

Policy version recorded.

## 526.119 — Reproducibility

Run metadata sufficient for replay where external nondeterminism permits.

## 526.120 — Historical inspection

Old runs remain inspectable according to retention policy.

---

# OBSERVABILITY

## 526.121 — Workflow trace

Integrate 481/523.

## 526.122 — Step duration

Each step duration measured.

## 526.123 — Queue delay

Scheduler waiting time measured.

## 526.124 — Tool latency

Tool execution latency measured.

## 526.125 — Model latency

Inference latency measured.

## 526.126 — Token usage

Input/output tokens measured where applicable.

## 526.127 — Cost

External cost metadata may be recorded.

## 526.128 — Failure reason

Structured failure reason.

## 526.129 — Recovery history

Retries/recoveries preserved.

## 526.130 — Critical path

Workflow critical path can be analyzed.

---

# AI INTROSPECTION

## 526.131 — Why waiting?

```text
why_waiting(step)
```

## 526.132 — Why failed?

```text
why_failed(step)
```

## 526.133 — Why retried?

```text
why_retried(step)
```

## 526.134 — Why blocked?

```text
why_blocked(step)
```

## 526.135 — Why plan changed?

```text
why_plan_changed(run)
```

## 526.136 — State query

Current state queryable.

## 526.137 — Dependency query

Step dependency graph queryable.

## 526.138 — Capability query

Required/granted capabilities queryable.

## 526.139 — Provenance query

Step → input → tool/model → output lineage.

## 526.140 — Replay

Run can be replayed in deterministic simulation where possible.

---

# 526.141 — HARD INVARIANTS

1. Workflow khác agent.
2. Workflow có identity.
3. Workflow có version.
4. Workflow definition có hash.
5. Workflow run có identity.
6. Step có logical identity.
7. Retry tạo attempt mới.
8. Workflow state machine explicit.
9. Step state machine explicit.
10. Persistent execution được hỗ trợ.
11. Memory-only execution được hỗ trợ.
12. Deterministic identity được hỗ trợ.
13. DAG workflow được hỗ trợ.
14. Dependencies explicit.
15. Parallel branches được hỗ trợ.
16. Join semantics explicit.
17. Conditional branches được hỗ trợ.
18. Loops được hỗ trợ.
19. Loop termination/resource policy explicit.
20. Dynamic plans được hỗ trợ.
21. Plan revisions được version.
22. Executed steps reference plan revision.
23. Dependency cycles được detect.
24. Compute steps được hỗ trợ.
25. Tool steps được hỗ trợ.
26. Agent steps được hỗ trợ.
27. Human steps được hỗ trợ.
28. Wait steps được hỗ trợ.
29. Condition steps được hỗ trợ.
30. Transform steps được hỗ trợ.
31. Retrieval steps được hỗ trợ.
32. Validation steps được hỗ trợ.
33. Compensation steps được hỗ trợ.
34. Step inputs có schema.
35. Step outputs có schema.
36. Large data dùng artifact reference khi phù hợp.
37. Persistent state serializable.
38. State schema versioned.
39. Secrets không nằm trong ordinary state.
40. State export hỗ trợ redaction.
41. Output có provenance.
42. Completed outputs immutable mặc định.
43. Checkpoint được hỗ trợ.
44. Checkpoint chứa đủ state cần recovery.
45. Checkpoint atomic.
46. Checkpoint có identity.
47. Checkpoint integrity hash được hỗ trợ.
48. Latest valid checkpoint được recover.
49. Corrupt checkpoint không restore silently.
50. Checkpoint retention explicit.
51. Incremental checkpoint được hỗ trợ.
52. Full checkpoint được hỗ trợ.
53. Remote checkpoint được hỗ trợ khi authorized.
54. Retry policy explicit.
55. Retryable errors được classify.
56. Non-retryable errors không retry vô hạn.
57. Retry budget được enforce.
58. Side effects có idempotency semantics.
59. Idempotency key được hỗ trợ.
60. Duplicate execution được detect/mitigate khi possible.
61. Compensation được hỗ trợ.
62. Partial failure được represent.
63. Recovery policy explicit.
64. Human approval là first-class.
65. Approval có token/reference.
66. Approval scope explicit.
67. Approval expiration được hỗ trợ.
68. Approval token không được escalate scope.
69. Human rejection explicit.
70. Clarification step được hỗ trợ.
71. Approval timeout policy explicit.
72. Approval event được audit.
73. Human identity được record khi available.
74. Multiple agents được orchestrate.
75. Agent role/capability explicit.
76. Delegation bounded.
77. Shared context explicit.
78. Shared memory explicit.
79. Agent communication integrate 472.
80. Supervision được hỗ trợ.
81. Child failure policy explicit.
82. Cancellation propagation explicit.
83. Resource budget propagation được hỗ trợ.
84. Workflow pause được hỗ trợ.
85. Resume được hỗ trợ.
86. Process restart recovery được hỗ trợ.
87. Machine restart recovery được hỗ trợ khi durable backend.
88. Worker lease được hỗ trợ.
89. Worker crash recovery được hỗ trợ.
90. Duplicate workers được kiểm soát.
91. Distributed workflow execution được hỗ trợ.
92. Scheduling integrate 471.
93. Deadline integrate 474.
94. External event wait được hỗ trợ.
95. Event identity được hỗ trợ.
96. Event deduplication được hỗ trợ.
97. Event ordering explicit.
98. Event timeout được hỗ trợ.
99. Event replay được hỗ trợ.
100. Event sourcing optional.
101. Event log optional.
102. Event compaction preserve recovery semantics.
103. Backpressure integrate 472/473.
104. Workflow steps dùng declared capabilities.
105. Side-effect classes được enforce.
106. Sensitive steps qua policy.
107. Tool trust boundary được preserve.
108. Prompt injection không alter workflow authority.
109. Untrusted output không mutate privileged state without validation.
110. Secret scope được enforce.
111. CPU/memory/network/token budgets được hỗ trợ.
112. Infinite workflow execution được bounded.
113. Side effects có audit provenance.
114. Workflow definition versioned.
115. Running workflow pins definition revision.
116. Live upgrade explicit.
117. State migration explicit.
118. Compatibility được validate.
119. Tool version được record.
120. Model version được record.
121. Policy version được record.
122. Replay metadata được preserve.
123. Historical runs được inspect theo retention policy.
124. Workflow tracing được hỗ trợ.
125. Step timing được record.
126. Queue delay được record.
127. Tool latency được record.
128. Model latency được record.
129. Token usage được record khi applicable.
130. Cost metadata được hỗ trợ.
131. Failure reasons structured.
132. Recovery history được preserve.
133. Critical-path analysis được hỗ trợ.
134. Waiting reason queryable.
135. Failure reason queryable.
136. Retry reason queryable.
137. Block reason queryable.
138. Plan-change reason queryable.
139. Capability/provenance graph queryable.
140. **Axiom Workflow Engine phải cho phép xây dựng agent/workflow dài hạn có DAG, dynamic planning, parallel execution, checkpoint/recovery, retry/compensation, human approval, multi-agent orchestration và event-driven execution; mọi side effect phải có capability/policy/provenance rõ ràng, còn workflow state phải có thể pause, resume, inspect và recover mà không phụ thuộc vào một process cụ thể.**

**BOOTSTRAP-526 hoàn tất / LOCKED.**

---

## Chuỗi tiếp theo

**`BOOTSTRAP-527 — AI EVALUATION & BENCHMARKING 2.0: MODEL QUALITY, AGENT QUALITY, TASK SUCCESS, REGRESSION, HUMAN EVALUATION, DATASET MANAGEMENT & CONTINUOUS AI EVALUATION`**