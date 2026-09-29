# BOOTSTRAP-148 — Vectorization, SIMD & Auto-Vectorization Engine
**STATUS: FROZEN / COMPLETED**

> **Axiom phải biến các vòng lặp dữ liệu song song thành SIMD khi compiler chứng minh được tính đúng đắn và target có lợi, mà không bắt programmer viết intrinsic, pointer arithmetic, `restrict` hay `unsafe`.**

Đây là tầng biến semantic loop thành **data-parallel machine computation**.

---

## 1. Vị trí

```text
Verified MIR
    ↓
Loop Analysis
    ↓
Range / Alias / MemorySSA
    ↓
Data Layout
    ↓
Scalar Evolution
    ↓
Vector Legality Analysis
    ↓
Vector Cost Model
    ↓
Vector Transformation
    ↓
Vector Cleanup / Epilogue
    ↓
Masked Vectorization
    ↓
Vector Optimization
    ↓
CPU Microarchitecture Optimization
    ↓
ABI MIR / LIR
```

---

# 2. Vectorization không phải là “thấy for là SIMD”

Ví dụ:

```ax
for i in 0..n {
    out[i] = a[i] + b[i];
}
```

Compiler phải chứng minh:

```text
1. iteration độc lập
2. memory accesses hợp lệ
3. không có aliasing nguy hiểm
4. bounds có thể chứng minh
5. floating-point semantics cho phép phép biến đổi
6. target có vector instruction phù hợp
7. vectorization có lợi hoặc ít nhất không gây chi phí bất hợp lý
```

Chỉ sau đó mới vectorize.

---

# 3. Vector Legality

Tạo subsystem:

```text
VectorLegalityAnalysis
```

kiểm tra:

```text
MemoryDependence
AliasInfo
RangeInfo
ScalarEvolution
EffectInfo
CapabilityInfo
FPMode
AtomicInfo
VolatileInfo
ControlFlow
```

### Ví dụ hợp lệ

```ax
for i in 0..n {
    c[i] = a[i] + b[i];
}
```

Nếu:

```text
a
b
c
```

được chứng minh không gây dependency nguy hiểm:

```text
iteration 0 ─┐
iteration 1 ─┼─ independent
iteration 2 ─┤
iteration 3 ─┘
```

thì vectorization khả thi.

---

# 4. Dependency giữa các iteration

Ví dụ:

```ax
for i in 1..n {
    a[i] = a[i - 1] + 1;
}
```

có:

```text
iteration i
    ↓
a[i]

iteration i+1
    ↓
a[i+1]
```

và:

```text
a[i] depends on a[i-1]
```

Đây là loop-carried dependency.

Không thể đơn giản biến thành:

```text
SIMD independent iterations
```

nếu không có transformation đặc biệt.

Compiler phải từ chối vectorization thông thường.

---

# 5. Alias proof

Đây là nơi các tầng trước phát huy tác dụng.

```ax
fn add(
    a: view<f32>,
    b: view<f32>,
    out: mut_view<f32>
)
```

Không cần:

```text
restrict
```

Compiler dùng capability + region:

```text
Region(A)
Region(B)
Region(OUT)
```

Nếu chứng minh:

```text
A ∩ OUT = ∅
B ∩ OUT = ∅
```

thì vectorization được phép.

Nếu:

```text
UNKNOWN
```

thì không được giả định độc lập.

---

# 6. Runtime alias check

Một trường hợp thú vị:

Compiler không chứng minh được tĩnh:

```text
a và b có overlap?
```

nhưng có thể kiểm tra rất rẻ runtime.

Có thể tạo:

```text
if proven_nonoverlap(a, b) {
    vector_loop()
} else {
    scalar_loop()
}
```

Đây là **optimization guard**, không phải safety mechanism.

Quan trọng:

> Runtime check chỉ cho phép chọn optimization path; nó không thay thế safety verification.

---

# 7. Vector width

Compiler không cố định:

```text
vector = 4 elements
```

mà chọn:

```text
VectorWidth {
    lanes
    element_type
    register_bits
    mask_width
}
```

Ví dụ `f32`:

```text
128-bit → 4 lanes
256-bit → 8 lanes
512-bit → 16 lanes
```

nhưng lựa chọn thực tế phụ thuộc:

```text
target ISA
microarchitecture
register pressure
memory bandwidth
loop size
alignment
code size
```

---

# 8. Không phải vector càng rộng càng nhanh

Ví dụ:

```text
128-bit
256-bit
512-bit
```

Compiler phải cân nhắc:

```text
instruction count
register pressure
frequency behavior
memory bandwidth
spill
setup cost
tail handling
```

Do đó:

```text
maximum ISA width
```

không đồng nghĩa với:

```text
optimal vector width
```

---

# 9. Vector IR

Nên có abstraction trong OptIR:

```text
VectorType<T, Lanes>
```

và operations:

```text
VectorLoad
VectorStore
VectorAdd
VectorSub
VectorMul
VectorDiv
VectorFMA
VectorCompare
VectorSelect
VectorShuffle
VectorReduce
VectorMask
VectorBroadcast
```

Nhưng đây là **compiler IR**, không phải Core language primitive bắt buộc.

---

# 10. Scalar → Vector transformation

Scalar:

```text
for i in 0..n {
    out[i] = a[i] + b[i];
}
```

Conceptually:

```text
i = i + 8

vA = load(a[i..i+8])
vB = load(b[i..i+8])
vC = vA + vB
store(out[i..i+8], vC)
```

Sau đó backend quyết định:

```text
AVX2
AVX-512
NEON
SVE
RVV
...
```

---

# 11. Remainder / Epilogue

Nếu:

```text
n = 100
vector width = 8
```

thì:

```text
12 × 8 = 96
remainder = 4
```

Compiler cần xử lý:

```text
main vector loop
+
remainder loop
```

Ví dụ concept:

```text
for i in 0..96 step 8 {
    vector(...)
}

for i in 96..100 {
    scalar(...)
}
```

Nhưng programmer không thấy transformation này.

---

# 12. Masked vectorization

Trên ISA hỗ trợ mask tốt, compiler có thể thay remainder bằng masked operation:

```text
mask = i < n

load(mask)
compute(mask)
store(mask)
```

Điều này đặc biệt hữu ích với:

- AVX-512
- SVE
- RVV
- các ISA có predication mạnh.

---

# 13. Alignment

Axiom không bắt programmer viết:

```text
assume_aligned(...)
```

trong ordinary code.

Compiler có thể phân loại:

```text
KnownAligned
KnownUnaligned
RuntimeAligned
Unknown
```

Nếu alignment được chứng minh:

```text
aligned load
```

Nếu không:

```text
unaligned load
```

Compiler vẫn vectorize nếu target hỗ trợ.

Không được giả định alignment chỉ vì “thường là aligned”.

---

# 14. Vectorization và `mut_view`

Ví dụ:

```ax
fn scale(x: mut_view<f32>, k: f32) {
    for i in 0..x.len {
        x[i] *= k;
    }
}
```

`mut_view` đã cung cấp exclusive write capability.

Compiler có thể sử dụng capability proof để biết:

```text
x[i]
```

không bị một conflicting safe writer khác truy cập đồng thời trong cùng semantic context.

Do đó capability system không chỉ giúp safety.

Nó trở thành **nguồn thông tin tối ưu hóa rất mạnh**.

---

# 15. Reduction

Một loop:

```ax
var sum = 0.0;

for i in 0..n {
    sum += a[i];
}
```

có dependency:

```text
sum0 → sum1 → sum2 → sum3
```

nhưng compiler có thể tạo nhiều accumulator:

```text
s0
s1
s2
s3
```

sau đó:

```text
sum = s0 + s1 + s2 + s3
```

Đây là **reduction vectorization**.

---

# 16. Floating-point reduction

Đây là chỗ Axiom phải rất nghiêm.

Với floating-point:

```text
(a + b) + c
```

không nhất thiết bằng:

```text
a + (b + c)
```

về bit pattern.

Do đó default:

```text
strict FP semantics
```

không cho phép compiler tự ý reassociate.

Có thể có profile/mode:

```text
strict
relaxed
fast
```

Trong đó:

```text
strict
```

bảo toàn phép tính theo semantics chuẩn của Axiom.

---

# 17. Horizontal reductions

Compiler có thể hạ:

```text
VectorReduceAdd
```

thành target instruction sequence.

Ví dụ:

```text
v0
 ↓
pairwise reduction
 ↓
scalar
```

Target-specific backend quyết định instruction cụ thể.

---

# 18. Gather / Scatter

Không phải dữ liệu nào cũng contiguous:

```ax
for i in 0..n {
    out[i] = table[index[i]];
}
```

Compiler có thể xem xét:

```text
gather
```

nhưng phải cân nhắc cost.

Không có gather tốt hoặc locality quá tệ:

```text
scalar
```

có thể nhanh hơn.

---

# 19. Interleaving

Compiler có thể kết hợp vectorization với instruction scheduling:

```text
load vector 0
load vector 1
compute vector 0
load vector 2
compute vector 1
store vector 0
...
```

để che latency.

Đây là điểm nối trực tiếp với **BOOTSTRAP-147**.

---

# 20. Loop versioning

Một kỹ thuật rất phù hợp với Axiom:

```text
runtime precondition
        ↓
┌───────┴────────┐
YES               NO
 ↓                 ↓
vector loop       scalar loop
```

Ví dụ runtime có thể kiểm tra:

```text
non-overlap
alignment
trip count
```

Nếu check rẻ và vector loop nhanh hơn đáng kể, compiler có thể tự sinh versioning.

---

# 21. Small-loop handling

Vectorization có overhead.

Nếu:

```text
n = 3
```

thì tạo vector setup có thể không đáng.

Compiler cost model cần:

```text
TripCountEstimate
VectorSetupCost
EpilogueCost
ExpectedSpeedup
```

để quyết định.

PGO có thể cải thiện quyết định này.

---

# 22. Predication

Control flow:

```ax
for i in 0..n {
    if a[i] > 0 {
        out[i] = a[i];
    }
}
```

có thể trở thành:

```text
load vector
compare vector
mask
select/store masked
```

nếu target phù hợp.

Nhưng compiler phải bảo đảm rằng việc thực hiện các phép tính “không được chọn” không tạo observable effect.

Ví dụ function call có side effect không thể tùy tiện thực hiện cả hai nhánh.

---

# 23. Calls trong vector loop

Loop:

```ax
for i in 0..n {
    out[i] = transform(a[i]);
}
```

Nếu:

```text
transform
```

pure/side-effect-limited và có thể inline:

```text
inline
→ scalarize
→ vectorize
```

Nếu có:

```text
IO
atomic
foreign
unknown side effects
```

thì vectorization bị hạn chế hoặc từ chối.

Đây là nơi:

```text
EffectInfo
+
Inlining
+
VectorLegality
```

phối hợp.

---

# 24. SIMD và generic code

Ví dụ:

```ax
fn add<T: Numeric>(...)
```

Không nên ép mọi `T` thành cùng một implementation.

Compiler có thể specialization:

```text
f32 → SIMD
f64 → SIMD
i32 → SIMD
custom type → scalar
```

Generic semantics vẫn giống nhau.

Đây chính là:

```text
Generic
 ↓
Specialization
 ↓
Vectorization
```

---

# 25. SIMD và fixed arrays

Axiom đã quy định fixed array:

```text
[T; N]
```

có semantic order và contiguous representation.

Điều này rất thuận lợi cho vectorization.

Compiler có thể scalarize/vectorize:

```ax
let a: [f32; 1024];
```

mà không thay đổi semantic representation guarantee.

---

# 26. SIMD và SoA

Với data-oriented code:

```ax
struct Particle {
    position: Vec3,
    velocity: Vec3,
    mass: f32
}
```

compiler có thể tối ưu layout nếu representation không observable.

Nhưng khi programmer cần guaranteed SoA semantics:

```text
SoA<Particle>
```

thì std library nên cung cấp abstraction rõ ràng.

Vectorizer có thể hiểu container đó trực tiếp.

---

# 27. GPU

Cùng một abstraction:

```text
VectorOperation
```

không nhất thiết chỉ dành cho CPU.

Pipeline có thể phân nhánh:

```text
Vector IR
   ├── CPU SIMD
   └── GPU vector/thread mapping
```

Tuy nhiên GPU có execution model khác CPU.

Do đó không nên giả định:

```text
CPU SIMD = GPU execution
```

Chúng chia sẻ semantic data-parallel reasoning nhưng backend khác nhau.

---

# 28. Vectorization phải giữ ownership

Một transformation:

```text
4 scalar loads
```

→

```text
1 vector load
```

không được tạo thêm ownership.

Semantic:

```text
read x0
read x1
read x2
read x3
```

vẫn là:

```text
read x0
read x1
read x2
read x3
```

chỉ physical representation khác.

---

# 29. Vectorization và Drop

Không được vectorize một aggregate theo kiểu phá Drop semantics.

Ví dụ:

```text
T có custom Drop
```

thì compiler phải bảo đảm:

```text
exactly-once destruction
correct order
```

Nếu không thể giữ semantics:

```text
vectorization rejected
```

Trivial Drop thì có thể được erase.

---

# 30. Vectorization và atomics

Ví dụ:

```ax
for i in 0..n {
    atomic_add(counter, 1);
}
```

Không được biến tùy tiện thành:

```text
counter += n
```

vì atomic semantics có thể khác.

Compiler chỉ được thực hiện reduction nếu transformation bảo toàn:

```text
atomicity
ordering
visibility
synchronization
```

---

# 31. Vectorization và volatile

`volatile` là observable machine interaction.

Do đó:

```text
volatile load/store
```

không được gộp tùy tiện thành vector load/store.

Backend phải bảo toàn volatile semantics.

---

# 32. Vectorization pipeline

Đóng băng pipeline:

```text
Loop
 ↓
Canonical Loop
 ↓
Scalar Evolution
 ↓
Range Analysis
 ↓
Dependence Analysis
 ↓
Alias Analysis
 ↓
MemorySSA
 ↓
Vector Legality
 ↓
Vector Cost
 ↓
Vector Transform
 ↓
Vector Cleanup
 ↓
Masked/Epilogue
 ↓
Vector Simplification
 ↓
Instruction Selection
```

---

# 33. Vector IR canonical form

Đề xuất:

```text
VectorType
VectorValue
VectorLoad
VectorStore
VectorBroadcast
VectorExtract
VectorInsert
VectorShuffle
VectorCompare
VectorSelect
VectorAdd/Sub/Mul/Div
VectorFMA
VectorReduce
VectorMask
VectorGather
VectorScatter
```

Không nhất thiết tất cả đều xuất hiện trong Core v0.1.

Đây là **compiler IR vocabulary**.

---

# 34. AI inspect

Thêm:

```text
axc inspect vectorize foo
axc inspect vectorize foo --loop 3
axc inspect vector-cost foo
axc inspect vector-dependence foo
```

Ví dụ:

```text
Loop #3
  Vectorized: YES
  Element: f32
  Width: 8
  Target: AVX2

  Alias:
    a/out = NO_ALIAS
    b/out = NO_ALIAS

  Bounds:
    proven

  Alignment:
    unknown

  Epilogue:
    scalar, 4 elements

  Estimated:
    scalar iterations: 100
    vector iterations: 12
    expected gain: high
```

Nếu thất bại:

```text
Vectorized: NO

Reason:
  loop-carried dependency detected
```

---

# 35. Invariants

Đóng băng:

### `AVEC-20`
Vectorization must preserve observable semantics.

### `AVEC-21`
Vectorization requires a proven legal transformation.

### `AVEC-22`
Unknown aliasing cannot be treated as independent.

### `AVEC-23`
Loop-carried dependencies must be respected.

### `AVEC-24`
Bounds safety must already be established by semantic verification.

### `AVEC-25`
Runtime checks may guard optimizations but cannot replace safety verification.

### `AVEC-26`
Vector width is target-dependent.

### `AVEC-27`
Maximum vector width is not inherently optimal.

### `AVEC-28`
Vectorization profitability must include setup and epilogue cost.

### `AVEC-29`
Register pressure participates in vectorization profitability.

### `AVEC-30`
Floating-point reassociation requires permitted FP semantics.

### `AVEC-31`
Atomic semantics must be preserved.

### `AVEC-32`
Volatile semantics must be preserved.

### `AVEC-33`
Foreign/observable effects constrain vectorization.

### `AVEC-34`
Drop and ownership semantics must remain exactly correct.

### `AVEC-35`
Capability proofs may provide alias/disjointness information.

### `AVEC-36`
Vectorization cannot create ownership/capability proofs.

### `AVEC-37`
Scalar remainder handling must preserve semantics.

### `AVEC-38`
Masked vectorization must not introduce forbidden side effects.

### `AVEC-39`
Generic specialization may expose vectorization opportunities.

### `AVEC-40`
SIMD representation is compiler/backend machinery, not mandatory Core syntax.

### `AVEC-41`
CPU SIMD and GPU execution are distinct execution models.

### `AVEC-42`
Target feature availability must be verified before emission.

### `AVEC-43`
Optimization guards are semantic-preserving fast-path mechanisms.

### `AVEC-44`
PGO may influence profitability but never legality.

### `AVEC-45`
Vectorization remains deterministic under reproducible compilation.

### `AVEC-46`
Source→loop→vector transformation provenance remains inspectable.

### `AVEC-47`
Failed vectorization reduces optimization only; it never changes program validity.

---

# Kết quả kiến trúc

Axiom hiện có một chuỗi tối ưu dữ liệu khá hoàn chỉnh:

```text
                PROGRAM
                   ↓
              Semantic MIR
                   ↓
             Verification
                   ↓
          ┌────────┼────────┐
          ↓        ↓        ↓
        Alias    Effect   Escape
          └────────┼────────┘
                   ↓
            MemorySSA / SSA
                   ↓
                OptIR
                   ↓
        ┌──────────┼──────────┐
        ↓          ↓          ↓
      Loop       Memory     Layout
        ↓          ↓          ↓
        └──────────┼──────────┘
                   ↓
              Vectorization
                   ↓
          Microarchitecture
                   ↓
                 LIR
                   ↓
               Machine
```

Đây là điểm rất quan trọng đối với mục tiêu ban đầu của Axiom: **programmer viết code cấp cao nhưng compiler vẫn có đủ thông tin để sinh code gần với code mà một programmer C/C++ tối ưu thủ công có thể viết.**

---

# BOOTSTRAP-149 — Profile-Guided Optimization, Auto-Tuning & Feedback-Directed Compilation

Task tiếp theo nên xử lý vấn đề còn thiếu ở tầng optimization:

> Compiler có rất nhiều lựa chọn hợp lệ — inline hay không, vector width 128/256/512, unroll bao nhiêu, layout nào, branch nào hot, specialization nào đáng tạo — nhưng compiler tĩnh không phải lúc nào cũng biết lựa chọn nào nhanh nhất trên **chương trình thực tế + CPU thực tế**.

Vì vậy 149 sẽ xây dựng:

```text
Build
  ↓
Instrument
  ↓
Run / Collect Profile
  ↓
Profile Database
  ↓
Hotness / Branch / Call / Loop / Memory Data
  ↓
Optimization Feedback
  ├── Inlining
  ├── Specialization
  ├── Vectorization
  ├── Loop Unrolling
  ├── Data Layout
  ├── Branch Layout
  ├── Code Splitting
  └── CPU Scheduling
  ↓
Optimized Binary
```

Đặc biệt cần thiết kế để **PGO không biến compiler thành một hệ thống benchmark tùy tiện, không deterministic hoặc làm thay đổi semantics**.