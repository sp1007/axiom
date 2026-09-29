# BOOTSTRAP-333 — AXIOM PACKAGE/BUILD GRAPH & INCREMENTAL COMPILATION ENGINE

Sau Artifact-332, bước tiếp theo là giải quyết **toàn bộ dependency graph ở cấp compiler/build** và cách Axiom tận dụng nó để đạt:

- build cực nhanh;
- incremental compilation;
- cache chính xác;
- parallel compilation;
- distributed compilation;
- thay đổi một file không làm rebuild cả project;
- thay đổi implementation không làm rebuild dependency downstream nếu public semantic interface không đổi.

Đây là một phần rất quan trọng đối với mục tiêu Axiom vì compiler của Axiom có rất nhiều tầng phân tích mạnh: ownership, capability, trait solving, comptime, optimization, ABI, `.axif`... Nếu không có graph/incremental architecture tốt, compiler sẽ trở nên rất nặng.

---

# 1. Mục tiêu cốt lõi

Axiom phải phân biệt:

```text
Source dependency
Semantic dependency
Type dependency
Comptime dependency
ABI dependency
Codegen dependency
Optimization dependency
Runtime dependency
```

Không được có mô hình đơn giản:

```text
file A changed
    ↓
recompile everything
```

Mà:

```text
Source Change
     ↓
Dependency Analysis
     ↓
Determine affected semantic queries
     ↓
Invalidate minimal nodes
     ↓
Recompute
     ↓
Reuse everything else
```

---

# 2. Build Graph ≠ Module Graph

Có ít nhất 4 graph:

```text
Package Graph
Module Graph
Semantic Query Graph
Codegen Graph
```

Ví dụ:

```text
Package A
 ├── Package B
 └── Package C

Module A
 ├── Module B
 └── Module C

Function A
 ├── Type B
 ├── Trait C
 └── Comptime D
```

Không được gộp tất cả thành một graph.

---

# 3. Package Graph

Package Graph đến từ BOOTSTRAP-329:

```text
PackageInstance
      ↓
DependencyEdge
```

Mỗi edge có loại:

```text
Source
Binary
Type
Build
Comptime
Runtime
Optional
TargetSpecific
```

Ví dụ:

```text
A
├── B [type]
├── C [runtime]
├── D [build]
└── E [optional]
```

---

# 4. Module Graph

Một package:

```text
package app
```

có:

```text
app.main
app.ui
app.network
app.model
```

Module graph phải phân biệt:

```text
Import
Re-export
Type-only import
Compile-time import
Runtime import
```

---

# 5. Semantic dependency

Ví dụ:

```axiom
struct User {
    id: u64
}
```

và:

```axiom
fn print_user(u: User)
```

`print_user` phụ thuộc semantic vào:

```text
User layout/type identity
```

Nhưng nếu chỉ đổi:

```axiom
fn helper() {
    ...
}
```

mà helper private và không ảnh hưởng reachable semantics, `print_user` không cần rebuild semantic analysis.

---

# 6. Public/private boundary

Đây là nguyên tắc cực kỳ quan trọng:

```text
Private implementation change
        ↓
    local invalidation
```

trong khi:

```text
Public semantic change
        ↓
    downstream invalidation
```

Ví dụ:

```axiom
pub struct User {
    id: u64
}

fn internal_helper() { ... }
```

Thay đổi `internal_helper()` không làm package consumer rebuild semantic interface.

---

# 7. `.axif` làm semantic firewall

Package consumer không cần biết implementation.

```text
Package A
   │
   ├── source
   └── .axif
         │
         ▼
Package B
```

Nếu:

```text
public API fingerprint
ABI fingerprint
semantic fingerprint
```

không thay đổi:

> downstream semantic compilation có thể được giữ nguyên.

---

# 8. Semantic Fingerprints

Mỗi declaration có fingerprint:

```text
DeclarationFingerprint
```

Bao gồm tùy loại:

```text
name
visibility
type
generic constraints
trait relationships
effects
ownership contract
capability contract
ABI
comptime dependencies
```

Không bao gồm private implementation nếu không observable.

---

# 9. Fingerprint hierarchy

Có nhiều mức:

```text
SourceFingerprint
SyntaxFingerprint
DeclarationFingerprint
TypeFingerprint
SemanticFingerprint
InterfaceFingerprint
ABIFingerprint
CodegenFingerprint
OptimizationFingerprint
ArtifactFingerprint
```

Mỗi fingerprint phục vụ một tầng cache khác nhau.

---

# 10. Query-based incremental compiler

CompilerDB sử dụng query model:

```text
parse(file)
resolve(module)
type_of(expr)
trait_solve(goal)
lower_hir(module)
lower_mir(function)
verify(function)
optimize(function)
codegen(function)
```

Mỗi query:

```text
Inputs → Result
```

được cache.

---

# 11. Query invalidation

Ví dụ:

```text
source.ax
```

thay đổi.

Compiler không xóa toàn bộ database.

Nó:

```text
SourceFile
   ↓
Syntax queries
   ↓
Affected declarations
   ↓
Affected semantic queries
   ↓
Affected MIR
   ↓
Affected codegen
```

Các query không phụ thuộc vẫn giữ nguyên.

---

# 12. Red-green incremental model

Có thể dùng trạng thái:

```text
GREEN
RED
```

GREEN:

> cached result vẫn valid.

RED:

> một dependency thay đổi và cần recompute.

Nhưng Axiom cần mở rộng thành:

```text
Fresh
Stale
Invalid
Uncomputed
Verified
```

---

# 13. Verified cache

Một cache result không chỉ có:

```text
value
```

mà:

```text
CachedResult {
    value
    input_fingerprint
    semantic_version
    compiler_version
    target
    proof_dependencies
}
```

Đặc biệt:

> Verified MIR cache chỉ hợp lệ nếu các proof dependencies vẫn còn valid.

---

# 14. Proof dependency

Ví dụ optimization dựa trên:

```text
A và B disjoint
```

Cache phải biết optimization phụ thuộc vào:

```text
CapabilityProof #42
```

Nếu API/type thay đổi khiến proof #42 mất hiệu lực:

```text
optimization cache → invalid
```

nhưng parser/type queries khác có thể vẫn giữ.

---

# 15. Trait solver cache

Trait solving có thể rất tốn CPU.

Cache:

```text
TraitGoal
   ↓
SolverResult
```

Ví dụ:

```text
Send<Vec<User>>
```

result:

```text
Proven
```

Fingerprint phải bao gồm:

```text
type definitions
trait definitions
impl set
where clauses
edition
compiler semantic version
```

---

# 16. Generic specialization cache

Ví dụ:

```axiom
fn sort<T: Ord>(x: mut_view<T>)
```

với:

```text
sort<i32>
sort<f64>
sort<User>
```

Mỗi instance có:

```text
GenericInstanceFingerprint
```

Nếu generic function unchanged và type semantics unchanged:

> reuse specialization.

---

# 17. Monomorphization cache

Compiler có thể cache:

```text
Generic MIR
```

và:

```text
Specialized MIR
```

riêng biệt.

```text
Generic Function
       ↓
Specialization
       ↓
Verified MIR
```

Thay đổi target CPU:

```text
Verified MIR
```

có thể giữ lại trong khi:

```text
Machine Code
```

phải rebuild.

---

# 18. Target-specific cache layers

Cache phải tách:

```text
Target-independent
Target-dependent
CPU-feature-dependent
OS-dependent
ABI-dependent
```

Ví dụ:

```text
Typed HIR
```

có thể dùng chung.

Nhưng:

```text
Instruction Selection
```

không thể dùng chung giữa:

```text
x86-64
ARM64
WASM
```

---

# 19. Cross-compilation

Build:

```text
host = Windows x86-64
target = Linux ARM64
```

không được làm invalid toàn bộ semantic cache.

Pipeline:

```text
Source
 ↓
Semantic
 ↓
Target parameterization
 ↓
Target-specific lowering
 ↓
Machine code
```

---

# 20. Comptime dependency

Đây là một nguồn invalidation rất quan trọng.

Ví dụ:

```axiom
const schema = comptime read_source("schema.ax");
```

Compiler phải biết:

```text
Function
   ↓
Comptime Query
   ↓
schema.ax
```

Nếu `schema.ax` đổi:

```text
comptime result → invalid
```

và mọi declaration phụ thuộc vào result cũng invalid.

---

# 21. Comptime dependency graph

Mỗi comptime evaluation tạo:

```text
ComptimeDependency {
    input
    capability
    fingerprint
}
```

Ví dụ:

```text
ReadSource("schema.ax")
```

không phải:

```text
ReadFilesystem("*")
```

Nếu capability chỉ đọc một file thì invalidation chỉ giới hạn file đó.

---

# 22. Environment dependency

Nếu build sử dụng:

```text
ENV["TARGET_MODE"]
```

thì query fingerprint phải chứa:

```text
TARGET_MODE=value
```

Nếu environment value thay đổi:

```text
affected comptime queries → invalid
```

Không rebuild unrelated code.

---

# 23. Build script dependency

Build script:

```text
build.ax
```

sinh:

```text
generated.ax
```

Graph:

```text
build.ax
   ↓
tool
   ↓
generated.ax
   ↓
compiler
```

Compiler phải lưu provenance.

Nếu tool version thay đổi:

```text
generated source → stale
```

---

# 24. Dependency graph closure

Không tính closure bằng cách rebuild toàn bộ.

Thay vào đó:

```text
ChangedNode
     ↓
ReverseDependencyGraph
     ↓
AffectedNodes
```

Nhưng phải dừng tại semantic firewall nếu public contract không đổi.

---

# 25. Change classification

Mỗi source change được classify:

```text
WhitespaceOnly
CommentOnly
PrivateImplementation
PrivateType
PublicImplementation
PublicType
PublicABI
PublicTrait
ComptimeInput
BuildInput
TargetConfig
DependencyChange
```

Mỗi category có invalidation policy khác nhau.

---

# 26. Ví dụ

Ban đầu:

```axiom
pub fn add(a: i32, b: i32) -> i32 {
    helper(a,b)
}

fn helper(a: i32, b: i32) -> i32 {
    a + b
}
```

Đổi helper:

```axiom
fn helper(a: i32, b: i32) -> i32 {
    a - b
}
```

Có:

```text
Source changed
↓
private implementation changed
↓
local MIR invalid
↓
local codegen invalid
```

Nhưng interface của package không đổi.

Consumer semantic cache:

```text
GREEN
```

---

# 27. Public signature change

Đổi:

```text
i32 → i64
```

thì:

```text
DeclarationFingerprint changed
```

→ `.axif` semantic fingerprint changed

→ downstream declaration queries invalid

→ type checking downstream

→ MIR

→ codegen.

---

# 28. ABI-only change

Ví dụ:

```text
@repr(C)
```

hoặc calling convention thay đổi.

Có thể:

```text
SemanticFingerprint = unchanged
ABIFingerprint = changed
```

Khi đó:

```text
semantic downstream cache
```

có thể giữ.

Nhưng:

```text
ABI/codegen/link
```

phải rebuild.

Đây là lý do phải tách fingerprint.

---

# 29. Optimization invalidation

Optimization không được làm semantic cache dirty.

```text
Verified MIR
    │
    ├── O0
    ├── O2
    ├── O3
    └── size
```

Có thể dùng cùng semantic result.

Optimization fingerprint:

```text
OptimizationConfig
Target
PGO profile
CPU features
```

quyết định cache.

---

# 30. PGO invalidation

Nếu profile thay đổi:

```text
source unchanged
semantic unchanged
MIR unchanged
```

nhưng:

```text
optimization cache → invalid
machine code → invalid
```

Không cần parse/typecheck lại.

---

# 31. LTO cache

Whole-program optimization phụ thuộc vào:

```text
reachable graph
semantic summaries
ABI
optimization summaries
dynamic boundaries
```

`.axif` có thể cung cấp summary.

Nếu dependency implementation thay đổi nhưng summary tương đương:

> LTO có thể giữ một số result.

---

# 32. Dynamic components

Component-325 tạo dynamic boundary.

Nếu component implementation thay đổi nhưng contract fingerprint không đổi:

```text
host semantic cache
```

không invalid.

Runtime component loading có thể sử dụng artifact mới.

---

# 33. Build graph node

Node chung:

```text
BuildNode {
    id
    kind
    inputs
    outputs
    fingerprint
    dependencies
    capabilities
    target
    status
}
```

Kinds:

```text
Parse
Resolve
TypeCheck
TraitSolve
Comptime
HIR
MIR
Verify
Optimize
Codegen
Link
Package
Generate
Test
```

---

# 34. Build graph edge

Edge có:

```text
DependencyKind
Strength
FingerprintScope
```

Ví dụ:

```text
Semantic
ABI
Codegen
Optimization
Build
Runtime
```

---

# 35. Strong vs weak dependencies

Ví dụ optimization summary có thể là:

```text
WeakDependency
```

Nếu summary mất:

> optimization được recompute.

Không làm semantic correctness invalid.

Ngược lại:

```text
type definition
```

là strong semantic dependency.

---

# 36. Scheduler

Build graph scheduler phải hỗ trợ:

```text
topological execution
parallel execution
priority
resource limits
target workers
cache lookup
failure propagation
```

Nhưng phải deterministic về output.

---

# 37. Resource-aware scheduler

Ví dụ:

```text
CPU-heavy:
trait solving
optimization

Memory-heavy:
LTO
whole-program analysis

GPU:
GPU compilation

IO-heavy:
artifact fetch
cache
```

Scheduler có thể phân loại resource.

Không để 32 job LLVM-like chạy đồng thời rồi hết RAM.

---

# 38. Critical path

Compiler có thể tính:

```text
CriticalPath
```

để ưu tiên node.

Ví dụ:

```text
A ── B ── D
 \       /
  └─ C ─
```

Nếu D đang block toàn build:

> ưu tiên A/B/C thay vì job không nằm trên critical path.

---

# 39. Incremental failure recovery

Nếu một query fail:

```text
TraitSolverError
```

không được phá toàn bộ cache.

Cached valid results vẫn giữ.

Sau khi source sửa:

```text
affected query
```

được recompute.

---

# 40. Crash-safe cache

Compiler crash giữa build:

```text
partial cache
```

không được corrupt valid cache.

Transaction:

```text
Compute
 ↓
Validate
 ↓
Write temp
 ↓
fsync/commit
 ↓
Publish cache entry
```

---

# 41. Cache corruption

Mỗi cache artifact:

```text
payload
metadata
hash
```

phải verify.

Nếu mismatch:

```text
discard cache entry
recompute
```

Không coi cache là trusted semantic source.

---

# 42. Compiler version

Cache key phải chứa:

```text
CompilerSemanticVersion
```

nhưng không nhất thiết:

```text
CompilerBuildTimestamp
```

Nếu compiler internal implementation thay đổi nhưng semantics không đổi, có thể giữ cache nếu contract cho phép.

Tách:

```text
SemanticCompilerVersion
ImplementationVersion
```

---

# 43. Semantic version vs implementation version

Ví dụ:

```text
Compiler 1.8.0
```

có optimization bug fix nhưng semantic model unchanged.

Một số semantic caches có thể reuse.

Nhưng:

```text
MachineCode cache
```

có thể invalid nếu backend thay đổi.

---

# 44. Cache trust

Không được giả định:

```text
cache == truth
```

Cache là:

> previously computed result.

Các result safety-critical như:

```text
OwnershipProof
CapabilityProof
ABIProof
```

phải có proof dependency + compiler semantic identity.

---

# 45. Distributed cache

Remote cache artifact:

```text
request
 ↓
download
 ↓
hash verify
 ↓
metadata verify
 ↓
proof dependency verify
 ↓
accept
```

Không thực thi remote result trước khi verify.

---

# 46. Distributed compiler

Worker nhận:

```text
BuildNode
InputArtifacts
CompilerIdentity
Target
Capabilities
```

Worker trả:

```text
ResultArtifact
ResultFingerprint
ProofMetadata
Attestation
```

Coordinator verify.

---

# 47. Deterministic worker

Hai worker:

```text
Linux x86
Linux x86
```

cùng compiler/target/input phải tạo semantic result tương đương.

Nếu binary reproducibility yêu cầu:

```text
byte-identical
```

thì backend phải canonicalize machine output.

---

# 48. Incremental testing

Test graph cũng incremental.

Ví dụ:

```text
unit test A
unit test B
unit test C
```

Nếu chỉ function X thay đổi:

```text
tests depending on X → rerun
```

Không nhất thiết chạy toàn bộ suite.

Nhưng CI có thể policy:

```text
always run full suite
```

---

# 49. Incremental documentation

Docs generation cũng là build node:

```text
API
 ↓
Documentation
```

Public API fingerprint unchanged:

> docs có thể reuse.

Implementation-only change:

> public docs không cần regenerate.

---

# 50. Incremental LSP

Language Server dùng cùng CompilerDB.

Khi user sửa:

```text
one expression
```

LSP chỉ invalidates affected queries.

Không chạy full compiler.

Điều này rất quan trọng để Axiom IDE có phản hồi gần realtime.

---

# 51. Query observability

Compiler phải cho biết:

```text
Why was this rebuilt?
```

Ví dụ:

```text
Function foo rebuilt because:

Public type User changed
    ↓
ABIFingerprint changed
    ↓
MIR invalidated
```

Hoặc:

```text
sort<i32> reused from cache
```

---

# 52. CLI

```text
axiom build

axiom build --incremental
axiom build --clean
axiom build --explain-rebuild

axiom cache inspect
axiom cache verify
axiom cache gc

axiom graph package
axiom graph module
axiom graph semantic
axiom graph build

axiom query explain <query>
axiom query dependencies <query>
axiom query invalidation <query>
```

---

# 53. Compiler APIs

```text
compute_fingerprint()
classify_change()

query()
query_cached()
invalidate_query()

get_dependencies()
get_reverse_dependencies()

explain_invalidation()
explain_rebuild()

schedule_build()
schedule_parallel()

load_cached_result()
verify_cached_result()
store_cached_result()

compute_critical_path()

invalidate_by_semantic_change()
invalidate_by_abi_change()
invalidate_by_target_change()
invalidate_by_comptime_change()
```

---

# 54. CompilerDB additions

```text
QueryDB
DependencyGraphDB
ReverseDependencyDB
FingerprintDB
IncrementalStateDB
CacheDB
ProofCacheDB
BuildGraphDB
BuildSchedulerDB
BuildResourceDB
InvalidationDB
DistributedBuildDB
```

---

# 55. Implementation architecture

```text
compiler/
├── query/
│   ├── engine/
│   ├── dependency/
│   ├── fingerprint/
│   ├── invalidation/
│   └── cache/
│
├── build/
│   ├── graph/
│   ├── scheduler/
│   ├── resource/
│   ├── critical_path/
│   └── distributed/
│
└── incremental/
    ├── semantic/
    ├── abi/
    ├── comptime/
    ├── codegen/
    ├── optimization/
    └── testing/
```

---

# 56. Invariants

```text id="AINCR-01"
Every cached query result must identify its semantic inputs.

AINCR-02
Invalidation must operate on dependency edges, not whole projects.

AINCR-03
Private implementation changes must not invalidate unrelated public interfaces.

AINCR-04
Public semantic changes must invalidate all dependent semantic queries.

AINCR-05
ABI changes must invalidate ABI-dependent results without necessarily invalidating semantic-only results.

AINCR-06
Target changes must invalidate target-dependent stages only.

AINCR-07
Optimization configuration changes must not invalidate semantic analysis.

AINCR-08
PGO changes must invalidate dependent optimization/codegen results.

AINCR-09
Comptime inputs must participate in dependency fingerprints.

AINCR-10
Build-tool inputs must participate in dependency fingerprints.

AINCR-11
Proof-dependent optimizations must record their proof dependencies.

AINCR-12
Invalid proofs must invalidate dependent transformations.

AINCR-13
Cached safety proofs must never survive incompatible semantic changes.

AINCR-14
Remote cache results must be independently verified.

AINCR-15
Cache corruption must cause recomputation, never semantic acceptance.

AINCR-16
Parallel compilation must remain deterministic.

AINCR-17
Distributed compilation must preserve semantic equivalence.

AINCR-18
Compiler crashes must not corrupt previously valid cache entries.

AINCR-19
Build graph scheduling must respect dependency ordering.

AINCR-20
Scheduler parallelism must respect resource limits.

AINCR-21
Dynamic component boundaries must limit invalidation to their declared contracts.

AINCR-22
AXIF interface stability must act as a semantic invalidation firewall.

AINCR-23
Semantic, ABI, codegen and optimization fingerprints must remain independently addressable.

AINCR-24
Incremental compilation must not alter language semantics.

AINCR-25
A clean build and a fully incremental build must produce semantically equivalent results.

AINCR-26
If binary reproducibility is requested, clean and incremental builds must produce byte-equivalent artifacts.

AINCR-27
LSP queries must reuse the same semantic truth as full compilation.

AINCR-28
Test invalidation must be derived from dependency information rather than source-file heuristics alone.

AINCR-29
Every rebuild should be explainable through a dependency/fingerprint chain.

AINCR-30
The incremental engine must remain an optimization of compilation, never a source of semantic authority.
```

---

# 57. Definition of Done

BOOTSTRAP-333 hoàn thành khi Axiom có:

- Package Graph.
- Module Graph.
- Semantic Query Graph.
- Build Graph.
- Codegen Graph.
- Query-based incremental compiler.
- Dependency tracking.
- Reverse dependency tracking.
- Multi-level fingerprints.
- Change classification.
- Semantic firewall.
- `.axif` incremental boundary.
- Trait-solver caching.
- Generic specialization caching.
- Comptime dependency tracking.
- Build-script dependency tracking.
- Proof dependency tracking.
- Target-aware cache.
- ABI-aware cache.
- Optimization-aware cache.
- PGO-aware cache.
- LTO-aware cache.
- Incremental test graph.
- Incremental LSP.
- Parallel build scheduler.
- Resource-aware scheduling.
- Critical-path scheduling.
- Crash-safe cache.
- Cache integrity verification.
- Remote cache.
- Distributed compilation foundation.
- Build explanation.
- Invalidation explanation.
- Deterministic incremental output.
- Integration với Package-329.
- Build Sandbox-331.
- Artifact-332.
- `.axif`-323.
- ABI-324.
- Component-325.
- CompilerDB/Query Engine.
- Proof/Verification infrastructure.

### Nguyên tắc khóa

> **Axiom không rebuild vì “file thay đổi”; Axiom rebuild vì một semantic dependency đã thay đổi.**

Và sâu hơn:

> **Mỗi tầng của compiler phải có fingerprint và invalidation boundary riêng.**

Đây là thứ cho phép Axiom vừa có compiler rất mạnh — ownership, trait solving, comptime, whole-program optimization, proof verification — vừa không biến mỗi lần sửa một dòng code thành một full rebuild.