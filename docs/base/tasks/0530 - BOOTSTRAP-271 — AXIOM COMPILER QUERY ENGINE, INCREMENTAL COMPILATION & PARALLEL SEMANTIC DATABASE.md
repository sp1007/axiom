# BOOTSTRAP-271 — AXIOM COMPILER QUERY ENGINE, INCREMENTAL COMPILATION & PARALLEL SEMANTIC DATABASE

**TRẠNG THÁI: FROZEN / COMPLETED**

Task này khóa cách `CompilerDB` vận hành thực tế. Đây là phần biến kiến trúc compiler Axiom từ một tập các subsystem thành **một semantic database có thể incremental, parallel, cacheable và deterministic**.

Nguyên tắc trung tâm:

> **Mọi compiler computation đáng kể đều là một query có dependency rõ ràng.**

Vì vậy compiler không nên hoạt động theo kiểu:

```text
parse toàn bộ
→ typecheck toàn bộ
→ compile toàn bộ
→ codegen toàn bộ
```

mà theo mô hình:

```text
Input
  ↓
Queries
  ↓
Dependency Graph
  ↓
Cached Results
  ↓
Invalidate đúng phần bị ảnh hưởng
  ↓
Recompute cần thiết
```

---

# 1. CompilerDB chính thức trở thành Query Database

Kiến trúc:

```text
                         CompilerDB
                             │
                  ┌──────────┴──────────┐
                  │                     │
             Input Database       Derived Database
                  │                     │
          ┌───────┼───────┐       ┌─────┼─────────┐
          ▼       ▼       ▼       ▼     ▼         ▼
       Source   Manifest  Config  Syntax Type     Trait
                                  │      │         │
                                  └──┬───┴────┬────┘
                                     ▼        ▼
                                    HIR      MIR
                                      \       /
                                       ▼     ▼
                                     Verify
                                       │
                                       ▼
                                    OptIR
                                       │
                              ┌────────┴────────┐
                              ▼                 ▼
                            Layout             ABI
                              │                 │
                              └────────┬────────┘
                                       ▼
                                    Codegen
```

---

# 2. Input và Derived Data phải khác nhau

Input:

```text
SourceFile
Manifest
Lockfile
TargetConfig
CompilerConfig
FeatureConfig
Environment
ComptimeExternalInput
```

Derived:

```text
Tokens
SyntaxTree
Declarations
Types
TraitResults
HIR
MIR
Verification
Optimization
Layout
ABI
MachineCode
```

---

# 3. Input revision

Mỗi input database có revision:

```text
RevisionId
```

Ví dụ:

```text
Revision 100
    source A
    source B
    source C

Revision 101
    source A changed
    source B unchanged
    source C unchanged
```

Compiler không mặc định xóa toàn bộ cache.

---

# 4. Query model

Mỗi query:

```text
Query<Key> → Value
```

Ví dụ:

```text
parse(SourceFileId)
resolve(ModuleId)
type_of(ExpressionId)
mir(FunctionId)
verify(FunctionId)
layout(TypeId, TargetId)
abi(FunctionId, TargetId)
codegen(FunctionId, TargetId, Profile)
```

---

# 5. Query key phải đầy đủ

Ví dụ:

```text
layout(TypeId, TargetId)
```

không được chỉ cache theo `TypeId`.

Vì:

```text
i64
```

có thể có layout khác theo target.

---

# 6. Query dependency graph

Ví dụ:

```text
codegen(foo, x86_64)
    │
    ├── optimize(foo)
    │     └── verify(foo)
    │           └── mir(foo)
    │                 └── typed_hir(foo)
    │
    ├── abi(foo, x86_64)
    │     └── layout(...)
    │
    └── target_spec(x86_64)
```

Compiler có thể biết chính xác codegen phụ thuộc vào gì.

---

# 7. Dependency tracking phải tự động

Query không cần programmer/compiler pass tự khai báo toàn bộ dependency thủ công.

Concept:

```text
with_query_context(query_key):
    result = compute()
```

Khi `compute()` gọi query khác:

```text
A → B
```

database tự ghi dependency.

---

# 8. Ví dụ

```text
type_of(expr42)
```

gọi:

```text
resolve(name)
type_of(arg1)
type_of(arg2)
trait_solve(Add, ...)
```

Database tự tạo:

```text
type_of(expr42)
 ├── resolve(name)
 ├── type_of(arg1)
 ├── type_of(arg2)
 └── trait_solve(...)
```

---

# 9. Dependency graph không nhất thiết phải lưu dưới dạng graph object khổng lồ

Có thể dùng:

```text
QueryKey → DependencyList
Dependency → DependentQueries
```

với compressed/interned representation.

---

# 10. Memoization

Nếu query:

```text
type_of(expr42)
```

đã có kết quả hợp lệ:

```text
cache hit
```

không chạy lại.

---

# 11. Nhưng cache hit phải kiểm tra revision

Không phải:

```text
key exists → valid
```

mà:

```text
key exists
    ↓
dependencies unchanged?
    ↓
yes → reuse
no  → recompute
```

---

# 12. Red-green incremental model

Có thể dùng mô hình:

```text
GREEN
```

= kết quả còn hợp lệ.

```text
RED
```

= có dependency thay đổi.

Nhưng Axiom nên ưu tiên **dependency verification/lazy validation** thay vì eagerly mark toàn bộ transitive dependents.

---

# 13. Tại sao?

Một thay đổi:

```text
foo()
```

có thể ảnh hưởng:

```text
bar()
baz()
```

nhưng nếu `bar` không dùng semantic fact đã thay đổi, không cần compile lại.

---

# 14. Semantic dependency quan trọng hơn textual dependency

Ví dụ:

```text
struct Point {
    x: i32
    y: i32
}
```

đổi implementation của một private function không nhất thiết invalidate tất cả users của `Point`.

---

# 15. Public API fingerprint

Compiler cần:

```text
SemanticFingerprint
```

cho declaration/module/package.

Ví dụ:

```text
struct Point {
    x: i32
    y: i32
}
```

fingerprint phụ thuộc vào semantic public contract.

---

# 16. Private implementation fingerprint

Tách:

```text
PublicSemanticFingerprint
ImplementationFingerprint
```

Để compiler biết:

```text
private implementation changed
```

không đồng nghĩa:

```text
downstream semantic API changed
```

---

# 17. Ví dụ incremental

```text
lib.ax
 ├── pub struct Vec
 ├── pub fn push
 └── private helper
```

Nếu chỉ sửa:

```text
private helper
```

thì:

```text
public semantic fingerprint
```

có thể giữ nguyên.

Downstream không cần typecheck lại.

---

# 18. Nhưng codegen của `lib` phải invalidate

Vì machine implementation thay đổi.

Do đó:

```text
Semantic cache
```

và:

```text
Codegen cache
```

không được đánh đồng.

---

# 19. Ba fingerprint quan trọng

```text
SemanticFingerprint
AbiFingerprint
CodegenFingerprint
```

Quan hệ:

```text
Semantic
   ↓
ABI
   ↓
Codegen
```

nhưng không phải lúc nào thay đổi semantic cũng làm ABI thay đổi.

---

# 20. Ví dụ

Thay đổi:

```text
private loop optimization
```

có thể:

```text
SemanticFingerprint = unchanged
AbiFingerprint      = unchanged
CodegenFingerprint  = changed
```

---

# 21. Thay đổi public struct layout

Nếu layout không ổn định:

```text
Semantic API changed
```

nhưng ABI có thể vẫn opaque.

Nếu:

```text
@repr(C)
```

thì:

```text
AbiFingerprint
```

có thể thay đổi.

---

# 22. Query purity

Mỗi query cần classification:

```text
PureQuery
InputQuery
ExternalEffectQuery
```

Compiler semantic query thông thường phải deterministic.

---

# 23. Semantic query không được tự ý đọc filesystem

Ví dụ:

```text
type_of(...)
```

không được âm thầm:

```text
read random file
```

Nếu cần external input:

```text
ExternalInputQuery(path/capability)
```

phải trở thành dependency.

---

# 24. Comptime

Comptime query:

```text
evaluate_comptime(...)
```

phải record:

```text
source dependency
input dependency
capability
result
```

---

# 25. External comptime input

Ví dụ:

```text
read source file X
```

thì:

```text
X content hash
```

phải nằm trong dependency identity.

---

# 26. Environment

Nếu comptime đọc:

```text
ENV_VAR
```

thì giá trị đó là dependency.

Không được cache:

```text
comptime_result
```

mà bỏ qua environment.

---

# 27. Network

Nếu build/comptime được cấp network:

```text
network input
```

phải được đưa vào build identity hoặc bị hạn chế trong reproducible mode.

---

# 28. Query cycle

Ví dụ:

```text
A → B
B → C
C → A
```

không được deadlock.

Database phải phát hiện:

```text
QueryCycle
```

---

# 29. Không phải cycle nào cũng là compiler error

Một số semantic query có recursive structure hợp lệ.

Ví dụ trait/type normalization có thể có recursion được kiểm soát.

Vì vậy:

```text
cycle detected
```

phải được xử lý bởi query policy.

---

# 30. Query cycle policy

```text
CyclePolicy {
    Reject
    FixedPoint
    RecursivePlaceholder
    DepthLimited
}
```

Trait solver đã có cycle semantics riêng.

Query engine không được tự ý biến mọi cycle thành error.

---

# 31. Recursive query safety

Mọi recursive query phải có:

```text
cycle detector
depth limit
resource limit
diagnostic path
```

---

# 32. Query cancellation

IDE thường yêu cầu:

```text
type information
```

sau đó người dùng gõ tiếp.

Query cũ không còn cần thiết.

Compiler phải hỗ trợ:

```text
CancellationToken
```

---

# 33. Cancellation không phải semantic failure

Phân biệt:

```text
Cancelled
Error
NotFound
Ambiguous
Incomplete
```

---

# 34. Production build

Trong production build:

```text
cancellation
```

thường chỉ xảy ra do external shutdown/resource policy.

Không được biến thành một semantic result hợp lệ.

---

# 35. Parallel query execution

Nếu:

```text
foo()
bar()
baz()
```

không phụ thuộc nhau:

```text
query(foo)
query(bar)
query(baz)
```

có thể chạy song song.

---

# 36. Deterministic parallelism

Kết quả không được phụ thuộc vào:

```text
worker 1 finishes first
worker 2 finishes first
```

---

# 37. Race trong cache

Hai worker cùng yêu cầu:

```text
type_of(expr42)
```

không nên cùng tính toán vô ích nếu có thể tránh.

Dùng trạng thái:

```text
Vacant
Computing
Ready
Poisoned
```

---

# 38. Computing entry

```text
QueryEntry {
    state
    owner
    dependencies
    result
}
```

---

# 39. Recursive same-query request

Nếu query đang:

```text
Computing
```

và cùng execution context yêu cầu lại chính nó:

```text
A → A
```

phải chuyển sang cycle handling, không chờ chính mình.

---

# 40. Parallel wait

Nếu worker A đang tính:

```text
Q
```

worker B cần `Q`:

```text
B waits
```

hoặc scheduler có thể steal/assist computation tùy implementation.

Semantic result không thay đổi.

---

# 41. No global compiler lock

Không nên:

```text
CompilerDB
   ↓
global mutex
```

cho mọi query.

Điều này sẽ phá khả năng scale.

---

# 42. Database concurrency

Các immutable/interned records có thể đọc đồng thời.

Mutation chỉ xảy ra ở:

```text
revision/input update
cache publication
```

và phải có synchronization phù hợp.

---

# 43. Query result immutability

Sau khi publish:

```text
QueryResult
```

không được mutate.

Muốn thay đổi:

```text
new revision
→ new result
```

---

# 44. Revision model

```text
Revision 100
   ↓
Revision 101
```

Không nhất thiết copy toàn bộ database.

Dùng persistent/interned structures.

---

# 45. Snapshot

Mỗi compiler operation nhìn thấy một:

```text
DatabaseSnapshot
```

Ví dụ IDE request:

```text
snapshot = revision 1042
```

mọi query trong request nhìn cùng revision.

---

# 46. Điều này rất quan trọng

Nếu user đang sửa file:

```text
A
```

trong lúc query:

```text
B
```

đang chạy, query không được nhìn:

```text
A revision 104
B revision 105
```

một cách ngẫu nhiên.

---

# 47. Atomic revision publication

Input changes được publish:

```text
old revision
     ↓
apply changes
     ↓
new revision
     ↓
publish snapshot
```

---

# 48. Query consistency

Một query tree phải sử dụng cùng semantic snapshot trừ khi explicitly requested otherwise.

---

# 49. Incremental parsing

```text
Source change
    ↓
incremental lexer
    ↓
green tree reuse
    ↓
AST affected region
```

Phần không đổi được reuse.

---

# 50. Incremental resolution

Không phải mọi symbol đều cần resolve lại.

Compiler dùng:

```text
DeclarationGraph
ModuleGraph
ImportGraph
```

để xác định vùng ảnh hưởng.

---

# 51. Incremental type checking

Type query ở expression-level:

```text
type_of(ExpressionId)
```

cho phép giữ lại kết quả của expression không bị ảnh hưởng.

---

# 52. Nhưng phải cẩn thận với semantic IDs

Nếu sửa source phía trước:

```text
expression IDs
```

không nên làm toàn bộ file mất identity.

Lossless syntax tree + stable node identity giúp giảm invalidation.

---

# 53. Stable syntax identity

Green tree node có thể có:

```text
NodeId
```

dựa trên structural reuse.

---

# 54. Declaration identity

Declaration identity nên ổn định khi declaration không thực sự đổi semantic identity.

Ví dụ:

```text
pub fn foo(...)
```

đổi whitespace:

```text
foo
```

vẫn là cùng declaration semantic identity.

---

# 55. Nhưng rename

```text
foo → bar
```

có thể tạo semantic identity mới hoặc migration mapping tùy tooling.

Compiler không được dựa vào text span đơn thuần để nhận diện declaration.

---

# 56. Incremental MIR

Nếu function không semantic-change:

```text
MIR cache hit
```

Nếu chỉ function khác thay đổi:

```text
MIR(foo)
```

có thể giữ.

---

# 57. Verification cache

```text
verify(FunctionId)
```

cache key cần bao gồm:

```text
MIR fingerprint
relevant type facts
trait facts
target-independent semantic config
```

---

# 58. Optimization cache

Optimization phụ thuộc:

```text
VerifiedMIR fingerprint
OptimizationProfile
CompilerCodegenVersion
Target-independent optimizer configuration
```

---

# 59. Target-specific cache

Codegen:

```text
CodegenKey {
    verified_mir
    target
    cpu_features
    abi
    profile
    codegen_version
}
```

---

# 60. Cross-target cache isolation

Không được reuse machine code:

```text
x86-64
```

cho:

```text
ARM64
```

chỉ vì source giống nhau.

---

# 61. Nhưng có thể reuse semantic stages

```text
Source
 ↓
HIR
 ↓
MIR
 ↓
Verified MIR
```

dùng chung cho:

```text
x86
ARM
RV64
WASM
```

sau đó diverge:

```text
ABI / LIR / MachineIR
```

---

# 62. Đây chính là lý do kiến trúc target-independent trước đây rất quan trọng.

---

# 63. Package-level incremental compilation

Package graph:

```text
App
 ├── CoreLib
 ├── Net
 └── UI
```

Compiler không rebuild:

```text
UI
```

chỉ vì:

```text
CoreLib private implementation
```

thay đổi, nếu semantic/ABI contract không ảnh hưởng.

---

# 64. Dependency edge classification

Không chỉ:

```text
A depends on B
```

mà:

```text
SemanticDependency
AbiDependency
CodegenDependency
BuildDependency
RuntimeDependency
ComptimeDependency
```

---

# 65. Ví dụ

```text
App
 ──Semantic──→ CoreLib
 ──ABI───────→ CoreLib
 ──Runtime───→ Net
```

---

# 66. ABI-stable package

Nếu package cung cấp:

```text
@abi(stable)
```

thì downstream binary có thể không cần rebuild khi implementation thay đổi nếu ABI fingerprint giữ nguyên.

---

# 67. Generic code

Generic implementation phức tạp hơn.

Ví dụ:

```text
Vec<T>
```

thay đổi implementation có thể ảnh hưởng instantiated code:

```text
Vec<i32>
Vec<f64>
Vec<MyStruct>
```

Compiler cần lưu:

```text
GenericDefinitionFingerprint
```

và:

```text
GenericInstanceFingerprint
```

---

# 68. Specialization dependency

Nếu:

```text
foo<T>
```

specialize thành:

```text
foo<i32>
```

thì codegen dependency phải record:

```text
GenericDefinition
+
TypeArguments
+
TraitFacts
+
Target
```

---

# 69. Trait solver cache

Key:

```text
TraitGoalKey {
    trait
    self_type
    arguments
    environment
}
```

Result:

```text
Proven
NotProven
Ambiguous
Error
```

---

# 70. Trait result phải fingerprint được

Nếu trait environment không đổi:

```text
cache hit
```

---

# 71. Layout cache

```text
LayoutKey {
    TypeId
    TargetId
    ReprContract
}
```

---

# 72. ABI cache

```text
AbiKey {
    FunctionId
    TargetId
    AbiVersion
    PublicAbiContract
}
```

---

# 73. Codegen cache

Machine object/function section có thể cache độc lập:

```text
foo.o
bar.o
baz.o
```

---

# 74. Function-level codegen

Axiom nên ưu tiên function-level codegen cache thay vì chỉ module-level.

Điều này giúp:

```text
large package
1 function changed
```

không cần codegen lại toàn bộ package.

---

# 75. LTO exception

Nếu bật:

```text
LTO
```

thì cross-function optimization có thể làm dependency rộng hơn.

Compiler phải biết:

```text
LTO dependency graph
```

---

# 76. Incremental LTO

Không nhất thiết bỏ incremental hoàn toàn.

Có thể dùng:

```text
summary cache
```

cho mỗi function/module:

```text
InlineSummary
AliasSummary
EffectSummary
SizeSummary
HotnessSummary
```

---

# 77. PGO

PGO data là input:

```text
ProfileDataId
```

thay đổi profile có thể invalidate optimization/codegen nhưng không invalidate semantic analysis.

---

# 78. Build cache hierarchy

```text
                    Build Cache
                        │
       ┌────────────────┼────────────────┐
       ▼                ▼                ▼
   Semantic          Optimization      Codegen
   Cache             Cache             Cache
       │                │                │
    HIR/MIR          OptIR             Object
    Trait            Alias             MachineCode
    Type             Range             Debug
```

---

# 79. Cache không được là semantic authority

Nếu cache corrupt:

```text
cache result
```

không được mặc định tin tuyệt đối.

Có thể:

```text
validate fingerprint
```

và trong compiler correctness mode:

```text
recompute
```

---

# 80. Cache poisoning

Package/binary cache phải xác thực:

```text
ArtifactFingerprint
CompilerSemanticVersion
Target
FeatureSet
DependencyIdentity
```

---

# 81. Distributed cache

Có thể hỗ trợ sau:

```text
local cache
        ↓
shared cache
        ↓
remote cache
```

nhưng semantic identity phải giống nhau.

---

# 82. Remote cache không được thay đổi semantics

Hai máy:

```text
Machine A
Machine B
```

dùng cùng semantic inputs phải có equivalent result.

---

# 83. Hash algorithm

Fingerprint không nên phụ thuộc vào:

```text
pointer address
hash-map random seed
thread ordering
```

Dùng canonical serialization trước khi hash.

---

# 84. Canonical fingerprinting

```text
SemanticObject
   ↓
canonical encoding
   ↓
hash
   ↓
Fingerprint
```

---

# 85. Không hash raw memory representation của compiler objects.

Vì compiler struct layout có thể thay đổi giữa phiên bản.

---

# 86. Compiler version

Tách:

```text
SemanticCompilerVersion
CodegenVersion
ToolingVersion
```

---

# 87. Semantic version thay đổi khi

Ví dụ:

```text
language semantics changed
type system changed
ownership rules changed
ABI semantic contract changed
```

---

# 88. Codegen version thay đổi khi

Ví dụ:

```text
instruction selector changed
register allocator changed
scheduler changed
```

Semantic cache có thể vẫn dùng được.

---

# 89. Tooling version

Thay đổi:

```text
LSP
formatter
diagnostic UI
```

không nên invalidate codegen.

---

# 90. Query error poisoning

Nếu query computation thất bại nội bộ:

```text
panic / ICE
```

không được lưu như semantic success.

---

# 91. Distinguish:

```text
SemanticError
UserError
QueryCancelled
QueryCycle
ResourceLimit
CompilerBug
```

---

# 92. Compiler Bug

Ví dụ:

```text
internal invariant failed
```

phải tạo:

```text
ICE
```

không biến thành:

```text
"program invalid"
```

---

# 93. Resource limits

Compiler cần giới hạn:

```text
recursion depth
trait solver depth
comptime steps
memory
query count
generated code
```

---

# 94. Resource exhaustion

Phải có diagnostic rõ:

```text
CompilerResourceLimit
```

không giả vờ rằng program semantic invalid nếu chưa chứng minh được.

---

# 95. IDE Partial Mode

Query engine phải hỗ trợ:

```text
Complete Semantic Mode
Partial Semantic Mode
```

đã khóa ở task 191.

---

# 96. Partial query result

Ví dụ:

```text
type_of(expr)
```

có thể trả:

```text
Known(T)
Unknown
Incomplete
Error(E)
Ambiguous
```

---

# 97. Nhưng production verifier chỉ nhận:

```text
Known + Complete
```

---

# 98. Query certainty

Mỗi result tooling quan trọng có thể mang:

```text
Certainty {
    Complete
    Partial
    Stale
    Error
}
```

---

# 99. AI compiler interface

`AXCP` có thể gọi trực tiếp query engine:

```text
query type
query ownership
query trait
query effects
query ABI
query allocation
query optimization
```

---

# 100. AI không được mutate semantic database trực tiếp

AI request:

```text
"assume this is Send"
```

không thể ghi:

```text
Send = true
```

---

# 101. AI chỉ có thể:

```text
request change
→ compiler validates
→ new revision
→ query
```

---

# 102. Explain query

Query engine phải hỗ trợ:

```text
explain(move)
explain(type)
explain(trait)
explain(alias)
explain(allocation)
explain(await)
```

---

# 103. Explain không phải một compiler pass riêng biệt

Nó query:

```text
facts
+
proof graph
+
source provenance
```

---

# 104. Example

```text
why cannot mutate x?
```

Compiler có thể trả:

```text
CapabilityConflict
 ├── existing READ capability
 │     └── source line 10
 └── requested WRITE capability
       └── source line 15
```

---

# 105. Incremental diagnostic

Nếu user sửa:

```text
line 15
```

compiler không nên xóa toàn bộ diagnostic database.

Chỉ invalidate diagnostic queries phụ thuộc vùng semantic bị thay đổi.

---

# 106. Query priorities

IDE có thể ưu tiên:

```text
1. syntax
2. name resolution
3. type
4. completion
5. diagnostics
6. ownership
7. full MIR
8. optimization
9. codegen
```

---

# 107. Background compilation

IDE foreground:

```text
completion
hover
diagnostic
```

background:

```text
full verification
optimization
codegen
indexing
```

---

# 108. Query scheduler

Có thể phân loại:

```text
Interactive
Background
BuildCritical
Optional
```

---

# 109. Interactive query không nên chờ một optimization query khổng lồ nếu có thể trả semantic information trước.

---

# 110. Cancellation ưu tiên

Nếu user tiếp tục gõ:

```text
revision 101
```

query của:

```text
revision 100
```

có thể bị cancel nếu không còn useful.

---

# 111. Nhưng cache kết quả hoàn thành của revision cũ vẫn có thể giữ lại.

---

# 112. Revision-independent interned objects

Ví dụ:

```text
i32
u64
```

không cần tạo lại mỗi revision.

---

# 113. Interning

```text
TypeInterner
StringInterner
SymbolInterner
TraitKeyInterner
```

giảm memory và tăng tốc equality.

---

# 114. Structural sharing

Hai revision:

```text
R100
R101
```

có thể cùng share:

```text
unchanged green trees
unchanged types
unchanged declarations
unchanged MIR
```

---

# 115. Garbage collection của compiler data

Đây là **compiler implementation memory management**, không phải Axiom runtime GC.

Compiler có thể dùng:

```text
arena
reference counting
generational cache
mark/sweep
```

nếu hữu ích.

Không ảnh hưởng language semantics.

---

# 116. Eviction

Cache có thể:

```text
evict
```

một result.

Sau đó query chỉ:

```text
recompute
```

Semantics không thay đổi.

---

# 117. Cache tiers

```text
L1 — request-local
L2 — process CompilerDB
L3 — project persistent cache
L4 — shared/remote cache
```

---

# 118. Persistent semantic cache

Có thể lưu:

```text
.axcache
```

nhưng cache artifact không phải source of truth.

---

# 119. Source + lockfile + compiler version vẫn là authority.

---

# 120. Query invalidation algorithm

Mô hình chuẩn:

```text
Input changed
     ↓
new revision
     ↓
query requested
     ↓
lookup previous result
     ↓
validate dependencies
     ├── all unchanged → reuse
     └── changed
           ↓
        recompute
```

---

# 121. Lazy invalidation

Không cần đi ngược toàn bộ graph ngay khi source thay đổi.

Điều này tránh:

```text
O(total dependency graph)
```

cho mỗi keystroke.

---

# 122. Dependency validation có thể short-circuit.

Nếu dependency đầu tiên đã thay đổi semantic result:

```text
recompute
```

không cần kiểm tra phần còn lại.

---

# 123. Fingerprint-based validation

Thay vì so sánh toàn bộ object:

```text
dependency fingerprint
```

có thể giúp validation nhanh.

---

# 124. Nhưng fingerprint collision không được trở thành semantic correctness assumption nếu dùng hash không đảm bảo tuyệt đối.

Compiler có thể:

```text
hash → fast path
structural verification → correctness mode
```

---

# 125. Query cache serialization

Persistent cache cần canonical format:

```text
version
query key
dependency fingerprints
result
result fingerprint
```

---

# 126. Không serialize raw pointer/reference của compiler process.

---

# 127. Parallel deterministic ordering

Diagnostic output cần stable order.

Ví dụ dù worker hoàn thành:

```text
line 50
line 10
line 30
```

output vẫn canonical:

```text
line 10
line 30
line 50
```

---

# 128. Hash-map iteration

Không được dùng iteration order để quyết định:

```text
symbol resolution
trait selection
diagnostic winner
ABI
codegen semantic behavior
```

---

# 129. Trait candidate ordering

Task 240 đã khóa:

```text
deterministic trait selection
```

Query engine phải bảo đảm execution scheduling không phá điều đó.

---

# 130. Parallel type inference

Có thể parallelize independent constraints.

Nhưng final unification/constraint result phải canonical.

---

# 131. Query engine và ownership

CompilerDB internal references không chịu Axiom source-level ownership rules.

Nhưng semantic records phải immutable/persistent để tránh mutation race.

---

# 132. CompilerDB API

Khung khái niệm:

```text
trait QueryDatabase {
    fn revision() -> RevisionId

    fn input<K>(key: K) -> InputValue

    fn query<Q>(key: Q::Key) -> Q::Value

    fn fingerprint<Q>(key: Q::Key) -> Fingerprint

    fn snapshot() -> Snapshot

    fn invalidate(...)
}
```

---

# 133. Query declaration

```text
trait Query {
    type Key
    type Value

    fn execute(db: &QueryDb, key: Key) -> Value
}
```

---

# 134. Input query

```text
SourceText(SourceFileId)
Manifest(PackageId)
TargetSpec(TargetId)
BuildConfig(BuildConfigId)
```

---

# 135. Derived queries

```text
tokens(file)
syntax(file)
declarations(module)
resolve(name)
type_of(expr)
hir(function)
mir(function)
verify(function)
optimize(function)
layout(type,target)
abi(function,target)
codegen(function,target)
```

---

# 136. Query layers

```text
                    Queries
                       │
        ┌──────────────┼──────────────┐
        ▼              ▼              ▼
     Frontend       Semantic       Backend
        │              │              │
     Syntax          MIR           Layout
     Resolve         Verify        ABI
     Types           Effects       LIR
     Traits          Ownership     MachineIR
     HIR             Capability    Object
```

---

# 137. Query boundary

Mỗi query nên có:

```text
Input
Dependencies
Result
Fingerprint
Diagnostics
Provenance
```

---

# 138. Compiler query tracing

Compiler debug mode cần có:

```text
query trace
```

ví dụ:

```text
codegen(foo)
 ├─ optimize(foo)
 │   ├─ verify(foo)
 │   │   ├─ mir(foo)
 │   │   └─ trait(...)
 │   └─ alias(foo)
 ├─ abi(foo)
 └─ target(x86_64)
```

---

# 139. Đây cũng là nền tảng cho compiler performance tooling.

Có thể biết:

```text
query count
cache hit rate
query time
dependency fanout
memory
parallelism
```

---

# 140. Hot query detection

Compiler có thể phát hiện:

```text
trait_solve(...)
```

đang chiếm 40% compile time.

Không cần thay semantic architecture.

---

# 141. Query batching

Một số query có thể batch:

```text
type_of(expr1)
type_of(expr2)
...
```

thay vì overhead từng call.

---

# 142. Speculative query

IDE có thể yêu cầu:

```text
what if this expression changed?
```

nhưng speculative result không được publish thành semantic truth.

---

# 143. Snapshot isolation

Một speculative compilation:

```text
Snapshot A
```

có thể tồn tại song song với:

```text
Current Snapshot B
```

---

# 144. Build graph integration

Package manager task 187:

```text
PackageGraph
```

được đưa vào CompilerDB như input.

Compiler query engine không tự resolve package source ngoài package graph.

---

# 145. Build system

```text
ax build
   ↓
resolve dependencies
   ↓
create BuildSnapshot
   ↓
CompilerDB queries
   ↓
artifacts
```

---

# 146. Cross-compilation

Một source snapshot có thể query nhiều target:

```text
layout(T,x86)
layout(T,arm)
layout(T,rv64)
layout(T,wasm)
```

semantic stages trước target divergence được share.

---

# 147. Multi-target parallelism

Có thể:

```text
x86 codegen ─┐
ARM codegen ─┼→ parallel
RV64 codegen─┤
WASM codegen ┘
```

---

# 148. Không được để target query mutate global TypeDB semantics.

---

# 149. GPU target

Tương tự:

```text
CPU MIR
   ↓
GPU legality query
   ↓
GPU MIR
```

GPU target-specific query độc lập.

---

# 150. Comptime query

Comptime có thể là một query graph con:

```text
comptime_eval
 ├── source
 ├── type
 ├── capability
 ├── external inputs
 └── generated declarations
```

---

# 151. Generated code

Generated declarations tạo revision/query inputs mới trong **virtual generated source space**, nhưng không được mutate user source.

---

# 152. Query provenance

Mọi generated object nên biết:

```text
GeneratedFrom {
    source query
    source span
    generator
}
```

---

# 153. Error recovery

Partial query có thể produce:

```text
RecoveryNode
```

nhưng production query:

```text
verify()
```

phải yêu cầu Complete Semantic Mode.

---

# 154. No silent fallback

Nếu:

```text
type_of(expr) = Unknown
```

không được codegen đoán thành:

```text
i32
```

---

# 155. AI agent integration

Một AI agent có thể yêu cầu:

```text
ax query --function foo
ax explain --why-move x
ax context --scope foo
```

Query engine là backend thực sự của các lệnh này.

---

# 156. Compiler CLI

Nên có:

```text
ax inspect
ax query
ax explain
ax dependencies
ax invalidate
ax cache
ax profile-compiler
```

---

# 157. `ax dependencies`

Ví dụ:

```text
ax dependencies foo
```

có thể hiển thị:

```text
foo
 ├── type Vec<i32>
 ├── trait Add
 ├── function bar
 ├── layout Vec<i32>
 └── ABI target x86_64
```

---

# 158. `ax cache`

Có thể:

```text
ax cache stats
ax cache clear
ax cache explain foo
```

---

# 159. `ax explain compile`

Ví dụ:

```text
ax explain compile foo
```

trả:

```text
cache hit:
  MIR        yes
  Verify     yes
  OptIR      no
  ABI        yes
  Codegen    no
```

---

# 160. Đây là lợi thế rất lớn cho AI.

Thay vì AI đoán:

> “Có lẽ compiler đang rebuild vì...”

AI có thể hỏi compiler:

```text
why invalidated?
```

---

# 161. Invalidation explanation

```text
Codegen(foo)
  invalidated because:
    GenericInstance(Vec<i32>)
      changed
```

hoặc:

```text
Layout(Point)
  unchanged
```

---

# 162. Compiler architecture sau task 271

```text
                         CompilerDB
                             │
                    ┌────────┴────────┐
                    │                 │
                 Inputs             Queries
                    │                 │
                    │          ┌──────┴──────┐
                    │          │             │
                    ▼          ▼             ▼
                 Revision    Semantic      Backend
                              Queries       Queries
                                │             │
                                ▼             ▼
                              MIR/Verify    ABI/LIR
                                │             │
                                └──────┬──────┘
                                       ▼
                                     Cache
                                       │
                     ┌─────────────────┼────────────────┐
                     ▼                 ▼                ▼
                 In-memory          Project          Remote
                   cache             cache           cache
```

---

# 163. Các invariant mới

```text
AQUERY-20
Compiler computations are represented as explicit queries.

AQUERY-21
Query keys must uniquely identify their semantic inputs.

AQUERY-22
Query dependencies are tracked explicitly.

AQUERY-23
Derived query results are immutable after publication.

AQUERY-24
Input state is revisioned.

AQUERY-25
Queries operate against a coherent database snapshot.

AQUERY-26
Query results may be reused only when all relevant dependencies remain valid.

AQUERY-27
Semantic and code-generation caches are distinct.

AQUERY-28
Semantic fingerprints exclude nondeterministic implementation state.

AQUERY-29
ABI fingerprints are distinct from semantic fingerprints.

AQUERY-30
Codegen fingerprints are distinct from ABI fingerprints.

AQUERY-31
Private implementation changes must not invalidate downstream semantic analysis when the public semantic contract is unchanged.

AQUERY-32
ABI-stable implementation changes may avoid downstream recompilation when the ABI contract remains unchanged.

AQUERY-33
Generic instances have independent cache identity from generic definitions.

AQUERY-34
Target-specific queries include TargetId and relevant target features.

AQUERY-35
Target-independent semantic results may be shared across targets.

AQUERY-36
Machine code may never be reused across incompatible targets.

AQUERY-37
Comptime external inputs are explicit query dependencies.

AQUERY-38
Environment-dependent computation is represented in build/query identity.

AQUERY-39
External effects cannot be hidden inside ordinary pure semantic queries.

AQUERY-40
Query cycles must be detected.

AQUERY-41
Recursive semantic systems may define explicit cycle policies.

AQUERY-42
Query cancellation is distinct from semantic failure.

AQUERY-43
Compiler bugs are distinct from user program errors.

AQUERY-44
Resource exhaustion is distinct from semantic invalidity.

AQUERY-45
Parallel query execution must preserve deterministic semantic results.

AQUERY-46
Query scheduling order must not affect trait resolution.

AQUERY-47
Query scheduling order must not affect declaration resolution.

AQUERY-48
Query scheduling order must not affect ABI classification.

AQUERY-49
Query scheduling order must not affect observable program semantics.

AQUERY-50
Duplicate concurrent requests for the same query should be safely coalesced where practical.

AQUERY-51
A query must never wait indefinitely on itself.

AQUERY-52
Query cache entries must never encode process-local raw pointers as persistent identity.

AQUERY-53
Persistent cache entries require complete identity validation.

AQUERY-54
Cache eviction must never change program semantics.

AQUERY-55
Compiler database revisions may use structural sharing.

AQUERY-56
Unchanged semantic objects should be reusable across revisions.

AQUERY-57
Incremental parsing must preserve unaffected syntax structures where possible.

AQUERY-58
Incremental semantic analysis must operate on semantic dependencies rather than textual proximity alone.

AQUERY-59
Diagnostic results may be incremental.

AQUERY-60
Partial semantic results must never enter the production verification/codegen boundary.

AQUERY-61
Unknown information must never be treated as proof.

AQUERY-62
Generated semantic objects retain source provenance.

AQUERY-63
Generated code cannot bypass ordinary semantic verification.

AQUERY-64
AI tooling may query compiler facts but cannot override semantic authority.

AQUERY-65
Compiler explanations must be derived from semantic facts and proof information.

AQUERY-66
Query results should expose enough dependency information to explain invalidation.

AQUERY-67
Compiler performance instrumentation must not alter semantic behavior.

AQUERY-68
Hashing and canonical serialization used for cache identity must be deterministic.

AQUERY-69
Compiler semantic version changes invalidate incompatible semantic cache entries.

AQUERY-70
Codegen implementation changes need not invalidate semantic caches when semantics are unchanged.

AQUERY-71
Tooling-only changes must not invalidate semantic or codegen caches unnecessarily.

AQUERY-72
Remote cache results must obey the same identity validation as local cache results.

AQUERY-73
CompilerDB is the authoritative semantic database for compiler and tooling queries.

AQUERY-74
No frontend, optimizer, backend, or AI agent may create an independent competing semantic authority.

AQUERY-75
Incremental compilation must preserve the same semantic result as clean compilation.

AQUERY-76
Cache hits and cache misses must be semantically indistinguishable.

AQUERY-77
Parallel and serial compilation must be semantically equivalent.

AQUERY-78
Different cache eviction policies must be semantically equivalent.

AQUERY-79
Different query scheduling policies must be semantically equivalent.

AQUERY-80
Compiler implementation memory management is independent from Axiom program memory semantics.
```

---

# 164. Kiến trúc compiler Axiom lúc này

Sau 271:

```text
                       AXIOM SOURCE
                            │
                            ▼
                    ┌──────────────┐
                    │  CompilerDB  │
                    │   Revision   │
                    └──────┬───────┘
                           │
                  ┌────────┴────────┐
                  │  Query Engine   │
                  └────────┬────────┘
                           │
             ┌─────────────┼─────────────┐
             ▼             ▼             ▼
          Frontend      Semantic       Backend
             │             │             │
          Syntax          MIR          Layout
          Resolve        Verify        ABI
          Type           Facts         LIR
          Trait          Effects       MachineIR
             │             │             │
             └─────────────┼─────────────┘
                           ▼
                     Incremental Cache
                           │
              ┌────────────┼────────────┐
              ▼            ▼            ▼
           Semantic      Opt/ABI      Codegen
             Cache         Cache        Cache
```

Điểm quan trọng nhất của task này là:

> **Axiom không chỉ có compiler pipeline; Axiom có một semantic database mà pipeline được xây dựng trên đó.**

Điều này đặc biệt phù hợp với mục tiêu trước đây của bạn về **compiler AI-native**: AI agent không cần “đọc code rồi đoán compiler nghĩ gì”, mà có thể hỏi trực tiếp semantic database.

---

## Task kế tiếp — **BOOTSTRAP-272: AXIOM COMPILER BOOTSTRAP IMPLEMENTATION — Rust/Host Compiler → Axiom Self-Hosting**

Task 272 sẽ chuyển từ **“compiler architecture đã hoàn chỉnh”** sang **“bắt đầu viết compiler thật”**: chọn bootstrap implementation language, repository layout, crate/module boundaries, compiler executable (`axc`), `CompilerDB` implementation, lexer/parser đầu tiên, reference interpreter, MIR interpreter, test harness, sau đó từng bước **compiler tự biên dịch chính Axiom**.

Đây sẽ là task rất quan trọng vì từ đây specification bắt đầu được chuyển thành **implementation plan có thể giao trực tiếp cho Antigravity/Gemini agent**.