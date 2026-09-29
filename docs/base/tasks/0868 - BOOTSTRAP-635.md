Tiếp tục chuỗi đặc tả Axiom. Task kế tiếp là **BOOTSTRAP-635**, xây lớp control-plane phân tán làm nền cho scheduler, cluster, leader election, placement và coordination.

:::writing{variant="document" id="58321" title="AXIOM BOOTSTRAP-635 — Native Distributed Scheduler, Cluster Membership, Leader Election, Consensus Boundary, Placement, Service Coordination & Control-Plane Runtime 5.0"}
# BOOTSTRAP-635
# Native Distributed Scheduler, Cluster Membership, Leader Election, Consensus Boundary, Placement, Service Coordination & Control-Plane Runtime 5.0

**Status:** COMPLETE  
**Layer:** Distributed Control Plane / Cluster Runtime  
**Depends on:** BOOTSTRAP-600 → BOOTSTRAP-634  
**Primary dependencies:** 603, 605, 606, 607, 608, 610, 611, 612, 628, 629, 630, 631, 632, 633, 634

---

## 1. Mục tiêu

BOOTSTRAP-635 định nghĩa control-plane phân tán native của Axiom.

Nó cung cấp:

- cluster membership;
- node identity;
- node health và failure detection;
- topology;
- cluster epochs/generations;
- leader election;
- consensus boundary;
- replicated control state;
- distributed leases;
- fencing;
- distributed coordination;
- workload placement;
- resource-aware scheduling;
- service coordination;
- reconciliation;
- node draining;
- workload evacuation;
- rescheduling;
- rolling coordination;
- maintenance coordination;
- cluster-level policy;
- multi-node control-plane APIs.

635 **không biến Axiom thành Kubernetes**.

Axiom chỉ cung cấp primitive runtime native đủ để xây dựng:

- cluster runtime;
- service platform;
- distributed compute;
- event processing;
- workflow workers;
- deployment controllers;
- database clusters;
- edge clusters;
- private infrastructure;
- embedded distributed systems.

External systems có thể được tích hợp thông qua provider boundary.

---

# 2. Nguyên tắc kiến trúc

## 2.1 Control plane ≠ data plane

635 quản lý:

```text
membership
leadership
desired state
placement
coordination
leases
control state
```

Không trực tiếp xử lý:

```text
application payload
large data streams
media streams
user traffic
bulk storage
GPU tensors
```

Các workload này thuộc:

- 609/626 networking;
- 628 distributed data;
- 629 workflow;
- 630 distributed compute;
- 631 service runtime;
- 632 gateway;
- 634 event runtime.

---

## 2.2 Không bắt buộc Kubernetes

Không có dependency bắt buộc vào:

- Kubernetes;
- etcd;
- Consul;
- ZooKeeper;
- Nomad;
- Raft implementation;
- cloud control plane.

Các hệ thống trên chỉ có thể xuất hiện dưới dạng provider/adapter.

---

## 2.3 Consensus là boundary

Axiom định nghĩa semantics của consensus nhưng không ép một thuật toán duy nhất.

```text
ConsensusProvider
```

có thể được implement bằng:

```text
Raft
Multi-Paxos
BFT provider
External consensus service
Platform consensus
Single-node deterministic provider
```

Core runtime chỉ yêu cầu các invariant về:

- term;
- quorum;
- commit;
- ordering;
- fencing;
- membership;
- leader safety.

---

## 2.4 Không có "best effort" đối với safety-critical control state

Control state quan trọng phải có semantics rõ ràng:

```text
Committed
Uncommitted
Applied
Stale
Unknown
```

Không được coi:

```text
locally observed
```

là:

```text
globally committed
```

---

# 3. Cluster Model

Cluster là tập hợp các node cùng tham gia một control domain.

```text
Cluster
 ├── ClusterId
 ├── ClusterGeneration
 ├── Membership
 ├── Topology
 ├── ControlState
 ├── Leader
 ├── Scheduler
 └── Coordination
```

---

# 4. Core Identity Types

```text
ClusterId
NodeId
NodeGeneration
ClusterGeneration

LeaderId
LeaderTerm

WorkloadId
WorkloadGeneration

PlacementId
LeaseId
FencingToken

ControlRevision
```

Tất cả identity phải có generation/revision khi cần tránh ABA.

---

# 5. Node Identity

Một node được định danh bởi:

```text
NodeIdentity {
    node_id
    node_generation
    cluster_id
    boot_id
    build_id
    platform
    architecture
}
```

`NodeId` không được tái sử dụng đồng thời cho hai generation.

---

# 6. Node Lifecycle

Node states:

```text
Joining
Ready
Suspect
Unhealthy
Draining
Leaving
Failed
Quarantined
Removed
```

State transition:

```text
Joining
   ↓
Ready
   ↓
Suspect
   ↓
Unhealthy
   ↓
Failed
```

Node có thể quay lại:

```text
Suspect → Ready
```

nếu failure detector xác nhận hồi phục.

---

# 7. Node Generation

Mỗi lần node boot lại phải tạo:

```text
NodeGeneration++
```

Ví dụ:

```text
node-A / generation 41
```

khác hoàn toàn:

```text
node-A / generation 42
```

Mọi lease/assignment/control record phụ thuộc node phải có generation.

Điều này ngăn:

```text
old node
```

tiếp tục thực hiện hành động sau reboot.

---

# 8. Cluster Generation

Cluster membership configuration có:

```text
ClusterGeneration
```

Mọi thay đổi membership quan trọng tạo revision mới.

Ví dụ:

```text
generation 100
generation 101
generation 102
```

Không được áp dụng membership configuration cũ nếu revision thấp hơn revision hiện tại.

---

# 9. Membership Provider

```text
trait MembershipProvider {
    join(...)
    leave(...)
    observe(...)
    list(...)
    watch(...)
}
```

Provider có thể là:

```text
StaticMembership
SeedMembership
GossipMembership
ConsensusMembership
ExternalMembership
EmbeddedMembership
```

---

# 10. Membership Lease

Node phải duy trì membership lease.

```text
MembershipLease {
    node_id
    node_generation
    lease_id
    expires_at
    renewal_revision
}
```

Node mất khả năng renew không lập tức đồng nghĩa node chết.

Nó chuyển qua:

```text
Suspect
```

sau đó mới:

```text
Unhealthy
Failed
```

theo failure detector policy.

---

# 11. Heartbeat

Heartbeat có:

```text
Heartbeat {
    node_id
    generation
    sequence
    monotonic_time
    health_summary
    resource_summary
    control_revision
}
```

Heartbeat không được sử dụng làm nguồn duy nhất cho consensus safety.

---

# 12. Failure Detector

Failure detector phải phân biệt:

```text
Healthy
Suspected
Unreachable
Failed
Unknown
```

Failure detector có thể sử dụng:

- heartbeat;
- direct probes;
- indirect probes;
- network reachability;
- process supervision;
- OS health;
- resource pressure;
- application health;
- consensus observation.

Không được suy ra:

```text
network timeout == process definitely dead
```

---

# 13. Split-Brain Protection

Axiom phải bảo vệ control-plane khỏi stale node.

Cơ chế:

```text
Term
Epoch
Generation
Lease
FencingToken
ConsensusCommit
```

Một node cũ có thể vẫn đang chạy nhưng không còn authority.

Ví dụ:

```text
Leader A term=51
    ↓ partition

Cluster elects B term=52
    ↓

A must no longer mutate protected state.
```

---

# 14. Topology

Node có topology metadata:

```text
region
zone
rack
host
room
datacenter
network_domain
failure_domain
power_domain
gpu_domain
storage_domain
```

Ví dụ:

```text
NodeTopology {
    region = "vn"
    zone = "hn-1"
    rack = "r07"
    gpu = "cuda"
    storage = "nvme"
}
```

Topology là metadata, không phải assumption cứng của scheduler.

---

# 15. Node Labels

Node có labels:

```text
label("gpu", "a100")
label("arch", "x86_64")
label("storage", "nvme")
label("zone", "hn-1")
```

Labels phải:

- typed hoặc canonical string;
- deterministic;
- versioned;
- bounded;
- policy-controlled.

---

# 16. Node Taints

Node có thể khai báo:

```text
Taint {
    key
    value
    effect
}
```

Effects:

```text
PreferNoSchedule
NoSchedule
NoExecute
```

Workload cần explicit toleration nếu muốn chạy trên node bị taint.

---

# 17. Resource Advertisement

Node công bố:

```text
CPU
Memory
GPU
VRAM
Storage
IOPS
Network
Threads
Handles
IPC
Device
```

Resource accounting sử dụng semantics của BOOTSTRAP-606.

Không được duy trì một resource accounting system thứ hai.

---

# 18. Node Capacity

```text
NodeCapacity {
    total
    allocatable
    reserved
    used
    available
}
```

Phải phân biệt:

```text
physical capacity
reserved capacity
allocatable capacity
currently free capacity
```

---

# 19. Workload Model

```text
Workload {
    workload_id
    generation
    desired_state
    resource_request
    placement_policy
    security_policy
    runtime_policy
}
```

Workload có thể đại diện cho:

```text
service
worker
workflow activity
compute task
event processor
gateway instance
database replica
custom process
```

---

# 20. Desired State

Ví dụ:

```text
Service A
desired_instances = 8
```

Control plane không trực tiếp đảm bảo 8 instance tồn tại.

Nó duy trì:

```text
desired = 8
actual = 6
```

và reconciliation sẽ tạo thêm 2.

---

# 21. Actual State

Actual state đến từ:

- supervisor 605;
- service runtime 631;
- compute runtime 630;
- workflow runtime 629;
- event runtime 634;
- node membership;
- health providers.

---

# 22. Reconciliation Loop

Control plane thực hiện:

```text
observe
→ compare
→ plan
→ validate
→ commit
→ execute
→ observe
```

Không được:

```text
mutate desired state
```

chỉ để che giấu actual-state failure.

---

# 23. Reconciler

```text
trait Reconciler<T> {
    observe(...)
    diff(...)
    plan(...)
    validate(...)
    apply(...)
}
```

`plan()` phải có thể chạy deterministic trong cùng input state.

---

# 24. Reconciliation Safety

Một reconciliation operation phải kiểm tra:

```text
object generation
cluster generation
leader term
resource availability
security policy
capabilities
fencing token
```

trước mutation.

---

# 25. Scheduler

Scheduler là control-plane component tạo placement decisions.

```text
Scheduler
 ├── Filter
 ├── Score
 ├── Reserve
 ├── Commit
 └── Reconcile
```

---

# 26. Scheduling Pipeline

```text
Workload
 ↓
Admission
 ↓
Constraint filtering
 ↓
Resource filtering
 ↓
Security filtering
 ↓
Topology filtering
 ↓
Scoring
 ↓
Reservation
 ↓
Placement commit
 ↓
Execution
```

---

# 27. Placement

```text
Placement {
    placement_id
    workload_id
    node_id
    node_generation
    resources
    fencing_token
    revision
}
```

Placement luôn gắn với node generation.

---

# 28. Hard Constraints

Hard constraints có thể gồm:

```text
required capability
required architecture
required GPU
minimum memory
required zone
required device
required security profile
required package
required network domain
```

Không thỏa hard constraint → node bị loại.

---

# 29. Soft Constraints

Soft constraints:

```text
locality
spread
latency
cost metadata
cache locality
data locality
GPU locality
network locality
```

Chỉ dùng để scoring.

---

# 30. Affinity

Workload có thể yêu cầu:

```text
Affinity {
    workload
    service
    node
    topology
    data
    device
}
```

---

# 31. Anti-Affinity

Ví dụ:

```text
replica A ≠ same node as replica B
```

hoặc:

```text
replicas should spread across zones
```

Anti-affinity có thể là:

```text
Hard
Preferred
```

---

# 32. Spreading

Scheduler hỗ trợ spread theo:

```text
node
rack
zone
region
failure domain
power domain
```

Mục tiêu là tránh concentration.

---

# 33. Bin Packing

Provider scheduler có thể sử dụng:

```text
BestFit
FirstFit
WorstFit
BalancedFit
ResourceAwareFit
```

Đây là algorithm choices, không phải ranking của scheduler.

---

# 34. Scoring Provider

```text
trait PlacementScorer {
    score(workload, node, context) -> Score
}
```

Score phải:

- bounded;
- deterministic trong cùng input;
- không thay đổi security semantics;
- không cấp thêm capability.

---

# 35. Locality

Scheduler có thể ưu tiên:

```text
data locality
cache locality
GPU locality
network locality
storage locality
```

nhưng locality không được vượt qua hard security constraints.

---

# 36. GPU Placement

GPU placement tích hợp 614/630.

Hỗ trợ:

```text
GPU count
GPU memory
GPU type
compute capability
device partition
exclusive GPU
shared GPU
accelerator class
```

---

# 37. Device Affinity

Workload có thể yêu cầu:

```text
device = GPU
device = camera
device = FPGA
device = NIC
device = accelerator
```

Device capability phải được cấp qua 603.

---

# 38. Reservation

Scheduler có thể reserve resources trước khi commit.

```text
Reservation {
    reservation_id
    workload_id
    node_id
    resources
    expires_at
}
```

Reservation hết hạn tự động giải phóng.

---

# 39. Reservation Atomicity

Nếu placement yêu cầu nhiều resource:

```text
CPU
Memory
GPU
Storage
```

scheduler không được commit partial reservation.

Hoặc:

```text
all reserved
```

hoặc:

```text
none reserved
```

---

# 40. Preemption

Preemption là optional policy.

Có thể:

```text
NoPreemption
BestEffort
PriorityBased
QuotaAware
```

Preemption phải:

- kiểm tra capability;
- tôn trọng workload protection;
- tạo audit event;
- có grace period;
- tránh starvation.

---

# 41. Priority

Priority là scheduling property.

Priority không được bypass:

- security;
- tenancy isolation;
- hard resource limit;
- capability policy;
- node taint.

---

# 42. Fairness

Scheduler phải hỗ trợ:

```text
tenant fairness
workload fairness
resource fairness
priority fairness
```

Không được để một tenant monopolize cluster nếu policy không cho phép.

---

# 43. Tenant Quota

Quota lấy semantics từ 606.

Ví dụ:

```text
tenant-A:
    cpu <= 32
    memory <= 128GiB
    gpu <= 2
```

Scheduler không tự tạo quota system riêng.

---

# 44. Scheduler Queue

Scheduler có:

```text
Pending
Admitted
Scheduled
Blocked
Rejected
```

Queue phải bounded hoặc quota-controlled.

---

# 45. Scheduling Backpressure

Khi scheduler quá tải:

```text
admission control
queue limit
tenant quota
priority
load shedding
```

Không được để pending workloads tăng vô hạn.

---

# 46. Leader Election

Cluster control-plane có leader abstraction:

```text
Leader
Term
Lease
Election
```

---

# 47. Leader Identity

```text
LeaderRecord {
    node_id
    node_generation
    term
    lease_id
    fencing_token
}
```

---

# 48. Election Safety

Trong một term:

```text
at most one valid leader
```

Một node chỉ được coi là leader sau khi provider xác nhận authority.

---

# 49. Leader Term

Term phải monotonically increasing.

```text
50 < 51 < 52
```

Node có term thấp hơn không được mutate committed control state.

---

# 50. Leader Lease

Leader có thể dùng lease để giảm election churn.

```text
LeaderLease {
    term
    holder
    expires_at
}
```

Lease không thay thế consensus commit khi safety yêu cầu mạnh hơn.

---

# 51. Leader Step-Down

Leader phải relinquish authority khi:

```text
lease expired
term superseded
membership invalid
fencing failure
consensus failure
cluster shutdown
administrative drain
```

---

# 52. Consensus Provider

```text
trait ConsensusProvider {
    propose(entry)
    read_consistent(key)
    commit_index()
    current_term()
    leader()
    watch(...)
}
```

---

# 53. Consensus Entry

```text
ConsensusEntry {
    term
    index
    command_type
    payload
    schema_fingerprint
}
```

Payload phải deterministic và schema-versioned.

---

# 54. Commit Semantics

Một entry chỉ được coi là committed khi provider xác nhận consensus commit.

```text
proposed != committed
```

---

# 55. Apply Semantics

Sau commit:

```text
committed
→ applied
```

Apply phải idempotent.

---

# 56. Control State Machine

Control state được biểu diễn bằng deterministic state machine.

```text
Command
 ↓
Validate
 ↓
Commit
 ↓
Apply
 ↓
Emit Event
```

---

# 57. State Machine Determinism

State machine không được phụ thuộc trực tiếp vào:

```text
wall clock
randomness
network response
local filesystem
GPU state
thread scheduling
```

trong deterministic apply path.

---

# 58. Consensus Snapshot

Control state có snapshot:

```text
ControlSnapshot {
    cluster_generation
    term
    commit_index
    schema_fingerprint
    state_hash
}
```

Snapshot tích hợp 612/628.

---

# 59. Log Compaction

Consensus/control history có thể compact.

Không được xóa state cần cho:

- active leases;
- current membership;
- current fencing;
- audit requirements;
- recovery.

---

# 60. Membership Changes

Thay đổi membership phải có explicit transition.

Ví dụ:

```text
Joining
→ Voting
→ Ready
```

hoặc:

```text
Ready
→ Draining
→ Leaving
→ Removed
```

---

# 61. Quorum

Quorum semantics phải explicit.

Không được suy luận:

```text
majority response
```

là đủ cho mọi loại operation.

Các operations phải khai báo consistency requirement:

```text
Local
Quorum
Committed
Linearizable
```

---

# 62. Fencing

Fencing là cơ chế ngăn stale owner tiếp tục hành động.

```text
FencingToken {
    resource_id
    epoch
    sequence
}
```

Consumer phải reject token cũ.

---

# 63. Fencing Example

Node A:

```text
token = 41
```

Node A mất leadership.

Node B:

```text
token = 42
```

Resource phải reject:

```text
token 41
```

---

# 64. Distributed Lease

```text
Lease {
    lease_id
    owner
    owner_generation
    epoch
    expires_at
}
```

Lease dùng cho:

- leader;
- worker ownership;
- scheduler reservation;
- distributed lock;
- task assignment.

---

# 65. Lease Renewal

Renewal phải:

- authenticate owner;
- validate generation;
- validate epoch;
- check current term;
- respect resource quota.

Không được renew lease của generation cũ.

---

# 66. Distributed Lock

Lock:

```text
DistributedLock {
    resource_id
    owner
    lease
    fencing_token
}
```

Không có:

```text
unfenced distributed lock
```

cho resource mutation safety-critical.

---

# 67. Lock Semantics

Supported:

```text
Exclusive
Shared
ReadWrite
```

Lock acquisition có:

```text
timeout
deadline
cancellation
```

---

# 68. Coordination Barrier

```text
Barrier {
    barrier_id
    participants
    epoch
}
```

Dùng cho:

- rolling operation;
- coordinated startup;
- migration phase;
- cluster upgrade.

---

# 69. Cluster Coordination Events

Control plane có thể phát:

```text
NodeJoined
NodeReady
NodeSuspected
NodeFailed
NodeDraining
LeaderChanged
PlacementCreated
PlacementReleased
WorkloadRescheduled
LeaseExpired
ClusterGenerationChanged
```

Events đi qua 634 khi cần distributed delivery.

---

# 70. Event vs Consensus

Không được dùng event bus thay consensus.

```text
Consensus = authority/state safety
Event bus = notification/stream
```

Một event có thể bị:

```text
duplicated
delayed
reordered
```

trừ khi contract đảm bảo khác.

---

# 71. Service Coordination

631 có thể đăng ký:

```text
ServiceInstance
```

với 635 để yêu cầu placement.

635 trả:

```text
PlacementDecision
```

631 chịu trách nhiệm thực thi instance.

---

# 72. Service Lifecycle Integration

Flow:

```text
635 Scheduler
    ↓
631 Service Runtime
    ↓
605 Supervisor
    ↓
OS Process
```

---

# 73. Workflow Integration

629 activity worker có thể yêu cầu:

```text
CPU
memory
GPU
capability
locality
```

635 quyết định placement.

---

# 74. Distributed Compute Integration

630 sử dụng:

```text
PlacementRequest
```

để chạy:

```text
ComputeTask
```

trên node phù hợp.

---

# 75. Event Processor Integration

634 consumer/stream processor có thể yêu cầu:

```text
partition locality
state locality
GPU
memory
network
```

635 có thể placement processor gần data.

---

# 76. Gateway Integration

632 có thể yêu cầu:

```text
gateway replicas
edge locality
network locality
TLS capability
device capability
```

---

# 77. Rolling Coordination

Control plane hỗ trợ primitives:

```text
StartBatch
DrainBatch
WaitReady
Advance
Rollback
Complete
```

Nó không tự định nghĩa deployment strategy duy nhất.

---

# 78. Node Draining

Node chuyển:

```text
Ready
→ Draining
```

Scheduler không đặt workload mới lên node nếu policy không cho phép.

Existing workloads:

```text
finish
migrate
restart
evacuate
```

theo workload policy.

---

# 79. Evacuation

```text
EvacuationPlan {
    node
    workloads
    destination_constraints
    deadline
}
```

Mỗi workload phải được xử lý riêng theo khả năng:

```text
Migratable
Restartable
Pinned
NonMovable
```

---

# 80. Non-Movable Workloads

Một workload có thể khai báo:

```text
non_movable = true
```

Scheduler phải giữ nó trên node hoặc báo maintenance conflict.

Không được tự ý phá workload.

---

# 81. Failure Recovery

Node failure:

```text
membership detects failure
        ↓
placements invalidated
        ↓
fencing
        ↓
workload reconciliation
        ↓
new placement
        ↓
service/worker restart
```

---

# 82. Stale Placement Protection

Placement chứa:

```text
node_generation
cluster_generation
scheduler_revision
fencing_token
```

Mọi executor phải validate chúng.

---

# 83. Rescheduling

Workload có thể được reschedule khi:

```text
node failure
resource loss
device loss
maintenance
policy change
placement invalidation
```

---

# 84. Rescheduling Backoff

Không được reschedule vô hạn với tốc độ cao.

Phải có:

```text
retry budget
backoff
jitter
failure-domain awareness
```

---

# 85. Anti-Thrashing

Scheduler phải tránh:

```text
A → B → A → B
```

do minor metric fluctuation.

Cơ chế:

```text
stability window
movement cost
cooldown
hysteresis
minimum residency
```

---

# 86. Placement Movement Cost

Scheduler có thể tính:

```text
network migration cost
cache loss
GPU initialization
storage locality loss
cold start cost
```

Movement cost chỉ ảnh hưởng placement policy, không bypass hard constraints.

---

# 87. Cluster Maintenance

Node có thể khai báo:

```text
maintenance_window
drain_deadline
reason
```

Maintenance reason là descriptive metadata.

---

# 88. Cluster Upgrade

Cluster upgrade primitives:

```text
Prepare
Drain
Upgrade
Validate
Rejoin
Advance
Rollback
```

Không mặc định yêu cầu in-place binary replacement.

---

# 89. Binary Compatibility

Node chỉ được join cluster nếu đáp ứng:

```text
protocol version
control schema version
ABI compatibility
platform compatibility
security policy
cluster policy
```

---

# 90. Control Schema

Control messages sử dụng 612 schema system.

Mỗi schema có:

```text
SchemaId
Version
Fingerprint
Compatibility
```

---

# 91. Control Plane API

Core:

```text
Cluster
Membership
Scheduler
PlacementManager
LeaderElector
Consensus
LeaseManager
FencingManager
Reconciler
CoordinationManager
TopologyManager
```

---

# 92. Struct-Only API

Ví dụ:

```text
struct Scheduler {
    state
}

fn Scheduler.submit(
    self: Scheduler,
    workload: Workload
) -> Result<WorkloadId>

fn Scheduler.schedule(
    self: Scheduler,
    workload_id: WorkloadId
) -> Result<Placement>

fn Scheduler.cancel(
    self: Scheduler,
    workload_id: WorkloadId
) -> Result<void>
```

Không cần class hierarchy.

---

# 93. Leader API

```text
struct LeaderElector {
    provider
}

fn LeaderElector.acquire(
    self,
    identity
) -> Result<Leadership>

fn LeaderElector.release(
    self,
    leadership
) -> Result<void>
```

---

# 94. Lease API

```text
struct LeaseManager {
    provider
}

fn LeaseManager.acquire(
    self,
    resource,
    duration
) -> Result<Lease>

fn LeaseManager.renew(
    self,
    lease
) -> Result<Lease>

fn LeaseManager.release(
    self,
    lease
) -> Result<void>
```

---

# 95. Placement API

```text
struct PlacementManager {
    scheduler
}

fn PlacementManager.place(
    self,
    workload
) -> Result<Placement>

fn PlacementManager.release(
    self,
    placement
) -> Result<void>
```

---

# 96. Capability Security

Control-plane operations được bảo vệ bởi 603.

Ví dụ:

```text
cluster.membership.read
cluster.membership.modify
cluster.scheduler.read
cluster.scheduler.modify
cluster.placement.read
cluster.placement.modify
cluster.leader.observe
cluster.leader.acquire
cluster.control.commit
cluster.node.drain
cluster.node.quarantine
```

---

# 97. No Authority Amplification

Workload capability:

```text
capability(workload)
```

không tự động trở thành:

```text
capability(cluster)
```

---

# 98. Node Bootstrap Security

Node join phải xác thực:

```text
cluster identity
node identity
credentials
build identity
policy
capabilities
```

Node không được tự đăng ký bằng arbitrary identity.

---

# 99. Cluster Admission

Admission policy có thể kiểm tra:

```text
publisher
build
version
platform
architecture
security profile
attestation
labels
resources
```

---

# 100. Quarantine

Node có thể bị:

```text
Quarantined
```

khi:

- identity invalid;
- protocol invalid;
- security policy violation;
- inconsistent generation;
- suspected compromise;
- incompatible build.

Quarantine không tự động kết luận nguyên nhân.

---

# 101. Secrets

Control-plane state không được lưu plaintext secret nếu không cần thiết.

Secret references sử dụng 601/610.

Không ghi secrets vào:

```text
consensus log
placement event
scheduler diagnostics
membership heartbeat
```

---

# 102. Configuration

635 lấy policy từ 601:

```text
membership policy
failure detector
scheduler policy
leader lease
quorum policy
placement policy
resource policy
maintenance policy
```

Configuration snapshot phải có fingerprint.

---

# 103. Dynamic Reload

Các policy có thể reload nếu semantic cho phép.

Reload:

```text
validate
→ stage
→ atomically activate
```

Không làm thay đổi control state nửa chừng.

---

# 104. Resource Integration

606 cung cấp:

```text
CPU budget
memory quota
GPU quota
network quota
storage quota
process quota
```

635 chỉ điều phối, không duplicate accounting.

---

# 105. Diagnostics

635 tích hợp 602/633.

Metrics:

```text
cluster_nodes
healthy_nodes
suspected_nodes
leader_changes
election_duration
scheduler_queue_depth
placement_latency
placement_failures
rescheduling_count
lease_expirations
fencing_rejections
reconciliation_latency
```

---

# 106. Tracing

Distributed traces phải có:

```text
cluster
term
scheduler_revision
workload_id
placement_id
node_id
```

Không ghi credential/secret.

---

# 107. Scheduler Explain

Axiom cung cấp diagnostic:

```text
why_not_scheduled(workload)
```

Ví dụ:

```text
node-1:
    rejected: insufficient_memory

node-2:
    rejected: gpu_required

node-3:
    accepted
```

Đây là diagnostic fact, không phải scheduler recommendation.

---

# 108. Control Audit

Audit events:

```text
NodeAdmission
NodeRemoval
LeaderElection
LeaderChange
LeaseGrant
LeaseRevoke
Fencing
PlacementCommit
PlacementRelease
WorkloadPreempt
NodeDrain
NodeQuarantine
PolicyChange
```

---

# 109. Persistent State

Persistent control state sử dụng:

```text
611 Storage
612 Serialization
628 Replicated Data
```

Không tạo storage engine riêng.

---

# 110. Control State Recovery

Recovery:

```text
snapshot
+
committed log
```

→ reconstruct state.

Uncommitted entries không được replay như committed state.

---

# 111. Cluster Restart

Nếu toàn cluster restart:

```text
restore control snapshot
restore committed entries
restore membership
validate node generations
reconstruct leases
fence stale owners
resume reconciliation
```

---

# 112. Lease Recovery

Lease có thể:

```text
expire on cluster restart
```

trừ khi provider có durable lease semantics rõ ràng.

Safety mặc định ưu tiên:

```text
reacquire
```

hơn:

```text
blindly restore
```

---

# 113. Scheduler State Recovery

Scheduler có thể rebuild:

```text
pending queue
active placements
reservations
resource view
```

từ authoritative state.

---

# 114. Eventual Observation

Actual node state có thể stale.

Scheduler phải ghi nhận:

```text
observed_at
revision
source
generation
```

---

# 115. Stale Observation

Observation cũ không được overwrite observation mới.

```text
revision_old < revision_new
```

→ reject old update.

---

# 116. Clock Semantics

Distributed control phải phân biệt:

```text
monotonic duration
wall-clock timestamp
logical revision
consensus term
```

Không dùng wall clock làm fencing authority.

---

# 117. Time Skew

Clock skew không được làm phá vỡ safety.

Lease có thể yêu cầu provider/platform semantics có bounded clock uncertainty.

---

# 118. Logical Time

635 có thể sử dụng:

```text
term
revision
sequence
logical epoch
```

cho ordering.

---

# 119. Scheduler Determinism

Cùng:

```text
cluster snapshot
workload set
policy
resource state
```

phải tạo cùng placement plan nếu scheduler provider khai báo deterministic mode.

---

# 120. Deterministic Simulation

Axiom cung cấp:

```text
ClusterSimulator
FakeMembership
FakeConsensus
FakeClock
FakeNetwork
FakeNode
FakeResourceProvider
FakeScheduler
```

để test control-plane.

---

# 121. Fault Injection

Simulator phải hỗ trợ:

```text
packet loss
delay
partition
node crash
leader crash
clock skew
duplicate message
reordered message
stale heartbeat
resource disappearance
GPU loss
disk full
consensus delay
lease expiry
```

---

# 122. Network Partition Test

Test:

```text
A B C
 \|/
partition
```

phải đảm bảo không có hai valid leaders cùng term.

---

# 123. Stale Leader Test

Leader A bị partition.

B được elected term+1.

A quay lại.

A phải:

```text
step down
refresh state
rejoin
```

không được mutate committed control state.

---

# 124. Stale Node Test

Node generation 41 chết.

Node generation 42 xuất hiện.

Placement dành cho generation 41 phải bị reject.

---

# 125. Lease Safety Test

Expired lease:

```text
renew → reject
execute → reject
```

trừ khi owner reacquires lease.

---

# 126. Fencing Test

```text
token=10
token=11
```

Operation bằng token 10 phải bị resource provider từ chối.

---

# 127. Scheduler Failure Test

Scheduler leader crash giữa:

```text
reserve
commit
```

Recovery không được tạo duplicate placement.

---

# 128. Reconciliation Idempotency

Chạy:

```text
reconcile()
reconcile()
reconcile()
```

với cùng state phải không tạo side effects duplicate.

---

# 129. Resource Race

Hai workloads cùng yêu cầu:

```text
GPU 1
```

Scheduler phải tránh double allocation.

---

# 130. Split-Brain Resource Test

Hai stale schedulers không được cùng commit placement hợp lệ.

---

# 131. Node Drain Test

Khi:

```text
node = Draining
```

scheduler không đặt workload mới nếu policy không cho phép.

---

# 132. Failed Node Recovery Test

Node failure phải tạo:

```text
placement invalidation
→ rescheduling
```

theo policy.

---

# 133. Anti-Thrashing Test

Repeated tiny resource fluctuations không được gây migration loop vô hạn.

---

# 134. Quota Test

Tenant vượt quota:

```text
admission → reject
```

Không được bypass bằng placement khác.

---

# 135. Security Test

Workload không có capability:

```text
cluster.placement.modify
```

không được mutate placement.

---

# 136. Consensus Provider Test

Provider test phải kiểm tra:

```text
proposal
commit
term
leader
snapshot
recovery
membership change
```

---

# 137. External Consensus Provider

External provider có adapter:

```text
ExternalConsensusProvider
```

Nhưng semantics phải map vào Axiom model.

---

# 138. Provider Isolation

Provider-specific API không được leak vào core scheduler API.

Ví dụ core không được yêu cầu:

```text
RaftLog
etcdRevision
ZooKeeperZNode
```

---

# 139. Cluster Networking

Control-plane transport có thể dùng:

```text
609 sockets
610 TLS
604 IPC
626 RPC
631 service transport
```

Không tạo transport stack mới.

---

# 140. Control-Plane Transport Security

Production distributed control traffic mặc định phải hỗ trợ:

```text
authentication
integrity
encryption
replay protection
identity verification
```

---

# 141. Control Message Limits

Mọi control message phải có:

```text
max size
decode budget
timeout
deadline
authentication budget
```

để chống resource exhaustion.

---

# 142. Backpressure

Control plane phải có:

```text
bounded queues
priority
coalescing
rate limits
load shedding
```

Không để heartbeat storm làm scheduler chết.

---

# 143. Membership Storm Protection

Khi hàng nghìn node join/rejoin:

```text
batching
rate limit
jitter
incremental reconciliation
```

---

# 144. Leader Election Storm Protection

Không được để transient network issue gây election liên tục.

Có:

```text
minimum election timeout
jitter
backoff
failure detector hysteresis
```

---

# 145. Control-Plane Priority

Control messages được phân loại:

```text
Critical
High
Normal
Low
```

Ví dụ:

```text
fencing > diagnostics
```

---

# 146. Multi-Control-Plane Instances

Có thể chạy nhiều control-plane instances.

```text
CP1
CP2
CP3
```

Consensus provider xác định authority.

---

# 147. Stateless Control Components

Một số components có thể stateless:

```text
scheduler workers
placement explainers
metrics collectors
API frontends
```

Authority vẫn nằm ở control state.

---

# 148. Control Plane Horizontal Scaling

Có thể scale:

```text
API readers
observers
scheduler workers
reconcilers
diagnostic workers
```

Nhưng mutation authority phải có concurrency control.

---

# 149. Read Consistency

Control API phải khai báo:

```text
Local
StaleOK
BoundedStaleness
Committed
Linearizable
```

Client không được giả định mọi read là linearizable.

---

# 150. Watch API

```text
watch_cluster()
watch_nodes()
watch_workloads()
watch_placements()
watch_leader()
watch_policy()
```

Watch phải hỗ trợ:

```text
revision
resume
heartbeat
timeout
backpressure
```

---

# 151. Watch Resume

Client có thể:

```text
watch(from_revision)
```

Nếu revision không còn do compaction:

```text
Compacted
```

client phải lấy snapshot mới.

---

# 152. Control API Versioning

API có:

```text
major
minor
schema fingerprint
```

Backward compatibility phải explicit.

---

# 153. Cluster Policy

Cluster policy có thể định nghĩa:

```text
membership
security
placement
resource
failure domains
maintenance
upgrade
```

---

# 154. Policy Precedence

```text
Security hard constraints
>
Cluster hard constraints
>
Tenant hard constraints
>
Workload hard constraints
>
Soft scheduling preferences
```

Không được để preference override security.

---

# 155. Placement Explainability

Scheduler phải có structured reason codes:

```text
InsufficientCpu
InsufficientMemory
GpuUnavailable
TaintMismatch
AffinityMismatch
AntiAffinityViolation
CapabilityMissing
QuotaExceeded
TopologyMismatch
PolicyDenied
```

---

# 156. AI-Readable Metadata

Compiler sinh:

```text
.axcluster
.axnode
.axplacement
.axcontrol
.axpolicy
```

Metadata chứa:

```text
schema
identity
dependencies
constraints
capabilities
resources
placement rules
state transitions
```

---

# 157. Compiler Annotations

Ví dụ:

```text
@cluster
@node
@placement
@leader
@replicated
@schedule
@affinity
@anti_affinity
@resource
@quorum
@lease
@fenced
@reconcile
```

---

# 158. Compile-Time Validation

Compiler có thể kiểm tra:

```text
invalid resource unit
invalid capability
invalid placement constraint
invalid schema
invalid lifecycle transition
invalid annotation combination
```

---

# 159. IR Integration

IR có semantic operations:

```text
cluster.join
cluster.leave
cluster.observe
cluster.leader
cluster.term
cluster.commit
cluster.watch
lease.acquire
lease.renew
lease.release
fence.validate
placement.request
placement.commit
placement.release
reconcile
```

---

# 160. No Hidden Runtime

Simple applications không sử dụng distributed features thì:

```text
không link membership
không link scheduler
không link consensus
không link cluster runtime
```

Dead stripping phải loại bỏ toàn bộ.

---

# 161. Local Mode

635 phải có:

```text
SingleNodeControlProvider
```

cho development.

Không cần network.

---

# 162. Embedded Mode

Embedded system có thể map:

```text
Node = device
Cluster = local control domain
Scheduler = deterministic coordinator
```

---

# 163. WASM Mode

WASM không tự truy cập cluster network.

Host cung cấp:

```text
MembershipProvider
ConsensusProvider
SchedulerProvider
```

thông qua capability.

---

# 164. Mobile Mode

Android/iOS có lifecycle restrictions.

Cluster membership phải chịu:

```text
background suspension
network loss
process termination
battery policy
```

Không giả định mobile process luôn online.

---

# 165. Edge Mode

Edge nodes có thể:

```text
intermittent connectivity
limited resources
local control plane
eventual synchronization
```

635 phải cho phép hierarchy:

```text
LocalCluster
    ↓
RegionalControlPlane
    ↓
GlobalControlPlane
```

nhưng không bắt buộc.

---

# 166. Hierarchical Control

Một cluster có thể là member của higher-level control domain.

Authority boundary phải rõ:

```text
local authority
regional authority
global authority
```

Không tự động propagate full capabilities.

---

# 167. Federation Boundary

Multi-cluster federation không được giả định:

```text
single global consensus
```

Mỗi cluster giữ authority riêng.

Federation sử dụng explicit APIs.

---

# 168. Cross-Cluster Placement

Cross-cluster scheduler là higher-level provider.

Local cluster vẫn enforce:

```text
local security
local quota
local resource
local fencing
```

---

# 169. Cluster-to-Cluster Identity

Mỗi cluster có:

```text
ClusterId
ClusterIdentity
ClusterGeneration
TrustDomain
```

Cross-cluster trust qua 603/610/627.

---

# 170. Control-Plane Federation Security

Không được:

```text
cluster-A capability → cluster-B full authority
```

Capability phải attenuate.

---

# 171. Autoscaling Boundary

635 có thể expose:

```text
capacity signals
pending workload count
resource pressure
```

Autoscaling policy có thể nằm ở higher layer.

635 không tự dự đoán future load.

---

# 172. Capacity Provider

```text
trait CapacityProvider {
    observe(...)
    request_scale(...)
    release_capacity(...)
}
```

Cloud/VM/bare-metal providers nằm ngoài core.

---

# 173. Cluster Expansion

Node join:

```text
authenticate
→ validate
→ assign generation
→ admit
→ initialize
→ ready
```

---

# 174. Cluster Shrink

Node removal:

```text
cordon
→ drain
→ verify
→ remove
→ revoke leases
→ finalize
```

---

# 175. Cordon

Cordon chỉ ngăn:

```text
new placement
```

không tự động terminate workloads.

---

# 176. Quarantine vs Drain

`Drain`:

```text
planned lifecycle action
```

`Quarantine`:

```text
security/safety isolation
```

Không được dùng interchangeably.

---

# 177. Node Recovery

Failed node returning phải:

```text
new generation
revalidate identity
rejoin
re-advertise resources
reconcile workloads
```

Không được reuse stale leases.

---

# 178. Device Failure

Nếu GPU/device mất:

```text
device generation changes
```

Workload phụ thuộc device phải:

```text
recover
migrate
restart
or fail
```

theo policy.

---

# 179. Persistent Device Identity

Device identity lấy từ 614.

635 chỉ lưu reference:

```text
DeviceId
DeviceGeneration
```

không duplicate device database.

---

# 180. Control Plane and Storage

Consensus state có thể sử dụng:

```text
611
612
628
```

nhưng consensus semantics vẫn thuộc 635 provider.

---

# 181. Control Plane and Event Bus

634 dùng để phát:

```text
notifications
audit streams
scheduler events
cluster events
```

Không dùng 634 làm sole source of truth cho consensus.

---

# 182. Control Plane and Workflow

629 có thể tạo durable workflow:

```text
cluster upgrade
node evacuation
rolling restart
```

635 cung cấp state/coordination primitives.

---

# 183. Control Plane and Compute

630 có thể request:

```text
placement
reservation
GPU
resource
```

635 không thực thi computation.

---

# 184. Control Plane and Services

631 chịu:

```text
service execution
health
connections
traffic
```

635 chịu:

```text
placement
coordination
cluster state
```

---

# 185. Control Plane and Gateway

632 chịu:

```text
edge traffic
TLS
routing
proxying
```

635 chịu:

```text
gateway instance placement
cluster coordination
capacity
```

---

# 186. Control Plane and Observability

633 cung cấp:

```text
metrics
traces
profiles
telemetry
```

635 cung cấp semantic dimensions:

```text
cluster
node
term
workload
placement
lease
```

---

# 187. Cluster Health

Cluster health không phải một boolean đơn giản.

```text
Healthy
Degraded
Partitioned
NoLeader
InsufficientQuorum
Overloaded
Recovering
Maintenance
Unknown
```

---

# 188. Quorum Health

Có thể có:

```text
leader present
quorum available
quorum lost
```

Quorum loss không nhất thiết đồng nghĩa toàn cluster down.

Data-plane behavior phải tuân theo service consistency policy.

---

# 189. No-Leader Mode

Khi không có leader:

```text
read-only local observations
```

có thể tiếp tục nếu policy cho phép.

Mutations yêu cầu authority không được commit.

---

# 190. Graceful Control-Plane Shutdown

Control instance:

```text
stop accepting leadership
finish/abort in-flight operations
release leases
flush audit
persist state
shutdown
```

---

# 191. Leader Handoff

Optional:

```text
prepare successor
transfer leadership
confirm new term
release old authority
```

giảm downtime.

---

# 192. Leadership Transfer Safety

Old leader không được tiếp tục commit sau transfer.

---

# 193. Control-Plane Overload

Khi overload:

```text
admission
prioritization
coalescing
batching
sampling
load shedding
```

Không được drop:

```text
fencing
security
consensus-critical
lease safety
```

messages tùy tiện.

---

# 194. Scheduler Batching

Scheduler có thể batch placement:

```text
N workloads
→ one scheduling cycle
```

nhưng mỗi placement vẫn phải có identity/revision.

---

# 195. Placement Batch Atomicity

Có thể hỗ trợ:

```text
atomic placement group
```

cho workloads cần cùng placement.

Ví dụ:

```text
frontend + sidecar + accelerator worker
```

---

# 196. Placement Group

```text
PlacementGroup {
    group_id
    workloads
    topology_constraints
    resource_constraints
}
```

---

# 197. Gang Scheduling

Optional provider:

```text
GangScheduling
```

Tất cả members phải được admitted cùng điều kiện.

---

# 198. Co-Scheduling

Có thể yêu cầu:

```text
same node
same zone
same rack
same GPU host
```

---

# 199. Data Locality

628 có thể cung cấp:

```text
replica locations
partition locations
```

635 sử dụng chúng như placement hints.

---

# 200. Consistency-Aware Placement

Workload yêu cầu:

```text
linearizable store
```

có thể cần placement gần quorum members.

635 chỉ sử dụng metadata; consistency semantics vẫn thuộc 628.

---

# 201. Replication-Aware Placement

Replicas nên tránh cùng:

```text
node
rack
zone
failure domain
```

nếu policy yêu cầu.

---

# 202. Failure Domain

Scheduler hỗ trợ explicit:

```text
FailureDomain {
    type
    identifier
}
```

---

# 203. Blast Radius Metadata

Placement policy có thể giới hạn số replicas cùng failure domain.

---

# 204. Resource Fragmentation

Scheduler có thể theo dõi fragmentation:

```text
CPU fragmentation
memory fragmentation
GPU fragmentation
device fragmentation
```

nhưng không được giả định một resource luôn fungible.

---

# 205. Heterogeneous Resources

Cluster có thể gồm:

```text
x86
ARM
GPU
NPU
FPGA
CPU-only
```

---

# 206. Architecture Constraint

Workload khai báo:

```text
arch = x86_64
```

Scheduler loại node không tương thích.

---

# 207. Binary Compatibility

Package/runtime metadata từ 613/625 phải được kiểm tra trước placement.

---

# 208. Image/Artifact Availability

Placement có thể yêu cầu:

```text
package available
model available
container/image equivalent
CAS object available
```

Axiom ưu tiên native AXPK/CAS semantics.

---

# 209. Artifact Locality

CAS 613 có thể cung cấp:

```text
object location
cache state
```

Scheduler có thể ưu tiên local artifact.

---

# 210. No Implicit Container Requirement

Axiom workload không mặc định là container.

Workload có thể là:

```text
native executable
module
service
task
WASM
GPU kernel
```

---

# 211. Process Placement

605 nhận:

```text
Placement
```

và spawn process phù hợp.

---

# 212. Resource Reservation Handoff

Flow:

```text
635 reservation
→ 605 process creation
→ 606 accounting
→ 631 readiness
→ 635 placement active
```

---

# 213. Placement Activation

Placement chỉ chuyển:

```text
Reserved
→ Active
```

sau khi executor xác nhận workload đã được admitted.

---

# 214. Failed Activation

Nếu activation thất bại:

```text
Active
```

không được ghi nhận.

Reservation được release hoặc retry theo policy.

---

# 215. Placement State Machine

```text
Pending
Reserved
Committed
Starting
Active
Draining
Released
Failed
Stale
```

---

# 216. Placement Generation

Mỗi replacement tạo generation mới.

```text
placement A generation 1
placement A generation 2
```

---

# 217. Duplicate Execution Prevention

Workload executor phải validate:

```text
workload generation
placement generation
fencing token
```

---

# 218. Exactly-Once Placement

635 không tuyên bố exactly-once execution.

Semantics:

```text
control state = at least once reconciliation
execution = provider-defined
```

---

# 219. Idempotent Execution

Executor phải hỗ trợ idempotent activation khi có thể.

---

# 220. Control Command Idempotency

Commands có:

```text
CommandId
```

Duplicate command không được tạo duplicate state transition.

---

# 221. Control Command Dedup

Dedup state có retention policy.

Không giữ vô hạn.

---

# 222. Command Authorization

Mỗi command được authorize trước khi commit.

---

# 223. Commit Authorization

Authorization result phải gắn với:

```text
policy fingerprint
identity
capability set
```

nếu operation security-critical.

---

# 224. Policy Change

Policy change có revision.

Các operations đã commit không bị retroactively thay đổi.

---

# 225. Policy Reconciliation

Sau policy change:

```text
existing state
→ evaluate
→ mark noncompliant
→ remediation policy
```

Không tự động kill workload nếu policy không yêu cầu.

---

# 226. Administrative Override

Admin override phải explicit capability.

Ví dụ:

```text
cluster.node.force_remove
```

---

# 227. Emergency Mode

Có thể có emergency control mode:

```text
Normal
Restricted
Emergency
Recovery
```

Mỗi mode có policy rõ ràng.

---

# 228. Emergency Fencing

Emergency mode có thể revoke leases/fence nodes theo authorization.

---

# 229. Recovery Mode

Recovery mode ưu tiên:

```text
restore authority
restore quorum
restore control state
reconcile workloads
```

---

# 230. Cluster Bootstrap

Bootstrap sequence:

```text
load config
→ load identity
→ initialize transport
→ initialize storage
→ establish membership
→ establish consensus
→ elect leader
→ recover control state
→ publish readiness
```

---

# 231. Cluster Ready

Cluster chỉ báo Ready khi:

```text
membership valid
control state recovered
required quorum available
leader authority established
scheduler initialized
security policy active
```

---

# 232. Node Ready

Node chỉ báo Ready khi:

```text
identity valid
resources advertised
required providers ready
security capabilities provisioned
executor ready
```

---

# 233. Control Plane Health Endpoint

Expose:

```text
/cluster/health
/cluster/membership
/cluster/leader
/cluster/scheduler
/cluster/placements
```

qua 626/631.

---

# 234. CLI

Native CLI:

```text
axiom cluster status
axiom cluster nodes
axiom cluster leader
axiom cluster quorum
axiom cluster leases
axiom cluster placements
axiom cluster schedule
axiom cluster drain NODE
axiom cluster quarantine NODE
axiom cluster reconcile
axiom cluster explain WORKLOAD
axiom cluster policy
```

---

# 235. CLI Safety

Destructive commands phải yêu cầu explicit confirmation/capability.

Script mode phải có:

```text
--non-interactive
```

với policy rõ ràng.

---

# 236. Cluster Graph

CLI có thể hiển thị:

```text
cluster
 ├── control plane
 ├── nodes
 ├── workloads
 ├── services
 ├── placements
 └── failure domains
```

---

# 237. AI Inspection

Compiler/runtime có thể xuất:

```text
axiom cluster inspect --format axcontrol
```

cho AI tooling.

---

# 238. AI Metadata Safety

AI-readable metadata không được chứa:

```text
private key
secret
token
credential
session cookie
```

---

# 239. Package Integration

635 package dependency:

```text
AXPK
service metadata
cluster metadata
node compatibility
```

Package installation vẫn do 625.

---

# 240. Plugin Integration

635 provider plugins có thể implement:

```text
MembershipProvider
ConsensusProvider
SchedulerProvider
CapacityProvider
TopologyProvider
```

Plugin được sandbox/capability-control bởi 603/623.

---

# 241. Hot Reload

Scheduler policies có thể hot reload.

Consensus provider replacement đang chạy không được hot swap tùy tiện.

---

# 242. Consensus Provider Upgrade

Provider upgrade phải có migration protocol.

Không thay đổi consensus semantics giữa chừng mà không có compatibility boundary.

---

# 243. Scheduler Provider Upgrade

Có thể thay scheduler algorithm mà không thay control-state schema.

Existing placements phải remain valid.

---

# 244. Placement Algorithm Version

Placement record có:

```text
algorithm_id
algorithm_version
```

để diagnostics/replay.

---

# 245. Reproducible Scheduling

Replay mode phải có:

```text
same input
same policy
same algorithm version
```

→ same result.

---

# 246. Control Replay

Committed control log có thể replay trong simulator.

---

# 247. Safety Properties

Các invariant bắt buộc:

1. stale leader cannot commit;
2. stale node generation cannot own new placement;
3. fencing token monotonically protects resource;
4. committed state is never treated as uncommitted;
5. uncommitted state is never treated as committed;
6. security constraints cannot be bypassed by scheduler scoring;
7. hard constraints cannot be overridden by soft preferences;
8. quota cannot be bypassed through placement;
9. duplicate command cannot create duplicate committed mutation;
10. expired lease cannot authorize protected mutation.

---

# 248. Additional Safety Invariants

11. at most one valid leader per term;
12. lower term cannot supersede higher term;
13. lower generation cannot supersede higher generation;
14. old placement cannot activate;
15. stale observation cannot overwrite newer observation;
16. control state machine is deterministic;
17. reconciliation is idempotent;
18. fencing is checked at mutation boundary;
19. node quarantine blocks protected operations;
20. control credentials never enter ordinary telemetry.

---

# 249. More Invariants

21. consensus provider is replaceable;
22. scheduler provider cannot alter security authority;
23. data plane cannot become control-plane authority implicitly;
24. event bus cannot substitute for consensus;
25. workload cannot grant cluster capability to itself;
26. resource accounting comes from 606;
27. device identity comes from 614;
28. service execution comes from 631;
29. process execution comes from 605;
30. distributed data authority comes from 628.

---

# 250. Performance Requirements

Target:

```text
leader read path: O(1) or bounded
lease validation: O(1)
generation validation: O(1)
fencing validation: O(1)
placement validation: O(number of constraints)
scheduler cycle: O(workloads × candidate_nodes)
```

Hot path phải tránh global locks.

---

# 251. Scheduler Performance

Scheduler phải hỗ trợ:

```text
incremental scheduling
cached node predicates
cached topology
resource snapshots
batch scheduling
parallel filtering
```

---

# 252. Membership Performance

Heartbeat handling phải:

```text
bounded
batchable
non-blocking
```

Không spawn unbounded task cho mỗi heartbeat.

---

# 253. Control Memory

All queues:

```text
bounded
quota-controlled
backpressure-aware
```

---

# 254. Binary Size

Minimal application không sử dụng distributed runtime không link:

```text
consensus
membership
scheduler
cluster storage
```

---

# 255. No Mandatory GC

635 không yêu cầu garbage collector.

Temporary control objects dùng:

```text
stack
arena
pool
owned value
generation-safe handle
```

---

# 256. No Raw Pointer API

Public distributed APIs không expose raw pointer ownership semantics.

---

# 257. Error Model

Errors phân loại:

```text
NotLeader
NoQuorum
LeaseExpired
Fenced
StaleGeneration
StaleRevision
NodeUnavailable
ResourceUnavailable
QuotaExceeded
PolicyDenied
PlacementConflict
ConsensusUnavailable
MembershipUnavailable
Timeout
Cancelled
Incompatible
```

---

# 258. Error Stability

Error code là stable ABI/schema.

Human message không phải machine contract.

---

# 259. Cancellation

Long-running control operation hỗ trợ:

```text
CancelToken
Deadline
Timeout
```

Cancellation không rollback committed consensus state.

---

# 260. Transaction Boundary

Control transaction:

```text
validate
→ propose
→ commit
→ apply
```

Không gọi network side effects bên trong deterministic state machine.

---

# 261. Side Effects

Side effect executor chạy sau commit.

Nếu crash:

```text
replay committed intent
```

và executor phải idempotent.

---

# 262. Outbox

Control state có thể dùng outbox semantics:

```text
committed command
→ durable outbox
→ event delivery
```

612/628/634 cung cấp primitives.

---

# 263. Eventual Executor Completion

Control plane không coi:

```text
command committed
```

là:

```text
workload execution successful
```

Hai trạng thái tách biệt.

---

# 264. Desired/Observed Separation

Bắt buộc:

```text
DesiredState
ObservedState
ControlState
```

không trộn thành một struct mutable duy nhất.

---

# 265. State Versioning

Mọi object quan trọng:

```text
generation
revision
```

phải có khi mutation concurrency có thể xảy ra.

---

# 266. Compare-And-Swap

Control mutations hỗ trợ:

```text
update_if_revision(...)
```

để tránh lost update.

---

# 267. Optimistic Concurrency

Default API có thể dùng:

```text
expected_revision
```

thay vì global lock.

---

# 268. Watch + CAS Pattern

Client:

```text
read revision 100
watch
modify expected=100
commit
```

Nếu revision đã thành 101:

```text
Conflict
```

---

# 269. Control Plane Testing Levels

Phải có:

```text
unit
property
model
integration
fault injection
stress
chaos
deterministic replay
cross-platform
```

---

# 270. Model Checking

Critical state machines:

```text
leader election
lease
fencing
membership
placement
reconciliation
```

nên có bounded model tests.

---

# 271. Race Testing

Kiểm tra:

```text
leader change
lease expiry
node failure
scheduler restart
placement activation
```

đồng thời.

---

# 272. Crash Testing

Crash points:

```text
before propose
after propose
before commit
after commit
before apply
after apply
before side effect
after side effect
```

---

# 273. Recovery Correctness

Mọi crash point phải reconstruct được:

```text
authoritative control state
```

mà không duplicate protected side effects.

---

# 274. Security Fuzzing

Fuzz:

```text
membership messages
consensus entries
lease tokens
placement requests
node labels
topology
control schemas
```

---

# 275. Resource Fuzzing

Fuzz:

```text
CPU=0
memory overflow
GPU count mismatch
negative-like encoded values
huge resource request
NaN/infinite floating values
```

Resource quantities phải dùng typed integer units khi có thể.

---

# 276. Network Fuzzing

Test:

```text
duplicate
reorder
truncate
delay
fragment
replay
corrupt
```

---

# 277. Security Replay Test

Old authenticated control message phải bị reject nếu:

```text
revision stale
term stale
generation stale
nonce/sequence invalid
```

---

# 278. Cross-Platform

Backends:

```text
Windows
Linux
macOS
Android
iOS
WASM
Embedded
```

Core semantics giữ nguyên.

---

# 279. Windows Backend

Có thể tích hợp:

```text
Job Objects
process handles
network stack
native synchronization
```

thông qua 605/607/609.

---

# 280. Linux Backend

Có thể tích hợp:

```text
cgroups
pidfd
epoll/io_uring
namespaces
scheduler APIs
```

nhưng không để Linux concepts leak vào portable API.

---

# 281. macOS Backend

Sử dụng:

```text
native process/network/device APIs
```

với security sandbox constraints.

---

# 282. Mobile Backend

Control runtime phải respect:

```text
background limits
network transitions
battery
process suspension
```

---

# 283. Embedded Backend

Có thể compile bỏ:

```text
consensus
dynamic membership
network
```

nếu profile không cần.

---

# 284. Profiles

Axiom định nghĩa:

```text
AXCLUSTER_NONE
AXCLUSTER_LOCAL
AXCLUSTER_MEMBERSHIP
AXCLUSTER_SCHEDULER
AXCLUSTER_CONTROL
AXCLUSTER_CONSENSUS
AXCLUSTER_DISTRIBUTED
AXCLUSTER_FULL
```

---

# 285. AXCLUSTER_NONE

Không có:

```text
membership
scheduler
consensus
cluster state
```

---

# 286. AXCLUSTER_LOCAL

Có:

```text
single-node control
local scheduler
local reconciliation
```

---

# 287. AXCLUSTER_MEMBERSHIP

Thêm:

```text
node identity
membership
health
topology
```

---

# 288. AXCLUSTER_SCHEDULER

Thêm:

```text
placement
resource-aware scheduling
reservations
```

---

# 289. AXCLUSTER_CONTROL

Thêm:

```text
leases
fencing
reconciliation
coordination
```

---

# 290. AXCLUSTER_CONSENSUS

Thêm:

```text
leader election
quorum
replicated control state
```

---

# 291. AXCLUSTER_DISTRIBUTED

Thêm integration:

```text
631
629
630
634
632
628
```

---

# 292. AXCLUSTER_FULL

Bao gồm toàn bộ provider/runtime integrations.

---

# 293. Generated Metadata

Compiler sinh tối thiểu:

```text
module.axcluster
cluster.axcluster
node.axnode
placement.axplacement
control.axcontrol
```

---

# 294. Metadata Example

Conceptual:

```text
cluster {
    id
    schema
    control_provider
    consensus_provider
    scheduler_provider
    security_policy
    resource_policy
    topology_policy
}
```

---

# 295. Inspection Tool

```text
axiom cluster inspect
axiom cluster explain
axiom cluster replay
axiom cluster validate
```

---

# 296. Validation Tool

`axiom cluster validate` phải kiểm tra:

```text
schema
membership
policy
resource units
placement constraints
security capabilities
provider compatibility
```

---

# 297. Replay Tool

```text
axiom cluster replay control.log
```

có thể tái tạo control state trong simulator.

---

# 298. Deterministic Replay Output

Replay phải có:

```text
state hash
revision
term
placement hash
```

để so sánh.

---

# 299. Acceptance Criteria

BOOTSTRAP-635 được coi là hoàn thành khi tối thiểu đạt các nhóm sau:

### Cluster
- [ ] Node identity có generation.
- [ ] Cluster có generation.
- [ ] Membership có lifecycle.
- [ ] Failure detector có hysteresis.
- [ ] Node admission có security validation.
- [ ] Stale node bị nhận diện.
- [ ] Quarantine hoạt động.
- [ ] Topology được version hóa.

### Consensus
- [ ] Leader election có term.
- [ ] Không có hai valid leaders cùng term.
- [ ] Stale leader không commit.
- [ ] Consensus provider là pluggable.
- [ ] Committed và uncommitted state tách biệt.
- [ ] Snapshot/recovery hoạt động.
- [ ] Membership change có safety semantics.

### Lease/Fencing
- [ ] Lease có generation.
- [ ] Lease expiry hoạt động.
- [ ] Fencing token tăng đơn điệu.
- [ ] Old token bị reject.
- [ ] Distributed lock có fencing.
- [ ] Leader handoff an toàn.

### Scheduler
- [ ] Workload model typed.
- [ ] Desired/observed state tách biệt.
- [ ] Hard constraints hoạt động.
- [ ] Soft constraints hoạt động.
- [ ] Affinity hoạt động.
- [ ] Anti-affinity hoạt động.
- [ ] Topology spreading hoạt động.
- [ ] Resource accounting dùng 606.
- [ ] GPU placement dùng 614/630.
- [ ] Quota enforcement hoạt động.
- [ ] Reservation atomic.
- [ ] Preemption có policy.
- [ ] Scheduler không bypass security.

### Placement
- [ ] Placement có generation.
- [ ] Placement có fencing token.
- [ ] Duplicate activation bị ngăn.
- [ ] Failed activation được recovery.
- [ ] Node drain hoạt động.
- [ ] Node evacuation hoạt động.
- [ ] Failed-node rescheduling hoạt động.
- [ ] Anti-thrashing hoạt động.

### Reconciliation
- [ ] Reconciler deterministic.
- [ ] Reconciler idempotent.
- [ ] Stale observation không overwrite state mới.
- [ ] Desired/actual convergence có kiểm thử.
- [ ] Side effects không nằm trong deterministic state machine.

### Integration
- [ ] 605 integration.
- [ ] 606 integration.
- [ ] 607/608 integration.
- [ ] 610 integration.
- [ ] 612 integration.
- [ ] 628 integration.
- [ ] 629 integration.
- [ ] 630 integration.
- [ ] 631 integration.
- [ ] 632 integration.
- [ ] 633 integration.
- [ ] 634 integration.

### Security
- [ ] Control operations dùng capability.
- [ ] Không có authority amplification.
- [ ] Control messages authenticated.
- [ ] Secrets không vào consensus log.
- [ ] Secrets không vào telemetry.
- [ ] Replay protection hoạt động.
- [ ] Quarantine hoạt động.

### Reliability
- [ ] Network partition test.
- [ ] Leader crash test.
- [ ] Scheduler crash test.
- [ ] Lease expiry test.
- [ ] Fencing test.
- [ ] Node generation test.
- [ ] Resource race test.
- [ ] Consensus recovery test.
- [ ] Deterministic replay test.
- [ ] Model-check critical state machines.

### Performance
- [ ] Hot-path không phụ thuộc global mutex.
- [ ] Membership processing bounded.
- [ ] Scheduler queues bounded.
- [ ] Control messages bounded.
- [ ] Heartbeat storms được kiểm soát.
- [ ] Election storms được kiểm soát.
- [ ] Minimal profile dead-strips distributed code.

Target tổng thể: **≥ 300 acceptance criteria**.

---

# 300. Architecture Boundary

Kiến trúc hoàn chỉnh:

```text
                    ┌───────────────────────────────┐
                    │        Axiom Applications     │
                    └───────────────┬───────────────┘
                                    │
                    ┌───────────────▼───────────────┐
                    │ 631 Distributed Service       │
                    │ 629 Workflow                  │
                    │ 630 Distributed Compute       │
                    │ 634 Event / Stream Runtime    │
                    │ 632 Gateway / Edge            │
                    └───────────────┬───────────────┘
                                    │
                    ┌───────────────▼───────────────┐
                    │       BOOTSTRAP-635            │
                    │                               │
                    │ Cluster Membership            │
                    │ Failure Detection             │
                    │ Leader Election               │
                    │ Consensus Boundary            │
                    │ Control State                 │
                    │ Lease / Fencing               │
                    │ Scheduler                     │
                    │ Placement                     │
                    │ Reconciliation                │
                    │ Coordination                  │
                    │ Node Drain / Recovery         │
                    └───────────────┬───────────────┘
                                    │
        ┌───────────────────────────┼────────────────────────────┐
        │                           │                            │
┌───────▼───────┐          ┌────────▼────────┐         ┌─────────▼────────┐
│ 628 Data      │          │ 606 Resources   │         │ 603 Security     │
│ Replication   │          │ Quotas/Budgets  │         │ Capabilities     │
└───────┬───────┘          └────────┬────────┘         └─────────┬────────┘
        │                           │                            │
        └───────────────────────────┼────────────────────────────┘
                                    │
                    ┌───────────────▼───────────────┐
                    │ 611 Storage / 612 Serialization│
                    │ 610 Crypto / 613 Package       │
                    │ 633 Observability / 634 Events │
                    └───────────────┬────────────────┘
                                    │
                    ┌───────────────▼───────────────┐
                    │       Native OS / Hardware    │
                    └───────────────────────────────┘
```

---

# 301. Final Design Decision

BOOTSTRAP-635 xác lập **Axiom Distributed Control Plane** theo nguyên tắc:

```text
Membership
    +
Consensus
    +
Leases/Fencing
    +
Resource-aware Scheduling
    +
Placement
    +
Reconciliation
    +
Coordination
```

là một runtime native độc lập.

Nó **không yêu cầu Kubernetes**, không ép Raft, không ép cloud provider và không biến scheduler thành một execution engine.

Boundary quan trọng nhất:

```text
635 decides
605 executes processes
631 executes services
629 executes workflows
630 executes distributed compute
634 transports events
628 stores distributed state
606 accounts resources
603 authorizes authority
633 observes the system
```

Điều này giữ cho Axiom có một control-plane đủ mạnh để xây dựng hệ thống phân tán lớn nhưng vẫn giữ được khả năng compile/dead-strip xuống một runtime rất nhỏ khi ứng dụng không cần distributed features.

**BOOTSTRAP-635: COMPLETE.**

**NEXT TASK: BOOTSTRAP-636 — Native Distributed Deployment, Rollout, Autoscaling, Canary, Blue/Green, Multi-Cluster Federation & Edge Orchestration Runtime 5.0**
:::

BOOTSTRAP-635 đã hoàn tất. Theo chuỗi tự động của Axiom, task kế tiếp là **BOOTSTRAP-636**.