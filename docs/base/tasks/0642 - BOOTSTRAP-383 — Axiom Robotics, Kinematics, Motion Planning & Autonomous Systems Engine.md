# BOOTSTRAP-383 — Axiom Robotics, Kinematics, Motion Planning & Autonomous Systems Engine

Sau **382 — Signal Processing & Control**, tầng tiếp theo là **Robotics**.

Đây là nơi các hệ thống trước bắt đầu hội tụ:

```text
Geometry
   +
Units
   +
Physics
   +
Linear Algebra
   +
Graph
   +
Optimization
   +
Signal Processing
   +
Control
   +
AD
   +
Parallel/GPU
```

Mục tiêu của 383 là tạo nền tảng để Axiom có thể xây:

- robot arm;
- mobile robot;
- drone;
- autonomous vehicle;
- humanoid;
- industrial robot;
- motion planner;
- SLAM/navigation;
- differentiable robotics.

Nhưng **Robotics vẫn là domain library**, không phải Core language.

---

# 1. Robotics Model

Tách:

```text
RobotModel
RobotState
RobotConfiguration
RobotGeometry
RobotDynamics
RobotSensor
RobotActuator
RobotController
MotionPlanner
```

Không dùng class hierarchy bắt buộc.

Có thể dùng:

```text
struct
trait
generic
```

theo mô hình Axiom đã thống nhất.

---

# 2. Robot là hệ thống nhiều Frame

Ví dụ:

```text
World
 └── RobotBase
      └── Joint1
           └── Link1
                └── Joint2
                     └── Link2
                          └── EndEffector
```

Mỗi frame là một semantic identity.

---

# 3. Frame Graph

Robot model có:

```text
FrameGraph
```

và:

```text
JointGraph
```

Compiler/library có thể suy ra:

```text
Base → Link1 → Link2 → EndEffector
```

và tính transform composition.

---

# 4. Joint Types

Chuẩn hóa:

```text
Fixed
Revolute
Prismatic
Continuous
Spherical
Planar
Floating
```

Mỗi joint có:

```text
position
velocity
acceleration
limits
```

---

# 5. Degrees of Freedom

Robot configuration:

```text
q ∈ R^N
```

với `N` có thể là compile-time constant.

Ví dụ:

```text
Robot<DOF = 6>
```

Compiler có thể specialize:

```text
vec<f64,6>
```

thay vì dynamic array.

---

# 6. Static DOF

Nếu:

```text
DOF = 6
```

compiler biết:

```text
q.shape == [6]
```

Do đó:

- bounds check có thể biến mất;
- matrix dimensions static;
- SIMD/vectorization tốt hơn;
- stack allocation dễ dàng;
- Jacobian size known.

---

# 7. Dynamic DOF

Robot runtime-loaded:

```text
Robot<Dynamic>
```

vẫn được hỗ trợ.

Khi đó:

```text
q
```

là dynamic vector.

Không bắt buộc mọi robot phải compile-time known.

---

# 8. Forward Kinematics

Semantic operation:

```text
forward_kinematics(robot, q)
```

trả về:

```text
Pose<Base, Link1>
Pose<Base, Link2>
...
Pose<Base, EndEffector>
```

Compiler có thể specialize toàn bộ chain.

---

# 9. FK Fusion

Không nên materialize toàn bộ intermediate transform nếu không cần.

Ví dụ:

```text
T01
T12
T23
T34
```

có thể compiler fuse thành:

```text
T04
```

khi chỉ cần end-effector pose.

---

# 10. Denavit-Hartenberg

Robotics library có thể hỗ trợ:

```text
DHParameter
```

nhưng không bắt buộc robot model dùng DH.

Có thể dùng:

```text
URDF-like
graph-based
custom kinematic chain
```

---

# 11. Jacobian

Robot Jacobian:

```text
J(q)
```

mapping:

```text
q_dot → end-effector velocity
```

có thể được sinh bằng:

```text
Analytical differentiation
AD
Geometric Jacobian
```

---

# 12. AD Jacobian

Nếu FK được viết bằng ordinary Axiom functions:

```text
fk(q)
```

thì:

```text
@differentiate
```

có thể sinh Jacobian.

Compiler không cần robot-specific differentiation engine.

---

# 13. Jacobian Sparsity

Robot chain có sparse dependency.

Ví dụ joint 1 ảnh hưởng mọi link phía sau, joint 6 không ảnh hưởng link trước nó.

Compiler có thể tận dụng dependency graph để tránh tính toán không cần thiết.

---

# 14. Inverse Kinematics

Semantic:

```text
inverse_kinematics(robot, target)
```

có thể dùng:

```text
Analytical
Jacobian
Damped Least Squares
Newton
SQP
Optimization
```

Algorithm selection thuộc library/solver/cost model.

---

# 15. IK không guarantee uniqueness

Một target có thể có:

```text
0 solutions
1 solution
multiple solutions
```

API phải biểu diễn rõ.

Không nên:

```text
-> q
```

nếu failure/multiple solutions là semantic possibilities.

Có thể:

```text
IKResult
```

với:

```text
NoSolution
OneSolution
MultipleSolutions
```

tùy API.

---

# 16. Joint Limits

Configuration constraints:

```text
q_min <= q <= q_max
```

được đưa vào Constraint/Solver infrastructure.

Nếu `q` static constant:

```text
compile-time validation
```

có thể thực hiện.

---

# 17. Velocity / Acceleration Limits

Tương tự:

```text
q_dot_min <= q_dot <= q_dot_max
q_ddot_min <= q_ddot <= q_ddot_max
```

Units được kiểm tra.

---

# 18. Motion Planning

Motion planning tách khỏi control.

```text
Planning
   ↓
Trajectory
   ↓
Controller
```

Planner không trực tiếp điều khiển motor.

---

# 19. Configuration Space

Robot configuration:

```text
q ∈ C
```

và obstacle constraints:

```text
C_free
```

Motion planner hoạt động trên configuration space.

---

# 20. Collision-aware Planning

Planner có thể sử dụng Geometry/Physics:

```text
collision(robot(q), environment)
```

để reject configuration.

---

# 21. Sampling-based Planning

Hỗ trợ:

```text
RRT
RRT*
PRM
FMT
```

và các biến thể.

Đây là library algorithm.

---

# 22. Graph-based Planning

Configuration samples tạo:

```text
Graph<Node, Edge>
```

Graph engine 375 có thể reuse.

Shortest-path algorithms:

```text
A*
Dijkstra
D* / incremental planning
```

có thể reuse graph infrastructure.

---

# 23. Cost Function

Motion planning có thể tối ưu:

```text
distance
time
energy
jerk
collision margin
smoothness
```

Cost function nên là generic function.

---

# 24. Trajectory

Trajectory:

```text
q(t)
```

với:

```text
position
velocity
acceleration
jerk
```

---

# 25. Polynomial Trajectory

Có thể hỗ trợ:

```text
Linear
Cubic
Quintic
Spline
B-spline
Bezier
```

Compiler có thể specialize degree.

---

# 26. Time Parameterization

Một geometric path:

```text
q(s)
```

có thể được time-parameterized:

```text
s(t)
```

tách:

```text
Path
TimeProfile
Trajectory
```

Đây là distinction quan trọng.

---

# 27. Minimum Jerk

Trajectory optimization có thể tối ưu:

```text
∫ jerk² dt
```

dùng Solver/Linear Algebra.

---

# 28. Minimum Snap

Drone/quadrotor cần:

```text
∫ snap² dt
```

có thể dùng cùng abstraction.

---

# 29. Differential Constraints

Ví dụ:

```text
|velocity| <= Vmax
|acceleration| <= Amax
```

và:

```text
dynamics(q,q_dot,q_ddot) = 0
```

được đưa vào solver.

---

# 30. Dynamics

Robot dynamics:

```text
M(q) q_ddot
+ C(q,q_dot)
+ G(q)
= τ
```

Có thể sinh:

```text
MassMatrix
Coriolis
Gravity
```

từ robot model.

---

# 31. Recursive Dynamics

Không cần materialize full matrices nếu không cần.

Có thể dùng algorithms:

```text
RNEA
CRBA
ABA
```

cho:

- inverse dynamics;
- mass matrix;
- forward dynamics.

---

# 32. Zero-Copy Dynamics

Robot state:

```text
q
q_dot
q_ddot
tau
```

có thể nằm trong caller-provided buffers.

Compiler không được mặc định allocate mỗi simulation step.

---

# 33. Robot Dynamics + Units

Ví dụ:

```text
q       : rad
q_dot   : rad/s
q_ddot  : rad/s²
tau     : N·m
```

Compiler có thể kiểm tra dimensional consistency.

---

# 34. Torque

Torque phải được phân biệt khỏi Force.

Geometry relation:

```text
τ = r × F
```

từ Geometry 380.

---

# 35. Robot Inertia

Inertia tensor:

```text
I
```

có physical units:

```text
kg·m²
```

và frame semantics.

---

# 36. Inertia Frame

Inertia phải gắn với frame:

```text
Inertia<BodyFrame>
```

chuyển frame cần đúng rotation law.

Không được treat arbitrary matrix như inertia.

---

# 37. Contact Dynamics

Robot/environment interaction:

```text
Contact
Friction
NormalForce
Impulse
```

reuse Physics 381.

---

# 38. Friction

Có thể hỗ trợ:

```text
Coulomb
Viscous
Stribeck
Custom
```

Material model là generic.

---

# 39. Sensor Model

Robotics sensor abstraction:

```text
Camera
Lidar
IMU
GPS
Encoder
ForceTorque
Radar
```

nhưng sensor interface chỉ cần:

```text
sample()
```

hoặc stream.

Signal 382 xử lý data.

---

# 40. Sensor Frame

Sensor output phải giữ frame:

```text
IMU<BodyFrame>
Camera<CameraFrame>
Lidar<LidarFrame>
```

để tránh lỗi coordinate conversion.

---

# 41. Sensor Noise

Sensor model có thể dùng Probability 376:

```text
Gaussian
Bias
Drift
Outlier
Quantization
```

và RNG explicit.

---

# 42. State Estimation

Robot state:

```text
Pose
Velocity
Bias
```

được estimate từ:

```text
IMU
GPS
Camera
Lidar
Encoder
```

dùng Kalman/particle/filter infrastructure.

---

# 43. Sensor Fusion

Pipeline:

```text
IMU
 ├──→ EKF
GPS ─┤
Lidar┘
```

Signal graph + Control/Estimator infrastructure có thể compose.

---

# 44. Odometry

Semantic abstraction:

```text
Odometry
```

có thể biểu diễn incremental transform:

```text
Pose(t)
→ Pose(t + dt)
```

---

# 45. Localization

Localization:

```text
LocalFrame
WorldFrame
MapFrame
```

phải sử dụng Frame system.

Ví dụ:

```text
Map → World → Robot → Sensor
```

---

# 46. SLAM

SLAM kết hợp:

```text
Geometry
Graph
Probability
Optimization
Sensor Processing
```

Có thể biểu diễn:

```text
PoseGraph
LandmarkGraph
FactorGraph
```

---

# 47. Factor Graph

Factor graph:

```text
Variable nodes
      ↕
Factor nodes
```

là một abstraction rất phù hợp với Graph engine.

Solver có thể tối ưu:

```text
Σ error_i(x_i)
```

---

# 48. Bundle Adjustment

Computer vision/robotics có thể dùng:

```text
BundleAdjustment
```

với:

```text
CameraPose
Landmark
Projection
ReprojectionError
```

và AD-generated Jacobian.

---

# 49. Visual Odometry

Pipeline:

```text
Image
 ↓
Feature
 ↓
Correspondence
 ↓
Geometry
 ↓
Pose Estimation
 ↓
State Estimator
```

Robotics layer chỉ compose các abstraction.

---

# 50. Navigation

Mobile robot navigation có thể dùng:

```text
Map
Localization
PathPlanner
TrajectoryPlanner
Controller
```

không cần một runtime object hierarchy.

---

# 51. Autonomous Agent

Có thể xây pipeline:

```text
Sensors
   ↓
Perception
   ↓
State Estimation
   ↓
World Model
   ↓
Planning
   ↓
Control
   ↓
Actuation
```

Axiom chỉ cung cấp efficient primitives và static semantics.

---

# 52. Real-Time Robotics

Robotics controller thường yêu cầu:

```text
@realtime
```

kế thừa task 382.

Compiler kiểm tra:

```text
NoBlocking
NoAllocation
BoundedExecution
```

khi profile yêu cầu.

---

# 53. Deterministic Control Loop

Một loop:

```text
read sensors
estimate
plan
control
write actuators
```

có thể yêu cầu:

```text
FixedPeriod
BoundedJitter
Deterministic
```

Runtime scheduler chịu trách nhiệm timing; compiler chỉ verify contract có thể kiểm chứng.

---

# 54. Hardware abstraction

Robot hardware:

```text
Motor
Encoder
CAN
EtherCAT
GPIO
SPI
I2C
```

thuộc System/FFI layer.

Robotics layer định nghĩa semantic interface.

---

# 55. Hardware-independent Robot Model

Cùng một:

```text
RobotModel
```

có thể chạy:

```text
Simulation
Hardware
GPU simulator
Test environment
```

vì hardware access nằm ngoài model.

---

# 56. Simulation/Hardware duality

Một controller:

```text
fn control(state) -> command
```

có thể chạy trên:

```text
simulated state
real sensor state
```

mà không cần thay đổi algorithm.

Đây rất quan trọng cho sim-to-real.

---

# 57. GPU Robotics

GPU có thể xử lý:

```text
IK batches
trajectory optimization
collision checks
particle environments
RL environments
```

đặc biệt khi có hàng nghìn robot instances.

---

# 58. Batch Robotics

Compiler có thể biến:

```text
Robot
```

thành batch:

```text
Robot[N]
```

và vectorize:

```text
FK
IK
Dynamics
Collision
```

cho reinforcement learning/simulation.

---

# 59. Parallel Environments

Ví dụ:

```text
10000 simulated robots
```

có thể chạy:

```text
parallel_for
+
SIMD
+
GPU
```

nếu ownership/alias/dependence proofs cho phép.

---

# 60. CompilerDB

Task 383 bổ sung:

```text id="n6zq1m"
RoboticsDB
RobotModelDB
RobotStateDB
RobotConfigurationDB
RobotDofDB
RobotFrameDB
RobotJointDB
RobotLinkDB

JointDB
FixedJointDB
RevoluteJointDB
PrismaticJointDB
SphericalJointDB
PlanarJointDB
FloatingJointDB
JointLimitDB

KinematicsDB
ForwardKinematicsDB
InverseKinematicsDB
KinematicChainDB
JacobianDB
JacobianSparsityDB

DynamicsDB
RobotDynamicsDB
MassMatrixDB
CoriolisDB
GravityDB
InverseDynamicsDB
ForwardDynamicsDB

RneaDB
CrbaDB
AbaDB

TrajectoryDB
PathDB
TimeParameterizationDB
PolynomialTrajectoryDB
SplineDB
JerkOptimizationDB
SnapOptimizationDB

MotionPlanningDB
ConfigurationSpaceDB
CollisionPlanningDB
RrtDB
RrtStarDB
PrmDB
GraphPlannerDB
TrajectoryPlannerDB

SensorDB
ImuDB
CameraSensorDB
LidarDB
GpsDB
EncoderDB
ForceTorqueSensorDB
SensorNoiseDB
SensorFrameDB

LocalizationDB
OdometryDB
StateEstimationDB
SensorFusionDB
PoseGraphDB
FactorGraphDB
SlamDB
BundleAdjustmentDB

NavigationDB
PathFollowingDB
ObstacleAvoidanceDB

RobotControlDB
RobotControllerDB
RealtimeControlDB
ActuatorDB
MotorDB

RobotSimulationDB
RobotBatchDB
RobotParallelDB
RobotSimdDB
RobotGpuDB
RobotAdDB

RobotHardwareDB
RobotProtocolDB
RobotInteropDB

RoboticsCostModelDB
RoboticsNumericalDB
RoboticsDeterminismDB
RoboticsProofDB
RoboticsVerificationDB
```

---

# 61. MIR additions

```text id="3ukn4d"
ROBOT_STATE_CREATE
ROBOT_CONFIG_CREATE

ROBOT_FORWARD_KINEMATICS
ROBOT_INVERSE_KINEMATICS
ROBOT_JACOBIAN

ROBOT_MASS_MATRIX
ROBOT_INVERSE_DYNAMICS
ROBOT_FORWARD_DYNAMICS

ROBOT_GRAVITY
ROBOT_CORIOLIS

ROBOT_COLLISION_CHECK
ROBOT_CONTACT_CHECK

ROBOT_PATH_PLAN
ROBOT_TRAJECTORY_PLAN
ROBOT_TIME_PARAMETERIZE

ROBOT_SENSOR_READ
ROBOT_SENSOR_SAMPLE

ROBOT_STATE_ESTIMATE
ROBOT_ODOMETRY

ROBOT_POSE_GRAPH
ROBOT_FACTOR_GRAPH
ROBOT_OPTIMIZE

ROBOT_CONTROL_STEP
ROBOT_ACTUATE

ROBOT_BATCH_BEGIN
ROBOT_BATCH_END
ROBOT_PARALLEL_STEP
```

---

# 62. Robotics Proofs

```text id="8j3x0c"
RobotFrameProof
RobotDofProof
JointCompatibilityProof
KinematicChainProof

ForwardKinematicsProof
InverseKinematicsProof
JacobianProof
JacobianSparsityProof

DynamicsDimensionProof
MassMatrixProof
InertiaFrameProof
DynamicsConstraintProof

JointLimitProof
VelocityLimitProof
AccelerationLimitProof

TrajectoryContinuityProof
TrajectoryDerivativeProof
TrajectoryConstraintProof

CollisionPlanningProof
ConfigurationSpaceProof
PathValidityProof

SensorFrameProof
SensorDimensionProof
SensorTimestampProof
SensorNoiseProof

LocalizationFrameProof
PoseGraphProof
FactorGraphProof

RealtimeRobotProof
RobotLatencyProof
RobotBoundedExecutionProof

RobotAliasProof
RobotStorageProof
RobotParallelProof
RobotSimdProof
RobotGpuProof
RobotAdProof
RobotDeterminismProof
```

---

# 63. Robotics invariants

### `AROBOT-01`
Robot configuration phải có DOF semantics rõ ràng.

### `AROBOT-02`
Static DOF phải được tận dụng để kiểm tra shape compile-time khi có thể.

### `AROBOT-03`
Dynamic DOF phải được hỗ trợ mà không phá static model.

### `AROBOT-04`
Joint type phải xác định đúng degrees of freedom.

### `AROBOT-05`
Joint limits phải có dimensional semantics hợp lệ.

### `AROBOT-06`
Frame mismatch trong robot kinematics phải được phát hiện khi statically provable.

### `AROBOT-07`
Forward kinematics phải preserve frame semantics.

### `AROBOT-08`
Transform composition phải có thể được compiler fuse khi semantics cho phép.

### `AROBOT-09`
Jacobian phải có shape đúng với DOF và output space.

### `AROBOT-10`
AD-generated Jacobian phải preserve robot kinematic semantics.

### `AROBOT-11`
Robot dynamics phải giữ dimensional consistency.

### `AROBOT-12`
Inertia tensor phải có đúng frame và physical dimension.

### `AROBOT-13`
Mass matrix phải có shape tương ứng với DOF.

### `AROBOT-14`
Dynamics algorithms không được tạo hidden allocations trong realtime profile.

### `AROBOT-15`
Motion planner phải phân biệt path và trajectory.

### `AROBOT-16`
Trajectory phải preserve declared continuity requirements.

### `AROBOT-17`
Planner không được coi collision result approximate là exact nếu contract yêu cầu exact.

### `AROBOT-18`
Collision-aware planning phải không bỏ sót collision khi completeness contract yêu cầu.

### `AROBOT-19`
Graph-based planners phải tuân thủ Graph semantics.

### `AROBOT-20`
Sensor data phải preserve timestamp semantics.

### `AROBOT-21`
Sensor data phải preserve coordinate-frame semantics.

### `AROBOT-22`
Sensor noise/randomness phải dùng explicit RNG semantics khi stochastic.

### `AROBOT-23`
Localization transformations phải preserve frame graph consistency.

### `AROBOT-24`
Pose graph/factor graph optimization phải preserve variable/factor ownership.

### `AROBOT-25`
Parallel robot instances phải chứng minh independence hoặc synchronization.

### `AROBOT-26`
Batch robot computation phải có thể lower xuống SIMD/GPU khi legal.

### `AROBOT-27`
Realtime robot code không được implicit blocking hoặc unbounded allocation khi profile cấm.

### `AROBOT-28`
Simulation và hardware execution phải có thể dùng cùng semantic controller interface.

### `AROBOT-29`
Robot abstractions phải compile away khi static specialization cho phép.

### `AROBOT-30`
Robotics layer không được tạo mandatory runtime dependency cho chương trình không sử dụng robotics.

---

# 64. Kiến trúc sau 383

Đến đây Axiom bắt đầu có một stack khá mạnh cho **autonomous systems**:

```text
                    Robotics
                       │
        ┌──────────────┼──────────────┐
        │              │              │
     Planning       Control       Estimation
        │              │              │
      Graph         Signal         Probability
        │              │              │
    Geometry       Physics         AD
        │              │              │
        └──────────────┼──────────────┘
                       │
              Tensor / Linear Algebra
                       │
              Numeric / Units
                       │
             Constraint / Proof
                       │
          SIMD / Parallel / GPU
                       │
               Axiom Native Code
```

Điểm quan trọng là **383 không tạo một “Robotics Runtime” nặng**.

Một hàm FK tĩnh có thể cuối cùng chỉ còn:

```text
load q
multiply/add/fma
store result
```

Một batch IK có thể thành:

```text
SIMD + parallel + GPU
```

Một hệ thống robot realtime có thể thành:

```text
fixed-size state
stack/caller storage
no GC
no hidden allocation
bounded control loop
```

Trong khi cùng code đó, nếu cần simulation quy mô lớn, compiler có thể chọn:

```text
Tensor
+
Sparse
+
Parallel
+
GPU
```

Đây chính là kiểu **“high-level source, low-level execution”** mà Axiom đang hướng tới.