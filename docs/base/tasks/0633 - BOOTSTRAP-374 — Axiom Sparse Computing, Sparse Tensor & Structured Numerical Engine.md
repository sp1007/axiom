# BOOTSTRAP-374 — Axiom Sparse Computing, Sparse Tensor & Structured Numerical Engine

Sau **373 — Scientific Computing, FFT & Numerical Transform**, bước tiếp theo hợp lý là **Sparse Computing**.

Lý do: hệ thống hiện tại đã xử lý rất tốt dữ liệu dense:

```text
Scalar
 → Vector
 → Tensor
 → Matrix
 → Linear Algebra
 → Transform
 → AD
```

Nhưng nhiều bài toán thực tế không thể dùng dense representation hiệu quả:

- sparse matrix;
- sparse tensor;
- graph;
- recommendation;
- scientific simulation;
- finite-element methods;
- sparse neural networks;
- large linear systems;
- compressed gradients;
- irregular numerical computation.

Nếu Axiom chỉ tối ưu dense tensor thì tầng scientific/AI vẫn thiếu một mảnh quan trọng.

---

# 1. Sparse không phải một kiểu dữ liệu duy nhất

Không nên tạo:

```text
Sparse<T>
```

và để compiler tự đoán representation.

Sparse representation phải explicit về semantic layout:

```text
CSR
CSC
COO
BSR
ELL
HYB
BlockSparse
CoordinateSparse
CompressedSparse
```

Và tensor có thể có:

```text
SparseLayout
```

tương tự như dense có `Layout`.

---

# 2. Sparse tensor là Tensor specialization

Không tạo hierarchy:

```text
class Tensor
class SparseTensor extends Tensor
```

Thay vào đó:

```text
Tensor<T, Shape, Layout, Storage>
```

có thể sử dụng:

```text
SparseLayout
```

Ví dụ:

```text
SparseTensor<f32, [1000000,1000000], CSR>
```

về semantic vẫn là tensor.

Điều này phù hợp với thiết kế generic/trait của Axiom.

---

# 3. CSR semantics

CSR conceptual:

```text
values
column_indices
row_offsets
```

Ví dụ:

```text id="g9y7p3"
row_offsets = [0, 2, 3, 5]
columns     = [0, 4, 2, 1, 3]
values      = [...]
```

Compiler phải biết:

```text
shape
nnz
index type
value type
storage
```

nhưng không cần expose internal pointer structure cho programmer nếu API high-level đủ dùng.

---

# 4. Sparse invariants

CSR phải có invariant:

```text
row_offsets[0] == 0
row_offsets[last] == nnz
row_offsets[i] <= row_offsets[i+1]
```

và:

```text
column index < number_of_columns
```

Compiler/library có thể đánh dấu:

```text
ValidatedCSR
```

sau khi validation.

---

# 5. COO

COO:

```text
row[]
column[]
value[]
```

rất thuận tiện cho:

- construction;
- insertion;
- interchange;
- dynamic sparse generation.

Nhưng không nhất thiết tối ưu cho mọi computation.

Compiler có thể chuyển:

```text
COO → CSR
```

nếu cost model chứng minh cần.

---

# 6. Conversion giữa sparse formats

Axiom cần semantic operation:

```text id="t1n5rc"
SPARSE_CONVERT(A, target_layout)
```

Ví dụ:

```text id="o5m8vk"
COO → CSR
CSR → CSC
CSR → BSR
```

Conversion là computation thực sự.

Không được coi là type cast miễn phí.

---

# 7. Sparse vs dense conversion

```text
dense → sparse
```

cần threshold/predicate:

```text id="j6q9xk"
abs(x) > threshold
```

nhưng threshold semantics phải explicit.

Ngược lại:

```text id="w2m5zn"
sparse → dense
```

có thể rất tốn memory.

Compiler không được tự động densify chỉ vì một operation chưa có sparse implementation.

---

# 8. Sparse operations

Semantic layer cần:

```text id="d7v4hs"
SPARSE_ADD
SPARSE_SUB
SPARSE_SCALE
SPARSE_MATMUL
SPARSE_MV
SPARSE_TRANSPOSE
SPARSE_REDUCE
SPARSE_GATHER
SPARSE_SCATTER
SPARSE_ELEMENTWISE
```

Không nhất thiết mọi operation phải được compiler intrinsic hóa ngay.

Nhưng semantics phải tồn tại để optimizer có thể nhận diện.

---

# 9. Sparse matrix multiplication

Ví dụ:

```text id="0u9x3f"
C = A @ B
```

với:

```text id="q5m7ke"
A = CSR
B = CSR
```

có thể dùng:

```text id="z4c2nm"
SpGEMM
```

Compiler phải phân biệt:

```text id="e7w1xp"
GEMM
```

với:

```text id="f6r8vq"
SpGEMM
```

vì complexity/memory behavior khác hoàn toàn.

---

# 10. Sparse × dense

Ví dụ:

```text id="q3k7mb"
A_sparse @ X_dense
```

có thể dùng:

```text id="h4v9sx"
SpMM
```

đây là pattern cực kỳ quan trọng trong AI và scientific computing.

---

# 11. Sparse × vector

```text id="v6c2rn"
y = A_sparse @ x
```

→ `SpMV`.

Compiler có thể tối ưu:

- row partitioning;
- SIMD;
- gather;
- cache;
- NUMA;
- parallel workers;
- GPU sparse kernels.

---

# 12. Sparse reduction

Sparse:

```text id="a7x4qp"
sum(A)
```

không được đơn giản coi là sum của storage arrays.

Compiler phải hiểu implicit zeros.

Ví dụ:

```text id="w8k2fc"
A = [0, 0, 5, 0]
```

sum = `5`, không phải sum của metadata.

---

# 13. Sparse elementwise operation

Ví dụ:

```text id="j5m8qy"
C = A + B
```

với hai CSR.

Compiler phải xử lý:

```text id="p1c7wa"
intersection
union
implicit zeros
duplicate entries
```

---

# 14. Duplicate sparse entries

COO có thể chứa:

```text id="b7q3zs"
(0,0,2)
(0,0,5)
```

Phải định nghĩa:

```text id="k9m2xd"
duplicate semantics
```

Có thể:

```text id="a6f1vp"
sum
last-write
reject
custom combine
```

Nhưng default phải rõ ràng.

---

# 15. Canonical sparse form

Compiler/library nên có concept:

```text id="y3q8lv"
CanonicalSparse
```

ví dụ CSR:

- sorted column indices;
- no duplicate entries;
- valid offsets.

Sau khi canonicalize:

```text id="m7p2cz"
SparseProof
```

có thể được dùng để bỏ validation runtime.

---

# 16. Sparse views

Tương tự dense:

```text id="s8x4qp"
TensorView
TensorMutView
```

Sparse cần semantic view:

```text id="j1v6nk"
SparseView<T>
SparseMutView<T>
```

nhưng view không được cho phép mutation phá cấu trúc sparse.

Ví dụ nếu đang có:

```text id="e8c2yf"
CSR view
```

thêm một non-zero mới có thể thay đổi:

```text id="q4w9mx"
row_offsets
indices
values
```

Do đó:

> Mutation of values và mutation of sparsity structure phải là hai capability khác nhau.

---

# 17. Structural mutation

Có thể phân biệt:

```text id="3v7nqk"
SparseValueMutView
SparseStructureMut
```

`SparseValueMutView`:

```text id="j2x8mc"
values[i] = ...
```

không thay đổi sparsity pattern.

`SparseStructureMut` có thể:

```text id="x9c4vf"
insert
remove
reallocate
reorder
```

và do đó invalidates các views liên quan.

Compiler phải theo dõi capability này.

---

# 18. Sparse ownership

Một sparse matrix:

```text id="n4b7sk"
A
```

sở hữu:

```text id="r7q2xm"
values
indices
offsets
```

Không được để một view sống lâu hơn các storage components cần thiết.

Ownership engine của Axiom đã có đủ foundation cho việc này.

---

# 19. Sparse GPU

GPU sparse computation có những pattern khác CPU.

Compiler có thể chọn:

```text id="k8f3zm"
CSR
ELL
HYB
BlockSparse
```

tùy:

```text id="w6j2qa"
row length distribution
density
warp divergence
memory coalescing
target GPU
```

Không nên hard-code một sparse format cho GPU.

---

# 20. Sparse + SIMD

Sparse SIMD khó hơn dense vì:

```text id="p8m4xq"
gather
irregular indices
```

Compiler cost model phải quyết định:

```text id="s5z1nh"
scalar
SIMD gather
blocked sparse
reorder
```

Không vectorize chỉ vì loop có vẻ phù hợp.

---

# 21. Sparse + parallel

Ví dụ SpMV:

```text id="c4x7jb"
for row in rows:
    y[row] = dot(A[row], x)
```

có thể parallel theo row nếu:

```text id="q1m6za"
rows independent
```

Compiler có thể partition:

```text id="n5v8yc"
row blocks
```

và vectorize inner loop.

---

# 22. Load balancing

Sparse rows có thể rất không đều:

```text id="a2x7hf"
row 0: 2 elements
row 1: 4 elements
row 2: 500000 elements
```

Static partitioning có thể rất kém.

Compiler/runtime có thể chọn:

```text id="p6r9ws"
static
dynamic
guided
work stealing
```

dựa trên sparsity statistics.

---

# 23. Sparse statistics

Sparse container có thể có metadata:

```text id="b4k8xm"
nnz
density
row_nnz_distribution
block_structure
sortedness
duplicate_state
```

Đây là **optimization metadata**, không phải semantic result.

Nếu metadata stale, correctness không được thay đổi.

---

# 24. Sparse pattern analysis

Compiler có thể phân tích:

```text id="v9m3ka"
A @ x
A @ B
A + B
```

và phát hiện pattern.

Ví dụ nếu sparsity pattern cố định qua nhiều iterations:

```text id="y2q6fp"
factorization
```

có thể reuse symbolic analysis.

---

# 25. Symbolic vs numeric sparse factorization

Đây là distinction quan trọng.

Ví dụ sparse LU:

```text id="e6v1zc"
Symbolic phase
```

xác định:

```text id="j3r8qb"
fill pattern
ordering
structure
```

Sau đó:

```text id="h5k2xn"
Numeric phase
```

tính numerical values.

Axiom nên có semantic distinction giữa hai phase.

---

# 26. Sparse solver foundation

373 có linear solve.

374 bổ sung:

```text id="sparse_solve"
```

với:

```text id="k7m1wp"
SparseLU
SparseQR
SparseCholesky
IterativeSolve
```

nhưng đây vẫn là library semantics.

---

# 27. Iterative solvers

Scientific computing cần:

```text id="y6p3cs"
CG
BiCGSTAB
GMRES
MINRES
```

Compiler không cần hard-code từng solver ngay.

Có thể có generic abstraction:

```text id="q9w4vx"
LinearOperator<T>
```

với operation:

```text id="r2k7mn"
apply(x)
```

Nhưng compiler phải hiểu rằng đây là computational operator chứ không phải ordinary object dispatch nếu static type cho phép specialize.

---

# 28. LinearOperator

Một `LinearOperator` có thể đại diện cho:

```text id="h8c3za"
DenseMatrix
SparseMatrix
FFT operator
Convolution operator
Implicit PDE operator
GPU operator
```

và expose:

```text id="n1m7rq"
y = A.apply(x)
```

Compiler có thể inline/specialize nếu concrete type known.

---

# 29. Sparse AD

Sparse computation phải tương thích AD.

Ví dụ:

```text id="m5v8kx"
loss = sparse_matmul(A, x)
```

gradient có thể là:

```text id="z2q6wc"
grad_x
grad_values
```

nhưng không nhất thiết gradient structure giống primal structure.

Đây là điểm quan trọng:

> Sparsity của value và sparsity của derivative là hai semantic properties khác nhau.

---

# 30. Sparse gradient structure

Ví dụ operation:

```text id="s9k4nb"
y = A_sparse @ x
```

gradient theo `A` chỉ có entries tương ứng với structural nonzeros nếu operation semantics giữ sparsity structure cố định.

Nếu structural sparsity có thể thay đổi:

```text id="x7p2qm"
gradient w.r.t structure
```

không phải ordinary numeric gradient.

Compiler phải reject hoặc yêu cầu custom derivative semantics.

---

# 31. Sparse neural networks

Axiom không cần neural-network primitives.

Nhưng:

```text id="SparseTensor
SpMM
BlockSparse
AD
GPU
```

đủ để library xây:

```text id="5c8w1v"
sparse neural layers
```

và compiler có thể optimize chúng.

---

# 32. Block sparse

Block sparse đặc biệt quan trọng vì:

```text id="u6x3za"
block = 4x4
block = 16x16
block = 32x32
```

cho phép:

```text id="r1m8qp"
SIMD
cache locality
GPU memory coalescing
```

tốt hơn arbitrary sparse.

Compiler có thể chọn block size theo target/cost model.

---

# 33. Graph representation

Graph có thể dùng sparse structures:

```text id="q5c8mx"
CSR adjacency matrix
```

Nhưng Axiom không nên biến Graph thành special Core type.

Library có thể xây:

```text id="k3v7nf"
Graph<Node, Edge>
```

trên:

```text id="z9p2xa"
Sparse
Collections
Ownership
```

Sau này compiler có thể recognize graph algorithms.

---

# 34. External sparse libraries

Có thể FFI:

```text id="p6m1vw"
SuiteSparse
cuSPARSE
rocSPARSE
MKL sparse
```

nhưng native fallback vẫn phải tồn tại nếu Axiom muốn giữ mục tiêu độc lập toolchain/runtime.

---

# 35. CompilerDB

374 bổ sung:

```text id="q7x4nb"
SparseDB
SparseTypeDB
SparseLayoutDB
SparseStorageDB
SparseShapeDB
SparsePatternDB
SparseValueDB
SparseIndexDB
SparseCanonicalDB
SparseValidationDB
SparseConversionDB
SparseViewDB
SparseMutationDB
SparseStructureDB
SparseValueMutationDB
SparseOperationDB
SparseAddDB
SparseMatmulDB
SparseMatvecDB
SparseSpMMDB
SparseSpMVDB
SparseReduceDB
SparseGatherDB
SparseScatterDB
SparseBlockDB
SparseBlockLayoutDB
SparsePartitionDB
SparseLoadBalanceDB
SparseStatisticsDB
SparseSymbolicDB
SparseNumericDB
SparseFactorizationDB
SparseSolverDB
SparseOperatorDB
SparseADDB
SparseGradientDB
SparseCpuDB
SparseSimdDB
SparseParallelDB
SparseGpuDB
SparseCostModelDB
SparseProofDB
SparseVerificationDB
```

---

# 36. MIR additions

Semantic MIR:

```text id="f1m8zc"
SPARSE_CREATE
SPARSE_VIEW
SPARSE_MUT_VIEW

SPARSE_LOAD_VALUE
SPARSE_STORE_VALUE

SPARSE_INSERT
SPARSE_REMOVE

SPARSE_CANONICALIZE
SPARSE_VALIDATE
SPARSE_CONVERT

SPARSE_ADD
SPARSE_MUL
SPARSE_SCALE

SPARSE_MV
SPARSE_MM

SPARSE_GATHER
SPARSE_SCATTER

SPARSE_REDUCE

SPARSE_SYMBOLIC_ANALYZE
SPARSE_NUMERIC_FACTOR

SPARSE_SOLVE
```

Sau optimization chúng có thể lower thành:

```text id="2c6v9q"
ordinary loops
SIMD
parallel regions
GPU kernels
```

hoặc backend/library calls.

---

# 37. Proof system

Cần:

```text id="s8k3yp"
SparseShapeProof
SparseLayoutProof
SparseIndexProof
SparseBoundsProof
SparseCanonicalProof
SparseDuplicateProof
SparseAliasProof
SparseStructureProof
SparseMutationProof
SparseConversionProof
SparseParallelProof
SparseVectorProof
SparseGpuProof
SparseADProof
SparseNumericalProof
SparseSolverProof
```

Đặc biệt `SparseStructureProof` rất quan trọng để compiler biết:

```text id="n2w6ck"
value mutation
```

không làm invalid các structure-dependent views.

---

# 38. Invariants

### `ASPAR-01`
Sparse representation phải có explicit layout semantics.

### `ASPAR-02`
CSR/CSC/COO/BSR/ELL không được bị coi là semantic-equivalent storage layout nếu observable representation khác.

### `ASPAR-03`
Sparse container phải bảo toàn shape semantics.

### `ASPAR-04`
Sparse indices phải được bounds-verified trong safe code.

### `ASPAR-05`
CSR offset invariants phải được bảo đảm.

### `ASPAR-06`
Duplicate-entry semantics phải được xác định.

### `ASPAR-07`
Canonical sparse state phải có explicit validity contract.

### `ASPAR-08`
Sparse format conversion không được mặc định là zero-cost cast.

### `ASPAR-09`
Dense↔Sparse conversion phải có explicit semantics.

### `ASPAR-10`
Implicit zero semantics phải được bảo toàn.

### `ASPAR-11`
Sparse value mutation phải được phân biệt với structural mutation.

### `ASPAR-12`
Structural mutation phải invalidate các capability/view bị ảnh hưởng.

### `ASPAR-13`
Sparse views không được outlive backing storage.

### `ASPAR-14`
Sparse operations phải tuân ownership/capability rules.

### `ASPAR-15`
Sparse parallelization phải chứng minh race safety.

### `ASPAR-16`
Sparse SIMD transformation phải chứng minh gather/scatter legality.

### `ASPAR-17`
Sparse GPU kernels phải tuân GPU memory/address-space semantics.

### `ASPAR-18`
Sparse format selection có thể phụ thuộc target/cost model.

### `ASPAR-19`
Format conversion có thể được inserted tự động nếu semantics observable không thay đổi và cost model cho phép.

### `ASPAR-20`
Compiler không được tự động densify sparse data chỉ vì thiếu một optimization.

### `ASPAR-21`
Sparse reduction phải tính implicit-zero semantics chính xác.

### `ASPAR-22`
Sparse matrix multiplication phải được phân biệt với dense matrix multiplication ở cost/representation level.

### `ASPAR-23`
Sparse symbolic analysis phải được phân biệt với numeric factorization.

### `ASPAR-24`
Sparse factorization phải tuân numerical contract.

### `ASPAR-25`
Sparse solver convergence semantics không được bị thay đổi bởi unsafe optimization.

### `ASPAR-26`
Sparse AD phải phân biệt value sparsity và derivative sparsity.

### `ASPAR-27`
Structural sparsity không được tự động coi là differentiable numeric value.

### `ASPAR-28`
External sparse libraries không được là mandatory language dependency.

### `ASPAR-29`
Sparse transformations phải có verification/validation path.

### `ASPAR-30`
Nếu sparse abstraction được compile away hoàn toàn, generated code không được giữ lại runtime metadata không cần thiết.

---

## Vị trí sau 374

Tầng numerical của Axiom hiện có thể nhìn như:

```text
                         Numeric
                            │
                  ┌─────────┴─────────┐
                  ▼                   ▼
             Dense Data          Sparse Data
                  │                   │
                  ▼                   ▼
              Tensor              Sparse Tensor
                  │                   │
          ┌───────┼────────┐    ┌─────┼─────┐
          ▼       ▼        ▼    ▼     ▼     ▼
        Linear   FFT       AD  SpMV  SpMM  Solvers
        Algebra  Conv          │
          │       │            │
          └───────┼────────────┘
                  ▼
           Expression Graph
                  │
          ┌───────┼────────┐
          ▼       ▼        ▼
        SIMD   Parallel    GPU
```

Điểm đáng chú ý của **374** là Axiom giờ không còn bị giới hạn bởi mô hình **dense tensor + GPU**. Sparse representation, sparse computation và sparse AD đều nằm trên cùng ownership/shape/numerical/compiler infrastructure, nên về sau có thể xây các thư viện scientific, graph hoặc sparse-ML mà **không cần sửa lại Core language**.