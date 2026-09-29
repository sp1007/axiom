# BOOTSTRAP-373 — Axiom Scientific Computing, FFT & Numerical Transform Engine

Sau **372 — Symbolic Computation & Expression Graph**, bước tiếp theo hợp lý là xây tầng **Numerical Transform & Scientific Computing**.

Lý do: đến đây Axiom đã có:

```text
Numeric
  ↓
Tensor / Shape / Layout
  ↓
Linear Algebra
  ↓
Automatic Differentiation
  ↓
Expression Algebra
```

Nhưng vẫn thiếu một nhóm primitive cực kỳ quan trọng của scientific/AI computing:

- FFT / IFFT
- DCT / DST
- convolution
- correlation
- prefix/reduction transforms
- spectral operations
- signal processing
- PDE/simulation building blocks

Mục tiêu của 373 là để những phép toán này trở thành **semantic operations có thể được compiler tối ưu**, thay vì chỉ là các hàm thư viện đen.

---

## 1. Không đưa FFT thành Core primitive

Axiom không nên có:

```text
builtin fft(...)
```

trong ngôn ngữ cơ bản.

Thay vào đó:

```text
Scientific Computing Library
        ↓
Compiler-known Numerical Operations
        ↓
Optimization / Kernel Selection
```

Compiler hiểu một số operation quan trọng nhưng chúng vẫn thuộc tầng numeric/scientific library.

---

# 2. FFT là semantic operation

Compiler cần nhận diện:

```text
FFT(x)
IFFT(x)
RFFT(x)
IRFFT(x)
```

như các operation có semantics xác định.

Không nên coi chúng đơn giản là:

```text
fn fft(x) {
    ...
    for ...
}
```

vì như vậy compiler rất khó biết đây là FFT để chọn implementation tối ưu.

---

# 3. Fourier transform semantics

Axiom phải định nghĩa rõ convention.

Ví dụ DFT:

\[
X_k = \sum_{n=0}^{N-1} x_n e^{-2\pi i kn/N}
\]

và inverse:

\[
x_n = \frac{1}{N}\sum_{k=0}^{N-1} X_k e^{2\pi i kn/N}
\]

Nhưng normalization không nên để implementation tự quyết định.

Phải có explicit convention:

```text
Normalization:
    None
    Forward
    Inverse
    Ortho
```

---

# 4. Vì sao normalization phải là semantic

Nếu:

```text
FFT(IFFT(x))
```

có scale khác nhau tùy backend thì chương trình có thể cho kết quả khác.

Do đó compiler phải biết:

```text
FFTConvention
NormalizationMode
SignConvention
```

trước khi optimization.

---

# 5. Complex numbers

373 sử dụng `Complex<T>` từ numeric layer.

Conceptual:

```text
struct Complex<T> {
    re: T
    im: T
}
```

Không cần object header.

Compiler có thể scalarize:

```text
(re, im)
```

hoặc vectorize thành:

```text
SIMD<re>
SIMD<im>
```

tùy target.

---

# 6. Real FFT

Đối với input thực:

```text
RFFT(x)
```

output có đối xứng Hermitian.

Không cần lưu toàn bộ spectrum.

Compiler/library có thể dùng:

```text
N/2 + 1
```

complex values.

Đây phải là semantics của `RFFT`, không phải implementation accident.

---

# 7. Multi-dimensional FFT

Tensor:

```text
X: [B,H,W,C]
```

có thể FFT theo:

```text
axis = 1
axis = 2
axis = [1,2]
```

Compiler phải hiểu:

```text
FFT(X, axes=[1,2])
```

là một transform trên các dimensions cụ thể.

---

# 8. Layout matters

FFT trên:

```text
contiguous tensor
```

và:

```text
strided tensor
```

có cost rất khác nhau.

Compiler phải đọc:

```text
Shape
Stride
Layout
Device
DType
```

để chọn implementation.

Không được mặc định copy tensor nếu không cần.

---

# 9. Zero-copy FFT

Nếu input layout tương thích:

```text
FFT(view)
```

có thể trực tiếp sử dụng view.

Nếu layout quá bất lợi:

```text
strided FFT
```

compiler có thể:

```text
transpose
pack
FFT
unpack
```

nhưng chỉ khi cost model chứng minh có lợi.

---

# 10. FFT algorithm selection

Compiler có thể chọn:

```text
Radix-2
Radix-4
Mixed-Radix
Split-Radix
Bluestein
Rader
Stockham
Direct DFT
```

theo:

```text
N
prime factors
dtype
CPU ISA
GPU
memory layout
batch size
```

Người lập trình không cần chọn thủ công trong trường hợp thông thường.

---

# 11. Không phải FFT nào cũng nên dùng Cooley-Tukey

Ví dụ:

```text
N = 17
```

không thuận lợi cho radix-2.

Compiler có thể chọn:

```text
Rader
Bluestein
mixed-radix
```

hoặc direct transform nếu N nhỏ.

Đây là nhiệm vụ của:

```text
FFTPlanner
```

---

# 12. FFT plan

Một FFT plan có thể chứa:

```text
FFTPlan {
    shape
    axes
    dtype
    direction
    normalization
    algorithm
    target
    workspace
}
```

Nhưng:

> Plan không được trở thành mandatory heap object.

Compiler có thể specialize toàn bộ plan tại compile time.

---

# 13. Compile-time FFT planning

Nếu:

```text
comptime N = 1024;
```

compiler biết kích thước.

Có thể generate trực tiếp:

```text
radix-2 stages
twiddle constants
permutation
SIMD strategy
```

và runtime chỉ còn kernel.

Đây là một ứng dụng rất mạnh của **Comptime + Expression Graph**.

---

# 14. Runtime-size FFT

Nếu:

```text
N = runtime_value();
```

thì library có thể dùng dynamic planner.

Compiler vẫn giữ semantics:

```text
FFT(input, N)
```

nhưng implementation có thể chọn runtime algorithm.

---

# 15. FFT + SIMD

FFT rất phù hợp với vectorization.

Compiler có thể vectorize:

```text
butterfly
twiddle multiplication
complex arithmetic
```

Ví dụ conceptual:

```text
(a,b)
```

→

```text
a+b
a-b
```

với nhiều butterflies song song.

---

# 16. FFT + parallelism

Batch FFT:

```text
FFT(X)
```

với:

```text
X: [batch, N]
```

có thể parallelize theo batch.

Large FFT có thể parallelize theo stages/chunks.

Compiler phải cân nhắc:

```text
parallel overhead
cache locality
NUMA
workspace
```

chứ không phải luôn spawn threads.

---

# 17. FFT + GPU

GPU backend có thể biến:

```text
FFT(X)
```

thành nhiều kernels:

```text
load
butterfly
transpose
butterfly
...
```

Compiler có thể fuse một số stages.

Không được implicit:

```text
Host → GPU
```

nếu input đang ở Host.

Storage semantics của 367 vẫn giữ nguyên.

---

# 18. FFT fusion

Expression:

```text
Y = FFT(A) * FFT(B)
```

không nhất thiết phải materialize cả hai spectrum.

Compiler có thể tạo:

```text
FFT(A)
FFT(B)
pointwise multiply
IFFT
```

hoặc sử dụng convolution strategy nếu expression tương đương.

---

# 19. Convolution

Scientific/AI computing cần:

```text
convolution
correlation
```

Compiler phải có semantic operation:

```text
CONV
CORRELATE
```

với explicit:

```text
mode:
    Full
    Same
    Valid

boundary:
    Zero
    Reflect
    Wrap
    Custom
```

---

# 20. Direct convolution vs FFT convolution

Compiler có thể chọn:

```text
Direct convolution
```

hoặc:

```text
FFT convolution
```

tùy:

```text
input size
kernel size
batch
dtype
device
reuse
```

Ví dụ kernel rất nhỏ:

```text
3x3
```

FFT thường không đáng để dùng.

Kernel rất lớn:

```text
1024x1024
```

FFT-based convolution có thể phù hợp.

Đây là nhiệm vụ của cost model.

---

# 21. Convolution semantics không được phụ thuộc implementation

Nếu compiler thay:

```text
direct convolution
```

bằng:

```text
FFT convolution
```

kết quả phải vẫn thỏa numerical contract.

Trong `Strict` mode, compiler phải đặc biệt thận trọng vì thứ tự phép tính thay đổi.

---

# 22. Correlation

Correlation:

```text
corr(x,y)
```

có semantics khác convolution.

Không được chỉ alias:

```text
correlation = convolution
```

mà không xác định rõ:

```text
reversal
conjugation
normalization
boundary
```

---

# 23. DCT / DST

Scientific computing còn cần:

```text
DCT
IDCT
DST
IDST
```

Các transform này có thể được implement bằng FFT hoặc specialized kernels.

Semantic layer chỉ cần biết:

```text
TransformType
Direction
Normalization
Axes
```

Backend quyết định implementation.

---

# 24. Prefix/scanning transforms

Không chỉ FFT.

Axiom nên có abstraction:

```text
Transform<T>
```

cho những phép biến đổi có cấu trúc.

Ví dụ:

```text
prefix_sum
prefix_product
scan
segmented_scan
```

Nhưng phải giữ distinction:

```text
Scan
Reduction
Transform
```

không gom tất cả thành một operation.

---

# 25. Numerical determinism

FFT/reduction/parallel transforms có thể có nhiều execution order.

Axiom phải tích hợp:

```text
NumericalContract
```

từ task 368.

Ví dụ:

```text
Strict
```

→ yêu cầu semantics nghiêm ngặt.

```text
Fast
```

→ compiler được phép thay đổi reduction/order trong phạm vi contract.

---

# 26. Error and tolerance

Một transform numerical không nên tự động trả:

```text
Result<T, Error>
```

chỉ vì sai số floating point.

Cần phân biệt:

```text
Numerical approximation
Runtime failure
Domain error
Allocation failure
```

Ví dụ:

```text
FFT
```

thường không thất bại về mặt toán học chỉ vì floating-point error.

---

# 27. Domain validation

Những operation như:

```text
log
sqrt
inverse
solve
```

có domain semantics.

Expression engine từ 372 có thể giữ:

```text
DomainConstraint
```

Ví dụ:

```text
sqrt(x)
```

có:

```text
x >= 0
```

nếu numerical mode không cho phép complex promotion.

---

# 28. Spectral operators

FFT engine nên làm nền cho:

```text
spectral_derivative
spectral_filter
low_pass
high_pass
band_pass
```

Nhưng đây là library-level abstractions.

Compiler có thể recognize pattern:

```text
FFT
multiply spectrum
IFFT
```

và fuse.

---

# 29. Scientific pipeline fusion

Ví dụ:

```text
y = IFFT(FFT(x) * H)
```

Expression graph có thể thấy:

```text
FFT
   ↓
multiply H
   ↓
IFFT
```

và tối ưu:

```text
single planned pipeline
```

thay vì tạo nhiều intermediate tensors.

---

# 30. Workspace management

FFT/convolution thường cần workspace.

Workspace phải tuân ownership model.

Conceptual:

```text
FFTWorkspace
```

có ownership rõ ràng.

Compiler có thể:

```text
reuse workspace
stack allocate
arena allocate
caller allocate
```

Không được tạo hidden global workspace.

---

# 31. Workspace lifetime

Nếu:

```text
FFTWorkspace
```

được dùng bởi GPU asynchronous kernel:

```text
launch_fft(workspace)
```

workspace không được drop trước khi GPU sử dụng xong.

Đây là nơi:

```text
GpuEvent
+
Ownership
+
Async
```

phối hợp.

Compiler có thể phát hiện lifetime violation.

---

# 32. Transform execution graph

Một transform có thể được biểu diễn:

```text
TransformGraph
```

gồm:

```text
Input
Permutation
Transpose
Kernel
Reduction
Synchronization
Output
```

Graph này không phải runtime graph bắt buộc.

Compiler có thể lower trực tiếp thành:

```text
MIR
```

---

# 33. Kernel selection

CompilerDB cần:

```text
TransformKernelDB
```

để biết:

```text
algorithm
target
dtype
shape
layout
workspace
cost
```

Ví dụ:

```text
FFT 1024 f32 AVX2
FFT 1024 f32 AVX512
FFT 1024 f32 CUDA
FFT 1024 f64 CPU
```

có thể là các implementation khác nhau nhưng cùng semantic operation.

---

# 34. External libraries

Axiom có thể sử dụng:

```text
FFTW
MKL
cuFFT
rocFFT
Accelerate
```

thông qua FFI/backend plugin.

Nhưng:

> Đây không được trở thành dependency bắt buộc của Axiom.

Nếu không có external library:

```text
Axiom Native Numerical Backend
```

vẫn có thể thực hiện operation.

---

# 35. Self-hosting implication

Đây cũng là lý do semantic operation rất quan trọng.

Axiom compiler có thể tự viết:

```text
FFT
Matmul
Convolution
```

trong Axiom.

Compiler sau đó có thể recognize:

```text
@intrinsic
```

hoặc:

```text
@compiler_intrinsic
```

và lower xuống target implementation.

---

# 36. CompilerDB

373 bổ sung:

```text id="2q3f6n"
ScientificDB
TransformDB
TransformTypeDB
TransformDirectionDB
TransformNormalizationDB
TransformAxisDB
TransformShapeDB
TransformLayoutDB
TransformDTypeDB
TransformStorageDB
TransformDeviceDB
TransformPlanDB
TransformPlannerDB
TransformAlgorithmDB
TransformKernelDB
TransformWorkspaceDB
TransformCostModelDB
TransformFusionDB
TransformParallelDB
TransformVectorDB
TransformGpuDB
TransformNumericalDB
TransformDeterminismDB
TransformConvolutionDB
TransformCorrelationDB
FFTDB
FFTPlanDB
FFTAlgorithmDB
FFTKernelsDB
FFTStageDB
FFTTwiddleDB
FFTWorkspaceDB
RFFTDB
DCTDB
DSTDB
SpectralDB
SpectralOperatorDB
TransformProofDB
TransformVerificationDB
```

---

# 37. MIR additions

Semantic MIR:

```text id="b3c7kq"
TRANSFORM_BEGIN
TRANSFORM_END

FFT
IFFT
RFFT
IRFFT

DCT
IDCT
DST
IDST

CONV
CORRELATE

TRANSFORM_PERMUTE
TRANSFORM_TRANSPOSE
TRANSFORM_KERNEL
TRANSFORM_WORKSPACE

SPECTRAL_FILTER
SPECTRAL_MULTIPLY
```

Sau optimization, các operation này có thể lower thành:

```text
loops
SIMD
parallel regions
GPU kernels
```

hoặc target intrinsic/library calls.

---

# 38. Proof system

Mỗi numerical transform cần:

```text id="q6x4mz"
TransformShapeProof
TransformLayoutProof
TransformDTypeProof
TransformNormalizationProof
TransformNumericalProof
TransformAliasProof
TransformStorageProof
TransformDeviceProof
TransformWorkspaceProof
TransformFusionProof
TransformDeterminismProof
```

Đặc biệt:

```text
FFT(A)
```

→

```text
optimized FFT(A)
```

phải có proof rằng normalization/direction/axis semantics không thay đổi.

---

# 39. Invariants

### `ASCI-01`
Scientific transforms không được trở thành mandatory runtime features.

### `ASCI-02`
FFT semantics phải xác định direction.

### `ASCI-03`
FFT semantics phải xác định normalization.

### `ASCI-04`
FFT axis semantics phải rõ ràng.

### `ASCI-05`
RFFT/IRFFT phải định nghĩa chính xác representation của real spectrum.

### `ASCI-06`
Complex arithmetic phải tuân numeric semantics.

### `ASCI-07`
Transform optimization phải tuân numerical contract.

### `ASCI-08`
Compiler không được tự ý thay đổi normalization.

### `ASCI-09`
Compiler không được tự ý thay đổi transform direction.

### `ASCI-10`
Layout phải được xem xét khi chọn transform implementation.

### `ASCI-11`
Compiler không được materialize contiguous storage nếu không cần thiết hoặc không được chứng minh hợp lệ.

### `ASCI-12`
Transform workspace phải có ownership rõ ràng.

### `ASCI-13`
Workspace không được bị giải phóng trước asynchronous operation.

### `ASCI-14`
GPU transform phải tuân device-memory semantics.

### `ASCI-15`
Host/device transfer không được implicit trong safe Core semantics.

### `ASCI-16`
Transform parallelization phải tuân data-race semantics.

### `ASCI-17`
Transform vectorization phải tuân numerical semantics.

### `ASCI-18`
FFT algorithm selection phải preserve observable transform semantics.

### `ASCI-19`
Cost model có thể chọn giữa nhiều implementation semantic-equivalent.

### `ASCI-20`
Direct convolution và FFT convolution chỉ được thay thế khi numerical contract cho phép.

### `ASCI-21`
Convolution boundary semantics phải explicit.

### `ASCI-22`
Correlation semantics phải phân biệt với convolution.

### `ASCI-23`
DCT/DST normalization phải explicit.

### `ASCI-24`
Compile-time-known transform dimensions có thể được specialize.

### `ASCI-25`
Runtime transform dimensions vẫn phải có defined semantics.

### `ASCI-26`
External numerical libraries không được là mandatory language dependency.

### `ASCI-27`
Compiler-native implementation và external implementation phải cùng semantic contract.

### `ASCI-28`
Transform fusion không được phá ownership, alias hoặc numerical guarantees.

### `ASCI-29`
Transform lowering phải có verification/validation path.

### `ASCI-30`
Nếu transform abstraction không còn observable sau optimization, nó phải bị loại khỏi generated runtime representation.

---

## Vị trí của 373

Sau task này, Axiom có một tầng numerical computing khá hoàn chỉnh:

```text
                    Axiom Numeric
                         │
              ┌──────────┴──────────┐
              ▼                     ▼
       Expression Algebra       Shape/Layout
              │                     │
              └──────────┬──────────┘
                         ▼
                  Tensor / Algebra
                         │
              ┌──────────┼──────────┐
              ▼          ▼          ▼
          Linear       Transform     AD
          Algebra      / FFT         │
              │          │           │
              └──────────┼───────────┘
                         ▼
                  Unified Expr Graph
                         │
          ┌──────────────┼──────────────┐
          ▼              ▼              ▼
        SIMD          Parallel         GPU
          │              │              │
          └──────────────┼──────────────┘
                         ▼
                   Native Backend
```

Một điểm kiến trúc quan trọng đã đạt được ở **373**:

> **Axiom không cần có một “AI subsystem”.**

Tensor, Linear Algebra, AD, FFT, Convolution và Scientific Computing đều trở thành các **semantic domains** dùng chung một compiler infrastructure. Vì vậy cùng một optimizer có thể biến một chương trình Axiom từ biểu thức cấp cao xuống **SIMD CPU, đa luồng, GPU hoặc native machine code** mà không cần tạo một compiler riêng cho từng lĩnh vực.