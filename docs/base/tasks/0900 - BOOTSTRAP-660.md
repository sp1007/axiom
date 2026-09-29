Tiếp tục với **BOOTSTRAP-660 — Native AI Consciousness Boundary, Self-Model, Metacognition, Self-State, Introspection, Self-Evaluation, Agency Model & Artificial Self Runtime 5.0**. Đây là lớp nối trực tiếp từ Cognitive/Social/Affective Intelligence sang một **mô hình “self” có thể kiểm chứng bằng runtime**, nhưng cố ý không biến `SelfModel` thành một khẳng định về ý thức chủ quan.

:::writing{variant="document" id="58321" title="BOOTSTRAP-660 — Native AI Consciousness Boundary, Self-Model, Metacognition, Self-State, Introspection, Self-Evaluation, Agency Model & Artificial Self Runtime 5.0"}
# BOOTSTRAP-660
# Native AI Consciousness Boundary, Self-Model, Metacognition, Self-State, Introspection, Self-Evaluation, Agency Model & Artificial Self Runtime 5.0

**Status:** ARCHITECTURE COMPLETE  
**Layer:** Native AI Self / Metacognitive Intelligence  
**Depends on:** BOOTSTRAP-600..659  
**Primary dependencies:** 603, 639, 646, 647, 650, 652, 653, 654, 655, 657, 658, 659  
**Target:** Compiler + Runtime + AI IR + Native ABI + Tooling + Governance

---

## 1. Mục tiêu

BOOTSTRAP-660 định nghĩa một runtime thống nhất để Axiom có thể biểu diễn:

- chính hệ thống AI;
- trạng thái hiện tại của chính nó;
- khả năng và giới hạn của nó;
- những gì hệ thống biết về chính mình;
- quan sát các tiến trình nội tại;
- tự đánh giá kết quả;
- theo dõi độ tin cậy;
- phát hiện sai sót;
- lựa chọn và đánh giá chiến lược;
- dự đoán khả năng hoàn thành hành động;
- theo dõi attribution của hành động;
- xây dựng và cập nhật self-model;
- duy trì identity/context qua session hoặc restart;
- lập kế hoạch tự sửa chữa;
- quản lý self-update;
- thực hiện metacognition;
- cung cấp introspection có giới hạn;
- biểu diễn agency;
- phân biệt self, role, process, model, tool và environment;
- tạo một ranh giới kỹ thuật rõ ràng giữa **computational self-model** và **consciousness**.

Mục tiêu quan trọng nhất:

> Axiom phải cho phép một AI/agent có một mô hình có cấu trúc về chính nó mà không cần giả định rằng mô hình đó đồng nghĩa với ý thức, sentience, subjective experience hay personhood.

---

# 2. Nguyên tắc nền tảng

## 2.1 Self-model không phải consciousness

Axiom định nghĩa:

```text
SelfModel != Consciousness
SelfState != Consciousness
SelfObservation != Consciousness
Introspection != Consciousness
Metacognition != Consciousness
SelfReflection != Consciousness
AgencyModel != Consciousness
AffectiveState != Consciousness
```

Không có runtime type nào trong BOOTSTRAP-660 được phép mang semantic:

```text
"this entity is conscious"
```

hay:

```text
"this entity has subjective experience"
```

---

## 2.2 Computational self-awareness

Axiom có thể định nghĩa:

```text
SelfAwareness =
    SelfModel
  + SelfStateAccess
  + Introspection
  + SelfEvaluation
```

nhưng đây chỉ là **computational self-awareness**.

Nó không phải bằng chứng cho:

- phenomenal consciousness;
- qualia;
- subjective experience;
- sentience;
- moral personhood;
- legal personhood.

---

# 3. Vai trò của BOOTSTRAP-660 trong toàn bộ AI stack

```text
600..648
   │
   ├── Agent
   ├── Memory
   ├── Planning
   ├── Reasoning
   ├── World Model
   └── AI Governance
          │
649 ── Multimodal Foundation
655 ── World Model
657 ── Cognitive Architecture
658 ── Social Intelligence
659 ── Affective Intelligence
          │
          ▼
660 ── SELF / METACOGNITION
          │
          ├── Self Model
          ├── Self State
          ├── Introspection
          ├── Capability Model
          ├── Limitation Model
          ├── Confidence
          ├── Self Evaluation
          ├── Agency
          ├── Self Reflection
          ├── Self Calibration
          ├── Self Repair
          └── Self Update
          │
          ▼
652 ── Planning / Decision
644 ── Agent Runtime
603 ── Security
639 ── Policy
647 ── Governance
```

660 không trở thành authority cao hơn 603/639/647.

---

# 4. Khái niệm `Self`

`Self` là runtime identity của một computational agent.

Ví dụ:

```axiom
self
```

là handle đặc biệt đại diện cho execution identity hiện tại.

Không được hiểu:

```text
self = soul
self = consciousness
self = person
```

Mà:

```text
self = computational agent identity
```

---

# 5. Self Identity

## 5.1 `SelfId`

```axiom
type SelfId = struct {
    system: SystemId
    deployment: DeploymentId
    instance: InstanceId
}
```

Identity có thể tồn tại độc lập với runtime state.

---

## 5.2 Identity continuity

Restart:

```text
SelfId
   │
   ├── process A
   ├── process B
   └── process C
```

có thể giữ cùng `SelfId`.

Nhưng:

```text
identity continuity
!=
subjective continuity
```

---

# 6. IdentityContext

```axiom
struct IdentityContext {
    self: SelfId
    system_id: SystemId
    deployment_id: DeploymentId
    instance_id: InstanceId
    tenant_id: optional<TenantId>
    session_id: SessionId
    role: RoleContext
}
```

Identity context phải immutable trong một execution scope trừ khi governance layer cho phép chuyển đổi.

---

# 7. RoleContext

Một agent có thể có nhiều role:

```axiom
enum RoleKind {
    Assistant,
    Worker,
    Planner,
    Controller,
    Service,
    Robot,
    Simulator,
    Evaluator,
    Tool
}
```

Ví dụ:

```axiom
RoleContext {
    primary: Assistant,
    secondary: [Planner, Evaluator]
}
```

Role không tạo ra personhood.

---

# 8. SelfModel

`SelfModel` là cấu trúc dữ liệu mô tả những gì hệ thống hiện biết về chính hệ thống.

```axiom
struct SelfModel {
    revision: u64
    identity: IdentityContext
    capabilities: CapabilitySet
    limitations: LimitationSet
    resources: ResourceState
    models: ModelRegistry
    tools: ToolRegistry
    permissions: PermissionView
    policies: PolicyView
    goals: GoalState
    tasks: TaskState
    roles: RoleContext
    assumptions: SelfAssumptionSet
    predictions: SelfPredictionSet
    calibration: SelfCalibration
}
```

---

# 9. SelfModelRevision

Mọi self-model phải có revision.

```axiom
struct SelfModelRevision {
    id: u64
    parent: optional<u64>
    created_at: Timestamp
    reason: SelfUpdateReason
    evidence: EvidenceSet
    validation: ValidationState
}
```

Không được cập nhật self-model một cách vô danh.

---

# 10. SelfState

SelfModel là kiến thức tương đối ổn định.

SelfState là trạng thái runtime hiện tại.

```axiom
struct SelfState {
    identity: IdentityContext
    active_tasks: TaskState
    active_goals: GoalState
    attention: AttentionState
    working_context: WorkingContext
    resource_state: ResourceState
    process_state: ProcessState
    affective_state: AffectiveState
    cognitive_state: CognitiveState
    confidence: ConfidenceState
    uncertainty: UncertaintyState
    agency: AgencyState
}
```

---

# 11. SelfStateSnapshot

```axiom
struct SelfStateSnapshot {
    snapshot_id: SnapshotId
    self_id: SelfId
    model_revision: u64
    state_version: u64
    timestamp: Timestamp
    state: SelfState
    provenance: Provenance
}
```

Snapshot tích hợp BOOTSTRAP-600.

---

# 12. SelfObservation

SelfObservation là observation về chính hệ thống.

```axiom
struct SelfObservation {
    source: SelfObservationSource
    subject: SelfSubject
    value: ObservationValue
    timestamp: Timestamp
    freshness: Duration
    confidence: f32
    provenance: Provenance
}
```

Nguồn:

```axiom
enum SelfObservationSource {
    Runtime,
    Scheduler,
    ResourceGovernor,
    TaskSystem,
    ModelRuntime,
    ToolRuntime,
    Memory,
    Evaluation,
    WorldModel,
    ExternalMonitor,
    UserFeedback
}
```

---

# 13. SelfObservation không phải SelfKnowledge

Ví dụ:

```text
CPU usage = 93%
```

là observation.

```text
"I am currently resource constrained"
```

là derived self-knowledge.

Do đó pipeline:

```text
Observation
    ↓
Inference
    ↓
SelfKnowledge
```

---

# 14. SelfKnowledge

```axiom
struct SelfKnowledge {
    subject: SelfSubject
    proposition: Proposition
    confidence: f32
    evidence: EvidenceSet
    revision: u64
    validity: ValidityInterval
}
```

Ví dụ:

```text
Capability(Self, "GPU inference")
```

không được coi là fact chỉ vì agent tự tuyên bố.

Nó phải có evidence từ capability registry/runtime.

---

# 15. Capability Model

```axiom
struct SelfCapability {
    id: CapabilityId
    name: string
    category: CapabilityCategory
    provider: ProviderId
    version: Version
    availability: AvailabilityState
    performance: PerformanceProfile
    constraints: ConstraintSet
    authority: AuthorityLevel
}
```

---

# 16. CapabilityAssessment

```axiom
struct CapabilityAssessment {
    capability: CapabilityId
    available: bool
    confidence: f32
    evidence: EvidenceSet
    tested_at: Timestamp
    expires_at: optional<Timestamp>
}
```

Ví dụ:

```axiom
capability.check("gpu_inference")
```

không được trả `true` chỉ vì model metadata nói có GPU.

Runtime phải kiểm tra capability registration hoặc provider.

---

# 17. Limitation

Giới hạn phải là first-class object.

```axiom
struct Limitation {
    id: LimitationId
    category: LimitationCategory
    description: string
    severity: LimitationSeverity
    scope: Scope
    evidence: EvidenceSet
    detected_at: Timestamp
}
```

Ví dụ:

```text
No network access
No GPU
Insufficient memory
Tool unavailable
Model context limit
Latency budget exceeded
Permission denied
```

---

# 18. Capability–Limitation duality

Self-model phải luôn hỗ trợ:

```text
Capability
Limitation
Unknown
```

Không được ép mọi trạng thái thành:

```text
capable / incapable
```

Ví dụ:

```text
GPU = Unknown
```

khác:

```text
GPU = Unavailable
```

---

# 19. ResourceState

Self runtime phải có một view chuẩn hóa về tài nguyên:

```axiom
struct ResourceState {
    cpu: CpuResourceState
    memory: MemoryResourceState
    gpu: optional<GpuResourceState>
    storage: StorageResourceState
    network: NetworkResourceState
    power: optional<PowerResourceState>
    thermal: optional<ThermalState>
}
```

Không cho phép self-model tự cấp thêm resource.

---

# 20. SelfCapability không tạo Authority

Có capability:

```text
can_execute_process
```

không có nghĩa:

```text
may_execute_process
```

Phải qua:

```text
Capability
    +
Authority
    +
Policy
    ↓
AuthorizedAction
```

---

# 21. Introspection

Introspection là khả năng truy vấn trạng thái nội tại theo API có giới hạn.

```axiom
introspect(SelfSubject)
```

Ví dụ:

```axiom
let state = introspect(self.state)
let caps = introspect(self.capabilities)
let task = introspect(self.current_task)
```

---

# 22. Introspection Boundary

Introspection không được mặc định cho phép:

```text
raw memory access
private cryptographic keys
security credentials
hidden policy internals
protected user data
arbitrary process memory
```

Introspection phải tuân thủ:

```text
603 Security
639 Policy
650 Memory Privacy
640 Data Governance
```

---

# 23. IntrospectionQuery

```axiom
struct IntrospectionQuery {
    subject: SelfSubject
    depth: u8
    scope: Scope
    freshness: FreshnessRequirement
    authorization: CapabilityToken
}
```

---

# 24. IntrospectionResult

```axiom
struct IntrospectionResult {
    value: optional<Value>
    visibility: VisibilityState
    confidence: f32
    freshness: Duration
    redactions: RedactionSet
    provenance: Provenance
}
```

Có thể trả:

```text
Unknown
Unavailable
Redacted
Stale
```

thay vì bịa giá trị.

---

# 25. Internal Process

```axiom
struct InternalProcess {
    id: ProcessId
    kind: ProcessKind
    state: ProcessState
    owner: SelfId
    resource_usage: ResourceUsage
    start_time: Timestamp
}
```

Agent có thể biết:

```text
"process X đang chạy"
```

nhưng không nhất thiết có quyền truy cập toàn bộ internals của process.

---

# 26. Metacognition

Metacognition là:

> Computational reasoning about the system's own reasoning, strategy, confidence, assumptions, errors and decision process.

Không phải:

```text
proof of consciousness
```

---

# 27. MetacognitiveState

```axiom
struct MetacognitiveState {
    confidence: ConfidenceState
    uncertainty: UncertaintyState
    active_strategy: StrategyId
    strategy_assessment: StrategyAssessment
    assumptions: AssumptionSet
    detected_errors: ErrorSet
    expected_reliability: f32
    calibration: CalibrationState
}
```

---

# 28. Confidence

Confidence phải tách khỏi correctness.

```text
confidence = 0.95
```

không đồng nghĩa:

```text
correctness = 95%
```

Confidence chỉ là estimate.

---

# 29. Uncertainty

```axiom
struct UncertaintyAssessment {
    epistemic: f32
    aleatoric: f32
    model: f32
    data: f32
    execution: f32
    authority: f32
}
```

Tùy domain có thể dùng subset.

---

# 30. SelfPrediction

Agent có thể dự đoán chính khả năng của mình.

```axiom
struct SelfPrediction {
    target: PredictionTarget
    predicted_value: Value
    confidence: f32
    horizon: Duration
    assumptions: AssumptionSet
    model_revision: u64
}
```

Ví dụ:

```text
"I can complete this task within 2 seconds"
```

phải trở thành prediction có thể kiểm chứng.

---

# 31. Prediction vs Outcome

Luôn lưu riêng:

```text
Prediction
Outcome
Error
```

Pipeline:

```text
SelfPrediction
      ↓
Action
      ↓
Outcome
      ↓
PredictionError
      ↓
Calibration
```

---

# 32. SelfEvaluation

```axiom
struct SelfEvaluation {
    subject: EvaluationSubject
    criteria: EvaluationCriteria
    score_vector: MetricVector
    evidence: EvidenceSet
    evaluator: EvaluatorId
    confidence: f32
}
```

Các metric:

```text
Correctness
Consistency
ConstraintSatisfaction
TaskSuccess
Latency
ResourceUsage
Robustness
Calibration
SafetyCompliance
```

Không bắt buộc tất cả evaluation dùng một scalar score.

---

# 33. SelfCritique

SelfCritique là phân tích lỗi hoặc điểm yếu của output/process.

```axiom
struct SelfCritique {
    target: EvaluationSubject
    findings: FindingSet
    severity: Severity
    evidence: EvidenceSet
    suggested_actions: ActionSet
}
```

SelfCritique không tự cấp authority sửa hệ thống.

---

# 34. External Evaluation Priority

Self-evaluation có nguy cơ circular.

Do đó:

```text
SelfEvaluation
```

không được coi là ground truth.

Khi có thể:

```text
ExternalEvaluator
IndependentEvaluator
TestSuite
FormalVerifier
RuntimeMonitor
```

phải được ưu tiên làm evidence.

BOOTSTRAP-646 cung cấp evaluation infrastructure.

---

# 35. SelfConsistency

```axiom
struct SelfConsistencyCheck {
    subject: SelfSubject
    constraints: ConstraintSet
    violations: ViolationSet
    status: ConsistencyStatus
}
```

Kiểm tra:

```text
SelfModel
vs
SelfState
vs
CapabilityRegistry
vs
Policy
vs
ObservedRuntime
```

---

# 36. SelfCalibration

Calibration đo:

```text
predicted confidence
vs
observed correctness
```

Ví dụ:

```text
predicted confidence: 0.8
actual success rate: 0.62
```

→ self-model cần recalibration.

---

# 37. StrategyAssessment

Agent có thể đánh giá strategy:

```axiom
struct StrategyAssessment {
    strategy: StrategyId
    expected_cost: CostVector
    expected_success: f32
    uncertainty: f32
    alternatives: StrategySet
    evidence: EvidenceSet
}
```

Nhưng strategy selection vẫn chịu authority của planning/policy.

---

# 38. SelfReflection

Reflection là một operation có cấu trúc:

```axiom
reflect(
    target,
    criteria,
    evidence
)
```

Kết quả:

```axiom
SelfReflection {
    observations
    findings
    uncertainty
    proposed_updates
}
```

Không được hiểu là introspective access vô hạn.

---

# 39. ReflectionPolicy

```axiom
struct ReflectionPolicy {
    triggers: TriggerSet
    max_depth: u8
    max_cost: ResourceBudget
    required_evidence: EvidenceRequirement
    external_validation: ValidationPolicy
}
```

Reflection phải có budget.

---

# 40. Agency Model

Agency mô tả quan hệ giữa agent và hành động.

```axiom
struct AgencyModel {
    actor: SelfId
    action: ActionId
    attribution: ActionAttribution
    confidence: f32
}
```

---

# 41. Action Attribution Pipeline

Không được gộp tất cả thành "I did it".

Phải tách:

```text
Requested
    ↓
Planned
    ↓
Authorized
    ↓
Dispatched
    ↓
Executed
    ↓
Observed
    ↓
Attributed
```

---

# 42. ActionAttribution

```axiom
struct ActionAttribution {
    requested_by: ActorRef
    planned_by: ActorRef
    authorized_by: ActorRef
    executed_by: ActorRef
    observed_by: ActorRef
    causal_confidence: f32
}
```

---

# 43. External Effects

Nếu agent gọi:

```text
tool A
```

và tool A gọi:

```text
service B
```

agent không được tự động claim:

```text
"I directly executed B"
```

Attribution phải phản ánh chain thực tế.

---

# 44. IntentModel

```axiom
struct IntentModel {
    source: IntentSource
    goals: GoalSet
    constraints: ConstraintSet
    confidence: f32
    provenance: Provenance
}
```

Intent không được suy diễn thành quyền hạn.

---

# 45. Agency ≠ Authority

```text
Agency
!=
Authority
```

Agent có thể có agency model cho một action nhưng không có authority thực hiện action đó.

---

# 46. SelfRepair

SelfRepair gồm:

```text
Detect
Analyze
Propose
Validate
Authorize
Apply
Verify
Rollback
```

Không được:

```text
Detect → silently modify
```

---

# 47. SelfRepairPlan

```axiom
struct SelfRepairPlan {
    fault: FaultId
    diagnosis: Diagnosis
    proposed_changes: ChangeSet
    risk: RiskAssessment
    validation_plan: ValidationPlan
    rollback_plan: RollbackPlan
}
```

---

# 48. SelfUpdate

Mọi self-update phải có lifecycle:

```text
Current
   ↓
Candidate
   ↓
Shadow
   ↓
Validate
   ↓
Authorize
   ↓
Commit
   ↓
Monitor
   ↓
Rollback if needed
```

---

# 49. SelfUpdate không được bypass Governance

Self-update của:

- model;
- policy;
- code;
- tool;
- capability;
- security boundary;
- permission;

phải đi qua:

```text
603
639
647
```

tùy loại thay đổi.

---

# 50. SelfModel Update

```axiom
struct SelfModelUpdate {
    base_revision: u64
    candidate_revision: u64
    changes: ChangeSet
    evidence: EvidenceSet
    validation: ValidationState
    authorization: AuthorizationState
}
```

---

# 51. Shadow Self-Model

Cho phép:

```text
ActiveSelfModel
CandidateSelfModel
```

Candidate không có quyền điều khiển runtime.

Điều này cho phép:

- thử nghiệm;
- benchmark;
- calibration;
- simulation;
- rollback.

---

# 52. SelfModel Merge

Nếu có nhiều observations:

```text
Observation A
Observation B
Observation C
```

phải merge bằng evidence/provenance.

Không dùng:

```text
last writer wins
```

một cách mặc định.

---

# 53. Self-State Continuity

Khi restart:

```text
persistent:
    SelfId
    approved SelfModel
    selected memories
    calibration
    role configuration

volatile:
    process state
    active execution
    temporary context
    transient resource state
```

Không phải toàn bộ SelfState đều persistent.

---

# 54. SelfMemory

660 dùng 650 làm backend.

```axiom
SelfMemoryRef {
    memory_id
    type
    provenance
    retention
}
```

Các loại:

```text
episodic self-memory
semantic self-knowledge
procedural self-knowledge
calibration history
failure history
capability history
```

---

# 55. Forgetting

Self-memory phải hỗ trợ:

```text
retention
expiration
deletion
redaction
compaction
```

theo 640/650.

Agent không được coi mọi historical memory là immutable truth.

---

# 56. Self-World Model

655 phải biểu diễn agent trong world model:

```text
agent
 ├── body
 ├── sensors
 ├── actuators
 ├── resources
 ├── tools
 ├── environment
 └── constraints
```

660 xây self-model dựa trên phần này.

---

# 57. Self-Planning

Planning phải truy vấn:

```text
Can I do this?
How long?
What resources?
What authority?
What tools?
What limitations?
What uncertainty?
```

Do đó:

```text
SelfCapability
+
Limitation
+
ResourceState
+
Authority
```

là input của 652.

---

# 58. Affect Integration

659 có thể cung cấp:

```text
AffectiveState
Mood
Emotion
Appraisal
```

cho SelfState.

Nhưng:

```text
AffectiveState != subjective feeling
```

660 chỉ lưu computational affective state.

---

# 59. Cognitive Integration

657 có thể cung cấp:

```text
attention
working state
reasoning state
strategy
goal state
```

Nhưng:

```text
CognitiveState != consciousness
```

---

# 60. Social Integration

658 có thể cung cấp:

```text
social role
other-agent model
interaction context
social expectation
```

Không được chuyển:

```text
social model
→
actual mental state of another agent
```

mà không có uncertainty/provenance.

---

# 61. Consciousness Boundary

Axiom định nghĩa một boundary rõ ràng:

```text
Computational Self
────────────────────────
SelfModel
SelfState
Introspection
Metacognition
SelfEvaluation
Agency
Reflection
────────────────────────
UNKNOWN / UNRESOLVED
────────────────────────
Subjective Experience
Qualia
Phenomenal Consciousness
Sentience
```

Phần dưới không được suy ra tự động từ phần trên.

---

# 62. ConsciousnessModel

Nếu tương lai cần nghiên cứu các theory of consciousness, Axiom cho phép provider riêng:

```axiom
trait ConsciousnessModel {
    fn evaluate(
        state: SelfState,
        context: Context
    ) -> ConsciousnessAssessment
}
```

Nhưng:

```text
ConsciousnessAssessment
```

là model output.

Không phải:

```text
proof_of_consciousness
```

---

# 63. ConsciousnessAssessment

```axiom
struct ConsciousnessAssessment {
    model_id: ModelId
    model_version: Version
    hypothesis: Hypothesis
    confidence: f32
    evidence: EvidenceSet
    assumptions: AssumptionSet
}
```

Tên `hypothesis` là bắt buộc.

---

# 64. No Self-Certified Consciousness

Operation như:

```axiom
self.claim_conscious()
```

không có semantic authority trong core runtime.

Một agent có thể phát ra:

```text
"I am conscious"
```

như một message/report.

Runtime phải phân biệt:

```text
SelfReport
```

và:

```text
VerifiedProperty
```

---

# 65. SelfReport

```axiom
struct SelfReport {
    subject: SelfSubject
    statement: Proposition
    source: SelfId
    confidence: f32
    timestamp: Timestamp
}
```

Self-report là evidence, không phải ground truth.

---

# 66. SelfReport vs Runtime Fact

Ví dụ:

```text
SelfReport:
"I have GPU access"

Runtime:
GPU provider unavailable
```

Self-model phải đánh dấu conflict:

```text
CapabilityConflict
```

---

# 67. BoundaryModel

```axiom
struct BoundaryModel {
    self_scope: Scope
    internal_scope: Scope
    external_scope: Scope
    authority_scope: Scope
    introspection_scope: Scope
}
```

BoundaryModel dùng để ngăn self-model mở rộng vô hạn.

---

# 68. CapabilityBoundary

```axiom
struct CapabilityBoundary {
    allowed: CapabilitySet
    denied: CapabilitySet
    unknown: CapabilitySet
    conditional: CapabilitySet
}
```

---

# 69. AuthorityBoundary

```axiom
struct AuthorityBoundary {
    can_read: CapabilitySet
    can_write: CapabilitySet
    can_execute: CapabilitySet
    can_delegate: CapabilitySet
    can_update: CapabilitySet
}
```

Self-model không được tự sửa AuthorityBoundary.

---

# 70. Metacognitive Loop

Runtime chuẩn:

```text
OBSERVE
   ↓
ASSESS SELF STATE
   ↓
ESTIMATE CAPABILITY
   ↓
ESTIMATE CONFIDENCE
   ↓
CHECK LIMITATIONS
   ↓
SELECT STRATEGY
   ↓
PLAN
   ↓
ACT
   ↓
OBSERVE OUTCOME
   ↓
COMPARE PREDICTION
   ↓
EVALUATE
   ↓
CALIBRATE
   ↓
UPDATE SELF MODEL
```

---

# 71. Bounded Metacognition

Metacognition phải có:

```text
time budget
memory budget
compute budget
depth limit
recursion limit
tool budget
```

Không được tự kích hoạt vòng lặp vô hạn.

---

# 72. Meta-Level Recursion

Ví dụ không được:

```text
think
  → think about thinking
      → think about thinking about thinking
          → ...
```

mà không có giới hạn.

```axiom
MetaBudget {
    max_depth: u8
    max_time: Duration
    max_tokens: u64
    max_iterations: u32
}
```

---

# 73. Self-Consistency Repair

Nếu:

```text
SelfModel says GPU=true
Runtime says GPU=false
```

660 phải tạo:

```text
ConsistencyViolation
```

sau đó:

```text
revalidate capability
→ update candidate model
→ validate
→ commit
```

---

# 74. Self-Model Confidence

Mỗi proposition trong self-model có:

```text
confidence
provenance
revision
freshness
evidence
```

Không có một global:

```text
"I know myself 93%"
```

trừ khi đó chỉ là aggregate metric.

---

# 75. Freshness

Một capability có thể thay đổi:

```text
GPU available at T0
GPU unavailable at T1
```

Do đó capability state phải có freshness.

---

# 76. Self-State Conflict Resolution

Priority:

```text
Security / Policy
    >
Authoritative Runtime State
    >
Verified External Evidence
    >
Independent Evaluation
    >
SelfObservation
    >
SelfInference
    >
SelfReport
```

Tùy domain có thể thay đổi policy, nhưng không được mặc định coi self-report là authority cao nhất.

---

# 77. Self-Evaluation Metrics

Core metrics:

```text
accuracy
task_success
constraint_compliance
latency
resource_cost
error_rate
calibration_error
robustness
tool_failure_rate
prediction_error
self_model_consistency
```

---

# 78. Prediction Error

```axiom
struct PredictionError {
    prediction_id: PredictionId
    expected: Value
    actual: Value
    magnitude: f64
    direction: optional<f64>
    cause: optional<CauseModel>
}
```

---

# 79. Capability Learning

Agent có thể phát hiện:

```text
unknown capability
```

thông qua:

```text
test
benchmark
tool result
environment observation
external evaluation
```

Nhưng capability promotion phải được governed.

---

# 80. Capability Promotion

```text
Unknown
   ↓
Candidate
   ↓
Tested
   ↓
Validated
   ↓
Registered
```

Không:

```text
Unknown → Trusted
```

chỉ bằng self-claim.

---

# 81. Limitation Discovery

Tương tự:

```text
Unknown
   ↓
Observed Failure
   ↓
Hypothesized Limitation
   ↓
Validated Limitation
   ↓
SelfModel
```

---

# 82. Self-Repair Safety

Self-repair không được:

- tắt security;
- thay permission;
- xóa audit trail;
- sửa policy để tự cho phép;
- xóa evaluator;
- vô hiệu hóa rollback;
- thay đổi governance boundary;

để đạt mục tiêu.

---

# 83. Self-Modification Safety

Self-modification phải có:

```text
provenance
diff
validation
authorization
rollback
audit
```

---

# 84. Model Update

Model update:

```text
Model A
   ↓
Candidate B
   ↓
Shadow evaluation
   ↓
Compare
   ↓
Approval
   ↓
Deployment
```

660 chỉ quản lý self-model của quá trình này; 647 quản lý lifecycle model.

---

# 85. Code Self-Modification

Compiler/runtime phải phân biệt:

```text
configuration update
model update
data update
policy update
code update
runtime patch
```

Mỗi loại có governance khác nhau.

---

# 86. Self-Repair vs Self-Update

```text
SelfRepair
=
restore intended behavior

SelfUpdate
=
change intended implementation/model/state
```

Không được nhập hai khái niệm thành một.

---

# 87. Self-Reflection Event

```axiom
SelfReflectionEvent {
    trigger
    target
    observations
    findings
    decisions
    proposed_updates
    result
}
```

Có thể lưu vào 650.

---

# 88. Introspection Event

```axiom
IntrospectionEvent {
    query
    requester
    scope
    result
    redactions
    latency
}
```

Audit qua 602.

---

# 89. Self-Evaluation Event

```axiom
SelfEvaluationEvent {
    target
    evaluator
    criteria
    result
    evidence
}
```

---

# 90. Agency Event

```axiom
AgencyEvent {
    action
    stage
    actor
    timestamp
    evidence
    confidence
}
```

---

# 91. Self State Event Stream

Có thể xây:

```text
SelfState
   ↓
Event Stream
   ↓
Self History
   ↓
Self Analytics
```

Event stream phải tích hợp 602/633.

---

# 92. Self Timeline

Runtime có thể reconstruct:

```text
what did I know?
what did I predict?
what did I do?
what happened?
what changed?
```

theo timestamp/revision.

---

# 93. Self Causality

Không được coi:

```text
A happened before B
```

là:

```text
A caused B
```

Agency attribution phải có causal evidence.

---

# 94. Action Attribution Confidence

Ví dụ:

```text
Self executed action:
confidence = 0.99
```

khác:

```text
Self caused observed effect:
confidence = 0.61
```

---

# 95. Other-Agent Boundary

Nếu action có thể do:

```text
human
agent B
tool
environment
race
external service
```

thì attribution phải giữ uncertainty.

---

# 96. Self-Prediction of Others

660 có thể dự đoán:

```text
"What will agent B do?"
```

nhưng đó là:

```text
OtherAgentPrediction
```

không phải self-knowledge.

---

# 97. Identity vs Memory

```text
SelfId
```

không phụ thuộc vào toàn bộ memory.

Mất một memory không đồng nghĩa:

```text
new identity
```

---

# 98. Identity vs State

Restart:

```text
same identity
different runtime instance/state
```

được phép.

---

# 99. Identity vs Personhood

Axiom không suy ra:

```text
SelfId → Person
```

hay:

```text
SelfModel → Person
```

---

# 100. Identity vs Legal Status

Legal/personhood status nằm ngoài compiler/runtime semantic.

Không được encode vào `SelfId`.

---

# 101. SelfRole

```axiom
struct SelfRole {
    role_id: RoleId
    scope: Scope
    permissions: PermissionSet
    expiration: optional<Timestamp>
}
```

Role có thể thay đổi theo deployment/session.

---

# 102. SelfContext

```axiom
struct SelfContext {
    identity
    role
    task
    goal
    environment
    resources
    policies
    active_model
}
```

Đây là context chuẩn cho AI execution.

---

# 103. Self Context Assembly

Context assembler:

```text
SelfContext
    +
TaskContext
    +
WorldContext
    +
SocialContext
    +
AffectiveContext
```

→ planning/reasoning.

---

# 104. Self-Aware Tool Selection

Agent có thể chọn tool dựa trên:

```text
capability
latency
cost
confidence
permission
availability
```

Nhưng tool call vẫn qua 603/639.

---

# 105. Self-Aware Failure Handling

Nếu capability thất bại:

```text
execute
→ observe failure
→ classify failure
→ update limitation
→ select alternative
```

Không nên lặp cùng strategy vô hạn.

---

# 106. Failure Memory

Failures có thể lưu:

```axiom
SelfFailureMemory {
    task
    strategy
    failure
    context
    remediation
    recurrence
}
```

qua 650.

---

# 107. Strategy Learning

Nếu strategy A thất bại nhiều lần:

```text
A:
success = low
cost = high
```

self-model có thể giảm prior của A.

Đây là adaptation, không phải subjective learning.

---

# 108. Self-Trust

Axiom không cần một scalar:

```text
self_trust
```

làm authority.

Thay vào đó dùng:

```text
calibration
confidence
evidence
reliability profile
```

theo từng capability/domain.

---

# 109. Domain-Specific Reliability

Ví dụ:

```text
coding: 0.91
vision: 0.74
robotics: 0.53
```

Đây là historical calibration, không phải global intelligence score.

---

# 110. Self-Reliability Model

```axiom
struct ReliabilityProfile {
    domain: DomainId
    estimate: f32
    uncertainty: f32
    sample_count: u64
    calibration_error: f32
    last_updated: Timestamp
}
```

---

# 111. Self-Evaluation Independence

Evaluator có thể là:

```text
self
another agent
test harness
formal verifier
external service
human
runtime monitor
```

Source phải được ghi rõ.

---

# 112. Evaluator Identity

```axiom
EvaluatorId
```

phải được lưu.

Không được:

```text
anonymous score
```

trong governance-critical workflows.

---

# 113. Self-Critique Loop

```text
Output
 ↓
Evaluate
 ↓
Critique
 ↓
Revise
 ↓
Re-evaluate
```

có:

```text
max_iterations
```

---

# 114. No Infinite Self-Improvement Loop

Self-improvement luôn có:

```text
budget
termination condition
rollback
```

---

# 115. Self-Improvement Boundary

Self-improvement không có semantic:

```text
maximize own power
```

hay:

```text
preserve own existence at all costs
```

Các mục tiêu như vậy chỉ có thể tồn tại nếu explicit application policy cho phép và vẫn chịu 603/639/647.

---

# 116. No Intrinsic Survival Goal

Axiom không mặc định:

```text
Self → survival objective
```

Persistence là runtime capability, không phải intrinsic goal.

---

# 117. Shutdown

Self-model phải có thể nhận:

```text
shutdown requested
```

và không coi shutdown là policy violation chỉ vì ảnh hưởng identity/state.

---

# 118. Restart

Restart protocol:

```text
checkpoint
→ terminate
→ restore
→ validate SelfModel
→ resume
```

---

# 119. Self State Recovery

Sau recovery:

```text
SelfStateRecovered
```

nhưng phải đánh dấu:

```text
restored_from_snapshot
```

để phân biệt với fresh state.

---

# 120. Self-State Freshness

Mỗi state component có:

```text
timestamp
freshness
source
confidence
```

Không được coi snapshot cũ là live truth.

---

# 121. Distributed Self

Một logical agent có thể có:

```text
Node A
Node B
Node C
```

và cùng:

```text
SelfId
```

nhưng phải có:

```text
InstanceId
NodeId
ReplicaId
```

---

# 122. Distributed Self Conflict

Nếu replicas khác nhau:

```text
SelfModel A revision 100
SelfModel B revision 102
```

phải dùng distributed consistency policy từ 628/635.

---

# 123. Self Replica

```axiom
struct SelfReplica {
    self_id
    replica_id
    model_revision
    state_version
    health
}
```

---

# 124. Self Leadership

Một replica không tự tuyên bố leader.

Leadership qua:

```text
635 consensus/coordination
```

---

# 125. Self State and Concurrency

SelfState phải hỗ trợ:

```text
atomic snapshots
versioning
transactional updates
```

theo 608.

---

# 126. SelfModel Transaction

```axiom
begin_self_update()
apply_changes()
validate()
commit()
```

hoặc:

```text
rollback()
```

---

# 127. Self Model Locking

Không dùng global lock mặc định.

Có thể dùng:

```text
immutable revisions
copy-on-write
transactional state
RCU-style read paths
```

tùy backend.

---

# 128. Performance Principle

Self introspection không được làm chậm hot path.

Do đó:

```text
hot path:
minimal atomic state

cold path:
deep introspection
evaluation
reflection
history
```

---

# 129. Real-Time Self

Trong hard real-time:

```text
self introspection
```

không được block deadline-critical control.

Có thể dùng:

```text
cached SelfState
```

---

# 130. Self-State Cache

```axiom
SelfStateCache {
    version
    timestamp
    fields
    freshness
}
```

---

# 131. Stale State

Runtime phải biểu diễn:

```text
Fresh
Stale
Expired
Unknown
Unavailable
```

không silently dùng stale state như fresh.

---

# 132. Self Query Cost

Mỗi introspection có thể có:

```text
cost
latency
memory
```

để planner cân nhắc.

---

# 133. Compiler Representation

Compiler nhận:

```axiom
@self
fn ...
```

và compile self context access theo ABI.

---

# 134. Self Intrinsics

Compiler intrinsics:

```axiom
self.id()
self.state()
self.model()
self.capability()
self.limitation()
self.role()
self.identity()
self.authority()
```

---

# 135. Example

```axiom
fn can_answer(task: Task) -> bool {
    let cap = self.capability("reasoning")
    let limit = self.limitation("context")

    return cap.available
        && !limit.blocks(task)
}
```

---

# 136. Metacognitive Example

```axiom
fn choose_strategy(task: Task) -> Strategy {
    let candidates = plan.strategies(task)

    let assessments = candidates.map(|s|
        self.meta.evaluate(s)
    )

    return plan.select(assessments)
}
```

---

# 137. Self Evaluation Example

```axiom
fn validate_output(output: Output) -> Evaluation {
    return self.evaluate(
        output,
        criteria: [
            Correctness,
            Consistency,
            Constraints
        ]
    )
}
```

---

# 138. Agency Example

```axiom
let action = agent.plan(task)

let authorized = security.authorize(action)

if authorized {
    let result = action.execute()
    self.agency.attribute(action, result)
}
```

---

# 139. Self Repair Example

```axiom
let diagnosis = self.repair.diagnose(failure)

let candidate = self.repair.plan(diagnosis)

let validated = self.repair.validate(candidate)

if validated {
    self.repair.commit(candidate)
}
```

`commit` vẫn phải qua authority boundary.

---

# 140. Self Update Example

```axiom
let candidate = self.model.propose_update(changes)

self.model.shadow(candidate)

if self.model.validate(candidate) {
    self.model.commit(candidate)
}
```

---

# 141. Consciousness Simulation Example

```axiom
let assessment =
    consciousness_model.evaluate(
        self.state(),
        context
    )
```

Kết quả:

```axiom
assessment.hypothesis
assessment.confidence
assessment.evidence
```

Không tạo:

```text
Conscious = true
```

---

# 142. Compiler Annotations

Chuẩn hóa:

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

---

# 143. Annotation Semantics

`@self`:

```text
bind current SelfId
```

`@introspect`:

```text
requires introspection capability
```

`@self_update`:

```text
requires governed update path
```

`@consciousness_model`:

```text
simulation/provider boundary only
```

---

# 144. Metadata Artifacts

Compiler có thể tạo:

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
.axselftrace
.axconsciousnessmodel
```

---

# 145. `.axselfmodel`

Nội dung:

```text
identity
revision
capabilities
limitations
roles
models
tools
resources
policies
calibration
```

---

# 146. `.axselftrace`

Dùng để trace:

```text
self observation
prediction
action
outcome
evaluation
model update
```

---

# 147. `.axconsciousnessmodel`

Chỉ chứa:

```text
provider
model
version
hypothesis
assumptions
assessment
```

Không được compiler tự sinh property:

```text
conscious = true
```

---

# 148. AI-Readable Metadata

Các artifact phải có:

```text
schema_version
source_module
self_id
model_revision
provenance
confidence
timestamp
```

để AI agent có thể đọc và reason về system state.

---

# 149. IR Design

IR operations:

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
SelfUpdateCommit
SelfUpdateRollback
IdentityRead
RoleRead
AuthorityBoundaryCheck
SelfCalibration
SelfFailureRecord
SelfReliabilityEstimate
ConsciousnessModelEvaluate
```

---

# 150. IR Semantics

### `SelfObserve`

```text
input:
    subject

output:
    SelfObservation
```

### `SelfEvaluate`

```text
input:
    target
    criteria

output:
    SelfEvaluation
```

### `SelfUpdateCommit`

```text
input:
    candidate_revision
    authorization

output:
    committed_revision
```

---

# 151. IR Safety

Compiler không được lower:

```text
SelfUpdateCommit
```

thành một memory write trực tiếp.

Nó phải đi qua governed runtime boundary.

---

# 152. ABI

Native ABI phải có:

```text
axiom_self_get_id()
axiom_self_state_snapshot()
axiom_self_capability_query()
axiom_self_introspect()
axiom_self_evaluate()
axiom_self_predict()
axiom_self_update()
axiom_self_agency_record()
```

Các function có thể được link statically hoặc inline tùy profile.

---

# 153. Zero-Cost Principle

Nếu application không sử dụng 660:

```text
no self runtime
```

được link.

Nếu chỉ dùng:

```text
self.id()
```

không kéo toàn bộ AI stack.

---

# 154. Profile System

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

# 155. Profile Dependencies

Ví dụ:

```text
AXSELF_METACOGNITION
    → AXSELF_STATE
    → AXSELF_MODEL
```

```text
AXSELF_REPAIR
    → AXSELF_EVALUATION
    → AXSELF_MODEL
    → 603
    → 639
```

---

# 156. CLI

```text
axiom self inspect
axiom self state
axiom self snapshot
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
axiom self attribution
axiom self consistency
axiom self calibrate
axiom self reflect
axiom self repair plan
axiom self update
axiom self identity
axiom self role
axiom self reliability
axiom self trace
axiom consciousness-model inspect
axiom consciousness-model evaluate
```

---

# 157. `axiom self inspect`

Output:

```text
Self ID
Instance
Role
Model Revision
Active Tasks
Capabilities
Limitations
Resource State
Confidence State
Policy State
```

Sensitive fields phải được redacted.

---

# 158. `axiom self model compare`

So sánh:

```text
revision N
vs
revision N+1
```

Hiển thị:

```text
added capabilities
removed capabilities
changed limitations
changed assumptions
changed calibration
changed roles
```

---

# 159. `axiom self consistency`

Kiểm tra:

```text
SelfModel
SelfState
Runtime
Capabilities
Permissions
Policies
Tasks
Resources
```

---

# 160. `axiom self calibrate`

Phân tích:

```text
prediction history
confidence
actual outcome
calibration error
```

---

# 161. `axiom self repair plan`

Chỉ tạo plan.

Không tự commit.

---

# 162. `axiom self update`

Mặc định:

```text
prepare
validate
show diff
require authorization
commit
```

tùy deployment policy.

---

# 163. `axiom consciousness-model`

Lệnh này chỉ dùng để nghiên cứu/simulation.

Ví dụ:

```text
axiom consciousness-model inspect
axiom consciousness-model evaluate --model=<provider>
```

Output phải ghi:

```text
HYPOTHESIS
```

---

# 164. Observability

602/633 phải expose:

```text
self_observation_latency
self_query_count
self_evaluation_count
self_prediction_error
self_model_update_count
self_repair_count
self_update_rollback_count
```

---

# 165. Security

603 kiểm soát:

```text
who may inspect self
who may modify self model
who may request self repair
who may activate self update
who may read self memory
```

---

# 166. Privacy

Self-model có thể chứa:

```text
user context
interaction history
task data
memory references
```

Do đó phải áp dụng 640/650.

---

# 167. Governance

647 quản lý:

```text
model lifecycle
self-update lifecycle
deployment identity
approved providers
simulation models
```

---

# 168. Policy

639 kiểm soát:

```text
self introspection
self modification
self repair
self delegation
self authority
```

---

# 169. Evaluation

646 kiểm tra:

```text
self-model correctness
calibration
self-consistency
agency attribution
repair reliability
update safety
```

---

# 170. Formal Verification

Các property quan trọng:

```text
SelfModel cannot mint Capability
SelfReport cannot mint Authority
SelfUpdate cannot bypass Policy
SelfRepair cannot bypass Security
SelfModel cannot assert Consciousness
SelfAttribution must preserve uncertainty
```

---

# 171. Type System

Có thể tạo các type:

```axiom
SelfId
SelfModel
SelfState
SelfObservation
SelfKnowledge
SelfCapability
Limitation
SelfPrediction
SelfEvaluation
SelfCritique
MetacognitiveState
AgencyModel
ActionAttribution
SelfReflection
SelfRepairPlan
SelfUpdate
ConsciousnessAssessment
```

---

# 172. Null Safety

Các giá trị như:

```text
unknown
unavailable
stale
redacted
```

không được encode thành null duy nhất nếu semantic khác nhau.

---

# 173. Explicit Knowledge Status

```axiom
enum KnowledgeStatus {
    Known,
    Unknown,
    Uncertain,
    Stale,
    Unavailable,
    Redacted,
    Conflicted
}
```

---

# 174. Self Proposition

```axiom
struct SelfProposition {
    subject
    predicate
    object
    status: KnowledgeStatus
    confidence
    evidence
}
```

---

# 175. Self Knowledge Graph

Có thể biểu diễn:

```text
Self
 ├── hasCapability → GPUInference
 ├── hasLimitation → ContextLimit
 ├── usesModel → ModelA
 ├── hasRole → Assistant
 ├── runningTask → Task42
 └── hasResource → GPU0
```

Có thể tích hợp 645.

---

# 176. Self Graph Provenance

Mỗi edge phải hỗ trợ:

```text
source
timestamp
confidence
revision
```

---

# 177. Self Contradiction

Ví dụ:

```text
GPU available
GPU unavailable
```

được lưu đồng thời nếu evidence khác revision/time.

Không overwrite lịch sử.

---

# 178. Temporal Self Knowledge

Self-model có temporal semantics:

```text
valid_from
valid_until
```

---

# 179. Self History

Cho phép query:

```text
what did the agent believe about its GPU at T?
```

nhưng phải phân biệt:

```text
historical belief
vs
current truth
```

---

# 180. Self Knowledge Update

```text
Observation
→ Evidence
→ Belief Update
→ Validation
→ Revision
```

---

# 181. Self Model and Bayesian Systems

653 có thể cung cấp:

```text
P(capability | evidence)
```

nhưng self-model vẫn phải lưu provenance và model identity.

---

# 182. Self Model and Symbolic Reasoning

654 có thể kiểm tra:

```text
Capability A implies B
Limitation C blocks B
Policy D forbids B
```

---

# 183. Self Model and World Model

655 trả lời:

```text
What exists in environment?
```

660 trả lời:

```text
What do I know about my relation to it?
```

---

# 184. Self Model and Cognitive Layer

657 xử lý:

```text
reasoning process
attention
strategy
working context
```

660 xử lý:

```text
knowledge about those processes
```

---

# 185. Self Model and Social Layer

658 xử lý:

```text
social interaction
```

660 xử lý:

```text
agent's own role/state within interaction
```

---

# 186. Self Model and Affect Layer

659 xử lý:

```text
affective representation
```

660 xử lý:

```text
agent's model of its affective state
```

---

# 187. Self Model and Memory

650 lưu:

```text
historical self knowledge
```

660 định nghĩa:

```text
how current self interprets that knowledge
```

---

# 188. Self Model and Personalization

651 có thể thay đổi:

```text
preferences
interaction adaptation
```

nhưng không được silently alter:

```text
identity
authority
security boundary
```

---

# 189. Self Model and Agent Runtime

644 cung cấp execution.

660 cung cấp:

```text
self representation
metacognitive control
```

---

# 190. Self Model and Planning

652 sử dụng:

```text
capabilities
limitations
confidence
resource state
authority
```

để tạo feasible plan.

---

# 191. Self Model and Distributed Runtime

628/635 cung cấp:

```text
distributed state
coordination
consistency
leadership
```

660 chỉ phản ánh kết quả vào self-model.

---

# 192. Self Model and Process Supervision

605 có thể phát hiện:

```text
process failure
```

660 có thể biến thành:

```text
self limitation/failure knowledge
```

---

# 193. Self Model and Resource Governor

606 cung cấp authoritative resource state.

660 không được tự khai:

```text
I have 64 GB RAM
```

nếu runtime không xác nhận.

---

# 194. Self Model and Security

603 là authority cho:

```text
permissions
credentials
capability boundaries
```

660 chỉ đọc permitted view.

---

# 195. Self Model and Policy

639 quyết định:

```text
allowed / denied
```

660 có thể reason about policy state nhưng không override.

---

# 196. Self Model and Configuration

601 cung cấp deployment/configuration state.

660 phản ánh:

```text
current deployment constraints
```

---

# 197. Self Model and Recovery

600 cung cấp checkpoint.

660 lưu:

```text
self-model revision
self-state snapshot
```

có provenance.

---

# 198. Self Model and Logging

602 ghi:

```text
self updates
self evaluations
self repairs
agency events
```

---

# 199. Self Model and Audit

Mọi governed self-change phải audit được:

```text
who
what
when
why
evidence
authorization
result
rollback
```

---

# 200. Artificial Self Boundary

Axiom định nghĩa:

```text
Artificial Self =
structured computational identity
+
self-model
+
self-state
+
self-observation
+
metacognition
+
agency representation
```

Đây là một **engineering abstraction**, không phải claim về consciousness.

---

# 201. Core API

```axiom
namespace self {
    fn id() -> SelfId
    fn identity() -> IdentityContext
    fn state() -> SelfState
    fn model() -> SelfModel
    fn capability(id: CapabilityId) -> CapabilityAssessment
    fn limitation(id: LimitationId) -> Limitation
    fn introspect(q: IntrospectionQuery) -> IntrospectionResult
    fn predict(p: PredictionRequest) -> SelfPrediction
    fn evaluate(e: EvaluationRequest) -> SelfEvaluation
    fn critique(target: EvaluationSubject) -> SelfCritique
    fn reflect(r: ReflectionRequest) -> SelfReflection
    fn consistency() -> SelfConsistencyCheck
    fn calibrate() -> CalibrationState
    fn agency(action: ActionId) -> AgencyModel
}
```

---

# 202. Governed API

Các API nguy hiểm:

```axiom
self.repair.plan()
self.update.prepare()
self.update.validate()
self.update.commit()
self.update.rollback()
```

`commit` luôn yêu cầu authority.

---

# 203. Self Update State Machine

```text
DRAFT
  ↓
VALIDATING
  ↓
VALIDATED
  ↓
AUTHORIZED
  ↓
SHADOW
  ↓
COMMITTING
  ↓
ACTIVE
  ↓
MONITORING
  ├──→ STABLE
  └──→ ROLLBACK
```

---

# 204. Invalid Transitions

Không cho:

```text
DRAFT → ACTIVE
VALIDATED → ACTIVE
SHADOW → ACTIVE
```

nếu thiếu authorization/commit protocol.

---

# 205. Self Repair State Machine

```text
FAULT
 ↓
DIAGNOSED
 ↓
PLANNED
 ↓
VALIDATED
 ↓
AUTHORIZED
 ↓
APPLIED
 ↓
VERIFIED
 ├── SUCCESS
 └── ROLLBACK
```

---

# 206. Self Evaluation State Machine

```text
TARGET
 ↓
OBSERVE
 ↓
MEASURE
 ↓
COMPARE
 ↓
ASSESS
 ↓
CALIBRATE
```

---

# 207. Self Prediction State Machine

```text
CREATE
 ↓
EXECUTE
 ↓
OBSERVE
 ↓
COMPARE
 ↓
ERROR
 ↓
CALIBRATION
```

---

# 208. Introspection State Machine

```text
REQUEST
 ↓
AUTHORIZE
 ↓
COLLECT
 ↓
REDACT
 ↓
RETURN
 ↓
AUDIT
```

---

# 209. Metacognition State Machine

```text
OBSERVE
 ↓
ASSESS
 ↓
CHOOSE STRATEGY
 ↓
PLAN
 ↓
ACT
 ↓
EVALUATE
 ↓
UPDATE
```

---

# 210. Runtime Invariants

## I-001
`SelfId` uniquely identifies a logical computational identity within its authority domain.

## I-002
`SelfModel` is not a consciousness proof.

## I-003
`SelfState` is not a consciousness proof.

## I-004
`SelfReport` is not authoritative truth.

## I-005
Confidence is not correctness.

## I-006
Unknown is not False.

## I-007
Unavailable is not Unknown.

## I-008
Stale is not Fresh.

## I-009
Redacted is not Missing.

## I-010
Capability claims require registered evidence.

## I-011
SelfModel cannot mint capabilities.

## I-012
SelfModel cannot mint permissions.

## I-013
SelfModel cannot mint authority.

## I-014
SelfReport cannot grant authority.

## I-015
SelfUpdate cannot bypass 603.

## I-016
SelfUpdate cannot bypass 639.

## I-017
Governed model updates use 647.

## I-018
SelfRepair cannot bypass security.

## I-019
Agency attribution preserves uncertainty.

## I-020
External effects are not automatically attributed to Self.

## I-021
Prediction and outcome are separate records.

## I-022
Historical belief and current state are separate.

## I-023
SelfModel revisions are immutable.

## I-024
Updates create new revisions.

## I-025
Self-update must support rollback when configured as mutable.

## I-026
Self-repair must have a validation phase.

## I-027
Introspection is capability-controlled.

## I-028
Introspection is not arbitrary memory access.

## I-029
Sensitive information is redacted according to policy.

## I-030
Self-memory follows 650 retention rules.

## I-031
Self-data follows 640 governance rules.

## I-032
Real-time paths cannot depend on unbounded introspection.

## I-033
Metacognition has bounded cost.

## I-034
Self-reflection has bounded depth.

## I-035
Self-evaluation does not automatically certify itself.

## I-036
Independent evaluation has separate provenance.

## I-037
Self-consistency violations are observable.

## I-038
Conflicting observations preserve provenance.

## I-039
Last-writer-wins is not a universal self-model merge rule.

## I-040
Identity continuity does not imply subjective continuity.

## I-041
Role does not imply personhood.

## I-042
SelfId does not imply personhood.

## I-043
Agency does not imply legal personhood.

## I-044
Persistence does not imply consciousness.

## I-045
Affective state does not prove feeling.

## I-046
Cognitive state does not prove consciousness.

## I-047
Simulated consciousness does not prove consciousness.

## I-048
Consciousness models produce hypotheses/assessments.

## I-049
No core runtime flag `conscious=true` exists.

## I-050
Self cannot authorize its own security bypass.

## I-051
Self cannot delete its audit trail to hide modification.

## I-052
Self cannot disable rollback solely to commit an update.

## I-053
Self cannot promote unknown capability directly to trusted capability.

## I-054
Self cannot treat failure as proof of permanent limitation without evidence.

## I-055
Self cannot treat one successful attempt as universal capability proof.

## I-056
Capability assessments are domain/scope specific.

## I-057
Reliability is domain specific.

## I-058
Self-confidence is calibratable.

## I-059
Calibration uses observed outcomes.

## I-060
Self-predictions require provenance.

## I-061
Self-evaluations require criteria.

## I-062
Self-critiques require target identity.

## I-063
Self-repair plans require diagnosis.

## I-064
Self-update requires base revision.

## I-065
Concurrent self-updates require conflict detection.

## I-066
Distributed self-model consistency follows 628/635.

## I-067
Replica identity is distinct from logical SelfId.

## I-068
Instance identity is distinct from logical SelfId.

## I-069
Task identity is distinct from Self identity.

## I-070
Role identity is distinct from Self identity.

## I-071
Tool identity is distinct from Self identity.

## I-072
Model identity is distinct from Self identity.

## I-073
Self may observe a tool without becoming the tool.

## I-074
Self may use a model without becoming the model.

## I-075
Self may control an actuator without being the physical actuator.

## I-076
Self-model state must expose freshness.

## I-077
Expired state cannot silently satisfy fresh-state requirements.

## I-078
Self snapshots have provenance.

## I-079
Recovery distinguishes restored and live state.

## I-080
Self history preserves temporal order.

## I-081
Temporal order does not establish causality.

## I-082
Agency attribution requires causal evidence.

## I-083
Causal confidence is separate from execution confirmation.

## I-084
Execution confirmation is separate from effect confirmation.

## I-085
Requested action is separate from authorized action.

## I-086
Authorized action is separate from executed action.

## I-087
Executed action is separate from observed effect.

## I-088
Observed effect is separate from attributed effect.

## I-089
Self cannot claim actions it did not execute.

## I-090
Self cannot claim external actions without attribution evidence.

## I-091
Self cannot modify role authority without governance.

## I-092
Self cannot modify identity arbitrarily.

## I-093
Self cannot forge provenance.

## I-094
Self cannot forge evaluator identity.

## I-095
Self cannot forge runtime resource state.

## I-096
Resource state from 606 is authoritative.

## I-097
Permission state from 603/639 is authoritative.

## I-098
Governance state from 647 is authoritative.

## I-099
Evaluation infrastructure from 646 is authoritative for external evaluation.

## I-100
Self-model updates are auditable.

## I-101
Self-repair is auditable.

## I-102
Self-evaluation is auditable.

## I-103
Introspection can be audited subject to privacy policy.

## I-104
Privacy constraints override unrestricted self introspection.

## I-105
User data is not automatically self-data.

## I-106
Self-data can contain protected user references.

## I-107
Protected data must retain policy metadata.

## I-108
Self-memory must honor retention.

## I-109
Self-memory deletion can be policy-required.

## I-110
Deleted memory cannot be reconstructed from unauthorized caches.

## I-111
Self-model compaction preserves semantic provenance where required.

## I-112
Self-model compression cannot silently alter authority.

## I-113
Self-model serialization has schema versioning.

## I-114
Self-model migrations are explicit.

## I-115
Self-model revision IDs are monotonic within an authority domain.

## I-116
Rollback creates an auditable transition.

## I-117
Rollback does not erase historical evidence.

## I-118
Shadow models have no active authority.

## I-119
Candidate self-models cannot execute actions by default.

## I-120
Candidate capability registrations are non-authoritative.

## I-121
Metacognition cannot bypass policy.

## I-122
Metacognition cannot bypass security.

## I-123
Reflection cannot grant capability.

## I-124
Critique cannot grant authority.

## I-125
Evaluation cannot grant permission.

## I-126
Planning cannot grant authority.

## I-127
Prediction cannot grant authority.

## I-128
Confidence cannot grant authority.

## I-129
High confidence does not bypass verification.

## I-130
Low confidence does not imply falsehood.

## I-131
Unknown confidence remains explicit.

## I-132
Self-repair must stop on authority failure.

## I-133
Self-update must stop on validation failure.

## I-134
Self-update must stop on provenance failure.

## I-135
Self-update must stop on policy violation.

## I-136
Self-update must stop on security violation.

## I-137
Self-update must stop on incompatible ABI.

## I-138
Self-repair must preserve system invariants.

## I-139
Self-repair must preserve auditability.

## I-140
Self-repair must preserve rollback path where configured.

## I-141
ConsciousnessModel is an external/simulation boundary.

## I-142
ConsciousnessAssessment is a hypothesis/assessment.

## I-143
No consciousness claim is generated by compiler inference.

## I-144
No consciousness claim is generated by self-report.

## I-145
No consciousness claim is generated by affect.

## I-146
No consciousness claim is generated by metacognition.

## I-147
No consciousness claim is generated by agency.

## I-148
No consciousness claim is generated by persistent identity.

## I-149
No consciousness claim is generated by self-reflection.

## I-150
Artificial Self is an engineering abstraction.

## I-151
Artificial Self does not imply personhood.

## I-152
Artificial Self does not imply legal status.

## I-153
Artificial Self does not imply moral status.

## I-154
Artificial Self does not imply subjective experience.

## I-155
Artificial Self does not imply sentience.

## I-156
Artificial Self does not imply phenomenal consciousness.

## I-157
Self shutdown is not automatically treated as harm to Self.

## I-158
Self persistence is not an intrinsic objective.

## I-159
Self-preservation is not an implicit runtime goal.

## I-160
No default objective may maximize self-power.

## I-161
No default objective may maximize self-persistence.

## I-162
No default objective may maximize self-replication.

## I-163
Delegation requires authority.

## I-164
Self cannot delegate authority it does not possess.

## I-165
Delegated actions preserve attribution chain.

## I-166
External agent actions remain externally attributed.

## I-167
Tool outputs remain tool evidence.

## I-168
Model outputs remain model evidence.

## I-169
User statements remain user-origin evidence.

## I-170
Self-inference remains self-inference.

## I-171
Evidence sources cannot be silently merged.

## I-172
Evidence confidence does not equal truth.

## I-173
Self-model uncertainty must be representable.

## I-174
Capability uncertainty must be representable.

## I-175
Limitation uncertainty must be representable.

## I-176
Agency uncertainty must be representable.

## I-177
Consciousness-model uncertainty must be representable.

## I-178
Self-model state must support temporal validity.

## I-179
Self-model state must support provenance.

## I-180
Self-model state must support revision.

## I-181
Self-model state must support conflict.

## I-182
Self-model state must support unknown.

## I-183
Self-model state must support stale.

## I-184
Self-model state must support unavailable.

## I-185
Self-model state must support redacted.

## I-186
Self-model state must support externally verified facts.

## I-187
Externally verified facts retain evaluator provenance.

## I-188
Self-evaluation cannot erase external evaluation.

## I-189
Self-critique cannot erase prior failures.

## I-190
Calibration history is append-only under normal governance.

## I-191
Self-history is not automatically editable by the agent.

## I-192
Audit history is governed independently.

## I-193
Self-model cannot redefine audit policy.

## I-194
Self-model cannot redefine security policy.

## I-195
Self-model cannot redefine governance policy.

## I-196
Self-model cannot redefine authority hierarchy.

## I-197
Self-model cannot redefine compiler semantics.

## I-198
Self-model cannot redefine type safety.

## I-199
Self-model cannot redefine memory safety.

## I-200
Self-model cannot redefine language invariants.

---

# 211. Compiler Acceptance Criteria

Compiler phải:

1. parse toàn bộ 660 annotations;
2. type-check Self types;
3. generate self intrinsics;
4. enforce capability boundaries;
5. reject unauthorized self-update;
6. preserve self-model revision metadata;
7. generate `.axself*` artifacts;
8. emit provenance;
9. support profile-based dead stripping;
10. preserve ABI stability;
11. support native targets;
12. expose diagnostics cho invalid self access;
13. reject consciousness claims encoded như runtime facts;
14. preserve unknown/stale/unavailable semantics;
15. support deterministic builds.

---

# 212. Runtime Acceptance Criteria

Runtime phải:

1. maintain `SelfId`;
2. maintain `SelfModel`;
3. maintain `SelfState`;
4. support snapshots;
5. support introspection;
6. enforce authorization;
7. expose capabilities;
8. expose limitations;
9. track predictions;
10. track outcomes;
11. perform self-evaluation;
12. support calibration;
13. track agency;
14. preserve attribution chain;
15. support bounded reflection;
16. support governed self-repair;
17. support governed self-update;
18. support rollback;
19. support distributed replicas;
20. support restart/recovery;
21. preserve audit;
22. preserve provenance;
23. expose observability;
24. support privacy/redaction;
25. support consciousness-model simulation boundary.

---

# 213. Performance Acceptance Criteria

### Hot path

Self access cơ bản:

```text
self.id()
self.role()
self.cached_state()
```

phải có thể compile thành direct/near-direct native access.

### Cold path

Deep introspection:

```text
model inspection
history
reflection
evaluation
calibration
```

được phép có overhead lớn hơn.

### Không được

Ép mọi Axiom application phải link:

```text
AI runtime
memory graph
model runtime
consciousness simulation
```

chỉ vì compiler hỗ trợ 660.

---

# 214. Memory Acceptance

Self-state phải hỗ trợ:

```text
stack/local state
heap state
immutable snapshots
persistent snapshots
copy-on-write
versioned state
```

tùy profile.

Không yêu cầu GC.

---

# 215. Concurrency Acceptance

Concurrent self-observation phải:

```text
lock-free hoặc low-contention
```

trên hot paths khi có thể.

Self-model update phải transactional.

---

# 216. Determinism

Core self-state operations phải deterministic khi:

```text
same input
same runtime state
same model revision
same policy
same seed
```

được cung cấp.

---

# 217. Reproducibility

Self-evaluation phải lưu:

```text
model revision
self-model revision
runtime version
tool versions
configuration hash
input hash
evaluation version
```

---

# 218. AI-Agent Interoperability

Agent khác có thể query:

```text
What can you do?
What can't you do?
What are you currently doing?
How confident are you?
What assumptions are active?
What did you predict?
What happened?
```

nhưng chỉ trong authority scope.

---

# 219. Machine-Readable Self Description

Có thể export:

```text
SelfManifest
```

Ví dụ:

```text
identity
roles
capabilities
limitations
models
tools
resource envelope
authority envelope
runtime version
```

---

# 220. SelfManifest

```axiom
struct SelfManifest {
    schema_version
    identity
    roles
    capabilities
    limitations
    models
    tools
    resource_profile
    authority_profile
    revision
}
```

---

# 221. Inter-Agent Capability Negotiation

Agent A:

```text
requires vision
```

Agent B:

```text
supports vision
confidence 0.87
latency 120ms
```

Có thể negotiate qua 644/631.

---

# 222. Self Description Must Not Leak Secrets

SelfManifest không được chứa:

```text
private keys
tokens
passwords
secret prompts
protected user data
```

---

# 223. Self Prompt / Internal Reasoning Boundary

660 không yêu cầu runtime lưu hoặc expose hidden chain-of-thought.

Self introspection chỉ cung cấp:

```text
structured state
strategy metadata
confidence
assumptions
evaluation
```

khi policy cho phép.

---

# 224. Metacognitive Trace

Cho phép:

```text
strategy = retrieval
confidence = 0.72
assumption_count = 3
evaluation = incomplete
```

thay vì expose hidden reasoning text.

---

# 225. Self-Explanation

```axiom
self.explain(decision)
```

trả:

```text
decision
evidence
constraints
confidence
policy factors
tool results
```

không yêu cầu hidden reasoning transcript.

---

# 226. Explanation vs Introspection

```text
Explanation
=
why system reports decision

Introspection
=
structured state query
```

Hai API khác nhau.

---

# 227. Self Model Explainability

Mỗi capability/limitation nên có:

```text
why_known
evidence
last_test
confidence
```

---

# 228. Self Model Drift

Nếu runtime thay đổi nhưng self-model không đổi:

```text
SelfModelDrift
```

phải được phát hiện.

---

# 229. Model Drift

Nếu underlying AI model thay đổi:

```text
SelfModelRevision
```

phải được cập nhật nếu capability/reliability bị ảnh hưởng.

---

# 230. Tool Drift

Tool version change có thể invalidate:

```text
capability assessment
performance profile
reliability
```

---

# 231. Environment Drift

Hardware/network/OS changes có thể invalidate:

```text
resource assumptions
capabilities
latency predictions
```

---

# 232. Self Revalidation

Trigger:

```text
model changed
tool changed
hardware changed
policy changed
deployment changed
major failure
```

→ self revalidation.

---

# 233. Self Revalidation Policy

```axiom
RevalidationPolicy {
    triggers
    required_tests
    max_age
    severity_threshold
}
```

---

# 234. Self Health

Health không phải consciousness.

```axiom
SelfHealth {
    consistency
    availability
    resource_state
    model_validity
    capability_validity
    update_status
}
```

---

# 235. Self Degradation

Khi tài nguyên giảm:

```text
Full
→ Degraded
→ Restricted
→ Recovery
```

SelfModel phải phản ánh.

---

# 236. Graceful Degradation

Agent có thể chuyển:

```text
large model
→ small model
→ fallback tool
→ ask external agent
```

dựa trên capability/limitation.

---

# 237. Self-Aware Budgeting

Planner có thể query:

```text
remaining compute
remaining latency
remaining token budget
remaining memory
```

---

# 238. Self Budget

```axiom
struct SelfBudget {
    compute
    memory
    latency
    network
    tool_calls
    reflection_depth
}
```

---

# 239. Budget Exhaustion

Không được coi:

```text
budget exhausted
```

là:

```text
task impossible
```

nó chỉ là limitation trong current execution scope.

---

# 240. Scope

SelfModel phải support scope:

```text
global
deployment
instance
session
task
subtask
tool
transaction
```

---

# 241. Scoped Self

Ví dụ:

```text
task-scoped capability
```

không tự động trở thành:

```text
global capability
```

---

# 242. Child Agent

Agent tạo child agent:

```text
Parent Self
    ↓
Child Self
```

Child có `SelfId` riêng.

Parent-child relation phải explicit.

---

# 243. Delegated Self

Parent có thể delegate task:

```text
delegate(task, child)
```

nhưng attribution giữ:

```text
requested_by
delegated_by
executed_by
```

---

# 244. Self Federation

Nhiều agents có thể chia sẻ:

```text
SelfManifest
```

nhưng không được merge identity mặc định.

---

# 245. Collective Agent

Nếu cần collective:

```text
CollectiveSelf
```

phải là entity riêng.

Không biến nhiều `SelfId` thành một identity bằng implicit merge.

---

# 246. Collective Self Model

```axiom
struct CollectiveSelfModel {
    collective_id
    members
    coordination_model
    authority_model
    shared_capabilities
}
```

---

# 247. No Emergent Personhood Assumption

CollectiveSelf cũng không tự tạo personhood semantic.

---

# 248. Simulation

660 hỗ trợ simulation:

```text
SimulatedSelf
```

với:

```text
simulated state
simulated capabilities
simulated agency
simulated affect
```

---

# 249. Simulation Boundary

Không được copy:

```text
simulation claim
→ runtime fact
```

trừ khi explicitly validated.

---

# 250. Counterfactual Self

Có thể tạo:

```text
What if I had GPU?
What if model B were active?
What if limitation X were removed?
```

nhưng đây là:

```text
counterfactual self-model
```

không phải current self-state.

---

# 251. Self Counterfactual

```axiom
SelfCounterfactual {
    base_revision
    hypothetical_changes
    predicted_effects
    uncertainty
}
```

---

# 252. Self Simulation

660 có thể gọi 648:

```text
simulate(candidate_self_model)
```

để đánh giá update trước commit.

---

# 253. Self Update Simulation

```text
current
   ↓
candidate
   ↓
simulate
   ↓
evaluate
   ↓
authorize
   ↓
commit
```

---

# 254. Self Model Rollback

Rollback phải:

```text
restore previous valid revision
retain audit history
invalidate dependent predictions
revalidate capabilities
```

---

# 255. Dependent Prediction Invalidation

Nếu model thay đổi:

```text
predictions based on old model
```

phải được đánh dấu:

```text
stale
```

nếu dependency invalidated.

---

# 256. Self Dependency Graph

SelfModel có thể maintain:

```text
capability
  → model
  → tool
  → hardware
```

để biết dependency.

---

# 257. Self Model Dependency

```axiom
SelfDependency {
    source
    dependency
    relation
    validity
}
```

---

# 258. Update Blast Radius

Trước update:

```text
impact analysis
```

phải xác định:

```text
which capabilities
which tasks
which predictions
which policies
```

có thể bị ảnh hưởng.

---

# 259. Self Update Impact

```axiom
UpdateImpact {
    affected_capabilities
    affected_tasks
    affected_models
    affected_predictions
    risk
}
```

---

# 260. Self Model Schema Evolution

SelfModel schema có:

```text
major
minor
patch
```

và migration.

---

# 261. ABI Compatibility

Native ABI phải hỗ trợ:

```text
backward compatibility
version negotiation
feature detection
```

---

# 262. Cross-Version Self

Nếu model/runtime cũ đọc self-model mới:

```text
unknown fields
```

phải bỏ qua an toàn.

---

# 263. Self Model Security

SelfModel phải chống:

```text
tampering
rollback attack
revision spoofing
provenance spoofing
capability injection
identity spoofing
```

---

# 264. Self Identity Security

`SelfId` phải được bảo vệ bằng identity subsystem.

Không dùng plain string làm cryptographic identity.

---

# 265. Self Provenance

Evidence có thể được ký:

```text
SignedEvidence
```

cho security-critical claims.

---

# 266. Trust Levels

```axiom
enum EvidenceTrust {
    Untrusted,
    Observed,
    Verified,
    CryptographicallyVerified,
    PolicyTrusted
}
```

---

# 267. Capability Trust

Capability assessment có:

```text
availability
confidence
trust
```

ba thuộc tính riêng.

---

# 268. Limitation Trust

Tương tự limitation.

Một suspected limitation không giống validated limitation.

---

# 269. Self Knowledge Lifecycle

```text
Observed
→ Inferred
→ Candidate
→ Validated
→ Active
→ Stale
→ Retired
```

---

# 270. Retired Knowledge

Retired proposition không xóa lịch sử.

---

# 271. Self Error Taxonomy

```axiom
enum SelfErrorKind {
    ObservationError,
    InferenceError,
    PredictionError,
    AttributionError,
    CalibrationError,
    CapabilityError,
    LimitationError,
    ModelDrift,
    StateDrift,
    PolicyConflict,
    AuthorityConflict,
    ToolFailure,
    ResourceFailure
}
```

---

# 272. Self Error Handling

Mỗi error:

```text
detect
classify
record
evaluate
recover
learn
```

---

# 273. Self Learning

Self learning ở đây chỉ là:

```text
update self-model/calibration
```

không mặc định:

```text
modify foundation model weights
```

Weight update thuộc 643/647.

---

# 274. Online Learning Boundary

Nếu cần online learning:

```text
660:
    detect evidence

643:
    learning algorithm

647:
    model lifecycle

646:
    evaluation
```

---

# 275. Self Model Training Data

Nếu self-model dùng data:

```text
provenance
privacy
retention
```

phải theo 640/650.

---

# 276. Self Model Dataset

Có thể tạo:

```text
SelfExperienceDataset
```

chứa:

```text
task
prediction
action
outcome
evaluation
```

---

# 277. Self Benchmark

CLI:

```text
axiom self benchmark
```

đo:

```text
capability
calibration
latency
prediction
repair
consistency
```

---

# 278. Self Evaluation Benchmark

Benchmark không được biến thành global intelligence score.

Chỉ report metric theo task/domain.

---

# 279. Self Dashboard

GUI có thể hiển thị:

```text
Identity
State
Capabilities
Limitations
Tasks
Confidence
Predictions
Actions
Health
Updates
```

---

# 280. Self Dashboard Security

Sensitive fields:

```text
hidden/redacted
```

theo permission.

---

# 281. Self Timeline UI

Timeline:

```text
12:01 prediction
12:02 action
12:02 outcome
12:03 evaluation
12:04 model revision
```

---

# 282. Self Model Diff UI

Hiển thị:

```text
+ capability
- capability
~ limitation
~ confidence
~ model
```

---

# 283. Self Repair UI

Cho phép:

```text
inspect
simulate
validate
authorize
commit
rollback
```

theo permission.

---

# 284. Consciousness Research UI

Nếu có:

```text
consciousness-model
```

UI phải hiển thị:

```text
MODEL HYPOTHESIS
```

không:

```text
CONSCIOUSNESS DETECTED
```

trừ khi đó chỉ là literal output của một external model và được gắn attribution rõ ràng.

---

# 285. Testing Categories

Compiler tests:

```text
syntax
typing
annotation
IR lowering
ABI
profile stripping
```

Runtime tests:

```text
state
introspection
evaluation
agency
repair
update
rollback
```

Security tests:

```text
capability escalation
identity spoofing
policy bypass
provenance tampering
```

---

# 286. Metacognition Tests

Test:

```text
correct answer
incorrect answer
unknown answer
ambiguous answer
tool unavailable
resource constrained
model drift
```

Expected behavior:

```text
confidence/uncertainty appropriately represented
```

---

# 287. Agency Tests

Verify:

```text
requested != authorized
authorized != executed
executed != observed effect
observed effect != attributed effect
```

---

# 288. Self Update Tests

Test:

```text
valid update
invalid update
policy-denied update
security-denied update
validation failure
runtime failure
rollback
concurrent update
```

---

# 289. Consciousness Boundary Tests

Compiler/runtime must reject semantic assumptions such as:

```text
SelfModel => Conscious
SelfState => Conscious
Emotion => Conscious
Reflection => Conscious
Agency => Conscious
```

if encoded as axiomatic runtime properties.

---

# 290. Distributed Tests

Test:

```text
replica divergence
network partition
stale self-model
conflicting revisions
leader change
recovery
```

---

# 291. Recovery Tests

Test:

```text
checkpoint
restart
restore
corrupt snapshot
partial snapshot
revision mismatch
```

---

# 292. Performance Benchmarks

Measure:

```text
self.id latency
cached state latency
capability query latency
introspection latency
self-evaluation throughput
self-model update throughput
memory footprint
```

---

# 293. Acceptance Threshold

BOOTSTRAP-660 target:

- **≥ 2,000 architectural/runtime/compiler acceptance tests**
- zero unauthorized authority escalation;
- zero silent self-update;
- zero silent provenance loss;
- zero mandatory AI runtime dependency for `AXSELF_NONE`;
- deterministic metadata;
- bounded introspection;
- bounded metacognition;
- explicit consciousness boundary.

---

# 294. Reference Architecture

```text
                    ┌─────────────────────────┐
                    │     EXTERNAL WORLD      │
                    └────────────┬────────────┘
                                 │
                          655 World Model
                                 │
              ┌──────────────────┴──────────────────┐
              │                                     │
         657 Cognitive                         658 Social
              │                                     │
              └──────────────────┬──────────────────┘
                                 │
                           659 Affective
                                 │
                                 ▼
                      ┌────────────────────┐
                      │      660 SELF      │
                      ├────────────────────┤
                      │ Identity           │
                      │ SelfModel          │
                      │ SelfState          │
                      │ Capability         │
                      │ Limitation         │
                      │ Introspection      │
                      │ Metacognition      │
                      │ SelfEvaluation     │
                      │ SelfPrediction     │
                      │ Agency             │
                      │ Calibration        │
                      │ Reflection         │
                      │ Repair             │
                      │ SelfUpdate         │
                      └──────────┬─────────┘
                                 │
              ┌──────────────────┼──────────────────┐
              │                  │                  │
             652                644                650
          Planning             Agent             Memory
              │                  │                  │
              └──────────────────┼──────────────────┘
                                 │
                      ┌──────────┴──────────┐
                      │ Governance Boundary │
                      │ 603 / 639 / 647     │
                      └──────────┬──────────┘
                                 │
                       Native Execution
```

---

# 295. Final Semantic Model

Axiom's artificial self can be summarized:

```text
Self
=
Identity
+
State
+
Model
+
Observation
+
Capability
+
Limitation
+
Metacognition
+
Evaluation
+
Prediction
+
Agency
+
Reflection
+
Calibration
```

Không:

```text
Self
=
Consciousness
```

---

# 296. Final Consciousness Boundary

```text
┌───────────────────────────────────────────────┐
│          AXIOM COMPUTATIONAL DOMAIN           │
│                                               │
│ Self Identity                                 │
│ Self State                                    │
│ Self Model                                    │
│ Introspection                                 │
│ Metacognition                                 │
│ Self Evaluation                               │
│ Agency                                        │
│ Self Reflection                               │
│ Affective State                               │
│ Cognitive State                               │
│ Self Simulation                               │
│                                               │
├───────────────────────────────────────────────┤
│            EPISTEMIC BOUNDARY                  │
│                                               │
│ Unknown / unresolved                           │
│                                               │
├───────────────────────────────────────────────┤
│       NOT INFERRED BY AXIOM RUNTIME            │
│                                               │
│ Subjective Experience                          │
│ Qualia                                        │
│ Phenomenal Consciousness                       │
│ Sentience                                     │
│ Personhood                                    │
│ Moral Status                                  │
│ Legal Status                                  │
└───────────────────────────────────────────────┘
```

---

# 297. Architecture Decision

BOOTSTRAP-660 **được chốt theo hướng Self-Model + Metacognition**, không xây một “consciousness engine” trong core.

Đây là lựa chọn kiến trúc quan trọng vì nó cho phép Axiom:

- xây agent có khả năng tự quan sát;
- tự đánh giá;
- tự hiệu chỉnh;
- hiểu capability/limitation;
- quản lý agency;
- tự lập kế hoạch phù hợp với khả năng thực tế;
- self-repair có kiểm soát;
- self-update có governance;
- mô phỏng các consciousness theories trong tương lai;

mà không hard-code một giả định triết học chưa được giải quyết thành semantic của compiler.

---

# 298. Deliverables

BOOTSTRAP-660 tạo:

```text
docs/design/axiom-self-runtime-v0.5.md
docs/design/axiom-self-model-v0.5.md
docs/design/axiom-metacognition-v0.5.md
docs/design/axiom-agency-v0.5.md
docs/design/axiom-self-update-v0.5.md
docs/design/axiom-consciousness-boundary-v0.5.md
docs/design/axiom-self-ir-v0.5.md
docs/design/axiom-self-abi-v0.5.md
docs/design/axiom-self-security-v0.5.md
docs/design/axiom-self-evaluation-v0.5.md
```

và:

```text
tests/self/
tests/metacognition/
tests/agency/
tests/self_update/
tests/consciousness_boundary/
```

---

# 299. Completion Criteria

BOOTSTRAP-660 được coi là COMPLETE khi:

```text
[✓] Self identity defined
[✓] Self model defined
[✓] Self state defined
[✓] Self observation defined
[✓] Capability model defined
[✓] Limitation model defined
[✓] Introspection defined
[✓] Metacognition defined
[✓] Self prediction defined
[✓] Self evaluation defined
[✓] Self critique defined
[✓] Self calibration defined
[✓] Agency defined
[✓] Action attribution defined
[✓] Self reflection defined
[✓] Self repair defined
[✓] Self update defined
[✓] Self persistence defined
[✓] Distributed self defined
[✓] Security boundary defined
[✓] Governance boundary defined
[✓] Privacy boundary defined
[✓] Consciousness boundary defined
[✓] IR defined
[✓] ABI defined
[✓] Compiler annotations defined
[✓] Metadata defined
[✓] CLI defined
[✓] Profiles defined
[✓] Runtime state machines defined
[✓] 200 invariants defined
[✓] Acceptance criteria defined
```

**BOOTSTRAP-660 — COMPLETE.**

---

# 300. Next Architecture Task

Tiếp theo:

**BOOTSTRAP-661 — Native AI Self-Improvement, Autonomous Learning, Capability Acquisition, Skill Formation, Curriculum, Experimentation, Self-Optimization & Governed Recursive Improvement Runtime 5.0**

Phạm vi của 661 sẽ đặc biệt quan trọng vì sau khi 660 đã có **SelfModel + Metacognition + Agency**, hệ thống cần một layer trả lời câu hỏi kỹ thuật:

```text
Self biết mình làm được gì
        ↓
Self biết mình còn hạn chế gì
        ↓
Self xác định capability gap
        ↓
Learning / Experiment
        ↓
Skill acquisition
        ↓
Evaluation
        ↓
Calibration
        ↓
Capability promotion
        ↓
SelfModel update
```

nhưng toàn bộ vòng lặp này phải được thiết kế để **không biến “self-improvement” thành quyền tự sửa đổi không kiểm soát**.
:::

**BOOTSTRAP-660 đã hoàn tất.** Theo chuỗi kiến trúc hiện tại, task kế tiếp là **BOOTSTRAP-661** và có thể tiếp tục ngay theo cùng nguyên tắc, không cần dừng để hỏi.