# BOOTSTRAP-370 — Axiom Linear Algebra, Tensor Algebra & Kernel Optimization Engine

Sau **369 — Tensor/Shape/Layout**, bước tiếp theo nên khóa **Linear Algebra semantics**. Đây là lớp trực tiếp biến Tensor thành các phép toán có ý nghĩa như `matmul`, `dot`, `transpose`, `solve`, `decomposition`, đồng thời tạo nền để compiler tối ưu chúng xuống SIMD, CPU parallel, GPU và accelerator.

Mục tiêu không phải biến Linear Algebra thành Core. Mục tiêu là định nghĩa **semantic contracts + compiler recognition** để một thư viện Axiom có thể đạt hiệu năng gần thư viện native chuyên dụng mà vẫn giữ type safety và numerical correctness.

---

## 1. Phân biệt Tensor Algebra và Linear Algebra

Tensor engine của 369 biết:

```text
shape
layout
stride
storage
dtype
device
```

Linear Algebra engine biết thêm:

```text
vector
matrix
dot product
inner product
outer product
matmul
convolution-like contraction
transpose
solve
decomposition
reduction
```

Ví dụ:

```text
A: Matrix<f32, M, K>
B: Matrix<f32, K, N>

C = A @ B
```

không chỉ là một tensor operation thông thường.

Compiler biết đây là:

```text
MatrixMultiplication
```

và có thể áp dụng algorithm-specific optimization.

---

# 2. Không tạo class Matrix trong Core

API có thể nằm ở library:

```text
Matrix<T, M, N>
Vector<T, N>
```

nhưng compiler chỉ cần nhận diện semantic traits/operations.

Ví dụ conceptual:

```text
struct Matrix<T, M, N, Layout> {
    storage: ...
}
```

Các method:

```text
transpose()
multiply()
solve()
det()
```

vẫn chỉ là functions/trait implementations theo triết lý Axiom.

---

# 3. Matrix multiplication là semantic operation

Compiler IR nên có operation riêng:

```text
MATMUL
```

thay vì chỉ thấy:

```text
for i
    for j
        for k
            C[i,j] += A[i,k] * B[k,j]
```

Tại sao?

Vì khi nhận diện được `MATMUL`, compiler có nhiều thông tin hơn:

```text
dtype
shape
layout
numerical contract
target
```

và có thể chọn:

```text
naive
blocked
tiled
SIMD
multithreaded
GPU
accelerator
```

---

# 4. Matmul semantics

Với:

```text
A: [M,K]
B: [K,N]
```

kết quả:

```text
C: [M,N]
```

Compiler tạo:

```text
MatmulShapeProof
```

Nếu:

```text
A: [M,K]
B: [X,N]
```

và `K` không tương thích `X`:

```text
compile-time error
```

nếu dimensions static.

---

# 5. Batched matmul

AI thường cần:

```text
[B,M,K] @ [B,K,N]
```

→

```text
[B,M,N]
```

hoặc broadcasting batch dimensions:

```text
[B,1,M,K]
@
[1,H,K,N]
```

Compiler cần một:

```text
BatchBroadcastProof
```

để xác định các batch dimensions.

Không được tạo copy batch chỉ để broadcasting.

---

# 6. Dot product

Phải phân biệt:

```text
elementwise_mul
dot
inner_product
outer_product
```

Ví dụ:

```text
dot(a,b)
```

có semantic:

```text
Σ a[i] * b[i]
```

và numerical contract riêng.

Compiler có thể lower thành:

```text
SIMD multiply
+
horizontal reduction
```

hoặc:

```text
GPU reduction
```

---

# 7. Reduction order

Với floating point:

```text
dot(a,b)
```

không được mặc định cho phép mọi thứ.

Có thể có:

```text
Strict
Deterministic
Fast
```

### Strict

Giữ reduction order contract.

### Deterministic

Có cùng kết quả theo cùng numerical target/profile.

### Fast

Cho phép tree reduction/reassociation.

Compiler phải biết contract trước khi vectorize hoặc parallelize.

---

# 8. BLAS-style operation recognition

Compiler nên có semantic categories:

```text
Level 1:
vector-vector

Level 2:
matrix-vector

Level 3:
matrix-matrix
```

Ví dụ:

```text
DOT
AXPY
GEMV
GEMM
GER
```

Không nhất thiết source phải gọi đúng tên BLAS.

Compiler có thể nhận diện:

```text
for ...
    y[i] += a * x[i]
```

thành:

```text
AXPY-like operation
```

nếu semantic equivalence được chứng minh.

---

# 9. Loop → Linear Algebra recognition

Đây là điểm rất mạnh.

Source:

```text
for i in 0..M {
    for j in 0..N {
        var s = 0;
        for k in 0..K {
            s += A[i,k] * B[k,j];
        }
        C[i,j] = s;
    }
}
```

compiler có thể nhận ra:

```text
MATMUL
```

và chuyển sang:

```text
blocked GEMM
```

thay vì chỉ vectorize từng loop.

Pipeline:

```text
Loop IR
   ↓
Reduction analysis
   ↓
Index analysis
   ↓
Affine/access pattern analysis
   ↓
Linear algebra recognition
   ↓
MATMUL
```

---

# 10. Tiling

Matmul naive:

```text
for i
  for j
    for k
```

có locality kém.

Compiler có thể chuyển thành:

```text
for ii in blocks
  for jj in blocks
    for kk in blocks
      compute_tile()
```

Tile size phụ thuộc:

```text
L1 cache
L2 cache
register count
SIMD width
GPU shared memory
target architecture
```

Đây là optimization, không phải semantics.

---

# 11. Register blocking

Sau cache tiling:

```text
Tile
 ↓
Register tile
 ↓
SIMD FMA
```

Ví dụ compiler có thể giữ:

```text
C[i:i+8, j:j+8]
```

trong vector registers.

Không cần programmer viết:

```text
vec<f32, 8>
```

trực tiếp.

---

# 12. Packing

Compiler có thể tạo temporary packed layout:

```text
A
 ↓
pack
 ↓
GEMM
```

nhưng chỉ khi cost model cho thấy có lợi.

Nếu matrix nhỏ:

```text
packing cost > compute gain
```

→ không pack.

---

# 13. Layout-aware matmul

Compiler phải biết:

```text
RowMajor
ColumnMajor
Strided
Blocked
```

Nếu:

```text
A = row-major
B = column-major
```

có thể chọn algorithm khác.

Không được ép:

```text
transpose/copy
```

mặc định.

---

# 14. Transpose

`transpose(A)` có hai trường hợp:

### View

Nếu chỉ đổi metadata:

```text
shape
stride
```

→ zero-copy.

### Materialized transpose

Nếu target kernel yêu cầu contiguous layout:

```text
transpose_copy(A)
```

→ tạo storage mới.

Compiler không được nhầm hai semantics.

---

# 15. GEMM specialization

Compiler có thể specialize:

```text
MATMUL<f32>
```

theo:

```text
shape
alignment
layout
CPU feature
GPU capability
numerical mode
```

Ví dụ:

```text
M,N,K small
→ register kernel

M,N,K medium
→ CPU blocked SIMD

large
→ threaded GEMM

GPU
→ tiled GPU kernel
```

---

# 16. Small matrix optimization

Một lỗi phổ biến là dùng GEMM lớn cho:

```text
2x2
3x3
4x4
```

Compiler nên có specialized kernels:

```text
MATMUL_2x2
MATMUL_3x3
MATMUL_4x4
```

và có thể inline hoàn toàn.

Ví dụ:

```text
Matrix<f32,3,3>
```

có thể trở thành một nhóm register operations, không allocation.

---

# 17. Matrix-vector

Operation:

```text
A @ x
```

với:

```text
A: [M,N]
x: [N]
```

→

```text
[M]
```

Compiler có thể dùng:

```text
SIMD dot per row
```

hoặc GPU mapping.

---

# 18. Outer product

```text
outer(a,b)
```

shape:

```text
[N] × [M]
→ [N,M]
```

Compiler có thể nhận ra:

```text
rank-1 update
```

và chọn specialized kernel.

---

# 19. Diagonal operations

Không nên materialize:

```text
diag(v)
```

thành:

```text
[N,N]
```

nếu chỉ cần logical diagonal matrix.

Có semantic:

```text
DiagonalView
```

với:

```text
shape = [N,N]
stride = N+1
```

hoặc specialized representation.

---

# 20. Sparse matrix foundation

Đây là phần cần chuẩn bị nhưng không cần đưa toàn bộ sparse implementation vào Core.

Semantic types:

```text
SparseMatrix<T>
SparseVector<T>
```

và layouts:

```text
CSR
CSC
COO
BSR
```

Compiler/library có thể biết:

```text
sparsity structure
```

nhưng không biến sparse matrix thành dense matrix.

---

# 21. Sparse matmul

Compiler phân biệt:

```text
dense × dense
dense × sparse
sparse × dense
sparse × sparse
```

vì algorithm khác nhau.

Ví dụ:

```text
SparseMatrix<f32>
@
Vector<f32>
```

→ sparse matrix-vector kernel.

---

# 22. Numerical solver foundation

Linear algebra library cần:

```text
solve(A,b)
```

không nên mặc định:

```text
inverse(A) * b
```

vì numerical behavior khác nhau.

Semantic operation:

```text
SOLVE_LINEAR_SYSTEM
```

cho phép backend chọn:

```text
LU
QR
Cholesky
iterative solver
specialized solver
```

---

# 23. Decomposition

Các semantic operations:

```text
LU
QR
Cholesky
SVD
EIGEN
```

có thể là library operations/compiler-recognized operations.

Compiler không nhất thiết implement algorithm trong Core compiler.

Nhưng IR có thể biểu diễn:

```text
LINEAR_SOLVE
MATRIX_FACTORIZE
```

để backend/library optimization có thể hoạt động.

---

# 24. Inversion

`inverse(A)` phải tồn tại như library API nhưng compiler có thể cảnh báo nếu context cho thấy:

```text
inverse(A) @ b
```

có thể được thay bằng:

```text
solve(A,b)
```

Tuy nhiên đây phải là:

```text
diagnostic / optimization
```

không được thay đổi semantics nếu numerical contract khác.

---

# 25. Matrix determinant

```text
det(A)
```

có numerical stability considerations.

Compiler chỉ nên treat:

```text
DET
```

là semantic operation.

Algorithm:

```text
LU
Laplace
specialized
```

là implementation choice.

---

# 26. Norms

Các operations:

```text
norm1
norm2
norm_inf
frobenius_norm
```

cần numerical contract.

Ví dụ `norm2` không nên đơn giản:

```text
sqrt(sum(x*x))
```

nếu có nguy cơ overflow/underflow.

Backend có thể dùng stable scaling algorithm.

---

# 27. Numerical stability metadata

Linear algebra operation có thể mang:

```text
NumericalStabilityClass
```

ví dụ:

```text
Stable
ConditionSensitive
Approximate
Iterative
```

Không nhất thiết expose toàn bộ cho programmer.

Compiler/library có thể dùng metadata để chọn implementation.

---

# 28. Autotuning

Với GEMM:

```text
M,N,K
dtype
CPU/GPU
cache
SIMD
```

không có một kernel tối ưu cho mọi trường hợp.

Axiom có thể hỗ trợ:

```text
KernelVariant
```

và cost model/PGO chọn:

```text
variant A
variant B
variant C
```

Runtime dispatch chỉ xảy ra nếu thông tin compile-time không đủ.

---

# 29. Library implementation vs compiler primitive

Đây là boundary cần freeze.

### Compiler biết:

```text
MATMUL
DOT
REDUCE
TRANSPOSE
SOLVE
```

ở mức semantic IR khi recognition thành công.

### Library biết:

```text
API
algorithm
fallback
specialized implementation
```

### Backend biết:

```text
machine instruction
GPU kernel
accelerator instruction
```

Như vậy compiler không biến thành một BLAS framework khổng lồ.

---

# 30. External BLAS integration

Axiom có thể gọi:

```text
MKL
OpenBLAS
BLIS
cuBLAS
rocBLAS
```

qua FFI.

Nhưng:

> Đây là optimization/deployment option, không phải dependency của language.

Axiom native implementation vẫn có thể tồn tại.

Compiler có thể chọn:

```text
Axiom-generated GEMM
```

hoặc:

```text
external optimized GEMM
```

theo build configuration.

---

# 31. ABI của external numeric libraries

FFI phải mô tả:

```text
layout
stride
dtype
alignment
ownership
threading
device
stream/queue
```

Không được giả định:

```text
Matrix<T>
```

tương thích C ABI chỉ vì memory layout nhìn có vẻ giống nhau.

Cần:

```text
@repr(C)
```

hoặc explicit FFI adapter.

---

# 32. Linear algebra + GPU

Pipeline:

```text
MATMUL
   ↓
Shape proof
   ↓
Layout analysis
   ↓
Numerical contract
   ↓
Cost model
   ↓
Target selection
   ├── CPU
   ├── SIMD
   ├── CPU parallel
   ├── GPU
   └── accelerator
```

GPU path:

```text
MATMUL
 ↓
Tile selection
 ↓
Shared-memory mapping
 ↓
Workgroup mapping
 ↓
SIMD/subgroup mapping
 ↓
GPU kernel
```

---

# 33. Linear algebra + ownership

Một API:

```text
fn matmul(
    a: TensorView<T>,
    b: TensorView<T>,
    out: TensorMutView<T>
)
```

không cần copy.

Compiler chỉ cần chứng minh:

```text
out
```

không conflict với input nếu operation yêu cầu no-alias.

Nếu operation hỗ trợ aliasing:

```text
matmul_inplace_safe(...)
```

thì contract khác.

---

# 34. Linear algebra + parallelism

Compiler có thể phân chia:

```text
C[M,N]
```

thành tiles:

```text
C[0:64,0:64]
C[0:64,64:128]
...
```

Mỗi tile:

```text
parallel worker
```

và bên trong:

```text
SIMD
```

Đây là:

```text
Parallel
  ↓
Tiling
  ↓
SIMD
```

hoặc GPU:

```text
Parallel
  ↓
Workgroup
  ↓
Subgroup
  ↓
Vector
```

---

# 35. Linear algebra + deterministic mode

Nếu:

```text
@deterministic
```

compiler không được tùy ý thay đổi reduction order.

Ví dụ:

```text
GEMM
```

có thể cần:

```text
fixed tile order
fixed reduction order
```

nếu numerical contract yêu cầu.

Performance có thể giảm, nhưng đây là trade-off explicit.

---

# 36. CompilerDB

Task 370 bổ sung:

```text id="c4y0vn"
LinearAlgebraDB
VectorAlgebraDB
MatrixAlgebraDB
MatmulDB
BatchedMatmulDB
DotProductDB
InnerProductDB
OuterProductDB
GemmDB
GemvDB
AxpyDB
TransposeDB
DiagonalDB
SparseMatrixDB
SparseLayoutDB
SparseOperationDB
LinearSolveDB
MatrixFactorizationDB
LUDB
QRDB
CholeskyDB
SVDDB
EigenDB
NormDB
ConditionNumberDB
LinearAlgebraPatternDB
AlgebraRecognitionDB
AlgebraRewriteDB
MatmulTilingDB
MatmulPackingDB
MatmulKernelDB
MatmulSpecializationDB
MatmulAutotuneDB
LinearAlgebraCostModelDB
LinearAlgebraNumericalDB
LinearAlgebraDeterminismDB
LinearAlgebraProofDB
```

---

# 37. MIR additions

Semantic operations:

```text id="9h8cx7"
MATMUL
BATCHED_MATMUL

DOT
INNER_PRODUCT
OUTER_PRODUCT

GEMM
GEMV
AXPY

TRANSPOSE
DIAGONAL

REDUCE_SUM
REDUCE_MAX
REDUCE_MIN

LINEAR_SOLVE
MATRIX_INVERSE
MATRIX_FACTORIZE

NORM
```

Không nhất thiết tất cả đều xuất hiện trực tiếp từ source.

Một loop thông thường có thể được compiler **recognize** thành các operation này.

---

# 38. Algebra proof

Compiler cần:

```text id="x6d2cu"
AlgebraRecognitionProof
MatmulShapeProof
MatmulAliasProof
MatmulLayoutProof
ReductionOrderProof
NumericalEquivalenceProof
KernelSelectionProof
```

Ví dụ:

```text id="hl1cqn"
Source loop
   ↓
recognized as MATMUL
   ↓
index mapping proven
   ↓
reduction proven
   ↓
alias constraints proven
   ↓
numerical contract compatible
   ↓
GEMM specialization legal
```

---

# 39. Invariants

### `ALIN-01`
Linear algebra operations có semantics độc lập với backend.

### `ALIN-02`
Matrix dimensions phải được kiểm tra theo shape semantics.

### `ALIN-03`
Static dimension mismatch phải là compile-time error.

### `ALIN-04`
Dynamic dimension mismatch phải được kiểm tra runtime.

### `ALIN-05`
Matmul không được implicit materialize tensor nếu không cần.

### `ALIN-06`
Broadcast batch dimensions phải tuân shape rules.

### `ALIN-07`
Broadcast không được tạo full-size copy nếu semantic không yêu cầu.

### `ALIN-08`
Transpose có thể là zero-copy view khi layout cho phép.

### `ALIN-09`
Materialized transpose phải là operation riêng về semantics/cost.

### `ALIN-10`
Dot product khác elementwise multiplication.

### `ALIN-11`
Reduction phải tuân numerical contract.

### `ALIN-12`
Floating-point reduction không được reassociate trong strict mode.

### `ALIN-13`
Parallel reduction phải giữ numerical semantics.

### `ALIN-14`
Compiler chỉ được nhận diện loop thành MATMUL khi semantic equivalence được chứng minh.

### `ALIN-15`
Matmul specialization không được thay đổi observable numerical behavior ngoài contract cho phép.

### `ALIN-16`
Tiling là optimization, không phải semantic requirement.

### `ALIN-17`
Packing chỉ được thực hiện khi cost model/semantics cho phép.

### `ALIN-18`
Small-matrix specialization phải giữ nguyên matrix semantics.

### `ALIN-19`
Layout-aware optimization không được phá stride semantics.

### `ALIN-20`
In-place linear algebra yêu cầu write/alias contract phù hợp.

### `ALIN-21`
No-alias optimization chỉ hợp lệ khi compiler có proof hoặc explicit trusted contract.

### `ALIN-22`
Sparse và dense representations phải có semantics phân biệt.

### `ALIN-23`
Sparse operation không được tự động densify nếu observable resource behavior bị thay đổi.

### `ALIN-24`
`solve(A,b)` không được mặc định semantic-equivalent với `inverse(A) @ b`.

### `ALIN-25`
Numerical stability là một consideration riêng với mathematical correctness.

### `ALIN-26`
External BLAS/accelerator libraries không phải dependency bắt buộc của Axiom.

### `ALIN-27`
External numeric ABI phải explicit về layout, ownership và storage.

### `ALIN-28`
Linear algebra optimization phải tái sử dụng ownership, memory, numeric và tensor proofs.

### `ALIN-29`
CPU/SIMD/GPU/accelerator implementations phải giữ cùng high-level semantics.

### `ALIN-30`
Linear algebra engine không được biến Core language thành một framework AI/BLAS cụ thể.

---

# 40. Vị trí kiến trúc sau 370

Axiom hiện hình thành một tầng rất rõ:

```text
                     Axiom Core
                         │
              ┌──────────┴──────────┐
              │                     │
        Numeric Semantics       Ownership
              │                     │
              └──────────┬──────────┘
                         │
                  Tensor Semantics
                         │
             Shape / Layout / Device
                         │
                Linear Algebra IR
                         │
          ┌──────────────┼──────────────┐
          │              │              │
        Scalar          SIMD          GPU
          │              │              │
          └──────────────┼──────────────┘
                         │
                  Target Optimizer
                         │
                   Native Code
```

Và đây là một điểm kiến trúc rất quan trọng:

**Axiom không cần có một “Tensor compiler” riêng biệt hay một “AI compiler” tách khỏi compiler chính.**

Thay vào đó:

```text
Source abstraction
       ↓
Typed semantic operation
       ↓
Proof
       ↓
High-level optimization
       ↓
Scalar/SIMD/Parallel/GPU lowering
       ↓
Machine optimization
```

Tất cả vẫn đi qua cùng **ownership + memory + numeric + proof infrastructure** đã xây dựng từ trước.