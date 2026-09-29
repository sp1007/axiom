# BOOTSTRAP-088 — Axiom SIMD, Vector Types, Auto-Vectorization & Portable Vector Semantics

**Trạng thái: FROZEN**

Mục tiêu của phần này là để Axiom có thể viết code kiểu:

```ax
fn add(a: view<f32>, b: view<f32>, out: mut_view<f32>) {
    for i in 0..a.len() {
        out[i] = a[i] + b[i]
    }
}
```

và compiler có thể tự biến nó thành AVX2/AVX-512/NEON/SVE/RVV khi thích hợp, **không cần programmer viết SIMD thủ công**.

Nhưng đồng thời Axiom phải cho phép programmer cần hiệu năng tuyệt đối viết vector code explicit.

Nguyên tắc:

> **Portable semantics ở trên, target-specific machine instructions ở dưới.**

---

# 1. Ba tầng SIMD

Axiom chia SIMD thành:

```text
1. Scalar
2. Portable Vector
3. Target Intrinsic
```

### Scalar

```ax
f32
i32
```

### Portable Vector

```ax
vector<f32, 8>
vector<i32, 8>
```

### Target intrinsic

Ví dụ abstraction tương ứng với:

```text
AVX2
AVX-512
NEON
SVE
RISC-V Vector
```

Target intrinsic thuộc **System/Compiler layer**, không phải Core semantic surface.

---

# 2. `vector<T, N>` là semantic type

Axiom nên có vector type portable:

```ax
vector<f32, 8>
```

Nó biểu diễn:

> Một vector gồm N lane của T.

Nó **không có nghĩa**:

> chắc chắn dùng một thanh ghi AVX 256-bit.

Compiler có thể:

```text
vector<f32, 8>
→ AVX2 register
→ hai SSE registers
→ scalar loop
→ memory
```

tùy target.

---

# 3. Vì sao không gọi là `simd<T>`

`vector<T, N>` thể hiện rõ semantic:

```text
element type
lane count
```

và phù hợp với:

```text
Array<T, N>
Tensor<T, N>
Matrix<T, R, C>
```

hơn.

---

# 4. Vector không phải Array

```ax
vector<f32, 8>
```

và:

```ax
[f32; 8]
```

khác semantic.

### Array

```text
8 phần tử memory
```

### Vector

```text
8 lane của một vector value
```

Vector có thể không có một vùng memory tương ứng.

---

# 5. Vector là value type

Ví dụ:

```ax
let a: vector<f32, 8> = ...
let b = a
```

Nếu vector thỏa `Copy`, `b` là một value độc lập.

Compiler có thể giữ chúng trong register.

---

# 6. Không expose register trong semantic model

Không có Core type kiểu:

```text
ymm256
xmm128
zmm512
```

vì đó là physical representation.

---

# 7. Const generic

Vector sử dụng const generic:

```ax
vector<f32, 8>
vector<i32, 16>
```

`N` phải là compile-time constant.

---

# 8. Không phải mọi N đều tối ưu như nhau

Ví dụ:

```ax
vector<f32, 7>
```

vẫn có thể hợp lệ.

Compiler có thể:

```text
scalarize
pad
split
```

hoặc reject trong target-specific intrinsic API nếu intrinsic yêu cầu width cố định.

Portable vector semantic không nên bị giới hạn bởi phần cứng cụ thể.

---

# 9. Vector arithmetic

Các phép toán arithmetic được định nghĩa lane-wise:

```text
a + b
a - b
a * b
a / b
```

Ví dụ:

```text
[a0,a1,a2,a3]
+
[b0,b1,b2,b3]

=

[a0+b0,a1+b1,a2+b2,a3+b3]
```

---

# 10. Integer overflow

Vector integer tuân theo semantic scalar đã frozen.

Không được tự động biến:

```text
i32 vector addition
```

thành wrapping arithmetic chỉ vì SIMD instruction phần cứng thường wrap.

Nếu ordinary `i32 + i32` overflow → arithmetic failure theo Core semantics.

Compiler chỉ dùng wrapping instruction khi đã chứng minh hoặc semantic operation là wrapping.

---

# 11. Explicit wrapping vector

Có thể có:

```ax
a.wrapping_add(b)
```

và compiler map trực tiếp sang SIMD integer instruction.

---

# 12. Saturating vector

Tương tự:

```ax
a.saturating_add(b)
```

có semantic saturation theo lane.

Nếu CPU có instruction tương ứng → dùng trực tiếp.

---

# 13. Comparison

Vector comparison trả về **mask**:

```text
mask<8>
```

Ví dụ:

```ax
let m = a > b
```

semantic:

```text
[true,false,true,false,...]
```

---

# 14. Mask là semantic type

Không dùng:

```text
vector<bool, N>
```

làm mask mặc định.

`mask<N>` là một type riêng vì physical representation có thể là:

```text
bitmask
vector mask register
predicate register
```

---

# 15. Mask không phải bool array

```text
mask<8>
```

không có nghĩa phải chiếm 8 byte.

Compiler có thể dùng:

```text
8 bits
predicate register
vector register
```

---

# 16. Mask operations

Cần các primitive:

```text
mask_and
mask_or
mask_xor
mask_not
any
all
none
count
```

và select:

```ax
select(mask, a, b)
```

---

# 17. `select`

Semantic:

```text
select(m, a, b)
```

mỗi lane:

```text
m[i] ? a[i] : b[i]
```

Compiler có thể biến thành hardware blend/select.

---

# 18. Không yêu cầu branch

```ax
if mask ...
```

không nhất thiết tạo branch.

Compiler có thể dùng:

```text
blend
predication
conditional move
```

nếu semantics cho phép.

---

# 19. Vector load/store

Portable vector API có thể cung cấp:

```text
load
store
```

nhưng representation không mặc định là aligned.

---

# 20. Alignment không tự động được giả định

Nếu:

```ax
view<u8>
```

không chứng minh alignment phù hợp với vector type, compiler không được tự giả định aligned load.

Nó có thể dùng:

```text
unaligned load
scalar fallback
```

---

# 21. Explicit alignment contract

Nếu programmer có contract:

```text
aligned<32>
```

thì compiler có thể sử dụng aligned operations.

Contract sai → thuộc unsafe/system semantics.

---

# 22. Vector load từ view

Một abstraction kiểu:

```ax
load_vector<f32, 8>(view)
```

có thể được library/compiler intrinsic cung cấp.

Semantic phải kiểm tra:

```text
length >= 8
alignment nếu yêu cầu
valid element representation
```

---

# 23. Bounds checking

Ví dụ:

```ax
for i in 0..n {
    out[i] = ...
}
```

nếu compiler chứng minh:

```text
i < out.len()
```

thì bounds check có thể biến mất.

---

# 24. Vectorization không cần vector syntax

Đây là điểm quan trọng nhất.

Code scalar:

```ax
for i in 0..n {
    out[i] = a[i] + b[i]
}
```

có thể được compiler vectorize thành:

```text
vector load
vector add
vector store
```

mà programmer không biết hoặc không quan tâm.

---

# 25. Điều kiện auto-vectorization

Compiler phân tích:

```text
LoopInfo
RangeInfo
AliasInfo
EffectInfo
EscapeInfo
TargetInfo
```

để xác định vectorization có hợp lệ không.

---

# 26. Alias analysis cực kỳ quan trọng

Ví dụ:

```ax
fn add(
    a: view<f32>,
    b: view<f32>,
    out: mut_view<f32>
)
```

Nếu compiler biết:

```text
a ∩ out = ∅
b ∩ out = ∅
```

thì vectorization dễ dàng.

---

# 27. UNKNOWN không được biến thành DISJOINT

Nếu compiler không biết:

```text
a overlaps out?
```

thì không được tự giả định:

```text
noalias
```

để vectorize.

Có thể:

```text
runtime alias check
scalar fallback
```

nếu optimization strategy cho phép.

---

# 28. Runtime versioning

Compiler có thể tạo:

```text
if ranges_do_not_overlap {
    vector_loop
} else {
    scalar_loop
}
```

miễn semantics giữ nguyên.

Đây là optimization nội bộ.

---

# 29. Không cần `restrict`

Axiom không cần đưa:

```text
restrict
```

vào syntax Core.

Ownership + capability + alias analysis đã cung cấp thông tin mạnh hơn trong safe code.

---

# 30. Gather

Portable vector có thể hỗ trợ:

```text
gather(base, indices)
```

nhưng semantics phải rõ ràng về:

```text
bounds
memory access
mask
```

---

# 31. Gather không tự nhiên an toàn hơn scalar indexing

Ví dụ:

```ax
gather(a, indices)
```

mọi index phải hợp lệ.

Nếu compiler không chứng minh:

```text
0 <= index[i] < a.len()
```

thì phải:

```text
check
```

hoặc dùng explicit unsafe intrinsic.

---

# 32. Scatter

```text
scatter(out, indices, values)
```

phức tạp hơn gather vì có thể có duplicate indices.

Ví dụ:

```text
indices = [2, 2, 5, 7]
```

Hai lane cùng ghi `out[2]`.

---

# 33. Scatter duplicate semantics

Portable vector scatter **không được mặc định giả định unique indices**.

Nếu duplicate writes có thứ tự không xác định, API phải nói rõ.

---

# 34. Deterministic scatter

Nếu muốn deterministic semantics:

```text
scatter
```

phải có contract xác định duplicate behavior, hoặc yêu cầu indices unique.

---

# 35. Atomic vector operations

Không được suy luận:

```text
vector operation
```

là atomic chỉ vì CPU có một instruction.

Atomicity phải đến từ:

```text
Atomic<T>
```

và memory ordering/scope.

---

# 36. Vector atomics

Có thể hỗ trợ target-specific/library APIs cho:

```text
atomic vector operations
```

nhưng phải theo memory model hiện tại.

---

# 37. Reduction

Ví dụ:

```text
sum(vector)
```

là vấn đề semantic quan trọng với floating point.

Phép cộng floating-point không kết hợp tuyệt đối:

```text
(a+b)+c
```

có thể khác:

```text
a+(b+c)
```

---

# 38. Reduction ordering phải explicit

Axiom phân biệt:

```text
reduce_ordered
reduce_tree
reduce_fast
```

hoặc abstraction tương đương.

Không được tự ý thay đổi thứ tự nếu semantics yêu cầu kết quả cụ thể.

---

# 39. Default floating reduction

Để giữ semantics predictable:

> Reduction thông thường phải bảo toàn ordering semantics của operation được định nghĩa.

Compiler chỉ được tree-reduce/reassociate nếu contract cho phép.

---

# 40. Fast reduction

Có thể có API/compiler contract cho phép:

```text
fast reduction
```

đổi thứ tự để tăng throughput.

Đây là semantic relaxation rõ ràng, không phải optimizer tự ý.

---

# 41. Horizontal operations

Các phép:

```text
sum
min
max
dot
```

được coi là reductions chứ không phải vector arithmetic đơn giản.

---

# 42. Floating `min/max`

NaN semantics phải tuân theo numeric model.

Không được lấy behavior của instruction hardware làm semantic mặc định nếu khác Axiom.

---

# 43. Integer reductions

Integer reductions dễ hơn nhưng vẫn phải giữ:

```text
overflow semantics
```

Nếu ordinary sum có thể overflow → không được tự động wrap.

---

# 44. Vector conversion

Ví dụ:

```text
vector<i32, 8>
→ vector<f32, 8>
```

là value conversion.

Không phải bitcast.

---

# 45. Vector bitcast

Có thể:

```text
bitcast<vector<u32, 4>, vector<f32, 4>>
```

nếu representation hợp lệ.

Kích thước phải tương thích.

---

# 46. Reinterpretation

Machine-level reinterpretation không hợp lệ trong safe portable API nếu nó tạo invalid value representation.

Unsafe/system có thể cung cấp primitive thấp hơn.

---

# 47. Vector shuffle

Portable vector cần abstraction:

```text
shuffle(v, indices)
```

để compiler có thể map sang:

```text
shuffle
permute
swizzle
```

tùy target.

---

# 48. Insert/extract

Có thể:

```text
extract(v, i)
insert(v, i, x)
```

với `i` compile-time hoặc runtime tùy API.

---

# 49. Constant lane index

Nếu:

```text
extract(v, 3)
```

thì compiler có thể map trực tiếp.

Nếu:

```text
extract(v, runtime_index)
```

có thể cần instruction khác hoặc scalar fallback.

---

# 50. Vector width legalization

Ví dụ target có:

```text
256-bit SIMD
```

nhưng programmer viết:

```text
vector<f32, 32>
```

Compiler có thể split:

```text
32 lanes
→ 4 × 8 lanes
```

Semantics vẫn là một vector value.

---

# 51. Vector width does not equal hardware width

Đây là invariant nền tảng:

> **Semantic lane count ≠ physical register width.**

---

# 52. Scalable vectors

SVE/RVV có vector length phụ thuộc runtime/hardware.

Axiom không ép portable `vector<T,N>` phải mô phỏng scalable vector.

Có thể thêm một abstraction riêng:

```text
scalable_vector<T>
```

ở System/Advanced SIMD layer sau này.

---

# 53. Vì sao không đưa SVE/RVV vào Core

Nếu Core phụ thuộc:

```text
VL
predicate registers
hardware vector length
```

thì semantic model trở nên target-dependent.

Portable Core nên giữ:

```text
vector<T,N>
```

---

# 54. Target-specific SIMD API

System/compiler layer có thể expose:

```text
x86.avx2
x86.avx512
arm.neon
arm.sve
riscv.vector
```

Nhưng đây là explicit target code.

---

# 55. Target feature

Sử dụng:

```ax
@target_feature("avx2")
```

hoặc contract tương đương.

Compiler phải biết function yêu cầu feature gì.

---

# 56. Feature safety

Không được gọi function yêu cầu AVX2 từ context không đảm bảo AVX2.

Compiler/linker/runtime dispatch phải giải quyết explicit.

---

# 57. Multi-versioning

Compiler có thể tạo:

```text
f_scalar
f_sse
f_avx2
f_avx512
```

và dispatch theo CPU capability.

Đây là library/compiler optimization, không phải Core requirement.

---

# 58. CPU dispatch

Có thể:

```text
compile-time target selection
```

hoặc:

```text
runtime CPU feature detection
```

nhưng runtime dispatch phải explicit nếu programmer muốn portable binary.

---

# 59. Auto-vectorization pipeline

Sau Verified MIR:

```text
MIR
 ↓
OptIR
 ↓
Loop analysis
 ↓
Dependence analysis
 ↓
Alias analysis
 ↓
Range analysis
 ↓
Vectorization legality
 ↓
Vector cost model
 ↓
Vector IR
 ↓
Machine IR
```

---

# 60. Vectorization legality

Compiler phải chứng minh:

```text
memory dependencies
control dependencies
exceptions/panic behavior
overflow behavior
floating semantics
atomic semantics
volatile semantics
```

cho phép transformation.

---

# 61. Panic semantics

Ví dụ scalar loop có thể panic tại lane 5.

Vectorized version không được tạo observable behavior sai.

Compiler có thể:

```text
scalar prologue
vector safe region
scalar remainder
```

hoặc dùng masked checks.

---

# 62. Bounds checks + vectorization

Có ba trường hợp:

### Proven safe

```text
no checks
```

### Checkable

```text
vectorized with guards
```

### Unknown

```text
scalar/fallback
```

---

# 63. Integer overflow + vectorization

Nếu ordinary arithmetic có panic-on-overflow:

```text
a[i] + b[i]
```

compiler chỉ vectorize nếu có:

```text
range proof
```

hoặc tạo equivalent overflow detection.

---

# 64. Overflow detection

Compiler có thể vectorize:

```text
checked_add
```

thành:

```text
vector add
+
vector overflow detection
+
aggregate failure
```

nếu target hỗ trợ hiệu quả.

---

# 65. Volatile blocks normal vectorization

Ví dụ MMIO:

```text
volatile read
volatile write
```

không được gom/reorder/vectorize như ordinary memory nếu semantics thay đổi.

---

# 66. Atomic blocks unsafe vectorization

Atomic accesses phải giữ:

```text
atomicity
ordering
scope
```

Không được biến chúng thành ordinary vector load/store.

---

# 67. IO/foreign calls

Một loop chứa opaque foreign call thường không vectorize được nếu compiler không có effect contract.

---

# 68. Function calls trong loop

Nếu function:

```ax
f(x)
```

có thể inline + specialize:

```text
loop
→ scalar operations
→ vectorize
```

---

# 69. Vector ABI

Portable vector type không nhất thiết có stable FFI representation.

C ABI vector interoperability phải explicit.

---

# 70. `@repr` và vector

Không nên cho:

```text
@repr(C)
vector<T,N>
```

tự động có ABI giống mọi compiler C.

ABI vector phụ thuộc target.

---

# 71. FFI vector

Nếu cần:

```text
extern "C"
```

phải có target-specific ABI contract.

---

# 72. GPU relationship

GPU vectorization và CPU SIMD dùng cùng semantic vector model ở mức có thể.

Nhưng:

```text
CPU vector
GPU warp
GPU wave
```

không đồng nhất.

---

# 73. Warp ≠ vector

Không định nghĩa:

```text
vector<T,32> == CUDA warp
```

vì execution semantics khác storage/value semantics.

---

# 74. GPU kernel vector

Kernel có thể dùng:

```text
vector<T,N>
```

nếu GPU backend hỗ trợ.

Backend có thể map thành:

```text
vector registers
```

hoặc scalar lanes.

---

# 75. Tensor relationship

Tensor không nên là:

```text
vector<vector<...>>
```

một cách mặc định.

Tensor layer sẽ dùng:

```text
data view
shape
stride
layout
```

và có thể vectorize inner dimensions.

---

# 76. Alignment + tensor

Tensor metadata có thể cung cấp:

```text
alignment
contiguity
stride
```

cho optimizer.

Nếu contract chứng minh được, vectorizer sử dụng.

---

# 77. Contiguous contract

Một `view<T>` chỉ nói:

```text
contiguous region
```

không nhất thiết nói:

```text
aligned for every SIMD width
```

Alignment phải được chứng minh riêng.

---

# 78. Vectorization và `view`

Đây là lợi thế lớn của Axiom.

Compiler đã biết:

```text
view
owner
region
lifetime
alias
```

nên không cần programmer viết:

```text
restrict
```

cho từng loop.

---

# 79. Example

```ax
fn saxpy(
    a: f32,
    x: view<f32>,
    y: mut_view<f32>
) {
    for i in 0..x.len() {
        y[i] = a * x[i] + y[i]
    }
}
```

Nếu verifier chứng minh:

```text
x ∩ y = ∅
```

và range hợp lệ:

```text
0 <= i < len
```

compiler có thể biến thành:

```text
broadcast(a)
load vector x
load vector y
mul
add
store y
```

không cần programmer viết SIMD.

---

# 80. Nếu x và y overlap?

Compiler không được giả định disjoint.

Nó có thể:

```text
scalarize
```

hoặc:

```text
runtime overlap check
```

rồi chọn fast path.

---

# 81. Programmer explicit vector

Khi cần kiểm soát:

```ax
fn f(v: vector<f32, 8>) -> vector<f32, 8> {
    v * v
}
```

Compiler phải preserve vector semantics nhưng vẫn có quyền chọn representation.

---

# 82. Explicit vector không cấm scalarization

Nếu target không có SIMD phù hợp:

```text
vector<f32,8>
```

vẫn có thể compile thành 8 scalar operations.

Không được coi đó là semantic failure.

---

# 83. Performance contract

Portable vector semantics không đảm bảo:

```text
one instruction
```

Nếu programmer cần guarantee machine instruction:

```text
target intrinsic
```

phải được dùng.

---

# 84. Target intrinsic contract

Intrinsic có thể mang semantic:

```text
requires AVX2
maps to specific target operation
```

và compiler không được tùy tiện scalarize nếu contract yêu cầu instruction-level behavior.

---

# 85. Nhưng instruction selection vẫn được optimize

Ngay cả intrinsic, compiler có thể:

```text
combine
schedule
eliminate
```

miễn giữ contract.

---

# 86. `volatile` SIMD

Explicit target intrinsic có thể cung cấp volatile vector memory operations nếu phần cứng/API yêu cầu.

Đây là system-level.

---

# 87. Vector memory safety

Portable vector APIs phải giữ:

```text
bounds
alignment
initialization
provenance
ownership
capability
```

như scalar.

SIMD không phải một “unsafe zone”.

---

# 88. Unsafe vector operations

Có thể có:

```text
unchecked_load
unchecked_store
unchecked_gather
unchecked_scatter
```

nhưng chúng thuộc unsafe/system abstraction.

---

# 89. Auto-vectorization không thay đổi observable semantics

Đây là nguyên tắc tuyệt đối:

```text
scalar semantics
==
vectorized semantics
```

về observable behavior.

---

# 90. Cost model

Compiler không vectorize chỉ vì có thể.

Nó cân nhắc:

```text
vector width
instruction cost
load/store cost
alignment
remainder
branch cost
code size
target CPU
register pressure
```

---

# 91. Register pressure

Vectorization có thể làm tăng:

```text
register usage
spill
```

Nếu cost model thấy bất lợi, compiler có thể giữ scalar.

---

# 92. Code size

`-Os` có thể chọn:

```text
scalar
```

thay vì vectorized code nếu code-size benefit quan trọng hơn.

---

# 93. PGO

PGO có thể cung cấp:

```text
hot loop
trip count
branch probability
```

cho vectorizer.

Nhưng PGO không thay đổi semantics.

---

# 94. Loop versioning

Compiler có thể tạo nhiều implementation:

```text
fast vector path
safe scalar path
```

và chọn runtime.

---

# 95. Parallel vectorization

SIMD không phải threading.

```text
vectorization
≠
parallel execution domain
```

SIMD vẫn là một operation/value abstraction.

---

# 96. SIMD + parallel iterator

Parallel iterator có thể:

```text
thread parallelism
+
SIMD vectorization
```

nhưng hai tầng độc lập.

Compiler/runtime có thể kết hợp nếu semantics cho phép.

---

# 97. Determinism

SIMD không tự động làm mất deterministic semantics.

Chỉ khi transformation thay đổi:

```text
ordering
floating reduction
atomic behavior
```

mới cần semantic contract tương ứng.

---

# 98. Architecture

Axiom pipeline cuối cùng:

```text
                  Verified MIR
                       │
                       ↓
                    OptIR
                       │
          ┌────────────┼────────────┐
          │            │            │
      Scalar opt   Vectorizer   Parallel opt
          │            │            │
          └────────────┼────────────┘
                       ↓
                   Vector IR
                       ↓
                 Axiom LIR
                       ↓
                 Machine IR
                       ↓
          ┌────────────┼────────────┐
        x86          ARM64         RISC-V
      AVX/SSE      NEON/SVE          RVV
```

---

# 99. Core philosophy

Axiom cuối cùng có hai con đường để đạt SIMD:

```text
Programmer writes scalar code
        ↓
Compiler proves/vectorizes
```

hoặc:

```text
Programmer explicitly writes vector<T,N>
        ↓
Portable vector semantics
        ↓
Target lowering
```

và khi cần kiểm soát phần cứng tuyệt đối:

```text
Target intrinsic
        ↓
Machine-specific contract
```

Ba tầng này không cạnh tranh mà bổ sung cho nhau.

---

# 100. Frozen Invariants — `ASIMD-20..100`

**ASIMD-20** — SIMD semantics are distinct from physical register representation.

**ASIMD-21** — Portable vectors are semantic value types.

**ASIMD-22** — `vector<T,N>` represents N semantic lanes of T.

**ASIMD-23** — Vector lane count does not imply hardware register width.

**ASIMD-24** — Vector values may be represented in registers, memory, split registers, or scalar operations.

**ASIMD-25** — Portable vector types are distinct from fixed arrays.

**ASIMD-26** — Vector types participate in ordinary Axiom value semantics.

**ASIMD-27** — Vector const parameters are compile-time values.

**ASIMD-28** — Portable vector semantics are not limited to hardware-native widths.

**ASIMD-29** — Unsupported vector widths may be legalized by splitting or scalarization.

**ASIMD-30** — Vector arithmetic is lane-wise unless explicitly defined otherwise.

**ASIMD-31** — Vector integer arithmetic preserves scalar overflow semantics.

**ASIMD-32** — Wrapping vector arithmetic is explicit.

**ASIMD-33** — Saturating vector arithmetic is explicit.

**ASIMD-34** — Vector comparisons produce semantic masks.

**ASIMD-35** — Masks are distinct semantic types from boolean arrays.

**ASIMD-36** — Mask representation is compiler/target dependent.

**ASIMD-37** — Mask operations preserve lane correspondence.

**ASIMD-38** — Vector select is semantically lane-wise selection.

**ASIMD-39** — Vector control operations do not inherently require branches.

**ASIMD-40** — Vector memory access preserves Axiom bounds semantics.

**ASIMD-41** — Vector alignment is not implicitly assumed.

**ASIMD-42** — Aligned access requires an applicable alignment guarantee.

**ASIMD-43** — Misaligned portable vector access remains semantically valid when the API permits it.

**ASIMD-44** — Vector loads do not imply allocation.

**ASIMD-45** — Vector stores do not imply allocation.

**ASIMD-46** — Gather access preserves bounds and provenance rules.

**ASIMD-47** — Scatter access has explicit duplicate-index semantics.

**ASIMD-48** — Atomicity is not implied by SIMD execution.

**ASIMD-49** — Vector atomic operations follow the Axiom atomic memory model.

**ASIMD-50** — Volatile vector access remains distinct from atomic access.

**ASIMD-51** — Vector conversions are distinct from bitcasts.

**ASIMD-52** — Vector bitcasts require valid compatible representations.

**ASIMD-53** — Vector shuffle/permute semantics are portable abstractions.

**ASIMD-54** — Constant lane extraction may be optimized to target-native operations.

**ASIMD-55** — Runtime lane extraction may use different target implementations.

**ASIMD-56** — Auto-vectorization is a compiler optimization, not a language semantic requirement.

**ASIMD-57** — Scalar code may be automatically vectorized.

**ASIMD-58** — Auto-vectorization requires semantic legality.

**ASIMD-59** — Alias analysis participates in vectorization legality.

**ASIMD-60** — UNKNOWN aliasing cannot be treated as DISJOINT.

**ASIMD-61** — Proven disjoint capabilities may provide compiler-internal no-alias facts.

**ASIMD-62** — Runtime alias checks may guard vectorized fast paths.

**ASIMD-63** — Scalar fallback paths may coexist with vectorized paths.

**ASIMD-64** — Bounds proofs may eliminate vector loop checks.

**ASIMD-65** — Overflow proofs may eliminate vector arithmetic checks.

**ASIMD-66** — Vectorization must preserve panic/trap behavior where observable.

**ASIMD-67** — Vectorization must preserve floating-point semantics.

**ASIMD-68** — Floating reductions require explicit ordering semantics.

**ASIMD-69** — Compiler cannot silently reassociate floating reductions when semantics forbid it.

**ASIMD-70** — Fast reductions may explicitly permit relaxed ordering.

**ASIMD-71** — Vectorization cannot alter atomic ordering.

**ASIMD-72** — Vectorization cannot alter volatile ordering or observability.

**ASIMD-73** — Opaque foreign effects conservatively restrict vectorization.

**ASIMD-74** — Inlining and specialization may expose additional vectorization opportunities.

**ASIMD-75** — Portable vector code may be scalarized when target support is insufficient.

**ASIMD-76** — Portable vector code does not guarantee a specific machine instruction.

**ASIMD-77** — Target intrinsics may provide stronger machine-level contracts.

**ASIMD-78** — Target intrinsics require explicit target-feature contracts where applicable.

**ASIMD-79** — Target-feature requirements must be respected at call boundaries.

**ASIMD-80** — Multi-versioning may provide scalar and SIMD implementations.

**ASIMD-81** — Runtime CPU dispatch is distinct from portable vector semantics.

**ASIMD-82** — Vector ABI representation is target-dependent unless explicitly contracted.

**ASIMD-83** — Portable vector types are not automatically C-ABI-compatible.

**ASIMD-84** — Explicit FFI vector contracts are required for foreign vector interfaces.

**ASIMD-85** — CPU SIMD and GPU execution semantics remain distinct.

**ASIMD-86** — GPU warp/wave execution is not defined as an Axiom vector.

**ASIMD-87** — GPU kernels may use portable vectors when target legality permits.

**ASIMD-88** — Tensor abstractions may use vectorization without becoming nested vector types.

**ASIMD-89** — Tensor contiguity/stride/alignment information may feed vectorization.

**ASIMD-90** — Portable SIMD operations preserve ownership and capability invariants.

**ASIMD-91** — SIMD operations do not inherently create aliases.

**ASIMD-92** — Unsafe SIMD operations remain subject to unsafe/system semantics.

**ASIMD-93** — Explicit unchecked SIMD access is not safe merely because hardware supports it.

**ASIMD-94** — Vectorization is independent of threading.

**ASIMD-95** — SIMD and parallel execution may be combined when independently legal.

**ASIMD-96** — Cost models may choose scalar over vector code.

**ASIMD-97** — Optimization level and code-size goals may influence vectorization decisions without changing semantics.

**ASIMD-98** — PGO may influence vectorization but cannot alter language semantics.

**ASIMD-99** — Vector abstractions may be completely erased into machine instructions when semantics permit.

**ASIMD-100** — Axiom SIMD design provides portable vector semantics, automatic optimization, and explicit target control without making the Core target-specific.

---

## Kiến trúc hiện tại đã khá hoàn chỉnh

Sau 088, chuỗi tối ưu quan trọng của Axiom đã trở thành:

```text
Ownership
   ↓
Capability
   ↓
Alias Proof
   ↓
Range Proof
   ↓
Verified MIR
   ↓
OptIR
   ↓
Constant Folding
   ↓
Inlining
   ↓
Specialization
   ↓
Loop Optimization
   ↓
Auto-Vectorization
   ↓
SIMD
   ↓
Machine IR
   ↓
Native Instructions
```

Điểm đáng chú ý là **programmer không cần viết `restrict`, lifetime, pointer alias annotations hay SIMD intrinsic trong trường hợp thông thường**. Compiler đã có đủ thông tin semantic để tự tối ưu.

Và khi programmer thực sự cần kiểm soát phần cứng, vẫn có đường xuống:

```text
Axiom portable code
        ↓
vector<T,N>
        ↓
target intrinsic
        ↓
inline asm / system layer
```

Đây là kiến trúc khá phù hợp với mục tiêu ban đầu của Axiom: **đơn giản ở source level nhưng không đơn giản hóa quá mức compiler/backend**.

### Tiếp theo: BOOTSTRAP-089

Phần kế tiếp nên xử lý **Axiom Memory/Container Performance Model & Data-Oriented Programming**:

```text
Vec
Array
Slice/View
SmallVec
Deque
HashMap
BTree
Arena
Pool
SoA / AoS
AoSoA
cache locality
prefetch
false sharing
cache line
alignment
layout optimization
field reordering
hot/cold data
zero-copy
move/copy elision
```

Đây là bước nối trực tiếp giữa **memory model + collections + SIMD + cache architecture**, và đặc biệt quan trọng nếu Axiom thực sự muốn hướng tới hiệu năng native chứ không chỉ “an toàn nhưng nhanh”.