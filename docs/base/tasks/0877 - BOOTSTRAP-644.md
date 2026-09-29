Tiếp tục với **BOOTSTRAP-644 — Native AI Agent, Tool Calling, Structured Generation, Context Runtime, Memory, RAG, Planning & Autonomous Task Runtime 5.0**.

:::writing{variant="document" id="74126" title="BOOTSTRAP-644 — Native AI Agent, Tool Calling, Structured Generation, Context Runtime, Memory, RAG, Planning & Autonomous Task Runtime 5.0"}
# BOOTSTRAP-644
## Native AI Agent, Tool Calling, Structured Generation, Context Runtime, Memory, Retrieval-Augmented Execution, Planning & Autonomous Task Runtime 5.0

**Status:** COMPLETE  
**Layer:** Native AI Agent & Cognitive Application Runtime  
**Depends on:** BOOTSTRAP-600 → BOOTSTRAP-643

---

# 1. Mục tiêu

BOOTSTRAP-644 xây dựng lớp runtime native phía trên 643 để Axiom có thể tạo:

- AI agent;
- tool-using agent;
- structured-output agent;
- RAG application;
- conversational AI;
- workflow-driven agent;
- planning/execution agent;
- memory-enabled agent;
- multi-agent system;
- local AI application;
- remote-model application;
- AI coding assistant;
- AI automation system;
- model orchestration;
- retrieval pipeline;
- agent server.

Điểm quan trọng:

> **644 không phải một LLM runtime.**

643 đã cung cấp tensor/model execution.

644 cung cấp **orchestration, context, tool, memory, planning và execution semantics**.

---

# 2. Boundary

| Layer | Responsibility |
|---|---|
| 641 | Search/retrieval/index/vector search |
| 642 | Analytics/DataFrame/OLAP |
| 643 | Tensor/model/training/inference |
| 629 | Durable workflows |
| 631 | Distributed services |
| 634 | Event bus/stream |
| 639 | Policy/admission |
| 640 | Data governance |
| **644** | AI agent execution |

644 không được:

- tự cấp capability;
- tự bypass security;
- tự bypass governance;
- tự tải arbitrary executable code;
- biến prompt thành arbitrary native execution;
- yêu cầu Python runtime.

---

# 3. Core architecture

```text id="5d3x1u"
                    AI Application
                          │
                          ▼
                     AgentRuntime
                          │
             ┌────────────┼────────────┐
             ▼            ▼            ▼
          Context       Memory        Planner
             │            │            │
             └────────────┼────────────┘
                          ▼
                    Model Executor
                          │
             ┌────────────┼────────────┐
             ▼            ▼            ▼
          Generate       Tool        Retrieve
             │            │            │
             │            ▼            ▼
             │        ToolRuntime     641
             │            │
             └────────────┼────────────
                          ▼
                    Agent State
                          │
              ┌───────────┼───────────┐
              ▼           ▼           ▼
             628         629         634
           Memory      Workflow      Events
```

---

# 4. Design principles

1. Agent execution is explicit.
2. Model inference is separate from orchestration.
3. Tool execution is capability-controlled.
4. Context is typed.
5. Memory is typed.
6. Agent state is checkpointable.
7. Planning is not execution.
8. Generated plans are untrusted data.
9. Tool arguments are schema-validated.
10. Structured output is schema-validated.
11. Retrieval is a provider operation.
12. Prompt construction is deterministic where required.
13. No arbitrary code execution from model output.
14. No implicit network access.
15. No implicit filesystem access.
16. No implicit process execution.
17. No implicit secrets.
18. No mandatory external agent framework.
19. No mandatory cloud provider.
20. Local models and remote models use the same model interface.
21. Agent capabilities are attenuated.
22. Long-running agents use 629.
23. Distributed agents use 631/630/635.
24. Agent data follows 640 governance.
25. All important execution state is inspectable.

---

# 5. Core objects

```text id="k0a3sd"
Agent
AgentId
AgentVersion
AgentDefinition
AgentRuntime
AgentSession
AgentRun
AgentStep
AgentState

Model
ModelProvider
ModelRequest
ModelResponse
GenerationConfig

Context
ContextItem
ContextWindow
ContextBudget
ContextPolicy

Message
SystemMessage
UserMessage
AssistantMessage
ToolMessage
DeveloperMessage

Tool
ToolId
ToolSchema
ToolCall
ToolResult
ToolRuntime
ToolExecution

Plan
PlanStep
PlanState
Planner
PlannerResult

Memory
MemoryId
MemoryItem
MemoryStore
MemoryQuery
MemoryWrite
MemoryPolicy

Retriever
RetrievalQuery
RetrievalResult
RetrievedDocument
Citation

PromptTemplate
PromptContext
StructuredSchema
StructuredValue

AgentCheckpoint
AgentEvent
AgentTrace
```

---

# 6. Agent

Agent là immutable definition + mutable execution state.

```text id="qgukq1"
Agent {
    definition
    model
    tools
    memory
    policies
    runtime_limits
}
```

---

# 7. Agent definition

Bao gồm:

- agent ID;
- version;
- model reference;
- system policy;
- tool declarations;
- memory policy;
- context policy;
- planning policy;
- resource policy.

---

# 8. Agent version

Immutable.

Thay đổi definition tạo version mới.

---

# 9. Agent session

Session đại diện một conversation/execution context.

---

# 10. Agent run

Một lần execution của agent.

```text id="e9nq9f"
AgentRunId
AgentId
SessionId
Generation
```

---

# 11. Agent step

Một step có thể là:

```text id="s0n5qk"
Generate
ToolCall
ToolResult
Retrieve
Plan
Observe
Wait
Complete
Fail
```

---

# 12. State machine

```text id="0sl5m8"
Created
→ Running
→ Waiting
→ ExecutingTool
→ Observing
→ Planning
→ Running
→ Completed
```

Failure:

```text id="b1qk6k"
→ Failed
→ Recovering
→ Resumed
```

---

# 13. Terminal states

```text id="z7s8n0"
Completed
Failed
Cancelled
TimedOut
PolicyDenied
ResourceExceeded
```

---

# 14. Agent generation

Generation prevents stale execution from modifying newer state.

---

# 15. Context

Context là typed collection of information supplied to model.

---

# 16. Context item

```text id="8i8xoq"
ContextItem {
    kind
    source
    content
    priority
    sensitivity
    timestamp
    provenance
}
```

---

# 17. Context kinds

```text id="m3db5k"
Instruction
Conversation
ToolResult
RetrievedDocument
Memory
SystemFact
UserFact
ModelOutput
Schema
Constraint
```

---

# 18. Context priority

Context có priority explicit.

---

# 19. Context provenance

Mỗi item có source:

```text id="4q0e7g"
User
Application
Tool
Retriever
Memory
System
Model
```

---

# 20. Context trust

Không phải context item nào cũng có cùng authority.

---

# 21. Instruction hierarchy

Runtime phân biệt:

```text id="v4gq8n"
System
Developer
Application
User
Tool
RetrievedData
ModelGenerated
```

Model-generated text không tự trở thành instruction có authority cao hơn.

---

# 22. Prompt injection boundary

Retrieved content/tool output được xem là **data**, không mặc định là instruction.

---

# 23. Context policy

```text id="i3p1tq"
max_tokens
max_items
max_bytes
allowed_sources
retention
priority_rules
```

---

# 24. Context budget

Budget được tính trước khi model invocation.

---

# 25. Context compaction

Có thể:

- truncate;
- summarize;
- compress;
- retrieve relevant history.

---

# 26. Compaction safety

Compaction không được biến untrusted data thành trusted instruction.

---

# 27. Conversation message

```text id="k4w8l9"
Message {
    role
    content
    metadata
}
```

---

# 28. Multimodal content

Message có thể chứa:

```text id="2v0u3x"
Text
Image
Audio
Video
Document
StructuredData
```

---

# 29. Media integration

616 cung cấp media representation.

---

# 30. Image input

Có thể chuyển image thành model-compatible tensor thông qua 643/provider.

---

# 31. Audio input

616 → preprocessing → 643.

---

# 32. Document input

612/617/641/642 providers.

---

# 33. Structured output

Model output có thể yêu cầu schema.

---

# 34. StructuredSchema

Schema sử dụng 612 schema system.

---

# 35. StructuredValue

Output phải validate trước khi application sử dụng.

---

# 36. Schema failure

Nếu output invalid:

```text id="o4a6lf"
ValidationFailed
```

không được coi là valid tool call.

---

# 37. Repair

Có thể yêu cầu model sửa output trong giới hạn retry budget.

---

# 38. Tool

Tool là typed capability endpoint.

```text id="8g6x3h"
Tool {
    id
    version
    schema
    capability_requirements
    execution_policy
}
```

---

# 39. Tool schema

Schema gồm:

```text id="n4e1mm"
name
description
input_schema
output_schema
errors
limits
```

---

# 40. Tool call

```text id="2f0m4w"
ToolCall {
    call_id
    tool_id
    arguments
}
```

---

# 41. Tool argument validation

Arguments được validate trước execution.

---

# 42. Tool result

```text id="d7v0qk"
ToolResult {
    call_id
    status
    output
    error
    metadata
}
```

---

# 43. Tool states

```text id="2p3xzx"
Created
Validated
Admitted
Running
Completed
Failed
Cancelled
TimedOut
Denied
```

---

# 44. Tool capability

Tool execution requires capabilities from 603.

---

# 45. Capability attenuation

Agent receives only subset required by declared tools.

---

# 46. No capability amplification

Model output cannot create new capabilities.

---

# 47. Tool approval

Certain tools can require explicit approval.

---

# 48. Approval token

639 approval system can issue bounded approval.

---

# 49. Tool timeout

Every tool call has timeout.

---

# 50. Tool resource budget

Every tool call has:

```text id="e6w5yc"
CPU
memory
network
storage
time
```

limits.

---

# 51. Tool idempotency

Tool declares:

```text id="r4s8hy"
Idempotent
NonIdempotent
Unknown
```

---

# 52. Retry

Only retry when policy allows.

---

# 53. Side effects

Tool declares whether it has side effects.

---

# 54. Dangerous side effects

Operations such as:

- deletion;
- financial transaction;
- deployment;
- external publication;
- process termination

can require explicit policy/approval.

---

# 55. Tool sandbox

Tool implementation may run:

- in-process;
- isolated module;
- subprocess;
- remote service.

---

# 56. Tool isolation

623/603 manage module/process isolation.

---

# 57. Remote tool

631 handles service invocation.

---

# 58. Tool transport

Supported:

```text id="k3jv0p"
InProcess
IPC
HTTP
RPC
Event
Workflow
```

---

# 59. Tool versioning

Tool schema version is immutable.

---

# 60. Tool compatibility

Agent definition records compatible tool schema.

---

# 61. Tool discovery

Agents may receive a predefined tool catalog.

Dynamic discovery requires explicit capability.

---

# 62. Tool discovery security

Model cannot arbitrarily discover privileged tools.

---

# 63. Tool result trust

Tool results remain data unless explicitly promoted by application policy.

---

# 64. Tool result size

Bounded by resource policy.

---

# 65. Tool streaming

Long-running tools can stream partial results.

---

# 66. Tool cancellation

Cancellation propagates through 607/631/629.

---

# 67. Planner

Planner creates candidate execution plan.

---

# 68. Planner output

```text id="ap2r7k"
Plan {
    steps
    dependencies
    conditions
    resource_estimate
}
```

---

# 69. Plan != execution

Plan is data.

It must pass validation/admission before execution.

---

# 70. Plan validation

Checks:

- known tool;
- valid arguments;
- dependencies;
- capability requirements;
- policy;
- resource budget;
- cycle;
- deadline.

---

# 71. Plan cycles

Static cycle detection where possible.

---

# 72. Plan execution

Valid plan becomes execution steps.

---

# 73. Planner providers

```text id="3x0y3b"
ModelPlanner
RulePlanner
WorkflowPlanner
ApplicationPlanner
```

---

# 74. No mandatory autonomous planning algorithm

Application chooses planner.

---

# 75. Deterministic planner

Rule-based planner can be fully deterministic.

---

# 76. Model planner

LLM-generated plans are untrusted until validated.

---

# 77. Plan repair

Invalid plan can be rejected or regenerated.

---

# 78. Planning budget

Planner has:

```text id="h9x6a5"
max_steps
max_depth
max_tokens
max_time
```

---

# 79. Recursive planning

Nested planning depth bounded.

---

# 80. Agent loop

Canonical loop:

```text id="qprm0w"
Observe
→ Context
→ Generate
→ Parse
→ Validate
→ Plan
→ Admit
→ Execute
→ Observe
→ Repeat
```

---

# 81. Loop limit

Agent run has:

```text id="s9u1w0"
max_steps
max_tool_calls
max_time
max_model_calls
```

---

# 82. Infinite-loop prevention

Runtime terminates execution when limits are exceeded.

---

# 83. Repeated tool detection

Optional duplicate-call detection.

---

# 84. Tool-call budget

Can be per:

- run;
- session;
- agent;
- tenant;
- tool.

---

# 85. Model-call budget

Same hierarchy.

---

# 86. Context budget

Independent from compute budget.

---

# 87. Token budget

Model provider reports estimated/actual usage where available.

---

# 88. Model abstraction

644 consumes 643:

```text id="y0t1p5"
InferenceSession
ModelRequest
ModelResponse
```

---

# 89. Model provider

```text id="8h0b4y"
LocalModelProvider
NativeModelProvider
RemoteModelProvider
ExternalProvider
TestProvider
```

---

# 90. Model neutrality

Agent runtime does not depend on a specific model vendor.

---

# 91. Generation configuration

```text id="v8x3l5"
temperature
top_k
top_p
max_tokens
stop
seed
structured_schema
```

---

# 92. Deterministic generation

If provider supports seed/deterministic mode.

---

# 93. Model streaming

Partial tokens/chunks are delivered as events.

---

# 94. Streaming cancellation

Client cancellation propagates immediately.

---

# 95. Backpressure

Streaming output uses 607/634 backpressure.

---

# 96. Model error

```text id="2ey5e9"
ModelUnavailable
ModelTimeout
ContextOverflow
InvalidRequest
ProviderError
RateLimited
ResourceExceeded
```

---

# 97. Model fallback

Fallback provider is explicit.

---

# 98. Fallback policy

Must specify whether:

- different model;
- different device;
- remote service

is permitted.

---

# 99. No silent provider change

Provider changes are recorded.

---

# 100. Retrieval

Retriever is an abstraction above 641.

```text id="w8a8n3"
Retriever {
    query
    filters
    limits
}
```

---

# 101. Retrieval sources

```text id="7sp7pl"
FullText
Vector
Hybrid
Database
Analytics
Document
Memory
Remote
```

---

# 102. Retrieval query

```text id="w7x5l4"
RetrievalQuery {
    text
    embedding
    filters
    top_k
    threshold
}
```

---

# 103. Retrieval result

```text id="s8q6bb"
RetrievedDocument {
    id
    content
    score
    source
    metadata
    provenance
}
```

---

# 104. Retrieval provenance

Every result records source/index revision where available.

---

# 105. RAG pipeline

```text id="d2q6go"
Question
→ QueryTransform
→ Retrieval
→ Filter
→ Rerank
→ Context
→ Model
```

---

# 106. Query transform

Optional model-generated query must be bounded and validated.

---

# 107. Reranking

Uses 641 rank primitives or 643 model.

---

# 108. Reranker

Separate from generator.

---

# 109. Retrieval filters

639/640 policies are applied before exposing content.

---

# 110. Retrieval security

Agent cannot retrieve data outside its capabilities.

---

# 111. Retrieval governance

640 determines:

- classification;
- residency;
- retention;
- lineage;
- purpose.

---

# 112. Citation

RAG responses may contain structured citations.

```text id="9xg4s4"
Citation {
    source_id
    revision
    location
}
```

---

# 113. Citation validation

Citation must correspond to retrieved source.

---

# 114. No fabricated citation

Runtime must not mark arbitrary model text as verified citation.

---

# 115. Memory

Memory is persistent information associated with agent/application.

---

# 116. Memory types

```text id="g3tq1d"
WorkingMemory
ConversationMemory
SemanticMemory
EpisodicMemory
ProceduralMemory
PreferenceMemory
ApplicationMemory
```

---

# 117. Working memory

Short-lived context.

---

# 118. Conversation memory

Historical messages.

---

# 119. Semantic memory

Facts/knowledge represented as structured records or embeddings.

---

# 120. Episodic memory

Records previous execution episodes.

---

# 121. Procedural memory

Stores reusable procedures/templates, not executable native code.

---

# 122. Preference memory

Application-defined user preferences.

---

# 123. Memory store

```text id="09q3xh"
MemoryStore {
    write
    query
    delete
    compact
}
```

---

# 124. Memory backend

Can use:

- 611;
- 612;
- 628;
- 641;
- 642.

---

# 125. Memory schema

Memory items are typed.

---

# 126. Memory provenance

Every memory item records origin.

---

# 127. Memory confidence

Optional metadata, never treated as proof.

---

# 128. Memory freshness

Memory can have:

```text id="z8a4g5"
created_at
updated_at
expires_at
source_revision
```

---

# 129. Memory conflict

Conflicting memories are represented explicitly.

---

# 130. Memory overwrite

Does not silently destroy provenance.

---

# 131. Memory deletion

Uses 640 retention/deletion semantics.

---

# 132. Memory classification

Memory can contain sensitive data and therefore carries governance metadata.

---

# 133. Memory residency

Distributed memory follows residency restrictions.

---

# 134. Memory retrieval

Memory query may combine:

```text id="h6s2yl"
semantic
lexical
structured
temporal
```

---

# 135. Memory ranking

Ranking is deterministic/configurable.

---

# 136. Memory compaction

Old memories can be summarized into derived memory.

---

# 137. Summary provenance

Summary stores source memory references.

---

# 138. Memory hallucination boundary

Model-generated memory is marked:

```text id="zv1n4p"
ModelDerived
```

until application verification if required.

---

# 139. Memory write policy

Agent cannot automatically persist every model claim.

---

# 140. Memory admission

Policy can require:

```text id="d4x8v5"
SourceVerified
UserConfirmed
ApplicationApproved
```

---

# 141. Agent state

State contains:

```text id="0s8z7r"
session
step
context references
plan
tool state
memory references
model state
budgets
```

---

# 142. Agent state persistence

Uses 600/611/612.

---

# 143. Agent checkpoint

```text id="4f4f8b"
AgentCheckpoint {
    run
    state
    context_revision
    plan_revision
    tool_state
    memory_revision
}
```

---

# 144. Secret exclusion

Checkpoint cannot contain plaintext secrets.

---

# 145. Resume

Agent can resume from checkpoint.

---

# 146. Tool recovery

Tool calls in progress are marked:

```text id="h9v8f0"
Unknown
```

unless provider has durable execution semantics.

---

# 147. Side-effect recovery

Non-idempotent tool calls require idempotency/confirmation before retry.

---

# 148. Durable agent

Long-running agent delegates durable waiting/execution to 629.

---

# 149. Agent workflow

644 can compile an agent loop into 629 workflow/activity primitives.

---

# 150. Agent event stream

634 emits:

```text id="0j3x7n"
AgentStarted
ModelRequested
ModelCompleted
ToolRequested
ToolCompleted
RetrievalPerformed
PlanCreated
PlanRejected
MemoryRead
MemoryWritten
AgentCompleted
AgentFailed
```

---

# 151. Event payload

Never contains secrets unless explicitly permitted.

---

# 152. Observability

633 captures:

- model latency;
- tool latency;
- retrieval latency;
- context size;
- token usage;
- step count;
- memory operations;
- plan depth.

---

# 153. Trace hierarchy

```text id="v4d8xk"
AgentRun
 ├─ ModelSpan
 ├─ RetrievalSpan
 ├─ PlanningSpan
 └─ ToolSpan
```

---

# 154. Explainability

Runtime exposes execution trace.

---

# 155. Agent explain API

```text id="j4p5me"
agent.explain(run_id)
```

returns structured execution metadata.

---

# 156. Explain limitation

It describes runtime events, not hidden model reasoning.

---

# 157. No hidden chain-of-thought storage

Runtime stores:

- prompts;
- outputs;
- tool calls;
- decisions represented by explicit state;

not private internal model reasoning.

---

# 158. Prompt template

```text id="5b3f4a"
PromptTemplate {
    segments
    variables
    schema
}
```

---

# 159. Template rendering

Variables are typed.

---

# 160. Template injection prevention

Structured values are encoded according to context.

---

# 161. Prompt fingerprint

Rendered prompt can have deterministic fingerprint.

---

# 162. Context fingerprint

Hash of selected context revisions.

---

# 163. Agent run fingerprint

Combines:

```text id="6y7f4u"
agent_version
model_version
prompt_fingerprint
tool_schema
context_revision
```

---

# 164. Reproducibility

A run can be reproduced when all required provider states are available.

---

# 165. Tool result replay

Testing runtime can replay recorded tool outputs.

---

# 166. Model replay

Provider may support deterministic response replay.

---

# 167. Simulation mode

Agent executes against fake tools/models/retrievers.

---

# 168. Dry-run mode

Tool calls are validated but side effects are not executed.

---

# 169. Approval mode

Tool call pauses until approval.

---

# 170. Observe-only mode

Agent may generate plans but not execute them.

---

# 171. Policy mode

639 controls allowed execution modes.

---

# 172. Agent capability profile

```text id="j0r0s3"
ReadOnly
Interactive
Automation
Privileged
Sandboxed
```

These are descriptive policy profiles, not capability grants themselves.

---

# 173. Tool groups

Tools can be grouped:

```text id="a3v7ns"
filesystem
network
database
process
deployment
communication
AI
```

---

# 174. Tool allowlist

Agent definition can explicitly list allowed tools.

---

# 175. Tool denylist

Policy can deny tools even if agent declares them.

---

# 176. Capability inheritance

Agent → tool execution gets attenuated capabilities.

---

# 177. Capability expiration

Long-running agent capability grants may expire.

---

# 178. Agent delegation

Agent can invoke another agent only through explicit service/tool interface.

---

# 179. Agent-to-agent call

Uses 631 service identity and 603 capabilities.

---

# 180. Multi-agent runtime

```text id="z6n2eu"
AgentCoordinator
AgentPool
AgentMessage
AgentTask
```

---

# 181. Agent roles

Roles are application-defined metadata.

---

# 182. Agent communication

Can use:

- direct call;
- IPC;
- service RPC;
- event;
- workflow.

---

# 183. Shared memory

Agents must not share mutable state implicitly.

---

# 184. Shared state

Uses 628 with explicit consistency.

---

# 185. Multi-agent coordination

629/635 can coordinate durable/distributed execution.

---

# 186. Agent hierarchy

Parent agent may create child execution with reduced budgets/capabilities.

---

# 187. Child budget

Child receives:

```text id="z0k0eq"
remaining_time
remaining_steps
remaining_tokens
remaining_resource_budget
```

---

# 188. No budget amplification

Children cannot increase parent authority.

---

# 189. Cancellation propagation

Parent cancellation propagates to child unless explicitly detached by policy.

---

# 190. Detached agents

Must be explicitly declared.

---

# 191. Detached agent

Gets independent lifecycle and resource budget.

---

# 192. Agent scheduling

607.

---

# 193. Distributed agent placement

630/635.

---

# 194. Edge agent

636.

---

# 195. Agent deployment

636 can deploy agent package/model/tools.

---

# 196. Agent package

613/625 includes:

```text id="8h4q5w"
agent definition
prompt templates
tool schemas
model references
retriever configuration
memory schema
policy metadata
```

---

# 197. Agent package security

Signed package required for trusted distribution.

---

# 198. Agent update

636 can rollout new agent version.

---

# 199. Agent rollback

Previous immutable generation restored.

---

# 200. Agent configuration

637 controls operational configuration.

---

# 201. Security policy

603/639 remains authoritative.

---

# 202. Dynamic tool configuration

637 may enable/disable declared tools, but cannot grant forbidden capability.

---

# 203. Agent policy

639 may impose:

```text id="q1x8v6"
max_steps
allowed_tools
allowed_models
allowed_regions
approval_required
```

---

# 204. Data governance

640 controls:

- memory;
- retrieval;
- prompts;
- tool inputs;
- model outputs;
- generated artifacts.

---

# 205. Data minimization

Only required context should be sent to model.

---

# 206. Context filtering

Sensitive fields can be removed/masked before model invocation.

---

# 207. Secret redaction

Credentials are never inserted into ordinary model context unless explicit secret-capable provider is used.

---

# 208. Secret-capable provider

Requires special capability and policy.

---

# 209. Prompt logging

Sensitive prompts can be excluded from telemetry.

---

# 210. Tool logging

Arguments may be redacted according to schema.

---

# 211. Structured secret fields

Schema can mark:

```text id="d9r7vh"
@secret
```

---

# 212. Model output classification

Outputs can be classified by policy.

---

# 213. Generated content provenance

Generated artifact references:

```text id="w0o6b8"
agent_run
model_version
prompt_revision
source_context
```

---

# 214. Generated code

If an agent generates code, it remains data until explicitly compiled/executed through authorized tooling.

---

# 215. Generated commands

Shell/process commands are never executed directly from model text.

---

# 216. Command tool

Execution must pass explicit tool schema and capability policy.

---

# 217. File operations

Agent receives scoped filesystem capability.

---

# 218. Network operations

Agent receives scoped network capability.

---

# 219. Database operations

Agent receives scoped data capability.

---

# 220. Deployment operations

Agent requires deployment capability + 639 admission.

---

# 221. Human approval

High-impact operations may require approval.

---

# 222. Approval binding

Approval binds:

```text id="v7x0zz"
agent_run
tool
arguments_hash
resource
policy_revision
expiry
```

---

# 223. Approval reuse

Approval cannot automatically be reused for different arguments.

---

# 224. Prompt injection protection

Runtime cannot perfectly determine malicious natural-language content.

Therefore security boundary is enforced structurally:

```text id="f7j5te"
model output
     ↓
typed parser
     ↓
schema validation
     ↓
capability check
     ↓
policy
     ↓
execution
```

---

# 225. Retrieved instruction

Retrieved documents are untrusted unless application explicitly promotes them.

---

# 226. Tool result instruction

Tool output is data unless schema explicitly defines an instruction channel.

---

# 227. Memory instruction

Memory is data unless explicitly classified as application policy.

---

# 228. Agent-generated policy

Agent cannot modify 603/639 policy directly.

---

# 229. Agent-generated configuration

637 changes require policy-controlled mutation.

---

# 230. Model-generated tool selection

Tool selection is a request, not an authorization.

---

# 231. Tool execution authority

Authorization comes from 603/639.

---

# 232. Retrieval authority

Authorization comes from 603/639/640.

---

# 233. Model authority

Model cannot invoke arbitrary providers.

---

# 234. Model provider policy

Allowed providers are declared.

---

# 235. Cost/resource control

Agent runtime tracks:

```text id="j1x0cz"
model calls
tokens
tool calls
CPU
memory
GPU
network
storage
```

---

# 236. Budget exhaustion

Agent terminates or enters controlled recovery.

---

# 237. Budget warning

Threshold events emitted before hard limit.

---

# 238. Agent quota

606 can enforce tenant/application/agent quotas.

---

# 239. Fairness

Scheduler integration prevents one agent from monopolizing workers.

---

# 240. Backpressure

Model/tool/retrieval queues propagate backpressure.

---

# 241. Concurrency

Agent may execute independent tools in parallel when plan explicitly permits.

---

# 242. Parallel tool execution

Requires independent side effects or explicit safety declaration.

---

# 243. Dependency graph

Parallel plan steps use DAG.

---

# 244. Tool race prevention

Shared mutable resources require synchronization.

---

# 245. Transactional tools

Tools may expose transaction handles.

---

# 246. Tool compensation

Long-running side effects can integrate with 629 Saga compensation.

---

# 247. Durable agent execution

Agent waits become durable timers in 629.

---

# 248. Agent event sourcing

Important state transitions can be recorded via 634/628.

---

# 249. Agent state snapshot

600/612.

---

# 250. Recovery

On runtime restart:

```text id="e2y0o5"
load checkpoint
→ validate generation
→ reconstruct state
→ recover pending operations
→ resume
```

---

# 251. Crash recovery

No duplicated non-idempotent side effects.

---

# 252. Idempotency

Tool calls receive idempotency key when supported.

---

# 253. Idempotency key

Derived from:

```text id="k7f2d1"
agent_run
step
tool_call
```

---

# 254. Exactly-once claim

Runtime does not claim exactly-once side effects.

---

# 255. At-least-once

Durable tools default to at-least-once unless stronger semantics are explicitly provided.

---

# 256. Agent memory consistency

Memory operations specify consistency level.

---

# 257. Conversation consistency

Session memory defaults to session consistency.

---

# 258. Distributed memory

Can use causal/quorum semantics from 628.

---

# 259. Agent event ordering

Events carry sequence/generation.

---

# 260. Agent trace

633 integrates trace context.

---

# 261. Agent metrics

Core metrics:

```text id="o7n8s9"
run_count
success_count
failure_count
step_count
model_calls
tool_calls
retrieval_calls
latency
token_usage
resource_usage
```

---

# 262. Quality metrics

Application-defined.

Runtime does not declare an automatic quality winner.

---

# 263. Evaluation

Agent evaluation can compare runs against declared test datasets.

---

# 264. Evaluation dataset

Uses 643 Dataset.

---

# 265. Evaluation metrics

Can include:

- exact match;
- structured validity;
- retrieval recall;
- task success;
- latency;
- resource usage.

---

# 266. Evaluation reproducibility

Run references model/agent/tool/data versions.

---

# 267. Agent test harness

```text id="7q7g4e"
AgentTest
MockModel
MockTool
MockRetriever
ReplayStore
```

---

# 268. Tool fuzzing

Invalid model-generated arguments are fuzz-tested.

---

# 269. Context fuzzing

Oversized/malformed context must fail safely.

---

# 270. Plan fuzzing

Malformed plans cannot execute.

---

# 271. Prompt template tests

Missing variables produce compile/runtime errors.

---

# 272. Structured output tests

Schema mismatch is detected.

---

# 273. Retrieval tests

Verify:

- filters;
- permissions;
- provenance;
- stale index behavior.

---

# 274. Memory tests

Verify:

- versioning;
- deletion;
- retention;
- conflicts;
- provenance.

---

# 275. Security tests

Verify:

- capability attenuation;
- tool denial;
- prompt injection boundary;
- secret redaction;
- cross-tenant isolation.

---

# 276. Resource tests

Verify:

- token limits;
- step limits;
- tool limits;
- GPU limits;
- memory limits;
- timeout.

---

# 277. Failure injection

Simulate:

- model timeout;
- tool crash;
- network failure;
- retriever failure;
- checkpoint corruption;
- worker loss.

---

# 278. Recovery tests

Verify deterministic recovery where declared.

---

# 279. Distributed tests

Simulate multi-agent/node failures.

---

# 280. Performance tests

Benchmark:

- context assembly;
- schema validation;
- tool dispatch;
- retrieval;
- memory;
- model invocation;
- scheduling.

---

# 281. Context assembly performance

Use immutable references and zero-copy where possible.

---

# 282. Tool dispatch performance

In-process tools avoid serialization when security boundary allows.

---

# 283. Remote tool performance

Use connection pooling from 609/631.

---

# 284. Retrieval performance

641 handles indexing/query execution.

---

# 285. Memory performance

Hot memory can use local cache; persistent memory uses 628/611.

---

# 286. Agent state allocation

Small state objects should avoid unnecessary heap allocations.

---

# 287. Native ABI

Tool providers expose stable ABI.

---

# 288. Compiler integration

Compiler can statically generate:

- tool schema;
- structured-output schema;
- agent manifest;
- context schema;
- memory schema.

---

# 289. Compiler annotations

```text id="5z5w2r"
@agent
@model
@tool
@tool_input
@tool_output
@retriever
@memory
@context
@prompt
@plan
@step
@approval
@capability
@agent_state
@agent_checkpoint
@model_server
```

---

# 290. Generated metadata

```text id="a5b8h7"
.axagent
.axtool
.axcontext
.axmemory
.axprompt
.axplan
.axagentstate
.axagentdeploy
```

---

# 291. Agent definition example

```text id="9f5a1x"
struct ResearchAgent {
    model: ModelRef
    retriever: Retriever
    tools: ToolSet
    memory: MemoryStore
}

fn run(
    self: ResearchAgent,
    question: String
) -> AgentResult {
    ...
}
```

---

# 292. Tool definition example

```text id="0g6z2p"
struct SearchTool {}

fn execute(
    self: SearchTool,
    input: SearchInput
) -> SearchOutput {
    ...
}
```

---

# 293. Structured schema

```text id="9k1zq2"
struct Answer {
    summary: String
    citations: List<Citation>
}
```

Model output can target `Answer`.

---

# 294. Typed tool invocation

Compiler can generate:

```text id="p3j4l7"
tool.call<SearchInput, SearchOutput>()
```

---

# 295. Agent state typing

Application-defined agent state is strongly typed.

---

# 296. Model output parser

Parser converts provider response to typed value.

---

# 297. Invalid output

Never silently coerced into a different schema.

---

# 298. Prompt DSL

Optional syntax:

```text id="m7h3n5"
prompt {
    system(...)
    context(...)
    user(...)
}
```

---

# 299. Prompt DSL compilation

Produces typed context graph.

---

# 300. Agent DSL

Optional:

```text id="v4q6r8"
agent Researcher {
    model ...
    tools ...
    memory ...
    policy ...
}
```

---

# 301. DSL status

Convenience syntax only; runtime APIs remain canonical.

---

# 302. RAG DSL

Optional declarative pipeline:

```text id="1f6m3k"
retrieve
→ filter
→ rerank
→ context
→ generate
```

---

# 303. Planner DSL

Can describe deterministic planning constraints.

---

# 304. Workflow integration

Agent can invoke workflow:

```text id="4w7v2q"
agent
→ workflow
→ activities
→ result
```

---

# 305. Agent as workflow activity

An agent run can itself be a 629 activity.

---

# 306. Workflow as agent tool

Workflow can be exposed as typed tool.

---

# 307. Event-driven agent

634 can trigger agent runs.

---

# 308. Scheduled agent

629 can schedule agent execution.

---

# 309. Service agent

631 exposes agent through service interface.

---

# 310. Gateway agent

632 exposes external API.

---

# 311. Deployment

636 manages rollout.

---

# 312. Model deployment

643 model lifecycle remains independent from agent lifecycle.

---

# 313. Agent/model compatibility

Agent version declares supported model signature.

---

# 314. Tool/model compatibility

Tool schema is independent from model vendor.

---

# 315. Provider abstraction

Core interfaces:

```text id="l4y8t2"
ModelProvider
ToolProvider
RetrieverProvider
MemoryProvider
PlannerProvider
EmbeddingProvider
```

---

# 316. Native provider

Axiom can implement provider entirely in native code.

---

# 317. External provider

Third-party provider can be plugged in with capability boundary.

---

# 318. Provider failure isolation

Failure of external provider must not corrupt agent state.

---

# 319. Provider timeout

All external calls bounded.

---

# 320. Provider authentication

638/610.

---

# 321. Provider secrets

Never stored in agent definition.

---

# 322. Provider configuration

601/637 stores references/configuration.

---

# 323. Agent package portability

An agent package declares provider requirements.

---

# 324. Local portability

If all providers available locally, agent can run offline.

---

# 325. Remote model portability

Model endpoint can be replaced by another compatible provider subject to policy.

---

# 326. Provider capability mismatch

Activation fails before serving.

---

# 327. Agent startup

Validate:

1. model;
2. tools;
3. schemas;
4. policies;
5. memory;
6. retriever;
7. resource budget.

---

# 328. Atomic agent activation

Only fully validated generation becomes active.

---

# 329. Agent hot reload

623 manages definition generation.

---

# 330. Hot reload safety

Running sessions remain bound to their original generation unless explicit migration is supported.

---

# 331. Agent migration

State migration requires schema compatibility.

---

# 332. Memory migration

Memory schema changes use 612 migration mechanisms.

---

# 333. Context migration

Context schema versioned.

---

# 334. Tool migration

Tool schema changes require compatibility check.

---

# 335. Model migration

643 model signature compatibility required.

---

# 336. Agent rollback

New sessions use old generation after rollback.

---

# 337. Existing sessions

Policy determines whether they drain or continue.

---

# 338. Agent draining

No new runs; existing runs complete or timeout.

---

# 339. Multi-version serving

Multiple agent generations may coexist.

---

# 340. Tenant isolation

Each tenant can have independent:

- agent;
- model;
- tools;
- memory;
- quotas.

---

# 341. Cross-tenant memory

Forbidden by default.

---

# 342. Cross-tenant tool execution

Forbidden unless explicit capability.

---

# 343. Cross-tenant retrieval

Policy-controlled.

---

# 344. Audit

Every privileged action is auditable.

---

# 345. Audit fields

```text id="1q7y8m"
agent
run
tenant
tool
resource
decision
policy_revision
timestamp
```

---

# 346. Privacy

Telemetry may redact:

- prompt;
- user content;
- tool arguments;
- memory;
- model output.

---

# 347. Retention

Agent traces obey 640.

---

# 348. Data deletion

Deleting user data must propagate to governed memory/retrieval caches where applicable.

---

# 349. Derived memory deletion

Derived summaries/embeddings must be considered in deletion lineage.

---

# 350. Vector memory

Memory embeddings can be indexed by 641.

---

# 351. Embedding model identity

Every embedding records model/version.

---

# 352. Embedding invalidation

Changing embedding model can require rebuilding vector memory.

---

# 353. Hybrid memory retrieval

Lexical + vector + structured filters.

---

# 354. Temporal retrieval

Memory queries may filter by time.

---

# 355. Recency weighting

Explicit ranking policy.

---

# 356. Semantic similarity

Uses 641 vector search.

---

# 357. Memory deduplication

Can deduplicate by content/provenance hash.

---

# 358. Memory conflict resolution

Does not silently discard conflicting facts.

---

# 359. Memory consolidation

Application-defined deterministic process or model-assisted process.

---

# 360. Model-assisted consolidation

Generated result marked as derived.

---

# 361. Agent self-modification

Agent cannot modify its own executable/runtime capabilities.

---

# 362. Agent definition mutation

Requires external authorized configuration/deployment operation.

---

# 363. Tool creation

Agent may generate a tool specification, but installation requires authorization.

---

# 364. Dynamic code

Generated code requires explicit compiler/tool execution capability.

---

# 365. Plugin installation

623 policy applies.

---

# 366. Package installation

625/639.

---

# 367. Deployment changes

636/639.

---

# 368. Security boundary

644 is never an authority root.

---

# 369. AI-specific capability

Optional:

```text id="9m2q4s"
Capability<ModelInference>
Capability<ToolInvoke<T>>
Capability<MemoryRead>
Capability<MemoryWrite>
Capability<Retrieve>
Capability<AgentSpawn>
```

---

# 370. Capability parameterization

Capabilities can be scoped to:

- model;
- tool;
- dataset;
- tenant;
- region;
- resource;
- time.

---

# 371. Capability attenuation

Child agents inherit reduced capability.

---

# 372. Agent spawn

`AgentSpawn` capability required.

---

# 373. Agent recursion

Maximum nesting depth enforced.

---

# 374. Multi-agent budget

Parent budget limits aggregate child execution.

---

# 375. Agent communication budget

606 controls message/IPC resources.

---

# 376. Agent topology

631/635 can place agents.

---

# 377. Agent locality

Memory/model/data locality can influence placement.

---

# 378. Placement constraint

635 receives:

```text id="e8q3b4"
model_device
data_residency
memory_size
accelerator
latency
```

requirements.

---

# 379. Edge locality

636 can place agent near data source.

---

# 380. Offline mode

Agent can operate with:

- local model;
- local tools;
- local memory;
- local package.

---

# 381. Degraded mode

If model unavailable, runtime can enter:

```text id="3m6n7p"
ReadOnly
Deferred
Fallback
```

according to policy.

---

# 382. No unsafe fallback

A fallback provider cannot automatically receive broader data/capability.

---

# 383. Human-in-the-loop

Approval tool integrates with GUI 619 or external service 631.

---

# 384. Human task

Can become 629 durable human activity.

---

# 385. Agent waiting

Durable wait uses 629 timer/signal.

---

# 386. External event resume

634 event can resume agent.

---

# 387. Agent state event

Event carries checkpoint reference rather than huge state.

---

# 388. Large context

Large documents remain in storage; context contains references/chunks.

---

# 389. Zero-copy context

Where possible, model provider consumes memory-mapped/owned buffers.

---

# 390. Context chunking

Chunking is application/provider policy.

---

# 391. Retrieval chunk identity

Every chunk has source revision and position.

---

# 392. Citation location

Citation can identify:

- document;
- chunk;
- byte/character range;
- page;
- record.

---

# 393. Document processing

617/641/642 provide text extraction/indexing.

---

# 394. OCR

Optional 616/AI provider.

---

# 395. Image retrieval

641 can support multimodal embeddings through provider.

---

# 396. Multimodal RAG

Retrieval result may reference:

```text id="5p8c2w"
text
image
audio
video
table
```

---

# 397. Multimodal context

644 packages references/data according to model signature.

---

# 398. Context modality validation

Model signature determines supported modality.

---

# 399. Structured generation

Supports:

```text id="k8w5x2"
JSON-like
AXBIN
Axiom struct
enum
union
array
```

---

# 400. Native structured decoding

Provider may constrain generation to schema.

---

# 401. Post-generation validation

Always performed when structured output requested.

---

# 402. Schema version

Structured schema fingerprint recorded in run.

---

# 403. Tool schema fingerprint

Recorded in run.

---

# 404. Agent reproducibility fingerprint

Includes all relevant schemas and versions.

---

# 405. Agent artifact

Native package:

```text id="a0b9c2"
AXAGENT
```

---

# 406. AXAGENT format

```text id="u7j4n9"
Header
AgentSchema
ModelReferences
ToolSchemas
MemorySchema
PromptTemplates
PolicyMetadata
ResourceRequirements
Checksums
```

---

# 407. No executable model code

AXAGENT contains references/artifacts, not hidden native execution payloads.

---

# 408. Package signature

638.

---

# 409. Agent registry

625 may distribute AXAGENT packages.

---

# 410. Agent version registry

Immutable versions.

---

# 411. Agent revocation

Revoked generation cannot start new runs.

---

# 412. Active sessions after revocation

Policy determines drain/cancel.

---

# 413. Model revocation

643 model generation becomes unavailable.

---

# 414. Tool revocation

603/639 can deny execution immediately.

---

# 415. Emergency kill switch

637 can disable agent/tool generation within policy bounds.

---

# 416. Kill switch semantics

Existing side effects are not magically rolled back.

---

# 417. Recovery

629 compensation may be used where defined.

---

# 418. Agent event retention

Controlled by 640.

---

# 419. Memory retention

Controlled by 640.

---

# 420. Prompt retention

Controlled by 640.

---

# 421. Tool-result retention

Controlled by 640.

---

# 422. Model telemetry retention

633 + 640.

---

# 423. Resource governor integration

606 enforces:

- CPU;
- memory;
- GPU;
- network;
- storage;
- concurrency.

---

# 424. Scheduler integration

607 handles local agent tasks.

---

# 425. Distributed compute

630 handles remote execution.

---

# 426. Cluster placement

635.

---

# 427. Deployment

636.

---

# 428. Dynamic configuration

637.

---

# 429. Trust lifecycle

638.

---

# 430. Policy

639.

---

# 431. Data governance

640.

---

# 432. Search

641.

---

# 433. Analytics

642.

---

# 434. Model execution

643.

---

# 435. Final architecture

```text id="f6n9r3"
                         Axiom AI Application
                                  │
                                  ▼
                           ┌──────────────┐
                           │ AgentRuntime │
                           └──────┬───────┘
                                  │
          ┌───────────────────────┼───────────────────────┐
          ▼                       ▼                       ▼
      Context                  Planner                 Memory
          │                       │                       │
          │                       ▼                       ▼
          │                    Plan DAG               628/641
          │                       │
          └──────────────┬────────┘
                         ▼
                  Policy / Admission
                       603/639
                         │
               ┌─────────┼─────────┐
               ▼         ▼         ▼
             Model      Tool    Retrieval
             643        Runtime    641
               │         │         │
               └─────────┼─────────┘
                         ▼
                    Agent State
                         │
          ┌──────────────┼──────────────┐
          ▼              ▼              ▼
        629            634            633
      Workflow         Events       Observability
          │
          ▼
        630/635
       Distributed
        Execution
```

---

# 436. Architecture invariants

1. Agent output is not authority.
2. Model output is not authority.
3. Retrieved text is not authority.
4. Memory is not authority.
5. Tool result is not authority.
6. Tool invocation requires authorization.
7. Tool arguments require schema validation.
8. Tool side effects require declared capability.
9. Capability cannot be created by model output.
10. Child agents cannot gain parent authority.
11. Agent loops are bounded.
12. Planner depth is bounded.
13. Tool calls are bounded.
14. Model calls are bounded.
15. Context size is bounded.
16. Resource consumption is bounded.
17. Agent state is generation-safe.
18. Durable state is checkpointable.
19. Non-idempotent side effects cannot be blindly retried.
20. Exactly-once side effects are never assumed.
21. Secrets are excluded from ordinary context.
22. Secrets are excluded from ordinary telemetry.
23. Structured outputs are schema-validated.
24. Tool schemas are versioned.
25. Model signatures are versioned.
26. Retrieval results carry provenance.
27. Citations reference actual retrieved data.
28. Memory provenance is preserved.
29. Memory deletion follows governance.
30. Model artifacts are immutable.
31. Agent artifacts are immutable.
32. Model loading cannot execute arbitrary code.
33. Tool providers have explicit trust boundaries.
34. External providers cannot bypass security.
35. Dynamic configuration cannot expand authority.
36. Policy remains authoritative.
37. Governance remains authoritative.
38. Residency restrictions apply to retrieval.
39. Residency restrictions apply to inference.
40. Classification restrictions apply to memory.
41. Model output cannot mutate policy.
42. Model output cannot install plugins.
43. Model output cannot install packages.
44. Model output cannot execute shell commands directly.
45. Generated code remains inert until explicitly authorized.
46. Agent recovery cannot duplicate protected side effects.
47. Agent deployment is generation-based.
48. Agent rollback uses immutable versions.
49. Multi-agent shared mutable state is explicit.
50. Distributed agent execution uses bounded leases.
51. Stale workers cannot commit state.
52. Agent telemetry is privacy-aware.
53. Agent runtime has no mandatory cloud dependency.
54. Agent runtime has no mandatory Python dependency.
55. Agent runtime has no mandatory external agent framework.
56. Local inference is first-class.
57. Remote inference is explicit.
58. RAG is compositional rather than magical.
59. Planning is separate from execution.
60. Security authority remains outside the model.

---

# 437. Acceptance criteria

Target: **≥500 acceptance criteria** covering:

- agent lifecycle;
- session;
- run;
- generation;
- context;
- context budgets;
- prompt construction;
- multimodal input;
- structured output;
- schema validation;
- tool discovery;
- tool schema;
- tool invocation;
- capability attenuation;
- tool approval;
- tool timeout;
- tool retry;
- idempotency;
- side-effect protection;
- planner;
- plan validation;
- plan execution;
- loop limits;
- model provider;
- streaming;
- cancellation;
- retrieval;
- hybrid retrieval;
- citations;
- provenance;
- memory;
- memory conflict;
- memory retention;
- memory deletion;
- vector memory;
- RAG;
- checkpoint;
- recovery;
- durable execution;
- workflow integration;
- event integration;
- distributed agents;
- multi-agent communication;
- model serving;
- deployment;
- rollback;
- security;
- governance;
- privacy;
- resource limits;
- observability;
- testing;
- fuzzing;
- deterministic replay;
- performance;
- package format;
- provider ABI.

---

# 438. Profiles

```text id="9f5j3c"
AXAGENT_NONE
AXAGENT_CONTEXT
AXAGENT_STRUCTURED
AXAGENT_TOOL
AXAGENT_RETRIEVAL
AXAGENT_MEMORY
AXAGENT_RAG
AXAGENT_PLANNING
AXAGENT_WORKFLOW
AXAGENT_MULTI
AXAGENT_DISTRIBUTED
AXAGENT_SERVING
AXAGENT_FULL
```

### `AXAGENT_CONTEXT`

Context/message runtime.

### `AXAGENT_TOOL`

Tool calling.

### `AXAGENT_RETRIEVAL`

RAG/retrieval.

### `AXAGENT_MEMORY`

Persistent memory.

### `AXAGENT_PLANNING`

Planning/execution.

### `AXAGENT_WORKFLOW`

Durable agents.

### `AXAGENT_DISTRIBUTED`

Multi-node/multi-agent.

### `AXAGENT_SERVING`

Production agent service.

### `AXAGENT_FULL`

Toàn bộ runtime.

---

# 439. Quan hệ 643 ↔ 644

Đây là ranh giới quan trọng:

```text
643
────────────────────────
Tensor
Model
Training
Inference
GPU
Autodiff
Quantization
Model compilation

644
────────────────────────
Agent
Context
Tool
Memory
Retrieval
Planning
RAG
Workflow
Multi-agent
```

Ví dụ:

```text
User
  │
  ▼
644 Agent
  │
  ├── 641 Search
  │
  ├── 643 Embedding
  │
  ├── 643 LLM inference
  │
  ├── Tool → 631 Service
  │
  └── Memory → 628 Data
```

---

# 440. Ý nghĩa đối với Axiom

Sau BOOTSTRAP-644, Axiom không chỉ có:

```text
language
compiler
runtime
database
network
graphics
GUI
distributed system
analytics
ML
```

mà còn có primitive native để xây dựng **AI applications**.

Một AI application điển hình có thể được biên dịch thành:

```text
Axiom source
     │
     ▼
Agent IR
     │
     ├── Model references
     ├── Tool schemas
     ├── Context graph
     ├── Retrieval graph
     ├── Memory graph
     ├── Policy metadata
     └── Resource metadata
     │
     ▼
Native Agent Runtime
     │
     ├── CPU
     ├── GPU
     ├── local storage
     ├── network
     └── distributed services
```

Không cần tạo một ngôn ngữ scripting riêng chỉ để xây agent.

---

# 441. Trạng thái

**BOOTSTRAP-644 — COMPLETE**

Task tiếp theo:

**BOOTSTRAP-645 — Native AI Knowledge Graph, Semantic Graph, Entity Resolution, Ontology, Graph Query, Graph Analytics & Knowledge Runtime 5.0**
:::