Tiếp tục với **BOOTSTRAP-656** — tầng biến World Model thành hệ thống **perception → state → prediction → planning → control → action → feedback** cho robot, thiết bị tự hành và embodied AI.

:::writing{variant="document" id="58321" title="BOOTSTRAP-656 — Native AI Embodied Intelligence, Perception–Action Loop, Sensor Fusion, Motor Control, Robotics, Autonomous Systems & Real-Time Agent Runtime 5.0"}

# BOOTSTRAP-656
## Native AI Embodied Intelligence, Perception–Action Loop, Sensor Fusion, Motor Control, Robotics, Autonomous Systems & Real-Time Agent Runtime 5.0

**Status:** COMPLETE  
**Layer:** Native AI Embodied Intelligence / Autonomous Systems  
**Depends on:** BOOTSTRAP-600 → BOOTSTRAP-655  
**Primary dependencies:** 603, 605, 606, 607, 608, 614, 615, 616, 618, 619, 620, 627, 629, 639, 640, 643, 644, 648, 649, 650, 652, 653, 654, 655.

---

# 1. Mục tiêu

BOOTSTRAP-656 bổ sung cho Axiom một runtime thống nhất để xây dựng:

- robot;
- autonomous vehicle;
- drone;
- robotic arm;
- humanoid;
- industrial automation;
- embodied AI;
- game agents có physical environment;
- autonomous software/hardware agents;
- sensor-driven controllers;
- real-time perception-action systems.

Core loop:

```text
Observation
    ↓
Perception
    ↓
Sensor Fusion
    ↓
State Estimation
    ↓
World Model
    ↓
Prediction
    ↓
Planning
    ↓
Control
    ↓
Actuation
    ↓
Feedback
    └───────────────┘
```

656 **không thay thế** 655.

655 trả lời:

> Thế giới đang ở trạng thái nào và sẽ thay đổi thế nào?

656 trả lời:

> Hệ thống vật lý phải nhận biết, quyết định và tác động vào thế giới như thế nào trong thời gian thực?

---

# 2. Architectural Position

```text
                 ┌───────────────┐
                 │   Sensors     │
                 └───────┬───────┘
                         ▼
                 ┌───────────────┐
                 │ Perception    │
                 └───────┬───────┘
                         ▼
                 ┌───────────────┐
                 │ Sensor Fusion │
                 └───────┬───────┘
                         ▼
                 ┌───────────────┐
                 │ State / Belief│
                 └───────┬───────┘
                         ▼
                 ┌───────────────┐
                 │ World Model   │
                 │     655       │
                 └───────┬───────┘
                         ▼
              ┌──────────────────────┐
              │ Planning / Reasoning │
              │       652–654        │
              └──────────┬───────────┘
                         ▼
                 ┌───────────────┐
                 │ Controller    │
                 └───────┬───────┘
                         ▼
                 ┌───────────────┐
                 │ Actuator      │
                 └───────┬───────┘
                         ▼
                     Physical World
```

---

# 3. Core Design Principle

Axiom phải phân biệt rõ:

```text
Perception
State estimation
Decision
Planning
Control
Actuation
```

Không cho phép một neural model duy nhất âm thầm thực hiện toàn bộ pipeline mà không expose contract.

---

# 4. Core Types

```text
EmbodiedAgent
Embodiment
Body
BodyPart

Sensor
SensorId
SensorFrame
SensorMeasurement
SensorStream

Actuator
ActuatorId
ActuatorCommand
ActuatorState

PerceptionModel
Detection
TrackingResult
Segmentation
PoseEstimate
DepthEstimate

SensorFusion
FusionState
MeasurementModel

Controller
ControlPolicy
ControlCommand
ControlLoop

Motion
Trajectory
Waypoint
Path

RobotState
KinematicState
DynamicState

SafetyEnvelope
ControlConstraint
EmergencyStop

RealtimeLoop
ControlCycle
Deadline
LatencyBudget
```

---

# 5. EmbodiedAgent

```axiom
agent Robot:
    body = RobotBody
    sensors = RobotSensors
    actuators = RobotActuators
    controller = RobotController
```

Agent phải có identity và lifecycle.

---

# 6. Embodiment

Embodiment mô tả physical interface:

```text
body
joints
links
sensors
actuators
coordinate_frames
kinematics
dynamics
limits
```

---

# 7. Body

Body có thể là:

```text
single rigid body
multi-link robot
vehicle
drone
humanoid
industrial machine
device
```

---

# 8. Body Part

```text
BodyPart:
    id
    parent
    transform
    mass
    geometry
    collision_shape
    inertia
```

---

# 9. Joint

Native joint types:

```text
Fixed
Revolute
Prismatic
Continuous
Spherical
Planar
Universal
Custom
```

---

# 10. Joint State

```text
position
velocity
acceleration
effort
temperature
limit_state
```

---

# 11. Joint Limits

```text
position_min
position_max
velocity_max
acceleration_max
jerk_max
effort_max
temperature_max
```

Limits là hard safety constraints nếu được khai báo là safety-critical.

---

# 12. Coordinate Frames

656 sử dụng frame system của 655:

```text
world
map
base
body
joint
sensor
tool
camera
```

Transform phải có timestamp.

---

# 13. Transform

```axiom
T = transform(
    from = camera,
    to = world,
    timestamp = t
)
```

Transform có thể uncertain.

---

# 14. Sensor

```axiom
sensor Camera:
    type = camera
    rate = 30Hz
```

Sensor metadata:

```text
resolution
sampling_rate
latency
noise_model
frame
calibration
timestamp_source
```

---

# 15. Sensor Types

Native abstraction:

```text
Camera
DepthCamera
Lidar
Radar
IMU
GPS
GNSS
Magnetometer
Encoder
ForceTorque
Microphone
Temperature
Pressure
Proximity
Touch
Custom
```

---

# 16. Sensor Measurement

```text
measurement
timestamp
sensor_id
frame
unit
quality
uncertainty
sequence_number
```

---

# 17. Sensor Stream

```axiom
stream camera.frames
```

Phải hỗ trợ:

- bounded buffer;
- backpressure;
- timestamp ordering;
- dropped-frame metadata;
- zero-copy where possible.

---

# 18. Sensor Synchronization

Sensors có clock khác nhau.

656 phải hỗ trợ:

```text
hardware timestamp
software timestamp
clock offset
clock drift
synchronization uncertainty
```

---

# 19. Time Synchronization

Không được giả định:

```text
camera.timestamp == imu.timestamp
```

Phải explicit synchronization.

---

# 20. Sensor Calibration

Calibration object:

```text
intrinsics
extrinsics
distortion
bias
scale
noise
temperature compensation
```

---

# 21. Calibration Version

Mỗi measurement phải có thể truy ngược:

```text
calibration_revision
```

---

# 22. Sensor Health

Sensor state:

```text
Healthy
Degraded
Unavailable
Stale
Invalid
```

---

# 23. Sensor Fault

Fault detection có thể dựa trên:

```text
range checks
rate checks
consistency
cross-sensor disagreement
statistical tests
learned anomaly detector
```

---

# 24. Sensor Fusion

```axiom
fusion.update(
    camera_measurement,
    lidar_measurement,
    imu_measurement
)
```

Output:

```text
FusionState
```

---

# 25. Fusion Strategies

Hỗ trợ:

```text
early fusion
mid-level fusion
late fusion
state-level fusion
decision-level fusion
```

---

# 26. Probabilistic Fusion

653 cung cấp:

```text
Bayesian update
Kalman filtering
particle filtering
factor graph
```

656 chỉ định integration contract.

---

# 27. Kalman Family

Provider có thể hỗ trợ:

```text
KF
EKF
UKF
information filter
```

---

# 28. Particle Fusion

```text
particles
weights
resampling
effective_sample_size
```

---

# 29. Factor Graph Fusion

```text
Sensor A ─┐
Sensor B ─┼→ Factors → State
Sensor C ─┘
```

654 có thể cung cấp graph constraints.

---

# 30. Perception

Perception chuyển measurement thành semantic information.

```axiom
objects = perception.detect(frame)
```

---

# 31. Detection

Detection:

```text
class
confidence
bounding_region
timestamp
frame
track_id optional
```

---

# 32. Segmentation

```text
semantic_mask
instance_mask
panoptic_label
confidence
```

---

# 33. Pose Estimation

Có thể trả:

```text
2D pose
3D pose
orientation
uncertainty
```

---

# 34. Depth

Depth sources:

```text
stereo
lidar
depth sensor
monocular model
multi-view
```

---

# 35. Optical Flow

Native perception primitive:

```text
flow_field
confidence
timestamp
```

---

# 36. Tracking

Tracker:

```axiom
tracker.update(detections)
```

Result:

```text
Track
TrackId
state
velocity
history
confidence
```

---

# 37. Track Lifecycle

```text
Tentative
Confirmed
Lost
Reidentified
Terminated
```

---

# 38. Multi-Object Tracking

Tracker phải hỗ trợ:

- association;
- gating;
- track birth;
- track death;
- occlusion;
- re-identification.

---

# 39. World Model Integration

```text
Perception
    ↓
Detection/Track
    ↓
655 World State
```

Không ghi trực tiếp observation thành ground-truth state.

---

# 40. Semantic Scene

655 world state có thể chứa:

```text
objects
agents
obstacles
surfaces
regions
goals
events
```

---

# 41. Spatial Map

656 hỗ trợ:

```text
occupancy_map
voxel_map
point_cloud_map
mesh_map
semantic_map
topological_map
```

---

# 42. Mapping

Mapping subsystem:

```axiom
map.update(observation, pose)
```

---

# 43. SLAM Boundary

Provider boundary:

```text
Visual SLAM
Lidar SLAM
Visual-Inertial SLAM
Graph SLAM
```

655 lưu resulting world state.

---

# 44. Localization

```axiom
pose = localize(sensor_data)
```

Result:

```text
pose
covariance
timestamp
frame
quality
```

---

# 45. Global Localization

Có thể dùng:

```text
GNSS
map matching
place recognition
visual localization
```

---

# 46. Localization Failure

Phải có explicit:

```text
LostLocalization
LowConfidenceLocalization
FrameMismatch
StalePose
```

---

# 47. Navigation

Navigation pipeline:

```text
Localization
 ↓
Map
 ↓
Global Planning
 ↓
Local Planning
 ↓
Control
```

---

# 48. Path

```text
Path:
    waypoints
    timestamps optional
    frame
    constraints
```

---

# 49. Trajectory

Trajectory extends Path:

```text
position
velocity
acceleration
jerk
time
```

---

# 50. Motion Planning

656 integration với 652:

```text
configuration space
constraints
obstacles
goal
cost
```

652 tìm solution.

---

# 51. Inverse Kinematics

Native API:

```axiom
joint_state = ik(
    target_pose,
    robot_model
)
```

---

# 52. Forward Kinematics

```axiom
pose = fk(
    robot_model,
    joint_state
)
```

---

# 53. Jacobian

```axiom
J = jacobian(
    robot,
    joint_state
)
```

---

# 54. Dynamics

Robot dynamics:

```text
M(q)q̈ + C(q,q̇) + G(q) = τ
```

Provider có thể expose:

```text
mass_matrix
coriolis
gravity
friction
external_force
```

---

# 55. Controller

Controller:

```axiom
controller.compute(
    state,
    target
)
```

Output:

```text
ControlCommand
```

---

# 56. Controller Types

Native abstractions:

```text
PID
PD
PI
LQR
MPC
computed_torque
impedance
admittance
feedforward
model-based
learned
hybrid
```

---

# 57. PID

```text
error
integral
derivative
output
```

Phải hỗ trợ:

```text
anti_windup
saturation
deadband
rate_limit
```

---

# 58. Safety Saturation

Controller output phải có thể bị giới hạn:

```text
min
max
rate
acceleration
jerk
```

---

# 59. Control Policy

Policy có thể là:

```text
deterministic
stochastic
learned
rule-based
hybrid
```

---

# 60. Learned Controller

643 model có thể produce:

```text
action
control_target
trajectory
```

Nhưng safety layer vẫn nằm bên ngoài.

---

# 61. Safety Controller

Kiến trúc:

```text
Learned Policy
      ↓
Safety Filter
      ↓
Actuator Command
```

---

# 62. Safety Filter

Có thể dùng:

```text
constraint projection
control barrier function provider
reachability provider
formal verification 654
```

---

# 63. Emergency Stop

Native:

```axiom
safety.emergency_stop()
```

Phải có latency contract.

---

# 64. Emergency Stop Authority

Emergency stop phải có priority cao hơn ordinary controller.

```text
Safety
  >
Control
  >
Planning
  >
Agent
```

---

# 65. Actuator

```axiom
actuator Motor:
    type = motor
```

Metadata:

```text
range
rate
latency
precision
failure_modes
```

---

# 66. Actuator Command

```text
target
mode
timestamp
duration
limits
```

---

# 67. Actuator Modes

```text
Position
Velocity
Torque
Force
Power
PWM
Digital
Custom
```

---

# 68. Command Acknowledgement

Actuator runtime phải phân biệt:

```text
command_sent
command_received
command_started
command_completed
command_failed
```

---

# 69. Actuator Feedback

```text
actual_position
actual_velocity
actual_effort
temperature
fault
```

---

# 70. Closed-Loop Control

```text
target
 ↓
controller
 ↓
actuator
 ↓
physical response
 ↓
sensor
 ↓
state estimate
 ↓
controller
```

---

# 71. Control Frequency

Control loop phải khai báo:

```text
frequency
period
deadline
jitter_budget
```

---

# 72. Real-Time Runtime

656 sử dụng 607 nhưng thêm real-time contract:

```text
hard realtime
soft realtime
best effort
```

---

# 73. Hard Real-Time

Hard real-time operation phải:

- tránh unbounded allocation;
- tránh blocking unknown operations;
- tránh GC;
- tránh unbounded locks;
- có deterministic scheduling contract.

Điều này phù hợp với định hướng Axiom tránh GC trong critical runtime.

---

# 74. Soft Real-Time

Cho phép:

- inference;
- perception;
- planning;
- logging;

miễn deadline miss được theo dõi.

---

# 75. Deadline

```text
deadline
budget
actual_duration
miss_count
```

---

# 76. Jitter

Runtime phải đo:

```text
period_jitter
execution_jitter
sensor_jitter
actuator_jitter
```

---

# 77. Priority

Control scheduling:

```text
Emergency
Safety
HardControl
Sensor
StateEstimation
Actuation
Planning
Perception
Logging
Background
```

Không phải mọi thread đều có cùng priority.

---

# 78. Executor

607 cung cấp executor.

656 yêu cầu:

```text
RealtimeExecutor
```

với bounded behavior.

---

# 79. Memory

Real-time loop nên hỗ trợ:

```text
preallocated buffers
object pools
ring buffers
stack allocation
arena
fixed-capacity containers
```

---

# 80. No Hidden Allocation

Một function được đánh dấu:

```axiom
@realtime
```

không được compiler/runtime silently allocate heap nếu profile cấm.

---

# 81. Zero-Copy Sensor Pipeline

```text
Sensor DMA
 ↓
Shared Buffer
 ↓
Perception
 ↓
Fusion
```

Có thể tránh copy.

---

# 82. Buffer Ownership

Dùng Axiom memory model thay vì raw pointer conventions.

Buffer states:

```text
owned
shared
borrowed
readonly
released
```

nhưng API user-facing phải tối giản.

---

# 83. DMA

614 cung cấp:

```text
DMA buffer
device memory
mapped memory
```

656 có thể consume.

---

# 84. GPU Perception

649/643 cung cấp model.

656 hỗ trợ:

```text
camera
 ↓
GPU preprocessing
 ↓
GPU inference
 ↓
CPU/world state
```

---

# 85. GPU Control

GPU chỉ được dùng cho control nếu latency contract đảm bảo.

Không tự động đẩy hard-real-time control lên GPU.

---

# 86. Accelerator

Có thể target:

```text
CUDA
Metal
Vulkan
DirectML
NPU
DSP
FPGA provider
```

nhưng core không phụ thuộc một backend.

---

# 87. Device Abstraction

614 giữ:

```text
Device
DeviceDriver
DeviceCapability
```

656 giữ:

```text
Sensor
Actuator
Embodiment
```

---

# 88. Robot Description

Axiom có declarative representation:

```axiom
robot Arm:
    link base
    link shoulder
    link elbow
    link wrist

    joint shoulder:
        type = revolute
```

---

# 89. Collision Model

Body phải khai báo:

```text
collision_geometry
collision_group
collision_mask
```

---

# 90. Collision Query

```axiom
collision = world.check_collision(
    robot_state,
    environment
)
```

---

# 91. Distance Query

```axiom
distance = world.distance(
    robot,
    obstacle
)
```

---

# 92. Collision Constraints

652 có thể sử dụng:

```text
distance >= safety_margin
```

làm constraint.

---

# 93. Reachability

655/654/652 có thể kiểm tra:

```text
reachable(target)
```

---

# 94. Workspace

Embodied agent có:

```text
reachable_workspace
safe_workspace
operational_workspace
```

---

# 95. Manipulation

Pipeline:

```text
perception
 ↓
object pose
 ↓
grasp planning
 ↓
motion planning
 ↓
control
 ↓
grasp
```

---

# 96. Grasp

Core abstraction:

```text
Grasp:
    object
    contact_points
    pose
    force
    quality
```

---

# 97. Force Control

656 hỗ trợ:

```text
force_target
impedance
admittance
```

---

# 98. Visual Servoing

```text
camera
 ↓
visual error
 ↓
controller
 ↓
actuator
```

---

# 99. Locomotion

Body abstraction phải hỗ trợ:

```text
wheeled
legged
flying
swimming
custom
```

---

# 100. Footstep Planning

Legged robot có:

```text
support_polygon
footstep
contact_schedule
```

---

# 101. Contact State

```text
contact
no_contact
sliding
impact
uncertain
```

---

# 102. Force/Torque Sensor

Measurement:

```text
force
torque
frame
timestamp
covariance
```

---

# 103. Haptic Feedback

Có thể đưa:

```text
force
touch
vibration
```

vào perception loop.

---

# 104. Human Interaction

618/619 cung cấp:

```text
human input
gesture
voice
pointer
```

656 có thể map thành:

```text
intent
target
command
```

---

# 105. Speech-Controlled Embodiment

649:

```text
speech
 ↓
semantic intent
 ↓
644
 ↓
652
 ↓
656 control
```

Không cho speech trực tiếp cấp actuator authority.

---

# 106. Agent Authority Boundary

```text
LLM/Agent
   ↓
Intent
   ↓
Planning
   ↓
Safety
   ↓
Control
   ↓
Actuator
```

---

# 107. LLM Cannot Directly Drive Motor

LLM output phải đi qua:

```text
typed action schema
policy validation
safety constraints
controller
```

---

# 108. Autonomous Mode

Modes:

```text
Manual
Assisted
Supervised
Autonomous
Emergency
SafeStop
```

---

# 109. Mode Transition

Không được arbitrary switch.

Mỗi transition phải có policy:

```text
Manual → Autonomous
Autonomous → SafeStop
```

---

# 110. Human Override

Human override phải có priority:

```text
Emergency human stop
>
autonomous controller
```

nếu hardware contract cho phép.

---

# 111. Safety Envelope

```text
SafetyEnvelope:
    velocity_limit
    acceleration_limit
    workspace
    collision_margin
    force_limit
    temperature_limit
    battery_limit
```

---

# 112. Runtime Safety Monitor

Monitor:

```text
state
command
sensor health
actuator health
deadline
collision
constraint violations
```

---

# 113. Safety Violation

Khi violation:

```text
warning
degrade
stop
emergency_stop
```

theo policy.

---

# 114. Graceful Degradation

Ví dụ camera mất:

```text
camera unavailable
 ↓
reduce capability
 ↓
lidar + IMU
```

Nếu không đủ:

```text
safe stop
```

---

# 115. Fault-Tolerant Sensor Fusion

Có thể loại bỏ sensor lỗi mà không crash toàn bộ pipeline.

---

# 116. Redundancy

Hỗ trợ:

```text
sensor redundancy
actuator redundancy
model redundancy
controller redundancy
```

---

# 117. Watchdog

605 cung cấp process watchdog.

656 bổ sung:

```text
control watchdog
sensor watchdog
actuator watchdog
deadline watchdog
```

---

# 118. Control Watchdog

Nếu control loop miss N deadlines:

```text
fallback_controller
```

hoặc:

```text
safe_stop
```

theo safety policy.

---

# 119. Health State

EmbodiedAgent:

```text
Healthy
Degraded
Unsafe
Emergency
Offline
```

---

# 120. Telemetry

633 thu thập:

```text
sensor_latency
perception_latency
fusion_latency
planning_latency
control_latency
actuator_latency
loop_jitter
deadline_miss
```

---

# 121. Recording

Có thể record:

```text
sensor streams
state
actions
commands
responses
model versions
```

để replay.

---

# 122. Deterministic Replay

Replay:

```text
recorded sensors
+
same model revision
+
same seed
```

cho phép reproduce control decisions trong declared tolerance.

---

# 123. Simulation Bridge

648:

```text
simulated sensors
simulated actuators
```

656:

```text
same perception/control APIs
```

Điều này cho phép:

```text
simulation → hardware
```

mà không đổi application architecture.

---

# 124. Sim-to-Real

Model metadata phải đánh dấu:

```text
simulation_domain
real_domain
domain_gap
calibration_revision
```

---

# 125. Hardware-in-the-Loop

656 hỗ trợ:

```text
real controller
+
simulated environment
```

---

# 126. Software-in-the-Loop

```text
simulation
+
software controller
+
software sensors
```

---

# 127. Digital Twin Loop

```text
Real Robot
 ↓
Telemetry
 ↓
655 Twin
 ↓
Simulation
 ↓
656 Controller Test
 ↓
Validated Update
```

---

# 128. Fleet Robotics

Một embodied model có thể chạy trên nhiều robots:

```text
RobotType
RobotInstance
RobotConfiguration
```

---

# 129. Fleet Coordination

652/630/635 cung cấp:

```text
task allocation
resource allocation
fleet scheduling
```

656 cung cấp local execution.

---

# 130. Multi-Robot Perception

Robot A/B có thể chia sẻ:

```text
observations
maps
tracks
world state
```

qua 604/628/634.

---

# 131. Distributed World Model

655 có thể giữ:

```text
local world model
```

và đồng bộ với:

```text
fleet world model
```

---

# 132. Latency-Aware Coordination

Mọi remote state phải có:

```text
source_time
receive_time
network_latency
staleness
```

---

# 133. Stale State

Một state quá cũ phải đánh dấu:

```text
stale
```

không được sử dụng như current state nếu policy cấm.

---

# 134. Safety Under Communication Loss

Nếu mất network:

```text
local autonomy
fallback
safe stop
```

tùy capability/policy.

---

# 135. No Network Dependency for Critical Loop

Hard-real-time control không được phụ thuộc mandatory cloud/network round-trip.

---

# 136. Remote AI

Cloud model có thể cung cấp:

```text
high-level plan
semantic interpretation
```

nhưng local safety/control phải có fallback.

---

# 137. Embodied Memory

650 lưu:

```text
successful trajectories
failures
environment maps
object interactions
calibration history
```

---

# 138. Skill Representation

Một embodied skill:

```axiom
skill PickObject:
    input ObjectPose
    output GraspResult
```

---

# 139. Skill Composition

```text
Navigate
 →
Detect
 →
Approach
 →
Grasp
 →
Lift
 →
Place
```

---

# 140. Skill Library

Skills có metadata:

```text
preconditions
effects
duration
required_capabilities
safety_requirements
```

---

# 141. Skill Learning

643/644 có thể học skill.

656 runtime thực thi skill qua typed interface.

---

# 142. Skill Verification

654 có thể kiểm tra:

```text
precondition
postcondition
invariant
```

---

# 143. Skill Failure

```text
SkillFailed
PartialSuccess
UnsafeState
PreconditionLost
Timeout
```

---

# 144. Recovery

644/652 có thể lập recovery plan.

656 cung cấp current state và failure context.

---

# 145. Recovery Example

```text
grasp_failed
 ↓
observe
 ↓
re-estimate
 ↓
re-plan
 ↓
retry
```

---

# 146. Real-Time Agent

656 định nghĩa:

```text
RealtimeAgent
```

gồm:

```text
observe()
estimate()
predict()
plan()
control()
act()
```

---

# 147. Agent Tick

```text
tick:
    observations = observe()
    state = estimate(observations)
    prediction = world.predict(state)
    plan = planner.plan(state, prediction)
    command = controller.compute(state, plan)
    safety.validate(command)
    actuate(command)
```

---

# 148. Tick Budget

Mỗi tick có:

```text
observation_budget
estimation_budget
planning_budget
control_budget
actuation_budget
```

---

# 149. Partial Completion

Nếu planning chưa xong nhưng control deadline tới:

```text
previous_safe_plan
```

có thể tiếp tục nếu policy cho phép.

---

# 150. Anytime Planning

652 có thể cung cấp:

```text
best_solution_so_far
```

656 có thể consume khi deadline gần tới.

---

# 151. Control Fallback

Nếu planner timeout:

```text
fallback_policy
```

Không được gửi uninitialized command.

---

# 152. Safe Default

Mỗi actuator/control path phải có:

```text
safe_default
```

nếu contract yêu cầu.

---

# 153. Runtime Contract

```axiom
@realtime
@deadline(2ms)
@priority(HardControl)
fn control_tick(...)
```

Compiler/runtime kiểm tra:

- blocking;
- allocation;
- unbounded loops;
- unsupported calls.

---

# 154. Compiler Analysis

Compiler phải có thể cảnh báo:

```text
RealtimeViolation
PossibleBlocking
UnboundedAllocation
UnboundedLoop
UnknownLatency
UnsafeActuatorPath
MissingSafetyFilter
```

---

# 155. Static Safety

Các annotation:

```text
@realtime
@safety_critical
@actuator
@sensor
@control
```

tạo static analysis.

---

# 156. Generated Metadata

```text
.axembodiment
.axrobot
.axsensor
.axactuator
.axcalibration
.axperception
.axtracking
.axfusion
.axlocalization
.axmapping
.axnavigation
.axtrajectory
.axcontroller
.axcontrol
.axsafety
.axrealtime
.axskill
```

---

# 157. Compiler IR

Core operations:

```text
SensorRead
SensorSync
SensorFuse
PerceptionInfer
TrackUpdate
StateEstimate
MapUpdate
Localize
PlanMotion
InverseKinematics
ForwardKinematics
ComputeControl
SafetyCheck
ActuatorWrite
EmergencyStop
ControlWatchdog
```

---

# 158. Zero-Copy IR

Compiler được phép biến:

```text
Sensor DMA
→ inference buffer
→ perception
```

thành shared buffer pipeline khi alias/lifetime contract an toàn.

---

# 159. SIMD

Các operation:

```text
sensor transforms
point cloud
image preprocessing
kinematics
matrix operations
```

có thể vectorize.

---

# 160. Tensor Integration

643/649 cung cấp:

```text
Tensor
```

656 sử dụng tensor cho:

- perception;
- learned control;
- sensor fusion;
- trajectory prediction.

---

# 161. Native Tensor Memory

Critical path phải hỗ trợ:

```text
CPU tensor
GPU tensor
device tensor
shared tensor
```

với explicit transfer semantics.

---

# 162. Async Integration

607:

```text
sensor_stream.async
```

nhưng hard realtime loop không phụ thuộc generic async scheduler nếu latency contract không đảm bảo.

---

# 163. Backpressure

Sensor stream có thể:

```text
drop_oldest
drop_newest
sample
block
coalesce
```

policy explicit.

---

# 164. Frame Dropping

Nếu perception không theo kịp camera:

```text
frame_drop_count
```

phải telemetry.

---

# 165. Temporal Alignment

Perception model phải biết:

```text
capture_time
processing_time
prediction_time
```

---

# 166. Latency Compensation

World model có thể predict từ:

```text
capture_time
```

đến:

```text
actuation_time
```

để compensate latency.

---

# 167. Prediction Horizon

Control API phải khai báo:

```text
latency_compensation_horizon
```

nếu sử dụng.

---

# 168. Actuator Delay

Actuator model có:

```text
command_delay
response_delay
settling_time
```

---

# 169. Closed-Loop Stability

Controller provider có thể expose:

```text
stability_certificate
```

hoặc:

```text
stability_status
```

Không tự tuyên bố stability nếu provider không chứng minh.

---

# 170. Formal Safety

654 có thể kiểm tra:

```text
invariant:
    robot.velocity <= 2m/s
```

---

# 171. Reachability Safety

Provider có thể kiểm tra:

```text
reachable unsafe region
```

---

# 172. Barrier Safety

Provider boundary:

```text
control_barrier_function
```

---

# 173. Runtime Safety Kernel

Một profile tối thiểu:

```text
AXEMBEDDED_SAFE
```

chỉ bao gồm:

```text
sensor
state
control
safety
actuator
watchdog
```

Không cần AI model.

---

# 174. Embedded Target

656 phải chạy được trên:

- microcontroller;
- embedded Linux;
- RTOS;
- desktop;
- mobile;
- server;
- GPU edge device.

---

# 175. Resource Profiles

```text
AXEMB_MIN
AXEMB_EMBEDDED
AXEMB_REALTIME
AXEMB_ROBOT
AXEMB_VISION
AXEMB_AUTONOMOUS
AXEMB_AI
AXEMB_GPU
AXEMB_FLEET
AXEMB_FULL
```

---

# 176. Memory Footprint

Runtime phải hỗ trợ static sizing cho critical components:

```text
sensor_buffer
state_buffer
command_buffer
trajectory_buffer
watchdog_state
```

---

# 177. Static Configuration

Embedded build có thể compile:

```text
fixed sensor count
fixed actuator count
fixed buffer sizes
fixed control rate
```

để loại bỏ dynamic overhead.

---

# 178. Dynamic Configuration

Desktop/server vẫn có:

```text
dynamic device discovery
hotplug
runtime model loading
```

---

# 179. Device Discovery

614 cung cấp device discovery.

656 maps device → sensor/actuator schema.

---

# 180. Driver Boundary

Axiom core không hard-code vendor driver.

Driver interface:

```text
open
configure
read
write
reset
diagnostics
close
```

---

# 181. Hardware Fault

Driver phải trả:

```text
HardwareFault
CommunicationFault
CalibrationFault
Overtemperature
Overcurrent
```

---

# 182. Fault Containment

Một sensor fault không được tự động crash unrelated control subsystems.

---

# 183. Safety-Critical Partition

Critical components có thể chạy trong isolated process/domain.

603/605 hỗ trợ isolation.

---

# 184. Process Isolation

```text
AI perception process
      ↓
validated state IPC
      ↓
control process
```

---

# 185. Capability Isolation

AI model chỉ nhận capability cần thiết:

```text
read_camera
read_state
request_plan
```

không:

```text
direct_motor_write
```

nếu policy không cấp.

---

# 186. Secure Firmware Boundary

614/603 quản lý:

```text
device identity
secure boot
firmware capability
```

656 chỉ consume.

---

# 187. Logging

633/602 ghi:

```text
sensor anomalies
control events
deadline misses
safety events
actuator faults
mode transitions
```

---

# 188. Event Timeline

Mỗi control cycle có thể trace:

```text
sensor timestamp
state timestamp
plan timestamp
command timestamp
actuator acknowledgement
```

---

# 189. Distributed Trace

Nếu planner chạy remote:

```text
sensor
→ edge
→ network
→ planner
→ edge
→ controller
```

633 trace phải preserve latency.

---

# 190. Data Recording Policy

640 quyết định:

```text
retention
privacy
residency
classification
```

656 chỉ expose metadata.

---

# 191. Privacy

Camera/microphone data có thể chứa personal data.

Không tự bypass 640/603.

---

# 192. Human Detection

Nếu perception phát hiện người:

```text
PersonDetection
```

không tự cấp identity.

Identity resolution thuộc 627/645 và governance.

---

# 193. Human Safety

Human presence có thể trở thành:

```text
safety_obstacle
```

nếu configured.

---

# 194. Social Interaction

Embodied agent có thể:

```text
listen
speak
gesture
move
```

nhưng action authority vẫn qua policy/control.

---

# 195. Natural Language Command

```text
"đi đến cửa"
```

pipeline:

```text
speech/text
 ↓
semantic intent
 ↓
644
 ↓
652
 ↓
656
```

---

# 196. No Direct Language-to-Motor

Compiler/runtime không cho phép:

```text
LLM string → actuator raw command
```

trong safety profile.

---

# 197. Skill API

```axiom
@skill
fn navigate_to(target: Pose) -> Result
```

Skill có:

```text
preconditions
effects
required_capabilities
safety_contract
```

---

# 198. Skill Contract

Ví dụ:

```axiom
requires:
    localization.confidence > 0.95

ensures:
    distance_to(target) < 0.2m
```

---

# 199. Skill Planner Integration

652 có thể compose skills.

---

# 200. Skill Learning

644/643 có thể generate candidate skill.

654 validates contract.

656 executes.

---

# 201. Skill Version

```text
SkillId
SkillVersion
ModelRevision
SafetyRevision
```

phải pin trong production execution.

---

# 202. Autonomous Task

```axiom
task DeliverPackage:
    navigate warehouse_A
    grasp package
    navigate station_B
    place package
```

652 lập plan.

656 thực thi primitive skills.

---

# 203. Recovery Policy

Task failure:

```text
observe
diagnose
replan
retry
fallback
safe_stop
```

---

# 204. Failure Diagnosis

Có thể sử dụng:

```text
653 probability
654 symbolic reasoning
655 world model
646 evaluation
```

---

# 205. Learning From Failure

Record:

```text
initial_state
action
prediction
actual_outcome
failure
recovery
```

để 643/644/655 học.

---

# 206. Experience Replay

650 có thể lưu:

```text
experience
```

656 cung cấp structured trajectory.

---

# 207. Reinforcement Learning Integration

643 RL policy:

```text
state → action
```

656:

```text
sensor → state
policy → command
safety → command
actuator
```

---

# 208. RL Safety

RL policy không được bypass:

```text
SafetyFilter
Capability
ActuatorLimits
```

---

# 209. Offline RL

Training data từ 656 recordings có thể feed 643.

---

# 210. Imitation Learning

Human demonstration:

```text
observation
action
trajectory
```

được record và đưa vào 643.

---

# 211. Teleoperation

Manual controller:

```text
human input
 ↓
teleoperation command
 ↓
safety filter
 ↓
actuator
```

---

# 212. Shared Autonomy

Human + AI:

```text
human intent
+
AI assistance
+
safety
```

---

# 213. Authority Arbitration

Nếu human và AI command khác nhau:

```text
authority_policy
```

quyết định.

656 không tự quyết định.

---

# 214. Fleet Learning

Nhiều robot gửi experience:

```text
Robot A
Robot B
Robot C
 ↓
shared dataset
 ↓
643
 ↓
new model
 ↓
647 validation
 ↓
fleet rollout
```

---

# 215. Canary Deployment

636 rollout model mới:

```text
small subset
 ↓
monitor
 ↓
validate
 ↓
expand
```

---

# 216. Rollback

Nếu safety/performance regression:

```text
647 rollback model
636 rollback deployment
```

---

# 217. Simulation Before Deployment

648 có thể test:

```text
new policy
new controller
new dynamics
```

trên scenario suite trước hardware.

---

# 218. Hardware Safety Gate

Production deployment có thể yêu cầu:

```text
simulation_pass
formal_check
hardware_test
shadow_test
approval
```

---

# 219. Compiler Annotations

```text
@embodied
@robot
@body
@link
@joint
@sensor
@actuator
@measurement
@sensor_stream
@calibration
@perception
@detect
@segment
@track
@localize
@mapping
@slam
@fusion
@navigation
@motion
@trajectory
@kinematics
@dynamics
@controller
@control
@realtime
@hard_realtime
@soft_realtime
@deadline
@watchdog
@safety
@safety_critical
@safety_filter
@emergency_stop
@skill
@teleoperation
@autonomous
@shared_autonomy
@sim2real
@hardware_in_loop
```

---

# 220. CLI

```text
axiom robot inspect
axiom robot validate
axiom robot calibrate

axiom sensor inspect
axiom sensor stream
axiom sensor diagnose
axiom sensor replay

axiom perception benchmark
axiom perception replay

axiom localization inspect
axiom mapping inspect
axiom mapping replay

axiom motion plan
axiom motion validate
axiom kinematics fk
axiom kinematics ik

axiom control benchmark
axiom control replay
axiom control analyze

axiom safety inspect
axiom safety validate
axiom safety test

axiom embodied replay
axiom embodied record
axiom embodied simulate
axiom embodied benchmark
```

---

# 221. Generated Reports

```text
.axembodied_report
.axsensor_report
.axcontrol_report
.axsafety_report
.axrealtime_report
.axtrajectory_report
.axreplay_report
```

---

# 222. Runtime Metrics

Required metrics:

```text
sensor_latency
fusion_latency
perception_latency
localization_latency
planning_latency
control_latency
actuation_latency
cycle_time
deadline_miss
jitter
dropped_frames
stale_measurements
safety_interventions
fallback_count
```

---

# 223. Critical Runtime Invariants

Tối thiểu 100 invariants.

Các invariant nền tảng:

1. Sensor measurement có timestamp.
2. Sensor measurement có source identity.
3. Sensor frame phải xác định coordinate frame.
4. Calibration revision phải truy xuất được.
5. Sensor stream phải có overflow policy.
6. Dropped frames phải observable.
7. Stale measurement phải detectable.
8. Fusion không được làm mất provenance.
9. State estimate phải giữ uncertainty nếu available.
10. Perception output không phải ground truth.
11. Track identity phải versioned.
12. Transform phải có frame source/destination.
13. Transform phải có time semantics.
14. Unit conversion phải explicit.
15. Actuator command phải typed.
16. Actuator command phải validate limits.
17. Safety limits không được bypass bởi controller.
18. Emergency stop có priority cao hơn normal control.
19. Control deadline phải measurable.
20. Hard realtime code không được hidden allocation.
21. Hard realtime code không được unbounded blocking.
22. Control fallback phải deterministic khi required.
23. Uninitialized actuator command không được gửi.
24. Failed controller không được trả success.
25. Sensor fault phải detectable.
26. Actuator fault phải detectable.
27. Safety monitor phải độc lập với learned policy.
28. Learned policy không có direct authority nếu capability không cấp.
29. LLM output không trực tiếp điều khiển actuator.
30. Planning không được bypass safety.
31. World model prediction không phải actual outcome.
32. Simulation không phải real observation.
33. Sim-to-real state phải marked.
34. Telemetry không được sửa control state.
35. Logging không được block hard realtime loop.
36. Remote network không được mandatory cho critical loop.
37. Remote state phải có staleness metadata.
38. Clock synchronization uncertainty phải preserve.
39. Model revision phải pin khi required.
40. Skill version phải pin khi required.
41. Safety contract phải versioned.
42. Robot embodiment schema phải versioned.
43. Joint limits phải explicit.
44. Collision geometry phải versioned.
45. Kinematic model phải compatible với joint state.
46. Dynamics model phải compatible với embodiment.
47. IK result phải validate joint limits.
48. FK phải preserve frame semantics.
49. Trajectory phải preserve time ordering.
50. Trajectory command phải kiểm tra dynamic limits.
51. Collision checking phải sử dụng compatible world revision.
52. Localization result phải có quality metadata.
53. Lost localization phải observable.
54. Mapping updates phải preserve timestamps.
55. Sensor fusion không được silently mix incompatible clocks.
56. Prediction latency compensation phải explicit.
57. Actuator delay phải modelable.
58. Control output saturation phải observable.
59. Watchdog state phải persistent trong critical profile.
60. Emergency stop phải have explicit hardware/software semantics.
61. Safety filter phải report rejected commands.
62. Rejected command không được coi là executed.
63. Command acknowledgement phải phân biệt sent/received/executed.
64. Actual actuator state không được suy ra chỉ từ command.
65. Replay phải pin model versions.
66. Replay phải pin RNG when stochastic.
67. Replay phải preserve sensor ordering.
68. Deterministic mode phải có declared numerical tolerance.
69. Simulation result phải mark synthetic.
70. Hardware-in-loop phải mark hardware participation.
71. Teleoperation command phải qua safety.
72. Shared autonomy phải có authority policy.
73. Autonomous mode transition phải policy-controlled.
74. Safe-stop transition phải observable.
75. Fallback activation phải observable.
76. Fleet state phải giữ robot identity.
77. Remote world state phải giữ source robot.
78. Cross-robot state phải preserve confidence.
79. Multi-agent state không được merge identities implicitly.
80. Human identity không được suy ra chỉ từ detection.
81. Human detection không tự cấp identity authority.
82. Privacy-sensitive sensor data phải obey governance.
83. Sensor recordings phải obey retention policy.
84. AI-generated skill phải marked generated.
85. Skill execution phải check preconditions.
86. Skill success phải check postconditions.
87. Skill failure phải preserve failure context.
88. Recovery không được bypass safety.
89. RL policy không được bypass actuator limits.
90. Model rollout không được mutate physical state.
91. World-model branch không được mutate real world.
92. Planning simulation không được execute actuator commands.
93. Safety-critical controller phải declare latency budget.
94. Compiler phải reject forbidden realtime operations.
95. Realtime annotation phải propagate through call graph.
96. Unknown-latency operation phải be explicit.
97. Device driver failure phải propagate.
98. Device reset phải preserve safety state.
99. Model deployment phải pass lifecycle policy.
100. Production model update phải create revision.
101. Shadow model không được affect command path.
102. Canary deployment phải be policy-controlled.
103. Rollback phải restore compatible model.
104. Safety regression phải observable.
105. World model uncertainty không được discarded silently.
106. Perception confidence không được treated as probability without declared semantics.
107. Controller stability claim phải have provider/certificate metadata.
108. Formal verification result phải include revision.
109. Safety envelope phải be versioned.
110. Critical loop phải have watchdog.
111. Sensor stream phải have bounded behavior.
112. Control buffers phải have declared capacity in hard realtime.
113. DMA buffers phải obey lifetime rules.
114. Zero-copy optimization không được break ownership.
115. Shared buffers phải preserve synchronization semantics.
116. GPU transfer phải be explicit when latency-critical.
117. Device tensor lifetime phải be safe.
118. Network timeout không được deadlock control.
119. Control loop must have safe behavior on planner timeout.
120. No AI component may silently acquire actuator capability.

---

# 224. Acceptance Criteria

Target:

```text
Embodiment                    >= 60
Sensors                       >= 70
Calibration                   >= 35
Sensor Fusion                 >= 60
Perception                    >= 80
Tracking                      >= 45
Localization                 >= 50
Mapping                       >= 45
Navigation                   >= 60
Kinematics                   >= 45
Dynamics                     >= 50
Motion Planning              >= 60
Controllers                  >= 70
Real-Time                    >= 70
Actuation                    >= 45
Safety                       >= 100
Watchdog                     >= 35
Simulation                   >= 50
Sim-to-Real                  >= 35
Replay                       >= 35
Embodied Agent               >= 50
Skills                       >= 50
RL/AI integration            >= 50
Fleet                        >= 35
Distributed                  >= 30
GPU/Accelerator              >= 35
Compiler/IR                  >= 60
Security/Governance          >= 50
```

Mục tiêu tổng:

```text
>= 1,300 acceptance criteria
```

---

# 225. Minimal Embedded Example

```axiom
robot MiniBot:
    sensor imu
    sensor encoder

    actuator left_motor
    actuator right_motor

    @realtime
    @deadline(1ms)
    fn control_tick():
        imu_state = imu.read()
        encoder_state = encoder.read()

        state = estimate(
            imu_state,
            encoder_state
        )

        command = controller.compute(state)

        safety.validate(command)

        left_motor.write(command.left)
        right_motor.write(command.right)
```

---

# 226. AI Robot Example

```axiom
agent DeliveryRobot:

    observe:
        camera
        lidar
        imu

    perceive:
        objects = detect(camera)
        obstacles = lidar.objects()

    estimate:
        state = world.estimate(
            objects,
            obstacles,
            imu
        )

    plan:
        route = planner.navigate(
            state,
            destination
        )

    control:
        command = controller.follow(
            route,
            state
        )

    safety:
        command = safety.filter(command)

    act:
        motors.write(command)
```

---

# 227. Full Autonomous Loop

```text
┌─────────────────────────────┐
│         Sensors             │
└──────────────┬──────────────┘
               ↓
┌─────────────────────────────┐
│       Perception            │
│  detection / tracking / map │
└──────────────┬──────────────┘
               ↓
┌─────────────────────────────┐
│      Sensor Fusion          │
└──────────────┬──────────────┘
               ↓
┌─────────────────────────────┐
│       State Estimate        │
└──────────────┬──────────────┘
               ↓
┌─────────────────────────────┐
│        World Model          │
│            655              │
└──────────────┬──────────────┘
               ↓
┌─────────────────────────────┐
│ Reasoning / Planning        │
│        652–654              │
└──────────────┬──────────────┘
               ↓
┌─────────────────────────────┐
│       Controller            │
└──────────────┬──────────────┘
               ↓
┌─────────────────────────────┐
│       Safety Filter         │
└──────────────┬──────────────┘
               ↓
┌─────────────────────────────┐
│       Actuators             │
└──────────────┬──────────────┘
               ↓
             WORLD
               │
               └──────────────→ Sensors
```

---

# 228. Separation of Responsibilities

| Layer | Responsibility |
|---|---|
| 643 | ML models / learning |
| 644 | agent reasoning/orchestration |
| 648 | simulation |
| 649 | multimodal perception |
| 650 | memory |
| 652 | planning/optimization |
| 653 | probability/causality |
| 654 | symbolic/formal reasoning |
| 655 | world state/dynamics/prediction |
| **656** | **embodiment/perception-action/control** |

---

# 229. Critical Architectural Rule

Axiom không nên xây dựng:

```text
LLM → motor
```

hoặc:

```text
neural_network → actuator
```

như một abstraction mặc định.

Kiến trúc chuẩn phải là:

```text
AI
 ↓
Intent / Policy
 ↓
Planning
 ↓
World Model
 ↓
Control
 ↓
Safety
 ↓
Actuator
```

Điều này cho phép AI model được thay thế mà không phá vỡ safety/control substrate.

---

# 230. Native Runtime Stack

```text
Axiom Core
   ↓
Memory / Concurrency
   ↓
Device Runtime
   ↓
Realtime Runtime
   ↓
Sensor / Actuator
   ↓
Perception
   ↓
World Model
   ↓
Planning
   ↓
Control
   ↓
Safety
   ↓
Embodied Agent
```

---

# 231. Completion Definition

BOOTSTRAP-656 được coi là hoàn thành khi Axiom có architecture/specification cho:

- embodied agent;
- robot embodiment;
- sensors;
- actuators;
- calibration;
- synchronization;
- perception;
- tracking;
- sensor fusion;
- localization;
- mapping;
- navigation;
- kinematics;
- dynamics;
- motion planning;
- trajectory;
- controllers;
- real-time execution;
- hard/soft realtime;
- safety filters;
- emergency stop;
- watchdog;
- fault tolerance;
- skill execution;
- autonomous agents;
- teleoperation;
- shared autonomy;
- RL integration;
- world-model integration;
- causal integration;
- symbolic verification;
- simulation;
- hardware-in-loop;
- sim-to-real;
- fleet robotics;
- distributed embodied systems;
- GPU/accelerator;
- zero-copy pipelines;
- deterministic replay;
- compiler IR;
- static realtime analysis;
- security/capability boundary;
- governance;
- ≥120 invariants;
- ≥1,300 acceptance criteria.

**BOOTSTRAP-656 — COMPLETE.**

**Next task: BOOTSTRAP-657 — Native AI Cognitive Architecture, Executive Function, Attention, Working Memory, Goal Management, Metacognition, Self-Monitoring & Unified Agent Control Runtime 5.0.**

:::