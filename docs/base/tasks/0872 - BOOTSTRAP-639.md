Tiếp tục với **BOOTSTRAP-639 — Native Distributed Policy Decision, Policy Evaluation, Rule Engine, Admission Control, Governance, Compliance Guardrails & Declarative Authorization Runtime 5.0**.

:::writing{variant="document" id="58314" title="BOOTSTRAP-639 — Native Distributed Policy Decision, Policy Evaluation, Rule Engine, Admission Control, Governance, Compliance Guardrails & Declarative Authorization Runtime 5.0"}
# BOOTSTRAP-639
## Native Distributed Policy Decision, Policy Evaluation, Rule Engine, Admission Control, Governance, Compliance Guardrails & Declarative Authorization Runtime 5.0

**Status:** COMPLETE  
**Layer:** Distributed Policy & Governance Plane  
**Depends on:** BOOTSTRAP-600 → BOOTSTRAP-638

---

# 1. Mục tiêu

BOOTSTRAP-639 xây dựng **policy decision engine** native của Axiom.

Nó chịu trách nhiệm:

- policy evaluation;
- authorization decision;
- admission control;
- operational governance;
- resource admission;
- service access rules;
- deployment guardrails;
- data access rules;
- tenant isolation;
- environment restrictions;
- credential usage constraints;
- dynamic policy evaluation;
- distributed policy distribution;
- policy versioning;
- policy rollout;
- policy simulation;
- policy audit;
- policy explanation.

Mục tiêu kiến trúc:

> **Policy phải là dữ liệu khai báo có thể kiểm chứng, không phải một chương trình tùy ý chạy trong control plane.**

639 vì vậy **không trở thành một scripting engine thứ hai**.

---

# 2. Ranh giới với các hệ thống trước

| Hệ thống | Vai trò |
|---|---|
| 603 | capability/security boundary |
| 610 | cryptography |
| 627 | identity/authentication |
| 637 | dynamic configuration/control values |
| 638 | credential/trust lifecycle |
| 639 | policy decision/evaluation |
| 635 | cluster/control-plane coordination |
| 636 | deployment orchestration |
| 606 | resource enforcement |
| 631 | service execution |
| 632 | edge execution |
| 633 | telemetry |
| 634 | events |

Điểm quan trọng:

```text
637 = giá trị runtime
639 = quyết định policy
603 = authority enforcement
```

Ví dụ:

```text
637:
request_timeout = 5s

639:
service A may call service B = true

603:
caller possesses capability X = true

631:
perform request
```

---

# 3. Không biến policy thành arbitrary code

Core policy language **không cho phép**:

- filesystem access;
- network access;
- arbitrary function calls;
- dynamic library loading;
- process creation;
- thread creation;
- mutable global state;
- unbounded loops;
- recursion không giới hạn;
- random numbers;
- wall-clock access tùy ý;
- secret extraction.

Policy phải là:

```text
Input
 ↓
Deterministic Evaluation
 ↓
Decision
```

---

# 4. Kiến trúc

```text
                         ┌───────────────────────┐
                         │   Application/Service  │
                         └───────────┬───────────┘
                                     │
                               Policy Request
                                     │
                         ┌───────────▼───────────┐
                         │       639 Runtime     │
                         ├───────────────────────┤
                         │ Policy Registry        │
                         │ Policy Compiler        │
                         │ Policy Evaluator      │
                         │ Decision Cache         │
                         │ Admission Controller  │
                         │ Governance Engine     │
                         │ Explain Engine        │
                         │ Simulation Engine     │
                         │ Rollout Controller    │
                         └───────────┬───────────┘
                                     │
       ┌──────────────┬──────────────┼──────────────┬──────────────┐
       ▼              ▼              ▼              ▼              ▼
      603            627            637            638            635
   Capability       Identity       Dynamic        Trust          Control
                                    Config
       │              │              │              │              │
       └──────────────┴──────────────┴──────────────┴──────────────┘
                                     │
                                     ▼
                               606 / 631 / 632
```

---

# 5. Core principles

1. Default deny đối với security-sensitive decisions.
2. Policy phải typed.
3. Policy revision immutable.
4. Evaluation deterministic trong cùng input snapshot.
5. Policy snapshot immutable.
6. Policy rollout atomic theo scope.
7. Policy update không cần restart application.
8. Policy engine không tự cấp capability.
9. Policy không được nâng authority.
10. Policy không được bypass 603.
11. Security policy có precedence cao hơn operational policy.
12. Policy evaluation phải bounded.
13. Không có arbitrary code execution.
14. Không bắt buộc GC.
15. Hot-path evaluation phải low allocation.
16. Distributed policy phải có version/revision.
17. Stale policy phải có semantics explicit.
18. Fail-open/fail-closed phải được khai báo.
19. Policy decision phải explainable.
20. Policy changes phải audit được.

---

# 6. Policy model

```text
Policy {
    policy_id
    namespace
    version
    revision
    schema
    priority
    scope
    rules
    defaults
    activation
    expiration
}
```

---

# 7. Policy identity

```text
PolicyId
PolicyVersion
PolicyRevision
PolicyGeneration
```

Ví dụ:

```text
policy = service-access
revision = 1842
generation = 12
```

Revision không được tái sử dụng.

---

# 8. Policy scope

Các scope:

```text
Global
Federation
Cluster
Region
Zone
Service
Workload
Device
Tenant
User
Session
Request
```

---

# 9. Scope precedence

Policy có thể kế thừa:

```text
Global
  ↓
Federation
  ↓
Cluster
  ↓
Region
  ↓
Service
  ↓
Workload
  ↓
Tenant
  ↓
Request
```

Nhưng quyền cao hơn không thể bị scope thấp hơn mở rộng ngoài authority.

---

# 10. Policy composition

Có ba kiểu:

```text
Override
Merge
Restrict
```

Security-sensitive policy mặc định:

```text
Restrict
```

---

# 11. Restrictive composition

Nếu global:

```text
allow TLS >= 1.3
```

local không thể:

```text
allow TLS 1.0
```

---

# 12. Policy priority

Mỗi policy có:

```text
priority
```

nhưng priority không được phép vượt security boundary.

---

# 13. Decision model

Core:

```text
PolicyDecision {
    result
    reason
    policy_id
    revision
    obligations
    constraints
}
```

---

# 14. Decision results

```text
Allow
Deny
Challenge
Indeterminate
Unavailable
NotApplicable
```

---

# 15. Challenge

Ví dụ:

```text
MFA required
additional capability required
step-up authentication required
```

639 chỉ trả decision.

627/ứng dụng thực hiện challenge.

---

# 16. Indeterminate

Dùng khi:

```text
required attribute unavailable
policy dependency missing
evaluation error
```

Không tự động chuyển thành Allow.

---

# 17. Unavailable

Ví dụ policy registry unavailable.

Decision phải phụ thuộc:

```text
availability_mode
```

---

# 18. Availability modes

```text
FailClosed
FailOpen
UseLastKnownGood
UseStaticDefault
DenyOnUnknown
```

Security policy mặc định:

```text
FailClosed
```

---

# 19. Request model

```text
PolicyRequest {
    request_id
    action
    resource
    subject
    environment
    attributes
    capabilities
    identity
    policy_snapshot
}
```

---

# 20. Subject

```text
Subject {
    subject_id
    identity
    type
    attributes
}
```

Có thể là:

```text
User
Service
Workload
Device
Tenant
System
Anonymous
```

---

# 21. Resource

```text
Resource {
    resource_id
    resource_type
    owner
    scope
    attributes
}
```

---

# 22. Action

Action phải typed:

```text
Read
Write
Create
Update
Delete
Execute
Publish
Subscribe
Deploy
Rotate
Admin
```

Ứng dụng có thể định nghĩa domain-specific actions.

---

# 23. Resource-action pair

Policy nên evaluate:

```text
(subject, action, resource, context)
```

không chỉ:

```text
subject → resource
```

---

# 24. Context

Context có thể chứa:

```text
cluster
region
service_version
deployment_revision
network_zone
device_type
tenant
request_type
risk_metadata
```

Chỉ attributes được explicit provision mới được sử dụng.

---

# 25. No hidden context

Policy không tự truy cập:

```text
filesystem
environment variables
process memory
network
```

để lấy context.

---

# 26. Policy attribute model

Typed:

```text
String
Bool
Int
UInt
Float
Enum
Duration
Timestamp
Version
IpAddress
Network
Identifier
Set<T>
Map<K,V>
```

---

# 27. Attribute absence

Ba-state:

```text
Present
Absent
Invalid
```

không ép:

```text
Absent → false
```

một cách mơ hồ.

---

# 28. Attribute source

Mỗi attribute có source:

```text
Request
Identity
Capability
Config
Credential
Cluster
Deployment
Resource
System
```

---

# 29. Attribute trust level

```text
Untrusted
Authenticated
Verified
Attested
SystemGenerated
```

Policy có thể yêu cầu minimum trust.

---

# 30. Policy expression language

Ví dụ:

```text
when
    subject.type == Service
    and action == Read
    and resource.type == Document
then
    allow
```

---

# 31. Operators

Core:

```text
==
!=
<
<=
>
>=
in
not_in
contains
starts_with
ends_with
matches
exists
is_null
```

Regex nếu hỗ trợ phải bounded.

---

# 32. Boolean operators

```text
and
or
not
```

---

# 33. Set operations

```text
contains
subset_of
intersects
```

Giới hạn kích thước để tránh DoS.

---

# 34. No arbitrary functions

Không:

```text
call(my_function())
```

trong policy core.

Chỉ built-in pure functions đã định nghĩa.

---

# 35. Built-in functions

Có thể có:

```text
hash
normalize
parse_version
ip_in_network
time_window
set_contains
```

Tất cả phải deterministic/bounded.

---

# 36. Hash function

Hash dùng cho:

- stable targeting;
- deterministic sampling;
- cohort assignment.

Không dùng hash policy như cryptographic primitive.

Crypto thuộc 610.

---

# 37. Time semantics

Policy có thể sử dụng:

```text
request.timestamp
```

đã được host cung cấp.

Không tự gọi system clock.

---

# 38. Version comparison

Native:

```text
version >= 2.4
```

phải có semantic rõ ràng.

---

# 39. IP/network matching

```text
ip in 10.0.0.0/8
```

phải parse canonical.

---

# 40. Rule

```text
Rule {
    id
    condition
    effect
    priority
    obligations
}
```

---

# 41. Effects

```text
Allow
Deny
Challenge
Limit
Transform
Route
Require
```

Security core ưu tiên:

```text
Allow/Deny/Challenge
```

Operational policies có thể sử dụng các effect khác.

---

# 42. Obligations

Ví dụ:

```text
audit = required
mfa = required
rate_limit = 100/s
timeout <= 5s
encryption = required
```

---

# 43. Constraints

Decision có thể trả:

```text
Constraint {
    name
    value
}
```

Ví dụ:

```text
max_response_bytes = 10MB
```

---

# 44. Constraint enforcement

639 phát decision.

Subsystem tương ứng thực thi:

```text
606 → resource
631 → service
632 → gateway
603 → capability
610 → crypto
```

---

# 45. Policy evaluation pipeline

```text
Receive
 ↓
Authenticate context
 ↓
Load snapshot
 ↓
Validate request
 ↓
Evaluate rules
 ↓
Resolve conflicts
 ↓
Apply obligations
 ↓
Produce decision
 ↓
Audit/telemetry
```

---

# 46. Policy snapshot

```text
PolicySnapshot {
    revision
    policies
    schema_fingerprint
    activation_epoch
}
```

Immutable.

---

# 47. Atomic activation

Policy revision mới:

```text
prepare
→ validate
→ compile
→ verify
→ activate
```

Nếu fail:

```text
old snapshot remains active
```

---

# 48. Compiled policy

Policy compiler có thể tạo:

```text
PolicyIR
PolicyBytecode
DecisionDAG
CompiledMatcher
```

---

# 49. Native policy compilation

Production profile có thể compile policy thành native decision code.

Mục tiêu:

```text
low latency
low allocation
predictable execution
```

---

# 50. No JIT requirement

Policy runtime không bắt buộc JIT.

Có thể:

```text
compile-time
install-time
runtime precompile
```

---

# 51. Policy IR

IR node:

```text
LoadAttribute
Compare
SetTest
And
Or
Not
Branch
Decision
Obligation
Constraint
```

---

# 52. Policy optimizer

Có thể:

```text
constant folding
dead rule elimination
predicate factoring
decision tree optimization
attribute prefetch planning
```

---

# 53. Short-circuit

```text
false AND X
```

không cần evaluate X.

```text
true OR X
```

không cần evaluate X.

---

# 54. Rule ordering

Compiler có thể reorder pure predicates nếu semantics giữ nguyên.

Nếu có side-effect obligations:

```text
preserve semantic order
```

---

# 55. Bounded evaluation

Policy phải có:

```text
max_rules
max_expression_depth
max_set_size
max_string_size
max_regex_cost
max_evaluation_steps
```

---

# 56. Evaluation budget

```text
EvaluationBudget {
    max_steps
    max_bytes
    max_depth
    deadline
}
```

---

# 57. Evaluation timeout

Nếu vượt budget:

```text
Indeterminate
```

không tự Allow.

---

# 58. Policy recursion

Core không cho recursion.

Nếu future extension hỗ trợ:

```text
explicit max_depth
```

---

# 59. Policy imports

Policy có thể import:

```text
policy module
```

nhưng import graph phải acyclic.

---

# 60. Policy modules

```text
PolicyModule {
    module_id
    version
    exports
    imports
    fingerprint
}
```

---

# 61. Policy package

638/625 package policy có:

```text
policy schema
compiler version
dependency versions
fingerprints
signature
```

---

# 62. Signed policy

Production policy có thể yêu cầu:

```text
signed = true
```

Signature verification qua 610.

---

# 63. Policy publisher

```text
PublisherId
PolicySigningKeyId
PolicyRevision
```

---

# 64. Policy trust

Policy chỉ active nếu:

```text
signature valid
publisher trusted
schema compatible
scope authorized
revision valid
```

---

# 65. Policy rollback

Rollback phải là:

```text
new revision
```

tham chiếu revision cũ.

Không mutate history.

---

# 66. Policy history

```text
Revision 100
Revision 101
Revision 102
Revision 103
```

Mỗi revision immutable.

---

# 67. Compare-and-swap

Update:

```text
update(policy, expected_revision=102)
```

Nếu current != 102:

```text
Conflict
```

---

# 68. Policy transactions

Có thể atomically thay đổi:

```text
policy A
policy B
policy C
```

trong cùng namespace.

---

# 69. Cross-policy transaction

Không mặc định atomic across clusters.

Distributed transaction nếu cần thuộc higher-level orchestration.

---

# 70. Policy dependency

Policy có thể khai báo:

```text
requires policy X revision >= 20
```

---

# 71. Dependency validation

Activation chỉ thành công nếu dependencies satisfy constraints.

---

# 72. Policy rollout

Strategies:

```text
All
Rolling
Canary
Wave
Region
Cluster
Tenant
ServiceVersion
```

---

# 73. Policy canary

Một policy revision có thể áp dụng:

```text
1%
10%
50%
100%
```

target bằng stable deterministic hashing.

---

# 74. Policy targeting

Targeting attributes:

```text
cluster
region
zone
service
version
tenant
device
cohort
labels
```

---

# 75. Targeting hash

```text
bucket =
hash(policy_id, subject_key, salt) % 10000
```

Stable.

---

# 76. No raw PII requirement

Subject key nên là:

```text
opaque stable identifier
```

không cần raw email/name.

---

# 77. Privacy

639 không thu thập PII mặc định.

Attributes phải được explicit provision.

---

# 78. Policy evaluation cache

Cache key:

```text
policy_revision
subject_context_fingerprint
resource
action
```

---

# 79. Cache invalidation

Policy revision change phải invalidate hoặc version-bypass cache.

---

# 80. Negative cache

Deny decisions có thể cache nếu:

```text
policy
context
TTL
```

an toàn.

---

# 81. Positive cache

Allow cache phải có TTL và policy revision.

Security-sensitive allow không được tồn tại vô hạn.

---

# 82. Decision cache poisoning

Cache entry phải gắn:

```text
policy_fingerprint
context_fingerprint
```

---

# 83. Local evaluator

Mỗi service có thể embed:

```text
PolicyEvaluator
```

để tránh network round-trip.

---

# 84. Central evaluator

Có thể có:

```text
PolicyDecisionService
```

cho policies cần centralized control.

---

# 85. Hybrid evaluation

Preferred:

```text
central policy distribution
+
local deterministic evaluation
```

---

# 86. Data-plane independence

Service không nên phụ thuộc network call cho mọi authorization decision.

Policy snapshot local phải hỗ trợ operation khi control plane tạm unavailable.

---

# 87. Staleness

Snapshot có:

```text
issued_at
expires_at
max_staleness
```

---

# 88. Stale policy

Nếu snapshot quá cũ:

```text
FailClosed
FailOpen
UseLastKnownGood
```

theo policy.

---

# 89. Security vs operational policy

Security:

```text
default fail closed
```

Operational tuning:

```text
policy-specific availability mode
```

---

# 90. Admission control

639 cung cấp:

```text
AdmissionController
```

cho:

- deploy;
- service activation;
- resource allocation;
- workload placement;
- API requests;
- tenant operations;
- plugin loading;
- package installation.

---

# 91. Admission request

```text
AdmissionRequest {
    actor
    operation
    object
    requested_resources
    environment
    context
}
```

---

# 92. Admission decision

```text
Admit
Reject
Defer
RequireApproval
```

---

# 93. Resource admission

606 cung cấp:

```text
available resources
```

639 quyết định:

```text
policy allows?
```

606 quyết định:

```text
resource available?
```

---

# 94. Deployment admission

636 gửi:

```text
release
target
resource_delta
risk_metadata
```

639 trả:

```text
allow
deny
require_approval
```

---

# 95. Placement admission

635 có thể hỏi:

```text
can workload run on node?
```

639 evaluate policy constraints.

635 vẫn quyết định placement.

---

# 96. Package admission

625 có thể hỏi:

```text
is package allowed in this environment?
```

639 evaluate:

```text
publisher
signature
target
capabilities
policy
```

---

# 97. Plugin admission

623:

```text
plugin load request
```

639:

```text
publisher
permissions
ABI
environment
```

---

# 98. Credential admission

638:

```text
issue credential?
```

639 có thể supply governance decision.

603 vẫn controls authority.

---

# 99. Network admission

632/631:

```text
service call
```

639 can evaluate operational authorization.

603 enforces capability.

---

# 100. Double authorization

Không được nhầm:

```text
639 decision
```

với:

```text
603 capability
```

Một operation cần cả hai nếu policy yêu cầu:

```text
CapabilityPresent
AND
PolicyAllows
```

---

# 101. Security composition

Effective authorization:

```text
Capability
AND
Identity
AND
Policy
AND
ResourceState
```

---

# 102. Capability cannot be granted by policy

639 không thể:

```text
create capability
```

chỉ có thể:

```text
require capability
```

---

# 103. Policy cannot widen capability

Nếu 603 deny:

```text
network.connect
```

639 allow không override được.

---

# 104. Governance policy

Operational governance examples:

```text
production deployment requires signed release
GPU workload requires approved image
external network requires declared capability
database migration requires backup
```

---

# 105. Guardrails

Guardrail:

```text
Guardrail {
    condition
    violation
    severity
    action
}
```

Actions:

```text
Reject
Warn
RequireApproval
Quarantine
Defer
Audit
```

---

# 106. Severity

```text
Info
Notice
Warning
High
Critical
```

Severity chỉ mô tả policy consequence, không phải security classification tự động.

---

# 107. Approval workflow

639 có thể trả:

```text
RequireApproval
```

629 workflow hoặc external governance system xử lý approval.

639 không trở thành workflow engine.

---

# 108. Approval token

Approval:

```text
Approval {
    approval_id
    policy_revision
    subject
    operation
    scope
    expires_at
}
```

---

# 109. Approval binding

Approval phải bind với:

```text
operation
resource
revision
actor
scope
expiry
```

Không reuse arbitrary.

---

# 110. Break-glass

Emergency override:

```text
BreakGlassGrant {
    issuer
    reason
    scope
    expires_at
    max_uses
}
```

---

# 111. Break-glass security

Break-glass:

- time bounded;
- scope bounded;
- audit mandatory;
- cannot disable cryptographic verification;
- cannot bypass immutable platform safety invariants.

---

# 112. Policy simulation

639 phải hỗ trợ:

```text
simulate(request, policy_revision)
```

không activate policy.

---

# 113. Policy diff

CLI:

```text
axiom policy diff v100 v101
```

show:

```text
added rules
removed rules
changed predicates
changed scope
changed defaults
changed obligations
```

---

# 114. Policy explain

```text
axiom policy explain request
```

trả:

```text
matched rule
non-matched rules
attributes
effective policy
decision
obligations
revision
```

---

# 115. Explain security

Explain output không được expose:

```text
secret
private key
sensitive identity attributes
```

nếu caller không có capability.

---

# 116. Explain trace

Internal evaluation trace:

```text
Rule 1 → false
Rule 2 → true
Rule 7 → skipped
Default → deny
```

Có thể redact values.

---

# 117. Audit event

```text
PolicyEvaluated
PolicyActivated
PolicyRolledBack
PolicyRejected
AdmissionDenied
AdmissionAllowed
ApprovalRequired
BreakGlassUsed
```

---

# 118. Decision logging

Không bắt buộc log every decision.

High-volume authorization có thể:

```text
sample
aggregate
count
```

---

# 119. Security-critical audit

Certain actions:

```text
credential.export
policy.modify
trust.modify
break_glass
```

phải audit đầy đủ nếu policy yêu cầu.

---

# 120. Metrics

```text
policy_evaluation_total
policy_allow_total
policy_deny_total
policy_error_total
policy_latency
policy_cache_hit
policy_cache_miss
admission_allow
admission_deny
policy_revision_lag
```

---

# 121. Cardinality protection

Không cho metric label trực tiếp chứa:

```text
raw user ID
request ID
secret
unbounded resource ID
```

---

# 122. Distributed policy registry

639 có:

```text
PolicyRegistry
```

storage có thể dùng 628.

---

# 123. Registry consistency

Policy types:

```text
SecurityCritical
Operational
Experimental
```

SecurityCritical có thể yêu cầu:

```text
Quorum
Linearizable
```

theo deployment.

---

# 124. Policy distribution

```text
Registry
 ↓
Policy Watch
 ↓
Local Compiler
 ↓
Validation
 ↓
Activation
```

---

# 125. Watch API

```text
watch(namespace)
watch(policy_id)
watch(prefix)
```

---

# 126. Watch event

```text
PolicyAdded
PolicyUpdated
PolicyRemoved
PolicyRevoked
SnapshotRequired
```

---

# 127. Watch reconnect

Consumer giữ:

```text
last_revision
```

Reconnect:

```text
resume(last_revision)
```

Nếu history unavailable:

```text
full snapshot
```

---

# 128. Backpressure

Policy watch phải có:

```text
bounded queue
coalescing
snapshot replacement
```

---

# 129. Coalescing

Nếu revisions:

```text
101
102
103
104
```

consumer chưa xử lý:

```text
101
```

có thể nhận:

```text
snapshot 104
```

nếu intermediate revisions không cần replay.

---

# 130. Revision monotonicity

Consumer không được activate:

```text
revision 103
```

sau:

```text
revision 104
```

---

# 131. Policy epochs

Distributed rollout có:

```text
PolicyEpoch
```

giúp detect stale controller.

---

# 132. Policy publisher fencing

Publisher phải có:

```text
issuer_epoch
```

635 có thể cấp/fence control-plane authority.

---

# 133. Multi-cluster policy

Federation có:

```text
GlobalPolicy
ClusterPolicy
RegionalPolicy
```

Global policy không nhất thiết force identical local state nếu federation policy cho phép exceptions.

---

# 134. Local exception

Exception phải explicit:

```text
exception_scope
reason
expiry
approver
```

---

# 135. Exception cannot widen security authority

Exception chỉ có thể:

```text
tighten
```

hoặc mở rộng trong explicit governance domain mà authority cho phép.

---

# 136. Policy inheritance

Child scope inherits parent.

Ví dụ:

```text
global deny external network
```

service không thể tự override.

---

# 137. Policy override

Operational policies có thể override parent nếu parent khai báo:

```text
override_allowed = true
```

---

# 138. Policy merge conflict

Nếu hai policies cùng priority conflict:

```text
Conflict
```

không random choose.

---

# 139. Deterministic conflict resolution

Conflict resolution:

```text
explicit priority
then scope
then policy id
```

nhưng security policies ưu tiên restrictive semantics.

---

# 140. Deny precedence

Trong security authorization:

```text
Deny
```

thường thắng:

```text
Allow
```

trừ khi policy language khai báo một semantics khác rõ ràng.

---

# 141. Default decision

Security authorization:

```text
Default = Deny
```

Operational admission:

```text
Default = policy-defined
```

---

# 142. Policy version compatibility

Policy schema có:

```text
schema_version
compiler_version
runtime_min_version
```

---

# 143. Forward compatibility

Runtime mới có thể đọc policy cũ.

Policy mới yêu cầu feature chưa hỗ trợ:

```text
Unsupported
```

không silent ignore.

---

# 144. Policy migration

Migration:

```text
PolicyV1
→
PolicyV2
```

phải explicit.

---

# 145. Deterministic compilation

Cùng:

```text
policy source
compiler version
schema
```

phải sinh cùng:

```text
policy fingerprint
```

nếu deterministic build profile bật.

---

# 146. Policy fingerprint

```text
PolicyFingerprint =
hash(canonical_policy + compiler_semantics + dependencies)
```

Hash primitive lấy từ 610.

---

# 147. Canonicalization

Canonical policy:

- deterministic ordering;
- normalized identifiers;
- normalized numbers;
- normalized strings;
- explicit defaults.

---

# 148. Policy signing

Signature được tạo trên:

```text
canonical_policy
fingerprint
metadata
```

---

# 149. Replay protection

Policy activation phải kiểm tra:

```text
revision
epoch
expiration
publisher
```

---

# 150. Expiring policies

Policy có thể:

```text
expires_at
```

Sau expiry:

```text
inactive
```

theo fallback policy.

---

# 151. Temporary emergency policy

Ví dụ:

```text
deny external traffic
expires in 1h
```

Sau expiry:

```text
previous stable policy
```

hoặc default tùy configuration.

---

# 152. Policy activation windows

Policy có thể:

```text
not_before
not_after
```

---

# 153. Scheduled activation

637/635 có thể trigger.

639 thực hiện activation nếu:

```text
all validations pass
```

---

# 154. Policy health gate

633 metrics có thể được sử dụng để quyết định:

```text
continue rollout
pause rollout
```

639 chỉ cung cấp policy decision; 636 orchestration.

---

# 155. Policy progressive rollout

```text
prepare
→ validate
→ canary
→ observe
→ wave
→ full
```

---

# 156. No automatic statistical judgment

639 không tự quyết định:

```text
which policy is "better"
```

Nó chỉ evaluate các điều kiện được cấu hình.

---

# 157. Experiment integration

637 experiment có thể chọn policy variant.

639 evaluate selected policy.

---

# 158. Policy variant

```text
PolicyVariant {
    variant_id
    policy_revision
    targeting
}
```

---

# 159. Policy targeting stability

Subject phải nhận cùng variant khi:

```text
experiment_id
subject_key
salt
allocation
```

không đổi.

---

# 160. Policy rollout safety

Một policy revision không được activate nếu:

```text
required schema unavailable
required provider unavailable
required capability absent
```

---

# 161. Admission dry-run

636:

```text
admission.check(deployment)
```

không mutate state.

---

# 162. Admission commit

Sau khi plan verified:

```text
admission.commit(token)
```

Token phải:

```text
short-lived
scope-bound
revision-bound
```

---

# 163. Admission token

```text
AdmissionToken {
    token_id
    request_fingerprint
    policy_revision
    expires_at
}
```

---

# 164. Replay protection

Token không được reuse sau:

```text
consumed
expired
policy changed
```

nếu policy yêu cầu single-use.

---

# 165. Governance graph

639 có thể model:

```text
Policy
 ├── requires
 ├── constrains
 ├── protects
 └── applies_to
```

Dùng để explain/dependency validation.

---

# 166. Policy dependency graph

Phải detect:

```text
cycle
missing dependency
version conflict
scope conflict
```

---

# 167. Policy bundle

Bundle:

```text
PolicyBundle {
    policies
    dependencies
    schema_fingerprint
    signature
    revision
}
```

---

# 168. Policy bundle activation

Atomic per target scope.

---

# 169. Policy bundle rollback

Rollback tạo bundle revision mới.

---

# 170. Policy package integration

625 có thể package:

```text
.axpolicy
```

với:

```text
policy definitions
schemas
signatures
dependencies
```

---

# 171. Policy compiler integration

Compiler command:

```text
axiom policy compile
axiom policy validate
axiom policy explain
axiom policy simulate
```

---

# 172. Generated metadata

Compiler tạo:

```text
.axpolicy
.axdecision
.axadmission
.axguardrail
```

---

# 173. Source annotations

```text
@policy
@rule
@allow
@deny
@requires
@guardrail
@admission
@scope
@priority
@default
@obligation
@constraint
```

---

# 174. Example

```text
@policy("orders-access")
policy OrdersAccess {
    rule read_orders {
        when
            subject.service == "billing"
            and action == Read
            and resource.type == "Order"
        then
            allow
    }
}
```

---

# 175. Example deny

```text
@policy("production-network")
policy ProductionNetwork {
    rule deny_external {
        when
            environment == Production
            and network.destination_class == External
        then
            deny
    }
}
```

---

# 176. Example guardrail

```text
@guardrail("production-deploy")
guard ProductionDeploy {
    when
        environment == Production
        and release.signed == false
    then
        reject
}
```

---

# 177. Example obligation

```text
then
    allow
    with audit = Required
```

---

# 178. Example admission

```text
@admission("gpu")
policy GpuAdmission {
    when
        workload.requires_gpu
        and workload.image_trusted
    then
        admit
}
```

---

# 179. Policy DSL syntax goals

Syntax phải:

- concise;
- typed;
- deterministic;
- AI-readable;
- parser-friendly;
- no punctuation overload;
- explicit scope;
- explicit defaults.

---

# 180. No reflection requirement

Policy metadata phải compiler-generated.

Runtime không cần reflection.

---

# 181. AI-readable representation

`.axpolicy` nên chứa:

```text
policy_id
scope
inputs
rules
effects
precedence
constraints
dependencies
revision
fingerprint
```

---

# 182. AI tooling

AI agent có thể query:

```text
why was request denied?
which rule applies?
what changed between revisions?
which service depends on this policy?
```

---

# 183. Policy impact analysis

CLI:

```text
axiom policy impact policy-123
```

cho biết:

```text
affected services
clusters
routes
workloads
tenants
```

---

# 184. Blast-radius analysis

Không thực hiện mutation.

Chỉ tính:

```text
policy scope
dependencies
targets
```

---

# 185. Policy linting

Lint rules:

```text
unreachable rule
shadowed rule
contradictory rules
missing default
overly broad scope
unbounded regex
unused attribute
conflicting priority
```

---

# 186. Security linting

Có thể cảnh báo:

```text
allow-all
wildcard resource
wildcard subject
long-lived exception
fail-open security policy
missing audit
```

---

# 187. No automatic rejection by lint

Lint severity:

```text
Error
Warning
Info
```

Production policy can enforce selected errors.

---

# 188. Policy test cases

Policy package có thể chứa:

```text
PolicyTest {
    input
    expected_decision
}
```

---

# 189. Golden tests

```text
input
→
decision
```

phải reproducible.

---

# 190. Differential tests

Hai compiler/runtime versions:

```text
same input
→
same decision
```

trong compatibility window.

---

# 191. Fuzz testing

Fuzz:

```text
parser
AST
compiler
evaluator
attributes
policy bundles
```

---

# 192. Resource abuse testing

Test:

```text
huge policy
huge string
huge set
deep AST
many rules
many targets
```

phải bounded.

---

# 193. Distributed failure tests

Test:

```text
registry unavailable
stale snapshot
partition
leader change
duplicate watch
out-of-order revisions
```

---

# 194. Security failure tests

Test:

```text
invalid signature
expired policy
revoked publisher
wrong scope
wrong tenant
stale epoch
invalid approval
```

---

# 195. Policy cache tests

Test:

```text
revision change
cache poisoning
negative cache
TTL expiry
snapshot replacement
```

---

# 196. Admission tests

Test:

```text
allow
deny
defer
approval
expired token
replay
policy change
```

---

# 197. Performance target

Local evaluation mục tiêu:

```text
O(number_of_relevant_rules)
```

không phải:

```text
O(all_policies)
```

---

# 198. Indexing

Compiler/runtime có thể index theo:

```text
action
resource_type
subject_type
scope
tenant
```

---

# 199. Hot path

Authorization hot path:

```text
request
→
snapshot lookup
→
compiled evaluator
→
decision
```

Không bắt buộc:

```text
network
database
allocation
global lock
```

---

# 200. Read-side synchronization

Policy snapshot pointer có thể dùng:

```text
atomic snapshot reference
```

hoặc equivalent immutable generation mechanism.

---

# 201. Update-side synchronization

Policy activation:

```text
build new snapshot
validate
atomic publish
```

Readers không block lâu.

---

# 202. Memory reclamation

Old policy snapshots được reclaim khi:

```text
no active readers
```

Không yêu cầu GC.

Có thể dùng:

```text
epoch reclamation
RCU-like mechanism
reference counting
```

tùy runtime implementation.

---

# 203. Compiler optimization

Nếu policy static:

```text
compile-time eliminate
```

Ví dụ:

```text
@requires(environment == Production)
```

có thể specialize binary nếu environment immutable.

---

# 204. Dead policy elimination

Nếu không có consumer:

```text
policy module
```

có thể dead-strip.

---

# 205. Minimal binary

Local application không dùng distributed policy:

```text
AXPOLICY_NONE
```

không link:

```text
registry
watch
distributed transport
```

---

# 206. Platform portability

639 phải hoạt động:

```text
Windows
Linux
macOS
Android
iOS
WASM
Embedded
```

---

# 207. WASM

WASM policy evaluation local.

Registry/network là host capability.

---

# 208. Embedded

Có thể compile policy static:

```text
ROM policy
```

không cần distributed runtime.

---

# 209. Mobile

Policy cache phải hỗ trợ:

```text
offline
background restrictions
network unavailable
```

---

# 210. Edge

Edge policy bundle có:

```text
scope
expiry
delegation
issuer_epoch
```

---

# 211. Edge offline

Khi disconnected:

```text
last valid signed snapshot
```

được dùng theo policy.

---

# 212. Edge stale limit

Nếu quá:

```text
max_offline_duration
```

decision:

```text
fail closed/open
```

theo policy.

---

# 213. Federation

Federation có:

```text
GlobalPolicy
RegionalPolicy
ClusterPolicy
EdgePolicy
```

---

# 214. Global policy distribution

```text
Global Registry
 ↓
Regional
 ↓
Cluster
 ↓
Node
 ↓
Service
```

---

# 215. Policy propagation

Propagation event:

```text
PolicyRevisionPublished
```

qua 634.

---

# 216. Policy consistency

Security-critical policy có thể yêu cầu:

```text
quorum activation
```

Operational policy có thể:

```text
eventual activation
```

---

# 217. Activation acknowledgment

Consumer trả:

```text
PolicyActivated {
    policy_id
    revision
    target
}
```

---

# 218. Activation lag

633 đo:

```text
policy_activation_lag
```

---

# 219. Policy drift

Nếu target:

```text
expected revision 100
actual revision 97
```

state:

```text
Drifted
```

---

# 220. Policy reconciliation

Controller:

```text
observe
compare
push
verify
retry
```

---

# 221. Retry

Policy distribution retry có:

```text
exponential backoff
jitter
budget
```

---

# 222. No retry storm

Global rollout phải có:

```text
max_concurrent_targets
```

---

# 223. Tenant isolation

Policy registry phải partition:

```text
tenant namespace
```

---

# 224. Cross-tenant policy

Chỉ platform authority mới được global tenant policy.

Tenant không được query arbitrary tenant policies.

---

# 225. Sensitive policy attributes

Policy attributes có classification.

Explain/logging phải redact theo 603.

---

# 226. Secret references

Policy không chứa secret plaintext.

Có thể reference:

```text
SecretRef
CredentialRef
IdentityRef
```

nhưng evaluation phải tôn trọng access capability.

---

# 227. Policy against credential

639 có thể evaluate:

```text
credential.type
credential.generation
credential.expiry
trust.status
```

Không cần đọc private key.

---

# 228. Credential usage policy

Ví dụ:

```text
when
    credential.provider != Hardware
then
    deny production-sign
```

---

# 229. Identity policy

Ví dụ:

```text
when
    subject.identity_generation < service.required_generation
then
    deny
```

---

# 230. Deployment policy

Ví dụ:

```text
when
    release.signature.valid == false
then
    deny
```

---

# 231. Network policy

Ví dụ:

```text
when
    destination.zone == External
    and capability.network_external == false
then
    deny
```

---

# 232. Resource governance policy

Ví dụ:

```text
when
    workload.gpu_count > 8
    and tenant.tier != Enterprise
then
    deny
```

---

# 233. Scheduling policy

635 can query:

```text
admission.can_place(workload,node)
```

639 evaluates governance constraints.

---

# 234. Event policy

634 can evaluate:

```text
publisher
topic
tenant
schema
```

before publish/subscribe.

---

# 235. Workflow policy

629 can evaluate:

```text
workflow
activity
worker
tenant
resource
```

---

# 236. Compute policy

630 can evaluate:

```text
job
GPU
dataset
worker
region
```

---

# 237. Plugin policy

623 can evaluate:

```text
publisher
capabilities
ABI
target
```

---

# 238. Package policy

625 can evaluate:

```text
publisher
signature
license metadata
target
capabilities
```

License semantics remain declarative metadata, not legal interpretation.

---

# 239. Storage policy

611/628 can evaluate:

```text
tenant
data_class
operation
location
encryption_requirement
```

---

# 240. Data policy

639 can enforce governance decisions such as:

```text
data must remain within declared region
```

Execution remains in storage/network layer.

---

# 241. Compliance guardrail abstraction

639 may support generic:

```text
Guardrail {
    condition
    required_state
    violation_action
}
```

Không tuyên bố rằng guardrail tự chứng minh compliance certification.

---

# 242. Evidence

Policy engine có thể emit:

```text
PolicyEvidence {
    decision
    policy_revision
    inputs_fingerprint
    timestamp
}
```

---

# 243. Evidence privacy

Evidence không mặc định lưu raw attributes.

Có thể lưu:

```text
fingerprint
classification
source
```

---

# 244. Decision provenance

Mỗi decision có:

```text
policy_id
revision
compiler_fingerprint
runtime_semantics_version
```

---

# 245. Reproducibility

Có thể replay decision nếu:

```text
same policy snapshot
same normalized input
same semantics version
```

---

# 246. Replay

```text
policy.replay(request, revision)
```

dùng cho debugging/audit.

---

# 247. Historical policy evaluation

Có thể evaluate request against:

```text
revision 100
```

mà không activate revision đó.

---

# 248. Security of replay

Replay không được thực hiện side effects.

---

# 249. Policy evaluation purity

Core evaluator:

```text
pure
```

trong semantics.

Obligations được xử lý bên ngoài evaluator.

---

# 250. Policy side effects

Không cho:

```text
send email
write database
start process
```

trực tiếp trong rule.

---

# 251. Obligation executor

Nếu cần:

```text
ObligationExecutor
```

là subsystem bên ngoài evaluator.

---

# 252. Obligation failure

Nếu:

```text
Allow
+ required audit
```

nhưng audit unavailable:

decision có thể trở thành:

```text
Indeterminate
```

nếu policy yêu cầu audit-before-allow.

---

# 253. Transactional authorization

Một operation có thể yêu cầu:

```text
evaluate
→ reserve
→ execute
```

639 không tự giữ transaction xuyên service.

---

# 254. Policy reservation

Admission token có thể giữ policy decision trong thời gian ngắn.

---

# 255. Token expiry

Mọi decision token phải có:

```text
expiry
policy_revision
scope
```

---

# 256. Policy decision signature

Distributed environments có thể ký decision:

```text
DecisionToken {
    decision
    revision
    scope
    expiry
    signature
}
```

610 xử lý cryptography.

---

# 257. Local verification

Consumer có thể verify token offline.

---

# 258. Decision replay protection

Token có:

```text
nonce
request_fingerprint
```

nếu required.

---

# 259. No universal decision token

Local authorization không nhất thiết cần signed token.

Profile quyết định.

---

# 260. API surface

Core structs:

```text
Policy
PolicyId
PolicyRevision
PolicySnapshot
PolicyRegistry
PolicyCompiler
PolicyEvaluator
PolicyRequest
PolicyDecision
PolicyRule
PolicyContext
PolicyAttribute
PolicyTarget
PolicyScope
PolicyBundle
PolicyWatch
PolicyGuardrail
AdmissionController
AdmissionRequest
AdmissionDecision
AdmissionToken
PolicySimulator
PolicyExplainer
PolicyAudit
```

---

# 261. Struct-only API

Ví dụ:

```text
PolicyEvaluator.evaluate(self, request)
PolicyRegistry.publish(self, bundle)
PolicyRegistry.watch(self, selector)
AdmissionController.check(self, request)
PolicySimulator.run(self, request, revision)
```

Không cần class hierarchy.

---

# 262. Error model

```text
PolicyError
SchemaError
SignatureError
RevisionConflict
ScopeDenied
EvaluationLimitExceeded
AttributeMissing
PolicyUnavailable
StaleSnapshot
UnsupportedPolicyVersion
DependencyConflict
AdmissionDenied
ApprovalRequired
```

---

# 263. Concurrency

Multiple evaluators có thể chạy song song trên immutable snapshot.

Policy update không block readers dài hạn.

---

# 264. Thread safety

`PolicySnapshot` immutable.

`PolicyEvaluator` có thể share nếu provider/compiler đảm bảo thread safety.

---

# 265. Async API

Registry:

```text
publish_async
watch_async
sync_snapshot_async
```

Evaluator local vẫn synchronous.

---

# 266. Scheduler integration

607 dùng cho:

```text
policy watch
distribution
recompile
rollout
```

---

# 267. Resource integration

606:

```text
policy evaluator CPU budget
memory budget
watcher quota
registry storage quota
```

---

# 268. Diagnostics integration

602:

```text
policy decision trace
revision
evaluation latency
errors
```

---

# 269. Distributed telemetry

633:

```text
policy revision lag
decision latency
deny rate
policy rollout state
```

---

# 270. Event integration

634:

```text
PolicyPublished
PolicyActivated
PolicyRevoked
PolicyRollback
PolicyDriftDetected
AdmissionDenied
```

---

# 271. Service integration

631:

```text
authorize(request)
```

có thể gọi local evaluator.

---

# 272. Gateway integration

632:

```text
route authorization
tenant policy
rate policy
header policy
edge admission
```

---

# 273. Deployment integration

636:

```text
deployment admission
rollout guardrails
health gate policy
```

---

# 274. Cluster integration

635:

```text
node admission
workload admission
control-plane policy
```

---

# 275. Identity integration

627:

```text
authenticated subject
session
token claims
```

được đưa vào PolicyContext.

---

# 276. Credential integration

638:

```text
credential state
identity generation
trust revision
```

---

# 277. Config integration

637:

```text
dynamic operational values
policy targeting
```

nhưng 639 vẫn áp dụng hard constraints.

---

# 278. Storage integration

628:

```text
policy registry
revision history
```

có thể persistent.

---

# 279. Package integration

625:

```text
policy bundle distribution
```

---

# 280. Security integration

603:

```text
policy management capabilities
policy evaluation access
```

---

# 281. Minimal runtime architecture

Ứng dụng local chỉ cần:

```text
PolicySnapshot
PolicyEvaluator
```

không cần:

```text
registry
distributed transport
control plane
```

---

# 282. Full runtime

Full profile:

```text
Registry
Compiler
Evaluator
Watch
Rollout
Admission
Governance
Audit
Simulation
Federation
```

---

# 283. Performance architecture

```text
              ┌──────────────┐
              │ Immutable    │
              │ PolicySnapshot│
              └──────┬───────┘
                     │
              ┌──────▼───────┐
              │ Compiled     │
              │ Decision DAG │
              └──────┬───────┘
                     │
             ┌───────▼────────┐
             │ Local Evaluator │
             └────────────────┘
```

Read path không cần distributed lock.

---

# 284. Compilation cache

Compiled policy cache key:

```text
policy_fingerprint
compiler_version
target
architecture
```

---

# 285. Persistent compiled policy

Có thể cache:

```text
.axpolc
```

nhưng binary phải validate fingerprint trước khi sử dụng.

---

# 286. Cache invalidation

Compiler version change:

```text
invalidate
```

Policy semantics version change:

```text
invalidate
```

---

# 287. Binary security

Compiled policy phải được verify:

```text
source fingerprint
compiler fingerprint
schema fingerprint
signature
```

---

# 288. Policy compiler trust

Policy compiler không được tự grant capabilities.

---

# 289. Runtime safety

Malformed compiled policy:

```text
reject
```

không fallback sang unsafe execution.

---

# 290. Policy sandbox

Nếu future user-defined policy extension tồn tại:

```text
sandboxed
capability-limited
bounded
```

nhưng không phải core requirement.

---

# 291. Future extension boundary

Có thể hỗ trợ:

```text
OPA-like provider
WASM policy provider
external policy service
```

nhưng chỉ qua provider interface.

---

# 292. External policy provider

```text
ExternalPolicyProvider {
    evaluate
    publish
    validate
}
```

---

# 293. External provider trust

External decision không tự động được trust.

Caller policy phải xác định:

```text
trusted provider
required signature
required revision
```

---

# 294. External outage

Fallback:

```text
last known good
static policy
deny
```

theo policy.

---

# 295. No mandatory external dependency

Core Axiom policy runtime phải hoạt động mà không cần:

```text
OPA
Kyverno
Open Policy Agent
Kubernetes
Envoy
cloud policy service
```

---

# 296. Final invariants

Ngoài 60 invariant cốt lõi ở trên, implementation phải giữ:

61. Policy parser không thực thi code.
62. Policy evaluator không thực hiện I/O.
63. Policy evaluation có bounded complexity.
64. Policy snapshot immutable.
65. Policy history append-only.
66. Policy rollback tạo revision mới.
67. Policy signature covers canonical semantics.
68. Policy compiler fingerprint deterministic.
69. Policy decision provenance luôn xác định revision.
70. Historical evaluation không có side effects.
71. Admission token có expiry.
72. Admission token gắn request fingerprint.
73. Approval không tự cấp capability.
74. Break-glass luôn audit.
75. Exception có expiry.
76. Cross-tenant evaluation bị chặn theo scope.
77. Policy registry không chứa secret plaintext.
78. Decision cache không vượt revision.
79. Stale snapshot semantics explicit.
80. Security default không implicit fail-open.
81. Policy cannot weaken 603.
82. Policy cannot export 638 secret.
83. Policy cannot bypass 610 verification.
84. Policy cannot mutate 635 state directly.
85. Policy cannot perform 636 deployment directly.
86. Policy cannot invoke 629 workflow directly.
87. Policy cannot invoke arbitrary plugin code.
88. Policy import graph phải bounded.
89. Regex evaluation phải bounded nếu tồn tại.
90. Large policy phải có admission limits.
91. Watch queues bounded.
92. Registry writes rate-limited.
93. Rollout concurrency bounded.
94. Policy activation atomic theo declared scope.
95. Partial federation state observable.
96. Global and local revisions distinguishable.
97. Stale publisher fenced.
98. Old policy cannot overwrite newer revision.
99. Same revision cannot represent different content.
100. Effective policy must be explainable.

---

# 297. Acceptance target

Implementation target:

**≥400 acceptance criteria**

trải trên:

- parser;
- type system;
- policy IR;
- compiler;
- optimizer;
- evaluator;
- deterministic semantics;
- cache;
- registry;
- replication;
- watches;
- rollout;
- admission;
- governance;
- authorization;
- capability integration;
- identity;
- credentials;
- resource policies;
- service policies;
- gateway policies;
- deployment policies;
- federation;
- edge;
- audit;
- explain;
- simulation;
- failure handling;
- performance;
- security;
- fuzzing;
- cross-platform support.

---

# 298. Profiles

```text
AXPOLICY_NONE
AXPOLICY_LOCAL
AXPOLICY_AUTH
AXPOLICY_ADMISSION
AXPOLICY_GOVERNANCE
AXPOLICY_DYNAMIC
AXPOLICY_DISTRIBUTED
AXPOLICY_FEDERATION
AXPOLICY_EDGE
AXPOLICY_FULL
```

---

# 299. Profile semantics

### AXPOLICY_NONE

Không policy runtime.

### AXPOLICY_LOCAL

Static local policy evaluator.

### AXPOLICY_AUTH

Authorization policy.

### AXPOLICY_ADMISSION

Admission control.

### AXPOLICY_GOVERNANCE

Guardrails/governance.

### AXPOLICY_DYNAMIC

Dynamic policy snapshots.

### AXPOLICY_DISTRIBUTED

Distributed registry/watch/rollout.

### AXPOLICY_FEDERATION

Global multi-cluster policy.

### AXPOLICY_EDGE

Offline delegated policy.

### AXPOLICY_FULL

Toàn bộ 639.

---

# 300. Final architecture

```text
                              Axiom Application
                                      │
                                      ▼
                         ┌─────────────────────────┐
                         │      639 Policy Plane   │
                         ├─────────────────────────┤
                         │ Policy Registry          │
                         │ Policy Compiler          │
                         │ Policy IR                │
                         │ Policy Evaluator         │
                         │ Decision Cache           │
                         │ Admission Controller     │
                         │ Governance/Guardrails    │
                         │ Simulation               │
                         │ Explain                  │
                         │ Rollout                  │
                         │ Audit                    │
                         └────────────┬────────────┘
                                      │
        ┌──────────────┬──────────────┼──────────────┬──────────────┐
        ▼              ▼              ▼              ▼              ▼
      603            627            637            638            635
   Capability       Identity       Dynamic        Credential      Control
      │              │              Config          Trust          Plane
      └──────────────┴──────────────┴──────────────┴──────────────┘
                                      │
       ┌──────────────┬───────────────┼───────────────┬─────────────┐
       ▼              ▼               ▼               ▼             ▼
      606            631             632             636           634
   Resources        Services        Gateway       Deployment      Events
```

---

# 301. Kiến trúc cuối cùng của 603–639

```text
603 Security / Capability
        │
        ├── 610 Cryptography
        │
        ├── 627 Identity
        │
        └── 638 Credential / Trust
                    │
637 Dynamic Control ─┤
                    ▼
              639 Policy
                    │
       ┌────────────┼─────────────┐
       ▼            ▼             ▼
     631           632           636
   Service        Gateway      Deployment
       │            │             │
       └────────────┼─────────────┘
                    ▼
              635 Control Plane
                    │
              606 Resources
                    │
              633 Telemetry
                    │
              634 Events
```

---

# 302. Kết luận kiến trúc

BOOTSTRAP-639 hoàn thành **policy plane** cho Axiom.

Axiom hiện có sự phân tách rõ:

```text
603  = Authority
610  = Cryptography
627  = Identity
637  = Dynamic Control
638  = Credential/Trust Lifecycle
639  = Policy Decision
635  = Distributed Coordination
636  = Deployment Intent
606  = Resource Enforcement
631  = Service Execution
632  = Edge Execution
633  = Observation
634  = Event Transport
```

Nguyên tắc quan trọng nhất:

> **Policy có thể quyết định một operation được phép hay không, nhưng policy không tự tạo authority.**

Điều này ngăn một lỗi kiến trúc phổ biến ở các hệ thống distributed:

```text
remote config
    ↓
changes policy
    ↓
policy grants privilege
    ↓
privilege grants capability
```

Axiom phải chặn chuỗi này.

Chuỗi đúng:

```text
Authority
   ↓
Capability
   ↓
Identity
   ↓
Policy
   ↓
Decision
   ↓
Enforcement
```

Dynamic configuration chỉ điều chỉnh behavior trong những giới hạn mà security architecture đã cho phép.

---

# 303. Trạng thái

**BOOTSTRAP-639 = COMPLETE**

Đã hoàn thành:

- declarative policy model;
- authorization;
- policy evaluation;
- policy compiler/IR;
- deterministic evaluation;
- admission control;
- governance;
- guardrails;
- policy registry;
- distributed policy;
- policy rollout;
- canary/wave;
- policy versioning;
- revision history;
- rollback;
- policy signatures;
- policy simulation;
- policy explanation;
- decision caching;
- stale-policy handling;
- fail-open/fail-closed semantics;
- multi-tenant policy;
- federation;
- edge/offline policy;
- credential/identity integration;
- capability integration;
- resource governance;
- deployment admission;
- service/gateway admission;
- audit;
- telemetry;
- security boundaries;
- compiler integration;
- AI-readable metadata;
- ≥400 acceptance-criteria target.

**Task tiếp theo: BOOTSTRAP-640 — Native Distributed Data Governance, Data Classification, Data Lineage, Access Control, Residency, Retention, Privacy, Transformation Policy & Data Lifecycle Runtime 5.0.**
:::