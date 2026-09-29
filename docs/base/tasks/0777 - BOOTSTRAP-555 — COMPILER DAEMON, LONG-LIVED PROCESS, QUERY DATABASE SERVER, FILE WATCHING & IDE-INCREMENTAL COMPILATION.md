# BOOTSTRAP-555 — COMPILER DAEMON, LONG-LIVED PROCESS, QUERY DATABASE SERVER, FILE WATCHING & IDE-INCREMENTAL COMPILATION

**Trạng thái: COMPLETED / LOCKED**

`555` xây lớp **compiler daemon** nằm trên `436`, `487`, `554` và cung cấp nền tảng cho IDE/LSP/AI có phản hồi gần như tức thời.

Mục tiêu không phải biến compiler thành một runtime thường trú bắt buộc. CLI vẫn phải hoạt động độc lập:

```text
One-shot Compiler
        │
        ├── same compiler engine
        │
        ▼
Compiler Daemon
        │
        ├── persistent query DB
        ├── persistent cache
        ├── source snapshots
        └── incremental analysis
```

**Daemon là optimization của developer experience, không phải một phần semantic của ngôn ngữ.**

---

## 555.1. Daemon architecture

```text
                  IDE / CLI / LSP / AI
                           │
                           ▼
                    IPC / API Boundary
                           │
                           ▼
                ┌──────────────────────┐
                │  Axiom Compiler      │
                │      Daemon          │
                ├──────────────────────┤
                │ Request Scheduler    │
                │ Workspace Manager    │
                │ Snapshot Manager     │
                │ Query Database       │
                │ Incremental Engine   │
                │ Cache Manager        │
                │ Build Graph          │
                │ Diagnostics          │
                │ Semantic Server      │
                └──────────┬───────────┘
                           │
             ┌─────────────┼─────────────┐
             ▼             ▼             ▼
        Source DB       Cache Store    Toolchain
```

---

# 555.2. Daemon không thay đổi compiler semantics

Daemon và one-shot compiler phải dùng cùng:

- parser;
- type checker;
- trait solver;
- ownership engine;
- MIR;
- optimizer;
- codegen;
- linker;
- diagnostics.

Không được có:

```text
daemon semantics
```

khác:

```text
CLI semantics
```

---

# 555.3. Daemon lifecycle

```text
Starting
   ↓
Ready
   ↓
Serving
   ↓
Draining
   ↓
Stopping
```

Unexpected termination:

```text
Serving
   ↓
Crash
   ↓
Restart
   ↓
Recover
```

---

# 555.4. Stateless fallback

Nếu daemon không chạy:

```text
axiom build
```

vẫn phải build bình thường.

---

# 555.5. Daemon discovery

CLI tìm daemon theo:

```text
workspace identity
toolchain identity
user/session policy
```

---

# 555.6. Workspace identity

Không dùng đường dẫn đơn thuần làm identity.

```text
WorkspaceId =
    normalized_root
    + project_manifest_hash
```

---

# 555.7. Multi-project daemon

Một daemon có thể phục vụ nhiều workspace:

```text
Daemon
 ├── Workspace A
 ├── Workspace B
 └── Workspace C
```

nhưng semantic state phải được namespace riêng.

---

# 555.8. Project isolation

Query của Project A không được đọc semantic state của Project B nếu dependency graph không cho phép.

---

# 555.9. Snapshot model

Source state được biểu diễn bằng immutable snapshot:

```text
SourceSnapshot {
    snapshot_id
    files[]
    content_hashes[]
    workspace_id
    parent_snapshot?
}
```

---

# 555.10. Snapshot immutability

Sau khi publish:

```text
Snapshot N
```

không được mutate.

---

# 555.11. Editing flow

```text
Editor
  │
  ▼
new text
  │
  ▼
Snapshot N+1
  │
  ▼
incremental queries
```

---

# 555.12. Snapshot chain

```text
S0 → S1 → S2 → S3
```

cho phép xác định chính xác change set.

---

# 555.13. Snapshot diff

Daemon tính:

```text
added
removed
modified
renamed
moved
```

và semantic classification từ `486/554`.

---

# 555.14. Unsaved buffers

IDE buffer có priority cao hơn filesystem.

```text
Editor Buffer
      ↓
Virtual Source
      ↓
Compiler Snapshot
```

---

# 555.15. Filesystem source

Nếu không có unsaved buffer:

```text
Filesystem
```

là source provider.

---

# 555.16. Source provider abstraction

```text
SourceProvider {
    read(FileId)
    version(FileId)
    list(workspace)
}
```

---

# 555.17. File watching

Daemon có thể theo dõi:

```text
create
modify
delete
rename
```

---

# 555.18. Filesystem events không phải semantic events

Một file system event có thể:

```text
duplicate
out-of-order
coalesced
missing
```

Do đó daemon phải revalidate source version.

---

# 555.19. Event coalescing

Ví dụ:

```text
write
write
write
rename
```

có thể hợp nhất thành một logical change.

---

# 555.20. Debounce

Daemon có thể delay analysis rất ngắn để tránh compile từng keystroke.

---

# 555.21. Interactive latency

Query interactive phải có priority cao hơn full release build.

---

# 555.22. Request priority

```text
Interactive
Diagnostic
Completion
Navigation
Check
Build
Test
Background
Maintenance
```

---

# 555.23. Query cancellation

Mọi long-running query phải hỗ trợ cancellation nếu có thể.

---

# 555.24. Cancellation semantics

Cancellation:

```text
cancel request
```

không được:

```text
corrupt query database
```

---

# 555.25. Cooperative cancellation

Pass/checkpoint dài phải periodically check cancellation token.

---

# 555.26. Non-cancellable critical section

Một số atomic publish/commit operations có thể không cancel giữa chừng.

---

# 555.27. Request isolation

Một query bị cancel không được invalidate shared valid state.

---

# 555.28. Query database

Daemon duy trì:

```text
QueryKey → QueryResult
```

và dependency graph.

---

# 555.29. Query result states

```text
Unknown
Computing
Ready
Invalidated
Cancelled
Failed
```

---

# 555.30. Cycle detection

Nếu:

```text
Query A → B → C → A
```

database phải detect cycle.

---

# 555.31. Query cycle diagnostics

Compiler phải report semantic cycle hoặc internal query cycle tùy loại.

---

# 555.32. Incremental query

Nếu dependency fingerprint unchanged:

```text
old result → reuse
```

---

# 555.33. Fine-grained query keys

Không dùng:

```text
typecheck(project)
```

cho mọi thứ.

Ưu tiên:

```text
typecheck(FunctionId)
resolve(SymbolId)
layout(TypeId)
trait_solve(Query)
```

khi có thể.

---

# 555.34. Query granularity

Granularity phải cân bằng:

```text
reuse
memory
scheduling overhead
serialization cost
```

---

# 555.35. Dependency tracking

Mỗi query record:

```text
inputs[]
dependencies[]
result_fingerprint
```

---

# 555.36. Dynamic dependencies

Một query có thể discover dependency trong quá trình thực thi.

Dependency graph phải được cập nhật sau khi query hoàn thành.

---

# 555.37. Dependency invalidation

```text
changed input
    ↓
dependent queries
    ↓
invalidated
```

---

# 555.38. Lazy recomputation

Invalidated query không nhất thiết recompute ngay.

Chỉ recompute khi consumer cần.

---

# 555.39. Demand-driven compilation

```text
IDE hover
   ↓
type query
   ↓
only required semantic region
```

---

# 555.40. Background warming

Daemon có thể dự đoán queries cần thiết và precompute background.

Prediction không được ảnh hưởng correctness.

---

# 555.41. Speculative query

Speculative result phải gắn:

```text
snapshot_id
```

và không được commit nhầm sang snapshot khác.

---

# 555.42. Snapshot isolation

```text
Request R1 → Snapshot S1
Request R2 → Snapshot S2
```

R1 không được lấy semantic result từ S2 nếu dependency semantics không tương thích.

---

# 555.43. Snapshot promotion

Khi editor xác nhận snapshot mới:

```text
S2
 ↓
current snapshot
```

---

# 555.44. Stale request

Nếu request trả về cho snapshot cũ:

```text
discard
```

hoặc đánh dấu stale.

---

# 555.45. Stale diagnostic

IDE không được hiển thị diagnostic của source version cũ như diagnostic hiện tại.

---

# 555.46. Stale completion

Completion result phải gắn document version.

---

# 555.47. LSP version integration

Axiom LSP document version phải map tới `SourceSnapshot`.

---

# 555.48. Query scheduler

Scheduler quản lý:

```text
priority
dependencies
CPU budget
memory budget
cancellation
fairness
```

---

# 555.49. Interactive starvation prevention

Background build không được chiếm toàn bộ CPU khiến completion/hover bị treo vô thời hạn.

---

# 555.50. Resource quotas

Daemon có:

```text
max_memory
max_workers
max_background_cpu
max_cache_memory
```

---

# 555.51. Memory pressure

Khi memory cao:

```text
drop derived query results
```

nhưng giữ persistent cache có giá trị.

---

# 555.52. Query result eviction

Eviction:

```text
Ready result
 ↓
evicted
 ↓
recompute
```

không thay đổi semantics.

---

# 555.53. Persistent vs ephemeral state

Persistent:

- cache artifacts;
- dependency fingerprints;
- compiled modules;
- trusted metadata.

Ephemeral:

- active snapshots;
- request state;
- cancellation tokens;
- interactive diagnostics.

---

# 555.54. Daemon restart

Restart không được yêu cầu source rebuild từ đầu nếu persistent cache còn valid.

---

# 555.55. Crash recovery

```text
Daemon crash
    ↓
restart
    ↓
validate persistent state
    ↓
reuse valid cache
    ↓
recompute invalid state
```

---

# 555.56. Corrupt daemon state

Nếu persistent state corrupt:

```text
quarantine
→ rebuild
```

---

# 555.57. No trusted mutable database corruption

Query database persistent metadata phải có integrity/version checks.

---

# 555.58. Compiler daemon IPC

IPC protocol:

```text
Request
Response
Notification
Event
```

---

# 555.59. Request identity

```text
RequestId
```

phải unique trong daemon session.

---

# 555.60. Request cancellation

```text
Cancel(RequestId)
```

---

# 555.61. Request deadline

Optional:

```text
Deadline
```

interactive request có thể timeout.

---

# 555.62. Deadline ≠ cancellation guarantee

Daemon phải report:

```text
completed
cancelled
deadline_exceeded
```

rõ ràng.

---

# 555.63. Protocol version

Client/daemon handshake:

```text
protocol_version
compiler_version
capabilities
workspace
```

---

# 555.64. Protocol incompatibility

Không cố parse request của protocol incompatible.

---

# 555.65. Local IPC security

Daemon socket/pipe phải giới hạn access theo OS identity khi có thể.

---

# 555.66. Remote daemon

Remote compiler daemon không được mặc định trusted.

Nếu hỗ trợ remote:

```text
authentication
authorization
transport security
artifact verification
```

phải explicit.

---

# 555.67. Capability model

Daemon capabilities có thể gồm:

```text
ReadWorkspace
WriteArtifacts
ExecuteBuildScript
AccessNetwork
AccessCompilerCache
```

---

# 555.68. Least privilege

IDE semantic query không cần quyền execute build script.

---

# 555.69. AI client

AI tooling có thể kết nối daemon qua semantic API.

---

# 555.70. AI semantic query

Ví dụ:

```text
find_symbol
find_references
get_type
get_layout
get_trait_impls
get_callers
get_callees
get_effects
get_unsafe_regions
get_dependencies
```

---

# 555.71. AI snapshot binding

AI request phải specify:

```text
workspace
snapshot
```

hoặc explicit current snapshot.

---

# 555.72. AI stale-context protection

AI không được nhận semantic result của source state khác mà không có indication.

---

# 555.73. Semantic neighborhood

Daemon có thể trả:

```text
symbol
signature
relevant types
trait constraints
callers
callees
effects
source spans
```

để AI không cần parse toàn project.

---

# 555.74. Context minimization

AI query mặc định trả context cần thiết thay vì toàn bộ repository.

---

# 555.75. Query provenance

Mỗi AI semantic result:

```text
snapshot_id
compiler_build
query_id
source_spans
```

---

# 555.76. AI explanation

Có thể hỏi:

```text
why_rebuilt
why_error
why_not_optimized
why_trait_not_implemented
why_allocation
```

---

# 555.77. Evidence-only explanation

Giống `446/553`, daemon không được tự bịa explanation.

---

# 555.78. IDE diagnostics

Diagnostics được cache theo:

```text
snapshot
query
diagnostic fingerprint
```

---

# 555.79. Diagnostic deduplication

Một semantic error không nên xuất hiện hàng chục lần chỉ vì nhiều queries consume cùng result.

---

# 555.80. Diagnostic dependencies

Nếu underlying type error thay đổi, diagnostics downstream phải invalidate.

---

# 555.81. Error recovery

Parser có thể tạo recovery AST/HIR cho IDE.

Recovery AST không được dùng để tạo release artifact.

---

# 555.82. Editor parsing mode

```text
IDE parse
```

có thể tolerate incomplete source:

```text
fn foo(
```

---

# 555.83. Build parsing mode

Build compiler yêu cầu valid syntax.

---

# 555.84. Completion engine

Completion dùng partial AST + semantic context.

---

# 555.85. Completion ranking

Ranking không phải semantic correctness.

---

# 555.86. Go-to-definition

Resolution phải dựa trên `SymbolId`, không phải text search đơn thuần.

---

# 555.87. Rename

Rename sử dụng semantic references từ `486`.

---

# 555.88. Refactoring transaction

IDE transformation:

```text
plan
→ validate
→ apply
→ new snapshot
```

---

# 555.89. Failed refactoring

Nếu validation thất bại:

```text
no partial mutation
```

---

# 555.90. File watcher race

Pattern:

```text
editor save
filesystem event
external process change
```

phải được reconcile bằng content/version checks.

---

# 555.91. File identity

File rename phải preserve identity khi daemon có đủ evidence.

---

# 555.92. File deletion

Deletion:

```text
SourceExists = false
```

phải invalidate dependent queries.

---

# 555.93. External dependency changes

Package/toolchain/SDK changes phải tạo new dependency fingerprint.

---

# 555.94. Workspace graph update

Manifest/lockfile changes phải trigger dependency graph refresh.

---

# 555.95. Toolchain switching

Nếu user đổi:

```text
Axiom toolchain
```

daemon phải tạo toolchain context mới.

---

# 555.96. Multi-toolchain isolation

Artifact/query state của:

```text
Toolchain A
```

không được nhầm với:

```text
Toolchain B
```

---

# 555.97. Target switching

IDE có thể query:

```text
target x86_64
```

sau đó:

```text
target aarch64
```

Semantic source information có thể reuse một phần; target-dependent layout/codegen không.

---

# 555.98. Configuration snapshots

Effective configuration từ `470` trở thành immutable snapshot input.

---

# 555.99. Configuration change

Thay đổi config:

```text
optimization
target
features
diagnostics
security
```

invalidate đúng layers.

---

# 555.100. Build request

Build request chứa:

```text
snapshot
target
profile
configuration
toolchain
```

---

# 555.101. Concurrent builds

Daemon có thể phục vụ:

```text
Debug build
Release build
WASM build
```

đồng thời nếu resource policy cho phép.

---

# 555.102. Build isolation

Build contexts phải tách artifact identity.

---

# 555.103. Artifact commit

Build hoàn thành:

```text
verify
→ publish
→ notify
```

---

# 555.104. Build cancellation

Cancel build:

```text
stop future work
```

nhưng artifacts đã verified/published vẫn hợp lệ.

---

# 555.105. Partial build artifact

Artifact chưa hoàn tất không được publish như complete artifact.

---

# 555.106. Parallel module compilation

Các module độc lập có thể compile song song.

---

# 555.107. Dependency barriers

Module B phụ thuộc interface A phải chờ semantic interface A, nhưng không nhất thiết chờ toàn bộ native code A.

---

# 555.108. Interface-first compilation

```text
A
 ├── interface
 └── implementation
```

interface có thể publish sớm.

---

# 555.109. Fast IDE path

IDE chỉ cần:

```text
interface + semantic query
```

không cần link executable.

---

# 555.110. Background native build

Native codegen/link có thể chạy background.

---

# 555.111. Query priority over codegen

Interactive query không nên bị block bởi full link.

---

# 555.112. Build graph scheduling

Scheduler sử dụng dependency graph từ `487`.

---

# 555.113. Query + build sharing

Nếu build đã tính:

```text
typecheck(F)
```

IDE có thể reuse kết quả.

Ngược lại cũng vậy.

---

# 555.114. Single semantic truth

Không tồn tại:

```text
IDE type checker
```

riêng biệt với:

```text
Build type checker
```

cùng semantics.

---

# 555.115. Incremental parser

Parser có thể reuse unchanged syntax regions.

---

# 555.116. Token cache

Tokenization có thể cache theo file content hash.

---

# 555.117. Incremental AST

AST nodes unchanged có thể preserve identity nếu source mapping cho phép.

---

# 555.118. Stable NodeId

Node identity:

```text
NodeId
```

phải không bị hiểu là permanent identity qua mọi source mutation.

---

# 555.119. Semantic identity

Semantic entities dùng:

```text
SymbolId
TypeId
```

từ `446`.

---

# 555.120. Identity preservation

Rename có thể giữ `SymbolId` nếu compiler xác định đây là cùng semantic entity.

---

# 555.121. Textual similarity ≠ identity

Không tự động coi hai declaration giống nhau chỉ vì text gần giống.

---

# 555.122. Incremental name resolution

Name resolution chỉ invalidate affected scopes/modules.

---

# 555.123. Scope cache

Scope environment có fingerprint.

---

# 555.124. Type checking incrementality

Thay đổi expression local không cần typecheck module không liên quan.

---

# 555.125. Trait solver incrementality

Trait query cache được reuse nếu:

```text
types
traits
impl set
compiler rules
```

không đổi.

---

# 555.126. Ownership incrementality

Ownership state chỉ invalidate affected MIR/semantic region.

---

# 555.127. MIR cache integration

MIR từ `554` có thể reuse nếu HIR semantics unchanged.

---

# 555.128. Optimization integration

Optimization cache `553/554` được daemon dùng trực tiếp.

---

# 555.129. Codegen integration

Codegen cache được query trước khi re-emit machine code.

---

# 555.130. Link integration

Link cache được reuse nếu input closure unchanged.

---

# 555.131. Debug integration

Debug metadata có cache identity riêng.

---

# 555.132. Source-map update

Source edits chỉ ảnh hưởng source mappings khi semantics/artifact mapping thực sự thay đổi.

---

# 555.133. Memory reclamation

Daemon phải có cơ chế:

```text
evict
compact
reclaim
```

---

# 555.134. Query memory generations

Có thể chia:

```text
hot
warm
cold
persistent
```

---

# 555.135. LRU không phải semantic

Eviction order không ảnh hưởng result.

---

# 555.136. Daemon memory leak detection

Long-running daemon phải test:

```text
open/close workspace
edit/build/revert
```

nhiều lần.

Memory phải không tăng vô hạn do stale snapshots.

---

# 555.137. Snapshot retention

Chỉ giữ số snapshot cần thiết:

```text
current
active requests
recent history
```

---

# 555.138. Snapshot pinning

Một request đang chạy có thể pin snapshot.

---

# 555.139. Snapshot release

Khi request kết thúc:

```text
unpin
```

và snapshot có thể reclaim nếu không còn dependency.

---

# 555.140. Background task lifecycle

Background task phải biết:

```text
snapshot
priority
cancellation
owner
```

---

# 555.141. Workspace close

Đóng workspace:

```text
cancel requests
flush required state
release snapshot
release watchers
```

---

# 555.142. Daemon shutdown

Graceful shutdown:

```text
stop accepting
drain critical writes
publish/flush state
close IPC
```

---

# 555.143. Forced shutdown

Không được làm persistent cache corrupt.

---

# 555.144. Daemon auto-start

CLI/IDE có thể auto-start daemon nếu policy cho phép.

---

# 555.145. Daemon auto-stop

Có thể shutdown sau idle timeout.

---

# 555.146. Idle daemon

Idle daemon không được tiêu thụ CPU đáng kể.

---

# 555.147. File watcher fallback

Nếu OS watcher unavailable:

```text
polling
```

có thể dùng nhưng phải explicit/per-policy.

---

# 555.148. Network filesystem

Filesystem event semantics không đáng tin phải fallback tới content/version validation.

---

# 555.149. Clock independence

Daemon cache correctness không dựa trên wall-clock chính xác.

---

# 555.150. Build timestamps

Timestamp chỉ là metadata, không semantic input trừ policy.

---

# 555.151. Determinism

```text
daemon build(S)
==
one-shot build(S)
```

về semantics/artifact contract.

---

# 555.152. Warm vs cold

Warm daemon có thể nhanh hơn nhưng không được tạo result khác cold daemon.

---

# 555.153. Daemon-specific bug

Nếu daemon result khác one-shot:

```text
DaemonDivergence
```

phải được xem là compiler infrastructure defect.

---

# 555.154. Differential daemon testing

Test:

```text
one-shot
vs
daemon
```

trên cùng snapshot.

---

# 555.155. Restart equivalence

Test:

```text
daemon build
→ restart daemon
→ build
```

phải equivalent với continuous daemon.

---

# 555.156. Cache purge equivalence

```text
warm daemon
vs
purged daemon
```

phải tạo semantic-equivalent result.

---

# 555.157. Edit sequence testing

Test:

```text
S0
→ S1
→ S2
→ S3
```

so với clean compile S3.

---

# 555.158. Revert testing

```text
S0
→ S1
→ S0
```

phải recover đúng cache/S0 semantics.

---

# 555.159. Rapid edit testing

Hàng trăm edits liên tiếp phải không tạo stale semantic state.

---

# 555.160. Cancellation testing

Random cancellation tại các compiler phases.

Không được corrupt persistent state.

---

# 555.161. Concurrent query testing

Nhiều requests cùng snapshot phải:

```text
safe
deterministic
```

---

# 555.162. Concurrent snapshot testing

S1/S2/S3 có thể tồn tại đồng thời.

---

# 555.163. Priority testing

Interactive query phải được scheduler ưu tiên đúng policy.

---

# 555.164. Memory stress

Mở nhiều workspace + nhiều snapshot + nhiều query phải có bounded memory policy.

---

# 555.165. Cache stress

Remote/local cache concurrent access phải atomic.

---

# 555.166. Protocol fuzzing

IPC parser phải được fuzz.

---

# 555.167. Malformed request

Malformed request:

```text
reject
```

không crash daemon.

---

# 555.168. Client crash

IDE chết không được làm daemon state corrupt.

---

# 555.169. Daemon crash

Daemon chết không được corrupt project source/cache.

---

# 555.170. Compiler panic

Internal compiler failure phải isolate request/process tùy severity.

---

# 555.171. Process isolation option

Security-critical daemon deployment có thể chạy compiler workers riêng process.

---

# 555.172. Worker restart

Một worker crash:

```text
restart worker
invalidate affected ephemeral state
reuse persistent cache
```

---

# 555.173. Daemon observability

Metrics:

```text
query latency
queue depth
cache hit/miss
memory
CPU
restarts
cancellations
```

---

# 555.174. No automatic telemetry

Observability local by default; không tự upload.

---

# 555.175. Performance tracing

Có thể trace:

```text
edit
→ query
→ invalidation
→ recomputation
→ codegen
```

---

# 555.176. Incremental build report

```text
changed entities
invalidated queries
reused queries
recompiled artifacts
cache hits
```

---

# 555.177. Why rebuild API

```text
why_rebuilt(SymbolId)
```

phải trả dependency evidence.

---

# 555.178. Why query slow

```text
why_slow(QueryId)
```

có thể hiển thị:

```text
waiting dependency
CPU
cache miss
I/O
memory pressure
```

---

# 555.179. AI daemon planning

AI có thể query:

```text
impact(change)
required_rebuild(change)
```

trước khi thực hiện refactor.

---

# 555.180. AI action boundary

AI semantic query read-only mặc định.

Write actions phải qua explicit transformation API.

---

# 555.181. AI write transaction

```text
AI
 ↓
propose edit
 ↓
semantic validation
 ↓
new snapshot
```

---

# 555.182. No hidden AI mutation

Semantic query không được tự ý sửa source.

---

# 555.183. Daemon package architecture

Đề xuất repository:

```text
compiler/
    daemon/
        server
        protocol
        scheduler
        workspace
        snapshot
        watcher
        query_server
        resource_manager
        recovery
        tests
```

---

# 555.184. Shared engine

Daemon gọi:

```text
compiler::driver
compiler::query
compiler::build
compiler::cache
```

không fork compiler semantics.

---

# 555.185. Protocol schema

Protocol phải machine-readable và versioned.

---

# 555.186. JSON mode

Development/debug có thể dùng JSON IPC.

---

# 555.187. Binary mode

Production IDE có thể dùng binary framed protocol để giảm overhead.

---

# 555.188. Streaming responses

Long-running build có thể stream:

```text
diagnostic
progress
artifact
completion
```

---

# 555.189. Backpressure

Client không đọc response không được làm daemon memory tăng vô hạn.

---

# 555.190. Response limits

Large semantic responses phải hỗ trợ:

```text
pagination
streaming
field selection
```

---

# 555.191. Query field selection

AI có thể yêu cầu:

```text
symbol
signature
type
```

thay vì toàn bộ semantic metadata.

---

# 555.192. Query batching

Nhiều independent semantic queries có thể batch.

---

# 555.193. Query deduplication

Nếu 10 clients hỏi cùng query:

```text
one computation
→ ten consumers
```

---

# 555.194. Shared in-flight query

`Computing` result có thể được nhiều requests await.

---

# 555.195. Cancel semantics for shared query

Cancel một consumer không được cancel computation nếu còn consumers khác.

---

# 555.196. Daemon correctness evidence

Daemon build có thể emit:

```text
DaemonBuildEvidence {
    snapshot
    compiler
    cache_inputs
    reused_results
    recomputed_results
    correctness_validation
}
```

---

# 555.197. Integration with 552

Cached/daemon-generated optimized artifacts vẫn phải tuân theo translation-validation contract.

---

# 555.198. Integration with 554

Persistent state sử dụng semantic cache identity từ `554`.

---

# 555.199. Final daemon contract

Axiom compiler daemon phải:

```text
Fast
Incremental
Persistent
Concurrent
Cancellable
Snapshot-isolated
IDE-friendly
AI-friendly
Recoverable
Deterministic
```

nhưng:

```text
Daemon ≠ semantic authority
Daemon ≠ runtime
Daemon ≠ required compiler component
```

---

# 555.200. Hard invariants

1. Daemon không được thay đổi language semantics.
2. Daemon và one-shot compiler dùng cùng semantic engine.
3. One-shot compiler phải hoạt động không cần daemon.
4. Daemon là optimization của toolchain.
5. Workspace phải có identity ổn định.
6. Source snapshot phải immutable.
7. Snapshot phải có identity.
8. Snapshot phải có source/content fingerprints.
9. Unsaved editor state phải được hỗ trợ.
10. Editor buffer phải được phân biệt filesystem state.
11. Filesystem events không được xem là source truth tuyệt đối.
12. Duplicate filesystem events phải chịu được.
13. Out-of-order filesystem events phải chịu được.
14. Event coalescing không được làm sai source state.
15. File watcher failure không được làm semantic state sai.
16. Content/version validation phải được dùng khi cần.
17. Snapshot diff phải được tính chính xác.
18. Semantic change classification phải tích hợp `486`.
19. Query result phải có identity.
20. Query result phải có dependency information.
21. Query result phải có version/schema.
22. Query dependency phải được track.
23. Dynamic dependencies phải được record.
24. Stale dependencies phải invalidate query.
25. Invalidated query không được xem là Ready.
26. Query cycle phải được detect.
27. Query cancellation không được corrupt shared state.
28. Cancelled query không được publish incomplete result.
29. Shared in-flight query phải hỗ trợ nhiều consumers.
30. Cancel một consumer không được hủy query còn consumer.
31. Snapshot isolation phải được enforce.
32. Request phải gắn snapshot khi semantics phụ thuộc source.
33. Stale request result phải được detect.
34. Stale diagnostics không được hiển thị như current.
35. Stale completion không được áp vào document mới.
36. LSP version phải map được tới source snapshot.
37. Interactive requests phải có priority.
38. Background compilation không được starve interactive requests.
39. Scheduler phải respect dependency ordering.
40. Scheduler phải respect cancellation.
41. Scheduler phải respect resource budgets.
42. Concurrent scheduling phải deterministic về semantics.
43. Parallel queries phải thread-safe.
44. Parallel queries không được tạo semantic races.
45. Query cache eviction không được thay đổi correctness.
46. Memory pressure không được thay đổi semantics.
47. Snapshot reclamation không được reclaim pinned snapshot.
48. Active request phải pin required snapshot.
49. Released snapshot phải có khả năng reclaim.
50. Daemon memory không được tăng vô hạn chỉ vì edit history.
51. Query cache phải có bounded retention policy.
52. Persistent cache phải tách ephemeral query state.
53. Persistent cache phải dùng `554` identities.
54. Cache hit phải qua compatibility validation.
55. Daemon restart phải recover valid persistent cache.
56. Daemon crash không được corrupt cache.
57. Daemon crash không được corrupt source.
58. Partial cache writes không được publish.
59. Persistent state phải có integrity/version validation.
60. Corrupt state phải quarantine hoặc rebuild.
61. Daemon restart không được thay đổi compilation semantics.
62. Daemon warm state không được thay đổi compilation semantics.
63. Cache purge không được thay đổi compilation semantics.
64. One-shot và daemon build phải equivalent.
65. Restarted daemon và continuous daemon phải equivalent.
66. Edit sequence và clean final build phải equivalent.
67. Revert sequence và clean final build phải equivalent.
68. Rapid edits không được tạo stale semantic result.
69. Concurrent snapshots phải isolated.
70. Workspace A không được leak semantic state sang Workspace B.
71. Toolchain contexts phải isolated.
72. Target contexts phải fingerprinted.
73. Configuration snapshot phải immutable.
74. Configuration changes phải trigger correct invalidation.
75. Optimization policy phải là cache dependency.
76. Security policy phải là cache dependency.
77. Numeric policy phải là cache dependency.
78. ABI phải là cache dependency.
79. Target phải là cache dependency.
80. SDK/sysroot phải là dependency khi relevant.
81. Semantic queries phải dùng SymbolId/TypeId khi phù hợp.
82. Text search không được thay thế semantic identity.
83. Incremental parser phải preserve correct source mapping.
84. Recovery AST không được dùng cho production artifact.
85. IDE incomplete syntax phải được tolerate.
86. Build syntax phải remain strict.
87. Incremental name resolution phải preserve correctness.
88. Incremental type checking phải preserve correctness.
89. Incremental trait solving phải preserve correctness.
90. Incremental ownership analysis phải preserve correctness.
91. Incremental MIR phải preserve semantics.
92. Incremental optimization phải integrate `553`.
93. Incremental cache phải integrate `554`.
94. Translation validation phải integrate `552`.
95. Object/link cache phải integrate `420`.
96. Semantic metadata phải integrate `446`.
97. Build graph phải integrate `487`.
98. Refactoring phải integrate `486`.
99. Debug metadata phải có cache identity riêng.
100. Source-map changes không được tự động invalidate semantic cache.
101. Build artifact phải chứa snapshot/source identity cần thiết.
102. Build request phải chứa target.
103. Build request phải chứa configuration identity.
104. Build request phải chứa toolchain identity.
105. Concurrent builds phải có isolated artifact identities.
106. Cancelled builds không được publish incomplete final artifacts.
107. Published artifacts phải verified.
108. Build workers phải không được tự trở thành trusted compiler.
109. Remote daemon phải không được trusted mặc định.
110. Daemon IPC phải versioned.
111. Protocol incompatibility phải được reject.
112. IPC parser phải chống malformed input.
113. Client crash không được corrupt daemon.
114. Daemon crash không được corrupt client source.
115. IPC response phải có request identity.
116. Long-running response phải support backpressure.
117. Large semantic response phải support bounded delivery.
118. Query batching không được thay đổi semantics.
119. Query deduplication không được thay đổi semantics.
120. Deadline không được biến incomplete result thành valid result.
121. Timeout phải được distinguish khỏi cancellation.
122. Background precomputation không được alter results.
123. Speculative result phải gắn snapshot.
124. Speculative result không được commit nhầm snapshot.
125. IDE semantic engine không được duplicate build semantics.
126. AI semantic API phải dùng same compiler semantic database.
127. AI query phải snapshot-bound.
128. AI result phải có provenance.
129. AI explanation phải evidence-based.
130. AI không được fabricate compiler state.
131. AI read-only query không được mutate source.
132. AI source modification phải qua transaction.
133. Refactoring transaction phải atomic.
134. Failed refactoring không được để partial source mutation.
135. File rename phải reconcile identity.
136. File deletion phải invalidate dependents.
137. Manifest change phải refresh build graph.
138. Lockfile change phải refresh dependency identity.
139. External dependency change phải invalidate affected artifacts.
140. Toolchain change phải isolate state.
141. Target change phải isolate target-dependent state.
142. Remote cache phải retain `554` trust requirements.
143. Remote cache failure phải fallback khi policy cho phép.
144. Remote cache artifact phải integrity-check.
145. Cache conflict phải detectable.
146. Cache poisoning phải detectable.
147. Worker result phải be verified.
148. Compiler internal error phải not silently publish artifact.
149. Compiler panic phải not corrupt persistent state.
150. Daemon worker isolation có thể được dùng cho recovery.
151. Worker crash phải recoverable.
152. Persistent query state phải schema-versioned.
153. Schema mismatch phải migrate hoặc invalidate.
154. Old query state không được silently reinterpret.
155. File watcher must not execute arbitrary source/build code.
156. IDE query capability phải least-privilege.
157. Semantic server không cần build-script authority.
158. Build-script authority phải explicit.
159. Network access phải capability-controlled.
160. Daemon không được tự upload source/metadata.
161. Observability không được imply telemetry upload.
162. Metrics phải local/explicit.
163. Trace phải respect privacy policy.
164. Semantic metadata response phải support access control.
165. Private symbols không được leak nếu policy cấm.
166. Shared daemon phải isolate tenants/workspaces.
167. Workspace close phải cancel relevant requests.
168. Workspace close phải release watchers.
169. Workspace close phải release snapshots.
170. Daemon shutdown phải flush critical persistent state.
171. Forced shutdown phải preserve cache integrity.
172. Idle daemon phải consume bounded CPU.
173. Idle daemon phải reclaim unnecessary memory.
174. Daemon must support graceful shutdown.
175. Daemon must support automatic restart/recovery policy.
176. Daemon must support `--no-daemon`/equivalent fallback.
177. Daemon must support cache bypass for forensic comparison.
178. Daemon must support incremental-build tracing.
179. Daemon must support dependency explanation.
180. Daemon must support query diagnostics.
181. Daemon must support performance tracing.
182. Daemon must support protocol fuzz testing.
183. Daemon must support concurrency testing.
184. Daemon must support cancellation testing.
185. Daemon must support restart equivalence testing.
186. Daemon must support cache purge equivalence testing.
187. Daemon must support clean/incremental equivalence testing.
188. Daemon must support multi-workspace testing.
189. Daemon must support multi-target testing.
190. Daemon must support multi-toolchain testing.
191. Daemon must support long-running memory tests.
192. Daemon must support stale snapshot tests.
193. Daemon must support filesystem race tests.
194. Daemon must support malformed IPC tests.
195. Daemon must support worker-crash recovery tests.
196. Daemon must support AI semantic API provenance.
197. Daemon must preserve `552` correctness evidence.
198. Daemon must preserve `554` cache provenance.
199. Daemon must remain an optional acceleration layer.
200. **Final invariant:** Axiom compiler daemon phải cung cấp một compiler engine lâu dài, snapshot-isolated, incremental, concurrent, cancellable và có cache/query persistence, nhưng mọi kết quả phải tương đương với one-shot clean compilation; daemon có thể làm compiler nhanh hơn rất nhiều cho IDE/AI/build liên tục nhưng không được trở thành một nguồn semantics riêng hoặc tạo ra trạng thái mà compiler sạch không thể tái tạo.

**BOOTSTRAP-555: LOCKED.**

---

# NEXT — BOOTSTRAP-556

## BOOTSTRAP-556 — COMPILER FRONTEND PERFORMANCE 2.0, INCREMENTAL LEXING/PARSING, PARALLEL NAME RESOLUTION & FAST SEMANTIC ANALYSIS

Sau daemon, bottleneck tiếp theo cần khóa là **frontend latency**.

Mục tiêu là để một thay đổi nhỏ trong file lớn không khiến lexer/parser/type checker xử lý lại toàn bộ file/project.

Kiến trúc:

```text
                 Source Snapshot
                       │
                       ▼
              Incremental Lexer
                       │
                Token Chunks
                       │
                       ▼
             Incremental Parser
                       │
                  Green Tree
                       │
                 Red/Semantic
                       │
             ┌─────────┴─────────┐
             ▼                   ▼
       Name Resolution      Syntax Queries
             │
             ▼
       Semantic Index
             │
       ┌─────┼─────┐
       ▼     ▼     ▼
     Types Traits Effects
       │     │     │
       └─────┼─────┘
             ▼
            HIR
```

`556` sẽ khóa:

- incremental lexer;
- token chunking;
- green/red tree;
- subtree reuse;
- incremental parser;
- error recovery;
- parallel parsing;
- parallel name resolution;
- symbol indexing;
- scope fingerprints;
- import resolution;
- module interface indexing;
- incremental type checking;
- trait query scheduling;
- semantic memoization;
- UTF-8/Unicode-aware incremental editing;
- parser memory reclamation;
- frontend latency budgets;
- interaction với `555` snapshots;
- interaction với `554` semantic cache;
- interaction với `430` type system;
- interaction với `436` query compiler architecture;
- và quan trọng nhất:

> **Một thay đổi nhỏ ở một vùng source phải chỉ làm frontend xử lý lại vùng thực sự bị ảnh hưởng; compiler không được lấy “file changed” làm lý do mặc định để parse/typecheck lại toàn bộ project.**