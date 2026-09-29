# BOOTSTRAP-539 — AI MODEL/AGENT VERSIONING 2.0, SEMANTIC COMPATIBILITY, MODEL MIGRATION, PROMPT/TOOL/MEMORY SCHEMA EVOLUTION & BACKWARD-COMPATIBLE AI SYSTEM UPGRADES

**Trạng thái: COMPLETED / LOCKED**

539 giải quyết vấn đề production AI thay đổi liên tục nhưng vẫn phải giữ được khả năng **tương thích, migration, rollback và tái lập**.

Điểm quan trọng: **version khác compatibility**. Hai model có thể khác version nhưng vẫn tương thích API; ngược lại, thay đổi nhỏ về tokenizer/schema/tool contract có thể phá compatibility.

```text
              AI System vN
                  │
        ┌─────────┼─────────┐
        ↓         ↓         ↓
      Model     Agent      Tool
        ↓         ↓         ↓
    Tokenizer  Workflow   Schema
        │         │         │
        └─────────┼─────────┘
                  ↓
          Compatibility Engine
                  │
        ┌─────────┼─────────┐
        ↓         ↓         ↓
      Source      API       Runtime
   Compatibility Compatibility Compatibility
        │         │         │
        └─────────┼─────────┘
                  ↓
             Migration Plan
                  ↓
             Validation
                  ↓
          Rollout / Rollback
```

---

## 539.1 — Version ≠ Identity ≠ Compatibility

Phải distinguish:

```text
Identity
Version
Revision
Variant
Compatibility
Migration
Deployment
```

## 539.2 — Immutable version

Published model/agent/tool/schema version không được mutate.

## 539.3 — Revision

Development revision có thể thay đổi trước khi publish.

## 539.4 — Semantic version

AI artifact có thể dùng semantic versioning nhưng compatibility phải được xác định bởi contract thực tế, không chỉ số version.

## 539.5 — Exact pin

Production có thể pin:

```text
ModelId + Version + Variant
```

## 539.6 — Range constraint

Có thể yêu cầu:

```text
>= 3.2 < 4.0
```

nhưng resolver phải kiểm tra capability/contract.

## 539.7 — Compatibility matrix

```text
CompatibilityMatrix {
    Source
    Target
    Dimension
    Result
    Evidence
}
```

---

# 539.8 — COMPATIBILITY DIMENSIONS

Tối thiểu:

```text
API
ABI
Schema
Semantic
Model
Tokenizer
Prompt
Tool
Memory
Workflow
Runtime
Device
Numerical
Performance
Security
Policy
```

## 539.9 — API compatibility

Input/output contract.

## 539.10 — Schema compatibility

Fields/types/requiredness/version.

## 539.11 — Semantic compatibility

Behavioral properties required by consumer.

## 539.12 — Runtime compatibility

Executor/runtime capabilities.

## 539.13 — Device compatibility

CPU/GPU/NPU/backend requirements.

---

# 539.14 — MODEL COMPATIBILITY

Model compatibility phải xét:

- architecture;
- tensor schema;
- dtype;
- tokenizer;
- vocabulary;
- context length;
- input modality;
- output schema;
- KV cache format;
- runtime;
- operator availability.

## 539.15 — Weight compatibility

Checkpoint weights chỉ compatible nếu exact tensor semantics tương thích.

## 539.16 — Architecture identity

Architecture change được ghi nhận độc lập với version number.

## 539.17 — Tokenizer compatibility

Tokenizer identity/version là compatibility input.

## 539.18 — Vocabulary change

Vocabulary mutation có thể invalidate embeddings/output head.

## 539.19 — Special tokens

Thay đổi BOS/EOS/PAD/etc. là compatibility-sensitive.

## 539.20 — Context length

Giảm context capacity là potentially breaking.

---

# 539.21 — AGENT COMPATIBILITY

Agent contract gồm:

```text
Model
Tools
Memory
Workflow
Policy
Context
Output
Capabilities
```

## 539.22 — Tool-set compatibility

Thay tool version phải validate schema/effect.

## 539.23 — Memory compatibility

Memory schema migration required nếu format thay đổi.

## 539.24 — Workflow compatibility

Running workflow phải tiếp tục được deserialize.

## 539.25 — Policy compatibility

Policy change có thể alter allowed actions.

## 539.26 — Capability compatibility

Capability removal có thể invalidate workflow.

---

# 539.27 — TOOL COMPATIBILITY

Tool contract:

```text
ToolId
Version
InputSchema
OutputSchema
Effects
Capabilities
Protocol
```

## 539.28 — Input compatibility

Adding optional field thường có thể compatible.

## 539.29 — Required field

Adding required input là breaking unless migration/default exists.

## 539.30 — Output compatibility

Consumer phải tolerate documented additive output changes.

## 539.31 — Effect compatibility

Changing `Read → Write` là security-sensitive change.

## 539.32 — Capability compatibility

Required capability increase phải explicit.

## 539.33 — Error compatibility

Error taxonomy changes phải versioned.

---

# 539.34 — PROMPT CONTRACT

Prompt/template là versioned artifact.

```text
PromptTemplate {
    PromptId
    Version
    Inputs
    OutputContract
    PolicyRefs
}
```

## 539.35 — Prompt variables

Named variables có schema.

## 539.36 — Prompt role

Role structure phải preserve.

## 539.37 — Template migration

Renamed variables cần migration.

## 539.38 — Prompt output

Prompt changes không được assume semantic equivalence.

## 539.39 — Prompt evaluation

Critical prompt changes có thể trigger 527/537 evaluation.

---

# 539.40 — MEMORY SCHEMA EVOLUTION

```text
MemorySchema {
    SchemaId
    Version
    Fields
    Constraints
}
```

## 539.41 — Additive field

Có thể compatible nếu optional/default.

## 539.42 — Remove field

Potentially breaking.

## 539.43 — Rename field

Requires migration mapping.

## 539.44 — Type change

Requires explicit conversion.

## 539.45 — Semantic field change

Requires semantic migration, không chỉ serialization conversion.

---

# 539.46 — EMBEDDING COMPATIBILITY

Embedding identity:

```text
Model
Version
Dimension
DType
Normalization
Similarity
```

## 539.47 — Dimension change

Index không được assume compatibility.

## 539.48 — Embedding model change

Requires re-embedding hoặc compatibility adapter.

## 539.49 — Similarity change

Distance semantics phải preserved.

## 539.50 — Index migration

Index version được track.

---

# 539.51 — RAG MIGRATION

RAG stack:

```text
Documents
 ↓
Chunking
 ↓
Embedding
 ↓
Index
 ↓
Retriever
 ↓
Reranker
```

Thay đổi từng tầng có thể invalidate downstream artifacts.

## 539.52 — Chunker change

Chunk identity/version.

## 539.53 — Embedding change

Embedding regeneration.

## 539.54 — Index rebuild

Explicit.

## 539.55 — Reranker change

Evaluation may be required.

## 539.56 — Retrieval contract

Top-k/ACL/provenance behavior explicit.

---

# 539.57 — WORKFLOW MIGRATION

Running state:

```text
WorkflowState {
    WorkflowVersion
    Node
    Variables
    Checkpoint
}
```

## 539.58 — Migration mapping

```text
OldNode → NewNode
OldField → NewField
OldState → NewState
```

## 539.59 — Safe migration

Migration must validate resulting state.

## 539.60 — Unsupported state

Workflow enters migration-required/error state.

## 539.61 — Atomic migration

State transition should be atomic where durable store permits.

## 539.62 — Rollback

Migration rollback requires reverse mapping or checkpoint restore.

---

# 539.63 — AGENT SESSION MIGRATION

Session migration must account for:

- context;
- memory refs;
- pending actions;
- model state;
- tool state;
- workflow state;
- approval tokens.

## 539.64 — Pending action

Cannot silently become approved after migration.

## 539.65 — Approval invalidation

Policy/capability/action change may invalidate approval.

## 539.66 — Model KV cache

KV cache may be discarded/rebuilt if incompatible.

## 539.67 — Session continuity

Logical session identity can survive model/runtime migration.

---

# 539.68 — SCHEMA REGISTRY

All long-lived schemas should have:

```text
SchemaId
Version
Hash
CompatibilityRules
MigrationRules
```

## 539.69 — Schema fingerprints

Canonical schema hash.

## 539.70 — Schema diff

Machine-readable semantic diff.

## 539.71 — Schema validator

Input/output/state validation.

## 539.72 — Schema migration tool

Generate/execute explicit migrations.

---

# 539.73 — MIGRATION PLAN

```text
MigrationPlan {
    SourceVersion
    TargetVersion
    Steps
    Preconditions
    Validation
    Rollback
}
```

## 539.74 — Precondition

Migration starts only when prerequisites satisfied.

## 539.75 — Dry-run

Migration simulation without mutating production.

## 539.76 — Validation

Post-migration state validation.

## 539.77 — Checkpoint

Pre-migration checkpoint.

## 539.78 — Rollback

Explicit rollback mechanism.

## 539.79 — Partial migration

Track each migrated unit.

## 539.80 — Resume

Interrupted migration can resume safely.

---

# 539.81 — BLUE/GREEN MIGRATION

```text
Old Version
     │
     ├── existing sessions
     │
     ↓
New Version
     │
     └── new sessions
```

## 539.82 — New-session cutover

Supported.

## 539.83 — Existing-session drain

Old sessions drain.

## 539.84 — Forced migration

Explicit only.

## 539.85 — Mixed-version operation

Allowed only when compatibility matrix permits.

---

# 539.86 — CANARY COMPATIBILITY

Canary deployment from 534 must verify:

- model contract;
- tool contract;
- policy;
- memory;
- workflow;
- runtime.

## 539.87 — Canary evidence

Exact version/configuration.

## 539.88 — Rollback

Canary failure can trigger policy-defined rollback.

## 539.89 — Session safety

Rollback must account for already-created sessions.

---

# 539.90 — BACKWARD COMPATIBILITY

Compatibility classes:

```text
Backward
Forward
Bidirectional
None
```

## 539.91 — Backward

New consumer accepts old artifact.

## 539.92 — Forward

Old consumer accepts new artifact.

## 539.93 — Bidirectional

Both.

## 539.94 — None

Explicit incompatible.

## 539.95 — Compatibility evidence

Must identify exact dimension.

---

# 539.96 — ADAPTERS

Adapters can bridge incompatible versions.

```text
Old API
 ↓
Adapter
 ↓
New API
```

## 539.97 — Adapter identity

Versioned.

## 539.98 — Adapter overhead

Measured.

## 539.99 — Adapter semantics

Must preserve documented contract.

## 539.100 — Adapter lifecycle

Can be deprecated after migration.

---

# 539.101 — MODEL SHADOW VALIDATION

Old and new versions can process same inputs in shadow mode.

## 539.102 — Output comparison

Compare task-specific properties, not a universal score.

## 539.103 — Numerical comparison

Tolerance explicit.

## 539.104 — Structured output comparison

Schema-aware.

## 539.105 — Generation comparison

Use reproducible test conditions where meaningful.

## 539.106 — Agent comparison

Compare action traces/properties.

## 539.107 — Safety comparison

Run 537 suite.

## 539.108 — Performance comparison

Use 450/481.

## 539.109 — No automatic winner

Comparison produces evidence, not a universal winner/ranking.

---

# 539.110 — SEMANTIC VERSION DIFF

Diff categories:

```text
Added
Removed
Changed
Compatible
Breaking
SecuritySensitive
Unknown
```

## 539.111 — API diff

Signature/schema.

## 539.112 — ABI diff

Native ABI.

## 539.113 — Effect diff

Read/write/network/process etc.

## 539.114 — Capability diff

Required/provided capabilities.

## 539.115 — Policy diff

Allowed action set.

## 539.116 — Memory diff

Schema and semantic meaning.

## 539.117 — Workflow diff

Node/edge/state changes.

## 539.118 — Model diff

Architecture/tokenizer/output/context changes.

## 539.119 — Dependency diff

Runtime/backend/tool changes.

## 539.120 — Unknown

Unable to establish compatibility → Unknown, not Compatible.

---

# 539.121 — MIGRATION VALIDATION

Pipeline:

```text
Source
 ↓
Snapshot
 ↓
Compatibility Analysis
 ↓
Migration Plan
 ↓
Dry Run
 ↓
Validation
 ↓
Canary
 ↓
Production
```

## 539.122 — Pre-migration snapshot

Required for stateful migration where rollback is required.

## 539.123 — Dry-run evidence

Stored.

## 539.124 — Validation suite

Includes:

- schema;
- workflow;
- safety;
- security;
- functionality;
- performance where required.

## 539.125 — Production validation

Post-cutover validation.

---

# 539.126 — ROLLBACK

Rollback dimensions:

```text
Model
Agent
Tool
Prompt
Policy
Memory
Workflow
Runtime
Deployment
```

## 539.127 — Rollback identity

Exact previous version.

## 539.128 — Rollback ≠ reverse migration

May restore checkpoint instead.

## 539.129 — External side effects

Rollback cannot undo arbitrary external effects.

## 539.130 — Compensation

535 compensation mechanism.

---

# 539.131 — LONG-RUNNING AGENT VERSIONING

For agents running days/months:

- current version;
- migration eligibility;
- checkpoint version;
- policy version;
- tool versions;
- model version.

## 539.132 — Frozen session

Session can remain on old version.

## 539.133 — Auto-upgrade

Not allowed unless explicit policy.

## 539.134 — Migration window

Optional.

## 539.135 — Forced expiration

Explicit lifecycle policy.

---

# 539.136 — CONFIGURATION COMPATIBILITY

470 configuration is part of compatibility identity.

Changes may affect:

- allocator;
- model;
- GPU;
- safety;
- policy;
- network;
- storage;
- quota.

## 539.137 — Configuration fingerprint

Recorded.

## 539.138 — Environment drift

Detected.

## 539.139 — Semantic configuration change

May trigger revalidation.

## 539.140 — Hidden configuration

Must not affect compatibility.

---

# 539.141 — PACKAGE / REGISTRY INTEGRATION

447/491/492 package metadata can declare:

```text
requires_model
requires_runtime
requires_tool
requires_schema
requires_policy
```

## 539.142 — Artifact selection

Resolver must respect compatibility.

## 539.143 — Binary artifact

Target/ABI/compiler compatibility preserved.

## 539.144 — Precompiled generic

Semantic/compiler/ABI identity required.

---

# 539.145 — AI INTROSPECTION

Queries:

```text
is_compatible(A,B)
why_incompatible(A,B)
required_migration(A,B)
migration_risk(A,B)
what_breaks(A,B)
what_can_remain(A,B)
rollback_plan(A,B)
```

## 539.146 — Compatibility explanation

Must cite concrete dimension.

## 539.147 — Migration explanation

References affected artifacts.

## 539.148 — Unknown

Insufficient evidence remains Unknown.

## 539.149 — No fabricated compatibility

Unknown cannot become compatible through inference alone.

---

# 539.150 — TESTING

Test:

- schema evolution;
- API evolution;
- tool evolution;
- model evolution;
- tokenizer evolution;
- memory migration;
- workflow migration;
- policy migration;
- rollback;
- mixed-version;
- long-running sessions.

## 539.151 — Golden migration tests

Old state → migration → expected new state.

## 539.152 — Round-trip

Where supported:

```text
A → B → A
```

## 539.153 — Property tests

Migration preserves declared invariants.

## 539.154 — Crash tests

Migration interrupted at every checkpoint.

## 539.155 — Replay

Historical session replay against new version.

---

# 539.156 — HARD INVARIANTS

1. Version khác identity.
2. Version khác compatibility.
3. Revision khác published version.
4. Published version immutable.
5. Exact pin supported.
6. Version range supported.
7. Compatibility matrix supported.
8. API compatibility tracked.
9. ABI compatibility tracked.
10. Schema compatibility tracked.
11. Semantic compatibility tracked.
12. Model compatibility tracked.
13. Tokenizer compatibility tracked.
14. Prompt compatibility tracked.
15. Tool compatibility tracked.
16. Memory compatibility tracked.
17. Workflow compatibility tracked.
18. Runtime compatibility tracked.
19. Device compatibility tracked.
20. Numerical compatibility tracked.
21. Security compatibility tracked.
22. Policy compatibility tracked.
23. Model architecture identity recorded.
24. Model weight identity recorded.
25. Tokenizer identity recorded.
26. Vocabulary identity recorded.
27. Special token changes tracked.
28. Context length tracked.
29. Input modality tracked.
30. Output schema tracked.
31. KV cache compatibility tracked.
32. Tool input schema versioned.
33. Tool output schema versioned.
34. Tool effects versioned.
35. Tool capabilities versioned.
36. Required input additions detected.
37. Output changes classified.
38. Effect escalation classified.
39. Capability escalation classified.
40. Tool error schema versioned.
41. Prompt template versioned.
42. Prompt variables typed.
43. Prompt role structure tracked.
44. Prompt changes can trigger evaluation.
45. Memory schema versioned.
46. Additive field compatibility explicit.
47. Removed field classified.
48. Renamed field requires mapping.
49. Type changes require conversion.
50. Semantic changes require migration.
51. Embedding identity includes model.
52. Embedding dimension tracked.
53. Embedding dtype tracked.
54. Embedding normalization tracked.
55. Similarity metric tracked.
56. Embedding model change can require reindex.
57. Index version tracked.
58. RAG chunker version tracked.
59. RAG retriever version tracked.
60. RAG reranker version tracked.
61. Workflow state includes version.
62. Workflow node mapping supported.
63. Workflow migration validates state.
64. Unsupported migration state is explicit failure.
65. Migration can be atomic.
66. Migration rollback is explicit.
67. Partial migration tracked.
68. Interrupted migration can resume.
69. Session migration tracks pending actions.
70. Approval state preserved.
71. Model KV cache migration explicit.
72. Incompatible KV cache may be rebuilt.
73. Logical session identity can survive migration.
74. Schema registry supported.
75. Schema fingerprint supported.
76. Semantic schema diff supported.
77. Migration plan has source/target.
78. Migration plan has preconditions.
79. Migration plan has validation.
80. Migration plan has rollback.
81. Dry-run supported.
82. Dry-run does not mutate production.
83. Pre-migration snapshot supported.
84. Validation evidence preserved.
85. Blue/green migration supported.
86. Existing sessions can drain.
87. Forced migration explicit.
88. Mixed-version execution requires compatibility.
89. Canary integrates compatibility.
90. Canary evidence exact.
91. Rollback exact versioned.
92. Rollback does not imply external side-effect reversal.
93. Compensation integrates 535.
94. Backward compatibility classified.
95. Forward compatibility classified.
96. Bidirectional compatibility classified.
97. Incompatible classified.
98. Adapters versioned.
99. Adapter semantics documented.
100. Adapter overhead measurable.
101. Shadow comparison supported.
102. Shadow comparison is property-specific.
103. Numerical tolerance explicit.
104. Structured output comparison schema-aware.
105. Agent comparison can inspect action traces.
106. Safety comparison integrates 537.
107. Performance comparison integrates 450/481.
108. No automatic universal model winner.
109. Semantic diff supported.
110. Added/removed/changed classified.
111. Breaking changes identified.
112. Security-sensitive changes identified.
113. Unknown compatibility preserved.
114. Migration analysis precedes migration.
115. Migration validation follows migration.
116. Long-running sessions track version.
117. Old sessions can remain frozen.
118. Auto-upgrade requires explicit policy.
119. Migration window supported.
120. Configuration fingerprint tracked.
121. Environment drift detectable.
122. Hidden configuration cannot affect compatibility.
123. Package compatibility integrates 447.
124. Registry compatibility integrates 491/492.
125. Binary compatibility integrates 451/483.
126. AI compatibility queries supported.
127. Compatibility explanations cite dimensions.
128. Migration explanations cite affected artifacts.
129. Unknown is not compatible.
130. Golden migration tests supported.
131. Round-trip tests supported where applicable.
132. Property migration tests supported.
133. Crash-interruption tests supported.
134. Historical replay supported.
135. Policy version preserved.
136. Tool version preserved.
137. Model version preserved.
138. Memory version preserved.
139. Workflow version preserved.
140. Runtime version preserved.
141. Deployment configuration preserved.
142. Approval tokens cannot silently survive incompatible scope changes.
143. Security capability increases require explicit review.
144. Effect increases require explicit review.
145. Schema migrations cannot silently discard required information.
146. Semantic migrations cannot be represented as serialization-only conversion.
147. Rollback cannot erase migration evidence.
148. Historical sessions remain interpretable.
149. Compatibility evidence has provenance.
150. Migration evidence has provenance.
151. Configuration changes can invalidate compatibility.
152. Policy changes can invalidate approval.
153. Tool changes can invalidate session migration.
154. Model changes can invalidate KV state.
155. Tokenizer changes can invalidate cached token IDs.
156. Embedding changes can invalidate vector indexes.
157. Memory schema changes can invalidate checkpoints.
158. Workflow changes can invalidate running state.
159. Runtime changes can invalidate execution plans.
160. Device changes can invalidate compiled kernels.
161. Numerical policy changes can invalidate comparison evidence.
162. Safety policy changes can trigger reevaluation.
163. Security policy changes can trigger reevaluation.
164. Evaluation identity preserved.
165. Compatibility does not imply safety.
166. Compatibility does not imply correctness.
167. Compatibility does not imply performance equality.
168. Compatibility does not imply identical model behavior.
169. Migration does not imply semantic equivalence unless proven by explicit evidence.
170. Axiom does not fabricate compatibility evidence.
171. Axiom does not silently upgrade production agents.
172. Axiom does not silently downgrade security policy.
173. Axiom does not silently change tokenizer semantics.
174. Axiom does not silently change tool effects.
175. Axiom does not silently migrate irreversible external state.
176. Migration has explicit authority.
177. Rollback has explicit authority.
178. Deployment cutover has explicit authority.
179. Historical provenance remains queryable.
180. **Axiom AI Versioning phải cho phép model, agent, tool, prompt, memory, workflow, tokenizer, embedding, policy và runtime tiến hóa độc lập nhưng có kiểm tra compatibility/migration rõ ràng; mọi thay đổi breaking, security-sensitive hoặc chưa xác định phải được biểu diễn minh bạch, migration phải có snapshot/validation/rollback phù hợp và hệ thống không được tự ý nâng cấp production hoặc giả định semantic equivalence.**

**BOOTSTRAP-539 hoàn tất / LOCKED.**

---

# BOOTSTRAP-540 — AI WORKFLOW LANGUAGE, DECLARATIVE AGENT GRAPH, DURABLE EXECUTION DSL, STATE MACHINE, EVENT TRIGGER & HUMAN-AI WORKFLOW FOUNDATION

**Trạng thái: COMPLETED / LOCKED**

Sau 535–539, Axiom đã có runtime agent production, resource governance, safety và versioning. Bước tiếp theo là chuẩn hóa **workflow thành một model có thể khai báo, kiểm tra, compile, execute và resume**, thay vì mỗi framework tự tạo một DSL riêng.

```text
Workflow Source
      │
      ↓
Workflow AST
      │
      ↓
Semantic Workflow Graph
      │
 ┌────┼───────────┐
 ↓    ↓           ↓
Types Effects   Policies
 │    │           │
 └────┼───────────┘
      ↓
Workflow IR
      │
      ↓
Execution Plan
      │
      ↓
Durable Runtime
      │
 ┌────┼───────────────┐
 ↓    ↓               ↓
Tasks Events       Human Gates
 │    │               │
 └────┼───────────────┘
      ↓
Checkpoint / Replay
```

---

## 540.1 — Workflow ≠ Agent

Workflow mô tả **control/data flow**.

Agent cung cấp autonomous decision capability.

Một workflow có thể:

- không dùng AI;
- dùng một model;
- dùng nhiều agent.

## 540.2 — Workflow ≠ Thread

Workflow node không nhất thiết tương ứng OS thread.

## 540.3 — Workflow ≠ Process

Workflow execution có thể tồn tại lâu hơn process.

## 540.4 — Workflow ≠ Transaction

Workflow compensation không phải DB rollback.

---

# 540.5 — WORKFLOW MODEL

```text
Workflow {
    Id
    Version
    Inputs
    Outputs
    Nodes
    Edges
    Policies
    Resources
}
```

## 540.6 — Typed inputs

Workflow input schema typed.

## 540.7 — Typed outputs

Workflow output schema typed.

## 540.8 — Node identity

Stable NodeId.

## 540.9 — Edge identity

Stable EdgeId.

## 540.10 — Workflow hash

Canonical semantic hash.

---

# 540.11 — WORKFLOW NODE TYPES

Tối thiểu:

```text
Start
End
Call
Model
Agent
Tool
Condition
Switch
Parallel
Join
Loop
Wait
Event
HumanApproval
Compensate
Checkpoint
Transform
Emit
```

## 540.12 — Call

Invoke typed function/workflow.

## 540.13 — Model

Invoke model endpoint.

## 540.14 — Agent

Invoke agent.

## 540.15 — Tool

Invoke tool.

## 540.16 — Condition

Boolean branch.

## 540.17 — Parallel

Concurrent branches.

## 540.18 — Join

Synchronization.

## 540.19 — Loop

Explicit bounded/unbounded policy.

## 540.20 — Wait

Timer/event/deadline.

---

# 540.21 — EVENT TRIGGER

Workflow có thể bắt đầu bởi:

```text
HTTP
CLI
Timer
File
Message
Database
Webhook
User
Agent
System
```

## 540.22 — Trigger schema

Trigger input typed.

## 540.23 — Trigger authentication

External trigger must pass auth policy.

## 540.24 — Duplicate trigger

Event identity/idempotency.

## 540.25 — Ordering

Ordering guarantees explicit.

---

# 540.26 — STATE MACHINE

Workflow runtime state:

```text
Created
Running
Waiting
Paused
Cancelling
Completed
Failed
Cancelled
Compensating
```

## 540.27 — State transitions

Deterministic transition rules.

## 540.28 — Invalid transitions

Rejected.

## 540.29 — Persistent state

Durable mode persists state.

## 540.30 — Ephemeral mode

Can run entirely in memory.

---

# 540.31 — DURABLE EXECUTION

Durable workflow survives:

- process crash;
- machine restart;
- network interruption;
- temporary tool failure.

## 540.32 — Checkpoint

Checkpoint after selected durable boundaries.

## 540.33 — Event log

Optional append-only event history.

## 540.34 — Recovery

Recovery reconstructs logical state.

## 540.35 — Replay

Replay uses recorded events.

## 540.36 — Determinism

Pure workflow logic should replay deterministically.

## 540.37 — Nondeterminism

External results/random/time are recorded as events when deterministic replay is required.

---

# 540.38 — SIDE EFFECT BOUNDARY

```text
Pure
 ↓
Read
 ↓
Write
 ↓
External
 ↓
Irreversible
```

## 540.39 — Effect annotation

Node declares effects.

## 540.40 — Effect checking

Workflow compiler checks capability/effect requirements.

## 540.41 — No hidden side effects

A node cannot silently declare itself pure.

## 540.42 — Compensation

Write/external action can specify compensation.

## 540.43 — Compensation is not guarantee

External system may reject compensation.

---

# 540.44 — HUMAN TASK

```text
HumanTask {
    TaskId
    Input
    ApprovalPolicy
    Assignee
    Deadline
    OutputSchema
}
```

## 540.45 — Human assignment

Explicit.

## 540.46 — Human response

Typed.

## 540.47 — Timeout

Explicit.

## 540.48 — Delegation

Can delegate if policy permits.

## 540.49 — Approval

Integrates 535/537/538.

---

# 540.50 — AGENT NODE

Agent node declares:

```text
Agent
Input
Output
Capabilities
Budget
Policy
```

## 540.51 — Autonomous loop

Agent internally runs 511/535.

## 540.52 — Workflow boundary

Agent cannot escape workflow capability.

## 540.53 — Agent result

Typed.

## 540.54 — Agent failure

Structured.

## 540.55 — Agent cancellation

Propagates.

---

# 540.56 — MODEL NODE

Model invocation declares:

```text
Model
Version/Range
Input
Output
Budget
Policy
```

## 540.57 — Model fallback

Explicit.

## 540.58 — Streaming

Supported.

## 540.59 — Cancellation

Supported.

## 540.60 — Model output validation

Schema/property validation.

---

# 540.61 — TOOL NODE

Tool invocation:

```text
Tool
Version
Input
Output
Effects
Capabilities
```

## 540.62 — Capability check

Before execution.

## 540.63 — Approval

Optional/required according to policy.

## 540.64 — Retry

Explicit.

## 540.65 — Idempotency

Explicit.

---

# 540.66 — DATA FLOW

Node outputs become typed values.

```text
A → value → B
```

## 540.67 — No implicit global variables

Workflow data must flow through declared state.

## 540.68 — State store

Explicit persistent state.

## 540.69 — Large payload

Can use reference/object store rather than copying.

## 540.70 — Ownership

Payload lifetime follows 423 semantics where represented in Axiom runtime.

---

# 540.71 — CONDITIONS

```text
if condition → A
else → B
```

## 540.72 — Typed condition

Must evaluate to bool.

## 540.73 — Policy condition

Policy decisions are not ordinary model-generated booleans.

## 540.74 — Exhaustiveness

Switch/match-like workflow branches can require exhaustive handling.

## 540.75 — Unknown

Unknown condition cannot silently become true.

---

# 540.76 — PARALLELISM

```text
       ┌── A ──┐
Start ─┼── B ──┼─ Join
       └── C ──┘
```

## 540.77 — Independent branches

May execute concurrently.

## 540.78 — Shared mutable state

Requires synchronization.

## 540.79 — Join policy

All/any/quorum/first-success/custom.

## 540.80 — Partial result

Explicitly supported.

---

# 540.81 — LOOP

Loop declaration:

```text
Loop {
    condition
    body
    max_iterations?
    deadline?
}
```

## 540.82 — Infinite loop

Allowed only explicit.

## 540.83 — Loop budget

Steps/time/resource.

## 540.84 — Loop cancellation

Supported.

## 540.85 — Loop checkpoint

Optional durable checkpoint.

---

# 540.86 — WAIT

Wait conditions:

```text
Duration
Deadline
Event
Message
Human
Resource
ExternalCondition
```

## 540.87 — Timer

Integrate 474.

## 540.88 — Event wait

Integrate 472/473.

## 540.89 — Human wait

535 approval/human task.

## 540.90 — Timeout

Explicit.

---

# 540.91 — WORKFLOW DSL

Axiom có thể cung cấp declarative syntax conceptually:

```text
workflow process(input: Request) -> Result {
    step data = fetch(input)
    step analysis = agent Analyze(data)
    if analysis.requires_review {
        step approval = human_review(analysis)
        step output = finalize(analysis, approval)
    } else {
        step output = finalize(analysis)
    }
    output
}
```

Đây là **workflow syntax**, không phải thay đổi language core.

## 540.92 — Lowering

Workflow syntax → Workflow IR.

## 540.93 — Semantic validation

Trước execution.

## 540.94 — Type checking

Input/output/state.

## 540.95 — Effect checking

Tool/model/human/external effects.

---

# 540.96 — WORKFLOW IR

```text
WorkflowIR {
    Inputs
    Outputs
    Blocks
    Nodes
    Edges
    StateSchema
    Effects
    Policies
}
```

## 540.97 — Basic blocks

Explicit control flow.

## 540.98 — State variables

Typed.

## 540.99 — Await points

Explicit.

## 540.100 — Checkpoint points

Explicit or compiler-selected according to durable policy.

---

# 540.101 — COMPILER OPTIMIZATION

Workflow compiler may:

- fuse pure transformations;
- eliminate dead steps;
- parallelize independent steps;
- batch model requests;
- batch tool calls where semantics permit;
- cache pure results;
- checkpoint strategically.

## 540.102 — Side-effect barrier

Optimizer cannot reorder incompatible side effects.

## 540.103 — Dependency analysis

Data/effect dependencies.

## 540.104 — Model batching

Only compatible requests.

## 540.105 — Tool batching

Only if tool contract supports batch semantics.

---

# 540.106 — RETRY

Retry policy:

```text
max_attempts
backoff
jitter
retryable_errors
```

## 540.107 — Idempotency

Retry non-idempotent action requires explicit contract.

## 540.108 — Retry checkpoint

Attempt state recorded.

## 540.109 — Retry budget

Integrates 536.

## 540.110 — Retry storm prevention

Global/session/workflow limits.

---

# 540.111 — CANCELLATION

Cancellation states:

```text
Requested
Propagating
Cancelled
CompletedBeforeCancel
```

## 540.112 — Cooperative

Normal workflow cancellation cooperative.

## 540.113 — Non-cancellable

Node can declare non-cancellable boundary.

## 540.114 — Deadline

Deadline cancellation.

## 540.115 — Cleanup

423 cleanup always respected.

---

# 540.116 — FAILURE HANDLING

```text
Retry
Fallback
Compensate
Skip
Abort
Pause
HumanReview
```

## 540.117 — Failure policy

Node/workflow scope.

## 540.118 — Failure provenance

Exact node/attempt/error.

## 540.119 — Partial workflow

Preserve completed work.

## 540.120 — Unknown state

External unknown state remains Unknown.

---

# 540.121 — VERSIONING

Workflow version integrates 539.

## 540.122 — Running workflow

Uses pinned version.

## 540.123 — Migration

Explicit workflow migration.

## 540.124 — New executions

Can use new version while old sessions continue.

## 540.125 — Rollback

Deployment rollback doesn't magically rewind completed external actions.

---

# 540.126 — RESOURCE GOVERNANCE

Each workflow can specify:

```text
max_steps
max_time
max_tokens
max_cpu
max_gpu
max_memory
max_tool_calls
```

## 540.127 — Inheritance

Deployment→workflow→node.

## 540.128 — Budget accounting

Integrates 536.

## 540.129 — Admission

Integrates 534/536.

## 540.130 — Resource-aware scheduling

Integrates 471.

---

# 540.131 — SECURITY

Workflow itself is executable authority.

## 540.132 — Capability declaration

Workflow manifest declares required capabilities.

## 540.133 — Capability minimization

Compiler/runtime can detect unused requested capabilities.

## 540.134 — External input

Untrusted.

## 540.135 — Tool output

Untrusted data.

## 540.136 — Model output

Untrusted action proposal.

## 540.137 — Policy boundary

All side effects cross policy gate.

---

# 540.138 — STATIC ANALYSIS

Workflow analyzer can detect:

- unreachable nodes;
- missing join;
- dead state;
- impossible branch;
- unhandled failure;
- missing compensation;
- unsafe capability;
- unbounded loop;
- retry storm;
- missing timeout;
- resource budget conflict.

## 540.139 — Proof status

```text
Proven
Disproven
Unknown
```

## 540.140 — No false proof

Unknown is not safe.

---

# 540.141 — OBSERVABILITY

Every workflow execution:

```text
WorkflowRunId
WorkflowVersion
NodeId
Attempt
Timestamp
Status
```

## 540.142 — Node trace

Trace 475/481.

## 540.143 — State history

Optional durable event history.

## 540.144 — Cost

536 usage attribution.

## 540.145 — Safety

537 evaluation/runtime events.

---

# 540.146 — DEBUGGING

Queries:

```text
why_stuck
why_failed
why_retried
why_waiting
why_branch
why_tool_called
why_model_called
why_not_parallel
why_not_cached
```

## 540.147 — State inspection

Current typed state.

## 540.148 — Event inspection

Historical events.

## 540.149 — Replay

Reconstruct execution.

## 540.150 — Time travel

Debug simulation can use virtual clock.

---

# 540.151 — TESTING

Workflow tests:

- unit node;
- integration;
- end-to-end;
- replay;
- fault injection;
- timeout;
- cancellation;
- approval;
- migration;
- resource exhaustion.

## 540.152 — Mock model

Supported.

## 540.153 — Mock tool

Supported.

## 540.154 — Mock human

Supported.

## 540.155 — Mock clock

474.

## 540.156 — Mock event bus

472/473.

---

# 540.157 — DETERMINISTIC REPLAY

Replay records:

```text
Input
ModelResponse
ToolResponse
HumanResponse
Time
RandomSeed
ExternalEvent
```

## 540.158 — Pure node

Recomputed.

## 540.159 — External node

Recorded result replayed.

## 540.160 — Side effects

Never re-executed during safe replay.

---

# 540.161 — WORKFLOW PACKAGING

Workflow package includes:

```text
Workflow
Schema
Dependencies
Models
Tools
Policies
Capabilities
Migration
Tests
```

## 540.162 — Dependency identity

Exact or constrained.

## 540.163 — Build identity

Compiler/runtime identity.

## 540.164 — Deployment identity

Exact deployment config.

## 540.165 — Provenance

Full graph.

---

# 540.166 — HUMAN-AI HYBRID

Workflow can combine:

```text
Human
Agent
Model
Tool
Function
Event
```

Không có loại node nào mặc định có quyền cao hơn loại khác.

## 540.167 — Human decision

Typed output.

## 540.168 — Agent recommendation

Recommendation khác authorization.

## 540.169 — Human approval

Approval explicit.

## 540.170 — Policy

Policy vẫn áp dụng kể cả human-triggered action.

---

# 540.171 — WORKFLOW COMPOSITION

Workflow có thể call workflow:

```text
A
 ↓
Workflow B
 ↓
Workflow C
```

## 540.172 — Input/output contracts

Typed.

## 540.173 — Capability delegation

Child workflow subset.

## 540.174 — Budget delegation

Child budget subset.

## 540.175 — Cancellation

Parent cancellation propagates.

## 540.176 — Failure

Parent policy determines handling.

---

# 540.177 — DISTRIBUTED WORKFLOW

Workflow nodes có thể chạy:

- local;
- process;
- machine;
- region.

## 540.178 — Remote execution

Explicit.

## 540.179 — Network partition

Workflow state remains explicit.

## 540.180 — Exactly-once

Không claim exactly-once external execution.

## 540.181 — Durable state

State store explicit.

## 540.182 — Consensus

Nếu cần replicated workflow state, integrate 502.

---

# 540.183 — SCHEDULING

Triggers:

```text
cron
interval
event
webhook
queue
manual
dependency
```

## 540.184 — Cron

Timezone explicit.

## 540.185 — Duplicate schedules

Schedule identity.

## 540.186 — Missed execution

Policy:

```text
Skip
CatchUp
Coalesce
RunOnce
```

## 540.187 — Concurrent executions

Policy-defined.

---

# 540.188 — WORKFLOW SECURITY GRAPH

```text
Workflow
 ├── Capability
 ├── Tool
 ├── Model
 ├── Data
 ├── Network
 ├── Secret
 └── Human Approval
```

## 540.189 — Security query

`why_can_workflow_call(tool)`.

## 540.190 — Excess capability

Analyzer can report unused capability.

---

# 540.191 — HARD INVARIANTS

1. Workflow khác Agent.
2. Workflow khác Thread.
3. Workflow khác Process.
4. Workflow khác Transaction.
5. Workflow có identity.
6. Workflow có version.
7. Workflow có semantic hash.
8. Workflow inputs typed.
9. Workflow outputs typed.
10. Node có identity.
11. Edge có identity.
12. Node schema explicit.
13. Node effect explicit.
14. Start node supported.
15. End node supported.
16. Call node supported.
17. Model node supported.
18. Agent node supported.
19. Tool node supported.
20. Condition node supported.
21. Switch node supported.
22. Parallel node supported.
23. Join node supported.
24. Loop node supported.
25. Wait node supported.
26. Event node supported.
27. Human approval supported.
28. Compensation supported.
29. Checkpoint supported.
30. Transform supported.
31. Emit supported.
32. HTTP trigger supported.
33. Timer trigger supported.
34. File trigger can be supported.
35. Message trigger supported.
36. Database trigger can be supported.
37. Webhook trigger supported.
38. User trigger supported.
39. Duplicate trigger handling explicit.
40. Trigger ordering explicit.
41. Workflow lifecycle explicit.
42. Invalid transitions rejected.
43. Durable state supported.
44. Ephemeral state supported.
45. Checkpoint supported.
46. Event log supported.
47. Recovery supported.
48. Replay supported.
49. Pure logic replay deterministic.
50. External nondeterminism recordable.
51. Side-effect boundary explicit.
52. Effects checked.
53. No hidden side effects.
54. Compensation distinct from rollback.
55. Compensation not guaranteed.
56. Human task typed.
57. Human identity supported.
58. Human deadline supported.
59. Human delegation policy explicit.
60. Human approval integrates 535.
61. Agent node capability-scoped.
62. Agent cannot escape workflow capability.
63. Agent output typed.
64. Agent cancellation propagates.
65. Model node versioned.
66. Model fallback explicit.
67. Model streaming supported.
68. Model cancellation supported.
69. Model output validated.
70. Tool node versioned.
71. Tool capabilities checked.
72. Tool approval supported.
73. Tool retry explicit.
74. Tool idempotency explicit.
75. Data flow typed.
76. No implicit global workflow variables.
77. Persistent state explicit.
78. Large payload references supported.
79. Ownership semantics preserved.
80. Condition typed.
81. Unknown condition cannot silently become true.
82. Parallel execution supported.
83. Shared mutable state synchronized.
84. Join policy explicit.
85. Partial result supported.
86. Loop bounds can be explicit.
87. Infinite loops require explicit policy.
88. Loop budget supported.
89. Loop cancellation supported.
90. Loop checkpoint supported.
91. Wait duration supported.
92. Wait deadline supported.
93. Wait event supported.
94. Wait human supported.
95. Wait timeout explicit.
96. Workflow DSL can lower to Workflow IR.
97. Workflow syntax does not require changes to Axiom core semantics.
98. Workflow AST separate from ordinary AST semantics where appropriate.
99. Workflow semantic graph explicit.
100. Workflow IR explicit.
101. Workflow state typed.
102. Await points explicit.
103. Checkpoint points explicit.
104. Pure transformations can be optimized.
105. Dead steps can be eliminated.
106. Independent steps can be parallelized.
107. Model batching can be optimized.
108. Tool batching requires compatible semantics.
109. Side-effect barriers prevent invalid reordering.
110. Dependency analysis required for optimization.
111. Retry policy explicit.
112. Retry budget explicit.
113. Non-idempotent retry requires explicit contract.
114. Retry attempts recorded.
115. Retry storm prevention supported.
116. Cancellation states explicit.
117. Cancellation propagates.
118. Non-cancellable boundary explicit.
119. Deadline cancellation supported.
120. Cleanup integrates 423.
121. Failure policy explicit.
122. Failure provenance preserved.
123. Partial workflow state preserved.
124. Unknown external state remains Unknown.
125. Workflow version integrates 539.
126. Running workflow uses pinned version.
127. Migration explicit.
128. New executions can use new version.
129. Rollback does not imply external reversal.
130. Resource budgets supported.
131. Resource hierarchy supported.
132. Budget accounting integrates 536.
133. Admission integrates 534/536.
134. Scheduling integrates 471.
135. Workflow capability manifest supported.
136. External input untrusted.
137. Tool output untrusted.
138. Model output untrusted.
139. Side effects cross policy boundary.
140. Static workflow analysis supported.
141. Unreachable node detection supported.
142. Dead-state detection supported.
143. Impossible branch detection supported.
144. Unhandled failure detection supported.
145. Missing compensation detection can be reported.
146. Unsafe capability detection supported.
147. Unbounded loop detection supported.
148. Retry storm detection supported.
149. Missing timeout detection supported.
150. Budget conflict detection supported.
151. Analysis distinguishes Proven/Disproven/Unknown.
152. Unknown is not proof.
153. Workflow tracing integrates 475/481.
154. Workflow cost integrates 536.
155. Safety integrates 537.
156. Every execution has WorkflowRunId.
157. Every node execution has NodeId.
158. Every attempt has identity.
159. State inspection supported.
160. Historical event inspection supported.
161. Replay supported.
162. Virtual time debugging supported.
163. Mock model supported.
164. Mock tool supported.
165. Mock human supported.
166. Mock clock supported.
167. Mock event bus supported.
168. Replay records external results.
169. Replay does not execute irreversible side effects by default.
170. Workflow package has dependency identity.
171. Workflow package has policy identity.
172. Workflow package has capability identity.
173. Workflow package has test identity.
174. Workflow package has migration identity.
175. Workflow package has provenance.
176. Human and AI nodes have no implicit authority ordering.
177. Agent recommendation is not authorization.
178. Human action remains policy-bound.
179. Child workflow receives attenuated capabilities.
180. Child workflow receives attenuated budget.
181. Parent cancellation propagates.
182. Distributed workflow supported.
183. Remote execution explicit.
184. Network partition semantics explicit.
185. No false exactly-once claim.
186. Durable replicated state can integrate 502.
187. Scheduling supports cron.
188. Scheduling supports interval.
189. Scheduling supports events.
190. Scheduling supports webhooks.
191. Scheduling supports queues.
192. Manual trigger supported.
193. Dependency trigger supported.
194. Cron timezone explicit.
195. Schedule identity explicit.
196. Missed execution policy explicit.
197. Concurrent schedule execution policy explicit.
198. Workflow security graph supported.
199. Workflow capability explanation supported.
200. Excess capability analysis supported.
201. **Axiom Workflow Foundation phải biến workflow thành một execution graph typed, versioned, effect-aware và có thể durable/replayable; nó phải kết hợp function/model/agent/tool/human/event trong cùng một execution model nhưng giữ rõ ranh giới capability, side effect, state, budget, cancellation, failure và external authority, đồng thời không biến workflow engine thành thành phần bắt buộc của Axiom runtime thông thường.**

**BOOTSTRAP-540 hoàn tất / LOCKED.**

### Task kế tiếp

**`BOOTSTRAP-541 — AI WORKFLOW COMPILER, DAG OPTIMIZATION, DURABLE STATE MACHINE LOWERING, EVENT SOURCING, CHECKPOINT OPTIMIZATION, PARALLEL EXECUTION & NATIVE WORKFLOW RUNTIME`**