Tiếp tục với **BOOTSTRAP-662** — lớp học hỏi và thích nghi, nối từ Goal/Decision 661 với Memory, Evaluation, Model Governance và Agent Runtime.

:::writing{variant="document" id="74163" title="AXIOM BOOTSTRAP-662 — Native AI Learning, Adaptation, Reinforcement, Skill Acquisition, Continual Learning & Model Update Runtime 5.0"}
# BOOTSTRAP-662
## Native AI Learning, Adaptation, Reinforcement, Skill Acquisition, Continual Learning & Model Update Runtime 5.0

**Status:** COMPLETE  
**Layer:** Native AI Learning & Adaptation Runtime  
**Predecessor:** BOOTSTRAP-661 — Goal, Value, Motivation & Decision Policy  
**Primary dependencies:** 600–661  
**Primary consumers:** 644, 646, 647, 648, 650, 651, 652, 653, 655, 657, 660, 661  
**Target acceptance:** ≥ 2,200 architectural/specification tests

---

# 1. Mục tiêu

BOOTSTRAP-662 định nghĩa native substrate để Axiom AI có thể:

- học từ dữ liệu;
- học từ feedback;
- cập nhật model;
- học online;
- continual learning;
- reinforcement learning;
- imitation learning;
- skill acquisition;
- transfer learning;
- adaptation;
- personalization;
- calibration;
- meta-learning;
- model selection;
- model rollback;
- safe model deployment;
- phát hiện concept drift;
- chống catastrophic forgetting;
- đánh giá trước/sau update.

662 không định nghĩa một neural-network architecture cụ thể.

Nó định nghĩa **runtime contract chung cho quá trình học và thích nghi**.

---

# 2. Nguyên tắc nền tảng

## 2.1 Learning không đồng nghĩa với thay đổi production model

Một learning event có thể tạo:

```text
CandidateModel
```

nhưng chưa được activate.

Pipeline chuẩn:

```text
Observation
    ↓
Dataset / Experience
    ↓
Learning
    ↓
Candidate Model
    ↓
Validation
    ↓
Evaluation
    ↓
Safety / Policy Check
    ↓
Shadow Deployment
    ↓
Canary
    ↓
Activation
    ↓
Monitoring
    ↓
Rollback nếu cần
```

---

# 3. Learning ≠ truth

Model học từ dữ liệu không đảm bảo:

```text
learned == true
```

Axiom phải lưu:

- dataset provenance;
- assumptions;
- uncertainty;
- validation result;
- model revision;
- evaluation result.

---

# 4. Learning ≠ intelligence guarantee

Việc loss giảm không chứng minh:

- reasoning tốt hơn;
- behavior tốt hơn;
- alignment tốt hơn;
- generalization tốt hơn;
- factual correctness cao hơn.

Do đó 646 phải đánh giá độc lập.

---

# 5. Learning object model

Core objects:

```text
LearningTask
LearningSession
Dataset
DatasetVersion
Example
Experience
ExperienceBatch
Label
Feature
Target
Model
ModelRevision
ModelArtifact
Optimizer
TrainingConfig
TrainingState
Checkpoint
ValidationSet
EvaluationSet
LearningObjective
LossFunction
RewardFunction
PolicyModel
ValueModel
Skill
SkillModel
SkillVersion
Adaptation
AdaptationPolicy
UpdateProposal
UpdatePlan
UpdateResult
DriftSignal
DriftModel
CalibrationModel
ReplayBuffer
ExperienceBuffer
Curriculum
TransferMap
DistillationPlan
FineTunePlan
ContinualLearningPlan
LearningTrace
```

---

# 6. LearningTask

```axiom
struct LearningTask {
    id: LearningTaskId
    kind: LearningKind
    dataset: DatasetRef[]
    objective: LearningObjective
    model: ModelRef
    budget: Budget
    constraints: ConstraintRef[]
    evaluation: EvaluationPlan
}
```

---

# 7. Learning kinds

```axiom
enum LearningKind {
    Supervised
    Unsupervised
    SelfSupervised
    SemiSupervised
    Reinforcement
    Imitation
    PreferenceLearning
    Online
    Continual
    Transfer
    Distillation
    FineTuning
    MetaLearning
    Federated
    ActiveLearning
    Curriculum
    SkillLearning
}
```

---

# 8. Dataset

```axiom
struct Dataset {
    id: DatasetId
    version: Version
    schema: SchemaRef
    source: DatasetSource
    provenance: Provenance
    splits: DatasetSplit[]
    policy: DataPolicy
}
```

Dataset version immutable.

---

# 9. Dataset provenance

```axiom
struct DatasetSource {
    kind: DatasetSourceKind
    source_id: Id
    collected_at: Time?
    owner: IdentityId?
    license: LicenseRef?
    consent: ConsentRef?
}
```

Không được train từ data không có provenance khi provenance là required.

---

# 10. Dataset split

```text
Train
Validation
Test
Holdout
Safety
Calibration
Shadow
Adversarial
```

Production evaluation không được mặc định sử dụng training set.

---

# 11. Dataset contamination

Runtime phải detect hoặc record:

```text
train/test overlap
evaluation leakage
duplicate samples
future-data leakage
label leakage
benchmark contamination
```

---

# 12. Experience

RL và agent learning sử dụng:

```axiom
struct Experience {
    state: StateRef
    action: ActionRef
    reward: RewardValue?
    next_state: StateRef?
    done: bool
    timestamp: Time
    provenance: Provenance
}
```

---

# 13. Experience provenance

Phải phân biệt:

```text
RealWorld
Simulation
HumanFeedback
Synthetic
ModelGenerated
Imported
Replay
Counterfactual
```

Synthetic experience không được tự động xem như real-world evidence.

---

# 14. Learning objective

```axiom
struct LearningObjective {
    id: ObjectiveId
    kind: LearningObjectiveKind
    loss: LossFunction?
    reward: RewardFunction?
    constraints: ConstraintRef[]
    metrics: MetricRef[]
}
```

---

# 15. Loss function

```axiom
struct LossFunction {
    id: LossId
    revision: Version
    evaluate: FunctionRef
}
```

Loss phải versioned.

---

# 16. Reward function

```axiom
struct RewardFunction {
    id: RewardId
    revision: Version
    evaluate: FunctionRef
    provenance: Provenance
}
```

Reward là optimization signal, không phải moral truth.

---

# 17. Reward boundary

```text
reward
    ≠
objective
    ≠
policy
    ≠
authority
```

Reward hacking phải được kiểm tra bởi 646.

---

# 18. Model

```axiom
struct Model {
    id: ModelId
    architecture: ArchitectureRef
    revision: Version
    artifact: ModelArtifact
    input_schema: SchemaRef
    output_schema: SchemaRef
    capabilities: CapabilityDescriptor[]
}
```

---

# 19. Model revision

Mỗi update tạo:

```text
ModelRevision(N+1)
```

không mutate:

```text
ModelRevision(N)
```

---

# 20. Model artifact

Artifact có thể là:

```text
weights
parameters
graph
compiled kernel
lookup tables
decision rules
embeddings
hybrid model
```

---

# 21. Model format

Axiom runtime không bắt buộc neural model phải có một architecture.

Provider boundary hỗ trợ:

```text
Dense
CNN
RNN
Transformer
StateSpace
Diffusion
Graph
Tree
Linear
Kernel
Rule
Hybrid
Custom
```

---

# 22. Training configuration

```axiom
struct TrainingConfig {
    epochs: u32
    batch_size: u32
    learning_rate: f64
    optimizer: OptimizerRef
    seed: u64?
    precision: NumericPrecision
    device: ComputeDevice
    gradient_policy: GradientPolicy
}
```

---

# 23. Optimizer

```text
SGD
Adam
AdamW
RMSProp
LBFGS
Evolutionary
Bayesian
Custom
```

Optimizer là provider.

---

# 24. Training state

```axiom
struct TrainingState {
    step: u64
    epoch: u32
    loss: f64
    metrics: MetricValue[]
    learning_rate: f64
    checkpoint: CheckpointRef?
}
```

---

# 25. Checkpoint

Checkpoint phải chứa:

```text
model revision
optimizer state
scheduler state
random state
dataset revision
training configuration
step
environment metadata
```

---

# 26. Reproducibility

Có ba levels:

```text
Exact
Deterministic
Statistical
```

`Exact` yêu cầu bit-level equivalence khi platform hỗ trợ.

`Deterministic` yêu cầu cùng logical output.

`Statistical` chỉ yêu cầu cùng distribution/tolerance.

---

# 27. Learning session

```axiom
struct LearningSession {
    id: SessionId
    task: LearningTaskId
    started_at: Time
    state: LearningSessionState
    checkpoint: CheckpointRef
    trace: LearningTraceRef
}
```

---

# 28. Learning session states

```text
Created
Prepared
Running
Paused
Checkpointed
Validating
Evaluating
Completed
Failed
Cancelled
RolledBack
```

---

# 29. Online learning

Online learning nhận:

```text
observation → update
```

nhưng không được mặc định commit ngay.

Có modes:

```text
Immediate
Buffered
Shadow
Periodic
ThresholdTriggered
HumanApproved
```

---

# 30. Continual learning

Continual learning phải quản lý:

```text
new knowledge
old knowledge
model stability
forgetting
distribution shift
```

---

# 31. Catastrophic forgetting

Runtime phải hỗ trợ detection:

```axiom
ForgettingSignal {
    baseline_model
    updated_model
    benchmark_set
    regression
}
```

---

# 32. Replay buffer

```axiom
struct ReplayBuffer {
    capacity: u64
    sampling_policy: SamplingPolicy
    retention_policy: RetentionPolicy
}
```

Có thể dùng:

```text
uniform
prioritized
stratified
reservoir
recency-weighted
```

---

# 33. Experience retention

Replay data phải tuân:

- retention policy;
- privacy policy;
- deletion policy;
- provenance;
- storage budget.

---

# 34. Reinforcement learning

RL pipeline:

```text
State
 ↓
Policy
 ↓
Action
 ↓
Environment
 ↓
Observation
 ↓
Reward
 ↓
Experience
 ↓
Update
```

---

# 35. RL components

```text
Policy
ValueFunction
QFunction
RewardModel
Environment
Episode
Trajectory
ReplayBuffer
ExplorationPolicy
```

---

# 36. Exploration

```text
EpsilonGreedy
Boltzmann
UCB
Noise
ParameterNoise
IntrinsicExploration
Custom
```

Exploration phải có scope và budget.

---

# 37. Exploration safety

Exploration không được bypass:

```text
603 capability
639 policy
hard constraints
real-time constraints
```

---

# 38. Offline RL

Offline RL có:

```text
Dataset
BehaviorPolicy
TargetPolicy
DistributionSupport
```

Runtime phải detect out-of-distribution action risk.

---

# 39. Imitation learning

```axiom
ImitationLearn(
    demonstrations,
    policy
)
```

Demonstration phải có provenance.

Không phải demonstration nào cũng được coi là normative.

---

# 40. Human feedback

Feedback có loại:

```text
Approval
Rejection
Correction
Ranking
Preference
Label
Comment
Demonstration
```

---

# 41. Feedback provenance

```axiom
struct Feedback {
    source: IdentityId
    kind: FeedbackKind
    context: ContextRef
    confidence: f64?
    timestamp: Time
}
```

---

# 42. Preference learning

651/661 cung cấp preference model.

662 có thể học:

```text
choice model
ranking model
reward model
preference predictor
```

nhưng phải giữ:

```text
observed choice
inferred preference
explicit preference
```

tách biệt.

---

# 43. Active learning

Model có thể chọn sample cần label.

```axiom
SelectQuery(
    uncertainty,
    information_gain,
    cost
)
```

Không được tự động truy cập restricted data.

---

# 44. Curriculum learning

```text
easy → medium → hard
```

hoặc curriculum được learned.

Curriculum revision phải traceable.

---

# 45. Transfer learning

```axiom
TransferMap {
    source_model
    target_model
    mapped_parameters
    compatibility
    evaluation
}
```

Không được giả định source domain = target domain.

---

# 46. Distillation

```axiom
DistillationPlan {
    teacher
    student
    objective
    temperature
    validation
}
```

Teacher model không được truyền authority sang student.

---

# 47. Fine-tuning

Fine-tuning phải preserve:

```text
base_model_revision
dataset_revision
training_config
evaluation
```

---

# 48. Skill

Skill là learned executable capability.

```axiom
struct Skill {
    id: SkillId
    version: Version
    input_schema: SchemaRef
    output_schema: SchemaRef
    preconditions: Predicate[]
    policy: SkillPolicy
    model: ModelRef
    evaluation: EvaluationRef
}
```

---

# 49. Skill acquisition

Pipeline:

```text
Observe
 ↓
Learn
 ↓
Evaluate
 ↓
Package
 ↓
Validate
 ↓
Register
 ↓
Deploy
```

---

# 50. Skill != authority

Một learned skill không tự có quyền sử dụng resource.

Execution vẫn phải đi qua 603/639.

---

# 51. Skill versioning

Skill update tạo:

```text
SkillRevision(N+1)
```

Có rollback.

---

# 52. Skill composition

Skills có thể compose:

```text
SkillA → SkillB → SkillC
```

Compiler/runtime phải validate:

- schema compatibility;
- preconditions;
- permissions;
- resource budget;
- latency.

---

# 53. Adaptation

```axiom
struct Adaptation {
    id: AdaptationId
    trigger: AdaptationTrigger
    target: ModelRef
    strategy: AdaptationStrategy
    budget: Budget
    validation: EvaluationPlan
}
```

---

# 54. Adaptation triggers

```text
PerformanceDrop
ConceptDrift
EnvironmentChange
UserPreferenceChange
ResourceChange
PolicyChange
ModelDegradation
Scheduled
Manual
```

---

# 55. Concept drift

```axiom
struct DriftSignal {
    metric: MetricId
    baseline: Distribution
    current: Distribution
    distance: f64
    confidence: f64
}
```

Supported detectors:

```text
PSI
KL
JS
Wasserstein
KS
PageHinkley
ADWIN
Custom
```

---

# 56. Drift ≠ degradation

Distribution change không nhất thiết nghĩa model xấu đi.

Phải đánh giá:

```text
drift
+
performance
```

separately.

---

# 57. Model update proposal

```axiom
struct UpdateProposal {
    base_model: ModelRevision
    candidate_model: ModelRevision
    reason: UpdateReason
    evidence: EvidenceRef[]
    expected_change: MetricDelta[]
    risk: RiskEstimate
}
```

---

# 58. Update plan

```axiom
struct UpdatePlan {
    proposal: UpdateProposal
    validation: ValidationPlan
    shadow: ShadowPlan?
    canary: CanaryPlan?
    approval: ApprovalPolicy
    rollback: RollbackPlan
}
```

---

# 59. Model promotion pipeline

```text
Candidate
 ↓
Static validation
 ↓
Offline evaluation
 ↓
Safety evaluation
 ↓
Regression evaluation
 ↓
Shadow
 ↓
Canary
 ↓
Production
```

---

# 60. Shadow deployment

Candidate nhận input production nhưng:

```text
cannot affect production action
```

trừ khi explicitly sandboxed.

---

# 61. Canary deployment

Canary chỉ được nhận bounded traffic:

```text
percentage
tenant
region
device
task type
```

với rollback threshold.

---

# 62. Rollback

Rollback trigger:

```text
regression
error spike
constraint violation
latency violation
resource violation
drift
policy violation
```

---

# 63. Model governance

647 quản lý:

```text
model registry
model approval
model lineage
model deployment
model retirement
model rollback
```

---

# 64. Model lineage

Phải biết:

```text
model
 ← parent model
 ← dataset
 ← preprocessing
 ← training config
 ← optimizer
 ← evaluation
 ← deployment
```

---

# 65. Model card metadata

Axiom model artifact có thể chứa:

```text
purpose
limitations
training_data
evaluation
known_failures
resource_profile
privacy
license
revision
```

---

# 66. Calibration

Model phải hỗ trợ calibration:

```text
confidence
probability
uncertainty
prediction interval
```

662 không cho phép:

```text
confidence = truth
```

---

# 67. Calibration update

Calibration model có revision riêng:

```text
ModelRevision
CalibrationRevision
```

Một model có thể giữ weights nhưng thay calibration.

---

# 68. Model ensemble

Hỗ trợ:

```text
Voting
Weighted
Stacking
Mixture
Routing
Specialist
```

---

# 69. Model routing

Router có thể chọn model dựa trên:

```text
input
latency
quality
cost
device
privacy
capability
confidence
```

Nhưng routing phải chịu 639/603.

---

# 70. Model selection

661 objective có thể chọn:

```text
quality
latency
cost
memory
energy
privacy
```

662 cung cấp model candidates.

---

# 71. Meta-learning

662 hỗ trợ:

```text
LearnToLearn
AdaptationPolicy
FewStepAdaptation
HyperparameterOptimization
```

Meta-learning không được tự sửa policy authority.

---

# 72. Hyperparameter optimization

Supported strategies:

```text
Grid
Random
Bayesian
Evolutionary
PopulationBased
```

Budget bắt buộc.

---

# 73. Learning budget

Mọi learning task phải có:

```text
compute
memory
storage
time
energy
network
financial_cost
```

budget nếu applicable.

---

# 74. Resource governor

606 có authority.

Learning không được tự:

```text
increase GPU budget
increase memory limit
disable quota
```

---

# 75. Privacy-preserving learning

Provider boundary hỗ trợ:

```text
DifferentialPrivacy
FederatedLearning
SecureAggregation
LocalLearning
DataMinimization
```

---

# 76. Federated learning

Node gửi:

```text
update
gradient
delta
statistics
```

thay vì raw data khi policy yêu cầu.

---

# 77. Federated aggregation

Có thể:

```text
FedAvg
FedProx
SecureAggregation
RobustAggregation
Custom
```

---

# 78. Byzantine robustness

Distributed learning có thể hỗ trợ:

```text
trimmed_mean
median
Krum
robust_aggregation
```

nhưng provider-specific.

---

# 79. Model poisoning

662 phải expose detector:

```text
UpdateAnomaly
GradientAnomaly
DataAnomaly
BehaviorAnomaly
```

---

# 80. Backdoor detection

Evaluation có thể kiểm tra:

```text
trigger sensitivity
behavioral anomaly
distribution shift
hidden behavior
```

---

# 81. Adversarial evaluation

646 có thể yêu cầu:

```text
adversarial dataset
perturbation test
distribution shift
worst-case test
counterfactual test
```

---

# 82. Learning trace

```axiom
struct LearningTrace {
    task
    dataset
    model_before
    model_after
    config
    metrics
    checkpoints
    evaluation
    deployment
    rollback
}
```

---

# 83. Learning explainability

Runtime phải trả lời:

```text
what changed?
why changed?
which data?
which objective?
which revision?
what evidence?
what evaluation?
```

Không yêu cầu expose hidden chain-of-thought.

---

# 84. Continual learning memory

650 cung cấp:

```text
episodic experience
semantic knowledge
long-term memory
```

662 sử dụng chúng như learning source.

Memory write phải tuân retention policy.

---

# 85. Learning from memory

Không phải toàn bộ memory đều trainable.

Mỗi memory item cần:

```text
learnable
non_learnable
restricted
expired
```

metadata.

---

# 86. Learning and personalization

651 có thể yêu cầu:

```text
user-specific adaptation
```

Nhưng:

```text
personalization
!=
global model update
```

---

# 87. User model isolation

User-specific learning phải hỗ trợ:

```text
local adapter
user profile
tenant adapter
private model
shared model
```

và explicit isolation.

---

# 88. Model contamination prevention

Private user data không được đưa vào global model nếu policy không cho phép.

---

# 89. Learning from interaction

Interaction loop:

```text
observe
→ predict
→ act
→ receive feedback
→ evaluate
→ update candidate
→ validate
→ optionally deploy
```

---

# 90. Safe online adaptation

Online adaptation phải hỗ trợ:

```text
shadow
bounded update
rate limit
rollback
freeze
manual approval
```

---

# 91. Model freeze

```axiom
@model(frozen=true)
```

cấm update runtime.

---

# 92. Learning freeze

System-wide:

```axiom
learning.freeze(scope)
```

được điều khiển bởi governance.

---

# 93. Emergency rollback

Emergency rollback phải:

```text
atomic
auditable
policy-authorized
fast
```

---

# 94. Axiom annotations

```text
@learn
@learning_task
@dataset
@dataset_version
@experience
@experience_buffer
@train
@validate
@test
@evaluate
@model
@model_revision
@checkpoint
@online_learning
@continual_learning
@reinforcement
@reward
@reward_model
@imitation
@preference_learning
@active_learning
@curriculum
@transfer
@distill
@fine_tune
@meta_learning
@skill
@skill_version
@skill_learn
@adapt
@drift
@calibrate
@model_update
@model_shadow
@model_canary
@model_promote
@model_rollback
@learning_budget
@learning_trace
@model_governance
@federated
@privacy_learning
```

---

# 95. Metadata artifacts

```text
.axlearn
.axdataset
.axexperience
.axtrain
.axcheckpoint
.axmodel
.axmodelrev
.axeval
.axcalibration
.axreward
.axpolicy
.axskill
.axskillrev
.axadapt
.axdrift
.axupdate
.axshadow
.axcanary
.axlearningtrace
.axmodelcard
```

---

# 96. IR

```text
LearningTaskCreate
LearningTaskPrepare
DatasetOpen
DatasetSplit
DatasetValidate

ExperienceRecord
ExperienceBatch
ReplaySample

ModelLoad
ModelCheckpoint
ModelRestore
ModelEvaluate

TrainForward
TrainBackward
OptimizerStep
GradientClip

RewardEvaluate
PolicyEvaluate
ValueEvaluate

Explore
Observe
ExperienceStore

PreferenceLearn
ImitationLearn

DriftDetect
CalibrationEvaluate

SkillCreate
SkillValidate
SkillRegister

AdaptationPropose
AdaptationValidate

UpdatePropose
UpdateShadow
UpdateCanary
UpdatePromote
UpdateRollback

LearningTrace
LearningExplain
```

---

# 97. IR safety rules

Compiler/runtime không được:

```text
Optimize away policy check
Remove provenance
Merge incompatible dataset revisions
Ignore model revision
Promote shadow model automatically
Bypass rollback
```

---

# 98. Profiles

```text
AXLEARN_NONE
AXLEARN_CORE
AXLEARN_SUPERVISED
AXLEARN_SELF_SUPERVISED
AXLEARN_UNSUPERVISED
AXLEARN_REINFORCEMENT
AXLEARN_IMITATION
AXLEARN_PREFERENCE
AXLEARN_ONLINE
AXLEARN_CONTINUAL
AXLEARN_TRANSFER
AXLEARN_DISTILL
AXLEARN_FINETUNE
AXLEARN_META
AXLEARN_ACTIVE
AXLEARN_CURRICULUM

AXSKILL_CORE
AXSKILL_LEARNING
AXADAPT_CORE
AXDRIFT
AXCALIBRATION

AXMODEL_CORE
AXMODEL_VERSIONING
AXMODEL_SHADOW
AXMODEL_CANARY
AXMODEL_ROLLBACK
AXMODEL_GOVERNANCE

AXFEDERATED
AXPRIVACY_LEARNING
AXDISTRIBUTED

AXLEARN_REALTIME
AXLEARN_GPU
AXLEARN_SIMULATION
AXLEARN_AGENT

AXLEARN_FULL
```

---

# 99. CLI

```text
axiom learn inspect
axiom learn create
axiom learn start
axiom learn pause
axiom learn resume
axiom learn cancel
axiom learn checkpoint
axiom learn restore
axiom learn evaluate
axiom learn trace
axiom learn explain

axiom dataset inspect
axiom dataset validate
axiom dataset split
axiom dataset lineage

axiom experience inspect
axiom experience replay
axiom experience purge

axiom model inspect
axiom model compare
axiom model evaluate
axiom model lineage
axiom model validate
axiom model shadow
axiom model canary
axiom model promote
axiom model rollback

axiom skill inspect
axiom skill validate
axiom skill register
axiom skill rollback

axiom drift inspect
axiom drift detect

axiom calibration inspect
axiom calibration evaluate

axiom learning benchmark
axiom learning regression
```

---

# 100. Learning invariants

1. Dataset phải versioned.
2. Model phải versioned.
3. Learning task phải có objective.
4. Learning task phải có budget.
5. Training config phải trace.
6. Dataset provenance phải preserve.
7. Dataset contamination phải detect hoặc flag.
8. Test data không được dùng để train khi test isolation yêu cầu.
9. Validation data không được mutate bởi training.
10. Model revision không được silent mutate.
11. Checkpoint phải pin model revision.
12. Checkpoint phải pin dataset revision.
13. Checkpoint phải pin optimizer state.
14. Reproducibility mode phải explicit.
15. Random seed phải preserve khi deterministic.
16. Learning result phải có metrics.
17. Metrics phải versioned.
18. Loss giảm không chứng minh task success.
19. Reward tăng không chứng minh real-world success.
20. Model update phải evaluation trước production.

---

# 101. Continual-learning invariants

21. Continual update phải có baseline.
22. Baseline phải immutable.
23. Regression phải detectable.
24. Catastrophic forgetting phải measurable.
25. Replay buffer phải policy-controlled.
26. Memory retention phải explicit.
27. New data không được tự xóa old knowledge.
28. Old knowledge regression phải tracked.
29. Model update phải rollbackable.
30. Online learning không mặc định production commit.
31. Drift không tự đồng nghĩa degradation.
32. Drift signal phải confidence-tagged.
33. Adaptation phải có trigger.
34. Adaptation phải có budget.
35. Adaptation phải có evaluation.
36. Adaptation không được bypass governance.
37. Model freeze phải enforceable.
38. Learning freeze phải enforceable.
39. Update rate phải bounded.
40. Continual model phải có lineage.

---

# 102. RL invariants

41. Reward phải versioned.
42. Reward provenance phải preserved.
43. Reward không phải moral truth.
44. Reward không cấp authority.
45. Exploration phải bounded.
46. Exploration không bypass security.
47. Action phải capability-checked.
48. Action phải policy-checked.
49. Offline RL phải track behavior policy.
50. OOD actions phải detectable.
51. Simulation experience phải tagged.
52. Synthetic experience không tự thành real evidence.
53. Counterfactual experience phải tagged.
54. Replay buffer phải retention-aware.
55. Reward hacking phải evaluable.
56. Reward model phải independently evaluable.
57. Policy update phải versioned.
58. Value model phải versioned.
59. Environment revision phải trace.
60. Episode provenance phải preserved.

---

# 103. Skill invariants

61. Skill phải có input schema.
62. Skill phải có output schema.
63. Skill phải có preconditions.
64. Skill phải có evaluation.
65. Skill phải có version.
66. Skill không cấp authority.
67. Skill không bypass policy.
68. Skill dependency phải versioned.
69. Skill composition phải validate.
70. Skill rollback phải atomic.
71. Skill update phải preserve provenance.
72. Learned skill phải distinguishable from built-in skill.
73. Skill confidence phải distinguishable from capability.
74. Skill registration phải governance-aware.
75. Unvalidated skill không được production activate.

---

# 104. Model-update invariants

76. Candidate model không được production activate trước evaluation.
77. Shadow model không có production authority.
78. Canary phải bounded.
79. Canary phải rollbackable.
80. Promotion phải policy-controlled.
81. Rollback phải atomic.
82. Model lineage phải complete.
83. Model artifact phải immutable theo revision.
84. Model metadata phải preserved.
85. Model capability declaration phải verifiable.
86. Model deployment phải pin revision.
87. Model router phải respect policy.
88. Model selection không tự cấp capability.
89. Model replacement phải auditable.
90. Emergency rollback phải auditable.

---

# 105. Privacy invariants

91. Dataset consent phải preserve.
92. Private dataset phải access-controlled.
93. Private data không tự trở thành global training data.
94. User-specific adaptation phải isolated khi required.
95. Replay buffer phải respect deletion.
96. Model lineage phải identify sensitive training sources khi policy yêu cầu.
97. Federated aggregation không được expose raw data nếu contract cấm.
98. Preference-derived training phải scope-aware.
99. Feedback provenance phải preserve.
100. Data retention phải enforceable.

---

# 106. Governance invariants

101. 647 controls model lifecycle.
102. 646 evaluates model quality.
103. 639 controls normative policy.
104. 603 controls capability access.
105. 606 controls resource budgets.
106. 650 controls memory persistence.
107. 651 controls personalization scope.
108. 661 controls objective/decision semantics.
109. 660 controls self-model claims.
110. Learning cannot override any authoritative layer.
111. Self-learning cannot mint authority.
112. Self-training cannot disable governance.
113. Self-update cannot silently rewrite policy.
114. Candidate model cannot grant itself capabilities.
115. Learned behavior cannot redefine security boundary.

---

# 107. Anti-gaming invariants

116. Benchmark score is not sufficient for promotion.
117. Training metric is not sufficient for promotion.
118. Reward score is not sufficient for promotion.
119. Self-evaluation is not sufficient for promotion.
120. Model must pass independent evaluation when required.
121. Proxy optimization must be distinguishable.
122. Evaluation contamination must be detectable.
123. Test-set memorization must be detectable where applicable.
124. Distribution shift must be monitored.
125. Hidden regression must block promotion when policy says so.
126. Confidence inflation must be detectable.
127. Calibration degradation must be measurable.
128. Model behavior changes must be diffable.
129. Update reason must be recorded.
130. Update evidence must be recorded.

---

# 108. Agent-learning invariants

131. Agent observation is not automatically training truth.
132. Agent memory is not automatically training data.
133. Tool output is not automatically ground truth.
134. User correction must preserve provenance.
135. Inferred preference is not explicit instruction.
136. Agent-generated data must be tagged.
137. Agent-generated labels must be tagged.
138. Self-generated curriculum must be bounded.
139. Self-generated model update requires policy.
140. Self-generated skill requires validation.
141. Agent cannot silently modify its production policy.
142. Agent cannot silently modify security policy.
143. Agent cannot silently modify authority.
144. Agent cannot declare itself validated.
145. Agent cannot suppress failed evaluations.

---

# 109. Distributed-learning invariants

146. Dataset shards must have provenance.
147. Model aggregation must be versioned.
148. Federated round must have identity.
149. Aggregation algorithm must be pinned.
150. Aggregation result must be reproducible when required.
151. Byzantine detection must be explicit when used.
152. Node updates must be traceable.
153. Stale updates must be detectable.
154. Conflicting model revisions must be detectable.
155. Rollback must be coordinated.
156. Privacy budget must be tracked.
157. Secure aggregation status must be observable.
158. Network failure must not corrupt model revision.
159. Duplicate updates must be idempotent where required.
160. Governance applies to distributed model activation.

---

# 110. Real-time invariants

161. Learning deadline must be bounded.
162. Online update cannot block hard realtime execution.
163. Training must run off critical control path unless explicitly designed otherwise.
164. Fallback model must be available when required.
165. Model swap must be atomic.
166. Memory budget must be enforced.
167. GPU budget must be enforced.
168. CPU budget must be enforced.
169. Learning scheduler must respect 607.
170. Resource governor 606 remains authoritative.

---

# 111. Explainability invariants

171. Learning trace must expose model revision.
172. Learning trace must expose dataset revision.
173. Learning trace must expose objective.
174. Learning trace must expose evaluation.
175. Learning trace must expose promotion state.
176. Learning trace must expose rollback state.
177. Explanation must not fabricate causal certainty.
178. Correlation must not be presented as causation.
179. Model-generated explanation must be marked as such.
180. Hidden chain-of-thought must not be required for learning audit.

---

# 112. Compiler invariants

181. Compiler must reject incompatible schemas.
182. Compiler must preserve model revision references.
183. Compiler must preserve dataset references.
184. Compiler must preserve policy checks.
185. Compiler must preserve capability checks.
186. Compiler may optimize tensor operations without semantic change.
187. Compiler may fuse compatible kernels.
188. Compiler may constant-fold static preprocessing.
189. Compiler may eliminate unused learning components.
190. Compiler must not eliminate required provenance.

---

# 113. Runtime performance

Hot paths phải hỗ trợ:

```text
zero-copy tensors
memory pools
batch execution
SIMD
GPU kernels
asynchronous data loading
pinned memory
streaming datasets
checkpoint compression
incremental checkpoint
```

---

# 114. CPU-first principle

Axiom learning runtime phải chạy được trên CPU.

GPU là acceleration provider:

```text
CPU baseline
   ↓
SIMD
   ↓
GPU
   ↓
Distributed
```

Không ép application phải phụ thuộc GPU runtime.

---

# 115. Native artifact model

Model có thể được đóng gói thành:

```text
.axmodel
```

bao gồm:

```text
header
schema
architecture
weights
metadata
revision
provenance
evaluation
capability descriptor
```

---

# 116. Compiled model

Model có thể được AOT compile thành native artifact:

```text
.axbin
```

hoặc embed trực tiếp vào executable.

Compiler có thể specialize:

```text
input shape
precision
target CPU
target GPU
batch size
```

---

# 117. Model specialization

Ví dụ:

```text
generic model
    ↓
x86-64 AVX2
    ↓
ARM64 NEON
    ↓
CUDA
    ↓
WASM SIMD
```

Semantics phải giữ tương đương trong tolerance được khai báo.

---

# 118. Quantization

Provider support:

```text
FP32
BF16
FP16
FP8
INT8
INT4
Binary
Custom
```

Quantization phải có calibration/evaluation.

---

# 119. Compression

Model artifact có thể dùng:

```text
sparse weights
weight sharing
pruning
quantization
distillation
delta encoding
```

nhưng phải preserve model revision semantics.

---

# 120. Learning cache

Compiler/runtime được phép cache:

```text
dataset preprocessing
compiled kernels
embeddings
feature extraction
checkpoints
model artifacts
```

Cache key phải chứa tất cả semantic inputs.

---

# 121. Cache correctness

Cache không được reuse nếu thay đổi:

```text
dataset revision
preprocessor revision
model architecture
compiler target
training config
optimizer
objective
```

khi chúng ảnh hưởng kết quả.

---

# 122. Model artifact dependency graph

```text
Model
 ├── Architecture
 ├── Dataset
 ├── Preprocessor
 ├── TrainingConfig
 ├── Optimizer
 ├── Objective
 ├── Evaluation
 └── CompilerTarget
```

---

# 123. Model deployment states

```text
Draft
Candidate
Validated
Shadow
Canary
Active
Deprecated
Retired
RolledBack
Rejected
```

---

# 124. Model registry

```axiom
model_registry.list()
model_registry.inspect()
model_registry.compare()
model_registry.activate()
model_registry.rollback()
```

Registry thuộc 647.

---

# 125. Learning event stream

662 có thể emit:

```text
LearningStarted
CheckpointCreated
EvaluationCompleted
DriftDetected
UpdateProposed
ShadowStarted
CanaryStarted
ModelPromoted
ModelRolledBack
LearningFailed
```

634/633 có thể transport/observe.

---

# 126. Model-health monitor

Theo dõi:

```text
accuracy
loss
latency
throughput
memory
CPU
GPU
energy
drift
calibration
error rate
safety violations
```

---

# 127. Learning health state

```text
Healthy
Degraded
Drifting
Uncalibrated
Regressing
Unsafe
Frozen
Updating
Unknown
```

`Unknown` phải khác `Healthy`.

---

# 128. Learning scheduler

607 điều phối:

```text
training jobs
evaluation jobs
checkpoint jobs
adaptation jobs
model deployment
rollback
```

Có priority và quota.

---

# 129. Goal integration

661 có thể yêu cầu:

```text
learn skill X
improve metric Y
reduce latency Z
```

662 biến thành LearningTask.

Nhưng 662 không được tự thay đổi goal.

---

# 130. Self-model integration

660 có thể nhận:

```text
new capability
new limitation
model revision
skill revision
calibration result
```

SelfModel update phải phản ánh model thật đang active.

---

# 131. Metacognitive learning loop

```text
predict capability
      ↓
act
      ↓
observe result
      ↓
compare prediction
      ↓
detect error
      ↓
propose learning
      ↓
train candidate
      ↓
evaluate
      ↓
update capability model
```

---

# 132. Learning-to-decision loop

```text
661 objective
    ↓
662 learning
    ↓
candidate model
    ↓
646 evaluation
    ↓
647 governance
    ↓
new model
    ↓
661 decision policy
```

---

# 133. No implicit self-improvement

Axiom không định nghĩa:

```text
"AI should improve itself"
```

như một default objective.

Self-improvement chỉ xảy ra khi một authorized learning objective tồn tại.

---

# 134. Model self-modification boundary

```text
SelfGeneratedLearning
    ↓
Policy check
    ↓
Candidate
    ↓
Evaluation
    ↓
Approval
    ↓
Activation
```

Không:

```text
SelfGeneratedLearning
    ↓
Production
```

---

# 135. Learning simulation

648 có thể chạy:

```text
train in simulation
test in simulation
evaluate counterfactual model
```

Simulation result phải tagged.

---

# 136. Sim-to-real

Nếu deploy simulation-trained model:

```text
simulation validation
+
domain-gap evaluation
+
real-world bounded validation
```

phải được hỗ trợ.

---

# 137. Model uncertainty

Model output nên hỗ trợ:

```text
prediction
confidence
uncertainty
out_of_distribution
```

khi architecture cho phép.

---

# 138. Abstention

Model có thể trả:

```text
Abstain
```

khi:

```text
confidence < threshold
OOD
policy restriction
insufficient data
deadline exceeded
```

---

# 139. Abstention policy

661 quyết định hậu quả của abstention.

Ví dụ:

```text
fallback model
ask user
request more data
safe default
defer
```

---

# 140. Learning failure handling

Failure categories:

```text
DataError
SchemaError
ResourceError
OptimizationFailure
EvaluationFailure
PolicyFailure
SecurityFailure
DriftFailure
DeploymentFailure
RollbackFailure
```

---

# 141. Atomic model activation

Activation phải là atomic pointer/version switch:

```text
active = ModelRevision(N)
```

→

```text
active = ModelRevision(N+1)
```

Không để state nửa cũ/nửa mới.

---

# 142. Concurrent model updates

Nếu hai update cùng dựa trên:

```text
ModelRevision(10)
```

thì cả hai phải được distinguish.

Không silent overwrite.

---

# 143. Update merge

Model update merge chỉ được hỗ trợ nếu architecture/provider định nghĩa semantic merge.

Không mặc định merge arbitrary weights.

---

# 144. Learning transaction

Learning transaction:

```text
Begin
Prepare
Train
Validate
Evaluate
Stage
Commit
Rollback
```

---

# 145. Commit contract

Commit chỉ khi:

```text
policy == allow
evaluation == pass
artifact == valid
revision == consistent
```

---

# 146. Model rollback contract

Rollback phải restore:

```text
model
routing
calibration
metadata
deployment state
```

theo policy.

---

# 147. Benchmark contract

Benchmark phải lưu:

```text
benchmark revision
dataset revision
metric revision
hardware
software
model revision
```

---

# 148. Learning benchmark

CLI:

```text
axiom learning benchmark
```

phải report:

```text
throughput
latency
memory
training time
quality
regression
energy
```

nếu metrics available.

---

# 149. Zero-cost unused feature

Nếu chương trình không sử dụng learning:

```text
662 runtime
training scheduler
optimizer
dataset engine
```

không được link vào executable.

---

# 150. Native dependency rule

Core learning ABI không bắt buộc:

```text
Python
PyTorch
TensorFlow
ONNX Runtime
CUDA
```

Một provider có thể dùng chúng bên ngoài, nhưng Axiom core phải có provider-independent ABI.

---

# 151. Provider boundary

```axiom
trait LearningProvider {
    train(...)
    evaluate(...)
    checkpoint(...)
    restore(...)
    update(...)
}
```

Provider có thể là:

```text
AxiomNativeCPU
AxiomNativeGPU
ExternalProvider
RemoteProvider
```

---

# 152. ABI stability

Learning ABI phải version:

```text
AX_LEARN_ABI_1
AX_LEARN_ABI_2
```

Provider mismatch phải reject rõ ràng.

---

# 153. Native tensor boundary

Tensor API phải hỗ trợ:

```text
shape
stride
dtype
device
layout
alignment
ownership
lifetime
```

Không yêu cầu Python object model.

---

# 154. Zero-copy boundary

Nếu provider hỗ trợ:

```text
CPU tensor → GPU
GPU tensor → kernel
model → inference
```

thì runtime ưu tiên zero-copy/borrowed buffer theo ownership contract.

---

# 155. Ownership safety

Learning buffer phải có:

```text
owner
borrow
lifetime
device
synchronization state
```

nhưng không kéo borrow checker vào language core.

Đây là runtime/ABI contract.

---

# 156. Error model

662 dùng structured error:

```text
LearningError {
    code
    phase
    model
    dataset
    revision
    recoverable
    retryable
}
```

---

# 157. Diagnostics

Compiler/runtime errors:

```text
AX662001 Dataset revision missing
AX662002 Model revision missing
AX662003 Training budget exceeded
AX662004 Evaluation set contaminated
AX662005 Candidate regression detected
AX662006 Model promotion unauthorized
AX662007 Shadow model attempted side effect
AX662008 Skill validation failed
AX662009 Drift confidence insufficient
AX662010 Rollback revision unavailable
AX662011 Privacy policy violation
AX662012 Learning provider ABI mismatch
AX662013 Checkpoint incompatible
AX662014 Determinism contract violated
AX662015 Candidate model lacks provenance
```

---

# 158. Security boundary

Learning runtime phải coi model artifact là untrusted input khi artifact đến từ bên ngoài.

Model loader phải kiểm tra:

- format;
- signature;
- provenance;
- architecture;
- resource claims;
- executable code;
- embedded kernels.

---

# 159. Executable model code

Native compiled model kernels phải chịu:

```text
603 capability policy
647 supply-chain governance
```

Không được execute arbitrary embedded code chỉ vì file mang `.axmodel`.

---

# 160. Model signing

Model deployment có thể yêu cầu:

```text
signature
certificate
trust root
revision
publisher
```

---

# 161. Supply-chain security

Model lineage phải support:

```text
publisher
source
hash
signature
dependencies
build environment
compiler revision
```

---

# 162. Deterministic artifact hashing

Model artifact hash phải tính trên canonical representation.

---

# 163. Dataset hash

Dataset version nên có:

```text
content hash
schema hash
preprocessing hash
provenance hash
```

---

# 164. Reproducible learning package

Có thể đóng gói:

```text
.axlearnpkg
```

gồm:

```text
dataset manifest
model
training config
optimizer
code revision
compiler revision
evaluation
provenance
```

---

# 165. Learning package portability

Package phải có capability requirements:

```text
CPU
RAM
GPU
VRAM
instruction set
OS
ABI
```

---

# 166. Edge learning

662 hỗ trợ:

```text
device-local learning
intermittent connectivity
offline adaptation
sync later
```

---

# 167. Mobile learning

iOS/Android:

```text
battery budget
thermal budget
memory budget
background execution policy
```

phải được tôn trọng.

---

# 168. WASM learning

WASM provider hỗ trợ:

```text
CPU inference
limited training
sandboxed adaptation
```

tùy target.

---

# 169. Learning on embedded devices

Có thể disable:

```text
training
online update
persistent replay
```

bằng compile-time profile.

---

# 170. AI-friendly source representation

Learning declarations phải machine-readable.

Ví dụ:

```axiom
@learn(
    kind = continual,
    target = SpeechModel,
    objective = Naturalness,
    budget = 30m
)
task ImproveSpeechModel {
    data = RecentVietnameseAudio
}
```

---

# 171. Semantic metadata

Compiler phải emit:

```text
learning task ID
objective ID
dataset ID
model ID
revision
constraints
budget
```

để AI agent có thể inspect.

---

# 172. AI agent interface

644 có thể:

```text
learn.inspect(task)
learn.propose_update(model)
learn.evaluate(candidate)
learn.rollback(model)
```

nhưng authority vẫn thuộc 647/639/603.

---

# 173. Learning planner

652 có thể lập kế hoạch:

```text
collect data
train
evaluate
distill
quantize
deploy
```

662 thực thi learning substrate.

---

# 174. Learning + decision

661 có thể tối ưu:

```text
model quality
training cost
adaptation latency
risk
```

662 cung cấp measurements.

---

# 175. Learning + affect

659 có thể cung cấp affective data cho model training.

Nhưng dataset phải preserve:

```text
observed affect
inferred affect
synthetic affect
```

không trộn chúng thành ground truth.

---

# 176. Learning + social intelligence

658 có thể cung cấp interaction data.

Phải preserve:

```text
agent identity
human identity scope
context
consent
privacy
```

---

# 177. Learning + consciousness boundary

660 có thể học self-model.

Nhưng:

```text
self-model update
≠
consciousness
```

Learning runtime không được tuyên bố rằng model đã trở nên conscious chỉ vì self-model trở nên phức tạp hơn.

---

# 178. Learning + value

661 value/objective có thể xác định:

```text
what to optimize
```

662 xác định:

```text
how model changes
```

Hai layer phải tách biệt.

---

# 179. Model objective separation

Ví dụ:

```text
661:
    objective = reduce latency

662:
    learning objective = distillation loss
```

Distillation loss không được tự thay đổi system objective.

---

# 180. Learning governance state machine

```text
Proposed
   ↓
Validated
   ↓
Approved
   ↓
Training
   ↓
Evaluated
   ↓
Shadow
   ↓
Canary
   ↓
Active
   ↓
Deprecated
   ↓
Retired
```

Các nhánh:

```text
Rejected
Failed
RolledBack
```

---

# 181. Required test families

Axiom phải có test suites:

```text
dataset
schema
training
checkpoint
reproducibility
RL
online learning
continual learning
drift
skill learning
model update
shadow
canary
rollback
privacy
security
governance
distributed
GPU
CPU
WASM
mobile
```

---

# 182. Acceptance test matrix

Tối thiểu:

```text
Core learning                  150
Dataset/provenance             150
Supervised                     100
Self-supervised                100
RL                             180
Continual                      180
Online                         120
Skill                          120
Adaptation                     120
Model lifecycle                180
Governance                     150
Privacy                        120
Security                       120
Distributed                    120
Performance                    100
Compiler/IR                    150
```

Tổng target:

```text
>= 2,000
```

---

# 183. Final architectural contract

662 phải đảm bảo:

```text
Learning
    is a controlled state transition
```

không phải:

```text
Learning
    = unrestricted self-modification
```

---

# 184. Final architecture

```text
             655 World Model
                   │
             650 Memory
                   │
        ┌──────────┴──────────┐
        │                     │
      660                   661
 Self/Metacognition     Goals/Decision
        │                     │
        └──────────┬──────────┘
                   ▼
                  662
          Learning & Adaptation
                   │
        ┌──────────┼──────────┐
        ▼          ▼          ▼
      Model      Skill      Policy
        │          │          │
        └──────────┼──────────┘
                   ▼
                 646
              Evaluation
                   │
                 647
              Governance
                   │
            ┌──────┴──────┐
            ▼             ▼
         Shadow         Canary
            │             │
            └──────┬──────┘
                   ▼
                Active
                   │
                 644
             Agent Runtime
```

---

# 185. Architectural principle

Axiom 662 phải cho phép hệ thống:

> **học nhanh, thích nghi liên tục, nhưng không tự ý thay đổi chính sách, quyền hạn, mục tiêu cấp cao hoặc security boundary.**

Learning là capability.

Adaptation là controlled state transition.

Model update là governed deployment.

Skill acquisition là versioned capability.

Không khái niệm nào trong số đó tự động tạo authority, consciousness, moral status hoặc subjective desire.

**BOOTSTRAP-662 — COMPLETE.**
:::

Task tiếp theo: **BOOTSTRAP-663 — Native AI Evaluation, Benchmarking, Verification, Validation, Red-Team, Safety Testing & Model Assurance Runtime 5.0**.