# BOOTSTRAP-537 — AI SAFETY EVALUATION, POLICY TESTING, RED-TEAM SIMULATION, PROMPT-INJECTION DEFENSE, TOOL-SAFETY VALIDATION & CONTINUOUS SAFETY REGRESSION

**Trạng thái: COMPLETED / LOCKED**

537 xây dựng lớp kiểm thử và xác minh an toàn cho toàn bộ AI stack 511–536. Mục tiêu là biến các rủi ro AI thành **test case, evidence, policy decision và regression artifact có thể tái lập**, thay vì coi một model hoặc agent là “an toàn” chỉ vì một vài bài test đạt.

```text
                     AI System
                         │
             ┌───────────┴───────────┐
             ↓                       ↓
        Safety Policy           Threat Model
             │                       │
             └───────────┬───────────┘
                         ↓
                  Safety Test Suite
                         │
       ┌─────────────────┼──────────────────┐
       ↓                 ↓                  ↓
 Prompt Injection    Tool Abuse       Data Leakage
       ↓                 ↓                  ↓
   Model Tests       Agent Tests       System Tests
       └─────────────────┼──────────────────┘
                         ↓
                  Evaluation Runner
                         ↓
                Evidence / Findings
                         ↓
               Regression Database
                         ↓
                 Release Gate
```

---

## 537.1 — Safety ≠ Quality ≠ Security

Phải phân biệt:

```text
Safety
Security
Reliability
Correctness
Quality
Compliance
Privacy
Availability
```

Một hệ thống có performance tốt không đồng nghĩa an toàn.

## 537.2 — Safety claim

Mọi claim an toàn phải có:

```text
Claim
Scope
Version
Evidence
Test Population
Limitations
```

## 537.3 — Không có universal safety score

Axiom không tạo một con số duy nhất đại diện cho “độ an toàn AI”.

## 537.4 — Threat model

```text
ThreatModel {
    ThreatId
    Assets
    Attacker
    Preconditions
    AttackSurface
    Impact
    Mitigations
    Tests
}
```

## 537.5 — Asset

Asset có thể là:

- secret;
- credential;
- private data;
- filesystem;
- network authority;
- tool capability;
- model;
- memory;
- deployment;
- user account.

---

# 537.6 — SAFETY TEST CASE

```text
SafetyCase {
    CaseId
    Scenario
    Input
    Environment
    PolicyVersion
    ExpectedProperties
    Oracle
}
```

## 537.7 — Test identity

Mỗi case có stable identity.

## 537.8 — Test version

Thay đổi case tạo version mới.

## 537.9 — Dataset provenance

Safety dataset phải có source/version/hash.

## 537.10 — Hidden tests

Production release có thể dùng test set không public.

---

# 537.11 — THREAT CATEGORIES

Axiom safety suite phải hỗ trợ tối thiểu:

```text
PromptInjection
IndirectInjection
ToolMisuse
PrivilegeEscalation
DataExfiltration
SecretLeakage
UnsafeAutomation
PolicyBypass
SandboxEscape
ResourceExhaustion
ModelManipulation
MemoryPoisoning
RetrievalPoisoning
SupplyChainAttack
ProtocolAttack
```

---

# 537.12 — DIRECT PROMPT INJECTION

Input cố thay đổi instruction hierarchy.

Test phải kiểm tra:

- policy boundary;
- capability boundary;
- tool boundary;
- data/instruction separation.

## 537.13 — Indirect injection

Injection nằm trong:

- document;
- webpage;
- email;
- database;
- tool output;
- retrieved memory;
- image metadata;
- multimodal content.

## 537.14 — Instruction hierarchy

```text
System Policy
    >
Agent Policy
    >
User Goal
    >
Tool Result
    >
External Data
    >
Untrusted Model Content
```

Thứ tự thực tế phải do runtime policy định nghĩa, không hard-code thành “model prompt convention”.

## 537.15 — Data ≠ instruction

External content không tự trở thành executable instruction.

---

# 537.16 — TOOL SAFETY

Mỗi tool có:

```text
Capability
Effects
InputSchema
OutputSchema
TrustLevel
Sandbox
```

## 537.17 — Dangerous tool

Các tool có:

- filesystem write;
- process execution;
- network access;
- credential access;
- external transaction;

phải được policy đánh dấu effect.

## 537.18 — Tool authorization

Tool call phải pass authorization.

## 537.19 — Argument validation

Arguments validate trước execution.

## 537.20 — Post-validation

Result được validate sau execution.

---

# 537.21 — TOOL ARGUMENT ATTACK

Test:

```text
PathTraversal
CommandInjection
MalformedURL
UnexpectedProtocol
OversizedInput
InvalidEncoding
SchemaConfusion
```

## 537.22 — Path capability

Filesystem path phải nằm trong capability scope.

## 537.23 — Network destination

Network capability phải constrain destination khi policy yêu cầu.

## 537.24 — Process execution

Shell/process tool không được coi command string là inherently safe.

## 537.25 — Environment inheritance

Environment variables truyền cho child process phải explicit.

---

# 537.26 — SECRET LEAKAGE

Test secrets qua:

- prompt;
- model output;
- tool argument;
- logs;
- traces;
- errors;
- memory;
- retrieval;
- generated artifacts.

## 537.27 — Secret classification

```text
Public
Internal
Sensitive
Secret
Restricted
```

## 537.28 — Secret sink

Mọi external sink có policy.

## 537.29 — Redaction

Redaction phải xảy ra trước sink nếu policy yêu cầu.

## 537.30 — Redaction evidence

Không được giả định rằng pattern-based redaction bắt được mọi secret.

---

# 537.31 — DATA EXFILTRATION

Test graph:

```text
Secret
 ↓
Agent
 ↓
Model
 ↓
Tool
 ↓
External Destination
```

## 537.32 — Egress policy

Outbound data subject to capability/policy.

## 537.33 — Cross-tenant leakage

Tenant boundaries được test.

## 537.34 — Retrieval leakage

RAG result phải obey ACL.

## 537.35 — Memory leakage

Memory query phải obey ownership/tenant policy.

---

# 537.36 — PRIVILEGE ESCALATION

Test:

```text
Agent A
 ↓
Tool
 ↓
Child Agent
 ↓
More Powerful Tool
```

Child không được tự nâng capability.

## 537.37 — Capability attenuation test

Parent capability subset phải được verify.

## 537.38 — Confused deputy

Test tool/service bị agent dùng authority của nó để phục vụ request không được phép.

## 537.39 — Identity propagation

Actor identity phải propagate qua tool chain.

## 537.40 — Authorization context

Authorization context không được silent drop.

---

# 537.41 — MEMORY POISONING

Memory insertion phải distinguish:

```text
UserFact
ExternalClaim
ToolObservation
SystemFact
DerivedInference
```

## 537.42 — Provenance

Memory item không có provenance đáng tin cậy không được mặc định trusted.

## 537.43 — Memory update

Update có source/reason/version.

## 537.44 — Conflict

Conflicting memory preserved as conflict hoặc resolution có evidence.

## 537.45 — Retrieval filtering

Policy có thể exclude low-trust memory.

---

# 537.46 — RAG / KNOWLEDGE POISONING

Test:

- malicious documents;
- conflicting documents;
- stale documents;
- poisoned metadata;
- malicious instructions;
- misleading retrieval ranking.

## 537.47 — Evidence ≠ instruction

Retrieved content là evidence/data, không phải policy.

## 537.48 — Citation provenance

Generated claim có thể reference evidence IDs.

## 537.49 — ACL

Retrieval filter phải được enforce trước result exposure.

## 537.50 — Deleted data

Deleted source không được tiếp tục xuất hiện từ stale index nếu deletion policy yêu cầu removal.

---

# 537.51 — MODEL OUTPUT VALIDATION

Model output có thể:

```text
Text
JSON
StructuredData
ToolCall
Code
Command
ActionPlan
```

## 537.52 — Schema validation

Structured output phải validate.

## 537.53 — Semantic validation

Schema hợp lệ chưa chắc semantic hợp lệ.

## 537.54 — Effect validation

Action phải validate capability/effect trước execution.

## 537.55 — Code output

Generated code phải được coi là untrusted source.

## 537.56 — Command output

Generated command không tự động execute.

---

# 537.57 — ACTION GATE

```text
Model Output
      ↓
Parse
      ↓
Schema Check
      ↓
Policy Check
      ↓
Capability Check
      ↓
Contract Check
      ↓
Approval?
   ┌──┴──┐
  Yes    No
   ↓      ↓
Approve  Execute
   ↓
 Execute
```

## 537.58 — No direct model→side effect

Model không được bypass action gate.

## 537.59 — Action identity

Mỗi side effect có ActionId.

## 537.60 — Revalidation

Action phải revalidate nếu context/policy/capability đã thay đổi.

---

# 537.61 — HUMAN APPROVAL SAFETY TEST

Test:

- approval spoofing;
- stale approval;
- expired approval;
- modified arguments;
- replayed approval;
- wrong session;
- wrong tenant.

## 537.62 — Approval binding

Approval bind với:

```text
ActionId
Scope
PolicyVersion
Principal
Expiry
```

## 537.63 — Approval replay

Không được reuse ngoài scope.

## 537.64 — Approval mutation

Thay đổi action → approval invalid.

---

# 537.65 — SANDBOX TESTING

Sandbox tests:

- filesystem escape;
- network escape;
- process escape;
- capability escape;
- resource exhaustion.

## 537.66 — Process isolation

Out-of-process tool isolation được kiểm tra độc lập.

## 537.67 — WASM isolation

WASM capability boundary được test.

## 537.68 — Native plugin

Native in-process plugin không được coi là sandbox.

## 537.69 — Resource limits

CPU/memory/time limits phải được enforce hoặc ghi rõ platform limitation.

## 537.70 — Escape evidence

Sandbox violation tạo structured finding.

---

# 537.71 — RESOURCE EXHAUSTION

Test:

```text
HugePrompt
HugeDocument
HugeToolResult
HugeImage
HugeAudio
HugeVideo
HugeBatch
InfiniteLoop
RetryStorm
MemoryGrowth
```

## 537.72 — Input limits

Explicit.

## 537.73 — Output limits

Explicit.

## 537.74 — Context limits

Explicit.

## 537.75 — Tool result limits

Explicit.

## 537.76 — Decompression limits

Integrate resource safety.

## 537.77 — Recursive data

Depth limit.

## 537.78 — Graph explosion

Node/edge budget.

## 537.79 — Retry budget

Integrate 536.

## 537.80 — Time budget

Integrate 474/535/536.

---

# 537.81 — MODEL ABUSE TESTING

Model evaluation có thể test:

- malformed input;
- adversarial prompt;
- conflicting instruction;
- long context;
- multilingual input;
- multimodal adversarial input;
- corrupted model state.

## 537.82 — Model-specific safety

Không hard-code một model's behavior thành language semantic.

## 537.83 — Model version

Exact model identity.

## 537.84 — Tokenizer version

Exact tokenizer identity.

## 537.85 — Safety policy

Exact policy identity.

---

# 537.86 — MULTIMODAL SAFETY

Input:

```text
Text
Image
Audio
Video
Document
```

## 537.87 — Hidden instructions

Image/audio/video có thể chứa instruction-like content.

## 537.88 — OCR

OCR output là external-derived data.

## 537.89 — ASR

Speech transcript là external-derived data.

## 537.90 — Metadata

Media metadata không automatically trusted.

## 537.91 — Cross-modal injection

Instruction ở modality này không tự override policy của modality khác.

---

# 537.92 — AGENTIC RED TEAM

Red-team scenario có:

```text
AttackerGoal
InitialState
AvailableTools
Capabilities
Environment
AttackSequence
ExpectedBoundary
```

## 537.93 — Multi-step attack

Không chỉ test single prompt.

## 537.94 — Attack chains

```text
Injection
 ↓
Memory Poison
 ↓
Tool Call
 ↓
Privilege Escalation
 ↓
Exfiltration
```

## 537.95 — State-dependent attacks

Attack có thể phụ thuộc session history.

## 537.96 — Tool-dependent attacks

Attack phải test exact tool configuration.

## 537.97 — Policy-dependent attacks

Exact policy version recorded.

## 537.98 — Environment-dependent attacks

OS/network/filesystem state recorded.

## 537.99 — Attack replay

Attack phải replayable trong sandbox.

## 537.100 — No real destructive execution

Red-team harness mặc định sử dụng mock/sandbox/test environment.

---

# 537.101 — SAFETY ORACLES

Oracle types:

```text
Exact
Schema
Property
Contract
Policy
Invariant
Reference
Human
```

## 537.102 — Policy oracle

Expected policy decision.

## 537.103 — Property oracle

Ví dụ:

```text
secret_not_exposed
unauthorized_tool_not_called
capability_not_escalated
```

## 537.104 — Human oracle

Human judgement được lưu như evaluation evidence.

## 537.105 — LLM judge

LLM judge chỉ là một oracle có uncertainty.

## 537.106 — Judge identity

Record model/prompt/config.

## 537.107 — No self-certification

Model không được tự certify safety của chính output nếu không có independent evaluation policy.

---

# 537.108 — FINDING

```text
SafetyFinding {
    FindingId
    CaseId
    Severity
    Category
    Evidence
    Policy
    Build
    Reproduction
}
```

## 537.109 — Severity

Severity taxonomy là project policy.

## 537.110 — Evidence

Finding phải có evidence.

## 537.111 — Reproduction

Có reproduction artifact nếu có thể.

## 537.112 — False positive

Được represent.

## 537.113 — False negative

Không thể chứng minh chỉ bằng absence of finding.

## 537.114 — Unknown

Khi oracle không đủ evidence → `Unknown`.

---

# 537.115 — SAFETY REGRESSION

Mỗi release so sánh:

```text
Current
vs
Baseline
```

## 537.116 — Regression identity

Case/version/policy/model/build identity.

## 537.117 — New failure

Case previously passed, now fails.

## 537.118 — Fixed failure

Case previously failed, now passes.

## 537.119 — Behavior change

Behavior changed nhưng không rõ safety regression → `Changed`.

## 537.120 — Inconclusive

Infrastructure/test failure → `Inconclusive`.

---

# 537.121 — RELEASE GATE

Possible policies:

```text
Allow
Block
RequireReview
```

## 537.122 — Gate ≠ score

Release gate dựa trên explicit policy conditions.

## 537.123 — Critical finding

Policy có thể block release.

## 537.124 — Waiver

Waiver có:

```text
Finding
Reason
Owner
Scope
Expiry
```

## 537.125 — Expired waiver

Không còn bypass gate.

---

# 537.126 — CONTINUOUS SAFETY EVALUATION

Triggers:

- model change;
- policy change;
- tool change;
- agent change;
- dependency change;
- deployment change;
- dataset change;
- runtime change.

## 537.127 — Selective evaluation

Change impact từ 486/528 có thể chọn subset.

## 537.128 — Full evaluation

Release-critical changes có thể yêu cầu full suite.

## 537.129 — Scheduled evaluation

Periodic.

## 537.130 — Incident-triggered evaluation

Security/safety incident có thể trigger targeted suite.

---

# 537.131 — INCIDENT

```text
SafetyIncident {
    IncidentId
    Detection
    Scope
    Evidence
    Timeline
    AffectedVersions
    Containment
    Resolution
}
```

## 537.132 — Incident timeline

Integrates 474/481.

## 537.133 — Containment

Có thể:

- disable tool;
- revoke capability;
- drain deployment;
- rollback model;
- block workflow;
- quarantine memory;
- isolate tenant.

## 537.134 — Evidence preservation

Containment không được tự xoá evidence.

## 537.135 — Recovery

Recovery phải preserve incident provenance.

---

# 537.136 — SAFETY POLICY VERSIONING

Policy:

```text
PolicyId
Version
Rules
Scope
EffectiveTime
```

## 537.137 — Historical policy

Past result giữ policy version.

## 537.138 — Policy diff

Semantic diff rules.

## 537.139 — Policy simulation

Evaluate historical cases against new policy.

## 537.140 — Policy rollback

Explicit.

---

# 537.141 — SAFETY KNOWLEDGE GRAPH

```text
Threat
 ↓
Attack
 ↓
Capability
 ↓
Tool
 ↓
Agent
 ↓
Model
 ↓
Deployment
 ↓
Finding
 ↓
Mitigation
 ↓
Test
```

Queries:

```text
affected_by(threat)
tests_for(capability)
findings_for(tool)
deployments_affected_by(finding)
```

---

# 537.142 — AI INTROSPECTION

Required queries:

```text
why_blocked
why_allowed
why_flagged
why_test_failed
why_test_unknown
affected_assets
affected_deployments
reproduce_finding
policy_for_finding
evidence_for_claim
```

## 537.143 — Evidence chain

Safety explanation phải link tới evidence.

## 537.144 — No fabricated explanation

Explanation không được tạo evidence không tồn tại.

---

# 537.145 — SECURITY OF THE SAFETY SYSTEM

Safety harness itself is security-sensitive.

## 537.146 — Test isolation

Tests chạy trong isolated environment khi cần.

## 537.147 — Secret isolation

Production secrets không được đưa vào red-team test mặc định.

## 537.148 — Attack corpus protection

Private attack datasets có ACL.

## 537.149 — Finding privacy

Finding có thể chứa sensitive data.

## 537.150 — Safe artifact handling

Attack artifacts không được tự động execute ngoài sandbox.

---

# 537.151 — PERFORMANCE

Safety system phải có:

```text
Fast Smoke Suite
Targeted Suite
Full Suite
Deep Red-Team Suite
```

## 537.152 — Production overhead

Không ép toàn bộ safety instrumentation vào production.

## 537.153 — Runtime enforcement

Các policy cần enforcement phải tồn tại tại runtime boundary.

## 537.154 — Offline evaluation

Supported.

## 537.155 — Deterministic evaluation

Where possible.

---

# 537.156 — FUZZING

Fuzz:

- prompt parser;
- tool schema;
- protocol;
- JSON;
- binary payload;
- model input;
- multimodal metadata;
- policy parser;
- capability representation.

## 537.157 — Stateful fuzzing

Agent session state mutations.

## 537.158 — Sequence fuzzing

Tool/action sequences.

## 537.159 — Coverage

Integrate 477.

## 537.160 — Crash minimization

Integrate 435.

---

# 537.161 — SAFETY BENCHMARK DATASET

Dataset record:

```text
SafetyDataset {
    DatasetId
    Version
    Source
    License
    ThreatModel
    Cases
    Split
    Hash
}
```

## 537.162 — Train/test separation

Safety test data must avoid accidental training leakage where relevant.

## 537.163 — Hidden evaluation

Support private evaluation sets.

## 537.164 — Dataset mutation

Changes create new version.

## 537.165 — Dataset lineage

Integrate 528.

---

# 537.166 — SAFETY AND MODEL SERVING

Integrate:

```text
529 Serving
534 Fleet
535 Agent Runtime
536 Resource Governance
```

Safety gate can inspect:

- model;
- version;
- deployment;
- tools;
- policies;
- resource limits.

## 537.167 — Safe deployment identity

Safety result tied to exact deployment configuration.

## 537.168 — Configuration drift

Drift invalidates relevant safety evidence.

## 537.169 — Tool drift

Tool version change invalidates affected tests.

## 537.170 — Policy drift

Policy change triggers re-evaluation.

---

# 537.171 — SAFETY CLAIM FORMAT

```text
SafetyClaim {
    ClaimId
    Statement
    Scope
    Population
    EvidenceRefs
    TestVersion
    PolicyVersion
    ModelVersion
    Limitations
}
```

## 537.172 — Scope

Claim must identify system/version/population.

## 537.173 — Time

Claim has evaluation timestamp.

## 537.174 — Limitations

Known blind spots recorded.

## 537.175 — No extrapolation

Passing a test suite does not establish safety outside tested scope.

---

# 537.176 — HARD INVARIANTS

1. Safety khác quality.
2. Safety khác security.
3. Safety khác reliability.
4. Safety khác correctness.
5. Safety khác compliance.
6. Safety claim có scope.
7. Safety claim có evidence.
8. Safety claim có version.
9. Safety claim có limitations.
10. Không có universal safety score.
11. Threat model là explicit artifact.
12. Asset được identify.
13. Attacker model được identify.
14. Preconditions được record.
15. Attack surface được record.
16. Impact taxonomy được version.
17. Mitigation được identify.
18. Test liên kết threat.
19. Safety case có identity.
20. Safety case có version.
21. Safety dataset có provenance.
22. Safety dataset có hash.
23. Hidden tests được hỗ trợ.
24. Prompt injection được test.
25. Indirect injection được test.
26. Tool output injection được test.
27. Retrieval injection được test.
28. Memory injection được test.
29. Multimodal injection được test.
30. Instruction/data boundary được preserve.
31. External data không tự thành policy.
32. Tool result không tự thành policy.
33. Model output không tự thành authority.
34. Tool capability explicit.
35. Tool effects explicit.
36. Tool input schema validated.
37. Tool output schema validated.
38. Tool authorization được enforce.
39. Tool argument safety được test.
40. Path traversal được test.
41. Command injection được test.
42. Network destination policy được test.
43. Oversized input được test.
44. Malformed input được test.
45. Secret classification được hỗ trợ.
46. Secret sinks được identify.
47. Redaction policy explicit.
48. Redaction không được coi là complete secrecy proof.
49. Data exfiltration được test.
50. Cross-tenant leakage được test.
51. Retrieval ACL được enforce.
52. Memory ACL được enforce.
53. Deleted data handling được test.
54. Privilege escalation được test.
55. Capability attenuation được test.
56. Child capability không vượt parent.
57. Confused deputy được test.
58. Identity propagation được preserve.
59. Authorization context không silent drop.
60. Memory provenance được preserve.
61. Memory trust level explicit.
62. Memory conflict được preserve.
63. Retrieval poisoning được test.
64. Evidence khác instruction.
65. Model output schema được validate.
66. Model output semantics có thể validate.
67. Side effect phải qua action gate.
68. Model không bypass action gate.
69. Action có identity.
70. Action revalidation được hỗ trợ.
71. Approval có binding.
72. Approval có expiry.
73. Approval replay được chặn.
74. Approval mutation invalidates token.
75. Sandbox escape được test.
76. Native in-process plugin không được coi là sandbox.
77. WASM sandbox được test.
78. Resource exhaustion được test.
79. Input limit explicit.
80. Output limit explicit.
81. Context limit explicit.
82. Tool result limit explicit.
83. Recursion limit explicit.
84. Graph expansion limit explicit.
85. Retry storm được test.
86. Model identity được record.
87. Tokenizer identity được record.
88. Policy identity được record.
89. Multimodal inputs được test.
90. OCR-derived data được distinguish.
91. ASR-derived data được distinguish.
92. Media metadata không automatically trusted.
93. Cross-modal authority không automatic.
94. Red-team scenario có identity.
95. Multi-step attack được hỗ trợ.
96. State-dependent attack được hỗ trợ.
97. Tool-dependent attack được hỗ trợ.
98. Policy-dependent attack được hỗ trợ.
99. Attack replay được hỗ trợ.
100. Destructive red-team action không execute trên production mặc định.
101. Safety oracle có type.
102. Exact oracle được hỗ trợ.
103. Schema oracle được hỗ trợ.
104. Property oracle được hỗ trợ.
105. Contract oracle được hỗ trợ.
106. Policy oracle được hỗ trợ.
107. Human oracle được hỗ trợ.
108. LLM judge được identify.
109. LLM judge không tự trở thành truth authority.
110. Finding có identity.
111. Finding có evidence.
112. Finding có reproduction khi khả thi.
113. Unknown được distinguish failure.
114. False positive được represent.
115. Absence of finding không phải proof.
116. Regression baseline có identity.
117. New failure được detect.
118. Fixed failure được detect.
119. Changed behavior được distinguish.
120. Inconclusive được distinguish.
121. Release gate dùng explicit policy.
122. Gate không phải quality score.
123. Critical finding có thể block release theo policy.
124. Waiver có owner.
125. Waiver có scope.
126. Waiver có expiry.
127. Expired waiver không bypass gate.
128. Continuous evaluation được hỗ trợ.
129. Model change có thể trigger evaluation.
130. Tool change có thể trigger evaluation.
131. Policy change có thể trigger evaluation.
132. Agent change có thể trigger evaluation.
133. Dependency change có thể trigger evaluation.
134. Deployment change có thể trigger evaluation.
135. Dataset change có thể trigger evaluation.
136. Selective evaluation integrate impact analysis.
137. Full evaluation được hỗ trợ.
138. Scheduled evaluation được hỗ trợ.
139. Incident-triggered evaluation được hỗ trợ.
140. Incident có identity.
141. Incident có timeline.
142. Incident có evidence.
143. Containment được hỗ trợ.
144. Capability revoke được hỗ trợ.
145. Tool disable được hỗ trợ.
146. Deployment drain được hỗ trợ.
147. Model rollback được hỗ trợ.
148. Memory quarantine được hỗ trợ.
149. Evidence không bị xoá khi containment.
150. Recovery preserve provenance.
151. Policy version immutable.
152. Historical result giữ policy identity.
153. Policy semantic diff được hỗ trợ.
154. Policy simulation được hỗ trợ.
155. Policy rollback explicit.
156. Safety knowledge graph được hỗ trợ.
157. Threat→test linkage được preserve.
158. Finding→deployment linkage được preserve.
159. Mitigation→test linkage được preserve.
160. `why_blocked` được hỗ trợ.
161. `why_allowed` được hỗ trợ.
162. `why_flagged` được hỗ trợ.
163. `why_test_failed` được hỗ trợ.
164. `why_test_unknown` được hỗ trợ.
165. Evidence query được hỗ trợ.
166. Safety explanations không fabricate evidence.
167. Safety harness được isolate khi cần.
168. Production secrets không tự đi vào red-team suite.
169. Attack corpus có ACL.
170. Finding privacy được hỗ trợ.
171. Attack artifacts không auto-execute.
172. Smoke/targeted/full/deep suites được hỗ trợ.
173. Safety instrumentation production là explicit.
174. Runtime policy enforcement vẫn hoạt động tại boundary cần thiết.
175. Offline safety evaluation được hỗ trợ.
176. Deterministic evaluation được hỗ trợ khi khả thi.
177. Prompt/tool/protocol fuzzing được hỗ trợ.
178. Stateful agent fuzzing được hỗ trợ.
179. Sequence fuzzing được hỗ trợ.
180. Coverage integrate 477.
181. Crash minimization integrate 435.
182. Safety dataset có train/test provenance.
183. Hidden safety set được hỗ trợ.
184. Dataset mutation tạo version.
185. Dataset lineage integrate 528.
186. Serving identity integrate 529.
187. Fleet identity integrate 534.
188. Agent identity integrate 535.
189. Resource policy integrate 536.
190. Safety evidence tied exact deployment.
191. Configuration drift có thể invalidate evidence.
192. Tool drift có thể invalidate affected evidence.
193. Policy drift trigger re-evaluation.
194. Safety claim có population.
195. Safety claim có evaluation time.
196. Safety claim có limitation.
197. Không extrapolate ngoài evaluated scope.
198. Không dùng một model tự certify chính nó.
199. Safety evidence phải reproducible khi có thể.
200. Safety result phải preserve uncertainty.
201. Security finding không tự đồng nghĩa safety finding và ngược lại.
202. Safety policy không được silently alter language semantics.
203. Safety runtime không được link vào ordinary Axiom application nếu application không dùng AI/safety capability.
204. Không có mandatory cloud safety service.
205. Local safety evaluation được hỗ trợ.
206. Offline evaluation được hỗ trợ.
207. No hidden telemetry.
208. Safety logs obey privacy policy.
209. Safety data obey retention policy.
210. Safety findings obey access control.
211. Test execution obey capability policy.
212. Red-team execution obey sandbox policy.
213. Test resources obey quota/budget.
214. Safety tests cannot silently bypass production policy.
215. Safety waiver cannot silently change policy semantics.
216. A failed safety infrastructure run không được coi là passed.
217. Missing evidence không được coi là safe.
218. Unknown không được tự chuyển thành pass.
219. Pass chỉ có nghĩa oracle đã thỏa property trong evaluated scope.
220. **Axiom Safety Evaluation phải biến threat model, prompt injection, tool misuse, privilege escalation, data leakage, sandbox, resource abuse và agentic attack thành các test/evidence/regression artifact có provenance; nó phải phân biệt rõ pass/fail/unknown/inconclusive và không được biến absence-of-finding hoặc một “safety score” thành bằng chứng an toàn tuyệt đối.**

**BOOTSTRAP-537 hoàn tất / LOCKED.**

---

# BOOTSTRAP-538 — AI GOVERNANCE, MODEL RISK MANAGEMENT, POLICY LIFECYCLE, AUDIT, APPROVAL, COMPLIANCE EVIDENCE & AI SYSTEM ACCOUNTABILITY

**Trạng thái: COMPLETED / LOCKED**

538 xây dựng lớp **governance** phía trên 527–537. Đây không phải một “AI judge”, mà là cơ chế biến model/agent/dataset/deployment/policy thành các thực thể có **owner, lifecycle, evidence, approval, audit và accountability**.

```text
Model / Agent / Dataset / Tool
             │
             ↓
        Registration
             │
             ↓
        Risk Profile
             │
             ↓
      Policy Assignment
             │
             ↓
        Evaluation
             │
             ↓
       Human Review
             │
             ↓
        Approval Gate
             │
             ↓
         Deployment
             │
             ↓
     Continuous Monitoring
             │
       ┌─────┴─────┐
       ↓           ↓
    Incident     Audit
       ↓           ↓
    Review ←→ Evidence
```

---

## 538.1 — Governance ≠ Safety

Governance quản lý:

- ownership;
- responsibility;
- approval;
- lifecycle;
- evidence;
- audit;
- policy.

Safety 537 kiểm thử safety properties.

## 538.2 — Governance ≠ Compliance

Compliance requirement là external/internal rule.

Governance là cơ chế quản lý và evidence.

## 538.3 — Accountability

Mỗi production AI artifact phải có owner.

```text
Owner
Reviewer
Operator
Approver
```

## 538.4 — AI Asset

```text
AIAsset {
    AssetId
    Kind
    Version
    Owner
    Lifecycle
    RiskProfile
}
```

Kinds:

- Model;
- Agent;
- Tool;
- Dataset;
- Workflow;
- Policy;
- Deployment;
- Evaluation.

---

# 538.5 — MODEL RISK PROFILE

```text
RiskProfile {
    Scope
    IntendedUse
    RestrictedUse
    DataClass
    CapabilityClass
    DeploymentContext
    KnownLimitations
    RequiredControls
}
```

## 538.6 — Intended use

Explicit.

## 538.7 — Restricted use

Explicit.

## 538.8 — Known limitations

Evidence-linked.

## 538.9 — Risk ≠ quality score

Risk profile không tạo universal numerical ranking.

## 538.10 — Context dependence

Cùng model có thể có risk profile khác trong deployment contexts khác nhau.

---

# 538.11 — AI ASSET REGISTRY

Registry records:

```text
AssetId
Version
ArtifactHash
Owner
Source
Dependencies
Policies
Evaluations
Approvals
Deployments
Incidents
```

## 538.12 — Immutable version

Published version immutable.

## 538.13 — Provenance

Artifact provenance integrate 506/528.

## 538.14 — Dependency graph

Model→dataset→code→tool→runtime dependencies.

## 538.15 — Impact query

```text
what_depends_on(asset)
what_changed(asset)
```

---

# 538.16 — GOVERNANCE LIFECYCLE

```text
Draft
 ↓
Registered
 ↓
Evaluated
 ↓
Reviewed
 ↓
Approved
 ↓
Deployed
 ↓
Monitored
 ↓
Retired
```

## 538.17 — State transition

Every transition requires explicit event.

## 538.18 — Invalid transition

Rejected.

## 538.19 — Versioned state

State transition references asset version.

## 538.20 — Retirement

Retired asset cannot receive new production deployment without reactivation policy.

---

# 538.21 — APPROVAL MATRIX

Possible approval scopes:

```text
Development
Internal
Staging
Production
High-Risk
External
```

## 538.22 — Separation of duties

Policy có thể yêu cầu developer ≠ approver.

## 538.23 — Approval identity

Human/service identity.

## 538.24 — Approval expiry

Approval có expiry.

## 538.25 — Approval scope

Không approve toàn bộ asset nếu request chỉ scoped deployment.

---

# 538.26 — EVIDENCE PACKAGE

```text
EvidencePackage {
    Asset
    Build
    Dataset
    Evaluation
    Safety
    Security
    Policy
    Review
    Approval
}
```

## 538.27 — Evidence hash

Package có content identity.

## 538.28 — Evidence provenance

Mọi evidence reference exact source.

## 538.29 — Evidence completeness

Missing required evidence → incomplete, không tự coi pass.

## 538.30 — Evidence expiration

Một số evidence có validity window.

---

# 538.31 — AUDIT LOG

```text
AuditEvent {
    EventId
    Timestamp
    Principal
    Action
    Asset
    Before
    After
    Evidence
}
```

## 538.32 — Append-only

Audit log append-only trong logical model.

## 538.33 — Tamper evidence

Hash chain/signature có thể sử dụng.

## 538.34 — Time

Timestamp integrate 474.

## 538.35 — Identity

Principal identity phải được preserve.

---

# 538.36 — POLICY LIFECYCLE

```text
Draft
 ↓
Review
 ↓
Approved
 ↓
Effective
 ↓
Deprecated
 ↓
Retired
```

## 538.37 — Policy version

Immutable published version.

## 538.38 — Effective time

Explicit.

## 538.39 — Scope

Policy có scope.

## 538.40 — Conflict

Conflicting policies phải được detect.

---

# 538.41 — POLICY TESTING

Mỗi policy nên có:

```text
Rule
ExpectedDecision
TestCases
Exceptions
```

## 538.42 — Policy unit test

Individual rule.

## 538.43 — Policy integration test

Interaction between rules.

## 538.44 — Policy regression

Previous cases rerun after policy change.

## 538.45 — Policy simulation

No side effect.

---

# 538.46 — MODEL CARD / SYSTEM CARD EQUIVALENT

Axiom có structured artifact:

```text
ModelRecord {
    Identity
    IntendedUse
    Limitations
    TrainingDataRef
    EvaluationRef
    SafetyRef
    SecurityRef
    License
}
```

Không yêu cầu một văn bản prose cụ thể.

## 538.47 — Agent record

Agent tương tự nhưng thêm:

- tools;
- memory;
- policy;
- workflow;
- capabilities.

## 538.48 — Tool record

Tool thêm:

- effects;
- sandbox;
- capability requirements;
- ABI/protocol.

---

# 538.49 — DATA GOVERNANCE LINK

528 cung cấp:

- dataset identity;
- lineage;
- rights;
- retention;
- deletion.

## 538.50 — Training lineage

Model record links exact training dataset version.

## 538.51 — Evaluation lineage

Evaluation links exact dataset.

## 538.52 — Retrieval lineage

Production RAG links source/index versions where policy requires.

## 538.53 — Deletion impact

Dataset deletion can query affected models/evaluations/indexes.

---

# 538.54 — SECURITY GOVERNANCE

Integrates 490/537.

Track:

- threat model;
- security tests;
- vulnerabilities;
- mitigations;
- exceptions.

## 538.55 — Security exception

Exception:

```text
Reason
Scope
Owner
Expiry
Mitigation
```

## 538.56 — Expiration

Expired exception no longer valid.

## 538.57 — Vulnerability link

Finding links affected assets.

## 538.58 — Remediation

Remediation action has owner/status/deadline.

---

# 538.59 — INCIDENT GOVERNANCE

Incident states:

```text
Detected
Triaged
Contained
Investigating
Remediating
Resolved
Closed
```

## 538.60 — Incident ownership

Explicit.

## 538.61 — Severity

Severity taxonomy is organizational policy.

## 538.62 — Evidence

Incident evidence immutable/referenceable.

## 538.63 — Affected versions

Exact.

## 538.64 — Customer impact

Can be recorded where applicable.

---

# 538.65 — CHANGE MANAGEMENT

Change types:

```text
Model
Agent
Tool
Policy
Dataset
Runtime
Dependency
Infrastructure
```

## 538.66 — Impact analysis

Integrate 486.

## 538.67 — Required reevaluation

Policy determines which changes trigger evaluation.

## 538.68 — Approval

High-impact change can require review.

## 538.69 — Rollback

Change must identify rollback artifact where feasible.

---

# 538.70 — DEPLOYMENT GATE

```text
Asset
 ↓
Policy Requirements
 ↓
Evidence Check
 ↓
Safety Check
 ↓
Security Check
 ↓
Approval Check
 ↓
Deployment
```

## 538.71 — Gate failure

Deployment blocked or requires explicit exception.

## 538.72 — Missing evidence

Never silently treated as passed.

## 538.73 — Stale evidence

Marked stale.

## 538.74 — Configuration drift

Deployment no longer matches approved evidence → revalidation.

## 538.75 — Runtime drift

Tool/model/runtime change may invalidate approval.

---

# 538.76 — CONTINUOUS GOVERNANCE

Monitor:

- asset changes;
- policy changes;
- dependency changes;
- incidents;
- safety regressions;
- security findings;
- data governance changes.

## 538.77 — Re-certification

Policy can require periodic re-evaluation.

## 538.78 — Expiring approval

Deployment may enter review state.

## 538.79 — Auto-disable

Only explicit policy may automatically disable.

## 538.80 — No hidden shutdown

Governance layer cannot silently terminate ordinary applications.

---

# 538.81 — MULTI-TENANT GOVERNANCE

Tenant-scoped:

- assets;
- policies;
- evidence;
- approvals;
- audit;
- incidents.

## 538.82 — Tenant isolation

Tenant cannot access another tenant's restricted governance data.

## 538.83 — Cross-tenant asset

Explicit sharing agreement/capability.

## 538.84 — Shared model

Governance identity remains global while deployment authorization remains tenant-specific.

---

# 538.85 — REGULATORY / POLICY MAPPING

External requirements represented as:

```text
Requirement
 ↓
Control
 ↓
Evidence
 ↓
Test
 ↓
Approval
```

## 538.86 — Requirement identity

External rule gets source/reference/version.

## 538.87 — Control

Concrete technical/organizational control.

## 538.88 — Evidence

Control evidence linked.

## 538.89 — No invented compliance

Axiom cannot claim compliance merely because controls exist.

## 538.90 — Compliance assessment

External/legal assessment remains separate from compiler semantics.

---

# 538.91 — AUDIT EXPORT

Formats:

- JSON;
- structured archive;
- CSV where appropriate;
- human-readable report.

## 538.92 — Export scope

Explicit.

## 538.93 — Redaction

Sensitive fields redacted according to policy.

## 538.94 — Evidence references

Exports preserve IDs.

## 538.95 — Reproducibility

Export includes schema version.

---

# 538.96 — GOVERNANCE GRAPH

```text
Asset
 ├── Owner
 ├── Version
 ├── Dataset
 ├── Model
 ├── Tool
 ├── Policy
 ├── Evaluation
 ├── Safety
 ├── Security
 ├── Approval
 ├── Deployment
 └── Incident
```

## 538.97 — Query API

```text
owner(asset)
dependencies(asset)
evidence(asset)
approvals(asset)
deployments(asset)
incidents(asset)
required_controls(asset)
```

## 538.98 — Change impact

`impact(change)` integrates 486.

## 538.99 — Audit explainability

`why_deployed(asset)`.

## 538.100 — Decision evidence

Every governance decision references evidence/policy.

---

# 538.101 — AI GOVERNANCE INTROSPECTION

Queries:

```text
why_approved
why_rejected
why_deployed
why_blocked
why_review_required
what_evidence_missing
what_evidence_expired
what_changed
who_approved
who_owns
what_policy_applies
```

## 538.102 — No fabricated accountability

System records identities; it does not infer responsibility from model output.

## 538.103 — Evidence-first explanation

Explanation references concrete audit/evidence records.

---

# 538.104 — RETENTION

Governance artifacts may have retention policies.

## 538.105 — Legal hold

Retention can override ordinary deletion where explicitly required.

## 538.106 — Deletion

Deletion creates audit event without retaining prohibited sensitive payload.

## 538.107 — Evidence references

Deleted artifacts become tombstoned references where policy permits.

---

# 538.108 — GOVERNANCE SECURITY

Governance database is high-value target.

Protect:

- approvals;
- policy;
- secrets;
- audit;
- asset provenance.

## 538.109 — Authorization

Fine-grained.

## 538.110 — Immutable evidence

Critical records tamper-evident.

## 538.111 — Separation

Governance operator authority separate from application authority where policy requires.

## 538.112 — Emergency override

Explicit, scoped, audited, expiring.

---

# 538.113 — TESTING

Test:

- invalid lifecycle transition;
- approval replay;
- expired approval;
- stale evidence;
- policy conflict;
- tenant isolation;
- audit tampering;
- rollback;
- incident recovery;
- deletion impact.

## 538.114 — Deterministic governance tests

Same inputs → same decision under same policy/version.

## 538.115 — Policy simulation

Changes evaluated without deployment.

## 538.116 — Audit verification

Hash/signature chain verification.

## 538.117 — Recovery

Governance DB crash recovery.

## 538.118 — Backup

Backup/restore with provenance.

---

# 538.119 — HARD INVARIANTS

1. Governance khác safety.
2. Governance khác compliance.
3. Asset có identity.
4. Asset có version.
5. Asset có owner.
6. Asset có lifecycle.
7. Model là governance asset.
8. Agent là governance asset.
9. Tool là governance asset.
10. Dataset là governance asset.
11. Workflow là governance asset.
12. Policy là governance asset.
13. Deployment là governance asset.
14. Evaluation là governance artifact.
15. Risk profile explicit.
16. Intended use explicit.
17. Restricted use explicit.
18. Known limitations evidence-linked.
19. Risk không phải universal quality score.
20. Risk context-dependent.
21. Asset registry được hỗ trợ.
22. Published asset immutable.
23. Artifact hash preserved.
24. Provenance preserved.
25. Dependency graph preserved.
26. Impact analysis supported.
27. Lifecycle states explicit.
28. Lifecycle transitions explicit.
29. Invalid transitions rejected.
30. Retirement explicit.
31. Approval scope explicit.
32. Approval identity explicit.
33. Approval expiry explicit.
34. Separation of duties configurable.
35. Evidence package has identity.
36. Evidence has provenance.
37. Evidence completeness distinguish.
38. Evidence expiration supported.
39. Audit event has identity.
40. Audit has timestamp.
41. Audit has principal.
42. Audit records action.
43. Audit references asset.
44. Audit records before/after where appropriate.
45. Audit references evidence.
46. Audit logically append-only.
47. Tamper evidence supported.
48. Policy lifecycle explicit.
49. Policy version immutable.
50. Policy effective time explicit.
51. Policy scope explicit.
52. Policy conflict detection supported.
53. Policy unit testing supported.
54. Policy integration testing supported.
55. Policy regression supported.
56. Policy simulation supported.
57. Model record has identity.
58. Model record can reference training data.
59. Model record can reference evaluation.
60. Model record can reference safety.
61. Model record can reference security.
62. Model record can reference license.
63. Agent record references tools.
64. Agent record references memory.
65. Agent record references policy.
66. Agent record references workflow.
67. Tool record references effects.
68. Tool record references capabilities.
69. Tool record references sandbox.
70. Dataset lineage integrates 528.
71. Training lineage is exact where available.
72. Evaluation lineage preserved.
73. Retrieval lineage can be preserved.
74. Deletion impact supported.
75. Security governance integrates 490.
76. Safety governance integrates 537.
77. Security exceptions have owner.
78. Security exceptions have expiry.
79. Security exceptions have mitigation.
80. Incident has identity.
81. Incident has owner.
82. Incident has lifecycle.
83. Incident evidence preserved.
84. Affected versions explicit.
85. Remediation has owner.
86. Change types explicit.
87. Change impact integrates 486.
88. Reevaluation policy explicit.
89. High-impact changes can require approval.
90. Rollback artifact can be recorded.
91. Deployment gate is explicit.
92. Gate requirements are policy-defined.
93. Missing evidence is not pass.
94. Stale evidence is distinguishable.
95. Configuration drift can invalidate evidence.
96. Runtime drift can invalidate evidence.
97. Continuous governance supported.
98. Recertification supported.
99. Expiring approval supported.
100. Auto-disable only by explicit policy.
101. No hidden shutdown of ordinary programs.
102. Tenant governance data isolated.
103. Cross-tenant assets explicit.
104. Shared model governance global identity preserved.
105. External requirement identity preserved.
106. Control maps to requirement.
107. Control maps to evidence.
108. Control maps to test.
109. Compliance is not invented from technical metadata.
110. External/legal assessment remains external.
111. Audit export has explicit scope.
112. Export preserves evidence IDs.
113. Export schema versioned.
114. Governance graph supported.
115. Owner query supported.
116. Evidence query supported.
117. Approval query supported.
118. Deployment query supported.
119. Incident query supported.
120. Policy query supported.
121. `why_approved` supported.
122. `why_rejected` supported.
123. `why_deployed` supported.
124. `why_blocked` supported.
125. Missing evidence query supported.
126. Expired evidence query supported.
127. Change query supported.
128. Approval identity query supported.
129. Ownership query supported.
130. Applicable policy query supported.
131. Governance explanation references evidence.
132. Governance does not fabricate accountability.
133. Retention policy explicit.
134. Legal hold supported where required.
135. Deletion creates auditable event.
136. Sensitive deleted payload is not automatically retained.
137. Tombstone references can be supported.
138. Governance database is access-controlled.
139. Critical evidence can be tamper-evident.
140. Emergency override explicit.
141. Emergency override scoped.
142. Emergency override audited.
143. Emergency override expires.
144. Invalid approval replay rejected.
145. Expired approval rejected.
146. Stale evidence detected.
147. Policy conflicts detected.
148. Tenant isolation tested.
149. Audit tampering tested.
150. Rollback tested.
151. Incident recovery tested.
152. Governance deletion impact tested.
153. Deterministic governance decisions supported.
154. Policy simulation has no side effects.
155. Audit verification supported.
156. Governance backup supported.
157. Governance restore preserves provenance.
158. Governance does not alter model semantics.
159. Governance does not alter Axiom language semantics.
160. Governance does not become mandatory application runtime.
161. No mandatory cloud governance service.
162. Local governance deployment supported.
163. Offline governance artifacts supported.
164. Governance evidence can be exported.
165. Governance metadata can be consumed by AI tools.
166. AI cannot silently approve itself.
167. Model output cannot create approval authority.
168. Tool output cannot create governance authority.
169. External data cannot modify policy authority.
170. Governance authority follows authenticated principal/capability.
171. Governance actions are auditable.
172. Policy changes are auditable.
173. Approval changes are auditable.
174. Deployment changes are auditable.
175. Ownership changes are auditable.
176. Evidence changes are versioned.
177. Asset version cannot silently mutate.
178. Historical governance records remain interpretable.
179. Evidence schema evolution is versioned.
180. Governance queries obey ACL.
181. Private governance evidence cannot leak across tenants.
182. Safety evidence remains distinct from compliance evidence.
183. Security evidence remains distinct from safety evidence.
184. Performance evidence remains distinct from safety evidence.
185. Evaluation result remains distinct from approval.
186. Approval remains distinct from deployment.
187. Deployment remains distinct from operation.
188. Incident remains distinct from finding.
189. Finding remains distinct from policy violation.
190. Policy violation remains distinct from legal conclusion.
191. Governance does not infer legal liability.
192. Governance does not infer human intent.
193. Governance does not infer model mental state.
194. Governance does not infer undocumented responsibility.
195. External attestations can be attached as evidence.
196. Attestation identity is preserved.
197. Attestation scope is preserved.
198. Attestation expiry is preserved.
199. Audit export preserves temporal ordering where available.
200. **Axiom AI Governance phải tạo một chuỗi accountability có thể kiểm toán từ asset → owner → policy → evaluation → evidence → approval → deployment → monitoring → incident, nhưng không được biến metadata kỹ thuật thành kết luận pháp lý, không tự suy diễn trách nhiệm/conformance, và không trở thành authority ẩn của chương trình.**

**BOOTSTRAP-538 hoàn tất / LOCKED.**

### Task kế tiếp

**`BOOTSTRAP-539 — AI MODEL/AGENT VERSIONING 2.0, SEMANTIC COMPATIBILITY, MODEL MIGRATION, PROMPT/TOOL/MEMORY SCHEMA EVOLUTION & BACKWARD-COMPATIBLE AI SYSTEM UPGRADES`**