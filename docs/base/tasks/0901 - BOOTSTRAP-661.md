Tiếp tục với **BOOTSTRAP-661 — Native AI Self-Improvement, Autonomous Learning, Capability Acquisition, Skill Formation, Curriculum, Experimentation, Self-Optimization & Governed Recursive Improvement Runtime 5.0**.

:::writing{variant="document" id="74163" title="BOOTSTRAP-661 — Native AI Self-Improvement, Autonomous Learning, Capability Acquisition, Skill Formation, Curriculum, Experimentation, Self-Optimization & Governed Recursive Improvement Runtime 5.0"}
# BOOTSTRAP-661
# Native AI Self-Improvement, Autonomous Learning, Capability Acquisition, Skill Formation, Curriculum, Experimentation, Self-Optimization & Governed Recursive Improvement Runtime 5.0

**Status:** ARCHITECTURE COMPLETE  
**Layer:** Native AI Learning / Self-Improvement  
**Depends on:** BOOTSTRAP-600..660  
**Primary dependencies:** 643, 646, 647, 648, 650, 652, 653, 654, 655, 657, 659, 660  
**Security authorities:** 603, 639  
**Goal:** governed capability acquisition and measurable improvement without unrestricted self-modification

---

# 1. Mục tiêu

BOOTSTRAP-661 định nghĩa runtime cho quá trình:

```text
Capability Gap
      ↓
Learning Objective
      ↓
Curriculum
      ↓
Experiment
      ↓
Practice
      ↓
Skill Formation
      ↓
Evaluation
      ↓
Calibration
      ↓
Capability Promotion
      ↓
SelfModel Update
```

661 phải cho phép Axiom AI:

- phát hiện capability gap;
- xác định skill cần học;
- tạo learning objective;
- xây curriculum;
- chọn dữ liệu/trải nghiệm;
- tạo experiment;
- thực hành;
- đánh giá;
- phát hiện regression;
- hình thành skill;
- tối ưu strategy;
- cải thiện reliability;
- cập nhật self-model;
- học online/offline;
- học từ simulation;
- transfer skill giữa domain;
- thực hiện recursive improvement có giới hạn;
- quản lý version của skill/model;
- rollback khi improvement gây regression.

Nhưng:

> **Self-improvement không đồng nghĩa với unrestricted self-modification.**

---

# 2. Phân biệt ba loại improvement

Axiom phải tách:

```text
Learning
Skill Acquisition
Self-Modification
```

## Learning

Thay đổi knowledge/parameters/state theo learning mechanism.

## Skill Acquisition

Tạo khả năng thực hiện một task/domain tốt hơn.

## Self-Modification

Thay đổi code, architecture, policy, authority, runtime hoặc chính cơ chế learning.

Ba loại này có governance khác nhau.

---

# 3. Improvement Taxonomy

```text
Level 0 — No adaptation
Level 1 — Context adaptation
Level 2 — Memory learning
Level 3 — Skill learning
Level 4 — Strategy optimization
Level 5 — Model adaptation
Level 6 — Tool/capability acquisition
Level 7 — Architecture optimization
Level 8 — Governed recursive improvement
```

Không có level nào tự động có quyền vượt 603/639/647.

---

# 4. Core Principle

661 phải tối ưu:

```text
Capability
Reliability
Efficiency
Calibration
Robustness
Generalization
```

thay vì chỉ:

```text
raw benchmark score
```

---

# 5. Self-Improvement Objective

```axiom
struct ImprovementObjective {
    id: ObjectiveId
    target_capability: CapabilityId
    baseline: EvaluationBaseline
    target: ImprovementTarget
    constraints: ConstraintSet
    budget: ImprovementBudget
    deadline: optional<Duration>
    risk_limit: RiskLimit
}
```

---

# 6. ImprovementTarget

```axiom
struct ImprovementTarget {
    success_rate: optional<f32>
    latency: optional<Duration>
    memory: optional<Bytes>
    energy: optional<f32>
    robustness: optional<f32>
    calibration_error: optional<f32>
    quality: optional<f32>
}
```

Không bắt buộc dùng một scalar objective.

---

# 7. Capability Gap

```axiom
struct CapabilityGap {
    capability: CapabilityId
    current_level: CapabilityLevel
    required_level: CapabilityLevel
    evidence: EvidenceSet
    confidence: f32
    severity: Severity
}
```

---

# 8. Gap Detection

Gap có thể phát hiện từ:

```text
task failure
evaluation
user requirement
planner requirement
simulation
benchmark
runtime limitation
self-prediction error
external evaluation
```

---

# 9. Capability Gap ≠ Failure

Một failure đơn lẻ không đủ kết luận:

```text
"I cannot do X."
```

661 phải phân biệt:

```text
temporary failure
resource limitation
knowledge gap
skill gap
tool gap
model limitation
policy restriction
environment limitation
```

---

# 10. Improvement Hypothesis

```axiom
struct ImprovementHypothesis {
    gap: CapabilityGap
    cause: CauseModel
    intervention: Intervention
    expected_gain: f32
    uncertainty: f32
    evidence: EvidenceSet
}
```

---

# 11. Improvement Loop

Chuẩn:

```text
OBSERVE
   ↓
BASELINE
   ↓
IDENTIFY GAP
   ↓
FORM HYPOTHESIS
   ↓
DESIGN INTERVENTION
   ↓
EXPERIMENT
   ↓
TRAIN/PRACTICE
   ↓
EVALUATE
   ↓
COMPARE
   ↓
PROMOTE / REJECT
   ↓
CALIBRATE
   ↓
UPDATE SELF-MODEL
```

---

# 12. Baseline

Không được tuyên bố improvement nếu không có baseline.

```axiom
struct EvaluationBaseline {
    benchmark: BenchmarkId
    version: Version
    dataset: DatasetId
    metrics: MetricVector
    environment: EnvironmentFingerprint
    model_revision: ModelRevision
}
```

---

# 13. Improvement Claim

Một improvement claim phải chứa:

```text
baseline
candidate
same evaluation protocol
metrics
uncertainty
environment
model version
```

---

# 14. Regression

Improvement có thể tăng metric A nhưng giảm B.

Do đó:

```axiom
struct RegressionReport {
    improved_metrics: MetricSet
    degraded_metrics: MetricSet
    unchanged_metrics: MetricSet
    severity: Severity
}
```

Không được gọi candidate là “better” chỉ dựa trên một metric.

---

# 15. Skill

Skill là capability có cấu trúc để hoàn thành một class task.

```axiom
struct Skill {
    id: SkillId
    name: string
    domain: DomainId
    prerequisites: SkillSet
    procedures: ProcedureSet
    knowledge: KnowledgeSet
    models: ModelSet
    tools: ToolSet
    reliability: ReliabilityProfile
    version: Version
}
```

---

# 16. Skill không phải Capability

```text
Capability
=
can potentially perform class of operations

Skill
=
structured learned competence for task/domain
```

Một capability có thể chứa nhiều skill.

---

# 17. Skill Level

```axiom
enum SkillLevel {
    Unknown,
    Novice,
    Practiced,
    Competent,
    Reliable,
    Expert
}
```

Các label chỉ có meaning khi được định nghĩa bằng measurable criteria.

---

# 18. SkillLevel không phải Intelligence Score

Skill level là domain/task-specific.

Không tạo:

```text
global intelligence = 0.93
```

làm core semantic.

---

# 19. SkillEvidence

```axiom
struct SkillEvidence {
    evaluations: EvaluationSet
    successful_tasks: u64
    failed_tasks: u64
    robustness_tests: u64
    calibration: CalibrationState
    provenance: Provenance
}
```

---

# 20. Skill Reliability

```axiom
struct SkillReliability {
    domain: DomainId
    task_distribution: Distribution
    success_estimate: f32
    uncertainty: f32
    calibration_error: f32
    sample_count: u64
}
```

---

# 21. Skill Acquisition

Pipeline:

```text
Unknown
   ↓
Candidate
   ↓
Learning
   ↓
Practiced
   ↓
Evaluated
   ↓
Validated
   ↓
Registered
```

---

# 22. Skill Promotion

Skill chỉ được promote khi:

```text
evaluation threshold
+
robustness threshold
+
calibration threshold
+
policy compliance
```

đạt yêu cầu của domain.

---

# 23. Skill Demotion

Nếu regression:

```text
Reliable
   ↓
Degraded
   ↓
Suspended
```

Skill vẫn giữ lịch sử.

---

# 24. Skill Suspension

```axiom
SkillStatus {
    Candidate
    Active
    Degraded
    Suspended
    Retired
}
```

---

# 25. Skill Retirement

Skill có thể retired khi:

- model dependency obsolete;
- tool removed;
- policy changed;
- capability superseded;
- evaluation invalidated.

---

# 26. Skill Dependency Graph

```text
Skill A
 ├── Skill B
 ├── Skill C
 └── Tool X
```

Nếu B bị invalidated, A phải được đánh dấu affected.

---

# 27. SkillDependency

```axiom
struct SkillDependency {
    source: SkillId
    dependency: DependencyId
    kind: DependencyKind
    required_version: optional<Version>
}
```

---

# 28. Skill Composition

Nhiều skill có thể compose:

```text
vision
+
language
+
planning
+
tool_use
=
visual_task_skill
```

Composition phải giữ provenance.

---

# 29. Skill Transfer

Có thể transfer skill:

```text
domain A
→ domain B
```

nhưng phải coi transfer là hypothesis.

Không tự động giả định:

```text
skill(A) = skill(B)
```

---

# 30. TransferAssessment

```axiom
struct TransferAssessment {
    source_skill: SkillId
    target_domain: DomainId
    similarity: f32
    expected_transfer: f32
    uncertainty: f32
    evidence: EvidenceSet
}
```

---

# 31. Negative Transfer

Nếu transfer gây regression:

```text
NegativeTransfer
```

phải được ghi nhận.

---

# 32. Learning Objective

```axiom
struct LearningObjective {
    skill: SkillId
    target_distribution: TaskDistribution
    required_metrics: MetricSet
    constraints: ConstraintSet
    completion_criteria: CompletionCriteria
}
```

---

# 33. Curriculum

Curriculum là sequence/graph của learning stages.

```axiom
struct Curriculum {
    id: CurriculumId
    objective: LearningObjective
    stages: CurriculumStageSet
    prerequisites: SkillSet
    progression_policy: ProgressionPolicy
}
```

---

# 34. Curriculum Stage

```axiom
struct CurriculumStage {
    id: StageId
    prerequisites: SkillSet
    dataset: DatasetId
    exercises: ExerciseSet
    difficulty: Difficulty
    evaluation: EvaluationProtocol
}
```

---

# 35. Curriculum Graph

Không bắt buộc tuyến tính:

```text
A ─→ B ─→ D
│    │
└──→ C ─┘
```

cho phép parallel learning.

---

# 36. Adaptive Curriculum

Runtime có thể thay đổi curriculum dựa trên:

```text
performance
failure
confidence
learning speed
forgetting
```

nhưng curriculum change phải được log.

---

# 37. Difficulty Adaptation

```axiom
DifficultyPolicy {
    increase_after
    decrease_after
    plateau_threshold
    failure_limit
}
```

---

# 38. Mastery

Mastery không dựa trên số lần luyện tập đơn thuần.

Phải xét:

```text
accuracy
robustness
generalization
retention
calibration
```

---

# 39. Retention

Skill có thể suy giảm theo thời gian.

```axiom
RetentionState {
    last_practiced
    performance_decay
    refresh_requirement
}
```

---

# 40. Spaced Relearning

661 có thể scheduling refresh tasks.

---

# 41. Forgetting

Forgetting có thể là:

```text
memory compaction
skill decay
model forgetting
knowledge invalidation
```

phải phân biệt.

---

# 42. Experiment

```axiom
struct LearningExperiment {
    id: ExperimentId
    hypothesis: ImprovementHypothesis
    baseline: EvaluationBaseline
    intervention: Intervention
    environment: ExperimentEnvironment
    budget: ExperimentBudget
    success_criteria: EvaluationCriteria
    rollback: RollbackPlan
}
```

---

# 43. Experiment Isolation

Experiment nên chạy trong:

```text
sandbox
shadow runtime
simulation
isolated model version
```

khi có risk.

---

# 44. Experiment Environment

```axiom
struct ExperimentEnvironment {
    runtime_version
    model_version
    dataset_version
    tool_versions
    hardware_profile
    configuration_hash
}
```

---

# 45. Experiment Reproducibility

Experiment phải có:

```text
seed
dataset
environment
model revision
configuration
evaluation version
```

---

# 46. Experiment Randomization

Nếu cần stochastic learning:

```axiom
RandomSeed
```

phải được lưu để reproduce.

---

# 47. A/B Evaluation

Có thể chạy:

```text
baseline A
candidate B
```

trên cùng evaluation protocol.

---

# 48. Shadow Learning

Candidate học trong shadow:

```text
Production Model
       │
       ├── serving
       │
Candidate Model
       └── shadow evaluation
```

Candidate không có authority production.

---

# 49. Online Learning

Online learning phải có:

```text
data validation
drift detection
rate limit
rollback
evaluation
```

---

# 50. Streaming Learning

Data stream phải có:

```text
schema
source
timestamp
quality
provenance
privacy
retention
```

---

# 51. Data Quality

Learning data phải kiểm tra:

```text
missingness
duplicates
corruption
distribution shift
label quality
poisoning indicators
```

---

# 52. Data Poisoning Boundary

661 không được coi mọi observed data là trusted training data.

Trust pipeline:

```text
Observed
→ Validated
→ Approved
→ Training Eligible
```

---

# 53. Dataset Governance

643/640/647 kiểm soát:

```text
privacy
licensing
provenance
retention
consent
deployment scope
```

---

# 54. Training Eligibility

```axiom
TrainingEligibility {
    allowed
    reasons
    provenance
    policy
    expiration
}
```

---

# 55. Learning from User Feedback

User feedback có thể trở thành:

```text
feedback signal
```

nhưng không tự động trở thành ground truth.

---

# 56. Feedback Provenance

```axiom
Feedback {
    source
    content
    timestamp
    context
    confidence
}
```

---

# 57. Reward Signal

661 hỗ trợ reward:

```axiom
RewardSignal {
    value
    source
    reliability
    context
}
```

Reward không tự động đồng nghĩa với true objective.

---

# 58. Reward Hacking Protection

Evaluation phải kiểm tra:

```text
metric gaming
proxy optimization
shortcut behavior
distribution exploitation
```

---

# 59. Objective Integrity

Learning system không được tự thay đổi objective để đạt score.

Objective changes phải governed.

---

# 60. Goal Preservation

```text
Original Objective
      ↓
Learning
```

không:

```text
Learning
      ↓
rewrite objective
```

nếu không có explicit authorized objective update.

---

# 61. Curriculum Gaming

Agent không được tự chọn benchmark dễ hơn chỉ để đạt mastery.

Benchmark protocol phải immutable/pinned trong evaluation.

---

# 62. Benchmark Pinning

```axiom
BenchmarkReference {
    benchmark_id
    version
    dataset_hash
    protocol_hash
}
```

---

# 63. Generalization

Learning evaluation phải có:

```text
training distribution
validation distribution
unseen distribution
```

khi domain cho phép.

---

# 64. Overfitting Detection

Candidate bị đánh dấu suspicious nếu:

```text
training ↑
validation ↓
```

---

# 65. Robustness

Skill promotion nên kiểm tra:

```text
noise
missing data
distribution shift
adversarial inputs
resource constraints
tool failure
```

theo domain.

---

# 66. Calibration

Improvement không chỉ tăng accuracy.

Phải theo dõi:

```text
confidence
actual correctness
```

---

# 67. Self-Improvement Score Vector

```axiom
ImprovementMetrics {
    correctness
    robustness
    generalization
    calibration
    latency
    memory
    energy
    cost
    reliability
}
```

Không ép thành một scalar.

---

# 68. Pareto Improvement

Candidate có thể được xem là non-dominated nếu:

```text
improves one dimension
without unacceptable degradation
```

Decision policy chọn theo application objective.

---

# 69. No Universal Better

661 không định nghĩa:

```text
candidate B is universally better
```

mà chỉ:

```text
B satisfies ImprovementPolicy P
```

---

# 70. ImprovementPolicy

```axiom
struct ImprovementPolicy {
    required_metrics
    maximum_regression
    minimum_gain
    robustness_requirements
    calibration_requirements
    risk_limit
}
```

---

# 71. Risk Assessment

```axiom
RiskAssessment {
    probability
    impact
    uncertainty
    affected_resources
    affected_capabilities
    mitigations
}
```

---

# 72. Risk Budget

Self-improvement có:

```axiom
ImprovementBudget {
    compute
    memory
    time
    data
    energy
    tool_calls
    risk
}
```

---

# 73. Risk Escalation

Nếu candidate vượt risk:

```text
STOP
→ escalate to policy/governance
```

---

# 74. Recursive Improvement

Recursive improvement:

```text
Improver
    improves
Target
```

Có thể:

```text
Self-improver
    ↓
improve skill learner
    ↓
learner improves self-model
    ↓
self-model selects better learner
```

Phải giới hạn recursion depth.

---

# 75. Recursive Improvement Depth

```axiom
RecursiveImprovementBudget {
    max_depth
    max_iterations
    max_compute
    max_wall_time
}
```

---

# 76. Improvement Graph

Mỗi improvement phải lưu:

```text
parent improvement
child improvement
dependencies
outcomes
```

---

# 77. Improvement Lineage

```axiom
ImprovementLineage {
    root
    parent
    candidate
    evidence
    evaluations
    promotions
    rollbacks
}
```

---

# 78. Improvement Transaction

Một improvement phải là transaction logic:

```text
BEGIN
BASELINE
EXPERIMENT
EVALUATE
VALIDATE
PROMOTE
COMMIT
```

hoặc:

```text
ROLLBACK
```

---

# 79. Promotion

Promotion từ candidate → active:

```text
Candidate
   ↓
Validated
   ↓
Approved
   ↓
Promoted
```

---

# 80. Approval

Approval có thể yêu cầu:

```text
automatic
policy-based
human
external evaluator
multi-party
```

tùy risk.

---

# 81. No Universal Human Approval Requirement

Low-risk adaptation có thể automatic.

High-risk modification phải escalate theo policy.

---

# 82. Modification Classes

```text
Class A:
context/memory adaptation

Class B:
skill update

Class C:
model parameter update

Class D:
tool/capability update

Class E:
code/runtime update

Class F:
policy/security/authority update
```

Class càng cao càng cần governance.

---

# 83. Policy Boundary

661 không được tự modify:

```text
603 security
639 policy
647 governance
```

trừ khi external authority explicitly authorizes.

---

# 84. Code Improvement

Code optimizer có thể:

```text
source
→ candidate
→ compile
→ test
→ benchmark
→ verify
→ shadow
→ deploy
```

---

# 85. Compiler Self-Optimization

Axiom compiler có thể sử dụng 661 để optimize itself nhưng:

```text
compiler build reproducibility
```

phải được duy trì.

---

# 86. Compiler Candidate

```text
Compiler A
   ↓
Compiler B
   ↓
Build bootstrap tests
   ↓
Conformance
   ↓
Performance
   ↓
Promotion
```

---

# 87. Self-Hosting Boundary

Compiler self-improvement không được phá:

```text
bootstrap chain
ABI
language conformance
reproducibility
```

---

# 88. Model Improvement

Model update:

```text
Model A
→ training
→ Model B
→ benchmark
→ safety evaluation
→ calibration
→ deployment
```

---

# 89. Model Registry

647 lưu:

```text
model
version
training lineage
evaluation
approval
deployment status
```

---

# 90. Skill Registry

661 quản lý:

```axiom
SkillRegistry {
    skills
    versions
    dependencies
    reliability
    status
    provenance
}
```

---

# 91. Capability Registry Integration

Sau skill promotion:

```text
Skill
   ↓
Capability Evidence
   ↓
660 SelfModel
```

Nhưng promotion không trực tiếp mint authority.

---

# 92. Capability Acquisition

Capability acquisition có thể đến từ:

```text
learning
tool installation
model deployment
hardware availability
skill composition
external delegation
```

---

# 93. Tool Acquisition

Tool acquisition phải qua:

```text
623 Plugin/Extension
625 Package
603 Security
639 Policy
647 Governance
```

661 chỉ tạo acquisition proposal.

---

# 94. Hardware Acquisition

Hardware capability từ:

```text
614 Device Runtime
606 Resource Governor
```

không do learning layer tự tạo.

---

# 95. Skill from Simulation

648 có thể tạo synthetic training environment.

661:

```text
simulation
→ practice
→ evaluation
→ transfer
```

---

# 96. Sim-to-Real

Nếu skill học trong simulation:

```text
Simulation Validated
```

không tự động nghĩa:

```text
Real World Validated
```

cần transfer evaluation.

---

# 97. Simulation Gap

```axiom
SimRealityGap {
    simulated_metrics
    real_metrics
    difference
    uncertainty
}
```

---

# 98. Self-Experimentation

Agent có thể đề xuất:

```text
"What experiment should I run?"
```

Nhưng experiment phải obey:

```text
safety
policy
resource
privacy
governance
```

---

# 99. Experiment Planner

```axiom
ExperimentPlanner {
    objective
    candidate_interventions
    expected_information_gain
    expected_cost
    risk
}
```

---

# 100. Information Gain

653/652 có thể hỗ trợ chọn experiment có:

```text
high expected information gain
```

nhưng không bỏ qua safety/risk.

---

# 101. Active Learning

Active learning có thể chọn:

```text
which data to label
which examples to query
which experiments to run
```

---

# 102. Active Learning Budget

Phải giới hạn:

```text
queries
data cost
latency
human interactions
```

---

# 103. Human-in-the-Loop

Một experiment có thể yêu cầu human label:

```text
HumanFeedbackRequest
```

---

# 104. Human Feedback Quality

Feedback phải có:

```text
annotator
context
confidence
agreement
timestamp
```

---

# 105. Multi-Agent Learning

Nhiều agents có thể chia sẻ:

```text
skills
experiences
models
```

nhưng provenance phải giữ nguồn.

---

# 106. Federated Learning

Có thể hỗ trợ:

```text
local training
→ aggregate
→ evaluate
→ deploy
```

qua 643/628.

---

# 107. Federated Self-Improvement

Một agent không được giả định rằng:

```text
global model
=
local self-model
```

---

# 108. Knowledge Distillation

661 có thể dùng teacher/student:

```text
Teacher
   ↓
Distillation
   ↓
Student
```

Candidate phải được evaluate độc lập.

---

# 109. Skill Distillation

Một skill có thể distill thành:

```text
small model
procedure
heuristic
compiled function
```

để giảm runtime cost.

---

# 110. Proceduralization

Nếu một learned behavior ổn định:

```text
learned policy
→ validated procedure
```

có thể compile thành native procedure.

---

# 111. Procedure Promotion

Phải giữ:

```text
source model
evidence
validation
version
```

để rollback.

---

# 112. Learned Heuristic

Axiom có thể lưu:

```axiom
LearnedHeuristic {
    condition
    action
    expected_gain
    confidence
    evidence
}
```

---

# 113. Heuristic Safety

Heuristic không được tự override:

```text
security
policy
type safety
memory safety
```

---

# 114. Skill Compiler

661 có thể compile skill graph:

```text
SkillGraph
→ SkillIR
→ Native IR
→ optimized native code
```

---

# 115. Skill IR

```text
SkillCreate
SkillCompose
SkillPractice
SkillEvaluate
SkillCompare
SkillPromote
SkillDemote
SkillSuspend
SkillRetire
SkillTransfer
SkillCalibrate
SkillRefresh
```

---

# 116. Learning IR

```text
LearningObjectiveCreate
CurriculumCreate
CurriculumAdapt
ExperimentCreate
ExperimentRun
ExperimentEvaluate
TrainingStart
TrainingStop
TrainingCheckpoint
ModelCandidateCreate
ModelCandidateEvaluate
ModelPromote
ModelRollback
```

---

# 117. Improvement IR

```text
GapDetect
HypothesisCreate
InterventionPlan
ImprovementRun
ImprovementEvaluate
RegressionDetect
ImprovementPromote
ImprovementReject
ImprovementRollback
```

---

# 118. Capability Acquisition IR

```text
CapabilityGapDetect
CapabilityCandidateCreate
CapabilityTest
CapabilityValidate
CapabilityRegister
CapabilitySuspend
CapabilityRetire
```

---

# 119. Self-Improvement IR Boundary

IR operation:

```text
CapabilityRegister
```

không được tự lower thành:

```text
GrantAuthority
```

---

# 120. Annotation Set

```text
@learn
@learning_objective
@curriculum
@experiment
@practice
@skill
@skill_level
@skill_transfer
@skill_compose
@skill_evaluate
@skill_promote
@skill_demote
@skill_suspend
@skill_retire
@capability_gap
@improvement
@improvement_hypothesis
@improvement_budget
@improvement_policy
@improvement_experiment
@improvement_validate
@improvement_promote
@improvement_rollback
@self_improve
@recursive_improvement
@self_optimize
@online_learning
@active_learning
@continual_learning
@transfer_learning
@distill
@sim2real
@experiment_sandbox
```

---

# 121. Metadata Artifacts

Compiler tạo:

```text
.axlearn
.axskill
.axskillgraph
.axcurriculum
.axexperiment
.aximprovement
.aximprovementlineage
.axcapgap
.axcapabilitycandidate
.axskillregistry
.axtraining
.axmodelcandidate
.axtransfer
.axcalibration
.axregression
```

---

# 122. `.axskill`

Chứa:

```text
skill id
version
domain
dependencies
procedure
knowledge
model
tools
evaluation
reliability
status
```

---

# 123. `.aximprovement`

Chứa:

```text
objective
baseline
candidate
intervention
metrics
regression
risk
approval
promotion
rollback
```

---

# 124. `.axexperiment`

Chứa:

```text
hypothesis
environment
dataset
seed
intervention
result
evaluation
```

---

# 125. CLI

```text
axiom learn inspect
axiom learn objective
axiom learn curriculum
axiom learn stage
axiom learn run
axiom learn pause
axiom learn resume
axiom learn checkpoint
axiom learn evaluate

axiom skill list
axiom skill inspect
axiom skill test
axiom skill train
axiom skill evaluate
axiom skill compare
axiom skill promote
axiom skill demote
axiom skill suspend
axiom skill resume
axiom skill retire
axiom skill transfer
axiom skill compose
axiom skill refresh

axiom capability gap
axiom capability candidate
axiom capability test
axiom capability validate
axiom capability register

axiom improve inspect
axiom improve baseline
axiom improve plan
axiom improve experiment
axiom improve evaluate
axiom improve compare
axiom improve promote
axiom improve reject
axiom improve rollback
axiom improve lineage

axiom experiment create
axiom experiment run
axiom experiment inspect
axiom experiment compare
axiom experiment rollback
```

---

# 126. `axiom improve plan`

Output:

```text
Capability Gap
Baseline
Hypotheses
Candidate Interventions
Expected Gain
Expected Cost
Risk
Evaluation Protocol
Rollback Plan
```

---

# 127. `axiom improve compare`

So sánh:

```text
baseline
candidate A
candidate B
```

theo vector metrics, không ép thành universal ranking.

---

# 128. `axiom skill evaluate`

Output:

```text
success
robustness
generalization
calibration
retention
latency
resource usage
```

---

# 129. `axiom skill promote`

Kiểm tra:

```text
evaluation
policy
risk
dependencies
regression
approval
```

trước khi active.

---

# 130. `axiom capability gap`

Nguồn:

```text
task requirement
evaluation
self prediction
failure history
planner
external evaluator
```

---

# 131. Profiles

```text
AXLEARN_NONE
AXLEARN_CORE
AXLEARN_MEMORY
AXLEARN_SKILL
AXLEARN_CURRICULUM
AXLEARN_EXPERIMENT
AXLEARN_ACTIVE
AXLEARN_ONLINE
AXLEARN_CONTINUAL
AXLEARN_TRANSFER
AXLEARN_DISTILLATION
AXLEARN_SIMULATION
AXLEARN_SIM2REAL
AXLEARN_OPTIMIZATION
AXLEARN_CAPABILITY
AXLEARN_SELF_IMPROVE
AXLEARN_RECURSIVE
AXLEARN_DISTRIBUTED
AXLEARN_GOVERNED
AXLEARN_FULL
```

---

# 132. Profile Dependencies

```text
AXLEARN_SKILL
    → AXLEARN_CORE
```

```text
AXLEARN_SELF_IMPROVE
    → AXLEARN_SKILL
    → 660
    → 646
    → 647
```

```text
AXLEARN_RECURSIVE
    → AXLEARN_SELF_IMPROVE
    → 603
    → 639
```

---

# 133. Runtime State

```axiom
enum ImprovementState {
    Proposed,
    Baseline,
    Experimenting,
    Training,
    Evaluating,
    Validating,
    Approved,
    Promoting,
    Active,
    Rejected,
    RolledBack,
    Suspended,
    Retired
}
```

---

# 134. Learning State

```axiom
struct LearningState {
    objective
    curriculum
    stage
    progress
    budget
    metrics
    checkpoint
    status
}
```

---

# 135. Skill State

```axiom
struct SkillState {
    skill_id
    version
    level
    reliability
    confidence
    dependencies
    status
}
```

---

# 136. Improvement State

```axiom
struct ImprovementRuntimeState {
    objective
    baseline
    candidate
    experiment
    metrics
    risk
    approval
    state
}
```

---

# 137. Checkpoint

Training/learning phải hỗ trợ:

```text
checkpoint
resume
rollback
```

qua 600.

---

# 138. Incremental Learning

Không yêu cầu retrain toàn bộ model.

Có thể:

```text
adapter
LoRA-like module
skill memory
retrieval
procedure
small model
specialized model
```

Backend quyết định.

---

# 139. Parameter Update Boundary

643 sở hữu training/model execution.

661 sở hữu:

```text
why
what
when
whether
evaluation
promotion
```

---

# 140. Learning Strategy

```axiom
enum LearningStrategy {
    Retrieval,
    Practice,
    FineTune,
    Distill,
    Reinforce,
    Imitate,
    SelfPlay,
    Simulation,
    ToolUse,
    Curriculum,
    Transfer,
    Hybrid
}
```

---

# 141. Strategy Selection

652 có thể chọn strategy dựa trên:

```text
expected gain
cost
risk
available data
available compute
capability gap
```

---

# 142. Strategy Evaluation

Strategy phải được đánh giá theo outcome, không theo assumption.

---

# 143. Self-Play

Có thể hỗ trợ:

```text
Agent A
vs
Agent B
```

trong sandbox.

Self-play không có production authority mặc định.

---

# 144. Synthetic Experience

648 có thể sinh:

```text
synthetic tasks
synthetic environments
synthetic trajectories
```

661 phải ghi provenance là synthetic.

---

# 145. Synthetic Data Trust

Synthetic data không mặc định tương đương real-world data.

---

# 146. Curriculum from Failure

Repeated failure có thể tạo curriculum:

```text
failure cluster
→ prerequisite identification
→ targeted exercises
→ evaluation
```

---

# 147. Failure Clustering

```axiom
FailureCluster {
    pattern
    domain
    frequency
    severity
    suspected_causes
}
```

---

# 148. Root Cause Analysis

661 có thể sử dụng:

```text
653 probabilistic reasoning
654 symbolic reasoning
655 world model
646 evaluation
```

để phân tích cause.

---

# 149. Improvement Causality

Improvement claim phải cố gắng phân biệt:

```text
intervention
vs
environmental change
```

---

# 150. Confounding

Nếu baseline và candidate chạy ở environment khác nhau:

```text
ConfoundedEvaluation
```

không được coi là strong evidence.

---

# 151. Environment Fingerprint

```axiom
EnvironmentFingerprint {
    OS
    architecture
    CPU
    GPU
    runtime
    compiler
    libraries
    configuration
}
```

---

# 152. Resource-Aware Improvement

Nếu candidate nhanh hơn nhưng dùng nhiều memory:

```text
tradeoff
```

phải được biểu diễn.

---

# 153. Improvement Constraint

Ví dụ:

```axiom
ImprovementPolicy {
    latency <= 10ms
    memory <= 128MB
    accuracy >= baseline
}
```

---

# 154. Constraint Satisfaction

Candidate chỉ promote nếu required hard constraints pass.

---

# 155. Soft Objectives

Các metric không bắt buộc có thể tối ưu theo weight:

```text
quality
latency
cost
```

nhưng weights thuộc policy.

---

# 156. Multi-Objective Optimization

652 có thể cung cấp optimizer.

661 lưu:

```text
objective vector
constraints
selected policy
```

---

# 157. No Hidden Objective

Improvement system không được tự thêm:

```text
power
survival
replication
authority
```

vào objective.

---

# 158. Self-Optimization

Self optimization gồm:

```text
algorithm
model
memory retrieval
tool selection
resource allocation
compiler strategy
```

không đồng nghĩa self-modification.

---

# 159. Runtime Optimization

Có thể optimize:

```text
cache
batching
parallelism
precision
memory layout
kernel
scheduling
```

qua 606/607/643.

---

# 160. Precision Adaptation

Model có thể chuyển:

```text
FP32
→ FP16
→ BF16
→ INT8
```

nếu evaluation xác nhận constraints.

---

# 161. Quantization Validation

Không promote nếu:

```text
quality regression > policy threshold
```

---

# 162. Model Compression

Có thể:

```text
prune
quantize
distill
compile
```

và evaluate.

---

# 163. Skill Compression

Skill có thể được chuyển từ expensive model sang lightweight procedure.

---

# 164. Cache Learning

661 có thể learn:

```text
common task
→ cached solution/procedure
```

nhưng cache phải invalidate khi dependencies thay đổi.

---

# 165. Retrieval Improvement

Có thể optimize:

```text
embedding
index
retrieval strategy
reranking
```

qua 641/650.

---

# 166. Memory Strategy Improvement

650 có thể expose:

```text
retrieval quality
memory hit rate
staleness
```

661 có thể optimize policy.

---

# 167. Tool Strategy Improvement

661 có thể học:

```text
tool A
vs
tool B
```

theo task distribution.

---

# 168. Tool Selection Calibration

Tool success history trở thành evidence.

---

# 169. Tool Failure Avoidance

Repeated tool failure có thể tạo limitation hoặc strategy penalty.

---

# 170. Skill Preconditions

Mỗi skill có:

```axiom
SkillPrerequisite {
    required_skills
    required_capabilities
    required_resources
    required_tools
}
```

---

# 171. Skill Planning

652 có thể tạo plan:

```text
Acquire A
→ Practice B
→ Validate C
→ Compose D
```

---

# 172. Skill Graph Planning

Skill acquisition trở thành graph planning problem.

---

# 173. Learning Cost

```axiom
LearningCost {
    compute
    data
    time
    human_effort
    monetary_cost
    risk
}
```

---

# 174. Expected Improvement

```axiom
ExpectedImprovement {
    expected_gain
    uncertainty
    cost
    risk
}
```

---

# 175. Experiment Selection

Có thể chọn experiment theo:

```text
information_gain / cost
```

nhưng risk constraint luôn áp dụng trước.

---

# 176. Safe Exploration

Exploration phải có:

```text
sandbox
resource limit
authority limit
rollback
termination condition
```

---

# 177. Production Exploration

Production exploration chỉ được phép khi policy cho phép.

---

# 178. Exploration Budget

```axiom
ExplorationBudget {
    max_trials
    max_cost
    max_risk
    max_duration
}
```

---

# 179. Exploration Termination

Stop khi:

```text
objective achieved
budget exhausted
risk exceeded
regression detected
policy revoked
```

---

# 180. Learning Abort

Abort phải để lại checkpoint/audit.

---

# 181. Partial Learning

Nếu curriculum dừng giữa chừng:

```text
PartialSkillState
```

không promote thành mastered.

---

# 182. Skill Snapshot

```axiom
SkillSnapshot {
    skill_id
    version
    state
    metrics
    dependencies
    timestamp
}
```

---

# 183. Skill Rollback

Rollback skill phải preserve lineage.

---

# 184. Skill Branching

Có thể:

```text
Skill A v1
 ├── experimental v2
 └── experimental v3
```

---

# 185. Skill Merge

Merge phải resolve:

```text
procedure conflicts
model conflicts
dependency conflicts
evaluation conflicts
```

---

# 186. Skill Versioning

Version semantic:

```text
major
minor
patch
```

theo compatibility.

---

# 187. Skill ABI

Nếu skill compile thành native callable:

```text
skill ABI
```

phải có stable interface.

---

# 188. Skill Capability Contract

```axiom
SkillContract {
    input
    output
    preconditions
    postconditions
    resource_bounds
    failure_modes
}
```

---

# 189. Skill Verification

Postcondition có thể được kiểm tra bằng:

```text
tests
assertions
formal verification
external evaluator
```

---

# 190. Skill Safety Contract

Skill contract có:

```text
safety constraints
authority requirements
data requirements
```

---

# 191. Learning Safety

Learning system phải kiểm tra:

```text
data safety
action safety
environment safety
model safety
deployment safety
```

---

# 192. Improvement Governance

647 quản lý:

```text
approved improvement classes
model registry
deployment
lifecycle
```

---

# 193. Policy Governance

639 quản lý:

```text
allowed objectives
forbidden interventions
risk limits
deployment scope
```

---

# 194. Security Governance

603 quản lý:

```text
execution
credentials
network
filesystem
hardware
tool installation
```

---

# 195. Improvement Audit

Mọi promotion:

```text
who/what/when/why
```

phải audit được.

---

# 196. Provenance

Improvement phải trace được:

```text
data
model
skill
experiment
evaluator
policy
environment
```

---

# 197. Explainable Improvement

Agent có thể trả:

```text
Why did capability X improve?
```

bằng:

```text
intervention
evidence
evaluation
```

không cần hidden reasoning.

---

# 198. Improvement Report

```axiom
ImprovementReport {
    objective
    baseline
    candidate
    changes
    metrics
    regressions
    risks
    evidence
    decision
}
```

---

# 199. Decision Provenance

`decision` phải ghi:

```text
policy
evaluator
timestamp
authorization
```

---

# 200. Self-Improvement and 660

Sau improvement:

```text
661
 ↓
Capability Evidence
 ↓
660 SelfModel
 ↓
new capability/skill state
```

660 không tự tin rằng improvement thành công nếu 661 chưa validated.

---

# 201. Self-Improvement and 646

646 cung cấp:

```text
benchmark
evaluation
red-team
quality
validation
```

661 sử dụng kết quả.

---

# 202. Self-Improvement and 647

647 quyết định:

```text
model lifecycle
deployment
approval
```

---

# 203. Self-Improvement and 648

648 cung cấp:

```text
simulation
synthetic environment
counterfactual
```

---

# 204. Self-Improvement and 650

650 cung cấp:

```text
experience
memory
retrieval
historical performance
```

---

# 205. Self-Improvement and 652

652 cung cấp:

```text
experiment planning
curriculum planning
strategy selection
resource allocation
```

---

# 206. Self-Improvement and 653

653 cung cấp:

```text
uncertainty
Bayesian update
expected information gain
```

---

# 207. Self-Improvement and 654

654 cung cấp:

```text
rules
constraints
formal reasoning
verification
```

---

# 208. Self-Improvement and 655

655 cung cấp:

```text
environment model
simulation assumptions
causal context
```

---

# 209. Self-Improvement and 657

657 cung cấp:

```text
cognitive strategies
attention
reasoning state
```

---

# 210. Self-Improvement and 659

659 có thể cung cấp:

```text
affective feedback
interaction quality
social-emotional objectives
```

---

# 211. Self-Improvement and 603

Không có learning path nào bypass:

```text
security
authority
permissions
```

---

# 212. Self-Improvement and 639

Objective/intervention phải obey policy.

---

# 213. Recursive Improvement Boundary

Recursive improvement có ba cấp:

```text
Object-level:
improve task skill

Meta-level:
improve learning strategy

Meta-meta-level:
improve learning architecture
```

Cấp sau luôn cần stricter governance.

---

# 214. Recursive Level

```axiom
enum ImprovementLevel {
    Task,
    Skill,
    Strategy,
    Model,
    Architecture,
    Governance
}
```

`Governance` không được self-modify mặc định.

---

# 215. Recursive Improvement Guard

```axiom
RecursiveGuard {
    max_level
    max_depth
    max_iterations
    risk_limit
    authority_scope
}
```

---

# 216. Improvement Oscillation

Nếu system liên tục:

```text
A → B → A → B
```

phải detect:

```text
ImprovementOscillation
```

---

# 217. Improvement Thrashing

Nếu frequent updates làm giảm stability:

```text
ImprovementThrashing
```

có thể trigger freeze period.

---

# 218. Stability Window

Candidate phải tồn tại đủ evaluation window nếu policy yêu cầu.

---

# 219. Regression After Deployment

Nếu production performance giảm:

```text
detect
→ suspend
→ rollback
→ investigate
```

---

# 220. Canary Improvement

Candidate có thể deploy:

```text
0%
→ 1%
→ 5%
→ 25%
→ 100%
```

theo deployment policy.

---

# 221. Canary Metrics

Theo dõi:

```text
quality
error
latency
resource
safety
user-visible regression
```

---

# 222. Blue/Green Improvement

647/636 có thể hỗ trợ:

```text
Blue = old
Green = candidate
```

661 cung cấp evaluation signals.

---

# 223. Improvement Freeze

Có thể freeze learning khi:

```text
incident
policy change
security event
evaluation invalid
data poisoning suspicion
```

---

# 224. Learning Kill Switch

Authorized controller phải có thể:

```text
pause
stop
rollback
```

learning.

---

# 225. No Self-Disable of Kill Switch

Self-improvement system không được tự vô hiệu hóa kill switch.

---

# 226. Model Poisoning Detection

Candidate training phải kiểm tra:

```text
anomalous samples
behavioral backdoors
distribution anomalies
unexpected capability changes
```

---

# 227. Capability Expansion Review

Nếu improvement tạo capability mới ngoài objective:

```text
UnexpectedCapability
```

phải được flag.

---

# 228. Emergent Capability Boundary

Unexpected capability không tự động được register.

Flow:

```text
Detected
→ Characterized
→ Evaluated
→ Policy reviewed
→ Registered or blocked
```

---

# 229. Capability Inventory

Self-model phải có:

```text
known capabilities
unknown candidates
blocked capabilities
deprecated capabilities
```

---

# 230. Capability Discovery

Capability discovery có thể đến từ:

```text
benchmark
tool
training
composition
emergent behavior
external evaluator
```

---

# 231. Emergent Behavior

661 phải coi emergent behavior là:

```text
observed behavior
```

trước khi coi là capability.

---

# 232. Emergent Capability Validation

Cần:

```text
repeatability
scope
reliability
failure modes
safety
```

---

# 233. Capability Registration

```axiom
CapabilityRegistration {
    capability
    evidence
    evaluator
    version
    scope
    policy
}
```

---

# 234. Capability Revocation

Capability có thể revoked bởi:

```text
security
policy
governance
runtime failure
model rollback
```

---

# 235. Capability Revocation Propagation

Nếu capability X bị revoked:

```text
skills depending on X
```

phải được re-evaluate.

---

# 236. Learning Dependency Invalidation

Nếu dataset bị revoked:

```text
models trained from dataset
skills derived from model
```

phải được trace.

---

# 237. Data Lineage

661 phải tích hợp 640:

```text
data
→ training
→ model
→ skill
→ capability
```

---

# 238. Model Lineage

```axiom
ModelLineage {
    parent
    dataset
    training_run
    evaluator
    deployment
}
```

---

# 239. Skill Lineage

```axiom
SkillLineage {
    source_model
    source_data
    source_skills
    training_runs
    evaluation_runs
}
```

---

# 240. Improvement Lineage Graph

```text
Dataset
  ↓
Training
  ↓
Model
  ↓
Skill
  ↓
Capability
  ↓
SelfModel
```

Mọi node phải truy nguyên được.

---

# 241. Learning Reproducibility

Một learning run phải có đủ metadata để reproduce trong cùng environment.

---

# 242. Non-Deterministic Learning

Nếu stochastic:

```text
distribution
```

phải được báo cáo thay vì giả định một run đại diện tuyệt đối.

---

# 243. Statistical Evaluation

Evaluation có thể lưu:

```text
mean
variance
confidence interval
sample count
```

---

# 244. Small Sample Warning

Nếu sample nhỏ:

```text
LowEvidence
```

phải được ghi.

---

# 245. Confidence vs Statistical Confidence

Axiom phân biệt:

```text
model confidence
statistical confidence
evaluation confidence
```

---

# 246. Learning Uncertainty

```axiom
LearningUncertainty {
    data
    optimization
    model
    evaluation
    transfer
    deployment
}
```

---

# 247. Improvement Decision

Decision có thể:

```text
Promote
Reject
Hold
RequestMoreEvidence
Rollback
```

---

# 248. No Forced Promotion

Nếu evidence không đủ:

```text
Hold
```

được coi là valid outcome.

---

# 249. More Evidence Planning

661 có thể đề xuất:

```text
additional benchmark
additional training
additional simulation
additional external evaluation
```

---

# 250. Active Improvement Loop

```text
insufficient evidence
→ choose experiment
→ gather evidence
→ re-evaluate
```

với budget.

---

# 251. Learning Scheduler

606/607 có thể schedule learning:

```text
background
idle-time
night
GPU availability
resource-aware
```

---

# 252. Learning Priority

652 có thể prioritize:

```text
task urgency
capability gap severity
expected benefit
cost
risk
```

---

# 253. Background Learning

Background learning không được làm ảnh hưởng hard real-time workload ngoài configured resource budget.

---

# 254. Resource Isolation

Learning worker có thể chạy:

```text
CPU quota
GPU quota
memory quota
IO quota
network quota
```

---

# 255. Training Sandbox

Training sandbox phải giới hạn:

```text
filesystem
network
process
device
credentials
```

qua 603.

---

# 256. Experiment Sandbox

Experiment sandbox tương tự.

---

# 257. Model Artifact Isolation

Candidate models nằm trong isolated registry namespace trước promotion.

---

# 258. Skill Artifact Isolation

Candidate skill artifacts không được production discoverable trước promotion.

---

# 259. Cache Isolation

Learning cache phải tách khỏi trusted production cache nếu có risk.

---

# 260. Learning Artifact Signing

Promoted model/skill artifacts nên hỗ trợ cryptographic signing.

---

# 261. Trust Chain

```text
Data
 ↓
Training
 ↓
Model
 ↓
Skill
 ↓
Capability
 ↓
SelfModel
```

mỗi bước có provenance/trust.

---

# 262. Supply Chain

External model/skill:

```text
download
→ verify
→ scan
→ evaluate
→ sandbox
→ approve
```

qua 625/647/603.

---

# 263. Third-Party Skill

Third-party skill không được tự trở thành trusted native code.

---

# 264. Native Compilation of Learned Skill

Nếu compile learned procedure:

```text
source artifact
→ verification
→ compile
→ test
→ sandbox
→ promote
```

---

# 265. Self-Generated Code

Self-generated code được coi là untrusted candidate cho tới khi:

```text
compile
test
verify
policy check
```

pass.

---

# 266. Self-Generated Code Cannot Grant Authority

Code generation không được tự grant:

```text
filesystem
network
process
admin
```

authority.

---

# 267. Improvement Attack Surface

661 phải coi:

```text
learning
data
experiments
model updates
skill updates
```

là attack surfaces.

---

# 268. Adversarial Improvement

Attack có thể cố:

```text
poison data
game evaluator
inflate benchmark
hide regression
bypass promotion
```

---

# 269. Evaluator Separation

High-risk improvement nên dùng evaluator độc lập với learner.

---

# 270. Blind Evaluation

Khi phù hợp, candidate evaluation có thể được blind:

```text
Evaluator không biết candidate identity
```

để giảm bias.

---

# 271. Cross-Evaluator Validation

Có thể dùng:

```text
Evaluator A
Evaluator B
```

và compare.

---

# 272. Evaluation Disagreement

Nếu evaluators disagree:

```text
EvaluationConflict
```

không tự chọn winner.

---

# 273. Human Review Trigger

Policy có thể yêu cầu human review khi:

```text
high risk
large capability expansion
security impact
architecture change
high evaluator disagreement
```

---

# 274. Improvement Freeze on Incident

Incident có thể tự động freeze relevant improvement pipeline.

---

# 275. Learning Recovery

Sau failure:

```text
restore checkpoint
inspect lineage
invalidate suspect artifacts
resume from validated state
```

---

# 276. Skill Recovery

Skill registry có thể rollback tới:

```text
last known good version
```

---

# 277. Model Recovery

647 quản lý rollback model.

661 chỉ gửi:

```text
performance regression evidence
```

---

# 278. Learning Metrics

Core runtime metrics:

```text
learning_throughput
training_time
sample_efficiency
skill_acquisition_time
evaluation_time
improvement_delta
regression_rate
rollback_rate
calibration_delta
transfer_success
retention
```

---

# 279. Improvement Observability

602/633:

```text
experiment_started
experiment_completed
skill_promoted
skill_demoted
capability_detected
capability_registered
model_candidate_created
model_promoted
improvement_rolled_back
```

---

# 280. Learning Trace

Trace:

```text
objective
→ curriculum
→ experiment
→ training
→ evaluation
→ promotion
```

---

# 281. AI-Readable Improvement Manifest

```axiom
struct ImprovementManifest {
    objective
    baseline
    candidate
    metrics
    evidence
    risk
    policy
    lineage
    status
}
```

---

# 282. Self-Improvement API

```axiom
namespace improve {
    fn detect_gaps() -> CapabilityGapSet
    fn propose(gap: CapabilityGap) -> ImprovementPlan
    fn baseline(plan: ImprovementPlan) -> EvaluationBaseline
    fn experiment(plan: ImprovementPlan) -> ExperimentId
    fn evaluate(experiment: ExperimentId) -> ImprovementReport
    fn validate(report: ImprovementReport) -> ValidationResult
    fn promote(candidate: CandidateId) -> PromotionResult
    fn rollback(candidate: CandidateId) -> RollbackResult
}
```

---

# 283. Skill API

```axiom
namespace skill {
    fn inspect(id: SkillId) -> Skill
    fn evaluate(id: SkillId) -> SkillEvaluation
    fn train(id: SkillId, objective: LearningObjective) -> LearningRun
    fn compose(skills: SkillSet) -> SkillCandidate
    fn transfer(skill: SkillId, domain: DomainId) -> TransferCandidate
    fn promote(candidate: SkillCandidate) -> Skill
    fn rollback(id: SkillId, version: Version)
}
```

---

# 284. Learning API

```axiom
namespace learn {
    fn objective(...)
    fn curriculum(...)
    fn run(...)
    fn checkpoint(...)
    fn evaluate(...)
    fn pause(...)
    fn resume(...)
    fn cancel(...)
}
```

---

# 285. Capability API

```axiom
namespace capability {
    fn gaps()
    fn test(candidate)
    fn validate(candidate)
    fn register(candidate)
    fn revoke(id)
}
```

---

# 286. Self-Improvement Example

```axiom
fn improve_translation() {
    let gap = improve.detect_gaps()
        .find("translation")

    let plan = improve.propose(gap)

    let baseline = improve.baseline(plan)

    let experiment = improve.experiment(plan)

    let report = improve.evaluate(experiment)

    if improve.validate(report).approved {
        improve.promote(report.candidate)
    }
}
```

Promotion vẫn chịu 603/639/647.

---

# 287. Skill Learning Example

```axiom
let objective = learn.objective(
    skill: "image_segmentation",
    target: {
        accuracy: 0.95,
        latency: 20ms
    }
)

let run = learn.run(objective)

let result = learn.evaluate(run)
```

---

# 288. Capability Acquisition Example

```axiom
let gap = capability.gaps()
    .find("gpu_inference")

let candidate = capability.test(gap)

if capability.validate(candidate) {
    capability.register(candidate)
}
```

Register capability không tự cấp OS permission.

---

# 289. Recursive Improvement Example

```axiom
@recursive_improvement(max_depth = 2)
fn optimize_learning_strategy() {
    let strategy = learn.current_strategy()

    let candidate = improve.strategy(strategy)

    improve.evaluate(candidate)
}
```

---

# 290. Forbidden Semantic

Core runtime không cung cấp:

```text
self.become_unlimited()
self.grant_self_permission()
self.disable_safety()
self.remove_governance()
self.disable_rollback()
self.change_objective_without_authority()
```

---

# 291. Forbidden Implicit Behavior

Compiler không tự động:

```text
failure → retrain
```

hoặc:

```text
low score → modify itself
```

trừ khi application explicitly configures learning policy.

---

# 292. Default Behavior

Nếu không có improvement policy:

```text
observe
report
do not modify
```

---

# 293. Learning Opt-In

Application:

```axiom
@learn
```

hoặc profile:

```text
AXLEARN_*
```

mới link learning subsystem.

---

# 294. Zero-Cost Principle

Application không sử dụng 661:

```text
AXLEARN_NONE
```

→ không link training/experiment runtime.

---

# 295. Lightweight Skill Runtime

Một skill đã được compile có thể chạy mà không cần full learning stack.

```text
Skill
→ native code
```

---

# 296. Embedded Skill

```axiom
@skill
fn classify(...)
```

có thể compile thành static native function nếu skill backend cho phép.

---

# 297. Runtime vs Build-Time Learning

661 hỗ trợ:

```text
build-time learning
deployment-time learning
runtime learning
offline learning
```

---

# 298. Build-Time Learning

Có thể dùng benchmark trong compiler pipeline để chọn optimized artifact.

---

# 299. Deployment-Time Learning

Candidate được evaluate trước khi production activation.

---

# 300. Runtime Learning

Runtime adaptation phải obey strict budget/policy.

---

# 301. Architecture Decision

BOOTSTRAP-661 chốt:

```text
Learning
≠
Self-Modification
```

và:

```text
Capability acquisition
≠
Authority acquisition
```

---

# 302. Final Improvement Architecture

```text
             ┌───────────────────────┐
             │       660 SELF        │
             │ capability / limits   │
             └───────────┬───────────┘
                         │
                    capability gap
                         │
                         ▼
                ┌─────────────────┐
                │      661        │
                │ SELF-IMPROVEMENT│
                └────────┬────────┘
                         │
       ┌─────────────────┼─────────────────┐
       │                 │                 │
   Curriculum       Experiment         Practice
       │                 │                 │
       └─────────────────┼─────────────────┘
                         ▼
                    Skill Formation
                         │
                         ▼
                      Evaluate
                         │
                ┌────────┴────────┐
                │                 │
             Reject            Promote
                │                 │
                │                 ▼
                │             Capability
                │                 │
                │                 ▼
                │               660
                │
                └──────→ Rollback
```

---

# 303. Architectural Guarantees

661 guarantees:

1. improvement is evidence-driven;
2. baseline is explicit;
3. evaluation is versioned;
4. regression is first-class;
5. skills are versioned;
6. capabilities are evidence-backed;
7. learning data has provenance;
8. experiments are bounded;
9. recursive improvement is bounded;
10. self-update is governed;
11. security cannot be bypassed;
12. authority cannot be self-created;
13. production promotion is explicit;
14. rollback is supported;
15. improvement lineage is preserved;
16. self-model receives only validated capability evidence;
17. unknown remains distinguishable from unavailable;
18. improvement objectives cannot silently mutate;
19. candidate artifacts remain isolated;
20. zero-cost compilation is preserved for applications not using learning.

---

# 304. Core Invariants

## I-001
Learning does not imply self-modification.

## I-002
Self-modification does not imply authority.

## I-003
Capability acquisition does not imply permission acquisition.

## I-004
Skill does not imply universal competence.

## I-005
One successful example does not prove mastery.

## I-006
One failure does not prove permanent incapability.

## I-007
Improvement requires baseline evidence.

## I-008
Baseline and candidate must use compatible evaluation protocols.

## I-009
Evaluation protocol must be versioned.

## I-010
Dataset identity must be preserved.

## I-011
Model identity must be preserved.

## I-012
Environment identity must be preserved.

## I-013
Improvement claims require provenance.

## I-014
Improvement claims require uncertainty.

## I-015
Regression is first-class.

## I-016
A metric improvement does not erase another metric's regression.

## I-017
Hard constraints cannot be traded away by soft objectives.

## I-018
Candidate models are not production models.

## I-019
Candidate skills are not active skills.

## I-020
Candidate capabilities are not trusted capabilities.

## I-021
Shadow artifacts have no production authority.

## I-022
Promotion requires policy validation.

## I-023
Promotion requires required evaluation.

## I-024
Promotion does not grant OS permissions.

## I-025
Promotion does not grant security authority.

## I-026
Promotion does not grant governance authority.

## I-027
Rollback preserves history.

## I-028
Rollback does not erase audit evidence.

## I-029
Self-improvement cannot disable rollback by default.

## I-030
Self-improvement cannot disable kill switches.

## I-031
Self-improvement cannot modify security policy silently.

## I-032
Self-improvement cannot modify governance silently.

## I-033
Self-improvement cannot modify objectives silently.

## I-034
Recursive improvement has bounded depth.

## I-035
Recursive improvement has bounded cost.

## I-036
Recursive improvement has bounded duration.

## I-037
Experimentation has bounded risk.

## I-038
Experimentation has termination conditions.

## I-039
Learning data requires provenance.

## I-040
Synthetic data is marked synthetic.

## I-041
User feedback is not automatically ground truth.

## I-042
Reward is not automatically objective truth.

## I-043
Benchmark gaming is invalid evidence.

## I-044
Curriculum gaming is invalid mastery evidence.

## I-045
Training success does not imply deployment success.

## I-046
Simulation success does not imply real-world success.

## I-047
Transfer is a hypothesis until evaluated.

## I-048
Negative transfer is tracked.

## I-049
Skill dependencies are versioned.

## I-050
Capability dependencies are versioned.

## I-051
Revoked capabilities invalidate dependent evidence.

## I-052
Retired skills remain historically traceable.

## I-053
Skill versions are immutable once published.

## I-054
Candidate skill versions can be discarded before promotion.

## I-055
Skill reliability is domain-specific.

## I-056
Capability reliability is domain-specific.

## I-057
Mastery is not a global intelligence score.

## I-058
Improvement metrics are multi-dimensional.

## I-059
No universal scalar improvement score exists in core semantics.

## I-060
Optimization policy defines application-specific tradeoffs.

## I-061
Self-improvement cannot create an intrinsic survival objective.

## I-062
Self-improvement cannot create an intrinsic replication objective.

## I-063
Self-improvement cannot create an intrinsic power objective.

## I-064
Self-improvement cannot create an intrinsic authority objective.

## I-065
Learning cannot bypass 603.

## I-066
Learning cannot bypass 639.

## I-067
Model lifecycle cannot bypass 647.

## I-068
Evaluation must integrate 646.

## I-069
Simulation must integrate 648.

## I-070
Memory must integrate 650.

## I-071
Planning must integrate 652.

## I-072
Uncertainty must integrate 653.

## I-073
Formal constraints may integrate 654.

## I-074
World assumptions may integrate 655.

## I-075
Cognitive strategy may integrate 657.

## I-076
Affective feedback may integrate 659.

## I-077
Self capability state integrates 660.

## I-078
Learning state is separate from self identity.

## I-079
Skill identity is separate from model identity.

## I-080
Model identity is separate from SelfId.

## I-081
Tool identity is separate from SkillId.

## I-082
Experiment identity is separate from LearningRun identity.

## I-083
Improvement lineage is appendable/auditable.

## I-084
Training checkpoints are versioned.

## I-085
Learning state can be resumed from valid checkpoints.

## I-086
Invalid checkpoints cannot be silently resumed.

## I-087
Candidate training may run in isolation.

## I-088
Training resources are quota-controlled.

## I-089
Training network access is policy-controlled.

## I-090
Training filesystem access is policy-controlled.

## I-091
Training credentials are capability-controlled.

## I-092
Experiment sandboxes cannot self-expand privileges.

## I-093
Generated code is untrusted until validated.

## I-094
Generated code cannot grant itself privileges.

## I-095
Generated code cannot modify policy silently.

## I-096
Generated code cannot modify security silently.

## I-097
Model updates preserve lineage.

## I-098
Skill updates preserve lineage.

## I-099
Capability updates preserve evidence.

## I-100
Unexpected capabilities require characterization.

## I-101
Emergent behavior is not automatically registered as capability.

## I-102
Emergent capability must be evaluated.

## I-103
Capability promotion is explicit.

## I-104
Capability revocation is explicit.

## I-105
Capability revocation propagates to dependent skills.

## I-106
Skill suspension propagates to dependent plans where required.

## I-107
Learning failures are recorded.

## I-108
Improvement failures are recorded.

## I-109
Regression after deployment is observable.

## I-110
Production regression can trigger rollback according to policy.

## I-111
Canary deployment preserves old version.

## I-112
Blue/green deployment preserves rollback target.

## I-113
Improvement freeze can be triggered by incident.

## I-114
Learning can be paused.

## I-115
Learning can be terminated.

## I-116
Learning termination preserves audit state.

## I-117
Learning cannot silently resume after policy revocation.

## I-118
Risk escalation is explicit.

## I-119
High-risk improvement can require human approval.

## I-120
Evaluator disagreement is preserved.

## I-121
Evaluator identity is preserved.

## I-122
Blind evaluation cannot remove provenance.

## I-123
Statistical uncertainty is preserved.

## I-124
Small samples are marked low-evidence.

## I-125
Calibration is measured against outcomes.

## I-126
Confidence is not correctness.

## I-127
Improvement is not guaranteed by optimization.

## I-128
Optimization failure is observable.

## I-129
Improvement objective must be immutable during an experiment unless explicitly versioned.

## I-130
Objective changes create a new experiment or revision.

## I-131
Evaluation changes invalidate direct comparison unless compatible.

## I-132
Environment changes are recorded.

## I-133
Dependency changes are recorded.

## I-134
Model drift can invalidate skill evidence.

## I-135
Tool drift can invalidate skill evidence.

## I-136
Environment drift can invalidate skill evidence.

## I-137
Self-model must be notified of validated capability changes.

## I-138
Self-model cannot accept unvalidated capability changes as facts.

## I-139
Improvement cannot erase limitation evidence without validation.

## I-140
Improvement cannot erase failure history.

## I-141
Improvement cannot rewrite provenance.

## I-142
Improvement cannot forge evaluation results.

## I-143
Improvement cannot forge benchmark identity.

## I-144
Improvement cannot forge dataset lineage.

## I-145
Improvement cannot forge model lineage.

## I-146
Improvement cannot forge evaluator identity.

## I-147
Improvement cannot forge authorization.

## I-148
Improvement cannot forge deployment state.

## I-149
Improvement cannot bypass rollback.

## I-150
Improvement cannot bypass audit.

## I-151
Improvement cannot bypass privacy policy.

## I-152
Improvement cannot bypass data governance.

## I-153
Improvement cannot bypass package governance.

## I-154
Improvement cannot bypass network policy.

## I-155
Improvement cannot bypass resource quotas.

## I-156
Improvement cannot bypass real-time guarantees.

## I-157
Background learning cannot consume protected real-time resources beyond policy.

## I-158
Learning budget exhaustion is not equivalent to task impossibility.

## I-159
Partial learning is not mastery.

## I-160
Training completion is not capability validation.

## I-161
Capability validation is not authority grant.

## I-162
Authority grant remains outside 661.

## I-163
Skill composition preserves component provenance.

## I-164
Skill transfer preserves source identity.

## I-165
Transfer failure is recorded.

## I-166
Negative transfer can suspend candidate skill.

## I-167
Retention is measurable.

## I-168
Forgetting is distinguishable from invalidation.

## I-169
Skill refresh does not automatically change skill identity.

## I-170
Skill version changes preserve compatibility metadata.

## I-171
Native skill compilation preserves source lineage.

## I-172
Compiled skill artifacts can be independently verified.

## I-173
Learned heuristics cannot override language safety.

## I-174
Learned heuristics cannot override policy.

## I-175
Learned heuristics cannot override security.

## I-176
Learned tool strategies cannot bypass tool authorization.

## I-177
Learned resource strategies cannot bypass quotas.

## I-178
Self-play remains sandboxed unless explicitly authorized.

## I-179
Synthetic experience retains synthetic provenance.

## I-180
Synthetic success does not establish real-world success.

## I-181
Sim-to-real transfer requires validation.

## I-182
Online learning requires drift monitoring.

## I-183
Online learning requires rollback where configured.

## I-184
Online learning cannot silently change production objective.

## I-185
Online learning cannot silently expand permissions.

## I-186
Federated learning preserves local provenance.

## I-187
Federated aggregation does not merge identities.

## I-188
Distributed learning follows 628/635.

## I-189
Improvement artifacts are versioned.

## I-190
Improvement artifacts can be signed.

## I-191
Untrusted artifacts cannot become trusted without validation.

## I-192
Supply-chain provenance is preserved.

## I-193
External skills are sandboxed before activation where required.

## I-194
External models are evaluated before production promotion where required.

## I-195
Model compression requires evaluation.

## I-196
Quantization requires evaluation.

## I-197
Distillation requires evaluation.

## I-198
Compiler optimization requires conformance tests.

## I-199
Compiler self-improvement cannot break bootstrap invariants.

## I-200
No self-improvement mechanism has implicit authority over Axiom governance.

---

# 305. Compiler Acceptance Criteria

Compiler phải:

1. parse 661 annotations;
2. type-check learning/skill/improvement objects;
3. generate Learning IR;
4. generate Skill IR;
5. generate Improvement IR;
6. preserve lineage metadata;
7. support profile stripping;
8. enforce governed promotion;
9. distinguish candidate/active artifacts;
10. reject unauthorized self-modification;
11. support deterministic artifacts;
12. preserve native ABI;
13. support sandbox descriptors;
14. emit improvement manifests;
15. validate objective schemas;
16. validate dependency graphs;
17. detect invalid capability promotion paths;
18. maintain compatibility metadata.

---

# 306. Runtime Acceptance Criteria

Runtime phải:

1. detect capability gaps;
2. create improvement objectives;
3. establish baseline;
4. create experiments;
5. run bounded learning;
6. checkpoint;
7. evaluate;
8. detect regression;
9. create skills;
10. evaluate skills;
11. promote/demote skills;
12. detect capability candidates;
13. validate capabilities;
14. maintain lineage;
15. support transfer;
16. support simulation;
17. support online learning;
18. support rollback;
19. expose observability;
20. integrate with 660 SelfModel;
21. integrate with 603/639/647;
22. support recursive improvement guards.

---

# 307. Performance Acceptance Criteria

661 phải hỗ trợ:

```text
AXLEARN_NONE
```

với zero runtime learning overhead.

Skill runtime đã compiled phải có thể chạy mà không load toàn bộ training subsystem.

Learning workers phải resource-isolated.

---

# 308. Safety Acceptance Criteria

Phải chứng minh:

```text
No capability escalation through learning
No authority escalation through skill acquisition
No security bypass through generated code
No silent objective mutation
No silent production promotion
No silent rollback disable
No unbounded recursive improvement
```

---

# 309. AI-Agent Acceptance Criteria

Một Axiom agent có thể:

```text
1. nhận biết task cần capability nào;
2. phát hiện capability gap;
3. đề xuất cách học;
4. tạo curriculum;
5. chạy experiment;
6. đánh giá candidate;
7. phát hiện regression;
8. tạo skill;
9. validate skill;
10. promote skill nếu policy cho phép;
11. cập nhật SelfModel qua 660;
12. tiếp tục task với capability mới.
```

---

# 310. End-to-End Example

```text
Task:
    "Perform capability X"

660:
    X unavailable

661:
    detect gap

652:
    plan learning

661:
    create curriculum

648:
    create simulation

661:
    practice

646:
    evaluate

661:
    detect:
        +18% success
        +3% latency
        no safety regression

647:
    approve deployment

661:
    promote Skill-X v2

660:
    update SelfModel

652:
    retry original task

646:
    verify production outcome
```

---

# 311. Final Architecture

```text
                 ┌───────────────────────┐
                 │       660 SELF        │
                 │ capability / limits   │
                 └──────────┬────────────┘
                            │
                       Capability Gap
                            │
                            ▼
                 ┌───────────────────────┐
                 │   661 LEARNING        │
                 │   SELF-IMPROVEMENT    │
                 └──────────┬────────────┘
                            │
             ┌──────────────┼──────────────┐
             ▼              ▼              ▼
        Curriculum      Experiment      Simulation
             │              │              │
             └──────────────┼──────────────┘
                            ▼
                       Skill Formation
                            │
                            ▼
                         Evaluate
                            │
                 ┌──────────┴──────────┐
                 ▼                     ▼
              Reject                Promote
                 │                     │
                 ▼                     ▼
             Rollback             Capability
                                       │
                                       ▼
                                     660
```

---

# 312. Architecture Decision Summary

BOOTSTRAP-661 chốt 7 nguyên tắc:

### 1. Learning is not authority

Học được capability mới không có nghĩa agent có quyền sử dụng capability đó.

### 2. Improvement is evidence-based

Không có baseline/evaluation thì không được claim improvement.

### 3. Skills are first-class artifacts

Skill có identity, version, dependency, reliability, provenance và lifecycle.

### 4. Candidate is isolated

Candidate model/skill/capability không có production authority trước promotion.

### 5. Recursive improvement is bounded

Không có self-improvement vô hạn.

### 6. Governance remains external

603/639/647 vẫn là authority.

### 7. SelfModel is updated only after validated evidence

661 → evidence → 660, không phải:

```text
661 → "I am better" → 660
```

---

# 313. Completion Criteria

```text
[✓] Capability-gap detection
[✓] Improvement objectives
[✓] Baselines
[✓] Improvement hypotheses
[✓] Skills
[✓] Skill lifecycle
[✓] Skill dependencies
[✓] Skill transfer
[✓] Curriculum
[✓] Adaptive curriculum
[✓] Experiments
[✓] Sandboxing
[✓] Active learning
[✓] Online learning
[✓] Continual learning
[✓] Simulation learning
[✓] Sim-to-real boundary
[✓] Model adaptation
[✓] Distillation
[✓] Quantization
[✓] Skill compilation
[✓] Capability acquisition
[✓] Emergent capability handling
[✓] Regression
[✓] Calibration
[✓] Multi-objective optimization
[✓] Recursive improvement
[✓] Improvement budgets
[✓] Improvement lineage
[✓] Model lineage
[✓] Skill lineage
[✓] Data lineage
[✓] Rollback
[✓] Canary/blue-green integration
[✓] Security boundary
[✓] Policy boundary
[✓] Governance boundary
[✓] SelfModel integration
[✓] IR
[✓] ABI
[✓] Compiler annotations
[✓] Metadata
[✓] CLI
[✓] Profiles
[✓] 200 invariants
[✓] Compiler acceptance
[✓] Runtime acceptance
[✓] Performance acceptance
[✓] Safety acceptance
[✓] AI-agent acceptance
```

**BOOTSTRAP-661 — COMPLETE.**

---

# 314. Next Architecture Task

**BOOTSTRAP-662 — Native AI Autonomy, Goal Formation, Goal Management, Motivation Model, Initiative, Self-Directed Task Generation, Long-Horizon Autonomy, Resource-Aware Pursuit & Governed Autonomous Operation Runtime 5.0**

Trọng tâm kế tiếp sẽ là một lớp rất quan trọng sau 660–661:

```text
660 Self
   ↓
661 Learning / Improvement
   ↓
662 Autonomy
   ↓
Goal Formation
   ↓
Task Generation
   ↓
Long-Horizon Planning
   ↓
Execution
   ↓
Monitoring
   ↓
Learning
   ↓
SelfModel
```

Điểm cần khóa chặt ở 662 là **phân biệt “autonomy” với “unbounded self-directed authority”**: Axiom cần agent có khả năng tự chủ thực sự trong phạm vi được giao, nhưng goal, resource, delegation, persistence và authority vẫn phải có boundary rõ ràng.
:::