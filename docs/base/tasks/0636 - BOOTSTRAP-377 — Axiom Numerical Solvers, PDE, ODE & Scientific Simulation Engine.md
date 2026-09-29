# BOOTSTRAP-377 — Axiom Numerical Solvers, PDE, ODE & Scientific Simulation Engine

Sau **376 — Probabilistic Computing**, Axiom đã có đủ nền tảng Numeric → Tensor → Sparse → Graph → AD → Parallel → GPU để bước sang lớp **scientific simulation**.

Đây là tầng rất quan trọng nếu mục tiêu của Axiom là một ngôn ngữ có thể dùng cho:

- physics;
- engineering;
- CFD;
- FEM;
- robotics;
- control;
- climate simulation;
- scientific computing;
- differentiable simulation;
- GPU simulation.

Nguyên tắc vẫn giữ nguyên:

> **Solver không phải Core language primitive.**  
> Nhưng compiler phải hiểu đủ semantic structure để tối ưu solver xuống native code.

---

# 1. Phân biệt Problem, Discretization và Solver

Không được gom tất cả thành một abstraction.

Axiom phân biệt:

```text
Mathematical Problem
        ↓
Discretization
        ↓
Numerical Representation
        ↓
Solver
        ↓
Execution Strategy
```

Ví dụ:

```text
PDE
 ↓
finite difference
 ↓
sparse matrix
 ↓
iterative solver
 ↓
SIMD + parallel + GPU
```

hoặc:

```text
PDE
 ↓
finite element
 ↓
sparse block system
 ↓
multigrid
 ↓
GPU
```

---

# 2. ODE

Ordinary Differential Equation:

```text
dy/dt = f(t, y)
```

Axiom có abstraction:

```text
ODEProblem
```

nhưng đây là library type.

Ví dụ semantic API:

```text
solve(problem, method, options)
```

không yêu cầu runtime reflection.

---

# 3. ODE state

State có thể là:

```text
Scalar
Vector
Tensor
Struct
SparseVector
CustomState
```

Không giới hạn ODE vào `f64[]`.

Compiler dùng generic specialization.

---

# 4. ODE function

RHS:

```text
fn rhs(t: f64, y: view<f64>, dy: mut_view<f64>)
```

có thể compile trực tiếp thành:

```text
loop
SIMD
parallel
GPU
```

nếu không có dependency cản trở.

---

# 5. In-place ODE

Để tránh allocation:

```text
rhs(t, y, dy)
```

ưu tiên hơn:

```text
rhs(t, y) -> Tensor
```

nhưng cả hai đều hợp lệ.

Compiler có thể biến functional form thành in-place form khi semantic equivalence được chứng minh.

---

# 6. ODE methods

Library có thể cung cấp:

```text
Euler
Midpoint
RK2
RK4
RK45
DormandPrince
BDF
AdamsBashforth
AdamsMoulton
```

Không cần compiler hiểu từng implementation.

Compiler chỉ cần nhận diện các kernel:

```text
state update
stage evaluation
reduction
error estimate
```

---

# 7. Adaptive timestep

Solver có thể điều chỉnh:

```text
dt
```

dựa trên error estimate.

Điều này tạo control flow động.

Compiler không được giả định số timestep cố định trừ khi có proof.

---

# 8. Numerical tolerance

Tách:

```text
absolute_tolerance
relative_tolerance
```

và không được coi tolerance là optimization hint thuần túy.

Tolerance ảnh hưởng observable numerical behavior.

---

# 9. Numerical contract

Solver phải sử dụng:

```text
Strict
Deterministic
Fast
Approximate
```

đã có trong Numeric engine.

Ví dụ:

```text
Fast
```

cho phép reduction/reassociation rộng hơn.

---

# 10. Stiff ODE

Stiffness là semantic property của problem/solver selection.

Có thể dùng:

```text
ImplicitEuler
BDF
Rosenbrock
Radau
```

Compiler không cần tự động đoán solver đúng về mặt toán học.

Auto-selection chỉ được chọn trong tập solver thỏa declared contract.

---

# 11. Jacobian

Implicit solvers cần:

```text
J = ∂f/∂y
```

Có thể lấy bằng:

```text
analytical
AD
finite_difference
user_supplied
```

AD engine của Axiom là lựa chọn tự nhiên.

---

# 12. Jacobian-free methods

Không phải solver nào cũng cần materialize Jacobian.

Có thể cung cấp:

```text
JVP
```

thay vì:

```text
Jacobian matrix
```

Compiler có thể fuse:

```text
ODE
+
AD/JVP
+
Linear solver
```

để giảm memory traffic.

---

# 13. Event detection

ODE có thể có event:

```text
g(t, y) = 0
```

Ví dụ:

```text
collision
threshold
switch
```

Solver phải xác định event semantics.

Event function là observable control flow, không được optimize away nếu có side effect.

---

# 14. Hybrid dynamical systems

Một simulation có thể chuyển mode:

```text
Continuous
       ↓
Event
       ↓
Discrete
       ↓
Continuous
```

Axiom có thể biểu diễn bằng state machine + ODE solver thay vì tạo một runtime hierarchy riêng.

---

# 15. DAE

Differential-algebraic equations:

```text
F(t, y, y') = 0
```

cần:

```text
DAEProblem
```

và solver tương ứng.

Constraint equations phải được giữ tách biệt với ordinary differential equations.

---

# 16. PDE

Partial Differential Equation:

```text
∂u/∂t = L(u)
```

không nên là một Core syntax.

Thay vào đó:

```text
PDEProblem
Discretization
BoundaryCondition
InitialCondition
```

là library abstractions.

---

# 17. Boundary conditions

Phải có semantic distinction:

```text
Dirichlet
Neumann
Robin
Periodic
Mixed
```

Compiler không cần hiểu mathematical theory nhưng representation phải preserve semantics.

---

# 18. Spatial discretization

Axiom hỗ trợ library:

```text
FiniteDifference
FiniteVolume
FiniteElement
Spectral
Particle
MeshFree
```

Mỗi loại tạo numerical representation khác nhau.

---

# 19. Finite Difference

Ví dụ:

```text
u[i-1] - 2*u[i] + u[i+1]
```

compiler có thể nhận diện stencil.

Đây là cơ hội lớn để tối ưu:

```text
Stencil
→ tiled loops
→ SIMD
→ parallel
→ GPU
```

---

# 20. Stencil abstraction

Nên có semantic metadata:

```text
Stencil {
    offsets
    coefficients
    boundary_behavior
}
```

Nhưng compiler có thể lower nó thành ordinary indexing.

Không cần runtime `Stencil` object.

---

# 21. Stencil fusion

Ví dụ:

```text
Laplacian(u)
→ gradient
→ flux
→ update
```

Compiler có thể fuse thành một kernel nếu:

- alias proof;
- bounds proof;
- numerical proof;
- dependency proof

đều hợp lệ.

---

# 22. Finite Volume

Finite volume dựa trên:

```text
cell
face
flux
conservation
```

Graph engine có thể biểu diễn connectivity.

Sparse engine có thể biểu diễn resulting systems.

Do đó không cần một memory model riêng.

---

# 23. Finite Element

FEM pipeline:

```text
Mesh
 ↓
Element
 ↓
Basis
 ↓
Quadrature
 ↓
Local matrix/vector
 ↓
Assembly
 ↓
Sparse global system
 ↓
Solver
```

Axiom có thể optimize từng stage.

---

# 24. FEM assembly

Naive:

```text
for element
    for local_i
        for local_j
            global_matrix[...] += local_matrix[...]
```

có contention.

Compiler có thể sử dụng:

```text
element partition
private local assembly
merge
```

thay cho atomic update khi proof cho phép.

---

# 25. Mesh

Mesh không phải graph đơn thuần.

Nó có:

```text
Geometry
Topology
ElementType
Boundary
Coordinates
Connectivity
```

Có thể xây trên graph + tensor + sparse.

---

# 26. Mesh identity

Node/element/face cần logical handles:

```text
VertexId
EdgeId
FaceId
CellId
ElementId
```

không phải raw pointers.

---

# 27. Mesh mutation

Phân biệt:

```text
GeometryMutation
TopologyMutation
AttributeMutation
```

Ví dụ:

```text
vertex.position = ...
```

không nhất thiết invalidate topology views.

Nhưng:

```text
split_edge()
```

có thể invalidate nhiều structures.

---

# 28. Linear system

Sau discretization thường có:

```text
A x = b
```

Axiom đã có Linear Algebra + Sparse.

Solver layer tái sử dụng:

```text
DenseMatrix
SparseMatrix
LinearOperator
Tensor
```

Không tạo một matrix type mới chỉ dành cho solver.

---

# 29. Direct solvers

Library:

```text
LU
Cholesky
QR
LDLT
SparseLU
SparseCholesky
```

đã có nền tảng từ task 370/374.

Solver engine bổ sung orchestration:

```text
factorize
solve
reuse factorization
```

---

# 30. Iterative solvers

Cần:

```text
CG
GMRES
BiCGSTAB
MINRES
TFQMR
```

và abstraction:

```text
LinearOperator
Preconditioner
StoppingCriterion
```

---

# 31. Matrix-free solver

Không nhất thiết materialize A.

Có thể:

```text
A(x)
```

trực tiếp.

Điều này cực kỳ quan trọng cho:

- PDE;
- GPU;
- huge systems.

Compiler có thể fuse:

```text
operator
+
vector operation
+
reduction
```

---

# 32. Preconditioner

Preconditioner:

```text
M⁻¹
```

có thể là:

```text
Jacobi
BlockJacobi
ILU
IC
AMG
Multigrid
```

là generic solver component.

---

# 33. Multigrid

Multigrid có structure:

```text
restriction
↓
coarse solve
↓
prolongation
↓
smoothing
```

Compiler có thể fuse kernels nếu storage/layout cho phép.

---

# 34. Nonlinear solver

Có:

```text
Newton
QuasiNewton
Broyden
FixedPoint
```

Newton:

```text
F(x) = 0
```

cần:

```text
Jacobian
linear solve
line search
```

Có thể reuse AD.

---

# 35. Optimization + solver

Scientific simulation thường:

```text
parameters
 ↓
simulation
 ↓
loss
 ↓
gradient
 ↓
optimization
```

Axiom có thể compile thành:

```text
Simulation
    ↓
AD
    ↓
Gradient
    ↓
Optimizer
```

mà không cần lưu toàn bộ runtime computation graph.

---

# 36. Checkpoint/recompute

Simulation lớn có thể vượt memory.

AD engine đã có checkpoint/recompute.

Solver layer phải cung cấp semantic boundaries:

```text
Checkpoint
Restart
Recompute
```

để AD có thể tối ưu memory.

---

# 37. Time integration + GPU

Một timestep:

```text
load
compute
boundary
reduce
update
```

có thể được fusion thành GPU kernel.

Compiler phải kiểm tra:

- dependency;
- synchronization;
- memory lifetime;
- numerical contract.

---

# 38. Simulation state

State có thể nằm ở:

```text
Host
Device
Unified
External
```

không có implicit transfer.

Ví dụ:

```text
solve_gpu(problem)
```

không được âm thầm copy hàng GB dữ liệu qua PCIe ở mỗi timestep.

Transfer phải là observable cost/explicit operation hoặc được abstraction contract cho phép.

---

# 39. Checkpoint storage

Simulation checkpoint có thể:

```text
save(state)
```

nhưng I/O là effect.

Compiler không được reorder checkpoint tùy tiện.

---

# 40. Solver pipeline

Semantic pipeline:

```text
Problem
  ↓
Discretization
  ↓
Representation
  ↓
Operator
  ↓
Solver
  ↓
Execution Plan
  ↓
CPU / SIMD / Parallel / GPU
```

Trong đó:

```text
Operator
```

là abstraction đặc biệt quan trọng.

---

# 41. Operator abstraction

Ví dụ:

```text
trait LinearOperator<T> {
    fn apply(x, y)
}
```

Không yêu cầu matrix.

Compiler có thể specialize:

```text
LinearOperator<SparseMatrix>
LinearOperator<Stencil>
LinearOperator<FEM>
LinearOperator<Graph>
```

thành kernel trực tiếp.

---

# 42. Operator fusion

Ví dụ:

```text
y = A(x)
z = B(y)
w = C(z)
```

có thể:

```text
A
 ↓
B
 ↓
C
```

được fuse nếu intermediate không observable.

Điều này tái sử dụng Expression Graph Engine.

---

# 43. Solver cost model

Compiler/runtime cần đánh giá:

```text
problem_size
sparsity
condition_estimate
memory_bandwidth
flops
parallelism
GPU_transfer
iteration_count
```

để lựa chọn implementation.

Không được thay đổi mathematical semantics.

---

# 44. Automatic solver selection

Có thể:

```text
solve_auto(problem)
```

nhưng lựa chọn phải bị giới hạn bởi contract.

Ví dụ:

```text
required_accuracy
determinism
memory_limit
target
```

Nếu không đủ thông tin:

```text
diagnostic
```

thay vì compiler tự ý chọn một solver có semantics khác.

---

# 45. Solver convergence

Convergence không nên là compiler assumption.

Solver phải trả:

```text
Converged
MaxIterations
Breakdown
Diverged
NumericalFailure
```

Ví dụ:

```text
Result<Solution, SolverError>
```

không dùng exception.

---

# 46. Floating-point failure

Phải phân biệt:

```text
Converged
ConvergedWithinTolerance
NumericalBreakdown
NaNDetected
InfDetected
Stagnation
```

để application có thể xử lý.

---

# 47. Deterministic solver

Một solver deterministic cần kiểm soát:

```text
reduction order
parallel scheduling
floating-point behavior
GPU atomic accumulation
```

Không chỉ seed RNG.

---

# 48. Approximate solver

Có thể có:

```text
Approximate
```

nhưng phải là explicit numerical contract.

Compiler được phép:

```text
reassociate
change reduction tree
use approximate math
```

chỉ khi contract cho phép.

---

# 49. Scientific simulation + probabilistic

Stochastic differential equation:

```text
dX = f(X,t)dt + g(X,t)dW
```

có thể kết hợp:

```text
ODE/SDE
+
RNG
+
Tensor
+
AD
+
GPU
```

Không cần thêm một runtime architecture hoàn toàn mới.

---

# 50. CompilerDB

Bổ sung:

```text
SolverDB
SolverProblemDB
SolverMethodDB
SolverOptionsDB
SolverToleranceDB
SolverConvergenceDB
SolverStoppingDB
SolverFailureDB
SolverCostModelDB

ODEDB
ODEProblemDB
ODERhsDB
ODEMethodDB
ODEStepDB
ODEAdaptiveStepDB
ODEEventDB
ODEJacobianDB
ODEStiffnessDB
ODEDAEDB

PDEDB
PDEProblemDB
PDEOperatorDB
PDEBoundaryDB
PDEInitialConditionDB
PDESpatialDiscretizationDB
PDETimeDiscretizationDB

StencilDB
StencilPatternDB
StencilBoundaryDB
StencilFusionDB
StencilOptimizationDB

MeshDB
MeshTypeDB
MeshVertexDB
MeshEdgeDB
MeshFaceDB
MeshCellDB
MeshElementDB
MeshGeometryDB
MeshTopologyDB
MeshConnectivityDB
MeshMutationDB
MeshPartitionDB

FEMDB
FEMElementDB
FEMBasisDB
FEMQuadratureDB
FEMAssemblyDB
FEMBoundaryDB

LinearOperatorDB
PreconditionerDB
DirectSolverDB
IterativeSolverDB
MatrixFreeSolverDB
MultigridDB
NonlinearSolverDB

SimulationDB
SimulationStateDB
SimulationStepDB
SimulationCheckpointDB
SimulationRestartDB
SimulationExecutionDB
SimulationCpuDB
SimulationSimdDB
SimulationParallelDB
SimulationGpuDB
SimulationCostModelDB

ScientificProofDB
SolverProofDB
ConvergenceProofDB
DiscretizationProofDB
StencilProofDB
MeshProofDB
OperatorProofDB
SimulationProofDB
```

---

# 51. MIR additions

```text
SOLVER_BEGIN
SOLVER_END
SOLVER_APPLY

ODE_INIT
ODE_EVALUATE
ODE_STEP
ODE_ERROR_ESTIMATE
ODE_ACCEPT_STEP
ODE_REJECT_STEP
ODE_EVENT_CHECK

PDE_BEGIN
PDE_END
PDE_OPERATOR

STENCIL_APPLY
STENCIL_FUSE

MESH_LOAD
MESH_CONNECTIVITY
MESH_PARTITION

FEM_ELEMENT
FEM_QUADRATURE
FEM_ASSEMBLE

LINEAR_OPERATOR_APPLY
PRECONDITIONER_APPLY

ITERATIVE_INIT
ITERATIVE_STEP
ITERATIVE_RESIDUAL
ITERATIVE_CHECK
ITERATIVE_CONVERGED

MULTIGRID_RESTRICT
MULTIGRID_SMOOTH
MULTIGRID_COARSE
MULTIGRID_PROLONG

SIMULATION_STEP
SIMULATION_CHECKPOINT
SIMULATION_RESTART
```

Các MIR operation này **không nhất thiết tồn tại tới Machine IR**.

Chúng là semantic anchors để compiler thực hiện optimization.

---

# 52. Proof system

Các proof quan trọng:

```text
ODEDimensionProof
ODEJacobianProof
ODEStepProof
ODEEventProof

PDEDiscretizationProof
PDEBoundaryProof
StencilBoundsProof
StencilDependencyProof
StencilFusionProof

MeshTopologyProof
MeshGeometryProof
MeshConnectivityProof

FEMAssemblyProof
FEMPartitionProof

LinearOperatorProof
SolverShapeProof
SolverAliasProof
SolverConvergenceProof
SolverNumericalProof
SolverDeterminismProof

PreconditionerProof
MatrixFreeProof
MultigridProof

SimulationStorageProof
SimulationTransferProof
SimulationCheckpointProof
SimulationGpuProof
SimulationADProof
```

---

# 53. Invariants

### `ASOLVER-01`
Solver layer không phải Core language primitive.

### `ASOLVER-02`
Problem semantics phải tách khỏi solver implementation.

### `ASOLVER-03`
Discretization phải explicit.

### `ASOLVER-04`
Solver không được thay đổi mathematical problem semantics.

### `ASOLVER-05`
Numerical tolerance phải là observable solver contract.

### `ASOLVER-06`
Adaptive timestep phải preserve declared accuracy semantics.

### `ASOLVER-07`
ODE state phải tuân generic ownership/type semantics.

### `ASOLVER-08`
ODE RHS phải có shape/type compatibility.

### `ASOLVER-09`
Jacobian source phải explicit hoặc compiler-verifiable.

### `ASOLVER-10`
AD-generated Jacobian/JVP phải qua verification bình thường.

### `ASOLVER-11`
PDE boundary conditions phải có semantic identity rõ ràng.

### `ASOLVER-12`
Discretization không được tự ý thay đổi boundary semantics.

### `ASOLVER-13`
Stencil access phải được bounds-verify hoặc proven safe.

### `ASOLVER-14`
Stencil fusion phải preserve dependency semantics.

### `ASOLVER-15`
FEM assembly phải preserve global contribution semantics.

### `ASOLVER-16`
Parallel assembly phải chứng minh race safety hoặc dùng synchronization.

### `ASOLVER-17`
Mesh topology mutation phải invalidate capability bị ảnh hưởng.

### `ASOLVER-18`
Mesh logical identity không được phụ thuộc physical address.

### `ASOLVER-19`
LinearOperator không cần materialize matrix.

### `ASOLVER-20`
Matrix-free solver phải preserve operator semantics.

### `ASOLVER-21`
Preconditioner phải preserve solver contract.

### `ASOLVER-22`
Solver convergence status phải được biểu diễn explicit.

### `ASOLVER-23`
Numerical breakdown không được biến thành silent success.

### `ASOLVER-24`
Deterministic solver phải kiểm soát reduction/scheduling semantics cần thiết.

### `ASOLVER-25`
Fast/Approximate numerical modes phải explicit.

### `ASOLVER-26`
GPU solver không được implicit transfer ngoài declared execution/storage contract.

### `ASOLVER-27`
Simulation state lifetime phải tuân ownership/storage semantics.

### `ASOLVER-28`
Checkpoint/restart operations phải preserve observable I/O ordering.

### `ASOLVER-29`
Solver optimization có thể thay implementation nhưng phải preserve declared numerical semantics.

### `ASOLVER-30`
Solver library không được tạo mandatory runtime/compiler dependency cho chương trình không sử dụng scientific computing.

---

## Kiến trúc sau 377

Axiom lúc này đã hình thành một stack scientific computing tương đối hoàn chỉnh:

```text
                    APPLICATION
                         │
          ┌──────────────┼──────────────┐
          │              │              │
       Machine         AI/ML         Scientific
       Software       Computing       Computing
          │              │              │
          │        ┌─────┴─────┐       │
          │        │           │       │
          │       Tensor      Graph    │
          │        │           │       │
          │        └─────┬─────┘       │
          │              │             │
          └──────────────┼─────────────┘
                         │
                 Numeric / AD
                         │
              Expression / Sparse
                         │
              Linear Algebra
                         │
             Solver / Simulation
                         │
          ┌──────────────┼──────────────┐
          │              │              │
         SIMD         Parallel         GPU
          │              │              │
          └──────────────┼──────────────┘
                         │
                    Native Code
```

Điểm đáng chú ý là **Solver 377 không tạo thêm một “framework” tách biệt**. Nó tái sử dụng gần như toàn bộ nền tảng Axiom đã xây: `Tensor`, `Sparse`, `Graph`, `AD`, `Expression`, `Parallel`, `SIMD`, `GPU`, `Ownership`, `NumericalContract`. Đây chính là hướng giúp Axiom mạnh mà không biến compiler thành một đống subsystem rời rạc.