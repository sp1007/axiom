BOOTSTRAP-658 tiếp tục tầng trên 657, tập trung vào **social intelligence và collective intelligence**, đồng thời giữ ranh giới rõ với agent orchestration 644, cognitive executive 657, knowledge graph 645, memory 650 và distributed coordination 630–637.

:::writing{variant="document" id="58321" title="BOOTSTRAP-658 — Native AI Social Intelligence, Theory of Mind, Multi-Agent Interaction, Communication, Negotiation, Cooperation, Competition, Social Memory & Collective Intelligence Runtime 5.0"}

# BOOTSTRAP-658
## Native AI Social Intelligence, Theory of Mind, Multi-Agent Interaction, Communication, Negotiation, Cooperation, Competition, Social Memory & Collective Intelligence Runtime 5.0

**Status:** COMPLETE  
**Layer:** Native AI Social / Multi-Agent Intelligence  
**Depends on:** BOOTSTRAP-600 → BOOTSTRAP-657.

---

# 1. Mục tiêu

658 bổ sung cho Axiom khả năng biểu diễn và điều phối **nhiều tác nhân có trạng thái, mục tiêu, niềm tin, năng lực và lợi ích khác nhau**.

Nó hỗ trợ:

```text
Agent
  ↓
Other-Agent Model
  ↓
Social Context
  ↓
Communication
  ↓
Coordination
  ↓
Negotiation
  ↓
Cooperation / Competition
  ↓
Collective Decision
  ↓
Collective Action
```

658 không giả định rằng agent khác có "tâm trí" giống con người.

Khái niệm **Theory of Mind** trong Axiom chỉ là mô hình hóa computational:

```text
what another agent may know
what another agent may believe
what another agent may observe
what another agent may intend
what another agent may prefer
what another agent may do
```

Tất cả phải được biểu diễn như **belief/model**, không phải sự thật nội tại của agent kia.

---

# 2. Architectural Position

```text
650 Memory
651 Personalization
652 Planning
653 Probability / Causality
654 Symbolic Reasoning
655 World Model
656 Embodiment
657 Cognitive Executive
        ↓
       658
        ↓
644 Agent Runtime
630 Distributed Compute
631 Distributed Services
634 Event Bus
635 Coordination
637 Dynamic Policy
639 Policy
640 Governance
```

658 tập trung vào:

```text
social cognition
agent interaction
communication semantics
coordination
negotiation
collective intelligence
```

---

# 3. Những vấn đề 658 giải quyết

Một hệ multi-agent không thể chỉ là:

```text
agent A → message → agent B
```

Nó cần:

- identity;
- role;
- capabilities;
- beliefs;
- goals;
- commitments;
- trust metadata;
- communication protocols;
- shared context;
- private context;
- coordination;
- negotiation;
- conflict handling;
- delegation;
- reputation metadata;
- coalition;
- voting/aggregation;
- consensus boundary;
- collective planning;
- social memory;
- interaction history;
- theory-of-mind models;
- deception-awareness boundary;
- uncertainty;
- provenance.

---

# 4. Core Principle

658 phải phân biệt:

```text
Agent Identity
Agent Capability
Agent Goal
Agent Belief
Agent Observation
Agent Statement
Agent Intention
Agent Commitment
Agent Action
Agent Reputation
Agent Trust Assessment
```

Không được coi:

```text
statement == truth
belief == fact
prediction == intention
intention == commitment
commitment == action
```

---

# 5. Core Types

```text
SocialAgent
AgentModel
AgentProfile
AgentRole
AgentCapability

SocialContext
Interaction
InteractionId
InteractionSession

Message
MessageId
MessageEnvelope
CommunicationChannel
Protocol

BeliefModel
OtherAgentBelief
OtherAgentGoal
OtherAgentIntent
OtherAgentCapability

Commitment
SocialCommitment
Agreement
Contract

TrustAssessment
TrustEvidence
Reputation
ReputationRecord

Negotiation
NegotiationSession
Proposal
CounterProposal
Offer
Constraint
UtilityModel
PreferenceModel

Coalition
Team
Group
Alliance
RoleAssignment

CoordinationPlan
SharedGoal
SharedTask

CollectiveDecision
DecisionRule
Vote
Ballot
Aggregation

SocialMemory
InteractionHistory
Relationship
RelationshipState

SocialPrediction
BehaviorHypothesis
SocialScenario

CollectiveKnowledge
SharedBelief
SharedContext
KnowledgeContribution

Conflict
ConflictState
ConflictResolution

SocialPolicy
InteractionPolicy
CommunicationPolicy
```

---

# 6. SocialAgent

```axiom
agent SocialAgent:
    identity
    capabilities
    goals
    communication
    policy
```

Agent có thể là:

```text
human
AI
robot
service
organization
simulation entity
```

658 không giả định species hoặc implementation.

---

# 7. Agent Identity

Identity đến từ 627.

658 chỉ tham chiếu:

```text
agent_id
identity_revision
session_id
```

---

# 8. Agent Capability

Capability mô tả:

```text
can_read
can_write
can_execute
can_observe
can_move
can_compute
can_delegate
```

Nhưng capability authority vẫn thuộc 603.

---

# 9. Agent Model

658 cho phép một agent xây model về agent khác:

```text
AgentModel:
    agent_id
    observed_capabilities
    observed_goals
    beliefs
    intentions
    behavior_model
    uncertainty
    evidence
```

---

# 10. Model ≠ Actual Agent State

Invariant:

```text
AgentModel != OtherAgentActualState
```

Agent A không thể đọc trực tiếp nội tâm agent B trừ khi B công khai thông tin.

---

# 11. Theory of Mind

658 hỗ trợ:

```text
model(agent)
model(agent, believes)
model(agent, wants)
model(agent, knows)
model(agent, intends)
```

Các kết quả đều là hypotheses/beliefs.

---

# 12. Nested Beliefs

Có thể biểu diễn:

```text
A believes B believes X
```

nhưng phải giới hạn depth:

```text
depth = 1
depth = 2
...
```

để tránh unbounded recursive reasoning.

---

# 13. Theory-of-Mind Budget

```text
ToMBudget:
    max_agents
    max_depth
    max_hypotheses
    max_time
```

---

# 14. Social Observation

Observation về agent khác:

```text
speech
action
reaction
timing
choice
public_state
```

không tự động chứng minh hidden intent.

---

# 15. Social Inference

653 có thể cung cấp probabilistic inference.

Ví dụ:

```text
P(intent = A | observed_behavior)
```

658 giữ:

```text
inferred
confidence
evidence
assumptions
```

---

# 16. Social Prediction

655 có thể dự đoán environment.

658 thêm:

```text
SocialPrediction
```

dành cho hành vi của agent khác.

Ví dụ:

```text
predicted_action
predicted_goal
predicted_response
```

---

# 17. Behavioral Model

Các loại:

```text
RuleBased
Probabilistic
Learned
GameTheoretic
Historical
Hybrid
```

---

# 18. Social Model Revision

Mọi model về agent khác phải có:

```text
revision
timestamp
evidence_window
model_provider
```

---

# 19. Social Model Drift

Nếu hành vi thực tế khác prediction:

```text
model_error
```

có thể kích hoạt:

```text
re-estimation
replanning
reflection
```

---

# 20. Communication

Communication API:

```axiom
send(agent, message)
receive()
broadcast(group, message)
request(agent, request)
reply(message)
```

---

# 21. Message Structure

```text
Message:
    id
    sender
    receiver
    type
    payload
    timestamp
    correlation_id
    expiration
    priority
```

---

# 22. Message Types

```text
Inform
Request
Query
Response
Proposal
CounterProposal
Commitment
Warning
Alert
Delegation
Acknowledgement
Cancellation
Status
Negotiation
```

---

# 23. Message Semantics

Message có thể là:

```text
fact_claim
belief_statement
request
proposal
commitment
opinion
prediction
```

Semantics phải explicit.

---

# 24. Communication Reliability

658 hỗ trợ:

```text
AtMostOnce
AtLeastOnce
ExactlyOnceBoundary
BestEffort
Ordered
Unordered
```

Provider thực hiện transport.

---

# 25. Transport Boundary

Transport nằm ở:

```text
604 IPC
609 networking
634 event bus
```

658 chỉ định nghĩa semantic communication.

---

# 26. Communication Protocol

Protocol:

```text
name
version
messages
states
timeouts
retries
termination
```

---

# 27. Protocol State Machine

Ví dụ:

```text
Idle
 ↓
RequestSent
 ↓
Proposal
 ↓
CounterProposal
 ↓
Agreement
 ↓
Committed
```

---

# 28. Protocol Validation

Protocol message sai state phải bị reject.

---

# 29. Shared Context

Multi-agent session có:

```text
SharedContext
PrivateContext
PublicContext
RestrictedContext
```

---

# 30. Information Visibility

Mỗi information item có:

```text
public
private
restricted
role_visible
capability_visible
```

---

# 31. Information Boundary

Agent không được truy cập private context của agent khác chỉ vì biết agent ID.

---

# 32. Information Disclosure

Disclosure phải qua:

```text
capability
policy
consent/authorization
```

tùy application.

---

# 33. Shared Belief

Một nhóm có thể giữ:

```text
SharedBelief
```

nhưng provenance của từng contributor phải giữ nguyên.

---

# 34. Belief Agreement

Không được coi:

```text
3 agents believe X
```

là:

```text
X is true
```

---

# 35. Belief Conflict

```text
A → X
B → not-X
```

658 biểu diễn:

```text
Conflict
```

và có thể gọi:

```text
653 inference
654 reasoning
```

để xử lý.

---

# 36. Knowledge Contribution

Agent có thể đóng góp:

```text
fact
observation
hypothesis
analysis
prediction
```

Mỗi loại có epistemic status.

---

# 37. Collective Knowledge

645 có thể lưu graph.

650 có thể lưu memory.

658 quản lý:

```text
who contributed what
when
under which context
with what confidence
```

---

# 38. Social Memory

```text
SocialMemory:
    interactions
    agreements
    conflicts
    commitments
    outcomes
    relationship_state
```

---

# 39. Interaction History

```text
Interaction:
    participants
    context
    messages
    decisions
    actions
    outcomes
```

---

# 40. Relationship

Relationship không phải human psychological claim.

Nó là computational state:

```text
cooperation_history
communication_frequency
agreement_rate
conflict_rate
reliability_evidence
shared_goals
```

---

# 41. Relationship State

Ví dụ:

```text
Unknown
Observed
Cooperative
Competitive
Coordinating
Conflict
Suspended
```

Đây là application state, không phải intrinsic judgment về agent.

---

# 42. Trust

Trust được biểu diễn như:

```text
TrustAssessment
```

không phải absolute truth.

---

# 43. Trust Evidence

```text
successful_commitments
failed_commitments
verified_outputs
communication_reliability
policy_compliance
```

---

# 44. Trust Score

Không bắt buộc một scalar.

Có thể dùng vector:

```text
technical_reliability
communication_reliability
commitment_reliability
data_quality
```

---

# 45. Trust Uncertainty

```text
estimate
confidence
sample_count
time_window
```

---

# 46. Trust Decay

Trust evidence có thể decay theo thời gian:

```text
recent evidence
```

nhưng policy quyết định decay function.

---

# 47. Reputation

Reputation là aggregated public/social evidence.

Không được coi reputation là identity truth.

---

# 48. Reputation Sources

```text
direct_interaction
verified_record
third_party_report
group_observation
historical_record
```

---

# 49. Reputation Provenance

Mỗi reputation update phải giữ source.

---

# 50. Commitment

Agent có thể tạo:

```text
Commitment:
    actor
    action
    conditions
    deadline
```

---

# 51. Commitment State

```text
Proposed
Accepted
Active
Fulfilled
Broken
Cancelled
Expired
```

---

# 52. Commitment Verification

Fulfillment phải được kiểm tra bằng observable evidence.

---

# 53. Agreement

Agreement gồm:

```text
participants
terms
constraints
deadlines
commitments
revision
```

---

# 54. Contract Boundary

Formal legal contracts không thuộc core 658.

658 chỉ cung cấp computational agreement structure.

---

# 55. Negotiation

Negotiation:

```text
participants
issues
preferences
constraints
offers
counteroffers
utility
deadline
```

---

# 56. Negotiation Session

```text
Created
Opening
Negotiating
Agreement
Rejected
Expired
Escalated
```

---

# 57. Proposal

```text
Proposal:
    terms
    constraints
    validity
    proposer
    utility_estimate
```

---

# 58. Counterproposal

Counterproposal phải reference proposal trước.

---

# 59. Negotiation Utility

Có thể sử dụng:

```text
652 objective
651 preferences
653 uncertainty
```

---

# 60. Utility Privacy

Agent không phải công khai toàn bộ utility function.

---

# 61. Private Preferences

Negotiation có thể sử dụng:

```text
private preference
revealed preference
declared constraint
```

và phải phân biệt.

---

# 62. Negotiation Strategies

```text
Concession
Competitive
Cooperative
DeadlineAware
UtilityBased
RuleBased
Auction
Bargaining
```

Không hard-code một strategy thành mặc định universal.

---

# 63. Negotiation Constraints

Hard constraints:

```text
must_hold
```

Soft constraints:

```text
preferred
```

---

# 64. Pareto Analysis

652 có thể đánh giá Pareto frontier.

658 chỉ dùng kết quả để negotiation.

---

# 65. Agreement Verification

Trước commit:

```text
validate terms
validate capabilities
validate constraints
validate policy
```

---

# 66. Negotiation Failure

Reasons:

```text
NoOverlap
Timeout
PolicyDenied
CapabilityMismatch
ConstraintConflict
ParticipantWithdrawn
```

---

# 67. Human Negotiation

658 có thể đại diện communication layer cho human-in-the-loop.

Không tự thay đổi authority.

---

# 68. Cooperation

Cooperation là:

```text
multiple agents
shared goal
coordinated actions
```

---

# 69. Shared Goal

```text
SharedGoal:
    owner
    participants
    objective
    constraints
    success_conditions
```

---

# 70. Shared Task

```text
SharedTask:
    subtasks
    dependencies
    assignments
```

---

# 71. Task Allocation

652 có thể solve:

```text
agent-task assignment
```

658 cung cấp social constraints:

```text
capability
availability
role
commitment
preference
```

---

# 72. Team

```text
Team:
    members
    roles
    shared_goal
    coordination_protocol
```

---

# 73. Role

```text
Role:
    responsibilities
    capabilities
    constraints
```

---

# 74. Role Assignment

Assignment phải kiểm tra:

```text
capability
authority
availability
conflicts
```

---

# 75. Coalition

Coalition là temporary group cho objective cụ thể.

```text
Coalition:
    members
    objective
    duration
    commitments
```

---

# 76. Coalition Formation

Có thể dùng:

```text
rule
optimization
negotiation
auction
```

---

# 77. Coalition Dissolution

Khi:

```text
goal completed
goal failed
deadline
member withdrawal
policy change
```

---

# 78. Competition

658 hỗ trợ competitive environments.

```text
Agent A goal
vs
Agent B goal
```

Không giả định competition là inherently desirable.

---

# 79. Competitive Model

Có thể sử dụng:

```text
game-theoretic provider
652 optimization
653 probabilistic reasoning
655 world model
```

---

# 80. Game Model

```text
Game:
    players
    actions
    observations
    utility
    information
    state
```

---

# 81. Information Structure

```text
PerfectInformation
PartialInformation
PrivateInformation
AsymmetricInformation
```

---

# 82. Game-Theoretic Boundary

658 không bắt buộc implementation của Nash equilibrium.

Provider boundary có thể hỗ trợ:

```text
Nash
Stackelberg
minimax
extensive-form
repeated games
```

---

# 83. Strategic Uncertainty

Agent model phải distinguish:

```text
uncertainty about world
uncertainty about agent
uncertainty about agent's model of me
```

---

# 84. Recursive Social Reasoning

Có thể biểu diễn:

```text
A models B
B models A
```

nhưng depth bounded.

---

# 85. Social Simulation

648 có thể generate:

```text
multiple agents
interaction scenarios
social outcomes
```

658 cung cấp agent interaction semantics.

---

# 86. Social Scenario

```text
SocialScenario:
    agents
    roles
    initial_beliefs
    goals
    environment
    interaction_protocol
```

---

# 87. Social Rollout

655/648 có thể simulate:

```text
state
→ agent decisions
→ interactions
→ state transition
```

---

# 88. Reality vs Simulation

Không được coi simulation outcome là real social evidence.

---

# 89. Collective Decision

658 hỗ trợ:

```text
CollectiveDecision
```

---

# 90. Decision Rules

```text
Unanimity
Majority
WeightedVote
RankedChoice
Consensus
Quorum
DelegatedVote
Randomized
```

Rule là configurable.

---

# 91. Voting

```text
Vote:
    voter
    choice
    weight
    timestamp
    proof
```

---

# 92. Voting Weight

Weight phải đến từ explicit policy.

Không tự suy ra authority từ reputation.

---

# 93. Quorum

```text
minimum_participants
minimum_weight
```

---

# 94. Consensus

Consensus không đồng nghĩa:

```text
truth
```

Nó chỉ biểu thị agreement theo protocol.

---

# 95. Collective Belief

```text
CollectiveBelief:
    proposition
    contributors
    evidence
    aggregation
    confidence
```

---

# 96. Aggregation

Các phương pháp:

```text
majority
weighted
Bayesian
confidence-weighted
evidence-based
```

Provider boundary cho phương pháp phức tạp.

---

# 97. Wisdom-of-Crowds Boundary

Aggregation có thể tận dụng nhiều independent estimates.

Nhưng correlation giữa agents phải được xét.

---

# 98. Correlated Reports

Nếu tất cả agents lấy thông tin từ cùng source:

```text
A → source X
B → source X
C → source X
```

không được coi như 3 independent evidence points.

---

# 99. Evidence Independence

653 có thể đánh giá:

```text
conditional dependence
```

658 giữ provenance.

---

# 100. Information Cascades

Social inference có thể bị cascade:

```text
A says X
B copies A
C copies B
```

Hệ thống phải giữ source lineage để tránh đếm duplicate evidence.

---

# 101. Groupthink Detection Boundary

658 có thể phát hiện metadata:

```text
low_independence
high_agreement
low_evidence_diversity
```

Nhưng không tự gán psychological diagnosis.

---

# 102. Diversity

Collective reasoning có thể tối ưu:

```text
source diversity
model diversity
strategy diversity
```

---

# 103. Ensemble Agents

Nhiều agent có thể giải cùng problem:

```text
Agent1 → solution A
Agent2 → solution B
Agent3 → solution C
```

652/653 aggregate.

---

# 104. Debate

Optional protocol:

```text
Proposal
→ Critique
→ Defense
→ Revision
→ Verification
```

---

# 105. Debate Safety

Debate output là evidence/analysis, không phải authority.

---

# 106. Critic Agent

Role:

```text
Critic
Verifier
Planner
Researcher
Executor
Observer
```

---

# 107. Role Separation

Một agent có thể giữ nhiều role, nhưng role boundaries phải explicit.

---

# 108. Cross-Checking

658 hỗ trợ:

```text
independent_review
```

trước decision quan trọng.

---

# 109. Redundancy

Critical task có thể yêu cầu:

```text
N independent agents
```

nhưng independence phải được đánh giá.

---

# 110. Collective Planning

Pipeline:

```text
SharedGoal
↓
Task Decomposition
↓
Capability Discovery
↓
Negotiation
↓
Task Allocation
↓
Individual Plans
↓
Conflict Detection
↓
Coordination
↓
Execution
```

---

# 111. Coordination Plan

```text
CoordinationPlan:
    tasks
    owners
    dependencies
    synchronization_points
    fallback
```

---

# 112. Synchronization Point

```text
Barrier
Checkpoint
Handoff
ConsensusPoint
CommitPoint
```

---

# 113. Handoff

Agent A → Agent B:

```text
task state
context
artifacts
assumptions
constraints
deadline
```

---

# 114. Handoff Validation

B phải xác nhận:

```text
received
understood
capable
accepted
```

---

# 115. Agent Failure

Nếu agent chết:

```text
task reassignment
fallback
recovery
human escalation
```

---

# 116. Distributed Coordination Boundary

635 handles:

```text
leader election
membership
consensus
placement
```

658 handles:

```text
social coordination semantics
```

---

# 117. Event Bus Integration

634 transport:

```text
social events
group events
coordination events
```

---

# 118. Service Mesh Integration

631 transport/discovery.

658 defines semantics, not network routing.

---

# 119. Conflict

Conflict types:

```text
GoalConflict
ResourceConflict
ScheduleConflict
BeliefConflict
PlanConflict
RoleConflict
CommitmentConflict
InformationConflict
```

---

# 120. Conflict Resolution

Strategies:

```text
Policy
Negotiation
Optimization
Priority
Mediation
HumanDecision
Abort
```

---

# 121. Mediation

Optional mediator:

```text
MediatorAgent
```

Mediator must not secretly modify participant commitments.

---

# 122. Conflict Provenance

Record:

```text
participants
claims
goals
constraints
resolution_method
result
```

---

# 123. Social Deadlock

Examples:

```text
A waits for B
B waits for A
```

658 must detect coordination cycles.

---

# 124. Deadlock Resolution

```text
timeout
priority
break_cycle
reassign
escalate
```

---

# 125. Social Liveness

Coordination protocols must define:

```text
timeout
retry
termination
failure state
```

---

# 126. Reputation Feedback

After interaction:

```text
outcome
→ evidence
→ relationship state
→ optional reputation update
```

---

# 127. Reputation Update

Must not automatically alter security permissions.

---

# 128. Trust vs Authorization

Critical invariant:

```text
TrustAssessment != Capability
```

---

# 129. Social Manipulation Awareness

658 may mark:

```text
inconsistent_claims
conflicting_commitments
unverified_claims
coordination_anomaly
```

without making unsupported psychological claims.

---

# 130. Deception Modeling

Deception can be represented as:

```text
agent may intentionally provide false information
```

as a scenario hypothesis.

Actual deception requires evidence.

---

# 131. Strategic Misrepresentation

Model:

```text
Claim
ObservedReality
Discrepancy
Evidence
```

---

# 132. No Automatic Mind Reading

Observed behavior cannot automatically prove:

```text
intent
belief
emotion
motive
```

---

# 133. Social Emotion Boundary

658 may support computational signals:

```text
urgency
frustration_signal
sentiment_signal
```

when supplied by 649/643.

These remain uncertain observations.

---

# 134. Social Personalization

651 can provide:

```text
communication preferences
interaction history
preferred formats
```

658 uses them only within policy.

---

# 135. Human Communication

658 supports:

```text
conversation state
turn taking
context
commitments
clarifications
```

---

# 136. Conversation State

```text
Open
WaitingForHuman
WaitingForAgent
Resolved
Escalated
Cancelled
```

---

# 137. Clarification

If ambiguity prevents safe execution:

```text
ClarificationRequest
```

---

# 138. Ambiguity

658 can represent:

```text
ambiguous_reference
ambiguous_goal
ambiguous_authority
ambiguous_constraint
```

---

# 139. Clarification Priority

Critical ambiguity must be resolved before irreversible action.

---

# 140. Social Context Window

Conversation context may combine:

```text
recent messages
social memory
current goal
current world state
commitments
policies
```

---

# 141. Social Memory Retention

650 governs retention.

658 determines which interaction artifacts are useful.

---

# 142. Forgetting

Social memory may expire according to:

```text
retention policy
privacy policy
application policy
```

---

# 143. Privacy

640 controls:

```text
personal data
interaction data
relationship data
```

---

# 144. Consent

Applications may require explicit consent before storing sensitive interaction state.

---

# 145. Data Minimization

658 should store only social metadata necessary for configured objectives.

---

# 146. Social Audit

Audit:

```text
participants
messages
agreements
decisions
commitments
permissions
outcomes
```

---

# 147. Collective Intelligence

Collective intelligence is represented as:

```text
multiple agents
+
information sharing
+
aggregation
+
coordination
+
feedback
```

Không giả định group intelligence là một conscious entity.

---

# 148. Collective Memory

Group memory:

```text
shared artifacts
shared facts
shared decisions
shared lessons
```

---

# 149. Collective Learning

Agents có thể share:

```text
experience
models
strategies
lessons
```

nhưng model lifecycle 647 vẫn kiểm soát production deployment.

---

# 150. Federated Social Learning

Có thể:

```text
local learning
→ aggregate metadata/model
```

với 610/647 security and governance.

---

# 151. Collective Skill

A team có thể có:

```text
skill
required_roles
execution_protocol
```

---

# 152. Team Skill

Ví dụ:

```axiom
team_skill rescue:
    requires:
        navigator
        operator
        observer
```

---

# 153. Skill Execution

652 selects team plan.

658 handles:

```text
role assignment
coordination
handoff
commitment
```

656 handles physical control if needed.

---

# 154. Social World Model

655 can contain:

```text
agents
roles
relationships
actions
environment
```

658 adds richer social semantics.

---

# 155. Social Prediction

Prediction output:

```text
predicted behavior
confidence
evidence
time horizon
```

---

# 156. Prediction Calibration

646 evaluates predictions against outcomes.

---

# 157. Agent Simulation

648 can instantiate simulated agents with:

```text
goals
beliefs
policies
behavior models
```

---

# 158. Sim-to-Real Social Gap

Simulation metadata must identify:

```text
simulation_assumption
behavior_model
domain_gap
```

---

# 159. Negotiation Simulation

Agent may simulate:

```text
possible offers
counteroffers
coalitions
```

before real negotiation.

---

# 160. No Silent External Communication

Simulation/debate does not send real messages unless explicitly authorized.

---

# 161. Communication Security

603/610 handle:

```text
identity
authentication
encryption
capabilities
```

---

# 162. Message Authorization

Every restricted message must pass policy/capability checks.

---

# 163. Message Integrity

Transport may provide:

```text
signature
MAC
sequence
nonce
```

---

# 164. Replay Protection

Protocol must support:

```text
message_id
sequence
expiration
nonce
```

where required.

---

# 165. Social Rate Limits

637/606 may limit:

```text
messages
negotiations
requests
broadcasts
```

---

# 166. Broadcast Safety

Broadcast requires explicit capability.

---

# 167. Group Membership

Membership states:

```text
Invited
Pending
Active
Suspended
Removed
Expired
```

---

# 168. Group Authority

Group membership does not automatically grant all member capabilities.

---

# 169. Group Policy

639 can define:

```text
who may join
who may vote
who may propose
who may execute
```

---

# 170. Collective Commit

A collective action can require:

```text
quorum
approval
commitment
policy
```

---

# 171. Two-Phase Collective Commit

Optional:

```text
Prepare
→ Validate
→ Commit
```

Useful for coordinated irreversible actions.

---

# 172. Partial Commit

If some agents commit and others fail:

```text
PartialCommit
```

must be explicit.

---

# 173. Compensation

629 provides saga/compensation.

658 can request:

```text
compensation_plan
```

---

# 174. Social Workflow

629 manages durable workflow.

658 manages:

```text
participant behavior
communication
negotiation
coordination
```

---

# 175. Collective Scheduling

635/652 schedule.

658 provides:

```text
participant availability
social commitments
handoffs
coordination barriers
```

---

# 176. Collective Resource Allocation

606 provides resource accounting.

652 solves allocation.

658 supplies social constraints and agreements.

---

# 177. Agent Availability

```text
Available
Busy
Committed
Offline
Unknown
```

---

# 178. Agent Load

```text
active_tasks
resource_load
deadline_pressure
```

---

# 179. Delegation Matching

Match task to agent based on:

```text
capability
availability
role
trust evidence
cost
deadline
```

No single scalar is mandatory.

---

# 180. Social Utility

Agent utility may include:

```text
task_value
cost
risk
relationship_objectives
future_coordination_value
```

---

# 181. Utility Privacy

Private utility functions remain private unless explicitly disclosed.

---

# 182. Bargaining

Negotiation provider may support:

```text
alternating_offers
deadline_bargaining
utility_bargaining
constraint_bargaining
```

---

# 183. Auction Boundary

Provider can support:

```text
English
Dutch
FirstPrice
SecondPrice
Combinatorial
```

658 only defines semantic interface.

---

# 184. Mechanism Metadata

```text
mechanism
rules
participants
bid_visibility
termination
winner_selection
```

---

# 185. Collective Optimization

652 may solve:

```text
maximize collective utility
```

subject to:

```text
individual constraints
group constraints
policy
```

---

# 186. Fairness Boundary

640/639 define governance requirements.

658 only exposes:

```text
allocation
weights
constraints
outcomes
```

---

# 187. Social Metrics

Metrics may include:

```text
coordination_latency
agreement_rate
commitment_success
communication_cost
task_completion
conflict_rate
information_diversity
```

---

# 188. No Universal Social Objective

Axiom does not hard-code:

```text
maximize cooperation
maximize competition
maximize trust
```

Applications specify objectives.

---

# 189. Social Benchmark

Benchmarks:

```text
negotiation success
coordination latency
task allocation efficiency
belief calibration
communication efficiency
conflict recovery
coalition stability
```

---

# 190. Collective Evaluation

646 can evaluate:

```text
individual agent
team
protocol
collective decision
```

---

# 191. Adversarial Agents

Simulation may include:

```text
ByzantineAgent
SelfInterestedAgent
UnreliableAgent
AdversarialAgent
```

as explicit test models.

---

# 192. Byzantine Boundary

635 handles distributed consensus semantics.

658 models social behavior around unreliable participants.

---

# 193. Robust Coordination

Collective plan can require:

```text
redundancy
fallback agents
alternative communication path
```

---

# 194. Agent Failure Recovery

If member fails:

```text
detect
→ update team state
→ reallocate task
→ notify members
→ continue/fallback
```

---

# 195. Communication Failure

If network unavailable:

```text
retry
alternate channel
local execution
safe stop
```

depending on policy.

---

# 196. Offline Coordination

Agents can use cached:

```text
commitments
plans
group state
```

but must mark staleness.

---

# 197. Stale Social State

Every shared state has:

```text
revision
timestamp
freshness
```

---

# 198. Split-Brain Social State

Distributed groups must detect:

```text
conflicting group revisions
```

---

# 199. Reconciliation

Use:

```text
635 consensus
637 policy
650 memory
652 conflict resolution
```

where applicable.

---

# 200. Compiler Annotations

```text
@social
@social_agent
@agent_model
@theory_of_mind
@belief_about
@intent_model
@social_prediction
@interaction
@message
@protocol
@conversation
@shared_context
@private_context
@social_memory
@relationship
@trust
@reputation
@commitment
@agreement
@negotiation
@proposal
@counterproposal
@cooperation
@competition
@team
@role
@coalition
@shared_goal
@shared_task
@coordination
@collective_decision
@vote
@consensus
@collective_belief
@collective_knowledge
@conflict
@mediation
@delegation
@handoff
@social_simulation
@social_prediction
@collective_learning
@collective_skill
```

---

# 201. Generated Metadata

```text
.axsocial
.axagentmodel
.axtom
.axinteraction
.axmessage
.axprotocol
.axconversation
.axsocialcontext
.axsocialmemory
.axrelationship
.axtrust
.axreputation
.axcommitment
.axagreement
.axnegotiation
.axcoalition
.axteam
.axcoordination
.axcollective
.axcollectivedecision
.axsocialconflict
.axsocialscenario
.axsocialtrace
```

---

# 202. Compiler IR

```text
SocialAgentCreate
AgentModelCreate
AgentModelUpdate
SocialObserve
SocialInfer
SocialPredict
SocialSend
SocialReceive
SocialBroadcast
ProtocolEnter
ProtocolTransition
ConversationOpen
ConversationClose

SharedContextCreate
SharedContextUpdate

CommitmentCreate
CommitmentAccept
CommitmentFulfill
CommitmentBreak

NegotiationOpen
ProposalCreate
ProposalAccept
ProposalReject
CounterProposal
NegotiationClose

TeamCreate
TeamJoin
TeamLeave
RoleAssign
TaskAllocate
TaskHandoff

CollectiveDecisionCreate
VoteCast
VoteAggregate
ConsensusCheck
CollectiveCommit

ConflictDetect
ConflictResolve
Mediate

TrustUpdate
ReputationUpdate
SocialMemoryWrite
CollectiveKnowledgeUpdate
SocialScenarioSimulate
```

---

# 203. Runtime Profiles

```text
AXSOCIAL_NONE
AXSOCIAL_CORE
AXSOCIAL_COMMUNICATION
AXSOCIAL_PROTOCOL
AXSOCIAL_TOM
AXSOCIAL_BELIEF
AXSOCIAL_PREDICTION
AXSOCIAL_MEMORY
AXSOCIAL_TRUST
AXSOCIAL_REPUTATION
AXSOCIAL_COMMITMENT
AXSOCIAL_NEGOTIATION
AXSOCIAL_COOPERATION
AXSOCIAL_COMPETITION
AXSOCIAL_TEAM
AXSOCIAL_COALITION
AXSOCIAL_COORDINATION
AXSOCIAL_COLLECTIVE
AXSOCIAL_CONSENSUS
AXSOCIAL_SIMULATION
AXSOCIAL_DISTRIBUTED
AXSOCIAL_HUMAN
AXSOCIAL_AGENT
AXSOCIAL_FULL
```

---

# 204. CLI

```text
axiom social inspect
axiom social trace
axiom social replay

axiom agent-model inspect
axiom agent-model compare
axiom agent-model predict

axiom social message send
axiom social message inspect

axiom social protocol inspect
axiom social protocol validate

axiom social relationship inspect
axiom social trust inspect
axiom social reputation inspect

axiom negotiation start
axiom negotiation inspect
axiom negotiation propose
axiom negotiation counter
axiom negotiation commit

axiom team create
axiom team inspect
axiom team assign
axiom team coordinate

axiom coalition create
axiom coalition inspect

axiom collective decide
axiom collective vote
axiom collective consensus

axiom social conflict inspect
axiom social conflict resolve

axiom social simulate
axiom social benchmark
```

---

# 205. Core Invariants

658 yêu cầu tối thiểu **140 invariants**.

Các invariant nền tảng:

1. Agent model không phải actual agent state.
2. Statement không phải fact.
3. Belief không phải fact.
4. Prediction không phải intention.
5. Intention không phải commitment.
6. Commitment không phải completed action.
7. Reputation không phải identity.
8. Trust không phải authorization.
9. Group agreement không phải truth.
10. Majority vote không phải truth.
11. Simulation không phải reality.
12. Social prediction phải có uncertainty.
13. Theory-of-mind inference phải giữ provenance.
14. Nested belief depth phải bounded.
15. Social inference không được đọc private state trái capability.
16. Private context không tự trở thành shared context.
17. Shared context phải có visibility policy.
18. Message phải có sender.
19. Restricted message phải có authorization.
20. Message replay phải được kiểm soát khi protocol yêu cầu.
21. Protocol state phải validated.
22. Invalid protocol transition phải bị reject.
23. Negotiation proposal phải có proposer.
24. Counterproposal phải reference proposal trước.
25. Agreement phải versioned.
26. Commitment phải có owner.
27. Commitment fulfillment phải có evidence.
28. Commitment failure phải observable.
29. Trust update phải có evidence.
30. Reputation update phải có provenance.
31. Trust không tự grant capability.
32. Reputation không tự grant capability.
33. Relationship state không phải psychological diagnosis.
34. Social emotion signal không phải fact.
35. Inferred intent không phải actual intent.
36. Inferred belief không phải actual belief.
37. Inferred goal không phải actual goal.
38. Agent availability phải có timestamp.
39. Shared state phải có revision.
40. Stale shared state phải detectable.
41. Group membership không tự grant authority.
42. Role assignment không tự grant security capability.
43. Delegation phải có scope.
44. Delegation không tự transfer all authority.
45. Team task allocation phải kiểm tra capability.
46. Team plan phải preserve task ownership.
47. Handoff phải preserve context.
48. Handoff phải preserve assumptions.
49. Handoff phải preserve deadlines.
50. Failed agent phải trigger configured recovery.
51. Collective decision rule phải explicit.
52. Vote weight phải derive từ explicit policy.
53. Quorum phải explicit.
54. Consensus phải distinguish với truth.
55. Collective belief phải preserve contributor provenance.
56. Correlated evidence không được silently count as independent.
57. Social evidence source lineage phải preserve.
58. Information cascade phải detectable where configured.
59. Social prediction phải record model revision.
60. Social model drift phải detectable.
61. Behavior mismatch không automatically imply deception.
62. Deception hypothesis phải retain uncertainty.
63. Strategic behavior must remain a model.
64. Competitive behavior does not authorize harmful action.
65. Cooperation does not bypass policy.
66. Negotiation does not bypass security.
67. Collective decision does not bypass policy.
68. Collective action must pass execution authority.
69. Simulation messages must not reach real agents.
70. Simulated commitments must be marked simulated.
71. Simulated reputation must not silently enter production.
72. Simulation evidence must remain synthetic.
73. Collective learning candidate != approved production model.
74. Social memory retention follows governance.
75. Privacy rules apply to interaction history.
76. Data minimization applies where configured.
77. Human communication state must preserve participant identity.
78. Human instruction remains subject to authorization.
79. Clarification is required where configured ambiguity blocks safe action.
80. Unknown participant state must remain unknown.
81. Missing information must not become false information.
82. Conflicting reports must remain distinguishable.
83. Aggregation must expose method.
84. Aggregation must expose weighting.
85. Aggregation must expose evidence window.
86. Aggregation must expose participant set.
87. Social metrics must identify measurement period.
88. Social benchmarks must identify scenario population.
89. Social models must expose assumptions.
90. Agent-model updates must be versioned.
91. Social memory updates must be traceable.
92. Collective memory must preserve contributor identity.
93. Collective knowledge must preserve source epistemic status.
94. Shared belief cannot silently overwrite private belief.
95. Private belief cannot silently enter public belief.
96. Negotiation utility may remain private.
97. Private preference must not be inferred as declared preference without marking inference.
98. Revealed preference must preserve observation source.
99. Auction mechanism must be explicit.
100. Mechanism rules must be immutable during a committed round unless protocol allows.
101. Collective commit must validate participants.
102. Partial commit must be observable.
103. Compensation must be explicit.
104. Distributed coordination must expose network state.
105. Social deadlocks must be detectable.
106. Coordination cycles must have timeout/break policy.
107. Multi-agent retries must respect idempotency.
108. Duplicate messages must be safely handled.
109. Event ordering must be explicit.
110. Correlation IDs must remain stable.
111. Agent failure must not silently transfer commitments.
112. Agent replacement must be authorized.
113. Role replacement must preserve policy.
114. Coalition membership must be explicit.
115. Coalition dissolution must be observable.
116. Group state must not be treated as a conscious entity.
117. Collective intelligence must be computational metadata only.
118. Theory of mind must not claim mind access.
119. Metacognitive confidence about another agent must remain a belief.
120. Social model confidence must not become truth.
121. Prediction success must be measured against observed outcomes.
122. Social prediction cannot mutate environment.
123. Social simulation cannot execute real side effects.
124. Social trace must not expose restricted information without authorization.
125. Communication logs obey retention policy.
126. Trust evidence must preserve time.
127. Reputation evidence must preserve source.
128. Reputation decay must be policy-defined.
129. Collective voting must preserve ballot integrity.
130. Consensus failure must be explicit.
131. Negotiation timeout must be explicit.
132. Negotiation termination must be explicit.
133. Agreement expiration must be explicit.
134. Commitment expiration must be explicit.
135. Social conflict resolution must preserve original conflict.
136. Mediation cannot silently modify participant state.
137. Mediator authority must be explicit.
138. Collective plan must preserve individual constraints.
139. Collective optimization must not silently discard participant constraints.
140. Social execution must pass 603/639.
141. Physical action must pass 656 safety.
142. Cognitive recommendation does not equal collective authorization.
143. Agent communication does not equal agent permission.
144. Social model cannot override world-model observation.
145. World-model observation cannot directly prove private intention.

---

# 206. Acceptance Criteria

Mục tiêu tối thiểu:

```text
Social Core                       >= 60
Agent Modeling                    >= 70
Theory of Mind                    >= 80
Communication                     >= 80
Protocol                          >= 70
Shared/Private Context            >= 60
Social Memory                     >= 65
Relationship Modeling             >= 60
Trust/Reputation                  >= 70
Commitment/Agreement              >= 75
Negotiation                       >= 100
Cooperation                       >= 70
Competition                       >= 55
Team/Role/Coalition               >= 90
Collective Decision               >= 80
Conflict Resolution               >= 80
Collective Knowledge              >= 65
Collective Intelligence           >= 80
Social Simulation                 >= 60
Distributed Integration            >= 60
Security/Privacy/Governance       >= 100
Human Interaction                >= 55
Fault Recovery                    >= 60
Compiler/IR                       >= 70
Testing/Evaluation                >= 90
```

**Tổng mục tiêu: ≥ 1,500 acceptance criteria.**

---

# 207. Unified Multi-Agent Architecture

Sau 658:

```text
                    Environment
                         ↓
                  655 World Model
                         ↓
                657 Cognitive Executive
                         ↓
                 ┌───────┴───────┐
                 ↓               ↓
              658 Social       644 Agent
              Intelligence     Runtime
                 ↓               ↓
          ┌──────┼──────┐        ↓
          ↓      ↓      ↓       Tools
       Social  Team  Negotiation
       Model   Model    Model
          ↓      ↓      ↓
          └──────┼──────┘
                 ↓
            Collective Plan
                 ↓
               652
                 ↓
             656 Action
```

---

# 208. Separation of Responsibilities

```text
644 = Agent lifecycle/orchestration

650 = Memory

652 = Optimization / planning

653 = Probability / uncertainty / causal reasoning

654 = Formal symbolic reasoning

655 = World state / dynamics / prediction

656 = Embodiment / perception-action / physical control

657 = Individual cognitive executive

658 = Social cognition / interaction / collective intelligence
```

Đây là boundary bắt buộc để tránh một runtime multi-agent biến thành một khối AI không thể kiểm thử.

---

# 209. Example

Một nhóm robot giao nhiệm vụ:

```axiom
goal rescue_person(location)
```

657:

```text
establish goal
→ retrieve relevant memory
→ inspect world
```

658:

```text
discover agents
→ inspect capabilities
→ negotiate roles
→ create shared goal
→ allocate tasks
→ establish commitments
```

652:

```text
optimize task allocation
```

655:

```text
predict environment
```

656:

```text
execute motion
```

658 tiếp tục:

```text
monitor agents
→ detect failure
→ reassign task
→ update shared state
```

---

# 210. Security Boundary

Luồng hành động:

```text
658 Social Decision
        ↓
657 Cognitive Executive
        ↓
652 Plan
        ↓
639 Policy
        ↓
603 Capability
        ↓
656 Safety / Control
        ↓
614 Hardware
```

Không có shortcut:

```text
658 → Hardware
```

---

# 211. Completion Definition

BOOTSTRAP-658 hoàn thành khi Axiom có specification thực thi được cho:

- social agent model;
- theory-of-mind representation;
- bounded nested beliefs;
- social prediction;
- communication;
- typed messages;
- protocol state machines;
- shared/private context;
- social memory;
- relationships;
- trust evidence;
- reputation;
- commitments;
- agreements;
- negotiation;
- proposals/counterproposals;
- cooperation;
- competition;
- teams;
- roles;
- coalitions;
- collective goals;
- collective task allocation;
- coordination;
- handoff;
- conflict detection;
- mediation;
- collective decisions;
- voting;
- consensus boundary;
- collective knowledge;
- collective belief;
- evidence aggregation;
- information cascades;
- debate;
- critic/verifier agents;
- collective intelligence;
- social simulation;
- adversarial-agent simulation;
- collective learning;
- social privacy;
- communication security;
- distributed coordination;
- failure recovery;
- human interaction;
- compiler annotations;
- compiler IR;
- runtime profiles;
- **≥145 core invariants**;
- **≥1,500 acceptance criteria**.

**BOOTSTRAP-658 — COMPLETE.**

**Next task: BOOTSTRAP-659 — Native AI Emotion, Affective Computing, Social-Emotional State, Empathy Modeling, Emotion-Aware Interaction, Mood Dynamics & Affective Agent Runtime 5.0.**

:::