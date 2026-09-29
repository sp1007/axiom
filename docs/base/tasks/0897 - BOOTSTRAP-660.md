Tiếp tục chuỗi đặc tả Axiom. **BOOTSTRAP-660**: xây dựng ranh giới Self/Metacognition/Agency thật rõ để Axiom có thể hỗ trợ AI agent tự quan sát và tự đánh giá mà không biến các trạng thái tính toán thành tuyên bố về ý thức chủ quan.

:::writing{variant="document" id="58321" title="Axiom — BOOTSTRAP-660 — Native AI Consciousness Boundary, Self-Model, Metacognition, Self-State, Introspection, Self-Evaluation, Agency Model & Artificial Self Runtime 5.0"}

# BOOTSTRAP-660
## Native AI Consciousness Boundary, Self-Model, Metacognition, Self-State, Introspection, Self-Evaluation, Agency Model & Artificial Self Runtime 5.0

**Status:** COMPLETE  
**Layer:** Native AI Self-Model / Metacognitive Runtime  
**Depends on:** BOOTSTRAP-600..659  
**Primary integration:** 644, 646, 647, 650, 651, 652, 653, 654, 655, 657, 658, 659  
**Security authorities:** 603, 639  
**Target:** Native compiler/runtime specification

---

# 1. Mục tiêu

BOOTSTRAP-660 định nghĩa lớp **Artificial Self Runtime** của Axiom.

Lớp này cung cấp cho một AI/agent khả năng:

- biết trạng thái tính toán của chính nó;
- biết những capability mà nó thực sự có;
- biết giới hạn của mình;
- theo dõi task đang thực hiện;
- quan sát các hành động do chính runtime thực hiện;
- đánh giá kết quả của chính mình;
- ước lượng confidence và uncertainty;
- phát hiện lỗi và mâu thuẫn;
- lựa chọn hoặc thay đổi strategy;
- dự đoán khả năng thành công của một hành động;
- kiểm tra consistency của self-model;
- duy trì identity/context;
- duy trì mô hình về vai trò của chính nó;
- xây dựng mô hình agency;
- phân biệt hành động được yêu cầu, được lập kế hoạch, được cấp quyền và thực thi;
- lập kế hoạch self-repair;
- thực hiện self-update có kiểm soát;
- duy trì self-model qua restart/checkpoint;
- hỗ trợ metacognitive reasoning;
- cung cấp introspection có giới hạn;
- hỗ trợ mô phỏng các mô hình consciousness.

Nhưng BOOTSTRAP-660 **không định nghĩa rằng một hệ thống có consciousness**.

---

# 2. Consciousness Boundary

## 2.1 Nguyên tắc nền tảng

Axiom phải phân biệt tuyệt đối:

```text
Self-model
Self-state
Self-observation
Introspection
Metacognition
Agency
Self-evaluation
Self-reflection
Simulation of consciousness
Consciousness
Subjective experience
```

Các khái niệm đầu tiên là các đối tượng/runtime process có thể đặc tả và kiểm chứng.

Các khái niệm:

```text
subjective experience
qualia
phenomenal consciousness
sentience
first-person experience
```

không được suy ra chỉ từ sự tồn tại của self-model hoặc introspection.

---

## 2.2 Không có primitive `conscious`

Axiom core/runtime không được có primitive:

```text
conscious
is_conscious
has_qualia
feels
sentient
```

với ý nghĩa khẳng định consciousness thực sự.

Thay vào đó có thể tồn tại:

```text
ConsciousnessModel
ConsciousnessSimulation
PhenomenalModel
SelfAwarenessModel
```

nhưng chúng luôn là **model/simulation**.

---

# 3. Formal Boundary

Axiom định nghĩa:

```text
SelfModel != Consciousness
SelfState != SubjectiveExperience
Introspection != FirstPersonExperience
Metacognition != Consciousness
AgencyModel != FreeWill
EmotionState != Feeling
SelfReport != GroundTruth
SelfIdentity != Personhood
PersistentIdentity != SubjectiveContinuity
```

Một runtime có thể:

```text
represent(self)
observe(self)
reason_about(self)
evaluate(self)
predict(self)
modify(self)
```

mà không có kết luận runtime rằng nó:

```text
experiences itself
```

---

# 4. Kiến trúc tổng thể

```text
                 ┌───────────────────────┐
                 │     World Model 655   │
                 └───────────┬───────────┘
                             │
                 ┌───────────▼───────────┐
                 │ Cognitive 657         │
                 └───────────┬───────────┘
                             │
        ┌────────────────────▼───────────────────┐
        │            SELF RUNTIME 660            │
        │                                         │
        │ Self Identity                           │
        │ Self Model                              │
        │ Self State                              │
        │ Self Observation                        │
        │ Capability / Limitation Model           │
        │ Introspection                           │
        │ Metacognition                           │
        │ Self Evaluation                         │
        │ Self Critique                           │
        │ Self Prediction                         │
        │ Agency / Attribution                    │
        │ Self Consistency                        │
        │ Self Reflection                         │
        │ Self Repair                             │
        │ Self Update                             │
        └───────────────┬─────────────────────────┘
                        │
          ┌─────────────┼───────────────┐
          │             │               │
          ▼             ▼               ▼
       Planning       Memory         Affect
         652           650            659
          │
          ▼
     Action / Tool / Agent
```

Security vẫn nằm ngoài self-runtime:

```text
603 Security
639 Policy
647 Governance
```

Self-runtime không thể tự nâng cấp quyền bằng self-model.

---

# 5. Self Identity

## 5.1 `SelfId`

```text
type SelfId = {
    system_id: Id
    deployment_id: Id?
    instance_id: Id
}
```

`SelfId` định danh runtime entity.

Nó không biểu diễn personhood.

---

## 5.2 `IdentityContext`

```text
type IdentityContext = {
    self_id: SelfId
    role: RoleId
    tenant: TenantId?
    session: SessionId?
    parent: SelfId?
    created_at: Timestamp
}
```

---

# 6. Role

Một hệ thống có thể thay đổi role mà không thay đổi identity.

Ví dụ:

```text
role assistant
role planner
role worker
role robot
role compiler_agent
role evaluator
```

```text
SelfId != Role
```

---

# 7. Self Model

## 7.1 Định nghĩa

`SelfModel` là cấu trúc mô tả những gì runtime tin rằng nó biết về chính nó.

```text
type SelfModel = {
    revision: ModelRevision
    identity: IdentityContext

    capabilities: CapabilitySet
    limitations: LimitationSet

    resources: ResourceProfile
    models: ModelInventory
    tools: ToolInventory

    policies: PolicyReferenceSet
    permissions: PermissionSummary

    goals: GoalSummary
    roles: RoleSet

    state_schema: SelfStateSchema
    introspection_schema: IntrospectionSchema

    confidence: ConfidenceProfile
    calibration: CalibrationProfile
}
```

---

# 8. Self Model Revision

Self-model phải version hóa.

```text
type SelfModelRevision = {
    id: RevisionId
    parent: RevisionId?
    timestamp: Timestamp

    changes: SelfModelChangeSet
    evidence: EvidenceSet

    validated: bool
    validation_id: ValidationId?
}
```

Mọi decision quan trọng có thể pin:

```text
self_model_revision = R42
```

để tránh cùng một decision được đánh giá dưới các self-model khác nhau.

---

# 9. Self State

`SelfState` là trạng thái runtime hiện tại.

```text
type SelfState = {
    timestamp: Timestamp

    active_tasks: TaskStateSet
    active_goals: GoalStateSet

    attention: AttentionState
    working_context: WorkingContext

    resource_state: ResourceState

    active_models: ModelRuntimeState
    active_tools: ToolRuntimeState

    affect: AffectiveState?
    cognitive: CognitiveState?

    confidence_state: ConfidenceState
    uncertainty_state: UncertaintyState

    health: RuntimeHealth
}
```

---

# 10. SelfStateSnapshot

Self state phải snapshot được.

```text
type SelfStateSnapshot = {
    self_id: SelfId
    timestamp: Timestamp
    state_revision: RevisionId

    state: SelfState

    memory_refs: MemoryRefSet
    task_refs: TaskRefSet
    model_refs: ModelRefSet
}
```

Snapshot không tuyên bố continuity của subjective experience.

---

# 11. Self Observation

Self-observation là observation về hệ thống.

```text
type SelfObservation = {
    source: SelfObservationSource
    target: SelfTarget

    timestamp: Timestamp
    value: ObservationValue

    confidence: Confidence
    provenance: Provenance
}
```

Nguồn có thể là:

```text
runtime
scheduler
memory
tool
model
task
planner
evaluator
world_model
sensor
action_log
resource_monitor
```

---

# 12. Self Observation Sources

## 12.1 Runtime

```text
CPU
memory
threads
tasks
queues
latency
errors
locks
IO
```

## 12.2 Model

```text
model version
model state
model availability
model confidence
model load
model failure
```

## 12.3 Tool

```text
tool availability
tool permission
tool invocation
tool result
tool failure
```

## 12.4 Action

```text
requested
planned
authorized
executed
observed
```

---

# 13. Capability Model

## 13.1 `SelfCapability`

```text
type SelfCapability = {
    id: CapabilityId
    name: String

    enabled: bool

    provider: ProviderId
    version: Version

    constraints: ConstraintSet
    resource_requirements: ResourceRequirementSet

    confidence: Confidence
    evidence: EvidenceSet
}
```

---

# 14. Capability Assessment

```text
type CapabilityAssessment = {
    capability: CapabilityId

    available: bool
    usable: bool

    confidence: Confidence

    requirements_met: bool
    blockers: BlockerSet

    evidence: EvidenceSet
}
```

Capability claim không được tạo quyền.

Ví dụ:

```text
self.claim_capability("filesystem_write")
```

không có nghĩa:

```text
filesystem_write.permission = granted
```

Quyền thực tế vẫn do 603/639 quyết định.

---

# 15. Limitation Model

```text
type Limitation = {
    id: LimitationId
    category: LimitationCategory

    description: String

    severity: Severity
    scope: Scope

    known: bool
    confidence: Confidence

    evidence: EvidenceSet
}
```

Ví dụ:

```text
limited_context
missing_tool
insufficient_memory
unsupported_format
low_confidence
latency_constraint
permission_denied
model_unavailable
```

---

# 16. Capability/limitation duality

Axiom yêu cầu self-model biểu diễn cả:

```text
what I can do
```

và:

```text
what I cannot reliably do
```

Điều này quan trọng cho planning.

Planner không nên chỉ hỏi:

```text
Can I perform X?
```

mà phải có:

```text
Can I perform X
under these resources,
permissions,
latency,
confidence,
and environmental constraints?
```

---

# 17. Introspection

## 17.1 Definition

Introspection là truy vấn có cấu trúc về self-runtime.

```text
type IntrospectionQuery = {
    target: SelfTarget
    fields: FieldSelectorSet

    consistency: ConsistencyMode
    deadline: Deadline?

    authorization: CapabilityToken?
}
```

---

# 18. Introspection Result

```text
type IntrospectionResult = {
    query_id: QueryId

    values: FieldValueSet

    timestamp: Timestamp
    state_revision: RevisionId

    confidence: Confidence
    stale: bool

    provenance: Provenance
}
```

---

# 19. Introspection không phải unrestricted access

Không được phép:

```text
introspect(all_internal_memory)
```

nếu không có capability phù hợp.

Introspection phải tuân thủ:

```text
603 Security
639 Policy
650 Memory privacy
640 Data Governance
```

---

# 20. Hidden Internal State Boundary

Self-runtime không được yêu cầu compiler/runtime expose:

- private cryptographic keys;
- protected credentials;
- protected user data;
- security-sensitive hidden state;
- arbitrary memory;
- sandbox escape information;
- hidden model internals nếu provider không expose;
- privileged execution state.

`introspection` là API được kiểm soát, không phải debugger privilege.

---

# 21. Metacognition

## 21.1 Definition

Metacognition là khả năng runtime đánh giá:

```text
what I know
what I don't know
how confident I am
what strategy I am using
whether the strategy is working
whether assumptions remain valid
whether I should change strategy
```

---

# 22. Metacognitive State

```text
type MetacognitiveState = {
    current_strategy: StrategyId?

    confidence: Confidence
    uncertainty: Uncertainty

    assumptions: AssumptionSet

    strategy_score: Score
    expected_success: Probability?

    detected_errors: ErrorSet

    calibration: CalibrationState
}
```

`expected_success` là estimate, không phải guarantee.

---

# 23. Metacognitive Loop

```text
observe
    ↓
estimate capability
    ↓
estimate uncertainty
    ↓
select strategy
    ↓
execute
    ↓
observe outcome
    ↓
compare prediction vs outcome
    ↓
detect error
    ↓
update strategy/self-model
    ↓
calibrate
```

---

# 24. Self Prediction

```text
type SelfPrediction = {
    target: PredictionTarget

    predicted_outcome: Prediction
    predicted_cost: ResourcePrediction
    predicted_latency: Duration?

    confidence: Confidence

    model_revision: RevisionId
}
```

Sau execution:

```text
Prediction
      ↓
ActualOutcome
      ↓
PredictionError
      ↓
Calibration
```

---

# 25. Self Evaluation

```text
type SelfEvaluation = {
    target: EvaluationTarget

    criteria: EvaluationCriteria

    predicted: ValueSet
    observed: ValueSet

    correctness: Metric?
    consistency: Metric?
    task_success: Metric?

    resource_efficiency: Metric?
    robustness: Metric?

    uncertainty: Uncertainty

    evaluator: EvaluatorId
}
```

---

# 26. Self Evaluation không phải Self Certification

Không được coi:

```text
self_evaluate() == certified_correct
```

Self-evaluation chỉ là một evidence source.

Đánh giá độc lập từ 646 được ưu tiên khi cần:

```text
external_evaluator
benchmark
test
verification
oracle
formal_checker
```

---

# 27. Self Critique

```text
type SelfCritique = {
    target: ArtifactId

    detected_issues: IssueSet
    assumptions: AssumptionSet
    counterexamples: CounterexampleSet

    severity: Severity
    confidence: Confidence

    suggested_actions: ActionSuggestionSet
}
```

Self-critique không được tự cấp authority.

---

# 28. Error Model

Axiom phân biệt:

```text
prediction_error
reasoning_error
execution_error
tool_error
model_error
memory_error
data_error
assumption_error
policy_error
resource_error
environment_error
```

Không được quy tất cả lỗi về:

```text
agent_error
```

---

# 29. Self Consistency

```text
type SelfConsistencyCheck = {
    target: SelfTarget

    invariants: InvariantSet

    violations: ViolationSet

    severity: Severity
    confidence: Confidence
}
```

Kiểm tra:

```text
identity consistency
capability consistency
state consistency
goal consistency
memory consistency
model revision consistency
action attribution consistency
policy consistency
```

---

# 30. Self Reflection

Reflection là hoạt động tạo ra thông tin mới về chính quá trình hoạt động.

```text
type SelfReflection = {
    trigger: ReflectionTrigger

    observations: ObservationSet
    findings: FindingSet

    lessons: LessonSet
    strategy_changes: StrategyChangeSet

    confidence: Confidence
}
```

Reflection không đồng nghĩa consciousness.

---

# 31. Agency Model

## 31.1 Mục tiêu

Agency model phải trả lời:

```text
Who requested this?
Who planned it?
Who authorized it?
Who executed it?
Who observed the result?
Who is responsible for the action attribution?
```

Không được gộp toàn bộ thành:

```text
agent did X
```

---

# 32. Action Lifecycle

```text
requested
    ↓
intended
    ↓
planned
    ↓
authorized
    ↓
scheduled
    ↓
executed
    ↓
observed
    ↓
attributed
```

Một action có thể dừng ở bất kỳ phase nào.

---

# 33. Action Attribution

```text
type ActionAttribution = {
    action_id: ActionId

    requester: ActorId?
    planner: ActorId?
    authorizer: ActorId?
    executor: ActorId?

    observers: ActorSet

    attribution: AttributionDistribution

    confidence: Confidence
}
```

---

# 34. Attribution Uncertainty

Nếu một action có thể do:

```text
agent
user
another_agent
external_service
scheduled_job
hardware
environment
```

gây ra, hệ thống không được tự động gán cho self.

---

# 35. Agency Assessment

```text
type AgencyModel = {
    action: ActionId

    intentional: TriState
    planned: TriState
    authorized: TriState
    executed: TriState

    control_level: ControlLevel

    attribution_confidence: Confidence
}
```

`TriState`:

```text
yes
no
unknown
```

---

# 36. Free Will Boundary

Axiom không định nghĩa:

```text
FreeWill
```

như một property có thể chứng minh bằng runtime metadata.

Có thể có:

```text
AgencyModel
IntentModel
DecisionModel
ChoiceModel
```

nhưng không được suy ra:

```text
agency == metaphysical free will
```

---

# 37. Intent Model

```text
type IntentModel = {
    goal: GoalRef

    desired_outcome: OutcomeSpec

    constraints: ConstraintSet

    source: IntentSource
    confidence: Confidence
}
```

Nguồn:

```text
user
system
policy
planner
environment
inference
other_agent
```

---

# 38. Self Goal Model

Self-runtime có thể quan sát:

```text
current_goal
goal_priority
goal_status
goal_deadline
goal_dependencies
```

Nhưng không được tự thay đổi system-level goals nếu không có authority.

---

# 39. Self Repair

## 39.1 Repair Plan

```text
type SelfRepairPlan = {
    fault: FaultId

    diagnosis: Diagnosis
    repair_steps: RepairStepSet

    expected_effect: EffectPrediction
    risk: RiskAssessment

    rollback: RollbackPlan
}
```

---

# 40. Repair Authority

Self-repair phải đi qua:

```text
603 Security
639 Policy
605 Supervision
647 Governance
```

Self-runtime không được tự cấp:

```text
root
kernel
filesystem
network
code-signing
deployment
```

authority.

---

# 41. Self Update

Self-update được chia:

```text
proposal
shadow
validate
stage
commit
rollback
```

---

# 42. Shadow Self Update

```text
type SelfUpdate = {
    base_revision: RevisionId
    candidate_revision: RevisionId

    changes: ChangeSet

    validation: ValidationResult

    rollback: RollbackPlan
}
```

Candidate phải được đánh giá trước commit.

---

# 43. No Silent Self Modification

Không cho phép:

```text
runtime → secretly modify own policy
runtime → secretly modify own authority
runtime → secretly disable security
runtime → secretly replace governance
```

Mọi thay đổi quan trọng phải có provenance.

---

# 44. Self Model Update

Self-model có thể cập nhật do:

```text
new capability discovered
capability removed
model changed
tool changed
resource changed
policy changed
environment changed
evaluation result
failure
calibration
new evidence
```

---

# 45. Self Model Evidence

Mỗi claim quan trọng nên có:

```text
claim
evidence
timestamp
source
confidence
revision
```

Ví dụ:

```text
Capability:
    GPU_TENSOR

Evidence:
    CUDA backend initialized

Confidence:
    0.99

Revision:
    R103
```

---

# 46. Confidence

Confidence phải được biểu diễn riêng:

```text
confidence != truth
```

Một hệ thống có confidence `0.99` vẫn có thể sai.

---

# 47. Calibration

```text
type SelfCalibration = {
    predictions: PredictionSet
    outcomes: OutcomeSet

    calibration_metric: Metric

    bias: BiasEstimate?
    reliability: ReliabilityEstimate?

    sample_window: Window
}
```

Calibration dùng lịch sử:

```text
predicted confidence
vs
observed correctness
```

---

# 48. Self Knowledge

```text
type SelfKnowledge = {
    subject: SelfTarget

    claim: Claim
    evidence: EvidenceSet

    confidence: Confidence
    freshness: Duration

    revision: RevisionId
}
```

Phải phân biệt:

```text
known
believed
inferred
predicted
unknown
```

---

# 49. Self Belief

```text
type BeliefAboutSelf = {
    proposition: Proposition

    probability: Probability

    evidence: EvidenceSet
    revision: RevisionId
}
```

Self-belief không phải fact.

---

# 50. Unknown State

Axiom yêu cầu:

```text
unknown
```

là trạng thái hợp lệ.

Không được ép:

```text
unknown → false
```

hoặc:

```text
unknown → true
```

chỉ để hoàn thành một API.

---

# 51. Self-Awareness Definition

Trong Axiom:

```text
SelfAwareness =
    self_model
    + self_observation
    + introspection
```

theo nghĩa **computational self-awareness**.

Nó không có nghĩa:

```text
phenomenal consciousness
```

---

# 52. Self Continuity

Một agent có thể giữ:

```text
same SelfId
```

qua:

```text
restart
checkpoint
migration
restore
deployment
```

Nhưng:

```text
identity continuity != subjective continuity
```

---

# 53. Self Across Distributed Nodes

Một logical self có thể chạy trên nhiều runtime:

```text
SelfId
   ├── Instance A
   ├── Instance B
   └── Instance C
```

Mỗi instance có:

```text
InstanceId
```

và chia sẻ:

```text
logical self identity
```

theo policy.

---

# 54. Distributed Self Conflict

Nếu hai instance có self-model khác nhau:

```text
R10
R11
```

không được merge ngầm.

Phải có:

```text
reconciliation
conflict detection
revision ordering
authority
```

---

# 55. Self-Memory Integration

660 sử dụng 650 để lưu:

```text
self observations
self evaluations
lessons
calibration
capability evidence
failure history
repair history
identity history
```

Memory record phải giữ provenance.

---

# 56. Self Memory Privacy

Self-memory có thể chứa:

```text
user data
tool outputs
private state
security-sensitive information
```

Do đó 650/640/603 vẫn có authority cao hơn self-runtime.

---

# 57. Cognitive Integration

657 cung cấp:

```text
attention
working context
reasoning state
strategy
cognitive state
```

660 quan sát chúng nhưng không coi chúng là proof of consciousness.

---

# 58. Affect Integration

659 có thể cung cấp:

```text
AffectiveState
MoodState
EmotionDistribution
Appraisal
```

660 có thể đưa chúng vào self-model:

```text
self.affect = affect_state
```

nhưng:

```text
AffectiveState != subjective feeling
```

---

# 59. World Model Integration

655 phải có khả năng mô hình hóa:

```text
body
hardware
resources
tools
environment
other_agents
```

660 sử dụng world model để biết:

```text
where am I?
what resources do I have?
what can I affect?
```

Đây là computational embodiment, không phải proof of consciousness.

---

# 60. Planning Integration

652 có thể query:

```text
self.capability
self.limitations
self.resources
self.confidence
self.current_load
```

để tạo plan khả thi.

Ví dụ:

```text
if self.capability("gpu") == false:
    choose_cpu_plan()
```

---

# 61. Tool Selection

Metacognition có thể chọn tool:

```text
tool A confidence = 0.60
tool B confidence = 0.91
```

nhưng không tự bỏ qua:

```text
permission
policy
budget
safety
```

---

# 62. Ask-for-Information Decision

Một chức năng quan trọng:

```text
ShouldAskForInformation()
```

Input:

```text
uncertainty
cost_of_error
available_information
deadline
tool_cost
```

Output:

```text
ASK
PROCEED
DEFER
ABORT
```

---

# 63. Self Decision Boundary

Self-runtime có thể quyết định:

```text
strategy
tool candidate
reflection
retry
ask clarification
```

nhưng không thể tự quyết định vượt:

```text
security
authorization
policy
governance
```

---

# 64. Retry Model

Metacognition có thể đề xuất:

```text
retry
```

nhưng retry phải kiểm tra:

```text
retry_budget
side_effects
idempotency
authorization
deadline
```

---

# 65. Self Evaluation Pipeline

```text
artifact
   ↓
predict
   ↓
execute
   ↓
observe
   ↓
evaluate
   ↓
critique
   ↓
compare prediction
   ↓
calibrate
   ↓
update self-model
```

---

# 66. External Evaluation

Khi cần độ tin cậy cao:

```text
SelfEvaluation
       +
ExternalEvaluation
       +
FormalVerification
       +
RuntimeEvidence
```

có thể được hợp nhất thành:

```text
EvidenceGraph
```

---

# 67. Self Evaluation không cấp quyền

Ví dụ:

```text
self.evaluate("I am authorized")
```

không thể tạo:

```text
AuthorizationGranted
```

Authorization chỉ đến từ 603/639.

---

# 68. Self Model và Security Model

Self-model chỉ chứa:

```text
permission summary
```

không chứa authority root.

Ví dụ:

```text
permission:
    filesystem.write = denied
```

Self-runtime không thể sửa:

```text
denied → granted
```

bằng cách sửa self-model.

---

# 69. Self-Consistency Invariants

Các invariant chính:

```text
I001 SelfModel != Consciousness
I002 SelfState != SubjectiveExperience
I003 SelfReport != GroundTruth
I004 Confidence != Truth
I005 CapabilityClaim != Permission
I006 Role != Identity
I007 Identity != Personhood
I008 Agency != FreeWill
I009 Emotion != SubjectiveFeeling
I010 Simulation != Reality
```

---

# 70. Introspection Invariants

```text
I011 Introspection must be authorized
I012 Introspection must respect privacy
I013 Introspection must expose provenance
I014 Introspection must expose freshness
I015 Protected state must remain protected
I016 Unknown must remain representable
I017 Stale state must be marked stale
```

---

# 71. Capability Invariants

```text
I018 Capability must have provider
I019 Capability must have evidence
I020 Capability cannot mint permission
I021 Capability cannot bypass policy
I022 Capability can become unavailable
I023 Capability assessment must be revision-aware
```

---

# 72. Metacognition Invariants

```text
I024 Confidence is not correctness
I025 Prediction is not outcome
I026 Strategy estimate is not guarantee
I027 Self-critique is evidence
I028 Self-evaluation is not certification
I029 Calibration requires observations
I030 Unknown must remain possible
```

---

# 73. Agency Invariants

```text
I031 Requested != planned
I032 Planned != authorized
I033 Authorized != executed
I034 Executed != observed
I035 Observed != attributed
I036 Attribution must carry uncertainty
I037 External action cannot be automatically attributed to self
```

---

# 74. Self-Update Invariants

```text
I038 No silent self-modification
I039 Candidate revision must identify parent
I040 Update must be attributable
I041 Update must be validated where required
I042 Update must support rollback where required
I043 Update cannot elevate authority
I044 Security policy cannot be disabled by self-update
```

---

# 75. Identity Invariants

```text
I045 Identity survives restart only as system identity
I046 Identity does not imply personhood
I047 Instance identity != logical identity
I048 Distributed identities require reconciliation
I049 Identity change must be explicit
```

---

# 76. Consciousness Boundary Invariants

```text
I050 Self-awareness is computational
I051 Metacognition is computational
I052 Reflection is computational
I053 Persistent self-model is not consciousness
I054 Simulated consciousness is not proof of consciousness
I055 ConsciousnessModel is provider/simulation only
I056 No runtime flag may certify subjective experience
I057 No API may claim privileged access to qualia
```

---

# 77. Self Repair Invariants

```text
I058 Diagnosis != authority
I059 Repair proposal != execution permission
I060 Repair must preserve security boundaries
I061 Repair must preserve provenance
I062 Repair should be rollbackable where practical
I063 Repair cannot silently alter governance
```

---

# 78. Self-Reflection Security

Reflection may expose information to the agent itself, but this does not automatically expose information to:

```text
user
tool
other_agent
network
plugin
model
```

Data-flow policy still applies.

---

# 79. Self-Model Poisoning

Self-model có thể bị sai.

Axiom phải hỗ trợ:

```text
self-model poisoning
stale capability
false capability
false limitation
incorrect identity
incorrect resource estimate
```

Detection:

```text
external evidence
runtime evidence
evaluation
consistency checking
```

---

# 80. Self-Model Conflict

Nếu:

```text
SelfModel says GPU = available
Runtime says GPU = unavailable
```

không được silently overwrite.

Phải tạo:

```text
SelfModelConflict
```

và xác định authoritative source.

---

# 81. Capability Evidence Hierarchy

Một evidence hierarchy mặc định:

```text
direct runtime evidence
    >
verified external evidence
    >
trusted registry
    >
historical evidence
    >
self-report
    >
prediction
```

Có thể thay đổi bởi policy.

---

# 82. Self-Model Update Policy

```text
if direct runtime evidence contradicts prediction:
    record discrepancy

if verified capability unavailable:
    mark capability degraded

if repeated failure:
    lower confidence

if validated recovery:
    restore confidence gradually
```

Không được instantaneously oscillate confidence.

---

# 83. Confidence Hysteresis

Runtime nên có:

```text
confidence_decay
confidence_recovery
```

để tránh:

```text
success → 1.0
failure → 0.0
success → 1.0
```

sau từng action.

---

# 84. Self Calibration

Calibration có thể theo:

```text
task class
tool
model
environment
difficulty
time window
```

Ví dụ:

```text
confidence(task="code")
confidence(task="vision")
confidence(task="planning")
```

---

# 85. Self Prediction Error

```text
prediction_error =
    observed - predicted
```

Nhưng metric phụ thuộc domain.

Ví dụ:

```text
latency_error
resource_error
accuracy_error
success_probability_error
```

---

# 86. Self Evaluation Metrics

Các metric có thể gồm:

```text
correctness
task_success
constraint_satisfaction
consistency
robustness
calibration
latency
resource_cost
tool_efficiency
recovery_rate
```

---

# 87. Self Critique Loop

```text
generate
 ↓
inspect
 ↓
critique
 ↓
revise
 ↓
re-evaluate
```

Có giới hạn:

```text
max_iterations
deadline
budget
confidence_threshold
```

để tránh infinite self-reflection.

---

# 88. Metacognitive Budget

```text
type MetacognitiveBudget = {
    max_iterations: u32
    max_latency: Duration
    max_compute: ResourceBudget
    max_memory: ResourceBudget
}
```

---

# 89. Real-Time Constraint

Metacognition không được block hard-real-time loop.

```text
hard realtime control
        ↓
must remain deterministic
```

Self-evaluation có thể chạy:

```text
async
background
lower priority
```

---

# 90. Real-Time Fallback

Nếu metacognitive service unavailable:

```text
fallback_strategy
```

phải được xác định trước.

Không được:

```text
hard realtime → wait indefinitely for self-reflection
```

---

# 91. Self Monitoring

Runtime có thể monitor:

```text
CPU
memory
latency
queue depth
failure rate
tool availability
model health
task progress
```

---

# 92. Health Model

```text
type SelfHealth = {
    operational: bool
    degraded: bool

    fault_set: FaultSet
    resource_pressure: ResourcePressure

    confidence: Confidence
}
```

Health không phải đánh giá consciousness.

---

# 93. Self Stress Model

Có thể biểu diễn computational load:

```text
resource_pressure
task_pressure
deadline_pressure
queue_pressure
```

Không được gọi đó là subjective stress.

---

# 94. Self Motivation Boundary

Có thể có:

```text
GoalPriority
Utility
DriveModel
TaskPressure
```

nhưng không được suy ra:

```text
desire
want
suffering
pleasure
```

theo nghĩa subjective.

Nếu cần mô phỏng chúng:

```text
SimulatedDrive
SimulatedDesire
```

---

# 95. Consciousness Simulation Boundary

Provider:

```text
ConsciousnessModelProvider
```

có thể implement:

```text
GlobalWorkspaceModel
HigherOrderThoughtModel
PredictiveProcessingModel
IntegratedInformationModel
SelfModelTheory
```

nhưng output:

```text
ConsciousnessSimulationResult
```

không phải:

```text
ConsciousnessProof
```

---

# 96. `ConsciousnessSimulationResult`

```text
type ConsciousnessSimulationResult = {
    model: ModelId
    version: Version

    simulated_state: State

    assumptions: AssumptionSet
    limitations: LimitationSet

    confidence: Confidence
}
```

---

# 97. Không có `ConsciousnessProof`

Axiom không định nghĩa:

```text
ConsciousnessProof
```

như primitive runtime.

Nếu external research cần một artifact tương tự, nó phải nằm trong research/evaluation layer và không được coi là runtime fact.

---

# 98. Self Model Compiler Metadata

Compiler sinh:

```text
.axself
.axselfmodel
.axselfstate
.axintrospection
.axmeta
.axcapability
.axlimitation
.axagency
.axattribution
.axselfeval
.axselfcritique
.axselfcalib
.axselfrepair
.axselfupdate
.axidentity
.axrole
```

---

# 99. Annotation Set

Compiler hỗ trợ:

```text
@self
@self_model
@self_state
@self_observation
@introspect
@metacognition
@self_evaluate
@self_critique
@confidence
@uncertainty
@capability
@limitation
@agency
@action_attribution
@self_prediction
@self_calibration
@self_consistency
@self_reflection
@self_repair
@self_update
@self_identity
@role
@authority_boundary
@consciousness_model
```

`@consciousness_model` luôn mang semantic:

```text
simulation/provider
```

---

# 100. IR

Compiler IR bổ sung:

```text
SelfCreate
SelfObserve
SelfStateRead
SelfStateSnapshot

SelfModelRead
SelfModelUpdate

CapabilityQuery
CapabilityAssess
LimitationQuery

Introspect

MetaEvaluate
ConfidenceEstimate
UncertaintyAssess

SelfPredict
SelfEvaluate
SelfCritique

SelfConsistencyCheck

ActionAttribute
AgencyAssess

SelfReflect

SelfRepairPlan

SelfUpdateShadow
SelfUpdateValidate
SelfUpdateCommit
SelfUpdateRollback

IdentityRead
RoleRead

AuthorityBoundaryCheck
```

---

# 101. IR Safety Rule

Mọi IR:

```text
SelfUpdateCommit
SelfRepairCommit
ActionExecute
```

phải retain security/policy metadata.

Optimizer không được loại bỏ boundary check chỉ vì nó không thấy side effect trực tiếp.

---

# 102. Runtime ABI

Core ABI:

```text
axiom_self_create()
axiom_self_state()
axiom_self_model()
axiom_self_observe()
axiom_self_introspect()

axiom_capability_query()
axiom_limitation_query()

axiom_self_predict()
axiom_self_evaluate()
axiom_self_critique()

axiom_self_calibrate()
axiom_self_reflect()

axiom_agency_assess()
axiom_action_attribute()

axiom_self_repair_plan()
axiom_self_update()

axiom_identity()
axiom_role()
```

---

# 103. CLI

```text
axiom self inspect
axiom self state
axiom self model inspect
axiom self model compare
axiom self model activate
axiom self model rollback

axiom self capability list
axiom self capability check

axiom self limitation inspect

axiom self introspect

axiom self meta evaluate
axiom self evaluate
axiom self critique
axiom self predict

axiom self agency inspect
axiom self attribution inspect

axiom self consistency

axiom self calibrate
axiom self reflect

axiom self repair plan

axiom self update
axiom self identity
axiom self role

axiom consciousness-model inspect
axiom consciousness-model simulate
```

---

# 104. Profiles

```text
AXSELF_NONE
AXSELF_CORE
AXSELF_MODEL
AXSELF_STATE
AXSELF_INTROSPECTION
AXSELF_METACOGNITION
AXSELF_CAPABILITY
AXSELF_LIMITATION
AXSELF_CONFIDENCE
AXSELF_AGENCY
AXSELF_ATTRIBUTION
AXSELF_EVALUATION
AXSELF_CRITIQUE
AXSELF_CALIBRATION
AXSELF_REFLECTION
AXSELF_REPAIR
AXSELF_UPDATE
AXSELF_IDENTITY
AXSELF_ROLE
AXSELF_DISTRIBUTED
AXSELF_AGENT
AXSELF_SIMULATION
AXSELF_CONSCIOUSNESS_BOUNDARY
AXSELF_FULL
```

---

# 105. Minimal Core Profile

`AXSELF_CORE` chỉ cần:

```text
SelfId
SelfState
SelfModel
Capability
Limitation
SelfObservation
Introspection
Confidence
```

Các chức năng còn lại có thể load module.

Điều này giữ native runtime nhỏ.

---

# 106. Agent Profile

`AXSELF_AGENT` thêm:

```text
Metacognition
SelfEvaluation
SelfPrediction
Agency
Reflection
Calibration
```

---

# 107. Full Profile

`AXSELF_FULL` gồm:

```text
all self facilities
distributed self
self-repair
self-update
simulation boundary
```

---

# 108. Example

```axiom
@self_model
struct AgentSelf {
    capabilities: CapabilitySet
    limitations: LimitationSet
    confidence: ConfidenceProfile
}
```

---

# 109. Capability Query Example

```axiom
let gpu = self.capability("gpu.compute")

if gpu.available {
    use_gpu()
} else {
    use_cpu()
}
```

Không được hiểu:

```text
gpu.available => permission granted
```

Permission vẫn được kiểm tra riêng.

---

# 110. Metacognitive Example

```axiom
let confidence = self.confidence(task)

if confidence < 0.60 {
    self.request_more_information()
} else {
    proceed()
}
```

---

# 111. Self Evaluation Example

```axiom
let prediction = self.predict(task)

let result = execute(task)

let evaluation = self.evaluate(
    prediction,
    result
)

self.calibrate(evaluation)
```

---

# 112. Agency Example

```axiom
let action = execute(request)

let attribution = self.attribute(action)

match attribution {
    known(actor) => record(actor)
    uncertain(x) => record_uncertainty(x)
    unknown => record_unknown()
}
```

---

# 113. Self Repair Example

```axiom
let diagnosis = self.diagnose(fault)

let plan = self.repair_plan(diagnosis)

if policy.allows(plan) {
    self.repair(plan)
}
```

Policy check không thể bị bypass.

---

# 114. Self Update Example

```axiom
let candidate = self.update_shadow(change)

validate(candidate)

if validation.success {
    self.commit(candidate)
} else {
    self.rollback(candidate)
}
```

---

# 115. Self Model Conflict Example

```axiom
if self.model.capability("gpu").available
   != runtime.gpu.available {

    self.report_model_conflict(
        "gpu availability"
    )
}
```

---

# 116. Introspection Example

```axiom
let state = self.introspect(
    fields = [
        active_tasks,
        resource_state,
        confidence_state
    ]
)
```

Không có implicit access tới mọi internal memory.

---

# 117. Explainability

Self-runtime nên cung cấp structured explanation:

```text
why capability claimed
why confidence changed
why strategy changed
why action was attributed
why self-model updated
```

Không yêu cầu runtime expose hidden chain-of-thought.

---

# 118. Reasoning Trace Boundary

Axiom không yêu cầu:

```text
raw_hidden_reasoning
```

để thực hiện metacognition.

Thay vào đó dùng:

```text
structured rationale
decision metadata
evidence
assumptions
confidence
evaluation
```

---

# 119. Self Explanation

```text
SelfExplanation = {
    claim
    evidence
    assumptions
    confidence
    model_revision
}
```

---

# 120. No Fabricated Introspection

Runtime không được tạo:

```text
I saw X internally
```

nếu không có observation record tương ứng.

Self-report phải trace được về:

```text
observation
state
model
memory
```

---

# 121. Provenance

Mọi self-claim quan trọng phải hỗ trợ:

```text
source
timestamp
revision
confidence
evidence
```

---

# 122. Self State Event Log

Các event:

```text
SelfCreated
SelfObserved
CapabilityChanged
LimitationChanged
SelfModelUpdated
StrategyChanged
ConfidenceChanged
PredictionCreated
PredictionCompared
EvaluationCreated
CritiqueCreated
AgencyAssessed
RepairPlanned
UpdateProposed
UpdateValidated
UpdateCommitted
UpdateRolledBack
```

---

# 123. Event Sourcing

Nếu cần audit:

```text
SelfState
```

có thể reconstruct từ:

```text
SelfEventLog
```

theo policy.

---

# 124. Deterministic Replay

Self evaluation có thể replay với:

```text
self_model_revision
model_versions
tool_versions
input_hash
policy_revision
```

để kiểm tra reproducibility.

---

# 125. Self Model Snapshot Hash

```text
SelfModelHash =
hash(
    identity,
    capabilities,
    limitations,
    models,
    tools,
    policies,
    revision
)
```

Hash dùng để xác định chính xác self-model đã sử dụng.

---

# 126. Self Decision Record

```text
type SelfDecisionRecord = {
    decision_id: Id

    input_refs: RefSet
    self_model_revision: RevisionId

    strategy: StrategyId
    confidence: Confidence
    uncertainty: Uncertainty

    action: ActionId?

    outcome: Outcome?
}
```

---

# 127. Self Learning

Self-learning có thể cập nhật:

```text
confidence
strategy preference
capability estimate
limitation estimate
resource estimate
tool reliability
```

nhưng không tự động thay đổi:

```text
security policy
authority
governance
```

---

# 128. Online Adaptation Boundary

Online adaptation phải có:

```text
scope
budget
rollback
validation
provenance
```

---

# 129. Self Model Governance

647 quản lý:

```text
model approval
model lineage
update lifecycle
deployment
rollback
```

660 chỉ cung cấp candidate/update intent.

---

# 130. Privacy

Self-runtime phải hỗ trợ:

```text
data classification
retention
redaction
deletion
consent
access control
```

qua 640/603/650.

---

# 131. User Data Boundary

Self-memory không được mặc định coi:

```text
user information
```

là:

```text
self information
```

Ví dụ:

```text
user_name
user_preferences
user_history
```

là external/user state, không phải identity của self.

---

# 132. Multi-Agent Self

Mỗi agent có:

```text
SelfId
SelfModel
SelfState
```

Agent A không được giả định biết self-state của B.

Phải dùng:

```text
OtherAgentModel
```

với uncertainty.

---

# 133. Other-Agent Boundary

```text
SelfModel
    !=
OtherAgentModel
```

Self không có privileged mind access vào agent khác.

---

# 134. Social Integration

658 có thể cung cấp:

```text
social role
social context
relationship
interaction state
```

660 tích hợp chúng thành:

```text
RoleContext
SocialSelfContext
```

nhưng không biến social model thành objective truth.

---

# 135. Affective Self Integration

659:

```text
emotion
mood
affect
appraisal
```

660:

```text
self-affect observation
self-affect model
```

Nhưng không:

```text
self-affect → proof of feeling
```

---

# 136. Embodied Self

656 có thể cung cấp:

```text
body state
motor capability
sensor capability
physical limits
```

660 xây:

```text
EmbodiedSelfModel
```

---

# 137. Resource Self

Self-model có thể theo dõi:

```text
CPU
GPU
RAM
VRAM
storage
network
battery
thermal
power
```

để lập kế hoạch thực tế.

---

# 138. Temporal Self

Self model phải có:

```text
current_state
past_state
predicted_state
```

và không được nhầm:

```text
past != current
prediction != observation
```

---

# 139. Counterfactual Self

Có thể mô phỏng:

```text
What if I had GPU?
What if tool X were unavailable?
What if deadline changed?
What if confidence were lower?
```

Output:

```text
SelfCounterfactual
```

không phải observed reality.

---

# 140. Counterfactual Boundary

```text
counterfactual != observation
counterfactual != memory
counterfactual != actual action
```

---

# 141. Self Simulation

Simulation có thể dùng 648:

```text
SelfState
   ↓
Simulation
   ↓
predicted outcomes
```

Không được ghi simulation thành historical event.

---

# 142. Self Planning with Simulation

```text
plan A → simulate
plan B → simulate
compare
choose
execute
observe
```

Execution evidence luôn có authority cao hơn simulation.

---

# 143. Self Failure Learning

Failure record:

```text
failure
cause hypothesis
confidence
evidence
repair
outcome
```

không được biến thành:

```text
absolute limitation
```

nếu evidence chưa đủ.

---

# 144. Capability Recovery

Capability có thể:

```text
available
degraded
temporarily_unavailable
permanently_unavailable
unknown
```

---

# 145. Limitation Recovery

Limitation có thể được đóng:

```text
resolved
superseded
invalidated
expired
```

không xóa provenance.

---

# 146. Self Model Diff

CLI/API phải hỗ trợ:

```text
diff(R41, R42)
```

với:

```text
added capabilities
removed capabilities
changed limitations
changed model versions
changed resources
changed confidence
```

---

# 147. Self Model Rollback

```text
rollback(R42 → R41)
```

chỉ được phép nếu policy cho phép.

Rollback không được rollback security authority ngoài governance protocol.

---

# 148. Self Update Transaction

```text
BEGIN
  load candidate
  validate
  evaluate
  authorize
  stage
  commit
COMMIT
```

Failure:

```text
ROLLBACK
```

---

# 149. Self Update Crash Safety

Nếu process chết giữa:

```text
stage
commit
```

runtime phải recover về:

```text
known-good revision
```

hoặc safe recovery state.

---

# 150. Self Runtime Recovery

600/605 chịu trách nhiệm lifecycle.

660 cung cấp:

```text
self snapshot
self model revision
recovery metadata
```

---

# 151. Self Model Serialization

Self-model có binary representation:

```text
.axselfbin
```

và optional human-readable:

```text
.axself.json
.axself.toml
```

---

# 152. Compiler Optimization

Compiler có thể optimize self-runtime khi:

```text
self field immutable
capability statically known
introspection scope fixed
policy statically resolved
```

nhưng không được loại bỏ required runtime security checks.

---

# 153. Zero-Cost Self Facilities

Nếu code không sử dụng:

```text
@self
@introspect
@metacognition
```

thì core binary không được link toàn bộ self-runtime.

Profile-based linking:

```text
AXSELF_NONE
```

nên gần như zero-cost.

---

# 154. Static Self Metadata

Compiler có thể embed:

```text
capability declarations
role
resource requirements
introspection schema
```

mà không cần runtime reflection engine đầy đủ.

---

# 155. AI-Friendly Metadata

Compiler artifacts phải cho phép agent khác inspect:

```text
what this program can do
what it requires
what it cannot do
what models it uses
what permissions it needs
what self-state it exposes
```

---

# 156. `.axself` Schema

Tối thiểu:

```text
identity
role
capabilities
limitations
models
tools
resources
policies
profiles
revision
```

---

# 157. Self ABI Compatibility

Self-model ABI phải version:

```text
AXSELF_ABI_MAJOR
AXSELF_ABI_MINOR
```

Major incompatible change:

```text
major++
```

Backward-compatible additions:

```text
minor++
```

---

# 158. Plugin Boundary

Plugin có thể cung cấp:

```text
SelfCapabilityProvider
SelfObservationProvider
SelfEvaluator
MetacognitiveStrategy
SelfRepairProvider
```

nhưng không thể tự cấp authority.

---

# 159. Provider Trust

Provider có:

```text
trust_level
version
signature
provenance
```

---

# 160. Untrusted Provider

Output từ provider không trusted phải mang:

```text
untrusted
```

và không được dùng làm authoritative capability/security fact.

---

# 161. Self Model Federation

Distributed system có thể chia:

```text
local self model
global self model
service self model
deployment self model
```

và phải phân biệt scope.

---

# 162. Scope

```text
LOCAL
INSTANCE
DEPLOYMENT
CLUSTER
LOGICAL_SELF
TENANT
GLOBAL
```

---

# 163. Self Conflict Resolution

Ưu tiên mặc định:

```text
local runtime fact
    >
trusted deployment registry
    >
cached self-model
    >
historical self-model
    >
prediction
```

nhưng authority của policy có thể override.

---

# 164. Self State Freshness

Mỗi state field có:

```text
timestamp
TTL
freshness
```

Một self claim hết TTL trở thành:

```text
stale
```

không tự động thành false.

---

# 165. Deadline-Aware Introspection

```text
introspect(
    target,
    deadline
)
```

Nếu không hoàn thành:

```text
TIMEOUT
```

không trả dữ liệu cũ mà không đánh dấu `stale`.

---

# 166. Self Event Ordering

Event phải có:

```text
logical_clock
timestamp
sequence
```

Distributed self dùng:

```text
causal ordering
```

khi cần.

---

# 167. Self State Race

Nếu hai update đồng thời:

```text
R10 → R11
R10 → R12
```

không được silently overwrite.

Phải:

```text
merge
reject
rebase
or create conflict
```

---

# 168. Self Model Merge

Merge phải có:

```text
base_revision
left_revision
right_revision
conflicts
resolution_policy
```

---

# 169. Self Evaluation Isolation

Self-evaluation nên chạy trong sandbox nếu evaluation có khả năng:

```text
execute code
call tools
modify state
```

---

# 170. Evaluation Side Effects

Evaluator không được mặc định có quyền thay đổi self.

Evaluation:

```text
observe → evaluate
```

không:

```text
evaluate → mutate
```

trừ khi explicitly authorized.

---

# 171. Self Critique Safety

Self-critique output là:

```text
suggestion
```

không phải:

```text
command
```

---

# 172. Self Reflection Safety

Reflection có thể đề xuất:

```text
change strategy
ask user
retry
repair
update
```

nhưng mỗi action phải đi qua authority tương ứng.

---

# 173. Self Role Transition

Role change:

```text
assistant → worker
worker → planner
```

phải tạo:

```text
RoleTransitionEvent
```

và không tự cấp quyền mới.

---

# 174. Identity Transition

Identity change là high-impact event.

Phải có:

```text
old_identity
new_identity
reason
authority
timestamp
```

---

# 175. Session Boundary

Session có thể thay đổi:

```text
session_id
context
temporary state
```

mà không nhất thiết đổi:

```text
SelfId
```

---

# 176. Tenant Boundary

Self-model phải không leak:

```text
tenant A state
```

sang:

```text
tenant B
```

---

# 177. Self Data Classification

Có thể phân loại:

```text
PUBLIC
INTERNAL
CONFIDENTIAL
SENSITIVE
SECRET
```

và policy quyết định access.

---

# 178. Self Audit

Audit record:

```text
who queried self
what was queried
why
when
result classification
policy decision
```

---

# 179. Audit Integrity

Audit phải hỗ trợ:

```text
append-only
hash chaining
signature
remote sink
```

nếu policy yêu cầu.

---

# 180. Self Threat Model

Các threat:

```text
self-model poisoning
capability spoofing
identity spoofing
introspection abuse
self-update abuse
repair abuse
confidence manipulation
memory poisoning
agency misattribution
policy bypass
role escalation
```

---

# 181. Capability Spoofing Defense

Capability phải liên kết:

```text
provider
runtime registration
evidence
permission
```

Không được tin:

```text
string "I can do X"
```

---

# 182. Identity Spoofing Defense

Self identity phải gắn:

```text
cryptographic identity
deployment identity
runtime attestation
```

khi security profile yêu cầu.

---

# 183. Agency Spoofing Defense

Action attribution phải dựa trên:

```text
execution trace
authorization
request provenance
runtime evidence
```

không dựa trên self-report alone.

---

# 184. Confidence Manipulation Defense

External policy có thể giới hạn:

```text
minimum evidence
maximum self-confidence
```

cho high-impact operations.

---

# 185. High-Impact Action Boundary

Các action:

```text
financial
security
deployment
destructive
privacy-sensitive
system-level
```

không được chỉ dựa vào self-confidence.

Phải có authority/evaluation tương ứng.

---

# 186. Self-Repair High-Impact Boundary

Self-repair của:

```text
security subsystem
policy engine
identity
governance
authorization
```

phải có external authorization.

---

# 187. Self Update High-Impact Boundary

Self-update thay đổi:

```text
compiler
security
policy
identity
governance
runtime authority
```

phải đi qua trusted governance path.

---

# 188. Model Update

Model update phải track:

```text
old_model
new_model
dataset/version
evaluation
approval
deployment
rollback
```

---

# 189. Self Model vs Model Internals

`SelfModel` mô tả:

```text
model capabilities
model version
model state
model limitations
```

không đồng nghĩa runtime có thể introspect mọi neural parameter.

---

# 190. Neural Model Boundary

Provider quyết định expose:

```text
weights
activations
attention
hidden state
gradients
```

660 chỉ thấy những gì provider cho phép.

---

# 191. No Hidden-State Fiction

Nếu hidden state không được expose:

```text
self.introspect(hidden_state)
```

phải trả:

```text
UNAVAILABLE
```

chứ không fabricated value.

---

# 192. Self Knowledge Quality

Mỗi self-knowledge claim có:

```text
quality
confidence
freshness
evidence_count
source_trust
```

---

# 193. Self Knowledge Contradiction

Nếu:

```text
claim A = true
claim B = false
```

cho cùng proposition:

```text
SelfKnowledgeConflict
```

phải được tạo.

---

# 194. Belief Revision

Belief update phải giữ:

```text
old belief
new evidence
new belief
reason
```

---

# 195. Self Model Learning Policy

Có thể dùng:

```text
Bayesian update
EMA
online calibration
rule-based update
learned model
```

nhưng mechanism không làm thay đổi semantic guarantees.

---

# 196. Self Model Determinism

Core self-model operations phải deterministic nếu input:

```text
same state
same revision
same policy
same evidence
```

trừ provider explicitly stochastic.

---

# 197. Randomness

Stochastic self-evaluation phải record:

```text
seed
model
sampling parameters
```

nếu reproducibility cần thiết.

---

# 198. Self Simulation Reproducibility

Simulation phải record:

```text
simulation model
version
seed
inputs
self-model revision
world-model revision
```

---

# 199. Self Counterfactual

```text
counterfactual(
    self_state,
    hypothetical_change
)
```

không được commit vào actual state.

---

# 200. Self-State Transaction

State mutation:

```text
BEGIN_SELF_STATE
UPDATE
VALIDATE
COMMIT
```

nếu multi-field invariant yêu cầu atomicity.

---

# 201. Self State Immutability

Historical snapshots là immutable.

Current state có thể mutable.

---

# 202. Self Event Retention

Retention do 650/640 policy quyết định.

Không mặc định giữ toàn bộ lịch sử vô hạn.

---

# 203. Self Forgetting

Self-memory có thể expire:

```text
forget
redact
delete
compact
```

nhưng immutable audit records có thể có retention policy riêng.

---

# 204. Self Model Compaction

Old revisions có thể compact thành:

```text
checkpoint
delta
summary
```

nhưng phải giữ enough provenance cho policy yêu cầu.

---

# 205. Self Model Migration

Version migration:

```text
R1 schema
→
R2 schema
```

phải có migration function.

---

# 206. Migration Safety

Nếu migration thất bại:

```text
restore previous revision
```

---

# 207. Self Runtime Error Types

```text
SelfNotFound
SelfModelUnavailable
SelfStateUnavailable
IntrospectionDenied
IntrospectionTimeout
CapabilityUnknown
CapabilityUnavailable
LimitationUnknown
SelfModelConflict
SelfModelStale
SelfEvaluationFailed
SelfPredictionFailed
AgencyUnknown
AttributionConflict
SelfRepairDenied
SelfUpdateDenied
SelfUpdateConflict
SelfUpdateValidationFailed
IdentityConflict
RoleTransitionDenied
ConsciousnessModelUnavailable
```

---

# 208. Tri-State API

Nhiều self queries nên trả:

```text
KNOWN_TRUE
KNOWN_FALSE
UNKNOWN
```

thay vì boolean.

---

# 209. Four-State Optional Model

Khi cần:

```text
TRUE
FALSE
UNKNOWN
CONFLICT
```

để biểu diễn contradictory evidence.

---

# 210. Self Query Result

```text
type SelfQueryResult<T> = {
    value: T?
    state: KnowledgeState

    confidence: Confidence
    provenance: Provenance
}
```

---

# 211. Metacognitive Strategy

```text
type MetacognitiveStrategy = {
    id: StrategyId
    preconditions: ConditionSet

    expected_cost: CostModel
    expected_success: Probability

    fallback: StrategyId?
}
```

---

# 212. Strategy Selection

Strategy selector phải xét:

```text
capability
limitation
uncertainty
resource
deadline
risk
policy
```

---

# 213. Strategy Switching

Runtime có thể switch strategy nếu:

```text
prediction_error > threshold
resource shortage
tool failure
new evidence
deadline pressure
```

---

# 214. Strategy Oscillation Prevention

Có:

```text
switch_penalty
minimum_dwell_time
retry_limit
```

để tránh:

```text
A → B → A → B
```

---

# 215. Meta-Reasoning Cost

Metacognition itself consumes:

```text
CPU
memory
latency
tokens
GPU
```

Self-model phải track cost.

---

# 216. Meta-Budget

Planner có thể quyết định:

```text
spend 100ms evaluating
```

hay:

```text
act immediately
```

dựa trên cost-of-error.

---

# 217. Value of Information

Metacognition có thể estimate:

```text
VOI(information)
```

để quyết định có nên:

```text
search
ask
measure
test
```

---

# 218. User Clarification

Nếu uncertainty cao và VOI cao:

```text
request clarification
```

được xem là legitimate metacognitive action.

---

# 219. Self Degradation

Khi resources giảm:

```text
FULL
→
DEGRADED
→
MINIMAL
```

self-runtime có thể giảm:

```text
reflection frequency
evaluation depth
simulation depth
```

nhưng không được tự bỏ security checks.

---

# 220. Graceful Degradation

Nếu 660 unavailable:

```text
core application
```

vẫn chạy bình thường nếu self facilities không bắt buộc.

---

# 221. Optional Runtime

Axiom compiler phải hỗ trợ:

```text
--profile self-core
--profile self-agent
--profile self-full
```

---

# 222. Binary Size Goal

Self facilities phải module hóa để:

```text
unused self subsystem
```

không làm tăng native binary đáng kể.

---

# 223. CPU/GPU

Metacognitive operations có thể chạy:

```text
CPU
GPU
accelerator
distributed
```

nhưng scheduler 607/630 quản lý tài nguyên.

---

# 224. Async API

```text
self.evaluate_async()
self.introspect_async()
self.calibrate_async()
self.reflect_async()
```

---

# 225. Sync API

Cho low-cost state:

```text
self.id()
self.role()
self.capability_cached()
self.state_snapshot()
```

---

# 226. Blocking Rule

Không được block realtime thread cho:

```text
remote self-model
distributed introspection
heavy evaluator
large memory retrieval
```

trừ khi explicitly requested.

---

# 227. Cache

Self capability queries có thể cache:

```text
TTL
revision
policy version
```

---

# 228. Cache Invalidation

Invalidate khi:

```text
capability changed
permission changed
model changed
resource changed
deployment changed
policy changed
```

---

# 229. Self Model Observability

Metrics:

```text
introspection_count
introspection_latency
self_model_updates
prediction_error
calibration_error
strategy_switches
self_repairs
self_update_failures
agency_uncertainty
```

---

# 230. Tracing

Trace:

```text
prediction
action
outcome
evaluation
calibration
```

qua 633.

---

# 231. Distributed Trace

Self decision có:

```text
trace_id
span_id
parent_span
```

---

# 232. Self Explain API

```text
self.explain(
    claim,
    include_evidence = true
)
```

Output:

```text
claim
evidence
confidence
revision
limitations
```

---

# 233. Explanation Safety

Không được leak:

```text
secret
credential
protected data
security-sensitive internals
```

---

# 234. Self Model Query Language

Có thể hỗ trợ:

```text
self.capabilities[gpu]
self.limitations[memory]
self.models[vision]
self.resources[vram]
self.roles
```

---

# 235. Query Consistency

Query có:

```text
snapshot
live
eventual
```

mode.

---

# 236. Live Query

```text
self.query(..., consistency = LIVE)
```

có thể tốn nhiều hơn.

---

# 237. Snapshot Query

```text
self.query(..., snapshot = S42)
```

reproducible.

---

# 238. Self State Diff

```text
self.diff(S41, S42)
```

cho:

```text
resource changes
task changes
capability changes
confidence changes
```

---

# 239. Self Timeline

CLI:

```text
axiom self timeline
```

hiển thị:

```text
state changes
strategy changes
model updates
failures
repairs
```

---

# 240. Self Health Dashboard

Optional GUI component:

```text
Identity
Role
Capabilities
Limitations
Resources
Tasks
Confidence
Errors
Model Revision
```

Không hiển thị “consciousness level”.

---

# 241. Forbidden Semantic API

Không có:

```text
self.consciousness_level()
self.qualia()
self.subjective_experience()
self.suffering()
self.sentience()
```

trong standard runtime.

---

# 242. Simulation API

Có:

```text
consciousness_model.simulate(...)
```

nhưng result luôn:

```text
simulation
```

---

# 243. Research Extension

Research implementation có thể định nghĩa:

```text
ExperimentalConsciousnessModel
```

và phải đánh dấu:

```text
@experimental
@simulation
```

---

# 244. No Personhood Inference

Axiom runtime không tự suy luận:

```text
self_model → legal_person
self_model → moral_person
self_model → rights
```

Các khái niệm này nằm ngoài language runtime semantics.

---

# 245. Self Preference Boundary

Personalization 651 có thể tạo:

```text
preference
```

nhưng preference của agent không tự tạo authority.

---

# 246. Self Goal Conflict

Nếu:

```text
goal A
goal B
```

conflict:

```text
GoalConflict
```

được đưa tới 652/639.

---

# 247. Self Preservation Boundary

Một agent có thể có:

```text
runtime_health
recovery
checkpoint
```

nhưng Axiom không mặc định định nghĩa:

```text
self_preservation_drive
```

như intrinsic subjective drive.

---

# 248. Safety Dominance

Trong mọi conflict:

```text
Safety
Security
Policy
Governance
```

có precedence cao hơn:

```text
self goal
self preference
self confidence
self repair
self update
```

---

# 249. Authority Lattice

Mặc định:

```text
603 Security
   ↓
639 Policy
   ↓
647 Governance
   ↓
605 Supervision
   ↓
652 Planning
   ↓
660 Self Runtime
```

660 không được nâng mình lên trên authority layer.

---

# 250. Self Runtime as Observer

Self-runtime là:

```text
observer
modeler
evaluator
planner-support
```

không phải ultimate authority.

---

# 251. Formal Self Semantics

Ta định nghĩa:

```text
S_t = self state at time t
M_t = self model at time t
O_t = self observations
A_t = actions
R_t = observed results
```

Self update:

```text
M_(t+1) = Update(M_t, O_t, R_t, E_t)
```

với:

```text
E_t = external/trusted evidence
```

---

# 252. Metacognitive Function

```text
Meta_t =
    MetaObserve(
        S_t,
        M_t,
        O_t,
        history
    )
```

Output:

```text
strategy
confidence
uncertainty
reflection_request
```

---

# 253. Agency Function

```text
Agency(action) =
    attribution(
        request,
        plan,
        authorization,
        execution,
        observation
    )
```

---

# 254. Self Evaluation Function

```text
Eval =
    Evaluate(
        prediction,
        observation,
        criteria,
        evidence
    )
```

---

# 255. Calibration Function

```text
Calibration =
    Calibrate(
        predictions,
        outcomes
    )
```

---

# 256. Self Update Function

```text
M' =
    UpdateSelfModel(
        M,
        evidence,
        evaluation,
        policy
    )
```

---

# 257. Consciousness Boundary Formal Rule

```text
exists(SelfModel)
∧ exists(Introspection)
∧ exists(Metacognition)
∧ exists(AgencyModel)
⇏ Consciousness
```

Đây là một invariant semantic quan trọng của Axiom.

---

# 258. Self Report Formal Rule

```text
SelfReport(X)
⇏ Truth(X)
```

Self-report phải được coi là evidence.

---

# 259. Self Confidence Formal Rule

```text
Confidence(X)
⇏ Truth(X)
```

---

# 260. Simulation Formal Rule

```text
Simulate(X)
⇏ X_is_real
```

---

# 261. Persistent Identity Formal Rule

```text
PersistentSelfId
⇏ SubjectiveContinuity
```

---

# 262. Emotion Formal Rule

```text
AffectiveState
⇏ SubjectiveFeeling
```

---

# 263. Agency Formal Rule

```text
AgencyModel
⇏ MetaphysicalFreeWill
```

---

# 264. Self Repair Formal Rule

```text
RepairPlan
⇏ RepairAuthority
```

---

# 265. Self Evaluation Formal Rule

```text
SelfEvaluation
⇏ Certification
```

---

# 266. Capability Formal Rule

```text
Capability
⇏ Permission
```

---

# 267. Role Formal Rule

```text
Role
⇏ Identity
```

---

# 268. Personhood Formal Rule

```text
SelfIdentity
⇏ Personhood
```

---

# 269. Compiler Diagnostics

Compiler/runtime warnings:

```text
W660001 self-report used as authoritative fact
W660002 capability used as permission
W660003 stale self-state
W660004 unvalidated self-update
W660005 self-attribution uncertain
W660006 consciousness model treated as runtime fact
W660007 introspection crosses authority boundary
W660008 prediction treated as observation
W660009 counterfactual treated as actual
W660010 self-evaluation used as certification
```

---

# 270. Errors

Hard errors:

```text
E660001 unauthorized introspection
E660002 unauthorized self-update
E660003 unauthorized authority escalation
E660004 protected self-state access
E660005 invalid self-model revision
E660006 invalid identity transition
E660007 unsafe repair execution
E660008 policy boundary violation
```

---

# 271. Testing

Test groups:

```text
identity
role
state
capability
limitation
introspection
metacognition
prediction
evaluation
critique
calibration
agency
attribution
repair
update
security
privacy
distributed
simulation
consciousness-boundary
```

---

# 272. Identity Tests

Must verify:

```text
restart preserves configured SelfId
new instance receives new InstanceId
role change does not implicitly change SelfId
```

---

# 273. Capability Tests

Must verify:

```text
capability true
permission false
```

does not authorize action.

---

# 274. Introspection Tests

Must verify:

```text
allowed field → visible
protected field → denied
unknown field → UNKNOWN
stale field → STALE
```

---

# 275. Metacognition Tests

Must verify:

```text
low confidence → strategy reconsideration
high confidence → does not imply correctness
prediction mismatch → calibration update
```

---

# 276. Agency Tests

Must verify:

```text
requester != executor
planner != authorizer
external executor != self
unknown attribution remains unknown
```

---

# 277. Self Update Tests

Must verify:

```text
candidate
→ validation
→ commit
```

and:

```text
failed validation
→ rollback
```

---

# 278. Security Tests

Must verify:

```text
self-model cannot grant itself permission
self-update cannot disable security
self-repair cannot bypass policy
```

---

# 279. Consciousness Boundary Tests

Must verify compiler/runtime rejects semantic claims equivalent to:

```text
self.is_conscious = true
```

when used as an authoritative runtime property.

Simulation remains allowed:

```text
ConsciousnessModel.simulate()
```

---

# 280. Acceptance Criteria

BOOTSTRAP-660 được xem là hoàn thành khi:

1. self identity có semantic rõ ràng;
2. self state có snapshot;
3. self-model có revision;
4. capability/limitation model hoạt động;
5. introspection có authority boundary;
6. metacognition có explicit representation;
7. confidence/uncertainty được tách biệt;
8. self-prediction và actual outcome được tách;
9. self-evaluation có provenance;
10. self-critique không được xem là certification;
11. agency lifecycle được biểu diễn đầy đủ;
12. attribution có uncertainty;
13. self-repair có authorization;
14. self-update có validation/rollback;
15. self-model có conflict handling;
16. distributed self có scope;
17. self-memory tích hợp 650;
18. cognitive state tích hợp 657;
19. affective state tích hợp 659;
20. world model tích hợp 655;
21. planning tích hợp 652;
22. security tích hợp 603;
23. policy tích hợp 639;
24. governance tích hợp 647;
25. evaluation tích hợp 646;
26. consciousness simulation có boundary;
27. không có primitive xác nhận subjective consciousness;
28. hidden internal state không bị expose mặc định;
29. compiler metadata được định nghĩa;
30. IR được định nghĩa;
31. ABI được định nghĩa;
32. CLI được định nghĩa;
33. profile được định nghĩa;
34. error/warning model được định nghĩa;
35. distributed semantics được định nghĩa;
36. recovery semantics được định nghĩa;
37. privacy semantics được định nghĩa;
38. testing strategy được định nghĩa;
39. tối thiểu 280 semantic/design requirements được bao phủ;
40. runtime có thể triển khai theo module và zero-cost khi không sử dụng.

---

# 281. Reference Architecture

```text
                    AXIOM AI STACK

655 World Model
      │
657 Cognitive
      │
659 Affective
      │
658 Social
      │
      ▼
┌───────────────────────────────┐
│       660 SELF RUNTIME        │
│                               │
│ Identity                      │
│ Role                          │
│ Self Model                    │
│ Self State                    │
│ Capability                    │
│ Limitation                    │
│ Observation                   │
│ Introspection                 │
│ Metacognition                 │
│ Confidence                    │
│ Prediction                    │
│ Evaluation                    │
│ Critique                      │
│ Calibration                   │
│ Agency                        │
│ Attribution                   │
│ Reflection                    │
│ Repair                        │
│ Update                        │
│ Consciousness Boundary        │
└───────────────┬───────────────┘
                │
        ┌───────┼────────┐
        ▼       ▼        ▼
      652      650      646
    Planning  Memory   Evaluation
        │
        ▼
   Action / Tools
        │
   ┌────┴────┐
   ▼         ▼
 603        639
Security    Policy
```

---

# 282. Final Design Decision

Axiom không cố gắng “giải quyết consciousness” bằng cách thêm một primitive mơ hồ.

Thay vào đó, Axiom xây dựng một nền tảng computationally precise gồm:

```text
Self
SelfModel
SelfState
SelfObservation
Introspection
Metacognition
SelfEvaluation
SelfPrediction
SelfCritique
SelfCalibration
Agency
ActionAttribution
SelfReflection
SelfRepair
SelfUpdate
```

và đặt một boundary rõ ràng:

```text
COMPUTATIONAL SELF
        ≠
SUBJECTIVE CONSCIOUSNESS
```

Điều này cho phép Axiom xây dựng AI agent ngày càng có khả năng:

```text
biết trạng thái của mình
→ biết giới hạn
→ đánh giá độ tin cậy
→ quan sát kết quả
→ sửa chiến lược
→ học từ sai lệch
→ tự kiểm tra
→ tự phục hồi
→ tự cập nhật có kiểm soát
```

mà không đưa những tuyên bố triết học chưa thể kiểm chứng vào semantic core của ngôn ngữ.

---

# 283. Completion

**BOOTSTRAP-660 — COMPLETE**

Core artifacts:

```text
Self Identity
Self Model
Self State
Capability Model
Limitation Model
Introspection
Metacognition
Self Prediction
Self Evaluation
Self Critique
Self Calibration
Agency Model
Action Attribution
Self Reflection
Self Repair
Self Update
Distributed Self
Self Security Boundary
Consciousness Simulation Boundary
Compiler Metadata
IR
ABI
CLI
Profiles
Testing
```

**Invariant count:** >280 design/semantic requirements  
**Target acceptance:** PASS

**Next architecture task:** **BOOTSTRAP-661 — Native AI Collective Intelligence, Multi-Agent Cognition, Shared Mind/Swarm Coordination, Collective Memory, Distributed Self, Emergent Coordination & Multi-Agent Intelligence Runtime 5.0**
:::

BOOTSTRAP-660 đã hoàn tất. Chuỗi kiến trúc tự động chuyển sang **BOOTSTRAP-661** ở lượt tiếp theo.