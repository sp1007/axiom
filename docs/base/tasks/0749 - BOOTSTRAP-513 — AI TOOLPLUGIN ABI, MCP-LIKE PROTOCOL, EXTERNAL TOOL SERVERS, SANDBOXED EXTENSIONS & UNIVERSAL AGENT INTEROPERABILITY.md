# BOOTSTRAP-513 — AI TOOL/PLUGIN ABI, MCP-LIKE PROTOCOL, EXTERNAL TOOL SERVERS, SANDBOXED EXTENSIONS & UNIVERSAL AGENT INTEROPERABILITY

**Trạng thái: COMPLETED / LOCKED**

513 chuẩn hóa tầng giao tiếp giữa **Axiom Agent 511** và thế giới bên ngoài. Mục tiêu là Axiom có thể dùng tool nội bộ, plugin native, WASM, process riêng, remote service hoặc giao thức kiểu MCP mà **không khóa ngôn ngữ vào một giao thức AI cụ thể**.

```text id="513arch"
                    Axiom Agent 511
                          │
                    Tool Registry
                          │
              ┌───────────┼────────────┐
              ↓           ↓            ↓
        Native Tool     WASM Tool    Remote Tool
              │           │            │
              └───────────┼────────────┘
                          ↓
                   Tool Protocol
                          │
              ┌───────────┼────────────┐
              ↓           ↓            ↓
            Local       Process       Network
              │           │            │
              └───────────┼────────────┘
                          ↓
                 Capability Boundary
                          ↓
                    Tool Execution
                          ↓
                  Typed Observation
                          ↓
                    Agent 511
```

---

## 513.1 — Tool ABI ≠ Tool Protocol

Hai tầng phải độc lập:

```text
Tool ABI
    ↓
Binary / in-process interoperability

Tool Protocol
    ↓
Process / network interoperability
```

## 513.2 — Native Tool ABI

Native tool có ABI version:

```text
ToolAbiVersion {
    major
    minor
}
```

## 513.3 — Stable tool descriptor

Mỗi tool export descriptor:

```text
ToolDescriptor {
    id
    version
    input_schema
    output_schema
    effects
    capabilities
}
```

## 513.4 — ABI-independent schema

Tool schema không được phụ thuộc layout native nếu tool chạy remote.

## 513.5 — Schema types

Schema hỗ trợ:

- bool;
- integer;
- float;
- string;
- bytes;
- array;
- object;
- enum;
- optional;
- union.

## 513.6 — Schema identity

Schema có canonical representation + hash.

## 513.7 — Input validation

Input phải validate trước invocation.

## 513.8 — Output validation

Output từ external tool phải validate trước khi trở thành typed value.

## 513.9 — Version negotiation

Client/server negotiate protocol capabilities.

## 513.10 — Unknown fields

Protocol có thể cho phép unknown fields để forward compatibility.

---

# TOOL PROTOCOL

## 513.11 — Transport-independent protocol

Protocol semantics độc lập transport.

Supported transports:

```text
stdio
pipe
socket
HTTP
WebSocket
IPC
custom
```

## 513.12 — Request

```text
ToolRequest {
    request_id
    tool_id
    arguments
    deadline
    cancellation
}
```

## 513.13 — Response

```text
ToolResponse {
    request_id
    status
    result
    error
    metadata
}
```

## 513.14 — Request identity

`request_id` phải unique trong protocol session.

## 513.15 — Correlation

Response phải correlate được với request.

## 513.16 — Notification

One-way notification được hỗ trợ.

## 513.17 — Streaming

Tool có thể trả streaming results.

## 513.18 — Partial results

Partial result semantics phải explicit.

## 513.19 — Completion

Stream completion phải distinguish:

```text
completed
cancelled
failed
```

## 513.20 — Error

Protocol errors là typed structured data.

---

# TOOL DISCOVERY

## 513.21 — Tool discovery

Client có thể query available tools.

## 513.22 — Tool metadata

Discovery trả:

- ID;
- version;
- description;
- schema;
- effects;
- capabilities.

## 513.23 — Capability discovery

Capability advertisement ≠ authorization.

## 513.24 — Dynamic registration

Tool server có thể register/unregister tools.

## 513.25 — Registry isolation

Different agent sessions có thể có different tool registries.

## 513.26 — Tool aliases

Aliases có thể tồn tại nhưng canonical identity vẫn required.

## 513.27 — Tool deprecation

Deprecated tool phải expose metadata.

## 513.28 — Compatibility

Tool replacement phải preserve schema/ABI contract hoặc increment version appropriately.

## 513.29 — Discovery cache

Discovery results có TTL/version.

## 513.30 — Stale registry

Stale discovery phải fail safely, không assume tool still exists.

---

# MCP-LIKE INTEROPERABILITY

## 513.31 — Protocol adapters

Axiom có thể implement adapters cho external agent-tool protocols.

## 513.32 — MCP-like semantics

Các concept như:

- tool;
- resource;
- prompt/template;
- server;
- client;
- capability negotiation

có thể được biểu diễn.

## 513.33 — Protocol neutrality

Không đưa MCP semantics vào Axiom language core.

## 513.34 — Resource

External resource có thể expose read-only/read-write operations theo capability.

## 513.35 — Prompt template

Prompt/template là data/schema artifact, không phải executable language primitive.

## 513.36 — Tool/resource distinction

Resource read và tool invocation không được tự động coi là cùng loại side effect.

## 513.37 — Server identity

External tool server có identity/version.

## 513.38 — Session

Protocol session có lifecycle explicit.

## 513.39 — Handshake

Handshake negotiate:

- protocol version;
- capabilities;
- limits;
- authentication.

## 513.40 — Protocol evolution

Unknown capabilities không được làm client crash nếu protocol cho phép forward compatibility.

---

# PROCESS / SANDBOX

## 513.41 — Out-of-process tool

Tool có thể chạy process riêng.

## 513.42 — Process isolation

Process boundary là security boundary theo 490.

## 513.43 — WASM tool

Tool có thể chạy trong WASM sandbox.

## 513.44 — Native plugin

Native plugin chạy in-process chỉ khi trusted.

## 513.45 — Untrusted native plugin

Untrusted native plugin không được mặc định load vào process chính.

## 513.46 — Capability grant

Sandbox được cấp explicit capabilities.

## 513.47 — Capability attenuation

Child process có thể nhận subset capability.

## 513.48 — Resource quotas

Sandbox có:

- CPU;
- memory;
- filesystem;
- network;
- output

limits.

## 513.49 — Timeout

Tool execution có deadline.

## 513.50 — Kill

Hung external process có thể bị terminate theo policy.

---

# NATIVE PLUGIN ABI

## 513.51 — Plugin descriptor

Plugin export:

```text
AxiomPluginDescriptor
```

chứa:

- ABI version;
- plugin ID;
- version;
- exported tools;
- required capabilities.

## 513.52 — Initialization

Plugin initialization explicit.

## 513.53 — Shutdown

Plugin shutdown explicit.

## 513.54 — Unload

Plugin chỉ được unload khi không còn live objects/callbacks/resources.

## 513.55 — ABI ownership

Ownership của objects crossing ABI phải explicit.

## 513.56 — Allocator boundary

Không được tự do `alloc` ở một runtime rồi `free` ở runtime khác nếu ABI không định nghĩa compatible allocator.

## 513.57 — String boundary

Strings crossing plugin ABI có explicit representation/ownership.

## 513.58 — Error boundary

Errors crossing ABI dùng stable error representation.

## 513.59 — Callback

Callbacks có lifetime contract.

## 513.60 — Threading

Plugin threading requirements phải khai báo.

---

# REMOTE TOOL EXECUTION

## 513.61 — Remote endpoint

Remote tool endpoint có:

```text
Endpoint {
    transport
    address
    protocol
}
```

## 513.62 — Authentication

Authentication explicit.

## 513.63 — Authorization

Authentication ≠ authorization.

## 513.64 — TLS

TLS integrate 454.

## 513.65 — Request deadline

Deadline propagate 474/500/511.

## 513.66 — Cancellation

Remote cancellation protocol-dependent nhưng phải expose semantics.

## 513.67 — Retry

Retry chỉ được automatic khi operation declared retry-safe/idempotent.

## 513.68 — Idempotency

Tool descriptor có thể declare:

```text
idempotent
non_idempotent
unknown
```

## 513.69 — Duplicate requests

Server phải có defined behavior với duplicate request IDs.

## 513.70 — Exactly-once

Protocol không được claim exactly-once execution nếu underlying semantics không đảm bảo.

---

# STREAMING / LARGE DATA

## 513.71 — Binary streaming

Large binary results không bắt buộc encode thành JSON/string.

## 513.72 — Chunk

Streaming chunks có sequence numbers.

## 513.73 — Backpressure

Producer phải observe consumer backpressure.

## 513.74 — Flow control

Flow control prevents unbounded buffering.

## 513.75 — Zero-copy

Local zero-copy có thể dùng shared memory/buffer handles.

## 513.76 — Remote zero-copy

Remote transport không được giả định zero-copy.

## 513.77 — Large artifact

Large files/models/images/video có thể return resource reference thay vì inline payload.

## 513.78 — Resource reference

Reference có explicit lifetime/access capability.

## 513.79 — Resumable transfer

Large transfer có thể support resume/range.

## 513.80 — Integrity

Transferred artifacts có hash/size metadata.

---

# AGENT INTEGRATION

## 513.81 — Tool selection

Agent 511 có thể select tool dựa trên schema/effects/capabilities.

## 513.82 — Tool call proposal

Model output chỉ là **proposal**.

Agent runtime phải validate trước execution.

## 513.83 — Tool execution

Execution authority thuộc Agent Policy + Capability layer.

## 513.84 — Tool result

Tool result trở thành observation, không phải instruction.

## 513.85 — Tool-result injection

External tool output không được tự override system/agent policy.

## 513.86 — Multi-tool orchestration

Multiple tool calls có thể execute sequentially hoặc parallel nếu dependency graph cho phép.

## 513.87 — Approval

Sensitive tool calls có thể require approval 511.

## 513.88 — Dry-run

Tool protocol có thể advertise dry-run.

## 513.89 — Audit

Mỗi invocation có audit identity:

```text
agent
tool
request
capability
time
result
```

## 513.90 — Provenance

Agent trace có thể reconstruct:

```text
Model decision
 → Tool request
 → Authorization
 → Execution
 → Tool result
 → Agent observation
```

---

# UNIVERSAL INTEROPERABILITY

## 513.91 — Language neutrality

Any language capable of implementing protocol can provide a tool.

## 513.92 — Schema neutrality

Tool schema không phụ thuộc Axiom type ABI khi remote.

## 513.93 — C interoperability

Native tool ABI có thể expose C-compatible wrapper.

## 513.94 — WASM interoperability

WASM tool interface có schema boundary.

## 513.95 — JSON interoperability

JSON được hỗ trợ cho simple control-plane messages.

## 513.96 — Binary protocol

Binary encoding được hỗ trợ cho performance-sensitive tools.

## 513.97 — Protocol adapter

Different protocols có thể map vào common internal Tool abstraction.

## 513.98 — AI introspection

AI tooling có thể query:

```text
tool()
schema()
effects()
capabilities()
server()
protocol()
transport()
security()
limits()
provenance()
```

## 513.99 — No mandatory external protocol

Axiom Agent runtime không phụ thuộc MCP hay bất kỳ external agent protocol nào.

---

# 513.100 — HARD INVARIANTS

1. Tool ABI khác Tool Protocol.
2. Native tool ABI có version.
3. Tool descriptor có stable identity.
4. Remote schema không phụ thuộc native layout.
5. Schema có canonical representation.
6. Schema có hash.
7. Input phải validate.
8. Output phải validate.
9. Version negotiation được hỗ trợ.
10. Forward-compatible fields có semantics rõ.
11. Protocol transport-independent.
12. stdio được hỗ trợ.
13. pipe được hỗ trợ.
14. socket được hỗ trợ.
15. HTTP có thể được hỗ trợ.
16. WebSocket có thể được hỗ trợ.
17. IPC được hỗ trợ.
18. Request có ID.
19. Response correlate với request.
20. Notification được hỗ trợ.
21. Streaming được hỗ trợ.
22. Partial results có semantics.
23. Stream completion có trạng thái rõ.
24. Protocol errors typed.
25. Tool discovery được hỗ trợ.
26. Discovery trả schema.
27. Discovery trả effects.
28. Discovery trả capabilities.
29. Capability advertisement không phải authorization.
30. Dynamic registration được hỗ trợ.
31. Registry có session isolation.
32. Tool aliases không thay canonical identity.
33. Deprecation được biểu diễn.
34. Compatibility được kiểm tra.
35. Discovery cache có version/TTL.
36. Stale discovery phải fail safely.
37. External protocol adapters được hỗ trợ.
38. MCP-like concepts có thể map.
39. MCP không thuộc language core.
40. External resources được hỗ trợ.
41. Prompt templates là data/schema.
42. Resource và tool semantics được phân biệt.
43. Tool server có identity.
44. Protocol session có lifecycle.
45. Handshake được hỗ trợ.
46. Protocol capability negotiation được hỗ trợ.
47. Out-of-process tools được hỗ trợ.
48. Process isolation integrate 490.
49. WASM sandbox được hỗ trợ.
50. Trusted native plugin được hỗ trợ.
51. Untrusted native plugin không được auto-load in-process.
52. Sandbox capabilities explicit.
53. Capability attenuation được hỗ trợ.
54. Sandbox resource quotas được hỗ trợ.
55. Tool timeout được hỗ trợ.
56. Hung tool process có termination policy.
57. Native plugin descriptor versioned.
58. Plugin initialization explicit.
59. Plugin shutdown explicit.
60. Plugin unload lifetime-safe.
61. ABI object ownership explicit.
62. Allocator boundary explicit.
63. String representation explicit.
64. Error representation stable.
65. Callback lifetime explicit.
66. Threading requirements explicit.
67. Remote endpoint có explicit transport/address.
68. Authentication explicit.
69. Authorization explicit.
70. TLS integrate 454.
71. Deadline integrate 474.
72. Cancellation được propagate khi protocol hỗ trợ.
73. Automatic retry chỉ cho retry-safe operations.
74. Idempotency được khai báo.
75. Duplicate request behavior defined.
76. Exactly-once không được claim sai.
77. Large binary streaming được hỗ trợ.
78. Streaming chunks có ordering identity.
79. Backpressure được hỗ trợ.
80. Flow control ngăn unbounded buffering.
81. Local zero-copy có thể hỗ trợ.
82. Remote zero-copy không được giả định.
83. Large artifacts có thể reference thay vì inline.
84. Resource references có lifetime/capability.
85. Resumable transfers có thể hỗ trợ.
86. Transfer integrity có hash/size.
87. Agent có thể select tools.
88. Model tool-call output chỉ là proposal.
89. Agent policy kiểm soát execution authority.
90. Tool result là observation, không phải trusted instruction.
91. Tool-result prompt injection phải được chống.
92. Multi-tool execution được hỗ trợ.
93. Parallel tool execution phải respect dependencies.
94. Sensitive actions có approval boundary.
95. Dry-run được hỗ trợ.
96. Every invocation có audit identity.
97. Execution provenance reconstructable.
98. Interoperability không phụ thuộc implementation language.
99. Không external AI protocol nào là mandatory.
100. **Axiom phải cung cấp một Tool ABI + Tool Protocol abstraction đủ thấp để native/WASM/process/remote tools giao tiếp zero-cost khi có thể, đủ cao để agent AI khám phá và gọi tool bằng schema/effects/capabilities, đồng thời giữ nguyên trust boundary: model chỉ đề xuất hành động, agent policy cấp quyền, tool thực thi, và kết quả quay trở lại dưới dạng untrusted observation có provenance.**

**BOOTSTRAP-513 hoàn tất / LOCKED.**

---

# BOOTSTRAP-514 — AI CONTEXT ENGINE, LONG-CONTEXT MEMORY, SEMANTIC COMPRESSION, CONTEXT CACHE & INFINITE-CONTEXT ARCHITECTURE

**Trạng thái: COMPLETED / LOCKED**

514 giải quyết một vấn đề trung tâm của Agent/LLM: **context hữu hạn nhưng workload có thể lớn hơn rất nhiều**.

```text id="514arch"
                   Knowledge / Files / Events
                            │
                       Context Source
                            ↓
                     Context Store
                            │
             ┌──────────────┼──────────────┐
             ↓              ↓              ↓
         Recent          Relevant       Persistent
          State           Recall          Memory
             └──────────────┼──────────────┘
                            ↓
                    Context Planner
                            ↓
                 Compress / Summarize
                            ↓
                     Token Budgeter
                            ↓
                    Model Context
                            ↓
                       Response
                            ↓
                    Context Update
```

---

## 514.1 — Context window

Context window là giới hạn model input/output theo model-specific semantics.

## 514.2 — External context

External context nằm ngoài model context window.

## 514.3 — Context store

Context store lưu information có thể retrieve lại.

## 514.4 — Context item

```text
ContextItem {
    id
    source
    content
    provenance
    priority
    timestamp
    sensitivity
}
```

## 514.5 — Context segment

Context được chia thành segments để quản lý.

## 514.6 — Context ordering

Ordering là semantic metadata, không chỉ array position.

## 514.7 — Context priority

Priority có thể là:

- required;
- high;
- normal;
- low;
- cacheable.

## 514.8 — Context budget

Budget tính theo token/byte/model-specific units.

## 514.9 — Budget reservation

System instructions/reserved output có thể reserve budget.

## 514.10 — Budget overflow

Overflow phải có explicit strategy:

```text
truncate
compress
retrieve
reject
```

---

# SEMANTIC COMPRESSION

## 514.11 — Compression

Compression có thể:

- summarize;
- merge;
- extract facts;
- remove redundancy.

## 514.12 — Lossy compression

Semantic compression là potentially lossy.

## 514.13 — Provenance

Summary giữ links đến source material.

## 514.14 — Compression model

Compression có thể dùng model riêng.

## 514.15 — Compression version

Compression algorithm/model có identity/version.

## 514.16 — Exact archive

Original content có thể lưu riêng để recover exact evidence.

## 514.17 — Summary ≠ source

Summary không được masquerade as original source.

## 514.18 — Compression policy

Policy explicit theo context type.

## 514.19 — Critical content

Required context không được silently compress.

## 514.20 — Rehydration

Summary có thể trigger retrieval original source.

---

# CONTEXT CACHE

## 514.21 — Prefix cache

Reusable context prefixes có thể cache.

## 514.22 — Cache identity

Cache key:

```text
model
tokenizer
prefix
generation configuration
```

## 514.23 — KV cache

514 integrate KV cache 509/505.

## 514.24 — Cross-request cache

Cross-request reuse chỉ khi isolation/security semantics cho phép.

## 514.25 — Session cache

Session-local cache được hỗ trợ.

## 514.26 — Persistent cache

Persistent context cache có thể dùng 455.

## 514.27 — Cache invalidation

Model/tokenizer/config changes invalidate incompatible caches.

## 514.28 — Cache eviction

Memory-aware eviction.

## 514.29 — Cache privacy

Private context không được leak qua shared cache.

## 514.30 — Cache provenance

Cache entries có source identity.

---

# LONG-CONTEXT STRATEGIES

## 514.31 — Sliding window

Recent context window.

## 514.32 — Hierarchical memory

Recent → summary → semantic memory.

## 514.33 — Retrieval memory

Retrieve relevant historical segments.

## 514.34 — Landmark memory

Important context markers có thể pin.

## 514.35 — Episodic summaries

Sessions có summary state.

## 514.36 — Semantic extraction

Facts có thể extracted thành structured records.

## 514.37 — Temporal memory

Historical context giữ time intervals.

## 514.38 — Dependency-aware context

Code/project context có thể select theo dependency graph 446/487.

## 514.39 — Conversation branches

Alternative conversation branches có thể giữ separately.

## 514.40 — Context fork

Agent session có thể fork context state.

---

# CONTEXT GRAPH

## 514.41 — Context graph

Nodes:

```text
source
document
message
event
summary
fact
tool result
model output
```

## 514.42 — Provenance edges

Graph giữ derived-from relationships.

## 514.43 — Contradiction edges

Conflicting records có thể link.

## 514.44 — Supersession

Newer fact có thể supersede older fact với explicit policy.

## 514.45 — Confidence

Inferred data có uncertainty metadata.

## 514.46 — Context lineage

Có thể trace:

```text
answer
→ context
→ summary
→ original source
```

## 514.47 — Deletion propagation

Deletion policy có thể propagate đến derived caches/summaries.

## 514.48 — Privacy boundary

Context graph obey access-control domains.

## 514.49 — Tenant boundary

Multi-agent/multi-user context isolation.

## 514.50 — Export

Context lineage có thể export audit artifact.

---

# TOKEN BUDGETER

## 514.51 — Token estimator

Model-specific tokenizer estimate được hỗ trợ.

## 514.52 — Exact tokenization

Final context phải use actual tokenizer khi required.

## 514.53 — Budget planner

Planner chọn context items trong budget.

## 514.54 — Required items

Required items được reserved trước optional items.

## 514.55 — Relevance

Relevance là one input, không phải guarantee of truth.

## 514.56 — Recency

Recency có thể influence selection.

## 514.57 — Diversity

Selection có thể tránh duplicate evidence.

## 514.58 — Coverage

Context planner có thể optimize topic/source coverage.

## 514.59 — Cost model

Token cost/model latency estimates là estimates.

## 514.60 — Explainability

Planner phải có thể explain why item included/excluded.

---

# MODEL CONTEXT MODES

## 514.61 — Full-context mode

Dùng tất cả content trong budget.

## 514.62 — Retrieval mode

Chỉ đưa selected evidence.

## 514.63 — Summary mode

Dùng summaries.

## 514.64 — Hybrid mode

Recent + summary + retrieval.

## 514.65 — Tool-assisted mode

Model gọi retrieval tools.

## 514.66 — Context policy

Agent policy chọn mode.

## 514.67 — Context determinism

Deterministic mode có deterministic ranking/tie-break.

## 514.68 — Context freshness

Freshness requirement explicit.

## 514.69 — Staleness

Stale context phải có metadata.

## 514.70 — Temporal cutoff

Agent có thể pin knowledge trước một timestamp.

---

# HUGE DOCUMENTS / CODEBASES

## 514.71 — File-aware context

Files có source identity.

## 514.72 — Symbol-aware context

Axiom code context dùng SymbolId.

## 514.73 — Dependency-aware expansion

Referenced symbols có thể được expand.

## 514.74 — Call-chain context

Caller/callee neighborhoods có thể retrieve.

## 514.75 — Change-aware context

Current diff + affected symbols từ 486.

## 514.76 — Build-aware context

Failed build/test nodes từ 487 có thể được injected.

## 514.77 — Documentation context

485 metadata được integrated.

## 514.78 — Diagnostic context

Compiler diagnostics có structured context.

## 514.79 — Repository-scale retrieval

Agent không cần load toàn repository vào model context.

## 514.80 — Context artifact

Context assembly có reproducible artifact identity.

---

# MULTIMODAL CONTEXT

## 514.81 — Text context

509 integration.

## 514.82 — Image context

510 visual embeddings/tokens.

## 514.83 — Audio context

510 audio/speech representations.

## 514.84 — Video context

510 temporal segments.

## 514.85 — Cross-modal retrieval

512 integration.

## 514.86 — Context alignment

Different modalities retain temporal/spatial provenance.

## 514.87 — Multimodal budget

Budget accounts for modality-specific cost.

## 514.88 — Visual compression

Images may be resized/cropped/summarized under explicit policy.

## 514.89 — Audio compression

Audio context may use segments/features/transcripts.

## 514.90 — Video compression

Video may use keyframes/summaries/temporal segments.

---

# SECURITY / PRIVACY

## 514.91 — Access control

Context retrieval integrates 490/512.

## 514.92 — Secret filtering

Secrets can be excluded/redacted.

## 514.93 — Prompt injection

Context content remains data.

## 514.94 — Cross-session isolation

Sessions cannot accidentally share private context.

## 514.95 — Cache isolation

Shared cache must enforce access identity.

## 514.96 — Deletion

Context deletion can invalidate derived artifacts.

## 514.97 — Audit

Context assembly is auditable.

## 514.98 — AI introspection

Queries:

```text
context()
budget()
included()
excluded()
compressed()
source()
lineage()
cache()
```

## 514.99 — No fake infinite context

“Unlimited/infinite context” is an architectural abstraction, not a claim that the model physically accepts infinite tokens.

---

# 514.100 — HARD INVARIANTS

1. Context window là model-specific limit.
2. External context khác model context.
3. Context store được hỗ trợ.
4. Context item có identity.
5. Context item có provenance.
6. Context item có priority.
7. Context item có timestamp metadata khi cần.
8. Sensitive context có policy.
9. Context segments được hỗ trợ.
10. Ordering semantics explicit.
11. Token/byte budget explicit.
12. Reserved budget được hỗ trợ.
13. Overflow strategy explicit.
14. Semantic compression được hỗ trợ.
15. Compression có provenance.
16. Compression có model/version identity.
17. Original source có thể preserve.
18. Summary không được masquerade source.
19. Critical context không silently compress.
20. Rehydration được hỗ trợ.
21. Prefix cache được hỗ trợ.
22. Cache identity include model/tokenizer/config.
23. KV cache integrate 509/505.
24. Cross-request cache có isolation.
25. Session cache được hỗ trợ.
26. Persistent cache được hỗ trợ.
27. Cache invalidation deterministic.
28. Cache eviction explicit.
29. Cache privacy được enforce.
30. Cache provenance được preserve.
31. Sliding-window strategy được hỗ trợ.
32. Hierarchical memory được hỗ trợ.
33. Retrieval memory được hỗ trợ.
34. Landmark memory được hỗ trợ.
35. Episodic summary được hỗ trợ.
36. Semantic extraction được hỗ trợ.
37. Temporal memory được hỗ trợ.
38. Dependency-aware code context được hỗ trợ.
39. Conversation branches được hỗ trợ.
40. Context fork được hỗ trợ.
41. Context graph được hỗ trợ.
42. Source nodes có identity.
43. Derived-from provenance được lưu.
44. Contradiction relationships được biểu diễn.
45. Supersession có explicit semantics.
46. Uncertainty metadata được preserve.
47. Context lineage có thể truy xuất.
48. Deletion policy có thể propagate.
49. Privacy boundaries được enforce.
50. Tenant boundaries được enforce.
51. Context export/audit được hỗ trợ.
52. Token estimator được hỗ trợ.
53. Final tokenization có thể exact.
54. Budget planner được hỗ trợ.
55. Required context được ưu tiên.
56. Relevance là selection signal, không phải truth proof.
57. Recency có thể influence selection.
58. Diversity có thể influence selection.
59. Coverage có thể influence selection.
60. Cost model là estimate.
61. Context planner có explainability.
62. Full-context mode được hỗ trợ.
63. Retrieval mode được hỗ trợ.
64. Summary mode được hỗ trợ.
65. Hybrid mode được hỗ trợ.
66. Tool-assisted mode được hỗ trợ.
67. Context policy explicit.
68. Deterministic context mode được hỗ trợ.
69. Freshness requirement explicit.
70. Staleness metadata được preserve.
71. Temporal cutoff được hỗ trợ.
72. File-aware code context được hỗ trợ.
73. Symbol-aware context được hỗ trợ.
74. Dependency expansion được hỗ trợ.
75. Caller/callee retrieval được hỗ trợ.
76. Change-aware context integrate 486.
77. Build-aware context integrate 487.
78. Documentation context integrate 485.
79. Diagnostic context integrate compiler metadata.
80. Repository-scale retrieval không yêu cầu full source loading.
81. Context assembly có artifact identity.
82. Text context integrate 509.
83. Image context integrate 510.
84. Audio context integrate 510.
85. Video context integrate 510.
86. Cross-modal retrieval integrate 512.
87. Spatial/temporal provenance được preserve.
88. Multimodal budget explicit.
89. Visual compression explicit.
90. Audio compression explicit.
91. Video compression explicit.
92. Access control integrate 490/512.
93. Secret filtering được hỗ trợ.
94. Retrieved context remains untrusted data.
95. Cross-session context isolation được enforce.
96. Shared cache isolation được enforce.
97. Context deletion có defined semantics.
98. Context assembly audit được hỗ trợ.
99. AI introspection được hỗ trợ.
100. **Axiom phải biến context hữu hạn của model thành một kiến trúc context mở rộng thông qua retrieval, memory, semantic compression, cache và provenance, nhưng không được đánh tráo summary thành source, relevance thành truth, hay “infinite context” thành khả năng vật lý vô hạn của model.**

**BOOTSTRAP-514 hoàn tất / LOCKED.**

---

## Tiến độ

```text
BOOTSTRAP-509  LLM / NLP / Tokenization / Generation       LOCKED
BOOTSTRAP-510  Multimodal AI                               LOCKED
BOOTSTRAP-511  AI Agent Foundation                         LOCKED
BOOTSTRAP-512  Knowledge Engine / RAG                     LOCKED
BOOTSTRAP-513  AI Tool / Plugin ABI / Interoperability    LOCKED
BOOTSTRAP-514  AI Context Engine / Long Context           LOCKED
```

**Task kế tiếp: `BOOTSTRAP-515 — AI MEMORY & PERSONALIZATION ENGINE, LONG-TERM MEMORY, USER/AGENT PROFILE, LEARNING, MEMORY CONSOLIDATION & FORGETTING SEMANTICS`.**