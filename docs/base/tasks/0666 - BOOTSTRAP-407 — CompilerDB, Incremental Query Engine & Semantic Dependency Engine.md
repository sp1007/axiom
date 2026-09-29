# BOOTSTRAP-407 — CompilerDB, Incremental Query Engine & Semantic Dependency Engine

Đây là bước chuyển quan trọng: từ việc đặc tả **Axiom ecosystem** sang đặc tả **bộ não bên trong compiler**.

Mục tiêu của 407 là định nghĩa một hệ thống mà compiler, IDE, AI, build system, diagnostics, incremental compilation và verification đều dùng chung.

Nguyên tắc trung tâm:

> **CompilerDB là nguồn sự thật duy nhất của mọi semantic fact trong Axiom.**

Không có:

```text
LSP parser riêng
AI parser riêng
Build system type checker riêng
IDE semantic model riêng
```

Tất cả truy vấn cùng một CompilerDB.

---

# 1. CompilerDB là gì?

CompilerDB không đơn thuần là database lưu AST.

Nó là:

```text
Source
   ↓
Syntax
   ↓
AST
   ↓
Resolution
   ↓
HIR
   ↓
Typed HIR
   ↓
MIR
   ↓
Verification
   ↓
Optimization
   ↓
LIR
   ↓
Artifact
```

được biểu diễn dưới dạng **incremental semantic query graph**.

Ví dụ:

```text
SourceFile("main.ax")
       ↓
SyntaxTree(main)
       ↓
Module(main)
       ↓
Function(foo)
       ↓
TypedFunction(foo)
       ↓
MIR(foo)
       ↓
VerifiedMIR(foo)
       ↓
Codegen(foo)
```

Mỗi node là một semantic query.

---

# 2. Tại sao không dùng pipeline tuyến tính đơn thuần?

Compiler truyền thống dễ hình dung:

```text
parse()
→ typecheck()
→ codegen()
```

Nhưng IDE/AI cần:

```text
"What is the type of expression X?"
"What functions implement Trait Y?"
"Which functions depend on struct Z?"
"Why did this move fail?"
"Which code will rebuild if I change field A?"
```

Không thể mỗi lần đều compile toàn project.

Vì vậy Axiom sử dụng:

> **Demand-driven incremental compilation.**

---

# 3. Query Model

Mọi semantic operation là:

```text
Query<Key> → Value
```

Ví dụ:

```text
parse(FileId)
resolve(SymbolId)
type_of(ExpressionId)
mir(FunctionId)
verify(FunctionId)
codegen(FunctionId, Target)
```

Một query có:

```text
QueryKey
Inputs
Dependencies
Result
Fingerprint
Revision
Proof
```

---

# 4. Query Categories

Chia query thành:

### Syntax

```text
SourceText
Tokens
SyntaxTree
AST
```

### Semantic

```text
ModuleResolution
NameResolution
TypeOf
TraitResolution
GenericInstantiation
EffectInference
CapabilityInference
```

### Ownership

```text
OwnershipState
MoveAnalysis
ViewAnalysis
DropAnalysis
EscapeAnalysis
```

### Execution

```text
MIR
CoroutineLowering
KernelLegality
```

### Verification

```text
TypeProof
OwnershipProof
RaceProof
CapabilityProof
ABIProof
```

### Optimization

```text
ConstEval
Inlining
EscapeAnalysis
AllocationElimination
Vectorization
```

### Codegen

```text
LIR
MachineIR
Object
Executable
```

---

# 5. Query Purity

Semantic query mặc định phải có tính chất:

```text
same inputs + same compiler semantics
        ↓
same result
```

Ví dụ:

```text
type_of(expr#123)
```

không được phụ thuộc vào:

```text
current wall clock
randomness
filesystem
network
```

trừ khi đó là query có capability/external dependency được khai báo rõ.

---

# 6. Revision Model

CompilerDB có revision:

```text
Revision 100
Revision 101
Revision 102
```

Ví dụ user sửa:

```text
x + y
```

thành:

```text
x * y
```

Compiler không coi toàn bộ source tree là mới.

Nó tạo:

```text
Revision 101
```

và xác định semantic impact.

---

# 7. Stable IDs

CompilerDB không dùng source position làm identity duy nhất.

Các entity có stable identity:

```text
FileId
ModuleId
PackageId
SymbolId
TypeId
FunctionId
StructId
TraitId
FieldId
ExpressionId
PatternId
BasicBlockId
MIRLocalId
```

Ví dụ:

```text
FunctionId(0x91A...)
```

có thể tồn tại xuyên revision nếu compiler xác định đó vẫn là cùng semantic declaration.

---

# 8. Syntax Identity vs Semantic Identity

Đây là distinction quan trọng.

```text
SyntaxNodeId
```

xác định node syntax.

```text
SymbolId
```

xác định declaration semantic.

Một declaration có thể thay đổi source location nhưng vẫn giữ:

```text
SymbolId
```

nếu compiler xác định identity không đổi.

---

# 9. Fingerprint

Mỗi query có semantic fingerprint.

Ví dụ:

```text
Fingerprint =
    hash(
        query kind,
        normalized inputs,
        dependency fingerprints,
        compiler semantic version,
        target/config
    )
```

Không sử dụng timestamp làm semantic identity.

---

# 10. Dependency Tracking

Nếu:

```text
type_of(foo)
```

phụ thuộc:

```text
resolve(TypeA)
resolve(TraitB)
```

CompilerDB lưu:

```text
type_of(foo)
   ├── resolve(TypeA)
   └── resolve(TraitB)
```

Khi `TraitB` thay đổi:

```text
invalidate
```

chỉ lan đến các query thực sự phụ thuộc.

---

# 11. Fine-Grained Invalidation

Ví dụ:

```text
struct User {
    id: u64
    name: String
}
```

đổi:

```text
name: String
```

thành:

```text
name: Text
```

Compiler phải biết:

```text
User layout changed
User field type changed
functions using name affected
serialization derived code affected
ABI potentially affected
```

nhưng:

```text
unrelated_math()
```

không cần rebuild.

---

# 12. Semantic Fingerprint vs Text Fingerprint

Đây là một điểm cực kỳ quan trọng cho Axiom.

Thay:

```text
fn foo() {
    // comment
    return x + y;
}
```

bằng:

```text
fn foo() {
    // another comment
    return x + y;
}
```

có thể thay source hash nhưng:

```text
SemanticFingerprint(foo)
```

không đổi.

Do đó downstream không rebuild.

---

# 13. Query Cache

Cache có hai tầng:

```text
Memory Cache
Disk Cache
```

Memory:

```text
fast
revision-local
```

Disk:

```text
persistent
content-addressed
cross-process
```

Remote cache đã được định nghĩa ở 406.

---

# 14. Cache Correctness

Compiler không được:

```text
cache hit → trust blindly
```

Mà phải kiểm tra:

```text
QueryKey
Dependency fingerprints
Compiler semantic version
Target
Features
External inputs
```

Nếu mismatch:

```text
cache miss
```

---

# 15. Cycle Detection

Semantic queries có thể tạo cycle:

```text
Trait A
 → Trait B
 → Trait A
```

hoặc:

```text
Type A
 → Type B
 → Type A
```

CompilerDB phải phát hiện cycle.

Không được:

```text
recursive query
→ stack overflow
```

mà phải tạo:

```text
CycleDiagnostic
```

nếu cycle không hợp lệ.

---

# 16. Hợp lệ hóa Recursion

Không phải cycle nào cũng lỗi.

Ví dụ:

```text
fn factorial(n: u64) -> u64 {
    if n == 0 {
        1
    } else {
        n * factorial(n - 1)
    }
}
```

là runtime recursion hợp lệ.

Nhưng semantic query:

```text
infer(foo)
→ infer(foo)
```

có thể là inference cycle cần xử lý riêng.

Do đó Query Engine phải phân biệt:

```text
Runtime recursion
Semantic recursion
Query cycle
```

---

# 17. Cancellation

IDE cần cancellation:

```text
user types
 ↓
revision 101
 ↓
typecheck starts
 ↓
user types again
 ↓
revision 102
 ↓
revision 101 work obsolete
```

Compiler phải hủy query không còn cần thiết.

Không để IDE chờ pipeline cũ.

---

# 18. Stale Result

Một query có:

```text
revision = 101
```

không được trả về như kết quả hiện tại cho:

```text
revision = 102
```

trừ khi CompilerDB chứng minh semantic result vẫn valid.

Đây là:

```text
StaleRevisionError
```

hoặc internal invalidation.

---

# 19. Parallel Query Evaluation

Các query độc lập có thể chạy song song:

```text
type_of(A)
type_of(B)
type_of(C)
```

nếu không có dependency.

Query engine cần:

```text
work stealing
dependency scheduling
cancellation
priority
```

IDE query có thể ưu tiên cao hơn background codegen.

---

# 20. Query Priority

Các mức:

```text
Interactive
High
Normal
Background
Build
CacheWarmup
```

Ví dụ:

```text
hover
```

có priority cao.

Trong khi:

```text
whole-project optimization
```

có thể chạy background.

---

# 21. Memory Management của CompilerDB

CompilerDB có thể rất lớn.

Không nên giữ toàn bộ:

```text
AST
HIR
MIR
MachineIR
DebugInfo
```

vĩnh viễn trong RAM.

Dùng:

```text
hot cache
cold cache
persistent store
eviction
```

CompilerDB phải có object lifetime độc lập với source language ownership.

---

# 22. Immutable Semantic Nodes

Semantic node sau khi tạo nên immutable:

```text
TypeId → TypeRecord
FunctionId → FunctionRecord
```

Không:

```text
modify FunctionRecord in place
```

Mà:

```text
revision N
FunctionId → FunctionRecord A

revision N+1
FunctionId → FunctionRecord B
```

Điều này làm snapshot và concurrency dễ hơn.

---

# 23. Snapshot

CompilerDB hỗ trợ:

```text
Snapshot(Revision)
```

IDE/AI có thể hỏi:

```text
semantic snapshot
```

tại một revision nhất định.

Snapshot phải nhất quán.

---

# 24. Compiler Transactions

Build operation có thể hoạt động như transaction:

```text
begin revision
 ↓
evaluate queries
 ↓
verify
 ↓
publish artifacts
```

Nếu failure:

```text
rollback publication
```

Không để artifact trạng thái nửa mới/nửa cũ.

---

# 25. Dependency Impact Query

Một tính năng rất mạnh cho AI:

```text
impact(SymbolId)
```

Ví dụ:

```text
change User.name
```

Compiler trả:

```text
affected:
    serialization
    database mapping
    API foo
    API bar
    package X
```

và:

```text
unaffected:
    math
    renderer
```

AI có thể dùng trực tiếp.

---

# 26. Explain Query

CompilerDB phải lưu đủ provenance để:

```text
axiom explain
```

trả lời:

```text
Why is this type invalid?
Why did this move happen?
Why can't this view escape?
Why was this function selected?
Why is this GPU kernel illegal?
Why did this artifact rebuild?
```

Không giải thích bằng cách chạy lại một compiler khác.

---

# 27. Proof Objects

Query có thể sinh:

```text
ProofId
```

Ví dụ:

```text
OwnershipProof
TypeProof
TraitResolutionProof
CapabilityProof
EffectProof
RaceProof
KernelProof
ABIProof
```

Proof không nhất thiết chứa toàn bộ proof tree trong memory.

Có thể lưu compressed provenance.

---

# 28. Query Engine Architecture

Đề xuất:

```text
                 ┌─────────────────────┐
                 │    Query Frontends   │
                 │ Compiler / IDE / AI  │
                 └──────────┬──────────┘
                            │
                            ▼
                  ┌───────────────────┐
                  │   Query Engine    │
                  ├───────────────────┤
                  │ dependency graph  │
                  │ scheduler         │
                  │ cancellation      │
                  │ revision          │
                  │ cycle detection   │
                  └─────────┬─────────┘
                            │
                            ▼
                    ┌───────────────┐
                    │  CompilerDB   │
                    ├───────────────┤
                    │ SyntaxDB      │
                    │ TypeDB        │
                    │ TraitDB       │
                    │ MIRDB         │
                    │ ProofDB       │
                    │ BuildDB       │
                    │ ArtifactDB    │
                    └───────────────┘
```

---

# 29. Database Layers

Không nên có một bảng khổng lồ.

Nên chia logical stores:

```text
SourceDB
SyntaxDB
ModuleDB
SymbolDB
TypeDB
TraitDB
ImplDB
GenericDB
EffectDB
CapabilityDB
OwnershipDB
MIRDB
ProofDB
OptimizationDB
LIRDB
CodegenDB
DebugDB
BuildDB
PackageDB
ArtifactDB
DiagnosticDB
SemanticDB
```

Nhưng tất cả cùng một Query Engine.

---

# 30. Query API

Compiler internal API có dạng khái niệm:

```text
query type_of(expr: ExpressionId)
    -> TypeId

query resolve(symbol: SymbolRef)
    -> SymbolId

query mir(function: FunctionId)
    -> MirId

query verify(function: FunctionId)
    -> VerificationResult

query codegen(function: FunctionId, target: Target)
    -> ArtifactId
```

AI/IDE không được gọi internal mutable APIs.

Chỉ gọi read/query/code-action APIs được kiểm soát.

---

# 31. External Inputs

Các query có external input phải khai báo:

```text
Filesystem
Environment
Target
CompilerFlags
ComptimeInput
PackageRegistry
```

Ví dụ:

```text
read_file(...)
```

không được trở thành dependency ẩn.

Nó phải tạo:

```text
ExternalDependency
```

trong BuildGraph/CompilerDB.

---

# 32. Query Purity Classes

Có thể phân loại:

```text
PURE
DETERMINISTIC_EXTERNAL
NONDETERMINISTIC_EXTERNAL
SIDE_EFFECTING
```

Core semantic queries chủ yếu:

```text
PURE
```

Comptime/build queries có thể:

```text
DETERMINISTIC_EXTERNAL
```

hoặc capability-gated class.

---

# 33. Query Result Classes

Kết quả:

```text
Value
Diagnostic
Proof
Artifact
Deferred
Cycle
Cancelled
```

Không dùng exception làm cơ chế query control flow.

---

# 34. Error Caching

Nếu query thất bại vì semantic error:

```text
type_of(expr)
→ TypeError
```

có thể cache diagnostic result.

Nhưng khi dependency thay đổi:

```text
invalidate
```

Không cache compiler crash như semantic truth.

---

# 35. Compiler Crash vs User Error

Phải phân biệt:

```text
Expected diagnostic
```

và:

```text
ICE — Internal Compiler Error
```

ICE không được biến thành:

```text
"your code is invalid"
```

CompilerDB phải lưu:

```text
CrashReport
QueryStack
Revision
CompilerVersion
Target
RelevantInputs
```

để tái hiện.

---

# 36. Incremental Parsing

Thay đổi:

```text
fn foo(...) { ... }
```

không nên parse lại toàn bộ project.

SyntaxDB hỗ trợ incremental parsing:

```text
old syntax tree
       +
text edit
       ↓
new syntax tree
```

Các node không đổi có thể giữ identity.

---

# 37. Incremental Semantic Analysis

Sau parsing:

```text
changed syntax
 ↓
changed semantic entities
 ↓
dependency propagation
```

Ví dụ comment:

```text
semantic impact = none
```

Thay function signature:

```text
impact = callers + trait resolution + ABI + codegen
```

---

# 38. Incremental MIR

Nếu chỉ đổi body:

```text
fn foo()
```

có thể giữ:

```text
FunctionId
TypeId
Signature
```

và chỉ invalidate:

```text
MIR
Optimization
Codegen
```

của function đó cùng downstream dependencies.

---

# 39. Incremental ABI

Nếu implementation đổi nhưng public ABI không đổi:

```text
foo body changed
```

thì package consumers không cần semantic recompile nếu interface artifact vẫn tương thích.

Chỉ cần:

```text
foo implementation artifact
```

được rebuild.

Đây là chìa khóa để Axiom compile project lớn nhanh.

---

# 40. Incremental Optimization

Optimization phải có boundary.

Không phải mọi optimization đều local.

Ví dụ:

```text
function-local:
inline candidate
constant folding
DCE
```

có thể cache độc lập.

Cross-function:

```text
whole-program devirtualization
LTO
global escape analysis
```

phải có dependency scope lớn hơn.

Query system phải biết scope.

---

# 41. Query Scope

Mỗi query có:

```text
Local
Module
Package
Workspace
WholeProgram
Target
```

Ví dụ:

```text
type_of(expr)
→ Local

trait_resolution
→ Package

LTO
→ WholeProgram
```

---

# 42. Semantic Change Classification

Compiler nên phân loại thay đổi:

```text
TextOnly
SyntaxOnly
PrivateSemantic
PublicSemantic
LayoutChange
ABIChange
TargetChange
DependencyChange
BuildConfigChange
```

Từ đó quyết định invalidation.

---

# 43. Compiler Daemon

CompilerDB được thiết kế để chạy lâu dài:

```text
axiom daemon
```

IDE:

```text
LSP
 ↓
Compiler Daemon
 ↓
CompilerDB
```

Build CLI cũng có thể kết nối daemon:

```text
axiom build
 ↓
daemon
```

thay vì khởi động compiler từ đầu.

---

# 44. Daemon Crash Recovery

Compiler daemon phải có khả năng:

```text
persist cache
restart
recover
```

Semantic cache corruption không được làm source project mất dữ liệu.

Nếu database invalid:

```text
discard affected cache
recompute
```

---

# 45. Multi-client

Một CompilerDB daemon có thể phục vụ:

```text
IDE
CLI
AI Agent
Build process
Debugger
```

nhưng phải quản lý revision.

Ví dụ:

```text
IDE revision 100
AI revision 101
Build revision 100
```

Các client không được ghi đè semantic state của nhau.

---

# 46. AI Context Compression

405 đã yêu cầu AI semantic interface.

407 bổ sung:

AI không nên nhận:

```text
50000 dòng source
```

nếu chỉ cần:

```text
FunctionId
signature
dependencies
proof
diagnostics
```

CompilerDB có thể tạo:

```text
SemanticContext
```

theo yêu cầu.

Ví dụ:

```text
SemanticContext {
    symbol
    signature
    relevant_types
    relevant_traits
    effects
    capabilities
    ownership
    callers
    diagnostics
}
```

---

# 47. AI Patch Validation

AI tạo patch:

```text
source diff
```

CompilerDB xử lý:

```text
parse
→ resolve
→ typecheck
→ ownership
→ capability
→ effects
→ tests
→ build impact
```

và trả:

```text
PatchValidationResult
```

AI không được tự tuyên bố patch đúng.

---

# 48. Semantic Search

CompilerDB hỗ trợ truy vấn kiểu:

```text
find functions where:
    return = Result<T, E>
    async = true
    capability includes Network
```

hoặc:

```text
find types:
    implements Trait Serializable
    size < 64
```

Đây là semantic search chứ không phải text search.

---

# 49. CompilerDB API cho Agent

Agent có thể yêu cầu:

```text
workspace()
package()
module()
symbol()
type()
trait()
implementations()
callers()
references()
dependencies()
impact()
diagnostics()
proof()
mir()
abi()
artifact()
```

Nhưng:

```text
AI → CompilerDB
```

không phải:

```text
AI → compiler memory internals
```

---

# 50. Bộ invariant ADB — Axiom Database

Đóng băng:

### ADB-01
CompilerDB là nguồn sự thật semantic duy nhất.

### ADB-02
Mọi semantic fact phải truy xuất qua query model.

### ADB-03
Query phải có identity deterministic.

### ADB-04
Semantic query mặc định deterministic.

### ADB-05
External input phải được khai báo.

### ADB-06
Query dependency phải được tracking.

### ADB-07
Cache validity phải phụ thuộc semantic fingerprints.

### ADB-08
Timestamp không được là semantic identity.

### ADB-09
Comment-only change không được gây semantic invalidation.

### ADB-10
Unrelated semantic change không được invalidate query.

### ADB-11
Revision phải có identity rõ ràng.

### ADB-12
Stale query result không được coi là current.

### ADB-13
Query cancellation phải an toàn.

### ADB-14
Query cycle phải được phát hiện.

### ADB-15
Query cycle không được gây compiler stack overflow.

### ADB-16
Semantic nodes phải immutable sau publication.

### ADB-17
Snapshot phải nhất quán.

### ADB-18
CompilerDB phải hỗ trợ parallel queries.

### ADB-19
Parallel query không được thay đổi semantics.

### ADB-20
Diagnostic phải là query result có provenance.

### ADB-21
Proof phải gắn với semantic revision.

### ADB-22
Proof stale không được dùng cho revision mới.

### ADB-23
ICE phải phân biệt với user semantic error.

### ADB-24
Incremental parsing phải bảo toàn semantic identity khi có thể.

### ADB-25
Incremental compilation phải dựa trên dependency impact.

### ADB-26
ABI compatibility phải có query/proof riêng.

### ADB-27
Optimization cache không được thay đổi semantic result.

### ADB-28
AI phải truy vấn semantic facts thay vì tự suy đoán compiler state.

### ADB-29
AI-generated patch phải quay lại compiler verification.

### ADB-30
CompilerDB, IDE, AI, Build và Compiler phải dùng cùng semantic model.

---

# 51. Kiến trúc Compiler hoàn chỉnh hơn

Sau 407, pipeline trước đây được nâng thành:

```text
                         ┌──────────────────────┐
                         │      CompilerDB      │
                         │                      │
Source ──▶ Syntax ──────▶│ Queries              │
                         │ Dependency Graph     │
                         │ Revision             │
                         │ Fingerprints         │
                         │ Cache                │
                         │ Proofs               │
                         └──────────┬───────────┘
                                    │
             ┌──────────────────────┼─────────────────────┐
             │                      │                     │
             ▼                      ▼                     ▼
         Compiler                  IDE                   AI
             │                      │                     │
             └──────────────────────┼─────────────────────┘
                                    ▼
                              Build / Codegen
                                    │
                                    ▼
                               Artifacts
```

Và quan trọng nhất:

```text
CompilerDB
    ≠ cache đơn thuần
    ≠ AST database
    ≠ build database
```

Nó là **semantic incremental engine** của toàn bộ Axiom toolchain.

---

## Trạng thái

**BOOTSTRAP-407 — SPECIFIED / FROZEN**

Đây là nền móng để những phần compiler tiếp theo không biến thành một compiler pipeline khổng lồ khó incremental hóa.

Bước kế tiếp sẽ đi sâu vào **Resolver + Name Resolution + Module/Symbol/Scope system**, tức cách Axiom biến source text thành một semantic symbol graph chính xác trước khi bước sang type system và HIR.