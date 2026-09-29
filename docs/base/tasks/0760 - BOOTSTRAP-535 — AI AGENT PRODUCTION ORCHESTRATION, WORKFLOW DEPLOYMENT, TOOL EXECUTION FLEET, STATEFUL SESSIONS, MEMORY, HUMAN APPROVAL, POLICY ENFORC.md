# BOOTSTRAP-535 — AI AGENT PRODUCTION ORCHESTRATION, WORKFLOW DEPLOYMENT, TOOL EXECUTION FLEET, STATEFUL SESSIONS, MEMORY, HUMAN APPROVAL, POLICY ENFORCEMENT & LONG-RUNNING AGENT RUNTIME

**Trạng thái: COMPLETED / LOCKED**

535 xây dựng lớp production cho Agent 511, phía trên Model Serving 529 và Fleet Orchestration 534.

```text
Agent Definition 511
        │
        ↓
Workflow / Policy
        │
        ↓
Agent Deployment 535
        │
 ┌──────┼───────────┐
 ↓      ↓           ↓
Session Memory    Tool Fleet
 │       │           │
 └──────┼───────────┘
        ↓
 Agent Runtime
        │
        ↓
Observe → Decide → Act
        │
        ↓
Validation / Approval
        │
        ↓
Result / Checkpoint
```

---

## 535.1 — Agent ≠ Model ≠ Session ≠ Workflow

- **Model**: khả năng suy luận/generation.
- **Agent**: policy + goal + memory + tools + execution loop.
- **Workflow**: graph các bước.
- **Session**: trạng thái của một lần tương tác.
- **Deployment**: instance production của agent.

Không được conflated.

## 535.2 — AgentDefinition

```text
AgentDefinition {
    AgentId
    Version
    ModelReference
    ToolSet
    MemoryPolicy
    Policy
    Workflow
    ResourceLimits
}
```

## 535.3 — Immutable version

Published agent version immutable.

## 535.4 — Deployment

```text
AgentDeployment {
    DeploymentId
    AgentVersion
    RuntimeVersion
    Target
    Replicas
    Resources
}
```

## 535.5 — Agent runtime

Runtime thực hiện execution loop; không tự sở hữu authority ngoài capabilities được cấp.

---

# 535.6 — AGENT SESSION

Session:

```text
AgentSession {
    SessionId
    AgentVersion
    State
    Context
    MemoryRefs
    PendingActions
    Checkpoints
}
```

## 535.7 — Stateless agent

Agent có thể chạy request độc lập.

## 535.8 — Stateful agent

Session giữ state qua nhiều requests.

## 535.9 — Session affinity

Stateful session phải route tới runtime có state hoặc state store tương thích.

## 535.10 — Session migration

Migration explicit.

## 535.11 — Session expiration

TTL/deadline configurable.

## 535.12 — Session cancellation

Cancellation phải propagate tới pending actions.

---

# 535.13 — AGENT STATE

State gồm:

```text
Goal
Context
Observations
Plan
PendingActions
Results
Errors
Budget
Deadline
Checkpoint
```

## 535.14 — State transitions

Mỗi transition có sequence number.

## 535.15 — Append-only event log

Có thể bật cho durable/replayable agents.

## 535.16 — Checkpoint

Checkpoint lưu state có version/hash.

## 535.17 — Recovery

Runtime có thể resume từ checkpoint.

## 535.18 — Exactly-once không mặc định

Replay có thể làm action lặp lại.

## 535.19 — Idempotency

External side-effecting tools nên có idempotency key.

## 535.20 — Action identity

```text
ActionId
```

duy nhất trong session/deployment scope.

---

# 535.21 — LONG-RUNNING AGENT

Agent có thể tồn tại:

- giây;
- phút;
- giờ;
- ngày.

## 535.22 — Lease

Long-running session có execution lease.

## 535.23 — Heartbeat

Runtime có thể heartbeat.

## 535.24 — Lease expiry

Expired lease không được tiếp tục side effect nếu policy yêu cầu fencing.

## 535.25 — Resume

Agent có thể resume từ checkpoint.

## 535.26 — Crash recovery

Crash không làm mất checkpoint đã durable.

## 535.27 — Partial execution

Recovery phải distinguish:

```text
planned
started
completed
failed
unknown
```

## 535.28 — Unknown side effect

Nếu crash xảy ra sau external action nhưng trước acknowledgement → `Unknown`, không tự giả định failed.

---

# 535.29 — WORKFLOW ENGINE

Workflow:

```text
Start
 ↓
Step
 ↓
Branch
 ├── Step A
 └── Step B
 ↓
Join
 ↓
Complete
```

## 535.30 — Workflow node

```text
WorkflowNode {
    NodeId
    InputSchema
    OutputSchema
    Effects
    RetryPolicy
    Timeout
}
```

## 535.31 — DAG

DAG mặc định.

## 535.32 — Cycles

Cycle phải explicit.

## 535.33 — Conditional branch

Branch expression typed.

## 535.34 — Parallel branch

Independent nodes có thể chạy song song.

## 535.35 — Join

Join policy explicit.

## 535.36 — Failure propagation

Continue/fail/retry/compensate policy explicit.

## 535.37 — Compensation

Compensation là action riêng, không phải rollback thần kỳ.

## 535.38 — Workflow checkpoint

Node completion được checkpoint nếu durable mode.

## 535.39 — Workflow version

Workflow version immutable.

## 535.40 — Workflow migration

Running workflow migration phải explicit.

---

# 535.41 — TOOL EXECUTION FLEET

```text
Agent
 │
 ↓
Tool Router
 │
 ├── Local Tool
 ├── Process Tool
 ├── Remote Tool
 ├── WASM Tool
 └── Sandboxed Tool
```

## 535.42 — Tool instance

Tool server/instance có identity.

## 535.43 — Tool capability

Capability explicit.

## 535.44 — Tool health

Ready/unhealthy/draining.

## 535.45 — Tool routing

Theo:

- tool identity;
- version;
- capability;
- locality;
- load;
- tenant.

## 535.46 — Tool version pinning

Agent có thể pin exact tool version.

## 535.47 — Tool compatibility

Input/output/effect schema phải compatible.

## 535.48 — Tool pool

Nhiều instances có thể phục vụ cùng tool.

## 535.49 — Tool concurrency

Per-tool concurrency limit.

## 535.50 — Tool isolation

Untrusted tools chạy process/WASM sandbox khi policy yêu cầu.

---

# 535.51 — APPROVAL BOUNDARY

Side effects được phân loại:

```text
Pure
Read
Write
External
Irreversible
```

## 535.52 — Approval policy

Policy xác định action nào cần approval.

## 535.53 — Approval token

```text
ApprovalToken {
    TokenId
    ActionId
    Scope
    Expiry
    Approver
}
```

## 535.54 — Token scope

Approval chỉ có hiệu lực cho action/scope đã cấp.

## 535.55 — No approval reuse

Token không được dùng cho action khác.

## 535.56 — Expiration

Expired approval invalid.

## 535.57 — Human identity

Approver identity được audit.

## 535.58 — Multi-party approval

Có thể yêu cầu nhiều approvers.

## 535.59 — Dry-run

Agent có thể generate planned actions mà chưa execute.

## 535.60 — Preview

Side-effecting action có preview representation nếu tool hỗ trợ.

---

# 535.61 — POLICY ENGINE

Policy áp dụng lên:

- model;
- tool;
- data;
- network;
- filesystem;
- process;
- budget;
- user;
- tenant;
- deployment.

## 535.62 — Policy decision

```text
Allow
Deny
RequireApproval
Constrain
```

## 535.63 — Policy version

Policy immutable/versioned.

## 535.64 — Policy precedence

Explicit, deterministic.

## 535.65 — Fail-closed

Security-sensitive unknown policy → deny/review according to policy.

## 535.66 — Policy provenance

Every denial/approval references policy rule.

## 535.67 — Policy simulation

Dry-run policy evaluation.

## 535.68 — Policy explanation

```text
why_allowed(action)
why_denied(action)
why_approval_required(action)
```

## 535.69 — Capability attenuation

Child agent/tool không được tự tăng authority.

## 535.70 — Delegation

Parent có thể delegate subset capability.

---

# 535.71 — MEMORY

Memory types:

```text
Working
Episodic
Semantic
Procedural
Cache
```

## 535.72 — Working memory

Current session context.

## 535.73 — Episodic

Past events.

## 535.74 — Semantic

Persistent knowledge.

## 535.75 — Procedural

Learned/reusable procedures.

## 535.76 — Cache

Performance data không nhất thiết semantic truth.

## 535.77 — Memory provenance

Mỗi memory item có source.

## 535.78 — Memory confidence

Confidence/uncertainty explicit nếu có.

## 535.79 — Memory version

Updated memory tạo revision.

## 535.80 — Memory deletion

Deletion policy explicit.

---

# 535.81 — CONTEXT MANAGEMENT

Context assembly:

```text
Goal
 ↓
System/Agent Policy
 ↓
Relevant Memory
 ↓
Current Session
 ↓
Tool Results
 ↓
Retrieved Evidence
 ↓
Model Input
```

## 535.82 — Priority

Context priority explicit.

## 535.83 — Token budget

Hard context limit.

## 535.84 — Truncation

Truncation policy explicit.

## 535.85 — Summarization

Summarized context retains provenance.

## 535.86 — Tool result separation

Tool output remains data unless explicitly designated instruction by trusted policy.

## 535.87 — External data

External documents never automatically gain policy authority.

## 535.88 — Prompt injection

Agent must preserve instruction/data boundary.

## 535.89 — Secret context

Secrets carry sensitivity metadata.

## 535.90 — Secret propagation

Secret data must obey downstream capability policy.

---

# 535.91 — AGENT SCHEDULING

Integrates 471.

Scheduling dimensions:

- priority;
- deadline;
- tenant;
- resource;
- model;
- tool;
- locality.

## 535.92 — Concurrency limit

Per-agent/session/deployment.

## 535.93 — Queue limit

Bounded queues supported.

## 535.94 — Backpressure

Explicit overload behavior.

## 535.95 — Fairness

Fairness policy configurable.

## 535.96 — Starvation

Scheduler may detect starvation.

## 535.97 — Deadline

474 deadline propagated.

## 535.98 — Cancellation

Cancellation propagates through workflow.

## 535.99 — Retry

Retries require policy.

## 535.100 — Retry budget

Prevent retry storms.

---

# 535.101 — MODEL ROUTING

Agent can reference:

```text
ModelId
Version
Variant
Capability
```

## 535.102 — Model fallback

Fallback explicit.

## 535.103 — Version compatibility

Fallback must satisfy contract.

## 535.104 — Session consistency

Stateful model session cannot silently switch incompatible model.

## 535.105 — Model failure

Classified separately from agent failure.

## 535.106 — Model timeout

Timeout propagates.

## 535.107 — Model cancellation

Cancellation propagated.

## 535.108 — Model budget

Token/compute budget.

## 535.109 — Model provenance

Exact serving model recorded.

## 535.110 — Model output provenance

Generated result references model/version/session.

---

# 535.111 — TOOL FAILURE

Failure classes:

```text
InvalidInput
Unauthorized
Unavailable
Timeout
Cancelled
ResourceExhausted
RemoteFailure
ProtocolError
Unknown
```

## 535.112 — Retryability

Each error declares retryable/non-retryable/unknown.

## 535.113 — Retry idempotency

Non-idempotent action không retry mặc định.

## 535.114 — Circuit breaker

Optional.

## 535.115 — Fallback tool

Explicit.

## 535.116 — Compensation

Workflow compensation explicit.

## 535.117 — Unknown completion

Never convert unknown external state to failure automatically.

## 535.118 — Error provenance

Tool/version/request/action identity.

## 535.119 — Error context

No secret leakage.

## 535.120 — Error normalization

Agent runtime may normalize protocol errors while preserving original details.

---

# 535.121 — HUMAN-IN-THE-LOOP

Approval request:

```text
ApprovalRequest {
    ActionId
    Description
    Scope
    RiskClass
    Preview
    Expiry
}
```

## 535.122 — Approval channel

UI/API/CLI.

## 535.123 — Approval timeout

Explicit.

## 535.124 — Timeout policy

Deny/cancel/escalate.

## 535.125 — Rejection

Rejection becomes structured result.

## 535.126 — Modification

Human may modify parameters only through validated transaction.

## 535.127 — Revalidation

Modified action must be validated again.

## 535.128 — Approval audit

Record.

## 535.129 — Emergency stop

Operator can stop deployment/session.

## 535.130 — Stop semantics

Stop prevents future actions and cancels pending actions according to capability policy.

---

# 535.131 — AGENT OBSERVABILITY

Integrates 475/481.

Track:

- session latency;
- model latency;
- tool latency;
- queue latency;
- planning steps;
- retries;
- tokens;
- memory retrieval;
- approval wait;
- failures;
- resource use.

## 535.132 — Trace

Every action gets TraceId/SpanId.

## 535.133 — Step trace

Observe/Decide/Act/Validate spans.

## 535.134 — Tool trace

Tool call linked.

## 535.135 — Model trace

Model request linked.

## 535.136 — Memory trace

Retrieval linked.

## 535.137 — Policy trace

Decision linked.

## 535.138 — Human trace

Approval linked.

## 535.139 — Privacy

Sensitive arguments redacted.

## 535.140 — No automatic telemetry

Explicit configuration required.

---

# 535.141 — AGENT SECURITY

Trust boundaries:

```text
User
 ↓
Agent
 ↓
Model
 ↓
Tool
 ↓
External System
```

## 535.142 — Model output untrusted

Model-generated instructions do not automatically gain authority.

## 535.143 — Tool result untrusted

Tool results are data unless trusted by explicit policy.

## 535.144 — User data

Input is subject to tenant/privacy policy.

## 535.145 — Capability check

Every side effect crosses capability boundary.

## 535.146 — SSRF protection

Remote tools must constrain destinations.

## 535.147 — Path protection

Filesystem tools enforce capability-scoped paths.

## 535.148 — Process protection

Shell/process tools explicit.

## 535.149 — Secret protection

Secrets cannot be automatically exposed to arbitrary model/tool.

## 535.150 — Exfiltration controls

Outbound channels subject to policy.

---

# 535.151 — MULTI-AGENT

```text
Supervisor
 ├── Agent A
 ├── Agent B
 └── Agent C
```

## 535.152 — Agent identity

Each agent has identity/version.

## 535.153 — Child capabilities

Subset of parent.

## 535.154 — Communication

Typed messages/channels.

## 535.155 — Shared memory

Explicit.

## 535.156 — Agent mailbox

Capacity/ordering explicit.

## 535.157 — Supervision

Failure/restart policy.

## 535.158 — Child termination

Parent can cancel child.

## 535.159 — Result aggregation

Typed.

## 535.160 — Cycles

Agent delegation cycles detected/limited.

---

# 535.161 — RESOURCE GOVERNANCE

Budgets:

```text
Time
Tokens
CPU
GPU
Memory
Network
ToolCalls
Steps
Storage
```

## 535.162 — Hierarchical budgets

Deployment → session → workflow → step.

## 535.163 — Budget reservation

Optional.

## 535.164 — Budget consumption

Measured.

## 535.165 — Budget exhaustion

Explicit failure/cancellation.

## 535.166 — Hard vs soft

Hard limit prevents continuation; soft limit warns.

## 535.167 — Resource accounting

Usage attributed to agent/session/tenant.

## 535.168 — Shared resources

Shared model/tool resources must not double-count physical resource incorrectly.

## 535.169 — Cost metadata

Cost can be measured without being universal monetary truth.

## 535.170 — No hidden unlimited retry

Retries consume budget.

---

# 535.171 — DEPLOYMENT

Deployment lifecycle:

```text
Draft
 ↓
Validated
 ↓
Staged
 ↓
Active
 ↓
Draining
 ↓
Stopped
```

## 535.172 — Deployment revision

Immutable.

## 535.173 — Rollout

Integrates 534.

## 535.174 — Canary

Integrates 534.

## 535.175 — Shadow

Integrates 534.

## 535.176 — Autoscaling

Integrates 534.

## 535.177 — Rollback

Explicit.

## 535.178 — Drain

Existing sessions finish according to policy.

## 535.179 — Forced stop

Explicit emergency operation.

## 535.180 — Deployment provenance

Agent/model/tool/policy versions recorded.

---

# 535.181 — TESTING & REPLAY

## 535.182 — Deterministic simulation

Mock model/tools.

## 535.183 — Recorded replay

Replay session event stream.

## 535.184 — Tool mocking

Tool results can be deterministic fixtures.

## 535.185 — Model mocking

Model responses can be fixture-based.

## 535.186 — Fault injection

Timeout/failure/cancellation/resource exhaustion.

## 535.187 — Approval simulation

Synthetic approval/rejection.

## 535.188 — Policy simulation

Test policy changes without side effects.

## 535.189 — Replay safety

Replay does not execute real irreversible actions by default.

## 535.190 — Differential workflow test

Compare state transitions, not merely final text.

---

# 535.191 — AI INTROSPECTION

```text
why_action
why_tool
why_model
why_memory
why_denied
why_approval
why_retry
why_cancelled
why_failed
why_budget_exhausted
```

## 535.192 — Decision provenance

Agent decision references context/evidence available at decision time.

## 535.193 — Context snapshot

Optional exact model input snapshot subject to privacy policy.

## 535.194 — Policy snapshot

Exact policy version.

## 535.195 — Tool snapshot

Exact tool version/schema.

## 535.196 — Model snapshot

Exact model version.

## 535.197 — Memory snapshot

Referenced memory revisions.

## 535.198 — Workflow snapshot

Exact workflow revision.

## 535.199 — Reproduction

These identities enable replay/reconstruction.

## 535.200 — No fabricated reasoning

Runtime metadata records observable execution evidence, not an invented internal chain of thought.

---

# 535.201 — HARD INVARIANTS

1. Agent khác model.
2. Agent khác workflow.
3. Agent khác session.
4. Deployment khác agent definition.
5. Agent version immutable.
6. Deployment revision immutable.
7. AgentDefinition có identity.
8. Model reference explicit.
9. Tool set explicit.
10. Memory policy explicit.
11. Agent policy explicit.
12. Resource limits explicit.
13. Session có identity.
14. Stateful/stateless semantics explicit.
15. Stateful routing preserve state.
16. Session migration explicit.
17. Session expiration explicit.
18. Session cancellation propagates.
19. Agent state có version.
20. State transition có sequence.
21. Event log có thể append-only.
22. Checkpoint có identity.
23. Checkpoint có hash.
24. Recovery dùng checkpoint đã durable.
25. Replay không mặc định exactly-once.
26. External action có ActionId.
27. Unknown external completion được preserve.
28. Idempotency key được hỗ trợ.
29. Workflow node có schema.
30. Workflow node có effects.
31. Workflow version immutable.
32. DAG mặc định.
33. Cycles explicit.
34. Conditional branch typed.
35. Parallel branch explicit.
36. Join policy explicit.
37. Failure propagation explicit.
38. Compensation khác rollback.
39. Workflow checkpoint được hỗ trợ.
40. Workflow migration explicit.
41. Tool instance có identity.
42. Tool capability explicit.
43. Tool health explicit.
44. Tool routing explicit.
45. Tool version pinning được hỗ trợ.
46. Tool compatibility được verify.
47. Tool pool được hỗ trợ.
48. Tool concurrency giới hạn được.
49. Untrusted tool có thể sandbox.
50. Side effects có classification.
51. Approval policy explicit.
52. Approval token có identity.
53. Approval token scoped.
54. Approval token có expiry.
55. Approval token không reuse ngoài scope.
56. Approver identity được audit.
57. Multi-party approval được hỗ trợ.
58. Dry-run được hỗ trợ.
59. Preview được hỗ trợ khi tool cho phép.
60. Policy version immutable.
61. Policy decision có Allow/Deny/Approval/Constrain.
62. Policy precedence deterministic.
63. Security-sensitive unknown không được mặc định allow.
64. Policy provenance được preserve.
65. Policy simulation được hỗ trợ.
66. Child capability không được vượt parent.
67. Delegation attenuation được enforce.
68. Working memory được distinguish.
69. Episodic memory được distinguish.
70. Semantic memory được distinguish.
71. Procedural memory được distinguish.
72. Cache memory được distinguish.
73. Memory provenance được preserve.
74. Memory confidence có thể represent.
75. Memory revision được preserve.
76. Memory deletion explicit.
77. Context budget explicit.
78. Context priority explicit.
79. Truncation policy explicit.
80. Summarization preserve provenance.
81. Tool output không tự gain instruction authority.
82. External data không tự gain policy authority.
83. Prompt injection boundary được preserve.
84. Secret context có sensitivity.
85. Secret propagation obey policy.
86. Agent scheduling integrate 471.
87. Concurrency limit explicit.
88. Queue limit explicit.
89. Backpressure được hỗ trợ.
90. Fairness policy configurable.
91. Deadline integrate 474.
92. Cancellation integrate 474/471.
93. Retry policy explicit.
94. Retry budget explicit.
95. Model fallback explicit.
96. Model fallback phải compatible.
97. Stateful model không silent switch.
98. Model failure được classify.
99. Model timeout propagate.
100. Model cancellation propagate.
101. Model compute/token budget explicit.
102. Exact model version được record.
103. Model output provenance được preserve.
104. Tool failure taxonomy structured.
105. Retryability explicit.
106. Non-idempotent action không retry mặc định.
107. Circuit breaker có thể hỗ trợ.
108. Fallback tool explicit.
109. Unknown tool completion preserve.
110. Tool error provenance preserve.
111. Error context không leak secret.
112. Human approval request có identity.
113. Approval request có scope.
114. Approval request có expiry.
115. Approval timeout explicit.
116. Rejection structured.
117. Modified action phải revalidate.
118. Approval audit được preserve.
119. Emergency stop được hỗ trợ.
120. Stop semantics explicit.
121. Agent tracing integrate 475/481.
122. Action trace có identity.
123. Tool trace linked.
124. Model trace linked.
125. Memory trace linked.
126. Policy trace linked.
127. Human approval trace linked.
128. Sensitive trace data redacted.
129. Không automatic telemetry.
130. Model output không có authority mặc định.
131. Tool result không có authority mặc định.
132. External input untrusted.
133. Side effects require capability.
134. Network capability scoped.
135. Filesystem capability scoped.
136. Process execution explicit.
137. Secret access explicit.
138. Exfiltration controls explicit.
139. Multi-agent identity explicit.
140. Child capability attenuation.
141. Typed inter-agent communication.
142. Shared memory explicit.
143. Mailbox capacity explicit.
144. Supervision explicit.
145. Child cancellation supported.
146. Result aggregation typed.
147. Delegation cycles bounded/detected.
148. Time budget explicit.
149. Token budget explicit.
150. CPU budget explicit.
151. GPU budget explicit.
152. Memory budget explicit.
153. Network budget explicit.
154. Tool-call budget explicit.
155. Step budget explicit.
156. Storage budget explicit.
157. Hierarchical budgets supported.
158. Budget consumption measurable.
159. Hard/soft budget distinction.
160. Resource attribution preserved.
161. Retry consumes budget.
162. Deployment lifecycle explicit.
163. Deployment state versioned.
164. Rollout integrates 534.
165. Canary integrates 534.
166. Shadow integrates 534.
167. Autoscaling integrates 534.
168. Rollback explicit.
169. Drain explicit.
170. Forced stop explicit.
171. Deployment provenance preserves agent/model/tool/policy identities.
172. Deterministic simulation supported.
173. Recorded replay supported.
174. Tool mocking supported.
175. Model mocking supported.
176. Fault injection supported.
177. Approval simulation supported.
178. Policy simulation supported.
179. Replay does not execute irreversible real actions by default.
180. Workflow differential testing supported.
181. `why_action` query supported.
182. `why_tool` query supported.
183. `why_model` query supported.
184. `why_memory` query supported.
185. `why_denied` query supported.
186. `why_approval` query supported.
187. `why_retry` query supported.
188. `why_cancelled` query supported.
189. `why_failed` query supported.
190. `why_budget_exhausted` query supported.
191. Decision provenance preserved.
192. Context snapshot can be preserved subject to privacy.
193. Policy snapshot preserved.
194. Tool schema/version snapshot preserved.
195. Model snapshot preserved.
196. Memory revisions preserved.
197. Workflow revision preserved.
198. Replay reconstruction uses exact identities.
199. Runtime does not fabricate hidden reasoning evidence.
200. Agent runtime has no ambient authority.
201. Agent cannot silently elevate capability.
202. Agent cannot silently bypass approval.
203. Tool cannot silently bypass policy.
204. Model cannot silently execute tools.
205. Memory cannot silently become trusted instruction.
206. External data cannot silently become policy.
207. Deployment cannot silently change agent version.
208. Rollout cannot mutate immutable agent version.
209. Rollback cannot delete failed execution evidence.
210. Checkpoint cannot claim completion without durable state.
211. Unknown external side effect cannot be converted to failed automatically.
212. Retry cannot exceed configured budget.
213. Cancellation must propagate to cancellable descendants.
214. Session state cannot cross tenants without explicit capability.
215. Memory ACL must follow tenant/security policy.
216. Tool results must retain provenance.
217. Model results must retain provenance.
218. Approval decisions must retain provenance.
219. Policy decisions must retain provenance.
220. Resource consumption must be attributable.
221. Agent execution must remain inspectable.
222. Production orchestration must remain separate from language core.
223. No mandatory agent runtime is linked into ordinary Axiom applications.
224. No mandatory model provider is built into Axiom.
225. No mandatory cloud service is required.
226. Local/offline agent execution is supported where dependencies are local.
227. Sandbox policy integrates 490.
228. Model registry integrates 533.
229. Model fleet integrates 534.
230. Knowledge/RAG integrates 512.
231. Dataset governance integrates 528.
232. Evaluation integrates 527/532.
233. Tool protocol integrates 513 when implemented.
234. Agent metadata integrates 446.
235. Agent observability integrates 475/481.
236. Agent scheduling integrates 471.
237. Async integrates 424.
238. Time/deadline integrates 474.
239. Security capabilities integrate 490.
240. **Axiom Agent Production Runtime phải cho phép triển khai agent dài hạn, stateful workflow, tool fleet, memory, human approval, policy enforcement, recovery và multi-agent orchestration với provenance đầy đủ; mọi authority và side effect đều explicit, không có ambient authority, hidden tool execution, hidden approval bypass hoặc runtime agent dependency trong các chương trình Axiom thông thường.**

**BOOTSTRAP-535 hoàn tất / LOCKED.**

---

# BOOTSTRAP-536 — AI AGENT ECONOMICS, RESOURCE/COST ACCOUNTING, QUOTA, BUDGET, ADMISSION CONTROL, FINOPS & COMPUTE ALLOCATION

**Trạng thái: COMPLETED / LOCKED**

Đây là lớp tiếp theo cần thiết sau 535: production Agent không chỉ cần biết **đang chạy gì**, mà phải biết **đang tiêu tốn tài nguyên nào, thuộc về ai, theo budget nào và tại sao bị giới hạn**.

```text
Agent / Workflow
       │
       ↓
Resource Request
       │
       ↓
Admission Control
       │
 ┌─────┼──────────────┐
 ↓     ↓              ↓
Quota Budget       Priority
 │     │              │
 └─────┼──────────────┘
       ↓
Resource Allocation
       │
 ┌─────┼───────────────┐
 ↓     ↓               ↓
CPU   GPU             Model
 ↓     ↓               ↓
Tool / Network / Storage
       │
       ↓
Usage Metering
       │
       ↓
Cost Attribution
       │
       ↓
Budget / Quota Enforcement
```

---

## 536.1 — Resource ≠ Cost

Phải phân biệt:

```text
Resource
Usage
Allocation
Quota
Budget
Cost
Price
```

CPU time là resource/usage.

GPU-hours là usage.

Giá tiền là cost theo pricing policy.

Không được conflated.

## 536.2 — Usage Record

```text
UsageRecord {
    UsageId
    TenantId
    AgentId
    SessionId
    Resource
    Quantity
    Start
    End
    Source
}
```

## 536.3 — Resource dimensions

Tối thiểu:

- CPU time;
- RAM;
- GPU compute;
- VRAM;
- NPU compute;
- storage;
- network ingress;
- network egress;
- model tokens;
- tool calls;
- execution steps;
- wall-clock time.

## 536.4 — Allocation

Resource allocation có owner và lifetime.

## 536.5 — Reservation

Resource có thể được reserve trước execution.

## 536.6 — Actual usage

Reservation khác actual usage.

## 536.7 — Quota

Quota giới hạn resource usage trong scope.

## 536.8 — Budget

Budget giới hạn execution/cost theo policy.

## 536.9 — Price

Pricing là external policy, không phải language semantic.

## 536.10 — Cost estimate

Estimate phải được distinguish khỏi actual cost.

---

# 536.11 — RESOURCE HIERARCHY

```text
Organization
   ↓
Project
   ↓
Tenant
   ↓
Deployment
   ↓
Agent
   ↓
Session
   ↓
Workflow
   ↓
Step
   ↓
Tool / Model
```

## 536.12 — Hierarchical quota

Parent quota giới hạn child aggregate.

## 536.13 — Child budget

Child có thể có budget nhỏ hơn parent.

## 536.14 — Budget reservation

Parent có thể reserve budget cho child.

## 536.15 — No budget amplification

Child không thể tạo budget vượt parent.

---

# 536.16 — ADMISSION CONTROL

Admission decision:

```text
Accept
Reject
Queue
Degrade
RequireApproval
```

## 536.17 — Admission inputs

- resource availability;
- quota;
- budget;
- priority;
- deadline;
- capability;
- model availability;
- tool availability.

## 536.18 — Admission explanation

```text
why_rejected(request)
why_queued(request)
why_degraded(request)
```

## 536.19 — Queue fairness

Policy-defined.

## 536.20 — Overload

Overload không được chuyển thành infinite queue.

---

# 536.21 — RESOURCE PRIORITY

Priority dimensions:

- emergency;
- interactive;
- batch;
- background;
- tenant;
- deadline.

## 536.22 — Priority inversion

Scheduler có thể detect priority inversion.

## 536.23 — Starvation

Long-running low-priority work phải có explicit starvation policy.

## 536.24 — Priority ≠ authorization

High priority không cấp thêm capability.

## 536.25 — Priority ≠ quality

Priority không phải đánh giá model/agent.

---

# 536.26 — TOKEN ACCOUNTING

LLM execution records:

```text
prompt_tokens
cached_tokens
output_tokens
total_tokens
```

## 536.27 — Token identity

Token counts tied to exact model/tokenizer.

## 536.28 — Cached tokens

Cached input tokens distinguish khỏi uncached.

## 536.29 — Streaming tokens

Incremental token usage.

## 536.30 — Token budget

Session/agent/workflow budgets.

## 536.31 — Context budget

Context length khác cost budget.

## 536.32 — Tool token usage

Tool-generated content may contribute to context usage.

## 536.33 — Token estimation

Estimates phải marked estimated.

## 536.34 — Provider billing

Provider-reported usage may differ from locally measured usage; preserve both.

## 536.35 — No fabricated billing

Axiom does not infer provider billing from token count unless pricing policy is explicit.

---

# 536.36 — GPU ACCOUNTING

Track:

- device;
- allocation;
- VRAM;
- compute duration;
- kernel execution;
- transfer;
- stream;
- model.

## 536.37 — GPU reservation

Reservation explicit.

## 536.38 — Shared GPU

Shared usage attribution explicit.

## 536.39 — GPU partition

Physical partition identity.

## 536.40 — Transfer accounting

Host↔device bytes.

---

# 536.41 — TOOL ACCOUNTING

Record:

```text
ToolCallId
ToolVersion
Duration
CPU
Memory
Network
ResultSize
RetryCount
```

## 536.42 — Tool pricing

External provider pricing metadata optional.

## 536.43 — Retry cost

Retries count toward usage.

## 536.44 — Failed calls

Failed calls may still consume resources.

## 536.45 — Cancelled calls

Partial usage preserved.

---

# 536.46 — COST ATTRIBUTION

Cost dimensions:

```text
Organization
Tenant
Project
Agent
Session
Workflow
Step
Model
Tool
Device
Region
```

## 536.47 — Shared model cost

Shared inference cost requires allocation policy.

## 536.48 — Allocation methods

Possible:

- actual measured;
- proportional;
- reserved;
- provider-reported;
- estimated.

## 536.49 — Method identity

Attribution result records method.

## 536.50 — No false precision

Estimated cost cannot be represented as exact actual billing.

---

# 536.51 — BUDGET STATES

```text
Available
Reserved
Consumed
Exceeded
Released
Expired
```

## 536.52 — Reservation expiration

Expired reservation released.

## 536.53 — Atomic reservation

Where supported, reservation is atomic.

## 536.54 — Partial allocation

Partial allocation explicit.

## 536.55 — Budget exhaustion

Policy determines:

- stop;
- degrade;
- queue;
- ask approval.

---

# 536.56 — DEGRADATION

Agent can explicitly degrade:

```text
Large Model → Smaller Model
FP32 → FP16
GPU → CPU
High Context → Reduced Context
Parallel → Sequential
```

## 536.57 — Degradation policy

Explicit.

## 536.58 — Contract preservation

Degradation cannot silently violate required API contract.

## 536.59 — Version provenance

Exact fallback model recorded.

## 536.60 — User-visible degradation

Policy may require notification.

---

# 536.61 — FINOPS

FinOps is ecosystem/platform layer.

Not language core.

## 536.62 — Cost report

```text
CostReport {
    Period
    Scope
    Usage
    PricingPolicy
    EstimatedCost
    ActualCost
}
```

## 536.63 — Pricing policy

Versioned.

## 536.64 — Currency

Explicit currency.

## 536.65 — Tax/fees

Separate components.

## 536.66 — Provider billing

Provider invoice can be imported.

## 536.67 — Reconciliation

Actual provider billing vs internal metering.

## 536.68 — Discrepancy

Difference reported, not silently corrected.

## 536.69 — Forecast

Forecast clearly marked prediction/estimate.

## 536.70 — No universal cost score

Cost reports measurements only.

---

# 536.71 — QUOTA POLICY

Quota types:

- concurrent requests;
- tokens;
- CPU;
- GPU;
- memory;
- network;
- storage;
- tool calls;
- sessions.

## 536.72 — Time windows

Second/minute/hour/day/month/custom.

## 536.73 — Sliding window

Supported.

## 536.74 — Fixed window

Supported.

## 536.75 — Token bucket

Supported.

## 536.76 — Leaky bucket

Supported.

## 536.77 — Distributed quota

Consistency model explicit.

## 536.78 — Approximate quota

Marked approximate.

## 536.79 — Fail-open/closed

Explicit.

## 536.80 — Quota inheritance

Parent-child hierarchy.

---

# 536.81 — RESOURCE POOL

Pools:

```text
CPU Pool
GPU Pool
NPU Pool
Memory Pool
Network Pool
Model Pool
Tool Pool
```

## 536.82 — Pool capacity

Observed capacity.

## 536.83 — Reserved capacity

Separate.

## 536.84 — Free capacity

Calculated.

## 536.85 — Overcommit

Allowed only explicit.

## 536.86 — Oversubscription

Tracked.

## 536.87 — Admission

Uses pool state.

## 536.88 — Pool isolation

Tenant/project pools.

## 536.89 — Borrowing

Resource borrowing explicit.

## 536.90 — Reclamation

Idle resources reclaimed according to policy.

---

# 536.91 — RESOURCE SCHEDULING

Scheduler considers:

```text
priority
deadline
quota
budget
capacity
locality
model
tool
tenant
```

## 536.92 — Preemption

Optional.

## 536.93 — Preemption safety

Cannot preempt non-interruptible critical section blindly.

## 536.94 — Graceful preemption

Drain/cancel/checkpoint.

## 536.95 — Checkpoint-aware scheduling

535 checkpoints can enable pause/resume.

## 536.96 — GPU preemption

Hardware-dependent.

## 536.97 — CPU preemption

OS scheduler/runtime.

## 536.98 — No hard latency promise

Scheduling policy is not deterministic latency guarantee unless environment guarantees it.

## 536.99 — Fair sharing

Optional policy.

## 536.100 — Weighted sharing

Explicit weights.

---

# 536.101 — RESOURCE OBSERVABILITY

Metrics:

- requested;
- reserved;
- allocated;
- used;
- released;
- wasted;
- queued;
- rejected.

## 536.102 — Waste

Unused reservation can be measured.

## 536.103 — Utilization

Utilization definition explicit.

## 536.104 — Saturation

Queue/capacity pressure.

## 536.105 — Efficiency

Derived metric, not universal quality score.

---

# 536.106 — BUDGET ALERTS

States:

```text
Normal
Warning
Critical
Exceeded
```

## 536.107 — Threshold

Project policy.

## 536.108 — Alert channels

Log/event/webhook/UI.

## 536.109 — Alert deduplication

Explicit.

## 536.110 — Alert suppression

Policy-controlled.

---

# 536.111 — COST GUARDRAILS

Examples:

```text
max_session_cost
max_tool_calls
max_model_tokens
max_gpu_seconds
max_wall_time
```

## 536.112 — Guardrail action

Stop/degrade/queue/approval.

## 536.113 — Guardrail scope

Agent/session/workflow/tenant.

## 536.114 — Guardrail inheritance

Child cannot exceed parent.

## 536.115 — Guardrail bypass

Only explicit privileged operation.

---

# 536.116 — RESOURCE LEAK DETECTION

Detect:

- abandoned session;
- unreleased reservation;
- orphaned GPU allocation;
- stuck tool;
- stale lease.

## 536.117 — Lease

Resource lease has expiry.

## 536.118 — Reclamation

Expired lease can reclaim resource.

## 536.119 — Safety

Reclamation must not kill active work incorrectly.

## 536.120 — Orphan state

Orphaned resources are observable.

---

# 536.121 — MULTI-TENANT COST ISOLATION

Tenant accounting:

```text
Tenant
 ├── Models
 ├── Tools
 ├── Sessions
 ├── Storage
 └── Network
```

## 536.122 — Tenant budget

Explicit.

## 536.123 — Tenant quota

Explicit.

## 536.124 — Cross-tenant shared resource

Allocation policy explicit.

## 536.125 — Cost privacy

Tenant A cannot inspect tenant B's sensitive usage.

## 536.126 — Aggregated reporting

Can expose aggregate data under policy.

## 536.127 — Internal overhead

Control-plane overhead may be attributed separately.

## 536.128 — Shared infrastructure

Infrastructure cost can be allocated by documented method.

## 536.129 — No hidden subsidy claim

Cost attribution does not imply actual provider billing unless reconciled.

## 536.130 — Audit

Usage records auditable.

---

# 536.131 — AI INTROSPECTION

Queries:

```text
why_rejected
why_queued
why_scaled
why_degraded
why_budget_exceeded
resource_usage
cost_breakdown
quota_status
budget_status
allocation
```

## 536.132 — Explain admission

References exact policy/capacity.

## 536.133 — Explain degradation

References trigger and fallback.

## 536.134 — Explain cost

References usage + pricing policy.

## 536.135 — Explain quota

References scope/window/current usage.

## 536.136 — Explain scaling

Integrates 534 evidence.

## 536.137 — Explain model cost

Exact model/version.

## 536.138 — Explain tool cost

Exact tool/version.

## 536.139 — Explain shared cost

Allocation method.

## 536.140 — Evidence first

Every derived cost/usage explanation points to raw measurements.

---

# 536.141 — TESTING

Test:

- quota;
- budget;
- reservation;
- release;
- exhaustion;
- concurrent allocation;
- race;
- retry;
- cancellation;
- crash;
- reconciliation;
- distributed consistency.

## 536.142 — Deterministic quota test

Virtual clock 474.

## 536.143 — Fault injection

Control-plane failure.

## 536.144 — Duplicate accounting

Duplicate event detection.

## 536.145 — Lost accounting

Missing usage detection.

## 536.146 — Reconciliation

Usage ledger vs runtime telemetry.

## 536.147 — Precision

Units explicitly tested.

## 536.148 — Overflow

Large usage counters checked.

## 536.149 — Privacy tests

Tenant isolation.

## 536.150 — Replay

Accounting event replay must be deterministic.

---

# 536.151 — HARD INVARIANTS

1. Resource khác cost.
2. Usage khác allocation.
3. Allocation khác reservation.
4. Quota khác budget.
5. Cost khác price.
6. Estimate khác actual.
7. Usage record có identity.
8. Usage có owner.
9. Usage có resource dimension.
10. Usage có quantity.
11. Usage có thời gian.
12. CPU usage được measure.
13. RAM usage được measure.
14. GPU usage được measure.
15. VRAM usage được measure.
16. NPU usage có thể measure.
17. Storage usage được measure.
18. Network usage được measure.
19. Token usage được measure.
20. Tool-call usage được measure.
21. Step usage được measure.
22. Wall-clock usage được measure.
23. Resource hierarchy được hỗ trợ.
24. Parent quota được enforce.
25. Child budget không vượt parent.
26. Admission control được hỗ trợ.
27. Admission có Accept/Reject/Queue.
28. Degrade có thể hỗ trợ.
29. Approval admission có thể hỗ trợ.
30. Admission decision có provenance.
31. Infinite queue không được mặc định.
32. Priority được distinguish authorization.
33. Priority không cấp capability.
34. Priority không phải quality score.
35. Token usage tied exact model.
36. Token usage tied tokenizer.
37. Cached tokens distinguish.
38. Streaming token usage được track.
39. Estimated tokens marked estimated.
40. Provider usage được distinguish local usage.
41. Billing không được tự suy diễn.
42. GPU device identity được preserve.
43. GPU reservation explicit.
44. Shared GPU attribution explicit.
45. GPU partition identity được preserve.
46. Host/device transfer được track.
47. Tool version được track.
48. Tool duration được track.
49. Tool resource usage được track.
50. Tool retries được track.
51. Failed calls có thể consume resource.
52. Cancelled calls preserve partial usage.
53. Cost attribution có scope.
54. Shared cost có allocation method.
55. Allocation method được record.
56. Estimated cost marked estimated.
57. Cost không có false precision.
58. Budget states explicit.
59. Reservation có lifecycle.
60. Reservation expiration được hỗ trợ.
61. Atomic reservation có thể hỗ trợ.
62. Partial allocation explicit.
63. Budget exhaustion explicit.
64. Degradation policy explicit.
65. Degradation không phá required contract.
66. Fallback model identity được record.
67. Fallback model version được record.
68. Degradation có thể require user visibility.
69. FinOps là platform layer.
70. Pricing policy versioned.
71. Currency explicit.
72. Fees/tax distinguish.
73. Provider billing import được hỗ trợ.
74. Billing reconciliation được hỗ trợ.
75. Billing discrepancy không silently corrected.
76. Forecast marked forecast.
77. Không có universal cost score.
78. Quota types explicit.
79. Quota windows explicit.
80. Fixed window được hỗ trợ.
81. Sliding window được hỗ trợ.
82. Token bucket được hỗ trợ.
83. Leaky bucket được hỗ trợ.
84. Distributed quota semantics explicit.
85. Approximate quota marked approximate.
86. Fail-open/closed explicit.
87. Quota inheritance được hỗ trợ.
88. Resource pools được hỗ trợ.
89. Pool capacity được distinguish observed/reserved/free.
90. Overcommit explicit.
91. Oversubscription tracked.
92. Pool admission explicit.
93. Pool isolation được hỗ trợ.
94. Resource borrowing explicit.
95. Resource reclamation được hỗ trợ.
96. Scheduling dùng quota.
97. Scheduling dùng budget.
98. Scheduling dùng capacity.
99. Scheduling dùng deadline.
100. Scheduling dùng locality khi policy yêu cầu.
101. Preemption optional.
102. Preemption safety explicit.
103. Graceful preemption supported.
104. Checkpoint-aware scheduling supported.
105. GPU preemption target-dependent.
106. Không claim hard latency guarantee từ scheduler policy.
107. Fair sharing optional.
108. Weighted sharing explicit.
109. Resource observability được hỗ trợ.
110. Requested/reserved/allocated/used/released distinguish.
111. Wasted reservation có thể measure.
112. Utilization definition explicit.
113. Saturation observable.
114. Efficiency không phải universal quality score.
115. Budget alerts được hỗ trợ.
116. Alert thresholds là project policy.
117. Alert channels explicit.
118. Alert deduplication supported.
119. Alert suppression policy-controlled.
120. Cost guardrails được hỗ trợ.
121. Session cost limit supported.
122. Tool-call limit supported.
123. Token limit supported.
124. GPU-time limit supported.
125. Wall-time limit supported.
126. Guardrail scope explicit.
127. Guardrail inheritance enforced.
128. Guardrail bypass explicit.
129. Resource leak detection được hỗ trợ.
130. Resource leases được hỗ trợ.
131. Lease expiry explicit.
132. Reclamation safety được enforce.
133. Orphan resources observable.
134. Tenant budget explicit.
135. Tenant quota explicit.
136. Shared tenant resources have attribution policy.
137. Tenant cost data isolated.
138. Aggregate reporting can be policy-controlled.
139. Infrastructure overhead separately attributable.
140. Shared infrastructure allocation method recorded.
141. Usage audit được hỗ trợ.
142. `why_rejected` supported.
143. `why_queued` supported.
144. `why_scaled` supported.
145. `why_degraded` supported.
146. `why_budget_exceeded` supported.
147. Resource usage query supported.
148. Cost breakdown query supported.
149. Quota status query supported.
150. Budget status query supported.
151. Allocation query supported.
152. Admission explanation references capacity/policy evidence.
153. Degradation explanation references trigger.
154. Cost explanation references measurements.
155. Quota explanation references window/scope.
156. Scaling explanation integrates 534.
157. Model cost identifies exact model version.
158. Tool cost identifies exact tool version.
159. Shared cost exposes allocation method.
160. Derived reports reference raw evidence.
161. Quota race conditions are tested.
162. Budget races are tested.
163. Reservation/release races are tested.
164. Cancellation accounting is tested.
165. Crash recovery accounting is tested.
166. Distributed consistency is tested.
167. Duplicate accounting detection is tested.
168. Missing accounting detection is tested.
169. Usage reconciliation is supported.
170. Virtual-clock quota testing integrates 474.
171. Control-plane failure injection is supported.
172. Units are explicitly validated.
173. Counters are overflow-safe.
174. Tenant isolation is tested.
175. Accounting replay is deterministic.
176. Usage records have provenance.
177. Cost reports have provenance.
178. Pricing reports have provenance.
179. Budget decisions have provenance.
180. Quota decisions have provenance.
181. Resource allocation has provenance.
182. Model usage integrates 529.
183. Fleet usage integrates 534.
184. Agent usage integrates 535.
185. Tool usage integrates 513/535.
186. Model registry identity integrates 533.
187. Dataset-related compute lineage integrates 528.
188. Evaluation compute integrates 527/532.
189. Profiling integrates 476/481.
190. Observability integrates 475.
191. Configuration integrates 470.
192. Security capabilities integrate 490.
193. Time windows integrate 474.
194. Cancellation integrates 424/471.
195. Resource ownership integrates 423.
196. No mandatory cloud billing service exists.
197. Local/offline accounting is supported.
198. Accounting does not become language-core semantics.
199. Pricing does not affect program correctness semantics.
200. Cost policy cannot silently change model semantics.
201. Quota enforcement cannot silently grant capabilities.
202. Budget exhaustion cannot silently continue unlimited execution.
203. Resource reclamation cannot silently destroy protected state.
204. Shared-resource allocation cannot expose another tenant's private usage.
205. Provider billing cannot be represented as verified without provider evidence.
206. Forecast cannot be presented as actual usage.
207. Estimate cannot be presented as exact measurement.
208. Retry consumption must be accounted.
209. Failed execution consumption must be accounted when measurable.
210. Partial execution must preserve partial usage.
211. Unknown usage must remain unknown rather than zero.
212. Missing telemetry must not be interpreted as zero consumption.
213. Duplicate usage events must not double-charge verified ledger entries.
214. Usage ledger must support idempotent event identity.
215. Cost attribution must remain reproducible under same inputs.
216. Pricing policy changes do not mutate historical raw usage.
217. Historical cost reports preserve pricing-policy identity.
218. Quota policy changes preserve historical policy identity.
219. Budget policy changes preserve historical policy identity.
220. Resource accounting must remain auditable.
221. **Axiom Resource/Cost Governance phải biến tài nguyên, quota, budget, allocation và cost thành dữ liệu đo lường có provenance và policy rõ ràng; nó phải ngăn runaway execution và hỗ trợ FinOps/AI introspection, nhưng không được biến pricing hoặc cloud economics thành semantics của ngôn ngữ hay tạo ra các “quality/cost scores” mang tính phán xét.**

**BOOTSTRAP-536 hoàn tất / LOCKED.**

### Task kế tiếp

**`BOOTSTRAP-537 — AI SAFETY EVALUATION, POLICY TESTING, RED-TEAM SIMULATION, PROMPT-INJECTION DEFENSE, TOOL-SAFETY VALIDATION & CONTINUOUS SAFETY REGRESSION`**