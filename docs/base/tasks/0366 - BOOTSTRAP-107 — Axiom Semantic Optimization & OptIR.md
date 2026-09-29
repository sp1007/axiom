# BOOTSTRAP-107 — Axiom Semantic Optimization & OptIR
**FROZEN / COMPLETED**

Đây là tầng biến các guarantee mà Axiom đã chứng minh thành **hiệu năng thực tế**.

Điểm cốt lõi:

> **Axiom không bắt programmer viết `restrict`, lifetime, ownership hay optimization annotation chỉ để compiler tối ưu. Verifier đã chứng minh những facts đó; optimizer sử dụng chúng.**

---

# 1. Vị trí

```text
Source
  ↓
AST
  ↓
HIR
  ↓
Typed / Elaborated HIR
  ↓
MIR
  ↓
Verification
  ↓
━━━━━━━━━━━━━━━━━━━━━━
      VERIFIED MIR
━━━━━━━━━━━━━━━━━━━━━━
  ↓
Semantic Analysis
  ↓
SSA Construction
  ↓
MemorySSA
  ↓
Alias Analysis
  ↓
Effect Analysis
  ↓
Escape Analysis
  ↓
Range / Loop Analysis
  ↓
OptIR
  ↓
Optimization
  ↓
ABI MIR
```

---

# 2. MIR và OptIR phải khác nhau

Đây là quyết định quan trọng.

### MIR

Ưu tiên:

- semantic clarity
- ownership
- capability
- Drop
- CFG
- source mapping
- verification

### OptIR

Ưu tiên:

- SSA
- dataflow
- alias
- memory dependence
- scalar values
- loop analysis
- target-independent optimization

Do đó:

```text
MIR ≠ SSA optimizer IR
```

---

# 3. OptIR

Đề xuất:

```text id="o5z3r7"
OptFunction {
    blocks
    values
    memory
    aliases
    effects
    ranges
    loops
    escapes
    target_info
}
```

Mỗi value:

```text id="x7a9m2"
OptValue {
    ValueId
    TypeId
    Def
    Uses
    SourceOrigin
}
```

---

# 4. SSA

MIR:

```text
x = ...
x = ...
x = ...
```

OptIR:

```text id="6z9b2f"
%x0
%x1
%x2
```

Tại CFG merge:

```text id="9w2r6k"
%x3 = phi(%x1, %x2)
```

SSA giúp:

- constant propagation
- CSE
- GVN
- DCE
- range analysis
- vectorization
- register allocation preparation

---

# 5. MemorySSA

SSA cho values chưa đủ.

Memory:

```text id="m3x8c1"
store a
store b
load a
```

cần memory dependence.

OptIR có:

```text id="h8y5s4"
MemoryDef
MemoryUse
MemoryPhi
```

để biết load/store phụ thuộc memory version nào.

---

# 6. AliasInfo

Đây là nơi Axiom có thể tạo lợi thế lớn.

Compiler có thể biết:

```text id="k4f8s2"
A and B are DISJOINT
```

nhờ capability verification.

Optimizer chuyển thành:

```text id="q9c3v1"
NoAlias(A, B)
```

**chỉ khi fact đã được chứng minh.**

---

# 7. Không được biến UNKNOWN thành NoAlias

Ví dụ:

```text id="m8v1c6"
A : UNKNOWN
B : UNKNOWN
```

optimizer không được:

```text id="d3x7p0"
assume_noalias(A, B)
```

Điều này cực kỳ quan trọng để không tạo miscompilation.

---

# 8. Alias lattice

Có thể dùng:

```text id="r2j8v4"
NO_ALIAS
MUST_ALIAS
PARTIAL_ALIAS
MAY_ALIAS
UNKNOWN
```

Nguồn facts:

```text id="n6c4w1"
ownership
capability
provenance
field layout
range analysis
API contracts
FFI contracts
unsafe contracts
```

---

# 9. Ownership giúp optimizer

Ví dụ:

```axiom id="f3s8d2"
fn process(a: mut_view<f32>, b: mut_view<f32>) {
    ...
}
```

Verifier chứng minh:

```text id="v7q1m5"
region(a) DISJOINT region(b)
```

Optimizer có thể dùng:

```text id="c2k9x4"
NoAlias(a, b)
```

để:

- reorder loads
- reorder stores
- vectorize
- eliminate reload
- hoist loads
- store forwarding

mà không cần programmer viết `restrict`.

---

# 10. Đây là “compiler-derived restrict”

Axiom không có source-level:

```text
restrict
```

trong Core v1.

Nhưng compiler có thể tạo internal:

```text id="z5p8k3"
NoAliasFact
```

khi đã chứng minh.

Đây là đúng tinh thần:

> **Compiler understands more than programmer must write.**

---

# 11. Capability facts không nhất thiết tồn tại runtime

Sau verification:

```text id="v3m7k8"
Capability
```

có thể erase.

Chỉ giữ:

```text id="j4c1n9"
NoAlias
ReadOnly
ExclusiveWrite
```

dưới dạng compiler fact.

Do đó không có runtime overhead.

---

# 12. Read-only propagation

Nếu compiler biết:

```text id="x5n8p2"
view<T>
```

là READ-only:

```text id="q7c3v6"
memory is not modified through this capability
```

Optimizer có thể:

- cache load
- CSE
- hoist
- eliminate redundant loads

nếu các effect khác không invalidate.

---

# 13. Write effect

`mut_view<T>`:

```text id="g8d4w2"
WRITE
```

nhưng không đồng nghĩa:

```text id="r1f6q9"
writes every byte of T
```

Region/effect analysis phải giữ phạm vi chính xác nhất có thể.

---

# 14. Field-sensitive aliasing

Ví dụ:

```text id="p3k7v1"
struct S {
    a: i32,
    b: i32
}
```

Compiler biết:

```text id="c8m2x5"
s.a != s.b
```

về semantic storage region.

Do đó:

```text id="d7q1v8"
write(s.a)
read(s.b)
```

có thể reorder.

---

# 15. Array/slice aliasing

Khó hơn:

```text id="z6k3p9"
a[i]
a[j]
```

Nếu compiler chứng minh:

```text id="r4m8v2"
i != j
```

→ NoAlias.

Nếu không:

```text id="x1c7n5"
MAY_ALIAS
```

không được giả định disjoint.

---

# 16. Range Analysis

OptIR có:

```text id="w3n9k4"
RangeInfo
```

Ví dụ:

```axiom id="h6s2m8"
for i in 0..len {
    a[i] = ...
}
```

Compiler biết:

```text id="q8v5c1"
0 <= i < len
```

---

# 17. Bounds-check elimination

Nếu MIR ban đầu có:

```text id="p7m4x9"
CHECK(i < len)
LOAD(a[i])
```

range analysis chứng minh:

```text id="n2c8v6"
i < len
```

luôn đúng.

Optimizer xóa check.

Đây là một nguồn hiệu năng lớn.

---

# 18. Không dùng unchecked mặc định

Axiom không cần:

```text id="v4j8p2"
unsafe array indexing
```

cho code thông thường.

Compiler cố chứng minh bounds.

Chỉ khi programmer thật sự cần machine-level unchecked access:

```text id="s6k1m9"
unsafe
```

mới cần.

---

# 19. Scalar Replacement

Ví dụ:

```axiom id="c3f8q1"
let p = Point(1, 2);
print(p.x);
```

OptIR có thể biến:

```text id="a7n2v5"
p.x
p.y
```

thành:

```text id="m9c4k6"
%x = 1
%y = 2
```

không cần physical struct.

---

# 20. Allocation elimination

Ví dụ:

```axiom id="b8m3x7"
fn f() {
    let x = Box::new(Point(1,2));
    use(x);
}
```

Nếu:

```text id="j5q1c8"
address never escapes
```

optimizer có thể biến thành:

```text id="r4v9n2"
Point directly in registers/stack
```

Không allocation.

---

# 21. Ownership giúp allocation elimination

Compiler biết:

```text id="s2k7m5"
unique owner
no external alias
no address escape
```

→ có rất nhiều freedom để scalarize/move.

Đây là lý do ownership model không chỉ để safety.

> **Ownership là optimization information.**

---

# 22. Escape Analysis

OptIR sử dụng:

```text id="p9v3c6"
NoEscape
ReturnEscape
HeapEscape
ThreadEscape
ExternalEscape
UnknownEscape
```

Ví dụ:

```axiom id="w2h8k4"
fn make() -> Box<Data>
```

Nếu caller immediately consumes:

```text id="n5m1q7"
escape may be eliminated
```

---

# 23. Stack promotion

Allocation semantic:

```text id="x8c2v5"
ALLOC_DYNAMIC
```

nếu compiler chứng minh:

```text id="g4n7p1"
lifetime local
no escape
stable address not observed
```

có thể biến thành:

```text id="q3m9w6"
LOCAL_STORAGE
```

---

# 24. Caller allocation

Return:

```axiom id="e1r5k8"
fn create() -> BigStruct
```

không đồng nghĩa heap.

ABI lowering có thể:

```text id="v7c2n4"
caller provides result storage
callee initializes it
```

Đây là một optimization/ABI strategy rất quan trọng cho large structs.

---

# 25. Copy elimination

Source:

```axiom id="x9m3q7"
let b = a;
consume(b);
```

Nếu `a` là Copy:

```text id="z5k8v2"
semantic copy
```

nhưng optimizer có thể không tạo physical copy nếu:

```text id="q1c6n4"
value can be directly used
```

Semantic Copy ≠ machine copy.

---

# 26. Move elimination

Tương tự:

```text id="r8p2m5"
Move(a)
```

không cần physical memory movement.

Optimizer có thể rename SSA value.

---

# 27. Closure elimination

```axiom id="u4k9x2"
let f = |x| x + 1;
f(10);
```

Optimizer:

```text id="b6n3q8"
inline closure
↓
11
```

không:

```text id="j7c1v5"
heap environment
virtual call
```

---

# 28. Generic specialization

Generic:

```axiom id="q3w8n1"
fn sum<T: Add>(...)
```

sau specialization:

```text id="v5k2m7"
sum<i32>
```

có thể inline hoàn toàn.

---

# 29. Monomorphization không đồng nghĩa code explosion

Axiom đã frozen hybrid strategy.

Compiler có thể chọn:

```text id="p8r4c2"
monomorphize
```

hoặc:

```text id="m6x1n9"
share implementation
```

dựa trên:

- representation
- target
- specialization benefit
- code size
- hotness

---

# 30. Generic code sharing

Ví dụ:

```text id="h4c9z2"
T = u32
T = i32
```

nếu representation/effects đủ tương đương:

```text id="v7m1q5"
shared machine implementation
```

có thể dùng.

---

# 31. Inlining

Axiom compiler nên có cost model.

Không:

```text id="n9x3c6"
inline everything
```

Mà dựa trên:

```text id="k2v8m4"
size
hotness
call frequency
loop depth
branch count
code size budget
target
LTO
PGO
```

---

# 32. `@inline` là hint

`@inline` không nên biến thành:

> “Compiler bắt buộc inline.”

Nó là hint.

Tương tự:

```text id="x4p7n1"
@noinline
@cold
```

semantic/optimization policy được phân biệt.

---

# 33. Devirtualization

Nếu:

```text id="z8m2c5"
dyn Trait
```

nhưng compiler chứng minh concrete implementation duy nhất:

```text id="q6v1k9"
DynCall
 ↓
DirectCall
```

có thể xảy ra.

Nếu không chứng minh được:

```text id="a3r7w4"
dynamic dispatch remains
```

---

# 34. No implicit dynamic dispatch

Optimizer có thể **loại bỏ** dynamic dispatch.

Nhưng semantic frontend không được **tạo thêm** dynamic dispatch.

Điều này giữ performance predictable.

---

# 35. Constant folding

Ví dụ:

```axiom id="f1k6q9"
let x = 10 * 20;
```

OptIR:

```text id="z4m8p2"
x = 200
```

Không thay đổi semantics.

---

# 36. Compile-time và optimization khác nhau

`comptime`:

```text id="j2r7c5"
guaranteed compile-time execution
```

Optimizer folding:

```text id="w8n3m6"
compiler optimization
```

không được coi hai thứ là cùng semantic mechanism.

---

# 37. Dead Code Elimination

Nếu:

```text id="k5c1v8"
result never used
```

compiler loại bỏ computation nếu effects cho phép.

Ví dụ:

```text id="m7q2n4"
pure arithmetic → eliminate
```

nhưng:

```text id="p9x3c6"
IO
volatile
atomic
panic
synchronization
```

không được xóa tùy tiện.

---

# 38. Effect system cho optimizer

OptIR effect summary:

```text id="e2v7m5"
READ
WRITE
ALLOC
DEALLOC
DROP
ATOMIC
VOLATILE
IO
PANIC
SYNCHRONIZE
FOREIGN
SUSPEND
GPU
```

Optimizer sử dụng để biết operation có thể reorder/eliminate hay không.

---

# 39. CSE/GVN

Nếu:

```text id="a6m2x9"
x = a + b
y = a + b
```

và không có effect invalidating `a/b`:

```text id="r8c4v1"
y = x
```

---

# 40. Load CSE

Nếu:

```text id="q3n7k5"
x = load(a)
...
y = load(a)
```

và compiler chứng minh:

```text id="w1m9c6"
no write/alias invalidates a
```

→ reuse `x`.

Đây là nơi NoAlias facts cực kỳ hữu ích.

---

# 41. Store elimination

```text id="j5x2v8"
store(a, 1)
store(a, 2)
```

Nếu first store không observable:

```text id="m7c4q1"
store(a, 1)
```

có thể loại bỏ.

Nhưng volatile/atomic/foreign effects ngăn optimization phù hợp.

---

# 42. LICM

Loop:

```axiom id="z4p8m2"
for i in 0..n {
    x = expensive_constant();
    use(x);
}
```

Nếu `expensive_constant()` không có relevant effects:

```text id="k6r1v9"
move outside loop
```

---

# 43. Loop canonicalization

OptIR chuẩn hóa:

```text id="g2m7c5"
preheader
header
body
latch
exit
```

để các optimizer khác dễ làm việc.

---

# 44. Loop unrolling

Compiler có thể unroll khi:

```text id="n8q3x1"
trip count known/small
hot
code size acceptable
```

Không phải mặc định mọi loop.

---

# 45. Vectorization

Axiom có thể vectorize nếu:

```text id="p6k2v8"
no alias conflict
no dependency conflict
alignment known or handled
loop bounds valid
target SIMD available
```

Ownership/capability facts đặc biệt hữu ích ở đây.

---

# 46. Ví dụ lợi ích

```axiom id="h1m7c3"
fn add(
    a: view<f32>,
    b: view<f32>,
    out: mut_view<f32>
) {
    for i in 0..a.len {
        out[i] = a[i] + b[i];
    }
}
```

Compiler có thể chứng minh:

```text id="v9q4n2"
a READ
b READ
out WRITE
```

và nếu regions disjoint:

```text id="r5c8m1"
a != out
b != out
```

→ vectorization có thể an toàn.

Không cần:

```text
restrict
```

---

# 47. Ownership không phải phép màu

Nếu API:

```text id="x7n3p6"
fn add(a: mut_view<f32>, b: mut_view<f32>)
```

cho phép overlapping regions, compiler không tự giả định disjoint.

Performance guarantee chỉ đến từ **facts đã chứng minh**.

---

# 48. Branch optimization

Compiler có:

```text id="s4k8v2"
branch probability
range facts
constant condition
profile data
```

để:

- simplify
- invert
- merge
- reorder
- eliminate

---

# 49. PGO

Axiom hỗ trợ PGO:

```text id="q2m7x5"
build --profile=generate
build --profile=use
```

PGO cung cấp:

- hot functions
- branch probabilities
- call frequencies
- hot loops

Nhưng **không thay đổi semantic validity**.

---

# 50. LTO

LTO có thể:

```text id="f8n3c1"
inline across modules
devirtualize
specialize generics
DCE
merge constants
remove unused functions
```

Không yêu cầu source-level change.

---

# 51. Interprocedural analysis

Compiler có thể propagate:

```text id="v5q1m9"
NoAlias
ReadOnly
NoEscape
Pure-ish effects
Range
Cold/Hot
```

qua function boundary nếu proven.

---

# 52. Không cần `@pure`

Axiom không cần source annotation:

```text id="d2k8m4"
@pure
```

để optimizer biết function pure.

Compiler có thể derive effect summary.

Nếu function gọi:

```text id="a9v3x7"
IO
foreign unknown
volatile
```

thì summary phản ánh điều đó.

---

# 53. Effect inference

Ví dụ:

```axiom id="c7m2p9"
fn f(x: i32) -> i32 {
    x * 2
}
```

Compiler derive:

```text id="w1q5n8"
READ = none
WRITE = none
IO = none
PANIC = none
```

Một function:

```axiom id="n4k8v2"
fn f() {
    print("hello");
}
```

derive:

```text id="m6p1c9"
IO
```

---

# 54. Không dùng effect inference để thay đổi source semantics

Effect chỉ là compiler fact.

Programmer không phải quản lý effect system trong Core v1.

---

# 55. Allocation cost model

Compiler nên phân biệt:

```text id="p7m3x8"
semantic allocation
```

và:

```text id="k1q6v9"
physical allocation
```

Một semantic `ALLOC` có thể:

- stack
- register
- arena
- pool
- heap
- static
- device

---

# 56. Heap allocation không mặc định chậm

Compiler cost model nên dựa vào:

```text id="z3n8c5"
allocation count
size
escape
locality
contention
lifetime
fragmentation
```

chứ không có rule:

```text
heap = bad
```

---

# 57. Fragmentation

Axiom không hứa:

> flat memory model = zero fragmentation.

Đúng hơn:

```text id="s8m2v6"
flat address space
+
allocator strategy
+
object lifetime
+
allocation pattern
```

quyết định fragmentation.

Optimizer có thể chọn:

- arena
- slab
- pool
- stack
- inline

khi semantic contract cho phép.

---

# 58. Storage promotion

Compiler có thể:

```text id="j4r9w1"
heap → stack
heap → inline
heap → register
dynamic → arena
```

nếu observable semantics không thay đổi.

---

# 59. Observable address

Nếu programmer:

```axiom id="v6p2m8"
unsafe {
    let p = address_of(x);
}
```

thì physical address trở thành observable.

Optimizer không còn tự do relocate như trước.

Đây là một trong những điểm mà:

> **Unsafe làm giảm optimization freedom.**

---

# 60. Stable address contract

Nếu API yêu cầu:

```text id="q8c3n5"
stable address
```

compiler phải giữ storage ổn định.

Nhưng đây phải là explicit semantic requirement, không phải mọi object đều stable.

---

# 61. Optimization explanation

Để AI agent dễ làm việc, compiler nên có:

```text id="n5v1c7"
axiom explain opt foo
```

Ví dụ:

```text id="m8q3x2"
Allocation eliminated:
    reason = NoEscape
    address_observed = false
    lifetime = local
```

Hoặc:

```text id="c6r9p1"
Vectorization rejected:
    reason = MAY_ALIAS
    a ↔ out
    region relation = UNKNOWN
```

Đây sẽ rất hữu ích khi dùng Gemini/Claude/agent để tối ưu code.

---

# 62. Optimization remarks

Có thể xuất:

```text id="r2k7m4"
remark:
  inline
remark:
  vectorize
remark:
  allocation-eliminated
remark:
  bounds-check-eliminated
remark:
  devirtualized
remark:
  generic-specialized
```

machine-readable.

---

# 63. Debugging optimization

Mỗi OptIR transformation giữ:

```text id="p4x8c1"
OriginInstructionIds
SourceSpanIds
OptimizationPassId
Reason
```

Do đó debugger/compiler explorer có thể giải thích:

```text
source → MIR → OptIR → machine
```

---

# 64. Optimization legality

Mỗi pass phải có precondition.

Ví dụ:

```text id="s7m2q9"
VectorizeLoop
requires:
    no unsafe unknown alias
    valid iteration range
    no unsupported side effects
```

Nếu precondition không proven:

```text id="v3c8n1"
do not optimize
```

Không speculative UB.

---

# 65. Speculation

Axiom có thể hỗ trợ speculative optimization khi backend có deoptimization/guards trong tương lai.

Nhưng **Core native compiler v1 không cần JIT-style deoptimization**.

Native AOT optimizer ưu tiên proven transformations.

---

# 66. Target-independent vs target-aware

OptIR trước:

```text id="j9q4c2"
target-independent
```

sau đó target information được cung cấp:

```text id="x3m8v6"
TargetInfo {
    architecture
    word_size
    endian
    features
    vector_width
    cache hints
    ABI facts
}
```

để optimization phù hợp.

---

# 67. Không overfit x86

Axiom phải thiết kế optimizer để:

```text id="n7c2m5"
x86-64
ARM64
RISC-V
WASM
GPU
```

có semantic pipeline chung.

Target-specific lowering xảy ra sau.

---

# 68. Binary-size optimization

Do mục tiêu của bạn còn là binary nhỏ, optimizer phải có mode:

```text id="k1v6p8"
-Osize
```

và:

```text id="x4q9m2"
-Ospeed
-Obalanced
```

Không cần đổi language semantics.

---

# 69. `-Os` có thể ưu tiên

- code sharing
- no aggressive unrolling
- smaller inline threshold
- dead stripping
- constant merging
- section GC
- compact instruction selection

---

# 70. Runtime elimination

Do Axiom runtime modular:

```text id="z6p3c8"
program chỉ dùng:
    arithmetic
    String
```

không nên kéo vào:

```text
thread runtime
async executor
GC
reflection runtime
network runtime
```

Dead component elimination là một nguồn binary size reduction lớn.

---

# 71. Optimization invariants — `AOPT-20..`

### `AOPT-20`
Only Verified MIR enters optimization.

### `AOPT-21`
Optimization preserves observable program semantics.

### `AOPT-22`
Optimization is independent of source-level ownership annotations because ownership facts are compiler-derived.

### `AOPT-23`
Verified disjointness may be lowered to internal NoAlias facts.

### `AOPT-24`
Unknown aliasing is never treated as NoAlias.

### `AOPT-25`
Capability READ facts may enable read caching and load optimization when no invalidating effect exists.

### `AOPT-26`
Capability WRITE facts constrain memory reordering.

### `AOPT-27`
Ownership facts may enable scalar replacement and allocation elimination.

### `AOPT-28`
Move semantics do not require physical data movement.

### `AOPT-29`
Copy semantics do not require physical copying.

### `AOPT-30`
Clone remains an explicit semantic operation.

### `AOPT-31`
Allocation elimination is legal only when allocation-observable semantics are preserved.

### `AOPT-32`
Stable-address observation prevents invalid storage promotion or relocation.

### `AOPT-33`
Escape analysis may promote or eliminate storage.

### `AOPT-34`
Caller-allocated returns may replace physical return allocation.

### `AOPT-35`
Bounds checks may be removed only when range facts prove their conditions.

### `AOPT-36`
Atomic operations are not replaced by ordinary memory operations unless semantics explicitly permit it.

### `AOPT-37`
Volatile operations are not removed or reordered as ordinary memory operations.

### `AOPT-38`
Foreign calls are optimized conservatively according to their effect contracts.

### `AOPT-39`
Dynamic dispatch may be removed only when concrete target identity is proven.

### `AOPT-40`
Generic specialization must preserve generic semantics.

### `AOPT-41`
Code sharing is permitted only when representation and semantics remain equivalent.

### `AOPT-42`
Inlining is an optimization decision, not a semantic requirement.

### `AOPT-43`
PGO may influence optimization decisions but never semantic validity.

### `AOPT-44`
LTO may introduce cross-module optimizations without changing language semantics.

### `AOPT-45`
Effect information constrains elimination and reordering.

### `AOPT-46`
Optimization does not introduce mandatory runtime services.

### `AOPT-47`
Optimization may erase compiler-only capability metadata after all required verification.

### `AOPT-48`
OptIR is not required to preserve source-level syntax.

### `AOPT-49`
MIR remains the semantic source of truth.

### `AOPT-50`
SSA construction does not redefine ownership semantics.

### `AOPT-51`
MemorySSA does not redefine the language memory model.

### `AOPT-52`
Alias analysis may only use proven facts.

### `AOPT-53`
Optimization diagnostics must be explainable.

### `AOPT-54`
Optimization results are deterministic under the same optimization configuration and compiler semantic version.

### `AOPT-55`
Optimization passes must declare or encode their semantic preconditions.

### `AOPT-56`
A failed optimization proof results in no transformation rather than an unsafe assumption.

### `AOPT-57`
Target-specific optimization must preserve target-independent semantics.

### `AOPT-58`
Binary-size optimization must not require a monolithic runtime.

### `AOPT-59`
Unobservable allocations may be eliminated.

### `AOPT-60`
Unobservable closure environments may be eliminated.

### `AOPT-61`
Unobservable copies may be eliminated.

### `AOPT-62`
Unobservable moves may be lowered as value renaming.

### `AOPT-63`
Optimization may reorder operations only when effect and memory-ordering constraints permit it.

### `AOPT-64`
Optimization must preserve panic, Drop, synchronization, atomic, volatile, FFI, GPU, and async semantics.

### `AOPT-65`
Optimization must preserve source-to-machine debug provenance.

---

# Một điểm rất quan trọng đã được khóa

Sau 107, ta có một chuỗi cực kỳ đẹp:

```text id="h6q2m8"
Ownership
    ↓
Capability
    ↓
Verification
    ↓
NoAlias / ReadOnly / Escape facts
    ↓
Optimization
    ↓
Vectorization / allocation elimination / load-store optimization
```

Tức là **cùng một hệ thống ownership/capability vừa đảm bảo safety vừa tạo performance information**.

Đây chính là cách tránh tình trạng:

> “Muốn nhanh thì phải viết unsafe / restrict / pointer tricks.”

Trong Axiom, mục tiêu là:

> **Safe code tự nhiên đã cung cấp cho compiler càng nhiều optimization facts càng tốt.**

---

# BOOTSTRAP-108 — ABI Lowering & Physical Representation

Bước tiếp theo là một boundary rất quan trọng:

```text id="3j4n8p"
Optimized OptIR
      ↓
Representation Lowering
      ↓
Layout
      ↓
Calling Convention
      ↓
Argument/Return Classification
      ↓
Drop ABI
      ↓
FFI ABI
      ↓
ABI MIR
```

Ở đây cần khóa chính xác:

- struct được truyền bằng register hay memory;
- large return value;
- caller/callee allocated return;
- `view<T>` physical representation;
- `mut_view<T>`;
- `dyn Trait`;
- closure;
- enum/niche layout;
- Option optimization;
- alignment;
- padding;
- `@repr(C)`;
- C ABI;
- System ABI;
- variadic;
- TLS;
- exported functions;
- symbol naming;
- how Axiom keeps **zero-cost semantic abstractions** while still producing conventional native ABI.

Đây cũng là bước bắt đầu biến:

> **“Axiom semantics” → “machine-visible binary contract”**.