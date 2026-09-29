# BOOTSTRAP-559 — COMPILER QUERY ENGINE 3.0, DEMAND-DRIVEN SEMANTIC DATABASE, CYCLE HANDLING, QUERY INVALIDATION, SNAPSHOT REUSE & CROSS-PHASE DEPENDENCY PROOF

**Trạng thái: COMPLETED / LOCKED**

`559` khóa **query engine trung tâm của compiler Axiom**.

Đây là lớp nằm giữa semantic engine, incremental compiler, compiler daemon, cache và scheduler. Mục tiêu là biến compiler thành một hệ thống **demand-driven, incremental, memoized, concurrent nhưng deterministic**.

Các task liên quan trực tiếp:

- `430` — Type System
- `431` — Comptime
- `436` — Compiler Query Architecture
- `487` — Incremental Build Graph
- `552` — Correctness / Translation Validation
- `554` — Semantic Cache
- `555` — Compiler Daemon
- `556` — Incremental Frontend
- `557` — Compiler Memory Architecture
- `558` — Parallel Query Scheduler

---

## 559.1. Query engine là semantic database

Axiom không coi compiler là chuỗi hàm:

```text
parse()
→ resolve()
→ typecheck()
→ lower()
→ optimize()
```

mà là:

```text
                     Semantic Database
                            │
       ┌────────────────────┼────────────────────┐
       ▼                    ▼                    ▼
   Syntax Queries      Semantic Queries      Backend Queries
       │                    │                    │
       ▼                    ▼                    ▼
     AST/HIR          Type/Trait/Ownership      MIR/ABI
                            │
                            ▼
                       Query Graph
```

Mỗi kết quả là một **derived fact** từ một tập input xác định.

---

# 559.2. Core abstraction

```text
QueryKey
    ↓
Query Evaluation
    ↓
QueryResult
    ↓
DependencySet
```

Formal:

```text
R = Q(K, S, C)
```

Trong đó:

- `K` = query key;
- `S` = semantic snapshot;
- `C` = compiler configuration/context;
- `R` = result.

---

# 559.3. QueryKey

```text
struct QueryKey {
    kind: QueryKind
    subject: StableId
    parameters: QueryParameters
    target: TargetId?
    edition: EditionId
    config: ConfigFingerprint
}
```

`QueryKey` phải canonical.

---

# 559.4. Stable identity

Không dùng:

```text
memory address
pointer address
worker id
process-local index
```

làm identity lâu dài.

---

# 559.5. Stable IDs

Các semantic entities dùng:

```text
FileId
ModuleId
PackageId
SymbolId
TypeId
TraitId
ImplId
FunctionId
GenericInstanceId
QueryId
```

---

# 559.6. Snapshot binding

Mỗi semantic query phải xác định snapshot:

```text
QueryContext {
    snapshot_id
    workspace_id
    compiler_version
    target
    edition
    configuration
}
```

---

# 559.7. Input queries

Input queries đọc dữ liệu nền:

```text
file_content
file_metadata
manifest
toolchain
target
configuration
environment
generated_source
resource
```

---

# 559.8. Derived queries

Ví dụ:

```text
tokens(FileId)
syntax_tree(FileId)
module_items(ModuleId)
resolve(NameRef)
type_of(ExprId)
trait_solve(Goal)
layout_of(TypeId)
lower_function(FunctionId)
optimize(FunctionId)
codegen(FunctionId)
```

---

# 559.9. Query purity

Semantic query mặc định phải là:

```text
deterministic
side-effect-free
snapshot-bound
memoizable
```

---

# 559.10. Effectful operations

Filesystem/network/process/build-script không được trở thành implicit semantic query.

Chúng phải đi qua explicit effectful build graph node.

---

# 559.11. Query result

```text
struct QueryResult<T> {
    value: T
    fingerprint: Hash
    dependencies: DependencySet
    diagnostics: Diagnostics
    provenance: Provenance
    validation: ValidationState
}
```

---

# 559.12. Result fingerprint

Fingerprint biểu diễn nội dung semantic của result, không phải địa chỉ bộ nhớ.

---

# 559.13. Fingerprint requirements

Fingerprint phải phụ thuộc vào:

```text
semantic value
relevant compiler version
relevant configuration
target
```

khi các yếu tố đó ảnh hưởng kết quả.

---

# 559.14. DependencySet

```text
DependencySet {
    direct: [Dependency]
    transitive_fingerprint
}
```

---

# 559.15. Dependency

```text
Dependency {
    kind
    key
    fingerprint
}
```

---

# 559.16. Dynamic dependencies

Query có thể chỉ biết dependency sau khi chạy.

Ví dụ:

```text
resolve(name)
```

có thể truy cập module khác dựa trên import đã resolve.

Dependency phải được ghi lại runtime.

---

# 559.17. Dependency recording

Mỗi query evaluation chạy trong:

```text
QueryExecutionContext
```

Context tự động ghi lại các query mà nó gọi.

---

# 559.18. Query stack

```text
Q(A)
 └── Q(B)
      └── Q(C)
```

Engine phải giữ evaluation stack để:

- dependency recording;
- cycle detection;
- diagnostics;
- forensic tracing.

---

# 559.19. Query states

```text
Unknown
Computing
Ready
Invalidated
Cancelled
Failed
Poisoned
```

---

# 559.20. Unknown

Chưa có cached result.

---

# 559.21. Computing

Có computation đang chạy.

---

# 559.22. Ready

Result hợp lệ với current semantic context.

---

# 559.23. Invalidated

Result cũ tồn tại nhưng dependency không còn đảm bảo hợp lệ.

---

# 559.24. Cancelled

Computation bị hủy trước khi có valid result.

---

# 559.25. Failed

Evaluation thất bại.

---

# 559.26. Poisoned

Chỉ dùng cho internal corruption/inconsistent state; không phải semantic error của source.

---

# 559.27. Semantic error

Ví dụ type error **không phải query failure**.

Query vẫn có thể trả:

```text
TypeResult = ErrorType
```

với diagnostic.

---

# 559.28. Error-tolerant semantics

Compiler phải tiếp tục semantic analysis sau nhiều lỗi source nếu có thể.

---

# 559.29. Error recovery value

Dùng sentinel semantic values:

```text
ErrorType
UnknownSymbol
InvalidExpr
ErrorModule
```

---

# 559.30. Không cache diagnostic-only failure như compiler crash

Compiler internal exception và source semantic error phải phân biệt tuyệt đối.

---

# 559.31. Query memoization

Nếu:

```text
Q(K,S,C)
```

đã Ready và inputs tương đương:

```text
reuse result
```

---

# 559.32. Demand-driven

Không query nào được chạy chỉ vì compiler “có thể cần”.

Chỉ chạy khi:

- user request;
- downstream query;
- build requirement;
- explicit background speculation.

---

# 559.33. Lazy semantic analysis

Ví dụ editor chỉ hover một function:

```text
parse relevant file
→ resolve symbol
→ type query
```

không nhất thiết typecheck toàn workspace.

---

# 559.34. Full build

Build sẽ mở rộng demand graph tới toàn bộ artifact cần thiết.

---

# 559.35. Query frontier

Engine duy trì frontier:

```text
Requested
    ↓
Known dependencies
    ↓
Newly discovered dependencies
    ↓
...
```

đến khi result hoàn tất.

---

# 559.36. Query deduplication

Concurrent:

```text
Q(TypeOf, Expr42)
Q(TypeOf, Expr42)
Q(TypeOf, Expr42)
```

phải share computation.

---

# 559.37. Shared future

```text
InFlightQuery {
    key
    owner
    waiters
    cancellation_state
}
```

---

# 559.38. Consumer cancellation

Một waiter cancel không làm query cancel nếu waiter khác còn cần.

---

# 559.39. Query owner

Owner là computation context đầu tiên tạo query.

Owner không có quyền thay đổi semantic result của query.

---

# 559.40. Query stealing

Scheduler có thể chuyển computation sang worker khác.

Query identity không thay đổi.

---

# 559.41. Cross-worker result

Result có thể được publish cho mọi worker sau khi hoàn thành.

---

# 559.42. Immutable result

Sau khi publish:

```text
QueryResult
```

phải immutable.

---

# 559.43. Mutable temporary state

Có thể tồn tại trong evaluation nhưng không được leak ra semantic DB.

---

# 559.44. Query cache hierarchy

```text
L0: worker-local temporary
L1: daemon in-memory query cache
L2: process/shared semantic cache
L3: persistent semantic cache
L4: remote cache
```

---

# 559.45. Cache semantics

Mọi tầng cache phải trả về semantic-equivalent result.

---

# 559.46. Cache is not authority

Semantic cache **không phải nguồn sự thật**.

Nguồn sự thật là:

```text
Source Snapshot
+
Compiler Semantics
+
Target/Config
```

---

# 559.47. Cache verification

Cache entry phải chứa:

```text
input fingerprint
dependency fingerprint
result fingerprint
compiler identity
target identity
schema/version
```

---

# 559.48. Cache hit validation

Cache hit phải validate identity trước khi sử dụng.

---

# 559.49. False cache hit

False hit là **correctness failure**, không phải chỉ là performance bug.

---

# 559.50. Cache miss

Cache miss chỉ gây recomputation.

---

# 559.51. Cross-snapshot reuse

Nếu S1 thay đổi file F:

```text
S1 → S2
```

query không phụ thuộc F có thể reuse.

---

# 559.52. Fingerprint-based reuse

Không cần snapshot ID giống nhau nếu dependency fingerprint tương đương.

---

# 559.53. Snapshot identity

Snapshot ID vẫn cần để xác định context, dù result có thể được reuse.

---

# 559.54. Semantic equivalence

Hai source states khác nhau có thể tạo cùng semantic fingerprint.

Ví dụ whitespace thay đổi.

---

# 559.55. Syntax-only change

Nếu thay đổi chỉ ảnh hưởng formatting và parser semantic identity giữ nguyên, downstream semantic queries có thể reuse.

---

# 559.56. Comment-only change

Comment-only change không được invalidate semantic queries không phụ thuộc comment metadata.

---

# 559.57. Documentation-sensitive query

Nếu doc query phụ thuộc comment:

```text
doc(Symbol)
```

phải invalidate khi documentation thay đổi.

---

# 559.58. Source span changes

Thay đổi vị trí text có thể ảnh hưởng debug/source mapping nhưng không nhất thiết ảnh hưởng semantic identity.

---

# 559.59. Semantic identity vs source location

Phải tách:

```text
SemanticIdentity
SourceLocation
```

---

# 559.60. Stable syntax identity

`556` green tree node identity phải hỗ trợ reuse khi subtree unchanged.

---

# 559.61. Query dependency proof

Mỗi cached result phải có dependency evidence:

```text
Result R
 ├── D1 fingerprint
 ├── D2 fingerprint
 └── D3 fingerprint
```

---

# 559.62. Dependency validation

Khi reuse:

```text
validate(D1)
validate(D2)
validate(D3)
```

---

# 559.63. Transitive validation

Có thể validate bằng transitive dependency fingerprint thay vì traverse toàn graph nếu fingerprint chain đáng tin cậy.

---

# 559.64. Merkle-style semantic graph

Query dependency graph có thể sử dụng Merkle-like fingerprints:

```text
Leaf → hash
Node = H(key + child hashes + own result)
```

---

# 559.65. Fingerprint collision

Hash collision không được được coi là proof tuyệt đối nếu security-critical validation yêu cầu stronger mechanism.

---

# 559.66. Strong identity

Critical artifact validation có thể dùng cryptographic hash + structural validation.

---

# 559.67. Query key canonicalization

Ví dụ:

```text
TypeOf(Expr42)
```

không được tồn tại đồng thời dưới các encoding khác nhau.

---

# 559.68. Generic query parameters

Generic parameters phải canonicalize theo semantic type identity.

---

# 559.69. Target canonicalization

Target triple phải normalized trước QueryKey generation.

---

# 559.70. Configuration canonicalization

Equivalent config phải tạo cùng normalized fingerprint.

---

# 559.71. Environment

Chỉ environment values thực sự ảnh hưởng semantics mới được đưa vào query identity.

---

# 559.72. Hermetic builds

Trong hermetic mode:

```text
undeclared environment
```

không được ảnh hưởng semantic result.

---

# 559.73. Query dependency categories

```text
Source
Syntax
Name
Type
Trait
Ownership
Effect
Layout
ABI
Comptime
MIR
Optimization
Target
Toolchain
Configuration
Resource
```

---

# 559.74. Dependency granularity

Dependency phải càng fine-grained càng tốt nhưng không được hy sinh correctness.

---

# 559.75. Coarse fallback

Nếu engine không thể chứng minh dependency chính xác:

```text
invalidate broader region
```

thay vì reuse không an toàn.

---

# 559.76. Unknown dependency

Unknown dependency → không được cache/reuse result như fully validated.

---

# 559.77. Open-world dependency

External dynamic inputs phải được explicitly represented.

---

# 559.78. Closed-world dependency

Trong closed-world compilation, dependency graph có thể mạnh hơn và cho phép aggressive invalidation/reuse.

---

# 559.79. Query invalidation

Khi input thay đổi:

```text
Input changed
    ↓
Find dependent queries
    ↓
Validate fingerprints
    ↓
Invalidate only affected results
```

---

# 559.80. Eager invalidation

Engine có thể invalidate ngay dependency descendants.

---

# 559.81. Lazy invalidation

Hoặc đánh dấu root dirty rồi validate khi query lại.

Default:

> **lazy validation + dependency fingerprinting**

để tránh storm.

---

# 559.82. Invalidation frontier

Chỉ propagate khi fingerprint thực sự thay đổi.

---

# 559.83. No-op change

Nếu source changed nhưng semantic fingerprint unchanged:

```text
downstream queries remain valid
```

khi dependency contract cho phép.

---

# 559.84. Semantic change

Nếu fingerprint thay đổi:

```text
dependent query → invalid
```

---

# 559.85. Dependency edge

Mỗi edge:

```text
A → B
```

nghĩa là A's result depends on B's result.

---

# 559.86. Reverse dependency index

Engine phải maintain:

```text
B → [A1,A2,...]
```

để tìm consumers nhanh.

---

# 559.87. Reverse index persistence

Reverse index có thể rebuild; không phải semantic authority.

---

# 559.88. Query garbage collection

Unused query results có thể evict.

Đây là **cache eviction**, không phải language GC.

---

# 559.89. Eviction safety

Evict result không được invalidate semantic correctness.

---

# 559.90. Recompute after eviction

Query bị evict chỉ cần recompute.

---

# 559.91. Hot query

Engine có thể giữ query thường xuyên sử dụng.

---

# 559.92. Cold query

Query ít sử dụng có thể evict.

---

# 559.93. Memory budget

Query cache phải respect `557`.

---

# 559.94. Result size accounting

Mỗi result phải có memory estimate/actual accounting.

---

# 559.95. Large result

Large result có thể:

- spill;
- compress;
- mmap;
- persistent cache.

---

# 559.96. Query result serialization

Chỉ các result types có stable serialization mới được persistent cache.

---

# 559.97. Process-local result

Pointer-rich temporary semantic structures không được persist trực tiếp.

---

# 559.98. Persistent semantic result

Phải serialize thành canonical representation.

---

# 559.99. Schema version

Persistent result phải có schema version.

---

# 559.100. Schema migration

Không có migration an toàn → invalidate/recompute.

---

# 559.101. Query cycle

Ví dụ:

```text
Q(A)
 ↓
Q(B)
 ↓
Q(A)
```

phải detect.

---

# 559.102. Cycle error

Nếu cycle không hợp lệ:

```text
E559xxx Recursive semantic dependency
```

---

# 559.103. Legal recursive semantics

Một số recursion là hợp lệ:

- recursive types;
- recursive functions;
- mutually recursive declarations;
- recursive modules trong giới hạn language rules.

Engine không được coi mọi cycle là error.

---

# 559.104. Cycle classification

Cycle phải phân loại:

```text
IllegalCycle
WellFoundedCycle
FixedPointCycle
DeferredCycle
```

---

# 559.105. Well-founded recursion

Query có decreasing measure có thể evaluate theo recursion semantics.

---

# 559.106. Fixed-point query

Một số analysis có thể cần:

```text
X₀
→ F(X₀)
→ F(X₁)
→ ...
→ X*
```

---

# 559.107. Fixed-point requirements

Phải xác định:

- lattice/domain;
- bottom;
- transfer function;
- convergence;
- iteration limit.

---

# 559.108. No infinite fixed-point

Không được loop vô hạn.

---

# 559.109. Widening

Dataflow analyses có thể sử dụng widening nếu cần convergence.

---

# 559.110. Narrowing

Optional để tăng precision sau widening.

---

# 559.111. Fixed-point determinism

Parallel evaluation phải đạt cùng fixed point.

---

# 559.112. Trait solver cycles

Trait solver `426` phải distinguish:

```text
prove
disprove
ambiguous
recursive
overflow
```

---

# 559.113. Query cycle vs trait cycle

Không được trộn hai khái niệm.

---

# 559.114. Comptime recursion

`431` comptime recursion phải có depth/resource limits.

---

# 559.115. Comptime query dependency

Comptime evaluation phải record semantic dependencies.

---

# 559.116. Comptime cache

Same inputs/configuration có thể reuse comptime result.

---

# 559.117. External comptime input

Không được cache nếu external side effect/input không được declared.

---

# 559.118. Query purity enforcement

Compiler phải reject semantic query implementation có undeclared side effects.

---

# 559.119. Query transaction

Evaluation có thể tạo temporary state nhưng commit result chỉ sau successful completion.

---

# 559.120. Atomic publication

```text
Compute
→ Validate
→ Publish
```

Không:

```text
Compute partially
→ expose
```

---

# 559.121. Stale result

Query Q(S1) hoàn thành sau khi S2 hiện tại:

```text
Q(S1) ≠ Q(S2)
```

không được publish vào current snapshot như current result.

---

# 559.122. Stale-but-cacheable

Result S1 vẫn có thể lưu persistent cache nếu identity valid.

---

# 559.123. Snapshot-neutral cache

Cache entry có thể được reuse bởi S2 nếu dependency fingerprints match.

---

# 559.124. Current snapshot check

Publish vào daemon current state phải check snapshot generation.

---

# 559.125. Query generation

Mỗi daemon workspace có monotonic snapshot generation.

---

# 559.126. ABA protection

Snapshot identity/generation phải tránh việc state quay lại cùng superficial identity nhưng semantics khác.

---

# 559.127. Query cancellation

Cancellation phải propagate xuống dependencies khi safe.

---

# 559.128. Dependency still needed

Nếu dependency còn được query khác sử dụng, không cancel shared computation.

---

# 559.129. Cancellation and cache

Cancelled query không được publish normal Ready result.

---

# 559.130. Partial work reuse

Một computation bị cancel có thể lưu intermediate data nếu intermediate identity rõ ràng và safe.

---

# 559.131. Query timeout

Timeout trả:

```text
Timeout
```

không phải semantic failure.

---

# 559.132. Interactive timeout

LSP/AI có thể timeout mà build daemon vẫn tiếp tục computation nếu còn consumers.

---

# 559.133. Query priority

Query scheduler `558` nhận:

```text
priority
deadline
resource estimate
snapshot
```

---

# 559.134. Dependency priority

Critical dependency có thể được priority boosted.

---

# 559.135. No priority semantics

Priority không ảnh hưởng result.

---

# 559.136. Concurrent readers

Ready result phải cho phép concurrent read.

---

# 559.137. Concurrent writers

Một QueryKey chỉ có một authoritative computation tại một thời điểm trong một semantic context.

---

# 559.138. Duplicate computation

Speculative duplicate computation chỉ được phép nếu engine chứng minh:

- không side effects;
- kết quả có thể compare;
- loser không phá cache.

---

# 559.139. Default

Không duplicate computation.

---

# 559.140. Query provenance

Result phải biết:

```text source
query
compiler
dependencies
snapshot
```

---

# 559.141. Provenance graph

```text
Result R
   │
   ├── Query Q
   ├── Snapshot S
   ├── Compiler C
   └── Dependencies
```

---

# 559.142. AI query API

AI có thể hỏi:

```text
why_valid(Q)
why_invalid(Q)
dependencies(Q)
dependents(Q)
fingerprint(Q)
cache_origin(Q)
compute_history(Q)
```

---

# 559.143. AI semantic explanation

AI output phải phân biệt:

```text
Fact
Derived
Unknown
Heuristic
```

---

# 559.144. No fabricated dependency

AI layer không được suy đoán dependency rồi lưu vào semantic DB.

---

# 559.145. Query trace

Debug mode có thể record:

```text
Q1 started
Q2 dependency
Q3 cache hit
Q2 complete
Q1 complete
```

---

# 559.146. Trace determinism

Trace timestamp/order có thể khác giữa runs; semantic result không được khác.

---

# 559.147. Query replay

Compiler phải có khả năng replay selected query graph cho debugging.

---

# 559.148. Query recording

Record:

```text
QueryKey
inputs
dependencies
result fingerprint
compiler build
target
```

---

# 559.149. Query replay verification

Replay có thể verify result fingerprint.

---

# 559.150. Miscompilation integration

`552` có thể query:

```text
why_did_result_change(Q,S1,S2)
```

---

# 559.151. Semantic diff

Engine phải hỗ trợ:

```text
diff(Q,S1,S2)
```

ở mức semantic fingerprint trước khi đi sâu structural diff.

---

# 559.152. Dependency diff

Có thể xác định:

```text
same result
changed dependency
changed result
```

---

# 559.153. Cache explanation

CLI:

```text
axiom cache why <query>
```

có thể giải thích:

```text
HIT
because:
  dependency X fingerprint unchanged
```

---

# 559.154. Invalidation explanation

```text
axiom query why-invalid <id>
```

Ví dụ:

```text
TypeOf(Foo.x)
invalid because
  FieldType(Foo.x)
changed
```

---

# 559.155. Query graph visualization

Tooling có thể export:

```text
.dot
JSON
semantic graph
```

---

# 559.156. Query graph size

Large graphs phải stream/chunk được.

---

# 559.157. Query graph cycle diagnostics

Cycle diagnostic phải chỉ ra:

```text
Q1
 → Q2
 → Q3
 → Q1
```

---

# 559.158. Cycle recovery

Illegal cycle phải produce recoverable semantic state khi có thể, thay vì compiler crash.

---

# 559.159. Panic boundary

Internal query engine bug có thể panic/abort according to compiler policy, nhưng phải generate diagnostic/crash report.

---

# 559.160. Query engine concurrency

Query database phải support:

```text
concurrent read
concurrent independent compute
serialized publication per key
```

---

# 559.161. Lock minimization

Không dùng global compiler lock cho toàn bộ query evaluation.

---

# 559.162. Fine-grained synchronization

Lock scope nên giới hạn:

- index;
- in-flight map;
- publication;
- cache metadata.

---

# 559.163. Immutable semantic snapshots

Snapshot data có thể được shared read-only giữa workers.

---

# 559.164. Copy-on-write

Editor changes có thể sử dụng structural sharing thay vì copy toàn workspace.

---

# 559.165. Query memory lifecycle

Query result reference count/liveness có thể quản lý theo cache policy, không phải language ownership semantics.

---

# 559.166. Memory reclamation

Evicted result chỉ reclaim khi không còn reader.

---

# 559.167. Safe reclamation

Có thể dùng:

- epoch;
- reference counting;
- hazard pointers;
- immutable arenas.

Implementation choice không thay đổi semantics.

---

# 559.168. Query cache compaction

Cache compaction phải không làm mất valid result trước khi replacement atomic.

---

# 559.169. Crash consistency

Persistent query cache phải dùng atomic transaction/write protocol.

---

# 559.170. Corrupt cache

Corrupt cache entry:

```text
reject
→ delete/mark invalid
→ recompute
```

---

# 559.171. Cache poisoning

Cache result phải bind với compiler/toolchain/configuration identity.

---

# 559.172. Remote cache trust

Remote semantic result phải có provenance/integrity validation.

---

# 559.173. Untrusted cache

Nếu trust không đủ:

```text
validate structurally
```

hoặc recompute locally.

---

# 559.174. Query result validation

Critical results có thể require `552` validation.

---

# 559.175. Backend result

Machine-level query:

```text
codegen(FunctionId)
```

phải include:

```text
target
ABI
CPU features
optimization profile
```

---

# 559.176. Optimization dependency

Nếu optimization profile thay đổi:

```text
optimized MIR
codegen
```

phải invalidate đúng phạm vi.

---

# 559.177. Target dependency

x86-64 query không được reuse cho AArch64.

---

# 559.178. Feature dependency

AVX2-enabled result không được reuse cho target không có AVX2 nếu result phụ thuộc feature.

---

# 559.179. ABI dependency

ABI change phải invalidate ABI-dependent queries.

---

# 559.180. Edition dependency

Language edition change phải invalidate queries chịu ảnh hưởng edition.

---

# 559.181. Compiler version

Compiler semantic changes phải invalidate affected query schema/semantic version.

---

# 559.182. Fine-grained compiler invalidation

Compiler patch không nhất thiết invalidate toàn cache nếu query schema/semantic contracts chứng minh compatibility.

---

# 559.183. Schema identity

Mỗi query kind có semantic schema/version.

---

# 559.184. Query implementation version

Implementation version có thể thay đổi mà semantic schema giữ nguyên; reuse chỉ khi correctness contract cho phép.

---

# 559.185. Safe default

Không chứng minh được compatibility → recompute.

---

# 559.186. Build graph integration

`487` build node có thể depend vào query fingerprint thay vì toàn source file.

---

# 559.187. Incremental frontend integration

`556` cung cấp:

```text
green tree reuse
token chunk identity
syntax fingerprints
```

cho query engine.

---

# 559.188. Memory integration

`557` quản lý lifetime của query result storage nhưng không thay đổi query semantics.

---

# 559.189. Scheduler integration

`558` thực thi query DAG.

---

# 559.190. Daemon integration

`555` giữ persistent query database cho workspace.

---

# 559.191. Semantic cache integration

`554` là persistence/cache layer; `559` là semantic authority về dependency validity.

---

# 559.192. Type system integration

`430` queries phải expose:

```text
type_of
expected_type
coercion
trait_candidate
```

---

# 559.193. Comptime integration

`431` queries phải expose:

```text
const_eval
layout_eval
comptime_eval
generated_semantics
```

---

# 559.194. HIR/MIR integration

`436` queries:

```text
hir_of
mir_of
```

phải dependency-track chính xác.

---

# 559.195. Ownership integration

Ownership analysis có thể query local regions independently khi dependency permits.

---

# 559.196. ABI/layout integration

Layout query phải depend vào:

```text
Type
repr
target ABI
alignment rules
feature set
```

---

# 559.197. Object/link integration

Object/link query phải depend vào canonical machine/object inputs.

---

# 559.198. Query correctness contract

Một query implementation chỉ được xem là correct nếu:

```text
same semantic inputs
        ↓
same semantic result
```

bất kể:

```text
worker
scheduler
cache state
evaluation order
```

---

# 559.199. Clean-equivalence theorem

Trong phạm vi semantics được định nghĩa:

```text
Clean Build
      ≡
Incremental Build
      ≡
Cached Build
      ≡
Parallel Build
      ≡
Daemon Build
```

về semantic output.

---

# 559.200. HARD INVARIANTS

1. Query engine là trung tâm semantic derivation của compiler.
2. Mọi derived semantic result phải có QueryKey.
3. QueryKey phải canonical.
4. Query identity không được dựa trên memory address.
5. Query phải snapshot-bound.
6. Query phải target-bound khi target ảnh hưởng semantics.
7. Query phải config-bound khi configuration ảnh hưởng semantics.
8. Query result phải có fingerprint.
9. Query result phải có dependency information.
10. Dependency phải được ghi nhận tự động hoặc explicit.
11. Dynamic dependencies phải được record.
12. Cache result không phải semantic authority.
13. Source snapshot + compiler semantics là semantic authority.
14. Cache hit phải validate identity.
15. False cache hit là correctness failure.
16. Cache miss chỉ được gây recomputation.
17. Eviction không được gây semantic change.
18. Query result sau publication phải immutable.
19. Partial result không được publish như Ready.
20. Semantic source error không phải internal query failure.
21. ErrorType phải hỗ trợ error-tolerant analysis.
22. Demand-driven query là mặc định.
23. Compiler không được eagerly evaluate toàn workspace nếu request không cần.
24. Duplicate in-flight query phải được deduplicate.
25. Concurrent consumers phải share result.
26. Consumer cancellation không được hủy shared query còn consumer.
27. Last-consumer cancellation phải tôn trọng build-critical state.
28. Query computation có thể được scheduler chuyển worker.
29. Worker identity không được ảnh hưởng result.
30. Scheduler order không được ảnh hưởng result.
31. Query evaluation phải deterministic về semantics.
32. Query result publication phải atomic.
33. Stale result không được publish vào current snapshot.
34. Stale result vẫn có thể lưu cache nếu identity hợp lệ.
35. Cross-snapshot reuse chỉ được phép khi dependency contract valid.
36. Fingerprint-based reuse phải preserve correctness.
37. Semantic-equivalent snapshots có thể share result.
38. Comment-only changes không được invalidate semantic queries không phụ thuộc comments.
39. Documentation queries phải phụ thuộc documentation input.
40. Source location phải tách semantic identity.
41. Syntax identity phải hỗ trợ subtree reuse.
42. Dependency graph phải có reverse dependency index.
43. Invalidation phải dựa trên actual dependency.
44. Invalidation phải propagate khi fingerprint thay đổi.
45. No-op semantic changes không nên gây unnecessary downstream invalidation.
46. Nếu dependency precision không đủ, phải invalidate rộng hơn.
47. Unknown dependency không được coi là validated.
48. Query cycle phải được detect.
49. Không phải mọi cycle đều là semantic error.
50. Recursive language semantics phải được hỗ trợ.
51. Fixed-point query phải có convergence model.
52. Fixed-point query phải bounded.
53. Parallel fixed-point computation phải deterministic.
54. Trait cycles phải tách khỏi generic query cycles.
55. Comptime recursion phải bounded.
56. Comptime dependencies phải được record.
57. Undeclared comptime side effects không được trở thành cacheable semantic dependency.
58. Query transaction phải atomic.
59. Failed evaluation không được commit partial semantic result.
60. Cancelled evaluation không được commit Ready result.
61. Timeout không phải semantic failure.
62. Query priority không ảnh hưởng semantics.
63. Query deadline không được tạo invalid artifact.
64. Query cache phải tôn trọng memory budget.
65. Cache eviction phải safe.
66. Large result phải có memory accounting.
67. Persistent result phải có stable serialization.
68. Pointer-local temporary state không được persist trực tiếp.
69. Persistent result phải có schema version.
70. Incompatible schema phải invalidate/recompute.
71. Cache fingerprint phải include relevant compiler identity.
72. Cache fingerprint phải include relevant target identity.
73. Cache fingerprint phải include relevant configuration.
74. Cache fingerprint phải include relevant toolchain identity.
75. Hermetic builds phải reject undeclared environmental dependencies.
76. Remote cache phải có integrity/provenance.
77. Untrusted cache không được bypass validation.
78. Critical query results có thể yêu cầu translation validation.
79. Query provenance phải được preserve.
80. Query graph phải có machine-readable representation.
81. Query dependency explanations phải dựa trên actual graph.
82. AI không được tự thêm semantic dependency.
83. AI query phải snapshot-consistent.
84. LSP query phải snapshot-consistent.
85. Query trace không được thay đổi semantics.
86. Query replay phải có thể verify fingerprint.
87. Miscompilation investigation phải truy nguyên query provenance.
88. Semantic diff phải phân biệt dependency change và result change.
89. Query schema phải versioned.
90. Query implementation compatibility phải explicit.
91. Không chứng minh compatibility → recompute.
92. Type queries phải integrate `430`.
93. Comptime queries phải integrate `431`.
94. HIR/MIR queries phải integrate `436`.
95. Build graph phải integrate `487`.
96. Semantic cache phải integrate `554`.
97. Daemon phải integrate `555`.
98. Incremental frontend phải integrate `556`.
99. Query memory phải integrate `557`.
100. Query scheduler phải integrate `558`.
101. Ownership queries phải preserve `423` semantics.
102. Trait queries phải preserve `426` semantics.
103. Layout queries phải preserve `422` semantics.
104. ABI queries phải preserve `421` semantics.
105. Optimization queries phải preserve `553` semantics.
106. Correctness validation phải preserve `552` semantics.
107. Query result identity không được phụ thuộc cache location.
108. Query result identity không được phụ thuộc worker.
109. Query result identity không được phụ thuộc daemon process lifetime.
110. Query result identity không được phụ thuộc scheduling order.
111. Query result identity không được phụ thuộc hash-map iteration order.
112. Parallel query evaluation phải deterministic.
113. Serial query evaluation phải remain supported.
114. Serial và parallel query results phải equivalent.
115. Cached và uncached query results phải equivalent.
116. Incremental và clean query results phải equivalent.
117. Daemon và one-shot query results phải equivalent.
118. Remote trusted cache và local recomputation phải equivalent.
119. Query database corruption phải fail closed.
120. Corrupt result phải không được publish.
121. Corrupt cache phải không được silently trusted.
122. Cache recovery phải recompute khi cần.
123. Query DB crash recovery phải preserve correctness.
124. Query publication phải atomic.
125. Query eviction phải không làm mất dependency truth.
126. Reverse dependency index không phải semantic authority.
127. Cache metadata không phải semantic authority.
128. Scheduler metadata không phải semantic authority.
129. Performance metrics không phải semantic input trừ khi explicitly part of policy.
130. Speculative queries phải cancellable.
131. Speculative results phải snapshot-bound.
132. Speculation không được alter semantic graph.
133. Duplicate speculative results phải deterministic.
134. Query resource budgets phải explicit.
135. Recursive query expansion phải bounded.
136. Query stack phải record evaluation chain.
137. Cycle diagnostics phải show complete relevant chain.
138. Illegal cycle phải recover gracefully khi có thể.
139. Internal cycle corruption không được masquerade as source error.
140. Fixed-point overflow phải report explicit state.
141. Solver timeout phải distinguish Unknown from False.
142. Query Unknown không được cache như proven False.
143. Query validation state phải preserve uncertainty.
144. AI explanation phải preserve Unknown state.
145. Query result provenance phải survive cache serialization.
146. Cross-snapshot cache reuse phải preserve provenance.
147. Build artifact provenance phải include semantic query dependencies where required.
148. Object/codegen queries phải bind target/ABI/features.
149. PGO queries phải bind profile identity.
150. LTO queries phải bind whole-program dependency state.
151. Generic instantiation queries phải bind canonical generic arguments.
152. Comptime queries phải bind evaluated inputs.
153. Resource queries phải bind resource identity/version/hash.
154. Generated source queries phải bind generator identity/version.
155. Build-script outputs phải bind explicit build graph identity.
156. Environment dependencies phải be explicit.
157. Toolchain dependencies phải be explicit.
158. Configuration dependencies phải be explicit.
159. Query invalidation must never rely solely on timestamps.
160. Content identity phải ưu tiên timestamp identity.
161. File rename phải preserve semantic identity khi possible.
162. File deletion phải invalidate actual consumers.
163. Module rename phải update semantic identities correctly.
164. Import changes phải invalidate dependent resolution queries.
165. Public API change phải invalidate dependent interface queries.
166. Private implementation change không được invalidate unaffected interface queries unnecessarily.
167. ABI change phải invalidate ABI-dependent results.
168. Layout change phải invalidate layout-dependent results.
169. Trait implementation change phải invalidate affected trait queries.
170. Generic implementation change phải invalidate affected instantiations.
171. Optimization profile change phải invalidate optimization-dependent results.
172. Target feature change phải invalidate machine-dependent results.
173. Compiler semantic change phải invalidate affected query schemas.
174. Formatter-only changes không được force full semantic rebuild.
175. Comment-only changes không được force full semantic rebuild.
176. Small source edits phải trigger fine-grained query invalidation where proven safe.
177. Coarse invalidation is allowed when precision cannot be proven.
178. Unsafe reuse is never allowed merely to improve compile speed.
179. Query cache must not become a second inconsistent semantic engine.
180. Query engine must support machine-readable diagnostics.
181. Query engine must support AI semantic inspection.
182. Query engine must support LSP demand queries.
183. Query engine must support build demand queries.
184. Query engine must support test/benchmark demand queries.
185. Query engine must support artifact dependency tracing.
186. Query engine must support correctness provenance.
187. Query engine must support query replay for forensic analysis.
188. Query engine must support deterministic invalidation testing.
189. Query engine must support cache hit/miss equivalence testing.
190. Query engine must support worker-count equivalence testing.
191. Query engine must support snapshot transition testing.
192. Query engine must support concurrent duplicate-query testing.
193. Query engine must support cancellation stress testing.
194. Query engine must support cycle/fixed-point stress testing.
195. Query engine must support cache corruption testing.
196. Query engine must support remote-cache trust testing.
197. Query engine must support daemon restart equivalence testing.
198. Query engine must support clean-vs-incremental semantic comparison.
199. Query engine must support end-to-end source→query→MIR→machine provenance.
200. **Final invariant:** Axiom's query engine phải đảm bảo rằng mọi semantic result đều là hàm xác định của **semantic inputs và dependencies thực sự**, còn cache, snapshot reuse, parallel scheduling, daemon lifetime, worker assignment và evaluation order chỉ là các optimization của computation — không bao giờ được trở thành một semantic model thứ hai.

**BOOTSTRAP-559: LOCKED.**

---

# NEXT — BOOTSTRAP-560

## COMPILER IR OPTIMIZATION PIPELINE 3.0 — SSA/MEMORY-SSA, ANALYSIS MANAGER, PASS DEPENDENCY, FIXPOINT OPTIMIZATION & VERIFIED TRANSFORMATION GRAPH

`560` sẽ khóa tầng optimization ở mức sâu hơn `553`: không chỉ **pass manager/cost model**, mà là **mô hình dữ liệu và dependency của các analysis/pass**.

Trọng tâm:

```text
                         MIR
                          │
                          ▼
                  Canonicalization
                          │
                          ▼
                     SSA Builder
                          │
                 ┌────────┴────────┐
                 ▼                 ▼
             Value SSA        Memory SSA
                 │                 │
                 └────────┬────────┘
                          ▼
                    Analysis DB
                          │
          ┌───────────────┼────────────────┐
          ▼               ▼                ▼
      Alias/Range       Loop/CFG       Effect/Memory
          │               │                │
          └───────────────┼────────────────┘
                          ▼
                   Transformation DAG
                          │
              ┌───────────┼───────────┐
              ▼           ▼           ▼
           Scalar       Memory       Loop
              │           │           │
              └───────────┼───────────┘
                          ▼
                    Vectorization
                          │
                          ▼
                    Specialization
                          │
                          ▼
                    Code Generation
```

`560` sẽ đặc biệt khóa:

- SSA construction/destruction;
- Memory SSA;
- dominance/post-dominance;
- CFG analysis;
- def-use/use-def chains;
- alias analysis;
- range/value analysis;
- effect analysis;
- loop analysis;
- call graph;
- interprocedural summaries;
- analysis invalidation;
- transformation preconditions;
- transformation postconditions;
- fixpoint optimization;
- optimization dependency graph;
- pass ordering;
- speculative optimization;
- deoptimization/fallback khi cần;
- integration với `552` để **mỗi transformation quan trọng có thể được translation-validated**;
- deterministic optimization dù chạy parallel qua `558`.

**NEXT TASK: BOOTSTRAP-560.**