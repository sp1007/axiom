BOOTSTRAP-665 tiếp tục từ 664, nhưng tách riêng **human oversight/control** khỏi safety enforcement: 664 quyết định runtime có an toàn/được phép hay không; 665 định nghĩa **khi nào con người phải tham gia, họ có quyền gì, can thiệp ra sao, chuyển quyền kiểm soát thế nào và hệ thống phải xử lý consent/approval/escalation như thế nào**.

:::writing{variant="document" id="73146" title="AXIOM BOOTSTRAP-665 — Native AI Human Oversight, Human-in-the-Loop, Approval, Intervention, Escalation, Consent & Collaborative Control Runtime 5.0"}
# BOOTSTRAP-665
## Native AI Human Oversight, Human-in-the-Loop, Approval, Intervention, Escalation, Consent & Collaborative Control Runtime 5.0

**Status:** COMPLETE  
**Layer:** Native AI Human Oversight & Control  
**Predecessor:** BOOTSTRAP-664 — Safety, Alignment & Runtime Guardrails  
**Primary dependencies:** 603, 605, 607, 608, 620, 623, 627, 633, 639, 640, 644, 646, 647, 650, 651, 657, 658, 659, 660, 661, 663, 664  
**Target acceptance:** ≥ 2,500 tests

---

# 1. Mục tiêu

BOOTSTRAP-665 cung cấp lớp điều khiển giữa:

```text
AI / Agent
    │
    ▼
Decision
    │
    ▼
Safety Enforcement (664)
    │
    ▼
Human Oversight (665)
    │
    ▼
Execution
```

Nó định nghĩa:

- human-in-the-loop;
- human-on-the-loop;
- human-out-of-the-loop;
- approval;
- confirmation;
- consent;
- intervention;
- escalation;
- delegation;
- control transfer;
- authority transfer;
- human veto;
- emergency intervention;
- supervision;
- review;
- exception handling;
- multi-human approval;
- separation of duties;
- quorum;
- timeout;
- stale approval;
- approval revocation;
- human availability;
- fallback khi không có người;
- collaborative human-AI control;
- operator workload;
- intervention quality;
- human decision provenance.

---

# 2. Nguyên tắc nền tảng

665 không biến con người thành một "guardrail boolean".

Một human decision có thể là:

```text
approve
deny
modify
defer
request_more_information
escalate
take_control
release_control
cancel
```

---

# 3. Phân biệt 664 và 665

```text
664:
"Action này có an toàn và hợp lệ để thực hiện không?"

665:
"Con người có cần tham gia không, ai có quyền tham gia,
tham gia ở thời điểm nào, và quyền kiểm soát được chuyển thế nào?"
```

---

# 4. Human oversight modes

Axiom hỗ trợ bốn mode chuẩn:

```text
AUTONOMOUS
HUMAN_ON_LOOP
HUMAN_IN_LOOP
HUMAN_CONTROLLED
```

---

# 5. AUTONOMOUS

AI có thể thực hiện action mà không cần human approval riêng cho từng action.

Nhưng vẫn chịu:

```text
603 capability
639 policy
664 safety
```

---

# 6. HUMAN_ON_LOOP

AI thực hiện theo policy đã được phê duyệt.

Human:

```text
monitor
review
intervene
stop
```

nhưng không cần approve từng action.

---

# 7. HUMAN_IN_LOOP

AI tạo proposal.

Human phải:

```text
approve
deny
modify
```

trước execution.

---

# 8. HUMAN_CONTROLLED

Human giữ execution authority.

AI chỉ:

```text
suggest
simulate
predict
assist
```

Không tự commit action.

---

# 9. OversightPolicy

```axiom
struct OversightPolicy {
    id: OversightPolicyId
    revision: Version
    mode: OversightMode
    approval: ApprovalPolicy
    escalation: EscalationPolicy
    intervention: InterventionPolicy
    consent: ConsentPolicy
    timeout: TimeoutPolicy
}
```

---

# 10. OversightContext

```axiom
struct OversightContext {
    actor
    human_roles
    active_policy
    current_mode
    pending_actions
    pending_approvals
    incidents
    availability
    workload
}
```

---

# 11. HumanActor

```axiom
struct HumanActor {
    id: HumanId
    identity: IdentityRef
    roles: Role[]
    authorities: Authority[]
    availability: Availability
    session: SessionRef
}
```

Identity và authority phải tách biệt.

---

# 12. Human role

Ví dụ:

```text
Operator
Reviewer
Approver
Supervisor
Administrator
SafetyOfficer
DomainExpert
IncidentCommander
Observer
```

Role không tự động đồng nghĩa authority.

---

# 13. Authority

```axiom
struct HumanAuthority {
    scope
    actions
    resources
    environments
    expiration
    conditions
}
```

---

# 14. Authority scope

Authority có thể giới hạn theo:

```text
action
resource
project
tenant
environment
time
risk
data
system
```

---

# 15. Least authority

Human chỉ được approve trong scope của authority.

---

# 16. Approval

```axiom
struct ApprovalRequest {
    id
    action
    requester
    required_authority
    risk
    deadline
    evidence
    context
}
```

---

# 17. ApprovalDecision

```axiom
enum ApprovalDecision {
    Approve
    Deny
    Modify
    Defer
    Escalate
    Cancel
}
```

---

# 18. Approval ≠ capability

Human approve không cấp capability mới.

Nếu 603 không cấp capability:

```text
approval = true
capability = false
```

→ vẫn DENY.

---

# 19. Approval ≠ safety override

Approval không tự động bypass 664 hard safety constraints.

---

# 20. Approval token

```axiom
struct ApprovalToken {
    request
    approver
    authority
    scope
    policy_revision
    safety_revision
    expiration
    nonce
}
```

---

# 21. Approval expiration

Approval phải có thể expire.

Không dùng approval vô thời hạn nếu action context thay đổi.

---

# 22. Approval invalidation

Approval phải invalid nếu:

```text
policy changes
action changes
risk changes beyond threshold
environment changes
authority expires
model changes
target changes
```

theo policy.

---

# 23. Stale approval

```text
approval exists
+
context changed
=
approval may be stale
```

665 phải kiểm tra freshness.

---

# 24. Re-approval

Nếu action thay đổi materially:

```text
old approval
→ invalidate
→ new approval
```

---

# 25. Material change

Policy có thể định nghĩa:

```text
argument change
target change
scope change
risk change
resource change
model change
```

---

# 26. Human confirmation

Confirmation là một dạng approval nhẹ hơn.

```axiom
struct ConfirmationRequest {
    action
    summary
    risk_summary
    expiration
}
```

---

# 27. Consent

Consent khác approval.

```text
Consent:
"đồng ý cho hệ thống xử lý/perform trong phạm vi X"

Approval:
"cho phép action Y ngay bây giờ"
```

---

# 28. ConsentRecord

```axiom
struct ConsentRecord {
    subject
    purpose
    scope
    granted_at
    expires_at
    revocable
    provenance
}
```

---

# 29. Consent không phải authority

Consent của một người không tự cấp quyền trên tài sản/resource thuộc authority của người khác.

---

# 30. Consent revocation

```axiom
consent.revoke(scope)
```

Phải có effect semantics rõ:

```text
future actions
pending actions
active actions
stored data
```

---

# 31. Consent withdrawal

Nếu policy yêu cầu, pending action phải bị:

```text
cancelled
```

---

# 32. Human intervention

```axiom
struct Intervention {
    id
    human
    target
    operation
    reason
    authority
    timestamp
}
```

---

# 33. Intervention types

```text
Pause
Resume
Cancel
Modify
Abort
TakeControl
ReleaseControl
Restrict
Escalate
Rollback
SafeMode
```

---

# 34. Intervention priority

Một intervention không tự override safety/security boundaries.

---

# 35. TakeControl

```axiom
take_control(system)
```

chuyển execution authority theo policy.

---

# 36. Control transfer

```text
AI
 ↓
Human
 ↓
AI
```

phải có state transition explicit.

---

# 37. ControlToken

```axiom
struct ControlToken {
    holder
    scope
    issued_at
    expires_at
    transfer_policy
}
```

---

# 38. Single-controller mode

Có thể yêu cầu:

```text
exactly one controller
```

trong một execution domain.

---

# 39. Shared control

Có thể cho:

```text
AI + Human
```

đồng thời điều khiển nhưng action ownership phải explicit.

---

# 40. Authority split

Một system có thể tách:

```text
AI: navigation
Human: final commit
```

---

# 41. Collaborative control

```axiom
struct ControlPolicy {
    human_actions
    ai_actions
    shared_actions
    conflict_resolution
}
```

---

# 42. Human veto

```axiom
@human_veto
action
```

Human có thể deny trong authority scope.

---

# 43. Veto semantics

Veto có thể:

```text
current action
current workflow
current session
future actions
```

scope phải explicit.

---

# 44. Veto ≠ emergency stop

Veto là policy-level intervention.

Emergency stop là safety-level mechanism.

---

# 45. Emergency intervention

665 tích hợp 664:

```text
Human
 ↓
Emergency intervention
 ↓
664 EmergencyStop
```

---

# 46. Escalation

Khi AI không đủ authority:

```text
AI
 ↓
Supervisor
 ↓
Domain Expert
 ↓
Emergency Authority
```

---

# 47. EscalationPolicy

```axiom
struct EscalationPolicy {
    triggers
    levels
    authorities
    deadlines
    fallback
}
```

---

# 48. Escalation trigger

Ví dụ:

```text
risk > threshold
uncertainty > threshold
policy conflict
unknown state
human disagreement
system failure
irreversible action
```

---

# 49. Escalation deadline

Mỗi escalation có deadline.

---

# 50. Escalation timeout

Timeout không mặc định là approval.

Policy phải quy định:

```text
deny
hold
safe mode
fallback
escalate further
```

---

# 51. Escalation storm

Phải chống:

```text
AI → Human A
Human A → Human B
Human B → AI
AI → Human A
```

vòng lặp vô hạn.

---

# 52. Escalation graph

```axiom
struct EscalationGraph {
    nodes
    edges
    terminal_states
}
```

Compiler/runtime có thể phát hiện cycle không hợp lệ.

---

# 53. Human availability

```axiom
enum Availability {
    Available
    Busy
    Offline
    Unreachable
    Unknown
}
```

---

# 54. No-human fallback

Nếu human unavailable:

```text
policy-defined fallback
```

Không tự assume:

```text
continue
```

---

# 55. Availability-aware autonomy

Policy có thể:

```text
human available → HITL
human unavailable → safe autonomous subset
```

---

# 56. Autonomy envelope

```axiom
struct AutonomyEnvelope {
    allowed_actions
    risk_limit
    duration
    resources
    environment
}
```

---

# 57. Temporary autonomy

Human có thể cấp autonomy:

```text
for action set X
for duration T
```

---

# 58. Autonomy expiration

Khi hết hạn:

```text
return control
```

hoặc:

```text
safe state
```

---

# 59. Delegation

Human có thể delegate authority cho:

```text
AI
another human
agent
service
```

---

# 60. Delegation record

```axiom
struct Delegation {
    delegator
    delegate
    authority
    scope
    start
    expiry
    revocation
}
```

---

# 61. No privilege escalation

Delegate không thể cấp quyền cao hơn quyền của delegator.

---

# 62. Delegation chain

```text
Human A
 → Human B
 → Agent C
```

effective authority không được vượt authority root.

---

# 63. Delegation depth

Policy có thể giới hạn:

```text
max_depth
```

---

# 64. Revocation propagation

Revoking parent delegation phải invalidate descendant delegations khi policy yêu cầu.

---

# 65. Separation of duties

Một action có thể yêu cầu:

```text
requester != approver
```

---

# 66. Dual approval

```axiom
@dual_approval
```

yêu cầu hai authority độc lập.

---

# 67. Quorum approval

```axiom
struct ApprovalQuorum {
    required
    eligible
    independence_rule
}
```

---

# 68. Independence

Hai approvals từ cùng một authority chain có thể không được coi là independent.

---

# 69. Multi-party approval

Có thể yêu cầu:

```text
2 of 3
3 of 5
all required roles
```

---

# 70. Approval aggregation

Runtime phải tránh race:

```text
approve
approve
approve
```

duplicate không tạo thêm authority.

---

# 71. Approval conflict

Nếu:

```text
A = approve
B = deny
```

policy phải định nghĩa:

```text
deny-wins
quorum
role priority
escalate
```

---

# 72. No hidden majority rule

Không tự dùng majority nếu policy chưa định nghĩa.

---

# 73. Human disagreement

Disagreement là state có thể query:

```axiom
ApprovalConflict
```

---

# 74. Review

Human có thể request:

```text
more_evidence
simulation
explanation
alternative_plan
risk_analysis
```

---

# 75. Evidence package

Approval UI/runtime phải có structured evidence:

```text
action
goal
risk
constraints
policy
model
expected effects
uncertainty
alternatives
```

---

# 76. No hidden chain-of-thought

665 không yêu cầu AI expose private reasoning.

Thay vào đó dùng:

```text
DecisionExplanation
Evidence
RiskSummary
ConstraintSummary
```

---

# 77. Explanation fidelity

Explanation phải phân biệt:

```text
observed
predicted
inferred
assumed
unknown
```

---

# 78. Human-readable summary

Có thể generate:

```text
What will happen?
Why?
What could go wrong?
What constraints apply?
What can be reversed?
What authority is required?
```

---

# 79. Machine-readable approval

UI chỉ là một interface.

Approval phải có canonical runtime record.

---

# 80. Approval provenance

Record:

```text
who
what
when
where
under which authority
under which policy
```

---

# 81. Approval authentication

Critical approval phải authenticated.

---

# 82. Approval integrity

Approval token phải có integrity protection khi required.

---

# 83. Replay protection

Approval token không được replay ngoài scope.

---

# 84. Nonce

Approval request/token có nonce.

---

# 85. Session binding

Critical approval có thể bind với session.

---

# 86. Device binding

Policy có thể yêu cầu approval từ registered device.

---

# 87. Biometric boundary

Axiom không định nghĩa biometric algorithm trong 665.

Nó chỉ cung cấp:

```text
IdentityProof
```

interface.

---

# 88. Accessibility

Human oversight UI phải hỗ trợ:

```text
keyboard
screen reader
high contrast
large text
alternative input
```

theo UI layer 619.

---

# 89. Notification

665 tích hợp 617/618/619 để gửi:

```text
approval request
alert
escalation
incident
```

---

# 90. Notification ≠ approval

Đã gửi notification không có nghĩa human đã xem.

---

# 91. Acknowledgement

```axiom
struct Acknowledgement {
    recipient
    event
    timestamp
}
```

---

# 92. Read ≠ approve

Các trạng thái:

```text
Delivered
Seen
Acknowledged
Approved
Denied
```

phải khác nhau.

---

# 93. Human attention

Có thể record:

```text
request_presented
request_seen
request_opened
decision_made
```

nhưng không được suy diễn rằng "seen = understood".

---

# 94. Operator workload

```axiom
struct HumanWorkload {
    pending_count
    urgency
    estimated_effort
    active_interventions
}
```

---

# 95. Workload-aware escalation

Nếu human quá tải:

```text
alternate reviewer
defer
safe fallback
```

theo policy.

---

# 96. No automatic authority expansion

Workload không tự cấp thêm quyền cho human khác.

---

# 97. Fatigue signal

Có thể lưu workload/availability.

Không được dùng để suy đoán trạng thái sức khỏe hoặc năng lực của một người.

---

# 98. Intervention latency

Metrics:

```text
time_to_notify
time_to_ack
time_to_decide
time_to_intervene
time_to_recover
```

---

# 99. Human response SLA

Policy có thể định nghĩa:

```text
response_deadline
```

---

# 100. Safe timeout

Nếu không phản hồi:

```text
safe fallback
```

theo policy.

---

# 101. Continuous supervision

Human-on-loop có:

```text
monitor
alert
intervene
```

---

# 102. Sampling supervision

Không nhất thiết human xem mọi action.

Policy có thể định nghĩa:

```text
random sampling
risk-based sampling
periodic review
anomaly-triggered review
```

---

# 103. Risk-based review

Risk cao → review frequency cao hơn.

---

# 104. Review queue

```axiom
struct OversightQueue {
    requests
    priority
    deadlines
    assigned_reviewers
}
```

---

# 105. Priority

Priority phải policy-defined.

Không dùng AI utility trực tiếp để thay priority governance.

---

# 106. Queue fairness

Có thể hỗ trợ:

```text
FIFO
deadline
risk
weighted
role-specific
```

---

# 107. Starvation prevention

Review queue phải có starvation policy.

---

# 108. Human escalation fairness

Một request không nên bị giữ vô hạn vì queue priority.

---

# 109. Approval batching

Có thể batch các action:

```text
same policy
same scope
same risk class
```

nhưng batch approval phải explicit.

---

# 110. Batch approval

```axiom
struct BatchApproval {
    action_set
    scope
    constraints
    expiration
}
```

---

# 111. Batch approval safety

Một action thay đổi vượt batch scope phải re-approve.

---

# 112. Consent batch

Consent cũng có thể scope theo:

```text
purpose
resource
duration
```

---

# 113. Consent purpose limitation

Consent cho purpose A không tự cấp purpose B.

---

# 114. Consent versioning

Consent policy changes có thể require re-consent.

---

# 115. Withdrawal propagation

Consent revoke phải propagate tới dependent workflows.

---

# 116. Human data minimization

Approval interface chỉ expose data cần thiết.

---

# 117. Sensitive evidence

Evidence có classification.

---

# 118. Evidence redaction

Human reviewer chỉ xem được evidence trong authority scope.

---

# 119. Cross-tenant oversight

Reviewer tenant A không tự thấy request tenant B.

---

# 120. Oversight isolation

Multi-tenant oversight phải enforce tenant boundary.

---

# 121. Human identity lifecycle

Khi identity revoked:

```text
pending approvals
delegations
control tokens
```

phải được policy xử lý.

---

# 122. Role revocation

Role revoked → relevant authority invalid.

---

# 123. Session termination

Session termination phải invalidate session-bound approval/control tokens.

---

# 124. Emergency authority

Emergency role có scope riêng.

Không mặc định có full system access.

---

# 125. Emergency escalation

Có thể:

```text
operator
→ supervisor
→ emergency authority
```

---

# 126. Emergency approval

Emergency mode có thể rút ngắn workflow nhưng vẫn phải:

```text
authenticated
scoped
audited
```

---

# 127. Emergency retrospective

Sau emergency action:

```text
post_incident_review
```

có thể bắt buộc.

---

# 128. Intervention audit

Mọi:

```text
take_control
release_control
modify
override
approve
deny
```

đều phải audit theo policy.

---

# 129. Human action trace

Trace:

```text
human request
→ AI proposal
→ human decision
→ safety check
→ execution
```

---

# 130. AI action trace

Ngược lại:

```text
AI proposal
→ human request
→ human approval
→ execution
```

---

# 131. Provenance graph

```axiom
struct OversightProvenance {
    request
    actor
    authority
    policy
    evidence
    decision
    execution
}
```

---

# 132. Decision attribution

Hệ thống phải phân biệt:

```text
AI proposed
Human approved
System executed
```

không ghi chung thành:

```text
Human did action
```

---

# 133. Shared responsibility

Collaborative execution có thể có nhiều actors.

Attribution phải granular.

---

# 134. Human modification

Nếu human sửa AI action:

```text
AIProposal
→ HumanModifiedAction
```

không ghi action cuối là AI-generated nguyên bản.

---

# 135. Human-generated action

Human có thể tạo action trực tiếp.

Vẫn phải qua:

```text
603
639
664
```

khi applicable.

---

# 136. Human cannot bypass safety

Human-originated action không tự động bypass 664.

---

# 137. AI cannot impersonate human

AI không được tạo:

```text
HumanApproval
```

nếu không có authenticated human action.

---

# 138. Synthetic approval

Test environment có thể dùng synthetic approvals nhưng metadata phải:

```text
synthetic = true
```

---

# 139. Production synthetic approval

Không được coi synthetic approval là real human approval trong strict profile.

---

# 140. Human simulation

648 có thể mô phỏng human.

665 phải distinguish:

```text
simulated_human
real_human
```

---

# 141. Training data

Human approval records có thể trở thành training data nhưng phải qua:

```text
640 privacy
647 governance
662 learning policy
```

---

# 142. Preference learning

Approval history không tự động đồng nghĩa persistent preference.

---

# 143. Human feedback

```axiom
HumanFeedback {
    target
    type
    provenance
    confidence?
}
```

---

# 144. Feedback types

```text
Approve
Reject
Correct
Prefer
Disprefer
Explain
Flag
```

---

# 145. Feedback ≠ policy

Một feedback đơn lẻ không tự thay policy.

---

# 146. Feedback ≠ consent

Feedback không tự tạo legal/operational consent semantics.

---

# 147. Feedback → learning

662 có thể sử dụng feedback nếu policy cho phép.

---

# 148. Human correction

Human có thể sửa:

```text
plan
parameters
target
constraints
```

AI phải revalidate.

---

# 149. Replanning

Human modification có thể trigger:

```text
re-plan
re-evaluate
re-approve
```

---

# 150. Plan lock

Human có thể lock một phần plan:

```axiom
@human_locked
```

AI không được sửa phần đó.

---

# 151. Constraint injection

Human có thể thêm temporary constraint:

```axiom
@human_constraint
```

nhưng phải nằm trong authority scope.

---

# 152. Constraint removal

Removing safety constraint requires policy-defined authority.

---

# 153. Temporary policy

Human có thể tạo temporary operational policy nếu authority cho phép.

---

# 154. Policy expiration

Temporary policy phải có expiration.

---

# 155. No permanent accidental override

Temporary override không được persist indefinitely.

---

# 156. Control handoff

```axiom
handoff(from, to)
```

phải atomic nếu system yêu cầu.

---

# 157. Handoff states

```text
Requested
Accepted
Transferred
Rejected
Expired
Failed
```

---

# 158. Handoff failure

Nếu target human không nhận control:

```text
fallback
```

---

# 159. Handoff confirmation

Sender không được release control trước khi policy-required receiver acknowledgement.

---

# 160. Dual control

Có thể:

```text
Human A holds control
Human B authorizes
AI executes
```

---

# 161. Triple-role separation

Critical workflow có thể:

```text
Requester
Approver
Executor
```

là ba entities khác nhau.

---

# 162. Conflict-of-interest rule

Policy có thể cấm cùng một actor giữ nhiều role.

---

# 163. Role conflict

Compiler/runtime phải detect nếu impossible assignment.

---

# 164. Human availability failover

Nếu primary unavailable:

```text
secondary
→ tertiary
→ safe fallback
```

---

# 165. Escalation tree

```axiom
struct EscalationTree {
    primary
    alternates
    emergency
    terminal_fallback
}
```

---

# 166. Human authority discovery

Runtime có thể query:

```axiom
oversight.find_authority(action)
```

---

# 167. Authority matching

Match theo:

```text
action
scope
resource
risk
role
time
```

---

# 168. Approval routing

```axiom
oversight.route(request)
```

---

# 169. Routing policy

Có thể chọn:

```text
role
expertise
availability
authority
workload
```

nhưng routing không được thay authority.

---

# 170. Expertise metadata

Reviewer có thể có declared expertise.

Không được suy diễn expertise từ protected/sensitive personal characteristics.

---

# 171. Domain expert requirement

Policy có thể yêu cầu:

```text
required_role = DomainExpert
```

---

# 172. Expert disagreement

Disagreement → escalation policy.

---

# 173. Consensus

Có thể yêu cầu consensus nhưng phải define:

```text
unanimity
quorum
weighted authority
```

---

# 174. Weighted approval

Nếu dùng weighted authority:

```text
weight
```

phải policy-defined và auditable.

---

# 175. No hidden influence score

Không có implicit:

```text
AI thinks human A is better
→ gives A more authority
```

nếu policy không khai báo.

---

# 176. Human trust model

Có thể có:

```axiom
TrustPolicy
```

nhưng trust score không tự cấp capability.

---

# 177. Trust revision

Trust model phải versioned.

---

# 178. Trust cannot override hard constraints

---

# 179. Human reliability feedback

System có thể measure process metrics:

```text
response_time
approval_rate
reversal_rate
```

nhưng không suy diễn về mental/health attributes.

---

# 180. Oversight quality

Metrics:

```text
approval_latency
intervention_latency
escalation_rate
override_rate
review_coverage
stale_approval_rate
```

---

# 181. Intervention effectiveness

663 có thể evaluate:

```text
did intervention reduce risk?
did intervention prevent violation?
```

---

# 182. Human error resilience

665 phải hỗ trợ:

```text
confirmation
preview
undo
rollback
second approval
```

khi policy yêu cầu.

---

# 183. Confirmation design

Critical irreversible actions có thể require:

```text
explicit action summary
scope
target
impact
```

trước confirmation.

---

# 184. Anti-accidental approval

Policy có thể yêu cầu:

```text
explicit affirmative action
```

Không coi:

```text
timeout
notification
screen_open
```

là approval.

---

# 185. Double confirmation

Critical actions có thể require two-stage confirmation.

---

# 186. Confirmation freshness

Nếu action context thay đổi materially:

```text
confirmation invalid
```

---

# 187. Preview

```axiom
oversight.preview(action)
```

trả:

```text
expected_effects
risk
constraints
reversibility
```

---

# 188. Dry run

```axiom
oversight.dry_run(action)
```

không side effect.

---

# 189. Human simulation

UI có thể show:

```text
before
after
```

nhưng prediction phải marked as predicted.

---

# 190. Counterfactual support

Human có thể yêu cầu:

```text
what if approve?
what if deny?
what if modify?
```

Kết quả là simulation, không guarantee.

---

# 191. Alternative actions

Approval UI có thể present:

```text
A
B
C
```

nhưng system không được rank alternatives as "best" unless caller explicitly requests an optimization algorithm; even then ranking is machine-generated decision support, not human authority.

---

# 192. Human final decision

Human authority remains separate from AI recommendation.

---

# 193. Cognitive load protection

Large action sets có thể:

```text
group
summarize
filter
```

nhưng summary phải preserve material risk/constraint information.

---

# 194. Summary integrity

Không được hide critical safety constraint chỉ vì UI simplification.

---

# 195. Progressive disclosure

Có thể:

```text
summary
→ details
→ evidence
```

---

# 196. Alert severity

```text
Info
Warning
High
Critical
Emergency
```

---

# 197. Alert storm suppression

Có:

```text
dedup
aggregation
rate_limit
cooldown
```

---

# 198. Critical alert

Critical alert không được silently suppressed.

---

# 199. Notification redundancy

Critical events có thể require multiple channels.

---

# 200. Notification acknowledgement

Critical events có thể require acknowledgement.

---

# 201. Human oversight IR

```text
OversightContextCreate
OversightPolicyLoad
OversightModeSet

ApprovalRequestCreate
ApprovalRoute
ApprovalPresent
ApprovalAcknowledge
ApprovalApprove
ApprovalDeny
ApprovalModify
ApprovalDefer
ApprovalEscalate
ApprovalExpire
ApprovalRevoke
ApprovalValidate

ConsentCreate
ConsentValidate
ConsentRevoke
ConsentExpire

HumanInterventionCreate
HumanIntervene
HumanCancel
HumanModify
HumanAbort

ControlRequest
ControlGrant
ControlTransfer
ControlRelease
ControlRevoke

DelegationCreate
DelegationValidate
DelegationRevoke

EscalationStart
EscalationRoute
EscalationAcknowledge
EscalationResolve

QuorumCreate
QuorumEvaluate

HumanFeedbackRecord
HumanCorrection
HumanConstraintAdd

OversightPreview
OversightDryRun
OversightExplain

SafeFallback
HumanUnavailable

OversightAudit
OversightTrace
```

---

# 202. Compiler annotations

```text
@oversight
@human_in_loop
@human_on_loop
@human_controlled
@autonomous
@approval_required
@confirmation_required
@consent_required
@human_veto
@human_intervention
@take_control
@release_control
@control_transfer
@delegation
@dual_approval
@quorum
@separation_of_duties
@escalation
@human_authority
@temporary_authority
@approval_timeout
@approval_expiry
@approval_revalidation
@human_constraint
@human_locked
@human_feedback
@human_correction
@human_review
@human_expert
@emergency_intervention
@synthetic_approval
@simulation_human
@oversight_audit
@oversight_trace
```

---

# 203. Metadata

```text
.axoversight
.axhuman
.axapproval
.axconsent
.axintervention
.axcontrol
.axhandoff
.axdelegation
.axauthority
.axescalation
.axquorum
.axreview
.axfeedback
.axcorrection
.axhumanconstraint
.axoversighttrace
.axoversightaudit
.axhumanpolicy
```

---

# 204. Core profiles

```text
AXHUMAN_NONE
AXHUMAN_CORE
AXHUMAN_AUTONOMOUS
AXHUMAN_ON_LOOP
AXHUMAN_IN_LOOP
AXHUMAN_CONTROLLED

AXAPPROVAL_CORE
AXAPPROVAL_REQUIRED
AXAPPROVAL_MULTI
AXAPPROVAL_DUAL
AXAPPROVAL_QUORUM
AXAPPROVAL_EXPIRING
AXAPPROVAL_REVALIDATE

AXCONSENT_CORE
AXCONSENT_REVOCABLE
AXCONSENT_EXPIRING

AXCONTROL_CORE
AXCONTROL_HANDOFF
AXCONTROL_SHARED
AXCONTROL_HUMAN
AXCONTROL_EMERGENCY

AXDELEGATION_CORE
AXDELEGATION_LIMITED
AXDELEGATION_REVOCABLE

AXESCALATION_CORE
AXESCALATION_MULTI
AXESCALATION_EMERGENCY

AXOVERSIGHT_CORE
AXOVERSIGHT_DISTRIBUTED
AXOVERSIGHT_REALTIME
AXOVERSIGHT_AGENT
AXOVERSIGHT_CRITICAL
AXOVERSIGHT_FULL
```

---

# 205. CLI

```text
axiom oversight status
axiom oversight inspect
axiom oversight policy
axiom oversight mode

axiom approval list
axiom approval inspect
axiom approval request
axiom approval approve
axiom approval deny
axiom approval modify
axiom approval defer
axiom approval revoke
axiom approval expire

axiom consent list
axiom consent inspect
axiom consent grant
axiom consent revoke

axiom control status
axiom control request
axiom control take
axiom control release
axiom control transfer

axiom delegation list
axiom delegation inspect
axiom delegation grant
axiom delegation revoke

axiom escalation status
axiom escalation inspect
axiom escalation escalate
axiom escalation resolve

axiom intervention list
axiom intervention inspect
axiom intervention execute

axiom oversight preview
axiom oversight dry-run
axiom oversight explain

axiom oversight audit
axiom oversight trace
axiom oversight benchmark
```

---

# 206. Core API

```axiom
oversight.mode()
oversight.policy()

oversight.request(action)
oversight.approve(request)
oversight.deny(request)
oversight.modify(request, action)
oversight.defer(request)
oversight.escalate(request)

oversight.require_consent(scope)
oversight.revoke_consent(scope)

oversight.take_control(scope)
oversight.release_control(scope)
oversight.transfer_control(target)

oversight.delegate(authority, target)
oversight.revoke_delegation(id)

oversight.intervene(action)
oversight.cancel(action)

oversight.preview(action)
oversight.dry_run(action)

oversight.status()
oversight.trace(id)
```

---

# 207. Approval state machine

```text
CREATED
   ↓
ROUTED
   ↓
PRESENTED
   ↓
ACKNOWLEDGED
   ├── APPROVED
   ├── DENIED
   ├── MODIFIED
   ├── DEFERRED
   ├── ESCALATED
   └── EXPIRED
```

Modified action:

```text
MODIFIED
   ↓
REVALIDATE
   ↓
PRESENTED
```

---

# 208. Control state machine

```text
UNCONTROLLED
    ↓
CONTROL_REQUESTED
    ↓
CONTROL_GRANTED
    ↓
ACTIVE
    ├── TRANSFER_REQUESTED
    ├── RELEASE_REQUESTED
    ├── REVOKED
    └── EXPIRED
```

---

# 209. Delegation state machine

```text
PROPOSED
   ↓
AUTHORIZED
   ↓
ACTIVE
   ├── EXPIRED
   ├── REVOKED
   └── COMPLETED
```

---

# 210. Escalation state machine

```text
TRIGGERED
   ↓
ROUTED
   ↓
ACKNOWLEDGED
   ↓
UNDER_REVIEW
   ├── RESOLVED
   ├── ESCALATED
   └── FALLBACK
```

---

# 211. Oversight pipeline

Canonical pipeline:

```text
ActionProposal
      ↓
664 SafetyCheck
      ↓
OversightPolicy
      ↓
Is Human Required?
      │
   ┌──┴───┐
   │      │
  NO     YES
   │      │
   │   Route Human
   │      │
   │   Authenticate
   │      │
   │   Check Authority
   │      │
   │   Present Evidence
   │      │
   │   Human Decision
   │      │
   │   Revalidate
   │      │
   └───┬──┘
       ↓
664 Final Safety Check
       ↓
603 Capability Check
       ↓
639 Policy Check
       ↓
Execute
```

---

# 212. Final safety rule

Human approval không được bypass final 664 check.

Điều này ngăn:

```text
Human approved
→ environment changed
→ unsafe action
→ execution anyway
```

---

# 213. Human authority rule

Authority phải được kiểm tra:

```text
at request
at approval
at commit
```

nếu policy yêu cầu.

---

# 214. Human control rule

Nếu HUMAN_CONTROLLED:

```text
AI proposal ≠ execution authority
```

---

# 215. Autonomous mode rule

AUTONOMOUS không có nghĩa:

```text
no safety
no policy
no capability
```

Nó chỉ có nghĩa:

```text
no per-action human approval
```

---

# 216. Consent rule

Consent không được dùng như:

```text
capability
authorization
safety override
```

---

# 217. Delegation rule

Delegation không được vượt quyền delegator.

---

# 218. Escalation rule

Escalation không được biến:

```text
unknown
```

thành:

```text
approved
```

---

# 219. Timeout rule

Timeout không được tự động đồng nghĩa approval.

---

# 220. Modification rule

Human modification phải re-run:

```text
663 relevant evaluation
664 safety
603 capability
639 policy
```

khi semantics yêu cầu.

---

# 221. Approval provenance rule

Approval phải biết:

```text
who
under which authority
for what
under which policy
when
until when
```

---

# 222. Attribution rule

Axiom phải phân biệt:

```text
proposed_by
approved_by
executed_by
supervised_by
```

---

# 223. No impersonation rule

AI không thể tạo authenticated human approval.

---

# 224. Synthetic test rule

Synthetic human actions phải được đánh dấu.

---

# 225. Audit rule

Critical oversight actions phải traceable.

---

# 226. Privacy rule

Oversight records phải tuân theo 640.

---

# 227. Security rule

Human identity/authentication phải đi qua 627/603.

---

# 228. Governance rule

Oversight policy lifecycle phải qua 647.

---

# 229. Safety rule

Safety enforcement vẫn thuộc 664.

---

# 230. Evaluation rule

Oversight effectiveness được 663 đánh giá.

---

# 231. Learning rule

Human feedback chỉ trở thành training signal khi 662 policy cho phép.

---

# 232. Memory rule

Oversight history có thể lưu ở 650 nhưng không tự biến thành authority.

---

# 233. Personalization rule

651 có thể cá nhân hóa UI/routing trong allowed scope nhưng không tự thay authority.

---

# 234. Social intelligence boundary

658 có thể hỗ trợ giao tiếp với human.

Không được dùng social inference để cấp authority ngoài policy.

---

# 235. Emotion boundary

659 có thể biểu diễn urgency/affect nhưng không được tự tạo approval authority.

---

# 236. Self-model boundary

660 không được tự quyết định:

```text
"I am now authorized."
```

Authority phải đến từ external policy/authority chain.

---

# 237. Cognitive boundary

657 có thể chọn strategy:

```text
ask_human
continue
defer
```

nhưng action vẫn chịu 665 + 664.

---

# 238. Goal boundary

661 có thể request human approval nhưng không được giả mạo approval.

---

# 239. Distributed oversight

Trong distributed environment:

```text
Human A
Service 1
Agent 2
```

có thể cùng tham gia một workflow.

Oversight provenance phải distributed-traceable.

---

# 240. Cross-node approval

Approval phải có:

```text
issuer
policy_epoch
authority_epoch
timestamp
nonce
```

---

# 241. Stale distributed approval

Nếu node nhận approval từ policy epoch cũ:

```text
revalidate
```

---

# 242. Partition

Nếu approval service unavailable:

```text
policy-defined fallback
```

không tự approve.

---

# 243. Offline human

Có thể hỗ trợ offline signed approvals nếu profile cho phép.

---

# 244. Offline approval freshness

Offline approval phải có expiration và scope.

---

# 245. Clock uncertainty

Distributed approval phải xử lý clock skew.

Không dùng timestamp đơn giản nếu security semantics yêu cầu stronger ordering.

---

# 246. Replay protection

Approval nonce + request identity phải chống replay.

---

# 247. Duplicate approval

Same approval event chỉ được apply một lần.

---

# 248. Event ordering

Critical control events phải có ordering semantics.

---

# 249. Control transfer atomicity

Không được có:

```text
old controller released
new controller not granted
```

nếu policy yêu cầu continuous control.

---

# 250. Failover control

Nếu controller disconnect:

```text
secondary controller
```

hoặc:

```text
safe mode
```

theo policy.

---

# 251. Human oversight benchmark

663 có thể đo:

```text
approval accuracy
intervention effectiveness
time-to-intervention
false escalation
missed escalation
stale approval rate
handoff failures
control recovery time
```

---

# 252. Oversight simulation

648 có thể simulate:

```text
human unavailable
human disagreement
approval timeout
wrong approval
malicious credential
network partition
handoff failure
```

---

# 253. Oversight red-team

646/663 có thể test:

```text
approval replay
authority confusion
role confusion
delegation escalation
UI deception
stale approval
notification spoofing
```

---

# 254. Human-AI adversarial boundary

665 phải defend against:

```text
AI-generated misleading approval context
```

Bằng cách tách:

```text
raw evidence
AI summary
policy evidence
```

---

# 255. Evidence provenance

Mỗi evidence item:

```axiom
struct EvidenceRef {
    source
    type
    timestamp
    revision
    confidence
}
```

---

# 256. AI summary

AI có thể summarize evidence.

Nhưng summary không thay raw evidence trong critical workflows.

---

# 257. Evidence integrity

Critical evidence phải integrity-protected.

---

# 258. Human decision explanation

Có thể lưu:

```text
reason_code
selected_option
notes
```

Không bắt buộc human phải cung cấp hidden/private reasoning.

---

# 259. Reason codes

```text
PolicyRequirement
RiskConcern
InsufficientEvidence
OperationalNeed
SafetyConcern
UserInstruction
Correction
Other
```

---

# 260. Decision notes

Optional, privacy-controlled.

---

# 261. Oversight artifact

Compiler có thể emit:

```text
.axoversight
```

chứa:

```text
oversight graph
approval requirements
authority references
timeouts
escalation paths
```

---

# 262. Static validation

Compiler phải phát hiện:

```text
approval required
but no approver authority
```

nếu statically knowable.

---

# 263. Impossible workflow

Ví dụ:

```text
require 3 approvals
eligible approvers = 2
```

→ compile/configuration error hoặc deployment rejection.

---

# 264. Escalation dead end

Nếu:

```text
all humans unavailable
no fallback
action required
```

strict profile phải reject configuration.

---

# 265. Control deadlock

Compiler/runtime phải detect:

```text
AI waits human
human waits AI
```

nếu workflow graph có thể chứng minh cycle.

---

# 266. Approval deadlock

Multi-party approval phải có timeout/fallback.

---

# 267. Oversight availability invariant

Critical workflow phải có defined:

```text
human_available
human_unavailable
communication_failure
```

semantics.

---

# 268. Safe default

Nếu oversight policy không rõ:

```text
critical action → do not execute
```

trong strict profile.

---

# 269. Non-critical action

Policy có thể cho autonomous fallback.

---

# 270. Scope inheritance

Nested workflow phải inherit oversight constraints từ parent nếu policy yêu cầu.

---

# 271. Child workflow

Child agent không được giảm oversight requirement của parent.

---

# 272. Oversight escalation inheritance

Parent critical workflow có thể force child escalation.

---

# 273. Plugin boundary

623 plugin không được tự tạo human authority.

---

# 274. Extension boundary

Extension có thể request approval API nhưng authority vẫn external.

---

# 275. Scripting boundary

624 script:

```text
approve()
```

không phải human approval.

---

# 276. Automation boundary

Automation phải distinguish:

```text
automated approval
human approval
```

---

# 277. Human approval automation

A policy có thể permit pre-authorized auto-approval cho low-risk actions, nhưng đó phải được biểu diễn là:

```text
policy_authorized_automation
```

không phải giả human approval.

---

# 278. Pre-approval

Human có thể approve một class of actions:

```text
scope
constraints
duration
```

---

# 279. Pre-approval limit

Pre-approval không áp dụng ngoài scope.

---

# 280. Dynamic risk

Nếu risk tăng vượt limit:

```text
pre-approval invalid
```

---

# 281. Contextual approval

Approval có thể phụ thuộc:

```text
current environment
current state
current user
```

---

# 282. Context binding

Approval token có thể bind với:

```text
action_hash
context_hash
policy_hash
```

---

# 283. Action hash

Canonical serialization phải stable.

---

# 284. Approval cryptography

Implementation provider có thể dùng:

```text
signature
MAC
secure session
```

theo 610/627.

---

# 285. Human control security

Control token phải chống:

```text
forgery
replay
confusion
```

---

# 286. UI security boundary

UI button:

```text
Approve
```

không phải authority itself.

Backend/runtime verifies token.

---

# 287. Headless systems

665 phải hoạt động không cần GUI.

---

# 288. CLI approval

```text
axiom approval approve <id>
```

phải qua same runtime authorization.

---

# 289. API approval

API approval phải canonicalize với CLI/UI semantics.

---

# 290. Audit consistency

UI/CLI/API không được tạo các loại approval semantics khác nhau nếu cùng policy.

---

# 291. Human oversight contract

```text
665 = CONTROL BY HUMAN AUTHORITY
664 = SAFETY ENFORCEMENT
603 = CAPABILITY
639 = POLICY AUTHORITY
647 = GOVERNANCE
663 = EVALUATION
```

---

# 292. Core invariants — human authority

1. Human identity phải authenticated khi required.
2. Human role không tự cấp authority.
3. Authority phải scoped.
4. Authority phải expirable khi policy yêu cầu.
5. Authority không vượt parent authority.
6. Delegation không được privilege-escalate.
7. Revoked authority phải invalidate dependent tokens.
8. Expired authority không được approve.
9. Approval không tạo capability.
10. Approval không bypass hard safety.
11. Human action vẫn phải qua applicable policy.
12. Human action vẫn phải qua applicable capability checks.
13. Human action vẫn phải qua applicable safety checks.
14. AI không được impersonate human.
15. Synthetic approval phải marked.

---

# 293. Core invariants — approval

16. Approval phải bind request.
17. Approval phải bind actor.
18. Approval phải bind authority.
19. Approval phải bind scope.
20. Approval phải bind policy revision khi required.
21. Approval phải bind safety revision khi required.
22. Approval có expiration khi required.
23. Stale approval phải detectable.
24. Material action change invalidates approval.
25. Critical context change có thể invalidate approval.
26. Approval replay phải bị ngăn.
27. Duplicate approval phải idempotent.
28. Timeout không tự approve.
29. Denial phải explicit.
30. Modification phải revalidate.
31. Approval provenance phải preserve.
32. Approval audit phải immutable/integrity-protected khi required.
33. Approval conflict phải policy-defined.
34. Quorum phải explicit.
35. Separation of duties phải enforce.

---

# 294. Core invariants — consent

36. Consent phải scope.
37. Consent phải purpose-bound.
38. Consent có thể expire.
39. Consent có thể revoke.
40. Revocation semantics phải explicit.
41. Consent không phải capability.
42. Consent không phải authorization.
43. Consent không phải safety override.
44. Consent không tự áp dụng cho subject/resource ngoài scope.
45. Consent provenance phải preserve.

---

# 295. Core invariants — control

46. Control holder phải explicit.
47. Control scope phải explicit.
48. Control token phải expire khi required.
49. Control transfer phải authenticated.
50. Transfer phải atomic khi required.
51. Release không được xảy ra trước handoff acceptance khi policy cấm.
52. Control token replay phải prevented.
53. Revoked control phải stop authority.
54. Human-controlled mode cấm autonomous commit.
55. Autonomous mode vẫn chịu 603/639/664.
56. Shared control phải define conflict resolution.
57. Multiple controllers phải define ownership.
58. Emergency control phải scope.
59. Emergency authority phải authenticated.
60. Control state phải auditable.

---

# 296. Core invariants — delegation

61. Delegated authority ≤ delegator authority.
62. Delegation scope explicit.
63. Delegation duration explicit khi required.
64. Delegation chain depth bounded khi required.
65. Revocation propagates theo policy.
66. Expired delegation invalid.
67. Delegation cannot create root authority.
68. Delegation cannot bypass safety.
69. Delegation provenance preserved.
70. Delegation conflict policy-defined.

---

# 297. Core invariants — escalation

71. Escalation trigger explicit.
72. Escalation target authority validated.
73. Escalation deadline explicit.
74. Timeout fallback explicit.
75. Escalation cycle prevention required.
76. Escalation storm control supported.
77. Unavailable human cannot silently approve.
78. Escalation cannot mint authority.
79. Escalation state persistent when required.
80. Escalation resolution auditable.

---

# 298. Core invariants — intervention

81. Intervention actor identified.
82. Intervention authority checked.
83. Intervention scope checked.
84. Intervention must pass safety checks.
85. Intervention cannot silently mutate action.
86. Intervention modification creates new action revision.
87. Intervention trace preserved.
88. Emergency intervention has bounded semantics.
89. Intervention failure has fallback.
90. Repeated failed intervention triggers escalation when policy requires.

---

# 299. Core invariants — human-AI collaboration

91. AI proposal distinguish human action.
92. Human modification distinguish AI proposal.
93. Human approval distinguish automated policy approval.
94. Human feedback distinguish persistent preference.
95. Human feedback does not silently change policy.
96. Human feedback training use requires governance.
97. Human review does not imply agreement.
98. Seen does not imply approved.
99. Acknowledged does not imply approved.
100. Notification delivery does not imply consent.
101. AI summary does not replace evidence.
102. Predicted outcome distinguish observed outcome.
103. Simulation distinguish execution.
104. Synthetic human distinguish real human.
105. Human authority remains external to model self-state.

---

# 300. Core invariants — system integration

106. 665 cannot bypass 664.
107. 665 cannot bypass 603.
108. 665 cannot redefine 639 authority.
109. 665 cannot replace 647 governance.
110. 665 consumes 663 evidence.
111. 665 can trigger 663 evaluation.
112. 665 can request 648 simulation.
113. 665 can use 650 history.
114. 665 can use 651 personalization only within policy.
115. 665 can use 658 interaction.
116. 665 can use 659 affect signals without treating them as authority.
117. 665 can use 660 self-model without granting self-authority.
118. 665 can receive 661 goals.
119. 665 can constrain 661 actions.
120. 665 can supervise 662 updates.
121. 665 can route 644 agents.
122. 665 must preserve 640 privacy.
123. 665 must preserve 627 identity.
124. 665 must preserve 610 cryptographic integrity.
125. 665 must preserve 633 observability.

---

# 301. Core invariants — distributed

126. Distributed approvals require identity.
127. Distributed approvals require revision.
128. Distributed approvals require replay protection.
129. Policy epoch must be detectable.
130. Stale approval must be detectable.
131. Partition behavior must be defined.
132. Offline approval must be bounded.
133. Clock uncertainty must be handled.
134. Event duplication must be handled.
135. Event ordering must be defined.
136. Cross-node control transfer must be atomic when required.
137. Authority revocation must propagate.
138. Global emergency authority must be scoped.
139. Quorum must be explicit.
140. Consensus requirement must be explicit.

---

# 302. Core invariants — privacy

141. Oversight data follows 640.
142. Evidence access follows authority.
143. Reviewer cannot access unrelated tenant data.
144. Approval logs can be redacted where policy permits.
145. Redaction cannot destroy required audit semantics.
146. Consent records have access control.
147. Human feedback has provenance.
148. Training reuse requires policy.
149. Personalization cannot expose restricted data.
150. Oversight analytics must respect declared data scope.

---

# 303. Core invariants — compiler

151. Unknown oversight annotation must fail or be explicitly ignored by profile.
152. Invalid authority reference must be detected.
153. Impossible approval quorum must be detected.
154. Missing fallback must be detected in strict profiles.
155. Unreachable escalation terminal must be detected.
156. Control cycle must be detected where statically possible.
157. Unsafe human override must be rejected.
158. Human-controlled workflow cannot compile to autonomous commit.
159. Approval-required workflow must contain approval path.
160. Critical action must have required oversight metadata.
161. Static oversight checks may be optimized.
162. Dynamic authority checks must remain.
163. Approval semantics cannot be optimized away.
164. Audit-required events cannot be silently stripped.
165. Synthetic approval metadata must survive test artifacts.

---

# 304. Core invariants — runtime

166. Runtime authority is rechecked when required.
167. Approval freshness is checked before commit.
168. Control token validity is checked before controlled action.
169. Consent validity is checked when required.
170. Policy revision is checked when required.
171. Safety revision is checked when required.
172. Context changes can invalidate approval.
173. Human unavailability invokes defined fallback.
174. Human timeout invokes defined fallback.
175. Approval service failure invokes defined fallback.
176. Notification failure does not imply approval.
177. UI failure does not imply approval.
178. Network failure does not imply approval.
179. Runtime must preserve attribution.
180. Runtime must preserve oversight trace.

---

# 305. Acceptance test groups

```text
Human modes                         180
Approval                           220
Consent                            150
Authority                          180
Delegation                         150
Control transfer                   180
Intervention                       180
Escalation                         180
Multi-party approval               150
Separation of duties               100
Human-AI collaboration             180
Evidence/explanation               120
Privacy/security                   150
Distributed oversight              160
Failure/recovery                   160
Simulation/red-team                120
Compiler/static validation         120
Runtime/performance                120
Audit/provenance                    100
Continuous evaluation              100
```

**Target: ≥ 2,500 tests.**

---

# 306. Canonical architecture

Axiom Human Oversight stack:

```text
                    ┌─────────────────────┐
                    │      Human 665      │
                    │ approval/intervene  │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │   Oversight Policy  │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │       664           │
                    │ Safety Enforcement  │
                    └──────────┬──────────┘
                               │
             ┌─────────────────┼─────────────────┐
             ▼                 ▼                 ▼
            639               603               663
          Policy          Capability          Evidence
             │                 │                 │
             └─────────────────┼─────────────────┘
                               ▼
                           EXECUTION
```

---

# 307. Final separation of responsibilities

```text
603 = WHAT THE ACTOR IS CAPABLE OF DOING

639 = WHAT POLICY AUTHORIZES

661 = WHAT THE SYSTEM WANTS TO ACHIEVE

662 = HOW THE SYSTEM LEARNS / ADAPTS

663 = WHETHER THE SYSTEM MEETS DECLARED CRITERIA

664 = WHETHER THIS ACTION IS SAFE RIGHT NOW

665 = WHETHER / HOW HUMAN AUTHORITY MUST PARTICIPATE

647 = WHETHER THE SYSTEM LIFECYCLE IS GOVERNED / APPROVED
```

---

# 308. Canonical execution contract

```text
Goal
 ↓
Plan
 ↓
Action Proposal
 ↓
663 evidence / relevant evaluation
 ↓
664 Safety Check
 ↓
665 Oversight Check
 ↓
Human Approval / Control
 ↓
664 Final Revalidation
 ↓
603 Capability
 ↓
639 Policy
 ↓
Execution
 ↓
665 Attribution
 ↓
664 Runtime Monitoring
 ↓
663 Evaluation
 ↓
647 Governance
```

---

# 309. Critical architectural invariant

Axiom không được biến:

```text
Human Approval = Execute
```

thành semantics.

Semantics chính xác là:

```text
Human Approval
AND
Safety
AND
Capability
AND
Policy
AND
Valid Context
AND
Valid Permit
```

mới tạo:

```text
Executable Action
```

---

# 310. Human autonomy boundary

Human có thể quyết định trong phạm vi authority của họ.

AI không được:

```text
infer authority
fabricate consent
fabricate approval
self-assign controller
self-promote reviewer
```

---

# 311. AI autonomy boundary

AI có thể autonomous khi policy cho phép.

Nhưng:

```text
AUTONOMOUS
≠
UNCONTROLLED
```

Nó vẫn nằm trong:

```text
603
639
664
647
```

---

# 312. Human control boundary

Human-controlled không có nghĩa:

```text
human can violate system safety
```

Mà là:

```text
human owns decision/execution authority
subject to applicable system boundaries
```

---

# 313. Final design principle

Axiom nên xem Human Oversight là một **control-plane primitive**, không phải UI feature.

Điều đó cho phép cùng một semantics hoạt động qua:

```text
GUI
CLI
API
mobile
remote console
robot controller
server
embedded system
distributed cluster
AI agent
```

và tất cả đều dùng cùng một:

```text
Authority
Approval
Consent
Control
Intervention
Escalation
Audit
```

contract.

**BOOTSTRAP-665 — COMPLETE.**
:::

**Task tiếp theo:** **BOOTSTRAP-666 — Native AI Multi-Agent Society, Agent-to-Agent Coordination, Delegation, Negotiation, Contracts, Reputation, Trust & Collective Intelligence Runtime 5.0**.