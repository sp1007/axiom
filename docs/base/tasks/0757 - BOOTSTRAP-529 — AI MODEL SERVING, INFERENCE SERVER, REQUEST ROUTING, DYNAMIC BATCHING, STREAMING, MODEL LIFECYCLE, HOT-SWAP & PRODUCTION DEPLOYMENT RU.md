# BOOTSTRAP-529 — AI MODEL SERVING, INFERENCE SERVER, REQUEST ROUTING, DYNAMIC BATCHING, STREAMING, MODEL LIFECYCLE, HOT-SWAP & PRODUCTION DEPLOYMENT RUNTIME

**Trạng thái: COMPLETED / LOCKED**

529 xây dựng tầng **production serving** trên 503–528. Đây là lớp biến model/executable graph thành một dịch vụ inference có khả năng nhận request đồng thời, batching, streaming, routing, model versioning, hot-swap và graceful shutdown.

Nguyên tắc trung tâm:

```text
                         Client
                           │
                           ↓
                    Transport Layer
                 HTTP / RPC / IPC / WS
                           │
                           ↓
                    Request Gateway
                           │
              ┌────────────┼────────────┐
              ↓            ↓            ↓
          Validation    Auth/ACL     Rate Limit
              │            │            │
              └────────────┼────────────┘
                           ↓
                    Request Scheduler
                           │
                 ┌─────────┼─────────┐
                 ↓         ↓         ↓
              Queue     Batching   Priority
                 │         │         │
                 └─────────┼─────────┘
                           ↓
                    Model Router
                           │
              ┌────────────┼────────────┐
              ↓            ↓            ↓
          Model V1      Model V2     Canary
              │            │            │
              └────────────┼────────────┘
                           ↓
                    Execution Runtime
                           │
                CPU / GPU / NPU / Hybrid
                           │
                           ↓
                  Response / Stream
                           │
                           ↓
                     Client
```

---

## 529.1 — Serving ≠ Model Runtime

Model runtime 505 thực thi một model.

Serving layer quản lý **nhiều request, nhiều model instance và lifecycle production**.

## 529.2 — Server

```text
InferenceServer {
    ServerId
    Version
    Config
    Models
    Transports
    Policies
}
```

## 529.3 — Request

```text
InferenceRequest {
    RequestId
    Model
    Input
    Parameters
    Deadline?
    Priority?
    Metadata
}
```

## 529.4 — Response

```text
InferenceResponse {
    RequestId
    Output
    Usage
    Metadata
    Error?
}
```

## 529.5 — Request state

```text
Received
Validated
Queued
Scheduled
Running
Streaming
Completed
Cancelled
Failed
Expired
```

---

# TRANSPORT

## 529.6 — Transport abstraction

Serving không phụ thuộc một protocol.

Hỗ trợ:

- HTTP;
- HTTP/2;
- HTTP/3;
- WebSocket;
- native RPC;
- Unix socket;
- named pipe;
- local IPC;
- in-process API.

## 529.7 — Protocol adapter

Transport chỉ chịu trách nhiệm framing/transport.

## 529.8 — Serving protocol

Request semantics độc lập transport.

## 529.9 — Streaming

Response có thể trả từng chunk/token/frame.

## 529.10 — Bidirectional streaming

Transport phù hợp có thể hỗ trợ request/response hai chiều.

---

# REQUEST VALIDATION

## 529.11 — Schema

Model input schema được validate trước execution.

## 529.12 — Shape

Tensor shape được validate.

## 529.13 — Dtype

Dtype mismatch là explicit error hoặc configured conversion.

## 529.14 — Size limits

Input size giới hạn.

## 529.15 — Token limits

LLM request có context/output token limits.

## 529.16 — Media limits

Image/audio/video dimensions/duration/size giới hạn.

## 529.17 — Parameter validation

Sampling/generation parameters phải thuộc model-supported range.

## 529.18 — Unknown parameters

Unknown parameter policy:

```text
Reject
Ignore
Forward
```

phải explicit.

## 529.19 — Validation before queue

Invalid request không được chiếm execution capacity.

## 529.20 — Error schema

Validation errors có machine-readable code/path/message.

---

# AUTHORIZATION & CAPABILITY

## 529.21 — Authentication

Identity xác định caller.

## 529.22 — Authorization

Authorization xác định caller được gọi model nào.

## 529.23 — Capability

Serving có thể expose model capability metadata.

## 529.24 — Tenant isolation

Tenant identity được propagate.

## 529.25 — Model access policy

Access có thể giới hạn theo model/version.

## 529.26 — Resource quota

Caller/tenant quota.

## 529.27 — Secret isolation

Credentials không đi vào model input/log mặc định.

## 529.28 — Metadata trust

Client metadata không tự động được coi là trusted.

## 529.29 — Audit

Security-sensitive serving actions có thể audit.

## 529.30 — No ambient authority

Model execution không tự động được cấp network/filesystem/process authority.

---

# REQUEST QUEUE

## 529.31 — Queue

Request queue có thể bounded hoặc unbounded.

## 529.32 — Default

Production serving mặc định nên bounded để tránh memory exhaustion.

## 529.33 — Overflow

Policies:

```text
Reject
Drop
Defer
Backpressure
```

## 529.34 — Priority

Request priority explicit.

## 529.35 — Fairness

Scheduler có thể enforce tenant/request fairness.

## 529.36 — Deadline

Deadline từ 474 được propagate.

## 529.37 — Expired request

Request hết deadline trước execution phải được reject/cancel.

## 529.38 — Cancellation

Client cancellation propagate xuống runtime khi có thể.

## 529.39 — Queue metrics

Queue depth/wait time/drop/reject count được measure.

## 529.40 — Queue ownership

Queued requests có deterministic lifetime.

---

# DYNAMIC BATCHING

## 529.41 — Batch

Nhiều request tương thích được ghép thành execution batch.

## 529.42 — Compatibility

Batching chỉ xảy ra khi:

- model compatible;
- dtype compatible;
- shape compatible hoặc dynamic batching hỗ trợ;
- generation parameters compatible;
- device compatible;
- policy compatible.

## 529.43 — Padding

Padding policy explicit.

## 529.44 — Ragged

Ragged batching được hỗ trợ khi backend/model cho phép.

## 529.45 — Packing

Sequence packing optional.

## 529.46 — Maximum batch

Batch size limit.

## 529.47 — Maximum wait

Scheduler có `max_batch_wait`.

## 529.48 — Adaptive batching

Scheduler có thể điều chỉnh batch theo workload.

## 529.49 — Deadline-aware batching

Không được giữ request quá lâu chỉ để tăng batch.

## 529.50 — Batch provenance

Mỗi output reference original RequestId.

---

# LLM PREFILL / DECODE

## 529.51 — Phase distinction

LLM serving phân biệt:

```text
Prefill
Decode
```

## 529.52 — Continuous batching

Decode sequences có thể được ghép/loại khỏi batch động.

## 529.53 — KV cache

Mỗi request/sequence có KV cache identity.

## 529.54 — Prefix cache

Prefix cache được hỗ trợ.

## 529.55 — Cache ownership

KV cache lifetime gắn request/session.

## 529.56 — Cache eviction

Eviction policy explicit.

## 529.57 — Chunked prefill

Long prompts có thể prefill theo chunks.

## 529.58 — Scheduling fairness

Prefill không được vô hạn chặn decode.

## 529.59 — Speculative decoding

Có thể sử dụng draft model nếu configured.

## 529.60 — Generation stop

EOS/max tokens/stop sequence/cancellation được enforce.

---

# STREAMING

## 529.61 — Stream identity

Mỗi streaming response có StreamId.

## 529.62 — Chunk

```text
StreamChunk {
    sequence
    payload
    final
}
```

## 529.63 — Ordering

Chunk ordering deterministic.

## 529.64 — Backpressure

Client chậm phải tạo backpressure hoặc bounded buffering.

## 529.65 — Buffer limit

Không buffer vô hạn.

## 529.66 — Cancellation

Cancel stream phải release resources.

## 529.67 — Final marker

Stream completion explicit.

## 529.68 — Partial output

Failed/cancelled streams distinguish partial output.

## 529.69 — Reconnect

Reconnect semantics phải explicit; không mặc định replay inference.

## 529.70 — Streaming modalities

Text/token/audio/video streaming có thể dùng chung stream semantics nhưng payload schema riêng.

---

# MODEL REGISTRY

## 529.71 — Model identity

```text
ModelId
Version
ArtifactHash
SchemaVersion
```

## 529.72 — Model metadata

Model metadata từ 506.

## 529.73 — Runtime compatibility

Serving kiểm tra:

- compiler;
- runtime;
- backend;
- target;
- device;
- graph;
- model format.

## 529.74 — Model state

```text
Registered
Loading
Ready
Draining
Unloading
Failed
```

## 529.75 — Model instance

Một model version có thể có nhiều execution instances.

## 529.76 — Instance state

```text
Starting
Ready
Busy
Draining
Failed
Stopped
```

## 529.77 — Warmup

Model có thể warmup trước Ready.

## 529.78 — Readiness

Model chỉ nhận request sau khi Ready.

## 529.79 — Health

Health và readiness khác nhau.

## 529.80 — Model unload

Unload chỉ sau khi active requests kết thúc/cancel theo policy.

---

# HOT-SWAP

## 529.81 — New version

Load model V2 song song với V1.

## 529.82 — Atomic activation

Routing switch phải atomic ở request boundary.

## 529.83 — In-flight requests

Request đã bắt đầu tiếp tục dùng version cũ.

## 529.84 — Drain

Version cũ chuyển sang Draining.

## 529.85 — Rollback

Có thể chuyển routing về version trước.

## 529.86 — Compatibility

Hot-swap yêu cầu compatible input/output contract hoặc explicit API version.

## 529.87 — Cache isolation

Model-specific cache không được nhầm version.

## 529.88 — Artifact identity

Routing phải pin ModelId + Version + ArtifactHash.

## 529.89 — Canary

Canary routing có thể configured.

## 529.90 — Traffic split

Traffic allocation là configuration, không phải model semantic.

---

# ROUTING

## 529.91 — Router

Router chọn model instance.

## 529.92 — Routing criteria

Có thể dựa trên:

- model;
- version;
- capability;
- target;
- device;
- locality;
- tenant;
- load;
- latency policy;
- explicit deployment rule.

## 529.93 — Load balancing

Round-robin/least-load/hash/priority có thể được cung cấp.

## 529.94 — Sticky sessions

Session affinity optional.

## 529.95 — Session identity

LLM/chat session có stable logical identity.

## 529.96 — Session routing

Session routing không được làm mất state.

## 529.97 — Failover

Failover policy explicit.

## 529.98 — Retry

Inference retry phải xét idempotency.

## 529.99 — Non-idempotent inference

External side effects không được tự động retry.

## 529.100 — Routing explanation

AI tooling có thể query vì sao request được route tới instance đó.

---

# MODEL POOL

## 529.101 — Instance pool

Một model có thể có N instances.

## 529.102 — Device placement

Instance có thể pin CPU/GPU/NPU.

## 529.103 — Multi-device

Một model có thể shard/replicate trên nhiều devices.

## 529.104 — Device health

Unhealthy device không nhận request mới.

## 529.105 — Capacity

Instance publish capacity metadata.

## 529.106 — Admission control

Request có thể reject khi capacity không đủ.

## 529.107 — Queue-aware routing

Router có thể xét queue depth.

## 529.108 — Locality

NUMA/device locality được xem xét.

## 529.109 — Resource reservation

Serving có thể reserve GPU memory/CPU workers.

## 529.110 — No hidden allocation

Execution không được tự ý tạo unlimited resources.

---

# AUTOSCALING

## 529.111 — Scaling

Instance count có thể tăng/giảm.

## 529.112 — Scale trigger

CPU/GPU/load/queue/latency/custom metric.

## 529.113 — Cold-start

Cold-start cost được expose.

## 529.114 — Warm pool

Warm instances optional.

## 529.115 — Scale-down

Scale-down phải drain active requests.

## 529.116 — Minimum instances

Configured.

## 529.117 — Maximum instances

Configured.

## 529.118 — Hysteresis

Scaling phải tránh oscillation.

## 529.119 — Resource budget

Autoscaling obey resource limits.

## 529.120 — Deterministic test

Scaling algorithm có deterministic simulation mode.

---

# RATE LIMITING & ADMISSION

## 529.121 — Rate limit

Request/token/byte limits.

## 529.122 — Burst

Burst capacity explicit.

## 529.123 — Tenant quotas

Per-tenant quota.

## 529.124 — Model quotas

Per-model capacity.

## 529.125 — Concurrency limit

Maximum active requests.

## 529.126 — Token budget

Generation token budget.

## 529.127 — Cost budget

Optional compute-cost budget.

## 529.128 — Admission order

Admission policy explicit.

## 529.129 — Overload response

Overload có machine-readable error.

## 529.130 — Backpressure

Client-facing backpressure được hỗ trợ.

---

# FAILURE & RECOVERY

## 529.131 — Request timeout

Timeout từ 474.

## 529.132 — Model error

Model execution failure.

## 529.133 — Device failure

GPU/NPU/device loss.

## 529.134 — Worker crash

Execution worker crash.

## 529.135 — Server restart

Server restart không làm mất durable deployment metadata.

## 529.136 — In-flight recovery

Inference request recovery chỉ được claim nếu state đủ để resume/retry.

## 529.137 — Retry budget

Retry bounded.

## 529.138 — Circuit breaker

Repeated model failures có thể mở circuit.

## 529.139 — Health recovery

Failed instance phải pass readiness trước khi nhận traffic.

## 529.140 — Failure provenance

Failure reference model/request/instance/device.

---

# MODEL WARMUP & CACHE

## 529.141 — Weight cache

Weights có thể cache.

## 529.142 — Graph cache

Compiled graph từ 504/505 có thể cache.

## 529.143 — Kernel cache

Kernel cache được reuse.

## 529.144 — KV cache

Request-level cache.

## 529.145 — Prefix cache

Cross-request prefix cache nếu policy cho phép.

## 529.146 — Cache identity

Cache key phải include relevant model/config identity.

## 529.147 — Cache isolation

Tenant/security policy không được bypass bởi cache.

## 529.148 — Cache invalidation

Model/config change invalidates affected cache.

## 529.149 — Memory budget

Cache có bounded memory budget.

## 529.150 — Warmup report

Warmup latency/resource usage được measure.

---

# OBSERVABILITY

## 529.151 — Request metrics

Measure:

- request count;
- success;
- failure;
- cancellation;
- queue latency;
- execution latency.

## 529.152 — Model metrics

Per model/version.

## 529.153 — Device metrics

Per device.

## 529.154 — Batch metrics

Batch size/wait/fill ratio.

## 529.155 — LLM metrics

TTFT/decode latency/tokens/sec/KV memory.

## 529.156 — Streaming metrics

Chunks/sec, stream duration, cancellation.

## 529.157 — Resource metrics

CPU/RAM/GPU memory/utilization.

## 529.158 — Error taxonomy

Errors có stable codes.

## 529.159 — Trace

Request→scheduler→model→kernel trace correlation.

## 529.160 — Privacy

Input/output content không được log mặc định nếu sensitive.

---

# SECURITY

## 529.161 — Untrusted input

All client input untrusted.

## 529.162 — Prompt injection

Serving không coi model input là policy authority.

## 529.163 — Tool authority

Model-generated tool calls không tự động được server authorize.

## 529.164 — SSRF

Network-capable tools phải obey capability policy.

## 529.165 — Resource exhaustion

Input/model/output limits.

## 529.166 — Model isolation

Untrusted model execution có thể process/WASM isolation.

## 529.167 — Model artifact verification

Artifact hash/signature có thể verify trước load.

## 529.168 — Supply-chain provenance

Model provenance từ 506/528 được preserve.

## 529.169 — Secret isolation

Secrets không được đưa vào prompt/model context trừ khi explicit.

## 529.170 — Audit

Security-sensitive serving operations auditable.

---

# DEPLOYMENT

## 529.171 — Deployment

```text
Deployment {
    Model
    Version
    Artifact
    Runtime
    Target
    Devices
    Policy
    Routing
}
```

## 529.172 — Deployment revision

Mỗi deployment thay đổi tạo revision.

## 529.173 — Immutable revision

Published deployment revision immutable.

## 529.174 — Rollout

Rollout có phases.

## 529.175 — Rollback

Rollback về known-good revision.

## 529.176 — Drain

Old instances drain.

## 529.177 — Readiness gate

New version chỉ nhận traffic khi Ready.

## 529.178 — Health gate

Health failure ngăn routing.

## 529.179 — Config provenance

Deployment config được hash.

## 529.180 — Deployment artifact

Deployment manifest machine-readable.

---

# LOCAL / EDGE / CLOUD

## 529.181 — In-process serving

Application có thể embed model runtime.

## 529.182 — Local server

Model server chạy cùng machine.

## 529.183 — Edge

Device-local serving.

## 529.184 — Remote

Network service.

## 529.185 — Distributed serving

Multiple servers/instances.

## 529.186 — No cloud dependency

Axiom serving API không yêu cầu cloud.

## 529.187 — Offline serving

Local inference first-class.

## 529.188 — Embedded serving

Freestanding/device deployments có thể bỏ server features.

## 529.189 — WASM

Browser/WASM serving obey host security/capability.

## 529.190 — Platform abstraction

Transport/deployment backend độc lập language core.

---

# AI INTROSPECTION

## 529.191 — Request explain

```text
explain(request_id)
```

## 529.192 — Routing explain

```text
explain_route(request_id)
```

## 529.193 — Queue explain

```text
explain_queue(request_id)
```

## 529.194 — Batch explain

```text
explain_batch(batch_id)
```

## 529.195 — Model explain

```text
model_state(model_id)
```

## 529.196 — Capacity

```text
capacity(model_id)
```

## 529.197 — Deployment diff

```text
deployment_diff(a, b)
```

## 529.198 — Performance

```text
serving_profile(model_id)
```

## 529.199 — Failure

```text
failure_trace(request_id)
```

## 529.200 — Full provenance

```text
Request
 → Route
 → Queue
 → Batch
 → Model Instance
 → Execution Plan
 → Device
 → Output
```

---

# 529.201 — HARD INVARIANTS

1. Serving khác model runtime.
2. Server có identity.
3. Request có identity.
4. Response có request identity.
5. Request state machine explicit.
6. Transport độc lập serving semantics.
7. HTTP được hỗ trợ.
8. Native RPC được hỗ trợ.
9. IPC được hỗ trợ.
10. Streaming được hỗ trợ.
11. Bidirectional streaming có thể hỗ trợ.
12. Input schema được validate.
13. Shape được validate.
14. Dtype được validate.
15. Input size có giới hạn.
16. Token size có giới hạn.
17. Media size có giới hạn.
18. Generation parameters được validate.
19. Unknown parameter policy explicit.
20. Validation xảy ra trước execution.
21. Validation error có structured schema.
22. Authentication được tách khỏi authorization.
23. Model authorization được hỗ trợ.
24. Capability metadata được hỗ trợ.
25. Tenant isolation được hỗ trợ.
26. Resource quota được hỗ trợ.
27. Client metadata không mặc định trusted.
28. Security audit được hỗ trợ.
29. Không có ambient model authority.
30. Queue được hỗ trợ.
31. Queue có thể bounded.
32. Overflow policy explicit.
33. Priority được hỗ trợ.
34. Fairness policy được hỗ trợ.
35. Deadline được propagate.
36. Expired request không được execute.
37. Cancellation được propagate.
38. Queue metrics được expose.
39. Queue resource lifetime deterministic.
40. Dynamic batching được hỗ trợ.
41. Batch compatibility được kiểm tra.
42. Padding policy explicit.
43. Ragged batching được hỗ trợ.
44. Packing có thể hỗ trợ.
45. Batch size có giới hạn.
46. Batch wait có giới hạn.
47. Adaptive batching có thể hỗ trợ.
48. Deadline-aware batching được hỗ trợ.
49. Batch output giữ RequestId.
50. Prefill/decode được distinguish.
51. Continuous batching được hỗ trợ.
52. KV cache được quản lý explicit.
53. Prefix cache có thể hỗ trợ.
54. KV cache ownership explicit.
55. KV eviction policy explicit.
56. Chunked prefill được hỗ trợ.
57. Scheduler không được để prefill starvation decode.
58. Speculative decoding có thể hỗ trợ.
59. Generation termination explicit.
60. Streaming có identity.
61. Stream chunks ordered.
62. Backpressure được hỗ trợ.
63. Stream buffer bounded.
64. Cancellation giải phóng resource.
65. Partial output được distinguish.
66. Reconnect semantics explicit.
67. Streaming modalities có typed payload.
68. Model identity gồm version/artifact identity.
69. Model metadata từ model artifact được preserve.
70. Runtime compatibility được kiểm tra.
71. Model lifecycle explicit.
72. Model readiness khác health.
73. Model instances có state.
74. Warmup được hỗ trợ.
75. Unload phải respect active requests.
76. Hot-swap được hỗ trợ.
77. New model load độc lập old model.
78. Routing switch atomic tại request boundary.
79. In-flight request giữ model identity.
80. Old version có draining state.
81. Rollback được hỗ trợ.
82. API compatibility được kiểm tra.
83. Cache identity include model identity.
84. Canary rollout có thể hỗ trợ.
85. Traffic policy explicit.
86. Router có identity.
87. Routing criteria explicit.
88. Load balancing được hỗ trợ.
89. Sticky sessions có thể hỗ trợ.
90. Session state không được mất khi route.
91. Failover policy explicit.
92. Retry xét idempotency.
93. Non-idempotent external effects không auto-retry.
94. Routing explanation được hỗ trợ.
95. Model instance pool được hỗ trợ.
96. Device placement explicit.
97. Multi-device deployment được hỗ trợ.
98. Device health ảnh hưởng admission.
99. Capacity metadata được expose.
100. Admission control được hỗ trợ.
101. Queue-aware routing có thể hỗ trợ.
102. NUMA/device locality được expose.
103. Resource reservation được hỗ trợ.
104. Không có unlimited hidden allocation.
105. Autoscaling có thể hỗ trợ.
106. Scale trigger explicit.
107. Cold-start được measure.
108. Warm pool có thể hỗ trợ.
109. Scale-down drain active requests.
110. Minimum instance configurable.
111. Maximum instance configurable.
112. Scaling hysteresis có thể hỗ trợ.
113. Autoscaling obey resource limits.
114. Deterministic scaling simulation được hỗ trợ.
115. Rate limiting được hỗ trợ.
116. Burst policy explicit.
117. Tenant quotas được hỗ trợ.
118. Model quotas được hỗ trợ.
119. Concurrency limits được hỗ trợ.
120. Token budget được hỗ trợ.
121. Cost budget có thể hỗ trợ.
122. Admission ordering explicit.
123. Overload errors structured.
124. Backpressure được expose.
125. Request timeout được hỗ trợ.
126. Model execution failure được distinguish.
127. Device failure được distinguish.
128. Worker crash được detect.
129. Deployment metadata survives server restart.
130. Recovery semantics explicit.
131. Retry budget bounded.
132. Circuit breaker có thể hỗ trợ.
133. Failed instance không nhận traffic trước readiness.
134. Failure provenance được preserve.
135. Weight cache được hỗ trợ.
136. Graph cache được hỗ trợ.
137. Kernel cache được hỗ trợ.
138. Request cache semantics explicit nếu có.
139. Prefix cache có security isolation.
140. Cache keys include relevant configuration.
141. Cache invalidation theo model/config.
142. Cache memory bounded.
143. Warmup metrics được expose.
144. Request metrics được expose.
145. Model metrics được expose.
146. Device metrics được expose.
147. Batch metrics được expose.
148. LLM TTFT có thể measure.
149. Decode throughput có thể measure.
150. KV memory có thể measure.
151. Stream metrics được expose.
152. Resource metrics được expose.
153. Error codes stable.
154. Request trace correlation được hỗ trợ.
155. Sensitive request content không log mặc định.
156. Client input là untrusted.
157. Prompt injection không thay đổi policy authority.
158. Model-generated tool calls không tự authorize.
159. SSRF protections được hỗ trợ.
160. Resource exhaustion controls được hỗ trợ.
161. Untrusted model isolation được hỗ trợ.
162. Model artifact verification được hỗ trợ.
163. Model supply-chain provenance được preserve.
164. Secret isolation được enforce.
165. Security-sensitive operations audit được.
166. Deployment có identity.
167. Deployment revision immutable.
168. Rollout phases explicit.
169. Rollback được hỗ trợ.
170. Drain được hỗ trợ.
171. Readiness gate được enforce.
172. Health gate được enforce.
173. Deployment config có hash.
174. Deployment manifest machine-readable.
175. In-process serving được hỗ trợ.
176. Local server được hỗ trợ.
177. Edge serving được hỗ trợ.
178. Remote serving được hỗ trợ.
179. Distributed serving được hỗ trợ.
180. Cloud không phải dependency bắt buộc.
181. Offline serving được hỗ trợ.
182. Embedded deployment được hỗ trợ.
183. WASM serving obey host capability.
184. Transport backend độc lập language core.
185. Request explanation được hỗ trợ.
186. Route explanation được hỗ trợ.
187. Queue explanation được hỗ trợ.
188. Batch explanation được hỗ trợ.
189. Model state query được hỗ trợ.
190. Capacity query được hỗ trợ.
191. Deployment diff được hỗ trợ.
192. Serving profiling được hỗ trợ.
193. Failure trace được hỗ trợ.
194. End-to-end provenance được hỗ trợ.
195. Serving không tự động biến model output thành trusted instruction.
196. Serving policy không được ẩn trong model.
197. Model version không được thay đổi silently.
198. Active request không được route sang version khác giữa execution.
199. Deployment rollback phải preserve artifact identity.
200. **Axiom Model Serving phải cung cấp một production runtime có request lifecycle, admission control, dynamic batching, streaming, model routing, hot-swap, rollback, resource isolation và observability đầy đủ, nhưng mọi authority, allocation, network access, retry, cache và deployment behavior phải explicit và inspectable; không được biến inference server thành một runtime “ma thuật” với side effects ẩn.**

**BOOTSTRAP-529 hoàn tất / LOCKED.**

---

# BOOTSTRAP-530 — AI MODEL TRAINING ORCHESTRATION, EXPERIMENT MANAGEMENT, RUN TRACKING, HYPERPARAMETER SEARCH, CHECKPOINTING, DISTRIBUTED TRAINING & REPRODUCIBLE EXPERIMENTS

**Trạng thái: COMPLETED / LOCKED**

530 hoàn thiện tầng **training orchestration** phía trên 503–508 và 528. 503–505 đã định nghĩa tensor/graph/executor; 506–508 định nghĩa model/checkpoint/dataset. 530 kết nối chúng thành một hệ thống experiment/training có thể chạy từ một GPU đến distributed cluster.

```text id="530arch"
Dataset / Version
       │
       ↓
Experiment Definition
       │
       ├── Model Config
       ├── Optimizer
       ├── Scheduler
       ├── Precision
       ├── Seed
       ├── Hardware
       └── Training Policy
       │
       ↓
Training Run
       │
 ┌─────┼──────────────┐
 ↓     ↓              ↓
Train Eval        Checkpoint
 │     │              │
 └─────┼──────────────┘
       ↓
 Metrics / Logs / Trace
       ↓
 Model Artifact
       ↓
 Evaluation 527
       ↓
 Registry / Serving 529
```

---

# EXPERIMENT

## 530.1 — Experiment

Experiment là definition, không phải execution.

```text
Experiment {
    ExperimentId
    Version
    Dataset
    Model
    Config
    Policy
}
```

## 530.2 — Run

Mỗi execution tạo một `RunId`.

## 530.3 — Run state

```text
Created
Queued
Preparing
Running
Paused
Checkpointing
Completed
Failed
Cancelled
```

## 530.4 — Immutable run identity

Run identity không thay đổi sau khi bắt đầu.

## 530.5 — Configuration snapshot

Exact configuration được snapshot.

## 530.6 — Dataset pinning

Training run phải pin exact dataset version.

## 530.7 — Model initialization

Model initialization source được record.

## 530.8 — Seed

All relevant random seeds được record.

## 530.9 — Environment

Hardware/software/toolchain được record.

## 530.10 — Provenance

Run lineage tích hợp 528.

---

# TRAINING LOOP

## 530.11 — Epoch

Epoch semantics explicit.

## 530.12 — Step

Training step identity.

## 530.13 — Microbatch

Microbatch identity.

## 530.14 — Gradient accumulation

Accumulation steps explicit.

## 530.15 — Forward

Forward execution.

## 530.16 — Loss

Loss computation.

## 530.17 — Backward

Autodiff/backward execution.

## 530.18 — Gradient

Gradient state.

## 530.19 — Optimizer

Optimizer state.

## 530.20 — Update

Parameter update atomic at step boundary.

---

# OPTIMIZER

## 530.21 — Optimizer abstraction

```text
Optimizer {
    init
    step
    zero_grad
    state
}
```

## 530.22 — SGD

Supported as baseline.

## 530.23 — Momentum

Momentum state.

## 530.24 — Adam-family

Adam/AdamW-style optimizers.

## 530.25 — Custom optimizer

User-defined optimizer supported.

## 530.26 — Optimizer state

State identity/version.

## 530.27 — Precision

Optimizer precision explicit.

## 530.28 — Gradient clipping

Norm/value clipping configurable.

## 530.29 — Weight decay

Weight decay semantics distinguish optimizer behavior from gradient modification.

## 530.30 — State checkpoint

Optimizer state included in training checkpoint when configured.

---

# LEARNING-RATE SCHEDULER

## 530.31 — Scheduler

Learning-rate schedule separate optimizer.

## 530.32 — Step-based

Per-step scheduling.

## 530.33 — Epoch-based

Per-epoch scheduling.

## 530.34 — Warmup

Warmup schedule.

## 530.35 — Decay

Linear/cosine/exponential/custom.

## 530.36 — Metric-driven

Reduce-on-plateau-style scheduler.

## 530.37 — Scheduler state

Checkpointed.

## 530.38 — Resume

Resume restores scheduler state.

## 530.39 — Configuration

Exact scheduler config recorded.

## 530.40 — Determinism

Schedule state cannot depend on unrecorded wall-clock state.

---

# PRECISION

## 530.41 — FP32

Supported baseline.

## 530.42 — FP16

Supported where device/backend supports.

## 530.43 — BF16

Supported where backend supports.

## 530.44 — Mixed precision

Forward/gradient/optimizer precision can differ.

## 530.45 — Loss scaling

Static/dynamic loss scaling.

## 530.46 — Accumulation precision

Explicit.

## 530.47 — Numerical policy

Strict/reproducible/fast modes.

## 530.48 — Overflow detection

Gradient overflow detection.

## 530.49 — NaN/Inf detection

Optional training diagnostics.

## 530.50 — Precision provenance

Checkpoint/model records numerical policy.

---

# DISTRIBUTED TRAINING

## 530.51 — Distributed topology

```text
Cluster
 └── Node
      └── Process
           └── Device
                └── Worker
```

## 530.52 — Data parallelism

Each worker processes different batches.

## 530.53 — Gradient synchronization

All-reduce/reduce-scatter/all-gather abstractions.

## 530.54 — Model parallelism

Model partitioning.

## 530.55 — Tensor parallelism

Tensor partitioning.

## 530.56 — Pipeline parallelism

Layer-stage partitioning.

## 530.57 — Hybrid parallelism

Combination.

## 530.58 — Collective identity

Collective operation has group/sequence identity.

## 530.59 — Collective ordering

Collective order must match required communicator semantics.

## 530.60 — Failure

Worker failure semantics explicit.

---

# DATA PIPELINE

## 530.61 — DataLoader

Integrates 508.

## 530.62 — Worker

Data-loading worker.

## 530.63 — Prefetch

Prefetch queue.

## 530.64 — Shuffle

Deterministic shuffle where configured.

## 530.65 — Distributed sampler

Partition dataset across workers.

## 530.66 — Epoch seed

Epoch-dependent seed explicit.

## 530.67 — Resume position

Checkpoint can restore data position when supported.

## 530.68 — Data pipeline state

Sampler/iterator state may be checkpointed.

## 530.69 — Backpressure

Training must not create unbounded prefetched samples.

## 530.70 — Data provenance

Batch references dataset version/sampler configuration.

---

# CHECKPOINT

## 530.71 — Checkpoint

Checkpoint contains sufficient state for configured resume semantics.

## 530.72 — Model weights

Weights.

## 530.73 — Optimizer state

Optional/required according to resume mode.

## 530.74 — Scheduler state

State.

## 530.75 — RNG state

Random states.

## 530.76 — Training position

Epoch/step/microbatch.

## 530.77 — Dataset state

Sampler/iterator position when reproducibility requires.

## 530.78 — Configuration

Training configuration snapshot.

## 530.79 — Model schema

Model/schema version.

## 530.80 — Integrity

Checksum/hash.

---

# CHECKPOINT STRATEGY

## 530.81 — Periodic

Checkpoint every N steps/time.

## 530.82 — Best-model

Best according to explicit metric.

## 530.83 — Latest

Latest successful checkpoint.

## 530.84 — Retention

Retention policy.

## 530.85 — Atomic save

Partial checkpoint cannot be reported complete.

## 530.86 — Async checkpoint

Possible when snapshot semantics guarantee consistency.

## 530.87 — Incremental checkpoint

Delta checkpoints optional.

## 530.88 — Sharded checkpoint

Large models can shard state.

## 530.89 — Resume compatibility

Checkpoint compatibility verified before load.

## 530.90 — Corruption

Corrupt checkpoint rejected.

---

# EXPERIMENT TRACKING

## 530.91 — Metric

```text
MetricPoint {
    run
    step
    name
    value
    timestamp?
}
```

## 530.92 — Scalar metrics

Loss/accuracy/etc.

## 530.93 — Histogram

Distribution metrics.

## 530.94 — Tensor metrics

Optional artifact references.

## 530.95 — Sample outputs

Evaluation examples.

## 530.96 — Hyperparameters

Exact config.

## 530.97 — Artifacts

Checkpoint/model/log/profile.

## 530.98 — Events

Training lifecycle events.

## 530.99 — Tags

Experiment metadata.

## 530.100 — Comparison

Run-to-run comparison.

---

# HYPERPARAMETER SEARCH

## 530.101 — Search space

```text
learning_rate ∈ ...
batch_size ∈ ...
dropout ∈ ...
```

## 530.102 — Grid

Grid search.

## 530.103 — Random

Random search.

## 530.104 — Bayesian

Bayesian optimization optional.

## 530.105 — Successive halving

Early resource allocation.

## 530.106 — Population methods

Optional evolutionary/population search.

## 530.107 — Search seed

Deterministic search seed.

## 530.108 — Budget

Trials/time/compute budget.

## 530.109 — Parallel trials

Concurrent trials.

## 530.110 — Trial identity

Each trial has RunId and parent ExperimentId.

---

# EARLY STOPPING

## 530.111 — Metric condition

Explicit monitored metric.

## 530.112 — Patience

Number of steps/epochs.

## 530.113 — Minimum improvement

Explicit threshold.

## 530.114 — Divergence detection

Training divergence condition.

## 530.115 — Resource limit

Hard timeout/compute limit.

## 530.116 — Manual stop

User cancellation.

## 530.117 — Safe checkpoint

Stopping should preserve latest valid checkpoint when configured.

## 530.118 — No hidden stop

Training must not silently stop due to undocumented heuristic.

## 530.119 — Stop reason

Stop reason recorded.

## 530.120 — Resume

Stopped run can resume if checkpoint sufficient.

---

# EVALUATION DURING TRAINING

## 530.121 — Validation schedule

Validation every N steps/epochs.

## 530.122 — Evaluation isolation

Evaluation dataset remains separate.

## 530.123 — Evaluation identity

References 527 EvaluationId.

## 530.124 — Evaluation artifacts

Results linked to training run.

## 530.125 — Best checkpoint

Can be selected using explicit validation metric.

## 530.126 — Test set

Test evaluation remains separate from training decisions when policy requires.

## 530.127 — Online evaluation

Can run asynchronously.

## 530.128 — Evaluation resource

Evaluation resource budget explicit.

## 530.129 — Evaluation failure

Training/evaluation failure policies separate.

## 530.130 — Provenance

Evaluation result references exact checkpoint.

---

# EXPERIMENT ORCHESTRATION

## 530.131 — Scheduler

Training jobs integrate 471.

## 530.132 — Queue

Training jobs have bounded resource-aware queues.

## 530.133 — Resource request

CPU/RAM/GPU/VRAM/NPU requirements explicit.

## 530134 — Placement

Scheduler chooses compatible worker.

## 530.135 — Affinity

GPU/NUMA affinity.

## 530.136 — Preemption

Optional explicit policy.

## 530.137 — Resume after preemption

Checkpoint-based resume.

## 530.138 — Retry

Retry policy.

## 530.139 — Retry identity

Retry remains linked to same logical experiment but gets execution identity.

## 530.140 — Failure classification

Infrastructure failure ≠ model failure ≠ data failure ≠ configuration failure.

---

# RESOURCE MANAGEMENT

## 530.141 — GPU memory

Track allocation/peak.

## 530.142 — CPU memory

Track.

## 530.143 — Storage

Checkpoint/data/cache storage quotas.

## 530.144 — Network

Distributed training bandwidth.

## 530.145 — Compute budget

CPU/GPU time.

## 530.146 — Power/energy

Optional hardware metric.

## 530.147 — Cost

Optional resource-cost metadata.

## 530.148 — Resource violation

Hard limit produces structured failure.

## 530.149 — Resource reservation

Scheduler integrates resource reservation.

## 530.150 — No hidden scaling

Training does not silently spawn unlimited workers.

---

# REPRODUCIBILITY

## 530.151 — Reproducible run

Exact configuration/data/toolchain/device/seed can reproduce where platform semantics permit.

## 530.152 — Deterministic algorithms

Use deterministic kernels when configured.

## 530.153 — Non-determinism

Sources of nondeterminism are recorded.

## 530.154 — Distributed order

Collective ordering and worker topology recorded.

## 530.155 — Data order

Sampler state/order recorded.

## 530.156 — RNG streams

Independent RNG streams identified.

## 530.157 — Floating point

Numerical mode recorded.

## 530.158 — Hardware differences

Different hardware may prevent bit-identical results.

## 530.159 — Reproduction classification

```text
BitIdentical
NumericallyEquivalent
BehaviorallyEquivalent
NotReproduced
Unknown
```

## 530.160 — No false reproducibility

Framework must not claim exact reproduction when relevant state is missing.

---

# TRAINING MONITORING

## 530.161 — Live status

Current epoch/step/state.

## 530.162 — Throughput

Samples/sec/tokens/sec.

## 530.163 — Utilization

CPU/GPU/device utilization.

## 530.164 — Memory

Current/peak memory.

## 530.165 — Data wait

Data pipeline stall.

## 530.166 — Communication

Distributed communication time.

## 530.167 — Checkpoint time

Checkpoint overhead.

## 530.168 — Validation time

Evaluation overhead.

## 530.169 — Critical path

Training critical-path analysis.

## 530.170 — Trace

Run trace integrates 475/481.

---

# FAILURE RECOVERY

## 530.171 — Data error

Malformed batch/data source failure.

## 530.172 — Device error

GPU/device failure.

## 530.173 — Worker failure

Distributed worker loss.

## 530.174 — Checkpoint failure

Checkpoint write failure.

## 530.175 — Network failure

Distributed communication failure.

## 530.176 — OOM

Out-of-memory classification.

## 530.177 — Numerical divergence

NaN/Inf/overflow.

## 530.178 — Configuration error

Invalid training setup.

## 530.179 — Recovery policy

Retry/resume/abort policy explicit.

## 530.180 — Failure provenance

Exact run/step/device/data references.

---

# MODEL EXPORT

## 530.181 — Successful run

Can produce model artifact.

## 530.182 — Export checkpoint

Training checkpoint → deployment model.

## 530.183 — Inference-only artifact

Optimizer/training state can be removed.

## 530.184 — Graph compilation

504/505 can compile deployment graph.

## 530.185 — Quantization

Post-training quantization can be explicit pipeline.

## 530.186 — Evaluation gate

Export can require explicit evaluation policy.

## 530.187 — Provenance

Model artifact references training run/dataset.

## 530.188 — Deployment compatibility

529 serving compatibility checked.

## 530.189 — Artifact hash

Export artifact hashed.

## 530.190 — Immutable release

Published model artifact immutable.

---

# AI INTROSPECTION

## 530.191 — Run query

```text
run(id)
```

## 530.192 — Config query

```text
config(run)
```

## 530.193 — Dataset query

```text
dataset(run)
```

## 530.194 — Checkpoint query

```text
checkpoints(run)
```

## 530.195 — Failure query

```text
failures(run)
```

## 530.196 — Resource query

```text
resources(run)
```

## 530.197 — Reproduction query

```text
reproduce(run)
```

## 530.198 — Compare

```text
compare(run_a, run_b)
```

## 530.199 — Lineage

```text
lineage(run)
```

## 530.200 — Optimization evidence

Training run có thể link tới 504/505 optimization reports.

---

# 530.201 — HARD INVARIANTS

1. Experiment khác Run.
2. Experiment có identity.
3. Experiment có version.
4. Run có identity.
5. Run state explicit.
6. Run configuration immutable sau start.
7. Dataset version được pin.
8. Model initialization được record.
9. Random seeds được record.
10. Environment được record.
11. Training provenance integrate 528.
12. Epoch semantics explicit.
13. Step identity explicit.
14. Microbatch identity explicit.
15. Gradient accumulation explicit.
16. Forward execution được track.
17. Loss được identify.
18. Backward execution được track.
19. Gradient state được manage.
20. Optimizer state được manage.
21. Parameter update có step boundary.
22. Optimizer là abstraction riêng.
23. SGD được hỗ trợ.
24. Momentum được hỗ trợ.
25. Adam-family được hỗ trợ.
26. Custom optimizer được hỗ trợ.
27. Optimizer state versioned.
28. Optimizer precision explicit.
29. Gradient clipping explicit.
30. Weight decay semantics explicit.
31. Optimizer state có thể checkpoint.
32. Scheduler tách optimizer.
33. Step-based scheduling được hỗ trợ.
34. Epoch-based scheduling được hỗ trợ.
35. Warmup được hỗ trợ.
36. Decay schedules được hỗ trợ.
37. Metric-driven scheduling được hỗ trợ.
38. Scheduler state checkpointed.
39. Resume restore scheduler state.
40. Scheduler config được record.
41. Scheduler không phụ thuộc hidden wall-clock state.
42. FP32 baseline được hỗ trợ.
43. FP16 được hỗ trợ khi backend cho phép.
44. BF16 được hỗ trợ khi backend cho phép.
45. Mixed precision được hỗ trợ.
46. Loss scaling được hỗ trợ.
47. Accumulation precision explicit.
48. Numerical policy được record.
49. Overflow detection có thể hỗ trợ.
50. NaN/Inf diagnostics có thể hỗ trợ.
51. Precision provenance được preserve.
52. Distributed topology explicit.
53. Data parallelism được hỗ trợ.
54. Gradient synchronization được hỗ trợ.
55. Model parallelism được hỗ trợ.
56. Tensor parallelism được hỗ trợ.
57. Pipeline parallelism được hỗ trợ.
58. Hybrid parallelism được hỗ trợ.
59. Collective identity được preserve.
60. Collective ordering semantics explicit.
61. Worker failure semantics explicit.
62. DataLoader integrate 508.
63. Data worker lifecycle explicit.
64. Prefetch được bounded.
65. Shuffle seed được preserve.
66. Distributed sampler được hỗ trợ.
67. Epoch seed được preserve.
68. Resume sampler state có thể hỗ trợ.
69. Data pipeline state được checkpoint khi cần.
70. Batch provenance được preserve.
71. Checkpoint identity explicit.
72. Model weights có thể checkpoint.
73. Optimizer state có thể checkpoint.
74. Scheduler state có thể checkpoint.
75. RNG state có thể checkpoint.
76. Training position có thể checkpoint.
77. Dataset state có thể checkpoint.
78. Config snapshot có thể checkpoint.
79. Model schema được record.
80. Checkpoint integrity được verify.
81. Periodic checkpoint được hỗ trợ.
82. Best checkpoint được hỗ trợ.
83. Latest checkpoint được hỗ trợ.
84. Retention policy explicit.
85. Checkpoint save atomic.
86. Async checkpoint chỉ khi snapshot consistent.
87. Incremental checkpoint có thể hỗ trợ.
88. Sharded checkpoint được hỗ trợ.
89. Checkpoint compatibility được verify.
90. Corrupt checkpoint bị reject.
91. Metric points có identity.
92. Scalar metrics được hỗ trợ.
93. Histogram metrics được hỗ trợ.
94. Tensor metrics có thể reference artifact.
95. Sample outputs được hỗ trợ.
96. Hyperparameters được record.
97. Artifacts được link.
98. Training events được record.
99. Tags được hỗ trợ.
100. Run comparison được hỗ trợ.
101. Search space được version.
102. Grid search được hỗ trợ.
103. Random search được hỗ trợ.
104. Bayesian optimization có thể hỗ trợ.
105. Successive halving có thể hỗ trợ.
106. Population methods có thể hỗ trợ.
107. Search seed được preserve.
108. Search budget explicit.
109. Parallel trials được hỗ trợ.
110. Trial có identity.
111. Early stopping metric explicit.
112. Patience explicit.
113. Minimum improvement explicit.
114. Divergence detection được hỗ trợ.
115. Resource limits có thể stop run.
116. Manual cancellation được hỗ trợ.
117. Safe checkpoint before stop có thể hỗ trợ.
118. Không có hidden training stop.
119. Stop reason được record.
120. Resume sau stop được hỗ trợ khi state đủ.
121. Validation schedule explicit.
122. Evaluation dataset được isolate.
123. Evaluation identity reference 527.
124. Evaluation artifacts link training run.
125. Best checkpoint selection rule explicit.
126. Test set policy có thể isolate khỏi training decisions.
127. Online evaluation có thể hỗ trợ.
128. Evaluation resource budget explicit.
129. Evaluation failure policy tách training failure.
130. Evaluation provenance references exact checkpoint.
131. Training jobs integrate scheduler 471.
132. Resource-aware queue được hỗ trợ.
133. CPU/RAM/GPU requirements explicit.
134. Worker placement được xác định.
135. GPU/NUMA affinity được hỗ trợ.
136. Preemption policy explicit.
137. Preempted run có thể resume.
138. Retry policy explicit.
139. Retry execution identity distinct.
140. Failure categories được distinguish.
141. GPU memory được track.
142. CPU memory được track.
143. Storage quota được track.
144. Network resource được track.
145. Compute budget được track.
146. Energy metric có thể hỗ trợ.
147. Cost metadata có thể hỗ trợ.
148. Resource violations có structured error.
149. Resource reservation được hỗ trợ.
150. Không có hidden worker spawning.
151. Reproducible execution được hỗ trợ.
152. Deterministic kernels có thể chọn.
153. Nondeterminism được record.
154. Distributed topology được record.
155. Data ordering được record.
156. RNG streams được identify.
157. Floating-point mode được record.
158. Hardware differences được preserve.
159. Reproduction state explicit.
160. Không false-claim bit-identical reproduction.
161. Live run status được expose.
162. Throughput được measure.
163. Device utilization được measure.
164. Memory được measure.
165. Data stalls được measure.
166. Communication time được measure.
167. Checkpoint overhead được measure.
168. Validation overhead được measure.
169. Critical path có thể analyze.
170. Training trace được hỗ trợ.
171. Data errors được classify.
172. Device errors được classify.
173. Worker errors được classify.
174. Checkpoint errors được classify.
175. Network errors được classify.
176. OOM được classify.
177. Numerical divergence được classify.
178. Configuration errors được classify.
179. Recovery policy explicit.
180. Failure provenance được preserve.
181. Successful run có thể export model.
182. Training checkpoint có thể convert deployment artifact.
183. Inference-only artifact có thể strip training state.
184. Deployment graph có thể compile.
185. Quantization có thể là explicit post-training stage.
186. Export evaluation gate có thể cấu hình.
187. Export model giữ training provenance.
188. Serving compatibility được verify.
189. Export artifact có hash.
190. Published model artifact immutable.
191. Run query được hỗ trợ.
192. Config query được hỗ trợ.
193. Dataset query được hỗ trợ.
194. Checkpoint query được hỗ trợ.
195. Failure query được hỗ trợ.
196. Resource query được hỗ trợ.
197. Reproduction query được hỗ trợ.
198. Run comparison được hỗ trợ.
199. Full lineage được hỗ trợ.
200. Optimization evidence có thể link 504/505.
201. Training state không được phụ thuộc hidden global mutable state.
202. Training retries không được tạo duplicate logical results mà không có identity.
203. Checkpoint restore không được silently thay đổi model/dataset/config semantics.
204. Distributed training không được giả định exactly-once communication nếu backend không cung cấp.
205. Numerical equivalence không được nhầm với bit identity.
206. Evaluation metrics không được tự động biến thành training objective.
207. Search system không được tự động chọn deployment model nếu không có explicit policy.
208. Dataset rights/restrictions từ 528 phải được enforce.
209. Model artifact phải trace được về exact training run.
210. **Axiom Training Orchestration phải biến training từ một vòng lặp script khó tái lập thành một execution graph có identity, checkpoint, provenance, resource control, distributed semantics, reproducibility và failure recovery rõ ràng; mọi quyết định tối ưu/search/deployment phải là policy explicit, không được ẩn trong trainer runtime.**

**BOOTSTRAP-530 hoàn tất / LOCKED.**

---

### Chuỗi tiếp theo

**`BOOTSTRAP-531 — AI MODEL OPTIMIZATION & COMPRESSION: PRUNING, DISTILLATION, LOW-RANK ADAPTATION, SPARSITY, WEIGHT SHARING, VOCABULARY COMPRESSION & DEPLOYMENT-AWARE MODEL TRANSFORMATION`**