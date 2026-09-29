# BOOTSTRAP-274 — AXIOM COMPILER COMMON INFRASTRUCTURE & QUERY ENGINE

**TRẠNG THÁI: FROZEN / COMPLETED**

Đây là tầng hạ tầng thấp nhất của compiler. Mục tiêu là khóa các primitive mà mọi subsystem phía trên sẽ dùng chung, đặc biệt là **CompilerDB + incremental query engine**.

Nguyên tắc quan trọng:

> **CompilerDB là semantic database; QueryEngine là cơ chế tính toán và duy trì database đó.**

Không để từng subsystem tự tạo cache/invalidation riêng.

---

# 1. Kiến trúc tổng thể

```text
                         CompilerDB
                             │
                    ┌────────┴────────┐
                    │                 │
               Immutable Data     Query Engine
                    │                 │
                    │        ┌────────┼────────┐
                    │        │        │        │
                    │      Cache   Dependency Revision
                    │        │        │        │
                    └────────┴────────┴────────┘
                             │
                         Semantic DB
```

---

# 2. Common layer

`compiler/common` chứa:

```text
common/
├── ids/
├── arena/
├── index/
├── intern/
├── hash/
├── fingerprint/
├── span/
├── revision/
├── bitset/
├── collections/
├── graph/
├── sync/
├── diagnostics/
└── serialization/
```

Không chứa:

```text
Type
Trait
MIR
Ownership
ABI
LLVM
```

---

# 3. Typed IDs

Mọi semantic entity dùng ID riêng:

```text
struct FunctionId(u32)
struct TypeId(u32)
struct ModuleId(u32)
struct TraitId(u32)
```

Không cho API nhận `u32` tùy ý.

Ví dụ:

```text
get_function(FunctionId)
```

thay vì:

```text
get_function(u32)
```

---

# 4. ID invariants

```text
ACOMMON-20
Different semantic entity kinds must have different ID types.

ACOMMON-21
A TypeId cannot be passed where FunctionId is required.

ACOMMON-22
ID representation is implementation-defined.

ACOMMON-23
Semantic identity must not depend on memory address.

ACOMMON-24
IDs must remain stable for their intended database lifetime.

ACOMMON-25
Stale IDs must be detectable where the underlying storage permits invalidation.
```

---

# 5. ID representation

Bootstrap có thể:

```text
struct TypeId(u32)
```

Nhưng thiết kế API phải cho phép sau này đổi thành:

```text
struct TypeId {
    index: u32
    generation: u32
}
```

mà không thay đổi frontend semantics.

---

# 6. Arena

Compiler cần arena cho object immutable:

```text
Arena<T>
```

API cơ bản:

```text
alloc(value) -> ArenaId<T>
get(id) -> &T
```

---

# 7. Arena không được dùng như semantic identity

Không:

```text
TypeId = memory address
```

Arena location chỉ là storage.

---

# 8. Typed arena

Nên có:

```text
Arena<Function>
Arena<Type>
Arena<Trait>
Arena<HIRNode>
Arena<MIRBody>
```

thay vì một arena `Any`.

---

# 9. Arena lifetime

Semantic object tồn tại ít nhất trong revision/query scope tương ứng.

Không trả reference có lifetime vượt quá storage owner.

---

# 10. Immutable semantic objects

Sau khi publish:

```text
Function
Type
Trait
HIR
MIR
```

nên immutable.

Thay đổi tạo revision mới hoặc object mới.

Điều này rất quan trọng cho parallel query.

---

# 11. `IndexVec`

Compiler có rất nhiều:

```text
LocalId
BasicBlockId
InstructionId
FieldId
```

Nên có:

```text
IndexVec<I, T>
```

để truy cập:

```text
locals[LocalId]
blocks[BasicBlockId]
```

---

# 12. Lợi ích

Thay:

```text
Vec<Local>
```

bằng:

```text
IndexVec<LocalId, Local>
```

compiler có type safety ở compile time.

---

# 13. StableMap

Khi cần map semantic ID → data:

```text
StableMap<K,V>
```

iteration order phải deterministic.

Không phụ thuộc random hash seed nếu kết quả được expose.

---

# 14. Deterministic hashing

Phải phân biệt:

```text
HashForLookup
FingerprintHash
RandomizedHash
```

Không dùng một loại hash cho mọi mục đích.

---

# 15. Fingerprint

`Fingerprint` dùng để phát hiện semantic equality/change:

```text
struct Fingerprint(u128)
```

hoặc representation tương đương.

Không nên coi fingerprint là cryptographic identity.

---

# 16. Fingerprint phải canonical

Ví dụ:

```text
struct A {
    x: i32
    y: i32
}
```

fingerprint không được thay đổi chỉ vì:

```text
HashMap iteration order
thread scheduling
arena address
```

---

# 17. Semantic fingerprint

Fingerprint của declaration cần phản ánh:

```text
name
signature
generic parameters
constraints
effects
repr
ABI
public semantic dependencies
```

tùy visibility.

---

# 18. Codegen fingerprint

Tách khỏi semantic fingerprint:

```text
SemanticFingerprint
CodegenFingerprint
```

Ví dụ thay instruction scheduling:

```text
SemanticFingerprint = unchanged
CodegenFingerprint = changed
```

---

# 19. Revision model

CompilerDB có:

```text
RevisionId
```

Mỗi lần source/build input thay đổi:

```text
Revision N
    ↓
Revision N+1
```

---

# 20. Revision không nhất thiết copy toàn bộ database

Database giữ immutable/shared data:

```text
Revision N
   │
   ├── unchanged objects
   ├── changed source
   └── new query results
```

---

# 21. Source update

Ví dụ:

```text
foo.ax
bar.ax
```

sửa `foo.ax`.

Revision mới chỉ invalidates query phụ thuộc vào `foo.ax`.

---

# 22. Query model

Một query:

```text
parse_file(SourceFileId)
```

được biểu diễn:

```text
QueryKey {
    kind
    input
}
```

---

# 23. Query result

```text
QueryResult<T> {
    value: T
    fingerprint: Fingerprint
}
```

có thể kèm:

```text
diagnostics
dependencies
```

nhưng dependency tracking nên do engine quản lý tự động.

---

# 24. Query dependency tracking

Nếu:

```text
type_check(FunctionId)
```

gọi:

```text
resolve(FunctionId)
```

thì engine tự ghi:

```text
type_check(F)
    depends_on
resolve(F)
```

Không yêu cầu programmer viết dependency list thủ công.

---

# 25. Query graph

Ví dụ:

```text
codegen(F)
   │
   ├── abi(F)
   │      └── layout(T)
   │
   └── optimize(F)
          └── verify(F)
                 └── mir(F)
                        └── type_check(F)
                               └── resolve(F)
                                      └── parse(M)
                                             └── source(file)
```

---

# 26. Dependency edge

Mỗi query execution có:

```text
DependencyEdge {
    parent
    child
}
```

Nhưng graph runtime không nhất thiết phải giữ toàn bộ dưới dạng object nặng; có thể lưu compact representation.

---

# 27. Query cache

Cache key:

```text
QueryKey
+
InputFingerprint
+
RelevantRevision
```

Không chỉ dùng:

```text
FunctionId
```

vì FunctionId có thể tồn tại qua nhiều revision.

---

# 28. Query memoization

Nếu query đã tính:

```text
type_of(expr42)
```

và dependencies chưa thay đổi:

```text
→ reuse result
```

---

# 29. Verification của cache

Cache hit phải chứng minh dependency facts vẫn valid.

Không được:

```text
cache hit → assume valid
```

mà không kiểm tra dependency revisions/fingerprints.

---

# 30. Dependency fingerprint

Mỗi query có:

```text
output fingerprint
```

Nếu dependency fingerprint không đổi:

```text
parent query
```

có thể giữ nguyên.

---

# 31. Fine-grained invalidation

Không invalidate toàn module chỉ vì một private function thay đổi nếu dependency graph chứng minh không cần.

---

# 32. Public/private dependency

Ví dụ:

```text
pub fn api() {
    helper()
}
```

thay đổi body `helper()` có thể invalidate codegen của `api` nhưng không nhất thiết invalidate public type information.

---

# 33. Query categories

Nên phân loại:

```text
Input Query
Parse Query
Semantic Query
Verification Query
Optimization Query
Codegen Query
Build Query
Tooling Query
```

---

# 34. Input Query

Ví dụ:

```text
source_text(file)
package_manifest(package)
build_config()
target_spec()
```

Input query được set bởi caller.

---

# 35. Pure Query

Ví dụ:

```text
parse
resolve
type_of
layout
verify
```

phải deterministic.

---

# 36. External Query

Ví dụ:

```text
filesystem metadata
SDK discovery
environment
compiler executable
```

phải được mô hình hóa thành explicit input.

Không cho query tự gọi filesystem tùy ý.

---

# 37. Comptime

Comptime external access cũng phải đi qua dependency system:

```text
comptime query
      ↓
ExternalInput
      ↓
Fingerprint
```

---

# 38. Cycle detection

Query graph có thể gặp:

```text
A → B → C → A
```

Engine phải phát hiện.

---

# 39. Không được deadlock vì cycle

Cycle phải trở thành:

```text
QueryCycle
```

để semantic layer quyết định:

```text
error
recursive semantics
fixed point
```

tùy query.

---

# 40. Semantic recursion

Không phải cycle nào cũng là compiler error.

Ví dụ type:

```text
struct Node {
    next: Box<Node>
}
```

là semantic recursion hợp lệ.

Vì vậy:

> Query cycle detection ≠ semantic recursion detection.

---

# 41. Query cycle handler

Conceptual:

```text
on_cycle(QueryStack) -> CycleResult
```

Query engine không tự quyết định semantics.

---

# 42. Query stack

Thread-local:

```text
QueryStack
```

ghi:

```text
current query
parent query
depth
```

dùng cho:

- cycle detection
- diagnostics
- profiling
- debugging.

---

# 43. Recursion depth

Compiler phải có giới hạn:

```text
max_query_depth
max_trait_depth
max_comptime_steps
```

để tránh compiler bị treo.

---

# 44. Parallel queries

Nếu:

```text
parse(A)
parse(B)
parse(C)
```

độc lập:

```text
parallel execution
```

được phép.

---

# 45. Query scheduler

Scheduler nên:

```text
discover dependencies
execute ready queries
publish results
wake dependents
```

---

# 46. Deterministic publication

Thứ tự thread hoàn thành không được quyết định semantic ordering.

---

# 47. Query result publication

Kết quả chỉ publish khi:

```text
query completed
dependencies validated
fingerprint computed
diagnostics finalized
```

---

# 48. Cancellation

IDE có thể hủy compilation cũ:

```text
Revision N
```

khi user gõ tiếp:

```text
Revision N+1
```

---

# 49. Cancellation semantics

Cancellation chỉ dừng computation.

Không được coi:

```text
cancelled
```

là:

```text
semantic failure
```

---

# 50. Poisoning

Nếu query panic/crash nội bộ:

```text
QueryFailure
```

cache entry không được coi là valid result.

---

# 51. Compiler crash isolation

Production compiler nên:

```text
catch internal failure
→ ICE diagnostic
→ preserve source state
```

trừ lỗi process-level không thể recover.

---

# 52. ICE

Internal compiler error phải chứa:

```text
query
revision
compiler version
target
diagnostic context
stack/provenance
```

nhưng không expose secrets.

---

# 53. Query statistics

Engine phải có counters:

```text
query_calls
cache_hits
cache_misses
recomputations
cycle_count
cancelled
parallel_tasks
```

---

# 54. Query tracing

Có thể bật:

```text
--query-trace
```

cho AI/compiler developers.

Ví dụ:

```text
type_of(expr42)
 ├── resolve(expr42)
 ├── trait_solve(...)
 └── normalize(...)
```

---

# 55. Query profiling

Mỗi query có:

```text
start
duration
memory
cache status
dependency count
```

---

# 56. Query memory

Compiler không nên giữ mọi intermediate representation mãi mãi.

Có ba mức:

```text
hot
warm
cold
```

---

# 57. Hot

Ví dụ:

```text
currently edited file
active IDE queries
```

giữ trong memory.

---

# 58. Warm

Compiled package semantic database có thể giữ cache.

---

# 59. Cold

Disk cache:

```text
.axcache/
```

---

# 60. Persistent query cache

Không serialize trực tiếp pointer/reference nội bộ.

Chỉ serialize:

```text
stable semantic IDs
canonical data
fingerprints
version
target/config
```

---

# 61. Cache compatibility

Disk cache header:

```text
CacheHeader {
    format_version
    semantic_compiler_version
    codegen_version
    target
}
```

Nếu incompatible:

```text
invalidate
```

không cố đọc.

---

# 62. Security

Cache artifact phải được coi là untrusted data.

Không deserialize:

```text
arbitrary executable object
```

---

# 63. Content-addressed cache

Artifact/query result có thể được lưu:

```text
cache/<fingerprint>
```

---

# 64. Cache poisoning protection

Hash collision hoặc corrupted artifact phải dẫn tới:

```text
cache miss / rejection
```

không semantic corruption.

---

# 65. Interning

Interning phù hợp với:

```text
Type
Symbol
GenericArgs
ConstValue
EffectSet
```

---

# 66. Không intern mọi thứ

Không intern:

```text
temporary diagnostic
large MIR body
large source buffers
```

một cách mặc định.

---

# 67. String interning

Compiler nên có:

```text
SymbolId
```

cho identifier phổ biến.

Source text vẫn giữ nguyên để diagnostics.

---

# 68. Symbol identity

```text
"foo"
```

→:

```text
SymbolId
```

nhưng:

```text
SourceSpan
```

vẫn trỏ tới source.

---

# 69. Unicode

Symbol interning không được tự ý normalize Unicode.

Axiom lexer đã khóa:

> Unicode normalization không implicit.

---

# 70. BitSet

Verifier cần bitset cực nhiều:

```text
live locals
initialized locals
moved locals
capabilities
basic blocks
```

Do đó:

```text
BitSet<I>
```

phải typed.

---

# 71. Graph infrastructure

Compiler cần generic:

```text
Graph<NodeId, Edge>
```

nhưng semantic graph không nên phụ thuộc graph implementation.

---

# 72. CFG

MIR CFG:

```text
BasicBlockId
```

là node identity.

---

# 73. Dominator

OptIR cần:

```text
DominatorTree
PostDominatorTree
LoopInfo
```

được xây từ CFG.

---

# 74. Dataflow framework

Đã frozen ở verifier.

Common layer cung cấp:

```text
DataflowAnalysis<State>
```

với:

```text
initial()
transfer()
join()
equals()
```

---

# 75. Forward analysis

Dùng cho:

```text
ownership
initialization
capability
storage
```

---

# 76. Backward analysis

Dùng cho:

```text
liveness
drop placement
escape
```

---

# 77. Worklist

Generic:

```text
Worklist<NodeId>
```

phải hỗ trợ deterministic mode.

---

# 78. Deterministic worklist

Khi nhiều node ready:

```text
lowest stable NodeId first
```

hoặc canonical ordering.

Không dùng completion timing để quyết định semantic result.

---

# 79. Thread-safe caches

Không cần mọi cache đều lock-free.

Ưu tiên:

```text
correctness
determinism
```

sau đó mới optimize contention.

---

# 80. Compiler internal locking

Không giữ lock trong khi gọi arbitrary semantic query nếu có thể tránh.

Tránh:

```text
lock A
 → query B
   → lock A
```

deadlock.

---

# 81. Recommended architecture

```text
immutable DB state
+
concurrent memo tables
+
short critical sections
```

---

# 82. Query API

Conceptual:

```text
trait Query {
    type Key
    type Value

    fn execute(db: &CompilerDB, key: Key) -> Value
}
```

Engine bao quanh:

```text
execute
dependency tracking
cache
cycle detection
profiling
```

---

# 83. Query implementation không tự quản cache

Không:

```text
fn type_of(...) {
    static CACHE: ...
}
```

---

# 84. Một cache duy nhất

```text
CompilerDB
   ↓
QueryEngine
```

tránh:

```text
TypeDB cache
TraitDB cache
MIR cache
```

mỗi nơi một kiểu invalidation.

Subsystem có thể có local algorithmic memoization, nhưng semantic query cache phải thuộc query engine.

---

# 85. Database layering

```text
CompilerDB
├── InputStorage
├── SyntaxStorage
├── SemanticStorage
├── VerificationStorage
├── OptimizationStorage
├── CodegenStorage
└── BuildStorage
```

---

# 86. Input mutability

Chỉ input layer được mutation trực tiếp:

```text
set_source()
set_target()
set_config()
set_dependency()
```

Các semantic layers đọc chúng.

---

# 87. Revision transaction

Source update:

```text
begin_revision()
set_input(...)
commit_revision()
```

Nếu compile fail:

```text
revision vẫn hợp lệ
```

vì semantic failure khác database corruption.

---

# 88. Snapshot

IDE có thể tạo:

```text
CompilerSnapshot
```

để query nhất quán trong một revision.

---

# 89. Snapshot semantics

Mọi query trong snapshot nhìn thấy cùng:

```text
RevisionId
```

Không bị source update giữa chừng.

---

# 90. Concurrent IDE

Có thể:

```text
Editor
   ↓
Revision N+1

Compiler
   ↓
Revision N
```

chạy song song.

---

# 91. Old revision cleanup

Khi không còn client/query sử dụng:

```text
Revision N
```

có thể garbage-collect **compiler database objects**.

Điều này không liên quan tới GC của Axiom language.

---

# 92. Đây là một distinction quan trọng

Axiom source:

> không có mandatory GC.

Compiler implementation:

> hoàn toàn có thể dùng GC hoặc memory reclamation nếu implementation language/framework hỗ trợ.

Không được trộn hai vấn đề.

---

# 93. Serialization

Compiler semantic snapshot có thể serialize:

```text
.axdb
```

đã được đề xuất ở task 189.

---

# 94. `.axdb`

Có thể chứa:

```text
source fingerprints
declarations
types
traits
public API
semantic metadata
diagnostics
```

Không bắt buộc chứa toàn bộ MIR/codegen.

---

# 95. `.axmeta`

Khác:

```text
.axdb
```

là compiler/IDE semantic database.

```text
.axmeta
```

là package/binary interface metadata.

---

# 96. `.axcache`

Là compiled cache:

```text
.axcache/
```

Ba khái niệm không được nhập làm một:

```text
.axdb
.axmeta
.axcache
```

---

# 97. Common error type

Compiler nội bộ nên có:

```text
CompilerError
```

nhưng phân biệt:

```text
UserDiagnostic
InternalError
Cancelled
QueryCycle
CacheCorruption
```

---

# 98. Không dùng exception cho semantic control flow

Semantic rejection là data:

```text
Diagnostic
```

không phải exception.

---

# 99. Panic chỉ dành cho violated compiler invariant

Ví dụ:

```text
unreachable invariant
```

có thể tạo ICE.

Không dùng panic cho:

```text
type mismatch
```

---

# 100. Query result categories

Nên phân biệt:

```text
Success
SuccessWithDiagnostics
SemanticError
Incomplete
Cancelled
InternalFailure
```

---

# 101. Partial mode

IDE có thể nhận:

```text
Incomplete
```

nhưng production compilation không được coi nó là verified.

---

# 102. Common source map

Compiler cần mapping:

```text
SourceSpan
 ↕
HIR
 ↕
MIR
 ↕
OptIR
 ↕
LIR
 ↕
MachineIR
 ↕
Machine code
```

---

# 103. Source provenance

Mọi compiler IR node quan trọng nên có:

```text
Origin {
    SourceSpan
    parent_origin
}
```

hoặc compact equivalent.

---

# 104. Debug information

Debug map không nên làm thay đổi semantics.

---

# 105. Stable semantic IDs cho tooling

IDE có thể giữ:

```text
FunctionId
```

qua query revisions nếu declaration identity vẫn được nhận diện là cùng declaration.

---

# 106. Declaration identity

Không dùng source line number làm identity.

Nếu function di chuyển dòng:

```text
line 20 → line 50
```

không có nghĩa semantic identity phải đổi.

---

# 107. Incremental identity

Có thể dùng:

```text
syntax identity
+
module
+
declaration kind
+
stable semantic matching
```

để preserve IDs.

---

# 108. Không over-engineer stable IDs ở bootstrap

Initial implementation có thể tạo IDs mới sau source replacement, miễn dependency invalidation đúng.

Stable cross-revision IDs là optimization/tooling feature.

---

# 109. Compiler memory ownership

CompilerDB owns:

```text
source
syntax
semantic objects
query cache
```

Query caller chỉ mượn kết quả hoặc giữ immutable handles.

---

# 110. Không trả raw mutable references

Semantic query:

```text
get_type(TypeId)
```

trả immutable reference/view hoặc owned snapshot.

---

# 111. Mutation model

Semantic transformation:

```text
old MIR
  ↓
new MIR
```

không mutate old MIR đang được query khác sử dụng.

---

# 112. Đây là nền tảng cho parallel compilation.

---

# 113. Query engine bootstrap implementation

Ban đầu có thể đơn giản:

```text
single-threaded
memoized
revision-aware
```

Sau đó thêm:

```text
parallel
persistent cache
remote cache
```

mà không đổi query API.

---

# 114. Không nên xây distributed compiler ngay

Remote compilation/cache là optimization sau này.

---

# 115. Phase 1 query engine

```text
Input
→ memoization
→ dependency tracking
→ invalidation
```

---

# 116. Phase 2

```text
parallel execution
```

---

# 117. Phase 3

```text
disk cache
```

---

# 118. Phase 4

```text
remote/content-addressed cache
```

---

# 119. Phase 5

```text
distributed build execution
```

nếu thực sự cần.

---

# 120. Compiler startup

`CompilerDB` tạo từ:

```text
CompilerConfig
```

gồm:

```text
workspace
target
profile
features
environment
cache_dir
diagnostic_mode
```

---

# 121. `TargetSpec`

Không để backend tự phát minh target.

```text
CompilerConfig
 ↓
TargetSpec
 ↓
ABI
 ↓
Backend
```

---

# 122. Profile

```text
Debug
Release
Size
Test
Reproducible
Freestanding
```

Profile là input query.

---

# 123. Feature set

Feature resolution xảy ra trước semantic compilation như task 187 đã khóa.

---

# 124. Compiler configuration fingerprint

Phải bao gồm:

```text
target
profile
features
optimization
debug
panic mode
overflow mode
fast-math
GPU features
```

khi chúng ảnh hưởng semantics/codegen.

---

# 125. Build identity

```text
BuildFingerprint =
    Source
  + Dependencies
  + CompilerSemanticVersion
  + Target
  + ABI
  + Features
  + ComptimeInputs
  + Profile
  + Codegen
```

---

# 126. Common infrastructure must not encode Axiom syntax

Ví dụ:

```text
common/parser
```

không được biết:

```text
Option<T>
view<T>
mut_view<T>
```

Semantic layers mới biết.

---

# 127. Common infrastructure must be reusable

Sau này:

```text
ax-ref
ax-mir
axc
IDE
language server
```

đều dùng chung:

```text
SourceSpan
Fingerprint
IDs
Diagnostics
CompilerDB queries
```

---

# 128. AI tooling

AI query:

```text
ax context FunctionId
```

phải lấy trực tiếp:

```text
Type
Ownership
Effects
Dependencies
Diagnostics
SourceSpan
```

từ CompilerDB.

---

# 129. AI không được mutate semantic DB trực tiếp

AI đề xuất:

```text
edit source
```

sau đó compiler re-query.

---

# 130. Compiler remains authority

Luồng:

```text
AI suggestion
 ↓
source edit
 ↓
CompilerDB
 ↓
semantic verification
```

không phải:

```text
AI says valid
 ↓
compiler trusts AI
```

---

# 131. Query engine API conceptual

```text
db.query(QueryKey)
```

với engine tự:

```text
lookup cache
detect recursion
record dependency
execute
fingerprint
publish
```

---

# 132. Query context

Mỗi execution có:

```text
QueryContext {
    db
    revision
    cancellation
    diagnostics
    stack
    budget
}
```

---

# 133. Budget

Query có thể có:

```text
max_steps
max_depth
max_memory
timeout/cancellation token
```

Timeout chỉ là tooling/build policy, không phải semantic meaning.

---

# 134. Query cancellation

Compiler agent có thể cancel một build cũ mà không corrupt cache.

---

# 135. Atomic publication

Query result phải được publish atomically:

```text
Incomplete
   ↓
Computed
   ↓
Validated
   ↓
Published
```

---

# 136. Cache corruption

Nếu disk cache invalid:

```text
delete/ignore
recompute
```

không làm compilation semantic khác đi.

---

# 137. Common infrastructure test suite

```text
tests/common/
├── ids/
├── arena/
├── interning/
├── fingerprints/
├── revisions/
├── query/
├── cycles/
├── cancellation/
├── parallel/
├── cache/
├── deterministic/
└── serialization/
```

---

# 138. Determinism test

Chạy cùng compilation:

```text
1 worker
2 workers
4 workers
8 workers
```

semantic fingerprints phải giống nhau.

---

# 139. Cache test

```text
cold build
→ warm build
→ modify unrelated file
→ incremental build
```

phải cho cùng semantic result.

---

# 140. Query invalidation test

Ví dụ:

```text
A → B → C
D độc lập
```

sửa A:

```text
A,B,C invalidated
D reused
```

---

# 141. Query cycle test

Tạo cycle giả:

```text
Q1 → Q2 → Q3 → Q1
```

engine phải:

```text
detect
diagnose
terminate query
```

không deadlock.

---

# 142. Parallel determinism test

Random scheduling simulation:

```text
same input
different completion order
```

→ same semantic result.

---

# 143. Memory stress

Test:

```text
millions of IDs
millions of syntax nodes
large dependency graph
```

để đảm bảo ID overflow/arena growth được xử lý.

---

# 144. Fingerprint test

Thay đổi:

```text
HashMap insertion order
```

không được thay fingerprint.

---

# 145. Cache compatibility test

Thay:

```text
semantic compiler version
```

→ cache invalidation đúng.

---

# 146. Security test

Corrupt cache:

```text
random bytes
truncated data
wrong version
wrong target
wrong fingerprint
```

→ cache rejected.

---

# 147. Implementation priority

Agent nên code theo thứ tự:

```text
1. Typed IDs
2. Arena/IndexVec
3. Symbol interning
4. Fingerprint
5. Revision
6. Input DB
7. Query key
8. Query cache
9. Dependency tracking
10. Cycle detection
11. Cancellation
12. Parallel scheduler
13. Persistent cache
```

---

# 148. Không nên code persistent cache trước query correctness.

---

# 149. Không nên code parallel scheduler trước deterministic single-thread query engine.

---

# 150. Không nên code remote cache trước local cache.

---

# 151. End-state

```text
                    CompilerDB
                       │
             ┌─────────┴─────────┐
             │                   │
         Input Store        Query Engine
                                 │
              ┌──────────────────┼─────────────────┐
              │                  │                 │
           Memoization      Dependencies       Revisions
              │                  │                 │
              └──────────────────┼─────────────────┘
                                 │
                           Semantic Graph
                                 │
              ┌──────────────────┼──────────────────┐
              ▼                  ▼                  ▼
             HIR                MIR              Layout
              │                  │                  │
              └──────────────┬───┴──────────────────┘
                             ▼
                         Verification
                             │
                         Optimization
                             │
                           Codegen
```

---

# 152. Frozen invariants

```text
ACOMMON-20
All major compiler semantic entities use typed identifiers.

ACOMMON-21
Semantic identity is independent of physical memory address.

ACOMMON-22
Compiler semantic objects are immutable after publication where practical.

ACOMMON-23
CompilerDB is the authoritative owner of semantic state.

ACOMMON-24
Semantic queries are deterministic for identical inputs and revisions.

ACOMMON-25
Query dependencies are tracked by the query engine.

ACOMMON-26
Semantic cache validity is dependency-based.

ACOMMON-27
Query caches must not silently reuse stale semantic results.

ACOMMON-28
Query cycles are detected explicitly.

ACOMMON-29
Query cycle handling does not define language-level recursion semantics.

ACOMMON-30
Cancellation does not produce a valid semantic result.

ACOMMON-31
Cancelled or failed queries must not publish valid cache entries.

ACOMMON-32
Parallel query execution must preserve deterministic semantic results.

ACOMMON-33
Observable ordering must not depend on thread completion order.

ACOMMON-34
Compiler input mutation occurs only through the input layer.

ACOMMON-35
Each compiler revision provides a coherent semantic snapshot.

ACOMMON-36
Incremental invalidation must be dependency-driven.

ACOMMON-37
Unrelated source changes must not force unnecessary semantic recomputation when dependency analysis proves independence.

ACOMMON-38
Semantic fingerprints are canonical and deterministic.

ACOMMON-39
Semantic fingerprints are distinct from code-generation fingerprints.

ACOMMON-40
Cache keys include all relevant semantic inputs.

ACOMMON-41
Persistent cache data is treated as untrusted input.

ACOMMON-42
Invalid or incompatible cache data must be ignored or rejected safely.

ACOMMON-43
Compiler diagnostics are structured data.

ACOMMON-44
Semantic errors are represented as data rather than internal compiler exceptions.

ACOMMON-45
Internal invariant violations are distinguishable from user-program errors.

ACOMMON-46
Source provenance remains available through compiler transformations.

ACOMMON-47
Common infrastructure must not depend on Axiom language semantics.

ACOMMON-48
Frontend, verifier and backend layers must use common typed infrastructure rather than duplicating identity systems.

ACOMMON-49
Compiler implementation may use arbitrary internal memory-management techniques without changing Axiom source semantics.

ACOMMON-50
Compiler garbage collection or cache eviction, if used internally, is unrelated to Axiom program memory semantics.

ACOMMON-51
Query implementation must not directly depend on target-specific backend representations.

ACOMMON-52
LLVM-specific state cannot become part of CompilerDB semantic identity.

ACOMMON-53
Compiler configuration is an explicit query input.

ACOMMON-54
Target, feature and profile changes invalidate all dependent results.

ACOMMON-55
Comptime external inputs participate in dependency tracking.

ACOMMON-56
Compiler AI tooling reads structured CompilerDB facts.

ACOMMON-57
AI-generated modifications must re-enter normal query and verification pipelines.

ACOMMON-58
No AI-generated semantic assertion can bypass compiler verification.

ACOMMON-59
Single-threaded and parallel query execution must produce equivalent semantic results.

ACOMMON-60
The query engine is infrastructure; it does not define Axiom language semantics.
```

---

## Kiến trúc đã đạt đến đâu?

Sau **274**, ta đã khóa được phần nền móng:

```text
                 Axiom Specification
                         │
                         ▼
                  CompilerDB
                         │
                   Query Engine
                         │
        ┌────────────────┼────────────────┐
        ▼                ▼                ▼
     Syntax          Semantic          Build
        │                │                │
        ▼                ▼                ▼
       HIR              MIR             Cache
                         │
                    Verification
                         │
                     Verified MIR
                         │
                       OptIR
                         │
                       ABI/LIR
                         │
                     Backends
```

Điểm quan trọng là từ đây **mọi subsystem tiếp theo đều có một “đường ray” chung**. Không còn tình trạng mỗi phần tự có ID, cache, dependency graph hay error model riêng.

### Task tiếp theo: **BOOTSTRAP-275 — AXIOM LEXER IMPLEMENTATION SPECIFICATION**

Sẽ đặc tả ở mức code-ready:

- Unicode/UTF-8 handling
- byte offset và `SourceSpan`
- token representation
- trivia/lossless syntax
- newline token
- identifier rules
- keyword table
- numeric literal scanner
- string/char/byte literal scanner
- escape processing
- nested comments
- longest-match
- malformed-token recovery
- incremental lexing
- token interning
- lexer state machine
- zero-copy source slices
- lexer diagnostics
- lexer fuzzing/conformance
- API cụ thể để agent có thể **viết lexer ngay**, không cần tự thiết kế thêm.