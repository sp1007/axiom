# BOOTSTRAP-366 — Axiom SIMD, Vector Types & Hardware Vectorization Engine

Sau 365, Axiom đã có abstraction parallel đủ để compiler quyết định **scalar / SIMD / threads / GPU**. Bước tiếp theo nên đi sâu vào **SIMD và vector semantics**, vì đây là cầu nối trực tiếp giữa Axiom source, CPU vector instructions và GPU-style data parallelism.

Mục tiêu của 366:

> Programmer có thể viết vectorized code khi cần, nhưng phần lớn code không cần biết AVX2/AVX-512/NEON/SVE/RVV. Compiler tự vectorize khi có thể; khi programmer cần kiểm soát phần cứng, Axiom vẫn cho phép explicit vector programming mà không biến toàn bộ language thành intrinsic soup.

---

## 1. SIMD không chỉ là optimization

Axiom cần phân biệt hai khái niệm:

```text id="g5aj8k"
Auto Vectorization
```

và:

```text id="6qyrq5"
Explicit Vector Type
```

### Auto vectorization

Programmer viết:

```axiom id="r6zq8h"
for i in 0..n {
    out[i] = a[i] + b[i]
}
```

Compiler tự tạo SIMD.

### Explicit vector

Programmer có thể viết:

```axiom id="rj1v2s"
let x: vec<f32, 8> = ...
```

khi thực sự cần kiểm soát vector semantics.

Hai cơ chế không được trộn.

---

# 2. Vector là value type

`vec<T, N>` là một value type.

Ví dụ:

```text id="8v5x2n"
vec<i32, 4>
vec<f32, 8>
vec<u8, 16>
```

có semantics:

```text id="pl4k5m"
N lanes
+
lane type T
```

Không có:

```text id="2f6r5a"
object header
heap allocation
runtime metadata
```

---

# 3. Vector không phải Array

Đây là distinction quan trọng.

```text id="p1sg4e"
array<T, N>
```

là N logical elements.

```text id="wm3s5t"
vec<T, N>
```

là một machine-oriented SIMD value.

Array có thể nằm:

```text id="i1n4h9"
stack
heap
static
```

Vector thường được map vào:

```text id="4js7ca"
register
vector register spill area
memory
```

Compiler được quyền lựa chọn representation nếu observable semantics không thay đổi.

---

# 4. Lane semantics

Ví dụ:

```axiom id="u1j4oe"
let a: vec<i32, 4>
let b: vec<i32, 4>

let c = a + b
```

semantic tương đương:

```text id="tw4o9y"
c[0] = a[0] + b[0]
c[1] = a[1] + b[1]
c[2] = a[2] + b[2]
c[3] = a[3] + b[3]
```

nhưng physical implementation có thể là một SIMD instruction.

---

# 5. Vector operations

Core vector operations nên gồm:

```text id="e9x6mj"
add
sub
mul
div
min
max

bit_and
bit_or
bit_xor
bit_not

shift_left
shift_right

compare
select

load
store
```

Các operation này có semantics lane-wise.

---

# 6. Comparison trả về vector mask

Ví dụ:

```axiom id="n1b9cs"
let mask = a > b
```

không trả về một `bool` duy nhất.

Nó trả:

```text id="k8m3zr"
mask<4>
```

hoặc semantic tương đương:

```text id="9y8s0d"
vec<bool, 4>
```

Nhưng compiler có thể chọn mask-register representation.

---

# 7. Mask là first-class semantic value

Mask cần hỗ trợ:

```text id="j7jv6m"
and
or
xor
not
any
all
none
select
```

Ví dụ:

```axiom id="t0v9cd"
let m = a > zero
let r = select(m, a, zero)
```

→ mỗi lane chọn `a` hoặc `0`.

---

# 8. Không dùng bool memory representation cho mask

`mask<T>` không nên mặc định là:

```text id="x6pxk5"
N × bool bytes
```

Compiler có thể dùng:

```text id="qj3x4h"
bitmask
vector mask register
predicate register
```

để tối ưu.

Semantic type và ABI representation phải tách biệt như các type khác.

---

# 9. Vector width

`vec<T, N>` biểu diễn **logical width**, không nhất thiết machine width.

Ví dụ:

```text id="j4d5nx"
vec<f32, 16>
```

trên CPU chỉ có:

```text id="j9p7az"
256-bit vector
```

compiler có thể lower thành:

```text id="8q3v2p"
2 × 8 lanes
```

hoặc:

```text id="0k3n2w"
4 × 4 lanes
```

mà semantics vẫn là một vector 16 lane.

---

# 10. Native vector type

Có thể có:

```text id="q4c7ya"
native_vec<T>
```

nhưng đây nên là system-level abstraction.

Nó cho phép programmer yêu cầu:

```text id="b2f8tu"
native hardware width
```

thay vì logical width.

Ví dụ:

```text id="0y2t4d"
native_vec<f32>
```

có width phụ thuộc target.

---

# 11. Portable vs target-specific SIMD

Axiom chia:

```text id="q8y1px"
Portable SIMD
```

và:

```text id="b3n5w7"
Target SIMD
```

Portable:

```text id="vec<f32, 8>"
```

Target-specific:

```text id="x86::avx2::..."
arm::neon::...
riscv::rvv::...
```

Target-specific API nằm ở system/architecture library.

---

# 12. Compiler auto-vectorization

Compiler pipeline:

```text id="m5o2r1"
Loop
 ↓
Dependence Analysis
 ↓
Memory Alias Analysis
 ↓
Trip Count Analysis
 ↓
Cost Model
 ↓
Vectorization Legality
 ↓
Vector Transform
 ↓
Vector IR
```

Không vectorize chỉ vì loop “trông đơn giản”.

---

# 13. Vectorization legality

Một loop không được vectorize nếu compiler không chứng minh được:

```text id="p5j8yq"
memory dependencies
```

không phá semantics.

Ví dụ:

```axiom id="z6m1hd"
for i in 1..n {
    a[i] = a[i-1] + 1
}
```

có loop-carried dependency.

Compiler phải giữ scalar order hoặc tìm transformation tương đương.

---

# 14. Dependency distance

Compiler cần biết:

```text id="c5k7sx"
distance = j - i
```

giữa conflicting accesses.

Một số dependency có thể vectorize bằng transformation.

Một số không.

---

# 15. Alignment

Vector load/store có thể có alignment requirements.

Axiom phân biệt:

```text id="f8k3wz"
Unaligned
Aligned(N)
```

Không được compiler tự giả định alignment chỉ vì type đẹp.

Ví dụ:

```axiom id="j1k9vx"
load_vec(ptr)
```

portable semantic mặc định phải an toàn với alignment mà API cho phép.

---

# 16. Alignment contract

Có thể có:

```text id="d4p7ws"
assume_aligned(ptr, 64)
```

nhưng đây là trusted/unsafe contract nếu compiler không thể chứng minh.

Ví dụ:

```text id="s6h2qc"
unsafe assume:
    address % 64 == 0
```

Sau đó vectorizer có thể dùng aligned instruction.

---

# 17. Gather / Scatter

SIMD không chỉ có contiguous memory.

Axiom vector library cần:

```text id="q2e5mn"
gather(base, indices)
scatter(base, indices, values)
```

Semantics:

```text id="x8k4rp"
gather:
    result[lane] = memory[base + index[lane]]
```

Scatter cần đặc biệt chú ý duplicate indices.

---

# 18. Scatter duplicate semantics

Ví dụ:

```text id="z0s8qm"
indices = [2,2,5,7]
```

hai lanes cùng ghi `memory[2]`.

Compiler không được giả định thứ tự nếu API không định nghĩa.

Portable scatter nên:

- reject conflicting duplicate writes,
- hoặc yêu cầu atomic scatter,
- hoặc định nghĩa explicit ordering.

Không được để hardware instruction quyết định ngẫu nhiên semantic result.

---

# 19. Masked load/store

Cần hỗ trợ:

```text id="a2f6kx"
masked_load
masked_store
```

Ví dụ:

```axiom id="8y3m5c"
let x = masked_load(ptr, mask, default)
```

inactive lanes không được access memory.

Điều này cực kỳ quan trọng cho:

- tail loops
- bounds safety
- vectorized filtering
- GPU-style predication.

---

# 20. Tail handling

Loop:

```text id="w9t1xr"
for i in 0..N
```

với vector width 8:

```text id="2w8s4a"
N = 19
```

có:

```text id="g7d2lm"
8 + 8 + 3
```

Compiler có thể:

```text id="f7u4mz"
scalar remainder
```

hoặc:

```text id="y1r5va"
masked vector tail
```

tùy cost model.

---

# 21. Vector reductions

Ví dụ:

```axiom id="1z3r6p"
sum(vec)
```

Compiler cần semantic reduction:

```text id="b3j8qx"
horizontal_add
```

Nhưng floating point phải giữ numerical contract.

Nếu strict:

```text id="4t6y5m"
preserve source-defined order
```

Nếu fast-math:

```text id="6c8s2j"
reassociation allowed
```

---

# 22. Vector math

Standard library nên cung cấp:

```text id="h9n2ke"
sqrt
exp
log
sin
cos
tan
abs
floor
ceil
round
```

trên vector.

Compiler có thể map:

```text id="5c8j3m"
libcall
SIMD intrinsic
hardware instruction
approximation
```

tùy numerical contract.

---

# 23. Numerical accuracy contract

Không nên chỉ có:

```text id="s4k2hy"
fast_math = true/false
```

Về lâu dài nên có semantic levels:

```text id="r3m7xq"
Strict
Relaxed
Approximate
```

Ví dụ:

```text id="j8p4kf"
Strict sqrt
```

không được thay bằng approximation.

`Approximate` có thể cho phép hardware approximation.

---

# 24. Vector integer overflow

Vector integer operations phải tuân theo semantics scalar tương ứng.

Ví dụ nếu scalar:

```text id="c4m8yq"
i32 overflow
```

không phải C-style UB, thì vector cũng vậy.

Có thể có:

```text id="2h5n7v"
checked_add
wrapping_add
saturating_add
```

lane-wise.

---

# 25. Saturating arithmetic

Đặc biệt hữu ích cho:

```text id="6t1p8s"
image processing
audio
DSP
quantized AI
```

Ví dụ:

```text id="h8r4kq"
u8.saturating_add()
```

Compiler map sang SIMD saturating instructions khi target có.

---

# 26. Horizontal operations

Vector API cần:

```text id="1n8v5z"
reduce_add
reduce_min
reduce_max
reduce_and
reduce_or
reduce_any
reduce_all
```

Nhưng compiler phải phân biệt:

```text id="d4m6qh"
lane-wise operation
```

với:

```text id="f2p7rx"
horizontal operation
```

---

# 27. Shuffle / Permute

SIMD cần:

```text id="4h7s2k"
shuffle
permute
broadcast
zip
unzip
transpose
extract
insert
```

Ví dụ:

```text id="0c6y8m"
shuffle(v, indices)
```

là compile-time hoặc runtime index tùy overload.

---

# 28. Constant index vs dynamic index

Nếu:

```axiom id="0d9f4w"
shuffle(v, [0,2,1,3])
```

indices compile-time constant:

```text id="v8n2la"
static shuffle
```

có thể map thành một instruction.

Nếu runtime:

```text id="n5m4cq"
shuffle(v, indices)
```

phải dùng dynamic permutation nếu target hỗ trợ, hoặc fallback.

---

# 29. Vector ABI

Vector parameter:

```axiom id="4b9q6d"
fn add(a: vec<f32, 8>, b: vec<f32, 8>) -> vec<f32, 8>
```

không nhất thiết truyền bằng memory.

ABI classifier có thể chọn:

```text id="r6y2ht"
vector registers
multiple registers
indirect
```

target-specific.

---

# 30. ABI stability

Axiom ABI semantic type:

```text id="9t5v1m"
vec<f32, 8>
```

không đồng nghĩa:

```text id="t2k7qp"
AVX register
```

Nếu ABI stability yêu cầu, representation phải được đóng băng bằng explicit ABI/repr.

---

# 31. Vector register pressure

Vectorization có thể làm tăng:

```text id="h5w2rx"
register pressure
```

→ spill.

Compiler cost model phải tính:

```text id="r8n3lz"
vector width
live vectors
register count
spill cost
instruction latency
throughput
```

Không phải vector width càng lớn càng nhanh.

---

# 32. Dynamic vector width

RISC-V Vector và một số kiến trúc khác có vector length runtime.

Axiom nên có abstraction:

```text id="x8n4mp"
scalable_vec<T>
```

khác:

```text id="k5r2qd"
vec<T, N>
```

`vec<T,N>`:

```text fixed logical lane count
```

`scalable_vec<T>`:

```text target-dependent runtime lane count
```

---

# 33. Scalable vector semantics

Programmer không được giả định:

```text id="v6q3rs"
lane_count == constant
```

thay vào đó dùng:

```text id="9y5h1k"
vector_length()
```

hoặc compiler intrinsic.

Đây là nền tảng cho:

```text id="k3m8xp"
RISC-V RVV
ARM SVE
```

mà không làm Core phụ thuộc architecture.

---

# 34. Vector memory safety

Vector load/store phải tuân thủ:

```text id="e8q4s1"
ownership
capability
bounds
alignment
address validity
```

Không được vì vectorization mà bypass safety.

Ví dụ:

```text id="m5v9xk"
masked lane inactive
```

thì compiler phải đảm bảo inactive lane không gây invalid memory access.

---

# 35. Bounds-check elimination

Compiler có thể chứng minh:

```text id="y7n3pa"
0 <= i + lane < N
```

thì vector loop không cần runtime bounds checks.

Nếu không chứng minh được:

```text id="s2k5vm"
masked operation
```

hoặc scalar fallback.

Không dùng unsafe để “may be valid” trong safe code.

---

# 36. Vector alias analysis

Ví dụ:

```axiom id="p3f8vz"
fn add(
    out: mut_view<f32>,
    a: view<f32>,
    b: view<f32>
)
```

vectorization phụ thuộc:

```text id="s9q4dn"
out ∩ a
out ∩ b
a ∩ b
```

Compiler sử dụng region system 282.

Nếu overlap unknown:

```text id="b7h1ks"
vectorization may be rejected
```

hoặc compiler dùng runtime alias check + versioning nếu profitable.

---

# 37. Runtime alias versioning

Compiler có thể tạo:

```text id="j8w4qz"
if disjoint(out,a,b)
    vector loop
else
    scalar loop
```

nếu:

- check rẻ;
- fast path đủ lớn;
- semantics chính xác.

Đây là một optimization mạnh mà không cần programmer viết `restrict`.

---

# 38. No `restrict` requirement

Axiom tiếp tục giữ nguyên:

```text id="m4c7yx"
no source-level restrict in Core v1
```

Thay vào đó:

```text id="n1s6pk"
ownership
capability
region proof
runtime versioning
```

giải quyết phần lớn nhu cầu.

FFI/system-level `@noalias` vẫn có thể tồn tại.

---

# 39. Vector + Parallel

365 và 366 kết hợp:

```text id="e6k4s9"
parallel_for
    ↓
vectorize each chunk
    ↓
CPU workers
```

Ví dụ:

```text id="v1m7cq"
N = 100M
```

compiler có thể tạo:

```text
8 workers
    ↓
each worker
    ↓
AVX/NEON/SVE vector loop
```

đây là mục tiêu rất quan trọng của Axiom.

---

# 40. Vector + GPU

GPU kernel cũng có thể được semantic lower từ:

```text id="p6z2ta"
vector/parallel operations
```

nhưng GPU backend có execution model riêng.

Không nên ép GPU phải giả lập CPU SIMD registers.

---

# 41. Explicit architecture intrinsics

System programmers vẫn cần:

```text id="g8c2vs"
prefetch
fence
specific instruction
CPU feature
```

Axiom cho:

```text id="q4k7dm"
arch::<target>::intrinsic(...)
```

nhưng:

- `unsafe` nếu machine assumptions;
- target-specific;
- không portable;
- không được giả vờ là portable vector API.

---

# 42. CPU feature detection

Compiler/runtime có:

```text id="b6x4pq"
CPUFeature
```

Ví dụ:

```text id="k8m1sr"
AVX2
AVX512
NEON
SVE
RVV
```

Có thể compile multiversioning:

```text id="z1p5vc"
generic implementation
AVX2 implementation
AVX512 implementation
```

runtime dispatch:

```text id="v4q7bn"
CPU capability
    ↓
select implementation
```

---

# 43. Function multiversioning

Conceptual:

```text id="x7n3km"
@target("avx2")
fn process(...)

@target("neon")
fn process(...)

fn process(...)
```

Compiler tạo dispatch.

Nhưng programmer không phải viết dispatcher thủ công.

---

# 44. CPU feature legality

Compiler không được emit:

```text id="f2m8rx"
AVX512 instruction
```

vào binary generic nếu target không guarantee AVX512.

Target feature state phải đi qua:

```text id="q6k4ns"
TargetConfig
```

và ABI verification.

---

# 45. Vector constant folding

Compiler có thể evaluate:

```text id="h7c3mz"
vec(1,2,3,4) + vec(5,6,7,8)
```

ở comptime.

Kết quả trở thành vector constant nếu target ABI hỗ trợ.

Không cần runtime instruction.

---

# 46. Vector compile-time generation

`comptime` có thể tạo:

```text id="c8r5jy"
lookup tables
shuffle masks
polynomial coefficients
kernel constants
```

nhưng không được biến comptime thành runtime dependency.

---

# 47. Debugging

Debugger cần hiển thị:

```text id="p4n7xs"
vec<f32, 8>:
    lane[0] = ...
    lane[1] = ...
    ...
```

và mask:

```text id="h3q8kw"
mask:
    1 0 1 1 0 ...
```

Machine register mapping chỉ là implementation detail.

---

# 48. Profiling

Profiler nên biết:

```text id="z6m2rv"
VectorWidth
VectorizationFactor
VectorInstructionCount
ScalarFallbackCount
MaskInstructionCount
GatherScatterCount
VectorSpillCount
```

để tìm bottleneck thực tế.

---

# 49. CompilerDB

BOOTSTRAP-366 bổ sung:

```text id="q7x2lm"
VectorDB
VectorTypeDB
VectorLaneDB
VectorMaskDB
VectorOperationDB
VectorConstantDB
VectorLayoutDB
VectorAbiDB
VectorLoadDB
VectorStoreDB
VectorGatherDB
VectorScatterDB
VectorShuffleDB
VectorReductionDB
VectorMathDB
VectorAlignmentDB
VectorizationDB
VectorizationLegalityDB
VectorizationCostDB
VectorLoopDB
VectorDependencyDB
VectorAliasDB
VectorRuntimeCheckDB
VectorTargetDB
VectorFeatureDB
VectorMultiversionDB
ScalableVectorDB
VectorDebugDB
VectorProfileDB
```

---

# 50. MIR additions

Semantic vector MIR:

```text id="m9q4tc"
VEC_SPLAT
VEC_LOAD
VEC_STORE

VEC_ADD
VEC_SUB
VEC_MUL
VEC_DIV

VEC_MIN
VEC_MAX

VEC_AND
VEC_OR
VEC_XOR
VEC_NOT

VEC_COMPARE
VEC_SELECT

VEC_SHUFFLE
VEC_PERMUTE
VEC_BROADCAST

VEC_GATHER
VEC_SCATTER

VEC_MASK_LOAD
VEC_MASK_STORE

VEC_REDUCE

VEC_EXTRACT
VEC_INSERT

VEC_FENCE
```

---

# 51. Vectorization proof

Mỗi transformed loop có:

```text id="y2v7mx"
VectorizationProof {
    original_loop
    vector_width
    lane_mapping
    dependency_proof
    alias_proof
    bounds_proof
    alignment_proof
    numerical_contract
    target_requirements
}
```

Nếu compiler không tạo được proof:

```text id="j7s3pk"
vectorization rejected
```

hoặc runtime versioning.

---

# 52. Vector transformation verification

Pipeline:

```text id="r5c8qn"
Scalar Loop
    ↓
Vectorization Analysis
    ↓
Vectorization Proof
    ↓
Vector IR
    ↓
Semantic Equivalence Check
    ↓
Verified Vector IR
```

Điều này kết nối trực tiếp với hệ thống **Translation Validation** đã thiết kế trước đó.

---

# 53. Invariants

Đóng băng:

### `AVEC-01`
Vector is a value type.

### `AVEC-02`
Vector has lane semantics independent of physical register representation.

### `AVEC-03`
Vector representation is target-dependent unless explicitly constrained.

### `AVEC-04`
Array and vector are semantically distinct types.

### `AVEC-05`
Mask is a first-class semantic vector predicate.

### `AVEC-06`
Inactive masked lanes must not perform memory access.

### `AVEC-07`
Vector operations preserve scalar operation semantics lane-wise.

### `AVEC-08`
Vector integer overflow follows Axiom integer semantics.

### `AVEC-09`
Floating-point reassociation requires explicit numerical permission.

### `AVEC-10`
Gather/scatter must define duplicate-index semantics.

### `AVEC-11`
Unknown aliasing cannot be assumed disjoint.

### `AVEC-12`
Vectorization requires proven legality or explicit runtime versioning.

### `AVEC-13`
Vectorization must preserve ownership and capability semantics.

### `AVEC-14`
Vectorization must preserve bounds safety.

### `AVEC-15`
Alignment assumptions must be proven or explicitly trusted.

### `AVEC-16`
Portable vector types cannot depend on a specific CPU ISA.

### `AVEC-17`
Target-specific intrinsics are isolated from portable vector semantics.

### `AVEC-18`
Scalable vectors do not expose a compile-time fixed lane count.

### `AVEC-19`
Vector ABI representation is distinct from semantic vector type.

### `AVEC-20`
SIMD optimization may be omitted when cost model predicts regression.

### `AVEC-21`
Vectorization may coexist with multithreading.

### `AVEC-22`
Vectorization may coexist with GPU lowering.

### `AVEC-23`
Compiler-generated vectorization must preserve observable semantics.

### `AVEC-24`
Vector operations do not imply heap allocation.

### `AVEC-25`
Vector operations do not imply a runtime dependency.

### `AVEC-26`
CPU feature-specific instructions require verified target support.

### `AVEC-27`
Multiversion dispatch must preserve one semantic function contract.

### `AVEC-28`
Vector transformation provenance must remain available for debugging.

### `AVEC-29`
Vectorization transformations must be verifiable by compiler equivalence infrastructure.

### `AVEC-30`
Explicit SIMD and automatic vectorization share the same underlying vector semantics.

---

## Vị trí của 366 trong toàn bộ kiến trúc

Ta hiện có:

```text
                     Axiom computation
                            │
              ┌─────────────┴─────────────┐
              │                           │
          Sequential                 Parallel
              │                           │
            Scalar                  ┌──────┼──────┐
                                   │      │      │
                                  SIMD   CPU    GPU
                                         │
                                      Workers
                                         │
                                       Tasks
```

Và SIMD không phải một “module phụ”:

```text
Loop
 ↓
Dependence Analysis
 ↓
Alias/Capability Proof
 ↓
Vectorization
 ↓
SIMD
 ↓
CPU instruction selection
```

Điều này cho phép Axiom đạt một mục tiêu rất quan trọng: **người lập trình không cần viết code AVX/NEON/RVV chỉ để đạt hiệu năng SIMD thông thường**, nhưng khi cần kiểm soát phần cứng thì vẫn có một vector model đủ thấp để compiler không cản đường.