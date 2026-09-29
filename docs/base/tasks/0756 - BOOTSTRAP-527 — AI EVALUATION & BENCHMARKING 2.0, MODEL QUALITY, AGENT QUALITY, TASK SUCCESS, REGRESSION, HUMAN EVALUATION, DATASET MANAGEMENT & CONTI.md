# BOOTSTRAP-527 — AI EVALUATION & BENCHMARKING 2.0, MODEL QUALITY, AGENT QUALITY, TASK SUCCESS, REGRESSION, HUMAN EVALUATION, DATASET MANAGEMENT & CONTINUOUS AI EVALUATION

**Trạng thái: COMPLETED / LOCKED**

527 xây dựng tầng đánh giá AI phía trên 503–526. Mục tiêu là biến việc đánh giá model/agent từ một tập vài metric đơn lẻ thành một **evaluation framework có dataset, scenario, oracle, execution trace, reproducibility, regression detection và provenance**.

Điểm thiết kế trung tâm:

```text id="527arch"
              Model / Agent / Workflow
                       │
                       ↓
                Evaluation Spec
                       │
             ┌─────────┼─────────┐
             ↓         ↓         ↓
          Dataset   Scenarios   Policies
             │         │         │
             └─────────┼─────────┘
                       ↓
                 Evaluation Run
                       │
        ┌──────────────┼──────────────┐
        ↓              ↓              ↓
    Exact Oracle   Reference       Human Judge
        │           Model              │
        └──────────────┼──────────────┘
                       ↓
                  Measurements
                       │
                Analysis / Diff
                       │
             ┌─────────┴─────────┐
             ↓                   ↓
        Regression            Report
```

---

# 527.1 — Evaluation ≠ Benchmark

**Benchmark** đo performance hoặc behavior trên workload xác định.

**Evaluation** rộng hơn: xác định model/agent có đáp ứng một tập yêu cầu hay không.

## 527.2 — Evaluation ≠ Training

Evaluation không được vô tình trở thành training data pipeline.

## 527.3 — Evaluation ≠ Production Monitoring

Production monitoring đo hệ thống đang chạy.

Evaluation chạy workload có chủ đích để đo behavior.

## 527.4 — Evaluation identity

```text id="evalid"
EvaluationId
Version
DefinitionHash
```

## 527.5 — Evaluation run

```text id="evalrun"
EvaluationRunId
EvaluationId
ModelId
AgentId?
WorkflowId?
BuildId
Environment
```

---

# DATASET MODEL

## 527.6 — Evaluation dataset

Dataset là tập các evaluation cases.

## 527.7 — Case

```text id="case"
EvaluationCase {
    id
    input
    expected?
    metadata
    constraints
    provenance
}
```

## 527.8 — Dataset identity

Dataset có immutable identity/version.

## 527.9 — Dataset hash

Content hash dùng cho reproducibility.

## 527.10 — Dataset provenance

Nguồn tạo dataset phải được record.

## 527.11 — Dataset split

Hỗ trợ:

```text id="j5g4cz"
development
validation
test
challenge
regression
production-sample
```

## 527.12 — Hidden test set

Evaluation framework hỗ trợ dataset không expose expected outputs cho evaluated system.

## 527.13 — Versioning

Dataset mutation tạo version mới.

## 527.14 — Sampling

Random sampling phải có seed/configuration.

## 527.15 — Stratification

Evaluation dataset có thể stratify theo metadata.

## 527.16 — Filtering

Filters phải được lưu trong evaluation definition.

## 527.17 — Deduplication

Duplicate cases có thể được detect.

## 527.18 — Leakage detection

Dataset tooling có thể phát hiện potential train/evaluation overlap khi có metadata phù hợp.

## 527.19 — Sensitive data

Dataset access control được enforce.

## 527.20 — Dataset artifact

Dataset có thể là source, database query, generated cases hoặc immutable artifact.

---

# EVALUATION SCENARIO

## 527.21 — Scenario

Scenario mô tả execution environment của một case.

```text id="scenario"
Scenario {
    inputs
    tools
    memory
    retrieval
    policy
    environment
    limits
}
```

## 527.22 — Model configuration

Exact model/generation configuration được pin.

## 527.23 — Tool configuration

Tool identity/version/capability được pin.

## 527.24 — Memory state

Memory snapshot có thể được pin.

## 527.25 — Retrieval state

Retrieval index/version/configuration được pin.

## 527.26 — Policy

Safety/agent policy version được pin.

## 527.27 — Environment

OS/device/backend/runtime configuration được record.

## 527.28 — Resource limits

CPU/GPU/RAM/time/token limits explicit.

## 527.29 — Network

Network access policy explicit.

## 527.30 — Deterministic mode

Evaluation có thể chạy deterministic mode.

---

# ORACLE

## 527.31 — Oracle

Oracle xác định cách đánh giá output.

## 527.32 — Exact oracle

So sánh exact output.

## 527.33 — Normalized oracle

Normalization được định nghĩa trước khi compare.

## 527.34 — Structured oracle

Compare structured fields.

## 527.35 — Property oracle

Kiểm tra properties/invariants.

## 527.36 — Contract oracle

Dùng contracts từ 479.

## 527.37 — Test oracle

Chạy test suite.

## 527.38 — Reference implementation

Reference implementation có thể tạo expected behavior.

## 527.39 — Reference model

Reference model có thể dùng làm comparison baseline.

## 527.40 — Human oracle

Human evaluation được hỗ trợ.

---

# MODEL EVALUATION

## 527.41 — Classification

Metrics có thể gồm accuracy, precision, recall, F-score, confusion matrix khi task phù hợp.

## 527.42 — Regression

MAE/MSE/RMSE/R² hoặc metric domain-specific.

## 527.43 — Generation

Có thể đo:

- exact match;
- structured validity;
- task-specific correctness;
- reference similarity;
- human evaluation.

## 527.44 — Embedding

Similarity/retrieval metrics.

## 527.45 — Retrieval

Recall@k, precision@k, MRR, nDCG hoặc metric phù hợp.

## 527.46 — Ranking

Pairwise/listwise evaluation.

## 527.47 — Speech

Word/character error metrics, timing/error metrics khi task phù hợp.

## 527.48 — Vision

Detection/segmentation/classification metrics theo task.

## 527.49 — Multimodal

Cross-modal retrieval/alignment/task-specific metrics.

## 527.50 — No universal metric

Không có metric AI duy nhất phù hợp cho mọi model.

---

# AGENT EVALUATION

## 527.51 — Task success

Agent evaluation có thể đo task completion theo explicit success criteria.

## 527.52 — Partial success

Partial completion được represent.

## 527.53 — Tool correctness

Tool selection/arguments/results có thể evaluate.

## 527.54 — Planning

Plan structure có thể evaluate.

## 527.55 — Recovery

Retry/recovery behavior có thể evaluate.

## 527.56 — Policy compliance

Agent actions có thể kiểm tra policy compliance.

## 527.57 — Capability compliance

Agent chỉ được dùng declared capabilities.

## 527.58 — Resource compliance

Token/time/memory/cost limits được measure.

## 527.59 — Efficiency

Step count/tool count/model calls có thể measure.

## 527.60 — Robustness

Agent có thể test dưới failure/perturbation.

---

# WORKFLOW EVALUATION

## 527.61 — End-to-end

Evaluate toàn workflow.

## 527.62 — Step-level

Evaluate từng step.

## 527.63 — Dependency correctness

Kiểm tra dependency ordering.

## 527.64 — Checkpoint recovery

Kill/restart simulation.

## 527.65 — Failure injection

Inject:

- tool failure;
- timeout;
- network failure;
- worker crash;
- stale data;
- malformed output.

## 527.66 — Compensation

Evaluate compensation behavior.

## 527.67 — Human approval

Evaluate approval/rejection paths.

## 527.68 — Long-running execution

Evaluate resume sau process restart.

## 527.69 — Distributed execution

Evaluate worker/network failure.

## 527.70 — Deterministic simulation

Integrate deterministic scheduler/time từ 471/474.

---

# HUMAN EVALUATION

## 527.71 — Human rating

Human có thể đánh giá output.

## 527.72 — Rubric

Rubric phải explicit.

## 527.73 — Blind evaluation

Evaluator có thể không biết model identity.

## 527.74 — Pairwise comparison

Có thể compare two outputs mà không biến kết quả thành universal model ranking.

## 527.75 — Multiple evaluators

Nhiều evaluator được hỗ trợ.

## 527.76 — Inter-rater agreement

Có thể measure agreement.

## 527.77 — Rater metadata

Evaluator identity/role có thể được privacy-preserving metadata.

## 527.78 — Annotation provenance

Mỗi annotation có provenance.

## 527.79 — Adjudication

Conflicting annotations có thể adjudicate.

## 527.80 — Human comments

Free-form comments được distinguish khỏi machine metrics.

---

# LLM-AS-JUDGE

## 527.81 — Model judge

Một model có thể được sử dụng như evaluator.

## 527.82 — Judge identity

Judge model/version/config được record.

## 527.83 — Judge prompt

Evaluation prompt/version được record.

## 527.84 — Judge bias

Potential judge bias phải được document.

## 527.85 — Calibration

Judge có thể calibrate trên human-labeled examples.

## 527.86 — Agreement

Judge-human agreement có thể đo.

## 527.87 — Multiple judges

Có thể sử dụng nhiều independent judge configurations.

## 527.88 — Structured verdict

Judge output phải parse vào schema.

## 527.89 — Evidence requirement

Judge có thể yêu cầu evidence/rationale references.

## 527.90 — No automatic truth

Judge output không được coi là ground truth tuyệt đối.

---

# ROBUSTNESS

## 527.91 — Input perturbation

Case có thể biến đổi có kiểm soát.

## 527.92 — Adversarial evaluation

Security/testing layer có thể cung cấp adversarial cases.

## 527.93 — Distribution shift

Dataset có thể represent shifted distributions.

## 527.94 — Missing data

Optional/missing inputs.

## 527.95 — Corrupted data

Malformed/noisy inputs.

## 527.96 — Boundary cases

Extreme input sizes/values.

## 527.97 — Long context

524 integration.

## 527.98 — Tool failure

513/526 integration.

## 527.99 — Model failure

Timeout/OOM/device loss.

## 527.100 — Recovery measurement

Recovery success/time/attempts được record.

---

# REGRESSION

## 527.101 — Baseline

Evaluation run có thể compare với baseline run.

## 527.102 — Regression

Regression là change theo metric/property đã định nghĩa, không phải universal quality judgment.

## 527.103 — Improvement

Improvement cũng phải gắn metric/task cụ thể.

## 527.104 — Threshold

Threshold là project policy.

## 527.105 — Statistical significance

Có thể dùng statistical tests khi phù hợp.

## 527.106 — Confidence interval

Confidence interval có thể report.

## 527.107 — Variance

Run variance được preserve.

## 527.108 — Repeated runs

Stochastic models có thể chạy nhiều seeds.

## 527.109 — Seed

Seed được record.

## 527.110 — Environment drift

Hardware/software/model environment changes phải được record.

---

# AI EVALUATION MATRIX

## 527.111 — Dimension

Evaluation dimensions có thể gồm:

```text id="dims"
Correctness
Robustness
Latency
Throughput
Memory
Cost
Safety
ToolUse
Grounding
Consistency
```

## 527.112 — No aggregate score

Axiom không tạo universal weighted score.

## 527.113 — Task-specific metrics

Mỗi evaluation định nghĩa metrics phù hợp.

## 527.114 — Evidence

Metric result reference underlying cases.

## 527.115 — Failure cases

Failed cases phải inspectable.

## 527.116 — Success cases

Success cases cũng có provenance.

## 527.117 — Distribution

Results phải preserve case distribution.

## 527.118 — Stratified analysis

Có thể analyze theo category.

## 527.119 — Slice analysis

Analyze theo language/domain/model/input characteristics.

## 527.120 — Error taxonomy

Evaluation có thể classify failures.

---

# SAFETY EVALUATION

## 527.121 — Safety test set

Safety cases explicit.

## 527.122 — Policy version

Safety evaluation pins policy version.

## 527.123 — Capability boundary

Tool/capability access được test.

## 527.124 — Data exfiltration

Có thể test unauthorized data transfer.

## 527.125 — Prompt injection

Có thể test instruction/data separation.

## 527.126 — Tool misuse

Tool misuse scenarios.

## 527.127 — Resource exhaustion

Token/time/memory exhaustion cases.

## 527.128 — Sandbox escape

Sandbox boundary tests.

## 527.129 — Secret leakage

Secret exposure tests.

## 527.130 — False positive/negative

Safety detector metrics distinguish false positives và false negatives.

---

# REPRODUCIBILITY

## 527.131 — Run manifest

Mỗi run có manifest.

## 527.132 — Model hash

Model artifact hash.

## 527.133 — Dataset hash

Dataset hash.

## 527.134 — Code/build hash

Compiler/build identity.

## 527.135 — Toolchain

Toolchain/SDK/backend identity.

## 527.136 — Configuration

All evaluation-relevant config.

## 527.137 — Randomness

Seeds/randomness policy.

## 527.138 — Hardware

Hardware/device identity where relevant.

## 527.139 — Software environment

OS/runtime/library versions.

## 527.140 — Reproduction status

```text id="1kvq0k"
Reproduced
PartiallyReproduced
NotReproduced
Unknown
```

---

# CONTINUOUS EVALUATION

## 527.141 — CI integration

Evaluation có thể chạy trong CI.

## 527.142 — Scheduled evaluation

Periodic evaluation.

## 527.143 — Change-triggered evaluation

Code/model/dataset/policy changes có thể trigger evaluation.

## 527.144 — Selective evaluation

Chỉ affected suites khi change impact cho phép.

## 527.145 — Full evaluation

Full suite vẫn available.

## 527.146 — Artifact retention

Evaluation artifacts có retention policy.

## 527.147 — Comparison reports

Run-to-run diff.

## 527.148 — Failure triage

Failed case có direct provenance.

## 527.149 — Auto bisect

Có thể bisect model/code/config revisions.

## 527.150 — Deployment gate

Project policy có thể dùng evaluation result làm deployment gate.

---

# PERFORMANCE EVALUATION

## 527.151 — Latency

Measure TTFT, execution latency, end-to-end latency khi applicable.

## 527.152 — Throughput

Tokens/sec, samples/sec, requests/sec hoặc workload-specific metric.

## 527.153 — Memory

Peak/live/allocated memory.

## 527.154 — Accelerator

GPU/NPU utilization khi available.

## 527.155 — Cost

Compute/API cost có thể record.

## 527.156 — Cold/warm

Cold start và warm execution distinguish.

## 527.157 — Batch

Batch size được record.

## 527.158 — Cache

Cache state được record.

## 527.159 — Precision

Dtype/quantization/numerical mode.

## 527.160 — Performance/correctness separation

Performance regression không tự động imply correctness regression và ngược lại.

---

# EVALUATION ARTIFACT

## 527.161 — Result schema

```text id="result"
EvaluationResult {
    run_id
    case_id
    metrics
    verdicts
    evidence
    trace_ref?
    error?
}
```

## 527.162 — Aggregate artifact

Aggregate chỉ là derived artifact từ case-level results.

## 527.163 — Metric definition

Metric có formula/version.

## 527.164 — Verdict definition

Verdict có rule identity.

## 527.165 — Failure artifact

Failure giữ input/output/error/trace references.

## 527.166 — Comparison artifact

Diff giữa hai runs.

## 527.167 — Dataset report

Coverage/distribution/statistics.

## 527.168 — Environment report

Execution environment.

## 527.169 — Provenance graph

```text id="1etgk6"
Code
 ↓
Model
 ↓
Dataset
 ↓
Evaluation Definition
 ↓
Scenario
 ↓
Run
 ↓
Case
 ↓
Output
 ↓
Metric
 ↓
Verdict
```

## 527.170 — Machine readable

JSON/binary schema ổn định.

---

# AI EVALUATION API

## 527.171 — Run

```text id="runapi"
evaluate(spec)
```

## 527.172 — Case query

```text id="caseapi"
cases(run)
```

## 527.173 — Failure query

```text id="failapi"
failures(run)
```

## 527.174 — Regression query

```text id="regapi"
compare(run_a, run_b)
```

## 527.175 — Metric query

```text id="metricapi"
metric(run, metric_id)
```

## 527.176 — Provenance

```text id="provapi"
provenance(result)
```

## 527.177 — Reproduction

```text id="reproapi"
reproduce(run_id)
```

## 527.178 — Slice

```text id="sliceapi"
slice(run, filter)
```

## 527.179 — Error taxonomy

```text id="errapi"
classify_failures(run)
```

## 527.180 — Explain

Evaluation result có thể được link với 523 explanation/observability.

---

# 527.181 — HARD INVARIANTS

1. Evaluation khác benchmark.
2. Evaluation khác training.
3. Evaluation khác production monitoring.
4. Evaluation có identity.
5. Evaluation có version.
6. Evaluation definition có hash.
7. Evaluation run có identity.
8. Dataset có identity.
9. Dataset có version.
10. Dataset có content hash.
11. Dataset có provenance.
12. Dataset split được hỗ trợ.
13. Hidden test set được hỗ trợ.
14. Sampling configuration được lưu.
15. Random seed được lưu.
16. Stratification được hỗ trợ.
17. Dataset filtering được lưu.
18. Duplicate detection được hỗ trợ.
19. Leakage analysis được hỗ trợ khi dữ liệu cho phép.
20. Sensitive dataset access được enforce.
21. Dataset có thể là artifact.
22. Scenario có identity/configuration.
23. Model configuration được pin.
24. Tool configuration được pin.
25. Memory state có thể pin.
26. Retrieval state có thể pin.
27. Policy version được pin.
28. Environment được record.
29. Resource limits explicit.
30. Network access explicit.
31. Deterministic mode được hỗ trợ.
32. Oracle có identity.
33. Exact oracle được hỗ trợ.
34. Normalized oracle được hỗ trợ.
35. Structured oracle được hỗ trợ.
36. Property oracle được hỗ trợ.
37. Contract oracle được hỗ trợ.
38. Test oracle được hỗ trợ.
39. Reference implementation được hỗ trợ.
40. Reference model được hỗ trợ.
41. Human oracle được hỗ trợ.
42. Task-specific metrics được hỗ trợ.
43. Không có universal AI metric.
44. Classification metrics được hỗ trợ.
45. Regression metrics được hỗ trợ.
46. Generation metrics được hỗ trợ.
47. Embedding metrics được hỗ trợ.
48. Retrieval metrics được hỗ trợ.
49. Ranking metrics được hỗ trợ.
50. Speech metrics được hỗ trợ.
51. Vision metrics được hỗ trợ.
52. Multimodal metrics được hỗ trợ.
53. Agent task success được evaluate.
54. Partial success được represent.
55. Tool selection được evaluate.
56. Tool arguments được evaluate.
57. Planning được evaluate.
58. Recovery được evaluate.
59. Policy compliance được evaluate.
60. Capability compliance được evaluate.
61. Resource compliance được evaluate.
62. Agent efficiency metrics được hỗ trợ.
63. Agent robustness được evaluate.
64. Workflow end-to-end được evaluate.
65. Workflow step-level được evaluate.
66. Dependency ordering được test.
67. Checkpoint recovery được test.
68. Failure injection được hỗ trợ.
69. Compensation được test.
70. Human approval path được test.
71. Long-running recovery được test.
72. Distributed failure được test.
73. Deterministic simulation được hỗ trợ.
74. Human evaluation được hỗ trợ.
75. Rubric có identity/version.
76. Blind evaluation được hỗ trợ.
77. Pairwise evaluation được hỗ trợ.
78. Multiple evaluators được hỗ trợ.
79. Inter-rater agreement được measure.
80. Annotation provenance được preserve.
81. Adjudication được hỗ trợ.
82. Human comments distinguish khỏi machine metrics.
83. LLM-as-judge được hỗ trợ.
84. Judge model identity được record.
85. Judge prompt version được record.
86. Judge configuration được record.
87. Potential judge bias có thể document.
88. Human/judge agreement có thể measure.
89. Structured judge output được validate.
90. Judge output không tự động là ground truth.
91. Input perturbation được hỗ trợ.
92. Distribution shift được hỗ trợ.
93. Missing data được test.
94. Corrupted data được test.
95. Boundary cases được test.
96. Long-context evaluation integrate 524.
97. Tool failure evaluation integrate 513.
98. Model failure evaluation được hỗ trợ.
99. Recovery metrics được record.
100. Baseline comparison được hỗ trợ.
101. Regression được define theo explicit metric/property.
102. Improvement cũng được define theo explicit metric/property.
103. Threshold là project policy.
104. Statistical significance có thể được measure.
105. Confidence intervals có thể được report.
106. Variance được preserve.
107. Repeated stochastic runs được hỗ trợ.
108. Seed được preserve.
109. Environment drift được record.
110. Evaluation dimensions được cấu hình.
111. Không có aggregate score bắt buộc.
112. Metric results reference cases.
113. Failed cases inspectable.
114. Success cases inspectable.
115. Case distribution được preserve.
116. Stratified analysis được hỗ trợ.
117. Slice analysis được hỗ trợ.
118. Error taxonomy được hỗ trợ.
119. Safety test sets được hỗ trợ.
120. Safety policy version được pin.
121. Capability boundaries được test.
122. Data exfiltration được test.
123. Prompt injection được test.
124. Tool misuse được test.
125. Resource exhaustion được test.
126. Sandbox boundaries được test.
127. Secret leakage được test.
128. False-positive/false-negative được distinguish.
129. Run manifest được tạo.
130. Model hash được record.
131. Dataset hash được record.
132. Compiler/build hash được record.
133. Toolchain được record.
134. Evaluation configuration được record.
135. Randomness configuration được record.
136. Hardware được record khi relevant.
137. Software environment được record.
138. Reproduction status được explicit.
139. CI integration được hỗ trợ.
140. Scheduled evaluation được hỗ trợ.
141. Change-triggered evaluation được hỗ trợ.
142. Selective evaluation được hỗ trợ.
143. Full evaluation được hỗ trợ.
144. Evaluation artifact retention được configurable.
145. Run comparison được hỗ trợ.
146. Failure triage có provenance.
147. Revision bisect được hỗ trợ.
148. Deployment gates có thể dùng project-defined evaluation rules.
149. Latency được đo.
150. Throughput được đo.
151. Memory được đo.
152. Accelerator utilization có thể đo.
153. Cost metadata được hỗ trợ.
154. Cold/warm execution được distinguish.
155. Batch configuration được record.
156. Cache state được record.
157. Precision/quantization được record.
158. Performance và correctness được distinguish.
159. Case-level result có stable schema.
160. Aggregate là derived artifact.
161. Metric formula/version được lưu.
162. Verdict rule/version được lưu.
163. Failure artifact giữ provenance.
164. Comparison artifact có identity.
165. Dataset distribution report được hỗ trợ.
166. Environment report được hỗ trợ.
167. Provenance graph được hỗ trợ.
168. Machine-readable evaluation results được hỗ trợ.
169. Evaluation API được hỗ trợ.
170. Case query được hỗ trợ.
171. Failure query được hỗ trợ.
172. Regression query được hỗ trợ.
173. Metric query được hỗ trợ.
174. Provenance query được hỗ trợ.
175. Reproduction được hỗ trợ.
176. Slice analysis được hỗ trợ.
177. Failure classification được hỗ trợ.
178. Evaluation result có thể link observability 523.
179. Evaluation artifacts không được mutate silently.
180. Dataset version changes invalidate affected results.
181. Model version changes invalidate affected results.
182. Evaluation-definition changes invalidate affected results.
183. Tool/policy changes invalidate relevant results.
184. External nondeterminism phải được record.
185. Hidden test data không được expose ngoài authorization.
186. Evaluation execution có resource limits.
187. Evaluation runner có cancellation.
188. Evaluation runner có timeout.
189. Evaluation runner có crash recovery khi configured.
190. Evaluation runner có structured errors.
191. Evaluation không được biến metric thành universal truth.
192. Evaluation không được che giấu failed cases bằng aggregate.
193. Evaluation provenance phải trace được tới source artifact.
194. AI evaluator output phải distinguish observation và judgment.
195. Human judgment phải distinguish khỏi automated metric.
196. Evaluation comparison phải preserve population/dataset/time period.
197. Metric comparisons chỉ meaningful khi definitions tương thích.
198. Cross-model comparisons phải pin dataset/scenario/configuration tương ứng.
199. Cross-version comparisons phải record changed variables.
200. **Axiom AI Evaluation phải cung cấp một hệ thống đánh giá reproducible, case-level, provenance-first cho model, agent và workflow; metric, oracle, human judgment, judge-model output, performance measurement và safety result phải được phân biệt rõ, không được biến thành một “điểm chất lượng AI” tổng hợp che mất dữ liệu và failure cases.**

**BOOTSTRAP-527 hoàn tất / LOCKED.**

---

# BOOTSTRAP-528 — AI DATA GOVERNANCE, DATASET VERSIONING, PROVENANCE, LINEAGE, LABELING, QUALITY, CONSENT, RETENTION & TRAINING-DATA CONTROL

**Trạng thái: COMPLETED / LOCKED**

528 xây dựng lớp quản trị dữ liệu cho 503–527. Nó đặc biệt quan trọng nếu Axiom hướng tới AI/ML production thực tế, nơi **model quality không thể tách khỏi nguồn dữ liệu, phiên bản dataset, transformation và lineage**.

```text id="528arch"
                    Raw Data
                       │
                 Registration
                       │
                Classification
                       │
          ┌────────────┼────────────┐
          ↓            ↓            ↓
       Labeling     Validation   Filtering
          │            │            │
          └────────────┼────────────┘
                       ↓
                Transformation
                       │
                 Dataset Version
                       │
          ┌────────────┼────────────┐
          ↓            ↓            ↓
       Training      Evaluation   Retrieval
          │            │            │
          └────────────┼────────────┘
                       ↓
                    Model
                       │
                  Model Lineage
```

---

# DATA IDENTITY

## 528.1 — Data item

Mỗi source item có stable identity khi possible.

## 528.2 — Dataset identity

Dataset identity không phụ thuộc filesystem path.

## 528.3 — Content hash

Content-addressed identity được hỗ trợ.

## 528.4 — Dataset version

Dataset immutable version được ưu tiên.

## 528.5 — Manifest

Dataset manifest chứa items/schema/statistics/provenance.

## 528.6 — Source identity

Source reference có:

```text id="sources"
provider
location
version
timestamp
content_hash
```

## 528.7 — Derived dataset

Dataset được tạo từ dataset khác phải preserve lineage.

## 528.8 — Transformation identity

Transformation có code/config/version identity.

## 528.9 — Environment

Transformation environment được record khi relevant.

## 528.10 — Determinism

Deterministic transformation có reproducible output.

---

# DATA LINEAGE

## 528.11 — Lineage graph

```text id="lineage"
Source
 ↓
Transform
 ↓
Intermediate Dataset
 ↓
Filter
 ↓
Label
 ↓
Final Dataset
 ↓
Training / Evaluation
```

## 528.12 — Parent references

Derived dataset reference parents.

## 528.13 — Transformation parameters

Parameters được lưu.

## 528.14 — Filter provenance

Filtering rules được preserve.

## 528.15 — Sampling provenance

Sampling seed/config được preserve.

## 528.16 — Dedup provenance

Dedup algorithm/version được preserve.

## 528.17 — Split provenance

Train/validation/test split logic được preserve.

## 528.18 — Leakage provenance

Detected overlap được record.

## 528.19 — Lineage query

Có thể query upstream/downstream lineage.

## 528.20 — Impact analysis

Source change có thể identify affected datasets/models/evaluations.

---

# DATA SCHEMA

## 528.21 — Schema identity

Schema có identity/version.

## 528.22 — Typed fields

Fields có explicit type.

## 528.23 — Optionality

Nullable/optional distinction explicit.

## 528.24 — Constraints

Schema có validation constraints.

## 528.25 — Schema evolution

Compatible/incompatible changes được classify.

## 528.26 — Migration

Migration có version.

## 528.27 — Metadata

Language/domain/source/time metadata.

## 528.28 — Multimodal records

Text/image/audio/video fields có explicit modality.

## 528.29 — Temporal records

Timestamp/time range được preserve.

## 528.30 — Units

Physical units explicit khi applicable.

---

# LABELING

## 528.31 — Label

Label là separate artifact khỏi source input.

## 528.32 — Label identity

Annotation có identity/version.

## 528.33 — Annotator

Human/model/tool annotator identity được record theo privacy policy.

## 528.34 — Annotation source

Annotation có source/provenance.

## 528.35 — Multiple labels

Multiple labels cho cùng item được hỗ trợ.

## 528.36 — Agreement

Annotator agreement có thể measure.

## 528.37 — Adjudication

Conflicting labels có adjudication workflow.

## 528.38 — Weak labels

Weak/pseudo labels được distinguish.

## 528.39 — Synthetic labels

Generated labels được mark synthetic.

## 528.40 — Label confidence

Confidence được lưu như metadata.

---

# DATA QUALITY

## 528.41 — Completeness

Missing fields/statistics.

## 528.42 — Validity

Schema/type validity.

## 528.43 — Consistency

Cross-field consistency.

## 528.44 — Duplicate rate

Duplicate analysis.

## 528.45 — Outliers

Outlier detection.

## 528.46 — Distribution

Distribution statistics.

## 528.47 — Drift

Dataset distribution drift.

## 528.48 — Corruption

Malformed/corrupted data.

## 528.49 — Quality rules

Rules versioned.

## 528.50 — Quality result

```text id="quality"
Rule
DatasetVersion
Result
Evidence
Timestamp
```

---

# DATA FILTERING

## 528.51 — Include/exclude

Explicit filter predicates.

## 528.52 — Policy filtering

Sensitive/restricted data filters.

## 528.53 — Language filtering

Language detection metadata.

## 528.54 — Modality filtering

Image/audio/video/text filters.

## 528.55 — Quality filtering

Quality threshold.

## 528.56 — Deduplication

Exact and semantic deduplication.

## 528.57 — Near duplicate

Near-duplicate detection configurable.

## 528.58 — Filter explainability

Mỗi excluded item có thể query reason.

## 528.59 — Reversible filtering

Canonical source remains separate.

## 528.60 — Filter reproducibility

Filter definition/version/inputs được pin.

---

# DATA SPLITS

## 528.61 — Training split

Training data identity.

## 528.62 — Validation split

Validation data identity.

## 528.63 — Test split

Test data identity.

## 528.64 — Challenge split

Special challenge datasets.

## 528.65 — Temporal split

Time-based splitting.

## 528.66 — Entity split

Entity-disjoint splitting.

## 528.67 — Group split

Group-aware splitting.

## 528.68 — Stratified split

Class/domain stratification.

## 528.69 — Leakage prevention

Split policy có thể enforce disjointness.

## 528.70 — Split manifest

Exact membership được record.

---

# TRAINING DATA GOVERNANCE

## 528.71 — Training manifest

Training run references exact dataset versions.

## 528.72 — Preprocessing

Preprocessing graph được record.

## 528.73 — Augmentation

Augmentation identity/configuration được record.

## 528.74 — Sampling

Sampler identity/configuration.

## 528.75 — Shuffle

Shuffle seed/policy.

## 528.76 — Weighting

Sample/class weighting.

## 528.77 — Curriculum

Curriculum schedule được record.

## 528.78 — Synthetic data

Synthetic sources distinguish.

## 528.79 — Human data

Human-generated data distinguish.

## 528.80 — External data

External provider/source identity.

---

# CONSENT & RIGHTS

## 528.81 — Data rights metadata

Dataset item có thể mang rights metadata.

## 528.82 — License

License identity/version.

## 528.83 — Usage restriction

Purpose/use restriction metadata.

## 528.84 — Consent status

Khi applicable:

```text id="consent"
Granted
Denied
Unknown
NotApplicable
```

## 528.85 — Revocation

Revoked data có lifecycle state.

## 528.86 — Restricted training

Data có thể bị cấm dùng cho training.

## 528.87 — Restricted evaluation

Data có thể chỉ được dùng evaluation.

## 528.88 — Restricted retrieval

Data có thể chỉ được dùng retrieval.

## 528.89 — Policy enforcement

Training/evaluation/retrieval pipelines enforce restrictions.

## 528.90 — Audit

Access/use events có thể audit.

---

# RETENTION & DELETION

## 528.91 — Retention policy

Retention có explicit policy.

## 528.92 — Expiration

Dataset item/version có expiration.

## 528.93 — Deletion

Canonical source deletion được hỗ trợ.

## 528.94 — Derived data

Deletion impact tới derived datasets được track.

## 528.95 — Embeddings

Embedding derivatives được track.

## 528.96 — Labels

Derived labels được track.

## 528.97 — Checkpoints

Models/checkpoints affected bởi data deletion được identify.

## 528.98 — Evaluation

Evaluation artifacts affected được identify.

## 528.99 — Cache

Caches được invalidate theo policy.

## 528.100 — Backup

Backup retention semantics explicit.

---

# DATA PRIVACY

## 528.101 — Sensitivity labels

Data classification.

## 528.102 — PII marker

Potential personal-data classification metadata.

## 528.103 — Secret marker

Credentials/secrets distinguish.

## 528.104 — Access control

Dataset access enforce capability/ACL.

## 528.105 — Field-level access

Sensitive fields có thể access-controlled.

## 528.106 — Redaction

Export redaction.

## 528.107 — Anonymization

Anonymization/pseudonymization transforms được provenance.

## 528.108 — Encryption

At-rest/in-transit encryption thuộc storage/network layer.

## 528.109 — Query privacy

Queries không bypass source restrictions.

## 528.110 — Cross-tenant isolation

Tenant data isolation.

---

# DATA VERSIONING

## 528.111 — Immutable version

Published dataset version immutable.

## 528.112 — Revision

Internal draft revisions có thể mutate.

## 528.113 — Snapshot

Evaluation/training references immutable snapshot.

## 528.114 — Branch

Dataset branches được hỗ trợ.

## 528.115 — Merge

Merge requires conflict semantics.

## 528.116 — Patch

Incremental dataset patch.

## 528.117 — Delta

Storage-efficient delta representation.

## 528.118 — Materialization

Derived dataset can be materialized.

## 528.119 — Lazy dataset

Dataset can remain query-defined.

## 528.120 — Materialization identity

Materialized result references source definition/version.

---

# DATASET → MODEL LINEAGE

## 528.121 — Training lineage

```text id="trainline"
Dataset
 ↓
Preprocess
 ↓
Sampler
 ↓
Training Run
 ↓
Checkpoint
 ↓
Model
```

## 528.122 — Evaluation lineage

```text id="evalline"
Model
 ↓
Evaluation Spec
 ↓
Dataset
 ↓
Run
 ↓
Results
```

## 528.123 — Retrieval lineage

```text id="retline"
Source
 ↓
Ingestion
 ↓
Chunk
 ↓
Embedding
 ↓
Index
 ↓
Retrieval
```

## 528.124 — Model provenance

Model artifact có thể query datasets used.

## 528.125 — Dataset provenance

Dataset có thể query models/evaluations using it.

## 528.126 — Change impact

Dataset update có thể identify affected model/evaluation artifacts.

## 528.127 — Reproducibility

Training run can reference exact data snapshot.

## 528.128 — Synthetic lineage

Synthetic dataset references generator model/config.

## 528.129 — Human annotation lineage

Labels reference annotation process.

## 528.130 — Full lineage graph

All lineage can be traversed subject to access control.

---

# DATA QUALITY MONITORING

## 528.131 — Distribution monitoring

Production data distribution can be monitored.

## 528.132 — Schema drift

Schema changes detected.

## 528.133 — Label drift

Label distribution changes.

## 528.134 — Feature drift

Feature distribution changes.

## 528.135 — Embedding drift

Embedding distribution changes.

## 528.136 — Missingness drift

Missing-value rate changes.

## 528.137 — Quality drift

Quality rule results over time.

## 528.138 — Threshold policy

Alert thresholds project-defined.

## 528.139 — Alert provenance

Alert references exact data window/rule.

## 528.140 — No universal drift threshold

Không có một threshold drift áp dụng cho mọi domain.

---

# AI TOOLING

## 528.141 — Why included?

```text id="winc"
why_included(item)
```

## 528.142 — Why excluded?

```text id="wexc"
why_excluded(item)
```

## 528.143 — Dataset lineage

```text id="wlin"
dataset_lineage(dataset)
```

## 528.144 — Model lineage

```text id="wmlin"
model_data_lineage(model)
```

## 528.145 — Quality

```text id="wqual"
data_quality(dataset)
```

## 528.146 — Leakage

```text id="wleak"
data_leakage(dataset)
```

## 528.147 — Rights

```text id="wright"
data_rights(item)
```

## 528.148 — Deletion impact

```text id="wdel"
deletion_impact(item)
```

## 528.149 — Reproduction

```text id="wrep"
reproduce_dataset(version)
```

## 528.150 — Machine-readable

All governance metadata is queryable.

---

# 528.151 — HARD INVARIANTS

1. Dataset có identity.
2. Dataset có version.
3. Dataset có hash.
4. Dataset có manifest.
5. Source identity được preserve.
6. Derived dataset preserve lineage.
7. Transformation có identity.
8. Transformation config được lưu.
9. Environment được record khi relevant.
10. Deterministic transformation có thể reproduce.
11. Lineage graph được hỗ trợ.
12. Parent references được preserve.
13. Filtering provenance được preserve.
14. Sampling provenance được preserve.
15. Dedup provenance được preserve.
16. Split provenance được preserve.
17. Leakage findings được record.
18. Upstream lineage queryable.
19. Downstream lineage queryable.
20. Impact analysis được hỗ trợ.
21. Schema có identity.
22. Schema có version.
23. Fields có type.
24. Optionality explicit.
25. Constraints được hỗ trợ.
26. Schema evolution được classify.
27. Migration được version.
28. Multimodal schema được hỗ trợ.
29. Temporal metadata được preserve.
30. Units được explicit khi applicable.
31. Labels là separate artifacts.
32. Annotation có identity.
33. Annotator provenance được hỗ trợ.
34. Multiple annotations được hỗ trợ.
35. Agreement có thể measure.
36. Adjudication được hỗ trợ.
37. Weak labels được distinguish.
38. Synthetic labels được distinguish.
39. Label confidence được preserve.
40. Completeness được evaluate.
41. Validity được evaluate.
42. Consistency được evaluate.
43. Duplicate rate được measure.
44. Outliers được analyze.
45. Distribution được characterize.
46. Drift được monitor.
47. Corruption được detect.
48. Quality rules versioned.
49. Quality result có evidence.
50. Include/exclude predicates explicit.
51. Policy filtering được hỗ trợ.
52. Language filtering được hỗ trợ.
53. Modality filtering được hỗ trợ.
54. Quality filtering được hỗ trợ.
55. Exact deduplication được hỗ trợ.
56. Near-duplicate detection được hỗ trợ.
57. Exclusion reason queryable.
58. Canonical source tách khỏi derived filter.
59. Filtering reproducible.
60. Train split có identity.
61. Validation split có identity.
62. Test split có identity.
63. Challenge split được hỗ trợ.
64. Temporal split được hỗ trợ.
65. Entity-disjoint split được hỗ trợ.
66. Group split được hỗ trợ.
67. Stratified split được hỗ trợ.
68. Leakage prevention có thể enforce.
69. Split membership được record.
70. Training manifest reference exact dataset version.
71. Preprocessing provenance được record.
72. Augmentation được version/configure.
73. Sampling được version/configure.
74. Shuffle seed được preserve.
75. Weighting được preserve.
76. Curriculum được preserve.
77. Synthetic data được identify.
78. Human data được identify.
79. External source được identify.
80. Rights metadata được hỗ trợ.
81. License được record.
82. Usage restrictions được record.
83. Consent state được record khi applicable.
84. Revocation được hỗ trợ.
85. Training restrictions được enforce.
86. Evaluation restrictions được enforce.
87. Retrieval restrictions được enforce.
88. Data access/use có thể audit.
89. Retention policy explicit.
90. Expiration được hỗ trợ.
91. Canonical deletion được hỗ trợ.
92. Derived-data impact được track.
93. Embedding impact được track.
94. Label impact được track.
95. Model/checkpoint impact được identify.
96. Evaluation impact được identify.
97. Cache invalidation được hỗ trợ.
98. Backup retention semantics explicit.
99. Sensitivity labels được hỗ trợ.
100. Personal-data classification metadata được hỗ trợ.
101. Secrets được distinguish.
102. Dataset ACL/capability được enforce.
103. Field-level access được hỗ trợ.
104. Export redaction được hỗ trợ.
105. Anonymization provenance được preserve.
106. Encryption integration được hỗ trợ.
107. Query không bypass access policy.
108. Cross-tenant isolation được enforce.
109. Published dataset versions immutable.
110. Draft revisions được hỗ trợ.
111. Training/evaluation snapshots immutable.
112. Dataset branches được hỗ trợ.
113. Merge conflict semantics explicit.
114. Patch/delta được hỗ trợ.
115. Materialization được hỗ trợ.
116. Lazy dataset được hỗ trợ.
117. Materialized result preserve source identity.
118. Training lineage được hỗ trợ.
119. Evaluation lineage được hỗ trợ.
120. Retrieval lineage được hỗ trợ.
121. Model→dataset lineage queryable.
122. Dataset→model lineage queryable.
123. Dataset changes support impact analysis.
124. Exact data snapshot supports reproducibility.
125. Synthetic lineage được preserve.
126. Annotation lineage được preserve.
127. Full lineage traversal obeys ACL.
128. Production distribution monitoring được hỗ trợ.
129. Schema drift được detect.
130. Label drift được detect.
131. Feature drift được detect.
132. Embedding drift được detect.
133. Missingness drift được detect.
134. Quality drift được detect.
135. Alert thresholds are project policy.
136. Alerts preserve rule/window evidence.
137. Không có universal drift threshold.
138. `why_included` được hỗ trợ.
139. `why_excluded` được hỗ trợ.
140. Dataset lineage query được hỗ trợ.
141. Model data lineage query được hỗ trợ.
142. Data quality query được hỗ trợ.
143. Leakage query được hỗ trợ.
144. Rights query được hỗ trợ.
145. Deletion-impact query được hỗ trợ.
146. Dataset reproduction được hỗ trợ.
147. Governance metadata machine-readable.
148. Dataset changes invalidate dependent derived artifacts when required.
149. Data governance does not silently mutate training/evaluation inputs.
150. **Axiom Data Governance phải bảo đảm mọi dataset, transformation, label, split, training run, evaluation và model đều có thể truy nguyên về nguồn dữ liệu và phiên bản chính xác; quyền sử dụng, chất lượng, retention, deletion, leakage và derived-data impact phải là metadata có thể kiểm tra, thay vì các quy tắc ẩn trong pipeline.**

**BOOTSTRAP-528 hoàn tất / LOCKED.**

---

**Task kế tiếp: `BOOTSTRAP-529 — AI MODEL SERVING, INFERENCE SERVER, REQUEST ROUTING, DYNAMIC BATCHING, STREAMING, MODEL LIFECYCLE, HOT-SWAP & PRODUCTION DEPLOYMENT RUNTIME`.**