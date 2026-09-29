# BOOTSTRAP-371 — Axiom Automatic Differentiation & Differentiable Programming Engine

Sau **370 — Linear Algebra**, bước tiếp theo hợp lý là **Automatic Differentiation (AD)**.

Đây là nền tảng để Axiom có thể xây các hệ thống:

- Machine Learning
- Deep Learning
- Optimization
- Scientific Computing
- Physics simulation
- Differentiable rendering
- Neural ODE
- inverse problems

mà **không cần đưa “AI” thành một phần bắt buộc của ngôn ngữ**.

Mục tiêu của task này là làm cho compiler có khả năng hiểu:

```text
f(x)
```

và sinh:

```text
df/dx
```

một cách có kiểm chứng, tối ưu được và tương thích với:

```text
Tensor
SIMD
Parallel
GPU
Comptime
Ownership
```

---

# 1. Trước tiên: AD không phải symbolic differentiation

Axiom phải phân biệt:

```text id="q9e4k1"
Symbolic differentiation
Automatic differentiation
Numerical differentiation
```

### Numerical differentiation

Ví dụ:

```text id="b8v1h6"
(f(x + ε) - f(x)) / ε
```

→ approximation.

### Symbolic differentiation

Biến:

```text id="0xw9gq"
x*x + sin(x)
```

thành:

```text id="r6a2k7"
2*x + cos(x)
```

→ manipulation của biểu thức.

### Automatic differentiation

Thực thi chương trình theo semantics mở rộng để tính derivative.

Axiom 371 tập trung vào **AD**.

---

# 2. Core philosophy

Không nên thêm syntax phức tạp như:

```text id="t8u4qf"
differentiate_everything<T, ...>
```

vào Core.

Có thể có compiler-known attribute:

```text id="n2w6hp"
@differentiate
fn f(...)
```

nhưng semantic foundation phải là compiler transformation.

---

# 3. Hai chế độ chính

Axiom cần hỗ trợ:

```text id="5wq8f4"
Forward Mode
Reverse Mode
```

và compiler/library có thể chọn.

---

# 4. Forward mode

Với:

```text id="q2p8xv"
y = f(x)
```

forward mode truyền:

```text id="5m7j2d"
value
derivative
```

Ví dụ conceptual:

```text id="3a1d9p"
Dual<T> {
    value: T
    derivative: T
}
```

Một phép:

```text id="q5y7r8"
z = x * x
```

trở thành:

```text id="x8m4ca"
z.value = x.value * x.value
z.derivative = 2 * x.value * x.derivative
```

Compiler không nhất thiết phải materialize `Dual<T>` như runtime struct.

---

# 5. Reverse mode

Reverse mode xây:

```text id="f1q6we"
primal computation
        ↓
tape / graph / checkpoint
        ↓
reverse propagation
        ↓
gradient
```

Đặc biệt phù hợp:

```text id="8y4hca"
many inputs
few outputs
```

ví dụ:

```text id="w2x5df"
loss = f(model_parameters, input)
```

với:

```text id="p7g2la"
millions of parameters
one scalar loss
```

---

# 6. AD không được phụ thuộc vào heap

Một implementation naive có thể tạo:

```text id="x4n7kb"
Node
Node
Node
Node
...
```

trên heap.

Axiom không được coi đây là bắt buộc.

Compiler có thể:

```text id="g0p2s9"
stack allocate
arena
static tape
SSA graph
checkpoint
recompute
```

tùy workload.

---

# 7. Primal và derivative

Mỗi differentiable value có conceptual:

```text id="a2z9v3"
Primal
Derivative
```

Nhưng compiler có thể optimize:

```text id="3e6m8r"
Primal + Derivative
```

thành registers/SSA values.

Không cần object header.

---

# 8. Differentiability

Không phải function nào cũng differentiable.

Compiler phải phân loại:

```text id="0h5x7v"
Differentiable
NonDifferentiable
ConditionallyDifferentiable
Unknown
```

Ví dụ:

```text id="m7d1qp"
x * x
```

→ differentiable.

Nhưng:

```text id="4f3b8a"
file.read()
```

→ non-differentiable.

---

# 9. Side effects

Function:

```text id="h8n5c2"
fn f(x) {
    print(x);
    return x*x;
}
```

có derivative của phần toán học, nhưng side effect:

```text id="a1v7qk"
print()
```

không thể tự động differentiate.

Do đó compiler cần:

```text id="5m4r9w"
EffectAnalysis
```

để xác định differentiable subset.

---

# 10. Differentiable function contract

Conceptual:

```text id="j9w5g1"
@differentiate
fn square(x: f32) -> f32 {
    x * x
}
```

compiler sinh:

```text id="s2n8xd"
square_primal
square_derivative
```

hoặc:

```text id="c4p7az"
square_with_grad
```

tùy API.

---

# 11. Derivative representation

Derivative có cùng type:

```text id="f8v2nc"
f32 → f32
```

hoặc:

```text id="k5q3jm"
Tensor<f32,S> → Tensor<f32,S>
```

Nhưng derivative của một vector/vector function có thể là Jacobian:

```text id="r7m1bh"
f : R^N → R^M
```

thì:

```text id="p9q4xs"
Df : R^N → R^M×N
```

Compiler không nên tự động materialize Jacobian nếu chỉ cần:

```text id="7c6m4a"
J·v
```

hoặc:

```text id="v9d2ka"
Jᵀ·v
```

---

# 12. JVP và VJP

Đây nên là semantic primitives.

### JVP

```text id="g6y1kp"
JVP(f, x, v)
```

tính:

```text id="9b2w7c"
J(x) · v
```

### VJP

```text id="k3m7zd"
VJP(f, x, w)
```

tính:

```text id="q8p4vs"
J(x)^T · w
```

Điều này quan trọng vì không cần tạo full Jacobian.

---

# 13. Higher-order differentiation

Axiom phải cho phép:

```text id="c6j9tr"
gradient(gradient(f))
```

hoặc:

```text id="x2m8fp"
differentiate(differentiate(f))
```

nếu function hợp lệ.

Compiler phải tránh tạo một hệ thống special-case cho từng derivative order.

AD transformation phải composable.

---

# 14. Higher-order AD

Conceptual:

```text id="0v3qka"
AD(AD(f))
```

phải vẫn quay về cùng IR.

Pipeline:

```text id="4j8nxy"
Source
 ↓
Typed HIR
 ↓
AD transformation
 ↓
Normal HIR/MIR
 ↓
Ownership
 ↓
Tensor
 ↓
SIMD/GPU
```

Không tạo “AD compiler” riêng biệt.

---

# 15. Derivative rules

Compiler/library cần derivative rule registry:

```text id="c8r5mv"
DerivativeRuleDB
```

Ví dụ:

```text id="6p1qxa"
d(x + y) = dx + dy

d(x * y) = dx*y + x*dy

d(sin(x)) = cos(x)*dx

d(exp(x)) = exp(x)*dx

d(log(x)) = dx/x
```

Rules phải có domain constraints.

---

# 16. Custom derivative

Có những function compiler không thể tự differentiate.

Ví dụ optimized GPU kernel:

```text id="m3c7yh"
fn custom_op(...)
```

library có thể cung cấp:

```text id="8s6v1k"
@derivative(custom_op)
fn custom_op_grad(...)
```

Nhưng derivative function phải có contract:

```text id="1q8c4m"
primal compatibility
shape compatibility
dtype compatibility
device compatibility
numerical contract
```

---

# 17. Derivative verification

Compiler không nên mù quáng tin custom derivative.

Có thể có:

```text id="j7d2vx"
DerivativeContract
```

và optional verification tooling:

```text id="s3f9pk"
finite difference test
symbolic test
property test
```

Nhưng finite difference **không phải proof**.

Compiler có thể đánh dấu:

```text id="2k5n8c"
TrustedDerivativeRule
```

nếu user/library cung cấp rule.

---

# 18. Branching

Function:

```text id="v9q1hb"
if x > 0 {
    x*x
} else {
    0
}
```

AD cần preserve branch semantics.

Derivative:

```text id="a7x4np"
if x > 0 {
    2*x
} else {
    0
}
```

tại boundary:

```text id="w6r2cm"
x = 0
```

có thể không differentiable.

Compiler phải không tự giả định differentiability tại discontinuity.

---

# 19. Loops

AD phải hoạt động với:

```text id="y4n7sv"
for
while
loop
```

Compiler có thể differentiate loop body và accumulate derivative.

Ví dụ:

```text id="4h1x8c"
var y = 1;

for i in 0..n {
    y *= x;
}
```

AD transformation phải tạo derivative semantics tương ứng.

---

# 20. Dynamic control flow

Reverse mode gặp vấn đề nếu branch/loop path phụ thuộc runtime.

Axiom cần IR có:

```text id="z6m3fa"
AD Control Flow Graph
```

không cần flatten mọi control flow.

Tape/state chỉ lưu những thông tin cần cho reverse execution.

---

# 21. Reverse tape

Compiler có thể xác định:

```text id="u5j2nz"
which values are needed during backward pass
```

và chỉ lưu chúng.

Ví dụ:

```text id="k9f1ra"
x
 ↓
mul
 ↓
relu
 ↓
loss
```

Nếu backward cần `x`:

```text id="b7m3qd"
save x
```

Nếu có thể recompute:

```text id="c2p8vf"
recompute x
```

thì không cần lưu.

---

# 22. Checkpointing

Đây là trade-off:

```text id="e4x7qm"
memory
vs
compute
```

Compiler/runtime có thể chọn:

```text id="h8p2lw"
save everything
save checkpoints
recompute
```

Cost model quyết định.

Không được làm thay đổi gradient semantics.

---

# 23. AD memory model

Tape/checkpoint storage phải tuân Axiom ownership.

Ví dụ:

```text id="w7c5ka"
GradientTape
```

có owner rõ ràng.

Không được tạo:

```text id="p9m2xf"
global hidden mutable tape
```

mà không có synchronization contract.

---

# 24. Reverse-mode mutation

Mutation là phần khó.

Ví dụ:

```text id="d5q7nw"
x += y
```

compiler phải hiểu mutation dependency.

AD transformation phải tạo derivative tương ứng.

Ownership/capability analysis chạy trước và sau transformation.

---

# 25. Tensor AD

Nếu:

```text id="b2m7qp"
x: Tensor<f32, [B,N]>
```

thì:

```text id="e5x9va"
gradient(f(x))
```

phải tạo tensor gradient tương thích shape.

Compiler có thể fuse:

```text id="4g1wkc"
primal kernel
+
gradient kernel
```

khi semantics cho phép.

---

# 26. AD + GPU

Pipeline:

```text id="6m4twp"
Tensor operation
      ↓
AD transform
      ↓
primal graph + backward graph
      ↓
kernel fusion
      ↓
GPU kernels
```

Ví dụ:

```text id="c0y7hd"
y = relu(A @ B)
```

có thể sinh:

```text id="v2p8kx"
forward GEMM
forward ReLU
backward ReLU
backward GEMM
```

sau đó fusion/tile/parallelize.

---

# 27. AD + SIMD

Derivative operations thường có cùng vector structure.

Ví dụ:

```text id="2q9bwc"
d(a*b)
```

→

```text id="1v5yfa"
da*b + a*db
```

có thể vectorize giống primal.

Không cần AD-specific SIMD ISA.

---

# 28. AD + parallelism

Forward/backward graph có thể chứa:

```text id="j7m4qc"
parallel reductions
parallel maps
```

nhưng backward reduction cần numerical contract.

Ví dụ gradient accumulation:

```text id="z3f8vn"
grad += contribution
```

có thể tạo race.

Compiler phải chọn:

```text id="q5h1yd"
atomic
private partial gradients + reduction
tree reduction
```

dựa trên semantics/cost model.

---

# 29. Gradient accumulation

Đây là một pattern compiler cần nhận diện:

```text id="6d4qba"
grad[x] += g
```

Các strategy:

```text id="7r2fmc"
Atomic accumulation
Thread-local accumulation
Workgroup accumulation
Tree reduction
Sorted reduction
```

Numerical semantics quyết định strategy nào legal.

---

# 30. Sparse gradients

Không phải gradient nào cũng dense.

Library có thể có:

```text id="q9v5cx"
SparseGradient<T>
```

Compiler không được tự động densify.

Shape/layout/storage contract vẫn áp dụng từ 369.

---

# 31. Non-differentiable types

Compiler cần trait/metadata:

```text id="f1x8zp"
Differentiable<T>
```

hoặc semantic property.

Ví dụ:

```text id="s7q2nm"
f32
f64
Tensor<f32>
```

differentiable.

Nhưng:

```text id="m4y8rk"
String
File
Socket
ThreadHandle
Mutex
```

không.

---

# 32. Integer differentiation

Integer không có derivative theo ordinary real calculus.

Do đó:

```text id="h8m3vc"
differentiate(fn(x: i32))
```

→ compile-time error nếu không có custom semantics.

Không tự động coi integer là real.

---

# 33. Boolean differentiation

Tương tự:

```text id="p3v9xa"
bool
```

không differentiable.

Nếu ML operation dùng:

```text id="1m5qkc"
mask
```

thì gradient semantics phải do operation định nghĩa.

Ví dụ ReLU:

```text id="x8k4pw"
gradient at x=0
```

phải có explicit convention.

---

# 34. Subgradient

Một số function:

```text id="4m9qvk"
abs
relu
max
```

không differentiable tại một số điểm.

Library có thể định nghĩa:

```text id="r7x3nb"
SubgradientRule
```

Compiler phải phân biệt:

```text id="m2q8vc"
Derivative
Subgradient
```

không gộp chúng.

---

# 35. Gradient API

Một high-level library API có thể:

```text id="j8v3sp"
let (value, grad) = value_and_grad(f, x);
```

Compiler semantic model:

```text id="x6n2wb"
DifferentiationRequest {
    function
    mode
    inputs
    outputs
    numerical_contract
}
```

---

# 36. `@differentiate`

Attribute có thể:

```text id="6q8mzr"
@differentiate(mode = auto)
fn loss(...)
```

Compiler có thể chọn:

```text id="r1v5cn"
forward
reverse
mixed
```

dựa trên:

```text id="n7k4dx"
input count
output count
tensor size
memory budget
target
cost model
```

---

# 37. Mixed mode

Với:

```text id="8q2mvs"
f: R^N → R^M
```

compiler có thể dùng:

```text id="x1z7pk"
forward for some dimensions
reverse for others
```

để tính Jacobian-vector products hiệu quả.

Không cần programmer manually split.

---

# 38. Higher-order graph

Compiler database:

```text id="q8c4ym"
ADTransformDB
ADFunctionDB
ADModeDB
ADInputDB
ADOutputDB
ADDerivativeRuleDB
ADCustomRuleDB
ADPrimalDB
ADDerivativeDB
ADJvpDB
ADVjpDB
ADJacobianDB
ADHessianDB
ADGraphDB
ADControlFlowDB
ADTapeDB
ADCheckpointDB
ADRecomputeDB
ADGradientDB
ADGradientAccumulationDB
ADSubgradientDB
ADNumericalDB
ADMemoryDB
ADCostModelDB
ADSpecializationDB
ADVerificationDB
```

---

# 39. MIR additions

Thêm các semantic operations:

```text id="g0m8xf"
AD_BEGIN
AD_END

AD_PRIMAL
AD_DERIVATIVE

AD_JVP
AD_VJP

AD_SAVE
AD_RESTORE
AD_CHECKPOINT
AD_RECOMPUTE

AD_GRAD_ACCUMULATE
AD_GRAD_ZERO

AD_BRANCH
AD_LOOP

AD_SUBGRADIENT
```

Sau AD transformation, các operation này có thể được hạ xuống **ordinary MIR**.

Điểm này rất quan trọng:

> AD không được trở thành một execution model thứ hai.

---

# 40. AD transformation pipeline

```text id="h6p3zq"
Typed HIR
    ↓
Differentiability Analysis
    ↓
Effect Analysis
    ↓
AD Mode Selection
    ↓
AD Transformation
    ↓
Primal + Derivative HIR
    ↓
Normal MIR
    ↓
Ownership / Capability
    ↓
Tensor / Parallel / SIMD / GPU
    ↓
Machine Optimization
```

---

# 41. Verification

Compiler phải kiểm tra:

```text id="g9x2vj"
ADShapeProof
ADTypeProof
ADControlFlowProof
ADMemoryProof
ADNumericalProof
ADDerivativeRuleProof
ADAliasProof
ADDeviceProof
```

Đặc biệt:

> AD-generated code phải được chạy qua **cùng ownership/memory/race verification** như code người dùng viết.

Không có special exemption.

---

# 42. AD transformation correctness

Mỗi transformation nên có contract:

```text id="r2m7wx"
Original function
        ↓
AD transformation
        ↓
Generated derivative
```

phải chứng minh:

```text id="q5k9cb"
primal result preserved
+
derivative semantics preserved
```

Trong compiler validation có thể dùng:

```text id="v8m3za"
finite-difference testing
randomized testing
property testing
symbolic reference implementation
```

nhưng testing chỉ bổ sung cho transformation proof/contract.

---

# 43. Performance principle

Không được thiết kế AD như:

```text id="3m7qwp"
AST interpreter
+
dynamic graph
+
heap nodes
+
virtual dispatch
```

mặc định.

Axiom có thể tạo:

```text id="5x1k9f"
static derivative code
SSA
stack/arena tape
fused kernels
SIMD
parallel reduction
GPU kernels
```

Mục tiêu:

```text id="9n4zdc"
AD abstraction
      ↓
native optimized code
```

---

# 44. Invariants

### `AAD-01`
AD là compiler transformation/semantic facility, không phải runtime requirement.

### `AAD-02`
AD phải phân biệt forward mode và reverse mode.

### `AAD-03`
Compiler có thể tự chọn mode khi semantics cho phép.

### `AAD-04`
AD không được yêu cầu heap-allocated computation graph.

### `AAD-05`
Generated primal code phải giữ nguyên semantics.

### `AAD-06`
Generated derivative code phải tuân numerical contract.

### `AAD-07`
Function có side effect không differentiable nếu effect không có derivative semantics.

### `AAD-08`
Non-differentiable types phải bị reject hoặc có explicit custom rule.

### `AAD-09`
Integer/boolean không được tự động coi là real-valued differentiable types.

### `AAD-10`
Custom derivative phải có explicit contract.

### `AAD-11`
Custom derivative không được bypass type checking.

### `AAD-12`
Custom derivative phải tương thích shape.

### `AAD-13`
Custom derivative phải tương thích dtype/storage/device contract.

### `AAD-14`
AD phải hỗ trợ control flow.

### `AAD-15`
AD phải hỗ trợ loops khi body/operation differentiable.

### `AAD-16`
Reverse-mode tape chỉ lưu dữ liệu cần thiết hoặc checkpoint theo cost model.

### `AAD-17`
Recomputation chỉ được dùng khi primal semantics vẫn tương đương.

### `AAD-18`
Gradient accumulation phải tuân memory/race semantics.

### `AAD-19`
Parallel gradient reduction phải tuân numerical contract.

### `AAD-20`
GPU gradient kernels phải trải qua GPU legality verification.

### `AAD-21`
Tensor AD phải bảo toàn shape/layout/device semantics.

### `AAD-22`
AD transformation không được phá ownership/lifetime semantics.

### `AAD-23`
Generated derivative code phải chạy qua ordinary ownership/capability verification.

### `AAD-24`
Higher-order differentiation phải composable với cùng AD infrastructure.

### `AAD-25`
JVP không được mặc định materialize full Jacobian.

### `AAD-26`
VJP không được mặc định materialize full Jacobian.

### `AAD-27`
Jacobian/Hessian materialization chỉ xảy ra khi API yêu cầu hoặc compiler chứng minh cần thiết.

### `AAD-28`
Subgradient phải được phân biệt với ordinary derivative.

### `AAD-29`
AD optimization phải có semantic-equivalence proof/contract.

### `AAD-30`
AD phải có thể lower xuống scalar, SIMD, CPU parallel, GPU và accelerator mà không tạo một runtime AD bắt buộc.

---

# 45. Vị trí của 371 trong Axiom

Sau task này, kiến trúc AI/scientific của Axiom bắt đầu hoàn chỉnh theo chuỗi:

```text
                Numeric Semantics
                       │
                       ▼
              Tensor / Shape / Layout
                       │
                       ▼
               Linear Algebra
                       │
                       ▼
             Automatic Differentiation
                       │
              ┌────────┴────────┐
              ▼                 ▼
           Forward           Reverse
              │                 │
              └────────┬────────┘
                       ▼
                 Tensor Graph
                       │
              ┌────────┼────────┐
              ▼        ▼        ▼
            SIMD     Parallel   GPU
              │        │        │
              └────────┼────────┘
                       ▼
                 Target Backend
                       │
                       ▼
                 Native Machine
```

Điểm quan trọng nhất của **371** là Axiom không cần trở thành “ngôn ngữ AI”.

Nó chỉ cần cung cấp một compiler đủ mạnh để:

```text
@differentiate
fn loss(...)
```

cuối cùng có thể trở thành:

```text
forward kernels
+
backward kernels
+
fused tensor operations
+
SIMD/GPU execution
+
native machine code
```

mà không cần một garbage collector, dynamic computation graph bắt buộc, object hierarchy hay runtime AD bắt buộc.