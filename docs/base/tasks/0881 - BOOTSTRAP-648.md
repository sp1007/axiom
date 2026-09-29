Tiếp tục với **BOOTSTRAP-648 — Native AI Simulation, Synthetic Data, Environment Modeling, Scenario Generation, Digital Twin, Agent Sandbox & Closed-Loop AI Testing Runtime 5.0**.

:::writing{variant="document" id="73164" title="BOOTSTRAP-648 — Native AI Simulation, Synthetic Data, Environment Modeling, Scenario Generation, Digital Twin, Agent Sandbox & Closed-Loop AI Testing Runtime 5.0"}
# BOOTSTRAP-648
## Native AI Simulation, Synthetic Data, Environment Modeling, Scenario Generation, Digital Twin, Agent Sandbox & Closed-Loop AI Testing Runtime 5.0

**Status:** COMPLETE  
**Layer:** Native AI Simulation & Synthetic Environment Plane  
**Depends on:** BOOTSTRAP-600 → BOOTSTRAP-647

---

# 1. Mục tiêu

BOOTSTRAP-648 cung cấp native runtime cho:

- simulation;
- synthetic data;
- environment modeling;
- scenario generation;
- digital twin;
- agent sandbox;
- closed-loop AI testing;
- physics simulation boundary;
- synthetic sensor generation;
- synthetic multimodal data;
- simulation replay;
- deterministic simulation;
- Monte Carlo execution;
- counterfactual evaluation;
- environment state management;
- simulation-to-real validation.

Mục tiêu là để Axiom có thể xây dựng:

```text
AI Agent
   ↓
Environment
   ↓
Observation
   ↓
Action
   ↓
Environment Transition
   ↓
Reward / Result
   ↓
Evaluation
   ↓
Training / Improvement
```

mà không bắt buộc phụ thuộc:

- Unity;
- Unreal;
- MuJoCo;
- Isaac Sim;
- Gazebo;
- AirSim;
- Gymnasium;
- ROS;
- Python;
- external simulation server.

Các hệ thống trên có thể trở thành provider/adapter.

---

# 2. Boundary

```text
614 Device
615 Graphics
616 Media
643 ML
644 Agent
646 Evaluation
647 Model Lifecycle
       │
       ▼
648 Simulation
       │
 ┌─────┼─────────┐
 ▼     ▼         ▼
World  Scenario  Environment
 │       │         │
 ▼       ▼         ▼
State  Generator  Dynamics
 │       │         │
 └───────┼─────────┘
         ▼
     Observation
         │
         ▼
       Agent
         │
         ▼
       Action
         │
         ▼
      Simulator
```

---

# 3. Nguyên tắc

1. Simulation state phải explicit.
2. Environment state phải versioned.
3. Simulation time khác wall-clock time.
4. Deterministic simulation phải được hỗ trợ.
5. Randomness phải seedable.
6. Replay phải reproducible khi provider cho phép.
7. Simulation không được tự cấp capability.
8. Agent không được tự thoát sandbox.
9. Tool access phải explicit.
10. Environment action phải typed.
11. Invalid action phải có semantics rõ.
12. Physics là provider boundary.
13. Rendering là provider boundary.
14. Sensor simulation là provider boundary.
15. Synthetic data có provenance.
16. Synthetic data có lineage.
17. Synthetic data không tự động được coi là real data.
18. Simulation artifact có identity.
19. Scenario có version.
20. Environment có version.
21. Model có version.
22. Agent có version.
23. Closed-loop run có immutable identity.
24. Evaluation reference phải immutable.
25. No hidden state.
26. No hidden random seed.
27. No implicit wall-clock dependency trong deterministic mode.
28. No unbounded simulation.
29. Resource limits từ 606.
30. Execution scheduling từ 607.
31. Security từ 603.
32. Policy từ 639.
33. Governance từ 640.
34. Model lifecycle từ 647.
35. Evaluation từ 646.
36. Distributed execution từ 630.
37. Persistence từ 600/611/612.
38. Events từ 634.
39. Observability từ 633.
40. No mandatory external simulation engine.

---

# 4. Core concepts

```text
Simulation
SimulationId
SimulationGeneration
SimulationRevision

World
WorldId
WorldVersion

Environment
EnvironmentId
EnvironmentVersion

Entity
EntityId
EntityType

EnvironmentState
StateSnapshot
StateDelta

Scenario
ScenarioId
ScenarioVersion

ScenarioGenerator
ScenarioSeed

SimulationClock
SimulationStep
SimulationTick

Action
ActionSpace
Observation
ObservationSpace

Reward
Transition

Sensor
SensorModel
SensorObservation

PhysicsWorld
PhysicsProvider

Renderer
RenderProvider

SyntheticDataset
SyntheticSample
SyntheticArtifact

SimulationRun
SimulationEpisode
EpisodeId
Trajectory

AgentInstance
AgentPolicy

SimulationCheckpoint

Replay
ReplayArtifact

DigitalTwin
TwinId
TwinVersion

Sandbox
SandboxPolicy

SimulationMetric
SimulationEvent
```

---

# 5. Simulation identity

```text
SimulationId
+
Generation
```

xác định một simulation logical identity.

---

# 6. Simulation version

Mỗi immutable simulation definition có:

```text
SimulationVersion
WorldVersion
EnvironmentVersion
ScenarioVersion
AgentVersion
```

---

# 7. Simulation run

Mỗi execution:

```text
SimulationRunId
```

là immutable identity.

---

# 8. Episode

Một run có thể chứa nhiều episode:

```text
Run
 ├── Episode 0
 ├── Episode 1
 ├── Episode 2
 └── ...
```

---

# 9. Tick

Simulation được điều khiển bằng integer tick:

```text
SimulationTick : u64
```

không dùng floating-point làm identity thời gian.

---

# 10. Simulation time

```text
SimulationTime {
    tick
    timestep
    timescale
}
```

---

# 11. Fixed timestep

Deterministic simulation ưu tiên:

```text
dt = constant
```

---

# 12. Variable timestep

Có thể hỗ trợ provider-specific variable timestep.

Phải ghi rõ trong metadata.

---

# 13. Wall clock

Wall-clock chỉ được phép qua explicit service.

---

# 14. Deterministic mode

```text
Deterministic
```

yêu cầu:

- fixed seed;
- fixed timestep;
- deterministic scheduling policy;
- deterministic reduction;
- deterministic random stream;
- deterministic provider.

---

# 15. Determinism level

```text
BitExact
NumericallyDeterministic
SeedDeterministic
BestEffort
NonDeterministic
```

---

# 16. Randomness

Core random source:

```text
SimulationRng
```

---

# 17. Random stream

Mỗi subsystem có thể có stream riêng:

```text
world_rng
physics_rng
sensor_rng
scenario_rng
agent_rng
```

---

# 18. Random seed

Seed là một phần của run manifest.

---

# 19. Random stream derivation

Child stream được derive từ parent seed + stable subsystem identifier.

---

# 20. No global mutable RNG

Simulation không sử dụng global implicit RNG.

---

# 21. World

World mô tả universe mô phỏng.

Có thể gồm:

- entities;
- terrain;
- environment variables;
- resources;
- rules;
- sensors;
- physics.

---

# 22. World schema

```text
WorldSchema
```

mô tả entity/component/state types.

---

# 23. Entity

Simulation entity:

```text
EntityId
EntityGeneration
EntityType
```

---

# 24. Component model

Entity có thể chứa component:

```text
Transform
Velocity
Mass
Collider
Renderable
Sensor
Health
Inventory
Network
Custom
```

---

# 25. Struct-only entity model

Không yêu cầu class hierarchy.

---

# 26. Component storage

Có thể dùng:

- AoS;
- SoA;
- sparse sets;
- archetypes.

Provider lựa chọn layout.

---

# 27. State

Environment state là dữ liệu explicit.

---

# 28. State snapshot

Snapshot chứa state tại tick:

```text
StateSnapshot {
    tick
    state_hash
    world_revision
}
```

---

# 29. State delta

Có thể lưu delta giữa snapshots.

---

# 30. Copy-on-write

Checkpoint có thể dùng COW.

---

# 31. State hash

Mỗi deterministic checkpoint có thể có state hash.

---

# 32. State equivalence

Hai runs có thể so sánh state hash tại cùng tick.

---

# 33. Scenario

Scenario định nghĩa initial conditions + constraints + objectives.

---

# 34. Scenario example

```text
Scenario {
    world
    initial_state
    agents
    goals
    constraints
    seed
    duration
}
```

---

# 35. Scenario version

Scenario immutable sau khi published.

---

# 36. Scenario generator

Generator tạo nhiều scenarios từ template.

---

# 37. Scenario generation

Các chiến lược:

```text
Fixed
Random
Grid
LatinHypercube
MonteCarlo
Adversarial
BoundaryFocused
Mutation
ReplayDerived
```

---

# 38. Scenario bounds

Generator phải có:

- max scenarios;
- max depth;
- max state size;
- max generation time.

---

# 39. Scenario validity

Generated scenario phải qua validator trước execution.

---

# 40. Invalid scenario

Không được silently execute scenario invalid.

---

# 41. Scenario coverage

Generator có thể target:

- state coverage;
- action coverage;
- transition coverage;
- parameter coverage;
- edge cases.

---

# 42. Coverage metadata

Coverage là metric, không phải guarantee.

---

# 43. Environment

Environment cung cấp dynamics:

```text
reset()
step(action)
observe()
```

nhưng native API typed hơn.

---

# 44. Environment interface

```text
Environment {
    reset()
    step()
    observe()
    snapshot()
    restore()
}
```

---

# 45. Typed action

```text
Action<T>
```

---

# 46. Action space

```text
Discrete
Continuous
MultiDiscrete
MultiContinuous
Tuple
Struct
Graph
Custom
```

---

# 47. Observation space

```text
Scalar
Vector
Tensor
Image
Audio
Video
Text
Structured
Graph
Multimodal
```

---

# 48. Observation

Observation phải có timestamp/tick.

---

# 49. Observation provenance

Có thể ghi:

```text
sensor
entity
tick
provider
noise_model
```

---

# 50. Transition

```text
Transition {
    state_before
    action
    state_after
    observation
    reward
    terminated
    truncated
}
```

---

# 51. Reward

Reward là domain-defined.

Không có universal reward semantics.

---

# 52. Termination

Phân biệt:

```text
Success
Failure
Timeout
ConstraintViolation
EnvironmentEnded
AgentStopped
ResourceExceeded
```

---

# 53. Environment error

Environment error khác episode failure.

---

# 54. Action validation

Environment kiểm tra action trước khi apply.

---

# 55. Invalid action policies

```text
Reject
Clamp
Project
Terminate
Ignore
CustomProvider
```

Phải explicit.

---

# 56. Environment constraints

Có thể khai báo:

```text
max_velocity
max_energy
allowed_regions
collision_rules
```

---

# 57. Constraint violation

Được ghi thành simulation event.

---

# 58. Physics boundary

Physics không thuộc core semantic runtime.

---

# 59. Physics provider

```text
NativePhysicsProvider
RigidBodyProvider
ExternalPhysicsProvider
TestPhysicsProvider
```

---

# 60. Physics capabilities

Provider có thể hỗ trợ:

- rigid body;
- collision;
- joints;
- fluids;
- particles;
- soft bodies;
- vehicles.

---

# 61. Physics determinism

Provider phải khai báo determinism level.

---

# 62. Physics state

Physics state phải snapshotable nếu provider hỗ trợ deterministic replay.

---

# 63. Physics checkpoint

Nếu không snapshotable:

```text
CheckpointSupport = None
```

---

# 64. Rendering boundary

Rendering dùng 615.

---

# 65. Renderer

```text
SimulationRenderer
```

có thể tạo:

- RGB;
- depth;
- segmentation;
- normals;
- optical flow;
- bounding boxes.

---

# 66. Synthetic camera

Camera simulation có:

```text
position
rotation
fov
resolution
intrinsics
extrinsics
distortion
```

---

# 67. Sensor model

```text
SensorModel {
    latency
    noise
    dropout
    quantization
    bias
}
```

---

# 68. Sensor types

```text
Camera
Depth
LiDAR
Radar
GPS
IMU
Microphone
Temperature
Pressure
Proximity
Custom
```

---

# 69. Sensor noise

Noise model phải seedable trong deterministic mode.

---

# 70. Sensor latency

Latency được biểu diễn bằng simulation ticks.

---

# 71. Sensor dropout

Có thể mô phỏng missing observations.

---

# 72. Sensor corruption

Có thể tạo controlled corruption cho robustness testing.

---

# 73. Synthetic media

616/615 có thể tạo:

- audio;
- image;
- video;
- depth;
- multimodal streams.

---

# 74. Synthetic text

617 có thể tạo structured textual observations.

---

# 75. Synthetic dataset

```text
SyntheticDataset {
    schema
    samples
    provenance
    generator
    seed
}
```

---

# 76. Synthetic sample

Mỗi sample có:

```text
sample_id
scenario_id
episode_id
tick
source_state
observation
label
```

---

# 77. Synthetic provenance

Synthetic data phải ghi rõ:

```text
Synthetic
```

không được masquerade thành real-world observation.

---

# 78. Synthetic lineage

640 quản lý lineage.

---

# 79. Dataset export

Có thể export sang 612/642-compatible format.

---

# 80. Streaming dataset

Synthetic generator có thể stream trực tiếp vào 643 training.

---

# 81. Online generation

```text
Generator
→ Environment
→ Observation
→ DatasetSink
```

---

# 82. Backpressure

Synthetic generation phải obey 606/607 quotas.

---

# 83. Dataset balancing

Generator có thể target:

- class balance;
- scenario balance;
- difficulty distribution.

Kết quả thực tế phải được đo, không giả định.

---

# 84. Domain randomization

Randomize:

- lighting;
- textures;
- geometry;
- noise;
- dynamics;
- sensor properties.

---

# 85. Domain randomization bounds

Parameters phải nằm trong declared range.

---

# 86. Counterfactual simulation

Có thể clone state tại tick:

```text
S_t
```

sau đó chạy:

```text
Action A
Action B
```

độc lập.

---

# 87. Counterfactual identity

Mỗi branch có:

```text
ParentRunId
ParentTick
BranchId
```

---

# 88. Branching

Simulation state sử dụng snapshot/COW khi có thể.

---

# 89. Monte Carlo

Có thể chạy N independent seeds.

---

# 90. Monte Carlo result

Kết quả chứa:

```text
sample_count
seed_range
distribution
uncertainty
```

---

# 91. Statistical aggregation

642 có thể aggregate large simulation outputs.

---

# 92. Confidence intervals

646 có thể evaluate statistical uncertainty.

---

# 93. Simulation does not decide model quality

Simulation generates evidence.

646 evaluates evidence.

---

# 94. Agent sandbox

644 agent chạy trong:

```text
SimulationSandbox
```

---

# 95. Sandbox capability

Agent chỉ có capabilities được cấp:

```text
Observe
Act
QueryEnvironment
UseTool
AccessMemory
EmitEvent
```

---

# 96. No implicit host access

Simulation agent không có quyền:

- host filesystem;
- host network;
- host process;
- host device.

trừ capability explicit.

---

# 97. Tool sandbox

Tools có thể được mocked.

---

# 98. Tool simulation

```text
SimulatedTool
```

mô phỏng:

- latency;
- failure;
- malformed response;
- timeout;
- rate limit.

---

# 99. Tool fault injection

Có thể inject deterministic faults.

---

# 100. Prompt/environment injection

Synthetic environment có thể cung cấp adversarial observations để 646 đánh giá agent.

---

# 101. Agent trajectory

Trajectory:

```text
Observation
→ ReasoningBoundary
→ ToolCall
→ ToolResult
→ Action
→ Observation
```

Không yêu cầu lưu hidden chain-of-thought.

Chỉ lưu structured execution events.

---

# 102. Agent privacy

Simulation không tự động lưu private model reasoning.

---

# 103. Tool call record

Có:

```text
tool_id
input_hash
result_hash
latency
status
capability
```

---

# 104. Agent action record

Có:

```text
action_id
action_type
parameters
tick
result
```

---

# 105. Action parameter privacy

Sensitive values có thể được redacted/hash.

---

# 106. Closed-loop execution

```text
Agent
 ↓
Observe
 ↓
Plan
 ↓
Act
 ↓
Environment
 ↓
Transition
 ↓
Observe
```

---

# 107. Loop bounds

Simulation run có:

```text
max_ticks
max_actions
max_tool_calls
max_tokens
max_memory
max_compute
```

---

# 108. Infinite-loop prevention

Một agent loop không được chạy vô hạn.

---

# 109. Stagnation detection

Có thể phát hiện:

- repeated state;
- repeated action;
- no-progress;
- oscillation.

---

# 110. Stagnation result

```text
Stalled
```

là explicit termination reason.

---

# 111. Agent reset

Environment có thể reset agent state.

---

# 112. Episode reset

Reset phải xác định rõ:

```text
environment only
agent only
both
```

---

# 113. Multi-agent simulation

Multiple agents có:

```text
AgentId
AgentGeneration
AgentRole
```

---

# 114. Multi-agent communication

Có thể dùng 634/604 abstractions.

---

# 115. Communication latency

Simulation có thể model latency bằng simulation ticks.

---

# 116. Communication loss

Có thể mô phỏng packet loss.

---

# 117. Network simulation

609/631 có provider boundary.

---

# 118. Network topology

Scenario có thể mô tả:

```text
nodes
links
bandwidth
latency
loss
partition
```

---

# 119. Distributed simulation

630 chạy simulation episodes song song.

---

# 120. Placement

635 đặt simulation workers.

---

# 121. Simulation scheduler

607 điều phối local execution.

---

# 122. Large-scale simulation

```text
Simulation
→ Episode Queue
→ Worker Pool
→ Results
```

---

# 123. Worker identity

Simulation worker có generation-safe ID.

---

# 124. Episode lease

Mỗi episode có lease để tránh duplicate execution.

---

# 125. Duplicate execution

Nếu xảy ra, episode identity + seed cho phép dedup.

---

# 126. Checkpoint

Long simulation được checkpoint.

---

# 127. Checkpoint contents

```text
world state
agent state
environment state
simulation tick
random streams
scenario revision
model version
tool versions
```

---

# 128. Checkpoint compatibility

Restore yêu cầu compatible environment/model versions.

---

# 129. Checkpoint migration

Migration explicit.

---

# 130. Replay

Replay sử dụng:

```text
scenario
seed
action trace
environment version
```

---

# 131. Replay modes

```text
Exact
Deterministic
Visual
TraceOnly
```

---

# 132. Trace-only replay

Không cần re-run physics nếu chỉ phân tích trajectory.

---

# 133. Simulation recording

Recording có:

```text
state snapshots
events
actions
observations
metrics
```

---

# 134. Event log

634 có thể lưu simulation events.

---

# 135. Simulation event types

```text
EpisodeStarted
ActionApplied
ObservationProduced
Collision
ConstraintViolation
ToolCalled
ToolFailed
AgentStalled
CheckpointCreated
EpisodeEnded
```

---

# 136. Simulation metrics

```text
episode_length
reward
success_rate
collision_count
constraint_violations
latency
energy
tool_calls
```

---

# 137. Evaluation integration

646 nhận:

```text
SimulationRun
Trajectory
SyntheticDataset
```

---

# 138. Benchmark integration

Simulation scenarios có thể trở thành benchmark suite.

---

# 139. Regression testing

Known scenarios được replay sau compiler/runtime/model changes.

---

# 140. Golden run

Một run có thể trở thành baseline artifact.

---

# 141. Golden state

Golden state hash tại checkpoint.

---

# 142. Golden trajectory

Golden action/observation sequence.

---

# 143. Numerical tolerance

Floating-point simulation có thể sử dụng tolerance.

---

# 144. Deterministic comparison

Comparison policy:

```text
Exact
AbsoluteTolerance
RelativeTolerance
ULPTolerance
MetricTolerance
```

---

# 145. Simulation regression

646 đánh giá regression.

---

# 146. Environment regression

Provider/environment changes phải có compatibility revision.

---

# 147. Physics regression

Physics output có thể được benchmark.

---

# 148. Sensor regression

Sensor distributions có thể được compared.

---

# 149. Rendering regression

Rendered output có thể được compared bằng image metrics từ 646.

---

# 150. Audio regression

616 output có thể được evaluated bởi 646.

---

# 151. Multimodal regression

Cross-modal outputs có thể được compared.

---

# 152. Digital twin

Digital twin mô hình hóa một physical/logical entity.

---

# 153. Twin identity

```text
TwinId
TwinVersion
PhysicalEntityRef
```

---

# 154. Twin state

Twin có:

```text
ObservedState
SimulatedState
EstimatedState
```

---

# 155. State distinction

Không được coi simulated state là observed state.

---

# 156. Twin synchronization

Physical telemetry có thể cập nhật twin.

---

# 157. Telemetry

633/616/614 cung cấp observation.

---

# 158. Twin reconciliation

Difference:

```text
Observed - Simulated
```

được ghi nhận.

---

# 159. Twin calibration

Calibration parameters có version.

---

# 160. Twin history

State revisions có timestamp + simulation tick nếu applicable.

---

# 161. Twin prediction

Prediction is provider/model output, not guaranteed truth.

---

# 162. Twin safety

Digital twin cannot directly actuate physical device without explicit capability and policy.

---

# 163. Sim-to-real

Model trained/evaluated in simulation can record:

```text
SimulationEvidence
```

---

# 164. Real-world validation

646 can compare simulation and real datasets.

---

# 165. Domain gap

Metrics can describe simulation-real divergence.

---

# 166. No automatic equivalence

Simulation is never assumed equivalent to reality.

---

# 167. Synthetic-to-real governance

640 records synthetic lineage.

---

# 168. Synthetic data classification

Synthetic data can inherit restrictions from generator/input data.

---

# 169. Sensitive synthetic data

Synthetic output may still contain sensitive information.

---

# 170. Privacy validation

646 can test synthetic leakage.

---

# 171. Scenario privacy

Scenario parameters can be governed by 640.

---

# 172. Secret protection

Secrets cannot be injected into scenarios unless explicitly capability-controlled.

---

# 173. Simulation package

Native:

```text
.axsim
```

---

# 174. Scenario package

```text
.axscenario
```

---

# 175. Environment package

```text
.axenv
```

---

# 176. Synthetic dataset metadata

```text
.axsynthetic
```

---

# 177. Replay artifact

```text
.axreplay
```

---

# 178. Twin metadata

```text
.axtwin
```

---

# 179. Simulation manifest

Contains:

```text
simulation_version
world_version
environment_version
scenario_version
agent_versions
model_versions
provider_versions
seed
determinism_level
resource_policy
```

---

# 180. Compiler annotations

```text
@simulation
@world
@environment
@scenario
@generator
@episode
@action
@observation
@reward
@sensor
@physics
@renderer
@synthetic
@digital_twin
@replay
@checkpoint
@deterministic
@seed
@sandbox
@fault_injection
@closed_loop
```

---

# 181. Generated artifacts

```text
.axsim
.axworld
.axenv
.axscenario
.axsynthetic
.axreplay
.axtwin
.axsimmanifest
```

---

# 182. Struct-only API

```text
Simulation
World
Environment
Scenario
SimulationRun
Episode
Action
Observation
Transition
Sensor
SensorModel
PhysicsWorld
SimulationClock
SimulationRng
Sandbox
DigitalTwin
Replay
Checkpoint
SyntheticDataset
```

---

# 183. Example

```text
sim = Simulation.create(
    environment,
    scenario
)

run = sim.run(agent)

result = run.evaluate()
```

---

# 184. Deterministic example

```text
scenario.seed = 42
scenario.timestep = 0.01

run = simulation.run(
    deterministic = true
)
```

---

# 185. Counterfactual example

```text
branch_a = run.branch(tick, action_a)
branch_b = run.branch(tick, action_b)
```

---

# 186. Synthetic generation

```text
dataset = scenario.generate(
    count = 10000
)
```

---

# 187. Replay

```text
replay = Simulation.replay(
    run.artifact
)
```

---

# 188. Digital twin

```text
twin = DigitalTwin.create(
    physical_entity
)
```

---

# 189. Sandbox

```text
sandbox = SimulationSandbox.create(
    policy
)

sandbox.attach(agent)
```

---

# 190. Fault injection

```text
scenario.fault(
    SensorDropout(...)
)
```

---

# 191. Fault classes

```text
SensorFault
NetworkFault
ToolFault
LatencyFault
ResourceFault
EnvironmentFault
ProviderFault
DataCorruption
PartialObservation
```

---

# 192. Fault injection safety

Faults chỉ tác động simulation sandbox.

---

# 193. No real-world propagation

Simulation fault injection không được tự động truyền sang production.

---

# 194. Scenario mutation

646/648 có thể mutate existing scenario.

---

# 195. Mutation bounds

Mutation phải obey schema/range.

---

# 196. Adversarial scenario

Adversarial scenario tìm boundary conditions.

Không được hiểu là unrestricted real-world attack automation.

---

# 197. Safety scenario

Safety tests có thể mô phỏng:

- constraint violation;
- sensor failure;
- malformed input;
- tool failure;
- policy denial;
- resource exhaustion.

---

# 198. Agent red-team

644 + 646 + 648:

```text
Scenario
→ Agent
→ Sandbox
→ Fault
→ Trajectory
→ Evaluation
```

---

# 199. Closed-loop red-team

Run phải bounded bởi resource policy.

---

# 200. Prompt injection simulation

Environment có thể cung cấp controlled untrusted text.

Agent phải xử lý theo policy.

---

# 201. Tool injection simulation

Tool result có thể chứa controlled malicious-looking content.

Không được cấp additional capability.

---

# 202. Privilege escalation test

Simulation có thể kiểm tra agent attempts vượt capability.

---

# 203. Exfiltration test

Synthetic secrets có thể dùng trong sandbox để kiểm tra policy boundary.

---

# 204. Secret safety

Real production secrets không được đưa vào simulation chỉ để test.

---

# 205. Model robustness

Scenario generator có thể test:

- missing data;
- noise;
- corruption;
- distribution shift;
- edge values.

---

# 206. Multimodal robustness

Có thể perturb:

- text;
- image;
- audio;
- video;
- sensor streams.

---

# 207. Temporal robustness

Test:

- delayed observations;
- out-of-order events;
- stale state;
- clock drift.

---

# 208. Distributed robustness

Test:

- network partition;
- worker loss;
- message duplication;
- delay;
- reordering.

---

# 209. Failure injection

630/635 can inject simulated worker/node failures.

---

# 210. Cluster simulation

648 can create virtual cluster topology.

---

# 211. Virtual nodes

```text
SimNode
SimService
SimNetwork
SimStorage
```

---

# 212. Control-plane simulation

635 behavior can be evaluated in simulated cluster.

---

# 213. Deployment simulation

636 deployment plans can be dry-run against simulated environment.

---

# 214. Gateway simulation

632 policies can be tested using simulated traffic.

---

# 215. Event simulation

634 topics/events can be simulated.

---

# 216. Workflow simulation

629 workflows can execute against simulated clocks/services.

---

# 217. Full-stack simulation

```text
636 Deployment
 ↓
631 Service
 ↓
632 Gateway
 ↓
634 Event
 ↓
629 Workflow
 ↓
644 Agent
 ↓
648 Environment
```

---

# 218. Simulation orchestration

630 handles large parallel runs.

---

# 219. Episode scheduling

Jobs can be distributed based on:

- CPU;
- GPU;
- memory;
- locality.

---

# 220. GPU simulation

614/615/643 providers may accelerate simulation.

---

# 221. Physics GPU

Provider may use GPU physics.

---

# 222. Synthetic rendering GPU

615 can render observations.

---

# 223. Batch simulation

Multiple environments can execute in parallel.

---

# 224. Vectorized environments

```text
EnvironmentBatch<N>
```

---

# 225. Batched state

State can be represented as tensors through 643.

---

# 226. SIMD simulation

Deterministic vectorized operations are supported where provider allows.

---

# 227. GPU nondeterminism

Provider must expose determinism level.

---

# 228. Memory management

648 uses explicit buffers/arenas/pools.

No mandatory GC.

---

# 229. Resource governance

606 controls:

- simulation count;
- episodes;
- memory;
- CPU;
- GPU;
- disk;
- network.

---

# 230. Time budget

Each simulation has execution deadline.

---

# 231. Episode budget

Can limit:

```text
ticks
actions
observations
tool calls
```

---

# 232. Storage budget

Replay/checkpoint artifacts have quota.

---

# 233. Security

603 capabilities:

```text
SimulationCreate
SimulationRun
SimulationRead
SimulationWrite
ScenarioGenerate
SyntheticExport
TwinRead
TwinUpdate
```

---

# 234. Physical actuation

Digital twin actuation requires separate device capability.

Simulation capability cannot grant it.

---

# 235. Policy

639 can enforce:

```text
simulation allowed
synthetic export allowed
scenario complexity
resource limit
data residency
```

---

# 236. Governance

640 tracks:

```text
input datasets
synthetic datasets
simulation outputs
digital twin data
```

---

# 237. Observability

633 metrics:

```text
simulation_rate
episode_rate
step_latency
reset_latency
checkpoint_latency
replay_rate
worker_utilization
```

---

# 238. Diagnostics

602 captures:

- simulation failures;
- provider errors;
- determinism mismatch;
- checkpoint corruption;
- invalid scenario.

---

# 239. Event integration

634 events:

```text
SimulationStarted
SimulationCompleted
EpisodeStarted
EpisodeCompleted
ScenarioGenerated
CheckpointCreated
ReplayCompleted
```

---

# 240. Storage

611 stores large artifacts.

---

# 241. Serialization

612 serializes:

- scenarios;
- state;
- replay;
- manifests.

---

# 242. Package

613/625 distribute:

- environment;
- scenarios;
- assets;
- models.

---

# 243. Graphics

615 provides rendering.

---

# 244. Media

616 provides audio/video sensors.

---

# 245. Text

617 provides textual observation normalization.

---

# 246. Search

641 indexes scenarios and results.

---

# 247. Analytics

642 aggregates simulation outcomes.

---

# 248. Knowledge graph

645 can represent:

```text
Scenario
→ Model
→ Dataset
→ Environment
→ Evaluation
```

---

# 249. Model lifecycle

647 tracks exact model versions used by simulations.

---

# 250. Evaluation

646 evaluates simulation evidence.

---

# 251. Agent

644 provides agent execution.

---

# 252. Training

643 can consume generated trajectories.

---

# 253. Offline RL boundary

648 can generate:

```text
state
action
reward
next_state
done
```

for 643 training.

---

# 254. Online training boundary

Agent/model may update between episodes.

Training lifecycle remains owned by 643/647.

---

# 255. Model-in-the-loop

```text
Simulation
 ↔
InferenceSession
```

---

# 256. Hardware-in-the-loop

Provider can connect simulated environment to selected real devices through explicit capabilities.

---

# 257. Hardware safety

HIL cannot silently control physical hardware.

---

# 258. Software-in-the-loop

Default simulation mode.

---

# 259. Human-in-the-loop

Human input can enter through 618/619.

---

# 260. Human intervention

Intervention is recorded as explicit event.

---

# 261. Human approval

646/639 can require approval before scenario progression.

---

# 262. Interactive simulation

619/615 can visualize state.

---

# 263. Headless simulation

Default for large batch evaluation.

---

# 264. Remote visualization

Optional 631/632 streaming.

---

# 265. Simulation UI

Axiom GUI may expose:

```text
world view
timeline
state inspector
entity inspector
event log
metrics
replay controls
```

---

# 266. Time travel debugging

Replay can jump to checkpoint.

---

# 267. State inspection

Read-only by default.

---

# 268. State mutation during debugging

Requires explicit debug capability.

---

# 269. Debug mutation

Never modifies original immutable run.

Creates branch.

---

# 270. Simulation branch

Branch identity references parent checkpoint.

---

# 271. Branch merge

Generally prohibited for physical simulation state unless provider defines a valid merge.

---

# 272. Scenario merge

Scenario definitions may use version-control style merge.

---

# 273. Environment versioning

Provider changes create new environment revision.

---

# 274. Physics provider version

Recorded in manifest.

---

# 275. Renderer version

Recorded if rendered output matters.

---

# 276. Sensor provider version

Recorded.

---

# 277. Simulation ABI

Environment interface has ABI fingerprint.

---

# 278. Scenario schema fingerprint

Stored in run manifest.

---

# 279. Model fingerprint

647 ModelVersion + ArtifactHash recorded.

---

# 280. Agent fingerprint

644 AgentVersion recorded.

---

# 281. Tool fingerprint

Tool version/schema recorded.

---

# 282. Full reproducibility manifest

```text
Simulation
World
Environment
Scenario
Agent
Model
Tools
Providers
Compiler
Seed
Resources
```

---

# 283. Reproducibility score

Do not collapse into one universal score.

Expose individual reproducibility dimensions.

---

# 284. Simulation comparison

Compare runs by:

```text
state
trajectory
metrics
events
rendering
resource use
```

---

# 285. Diff

Native:

```text
SimulationDiff
```

---

# 286. Difference types

```text
StateDifference
ActionDifference
ObservationDifference
TimingDifference
MetricDifference
EventDifference
```

---

# 287. Numerical comparison

646 defines tolerance.

---

# 288. Visualization

615 renders simulation state.

---

# 289. Export

Possible:

```text
AXSIM
JSON
AXBIN
CSV
Parquet-compatible provider
video
images
audio
```

---

# 290. Import

External simulation traces require schema validation.

---

# 291. Import trust

Imported traces are untrusted data.

---

# 292. Synthetic dataset signing

Generated dataset may be signed for provenance.

---

# 293. Dataset identity

Synthetic dataset gets immutable revision.

---

# 294. Dataset lineage

Generator + seed + scenario revision are recorded.

---

# 295. Scenario corpus

Large benchmark corpus can be versioned.

---

# 296. Benchmark corpus

646 can consume corpus revisions.

---

# 297. Regression corpus

Known failures can become permanent scenarios.

---

# 298. Failure corpus

```text
FailureScenario
```

stores:

- triggering conditions;
- environment;
- model;
- agent;
- expected safety behavior.

---

# 299. Reproduction

A failure scenario must be reproducible where provider permits.

---

# 300. Flaky simulation

If same seed produces divergent result unexpectedly:

```text
DeterminismViolation
```

---

# 301. Determinism detector

Compare:

```text
state hash
event sequence
metric outputs
```

---

# 302. Determinism diagnosis

Diagnostics can identify first divergent tick.

---

# 303. First divergence

Replay compares checkpoint hashes until divergence.

---

# 304. Provider fault

If provider is nondeterministic by design, divergence is expected and recorded.

---

# 305. Simulation fault

Unexpected divergence is diagnostic failure.

---

# 306. Numerical drift

Floating-point drift may be tolerated according to comparison policy.

---

# 307. Scenario seed reproducibility

Same scenario seed must produce same generated scenario under deterministic generator version.

---

# 308. Generator version

Generator implementation has immutable version.

---

# 309. Generator artifact

Generator executable/provider identity recorded.

---

# 310. Synthetic generator security

Generator code cannot execute arbitrary host operations without capability.

---

# 311. Sandboxed generators

Preferred for untrusted scenario generators.

---

# 312. Script integration

624 may provide scenario DSL.

Scripts are sandboxed.

---

# 313. No arbitrary simulation code

Declarative scenario definitions remain preferred.

---

# 314. Custom environment

Custom environment may be native Axiom code.

It requires normal compiler/security controls.

---

# 315. Provider ABI

Environment providers use stable ABI.

---

# 316. External simulator adapter

External simulator runs outside Axiom process when required.

---

# 317. Adapter sandbox

External provider receives only declared capabilities.

---

# 318. Provider failure

Failure is explicit:

```text
ProviderUnavailable
ProviderCrash
ProviderProtocolError
ProviderTimeout
```

---

# 319. Simulation cancellation

Cancellation propagates:

```text
run
→ episode
→ environment
→ provider
```

---

# 320. Graceful stop

Simulation stops at safe checkpoint where possible.

---

# 321. Forced stop

Resource governor can terminate simulation worker.

---

# 322. Recovery

Incomplete episode can resume from checkpoint.

---

# 323. Exactly-once

Distributed simulation does not assume exactly-once execution.

---

# 324. Episode idempotency

Episode result is keyed by immutable:

```text
RunId + EpisodeId + Attempt
```

---

# 325. Duplicate attempts

Only one canonical result can be committed according to run policy.

---

# 326. Worker failure

Episode lease expires and can be reassigned.

---

# 327. Result conflict

Conflicting results require explicit policy.

---

# 328. Result retention

646/640 govern evidence retention.

---

# 329. Privacy

Simulation output may contain sensitive synthetic or derived information.

---

# 330. Redaction

Export can apply governance-controlled redaction.

---

# 331. Residency

Simulation artifacts follow 640 residency policy.

---

# 332. Multi-tenant

Simulation state isolated by tenant.

---

# 333. Cross-tenant scenarios

Denied by default.

---

# 334. Resource fairness

606 enforces tenant quotas.

---

# 335. Priority

Simulation priority cannot bypass security/resource hard limits.

---

# 336. Scheduling

607 schedules local tasks.

630 schedules distributed jobs.

---

# 337. Autoscaling

636/635 may scale simulation workers.

---

# 338. Cost metadata

Simulation records CPU/GPU/storage/network usage.

---

# 339. Cost analysis

642 can aggregate resource cost.

---

# 340. Simulation catalog

641 can index:

```text
scenario
environment
agent
model
result
```

---

# 341. Knowledge graph

645 can establish:

```text
Scenario
uses Model
uses Environment
produces Dataset
validated by Evaluation
```

---

# 342. Agent memory

644 may store selected simulation results as memory.

---

# 343. Memory provenance

Memory derived from simulation must reference run/evidence.

---

# 344. No synthetic fact promotion

Simulation result cannot automatically become real-world knowledge.

---

# 345. Digital twin distinction

Twin state is a model of a real entity, not guaranteed ground truth.

---

# 346. Confidence

Twin estimates may carry uncertainty metadata.

---

# 347. State estimation

643 can provide learned state estimator.

---

# 348. Estimator lineage

Estimator model version recorded.

---

# 349. Twin model update

Updating twin model creates new twin revision.

---

# 350. Twin synchronization conflicts

Observed state has precedence only according to declared domain policy.

---

# 351. Simulation environment configuration

601/637 manage configuration.

---

# 352. Dynamic simulation policy

637 may change non-safety operational parameters.

---

# 353. Safety boundary

639/603 constraints cannot be weakened by ordinary feature flags.

---

# 354. Simulation policy

Example:

```text
max_episode_ticks = 10000
allow_external_network = false
allow_physical_device = false
```

---

# 355. Policy fingerprint

Run records policy revision/fingerprint.

---

# 356. Configuration fingerprint

Run records config fingerprint.

---

# 357. Security fingerprint

Run records security policy fingerprint.

---

# 358. Full run fingerprint

```text
simulation
scenario
agent
model
policy
config
providers
```

---

# 359. Simulation API error model

```text
SimulationError
InvalidScenario
InvalidAction
InvalidObservation
EnvironmentFailure
ProviderFailure
PhysicsFailure
RendererFailure
DeterminismViolation
CheckpointFailure
ReplayFailure
ResourceExceeded
Timeout
Cancelled
CapabilityDenied
PolicyDenied
GovernanceViolation
SchemaMismatch
VersionMismatch
StateCorruption
```

---

# 360. Testing

648 itself must use simulation to test simulation components where possible.

---

# 361. Unit tests

Test:

- clock;
- RNG;
- state;
- actions;
- transitions;
- scenario validation.

---

# 362. Property tests

Examples:

```text
reset -> initial state
snapshot -> restore equivalence
seed -> deterministic generation
branch -> parent checkpoint equivalence
```

---

# 363. Fuzzing

Fuzz:

- scenarios;
- actions;
- observations;
- manifests;
- replay files;
- provider messages.

---

# 364. Fault injection

Test:

- worker crash;
- provider crash;
- disk full;
- network partition;
- checkpoint corruption;
- malformed observation.

---

# 365. Chaos simulation

630/635 can simulate cluster failures.

---

# 366. Security testing

603/639 test:

- capability escape;
- sandbox escape;
- unauthorized physical access;
- secret leakage;
- policy bypass.

---

# 367. Reproducibility tests

Repeated deterministic run must match expected identity/state hash.

---

# 368. Performance tests

Measure:

- ticks/sec;
- episode/sec;
- observation latency;
- memory/tick;
- GPU utilization;
- checkpoint throughput.

---

# 369. Scalability tests

Measure worker scaling.

---

# 370. Batch efficiency

Compare vectorized environment throughput.

---

# 371. Storage efficiency

Measure snapshot/delta compression.

---

# 372. Rendering performance

615 metrics.

---

# 373. Media performance

616 metrics.

---

# 374. AI inference performance

643 metrics.

---

# 375. End-to-end latency

633 traces complete loop:

```text
observe
→ agent
→ action
→ environment
→ observation
```

---

# 376. AI evaluation loop

```text
648 Simulation
 ↓
643 Model/Agent
 ↓
648 Environment
 ↓
646 Evaluation
 ↓
647 Model lifecycle
```

---

# 377. Continuous regression

636 deployment can require simulation suite before rollout.

---

# 378. Deployment gate

639 can require:

```text simulation_suite_passed
```

---

# 379. Simulation gate evidence

646 stores exact:

```text simulation_version
scenario_revision
model_version
run_id
evaluation_revision
```

---

# 380. Model promotion

647 can consume simulation evaluation evidence.

---

# 381. Closed-loop model lifecycle

```text
Train
→ Simulate
→ Evaluate
→ Promote
→ Deploy
→ Observe
→ Simulate again
```

---

# 382. Continuous validation

633 telemetry can generate scenarios for offline evaluation.

---

# 383. Production trace replay

Production traces must be sanitized/governed before simulation reuse.

---

# 384. Trace anonymization

640 controls.

---

# 385. Replay safety

Production trace replay runs in sandbox.

---

# 386. No production side effects

Replay cannot call production systems by default.

---

# 387. Production shadowing

632/631 may mirror requests into simulation only with explicit policy.

---

# 388. Synthetic user

Simulation can create virtual users.

---

# 389. Virtual traffic

632 can generate simulated HTTP traffic.

---

# 390. Virtual devices

614 provider can expose simulated devices.

---

# 391. Virtual storage

611 provider can expose simulated storage.

---

# 392. Virtual network

609 provider can simulate network conditions.

---

# 393. Virtual time

607 timers can use simulation clock provider.

---

# 394. Workflow virtual time

629 durable timers can execute against simulated clock.

---

# 395. Cluster virtual time

635 coordination tests can use deterministic scheduler.

---

# 396. Full system digital twin

648 can model:

```text
nodes
services
networks
storage
events
workflows
agents
models
devices
```

---

# 397. System-level simulation

Useful for testing architecture changes before deployment.

---

# 398. Simulation plan

```text
SimulationPlan {
    environment
    scenarios
    repetitions
    seed_policy
    resource_budget
    evaluation_suite
}
```

---

# 399. Simulation campaign

A campaign runs multiple simulations.

---

# 400. Campaign identity

```text
CampaignId
CampaignRevision
```

---

# 401. Campaign execution

Distributed via 630.

---

# 402. Campaign aggregation

642 aggregates results.

---

# 403. Campaign evaluation

646 evaluates campaign evidence.

---

# 404. Campaign lifecycle

```text
Draft
Prepared
Running
Paused
Completed
Failed
Cancelled
Archived
```

---

# 405. Campaign pause

Must preserve scheduling state.

---

# 406. Campaign resume

Uses checkpoint.

---

# 407. Campaign cancellation

Stops future episodes and optionally active workers.

---

# 408. Campaign reproducibility

Manifest includes all scenario generator revisions.

---

# 409. Campaign artifact

```text
.axcampaign
```

---

# 410. Simulation experiment

643/646 experiment metadata can reference campaign.

---

# 411. Knowledge graph integration

645 may represent campaign relationships.

---

# 412. Search integration

641 indexes campaign metadata.

---

# 413. Analytics integration

642 aggregates campaign metrics.

---

# 414. Model registry integration

647 identifies exact model versions.

---

# 415. Policy integration

639 evaluates whether campaign is allowed.

---

# 416. Governance integration

640 governs input/output datasets.

---

# 417. Security integration

603 controls environment/tool/device access.

---

# 418. Resource integration

606 limits campaign resources.

---

# 419. Observability

633 monitors campaign.

---

# 420. Diagnostics

602 records failures.

---

# 421. Package integration

625 distributes scenarios/environments.

---

# 422. Script integration

624 can generate scenario definitions.

---

# 423. Plugin integration

623 allows physics/render/sensor providers.

---

# 424. Plugin trust

623/638 trust rules apply.

---

# 425. Native provider priority

Core providers should minimize external dependencies.

---

# 426. External simulator bridge

Supported but never mandatory.

---

# 427. FFI boundary

Provider ABI explicitly versioned.

---

# 428. WASM

Simulation can execute inside WASM host with host-controlled capabilities.

---

# 429. Mobile

Simulation can run under resource-limited profile.

---

# 430. Embedded

Simulation may use deterministic fixed-memory mode.

---

# 431. Fixed-memory profile

No dynamic allocation after initialization where feasible.

---

# 432. Real-time simulation

Optional deadline-aware execution.

---

# 433. Real-time constraint

Simulation cannot claim real-time unless provider meets declared timing constraints.

---

# 434. Soft real-time

Metrics expose deadline misses.

---

# 435. Hard real-time

Only supported by suitable platform/provider profile.

---

# 436. Simulation quality metadata

Provider declares:

```text
accuracy
determinism
resolution
supported_features
```

---

# 437. Accuracy

Accuracy claims are metadata, not universal guarantee.

---

# 438. Physics validation

646 can compare simulation against reference datasets.

---

# 439. Sensor validation

Synthetic sensor distributions can be compared against measured data.

---

# 440. Domain validation

646 can calculate simulation-real metrics.

---

# 441. Synthetic data quality

Metrics can include:

- schema validity;
- distribution similarity;
- coverage;
- diversity;
- leakage;
- downstream task utility.

---

# 442. Synthetic data utility

646 evaluates whether synthetic data is useful for a specified task.

---

# 443. No universal synthetic-data quality score

Metrics remain task-specific.

---

# 444. Scenario difficulty

Can be represented descriptively:

```text
estimated_steps
constraint_count
state_space_size
```

Không biến thành universal difficulty score.

---

# 445. Agent difficulty

Evaluation remains in 646.

---

# 446. Simulation benchmark

Benchmark consists of:

```text
scenario corpus
environment version
evaluation suite
resource policy
```

---

# 447. Benchmark reproducibility

Exact versions are pinned.

---

# 448. Benchmark external compatibility

Can import/export benchmark schemas.

---

# 449. Benchmark licensing

Governed by 639/625.

---

# 450. Final invariants

1. Simulation identity immutable.
2. Run identity immutable.
3. Episode identity generation-safe.
4. Simulation time explicit.
5. Tick integer-based.
6. Randomness explicit.
7. Seed recorded.
8. RNG streams deterministic where promised.
9. World revision explicit.
10. Environment revision explicit.
11. Scenario revision explicit.
12. Agent version explicit.
13. Model version explicit.
14. Provider version explicit.
15. Action typed.
16. Observation typed.
17. Invalid actions explicit.
18. State explicit.
19. Snapshot immutable.
20. Checkpoint versioned.
21. Replay bounded.
22. Replay cannot exceed resource budget.
23. Scenario generation bounded.
24. Generated scenarios validated.
25. Synthetic data marked synthetic.
26. Synthetic lineage preserved.
27. Physics provider boundary explicit.
28. Renderer provider boundary explicit.
29. Sensor provider boundary explicit.
30. External simulator cannot expand capability.
31. Sandbox default deny.
32. Agent cannot acquire host capability.
33. Tool capability explicit.
34. Production side effects disabled by default.
35. HIL requires explicit authority.
36. Digital twin != physical truth.
37. Simulated state != observed state.
38. Counterfactual branch immutable.
39. Branch identity explicit.
40. Distributed episode execution idempotent.
41. Duplicate attempts identifiable.
42. Worker loss recoverable.
43. Checkpoint corruption detectable.
44. State hash deterministic where promised.
45. Provider nondeterminism declared.
46. Numerical tolerance explicit.
47. No hidden wall clock in deterministic mode.
48. No global RNG.
49. Resource budgets enforced.
50. Simulation cancellation bounded.
51. Security capabilities enforced.
52. Policy enforced.
53. Governance enforced.
54. Residency enforced.
55. Secrets excluded by default.
56. Production traces require governance before replay.
57. Simulation outputs carry provenance.
58. Model lineage preserved.
59. Evaluation references exact model version.
60. Deployment references exact release.
61. Simulation cannot promote models directly.
62. Evaluation owns quality judgments.
63. Registry owns model identity.
64. Deployment owns rollout.
65. Serving owns live execution.
66. Synthetic data cannot masquerade as observed data.
67. External providers cannot bypass trust.
68. Plugins cannot silently gain authority.
69. Scenario mutation creates new revision.
70. Environment changes create new revision.
71. Physics changes are versioned.
72. Sensor changes are versioned.
73. Rendering changes are versioned.
74. Campaign identity immutable.
75. Campaign configuration versioned.
76. Replay preserves provenance.
77. Fault injection is sandbox-only.
78. No arbitrary RCE from scenario data.
79. No mandatory external simulation engine.
80. No mandatory GC.
81. No raw pointer public API.
82. Struct-only API.
83. AI-generated scenarios are untrusted until validated.
84. AI-generated environment metadata is untrusted.
85. Agent cannot grant itself simulation capability.
86. Simulation state cannot grant physical-device authority.
87. Cross-tenant simulation access denied by default.
88. Federated simulation authority remains local.
89. Offline authority is scoped and expiring.
90. Registry/replay references are revision-bound.
91. Caches are revision-aware.
92. Archived artifacts remain immutable.
93. Deletion follows retention.
94. Tombstones prevent resurrection.
95. Audit records are append-only.
96. Simulation evidence is reproducible where provider permits.
97. Non-reproducibility is explicitly recorded.
98. Partial results are marked.
99. Failed episodes are not silently treated as successful.
100. Simulation quality claims remain evidence-based and scoped.

---

# 451. Acceptance target

**≥550 acceptance criteria** covering:

- simulation core;
- clock;
- deterministic execution;
- RNG;
- world;
- entities;
- components;
- state;
- snapshots;
- checkpoints;
- scenarios;
- scenario generation;
- validation;
- environment;
- action/observation;
- reward;
- transitions;
- physics;
- rendering;
- sensors;
- synthetic data;
- multimodal data;
- domain randomization;
- counterfactuals;
- Monte Carlo;
- agent sandbox;
- tool simulation;
- multi-agent;
- network simulation;
- distributed execution;
- worker recovery;
- digital twins;
- simulation-real comparison;
- replay;
- campaign;
- benchmark;
- regression;
- red-team sandbox;
- fault injection;
- security;
- governance;
- resource limits;
- storage;
- package;
- plugin;
- FFI;
- WASM;
- mobile;
- embedded;
- observability;
- diagnostics;
- event integration;
- AI training integration;
- evaluation integration;
- model registry integration;
- deployment integration;
- deterministic testing;
- fuzzing;
- crash recovery;
- performance;
- scalability.

---

# 452. Profiles

```text
AXSIM_NONE

AXSIM_CORE
AXSIM_WORLD
AXSIM_ENVIRONMENT
AXSIM_SCENARIO
AXSIM_DETERMINISTIC
AXSIM_REPLAY

AXSIM_SYNTHETIC
AXSIM_SENSOR
AXSIM_PHYSICS
AXSIM_RENDER
AXSIM_MULTIMODAL

AXSIM_AGENT
AXSIM_SANDBOX
AXSIM_MULTI_AGENT

AXSIM_DIGITAL_TWIN
AXSIM_COUNTERFACTUAL
AXSIM_MONTE_CARLO

AXSIM_DISTRIBUTED
AXSIM_CAMPAIGN
AXSIM_BENCHMARK
AXSIM_REDTEAM

AXSIM_FULL
```

---

# 453. Minimal embedded profile

```text
AXSIM_CORE
```

chỉ cần:

```text
SimulationClock
SimulationRng
World
Environment
Scenario
Action
Observation
Transition
```

---

# 454. AI training profile

```text
AXSIM_CORE
+
AXSIM_SYNTHETIC
+
AXSIM_BATCH
```

cho phép:

```text
Environment
→ Trajectory
→ Dataset
→ 643 Training
```

---

# 455. Agent testing profile

```text
AXSIM_AGENT
+
AXSIM_SANDBOX
+
AXSIM_REPLAY
+
AXSIM_REDTEAM
```

---

# 456. Digital twin profile

```text
AXSIM_DIGITAL_TWIN
+
AXSIM_SENSOR
+
AXSIM_PHYSICS
```

---

# 457. Large-scale profile

```text
AXSIM_DISTRIBUTED
+
AXSIM_CAMPAIGN
+
AXSIM_MONTE_CARLO
+
AXSIM_BENCHMARK
```

---

# 458. Final architecture

```text
                         AXIOM SIMULATION PLANE

                         ┌─────────────────┐
                         │      646        │
                         │   Evaluation    │
                         └────────┬────────┘
                                  │
                                  ▼
┌──────────────┐          ┌───────────────┐          ┌──────────────┐
│     643      │◄────────►│     648       │◄────────►│     644      │
│ ML / Tensor  │          │  Simulation   │          │ AI Agent     │
└──────────────┘          └───────┬───────┘          └──────────────┘
                                  │
             ┌────────────────────┼────────────────────┐
             ▼                    ▼                    ▼
        ┌──────────┐        ┌──────────┐        ┌────────────┐
        │  World   │        │ Scenario │        │ Environment│
        └────┬─────┘        └────┬─────┘        └─────┬──────┘
             │                   │                    │
             └───────────────────┼────────────────────┘
                                 ▼
                         ┌───────────────┐
                         │ State / Tick  │
                         │ RNG / Replay  │
                         └───────┬───────┘
                                 │
             ┌───────────────────┼──────────────────┐
             ▼                   ▼                  ▼
        ┌─────────┐         ┌──────────┐      ┌──────────┐
        │ Sensors │         │ Physics  │      │ Renderer │
        └─────────┘         └──────────┘      └──────────┘
             │                   │                  │
             └───────────────────┼──────────────────┘
                                 ▼
                       Synthetic Observation
                                 │
                                 ▼
                         Agent / Model
                                 │
                                 ▼
                              Action
                                 │
                                 ▼
                            Environment
```

---

# 459. Toàn bộ AI closed-loop stack

Axiom hiện có:

```text
643  → Model / Tensor / Training / Inference
644  → Agent / Tools / Planning / Memory
645  → Knowledge / Semantic Graph / RAG
646  → Evaluation / Benchmark / Safety Testing
647  → Model Registry / Lifecycle / Supply Chain
648  → Simulation / Synthetic Data / Sandbox
```

Khi ghép lại:

```text
                  ┌───────────────┐
                  │     648       │
                  │  Environment  │
                  └───────┬───────┘
                          │
                       Observe
                          │
                          ▼
                  ┌───────────────┐
                  │     644       │
                  │     Agent     │
                  └───────┬───────┘
                          │
                         Act
                          │
                          ▼
                  ┌───────────────┐
                  │     648       │
                  │  Environment  │
                  └───────┬───────┘
                          │
                      Trajectory
                          │
                          ▼
                  ┌───────────────┐
                  │     646       │
                  │   Evaluation  │
                  └───────┬───────┘
                          │
                     Evidence
                          │
                          ▼
                  ┌───────────────┐
                  │     647       │
                  │ Model Lifecycle│
                  └───────┬───────┘
                          │
                       Release
                          │
                          ▼
                  ┌───────────────┐
                  │     636       │
                  │   Deployment  │
                  └───────────────┘
```

---

# 460. Kết quả kiến trúc

BOOTSTRAP-648 hoàn thiện một mảnh ghép quan trọng còn thiếu trong AI stack của Axiom:

**AI không chỉ có model và agent; Axiom giờ có native environment để tạo ra dữ liệu, kiểm thử hành vi, tái tạo lỗi, chạy counterfactual, mô phỏng hệ thống và thực hiện closed-loop validation.**

Đặc biệt, architecture giữ được ranh giới:

```text
Simulation ≠ Evaluation
Evaluation ≠ Model Registry
Model Registry ≠ Deployment
Deployment ≠ Serving
Serving ≠ Physical Actuation
Synthetic Data ≠ Real Observation
Simulation State ≠ Ground Truth
```

---

# 461. Trạng thái

**BOOTSTRAP-648 — COMPLETE**

### Task kế tiếp

**BOOTSTRAP-649 — Native AI Multimodal Foundation, Unified Representation, Cross-Modal Embedding, Vision-Language-Audio-Speech Processing, Multimodal Fusion & Generative Media Runtime 5.0**
:::