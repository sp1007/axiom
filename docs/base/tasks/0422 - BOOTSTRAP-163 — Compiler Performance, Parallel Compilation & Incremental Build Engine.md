# BOOTSTRAP-163 — Compiler Performance, Parallel Compilation & Incremental Build Engine
**STATUS: FROZEN / COMPLETED**

> **Compiler phải nhanh ngay cả khi Axiom có semantic analysis rất sâu. Mọi phép phân tích độc lập phải có thể chạy song song; mọi kết quả không thay đổi phải được tái sử dụng; parallelism không được làm mất tính deterministic.**

---

## 1. Compiler execution model

Chốt kiến trúc:

```text
                         CompilerDB
                             │
                    Dependency Graph
                             │
                    Query Scheduler
                             │
              ┌──────────────┼──────────────┐
              ▼              ▼              ▼
           Frontend       Analysis       Codegen
              │              │              │
              └──────────────┼──────────────┘
                             ▼
                       Artifact Cache
```

Compiler không phải một pipeline tuần tự khổng lồ.

Mỗi compiler computation là một **query có dependency**.

---

# 2. Query model

Ví dụ:

```text
parse(file)
resolve(module)
type_of(expr)
trait_solve(goal)
lower_mir(function)
verify_mir(function)
optimize(function)
lower_abi(function)
codegen(function)
```

Mỗi query:

```text
Inputs → Result
```

và CompilerDB ghi nhận dependencies.

---

# 3. Incremental principle

Nếu sửa:

```text
foo.ax
```

compiler không được mặc định:

```text
recompile everything
```

Mà:

```text
foo.ax
 ↓
affected syntax
 ↓
affected declarations
 ↓
affected semantic queries
 ↓
affected MIR
 ↓
affected machine code
```

Phần không bị ảnh hưởng được giữ lại.

---

# 4. Revision model

CompilerDB sử dụng:

```text
RevisionId
```

Mỗi source/database mutation tạo revision mới.

Derived query có thể kiểm tra:

```text
input fingerprint
dependency fingerprint
revision
```

để quyết định cache còn hợp lệ.

---

# 5. Fine-grained invalidation

Không chỉ:

```text
file changed
→ module invalid
```

mà cố gắng:

```text
field changed
→ affected declaration
→ affected downstream queries
```

Tuy nhiên interface fingerprint vẫn là boundary để tránh dependency graph quá chi tiết.

---

# 6. Interface vs implementation

Đã frozen trước đây:

```text
Public Interface Fingerprint
Implementation Fingerprint
```

Nếu đổi:

```ax id="l2r3x7"
fn internal() { ... }
```

không nên invalidate mọi consumer.

Nếu đổi:

```ax id="w8a6b2"
pub struct API { ... }
```

thì downstream có thể phải rebuild.

---

# 7. Semantic fingerprint

Fingerprint bao gồm những thứ thực sự ảnh hưởng semantic result:

```text
type
trait
generic
repr
ABI
comptime dependency
target
features
compiler semantic version
```

Không hash những thứ không liên quan.

---

# 8. Parallel query scheduler

Scheduler:

```text
Ready Queries
      │
      ▼
Work Queue
      │
 ┌────┼────┬────┐
 ▼    ▼    ▼    ▼
CPU0 CPU1 CPU2 CPU3
```

Các query không có dependency lẫn nhau được chạy đồng thời.

---

# 9. Work stealing

Mỗi worker có local deque.

```text
Worker 0 ─ local tasks
Worker 1 ─ local tasks
Worker 2 ─ local tasks
Worker 3 ─ local tasks
```

Worker rảnh có thể steal task từ worker khác.

Mục tiêu:

- giảm contention,
- tận dụng nhiều core,
- cân bằng workload.

---

# 10. Deterministic result

Parallel execution order:

```text
không deterministic
```

nhưng semantic result:

```text
phải deterministic
```

Ví dụ hai query hoàn thành theo thứ tự khác nhau không được tạo khác diagnostic/type/layout.

---

# 11. Canonicalization

Những collection mà thứ tự không có ý nghĩa phải canonicalize:

```text
HashMap iteration
parallel result
trait candidates
dependency sets
diagnostic sets
symbol collections
```

Không để hash iteration order lọt vào semantics.

---

# 12. Parallel type checking

Các function độc lập:

```text
foo()
bar()
baz()
```

có thể type-check song song sau khi declaration/interface collection hoàn thành.

---

# 13. Parallel trait solving

Trait goals độc lập:

```text
T: Copy
T: Ord
U: Hash
```

có thể solve song song.

Shared memoization phải thread-safe và deterministic.

---

# 14. Trait solver contention

Không dùng một global lock lớn.

Thay vào đó:

```text
canonical goal
→ concurrent memo table
→ immutable result
```

Các semantic objects ưu tiên immutable/interned.

---

# 15. Parallel MIR lowering

Các function có thể lower:

```text
foo → MIR
bar → MIR
baz → MIR
```

song song.

Generic instances cũng có thể được partition.

---

# 16. Parallel verification

Đây là điểm quan trọng vì verifier rất nặng.

Các function độc lập:

```text
Ownership
Initialization
Capability
Drop
Concurrency
```

có thể chạy song song.

Trong một function, các CFG region độc lập cũng có thể được phân tích song song ở những stage phù hợp.

---

# 17. Shared dataflow engine

`DataflowAnalysis<State>` đã thiết kế trước đó.

Compiler có thể dùng cùng engine cho:

```text
ownership
initialization
liveness
capability
escape
range
effects
```

giảm duplication và giúp parallelization nhất quán.

---

# 18. Deterministic fixed point

Loop/SCC analysis:

```text
SCC
 ↓
worklist
 ↓
fixed point
```

thứ tự xử lý worklist có thể khác nhau nhưng lattice join phải đảm bảo kết quả canonical.

---

# 19. Parallel optimization

Có thể chạy:

```text
Function A optimization
Function B optimization
Function C optimization
```

song song.

Trong một function, các optimization region/pass có dependency phải tuần tự.

---

# 20. Pass dependency graph

Không hard-code:

```text
pass1
pass2
pass3
```

thành một chuỗi duy nhất.

Có:

```text
OptimizationPipelineGraph
```

Ví dụ:

```text
SROA ──┐
       ├── GVN ── DCE
Alias ─┘
```

Scheduler chạy pass độc lập song song khi có thể.

---

# 21. Không parallelize mù quáng

Một pass chỉ được parallel nếu:

```text
no conflicting mutable state
```

hoặc compiler cung cấp isolated snapshot.

Correctness trước throughput.

---

# 22. Immutable IR

Các IR objects nên immutable sau khi hoàn thành phase:

```text
Verified MIR
OptIR snapshot
ABI MIR
```

Transformation tạo revision/new representation thay vì nhiều thread cùng mutate một object.

---

# 23. Mutable builder phase

Trong construction phase:

```text
MIRBuilder
OptBuilder
```

có thể mutable nhưng ownership của builder phải rõ.

Không chia sẻ builder mutable giữa worker nếu không cần.

---

# 24. Type interning

`TypeDB` interning phải concurrent.

Hai worker request:

```text
Vec<i32>
```

phải nhận cùng canonical `TypeId`.

Không tạo:

```text
TypeId 100
TypeId 104
```

cho cùng semantic type.

---

# 25. Declaration interning

Tương tự:

```text
GenericInstanceId
TraitGoal
ConstValue
LayoutKey
```

được canonicalize.

---

# 26. Cache hierarchy

Giữ cache nhiều tầng:

```text
L0  in-memory query cache
L1  session cache
L2  local artifact cache
L3  shared/remote cache
L4  package/dependency cache
```

Không phải mọi project đều cần remote cache.

---

# 27. Content-addressed cache

Artifact identity:

```text
ArtifactKey =
    source fingerprint
  + dependency fingerprints
  + compiler semantic version
  + target
  + ABI
  + profile
  + features
  + comptime inputs
  + codegen configuration
```

---

# 28. Cache không được ảnh hưởng semantics

Cache hit:

```text
semantic result A
```

Cache miss:

```text
semantic result A
```

phải giống nhau.

Cache là performance mechanism.

---

# 29. Cache poisoning defense

Cache artifact phải verify:

```text
artifact key
metadata
compiler version
target
ABI
content hash
```

Không tin artifact chỉ vì filename giống nhau.

---

# 30. Comptime cache

Comptime đã có dependency graph.

Ví dụ:

```text
comptime fn generate()
```

phụ thuộc:

```text
source
filesystem input
environment
```

thì cache key phải bao gồm những inputs đó.

---

# 31. Parallel comptime

Các comptime invocation độc lập có thể chạy song song.

Nhưng external capabilities phải obey:

```text
sandbox
dependency tracking
determinism
```

---

# 32. Comptime side effects

Nếu comptime ghi file:

```text
WriteGenerated
```

scheduler phải biết dependency/output relationship.

Không cho hai task ghi cùng output một cách race-condition mà semantic result phụ thuộc scheduling.

---

# 33. Parallel code generation

Generic instances có thể codegen song song:

```text
Vec<i32>
Vec<f32>
HashMap<K,V>
...
```

sau semantic specialization hoàn tất.

---

# 34. Object writing

Mỗi object section/object file có thể được tạo song song.

Sau đó linker thực hiện deterministic merge.

---

# 35. Parallel linker

Có thể song song:

```text
symbol indexing
archive scanning
relocation analysis
section analysis
debug processing
```

nhưng final layout phải canonical.

---

# 36. Deterministic link

Final:

```text
section order
symbol order
relocation order
archive extraction
padding decisions
```

phải deterministic trong reproducible mode.

---

# 37. Parallel build graph

Package graph:

```text
A
├── B
├── C
└── D
```

B/C/D build song song.

Nếu:

```text
E → B
```

thì E đợi B.

---

# 38. Module graph

Module cycles được phép nhưng build scheduler phải xử lý SCC:

```text
A ↔ B ↔ C
```

thành một semantic SCC.

Package cycles vẫn reject.

---

# 39. Workspace scheduling

Một workspace lớn:

```text
100 packages
5000 modules
```

scheduler nên ưu tiên critical path.

Có thể dùng:

```text
critical-path priority
dependency depth
estimated compile cost
cache hit probability
```

---

# 40. Compile cost model

Compiler theo dõi:

```text
ParseCost
ResolveCost
TypeCost
TraitCost
MIRCost
VerifyCost
OptimizeCost
CodegenCost
LinkCost
```

để scheduler dự đoán workload.

---

# 41. Adaptive scheduling

Ví dụ trait solver package cực nặng.

Scheduler có thể ưu tiên:

```text
heavy query
```

sớm để tránh CPU idle.

Đây là compiler optimization, không semantic.

---

# 42. Memory budgeting

Parallel compiler dễ gặp:

```text
N workers × N GB
```

→ OOM.

Scheduler cần:

```text
MemoryBudget
```

và worker admission control.

---

# 43. Backpressure

Nếu codegen queue quá lớn:

```text
frontend
  ↓
1000 MIRs
  ↓
memory explosion
```

scheduler có thể tạm giảm frontend parallelism.

---

# 44. Query cancellation

IDE:

```text
user typing
```

→ revision mới.

Query cũ:

```text
cancel
```

nhưng build chính thức có thể disable cancellation ở critical phases.

---

# 45. Priority classes

Đề xuất:

```text
Interactive
Build
Background
Indexing
Analysis
Optimization
```

IDE query ưu tiên cao hơn background indexing.

---

# 46. Incremental IDE

Khi user gõ:

```text
fn foo...
```

IDE không cần đợi:

```text
whole workspace
whole optimization
whole linker
```

để trả:

```text
type
completion
diagnostic
```

---

# 47. Lazy codegen

IDE check không codegen machine code.

Pipeline có thể dừng:

```text
Source
→ HIR
→ Typed HIR
```

hoặc:

```text
→ MIR
→ Verified MIR
```

tùy query.

---

# 48. Lazy optimization

`axc check` không cần:

```text
LTO
PGO
vectorization
machine encoding
```

`axc build` mới yêu cầu các phase cần thiết.

---

# 49. Query demand-driven

Ví dụ IDE hỏi:

```text
type_at(position)
```

compiler không nên build:

```text
entire binary
```

Query graph chỉ compute dependency cần thiết.

---

# 50. Compilation modes

Chốt các mode:

```text
check
build
run
test
bench
emit
inspect
```

mỗi mode có query demand khác nhau.

---

# 51. Fast edit mode

Có thể có:

```text
axc check --incremental
```

với mục tiêu latency thấp.

Không cần tạo native executable.

---

# 52. Fast build mode

Development:

```text
incremental
parallel
minimal optimization
debug info
```

Release:

```text
maximum optimization
LTO
PGO optional
reproducibility
```

---

# 53. ThinLTO architecture

Whole-program optimization đã frozen.

Để scale project lớn:

```text
Module compile
 ↓
summary/index
 ↓
parallel optimization
 ↓
distributed codegen
```

giảm memory peak so với full monolithic LTO.

---

# 54. Full LTO

Vẫn hỗ trợ:

```text
full LTO
```

cho executable cần maximum global optimization.

---

# 55. Distributed compilation

Kiến trúc cho phép:

```text
Developer
   ↓
Build Graph
 ┌─┼──────────┐
 ▼ ▼          ▼
Node1 Node2   Node3
```

nhưng remote execution không phải Core requirement.

---

# 56. Remote cache

Có thể dùng:

```text
content-addressed artifact
```

và verify hash.

Không cần tin remote server.

---

# 57. Build reproducibility

Parallel execution:

```text
worker order A
```

hay:

```text
worker order B
```

phải tạo cùng artifact trong reproducible mode.

---

# 58. Timestamp/path normalization

Artifact không nên chứa:

```text
machine-specific temp path
wall-clock timestamp
random ID
```

nếu reproducible build yêu cầu loại bỏ chúng.

---

# 59. Randomness

Nếu compiler dùng randomized algorithms để optimization:

- default reproducible mode phải seed deterministic;
- nếu có nondeterministic performance mode, seed phải trở thành build metadata.

---

# 60. Incremental correctness

Không được:

```text
cache hit
→ skip verifier
```

một cách mù quáng.

Cached Verified MIR phải được xác thực bằng fingerprint/schema/compiler semantic version.

---

# 61. Compiler versioning

Thay đổi semantic compiler:

```text
compiler semantic version
```

có thể invalidate semantic caches.

Thay đổi UI:

```text
diagnostic wording
```

không nhất thiết invalidate codegen cache.

---

# 62. Cache schema version

Mỗi persistent cache:

```text
CacheSchemaVersion
```

để compiler mới không đọc nhầm representation cũ.

---

# 63. Memory reclamation

Compiler DB có thể rất lớn.

Cần:

```text
arena
intern pool
generation
reference tracking
snapshot reclamation
```

và garbage collection **của compiler process** có thể được dùng nếu implementation cần.

Điều này **không liên quan** tới Axiom runtime và không tạo GC cho chương trình Axiom.

---

# 64. Đây là distinction quan trọng

Axiom application:

```text
NO mandatory GC
```

Axiom compiler:

```text
có thể dùng GC / arena / refcount / Rust-like implementation
```

nếu giúp compiler nhanh và an toàn.

Ngôn ngữ implementation không cần tự áp dụng toàn bộ runtime model cho compiler.

---

# 65. Parallel memory arenas

Compiler có thể dùng:

```text
ThreadLocalArena
```

cho temporary IR/query data.

Sau khi task hoàn tất:

```text
arena reset
```

giảm allocator contention.

---

# 66. Interned objects lifetime

Semantic interned objects sống theo:

```text
CompilerDB snapshot/session
```

không theo từng query.

---

# 67. Snapshot isolation

Một query có thể đọc immutable snapshot trong khi background thread tạo revision mới.

Điều này rất hữu ích cho IDE.

---

# 68. Transactional update

Source edit:

```text
apply edit
→ new revision
```

không để CompilerDB rơi vào trạng thái semantic half-updated.

---

# 69. Query dependency tracing

Compiler có thể inspect:

```text
axc inspect query type_of Foo
```

và hiển thị:

```text
type_of
 ↓
resolve
 ↓
trait_solve
 ↓
normalize
 ↓
const_eval
```

---

# 70. Compile performance explanation

```text
axc inspect compile foo
```

có thể trả:

```text
Parsing             12 ms
Resolution          18 ms
Type checking       43 ms
Trait solving       61 ms
MIR                  9 ms
Verification        37 ms
Optimization        92 ms
Codegen             31 ms
Link                 8 ms
```

kèm:

```text
cache hits
cache misses
parallelism
peak memory
```

---

# 71. Bottleneck explanation

```text
axc explain compile-bottleneck
```

Ví dụ:

```text
Trait solving:
    31% of compiler time

Primary cause:
    18,420 unique generic obligations

Cache reuse:
    94%

Parallel efficiency:
    71%
```

AI có thể dùng trực tiếp.

---

# 72. Parallel efficiency metrics

Compiler có thể theo dõi:

```text
CPU utilization
parallel speedup
critical path
worker idle time
lock contention
memory bandwidth
cache hit rate
```

nhưng đây là diagnostics, không semantics.

---

# 73. Compiler self-optimization

Khi Axiom compiler được self-hosted, chính compiler có thể dùng:

```text
PGO
LTO
cache
parallel build
```

để tối ưu compiler.

Compiler bootstrap không cần special language privileges.

---

# 74. Bootstrap implications

Stage 0:

```text
external compiler
```

Stage 4:

```text
Axiom compiler compiled by Axiom itself
```

Compiler performance infrastructure phải tồn tại trong Axiom implementation architecture từ sớm, nhưng feature có thể triển khai dần.

---

# 75. Parallel backend

Target-independent optimization có thể chạy song song.

Target backend instances:

```text
x86-64
AArch64
RISC-V
WASM
GPU
```

có thể compile song song trong cross-build.

---

# 76. Multi-target builds

Ví dụ:

```text
axc build --target x86_64
axc build --target aarch64
```

có thể share:

```text
Source
AST
HIR
Type
Trait
MIR
```

và chỉ tách từ target-dependent phases khi semantics cho phép.

---

# 77. Target-independent cache

Đây là optimization lớn:

```text
Source
 ↓
HIR
 ↓
Typed HIR
 ↓
MIR
```

có thể reuse giữa:

```text
x86-64
AArch64
RISC-V
```

nếu target-independent.

Target-specific:

```text
Layout
ABI
LIR
Machine
```

phải tách cache key.

---

# 78. Cross-target invalidation

Thay đổi CPU feature:

```text
AVX2 → AVX512
```

không cần reparse source.

Chỉ invalidate target-dependent phases.

---

# 79. Generic specialization cache

Generic:

```text
foo<T>
```

có thể có:

```text
GenericSemanticInstance
```

dùng chung giữa target.

Nhưng:

```text
MachineSpecialization
```

thường target-specific.

---

# 80. Invariants

Đóng băng:

### `ACOMPIL-20`
Compiler computations are represented as dependency-tracked queries.

### `ACOMPIL-21`
Incremental compilation reuses valid query results.

### `ACOMPIL-22`
Query invalidation is dependency-driven.

### `ACOMPIL-23`
Public interface changes are distinguished from implementation changes.

### `ACOMPIL-24`
Semantic fingerprints determine relevant cache validity.

### `ACOMPIL-25`
Independent compiler queries may execute concurrently.

### `ACOMPIL-26`
Parallel execution must not alter semantic results.

### `ACOMPIL-27`
Semantic collections have deterministic canonical ordering where required.

### `ACOMPIL-28`
Compiler semantic objects are immutable after publication where practical.

### `ACOMPIL-29`
Type interning produces canonical semantic TypeIds.

### `ACOMPIL-30`
Trait solving supports concurrent memoization.

### `ACOMPIL-31`
MIR lowering may execute independently per function.

### `ACOMPIL-32`
Verification may execute independently across independent compilation units.

### `ACOMPIL-33`
Dataflow fixed points remain deterministic under parallel scheduling.

### `ACOMPIL-34`
Optimization passes have explicit dependency relationships.

### `ACOMPIL-35`
Independent optimization work may execute concurrently.

### `ACOMPIL-36`
Parallel optimization cannot bypass legality checks.

### `ACOMPIL-37`
Code generation may execute concurrently for independent instances.

### `ACOMPIL-38`
Object generation may execute concurrently.

### `ACOMPIL-39`
Link-time parallelism must preserve deterministic final layout.

### `ACOMPIL-40`
Package DAG dependencies constrain build scheduling.

### `ACOMPIL-41`
Module SCCs are scheduled as semantic units where required.

### `ACOMPIL-42`
Package cycles remain invalid.

### `ACOMPIL-43`
Compiler scheduling may prioritize critical paths without changing semantics.

### `ACOMPIL-44`
Compiler memory usage must be bounded through resource-aware scheduling.

### `ACOMPIL-45`
Compiler supports backpressure between pipeline stages.

### `ACOMPIL-46`
Interactive compiler queries support cancellation.

### `ACOMPIL-47`
Interactive queries have higher priority than background work where appropriate.

### `ACOMPIL-48`
IDE queries do not require full executable code generation.

### `ACOMPIL-49`
Compiler work is demand-driven where practical.

### `ACOMPIL-50`
Persistent caches are content-addressed or equivalently integrity-checked.

### `ACOMPIL-51`
Cache hits and misses cannot change program semantics.

### `ACOMPIL-52`
Cache artifacts are validated against compiler and schema identity.

### `ACOMPIL-53`
Comptime cache identity includes all observable external dependencies.

### `ACOMPIL-54`
Parallel comptime execution obeys capability and dependency constraints.

### `ACOMPIL-55`
ThinLTO can scale whole-program optimization without requiring monolithic compilation.

### `ACOMPIL-56`
Full LTO remains available where global optimization is desired.

### `ACOMPIL-57`
Remote/distributed compilation is optional.

### `ACOMPIL-58`
Reproducible builds do not depend on worker scheduling order.

### `ACOMPIL-59`
Compiler randomness is deterministic in reproducible mode.

### `ACOMPIL-60`
Persistent cache schema versions are explicit.

### `ACOMPIL-61`
Compiler semantic-version changes may invalidate semantic caches.

### `ACOMPIL-62`
Compiler implementation may use memory-management techniques independent of Axiom application semantics.

### `ACOMPIL-63`
Compiler snapshots provide consistent query views.

### `ACOMPIL-64`
Source updates are transactional at the CompilerDB level.

### `ACOMPIL-65`
Compiler dependency graphs are inspectable.

### `ACOMPIL-66`
Compiler performance metrics are non-semantic diagnostics.

### `ACOMPIL-67`
Compiler bottlenecks can be exposed through structured performance data.

### `ACOMPIL-68`
Target-independent IR can be reused across compatible target builds.

### `ACOMPIL-69`
Target-specific cache invalidation begins only at the first target-dependent phase.

### `ACOMPIL-70`
Generic semantic analysis and target-specific machine specialization are separately cacheable.

### `ACOMPIL-71`
Compiler parallelism cannot weaken verification.

### `ACOMPIL-72`
Compiler optimization cannot depend on execution scheduling.

### `ACOMPIL-73`
Compiler correctness takes precedence over maximum parallelism.

### `ACOMPIL-74`
Compiler performance infrastructure does not alter Axiom language semantics.

### `ACOMPIL-75`
AI tooling may consume compiler performance/query provenance.

### `ACOMPIL-76`
Compiler execution remains deterministic under reproducible configuration.

### `ACOMPIL-77`
Incremental compilation must be semantically equivalent to clean compilation.

### `ACOMPIL-78`
Parallel compilation must be semantically equivalent to serial compilation.

### `ACOMPIL-79`
Cached compilation must be semantically equivalent to uncached compilation.

### `ACOMPIL-80`
Axiom compiler architecture must scale from small files to large multi-package workspaces.

---

# Kiến trúc compiler hiện đã tiến tới mức khá hoàn chỉnh

Đến đây, ta có thể nhìn Axiom compiler thành 5 tầng lớn:

```text
┌───────────────────────────────────────────────┐
│              DEVELOPER / AI UX                │
│ Diagnostics • IDE • Explain • Debug • Query  │
├───────────────────────────────────────────────┤
│               BUILD ENGINE                    │
│ Incremental • Parallel • Cache • LTO • PGO   │
├───────────────────────────────────────────────┤
│             SEMANTIC COMPILER                 │
│ Type • Trait • Ownership • Capability • Drop │
│ Async • GPU • FFI • Comptime • Effects       │
├───────────────────────────────────────────────┤
│              OPTIMIZATION                     │
│ SSA • MemorySSA • Alias • Escape • Loop      │
│ SIMD • Layout • Microarch • Specialization   │
├───────────────────────────────────────────────┤
│                CODEGEN                        │
│ ABI • LIR • Machine • Object • Linker        │
│ PE/ELF/Mach-O/WASM                            │
└───────────────────────────────────────────────┘
```

Điểm đáng chú ý là **không còn cần thêm một “magic optimizer” nào nữa**. Những thành phần quan trọng nhất của compiler core đã gần đủ.

---

# BOOTSTRAP-164 — Testing at Scale, Fuzzing, Differential Testing & Compiler Bug Defense

Bước tiếp theo là một bước cực kỳ quan trọng trước khi tiếp tục mở rộng language features:

> **Làm thế nào chứng minh compiler Axiom không tạo ra binary sai khi compiler ngày càng tối ưu mạnh?**

Task 164 sẽ xây dựng lớp phòng thủ:

```text
Specification
      ↓
Conformance Tests
      ↓
Semantic Interpreter
      ↓
MIR Verification
      ↓
Optimization Validation
      ↓
Differential Testing
      ↓
Fuzzing
      ↓
Random Program Generation
      ↓
Minimization
      ↓
Regression Corpus
      ↓
Cross-target Validation
```

Đặc biệt sẽ khóa **metamorphic testing**, **miscompilation detection**, **IR fuzzing**, **backend fuzzing**, **compiler crash fuzzing**, và cơ chế đảm bảo rằng:

```text
-O0
-O2
-O3
-LTO
-PGO
x86-64
ARM64
RISC-V
WASM
```

đều phải giữ nguyên semantic result.