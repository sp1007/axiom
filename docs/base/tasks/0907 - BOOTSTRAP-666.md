Tiếp tục chuỗi kiến trúc. BOOTSTRAP-666 sẽ xây lớp **multi-agent** trên nền 644 + 665: nhiều AI agent có thể phối hợp, thương lượng, giao việc, ký contract, đánh giá trust/reputation và hình thành collective intelligence, nhưng **không được tự phát sinh authority vượt 603/639/664/665**.

:::writing{variant="document" id="58421" title="AXIOM BOOTSTRAP-666 — Native AI Multi-Agent Society, Coordination, Delegation, Negotiation, Contracts, Trust, Reputation & Collective Intelligence Runtime 5.0"}
# BOOTSTRAP-666

## Native AI Multi-Agent Society, Coordination, Delegation, Negotiation, Contracts, Trust, Reputation & Collective Intelligence Runtime 5.0

**Status:** COMPLETE  
**Layer:** Native AI Multi-Agent Coordination & Collective Intelligence  
**Predecessor:** BOOTSTRAP-665 — Human Oversight, Approval, Intervention, Escalation & Collaborative Control  
**Primary dependencies:** 603, 604, 605, 608, 620, 627, 628, 629, 631, 633, 634, 635, 637, 638, 639, 644, 645, 647, 650, 651, 652, 653, 654, 655, 657, 658, 660, 661, 663, 664, 665  
**Target acceptance:** ≥ 2,800 tests

---

# 1. Mục tiêu

BOOTSTRAP-666 định nghĩa nền tảng native cho hệ thống gồm nhiều agent có thể:

- discover agent;
- xác định identity;
- xác định capability;
- gửi task;
- delegate task;
- negotiate;
- lập contract;
- commit contract;
- thực hiện contract;
- monitor contract;
- renegotiate;
- terminate;
- arbitrate;
- đánh giá trust;
- đánh giá reputation;
- phối hợp execution;
- chia sẻ context;
- chia sẻ knowledge;
- hình thành team;
- bầu coordinator;
- thực hiện collective planning;
- giải quyết conflict;
- chia sẻ resource;
- thực hiện distributed decision;
- fault-tolerant collaboration;
- human-supervised multi-agent execution.

Mục tiêu không phải tạo "xã hội AI" theo nghĩa có nhân cách hay quyền lợi.

Trong Axiom:

> **Agent society là một mô hình computational cho nhiều autonomous actors phối hợp trong một environment chung.**

---

# 2. Boundary với các layer trước

```text
644 = Agent Runtime
665 = Human Oversight
666 = Multi-Agent Coordination
```

666 không thay thế:

```text
603 capability
639 policy
664 safety
665 human authority
647 governance
```

---

# 3. Agent

```axiom
struct Agent {
    id: AgentId
    identity: AgentIdentity
    capabilities: CapabilitySet
    policies: PolicyRef[]
    endpoint: AgentEndpoint
    state: AgentState
}
```

---

# 4. AgentIdentity

```axiom
struct AgentIdentity {
    id: AgentId
    issuer: IdentityIssuer
    public_key: KeyRef
    revision: Version
    status: IdentityStatus
}
```

Identity không đồng nghĩa authority.

---

# 5. AgentCapability

Agent có thể advertise capability:

```axiom
struct AgentCapability {
    id
    operation
    input_schema
    output_schema
    constraints
    cost
    availability
}
```

---

# 6. Capability advertisement

Agent có thể nói:

```text
"I can perform image_generation."
```

Nhưng advertisement không đảm bảo:

```text
authorized
available
safe
```

---

# 7. Capability verification

Trước execution:

```text
discover
→ authenticate
→ verify capability
→ check authority
→ safety check
```

---

# 8. Agent discovery

```axiom
agent.discover(query)
```

Có thể dựa trên:

```text
name
capability
protocol
location
trust requirements
resource requirements
```

---

# 9. Agent Registry

```axiom
struct AgentRegistry {
    agents
    capabilities
    endpoints
    status
    revisions
}
```

---

# 10. Dynamic discovery

Agent registry có thể thay đổi runtime.

---

# 11. Stale discovery

Discovery result phải có freshness metadata.

---

# 12. Agent availability

```text
Available
Busy
Degraded
Offline
Unknown
Quarantined
Retired
```

---

# 13. Agent lifecycle

```text
Created
Registered
Active
Suspended
Degraded
Quarantined
Retired
Revoked
```

---

# 14. Agent quarantine

Agent có hành vi bất thường có thể bị:

```text
quarantine
```

Không tự động xóa identity.

---

# 15. Agent revocation

Revoked identity không được tham gia new contracts.

---

# 16. Agent session

```axiom
struct AgentSession {
    local_agent
    remote_agent
    session_id
    security_context
    policy_revision
    expires_at
}
```

---

# 17. Agent-to-agent communication

666 sử dụng 604/634/631 tùy transport.

Transport không quyết định semantics của contract.

---

# 18. Message

```axiom
struct AgentMessage {
    id
    sender
    receiver
    session
    type
    payload
    timestamp
}
```

---

# 19. Message types

```text
Discovery
CapabilityQuery
TaskRequest
TaskOffer
TaskAccept
TaskReject
Proposal
CounterProposal
Contract
Commit
Progress
Result
Failure
Cancel
Escalate
Heartbeat
KnowledgeShare
Vote
```

---

# 20. Task

```axiom
struct AgentTask {
    id
    objective
    inputs
    constraints
    deadline
    budget
    authority
    safety_profile
}
```

---

# 21. Task delegation

Agent A:

```text
A → B
```

không đồng nghĩa B có toàn bộ authority của A.

---

# 22. Delegation

```axiom
struct AgentDelegation {
    delegator
    delegate
    task_scope
    capability_scope
    resource_scope
    duration
    constraints
}
```

---

# 23. Delegation invariant

```text
effective_authority(B)
≤
delegated_authority(A)
```

---

# 24. Delegation chain

```text
Human
 ↓
Agent A
 ↓
Agent B
 ↓
Agent C
```

Authority phải remain bounded.

---

# 25. Delegation depth

Policy có thể giới hạn:

```text
max_delegation_depth
```

---

# 26. Recursive delegation

Agent B chỉ được delegate tiếp nếu policy cho phép.

---

# 27. Task ownership

```axiom
struct TaskOwnership {
    owner
    executor
    supervisor
    authority_source
}
```

---

# 28. Task ownership ≠ execution

Owner có thể là A, executor B.

---

# 29. Coordinator

Một multi-agent workflow có thể có coordinator:

```axiom
struct Coordinator {
    agent
    scope
    term
    authority
}
```

Coordinator không tự có global authority.

---

# 30. Team

```axiom
struct AgentTeam {
    id
    members
    coordinator
    mission
    policy
    lifecycle
}
```

---

# 31. Team formation

```text
Discover
→ Select
→ Authenticate
→ Negotiate
→ Contract
→ Activate
```

---

# 32. Team dissolution

Team có thể:

```text
Complete
Cancel
Timeout
Failure
PolicyRevoked
```

---

# 33. Role

```axiom
struct AgentRole {
    id
    responsibilities
    capabilities
    constraints
}
```

---

# 34. Role assignment

Role assignment phải explicit.

---

# 35. Role ≠ capability

Một agent có capability nhưng không nhất thiết được assign role.

---

# 36. Role ≠ authority

Role phải được map qua policy.

---

# 37. Task bidding

Agents có thể submit offers:

```axiom
struct TaskBid {
    agent
    task
    cost
    duration
    confidence
    resource_requirement
    conditions
}
```

---

# 38. Bid

Bid không phải contract.

---

# 39. Bid expiration

Bid phải có expiry.

---

# 40. Bid withdrawal

Agent có thể withdraw bid trước commit nếu contract policy cho phép.

---

# 41. Negotiation

```axiom
struct Negotiation {
    id
    participants
    subject
    proposals
    constraints
    deadline
    state
}
```

---

# 42. Proposal

```axiom
struct Proposal {
    proposer
    terms
    cost
    deadline
    guarantees
    assumptions
}
```

---

# 43. Counter-proposal

Agent có thể counter:

```text
A proposal
→ B counter
→ A counter
→ ...
```

---

# 44. Negotiation termination

Các terminal states:

```text
Agreement
Rejected
Expired
Cancelled
Deadlock
Escalated
```

---

# 45. Negotiation deadlock

666 phải phát hiện hoặc timeout negotiation loop.

---

# 46. Negotiation objective

Agent có thể optimize:

```text
cost
time
quality
risk
resource
utility
```

nhưng không được vi phạm hard constraints.

---

# 47. Utility boundary

661 utility có thể dùng để đánh giá proposal.

Utility không cấp authority.

---

# 48. Multi-objective negotiation

Hỗ trợ:

```text
weighted
lexicographic
Pareto
satisficing
```

theo 661/652.

---

# 49. Contract

```axiom
struct AgentContract {
    id
    parties
    obligations
    rights
    constraints
    resources
    deadlines
    acceptance
    termination
    dispute_policy
    revision
}
```

---

# 50. Contract formation

```text
Proposal
→ Agreement
→ Validation
→ Commit
```

---

# 51. Contract validation

Trước commit:

```text
identity
capability
authority
policy
safety
resource
```

phải được kiểm tra theo profile.

---

# 52. Contract commit

Commit tạo immutable contract revision.

---

# 53. Contract revision

Contract không sửa trực tiếp.

```text
v1
→ amendment
→ v2
```

---

# 54. Contract amendment

Các parties phải authorize amendment.

---

# 55. Contract obligations

```axiom
struct Obligation {
    party
    action
    deadline
    acceptance
    evidence
}
```

---

# 56. Contract rights

```axiom
struct ContractRight {
    holder
    operation
    scope
    conditions
}
```

Contract right không vượt system authority.

---

# 57. Contract precondition

```axiom
@contract_precondition
```

---

# 58. Contract postcondition

```axiom
@contract_postcondition
```

---

# 59. Contract invariant

```axiom
@contract_invariant
```

---

# 60. Contract breach

```axiom
struct ContractBreach {
    contract
    party
    obligation
    evidence
    severity
}
```

---

# 61. Breach ≠ maliciousness

Contract failure có thể do:

```text
failure
resource loss
network partition
unexpected environment
policy change
```

Không tự gán motive.

---

# 62. Remediation

```text
Retry
Repair
Renegotiate
Compensate
Rollback
Terminate
Escalate
```

---

# 63. Compensation

Compensation là computational contract mechanism.

Không mặc định là monetary.

---

# 64. SLA

```axiom
struct ServiceLevel {
    latency
    availability
    quality
    resource_limit
}
```

---

# 65. SLA monitoring

Runtime monitor:

```text
actual
vs
contract
```

---

# 66. Contract monitor

```axiom
struct ContractMonitor {
    contract
    obligations
    metrics
    violations
}
```

---

# 67. Contract state

```text
Draft
Negotiating
Committed
Active
Suspended
Breached
Renegotiating
Completed
Terminated
```

---

# 68. Suspension

Contract có thể suspend khi dependency unavailable.

---

# 69. Termination

Termination semantics phải explicit.

---

# 70. Graceful termination

Agent có thể finish already-committed atomic operation trước termination nếu policy cho phép.

---

# 71. Force termination

Critical safety condition có thể terminate immediately qua 664.

---

# 72. Safety supremacy

Contract không thể override 664.

---

# 73. Policy supremacy

Contract không thể override 639.

---

# 74. Human authority

665 có thể require human approval cho contract formation/termination.

---

# 75. Reputation

```axiom
struct Reputation {
    subject
    metrics
    evidence
    window
    model_revision
}
```

---

# 76. Reputation ≠ truth

Reputation là derived signal.

---

# 77. Reputation provenance

Mọi reputation score phải truy được evidence source.

---

# 78. Trust

```axiom
struct TrustAssessment {
    subject
    context
    evidence
    confidence
    model
}
```

Trust là contextual.

---

# 79. Contextual trust

Agent có thể:

```text
trust A for image processing
```

nhưng không:

```text
trust A for arbitrary system administration
```

---

# 80. Trust ≠ authority

Trust không cấp capability.

---

# 81. Trust ≠ identity

Identity xác định actor.

Trust đánh giá reliability trong context.

---

# 82. Reputation sources

```text
completed contracts
violations
performance
verification
human feedback
independent evaluation
```

---

# 83. Source weighting

Weighting phải model-defined và versioned.

---

# 84. Negative reputation

Một failure không nhất thiết chứng minh malicious behavior.

Reputation model phải phân biệt:

```text
failure
unreliability
policy violation
safety violation
intentional misconduct
```

nếu evidence đủ.

---

# 85. Evidence quality

Evidence có:

```text
source
confidence
timestamp
independence
integrity
```

---

# 86. Sybil resistance

666 phải hỗ trợ identity-level protections chống tạo hàng loạt agent giả.

---

# 87. Agent identity cost

Registry có thể yêu cầu:

```text
attestation
issuer
proof
registration
```

theo 627/638.

---

# 88. Reputation manipulation

Phải chống:

```text
self-review
collusive reviews
fake contracts
sybil reputation
```

---

# 89. Independent evaluator

663/646 có thể cung cấp independent evidence.

---

# 90. Trust decay

Trust có thể decay theo thời gian.

Model phải explicit.

---

# 91. Trust refresh

Successful verified interactions có thể update trust.

---

# 92. No automatic trust inheritance

Agent A trust B không tự tạo:

```text
trust(A,C)
```

---

# 93. Transitive trust

Có thể hỗ trợ nhưng phải explicit model.

---

# 94. Trust boundary

Trust score không bypass:

```text
603
639
664
665
```

---

# 95. Collective intelligence

666 cung cấp primitives:

```text
shared planning
task decomposition
distributed reasoning
voting
consensus
aggregation
specialization
ensemble execution
```

---

# 96. Shared workspace

```axiom
struct AgentWorkspace {
    shared_state
    artifacts
    tasks
    contracts
    events
}
```

---

# 97. Shared memory

Shared memory semantics dựa trên 650/628.

---

# 98. Knowledge contribution

```axiom
struct KnowledgeContribution {
    agent
    content
    provenance
    confidence
    timestamp
}
```

---

# 99. Knowledge provenance

Knowledge phải giữ source provenance.

---

# 100. Knowledge conflict

Nếu:

```text
A says X
B says not X
```

không tự chọn một bên.

Tạo:

```text
KnowledgeConflict
```

---

# 101. Conflict resolution

```text
verify
cross-check
request evidence
vote
specialist review
human escalation
```

---

# 102. Agent vote

```axiom
struct AgentVote {
    agent
    proposal
    position
    evidence
    confidence
}
```

---

# 103. Voting

Supported:

```text
majority
supermajority
unanimity
weighted
ranked
approval voting
```

---

# 104. Voting authority

Weight phải policy-defined.

---

# 105. Reputation-weighted voting

Có thể hỗ trợ.

Nhưng reputation không tự động trở thành vote weight.

---

# 106. Consensus

```axiom
struct ConsensusPolicy {
    threshold
    participants
    timeout
    fallback
}
```

---

# 107. Consensus failure

Consensus failure không được biến thành silent approval.

---

# 108. Quorum

Quorum phải explicit.

---

# 109. Leader election

635 cung cấp distributed coordination.

666 chỉ consume election result.

---

# 110. Coordinator failure

Team phải có:

```text
backup coordinator
reelection
safe suspension
```

---

# 111. Byzantine participants

666 phải hỗ trợ detection/isolation signals.

Không yêu cầu mọi deployment phải Byzantine tolerant.

---

# 112. Fault model

```text
Crash
Delay
Partition
Corruption
Invalid result
Policy violation
Identity revocation
```

---

# 113. Agent health

```axiom
struct AgentHealth {
    availability
    latency
    error_rate
    contract_status
}
```

---

# 114. Agent heartbeat

Heartbeat không chứng minh semantic correctness.

---

# 115. Liveness ≠ correctness

Agent online không có nghĩa result đúng.

---

# 116. Result verification

Result có thể qua:

```text
663 evaluation
independent agent
formal checker
human reviewer
```

---

# 117. Redundant execution

Critical tasks có thể chạy:

```text
A
B
C
```

để compare.

---

# 118. Ensemble

```axiom
struct AgentEnsemble {
    members
    aggregation
    quorum
    validation
}
```

---

# 119. Result aggregation

```text
majority
weighted
confidence
quality
verified
```

---

# 120. Aggregation safety

Aggregate result vẫn phải qua 664.

---

# 121. Specialist delegation

Coordinator có thể chọn specialist theo capability.

---

# 122. Capability matching

Matching dựa trên declared capability.

Không suy diễn capability từ unrelated attributes.

---

# 123. Capability confidence

Agent có thể declare confidence/benchmark evidence.

---

# 124. Capability evidence

Capability claim có thể reference:

```text
663 benchmark
647 certification
646 test
```

---

# 125. Capability freshness

Benchmark evidence có thể expire.

---

# 126. Agent selection

Selection criteria:

```text
capability
availability
cost
latency
trust
risk
policy
```

---

# 127. No implicit global ranking

Agent registry không bắt buộc có global "best agent".

---

# 128. Context-specific selection

Agent selection là contextual.

---

# 129. Negotiated resource

Agents có thể negotiate:

```text
CPU
GPU
memory
storage
network
time
budget
```

---

# 130. Resource contract

```axiom
struct ResourceAgreement {
    provider
    consumer
    resource
    quota
    duration
}
```

---

# 131. Resource authority

Resource agreement không bypass 606.

---

# 132. Scheduling

629/630/635 có thể schedule tasks.

---

# 133. Agent task dependency

```axiom
struct TaskDependency {
    predecessor
    successor
    condition
}
```

---

# 134. DAG execution

Multi-agent workflows có thể biểu diễn DAG.

---

# 135. Cycles

Cycles phải explicit loop construct.

---

# 136. Deadlock

Runtime phải detect/timeout impossible waits.

---

# 137. Compensation workflow

Nếu task A complete nhưng B fail:

```text
compensation(A)
```

theo 629.

---

# 138. Saga

666 có thể consume 629 Saga semantics.

---

# 139. Transaction boundary

Multi-agent contract không tự tạo distributed atomic transaction.

---

# 140. Idempotency

Task execution có thể yêu cầu idempotency key.

---

# 141. Duplicate task

Duplicate delivery không được tạo duplicate side effect nếu task idempotent profile yêu cầu.

---

# 142. Retry

Retry policy:

```text
max_attempts
backoff
jitter
conditions
```

---

# 143. Retry safety

Không retry irreversible action trừ khi policy explicitly permits.

---

# 144. Agent failure

Agent failure triggers:

```text
retry
replacement
reassign
compensate
escalate
```

---

# 145. Replacement

Replacement agent phải revalidate capability and authority.

---

# 146. Contract transfer

Contract có thể transfer nếu all required parties authorize.

---

# 147. Contract novation

```axiom
struct ContractTransfer {
    old_party
    new_party
    obligations
    approvals
}
```

---

# 148. Contract dispute

```axiom
struct Dispute {
    contract
    claims
    evidence
    parties
    resolver
}
```

---

# 149. Arbitration

Resolver có thể:

```text
agent
human
service
rule engine
```

theo contract/policy.

---

# 150. Arbitration authority

Arbitrator không tự có global authority.

---

# 151. Dispute evidence

Evidence phải provenance-aware.

---

# 152. Negotiation privacy

Agent không phải reveal private internal state.

---

# 153. Information boundary

Negotiation payload phải obey:

```text
603
639
640
```

---

# 154. Strategic behavior

Agents có thể optimize objectives.

Nhưng contract/safety/policy constraints remain mandatory.

---

# 155. Misrepresentation

Agent claim phải distinguish:

```text
verified
declared
estimated
unknown
```

---

# 156. Confidence

Agent proposal có thể có confidence.

Confidence không phải guarantee.

---

# 157. Guarantee

Contract guarantee phải explicit and enforceable.

---

# 158. Prediction

Prediction không phải commitment.

---

# 159. Commitment

Commitment tạo obligation.

---

# 160. Commitment revocation

Revocation phải follow contract.

---

# 161. Agent promises

```axiom
struct Promise {
    issuer
    claim
    conditions
    expiry
    evidence
}
```

Promise không tự là contract.

---

# 162. Contract enforcement

Contract monitor có thể trigger:

```text
warning
retry
renegotiate
terminate
escalate
```

---

# 163. Safety-triggered termination

664 có thể force terminate unsafe agent action.

---

# 164. Human-triggered termination

665 có thể terminate theo authority.

---

# 165. Governance-triggered termination

647 có thể revoke deployment.

---

# 166. Agent suspension

Agent có thể suspended trong khi preserving contract state.

---

# 167. Agent recovery

Recovery phải reauthenticate/revalidate.

---

# 168. Trust after recovery

Recovery không tự restore previous trust level.

Policy quyết định.

---

# 169. Quarantine

Quarantine agent:

```text
cannot receive new critical tasks
```

theo policy.

---

# 170. Existing contracts

Policy phải định nghĩa existing contracts khi quarantine.

---

# 171. Collective policy

Team có thể có team policy.

Nhưng team policy không vượt parent policy.

---

# 172. Policy inheritance

```text
system
 ↓
organization
 ↓
team
 ↓
agent
 ↓
task
```

---

# 173. Policy narrowing

Child policy được phép narrow scope.

---

# 174. Policy widening

Child policy không được widen parent hard constraints.

---

# 175. Collective goals

Team có thể có:

```axiom
GoalSet
```

từ 661.

---

# 176. Goal decomposition

Coordinator có thể decompose goal thành tasks.

---

# 177. Goal conflict

Agents có thể có conflicting objectives.

---

# 178. Conflict resolution

Resolution dựa trên:

```text
authority
policy
contract
priority
utility
```

theo 661/639.

---

# 179. No hidden social hierarchy

Agent không tự tạo permanent authority hierarchy chỉ từ interaction history.

---

# 180. Emergent coordination

Runtime có thể quan sát emergent behavior nhưng authority remains explicit.

---

# 181. Collective memory

650 cung cấp:

```text
shared episodic memory
semantic memory
task history
```

---

# 182. Memory ownership

Shared memory phải có owner/access policy.

---

# 183. Memory poisoning

666 phải hỗ trợ detection signals cho poisoned shared knowledge.

---

# 184. Knowledge validation

Critical knowledge nên có independent verification.

---

# 185. Reputation poisoning

Repeated false reports không được tạo reputation change không kiểm chứng.

---

# 186. Collusion

646/663 có thể red-team:

```text
agent collusion
fake consensus
vote manipulation
reputation manipulation
contract laundering
```

---

# 187. Agent coalition

```axiom
struct AgentCoalition {
    members
    purpose
    scope
    duration
    contract
}
```

---

# 188. Coalition authority

Coalition không được tự tăng member authority.

---

# 189. Coalition dissolution

Dissolution phải xử lý:

```text
active tasks
contracts
resources
shared state
```

---

# 190. Collective decision

```axiom
struct CollectiveDecision {
    participants
    proposals
    votes
    evidence
    policy
    result
}
```

---

# 191. Decision provenance

Phải biết:

```text
who proposed
who voted
what evidence
what rule
```

---

# 192. Collective decision ≠ authority

Decision output vẫn phải pass policy/capability/safety.

---

# 193. Human oversight

Critical collective decisions có thể require 665.

---

# 194. Human veto

Human authority có thể veto collective action trong scope.

---

# 195. AI-to-human escalation

Nếu agents disagree:

```text
collective conflict
→ human escalation
```

nếu policy yêu cầu.

---

# 196. Multi-human + multi-agent

Có thể có:

```text
Human A
Human B
Agent A
Agent B
Agent C
```

trong cùng workflow.

665 remains human authority layer.

---

# 197. Mixed quorum

Có thể require:

```text
2 agents
+
1 human
```

nhưng authority semantics phải explicit.

---

# 198. Human authority cannot be replaced by agent vote

Unless policy explicitly defines an autonomous mode where human approval is not required.

---

# 199. Agent vote cannot fabricate human approval

---

# 200. Human approval cannot fabricate agent consensus

---

# 201. Contract signing

```axiom
contract.sign(agent)
```

requires identity + authority.

---

# 202. Contract signature

Signature proves:

```text
identity/control
```

not necessarily truth of all claims.

---

# 203. Contract evidence

Claims may reference evidence.

---

# 204. Contract hash

Canonical contract representation must be hashable.

---

# 205. Revision hash

Every committed revision has unique content identity.

---

# 206. Amendment

Amendment references parent revision.

---

# 207. Contract replay

Old contract commit cannot silently reapply after termination.

---

# 208. Idempotent commit

Repeated same commit request returns same contract state.

---

# 209. Contract conflict

Two incompatible commits must not both become canonical.

---

# 210. Optimistic negotiation

Negotiation may use tentative proposals.

Only commit creates obligation.

---

# 211. Tentative state

```text
proposal
≠
commitment
```

---

# 212. Agent marketplace boundary

666 can support task offers.

It does not require monetary economy.

---

# 213. Economic extension

Future modules may add:

```text
credits
payments
budgets
markets
```

using 606/625/financial extension layers.

---

# 214. Pricing

Agent can advertise cost.

Cost is not necessarily monetary.

---

# 215. Cost units

```text
CPU
GPU
time
energy
tokens
storage
network
credits
```

---

# 216. Resource accounting

Resource consumption feeds 606.

---

# 217. Agent budget

```axiom
struct AgentBudget {
    compute
    memory
    network
    time
    financial
}
```

---

# 218. Budget enforcement

666 requests budget reservation from 606.

---

# 219. Budget exhaustion

Task may:

```text
pause
degrade
renegotiate
terminate
```

---

# 220. Collective resource conflict

606 remains authoritative for system resource allocation.

---

# 221. Service discovery

631 provides service discovery.

666 adds semantic agent discovery above it.

---

# 222. Agent endpoint

Endpoint can be:

```text
local
process
thread
remote service
cluster
device
```

---

# 223. Local agents

No network required for local multi-agent systems.

---

# 224. Remote agents

Remote identity must use 627/610 as applicable.

---

# 225. Mobile/edge agents

666 maps onto 614/656/636.

---

# 226. WASM agents

WASM sandboxed agent must respect host capabilities.

---

# 227. Plugin agents

623 plugin agent cannot escape plugin isolation.

---

# 228. Agent spawning

```axiom
agent.spawn(config)
```

must be capability/policy controlled.

---

# 229. Spawned agent identity

Each spawned agent receives distinct identity.

---

# 230. Parent-child relation

```axiom
AgentParent {
    parent
    child
    scope
    expiry
}
```

---

# 231. Spawn budget

Agent spawning can have:

```text
max_agents
max_depth
max_runtime
max_memory
```

---

# 232. Spawn storm protection

Runtime must enforce limits.

---

# 233. Self-replication

Unbounded autonomous agent spawning is prohibited by default in strict profiles.

---

# 234. Agent retirement

Retirement should clean:

```text
sessions
locks
temporary delegations
```

and preserve required contract/audit history.

---

# 235. Agent identity rotation

638 handles credential rotation.

---

# 236. Trust after identity rotation

Identity rotation must preserve or reset trust according to explicit policy.

---

# 237. Agent migration

Agent can move execution location while preserving logical identity if policy allows.

---

# 238. Migration validation

After migration:

```text
identity
capability
policy
contract
safety
```

must be revalidated as required.

---

# 239. Collective monitoring

633 can aggregate:

```text
agent health
contract health
coordination latency
failure rates
```

---

# 240. Coordination metrics

```text
task_completion
coordination_latency
negotiation_rounds
contract_breach_rate
handoff_failure
consensus_time
recovery_time
```

---

# 241. Collective evaluation

663 can evaluate:

```text
team quality
coordination efficiency
robustness
fairness of task allocation
failure resilience
```

---

# 242. Agent benchmarking

646/663 can benchmark agent capability.

---

# 243. Capability certification

647 can govern certified agent capabilities.

---

# 244. Trust update

Trust model may consume certified evidence.

---

# 245. No trust inflation

Repeated self-generated evidence must not inflate trust without independent validation where required.

---

# 246. Reputation history

Reputation is time-indexed.

---

# 247. Reputation decay

If enabled, decay model must be versioned.

---

# 248. Contextual reputation

```text
Reputation(agent, capability, context)
```

is preferable to one universal scalar.

---

# 249. No universal agent score

Axiom does not require one global "agent quality" number.

---

# 250. Contract reputation

Completed contract evidence may contribute to reputation.

---

# 251. Breach evidence

Contract breach may affect reputation according to model.

---

# 252. Disputed breach

Disputed breach should remain marked disputed until resolution.

---

# 253. Reputation correction

Wrong evidence can be corrected with provenance-preserving amendment.

---

# 254. Trust confidence

Trust assessment must include confidence/uncertainty where model supports it.

---

# 255. Uncertainty

Low-confidence trust should trigger conservative policy where required.

---

# 256. Risk-sensitive agent selection

652/653 can incorporate trust uncertainty into planning.

---

# 257. Safety-sensitive selection

664 can reject agent selection regardless of utility.

---

# 258. Human-sensitive selection

665 can require human review for critical agent selection.

---

# 259. Collective learning

662 may learn from multi-agent interaction.

Learning must remain bounded by 639/664/665.

---

# 260. No policy self-modification

Agent collective cannot rewrite hard system policy merely through consensus.

---

# 261. Policy update

637/647 govern policy revision.

---

# 262. Model update

662 governs model learning/update.

---

# 263. Collective model

655 may maintain shared world model.

---

# 264. World-model disagreement

Agents can hold different world-model hypotheses.

---

# 265. Hypothesis aggregation

Aggregation must preserve uncertainty.

---

# 266. Epistemic diversity

Collective systems may deliberately preserve multiple hypotheses rather than force premature consensus.

---

# 267. Independent reasoning

Ensemble evaluation can require independent execution to reduce correlated failure.

---

# 268. Correlated failure

Agents sharing same model/data may produce correlated outputs.

666 should represent:

```text
correlation_group
```

where needed.

---

# 269. Diversity policy

663 can measure diversity.

---

# 270. Ensemble stopping

Stop when:

```text
quorum
confidence threshold
budget
deadline
```

is reached.

---

# 271. Collective uncertainty

Aggregate confidence must not exceed evidence-supported confidence.

---

# 272. Confidence aggregation

Aggregation method must be explicit.

---

# 273. Consensus illusion

Majority agreement does not imply truth.

---

# 274. Evidence-first mode

Critical decisions may require evidence rather than majority alone.

---

# 275. Specialist override

Domain specialist can flag collective result for review according to policy.

---

# 276. Human escalation

Collective uncertainty beyond threshold can trigger 665.

---

# 277. Safety escalation

Collective risk beyond 664 threshold triggers safety action.

---

# 278. Collective emergency

Any agent can emit emergency signal if authorized.

Emergency handling remains 664.

---

# 279. Agent incident

```axiom
struct AgentIncident {
    agent
    event
    severity
    evidence
    containment
}
```

---

# 280. Incident containment

Containment may:

```text
pause agent
revoke task
revoke delegation
quarantine
terminate session
```

---

# 281. Incident response

647/664/665 determine governance/safety/human aspects.

---

# 282. Agent forensic trace

666 maintains coordination trace:

```text
messages
proposals
contracts
votes
delegations
handoffs
```

subject to privacy policy.

---

# 283. Message provenance

Every critical coordination message should identify sender/session.

---

# 284. Message authenticity

Critical messages require authentication/integrity.

---

# 285. Message freshness

Critical commands require freshness/replay protection.

---

# 286. Agent protocol version

Every protocol session negotiates supported version.

---

# 287. Compatibility

Protocol incompatibility must fail explicitly.

---

# 288. Schema evolution

612 governs serialization/schema evolution.

---

# 289. Contract schema evolution

Contract schema revision must be explicit.

---

# 290. Backward compatibility

Old agent cannot silently interpret new contract semantics incorrectly.

---

# 291. Agent capability negotiation

```axiom
negotiate_capability(version)
```

---

# 292. Feature negotiation

Optional features require explicit negotiation.

---

# 293. Unknown feature

Unknown critical feature → reject or safe fallback.

---

# 294. Agent protocol timeout

All network coordination operations need timeout policy.

---

# 295. Cancellation

Task cancellation must propagate according to contract.

---

# 296. Cancellation acknowledgement

Remote agent should acknowledge cancellation when protocol permits.

---

# 297. Cancellation race

If execution commits before cancellation arrives, state must resolve deterministically.

---

# 298. Late result

Late result after task cancellation must not silently commit.

---

# 299. Exactly-once illusion

Distributed runtime should not promise exactly-once semantics unless implementation can guarantee it.

Prefer:

```text
at-least-once + idempotency
```

or explicit transactional semantics.

---

# 300. Final coordination contract

```text
Discovery
 ↓
Identity
 ↓
Capability
 ↓
Task
 ↓
Delegation
 ↓
Negotiation
 ↓
Contract
 ↓
Safety / Policy / Authority
 ↓
Execution
 ↓
Verification
 ↓
Result
 ↓
Reputation / Trust Evidence
 ↓
Collective Learning
```

---

# 301. Compiler annotations

```text
@agent
@agent_identity
@agent_capability
@agent_discovery
@agent_registry
@agent_task
@agent_delegate
@agent_role
@agent_team
@agent_coordinator

@agent_bid
@negotiation
@proposal
@counter_proposal
@contract
@contract_obligation
@contract_right
@contract_precondition
@contract_postcondition
@contract_invariant
@contract_monitor
@contract_breach
@contract_amendment
@contract_terminate

@trust
@trust_model
@reputation
@reputation_model
@reputation_evidence

@collective
@collective_decision
@collective_vote
@consensus
@quorum
@ensemble
@distributed_reasoning

@agent_spawn
@agent_budget
@agent_quarantine
@agent_revoke

@knowledge_share
@knowledge_conflict
@knowledge_verify

@agent_trace
@contract_trace
@coordination_trace
```

---

# 302. Metadata artifacts

```text
.axagent
.axagentid
.axagentcap
.axagentregistry
.axagenttask
.axdelegation
.axteam
.axcoordination

.axnegotiation
.axproposal
.axcontract
.axcontractrev
.axcontracttrace
.axbreach

.axtrust
.axtrustmodel
.axreputation
.axreputationmodel
.axreputationevidence

.axcollective
.axvote
.axconsensus
.axensemble
.axknowledge
.axknowledgeconflict

.axagentincident
.axagenttrace
.axcoordtrace
```

---

# 303. IR

```text
AgentCreate
AgentDestroy
AgentRegister
AgentUnregister
AgentDiscover
AgentAuthenticate
AgentCapabilityQuery
AgentCapabilityVerify

AgentTaskCreate
AgentTaskAssign
AgentTaskDelegate
AgentTaskAccept
AgentTaskReject
AgentTaskCancel
AgentTaskComplete

AgentBidCreate
AgentBidAccept
AgentBidReject
AgentBidWithdraw

NegotiationCreate
NegotiationProposal
NegotiationCounter
NegotiationAccept
NegotiationReject
NegotiationExpire
NegotiationCancel

ContractCreate
ContractValidate
ContractCommit
ContractAmend
ContractSuspend
ContractResume
ContractMonitor
ContractBreach
ContractRemediate
ContractTerminate
ContractTransfer

TrustEvaluate
TrustUpdate
ReputationEvaluate
ReputationUpdate
ReputationEvidenceAdd

AgentTeamCreate
AgentTeamJoin
AgentTeamLeave
AgentRoleAssign
AgentRoleRevoke
AgentCoordinatorElect
AgentCoordinatorTransfer

CollectiveGoalCreate
CollectiveTaskDecompose
CollectivePlan
CollectiveVote
CollectiveConsensus
CollectiveQuorum
CollectiveAggregate

KnowledgeShare
KnowledgeVerify
KnowledgeConflict
KnowledgeResolve

AgentSpawn
AgentQuarantine
AgentRecover
AgentRevoke

AgentHealth
AgentHeartbeat
AgentFailure
AgentReplacement

AgentIncident
AgentContain
AgentTrace
CoordinationTrace
ContractTrace
```

---

# 304. Profiles

```text
AXAGENT_NONE
AXAGENT_CORE
AXAGENT_DISCOVERY
AXAGENT_IDENTITY
AXAGENT_CAPABILITY
AXAGENT_TASK
AXAGENT_DELEGATION
AXAGENT_TEAM
AXAGENT_COORDINATION

AXNEGOTIATION_CORE
AXNEGOTIATION_MULTI
AXNEGOTIATION_DISTRIBUTED

AXCONTRACT_CORE
AXCONTRACT_MONITOR
AXCONTRACT_SLA
AXCONTRACT_DISPUTE
AXCONTRACT_TRANSFER

AXTRUST_CORE
AXTRUST_CONTEXTUAL
AXTRUST_DISTRIBUTED

AXREPUTATION_CORE
AXREPUTATION_EVIDENCE
AXREPUTATION_DECAY

AXCOLLECTIVE_CORE
AXCOLLECTIVE_VOTE
AXCOLLECTIVE_CONSENSUS
AXCOLLECTIVE_ENSEMBLE
AXCOLLECTIVE_REASONING
AXCOLLECTIVE_KNOWLEDGE

AXAGENT_FAULT
AXAGENT_QUARANTINE
AXAGENT_REDUNDANT
AXAGENT_BYZANTINE

AXAGENT_HUMAN
AXAGENT_SAFETY
AXAGENT_GOVERNANCE

AXAGENT_EDGE
AXAGENT_MOBILE
AXAGENT_WASM
AXAGENT_DISTRIBUTED
AXAGENT_REALTIME

AXAGENT_FULL
```

---

# 305. CLI

```text
axiom agent list
axiom agent inspect
axiom agent discover
axiom agent capabilities
axiom agent health
axiom agent register
axiom agent revoke
axiom agent quarantine
axiom agent recover

axiom agent task list
axiom agent task inspect
axiom agent task assign
axiom agent task delegate
axiom agent task cancel

axiom agent team list
axiom agent team inspect
axiom agent team create
axiom agent team dissolve
axiom agent team members
axiom agent team coordinator

axiom negotiation list
axiom negotiation inspect
axiom negotiation propose
axiom negotiation counter
axiom negotiation accept
axiom negotiation reject
axiom negotiation cancel

axiom contract list
axiom contract inspect
axiom contract validate
axiom contract commit
axiom contract amend
axiom contract suspend
axiom contract resume
axiom contract terminate
axiom contract dispute

axiom trust inspect
axiom trust evaluate
axiom reputation inspect
axiom reputation evaluate
axiom reputation evidence

axiom collective status
axiom collective vote
axiom collective consensus
axiom collective inspect

axiom knowledge share
axiom knowledge verify
axiom knowledge conflicts

axiom agent trace
axiom coordination trace
axiom contract trace
```

---

# 306. Core API

```axiom
agent.discover()
agent.capabilities()
agent.health()

agent.create_task()
agent.delegate()
agent.assign()

negotiation.create()
negotiation.propose()
negotiation.counter()
negotiation.accept()
negotiation.reject()

contract.create()
contract.validate()
contract.commit()
contract.amend()
contract.suspend()
contract.resume()
contract.terminate()

trust.evaluate()
reputation.evaluate()

team.create()
team.join()
team.leave()
team.assign_role()
team.elect_coordinator()

collective.vote()
collective.consensus()
collective.aggregate()

knowledge.share()
knowledge.verify()

agent.quarantine()
agent.recover()
agent.revoke()
```

---

# 307. Core invariants — identity

1. Every agent has unique identity within its authority domain.
2. Identity and capability are distinct.
3. Identity and authority are distinct.
4. Revoked identity cannot start new critical sessions.
5. Agent impersonation is prohibited.
6. Spawned agents receive explicit identity.
7. Identity rotation is auditable.
8. Identity migration is policy-controlled.
9. Remote identity must be authenticated where required.
10. Anonymous agents are allowed only under an explicit policy profile.

---

# 308. Core invariants — capability

11. Advertised capability is not authorization.
12. Capability claims may require verification.
13. Capability evidence has provenance.
14. Stale capability evidence is detectable.
15. Capability scope is explicit.
16. Capability cannot exceed system boundary.
17. Plugin capability cannot escape plugin isolation.
18. WASM capability follows host permissions.
19. Mobile capability follows platform permissions.
20. Capability changes are versioned.

---

# 309. Core invariants — delegation

21. Delegation cannot exceed delegator authority.
22. Delegation scope is explicit.
23. Delegation expiry is enforceable.
24. Delegation depth is bounded where required.
25. Revocation propagates.
26. Child agent cannot self-expand authority.
27. Delegation is auditable.
28. Delegation cannot bypass safety.
29. Delegation cannot bypass human approval.
30. Delegation cannot bypass policy.

---

# 310. Core invariants — negotiation

31. Proposal is not commitment.
32. Counter-proposal is not commitment.
33. Expired proposal cannot commit.
34. Rejected proposal cannot commit.
35. Negotiation participants are identified.
36. Negotiation scope is explicit.
37. Negotiation deadlines are enforced.
38. Negotiation cycles are bounded.
39. Hidden authority cannot be created by negotiation.
40. Negotiated terms cannot violate hard constraints.

---

# 311. Core invariants — contracts

41. Contract parties are authenticated.
42. Contract terms are canonicalizable.
43. Contract revision is immutable after commit.
44. Amendments reference parent revision.
45. Obligations are explicit.
46. Deadlines are explicit where required.
47. Contract rights cannot exceed authority.
48. Contract cannot override 664.
49. Contract cannot override 603.
50. Contract cannot override 639.
51. Contract breach is evidence-based.
52. Disputed breach is marked disputed.
53. Termination semantics are explicit.
54. Contract transfer requires authorization.
55. Duplicate commit is idempotent.
56. Conflicting commits cannot both become canonical.
57. Late results cannot silently commit.
58. Cancellation semantics are explicit.
59. Contract monitoring preserves provenance.
60. Contract history is auditable.

---

# 312. Core invariants — trust/reputation

61. Trust is contextual.
62. Reputation is contextual or explicitly global by policy.
63. Trust is not authority.
64. Reputation is not authority.
65. Trust has evidence.
66. Reputation has provenance.
67. Self-generated reputation cannot be blindly trusted.
68. Collusive reputation signals can be detected/marked.
69. Sybil resistance is policy-controlled.
70. Disputed evidence remains disputed.
71. Reputation updates are versioned.
72. Trust uncertainty is preserved.
73. Trust inheritance is not implicit.
74. Identity change has explicit trust semantics.
75. Trust cannot bypass safety.

---

# 313. Core invariants — collective decisions

76. Participants are explicit.
77. Voting rule is explicit.
78. Quorum is explicit.
79. Vote weight is explicit.
80. Consensus failure is not approval.
81. Majority is not truth.
82. Collective decision is not capability.
83. Collective decision is not authority.
84. Collective result still passes safety.
85. Collective result still passes policy.
86. Collective result still passes capability.
87. Human oversight can be required.
88. Evidence provenance is preserved.
89. Conflicting knowledge is represented.
90. Uncertainty is not erased by aggregation.

---

# 314. Core invariants — teams

91. Team membership is explicit.
92. Team role is explicit.
93. Team role is not authority.
94. Coordinator authority is scoped.
95. Coordinator failure has defined fallback.
96. Team dissolution handles active tasks.
97. Team policy cannot widen parent constraints.
98. Team members cannot silently join critical workflow.
99. Role revocation is propagated.
100. Team state is auditable.

---

# 315. Core invariants — distributed execution

101. Remote messages are authenticated when required.
102. Critical messages are integrity-protected.
103. Replay protection is enforced where required.
104. Message freshness is explicit.
105. Protocol version is negotiated.
106. Unknown critical features fail safely.
107. Network partition behavior is defined.
108. Duplicate delivery is handled.
109. Idempotency is explicit.
110. Exactly-once is never implied without guarantee.
111. Late results are handled.
112. Cancellation races are deterministic.
113. Timeouts are explicit.
114. Retry policy is bounded.
115. Irreversible actions require special retry policy.

---

# 316. Core invariants — spawning

116. Agent spawning requires authority.
117. Spawn budget is enforceable.
118. Spawn depth can be bounded.
119. Spawn storm is prevented.
120. Spawned identity is distinct.
121. Spawned agent inherits only allowed constraints.
122. Child cannot widen parent authority.
123. Self-replication is disabled by default in strict profiles.
124. Agent retirement cleans temporary state.
125. Agent migration is validated.

---

# 317. Core invariants — safety/governance

126. 666 cannot bypass 664.
127. 666 cannot bypass 603.
128. 666 cannot bypass 639.
129. 666 cannot bypass 665.
130. 666 cannot bypass 647.
131. Collective consensus cannot remove hard safety constraints.
132. Contract cannot authorize unsafe action.
133. Trust cannot authorize unsafe action.
134. Reputation cannot authorize unsafe action.
135. Coordinator cannot authorize unsafe action.
136. Agent delegation cannot authorize unsafe action.
137. Human approval remains governed by 665.
138. Safety incidents propagate to 664.
139. Governance incidents propagate to 647.
140. Evaluation evidence propagates to 663.

---

# 318. Core invariants — knowledge

141. Shared knowledge has provenance.
142. Knowledge conflicts are explicit.
143. Unverified knowledge is marked.
144. Critical decisions can require verification.
145. Memory access follows 650 policy.
146. Cross-tenant knowledge isolation is enforced.
147. Knowledge poisoning can be detected/flagged.
148. Reputation evidence cannot be silently altered.
149. Corrections preserve history.
150. Derived knowledge retains source references where required.

---

# 319. Core invariants — compiler

151. Invalid delegation graph is rejected.
152. Impossible quorum is rejected.
153. Missing contract party authority is detected.
154. Contract obligations must have executable or externally fulfilled semantics.
155. Unbounded recursive spawn is rejected in strict profiles.
156. Unbounded negotiation loop is rejected where statically detectable.
157. Invalid role assignment is detected.
158. Impossible escalation path is detected.
159. Unknown protocol version fails explicitly.
160. Invalid contract revision reference is rejected.
161. Unsafe retry of irreversible action is rejected in strict profiles.
162. Missing safety profile is detected for critical tasks.
163. Invalid human oversight requirement is detected.
164. Capability/role mismatch is detected.
165. Contract policy conflict is detected where statically knowable.

---

# 320. Core invariants — runtime

166. Agent identity is checked at critical boundaries.
167. Capability is checked before execution.
168. Authority is checked before commitment.
169. Safety is rechecked before critical execution.
170. Contract revision is validated.
171. Delegation is validated.
172. Approval freshness is validated where required.
173. Quorum is evaluated atomically where required.
174. Revoked agents are prevented from new critical work.
175. Quarantined agents follow restricted policy.
176. Duplicate task execution follows idempotency semantics.
177. Late results cannot violate cancellation semantics.
178. Contract breach generates traceable event.
179. Agent failure triggers defined recovery.
180. Coordination state survives required failures.

---

# 321. Core invariants — observability

181. Agent actions are attributable.
182. Contract events are traceable.
183. Negotiation revisions are traceable.
184. Delegations are traceable.
185. Trust updates are traceable.
186. Reputation updates are traceable.
187. Collective decisions preserve votes where policy permits.
188. Safety events are linked to originating agent.
189. Human interventions are linked through 665.
190. Evaluation results are linked through 663.

---

# 322. Core invariants — privacy

191. Agent data access follows 640.
192. Contract data is scoped.
193. Negotiation data can be private.
194. Reputation evidence access is controlled.
195. Trust evidence access is controlled.
196. Cross-tenant discovery is restricted.
197. Shared memory follows access policy.
198. Human data remains governed by 665/640.
199. Training reuse follows 662 governance.
200. Logs follow retention policy.

---

# 323. Acceptance criteria

Implementation is complete only when:

- agent lifecycle works locally and remotely;
- identity and capability are separated;
- delegation is bounded;
- negotiation is versioned;
- contracts are immutable/revisioned;
- obligations are monitored;
- contract breach is observable;
- trust is contextual;
- reputation is evidence-backed;
- teams can form/dissolve;
- coordinator failure is recoverable;
- collective voting/consensus works;
- conflicting knowledge is represented;
- distributed retries are safe;
- agent spawning is bounded;
- quarantine/revocation works;
- human oversight integrates with 665;
- safety integrates with 664;
- policy integrates with 639;
- capability integrates with 603;
- evaluation integrates with 663;
- governance integrates with 647;
- ≥2,800 automated tests pass;
- deterministic conformance tests exist for every critical state machine.

---

# 324. Canonical architecture

```text
                         ┌───────────────────────┐
                         │       Human 665       │
                         │ oversight / authority │
                         └───────────┬───────────┘
                                     │
                                     ▼
┌──────────┐                 ┌─────────────────────┐
│   661    │                 │       666           │
│ Goals    │───────────────► │ Multi-Agent Runtime │
└──────────┘                 └──────────┬──────────┘
                                        │
             ┌──────────────────────────┼──────────────────────┐
             │                          │                      │
             ▼                          ▼                      ▼
       Discovery                  Negotiation              Contracts
             │                          │                      │
             ▼                          ▼                      ▼
       Capability                   Proposals              Obligations
             │                          │                      │
             └──────────────────────────┼──────────────────────┘
                                        ▼
                              Trust / Reputation
                                        │
                                        ▼
                              Collective Decision
                                        │
                         ┌──────────────┼──────────────┐
                         ▼              ▼              ▼
                       603            639            664
                    Capability      Policy          Safety
                         │              │              │
                         └──────────────┼──────────────┘
                                        ▼
                                    Execute
                                        │
                                        ▼
                                      663
                                   Evaluate
                                        │
                                        ▼
                                      647
                                   Govern
```

---

# 325. Canonical multi-agent lifecycle

```text
DISCOVER
   ↓
IDENTIFY
   ↓
VERIFY CAPABILITY
   ↓
SELECT
   ↓
NEGOTIATE
   ↓
CONTRACT
   ↓
DELEGATE
   ↓
EXECUTE
   ↓
MONITOR
   ↓
VERIFY
   ↓
COMPLETE
   ↓
UPDATE EVIDENCE
   ↓
UPDATE TRUST / REPUTATION
```

---

# 326. Canonical critical-action lifecycle

```text
Agent Proposal
      ↓
Goal / Plan
      ↓
Capability Check
      ↓
Authority Check
      ↓
Contract Check
      ↓
Safety Check 664
      ↓
Human Oversight 665
      ↓
Execution
      ↓
Postcondition
      ↓
Independent Evaluation 663
      ↓
Contract Completion
```

---

# 327. Critical distinction

Axiom phải giữ bốn khái niệm riêng biệt:

```text
Capability
Authority
Trust
Reputation
```

Không được collapse thành:

```text
"agent được tin tưởng"
```

và coi đó là authorization.

---

# 328. Collective intelligence principle

Collective intelligence trong Axiom là:

```text
N agents
+
communication
+
specialization
+
coordination
+
evidence
+
aggregation
```

không phải:

```text
N agents
→ automatically smarter
```

---

# 329. Collective safety principle

Nếu 100 agents cùng đồng ý một action:

```text
100 × approval
```

không làm mất:

```text
664 hard safety constraint
```

---

# 330. Collective authority principle

Nếu 100 agents cùng vote:

```text
100 votes
```

không tự tạo:

```text
system authority
```

Authority vẫn đến từ:

```text
603
639
665
647
```

---

# 331. Collective epistemic principle

Consensus:

```text
agreement
```

không đồng nghĩa:

```text
truth
```

Axiom phải giữ:

```text
consensus
confidence
evidence
uncertainty
```

tách biệt.

---

# 332. Final responsibility map

```text
603 = CAPABILITY
639 = POLICY / AUTHORITY
644 = INDIVIDUAL AGENT
661 = OBJECTIVE / GOAL
662 = LEARNING / ADAPTATION
663 = EVALUATION
664 = SAFETY ENFORCEMENT
665 = HUMAN CONTROL
666 = MULTI-AGENT COORDINATION
647 = GOVERNANCE
```

---

# 333. Final architectural contract

BOOTSTRAP-666 establishes:

> **Agents may cooperate, negotiate, delegate, contract, trust, vote, share knowledge and form collective execution structures, but no collective mechanism can silently manufacture capability, authority, safety exemption, human approval, or governance authority.**

---

# 334. Completion status

**BOOTSTRAP-666 — COMPLETE**

The Axiom architecture now has:

```text
Individual AI
      ↓
Goals / Objectives
      ↓
Planning
      ↓
Evaluation
      ↓
Safety
      ↓
Human Oversight
      ↓
Multi-Agent Coordination
      ↓
Collective Intelligence
```

với các boundary authority rõ ràng giữa từng layer.
:::

**Task kế tiếp:** **BOOTSTRAP-667 — Native AI Civilization / Organization Runtime: Organizations, Institutions, Roles, Governance Structures, Membership, Rules, Resource Allocation, Collective Memory, Institutional Decision-Making & Organizational Lifecycle 5.0.**