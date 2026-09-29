# BOOTSTRAP-568 — COMPILER BUILD ORCHESTRATOR 3.0 — DAG EXECUTION ENGINE, SPECULATIVE COMPILATION, CRITICAL-PATH SCHEDULING, RESOURCE-AWARE PARALLELISM & ADAPTIVE BUILD

**Trạng thái: COMPLETED / LOCKED**

`568` khóa execution engine ở tầng trên `567`. Mục tiêu là biến Build DAG thành một hệ thống thực thi **song song tối đa nhưng deterministic**, phục vụ cả IDE latency thấp lẫn CI throughput cao.

Nguyên tắc:

> **Scheduler được phép thay đổi cách thực thi, nhưng tuyệt đối không được thay đổi kết quả build.**

---

## 568.1. Kiến trúc tổng thể

```text
                    Build Snapshot
                          │
                          ▼
                   Build Graph 2.0
                          │
                          ▼
                 ┌─────────────────┐
                 │ DAG Analyzer    │
                 ├─────────────────┤
                 │ Dependencies    │
                 │ SCC             │
                 │ Critical Path   │
                 │ Cost Model      │
                 │ Resource Needs  │
                 │ Cache State     │
                 └────────┬────────┘
                          ▼
                 ┌─────────────────┐
                 │ Orchestrator    │
                 ├─────────────────┤
                 │ Ready Queue     │
                 │ Priority Queue  │
                 │ Resource Pool   │
                 │ Speculation     │
                 │ Cancellation    │
                 └────────┬────────┘
                          ▼
                 Local / Remote Workers
                          │
                          ▼
                    Result Verify
                          │
                          ▼
                    Artifact Store
```

---

# 568.2. Execution unit

Đơn vị thực thi vẫn là `Action` của `567`.

Orchestrator không được trực tiếp thay đổi semantics của Action.

---

# 568.3. Action state machine

```text
PENDING
  ↓
BLOCKED
  ↓
READY
  ↓
DISPATCHED
  ↓
RUNNING
  ├── SUCCESS
  ├── FAILED
  ├── CANCELLED
  └── LOST
```

---

# 568.4. Cache state

Trước `READY`, action có thể chuyển:

```text
CACHE_CHECK
    ↓
HIT → VERIFIED
MISS → READY
```

---

# 568.5. Verified state

Artifact cache hit chỉ được coi là hoàn thành sau validation.

---

# 568.6. Dependency counters

Mỗi action duy trì:

```text
remaining_dependencies
```

Khi về `0` → `READY`.

---

# 568.7. Dependency failure

Nếu required dependency thất bại:

```text
BLOCKED_BY_FAILURE
```

action downstream không được chạy.

---

# 568.8. DAG invariant

Build graph phải là DAG sau khi SCC/cyclic compilation units đã được collapse theo compiler rules.

---

# 568.9. SCC

Strongly Connected Components được xử lý thành logical scheduling unit khi semantic dependency cho phép cycle.

---

# 568.10. SCC atomicity

Một SCC không được coi là complete cho tới khi toàn bộ required members hoàn thành.

---

# 568.11. Critical path

Mỗi action có:

```text
critical_cost
```

xấp xỉ chi phí lớn nhất từ action tới build completion.

---

# 568.12. Critical-path priority

Ready actions trên critical path được ưu tiên.

---

# 568.13. Critical path không bắt buộc

Critical-path analysis chỉ là scheduling hint.

---

# 568.14. Cost model

Cost có thể dựa trên:

- historical duration;
- input size;
- IR size;
- function count;
- template/generic expansion;
- LTO complexity;
- target backend;
- cache locality.

---

# 568.15. Cost model identity

Cost prediction không thuộc artifact identity.

---

# 568.16. Historical statistics

Orchestrator có thể lưu:

```text
ActionClass → duration distribution
```

---

# 568.17. Cold-start estimation

Nếu không có history, dùng static estimate.

---

# 568.18. Adaptive estimation

Sau mỗi execution, estimator được cập nhật.

---

# 568.19. Scheduler modes

```text
Interactive
Balanced
Throughput
MemoryBound
LowPower
DeterministicDebug
```

---

# 568.20. Interactive mode

Ưu tiên:

```text
user-requested file
↓
direct dependencies
↓
diagnostics
↓
background work
```

---

# 568.21. Throughput mode

Ưu tiên utilization và critical path.

---

# 568.22. Low-power mode

Giới hạn parallelism để giảm CPU/power.

---

# 568.23. MemoryBound mode

Giới hạn concurrent high-memory actions.

---

# 568.24. Scheduler policy

Scheduler policy có thể thay đổi execution order nhưng không được thay đổi artifact semantics.

---

# 568.25. Parallelism budget

```text
max_parallel_actions
```

là runtime configuration.

---

# 568.26. CPU budget

```text
cpu_parallelism
```

không nhất thiết bằng số CPU cores.

---

# 568.27. Memory budget

Orchestrator phải theo dõi estimated peak memory.

---

# 568.28. Memory admission

Action chỉ được dispatch nếu resource budget cho phép.

---

# 568.29. Memory reservation

Worker nhận reservation trước khi chạy high-memory action.

---

# 568.30. Oversubscription

CPU oversubscription phải được kiểm soát.

---

# 568.31. Nested parallelism

Compiler action có thể tự parallelize.

Orchestrator phải biết hoặc giới hạn nested parallelism.

---

# 568.32. Parallelism tokens

Có thể dùng token model:

```text
CPU tokens
Memory tokens
GPU tokens
IO tokens
```

---

# 568.33. CPU token

Một action tiêu thụ số CPU tokens tương ứng estimated concurrency.

---

# 568.34. GPU token

GPU action yêu cầu explicit GPU resources.

---

# 568.35. GPU memory

GPU memory là resource riêng.

---

# 568.36. IO budget

Large artifact transfers phải có bandwidth/IO scheduling.

---

# 568.37. Locality

Scheduler ưu tiên worker có artifact inputs.

---

# 568.38. Cache locality

Cache hit có thể được ưu tiên hơn execution.

---

# 568.39. Transfer avoidance

Không dispatch remote nếu transfer cost lớn hơn expected execution benefit, trừ policy override.

---

# 568.40. Worker affinity

Action có thể có affinity:

```text
none
artifact-local
CPU-local
NUMA-local
GPU-local
```

---

# 568.41. NUMA

Compiler daemon trên NUMA host có thể bind worker memory/threads theo NUMA node.

---

# 568.42. NUMA correctness

NUMA placement không được ảnh hưởng semantics.

---

# 568.43. Work stealing

Worker không có việc có thể lấy ready action từ queue khác.

---

# 568.44. Work stealing policy

Steal ưu tiên action phù hợp resource capability.

---

# 568.45. Queue hierarchy

```text
Global Ready Queue
       │
       ├── Critical
       ├── Interactive
       ├── Normal
       └── Background
             ↓
       Worker-local queues
```

---

# 568.46. Priority aging

Background action không được starvation vô hạn.

---

# 568.47. Priority inheritance

Dependent critical action có thể nâng priority của prerequisite.

---

# 568.48. Priority inversion

Scheduler phải hạn chế priority inversion.

---

# 568.49. Batching

Các actions nhỏ có thể batch để giảm scheduler overhead.

---

# 568.50. Batch correctness

Batching không được thay đổi observable semantics.

---

# 568.51. Query batching

Semantic queries cùng snapshot có thể batch.

---

# 568.52. Frontend batching

Nhiều modules có thể lexical/parse song song.

---

# 568.53. Codegen batching

Functions nhỏ có thể grouped cho worker efficiency.

---

# 568.54. Link preprocessing

Object scanning có thể batch.

---

# 568.55. Speculative execution

Orchestrator có thể chạy action trước khi mọi thông tin downstream chắc chắn nếu speculation có lợi.

---

# 568.56. Speculation condition

Speculation chỉ hợp lệ nếu action inputs đã đủ xác định.

---

# 568.57. Speculative semantic query

Có thể speculate query với assumptions rõ ràng.

---

# 568.58. Speculative compile

Ví dụ:

```text
module A changed
      │
      ├── compile A
      ├── speculate B
      └── speculate C
```

---

# 568.59. Speculation validation

Khi dependency chính thức hoàn thành:

```text
assumption == actual
```

thì result có thể reuse.

---

# 568.60. Speculation invalidation

Nếu assumption khác:

```text
discard speculative result
```

---

# 568.61. Speculative cache

Speculative artifact không được public-cache trước validation.

---

# 568.62. Speculation budget

Có giới hạn:

```text
max_speculative_actions
```

---

# 568.63. Speculation economics

Scheduler chỉ speculate nếu expected saved latency > estimated wasted work.

---

# 568.64. Cancellation

Speculative action phải có thể cancel khi assumption invalidated.

---

# 568.65. Non-cancellable action

Nếu action không cancellable, result vẫn chỉ được publish nếu valid.

---

# 568.66. Waste accounting

Scheduler record speculative wasted CPU nhưng metadata không ảnh hưởng build identity.

---

# 568.67. Interactive speculation

IDE có thể speculate compilation of likely next dependencies.

---

# 568.68. CI speculation

CI mặc định có thể disable speculation nếu throughput economics không có lợi.

---

# 568.69. Adaptive speculation

Scheduler học từ historical hit rate.

---

# 568.70. Bad speculation

Repeated low-value speculation phải bị giảm priority hoặc disabled.

---

# 568.71. Prefetch

Artifact prefetch được coi là asynchronous background work.

---

# 568.72. Prefetch correctness

Prefetch không được trở thành hidden semantic input.

---

# 568.73. Remote cache prefetch

Có thể tải trước artifacts dự kiến cần.

---

# 568.74. Dependency prefetch

Scheduler có thể prefetch dependency artifacts khi parent action được scheduled.

---

# 568.75. Cache prediction

Có thể dự đoán cache hit nhưng chỉ verified hit mới complete.

---

# 568.76. Build criticality

Action có thể được đánh dấu:

```text
critical
normal
optional
background
```

---

# 568.77. Optional work

Debug index, documentation, profiling metadata có thể chạy sau final executable nếu policy cho phép.

---

# 568.78. Required work

Final executable/link artifact không được publish trước required actions.

---

# 568.79. Background work

Background actions không được làm chậm interactive diagnostics nếu resources constrained.

---

# 568.80. Fairness

Scheduler phải đảm bảo bounded starvation.

---

# 568.81. Deadlock prevention

Resource acquisition order phải tránh scheduler-induced deadlock.

---

# 568.82. Resource cycle

Không được tạo:

```text
A waits B resource
B waits A resource
```

---

# 568.83. Admission control

Action được admission trước execution.

---

# 568.84. Resource release

Resources phải được release ngay khi action kết thúc.

---

# 568.85. Lost worker

Action chuyển sang retry queue nếu worker mất.

---

# 568.86. Retry backoff

Repeated worker failure dùng exponential backoff có giới hạn.

---

# 568.87. Retry storm

Coordinator phải chống retry storm.

---

# 568.88. Duplicate execution

Speculative và retry có thể tạo duplicate execution.

Kết quả phải deduplicate bằng `ActionId`.

---

# 568.89. First valid result

First verified valid result có thể commit.

---

# 568.90. Later duplicate

Duplicate result sau commit phải verify equivalence hoặc discard.

---

# 568.91. Nondeterministic duplicate

Mismatch → `BUILD_INCONSISTENCY`.

---

# 568.92. Failure classification

```text
SourceFailure
ToolFailure
WorkerFailure
ResourceFailure
NetworkFailure
ArtifactFailure
InfrastructureFailure
```

---

# 568.93. Source failure

Không retry vô hạn.

---

# 568.94. Infrastructure failure

Có thể retry.

---

# 568.95. Resource failure

Có thể reschedule với resource profile khác.

---

# 568.96. Worker failure

Có thể retry worker khác.

---

# 568.97. Artifact failure

Artifact phải quarantine.

---

# 568.98. Quarantine

Artifact suspect không được enter trusted cache.

---

# 568.99. Build snapshot binding

Mọi action thuộc snapshot:

```text
BuildSnapshotId
```

---

# 568.100. Snapshot isolation

Một build snapshot không được consume result của snapshot khác nếu compatibility chưa verified.

---

# 568.101. Incremental rebuild

Change detection từ `566` tạo dirty actions.

---

# 568.102. Dirty propagation

Dirty state truyền theo dependency graph.

---

# 568.103. Minimal rebuild

Chỉ dirty/required downstream actions mới cần chạy.

---

# 568.104. Cache dominance

Cache hit loại bỏ execution nhưng không loại bỏ dependency validation.

---

# 568.105. Clean build

Scheduler phải support zero-cache build.

---

# 568.106. Warm build

Scheduler phải support high-cache-hit build.

---

# 568.107. Partial cache

Scheduler phải handle arbitrary cache availability.

---

# 568.108. Cache storm

Nhiều actions miss cùng lúc phải avoid remote-store overload.

---

# 568.109. Cache lookup batching

Có thể lookup nhiều ActionIds một request.

---

# 568.110. Artifact transfer batching

Có thể request nhiều chunks/artifacts trong batch.

---

# 568.111. Build graph persistence

Coordinator có thể persist graph execution state.

---

# 568.112. Crash recovery

Sau restart:

```text
completed verified actions
```

được giữ.

---

# 568.113. Unknown running actions

Sau coordinator restart, in-flight actions trở thành unknown và phải verify/retry.

---

# 568.114. Orphan actions

Worker có thể finish action sau coordinator restart.

Result được nhận nếu ActionId vẫn valid.

---

# 568.115. Lease

Running action có execution lease.

---

# 568.116. Lease expiration

Expired lease cho phép retry.

---

# 568.117. Duplicate lease

Hai workers có thể execute same action; artifact identity resolves conflict.

---

# 568.118. Build cancellation

User cancel build → scheduler stop dispatching new actions.

---

# 568.119. Cancellation propagation

Cancellation truyền xuống speculative/background actions trước required completed actions.

---

# 568.120. Graceful cancellation

Worker được signal để cleanup.

---

# 568.121. Hard cancellation

Policy có thể terminate worker process.

---

# 568.122. Cleanup

Temporary outputs không được publish.

---

# 568.123. Interactive priority

User-triggered diagnostic action có thể preempt background actions.

---

# 568.124. Preemption

Preemption ưu tiên cancellable work.

---

# 568.125. Non-preemptible actions

Long codegen/link actions có thể finish thay vì restart nếu gần hoàn thành.

---

# 568.126. Completion-aware scheduling

Scheduler có thể tránh preempt action gần completion.

---

# 568.127. Latency target

Interactive build tối ưu time-to-first-diagnostic.

---

# 568.128. First diagnostic

Compiler không cần chờ toàn bộ build để report independent diagnostic.

---

# 568.129. Diagnostic dependency

Diagnostic action chạy ngay khi required semantic facts available.

---

# 568.130. IDE responsiveness

Background distributed work không được block daemon query path.

---

# 568.131. LSP integration

LSP request có priority class cao hơn background build.

---

# 568.132. Query cancellation

Stale IDE queries có thể cancel.

---

# 568.133. Query coalescing

Hai identical semantic queries có thể share computation.

---

# 568.134. Query deduplication

Same query/snapshot được deduplicate.

---

# 568.135. Build deduplication

Hai build requests cùng BuildSnapshot có thể share actions.

---

# 568.136. Multi-client daemon

Nhiều IDE/CLI clients có thể attach cùng daemon.

---

# 568.137. Fair client scheduling

Một client không được monopolize toàn bộ resources trừ explicit policy.

---

# 568.138. Build priorities

```text
Foreground
Normal
Background
Maintenance
```

---

# 568.139. Maintenance

Cache GC/index rebuild chạy low priority.

---

# 568.140. Remote worker selection

Worker score có thể dựa trên:

```text
capability
cache locality
latency
load
estimated completion
```

---

# 568.141. Worker score

Worker score chỉ scheduling metadata.

---

# 568.142. Worker failure history

Có thể lower worker scheduling preference.

---

# 568.143. Worker quarantine

Repeated integrity failures có thể quarantine worker.

---

# 568.144. Worker trust escalation

Worker phải pass verification trước khi được trusted-cache publisher.

---

# 568.145. Resource-aware remote scheduling

Scheduler cân bằng:

```text
compute_cost
transfer_cost
queue_delay
cache_locality
```

---

# 568.146. Cost formula

Conceptually:

```text
estimated_completion =
queue_delay
+ transfer_time
+ execution_time
+ verification_time
```

---

# 568.147. No semantic dependence

Cost formula không được ảnh hưởng artifact contents.

---

# 568.148. Adaptive concurrency

Scheduler tăng/giảm concurrency dựa trên:

- CPU saturation;
- memory pressure;
- IO;
- worker queue;
- observed action duration.

---

# 568.149. Memory pressure

Memory pressure phải trigger throttling trước OOM.

---

# 568.150. OOM recovery

Một OOM action có thể retry với lower concurrency hoặc larger worker.

---

# 568.151. Compilation locality

Related actions có thể được colocated để giảm transfer.

---

# 568.152. Module locality

Một package/module group có thể ưu tiên cùng worker.

---

# 568.153. LTO locality

LTO partitions có thể colocate với required IR.

---

# 568.154. Link locality

Final linker chạy nơi có object set tối ưu nhất.

---

# 568.155. Large build strategy

Build lớn phải tránh đưa toàn bộ DAG/artifacts vào RAM.

---

# 568.156. Streaming graph

DAG metadata có thể stream/page.

---

# 568.157. Lazy graph materialization

Only reachable actions cần cho current goal mới materialize.

---

# 568.158. Goal-directed build

Build request xác định root targets.

---

# 568.159. Unreachable actions

Không schedule actions không nằm trong dependency closure của requested goal.

---

# 568.160. Multiple goals

Nhiều targets share common action nodes.

---

# 568.161. Shared execution

Common ActionId chỉ cần execute một lần.

---

# 568.162. Artifact reuse

Một artifact có thể serve nhiều downstream builds nếu identity compatible.

---

# 568.163. Build graph canonicalization

Equivalent build requests phải canonicalize thành compatible action graph.

---

# 568.164. Scheduler persistence

Historical scheduling data có thể persist nhưng không phải semantic source.

---

# 568.165. Model update

Cost model có thể update online.

---

# 568.166. Model corruption

Corrupt scheduling model phải fallback static policy.

---

# 568.167. Safe fallback

Compiler correctness không phụ thuộc ML scheduler.

---

# 568.168. AI scheduler

AI/ML prediction có thể hỗ trợ scheduling.

---

# 568.169. AI authority

AI scheduler không được thay đổi dependency graph semantics.

---

# 568.170. AI failure

AI scheduling failure phải fallback deterministic heuristic.

---

# 568.171. Deterministic debug mode

Debug mode có thể force stable scheduling order để forensic analysis.

---

# 568.172. Stable scheduler

Stable mode sort bằng canonical ActionId.

---

# 568.173. Stable order

Stable order không phải requirement của artifact correctness, chỉ debugging/reproducibility aid.

---

# 568.174. Trace

Scheduler trace record:

```text
action
timestamp
worker
queue
reason
resource
cache_state
```

---

# 568.175. Trace privacy

Trace không được chứa source secrets ngoài explicit policy.

---

# 568.176. Build visualization

Graph có thể hiển thị:

```text
critical path
cache hits
worker assignment
resource bottlenecks
```

---

# 568.177. Bottleneck analysis

Orchestrator phải xác định:

- CPU bottleneck;
- memory bottleneck;
- IO bottleneck;
- remote latency;
- critical-path bottleneck.

---

# 568.178. Build statistics

Expose:

```text
total_actions
executed
cached
speculative
cancelled
failed
remote
local
```

---

# 568.179. Performance regression

Build orchestration metrics có thể được benchmark.

---

# 568.180. Scheduler benchmark

Benchmark:

- cold build;
- warm build;
- incremental;
- large monorepo;
- distributed;
- high-latency workers.

---

# 568.181. Synthetic DAG benchmark

Phải có DAG:

```text
wide
deep
mixed
diamond
SCC-heavy
cache-heavy
```

---

# 568.182. Stress

Test hàng triệu logical actions mà không yêu cầu triệu process đồng thời.

---

# 568.183. Worker scalability

Worker count tăng phải improve hoặc giữ nguyên throughput trong giới hạn bottleneck.

---

# 568.184. Scheduler overhead

Scheduler overhead phải bounded và measurable.

---

# 568.185. Small build optimization

Build nhỏ không được chịu overhead distributed orchestration quá lớn.

---

# 568.186. Local fast path

Nếu build nhỏ và local cache đầy đủ:

```text
fast local path
```

được phép bypass remote scheduling.

---

# 568.187. Remote fast path

Nếu artifact đã tồn tại remote cache:

```text
fetch → verify
```

không cần worker execution.

---

# 568.188. Single-file fast path

IDE save một file phải avoid reconstructing toàn bộ build graph nếu không cần.

---

# 568.189. Background completion

Các artifact không cần immediate có thể tiếp tục sau diagnostic response.

---

# 568.190. Finalization barrier

Final artifact chỉ publish sau tất cả required actions.

---

# 568.191. Link barrier

Final link action là barrier cho executable target.

---

# 568.192. Package barrier

Package action chỉ chạy sau final artifacts.

---

# 568.193. Signing barrier

Code signing chỉ chạy sau final bytes validated.

---

# 568.194. Artifact promotion

Artifact promotion:

```text
Produced
 → Verified
 → Trusted
 → Published
```

---

# 568.195. Trust boundary

Scheduler không được tự động biến untrusted result thành trusted artifact.

---

# 568.196. Correctness authority

Correctness vẫn thuộc compiler semantic/codegen/link validation layers.

---

# 568.197. Scheduler independence

Có thể thay scheduler mà không thay đổi language semantics.

---

# 568.198. Local/remote equivalence

Một build chạy:

```text
serial
parallel
local
remote
mixed
```

phải produce equivalent canonical artifacts.

---

# 568.199. Full execution equivalence

Clean build, incremental build, cache-hit build, speculative build và retry build phải converge tới cùng kết quả khi cùng logical inputs.

---

# 568.200. FINAL HARD INVARIANT

> **Axiom Build Orchestrator được phép tối ưu thứ tự, mức độ song song, worker, locality, speculation, cache usage, resource allocation và execution strategy; nhưng với cùng BuildSnapshot, Action graph, inputs, toolchain, target và policy, mọi execution strategy hợp lệ phải hội tụ về cùng canonical artifacts. Scheduler không phải semantic authority và không được trở thành một nguồn gây sai khác giữa clean/local/remote/incremental/cached/parallel builds.**

**BOOTSTRAP-568: LOCKED.**

---

# NEXT — BOOTSTRAP-569

## COMPILER DIAGNOSTIC ENGINE 3.0 — ERROR RECOVERY, MULTI-DIAGNOSTIC ANALYSIS, ERROR CASCADE SUPPRESSION, SOURCE SPANS, FIX-IT, EXPLANATION GRAPH & AI-READABLE DIAGNOSTICS

Task tiếp theo sẽ khóa **hệ thống diagnostic compiler ở cấp độ production**, không chỉ là `error: ... line ...`.

Mục tiêu:

```text
Source
  ↓
Lexer / Parser
  ↓
Semantic Engine
  ↓
Type / Trait / Ownership / Const
  ↓
Diagnostic Engine
  ├── Primary Error
  ├── Related Locations
  ├── Explanation
  ├── Fix-it
  ├── Error Recovery
  ├── Cascade Suppression
  ├── Machine-readable JSON
  ├── LSP
  └── AI Semantic Explanation
```

Đặc biệt `569` sẽ phải giải quyết một vấn đề rất quan trọng đối với Axiom:

**khi source có 1 lỗi gốc, compiler không được phun ra 50–500 lỗi giả do các phase phía sau bị nhiễm lỗi.**

Nó cũng sẽ khóa:

- diagnostic severity;
- primary/secondary span;
- source snapshot;
- Unicode/UTF-8 span chính xác;
- parser recovery;
- semantic recovery;
- placeholder/error types;
- expected-token sets;
- overload/trait-resolution explanations;
- generic inference diagnostics;
- ownership/resource diagnostics;
- `Result`/panic diagnostics;
- cross-module errors;
- dependency errors;
- ABI/FFI diagnostics;
- linker diagnostics integration;
- fix-it edits;
- safe vs unsafe automatic fixes;
- diagnostic grouping;
- cascade suppression;
- duplicate suppression;
- confidence;
- error provenance;
- JSON schema;
- LSP mapping;
- IDE code actions;
- compiler CLI rendering;
- AI-readable diagnostic graph;
- diagnostic caching;
- incremental diagnostics;
- deterministic diagnostics;
- multilingual explanation layer mà **không thay đổi diagnostic identity**;
- và test/fuzz framework cho toàn bộ diagnostic engine.

**BOOTSTRAP-569: NEXT.**