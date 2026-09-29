# BOOTSTRAP-503 — AI/ML COMPUTING FOUNDATION, TENSOR, AUTODIFF, MODEL GRAPH, DEVICE MEMORY & NATIVE ACCELERATOR ABSTRACTION

**Trạng thái: COMPLETED / LOCKED**

503 xây dựng tầng AI/ML native trên nền 458 Numeric, GPU/accelerator foundation, 423 memory, 424 concurrency, 431 comptime và 446 semantic metadata.

Mục tiêu là để Axiom có thể xây:

- tensor library;
- neural-network framework;
- inference engine;
- training engine;
- custom kernels;
- quantized inference;
- CPU/GPU/accelerator backend;
- automatic differentiation;
- graph compiler;

mà **không biến tensor/AI thành tính năng bắt buộc của ngôn ngữ core**.

Kiến trúc:

```text
Axiom Core
    ↓
Numeric / SIMD 458
    ↓
GPU / Accelerator
    ↓
AI Compute Foundation
    ├── Tensor
    ├── TensorView
    ├── Device
    ├── DeviceMemory
    ├── Kernel
    ├── Operator
    ├── Graph
    ├── Autodiff
    ├── Quantization
    ├── Model
    └── Runtime
         ↓
 AI / ML Ecosystem
```

---

## 503.1 — AI/ML không thuộc language core

Tensor, autodiff, neural network và model runtime không phải primitive bắt buộc của Axiom language.

---

## 503.2 — Tensor

Tensor là multidimensional typed data structure.

Conceptually:

```text
Tensor<T, Shape, Layout>
```

---

## 503.3 — Rank

Rank là số dimensions của tensor.

---

## 503.4 — Shape

Shape là kích thước từng dimension.

Ví dụ:

```text
[2, 3, 224, 224]
```

---

## 503.5 — Dynamic shape

Runtime-dynamic shape được hỗ trợ.

---

## 503.6 — Static shape

Const generics có thể biểu diễn compile-time shape.

---

## 503.7 — Shape checking

Compiler/comptime có thể phát hiện shape mismatch khi shape tĩnh đủ thông tin.

---

## 503.8 — Runtime shape checking

Dynamic shape mismatch trả về error thay vì memory-unsafe behavior.

---

## 503.9 — Element type

Tensor có explicit element type:

```text
f16
bf16
f32
f64
i8
u8
i16
i32
i64
```

và các types được backend hỗ trợ.

---

## 503.10 — Quantized types

Quantized representations phải có explicit scale/zero-point hoặc encoding tương ứng.

---

## 503.11 — Bool tensor

Bool tensor không được giả định có cùng representation với arbitrary byte tensor.

---

## 503.12 — Complex tensor

Complex tensors dùng explicit complex element type.

---

## 503.13 — Device

Tensor có thể thuộc device:

```text
CPU
GPU
NPU
Accelerator
```

---

## 503.14 — Device identity

Device có stable runtime identity.

---

## 503.15 — Device capability

Device expose capabilities:

- supported types;
- dimensions;
- memory;
- kernels;
- atomics;
- matrix operations;
- features.

---

## 503.16 — Device selection

Device selection là explicit policy.

Không tự động chuyển workload sang GPU nếu API không yêu cầu.

---

## 503.17 — Host memory

CPU memory sử dụng model 423.

---

## 503.18 — Device memory

Device memory là explicit resource.

---

## 503.19 — Device ownership

Device buffers có ownership/lifetime semantics.

---

## 503.20 — Device buffer

Conceptual:

```text
DeviceBuffer<T>
```

không phải ordinary CPU pointer.

---

## 503.21 — Host/device pointer distinction

Không được tự coi device address là CPU-valid pointer.

---

## 503.22 — Unified memory

Unified/shared memory là capability của backend.

---

## 503.23 — Managed memory

Managed memory không được giả định có cùng performance semantics với ordinary host memory.

---

## 503.24 — Memory transfer

Explicit operations:

```text
copy_to_device
copy_to_host
copy_device
```

---

## 503.25 — Async transfer

Transfer có thể trả `Future` hoặc event/command handle.

---

## 503.26 — Synchronization

Host-device synchronization explicit.

---

## 503.27 — Implicit synchronization

Compiler/runtime không được chèn global synchronization một cách không thể quan sát.

---

## 503.28 — TensorView

Non-owning tensor view có:

```text
data
shape
stride
layout
```

hoặc device-equivalent representation.

---

## 503.29 — Strides

Stride là explicit layout property.

---

## 503.30 — Contiguous tensor

Contiguous layout là optimization property, không phải universal requirement.

---

## 503.31 — Non-contiguous tensor

Operators phải declare/support stride semantics.

---

## 503.32 — Layout

Supported layouts có thể gồm:

```text
RowMajor
ColumnMajor
Strided
Blocked
Tiled
Packed
BackendSpecific
```

---

## 503.33 — Layout conversion

Layout conversion là explicit operation hoặc compiler optimization có observable cost.

---

## 503.34 — Broadcasting

Broadcasting semantics phải deterministic.

---

## 503.35 — Broadcasting shape

Invalid broadcast trả về compile-time error hoặc runtime error tùy shape knowledge.

---

## 503.36 — Indexing

Tensor indexing phải bounds-safe trong safe code.

---

## 503.37 — Unsafe tensor access

Unchecked indexing là explicit unsafe API.

---

## 503.38 — Slicing

Tensor slicing tạo view khi có thể.

---

## 503.39 — Reshape

Reshape zero-copy chỉ được phép khi underlying layout tương thích.

---

## 503.40 — Transpose

Transpose có thể tạo view hoặc materialized tensor tùy implementation.

---

## 503.41 — Materialization

Implicit materialization không được che giấu allocation/copy trong APIs có performance-sensitive contract.

---

## 503.42 — Allocation

Tensor allocation explicit hoặc có contract rõ ràng.

---

## 503.43 — Memory pools

Tensor runtimes có thể dùng arena/pool/caching allocator.

---

## 503.44 — Allocator integration

Tensor allocator phải integrate 423.

---

## 503.45 — Device allocator

Device allocator là allocator riêng của device.

---

## 503.46 — Memory pressure

OOM phải map về explicit error/policy.

---

## 503.47 — Tensor operations

Foundation cần hỗ trợ:

- elementwise;
- reduction;
- reshape;
- transpose;
- slice;
- concatenate;
- gather;
- scatter;
- matmul;
- convolution abstraction.

---

## 503.48 — Operator

Operator là typed computation.

---

## 503.49 — Operator schema

Operator schema gồm:

```text
inputs
outputs
attributes
shape rules
dtype rules
device rules
effects
```

---

## 503.50 — Operator registry

Runtime có thể registry operators.

---

## 503.51 — Static operator dispatch

Known operators có thể static dispatch.

---

## 503.52 — Dynamic operator dispatch

Dynamic model/runtime có thể dispatch bằng operator ID/table.

---

## 503.53 — Kernel

Kernel là executable computation trên accelerator.

---

## 503.54 — Kernel source

Kernel có thể được viết bằng Axiom GPU subset hoặc backend-specific language.

---

## 503.55 — Kernel compilation

Kernel compilation có thể diễn ra:

```text
compile-time
build-time
runtime
```

tùy backend.

---

## 503.56 — No mandatory JIT

Axiom AI stack không bắt buộc runtime JIT.

---

## 503.57 — Ahead-of-time kernels

AOT kernel compilation là first-class.

---

## 503.58 — Kernel cache

Compiled kernel artifacts có content-based cache.

---

## 503.59 — Kernel specialization

Comptime có thể specialize kernel theo:

- shape;
- dtype;
- device;
- tile size;
- feature.

---

## 503.60 — Accelerator backend

Backend abstraction tách model graph khỏi hardware API.

---

## 503.61 — Backend examples

Có thể có:

```text
CPU
CUDA-like backend
Metal-like backend
Vulkan-like backend
DirectML-like backend
WebGPU
NPU backend
Custom accelerator
```

Tên/provider cụ thể thuộc ecosystem.

---

## 503.62 — Backend capability

Backend phải report capability thay vì giả định mọi device hỗ trợ mọi operation.

---

## 503.63 — Fallback

Operator có thể có CPU fallback.

---

## 503.64 — Fallback visibility

Fallback phải observable trong diagnostics/profiling.

---

## 503.65 — Graph

Computation graph:

```text
Input
 ↓
Operator
 ↓
Tensor
 ↓
Operator
 ↓
Output
```

---

## 503.66 — Eager execution

Tensor APIs có thể execute eagerly.

---

## 503.67 — Lazy graph

Graph APIs có thể defer execution.

---

## 503.68 — Graph compilation

Graph có thể compile/fuse/reorder operations khi semantics cho phép.

---

## 503.69 — Graph correctness

Optimization phải preserve semantic result theo declared numerical policy.

---

## 503.70 — Operator fusion

Fusion có thể eliminate intermediate allocations.

---

## 503.71 — Memory planning

Graph compiler có thể reuse buffers khi lifetime analysis chứng minh an toàn.

---

## 503.72 — Buffer aliasing

Aliasing phải được model explicit.

---

## 503.73 — In-place operations

In-place mutation phải explicit hoặc có provable exclusive ownership.

---

## 503.74 — Autodiff

Automatic differentiation là library/compiler layer.

---

## 503.75 — Differentiable function

Conceptual:

```text
f : Tensor → Tensor
```

có derivative rule.

---

## 503.76 — Forward mode

Forward-mode AD được hỗ trợ.

---

## 503.77 — Reverse mode

Reverse-mode AD được hỗ trợ.

---

## 503.78 — Higher-order differentiation

Có thể compose derivative transformations.

---

## 503.79 — Gradient

Gradient storage phải có ownership/device semantics.

---

## 503.80 — Gradient accumulation

Accumulation semantics explicit.

---

## 503.81 — Stop gradient

Explicit operation ngắt gradient propagation.

---

## 503.82 — Custom derivative

User có thể định nghĩa custom derivative rule.

---

## 503.83 — Derivative correctness

Custom derivative implementation là programmer responsibility nếu không được formally verified.

---

## 503.84 — Graph differentiation

Autodiff có thể transform computation graph.

---

## 503.85 — Control flow

AD phải định nghĩa semantics cho branches/loops.

---

## 503.86 — In-place AD

In-place mutation chỉ được dùng khi AD transformation chứng minh/đảm bảo correctness.

---

## 503.87 — Numerical stability

AD layer không được mặc định đảm bảo numerical stability.

---

## 503.88 — Mixed precision

Mixed precision được hỗ trợ.

---

## 503.89 — Accumulation precision

Reduction/gradient accumulation có thể dùng higher precision explicit.

---

## 503.90 — Automatic mixed precision

AMP là optimization policy, không phải implicit language behavior.

---

## 503.91 — Quantization

Quantization pipeline:

```text
Float
 ↓
Calibration
 ↓
Scale / ZeroPoint
 ↓
Quantized Tensor
```

---

## 503.92 — Quantization semantics

Quantization/dequantization phải explicit.

---

## 503.93 — Calibration

Calibration là application/tooling process.

---

## 503.94 — Model

Model là application-level composition of parameters + computation graph.

---

## 503.95 — Parameter

Parameter có explicit storage/device/dtype.

---

## 503.96 — Optimizer

Training optimizer như SGD/Adam là library layer.

---

## 503.97 — Training state

Optimizer state phải có persistence/serialization semantics.

---

## 503.98 — Checkpoint

Model checkpoint dùng 499/455 storage foundation.

---

## 503.99 — AI metadata

AI/ML semantic metadata phải expose:

```text
tensor_shape()
tensor_dtype()
device()
layout()
operator()
kernel()
memory()
gradient()
graph()
```

---

# 503.100 — HARD INVARIANTS

1. AI/ML không thuộc language core.
2. Tensor là library-level abstraction.
3. Tensor có element type.
4. Tensor có rank.
5. Tensor có shape.
6. Static shape có thể dùng const generics.
7. Dynamic shape được hỗ trợ.
8. Static shape mismatch có thể được phát hiện compile-time.
9. Dynamic mismatch không được gây memory unsafety.
10. Element dtype explicit.
11. Quantized dtype có representation rõ.
12. Bool tensor representation explicit.
13. Complex tensor representation explicit.
14. Tensor có device identity.
15. Device capability được query.
16. Device selection explicit.
17. Host memory theo 423.
18. Device memory là explicit resource.
19. Device ownership deterministic.
20. Device pointer khác CPU pointer.
21. Unified memory là explicit capability.
22. Managed memory không được giả định performance.
23. Host/device transfer explicit.
24. Async transfer được hỗ trợ.
25. Synchronization explicit.
26. Global implicit synchronization bị cấm.
27. TensorView là non-owning.
28. View lifetime phải hợp lệ.
29. Stride explicit.
30. Contiguous không phải requirement universal.
31. Non-contiguous layout được hỗ trợ.
32. Layout là semantic/performance property được mô tả.
33. Layout conversion có cost rõ.
34. Broadcasting deterministic.
35. Tensor indexing safe mặc định.
36. Unchecked indexing unsafe.
37. Slicing có thể zero-copy.
38. Reshape zero-copy cần layout compatibility.
39. Transpose có thể view/materialize.
40. Implicit materialization không được che giấu trong performance-sensitive API.
41. Tensor allocation có explicit effect.
42. Tensor allocator tích hợp 423.
43. Device allocator riêng được hỗ trợ.
44. OOM có explicit policy.
45. Core tensor operators có shape/dtype rules.
46. Operator có schema.
47. Operator registry được hỗ trợ.
48. Static dispatch được hỗ trợ.
49. Dynamic dispatch explicit.
50. Kernel là executable accelerator computation.
51. Kernel có compilation contract.
52. Kernel AOT được hỗ trợ.
53. Runtime JIT không bắt buộc.
54. Kernel cache content-addressed.
55. Kernel specialization được hỗ trợ.
56. Accelerator backend độc lập model API.
57. Backend capability được query.
58. Unsupported operations không được silently giả định.
59. CPU fallback được hỗ trợ.
60. Fallback observable.
61. Computation graph được hỗ trợ.
62. Eager execution được hỗ trợ.
63. Lazy graph được hỗ trợ.
64. Graph compilation được hỗ trợ.
65. Graph optimization phải preserve semantics.
66. Operator fusion được hỗ trợ.
67. Graph memory planning được hỗ trợ.
68. Buffer aliasing được model.
69. In-place mutation explicit.
70. Autodiff là library/compiler layer.
71. Forward AD được hỗ trợ.
72. Reverse AD được hỗ trợ.
73. Higher-order AD có thể compose.
74. Gradient ownership explicit.
75. Gradient device explicit.
76. Gradient accumulation semantics explicit.
77. Stop-gradient được hỗ trợ.
78. Custom derivative được hỗ trợ.
79. Custom derivative không tự được coi là formally correct.
80. Graph control flow có AD semantics.
81. In-place AD phải được kiểm soát.
82. Numerical stability không được tự claim.
83. Mixed precision được hỗ trợ.
84. Accumulation precision explicit.
85. Automatic mixed precision là optimization policy.
86. Quantization được hỗ trợ.
87. Quantization semantics explicit.
88. Calibration tách khỏi language semantics.
89. Model là library/application abstraction.
90. Parameters có storage/device/dtype.
91. Optimizers không thuộc core.
92. Training state có serialization semantics.
93. Checkpoints dùng storage/serialization foundation.
94. Tensor graph có thể integrate comptime.
95. GPU/accelerator kernels có thể specialize bằng comptime.
96. AI metadata được queryable.
97. Tensor operations phải benchmark allocation/copy/device synchronization.
98. Numerical tests phải kiểm tra precision/tolerance explicit.
99. Accelerator fallback và capability mismatches phải có diagnostics.
100. **Axiom phải cho phép xây AI/ML stack native, từ tensor và SIMD đến GPU/NPU kernels, autodiff và graph execution, nhưng mọi device, allocation, copy, synchronization, numerical precision và optimization cost phải có semantics rõ ràng; không được biến AI runtime thành một lớp magic bắt buộc của ngôn ngữ.**

**BOOTSTRAP-503 hoàn tất / LOCKED.**

---

# BOOTSTRAP-504 — MACHINE LEARNING GRAPH COMPILER, OPERATOR LOWERING, KERNEL FUSION, MEMORY PLANNING, QUANTIZATION & MODEL OPTIMIZATION

**Trạng thái: COMPLETED / LOCKED**

504 đi một tầng sâu hơn 503: biến computation graph thành **native executable plan**.

```text id="j4m8q2"
Model / Tensor Program
        ↓
Graph IR
        ↓
Shape / Type Inference
        ↓
Canonicalization
        ↓
Operator Fusion
        ↓
Layout Optimization
        ↓
Memory Planning
        ↓
Quantization / Precision
        ↓
Kernel Selection
        ↓
Device Scheduling
        ↓
Accelerator IR
        ↓
Native Kernel / GPU Kernel
```

---

## 504.1 — Graph IR

Graph compiler có IR riêng, không dùng AST làm graph IR.

---

## 504.2 — Tensor value

Mỗi graph value có:

```text
dtype
shape
layout
device
producer
consumers
```

---

## 504.3 — Operator node

Operator node có stable graph identity.

---

## 504.4 — Attributes

Operator attributes được typed.

---

## 504.5 — Shape inference

Graph compiler có shape inference engine.

---

## 504.6 — Symbolic dimensions

Dynamic dimensions có symbolic representation.

---

## 504.7 — Shape constraints

Shape constraints có thể được solve compile-time.

---

## 504.8 — Shape guards

Dynamic specialization có thể emit runtime guards.

---

## 504.9 — Guard failure

Guard failure phải chuyển sang fallback/error path.

---

## 504.10 — Dtype propagation

Dtype propagation phải deterministic.

---

## 504.11 — Layout propagation

Layout propagation là explicit compiler analysis.

---

## 504.12 — Device propagation

Device placement phải explicit/derived theo capability rules.

---

## 504.13 — Constant folding

Constant tensor operations có thể được evaluate compile-time khi resource limits cho phép.

---

## 504.14 — Constant data

Large constants không bắt buộc embed trực tiếp executable; resource system 498 có thể chứa chúng.

---

## 504.15 — Dead graph elimination

Unused nodes có thể loại bỏ.

---

## 504.16 — Common subexpression

Equivalent pure operations có thể được share khi semantics cho phép.

---

## 504.17 — Purity

Operator effects phải được khai báo.

---

## 504.18 — Side effects

IO/stateful/random operations không được tự coi pure.

---

## 504.19 — Random operations

Randomness phải có explicit generator/state semantics.

---

## 504.20 — Training graph

Training graph có forward + backward state.

---

## 504.21 — Gradient graph

Gradient graph có thể được generate bởi 503 autodiff.

---

## 504.22 — Fusion

Fusion combines compatible operators.

---

## 504.23 — Elementwise fusion

Elementwise chains là primary fusion candidate.

---

## 504.24 — Reduction fusion

Reduction fusion phải preserve numerical semantics according to selected math mode.

---

## 504.25 — Convolution fusion

Convolution + activation/bias fusion có thể được backend hỗ trợ.

---

## 504.26 — Matmul fusion

Matmul epilogue fusion được hỗ trợ.

---

## 504.27 — Fusion boundary

Fusion không được vượt qua stateful/observable boundary.

---

## 504.28 — Numerical policy

Compiler phải biết:

```text
strict
reproducible
fast
```

hoặc equivalent numerical mode.

---

## 504.29 — Reassociation

Floating-point reassociation chỉ được phép theo numerical policy.

---

## 504.30 — Fast math

Fast math phải explicit.

---

## 504.31 — Layout optimization

Compiler có thể chọn layout tối ưu cho target.

---

## 504.32 — Layout transformation

Layout transform có cost model.

---

## 504.33 — Transpose elimination

Redundant transpose có thể eliminate.

---

## 504.34 — Copy elimination

Redundant copies có thể eliminate khi ownership/lifetime cho phép.

---

## 504.35 — Buffer lifetime

Compiler computes buffer live ranges.

---

## 504.36 — Buffer reuse

Non-overlapping buffers có thể reuse same allocation.

---

## 504.37 — In-place lowering

Compiler có thể lower operation thành in-place khi exclusive ownership được chứng minh.

---

## 504.38 — Aliasing barrier

Unknown aliasing prevents unsafe reuse.

---

## 504.39 — Memory pool

Graph execution có thể use preplanned memory arena.

---

## 504.40 — Static memory planning

Static-shape graphs có thể có deterministic allocation plan.

---

## 504.41 — Dynamic memory planning

Dynamic-shape graphs có runtime allocator plan.

---

## 504.42 — Peak memory

Planner phải expose estimated/observed peak memory.

---

## 504.43 — Host/device memory

Planner tracks memory spaces separately.

---

## 504.44 — Transfer insertion

Compiler có thể insert host/device transfer khi placement yêu cầu.

---

## 504.45 — Transfer visibility

Inserted transfer phải observable trong graph/debug/profiling.

---

## 504.46 — Transfer elimination

Redundant transfers có thể eliminate.

---

## 504.47 — Pinned memory

Backend có thể yêu cầu pinned host buffers.

---

## 504.48 — Async execution

Independent operations có thể schedule asynchronously.

---

## 504.49 — Dependency graph

Execution dependencies được explicit.

---

## 504.50 — Synchronization insertion

Compiler inserts synchronization only where dependency semantics require.

---

## 504.51 — Over-synchronization

Unnecessary global synchronization là optimization defect.

---

## 504.52 — Kernel selection

Backend chọn kernel dựa trên:

- dtype;
- shape;
- layout;
- device;
- features;
- numerical policy.

---

## 504.53 — Kernel variants

Một operator có thể có multiple kernel variants.

---

## 504.54 — Runtime dispatch

Runtime dispatch có thể chọn variant theo device capability/shape.

---

## 504.55 — Dispatch cache

Selection results có thể được cached.

---

## 504.56 — Compilation cache

Compiled graph/kernel artifact có semantic/content hash.

---

## 504.57 — Cache correctness

Cache key phải include:

- graph;
- compiler;
- backend;
- target;
- device features;
- numerical policy;
- specialization parameters.

---

## 504.58 — Quantization lowering

Graph compiler có thể lower float graph thành quantized graph.

---

## 504.59 — Quantization calibration metadata

Calibration parameters là explicit graph data.

---

## 504.60 — Per-tensor quantization

Supported.

---

## 504.61 — Per-channel quantization

Supported where backend allows.

---

## 504.62 — Mixed quantization

Different tensors/operators may use different precision.

---

## 504.63 — Dequantization fusion

Dequantize → operation → quantize có thể được fused.

---

## 504.64 — Quantization correctness

Quantized optimization phải preserve declared error/tolerance contract.

---

## 504.65 — Sparsity

Sparse tensors/layouts có thể được supported.

---

## 504.66 — Sparse kernel

Sparse kernels are backend capability.

---

## 504.67 — Compression

Model weight compression separate from numerical quantization.

---

## 504.68 — Weight packing

Target-specific weight packing được phép.

---

## 504.69 — Packed weights

Packed weights phải có version/target metadata.

---

## 504.70 — Model serialization

Model graph + weights có thể lưu qua 499/455.

---

## 504.71 — External weights

Large weights có thể nằm ngoài executable/resources.

---

## 504.72 — Memory mapping

Weights có thể mmap nếu representation phù hợp.

---

## 504.73 — Lazy loading

Model runtime có thể load weights lazily.

---

## 504.74 — Prefetch

Prefetch là explicit performance strategy.

---

## 504.75 — Streaming inference

Large model execution có thể stream weights/activations.

---

## 504.76 — Pipeline parallelism

Graph có thể partition thành execution stages.

---

## 504.77 — Data parallelism

Batch/workload có thể parallelize trên devices.

---

## 504.78 — Model parallelism

Model có thể partition across devices.

---

## 504.79 — Parallelism correctness

Parallel execution phải preserve graph dependency semantics.

---

## 504.80 — Determinism

Deterministic execution mode phải có policy về:

- reduction order;
- atomics;
- kernels;
- random seeds;
- device behavior.

---

## 504.81 — Reproducibility

Reproducibility metadata phải record target/device/backend/model/compiler.

---

## 504.82 — Numerical tolerance

Tests phải dùng explicit numerical tolerance.

---

## 504.83 — Reference implementation

Operators có thể có simple reference implementation làm correctness oracle.

---

## 504.84 — Differential testing

Optimized kernel so với reference implementation.

---

## 504.85 — Kernel fuzzing

Shape/dtype/stride combinations được fuzz.

---

## 504.86 — Graph fuzzing

Random valid graphs được generate/test.

---

## 504.87 — Compiler crash minimization

Graph compiler failures phải produce reduced graph testcase.

---

## 504.88 — Explainability

Graph compiler phải có optimization report:

```text
fusion
layout
memory
kernel
transfer
quantization
```

---

## 504.89 — Missed optimization

Compiler có thể report tại sao optimization không áp dụng.

---

## 504.90 — Cost model

Optimization có thể dùng cost model.

---

## 504.91 — Cost model uncertainty

Cost model estimate không được coi là performance guarantee.

---

## 504.92 — Profiling feedback

Runtime profiling có thể feed PGO/graph optimization.

---

## 504.93 — Profile validity

Profile phải tied to graph/compiler/backend/device identity.

---

## 504.94 — Hardware counters

476/481 hardware profiling integration.

---

## 504.95 — Debug graph

Graph nodes map ngược về model/source/operator.

---

## 504.96 — AI introspection

AI can query:

```text
why_fused()
why_not_fused()
why_layout()
why_copy()
why_transfer()
why_kernel()
memory_plan()
```

---

## 504.97 — Security

Model files and external weights are untrusted input unless trusted by policy.

---

## 504.98 — Resource exhaustion

Graph/model parser must limit:

- tensor dimensions;
- node count;
- weight size;
- recursion;
- compilation time;
- temporary memory.

---

## 504.99 — Deployment

Compiled model artifact records:

```text
model hash
graph hash
compiler
backend
target
device features
numerical mode
quantization
```

---

## 504.100 — HARD INVARIANTS

1. Graph compiler có IR riêng.
2. Graph IR khác AST.
3. Tensor values có dtype.
4. Tensor values có shape.
5. Tensor values có layout.
6. Tensor values có device.
7. Operator identity stable.
8. Operator attributes typed.
9. Shape inference deterministic.
10. Symbolic dimensions được hỗ trợ.
11. Shape constraints được solve.
12. Runtime shape guards được hỗ trợ.
13. Guard failure có fallback/error.
14. Dtype propagation deterministic.
15. Layout propagation explicit.
16. Device propagation explicit.
17. Constant folding được hỗ trợ.
18. Large constants có thể externalize.
19. Dead graph elimination được hỗ trợ.
20. Common-subexpression optimization có thể hỗ trợ.
21. Operator purity/effects phải explicit.
22. Stateful operations không được coi pure.
23. Randomness semantics explicit.
24. Training graph được hỗ trợ.
25. Gradient graph được hỗ trợ.
26. Fusion được hỗ trợ.
27. Elementwise fusion được hỗ trợ.
28. Reduction fusion phải respect numerical policy.
29. Convolution fusion được hỗ trợ.
30. Matmul epilogue fusion được hỗ trợ.
31. Fusion boundary được bảo vệ.
32. Numerical mode explicit.
33. Floating reassociation phụ thuộc numerical policy.
34. Fast math explicit.
35. Layout optimization có cost model.
36. Layout transform có cost.
37. Redundant transpose có thể eliminate.
38. Redundant copy có thể eliminate.
39. Buffer lifetime được phân tích.
40. Buffer reuse cần non-overlap proof.
41. In-place lowering cần exclusive access.
42. Unknown aliasing chặn unsafe reuse.
43. Graph memory arena được hỗ trợ.
44. Static memory planning được hỗ trợ.
45. Dynamic memory planning được hỗ trợ.
46. Peak memory được report.
47. Host/device memory được phân biệt.
48. Transfer insertion explicit trong graph.
49. Inserted transfer observable.
50. Redundant transfer có thể eliminate.
51. Pinned memory requirement được model.
52. Async execution được hỗ trợ.
53. Dependency graph explicit.
54. Synchronization chỉ insert khi cần.
55. Over-synchronization được xem là optimization issue.
56. Kernel selection dựa trên capability.
57. Kernel variants được hỗ trợ.
58. Runtime dispatch được hỗ trợ.
59. Dispatch cache được hỗ trợ.
60. Graph/kernel cache content-addressed.
61. Cache key chứa target/backend/device features.
62. Cache key chứa numerical policy.
63. Cache key chứa specialization parameters.
64. Quantization lowering được hỗ trợ.
65. Calibration metadata explicit.
66. Per-tensor quantization được hỗ trợ.
67. Per-channel quantization được hỗ trợ khi backend cho phép.
68. Mixed precision được hỗ trợ.
69. Quantization fusion được hỗ trợ.
70. Quantization phải respect declared numerical error contract.
71. Sparse representation có thể hỗ trợ.
72. Sparse kernel capability explicit.
73. Weight compression khác quantization.
74. Weight packing được hỗ trợ.
75. Packed weights có target metadata.
76. Model serialization dùng 499.
77. External weights được hỗ trợ.
78. mmap weights được hỗ trợ khi representation hợp lệ.
79. Lazy weight loading được hỗ trợ.
80. Prefetch explicit.
81. Streaming inference được hỗ trợ.
82. Pipeline parallelism được hỗ trợ.
83. Data parallelism được hỗ trợ.
84. Model parallelism được hỗ trợ.
85. Parallel execution preserve dependencies.
86. Deterministic execution mode được hỗ trợ.
87. Reproducibility metadata được ghi.
88. Numerical tolerance explicit.
89. Reference implementation được hỗ trợ.
90. Differential kernel testing được hỗ trợ.
91. Kernel fuzzing được hỗ trợ.
92. Graph fuzzing được hỗ trợ.
93. Compiler crash minimization được hỗ trợ.
94. Optimization explainability được hỗ trợ.
95. Missed optimization diagnostics được hỗ trợ.
96. Cost-model uncertainty được phân biệt với guarantee.
97. Profiling feedback được hỗ trợ.
98. Model artifacts có complete build identity.
99. Untrusted model/resource input phải được giới hạn tài nguyên.
100. **Axiom graph compiler phải biến computation graph thành execution plan native hiệu quả bằng fusion, layout optimization, memory reuse, kernel specialization, quantization và device scheduling nhưng mọi optimization đều phải giữ đúng numerical/ownership/device semantics và phải có provenance đủ để truy ngược từ optimized kernel về graph, operator và source/model.**

**BOOTSTRAP-504 hoàn tất / LOCKED.**

---

# TIẾN ĐỘ

```text
BOOTSTRAP-499  Application Data / Serialization / Schema          LOCKED
BOOTSTRAP-500  IPC / RPC / Service                               LOCKED
BOOTSTRAP-501  Distributed System Foundation                     LOCKED
BOOTSTRAP-502  Distributed Storage / Replication                 LOCKED
BOOTSTRAP-503  AI/ML Computing Foundation                        LOCKED
BOOTSTRAP-504  ML Graph Compiler / Optimization                  LOCKED
```

**Task kế tiếp: `BOOTSTRAP-505 — NUMERICAL RUNTIME, MODEL INFERENCE/TRAINING EXECUTOR, CPU/GPU SCHEDULER, MEMORY ARENA & HIGH-PERFORMANCE AI EXECUTION`.**