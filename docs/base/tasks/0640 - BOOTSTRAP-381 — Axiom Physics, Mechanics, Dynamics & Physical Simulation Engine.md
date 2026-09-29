# BOOTSTRAP-381 — Axiom Physics, Mechanics, Dynamics & Physical Simulation Engine

Sau **380 — Geometry & Spatial Computing**, tầng tiếp theo tự nhiên là **Physics/Mechanics**.

Mục tiêu của task này không phải biến Axiom thành một physics engine cụ thể, mà thiết kế **semantic foundation** để các physics engine, robotics simulator, game engine, CAD/CAE và scientific simulation có thể xây dựng trực tiếp trên Axiom.

Nguyên tắc:

> **Physics là một domain library/semantic layer trên Geometry + Units + Tensor + Solver + AD + Parallel/GPU, không phải tính năng bắt buộc của Core language.**

---

# 1. Tách Physical Model khỏi Numerical Representation

Axiom phải phân biệt:

```text
PhysicalModel
PhysicalState
PhysicalParameter
PhysicalConstraint
NumericalState
Solver
ExecutionStrategy
```

Ví dụ một con lắc:

```text
PhysicalModel:
    mass
    length
    gravity
    constraints

NumericalState:
    position
    velocity

Solver:
    ODE integrator
```

Không để physics model bị khóa vào một representation cụ thể.

---

# 2. Physical Quantity tiếp tục dùng Units

Ví dụ:

```text
mass     : kg
position : m
velocity : m/s
force    : N
time     : s
```

Compiler/constraint engine có thể kiểm tra:

```text
F = m * a
```

vì:

```text
kg * m/s² = N
```

Sai dimension phải bị bắt ở compile-time khi có đủ static information.

---

# 3. Physical Frame

Physics phải kế thừa Frame system của 380:

```text
World
Body
Local
Contact
Joint
Sensor
```

Ví dụ:

```text
Point<World>
Vector<World>
Velocity<Body>
Force<World>
```

Không cho phép vô tình cộng các đại lượng thuộc frame incompatible.

---

# 4. State không nhất thiết là struct khổng lồ

Một physical state có thể gồm:

```text
Position
Orientation
LinearVelocity
AngularVelocity
Mass
Inertia
```

nhưng compiler/library được phép layout thành:

```text
AoS
SoA
AoSoA
```

tùy workload.

---

# 5. Rigid Body

Semantic abstraction:

```text
RigidBody<T, Frame>
```

với:

```text
mass
center_of_mass
inertia
pose
linear_velocity
angular_velocity
```

Nhưng đây là **struct semantic**, không phải class object bắt buộc.

---

# 6. Orientation

Không nên chỉ dùng Euler angles.

Physics layer nên hỗ trợ:

```text
Quaternion
RotationMatrix
AxisAngle
ExponentialMap
```

và abstraction:

```text
Rotation<From, To>
```

Compiler có thể chọn representation.

---

# 7. Quaternion

Quaternion phải có semantic distinction:

```text
Quaternion<T>
```

và operations:

```text
normalize
inverse
compose
rotate
slerp
```

Không coi quaternion như arbitrary `vec<f32,4>` trong semantic layer dù representation cuối có thể giống hệt.

---

# 8. Pose

Chuẩn hóa:

```text
Pose<From, To>
```

bao gồm:

```text
translation
rotation
```

và có thể compose:

```text
Pose<A,B> × Pose<B,C>
    -> Pose<A,C>
```

Constraint engine có thể kiểm tra frame compatibility.

---

# 9. Velocity

Phải phân biệt:

```text
LinearVelocity
AngularVelocity
```

vì dimension và transformation semantics khác nhau.

---

# 10. Acceleration

Tương tự:

```text
LinearAcceleration
AngularAcceleration
```

Compiler không nên coi tất cả chỉ là `Vector`.

---

# 11. Force và Torque

Physics semantic types:

```text
Force
Torque
Impulse
AngularImpulse
```

Units khác nhau và phép biến đổi khác nhau.

Ví dụ:

```text
Torque = r × Force
```

Constraint engine kiểm tra dimension.

---

# 12. Momentum

Hỗ trợ:

```text
LinearMomentum
AngularMomentum
```

và conservation laws.

---

# 13. Energy

Phân biệt:

```text
KineticEnergy
PotentialEnergy
MechanicalEnergy
```

với:

```text
Energy
```

theo semantic domain.

Không cần runtime wrapper nếu compile-time type đủ.

---

# 14. Material properties

Physics material:

```text
Density
Friction
Restitution
Elasticity
Damping
```

phải có unit/type semantics phù hợp.

---

# 15. Constraint

Physics constraints khác Constraint Engine 379.

Ví dụ:

```text
DistanceConstraint
HingeConstraint
FixedConstraint
BallConstraint
SliderConstraint
ContactConstraint
```

Đây là **physical constraint**.

Nhưng compiler có thể dùng Constraint Engine để kiểm tra metadata/type/shape.

---

# 16. Holonomic / Non-Holonomic

Constraint system nên phân biệt:

```text
Holonomic
NonHolonomic
Unilateral
Bilateral
```

để solver biết loại phương trình cần giải.

---

# 17. Constraint Jacobian

Physics constraint thường tạo:

```text
J(q) · v
```

hoặc:

```text
J(q) · q_dot
```

Có thể dùng AD Engine 371 để sinh Jacobian.

Không cần programmer viết Jacobian thủ công nếu function differentiable.

---

# 18. Automatic Differentiation

Ví dụ:

```text
constraint(q)
```

compiler có thể sinh:

```text
Jacobian(constraint, q)
```

và tối ưu:

```text
JVP
VJP
Sparse Jacobian
```

dựa trên sparsity analysis.

---

# 19. Dynamics

Physics layer hỗ trợ:

```text
Kinematics
Dynamics
Statics
```

Tách rõ:

```text
Kinematics:
    position
    velocity
    acceleration

Dynamics:
    force
    momentum
    energy
```

---

# 20. Newtonian dynamics

Semantic equation:

```text
F = m a
```

không nhất thiết phải trở thành runtime symbolic expression.

Compiler có thể lower thành numeric kernel.

---

# 21. Lagrangian mechanics

Có thể biểu diễn:

```text
L(q, q_dot, t)
```

và Euler-Lagrange:

```text
d/dt(∂L/∂q_dot) - ∂L/∂q = 0
```

AD + Solver infrastructure có thể tự sinh equations.

---

# 22. Hamiltonian mechanics

Tương tự:

```text
H(q,p,t)
```

và:

```text
q_dot = ∂H/∂p
p_dot = -∂H/∂q
```

Đây nên là library semantic abstraction, không phải Core keyword.

---

# 23. Differential equations

Physics layer tích hợp trực tiếp với:

```text
ODE
DAE
PDE
```

từ task 377.

Ví dụ:

```text
RigidBody
    ↓
ODEProblem
    ↓
Solver
```

---

# 24. Integrator abstraction

Chuẩn hóa:

```text
Integrator
```

với các loại:

```text
Euler
Midpoint
RK4
RK45
Verlet
Leapfrog
Newmark
BDF
ImplicitEuler
```

Solver selection dựa trên declared numerical contract.

---

# 25. Symplectic integration

Physics cần semantic category:

```text
Symplectic
EnergyAware
StructurePreserving
```

để optimizer không tùy tiện biến đổi numerical algorithm theo cách phá structure.

---

# 26. Energy preservation

Không phải solver nào cũng bảo toàn energy.

Physics contract có thể yêu cầu:

```text
EnergyPolicy:
    None
    Monitor
    PreserveApprox
    PreserveStructure
```

Compiler không tự hứa numerical conservation nếu algorithm không có guarantee.

---

# 27. Determinism

Physics simulation cần:

```text
Deterministic
Reproducible
Fast
```

contracts.

Ví dụ parallel reduction có thể thay đổi floating-point result.

Nếu simulation yêu cầu deterministic:

```text
reduction order
thread scheduling
solver order
```

phải được kiểm soát.

---

# 28. Collision system

Dựa trên Geometry 380:

```text
BroadPhase
NarrowPhase
ContactGeneration
ContactManifold
```

---

# 29. Contact manifold

Một collision không chỉ là boolean.

Semantic result:

```text
Contact {
    point
    normal
    penetration
    relative_velocity
}
```

Có thể có nhiều contact points.

---

# 30. Continuous Collision Detection

CCD cần:

```text
Sweep
TimeOfImpact
ConservativeAdvancement
```

và phải tránh tunnel effect.

---

# 31. Collision filtering

Physics world cần semantic categories:

```text
CollisionLayer
CollisionMask
CollisionGroup
```

Compiler không cần hiểu mọi game-specific layer, nhưng representation phải zero-cost.

---

# 32. Broad-phase structures

Có thể dùng:

```text
BVH
AABB Tree
SweepAndPrune
SpatialHash
UniformGrid
```

Compiler/runtime chọn theo workload.

---

# 33. Solver pipeline

Physics constraint solver có thể:

```text
Detect contacts
      ↓
Generate constraints
      ↓
Build Jacobian
      ↓
Build system
      ↓
Solve
      ↓
Apply impulses
      ↓
Integrate
```

Các bước có thể fusion.

---

# 34. Linear solver integration

Constraint systems thường tạo:

```text
Ax = b
```

hoặc sparse systems.

Có thể dùng:

```text
Sparse
LinearAlgebra
Solver
```

đã thiết kế trước.

---

# 35. Iterative physics solvers

Các engine thực tế thường cần iterative methods:

```text
PGS
CG
GMRES
MINRES
Newton
```

Axiom không bắt buộc một solver cụ thể.

---

# 36. Sparse Jacobian

Physics constraint graph thường sparse.

Compiler có thể phân tích:

```text
body A interacts with B
body B interacts with C
```

để xây sparse system.

---

# 37. Constraint graph

Đây là một graph semantic:

```text
Body
  ↕
Constraint
  ↕
Body
```

Graph engine 375 có thể được reuse.

---

# 38. Island detection

Physics engine có thể chia:

```text
World
 ↓
Interaction Graph
 ↓
Connected Components
 ↓
Physics Islands
```

Mỗi island có thể solve độc lập.

Đây là ứng dụng trực tiếp của:

```text
Graph
+
Parallelism
```

---

# 39. Parallel physics

Các island độc lập:

```text
Island 1 → Worker 1
Island 2 → Worker 2
Island 3 → Worker 3
```

Compiler có thể dùng parallel execution.

---

# 40. SIMD physics

Batch:

```text
4 / 8 / 16 bodies
```

có thể vectorize:

```text
position
velocity
force
collision
```

Data layout:

```text
SoA / AoSoA
```

rất quan trọng.

---

# 41. GPU physics

GPU có thể xử lý:

```text
broad phase
particle simulation
SPH
cloth
soft body
constraint batches
```

nhưng không phải mọi physics algorithm đều phù hợp GPU.

Cost model quyết định.

---

# 42. Particle system

Particle là một abstraction đơn giản:

```text
Particle {
    position
    velocity
    mass
}
```

Nhưng storage nên được tối ưu thành SoA khi cần.

---

# 43. Particle interaction

Các mô hình:

```text
N-body
SPH
PIC
MPM
DEM
```

có thể xây trên:

```text
SpatialIndex
NeighborSearch
Parallel
GPU
```

---

# 44. Soft body

Có thể biểu diễn:

```text
MassSpring
FEM
PositionBasedDynamics
XPBD
```

Tất cả đều library-level.

---

# 45. Cloth

Cloth là một specialization của constrained deformable body.

Không cần class inheritance.

Có thể dùng:

```text
Mesh
+
Constraint
+
Solver
```

---

# 46. Fluid

Fluid simulation nên nằm trên:

```text
PDE
Mesh
Particle
Sparse
Solver
GPU
```

Ví dụ:

```text
Eulerian
Lagrangian
SPH
PIC
FLIP
```

Không đưa fluid primitive vào language Core.

---

# 47. Physical state ownership

Simulation state phải tuân thủ Axiom ownership.

Ví dụ:

```text
step(
    state: mut_view<SimulationState>
)
```

Compiler đảm bảo không có concurrent mutation trái phép.

---

# 48. Zero-copy solver

Solver có thể nhận:

```text
mut_view<T>
```

thay vì copy:

```text
State → SolverBuffer → State
```

nếu algorithm cho phép.

---

# 49. In-place vs out-of-place

API phải phân biệt:

```text
step_inplace(state)
step(state) -> new_state
```

Không được hidden allocation/copy.

Compiler có thể optimize out-of-place thành in-place nếu observable semantics tương đương.

---

# 50. Checkpoint/restart

Simulation có thể cần:

```text
checkpoint()
restart()
```

Nhưng checkpoint representation phải explicit.

Không được Drop tự động serialize physics state.

---

# 51. Units + Physics + Constraints

Ví dụ:

```text
fn acceleration(
    force: Force,
    mass: Mass
) -> Acceleration
```

Compiler biết:

```text
Force / Mass
=
kg·m/s² / kg
=
m/s²
```

và reject:

```text
Force / Length
```

nếu return type yêu cầu Acceleration.

---

# 52. Frame + Units cùng lúc

Một type có thể conceptually chứa:

```text
Vector<
    Quantity<f64, Length>,
    World
>
```

Tức là compiler kiểm tra cả:

```text
dimension
+
coordinate frame
```

nhưng representation cuối vẫn có thể chỉ là:

```text
3 × f64
```

---

# 53. Physical constants

Ví dụ:

```text
gravity
speed_of_light
gravitational_constant
Planck_constant
```

được biểu diễn với:

```text
Quantity
Dimension
Unit
Precision
```

Không có runtime metadata bắt buộc.

---

# 54. Physical laws

Axiom có thể hỗ trợ library-level abstraction:

```text
Law
ConservationLaw
ConstitutiveLaw
ConstraintLaw
```

Không phải class hierarchy.

Có thể là traits:

```text
trait ConservativeSystem
trait HamiltonianSystem
trait DissipativeSystem
```

---

# 55. Constitutive models

Engineering simulation:

```text
Stress
Strain
MaterialModel
```

Ví dụ:

```text
Elastic
Plastic
Viscoelastic
Hyperelastic
```

Compiler có thể specialize generic material models.

---

# 56. Material specialization

Ví dụ:

```text
simulate<Material = Steel>()
```

có thể monomorphize:

```text
material properties
constitutive equation
derivative
```

và eliminate dynamic dispatch.

---

# 57. Runtime polymorphism

Nếu thật sự cần:

```text
dyn MaterialModel
```

được phép.

Nhưng physics Core abstraction không yêu cầu vtable.

---

# 58. Physics + AD

Có thể tự động sinh:

```text
∂state_next / ∂state
∂loss / ∂parameters
∂force / ∂position
```

phục vụ:

- optimization;
- system identification;
- control;
- differentiable simulation;
- robotics.

---

# 59. Differentiable physics

Pipeline:

```text
Physical Model
      ↓
Numerical Solver
      ↓
AD transformation
      ↓
Gradient
```

Compiler phải giữ distinction giữa:

```text
exact derivative
subgradient
adjoint
finite difference
```

---

# 60. Physics proof system

Physics-specific proofs:

```text
PhysicalDimensionProof
FrameConsistencyProof
KinematicProof
ConstraintCompatibilityProof
JacobianProof
CollisionProof
ContactProof
SolverShapeProof
EnergyContractProof
DeterminismProof
ConservationProof
StabilityProof
SymplecticProof
SparseStructureProof
PhysicsAliasProof
PhysicsStorageProof
PhysicsGpuProof
PhysicsParallelProof
PhysicsADProof
```

---

# 61. CompilerDB

Task 381 bổ sung:

```text
PhysicsDB
PhysicalModelDB
PhysicalStateDB
PhysicalParameterDB
PhysicalLawDB
PhysicalConstraintDB
PhysicalFrameDB

RigidBodyDB
RigidBodyMassDB
RigidBodyInertiaDB
RigidBodyPoseDB
RigidBodyVelocityDB
RigidBodyForceDB
RigidBodyTorqueDB

RotationDB
QuaternionDB
PoseDB
TwistDB
WrenchDB
MomentumDB
EnergyDB

DynamicsDB
KinematicsDB
StaticsDB
LagrangianDB
HamiltonianDB
DynamicsEquationDB

PhysicsIntegratorDB
PhysicsSolverDB
PhysicsConstraintSolverDB
PhysicsJacobianDB
PhysicsContactDB
PhysicsManifoldDB
PhysicsCcdDB

PhysicsCollisionDB
PhysicsBroadPhaseDB
PhysicsNarrowPhaseDB
PhysicsFilterDB

PhysicsIslandDB
PhysicsInteractionGraphDB
PhysicsPartitionDB

PhysicsParticleDB
PhysicsSoftBodyDB
PhysicsClothDB
PhysicsFluidDB
PhysicsMaterialDB
PhysicsConstitutiveDB

PhysicsParallelDB
PhysicsSimdDB
PhysicsGpuDB
PhysicsAdDB
PhysicsCostModelDB
PhysicsNumericalDB
PhysicsDeterminismDB
PhysicsProofDB
PhysicsVerificationDB
```

---

# 62. MIR additions

Chỉ đưa những semantic operations có lợi cho compiler:

```text
PHYSICS_STATE_CREATE
PHYSICS_STATE_UPDATE

PHYSICS_TRANSFORM
PHYSICS_ROTATE
PHYSICS_COMPOSE_POSE

PHYSICS_FORCE
PHYSICS_TORQUE
PHYSICS_IMPULSE

PHYSICS_INTEGRATE
PHYSICS_CONSTRAINT

PHYSICS_CONTACT
PHYSICS_COLLISION
PHYSICS_CCD

PHYSICS_JACOBIAN
PHYSICS_SOLVE

PHYSICS_ISLAND_BEGIN
PHYSICS_ISLAND_END

PHYSICS_PARTICLE_STEP
PHYSICS_NEIGHBOR_SEARCH

PHYSICS_CHECKPOINT
PHYSICS_RESTART
```

---

# 63. Physics invariants

### `APHYS-01`
Physical quantities phải giữ đúng dimension semantics.

### `APHYS-02`
Coordinate frame mismatch phải bị phát hiện khi statically provable.

### `APHYS-03`
Physical frame metadata không tạo runtime overhead nếu đã được erase.

### `APHYS-04`
Point, Vector, Velocity, Force, Torque và các physical categories phải giữ semantic distinction.

### `APHYS-05`
Physical transformation phải preserve frame correctness.

### `APHYS-06`
Rotation representation phải preserve rotation semantics independent of physical representation.

### `APHYS-07`
Quaternion operations phải giữ normalization/rotation contract khi contract yêu cầu.

### `APHYS-08`
Physical constraints phải có semantics rõ ràng về equality/inequality/unilateral/bilateral.

### `APHYS-09`
Constraint Jacobian phải tương thích với physical constraint.

### `APHYS-10`
AD-generated Jacobian phải tuân thủ differentiation semantics.

### `APHYS-11`
Solver không được thay đổi physical model semantics ngoài numerical contract đã khai báo.

### `APHYS-12`
Structure-preserving solver không được bị optimizer biến đổi thành algorithm phá structure khi contract cấm.

### `APHYS-13`
Energy/conservation guarantees chỉ được công bố khi solver có corresponding proof/contract.

### `APHYS-14`
Deterministic simulation phải kiểm soát các nguồn nondeterministic observable.

### `APHYS-15`
Parallel physics phải tuân thủ ownership, alias và data-race rules.

### `APHYS-16`
Independent physics islands có thể chạy song song nếu proof chứng minh independence.

### `APHYS-17`
Collision broad phase không được tạo false-negative trong contract yêu cầu completeness.

### `APHYS-18`
Narrow phase phải preserve collision semantics.

### `APHYS-19`
CCD phải preserve declared time-of-impact contract.

### `APHYS-20`
Physics state views không được outlive storage.

### `APHYS-21`
In-place mutation phải có exclusive mutation capability.

### `APHYS-22`
Out-of-place operations không được mặc định imply heap allocation.

### `APHYS-23`
Compiler được phép eliminate physical temporaries nếu observable semantics giữ nguyên.

### `APHYS-24`
Physics storage có thể là Host/Device/External nhưng domain crossing phải explicit.

### `APHYS-25`
GPU physics phải obey GPU execution and synchronization rules.

### `APHYS-26`
SIMD physics phải preserve numerical contract.

### `APHYS-27`
Material specialization phải có thể compile-time specialize khi static type known.

### `APHYS-28`
Dynamic physics polymorphism chỉ xuất hiện khi programmer/API yêu cầu.

### `APHYS-29`
Physics proof phải được tích hợp với Constraint/Proof Engine.

### `APHYS-30`
Physics abstractions không được tạo mandatory runtime dependency cho chương trình không sử dụng physics.

---

## Vị trí của task 381

Axiom hiện có một chuỗi khá đẹp:

```text
Numeric
   ↓
Tensor
   ↓
Linear Algebra
   ↓
AD / Symbolic
   ↓
Sparse / Graph
   ↓
ODE / PDE / Solver
   ↓
Units / Dimensions
   ↓
Geometry
   ↓
Physics
```

và phía dưới tất cả:

```text
Ownership
Memory
SIMD
Parallelism
GPU
Constraint / Proof
Compiler Optimization
```

Điểm quan trọng nhất của **381** là Physics **không trở thành một hệ thống riêng biệt**. Một phương trình vật lý có thể đi xuyên toàn bộ stack:

```text
Physical equation
      ↓
Units / Dimensions
      ↓
Constraint Solver
      ↓
Symbolic / AD
      ↓
Tensor / Sparse / Linear Algebra
      ↓
ODE / PDE Solver
      ↓
SIMD / Parallel / GPU
      ↓
Native machine code
```

Như vậy Axiom có thể hỗ trợ từ **game physics** đến **robotics, CAD/CAE và scientific simulation**, trong khi Core language vẫn không cần chứa một từ khóa `physics` nào.