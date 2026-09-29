Tiếp tục với **BOOTSTRAP-650 — Native AI Memory & Persistent Cognitive State Runtime 5.0**.

:::writing{variant="document" id="73164" title="BOOTSTRAP-650 — Native AI Memory, Context Engineering, Episodic/Semantic/Procedural Memory, Long-Context Runtime, Retrieval Memory, Forgetting, Consolidation & Persistent Cognitive State 5.0"}
# BOOTSTRAP-650
## Native AI Memory, Context Engineering, Episodic/Semantic/Procedural Memory, Long-Context Runtime, Retrieval Memory, Forgetting, Consolidation & Persistent Cognitive State 5.0

**Status:** COMPLETE  
**Layer:** Native AI Memory & Cognitive State Plane  
**Depends on:** BOOTSTRAP-600 → BOOTSTRAP-649

---

# 1. Mục tiêu

BOOTSTRAP-650 định nghĩa memory runtime native cho Axiom.

Mục tiêu:

- working memory;
- short-term memory;
- episodic memory;
- semantic memory;
- procedural memory;
- long-term memory;
- persistent cognitive state;
- context construction;
- context compression;
- retrieval memory;
- memory indexing;
- memory consolidation;
- forgetting;
- archival;
- memory replay;
- memory provenance;
- memory versioning;
- memory importance;
- memory decay;
- memory conflict handling;
- multimodal memory;
- agent memory;
- model context memory;
- distributed memory;
- privacy-aware memory;
- memory governance.

650 không biến Axiom thành một "AI chatbot memory API".

Nó là một **general-purpose persistent cognitive state runtime** có thể được sử dụng bởi:

```text
Agent
Model
Workflow
Application
Robot
Simulation
Knowledge System
Search/RAG
```

---

# 2. Boundary

```text
600  State / Checkpoint
628  Distributed Data
641  Search / Retrieval
642  Analytics
643  ML / Tensor
644  Agent
645  Knowledge Graph
646  Evaluation
647  Model Lifecycle
648  Simulation
649  Multimodal
650  AI Memory
```

Phân biệt:

```text
600 = application state
628 = distributed persistent data
641 = retrieval/indexing
645 = semantic graph
650 = cognitive memory semantics
```

650 không thay thế database.

---

# 3. Kiến trúc tổng quát

```text
                 ┌─────────────────────┐
                 │      AI / Agent     │
                 └──────────┬──────────┘
                            │
                            ▼
                 ┌─────────────────────┐
                 │        650          │
                 │   Memory Runtime    │
                 └──────────┬──────────┘
                            │
        ┌───────────────────┼───────────────────┐
        ▼                   ▼                   ▼
   Working Memory      Long-Term Memory      Context
        │                   │                   │
        ▼                   ▼                   ▼
   Session State      Episodic/Semantic     Context Builder
                         /Procedural             │
        │                   │                    ▼
        └───────────────────┼──────────────► 643
                            │
                ┌───────────┼───────────┐
                ▼           ▼           ▼
               641         645         628
             Search      Knowledge    Storage
```

---

# 4. Nguyên tắc

1. Memory là dữ liệu, không phải authority.
2. Memory không tự cấp capability.
3. Memory provenance phải được bảo toàn.
4. Memory revision phải explicit.
5. Memory identity phải ổn định.
6. Memory generation chống stale writer.
7. Context không phải memory.
8. Retrieval không phải memory.
9. Embedding không phải semantic truth.
10. Model-generated memory không mặc định verified.
11. User-provided memory và inferred memory phải phân biệt.
12. Memory source phải được ghi nhận.
13. Memory có thể mâu thuẫn.
14. Conflict không được tự động biến thành truth.
15. Forgetting phải explicit.
16. Retention thuộc governance 640.
17. Security thuộc 603.
18. Policy thuộc 639.
19. Storage thuộc 611/628.
20. Search thuộc 641.
21. Knowledge semantics thuộc 645.
22. Model execution thuộc 643.
23. Agent lifecycle thuộc 644.
24. Multimodal representation thuộc 649.
25. Checkpoint thuộc 600.
26. Không cần GC.
27. Không bắt buộc vector database.
28. Không bắt buộc LLM.
29. Không bắt buộc embedding.
30. Không bắt buộc external memory server.
31. Memory phải chạy local.
32. Memory có thể distributed.
33. Context construction phải bounded.
34. Retrieval phải bounded.
35. Memory consolidation phải bounded.
36. Memory writes phải idempotent khi cần.
37. Replay phải reproducible khi provider hỗ trợ.
38. Sensitive memory phải được governance.
39. Memory deletion phải chống resurrection.
40. Struct-only API.

---

# 5. MemoryKind

```text
Working
ShortTerm
Episodic
Semantic
Procedural
LongTerm
External
Derived
```

---

# 6. Working Memory

Working Memory chứa thông tin đang được sử dụng.

Ví dụ:

```text
current task
current context
current observations
current tool results
current intermediate state
```

Không nhất thiết persistent.

---

# 7. Short-Term Memory

Dữ liệu session gần đây.

Có thể có TTL.

---

# 8. Episodic Memory

Lưu các sự kiện/episode đã xảy ra.

Ví dụ:

```text
Agent performed action X
Tool returned Y
User requested Z
Simulation produced event Q
```

---

# 9. Semantic Memory

Kiến thức đã được tổng hợp.

Ví dụ:

```text
Entity A has property B
Concept X relates to Y
```

Có thể lưu trực tiếp trong 645.

650 giữ semantics về **memory lifecycle**.

---

# 10. Procedural Memory

Lưu cách thực hiện task.

Ví dụ:

```text
Procedure:
1. inspect input
2. validate schema
3. transform
4. save
```

Procedural memory không tự động được thực thi.

---

# 11. Long-Term Memory

Logical class bao gồm memory persistent lâu dài.

---

# 12. MemoryRecord

```text id="b6f1f2"
MemoryRecord {
    memory_id
    generation
    kind
    payload
    source
    provenance
    importance
    created_at
    updated_at
    retention
    status
}
```

---

# 13. MemoryId

Ổn định qua các revision.

---

# 14. MemoryGeneration

Mỗi replacement tạo generation mới.

---

# 15. MemoryRevision

Revision immutable.

---

# 16. MemoryStatus

```text
Candidate
Active
Superseded
Archived
Expired
Deleted
Quarantined
```

---

# 17. Candidate memory

Thông tin mới nhưng chưa được xác thực.

---

# 18. Verified memory

Có evidence đủ theo policy.

---

# 19. Rejected memory

Được lưu để audit nếu policy yêu cầu, nhưng không được retrieval như active truth.

---

# 20. MemorySource

```text
User
Agent
Tool
Model
Sensor
Document
Event
Simulation
KnowledgeGraph
Search
ExternalSystem
Derived
```

---

# 21. Source trust

Trust metadata:

```text
Declared
Observed
Imported
Inferred
Generated
Verified
```

---

# 22. Memory provenance

Mỗi memory có thể truy ngược:

```text
source
event
model
tool
document
revision
transformation
```

---

# 23. Evidence

Evidence có thể là:

- text span;
- image region;
- audio segment;
- video interval;
- document revision;
- event;
- graph assertion;
- tool result.

---

# 24. Evidence reference

```text id="w8kz4p"
EvidenceRef {
    source_id
    revision
    span
    modality
}
```

---

# 25. Memory confidence

Confidence là metadata, không phải truth.

---

# 26. Importance

Memory có thể có:

```text
importance
utility
recency
frequency
confidence
```

---

# 27. Memory score

Axiom không định nghĩa một universal score.

Runtime cho phép nhiều signal độc lập.

---

# 28. Retrieval relevance

641 có thể cung cấp relevance.

---

# 29. Memory utility

Application/agent có thể ghi nhận memory hữu ích.

---

# 30. Memory frequency

Có thể theo dõi số lần được truy cập.

---

# 31. Recency

Dựa trên memory timestamp.

---

# 32. Decay

Memory có thể có decay policy.

Ví dụ:

```text
Never
Linear
Exponential
Step
TTL
PolicyDefined
```

---

# 33. Decay không xóa dữ liệu

Decay chỉ ảnh hưởng retrieval/consolidation.

---

# 34. Retention

640 quyết định retention bắt buộc.

---

# 35. Forgetting

Forgetting là lifecycle operation.

```text
Active
→ Archived
→ Deleted
```

theo policy.

---

# 36. User-requested forgetting

Có thể tạo explicit deletion request.

---

# 37. Deletion token

Deletion operation phải bound vào:

```text
memory_id
generation
governance_revision
policy_revision
```

---

# 38. No resurrection

Old replication/checkpoint không được phục hồi deleted memory.

---

# 39. Memory namespaces

Memory có namespace:

```text
Application
Tenant
User
Agent
Session
Workflow
Device
Simulation
Project
```

---

# 40. Isolation

Namespace boundaries được enforce bởi 603/639.

---

# 41. Agent memory

644 có thể sở hữu memory namespace riêng.

---

# 42. Shared memory

Agents có thể chia sẻ memory nếu capability/policy cho phép.

---

# 43. Memory delegation

Delegation chỉ cấp quyền đọc/ghi namespace cụ thể.

---

# 44. No implicit cross-agent memory

Agent A không tự thấy memory của Agent B.

---

# 45. WorkingMemory

```text id="1m0r7f"
WorkingMemory {
    items[]
    capacity
    revision
}
```

---

# 46. Working memory operations

```text id="m0w3xq"
push
replace
remove
pin
unpin
clear
snapshot
```

---

# 47. Pinned memory

Không bị eviction theo policy thông thường.

---

# 48. Eviction

```text
LRU
LFU
Importance
Recency
TTL
Priority
Policy
```

---

# 49. Eviction không override retention

Governance always wins.

---

# 50. SessionMemory

Session-specific state.

---

# 51. Session boundary

Session termination có policy:

```text
Discard
Archive
Consolidate
Persist
```

---

# 52. Episodic memory

```text id="m3lq78"
Episode {
    episode_id
    start
    end
    events[]
    outcome
    provenance
}
```

---

# 53. Event memory

Có thể reference 634 event thay vì copy payload.

---

# 54. Memory compression

Có thể summarize episode.

---

# 55. Summary provenance

Summary phải reference source episodes.

---

# 56. Lossy compression

Nếu summary bỏ chi tiết, phải đánh dấu derived/lossy.

---

# 57. Semantic consolidation

Episode:

```text
events
→ pattern
→ semantic fact
```

---

# 58. Consolidation

Không tự động biến inferred fact thành verified fact.

---

# 59. Consolidation policy

```text
Suggest
RequireEvidence
RequireApproval
Automatic
```

---

# 60. Semantic memory

Có thể lưu vào:

- 645 graph;
- 628 structured store;
- 641 vector index.

---

# 61. Memory facade

650 cung cấp logical memory API trên các storage backends.

---

# 62. Procedural memory

```text
Procedure {
    procedure_id
    version
    steps[]
    preconditions
    postconditions
}
```

---

# 63. Procedure step

```text
Action
ToolCall
Decision
Observation
Condition
Loop
Parallel
```

---

# 64. Procedural execution

Memory runtime không tự execute procedure.

644/629 thực hiện.

---

# 65. Procedure trust

Generated procedures cần validation trước execution.

---

# 66. Memory graph

Memory có thể liên kết:

```text
Memory A
   ↓
Memory B
   ↓
Evidence C
   ↓
Entity D
```

---

# 67. MemoryRelation

```text
Supports
Contradicts
DerivedFrom
Supersedes
RelatedTo
CausedBy
ObservedDuring
UsedWith
```

---

# 68. Temporal memory

Memory có:

```text
valid_from
valid_until
observed_at
recorded_at
```

---

# 69. Bitemporal semantics

Có thể phân biệt:

```text
event time
record time
```

---

# 70. Memory conflict

Hai memories có thể đồng thời tồn tại:

```text
A says X
B says not X
```

---

# 71. Conflict representation

```text id="smf5yr"
MemoryConflict {
    memory_a
    memory_b
    reason
    evidence[]
}
```

---

# 72. Conflict resolution

```text
KeepBoth
PreferEvidence
PreferRecent
RequireApproval
Supersede
Reject
```

---

# 73. Resolution policy

Application-specific.

Không có universal truth resolver.

---

# 74. Memory merge

Merging tạo revision mới.

Không mutate historical records.

---

# 75. Memory split

Một memory có thể được tách thành nhiều records.

---

# 76. Memory supersession

Record cũ giữ provenance.

---

# 77. Retrieval

650 sử dụng 641.

---

# 78. Retrieval index

Memory có thể index:

- lexical;
- vector;
- graph;
- metadata;
- temporal.

---

# 79. Hybrid retrieval

```text id="z5v4o9"
semantic
+
lexical
+
recency
+
importance
+
metadata
```

---

# 80. Retrieval policy

Policy có thể giới hạn:

```text max_items
max_bytes
max_age
allowed_sources
allowed_modalities
```

---

# 81. Retrieval query

```text id="l1x1qn"
MemoryQuery {
    namespace
    kinds[]
    query
    filters
    time_range
    limit
}
```

---

# 82. Retrieval result

```text id="0n6l9a"
MemoryHit {
    memory_id
    revision
    score
    evidence
    source
}
```

---

# 83. Retrieval score separation

Different score components remain available.

---

# 84. Query explanation

Memory retrieval can explain:

```text lexical score
semantic score
recency
importance
filter
```

---

# 85. Context engineering

Context builder transforms memories into model context.

---

# 86. ContextBuilder

```text id="l1j3xq"
ContextBuilder {
    retrieve
    filter
    rank
    compress
    order
    pack
}
```

---

# 87. Context policy

```text
max_tokens
max_items
max_modalities
max_age
priority
```

---

# 88. Context sections

```text
System
Task
Recent
Relevant
Evidence
Procedures
Tools
Constraints
```

---

# 89. Section ordering

Model-specific but explicit.

---

# 90. Context packing

649 multimodal representation may be used.

---

# 91. Context compression

Methods:

```text
Truncate
Summarize
Extract
Cluster
Deduplicate
Compress
```

---

# 92. Summarization

Uses 643 model.

---

# 93. Summary verification

Summary should retain source references.

---

# 94. Context deduplication

Duplicate information should not consume unlimited budget.

---

# 95. Semantic deduplication

641/643 embeddings optional.

---

# 96. Context hierarchy

```text
Memory
 ↓
Candidate
 ↓
Selected
 ↓
Compressed
 ↓
Packed
 ↓
Model
```

---

# 97. Context fingerprint

Final context has deterministic fingerprint where possible.

---

# 98. Context provenance

Every context item references originating memory.

---

# 99. Context audit

Can inspect why memory was included.

---

# 100. Long-context

650 does not impose a fixed model context limit.

Model declares capacity.

---

# 101. Context window overflow

Policy:

```text
Reject
Compress
Truncate
RetrieveAgain
Hybrid
```

---

# 102. Sliding context

Long streams can use sliding windows.

---

# 103. Hierarchical context

Old content → summaries → detailed retrieval.

---

# 104. Memory pyramid

```text
Recent raw events
       ↓
Compressed episodes
       ↓
Semantic facts
       ↓
Long-term knowledge
```

---

# 105. Memory consolidation scheduler

607/629 can execute consolidation jobs.

---

# 106. Consolidation trigger

```text
Time
Capacity
SessionEnd
Importance
ExplicitRequest
Event
Threshold
```

---

# 107. Consolidation job

```text id="wq2fvi"
ConsolidationJob {
    namespace
    source_range
    policy
    model
}
```

---

# 108. Consolidation checkpoint

600.

---

# 109. Large-scale consolidation

630 distributes work.

---

# 110. Analytics

642 measures:

- memory growth;
- access frequency;
- retrieval latency;
- consolidation throughput;
- stale ratio.

---

# 111. Memory statistics

```text id="8jgd6e"
count
bytes
age_distribution
access_distribution
kind_distribution
source_distribution
```

---

# 112. Memory compaction

Storage compaction is distinct from cognitive consolidation.

---

# 113. Storage compaction

611/628/612.

---

# 114. Cognitive compaction

650 transforms records.

---

# 115. No GC

Neither operation is language garbage collection.

---

# 116. Memory archival

Old memory can move to lower-cost storage.

---

# 117. Archive tiers

```text
Hot
Warm
Cold
External
```

---

# 118. Retrieval across tiers

Search can fan out within bounded limits.

---

# 119. Cold retrieval

May have larger latency.

---

# 120. Latency budget

Context builder respects deadline.

---

# 121. Retrieval timeout

Partial result marked.

---

# 122. Memory failure

Failure policy:

```text
Fail
Degrade
UseRecent
UseCache
ContinueWithoutMemory
```

---

# 123. Memory availability

Agent must know whether memory was unavailable.

---

# 124. No silent memory failure

A response cannot pretend memory was consulted if it was not.

---

# 125. Memory provenance flag

```text
MemoryAvailable
MemoryPartial
MemoryUnavailable
```

---

# 126. Memory hallucination prevention

Model context can include:

```text
memory_status
source
revision
```

---

# 127. Agent memory tools

644 may expose:

```text
memory.search
memory.get
memory.store
memory.update
memory.forget
memory.link
memory.explain
```

---

# 128. Tool authorization

Each operation requires capability.

---

# 129. Memory write policy

Writes may require:

```text
Auto
Approval
Evidence
Policy
```

---

# 130. Memory write deduplication

Use content/source fingerprint.

---

# 131. Idempotent write

Repeated event should not create unbounded duplicates.

---

# 132. Event identity

634 EventId can be used as dedup key.

---

# 133. Workflow memory

629 workflows can persist durable cognitive state.

---

# 134. Workflow memory distinction

Workflow state ≠ cognitive memory.

---

# 135. Simulation memory

648 episodes can be stored as episodic memory.

---

# 136. Simulation provenance

Simulation memories must identify:

```text
simulation
scenario
seed
model
environment
```

---

# 137. Multimodal memory

649 representations can be attached.

---

# 138. Image memory

Store reference + embedding + region metadata.

---

# 139. Audio memory

Store reference + timestamps + embedding.

---

# 140. Video memory

Store reference + temporal spans + embeddings.

---

# 141. Speech memory

Store transcript + audio reference + alignment.

---

# 142. Sensor memory

Store typed measurements + timestamp.

---

# 143. Graph memory

645 references.

---

# 144. Structured memory

612/628 records.

---

# 145. Memory embeddings

Embedding generated through 643/649.

---

# 146. Embedding model identity

Mandatory.

---

# 147. Embedding invalidation

Model version changes can require re-embedding.

---

# 148. Re-embedding job

630/629.

---

# 149. Dual embeddings

Old/new embedding versions may coexist during migration.

---

# 150. Index migration

641 supports blue/green index generation.

---

# 151. Memory schema

612 defines serializable schema.

---

# 152. Memory schema version

Required.

---

# 153. Migration

Explicit migration only.

---

# 154. Memory API

```text id="f9v6e3"
MemoryStore
MemoryNamespace
MemoryRecord
MemoryQuery
MemoryHit
MemoryRelation
MemoryPolicy
MemorySnapshot
ContextBuilder
Context
Consolidator
MemoryIndex
MemoryArchive
```

---

# 155. MemoryStore

```text
put
get
update
delete
search
link
snapshot
restore
```

---

# 156. Atomic update

Expected generation required for concurrent update.

---

# 157. Stale update

Returns conflict.

---

# 158. Snapshot

Immutable.

---

# 159. Restore

Governance/security validated before activation.

---

# 160. Distributed memory

628 stores replicated memory.

---

# 161. Consistency

Supported:

```text
Local
Session
Causal
Quorum
Linearizable
Eventual
```

where backend supports.

---

# 162. Memory session consistency

Agent session can maintain session token.

---

# 163. Offline memory

Edge agent can continue with local memory.

---

# 164. Reconnect

Offline memory syncs using revision/conflict semantics.

---

# 165. Federation

Cross-cluster memory sharing is explicit.

---

# 166. Cross-tenant memory

Denied by default.

---

# 167. Cross-agent sharing

Explicit capability.

---

# 168. Memory leases

Temporary access can expire.

---

# 169. Read-only memory

Useful for shared knowledge.

---

# 170. Immutable memory

Historical evidence can be immutable.

---

# 171. Memory lock

Optional concurrency mechanism.

---

# 172. Memory transaction

Atomic multi-record update within declared scope.

---

# 173. Cross-store transaction

Not assumed.

---

# 174. Outbox

634 can publish memory-change events.

---

# 175. Event

```text
MemoryCreated
MemoryUpdated
MemorySuperseded
MemoryArchived
MemoryDeleted
MemoryConflict
MemoryConsolidated
MemoryRetrieved
ContextBuilt
```

---

# 176. Audit

Sensitive memory access can be audited.

---

# 177. Retrieval logging

Can record metadata without storing payload.

---

# 178. Privacy

Payload logging disabled by default.

---

# 179. Secret memory

Secret material should use 638/610 rather than ordinary memory.

---

# 180. Secret references

Memory can contain `SecretRef`, not plaintext secret.

---

# 181. Credential separation

Memory cannot become credential store.

---

# 182. Policy

639 can restrict:

```text
memory read
memory write
memory export
memory forget
memory share
```

---

# 183. Governance

640 controls:

- classification;
- residency;
- retention;
- lineage;
- deletion.

---

# 184. Residency

Memory replica must satisfy residency.

---

# 185. Retention

Memory expiry cannot exceed policy.

---

# 186. Hold

Legal/operational hold represented by 640.

---

# 187. Deletion propagation

Derived indexes/embeddings must follow policy.

---

# 188. Memory quarantine

Potentially unsafe memory can be quarantined.

---

# 189. Quarantine reason

```text
Security
Governance
Quality
Conflict
UntrustedSource
Corruption
```

---

# 190. Memory quality

646 can evaluate memory retrieval/grounding.

---

# 191. Retrieval benchmark

Metrics:

```text
Recall@K
Precision@K
MRR
nDCG
GroundedRecall
```

---

# 192. Memory benchmark

Measures:

- retrieval latency;
- hit quality;
- context usefulness;
- stale rate.

---

# 193. No universal memory quality score

Metrics remain task-specific.

---

# 194. Agent evaluation

644 trajectories can identify:

```text
memory_used
memory_missed
memory_misled
```

---

# 195. Memory attribution

Agent step can reference memory IDs.

---

# 196. Memory-assisted reasoning

System can distinguish:

```text
model knowledge
retrieved memory
tool observation
user statement
```

---

# 197. Source hierarchy

Application chooses precedence.

---

# 198. No automatic truth hierarchy

Runtime does not declare that one source is universally superior.

---

# 199. Memory instruction injection

Stored memory may contain malicious text.

---

# 200. Memory as data

Memory content is never automatically system-level instruction.

---

# 201. Instruction provenance

System/instruction/task memory has explicit trust class.

---

# 202. Agent context policy

644 decides what memory can become instruction/context.

---

# 203. Procedural memory safety

Procedures retrieved from memory remain untrusted until policy permits execution.

---

# 204. Tool memory

Tool results stored with tool identity/version.

---

# 205. Tool result expiry

Some tool observations become stale.

---

# 206. Freshness

Memory may specify:

```text
fresh_until
max_age
```

---

# 207. Stale retrieval

Stale memory can be returned only if policy allows.

---

# 208. Freshness-aware context

Context builder can require:

```text
max_age
```

---

# 209. Revalidation

644 can call tool to validate stale memory.

---

# 210. Memory-triggered action

Memory retrieval alone cannot trigger external action.

---

# 211. Memory-triggered workflow

Requires explicit 629 workflow.

---

# 212. Memory-triggered event

Requires explicit event rule.

---

# 213. Context cache

Context can be cached.

---

# 214. Context cache key

Includes:

```text
memory revisions
model version
context policy
governance revision
```

---

# 215. Cache invalidation

Memory revision invalidates dependent context.

---

# 216. Context snapshot

Can be persisted for reproducibility.

---

# 217. Snapshot contents

```text
memory IDs
revisions
selected evidence
builder config
model
```

---

# 218. Context replay

646 can reproduce model evaluation using snapshot.

---

# 219. Context diff

Compare two context builds.

---

# 220. Context explain

Explain:

```text
why included
why excluded
why compressed
why truncated
```

---

# 221. Memory explain

Explain:

```text
source
revision
retrieval signals
policy
governance
```

---

# 222. Memory graph traversal

641/645 can support related memory discovery.

---

# 223. Memory relationship indexing

641/645.

---

# 224. Semantic clustering

642/643.

---

# 225. Automatic clustering

Must not change memory truth status.

---

# 226. Topic extraction

Derived metadata.

---

# 227. Summaries

Derived memory.

---

# 228. Summary revision

When source memories change, summary becomes stale.

---

# 229. Stale derived memory

Marked `Superseded` or `Stale`.

---

# 230. Dependency graph

Derived memory references source revisions.

---

# 231. Recompute

Consolidation can regenerate derived memory.

---

# 232. Incremental consolidation

Only changed source ranges need processing.

---

# 233. Distributed consolidation

630.

---

# 234. Consolidation scheduling

629.

---

# 235. Consolidation resources

606.

---

# 236. Consolidation events

634.

---

# 237. Consolidation observability

633.

---

# 238. Memory service

631 can expose memory through service API.

---

# 239. Gateway

632 can expose controlled remote memory APIs.

---

# 240. Deployment

636 deploys memory services.

---

# 241. Cluster placement

635.

---

# 242. Package

625.

---

# 243. Configuration

601/637.

---

# 244. Credentials

638.

---

# 245. Crypto

610.

---

# 246. Storage

611.

---

# 247. Serialization

612.

---

# 248. Compression

613.

---

# 249. IPC

604.

---

# 250. Scheduling

607.

---

# 251. Synchronization

608.

---

# 252. Network

609.

---

# 253. Diagnostics

602.

---

# 254. Resource governance

606.

---

# 255. Security

603.

---

# 256. Policy

639.

---

# 257. Governance

640.

---

# 258. Search

641.

---

# 259. Analytics

642.

---

# 260. ML

643.

---

# 261. Agent

644.

---

# 262. Knowledge

645.

---

# 263. Evaluation

646.

---

# 264. Lifecycle

647.

---

# 265. Simulation

648.

---

# 266. Multimodal

649.

---

# 267. Compiler metadata

```text id="0g6gla"
@memory
@memory_namespace
@working_memory
@episodic
@semantic_memory
@procedural_memory
@long_term
@memory_source
@memory_relation
@evidence
@remember
@forget
@retention
@importance
@decay
@consolidate
@context
@context_section
@retrieval
@memory_index
@memory_policy
@memory_snapshot
```

---

# 268. Generated files

```text id="0j9b9a"
.axmemory
.axmemschema
.axmemindex
.axepisode
.axsemantic
.axprocedure
.axcontext
.axmemorypolicy
.axmemsnapshot
.axconsolidation
```

---

# 269. CLI

```text id="q9cb0c"
axiom memory list
axiom memory inspect
axiom memory get
axiom memory search
axiom memory explain
axiom memory conflicts
axiom memory lineage
axiom memory archive
axiom memory restore
axiom memory forget
axiom memory consolidate
axiom memory reindex
axiom memory snapshot
axiom memory diff-context
axiom memory trace
```

---

# 270. Errors

```text
MemoryNotFound
MemoryGenerationConflict
MemorySchemaMismatch
MemoryPolicyDenied
MemoryGovernanceViolation
MemoryResidencyViolation
MemoryRetentionConflict
MemoryQuarantined
MemoryCorrupt
MemoryUnavailable
MemoryTimeout
MemoryBudgetExceeded
ContextBudgetExceeded
ContextOverflow
RetrievalFailed
RetrievalPartial
ConsolidationFailed
ConsolidationConflict
StaleDerivedMemory
EmbeddingVersionMismatch
NamespaceDenied
CrossTenantAccess
```

---

# 271. Provider architecture

```text
NativeMemoryProvider
LocalMemoryProvider
DistributedMemoryProvider
SearchMemoryProvider
GraphMemoryProvider
ExternalMemoryProvider
TestMemoryProvider
```

---

# 272. Local provider

Có thể dùng:

```text
611
612
641
```

---

# 273. Distributed provider

628.

---

# 274. Graph provider

645.

---

# 275. Vector provider

641.

---

# 276. External provider

Adapter tới external memory/vector/database services.

---

# 277. Provider authority

Provider không thể mở rộng capability.

---

# 278. Provider consistency

Provider phải khai báo consistency.

---

# 279. Provider durability

Provider phải khai báo durability.

---

# 280. Provider retention

640 remains authoritative.

---

# 281. Memory API example

```text
memory := MemoryStore.open("agent.main")

memory.put(
    MemoryRecord {
        kind: Episodic,
        payload: event,
        source: Tool,
        importance: 0.8
    }
)
```

---

# 282. Retrieval example

```text
hits := memory.search(
    MemoryQuery {
        kind: Episodic,
        query: "previous deployment failure",
        limit: 8
    }
)
```

---

# 283. Context example

```text
context := ContextBuilder()
    .retrieve(hits)
    .add_recent(session)
    .add_evidence(evidence)
    .compress()
    .pack(model)
```

---

# 284. Forget example

```text
memory.forget(
    memory_id,
    expected_generation
)
```

---

# 285. Consolidation example

```text
consolidator.run(
    namespace,
    session_range,
    ConsolidationPolicy {
        preserve_evidence: true,
        require_verification: true
    }
)
```

---

# 286. Multimodal example

```text
memory.put(
    MemoryRecord {
        kind: Episodic,
        payload: {
            text: transcript,
            image: image_ref,
            audio: audio_ref
        }
    }
)
```

---

# 287. AI-friendly representation

Memory metadata được compiler xuất dưới dạng schema-readable artifacts.

---

# 288. Static inspection

Compiler có thể kiểm tra:

- memory type;
- schema;
- source;
- retention;
- namespace;
- capability requirements.

---

# 289. Generated accessors

Typed memory schema có thể sinh accessor compile-time.

---

# 290. Reflection

Không bắt buộc runtime reflection.

---

# 291. ABI

Memory provider API có stable ABI boundary.

---

# 292. FFI

External memory providers có FFI adapter.

---

# 293. Performance

Hot path:

```text
retrieve
get
put
context-build
```

phải allocation-conscious.

---

# 294. Locking

Không dùng global mutex cho toàn memory system.

---

# 295. Sharding

Namespace/key based sharding.

---

# 296. Cache

Local hot-memory cache.

---

# 297. Prefetch

Có thể prefetch memory theo session.

---

# 298. Admission

Không prefetch unbounded.

---

# 299. Backpressure

Memory retrieval phải obey 606/607.

---

# 300. Large payload

Media không nên được copy vào memory record nếu reference đủ.

---

# 301. Reference semantics

`MediaRef` là stable reference, không phải raw pointer.

---

# 302. Memory-safe handles

Generation-safe handles.

---

# 303. No raw pointer

Public API không expose raw memory pointers.

---

# 304. Checkpoint

600 có thể checkpoint:

```text
working memory
context snapshot
consolidation state
```

---

# 305. Restore

Restore phải validate:

```text
schema
generation
policy
governance
model compatibility
```

---

# 306. Agent restart

Agent có thể khôi phục persistent memory mà không khôi phục capability.

---

# 307. Security invariant

Restored memory never restores authority.

---

# 308. Workflow restart

629 có thể restore workflow memory.

---

# 309. Simulation replay

648 có thể restore episodic memory associated with simulation.

---

# 310. Evaluation replay

646 có thể use context snapshot + memory revisions.

---

# 311. Reproducibility

Memory snapshot + model revision + context policy enables reproducible evaluation where model/provider is deterministic.

---

# 312. Model drift

Memory remains independent from model version.

---

# 313. Re-embedding

Model change may require new embeddings.

---

# 314. Memory semantic migration

Model may change summary/semantic representation.

Historical raw memory remains where retention permits.

---

# 315. Dual representation

Raw + derived summary can coexist.

---

# 316. Lossless archive

Important memories can retain source data.

---

# 317. Lossy archive

Summaries may be retained when source retention permits.

---

# 318. Importance policy

Application-defined.

---

# 319. Decay policy

Application-defined.

---

# 320. No anthropomorphic semantics

Runtime does not claim that memory constitutes consciousness, identity, emotion, or personhood.

---

# 321. Cognitive-state terminology

"Cognitive state" is an engineering abstraction.

---

# 322. Memory identity

Agent identity is not derived solely from memory.

---

# 323. Agent lifecycle

644 controls agent generation.

---

# 324. Memory lifecycle

650 controls memory generation.

---

# 325. Separation

Agent restart does not necessarily create new memory identity.

---

# 326. Multi-agent memory

Shared memory has explicit namespace and access policy.

---

# 327. Memory replication

628.

---

# 328. Memory conflict resolution

628 + 650.

---

# 329. Event ordering

634 event IDs and offsets.

---

# 330. Exactly-once

Not assumed.

---

# 331. Idempotency

Memory writes should use idempotency keys where needed.

---

# 332. Duplicate consolidation

Must be detectable.

---

# 333. Duplicate summaries

Can be merged/replaced via revision.

---

# 334. Memory provenance graph

645 can represent provenance relationships.

---

# 335. Memory-to-knowledge promotion

```text
Episodic
→ Evidence
→ Candidate Assertion
→ Verified Assertion
→ Knowledge Graph
```

---

# 336. Knowledge-to-memory

645 facts can become retrieval memories.

---

# 337. Memory-to-search

641 indexes memory.

---

# 338. Search-to-memory

Search result can become episodic memory if explicitly configured.

---

# 339. Model-to-memory

Model extraction creates candidate memory.

---

# 340. User-to-memory

Explicit user-provided facts can be stored according to policy.

---

# 341. No implicit permanent storage

Applications choose which data becomes long-term memory.

---

# 342. Default retention

Session memory may default to bounded lifetime.

---

# 343. Memory policy declaration

```text
MemoryPolicy {
    allowed_sources
    retention
    namespace
    verification
    sharing
    embedding
}
```

---

# 344. Policy fingerprint

Every context build can reference effective memory policy revision.

---

# 345. Dynamic policy

637 can update non-security memory behavior.

---

# 346. Security policy

603/639 remains authoritative.

---

# 347. Governance policy

640 remains authoritative for retention/residency.

---

# 348. Policy conflict

More restrictive applicable policy wins where semantics require.

---

# 349. Break-glass

Does not bypass hard security/governance constraints.

---

# 350. Memory export

Export requires capability + policy.

---

# 351. Export format

612 schema.

---

# 352. Encryption

610.

---

# 353. Credential

638.

---

# 354. Package

613/625.

---

# 355. Network

609/626.

---

# 356. Service

631.

---

# 357. Gateway

632.

---

# 358. Observability

633.

---

# 359. Cluster

635.

---

# 360. Deployment

636.

---

# 361. Dynamic control

637.

---

# 362. Trust

638.

---

# 363. Policy

639.

---

# 364. Governance

640.

---

# 365. Search

641.

---

# 366. Analytics

642.

---

# 367. ML

643.

---

# 368. Agent

644.

---

# 369. Knowledge

645.

---

# 370. Evaluation

646.

---

# 371. Model lifecycle

647.

---

# 372. Simulation

648.

---

# 373. Multimodal

649.

---

# 374. Core invariants

1. Memory identity is stable.
2. Memory generation prevents stale writes.
3. Revisions are immutable.
4. Historical revisions retain provenance.
5. Memory type is explicit.
6. Memory source is explicit.
7. Trust status is explicit.
8. Evidence is explicit.
9. Confidence is metadata.
10. Confidence is not truth.
11. Conflicts may coexist.
12. Conflict resolution is explicit.
13. Summaries are derived.
14. Derived memory references source revisions.
15. Lossy summaries are marked.
16. Semantic promotion is explicit.
17. Memory never grants capability.
18. Memory never restores authority.
19. Agent namespaces are isolated.
20. Tenant namespaces are isolated.
21. Cross-agent access is explicit.
22. Cross-tenant access is denied by default.
23. Retrieval is bounded.
24. Context construction is bounded.
25. Context overflow is explicit.
26. Memory failure is observable.
27. Partial retrieval is marked.
28. Stale memory is marked.
29. Freshness policy is explicit.
30. Retention belongs to governance.
31. Residency belongs to governance.
32. Security belongs to 603.
33. Policy belongs to 639.
34. Storage belongs to 611/628.
35. Search belongs to 641.
36. Knowledge belongs to 645.
37. Model execution belongs to 643.
38. Agent execution belongs to 644.
39. Multimodal representation belongs to 649.
40. No mandatory vector database.
41. No mandatory LLM.
42. No mandatory external memory server.
43. No mandatory GC.
44. Raw media may be referenced rather than copied.
45. Large memory operations are bounded.
46. Context caches include memory revisions.
47. Context caches include policy revisions.
48. Embeddings identify their model.
49. Re-embedding is versioned.
50. Deletion prevents resurrection.
51. Derived indexes follow deletion policy.
52. Secret material is not ordinary memory.
53. Secret references are allowed.
54. Tool outputs have provenance.
55. Model-generated memories are untrusted by default.
56. Procedures retrieved from memory are untrusted.
57. Stored instructions are not automatically system instructions.
58. Memory cannot execute code.
59. Memory cannot execute tools.
60. Memory cannot change security policy.
61. Memory cannot change governance policy.
62. Memory cannot mint identity.
63. Memory cannot mint credentials.
64. Memory cannot expand capability.
65. Memory writes can be idempotent.
66. Consolidation is checkpointable.
67. Consolidation is bounded.
68. Replay is reproducible where promised.
69. Memory schema is versioned.
70. Provider consistency is declared.
71. Provider durability is declared.
72. External provider cannot expand authority.
73. Distributed memory does not imply exactly-once.
74. Conflict resolution is deterministic when configured.
75. Context provenance is preserved.
76. Evidence spans remain addressable.
77. Memory snapshots are immutable.
78. Restore validates policy.
79. Restore validates governance.
80. Restore never restores capability.
81. Agent identity and memory identity are separate.
82. Memory lifecycle and storage compaction are separate.
83. Cognitive consolidation and database compaction are separate.
84. Forgetting is explicit.
85. Eviction cannot violate retention.
86. Archive cannot bypass governance.
87. Cross-region replication obeys residency.
88. Context truncation is observable.
89. Memory unavailability is observable.
90. No hidden global memory.
91. Struct-only public API.
92. No raw pointer public API.
93. Native implementation possible.
94. External providers are adapters.
95. Memory retrieval remains authorization-aware.
96. Memory output cannot silently cross trust boundaries.
97. Derived semantic facts preserve provenance.
98. Memory benchmarks identify dataset/revision.
99. Evaluation does not mutate memory truth.
100. Memory is an engineering data abstraction, not a claim about consciousness.

---

# 375. Acceptance target

**≥600 acceptance criteria** covering:

- memory identity;
- generation;
- revisions;
- namespaces;
- working memory;
- session memory;
- episodic memory;
- semantic memory;
- procedural memory;
- long-term memory;
- external memory;
- multimodal memory;
- evidence;
- provenance;
- trust;
- conflict;
- resolution;
- temporal memory;
- retention;
- forgetting;
- archival;
- retrieval;
- lexical search;
- vector search;
- graph search;
- hybrid retrieval;
- ranking;
- freshness;
- context engineering;
- context compression;
- context packing;
- context snapshots;
- context replay;
- context explainability;
- consolidation;
- summarization;
- semantic promotion;
- procedural validation;
- memory indexing;
- embedding migration;
- distributed replication;
- offline memory;
- synchronization;
- conflict resolution;
- privacy;
- security;
- governance;
- resource limits;
- caching;
- streaming;
- agent integration;
- workflow integration;
- simulation integration;
- multimodal integration;
- model integration;
- evaluation;
- reproducibility;
- testing;
- fuzzing;
- crash recovery;
- performance;
- scalability.

---

# 376. Profiles

```text
AXMEM_NONE

AXMEM_CORE
AXMEM_WORKING
AXMEM_SESSION
AXMEM_EPISODIC
AXMEM_SEMANTIC
AXMEM_PROCEDURAL
AXMEM_LONGTERM

AXMEM_RETRIEVAL
AXMEM_VECTOR
AXMEM_GRAPH
AXMEM_CONTEXT

AXMEM_CONSOLIDATION
AXMEM_FORGETTING
AXMEM_MULTIMODAL

AXMEM_AGENT
AXMEM_DISTRIBUTED
AXMEM_PERSISTENT
AXMEM_EVALUATION

AXMEM_FULL
```

---

# 377. Minimal profile

```text
AXMEM_CORE
```

chỉ cần:

```text
MemoryId
MemoryRecord
MemoryNamespace
MemoryStore
MemoryRevision
```

---

# 378. Embedded/edge profile

```text
AXMEM_CORE
+
AXMEM_WORKING
+
AXMEM_SESSION
+
AXMEM_RETRIEVAL
```

---

# 379. Agent profile

```text
AXMEM_WORKING
+
AXMEM_EPISODIC
+
AXMEM_SEMANTIC
+
AXMEM_CONTEXT
+
AXMEM_AGENT
```

---

# 380. Full cognitive memory profile

```text
AXMEM_FULL
```

bao gồm persistent distributed multimodal memory và consolidation.

---

# 381. Architecture diagram

```text
                         AXIOM AI MEMORY

                         ┌─────────────┐
                         │    644      │
                         │    Agent    │
                         └──────┬──────┘
                                │
                                ▼
                    ┌─────────────────────┐
                    │        650          │
                    │   Memory Runtime    │
                    └──────────┬──────────┘
                               │
          ┌────────────────────┼────────────────────┐
          ▼                    ▼                    ▼
   ┌─────────────┐      ┌─────────────┐      ┌─────────────┐
   │   Working   │      │ Long-Term   │      │   Context   │
   │   Memory    │      │   Memory    │      │   Builder   │
   └──────┬──────┘      └──────┬──────┘      └──────┬──────┘
          │                     │                    │
          ▼                     ▼                    ▼
      Session              ┌───────────┐        643 Model
                           │ Episodic  │
                           │ Semantic  │
                           │Procedural │
                           └─────┬─────┘
                                 │
                    ┌────────────┼─────────────┐
                    ▼            ▼             ▼
                   641          645           628
                 Search       Knowledge      Storage
                    │            │             │
                    └────────────┼─────────────┘
                                 │
                                 ▼
                         649 Multimodal
                                 │
                                 ▼
                         646 Evaluation
```

---

# 382. End-to-end cognitive data flow

```text
Observation
    ↓
Event / Tool / User Input
    ↓
Working Memory
    ↓
Episodic Memory
    ↓
Consolidation
    ↓
Semantic / Procedural Memory
    ↓
Search + Knowledge Graph
    ↓
Context Builder
    ↓
Multimodal Context
    ↓
643 Model
    ↓
644 Agent
    ↓
Action / Tool
    ↓
New Observation
    ↓
Memory
```

---

# 383. Kết quả

BOOTSTRAP-650 bổ sung lớp còn thiếu giữa:

```text
Raw Data
    ↓
Knowledge
    ↓
Model
    ↓
Agent
```

và:

```text
Experience
    ↓
Memory
    ↓
Retrieval
    ↓
Context
    ↓
Decision
    ↓
New Experience
```

Axiom vì vậy có thể hỗ trợ agent có **persistent, versioned, provenance-aware, multimodal, distributed memory** mà không cần phụ thuộc vào một "memory server" bên ngoài.

Đặc biệt, kiến trúc giữ rõ ba lớp:

```text
Storage      = nơi dữ liệu tồn tại
Knowledge    = dữ liệu có semantic structure
Memory       = dữ liệu được quản lý theo cognitive/use context
```

Ba khái niệm này không bị trộn thành một database abstraction duy nhất.

---

# 384. Trạng thái

**BOOTSTRAP-650 — COMPLETE**

### Task kế tiếp

**BOOTSTRAP-651 — Native AI Personalization, User/Agent Profiles, Preference Learning, Recommendation, Ranking, Adaptive Behavior & Online Learning Runtime 5.0**
:::