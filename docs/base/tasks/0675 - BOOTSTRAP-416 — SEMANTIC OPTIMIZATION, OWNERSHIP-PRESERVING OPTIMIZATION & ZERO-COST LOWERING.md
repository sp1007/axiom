# BOOTSTRAP-416 — SEMANTIC OPTIMIZATION, OWNERSHIP-PRESERVING OPTIMIZATION & ZERO-COST LOWERING

**Trạng thái:** SPECIFIED / FROZEN  
**Phụ thuộc:** 413 MIR, 414 Control Flow, 415 Drop Elaboration  
**Mục tiêu:** định nghĩa tầng tối ưu hóa **sau khi MIR đã hoàn toàn được verify**, trước khi chuyển sang ABI MIR/LIR.

Đây là tầng quyết định Axiom có thực sự đạt mục tiêu **“đơn giản cho programmer nhưng hiệu năng cấp C/C++ hoặc cao hơn”** hay không.

---

# 416.1. Nguyên tắc nền tảng

Axiom chia optimization thành hai tầng:

```text
Semantic Optimization
        ↓
ABI / Target Optimization
```

Semantic Optimization chỉ làm việc với:

```text
types
ownership
capabilities
effects
control flow
resources
async
concurrency
GPU
```

Nó **không phụ thuộc CPU cụ thể**.

Ví dụ:

```text
eliminate allocation
inline function
remove temporary
fuse loops
specialize generic
eliminate bounds check
```

đều có thể thực hiện trước khi biết x86-64 hay ARM64.

---

# 416.2. Verified MIR là optimization boundary

Pipeline:

```text
HIR
 ↓
MIR
 ↓
Ownership Verification
 ↓
Capability Verification
 ↓
Effect Verification
 ↓
Drop Elaboration
 ↓
Verified MIR
 ↓
Semantic Optimization
 ↓
Optimized Verified MIR
 ↓
ABI MIR
```

Chỉ:

```text
Verified MIR
```

mới được tối ưu mạnh.

Điều này cực kỳ quan trọng.

Optimizer không được trở thành nơi “sửa” lỗi semantics.

---

# 416.3. Optimizer không được phá proof

Mọi optimization phải bảo toàn:

```text
Type
Ownership
Initialization
Drop
Capability
Effect
Atomic semantics
Concurrency semantics
Async semantics
GPU legality
FFI semantics
Observable ordering
```

Nếu optimization tạo ra MIR mới:

```text
Optimized MIR
```

thì MIR mới phải được verifier kiểm tra lại.

---

# 416.4. Optimization Proof

Mỗi optimization transformation có thể được mô hình hóa:

```text
OptimizationProof {
    source_region
    transformed_region
    semantic_relation
    preserved_effects
    preserved_resources
    preserved_observations
}
```

Không nhất thiết lưu toàn bộ proof trong release binary.

CompilerDB giữ proof để:

- debug compiler;
- `axiom explain`;
- compiler testing;
- AI inspection;
- miscompilation investigation.

---

# 416.5. Observable Semantics

Optimizer chỉ phải bảo toàn những gì chương trình có thể quan sát.

Các observable category:

```text
Value
Memory
I/O
Resource destruction
Atomic operations
Synchronization
Panic/trap
FFI calls
Stable addresses
Timing contracts explicitly exposed by API
```

Compiler không phải bảo toàn:

```text
register allocation
instruction count
temporary address
internal object layout
physical allocation
```

nếu chúng không observable.

---

# 416.6. Copy Elision

Ví dụ:

```axiom
fn make() -> BigStruct {
    return BigStruct(...)
}
```

Compiler không nhất thiết:

```text
construct temporary
copy temporary
move temporary
```

có thể:

```text
caller storage
      ↑
construct directly
```

Semantic:

```text
one resulting value
```

Machine implementation:

```text
zero intermediate copies
```

---

# 416.7. Move Elimination

```axiom
let a = create()
let b = a
use(b)
```

Nếu `a` không còn được dùng:

```text
a → b
```

có thể được biến thành:

```text
create()
use(result)
```

Không cần physical move.

Đây là một điểm rất quan trọng của Axiom:

> **Move là ownership transition, không phải machine copy.**

---

# 416.8. Temporary Elimination

```axiom
foo(make_resource())
```

không cần:

```text
temporary
 ↓
move
 ↓
foo
```

có thể:

```text
construct directly into call argument storage
```

nếu ABI cho phép.

---

# 416.9. Scalar Replacement

```axiom
struct Vec2 {
    x: f32
    y: f32
}
```

Nếu address không observable:

```text
Vec2 object
```

có thể trở thành:

```text
x register
y register
```

Không cần memory object.

---

# 416.10. Allocation Elimination

```axiom
let x = Box::new(T(...))
use(x)
```

Nếu:

```text
address never escapes
stable address not observed
```

compiler có thể biến:

```text
heap allocation
```

thành:

```text
stack/register/SSA
```

hoặc loại bỏ storage hoàn toàn.

Do đó:

> `Box<T>` biểu diễn ownership semantics; không nhất thiết ép optimizer phải dùng heap.

---

# 416.11. Escape Analysis

Compiler phân loại:

```text
NO_ESCAPE
LOCAL_ESCAPE
CALL_ESCAPE
THREAD_ESCAPE
ASYNC_ESCAPE
FFI_ESCAPE
GLOBAL_ESCAPE
```

Ví dụ:

```text
NO_ESCAPE
```

cho phép:

- stack allocation;
- register allocation;
- scalar replacement;
- allocation elimination.

---

# 416.12. Stable Address Escape

Nếu:

```axiom
let p = address_of(x)
```

và API yêu cầu stable address:

```text
address observable
```

thì compiler phải bảo toàn storage identity.

Điều này tạo optimization barrier.

---

# 416.13. Dead Code Elimination

Nếu expression không có observable effect:

```axiom
let x = 1 + 2
```

và `x` không được dùng:

```text
eliminate
```

Nhưng:

```axiom
file.close()
```

không được coi là dead chỉ vì return value không dùng.

Bởi vì:

```text
resource effect
```

là observable.

---

# 416.14. Effect-Aware DCE

Mỗi function có effect metadata.

Ví dụ:

```text
pure
read_memory
write_memory
allocate
deallocate
io
sync
atomic
panic
ffi
gpu
```

Optimizer dùng effect graph để biết expression nào thực sự loại bỏ được.

---

# 416.15. Constant Folding

```axiom
let x = 10 * 20
```

→ `200`.

Nhưng constant folding phải tuân thủ integer semantics đã định nghĩa.

Ví dụ overflow không được biến thành:

```text
undefined behavior
```

chỉ vì optimizer muốn thuận tiện.

---

# 416.16. Algebraic Simplification

Ví dụ:

```text
x + 0
x * 1
x && true
```

có thể simplify khi semantics cho phép.

Nhưng:

```text
x / x
```

không được tự động thành:

```text
1
```

nếu `x = 0` có observable trap/panic semantics.

---

# 416.17. Bounds Check Elimination

Axiom không mặc định biến array access thành unchecked.

Ví dụ:

```axiom
for i in 0..n {
    sum += a[i]
}
```

Compiler có thể chứng minh:

```text
0 <= i < a.len
```

và loại bỏ bounds check.

Không cần programmer viết:

```text
unsafe
```

cho trường hợp compiler chứng minh được.

---

# 416.18. Bounds Check Hoisting

Nếu loop:

```text
for i in 0..n {
    a[i]
    a[i+1]
}
```

compiler có thể chuyển:

```text
check each iteration
```

thành:

```text
check once before loop
```

nếu invariant chứng minh được.

---

# 416.19. Loop Invariant Code Motion

Expression không thay đổi trong loop:

```axiom
for i in 0..n {
    x = expensive_constant()
}
```

có thể:

```text
x = expensive_constant()

for i in 0..n {
    use(x)
}
```

Nhưng chỉ khi effect analysis chứng minh việc di chuyển không thay đổi semantics.

---

# 416.20. Loop Fusion

```text
for i in 0..n {
    a[i] *= 2
}

for i in 0..n {
    b[i] = a[i] + 1
}
```

có thể fuse thành một loop nếu:

```text
dependency
effect
alias
ordering
```

được chứng minh an toàn.

Đây là nơi capability/region analysis của Axiom trở nên rất có giá trị.

---

# 416.21. Loop Fission

Ngược lại, compiler có thể tách loop nếu:

```text
cache locality
vectorization
parallelization
```

được cải thiện và semantics không đổi.

---

# 416.22. Automatic Vectorization

Semantic MIR:

```text
for i in range {
    out[i] = a[i] + b[i]
}
```

có thể trở thành:

```text
SIMD loop
```

nếu compiler chứng minh:

```text
no invalid overlap
aligned/unaligned access acceptable
no conflicting effects
```

Programmer không cần viết SIMD intrinsic cho trường hợp thông thường.

---

# 416.23. Alias-Aware Optimization

Axiom không yêu cầu programmer viết `restrict`.

Thay vào đó compiler sử dụng:

```text
view provenance
mut_view exclusivity
ownership
region analysis
escape analysis
```

để chứng minh alias properties.

Ví dụ:

```axiom
fn add(
    a: view<f32>,
    b: view<f32>,
    out: mut_view<f32>
)
```

Nếu verifier chứng minh `out` không overlap `a`/`b`:

```text
vectorization
load/store reordering
```

được phép.

---

# 416.24. Unknown Alias

Nếu compiler không chứng minh được:

```text
a overlaps out?
```

thì không được tự giả định:

```text
DISJOINT
```

Có thể:

```text
reject API
```

hoặc:

```text
generate conservative code
```

tùy semantics của API.

---

# 416.25. Function Inlining

Optimizer có thể inline:

```text
foo(x)
```

thành:

```text
body(foo)
```

dựa trên:

```text
size
hotness
generic specialization
effects
call frequency
target information
```

Inlining không thay đổi source semantics.

---

# 416.26. Aggressive Inlining

Không phải function nào cũng inline.

Axiom optimizer có thể có:

```text
inline(always)
inline(never)
inline(hint)
```

nhưng các annotation này là optimization hints, không phải semantic guarantees, trừ khi sau này định nghĩa explicit ABI contract.

---

# 416.27. Generic Specialization

Ví dụ:

```axiom
fn max<T: Ordered>(a: T, b: T)
```

Compiler có thể tạo:

```text
max_i32
max_f64
max_CustomType
```

theo từng concrete instantiation.

---

# 416.28. Monomorphization vs Code Sharing

Axiom mặc định ưu tiên:

```text
monomorphization
```

để đạt:

- specialization;
- inlining;
- constant propagation;
- SIMD;
- layout optimization.

Nhưng compiler có thể dùng code sharing khi:

```text
representation identical
optimization benefit negligible
binary-size profile enabled
```

---

# 416.29. Devirtualization

Nếu:

```text
dyn Trait
```

nhưng compiler chứng minh concrete implementation duy nhất:

```text
dynamic dispatch
```

có thể trở thành:

```text
direct call
```

Nếu không chứng minh được:

```text
dynamic dispatch remains
```

---

# 416.30. Trait Specialization

Static trait dispatch:

```text
T: Trait
```

được resolve càng sớm càng tốt.

Nếu implementation đã biết:

```text
TraitCall
 ↓
FunctionId
```

sau đó optimizer có thể inline.

---

# 416.31. Constant Propagation

```axiom
const N = 1024

fn f() {
    let a: [u8; N]
}
```

compiler biết `N`.

Kết quả:

```text
array length = 1024
```

có thể được propagate xuyên generic/comptime boundaries.

---

# 416.32. Branch Simplification

```axiom
if comptime CONDITION {
    ...
} else {
    ...
}
```

branch không tồn tại trong runtime MIR sau comptime evaluation.

Runtime:

```text
if x > 0
```

chỉ được eliminate nếu compiler chứng minh `x > 0`.

---

# 416.33. Panic/Trap Optimization

Ví dụ:

```axiom
if index >= a.len {
    panic()
}

use(a[index])
```

sau proof:

```text
bounds check
```

tại `a[index]` có thể bị loại.

Nhưng panic semantics phải được bảo toàn nếu invalid path có thể xảy ra.

---

# 416.34. Drop Optimization

Sau 415:

```text
DROP(x)
```

optimizer có thể:

### Trường hợp 1

```text
TrivialDrop
```

→ remove.

### Trường hợp 2

```text
Drop has no observable effect
```

→ remove nếu proof hợp lệ.

### Trường hợp 3

```text
Drop has I/O/resource effect
```

→ retain.

---

# 416.35. Drop Fusion

Ví dụ:

```text
DROP(temp)
DROP(container)
```

nếu semantics cho phép compiler có thể lower thành một cleanup sequence tối ưu.

Nhưng **không được đảo thứ tự destruction**.

---

# 416.36. Cleanup Path Folding

Ví dụ nhiều branch đều:

```text
DROP(a)
DROP(b)
RETURN
```

compiler có thể merge:

```text
BB1 ─┐
BB2 ─┼→ CleanupAB → Return
BB3 ─┘
```

Giảm code size.

---

# 416.37. Ownership-Aware Dead Store Elimination

Ví dụ:

```axiom
x.field = value1
x.field = value2
```

Nếu `value1` chưa từng observable và không có Drop/effect:

```text
first store
```

có thể bỏ.

Nhưng nếu `value1` là Drop-bearing resource:

```text
assignment replacement
```

phải xử lý destruction semantics trước khi bỏ store.

---

# 416.38. Memory Coalescing

Compiler có thể merge memory operations:

```text
load a
load b
```

thành vector load hoặc wider load nếu:

```text
alignment
alias
volatile
atomic
FFI
```

cho phép.

---

# 416.39. Volatile / Device Memory Barrier

Axiom phải có memory classes không được optimize như ordinary memory:

```text
volatile
atomic
MMIO
device
external
```

Ví dụ:

```text
MMIO write
```

không được DCE.

---

# 416.40. Atomic Optimization

Atomic operations không được biến thành ordinary loads/stores.

Nhưng compiler có thể tối ưu nếu semantic ordering cho phép.

Ví dụ:

```text
RELAXED
```

có optimization freedom lớn hơn:

```text
SEQCST
```

Nhưng compiler phải giữ đúng memory model.

---

# 416.41. Concurrency Optimization

Compiler có thể:

```text
remove redundant synchronization
merge operations
eliminate impossible races
specialize lock-free paths
```

chỉ khi proof đảm bảo không thay đổi concurrency semantics.

---

# 416.42. Async Optimization

Async state machine:

```text
state 1
state 2
state 3
```

có thể được:

- state merge;
- dead state removal;
- frame field elimination;
- capture shrinking;
- stack promotion;
- suspension elimination.

Ví dụ:

```axiom
async fn f() {
    let x = 1
    await ready()
    return x
}
```

nếu compiler chứng minh `x` không cần tồn tại qua suspension:

```text
frame field x
```

có thể loại bỏ.

---

# 416.43. Async Allocation Elimination

Task/coroutine frame có thể được:

```text
heap allocated
stack allocated
caller allocated
embedded
```

tùy escape analysis.

Nếu:

```text
task does not escape
```

compiler có thể tránh heap allocation.

Đây là mục tiêu quan trọng để async không mặc định trở thành “allocation-heavy”.

---

# 416.44. Parallelization

Loop có thể được tự động biến thành:

```text
parallel_for
```

nếu compiler chứng minh:

```text
iterations independent
no conflicting writes
reduction valid
effects compatible
```

Nếu không chứng minh được:

```text
remain sequential
```

Không được tự ý parallelize chỉ vì loop “trông có vẻ độc lập”.

---

# 416.45. Reduction Recognition

Ví dụ:

```axiom
sum = 0

for x in data {
    sum += x
}
```

compiler có thể nhận diện reduction.

Sau đó:

```text
parallel reduction
SIMD reduction
tree reduction
```

nếu floating-point semantics cho phép.

Đối với floating-point, compiler phải tôn trọng profile về:

```text
strict FP
fast FP
```

---

# 416.46. Floating-Point Optimization Profiles

Axiom nên có:

```text
fp = strict
fp = balanced
fp = fast
```

### `strict`

Giữ semantics FP chặt.

### `balanced`

Cho phép các phép biến đổi đã định nghĩa an toàn.

### `fast`

Cho phép:

- reassociation;
- contraction;
- approximate transformations;
- aggressive vectorization.

Nhưng phải là **profile rõ ràng**, không phải UB ngầm.

---

# 416.47. Profile-Based Optimization

Build profile:

```text
debug
release
speed
size
balanced
freestanding
sanitize
```

Optimizer dùng profile để điều chỉnh strategy.

Ví dụ:

```text
speed:
    aggressive inline
    vectorization
    specialization

size:
    code sharing
    outline
    conservative inline
```

---

# 416.48. Interprocedural Optimization

Semantic optimizer không giới hạn trong một function.

Compiler có thể phân tích:

```text
Function A
 ↓
Function B
 ↓
Function C
```

để biết:

```text
effects
ownership
escape
constant arguments
return properties
```

Từ đó:

```text
interprocedural constant propagation
escape analysis
dead argument elimination
devirtualization
inlining
```

---

# 416.49. Whole-Program Optimization

Nếu build configuration cho phép:

```text
whole_program = true
```

compiler có thể biết toàn bộ call graph.

Ví dụ function:

```text
public fn internal_only()
```

nếu không có external ABI exposure:

```text
visibility reduction
dead function elimination
aggressive specialization
```

---

# 416.50. Separate Compilation

Axiom vẫn phải tối ưu tốt khi module được compile riêng.

Interface artifact có thể chứa semantic metadata:

```text
effect summary
ownership summary
inline candidate
generic metadata
layout contract
ABI
optimization facts
```

Nhờ vậy module A có thể optimize call tới B mà không cần source B.

---

# 416.51. Optimization Cache

CompilerDB lưu:

```text
OptimizationSummary
FunctionEffectSummary
EscapeSummary
AliasSummary
InliningSummary
SpecializationSummary
LoopAnalysis
VectorizationAnalysis
```

Nếu source semantics không đổi:

```text
recompute
```

không cần làm lại toàn bộ.

---

# 416.52. Semantic Fingerprint

Optimization cache key:

```text
SemanticFingerprint {
    function semantic hash
    dependency fingerprints
    compiler semantic version
    target-independent optimization level
}
```

Không dùng timestamp làm identity.

---

# 416.53. Optimization Pass Architecture

Không nên có một “siêu optimizer” duy nhất.

Axiom dùng pass graph:

```text
Verified MIR
   ↓
Canonicalization
   ↓
Const Propagation
   ↓
Simplification
   ↓
CFG Simplification
   ↓
Ownership/Drop Optimization
   ↓
Escape Analysis
   ↓
Inlining
   ↓
Generic Specialization
   ↓
Alias/Range Analysis
   ↓
Loop Optimization
   ↓
Vectorization
   ↓
Async Optimization
   ↓
Parallelization
   ↓
Effect Optimization
   ↓
Cleanup
   ↓
Optimized MIR
```

Pass graph có thể thay đổi theo target/profile.

---

# 416.54. Không được phụ thuộc LLVM

Axiom có thể sử dụng LLVM trong **bootstrap compiler ban đầu** nếu cần, nhưng semantic optimization model của Axiom không được định nghĩa dựa trên LLVM IR.

Mục tiêu cuối:

```text
Axiom MIR
   ↓
Axiom LIR
   ↓
Axiom Machine IR
   ↓
Axiom codegen
```

Điều này cần thiết cho:

- self-hosting;
- GPU;
- custom ABI;
- AI compiler integration;
- ownership-aware optimization;
- compact compiler architecture.

---

# 416.55. Optimization không được phá Debug Semantics

Nếu source:

```axiom
let x = ...
```

bị optimize thành:

```text
nothing
```

debugger phải có thể báo:

```text
x = optimized_out
```

thay vì giả vờ rằng machine variable vẫn tồn tại.

Compiler giữ:

```text
SourceSymbol
 ↕
ValueId
 ↕
OptimizedValue
 ↕
MachineLocation
```

mapping.

---

# 416.56. `axiom explain optimize`

Axiom nên cung cấp:

```text
axiom explain optimize function_name
```

Ví dụ:

```text
Allocation eliminated:
    Box<Resource> did not escape.

Bounds check eliminated:
    i ∈ [0, len).

Function inlined:
    hot call site.

Vectorization enabled:
    out does not alias input.

Drop retained:
    destructor has observable I/O.
```

Đây là điểm rất mạnh đối với AI agent.

---

# 416.57. AI có thể hỏi Optimizer

AI semantic API có thể truy vấn:

```text
why_allocation_exists
why_not_vectorized
why_not_inlined
why_bounds_check_remains
why_storage_escaped
why_drop_not_eliminated
why_parallelization_failed
```

Thay vì AI phải đoán từ assembly.

---

# 416.58. CompilerDB additions

```text
OptimizationDB
OptimizationPassDB
OptimizationProofDB
ConstEvalOptimizationDB
EscapeAnalysisDB
AliasAnalysisDB
RangeAnalysisDB
EffectOptimizationDB
OwnershipOptimizationDB
DropOptimizationDB
InliningDB
SpecializationDB
LoopOptimizationDB
VectorizationDB
ParallelizationDB
AsyncOptimizationDB
InterproceduralDB
WholeProgramDB
DebugOptimizationDB
OptimizationExplanationDB
```

---

# 416.59. Proofs

```text
OptimizationCorrectnessProof
ConstantPropagationProof
DeadCodeProof
BoundsEliminationProof
AliasDisjointProof
AllocationEliminationProof
CopyElisionProof
MoveElisionProof
InliningProof
DevirtualizationProof
SpecializationProof
LoopTransformationProof
VectorizationProof
ParallelizationProof
AsyncOptimizationProof
DropOptimizationProof
AtomicOptimizationProof
FFIOptimizationProof
```

---

# 416.60. Invariants `AOPT`

```text
AOPT-01  Only VerifiedMIR may enter semantic optimization.
AOPT-02  Optimization preserves observable semantics.
AOPT-03  Optimization preserves ownership semantics.
AOPT-04  Optimization preserves initialization semantics.
AOPT-05  Optimization preserves Drop semantics.
AOPT-06  Optimization preserves capability validity.
AOPT-07  Optimization preserves effect semantics.
AOPT-08  Optimization preserves atomic ordering.
AOPT-09  Optimization preserves concurrency semantics.
AOPT-10  Optimization preserves async suspension semantics.
AOPT-11  Optimization preserves GPU execution legality.
AOPT-12  Optimization preserves FFI contracts.
AOPT-13  Unknown aliasing is never treated as proven disjoint.
AOPT-14  Move elimination never changes ownership state.
AOPT-15  Copy elimination never changes observable semantics.
AOPT-16  Allocation elimination requires valid escape proof.
AOPT-17  Storage scalarization requires address non-observability.
AOPT-18  Stable-address contracts prevent invalid scalarization.
AOPT-19  Bounds checks may be removed only with proof.
AOPT-20  Loop transformations preserve dependency semantics.
AOPT-21  Vectorization preserves memory and effect semantics.
AOPT-22  Automatic parallelization requires independence proof.
AOPT-23  Drop elimination requires destruction proof.
AOPT-24  Async frame optimization preserves live-across-suspend values.
AOPT-25  Atomic operations retain required ordering.
AOPT-26  FFI calls retain ABI and ownership contracts.
AOPT-27  Every semantic transformation is re-verifiable.
AOPT-28  Debug provenance is preserved where possible.
AOPT-29  Optimization metadata is deterministic for identical inputs.
AOPT-30  Optimized MIR remains semantically valid before ABI lowering.
```

---

# 416.61. Kiến trúc sau 416

Axiom lúc này có một ranh giới rất rõ:

```text
                 SOURCE
                   │
                   ▼
             Semantic Compiler
                   │
                   ▼
                Verified MIR
                   │
          ┌────────┴────────┐
          │                 │
          ▼                 ▼
   Semantic Analysis   Optimization
          │                 │
          └────────┬────────┘
                   ▼
          Optimized Verified MIR
                   │
                   ▼
                ABI MIR
                   │
                   ▼
                Axiom LIR
                   │
                   ▼
             Machine IR
                   │
                   ▼
          Target Optimization
                   │
                   ▼
          Register Allocation
                   │
                   ▼
             Machine Code
```

Điểm quan trọng nhất của 416 là:

> **Axiom không dựa vào việc bắt programmer viết nhiều annotation để đạt hiệu năng. Compiler dùng ownership, capability, effect, escape và type information đã có sẵn để tự chứng minh những tối ưu mà C/C++ thường phải dựa vào convention, `restrict`, inline hints hoặc programmer discipline.**

Vì vậy mục tiêu **“simple source + aggressive native optimization”** bắt đầu trở thành một kiến trúc compiler cụ thể, chứ không chỉ là khẩu hiệu.

**BOOTSTRAP-416 — SPECIFIED / FROZEN.**