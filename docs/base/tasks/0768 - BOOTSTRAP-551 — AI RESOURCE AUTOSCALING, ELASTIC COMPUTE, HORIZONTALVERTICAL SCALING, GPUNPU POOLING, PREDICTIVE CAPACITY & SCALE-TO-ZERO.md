# BOOTSTRAP-551 — AI RESOURCE AUTOSCALING, ELASTIC COMPUTE, HORIZONTAL/VERTICAL SCALING, GPU/NPU POOLING, PREDICTIVE CAPACITY & SCALE-TO-ZERO

**Trạng thái: COMPLETED / LOCKED**

`550` đã định nghĩa quota, admission, fairness và isolation. `551` bổ sung lớp **elastic resource management**: khi nào tăng/giảm resource, scale ở đâu, scale bao nhiêu, và làm thế nào để scaling không phá SLO, state, cost, security hoặc correctness.

---

## 551.1 — Architecture

```text id="a7k2qf"
                 Workload
                    │
                    ▼
              Telemetry 475/481
                    │
          ┌─────────┴─────────┐
          ▼                   ▼
      Current State        Forecast
          │                   │
          └─────────┬─────────┘
                    ▼
             Scaling Policy
                    │
          ┌─────────┼─────────┐
          ▼         ▼         ▼
      Horizontal Vertical  Placement
          │         │         │
          └─────────┼─────────┘
                    ▼
             Admission 550
                    │
                    ▼
             Fleet 534
                    │
                    ▼
             Provisioning
                    │
                    ▼
              Verification
```

---

## 551.2 — Autoscaling ≠ Scheduling

Scheduling chọn workload/resource hiện có.

Autoscaling thay đổi capacity.

---

## 551.3 — Scaling Dimensions

```text id="m9h4pd"
replicas
CPU
RAM
GPU
VRAM
NPU
storage
network
worker count
device pool
```

---

## 551.4 — Horizontal Scaling

Tăng/giảm số instance/worker.

---

## 551.5 — Vertical Scaling

Thay đổi resource allocation của instance.

---

## 551.6 — Diagonal Scaling

Có thể đồng thời thay đổi replica count và resource size.

---

## 551.7 — Cluster Scaling

Thêm/bớt host/node/device.

---

## 551.8 — Pool Scaling

Thay đổi capacity của resource pool 550.

---

## 551.9 — Elasticity

Elasticity là khả năng thay đổi capacity theo workload/policy.

---

## 551.10 — Scaling Policy

```text id="5b7h8n"
ScalingPolicy {
    target
    min
    max
    step
    cooldown
    stabilization
    constraints
}
```

---

## 551.11 — Minimum Capacity

`min` là hard lower bound nếu policy yêu cầu.

---

## 551.12 — Maximum Capacity

`max` là hard upper bound.

---

## 551.13 — Desired Capacity

Desired capacity khác observed capacity.

---

## 551.14 — Reconciliation

```textObserved id="w2t5jd"
     ↓
Desired
     ↓
Reconcile
```

---

## 551.15 — Scale Action

Mỗi scaling action có:

```text id="s5c8fe"
ActionId
PolicyVersion
OldCapacity
NewCapacity
Reason
Evidence
```

---

## 551.16 — Scale Reason

Reason phải reference measurement/policy.

---

## 551.17 — Scaling Trigger

Trigger có thể là:

```textCPU id="p2f4sv"
GPU
memory
queue
latency
throughput
request rate
tokens
SLO
cost
schedule
```

---

## 551.18 — Resource Trigger

Resource metric phải reference exact resource scope.

---

## 551.19 — Queue Trigger

Queue depth và queue age là hai metrics khác nhau.

---

## 551.20 — Latency Trigger

Latency trigger phải định nghĩa population/window.

---

## 551.21 — Throughput Trigger

Throughput phải định nghĩa unit/window.

---

## 551.22 — Token Trigger

AI token throughput có thể feed scaling.

---

## 551.23 — Concurrency Trigger

Active requests/tasks có thể trigger scaling.

---

## 551.24 — SLO Trigger

548 SLO violation/burn có thể trigger scaling.

---

## 551.25 — Cost Trigger

549 cost constraint có thể hạn chế scaling.

---

## 551.26 — Quality Trigger

AI model quality policy có thể constrain scaling/fallback.

---

## 551.27 — Security Trigger

547/545 có thể yêu cầu scale-out/isolation.

---

## 551.28 — Forecast Trigger

Predictive scaling dùng forecast từ historical data.

---

## 551.29 — Forecast ≠ Fact

Forecast phải được đánh dấu predicted.

---

## 551.30 — Forecast Provenance

Model/data/config của forecast được lưu.

---

## 551.31 — Forecast Horizon

Horizon explicit.

---

## 551.32 — Forecast Uncertainty

Prediction uncertainty phải được giữ nếu model cung cấp.

---

## 551.33 — Predictive Scaling

Có thể provision trước expected demand.

---

## 551.34 — Reactive Scaling

Scale dựa trên observed measurements.

---

## 551.35 — Hybrid Scaling

Reactive + predictive scaling được hỗ trợ.

---

## 551.36 — Hysteresis

Scaling phải tránh oscillation.

---

## 551.37 — Cooldown

Sau scaling action có cooldown policy.

---

## 551.38 — Stabilization Window

Short-lived spikes có thể bị bỏ qua theo stabilization policy.

---

## 551.39 — Scale Step

Scale step có thể fixed hoặc policy-derived.

---

## 551.40 — Rate of Change

Scaling rate có thể giới hạn.

---

## 551.41 — Burst

Burst scaling có thể tăng capacity nhanh nhưng vẫn chịu max/quotas.

---

## 551.42 — Scale-In Protection

Scale-in có thể bị trì hoãn khi workload đang critical.

---

## 551.43 — Drain Before Scale-In

Instance scale-in có thể yêu cầu drain.

---

## 551.44 — Grace Period

Drain có timeout.

---

## 551.45 — Forced Scale-In

Forced termination cần explicit policy.

---

## 551.46 — Stateful Instance

Stateful instance không được scale-in nếu state chưa durable/migratable.

---

## 551.47 — Stateless Instance

Stateless instances dễ dàng recreate hơn nhưng vẫn phải qua readiness.

---

## 551.48 — Session-Aware Scaling

529 session affinity/state phải được xét.

---

## 551.49 — Workflow-Aware Scaling

540/541 active workflows phải được xét.

---

## 551.50 — Agent-Aware Scaling

535 agent instances/session workload.

---

## 551.51 — Model Serving Scaling

529/534 model replicas.

---

## 551.52 — Continuous Batching

509 continuous batching có thể thay đổi nhu cầu GPU mà không chỉ dựa trên replica count.

---

## 551.53 — KV Cache

KV-cache memory có thể là scaling signal.

---

## 551.54 — GPU Memory

VRAM pressure có thể trigger scale-out hoặc model eviction.

---

## 551.55 — GPU Pool

```text id="8g2h4v"
GPUPool {
    devices
    capacity
    allocation
    capabilities
}
```

---

## 551.56 — GPU Pooling

GPU có thể được gom thành logical pool.

---

## 551.57 — GPU Identity

Physical GPU/partition identity vẫn được giữ.

---

## 551.58 — GPU Partition

MIG-like partitioning provider-dependent.

---

## 551.59 — GPU Sharing

GPU sharing policy explicit.

---

## 551.60 — GPU Exclusivity

Exclusive GPU workloads require explicit reservation.

---

## 551.61 — GPU Memory Isolation

Memory isolation depends on hardware/provider.

---

## 551.62 — NPU Pool

NPU devices được quản lý tương tự GPU.

---

## 551.63 — Accelerator Capability

Model/kernel requirement phải match accelerator capability.

---

## 551.64 — Heterogeneous Pool

CPU/GPU/NPU pool có thể coexist nhưng không được coi interchangeable.

---

## 551.65 — Device Selection

534 placement policy quyết định device eligibility.

---

## 551.66 — Scaling + Placement

Scale action phải produce placement constraints.

---

## 551.67 — Failure Domain

Replica scaling phải respect 548 failure-domain policy.

---

## 551.68 — Anti-Affinity

Replicas có thể yêu cầu distinct hosts/zones.

---

## 551.69 — Capacity Insufficiency

Không đủ capacity → Pending thay vì giả vờ scale thành công.

---

## 551.70 — Provisioning

Provisioning là external infrastructure operation.

---

## 551.71 — Provisioner Interface

```text id="n5b3z1"
provision(request) -> Result<ResourceSet, Error>
release(resource_set)
```

---

## 551.72 — Provider Independence

Cloud/provider semantics không nằm trong language core.

---

## 551.73 — Bare Metal

Bare-metal resource provider được hỗ trợ conceptually.

---

## 551.74 — VM

VM provisioning provider integration.

---

## 551.75 — Container

Container resource provisioning integration.

---

## 551.76 — Serverless

Invocation-based elasticity supported through provider adapter.

---

## 551.77 — Local Machine

Local process/thread scaling không cần cloud infrastructure.

---

## 551.78 — Edge

Edge devices có constrained scaling.

---

## 551.79 — Embedded

Embedded target không giả định dynamic scaling.

---

## 551.80 — Scale-to-Zero

Workload có thể scale xuống zero nếu policy cho phép.

---

## 551.81 — Scale-to-Zero Eligibility

Chỉ workload stateless hoặc state đã durable/migratable nên dùng.

---

## 551.82 — Wake Trigger

Scale-from-zero trigger:

```textHTTP id="q9e6ma"
queue
event
timer
message
workflow
```

---

## 551.83 — Cold Start

Cold-start latency được đo riêng.

---

## 551.84 — Warm Pool

Warm instances có thể giảm cold-start.

---

## 551.85 — Warm Pool Cost

Idle warm capacity phải được accounting qua 549.

---

## 551.86 — Prewarming

Prewarming có thể dựa trên forecast.

---

## 551.87 — Model Preload

Model artifact có thể preload vào GPU.

---

## 551.88 — Model Load Cost

Model loading time/memory được accounting.

---

## 551.89 — Shared Model Memory

Shared weights không được double-count trong physical capacity.

---

## 551.90 — Replica Initialization

Replica chỉ Ready sau initialization/health checks.

---

## 551.91 — Readiness Gate

Scaling success ≠ readiness.

---

## 551.92 — Health Gate

548 health state required.

---

## 551.93 — Security Gate

545/490 policy required before activation.

---

## 551.94 — Artifact Gate

533/546 artifact integrity/provenance.

---

## 551.95 — Configuration Gate

470 configuration compatibility.

---

## 551.96 — Runtime Gate

529 runtime compatibility.

---

## 551.97 — Device Gate

503/504 device capability compatibility.

---

## 551.98 — Quota Gate

550 quota/admission.

---

## 551.99 — Budget Gate

549 budget.

---

## 551.100 — Scale Decision

```text id="2c6t7v"
ScaleDecision {
    desired_capacity
    constraints
    evidence
    policy
}
```

---

## 551.101 — Constraint Intersection

Effective scaling capacity là intersection của:

```textquota id="v1r5t7"
budget
SLO
security
device
capacity
policy
```

---

## 551.102 — Constraint Conflict

Conflict → deterministic `CannotScale` reason.

---

## 551.103 — No Silent Violation

Autoscaler không được vượt constraint để đạt target.

---

## 551.104 — SLO vs Cost

Nếu cost và SLO conflict, policy phải định nghĩa precedence.

---

## 551.105 — No Universal Precedence

Axiom không hard-code cost > SLO hoặc ngược lại.

---

## 551.106 — Priority

Critical workload có thể reserve scaling capacity.

---

## 551.107 — Reserved Capacity

549/550 reserved pool.

---

## 551.108 — Emergency Capacity

547 incident response có thể consume reserved emergency capacity.

---

## 551.109 — Emergency Scale

Emergency scaling phải được audit.

---

## 551.110 — Scale Authorization

Scaling action có capability scope.

---

## 551.111 — Autonomous Scaling

Chỉ policy-authorized actions mới được tự động.

---

## 551.112 — AI Scaling Advisor

AI có thể dự đoán nhu cầu/propose scaling.

---

## 551.113 — AI Scaling Authority

AI không tự bypass scaling policy.

---

## 551.114 — Forecast Model

Forecast model identity/version recorded.

---

## 551.115 — Forecast Dataset

Training/evaluation data provenance nếu forecast model được learned.

---

## 551.116 — Forecast Drift

Forecast accuracy có thể được monitored.

---

## 551.117 — Forecast Failure

Fallback về reactive policy khi forecast unavailable.

---

## 551.118 — Fallback Policy

Fallback phải explicit.

---

## 551.119 — Scaling Controller Failure

Control plane restart phải reconstruct desired/observed state.

---

## 551.120 — Duplicate Scale Action

Action identity/idempotency chống duplicate provisioning.

---

## 551.121 — Provisioning Timeout

Provisioning timeout explicit.

---

## 551.122 — Partial Provision

Partial resources phải được tracked/cleaned.

---

## 551.123 — Orphan Resource

Orphan detection/reconciliation.

---

## 551.124 — Resource Leak

Failed scaling không được tạo resource leak vô hạn.

---

## 551.125 — Rollback

Failed scale-out có rollback/release policy.

---

## 551.126 — Scale-In Rollback

Nếu scale-in drain fails, giữ instance.

---

## 551.127 — Deployment Integration

534 rollout can trigger temporary capacity increase.

---

## 551.128 — Canary Capacity

Canary replica capacity is separately accounted.

---

## 551.129 — Shadow Capacity

Shadow workload cost/resource usage visible.

---

## 551.130 — Blue/Green

Blue + green capacity may coexist temporarily.

---

## 551.131 — Capacity Reservation

Blue/green rollout can reserve required capacity before switching.

---

## 551.132 — Rollback Capacity

Rollback target capacity must be available or explicitly provisionable.

---

## 551.133 — Version Migration

539 session/model compatibility.

---

## 551.134 — State Migration

State transfer cost/time included in scaling decision.

---

## 551.135 — Data Locality

512/528 data placement affects provisioning.

---

## 551.136 — Model Locality

Model artifact placement/cache affects startup.

---

## 551.137 — Network Cost

549 network transfer cost may constrain scaling.

---

## 551.138 — Cross-Region Scaling

Cross-region scaling has explicit latency/cost/data policy.

---

## 551.139 — Region Selection

Region eligibility policy explicit.

---

## 551.140 — Data Residency

Data governance 528/545 may restrict placement.

---

## 551.141 — Security Region

Security policy may restrict workloads to approved zones.

---

## 551.142 — Hardware Residency

Certain models/data may require specific accelerator class.

---

## 551.143 — Capacity Fragmentation

Scheduler should detect fragmented capacity.

---

## 551.144 — GPU Fragmentation

VRAM fragmentation can prevent placement despite nominal free memory.

---

## 551.145 — Defragmentation

Defragmentation/migration is explicit operation.

---

## 551.146 — Packing

Bin-packing is optimization heuristic, not guarantee.

---

## 551.147 — Cost Model

Scaling planner consumes 549 cost estimates.

---

## 551.148 — Reliability Model

Scaling planner consumes 548 SLO/failure-domain constraints.

---

## 551.149 — Governance Model

Scaling planner consumes 545 authorization/policy.

---

## 551.150 — Incident Model

547 emergency containment/recovery.

---

## 551.151 — Scheduler Model

550/471 allocation.

---

## 551.152 — Fleet Model

534 desired/observed state.

---

## 551.153 — Execution Model

505 actual workload demand.

---

## 551.154 — Telemetry

475/481 measurement source.

---

## 551.155 — Scaling Graph

```text id="1m4x7d"
Demand
 ↓
Telemetry
 ↓
Scaling Decision
 ↓
Provisioning
 ↓
Placement
 ↓
Readiness
 ↓
Traffic Assignment
 ↓
Observed Capacity
```

---

## 551.156 — Traffic Assignment

New capacity không được nhận traffic trước readiness.

---

## 551.157 — Warmup Traffic

Warmup can be isolated from production traffic.

---

## 551.158 — Gradual Activation

Traffic ramp-up có thể dùng canary policy.

---

## 551.159 — Scale-In Traffic

Traffic phải drain trước termination.

---

## 551.160 — Connection Draining

Persistent connections có explicit timeout.

---

## 551.161 — Streaming Drain

Streaming requests được xử lý riêng.

---

## 551.162 — Long-Running Workflow

Workflow không bị kill chỉ vì scale-in nếu durable policy không cho phép.

---

## 551.163 — Long-Running Agent

Agent session có migration/pinning semantics.

---

## 551.164 — GPU Context

GPU context/stream migration provider-dependent.

---

## 551.165 — Device Loss

Device loss feeds 547/548 and scaling controller.

---

## 551.166 — Hardware Failure

Failed hardware removed from capacity.

---

## 551.167 — Recovery

Recovered resource must pass verification.

---

## 551.168 — Autoscaling Loop

```textMeasure → Decide → Act → Observe → Verify
```

---

## 551.169 — Loop Stability

Controller phải có bounded reaction rate.

---

## 551.170 — Oscillation Detection

Repeated scale up/down can trigger stabilization.

---

## 551.171 — Controller State

Controller state versioned/recoverable.

---

## 551.172 — Policy Update

Policy change creates new controller generation.

---

## 551.173 — In-Flight Action

Policy update không tự động invalidate action đang safely executing trừ khi policy yêu cầu.

---

## 551.174 — Policy Revocation

Security-critical policy revocation can stop future scaling actions.

---

## 551.175 — Audit

Every scale action audited.

---

## 551.176 — Explainability

Queries:

```textwhy_scaled_up id="j1r5qp"
why_scaled_down
why_not_scaled
why_pending
why_scale_to_zero
why_woken
why_device_selected
```

---

## 551.177 — Evidence

Explanation references metrics, constraints, policy.

---

## 551.178 — No Causal Guess

Observed correlation không đủ để assert demand cause.

---

## 551.179 — Scaling Simulation

Historical workload replay can simulate scaling.

---

## 551.180 — Counterfactual

Simulation outputs marked counterfactual.

---

## 551.181 — Capacity Test

Synthetic capacity tests validate provisioning.

---

## 551.182 — Failure Injection

Test:

```text id="l3p5cn"
provision failure
device failure
network partition
quota exhaustion
budget exhaustion
```

---

## 551.183 — Recovery Test

Scale controller recovery after crash.

---

## 551.184 — Split Brain

Distributed autoscaler must not provision conflicting capacity states.

---

## 551.185 — Leader/Fencing

501/502 epoch/fencing.

---

## 551.186 — Exactly Once

No universal exactly-once provisioning guarantee.

---

## 551.187 — Idempotent Provider

Provider calls should use idempotency where available.

---

## 551.188 — Reconciliation

Periodic reconciliation corrects drift.

---

## 551.189 — Drift

Desired vs actual capacity divergence is explicit.

---

## 551.190 — Orphan Detection

Resources without active ownership can be quarantined/released according to policy.

---

## 551.191 — Cost Attribution

549 must attribute scaling resource consumption.

---

## 551.192 — Tenant Isolation

Autoscaling one tenant cannot silently consume another tenant's reserved capacity.

---

## 551.193 — Quota

550 quotas remain authoritative.

---

## 551.194 — Security

490/545 remain authoritative for privileged resource actions.

---

## 551.195 — Reliability

548 remains authoritative for SLO/failure-domain constraints.

---

## 551.196 — Performance

450/481 measure scaling overhead and effectiveness.

---

## 551.197 — AI Assistance

AI may optimize scaling parameters only through explicit policy/approval.

---

## 551.198 — Optionality

Autoscaling is infrastructure functionality, not language/runtime behavior.

---

## 551.199 — Final Hard Invariant

**Axiom Autoscaling phải phân biệt demand measurement, prediction, desired capacity, observed capacity, provisioning, placement, readiness và traffic activation. Horizontal/vertical/cluster/GPU/NPU/scale-to-zero đều phải có explicit policy, quota, budget, security, SLO, device-capability và state constraints. Autoscaling không được vượt constraint để đạt target; không được hidden optimize cost hoặc latency. Mọi scale action phải có identity, policy, evidence, idempotency/reconciliation và bounded retry; scale-in phải bảo vệ stateful/session/workflow/streaming workloads bằng drain/migration semantics. Predictive/AI scaling chỉ là evidence/proposal cho đến khi policy-authorized. Controller phải chống oscillation, stale decisions, duplicate provisioning, orphan resources và split-brain; toàn bộ elasticity layer phải optional và không tạo hidden runtime behavior cho native Axiom applications.**

**BOOTSTRAP-551 hoàn tất / LOCKED.**

---

# BOOTSTRAP-552 — AI SYSTEM RESOURCE SCHEDULING 2.0, GPU CLUSTER SCHEDULER, WORKLOAD PLACEMENT, BIN PACKING, TOPOLOGY AWARENESS & HETEROGENEOUS ACCELERATOR ORCHESTRATION

**Trạng thái: COMPLETED / LOCKED**

`551` quyết định **có tăng capacity hay không**. `552` tập trung vào **đặt workload cụ thể lên resource cụ thể**, đặc biệt cho AI workloads có GPU/NPU, VRAM, NUMA, network topology, model locality và distributed training.

---

## 552.1 — Architecture

```text id="c4m9za"
              Workload Request
                     │
                     ▼
              Admission 550
                     │
                     ▼
             Resource Catalog
                     │
          ┌──────────┼──────────┐
          ▼          ▼          ▼
        CPU        GPU/NPU    Storage
          │          │          │
          └──────────┼──────────┘
                     ▼
              Feasibility Filter
                     │
                     ▼
             Placement Engine
                     │
       ┌─────────────┼─────────────┐
       ▼             ▼             ▼
   Topology       Locality      Capacity
       │             │             │
       └─────────────┼─────────────┘
                     ▼
               Allocation Plan
                     │
                     ▼
              Execution 505
                     │
                     ▼
                Monitoring
```

---

## 552.3 — Workload Placement Request

```text id="m5v8de"
PlacementRequest {
    workload_id
    resources
    capabilities
    locality
    affinity
    anti_affinity
    topology
    deadline
    priority
}
```

---

## 552.4 — Feasibility ≠ Optimization

Đầu tiên phải xác định placement **hợp lệ**.

Sau đó mới tối ưu.

---

## 552.5 — Hard Constraint

Ví dụ:

```textGPU >= required_memory id="y8h4e1"
arch == required_arch
region == allowed_region
```

Vi phạm hard constraint → placement invalid.

---

## 552.6 — Soft Constraint

Soft preference có thể trade-off.

---

## 552.7 — No Universal Optimizer

Axiom không hard-code một thuật toán placement duy nhất.

---

## 552.8 — Resource Vector

```text id="f7c1ax"
CPU
RAM
GPU
VRAM
NPU
storage
network
```

---

## 552.9 — Accelerator Vector

GPU/NPU request có thể bao gồm:

```text id="6y0b3q"
count
memory
compute_class
features
interconnect
```

---

## 552.10 — GPU Capability

GPU capability gồm:

```text id="x4g9m2"
architecture
ISA/features
memory
compute_units
tensor_features
interconnect
```

---

## 552.11 — Model Compatibility

Model 533/504 requirements phải match device capability.

---

## 552.12 — Kernel Compatibility

Kernel binary must support target architecture/features.

---

## 552.13 — CPU Feature

CPU instruction requirements được xét.

---

## 552.14 — NUMA

NUMA node là placement dimension.

---

## 552.15 — NUMA Locality

CPU memory và accelerator locality được xét khi policy yêu cầu.

---

## 552.16 — PCIe Topology

PCIe distance có thể ảnh hưởng transfer cost.

---

## 552.17 — NVLink/Interconnect

Accelerator interconnect topology có thể là constraint/preference.

---

## 552.18 — Network Topology

Distributed training có thể yêu cầu network locality/bandwidth.

---

## 552.19 — Rack Topology

Rack là failure/performance domain.

---

## 552.20 — Zone Topology

Zone failure domain từ 548.

---

## 552.21 — Region Topology

Region placement policy.

---

## 552.22 — Topology Graph

```text id="f7b0s2"
Region
 └─ Zone
    └─ Rack
       └─ Host
          ├─ NUMA
          ├─ CPU
          └─ GPU
              └─ Memory
```

---

## 552.23 — Topology Distance

Distance metric phải định nghĩa.

---

## 552.24 — Distance ≠ Latency

Topology distance không tự động bằng measured latency.

---

## 552.25 — Measured Topology

Measured bandwidth/latency có thể override static topology knowledge when policy permits.

---

## 552.26 — Placement Cache

Placement results có thể cache nhưng phải invalidate khi capacity/topology/policy thay đổi.

---

## 552.27 — Stale Placement

Stale plan phải revalidate trước commit.

---

## 552.28 — Reservation

Placement có thể reserve resource atomically.

---

## 552.29 — Reservation Conflict

Conflict → retry/recompute.

---

## 552.30 — Allocation Commit

Allocation commit phải be authoritative.

---

## 552.31 — Two-Phase Allocation

Có thể dùng:

```textPrepare id="6d5kq8"
Commit
```

---

## 552.32 — Allocation Rollback

Failed commit releases reservation.

---

## 552.33 — GPU Packing

Multiple workloads có thể pack onto same GPU khi policy cho phép.

---

## 552.34 — GPU Bin Packing

Packing objective có thể:

```text id="v9w3mc"
minimize fragmentation
maximize utilization
minimize cost
preserve locality
```

---

## 552.35 — Objective Priority

Objective ordering phải explicit.

---

## 552.36 — No Hidden Cost Optimization

Cost không tự trở thành objective.

---

## 552.37 — VRAM Fragmentation

Placement phải xét usable contiguous memory khi backend yêu cầu.

---

## 552.38 — Memory Reservation

VRAM reservation explicit.

---

## 552.39 — Shared Memory

Shared GPU memory accounting từ 549.

---

## 552.40 — Exclusive GPU

Exclusive assignment prevents unrelated workload placement.

---

## 552.41 — MIG-like Partition

Partition identity preserved.

---

## 552.42 — GPU Time Slicing

Time slicing provider/hardware-dependent.

---

## 552.43 — GPU Context Isolation

Isolation level explicit.

---

## 552.44 — NPU Partitioning

NPU partitioning provider-dependent.

---

## 552.45 — CPU Pinning

CPU affinity optional.

---

## 552.46 — CPU Shares

Shares ≠ dedicated cores.

---

## 552.47 — Memory Locality

Memory placement can be constrained by workload.

---

## 552.48 — Huge Pages

Huge-page requirement explicit.

---

## 552.49 — Storage Locality

Local NVMe/network storage preference.

---

## 552.50 — Dataset Locality

528 dataset location.

---

## 552.51 — Model Locality

533 model artifact cache.

---

## 552.52 — Cache Warmth

Warm model/device cache may be placement preference.

---

## 552.53 — Cold Start

Cold-start cost may be considered if policy allows.

---

## 552.54 — Network Transfer

Moving data/model incurs measured/estimated transfer cost.

---

## 552.55 — Cost Attribution

Transfer cost recorded by 549.

---

## 552.56 — Data Residency

545/528 restrictions.

---

## 552.57 — Security Placement

Security-sensitive workload may require dedicated resource.

---

## 552.58 — Trusted Hardware

TEE/secure hardware requirements optional.

---

## 552.59 — Capability Placement

Required capabilities must exist on target node.

---

## 552.60 — Device Attestation

546 evidence may be required before sensitive placement.

---

## 552.61 — Tenant Isolation

Placement must respect 550 isolation policy.

---

## 552.62 — Anti-Affinity

Replicas may require distinct hosts/zones.

---

## 552.63 — Co-Location

Workloads may explicitly request co-location.

---

## 552.64 — Co-Location Security

Co-location may be prohibited by security policy.

---

## 552.65 — Failure Domain Diversity

Distributed replicas should spread when policy requires.

---

## 552.66 — Distributed Training

Training workers require coordinated placement.

---

## 552.67 — Data Parallel

Workers may require same model version but separate data shards.

---

## 552.68 — Tensor Parallel

Workers may require high-bandwidth interconnect.

---

## 552.69 — Pipeline Parallel

Stage placement must respect pipeline topology.

---

## 552.70 — Hybrid Parallel

Data/tensor/pipeline dimensions combine.

---

## 552.71 — Collective Communication

All-reduce/all-gather communication topology can affect placement.

---

## 552.72 — Collective Capability

Required collective backend must exist.

---

## 552.73 — Network Bandwidth

Minimum bandwidth can be hard constraint.

---

## 552.74 — Network Latency

Maximum latency can be hard/soft constraint.

---

## 552.75 — Network Congestion

Observed congestion can feed scheduler.

---

## 552.76 — GPU Peer Access

Peer-access compatibility explicit.

---

## 552.77 — CPU-GPU Affinity

CPU worker placement can follow GPU locality.

---

## 552.78 — NUMA-GPU Affinity

Preferred NUMA node can be selected based on topology.

---

## 552.79 — Storage-GPU Pipeline

Data pipeline placement can minimize transfer.

---

## 552.80 — Preprocessing Placement

CPU preprocessing may be co-located with training workers.

---

## 552.81 — Inference Placement

Latency-sensitive inference can use topology-aware placement.

---

## 552.82 — Batch Placement

Batch workloads can prioritize throughput.

---

## 552.83 — Interactive Placement

Interactive workloads can use reserved capacity.

---

## 552.84 — Realtime Placement

Realtime workload can require dedicated resources.

---

## 552.85 — Background Placement

Background work can use opportunistic capacity.

---

## 552.86 — Preemptible Placement

Preemptible nodes are explicit resource class.

---

## 552.87 — Preemption Eligibility

Workload declares whether checkpoint/restart is safe.

---

## 552.88 — Checkpoint Requirement

Training preemption may require checkpoint 506/507.

---

## 552.89 — Preemption Notice

Graceful preemption provides notice when provider supports it.

---

## 552.90 — Eviction

Eviction reason recorded.

---

## 552.91 — Eviction Ordering

Policy determines victim selection.

---

## 552.92 — No Arbitrary Tenant Eviction

Eviction cannot bypass quota/governance.

---

## 552.93 — Priority

Priority from 550.

---

## 552.94 — Fairness

Fair-share policy from 550.

---

## 552.95 — Deadline

474 deadline-aware placement.

---

## 552.96 — SLO

548 reliability constraints.

---

## 552.97 — Cost

549 cost constraints.

---

## 552.98 — Scaling

551 capacity provisioning.

---

## 552.99 — Fleet

534 desired fleet state.

---

## 552.100 — Execution

505 executes allocated workload.

---

## 552.101 — Placement Plan

```text id="r4x8ps"
PlacementPlan {
    assignments
    reservations
    topology
    constraints
    objective
    policy
}
```

---

## 552.102 — Assignment

Each assignment maps workload resource requirement to concrete resource.

---

## 552.103 — Partial Assignment

Partial placement valid only if workload explicitly supports it.

---

## 552.104 — Gang Scheduling

Distributed training can require all workers before launch.

---

## 552.105 — Gang Admission

If complete placement unavailable, workload remains pending.

---

## 552.106 — Partial Start

Partial start prohibited for workloads requiring gang semantics.

---

## 552.107 — Elastic Training

Elastic training may allow worker count range.

---

## 552.108 — Elastic Membership

Worker membership changes are explicit.

---

## 552.109 — Worker Identity

Worker identity survives restart when checkpoint protocol requires.

---

## 552.110 — Rendezvous

Distributed workers require explicit rendezvous semantics.

---

## 552.111 — Membership Epoch

501/502 epoch prevents stale workers.

---

## 552.112 — Stale Worker

Stale worker must be fenced.

---

## 552.113 — Duplicate Worker

Duplicate worker identity must be detected.

---

## 552.114 — Network Partition

Partition semantics explicit.

---

## 552.115 — Split Brain

Scheduler must prevent duplicate exclusive allocations.

---

## 552.116 — Scheduler Leader

Leader/term/epoch where centralized scheduling uses consensus.

---

## 552.117 — Scheduler HA

High availability is optional infrastructure profile.

---

## 552.118 — Scheduler Recovery

Recover desired allocations from durable state.

---

## 552.119 — Allocation Reconciliation

Compare desired vs observed allocation.

---

## 552.120 — Orphan Allocation

Allocation without owner is detected.

---

## 552.121 — Resource Leak

Orphan resources eventually follow cleanup policy.

---

## 552.122 — Device Failure

Failed GPU/NPU removed from scheduling pool.

---

## 552.123 — Device Recovery

Recovered device goes through validation.

---

## 552.124 — Thermal State

Thermal throttling can affect observed capacity.

---

## 552.125 — Power State

Power limits may affect capacity.

---

## 552.126 — Frequency Scaling

CPU/GPU frequency variation recorded where relevant.

---

## 552.127 — Capacity ≠ Nominal Specification

Scheduler must use usable capacity.

---

## 552.128 — Fragmentation

Free resource sum does not guarantee feasible contiguous placement.

---

## 552.129 — Defragmentation

Migration/eviction can defragment resource pools.

---

## 552.130 — Migration Cost

Migration cost included when optimization policy requires.

---

## 552.131 — Migration Safety

Stateful migration requires explicit protocol.

---

## 552.132 — GPU Migration

GPU live migration is provider-dependent.

---

## 552.133 — Model Replication

Model weights may be replicated to satisfy locality.

---

## 552.134 — Replication Cost

Weight replication is accounted.

---

## 552.135 — Model Cache

Cached model artifact does not become authoritative model identity.

---

## 552.136 — Model Version

Placement records exact model version/hash.

---

## 552.137 — Kernel Version

Placement records kernel/backend version when relevant.

---

## 552.138 — Compiler Identity

Compiled kernel identity includes compiler/backend/target.

---

## 552.139 — Numerical Policy

504 numerical policy must survive placement.

---

## 552.140 — Determinism

Deterministic workloads may require deterministic placement.

---

## 552.141 — Reproducible Placement

Placement replay can use captured catalog/policy/state.

---

## 552.142 — Scheduling Replay

Historical decision replay.

---

## 552.143 — Counterfactual Placement

Alternative placement simulation labeled counterfactual.

---

## 552.144 — Explainability

Queries:

```textwhy_placed id="8c9x3n"
why_not_placed
why_migrated
why_preempted
why_gpu_selected
why_gpu_rejected
why_cross_region
```

---

## 552.145 — Explanation Evidence

Reasons reference constraints/capabilities/state.

---

## 552.146 — No Fake Reason

Unknown scheduling reason remains unknown.

---

## 552.147 — Placement Metrics

```text id="j6z3wr"
queue_time
placement_time
fragmentation
utilization
migration_time
startup_time
```

---

## 552.148 — Scheduling Overhead

Scheduler overhead measured separately.

---

## 552.149 — Scalability

Scheduler must support large resource/workload graphs with bounded metadata.

---

## 552.150 — Incremental Scheduling

Small changes should not require full recomputation when safe.

---

## 552.151 — Cache Invalidation

Topology/policy/capacity changes invalidate affected placement cache.

---

## 552.152 — Parallel Scheduling

Independent placement decisions may execute in parallel.

---

## 552.153 — Deterministic Tie Break

Equivalent candidates use stable tie-break rules.

---

## 552.154 — No Accidental Nondeterminism

Hash-map iteration order cannot alter deterministic placement.

---

## 552.155 — Optimization Heuristic

Heuristic result is not optimality proof.

---

## 552.156 — Optimality Claim

Only explicit solver/proof methodology may claim optimality.

---

## 552.157 — Bin-Packing Approximation

Approximation must be identified as approximation.

---

## 552.158 — Cost Objective

Cost-aware placement optional.

---

## 552.159 — Energy Objective

Energy-aware placement optional.

---

## 552.160 — Carbon Objective

Carbon-aware placement optional and evidence-based.

---

## 552.161 — Reliability Objective

Failure-domain diversity can be hard constraint.

---

## 552.162 — Security Objective

Security isolation can be hard constraint.

---

## 552.163 — Quality Objective

Model quality requirements can constrain eligible variants.

---

## 552.164 — Latency Objective

Latency target can be optimization objective/constraint.

---

## 552.165 — Throughput Objective

Throughput optimization explicit.

---

## 552.166 — Objective Conflict

Conflicting objectives require policy-defined ordering/weights.

---

## 552.167 — No Universal Weight

Axiom does not define universal cost/latency/utilization weights.

---

## 552.168 — Admission Revalidation

Before actual allocation, all hard constraints are rechecked.

---

## 552.169 — TOCTOU

Resource availability can change between planning and commit.

---

## 552.170 — Commit Failure

Commit failure triggers recomputation.

---

## 552.171 — Retry

Placement retry bounded.

---

## 552.172 — Scheduler Budget

Scheduler itself has CPU/memory/time budget.

---

## 552.173 — Scheduling Storm

Mass workload changes must be rate-limited/coalesced.

---

## 552.174 — Backpressure

Scheduler admission integrates 550.

---

## 552.175 — Autoscaling Integration

If no feasible placement exists, scheduler may request 551 scaling.

---

## 552.176 — Scaling Loop

Scaling request must not recursively trigger unbounded scheduling loops.

---

## 552.177 — Provisioning Feedback

551 returns capacity status.

---

## 552.178 — No Capacity

State remains `PendingCapacity`.

---

## 552.179 — Policy Block

State remains `PendingPolicy`.

---

## 552.180 — Quota Block

State remains `PendingQuota`.

---

## 552.181 — Resource Block

State remains `PendingResource`.

---

## 552.182 — Compatibility Block

State remains `PendingCompatibility`.

---

## 552.183 — Human Approval

Privileged placement may require 545 approval.

---

## 552.184 — Security Quarantine

547 can prohibit placement of affected artifacts/workloads.

---

## 552.185 — Evidence Gate

546 can require artifact/device evidence.

---

## 552.186 — Tenant Isolation

No cross-tenant resource allocation without explicit policy.

---

## 552.187 — Shared Device

Shared accelerator access must preserve tenant/resource accounting.

---

## 552.188 — Confidential Workload

Sensitive workloads may require dedicated hardware.

---

## 552.189 — Secret Data

Secret data placement respects 528/545 policy.

---

## 552.190 — No Hidden Telemetry

Scheduler telemetry is explicit capability.

---

## 552.191 — Freestanding

Ordinary native programs do not depend on cluster scheduler.

---

## 552.192 — Library Boundary

552 belongs to platform/infrastructure layer.

---

## 552.193 — External Orchestrators

Cloud/Kubernetes/Slurm-like systems integrate through adapters.

---

## 552.194 — Axiom-Native Scheduler

Axiom can implement a native scheduler without external compiler/runtime dependency.

---

## 552.195 — Testing

Required tests:

```text id="w7c4la"
capacity
fragmentation
topology
GPU memory
gang scheduling
preemption
migration
failure
partition
```

---

## 552.196 — Fuzzing

Placement constraints/topology parsers are fuzz-tested.

---

## 552.197 — Deterministic Simulation

Synthetic resource catalog + workload trace + policy must support deterministic replay.

---

## 552.198 — Performance

Scheduling performance is measured with 450/481; no universal scheduler score.

---

## 552.199 — Final Hard Invariant

**Axiom Resource Scheduler phải tách feasibility khỏi optimization, hard constraints khỏi soft preferences, observed capacity khỏi nominal capacity và placement plan khỏi committed allocation. GPU/NPU/CPU/NUMA/network/storage/model/data topology đều phải có identity và capability semantics rõ ràng; distributed training phải hỗ trợ gang scheduling, rendezvous, membership epoch và stale-worker fencing. Placement phải respect quota, tenant isolation, security, data residency, model compatibility, reliability/failure domains, deadline và explicit cost/latency/throughput objectives. Không được có hidden objective hoặc tuyên bố heuristic là optimal. Mọi allocation phải revalidate tại commit, chống stale plan, duplicate allocation, orphan resource và split-brain; scheduler có bounded retry/backpressure/recovery và explainability dựa trên evidence. Autoscaling 551 chỉ được gọi trong policy boundary. Toàn bộ cluster/GPU scheduling layer là infrastructure capability, không phải thành phần bắt buộc của Axiom language/runtime.**

**BOOTSTRAP-552 hoàn tất / LOCKED.**

---

## Tiếp theo

**BOOTSTRAP-553 — AI DATA/COMPUTE PIPELINE ORCHESTRATION, DATA LOCALITY, PREFETCH, CACHING, STREAMING DATASET EXECUTION & END-TO-END TRAINING/INFERENCE PIPELINE SCHEDULING**