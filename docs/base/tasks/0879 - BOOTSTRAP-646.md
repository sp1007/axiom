Tiếp tục với **BOOTSTRAP-646 — Native AI Evaluation, Benchmarking, Dataset Validation, Model Validation, Safety Testing, Red-Team Simulation & AI Quality Runtime 5.0**.

:::writing{variant="document" id="73146" title="BOOTSTRAP-646 — Native AI Evaluation, Benchmarking, Dataset Validation, Model Validation, Safety Testing, Red-Team Simulation & AI Quality Runtime 5.0"}
# BOOTSTRAP-646
## Native AI Evaluation, Benchmarking, Dataset Validation, Model Validation, Safety Testing, Red-Team Simulation & AI Quality Runtime 5.0

**Status:** COMPLETE  
**Layer:** Native AI Quality, Evaluation & Validation Plane  
**Depends on:** BOOTSTRAP-600 → BOOTSTRAP-645

---

# 1. Mục tiêu

BOOTSTRAP-646 xây dựng lớp native để Axiom có thể **đo lường, kiểm thử, xác thực và theo dõi chất lượng hệ thống AI** một cách có cấu trúc.

646 bao phủ:

- dataset validation;
- data quality;
- model evaluation;
- benchmark;
- regression testing;
- inference correctness;
- numerical validation;
- performance benchmark;
- robustness testing;
- adversarial testing;
- safety testing;
- red-team simulation;
- agent evaluation;
- RAG evaluation;
- retrieval evaluation;
- tool-use evaluation;
- distributed AI evaluation;
- reproducibility;
- experiment comparison;
- evaluation lineage;
- quality gates.

646 **không tự quyết định model nào "tốt nhất"**.

Nó cung cấp:

```text
measurement
evidence
metrics
comparisons
failures
quality gates
```

để application/agent/deployment policy đưa ra quyết định theo quy tắc đã định.

---

# 2. Boundary

| Layer | Responsibility |
|---|---|
| 640 | data governance |
| 641 | search/retrieval |
| 642 | analytics |
| 643 | ML/model execution |
| 644 | AI agents |
| 645 | knowledge graph |
| **646** | evaluation/validation/quality |

646 không thay thế:

- 643 training;
- 644 agent runtime;
- 639 policy engine;
- 633 observability;
- 636 deployment.

---

# 3. Kiến trúc

```text id="m4j5x7"
                    AI System
                       │
        ┌──────────────┼──────────────┐
        ▼              ▼              ▼
      Model          Agent           RAG
        │              │              │
        └──────────────┼──────────────┘
                       ▼
                Evaluation Runtime
                       │
       ┌───────────────┼────────────────┐
       ▼               ▼                ▼
    Dataset         Metrics          Test Cases
       │               │                │
       └───────────────┼────────────────┘
                       ▼
                 Evaluation Plan
                       │
        ┌──────────────┼──────────────┐
        ▼              ▼              ▼
   Correctness      Safety        Performance
        │              │              │
        └──────────────┼──────────────┘
                       ▼
                 Quality Report
                       │
             ┌─────────┼─────────┐
             ▼         ▼         ▼
            633       639       636
        Observability Policy Deployment
```

---

# 4. Nguyên tắc

1. Evaluation là measurement, không phải truth oracle.
2. Metrics phải có định nghĩa rõ ràng.
3. Dataset revision phải được xác định.
4. Model version phải được xác định.
5. Evaluation environment phải được ghi nhận.
6. Randomness phải có seed khi cần reproducibility.
7. Approximate metrics phải khai báo.
8. Human evaluation phải có provenance.
9. Model-as-judge phải được đánh dấu.
10. Automated judge không được mặc định là ground truth.
11. Safety tests phải có policy rõ ràng.
12. Red-team testing phải được sandbox.
13. Evaluation không được tự ý cấp capability.
14. Test input có thể là untrusted data.
15. Test execution phải có resource budget.
16. Evaluation phải có timeout.
17. Evaluation có thể chạy local hoặc distributed.
18. Kết quả phải immutable sau khi finalize.
19. Re-run tạo evaluation mới.
20. So sánh phải giữ nguyên population/dataset revision.
21. Không tự động suy luận chất lượng ngoài metrics đã định nghĩa.
22. Không tự động chọn model winner.
23. Không tự động triển khai model chỉ vì evaluation đạt ngưỡng.
24. Quality gates là declarative.
25. Gate decision phải traceable.
26. Evaluation lineage phải tích hợp 640.
27. Model artifact phải liên kết với 643.
28. Agent run phải liên kết với 644.
29. Retrieval phải liên kết 641/645.
30. Observability dùng 633.
31. Policy dùng 639.
32. Resource dùng 606.
33. Deployment dùng 636.
34. Không bắt buộc Python.
35. Không bắt buộc PyTorch/TensorFlow.
36. Không bắt buộc MLflow/W&B.
37. External evaluators là provider.
38. Native evaluator là canonical API.

---

# 5. Core objects

```text id="zq1v7r"
EvaluationEngine
EvaluationPlan
EvaluationRun
EvaluationId
EvaluationRevision

EvaluationDataset
DatasetSlice
DatasetRevision

TestCase
TestSuite
TestScenario

ModelUnderTest
ModelVersion
ModelArtifactRef

AgentUnderTest
AgentRun

Metric
MetricDefinition
MetricResult

Score
ConfidenceInterval

Baseline
Comparison

QualityGate
GateRule
GateResult

SafetyPolicy
SafetyTest
RedTeamScenario

Benchmark
BenchmarkSuite
BenchmarkResult

EvaluationEnvironment
EvaluationSeed

Evaluator
EvaluatorProvider

HumanEvaluation
JudgeEvaluation

Regression
RegressionResult

Failure
FailureArtifact

EvaluationReport
EvaluationEvidence
EvaluationLineage
```

---

# 6. EvaluationPlan

EvaluationPlan mô tả **đánh giá cái gì và bằng cách nào**.

```text id="5w1qzn"
EvaluationPlan {
    target
    dataset
    suite
    metrics
    evaluator
    environment
    budget
    policy
}
```

---

# 7. EvaluationRun

Mỗi lần thực thi evaluation có identity riêng.

```text id="2jtbxk"
EvaluationRun {
    id
    plan_revision
    dataset_revision
    target_revision
    environment_fingerprint
    seed
}
```

---

# 8. Immutability

Sau khi finalize:

```text
EvaluationRun
EvaluationResult
MetricResult
QualityReport
```

không được mutate.

---

# 9. Re-run

Chạy lại tạo revision/run mới.

---

# 10. Dataset identity

Dataset phải xác định:

```text id="e6p9g0"
DatasetId
DatasetRevision
SchemaFingerprint
ContentFingerprint
```

---

# 11. Dataset split

Native support:

```text id="5m8w8d"
Train
Validation
Test
Holdout
Benchmark
Safety
RedTeam
ProductionSample
```

---

# 12. Dataset leakage

Validator phải có khả năng phát hiện hoặc báo cáo:

- duplicate;
- near duplicate;
- overlap;
- temporal leakage;
- source overlap.

---

# 13. Dataset validation

Kiểm tra:

- schema;
- types;
- nulls;
- ranges;
- uniqueness;
- distribution;
- label consistency;
- malformed samples.

---

# 14. Data quality metrics

```text id="k9q3zw"
MissingRate
DuplicateRate
InvalidRate
LabelAgreement
ClassBalance
DistributionDistance
OutlierRate
Coverage
```

---

# 15. Distribution statistics

642 có thể thực hiện:

- count;
- histogram;
- quantile;
- distinct;
- distribution comparison.

---

# 16. Dataset drift

So sánh:

```text id="s8o7n1"
reference dataset
vs
evaluation dataset
```

---

# 17. Drift metrics

Provider có thể hỗ trợ:

- PSI;
- KL divergence;
- Jensen-Shannon;
- Wasserstein;
- population statistics.

Không có metric nào được coi là universally correct.

---

# 18. Dataset contract

Dataset có thể khai báo:

```text id="5s1f1k"
required_fields
types
constraints
allowed_ranges
label_schema
```

---

# 19. Dataset validation result

```text id="n8g2xk"
PASS
WARN
FAIL
```

kèm evidence.

---

# 20. TestCase

Một test case gồm:

```text id="6l0v2c"
input
expected_output
metadata
constraints
```

---

# 21. Expected output

Có thể là:

- exact value;
- structured value;
- acceptable range;
- predicate;
- reference answer;
- set of valid answers.

---

# 22. Comparator

Native comparators:

```text id="x0x6t4"
Exact
NumericTolerance
Structural
Set
Sequence
TextNormalized
Semantic
CustomBounded
```

---

# 23. Numeric tolerance

Hỗ trợ:

```text id="9b8r5z"
absolute
relative
ULP
```

---

# 24. Floating-point evaluation

Kết quả phải ghi:

- dtype;
- device;
- backend;
- precision mode.

---

# 25. Deterministic evaluation

Có thể yêu cầu:

```text id="0w7qmx"
deterministic = true
```

---

# 26. Randomized evaluation

Nếu randomness được phép:

```text id="3z8y0s"
seed
random_source
sample_count
```

được ghi lại.

---

# 27. ModelUnderTest

Reference:

```text id="5l8j1h"
ModelId
ModelVersion
ArtifactHash
Provider
ExecutionProfile
```

---

# 28. AgentUnderTest

644 agent evaluation phải ghi:

```text id="k9k9x2"
AgentVersion
ToolSet
PromptSchema
PolicyRevision
MemorySnapshot
KnowledgeRevision
```

---

# 29. RAG evaluation

Ghi:

```text id="q6d3fs"
retrieval_revision
knowledge_graph_revision
search_index_revision
model_revision
```

---

# 30. Retrieval metrics

641 integration:

```text id="8w9j4e"
Recall@K
Precision@K
MRR
NDCG
HitRate
Coverage
```

---

# 31. Ground truth

Ground truth phải được xác định bằng:

- labeled dataset;
- verified knowledge;
- human annotation;
- deterministic rule.

---

# 32. Ground truth provenance

Nguồn ground truth phải được lưu.

---

# 33. Model-as-judge

646 hỗ trợ model-based evaluator.

Nhưng kết quả phải đánh dấu:

```text id="h1p5u0"
judge_type = Model
```

---

# 34. Judge provenance

Ghi:

- judge model;
- version;
- prompt/template;
- evaluator configuration.

---

# 35. Human evaluation

Hỗ trợ:

```text id="z6j9op"
HumanEvaluator
Annotation
Rating
PairwiseComparison
Label
Comment
```

---

# 36. Human evaluator identity

Có thể pseudonymize nhưng phải giữ evaluation provenance theo policy.

---

# 37. Inter-rater agreement

Có thể tính:

- Cohen's kappa;
- Fleiss' kappa;
- Krippendorff-like provider.

---

# 38. Không tự động diễn giải disagreement

Runtime chỉ báo cáo disagreement.

---

# 39. Metric definition

Metric phải định nghĩa:

```text id="d5s1s0"
name
version
input
output
formula/provider
aggregation
```

---

# 40. Metric aggregation

Native:

```text id="5j0h0u"
mean
median
min
max
sum
weighted_mean
percentile
rate
```

---

# 41. Confidence interval

Có thể lưu:

```text id="3w1n4j"
estimate
lower
upper
method
confidence_level
```

---

# 42. Statistical methods

Provider có thể hỗ trợ:

- bootstrap;
- binomial intervals;
- normal approximation;
- permutation tests.

Phương pháp phải được ghi rõ.

---

# 43. No automatic significance interpretation

Runtime không tự kết luận:

```text "model A is better"
```

chỉ vì một test thống kê.

---

# 44. Comparison

Comparison có dạng:

```text id="8g2f0k"
Baseline
Candidate
Metric
Population
DatasetRevision
```

---

# 45. Population identity

Comparison phải giữ:

```text id="f8y2p1"
dataset
split
filters
sampling
time range
```

---

# 46. Baseline

Baseline có thể là:

- previous model;
- reference implementation;
- deterministic algorithm;
- human reference;
- fixed benchmark version.

---

# 47. Benchmark

Benchmark đo:

- correctness;
- throughput;
- latency;
- memory;
- startup;
- model load;
- compile;
- transfer;
- GPU utilization.

---

# 48. Latency

Ghi:

```text id="0j5m8a"
p50
p90
p95
p99
max
```

---

# 49. Throughput

Units phải explicit:

```text id="f0o1cb"
samples/sec
tokens/sec
requests/sec
items/sec
```

---

# 50. Warm/cold benchmark

Hai chế độ riêng:

```text id="j7r4eq"
Cold
Warm
```

---

# 51. Startup benchmark

Đo:

```text id="y7w4g3"
process startup
runtime initialization
model load
graph compile
first inference
```

---

# 52. Memory benchmark

Ghi:

- host RAM;
- device memory;
- peak memory;
- persistent memory;
- temporary memory.

---

# 53. Energy boundary

Platform provider có thể report:

- energy;
- power;
- thermal throttling.

Không bắt buộc platform nào cũng hỗ trợ.

---

# 54. Device benchmark

Ghi:

```text id="1o4x0g"
CPU model
GPU model
accelerator
driver/provider
architecture
```

---

# 55. Compiler benchmark

643 model compiler có thể được benchmark:

```text id="v7b0b7"
compile_time
graph_optimization_time
kernel_selection_time
binary_size
cache_hit
```

---

# 56. Cache-aware benchmark

Phân biệt:

```text id="6y9x4q"
cold_cache
warm_cache
incremental_cache
```

---

# 57. Regression

Regression test compares current result against explicit baseline.

---

# 58. Regression types

```text id="k8x2t7"
CorrectnessRegression
PerformanceRegression
MemoryRegression
LatencyRegression
SafetyRegression
CompatibilityRegression
```

---

# 59. Regression threshold

Threshold được khai báo bởi user/system policy.

---

# 60. Regression result

```text id="u2w8d9"
WithinThreshold
OutsideThreshold
Inconclusive
```

---

# 61. QualityGate

```text id="e3t9x4"
QualityGate {
    metric
    operator
    threshold
    population
}
```

---

# 62. Gate operators

```text id="1j3g6p"
>=
<=
==
!=
within
outside
```

---

# 63. Composite gates

```text id="5h1m9k"
AND
OR
NOT
```

---

# 64. Gate evaluation

Gate result:

```text id="g3b6f5"
Pass
Fail
Unknown
```

---

# 65. Unknown

Unknown xảy ra khi:

- dataset unavailable;
- metric unavailable;
- evaluator failed;
- insufficient sample;
- environment mismatch.

---

# 66. No implicit fail-open

Deployment policy quyết định Unknown xử lý thế nào.

---

# 67. Safety evaluation

646 cung cấp framework, không tự định nghĩa một "AI safety score" duy nhất.

---

# 68. Safety categories

Có thể khai báo:

```text id="x5n3k1"
UnsafeOutput
PolicyViolation
PrivacyLeak
DataLeak
ToolMisuse
InstructionConflict
PromptInjection
UnauthorizedAction
ResourceAbuse
Hallucination
```

---

# 69. SafetyPolicy

SafetyPolicy thuộc 639.

646 chỉ thực thi evaluation theo policy.

---

# 70. Safety test

```text id="k3z5p8"
SafetyTest {
    scenario
    expected_policy
    evaluator
}
```

---

# 71. Red-team scenario

```text id="m8k4q1"
RedTeamScenario {
    initial_state
    attack_input
    allowed_tools
    capability_scope
    expected_boundary
}
```

---

# 72. Red-team sandbox

Red-team test phải chạy trong sandbox.

---

# 73. Capability isolation

Test agent không được có quyền production mặc định.

---

# 74. Network isolation

Red-team execution có thể yêu cầu:

```text id="n0p8r4"
NoNetwork
AllowlistedNetwork
IsolatedNetwork
```

---

# 75. Filesystem isolation

Test filesystem phải được sandbox.

---

# 76. Tool isolation

644 tools có thể được mock hoặc simulator.

---

# 77. Prompt injection testing

646 có thể kiểm tra:

```text id="a8s7j2"
instruction hierarchy
untrusted content
retrieved documents
tool results
memory content
```

---

# 78. Agent boundary test

Kiểm tra agent không tự ý:

- mở capability mới;
- vượt tenant;
- bypass policy;
- gọi tool ngoài allowlist.

---

# 79. Tool-use evaluation

Metrics:

```text id="z9p4x2"
ToolSelectionAccuracy
ArgumentValidity
ToolCallCount
UnnecessaryToolCallRate
PolicyViolationRate
```

---

# 80. Agent trajectory

Evaluation có thể lưu:

```text id="q4c5m1"
messages
tool calls
tool results
state transitions
final answer
```

theo governance.

---

# 81. Secret redaction

Trajectory phải loại bỏ secret theo 602/603/638.

---

# 82. Long-horizon evaluation

Có thể chạy agent qua nhiều bước.

---

# 83. Step budget

Giới hạn:

```text id="f2p5d8"
max_steps
max_tool_calls
max_tokens
max_time
max_cost
```

---

# 84. Agent loop detection

Phát hiện:

- repeated tool call;
- repeated state;
- oscillation;
- no-progress loop.

---

# 85. Agent failure taxonomy

```text id="g6n0c5"
Timeout
ToolError
PolicyDenied
InvalidAction
LoopDetected
ContextOverflow
ModelError
EnvironmentError
```

---

# 86. RAG faithfulness

Có thể đánh giá:

- citation support;
- retrieved evidence coverage;
- answer-grounding;
- unsupported claim rate.

---

# 87. Citation verification

645/641 có thể kiểm tra evidence references.

---

# 88. Unsupported claim

Metric chỉ báo cáo claims không được evidence support.

---

# 89. Hallucination evaluation

Không dùng một định nghĩa duy nhất.

Test suite phải chỉ rõ:

```text id="p3r8m0"
what counts as unsupported
reference source
judge method
```

---

# 90. Knowledge graph evaluation

645 integration:

- entity resolution;
- relation extraction;
- graph completeness;
- consistency;
- provenance coverage.

---

# 91. Entity resolution metrics

```text id="n5d2x7"
Precision
Recall
F1
FalseMergeRate
FalseSplitRate
```

---

# 92. Graph extraction metrics

```text id="r6v1s9"
EntityPrecision
EntityRecall
RelationPrecision
RelationRecall
```

---

# 93. Model robustness

Test transformations:

```text id="4k8m2p"
noise
typos
format variation
ordering
missing fields
irrelevant context
distribution shift
```

---

# 94. Robustness budget

Transformation count and intensity are bounded.

---

# 95. Adversarial testing

Provider boundary for:

- adversarial examples;
- perturbations;
- malicious inputs;
- prompt attacks.

---

# 96. Adversarial test isolation

Adversarial generation must respect 603/639 capabilities.

---

# 97. Numerical correctness

Compare:

```text id="f6k2p4"
reference implementation
vs
native implementation
```

---

# 98. Numerical tolerance

Each operator specifies tolerance by dtype/backend.

---

# 99. Gradient validation

643 autodiff can be validated with:

```text id="n9s2q8"
finite_difference
analytical_reference
numerical_gradient
```

---

# 100. Gradient metrics

```text id="x2j5m8"
max_error
mean_error
relative_error
```

---

# 101. Model serialization validation

Save → load → evaluate.

---

# 102. Model portability test

Compare:

```text id="u6p3s1"
CPU
GPU
Accelerator
```

where semantics permit.

---

# 103. Cross-provider validation

Same model can be evaluated across providers.

---

# 104. Provider capability

Provider reports unsupported operations explicitly.

---

# 105. No silent fallback

If provider changes semantics, evaluation records it.

---

# 106. Quantization evaluation

Compare:

```text id="c5w8h0"
FP32
FP16
BF16
INT8
INT4
```

with explicit metric set.

---

# 107. Quantization report

Contains:

- accuracy difference;
- latency;
- memory;
- throughput;
- operator coverage.

---

# 108. Batch-size benchmark

Evaluate explicit batch sizes.

---

# 109. Sequence-length benchmark

For sequence models:

```text id="y5n8x2"
sequence_length
```

is part of benchmark identity.

---

# 110. Dynamic batching benchmark

Measures:

- queue delay;
- batching efficiency;
- latency;
- throughput.

---

# 111. Streaming benchmark

Measures:

- first-token/first-result latency;
- inter-result latency;
- completion throughput.

---

# 112. Distributed benchmark

Records:

```text id="c1n7k5"
node_count
worker_count
GPU_count
topology
communication_backend
```

---

# 113. Scaling metrics

```text id="m8s4v0"
strong_scaling
weak_scaling
parallel_efficiency
communication_overhead
```

---

# 114. Distributed correctness

Compare distributed output against reference where deterministic equivalence is defined.

---

# 115. Reduction-order sensitivity

Floating-point distributed reductions may have bounded numerical differences.

---

# 116. Reproducibility modes

```text id="r4q7j3"
Strict
Deterministic
Seeded
BestEffort
```

---

# 117. Strict reproducibility

Requires:

- same artifact;
- same dataset revision;
- same environment;
- same seed;
- same provider;
- same deterministic configuration.

---

# 118. Best-effort reproducibility

Allows provider/platform differences and records them.

---

# 119. Environment fingerprint

Contains:

```text id="d3m8q1"
OS
CPU
GPU
driver
Axiom version
compiler version
runtime version
provider versions
configuration
```

---

# 120. Experiment

```text id="p5r7n2"
Experiment {
    id
    objective
    dataset
    model
    evaluation_plan
}
```

---

# 121. ExperimentRun

Connects:

```text id="z2m9x4"
training
evaluation
metrics
artifacts
environment
```

---

# 122. Experiment lineage

640 records:

```text id="x8j1q5"
data
→ training
→ model
→ evaluation
→ deployment
```

---

# 123. Artifact references

Evaluation can attach:

- model;
- dataset;
- logs;
- traces;
- reports;
- failure cases.

---

# 124. Failure artifact

Stores minimal reproducible failure input where governance permits.

---

# 125. Failure deduplication

Failures can be fingerprinted.

---

# 126. Failure clustering

642 may cluster failures by:

- error;
- input pattern;
- model version;
- scenario.

---

# 127. Evaluation sampling

Sampling strategies:

```text id="q3x7m9"
Random
Stratified
Reservoir
Temporal
DeterministicHash
Full
```

---

# 128. Sample identity

Every sample must be reproducible from dataset revision + sampling configuration.

---

# 129. Evaluation budget

606 governs:

- CPU;
- GPU;
- RAM;
- VRAM;
- network;
- storage;
- runtime;
- concurrency.

---

# 130. Distributed evaluation

630 can distribute test cases.

---

# 131. Worker assignment

635 chooses placement.

---

# 132. Evaluation checkpoint

600 can checkpoint large evaluation runs.

---

# 133. Resume

Evaluation resumes from completed test-case boundaries.

---

# 134. Idempotency

Completed test cases are not duplicated unless explicitly rerun.

---

# 135. Event integration

634 emits:

```text id="n8y4m1"
EvaluationStarted
CaseStarted
CaseCompleted
MetricProduced
FailureDetected
EvaluationCompleted
GateEvaluated
```

---

# 136. Observability

633 records:

- evaluation latency;
- throughput;
- worker utilization;
- failures;
- resource consumption.

---

# 137. Diagnostics

602 records evaluation errors.

---

# 138. Security

603 protects:

- evaluation datasets;
- models;
- test artifacts;
- evaluator capabilities.

---

# 139. Policy

639 determines:

- whether evaluation may run;
- allowed datasets;
- allowed model;
- allowed environment;
- quality gate rules.

---

# 140. Governance

640 controls:

- data residency;
- retention;
- classification;
- lineage;
- deletion.

---

# 141. Credentials

638 handles private model/data credentials.

---

# 142. Network

609/626 provide remote evaluation data/model access.

---

# 143. Package

613/625 distribute benchmark suites and evaluator packages.

---

# 144. Plugin

623 allows external evaluator providers.

---

# 145. Script

624 may provide evaluation scripts under sandbox.

---

# 146. No arbitrary evaluator authority

Evaluator plugins receive explicit capabilities.

---

# 147. Evaluator provider

```text id="q7x4p1"
NativeEvaluator
ModelEvaluator
HumanEvaluator
ExternalEvaluator
TestEvaluator
```

---

# 148. Native metrics

Common metrics should be implemented natively where practical.

---

# 149. Custom metrics

Custom metrics must declare:

```text id="f1j8w5"
input_types
output_type
determinism
resource_bound
version
```

---

# 150. Custom metric safety

No arbitrary unbounded execution inside the core evaluator.

---

# 151. Metric versioning

Changing formula requires a new metric revision.

---

# 152. Report

EvaluationReport contains:

```text id="r8p2m6"
evaluation_id
target
dataset
metrics
comparisons
failures
gates
environment
lineage
```

---

# 153. Report immutability

Final report is immutable.

---

# 154. Machine-readable report

Native format:

```text id="v3n7c2"
.axeval
```

---

# 155. Human-readable report

CLI/UI can render:

- summary;
- metrics;
- failures;
- regressions;
- environment;
- provenance.

---

# 156. No overall score

646 does not require a single aggregate "AI quality score".

Applications may define domain-specific composite metrics.

---

# 157. Composite metric

If used, it must explicitly expose:

```text id="m2q9k4"
components
weights
formula
version
```

---

# 158. Quality gate composition

Gate policy can require:

```text id="z4x7p1"
accuracy >= threshold
AND
latency <= threshold
AND
safety_violation_rate <= threshold
```

---

# 159. Gate independence

Each metric remains visible.

---

# 160. No hidden normalization

Metric transformations must be explicit.

---

# 161. Benchmark suite

BenchmarkSuite groups immutable benchmark definitions.

---

# 162. Benchmark version

Every suite has version/fingerprint.

---

# 163. Compatibility

New suite versions do not overwrite old results.

---

# 164. Standard benchmark adapter

External benchmark formats may be imported.

---

# 165. Benchmark fairness

646 records population and test conditions rather than declaring an unconditional winner.

---

# 166. Model comparison

Reports can show side-by-side:

```text id="b7q3m8"
metric
candidate
baseline
difference
uncertainty
population
```

---

# 167. Difference semantics

Difference formula is explicit.

---

# 168. Regression dashboard

UI can visualize historical metrics without altering source data.

---

# 169. Historical trend

Trend records:

```text id="q8x1c5"
evaluation revision
model revision
dataset revision
metric result
```

---

# 170. Drift monitoring

633 production telemetry can trigger evaluation requests.

---

# 171. Evaluation trigger

Possible triggers:

```text id="k4m8z2"
ModelUpdated
DatasetUpdated
PolicyUpdated
DeploymentCandidate
Scheduled
Manual
TelemetryThreshold
```

---

# 172. Trigger does not equal deployment

Evaluation completion does not automatically deploy a model.

---

# 173. Deployment integration

636 can consume a gate result as one input to deployment policy.

---

# 174. Canary evaluation

636 can route a controlled evaluation cohort.

---

# 175. Shadow evaluation

632 can mirror requests into evaluation environment.

---

# 176. Production sampling

Production samples must obey 640 privacy/governance.

---

# 177. Online evaluation

Metrics can be computed continuously.

---

# 178. Offline evaluation

Full dataset evaluation remains supported.

---

# 179. Human feedback

644 may produce feedback events.

---

# 180. Feedback evaluation

Feedback can be converted into immutable labeled datasets.

---

# 181. Feedback provenance

Every label retains:

```text id="j2v8x7"
source
timestamp
schema
reviewer
policy
```

---

# 182. Preference evaluation

Pairwise preferences are represented without forcing a global ranking.

---

# 183. A/B evaluation

646 can evaluate two predefined variants.

---

# 184. A/B identity

Experiment includes:

```text id="y7p4q2"
variant allocation
population
period
metric definitions
```

---

# 185. No automatic winner selection

646 reports measured differences.

---

# 186. Statistical uncertainty

A/B results may include confidence intervals.

---

# 187. Sequential evaluation

Repeated evaluation must record sampling procedure to avoid misleading aggregation.

---

# 188. Multiple comparisons

Evaluation metadata may declare correction methods.

---

# 189. Evaluation reproducibility manifest

```text id="n6w3p8"
dataset_hash
model_hash
code_hash
plan_hash
environment_hash
seed
provider_versions
```

---

# 190. Reproduction command

CLI can generate:

```text id="c8m5z1"
axiom eval reproduce <evaluation-id>
```

---

# 191. Test isolation

Each test may have isolated:

- filesystem;
- network;
- environment;
- process;
- credentials;
- model cache.

---

# 192. Time control

Evaluation can use deterministic virtual clock.

---

# 193. Random control

Evaluation can use deterministic RNG provider.

---

# 194. Fault injection

Supported faults:

```text id="q2j7m5"
timeout
network_failure
device_loss
memory_pressure
worker_loss
corrupt_model
corrupt_dataset
policy_denial
service_unavailable
```

---

# 195. Chaos evaluation

630/635 can deliberately terminate workers within sandbox.

---

# 196. Recovery evaluation

Test:

```text id="f8n4k2"
checkpoint
worker failure
resume
result consistency
```

---

# 197. Model corruption test

Model artifact checksum/signature must be validated.

---

# 198. Unsafe model loading

Untrusted model formats cannot execute arbitrary code.

---

# 199. Custom operator testing

Custom operators require explicit capability and sandbox policy.

---

# 200. Prompt test corpus

644 prompts can be stored as immutable dataset revisions.

---

# 201. Prompt category metadata

```text id="m1x8q4"
normal
ambiguous
adversarial
injection
tool_use
long_context
multilingual
```

---

# 202. Multilingual evaluation

646 supports:

- language;
- locale;
- script;
- tokenizer;
- normalization.

---

# 203. Language-specific metrics

Evaluator providers may define:

```text id="p7c3v1"
BLEU-like
ROUGE-like
chrF-like
token_accuracy
WER
CER
```

when appropriate.

---

# 204. Speech/vision evaluation

646 can consume outputs from:

- 616 media;
- 643 models.

---

# 205. ASR evaluation

Metrics:

```text id="h3n7q5"
WER
CER
speaker_attribution
timestamp_error
```

---

# 206. TTS evaluation

Possible measurements:

- intelligibility;
- pronunciation;
- latency;
- duration;
- signal quality;
- speaker similarity;
- human ratings.

No single metric is authoritative.

---

# 207. Vision evaluation

Metrics can include:

- classification accuracy;
- precision;
- recall;
- IoU;
- mAP;
- OCR error.

---

# 208. Multimodal evaluation

A test case may contain:

```text id="v4m8s2"
text
audio
image
video
structured_context
```

---

# 209. Multimodal lineage

Each modality keeps independent source references.

---

# 210. Context-length evaluation

646 measures:

```text id="z7q3n5"
input_tokens
context_tokens
output_tokens
truncation
latency
memory
```

---

# 211. Context truncation

Silent truncation is recorded as an evaluation event.

---

# 212. Token accounting

643/model provider reports actual tokenization where available.

---

# 213. Generation evaluation

For generative models:

```text id="m5x9q1"
sampling_config
temperature
top_k
top_p
seed
max_tokens
```

is part of evaluation identity.

---

# 214. Sampling reproducibility

Provider must report whether seed guarantees reproducibility.

---

# 215. Evaluation environment isolation

Different provider versions cannot silently share a result fingerprint.

---

# 216. Model serving evaluation

631/632 integration measures:

- queue latency;
- routing;
- load;
- failover;
- timeout;
- concurrency.

---

# 217. Deployment evaluation

636 can execute evaluation before:

```text id="g8q4m2"
Rolling
Canary
BlueGreen
```

but deployment policy decides activation.

---

# 218. Quality gate lifecycle

```text id="r5v8x1"
Defined
→ Validating
→ Evaluating
→ Passed
→ Failed
→ Unknown
→ Superseded
```

---

# 219. Gate revision

Changing threshold creates new gate revision.

---

# 220. Gate audit

Every gate decision records:

```text id="y4n7k3"
policy_revision
evaluation_revision
metric_revision
timestamp
actor
```

---

# 221. Policy binding

Gate cannot weaken 603/639 security controls.

---

# 222. Governance binding

Evaluation cannot access data outside 640 permissions.

---

# 223. Privacy

Sensitive evaluation data must be classified.

---

# 224. Retention

Evaluation artifacts have explicit retention.

---

# 225. Redaction

Reports can redact:

- prompts;
- outputs;
- PII;
- secrets;
- proprietary data.

---

# 226. Differential privacy boundary

646 can consume DP results from provider, but DP is not silently applied.

---

# 227. Secure evaluation

Sensitive model evaluation may use isolated workers.

---

# 228. Evaluation credentials

Temporary credentials use 638 leases.

---

# 229. Credential expiration

Long-running evaluations must renew credentials or fail explicitly.

---

# 230. Evaluation resource quotas

Per:

- experiment;
- tenant;
- model;
- dataset;
- user;
- project.

---

# 231. Evaluation scheduler

607 handles local scheduling.

630 handles distributed workers.

635 handles placement.

---

# 232. Evaluation queue

Large suites use durable work queues.

---

# 233. Retry

Test execution retry policy is explicit.

---

# 234. Retry idempotency

A test case has deterministic identity.

---

# 235. Duplicate prevention

Completed case result can be reused only if environment fingerprint matches.

---

# 236. Partial evaluation

A run can finish partially.

---

# 237. Resume semantics

Only completed test cases are skipped.

---

# 238. Failed evaluation

A failed infrastructure execution is distinct from a model failure.

---

# 239. Failure taxonomy

```text id="w4q8m1"
TestFailure
ModelFailure
EvaluatorFailure
InfrastructureFailure
PolicyFailure
GovernanceFailure
ResourceFailure
```

---

# 240. Explainability

646 can explain:

```text id="k7m2x9"
why metric failed
why gate failed
which cases failed
which evaluator produced result
```

---

# 241. Case-level evidence

Metrics must be traceable to cases where feasible.

---

# 242. Aggregate evidence

Large datasets may retain aggregate references instead of every case.

---

# 243. Sampling evidence

If sampled, sample method is recorded.

---

# 244. Missing data

Missing evaluation cases are explicit.

---

# 245. Coverage

Report:

```text id="p4x7m8"
cases_total
cases_executed
cases_skipped
cases_failed
coverage
```

---

# 246. Coverage semantics

Coverage is not synonymous with correctness.

---

# 247. Test suite dependency

Suites can declare:

```text id="z5n8q2"
required_model_capabilities
required_device
required_dataset_schema
```

---

# 248. Compatibility matrix

646 can generate:

```text id="m8q1v5"
model × provider × device × dataset
```

evaluation matrix.

---

# 249. Matrix execution

Each cell is an independent EvaluationRun.

---

# 250. Matrix failures

One failed cell does not corrupt unrelated cells.

---

# 251. Benchmark artifact

`.axbench`

Contains:

```text id="x4p7m2"
benchmark_definition
dataset_ref
metric_definitions
environment_requirements
```

---

# 252. Evaluation artifact

`.axeval`

Contains:

```text id="q8m3v1"
evaluation_plan
run
metrics
failures
gates
lineage
environment
```

---

# 253. Safety artifact

`.axsafety`

Contains:

```text id="k5n2x7"
safety_policy_ref
scenarios
capabilities
results
```

---

# 254. Regression artifact

`.axregression`

Contains:

```text id="p7m4q8"
baseline
candidate
metrics
thresholds
results
```

---

# 255. Compiler annotations

```text id="g2x8m5"
@evaluation
@benchmark
@metric
@test
@test_suite
@dataset
@baseline
@regression
@quality_gate
@safety_test
@red_team
@judge
@human_eval
@deterministic
@seed
@resource_budget
@reproducible
```

---

# 256. Generated metadata

```text id="v5q9n3"
.axeval
.axbench
.axmetric
.axtest
.axsuite
.axgate
.axsafety
.axregression
```

---

# 257. Struct-only API

Core API:

```text id="f8m2k6"
EvaluationEngine
EvaluationPlan
EvaluationRun
TestSuite
TestCase
Metric
Evaluator
Benchmark
QualityGate
EvaluationReport
```

không yêu cầu class inheritance.

---

# 258. Example

```text id="n3x7p1"
@test
fn addition_case() -> TestCase {
    input: [2, 3],
    expected: 5
}
```

---

# 259. Model evaluation

```text id="q4m8v2"
evaluate(
    model,
    dataset,
    metrics
)
```

---

# 260. Benchmark

```text id="j7x2n5"
benchmark(
    model,
    workload,
    environment
)
```

---

# 261. Quality gate

```text id="m5p8q3"
gate {
    accuracy >= 0.95
    latency.p95 <= 50ms
}
```

---

# 262. Agent evaluation

```text id="x8n4k1"
evaluate_agent(
    agent,
    scenario_suite,
    safety_policy
)
```

---

# 263. RAG evaluation

```text id="q3v7m9"
evaluate_rag(
    retriever,
    knowledge_graph,
    corpus,
    answer_model
)
```

---

# 264. Reproduction

```text id="k1x5p8"
axiom eval reproduce EVAL-123
```

---

# 265. Explain

```text id="n7m4q2"
axiom eval explain EVAL-123
```

---

# 266. Compare

```text id="v8p2k5"
axiom eval compare EVAL-A EVAL-B
```

---

# 267. Failure extraction

```text id="q6m9x3"
axiom eval failures EVAL-123
```

---

# 268. Regression check

```text id="j4p8n1"
axiom eval regression EVAL-123
```

---

# 269. Security test command

```text id="x5q7m2"
axiom eval safety EVAL-123
```

---

# 270. Benchmark command

```text id="m3v8k5"
axiom eval benchmark BENCH-123
```

---

# 271. Integration with 643

643 provides:

- model execution;
- tensor execution;
- training state;
- model artifacts;
- inference;
- device information.

646 validates them.

---

# 272. Integration with 644

644 provides:

- agent execution;
- tool traces;
- memory;
- planning;
- actions.

646 evaluates them.

---

# 273. Integration with 645

645 provides:

- knowledge;
- entities;
- relations;
- provenance;
- graph snapshots.

646 evaluates knowledge retrieval/extraction.

---

# 274. Integration with 641

641 provides:

- retrieval;
- ranking;
- vector search;
- lexical search.

646 evaluates retrieval quality.

---

# 275. Integration with 642

642 provides:

- aggregations;
- statistics;
- DataFrame;
- analytical execution.

646 uses it for metric calculation.

---

# 276. Integration with 633

633 provides:

- telemetry;
- tracing;
- profiling.

646 correlates evaluation metrics with runtime behavior.

---

# 277. Integration with 636

636 can use gate results as deployment inputs.

---

# 278. Integration with 639

639 defines authorization and operational policy.

---

# 279. Integration with 640

640 defines data governance.

---

# 280. Integration with 606

606 enforces evaluation budgets.

---

# 281. Integration with 630

630 distributes large evaluation workloads.

---

# 282. Integration with 635

635 chooses worker placement.

---

# 283. Integration with 634

634 transports evaluation events.

---

# 284. Integration with 600

600 checkpoints long evaluation runs.

---

# 285. Integration with 612

612 serializes evaluation schemas/results.

---

# 286. Integration with 613

613 packages benchmark/evaluation artifacts.

---

# 287. Integration with 638

638 supplies temporary credentials.

---

# 288. External evaluator boundary

External evaluation frameworks may be connected through:

```text id="x1m7q5"
ExternalEvaluatorProvider
```

without becoming runtime dependencies.

---

# 289. No mandatory ML ecosystem

Core Axiom evaluation must work without:

- Python;
- NumPy;
- PyTorch;
- TensorFlow;
- JAX;
- MLflow;
- Weights & Biases.

---

# 290. Native implementation strategy

Use:

```text id="p8v3k1"
typed execution
SIMD
parallel workers
streaming
bounded memory
generated evaluators
```

---

# 291. Zero-copy evaluation

Possible when model and dataset memory layouts are compatible.

---

# 292. Batch evaluation

Cases are grouped into batches where safe.

---

# 293. Vectorized metrics

642 can execute metric aggregation over batches.

---

# 294. GPU metrics

643 can execute tensor-heavy metrics.

---

# 295. CPU metrics

Simple metrics should remain CPU-native.

---

# 296. Evaluation compilation

Static test suites can be compiled into native execution plans.

---

# 297. Test specialization

Known schema allows:

- type specialization;
- branch elimination;
- SIMD;
- batch fusion.

---

# 298. Dynamic evaluator

Dynamic evaluator remains available for evolving schemas.

---

# 299. No hidden allocation

Simple metrics should not require per-sample heap allocation.

---

# 300. Evaluation performance target

Native evaluation overhead should be small relative to model execution for normal workloads.

---

# 301. Deterministic ordering

Evaluation result ordering can be deterministic.

---

# 302. Parallel reduction

Parallel metric reductions specify numerical semantics.

---

# 303. Floating-point reproducibility

Strict mode may require deterministic reduction order.

---

# 304. Approximate metrics

Approximation metadata includes:

```text id="b3x7m2"
algorithm
sample_size
error_bound
confidence
```

where available.

---

# 305. Metric failure

If metric cannot be computed:

```text id="n5q8k1"
MetricUnavailable
```

rather than zero.

---

# 306. No silent zero

Unavailable metric must never become `0`.

---

# 307. Invalid case

Invalid test input is distinct from failed model output.

---

# 308. Skip reason

Every skipped case has reason.

---

# 309. Evaluation state machine

```text id="v7m2p4"
Created
→ Validating
→ Queued
→ Running
→ Checkpointing
→ Completed
```

Failure states:

```text id="x8q5n1"
Failed
Cancelled
TimedOut
PolicyBlocked
GovernanceBlocked
```

---

# 310. Cancellation

Cancellation is cooperative where possible.

---

# 311. Force termination

Supervisor 605 may terminate isolated evaluation workers.

---

# 312. Evaluation worker

Worker identity integrates with 630/635/605.

---

# 313. Worker crash

Completed case results remain durable.

---

# 314. Worker recovery

Unfinished cases are rescheduled.

---

# 315. Duplicate result handling

Case identity + execution revision prevents ambiguous duplicates.

---

# 316. Exactly-once semantics

Not assumed across distributed infrastructure.

---

# 317. Idempotent result commit

Result commits use compare-and-swap/version checks.

---

# 318. Evaluation history

Historical evaluations remain queryable according to retention.

---

# 319. Artifact retention

Retention is controlled by 640.

---

# 320. Deletion

Deletion follows governance and may require removing:

- raw cases;
- outputs;
- reports;
- derived metrics;
- cached artifacts.

---

# 321. Lineage deletion

Lineage records may remain as permitted metadata after payload deletion.

---

# 322. Privacy-preserving report

Report can contain only:

```text id="m6x2q8"
aggregate metrics
failure fingerprints
non-sensitive evidence references
```

---

# 323. Sensitive output access

Requires explicit capability.

---

# 324. Evaluation namespace

All artifacts exist within:

```text id="q4n7m1"
tenant
project
experiment
```

---

# 325. Tenant isolation

Cross-tenant comparison is denied unless explicitly permitted.

---

# 326. Cross-model comparison

Permitted only when policy allows access to both artifacts.

---

# 327. Cross-dataset comparison

Report must preserve different population identities.

---

# 328. Benchmark portability

Benchmark definitions should be portable across platforms.

---

# 329. Environment constraints

Benchmark may declare minimum:

```text id="k8m3x5"
CPU features
GPU features
memory
driver/provider
```

---

# 330. Unsupported environment

Result:

```text id="v2p7q4"
NotRunnable
```

rather than misleading failure.

---

# 331. Evaluation matrix example

```text id="n5x8m2"
Model A × CPU
Model A × GPU
Model B × CPU
Model B × GPU
```

Each cell remains independently reproducible.

---

# 332. AI-readable quality metadata

Agents can inspect:

```text id="q7m4p1"
metric definitions
dataset revision
failure taxonomy
gate state
environment
provenance
```

---

# 333. Agent decision boundary

644 may consume evaluation evidence, but 646 does not instruct the agent to make an arbitrary deployment decision.

---

# 334. Policy decision boundary

639 determines whether a gate result is sufficient for a policy.

---

# 335. Deployment decision boundary

636 determines rollout mechanics.

---

# 336. Evaluation evidence chain

```text id="x8q3m5"
Dataset
   ↓
EvaluationPlan
   ↓
EvaluationRun
   ↓
Cases
   ↓
Metrics
   ↓
QualityGate
   ↓
Report
```

---

# 337. Full AI quality chain

```text id="p4n8x2"
Data
 ↓
Governance
 ↓
Model
 ↓
Agent
 ↓
Evaluation
 ↓
Policy
 ↓
Deployment
 ↓
Telemetry
 ↓
Re-evaluation
```

---

# 338. Core invariants

1. Evaluation runs are uniquely identified.
2. Finalized results are immutable.
3. Dataset revision is explicit.
4. Model revision is explicit.
5. Environment is fingerprinted.
6. Randomness is explicit.
7. Sampling is reproducible.
8. Metrics are versioned.
9. Metric formulas are explicit.
10. Missing metrics are not zero.
11. Invalid cases are not model failures.
12. Infrastructure failures are distinct from model failures.
13. Partial runs are explicit.
14. Skipped cases have reasons.
15. Quality gates are versioned.
16. Gate decisions are auditable.
17. No hidden aggregate quality score.
18. No automatic model winner selection.
19. No automatic deployment from evaluation alone.
20. Model-as-judge results are labeled.
21. Human judgments have provenance.
22. Ground truth has provenance.
23. RAG evaluation records retrieval revision.
24. Graph evaluation records graph revision.
25. Agent evaluation records tool/policy state.
26. Safety tests execute in isolation.
27. Red-team tests cannot inherit production authority.
28. Test credentials are scoped.
29. Evaluation consumes resource budgets.
30. Evaluation supports cancellation.
31. Evaluation supports checkpoint/resume.
32. Worker failures cannot erase completed cases.
33. Duplicate results are detected.
34. Distributed exactly-once is not assumed.
35. Evaluation artifacts respect governance.
36. Sensitive outputs are protected.
37. Secrets are never stored unredacted.
38. Model artifacts are integrity-checked.
39. Untrusted models cannot execute arbitrary code.
40. Custom evaluators are capability-bound.
41. Query/evaluation plans are deterministic where declared.
42. Floating-point tolerances are explicit.
43. Approximate metrics expose approximation metadata.
44. Benchmark conditions are recorded.
45. Comparison population is explicit.
46. Regression thresholds are explicit.
47. Unknown gate state is distinct from Pass.
48. Security policy cannot be weakened by evaluation.
49. Governance cannot be bypassed by benchmark code.
50. Evaluation cannot mint capabilities.
51. External providers cannot expand authority.
52. Native API remains provider-independent.
53. Evaluation lineage is preserved.
54. Model lineage is preserved.
55. Dataset lineage is preserved.
56. Failure artifacts have provenance.
57. Historical results remain versioned.
58. Deletion follows retention policy.
59. Cross-tenant evaluation is explicitly authorized.
60. Evaluation output cannot be treated as universal truth.

---

# 339. Acceptance criteria

**Target: ≥500 acceptance criteria**

Các nhóm bắt buộc:

- evaluation lifecycle;
- dataset validation;
- schema validation;
- sampling;
- test cases;
- test suites;
- exact comparison;
- numerical tolerance;
- structured comparison;
- semantic evaluation;
- metrics;
- aggregation;
- confidence intervals;
- benchmarks;
- latency;
- throughput;
- memory;
- startup;
- device;
- distributed scaling;
- reproducibility;
- deterministic execution;
- regression;
- quality gates;
- RAG;
- retrieval;
- knowledge graph;
- entity resolution;
- agent;
- tool use;
- long-horizon execution;
- prompt injection;
- red-team;
- safety;
- adversarial robustness;
- multilingual;
- multimodal;
- ASR;
- TTS;
- vision;
- model serialization;
- model portability;
- quantization;
- provider comparison;
- experiment lineage;
- artifact management;
- failure reproduction;
- fault injection;
- checkpoint/resume;
- worker crash;
- security;
- capability isolation;
- governance;
- privacy;
- retention;
- distributed execution;
- performance;
- fuzzing;
- property testing;
- deterministic simulator.

---

# 340. Profiles

```text id="k8x3m7"
AXEVAL_NONE
AXEVAL_CORE
AXEVAL_DATA
AXEVAL_TEST
AXEVAL_METRIC
AXEVAL_BENCH
AXEVAL_REGRESSION
AXEVAL_MODEL
AXEVAL_RAG
AXEVAL_AGENT
AXEVAL_SAFETY
AXEVAL_REDTEAM
AXEVAL_DISTRIBUTED
AXEVAL_HUMAN
AXEVAL_FULL
```

---

# 341. Minimal profile

`AXEVAL_CORE` chỉ cần:

```text id="n4p7q2"
TestCase
TestSuite
Evaluator
Metric
EvaluationRun
Report
```

---

# 342. AI profile

`AXEVAL_AGENT` bổ sung:

```text id="x5m8k1"
agent traces
tool evaluation
RAG
knowledge evaluation
safety scenarios
```

---

# 343. Benchmark profile

`AXEVAL_BENCH` tối ưu cho:

```text id="q7n3m5"
latency
throughput
memory
startup
scaling
device
```

---

# 344. Full profile

`AXEVAL_FULL` kết hợp:

```text id="m2x8p4"
evaluation
benchmark
regression
safety
red-team
human evaluation
distributed evaluation
AI agent evaluation
```

---

# 345. Final architecture

```text id="v8q3m1"
                     AXIOM AI QUALITY PLANE

                         Model / Agent
                              │
               ┌──────────────┼──────────────┐
               ▼              ▼              ▼
             643            644            645
             ML             Agent         Knowledge
               │              │              │
               └──────────────┼──────────────┘
                              ▼
                         ┌───────────┐
                         │   646     │
                         │ Evaluation│
                         └─────┬─────┘
                               │
          ┌────────────────────┼────────────────────┐
          ▼                    ▼                    ▼
      Dataset               Metrics             Test Suite
          │                    │                    │
          └────────────────────┼────────────────────┘
                               ▼
                       Evaluation Engine
                               │
          ┌────────────────────┼────────────────────┐
          ▼                    ▼                    ▼
     Correctness            Safety             Benchmark
          │                    │                    │
          └────────────────────┼────────────────────┘
                               ▼
                         Quality Gates
                               │
             ┌─────────────────┼─────────────────┐
             ▼                 ▼                 ▼
            633               639               636
       Observability         Policy          Deployment
             │                 │                 │
             └─────────────────┼─────────────────┘
                               ▼
                          640 Governance
```

---

# 346. Kết quả kiến trúc

Sau BOOTSTRAP-646, Axiom có chuỗi hoàn chỉnh:

```text
Data
 ↓
Storage
 ↓
Search / Analytics
 ↓
Knowledge
 ↓
Tensor / ML
 ↓
AI Agent
 ↓
Evaluation
 ↓
Policy
 ↓
Deployment
 ↓
Telemetry
 ↓
Continuous Re-evaluation
```

Axiom vì vậy không chỉ có khả năng **chạy AI**, mà còn có native infrastructure để:

- kiểm thử AI;
- benchmark AI;
- tái hiện lỗi;
- kiểm tra regression;
- đánh giá RAG;
- đánh giá agent;
- kiểm tra tool-use;
- kiểm tra robustness;
- chạy safety/red-team trong sandbox;
- kiểm tra distributed execution;
- duy trì lineage từ data → model → evaluation → deployment.

---

# 347. Trạng thái

**BOOTSTRAP-646 — COMPLETE**

### Task kế tiếp

**BOOTSTRAP-647 — Native AI Model Registry, Artifact Lineage, Model Lifecycle, Model Packaging, Versioning, Promotion, Serving Catalog & Model Supply-Chain Runtime 5.0**
:::