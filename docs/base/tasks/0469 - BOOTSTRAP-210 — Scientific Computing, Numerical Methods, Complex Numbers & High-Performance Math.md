# BOOTSTRAP-210 — Scientific Computing, Numerical Methods, Complex Numbers & High-Performance Math

**TRẠNG THÁI: FROZEN / COMPLETED**

Mục tiêu của 210:

> **Axiom phải đủ mạnh để xây dựng scientific computing, physics, engineering, simulation, HPC, statistics và numerical AI mà không biến toàn bộ hệ toán học thành Core language.**

Nguyên tắc:

```text
Core
 │
 ├── Integer / Float
 ├── SIMD
 ├── Generic
 ├── Comptime
 └── Tensor
       │
       ▼
 Numerical Library
       │
 ├── Complex
 ├── Rational
 ├── BigInt
 ├── BigFloat
 ├── Linear Algebra
 ├── FFT
 ├── Statistics
 ├── ODE/PDE
 └── Optimization
```

---

## 210.1. Không đưa mọi numeric type vào Core

Core chỉ giữ:

```text
i8..i64
u8..u64
isize
usize
f32
f64
```

Các loại:

```text
complex
rational
decimal
bigint
bigfloat
interval
dual
quaternion
```

là library types.

Điều này giữ Core nhỏ nhưng không giới hạn khả năng toán học.

---

# 210.2. Numeric trait hierarchy

Không tạo một `Number` khổng lồ.

Nên có các capability riêng:

```text
Add
Sub
Mul
Div
Neg
Zero
One
Abs
Sqrt
Exp
Log
Sin
Cos
Pow
```

Một type chỉ implement những operation có ý nghĩa.

---

# 210.3. Algebraic traits

Có thể biểu diễn:

```text
Semigroup
Monoid
Group
Ring
Field
```

ở library/math layer.

Không bắt buộc mọi numeric type phải implement toàn bộ.

---

# 210.4. Complex

```text
Complex<f32>
Complex<f64>
```

là generic type.

Conceptually:

```text
Complex<T>
    real: T
    imag: T
```

Compiler có thể scalarize hoặc vectorize.

---

# 210.5. Complex không cần runtime object

Không có:

```text
ComplexObject
```

hay object header.

Một `Complex<f64>` có thể compile xuống hai thanh ghi FP.

---

# 210.6. Complex arithmetic

Compiler có thể recognize:

```text
a + b
a * b
conj(a)
abs(a)
```

và generate optimized instructions.

---

# 210.7. Quaternion

```text
Quaternion<f32>
Quaternion<f64>
```

library abstraction.

Đặc biệt hữu ích cho:

```text
3D rotation
robotics
simulation
graphics
```

---

# 210.8. Rational

```text
Rational<I>
```

với:

```text
numerator
denominator
```

Invariant:

```text
denominator != 0
```

và normalization tùy implementation.

---

# 210.9. BigInt

`BigInt` không phải primitive machine integer.

Nó là:

```text
heap-backed / arena-backed arbitrary precision value
```

và:

```text
!Copy
```

nếu implementation lớn.

---

# 210.10. BigInt allocation

Compiler không được giả định:

```text
BigInt = fixed size
```

nhưng library có thể tối ưu small values:

```text
SmallInt
   ↓
inline
```

và chỉ allocate khi vượt giới hạn.

---

# 210.11. BigFloat

```text
BigFloat
```

có precision runtime/compile-time.

Ví dụ conceptual:

```text
BigFloat<256>
```

hoặc:

```text
BigFloat<DynamicPrecision>
```

---

# 210.12. Precision là semantic

Không được silently chuyển:

```text
BigFloat<256>
→
f64
```

nếu có nguy cơ mất precision.

Phải explicit.

---

# 210.13. Decimal

Financial/scientific decimal có thể là library type:

```text
Decimal<P,S>
```

với precision/scale rõ ràng.

---

# 210.14. Interval arithmetic

```text
Interval<f64>
```

biểu diễn:

```text
[lower, upper]
```

Mục tiêu:

> kết quả thật phải nằm trong interval theo rounding contract.

---

# 210.15. Directed rounding

Interval arithmetic có thể cần:

```text
round_down
round_up
```

Compiler/backend phải hỗ trợ primitive khi target có.

---

# 210.16. NaN và Infinity

Axiom giữ semantic FP rõ ràng:

```text
NaN
+Infinity
-Infinity
-0
```

Không được compiler tùy tiện coi NaN là impossible trong strict FP.

---

# 210.17. Numerical equality

Không mặc định:

```text
a == b
```

là numerical approximate equality.

Phải phân biệt:

```text
ExactEqual
ApproxEqual
ULPDistance
```

---

# 210.18. Approximate equality

Library có thể:

```text
approx_eq(a, b, tolerance)
```

với policy:

```text
absolute tolerance
relative tolerance
ULP tolerance
```

---

# 210.19. ULP

Math library có thể expose:

```text
ulp_distance(a, b)
```

nhưng phải định nghĩa rõ NaN/infinity behavior.

---

# 210.20. Numerical stability là semantic documentation

Algorithm có thể ghi:

```text
Stable
ConditionallyStable
Unstable
```

để tooling/AI biết.

Đây không nhất thiết là compiler type.

---

# 210.21. Condition number

Linear algebra API có thể expose:

```text
condition_number(A)
```

và diagnostics:

```text
ill_conditioned
```

---

# 210.22. Linear algebra

Foundation:

```text
Vector
Matrix
Tensor
```

nhưng Matrix không phải một object hierarchy.

---

# 210.23. Matrix layout

Hỗ trợ:

```text
RowMajor
ColumnMajor
Strided
Blocked
Packed
```

---

# 210.24. Matrix view

```text
MatrixView<T>
```

chỉ là semantic view trên storage.

Không copy khi slicing/submatrix nếu layout cho phép.

---

# 210.25. BLAS

Library có thể cung cấp:

```text
BLAS-1
BLAS-2
BLAS-3
```

với backend:

```text
Axiom native
CPU SIMD
vendor library
GPU
```

---

# 210.26. Vendor math libraries

Axiom không cấm dùng:

```text
MKL
OpenBLAS
BLIS
cuBLAS
Accelerate
```

nhưng chúng là optional backend/FFI.

Core semantics không phụ thuộc chúng.

---

# 210.27. Linalg backend abstraction

```text
Matrix
   │
   ▼
Linalg operation
   │
 ┌─┼─────────────┐
 ▼ ▼             ▼
CPU GPU      Vendor BLAS
```

---

# 210.28. GEMM

`matmul` là operation đặc biệt quan trọng.

Compiler có thể chọn:

```text
naive
blocked
SIMD
BLAS
GPU kernel
```

dựa trên cost model.

---

# 210.29. Tiling

Compiler có thể tự động chọn:

```text
M tile
N tile
K tile
```

theo cache/register/GPU shared-memory characteristics.

---

# 210.30. Matrix multiplication specialization

Nếu:

```text
M,N,K
```

known at compile time, compiler có thể specialize.

Nếu dynamic, sử dụng runtime dispatch/kernel selection.

---

# 210.31. Sparse linear algebra

Các representation:

```text
CSR
CSC
COO
BSR
ELL
Hybrid
```

là library types.

---

# 210.32. Sparse matrix semantics

Logical matrix:

```text
M × N
```

không phụ thuộc storage format.

Điều này cho phép compiler/library đổi representation.

---

# 210.33. FFT

FFT library:

```text
fft
ifft
rfft
irfft
```

với planner/cache.

---

# 210.34. FFT planning

Planner có thể chọn:

```text
radix-2
radix-4
mixed-radix
Bluestein
Rader
```

tùy kích thước.

---

# 210.35. FFT cache

Plan cache fingerprint:

```text
size
dtype
layout
target
CPU/GPU
direction
optimization profile
```

---

# 210.36. FFT numerical profile

Strict mode giữ định nghĩa numerical behavior.

Fast mode có thể cho phép backend-specific approximation.

---

# 210.37. Polynomial

```text
Polynomial<T>
```

với:

```text
evaluate
differentiate
integrate
multiply
divide
roots
```

---

# 210.38. Symbolic vs numerical

Axiom cần phân biệt:

```text
SymbolicExpression
```

với:

```text
NumericalExpression
```

Symbolic algebra là library/tooling layer.

---

# 210.39. Compile-time symbolic computation

Comptime có thể xây symbolic utilities:

```text
comptime
    derive(...)
```

nhưng generated code vẫn phải đi qua compiler.

---

# 210.40. ODE

ODE solver API:

```text
solve_ode(...)
```

với methods:

```text
Euler
RK4
RK45
BDF
Adams
```

là library.

---

# 210.41. Adaptive stepping

Solver có thể dynamically chọn:

```text
step_size
```

dựa trên error estimate.

---

# 210.42. PDE

PDE framework có thể xây trên:

```text
Tensor
SparseMatrix
Mesh
LinearSolver
Parallel execution
GPU
```

Không cần PDE primitive trong language.

---

# 210.43. Mesh

Scientific mesh có:

```text
NodeId
ElementId
Cell
Face
Edge
```

dùng logical identity, không dùng raw address.

---

# 210.44. Simulation state

Simulation state là ordinary Axiom structs:

```text
State
Particle
Field
Grid
BoundaryCondition
```

Không cần object hierarchy.

---

# 210.45. Numerical optimization

Core library:

```text
GradientDescent
Newton
QuasiNewton
ConjugateGradient
Adam
LBFGS
```

---

# 210.46. Optimization objective

API có thể nhận:

```text
fn(x) -> loss
```

và AD infrastructure có thể generate gradient.

---

# 210.47. Constraint optimization

Hỗ trợ:

```text
bounds
equality constraints
inequality constraints
```

ở library level.

---

# 210.48. Statistics

Types:

```text
Mean
Variance
Covariance
Correlation
Distribution
```

---

# 210.49. Probability distributions

Ví dụ:

```text
Normal
Bernoulli
Binomial
Poisson
Uniform
Gamma
Beta
```

---

# 210.50. Random streams

Scientific random generator:

```text
Rng
```

khác CSPRNG.

Có thể:

```text
split()
jump()
fork()
```

để parallel simulation.

---

# 210.51. Reproducible RNG

Một simulation có thể xác định:

```text
seed
algorithm
stream
substream
```

để reproducibility.

---

# 210.52. Parallel RNG

Mỗi worker có independent stream.

Không dùng một global mutable RNG mặc định.

---

# 210.53. Units of measurement

Một tính năng rất đáng có ở math library:

```text
Quantity<f64, Meter>
Quantity<f64, Second>
```

Compiler có thể ngăn:

```text
meter + second
```

---

# 210.54. Dimension analysis

Ví dụ:

```text
Velocity = Meter / Second
Acceleration = Meter / Second^2
```

Dimension có thể được encode bằng const generics/comptime.

---

# 210.55. Zero-cost units

Nếu quantity chỉ chứa:

```text
f64
```

thì sau compilation:

```text
Meter<f64>
```

có thể có representation giống `f64`.

Unit metadata biến mất.

---

# 210.56. Physical constants

Có thể có:

```text
SpeedOfLight
PlanckConstant
BoltzmannConstant
```

nhưng version/precision phải rõ ràng.

---

# 210.57. Dimensional compile-time checking

Ví dụ conceptual:

```axiom
let distance: Quantity<f64, Meter>
let time: Quantity<f64, Second>

let velocity = distance / time
```

Compiler suy ra:

```text
Quantity<f64, MeterPerSecond>
```

---

# 210.58. Complex + units

Có thể biểu diễn:

```text
Complex<Quantity<f64, Voltage>>
```

nếu algebraic constraints cho phép.

---

# 210.59. Generic numerical algorithms

Algorithm nên viết trên constraints:

```text
fn norm<T: Floating>(x: view<T>) -> T
```

thay vì hard-code f64.

---

# 210.60. Generic specialization

Compiler có thể specialize:

```text
T = f32
T = f64
T = SIMD<f32, 8>
```

---

# 210.61. SIMD numeric types

Đã có SIMD architecture.

Math library có thể expose:

```text
Vec<f32, 8>
Mask<8>
```

hoặc compiler-native equivalents.

---

# 210.62. SIMD math

Operations:

```text
sin
cos
exp
log
sqrt
```

có thể map tới vector math backend.

---

# 210.63. Approximate vector math

Fast math có thể dùng approximations.

Strict numerical mode phải giữ required accuracy/semantics.

---

# 210.64. Math intrinsics

Compiler có thể recognize:

```text
sqrt
fma
reciprocal
rsqrt
exp
log
```

nhưng language semantics vẫn nằm ở standard library/compiler contract.

---

# 210.65. FMA

Nếu strict semantics cho phép fused operation theo định nghĩa FP, compiler có thể dùng FMA.

Nếu observable rounding khác:

```text
do not fuse
```

---

# 210.66. Extended precision

Backend có thể có:

```text
f80
quad
software precision
```

mà không bắt buộc Core type.

---

# 210.67. Arbitrary precision backend

BigFloat có thể chọn:

```text
software
hardware
MP backend
```

---

# 210.68. Precision-aware algorithms

CompilerDB có thể expose:

```text
precision
rounding
error bound
```

cho tooling.

---

# 210.69. Error propagation

Numerical library có thể track:

```text
absolute error
relative error
interval
condition estimate
```

nhưng không bắt buộc compiler phải formalize toàn bộ numerical analysis.

---

# 210.70. Numerical exceptions

Không biến FP exceptional condition thành C++-style exception.

Các API có thể trả:

```text
Result
```

hoặc sử dụng IEEE behavior tùy operation/profile.

---

# 210.71. Divide-by-zero

Integer và floating semantics vẫn khác nhau.

Integer:

```text
Result / panic / defined trap
```

theo operation semantics.

Floating:

```text
Infinity / NaN
```

theo FP semantics nếu operation cho phép.

---

# 210.72. Overflow

Integer numerical libraries phải dùng:

```text
checked
wrapping
saturating
```

explicit semantics.

---

# 210.73. Saturating arithmetic

Đặc biệt hữu ích cho:

```text
DSP
image processing
quantization
embedded
```

---

# 210.74. Fixed-point

Có thể có library:

```text
Fixed<I,F>
```

với:

```text
I = integer bits
F = fractional bits
```

---

# 210.75. Fixed-point zero-cost

Nếu parameters compile-time, representation có thể chỉ là integer machine value.

---

# 210.76. Interval + optimization

Interval arithmetic có thể hỗ trợ:

```text
verified bounds
constraint solving
numerical robustness
```

---

# 210.77. Numerical kernel contracts

Một math kernel có thể metadata:

```text
accuracy
domain
range
NaN behavior
Inf behavior
rounding
vectorizability
```

---

# 210.78. Domain restrictions

Ví dụ:

```text
sqrt(x)
```

với real x có domain:

```text
x >= 0
```

Library có thể cung cấp:

```text
sqrt
sqrt_checked
complex_sqrt
```

không để compiler đoán.

---

# 210.79. Numerical contracts không phải dependent type

Không cần biến mọi mathematical precondition thành compile-time theorem.

Compiler kiểm tra được thì kiểm tra.

Không kiểm tra được → runtime Result/contract.

---

# 210.80. Scientific computing invariants — `AMATH`

### `AMATH-20`
Advanced mathematical types shall remain library-level unless required as fundamental machine semantics.

### `AMATH-21`
Generic numerical algorithms shall be expressible through compositional traits.

### `AMATH-22`
Numeric traits shall not require a universal `Number` abstraction.

### `AMATH-23`
Complex numbers shall support zero-cost representation when the target permits.

### `AMATH-24`
Rational arithmetic shall preserve denominator validity.

### `AMATH-25`
Arbitrary-precision values shall remain explicit dynamic-size values.

### `AMATH-26`
Precision shall not be silently reduced.

### `AMATH-27`
Strict floating-point semantics shall preserve required IEEE-observable behavior.

### `AMATH-28`
Fast numerical profiles shall be explicit.

### `AMATH-29`
NaN and infinity behavior shall not be silently optimized away under strict FP semantics.

### `AMATH-30`
Exact equality and approximate numerical equality shall remain distinct.

### `AMATH-31`
ULP-based comparison shall define special-value behavior explicitly.

### `AMATH-32`
Numerical algorithms may expose stability and conditioning metadata.

### `AMATH-33`
Matrix and vector abstractions shall preserve explicit layout semantics.

### `AMATH-34`
Matrix views shall support zero-copy operation where representation permits.

### `AMATH-35`
BLAS/LAPACK-style operations shall support multiple backends.

### `AMATH-36`
Vendor math libraries shall remain optional implementations.

### `AMATH-37`
FFT plans shall be cacheable using complete semantic fingerprints.

### `AMATH-38`
FFT backend selection shall preserve the active numerical profile.

### `AMATH-39`
Sparse matrix logical semantics shall remain independent from physical storage format.

### `AMATH-40`
Numerical solvers shall distinguish approximation error from language errors.

### `AMATH-41`
Adaptive numerical algorithms shall not require GC or a monolithic runtime.

### `AMATH-42`
Parallel numerical algorithms shall explicitly define reduction ordering semantics.

### `AMATH-43`
Strict reductions shall preserve their defined numerical ordering.

### `AMATH-44`
Relaxed reductions may permit reassociation only under an explicit numerical profile.

### `AMATH-45`
Scientific RNG shall remain distinct from cryptographic RNG.

### `AMATH-46`
Parallel RNG streams shall support reproducible independent streams.

### `AMATH-47`
Units of measurement may be encoded using compile-time generic/comptime metadata.

### `AMATH-48`
Unit metadata may be erased completely when it has no runtime semantic effect.

### `AMATH-49`
Invalid dimensional operations shall be rejected when provable at compile time.

### `AMATH-50`
Runtime dimensional validation shall remain available when dimensions are dynamic.

### `AMATH-51`
Fixed-point arithmetic shall provide explicit overflow/rounding semantics.

### `AMATH-52`
Saturating arithmetic shall remain distinct from wrapping and checked arithmetic.

### `AMATH-53`
Interval arithmetic shall preserve its declared enclosure semantics.

### `AMATH-54`
Directed rounding operations shall not be optimized into semantically incompatible rounding.

### `AMATH-55`
Numerical domain restrictions shall not be silently ignored.

### `AMATH-56`
Symbolic computation shall remain distinct from numerical computation.

### `AMATH-57`
Compile-time symbolic transformations shall re-enter ordinary compiler verification.

### `AMATH-58`
Numerical precision metadata shall be available to CompilerDB.

### `AMATH-59`
Math intrinsics shall remain target-aware while preserving language semantics.

### `AMATH-60`
FMA and similar transformations shall be legal only when permitted by the active numerical profile.

### `AMATH-61`
SIMD math shall preserve the semantic contract of scalar math within the selected numerical profile.

### `AMATH-62`
Numerical backend specialization shall not alter type or ownership semantics.

### `AMATH-63`
Numerical optimization shall declare its numerical preconditions.

### `AMATH-64`
Numerical optimization lacking required proof shall not be applied.

### `AMATH-65`
Scientific libraries shall support CPU and accelerator backends without changing Core semantics.

### `AMATH-66`
Numerical code shall remain compatible with freestanding Axiom where dependencies permit.

### `AMATH-67`
Scientific computing shall not require a garbage collector.

### `AMATH-68`
Scientific computing shall not require a mandatory runtime.

### `AMATH-69`
Scientific types shall remain compatible with Axiom ownership and capability semantics.

### `AMATH-70`
Numerical algorithms shall be testable against reference implementations.

---

# Một bổ sung rất quan trọng: Physical Units

Trong toàn bộ architecture hiện tại, tôi đánh giá **units-of-measurement** là một trong những tính năng đáng đưa vào Axiom standard library ngay từ đầu.

Ví dụ:

```axiom
let distance = 100.0 * Meter
let time     = 9.58 * Second

let speed = distance / time
```

Compiler có thể suy ra:

```text
Quantity<f64, MeterPerSecond>
```

và:

```axiom
distance + time
```

bị reject.

Sau compilation:

```text
Quantity<f64, Meter>
```

có thể hoàn toàn biến thành:

```text
f64
```

Nếu không còn semantic runtime effect.

Đây là đúng tinh thần Axiom:

> **Type system làm việc nhiều hơn để programmer phải làm ít hơn, nhưng abstraction biến mất hoàn toàn khi không cần runtime.**

---

# Tổng hợp vị trí của BOOTSTRAP-210

Đến đây tầng numerical stack của Axiom là:

```text
                    Axiom Core
                        │
              ┌─────────┴─────────┐
              │                   │
           Numeric              SIMD
              │                   │
       ┌──────┼──────┐            │
       ▼      ▼      ▼            ▼
    Complex  Big   Rational      Vector
       │      │      │            │
       └──────┼──────┴────────────┘
              ▼
       Linear Algebra
              │
       ┌──────┼─────────┐
       ▼      ▼         ▼
      FFT    Sparse    Solver
       │      │         │
       └──────┼─────────┘
              ▼
       Scientific Computing
              │
       ┌──────┼─────────────┐
       ▼      ▼             ▼
      AI    Physics       Engineering
```

Và tất cả đều có thể dùng:

```text
CPU
SIMD
GPU
Accelerator
Distributed
```

mà không cần thay đổi Core language.

---

# BOOTSTRAP-211 — Parallel Computing, HPC, NUMA, SIMD/SIMT & Distributed Compute

**TRẠNG THÁI: NEXT**

Đây là bước tiếp theo rất quan trọng vì hiện tại Axiom đã có:

- ownership
- capability
- threads
- async
- GPU
- tensor
- networking
- distributed communication
- numerical computing

Nhưng chưa gom chúng thành một **HPC execution model thống nhất**.

211 sẽ giải quyết:

```text
CPU cores
Threads
Tasks
Fibers
SIMD
SIMT
GPU
NUMA
CPU affinity
Cache topology
Memory locality
Work stealing
Thread pools
Task graphs
Parallel loops
Reductions
Barriers
Atomics
Lock-free structures
MPI-like communication
Collectives
Distributed execution
```

Câu hỏi trung tâm:

> **Làm thế nào để Axiom cho phép programmer viết một computation gần như bình thường, nhưng compiler/runtime có thể tự chọn scalar → SIMD → multithread → GPU → distributed execution mà không biến language thành một DSL HPC riêng biệt?**