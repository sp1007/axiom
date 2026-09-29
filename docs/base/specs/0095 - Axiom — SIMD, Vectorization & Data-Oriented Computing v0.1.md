Tiếp tục.

# Axiom — SIMD, Vectorization & Data-Oriented Computing v0.1

Đây là phần rất quan trọng nếu mục tiêu của Axiom là **không chỉ ngang C/C++ mà còn giúp compiler có cơ hội vượt C/C++ trong những workload phù hợp**.

Tôi đề xuất một nguyên tắc:

> **Programmer mô tả dữ liệu và semantics; compiler quyết định vector hóa khi có thể. Intrinsics chỉ là escape hatch.**

---

## 1. Không biến SIMD thành một đống intrinsic trong Core

Không nên bắt programmer viết:

```text
_mm256_add_ps(...)
_mm256_mul_ps(...)
_mm256_loadu_ps(...)
```

như API chính.

Axiom nên cho phép:

```axiom
fn add(a: view<f32>, b: view<f32>, out: mut_view<f32>) {
    for i in 0..a.len() {
        out[i] = a[i] + b[i]
    }
}
```

Compiler có thể biến thành:

```text
scalar loop
       ↓
dependency analysis
       ↓
vectorization
       ↓
AVX2 / AVX-512 / NEON / SVE / RVV
```

Nếu không vectorize được, vẫn có scalar code đúng.

---

# 2. SIMD type vẫn cần tồn tại

Auto-vectorization không đủ.

System programmer đôi khi cần semantic vector:

```axiom
Vector<f32, 8>
```

Ví dụ:

```axiom
let a: Vector<f32, 8>
let b: Vector<f32, 8>

let c = a + b
```

`Vector<T,N>` là **semantic type**, không phải cam kết:

```text
N × sizeof(T)
```

luôn nằm trong đúng một CPU register.

---

# 3. `Vector<T,N>` không phải CPU register

Ví dụ:

```axiom
Vector<f32, 16>
```

trên CPU AVX2 có thể trở thành:

```text
2 × ymm register
```

hoặc:

```text
memory + multiple operations
```

Compiler có toàn quyền chọn representation.

Do đó:

```text id="z7h1p3"
Vector<T,N>
```

là semantic abstraction.

---

# 4. Khi nào vector layout trở thành observable?

Chỉ khi programmer explicit yêu cầu:

```text id="6qg9um"
SIMD intrinsic
FFI
raw pointer
specific ABI
```

Nếu chỉ:

```axiom
Vector<f32, 8>
```

thì compiler vẫn được:

- split
- merge
- scalarize
- pack
- keep in registers
- spill.

---

# 5. SIMD intrinsic layer

Axiom nên có:

```text
std.simd
```

với:

```text id="q8f8h1"
Vector
Mask
Shuffle
Load
Store
Gather
Scatter
Reduce
FMA
```

Nhưng API nên hướng semantic, không expose từng instruction CPU.

Ví dụ:

```axiom id="1pk0k3"
let x = Vector.load(data)
let y = Vector.load(other)

let z = x.fma(y, c)
```

Backend:

```text id="k1xk4b"
x86 → VFMADD
ARM → FMLA
RISC-V → vector FMA
```

---

# 6. CPU-specific intrinsics vẫn phải có

Có những thứ compiler abstraction không thể che hết:

```text id="c5hjc8"
AVX512 mask
CRC instruction
AES instruction
SHA extension
BMI
RDTSCP
prefetch
```

Có thể có:

```text
std.arch.x86
std.arch.arm
```

Nhưng đây là **system-specific API**, không phải Core language.

---

# 7. Feature detection

Không được compile:

```axiom
use_avx512()
```

và giả định mọi CPU đều hỗ trợ.

Có thể có:

```axiom id="1x2a1p"
if cpu.features().avx2 {
    ...
}
```

Compiler có thể tạo:

```text
dispatch
 ├── AVX512
 ├── AVX2
 ├── SSE
 └── scalar
```

hoặc programmer dùng explicit target attributes.

---

# 8. Function multiversioning

Một abstraction rất hữu ích:

```text id="f8brcb"
@target("avx2")
fn process_avx2(...)

@target("default")
fn process_scalar(...)
```

Compiler/linker có thể tạo dispatcher.

Nhưng đây là platform/compiler feature, không phải Core semantic primitive.

---

# 9. Auto-vectorization

Compiler cần một pipeline:

```text id="o0aq1v"
MIR
 ↓
loop analysis
 ↓
alias analysis
 ↓
dependence analysis
 ↓
trip-count analysis
 ↓
cost model
 ↓
vectorization
 ↓
unrolling
 ↓
target lowering
```

Axiom ownership/view model đặc biệt hữu ích ở đây.

---

# 10. Alias analysis là lợi thế lớn

Ví dụ:

```axiom
fn add(
    a: view<f32>,
    b: view<f32>,
    out: mut_view<f32>
)
```

Compiler biết:

```text
out = WRITE
a = READ
b = READ
```

Nếu provenance cho thấy regions disjoint:

```text id="u8tv11"
A ∩ OUT = ∅
B ∩ OUT = ∅
```

compiler có thể vectorize mạnh.

---

# 11. Nhưng không nên thêm `restrict` vào source

Đây là một quyết định tôi khuyến nghị.

Không cần:

```text id="6o4h9r"
restrict
noalias
restrict_mut
```

cho application code.

Compiler đã có:

```text id="z73l6j"
ownership
view
mut_view
provenance
region analysis
```

để suy ra rất nhiều alias facts.

---

# 12. Khi compiler không chứng minh được

Ví dụ unsafe:

```axiom
unsafe fn process(a: *mut f32, b: *mut f32) {
    ...
}
```

Compiler không biết alias.

Mặc định:

```text id="e1y2m5"
UNKNOWN
```

→ vectorization phải conservative.

Nếu programmer biết invariant:

```text id="m6zq8x"
a và b không overlap
```

có thể dùng explicit unsafe contract:

```text
@noalias(1, 2)
```

nhưng đây phải là **programmer assertion**, không phải safe guarantee.

---

# 13. `@noalias` không nên là keyword Core

Tôi đề xuất:

```text
@noalias
```

là compiler/system attribute.

Lý do:

- không cần trong 99% code
- có thể sai
- ảnh hưởng optimizer correctness
- cần audit như unsafe assumption.

---

# 14. Loop vectorization và bounds checks

Ví dụ:

```axiom id="tdw34e"
for i in 0..a.len() {
    out[i] = a[i] + b[i]
}
```

Mỗi:

```text id="7x2vhm"
a[i]
b[i]
out[i]
```

có thể conceptually có bounds check.

Nhưng compiler biết:

```text id="4qzmb3"
i < len
```

và có thể:

```text id="d7c8pk"
hoist/remove bounds checks
```

trước vector loop.

Do đó safe code vẫn có cơ hội tạo machine code như C.

---

# 15. Không cần `unchecked` để đạt performance thông thường

Đây là mục tiêu quan trọng.

Cách tiếp cận không nên là:

```text
safe code = slow
unsafe code = fast
```

Mà:

```text
safe semantics
      ↓
optimizer proves safety
      ↓
checks disappear
      ↓
fast machine code
```

Unsafe chỉ cần khi programmer muốn thực hiện operation compiler **không thể chứng minh**.

---

# 16. Example

Source:

```axiom id="s7v5l4"
fn sum(xs: view<i32>) -> i64 {
    var result: i64 = 0

    for x in xs {
        result += x as i64
    }

    result
}
```

Compiler có thể tạo:

```text id="g5t7kq"
load vector
extend i32 → i64
horizontal/add
reduce
```

không cần programmer biết SIMD.

---

# 17. Reduction

Reduction là workload compiler cần đặc biệt hỗ trợ:

```text id="k6z7yx"
sum
min
max
dot product
count
any
all
```

Ví dụ:

```axiom id="8x0z5w"
xs.reduce(0, |a, b| a + b)
```

có thể vectorize nếu semantics cho phép.

---

# 18. Floating-point reduction

Đây là vấn đề quan trọng.

Ví dụ:

```text
(a + b) + c
```

không nhất thiết bằng:

```text
a + (b + c)
```

do floating-point rounding.

Do đó compiler **không được tự ý reassociate**:

```text id="7c7z9k"
(a+b)+c → a+(b+c)
```

trong default semantics.

Nếu muốn:

```text id="0yq1g4"
fast math
```

phải explicit.

---

# 19. Fast math

Có thể có profile/attribute:

```text id="6m0k9e"
@fast_math
```

hoặc compiler option.

Nó cho phép:

- reassociation
- relaxed NaN handling
- relaxed signed-zero behavior
- approximate reciprocal
- FMA transformations.

Nhưng **không phải default**.

---

# 20. Integer vector overflow

Axiom đã định nghĩa:

```text id="2z4q0d"
checked
wrapping
saturating
```

Do đó SIMD phải giữ đúng semantics.

Ví dụ:

```axiom
a +% b
```

→ wrapping vector add.

```axiom
a +| b
```

→ saturating vector add.

Nếu CPU có instruction phù hợp, dùng trực tiếp.

Nếu không:

```text id="px4r8b"
legalize into equivalent operations
```

---

# 21. Alignment

Không nên bắt mọi vector phải aligned.

Ví dụ:

```text id="1j48a9"
view<T>
```

không đảm bảo alignment SIMD cao.

Compiler có thể:

```text id="g1p5xj"
unaligned load
```

hoặc:

```text id="c9k0tz"
runtime alignment check
    ├── aligned fast path
    └── unaligned fallback
```

Nếu programmer biết alignment:

```axiom id="o8e8is"
@align(32)
```

thì compiler có thể tận dụng.

---

# 22. `assume_aligned`

Có thể có unsafe intrinsic:

```text id="1m5x7f"
assume_aligned(ptr, 32)
```

nhưng nếu assertion sai:

```text id="yq6b8d"
program invalid
```

Đây phải được coi là optimizer contract, không phải safe hint bình thường.

---

# 23. AoS

Thông thường:

```axiom id="c9u1xq"
struct Particle {
    position: Vec3
    velocity: Vec3
    mass: f32
}
```

và:

```axiom
Vec<Particle>
```

là AoS:

```text id="6e4i3x"
P0 P0 P0
P1 P1 P1
P2 P2 P2
```

Tốt khi xử lý từng object.

---

# 24. SoA

Trong simulation:

```text id="6b4i7d"
positions
velocities
masses
```

có locality tốt hơn nếu chỉ xử lý position.

Không nên đưa:

```text
soa struct
```

thành Core language feature.

Library có thể cung cấp:

```text id="s6l1wu"
SoA<T>
```

hoặc code generator.

---

# 25. AoSoA

Đối với SIMD-heavy workloads:

```text id="l6u4eg"
Array of Structs of Arrays
```

thường rất hiệu quả.

Ví dụ:

```text id="q6e3kr"
chunk[0]
  x[0..7]
  y[0..7]
  z[0..7]

chunk[1]
  x[8..15]
  ...
```

Đây hoàn toàn nên là library/data-layout abstraction.

---

# 26. Data layout phải explicit khi performance-critical

Axiom không nên tự động biến:

```text
Vec<Particle>
```

thành SoA.

Vì layout có thể observable qua:

- FFI
- pointer/address
- iteration semantics
- serialization
- cache behavior.

Compiler có thể scalarize/reorganize **khi không observable**, nhưng không nên âm thầm thay đổi semantic collection layout contract.

---

# 27. Data-oriented API

Thay vì:

```axiom
particles[i].position.x
```

mọi nơi, library có thể cung cấp:

```axiom
particles.positions()
particles.velocities()
```

trả về views.

Ví dụ:

```axiom id="k1y6p8"
fn integrate(
    positions: mut_view<Vec3>,
    velocities: view<Vec3>,
    dt: f32
)
```

Compiler thấy:

```text id="4p9k8x"
WRITE positions
READ velocities
```

→ rất thuận lợi vectorization.

---

# 28. Cache locality

Axiom không nên có một keyword cho cache locality.

Compiler có thể cung cấp diagnostics:

```text
axiom perf
```

và library:

```text id="d9u0pn"
CachePadded<T>
Aligned<T>
SoA<T>
AoSoA<T>
```

Như vậy language không bị ô nhiễm bởi microarchitecture.

---

# 29. Prefetch

Explicit prefetch có thể tồn tại:

```text id="1k1i8f"
prefetch(ptr)
```

nhưng là system intrinsic.

Compiler cũng có thể tự thêm prefetch nếu cost model cho phép.

Không nên expose nó trong normal high-level API.

---

# 30. Branch prediction

Không cần:

```text
likely()
unlikely()
```

ở Core.

Có thể có compiler hint:

```text
@cold
@hot
```

và:

```text
@likely
@unlikely
```

nhưng đây là optimization hints, không semantic.

Nếu hint sai:

```text
program vẫn đúng
```

đó là điều kiện bắt buộc.

---

# 31. `@cold`

Rất hữu ích cho:

```text id="b0s8un"
error path
panic path
logging
slow fallback
```

Compiler có thể:

- tách cold block
- tối ưu I-cache
- giảm code layout pressure.

---

# 32. `@hot`

Có thể gợi ý:

```text id="8rj2lp"
hot loop
```

nhưng compiler profile-guided optimization vẫn đáng tin hơn.

---

# 33. PGO

Axiom nên hỗ trợ:

```text id="kq30d4"
Profile Guided Optimization
```

pipeline:

```text
build instrumented
       ↓
run workload
       ↓
profile
       ↓
rebuild
       ↓
PGO optimizer
```

Không phải language semantic.

---

# 34. LTO

Nên hỗ trợ:

```text id="xj5j61"
LTO
ThinLTO
whole-program optimization
```

vì đây là một trong những cách compiler có thể vượt compiler C truyền thống nếu có semantic information tốt hơn.

---

# 35. Ownership giúp optimizer biết nhiều hơn C

C compiler thường gặp:

```c
void f(float *a, float *b, float *out)
```

Không chắc:

```text
a == out?
b == out?
```

Axiom:

```axiom
fn f(
    a: view<f32>,
    b: view<f32>,
    out: mut_view<f32>
)
```

có semantic capability constraints.

Compiler có thể tận dụng chúng.

Đây có thể là **một lợi thế kiến trúc thực sự** của Axiom.

---

# 36. Nhưng không nên overclaim

Không phải cứ có `view` là mọi alias đều disjoint.

Ví dụ:

```axiom id="1c0t7q"
let a = view(buffer)
let b = view(buffer)
```

hai READ views có thể overlap.

Compiler phải biết:

```text id="x3n7gk"
READ + READ → safe
```

nhưng không được tự suy ra:

```text
a ∩ b = ∅
```

---

# 37. `mut_view` tạo noalias opportunity

Ví dụ:

```axiom
fn transform(
    input: view<f32>,
    output: mut_view<f32>
)
```

Nếu compiler chứng minh regions không overlap:

```text id="8y9p9k"
input ≠ output
```

có thể tạo LLVM-like noalias internal metadata hoặc equivalent Axiom LIR fact.

Nhưng:

> **Noalias là optimizer fact được suy ra từ semantics, không phải source syntax bắt programmer quản lý.**

---

# 38. Loop canonicalization

Compiler nên biến:

```axiom
for i in 0..n {
    ...
}
```

thành canonical loop:

```text
preheader
header
body
latch
exit
```

Sau đó:

```text id="m4e2lm"
LICM
unroll
vectorize
interleave
bounds-check elimination
```

---

# 39. Generic + SIMD

Generic code:

```axiom id="u9s6ez"
fn add<T: Add>(
    a: view<T>,
    b: view<T>,
    out: mut_view<T>
)
```

có thể monomorphize:

```text
add<i32>
add<f32>
add<Vector<f32,8>>
```

Compiler nhìn thấy concrete operations.

Do đó generic abstraction có thể biến mất hoàn toàn.

Đây chính là:

```text
Generic
 ↓
Monomorphization
 ↓
Optimization
 ↓
SIMD
```

---

# 40. SIMD và FFI

Nếu:

```axiom
extern "C" fn process(v: Vector<f32, 8>)
```

thì representation phải được xác định rõ.

Nếu không có ABI contract:

```text id="5d6u8x"
Vector<T,N>
```

không nên được truyền qua FFI.

Có thể dùng explicit:

```text id="d9y8yk"
@repr(simd)
```

nếu sau này cần.

Nhưng `repr(simd)` chỉ nên dùng khi ABI thực sự yêu cầu.

---

# 41. GPU boundary

GPU không nên bị ép thành:

```text
Vector<T,N>
```

vì GPU programming có execution model riêng:

```text id="0m58z0"
threads
warps/wavefronts
shared memory
barriers
address spaces
kernels
```

Để sau phần CPU SIMD, ta sẽ thiết kế:

```text id="2f7r4q"
Axiom GPU/System Layer
```

chứ không nhồi vào Core.

---

# 42. SIMD invariants

Chốt:

```text id="l5p4kq"
ASIMD-01  SIMD Is A Semantic Vector Abstraction
ASIMD-02  Vector Width Is Not CPU Register Width
ASIMD-03  Auto-Vectorization Is Preferred
ASIMD-04  SIMD Does Not Require Unsafe
ASIMD-05  Scalar Fallback Is Always Semantically Valid
ASIMD-06  Vector Semantics Preserve Integer Overflow Rules
ASIMD-07  Float Reassociation Is Not Allowed By Default
ASIMD-08  Fast-Math Is Explicit
ASIMD-09  Alignment Is Explicit When Required
ASIMD-10  Auto-Vectorization May Remove Bounds Checks
ASIMD-11  Alias Analysis Feeds Vectorization
ASIMD-12  @noalias Is An Explicit Unsafe/Compiler Contract
ASIMD-13  SIMD Intrinsics Are Library/System Layer
ASIMD-14  CPU Feature Dispatch Is Explicit
ASIMD-15  Data Layout Is Independent From SIMD Semantics
ASIMD-16  AoS/SoA/AoSoA Are Library Abstractions
ASIMD-17  Compiler May Scalarize Or Vectorize
ASIMD-18  SIMD ABI Requires Explicit Representation
ASIMD-19  PGO/LTO Are Compiler Optimizations
ASIMD-20  Performance Hints Never Change Correctness
```

---

# 43. Một điểm rất đáng chú ý cho Axiom

Sau các phần ownership + views + concurrency + SIMD, Axiom đang có một đặc điểm mà tôi cho rằng nên trở thành **mục tiêu thiết kế chính thức**:

```text
                 Programmer
                     │
          expresses semantics
                     │
                     ▼
              Axiom Compiler
                     │
       ┌─────────────┼─────────────┐
       │             │             │
   ownership      aliasing      effects
       │             │             │
       └─────────────┼─────────────┘
                     ▼
               optimization
                     │
          ┌──────────┼──────────┐
          │          │          │
        scalar     SIMD       parallel
          │          │          │
          └──────────┼──────────┘
                     ▼
                 machine code
```

Tức là programmer **không cần lựa chọn trước**:

> “Tôi phải viết scalar hay SIMD?”

> “Tôi phải dùng pointer hay reference?”

> “Tôi phải manually annotate noalias?”

> “Tôi phải manually manage lifetime?”

Compiler có đủ semantic information để tự quyết định trong phần lớn trường hợp.

Đây là hướng có khả năng làm Axiom **đơn giản ở source nhưng không đơn giản ở compiler** — chính xác với mục tiêu bạn đặt ra từ đầu.

---

## Tiếp tục → GPU / heterogeneous computing

Bước tiếp theo hợp lý là **GPU + accelerator + heterogeneous memory**, sau đó mới chuyển sang OS/platform abstraction.

Ở phần đó cần quyết định một vấn đề lớn:

```text
CPU memory
GPU memory
shared/unified memory
device memory
DMA
address spaces
kernel
```

có nên trở thành **type/semantic system của Axiom**, hay chỉ là library/FFI abstraction.

Tôi sẽ tiếp tục theo hướng **không đưa GPU vào Core nếu compiler không cần nó để chứng minh safety**, nhưng vẫn phải đảm bảo Axiom đủ mạnh để viết CUDA/Metal/Vulkan-like workloads mà không bị bó tay.