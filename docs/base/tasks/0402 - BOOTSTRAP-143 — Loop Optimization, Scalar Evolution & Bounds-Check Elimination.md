# BOOTSTRAP-143 — Loop Optimization, Scalar Evolution & Bounds-Check Elimination

**Trạng thái: FROZEN / COMPLETED**

Đây là tầng biến Axiom từ một ngôn ngữ có semantics mạnh thành một compiler có khả năng khai thác **vòng lặp rất sâu** mà không bắt programmer quay lại pointer arithmetic hoặc `unsafe`.

Mục tiêu:

> **Safe code phải có khả năng đạt machine code tương đương với low-level hand-optimized code khi compiler có đủ proof.**

Không có nghĩa mọi loop luôn nhanh hơn C/C++; mà là **Axiom không tự tạo overhead chỉ vì programmer dùng abstraction an toàn**.

---

## 1. Vị trí trong pipeline

```text id="loop143"
Verified MIR
    ↓
SSA + MemorySSA
    ↓
AliasInfo
RangeInfo
EscapeInfo
EffectInfo
    ↓
Loop Discovery
    ↓
Loop Canonicalization
    ↓
Induction Analysis
    ↓
Scalar Evolution
    ↓
Range / Bounds Analysis
    ↓
Loop Optimization
    ↓
Vectorization
    ↓
Optimized OptIR
```

---

# 2. Loop representation

Compiler tạo:

```text id="loopgraph"
LoopInfo {
    LoopId
    Header
    Preheader
    Latches
    ExitBlocks
    NestedLoops
    BackEdges
    TripCount
    InductionVariables
}
```

Loop phải được xác định từ CFG chứ không từ syntax `for`.

Do đó:

```ax
for ...
```

```ax
while ...
```

```ax
loop ...
```

sau lowering đều có thể trở thành cùng một dạng loop IR.

---

# 3. Natural loop

Ví dụ:

```ax id="ex143a"
let mut i = 0;

while i < n {
    work(i);
    i += 1;
}
```

Compiler nhận diện:

```text id="natural"
header
   ↓
body
   ↓
latch
   └────→ header
```

---

# 4. Loop preheader

Compiler cố gắng canonicalize thành:

```text id="preheader"
Preheader
    ↓
Header
    ↓
Body
    ↓
Latch
    └──→ Header
```

Invariant loop-invariant computation có thể được đưa ra preheader.

---

# 5. Loop canonicalization

Compiler chuẩn hóa:

```text id="canon"
induction variable
loop condition
latch update
exit condition
```

về dạng dễ phân tích.

Không làm thay đổi source semantics.

---

# 6. Induction variable

Ví dụ:

```ax id="ind"
for i in 0..n {
    ...
}
```

Compiler nhận:

```text id="indinfo"
i₀ = 0
step = 1
upper = n
```

Đây là **canonical induction variable**.

---

# 7. Derived induction variable

Ví dụ:

```ax id="derived"
j = i * 4
```

Compiler có thể suy ra:

```text id="derived2"
j₀ = 0
step = 4
```

rất hữu ích cho indexing và address calculation.

---

# 8. Scalar Evolution

Axiom cần một subsystem:

```text id="scev"
ScalarEvolution
```

mô tả giá trị scalar qua iterations.

Ví dụ:

```text id="scev2"
i = 0 + iteration * 1
j = base + iteration * 4
```

---

# 9. Trip count

Compiler cố gắng chứng minh:

```text id="trip"
iterations = n
```

hoặc:

```text id="trip2"
iterations = max(0, n - start)
```

Nếu không chứng minh được chính xác:

```text id="trip3"
unknown / symbolic
```

vẫn có thể optimize.

---

# 10. Không được giả định overflow sai

Đây là điểm quan trọng với Axiom.

Axiom đã quyết định integer overflow có semantics xác định.

Vì vậy compiler **không được tự động giả định**:

```text id="overflowbad"
i + 1 > i
```

nếu semantics của kiểu cho phép wrap.

Scalar Evolution phải biết:

```text id="overflowaware"
checked
wrapping
saturating
```

---

# 11. Loop induction với wrapping

Nếu:

```ax
var i: u32 = 0;
```

thì:

```text id="wrap"
i + 1
```

có thể wrap.

Compiler không được suy ra vô điều kiện:

```text i < i + 1
```

---

# 12. Range analysis

Axiom dùng:

```text id="range"
RangeInfo {
    Min
    Max
    Signedness
    KnownBits
    Relations
}
```

Ví dụ:

```ax
if i < n {
    a[i]
}
```

ta có:

```text
0 ≤ i < n
```

nếu `i` đã được chứng minh không âm.

---

# 13. Bounds-check elimination

Đây là optimization rất quan trọng.

Source:

```ax id="bounds"
for i in 0..n {
    out[i] = a[i] + b[i];
}
```

Mỗi:

```text
a[i]
b[i]
out[i]
```

về semantic level đều có bounds requirement.

Nhưng compiler chứng minh:

```text
0 ≤ i < n
```

và:

```text
len(a) ≥ n
len(b) ≥ n
len(out) ≥ n
```

→ bounds checks có thể biến mất.

---

# 14. Đây không phải `unsafe`

Programmer vẫn viết safe code:

```ax
for i in 0..n {
    ...
}
```

Compiler tự chứng minh.

Nếu proof thất bại:

```text id="boundsfail"
bounds check remains
```

Không chuyển code sang unsafe.

---

# 15. Range relation

Compiler giữ các quan hệ:

```text id="rel"
i < n
j <= i
k = i + c
len(a) = n
```

để chứng minh safety và optimization.

---

# 16. Loop-carried range

Ví dụ:

```ax id="looprange"
var i = 0;
while i < n {
    ...
    i += 1;
}
```

sau mỗi iteration:

```text id="range2"
0 ≤ i ≤ n
```

và trước body:

```text id="range3"
0 ≤ i < n
```

---

# 17. Dominance-based bounds proof

Nếu:

```ax
if i < n {
    use(i);
}
```

và block `use` chỉ reachable qua branch true:

```text id="dom"
i < n
```

dominates access.

→ check có thể được dùng làm proof.

---

# 18. Check hoisting

Nếu check không thể eliminate hoàn toàn:

```ax
for i in 0..n {
    a[i]
}
```

compiler có thể chuyển từ:

```text
check mỗi iteration
```

thành:

```text
check một lần trước loop
```

nếu semantics cho phép.

---

# 19. Check sinking

Ngược lại, check có thể được đẩy gần access nếu điều đó giảm speculative work mà không thay đổi observable behavior.

---

# 20. Loop-invariant code motion

Ví dụ:

```ax
for i in 0..n {
    y = expensive_constant();
    ...
}
```

Nếu `expensive_constant()`:

```text id="licm"
Pure
No external effects
No dependency on i
```

→ đưa ra ngoài loop.

---

# 21. Không LICM function có effect

Nếu:

```ax
read_clock()
```

thì không thể giả định:

```text
same value every iteration
```

vì `Time`/external state là observable.

---

# 22. Alias + LICM

Ví dụ:

```ax id="aliaslicm"
for i in 0..n {
    x = a[i];
    y = invariant_field;
}
```

Nếu compiler không chứng minh loop không ghi `invariant_field`:

```text
→ không hoist.
```

AliasInfo + EffectInfo quyết định legality.

---

# 23. Store-to-load

Nếu:

```ax
a[i] = x;
y = a[i];
```

và không có intervening write/alias:

```text id="stl"
y = x
```

MemorySSA chứng minh defining store.

---

# 24. Loop-invariant load

Nếu load:

```text id="load"
*p
```

không bị loop writes/clobbers:

```text id="load2"
hoist load
```

nhưng chỉ khi AliasInfo + MemorySSA + EffectInfo chứng minh.

---

# 25. Unknown alias

Nếu:

```text id="unknownalias"
foreign_call()
```

có thể sửa memory:

```text id="conservative"
```

không được hoist load qua call nếu semantics không cho phép.

---

# 26. Loop unswitching

Ví dụ:

```ax id="unswitch"
for i in 0..n {
    if fast_mode {
        fast(i);
    } else {
        slow(i);
    }
}
```

Nếu `fast_mode` loop-invariant:

```text id="unswitch2"
if fast_mode {
    loop fast
} else {
    loop slow
}
```

Có thể loại branch khỏi mỗi iteration.

---

# 27. Code-size control

Loop unswitching có thể duplicate code.

Vì vậy CostModel:

```text id="unswitchcost"
BranchCost
CodeGrowth
LoopHotness
TripCount
VectorizationBenefit
```

---

# 28. Loop peeling

Compiler có thể tách vài iteration đầu:

```text id="peel"
prologue
main loop
```

để tạo điều kiện:

- alignment;
- vectorization;
- bounds proof;
- branch simplification.

---

# 29. Loop versioning

Khi compiler chưa biết:

```text id="version"
a và b có overlap không?
```

có thể tạo:

```text
if runtime_condition {
    optimized_loop
} else {
    generic_loop
}
```

Runtime check chỉ là **optimization guard**.

---

# 30. Runtime guard không thay safety proof

Nếu code safe yêu cầu:

```text id="safety"
bounds valid
```

thì compiler vẫn phải chứng minh safety.

Runtime versioning chỉ quyết định chọn implementation tối ưu nào.

---

# 31. Alias versioning

Ví dụ:

```text id="aliasversion"
if addresses_do_not_overlap {
    vectorized path
} else {
    safe generic path
}
```

Nếu điều kiện false, generic path vẫn phải đúng.

---

# 32. Vectorization

Loop:

```ax id="vector"
for i in 0..n {
    out[i] = a[i] + b[i];
}
```

có thể thành:

```text id="vec"
vector load
vector add
vector store
```

---

# 33. Vectorization legality

Compiler phải kiểm tra:

```text id="veclaw"
memory dependence
alias
side effects
ordering
atomicity
volatile
exceptions/panic
```

---

# 34. Vectorization và capability

Nếu:

```text id="cap"
a: view<f32>
b: view<f32>
out: mut_view<f32>
```

và verifier/alias analysis chứng minh:

```text id="cap2"
a ∩ out = ∅
b ∩ out = ∅
```

thì vectorization rất thuận lợi.

---

# 35. Unknown overlap

Nếu overlap unknown:

```text id="unknown"
```

compiler không được tự biến thành NoAlias.

Có thể:

```text id="version2"
runtime alias check
```

nếu profitable.

---

# 36. Reduction recognition

Ví dụ:

```ax
var sum = 0.0;

for x in data {
    sum += x;
}
```

Compiler có thể nhận:

```text id="reduction"
Reduction {
    operator = add
    identity = 0
}
```

---

# 37. Floating-point reduction

Không được tự ý reassociate:

```text id="fp"
(a + b) + c
```

thành:

```text
a + (b + c)
```

nếu configured FP semantics không cho phép.

Fast-math/relaxed FP phải là explicit compilation mode/contract nếu muốn.

---

# 38. Integer reduction

Integer reduction có semantics overflow xác định.

Compiler phải bảo toàn:

```text id="integersem"
checked
wrapping
saturating
```

đã chọn.

---

# 39. Parallel reduction

GPU/SIMD/thread parallel reduction chỉ được thực hiện nếu semantics cho phép thứ tự thay đổi.

Đặc biệt:

```text id="parallel"
observable ordering
atomic semantics
FP semantics
```

phải được giữ.

---

# 40. Loop interchange

Nested loop:

```text id="interchange"
for i ...
    for j ...
```

có thể đổi:

```text
for j ...
    for i ...
```

nhưng chỉ khi memory dependencies và observable effects cho phép.

---

# 41. Loop fusion

Hai loop:

```text id="fusion"
for i { A[i] }
for i { B[i] }
```

có thể fusion:

```text
for i {
    A[i]
    B[i]
}
```

nếu:

- ordering preserved;
- dependencies safe;
- effects preserved;
- code-size/profitability phù hợp.

---

# 42. Loop distribution

Ngược lại:

```text id="distribution"
for i {
    A[i];
    B[i];
}
```

có thể tách nếu điều đó cải thiện vectorization/cache/parallelism.

---

# 43. Loop unrolling

Compiler có thể biến:

```text id="unroll"
for i ...
```

thành nhiều iteration trong body.

Nhưng phải kiểm soát:

```text
code size
register pressure
instruction cache
trip count
```

---

# 44. Partial unrolling

Nếu trip count unknown:

```text id="partial"
```

có thể:

```text
main unrolled loop
+
remainder loop
```

---

# 45. Full unrolling

Nếu:

```ax
for i in 0..4
```

compiler biết chính xác:

```text id="full"
trip_count = 4
```

có thể full-unroll.

---

# 46. Compile-time arrays

Ví dụ:

```ax
const N = 4;

for i in 0..N {
    ...
}
```

`N` có thể được constant-fold trước loop optimization.

---

# 47. Bounds-check elimination sau unrolling

Unrolling thường tạo thêm proof:

```text id="unrollbounds"
i
i+1
i+2
i+3
```

RangeInfo phải theo từng lane/access.

---

# 48. Induction variable elimination

Nếu:

```text id="iv"
i
```

chỉ được dùng để tính address:

```text
a[i]
```

target backend có thể chuyển thành pointer/address induction internally mà không expose pointer semantics cho programmer.

---

# 49. Đây rất phù hợp với triết lý Axiom

Source:

```ax
a[i]
```

OptIR:

```text
base + scaled_index
```

Machine IR:

```text
[target addressing mode]
```

Programmer không cần viết:

```c
*(base + i)
```

---

# 50. Strength reduction

Ví dụ:

```text id="strength"
i * 4
```

có thể trở thành:

```text
increment address by 4
```

nếu target/loop structure phù hợp.

---

# 51. Address evolution

Compiler có thể duy trì:

```text id="addr"
addr₀ = base
addr_next = addr + stride
```

thay vì tính:

```text base + i * stride
```

mỗi iteration.

---

# 52. Target-aware loop optimization

Loop optimizer nhận:

```text id="target"
TargetInfo {
    SIMDWidth
    VectorRegisters
    CacheHints
    AddressingModes
    BranchCost
    GatherCost
    FMA
}
```

---

# 53. x86-64

Có thể tận dụng:

```text
AVX2
AVX-512
FMA
scaled addressing
```

nếu target feature cho phép.

---

# 54. AArch64

Có thể tận dụng:

```text
NEON
SVE/SVE2
scaled addressing
```

theo target configuration.

---

# 55. RISC-V

Vectorization phải phụ thuộc:

```text
RVV
```

và vector length semantics.

---

# 56. GPU

Loop optimizer có thể chuyển loop phù hợp thành:

```text
thread-level parallelism
SIMT
vector operations
```

nhưng GPU legality vẫn là subsystem riêng.

---

# 57. Async loop

Nếu loop chứa:

```ax
await foo();
```

thì đây không còn là ordinary tight loop.

Compiler phải giữ:

```text id="async"
suspension points
state fields
wake semantics
```

không được LICM qua await nếu semantics thay đổi.

---

# 58. Panic trong loop

Nếu body có:

```ax
panic(...)
```

compiler phải giữ khả năng panic và cleanup semantics.

Không được xem branch là dead chỉ vì profile.

---

# 59. Drop trong loop

Ví dụ:

```ax
for x in values {
    consume(x);
}
```

Drop của `x` phải được bảo toàn.

Optimizer có thể:

```text
eliminate trivial drop
```

nhưng không thể bỏ observable destructor.

---

# 60. Drop + vectorization

Nếu element có custom Drop:

```text id="dropvec"
```

vectorization chỉ được thực hiện khi compiler có thể giữ đúng destruction order/semantics.

---

# 61. Effectful iteration

Nếu:

```ax
for x in data {
    write_log(x);
}
```

compiler không được reorder các observable calls chỉ để vectorize.

---

# 62. Atomic loop

```ax
for x in data {
    atomic_add(counter, x);
}
```

không được biến thành ordinary reduction nếu làm thay đổi atomic semantics.

---

# 63. Volatile loop

```text id="volatile"
volatile_load()
```

phải giữ:

```text ordering
number of accesses
observable access semantics
```

Không được CSE/eliminate như ordinary load.

---

# 64. Memory fence

Loop chứa:

```text id="fence"
CPU fence
```

không được reorder memory operations qua fence nếu làm thay đổi memory model.

---

# 65. Bounds-check proof và safety boundary

Điểm quan trọng:

```text id="safetyboundary"
Safety verifier:
    Is a[i] legal?

Loop optimizer:
    Can the proof remove the check?
```

Optimizer **không tự quyết định safety**.

---

# 66. Nếu proof thất bại

Axiom không:

```text
→ assume safe
```

mà:

```text
→ retain check
```

Đây là một property cực kỳ quan trọng của ngôn ngữ.

---

# 67. Optimization không thay đổi semantics

Ví dụ:

```text id="semantics"
-O0:
    bounds check

-O3:
    no bounds check
```

Hai chương trình phải có cùng observable behavior đối với valid source execution.

---

# 68. Debug build

`-O0` vẫn phải sử dụng semantics chính xác.

Không được dựa vào optimization để “làm code đúng”.

---

# 69. Diagnostics

Compiler có thể cung cấp:

```text id="diag"
axc inspect loop foo
```

Ví dụ:

```text
Loop #3

Trip count:
    symbolic n

Induction:
    i = 0..n-1

Bounds:
    a[i] proven safe
    b[i] proven safe
    out[i] proven safe

Vectorization:
    yes

Alias:
    out disjoint from a
    out disjoint from b
```

---

# 70. AI-readable optimization explanation

```text id="explain"
axc explain optimization foo --loop=3
```

có thể trả:

```text
BCE:
    eliminated 3 checks
Reason:
    i ∈ [0,n)
    len(a) ≥ n
    len(b) ≥ n
    len(out) ≥ n

Vectorization:
    width = 8
    reason = no conflicting writes
```

---

# 71. Không expose pointer tricks

AI/programmer không cần yêu cầu:

```text
restrict
unsafe pointer
manual SIMD
manual prefetch
```

để đạt optimization cơ bản.

Nếu cần explicit hardware control, system layer vẫn có thể cung cấp.

---

# 72. Prefetch

Compiler có thể tự chèn prefetch nếu target/profile chứng minh lợi ích.

Nhưng prefetch không được trở thành semantic requirement.

---

# 73. Cache-aware optimization

Loop optimizer có thể sử dụng:

```text
working-set estimate
stride
reuse distance
nested-loop structure
```

để quyết định interchange/tiling.

---

# 74. Loop tiling

Ví dụ matrix operation:

```text id="tile"
for i ...
    for j ...
```

có thể tile:

```text id="tile2"
for ii in tiles
    for jj in tiles
        for i in tile
            for j in tile
```

nếu semantics cho phép.

---

# 75. Matrix/tensor library

Axiom standard/GPU libraries có thể cung cấp high-level:

```ax
matmul(A, B, C);
```

Compiler có thể:

```text id="mat"
inline
→ loop recognition
→ tiling
→ vectorization
→ target instruction selection
```

hoặc nhận dạng intrinsic/library semantic operation.

---

# 76. Loop idiom recognition

Compiler có thể nhận dạng:

```text
memcpy
memset
search
reduce
min/max
count
copy
compare
```

và lower thành target-optimized implementation.

---

# 77. Không hard-code library implementation

Semantic optimization nên nhận dạng **operation semantics**, không phụ thuộc implementation source cụ thể.

---

# 78. Loop optimizer và ownership

Move trong loop:

```ax
for x in values {
    consume(x);
}
```

không được biến thành Copy.

Ownership state vẫn do verifier xác định.

---

# 79. Capability validity

Nếu active `view`/`mut_view` ngăn relocation:

```text id="capreloc"
```

loop transformation không được làm allocation relocate.

---

# 80. Các invariants đã khóa

### `ALOOP-20`
Loop transformations preserve observable semantics.

### `ALOOP-21`
Loop discovery is CFG-based.

### `ALOOP-22`
Loop canonicalization preserves semantics.

### `ALOOP-23`
Induction variables are compiler facts, not source-level ownership constructs.

### `ALOOP-24`
Scalar Evolution respects Axiom integer overflow semantics.

### `ALOOP-25`
Wrapping arithmetic cannot be treated as mathematical unbounded arithmetic without proof.

### `ALOOP-26`
Trip counts require valid proofs.

### `ALOOP-27`
Unknown trip counts remain conservative.

### `ALOOP-28`
Range analysis is distinct from ownership verification.

### `ALOOP-29`
Range facts may be consumed by optimization only after validity is established.

### `ABCE-20`
Bounds-check elimination requires proof of bounds validity.

### `ABCE-21`
Failure to prove bounds validity retains the required check.

### `ABCE-22`
Optimization never converts an unsafe access into a safe access by assumption.

### `ABCE-23`
Dominating range facts may establish bounds validity.

### `ABCE-24`
Loop induction facts may establish bounds validity.

### `ABCE-25`
Array/view lengths are semantic facts.

### `ABCE-26`
Adjacent half-open ranges are disjoint.

### `ABCE-27`
Unknown dynamic index relations are never assumed disjoint.

### `ALICM-20`
Loop-invariant code motion requires effect and dependency proof.

### `ALICM-21`
Observable external state prevents invalid hoisting.

### `ALICM-22`
Alias uncertainty prevents unsafe hoisting.

### `ALICM-23`
MemorySSA must validate load/store dependencies.

### `ALICM-24`
Atomic and volatile operations remain observable according to their semantics.

### `AVEC-20`
Vectorization requires memory-dependence legality.

### `AVEC-21`
Compiler-proven capability disjointness may enable vectorization.

### `AVEC-22`
Unknown aliasing cannot be treated as NoAlias.

### `AVEC-23`
Vectorization preserves atomic semantics.

### `AVEC-24`
Vectorization preserves volatile semantics.

### `AVEC-25`
Vectorization preserves floating-point semantics unless relaxed semantics are explicitly enabled.

### `AVEC-26`
Reduction transformations preserve the semantics of the reduction operator.

### `ALOOP-29`
Loop transformations must preserve Drop semantics.

### `ALOOP-30`
Loop transformations must preserve ownership semantics.

### `ALOOP-31`
Loop transformations must preserve capability validity.

### `ALOOP-32`
Loop transformations cannot invalidate stable-address contracts.

### `ALOOP-33`
Loop transformations cannot weaken synchronization semantics.

### `ALOOP-34`
Loop transformations respect async suspension boundaries.

### `ALOOP-35`
Loop transformations respect GPU execution/storage domains.

### `ALOOP-36`
Loop transformations respect FFI/foreign effects.

### `ALOOP-37`
Runtime optimization guards are not safety proofs.

### `ALOOP-38`
Optimization guards must retain a semantically correct fallback.

### `ALOOP-39`
Loop versioning cannot change observable behavior.

### `ALOOP-40`
Loop fusion requires dependency legality.

### `ALOOP-41`
Loop distribution requires dependency legality.

### `ALOOP-42`
Loop interchange requires dependency legality.

### `ALOOP-43`
Loop unrolling is bounded by code-size/resource policy.

### `ALOOP-44`
Loop peeling preserves iteration semantics.

### `ALOOP-45`
Loop unswitching preserves branch effects.

### `ALOOP-46`
Reduction reassociation requires operator/FP legality.

### `ALOOP-47`
Integer strength reduction preserves overflow semantics.

### `ALOOP-48`
Address evolution is an optimizer representation, not a programmer-visible pointer semantic.

### `ALOOP-49`
Target-specific loop transformations respect target feature availability.

### `ALOOP-50`
Optimization level cannot alter program semantics.

### `ALOOP-51`
Debug and release builds share the same semantic rules.

### `ALOOP-52`
Loop optimization may consume AliasInfo, EffectInfo, EscapeInfo, RangeInfo and MemorySSA.

### `ALOOP-53`
Loop optimization cannot create safety proofs.

### `ALOOP-54`
Loop optimization cannot weaken existing safety proofs.

### `ALOOP-55`
Failed optimization proofs reduce optimization opportunity rather than program validity.

### `ALOOP-56`
Loop analyses are deterministic.

### `ALOOP-57`
Independent loop analyses may run in parallel.

### `ALOOP-58`
Loop analysis is incrementally cacheable.

### `ALOOP-59`
Loop transformations preserve source provenance.

### `ALOOP-60`
AI/compiler tooling can explain loop optimization decisions.

### `ALOOP-61`
Compiler-generated loop transformations must remain verifiable.

### `ALOOP-62`
No optimization may introduce mandatory runtime ownership machinery.

### `ALOOP-63`
Safe array/view indexing may compile to unchecked machine addressing when bounds validity is proven.

### `ALOOP-64`
Eliminated bounds checks are an optimization consequence, not a semantic relaxation.

### `ALOOP-65`
Vectorized safe code must remain semantically equivalent to its scalar form.

### `ALOOP-66`
Parallelization requires explicit semantic permission when ordering is observable.

### `ALOOP-67`
Atomic operations cannot be silently converted into ordinary operations.

### `ALOOP-68`
Volatile operations cannot be silently eliminated or reordered.

### `ALOOP-69`
Observable Drop ordering cannot be changed by loop optimization.

### `ALOOP-70`
Verified MIR remains the ultimate safety/semantic authority.

---

# Một kết quả rất quan trọng của BOOTSTRAP-143

Axiom giờ có thể hướng tới trường hợp:

```ax
fn add_arrays(
    a: view<f32>,
    b: view<f32>,
    out: mut_view<f32>
) {
    for i in 0..out.len() {
        out[i] = a[i] + b[i];
    }
}
```

Compiler có thể suy luận:

```text
ownership      ✓
capability     ✓
bounds         ✓
alias          ✓
range          ✓
loop           ✓
vectorization  ✓
```

và cuối cùng tạo:

```text
vector load a
vector load b
vector add
vector store out
```

**không cần pointer, `restrict`, bounds-check runtime hay unsafe trong source.**

Đây chính là một trong những điểm mà thiết kế `view/mut_view + compiler alias analysis + range analysis` của Axiom bắt đầu phát huy tác dụng rất rõ.

---

# BOOTSTRAP-144 — SIMD, Vector Types & Auto-Vectorization Engine

Task kế tiếp nên đi sâu hơn vào SIMD thay vì chỉ coi vectorization là một pass của loop.

Sẽ khóa:

```text
Scalar Types
      ↓
Vector Types
      ↓
Vector ABI
      ↓
SIMD Operations
      ↓
Mask/Predicate
      ↓
Horizontal Reduction
      ↓
Auto-Vectorization
      ↓
SLP Vectorization
      ↓
Loop Vectorization
      ↓
Target ISA
      ↓
AVX2 / AVX-512 / NEON / SVE / RVV
```

Đặc biệt cần quyết định một vấn đề quan trọng của Axiom: **SIMD có phải type primitive trong Core hay nên là compiler/library abstraction để Core vẫn sạch nhưng vẫn đạt performance?**