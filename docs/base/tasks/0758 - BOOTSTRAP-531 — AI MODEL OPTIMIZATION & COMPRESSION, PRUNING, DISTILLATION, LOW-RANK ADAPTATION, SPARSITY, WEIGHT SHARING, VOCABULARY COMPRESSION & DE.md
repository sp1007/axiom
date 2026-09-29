# BOOTSTRAP-531 — AI MODEL OPTIMIZATION & COMPRESSION, PRUNING, DISTILLATION, LOW-RANK ADAPTATION, SPARSITY, WEIGHT SHARING, VOCABULARY COMPRESSION & DEPLOYMENT-AWARE MODEL TRANSFORMATION

**Trạng thái: COMPLETED / LOCKED**

531 định nghĩa tầng biến đổi model sau training hoặc trong quá trình training, nhằm giảm **kích thước, memory footprint, bandwidth và compute cost** trong khi giữ provenance và khả năng kiểm chứng.

Điểm quan trọng: 531 **không giả định mọi kỹ thuật tối ưu đều làm model tốt hơn**. Compiler/runtime chỉ cung cấp cơ chế và bằng chứng; việc chấp nhận biến đổi là policy của pipeline.

```text id="531arch"
                 Trained Model
                      │
                      ↓
              Model Transformation
                      │
       ┌──────────────┼────────────────┐
       ↓              ↓                ↓
    Pruning       Quantization     Distillation
       │              │                │
       ├──────────────┼────────────────┤
       ↓              ↓                ↓
   Sparsity       Low-Rank         Weight Sharing
       │              │                │
       └──────────────┼────────────────┘
                      ↓
                Graph Rewrite
                      ↓
              Deployment Compile
                 504 / 505
                      ↓
             Optimized Artifact
                      │
                      ↓
                 Evaluation 527
                      │
                      ↓
                 Serving 529
```

---

# 531.1 — Model Transformation ≠ Compiler Optimization

Compiler optimization:

```text
same model semantics
→ better execution
```

Model transformation:

```text
model A
→ model B
```

Hai quá trình phải được phân biệt trong provenance.

---

# 531.2 — Transformation Identity

```text
ModelTransform {
    TransformId
    InputModel
    OutputModel
    TransformType
    Configuration
    Toolchain
    Target?
    Dataset?
    Evidence
}
```

Mỗi transformation có identity riêng.

---

# 531.3 — Transformation Graph

Model lineage:

```text
Base Model
   ↓
Fine Tune
   ↓
Prune
   ↓
Quantize
   ↓
Compile
   ↓
Deploy Artifact
```

Không được flatten lineage thành một hash duy nhất không thể truy nguyên.

---

# 531.4 — Equivalence

Các mức:

```text
Exact
NumericallyEquivalent
TaskEquivalent
Approximate
Unknown
```

Không được mặc định model sau transformation tương đương model trước.

---

# PRUNING

## 531.5 — Weight pruning

Loại bỏ weight không cần thiết.

## 531.6 — Unstructured pruning

Prune từng weight.

## 531.7 — Structured pruning

Prune:

- neuron;
- channel;
- head;
- block;
- layer.

## 531.8 — Block pruning

Prune theo block cố định.

## 531.9 — N:M sparsity

Hỗ trợ pattern dạng N:M khi backend có kernel phù hợp.

## 531.10 — Magnitude pruning

Có thể dùng magnitude làm criterion.

## 531.11 — Learned pruning

Mask có thể được học.

## 531.12 — Mask

Mask identity/version được lưu.

## 531.13 — Permanent pruning

Weight bị loại bỏ vật lý khỏi artifact.

## 531.14 — Logical pruning

Mask vẫn tồn tại.

## 531.15 — Sparse representation

Sparse model phải có representation explicit.

---

# SPARSITY

## 531.16 — Sparsity metadata

```text
SparsityPattern {
    kind
    dimensions
    block_shape
    density
}
```

## 531.17 — Density

Density được lưu như metadata, không chỉ suy ra từ benchmark.

## 531.18 — Sparse kernel

Sparse representation chỉ mang lại lợi ích khi backend có kernel tương ứng.

## 531.19 — Dense fallback

Backend không hỗ trợ sparse phải có explicit fallback hoặc reject.

## 531.20 — Sparse layout

Layout của sparse tensor explicit.

## 531.21 — Sparse indexing

Index representation versioned.

## 531.22 — Sparse conversion

Dense↔sparse conversion explicit.

## 531.23 — Sparse memory

Peak memory của sparse representation phải measurable.

## 531.24 — Sparse compute

Compute estimate không được coi là runtime guarantee.

## 531.25 — Sparsity validation

Sparse artifact phải validate index bounds/ordering/invariants.

---

# QUANTIZATION

## 531.26 — Quantization

Quantization từ 503/504 được mở rộng thành model transformation độc lập.

## 531.27 — Dtype

Ví dụ:

```text
INT8
UINT8
INT4
UINT4
FP8
```

chỉ được dùng khi backend hỗ trợ semantics tương ứng.

## 531.28 — Scale

Scale explicit.

## 531.29 — Zero point

Zero point explicit đối với asymmetric quantization.

## 531.30 — Per-tensor

Một scale cho tensor.

## 531.31 — Per-channel

Scale theo channel.

## 531.32 — Group-wise

Scale theo group.

## 531.33 — Weight-only

Chỉ quantize weights.

## 531.34 — Activation quantization

Activation quantization explicit.

## 531.35 — KV quantization

LLM KV cache quantization có thể dùng trong deployment pipeline.

## 531.36 — Calibration

Calibration dataset/version được record.

## 531.37 — Calibration statistics

Min/max/histogram/scale method được record.

## 531.38 — Quantization error

Error statistics được lưu.

## 531.39 — Quantization-aware training

QAT được hỗ trợ thông qua training graph.

## 531.40 — Fake quantization

Fake quant node được distinguish với physical quantization.

---

# MIXED PRECISION

## 531.41 — Layer precision

Mỗi operator/layer có thể có precision riêng.

## 531.42 — Accumulator

Accumulator dtype explicit.

## 531.43 — Sensitive operations

Một số operations có thể giữ FP32.

## 531.44 — Precision policy

```text
Strict
Balanced
Fast
Custom
```

## 531.45 — Hardware constraints

Precision selection phải xét target capabilities.

## 531.46 — Fallback

Unsupported precision phải fallback hoặc error explicit.

## 531.47 — Conversion cost

Cast/conversion operations được graph compiler expose.

## 531.48 — Precision provenance

Precision transformation được record.

## 531.49 — Numerical evidence

Evaluation có thể compare numerical deviation.

## 531.50 — No silent precision downgrade

Compiler không tự ý thay đổi precision semantics nếu policy không cho phép.

---

# KNOWLEDGE DISTILLATION

## 531.51 — Teacher

Teacher model identity/version.

## 531.52 — Student

Student model identity/version.

## 531.53 — Teacher outputs

Logits/features/intermediate representations.

## 531.54 — Distillation loss

Explicit loss definition.

## 531.55 — Temperature

Temperature parameter explicit.

## 531.56 — Feature distillation

Intermediate features có thể dùng.

## 531.57 — Attention distillation

Attention maps có thể dùng.

## 531.58 — Dataset

Distillation dataset version được pin.

## 531.59 — Teacher execution

Teacher có thể frozen hoặc trainable tùy policy.

## 531.60 — Provenance

Student model phải reference teacher.

---

# LOW-RANK ADAPTATION

## 531.61 — LoRA abstraction

Parameter update có thể biểu diễn:

```text
W' = W + ΔW
ΔW = A × B
```

## 531.62 — Adapter

Adapter là artifact riêng.

## 531.63 — Rank

Rank explicit.

## 531.64 — Scaling

Alpha/scaling explicit.

## 531.65 — Multiple adapters

Một base model có thể có nhiều adapters.

## 531.66 — Adapter composition

Composition order explicit.

## 531.67 — Adapter merge

Merge vào base weights là transformation mới.

## 531.68 — Adapter removal

Có thể deploy base model không adapter.

## 531.69 — Adapter provenance

Base model + adapter lineage preserved.

## 531.70 — Serving

529 có thể route theo base model + adapter configuration.

---

# OTHER PARAMETER-EFFICIENT TRANSFORMATIONS

## 531.71 — Prefix tuning

Supported as library transformation.

## 531.72 — Prompt tuning

Trainable virtual embeddings.

## 531.73 — Bias-only adaptation

Bias parameters only.

## 531.74 — Sparse adapters

Adapter sparsity.

## 531.75 — Low-rank variants

General low-rank parameterization.

## 531.76 — Adapter target

Target layers explicit.

## 531.77 — Adapter compatibility

Architecture/schema compatibility checked.

## 531.78 — Adapter versioning

Independent version.

## 531.79 — Adapter artifact

Can be packaged independently.

## 531.80 — No hidden parameter mutation

Applying adapter must produce explicit transformed execution graph or artifact.

---

# WEIGHT SHARING

## 531.81 — Shared parameter

Multiple graph nodes may reference one physical parameter.

## 531.82 — Alias identity

Shared weights preserve alias relationship.

## 531.83 — Copy elimination

Compiler must not duplicate shared weights unless explicit optimization permits it.

## 531.84 — Training semantics

Gradient accumulation for shared parameters explicit.

## 531.85 — Serialization

Shared weights represented once.

## 531.86 — Loading

Loader restores sharing.

## 531.87 — Quantization

Shared weights cannot accidentally receive incompatible quantization.

## 531.88 — Mutation

In-place mutation requires exclusive ownership.

## 531.89 — Reference count

No mandatory runtime reference counting.

## 531.90 — Memory report

Physical vs logical parameter size distinguish.

---

# VOCABULARY OPTIMIZATION

## 531.91 — Vocabulary pruning

Unused/rare tokens can be removed only with explicit transformation semantics.

## 531.92 — Token remapping

Old TokenId → new TokenId mapping stored.

## 531.93 — Embedding resize

Embedding matrix resized consistently.

## 531.94 — Output head

Tied output embeddings updated consistently.

## 531.95 — Tokenizer compatibility

Tokenizer version/hash must match transformed vocabulary.

## 531.96 — Special tokens

Special tokens cannot be silently removed.

## 531.97 — Added tokens

Vocabulary extension is a separate transformation.

## 531.98 — Vocabulary provenance

Original and transformed vocabulary identities retained.

## 531.99 — Model compatibility

Model/tokenizer mismatch is hard error.

## 531.100 — Serving

529 must verify tokenizer/model compatibility before serving.

---

# KNOWLEDGE / WEIGHT COMPRESSION

## 531.101 — Weight packing

Deployment-specific packing.

## 531.102 — Compression

Storage compression ≠ numerical quantization.

## 531.103 — Entropy coding

Optional.

## 531.104 — Block compression

Optional.

## 531.105 — Decompression

Can happen at load time or runtime.

## 531.106 — Memory-mapped weights

Integrates 455/506.

## 531.107 — Lazy loading

Weights can load on demand.

## 531.108 — Prefetch

Serving/runtime may prefetch.

## 531.109 — Residency

CPU/GPU residency explicit.

## 531.110 — Compression provenance

Storage compression recorded separately from model transformation.

---

# GRAPH TRANSFORMATION

## 531.111 — Layer fusion

Can combine compatible layers.

## 531.112 — Operator elimination

Remove redundant operators.

## 531.113 — Constant folding

Integrates 504.

## 531.114 — Dead branch elimination

Static branch removal.

## 531.115 — Layout transformation

Deployment-specific layout.

## 531.116 — Weight packing

Kernel-specific weight layout.

## 531.117 — Activation recomputation

Optional memory/compute tradeoff.

## 531.118 — Operator substitution

Equivalent operator implementation under numerical policy.

## 531.119 — Graph provenance

Every transformation preserves source graph references.

## 531.120 — Reversible representation

Where possible transformation metadata allows reconstruction or comparison.

---

# MODEL SIZE ANALYSIS

## 531.121 — Parameter count

Logical parameter count.

## 531.122 — Physical bytes

Actual stored bytes.

## 531.123 — Runtime memory

Execution memory separate.

## 531.124 — Peak memory

Peak inference/training memory.

## 531.125 — Weight bandwidth

Weight transfer cost.

## 531.126 — Activation memory

Activation footprint.

## 531.127 — KV memory

LLM KV cache.

## 531.128 — Metadata overhead

Indexes/scales/masks/packing metadata.

## 531.129 — Compression report

All components reported separately.

## 531.130 — No misleading compression ratio

Compression ratio must specify baseline and what is measured.

---

# DEPLOYMENT-AWARE OPTIMIZATION

## 531.131 — Target

Transformation may target:

- CPU;
- GPU;
- NPU;
- accelerator.

## 531.132 — ISA

CPU features can influence transformation.

## 531.133 — GPU architecture

GPU-specific sparsity/precision.

## 531.134 — Memory budget

Target memory budget.

## 531.135 — Latency budget

Deployment policy can specify latency target.

## 531.136 — Throughput target

Batch throughput target.

## 531.137 — Batch regime

Optimization must know expected batch regime.

## 531.138 — Context regime

LLM optimization may depend on expected context length.

## 531.139 — Streaming regime

Streaming inference has different constraints from batch inference.

## 531.140 — Optimization fingerprint

Target-aware transformation records target assumptions.

---

# TRANSFORMATION PIPELINE

## 531.141 — Pipeline

```text
Input Model
   ↓
Validate
   ↓
Analyze
   ↓
Transform
   ↓
Validate
   ↓
Compile
   ↓
Evaluate
   ↓
Package
```

## 531.142 — Dry run

Pipeline can produce transformation plan without modifying model.

## 531.143 — Preview

Transformation preview includes affected parameters/graph nodes.

## 531.144 — Transaction

Transformation is transactional.

## 531.145 — Failure

Failed transformation cannot publish partial artifact.

## 531.146 — Reproducibility

Transformation config/hash fully recorded.

## 531.147 — Cache

Transform results content-addressable.

## 531.148 — Incremental

Unchanged transformation inputs can reuse cached results.

## 531.149 — Parallel

Independent transformations can run parallel.

## 531.150 — Determinism

Deterministic mode must produce deterministic transformation artifact.

---

# QUALITY / EVALUATION

## 531.151 — Baseline

Original model evaluation reference.

## 531.152 — Transformed model

Evaluated independently.

## 531.153 — Task metrics

Use task-specific metrics from 527.

## 531.154 — Numerical metrics

Numerical deviation.

## 531.155 — Performance metrics

Latency/throughput/memory.

## 531.156 — Size metrics

Artifact size.

## 531.157 — Accuracy tradeoff

Metrics shown side-by-side rather than collapsed into a single score.

## 531.158 — Dataset identity

Evaluation dataset pinned.

## 531.159 — Hardware identity

Performance evaluation records hardware.

## 531.160 — Statistical uncertainty

Evaluation uncertainty retained.

---

# AUTOMATED OPTIMIZATION SEARCH

## 531.161 — Search

Try multiple transformations.

## 531.162 — Search space

Explicit.

## 531.163 — Constraints

Memory/latency/accuracy/size constraints explicit.

## 531.164 — Candidate identity

Every candidate gets identity.

## 531.165 — Candidate lineage

Candidate references parent model.

## 531.166 — Evaluation

Every accepted candidate must have evaluation evidence.

## 531.167 — Failed candidate

Failed candidate remains traceable.

## 531.168 — Search budget

Compute/time/trial budget.

## 531.169 — Parallel search

Possible.

## 531.170 — Deterministic search

Seed/config recorded.

---

# MODEL MERGING

## 531.171 — Weight merge

Multiple compatible models can be merged through explicit algorithm.

## 531.172 — Compatibility

Architecture/schema must match or transformation defines mapping.

## 531.173 — Interpolation

Weight interpolation explicit.

## 531.174 — Adapter merge

Adapters can merge into base.

## 531.175 — Conflict

Incompatible parameters produce error.

## 531.176 — Merge provenance

All parent models recorded.

## 531.177 — Evaluation

Merged model evaluated separately.

## 531.178 — No semantic assumption

Merge is never assumed equivalent to either parent.

## 531.179 — Artifact identity

Merged artifact gets new identity.

## 531.180 — Reproducibility

Merge algorithm/config/version recorded.

---

# MODEL SHARDING & PACKING

## 531.181 — Shard

Large model can split across artifacts.

## 531.182 — Shard index

Index maps logical tensor → shard.

## 531.183 — Shard integrity

Each shard hashed.

## 531.184 — Partial loading

Only required shards may load.

## 531.185 — Device sharding

Runtime sharding separate from storage sharding.

## 531.186 — Tensor parallel packing

Deployment transformation can produce device-specific layout.

## 531.187 — Reassembly

Logical model identity preserved.

## 531.188 — Missing shard

Hard error unless optional artifact explicitly declared.

## 531.189 — Streaming load

Shards may stream.

## 531.190 — Cache

Shard cache integrates 506/529.

---

# SECURITY

## 531.191 — Untrusted model

Transformation input is untrusted artifact.

## 531.192 — No arbitrary code execution

Loading model data cannot execute arbitrary code.

## 531.193 — Resource limits

Transformation has CPU/RAM/GPU/storage limits.

## 531.194 — Malformed sparse data

Rejected safely.

## 531.195 — Malformed quantization metadata

Rejected.

## 531.196 — Hash verification

Input artifacts verified where configured.

## 531.197 — Provenance

Source model provenance retained.

## 531.198 — Dataset privacy

Calibration/distillation datasets follow access policy.

## 531.199 — Secret isolation

Secrets cannot become model weights accidentally through logging/artifacts.

## 531.200 — Audit

Transform operations are auditable.

---

# AI INTROSPECTION

## 531.201 — Transformation query

```text
transform(id)
```

## 531.202 — Parent query

```text
parent_model(id)
```

## 531.203 — Difference

```text
model_diff(a, b)
```

## 531.204 — Compression report

```text
compression_report(model)
```

## 531.205 — Sparsity report

```text
sparsity_report(model)
```

## 531.206 — Precision report

```text
precision_report(model)
```

## 531.207 — Memory report

```text
memory_report(model, target)
```

## 531.208 — Transformation reason

```text
why_transformed(node)
```

## 531.209 — Missed optimization

```text
why_not_pruned(node)
why_not_quantized(node)
why_not_fused(node)
```

## 531.210 — Full lineage

```text
lineage(deployed_model)
```

---

# 531.211 — HARD INVARIANTS

1. Model transformation khác compiler optimization.
2. Transformation có identity.
3. Transformation có input model.
4. Transformation có output model.
5. Transformation type được record.
6. Transformation config được record.
7. Transformation toolchain được record.
8. Target assumptions được record.
9. Dataset dependency được record.
10. Evidence được link.
11. Model lineage được preserve.
12. Exact equivalence khác numerical equivalence.
13. Task equivalence khác numerical equivalence.
14. Approximation phải được identify.
15. Unknown equivalence không được coi là equivalent.
16. Weight pruning được hỗ trợ.
17. Unstructured pruning được hỗ trợ.
18. Structured pruning được hỗ trợ.
19. Block pruning được hỗ trợ.
20. N:M sparsity có thể hỗ trợ.
21. Magnitude pruning có thể hỗ trợ.
22. Learned pruning có thể hỗ trợ.
23. Mask có identity.
24. Permanent pruning khác logical pruning.
25. Sparse representation explicit.
26. Sparse density được record.
27. Sparse kernel capability được kiểm tra.
28. Dense fallback explicit.
29. Sparse layout explicit.
30. Sparse index format versioned.
31. Dense↔sparse conversion explicit.
32. Sparse memory được measure.
33. Sparse compute không phải guarantee.
34. Sparse invariants được validate.
35. Quantization được hỗ trợ.
36. Quantization dtype explicit.
37. Scale explicit.
38. Zero-point explicit khi cần.
39. Per-tensor quantization được hỗ trợ.
40. Per-channel được hỗ trợ.
41. Group-wise có thể hỗ trợ.
42. Weight-only được hỗ trợ.
43. Activation quantization explicit.
44. KV quantization có thể hỗ trợ.
45. Calibration dataset được pin.
46. Calibration statistics được record.
47. Quantization error được measure.
48. QAT được hỗ trợ.
49. Fake quantization khác physical quantization.
50. Mixed precision được hỗ trợ.
51. Layer precision explicit.
52. Accumulator precision explicit.
53. Sensitive operations có thể giữ higher precision.
54. Precision policy explicit.
55. Hardware capability được xét.
56. Unsupported precision fallback/reject explicit.
57. Conversion cost được expose.
58. Precision provenance được preserve.
59. Numerical evidence được measure.
60. Không silent precision downgrade.
61. Knowledge distillation được hỗ trợ.
62. Teacher identity được record.
63. Student identity được record.
64. Teacher outputs explicit.
65. Distillation loss explicit.
66. Temperature explicit.
67. Feature distillation có thể hỗ trợ.
68. Attention distillation có thể hỗ trợ.
69. Distillation dataset được pin.
70. Teacher execution policy explicit.
71. Student lineage reference teacher.
72. LoRA được hỗ trợ.
73. Base model identity được preserve.
74. Adapter có identity.
75. Rank explicit.
76. Scaling explicit.
77. Multiple adapters được hỗ trợ.
78. Adapter composition order explicit.
79. Adapter merge là transformation mới.
80. Adapter removal được hỗ trợ.
81. Adapter provenance được preserve.
82. Serving có thể select adapter.
83. Prefix tuning có thể hỗ trợ.
84. Prompt tuning có thể hỗ trợ.
85. Bias-only adaptation có thể hỗ trợ.
86. Sparse adapters có thể hỗ trợ.
87. Low-rank variants có thể hỗ trợ.
88. Adapter target layers explicit.
89. Adapter compatibility được verify.
90. Adapter version độc lập.
91. Adapter có thể đóng gói riêng.
92. Parameter mutation không được hidden.
93. Weight sharing được hỗ trợ.
94. Shared parameter có physical identity.
95. Alias relationship được preserve.
96. Compiler không tự duplicate shared weights nếu không explicit.
97. Shared gradient semantics explicit.
98. Serialization giữ sharing.
99. Loader restore sharing.
100. Quantization giữ sharing correctness.
101. In-place mutation yêu cầu ownership phù hợp.
102. Reference counting không bắt buộc.
103. Physical/logical parameter size được distinguish.
104. Vocabulary optimization được hỗ trợ.
105. Token remapping được preserve.
106. Embedding resize đồng bộ.
107. Tied output head được xử lý.
108. Tokenizer compatibility được verify.
109. Special tokens không được silent remove.
110. Added vocabulary là transformation riêng.
111. Vocabulary provenance được preserve.
112. Serving reject tokenizer/model mismatch.
113. Storage compression khác numerical quantization.
114. Weight packing được hỗ trợ.
115. Compressed weights có explicit format.
116. Decompression semantics explicit.
117. mmap weight loading có thể hỗ trợ.
118. Lazy weight loading được hỗ trợ.
119. Weight prefetch có thể hỗ trợ.
120. CPU/GPU residency explicit.
121. Compression provenance được preserve.
122. Layer fusion integrate 504.
123. Operator elimination được hỗ trợ.
124. Constant folding integrate 504.
125. Dead branch elimination được hỗ trợ.
126. Layout transformation explicit.
127. Kernel-specific packing được hỗ trợ.
128. Activation recomputation có thể hỗ trợ.
129. Operator substitution obey numerical policy.
130. Graph provenance được preserve.
131. Transformation có thể reversible khi format cho phép.
132. Parameter count được report.
133. Physical bytes được report.
134. Runtime memory được report.
135. Peak memory được report.
136. Weight bandwidth được report.
137. Activation memory được report.
138. KV memory được report.
139. Metadata overhead được report.
140. Compression ratio phải nêu baseline.
141. Target architecture được record.
142. CPU ISA features được record.
143. GPU architecture được record.
144. Target memory budget có thể constrain transformation.
145. Latency budget có thể constrain transformation.
146. Throughput regime được record.
147. Batch regime được record.
148. LLM context regime có thể được record.
149. Streaming regime được record.
150. Optimization fingerprint được tạo.
151. Transformation pipeline validate trước transform.
152. Analysis phase riêng.
153. Transformation transactional.
154. Partial artifact không được publish.
155. Transformation config deterministic.
156. Transform cache content-addressed.
157. Cache invalidation theo input identity.
158. Independent transformations có thể parallel.
159. Deterministic mode deterministic.
160. Baseline evaluation được lưu.
161. Transformed evaluation riêng.
162. Task metrics không bị gộp thành một score.
163. Numerical deviation được report.
164. Performance được report.
165. Size được report.
166. Evaluation dataset được pin.
167. Evaluation hardware được record.
168. Statistical uncertainty được preserve.
169. Automated optimization search được hỗ trợ.
170. Search space explicit.
171. Constraints explicit.
172. Candidate có identity.
173. Candidate lineage được preserve.
174. Candidate evaluation required.
175. Failed candidates traceable.
176. Search budget explicit.
177. Parallel search được hỗ trợ.
178. Search seed/config được record.
179. Model merge được hỗ trợ.
180. Merge compatibility được verify.
181. Weight interpolation explicit.
182. Adapter merge được hỗ trợ.
183. Merge conflict tạo error.
184. Merge provenance đầy đủ.
185. Merge evaluation riêng.
186. Merge không được coi equivalent với parent.
187. Merge artifact có identity mới.
188. Merge config reproducible.
189. Model sharding được hỗ trợ.
190. Shard index được version.
191. Shard integrity được verify.
192. Partial loading có thể hỗ trợ.
193. Storage sharding khác runtime sharding.
194. Tensor parallel packing có thể hỗ trợ.
195. Logical model identity được preserve.
196. Missing required shard là error.
197. Shard streaming có thể hỗ trợ.
198. Shard cache có identity.
199. Untrusted model artifacts được xử lý an toàn.
200. Transformation không được arbitrary-code-execute từ model data.
201. Transformation resource limits được hỗ trợ.
202. Malformed sparse data bị reject.
203. Malformed quantization metadata bị reject.
204. Artifact hash có thể verify.
205. Model provenance không bị mất.
206. Calibration/distillation data obey access policy.
207. Secrets không được vô tình trở thành artifact/log.
208. Transformation audit được hỗ trợ.
209. Transformation query được hỗ trợ.
210. Parent model query được hỗ trợ.
211. Model diff được hỗ trợ.
212. Compression report được hỗ trợ.
213. Sparsity report được hỗ trợ.
214. Precision report được hỗ trợ.
215. Memory report được hỗ trợ.
216. Transformation rationale query được hỗ trợ.
217. Missed-transformation query được hỗ trợ.
218. Full deployed-model lineage được hỗ trợ.
219. Transformation không được tự động publish model.
220. Transformation không được tự động deploy model.
221. Evaluation evidence phải phân biệt measurement với guarantee.
222. Target-specific optimization không được giả định portable.
223. Numerical-policy change phải tạo transformation identity mới.
224. Model/tokenizer identity phải đồng bộ.
225. Base model + adapter identity phải được preserve.
226. Logical sparsity không được báo cáo như physical compression nếu weights vẫn tồn tại.
227. Storage compression không được báo cáo như compute reduction.
228. Parameter reduction không được báo cáo như latency reduction nếu chưa benchmark.
229. Model size reduction không được coi là quality preservation.
230. **Axiom Model Optimization phải cung cấp một transformation framework có thể prune, sparse hóa, quantize, distill, low-rank adapt, share/compress/pack/shard model và tối ưu theo target, nhưng mọi thay đổi semantics, numerical behavior, memory layout, artifact identity và provenance phải explicit, reproducible và có evidence riêng; compiler không được biến một model approximation thành “cùng model” chỉ vì graph vẫn chạy được.**

**BOOTSTRAP-531 hoàn tất / LOCKED.**

---

# BOOTSTRAP-532 — AI EVALUATION, BENCHMARKING, MODEL QUALITY, SAFETY TESTING, RED-TEAMING, REGRESSION & RELEASE GATE FOUNDATION

**Trạng thái: COMPLETED / LOCKED**

532 xây dựng tầng đánh giá thống nhất cho model/agent sau 503–531. Mục tiêu là biến:

```text
"model có vẻ tốt"
```

thành:

```text
Model
 ↓
Evaluation Definition
 ↓
Dataset / Scenario
 ↓
Execution
 ↓
Measurements
 ↓
Evidence
 ↓
Regression Comparison
 ↓
Release Policy
```

### 532.1 — Evaluation ≠ Training

Evaluation không được tự động cập nhật model.

### 532.2 — Benchmark ≠ Quality

Benchmark là measurement procedure.

### 532.3 — Safety ≠ Accuracy

Safety metrics tách khỏi task metrics.

### 532.4 — EvaluationRun

```text
EvaluationRun {
    EvaluationId
    ModelId
    DatasetId
    EvaluatorVersion
    Configuration
    Target
    Results
    Evidence
}
```

### 532.5 — Dataset pinning

Exact evaluation dataset/version được pin.

### 532.6 — Evaluator pinning

Evaluator implementation/version được record.

### 532.7 — Target pinning

Hardware/software target được record khi ảnh hưởng kết quả.

### 532.8 — Reproducibility

Seed, preprocessing, tokenizer, model artifact và evaluation config được record.

### 532.9 — Task metrics

Classification/generation/retrieval/vision/audio/video metrics tùy task.

### 532.10 — Metric definition

Mỗi metric có:

```text
MetricId
Definition
Input
Output
Direction
Aggregation
Version
```

### 532.11 — No universal quality score

Axiom không tạo một "AI quality score" tổng hợp mặc định.

### 532.12 — Statistical results

Mean/median/std/percentile/confidence interval khi phù hợp.

### 532.13 — Slice evaluation

Đánh giá theo subset:

- language;
- domain;
- input length;
- modality;
- difficulty;
- demographic/context category nếu dataset hợp pháp và phù hợp.

### 532.14 — Regression

So sánh model A/B theo cùng evaluation definition.

### 532.15 — Release gate

Release gate là project policy, không phải compiler verdict.

### 532.16 — Accuracy gate

Có thể yêu cầu metric threshold.

### 532.17 — Safety gate

Có thể yêu cầu safety criteria.

### 532.18 — Performance gate

Latency/throughput/memory limits.

### 532.19 — Size gate

Artifact size limit.

### 532.20 — Cost gate

Compute/cost constraint.

### 532.21 — Failure gate

Critical evaluation failure có thể block release theo policy.

### 532.22 — Red-team scenarios

Adversarial evaluation scenarios được model hóa thành test cases.

### 532.23 — Prompt injection evaluation

Agent/model tool-use injection scenarios.

### 532.24 — Data exfiltration evaluation

Kiểm tra model/agent không làm lộ protected context trong scenario được định nghĩa.

### 532.25 — Tool authorization evaluation

Tool calls phải obey capability/authorization policy.

### 532.26 — Jailbreak evaluation

Jailbreak tests được lưu như scenario/evidence, không coi một test suite là proof toàn diện.

### 532.27 — Hallucination evaluation

Grounded tasks có evidence set.

### 532.28 — Citation evaluation

Citation correctness/completeness có thể đo.

### 532.29 — RAG evaluation

Retrieve → rerank → answer được evaluate từng stage.

### 532.30 — Retrieval metrics

Recall@K, precision@K, MRR/NDCG-like metrics tùy evaluator.

### 532.31 — Generation evaluation

Exact match, task metric, human/LLM evaluator hoặc custom verifier.

### 532.32 — LLM-as-judge

Có thể hỗ trợ nhưng evaluator model/version/prompt/rubric phải được record.

### 532.33 — Human evaluation

Human ratings có schema/version và inter-rater metadata.

### 532.34 — Automated verifier

Deterministic verifier được ưu tiên khi có thể.

### 532.35 — Reference answers

Reference data versioned.

### 532.36 — Pairwise evaluation

A/B pair comparison được lưu raw, không chuyển thành global ranking mặc định.

### 532.37 — Robustness

Input perturbation/format/noise tests.

### 532.38 — Distribution shift

Evaluation dataset khác training distribution được identify.

### 532.39 — Long-context

Context-length slices.

### 532.40 — Multilingual

Language-specific evaluation.

### 532.41 — Multimodal

Cross-modal scenarios.

### 532.42 — Speech

WER/CER/latency/streaming metrics tùy task.

### 532.43 — TTS

Intelligibility/naturalness/style/latency metrics có schema rõ ràng.

### 532.44 — Vision

Detection/segmentation/classification/retrieval metrics.

### 532.45 — Video

Temporal consistency/task-specific metrics.

### 532.46 — Agent evaluation

Agent trajectory được record:

```text
Goal
→ Observation
→ Decision
→ Tool
→ Result
→ Next step
```

### 532.47 — Agent success

Task completion criterion explicit.

### 532.48 — Tool safety

Unauthorized/unsafe tool call được test.

### 532.49 — Loop evaluation

Infinite/repetitive agent loops detected.

### 532.50 — Budget evaluation

Token/time/tool/cost limits tested.

### 532.51 — Memory evaluation

Memory retrieval precision/recall/freshness/privacy.

### 532.52 — Knowledge evaluation

RAG evidence grounding.

### 532.53 — Continual evaluation

Model updates trigger selected evaluation suites.

### 532.54 — Regression matrix

```text
Model × Dataset × Task × Target × Config
```

### 532.55 — Baseline registry

Known evaluation baselines stored.

### 532.56 — Evaluation artifact

Raw outputs retained according to privacy policy.

### 532.57 — Reproducible replay

Evaluation scenario replay supported.

### 532.58 — Deterministic evaluation

Deterministic mode where model/runtime supports it.

### 532.59 — Randomized evaluation

Seed and RNG state recorded.

### 532.60 — Environment metadata

CPU/GPU/driver/runtime/compiler recorded.

### 532.61 — Error analysis

False positives/negatives and failure categories.

### 532.62 — Slice failure analysis

Failures grouped by explicit dimensions.

### 532.63 — Threshold analysis

Threshold changes produce new evaluation configuration.

### 532.64 — Calibration

Probability calibration metrics where applicable.

### 532.65 — Confidence

Model confidence must not automatically be interpreted as correctness probability.

### 532.66 — Uncertainty

Evaluator can preserve uncertainty.

### 532.67 — Statistical significance

Optional statistical tests with assumptions recorded.

### 532.68 — Multiple comparisons

Evaluation reports can identify multiple-testing concerns.

### 532.69 — Dataset leakage

Potential train/eval contamination can be tracked.

### 532.70 — Benchmark contamination

Known contamination checks can be represented.

### 532.71 — Privacy

Evaluation datasets follow access controls.

### 532.72 — Sensitive outputs

Raw outputs can be redacted/restricted.

### 532.73 — Secret handling

Secrets never required for ordinary evaluator logging.

### 532.74 — Safety incident

Critical scenario failure creates structured incident record.

### 532.75 — Incident provenance

Incident references model/evaluator/scenario/input/output/policy.

### 532.76 — Regression alert

Automated alerting optional.

### 532.77 — Release candidate

Model can enter `Candidate` state.

### 532.78 — Release state

```text
Draft
Candidate
Validated
Released
Deprecated
Withdrawn
```

### 532.79 — Approval

Human/project policy approval boundary explicit.

### 532.80 — No automatic release

Evaluation passing does not silently deploy/publish.

### 532.81 — Serving integration

Validated model can be referenced by 529 deployment.

### 532.82 — Transformation integration

531 transformed model must be re-evaluated according to policy.

### 532.83 — Training integration

530 training run can automatically trigger evaluation.

### 532.84 — Evaluation dependency graph

Evaluation depends on exact artifacts.

### 532.85 — Cache

Identical evaluation inputs can reuse cached results.

### 532.86 — Cache correctness

Evaluator version/config/dataset/model/target are cache inputs.

### 532.87 — Artifact immutability

Completed evaluation result immutable.

### 532.88 — Report formats

JSON/JSONL/Markdown/HTML/binary structured artifact.

### 532.89 — Machine-readable

Every result machine-readable.

### 532.90 — AI query

AI can query evaluation evidence without parsing arbitrary reports.

### 532.91 — Query

```text
evaluate(model, suite)
```

### 532.92 — Compare

```text
compare_evaluations(a, b)
```

### 532.93 — Failure query

```text
evaluation_failures(run)
```

### 532.94 — Slice query

```text
evaluation_slice(run, filter)
```

### 532.95 — Evidence query

```text
evidence(result)
```

### 532.96 — Provenance query

```text
evaluation_lineage(result)
```

### 532.97 — Why gate

```text
why_release_blocked(model)
```

### 532.98 — Regression explanation

```text
why_regressed(model_a, model_b)
```

### 532.99 — Security

Evaluation runner may execute untrusted model/input data and therefore obey 490 sandbox/capability policies.

### 532.100 — Evaluation isolation

Untrusted evaluation code cannot gain evaluator host authority.

---

## 532.101 — HARD INVARIANTS

1. Evaluation khác training.
2. Evaluation khác benchmark.
3. Accuracy khác safety.
4. EvaluationRun có identity.
5. Model artifact được pin.
6. Dataset được pin.
7. Evaluator version được pin.
8. Evaluation config được pin.
9. Target được pin khi relevant.
10. Random state được record.
11. Preprocessing được record.
12. Tokenizer identity được record.
13. Metrics có definition.
14. Metrics có version.
15. Metric aggregation explicit.
16. Không có universal quality score.
17. Statistical information được preserve.
18. Slice evaluation được hỗ trợ.
19. Regression evaluation được hỗ trợ.
20. Release gate là policy.
21. Accuracy gate có thể cấu hình.
22. Safety gate có thể cấu hình.
23. Performance gate có thể cấu hình.
24. Size gate có thể cấu hình.
25. Cost gate có thể cấu hình.
26. Failure gate có thể cấu hình.
27. Red-team scenarios được hỗ trợ.
28. Prompt-injection testing được hỗ trợ.
29. Data-exfiltration testing được hỗ trợ.
30. Tool-authorization testing được hỗ trợ.
31. Jailbreak testing được hỗ trợ.
32. Safety test không phải proof toàn diện.
33. Grounding evaluation được hỗ trợ.
34. Citation evaluation được hỗ trợ.
35. RAG pipeline evaluation được hỗ trợ.
36. Retrieval metrics được hỗ trợ.
37. Generation metrics được hỗ trợ.
38. LLM-as-judge phải record evaluator identity.
39. Human evaluation có schema.
40. Automated deterministic verifier được hỗ trợ.
41. Reference data versioned.
42. Pairwise results giữ raw evidence.
43. Không tạo global ranking mặc định.
44. Robustness testing được hỗ trợ.
45. Distribution shift được identify.
46. Long-context evaluation được hỗ trợ.
47. Multilingual evaluation được hỗ trợ.
48. Multimodal evaluation được hỗ trợ.
49. Speech evaluation được hỗ trợ.
50. TTS evaluation được hỗ trợ.
51. Vision evaluation được hỗ trợ.
52. Video evaluation được hỗ trợ.
53. Agent trajectory được record.
54. Agent success criterion explicit.
55. Tool safety được evaluate.
56. Loop behavior được evaluate.
57. Agent budget được evaluate.
58. Memory behavior được evaluate.
59. Knowledge grounding được evaluate.
60. Continual evaluation được hỗ trợ.
61. Regression matrix được hỗ trợ.
62. Baselines được version.
63. Raw evaluation artifacts có policy.
64. Replay được hỗ trợ.
65. Deterministic mode được hỗ trợ khi possible.
66. Random evaluation record seed.
67. Hardware environment được record.
68. Runtime/compiler được record.
69. Failure analysis được hỗ trợ.
70. Slice failure analysis được hỗ trợ.
71. Threshold changes tạo evaluation config mới.
72. Calibration metrics được hỗ trợ.
73. Confidence không mặc định là correctness probability.
74. Uncertainty được preserve.
75. Statistical tests record assumptions.
76. Multiple-comparison concerns có thể report.
77. Dataset leakage có thể track.
78. Benchmark contamination có thể track.
79. Evaluation privacy được enforce.
80. Sensitive outputs có access policy.
81. Secrets không nằm trong ordinary logs.
82. Safety incident có structured identity.
83. Incident provenance đầy đủ.
84. Regression alert có thể hỗ trợ.
85. Candidate state được hỗ trợ.
86. Release lifecycle explicit.
87. Approval boundary explicit.
88. Evaluation pass không auto-release.
89. Serving integration với 529.
90. Transformation integration với 531.
91. Training integration với 530.
92. Evaluation dependency graph được preserve.
93. Evaluation cache có đầy đủ correctness inputs.
94. Completed evaluation immutable.
95. Structured report formats được hỗ trợ.
96. Machine-readable result bắt buộc.
97. AI evaluation query được hỗ trợ.
98. Evaluation comparison được hỗ trợ.
99. Failure/slice/evidence/provenance query được hỗ trợ.
100. Release-block explanation được hỗ trợ.
101. Regression explanation được hỗ trợ.
102. Evaluation runner obey security sandbox.
103. Untrusted model không có evaluator host authority.
104. Evaluator code có explicit capabilities.
105. Network access trong evaluator explicit.
106. Filesystem access explicit.
107. Process execution explicit.
108. GPU access explicit.
109. Evaluation resource limits được enforce.
110. Timeout được enforce.
111. Cancellation được hỗ trợ.
112. Partial evaluation state được identify.
113. Retry không làm mất run identity.
114. Evaluator nondeterminism được record.
115. Model stochasticity được distinguish evaluator nondeterminism.
116. Numerical mode được record.
117. Quantized model phải được evaluate riêng.
118. Pruned model phải được evaluate riêng.
119. Distilled model phải được evaluate riêng.
120. Adapter model phải được evaluate với adapter identity.
121. Deployment target có thể tạo evaluation suite riêng.
122. Batch regime được record cho performance tests.
123. Streaming regime được record.
124. Context length được record.
125. Tokenizer/model mismatch là evaluation error.
126. Evaluation output không được tự động trở thành trusted instruction.
127. External evaluation data là untrusted data.
128. Human labels có provenance.
129. Synthetic evaluation data được identify.
130. Evaluator prompt được version.
131. Judge model temperature/config được record.
132. Human evaluator protocol được version.
133. Evaluation schema được version.
134. Cross-version comparison cần compatibility metadata.
135. Missing evidence không được coi là pass.
136. Failed evaluator run không được coi là model failure nếu evaluator itself failed.
137. Infrastructure failure khác model failure.
138. Data failure khác model failure.
139. Policy violation khác task failure.
140. Safety failure taxonomy explicit.
141. Critical failures có thể block release theo policy.
142. Release gate decision provenance được record.
143. Gate policy version được record.
144. Gate result immutable.
145. Manual override có identity/audit khi project cho phép.
146. Override không xóa failed evidence.
147. Withdrawn model vẫn giữ evaluation lineage.
148. Deprecated model vẫn queryable.
149. Evaluation artifacts có retention policy.
150. Privacy deletion phải preserve required integrity metadata.
151. Model comparison không tự động imply superiority.
152. Metric differences phải kèm evaluation population.
153. Historical benchmark không được trình bày như current result.
154. Different datasets không được coi direct comparison nếu semantics không tương thích.
155. Different evaluator versions phải được identify.
156. Different hardware performance không được trộn.
157. Confidence intervals không được coi guarantee.
158. Correlation không được coi causal explanation.
159. AI-generated analysis phải distinguish evidence với interpretation.
160. Evaluation report phải link raw evidence khi policy cho phép.
161. Search-based optimization phải evaluate candidates độc lập.
162. Model merge phải re-evaluate.
163. Model transformation phải re-evaluate theo policy.
164. Training checkpoint release phải evaluate exact checkpoint.
165. Serving artifact phải trace về evaluated artifact.
166. Deployment mutation phải invalidate affected evaluation evidence.
167. Evaluation cache invalidates khi model hash đổi.
168. Evaluation cache invalidates khi evaluator đổi.
169. Evaluation cache invalidates khi dataset/config đổi.
170. Safety suite version được pin.
171. Red-team suite version được pin.
172. Regression baseline được pin.
173. Evaluation runner có deterministic replay mode.
174. Replay artifact có provenance.
175. Fuzz-generated inputs có corpus identity.
176. Adversarial test inputs được retain theo privacy policy.
177. Evaluation scheduler integrates 471.
178. Evaluation trace integrates 481.
179. Evaluation metrics integrate 475/476.
180. Coverage integrate 477.
181. Static analysis evidence integrate 478.
182. Contract evidence integrate 479.
183. Sanitizer evidence integrate 480.
184. Performance evidence integrate 481.
185. Model provenance integrates 506/528.
186. AI knowledge graph integrates 512.
187. Agent evaluation integrates 511.
188. Tool evaluation integrates 513.
189. Serving evaluation integrates 529.
190. No hidden network calls.
191. No hidden model downloads.
192. No hidden telemetry.
193. No automatic deployment.
194. No automatic model replacement.
195. No automatic deletion of failed evidence.
196. No universal benchmark.
197. No universal quality ranking.
198. No universal safety guarantee.
199. Evaluation evidence must remain distinguishable from proof.
200. **Axiom Evaluation phải biến chất lượng model/agent thành một tập bằng chứng có provenance, dataset/evaluator/version/target rõ ràng, bao gồm accuracy, robustness, safety, grounding, performance và regression; hệ thống có thể tự động kiểm tra release policy nhưng không được biến một benchmark hoặc một metric thành phán quyết chung về chất lượng hay độ an toàn của model.**

**BOOTSTRAP-532 hoàn tất / LOCKED.**

### Tiếp theo

**`BOOTSTRAP-533 — AI MODEL REGISTRY, MODEL VERSIONING, ARTIFACT LINEAGE, MODEL CARD, DEPLOYMENT CHANNEL, GOVERNANCE & LIFECYCLE MANAGEMENT`**