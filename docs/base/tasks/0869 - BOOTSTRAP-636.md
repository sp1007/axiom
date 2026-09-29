Tiếp tục với **BOOTSTRAP-636**, mở rộng control-plane 635 thành lớp deployment/orchestration phân tán, nhưng vẫn giữ rõ ranh giới giữa **desired state, rollout policy, scheduler, runtime execution và multi-cluster federation**.

:::writing{variant="document" id="74163" title="AXIOM BOOTSTRAP-636 — Native Distributed Deployment, Rollout, Autoscaling, Canary, Blue/Green, Multi-Cluster Federation & Edge Orchestration Runtime 5.0"}
# BOOTSTRAP-636
# Native Distributed Deployment, Rollout, Autoscaling, Canary, Blue/Green, Multi-Cluster Federation & Edge Orchestration Runtime 5.0

**Status:** COMPLETE  
**Layer:** Distributed Deployment / Orchestration / Federation  
**Depends on:** BOOTSTRAP-600 → BOOTSTRAP-635  
**Primary dependencies:** 601, 602, 603, 605, 606, 609, 610, 612, 613, 625, 628, 629, 630, 631, 632, 633, 634, 635

---

# 1. Mục tiêu

BOOTSTRAP-636 định nghĩa native runtime cho:

- deployment;
- rollout;
- rollout planning;
- rolling update;
- blue/green deployment;
- canary deployment;
- traffic-weighted rollout;
- shadow deployment;
- staged deployment;
- rollback;
- pause/resume rollout;
- deployment health gates;
- autoscaling;
- horizontal scaling;
- vertical resource adjustment boundary;
- workload elasticity;
- cluster capacity coordination;
- multi-cluster deployment;
- cluster federation;
- edge orchestration;
- regional placement;
- disaster recovery orchestration;
- global service placement;
- deployment waves;
- maintenance orchestration.

636 xây dựng trên:

```text
635 = cluster authority + placement + reconciliation
636 = deployment intent + rollout strategy + elasticity + federation
```

---

# 2. Architectural Boundary

636 **không thay thế**:

```text
605 Process Supervisor
606 Resource Governor
629 Workflow
630 Distributed Compute
631 Distributed Service Runtime
632 Gateway
635 Cluster Control Plane
```

Thay vào đó:

```text
636 decides WHAT / WHEN / HOW to deploy
635 decides WHERE
631 decides HOW service runs
605 decides HOW process runs
606 enforces resources
632 controls edge traffic
```

---

# 3. Deployment Model

Deployment là một desired-state object.

```text
Deployment {
    deployment_id
    generation
    workload_spec
    target_scope
    strategy
    rollout_policy
    health_policy
    resource_policy
    traffic_policy
}
```

Deployment không trực tiếp spawn process.

---

# 4. Deployment Identity

```text
DeploymentId
DeploymentGeneration
ReleaseId
ReleaseGeneration
RevisionId
RolloutId
RolloutGeneration
WaveId
```

Mọi mutation phải có generation/revision.

---

# 5. Release Model

Một deployment có thể chứa nhiều release:

```text
Deployment
 ├── Release A
 ├── Release B
 └── Release C
```

Ví dụ:

```text
A = version 1.0
B = version 1.1
```

Release là immutable artifact reference.

---

# 6. Release Identity

```text
Release {
    release_id
    version
    package_hash
    schema_fingerprint
    build_id
    target
    architecture
}
```

Package hash lấy từ 613/625.

---

# 7. Immutable Release

Sau khi release được published:

```text
package_hash
version
build_id
schema
```

không được mutable.

Muốn thay đổi → tạo release mới.

---

# 8. Deployment Revision

Deployment revision biểu diễn desired state.

```text
Revision {
    revision_id
    release_id
    generation
    created_at
    policy_fingerprint
}
```

---

# 9. Deployment State

```text
Pending
Admitted
Preparing
RollingOut
Paused
Healthy
Degraded
Failed
RollingBack
RolledBack
Completed
Cancelled
```

---

# 10. Desired vs Actual

636 phải giữ riêng:

```text
DesiredDeployment
ObservedDeployment
RolloutState
```

Không được merge thành một mutable state object.

---

# 11. Deployment Controller

```text
trait DeploymentController<T> {
    observe(...)
    plan(...)
    validate(...)
    advance(...)
    pause(...)
    resume(...)
    rollback(...)
}
```

Controller phải deterministic trong cùng input state.

---

# 12. Deployment Admission

Trước rollout:

```text
release exists
package trusted
target compatible
security policy valid
resource policy valid
schema compatible
cluster capacity available
traffic policy valid
```

---

# 13. Artifact Verification

Release phải pass:

```text
signature verification
hash verification
publisher trust
platform compatibility
ABI compatibility
capability policy
```

qua 610/613/625.

---

# 14. Deployment Scope

Deployment có thể target:

```text
Node
Cluster
Region
Zone
FailureDomain
Federation
EdgeGroup
Global
```

---

# 15. Cluster Target

```text
ClusterTarget {
    cluster_id
    constraints
    required_capabilities
}
```

---

# 16. Multi-Cluster Target

```text
FederatedTarget {
    clusters
    regions
    topology_policy
    capacity_policy
}
```

636 không giả định mọi cluster giống nhau.

---

# 17. Deployment Strategy

Core strategies:

```text
Recreate
Rolling
BlueGreen
Canary
Shadow
Staged
OnDemand
```

Provider có thể bổ sung strategy.

---

# 18. Recreate

```text
old → stop → new
```

Đơn giản nhưng có thể gây downtime.

Runtime chỉ thực thi semantics; không đánh giá strategy.

---

# 19. Rolling Deployment

```text
old replicas
    ↓
replace batch
    ↓
wait health
    ↓
next batch
```

---

# 20. Rolling Parameters

```text
max_unavailable
max_surge
batch_size
min_ready
pause_between_batches
health_timeout
```

Các giá trị phải có bound.

---

# 21. Rolling Invariants

Không được vượt:

```text
max_unavailable
max_surge
```

trừ khi explicit emergency policy.

---

# 22. Blue/Green

Có hai release sets:

```text
Blue = current
Green = candidate
```

Traffic initially:

```text
Blue = 100%
Green = 0%
```

Sau validation:

```text
Blue = 0%
Green = 100%
```

---

# 23. Blue/Green Resource Requirement

Nếu giữ cả hai phiên bản đồng thời:

```text
capacity >= blue + green
```

Nếu không đủ capacity:

```text
deployment blocked
```

không tự phá resource limits.

---

# 24. Canary

Canary là rollout theo traffic hoặc workload percentage.

Ví dụ:

```text
candidate = 1%
candidate = 5%
candidate = 10%
candidate = 25%
candidate = 50%
candidate = 100%
```

Các bước là policy, không phải prediction.

---

# 25. Canary Dimension

Canary có thể phân chia theo:

```text
traffic
instances
regions
zones
tenants
headers
user cohorts
```

Nhưng targeting phải explicit.

---

# 26. Traffic Weight

636 chỉ phát hành desired traffic policy.

Actual routing do:

```text
632 Gateway
631 Service Runtime
```

thực hiện.

---

# 27. Canary Boundary

```text
636 = rollout intent
632 = edge traffic execution
631 = service routing execution
```

Không duplicate routing logic.

---

# 28. Shadow Deployment

Candidate nhận traffic copy nhưng response không được gửi cho user.

```text
Production
   ├── primary
   └── shadow
```

Shadow request phải được đánh dấu:

```text
shadow = true
```

---

# 29. Shadow Safety

Shadow workload không được tự động:

- mutate production state;
- send external side effects;
- charge external account;
- modify durable data.

Nếu muốn side effect phải có explicit capability/policy.

---

# 30. Staged Deployment

Deployment có waves:

```text
Wave 1
Wave 2
Wave 3
...
```

Mỗi wave có:

```text
targets
strategy
health_gate
pause_policy
```

---

# 31. Deployment Wave

```text
Wave {
    wave_id
    targets
    rollout_policy
    health_policy
}
```

---

# 32. Wave Ordering

Có thể:

```text
region-by-region
zone-by-zone
cluster-by-cluster
failure-domain-by-failure-domain
```

---

# 33. Failure Domain Safety

Deployment policy có thể yêu cầu:

```text
never update all replicas in same failure domain
```

---

# 34. Deployment Budget

Deployment budget là riêng với resource budget.

Ví dụ:

```text
max_parallel_clusters
max_parallel_nodes
max_unavailable
max_failure_rate
```

---

# 35. Rollout State Machine

```text
Pending
 ↓
Preparing
 ↓
Admitted
 ↓
RollingOut
 ├── Paused
 ├── Degraded
 └── Failed
 ↓
Completed
```

Rollback:

```text
RollingOut
   ↓
RollingBack
   ↓
RolledBack
```

---

# 36. Pause

Rollout có thể pause:

```text
manual
health
policy
capacity
security
dependency
```

Pause không tự rollback.

---

# 37. Resume

Resume phải revalidate:

```text
release
policy
capacity
cluster generation
traffic state
health
```

---

# 38. Cancel

Cancel semantics:

```text
before commit → stop
after partial rollout → policy-defined recovery
```

Không được gọi cancel là rollback.

---

# 39. Rollback

Rollback tạo desired revision mới trỏ về previous release.

Không sửa lịch sử release.

---

# 40. Rollback Target

Rollback có thể:

```text
previous_revision
explicit_revision
known_good_release
```

"previous" phải là immutable historical reference.

---

# 41. Rollback Safety

Rollback cũng phải chạy health gates.

Không mặc định giả định bản cũ luôn healthy.

---

# 42. Known-Good Release

Một release có thể được đánh dấu:

```text
KnownGood
```

nhưng designation phải được lưu như metadata có revision.

---

# 43. Deployment History

History gồm:

```text
release
revision
strategy
start
end
state
policy
result
```

Không lưu secret.

---

# 44. Health Gate

Health gate có thể kiểm tra:

```text
readiness
error rate
latency
resource pressure
crash rate
availability
custom health signal
```

Metrics lấy từ 633.

---

# 45. Health Gate Semantics

Health gate không phải machine-learning predictor.

Chỉ evaluate documented conditions.

---

# 46. Threshold

Ví dụ:

```text
error_rate < threshold
latency_p95 < threshold
ready_instances >= threshold
```

Threshold có thời gian quan sát.

---

# 47. Observation Window

```text
HealthWindow {
    duration
    minimum_samples
    aggregation
}
```

Không quyết định rollout từ một sample duy nhất nếu policy yêu cầu nhiều sample.

---

# 48. Consecutive Failures

Policy có thể yêu cầu:

```text
N consecutive failures
```

trước pause/rollback.

---

# 49. Health Recovery

Sau failure:

```text
candidate unhealthy
→ pause
→ observe recovery
→ resume
```

nếu policy cho phép.

---

# 50. Rollout Failure

Deployment failure phải có reason code:

```text
InsufficientCapacity
HealthGateFailed
ArtifactUnavailable
SecurityDenied
CompatibilityFailed
SchedulingFailed
TrafficPolicyFailed
Timeout
DependencyUnavailable
ClusterUnavailable
```

---

# 51. Rollout Explain

CLI:

```text
axiom deploy explain DEPLOYMENT
```

phải trả:

```text
current revision
candidate revision
current phase
blocked reason
health gate
placement state
traffic state
next permitted transition
```

---

# 52. Rollout Plan

Trước mutation có thể tạo:

```text
DeploymentPlan
```

gồm:

```text
targets
waves
placements
traffic transitions
health gates
rollback target
resource impact
```

---

# 53. Dry Run

```text
axiom deploy plan APP --dry-run
```

không thay đổi cluster state.

---

# 54. Plan Determinism

Cùng:

```text
cluster snapshot
deployment spec
policy
release
```

→ deterministic plan nếu provider deterministic.

---

# 55. Deployment Commit

Plan được commit thành immutable rollout revision.

Sau commit executor bắt đầu side effects.

---

# 56. Rollout Controller

Controller loop:

```text
observe
→ evaluate
→ plan
→ commit intent
→ execute
→ observe
```

---

# 57. Execution Boundary

Execution sử dụng:

```text
635 Placement
631 Service
605 Process
```

636 không tự spawn process.

---

# 58. Deployment Executor

```text
trait DeploymentExecutor {
    prepare(...)
    activate(...)
    drain(...)
    deactivate(...)
}
```

---

# 59. Prepare

Prepare có thể:

```text
download package
verify package
warm cache
allocate resources
initialize configuration
```

---

# 60. Activate

Activate:

```text
placement active
service starts
readiness published
traffic eligibility enabled
```

---

# 61. Drain

Drain:

```text
stop new requests
wait active work
close connections
stop instance
```

631/632 chịu traffic semantics.

---

# 62. Grace Period

Deployment policy có:

```text
graceful_shutdown_timeout
```

---

# 63. Force Termination

Chỉ dùng nếu:

```text
grace expired
explicit policy
capability authorized
```

605 thực hiện actual termination.

---

# 64. Deployment Dependencies

Deployment có thể khai báo:

```text
requires_service
requires_schema
requires_package
requires_cluster_capability
requires_device
```

---

# 65. Dependency Ordering

Ví dụ:

```text
database schema
→ service
→ gateway
```

636 tạo dependency DAG.

---

# 66. Dependency Cycle

Cycle phải được phát hiện trước rollout:

```text
A → B
B → A
```

→ `DependencyCycle`.

---

# 67. Dependency Readiness

Dependency phải đạt required readiness level.

Không chỉ kiểm tra process Running.

---

# 68. Schema Compatibility

Deployment phải kiểm tra 612 schema compatibility.

Ví dụ:

```text
reader old
writer new
```

chỉ được phép nếu schema contract cho phép.

---

# 69. Expand/Contract Migration

Database/service migrations có thể dùng pattern:

```text
expand
→ dual compatible
→ migrate
→ switch
→ contract
```

636 chỉ orchestrates phases.

Migration logic thuộc application/workflow.

---

# 70. Migration Safety

636 không tự sửa dữ liệu.

---

# 71. Autoscaling

636 định nghĩa scaling control-plane.

Autoscaling không phải prediction engine.

Nó phản ứng với observed signals.

---

# 72. Autoscaler Model

```text
Autoscaler {
    target
    min
    max
    metric
    policy
    cooldown
}
```

---

# 73. Scaling Dimensions

Có thể scale:

```text
instances
CPU allocation
memory allocation
GPU allocation
worker count
partition consumers
cluster capacity
```

Vertical resource scaling phải tuân thủ provider capability.

---

# 74. Horizontal Scaling

HPA-like semantics:

```text
desired_instances = function(observed_metric)
```

Function phải deterministic và bounded.

---

# 75. Scaling Metric

Metrics có thể từ:

```text
CPU
memory
queue depth
request rate
latency
event lag
workflow backlog
custom metric
```

---

# 76. Metric Source

633 là telemetry authority.

634 có thể cung cấp:

```text
consumer lag
partition backlog
```

628:

```text
replica/storage metrics
```

---

# 77. Metric Freshness

Autoscaler phải biết:

```text
sample timestamp
aggregation window
freshness
```

Stale metrics có thể bị reject.

---

# 78. Scale-Up

Scale-up policy có thể có:

```text
step
percentage
target_utilization
absolute_delta
```

---

# 79. Scale-Down

Scale-down phải có:

```text
cooldown
stability window
minimum residency
```

để tránh thrashing.

---

# 80. Scale Limits

Mọi scaling action phải obey:

```text
min
max
quota
capacity
security
```

---

# 81. Scale Rate Limit

Không cho phép:

```text
1 → 10000 instances
```

trong một bước nếu policy không explicit.

---

# 82. Scaling Cooldown

Sau scale operation:

```text
cooldown
```

trước action tiếp theo nếu policy yêu cầu.

---

# 83. Scaling Hysteresis

Ví dụ:

```text
scale up > 70%
scale down < 30%
```

giảm oscillation.

---

# 84. Predictive Scaling Boundary

Predictive scaling có thể là provider.

Core 636 không đưa ra forecast riêng.

---

# 85. Multi-Metric Scaling

Có thể kết hợp:

```text
CPU
AND
queue
```

hoặc:

```text
CPU
OR
latency
```

Semantics phải explicit.

---

# 86. Scaling Policy

```text
ScalingPolicy {
    min
    max
    target
    metrics
    behavior
    cooldown
    stabilization
}
```

---

# 87. Autoscaler State

```text
Idle
Observing
ScalingUp
CoolingDown
ScalingDown
Blocked
Failed
```

---

# 88. Autoscaling + Scheduler

Flow:

```text
633 metrics
 ↓
636 autoscaler
 ↓
desired instances
 ↓
635 scheduler
 ↓
placements
 ↓
631 service
```

---

# 89. Autoscaling + Event Runtime

634 lag:

```text
partition lag ↑
```

→ autoscaler may increase consumers.

---

# 90. Autoscaling + Workflow

629 backlog:

```text
pending activities ↑
```

→ worker count may scale.

---

# 91. Autoscaling + Compute

630 pending jobs:

```text
queue ↑
```

→ capacity provider may request more nodes.

---

# 92. Capacity Scaling

Cluster-level scaling:

```text
desired_capacity
```

may be passed to:

```text
CapacityProvider
```

---

# 93. Capacity Provider

```text
trait CapacityProvider {
    request_capacity(...)
    release_capacity(...)
    observe_capacity(...)
}
```

External cloud APIs are adapters.

---

# 94. Node Provisioning

Provisioning states:

```text
Requested
Provisioning
Joining
Validating
Ready
Failed
Released
```

---

# 95. Node Provisioning Security

New nodes require:

```text
identity
attestation if configured
certificate
cluster admission
capability policy
```

---

# 96. Cluster Capacity Safety

Do not count:

```text
requested node
```

as:

```text
ready capacity
```

until node reaches Ready.

---

# 97. Multi-Cluster Federation

Federation connects multiple independent clusters.

```text
Federation
 ├── Cluster A
 ├── Cluster B
 ├── Cluster C
 └── Cluster D
```

---

# 98. Cluster Authority

Each cluster retains its own:

```text
leader
consensus
membership
security boundary
scheduler
```

Federation does not collapse them into one global consensus domain.

---

# 99. Federation Identity

```text
FederationId
ClusterId
ClusterGeneration
TrustDomain
```

---

# 100. Federation Membership

```text
FederatedCluster {
    cluster_id
    endpoint
    region
    capabilities
    capacity
    health
    trust
}
```

---

# 101. Federation Health

Cluster states:

```text
Healthy
Degraded
Unavailable
Partitioned
Joining
Leaving
Quarantined
```

---

# 102. Cross-Cluster Trust

Federation uses:

```text
603 capabilities
610 cryptography
627 identity
```

---

# 103. No Implicit Trust

Cluster A membership does not imply cluster B authority.

---

# 104. Federated Deployment

Deployment can target:

```text
all eligible clusters
subset
specific regions
specific capabilities
```

---

# 105. Federation Placement

Global scheduler may choose cluster based on:

```text
capacity
topology
latency metadata
data locality
policy
cost metadata
health
capabilities
```

No hidden cloud-specific assumptions.

---

# 106. Federation Scheduler

```text
FederationScheduler
```

produces:

```text
ClusterPlacement
```

Then local 635 scheduler produces:

```text
NodePlacement
```

---

# 107. Two-Level Scheduling

```text
Global:
Federation
   ↓
Cluster

Local:
Cluster
   ↓
Node
```

---

# 108. Federation Failure

If cluster B unavailable:

```text
global desired state remains
cluster B actual state unavailable
```

Do not immediately assume workload is lost.

---

# 109. Failover Policy

Failover can be:

```text
Disabled
Manual
Automatic
PriorityOrdered
CapacityAware
```

---

# 110. Failover Safety

Failover must consider:

```text
duplicate execution
data consistency
identity
fencing
state replication
traffic routing
```

---

# 111. Active/Passive

Supported:

```text
Primary cluster
Secondary cluster
```

Secondary may be:

```text
Warm
Cold
Hot
```

---

# 112. Active/Active

Multiple clusters may actively serve.

Requires explicit:

```text
traffic routing
data consistency
conflict policy
identity
```

---

# 113. Data Dependency

636 must not assume cross-cluster data is immediately consistent.

628 defines actual consistency.

---

# 114. Cross-Cluster State

Can use:

```text
628 replication
634 events
```

but deployment state remains controlled by federation policy.

---

# 115. Edge Orchestration

Edge group:

```text
EdgeGroup {
    id
    clusters
    topology
    connectivity
    capacity
}
```

---

# 116. Edge Characteristics

Edge may have:

```text
intermittent network
limited storage
limited CPU
limited GPU
high latency
temporary disconnection
```

---

# 117. Edge Deployment

Deployment can specify:

```text
required_edge_labels
minimum_edge_count
local_only
offline_capable
```

---

# 118. Offline Deployment

An edge cluster can continue local execution while disconnected if its cached desired state remains valid.

---

# 119. Offline Authority

Disconnected edge cluster cannot claim global authority.

It can continue only operations permitted by its delegated authority.

---

# 120. Delegated Authority

Federation can issue:

```text
DelegatedControlLease
```

containing:

```text
scope
permissions
expiry
fencing epoch
```

---

# 121. Authority Expiry

After delegation expires:

```text
global mutations blocked
```

unless renewed.

---

# 122. Edge Reconciliation

After reconnect:

```text
local state
↕
federation desired state
```

Differences become explicit conflicts.

---

# 123. Federation Conflict

Possible:

```text
LocalChanged
GlobalChanged
BothChanged
VersionConflict
PolicyConflict
```

---

# 124. Conflict Resolution

Resolution policies:

```text
GlobalWins
LocalWins
ExplicitApproval
RevisionBased
PolicyBased
```

No universal winner is assumed.

---

# 125. Edge Split-Brain

Two disconnected clusters must not both possess unrestricted global mutation authority.

Delegated fencing/epochs prevent this.

---

# 126. Regional Deployment

A deployment can define:

```text
region waves
```

Example:

```text
Region A
→ health gate
→ Region B
→ health gate
→ Region C
```

---

# 127. Global Rollout

Global rollout is composed of local rollouts:

```text
Federation controller
 ↓
cluster rollout
 ↓
local 636
 ↓
635 placement
```

---

# 128. Federation Rollout State

```text
Pending
Preparing
WaveActive
WavePaused
WaveFailed
Completed
RollingBack
```

---

# 129. Cross-Cluster Rollback

Rollback may target:

```text
all clusters
affected clusters only
failed wave
specific cluster
```

Policy must be explicit.

---

# 130. Federation Rollback Safety

A cluster already on new release must not silently downgrade merely because another cluster failed.

Rollback scope is explicit.

---

# 131. Global Health Gate

Can aggregate:

```text
cluster health
deployment health
traffic health
data replication health
```

from 633/628.

---

# 132. Regional Health Gate

Allows:

```text
region-specific threshold
```

without treating regional metrics as globally representative.

---

# 133. Traffic Steering

636 publishes desired traffic distribution.

632 executes edge routing.

Example:

```text
Cluster A = 70%
Cluster B = 30%
```

---

# 134. DNS Boundary

DNS integration is provider-level.

636 does not implement authoritative DNS.

---

# 135. Global Load Balancing

Can integrate with:

```text
632 Gateway
external DNS
Anycast provider
provider-specific edge
```

---

# 136. Multi-Region Failover

When region unavailable:

```text
traffic policy
→ alternate region
```

must verify:

```text
capacity
health
data consistency
security
```

---

# 137. Disaster Recovery

636 can orchestrate DR:

```text
Prepare
Replicate
Validate
Promote
Route
Verify
```

---

# 138. DR State

```text
Primary
Standby
Recovering
Promoting
Active
Demoting
Failed
```

---

# 139. DR Does Not Equal Backup

Backup remains 611/612/613/628 concern.

636 orchestrates recovery sequence.

---

# 140. Recovery Point

DR policy may specify:

```text
maximum tolerated replication lag
```

based on 628.

---

# 141. Recovery Time

DR policy may specify:

```text
activation deadline
```

but actual ability depends on capacity and providers.

---

# 142. DR Fencing

Before promotion:

```text
old primary must be fenced
```

if split-brain could create conflicting writes.

---

# 143. Global Lease

Cross-cluster active ownership may use:

```text
FederationLease
```

with fencing.

---

# 144. Deployment Lock

A deployment can acquire:

```text
DeploymentLock
```

to prevent conflicting rollout controllers.

---

# 145. Lock Scope

Locks can cover:

```text
deployment
cluster
region
service
workload
```

---

# 146. No Global Lock Requirement

Federation should not require a single global lock for all deployments.

Locks are scoped.

---

# 147. Concurrent Deployments

Two independent deployments may run concurrently if their resource/security scopes do not conflict.

---

# 148. Conflict Detection

Conflict dimensions:

```text
same workload
same service
same cluster
same resource
same traffic route
same schema
```

---

# 149. Deployment Priority

Priority can resolve scheduling order, but not override safety/security.

---

# 150. Deployment Queue

Federated controller has:

```text
Pending
Admitted
Running
Blocked
Completed
Failed
```

---

# 151. Deployment Backpressure

Must bound:

```text
simultaneous rollouts
cluster operations
capacity requests
traffic changes
```

---

# 152. Autoscaler + Deployment

During rollout, autoscaler must know:

```text
surge capacity
candidate capacity
rollback capacity
```

so it does not accidentally scale down required rollout resources.

---

# 153. Deployment Resource Reservation

A rollout can reserve temporary:

```text
surge CPU
surge memory
surge GPU
```

through 606.

---

# 154. Rollout + Quota

Surge resources count against quota unless explicit policy grants temporary quota.

---

# 155. Autoscaling During Canary

Autoscaler must distinguish:

```text
stable workload
candidate workload
shadow workload
```

to avoid metric contamination.

---

# 156. Metric Attribution

633 telemetry labels include:

```text
release_id
revision_id
deployment_id
cluster_id
```

---

# 157. Canary Metric Isolation

Candidate metrics must be separately observable.

---

# 158. Traffic-Based Autoscaling

If enabled, autoscaler must define whether:

```text
total traffic
candidate traffic
stable traffic
```

drives scaling.

No implicit assumption.

---

# 159. Deployment and Event Consumers

For 634 consumers:

```text
old release
new release
```

consumer-group migration must preserve offset semantics.

---

# 160. Consumer Rollout

Strategies:

```text
replace
parallel
partition handoff
shadow
```

---

# 161. Partition Safety

Two consumer generations must not both own the same partition unless 634 semantics explicitly allow it.

---

# 162. Workflow Worker Rollout

629 workers may roll independently.

Existing activity leases remain valid until:

```text
completed
expired
cancelled
```

---

# 163. Compute Worker Rollout

630 workers may drain before replacement.

In-flight jobs follow 629/630 retry semantics.

---

# 164. Service Rollout

631 readiness is required before a new service instance is considered available.

---

# 165. Gateway Rollout

632 route state must remain consistent during gateway replacement.

---

# 166. Certificate Rollout

610 certificates can be rotated independently.

636 can orchestrate:

```text
prepare
deploy
verify
retire old
```

---

# 167. Configuration Rollout

601 configuration snapshots can be versioned.

Deployment can bind:

```text
release
config fingerprint
secret reference version
```

---

# 168. Secret Rotation

636 never copies secret values into rollout state.

It references:

```text
SecretId
SecretVersion
```

---

# 169. Package Rollout

613/625 package hashes identify exact release content.

---

# 170. Content Addressability

Deployment state should prefer:

```text
package_hash
content_hash
```

over mutable download URLs.

---

# 171. Reproducibility

Deployment manifest should contain:

```text
source identity
build id
package hash
schema fingerprint
compiler version
target
```

where available.

---

# 172. Deployment Manifest

Axiom format:

```text
AXDEP
```

Logical fields:

```text
deployment
release
target
strategy
resources
security
health
traffic
scaling
rollback
federation
```

---

# 173. AI-Readable Deployment Metadata

Generated:

```text
.axdeploy
.axrelease
.axrollout
.axscale
.axfederation
```

---

# 174. Deployment Compiler Metadata

Annotations:

```text
@deployment
@release
@rollout
@rolling
@blue_green
@canary
@shadow
@wave
@health_gate
@rollback
@autoscale
@federation
@edge
@dr
```

---

# 175. Compile-Time Checks

Compiler/tooling validates:

```text
invalid target
invalid strategy
invalid resource
invalid health metric
invalid dependency
invalid rollout transition
invalid federation scope
```

---

# 176. Deployment Schema Evolution

Manifest schema evolves through 612.

Old deployment definitions can be migrated explicitly.

---

# 177. No Hidden Migration

Axiom does not silently mutate deployment specifications during upgrade.

---

# 178. Rollout State Persistence

636 state uses:

```text
612 serialization
628 replicated storage
611 durable storage
```

---

# 179. Controller Recovery

After controller crash:

```text
restore rollout state
observe actual state
rebuild plan
continue safely
```

---

# 180. Controller Idempotency

Repeated:

```text
advance()
```

must not produce duplicate activation.

---

# 181. Controller Leadership

Multiple deployment controllers may run.

635 leader/lease/fencing semantics prevent conflicting authority.

---

# 182. Controller Sharding

Deployments can be sharded by:

```text
deployment_id
cluster_id
tenant_id
region
```

---

# 183. Federation Controller Sharding

Large federation can shard by:

```text
region
cluster group
tenant
deployment
```

---

# 184. Control-Plane Scaling

636 must avoid one global serialized deployment loop.

Independent deployment scopes should progress independently.

---

# 185. Deployment Event Stream

636 emits:

```text
DeploymentCreated
RolloutStarted
WaveStarted
InstanceActivated
HealthGatePassed
HealthGateFailed
RolloutPaused
RolloutResumed
RollbackStarted
RollbackCompleted
DeploymentCompleted
DeploymentFailed
ScaleRequested
ScaleCompleted
ClusterTargetChanged
```

via 634.

---

# 186. Event Semantics

Events are notifications, not authoritative deployment state.

Authoritative state remains 636/635.

---

# 187. Audit

Every administrative mutation records:

```text
identity
capability
deployment
revision
timestamp
reason
result
```

---

# 188. Privacy

Do not log:

```text
secret values
private keys
tokens
credentials
```

---

# 189. Tenant Isolation

Tenant deployments are isolated by:

```text
capabilities
quota
namespace
resource policy
cluster scope
```

---

# 190. Namespace

636 can expose:

```text
DeploymentNamespace
```

for logical isolation.

Namespace is not itself a security boundary; capabilities still enforce authority.

---

# 191. Cross-Tenant Placement

Scheduler must not place workloads across tenants if policy forbids it.

---

# 192. Tenant Rollout Limits

Policy may define:

```text
max concurrent deployments
max cluster targets
max surge
max capacity request
```

---

# 193. Rate Limiting

636 administrative APIs use 606/631/632 resource controls.

---

# 194. Deployment API

```text
struct DeploymentManager {
    controller
}

fn DeploymentManager.create(...)
fn DeploymentManager.plan(...)
fn DeploymentManager.start(...)
fn DeploymentManager.pause(...)
fn DeploymentManager.resume(...)
fn DeploymentManager.cancel(...)
fn DeploymentManager.rollback(...)
fn DeploymentManager.status(...)
```

---

# 195. Autoscaler API

```text
struct Autoscaler {
    policy
}

fn Autoscaler.observe(...)
fn Autoscaler.evaluate(...)
fn Autoscaler.scale(...)
```

---

# 196. Federation API

```text
struct FederationManager {
    registry
}

fn FederationManager.register(...)
fn FederationManager.remove(...)
fn FederationManager.deploy(...)
fn FederationManager.failover(...)
fn FederationManager.status(...)
```

---

# 197. Edge API

```text
struct EdgeOrchestrator {
    federation
}

fn EdgeOrchestrator.deploy(...)
fn EdgeOrchestrator.sync(...)
fn EdgeOrchestrator.reconcile(...)
fn EdgeOrchestrator.promote(...)
```

---

# 198. Rollout API

```text
struct Rollout {
    rollout_id
}

fn Rollout.start(...)
fn Rollout.pause(...)
fn Rollout.resume(...)
fn Rollout.rollback(...)
fn Rollout.status(...)
```

---

# 199. Struct-Only Design

Không cần:

```text
DeploymentManagerClass
CanaryControllerClass
FederationControllerClass
```

Tất cả là structs + functions + traits.

---

# 200. Resource Ownership

Deployment objects own configuration/state references.

Runtime resources remain owned by:

```text
635
631
605
606
```

---

# 201. No Raw Pointer

Public deployment APIs không expose raw pointer ownership.

---

# 202. Memory Management

636 không cần GC.

State containers dùng:

```text
owned values
immutable snapshots
arena
pool
generation handles
```

---

# 203. Async

Deployment operations là async:

```text
async deploy(...)
async rollout(...)
async rollback(...)
async scale(...)
```

Compiler lower qua 607.

---

# 204. Cancellation

Cancel signal phải propagate tới:

```text
deployment controller
placement
service activation
traffic transition
capacity request
```

nhưng không undo committed consensus entries.

---

# 205. Timeout

Mọi remote phase có:

```text
deadline
```

---

# 206. Retry

Retries phải có:

```text
bounded retry
backoff
jitter
idempotency
```

---

# 207. Retry Scope

Retry riêng cho:

```text
artifact download
node provisioning
placement
activation
health observation
traffic update
```

Không retry toàn bộ deployment mù quáng.

---

# 208. Retry Storm Prevention

Global and per-deployment retry budgets.

---

# 209. Failure Domains

Rollout policy có:

```text
max simultaneous failure domains
```

---

# 210. Zone-Aware Rolling

Ví dụ:

```text
zone A
→ health
→ zone B
→ health
→ zone C
```

---

# 211. Rack-Aware Rolling

Tương tự zone nhưng ở rack level.

---

# 212. Cluster-Aware Rolling

Federated rollout:

```text
cluster A
→ cluster B
→ cluster C
```

---

# 213. Region-Aware Rolling

```text
region A
→ region B
→ region C
```

---

# 214. Global Stop Condition

Rollout có thể stop nếu:

```text
failure rate
health gate
capacity failure
security violation
```

vượt policy.

---

# 215. Global Pause

Pause tất cả future waves.

Current already-committed work vẫn theo lifecycle rules.

---

# 216. Rollout Resume After Controller Restart

State được load từ durable store.

Controller không tự assume previous action failed.

Nó kiểm tra actual state trước khi retry.

---

# 217. Two-Phase Activation

Optional:

```text
prepare
commit activation
```

Useful cho:

```text
multi-service coordinated rollout
```

---

# 218. Activation Barrier

Một group có thể yêu cầu:

```text
all prepared
→ barrier
→ activate
```

---

# 219. Barrier Failure

Nếu một member fail:

```text
abort before activation
```

nếu chưa commit.

Sau commit:

```text
compensating recovery
```

---

# 220. Deployment Transactions

Không tuyên bố distributed transaction cho toàn bộ deployment.

Deployment coordination sử dụng:

```text
intent
barrier
reconciliation
compensation
```

---

# 221. Saga Boundary

629 có thể orchestrate complex deployment workflows.

636 cung cấp deployment primitives.

---

# 222. Human Approval

Optional gate:

```text
AwaitApproval
```

UI/CLI qua 619/622.

---

# 223. Approval Security

Approval là signed/audited control action.

---

# 224. Manual Rollback

Operator có thể yêu cầu rollback nếu có capability.

---

# 225. Automatic Rollback

Chỉ khi deployment policy bật.

Trigger:

```text
health gate
availability
crash rate
```

---

# 226. Automatic Rollback Safety

Rollback phải không tạo:

```text
rollback loop
```

Có rollback budget.

---

# 227. Rollback Loop Prevention

Ví dụ:

```text
A → B
B fails → A
A fails again
```

Controller phải stop thay vì infinite oscillation.

---

# 228. Deployment Stabilization

Sau successful rollout:

```text
stabilization_window
```

trước khi coi rollout fully healthy nếu policy yêu cầu.

---

# 229. Stable Revision

Một revision có thể chuyển:

```text
Candidate
→ Stable
```

sau health window.

---

# 230. Revision Retention

Old revisions có retention:

```text
count
age
known-good
manual pin
```

---

# 231. Rollback Availability

Revision chỉ rollback được nếu:

```text
artifact available
schema compatible
target compatible
security valid
```

---

# 232. Garbage Collection Boundary

Release artifacts có thể được reclaim bởi 613/625.

636 chỉ giữ references.

---

# 233. Artifact Pinning

Active/rollback-eligible releases được pin.

---

# 234. Deployment Artifact Lifecycle

```text
Referenced
Pinned
Unreferenced
EligibleForGC
Deleted
```

---

# 235. Autoscaling and Artifact Cache

Scaling up may require package fetch.

Scheduler may prefer nodes with artifact cached.

---

# 236. Cold Start

Autoscaler can expose:

```text
estimated activation duration
```

as provider metadata.

Không phải prediction bắt buộc.

---

# 237. Warm Pool

Capacity provider may maintain warm nodes.

---

# 238. Warm Pool Security

Warm nodes still require valid:

```text
identity
generation
security policy
```

---

# 239. Scale-to-Zero

Optional:

```text
min_instances = 0
```

Workload activation can be event/request triggered.

---

# 240. Scale-from-Zero

Trigger sources:

```text
request
event
schedule
workflow
manual
```

---

# 241. Scale-to-Zero Safety

Stateful services require explicit drain/persistence policy.

---

# 242. Stateful Deployment

Stateful workloads may require:

```text
stable identity
persistent storage
replica placement
ordered startup
```

628/611 own state semantics.

---

# 243. Stateful Rolling

Policy can specify:

```text
one replica at a time
quorum-aware
leader-first
follower-first
```

---

# 244. Database Deployment Boundary

636 does not implement database internals.

It coordinates 628 stateful replicas.

---

# 245. Leader-Aware Deployment

For service/database with leader:

```text
identify leader
prepare follower
handoff
replace leader
```

using 635/628 provider semantics.

---

# 246. Leadership Handoff

636 cannot assume all services support handoff.

Capability must be explicit.

---

# 247. Quorum-Aware Deployment

Before removing replica:

```text
remaining replicas >= required quorum
```

---

# 248. Event Consumer Quorum

634 consumer groups have their own semantics; 636 must use 634 API rather than inventing consumer ownership.

---

# 249. Deployment of Event Processor

Canary consumer may use:

```text
new consumer group
shadow processing
partition subset
```

according to 634.

---

# 250. Deployment of Workflow Workers

Worker version routing through 629:

```text
worker version
task queue
compatibility
```

---

# 251. Version Compatibility

Task queue can require:

```text
minimum worker version
maximum worker version
```

---

# 252. Deployment of Compute Workers

630 job compatibility determines worker eligibility.

---

# 253. GPU Rollout

GPU workloads require:

```text
device compatibility
driver compatibility
GPU capability
artifact compatibility
```

---

# 254. Driver Boundary

636 does not install arbitrary kernel drivers.

Device management belongs to 614/OS/platform layer.

---

# 255. Security Policy Rollout

Security policies can be rolled independently.

Order:

```text
prepare policy
validate
activate
deploy workload
```

or explicit reverse compatibility strategy.

---

# 256. Capability Migration

New release requiring new capability must pass admission before rollout.

---

# 257. Least Privilege

Deployment cannot grant capabilities merely because the new binary requests them.

Policy must explicitly permit.

---

# 258. Capability Diff

Deployment plan should expose:

```text
added capabilities
removed capabilities
changed capability scopes
```

---

# 259. ABI Diff

Deployment tooling should expose:

```text
API changes
ABI changes
schema changes
resource changes
capability changes
```

---

# 260. Deployment Compatibility Report

```text
axiom deploy diff OLD NEW
```

returns structured differences.

---

# 261. AI-Friendly Diff

Output:

```text
release
API
ABI
schema
resource
security
placement
traffic
```

without requiring prose parsing.

---

# 262. Federation Compatibility

Before multi-cluster rollout, verify each target cluster's:

```text
runtime version
platform
architecture
provider capability
schema version
security policy
```

---

# 263. Partial Compatibility

Deployment can target only compatible clusters.

Incompatible clusters produce explicit result.

---

# 264. Federation Enrollment

Cluster joining federation:

```text
identity validation
trust establishment
capability negotiation
schema negotiation
health validation
```

---

# 265. Capability Negotiation

Example:

```text
supports_gpu
supports_blue_green
supports_http3
supports_hardware_keys
```

---

# 266. Feature Negotiation

Features are explicit:

```text
FeatureId
Version
Provider
```

---

# 267. No Silent Downgrade

If feature unavailable:

```text
deployment blocked
```

unless fallback is explicit.

---

# 268. Fallback Policy

```text
Require
Prefer
Optional
```

---

# 269. Edge Capability Negotiation

Edge nodes may advertise limited capabilities.

---

# 270. Offline Package Distribution

613/625 package cache can pre-stage releases to edge.

---

# 271. Edge Preloading

636 can request:

```text
preload package
preload model
preload configuration
```

before rollout.

---

# 272. Offline Rollout

Edge rollout may execute locally from previously committed deployment intent.

---

# 273. Offline Rollout Authority

Offline deployment must carry a valid:

```text
delegation epoch
expiry
scope
fencing token
```

---

# 274. Edge Reconnect

Upon reconnect:

```text
validate epoch
upload observed state
reconcile
resolve conflicts
```

---

# 275. Edge Conflict Audit

All divergent changes must be recorded.

---

# 276. Federation Clock

Cross-cluster coordination should use:

```text
logical revisions
fencing epochs
```

rather than relying solely on synchronized wall clocks.

---

# 277. Global Revision

Optional federation-level revision:

```text
FederationRevision
```

It is not a replacement for each cluster's local consensus revision.

---

# 278. Federation Event Ordering

No global total ordering is assumed unless provider explicitly supplies one.

---

# 279. Federation Data Consistency

Deployment state may be eventually consistent between clusters.

Safety-critical local actions remain governed by local cluster authority.

---

# 280. Global Control State

Only metadata requiring federation-level coordination belongs in global control state.

Bulk state remains in 628/611.

---

# 281. Global Control Storage

May use:

```text
628 replicated store
612 schemas
610 cryptography
```

---

# 282. Federation Failover

Failover controller must ensure:

```text
old authority fenced
new authority valid
data state compatible
traffic route updated
```

---

# 283. Deployment SLO Metadata

636 can store descriptive targets:

```text
availability_target
rollout_deadline
max_unavailable
```

It does not independently declare whether an SLO has been achieved; 633 provides measurements.

---

# 284. Observability Integration

Each rollout span contains:

```text
deployment_id
release_id
revision_id
rollout_id
wave_id
cluster_id
```

---

# 285. Metrics

Required:

```text
deployment_count
rollout_duration
rollout_failures
rollback_count
instances_pending
instances_ready
scale_actions
scale_failures
cluster_failovers
federation_health
```

---

# 286. Traces

Trace:

```text
deployment request
→ rollout plan
→ cluster target
→ placement
→ activation
→ health gate
→ traffic transition
```

---

# 287. Resource Accounting

Every rollout resource request must be visible to 606.

---

# 288. Deployment Cost Metadata

Provider may expose:

```text
resource consumption
capacity reservation
network transfer
storage
```

as descriptive metadata.

636 does not define billing.

---

# 289. No Mandatory Cloud Dependency

Cloud provider integration is optional.

Possible providers:

```text
BareMetal
VM
Cloud
EdgeDevice
Embedded
Local
```

---

# 290. Provider Architecture

```text
DeploymentProvider
CapacityProvider
FederationProvider
TrafficProvider
ArtifactProvider
HealthProvider
```

---

# 291. Provider Isolation

Provider-specific APIs stay outside portable core.

---

# 292. Plugin Security

Providers loaded as plugins must use 603/623 capability and trust rules.

---

# 293. External Orchestrator Integration

Axiom may expose adapters for:

```text
Kubernetes
Nomad
Cloud schedulers
external CI/CD
external deployment systems
```

but these are integration modules.

---

# 294. Import Existing Cluster

External cluster can appear as:

```text
FederatedCluster
```

through provider.

---

# 295. Export Desired State

Axiom can emit:

```text
deployment plan
placement intent
traffic policy
```

for external systems.

---

# 296. No Vendor Lock-In

Portable deployment specification must not contain mandatory cloud-specific fields.

---

# 297. Deterministic Deployment Simulator

Provide:

```text
DeploymentSimulator
ClusterSimulator
FederationSimulator
TrafficSimulator
HealthSimulator
CapacitySimulator
```

---

# 298. Simulator Scenarios

Must simulate:

```text
node loss
cluster loss
network partition
artifact loss
health failure
capacity shortage
traffic failure
leader change
controller crash
rollback
autoscaling oscillation
```

---

# 299. Property Tests

Properties:

```text
desired state eventually converges when dependencies recover
no unauthorized rollout
no stale rollout mutation
no duplicate activation
no impossible capacity allocation
no quota bypass
no infinite rollback loop
```

---

# 300. Chaos Tests

Chaos engine should support:

```text
random node failure
random network delay
random controller restart
random health degradation
random cluster disconnect
```

with deterministic seeds for replay.

---

# 301. Rollout Safety Invariants

1. Immutable releases cannot mutate.
2. Deployment revisions are append-only.
3. Rollback creates a new desired revision.
4. Desired and observed state remain separate.
5. Scheduler remains authority for node placement.
6. Deployment controller cannot bypass scheduler.
7. Traffic controller remains authority for traffic.
8. Resource governor remains authority for resource limits.
9. Security capability policy cannot be bypassed by rollout.
10. Stale deployment controller cannot mutate current state.

---

# 302. Autoscaling Invariants

11. Scaling never exceeds min/max.
12. Scaling never bypasses quota.
13. Scaling never bypasses capacity.
14. Scaling uses bounded rate.
15. Scaling observes metric freshness.
16. Scaling cannot create infinite oscillation.
17. Scale-to-zero is explicit.
18. Stateful workloads require explicit zero-scale semantics.

---

# 303. Federation Invariants

19. Each cluster retains local authority.
20. Federation does not imply global consensus.
21. Cross-cluster authority is delegated explicitly.
22. Expired delegation cannot mutate.
23. Stale cluster generation cannot mutate.
24. Failover requires fencing where required.
25. Federation cannot grant capabilities implicitly.
26. Local security policy cannot be bypassed by global deployment.

---

# 304. Rollout Invariants

27. maxUnavailable is respected.
28. maxSurge is respected.
29. Health gates are explicit.
30. Automatic rollback is opt-in.
31. Rollback cannot loop forever.
32. Candidate and stable metrics remain distinguishable.
33. Shadow workloads cannot perform unauthorized side effects.
34. Wave ordering is deterministic.
35. Paused rollout cannot advance accidentally.

---

# 305. Edge Invariants

36. Offline authority is bounded.
37. Delegated authority expires.
38. Edge cannot claim global authority after delegation expiry.
39. Reconnect reconciles divergent state explicitly.
40. Federation conflicts are visible.

---

# 306. Performance Invariants

41. Independent deployments may progress independently.
42. Controller queues are bounded.
43. Rollout state is incrementally reconciled.
44. Metrics processing does not block control state.
45. Artifact downloads do not block consensus.
46. Health observation is asynchronous.
47. Federation communication is bounded.
48. Minimal builds dead-strip unused deployment modules.

---

# 307. Security Invariants

49. No secret in rollout state.
50. No secret in deployment events.
51. Release signatures are verified.
52. Capability changes require authorization.
53. Administrative mutations are audited.
54. Cross-cluster trust is explicit.
55. Provider plugins are sandboxed/capability-controlled.
56. Shadow execution cannot gain production authority implicitly.

---

# 308. Reliability Invariants

57. Controller restart does not lose committed intent.
58. Controller retry does not duplicate protected side effects.
59. Node failure causes deterministic reconciliation.
60. Cluster failure produces explicit degraded state.
61. Rollback checks artifact availability.
62. Recovery checks data consistency.
63. Deployment state survives control-plane restart.
64. Federation state can recover from partial connectivity.

---

# 309. Acceptance Criteria — Deployment

- [ ] Deployment creation.
- [ ] Release immutability.
- [ ] Revision history.
- [ ] Deployment admission.
- [ ] Rolling rollout.
- [ ] Blue/green.
- [ ] Canary.
- [ ] Shadow.
- [ ] Staged waves.
- [ ] Pause.
- [ ] Resume.
- [ ] Cancel.
- [ ] Rollback.
- [ ] Known-good revision.
- [ ] Health gates.
- [ ] Deployment dependencies.
- [ ] Schema compatibility.
- [ ] Resource reservation.
- [ ] Surge limits.
- [ ] Failure-domain protection.

---

# 310. Acceptance Criteria — Autoscaling

- [ ] Horizontal scaling.
- [ ] Min/max.
- [ ] Cooldown.
- [ ] Hysteresis.
- [ ] Multiple metrics.
- [ ] Metric freshness.
- [ ] Scale rate limit.
- [ ] Queue-based scaling.
- [ ] Event-lag scaling.
- [ ] Workflow-backlog scaling.
- [ ] Scale-to-zero.
- [ ] Scale-from-zero.
- [ ] Cluster capacity requests.
- [ ] Warm capacity.
- [ ] Quota integration.
- [ ] Resource accounting.
- [ ] Autoscaling stabilization.

---

# 311. Acceptance Criteria — Federation

- [ ] Federation identity.
- [ ] Cluster registration.
- [ ] Trust establishment.
- [ ] Capability negotiation.
- [ ] Cluster health.
- [ ] Global target selection.
- [ ] Regional rollout.
- [ ] Multi-cluster rollout.
- [ ] Cross-cluster rollback.
- [ ] Failover.
- [ ] Active/passive.
- [ ] Active/active boundary.
- [ ] Federation fencing.
- [ ] Delegated authority.
- [ ] Offline edge.
- [ ] Reconnect.
- [ ] Conflict detection.
- [ ] Conflict policy.
- [ ] Cluster removal.

---

# 312. Acceptance Criteria — Edge

- [ ] Edge groups.
- [ ] Offline-capable deployment.
- [ ] Delegated authority.
- [ ] Expiry.
- [ ] Local reconciliation.
- [ ] Reconnect reconciliation.
- [ ] Package preloading.
- [ ] Artifact cache.
- [ ] Limited-resource placement.
- [ ] Intermittent network handling.
- [ ] Edge failover.
- [ ] Edge quarantine.

---

# 313. Acceptance Criteria — Safety

- [ ] Stale controller rejected.
- [ ] Stale cluster rejected.
- [ ] Stale deployment generation rejected.
- [ ] Duplicate command deduplicated.
- [ ] Duplicate activation prevented.
- [ ] Rollback loop prevented.
- [ ] Split-brain federation prevented.
- [ ] Expired delegation rejected.
- [ ] Expired lease rejected.
- [ ] Fencing enforced.
- [ ] Unauthorized capability change rejected.
- [ ] Invalid artifact rejected.

---

# 314. Acceptance Criteria — Recovery

- [ ] Controller crash.
- [ ] Scheduler crash.
- [ ] Leader change.
- [ ] Cluster restart.
- [ ] Node failure.
- [ ] Network partition.
- [ ] Artifact unavailable.
- [ ] Capacity provider failure.
- [ ] Traffic provider failure.
- [ ] Health provider failure.
- [ ] Federation partition.
- [ ] Edge disconnect.
- [ ] Rollout interrupted.
- [ ] Rollback interrupted.

---

# 315. Acceptance Criteria — Tooling

- [ ] `axiom deploy plan`
- [ ] `axiom deploy apply`
- [ ] `axiom deploy pause`
- [ ] `axiom deploy resume`
- [ ] `axiom deploy rollback`
- [ ] `axiom deploy status`
- [ ] `axiom deploy history`
- [ ] `axiom deploy diff`
- [ ] `axiom deploy explain`
- [ ] `axiom scale status`
- [ ] `axiom federation status`
- [ ] `axiom federation deploy`
- [ ] `axiom edge status`
- [ ] deterministic simulator
- [ ] structured JSON/AXIOM output
- [ ] AI-readable metadata.

---

# 316. Performance Targets

Target behavior:

```text
deployment planning:
O(targets × candidate placements)

rollout reconciliation:
O(changed objects)

health evaluation:
O(number of configured signals)

autoscaling:
O(number of active policies × metrics)

federation target selection:
O(clusters × constraints)
```

Không được yêu cầu scan toàn bộ cluster cho mỗi small state change.

---

# 317. Incremental Reconciliation

Controller phải sử dụng:

```text
revision
watch
dirty set
dependency graph
```

để tránh full-cluster recomputation.

---

# 318. Event-Driven Controller

Primary mechanism:

```text
watch
→ enqueue affected object
→ reconcile
```

Periodic full reconciliation là safety net, không phải hot path duy nhất.

---

# 319. Queue Coalescing

Nếu một deployment nhận:

```text
10 updates
```

trước khi reconcile, controller có thể coalesce thành latest revision nếu intermediate states không cần xử lý.

---

# 320. Critical Events

Một số transitions không được coalesce nếu policy yêu cầu audit:

```text
fence
rollback
security denial
manual approval
failover
```

---

# 321. Binary Size

Minimal native application:

```text
AXDEPLOY_NONE
```

không link:

```text
autoscaler
federation
edge
rollout controller
```

---

# 322. Profiles

Axiom định nghĩa:

```text
AXDEPLOY_NONE
AXDEPLOY_LOCAL
AXDEPLOY_ROLLOUT
AXDEPLOY_AUTOSCALE
AXDEPLOY_CLUSTER
AXDEPLOY_FEDERATION
AXDEPLOY_EDGE
AXDEPLOY_FULL
```

---

# 323. AXDEPLOY_NONE

Không có deployment control-plane runtime.

---

# 324. AXDEPLOY_LOCAL

Local desired-state deployment:

```text
package
process
service
```

---

# 325. AXDEPLOY_ROLLOUT

Thêm:

```text
rolling
blue-green
canary
shadow
rollback
```

---

# 326. AXDEPLOY_AUTOSCALE

Thêm:

```text
metrics
scaling
capacity
```

---

# 327. AXDEPLOY_CLUSTER

Thêm:

```text
635 integration
multi-node deployment
```

---

# 328. AXDEPLOY_FEDERATION

Thêm:

```text
multi-cluster
regional deployment
global failover
```

---

# 329. AXDEPLOY_EDGE

Thêm:

```text
offline
delegation
edge orchestration
```

---

# 330. AXDEPLOY_FULL

Toàn bộ deployment/federation runtime.

---

# 331. Final Architecture

```text
                        ┌──────────────────────────────┐
                        │       Axiom Application      │
                        └──────────────┬───────────────┘
                                       │
                         Deployment Intent / Policy
                                       │
                        ┌──────────────▼───────────────┐
                        │        BOOTSTRAP-636         │
                        │                              │
                        │ Deployment Controller        │
                        │ Rollout Engine               │
                        │ Blue/Green                   │
                        │ Canary                       │
                        │ Shadow                       │
                        │ Wave Manager                 │
                        │ Health Gates                 │
                        │ Autoscaler                   │
                        │ Federation Controller        │
                        │ Edge Orchestrator            │
                        │ DR Coordinator               │
                        └──────────────┬───────────────┘
                                       │
                         ┌─────────────▼──────────────┐
                         │       BOOTSTRAP-635        │
                         │                            │
                         │ Cluster Control Plane      │
                         │ Scheduler                  │
                         │ Placement                  │
                         │ Consensus                  │
                         │ Leader / Lease / Fencing   │
                         │ Reconciliation             │
                         └─────────────┬──────────────┘
                                       │
             ┌─────────────────────────┼────────────────────────┐
             │                         │                        │
      ┌──────▼──────┐          ┌───────▼───────┐        ┌───────▼──────┐
      │ 631 Service │          │ 605 Supervisor │        │ 630 Compute  │
      └──────┬──────┘          └───────┬───────┘        └───────┬──────┘
             │                         │                        │
             └─────────────────────────┼────────────────────────┘
                                       │
                              ┌────────▼────────┐
                              │ 606 Resources   │
                              │ 603 Security    │
                              │ 633 Telemetry   │
                              │ 634 Events      │
                              └─────────────────┘
```

---

# 332. Multi-Cluster Architecture

```text
                    Federation Controller
                            │
             ┌──────────────┼──────────────┐
             │              │              │
        Cluster A       Cluster B       Cluster C
             │              │              │
          636/635        636/635        636/635
             │              │              │
          Nodes           Nodes           Nodes
```

Mỗi cluster vẫn có authority riêng.

---

# 333. Edge Architecture

```text
Global Federation
       │
       ├── Region
       │     ├── Cluster
       │     └── Cluster
       │
       └── Edge Group
              ├── Edge Cluster
              ├── Edge Cluster
              └── Offline Edge
```

---

# 334. Core Design Decision

BOOTSTRAP-636 xác lập ranh giới:

```text
636
=
deployment intent
+
rollout
+
autoscaling
+
federation
+
edge orchestration
```

trong khi:

```text
635
=
cluster authority
+
placement
+
consensus
+
coordination
```

và:

```text
631
=
service execution
```

```text
605
=
process execution
```

```text
606
=
resource enforcement
```

```text
632
=
edge traffic execution
```

---

# 335. Architectural Invariant

Không component nào ở 636 được phép tự ý bypass:

```text
Security 603
Resource 606
Cluster Authority 635
Service Runtime 631
Process Supervisor 605
Traffic Runtime 632
Distributed State 628
```

---

# 336. Final Completion Criteria

BOOTSTRAP-636 được xem là **COMPLETE** khi implementation/specification có:

- deployment state machine;
- immutable releases;
- revision model;
- rollout engine;
- rolling strategy;
- blue/green;
- canary;
- shadow;
- staged waves;
- health gates;
- rollback;
- autoscaling;
- capacity provider;
- resource integration;
- multi-cluster federation;
- delegated authority;
- federation fencing;
- edge orchestration;
- offline operation;
- disaster recovery orchestration;
- deterministic reconciliation;
- controller recovery;
- complete security boundary;
- complete observability;
- AI-readable metadata;
- compiler annotations;
- CLI;
- deterministic simulator;
- fault injection;
- model/property tests;
- cross-platform provider boundary;
- minimal build profiles;
- dead stripping.

**Target:** ≥ 350 implementation-level acceptance criteria.

---

# 337. Completion

**BOOTSTRAP-636 — COMPLETE.**

Axiom hiện đã có chuỗi distributed architecture từ:

```text
628 Distributed Data
629 Durable Workflow
630 Distributed Compute
631 Distributed Service
632 Gateway / Edge
633 Observability
634 Event / Stream
635 Cluster Control Plane
636 Deployment / Federation / Autoscaling
```

Lớp tiếp theo nên chuyển từ **deployment/control-plane** sang một tầng còn thiếu để hoàn thiện platform semantics: **BOOTSTRAP-637 — Native Distributed Configuration, Feature Flags, Dynamic Policy, Runtime Experimentation, Progressive Delivery Signals & Global Control Registry Runtime 5.0**.
:::