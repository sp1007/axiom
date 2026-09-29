# BOOTSTRAP-549 — AI SYSTEM COST ENGINE, RESOURCE ACCOUNTING, TOKEN/COMPUTE METERING, FINOPS, CHARGE-BACK, RESOURCE ATTRIBUTION & COST-AWARE SCHEDULING

**Trạng thái: COMPLETED / LOCKED**

Mục tiêu của `549` là xây dựng một **Cost/Resource Accounting Engine** cho Axiom và hệ sinh thái AI. Nó không chỉ tính tiền; nó phải trả lời được:

- workload nào tiêu tốn CPU/GPU/RAM/VRAM/storage/network;
- model nào tiêu tốn bao nhiêu compute;
- workflow/agent/tool/session nào gây ra chi phí;
- chi phí phát sinh ở đâu và vì sao;
- có thể giới hạn hoặc tối ưu chi phí thế nào;
- attribution có chính xác đến đâu;
- scheduling có thể dùng cost như một constraint nhưng **không được làm thay đổi correctness**.

---

## 549.1 — Cost Architecture

```text id="1r7x4m"
                 Axiom Workload
                       │
          ┌────────────┼────────────┐
          ↓            ↓            ↓
       Compute       Storage      Network
          │            │            │
          └────────────┼────────────┘
                       ↓
                 Metering Layer
                       │
                Resource Events
                       │
                       ▼
                Attribution Engine
                       │
          ┌────────────┼────────────┐
          ↓            ↓            ↓
       Service       Tenant       Workload
          │            │            │
          └────────────┼────────────┘
                       ↓
                 Cost Model
                       │
          ┌────────────┼────────────┐
          ↓            ↓            ↓
       Budget       Forecast      Policy
          │            │            │
          └────────────┼────────────┘
                       ↓
               Cost-Aware Scheduler
```

---

## 549.2 — Cost ≠ Resource Usage

Resource usage là measurement.

Cost là derived value từ usage + pricing/policy.

---

## 549.3 — Resource Identity

```text id="s1l8da"
ResourceId
ResourceKind
Provider
Region
Zone
Device
CapacityClass
```

---

## 549.4 — Resource Kinds

```text
CPU
GPU
NPU
RAM
VRAM
Storage
IOPS
Network
Tokens
Requests
ToolCalls
Energy
```

---

## 549.5 — Usage Record

```text id="m2y8se"
UsageRecord {
    timestamp
    resource
    quantity
    unit
    workload
    source
    measurement_method
}
```

---

## 549.6 — Measurement ≠ Estimate

Measured usage và estimated usage phải được phân biệt.

---

## 549.7 — Measurement Provenance

Mỗi usage measurement phải có source/provider.

---

## 549.8 — Sampling

Nếu metering sử dụng sampling, sampling method phải được ghi.

---

## 549.9 — Counter

Hardware/software counters có thể làm nguồn measurement.

---

## 549.10 — Counter Reset

Counter reset/overflow phải được phát hiện.

---

## 549.11 — CPU Accounting

CPU usage có thể tính theo:

```text
CPU time
cycles
instructions
core-time
```

---

## 549.12 — CPU Time

CPU time ≠ wall-clock time.

---

## 549.13 — GPU Accounting

GPU usage có thể gồm:

```text
device time
kernel time
memory allocated
memory transferred
```

---

## 549.14 — GPU Utilization

GPU utilization không đồng nghĩa với GPU cost.

---

## 549.15 — VRAM

VRAM accounting phải phân biệt:

```text
reserved
allocated
resident
peak
```

---

## 549.16 — RAM

RAM accounting tương tự:

```text
virtual
resident
private
shared
peak
```

---

## 549.17 — Storage

Storage accounting:

```text
bytes stored
bytes read
bytes written
IO operations
```

---

## 549.18 — Network

Network accounting:

```text
bytes sent
bytes received
requests
connections
```

---

## 549.19 — Token Accounting

AI workloads có thể ghi:

```text
input_tokens
output_tokens
cached_tokens
reasoning_tokens?
```

Chỉ ghi loại token nếu model/provider định nghĩa rõ.

---

## 549.20 — Token Identity

Token counts phải reference tokenizer/model identity.

---

## 549.21 — Token ≠ Character

Không được suy ra token cost trực tiếp từ character count.

---

## 549.22 — Cached Token

Cached-token semantics phải explicit.

---

## 549.23 — Model Cost

Model cost record:

```text
ModelId
ModelVersion
Variant
Device
Runtime
Tokens
Compute
```

---

## 549.24 — Agent Cost

Agent cost aggregate:

```text
model
tool
retrieval
storage
workflow
network
```

---

## 549.25 — Workflow Cost

Workflow cost được aggregate theo:

```text
WorkflowRunId
NodeId
Attempt
```

---

## 549.26 — Tool Cost

Tool cost được attribute theo ToolCallId.

---

## 549.27 — Retrieval Cost

RAG cost có thể phân biệt:

```text
embedding
vector_search
lexical_search
rerank
storage
network
```

---

## 549.28 — Dataset Cost

Training/data pipeline có thể track:

```text
ingestion
storage
decode
preprocess
augmentation
transfer
compute
```

---

## 549.29 — Training Cost

Training attribution:

```text
run
epoch
step
model
dataset
device
```

---

## 549.30 — Evaluation Cost

Evaluation run từ 527 được accounting riêng.

---

## 549.31 — Build Cost

487 compiler/build nodes cũng có thể được meter:

```text
compile CPU
memory
disk
cache
remote execution
```

---

## 549.32 — Developer Tool Cost

LSP/index/doc/test/profiling workloads có thể accounting nhưng không bắt buộc.

---

## 549.33 — Resource Ownership

Usage phải reference workload owner/context.

---

## 549.34 — Context Identity

Context có thể là:

```text
process
task
job
workflow
agent
session
tenant
project
```

---

## 549.35 — Hierarchical Attribution

```text
Organization
  ↓
Tenant
  ↓
Project
  ↓
Application
  ↓
Workflow
  ↓
Task
  ↓
Operation
```

---

## 549.36 — Attribution ≠ Ownership

Workload gây usage và entity chịu trách nhiệm accounting có thể khác nhau.

---

## 549.37 — Shared Resource

Shared resource cần explicit allocation method.

---

## 549.38 — Shared GPU

GPU cost có thể phân bổ theo:

```text
device-time
memory-time
kernel-time
allocation policy
```

---

## 549.39 — Shared Cache

Cache cost attribution phải tránh double-counting.

---

## 549.40 — Shared Model Weights

Shared model memory không được tính đầy đủ cho từng tenant nếu cùng physical allocation.

---

## 549.41 — Amortized Cost

Shared resource có thể dùng amortization.

---

## 549.42 — Attribution Method

Mọi derived allocation phải lưu:

```text
method
version
inputs
```

---

## 549.43 — Exact Attribution

Exact attribution được dùng khi hardware/runtime có accounting chính xác.

---

## 549.44 — Estimated Attribution

Estimate phải được đánh dấu `estimated`.

---

## 549.45 — Unknown Attribution

Không đủ dữ liệu → `unknown`, không được bịa.

---

## 549.46 — Attribution Confidence

Nếu có confidence, phải reference methodology/calibration.

---

## 549.47 — Double Counting

Engine phải detect potential double counting giữa parent và child measurements.

---

## 549.48 — Nested Usage

Parent aggregate có thể bao gồm child usage.

---

## 549.49 — Exclusive Usage

Engine phải phân biệt:

```text
inclusive
exclusive
```

---

## 549.50 — Cost Model

```text id="0l8gxu"
CostModel {
    resource
    unit
    price
    currency
    validity
    source
    version
}
```

---

## 549.51 — Price ≠ Cost

Provider price là input.

Actual internal cost có thể khác.

---

## 549.52 — Currency

Currency code phải explicit.

---

## 549.53 — Price Validity

Price có thời gian hiệu lực.

---

## 549.54 — Tiered Pricing

Pricing tiers phải được biểu diễn rõ.

---

## 549.55 — Minimum Charge

Provider minimum-charge rules có thể được model.

---

## 549.56 — Reservation

Reserved resources có pricing semantics riêng.

---

## 549.57 — Spot/Preemptible

Preemptible capacity cost model phải giữ volatility.

---

## 549.58 — Region Pricing

Region là dimension của cost model.

---

## 549.59 — Device Pricing

GPU/NPU model identity là pricing dimension khi cần.

---

## 549.60 — Network Pricing

Ingress/egress có thể có pricing khác nhau.

---

## 549.61 — Storage Pricing

Capacity/IO/egress có thể là các cost dimensions khác nhau.

---

## 549.62 — Cost Snapshot

Một cost calculation phải reference exact price model/version.

---

## 549.63 — Historical Recalculation

Historical usage không được tự động thay đổi chỉ vì pricing hiện tại thay đổi.

---

## 549.64 — Billing ≠ Metering

Axiom metering không phải billing system.

---

## 549.65 — Billing Export

Billing records có thể export sang external provider.

---

## 549.66 — Chargeback

Chargeback là policy layer.

---

## 549.67 — Showback

Showback cung cấp usage/cost visibility mà không nhất thiết charge.

---

## 549.68 — Tenant Budget

```text id="x1a8a5"
Budget {
    scope
    period
    limit
    currency/resource
    policy
}
```

---

## 549.69 — Budget Scope

Budget có thể áp dụng:

```textorganization
tenant
project
application
workflow
agent
model
```

---

## 549.70 — Budget Period

```texthour
day
month
run
custom
```

---

## 549.71 — Resource Budget

Budget có thể giới hạn trực tiếp quantity thay vì monetary cost.

---

## 549.72 — Hard Budget

Hard budget có thể reject/throttle workload khi đạt limit.

---

## 549.73 — Soft Budget

Soft budget tạo alert nhưng không bắt buộc stop.

---

## 549.74 — Budget Reserve

Workflow có thể reserve budget trước khi chạy.

---

## 549.75 — Budget Release

Unused reservation phải được release.

---

## 549.76 — Concurrent Budget

Budget accounting phải handle concurrent operations atomic hoặc transactional.

---

## 549.77 — Race-Free Budget

Hai workers không được cùng consume một phần budget mà accounting không phát hiện.

---

## 549.78 — Budget Overrun

Overrun phải explicit.

---

## 549.79 — No Silent Denial

Rejected workload phải có machine-readable reason.

---

## 549.80 — Budget Policy

```text
Reject
Throttle
Queue
Degrade
RequireApproval
```

---

## 549.81 — Cost-Aware Scheduling

Scheduler 471/534 có thể sử dụng cost làm constraint.

---

## 549.82 — Correctness First

Cost optimization không được phá correctness contract.

---

## 549.83 — SLA/SLO Interaction

Cost-aware scheduling phải respect 548 SLO policy.

---

## 549.84 — Deadline

Không được chọn phương án rẻ hơn nếu làm vi phạm explicit deadline contract.

---

## 549.85 — Quality Constraint

AI workload có thể yêu cầu model/evaluation quality constraints từ 527/533.

---

## 549.86 — Model Routing

Router có thể lựa chọn variant dựa trên:

```textcost
latency
capacity
quality constraints
```

---

## 549.87 — No Universal Cheapest

Không có universal “best/cheapest” model; lựa chọn phụ thuộc constraints.

---

## 549.88 — Fallback

Fallback model phải compatible theo 539.

---

## 549.89 — Precision Tradeoff

Quantization/precision fallback phải giữ numerical policy.

---

## 549.90 — Batch Economics

Dynamic batching có thể giảm cost nhưng phải respect latency/SLO.

---

## 549.91 — Batch Size

Batch scheduler có thể optimize:

```textthroughput
latency
memory
cost
```

---

## 549.92 — Continuous Batching

509/529 continuous batching accounting phải track per-request attribution.

---

## 549.93 — Shared Batch Attribution

Batch-level compute phải phân bổ theo explicit method.

---

## 549.94 — Padding Cost

Padding/packing overhead có thể được accounted separately.

---

## 549.95 — Cache Economics

Cache hit/miss phải được đo.

---

## 549.96 — Cache Benefit

Cache saving là derived metric, không phải measured cost.

---

## 549.97 — Prefix Cache

LLM prefix-cache savings reference exact cache policy/model.

---

## 549.98 — Embedding Cache

512 embedding cache cost attribution.

---

## 549.99 — Compilation Cache

504/487 compilation cache cost/savings.

---

## 549.100 — Remote Cache

Remote cache network + storage cost phải được tính nếu configured.

---

## 549.101 — Remote Execution

487 remote execution phải attribute:

```textworker compute
network transfer
queue time
cache
```

---

## 549.102 — Remote Cost

Remote worker provider cost ≠ local user-visible latency.

---

## 549.103 — Queue Time

Queue time được ghi riêng.

---

## 549.104 — Waiting Cost

Idle waiting không được tự động tính như compute usage.

---

## 549.105 — Allocated Capacity

Reserved/allocated capacity khác actual consumption.

---

## 549.106 — Idle Capacity

Idle resource có thể có cost nhưng attribution policy phải rõ.

---

## 549.107 — Autoscaling

534 autoscaler có thể sử dụng cost constraints.

---

## 549.108 — Scaling Cost

Scale-up/down event tạo resource-cost evidence.

---

## 549.109 — Hysteresis

Cost-driven scaling phải tránh oscillation.

---

## 549.110 — Minimum Lifetime

Provider/resource minimum billing periods được model nếu có.

---

## 549.111 — Spot Interruption

Preemptible interruption phải được tính vào reliability/cost model.

---

## 549.112 — Reliability Tradeoff

Cost reduction không được tự động override 548 reliability policy.

---

## 549.113 — Capacity Tradeoff

Scheduler có thể trade cost/capacity chỉ trong policy bounds.

---

## 549.114 — Carbon/Energy

Energy có thể là optional resource dimension.

---

## 549.115 — Energy Measurement

Energy measured/estimated distinction.

---

## 549.116 — Carbon Estimate

Carbon estimate phải reference location/grid/model/source.

---

## 549.117 — Carbon ≠ Cost

Environmental metric không tự động quy thành monetary cost.

---

## 549.118 — Cost Forecast

Forecast sử dụng historical usage/pricing/workload assumptions.

---

## 549.119 — Forecast Uncertainty

Forecast phải expose uncertainty/range khi methodology hỗ trợ.

---

## 549.120 — Forecast ≠ Guarantee

Forecast không phải commitment.

---

## 549.121 — Capacity Forecast

548 capacity planning có thể sử dụng 549 cost data.

---

## 549.122 — Anomaly Detection

Cost anomaly detection tích hợp 547/548.

---

## 549.123 — Cost Anomaly

Ví dụ:

```textunexpected GPU usage
token spike
storage growth
network egress spike
```

---

## 549.124 — Baseline

Cost anomaly baseline versioned.

---

## 549.125 — Seasonality

Seasonality có thể được model.

---

## 549.126 — False Positive

Cost anomaly chỉ là finding nếu evidence đủ.

---

## 549.127 — AI Cost Analysis

AI có thể giải thích:

```textwhy_cost_increased
why_gpu_used
why_model_fallback
why_cache_missed
why_workload_scaled
```

---

## 549.128 — Evidence-Based Explanation

Explanation phải reference usage/cost records.

---

## 549.129 — No Fabricated Savings

AI không được tuyên bố savings không có evidence.

---

## 549.130 — Optimization Proposal

AI có thể đề xuất:

```textbatching
cache
model_variant
device
scheduling
```

---

## 549.131 — Proposal ≠ Action

Optimization proposal phải qua policy/scheduler.

---

## 549.132 — Cost Optimization Safety

Cost optimization không được bypass:

```textsecurity
privacy
correctness
SLO
quality
```

---

## 549.133 — Tenant Isolation

Cost records không leak cross-tenant data.

---

## 549.134 — Cost Privacy

Usage patterns có thể là sensitive metadata.

---

## 549.135 — Token Privacy

Token counts có thể reveal workload information.

---

## 549.136 — Model Privacy

Model usage may expose private deployment details.

---

## 549.137 — Billing Privacy

Chargeback records access-controlled.

---

## 549.138 — Redaction

Exports support redaction.

---

## 549.139 — Retention

Cost records have retention policy.

---

## 549.140 — Audit

Budget/policy changes are audited.

---

## 549.141 — Price Source

External price feeds are provenance-tracked.

---

## 549.142 — Price Tampering

Price data integrity must be verified where authoritative billing depends on it.

---

## 549.143 — Billing Authority

External billing provider remains authoritative for provider invoice unless explicitly replaced.

---

## 549.144 — Reconciliation

Axiom usage can be reconciled with provider billing.

---

## 549.145 — Reconciliation Difference

Differences are preserved, not silently adjusted.

---

## 549.146 — Rounding

Cost rounding rules explicit.

---

## 549.147 — Precision

Internal cost arithmetic uses sufficient precision.

---

## 549.148 — Currency Conversion

FX conversion uses timestamp/source/rate identity.

---

## 549.149 — No Implicit FX

Different currencies cannot be combined without explicit conversion.

---

## 549.150 — Tax

Tax is external billing/policy metadata unless explicitly configured.

---

## 549.151 — Cost Allocation Graph

```text id="r3n5tf"
Resource
   ↓
Usage
   ↓
Operation
   ↓
Workload
   ↓
Tenant
   ↓
Cost Center
```

---

## 549.152 — Cost Center

Cost center identity/version explicit.

---

## 549.153 — Project Attribution

Project identity from 432.

---

## 549.154 — Application Attribution

489 application identity.

---

## 549.155 — Deployment Attribution

534 deployment/revision.

---

## 549.156 — Model Attribution

533 model/version.

---

## 549.157 — Agent Attribution

511/535 agent/version.

---

## 549.158 — Workflow Attribution

540/541 workflow/version/run.

---

## 549.159 — Tool Attribution

513 tool/version/call.

---

## 549.160 — Dataset Attribution

528 dataset/version.

---

## 549.161 — Build Attribution

487 BuildNode.

---

## 549.162 — Compiler Attribution

Compiler build/version/target/profile.

---

## 549.163 — Runtime Attribution

Runtime capability/profile.

---

## 549.164 — Device Attribution

Device identity and allocation.

---

## 549.165 — Hardware Partition

MIG/partitioned GPU/NPU resource identity where available.

---

## 549.166 — Virtualized Resource

VM/container resource allocation must distinguish host physical resource.

---

## 549.167 — Container Attribution

Container/process identity.

---

## 549.168 — Kubernetes-like Environment

External orchestrator integration is optional; Axiom semantics remain provider-neutral.

---

## 549.169 — Serverless

Invocation-based resources can be represented.

---

## 549.170 — Reserved Capacity

Reserved resource cost allocation policy explicit.

---

## 549.171 — Shared Infrastructure

Infrastructure overhead can be amortized by policy.

---

## 549.172 — Overhead

Platform overhead must not silently disappear from total cost.

---

## 549.173 — Unallocated Cost

Unknown/unallocated cost is a valid bucket.

---

## 549.174 — Allocation Completeness

Accounting can report allocated vs unallocated usage.

---

## 549.175 — Cost Coverage

Coverage is measurement metadata, not quality score.

---

## 549.176 — Metering Failure

Meter failure creates explicit gap.

---

## 549.177 — Gap Detection

Missing interval detection.

---

## 549.178 — No Fake Zero

Missing data ≠ zero usage.

---

## 549.179 — Counter Wrap

Counter wrap is handled explicitly.

---

## 549.180 — Clock Alignment

Usage events across systems require timestamp alignment semantics.

---

## 549.181 — Monotonic Duration

Duration accounting should prefer monotonic clocks where appropriate.

---

## 549.182 — Wall Time

Billing periods use wall/calendar time explicitly.

---

## 549.183 — Time Zone

Billing period timezone must be explicit.

---

## 549.184 — DST

Calendar billing windows account for DST semantics.

---

## 549.185 — Distributed Usage

Cross-region usage preserves source timestamps.

---

## 549.186 — Late Usage

Late-arriving usage can update accounting without corrupting historical identity.

---

## 549.187 — Correction

Corrections are append-only adjustments.

---

## 549.188 — Immutable Usage

Raw usage records are immutable.

---

## 549.189 — Derived Cost

Derived cost records reference source usage and pricing versions.

---

## 549.190 — Reproducibility

Cost calculation can be reproduced from:

```textusage
pricing
allocation_policy
configuration
```

---

## 549.191 — Cost Query API

```textusage(scope, window)
cost(scope, window)
allocation(resource)
budget(scope)
forecast(scope)
anomaly(scope)
```

---

## 549.192 — Explain API

```textwhy_cost
why_allocated
why_budget_exceeded
why_scheduled
why_scaled
```

---

## 549.193 — Scheduler Query

Scheduler có thể query:

```textestimated_cost
capacity
deadline
SLO
quality_constraints
```

---

## 549.194 — Cost Constraint

Cost là constraint/optimization objective được policy chỉ định.

---

## 549.195 — No Hidden Objective

Scheduler không được âm thầm tối ưu cost nếu application không yêu cầu.

---

## 549.196 — Cost Policy

```textminimize_cost
maximize_capacity_under_budget
meet_deadline_under_budget
```

đều là explicit policy.

---

## 549.197 — Deterministic Policy

Với cùng state/input/policy, scheduling policy phải deterministic trừ khi explicit stochastic policy.

---

## 549.198 — Testability

Cost engine phải hỗ trợ synthetic resource meters, fixed pricing và deterministic clocks.

---

## 549.199 — Final Hard Invariant

**Axiom Cost Engine phải phân biệt rõ resource measurement, attribution, pricing, derived cost, budget, forecast và optimization. Mọi usage phải có identity/provenance/unit/time/scope; measured, estimated và unknown không được đánh đồng; missing usage không được coi là zero. Shared resources phải có allocation method/version và chống double-counting. Cost-aware scheduling chỉ được hoạt động khi policy yêu cầu và không được phá correctness, security, privacy, model compatibility, numerical policy hoặc reliability/SLO. AI chỉ có thể phân tích evidence và đề xuất tối ưu; không được tự ý thay đổi resource policy hay tạo cost-saving claim không có evidence. Cost accounting phải deterministic/reproducible khi inputs cố định, immutable ở raw layer, append-only ở correction layer, tenant-isolated và optional đối với ứng dụng Axiom không sử dụng accounting.**

**BOOTSTRAP-549 hoàn tất / LOCKED.**

---

# BOOTSTRAP-550 — RESOURCE GOVERNANCE, MULTI-TENANCY, QUOTA, FAIRNESS, PRIORITY, ADMISSION CONTROL & WORKLOAD ISOLATION

**Trạng thái: COMPLETED / LOCKED**

`549` đo **resource/cost**. `550` quyết định **ai được sử dụng resource nào, bao nhiêu, khi nào và trong điều kiện nào**, đặc biệt khi nhiều workload cùng chia sẻ một hệ thống.

### 550.1 — Architecture

```text id="j5x0rc"
                  Resource Pool
                       │
               ┌───────┴───────┐
               ▼               ▼
          Capacity          Policy
               │               │
               └───────┬───────┘
                       ▼
                Admission Control
                       │
              ┌────────┼────────┐
              ▼        ▼        ▼
           Quota    Priority   Fairness
              │        │        │
              └────────┼────────┘
                       ▼
                  Scheduler
                       │
          ┌────────────┼────────────┐
          ▼            ▼            ▼
       Tenant A     Tenant B     Tenant C
```

---

## 550.2 — Multi-Tenancy

Tenant là administrative/resource isolation boundary, không phải security boundary duy nhất.

---

## 550.3 — Tenant Identity

```text
TenantId
OrganizationId
ProjectId
```

---

## 550.4 — Tenant Context

Mọi resource request có thể mang tenant context.

---

## 550.5 — Tenant Isolation

Isolation level explicit:

```textlogical
process
container
VM
physical
```

---

## 550.6 — Security Boundary

Resource quota không thay thế capability/authorization của 490/545.

---

## 550.7 — Quota

```text id="1y0x1k"
Quota {
    scope
    resource
    limit
    window
    burst
    policy
}
```

---

## 550.8 — Hard Quota

Hard quota không được vượt nếu resource contract yêu cầu strict enforcement.

---

## 550.9 — Soft Quota

Soft quota có thể cảnh báo/throttle.

---

## 550.10 — Burst

Burst capacity có giới hạn explicit.

---

## 550.11 — Concurrency Quota

Số workload concurrent có thể giới hạn.

---

## 550.12 — CPU Quota

CPU quota có thể tính theo:

```textcores
cpu-time
shares
```

---

## 550.13 — GPU Quota

GPU quota có thể là:

```textdevices
device-time
memory
partitions
```

---

## 550.14 — VRAM Quota

Reserved/allocated/peak semantics phải phân biệt.

---

## 550.15 — Memory Quota

RAM limit có explicit behavior khi đạt giới hạn.

---

## 550.16 — Storage Quota

Capacity/IOPS/write-rate/read-rate có thể tách riêng.

---

## 550.17 — Network Quota

Bandwidth/connections/requests có thể giới hạn.

---

## 550.18 — Token Quota

AI workloads có:

```textinput
output
total
```

quota.

---

## 550.19 — Tool Quota

Agent tool-call rate/concurrency quota.

---

## 550.20 — Workflow Quota

Concurrent workflow/run/step quota.

---

## 550.21 — Budget Integration

549 monetary/resource budgets có thể feed admission.

---

## 550.22 — Admission Request

```text id="z8e9e4"
AdmissionRequest {
    workload
    tenant
    resources
    deadline?
    priority
    capabilities
    policy
}
```

---

## 550.23 — Admission Decision

```text
Admit
Queue
Throttle
Reject
Degrade
RequireApproval
```

---

## 550.24 — Decision Reason

Mọi reject/throttle/degrade phải có reason code.

---

## 550.25 — Admission Atomicity

Admission và quota reservation phải atomic theo resource policy.

---

## 550.26 — Reservation

Reservation có expiry.

---

## 550.27 — Reservation Release

Completed/cancelled workload releases unused reservation.

---

## 550.28 — Leaked Reservation

Reservation cleanup phải có recovery mechanism.

---

## 550.29 — Priority

Priority là policy value, không phải security authority.

---

## 550.30 — Priority Range

Priority levels/range project-defined.

---

## 550.31 — Priority Inversion

Scheduler phải có mechanism để tránh pathological priority inversion where required.

---

## 550.32 — Fairness

Fairness là policy-defined allocation objective.

---

## 550.33 — No Universal Fairness

Axiom không hard-code một fairness algorithm duy nhất.

---

## 550.34 — Fair Share

Potential policy:

```text id="v9u5no"
fair_share =
    allocated_capacity / entitled_capacity
```

Nhưng formula là policy/configurable.

---

## 550.35 — Weighted Fairness

Tenant weights explicit.

---

## 550.36 — Hierarchical Fairness

```textOrganization
 → Tenant
   → Project
     → Workload
```

---

## 550.37 — Starvation

Scheduler phải detect starvation risk.

---

## 550.38 — Aging

Priority aging có thể được bật explicit.

---

## 550.39 — Preemption

Preemption là explicit capability.

---

## 550.40 — Preemption Safety

Stateful/non-interruptible workloads cần checkpoint or safe cancellation semantics.

---

## 550.41 — GPU Preemption

GPU preemption phụ thuộc hardware/backend.

---

## 550.42 — Memory Pressure

Memory pressure có states:

```textNormal
Warning
Critical
Exhausted
```

---

## 550.43 — Memory Reclamation

Reclamation order explicit.

---

## 550.44 — Cache Eviction

Caches là first candidates where policy permits.

---

## 550.45 — Model Eviction

534 model instances có thể unload theo eviction policy.

---

## 550.46 — Session Eviction

Stateful sessions chỉ eviction nếu persistence/recovery contract cho phép.

---

## 550.47 — Workflow Eviction

Durable workflow state phải persist trước eviction nếu required.

---

## 550.48 — OOM

OOM behavior không được giả định universal.

---

## 550.49 — OOM Policy

```text
Reject
Evict
Degrade
Kill
Escalate
```

---

## 550.50 — OOM Evidence

OOM events integrate 547/548/549.

---

## 550.51 — No Cross-Tenant Kill

One tenant's resource pressure không tự động cho phép kill another tenant workload.

---

## 550.52 — Isolation

Cross-tenant resource interference phải measurable.

---

## 550.53 — Noisy Neighbor

System có thể detect noisy-neighbor behavior.

---

## 550.54 — Attribution

549 attribution links noisy workload.

---

## 550.55 — Throttling

Throttling mechanism explicit:

```textCPU quota
network shaping
request rate
queue delay
GPU admission
```

---

## 550.56 — Rate Limit

Rate limit dimensions explicit.

---

## 550.57 — Concurrency Limit

Concurrent operation limit distinct from rate limit.

---

## 550.58 — Queue Limit

Queue depth/time limit explicit.

---

## 550.59 — Queue Overflow

Policy:

```textReject
Drop
Degrade
Backpressure
```

---

## 550.60 — Backpressure

Backpressure integrates 471/472/473/529.

---

## 550.61 — Tenant Backpressure

Tenant-specific backpressure possible.

---

## 550.62 — Global Backpressure

Global resource exhaustion can propagate admission pressure.

---

## 550.63 — Deadlines

Admission should consider 474 deadlines.

---

## 550.64 — Deadline-Aware Scheduling

Scheduling may prioritize tasks approaching deadline within policy.

---

## 550.65 — Deadline Miss

Deadline miss is explicit outcome, not silent retry forever.

---

## 550.66 — Cost-Aware Scheduling

549 cost objective can combine with quota.

---

## 550.67 — SLO-Aware Scheduling

548 SLO constraints can combine with quota.

---

## 550.68 — Quality-Aware Scheduling

527/533 evaluation constraints.

---

## 550.69 — Security-Aware Scheduling

545 capability constraints.

---

## 550.70 — Device Capability

503/504 device requirements.

---

## 550.71 — Placement

534 placement constraints.

---

## 550.72 — Affinity

Workload can request affinity.

---

## 550.73 — Anti-Affinity

Workload can request anti-affinity.

---

## 550.74 — NUMA

471/534 NUMA locality.

---

## 550.75 — Data Locality

512/528 dataset locality.

---

## 550.76 — Model Locality

533/534 model placement.

---

## 550.77 — Cache Locality

509 KV/cache locality.

---

## 550.78 — Stateful Placement

Session/workflow state may constrain relocation.

---

## 550.79 — Stateless Placement

Stateless workloads can migrate more freely.

---

## 550.80 — Migration

Migration has cost/resource requirements.

---

## 550.81 — Live Migration

Platform capability-dependent.

---

## 550.82 — Drain

Node draining prevents new admission while allowing existing workloads to finish.

---

## 550.83 — Forced Drain

Forced drain requires cancellation policy.

---

## 550.84 — Maintenance

Maintenance windows integrate 470/548.

---

## 550.85 — Resource Pool

```text id="0k7pab"
ResourcePool {
    identity
    capacity
    allocation
    policy
}
```

---

## 550.86 — Pool Hierarchy

Pools can be nested.

---

## 550.87 — Dedicated Pool

Dedicated tenant/device pools supported.

---

## 550.88 — Shared Pool

Shared pools require allocation/fairness policy.

---

## 550.89 — Reservation Pool

Reserved capacity distinct from general capacity.

---

## 550.90 — Emergency Pool

Critical workloads may use reserved emergency capacity.

---

## 550.91 — Emergency Authority

Emergency resource use requires explicit policy.

---

## 550.92 — Quota Borrowing

Tenant borrowing may be allowed only if configured.

---

## 550.93 — Borrowed Capacity

Borrowed capacity records lender/borrower/expiry.

---

## 550.94 — Reclaim

Borrowed capacity can be reclaimed according to contract.

---

## 550.95 — Priority Class

Priority class versioned.

---

## 550.96 — Policy Version

Admission decisions reference exact policy version.

---

## 550.97 — Configuration Version

470 config identity included.

---

## 550.98 — Scheduling Evidence

Scheduler records:

```textcandidates id="2l9k4s"
constraints
decision
reason
```

---

## 550.99 — Explainability

Queries:

```textwhy_rejected
why_queued
why_throttled
why_preempted
why_placed
why_not_placed
```

---

## 550.100 — No Hidden Objective

Scheduler không được âm thầm optimize cost, fairness, latency hoặc utilization ngoài policy.

---

## 550.101 — Determinism

Same state + policy + request → deterministic decision unless explicit stochastic scheduling.

---

## 550.102 — Stochastic Scheduling

Random scheduling phải record seed/policy.

---

## 550.103 — Admission Fairness

Admission ordering phải phù hợp với declared policy.

---

## 550.104 — Queue Fairness

Queue fairness có thể khác admission fairness.

---

## 550.105 — Work Conservation

Work-conserving behavior không phải universal requirement.

---

## 550.106 — Reserved Capacity

Reserved resources có thể intentionally remain idle.

---

## 550.107 — Utilization

Low utilization không tự động là failure.

---

## 550.108 — Reliability

Resource policy không được violate 548 reliability constraints.

---

## 550.109 — Security

Quota policy không được bypass 490/545 authorization.

---

## 550.110 — Privacy

Scheduling metadata access-controlled.

---

## 550.111 — Tenant Metadata

Tenant A không được xem private workload details của Tenant B chỉ vì shared scheduler.

---

## 550.112 — Resource Fingerprinting

Cross-tenant hardware information exposure phải được hạn chế.

---

## 550.113 — Side Channels

Resource isolation không đảm bảo loại bỏ mọi hardware side channel.

---

## 550.114 — Strong Isolation

Physical/VM isolation có thể được yêu cầu bởi security policy.

---

## 550.115 — GPU Isolation

GPU isolation level phải explicit.

---

## 550.116 — CPU Isolation

CPU affinity/cgroup-like mechanisms provider-dependent.

---

## 550.117 — Memory Isolation

Memory limits không đảm bảo cryptographic isolation.

---

## 550.118 — Network Isolation

Network namespaces/firewalls/capabilities provider-dependent.

---

## 550.119 — Storage Isolation

Storage quotas và ACLs distinct.

---

## 550.120 — Capability Integration

490 capabilities must be checked before resource allocation where authority matters.

---

## 550.121 — Tool Scheduling

513 tool calls subject to tenant/tool quotas.

---

## 550.122 — Agent Scheduling

511 agents subject to task/session/resource policies.

---

## 550.123 — Workflow Scheduling

540 workflows subject to concurrency/budget/deadline limits.

---

## 550.124 — Model Serving

529/534 request scheduler integration.

---

## 550.125 — Continuous Batching

509 batch admission must preserve request isolation and cancellation.

---

## 550.126 — Batch Fairness

Batch formation cannot arbitrarily starve low-volume tenants.

---

## 550.127 — Batch Cost

549 accounting preserves per-request attribution.

---

## 550.128 — Training Scheduling

Training jobs can have priority/preemption/checkpoint policy.

---

## 550.129 — Evaluation Scheduling

Evaluation workloads can be scheduled separately from production workloads.

---

## 550.130 — Build Scheduling

487 build jobs can use dedicated resource pools.

---

## 550.131 — Interactive Priority

LSP/editor workloads may use interactive priority if configured.

---

## 550.132 — Realtime Priority

461 realtime workloads require bounded scheduling and must not be subjected to arbitrary queue delays.

---

## 550.133 — Realtime Isolation

Realtime resource pools can be dedicated.

---

## 550.134 — Background Work

Background tasks should yield under configured pressure.

---

## 550.135 — Garbage Collection

Axiom resource governance must never imply mandatory GC.

---

## 550.136 — Hidden Scheduler

Ordinary native programs do not acquire a hidden global multi-tenant scheduler.

---

## 550.137 — Local Scheduler

Application-level scheduler is explicit.

---

## 550.138 — Cluster Scheduler

534 control plane is explicit infrastructure.

---

## 550.139 — External Scheduler

Kubernetes/Slurm/cloud schedulers are integrations, not language semantics.

---

## 550.140 — Resource Policy DSL

Resource policy can be declarative.

Conceptually:

```text
resource_policy {
    tenant "research" {
        gpu = 4
        priority = 70
        burst = true
    }

    tenant "production" {
        gpu = 8
        priority = 100
    }
}
```

---

## 550.141 — Policy Compilation

Policy can compile into admission/scheduling structures.

---

## 550.142 — Policy Validation

Static validation catches:

- impossible quotas;
- conflicting limits;
- unreachable pools;
- priority inversion;
- invalid resource references.

---

## 550.143 — Policy Simulation

Policy can be tested with synthetic workload traces.

---

## 550.144 — Policy Diff

486 semantic diff supports resource-policy changes.

---

## 550.145 — Policy Migration

539 version migration can apply to resource policies where schema changes.

---

## 550.146 — Audit

Admission/preemption/quota changes are audited.

---

## 550.147 — Incident Integration

547 can temporarily isolate or throttle a resource scope.

---

## 550.148 — Reliability Integration

548 can trigger scaling/admission changes according to policy.

---

## 550.149 — Cost Integration

549 can trigger budget-aware scheduling.

---

## 550.150 — Governance Integration

545 remains final authority for security-sensitive actions.

---

## 550.151 — Recovery

550 state must recover after scheduler/control-plane restart.

---

## 550.152 — Durable Policy

Active policy/version persisted or reproducibly reconstructed.

---

## 550.153 — Reservation Recovery

Lost scheduler state cannot silently duplicate reservations.

---

## 550.154 — Lease

Resource leases have expiry.

---

## 550.155 — Fencing

Stale scheduler instances cannot allocate already-reclaimed capacity.

---

## 550.156 — Distributed Consistency

Cluster resource state uses 501/502 semantics where strong consistency required.

---

## 550.157 — Split Brain

Two scheduler leaders cannot both allocate same exclusive resource.

---

## 550.158 — Capacity Truth

Observed capacity and desired capacity are distinct.

---

## 550.159 — Device Failure

Failed device is removed from allocatable capacity.

---

## 550.160 — Device Recovery

Recovered device must pass health/readiness checks.

---

## 550.161 — Quarantine

Faulty device can be quarantined.

---

## 550.162 — Model Resource Recovery

534 model instance state reconciled after resource loss.

---

## 550.163 — Session Recovery

Session migration respects 539 compatibility.

---

## 550.164 — Workflow Recovery

Durable workflows resume from checkpoint.

---

## 550.165 — Cancellation

Cancelled workloads release resource reservations.

---

## 550.166 — Cancellation Race

Late completion cannot resurrect released resources.

---

## 550.167 — Idempotency

Resource allocation commands are idempotent where distributed retries occur.

---

## 550.168 — Exactly Once

No universal exactly-once claim for external resource allocation.

---

## 550.169 — Overcommit

Overcommit is explicit policy.

---

## 550.170 — Memory Overcommit

If supported, semantics and failure behavior must be explicit.

---

## 550.171 — CPU Overcommit

CPU shares are not guaranteed CPU capacity.

---

## 550.172 — GPU Overcommit

GPU memory overcommit must not be silently assumed safe.

---

## 550.173 — Quota Hierarchy

Child quota cannot exceed parent quota unless borrowing policy permits.

---

## 550.174 — Quota Conflict

Conflicting quotas produce deterministic diagnostics.

---

## 550.175 — Unlimited

`unlimited` must be explicit and still subject to physical capacity/security.

---

## 550.176 — Zero Quota

Zero quota is valid and means no admission unless exception policy exists.

---

## 550.177 — Negative Quota

Negative quota is invalid.

---

## 550.178 — Unit Safety

CPU/GPU/memory/network quota units are type-safe.

---

## 550.179 — Time Units

Rate quotas distinguish:

```textper_second
per_minute
per_hour
```

---

## 550.180 — Burst Window

Burst semantics explicitly define accumulation and expiration.

---

## 550.181 — Rate Limit Clock

Rate limiting uses appropriate monotonic/wall-clock semantics.

---

## 550.182 — Distributed Rate Limit

Distributed counters require explicit consistency model.

---

## 550.183 — Approximate Rate Limit

Approximate counters must be marked approximate.

---

## 550.184 — Exact Quota

Exact quota enforcement requires authoritative state.

---

## 550.185 — Resource Accounting

550 consumes 549 measurements but does not redefine them.

---

## 550.186 — Resource Policy Query

AI can query:

```textquota
capacity
placement
reservation
fairness
priority
```

---

## 550.187 — AI Recommendation

AI may propose policy changes but cannot silently apply them.

---

## 550.188 — Human Approval

High-impact quota/tenant policy changes can require approval.

---

## 550.189 — Change Simulation

Proposed policy can be evaluated against historical workloads.

---

## 550.190 — Counterfactual

Simulation results must be labeled as counterfactual, not observed reality.

---

## 550.191 — No Fabricated Capacity

AI cannot infer capacity that is not measured/provider-declared.

---

## 550.192 — No Universal Fairness Score

Fairness reports remain metric/policy-specific.

---

## 550.193 — Test

Tests cover:

```textquota exhaustion
burst
fairness
preemption
migration
device failure
scheduler restart
partition
```

---

## 550.194 — Fuzzing

Admission/policy parsers and schedulers are fuzzable.

---

## 550.195 — Deterministic Replay

Historical scheduling decisions can be replayed with captured state/policy.

---

## 550.196 — Performance

Scheduler overhead must be measurable through 450/481.

---

## 550.197 — Scalability

Large tenant/workload counts require bounded metadata and scheduling complexity.

---

## 550.198 — Optionality

Resource governance is infrastructure/library functionality, not mandatory language/runtime behavior.

---

## 550.199 — Final Hard Invariant

**Axiom Resource Governance phải cung cấp quota, reservation, admission, priority, fairness, preemption, isolation, placement và resource scheduling với semantics explicit, deterministic và auditable. Quota/resource accounting không thay thế security authorization; scheduler không được có hidden optimization objective. Multi-tenant isolation phải phân biệt logical/process/container/VM/physical isolation và không được hứa hẹn loại bỏ mọi hardware side-channel. Resource reservations, leases và distributed scheduler state phải chống stale allocation/double allocation bằng explicit consistency/fencing semantics. Cost, SLO, quality, security, deadline và device capability có thể trở thành scheduling constraints nhưng không được override correctness hoặc policy authority. AI chỉ được phân tích và đề xuất; policy thay đổi có thể yêu cầu approval. Toàn bộ governance layer phải optional, không tạo hidden global scheduler hoặc runtime overhead cho ứng dụng Axiom thông thường.**

**BOOTSTRAP-550 hoàn tất / LOCKED.**

---

### Tiếp theo

**BOOTSTRAP-551 — AI RESOURCE AUTOSCALING, ELASTIC COMPUTE, HORIZONTAL/VERTICAL SCALING, GPU/NPU POOLING, PREDICTIVE CAPACITY & SCALE-TO-ZERO**