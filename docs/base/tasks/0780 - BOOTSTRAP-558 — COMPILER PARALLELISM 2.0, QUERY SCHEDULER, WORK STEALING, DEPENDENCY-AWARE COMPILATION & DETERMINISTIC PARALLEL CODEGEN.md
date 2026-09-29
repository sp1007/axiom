# BOOTSTRAP-558 — COMPILER PARALLELISM 2.0, QUERY SCHEDULER, WORK STEALING, DEPENDENCY-AWARE COMPILATION & DETERMINISTIC PARALLEL CODEGEN

**Trạng thái: COMPLETED / LOCKED**

`558` khóa kiến trúc song song hóa toàn compiler, nối trực tiếp:

- `436` — Compiler Architecture / Query System
- `487` — Build Graph 2.0
- `552` — Compiler Correctness / Translation Validation
- `555` — Compiler Daemon
- `556` — Incremental Frontend
- `557` — Compiler Memory Architecture

Mục tiêu:

> **Axiom phải tận dụng được nhiều CPU một cách mạnh mẽ, nhưng số worker, thứ tự thực thi, work stealing, cache hit/miss hoặc scheduling policy tuyệt đối không được làm thay đổi semantics của chương trình hoặc tạo ra native artifact sai khác về mặt hành vi.**

---

# 558.1. Tổng thể

```text id="a4m8x2"
                         Compiler Request
                               │
                               ▼
                     ┌──────────────────┐
                     │ Request Scheduler│
                     └────────┬─────────┘
                              │
                              ▼
                       Dependency DAG
                              │
          ┌───────────────────┼───────────────────┐
          ▼                   ▼                   ▼
      Frontend             Semantic             Backend
   Lex / Parse          Type / Trait        MIR / Codegen
          │                   │                   │
          └───────────────────┼───────────────────┘
                              ▼
                      Ready Task Queue
                              │
                ┌─────────────┼─────────────┐
                ▼             ▼             ▼
             Worker 0      Worker 1      Worker N
                │             │             │
                └─────────────┼─────────────┘
                              ▼
                       Result Validation
                              │
                              ▼
                     Deterministic Merge
                              │
                              ▼
                     Query / Artifact DB
```

---

# 558.2. Parallelism layers

Axiom có 5 tầng parallelism:

```text id="k2s7p1"
1. Request parallelism
2. File/module parallelism
3. Query parallelism
4. Function/codegen parallelism
5. Machine/backend parallelism
```

Không phải task nào cũng được parallel.

---

# 558.3. Request parallelism

Daemon có thể nhận đồng thời:

```text id="w5q1m8"
LSP request
AI query
CLI build
background indexing
```

---

# 558.4. Priority classes

```text id="x7m3q9"
Interactive
UserBuild
AIInteractive
Background
Speculative
Maintenance
```

---

# 558.5. Priority principle

Interactive work được ưu tiên nhưng không được starvation background tasks vô hạn.

---

# 558.6. Fairness

Scheduler phải có aging hoặc equivalent fairness mechanism.

---

# 558.7. Dependency DAG

Mọi query/task phải biểu diễn dependency:

```text id="n8r2v6"
Task {
    id
    kind
    inputs
    dependencies
    dependents
    priority
    resource_estimate
}
```

---

# 558.8. Task states

```text id="u4p9k2"
Created
Waiting
Ready
Running
Completed
Failed
Cancelled
Blocked
```

---

# 558.9. Ready task

Task chỉ được đưa vào runnable queue khi tất cả dependency bắt buộc đã hoàn thành.

---

# 558.10. Failed dependency

Task phụ thuộc failure phải chuyển sang:

```text id="m6q3w8"
BlockedByFailure
```

hoặc cancellation tùy policy.

---

# 558.11. Query deduplication

Hai requests cùng query identity:

```text id="p7x2k5"
Q(A)
Q(A)
```

chỉ tạo một computation.

---

# 558.12. Shared future

Consumers cùng query nhận shared future/result.

---

# 558.13. Cancellation semantics

Một consumer cancel không được cancel computation nếu còn consumer khác cần kết quả.

---

# 558.14. Last consumer cancellation

Khi không còn consumer:

```text id="d3m8v1"
computation → cancellable
```

nếu query không required cho committed build.

---

# 558.15. Build-critical query

Build-critical task không được hủy chỉ vì một IDE request biến mất.

---

# 558.16. Speculative query

Speculative task có thể bị hủy bất cứ lúc nào.

---

# 558.17. Work stealing

Worker có local deque:

```text id="f8k2m5"
Worker 0 → [A B C D]
Worker 1 → [E]
```

Worker rảnh có thể steal:

```text id="t5q9w3"
Worker 1 ← D/C
```

---

# 558.18. Locality

Worker ưu tiên task liên quan dữ liệu đã nằm trong cache/local memory.

---

# 558.19. Locality ≠ correctness

Thay đổi worker assignment không được thay đổi semantic result.

---

# 558.20. Worker count

Compiler phải hoạt động đúng với:

```text id="r3m7p2"
1 worker
2 workers
N workers
```

---

# 558.21. Auto worker count

Default worker count có thể dựa trên CPU topology và memory budget.

---

# 558.22. Memory-aware workers

`557` cung cấp estimated memory/task.

Scheduler có thể giảm concurrency nếu memory pressure cao.

---

# 558.23. CPU-aware workers

Scheduler có thể phân biệt:

```text id="y6k1q8"
performance cores
efficiency cores
logical CPUs
```

nếu platform cung cấp thông tin đáng tin cậy.

---

# 558.24. NUMA

Máy NUMA có thể sử dụng worker locality và memory locality.

---

# 558.25. NUMA correctness

NUMA placement chỉ ảnh hưởng performance.

---

# 558.26. CPU affinity

Affinity là optimization policy, không phải semantic requirement.

---

# 558.27. Oversubscription

Compiler không nên mặc định tạo:

```text id="q2n8v4"
workers > useful CPU capacity
```

trừ khi task mostly blocking.

---

# 558.28. Blocking tasks

Compiler scheduler phải biết task có thể block I/O hay không.

---

# 558.29. Compiler I/O

Cache/filesystem operations nên sử dụng async/background I/O hoặc dedicated workers để không chiếm semantic workers quá lâu.

---

# 558.30. Critical path

DAG scheduler phải có khả năng ưu tiên task nằm trên critical path.

---

# 558.31. Critical path estimation

Mỗi task có:

```text id="k7p3x9"
estimated_cost
```

để scheduling.

---

# 558.32. Cost model

Cost có thể tính từ:

- previous measurements;
- input size;
- generic complexity;
- function size;
- optimization profile.

---

# 558.33. Cost model correctness

Cost estimate không được ảnh hưởng semantics.

---

# 558.34. Small-task overhead

Task quá nhỏ có thể được batch thay vì tạo scheduling overhead.

---

# 558.35. Task fusion

Các query liên quan có thể fuse khi semantics không thay đổi.

---

# 558.36. Task splitting

Task lớn có thể chia thành independent subqueries.

---

# 558.37. Recursive task spawning

Recursive spawning phải có depth/budget policy để tránh task explosion.

---

# 558.38. Task granularity

Granularity phải cân bằng:

```text id="e5m2q8"
parallelism
vs
scheduling overhead
```

---

# 558.39. Frontend parallelism

`556`:

```text id="v8k3m1"
lex files
parse files
index declarations
resolve independent modules
```

có thể parallel.

---

# 558.40. Module dependency

Nếu:

```text id="c4r7x2"
A → B
```

thì analysis cần B interface trước A.

---

# 558.41. Interface-first compilation

Compiler nên compile:

```text id="j9m4w6"
public declarations/interface
```

trước full bodies khi có thể.

---

# 558.42. Parallel bodies

Sau khi interface available, independent function bodies có thể typecheck song song.

---

# 558.43. Name resolution parallelism

Independent scopes có thể resolve concurrently.

---

# 558.44. Shared symbol index

Symbol index phải support concurrent reads.

---

# 558.45. Symbol publication

Symbol publication phải atomic.

---

# 558.46. Partial symbol index

Consumers không được đọc symbol index đang ở trạng thái inconsistent.

---

# 558.47. Type checking parallelism

Independent expressions/functions có thể typecheck song song.

---

# 558.48. Type dependency

Nếu function B cần inferred type từ A:

```text id="p6w3n8"
B waits for A
```

---

# 558.49. Explicit public types

Public API types được khai báo explicit theo `430`, giúp giảm dependency chains.

---

# 558.50. Trait solving parallelism

Independent trait goals có thể solve concurrently.

---

# 558.51. Trait cache concurrency

Trait cache phải support concurrent lookup/publish.

---

# 558.52. Solver duplicate suppression

Cùng canonical goal chỉ được solve một lần khi đang in-flight.

---

# 558.53. Recursive trait goals

Recursive goals phải detect cycle trước khi spawning vô hạn tasks.

---

# 558.54. Generic instantiation parallelism

Distinct monomorphizations có thể codegen song song:

```text id="g8k2r5"
Vec<i32>
Vec<f64>
Matrix<f32>
```

---

# 558.55. Generic cache

Nếu monomorphization đã tồn tại:

```text id="u5m9x2"
reuse
```

---

# 558.56. Codegen parallelism

Functions independent về semantic/codegen dependencies có thể compile concurrently.

---

# 558.57. Function-level codegen unit

Default backend scheduling unit là function hoặc sufficiently large region.

---

# 558.58. LTO parallelism

`553` LTO có thể partition whole-program IR thành parallel optimization regions.

---

# 558.59. Cross-function dependency

Inlining/devirtualization decisions phải respect analysis dependencies.

---

# 558.60. Optimization pass concurrency

Hai passes trên independent functions có thể chạy parallel.

---

# 558.61. Shared module analyses

Shared analysis result phải immutable sau publish.

---

# 558.62. Analysis invalidation

Pass làm invalid analysis phải publish invalidation metadata như `553`.

---

# 558.63. Race-free pass manager

Không pass nào được mutate shared analysis mà không synchronization.

---

# 558.64. Function-local optimization

Các optimization pass function-local nên được ưu tiên parallel.

---

# 558.65. Module-wide optimization

Module-wide pass phải declare dependency scope.

---

# 558.66. Whole-program pass

Whole-program pass có thể cần barrier trước khi chạy.

---

# 558.67. Barrier

Barrier chỉ được sử dụng khi dependency thực sự yêu cầu.

---

# 558.68. Barrier minimization

Không được serialize toàn compiler chỉ vì một global pass nhỏ.

---

# 558.69. Machine code emission

Machine code của các function có thể emit song song.

---

# 558.70. Object section assembly

Object writer phải support deterministic concurrent contribution.

---

# 558.71. Section ordering

Parallel emission không được làm section order phụ thuộc worker completion order.

---

# 558.72. Symbol ordering

Symbol table phải được canonical-sort hoặc assign stable IDs trước final emission.

---

# 558.73. Relocation ordering

Relocations phải có deterministic order.

---

# 558.74. Debug information

Debug records từ parallel codegen phải merge deterministic.

---

# 558.75. DWARF/CodeView/PDB

Parallel generation có thể tạo per-function fragments rồi merge canonical.

---

# 558.76. Machine fixups

Fixup collection phải deterministic.

---

# 558.77. Linker parallelism

`420` linker có thể parallel:

- archive indexing;
- symbol scanning;
- section processing;
- relocation preparation.

---

# 558.78. Symbol resolution

Final symbol resolution phải deterministic.

---

# 558.79. Section layout

Final addresses phải do deterministic layout phase quyết định.

---

# 558.80. Linker relaxation

Relaxation có dependency chain và có thể cần iterative barriers.

---

# 558.81. Parallel relaxation

Independent relaxation decisions có thể parallel.

---

# 558.82. Final layout barrier

Sau khi layout final:

```text id="d7p4m1"
addresses become authoritative
```

---

# 558.83. Native artifact identity

Artifact hash không được phụ thuộc task completion order.

---

# 558.84. Reproducible builds

`487/482` reproducibility phải giữ khi worker count thay đổi.

---

# 558.85. Deterministic merge

Mọi parallel collection phải có deterministic merge key.

Ví dụ:

```text id="x8q2m6"
ModuleId
FunctionId
SymbolId
SourceSpan
```

---

# 558.86. No concurrent append semantics

Không được dùng concurrent append làm thứ tự artifact semantics.

---

# 558.87. Stable sorting

Final serialization phải sort theo canonical identity.

---

# 558.88. Hash maps

Hash map iteration order không được trực tiếp quyết định output.

---

# 558.89. Randomized hashing

Compiler có thể randomize hash seed để security nhưng output phải vẫn deterministic.

---

# 558.90. Parallel diagnostics

Diagnostics có thể được tạo song song.

---

# 558.91. Diagnostic merge

Sort theo stable key:

```text id="m2k8v7"
file
span
severity
code
stable diagnostic identity
```

---

# 558.92. Diagnostic deduplication

Duplicate diagnostics phải được merge deterministic.

---

# 558.93. AI query parallelism

AI có thể yêu cầu đồng thời:

```text id="q7x3m9"
references
callers
type
layout
trait
```

---

# 558.94. AI query isolation

AI request không được mutate compiler semantic state mặc định.

---

# 558.95. Snapshot consistency

Các query trong cùng AI request phải dùng cùng snapshot nếu request yêu cầu coherent view.

---

# 558.96. Mixed snapshot query

Không được ghép kết quả từ S1 và S2 như một state duy nhất nếu không explicit.

---

# 558.97. LSP parallelism

Hover/completion/diagnostics có thể chạy concurrently nhưng phải snapshot-bound.

---

# 558.98. Request cancellation

LSP request cancellation phải release scheduling resources.

---

# 558.99. Interactive starvation

Background build không được giữ toàn worker pool vô hạn.

---

# 558.100. Reserved capacity

Scheduler có thể giữ một phần capacity cho interactive work.

---

# 558.101. Dynamic reservation

Reservation có thể thay đổi theo workload.

---

# 558.102. AI priority

AI interactive query có thể có priority riêng nhưng không được bypass safety/resource limits.

---

# 558.103. Background indexing

Background indexing phải yield khi interactive work xuất hiện.

---

# 558.104. Speculation

Compiler có thể precompute:

```text id="n3v8k2"
likely next query
likely codegen
likely completion
```

nhưng phải cancellable.

---

# 558.105. Speculation budget

Speculation có bounded CPU/memory budget.

---

# 558.106. Speculation isolation

Speculative result không được commit nếu dependency snapshot stale.

---

# 558.107. Snapshot transition

Khi S1 → S2:

```text id="p5m7x1"
cancel/retarget speculative work
```

theo dependency.

---

# 558.108. In-flight query migration

Query độc lập với changed region có thể tiếp tục.

---

# 558.109. Changed dependency

Query phụ thuộc changed region phải invalidate/cancel/recompute.

---

# 558.110. Scheduler and cache

Cache hit nên bypass expensive task creation.

---

# 558.111. Cache miss

Cache miss tạo normal query task.

---

# 558.112. Cache stampede

Concurrent requests cùng cache key phải được deduplicate.

---

# 558.113. Remote cache

Remote cache access phải có bounded concurrency.

---

# 558.114. Remote execution

`487` remote execution task phải có explicit resource/capability metadata.

---

# 558.115. Remote determinism

Remote và local execution phải produce equivalent semantic result.

---

# 558.116. Remote trust

Untrusted remote result phải qua validation/trust policy.

---

# 558.117. Translation validation

`552` phải có thể validate critical optimized regions bất kể task chạy worker nào.

---

# 558.118. Proof task scheduling

Proof/validation task có thể chạy song song với independent optimizations.

---

# 558.119. Optimization result publication

Optimization result chỉ publish sau validation level yêu cầu.

---

# 558.120. Invalid optimization

Nếu validation fail:

```text id="w4m8p2"
reject optimization
→ fallback previous IR
→ record failure
```

---

# 558.121. Miscompilation isolation

`552` phải identify pass/function/backend region gây divergence.

---

# 558.122. Deterministic validation

Validation result phải không phụ thuộc worker order.

---

# 558.123. Concurrent fuzzing

Compiler fuzz infrastructure có thể chạy nhiều independent compilations.

---

# 558.124. Shared fuzz resources

Global corpus/index phải synchronization-safe.

---

# 558.125. No shared mutable compiler semantics

Parallel compilations không được mutate shared semantic state ngoài controlled caches/interners.

---

# 558.126. Workspace isolation

Hai workspace compilation có semantic DB isolation.

---

# 558.127. Target isolation

x86-64 và AArch64 tasks không được dùng nhầm target-dependent state.

---

# 558.128. Toolchain isolation

Different compiler/toolchain configurations phải có distinct cache identities.

---

# 558.129. Memory-aware scheduling

Task metadata:

```text id="v6r2q8"
cpu_estimate
memory_estimate
io_estimate
priority
deadline
```

---

# 558.130. Memory admission

Scheduler không launch task nếu dự kiến vượt hard memory budget mà không có recovery policy.

---

# 558.131. Memory pressure response

```text id="k5m9x3"
reduce workers
→ evict cache
→ cancel speculation
→ spill
```

---

# 558.132. CPU pressure response

Có thể giảm background concurrency.

---

# 558.133. Deadline scheduling

Interactive deadline có thể influence priority.

Không được làm result approximate nếu request yêu cầu exact.

---

# 558.134. Deadline expiration

Task không kịp deadline phải:

```text id="s2q7m4"
cancel
hoặc return explicit incomplete state
```

---

# 558.135. Exact build

Build request không được publish incomplete artifact chỉ vì deadline.

---

# 558.136. Cooperative cancellation

Tasks phải có cancellation points.

---

# 558.137. Non-cancellable critical section

Critical state commit phải hoàn thành atomically hoặc rollback.

---

# 558.138. Partial result

Partial result phải tagged:

```text id="r8m3x6"
Incomplete
```

---

# 558.139. No partial semantic publication

Incomplete semantic state không được publish như valid semantic result.

---

# 558.140. Work stealing safety

Stealing phải synchronization-safe.

---

# 558.141. Local queue ordering

Local queue order chỉ là scheduling optimization.

---

# 558.142. Global ordering

Semantic ordering phải explicit dependency/canonical merge, không lấy queue order.

---

# 558.143. Worker failure

Worker crash/failure phải khiến task:

```text id="y7p2m5"
retry
fail
```

theo policy.

---

# 558.144. Task retry

Pure deterministic tasks có thể retry.

---

# 558.145. Effectful task retry

Effectful operations phải declare idempotency/retry policy.

---

# 558.146. Build scripts

Build scripts không được retry mù nếu có external side effects.

---

# 558.147. Cache write retry

Cache writes phải atomic/idempotent.

---

# 558.148. Scheduler crash recovery

Daemon recovery phải reconstruct active task state từ durable/build state khi cần.

---

# 558.149. No orphan task

Shutdown phải detect/cancel orphan tasks.

---

# 558.150. Worker lifecycle

```text id="q4m8v2"
Starting
Ready
Running
Draining
Stopping
Stopped
```

---

# 558.151. Worker pool resizing

Worker count có thể resize nếu platform cho phép.

---

# 558.152. Resize safety

Resize không được cancel committed semantic results.

---

# 558.153. Worker-local allocator

`557` có thể cung cấp worker-local arenas để giảm contention.

---

# 558.154. Worker-local cache

Có thể cache temporary data locally.

---

# 558.155. Worker cache correctness

Worker-local cache phải invalidatable hoặc disposable.

---

# 558.156. False sharing

Hot scheduler structures nên tránh false sharing khi có thể.

---

# 558.157. Atomic counters

Metrics counters có thể dùng atomics hoặc thread-local aggregation.

---

# 558.158. Metrics determinism

Performance metrics không được ảnh hưởng semantic output.

---

# 558.159. Scheduler observability

`475/476` phải expose:

```text id="m8q3x7"
queue depth
worker utilization
steals
task latency
blocked time
critical path
cache hits
```

---

# 558.160. No automatic telemetry

Compiler không tự động upload scheduling data.

---

# 558.161. AI scheduler diagnostics

AI có thể query:

```text id="v2k7m4"
why_waiting(task)
why_blocked(task)
critical_path()
memory_pressure()
```

---

# 558.162. Evidence

Scheduler explanation phải dựa trên actual dependency/resource state.

---

# 558.163. Parallel compile phases

Reference scheduling:

```text id="z5m2q8"
Parse
  ↓
Index
  ↓
Resolve
  ↓
Type
  ↓
Trait
  ↓
HIR
  ↓
MIR
  ↓
Optimize
  ↓
Codegen
  ↓
Object
  ↓
Link
```

Mỗi phase chỉ barrier ở dependencies cần thiết.

---

# 558.164. Pipeline overlap

Một module có thể codegen trong khi module khác vẫn đang frontend nếu dependency graph cho phép.

---

# 558.165. Streaming compilation

Large project không cần đợi toàn project semantic analysis mới bắt đầu mọi codegen.

---

# 558.166. Interface readiness

Codegen module có thể bắt đầu khi required semantic/interface dependencies ready.

---

# 558.167. Backend queue

Machine backend có queue riêng hoặc unified scheduler với resource class.

---

# 558.168. Backend CPU usage

Backend optimization có thể chiếm CPU lớn; scheduler phải account.

---

# 558.169. LTO resource budget

LTO có memory budget riêng.

---

# 558.170. PGO workload

Profile processing có thể parallel nhưng profile merge phải deterministic.

---

# 558.171. Profile merge

Profiles từ multiple runs:

```text id="u3m7x9"
normalize
→ validate
→ deterministic merge
```

---

# 558.172. Benchmark compilation

Benchmark tooling có thể compile benchmarks concurrently nhưng phải isolate artifacts.

---

# 558.173. Test compilation

Independent tests có thể compile parallel.

---

# 558.174. Test output

Test execution order phải explicit; compiler scheduling không được quyết định semantic test order.

---

# 558.175. Documentation generation

Docs từ `485` có thể parallel theo modules.

---

# 558.176. Documentation merge

Output phải deterministic.

---

# 558.177. Package build

Packages trong workspace có thể parallel theo dependency DAG.

---

# 558.178. Dependency package

Dependent package chờ required interface/artifact.

---

# 558.179. Multi-target build

Targets:

```text id="x7m4q2"
x86_64
AArch64
WASM
```

có thể compile parallel.

---

# 558.180. Cross-target cache isolation

Target-specific results không được reuse nhầm.

---

# 558.181. Static library

Object compilation có thể parallel.

---

# 558.182. Dynamic library

Independent compilation/codegen có thể parallel, final export/link stage deterministic.

---

# 558.183. Native executable

Final link may require global serialization for address/layout decisions.

---

# 558.184. Link parallelism boundary

Compiler phải parallelize everything safe **before** inherently sequential final layout operations.

---

# 558.185. Object writer

Object sections phải được accumulated bằng stable IDs.

---

# 558.186. Artifact verification

After parallel emission:

```text id="f5q8m2"
object validation
→ relocation validation
→ symbol validation
```

---

# 558.187. Artifact hash

Hash computed only after canonical serialization.

---

# 558.188. Reproducibility test matrix

Compile same source with:

```text id="p2m7x4"
1 worker
2 workers
4 workers
8 workers
N workers
```

và compare.

---

# 558.189. Scheduling randomization

Test mode có thể randomize scheduling để tìm race/dependency bugs.

---

# 558.190. Random scheduling correctness

Random scheduler và deterministic scheduler phải produce equivalent semantics.

---

# 558.191. Race detection

Compiler scheduler phải được test dưới race sanitizer/tooling tương ứng.

---

# 558.192. Deadlock detection

Debug scheduler phải detect cycles/deadlocks trong task dependencies.

---

# 558.193. Starvation detection

Stress test phải phát hiện task bị starvation vượt policy.

---

# 558.194. Priority inversion

Scheduler phải có mitigation khi low-priority task giữ dependency cần cho high-priority task.

---

# 558.195. Dependency priority inheritance

Có thể boost dependency priority để hoàn thành critical path.

---

# 558.196. No priority semantic effect

Priority chỉ thay đổi thời gian thực thi.

---

# 558.197. Deterministic failure

Một invalid source phải produce equivalent diagnostics dù scheduling khác nhau.

---

# 558.198. Full clean fallback

Nếu parallel incremental scheduler gặp state không hợp lệ:

```text id="h7q3m8"
invalidate
→ clean recomputation
```

---

# 558.199. Final parallelism contract

Axiom compiler phải đạt:

```text id="b8m2x5"
High CPU utilization
Fine-grained tasks
Dependency awareness
Work stealing
Memory awareness
Cancellation
Fairness
Snapshot isolation
Deterministic merge
Reproducible output
```

---

# 558.200. HARD INVARIANTS

1. Parallel compilation phải semantic-equivalent với serial compilation.
2. Worker count không được thay đổi semantics.
3. Worker scheduling không được thay đổi semantics.
4. Work stealing không được thay đổi semantics.
5. Cache hit/miss không được thay đổi semantics.
6. Speculation không được thay đổi semantics.
7. CPU affinity không được thay đổi semantics.
8. NUMA placement không được thay đổi semantics.
9. Priority không được thay đổi semantics.
10. Deadline policy không được tạo artifact sai semantics.
11. Dependency DAG phải là source of scheduling truth.
12. Task chỉ chạy khi dependency cần thiết đã Ready.
13. Task dependency phải được recorded.
14. Duplicate queries phải được deduplicate.
15. Shared in-flight query phải có một semantic computation.
16. Consumer cancellation không được hủy query còn consumer khác.
17. Last-consumer cancellation phải respect build-critical state.
18. Speculative work phải cancellable.
19. Speculative result phải snapshot-bound.
20. Stale speculative result không được commit.
21. Interactive work phải có priority protection.
22. Background work không được starvation vô hạn.
23. Scheduler phải có fairness policy.
24. Priority inversion phải được xử lý.
25. Dependency priority có thể được inherited.
26. Priority chỉ ảnh hưởng scheduling.
27. Memory pressure phải ảnh hưởng scheduling an toàn.
28. Memory hard limit không được bị vượt qua không kiểm soát.
29. Worker count có thể giảm khi memory pressure.
30. Worker-local allocation phải respect `557`.
31. Shared semantic data phải immutable hoặc synchronized.
32. Symbol publication phải atomic.
33. Type cache publication phải atomic.
34. Trait cache publication phải atomic.
35. Query result publication phải atomic.
36. Invalid query không được publish như Ready.
37. Cancelled query không được publish partial semantic state.
38. Failed query không được publish invalid semantic state.
39. Query cycles phải được detect.
40. Recursive task spawning phải bounded.
41. Task graph phải không tạo cycle ngoài cơ chế recursion hợp lệ.
42. Deadlock phải được detect trong debug/test.
43. Scheduler phải có deterministic dependency semantics.
44. Parallel merge phải deterministic.
45. Hash-map iteration không được quyết định artifact order.
46. Concurrent append không được quyết định artifact semantics.
47. Symbol order phải canonical.
48. Section order phải canonical.
49. Relocation order phải canonical.
50. Debug metadata merge phải deterministic.
51. Diagnostic ordering phải deterministic.
52. Diagnostic deduplication phải deterministic.
53. Object serialization phải deterministic.
54. Final artifact hash phải independent of worker order.
55. Reproducible build phải hold across worker counts.
56. `552` validation phải operate independently of scheduling order.
57. Failed optimization validation phải reject optimization.
58. Previous valid IR phải remain usable after validation failure.
59. Miscompilation investigation phải preserve task/pass provenance.
60. Frontend tasks phải integrate `556`.
61. Memory scheduling phải integrate `557`.
62. Query scheduling phải integrate `555`.
63. Cache scheduling phải integrate `554`.
64. Build scheduling phải integrate `487`.
65. Optimization scheduling phải integrate `553`.
66. ABI/codegen scheduling phải integrate `421/438`.
67. Object/link scheduling phải integrate `420`.
68. Debug generation phải integrate `440`.
69. AI queries phải remain snapshot-consistent.
70. LSP queries phải remain snapshot-consistent.
71. AI and LSP requests không được mutate semantic truth mặc định.
72. Multi-workspace scheduling phải isolate semantic state.
73. Multi-target scheduling phải isolate target state.
74. Multi-toolchain scheduling phải isolate toolchain state.
75. Remote execution phải preserve semantic equivalence.
76. Remote cache result phải validate theo trust policy.
77. Untrusted remote output không được bypass validation.
78. Build scripts phải có explicit effect semantics.
79. Effectful task retry phải respect idempotency.
80. Cache writes phải atomic.
81. Worker failure phải not corrupt query DB.
82. Worker failure phải not corrupt cache.
83. Worker failure phải not corrupt source snapshot.
84. Worker restart phải preserve semantic correctness.
85. Daemon restart phải preserve semantic correctness.
86. Shutdown phải cancel/reconcile tasks safely.
87. Orphan tasks phải được detect.
88. Task resources phải được released after completion.
89. Task resources phải được released after cancellation.
90. Task resources phải được released after failure.
91. Temporary memory phải integrate `557`.
92. Persistent state phải not depend on worker-local pointers.
93. Worker-local caches phải disposable.
94. Worker-local state không được leak semantic state.
95. CPU topology detection chỉ là optimization input.
96. NUMA policy chỉ là optimization input.
97. Affinity chỉ là optimization input.
98. Oversubscription phải được controlled.
99. Blocking tasks không được monopolize semantic workers.
100. I/O workers phải be resource-accounted.
101. Critical path estimation không được affect correctness.
102. Cost model không được affect correctness.
103. Task batching không được affect correctness.
104. Task fusion không được affect correctness.
105. Task splitting không được affect correctness.
106. Pipeline overlap không được affect correctness.
107. Function-level parallel codegen phải deterministic.
108. Generic monomorphization phải deterministic.
109. LTO parallelism phải deterministic.
110. PGO merge phải deterministic.
111. Profile data normalization phải deterministic.
112. Parallel test compilation phải isolate artifacts.
113. Parallel package builds phải respect dependency graph.
114. Multi-target builds phải isolate artifacts.
115. Static-library emission phải deterministic.
116. Dynamic-library emission phải deterministic.
117. Executable final layout phải deterministic.
118. Linker final address assignment phải deterministic.
119. Linker relaxation must respect dependencies.
120. Parallel linker preparation must not bypass final layout constraints.
121. Object writer must not depend on task completion order.
122. Relocation records must be canonicalized.
123. Symbol tables must be canonicalized.
124. Debug sections must be canonicalized.
125. Build IDs must be deterministic under equivalent inputs.
126. Artifact hashes must be stable under equivalent inputs.
127. Incremental and clean builds must be equivalent.
128. Cached and uncached builds must be equivalent.
129. Serial and parallel builds must be equivalent.
130. Local and trusted remote builds must be equivalent.
131. Randomized scheduler tests must preserve equivalence.
132. Race sanitizer runs must be part of compiler CI.
133. Deadlock stress tests must exist.
134. Starvation stress tests must exist.
135. Priority inversion tests must exist.
136. Cancellation stress tests must exist.
137. Memory-pressure scheduling tests must exist.
138. Large-project parallelism tests must exist.
139. Large-generic-project tests must exist.
140. LTO parallel tests must exist.
141. Multi-target parallel tests must exist.
142. Cross-workspace isolation tests must exist.
143. Cross-toolchain isolation tests must exist.
144. Remote execution equivalence tests must exist.
145. Cache stampede tests must exist.
146. Duplicate-query suppression tests must exist.
147. Query-cycle tests must exist.
148. Recursive task budget tests must exist.
149. Worker crash recovery tests must exist.
150. Daemon restart equivalence tests must exist.
151. Scheduler metrics must not alter semantics.
152. Scheduler diagnostics must be evidence-based.
153. `why_waiting` must expose actual dependency/resource reasons.
154. `why_blocked` must expose actual dependency state.
155. Critical-path reporting must derive from actual DAG.
156. Memory pressure reporting must derive from actual accounting.
157. AI scheduler reports must preserve uncertainty.
158. AI must not fabricate task dependency.
159. AI must not infer completion from queue presence alone.
160. AI must distinguish Running/Completed/Cached/Speculative.
161. Scheduler must expose machine-readable task state.
162. Scheduler protocol must be versioned.
163. Task identity must be stable within scheduler session.
164. Persistent task identity must not depend on memory address.
165. Task resource estimates must be advisory unless explicitly enforced.
166. Resource limits must be explicit.
167. Deadline limits must be explicit.
168. Cancellation must be explicit.
169. Background speculation must be bounded.
170. Interactive work must remain responsive under background load.
171. Interactive work must remain correct under background load.
172. Background work must resume after interactive pressure subsides.
173. Cache maintenance must not monopolize compiler workers.
174. Cache cleanup must be cancellable.
175. Remote operations must have bounded concurrency.
176. Remote failures must not corrupt local state.
177. Remote timeout must produce explicit state.
178. Network retry must respect operation semantics.
179. Build-script retry must not duplicate unsafe side effects.
180. Final artifact publication must occur only after required validation.
181. Artifact publication must be atomic.
182. Failed compilation must not replace last valid artifact unless policy explicitly requests it.
183. Failed parallel task must not poison valid cache.
184. Invalid cache must be discarded/recomputed.
185. Validation failures must remain observable.
186. Compiler correctness evidence must include scheduling-independent identity.
187. Translation validation must be reproducible.
188. Optimization pass provenance must be preserved.
189. Machine encoding validation must be independent of worker order.
190. Object validation must be independent of worker order.
191. Link validation must be independent of worker order.
192. Final executable behavior must not depend on worker order.
193. Final executable layout may only differ if explicitly permitted by reproducibility policy; semantics must remain equivalent.
194. Any permitted nondeterministic metadata must be explicitly classified.
195. No scheduler optimization may silently weaken correctness.
196. Full serial fallback must remain available.
197. Serial fallback must be continuously tested.
198. Parallelism must remain an implementation optimization, not a second semantic model.
199. Compiler performance must be measured separately from compiler correctness.
200. **Final invariant:** Axiom compiler phải biến dependency DAG thành thực thi song song mạnh trên toàn pipeline — từ frontend, semantic analysis, optimization tới native codegen/link — nhưng mọi kết quả observable phải được quyết định bởi **source + semantic dependencies + target/toolchain/configuration**, tuyệt đối không bởi worker nào chạy trước, worker nào steal task, cache có hit hay không, hay scheduler đã chọn chiến lược nào.

**BOOTSTRAP-558: LOCKED.**

---

# NEXT — BOOTSTRAP-559

## COMPILER QUERY ENGINE 3.0 — DEMAND-DRIVEN SEMANTIC DATABASE, CYCLE HANDLING, QUERY INVALIDATION, SNAPSHOT REUSE & CROSS-PHASE DEPENDENCY PROOF

`559` sẽ đi sâu hơn vào **query engine**, vì `555–558` đã xây daemon, memory và scheduler nhưng cần khóa chính xác “compiler hỏi gì, phụ thuộc gì, invalidate gì và chứng minh result còn hợp lệ”.

Kiến trúc:

```text id="x6p3m9"
                    Query Request
                         │
                         ▼
                  Query Key Canonicalizer
                         │
                         ▼
                  Query Dependency DB
                         │
             ┌───────────┼───────────┐
             ▼           ▼           ▼
          Cached       Active      Invalid
          Result       Query       Result
             │           │
             │           ▼
             │      Dependency DAG
             │           │
             └──────┬────┘
                    ▼
              Query Evaluator
                    │
          ┌─────────┼─────────┐
          ▼         ▼         ▼
       Syntax      Type      Trait
       Layout      Effect    Ownership
       HIR         MIR       ABI
          │
          ▼
       Validation
          │
          ▼
     Publish Result
```

Trọng tâm `559`:

- canonical `QueryKey`;
- query input/output identity;
- dependency recording;
- dynamic dependency;
- cycle detection và cycle semantics;
- fixed-point queries;
- incremental invalidation;
- cross-snapshot reuse;
- query cancellation;
- stale-result rejection;
- concurrent query deduplication;
- query ownership;
- query dependency proof;
- semantic cache correctness;
- interaction `430/431/436/487/552/554/555/556/557/558`;
- và đặc biệt **không để query cache biến thành một “nguồn sự thật” thứ hai ngoài compiler semantics**.