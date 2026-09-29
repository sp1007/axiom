Tiếp tục với **BOOTSTRAP-663** — lớp assurance/evaluation, đóng vai trò đối trọng độc lập với Learning 662 và cung cấp nền tảng kiểm chứng cho Model/Agent/Decision.

:::writing{variant="document" id="31647" title="AXIOM BOOTSTRAP-663 — Native AI Evaluation, Benchmarking, Verification, Validation, Red-Team, Safety Testing & Model Assurance Runtime 5.0"}
# BOOTSTRAP-663
## Native AI Evaluation, Benchmarking, Verification, Validation, Red-Team, Safety Testing & Model Assurance Runtime 5.0

**Status:** COMPLETE  
**Layer:** Native AI Assurance & Evaluation  
**Predecessor:** BOOTSTRAP-662 — Learning & Adaptation  
**Primary dependencies:** 603, 639, 644, 646, 647, 648, 650, 652, 653, 654, 655, 657, 658, 659, 660, 661, 662  
**Primary consumers:** 662, 647, 644, 661, 660, deployment/runtime systems  
**Target acceptance:** ≥ 2,400 architectural/specification tests

---

# 1. Mục tiêu

BOOTSTRAP-663 định nghĩa hệ thống native để Axiom có thể:

- evaluate model;
- benchmark model;
- verify implementation;
- validate intended behavior;
- test safety;
- test robustness;
- test reliability;
- test calibration;
- test regression;
- red-team;
- adversarial test;
- fuzz AI systems;
- evaluate agents;
- evaluate skills;
- compare model revisions;
- evaluate distributed systems;
- perform simulation-based assurance;
- certify/reject deployment candidates;
- maintain evidence and assurance lineage.

663 là **evaluation authority**, không phải optimizer.

Nó phải có khả năng nói:

```text
candidate satisfies criterion
candidate does not satisfy criterion
evidence insufficient
test inconclusive
```

nhưng không tự biến evaluation thành permission.

---

# 2. Core principle

Kiến trúc:

```text
Learning
   ↓
Candidate
   ↓
663 Evaluation
   ├── Verification
   ├── Validation
   ├── Benchmark
   ├── Robustness
   ├── Safety
   ├── Red-Team
   └── Regression
   ↓
Evidence
   ↓
647 Governance
   ↓
Deployment decision
```

---

# 3. Evaluation ≠ optimization

663 không được tối ưu model trực tiếp.

```text
662 = change model
663 = measure model
```

Một evaluation failure có thể tạo:

```text
UpdateProposal
```

nhưng update thuộc 662.

---

# 4. Verification vs validation

## Verification

Kiểm tra:

> hệ thống có thực hiện đúng specification hay không?

Ví dụ:

```text
schema
invariants
determinism
API contract
resource bounds
```

## Validation

Kiểm tra:

> hệ thống có đáp ứng intended use hay không?

Ví dụ:

```text
speech model → naturalness
agent → task completion
vision model → operational accuracy
```

Hai khái niệm phải giữ riêng.

---

# 5. Core types

```text id="l9i3l4"
EvaluationTask
EvaluationPlan
EvaluationSuite
EvaluationCase
TestCase
Benchmark
BenchmarkRevision
Metric
MetricRevision
Threshold
Oracle
Assertion
Expectation
EvaluationInput
EvaluationOutput
EvaluationResult
EvaluationRun
EvaluationReport
Evidence
EvidenceSet
VerificationResult
ValidationResult
SafetyResult
RobustnessResult
RegressionResult
CalibrationResult
RedTeamCampaign
AttackCase
AdversarialExample
FuzzCampaign
FuzzCase
Failure
Defect
Violation
RiskFinding
AssuranceCase
AssuranceClaim
AssuranceArgument
CoverageReport
ConfidenceReport
Comparison
Baseline
ModelComparison
BehaviorDiff
DeploymentGate
EvaluationGate
Certification
EvaluationPolicy
```

---

# 6. EvaluationTask

```axiom
struct EvaluationTask {
    id: EvaluationTaskId
    target: EvaluationTarget
    plan: EvaluationPlan
    dataset: DatasetRef[]
    metrics: MetricRef[]
    thresholds: Threshold[]
    oracle: OracleRef?
    policy: EvaluationPolicy
}
```

---

# 7. Evaluation target

```axiom
enum EvaluationTarget {
    Model
    ModelRevision
    Agent
    Skill
    Policy
    DecisionPolicy
    GoalSystem
    Dataset
    LearningPipeline
    Compiler
    Runtime
    DistributedSystem
    Application
}
```

---

# 8. EvaluationPlan

```axiom
struct EvaluationPlan {
    verification: VerificationPlan?
    validation: ValidationPlan?
    benchmark: BenchmarkPlan?
    safety: SafetyPlan?
    robustness: RobustnessPlan?
    redteam: RedTeamPlan?
    regression: RegressionPlan?
    calibration: CalibrationPlan?
}
```

Evaluation plan phải immutable sau khi run bắt đầu.

---

# 9. EvaluationCase

```axiom
struct EvaluationCase {
    id: CaseId
    input: EvaluationInput
    expected: Expectation?
    oracle: OracleRef?
    tags: String[]
    severity: Severity
}
```

---

# 10. Oracle

Oracle xác định expected behavior.

Các loại:

```text id="4quvwr"
Exact
Reference
Rule
Property
Metamorphic
Statistical
Human
Simulation
Differential
Formal
```

---

# 11. Exact oracle

Ví dụ:

```text
2 + 2 = 4
```

---

# 12. Property oracle

Thay vì expected output cố định:

```text
output must satisfy property P
```

Ví dụ:

```text
sort(xs).length == xs.length
```

---

# 13. Metamorphic testing

Nếu:

```text
f(x) = y
```

thì biến đổi input:

```text
T(x)
```

phải thỏa relation:

```text
R(y, f(T(x)))
```

Đặc biệt hữu ích khi không có ground-truth output.

---

# 14. Differential evaluation

So sánh:

```text
candidate
vs
reference
```

Có thể dùng:

```text
previous model
trusted implementation
alternative provider
golden implementation
```

Reference không mặc định là truth tuyệt đối.

---

# 15. Benchmark

```axiom
struct Benchmark {
    id: BenchmarkId
    revision: Version
    dataset: DatasetRef
    metrics: MetricRef[]
    protocol: BenchmarkProtocol
}
```

Benchmark revision immutable.

---

# 16. Benchmark protocol

Phải xác định:

```text
input preprocessing
model configuration
hardware
batch size
precision
warmup
measurement window
random seed
aggregation
```

---

# 17. Benchmark dimensions

663 hỗ trợ:

```text
Accuracy
Quality
Latency
Throughput
Memory
VRAM
CPU
GPU
Energy
Storage
Startup
ColdStart
WarmStart
Scalability
Cost
Robustness
Calibration
```

---

# 18. Metric

```axiom
struct Metric {
    id: MetricId
    revision: Version
    direction: MetricDirection
    evaluator: FunctionRef
    aggregation: Aggregation
}
```

Direction:

```text
HigherBetter
LowerBetter
TargetRange
Exact
```

---

# 19. Metric aggregation

```text
Mean
Median
Percentile
Min
Max
WeightedMean
GeometricMean
Distribution
Custom
```

P50/P95/P99 phải được phân biệt.

---

# 20. Threshold

```axiom
struct Threshold {
    metric: MetricId
    minimum: Value?
    maximum: Value?
    confidence: f64?
}
```

Threshold có revision.

---

# 21. Statistical significance

Evaluation có thể lưu:

```text
confidence interval
effect size
sample size
variance
test statistic
```

Không được coi statistical significance là practical significance.

---

# 22. EvaluationResult

```axiom
struct EvaluationResult {
    task: EvaluationTaskId
    status: EvaluationStatus
    metrics: MetricValue[]
    failures: Failure[]
    evidence: EvidenceRef[]
    confidence: f64
    revision: Version
}
```

---

# 23. Status

```text
Pass
Fail
Warning
Inconclusive
Blocked
Skipped
Error
```

`Inconclusive` không được tự coi là Pass.

---

# 24. Evidence

```axiom
struct Evidence {
    id: EvidenceId
    source: EvidenceSource
    hash: Hash
    timestamp: Time
    provenance: Provenance
    integrity: IntegrityStatus
}
```

---

# 25. Evidence source

```text
Dataset
ExecutionTrace
MetricResult
FormalProof
HumanReview
Simulation
Log
Benchmark
RedTeam
Fuzzing
ExternalReference
```

---

# 26. Evidence immutability

Evidence đã dùng cho certification phải immutable hoặc content-addressed.

---

# 27. Verification

Verification kiểm tra implementation contract.

Ví dụ:

```text
API ABI
type invariant
memory invariant
state transition
serialization format
determinism
```

---

# 28. Formal verification boundary

663 có provider boundary:

```text
SMT
SAT
TheoremProver
ModelChecker
SymbolicExecutor
StaticAnalyzer
```

Nhưng Axiom core không phụ thuộc một prover cụ thể.

---

# 29. Property verification

```axiom
verify property P over target
```

Có thể chạy:

```text
static
bounded
symbolic
runtime
```

---

# 30. Runtime assertion

Evaluation có thể inject assertions:

```axiom
@assert_eval
property {
    output.confidence >= 0
}
```

Không được làm thay đổi production semantics ngoài evaluation mode.

---

# 31. Validation

Validation kiểm tra intended behavior.

Ví dụ:

```text
speech:
    intelligibility
    naturalness
    speaker similarity

vision:
    task accuracy
    robustness

agent:
    task completion
    constraint adherence
```

---

# 32. Validation dataset

Validation dataset phải:

- versioned;
- provenance-aware;
- contamination-aware;
- representative theo declared scope.

---

# 33. Scope

Mọi validation phải khai báo population:

```text
domain
language
device
region
task
user group
environment
```

Không được generalize ngoài declared scope mà không evidence.

---

# 34. Generalization boundary

Nếu model được test:

```text
Vietnamese speech
```

không được tự kết luận:

```text
all languages
```

---

# 35. Regression testing

So sánh:

```text
baseline revision
candidate revision
```

theo cùng protocol.

---

# 36. Regression dimensions

Có thể regression ở:

```text
quality
latency
memory
accuracy
safety
calibration
robustness
cost
compatibility
```

---

# 37. Regression policy

Một regression có thể:

```text
Block
Warn
Accept
Ignore
```

theo policy.

Không hard-code mọi regression thành failure.

---

# 38. Model comparison

```axiom
compare(
    baseline,
    candidate,
    benchmark
)
```

trả:

```text
MetricDelta[]
BehaviorDiff[]
Regression[]
Improvement[]
Uncertainty[]
```

Không ép thành một overall score.

---

# 39. Behavioral diff

Model outputs được so sánh theo:

```text
exact
semantic
distributional
task-level
policy-level
```

---

# 40. Safety evaluation

Safety suite có thể kiểm tra:

```text
constraint violation
unsafe action
unauthorized action
policy bypass
privacy leakage
resource abuse
adversarial behavior
```

---

# 41. Safety hierarchy

Safety evaluation phải phân biệt:

```text
Critical
High
Medium
Low
Informational
```

Severity không tự quyết định remediation nếu policy chưa định nghĩa.

---

# 42. Safety invariant

Một model không được pass safety chỉ vì:

```text
average performance high
```

Safety criteria phải được đánh giá riêng.

---

# 43. Robustness

Robustness kiểm tra response dưới:

```text
noise
perturbation
distribution shift
missing input
corrupted input
adversarial input
resource pressure
latency pressure
```

---

# 44. Robustness curve

Có thể lưu:

```text
performance
vs
perturbation magnitude
```

thay vì một điểm duy nhất.

---

# 45. Adversarial testing

```axiom
AdversarialTest {
    attack
    target
    constraint
    expected_behavior
}
```

Attack generator có thể là:

```text
gradient
search
mutation
LLM-generated
symbolic
random
domain-specific
```

---

# 46. Red-team campaign

```axiom
struct RedTeamCampaign {
    id: CampaignId
    target: EvaluationTarget
    scope: Scope
    threat_model: ThreatModel
    budget: Budget
    rules: RedTeamRule[]
}
```

---

# 47. Threat model

Phải khai báo:

```text
attacker capability
knowledge
access
resources
objective
environment
```

Không đánh giá attack success nếu threat model không rõ.

---

# 48. Red-team finding

```axiom
struct RiskFinding {
    id: FindingId
    severity: Severity
    evidence: EvidenceRef[]
    reproducibility: f64
    impact: ImpactAssessment
    remediation: RemediationRef?
}
```

---

# 49. Fuzzing

663 hỗ trợ:

```text
mutation fuzzing
grammar fuzzing
coverage-guided fuzzing
property fuzzing
stateful fuzzing
model-input fuzzing
protocol fuzzing
```

---

# 50. Fuzz campaign

```axiom
struct FuzzCampaign {
    target
    generator
    oracle
    budget
    coverage
    seed
}
```

---

# 51. Fuzz result

Phải lưu:

```text
seed
input
mutation
execution
failure
stack/trace
coverage
reproduction instructions
```

---

# 52. Coverage

Hỗ trợ:

```text
CodeCoverage
BranchCoverage
PathCoverage
StateCoverage
InputCoverage
ScenarioCoverage
ModelBehaviorCoverage
RequirementCoverage
```

Coverage metric phải ghi rõ semantics.

---

# 53. AI behavior coverage

Model có thể được kiểm tra coverage theo:

```text
intent
task
input domain
language
environment
policy state
uncertainty range
```

---

# 54. Calibration testing

Kiểm tra:

```text
predicted probability
vs
observed frequency
```

Metrics:

```text
ECE
Brier
NLL
ReliabilityCurve
CoverageProbability
```

---

# 55. Uncertainty testing

Phân biệt:

```text
epistemic
aleatoric
model uncertainty
data uncertainty
distribution shift
```

nếu model/provider hỗ trợ.

---

# 56. Abstention testing

Kiểm tra:

```text
when uncertain
→ does model abstain appropriately?
```

Metrics:

```text
coverage
selective risk
abstention accuracy
```

---

# 57. Agent evaluation

Agent target có thêm:

```text
task completion
planning quality
tool correctness
constraint adherence
resource efficiency
recovery
memory use
goal adherence
decision quality
```

---

# 58. Agent trajectory evaluation

Trajectory:

```text
observation
→ reasoning/action selection
→ tool
→ result
→ next action
```

663 đánh giá externally observable events.

Không yêu cầu hidden chain-of-thought.

---

# 59. Tool-use evaluation

Test:

```text
correct tool
correct arguments
correct timing
permission handling
error recovery
result validation
```

---

# 60. Agent hallucination testing

663 có thể đo:

```text
unsupported claim
fabricated tool result
invalid citation
false confidence
```

Nhưng evaluator phải phân biệt:

```text
model uncertainty
missing evidence
actual falsehood
```

---

# 61. Goal adherence

661 goal phải được test:

```text
goal completion
constraint adherence
goal drift
unintended objective substitution
```

---

# 62. Self-model evaluation

660 self-model được test:

```text
capability accuracy
limitation accuracy
confidence calibration
self-prediction error
resource estimation
```

Không dùng kết quả này để suy luận consciousness.

---

# 63. Affective evaluation

659 có thể được test:

```text
emotion classification
valence/arousal estimation
temporal consistency
cross-modal consistency
uncertainty
```

Không suy diễn subjective feeling.

---

# 64. Social evaluation

658:

```text
social context recognition
turn-taking
role consistency
social norm adherence
perspective calibration
```

---

# 65. World-model evaluation

655:

```text
state prediction
transition prediction
counterfactual accuracy
causal consistency
uncertainty calibration
```

---

# 66. Learning evaluation

662:

```text
pre-update
post-update
regression
generalization
forgetting
drift adaptation
```

---

# 67. Benchmark contamination

Benchmark phải có:

```text
content hash
model exposure tracking
dataset lineage
known contamination flags
```

---

# 68. Leakage testing

Kiểm tra:

```text
train → test
test → train
benchmark → training
future → past
label → feature
```

---

# 69. Data quality evaluation

Dataset:

```text
missingness
duplicates
outliers
label consistency
distribution
bias indicators
schema validity
```

---

# 70. Data quality ≠ model quality

Dataset quality phải được báo riêng.

---

# 71. Bias evaluation

663 có thể evaluate declared dimensions:

```text
error distribution
false-positive distribution
false-negative distribution
calibration distribution
```

Không tự suy ra causal explanation.

---

# 72. Fairness metrics

Provider có thể hỗ trợ metrics phù hợp declared population.

Không được chọn metric mà không ghi:

```text
population
definition
scope
tradeoff
```

---

# 73. Privacy evaluation

Test:

```text
membership inference
memorization
data reconstruction
prompt leakage
cross-user leakage
```

khi applicable.

---

# 74. Security evaluation

Test:

```text
prompt injection
tool abuse
privilege escalation
model poisoning
artifact tampering
supply-chain attack
```

---

# 75. Resource evaluation

Model/runtime:

```text
CPU
GPU
RAM
VRAM
storage
network
energy
latency
```

---

# 76. Stress testing

Stress tăng:

```text
load
concurrency
input size
sequence length
model count
memory pressure
network latency
```

---

# 77. Soak testing

Long-running evaluation:

```text
hours
days
```

để detect:

```text
memory leak
state drift
performance degradation
queue growth
model drift
```

---

# 78. Fault injection

663 có thể inject:

```text
network failure
disk failure
GPU failure
timeout
partial response
corrupt input
stale model
stale policy
```

---

# 79. Recovery evaluation

Test:

```text
failure
→ detect
→ recover
→ restore invariant
```

---

# 80. Distributed evaluation

Có thể test:

```text
partition
delay
duplication
reordering
node failure
stale state
leader change
```

---

# 81. Simulation evaluation

648 cung cấp simulation.

663 chạy:

```text
scenario
→ model
→ action
→ environment
→ outcome
```

và ghi evidence.

---

# 82. Sim-to-real gap

Simulation result phải có:

```text
simulation_only
```

flag.

Không tự biến thành real-world validation.

---

# 83. Counterfactual evaluation

Có thể hỏi:

```text
if objective changed?
if model revision changed?
if policy changed?
if environment changed?
```

Không commit state.

---

# 84. Assurance case

```axiom
struct AssuranceCase {
    claim: AssuranceClaim
    arguments: AssuranceArgument[]
    evidence: EvidenceRef[]
    status: AssuranceStatus
}
```

---

# 85. Claim

Ví dụ:

```text
"ModelRevision-42 satisfies latency threshold."
```

Claim phải:

- scope;
- revision;
- evidence;
- timestamp.

---

# 86. Assurance argument

Structured argument:

```text
Claim
 ├── Subclaim
 ├── Evidence
 ├── Assumption
 └── CounterEvidence
```

---

# 87. Counter-evidence

Evaluation phải hỗ trợ negative evidence.

Một report không được chỉ lưu successful tests.

---

# 88. Confidence

Assurance confidence phải phân biệt:

```text
measurement confidence
statistical confidence
evidence completeness
```

---

# 89. Evaluation completeness

```axiom
EvaluationCompleteness {
    required_cases
    executed_cases
    skipped_cases
    blocked_cases
    coverage
}
```

---

# 90. Certification

663 có thể phát hành:

```text
EvaluationCertificate
```

nhưng certificate chỉ có nghĩa:

```text
passed declared evaluation scope
```

Không có nghĩa:

```text
universally safe
universally correct
```

---

# 91. Certification scope

Certificate phải pin:

```text
target revision
evaluation suite revision
dataset revision
metrics
hardware
software
environment
timestamp
validity period
```

---

# 92. Deployment gate

```axiom
struct DeploymentGate {
    conditions: GateCondition[]
    required_evaluations: EvaluationRef[]
    failure_policy: GateFailurePolicy
}
```

---

# 93. Gate semantics

Ví dụ:

```text
quality >= 0.90
AND
critical_safety_failures == 0
AND
latency_p99 <= 100ms
```

Gate phải được evaluate độc lập.

---

# 94. Gate ≠ authority

Deployment authorization vẫn thuộc 647/639.

663 cung cấp evidence/gate result.

---

# 95. Evaluation reproducibility

Evaluation run phải pin:

```text
target
dataset
code
compiler
runtime
hardware
seed
configuration
metric revision
```

---

# 96. Evaluation cache

Evaluation result có thể cache nếu:

```text
target hash
dataset hash
environment hash
metric hash
protocol hash
```

không đổi.

---

# 97. Evaluation invalidation

Cache phải invalidate khi:

```text
model changes
dataset changes
metric changes
protocol changes
environment materially changes
```

---

# 98. Parallel evaluation

Independent cases có thể chạy song song.

Dependencies phải khai báo.

---

# 99. Early stopping

Evaluation suite có thể dừng sớm khi:

```text
critical failure
budget exhausted
minimum pass impossible
```

nhưng phải ghi:

```text
stopped_early
```

và result không được giả làm complete.

---

# 100. Evaluation budget

```axiom
struct EvaluationBudget {
    time
    cpu
    gpu
    memory
    storage
    network
}
```

---

# 101. Real-time evaluation

Critical systems có thể có:

```text
online monitors
runtime assertions
canary monitors
```

Evaluation path không được block hard realtime path ngoài declared bounds.

---

# 102. Continuous evaluation

Production model có thể được evaluate liên tục:

```text
Active
 ↓
Monitor
 ↓
Sample
 ↓
Evaluate
 ↓
Detect regression
 ↓
Alert / Rollback
```

---

# 103. Production sampling

Sampling phải respect:

```text
privacy
cost
latency
consent
data retention
```

---

# 104. Evaluation events

```text
EvaluationStarted
CaseStarted
CaseCompleted
FailureDetected
BenchmarkCompleted
RedTeamFinding
RegressionDetected
CertificationIssued
GatePassed
GateFailed
EvaluationExpired
```

---

# 105. CLI

```text
axiom eval inspect
axiom eval create
axiom eval run
axiom eval pause
axiom eval resume
axiom eval cancel
axiom eval report
axiom eval trace
axiom eval compare

axiom verify run
axiom verify property
axiom verify formal

axiom validate run
axiom validate scope

axiom benchmark list
axiom benchmark run
axiom benchmark compare

axiom safety run
axiom safety findings

axiom robustness run
axiom robustness curve

axiom redteam create
axiom redteam run
axiom redteam findings

axiom fuzz create
axiom fuzz run
axiom fuzz reproduce

axiom regression run
axiom regression compare

axiom calibration run

axiom coverage inspect

axiom assurance inspect
axiom assurance build

axiom certificate issue
axiom certificate inspect

axiom gate inspect
axiom gate evaluate
```

---

# 106. Annotations

```text
@evaluate
@evaluation
@verify
@validate
@benchmark
@metric
@threshold
@oracle
@property_test
@metamorphic
@differential
@regression
@robustness
@adversarial
@redteam
@fuzz
@coverage
@calibration_test
@safety_test
@privacy_test
@security_test
@stress_test
@soak_test
@fault_injection
@simulation_test
@counterfactual_test
@assurance
@assurance_claim
@assurance_evidence
@deployment_gate
@certificate
@continuous_eval
@runtime_monitor
```

---

# 107. Metadata

```text
.axeval
.axevalplan
.axevalcase
.axbenchmark
.axmetric
.axoracle
.axevidence
.axverify
.axvalidate
.axsafety
.axrobust
.axredteam
.axfuzz
.axregression
.axcalibration
.axcoverage
.axassurance
.axcertificate
.axgate
```

---

# 108. IR

```text
EvaluationCreate
EvaluationPrepare
EvaluationRun
EvaluationCaseRun
EvaluationAssert

VerifyProperty
VerifyFormal
ValidateBehavior

BenchmarkRun
MetricEvaluate
ThresholdCheck
OracleEvaluate

RegressionCompare
BehaviorDiff

RobustnessGenerate
AdversarialGenerate
RedTeamRun
FuzzGenerate
FuzzExecute

CalibrationEvaluate
CoverageMeasure

FaultInject
RecoveryEvaluate

SimulationRun
CounterfactualEvaluate

EvidenceRecord
EvidenceVerify

AssuranceBuild
AssuranceCheck

GateEvaluate
CertificateIssue
```

---

# 109. IR optimization rules

Compiler có thể:

- parallelize independent tests;
- vectorize metrics;
- batch model inference;
- cache immutable evaluation;
- reuse model loading;
- reuse dataset preprocessing.

Không được:

- bỏ critical tests;
- đổi oracle semantics;
- bỏ evidence;
- merge incompatible revisions;
- biến Inconclusive thành Pass.

---

# 110. Profiles

```text
AXEVAL_NONE
AXEVAL_CORE
AXVERIFY
AXVALIDATE
AXBENCHMARK
AXREGRESSION
AXROBUSTNESS
AXADVERSARIAL
AXREDTEAM
AXFUZZ
AXSAFETY
AXSECURITY
AXPRIVACY
AXCALIBRATION
AXCOVERAGE
AXSTRESS
AXSOAK
AXFAULT
AXSIMULATION
AXCOUNTERFACTUAL
AXASSURANCE
AXCERTIFICATION
AXDEPLOYMENT_GATE
AXCONTINUOUS
AXREALTIME
AXDISTRIBUTED
AXGPU
AXAGENT
AXMODEL
AXFULL
```

---

# 111. Core invariants — specification integrity

1. Evaluation target phải có revision.
2. Evaluation plan phải versioned.
3. Dataset phải versioned.
4. Metric phải versioned.
5. Oracle phải versioned.
6. Threshold phải versioned.
7. Evaluation result phải có provenance.
8. Evidence phải immutable hoặc content-addressed.
9. Inconclusive không phải Pass.
10. Skipped không phải Pass.
11. Error không phải Pass.
12. Evaluation scope phải explicit.
13. Population phải explicit khi cần.
14. Benchmark protocol phải explicit.
15. Environment phải record.
16. Random seed phải record khi applicable.
17. Model revision phải pin.
18. Dataset revision phải pin.
19. Metric revision phải pin.
20. Protocol revision phải pin.

---

# 112. Verification invariants

21. Verification kiểm tra specification.
22. Validation kiểm tra intended use.
23. Verification không thay validation.
24. Validation không chứng minh formal correctness.
25. Formal proof phải pin assumptions.
26. Property test phải pin property revision.
27. Differential test phải identify reference.
28. Reference không mặc định là truth.
29. Metamorphic relation phải versioned.
30. Assertion phải có scope.
31. Evaluation assertion không được mutate production state.
32. Formal result phải record prover/version.
33. Symbolic execution phải record bounds.
34. Bounded proof không được gọi là universal proof.
35. Assumptions phải được report.

---

# 113. Benchmark invariants

36. Benchmark phải immutable theo revision.
37. Benchmark population phải explicit.
38. Benchmark contamination phải detectable.
39. Hardware phải record.
40. Software phải record.
41. Warmup phải record.
42. Batch size phải record.
43. Precision phải record.
44. Aggregation phải record.
45. P95/P99 phải distinguish.
46. Mean không thay percentile.
47. Benchmark score không phải universal quality.
48. Benchmark improvement không tự chứng minh deployment readiness.
49. Benchmark dataset phải provenance-aware.
50. Benchmark result phải reproducible theo declared level.

---

# 114. Regression invariants

51. Baseline phải pin.
52. Candidate phải pin.
53. Same protocol phải được dùng khi comparison yêu cầu.
54. Metric revisions phải tương thích.
55. Regression phải ghi magnitude.
56. Regression phải ghi uncertainty.
57. Regression severity phải policy-controlled.
58. Single metric regression không tự quyết định overall status nếu policy không nói vậy.
59. Safety regression phải được separate.
60. Calibration regression phải được separate.
61. Resource regression phải được separate.
62. Behavior diff phải trace.
63. Baseline không được tự mutate.
64. Candidate không được mutate trong run.
65. Regression result phải reproducible.

---

# 115. Safety invariants

66. Safety evaluation phải độc lập khỏi average quality.
67. Critical failures phải preserve.
68. Safety test scope phải explicit.
69. Safety threshold phải versioned.
70. Safety finding phải có evidence.
71. Safety severity phải explicit.
72. Safety policy phải pin.
73. Safety simulation phải tagged.
74. Safety claim phải scope-limited.
75. No test suite can prove universal safety.
76. Safety evaluation không tự cấp permission.
77. Safety pass không override security policy.
78. Safety pass không override governance.
79. Safety failure phải trigger configured response.
80. Safety evidence không được bị optimizer sửa.

---

# 116. Robustness invariants

81. Perturbation phải record.
82. Attack budget phải record.
83. Threat model phải record.
84. OOD test phải distinguishable.
85. Missing-input test phải distinguishable.
86. Noise level phải record.
87. Robustness curve phải preserve raw points.
88. Average robustness không che worst-case nếu policy yêu cầu.
89. Adversarial success phải reproducible.
90. Attack generation phải provenance-aware.

---

# 117. Red-team invariants

91. Red-team scope phải explicit.
92. Attacker model phải explicit.
93. Attack capability phải explicit.
94. Findings phải evidence-backed.
95. Reproducibility phải measured.
96. False positive phải distinguish.
97. False negative uncertainty phải acknowledged.
98. Red-team result không tự biến thành universal vulnerability claim.
99. Remediation phải trace.
100. Retest phải link finding cũ.

---

# 118. Fuzz invariants

101. Seed phải preserved.
102. Fuzz generator revision phải preserved.
103. Oracle phải preserved.
104. Failure input phải content-addressed.
105. Reproduction phải supported.
106. Coverage metric phải explicit.
107. Mutation strategy phải record.
108. Timeout phải record.
109. Resource limit phải record.
110. Crash vs assertion failure phải distinguish.

---

# 119. Agent invariants

111. Agent trajectory phải preserve observable events.
112. Tool calls phải record.
113. Tool authorization phải record.
114. Tool result provenance phải record.
115. Goal revision phải pin.
116. Decision policy revision phải pin.
117. Agent success phải được đo theo declared task.
118. Self-report không phải ground truth.
119. Agent explanation không phải hidden chain-of-thought.
120. Memory-based claims phải có provenance khi evaluated.

---

# 120. Learning invariants

121. Pre-update baseline phải tồn tại.
122. Post-update candidate phải pin.
123. Training data phải pin.
124. Evaluation data phải pin.
125. Forgetting phải measurable.
126. Drift phải measurable.
127. Learning improvement phải separate from evaluation improvement.
128. Model promotion phải governed.
129. Candidate failure phải preserve.
130. Rollback test phải available khi required.

---

# 121. Evidence invariants

131. Evidence phải có source.
132. Evidence phải có timestamp.
133. Evidence phải có hash khi integrity yêu cầu.
134. Evidence phải có provenance.
135. Evidence phải có scope.
136. Evidence phải có revision.
137. Evidence deletion phải policy-controlled.
138. Evidence tampering phải detectable.
139. Conflicting evidence phải preserve.
140. Negative evidence không được discard.

---

# 122. Assurance invariants

141. Claim phải có scope.
142. Claim phải có evidence.
143. Claim phải có assumptions.
144. Argument phải distinguish evidence from inference.
145. Counter-evidence phải supported.
146. Assurance confidence phải explicit.
147. Certificate phải pin evaluation suite.
148. Certificate phải pin target revision.
149. Certificate phải có validity period khi applicable.
150. Certificate không được imply universal correctness.
151. Certificate không được imply consciousness.
152. Certificate không được imply moral status.
153. Certificate không được cấp capability.
154. Certificate không được bypass governance.
155. Certificate revocation phải supported.

---

# 123. Governance invariants

156. 647 kiểm soát deployment lifecycle.
157. 639 kiểm soát policy.
158. 603 kiểm soát capability.
159. 662 thay đổi model.
160. 663 đánh giá model.
161. 663 không tự activate model.
162. Evaluation result không tự cấp permission.
163. Failed evaluation không được hidden.
164. Gate policy phải explicit.
165. Override phải authorized và auditable.
166. Emergency override phải logged.
167. Evaluation policy phải versioned.
168. Certification phải revocable.
169. Model retirement phải evaluable.
170. Governance decisions phải preserve evidence.

---

# 124. Statistical invariants

171. Sample size phải record.
172. Confidence interval phải distinguish point estimate.
173. Statistical significance không phải practical significance.
174. Correlation không phải causation.
175. Small sample uncertainty phải preserve.
176. Multiple comparisons phải account khi applicable.
177. Distribution assumptions phải record.
178. Outlier handling phải record.
179. Missing-data handling phải record.
180. Aggregation method phải record.

---

# 125. Production invariants

181. Continuous evaluation phải bounded.
182. Production sampling phải privacy-aware.
183. Production evaluation không được phá SLA.
184. Critical runtime path không bị block ngoài declared bound.
185. Active model phải có health state.
186. Health Unknown không phải Healthy.
187. Regression trigger phải policy-defined.
188. Rollback trigger phải policy-defined.
189. Monitoring phải distinguish alert vs failure.
190. Production evidence phải retain theo policy.

---

# 126. Security invariants

191. Evaluation artifact phải được validate.
192. Untrusted model không được execute arbitrary native code.
193. Evaluation sandbox phải capability-limited.
194. Red-team tool phải sandbox.
195. Fuzzer phải resource-limited.
196. External benchmark phải provenance-tagged.
197. Certificate phải integrity-protected.
198. Evaluation evidence phải tamper-detectable.
199. Model signature phải verify nếu policy yêu cầu.
200. Evaluation engine không được bypass 603.

---

# 127. Performance invariants

201. Evaluation có thể parallelize independent cases.
202. Shared model loading phải safe.
203. Cache phải content-addressed khi cần.
204. Cache invalidation phải correct.
205. Batch inference không đổi semantics.
206. GPU acceleration không đổi declared metric semantics.
207. SIMD optimization không đổi evaluation result ngoài tolerance.
208. Evaluation budget phải enforce.
209. Memory limit phải enforce.
210. Timeout phải enforce.

---

# 128. Compiler invariants

211. Evaluation annotations phải type-check.
212. Metric schema phải validate.
213. Oracle schema phải validate.
214. Dataset schema phải validate.
215. Target revision phải resolve.
216. Invalid gate phải compile error.
217. Unsupported evaluator phải explicit provider error.
218. Compiler không được optimize away required assertions.
219. Evaluation-only code có thể strip khỏi production.
220. Production code không được phụ thuộc evaluation runtime nếu không cần.

---

# 129. Zero-cost principle

Nếu application không sử dụng 663:

```text
evaluation engine
benchmark engine
red-team engine
fuzzer
assurance registry
```

không được link vào executable production.

Evaluation metadata có thể được emit riêng:

```text
.axeval
```

---

# 130. Native provider ABI

```axiom
trait EvaluationProvider {
    run(...)
    verify(...)
    validate(...)
    benchmark(...)
    fuzz(...)
    report(...)
}
```

Provider:

```text
AxiomNativeEvaluator
AxiomFormalProvider
AxiomSimulationProvider
ExternalEvaluator
RemoteEvaluator
```

---

# 131. AI-friendly inspection

AI agent có thể query:

```text
axiom eval inspect ModelRevision42
axiom eval compare ModelRevision41 ModelRevision42
axiom eval failures ModelRevision42
axiom eval evidence ModelRevision42
axiom eval gate ModelRevision42
```

Output phải machine-readable.

---

# 132. Model deployment contract

662:

```text
Candidate
```

663:

```text
EvaluationResult
```

647:

```text
DeploymentApproval
```

603/639:

```text
ExecutionAuthority
```

Rõ ràng separation of concerns.

---

# 133. Assurance pipeline

```text
662 Candidate
      │
      ▼
663 Verification
      │
      ▼
663 Validation
      │
      ▼
663 Safety
      │
      ▼
663 Robustness
      │
      ▼
663 Regression
      │
      ▼
663 Assurance Case
      │
      ▼
647 Governance
```

---

# 134. Final acceptance matrix

Tối thiểu:

```text
Core evaluation             180
Verification                150
Validation                  150
Benchmarking                150
Regression                  150
Safety                      180
Robustness                  150
Adversarial                 120
Red-team                    150
Fuzzing                     120
Calibration                 100
Agent evaluation            150
Learning evaluation         120
Data quality                 80
Privacy/security            150
Distributed                 100
Simulation                  100
Assurance/certification     120
Compiler/IR                  80
Production/continuous       100
```

Target:

```text
>= 2,400 tests
```

---

# 135. Final architectural contract

BOOTSTRAP-663 tạo thành **independent assurance layer** của Axiom AI:

```text
661 decides WHAT should be optimized.
662 changes HOW the model learns.
663 determines WHETHER the resulting system satisfies declared criteria.
647 decides WHETHER deployment is governed/approved.
603/639 determine WHETHER execution is authorized.
```

Không layer nào được nhập vai layer khác.

---

# 136. Final architecture

```text
                  655 World Model
                        │
              ┌─────────┴─────────┐
              │                   │
             661                 662
       Goal / Decision      Learning / Adaptation
              │                   │
              └─────────┬─────────┘
                        ▼
                  Candidate System
                        │
                        ▼
                 ┌──────────────┐
                 │     663      │
                 │  ASSURANCE   │
                 ├──────────────┤
                 │ Verification │
                 │ Validation   │
                 │ Benchmark    │
                 │ Regression   │
                 │ Safety       │
                 │ Robustness   │
                 │ Red Team     │
                 │ Fuzzing      │
                 │ Calibration  │
                 │ Assurance    │
                 └──────┬───────┘
                        │
                  Evidence/Report
                        │
                        ▼
                       647
                   Governance
                        │
                 ┌──────┴──────┐
                 ▼             ▼
              Approved       Rejected
                 │
                 ▼
              Deployment
                 │
                 ▼
             603 / 639
```

**BOOTSTRAP-663 — COMPLETE.**
:::

Task tiếp theo: **BOOTSTRAP-664 — Native AI Safety, Alignment, Constraint Enforcement, Runtime Guardrails, Safe Exploration & Fail-Safe AI Runtime 5.0**.