BOOTSTRAP-657 tiếp tục tầng trên 656: xây dựng **kiến trúc nhận thức thống nhất cho AI agent**, nhưng giữ ranh giới rõ với memory 650, planning 652, reasoning 653–654, world model 655 và embodied control 656.

:::writing{variant="document" id="74162" title="BOOTSTRAP-657 — Native AI Cognitive Architecture, Executive Function, Attention, Working Memory, Goal Management, Metacognition, Self-Monitoring & Unified Agent Control Runtime 5.0"}

# BOOTSTRAP-657
## Native AI Cognitive Architecture, Executive Function, Attention, Working Memory, Goal Management, Metacognition, Self-Monitoring & Unified Agent Control Runtime 5.0

**Status:** COMPLETE  
**Layer:** Native AI Cognitive / Executive Architecture  
**Depends on:** BOOTSTRAP-600 → BOOTSTRAP-656.

---

# 1. Mục tiêu

657 là tầng **executive cognition** của Axiom.

Nó không phải một LLM, không phải memory system, không phải planner và không phải world model.

Nó cung cấp một runtime thống nhất để một AI agent có thể:

```text
observe
→ understand
→ attend
→ remember
→ establish goals
→ prioritize
→ reason
→ plan
→ act
→ monitor
→ evaluate
→ reflect
→ revise
```

Kiến trúc tổng quát:

```text
                 ┌──────────────────────┐
                 │     Environment      │
                 └──────────┬───────────┘
                            ↓
                    Perception 656/649
                            ↓
                    World Model 655
                            ↓
              ┌─────────────────────────┐
              │   Cognitive Executive   │
              │          657            │
              ├─────────────────────────┤
              │ Attention               │
              │ Working Memory          │
              │ Goals                   │
              │ Priorities              │
              │ Context                 │
              │ Reasoning Coordination  │
              │ Planning Coordination   │
              │ Monitoring              │
              │ Metacognition           │
              │ Reflection              │
              └────────────┬────────────┘
                           ↓
                 Planning / Reasoning
                    652 / 653 / 654
                           ↓
                      Action 656
                           ↓
                       Environment
```

---

# 2. Architectural Position

657 nằm giữa các subsystem AI cấp thấp và agent execution:

```text
643 ML
649 Multimodal
650 Memory
655 World Model
656 Embodiment
       ↓
      657
       ↓
644 Agent Runtime
652 Planning
653 Probabilistic Reasoning
654 Symbolic Reasoning
```

657 quyết định **khi nào và vì sao subsystem nào được gọi**, nhưng không tự sở hữu authority của chúng.

---

# 3. Những vấn đề 657 giải quyết

Một agent thực tế không chỉ cần:

```text
memory + LLM + planner
```

Nó cần:

- attention;
- context selection;
- working memory;
- goal stack;
- priorities;
- task decomposition;
- interruption;
- conflict resolution;
- uncertainty awareness;
- self-monitoring;
- error detection;
- confidence tracking;
- reflection;
- strategy switching;
- resource-aware cognition;
- bounded cognition;
- temporal reasoning;
- executive state;
- internal events;
- metacognitive state.

657 cung cấp substrate cho các thành phần này.

---

# 4. Core Principle

657 phải phân biệt:

```text
Knowledge
Memory
Belief
Goal
Plan
Intent
Decision
Action
Observation
Reflection
```

Không được coi chúng là cùng một loại object.

---

# 5. Core Types

```text
CognitiveAgent
CognitiveState
ExecutiveState

Attention
AttentionFocus
AttentionPolicy
AttentionBudget

WorkingMemory
WorkingMemoryItem
WorkingMemorySlot
ContextWindow
ContextAssembly

Goal
GoalId
GoalSet
GoalPriority
GoalStatus
GoalStack

Intent
Task
Subtask
TaskContext

CognitiveEvent
CognitiveTrace

Belief
Hypothesis
Expectation

DecisionContext

Reflection
MetacognitiveState
Confidence
UncertaintyAssessment

Strategy
StrategyState
StrategyTransition

Monitor
InvariantMonitor
AnomalyMonitor
PerformanceMonitor

CognitiveCycle
CognitiveBudget
CognitiveDeadline
```

---

# 6. CognitiveAgent

```axiom
agent CognitiveAgent:
    memory = memory
    world = world
    planner = planner
    reasoner = reasoner
    executive = executive
```

Agent không nhất thiết phải có embodiment.

Có thể là:

```text
software agent
robot
game agent
research agent
coding agent
workflow agent
simulation agent
```

---

# 7. Executive State

ExecutiveState đại diện trạng thái điều phối hiện tại:

```text
active_goal
active_task
attention_focus
working_memory
pending_tasks
blocked_tasks
running_actions
uncertainties
constraints
resource_budget
current_strategy
```

---

# 8. Cognitive Cycle

Một cycle chuẩn:

```text
Observe
↓
Update State
↓
Select Attention
↓
Assemble Context
↓
Evaluate Goals
↓
Select Task
↓
Reason / Plan
↓
Execute
↓
Monitor
↓
Evaluate Outcome
↓
Update Memory
↓
Reflect
```

Không bắt buộc mọi cycle phải chạy toàn bộ các bước.

---

# 9. Event-Driven Cognition

Ngoài periodic cycle, 657 hỗ trợ event-driven cognition:

```text
NewObservation
GoalChanged
PlanFailed
ActionCompleted
ActionFailed
DeadlineNear
SafetyAlert
MemoryRetrieved
ModelChanged
HumanIntervention
```

---

# 10. Cognitive Event

```text
CognitiveEvent:
    type
    timestamp
    source
    priority
    payload
    correlation_id
```

---

# 11. Event Priority

```text
Emergency
Safety
Human
Deadline
Goal
Task
Information
Background
```

Priority không tự cấp authority.

Nó chỉ quyết định scheduling của cognitive work.

---

# 12. Attention

Attention là cơ chế chọn subset thông tin cho processing.

```axiom
focus = attention.select(
    observations,
    goals,
    context
)
```

---

# 13. Attention ≠ Consciousness

657 định nghĩa attention như computational resource allocation.

Không đưa ra bất kỳ giả định nào về consciousness.

---

# 14. Attention Object

```text
Attention:
    target
    relevance
    urgency
    confidence
    novelty
    goal_alignment
    cost
    timestamp
```

---

# 15. Attention Score

Có thể sử dụng:

```text
priority
relevance
uncertainty
novelty
urgency
goal_value
risk
```

Nhưng scoring model phải configurable.

---

# 16. Attention Policy

```text
Fixed
RuleBased
UtilityBased
Learned
GoalDirected
SaliencyBased
Hybrid
```

---

# 17. Attention Budget

Agent không thể xử lý vô hạn thông tin.

```text
AttentionBudget:
    tokens
    objects
    memory_items
    model_calls
    cpu_time
    gpu_time
```

---

# 18. Context Assembly

650 giữ memory.

657 quyết định:

> memory nào nên được đưa vào context hiện tại?

Pipeline:

```text
Goal
↓
Attention
↓
Retrieval 650
↓
Filtering
↓
Compression
↓
Context
```

---

# 19. Context Window

```text
ContextWindow:
    system_context
    task_context
    world_context
    memory_context
    tool_context
    reasoning_context
```

---

# 20. Context Priority

Context có thể có:

```text
mandatory
important
optional
discardable
```

---

# 21. Context Compression

657 có thể yêu cầu 650:

```text
summarize
compress
deduplicate
abstract
```

Nhưng compression không được biến mất provenance.

---

# 22. Context Provenance

Mỗi context item có thể truy về:

```text
memory_id
observation_id
world_revision
model_revision
timestamp
source
```

---

# 23. Working Memory

Working memory là trạng thái tạm thời của cognition.

Khác với long-term memory 650.

```text
WorkingMemory:
    capacity
    items
    priorities
    expiration
```

---

# 24. Working Memory Item

```text
WorkingMemoryItem:
    value
    type
    source
    importance
    confidence
    expiry
```

---

# 25. Working Memory Lifetime

Các mode:

```text
cycle
task
session
goal
persistent
```

Persistent memory phải chuyển qua 650.

---

# 26. Working Memory Eviction

Strategies:

```text
FIFO
LRU
importance
goal_relevance
confidence
utility
hybrid
```

---

# 27. Goal

Goal là trạng thái mong muốn.

```axiom
goal reach(destination)
```

---

# 28. Goal Structure

```text
Goal:
    id
    description
    desired_state
    priority
    deadline
    constraints
    utility
    status
    parent
```

---

# 29. Goal Status

```text
Pending
Active
Blocked
Suspended
Completed
Failed
Cancelled
Expired
Superseded
```

---

# 30. Goal Hierarchy

```text
Mission
 ├── Objective A
 │    ├── Task A1
 │    └── Task A2
 └── Objective B
```

---

# 31. Goal Stack

657 hỗ trợ:

```text
push_goal
suspend_goal
resume_goal
complete_goal
cancel_goal
replace_goal
```

---

# 32. Goal Conflict

Hai goal có thể xung đột:

```text
Goal A → minimize_time
Goal B → minimize_cost
```

Conflict resolution đi qua:

```text
639 policy
652 optimization
653 uncertainty
```

657 không tự tạo political/moral authority.

---

# 33. Goal Priority

Priority có thể đến từ:

```text
user
system
policy
task
safety
deadline
```

Nguồn phải được ghi rõ.

---

# 34. Goal Origin

```text
UserGoal
SystemGoal
PolicyGoal
DerivedGoal
LearnedGoal
EmergencyGoal
```

---

# 35. Goal Authority

Một goal không có capability thì không thể tạo action authority.

```text
Goal ≠ Permission
```

---

# 36. Intent

Intent là mục tiêu hành động gần-term.

Ví dụ:

```text
Goal:
    deliver package

Intent:
    navigate to room 203
```

---

# 37. Task

Task là executable cognitive unit.

```text
Task:
    input
    preconditions
    procedure
    deadline
    resources
    expected_effect
```

---

# 38. Task Decomposition

```text
Task
 ↓
Subtasks
 ↓
Primitive operations
```

652 có thể thực hiện decomposition planning.

---

# 39. Task State

```text
Created
Ready
Running
Waiting
Blocked
Completed
Failed
Cancelled
```

---

# 40. Task Dependencies

```text
A → B
A → C
B,C → D
```

DAG semantics mặc định.

---

# 41. Cognitive Scheduler

657 điều phối cognitive tasks:

```text
retrieval
reasoning
planning
reflection
monitoring
tool calls
```

607 cung cấp underlying execution.

---

# 42. Cognitive Scheduling

Policy có thể cân nhắc:

```text
priority
deadline
utility
cost
dependency
risk
```

---

# 43. Interruptions

Agent có thể bị interrupt:

```text
new_goal
safety_event
human_command
deadline
sensor_change
```

---

# 44. Interrupt Policy

```text
Ignore
Queue
Pause
Preempt
Abort
Escalate
```

---

# 45. Preemption

Preempted task phải giữ:

```text
task_state
working_context
resources
checkpoint
```

nếu resumable.

---

# 46. Cognitive Checkpoint

```text
CognitiveCheckpoint:
    executive_state
    active_goal
    task_states
    working_memory
    strategy_state
```

Có thể dùng 600 snapshot/recovery.

---

# 47. Strategy

Strategy mô tả cách agent giải quyết task.

```text
Direct
Decompose
Search
Retrieve
AskHuman
Simulate
Experiment
Delegate
Fallback
```

---

# 48. Strategy Selection

Có thể dựa trên:

```text
task
cost
deadline
uncertainty
past performance
available tools
```

---

# 49. Strategy Switching

Agent có thể chuyển:

```text
Search
→
Simulation
→
AskHuman
```

khi điều kiện thay đổi.

---

# 50. Strategy State

```text
StrategyState:
    strategy
    confidence
    start_time
    attempts
    success_rate
```

---

# 51. Metacognition

Metacognition trong Axiom là khả năng runtime biểu diễn:

```text
what I know
what I do not know
what I am uncertain about
what strategy I am using
whether current strategy is working
```

Không phải claim về consciousness.

---

# 52. MetacognitiveState

```text
knowledge_confidence
goal_confidence
plan_confidence
execution_confidence
model_confidence
memory_confidence
```

---

# 53. Confidence

Confidence phải có source:

```text
ModelConfidence
EvidenceConfidence
EstimatorConfidence
HeuristicConfidence
HumanProvidedConfidence
```

Không được giả định mọi confidence đều cùng semantics.

---

# 54. Uncertainty

653 cung cấp formal uncertainty.

657 sử dụng:

```text
known
unknown
uncertain
conflicting
insufficient_evidence
```

---

# 55. Knowledge Gap

```text
KnowledgeGap:
    topic
    importance
    urgency
    evidence_needed
```

---

# 56. Information Seeking

Nếu knowledge gap quan trọng:

```text
retrieve
search
experiment
simulate
ask_human
```

---

# 57. Active Information Gathering

652/653 có thể chọn action làm giảm uncertainty.

657 điều phối loop:

```text
uncertainty
↓
information_goal
↓
information_action
↓
new_observation
```

---

# 58. Epistemic vs Task Action

Phân biệt:

```text
TaskAction
InformationAction
```

Ví dụ:

```text
"move object"
```

khác:

```text
"look at object to determine identity"
```

---

# 59. Reflection

Reflection là structured post-task analysis.

```text
Reflection:
    objective
    outcome
    expected
    actual
    discrepancy
    cause_hypotheses
    lessons
```

---

# 60. No Hidden Chain-of-Thought

657 chỉ lưu:

```text
structured decision metadata
```

Không yêu cầu lưu hidden chain-of-thought.

---

# 61. Outcome Evaluation

Sau action:

```text
expected_state
actual_state
difference
```

được đánh giá.

---

# 62. Prediction Error

655 cung cấp prediction.

657 tính:

```text
prediction_error
```

và có thể gửi feedback về 655/643.

---

# 63. Planning Error

652 plan:

```text
expected success
```

657 nhận:

```text
actual failure
```

để trigger replanning.

---

# 64. Strategy Evaluation

```text
strategy_success
strategy_cost
strategy_latency
strategy_risk
```

---

# 65. Self-Monitoring

Monitor:

```text
GoalMonitor
TaskMonitor
PlanMonitor
ModelMonitor
MemoryMonitor
ResourceMonitor
SafetyMonitor
PerformanceMonitor
```

---

# 66. Goal Monitor

Kiểm tra:

```text
goal progress
deadline
blockers
```

---

# 67. Plan Monitor

Kiểm tra:

```text
plan validity
world changes
assumptions
execution progress
```

---

# 68. Model Monitor

Kiểm tra:

```text
model revision
confidence
OOD
drift
prediction error
```

---

# 69. Memory Monitor

Kiểm tra:

```text
retrieval quality
staleness
contradictions
provenance
```

---

# 70. Resource Monitor

Theo dõi:

```text
CPU
GPU
memory
tokens
network
energy
time
```

606/633 cung cấp infrastructure.

---

# 71. Cognitive Budget

```text
CognitiveBudget:
    max_time
    max_tokens
    max_model_calls
    max_memory
    max_cpu
    max_gpu
    max_tool_calls
```

---

# 72. Budget Allocation

Executive có thể chia:

```text
perception 20%
reasoning 30%
planning 30%
verification 20%
```

tùy task.

---

# 73. Budget Reallocation

Nếu perception đủ chắc chắn:

```text
perception_budget ↓
planning_budget ↑
```

Đây là policy-driven adaptation.

---

# 74. Deadline-Aware Cognition

Khi deadline gần:

```text
deep_reasoning
→
bounded_reasoning
→
fast_fallback
```

---

# 75. Anytime Cognition

Agent có thể trả:

```text
best_answer_so_far
confidence
remaining_budget
```

---

# 76. Cognitive Timeout

Timeout không đồng nghĩa failure.

Statuses:

```text
Complete
Partial
Timeout
InsufficientEvidence
Blocked
Failed
```

---

# 77. Tool Selection

657 chọn tool dựa trên:

```text
goal
task
capability
cost
latency
risk
availability
```

---

# 78. Tool Capability

Tool metadata:

```text
name
input_schema
output_schema
latency
cost
side_effects
required_capability
risk
```

---

# 79. Tool Side Effects

Phân loại:

```text
Pure
ReadOnly
Reversible
Irreversible
ExternalSideEffect
PhysicalAction
```

---

# 80. Tool Safety

Tool call phải đi qua:

```text
603 capability
639 policy
```

nếu cần.

---

# 81. Tool Verification

Trước execution:

```text
validate input
validate capability
validate policy
validate preconditions
```

---

# 82. Postcondition

Sau execution:

```text
verify output
verify state change
verify expected effect
```

---

# 83. Tool Failure

657 phải distinguish:

```text
ToolUnavailable
ToolTimeout
ToolRejected
ToolInvalidOutput
ToolSideEffectUnknown
ToolExecutionFailed
```

---

# 84. Tool Retry

Retry policy:

```text
Never
SafeOnly
IdempotentOnly
Bounded
ManualApproval
```

---

# 85. Idempotency

Tool metadata phải khai báo idempotency.

Không retry arbitrary side-effecting action.

---

# 86. Human-in-the-Loop

Agent có thể tạo:

```text
HumanDecisionRequest
```

khi:

```text
uncertainty high
authority insufficient
conflicting goals
irreversible action
missing information
```

---

# 87. Human Response

Human response phải được ghi:

```text
source = human
timestamp
scope
```

---

# 88. Human Override

Human có thể:

```text
approve
reject
modify
pause
cancel
```

theo capability.

---

# 89. Multi-Agent Cognition

644 quản lý multi-agent.

657 cung cấp:

```text
CognitiveSession
AgentRole
Delegation
CoordinationContext
```

---

# 90. Delegation

```text
delegate(task, agent)
```

với:

```text
scope
deadline
authority
expected_result
```

---

# 91. Delegation ≠ Authority Transfer

Delegating reasoning không tự động transfer physical/security authority.

---

# 92. Agent Communication

Messages phải typed:

```text
Request
Proposal
Observation
Result
Warning
Failure
Commitment
```

---

# 93. Commitment

Agent có thể giữ commitment:

```text
goal
deadline
resource
expected_action
```

---

# 94. Commitment Violation

Nếu không thể fulfill:

```text
CommitmentAtRisk
```

phải được phát hiện.

---

# 95. Shared Cognitive State

Multi-agent system có thể chia sẻ:

```text
goals
beliefs
plans
observations
```

nhưng provenance phải preserve.

---

# 96. Belief

Belief là agent's current representation về proposition.

```text
Belief:
    proposition
    confidence
    evidence
    timestamp
    source
```

---

# 97. Belief Revision

Khi evidence mới mâu thuẫn:

```text
old belief
+
new evidence
→
belief revision
```

653 cung cấp probabilistic update.

---

# 98. Contradiction

657 phải detect:

```text
Belief A
Belief not-A
```

và đánh dấu:

```text
Contradictory
```

Không âm thầm chọn một bên.

---

# 99. Belief Provenance

Belief phải truy xuất:

```text
observation
memory
model
human
inference
```

---

# 100. Expectation

Agent có expectation:

```text
expected outcome
probability/confidence
deadline
```

---

# 101. Surprise

Surprise là measurable discrepancy:

```text
actual != expected
```

Có thể kích hoạt:

```text
attention
replanning
reflection
model update
```

---

# 102. Novelty

Novelty signal có thể làm tăng attention priority.

---

# 103. Curiosity

Curiosity trong runtime được mô hình hóa thành:

```text
information_gain
novelty
uncertainty_reduction
```

không phải một anthropomorphic claim.

---

# 104. Exploration

651/652/653 có thể chọn exploratory actions.

657 điều phối budget.

---

# 105. Exploitation vs Exploration

Strategy state có thể biểu diễn:

```text
explore
exploit
balanced
```

---

# 106. Learning Trigger

Reflection có thể tạo:

```text
LearningEvent
```

gửi 643:

```text
model improvement candidate
```

---

# 107. Model Update Boundary

657 không tự mutate production model.

647 lifecycle vẫn kiểm soát:

```text
train
validate
approve
deploy
rollback
```

---

# 108. Cognitive Adaptation

Agent có thể thay đổi:

```text
strategy
attention policy
tool choice
planning depth
memory retrieval policy
```

trong runtime.

---

# 109. Stable Core

Các thay đổi trên không được tự động thay đổi:

```text
security policy
safety policy
authority
runtime invariants
```

---

# 110. Cognitive Policy

Policy có thể quy định:

```text
maximum_reasoning_depth
allowed_tools
allowed_models
required_verification
human_approval_threshold
```

---

# 111. Cognitive Modes

Native modes:

```text
Reactive
Deliberative
Reflective
Exploratory
Conservative
Emergency
Learning
```

---

# 112. Reactive Mode

Ưu tiên:

```text
latency
simple policy
known action
```

---

# 113. Deliberative Mode

Ưu tiên:

```text
planning
simulation
reasoning
verification
```

---

# 114. Reflective Mode

Ưu tiên:

```text
outcome analysis
prediction error
strategy evaluation
memory update
```

---

# 115. Emergency Mode

Chỉ cognition cần thiết cho safe behavior.

---

# 116. Cognitive State Machine

```text
Idle
 ↓
Observe
 ↓
Orient
 ↓
GoalSelect
 ↓
Plan
 ↓
Execute
 ↓
Monitor
 ↓
Evaluate
 ↓
Reflect
 ↓
Idle
```

Có thể branch:

```text
Execute → Failure → Replan
Monitor → Emergency → SafeState
```

---

# 117. Cognitive Blackboard

657 cung cấp optional blackboard:

```text
facts
goals
tasks
hypotheses
plans
alerts
resources
```

Blackboard entries có revision.

---

# 118. Blackboard Concurrency

608 đảm bảo:

```text
atomic update
version check
conflict detection
```

---

# 119. Optimistic Cognitive Updates

Agent có thể:

```text
read revision 10
compute
commit only if revision == 10
```

---

# 120. Context Conflict

Nếu world revision đổi:

```text
context invalidated
```

Agent phải refresh hoặc explicitly continue.

---

# 121. World Change Detection

655 gửi:

```text
WorldRevisionChanged
```

657 quyết định:

```text
continue
replan
abort
```

---

# 122. Goal Drift

Nếu environment thay đổi khiến goal không còn valid:

```text
GoalInvalidated
```

---

# 123. Goal Progress

Goal có thể có measurable progress:

```text
0.0 → 1.0
```

Nhưng semantics phải do goal định nghĩa.

---

# 124. Goal Completion

Không được coi action success = goal success.

Phải kiểm tra desired state/postcondition.

---

# 125. Goal Failure

Failure reasons:

```text
Impossible
Timeout
ResourceUnavailable
SafetyViolation
PolicyDenied
WorldChanged
InsufficientInformation
ToolFailure
```

---

# 126. Goal Replanning

Khi failure:

```text
diagnose
→ revise assumptions
→ generate alternatives
→ plan
```

---

# 127. Alternative Plans

657 có thể giữ:

```text
primary_plan
fallback_plan
emergency_plan
```

---

# 128. Plan Commitment

Agent có thể commit plan trong thời gian ngắn.

Nếu assumptions thay đổi:

```text
plan invalidated
```

---

# 129. Assumption Registry

Plan/goal có thể khai báo:

```text
Assumption:
    statement
    source
    confidence
    expiration
```

---

# 130. Assumption Monitoring

657 theo dõi assumptions.

Nếu violated:

```text
AssumptionBroken
```

---

# 131. Epistemic Status

Information có:

```text
Observed
Inferred
Predicted
Hypothesized
Simulated
HumanProvided
Unknown
```

---

# 132. Critical Distinction

Không được tự động chuyển:

```text
Predicted → Observed
Hypothesis → Fact
Simulation → Reality
```

---

# 133. Cognitive Audit

Mỗi significant decision có structured record:

```text
goal
context_revision
world_revision
memory_references
models
tools
plan
constraints
decision
outcome
```

---

# 134. Decision Explanation

Không lưu hidden reasoning.

Chỉ lưu:

```text
selected_option
relevant_factors
constraints
evidence
uncertainty
verification
```

---

# 135. Self-Evaluation

657 có thể tính:

```text
goal_success_rate
plan_success_rate
tool_success_rate
prediction_error
deadline_compliance
resource_efficiency
```

---

# 136. Calibration

Confidence calibration có thể được đánh giá bằng 646.

---

# 137. Overconfidence

Nếu confidence cao nhưng error cao:

```text
metacognitive_warning
```

---

# 138. Underconfidence

Nếu confidence thấp nhưng evidence mạnh:

```text
possible_overcaution
```

---

# 139. Cognitive Health

Không dùng khái niệm health theo nghĩa y khoa.

Runtime health chỉ là:

```text
latency
error rate
resource state
model availability
memory integrity
task progress
```

---

# 140. Cognitive Degradation

Khi resource thấp:

```text
full reasoning
→ bounded reasoning
→ heuristic
→ fallback
```

---

# 141. Graceful Degradation

Agent không được crash chỉ vì:

```text
model unavailable
memory retrieval unavailable
planner timeout
optional tool unavailable
```

nếu fallback tồn tại.

---

# 142. Critical Dependencies

Mỗi task phải biết:

```text
required
optional
fallback
```

dependencies.

---

# 143. Dependency Graph

```text
Goal
 ↓
Task
 ├── Memory
 ├── WorldModel
 ├── Planner
 └── Tool
```

---

# 144. Cognitive Resource Manager

606 cung cấp resource manager.

657 thêm:

```text
CognitiveResource
```

cho:

```text
reasoning budget
attention budget
memory budget
tool budget
```

---

# 145. Token Budget

LLM-backed models có:

```text
input_tokens
output_tokens
context_tokens
```

nhưng architecture không phụ thuộc LLM.

---

# 146. Non-LLM Reasoner

657 phải hoạt động với:

```text
rules
search
planner
symbolic engine
finite state machine
classical algorithms
```

---

# 147. LLM Adapter

LLM chỉ là provider:

```text
LanguageModelProvider
```

---

# 148. Model Provider

Provider interface:

```text
infer
stream
estimate_cost
estimate_latency
cancel
```

---

# 149. Model Selection

657 có thể chọn model theo:

```text
task
latency
quality
cost
context
availability
```

---

# 150. Model Fallback

```text
large_model
→ medium_model
→ small_model
→ deterministic fallback
```

---

# 151. Model Revision

Mọi production inference phải có model revision.

---

# 152. Model Failure

Không được retry vô hạn.

---

# 153. Cognitive Cache

Có thể cache:

```text
retrieval
reasoning result
tool result
world interpretation
```

nhưng cache key phải bao gồm relevant revisions.

---

# 154. Cache Invalidation

World/goal/model revision thay đổi có thể invalidate cache.

---

# 155. Temporal Context

Context phải hỗ trợ:

```text
past
present
future
deadline
sequence
duration
```

---

# 156. Temporal Reasoning Boundary

653/654 xử lý formal reasoning.

657 quản lý temporal context.

---

# 157. Long-Horizon Task

Task có thể chạy:

```text
seconds
minutes
hours
days
```

với checkpoint.

---

# 158. Durable Cognition

600 cung cấp persistence.

657 lưu:

```text
goal state
task state
commitments
pending actions
```

---

# 159. Crash Recovery

Sau restart:

```text
restore executive state
validate world revision
validate outstanding actions
resume/replan
```

Không tự động replay irreversible action.

---

# 160. Exactly-Once Cognition

Không giả định mọi cognitive operation exactly-once.

Tool side effects phải có idempotency semantics.

---

# 161. Action Journal

Mỗi side-effecting action có:

```text
action_id
attempt
status
idempotency_key
```

---

# 162. Duplicate Prevention

Recovery phải detect:

```text
already_executed
unknown_execution_state
```

---

# 163. Unknown Execution State

Nếu external action status unknown:

```text
query
reconcile
human approval
safe fallback
```

tùy policy.

---

# 164. Goal Persistence

Goal có thể survive process restart nếu configured durable.

---

# 165. Session

Session groups:

```text
goals
context
working_memory
tools
permissions
```

---

# 166. Agent Identity

627 quản lý identity.

657 chỉ giữ:

```text
agent_id
session_id
```

---

# 167. Security

603/639 remain authoritative.

657 cannot:

```text
grant capability
change policy
bypass safety
```

---

# 168. Governance

640 controls:

```text
data classification
retention
privacy
residency
```

657 consumes policy.

---

# 169. Cognitive Data Lineage

Context-derived decision phải có lineage:

```text
source
transformation
model
revision
```

---

# 170. Prompt/Context Security

Untrusted data phải được marked:

```text
UntrustedContent
```

---

# 171. Instruction Hierarchy

Runtime phân biệt:

```text
system policy
developer/application policy
user instruction
external content
model-generated suggestion
```

Không coi external content là authority.

---

# 172. Prompt Injection Boundary

Retrieved content không được tự động thay đổi:

```text
policy
capability
system configuration
```

---

# 173. Tool Injection Boundary

Tool result không được tự động execute như command.

---

# 174. Cognitive Sandboxing

Untrusted reasoning có thể chạy:

```text
sandbox
```

với restricted capabilities.

---

# 175. Speculative Cognition

Agent có thể tạo:

```text
hypothetical_plan
```

mà không execute.

---

# 176. Simulation-Based Reasoning

```text
hypothesis
→ 655 rollout
→ 648 simulation
→ evaluate
```

---

# 177. Counterfactual Cognition

653 cung cấp:

```text
what_if
```

657 dùng để so sánh strategies.

---

# 178. Decision Boundary

652 vẫn là subsystem quyết định optimization.

657:

```text
select which decision problem to solve
```

652:

```text
solve decision problem
```

---

# 179. Reasoning Boundary

654:

```text
prove / derive
```

657:

```text
decide when proof/reasoning is needed
```

---

# 180. Memory Boundary

650:

```text
store / retrieve
```

657:

```text
decide what to retrieve and when
```

---

# 181. World Model Boundary

655:

```text
state / prediction
```

657:

```text
decide what state information matters now
```

---

# 182. Embodiment Boundary

656:

```text
physical perception / control
```

657:

```text
decide which task/action should be pursued
```

---

# 183. Agent Boundary

644:

```text
agent orchestration
```

657:

```text
cognitive executive
```

644 can host multiple 657 cognitive loops.

---

# 184. Cognitive API

```axiom
executive.run(goal)
executive.observe(event)
executive.focus(target)
executive.remember(item)
executive.retrieve(query)
executive.plan(task)
executive.execute(action)
executive.monitor()
executive.reflect()
```

---

# 185. Cognitive Cycle API

```axiom
cycle = executive.tick()

cycle.goal
cycle.focus
cycle.context
cycle.plan
cycle.actions
cycle.monitoring
cycle.status
```

---

# 186. Cognitive Trace

```text
CognitiveTrace:
    cycle_id
    goal
    context_revision
    attention
    decisions
    actions
    outcomes
    metrics
```

---

# 187. Cognitive Replay

Replay có thể tái hiện:

```text
events
state revisions
tool results
model revisions
```

nhưng không tự thực hiện external side effects.

---

# 188. Deterministic Replay

Deterministic mode yêu cầu:

```text
fixed seeds
fixed model revision
fixed tool responses
fixed event ordering
```

---

# 189. Cognitive Benchmark

Benchmark:

```text
goal completion
latency
cost
tool efficiency
planning efficiency
memory retrieval
calibration
recovery
```

---

# 190. Cognitive Evaluation

646 cung cấp evaluation.

657 cung cấp structured traces.

---

# 191. Online Adaptation

Có thể adapt:

```text
attention policy
retrieval policy
strategy selection
```

nhưng production model lifecycle vẫn thuộc 647.

---

# 192. Shadow Adaptation

Agent có thể thử strategy mới ở shadow mode:

```text
actual_strategy
shadow_strategy
```

Shadow không affect action.

---

# 193. Strategy Rollback

Nếu adaptation làm giảm performance:

```text
restore previous strategy revision
```

---

# 194. Cognitive A/B Testing

651/637 có thể experiment trên:

```text
attention policy
retrieval policy
strategy policy
```

---

# 195. Multi-Agent Cognitive Coordination

Agent có thể:

```text
request
delegate
negotiate
merge_results
```

nhưng authority remains external policy.

---

# 196. Shared Goal

Multiple agents có thể subscribe:

```text
GoalId
```

---

# 197. Goal Ownership

Goal phải có:

```text
owner
delegates
authority_scope
```

---

# 198. Goal Lease

Long-running distributed goal có:

```text
lease
expiration
renewal
```

---

# 199. Conflict Resolution

Conflict có thể được giải quyết bằng:

```text
policy
priority
optimization
human decision
```

không hard-code một universal preference order.

---

# 200. Cognitive Safety Invariant

Executive cognition có thể:

```text
suggest
plan
reason
simulate
```

nhưng không tự cấp:

```text
security authority
physical authority
policy authority
```

---

# 201. Compiler Annotations

```text
@cognitive
@executive
@attention
@working_memory
@context
@goal
@goal_stack
@intent
@task
@subtask
@strategy
@strategy_switch
@belief
@expectation
@hypothesis
@reflection
@metacognition
@monitor
@self_monitor
@cognitive_cycle
@cognitive_budget
@cognitive_deadline
@tool
@tool_policy
@delegation
@commitment
@assumption
@information_goal
@exploration
@replanning
@fallback
@human_in_loop
@cognitive_checkpoint
@cognitive_replay
```

---

# 202. Generated Metadata

```text
.axcognitive
.axexecutive
.axattention
.axworking
.axcontext
.axgoal
.axtask
.axstrategy
.axbelief
.axexpectation
.axreflection
.axmetacognition
.axmonitor
.axcommitment
.axassumption
.axcognitive_trace
.axcognitive_checkpoint
```

---

# 203. Compiler IR

```text
CognitiveCreate
CognitiveTick
AttentionSelect
WorkingMemoryRead
WorkingMemoryWrite
ContextAssemble
GoalCreate
GoalActivate
GoalSuspend
GoalComplete
GoalCancel
TaskCreate
TaskSchedule
TaskPreempt
StrategySelect
StrategySwitch
BeliefUpdate
ExpectationCreate
MonitorRegister
MonitorEvaluate
ToolSelect
ToolCall
ToolValidate
ToolResult
Reflect
Replan
CheckpointCognition
RestoreCognition
RequestHumanDecision
DelegateTask
CommitGoal
```

---

# 204. Runtime Profiles

```text
AXCOG_NONE
AXCOG_CORE
AXCOG_ATTENTION
AXCOG_WORKING
AXCOG_CONTEXT
AXCOG_GOAL
AXCOG_TASK
AXCOG_STRATEGY
AXCOG_BELIEF
AXCOG_METACOG
AXCOG_REFLECTION
AXCOG_MONITOR
AXCOG_TOOL
AXCOG_HUMAN
AXCOG_MULTI_AGENT
AXCOG_REALTIME
AXCOG_DISTRIBUTED
AXCOG_LEARNING
AXCOG_FULL
```

---

# 205. CLI

```text
axiom cognitive inspect
axiom cognitive run
axiom cognitive replay
axiom cognitive benchmark

axiom goal list
axiom goal inspect
axiom goal trace
axiom goal cancel

axiom task list
axiom task inspect
axiom task graph

axiom attention inspect
axiom attention benchmark

axiom context inspect
axiom context trace

axiom strategy inspect
axiom strategy compare

axiom belief inspect
axiom belief conflicts

axiom reflection inspect

axiom cognition checkpoint
axiom cognition restore
```

---

# 206. Core Invariants

657 yêu cầu tối thiểu **120 invariants**.

Các invariant quan trọng:

1. Goal không phải permission.
2. Intent không phải permission.
3. Belief không phải observation.
4. Prediction không phải observation.
5. Hypothesis không phải fact.
6. Simulation không phải reality.
7. Memory không phải current world state.
8. Working memory không phải durable memory.
9. Attention không thay đổi source truth.
10. Context assembly phải preserve provenance.
11. Context compression không được silently erase provenance.
12. Goal origin phải được ghi nhận.
13. Goal priority phải có source.
14. Goal conflict phải observable.
15. Goal completion phải kiểm tra postcondition.
16. Goal failure phải preserve cause.
17. Task state phải versioned.
18. Task preemption phải preserve required state.
19. Retry phải respect idempotency.
20. Side-effecting tool không được retry vô hạn.
21. Tool capability phải được kiểm tra.
22. Tool output không tự động trở thành instruction.
23. External content không tự động trở thành authority.
24. Retrieved content không được thay đổi system policy.
25. Model output không tự cấp capability.
26. Reflection không tự mutate production model.
27. Shadow strategy không affect live action.
28. Cognitive adaptation không bypass security.
29. Cognitive adaptation không bypass safety.
30. Model revision phải observable.
31. World revision phải observable.
32. Memory revision phải observable.
33. Stale context phải detectable.
34. Invalidated plan phải detectable.
35. Broken assumption phải detectable.
36. Belief contradiction không được silently discard.
37. Confidence phải có semantics.
38. Uncertainty phải preserve source.
39. Human input phải preserve source.
40. Learned information phải mark provenance.
41. Synthetic information phải mark synthetic.
42. Simulated evidence không phải real-world evidence.
43. Agent confidence không phải truth guarantee.
44. Strategy success phải đo được.
45. Strategy switch phải traceable.
46. Attention policy phải bounded.
47. Working memory phải bounded trong realtime profile.
48. Cognitive budget phải enforceable.
49. Cognitive deadline phải measurable.
50. Timeout phải distinguish với failure.
51. Partial result phải marked partial.
52. Tool failure phải distinguish với invalid result.
53. Unknown external action state phải preserved.
54. Recovery không được duplicate irreversible action.
55. Checkpoint phải versioned.
56. Restore phải validate environment revision.
57. Restored goal không được tự execute stale action.
58. Distributed goal phải có owner.
59. Delegation phải có scope.
60. Delegation không tự transfer security authority.
61. Commitment phải có deadline nếu required.
62. Commitment violation phải observable.
63. Multi-agent state phải preserve source agent.
64. Shared belief phải preserve provenance.
65. Conflicting beliefs phải remain distinguishable.
66. Attention cannot mutate world state.
67. Reasoning cannot mutate physical state directly.
68. Planning cannot bypass safety.
69. Cognitive executive cannot bypass 603.
70. Cognitive executive cannot bypass 639.
71. Cognitive executive cannot bypass 656 safety.
72. Human override must obey configured authority.
73. Emergency event must preempt ordinary cognition where policy requires.
74. Replanning must use compatible world revision.
75. Replanning must use compatible goal revision.
76. Memory retrieval must identify retrieval timestamp.
77. Context must identify source revisions.
78. Tool selection must account for capability.
79. Tool selection must account for side effects.
80. Tool selection must account for timeout.
81. Model selection must account for availability.
82. Model fallback must be bounded.
83. Model calls must be cancellable where contract supports.
84. Cognitive traces must not contain hidden chain-of-thought.
85. Structured explanations must preserve evidence references.
86. Self-monitoring cannot claim capabilities not measured.
87. Metacognitive state is computational metadata, not consciousness claim.
88. Surprise must be based on explicit expectation.
89. Prediction error must preserve prediction revision.
90. Reflection must distinguish observation from interpretation.
91. Learning event must distinguish candidate update from approved update.
92. Production model update requires lifecycle approval.
93. Strategy update requires revision.
94. Policy update requires policy authority.
95. Cognitive cache must include relevant revisions.
96. Cache invalidation must be deterministic where required.
97. Context priority must not alter source semantics.
98. Goal priority must not override higher-level policy.
99. Human request must still pass policy/capability checks.
100. Cognitive state must be recoverable when durability is enabled.
101. Event ordering must be explicit.
102. Duplicate event handling must be defined.
103. Event correlation IDs must remain stable.
104. Long-running tasks must support checkpointing when configured.
105. Distributed cognition must expose network staleness.
106. Network loss must not deadlock critical cognition.
107. Realtime cognition must avoid unbounded operations.
108. Realtime cognitive path must not silently allocate if prohibited.
109. Cognitive scheduler must obey deadlines.
110. Cognitive scheduler must expose missed deadlines.
111. Resource exhaustion must trigger defined degradation.
112. Degradation must not silently change safety policy.
113. Fallback must be declared or explicitly unavailable.
114. Human escalation must preserve reason.
115. Human decision must be auditable.
116. Goal cancellation must not silently cancel already-executing irreversible action.
117. Action cancellation semantics must be explicit.
118. Cognitive replay must not execute side effects.
119. Cognitive replay must preserve model revisions.
120. Cognitive replay must preserve tool-result fixtures.
121. Cognitive replay must preserve random seeds when applicable.
122. Cognitive benchmark must report population/task definition.
123. Cognitive evaluation must distinguish synthetic from real data.
124. Cognitive metrics must preserve measurement period.
125. Agent cannot infer user authority from arbitrary text.
126. Agent cannot infer safety approval from confidence.
127. Agent cannot infer policy approval from successful reasoning.
128. Executive state must not be treated as ground truth.
129. Goal state must not be treated as world state.
130. Cognitive recommendations must remain recommendations until authorized execution.

---

# 207. Acceptance Criteria

Target:

```text
Cognitive Core                  >= 60
Executive State                 >= 50
Attention                       >= 70
Working Memory                  >= 55
Context Assembly                >= 70
Goals                           >= 80
Tasks                           >= 60
Strategy                        >= 65
Belief Management               >= 60
Metacognition                   >= 65
Reflection                      >= 55
Self-Monitoring                 >= 65
Tool Selection                  >= 60
Human-in-the-Loop               >= 45
Multi-Agent Cognition           >= 50
Resource/Deadline Cognition     >= 55
Persistence/Recovery            >= 50
Security/Governance             >= 70
Realtime Cognition              >= 40
Distributed Cognition           >= 45
Learning Integration            >= 60
Simulation/Counterfactual       >= 45
Compiler/IR                     >= 60
Testing/Evaluation              >= 70
```

Mục tiêu tổng:

```text
>= 1,400 acceptance criteria
```

---

# 208. Unified Axiom Cognitive Stack

Sau BOOTSTRAP-657:

```text
600  State / Persistence
601  Configuration
602  Diagnostics
603  Security
604  IPC
605  Supervision
606  Resources
607  Scheduling
608  Synchronization
...
643  Machine Learning
644  AI Agents
645  Knowledge Graph
646  AI Evaluation
647  AI Governance
648  Simulation
649  Multimodal AI
650  AI Memory
651  Personalization
652  Planning
653  Probability / Causality
654  Symbolic Reasoning
655  World Model
656  Embodiment / Control
657  Cognitive Executive
```

Quan hệ chính:

```text
             ┌───────────────┐
             │   Environment │
             └───────┬───────┘
                     ↓
              656 Embodiment
                     ↓
              655 World Model
                     ↓
              650 Memory
                     ↓
              657 Cognitive Executive
                ↙    ↓     ↘
             653    654     652
          Probability Logic Planning
                \     |     /
                     ↓
                    644
                 AI Agent
                     ↓
                   656
```

---

# 209. Thiết kế quan trọng nhất

Axiom giờ có thể phân biệt rõ bốn tầng:

```text
655 = What is happening?
656 = How can I physically act?
657 = What should I focus on and coordinate now?
652 = Which plan satisfies the objectives?
```

Trong khi:

```text
653 = How uncertain is this?
654 = What follows formally from these facts/rules?
650 = What do I remember?
644 = How do I orchestrate an agent?
```

Đây là separation quan trọng để tránh biến toàn bộ AI runtime thành một "LLM loop" khó kiểm soát.

---

# 210. Completion Definition

BOOTSTRAP-657 hoàn thành khi Axiom có specification thực thi được cho:

- cognitive executive;
- cognitive state;
- attention;
- attention budgeting;
- working memory;
- context assembly;
- context compression;
- goal hierarchy;
- goal stack;
- task graph;
- task scheduling;
- strategy selection;
- strategy switching;
- belief management;
- expectation;
- uncertainty awareness;
- knowledge gaps;
- information-seeking;
- reflection;
- metacognition;
- self-monitoring;
- prediction-error monitoring;
- tool selection;
- tool validation;
- tool retry;
- human-in-the-loop;
- delegation;
- multi-agent cognition;
- commitment;
- assumption monitoring;
- cognitive budgets;
- deadline-aware cognition;
- realtime cognition;
- durable cognition;
- checkpoint/recovery;
- cognitive replay;
- LLM/provider abstraction;
- non-LLM reasoning integration;
- model fallback;
- prompt/context security;
- sandboxing;
- simulation/counterfactual reasoning;
- adaptive strategies;
- learning feedback;
- structured cognitive audit;
- compiler annotations;
- compiler IR;
- runtime profiles;
- security boundary;
- governance boundary;
- **≥130 invariants**;
- **≥1,400 acceptance criteria**.

**BOOTSTRAP-657 — COMPLETE.**

**Next task: BOOTSTRAP-658 — Native AI Social Intelligence, Theory of Mind, Multi-Agent Interaction, Communication, Negotiation, Cooperation, Competition, Social Memory & Collective Intelligence Runtime 5.0.**

:::