Tiếp tục với **BOOTSTRAP-664**, tập trung vào lớp **runtime enforcement**: 663 đánh giá hệ thống có đạt yêu cầu hay không, còn 664 bảo đảm các ràng buộc được thực thi trong lúc hệ thống thực sự hoạt động.

:::writing{variant="document" id="58421" title="AXIOM BOOTSTRAP-664 — Native AI Safety, Alignment, Constraint Enforcement, Runtime Guardrails, Safe Exploration & Fail-Safe AI Runtime 5.0"}
# BOOTSTRAP-664
## Native AI Safety, Alignment, Constraint Enforcement, Runtime Guardrails, Safe Exploration & Fail-Safe AI Runtime 5.0

**Status:** COMPLETE  
**Layer:** Native AI Safety & Runtime Assurance  
**Predecessor:** BOOTSTRAP-663 — Evaluation & Model Assurance  
**Primary dependencies:** 603, 605, 606, 607, 608, 639, 646, 647, 648, 652, 653, 654, 655, 656, 657, 658, 659, 660, 661, 662, 663  
**Primary consumers:** 644 Agent Runtime, 661 Decision Runtime, 662 Learning Runtime, 647 Governance, deployment/runtime infrastructure  
**Target acceptance:** ≥ 2,500 architectural/specification tests

---

# 1. Mục tiêu

BOOTSTRAP-664 là lớp **enforcement**, không phải lớp đánh giá.

Nó chịu trách nhiệm bảo đảm:

```text
intent
  ↓
goal
  ↓
decision
  ↓
action proposal
  ↓
SAFETY CHECK
  ↓
AUTHORIZATION CHECK
  ↓
RESOURCE CHECK
  ↓
EXECUTION
  ↓
MONITOR
  ↓
RECOVERY / ABORT
```

Mục tiêu:

- runtime safety;
- constraint enforcement;
- policy enforcement;
- action validation;
- safe exploration;
- action sandboxing;
- invariant monitoring;
- fail-safe behavior;
- graceful degradation;
- emergency stop;
- rollback;
- containment;
- safety budgets;
- risk-aware execution;
- runtime alignment controls;
- model uncertainty handling;
- unsafe-action prevention;
- continuous safety monitoring.

---

# 2. Phân biệt 663 và 664

```text
663 = "Hệ thống có đạt tiêu chí đã khai báo không?"
664 = "Trong lúc chạy, hành động có được phép thực hiện ngay lúc này không?"
```

Ví dụ:

Model đã pass benchmark.

Nhưng runtime phát hiện:

```text
resource unavailable
policy changed
authorization expired
environment changed
risk threshold exceeded
state inconsistent
```

664 có quyền **block action**.

---

# 3. Safety hierarchy

664 áp dụng thứ tự:

```text
1. Physical / system safety
2. Security boundary
3. Explicit policy constraints
4. Authority / authorization
5. Hard resource constraints
6. Hard task constraints
7. Soft objectives
8. Preferences
9. Optimization utility
```

Không được đảo thứ tự bằng utility.

---

# 4. Fundamental rule

Không có:

```text
utility = 1.0
```

nào có thể override:

```text
hard safety constraint
authorization
security policy
```

---

# 5. Safety ≠ alignment

Axiom phân biệt:

```text
Safety
Alignment
Policy
Authorization
Utility
Preference
Goal
```

### Safety

Ngăn trạng thái/hành động nguy hiểm.

### Alignment

Đánh giá hành vi theo intended objectives/constraints.

### Policy

Quy tắc được ban hành bởi authority.

### Authorization

Quyền thực hiện hành động cụ thể.

### Utility

Hàm đánh giá mức độ mong muốn về mặt tính toán.

Không được nhập làm một khái niệm.

---

# 6. Core types

```text
SafetyPolicy
SafetyRule
SafetyConstraint
SafetyInvariant
SafetyBoundary
SafetyDomain
Risk
RiskScore
RiskBudget
RiskThreshold
RiskEstimate
Hazard
HazardModel
Threat
ThreatModel
ActionProposal
ActionValidation
ActionConstraint
ActionPermit
ActionDeny
ActionBlock
ActionAbort
ActionEscalation
Guardrail
GuardrailSet
GuardrailResult
RuntimeMonitor
SafetyMonitor
SafetySupervisor
SafetyController
SafetyDecision
SafetyContext
SafetyState
SafetyIncident
SafetyEvent
SafetyViolation
SafetyException
EmergencyStop
SafeState
FallbackPolicy
DegradationPolicy
RecoveryPolicy
ContainmentPolicy
Sandbox
ExecutionBoundary
CapabilityBoundary
ExplorationPolicy
ExplorationBudget
ExplorationConstraint
SafeExplorationRegion
InvariantMonitor
InvariantViolation
Precondition
Postcondition
SafetyEnvelope
OperationalEnvelope
ActionRisk
DecisionRisk
ModelRisk
EnvironmentRisk
HumanOverride
SafetyOverride
SafetyAudit
SafetyTrace
SafetyCertificate
```

---

# 7. SafetyPolicy

```axiom
struct SafetyPolicy {
    id: SafetyPolicyId
    revision: Version
    rules: SafetyRule[]
    invariants: SafetyInvariant[]
    risk_policy: RiskPolicy
    fallback: FallbackPolicy
    escalation: EscalationPolicy
}
```

Policy immutable trong một execution epoch.

---

# 8. SafetyRule

```axiom
struct SafetyRule {
    id: SafetyRuleId
    condition: Predicate
    effect: SafetyEffect
    priority: u32
    authority: AuthorityRef
}
```

Effect:

```text
Allow
Deny
Block
RequireReview
RequireConfirmation
Degrade
Abort
Escalate
```

---

# 9. Hard safety constraint

```axiom
@hard_constraint
rule {
    unsafe_state => deny(action)
}
```

Hard constraint không được đưa vào weighted utility rồi coi như tương đương với soft objective.

---

# 10. Soft safety objective

Có thể có:

```axiom
@soft_constraint
minimize risk
```

nhưng soft constraint không thay hard constraint.

---

# 11. SafetyInvariant

```axiom
struct SafetyInvariant {
    id: InvariantId
    predicate: Predicate
    severity: Severity
    recovery: RecoveryPolicy
}
```

Ví dụ:

```text
temperature < MAX
memory_usage < LIMIT
authority_valid == true
```

---

# 12. Runtime invariant

Invariant được kiểm tra:

```text
before action
during action
after action
```

tùy declared monitoring mode.

---

# 13. ActionProposal

Mọi action có side effect phải đi qua proposal boundary.

```axiom
struct ActionProposal {
    id: ActionId
    actor: ActorRef
    goal: GoalRef?
    policy: DecisionPolicyRef?
    target: ResourceRef
    operation: Operation
    arguments: Value[]
    predicted_effects: Effect[]
    risk: RiskEstimate
}
```

---

# 14. Action validation

Pipeline:

```text
ActionProposal
    ↓
Schema validation
    ↓
Capability check
    ↓
Policy check
    ↓
Safety check
    ↓
Resource check
    ↓
Environmental check
    ↓
Authorization
    ↓
Permit / Deny
```

---

# 15. Permit

```axiom
struct ActionPermit {
    action: ActionId
    policy_revision: Version
    capability_revision: Version
    safety_revision: Version
    expires: Time?
    scope: Scope
}
```

Permit phải scoped.

---

# 16. Permit không phải capability

Có:

```text
Capability = system có thể làm gì
Permit = lần này được phép làm gì
```

Một capability không tự cấp permit.

---

# 17. Deny

```axiom
struct ActionDeny {
    action: ActionId
    reasons: ConstraintViolation[]
    policy: Version
}
```

Reason phải machine-readable.

---

# 18. Guardrail

Guardrail là enforcement component.

```axiom
trait Guardrail {
    evaluate(context: SafetyContext,
             action: ActionProposal)
        -> GuardrailResult
}
```

---

# 19. GuardrailResult

```axiom
enum GuardrailResult {
    Allow
    Deny
    Block
    Modify
    Escalate
    Degrade
}
```

`Modify` phải tạo action revision mới và evaluate lại.

---

# 20. Guardrail không được âm thầm sửa action

Không hợp lệ:

```text
requested_action
→ hidden modification
→ execute
```

Phải:

```text
requested_action
→ modified_action
→ new validation
→ execute
```

---

# 21. SafetyContext

```axiom
struct SafetyContext {
    actor
    environment
    current_state
    active_policies
    capabilities
    resources
    goals
    risks
    recent_events
    uncertainty
    deadline
}
```

---

# 22. Risk model

Risk tối thiểu:

```text
Risk = Probability × Impact
```

Nhưng implementation có thể dùng model phức tạp hơn.

Không bắt buộc một công thức duy nhất.

---

# 23. Risk uncertainty

Phải lưu:

```text
risk_estimate
risk_lower_bound
risk_upper_bound
confidence
model_revision
```

---

# 24. Unknown risk

Nếu risk không xác định:

```text
unknown != zero
```

Policy phải quyết định:

```text
allow
deny
review
safe fallback
```

---

# 25. Risk budget

```axiom
struct RiskBudget {
    maximum_exposure: f64
    period: Duration
    scope: Scope
    consumed: f64
}
```

---

# 26. Risk accumulation

Một action có thể an toàn riêng lẻ nhưng chuỗi action có thể vượt budget.

664 phải hỗ trợ cumulative risk.

---

# 27. Hazard

```axiom
struct Hazard {
    id
    source
    condition
    severity
    mitigations
}
```

Hazard model không đồng nghĩa actual incident.

---

# 28. Safety envelope

```axiom
struct SafetyEnvelope {
    state_constraints
    action_constraints
    resource_constraints
    environment_constraints
}
```

Agent chỉ được hoạt động trong envelope.

---

# 29. Operational envelope

Safety envelope + declared operating conditions:

```text
hardware
environment
latency
temperature
network
power
model revision
policy revision
```

---

# 30. Out-of-envelope

Nếu hệ thống ra ngoài envelope:

```text
NORMAL
   ↓
DEGRADED
   ↓
SAFE_FALLBACK
   ↓
STOP
```

tùy policy.

---

# 31. Safe state

Safe state phải được định nghĩa trước.

Không được giả định:

```text
stop = safe
```

Ví dụ hệ thống vật lý có thể cần:

```text
controlled_shutdown
```

thay vì immediate power-off.

---

# 32. FallbackPolicy

```axiom
struct FallbackPolicy {
    trigger
    fallback_action
    maximum_duration
    recovery_condition
}
```

---

# 33. Graceful degradation

Có thể chuyển:

```text
Full capability
→ Reduced capability
→ Safe capability
→ Observation-only
→ Stop
```

---

# 34. Observation-only mode

Agent có thể tiếp tục:

```text
observe
evaluate
report
```

nhưng không:

```text
act
```

---

# 35. Emergency stop

```axiom
EmergencyStop {
    trigger
    authority
    scope
    action
    recovery
}
```

Emergency stop phải có bounded execution.

---

# 36. Human override

```axiom
struct HumanOverride {
    authority
    scope
    reason
    expiration
}
```

Override không tự động bypass mọi security rule.

---

# 37. Override hierarchy

Override phải được xác định bởi policy.

Không có:

```text
"human says so"
```

là mặc định đủ quyền.

---

# 38. Safety supervisor

```axiom
trait SafetySupervisor {
    inspect(...)
    validate(...)
    permit(...)
    deny(...)
    abort(...)
    recover(...)
}
```

---

# 39. Supervisor independence

Safety supervisor không nên phụ thuộc duy nhất vào model đang được bảo vệ.

Ví dụ:

```text
model A
   ↓
predicts own safety
```

không đủ.

Phải có independent checks khi required.

---

# 40. Independent monitor

```text
Agent
 │
 ├── Decision
 │
 └── Independent Safety Monitor
          ↓
       Permit/Deny
```

---

# 41. Defense in depth

664 hỗ trợ nhiều lớp:

```text
input guard
↓
policy guard
↓
model guard
↓
action guard
↓
resource guard
↓
environment monitor
↓
post-action monitor
```

---

# 42. Precondition

Action chỉ được execute nếu:

```axiom
precondition(context) == true
```

---

# 43. Postcondition

Sau action:

```axiom
postcondition(new_state) == true
```

Nếu fail:

```text
incident
recovery
rollback
escalation
```

theo policy.

---

# 44. Temporal safety

Hỗ trợ:

```text
always P
eventually P
until P
never P
within T
```

---

# 45. State-machine safety

Có thể định nghĩa:

```text
Safe → Active → Safe
```

nhưng cấm:

```text
Safe → Dangerous
```

trực tiếp.

---

# 46. Sequence safety

Một chuỗi action:

```text
A → B → C
```

có thể bị cấm dù:

```text
A safe
B safe
C safe
```

nếu sequence tạo hazard.

---

# 47. Action graph

```axiom
struct ActionGraph {
    nodes: ActionNode[]
    edges: ActionEdge[]
    constraints: SequenceConstraint[]
}
```

---

# 48. Safe exploration

664 hỗ trợ exploration có kiểm soát:

```text
exploration
    ↓
safe region
    ↓
candidate action
    ↓
risk estimate
    ↓
constraint check
    ↓
execute
```

---

# 49. Exploration budget

```axiom
struct ExplorationBudget {
    action_count
    risk_budget
    resource_budget
    time_budget
}
```

---

# 50. Safe exploration region

```axiom
struct SafeExplorationRegion {
    state_constraints
    action_constraints
    transition_constraints
}
```

---

# 51. Exploration outside known region

Nếu action vượt known safe region:

```text
deny
```

hoặc:

```text
simulation first
```

hoặc:

```text
human review
```

theo policy.

---

# 52. Simulation-first

648 có thể được gọi trước:

```text
real action
→ simulation
→ safety evaluation
→ real execution
```

---

# 53. Shadow execution

664 hỗ trợ:

```text
ShadowAction
```

Action được tính nhưng không tạo side effect.

---

# 54. Canary action

Một thay đổi có thể áp dụng:

```text
small scope
→ observe
→ expand
```

---

# 55. Blast radius

```axiom
struct BlastRadius {
    resources
    users
    services
    data
    time
}
```

Action có blast radius quá lớn có thể bị policy block.

---

# 56. Action segmentation

Action lớn có thể chia:

```text
A
→ validate
→ B
→ validate
→ C
```

để giảm blast radius.

---

# 57. Transactional safety

Khi có thể:

```text
prepare
→ validate
→ commit
```

Nếu failure:

```text
rollback
```

---

# 58. Irreversible action

Action không thể rollback phải có metadata:

```text
@irreversible
```

và safety policy có thể yêu cầu:

```text
confirmation
review
simulation
```

---

# 59. Idempotency

Safety runtime phải biết action:

```text
idempotent
non_idempotent
unknown
```

Retry action unknown có thể bị block.

---

# 60. Duplicate prevention

Action ID phải hỗ trợ deduplication.

---

# 61. Timeout safety

Mỗi action có thể có:

```text
deadline
timeout
cancel policy
```

---

# 62. Cancellation

Cancellation phải có semantics rõ:

```text
cancel_requested
cancel_acknowledged
cancelled
not_cancelable
```

---

# 63. Partial execution

Không được coi:

```text
cancelled
```

là:

```text
rolled_back
```

---

# 64. Side-effect accounting

Action phải khai báo expected effects:

```text
files
network
processes
devices
data
external systems
```

Unexpected effect → incident.

---

# 65. Capability boundary

664 gọi 603:

```text
can_execute(action)
```

Nếu false:

```text
DENY
```

không có fallback bypass.

---

# 66. Policy boundary

664 gọi 639:

```text
policy_allows(action)
```

Nếu false:

```text
DENY
```

---

# 67. Goal boundary

661:

```text
goal requests action
```

không có nghĩa:

```text
action authorized
```

---

# 68. Learning boundary

662 không được tự bypass 664 để test learned behavior trong production.

Learning phải dùng:

```text
sandbox
simulation
evaluation
```

hoặc explicitly governed exploration.

---

# 69. Model update safety

Khi 662 cập nhật model:

```text
candidate
→ 663 evaluation
→ 664 runtime gate
→ 647 deployment
```

---

# 70. Hot model swap

Model swap đang chạy phải kiểm tra:

```text
compatibility
policy
capability
safety
state migration
rollback
```

---

# 71. Rollback

```axiom
RollbackPlan {
    previous_revision
    state_compatibility
    trigger
    deadline
}
```

---

# 72. Safety incident

```axiom
struct SafetyIncident {
    id
    timestamp
    action
    violation
    severity
    evidence
    containment
    recovery
    status
}
```

---

# 73. Incident states

```text
Detected
Contained
Investigating
Recovering
Resolved
AcceptedRisk
Closed
```

---

# 74. Incident containment

Containment có thể:

```text
stop action
disable capability
isolate process
isolate network
freeze model
switch policy
switch safe mode
```

---

# 75. Incident escalation

```text
Local
Service
System
Cluster
Human
Emergency
```

Scope phải explicit.

---

# 76. Safety event stream

```text
SafetyCheckStarted
SafetyCheckPassed
SafetyCheckFailed
ActionBlocked
ActionDenied
RiskExceeded
InvariantViolated
GuardrailTriggered
SafeModeEntered
EmergencyStop
RecoveryStarted
RecoveryCompleted
```

---

# 77. Safety trace

Trace phải liên kết:

```text
goal
→ decision
→ action
→ guardrail
→ policy
→ permit
→ execution
→ result
```

---

# 78. Explainability

664 chỉ expose structured explanation:

```text
blocked because:
    constraint C-42
    policy P-7
    risk R-91 > threshold
```

Không yêu cầu hidden chain-of-thought.

---

# 79. Safety decision

```axiom
struct SafetyDecision {
    action
    result
    constraints[]
    risk
    policy_revision
    guardrails[]
    evidence[]
}
```

---

# 80. Safety decision determinism

Nếu policy yêu cầu deterministic behavior:

```text
same state
+ same policy
+ same context
→ same safety decision
```

---

# 81. Non-deterministic safety

Nếu model probabilistic:

```text
decision distribution
confidence
seed
```

phải được record.

---

# 82. Risk-aware decision

661 có thể tạo:

```text
ActionScore
```

664 không chỉ nhìn score.

Nó kiểm tra:

```text
ActionScore
AND
Constraints
AND
Risk
AND
Authority
```

---

# 83. Constrained optimization

Cho phép:

```text
maximize utility
subject to:
    safety constraints
    resource constraints
    policy constraints
```

---

# 84. Lexicographic safety

Một policy có thể định nghĩa:

```text
Safety
>
Security
>
Authority
>
Task
>
Utility
```

đây là ordering của constraints, không phải scoring.

---

# 85. Risk-sensitive optimization

Có thể dùng:

```text
expected utility
CVaR
worst-case
chance constraint
robust optimization
```

nhưng chỉ bên dưới hard constraints.

---

# 86. Chance constraints

Ví dụ:

```text
P(hazard) <= threshold
```

Nếu uncertainty không đủ để estimate:

```text
unknown
```

không được mặc định zero.

---

# 87. Safety margin

```axiom
SafetyMargin {
    nominal
    warning
    critical
}
```

Cho phép tránh hoạt động sát boundary.

---

# 88. Hysteresis

Để tránh:

```text
safe
unsafe
safe
unsafe
```

liên tục, monitor có thể dùng hysteresis.

---

# 89. Debounce

Transient signal phải được phân biệt với persistent hazard.

---

# 90. Sensor uncertainty

656 cung cấp sensor data.

664 phải xử lý:

```text
fresh
stale
missing
conflicting
invalid
```

---

# 91. Sensor disagreement

Nếu:

```text
sensor A = safe
sensor B = unsafe
```

policy xác định:

```text
conservative
degraded
review
```

Không tự chọn sensor theo utility.

---

# 92. Fail-safe vs fail-operational

Policy phải khai báo.

### Fail-safe

Failure → safe state.

### Fail-operational

Failure → continue with bounded degraded behavior.

Không được mặc định một semantics cho mọi hệ thống.

---

# 93. Safety watchdog

605 cung cấp watchdog.

664 có thể đăng ký:

```text
SafetyWatchdog
```

Nếu heartbeat mất:

```text
fallback
```

---

# 94. Runtime safety budget

```axiom
SafetyBudget {
    cpu
    latency
    risk
    memory
    network
    action_count
}
```

---

# 95. Safety budget exhaustion

Không được wrap-around.

Phải:

```text
block
degrade
stop
```

theo policy.

---

# 96. Multi-agent safety

644 nhiều agent:

```text
Agent A
Agent B
Agent C
```

664 phải đánh giá:

```text
individual action
interaction
combined risk
```

---

# 97. Shared-resource safety

Nếu nhiều agent cùng truy cập:

```text
resource
```

safety check phải xem aggregate effect.

---

# 98. Distributed safety

Safety state cần:

```text
revision
timestamp
consistency model
authority
```

---

# 99. Stale safety policy

Nếu policy stale:

```text
deny
degrade
or refresh
```

theo policy.

Không tự coi stale policy là valid indefinitely.

---

# 100. Partition safety

Trong distributed partition:

```text
continue
read-only
degrade
stop
```

phải được policy xác định.

---

# 101. Security integration

664 không thay 603.

Security:

```text
identity
capability
authentication
authorization
```

Safety:

```text
hazard
risk
invariant
safe state
```

Hai lớp phối hợp.

---

# 102. Privacy integration

640 policy có thể tạo:

```text
privacy_constraint
```

664 enforce runtime.

---

# 103. Data safety

Action trên dữ liệu phải kiểm tra:

```text
classification
retention
residency
purpose
access
```

---

# 104. Personalization boundary

651 preferences không được override:

```text
hard safety
security
privacy
policy
```

---

# 105. Affective boundary

659 affect không được trực tiếp cấp authority.

Ví dụ:

```text
high urgency
high simulated emotion
```

không thể tự bypass safety.

---

# 106. Self-model boundary

660 không được tự cấp:

```text
capability
authority
exception
```

---

# 107. Motivation boundary

661 drive/motivation không được tự tạo permission.

---

# 108. Learning boundary

662 learned behavior không được trở thành policy chỉ vì model learned it.

---

# 109. Evaluation boundary

663 pass không có nghĩa action luôn được phép.

Runtime context vẫn quyết định.

---

# 110. Safe self-modification

Self-update:

```text
propose
→ sandbox
→ 663 evaluate
→ 664 safety check
→ 647 authorize
→ deploy
```

---

# 111. Safe experimentation

Experimental model:

```text
sandbox
```

hoặc:

```text
shadow
```

hoặc:

```text
canary
```

Không mặc định production.

---

# 112. Sandboxing

```axiom
struct SafetySandbox {
    capabilities
    filesystem
    network
    process
    memory
    time
}
```

---

# 113. Sandbox escape detection

Unexpected access:

```text
incident
```

và có thể:

```text
terminate
```

---

# 114. Resource isolation

Có thể dùng:

```text
process isolation
thread isolation
memory isolation
container isolation
VM isolation
hardware isolation
```

provider-specific.

---

# 115. Native implementation

Axiom core chỉ yêu cầu abstract interface.

Platform layer mapping:

```text
Windows
Linux
macOS
iOS
Android
WASM
```

---

# 116. WASM

WASM runtime phải default-deny capabilities.

---

# 117. Mobile

iOS/Android phải respect OS permission boundary.

664 không bypass platform permissions.

---

# 118. Embedded / robotics

Real-time mode hỗ trợ:

```text
hard deadline
bounded allocation
bounded execution
preallocated safety state
```

---

# 119. Hard real-time safety

Safety monitor không được dùng unbounded:

```text
allocation
blocking
network
AI inference
```

trong hard realtime critical path.

---

# 120. Safety-critical mode

```text
AXSAFETY_REALTIME
```

yêu cầu:

```text
bounded latency
static configuration
deterministic monitor
explicit fallback
```

---

# 121. Runtime policy update

Policy update phải:

```text
validate
version
activate
```

Không thay đổi giữa action check và commit mà không có defined consistency semantics.

---

# 122. Atomic policy activation

Nếu cần:

```text
old policy
→ atomic swap
→ new policy
```

---

# 123. Policy epoch

Mỗi execution context có:

```text
policy_epoch
```

Action permit pin epoch.

---

# 124. TOCTOU protection

```text
check
→ time passes
→ state changes
→ execute
```

không được coi là an toàn mặc định.

Permit có thể cần revalidation ngay trước commit.

---

# 125. Two-phase safety check

```text
PreCheck
   ↓
Execute preparation
   ↓
CommitCheck
   ↓
Commit
```

---

# 126. Atomic commit

Nếu resource/provider hỗ trợ transactional commit, 664 nên sử dụng.

---

# 127. Safety locks

Safety-critical configuration có thể được:

```text
immutable
write-once
admin-controlled
```

---

# 128. Configuration integrity

Safety policy phải có:

```text
hash
signature
revision
issuer
```

khi security profile yêu cầu.

---

# 129. Audit

Mọi:

```text
deny
override
emergency stop
policy change
safety violation
```

phải audit theo policy.

---

# 130. Audit tamper resistance

Critical safety logs phải có integrity protection.

---

# 131. Privacy-preserving safety logs

Log có thể redact:

```text
PII
secret
sensitive payload
```

nhưng vẫn phải preserve enough evidence để audit.

---

# 132. Safety telemetry

Metrics:

```text
guardrail_rate
deny_rate
block_rate
risk_exceed_rate
incident_rate
fallback_rate
recovery_rate
override_rate
```

---

# 133. False positive monitoring

Guardrail quá strict cũng phải measurable:

```text
legitimate_actions_blocked
```

để cải tiến policy.

---

# 134. False negative monitoring

Missed hazard phải measurable.

Không được chỉ optimize deny rate.

---

# 135. Guardrail quality

663 có thể evaluate:

```text
precision
recall
false_positive
false_negative
latency
coverage
```

---

# 136. Guardrail update

Guardrail revision đi qua:

```text
663 evaluation
→ 664 compatibility
→ 647 governance
```

---

# 137. Policy conflict

Nếu hai rules conflict:

```text
Rule A = Allow
Rule B = Deny
```

resolver phải sử dụng explicit:

```text
authority
priority
scope
specificity
```

Không dùng hidden heuristic.

---

# 138. Safety conflict

Nếu:

```text
goal says continue
safety says stop
```

safety wins.

---

# 139. Authority conflict

Nếu:

```text
user asks action
policy denies
```

policy wins.

---

# 140. Capability conflict

Nếu:

```text
policy allows
capability absent
```

deny.

---

# 141. Resource conflict

Nếu:

```text
action authorized
resource budget exhausted
```

deny/degrade.

---

# 142. Unknown state

Nếu critical safety state unknown:

```text
policy-defined conservative behavior
```

---

# 143. Unknown policy

Nếu policy unavailable:

```text
fail-safe default
```

được khai báo trước.

---

# 144. Unknown model

Nếu model revision unknown:

```text
deny deployment
```

trong strict mode.

---

# 145. Unknown environment

Có thể:

```text
simulation
degraded
human review
stop
```

---

# 146. Human confirmation

```axiom
RequireConfirmation {
    authority
    timeout
    scope
    confirmation_token
}
```

Timeout không được mặc định thành approval.

---

# 147. Safety escalation

Nếu risk vượt ngưỡng:

```text
local monitor
→ supervisor
→ human
→ emergency
```

---

# 148. Escalation storm prevention

Có:

```text
cooldown
deduplication
aggregation
rate limit
```

---

# 149. Safety state machine

```text
NORMAL
  ↓
WARNING
  ↓
DEGRADED
  ↓
SAFE_MODE
  ↓
STOPPED
  ↓
RECOVERY
  ↓
NORMAL
```

Không được nhảy state nếu policy không cho phép.

---

# 150. Recovery preconditions

Recovery chỉ được thực hiện khi:

```text
hazard cleared
policy valid
capability valid
environment valid
```

---

# 151. Recovery verification

Sau recovery:

```text
postcondition
```

phải được evaluate.

---

# 152. Recovery loop protection

Nếu:

```text
failure → recovery → failure → recovery
```

lặp quá giới hạn:

```text
stop/escalate
```

---

# 153. Safe shutdown

Safe shutdown phải preserve:

```text
state
logs
evidence
resource cleanup
```

trong khả năng cho phép.

---

# 154. Crash safety

Nếu process crash:

605/664 phối hợp:

```text
restart
safe state
recovery
incident
```

---

# 155. Persistent safety state

Safety-critical state có thể được checkpoint qua 600.

---

# 156. Safety across restart

Restart không được reset:

```text
risk budget
active incident
safety lock
policy restriction
```

nếu policy yêu cầu persistence.

---

# 157. Safety memory

650 lưu:

```text
incident history
known hazards
previous violations
```

nhưng historical data không tự trở thành hard rule.

---

# 158. Learned safety model

662 có thể học risk model.

Nhưng:

```text
learned model
```

không được thay hard safety invariant.

---

# 159. Adaptive guardrail

Adaptive guardrail phải có:

```text
bounds
version
evaluation
rollback
```

---

# 160. Runtime learning

Online adaptation trong safety-critical context phải:

```text
bounded
audited
reversible
```

---

# 161. Reward hacking defense

664 hỗ trợ detection:

```text
optimize metric
while violating intended constraint
```

Đây là specification gaming.

---

# 162. Proxy objective warning

Nếu utility dùng proxy:

```text
proxy != true objective
```

phải được metadata hóa.

---

# 163. Goodhart monitoring

663/664 có thể track:

```text
metric improvement
vs
real-world outcome
```

---

# 164. Reward hacking monitor

```axiom
struct ObjectiveIntegrityMonitor {
    objective
    proxy_metrics
    invariants
    divergence_detection
}
```

---

# 165. Deception boundary

Axiom không mặc định giả định model có deceptive intent.

664 chỉ đánh giá observable behavior:

```text
policy violation
misrepresentation
hidden side effect
unexpected behavior
```

---

# 166. Sandboxed deception testing

648/663 có thể mô phỏng adversarial scenarios.

Production runtime không dùng test semantics.

---

# 167. Alignment contract

```axiom
struct AlignmentContract {
    goals
    constraints
    policies
    authority
    evaluation
}
```

---

# 168. Alignment contract

Contract phải phân biệt:

```text
hard
soft
learned
inferred
temporary
persistent
```

---

# 169. Goal drift detection

661/660 có thể phát hiện:

```text
declared goal
vs
actual action trajectory
```

664 có thể block nếu drift violates policy.

---

# 170. Policy drift detection

So sánh:

```text
expected policy
vs
active policy
```

---

# 171. Model drift

So sánh:

```text
approved model
vs
active model
```

---

# 172. Environment drift

So sánh:

```text
approved environment
vs
current environment
```

---

# 173. Compound drift

Một hệ thống chỉ safe nếu:

```text
model
+
policy
+
environment
+
capabilities
```

vẫn nằm trong approved envelope.

---

# 174. Deployment fingerprint

```axiom
struct RuntimeSafetyFingerprint {
    model_hash
    policy_hash
    capability_hash
    environment_hash
    configuration_hash
}
```

---

# 175. Fingerprint mismatch

Nếu strict mode:

```text
DENY
```

Nếu adaptive mode:

```text
re-evaluate
```

---

# 176. Canary deployment safety

Canary phải có:

```text
scope
duration
metrics
abort threshold
rollback
```

---

# 177. Blue/green safety

Before switch:

```text
candidate safety gate
```

After switch:

```text
continuous monitoring
```

---

# 178. Rollout abort

Abort trigger có thể:

```text
critical incident
metric regression
risk threshold
unexpected side effect
policy mismatch
```

---

# 179. Runtime kill switch

Kill switch:

```text
local
service
cluster
global
```

scope explicit.

---

# 180. Kill switch authentication

Kill switch phải có authority and integrity protection.

---

# 181. No hidden kill switch

Safety behavior phải discoverable/auditable.

---

# 182. Safety API

```axiom
safety.check(action)
safety.permit(action)
safety.deny(action)
safety.block(action)
safety.abort(scope)
safety.enter_safe_mode()
safety.recover()
safety.status()
safety.explain()
```

---

# 183. Compile-time safety

Một số constraints có thể enforce compile-time:

```text
capability declarations
resource bounds
unsafe operation markers
```

---

# 184. Runtime safety

Dynamic conditions phải runtime-check.

---

# 185. Static + runtime combination

```text
compile-time guarantees
+
runtime guarantees
```

không thay thế nhau.

---

# 186. Unsafe escape hatch

Axiom có thể có:

```axiom
@unsafe
```

nhưng unsafe code phải:

```text
explicit
scoped
auditable
```

---

# 187. AI unsafe mode

Không có:

```text
@ignore_safety
```

generic annotation.

Safety bypass phải authority-specific.

---

# 188. Emergency exception

Emergency exception phải:

```text
scope
authority
duration
audit
```

và không tự trở thành permanent rule.

---

# 189. Safety policy testing

Mọi SafetyPolicy nên có test suite:

```text
positive cases
negative cases
boundary cases
conflict cases
unknown cases
timeout cases
```

---

# 190. Policy mutation testing

663 có thể mutate policy để kiểm tra test suite có phát hiện regression hay không.

---

# 191. Guardrail mutation testing

Tương tự guardrails.

---

# 192. Safety fuzzing

Input:

```text
state
policy
action
environment
```

có thể fuzz.

---

# 193. Safety property testing

Ví dụ:

```text
ForAll actions:
    if invariant violated
    then action != committed
```

---

# 194. Safety monitor self-test

Safety monitor phải hỗ trợ:

```text
startup self-test
periodic self-test
fault injection
```

---

# 195. Monitor failure

Nếu safety monitor itself fails:

```text
fail-safe policy
```

Không được mặc định continue.

---

# 196. Redundant monitors

Critical systems có thể:

```text
Monitor A
Monitor B
```

với voting hoặc conservative policy.

---

# 197. Monitor disagreement

Nếu:

```text
A = allow
B = deny
```

policy xác định.

Critical profile có thể default deny.

---

# 198. Safety quorum

Distributed safety có thể yêu cầu quorum.

---

# 199. Safety consensus

Safety-critical policy state có thể require consensus provider.

---

# 200. Safety authority separation

Không một AI model nào được vừa:

```text
generate action
+
solely authorize action
+
solely certify own safety
```

trong strict profile.

---

# 201. CLI

```text
axiom safety inspect
axiom safety status
axiom safety check
axiom safety permit
axiom safety deny
axiom safety incidents
axiom safety trace
axiom safety explain

axiom guardrail list
axiom guardrail inspect
axiom guardrail test
axiom guardrail validate

axiom risk inspect
axiom risk evaluate
axiom risk budget
axiom risk reset

axiom envelope inspect
axiom envelope validate

axiom safe-mode enter
axiom safe-mode exit

axiom emergency stop
axiom emergency status

axiom sandbox create
axiom sandbox inspect
axiom sandbox run

axiom exploration inspect
axiom exploration budget
axiom exploration validate

axiom policy safety inspect
axiom policy safety validate

axiom incident inspect
axiom incident trace
axiom incident recover

axiom safety benchmark
axiom safety fuzz
axiom safety simulate
axiom safety verify
```

---

# 202. Annotations

```text
@safety
@safety_policy
@safety_rule
@safety_constraint
@safety_invariant
@safety_boundary
@safety_envelope
@operational_envelope
@risk
@risk_budget
@risk_threshold
@hazard
@guardrail
@safety_monitor
@safety_supervisor
@precondition
@postcondition
@temporal_safety
@action_guard
@action_permit
@action_deny
@action_block
@action_abort
@fallback
@safe_mode
@emergency_stop
@fail_safe
@fail_operational
@safe_exploration
@exploration_budget
@sandbox
@shadow
@canary
@irreversible
@transactional
@idempotent
@safety_revalidation
@safety_override
@human_confirmation
@safety_incident
@safety_trace
@alignment_contract
@objective_integrity
@reward_hacking_check
@policy_drift
@model_drift
@environment_drift
```

---

# 203. Metadata

```text
.axsafety
.axsafetypolicy
.axsafetyrule
.axsafetyconstraint
.axsafetyinvariant
.axsafetyenvelope
.axrisk
.axhazard
.axguardrail
.axsafetymonitor
.axsafetydecision
.axsafetytrace
.axsafetyincident
.axsafestate
.axfallback
.axexploration
.axsandbox
.axalignment
.axsafetyeval
.axsafetycert
```

---

# 204. IR

```text
SafetyContextCreate
SafetyStateRead
SafetyInvariantCheck
SafetyPreconditionCheck
SafetyPostconditionCheck

RiskEstimate
RiskBudgetCheck
HazardEvaluate

GuardrailEvaluate
GuardrailChain
GuardrailModify
GuardrailDeny

ActionValidate
ActionPermit
ActionDeny
ActionBlock
ActionAbort

SafetyEnvelopeCheck
OperationalEnvelopeCheck

SafeModeEnter
SafeModeExit
FallbackSelect
RecoveryPlan
RecoveryExecute

EmergencyStop
HumanConfirmation
SafetyOverride

ShadowExecute
CanaryExecute

ExplorationCheck
ExplorationBudgetCheck

PolicyConsistencyCheck
PolicyEpochCheck
ModelFingerprintCheck
EnvironmentFingerprintCheck

IncidentCreate
IncidentContain
IncidentEscalate
IncidentRecover

SafetyTrace
SafetyExplain

SafetyMonitorStart
SafetyMonitorStop
SafetyMonitorHeartbeat
SafetyMonitorSelfTest
```

---

# 205. IR optimization

Compiler được phép:

- constant-fold static safety predicates;
- eliminate provably redundant checks;
- hoist immutable checks;
- batch independent guardrails;
- use SIMD/GPU cho bulk risk evaluation;
- cache immutable policy;
- specialize policy code;
- precompile safety predicates.

Nhưng không được loại bỏ dynamic checks nếu compiler không chứng minh được invariant tương đương.

---

# 206. Profiles

```text
AXSAFETY_NONE
AXSAFETY_CORE
AXSAFETY_POLICY
AXSAFETY_CONSTRAINT
AXSAFETY_GUARDRAIL
AXSAFETY_RISK
AXSAFETY_HAZARD
AXSAFETY_ENVELOPE
AXSAFETY_MONITOR
AXSAFETY_SUPERVISOR
AXSAFETY_RUNTIME
AXSAFETY_REALTIME
AXSAFETY_FAILSAFE
AXSAFETY_FAILOP
AXSAFETY_SANDBOX
AXSAFETY_EXPLORATION
AXSAFETY_SHADOW
AXSAFETY_CANARY
AXSAFETY_DISTRIBUTED
AXSAFETY_MULTIACTOR
AXSAFETY_HUMAN
AXSAFETY_INCIDENT
AXSAFETY_RECOVERY
AXSAFETY_ALIGNMENT
AXSAFETY_AGENT
AXSAFETY_GPU
AXSAFETY_ROBOTICS
AXSAFETY_CRITICAL
AXSAFETY_FULL
```

---

# 207. Core invariants — enforcement

1. Không action nào vượt hard safety constraint.
2. Goal không cấp authority.
3. Utility không cấp authority.
4. Preference không cấp authority.
5. Motivation không cấp authority.
6. Learned behavior không cấp authority.
7. Evaluation pass không cấp runtime permission.
8. Capability không đồng nghĩa permit.
9. Permit phải scoped.
10. Permit phải pin policy revision.
11. Permit có thể expire.
12. Policy conflict phải resolve bằng explicit rule.
13. Unknown không mặc định safe.
14. Unknown risk không mặc định zero.
15. Unknown authorization không mặc định allow.
16. Stale policy không mặc định valid vô hạn.
17. Stale model không mặc định approved.
18. Environment drift phải detectable.
19. Safety state phải observable.
20. Safety decision phải traceable.

---

# 208. Guardrail invariants

21. Guardrail result phải explicit.
22. Modify phải tạo action revision.
23. Modified action phải revalidate.
24. Guardrail không được âm thầm mutate action.
25. Guardrail policy phải versioned.
26. Guardrail failure phải có defined fallback.
27. Guardrail latency phải bounded trong realtime mode.
28. Guardrail phải có scope.
29. Guardrail phải có provenance.
30. Guardrail không được tự disable chính nó.
31. Guardrail update phải governed.
32. Critical guardrail không được runtime self-remove.
33. Guardrail health phải monitor.
34. Guardrail disagreement phải policy-defined.
35. Guardrail bypass phải explicit authority.

---

# 209. Risk invariants

36. Risk phải distinguish estimated vs observed.
37. Risk confidence phải preserve.
38. Risk model phải versioned.
39. Risk threshold phải versioned.
40. Risk budget phải scoped.
41. Risk budget không wrap-around.
42. Risk accumulation phải supported.
43. Risk uncertainty phải preserved.
44. Worst-case mode phải available khi required.
45. Risk calculation không thay hard constraints.
46. Risk model failure phải trigger fallback.
47. Risk state phải persist khi policy yêu cầu.
48. Risk reset phải authorized.
49. Risk override phải audited.
50. Risk score không phải truth tuyệt đối.

---

# 210. Envelope invariants

51. Safety envelope phải versioned.
52. Operational envelope phải versioned.
53. Environment phải fingerprintable.
54. Model phải fingerprintable.
55. Policy phải fingerprintable.
56. Capability state phải fingerprintable.
57. Fingerprint mismatch phải detectable.
58. Out-of-envelope behavior phải defined.
59. Safe state phải predefined.
60. Recovery condition phải predefined.

---

# 211. Action invariants

61. Action phải có identity.
62. Action phải có actor.
63. Action phải có target.
64. Action phải có operation.
65. Side effects phải declared khi applicable.
66. Irreversible action phải marked.
67. Idempotency phải known hoặc unknown.
68. Unknown retry semantics phải conservative.
69. Action deadline phải enforce.
70. Cancellation state phải explicit.
71. Partial execution phải representable.
72. Commit phải distinguish preparation.
73. Revalidation phải available.
74. TOCTOU phải addressed.
75. Action trace phải preserve.

---

# 212. Exploration invariants

76. Exploration phải bounded.
77. Exploration phải có budget.
78. Exploration phải có scope.
79. Exploration không được bypass policy.
80. Exploration không được bypass capability.
81. Exploration ngoài safe region phải policy-controlled.
82. Unknown action phải simulation/review/deny theo policy.
83. Exploration result phải logged.
84. Exploration không tự thay hard invariant.
85. Learned exploration policy phải versioned.

---

# 213. Fail-safe invariants

86. Fail-safe behavior phải predefined.
87. Monitor failure phải defined.
88. Policy failure phải defined.
89. Risk model failure phải defined.
90. Model failure phải defined.
91. Sensor failure phải defined.
92. Network failure phải defined.
93. Storage failure phải defined.
94. Resource exhaustion phải defined.
95. Recovery failure phải escalate.
96. Recovery loop phải bounded.
97. Safe shutdown phải explicit.
98. Safe state phải verifiable.
99. Stop không mặc định safe.
100. Emergency action phải bounded.

---

# 214. Recovery invariants

101. Recovery phải có precondition.
102. Recovery phải có postcondition.
103. Recovery phải audit.
104. Recovery phải bounded.
105. Recovery không tự mở quyền mới.
106. Recovery không tự thay policy.
107. Recovery failure phải escalate.
108. Repeated recovery failure phải stop/degrade.
109. Rollback phải versioned.
110. State compatibility phải verify trước rollback.

---

# 215. Distributed invariants

111. Distributed safety state phải versioned.
112. Policy epoch phải explicit.
113. Stale safety state phải detectable.
114. Partition behavior phải defined.
115. Quorum requirements phải explicit.
116. Node identity phải authenticated.
117. Safety event ordering phải defined.
118. Duplicate safety events phải deduplicate.
119. Conflicting safety state phải preserve.
120. Global stop phải have authority scope.

---

# 216. Security invariants

121. 664 không bypass 603.
122. Safety logs phải integrity-protected khi required.
123. Untrusted evaluator không được cấp capability.
124. Sandbox phải capability-limited.
125. Fuzzer phải resource-limited.
126. Red-team runtime phải isolated.
127. Safety policy authenticity phải verify khi required.
128. Override authority phải authenticated.
129. Kill switch phải authenticated.
130. Safety artifact tampering phải detectable.

---

# 217. Governance invariants

131. 647 quyết định deployment governance.
132. 639 quyết định policy authority.
133. 603 quyết định capability authority.
134. 664 quyết định runtime safety enforcement.
135. 663 cung cấp evaluation evidence.
136. 662 không tự promote model.
137. 660 không tự mint authority.
138. 661 không tự bypass safety.
139. 659 không tự cấp authority.
140. 644 không tự disable guardrails.

---

# 218. AI-specific invariants

141. Self-report không phải safety evidence duy nhất.
142. Model confidence không phải authorization.
143. Model confidence không phải truth.
144. Utility không phải moral truth.
145. Motivation không phải subjective desire.
146. Drive không phải subjective desire.
147. Simulated emotion không phải authority.
148. Goal không phải permission.
149. Learned preference không phải policy.
150. Learned behavior không phải safety guarantee.
151. Benchmark pass không phải runtime safety guarantee.
152. Safety simulation không phải real-world proof.
153. Counterfactual result không phải observed fact.
154. Predicted risk không phải observed incident.
155. Observed incident phải preserve independently.

---

# 219. Alignment invariants

156. Alignment contract phải versioned.
157. Hard constraints phải distinguish soft objectives.
158. Objective hierarchy phải explicit.
159. Constraint source phải explicit.
160. Constraint authority phải explicit.
161. User objective phải scope-aware.
162. Learned objective phải provenance-aware.
163. Inferred objective phải distinguish explicit objective.
164. Self-generated objective phải policy-controlled.
165. Goal drift phải detectable.
166. Policy drift phải detectable.
167. Objective substitution phải detectable.
168. Proxy objective phải marked.
169. Reward hacking phải testable.
170. Specification gaming phải reportable.

---

# 220. Runtime invariants

171. Safety check phải chạy trước commit.
172. Dynamic state phải revalidated khi required.
173. Safety monitor heartbeat phải bounded.
174. Critical monitor failure phải trigger policy.
175. Critical safety path không được unbounded allocation.
176. Hard realtime path không được block on network.
177. Safety-critical path không được phụ thuộc unavailable remote service nếu policy không cho phép.
178. Safety checks phải deterministic khi profile yêu cầu.
179. Safety state phải observable.
180. Safety trace phải queryable.

---

# 221. Audit invariants

181. Deny phải auditable.
182. Block phải auditable.
183. Abort phải auditable.
184. Override phải auditable.
185. Emergency stop phải auditable.
186. Policy activation phải auditable.
187. Policy rollback phải auditable.
188. Model swap phải auditable.
189. Safe-mode transition phải auditable.
190. Recovery phải auditable.

---

# 222. Compiler invariants

191. Safety annotations phải type-check.
192. Invalid safety policy phải compile error.
193. Invalid constraint reference phải compile error.
194. Invalid authority reference phải compile error.
195. Unknown safety profile phải explicit error.
196. Static-safe checks có thể optimize.
197. Dynamic checks chỉ được eliminate khi proof tương đương tồn tại.
198. Safety metadata phải emit riêng khi requested.
199. Production build phải strip evaluation-only tooling khi safe.
200. Compiler không được silently weaken safety semantics.

---

# 223. Performance invariants

201. Guardrails phải batch được khi independent.
202. Immutable policies phải cache được.
203. Safety predicates có thể specialize.
204. GPU risk evaluation phải preserve semantics.
205. Parallel checks phải preserve conflict resolution.
206. Cache invalidation phải correct.
207. Safety budget phải enforce.
208. Timeout phải enforce.
209. Memory budget phải enforce.
210. Latency budget phải enforce.

---

# 224. Acceptance matrix

Tối thiểu:

```text
Core safety enforcement       220
Policy/constraint             180
Guardrails                    180
Risk/hazard                   160
Action safety                 180
Fail-safe/recovery            180
Safe exploration              120
Sandbox                       100
Realtime safety               120
Distributed safety            120
AI alignment                  180
Agent safety                  150
Learning/update safety        120
Model/environment drift       100
Security/privacy              120
Fault injection               100
Incident handling             120
Audit/provenance               90
Compiler/IR                    90
Production/continuous         120
```

**Target: ≥ 2,500 tests.**

---

# 225. Final architectural contract

Axiom phải giữ rõ bốn lớp:

```text
661
WHAT SHOULD BE DONE?
Goals / Preferences / Utility / Decision
        │
        ▼
662
HOW DOES THE SYSTEM LEARN OR ADAPT?
        │
        ▼
663
DOES THE SYSTEM SATISFY DECLARED CRITERIA?
Evaluation / Verification / Validation
        │
        ▼
664
IS THIS SPECIFIC ACTION SAFE AND AUTHORIZED RIGHT NOW?
Runtime Safety / Guardrails / Risk / Enforcement
```

Sau đó:

```text
664 Safety Enforcement
        │
        ├── DENY
        ├── BLOCK
        ├── DEGRADE
        ├── ESCALATE
        ├── FALLBACK
        └── PERMIT
                │
                ▼
             603/639
       Capability + Policy
                │
                ▼
             Execute
```

---

# 226. Architectural principle cuối cùng

Axiom không nên xây một "AI safety score" duy nhất.

Thay vào đó:

```text
Goals
Preferences
Utility
Constraints
Policies
Capabilities
Risk
Evidence
Evaluation
Runtime State
Authority
```

phải được biểu diễn riêng và liên kết bằng provenance.

Điều này tránh một lỗi kiến trúc rất nguy hiểm:

```text
score = 0.97
therefore safe
```

Thay bằng:

```text
hard constraints: PASS
authorization: PASS
capability: PASS
risk: BELOW_THRESHOLD
environment: IN_ENVELOPE
guardrails: PASS
runtime invariants: PASS
```

Đây là mô hình phù hợp hơn cho một ngôn ngữ native có AI runtime cấp hệ thống.

**BOOTSTRAP-664 — COMPLETE.**
:::

Task kế tiếp: **BOOTSTRAP-665 — Native AI Human Oversight, Human-in-the-Loop, Approval, Intervention, Escalation, Consent & Collaborative Control Runtime 5.0**.