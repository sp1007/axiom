# BOOTSTRAP-523 — AI OBSERVABILITY & INTERPRETABILITY, EXPLANATION, ATTRIBUTION, ACTIVATION TRACING, ATTENTION/FEATURE ANALYSIS, MODEL DEBUGGING & DECISION PROVENANCE

**Trạng thái: COMPLETED / LOCKED**

523 xây dựng tầng để quan sát **model đã thực sự làm gì trong quá trình inference/training**, nối 503–522 với profiling, tracing và AI tooling.

Mục tiêu không phải tạo ra một “explanation” giả định là sự thật. Axiom phải phân biệt rõ:

```text
Observed Execution
       │
       ├── Inputs
       ├── Intermediate Activations
       ├── Attention / Scores
       ├── Operator Outputs
       ├── Gradients
       ├── Selected Actions
       └── Final Output
                │
                ↓
        Analysis / Attribution
                │
                ↓
       Explanation Artifact
                │
                ↓
        Evidence + Method
```

Một explanation luôn phải kèm **phương pháp tạo ra nó và mức độ bằng chứng**.

---

# 523.1 — Observation ≠ Explanation

Observation là dữ liệu trực tiếp từ execution.

Explanation là kết quả phân tích observation.

Không được coi explanation là execution fact.

## 523.2 — Attribution ≠ Causality

Feature attribution cho biết một phương pháp attribution gán contribution như thế nào.

Nó không tự động chứng minh causal effect.

## 523.3 — Attention ≠ Universal Explanation

Attention weights có thể được quan sát, nhưng không được compiler/runtime mặc định diễn giải chúng là “lý do” duy nhất của model.

## 523.4 — Explanation artifact

```text
ExplanationArtifact {
    model_id
    model_version
    input_id
    output_id
    method
    configuration
    evidence
    provenance
}
```

## 523.5 — Evidence type

```text
Observed
Derived
Estimated
Heuristic
Counterfactual
HumanAnnotated
Unknown
```

## 523.6 — Method identity

Mọi explanation method có:

```text
MethodId
Version
ConfigurationHash
```

## 523.7 — Reproducibility

Explanation có thể reproduce khi model/input/method/environment đủ deterministic.

## 523.8 — Model version

Explanation phải reference exact model artifact.

## 523.9 — Input identity

Input phải có identity hoặc content hash khi possible.

## 523.10 — Output identity

Output/logit/action được reference.

---

# EXECUTION OBSERVABILITY

## 523.11 — Execution trace

AI execution có thể tạo trace.

## 523.12 — Trace scope

Có thể trace:

- whole request;
- layer;
- operator;
- tensor;
- kernel;
- device;
- tool call;
- agent step.

## 523.13 — Trace levels

```text
none
request
operator
tensor
debug
full
```

## 523.14 — Selective tracing

Chỉ capture selected nodes/tensors.

## 523.15 — Sampling

Large workloads có thể sample execution.

## 523.16 — Trace overhead

Trace overhead phải được đo.

## 523.17 — Trace identity

Trace có build/model/runtime identity.

## 523.18 — Trace timestamps

Integrate 474/481 temporal semantics.

## 523.19 — Cross-device trace

CPU/GPU/NPU events có thể được correlate khi clocks có conversion metadata.

## 523.20 — Distributed trace

Distributed model execution có correlation IDs.

---

# ACTIVATION TRACING

## 523.21 — Activation

Intermediate tensor output của operator/layer.

## 523.22 — Activation capture

Có thể capture activation theo node.

## 523.23 — Tensor metadata

Capture phải preserve:

```text
dtype
shape
layout
device
stride
```

## 523.24 — Statistics mode

Thay vì raw tensor có thể capture:

```text
min
max
mean
variance
norm
histogram
NaN count
Inf count
```

## 523.25 — Histogram

Histogram configuration phải được lưu.

## 523.26 — Quantile

Quantiles có thể được capture.

## 523.27 — Sampling tensor

Large tensors có thể sample với explicit sampling method.

## 523.28 — Raw capture

Raw activation capture là optional.

## 523.29 — Compression

Activation trace có thể compressed.

## 523.30 — Privacy

Activation có thể chứa sensitive information và phải obey access policy.

---

# ACTIVATION COMPARISON

## 523.31 — Reference activation

Có thể compare activation với reference model.

## 523.32 — Layer diff

Layer-by-layer difference.

## 523.33 — Numerical metrics

```text
max_abs_error
mean_abs_error
RMSE
relative_error
cosine_similarity
```

## 523.34 — Tolerance

Tolerance explicit.

## 523.35 — Shape mismatch

Shape mismatch là structured diagnostic.

## 523.36 — Dtype mismatch

Dtype changes được report.

## 523.37 — Layout mismatch

Layout mismatch distinguish khỏi numerical mismatch.

## 523.38 — Device mismatch

Device placement difference được record.

## 523.39 — NaN propagation

NaN/Inf propagation có thể trace.

## 523.40 — First divergence

Debugger có thể tìm node đầu tiên khác reference trong deterministic comparison.

---

# ATTENTION ANALYSIS

## 523.41 — Attention observation

Attention matrices có thể capture nếu model/backend expose.

## 523.42 — Head identity

Attention head có stable logical identity.

## 523.43 — Layer identity

Attention layer identity được preserve.

## 523.44 — Token mapping

Attention entries map tới token offsets từ 509.

## 523.45 — Multimodal mapping

Vision/audio/video tokens có provenance từ 510.

## 523.46 — Sparse attention

Sparse attention representation được preserve.

## 523.47 — Aggregation

Head/layer aggregation phải ghi rõ method.

## 523.48 — Visualization

Visualization là tooling layer.

## 523.49 — Interpretation warning

Attention visualization không tự động được gắn nhãn causal explanation.

## 523.50 — Large attention

Large attention tensors có thể stream/sample.

---

# FEATURE ATTRIBUTION

## 523.51 — Attribution target

Attribution phải specify target:

```text
logit
probability
embedding dimension
classification output
generated token
reward
agent action
```

## 523.52 — Input feature

Feature identity và offset được preserve.

## 523.53 — Token attribution

Text attribution map về token/character/grapheme provenance.

## 523.54 — Image attribution

Pixel/patch/region attribution.

## 523.55 — Audio attribution

Time-frequency/sample-region attribution.

## 523.56 — Video attribution

Spatial-temporal attribution.

## 523.57 — Multimodal attribution

Attribution có thể phân tách theo modality.

## 523.58 — Methods

Foundation có thể support:

- gradient;
- integrated gradients;
- perturbation;
- occlusion;
- SHAP-like methods;
- attention-based analysis;
- counterfactual analysis.

## 523.59 — Method assumptions

Method assumptions được lưu.

## 523.60 — Approximation

Approximate methods phải được mark là approximate.

---

# GRADIENT ANALYSIS

## 523.61 — Gradient capture

Training execution có thể capture gradients.

## 523.62 — Gradient statistics

Min/max/mean/norm/histogram.

## 523.63 — Vanishing gradient

Có thể detect suspiciously small gradients.

## 523.64 — Exploding gradient

Có thể detect unusually large gradients.

## 523.65 — NaN gradient

NaN/Inf gradient phải được detect khi instrumentation enabled.

## 523.66 — Per-layer gradient

Layer-level analysis.

## 523.67 — Gradient clipping

Clipping event được record.

## 523.68 — Optimizer state

Optimizer state statistics có thể inspect.

## 523.69 — Checkpoint comparison

Gradient behavior có thể compare giữa checkpoints.

## 523.70 — Debug mode

Gradient tracing không được trở thành mặc định production overhead.

---

# MODEL STRUCTURE INSPECTION

## 523.71 — Model graph

Integrate graph IR 504.

## 523.72 — Layer tree

Logical model hierarchy.

## 523.73 — Parameter inventory

Mỗi parameter có:

```text
name
shape
dtype
device
storage
trainable
```

## 523.74 — Parameter statistics

Size/norm/distribution.

## 523.75 — Parameter sharing

Shared parameters được identify.

## 523.76 — Frozen parameters

Frozen/trainable distinction.

## 523.77 — Adapter parameters

LoRA/adapter parameters từ 521 được identify.

## 523.78 — Quantized parameters

Quantization metadata được expose.

## 523.79 — Sparse parameters

Sparsity metadata được expose.

## 523.80 — Model diff

Hai model versions có semantic diff.

---

# COUNTERFACTUAL ANALYSIS

## 523.81 — Counterfactual

Counterfactual là một input/model modification được tạo có chủ đích để compare behavior.

## 523.82 — Perturbation

Perturbation phải record.

## 523.83 — Paired execution

Original/counterfactual executions được linked.

## 523.84 — Output delta

Difference được measure.

## 523.85 — Causal claim

Không được tự động chuyển output delta thành causal proof.

## 523.86 — Input preservation

Original input phải remain available/referenceable.

## 523.87 — Counterfactual validity

Transformation có thể có validity constraints.

## 523.88 — Invalid counterfactual

Invalid transformation phải được mark.

## 523.89 — Human-defined counterfactual

Human-authored scenario có provenance.

## 523.90 — Automated generation

Automated counterfactual generator có version/config identity.

---

# MODEL DEBUGGER

## 523.91 — Breakpoint

Logical breakpoint có thể đặt tại model node.

## 523.92 — Tensor breakpoint

Condition có thể trigger khi tensor matches predicate.

## 523.93 — Value condition

Ví dụ:

```text
is_nan(x)
max(x) > threshold
shape(x) == expected
```

## 523.94 — Step execution

Debugger có thể execute graph từng node ở debug backend.

## 523.95 — Inspect tensor

Tensor metadata/statistics/raw subset.

## 523.96 — Compare checkpoint

Checkpoint-to-checkpoint inspection.

## 523.97 — Compare backend

CPU/GPU backend output comparison.

## 523.98 — Deterministic replay

Replay mode integrate 435/481.

## 523.99 — Failure capture

Failure artifact chứa model/input/node/runtime context.

## 523.100 — Source provenance

Model operation có thể map về source/comptime/generated model definition nếu available.

---

# DECISION PROVENANCE

## 523.101 — Decision

AI output/action có provenance chain.

## 523.102 — Generation provenance

Generated token/output reference:

- model;
- tokenizer;
- prompt/input;
- generation configuration.

## 523.103 — Retrieval provenance

511/512 retrieval sources được reference.

## 523.104 — Tool provenance

Tool call reference tool identity/version.

## 523.105 — Agent provenance

Agent step identity.

## 523.106 — Policy provenance

522 policy decision được reference.

## 523.107 — Human approval

Human approval có explicit identity/token/reference khi system hỗ trợ.

## 523.108 — Final action provenance

Final external action reference complete chain.

## 523.109 — Provenance graph

```text id="f8m1g5"
Input
  ↓
Retrieval
  ↓
Prompt / Context
  ↓
Model
  ↓
Output
  ↓
Guardrail
  ↓
Tool Decision
  ↓
Tool
  ↓
External Effect
```

## 523.110 — Missing provenance

Missing provenance phải được biểu diễn là unknown, không tự động suy đoán.

---

# EXPLANATION API

## 523.111 — Explanation request

```text
ExplainRequest {
    target
    method
    scope
    configuration
}
```

## 523.112 — Explanation result

```text
ExplainResult {
    evidence
    attribution
    limitations
    provenance
}
```

## 523.113 — Limitations

Explanation phải có limitations metadata.

## 523.114 — Evidence links

Mỗi conclusion-derived value có thể link tới evidence.

## 523.115 — Confidence

Confidence có thể tồn tại nhưng không được coi là universal correctness probability.

## 523.116 — Uncertainty

Uncertainty phải được preserve.

## 523.117 — Human annotation

Human interpretation được distinguish khỏi machine-derived result.

## 523.118 — Explanation cache

Có thể cache explanation khi identity inputs/method unchanged.

## 523.119 — Cache invalidation

Model/input/method changes invalidate explanation.

## 523.120 — Privacy

Explanation output không được bypass source access controls.

---

# MODEL INTERPRETABILITY LIMITS

## 523.121 — No universal interpretability metric

Không có một số duy nhất đo “model interpretability”.

## 523.122 — Method dependence

Different methods có thể produce different attribution.

## 523.123 — Stability

Attribution stability có thể evaluate.

## 523.124 — Faithfulness

Faithfulness có thể được measured bằng method-specific tests.

## 523.125 — Completeness

Completeness semantics phải do method định nghĩa.

## 523.126 — Sensitivity

Sensitivity analysis được hỗ trợ.

## 523.127 — Sanity checks

Randomization/model parameter tests có thể validate explanation methods.

## 523.128 — Distribution shift

Explanation behavior có thể thay đổi khi input distribution thay đổi.

## 523.129 — Model change

Model update invalidates old explanation evidence.

## 523.130 — Policy change

Policy update invalidates relevant decision provenance/evaluation.

---

# AI TOOLING

## 523.131 — Query API

```text
trace(model)
activations(model, node)
attention(model, layer)
gradients(run)
attribution(input, target)
counterfactual(input)
decision_provenance(output)
model_diff(a,b)
explanation(id)
```

## 523.132 — Why query

AI có thể hỏi:

```text
why_output()
why_action()
why_prediction_changed()
why_activation_changed()
why_quantized()
why_fallback()
```

## 523.133 — Evidence-first response

Tooling phải trả evidence trước explanation prose.

## 523.134 — Machine-readable

Results có stable schema.

## 523.135 — Source links

Evidence có source/model/graph node references.

## 523.136 — Temporal links

Execution evidence có timestamps khi relevant.

## 523.137 — Security filtering

AI tooling respect access permissions.

## 523.138 — Large result handling

Large traces support query/filter/stream instead of mandatory full loading.

## 523.139 — Snapshot isolation

Inspection uses immutable execution/model snapshot.

## 523.140 — No hidden interpretation

Compiler/runtime không được silently insert semantic explanation claims.

---

# 523.141 — HARD INVARIANTS

1. Observation khác explanation.
2. Attribution khác causality.
3. Attention không mặc định là causal explanation.
4. Explanation là artifact.
5. Explanation reference exact model.
6. Explanation reference input.
7. Explanation reference output.
8. Explanation có method identity.
9. Explanation có configuration identity.
10. Evidence type được classify.
11. Observed/derived/estimated/heuristic được distinguish.
12. Counterfactual được distinguish.
13. Human annotation được distinguish.
14. Unknown được preserve.
15. Explanation có provenance.
16. Explanation có thể reproduce khi đủ deterministic inputs.
17. Execution trace được hỗ trợ.
18. Trace scope configurable.
19. Trace level configurable.
20. Selective tracing được hỗ trợ.
21. Trace overhead được đo.
22. Trace có build/model/runtime identity.
23. Temporal metadata được preserve.
24. Cross-device correlation explicit.
25. Distributed correlation được hỗ trợ.
26. Activation capture được hỗ trợ.
27. Activation metadata preserve dtype.
28. Activation metadata preserve shape.
29. Activation metadata preserve layout.
30. Activation metadata preserve device.
31. Activation statistics được hỗ trợ.
32. Histogram configuration được lưu.
33. Quantile analysis được hỗ trợ.
34. Tensor sampling method explicit.
35. Raw tensor capture optional.
36. Activation compression được hỗ trợ.
37. Activation privacy được enforce.
38. Reference activation comparison được hỗ trợ.
39. Layer diff được hỗ trợ.
40. Numerical comparison metrics explicit.
41. Tolerance explicit.
42. Shape mismatch được report.
43. Dtype mismatch được report.
44. Layout mismatch được distinguish.
45. Device mismatch được distinguish.
46. NaN/Inf propagation có thể trace.
47. First-divergence analysis được hỗ trợ.
48. Attention capture được hỗ trợ khi backend expose.
49. Attention head identity được preserve.
50. Attention layer identity được preserve.
51. Token mapping được preserve.
52. Multimodal mapping được preserve.
53. Sparse attention được preserve.
54. Attention aggregation method explicit.
55. Visualization là tooling.
56. Attention không tự động chứng minh causality.
57. Attribution target explicit.
58. Input feature identity được preserve.
59. Text attribution map được preserve.
60. Image attribution map được preserve.
61. Audio attribution map được preserve.
62. Video attribution map được preserve.
63. Multimodal attribution được hỗ trợ.
64. Multiple attribution methods được hỗ trợ.
65. Method assumptions được record.
66. Approximate attribution được mark.
67. Gradient capture được hỗ trợ.
68. Gradient statistics được hỗ trợ.
69. Vanishing-gradient diagnostics được hỗ trợ.
70. Exploding-gradient diagnostics được hỗ trợ.
71. NaN/Inf gradient detection được hỗ trợ.
72. Per-layer gradient inspection được hỗ trợ.
73. Gradient clipping events được record.
74. Optimizer state inspection được hỗ trợ.
75. Checkpoint comparison được hỗ trợ.
76. Debug instrumentation không mặc định production.
77. Model graph inspection được hỗ trợ.
78. Layer tree được expose.
79. Parameter inventory được expose.
80. Parameter statistics được expose.
81. Parameter sharing được identify.
82. Frozen/trainable state được expose.
83. Adapter parameters được identify.
84. Quantized parameters được identify.
85. Sparse parameters được identify.
86. Model semantic diff được hỗ trợ.
87. Counterfactual execution được hỗ trợ.
88. Perturbation được record.
89. Original/counterfactual executions linked.
90. Output delta được measure.
91. Output delta không mặc định là causal proof.
92. Counterfactual validity được biểu diễn.
93. Invalid counterfactual được mark.
94. Human-created counterfactual có provenance.
95. Automated generator có version/config.
96. Model debugger có logical breakpoints.
97. Tensor breakpoints được hỗ trợ.
98. Value predicates được hỗ trợ.
99. Graph step execution được hỗ trợ.
100. Tensor inspection được hỗ trợ.
101. Checkpoint comparison được hỗ trợ.
102. Backend comparison được hỗ trợ.
103. Deterministic replay được hỗ trợ.
104. Failure artifacts được tạo.
105. Model/source provenance được preserve khi available.
106. AI output có decision provenance.
107. Generation provenance được preserve.
108. Retrieval provenance được preserve.
109. Tool provenance được preserve.
110. Agent provenance được preserve.
111. Policy provenance được preserve.
112. Human approval provenance được preserve.
113. Final external action provenance được preserve.
114. Provenance graph được queryable.
115. Missing provenance không được suy đoán.
116. Explanation request có explicit target.
117. Explanation method explicit.
118. Explanation scope explicit.
119. Explanation result chứa evidence.
120. Explanation result chứa limitations.
121. Evidence có thể link tới source.
122. Confidence không phải universal correctness probability.
123. Uncertainty được preserve.
124. Explanation cache có identity.
125. Cache invalidation explicit.
126. Explanation access control được enforce.
127. Không có universal interpretability score.
128. Method dependence được document.
129. Attribution stability có thể evaluate.
130. Faithfulness có thể test.
131. Completeness semantics method-specific.
132. Sensitivity analysis được hỗ trợ.
133. Explanation sanity checks được hỗ trợ.
134. Distribution shift được record.
135. Model changes invalidate relevant evidence.
136. Policy changes invalidate relevant decision evidence.
137. AI query API được hỗ trợ.
138. Evidence-first tooling được hỗ trợ.
139. Large traces có filter/stream/query API.
140. **Axiom AI Observability & Interpretability phải cho phép quan sát và debug model từ input → tensor/operator → attention/activation/gradient → output → policy/tool/action, đồng thời phân biệt tuyệt đối execution evidence với attribution, heuristic và causal claim; mọi explanation phải mang method, provenance, uncertainty và limitations thay vì được coi là sự thật tuyệt đối.**

**BOOTSTRAP-523 hoàn tất / LOCKED.**

---

# BOOTSTRAP-524 — AI CONTEXT ENGINE, CONTEXT WINDOW MANAGEMENT, MEMORY HIERARCHY, PROMPT COMPILATION, CONTEXT CACHING & LONG-CONTEXT EXECUTION

**Trạng thái: COMPLETED / LOCKED**

524 xây dựng tầng **context engineering** cho 509/511/512/515. Đây là phần biến một lượng lớn information thành context mà model thực sự có thể consume.

Điểm thiết kế quan trọng:

> **Context không phải Memory. Context là một execution artifact được materialize có giới hạn kích thước, provenance và priority.**

```text id="524arch"
Sources / Memory / Retrieval / User Input
                  │
                  ↓
             Context Items
                  │
          Normalize / Validate
                  │
          Rank / Filter / Budget
                  │
          Compress / Summarize
                  │
          Deduplicate / Merge
                  │
          Prompt / Message Assembly
                  │
             Context Artifact
                  │
             Tokenization 509
                  │
            Context Window
                  │
          Prefill / KV Cache
                  │
              Model 505
```

---

# CONTEXT MODEL

## 524.1 — Context

Context là tập information được cung cấp cho một model execution.

## 524.2 — Memory

Memory là persistent/long-lived information store.

## 524.3 — Context item

```text id="ctxitem"
ContextItem {
    id
    source
    content
    type
    priority
    trust
    timestamp
    token_cost
    provenance
}
```

## 524.4 — Context source

Nguồn có thể là:

```text
System
Developer
User
Memory
Retrieval
Tool
Environment
Generated
```

## 524.5 — Authority

Context source có authority metadata.

## 524.6 — Trust

Trust metadata khác authority.

## 524.7 — Provenance

Mọi derived context có source reference.

## 524.8 — Context snapshot

Một model call sử dụng immutable context snapshot.

## 524.9 — Context identity

Snapshot có deterministic identity khi possible.

## 524.10 — Context budget

Budget tính theo model tokenizer/context semantics, không chỉ character count.

---

# CONTEXT BUDGET

## 524.11 — Token budget

Input context có token budget.

## 524.12 — Output reservation

Output budget phải được reserve.

## 524.13 — System reservation

System/developer instructions có reserved budget nếu policy yêu cầu.

## 524.14 — Tool reservation

Tool schemas/results có budget.

## 524.15 — Memory reservation

Memory retrieval có budget.

## 524.16 — Retrieval reservation

Retrieved evidence có budget.

## 524.17 — Dynamic budget

Budget có thể adapt theo request.

## 524.18 — Hard limit

Model context limit không được vượt.

## 524.19 — No silent truncation

Context overflow phải có explicit policy.

## 524.20 — Overflow policies

```text
Reject
Trim
Summarize
Compress
Prioritize
Chunk
Retrieve-on-demand
```

---

# PRIORITY

## 524.21 — Priority

Context items có priority.

## 524.22 — Priority classes

Ví dụ:

```text
Critical
High
Normal
Low
Ephemeral
```

## 524.23 — Priority is policy

Priority không phải universal truth.

## 524.24 — Recency

Recency có thể là ranking signal.

## 524.25 — Relevance

Semantic relevance có thể là ranking signal.

## 524.26 — Authority

Authority có thể influence selection.

## 524.27 — Trust

Trust có thể influence selection nhưng không tự động biến content thành instruction.

## 524.28 — Diversity

Context selection có thể penalize redundant content.

## 524.29 — Coverage

Selection có thể optimize topic coverage.

## 524.30 — Deterministic selection

Equal inputs/configuration phải produce deterministic selection nếu deterministic mode.

---

# CONTEXT COMPRESSION

## 524.31 — Compression

Context compression giảm token usage.

## 524.32 — Summarization

Summarization tạo derived artifact.

## 524.33 — Summary provenance

Summary reference source items.

## 524.34 — Loss metadata

Compression có thể có information-loss metadata.

## 524.35 — Extractive compression

Có thể giữ exact source spans.

## 524.36 — Abstractive compression

Generated summary phải mark generated.

## 524.37 — Structured compression

Tables/records có thể compress theo schema.

## 524.38 — Semantic compression

Embedding/retrieval representation có thể giữ ngoài textual context.

## 524.39 — Multi-stage compression

Context có thể compress nhiều lần.

## 524.40 — Compression invalidation

Source update invalidates derived compression artifact.

---

# PROMPT COMPILATION

## 524.41 — Prompt

Prompt là assembled model input, không phải source-language construct.

## 524.42 — Prompt template

Template có identity/version.

## 524.43 — Prompt variables

Variables typed khi possible.

## 524.44 — Prompt compilation

Template + context → concrete prompt.

## 524.45 — Prompt provenance

Generated prompt reference template/context.

## 524.46 — Injection boundary

External content không được tự động trở thành trusted instruction.

## 524.47 — Delimitation

Context source boundaries có thể được preserve.

## 524.48 — Message roles

Roles từ 509/chat model semantics được preserve.

## 524.49 — Structured prompt

Prompt có thể được model-specific structured representation.

## 524.50 — Prompt validation

Required fields/roles/schema được validate trước execution.

---

# CONTEXT CACHING

## 524.51 — Prefix cache

Stable prefix có thể cache.

## 524.52 — KV cache

Integrate 509/505.

## 524.53 — Cache identity

Cache key include:

```text
model
tokenizer
context
generation-relevant config
```

## 524.54 — Prefix validity

Only exact compatible prefix can reuse KV state.

## 524.55 — Cross-request reuse

Cross-request cache phải respect access/privacy boundaries.

## 524.56 — Tenant isolation

Cache entries không leak giữa tenants.

## 524.57 — Cache eviction

LRU/LFU/TTL/size-aware policies.

## 524.58 — Memory budget

KV/context cache có explicit budget.

## 524.59 — Paged cache

Paged KV cache được hỗ trợ.

## 524.60 — Cache invalidation

Model/tokenizer/context changes invalidate incompatible cache.

---

# LONG CONTEXT

## 524.61 — Sliding window

Sliding-window context được hỗ trợ.

## 524.62 — Chunked context

Large source được chunk.

## 524.63 — Hierarchical context

Document hierarchy được preserve.

## 524.64 — Retrieval-on-demand

Model/agent có thể retrieve additional context.

## 524.65 — Recency window

Recent conversation window được hỗ trợ.

## 524.66 — Summary memory

Old context có thể chuyển thành summary artifact.

## 524.67 — Anchor facts

Important facts có thể pin.

## 524.68 — Context eviction

Evicted content có explicit state.

## 524.69 — Rehydration

Evicted content có thể retrieve lại.

## 524.70 — Long-context provenance

Context assembled từ nhiều stages phải preserve complete lineage.

---

# MULTI-TURN CONVERSATION

## 524.71 — Turn

Conversation turn có identity.

## 524.72 — Message

Message có role/content/provenance.

## 524.73 — Conversation state

Conversation state tách khỏi prompt snapshot.

## 524.74 — Message deletion

Deleted messages không được silently reappear từ cache.

## 524.75 — Edit

Edited message tạo new version.

## 524.76 — Branch

Conversation branches được hỗ trợ.

## 524.77 — Fork

Fork tạo independent conversation state.

## 524.78 — Merge

Merge conversations phải có conflict semantics.

## 524.79 — Compaction

Conversation compaction tạo derived snapshot.

## 524.80 — Replay

Conversation replay dùng exact snapshot/config khi possible.

---

# CONTEXT SECURITY

## 524.81 — Untrusted context

Retrieved/tool/external content là untrusted data mặc định.

## 524.82 — Instruction injection

Embedded instructions không gain authority.

## 524.83 — Secret filtering

Secrets không được đưa vào context nếu policy cấm.

## 524.84 — Access filtering

Retrieval respects source ACL.

## 524.85 — Cross-user isolation

Context không cross user/session ngoài explicit sharing.

## 524.86 — Cross-agent isolation

Agent memory/context isolation explicit.

## 524.87 — Context exfiltration

Tool/action policies có thể detect context exfiltration.

## 524.88 — Sensitive markers

Context items có thể carry sensitivity labels.

## 524.89 — Redaction

Redaction creates provenance-preserving derived item.

## 524.90 — Audit

Sensitive context access có thể audit.

---

# CONTEXT EVALUATION

## 524.91 — Context quality

Context quality là multidimensional.

## 524.92 — Relevance

Retrieved relevance có thể measure.

## 524.93 — Coverage

Topic/fact coverage có thể measure.

## 524.94 — Redundancy

Duplicate content có thể measure.

## 524.95 — Freshness

Freshness có thể measure.

## 524.96 — Authority

Source authority metadata được preserve.

## 524.97 — Context utilization

Có thể measure model behavior under context variations.

## 524.98 — Ablation

Remove selected context items để evaluate effect.

## 524.99 — Counterfactual context

Alternative context snapshots có thể compare.

## 524.100 — No universal context score

Không có một aggregate context-quality score bắt buộc.

---

# 524.101 — HARD INVARIANTS

1. Context khác memory.
2. Context là execution artifact.
3. Context item có identity.
4. Context source được preserve.
5. Context type được preserve.
6. Context priority được preserve.
7. Context trust được preserve.
8. Context authority được preserve.
9. Context provenance được preserve.
10. Context snapshot được hỗ trợ.
11. Context identity được hỗ trợ.
12. Context budget được tính theo model/tokenizer semantics.
13. Output reservation được hỗ trợ.
14. System reservation có thể được hỗ trợ.
15. Tool reservation được hỗ trợ.
16. Memory reservation được hỗ trợ.
17. Retrieval reservation được hỗ trợ.
18. Dynamic budget được hỗ trợ.
19. Context limit không được vượt.
20. Overflow policy phải explicit.
21. Silent truncation bị cấm.
22. Reject overflow được hỗ trợ.
23. Trim được hỗ trợ.
24. Summarization được hỗ trợ.
25. Compression được hỗ trợ.
26. Prioritization được hỗ trợ.
27. Chunking được hỗ trợ.
28. On-demand retrieval được hỗ trợ.
29. Context item priority được hỗ trợ.
30. Priority là policy.
31. Recency có thể influence selection.
32. Relevance có thể influence selection.
33. Authority có thể influence selection.
34. Trust có thể influence selection.
35. Trust không tự động grant instruction authority.
36. Diversity được hỗ trợ.
37. Coverage được hỗ trợ.
38. Deterministic selection được hỗ trợ.
39. Context compression tạo derived artifact.
40. Summary có provenance.
41. Information loss có thể được metadata hóa.
42. Extractive compression preserve source spans.
43. Abstractive summary được mark generated.
44. Structured compression preserve schema semantics.
45. Semantic compression được hỗ trợ.
46. Multi-stage compression được hỗ trợ.
47. Source changes invalidate derived compression.
48. Prompt không phải language syntax.
49. Prompt template có identity.
50. Prompt template có version.
51. Prompt variables được typed khi possible.
52. Prompt compilation được hỗ trợ.
53. Prompt provenance được preserve.
54. External content không tự động trở thành instruction.
55. Context boundaries có thể được preserve.
56. Message roles được preserve.
57. Structured prompts được hỗ trợ.
58. Prompt schema được validate.
59. Prefix caching được hỗ trợ.
60. KV caching integrate 509/505.
61. Cache key có model identity.
62. Cache key có tokenizer identity.
63. Cache key có context identity.
64. Generation-relevant config được include khi cần.
65. Chỉ prefix compatible mới được reuse.
66. Cache privacy boundary được enforce.
67. Tenant isolation được enforce.
68. Cache eviction policy explicit.
69. Cache memory budget được hỗ trợ.
70. Paged KV cache được hỗ trợ.
71. Cache invalidation được định nghĩa.
72. Sliding-window context được hỗ trợ.
73. Chunked context được hỗ trợ.
74. Hierarchical context được preserve.
75. Retrieval-on-demand được hỗ trợ.
76. Recent-context window được hỗ trợ.
77. Summary memory được hỗ trợ.
78. Pinned facts được hỗ trợ.
79. Eviction state được explicit.
80. Rehydration được hỗ trợ.
81. Long-context lineage được preserve.
82. Conversation turn có identity.
83. Message có role/content/provenance.
84. Conversation state khác prompt snapshot.
85. Deleted message không được tự động reappear.
86. Edited message có version.
87. Conversation branch được hỗ trợ.
88. Conversation fork được hỗ trợ.
89. Merge có conflict semantics.
90. Conversation compaction có identity.
91. Replay được hỗ trợ.
92. External context mặc định untrusted.
93. Embedded instructions không gain authority.
94. Secret filtering được hỗ trợ.
95. ACL filtering được enforce.
96. Cross-user isolation được enforce.
97. Cross-agent isolation explicit.
98. Context exfiltration policy được hỗ trợ.
99. Sensitivity labels được hỗ trợ.
100. Redaction preserve provenance.
101. Sensitive context access có thể audit.
102. Context relevance có thể evaluate.
103. Context coverage có thể evaluate.
104. Context redundancy có thể evaluate.
105. Context freshness có thể evaluate.
106. Source authority được preserve.
107. Context utilization có thể measure.
108. Context ablation được hỗ trợ.
109. Counterfactual contexts được hỗ trợ.
110. Không có universal context-quality score.
111. Context changes có thể invalidate model cache.
112. Model changes invalidate incompatible context/KV artifacts.
113. Tokenizer changes invalidate token-dependent artifacts.
114. Context artifact có deterministic fingerprint khi possible.
115. Context provenance queryable.
116. AI tooling có thể explain inclusion/exclusion.
117. AI tooling có thể query token cost.
118. AI tooling có thể query compression history.
119. AI tooling có thể query retrieval lineage.
120. AI tooling có thể query context cache status.
121. Context construction có thể replay.
122. Context policy được versioned.
123. Context security policy integrate 490/522.
124. Context retrieval integrate 512.
125. Agent context integrate 511.
126. Long-term memory integrate 515.
127. Model context constraints integrate 509.
128. Context execution integrates 505.
129. Context selection không được silently discard critical policy/system information.
130. Context system không được biến external text thành privileged instruction.
131. Context cache không được leak protected content.
132. Context artifact deletion semantics được hỗ trợ.
133. Context lineage có thể reverse-query về source.
134. Context assembly errors là structured diagnostics.
135. Token overflow là explicit diagnostic.
136. Model-specific context limits được queryable.
137. Model-specific tokenizer identity được queryable.
138. Context budget accounting được reproducible.
139. Context construction overhead được measurable.
140. **Axiom Context Engine phải biến memory, retrieval, conversation, tools và user input thành một context artifact có budget, provenance, authority, priority, compression và security semantics rõ ràng; context overflow, cache reuse và information loss không được xảy ra một cách âm thầm, và hệ thống phải cho phép truy nguyên vì sao một item được đưa vào hoặc loại khỏi context.**

**BOOTSTRAP-524 hoàn tất / LOCKED.**

**Task kế tiếp: `BOOTSTRAP-525 — AI MEMORY ENGINE, EPISODIC/SEMANTIC/PROCEDURAL MEMORY, MEMORY CONSOLIDATION, RETENTION, FORGETTING, PERSONALIZATION & CROSS-SESSION STATE`.**