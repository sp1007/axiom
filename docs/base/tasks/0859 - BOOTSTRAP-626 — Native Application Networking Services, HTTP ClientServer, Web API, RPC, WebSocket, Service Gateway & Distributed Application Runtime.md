Tiếp tục với **BOOTSTRAP-626** — mở rộng networking 609 lên tầng dịch vụ ứng dụng, nhưng không làm phình core network primitive.

:::writing{variant="document" id="74126" title="BOOTSTRAP-626 — Native Application Networking Services, HTTP Client/Server, Web API, RPC, WebSocket, Service Gateway & Distributed Application Runtime 5.0"}
# BOOTSTRAP-626 — Native Application Networking Services, HTTP Client/Server, Web API, RPC, WebSocket, Service Gateway & Distributed Application Runtime 5.0

**Status:** SPECIFIED  
**Layer:** Application Networking / Service Runtime  
**Depends on:** BOOTSTRAP-600 → 625

---

# 1. Purpose

BOOTSTRAP-609 established Axiom's low-level networking foundation:

- sockets;
- TCP/UDP;
- DNS;
- TLS boundary;
- network buffers;
- asynchronous network I/O.

BOOTSTRAP-626 builds the higher-level **application networking and distributed-service layer** above 609.

It provides:

- HTTP client;
- HTTP server;
- routing;
- middleware;
- request/response handling;
- Web API;
- WebSocket;
- RPC;
- service discovery;
- connection management;
- authentication hooks;
- authorization hooks;
- serialization integration;
- streaming;
- multipart/form-data;
- content negotiation;
- compression;
- retries;
- circuit breakers;
- rate limiting;
- service health;
- distributed tracing;
- API versioning;
- graceful shutdown;
- gateway/proxy primitives;
- reverse proxy;
- service-to-service communication;
- local and remote service abstraction.

The architecture must remain usable for:

```text
Desktop application
CLI tool
Web server
REST API
RPC service
Game backend
AI service
Microservice
Local IPC-like service
Embedded device
WASM host application
```

---

# 2. Core Principle

626 is an **application networking layer**, not a replacement for 609.

```text
Application
    │
    ▼
626 Application Networking
    │
    ├── HTTP
    ├── RPC
    ├── WebSocket
    ├── Gateway
    ├── Service Discovery
    └── API Services
    │
    ▼
609 Network Runtime
    │
    ▼
608 / 607
    │
    ▼
OS / Network Device
```

---

# 3. Non-Goals

626 does not mandate:

- REST;
- JSON;
- HTTP;
- microservices;
- service mesh;
- cloud infrastructure;
- centralized service discovery;
- distributed databases;
- Kubernetes;
- a particular RPC protocol;
- a particular authentication provider.

These are implementations/profiles above the core abstractions.

---

# 4. Design Goals

626 must provide:

1. low overhead;
2. type safety;
3. streaming;
4. async-first operation;
5. explicit cancellation;
6. bounded buffering;
7. predictable resource usage;
8. secure defaults;
9. protocol extensibility;
10. easy local development;
11. production scalability;
12. cross-platform behavior;
13. observability;
14. deterministic testing.

---

# 5. Layering

```text
┌──────────────────────────────────────┐
│ Application / Business Logic         │
├──────────────────────────────────────┤
│ Web API / RPC / Gateway              │
├──────────────────────────────────────┤
│ HTTP / WebSocket / Service Runtime   │
├──────────────────────────────────────┤
│ 626 Application Networking           │
├──────────────────────────────────────┤
│ 609 Sockets / DNS / TLS Transport    │
├──────────────────────────────────────┤
│ 607 Async + 608 Sync                 │
├──────────────────────────────────────┤
│ OS / Device                          │
└──────────────────────────────────────┘
```

---

# 6. Core Objects

```text
NetworkApplication
HttpClient
HttpServer
HttpRequest
HttpResponse
HttpHeaders
HttpBody
HttpRoute
HttpRouter
HttpMiddleware
HttpConnection
WebSocket
WebSocketServer
RpcClient
RpcServer
RpcMethod
RpcRequest
RpcResponse
Service
ServiceEndpoint
ServiceDiscovery
ServiceRegistry
Gateway
RateLimiter
CircuitBreaker
RetryPolicy
ApiSchema
```

---

# 7. Struct-Only Design

No classes are required.

Example:

```text
struct HttpRequest {
    method: HttpMethod
    uri: Uri
    headers: HttpHeaders
    body: HttpBody
}

fn HttpRequest.header(
    self: HttpRequest,
    name: HeaderName
) -> Option<StringView>
```

---

# 8. URI Model

626 uses a structured URI model.

```text
Uri {
    scheme
    authority
    path
    query
    fragment
}
```

---

# 9. URI Safety

URI parsing must reject malformed or ambiguous representations when used for security-sensitive operations.

---

# 10. HTTP Versions

Core support:

```text
HTTP/1.1
```

Optional providers:

```text
HTTP/2
HTTP/3
```

---

# 11. HTTP/1.1

626 provides:

- request parsing;
- response generation;
- persistent connections;
- chunked transfer;
- content length;
- connection management;
- trailers.

---

# 12. HTTP/2 Boundary

HTTP/2 is implemented as a transport/provider layer without changing the application request model.

---

# 13. HTTP/3 Boundary

HTTP/3 uses 609/transport-provider integration and does not alter application APIs.

---

# 14. HTTP Methods

Built-in:

```text
GET
POST
PUT
PATCH
DELETE
HEAD
OPTIONS
CONNECT
TRACE
```

Applications can represent extension methods.

---

# 15. HTTP Status

Typed status representation:

```text
HttpStatus {
    code: u16
}
```

with standard constants.

---

# 16. Headers

Headers use efficient case-insensitive lookup.

---

# 17. Header Storage

Implementation may use:

```text
small-vector
hash table
indexed representation
```

depending on header count.

---

# 18. Header Limits

Limits are configurable:

```text
max_header_count
max_header_bytes
max_header_name
max_header_value
```

---

# 19. Header Security

Reject:

- invalid control characters;
- ambiguous separators;
- malformed field names;
- unsafe line folding.

---

# 20. Request Body

Body abstraction supports:

```text
Empty
Bytes
Stream
File
Generated
```

---

# 21. Response Body

Same abstraction:

```text
Empty
Bytes
Stream
File
Generated
```

---

# 22. Streaming

Large payloads must not require full in-memory buffering.

---

# 23. Backpressure

Body streams integrate with 607 and 609 backpressure.

---

# 24. Zero-Copy

When possible:

```text
file → socket
```

uses 609 sendfile/splice-style primitives.

---

# 25. File Response

Example:

```text
HttpResponse.file(path)
```

may use zero-copy transport.

---

# 26. Memory Response

Small responses can use inline/owned buffers.

---

# 27. Body Limits

Servers must define maximum request-body limits.

---

# 28. Upload Streaming

Large uploads can stream directly to 611 storage.

---

# 29. Temporary Upload

626 may expose secure temporary upload streams.

---

# 30. Multipart

Support:

```text
multipart/form-data
multipart/mixed
```

through streaming parsers.

---

# 31. Multipart Limits

Each multipart section has configurable:

```text
max_size
max_headers
max_parts
```

---

# 32. Content Types

Typed `MediaType`.

Examples:

```text
application/json
application/octet-stream
text/plain
multipart/form-data
```

---

# 33. Content Negotiation

Server can negotiate:

- media type;
- encoding;
- language.

---

# 34. JSON

JSON support is an adapter built on 612.

It is not the canonical Axiom serialization format.

---

# 35. AXBIN

626 can transport AXBIN/AXBF from 612.

---

# 36. Binary API

Applications may expose:

```text
application/axiom-binary
```

or another registered media type.

---

# 37. Serialization Separation

HTTP knows only:

```text
bytes ↔ stream
```

Serialization belongs to 612 or higher-level API modules.

---

# 38. Compression

Content compression integrates with 613.

Supported providers may include:

```text
gzip
deflate
br
zstd
```

subject to provider availability.

---

# 39. Compression Bomb Protection

Decompression limits must account for:

```text
compressed_size
expanded_size
ratio
CPU_cost
```

---

# 40. HTTP Client

```text
HttpClient {
    request()
    get()
    post()
    send()
}
```

---

# 41. Connection Pool

Client maintains reusable connections.

---

# 42. Pool Key

Connection pools are keyed by:

```text
scheme
host
port
proxy
TLS policy
authentication context
HTTP version
```

---

# 43. Connection Limits

Limits:

```text
max_connections
max_idle
max_pending
```

---

# 44. Keep-Alive

Persistent connections are reused where protocol permits.

---

# 45. Connection Lifetime

Maximum lifetime and idle timeout are configurable.

---

# 46. DNS

609 provides DNS.

626 adds:

- connection-resolution integration;
- caching policy;
- endpoint selection.

---

# 47. Happy Eyeballs

Client may use 609 dual-stack connection strategy.

---

# 48. Redirects

Redirect handling is explicit.

Default policy:

```text
disabled or bounded
```

rather than unlimited following.

---

# 49. Redirect Security

Cross-origin redirects may require explicit policy.

---

# 50. Retry

Retry is not automatic for every HTTP request.

---

# 51. Retry Policy

```text
RetryPolicy {
    max_attempts
    backoff
    jitter
    retryable_statuses
    retryable_errors
}
```

---

# 52. Idempotency

Retry logic must consider HTTP method and application idempotency.

---

# 53. Idempotency Key

Applications can provide:

```text
Idempotency-Key
```

for operations designed to tolerate retries.

---

# 54. Timeout

Every network operation supports:

```text
connect_timeout
header_timeout
body_timeout
total_deadline
```

---

# 55. Cancellation

All async operations accept 607 cancellation tokens.

---

# 56. Request Context

```text
RequestContext {
    request_id
    trace_id
    deadline
    cancellation
    peer
    capabilities
}
```

---

# 57. Server

```text
HttpServer {
    bind()
    start()
    stop()
    serve()
}
```

---

# 58. Bind

Binding requires the appropriate 603 network capability.

---

# 59. Listen

Server lifecycle integrates with 605.

---

# 60. Graceful Shutdown

Server shutdown:

```text
stop accepting
    ↓
finish active requests
    ↓
deadline
    ↓
cancel remaining requests
    ↓
close connections
```

---

# 61. Connection Draining

Existing connections can drain during deployment.

---

# 62. Request Concurrency

Server limits concurrent requests.

---

# 63. Resource Governor

606 controls:

- connections;
- requests;
- body memory;
- worker tasks;
- sockets;
- bandwidth.

---

# 64. Router

```text
HttpRouter {
    route()
    group()
    mount()
    handle()
}
```

---

# 65. Route

Route consists of:

```text
method
path pattern
handler
metadata
```

---

# 66. Path Parameters

Example:

```text
/users/{id}
```

---

# 67. Typed Parameters

Route parameters may be decoded into typed values.

---

# 68. Query Parameters

Typed query parsing uses explicit schemas.

---

# 69. Route Matching

Router should avoid pathological backtracking.

---

# 70. Deterministic Matching

Route precedence is deterministic.

---

# 71. Route Conflict

Ambiguous routes are detected during registration when possible.

---

# 72. Middleware

Middleware pipeline:

```text
request
 ↓
middleware
 ↓
handler
 ↓
middleware
 ↓
response
```

---

# 73. Middleware Ordering

Order is explicit and deterministic.

---

# 74. Middleware Examples

Built-in boundaries:

```text
logging
tracing
authentication
authorization
compression
CORS
rate limiting
timeout
request ID
```

---

# 75. No Hidden Middleware

Framework must not inject security-sensitive behavior without configuration.

---

# 76. Error Handler

Unhandled request errors map to structured HTTP responses.

---

# 77. Error Model

Internal errors must not automatically expose stack traces or secrets.

---

# 78. Problem Details

626 can expose structured error responses similar to RFC problem-details semantics.

---

# 79. API Schema

Higher-level APIs may declare:

```text
ApiSchema
ApiEndpoint
ApiParameter
ApiResponse
ApiError
```

---

# 80. Schema Source

Schemas can be generated from Axiom declarations.

---

# 81. API Metadata

Compiler can emit:

```text
.axapi
```

metadata.

---

# 82. OpenAPI Boundary

OpenAPI import/export is optional.

It does not define the native API model.

---

# 83. API Versioning

Supported patterns:

```text
URI version
header version
media-type version
service version
```

---

# 84. Version Compatibility

API schema may specify:

```text
introduced
deprecated
removed
```

---

# 85. Deprecation

Deprecated endpoints remain functional according to declared compatibility policy.

---

# 86. RPC

RPC provides typed remote function invocation.

---

# 87. RPC Core

```text
RpcService
RpcMethod
RpcClient
RpcServer
RpcRequest
RpcResponse
```

---

# 88. RPC Method

```text
RpcMethod {
    service
    name
    request_type
    response_type
    streaming_mode
}
```

---

# 89. Streaming Modes

```text
Unary
ServerStream
ClientStream
Bidirectional
```

---

# 90. Serialization

RPC uses 612 schemas.

---

# 91. Schema Fingerprint

RPC messages include schema/type fingerprints where required.

---

# 92. Compatibility

Backward-compatible schema evolution follows 612.

---

# 93. RPC Transport

Transport may be:

```text
HTTP/1.1
HTTP/2
HTTP/3
Unix socket
TCP
IPC transport
```

---

# 94. Local RPC

RPC may operate over local transports.

---

# 95. Remote RPC

Remote RPC uses 609 network transport.

---

# 96. Authentication

RPC authentication integrates with 610/603.

---

# 97. Authorization

Method invocation requires appropriate capability/policy.

---

# 98. Service Identity

Remote services have:

```text
ServiceId
PublisherId
Endpoint
Identity
```

---

# 99. Service Discovery

```text
ServiceDiscovery {
    resolve()
    watch()
}
```

---

# 100. Discovery Providers

Possible providers:

```text
StaticConfig
LocalRegistry
DNS
mDNS
EnterpriseRegistry
CustomProvider
```

---

# 101. Static Discovery

Simplest mode:

```text
service.image = https://10.0.0.5:8443
```

---

# 102. Dynamic Discovery

Provider may return multiple endpoints.

---

# 103. Endpoint Selection

Selection can consider:

- availability;
- protocol;
- target;
- locality;
- priority.

---

# 104. No Implicit Trust

Discovery result does not automatically grant trust.

---

# 105. Endpoint Authentication

Endpoint identity is independently validated.

---

# 106. Service Health

Health information can be consumed from 605/service APIs.

---

# 107. Health Check

Optional endpoints:

```text
/health
/ready
```

or RPC equivalents.

---

# 108. Readiness

A service should not receive production traffic before readiness.

---

# 109. Circuit Breaker

```text
Closed
Open
HalfOpen
```

---

# 110. Circuit Breaker Policy

Tracks failures/timeouts according to configurable thresholds.

---

# 111. No Global Failure State

Circuit breakers are scoped by service/endpoint/policy.

---

# 112. Bulkhead

Resource isolation may limit concurrent calls to a dependency.

---

# 113. Rate Limiter

Supports:

```text
fixed window
sliding window
token bucket
leaky bucket
```

where appropriate.

---

# 114. Rate-Limit Scope

Can be:

```text
global
service
route
client
identity
IP
capability
```

---

# 115. Distributed Rate Limits

Distributed rate limiting requires an external coordination service and is not part of the mandatory runtime.

---

# 116. Authentication Boundary

626 defines authentication interfaces, not one mandatory identity system.

---

# 117. Authentication Providers

Possible providers:

```text
TLS client certificate
API key
Bearer token
signed request
OS identity
custom provider
```

---

# 118. Credential Handling

Credentials use 601/610.

---

# 119. Authorization

Authorization evaluates:

```text
identity
resource
operation
request context
capabilities
policy
```

---

# 120. Capability Model

Network capability remains the fundamental authority.

Application-level authorization cannot bypass 603.

---

# 121. Anonymous Access

Explicitly allowed only by application policy.

---

# 122. Authentication Failure

Returns a structured authorization error without leaking credential details.

---

# 123. WebSocket

```text
WebSocket {
    connect()
    send()
    receive()
    close()
}
```

---

# 124. WebSocket Server

HTTP upgrade establishes WebSocket connection.

---

# 125. WebSocket Frames

Supports:

```text
Text
Binary
Ping
Pong
Close
```

---

# 126. Message Limits

Configurable:

```text
max_frame
max_message
max_queue
```

---

# 127. Backpressure

WebSocket send buffers are bounded.

---

# 128. WebSocket Cancellation

Close/cancel integrates with 607.

---

# 129. WebSocket Security

Origin and authentication policy are explicit.

---

# 130. Server-Sent Events

Optional higher-level streaming API:

```text
EventStream
```

---

# 131. Streaming Response

Streaming HTTP response remains available without WebSocket.

---

# 132. Server Push

No mandatory application-level push mechanism beyond explicit streaming APIs.

---

# 133. Reverse Proxy

626 can provide:

```text
Gateway
ReverseProxy
ForwardProxy
```

as optional services.

---

# 134. Reverse Proxy

Maps:

```text
public route
    ↓
backend service
```

---

# 135. Proxy Streaming

Proxy should stream request/response bodies without unnecessary buffering.

---

# 136. Header Policy

Proxy must explicitly define which headers are forwarded.

---

# 137. Hop-by-Hop Headers

Hop-by-hop headers must not be forwarded incorrectly.

---

# 138. Proxy Timeouts

Separate:

```text
upstream_connect
upstream_header
upstream_body
downstream
```

timeouts.

---

# 139. Gateway

Gateway combines:

```text
routing
authentication
authorization
rate limiting
load balancing
observability
```

---

# 140. Load Balancing

Optional algorithms:

```text
round_robin
least_connections
weighted
random
consistent_hash
```

---

# 141. Load-Balancer State

State is scoped to the gateway instance unless an external coordinator is configured.

---

# 142. Health-Aware Routing

Unavailable endpoints can be temporarily removed from selection.

---

# 143. Retry + Load Balancing

Retry policies must avoid uncontrolled retry amplification.

---

# 144. Retry Budget

Gateway may enforce a global retry budget.

---

# 145. Request Hedging

Hedged requests are optional and disabled by default.

---

# 146. Distributed Tracing

626 integrates with 602 spans.

---

# 147. Trace Context

Trace IDs can propagate through standard request metadata.

---

# 148. Trace Security

Trace metadata must not contain secrets.

---

# 149. Correlation

Request context can contain:

```text
request_id
trace_id
span_id
```

---

# 150. Metrics

Built-in metrics:

```text
requests
responses
latency
status
connections
bytes
retries
timeouts
errors
active_streams
```

---

# 151. Cardinality

Metrics must avoid uncontrolled label cardinality.

---

# 152. Logging

602 structured logs receive:

```text
route
method
status
duration
request_id
trace_id
```

---

# 153. Sensitive Data

Headers such as authorization/cookies must be redacted.

---

# 154. Body Logging

Body logging is disabled by default.

---

# 155. Diagnostic Sampling

Request tracing/logging can be sampled.

---

# 156. Server Errors

5xx errors are observable without exposing internal details to clients.

---

# 157. Client Errors

4xx responses remain application-visible structured results.

---

# 158. HTTP Cache

Optional client/server cache primitives.

---

# 159. Cache-Control

HTTP cache headers are preserved according to protocol rules.

---

# 160. Application Cache

Higher-level response caching may use 612/613.

---

# 161. ETag

Client/server APIs expose ETag/If-None-Match.

---

# 162. Conditional Requests

Supports:

```text
If-Match
If-None-Match
If-Modified-Since
If-Unmodified-Since
```

where applicable.

---

# 163. Range Requests

Servers can support byte ranges for large resources.

---

# 164. Range Streaming

Range responses integrate with 611 file storage.

---

# 165. CORS

CORS is an explicit server policy.

---

# 166. Origin

Origin parsing is structured and normalized.

---

# 167. CSRF

626 may expose CSRF protection primitives but cannot infer application-specific state semantics.

---

# 168. Cookie

Cookie parsing/storage is optional.

---

# 169. Cookie Security

APIs expose:

```text
Secure
HttpOnly
SameSite
Domain
Path
Expires
MaxAge
```

---

# 170. Cookie Jar

Client cookie storage is opt-in.

---

# 171. Session

Session management belongs above the transport layer.

---

# 172. Authentication Tokens

Tokens are opaque application credentials.

---

# 173. Secret Redaction

Tokens never appear in normal diagnostics.

---

# 174. Request Size

Server request-size policy is mandatory.

---

# 175. Response Size

Client response limits are configurable.

---

# 176. Slowloris Protection

Server can enforce:

```text
header deadline
minimum receive rate
connection limits
```

---

# 177. Idle Connection Protection

Idle timeout limits resource exhaustion.

---

# 178. Connection Flood

606 quotas limit connection counts.

---

# 179. File Descriptor Protection

609/606 enforce FD/socket budgets.

---

# 180. Thread Protection

Server cannot spawn unbounded threads per request.

---

# 181. Async Request Execution

Default server execution uses 607 tasks.

---

# 182. Blocking Handler

Blocking handlers must use an explicit blocking executor.

---

# 183. UI Integration

GUI applications may expose HTTP/RPC services without blocking 619 UI execution.

---

# 184. Desktop Local Service

A desktop application may expose:

```text
127.0.0.1:port
```

subject to explicit 603 policy.

---

# 185. Localhost Security

Binding localhost does not automatically mean trusted access.

Authentication may still be required.

---

# 186. Unix Socket

Local services can use Unix domain sockets or Windows equivalent through 609.

---

# 187. Local Service Discovery

Application-local service discovery can use 604/605 or static configuration.

---

# 188. IPC vs HTTP

For same-machine structured communication, 604 remains the lower-level IPC mechanism.

626 should not force HTTP where native IPC is more appropriate.

---

# 189. RPC over IPC

626 RPC can use 604 transports.

---

# 190. Transport Independence

RPC API should not expose transport-specific details unless explicitly requested.

---

# 191. Transport Metadata

Low-level transport metadata remains accessible through a controlled context object.

---

# 192. Protocol Negotiation

Services can negotiate supported protocol versions.

---

# 193. Version Mismatch

Version mismatch produces a structured compatibility error.

---

# 194. API Compatibility

Schema compatibility is checked through 612 fingerprints.

---

# 195. Code Generation

Compiler may generate:

```text
client stubs
server adapters
schema descriptors
documentation
```

from API declarations.

---

# 196. Generated Client

Example:

```text
client = ImageServiceClient.connect(endpoint)

result = await client.resize(request)
```

---

# 197. Generated Server

Example:

```text
service ImageService {
    resize(ImageResizeRequest) -> ImageResizeResponse
}
```

---

# 198. Struct-Only Service Definition

Generated runtime remains struct/function based.

---

# 199. No Required Reflection

RPC metadata can be compiler-generated.

---

# 200. Dynamic RPC

A dynamic schema API may exist for tooling, gateways and scripting.

It is not required for ordinary compiled calls.

---

# 201. RPC Dispatch

Dispatch uses numeric method IDs where possible.

---

# 202. Method ID

Method identity:

```text
service_id
method_id
schema_fingerprint
```

---

# 203. Name Resolution

Human-readable method names are metadata.

---

# 204. Fast Path

Known RPC methods should avoid dynamic string lookup on the hot path.

---

# 205. Streaming RPC

Streaming uses bounded channels from 608.

---

# 206. Flow Control

RPC streams propagate backpressure end-to-end.

---

# 207. Cancellation

Remote cancellation is best-effort and deadline-aware.

---

# 208. Deadline Propagation

Incoming deadlines may be propagated to downstream calls.

---

# 209. Deadline Clamping

A service must not extend a caller's deadline arbitrarily.

---

# 210. Retry Propagation

Retries are not automatically propagated.

---

# 211. Distributed Failure

RPC must expose:

```text
timeout
unavailable
cancelled
protocol_error
authentication_error
authorization_error
transport_error
remote_error
```

---

# 212. Exactly Once

626 does not promise distributed exactly-once execution.

---

# 213. At-Least-Once

Retries may produce duplicate execution.

---

# 214. Idempotency

Applications must explicitly define idempotent operations.

---

# 215. Transaction

Distributed transactions are outside 626 core.

---

# 216. Saga Boundary

Higher-level workflow systems may build sagas on top of RPC.

---

# 217. Service Registry

Registry API:

```text
register()
unregister()
resolve()
watch()
```

---

# 218. Service Lease

Dynamic registration may use leases.

---

# 219. Lease Renewal

Failed renewal causes expiration.

---

# 220. Service Identity

Registration does not prove endpoint identity; authentication still applies.

---

# 221. DNS Discovery

DNS-based discovery can use SRV records.

---

# 222. mDNS

Local-network discovery may use mDNS providers.

---

# 223. Static Discovery

Static discovery remains the simplest deterministic mode.

---

# 224. Service Mesh Boundary

Service mesh integration is optional.

---

# 225. Proxy Mesh

626 can operate behind an external sidecar/proxy without requiring one.

---

# 226. No Mandatory Sidecar

Axiom applications must run correctly without service-mesh infrastructure.

---

# 227. Distributed Configuration

601 remains responsible for configuration.

626 consumes configuration snapshots.

---

# 228. Secrets

601/610 manage credentials.

---

# 229. State

600 handles application checkpoints.

Network connections are not generally checkpointable.

---

# 230. Recovery

On application restore, services reconnect rather than restoring stale sockets.

---

# 231. Supervision

605 supervises long-running network services.

---

# 232. Resource Governance

606 limits networking resources.

---

# 233. Scheduling

607 handles network tasks.

---

# 234. Synchronization

608 handles queues and shared state.

---

# 235. Security

603 controls network capabilities.

---

# 236. Storage

611 handles streamed uploads/downloads.

---

# 237. Serialization

612 handles RPC and structured payloads.

---

# 238. Package

613 provides compression and optional protocol/resource packaging.

---

# 239. Extensions

623 can provide protocol/service extensions.

---

# 240. Scripting

624 can consume HTTP/RPC APIs under explicit capabilities.

---

# 241. GUI

619/622 can provide API administration interfaces.

---

# 242. Compiler Metadata

Compiler may emit:

```text
.axapi
.axrpc
.axservice
```

---

# 243. API Metadata

Metadata contains:

```text
service
method
request
response
version
auth requirements
streaming
```

---

# 244. Static Validation

Compiler validates:

- request/response types;
- schema compatibility;
- route conflicts;
- method IDs.

---

# 245. Link-Time Validation

Linker verifies generated service references.

---

# 246. Dead Stripping

Unused protocol providers and middleware are removable.

---

# 247. Minimal HTTP Client

Application that only performs HTTP GET should not link:

```text
server
WebSocket
RPC
gateway
```

unless used.

---

# 248. Minimal RPC

Application using only local RPC should not require HTTP.

---

# 249. Minimal Server

A small server can contain:

```text
TCP
HTTP/1.1
router
handler
```

without full distributed runtime.

---

# 250. Memory Allocation

Hot paths should use reusable buffers and bounded pools.

---

# 251. Allocation-Free Parsing

Common HTTP header/request parsing paths should support allocation-minimized operation.

---

# 252. Buffer Pools

626 can use 611/609-compatible buffer pools.

---

# 253. Scatter/Gather

Large network operations can use vectored I/O.

---

# 254. File Streaming

File responses should avoid unnecessary copies.

---

# 255. TLS Streaming

TLS remains transparent to application streams.

---

# 256. HTTP/2 Multiplexing

Multiple requests may share a connection without changing application APIs.

---

# 257. HTTP/3 Multiplexing

Same application model.

---

# 258. Connection Migration

HTTP/3-specific migration remains transport/provider behavior.

---

# 259. Protocol Errors

Malformed protocol input must terminate only the affected connection/request where possible.

---

# 260. Parser Fuzzing

HTTP parsers must be fuzz tested.

---

# 261. Request Smuggling

Parser behavior must reject ambiguous framing combinations.

---

# 262. Response Splitting

Header serialization must reject control characters.

---

# 263. Host Validation

Server can validate Host/authority according to configured policy.

---

# 264. DNS Rebinding

Client security policy may restrict sensitive services from arbitrary DNS resolution.

---

# 265. SSRF Boundary

Applications performing server-side outbound requests must explicitly configure allowed destinations where security requires it.

---

# 266. Redirect SSRF

Redirect targets must be revalidated against outbound network policy.

---

# 267. Proxy SSRF

Proxy destination policy is independently enforced.

---

# 268. URL Credentials

Credentials embedded in URLs are discouraged and must not appear in logs.

---

# 269. Certificate Validation

610 performs TLS certificate validation.

---

# 270. Hostname Validation

TLS provider validates hostname unless explicitly overridden by a trusted policy.

---

# 271. Insecure TLS

Insecure certificate bypass requires an explicit development/testing capability.

---

# 272. Production Policy

Production profile can forbid TLS bypass entirely.

---

# 273. API Keys

API key storage uses 601 secrets.

---

# 274. Bearer Tokens

Bearer tokens are represented as secret values.

---

# 275. Mutual TLS

mTLS uses 610 keys/certificates.

---

# 276. Web Authentication

Higher-level authentication providers can integrate with 610.

---

# 277. Authorization Policy

Policy is evaluated before handler execution where possible.

---

# 278. Capability Attenuation

Request handlers receive only required capability scopes.

---

# 279. Plugin Services

623 plugins cannot automatically expose network services without declared capabilities.

---

# 280. Script Services

624 scripts cannot open network listeners unless explicitly granted.

---

# 281. Audit

Security-sensitive service operations can generate 602 audit events.

---

# 282. Health Diagnostics

626 exposes:

```text
active connections
pending requests
latency
error rate
pool utilization
```

---

# 283. Per-Route Metrics

Optional route metrics are supported.

---

# 284. High Cardinality

User-provided path values must not automatically become metric labels.

---

# 285. Request Sampling

Tracing can sample requests according to policy.

---

# 286. Performance Targets

Target goals:

```text
low-overhead request dispatch
bounded per-request allocations
zero-copy streaming where possible
O(1)-average route dispatch for common routers
bounded connection memory
no mandatory global lock
```

---

# 287. Concurrency

Each connection can be handled asynchronously.

---

# 288. Worker Scaling

Server worker count integrates with 607.

---

# 289. NUMA

Large servers may use NUMA-aware worker assignment.

---

# 290. CPU Affinity

606 controls CPU affinity.

---

# 291. Priority

Network workers cannot self-elevate priority.

---

# 292. Blocking Operations

Blocking filesystem/CPU work must use explicit worker pools.

---

# 293. Shutdown

Shutdown integrates with 605.

---

# 294. Service Activation

Server may be:

```text
AlwaysOn
OnDemand
Manual
DependencyTriggered
```

---

# 295. Readiness

Listener can remain unpublished until application readiness.

---

# 296. Endpoint Publication

Endpoint publication occurs only after:

```text
security initialized
dependencies ready
server bound
health ready
```

---

# 297. Failure Recovery

Failed server instances can be restarted by 605.

---

# 298. Connection Recovery

Clients can reconnect according to explicit policy.

---

# 299. Reconnection Backoff

Bounded exponential backoff with jitter.

---

# 300. Reconnect Storm Protection

Client libraries enforce retry budgets.

---

# 301. Distributed Thundering Herd

Service discovery changes should not cause unlimited synchronized reconnects.

---

# 302. Deterministic Test Runtime

626 provides:

```text
FakeTransport
FakeDns
FakeClock
FakeRepository
FakeServiceDiscovery
```

where appropriate.

---

# 303. HTTP Test Server

Tests can run an in-process server without external network dependencies.

---

# 304. Loopback Transport

Client/server tests may use an in-memory transport.

---

# 305. Protocol Golden Tests

HTTP/RPC serialization has deterministic golden tests.

---

# 306. Fuzzing

Required fuzz targets:

```text
URI
headers
HTTP parser
chunked encoding
multipart
WebSocket frames
RPC framing
schema decoding
proxy headers
```

---

# 307. Fault Injection

Inject:

- connection reset;
- timeout;
- DNS failure;
- TLS failure;
- partial read;
- partial write;
- malformed packet;
- server crash;
- client cancellation;
- disk full during upload.

---

# 308. Race Testing

Concurrent connection/pool/router tests must be race tested.

---

# 309. Load Testing

Benchmark:

```text
requests/sec
latency
memory/request
connection scalability
stream throughput
RPC throughput
```

---

# 310. Determinism

Routing and generated API metadata must be deterministic.

---

# 311. ABI

Public binary service APIs use stable generated ABI boundaries.

---

# 312. FFI

Foreign HTTP/RPC providers can implement defined interfaces.

---

# 313. Native Backend

Core implementation may use:

```text
Windows
Linux
macOS
Android
iOS
WASM host
Embedded
```

---

# 314. WASM

Browser WASM cannot open arbitrary sockets; 626 maps HTTP/WebSocket operations to host/browser APIs.

---

# 315. WASM Capability

Network access remains host-controlled.

---

# 316. Mobile

Background network execution follows platform lifecycle constraints.

---

# 317. Embedded

Minimal profiles may expose only TCP/UDP or a custom transport.

---

# 318. Desktop

Desktop applications can use both client and server functionality.

---

# 319. Server

Dedicated server builds can strip GUI/media/device layers.

---

# 320. Binary Size

Unused protocol providers are dead-stripped.

---

# 321. No Mandatory Runtime Daemon

HTTP/RPC does not require a global Axiom daemon.

---

# 322. No Mandatory Service Mesh

Distributed applications can operate directly.

---

# 323. No Mandatory Registry

Service endpoints may come from static configuration.

---

# 324. Application Composition

Axiom applications may combine:

```text
GUI
HTTP client
RPC client
HTTP server
WebSocket
local IPC
```

in one process.

---

# 325. Security Boundary

The complete request path is:

```text
OS
 ↓
603 capability
 ↓
609 socket
 ↓
610 TLS
 ↓
626 protocol
 ↓
authentication
 ↓
authorization
 ↓
application handler
```

---

# 326. Error Propagation

Errors remain typed from:

```text
transport
protocol
serialization
authentication
authorization
application
```

---

# 327. No Exception Requirement

Axiom networking does not require exceptions.

---

# 328. Result-Based API

Preferred:

```text
Result<T, NetworkError>
```

---

# 329. Error Context

Errors contain structured context without sensitive payloads.

---

# 330. API Example

```text
fn get_user(
    client: HttpClient,
    id: UserId,
    cancel: CancelToken
) async -> Result<User, ApiError> {

    let response =
        await client.get("/users/{id}".format(id), cancel)?

    let body =
        await response.body.read_all()?

    return User.decode_json(body)?
}
```

---

# 331. Server Example

```text
fn get_user(
    ctx: RequestContext,
    id: UserId
) async -> Result<HttpResponse, ApiError> {

    let user = await UserStore.find(id)?

    return HttpResponse.json(user)
}
```

---

# 332. RPC Example

```text
service UserService {
    get_user(UserRequest) -> UserResponse
}
```

Generated client:

```text
let user =
    await user_client.get_user(request)?
```

---

# 333. WebSocket Example

```text
let socket =
    await WebSocket.connect(url)?

await socket.send_text("hello")?

while true {
    let message = await socket.receive()?
    handle(message)
}
```

---

# 334. Gateway Example

```text
gateway.route("/api/{path}")
    .authenticate(auth)
    .rate_limit(policy)
    .proxy(users_service)
```

---

# 335. Architecture Invariants

1. 609 remains the transport foundation.
2. 626 never bypasses 603.
3. TLS uses 610.
4. Serialization uses 612.
5. Compression uses 613.
6. Async uses 607.
7. synchronization uses 608.
8. resource limits use 606.
9. supervision uses 605.
10. diagnostics use 602.
11. configuration uses 601.
12. state uses 600.
13. IPC remains available through 604.
14. HTTP is not mandatory for RPC.
15. RPC is not mandatory for HTTP.
16. REST is not mandatory.
17. JSON is not canonical.
18. Streaming is first-class.
19. Backpressure is mandatory.
20. Request sizes are bounded.
21. Connection counts are bounded.
22. Retry is explicit.
23. Distributed exactly-once is not promised.
24. Authentication is explicit.
25. Authorization is explicit.
26. Capability authority comes from 603.
27. Credentials use secret handling.
28. Body logging is disabled by default.
29. Service discovery does not imply trust.
30. Localhost does not imply trusted caller.
31. Redirects are bounded.
32. Cross-origin redirects can be restricted.
33. Update/service configuration remains external.
34. No mandatory service mesh.
35. No mandatory registry.
36. No mandatory daemon.
37. No mandatory cloud.
38. Minimal applications can strip unused layers.
39. APIs are struct/function based.
40. Generated RPC APIs need not use reflection.
41. Hot paths minimize allocation.
42. Blocking work is isolated.
43. Shutdown is graceful.
44. Readiness precedes endpoint publication.
45. Crash recovery uses 605.
46. Network connections are not checkpointed.
47. Recovery reconnects instead.
48. Protocol parsers are fuzz-tested.
49. Security-sensitive parsing is deterministic.
50. Native applications remain fully offline-capable.

---

# 336. Acceptance Criteria

### HTTP
1. HTTP/1.1 client.
2. HTTP/1.1 server.
3. HTTP/2 provider boundary.
4. HTTP/3 provider boundary.
5. request parsing.
6. response parsing.
7. headers.
8. body streams.
9. chunked encoding.
10. trailers.
11. persistent connections.
12. connection pooling.
13. redirect policy.
14. timeout.
15. cancellation.
16. request limits.
17. response limits.
18. multipart.
19. range requests.
20. conditional requests.

### Routing
21. route registration.
22. path parameters.
23. query parameters.
24. typed parameters.
25. deterministic precedence.
26. conflict detection.
27. route groups.
28. middleware.
29. middleware ordering.
30. error handling.

### Streaming
31. streaming upload.
32. streaming download.
33. bounded buffers.
34. backpressure.
35. zero-copy file response.
36. vectored I/O.
37. file streaming.
38. cancellation.
39. deadline propagation.
40. flow control.

### RPC
41. typed RPC.
42. unary.
43. server streaming.
44. client streaming.
45. bidirectional streaming.
46. schema fingerprints.
47. generated clients.
48. generated servers.
49. method IDs.
50. transport independence.
51. local RPC.
52. remote RPC.
53. authentication.
54. authorization.
55. cancellation.
56. deadline.
57. typed errors.
58. compatibility checks.
59. retry policy.
60. idempotency support.

### WebSocket
61. client.
62. server.
63. text.
64. binary.
65. ping/pong.
66. close.
67. frame limits.
68. message limits.
69. backpressure.
70. cancellation.

### Services
71. service abstraction.
72. endpoint abstraction.
73. static discovery.
74. DNS discovery.
75. mDNS provider.
76. custom discovery.
77. service registration.
78. lease.
79. health.
80. readiness.
81. endpoint authentication.
82. circuit breaker.
83. bulkhead.
84. retry budget.
85. reconnect.

### Security
86. network capability.
87. TLS integration.
88. certificate validation.
89. credential isolation.
90. auth provider.
91. authorization.
92. localhost policy.
93. redirect validation.
94. SSRF policy boundary.
95. request-size limits.
96. slow-client protection.
97. connection limits.
98. secret redaction.
99. safe logging.
100. parser fuzzing.

### Gateway
101. reverse proxy.
102. streaming proxy.
103. header policy.
104. load balancing.
105. health-aware routing.
106. rate limiting.
107. retry budget.
108. CORS.
109. origin policy.
110. proxy timeout.

### Observability
111. request metrics.
112. connection metrics.
113. route metrics.
114. tracing.
115. correlation IDs.
116. structured logs.
117. sensitive-data redaction.
118. diagnostics.
119. health.
120. fault injection.

### Runtime
121. scheduler integration.
122. synchronization integration.
123. resource governor.
124. service supervision.
125. configuration.
126. state/recovery.
127. package integration.
128. extension integration.
129. scripting integration.
130. compiler metadata.

### Cross-platform
131. Windows.
132. Linux.
133. macOS.
134. Android.
135. iOS.
136. WASM.
137. embedded.
138. local IPC.
139. native sockets.
140. host-network boundary.

### Performance
141. bounded allocation.
142. connection pooling.
143. buffer pooling.
144. zero-copy.
145. async-first server.
146. no mandatory global lock.
147. scalable worker model.
148. dead stripping.
149. minimal HTTP client.
150. minimal RPC client.

---

# 337. Final Architecture

```text
                       APPLICATION
                            │
              ┌─────────────┴─────────────┐
              │                           │
          Web API                        RPC
              │                           │
              └─────────────┬─────────────┘
                            │
                  ┌─────────┴─────────┐
                  │       626         │
                  │ Application Net   │
                  ├───────────────────┤
                  │ HTTP              │
                  │ WebSocket         │
                  │ Router             │
                  │ Middleware         │
                  │ Gateway            │
                  │ Discovery          │
                  │ Rate Limit         │
                  │ Circuit Breaker    │
                  │ Observability      │
                  └─────────┬─────────┘
                            │
                     ┌──────┴──────┐
                     │     609     │
                     │   Network   │
                     └──────┬──────┘
                            │
                  ┌─────────┼─────────┐
                  ▼         ▼         ▼
                607       608       610
             Scheduler    Sync       TLS
                  │         │         │
                  └─────────┼─────────┘
                            ▼
                           OS
```

---

# 338. Minimal Profiles

## AXNET-MIN

```text
TCP/UDP
DNS
```

Provided by 609.

## AXHTTP-CLIENT

```text
HTTP/1.1
TLS
DNS
async
```

## AXHTTP-SERVER

```text
HTTP/1.1
router
middleware
async
```

## AXRPC

```text
612 schema
RPC
streaming
transport
```

## AXWEB

```text
HTTP
WebSocket
Web API
```

## AXSERVER

```text
HTTP
RPC
WebSocket
Gateway
Observability
```

Unused modules are dead-stripped.

---

# 339. Final Boundary

Axiom now has a clean separation:

```text
609
Low-level network transport

610
Cryptographic transport

626
Application network protocols and services
```

This prevents the fundamental socket layer from becoming overloaded with framework concerns.

---

# 340. Task Completion

**BOOTSTRAP-626 — COMPLETE**

**Next queued task: BOOTSTRAP-627 — Native Distributed Systems Runtime: Service Mesh Boundary, Distributed Coordination, Leases, Membership, Leader Election, Distributed Locks, Consensus Boundary & Cluster Runtime 5.0**
:::