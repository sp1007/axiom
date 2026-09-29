# BOOTSTRAP-144 — SIMD, Vector Types & Auto-Vectorization Engine

**Trạng thái: FROZEN / COMPLETED**

Đây là bước hoàn thiện phần vector/SIMD của Axiom. Có một quyết định kiến trúc quan trọng:

> **SIMD không nên trở thành một đống type và intrinsic gắn cứng vào ISA trong Core.**

Axiom nên có **vector semantic types ở mức ngôn ngữ/compiler**, còn ISA-specific details nằm ở compiler backend + `std::simd`/`std::arch` tương ứng.

Như vậy vừa giữ được ngôn ngữ sạch, vừa cho phép khai thác AVX2/AVX-512/NEON/SVE/RVV.

---

# 1. Kiến trúc được chọn

```text
                    Axiom Scalar
                         │
                         ▼
                  Vector Semantics
                         │
              ┌──────────┴──────────┐
              │                     │
       Auto-vectorization      Explicit SIMD API
              │                     │
              └──────────┬──────────┘
                         ▼
                   Vector OptIR
                         │
                         ▼
                 Target Legalization
                         │
          ┌──────────────┼──────────────┐
          ▼              ▼              ▼
        AVX2           NEON            RVV
        AVX-512        SVE/SVE2        ...
```

---

# 2. Không đưa AVX vào Core

Không nên có:

```ax
avx256_f32
avx512_f32
neon_f32
```

trong Core.

Lý do:

- ISA thay đổi;
- architecture-specific;
- khó portable;
- làm Core phình to;
- ABI trở nên phức tạp;
- generic code khó tái sử dụng.

---

# 3. Vector semantic type

Axiom vẫn cần khái niệm vector ở compiler IR:

```text
Vector<T, N>
```

với semantics:

```text
N lanes
element type T
lane-wise operation
```

Đây là **semantic vector**, không phải “AVX register”.

---

# 4. Core hay std?

Đề xuất:

### Core biết:

```text
Vector semantic category
```

### `std` cung cấp:

```text
std::simd
```

### `std::arch` cung cấp:

```text
target-specific intrinsics
```

Compiler nhận diện cả hai.

---

# 5. Vì sao không để SIMD hoàn toàn trong std?

Nếu hoàn toàn opaque library:

```ax
std::simd::add(...)
```

compiler vẫn có thể optimize, nhưng sẽ khó đảm bảo rằng vector semantics được biểu diễn xuyên:

```text
HIR
MIR
OptIR
ABI
LIR
```

Vì vậy **compiler phải hiểu semantic vector operations**.

---

# 6. Vector semantic operations

OptIR hỗ trợ:

```text
VAdd
VSub
VMul
VDiv
VMin
VMax
VAbs
VSqrt
VFma
VAnd
VOr
VXor
VShift
VCmp
VSelect
VLoad
VStore
```

Không phải mọi operation đều tồn tại cho mọi type.

---

# 7. Lane semantics

Ví dụ:

```text
[a,b,c,d] + [e,f,g,h]
```

có semantic:

```text
[a+e, b+f, c+g, d+h]
```

---

# 8. Vector type identity

Vector identity gồm:

```text
ElementType
LaneCount
SemanticMode
```

Không gồm:

```text
AVX
NEON
SSE
```

ISA là target property.

---

# 9. Fixed-width vector

Có thể hỗ trợ:

```text
Vector<f32, 4>
Vector<f32, 8>
Vector<i32, 8>
```

để viết algorithm SIMD rõ ràng.

---

# 10. Scalable vector

Đối với:

- ARM SVE;
- RISC-V RVV;

lane count vật lý có thể không cố định.

Do đó Axiom cần semantic:

```text
ScalableVector<T>
```

ở tầng SIMD API/IR.

---

# 11. Không ép programmer biết vector register

Programmer có thể viết:

```ax
for x in simd_chunks(data) {
    ...
}
```

Compiler quyết định:

```text
128-bit
256-bit
512-bit
SVE
RVV
```

---

# 12. Portable SIMD

`std::simd` nên có abstraction:

```text
Simd<T, N>
Mask<N>
```

nhưng implementation có thể target-specific.

---

# 13. Auto-vectorization vẫn là đường mặc định

Programmer không cần viết SIMD:

```ax
for i in 0..n {
    out[i] = a[i] + b[i];
}
```

Compiler tự:

```text
scalar loop
    ↓
vector dependence analysis
    ↓
vector loop
```

---

# 14. Explicit SIMD

Khi cần kiểm soát chính xác:

```ax
let x: Simd<f32, 8> = ...;
```

Compiler phải giữ semantics explicit.

---

# 15. Explicit SIMD không đồng nghĩa ISA

`Simd<f32, 8>` không đảm bảo:

```text
AVX2
```

Có thể lower thành:

```text
AVX2
AVX-512
multiple SSE operations
scalar fallback
```

tùy target.

---

# 16. Target-specific intrinsic

Nếu programmer thực sự cần instruction cụ thể:

```text
std::arch::x86::...
std::arch::arm::...
std::arch::riscv::...
```

được phép ở system layer.

Đây là nơi chứa:

```text
_mm256_...
sv...
v...
```

tương đương.

---

# 17. Unsafe boundary

ISA-specific intrinsic có thể là:

```text
unsafe
```

nếu yêu cầu:

- target feature;
- alignment;
- special register state;
- memory contract.

---

# 18. `@target_feature`

Ví dụ:

```ax
@target_feature("avx2")
fn fast_add(...) {
    ...
}
```

đây là target/codegen contract, không phải semantic vector type.

---

# 19. Unsupported feature

Compiler không được emit AVX2 nếu target không hỗ trợ.

Có ba khả năng:

```text
compile error
runtime dispatch
scalar fallback
```

tùy API/configuration.

---

# 20. Runtime CPU dispatch

Library/system layer có thể:

```text
detect CPU
    ↓
select implementation
```

Ví dụ:

```text
generic
AVX2
AVX-512
```

Compiler không được tự giả định runtime CPU feature nếu executable target không khai báo.

---

# 21. Vector ABI

Vector ABI phụ thuộc target.

OptIR:

```text
Vector<f32, 8>
```

sau ABI:

```text
YMM register
```

hoặc:

```text
stack
```

hoặc:

```text
multiple registers
```

---

# 22. Vector ABI không phải semantic type

Đây tiếp tục nguyên tắc:

```text
Type
≠
Representation
≠
Layout
≠
ABI
≠
Machine register
```

---

# 23. Mask type

Vector comparison:

```text
x < y
```

không nhất thiết tạo:

```text
Vector<bool, N>
```

về physical representation.

Semantic type:

```text
Mask<N>
```

---

# 24. Mask operations

OptIR:

```text
MaskAnd
MaskOr
MaskXor
MaskNot
MaskSelect
MaskAny
MaskAll
```

---

# 25. Select

Ví dụ:

```text
select(mask, a, b)
```

semantic:

```text
lane_i =
    a_i if mask_i
    b_i otherwise
```

Backend quyết định dùng:

- blend;
- predication;
- conditional select;
- vector instructions.

---

# 26. SVE/RVV predicate

Mask semantic phải đủ tổng quát để map sang:

```text
AVX mask registers
AVX blend masks
SVE predicates
RVV masks
```

---

# 27. Gather/scatter

Axiom SIMD semantic có thể hỗ trợ:

```text
VGather
VScatter
```

nhưng optimizer không tự tạo gather nếu scalar contiguous load tốt hơn.

---

# 28. Gather legality

Compiler phải xét:

```text
bounds
alias
memory effects
fault behavior
mask
target support
```

---

# 29. Masked load/store

Có:

```text
MaskedLoad
MaskedStore
```

để biểu diễn tail handling và conditional memory access.

---

# 30. Tail loop

Ví dụ vector width = 8:

```text
n = 19
```

Compiler có thể:

```text
16 elements → vector
3 elements  → scalar
```

hoặc:

```text
16 elements → vector
masked vector → 3 lanes
```

---

# 31. Runtime vector width

Với scalable vector:

```text
while remaining > 0 {
    process vl lanes
}
```

Compiler/backend có thể map `vl` sang:

```text
SVE VL
RVV VL
```

---

# 32. SLP Vectorization

Không chỉ loop.

Ví dụ:

```ax
let a = x1 + y1;
let b = x2 + y2;
let c = x3 + y3;
let d = x4 + y4;
```

SLP có thể tạo một vector operation.

---

# 33. Basic-block vectorization

Các operations độc lập trong cùng basic block:

```text id="bbvec"
a = ...
b = ...
c = ...
d = ...
```

có thể được pack.

---

# 34. Loop vectorization

Loop vectorization:

```text id="loopvec"
iteration i
iteration i+1
iteration i+2
...
```

được thực hiện song song.

---

# 35. Vector dependence analysis

Compiler kiểm tra:

```text id="dep"
RAW
WAR
WAW
memory dependence
loop-carried dependence
```

---

# 36. Reduction vectorization

```ax
sum += a[i];
```

có thể thành:

```text
vector accumulators
      ↓
horizontal reduction
```

nếu FP/integer semantics cho phép.

---

# 37. Multiple accumulators

Compiler có thể dùng:

```text
sum0
sum1
sum2
sum3
```

để giảm dependency chain.

---

# 38. FMA

```text
a * b + c
```

có thể lower thành FMA nếu floating semantics cho phép.

Fast/relaxed FP phải được tôn trọng.

---

# 39. Fast math

Không tự động bật:

```text
reassociation
approximate reciprocal
approximate sqrt
flush-to-zero
```

Chúng phải thuộc FP configuration/explicit relaxed mode.

---

# 40. Integer SIMD overflow

Vector integer operations phải giữ chính xác semantics scalar:

```text
checked
wrapping
saturating
```

---

# 41. Saturating SIMD

Compiler có thể sử dụng native saturating instruction nếu target có.

Nếu không:

```text
expand into equivalent operations
```

---

# 42. Vectorization và alias

Ví dụ:

```ax
fn add(
    a: view<f32>,
    b: view<f32>,
    out: mut_view<f32>
)
```

nếu disjoint:

```text
NoAlias
```

→ vectorization thuận lợi.

---

# 43. Vectorization không được tạo NoAlias

Nếu:

```text
UNKNOWN
```

thì optimizer:

```text
UNKNOWN
```

hoặc versioning.

Không được tự giả định.

---

# 44. Runtime alias versioning

Có thể:

```text
if disjoint(a,b,out) {
    vector_loop()
} else {
    scalar_loop()
}
```

nếu check có lợi.

---

# 45. Capability semantics

`mut_view` vẫn là exclusive capability.

Vectorization chỉ thay đổi cách thực hiện nhiều access.

Nó không tạo thêm safe mutable aliases.

---

# 46. Memory ordering

Atomic vector operations chỉ được tạo khi target semantics tương ứng.

Không được biến:

```text
atomic
```

thành ordinary vector load/store.

---

# 47. Volatile

Volatile:

```text
không vectorize tùy tiện.
```

Số lượng và thứ tự access observable phải được giữ.

---

# 48. Function calls trong vector loop

Nếu:

```ax
for x in data {
    foo(x);
}
```

vectorize chỉ khi:

```text
foo
```

được inline/vectorizable hoặc có vector semantic implementation.

---

# 49. Vector function specialization

Có thể có:

```text
foo<T>
foo<Vector<T,N>>
```

và specialization tự động chọn vector implementation.

---

# 50. Library vector algorithms

`std::simd` nên cung cấp:

```text
map
zip
reduce
min
max
sum
load
store
masked_load
masked_store
```

Compiler nhận diện semantic patterns khi thích hợp.

---

# 51. Vector math

Các hàm:

```text
sin
cos
exp
log
sqrt
```

phải phân biệt:

```text
exact/required semantics
vector implementation
approximate fast-math
```

Không được silently đổi accuracy contract.

---

# 52. Horizontal operations

Semantic:

```text
reduce_add
reduce_min
reduce_max
any
all
```

được lower target-specifically.

---

# 53. Transpose/shuffle

SIMD semantic operations:

```text
Shuffle
Permute
Swizzle
Interleave
Zip
Unzip
```

có thể tồn tại trong SIMD library/IR.

---

# 54. Compiler recognition

Code như:

```ax
let y = simd_shuffle(x, idx);
```

có thể lower thành target instruction.

---

# 55. Alignment

Portable SIMD không nên yêu cầu programmer tự quản lý alignment cho ordinary usage.

Compiler biết:

```text
natural alignment
allocation alignment
target requirements
```

---

# 56. Explicit aligned load

Nếu programmer yêu cầu aligned load:

```text
```

thì API phải có contract rõ ràng.

Nếu contract sai:

```text
unsafe/system
```

---

# 57. Unaligned vector load

Compiler có thể dùng unaligned load khi target hỗ trợ.

Không cần programmer viết pointer.

---

# 58. Vector register pressure

Vectorization có cost:

```text
register pressure
spill
code size
load/store pressure
```

Do đó không phải loop nào cũng nên vectorize.

---

# 59. Vectorization cost model

```text
VectorCostModel {
    Width
    SetupCost
    ScalarCost
    VectorCost
    MaskCost
    GatherCost
    ReductionCost
    RegisterPressure
    CodeGrowth
}
```

---

# 60. Profitability

Compiler vectorize khi:

```text
ExpectedBenefit > ExpectedCost
```

chứ không chỉ:

```text
“loop có thể vectorize”
```

---

# 61. Small loops

Nếu:

```text
n = 3
```

scalar code có thể nhanh hơn vector setup.

Compiler có thể giữ scalar path.

---

# 62. Runtime trip count

Compiler có thể version:

```text
if n >= threshold:
    vector loop
else:
    scalar loop
```

---

# 63. Alignment versioning

Nếu alignment không biết:

```text
if aligned {
    aligned vector path
} else {
    generic vector path
}
```

chỉ khi target benefit đủ lớn.

---

# 64. Auto-vectorization không thay semantics

Đây là invariant cốt lõi:

```text
scalar execution
≡
vector execution
```

theo Axiom observable semantics.

---

# 65. Floating-point caveat

Nếu vectorization làm thay đổi thứ tự floating operations:

```text
```

thì chỉ được phép khi FP semantics cho phép.

---

# 66. Exceptions/panic

Vectorization không được biến:

```text
operation may panic
```

thành semantics khác.

Nếu operation có trapping behavior observable, compiler phải xử lý đúng.

---

# 67. Bounds checking

Masked/vector accesses vẫn phải đảm bảo:

```text
safe lane
```

Compiler có thể chứng minh toàn bộ vector nằm trong bounds hoặc dùng masked safe access.

---

# 68. Example

Source:

```ax
for i in 0..n {
    out[i] = a[i] * b[i] + c[i];
}
```

Pipeline:

```text
Range Analysis
      ↓
Bounds proven
      ↓
Alias proven
      ↓
Loop vectorization
      ↓
Vector FMA
      ↓
Target legalization
```

---

# 69. AVX2 result

Có thể thành:

```text
VMOVUPS
VMULPS
VADDPS
VMOVUPS
```

hoặc FMA nếu target/configuration cho phép.

---

# 70. AArch64 result

Có thể thành NEON/SVE tương ứng.

Source không thay đổi.

---

# 71. RVV result

Compiler có thể dùng scalable vector loop.

Source vẫn:

```ax
for i in 0..n
```

---

# 72. GPU distinction

SIMD ≠ GPU.

SIMD:

```text
same execution domain
vector lanes
```

GPU:

```text
different execution domain
different storage domain
different synchronization model
```

Không gộp hai khái niệm.

---

# 73. Tensor layer

Tensor library có thể build trên:

```text
SIMD
GPU
CPU kernels
```

nhưng Tensor không phải Core primitive.

---

# 74. Compiler-generated SIMD

Ngay cả khi source hoàn toàn scalar:

```text id="scalar"
```

OptIR có thể trở thành:

```text id="vector"
```

đây là implementation detail.

---

# 75. Explicit SIMD phải được bảo toàn

Nếu source dùng:

```ax
Simd<f32, 8>
```

compiler không được scalarize nếu làm thay đổi observable performance contract của API?

**Không.**

Performance không phải semantics.

Compiler **có thể scalarize** nếu semantics vẫn đúng, trừ khi API/system contract yêu cầu exact representation/ABI.

Đây là nguyên tắc rất quan trọng.

---

# 76. `@repr(simd)`

Nếu cần FFI/hardware ABI, có thể có:

```ax
@repr(simd)
struct ...
```

nhưng đây là representation contract, không phải Core semantic requirement.

---

# 77. SIMD FFI

FFI phải chỉ rõ:

```text
vector width
element type
ABI
alignment
calling convention
```

Không được đoán.

---

# 78. Vector ABI stability

Default Axiom ABI có thể target-dependent.

C ABI vector interop chỉ được coi là stable trong subset compiler đã định nghĩa.

---

# 79. Debugging

Debug mode vẫn có thể scalarize/vectorize tùy `-O`.

Debug info phải map:

```text
scalar source variable
→ vector lane
```

khi có thể.

---

# 80. AI inspection

```text id="simdinspect"
axc inspect vectorize foo
```

Ví dụ:

```text
Loop #4

Vectorized:
    yes

Width:
    8 x f32

Reason:
    no loop-carried dependency
    output disjoint from input
    bounds proven

Tail:
    masked

Target:
    AVX2
```

---

# 81. Nếu không vectorize

Compiler nên giải thích:

```text
Not vectorized

Reason:
    possible alias between memory accesses
```

hoặc:

```text
Reason:
    vector setup cost exceeds estimated benefit
```

hoặc:

```text
Reason:
    atomic ordering prevents transformation
```

---

# 82. Invariants đã khóa

### `ASIMD-20`
Vector semantics are independent of target ISA.

### `ASIMD-21`
Core does not expose ISA-specific vector register types.

### `ASIMD-22`
Vector semantic types are distinct from physical register representations.

### `ASIMD-23`
Fixed-width vectors have semantic lane counts.

### `ASIMD-24`
Scalable vectors represent target-scalable lane execution.

### `ASIMD-25`
Mask semantics are independent of physical mask representation.

### `ASIMD-26`
Vector operations preserve scalar semantic meaning.

### `ASIMD-27`
Explicit SIMD does not inherently imply a particular ISA.

### `ASIMD-28`
Target-specific intrinsics belong to architecture/system APIs.

### `ASIMD-29`
Target-specific intrinsics may require unsafe contracts.

### `ASIMD-30`
Unsupported target features cannot be emitted.

### `ASIMD-31`
`@target_feature` affects code generation legality.

### `ASIMD-32`
Runtime CPU dispatch remains outside Core semantics.

### `ASIMD-33`
Vector ABI is target-specific.

### `ASIMD-34`
Vector ABI is distinct from vector semantic type identity.

### `ASIMD-35`
Mask operations preserve lane semantics.

### `ASIMD-36`
Masked memory operations preserve memory safety.

### `ASIMD-37`
Gather/scatter operations preserve bounds and memory semantics.

### `ASIMD-38`
Vectorization requires dependency legality.

### `ASIMD-39`
Vectorization requires alias legality.

### `ASIMD-40`
Unknown aliasing cannot be treated as NoAlias.

### `ASIMD-41`
Proven capability disjointness may enable vectorization.

### `ASIMD-42`
Vectorization cannot create ownership or capability proofs.

### `ASIMD-43`
Vectorization preserves ownership semantics.

### `ASIMD-44`
Vectorization preserves Drop semantics.

### `ASIMD-45`
Vectorization preserves atomic semantics.

### `ASIMD-46`
Vectorization preserves volatile semantics.

### `ASIMD-47`
Vectorization preserves synchronization semantics.

### `ASIMD-48`
Vectorization preserves configured floating-point semantics.

### `ASIMD-49`
Integer vectorization preserves overflow semantics.

### `ASIMD-50`
Vector reductions preserve reduction semantics.

### `ASIMD-51`
Vectorization may use runtime guards only with a correct fallback.

### `ASIMD-52`
Runtime optimization guards are not safety proofs.

### `ASIMD-53`
Bounds-check elimination remains proof-based.

### `ASIMD-54`
Vector tail handling preserves semantics.

### `ASIMD-55`
SLP vectorization preserves operation dependencies.

### `ASIMD-56`
Loop vectorization preserves loop-carried dependencies.

### `ASIMD-57`
Vectorization cost models are separate from legality.

### `ASIMD-58`
Vectorization may be rejected for profitability reasons.

### `ASIMD-59`
Vectorization is allowed to change physical representation.

### `ASIMD-60`
Performance characteristics are not normally language semantics.

### `ASIMD-61`
Exact representation contracts prevent invalid scalarization.

### `ASIMD-62`
FFI vector representations require explicit ABI contracts.

### `ASIMD-63`
Alignment requirements are explicit representation/system contracts.

### `ASIMD-64`
Ordinary portable SIMD APIs do not require manual pointer manipulation.

### `ASIMD-65`
Compiler-generated SIMD may arise from scalar source.

### `ASIMD-66`
Compiler-generated SIMD remains semantically equivalent to scalar execution.

### `ASIMD-67`
GPU execution is distinct from SIMD execution.

### `ASIMD-68`
Tensor abstractions are above the Core SIMD semantic layer.

### `ASIMD-69`
SIMD transformations preserve source provenance.

### `ASIMD-70`
SIMD analyses are deterministic, incremental and parallelizable.

### `ASIMD-71`
AI/compiler tooling can explain vectorization decisions.

### `ASIMD-72`
Failed vectorization proofs reduce optimization opportunity only.

### `ASIMD-73`
Vector optimization cannot weaken Verified MIR guarantees.

### `ASIMD-74`
Optimized vector code must remain within target feature legality.

### `ASIMD-75`
No mandatory SIMD runtime is introduced for scalar programs.

### `ASIMD-76`
Portable SIMD abstractions do not require a monolithic runtime.

### `ASIMD-77`
Explicit SIMD does not imply heap allocation.

### `ASIMD-78`
Explicit SIMD does not imply object headers or dynamic dispatch.

### `ASIMD-79`
SIMD lowering occurs before machine instruction selection but after semantic verification.

### `ASIMD-80`
Verified MIR remains the ultimate semantic authority.

---

# Axiom optimizer hiện tại đã tiến khá xa

```text
                    VERIFIED MIR
                         │
              ┌──────────┼──────────┐
              ▼          ▼          ▼
           Alias       Effect     Escape
              └──────────┼──────────┘
                         ▼
                  SSA + MemorySSA
                         │
                       OptIR
                         │
                    Call Graph
                         │
                Interprocedural
                         │
        ┌────────────────┼────────────────┐
        ▼                ▼                ▼
 Specialization      Inlining       Devirtualization
        └────────────────┼────────────────┘
                         ▼
                Loop Optimization
                         │
               Scalar Evolution
                         │
                Range Analysis
                         │
             Bounds Elimination
                         │
                 Vectorization
                         │
                    SIMD IR
                         │
                  Optimized OptIR
                         │
                      ABI MIR
                         │
                        LIR
                         │
                     MACHINE
```

Điểm rất tốt của kiến trúc này là **programmer viết code ở mức rất cao**, nhưng compiler có đủ information để hạ xuống gần mức hand-written low-level code.

---

# BOOTSTRAP-145 — Memory Optimization, Load/Store Optimization & Cache-Aware Transformation

Bước tiếp theo nên xử lý **memory subsystem của optimizer**.

Đây là phần đặc biệt quan trọng với mục tiêu hiệu năng của Axiom, vì sau khi đã có:

- ownership;
- capability;
- alias;
- effect;
- escape;
- MemorySSA;
- loop;
- SIMD;

thì compiler đã có đủ thông tin để bắt đầu tối ưu **cách dữ liệu thực sự đi qua cache và memory hierarchy**.

Pipeline tiếp theo:

```text
MemorySSA
    ↓
AliasInfo
    ↓
Load/Store Analysis
    ↓
Redundant Load Elimination
    ↓
Store-to-Load Forwarding
    ↓
Dead Store Elimination
    ↓
Store Merging
    ↓
Load Hoisting
    ↓
Memory Coalescing
    ↓
Scalar Replacement
    ↓
Cache-aware Transform
    ↓
Prefetch / Tiling / Layout Optimization
```

Đặc biệt cần khóa một vấn đề rất quan trọng cho Axiom:

> **Compiler có thể tự thay đổi physical data layout để tối ưu cache hay không, trong khi semantic struct vẫn giữ nguyên?**

Đây sẽ nối trực tiếp `AREPR`, `AALIAS`, `AESCAPE`, `AMEMSSA` với optimizer và sau này là **data-oriented programming** của Axiom.