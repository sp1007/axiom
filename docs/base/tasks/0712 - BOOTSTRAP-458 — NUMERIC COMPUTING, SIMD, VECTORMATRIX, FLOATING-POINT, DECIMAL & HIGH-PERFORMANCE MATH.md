# BOOTSTRAP-458 — NUMERIC COMPUTING, SIMD, VECTOR/MATRIX, FLOATING-POINT, DECIMAL & HIGH-PERFORMANCE MATH

**Trạng thái: COMPLETED / LOCKED**

Mục tiêu của 458 là thiết kế numeric foundation đủ mạnh để Axiom có thể xây dựng:

```text
scalar computing
SIMD
signal processing
image processing
linear algebra
scientific computing
statistics
cryptography
tensor/ML
GPU compute
```

nhưng không biến language core thành một framework toán học hoặc ML.

Nguyên tắc:

```text
Axiom Core
    ↓
Scalar numeric types
    ↓
Vector/SIMD primitives
    ↓
Numeric library
    ↓
Matrix / Linear Algebra
    ↓
Tensor / ML
    ↓
GPU
```

---

## 458.1 — Numeric layers

Numeric functionality chia thành:

```text
numeric-core
numeric-integer
numeric-float
numeric-fixed
numeric-decimal
numeric-complex
numeric-simd
numeric-vector
numeric-matrix
numeric-math
numeric-random
numeric-stat
```

Tensor/ML không thuộc 458 core.

---

## 458.2 — Primitive scalar types

Axiom giữ:

```text
bool
i8 i16 i32 i64
u8 u16 u32 u64
isize usize
f16 f32 f64
```

và có thể mở rộng:

```text
i128 u128
f128
```

như target/library capability.

---

## 458.3 — No implicit numeric promotion

Quy tắc 430 tiếp tục được giữ.

Ví dụ:

```text
i32 + i64
```

không tự động đổi kiểu.

---

## 458.4 — Explicit conversion

Conversion dùng:

```text
as
```

hoặc conversion traits.

---

## 458.5 — Numeric literals

Compiler phải infer literal theo expected type.

Ví dụ:

```text
let x: i64 = 42
let y: f32 = 3.14
```

---

## 458.6 — Integer default

Integer literal không bị ràng buộc mặc định là `i32`.

---

## 458.7 — Float default

Floating literal không bị ràng buộc mặc định là `f64`.

---

## 458.8 — Overflow model

Integer arithmetic có các semantic modes:

```text
checked
wrapping
saturating
```

---

## 458.9 — Default integer arithmetic

Debug/release behavior phải deterministic và không được âm thầm thay đổi semantic model.

---

## 458.10 — Explicit wrapping

Có API/operator cho wrapping arithmetic.

---

# 458.11 — Checked integer arithmetic

Checked arithmetic trả:

```text
Option<T>
```

hoặc equivalent checked-result abstraction.

---

## 458.12 — Overflow detection

Compiler có thể lower checked arithmetic xuống hardware overflow flags.

---

## 458.13 — Saturating arithmetic

Saturating operations clamp về min/max.

---

## 458.14 — Wrapping arithmetic

Wrapping operations dùng two's-complement modulo semantics.

---

## 458.15 — Division

Integer division phải define:

- zero divisor;
- signed overflow;
- quotient;
- remainder.

---

## 458.16 — Division by zero

Safe integer division phải xử lý zero divisor theo typed failure/panic contract phù hợp API.

---

## 458.17 — Remainder

Remainder sign semantics phải được specify rõ.

---

## 458.18 — Bit operations

Numeric core hỗ trợ:

```text
and
or
xor
not
shl
shr
rotl
rotr
```

---

## 458.19 — Shift semantics

Shift amount ngoài range phải có defined behavior theo operation variant.

---

## 458.20 — Bit counting

Core/library cung cấp:

```text
clz
ctz
popcount
bit_reverse
```

---

# 458.21 — Fixed-width integer representation

All fixed-width integers use two's-complement signed representation.

---

## 458.22 — Endianness

Integer value semantics không phụ thuộc host endianness.

---

## 458.23 — Byte conversion

`to_le`, `to_be`, `from_le`, `from_be` là explicit operations.

---

## 458.24 — Native endian

Native-endian conversion là explicit.

---

## 458.25 — Integer serialization

Serialization phải specify endian.

---

## 458.26 — Integer narrowing

Narrowing conversion không implicit.

---

## 458.27 — Integer widening

Widening cũng không implicit giữa unrelated numeric types.

---

## 458.28 — Sign conversion

Signed ↔ unsigned conversion explicit.

---

## 458.29 — Numeric casts

Compiler phải distinguish:

```text
numeric conversion
bit reinterpretation
```

---

## 458.30 — `bitcast`

`bitcast` chỉ cho phép representation-compatible types.

---

# 458.31 — Floating-point model

`f16/f32/f64` dùng IEEE-754 semantics khi target hỗ trợ representation tương ứng.

---

## 458.32 — NaN

NaN là valid floating-point value.

---

## 458.33 — Infinity

`+Inf` và `-Inf` là valid values.

---

## 458.34 — Signed zero

`+0` và `-0` được preserve theo IEEE semantics nơi applicable.

---

## 458.35 — NaN comparison

Ordinary equality follows floating-point semantics; NaN does not compare equal to itself.

---

## 458.36 — Total ordering

Nếu cần ordering toàn phần:

```text
total_cmp(a,b)
```

là separate operation.

---

## 458.37 — NaN payload

Implementations có thể preserve NaN payload where hardware allows, nhưng ordinary language semantics không phụ thuộc payload identity.

---

## 458.38 — Floating exception flags

Platform-specific floating exception/status state thuộc numeric runtime/platform layer.

---

## 458.39 — Floating traps

Floating traps không phải default language behavior.

---

## 458.40 — FP environment

Code cần control rounding/environment phải dùng explicit platform/numeric API.

---

# 458.41 — Rounding modes

Hỗ trợ conceptual:

```text
nearest_even
toward_zero
toward_positive
toward_negative
```

---

## 458.42 — Default rounding

Default floating arithmetic follows target/compiler-defined IEEE-compatible default environment.

---

## 458.43 — Explicit rounding

Applications requiring exact rounding policy phải request it explicitly.

---

## 458.44 — Constant evaluation

Comptime floating-point evaluation phải deterministic theo 431.

---

## 458.45 — Host/target floating semantics

Compiler không được để host CPU vô tình thay đổi compile-time result.

---

## 458.46 — FMA

Compiler có thể generate fused multiply-add khi semantic contract cho phép.

---

## 458.47 — Strict FP

Strict floating-point mode phải preserve observable IEEE behavior required by program.

---

## 458.48 — Fast math

Fast-math là explicit optimization mode/attribute.

---

## 458.49 — Fast-math assumptions

Fast math có thể cho phép:

- reassociation;
- ignoring signed zero;
- simplified NaN handling;
- approximate transformations;

nhưng phải được khai báo rõ.

---

## 458.50 — No hidden fast math

Release build không tự động biến ordinary IEEE code thành fast-math.

---

# 458.51 — Math library

Math functions:

```text
sqrt
cbrt
exp
exp2
log
log2
log10
pow
sin
cos
tan
asin
acos
atan
atan2
sinh
cosh
tanh
```

thuộc numeric library.

---

## 458.52 — Elementary function accuracy

Library phải document accuracy/maximum error theo target/provider.

---

## 458.53 — Hardware math

Compiler có thể map một số functions tới hardware instructions.

---

## 458.54 — Software math

Fallback software implementation phải tồn tại khi target không có instruction.

---

## 458.55 — Determinism

Applications yêu cầu cross-platform bitwise reproducibility phải chọn deterministic math profile/provider.

---

## 458.56 — Approximate math

Approximate functions phải có explicit API/metadata.

---

## 458.57 — Vector math

Math functions có vector overloads khi target hỗ trợ.

---

## 458.58 — Polynomial functions

Numeric library có thể expose efficient polynomial evaluation.

---

## 458.59 — Horner evaluation

Horner-style evaluation có thể được optimizer recognize.

---

## 458.60 — Math error handling

Domain errors phải follow explicit API contract, không dựa vào hidden exceptions.

---

# 458.61 — SIMD foundation

Axiom có explicit vector types.

Conceptual:

```text
vec<T, N>
```

---

## 458.62 — Vector element type

Element type phải là SIMD-compatible scalar.

---

## 458.63 — Vector length

`N` có thể là compile-time constant.

---

## 458.64 — Vector layout

Vector layout phải deterministic theo target ABI.

---

## 458.65 — SIMD register mapping

Compiler có thể map `vec<T,N>` vào native SIMD registers.

---

## 458.66 — Vector register classes

Backend 438 define register classes cho vector values.

---

## 458.67 — Scalar fallback

Không có SIMD hardware thì library/compiler có thể lower vector operations thành scalar operations.

---

## 458.68 — Semantic portability

Scalar fallback phải preserve vector operation semantics.

---

## 458.69 — Vector alignment

Alignment phụ thuộc vector type/target ABI.

---

## 458.70 — Explicit alignment

Developer có thể request alignment bằng `@repr(align(N))` hoặc allocation API.

---

# 458.71 — Vector arithmetic

Support:

```text
+
-
*
/
```

where operation is defined for element type.

---

## 458.72 — Vector comparison

Comparisons produce mask vectors.

---

## 458.73 — Mask type

Conceptual:

```text
mask<T, N>
```

---

## 458.74 — Mask operations

Support:

```text
mask_and
mask_or
mask_xor
mask_not
select
```

---

## 458.75 — Select

Conceptual:

```text
select(mask, a, b)
```

---

## 458.76 — Horizontal reduction

Library/compiler supports:

```text
reduce_add
reduce_min
reduce_max
reduce_and
reduce_or
```

where valid.

---

## 458.77 — Lane extraction

Lane extraction is explicit.

---

## 458.78 — Lane insertion

Lane insertion is explicit.

---

## 458.79 — Shuffle

Vector shuffle uses compile-time or dynamic index forms.

---

## 458.80 — Permute

Target-specific efficient permute instructions may be selected by backend.

---

# 458.81 — SIMD load/store

Vector memory operations support:

```text
load
store
load_unaligned
store_unaligned
```

when appropriate.

---

## 458.82 — Alignment-safe load

Aligned load requires valid alignment.

---

## 458.83 — Unaligned load

Unaligned operations are explicit.

---

## 458.84 — Gather

Gather is optional target capability.

---

## 458.85 — Scatter

Scatter is optional target capability.

---

## 458.86 — Masked load/store

Masked memory operations can avoid invalid lanes.

---

## 458.87 — Bounds safety

Safe vector load/store must obey memory bounds.

---

## 458.88 — Unsafe SIMD memory

Raw pointer SIMD access follows 445.

---

## 458.89 — Volatile SIMD

Volatile operations are explicit and primarily for MMIO/special memory.

---

## 458.90 — Atomic vectors

Atomic vector operations are not implied by ordinary SIMD vectors.

---

# 458.91 — SIMD ABI

Vectors crossing function boundaries use target ABI rules.

---

## 458.92 — ABI portability

A vector type does not imply identical calling convention on all targets.

---

## 458.93 — FFI vectors

FFI vector layout/calling convention must be explicit.

---

## 458.94 — `repr(C)` vectors

C-compatible vector representations can be supported where target ABI defines them.

---

## 458.95 — Vector return

Vector return follows ABI classification.

---

## 458.96 — Vector arguments

Vector argument passing follows ABI.

---

## 458.97 — Vector spills

Register allocator may spill vectors to stack.

---

## 458.98 — Stack alignment

Backend must satisfy vector stack alignment requirements.

---

## 458.99 — Vector aliasing

Vector references obey normal Axiom alias/lifetime rules.

---

## 458.100 — Vector ownership

Owning vector containers are separate from SIMD register vectors.

---

# 458.101 — SIMD intrinsics

Low-level intrinsic API is available for advanced code.

---

## 458.102 — Intrinsic portability

Portable vector operations should be preferred where semantics are available.

---

## 458.103 — ISA-specific intrinsics

Examples conceptually:

```text
x86.sse
x86.avx
x86.avx2
x86.avx512
arm.neon
```

---

## 458.104 — Intrinsic target checks

Using unsupported intrinsic must produce compile-time diagnostic.

---

## 458.105 — Feature gating

ISA-specific APIs require target feature declaration.

---

## 458.106 — Runtime feature dispatch

Function multiversioning can provide:

```text
generic
AVX2
AVX-512
NEON
```

variants.

---

## 458.107 — CPU dispatch safety

Dispatcher must never call unsupported instruction variant.

---

## 458.108 — Compile target

`-march`/CPU target configuration belongs to build target model 438/432.

---

## 458.109 — Portable binary

Generic binaries must not contain unconditional unsupported instructions.

---

## 458.110 — Optimization metadata

Compiler records vectorization decisions in metadata 446.

---

# 458.111 — Auto-vectorization

Optimizer may vectorize loops automatically.

---

## 458.112 — Vectorization correctness

Vectorization must preserve observable program semantics unless fast-math/other relaxed contract permits transformations.

---

## 458.113 — Alias analysis

Optimizer can vectorize more aggressively when aliasing information proves safety.

---

## 458.114 — Bounds-check elimination

Vectorization may combine with bounds-check elimination.

---

## 458.115 — Reduction recognition

Optimizer may recognize reduction loops.

---

## 458.116 — SIMD profitability

Vectorization must use target-specific cost models.

---

## 458.117 — Scalar fallback

If vectorization is not profitable, scalar implementation remains valid.

---

## 458.118 — Missed-vectorization reason

Compiler metadata should explain major missed vectorization reasons.

---

## 458.119 — AI optimization query

AI tooling can ask:

```text
why wasn't this loop vectorized?
```

---

## 458.120 — Vectorization reports

Optional optimization report can show:

```text
vectorized
width
unroll factor
runtime checks
reason rejected
```

---

# 458.121 — Matrix type

Matrix is a library abstraction, not necessarily a language primitive.

Conceptual:

```text
Matrix<T, Rows, Cols>
```

---

## 458.122 — Matrix storage

Supported layouts:

```text
row_major
column_major
strided
```

---

## 458.123 — Layout explicitness

Layout must be represented in type/metadata when ABI/performance correctness depends on it.

---

## 458.124 — Matrix indexing

Matrix indexing is bounds-checked in safe APIs.

---

## 458.125 — Matrix views

Matrix slices/views avoid allocation.

---

## 458.126 — Submatrix

Submatrix can be represented as strided view.

---

## 458.127 — Transpose

Transpose may be a view when possible.

---

## 458.128 — Materialized transpose

Explicit operation can allocate a new matrix.

---

## 458.129 — Matrix multiplication

Matrix multiplication is library functionality.

---

## 458.130 — Matmul optimization

Library can use:

```text
SIMD
blocking
tiling
cache-aware algorithms
parallelism
```

---

# 458.131 — BLAS-style abstraction

Linear algebra library may provide BLAS-like APIs.

---

## 458.132 — GEMM

Matrix multiplication should expose efficient GEMM primitive.

---

## 458.133 — GEMV

Matrix-vector operations are separate primitives.

---

## 458.134 — Dot product

Dot product supports scalar/SIMD optimized implementations.

---

## 458.135 — Norms

Common norms belong to linear algebra library.

---

## 458.136 — Decomposition

Optional APIs:

```text
LU
QR
SVD
Cholesky
eigen
```

---

## 458.137 — Numeric stability

Library documentation must distinguish mathematically correct algorithm from numerically stable implementation.

---

## 458.138 — Precision selection

Algorithms should permit `f32/f64` choice where meaningful.

---

## 458.139 — Mixed precision

Mixed-precision operations must be explicit or strongly type-directed.

---

## 458.140 — Accumulation precision

Reduction APIs should permit higher-precision accumulation.

---

# 458.141 — Complex numbers

Complex numbers are library types:

```text
Complex<T>
```

---

## 458.142 — Complex arithmetic

Support:

```text
+
-
*
/
```

---

## 458.143 — Complex functions

Library can provide:

```text
abs
arg
conj
sqrt
exp
log
sin
cos
```

---

## 458.144 — Complex layout

Complex `<f32>`/`<f64>` may use two adjacent floating values.

---

## 458.145 — FFI complex

C ABI compatibility must not be assumed without explicit target ABI contract.

---

# 458.146 — Fixed-point

Fixed-point types can be library-provided:

```text
Fixed<I, F>
```

where:

- `I` = integer/storage width;
- `F` = fractional bits.

---

## 458.147 — Fixed-point overflow

Operations support checked/wrapping/saturating modes.

---

## 458.148 — Fixed-point scaling

Conversions must preserve explicitly documented scale semantics.

---

## 458.149 — Fixed-point division

Division semantics must document rounding.

---

## 458.150 — Fixed-point use cases

Useful for:

```text
embedded
DSP
audio
control systems
deterministic simulation
```

---

# 458.151 — Decimal

Decimal type is library functionality.

---

## 458.152 — Decimal representation

Decimal may use:

```text
coefficient
scale
sign
```

or equivalent representation.

---

## 458.153 — Financial arithmetic

Decimal supports exact decimal-oriented arithmetic for appropriate ranges.

---

## 458.154 — Decimal rounding

Rounding policy is explicit.

---

## 458.155 — Decimal overflow

Overflow returns error or uses explicitly selected mode.

---

## 458.156 — Decimal serialization

Canonical decimal encoding must be defined.

---

## 458.157 — Decimal vs float

`Decimal` is not a drop-in semantic replacement for `f64`.

---

## 458.158 — Decimal performance

Compiler need not special-case arbitrary Decimal operations initially.

---

## 458.159 — Decimal SIMD

Decimal SIMD is optional and target/provider dependent.

---

## 458.160 — Decimal comptime

Decimal constant evaluation may be provided through comptime library implementation.

---

# 458.161 — Random numeric generation

General random distributions belong to numeric/random library.

---

## 458.162 — PRNG

Fast deterministic PRNG is separate from secure RNG 456.

---

## 458.163 — Distribution abstraction

Possible distributions:

```text
uniform
normal
exponential
bernoulli
poisson
```

---

## 458.164 — Reproducible simulation

Explicit seed produces deterministic stream.

---

## 458.165 — Parallel RNG

Parallel simulations need independent streams/substreams.

---

## 458.166 — RNG state ownership

RNG state is ordinary explicit value.

---

## 458.167 — No hidden global RNG

Numeric library must not silently use process-global mutable RNG.

---

## 458.168 — Secure RNG distinction

Cryptographic randomness always uses 456 APIs.

---

## 458.169 — Statistical APIs

Statistical calculations belong numeric library.

---

## 458.170 — Statistics precision

Accumulation precision should be explicit for numerically sensitive workloads.

---

# 458.171 — Approximate equality

Floating approximate comparison is library functionality.

---

## 458.172 — Absolute tolerance

Support absolute tolerance.

---

## 458.173 — Relative tolerance

Support relative tolerance.

---

## 458.174 — Combined tolerance

Combined absolute/relative comparison may be provided.

---

## 458.175 — No universal epsilon

Library must not pretend one epsilon works for all numeric domains.

---

## 458.176 — Total order

Algorithms requiring ordering can use explicit total ordering.

---

## 458.177 — Hashing floats

Hash semantics must define NaN and signed-zero behavior.

---

## 458.178 — Float equality/hash

Hash implementation must be consistent with equality semantics.

---

## 458.179 — Numeric formatting

Formatting precision/rounding should be explicit.

---

## 458.180 — Bit representation

`to_bits/from_bits` can expose IEEE representation.

---

# 458.181 — Numeric generic programming

Generic numeric algorithms use traits.

Conceptually:

```text id="3z0h5s"
trait Numeric {
    ...
}
```

---

## 458.182 — Trait specialization

Algorithms can specialize for SIMD/f32/f64 through static generics.

---

## 458.183 — Monomorphization

Generic numeric code is statically monomorphized according to 426.

---

## 458.184 — Generic vector

`vec<T,N>` can be generic while backend lowers concrete instances.

---

## 458.185 — Const dimensions

Matrix dimensions use const generics.

---

## 458.186 — Shape typing

Compile-time matrix shape checking can be implemented with const generics.

---

## 458.187 — Dynamic shape

Runtime-shaped matrices remain supported.

---

## 458.188 — Shape metadata

Dynamic matrix dimensions are explicit values.

---

## 458.189 — No mandatory tensor type

Tensor is not a primitive language type.

---

## 458.190 — ML separation

ML frameworks can build on vector/matrix/tensor libraries.

---

# 458.191 — Tensor foundation

Future tensor library can represent:

```text
Tensor<T, Shape, Layout>
```

---

## 458.192 — Tensor ownership

Tensor owns or views explicit memory.

---

## 458.193 — Tensor allocation

Allocation uses allocator model 423.

---

## 458.194 — Tensor views

Strided tensor views are non-owning.

---

## 458.195 — Tensor device

Future device abstraction:

```text
CPU
GPU
NPU
```

---

## 458.196 — Device memory

Device memory is explicit resource ownership.

---

## 458.197 — Async device operations

Device operations integrate with 424 async model.

---

## 458.198 — Synchronization

CPU/GPU synchronization is explicit.

---

## 458.199 — No hidden GPU synchronization

Compiler/runtime must not insert expensive device synchronization invisibly.

---

## 458.200 — GPU boundary

GPU compiler/backend is separate from CPU numeric semantics.

---

# 458.201 — Numeric memory layout

All numeric containers expose:

```text
size
alignment
stride
layout
```

where meaningful.

---

## 458.202 — Contiguous storage

Contiguous arrays are first-class optimization target.

---

## 458.203 — Strided storage

Strided views must represent stride explicitly.

---

## 458.204 — Negative stride

Negative strides can be supported if representation permits.

---

## 458.205 — Alignment

Allocator may provide requested SIMD alignment.

---

## 458.206 — Pinned memory

Pinned memory is platform/device capability, not ordinary heap memory.

---

## 458.207 — NUMA

NUMA placement belongs platform/runtime layer.

---

## 458.208 — Cache locality

Compiler and library may use blocking/tiling.

---

## 458.209 — Prefetch

Prefetch intrinsics are optional low-level optimization.

---

## 458.210 — Non-temporal memory

Non-temporal load/store is target-specific intrinsic.

---

# 458.211 — Atomic numeric operations

Scalar atomics are defined by 424.

---

## 458.212 — Atomic floating point

Atomic float operations are optional target/library capabilities.

---

## 458.213 — Atomic vector

Vector atomics are optional target-specific functionality.

---

## 458.214 — Reduction concurrency

Parallel reductions must define determinism/associativity implications.

---

## 458.215 — Floating parallel reduction

Parallel floating reduction may produce different rounding than serial reduction.

---

## 458.216 — Strict reduction

Strict deterministic reduction is separate API/optimization mode.

---

## 458.217 — Fast reduction

Fast reduction may permit reassociation under explicit relaxed semantics.

---

## 458.218 — Numerical determinism

Compiler metadata should expose relaxed numeric contracts.

---

## 458.219 — AI numeric query

AI can ask:

```text
is this operation deterministic?
can it use SIMD?
can it reassociate?
does it allocate?
what precision does it accumulate in?
```

---

## 458.220 — Optimization explanation

Compiler reports can explain numeric transformations.

---

# 458.221 — Compiler intrinsics

Core intrinsic namespace may provide low-level operations:

```text
add_with_carry
sub_with_borrow
mul_wide
fma
clz
ctz
popcount
vector_shuffle
prefetch
```

---

## 458.222 — Intrinsic safety

Intrinsic safety is individually specified.

---

## 458.223 — Target-specific intrinsic

Unsupported target intrinsic is compile-time error.

---

## 458.224 — Instruction selection

Portable arithmetic must be lowered to best available target instructions.

---

## 458.225 — Carry arithmetic

Compiler supports multiword arithmetic efficiently.

---

## 458.226 — Wide multiplication

`mul_wide` can produce high/low components.

---

## 458.227 — Division optimization

Compiler may use target-specific reciprocal/magic-number optimization when semantics permit.

---

## 458.228 — Constant division

Compile-time constant integer division should optimize efficiently.

---

## 458.229 — Bit tricks

Compiler may recognize standard bit manipulation patterns.

---

## 458.230 — Undefined hardware assumptions

Language semantics must not rely on undocumented CPU behavior.

---

# 458.231 — Math and comptime

Pure numeric functions may execute at compile time.

---

## 458.232 — Constant folding

Compiler folds arithmetic constants.

---

## 458.233 — Floating constant folding

Must respect selected FP semantics.

---

## 458.234 — Fast-math comptime

Fast-math compile-time evaluation must be deterministic according to the selected profile.

---

## 458.235 — Table generation

Comptime can generate lookup tables.

---

## 458.236 — Numeric lookup tables

Useful for:

```text
trigonometry
DSP
signal processing
graphics
ML kernels
```

---

## 458.237 — Resource limits

Large comptime numeric generation obeys 431 resource limits.

---

## 458.238 — Compile-time SIMD

Semantic vector operations can be evaluated at comptime when fully constant.

---

## 458.239 — Target-specific tables

Target-specific generation requires explicit target query.

---

## 458.240 — Reproducibility

Generated numeric tables are cacheable by semantic hash.

---

# 458.241 — DSP foundation

Optional DSP library can build on:

```text
vector
complex
matrix
FFT
convolution
window
filter
```

---

## 458.242 — FFT

FFT implementation should support power-of-two optimized paths and general sizes where practical.

---

## 458.243 — Convolution

Convolution can use direct or FFT-based algorithms.

---

## 458.244 — FIR/IIR

Signal-processing filters belong library layer.

---

## 458.245 — Audio

Audio sample types should be explicit numeric types.

---

## 458.246 — Image processing

Pixel types are library types:

```text
u8
u16
f16
f32
```

and vectorized operations can use SIMD.

---

## 458.247 — Color space

Color-space semantics belong graphics/image libraries.

---

## 458.248 — Quantization

Quantized numeric types can be library abstractions.

---

## 458.249 — Integer quantization

Explicit scale/zero-point metadata required.

---

## 458.250 — ML separation

Quantization does not make Axiom an ML framework.

---

# 458.251 — Benchmarking

Numeric benchmarks measure:

```text
scalar throughput
SIMD throughput
latency
memory bandwidth
cache behavior
vectorization
allocation
```

---

## 458.252 — Benchmark correctness

Benchmarks must prevent dead-code elimination from invalidating measurements.

---

## 458.253 — Target recording

Record:

```text
CPU
ISA features
compiler version
optimization
math mode
```

---

## 458.254 — SIMD benchmark

Report scalar and vector versions separately.

---

## 458.255 — Floating benchmark

Record precision and math mode.

---

## 458.256 — Reproducibility

Numerical benchmark datasets and parameters must be pinned.

---

## 458.257 — Accuracy benchmark

Performance benchmark không được bỏ qua numerical error.

---

## 458.258 — Error bounds

Scientific kernels may record accuracy/error metrics.

---

## 458.259 — Compiler regression

Track vectorization and instruction-count regressions.

---

## 458.260 — Code-size regression

SIMD dispatch/vectorized code bloat phải được measured.

---

# 458.261 — FFI

Numeric types integrate with 451 ABI.

---

## 458.262 — C integer types

C ABI mappings:

```text
int
unsigned int
long
unsigned long
size_t
ptrdiff_t
```

phải target-specific.

---

## 458.263 — C floating types

`float/double` map explicitly.

---

## 458.264 — Vector FFI

Vendor/platform vector ABI must be explicit.

---

## 458.265 — Matrix FFI

Matrix layout must be specified.

---

## 458.266 — Decimal FFI

Decimal FFI is not assumed compatible with C floating types.

---

## 458.267 — Packed numeric structs

Packed representations may be defined using 422 representation attributes.

---

## 458.268 — Alignment mismatch

FFI ABI verifier detects incompatible numeric alignment/layout.

---

## 458.269 — Endian FFI

Wire/binary interfaces specify endian.

---

## 458.270 — Numeric ABI metadata

446 exposes layout/ABI metadata.

---

# 458.271 — Error model

Numeric APIs use:

```text
Result
Option
```

where failures are meaningful.

---

## 458.272 — NaN vs error

Floating domain errors must distinguish mathematically undefined results from API/resource errors where appropriate.

---

## 458.273 — Allocation failures

Large numeric containers return allocation failure according to allocator policy.

---

## 458.274 — Out-of-range

Conversions can return checked errors.

---

## 458.275 — Singular matrices

Linear algebra operations that may fail must expose failure explicitly.

---

## 458.276 — Ill-conditioned matrices

Numerical instability is distinct from structural failure and should be documented.

---

## 458.277 — Panic-free numeric APIs

Parsing and ordinary arithmetic library APIs should avoid panic for externally supplied values.

---

## 458.278 — Unsafe numeric operations

Unchecked SIMD memory and raw pointer operations follow 445.

---

## 458.279 — Resource contracts

Numeric functions can expose:

```text
@no_alloc
@no_block
@no_panic
```

---

## 458.280 — AI diagnostics

Machine-readable diagnostics identify numeric conversion, overflow, precision, and target-feature errors.

---

# 458.281 — Hard invariants

1. Numeric foundation does not turn Axiom into an ML framework.
2. Scalar numeric semantics are deterministic.
3. No implicit numeric promotion.
4. Numeric conversion is explicit.
5. Signed integers use two's complement.
6. Endianness is explicit for byte representation.
7. Checked, wrapping and saturating arithmetic are distinct.
8. Division semantics are defined.
9. Shift semantics are defined.
10. Bit operations are explicit and efficient.
11. `f16/f32/f64` follow defined floating-point semantics.
12. NaN is a valid floating value.
13. Infinity is a valid floating value.
14. Signed zero semantics are preserved where required.
15. Floating equality is not total ordering.
16. Total ordering is explicit.
17. Rounding modes are defined.
18. Fast-math is explicit.
19. Compiler must not silently enable unsafe floating transformations.
20. FMA generation must obey selected FP semantics.
21. Comptime floating evaluation must be deterministic.
22. Math accuracy must be documented.
23. Approximate math must be explicit.
24. SIMD vectors are explicit value types.
25. SIMD vector width is part of the type/representation.
26. Vector layout is target-defined.
27. Scalar fallback must exist where semantics permit.
28. SIMD alignment is explicit.
29. Unaligned access is explicit.
30. Vector comparison returns mask semantics.
31. Mask operations are first-class library/compiler operations.
32. Vector reductions are explicit.
33. Shuffle/permute are supported.
34. Gather/scatter are optional target capabilities.
35. Safe SIMD memory access obeys bounds.
36. Raw SIMD memory follows unsafe model.
37. Vector ABI is target-specific and explicit.
38. FFI vector ABI cannot be assumed portable.
39. ISA-specific intrinsics require target-feature checks.
40. Unsupported ISA instructions are compile-time errors.
41. Runtime CPU dispatch must not call unsupported instructions.
42. Generic portable binaries must not unconditionally emit unsupported instructions.
43. Auto-vectorization is allowed.
44. Auto-vectorization must preserve semantics.
45. Optimizer may use alias/bounds information.
46. Compiler should report major missed vectorization opportunities.
47. Matrix is library functionality.
48. Matrix dimensions may use const generics.
49. Runtime-sized matrices remain supported.
50. Matrix layout must be explicit where performance/ABI depends on it.
51. Matrix views must avoid unnecessary allocation.
52. Transpose may be a view.
53. Linear algebra algorithms must document numerical stability.
54. Mixed precision must be explicit or type-directed.
55. Complex numbers are library types.
56. Fixed-point is a library abstraction.
57. Decimal is a library abstraction.
58. Financial decimal arithmetic must not silently use binary floating semantics.
59. General PRNG is distinct from CSPRNG.
60. CSPRNG always uses 456.
61. No hidden global numeric RNG.
62. Reproducible simulations can inject deterministic RNG.
63. Parallel RNG streams must be separable.
64. Floating approximate equality must use explicit tolerance semantics.
65. There is no universal floating epsilon.
66. Float hashing must be consistent with equality semantics.
67. IEEE representation can be accessed through explicit bit operations.
68. Numeric generics use trait/static-dispatch machinery 426.
69. Numeric generic instances can be monomorphized.
70. Const-generic shapes are supported.
71. Dynamic shapes remain supported.
72. Tensor is not a core primitive.
73. Tensor memory obeys ownership model 423.
74. Device memory is explicit.
75. GPU synchronization must not be hidden.
76. CPU/GPU execution remains separate from scalar numeric semantics.
77. SIMD/vector operations can be used in comptime where deterministic.
78. Numeric comptime obeys 431 resource limits.
79. Target-specific numeric generation must be explicit.
80. Numeric table generation is deterministic.
81. DSP functionality builds on numeric primitives.
82. Image processing builds on numeric/vector primitives.
83. ML functionality remains ecosystem/library-level.
84. Numeric benchmarks must measure correctness as well as speed.
85. Benchmarks record target ISA/features.
86. Vectorized and scalar benchmarks are distinguishable.
87. Floating benchmarks record precision/math mode.
88. Code-size impact of SIMD dispatch is measurable.
89. Numeric FFI uses explicit ABI mappings.
90. C numeric types are target-specific.
91. Vector FFI is ABI-specific.
92. Matrix FFI requires explicit layout.
93. Numeric parsing failures use typed errors.
94. Singular/invalid numeric operations expose explicit failure.
95. Numeric APIs can declare `@no_alloc`, `@no_block`, `@no_panic`.
96. Compiler diagnostics expose numeric semantic errors.
97. AI tooling can query precision, allocation, vectorization and target-feature behavior.
98. Numeric optimizations must remain observable through compiler metadata.
99. Numeric facilities must remain independently linkable/prunable.
100. **Axiom must make high-performance scalar and SIMD numeric programming natural, while preserving explicit semantics for precision, overflow, floating-point behavior, memory layout and hardware capabilities.**

**BOOTSTRAP-458 hoàn tất.**

---

# BOOTSTRAP-459 — GPU COMPUTING, DEVICE MEMORY, KERNEL MODEL, CPU↔GPU EXECUTION & ACCELERATOR ABSTRACTION

Task tiếp theo sẽ thiết kế **GPU/accelerator model** trên nền 458 + 424, với mục tiêu đặc biệt quan trọng của Axiom:

```text
CPU code
   ↓
GPU kernel
   ↓
device memory
   ↓
CPU↔GPU transfer
   ↓
async execution
   ↓
synchronization
```

nhưng **không khóa Axiom vào CUDA, ROCm, Metal hay một GPU vendor cụ thể**.

459 sẽ xác định:

- GPU device/context/queue;
- device memory và ownership;
- host/device/shared/unified memory;
- kernel syntax;
- kernel compilation;
- workgroup/thread/lane model;
- synchronization/barriers;
- atomics;
- GPU async;
- command buffers;
- streams/queues/events;
- CPU↔GPU transfer;
- zero-copy/unified memory;
- GPU error model;
- shader vs compute kernel;
- SIMD/SIMT;
- GPU-specific generics/comptime;
- SPIR-V/Metal/DXIL/other backend boundary;
- accelerator abstraction;
- multi-GPU;
- device selection;
- capability discovery;
- AI/tensor integration;
- debugging/profiling;
- và đặc biệt **không để GPU runtime trở thành mandatory dependency của executable CPU thông thường**.