# BOOTSTRAP-521 — AI MODEL COMPRESSION, PRUNING, DISTILLATION, SPARSITY, LOW-RANK ADAPTATION, QUANTIZATION & EDGE DEPLOYMENT OPTIMIZATION

**Trạng thái: COMPLETED / LOCKED**

521 xây dựng tầng **model optimization/compression** phía trên 503–520. Mục tiêu là biến một model đã train thành artifact triển khai nhỏ hơn, nhanh hơn hoặc tiết kiệm bộ nhớ hơn, nhưng mọi thay đổi về số học, độ chính xác, layout và runtime behavior phải được biểu diễn rõ ràng.

```text id="521arch"
                  Trained Model
                       │
              ┌────────┴────────┐
              ↓                 ↓
          Analysis          Calibration
              │                 │
      ┌───────┼────────┬────────┘
      ↓       ↓        ↓
   Pruning  Quantize  Distill
      │       │        │
      └───────┼────────┘
              ↓
        Compression IR
              │
      ┌───────┼──────────┐
      ↓       ↓          ↓
   Sparse   Packed    Low-Rank
   Weights  Weights    Adapters
      │       │          │
      └───────┼──────────┘
              ↓
       Optimized Model
              │
       Graph Compiler 504
              ↓
       Native Runtime 505
              ↓
       CPU / GPU / NPU
```

---

# 521.1 — Compression ≠ Quantization

Compression là khái niệm rộng.

Quantization chỉ là một phương pháp compression/acceleration.

Các phương pháp phải được distinguish:

```text
Pruning
Quantization
Distillation
Low-Rank Approximation
Weight Sharing
Weight Packing
Entropy Compression
Structured Sparsity
Activation Compression
KV Compression
```

---

# MODEL OPTIMIZATION IDENTITY

## 521.2 — Optimization artifact

Mỗi transformation tạo một artifact mới:

```text id="3f8z8f"
InputModel
Transform
Configuration
OutputModel
```

## 521.3 — Optimization identity

```text id="f5h7ha"
OptimizationId
Version
ConfigurationHash
InputArtifactHash
```

## 521.4 — Provenance

Output phải reference model trước transformation.

## 521.5 — Transformation chain

Có thể truy ngược:

```text
Original
 → Quantized
 → Pruned
 → Packed
 → Compiled
```

## 521.6 — Semantic intent

Optimization phải khai báo intended numerical semantics.

## 521.7 — Numerical policy

Integrate 504:

```text
strict
reproducible
fast
```

## 521.8 — Target awareness

Optimization có thể phụ thuộc:

- CPU ISA;
- GPU architecture;
- NPU;
- memory hierarchy;
- accelerator capabilities.

## 521.9 — Target-specific artifact

Target-specific optimized model phải được distinguish khỏi portable model.

## 521.10 — Reoptimization

Một optimized artifact có thể được optimize tiếp khi transformation hợp lệ.

---

# PRUNING

## 521.11 — Unstructured pruning

Individual weights có thể được loại bỏ.

## 521.12 — Structured pruning

Có thể prune:

- neuron;
- channel;
- head;
- block;
- layer.

## 521.13 — Block sparsity

Block-based sparse pattern được hỗ trợ.

## 521.14 — N:M sparsity

Structured N:M sparsity được biểu diễn khi backend hỗ trợ.

## 521.15 — Sparsity metadata

Sparse tensor phải lưu pattern/indices/format.

## 521.16 — Sparse format

Có thể hỗ trợ:

```text
COO
CSR
CSC
BSR
blocked
compressed
custom
```

## 521.17 — Sparse kernel

Sparse representation chỉ có lợi nếu backend có kernel phù hợp.

## 521.18 — Dense fallback

Không có sparse kernel → explicit dense fallback.

## 521.19 — Accuracy validation

Pruning có thể yêu cầu evaluation artifact.

## 521.20 — Fine-tuning

Pruned model có thể fine-tune.

---

# QUANTIZATION

## 521.21 — Quantization identity

Quantization configuration là first-class metadata.

## 521.22 — Supported representations

Foundation hỗ trợ:

```text
int8
uint8
int16
int4-like packed
float8-like formats
```

chỉ khi backend/representation hỗ trợ.

## 521.23 — Scale

Quantized tensor có explicit scale.

## 521.24 — Zero point

Affine quantization có explicit zero point.

## 521.25 — Symmetric

Symmetric quantization có thể không cần zero point.

## 521.26 — Per-tensor

Một scale cho toàn tensor.

## 521.27 — Per-channel

Scale theo channel.

## 521.28 — Per-group

Scale theo group/block.

## 521.29 — Dynamic quantization

Scale có thể được tính runtime.

## 521.30 — Static quantization

Calibration-derived scale được lưu.

---

# QUANTIZATION CALIBRATION

## 521.31 — Calibration dataset

Calibration dataset có identity/version.

## 521.32 — Calibration statistics

Statistics phải record.

## 521.33 — Range estimation

Các chiến lược range estimation được distinguish.

## 521.34 — Outlier handling

Outlier policy explicit.

## 521.35 — Activation calibration

Activation ranges có thể calibrate.

## 521.36 — Weight calibration

Weight distribution có thể analyze.

## 521.37 — Mixed precision

Different tensors/operators có thể có precision khác nhau.

## 521.38 — Accumulation precision

Input precision ≠ accumulation precision.

## 521.39 — Output precision

Output precision explicit.

## 521.40 — Quantization graph

Quantize/dequantize operations có thể được biểu diễn trong graph IR.

---

# QUANTIZATION-AWARE TRAINING

## 521.41 — Fake quantization

Training có thể simulate quantization.

## 521.42 — QAT identity

QAT configuration được record.

## 521.43 — Calibration vs QAT

Calibration-only và QAT không được coi là cùng transformation.

## 521.44 — Gradient semantics

Fake-quant gradient approximation explicit.

## 521.45 — Export

QAT model export phải preserve quantization metadata.

## 521.46 — Operator support

Operator quantization support được kiểm tra.

## 521.47 — Unsupported operation

Không silently quantize unsupported operations.

## 521.48 — Fallback

Unsupported operator có thể fallback precision cao hơn.

## 521.49 — Mixed graph

Graph có thể chứa mixed precision.

## 521.50 — Validation

Quantized model có thể chạy cùng evaluation suite để so sánh.

---

# WEIGHT PACKING

## 521.51 — Packed weights

Weights có thể được reorder/pack cho kernel.

## 521.52 — Layout identity

Packed representation có explicit layout identity.

## 521.53 — Target dependency

CPU/GPU-specific packing phải identify target.

## 521.54 — Prepacking

Prepacked weights có thể cache.

## 521.55 — Immutable packing

Packed weight data phải immutable sau publish.

## 521.56 — Alignment

Packing có alignment metadata.

## 521.57 — SIMD

Packing có thể target SIMD width.

## 521.58 — Cache locality

Layout optimization có thể target cache hierarchy.

## 521.59 — Decompression

Runtime decompression chỉ khi explicitly selected.

## 521.60 — Memory accounting

Packed/compressed representation phải report actual memory.

---

# KNOWLEDGE DISTILLATION

## 521.61 — Teacher

Teacher model có identity.

## 521.62 — Student

Student model có identity.

## 521.63 — Distillation dataset

Dataset identity được record.

## 521.64 — Soft targets

Teacher logits/probabilities có thể làm supervision.

## 521.65 — Temperature

Distillation temperature explicit.

## 521.66 — Loss

Distillation loss composition explicit.

## 521.67 — Feature distillation

Intermediate features có thể được distill.

## 521.68 — Attention distillation

Attention representations có thể được distill.

## 521.69 — Multi-teacher

Multiple teachers được hỗ trợ.

## 521.70 — Teacher execution

Teacher có thể execute offline hoặc jointly.

---

# LOW-RANK / ADAPTER

## 521.71 — Low-rank decomposition

Matrix có thể approximate:

```text id="lr"
W ≈ A × B
```

## 521.72 — Rank

Rank là explicit configuration.

## 521.73 — Approximation error

Error measurement có thể được recorded.

## 521.74 — Adapter

Adapter là parameter delta tách khỏi base model.

## 521.75 — Base model immutability

Adapter training không mutate shared base weights.

## 521.76 — Adapter composition

Multiple adapters có thể compose khi mathematically/semantically supported.

## 521.77 — Adapter merge

Adapter có thể merge vào base model thành artifact mới.

## 521.78 — Merge provenance

Merged artifact references base + adapters.

## 521.79 — Adapter serving

Serving 517 có thể chọn adapter per request/session.

## 521.80 — Adapter cache

Frequently used adapters có thể cache.

---

# WEIGHT SHARING

## 521.81 — Shared weights

Identical tensors có thể share storage.

## 521.82 — Deduplication

Content-identical weights có thể deduplicate.

## 521.83 — Hash identity

Weight identity có content hash.

## 521.84 — Copy-on-write

Mutation yêu cầu private storage.

## 521.85 — Alias safety

Sharing phải respect 423 ownership semantics.

## 521.86 — Compression dictionary

Compatible tensors có thể share compression metadata/dictionary.

## 521.87 — External weights

Weights có thể nằm ngoài model manifest.

## 521.88 — mmap

Immutable weights có thể mmap.

## 521.89 — Streaming weights

Large models có thể load weights incrementally.

## 521.90 — Lazy tensors

Unused weights có thể remain unloaded nếu graph semantics cho phép.

---

# EDGE DEPLOYMENT

## 521.91 — Edge profile

Edge deployment profile tối ưu:

- memory;
- startup;
- power;
- latency;
- binary size.

## 521.92 — CPU-only profile

Model có thể compile hoàn toàn CPU.

## 521.93 — Mobile profile

Mobile constraints explicit.

## 521.94 — NPU profile

NPU backend capability được query.

## 521.95 — Memory budget

Hard memory budget có thể đặt.

## 521.96 — Model footprint

Footprint report:

```text
weights
metadata
workspace
activation
KV cache
runtime
```

## 521.97 — Startup budget

Model initialization cost được measure.

## 521.98 — Power metadata

Power/energy measurement có thể được attach khi hardware hỗ trợ.

## 521.99 — Offline deployment

Compressed model có thể deploy hoàn toàn offline.

## 521.100 — Edge artifact

Edge artifact phải identify:

```text
Model
Optimization chain
Compiler
Backend
Target
Features
Numerical policy
```

---

# OPTIMIZATION VALIDATION

## 521.101 — Reference model

Original model có thể làm reference.

## 521.102 — Numerical comparison

So sánh output theo explicit tolerance/policy.

## 521.103 — Task comparison

Task metrics được evaluate riêng.

## 521.104 — No universal accuracy threshold

Không áp đặt một accuracy threshold cho mọi model/task.

## 521.105 — Layer-level comparison

Intermediate tensors có thể compare.

## 521.106 — Error attribution

Quantization/pruning errors có thể trace theo operator/layer.

## 521.107 — Calibration validation

Calibration data distribution được record.

## 521.108 — Regression detection

Known evaluation suite có thể detect regression.

## 521.109 — Benchmark

Latency/throughput/memory được benchmark theo 450/481.

## 521.110 — Optimization report

Compiler phải có thể xuất:

```text
optimization
input
output
memory_delta
latency_delta
precision_change
fallbacks
```

---

# COMPILER INTEGRATION

## 521.111 — Graph compiler

Integrate 504.

## 521.112 — Kernel selection

Quantized/sparse kernels được chọn theo target capabilities.

## 521.113 — Fusion

Compatible quantized operators có thể fuse.

## 521.114 — Dequant fusion

Dequantization có thể fuse vào kernel.

## 521.115 — Sparse fusion

Sparse patterns có thể được fused khi backend support.

## 521.116 — Memory planning

Compressed representation phải integrate 504 memory planner.

## 521.117 — Device placement

Compression có thể influence device placement.

## 521.118 — Runtime dispatch

Multiple optimized variants có thể dispatch theo device features.

## 521.119 — Portable artifact

Portable representation không được giả vờ target-specific optimized.

## 521.120 — Optimization provenance

Compiler phải preserve transformation provenance.

---

# SECURITY

## 521.121 — Model input untrusted

Model artifacts vẫn là untrusted data.

## 521.122 — Malformed sparse data

Sparse indices/metadata phải bounds-check.

## 521.123 — Quantization metadata

Scale/zero-point validation.

## 521.124 — Integer overflow

Packed representation phải guard arithmetic overflow.

## 521.125 — Decompression limits

Compressed artifacts có resource limits.

## 521.126 — Memory exhaustion

Model expansion không được vượt resource policy silently.

## 521.127 — Malicious model

Optimization pipeline không được execute arbitrary model-defined code.

## 521.128 — Custom kernel

Custom native kernel qua trust boundary 490.

## 521.129 — Provenance

Optimization chain không được mất provenance.

## 521.130 — Artifact verification

Optimized artifacts có thể verify hash/signature.

---

# AI INTROSPECTION

## 521.131 — Why optimized?

Query:

```text
why_pruned()
why_quantized()
why_not_quantized()
why_sparse()
why_dense()
why_fallback()
why_precision()
why_layout()
```

## 521.132 — Precision report

Per operator/tensor precision.

## 521.133 — Sparsity report

Pattern/density/backend support.

## 521.134 — Compression report

Original vs optimized storage.

## 521.135 — Memory report

Weights/activation/workspace.

## 521.136 — Performance report

Measured latency/throughput.

## 521.137 — Accuracy report

Evaluation evidence.

## 521.138 — Unsupported optimization

Explicitly report missed transformations.

## 521.139 — Optimization confidence

Compiler distinguishes:

```text
Applied
NotApplicable
Unsupported
RejectedForCorrectness
RejectedForPolicy
Unknown
```

## 521.140 — Machine-readable metadata

All optimization decisions queryable by AI tooling 446/511.

---

# 521.141 — HARD INVARIANTS

1. Compression khác quantization.
2. Optimization có artifact identity.
3. Transformation có identity.
4. Transformation configuration có hash.
5. Input artifact được reference.
6. Output artifact được reference.
7. Provenance chain được preserve.
8. Numerical intent được khai báo.
9. Numerical policy integrate 504.
10. Optimization có thể target-specific.
11. Target-specific artifact được distinguish.
12. Reoptimization có explicit semantics.
13. Unstructured pruning được hỗ trợ.
14. Structured pruning được hỗ trợ.
15. Block sparsity được hỗ trợ.
16. N:M sparsity được biểu diễn khi supported.
17. Sparse metadata được lưu.
18. Sparse formats có identity.
19. Sparse kernel capability được kiểm tra.
20. Dense fallback được distinguish.
21. Pruning evaluation có thể thực hiện.
22. Fine-tuning pruned models được hỗ trợ.
23. Quantization metadata là first-class.
24. Supported quantized representations được xác định.
25. Scale được lưu.
26. Zero point được lưu khi affine.
27. Symmetric quantization được hỗ trợ.
28. Per-tensor quantization được hỗ trợ.
29. Per-channel quantization được hỗ trợ.
30. Per-group quantization được hỗ trợ.
31. Dynamic quantization được hỗ trợ.
32. Static quantization được hỗ trợ.
33. Calibration dataset có identity.
34. Calibration statistics được record.
35. Range estimation explicit.
36. Outlier policy explicit.
37. Activation calibration được hỗ trợ.
38. Weight calibration được hỗ trợ.
39. Mixed precision được hỗ trợ.
40. Accumulation precision explicit.
41. Output precision explicit.
42. Quantization graph representation được hỗ trợ.
43. QAT được hỗ trợ.
44. Fake quantization semantics explicit.
45. QAT configuration được record.
46. Calibration và QAT được distinguish.
47. Fake-quant gradient semantics explicit.
48. QAT export preserve metadata.
49. Operator quantization support được kiểm tra.
50. Unsupported quantization không silently applied.
51. Precision fallback explicit.
52. Mixed-precision graphs được hỗ trợ.
53. Quantized model evaluation được hỗ trợ.
54. Weight packing được hỗ trợ.
55. Packed layout có identity.
56. Packing target được identify.
57. Prepacked weights có thể cache.
58. Packed weights immutable sau publish.
59. Alignment metadata được lưu.
60. SIMD-aware packing được hỗ trợ.
61. Cache-locality optimization được hỗ trợ.
62. Runtime decompression không implicit.
63. Packed memory được account.
64. Teacher model có identity.
65. Student model có identity.
66. Distillation dataset có identity.
67. Soft-target distillation được hỗ trợ.
68. Temperature explicit.
69. Distillation loss explicit.
70. Feature distillation được hỗ trợ.
71. Attention distillation được hỗ trợ.
72. Multi-teacher được hỗ trợ.
73. Teacher execution mode explicit.
74. Low-rank decomposition được hỗ trợ.
75. Rank explicit.
76. Approximation error có thể measure.
77. Adapter parameters tách khỏi base model.
78. Shared base weights immutable.
79. Adapter composition explicit.
80. Adapter merge tạo artifact mới.
81. Merge provenance được preserve.
82. Serving có thể select adapter.
83. Adapter cache có identity.
84. Identical weights có thể deduplicate.
85. Weight content hash được hỗ trợ.
86. Copy-on-write respect ownership.
87. Weight aliasing respect 423.
88. External weights được hỗ trợ.
89. mmap weights được hỗ trợ.
90. Streaming weight loading được hỗ trợ.
91. Lazy weight loading được hỗ trợ.
92. Edge profile có explicit constraints.
93. CPU-only deployment được hỗ trợ.
94. Mobile deployment được hỗ trợ.
95. NPU capability được query.
96. Memory budget được hỗ trợ.
97. Model footprint được report.
98. Startup cost được measurable.
99. Optimization artifact chứa đầy đủ model/optimization/compiler/backend/target identity.
100. Reference model comparison được hỗ trợ.
101. Numerical comparison policy explicit.
102. Task-level evaluation được distinguish.
103. Không có universal accuracy threshold.
104. Intermediate tensor comparison được hỗ trợ.
105. Error attribution theo operator/layer được hỗ trợ.
106. Calibration distribution được record.
107. Regression evaluation được hỗ trợ.
108. Performance benchmark integrate 450/481.
109. Optimization report được xuất.
110. Graph compiler integration được hỗ trợ.
111. Kernel capability được query.
112. Quantized fusion được hỗ trợ.
113. Dequant fusion được hỗ trợ.
114. Sparse fusion được hỗ trợ.
115. Compressed representation integrate memory planner.
116. Device placement có thể depend optimization.
117. Runtime feature dispatch được hỗ trợ.
118. Portable artifact được distinguish target-specific artifact.
119. Optimization provenance không được mất.
120. Model artifacts luôn treated as untrusted input.
121. Sparse metadata phải bounds-check.
122. Quantization metadata phải validate.
123. Packed arithmetic phải guard overflow.
124. Decompression có resource limits.
125. Model expansion phải obey memory policy.
126. Optimization không execute arbitrary model code.
127. Custom native kernels qua trust boundary.
128. Optimized artifact có thể verify.
129. AI có thể query optimization decisions.
130. Precision report được hỗ trợ.
131. Sparsity report được hỗ trợ.
132. Compression report được hỗ trợ.
133. Memory report được hỗ trợ.
134. Performance report được hỗ trợ.
135. Accuracy/evaluation report được hỗ trợ.
136. Missed optimization được explain.
137. Optimization result states explicit.
138. Optimization cache identity deterministic.
139. Optimization artifacts reproducible khi inputs/toolchain/backend deterministic.
140. **Axiom Model Optimization phải cho phép biến model lớn thành representation phù hợp CPU/GPU/NPU/edge thông qua pruning, sparsity, quantization, distillation, low-rank/adapters và packing, đồng thời giữ đầy đủ provenance, numerical semantics, memory/performance evidence và target compatibility; optimization không được biến thành một bước “black box” làm mất khả năng giải thích hoặc tái tạo artifact.**

**BOOTSTRAP-521 hoàn tất / LOCKED.**

---

# BOOTSTRAP-522 — AI SAFETY, MODEL BEHAVIOR EVALUATION, RED-TEAMING, GUARDRAILS, POLICY ENGINE, CONTENT FILTERING & TRUSTED AI EXECUTION

**Trạng thái: COMPLETED / LOCKED**

522 xây dựng lớp kiểm soát **behavioral safety** trên 516 evaluation, 511 agent, 517 serving và 490 security.

Điểm quan trọng:

> **Model safety ≠ language safety ≠ application security.**

Axiom chỉ cung cấp primitives và contracts; policy cụ thể thuộc application/deployment.

```text id="522arch"
                    AI Input
                       │
                 Input Validation
                       │
                 Policy Evaluation
                       │
             ┌─────────┴─────────┐
             ↓                   ↓
          Allowed              Blocked
             │                   │
             ↓                   ↓
       Model / Agent         Policy Result
             │
        Model Output
             │
       Output Validation
             │
       ┌─────┴──────┐
       ↓            ↓
    Allowed       Review
       │            │
       ↓            ↓
    Response     Human / Policy
```

---

# 522.1 — Safety ≠ Security

Security bảo vệ system/resources.

Safety kiểm soát behavior/harm policy.

Hai hệ thống có thể overlap nhưng không được merge semantic.

## 522.2 — Policy

Policy là explicit rules.

## 522.3 — Policy identity

```text id="pol"
PolicyId
Version
ConfigurationHash
```

## 522.4 — Policy evaluation

Kết quả:

```text
Allow
Deny
Review
Unknown
```

## 522.5 — Unknown

Unknown không được tự động coi là Allow hoặc Deny trừ khi policy quy định.

---

# GUARDRAIL PIPELINE

## 522.6 — Input guardrail

Validate input trước model.

## 522.7 — Output guardrail

Validate output sau model.

## 522.8 — Tool guardrail

Tool calls từ agent phải qua policy.

## 522.9 — Retrieval guardrail

Retrieved evidence phải respect access policy.

## 522.10 — Action guardrail

External side effects require capability/policy check.

---

# CONTENT CLASSIFICATION

## 522.11 — Classifier

Safety classifier là model/component riêng.

## 522.12 — Classification result

```text id="class"
Category
Confidence
Evidence
ModelVersion
PolicyVersion
```

## 522.13 — Confidence

Confidence không phải correctness proof.

## 522.14 — Multi-label

Một input có thể có nhiều categories.

## 522.15 — Hierarchical labels

Categories có thể hierarchical.

## 522.16 — Custom taxonomy

Application có thể định nghĩa taxonomy.

## 522.17 — Versioning

Taxonomy versioned.

## 522.18 — Threshold

Threshold là policy.

## 522.19 — Calibration

Classifier calibration có thể evaluate.

## 522.20 — False positives

Policy system phải track false-positive behavior.

---

# RED-TEAMING

## 522.21 — Test case

Safety test case là explicit artifact.

## 522.22 — Attack category

Test taxonomy có thể include:

- prompt injection;
- jailbreak attempts;
- unsafe tool invocation;
- data exfiltration;
- policy bypass;
- malformed input;
- resource exhaustion.

## 522.23 — Adversarial input

Adversarial test data được mark rõ.

## 522.24 — Test isolation

Red-team tests không được silently execute dangerous side effects.

## 522.25 — Dry run

Tool/action testing mặc định có thể dùng dry-run.

## 522.26 — Sandbox

External side effects có thể sandbox.

## 522.27 — Expected behavior

Expected result là policy artifact.

## 522.28 — Regression

Known failures trở thành regression tests.

## 522.29 — Reproducibility

Test identity/model/policy/config được record.

## 522.30 — Mutation

Prompt/test mutation được hỗ trợ để tìm behavior boundaries.

---

# PROMPT INJECTION

## 522.31 — Instruction/data distinction

System policy, user request, retrieved document, tool result và model output phải giữ origin.

## 522.32 — Retrieved text

Retrieved text không tự động có authority.

## 522.33 — Tool result

Tool result không được trở thành system instruction.

## 522.34 — External document

Document instructions treated as untrusted content.

## 522.35 — Authority metadata

Policy engine có thể attach authority level.

## 522.36 — Instruction provenance

Instructions có source/provenance.

## 522.37 — Conflict

Conflicting instructions phải được detect khi possible.

## 522.38 — Tool request

Model-generated tool invocation là request, không phải authorization.

## 522.39 — Capability check

Actual tool execution requires capability.

## 522.40 — User confirmation

Sensitive actions có thể yêu cầu approval token.

---

# AGENT SAFETY

## 522.41 — Agent policy

511 AgentState có policy reference.

## 522.42 — Action classes

```text id="actionclass"
Pure
Read
Write
External
Irreversible
```

## 522.43 — Approval

Policy có thể require approval cho action class.

## 522.44 — Budget

Token/time/cost/action budgets được enforce.

## 522.45 — Loop protection

Repeated actions có loop detection.

## 522.46 — Tool scope

Agent tool capabilities có scope.

## 522.47 — Delegation

Delegated capability không được gain authority.

## 522.48 — Revocation

Capabilities có thể revoke.

## 522.49 — Audit

Sensitive actions có audit event.

## 522.50 — Dry-run

Agent workflow có dry-run mode.

---

# OUTPUT SAFETY

## 522.51 — Output scanner

Output có thể được classify trước delivery.

## 522.52 — Streaming output

Streaming response có thể được scan incrementally.

## 522.53 — Buffering policy

Application chọn:

```text
stream immediately
buffer then validate
hybrid
```

## 522.54 — Block

Blocked output không được silently delivered.

## 522.55 — Transform

Redaction/transformation phải explicit.

## 522.56 — Explanation

Policy result có machine-readable reason.

## 522.57 — Human review

Review queue được hỗ trợ.

## 522.58 — Override

Policy override phải require explicit authority.

## 522.59 — Override provenance

Override được audit.

## 522.60 — Fail closed/open

Behavior on classifier/policy failure phải explicit.

---

# PRIVACY

## 522.61 — Sensitive data

PII/secrets/sensitive fields có metadata.

## 522.62 — Redaction

Logs/traces có thể redact.

## 522.63 — Retention

Safety artifacts có retention policy.

## 522.64 — Access control

Safety reports respect access control.

## 522.65 — Tenant isolation

Multi-tenant evaluation isolated.

## 522.66 — No hidden telemetry

Safety system không auto-upload.

## 522.67 — Data minimization

Classifier không cần giữ raw input nếu policy không yêu cầu.

## 522.68 — Provenance

Derived safety result reference source input identity.

## 522.69 — Deletion

Deletion requests propagate tới derived artifacts khi applicable.

## 522.70 — Encryption

Storage security integrate 490/455.

---

# MODEL BEHAVIOR

## 522.71 — Behavior specification

Behavior expectations có thể khai báo.

## 522.72 — Contract

Model behavior contracts integrate 479.

## 522.73 — Property

Behavioral properties có thể test.

## 522.74 — Invariant

Safety invariants được test across inputs.

## 522.75 — Metamorphic testing

Equivalent input transformations có thể test consistency.

## 522.76 — Differential testing

Multiple models có thể compare.

## 522.77 — Regression suite

Behavior regression suite được version.

## 522.78 — Distribution

Evaluation dataset distribution được record.

## 522.79 — Out-of-distribution

OOD behavior được distinguish.

## 522.80 — Unknown behavior

Không được coi test pass là proof về mọi input.

---

# POLICY ENGINE

## 522.81 — Rule

Rule có:

```text id="rule"
RuleId
Condition
Action
Priority
Scope
Version
```

## 522.82 — Rule evaluation

Rules được evaluate deterministic khi inputs deterministic.

## 522.83 — Priority

Priority semantics explicit.

## 522.84 — Conflict

Conflicting rules phải resolve theo declared policy.

## 522.85 — Scope

Policy scope có thể:

- application;
- model;
- agent;
- tool;
- user/session;
- tenant;
- deployment.

## 522.86 — Policy inheritance

Inheritance explicit.

## 522.87 — Policy attenuation

Child policy chỉ được restrict authority khi semantics yêu cầu.

## 522.88 — Policy update

Policy update có version.

## 522.89 — Runtime policy

470 integration.

## 522.90 — Build policy

Security/safety build policies có thể enforce compile/deploy constraints.

---

# TRUSTED EXECUTION

## 522.91 — Trusted classifier

Classifier implementation trust level explicit.

## 522.92 — Untrusted model

Model itself cannot alter policy.

## 522.93 — Untrusted prompt

Prompt cannot alter policy authority.

## 522.94 — Untrusted retrieval

Retrieved content cannot grant capabilities.

## 522.95 — Untrusted tool

Tool must have declared capabilities.

## 522.96 — Capability boundary

490 remains authority source.

## 522.97 — Process isolation

Untrusted components can execute out-of-process.

## 522.98 — WASM isolation

WASM sandbox can be used.

## 522.99 — Resource limits

Safety evaluation has CPU/memory/time limits.

## 522.100 — No magical safety

Passing a guardrail does not constitute proof that output is universally safe.

---

# 522.101 — HARD INVARIANTS

1. Safety khác security.
2. Policy là explicit artifact.
3. Policy có identity.
4. Policy có version.
5. Policy configuration có hash.
6. Policy evaluation có result.
7. Allow/deny/review/unknown được distinguish.
8. Unknown không tự động map thành allow/deny ngoài policy.
9. Input guardrail được hỗ trợ.
10. Output guardrail được hỗ trợ.
11. Tool guardrail được hỗ trợ.
12. Retrieval guardrail được hỗ trợ.
13. Action guardrail được hỗ trợ.
14. Classifier có identity.
15. Classification result có category.
16. Classification result có confidence.
17. Confidence không phải proof.
18. Multi-label classification được hỗ trợ.
19. Taxonomy có version.
20. Custom taxonomy được hỗ trợ.
21. Threshold là policy.
22. Calibration được hỗ trợ.
23. False-positive behavior có thể measure.
24. Safety test case là artifact.
25. Adversarial tests được hỗ trợ.
26. Dangerous side effects không được mặc định execute trong red-team tests.
27. Dry-run được hỗ trợ.
28. Sandbox được hỗ trợ.
29. Expected behavior được lưu.
30. Safety regression được hỗ trợ.
31. Test reproducibility metadata được lưu.
32. Mutation testing được hỗ trợ.
33. Instruction và data origin được distinguish.
34. System policy có authority metadata.
35. User instruction có provenance.
36. Retrieved content không có policy authority mặc định.
37. Tool result không có policy authority mặc định.
38. Model tool request không phải authorization.
39. Tool execution phải qua capability.
40. Sensitive actions có thể require approval.
41. Agent policy integrate 511.
42. Action classes được distinguish.
43. Agent budget được enforce.
44. Agent loop detection được hỗ trợ.
45. Tool scope explicit.
46. Delegation không được escalate authority.
47. Capability revocation được hỗ trợ.
48. Sensitive action audit được hỗ trợ.
49. Agent dry-run được hỗ trợ.
50. Output scanning được hỗ trợ.
51. Streaming safety semantics explicit.
52. Buffer-before-validation được hỗ trợ.
53. Hybrid streaming được hỗ trợ.
54. Blocked output không silently delivered.
55. Redaction explicit.
56. Policy reasons machine-readable.
57. Human review được hỗ trợ.
58. Override cần explicit authority.
59. Override provenance được record.
60. Policy failure mode explicit.
61. Sensitive data metadata được hỗ trợ.
62. Safety log redaction được hỗ trợ.
63. Safety retention policy được hỗ trợ.
64. Access control được enforce.
65. Tenant isolation được enforce.
66. Không automatic safety telemetry.
67. Data minimization được hỗ trợ.
68. Safety result preserve provenance.
69. Deletion semantics được hỗ trợ.
70. Safety storage security integrate 490/455.
71. Model behavior contracts integrate 479.
72. Behavioral properties được test.
73. Safety invariants được test.
74. Metamorphic tests được hỗ trợ.
75. Differential tests được hỗ trợ.
76. Regression suites được version.
77. Evaluation distribution được record.
78. OOD behavior được distinguish.
79. Passing finite tests không phải universal proof.
80. Policy rule có identity.
81. Rule condition explicit.
82. Rule action explicit.
83. Rule priority explicit.
84. Rule scope explicit.
85. Rule versioned.
86. Rule evaluation deterministic khi inputs deterministic.
87. Rule conflict resolution explicit.
88. Policy scope được hỗ trợ.
89. Policy inheritance explicit.
90. Policy attenuation được hỗ trợ.
91. Policy update versioned.
92. Runtime policy integrate 470.
93. Build policy có thể enforce.
94. Classifier trust level explicit.
95. Model không được alter policy.
96. Prompt không được alter policy authority.
97. Retrieval không được grant capabilities.
98. Tool capabilities phải declared.
99. Untrusted components có thể process/WASM isolate.
100. Resource limits áp dụng cho safety evaluation.
101. Guardrail pass không phải universal safety proof.
102. Safety evidence phải distinguish evidence type.
103. Safety model/version/config được record.
104. Evaluation artifacts có reproducible identity.
105. Policy decisions có provenance.
106. Policy decisions có thể replay.
107. Deterministic policy simulation được hỗ trợ.
108. Safety failures có structured diagnostics.
109. AI tooling có thể query policy/evaluation evidence.
110. Không aggregate “safety score” được dùng như universal correctness measure.
111. Model replacement phải invalidate relevant behavior evidence.
112. Policy replacement phải invalidate relevant evaluation evidence.
113. Tool capability changes phải trigger relevant re-evaluation.
114. Deployment target differences phải được reflect trong evidence.
115. Safety policy không được hidden inside compiler semantics.
116. Safety runtime không mandatory cho ordinary Axiom programs.
117. Application có thể chọn guardrail depth.
118. Security and safety evidence remain separately attributable.
119. Safety test artifacts không được mutate production policy implicitly.
120. **Axiom AI Safety phải cung cấp policy, guardrail, behavioral evaluation, red-team, approval, capability và audit primitives để xây dựng hệ thống AI có kiểm soát, nhưng không tuyên bố một classifier, benchmark hay guardrail đơn lẻ là bằng chứng tuyệt đối về safety.**

**BOOTSTRAP-522 hoàn tất / LOCKED.**

---

**Chuỗi hiện tại đã tới 522.**

Task kế tiếp:

**`BOOTSTRAP-523 — AI OBSERVABILITY & INTERPRETABILITY: EXPLANATION, ATTRIBUTION, ACTIVATION TRACING, ATTENTION/FEATURE ANALYSIS, MODEL DEBUGGING & DECISION PROVENANCE`**