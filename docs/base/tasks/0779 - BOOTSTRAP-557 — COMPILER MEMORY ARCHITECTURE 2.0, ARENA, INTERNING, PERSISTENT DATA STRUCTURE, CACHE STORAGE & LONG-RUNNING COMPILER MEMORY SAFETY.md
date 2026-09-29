# BOOTSTRAP-557 — COMPILER MEMORY ARCHITECTURE 2.0, ARENA, INTERNING, PERSISTENT DATA STRUCTURE, CACHE STORAGE & LONG-RUNNING COMPILER MEMORY SAFETY

**Trạng thái: COMPLETED / LOCKED**

`557` khóa mô hình quản lý bộ nhớ **bên trong compiler**, không phải memory model của chương trình Axiom đã được định nghĩa ở `423`.

Mục tiêu đặc biệt quan trọng đối với `555–556`:

> Compiler daemon có thể chạy hàng giờ hoặc hàng ngày, liên tục nhận hàng nghìn lần edit, nhưng memory không được tăng vô hạn chỉ vì lịch sử snapshot/query/cache.

---

# 557.1. Phạm vi

Có hai memory world hoàn toàn riêng:

```text id="m7m2s8"
┌──────────────────────────────────────────────┐
│              Axiom Program                   │
│                                              │
│  memory model 423                            │
│  ownership / move / allocator / unsafe       │
└──────────────────────────────────────────────┘


┌──────────────────────────────────────────────┐
│              Axiom Compiler                  │
│                                              │
│  compiler memory architecture 557           │
│  arenas / interning / snapshots / caches     │
└──────────────────────────────────────────────┘
```

Compiler có thể dùng kỹ thuật quản lý memory khác với chương trình Axiom.

---

# 557.2. Compiler memory hierarchy

```text id="6v1w2p"
                    Compiler Daemon
                          │
        ┌─────────────────┼─────────────────┐
        ▼                 ▼                 ▼
   Session Memory    Persistent State    OS/File Cache
        │                 │
   ┌────┼────┐            │
   ▼    ▼    ▼            ▼
Arena Intern Query DB   Disk Cache
        │
        ▼
Snapshot Objects
```

---

# 557.3. Memory classes

Compiler memory được chia thành:

```text id="g1x3q9"
Ephemeral
Snapshot
Query
Session
Persistent
Mapped
External
```

Không được trộn lifecycle giữa chúng.

---

# 557.4. Ephemeral memory

Dùng cho:

- temporary parser state;
- temporary vectors;
- intermediate algorithms;
- sort buffers;
- diagnostics;
- optimization scratch.

Lifetime ngắn.

---

# 557.5. Snapshot memory

Chứa dữ liệu thuộc một source snapshot.

Có thể bao gồm:

```text id="9f4p3s"
source
tokens
syntax
semantic overlay
diagnostics
```

---

# 557.6. Query memory

Chứa kết quả của semantic query:

```text id="q4s6n1"
Resolve
TypeOf
TraitSolve
LayoutOf
HIR
```

---

# 557.7. Session memory

Dữ liệu sống lâu hơn snapshot:

- intern table;
- workspace metadata;
- symbol identity maps;
- compiler configuration;
- target descriptions.

---

# 557.8. Persistent memory

Là dữ liệu được serialize ra disk:

- semantic cache;
- parser cache;
- build cache;
- indexes;
- metadata.

Không được coi persistent storage là RAM.

---

# 557.9. Memory ownership graph

```text id="f8q2b7"
Daemon
 │
 ├── Session
 │    ├── Interners
 │    └── Workspace
 │
 ├── Snapshot S1
 │
 ├── Snapshot S2
 │
 └── Query DB
       ├── S1-dependent
       └── Cross-snapshot reusable
```

---

# 557.10. Arena allocation

Compiler được phép sử dụng arena cho object có lifetime đồng nhất.

Ví dụ:

```text id="m2k8v4"
SyntaxArena
HIRArena
MIRArena
DiagnosticArena
QueryScratchArena
```

---

# 557.11. Bump arena

Arena cơ bản:

```text id="y8v1c3"
allocate(size, align)
→ pointer
```

chỉ tăng cursor.

---

# 557.12. Arena destruction

Toàn bộ arena có thể reclaim bằng một thao tác thay vì destroy từng object.

---

# 557.13. Destructor limitation

Không được dùng bump arena cho object yêu cầu destructor quan trọng nếu arena destroy không chạy destructor.

---

# 557.14. Trivial arena objects

Green nodes, immutable metadata và compiler POD-like structures là ứng viên tốt.

---

# 557.15. Drop arena

Nếu object cần destructor:

```text id="0n7d5a"
DropArena
```

phải maintain destruction list hoặc dùng ownership khác.

---

# 557.16. Region ownership

Mỗi arena phải có owner:

```text id="w3r5q8"
Daemon
Workspace
Snapshot
Query
Temporary
```

---

# 557.17. Region lifetime

Object không được giữ reference tới arena có lifetime ngắn hơn object đang giữ reference.

---

# 557.18. Arena references

Compiler implementation có thể dùng raw/internal pointers, nhưng phải có invariant lifetime nội bộ.

Điều này không làm thay đổi semantics của Axiom.

---

# 557.19. Generational arena

Các object persistent theo snapshot có thể dùng generation:

```text id="p6n4x2"
Generation 100
Generation 101
Generation 102
```

---

# 557.20. Generation reclamation

Generation chỉ được reclaim khi không còn live reference/query dependency.

---

# 557.21. Epoch model

Compiler có thể sử dụng epoch để theo dõi:

```text id="s3h8k2"
active readers
published snapshots
background queries
```

---

# 557.22. Snapshot pinning

Query đang chạy phải pin snapshot hoặc dependency objects cần thiết.

---

# 557.23. Snapshot release

Sau khi:

```text id="x9r4d1"
no active query
no persistent reference
no cache ownership
```

snapshot memory có thể reclaim.

---

# 557.24. Old snapshot policy

Daemon không được giữ vô hạn mọi snapshot.

---

# 557.25. Snapshot retention

Retention mặc định chỉ cần đủ cho:

- current snapshot;
- previous useful snapshot;
- active queries;
- undo/refactoring policy nếu được yêu cầu.

---

# 557.26. Explicit historical snapshots

Nếu user/AI yêu cầu historical analysis, snapshot phải được pin explicit.

---

# 557.27. Memory pressure

Khi memory pressure tăng:

```text id="a8m2k7"
drop speculative queries
→ drop cold diagnostics
→ drop cold syntax caches
→ drop old snapshots
→ evict query results
→ compact persistent caches
```

---

# 557.28. Eviction priority

Dữ liệu semantic nóng không được evict trước temporary/speculative data nếu có lựa chọn.

---

# 557.29. Query cache tiers

```text id="h2v6q1"
L0: active query
L1: hot memory cache
L2: session cache
L3: persistent disk cache
```

---

# 557.30. Cache promotion

Query thường xuyên sử dụng có thể được promote.

---

# 557.31. Cache demotion

Query lạnh có thể bị demote hoặc evict.

---

# 557.32. No semantic dependency on cache tier

Kết quả phải giống nhau dù query lấy từ L0, L1, L2 hay recompute.

---

# 557.33. Interning

Compiler có thể intern:

- identifier;
- strings;
- type descriptors;
- trait keys;
- module paths;
- attribute names.

---

# 557.34. String interner

```text id="n7x3w5"
StringId → UTF-8 bytes
```

---

# 557.35. StringId stability

Trong cùng compiler session, StringId phải stable.

---

# 557.36. Persistent StringId

Không được mặc định serialize StringId nội bộ sang cache vì interner session khác có thể có numbering khác.

---

# 557.37. Persistent representation

Persistent cache phải lưu:

```text id="u5c8n2"
string content
```

hoặc canonical content hash.

---

# 557.38. Type interning

Canonical immutable type descriptors có thể intern.

---

# 557.39. Type identity

`TypeId` từ `430/446` phải phân biệt:

```text id="4v7s1m"
nominal identity
generic substitution
structural components
```

theo semantics.

---

# 557.40. Type interning correctness

Hai TypeId chỉ được merge nếu compiler chứng minh chúng cùng semantic type.

---

# 557.41. Generic types

Ví dụ:

```text id="e1s7q3"
Vec<i32>
Vec<i64>
```

phải có identity riêng.

---

# 557.42. Canonical generic substitution

Substitution map phải có canonical representation để tránh tạo duplicate objects.

---

# 557.43. Trait goal interning

Trait solver có thể intern canonical goals.

---

# 557.44. Symbol interning

SymbolId không đồng nghĩa StringId.

```text id="z4k8p1"
"foo"       → StringId
declaration → SymbolId
```

---

# 557.45. Symbol lifetime

Symbol identity phải tồn tại đủ lâu cho semantic references nhưng không bắt buộc giữ toàn bộ snapshot.

---

# 557.46. Symbol tombstones

Symbol bị xóa có thể được biểu diễn trong semantic diff/history nhưng không cần giữ full declaration forever.

---

# 557.47. Intern table growth

Intern table phải có growth policy.

Không được để identifier từ hàng triệu edit làm session memory tăng vô hạn nếu strings không còn cần thiết.

---

# 557.48. Session-local interner compaction

Có thể rebuild interner khi:

```text id="d8m3y7"
no active query
```

và remap IDs.

---

# 557.49. ID remapping

Remapping phải atomic đối với semantic DB.

---

# 557.50. Persistent IDs

Nếu external tool cần stable IDs xuyên session:

```text id="p3q7v2"
StableSymbolKey
```

được dùng thay vì raw session ID.

---

# 557.51. Persistent semantic key

Ví dụ:

```text id="n6r2w8"
package
module
declaration identity
signature fingerprint
```

---

# 557.52. Stable identity ambiguity

Nếu declaration identity không thể xác định chắc chắn:

```text id="q1v7m3"
new identity
```

được phép.

---

# 557.53. Persistent trees

Green tree có thể dùng persistent immutable structure.

---

# 557.54. Structural sharing

Hai snapshots:

```text id="e7x2n9"
S1
 ├─ A
 ├─ B
 └─ C

S2
 ├─ A
 ├─ B'
 └─ C
```

A và C có thể share.

---

# 557.55. Sharing safety

Shared object phải immutable hoặc synchronization-safe.

---

# 557.56. No hidden mutation

Không được mutate green node sau publish.

---

# 557.57. Persistent vectors

Large child arrays có thể dùng persistent vector/rope/chunked arrays.

---

# 557.58. Small-vector optimization

Compiler có thể inline một số lượng nhỏ elements:

```text id="j8w3p2"
SmallVec<T, N>
```

để tránh heap allocation.

---

# 557.59. Allocation minimization

Hot frontend paths phải tránh allocation không cần thiết.

---

# 557.60. Stack scratch

Temporary parser/query buffers nên ưu tiên stack hoặc arena khi kích thước bounded.

---

# 557.61. Heap allocation instrumentation

Compiler debug mode phải có khả năng đếm:

```text id="s4f8k1"
allocations
bytes
peak
retained
```

theo subsystem.

---

# 557.62. Allocation attribution

Ít nhất:

```text id="u2k7m5"
lexer
parser
resolver
typechecker
trait solver
HIR
query DB
LSP
daemon
```

---

# 557.63. Memory profile

Profiler từ `476` phải hỗ trợ compiler memory.

---

# 557.64. Retained memory

Phải phân biệt:

```text id="c9m1v4"
allocated
live
reachable
retained
mapped
```

---

# 557.65. Leak detection

Compiler debug/test build phải có leak detector hoặc equivalent accounting.

---

# 557.66. Logical leak

Object còn reachable nhưng không còn hữu ích cũng được xem là memory-retention problem.

---

# 557.67. Snapshot leak test

Test:

```text id="r6w3k9"
edit
compile
discard snapshot
repeat 1000x
```

memory không được tăng tuyến tính ngoài cache policy cho phép.

---

# 557.68. Daemon soak test

Compiler daemon phải được chạy hàng giờ trong stress test.

---

# 557.69. Edit storm

Test hàng nghìn edits liên tiếp.

---

# 557.70. Query storm

Test hàng nghìn concurrent IDE/AI queries.

---

# 557.71. Cancellation memory

Cancelled query phải release temporary allocations.

---

# 557.72. Failed query memory

Failed query không được giữ partial structures vô thời hạn.

---

# 557.73. Panic/crash recovery

Daemon crash/restart không được yêu cầu persistent in-memory state để correctness.

---

# 557.74. Query ownership

Query result phải có explicit ownership/lifetime semantics.

---

# 557.75. Query dependency retention

Result chỉ giữ dependencies cần thiết cho invalidation/reuse.

---

# 557.76. Dependency compression

Large dependency sets có thể được fingerprint/compress.

---

# 557.77. Dependency graph cycles

Cycle trong query graph phải được phát hiện và xử lý theo `436`.

---

# 557.78. Query recursion

Recursive query không được làm stack/memory tăng vô hạn.

---

# 557.79. Cycle diagnostic

Cycle phải có machine-readable diagnostic.

---

# 557.80. Memoization

Pure deterministic queries nên memoize.

---

# 557.81. Impure query

Query có side effect không được đưa vào ordinary semantic memoization.

---

# 557.82. Build scripts

Build scripts từ `432/487` là external effectful nodes, không được giả định pure.

---

# 557.83. Query result immutability

Published semantic query result phải immutable.

---

# 557.84. Copy-on-write

Mutable analysis structures có thể dùng COW để giảm copy.

---

# 557.85. COW uniqueness

Mutation chỉ được phép khi object ownership/refcount/epoch đảm bảo exclusive.

---

# 557.86. Thread safety

Shared immutable structures có thể đọc đồng thời.

---

# 557.87. Mutable caches

Mutable cache phải synchronization-safe.

---

# 557.88. Lock granularity

Hot cache không được dùng một global lock nếu gây contention rõ ràng.

---

# 557.89. Lock-free option

Lock-free structures có thể được dùng nhưng không phải yêu cầu ngôn ngữ.

---

# 557.90. Deterministic memory semantics

Memory optimization không được làm thay đổi compiler result.

---

# 557.91. Persistent cache format

Cache object:

```text id="k7v3q1"
CacheHeader
SchemaVersion
CompilerBuildId
LanguageEdition
TargetIdentity
DependencyFingerprint
Payload
Checksum
```

---

# 557.92. Cache corruption

Corrupt cache:

```text id="h8m2d4"
invalidate
→ recompute
```

---

# 557.93. Cache version

Schema incompatibility phải trigger migration hoặc rebuild.

---

# 557.94. Cache mmap

Large read-only cache payload có thể mmap.

---

# 557.95. Mmap lifetime

Mapped region phải được unmap khi không còn references.

---

# 557.96. Partial mapping

Large cache không nhất thiết map toàn bộ file.

---

# 557.97. Page locality

Persistent cache layout nên tối ưu access locality cho common queries.

---

# 557.98. Lazy deserialization

Cold data chỉ deserialize khi được query.

---

# 557.99. Zero-copy cache

Byte/string payload có thể được đọc trực tiếp từ mmap nếu representation phù hợp.

---

# 557.100. Endianness

Persistent binary cache phải encode endianness/representation hoặc canonicalize.

---

# 557.101. Pointer prohibition in persistent cache

Raw memory pointers tuyệt đối không được serialize như persistent semantic references.

---

# 557.102. Offset references

Nếu cần internal references:

```text id="m5x8c2"
offset
index
stable key
```

thay vì process pointer.

---

# 557.103. Cache relocation

Mmap ở address khác vẫn phải hoạt động.

---

# 557.104. Persistent object graph

Object graph phải reconstructable mà không phụ thuộc process address.

---

# 557.105. Cache integrity

Checksum/hash phải cover payload và relevant header.

---

# 557.106. Cache authenticity

Nếu cache distribution từ remote source, signature/provenance từ `487/550` có thể được áp dụng.

---

# 557.107. Untrusted cache

Compiler không được execute arbitrary code từ cache.

---

# 557.108. Deserialization safety

Deserializer phải validate:

- bounds;
- lengths;
- offsets;
- enum tags;
- alignment;
- recursion limits.

---

# 557.109. Malformed cache

Malformed cache phải produce controlled failure.

---

# 557.110. Cache bomb protection

Compiler phải giới hạn:

```text id="v7q3n5"
object count
string length
nesting
decompression ratio
```

---

# 557.111. Compression

Cache có thể compress cold sections.

---

# 557.112. Compression policy

Compression không được làm hot-path latency unacceptable.

---

# 557.113. Disk budget

Persistent cache có giới hạn:

```text id="r8m4w1"
max bytes
max entries
max age
```

---

# 557.114. Cache eviction

Eviction có thể LRU/LFU/size-aware nhưng correctness-independent.

---

# 557.115. Cache cleanup

Cleanup phải chạy background, không block interactive query quá mức.

---

# 557.116. Cache lock

Multiple compiler processes phải tránh corrupt cùng cache store.

---

# 557.117. Atomic cache publish

Cache entry:

```text id="x2f7p9"
write temp
→ fsync/policy
→ atomic rename
```

hoặc equivalent.

---

# 557.118. Partial write

Partial cache file không được được nhận diện như valid entry.

---

# 557.119. Cache namespace

Cache phải phân biệt:

```text id="j4q8s2"
workspace
toolchain
target
compiler
profile
```

---

# 557.120. Shared cache

Remote/shared cache chỉ được reuse khi dependency identity đầy đủ.

---

# 557.121. Cache trust

`550` supply-chain trust phải áp dụng nếu cache có thể đến từ untrusted source.

---

# 557.122. Memory budgets

Daemon phải có:

```text id="e6m2r8"
soft memory limit
hard memory limit
```

---

# 557.123. Soft limit

Khi vượt soft limit:

```text id="n3w7p5"
evict
compact
drop speculation
reduce parallelism
```

---

# 557.124. Hard limit

Hard limit yêu cầu graceful resource reduction hoặc request failure.

---

# 557.125. OOM policy

Compiler không được để OOM trở thành corrupted semantic DB.

---

# 557.126. Query admission

Large analysis có thể bị admission control khi memory không đủ.

---

# 557.127. Parallelism adaptation

Memory pressure có thể giảm số worker.

---

# 557.128. Memory-aware scheduler

Scheduler `555` nên biết estimated memory cost của query.

---

# 557.129. Large project mode

Project lớn có thể dùng:

```text id="u8q2m4"
streaming indexing
lazy body analysis
bounded cache
```

---

# 557.130. Small project mode

Project nhỏ có thể ưu tiên latency bằng memory caching mạnh hơn.

---

# 557.131. Adaptive policy

Memory policy có thể tự điều chỉnh theo:

```text id="b7v4k1"
project size
RAM
working set
query frequency
edit rate
```

---

# 557.132. Determinism

Adaptive memory policy không được thay đổi semantic result.

---

# 557.133. Compilation reproducibility

Memory pressure không được thay đổi native artifact semantics.

---

# 557.134. Allocation failure

Compiler internal allocation failure phải produce controlled diagnostic hoặc process termination an toàn.

---

# 557.135. Partial compilation state

Không publish artifact từ compilation đã thất bại do resource exhaustion.

---

# 557.136. Temporary spill

Large algorithms có thể spill intermediate data sang disk.

---

# 557.137. Spill security

Spilled data phải respect workspace security/permissions.

---

# 557.138. Spill cleanup

Temporary spill phải được cleanup sau completion/failure/cancellation.

---

# 557.139. Memory-mapped source

Source file lớn có thể mmap read-only.

---

# 557.140. Source ownership

Syntax nodes không được giữ pointer tới mmap đã unmap.

---

# 557.141. Source slice

String/token slices có thể tham chiếu source storage nếu lifetime được pin.

---

# 557.142. Source detachment

Khi source snapshot bị release, dependent nodes phải:

```text id="p8x3m6"
retain needed data
```

hoặc không còn live.

---

# 557.143. Token zero-copy

Token có thể giữ `(offset,length)` thay vì copy text.

---

# 557.144. Token text extraction

Text được materialize lazy khi cần.

---

# 557.145. Identifier copy avoidance

Common identifier strings nên intern.

---

# 557.146. Diagnostic allocation

Diagnostics có thể giữ source span thay vì copy source text.

---

# 557.147. Diagnostic lifetime

Nếu diagnostic tồn tại sau snapshot:

```text id="g2n7w5"
snapshot pin
```

hoặc copy required data.

---

# 557.148. LSP lifetime

LSP response phải không giữ hidden reference tới snapshot sau khi response complete.

---

# 557.149. AI response lifetime

AI semantic response phải serialize/copy required information trước khi snapshot release.

---

# 557.150. Refactoring transaction

Refactoring operation có thể pin source snapshots trong transaction.

---

# 557.151. Transaction abort

Abort phải release all temporary memory.

---

# 557.152. Transaction commit

Commit tạo new snapshot thay vì mutate old immutable snapshot.

---

# 557.153. Undo

Undo có thể reference previous source content nhưng retention phải bounded/policy-controlled.

---

# 557.154. History storage

Long history nên ở persistent storage, không phải giữ tất cả AST trong RAM.

---

# 557.155. Memory accounting

Mỗi major subsystem phải expose:

```text id="q6v1s8"
resident_bytes
retained_bytes
mapped_bytes
allocation_count
```

---

# 557.156. Memory attribution tree

```text id="m3w8k5"
Total
 ├─ Source
 ├─ Syntax
 ├─ Semantic
 ├─ Query
 ├─ Intern
 ├─ Cache
 ├─ LSP
 └─ Temporary
```

---

# 557.157. AI memory diagnostics

AI tooling có thể query:

```text id="t7p2q4"
memory_summary()
largest_regions()
retained_by(snapshot)
why_retained(object)
```

---

# 557.158. Retention graph

Compiler debug mode có thể tạo:

```text id="v4k8m1"
Object
 ↓
Owner
 ↓
Reference
 ↓
Snapshot/Query
```

để tìm retention leak.

---

# 557.159. Memory leak classification

Phải phân biệt:

```text id="e8r2n6"
true leak
intentional cache
snapshot retention
in-flight query
persistent mapping
fragmentation
```

---

# 557.160. Fragmentation

Compiler phải theo dõi allocator fragmentation.

---

# 557.161. Arena fragmentation

Bump arena không fragmentation bên trong theo allocation pattern, nhưng có internal waste.

---

# 557.162. Slab allocation

Small fixed-size objects có thể dùng slab.

---

# 557.163. Size classes

Compiler allocator có thể group allocations theo size class.

---

# 557.164. Large allocation path

Allocation lớn có thể bypass general slab.

---

# 557.165. Alignment

Internal compiler allocations phải respect platform alignment.

---

# 557.166. Cache locality

Hot query structures nên ưu tiên contiguous storage.

---

# 557.167. Pointer chasing

Critical frontend structures không nên tạo linked-object graph nếu flat arrays/indexes hiệu quả hơn.

---

# 557.168. Index-based references

Ưu tiên:

```text id="z6m2r9"
NodeId
SymbolId
TypeId
QueryId
```

cho persistent semantic structures.

---

# 557.169. Pointer use

Raw pointer nội bộ compiler được phép khi chứng minh lifetime/locality.

---

# 557.170. Pointer persistence

Không pointer nào được escape process lifetime vào persistent state.

---

# 557.171. Generation checking

Debug compiler có thể encode:

```text id="p4x7k2"
index + generation
```

để phát hiện stale references.

---

# 557.172. Stale handle

Access stale handle phải fail loudly trong debug builds.

---

# 557.173. Release behavior

Release compiler phải có behavior xác định, không silent memory corruption.

---

# 557.174. Unsafe compiler internals

Compiler implementation có thể có unsafe sections nhưng phải isolate.

---

# 557.175. Sanitizer integration

`480` phải hỗ trợ sanitizer compiler internals.

---

# 557.176. Thread sanitizer

Concurrent query DB/cache/arena logic phải được race-tested.

---

# 557.177. Address sanitizer

Persistent structure/arena access phải được ASan-like validation.

---

# 557.178. Fuzz allocator

Parser/query fuzzing phải có memory-limit fuzz mode.

---

# 557.179. Long-run correctness

Compiler phải test:

```text id="q2m8v4"
edit
→ analyze
→ query
→ discard
→ repeat
```

và cuối cùng clean compile phải equivalent.

---

# 557.180. Memory determinism

Memory layout của compiler không cần binary-identical giữa runs, nhưng semantic outputs phải deterministic.

---

# 557.181. Cache determinism

Cùng inputs phải produce equivalent cache result bất kể worker scheduling.

---

# 557.182. Persistent cache independence

Build sạch không có cache phải cho cùng semantic/native result như build có cache.

---

# 557.183. Cache purge

`clean cache` không được thay đổi correctness.

---

# 557.184. Daemon restart

Restart daemon không được thay đổi result.

---

# 557.185. Memory pressure equivalence

Compilation dưới memory pressure phải:

```text id="c7n2w8"
finish equivalently
```

hoặc fail rõ ràng do resource limit.

Không được silently produce khác semantics.

---

# 557.186. Resource exhaustion

OOM/cancel/deadline phải không publish partial result.

---

# 557.187. Query checkpoint

Long-running query có thể checkpoint nếu hữu ích.

---

# 557.188. Checkpoint validity

Checkpoint phải versioned và dependency-bound.

---

# 557.189. Memory budget metadata

Compiler diagnostics có thể báo:

```text id="y4m8q1"
estimated memory
actual peak
dominant subsystem
```

---

# 557.190. User-configurable limits

Có thể cấu hình:

```text id="k6r3p9"
compiler.max_memory
compiler.max_cache
compiler.max_workers
```

qua `470`.

---

# 557.191. No hidden global memory

Compiler subsystem không được tạo unbounded process-global cache không chịu eviction.

---

# 557.192. Session shutdown

Daemon shutdown phải release:

- workers;
- snapshots;
- mmap;
- sockets;
- temp files;
- cache locks.

---

# 557.193. Graceful shutdown

Shutdown chờ active requests hoặc cancel theo policy.

---

# 557.194. Crash-safe persistent state

Crash giữa cache write không được corrupt existing valid cache.

---

# 557.195. Atomic metadata

Persistent cache metadata phải publish atomic.

---

# 557.196. Memory architecture API

Compiler internal API nên cung cấp:

```text
Arena
Region
Interner
Handle
SnapshotRef
QueryRef
MemoryBudget
CacheStore
```

---

# 557.197. Abstraction boundary

Compiler algorithms không được phụ thuộc trực tiếp vào OS virtual-memory APIs nếu abstraction tương đương đủ.

---

# 557.198. Platform portability

Memory subsystem phải chạy trên:

- Windows;
- Linux;
- macOS;
- AArch64;
- x86-64;
- WASM host tooling nếu compiler được port.

---

# 557.199. Final memory contract

Compiler daemon phải đạt:

```text id="r8w2m5"
bounded retention
incremental reuse
snapshot isolation
safe reclamation
persistent cache independence
parallel safety
deterministic semantics
memory observability
graceful pressure handling
```

---

# 557.200. HARD INVARIANTS

1. Compiler memory model độc lập với Axiom program memory model.
2. Mọi compiler object phải có lifecycle xác định.
3. Mọi arena phải có owner.
4. Arena không được sống ngắn hơn object phụ thuộc.
5. Object không được giữ reference tới released arena.
6. Green tree phải immutable sau publish.
7. Persistent semantic objects phải immutable hoặc synchronization-safe.
8. Snapshot phải có ownership/lifetime rõ ràng.
9. Query đang chạy phải pin dependency cần thiết.
10. Snapshot không được giữ vô hạn mặc định.
11. Historical snapshot phải được pin explicit.
12. Memory pressure phải có eviction policy.
13. Speculative data phải có thể drop.
14. Cache không được là semantic authority.
15. Cache tier không được thay đổi semantics.
16. Cache purge phải giữ correctness.
17. Daemon restart phải giữ correctness.
18. Clean build phải equivalent cached build.
19. Persistent cache không được chứa process pointers.
20. Mmap cache phải relocatable.
21. Cache format phải versioned.
22. Cache payload phải integrity-checked.
23. Cache deserializer phải bounds-check.
24. Cache deserializer phải chống malformed lengths.
25. Cache phải chống excessive nesting.
26. Cache phải chống decompression/resource bombs.
27. Corrupt cache phải được discard hoặc rebuild.
28. Cache write phải atomic.
29. Partial cache không được publish.
30. Shared cache phải có synchronization.
31. Untrusted cache không được execute code.
32. Persistent IDs không được phụ thuộc session numbering.
33. StringId không phải SymbolId.
34. SymbolId không phải TypeId.
35. Type interning phải semantic-safe.
36. Trait-goal interning phải canonical.
37. Generic substitutions phải canonicalizable.
38. Interner growth phải bounded hoặc compactable.
39. Session interner phải có reclamation strategy.
40. Session compaction phải atomic với semantic DB.
41. Symbol identity không được đoán khi ambiguous.
42. Semantic identity không được phụ thuộc byte offset.
43. Source slices phải pin storage hoặc materialize.
44. Token zero-copy phải respect source lifetime.
45. Diagnostic source references phải remain valid.
46. LSP responses không được giữ hidden snapshot references.
47. AI responses không được giữ hidden snapshot references.
48. Refactoring transaction phải pin required snapshot.
49. Transaction abort phải release temporary state.
50. Transaction commit phải tạo consistent new snapshot.
51. Undo history phải có bounded retention.
52. Long history nên persistent hóa thay vì giữ AST vô hạn.
53. Compiler internal pointers không được escape persistent storage.
54. Internal handles phải có stale-reference strategy.
55. Debug builds phải detect stale handles khi khả thi.
56. Release builds không được silent memory corruption.
57. Arena destruction phải respect destructor requirements.
58. Trivial objects mới nên ưu tiên bump arena.
59. Destructor-required objects phải có explicit cleanup.
60. Snapshot arena phải reclaimable.
61. Query temporary memory phải reclaimable.
62. Cancelled queries phải release temporary allocations.
63. Failed queries không được retain partial state vô hạn.
64. Query result publish phải atomic.
65. Invalid query result không được trở thành Ready.
66. Query dependency graph phải track retention.
67. Dependency graph phải tránh unbounded accidental retention.
68. Query memoization chỉ áp dụng cho deterministic semantics.
69. Effectful operations không được giả định pure.
70. Build scripts không được đưa vào pure semantic cache.
71. Compiler worker scheduling không được thay đổi semantic output.
72. Parallel cache access phải thread-safe.
73. Shared immutable structures có thể đọc concurrently.
74. Mutable caches phải synchronization-safe.
75. Hot caches không nên phụ thuộc global lock.
76. Race detector phải được chạy trên compiler concurrency.
77. Sanitizer phải có compiler-internal mode.
78. Address errors phải được test.
79. Memory leaks phải được test.
80. Logical retention phải được test.
81. Snapshot leak test phải tồn tại.
82. Edit storm test phải tồn tại.
83. Query storm test phải tồn tại.
84. Daemon soak test phải tồn tại.
85. Memory pressure test phải tồn tại.
86. OOM test phải tồn tại.
87. Cancellation memory test phải tồn tại.
88. Cache corruption test phải tồn tại.
89. Cache migration test phải tồn tại.
90. Restart equivalence test phải tồn tại.
91. Cache purge equivalence test phải tồn tại.
92. Clean/cached equivalence phải được kiểm tra.
93. Incremental/clean equivalence phải được kiểm tra.
94. Persistent cache phải có schema identity.
95. Toolchain identity phải fingerprint cache.
96. Compiler build identity phải fingerprint cache.
97. Target identity phải fingerprint target-dependent cache.
98. Language edition phải fingerprint syntax/semantic cache khi relevant.
99. Configuration phải fingerprint affected results.
100. Security policy phải fingerprint security-dependent results.
101. ABI policy phải fingerprint ABI-dependent results.
102. Memory layout không được serialize bằng host pointer.
103. Endianness phải được xác định persistent.
104. Alignment phải được validate khi deserialize.
105. Enum/tag values phải được validate.
106. Offset references phải bounds-check.
107. Mmap regions phải được lifecycle-manage.
108. Large cache phải hỗ trợ lazy loading khi hữu ích.
109. Hot cache phải tối ưu locality.
110. Compiler hot path phải giảm allocation.
111. Small collections nên có small-vector optimization khi phù hợp.
112. Large allocations phải có dedicated path khi cần.
113. Compiler phải account memory theo subsystem.
114. Memory metrics phải distinguish allocated/live/retained/mapped.
115. Memory profile phải distinguish intentional cache và leak.
116. Memory attribution phải có provenance.
117. AI memory diagnostics phải dựa trên evidence.
118. `why_retained` không được suy đoán.
119. Memory policy phải deterministic về semantics.
120. Adaptive cache policy không được thay đổi result.
121. Adaptive worker count không được thay đổi result.
122. Memory pressure không được silently degrade correctness.
123. Resource exhaustion phải produce explicit failure.
124. Partial compilation không được publish artifact.
125. Persistent cache không được chứa unvalidated external data.
126. Compiler cache phải chống cache poisoning.
127. Shared cache phải integrate `550` trust model.
128. Remote cache phải có provenance nếu trusted.
129. Temporary spill phải có lifecycle.
130. Temporary spill phải respect permissions.
131. Temporary spill phải cleanup.
132. Source mmap phải được lifetime-manage.
133. Source snapshot phải immutable.
134. Source edits phải tạo snapshot mới.
135. Old snapshots không được bị mutate.
136. Green-node sharing phải preserve immutability.
137. Persistent data sharing phải preserve ownership.
138. Copy-on-write phải verify uniqueness.
139. COW mutation không được race.
140. Generation-based reclamation phải account active readers.
141. Epoch reclamation không được free active object.
142. Object references phải not outlive owner.
143. Compiler shutdown phải release active resources.
144. Shutdown phải handle cancellation.
145. Shutdown phải handle cache locks.
146. Shutdown phải cleanup temporary files.
147. Shutdown phải unmap persistent mappings.
148. Crash-safe cache publication phải tồn tại.
149. Compiler memory subsystem phải portable.
150. Compiler memory abstraction không được hard-code một OS.
151. Internal allocator có thể khác system allocator.
152. Allocator strategy không được thay đổi compiler semantics.
153. Memory layout optimization không được thay đổi query identity.
154. Memory reuse không được làm aliasing bug.
155. Shared arena objects phải immutable.
156. Arena ownership phải machine-checkable trong debug mode khi khả thi.
157. Memory budget phải integrate `470`.
158. Scheduler phải integrate memory estimates.
159. Query admission phải tôn trọng hard limits.
160. Parallelism có thể giảm khi memory pressure tăng.
161. Interactive request không được bị starvation bởi background memory usage.
162. Background warming phải cancellable.
163. Speculative query memory phải bounded.
164. LSP memory usage phải bounded theo policy.
165. AI query memory usage phải bounded theo policy.
166. Semantic index phải hỗ trợ partial/lazy loading.
167. Large projects không được yêu cầu toàn bộ AST resident mặc định.
168. Cold declarations có thể persistent hóa.
169. Hot declarations nên remain memory-resident.
170. Cache eviction phải không phá semantic identity.
171. Stable external identity phải tách session IDs.
172. Symbol identity migration phải preserve references khi evidence đủ.
173. Ambiguous identity migration phải fail safe.
174. Persistent semantic graph phải reconstructable.
175. Cache schema migration phải explicit.
176. Unsupported cache schema không được silent reinterpret.
177. Memory corruption phải be treated as compiler failure.
178. Memory diagnostics phải be machine-readable.
179. Long-running daemon phải được soak-tested.
180. Thousands-of-edits test phải tồn tại.
181. Thousands-of-queries test phải tồn tại.
182. Multi-workspace memory isolation phải được test.
183. Multi-target memory isolation phải được test.
184. Multi-toolchain memory isolation phải được test.
185. Compiler memory state không được leak giữa workspaces.
186. Compiler memory state không được leak giữa incompatible toolchains.
187. Compiler memory state không được leak giữa incompatible targets.
188. Cache namespaces phải isolate incompatible configurations.
189. Security-sensitive data trong memory phải có retention policy.
190. Secrets không được xuất hiện trong generic memory diagnostics.
191. Debug dumps phải redact sensitive data theo `470/545`.
192. Compiler crash dump phải respect security policy.
193. Persistent cache phải respect workspace security.
194. Memory optimizations phải integrate `552` correctness validation.
195. Incremental memory reuse phải compare clean behavior.
196. Memory subsystem phải expose enough telemetry cho `476`.
197. Memory telemetry không được tự động upload.
198. Compiler memory architecture phải support self-hosted compiler.
199. Không có memory-management optimization nào được trở thành semantic dependency.
200. **Final invariant:** Axiom compiler daemon phải có khả năng **allocate → share → snapshot → incrementally reuse → evict → reclaim → persist → restore** mà không tạo memory growth vô hạn, không tạo dangling semantic state, không phụ thuộc process pointers, và không làm thay đổi kết quả compilation; memory management chỉ là implementation mechanism, còn semantic correctness luôn độc lập với việc dữ liệu đang nằm trên stack, arena, heap, mmap, cache hay đã được recompute.

**BOOTSTRAP-557: LOCKED.**

---

# NEXT — BOOTSTRAP-558

## COMPILER PARALLELISM 2.0 — QUERY SCHEDULER, WORK STEALING, DEPENDENCY-AWARE COMPILATION & DETERMINISTIC PARALLEL CODEGEN

Task tiếp theo sẽ xây lớp song song hóa sâu hơn trên nền `555–557`.

Kiến trúc dự kiến:

```text id="q8w4m2"
                    Compiler Request
                           │
                           ▼
                    Query Scheduler
                           │
                ┌──────────┼──────────┐
                ▼          ▼          ▼
             Lex/Parse   Semantic    Codegen
                │          │          │
                └──────────┼──────────┘
                           ▼
                    Dependency DAG
                           │
              ┌────────────┼────────────┐
              ▼            ▼            ▼
          Worker 0      Worker 1      Worker N
              │            │            │
              └────────────┼────────────┘
                           ▼
                    Deterministic Merge
                           │
                           ▼
                     Query Results
```

`558` sẽ khóa đặc biệt:

- query scheduler;
- dependency DAG scheduling;
- work stealing;
- priority giữa IDE/CLI/AI/background;
- parallel module compilation;
- parallel type/trait queries;
- parallel MIR optimization;
- parallel code generation;
- parallel object emission;
- memory-aware scheduling dựa trên `557`;
- cancellation/deadline;
- starvation prevention;
- deterministic result merging;
- tránh duplicate computation;
- CPU topology/NUMA;
- incremental compilation;
- interaction với `552` translation validation;
- và cơ chế bảo đảm **chạy 1 worker hay 32 workers đều tạo cùng semantics và native artifact tương đương**.