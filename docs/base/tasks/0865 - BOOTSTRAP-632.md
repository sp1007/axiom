Tiếp tục với **BOOTSTRAP-632**.

:::writing{variant="document" id="74126" title="BOOTSTRAP-632 — Native Distributed API Gateway, Edge Runtime, Reverse Proxy, Load Balancer, Ingress/Egress Policy, Rate Limiting, Authentication Boundary & Edge Service Runtime 5.0"}

# BOOTSTRAP-632
## Native Distributed API Gateway, Edge Runtime, Reverse Proxy, Load Balancer, Ingress/Egress Policy, Rate Limiting, Authentication Boundary & Edge Service Runtime 5.0

**Status:** COMPLETE  
**Layer:** Edge / Gateway Runtime  
**Depends on:** BOOTSTRAP-600 → BOOTSTRAP-631

---

# 1. Purpose

BOOTSTRAP-632 defines the native Axiom runtime for the boundary between external clients and internal services.

It provides:

- reverse proxying;
- API gateway;
- ingress;
- egress;
- L4/L7 load balancing;
- authentication boundary;
- authorization enforcement;
- TLS termination/pass-through;
- request routing;
- traffic shaping;
- rate limiting;
- quotas;
- request transformation;
- response transformation;
- caching;
- connection management;
- health-aware upstream selection;
- circuit breaking;
- request admission;
- observability;
- edge security;
- protocol translation.

The runtime must remain usable without Kubernetes, cloud providers, Envoy, NGINX, HAProxy, or another mandatory external gateway.

---

# 2. Architectural Position

```text
                    INTERNET / CLIENT
                           │
                           ▼
                  ┌─────────────────┐
                  │      632        │
                  │ EDGE / GATEWAY  │
                  ├─────────────────┤
                  │ Listener        │
                  │ TLS             │
                  │ Authentication  │
                  │ Authorization   │
                  │ Rate Limit      │
                  │ Routing         │
                  │ Load Balance    │
                  │ Cache           │
                  │ Proxy           │
                  │ Observability   │
                  └────────┬────────┘
                           │
                     631 Service
                        Runtime
                           │
             ┌─────────────┼─────────────┐
             ▼             ▼             ▼
          Service A     Service B     Service C
```

---

# 3. Separation of Responsibilities

632 is not:

```text
631 service discovery
626 raw network transport
627 distributed coordination
603 capability authority
610 cryptographic primitive implementation
605 process supervision
```

Instead:

```text
632
 = edge policy + gateway execution
```

---

# 4. Deployment Modes

632 supports:

```text
EmbeddedGateway
StandaloneGateway
NodeGateway
ClusterGateway
EdgeGateway
LocalGateway
DevelopmentGateway
```

---

# 5. Listener

A listener represents an externally reachable endpoint.

```text
Listener:
    ListenerId
    Address
    Port
    Protocol
    SecurityPolicy
    Limits
```

---

# 6. Listener Types

```text
TcpListener
TlsListener
HttpListener
Http3Listener
UnixListener
NamedPipeListener
PlatformListener
```

HTTP/3 remains provider-dependent.

---

# 7. Listener Lifecycle

```text
Created
 ↓
Binding
 ↓
Listening
 ↓
Draining
 ↓
Closed
```

---

# 8. Listener Binding

A listener must verify:

- address;
- port;
- capability;
- security policy;
- resource limits.

Privileged ports require explicit OS capability.

---

# 9. L4 Gateway

Layer-4 gateway operates on:

```text
TCP
UDP
TLS passthrough
```

without interpreting application payloads.

---

# 10. L7 Gateway

Layer-7 gateway understands:

```text
HTTP
HTTP/2
HTTP/3
WebSocket
Axiom RPC
```

through protocol providers.

---

# 11. Reverse Proxy

A reverse proxy maps:

```text
external endpoint
→
upstream service
```

using 631.

---

# 12. Upstream

```text
Upstream:
    ServiceId
    VersionPolicy
    EndpointPolicy
    HealthPolicy
    RetryPolicy
    TimeoutPolicy
```

---

# 13. Gateway Route

```text
Route:
    Match
    Authentication
    Authorization
    RateLimit
    Upstream
    Transform
    Cache
    Timeout
```

---

# 14. Route Matching

Routes may match:

```text
host
path
method
protocol
headers
query parameters
source identity
tenant
API version
content type
```

---

# 15. Route Priority

Route evaluation must be deterministic.

More-specific routes may be evaluated before generic routes.

No ambiguous route may be silently selected.

---

# 16. Route Compilation

At startup or policy reload, route definitions should be compiled into an efficient matching structure.

Hot-path route matching must not require parsing arbitrary configuration.

---

# 17. Route Configuration

Example:

```text
route /api/video/*
    methods = [GET, POST]
    auth = required
    upstream = video.service
    timeout = 10s
```

---

# 18. Route Security

A route cannot grant capabilities.

It only selects an enforcement policy.

---

# 19. TLS Termination

632 can terminate TLS at the edge.

Certificate handling is delegated to 610.

---

# 20. TLS Passthrough

TLS may instead pass through to the upstream service.

---

# 21. TLS Re-Encryption

Gateway may:

```text
client
  ↓ TLS
gateway
  ↓ new TLS
service
```

This is recommended for security boundaries where policy requires it.

---

# 22. Certificate Rotation

Gateway must support certificate rotation without dropping existing connections where the platform permits.

---

# 23. SNI Routing

TLS SNI may select:

```text
certificate
route
upstream
```

subject to security policy.

---

# 24. Hostname Routing

HTTP Host/:authority may select a route.

Unrecognized hosts are rejected unless explicitly configured.

---

# 25. Authentication Boundary

632 can authenticate:

```text
public client
service client
machine
device
user
```

using 627/610 providers.

---

# 26. Authentication Methods

Possible providers:

```text
mTLS
BearerToken
SignedToken
APIKey
PlatformIdentity
LocalCredential
CustomProvider
```

The core runtime does not require one universal authentication mechanism.

---

# 27. Authentication Result

```text
AuthenticationResult:
    Principal
    Identity
    CredentialExpiry
    Claims
    SecurityContext
```

---

# 28. Authentication Failure

Unauthenticated traffic is rejected before protected upstream execution.

---

# 29. Authorization

Authorization is evaluated using:

```text
principal
route
operation
resource
tenant
claims
capabilities
```

627 provides policy semantics.

---

# 30. Capability Boundary

A gateway may attenuate authority before forwarding.

Example:

```text
external client
    ↓
gateway capability subset
    ↓
service
```

---

# 31. No Capability Escalation

Gateway transformation must never create a stronger capability than it received.

---

# 32. Identity Forwarding

The gateway may forward authenticated identity using authenticated downstream mechanisms.

It must not simply trust user-supplied identity headers.

---

# 33. Trusted Identity Headers

Headers such as:

```text
X-User-Id
X-Tenant-Id
```

are trusted only when generated by an authenticated gateway boundary and protected against client injection.

---

# 34. Request ID

Every accepted request receives or preserves:

```text
RequestId
```

according to configured trust rules.

---

# 35. Trace Context

632 propagates distributed tracing metadata through 602.

---

# 36. Correlation

The gateway correlates:

```text
client request
gateway request
upstream request
retry attempts
response
```

without exposing secrets.

---

# 37. Rate Limiting

Supported limits:

```text
per-IP
per-principal
per-tenant
per-route
per-service
per-operation
per-api-key
global
```

---

# 38. Rate-Limit Algorithms

```text
TokenBucket
LeakyBucket
FixedWindow
SlidingWindow
ConcurrencyLimit
AdaptiveLimit
```

---

# 39. Token Bucket

Parameters:

```text
capacity
refill_rate
```

provide bounded burst capacity.

---

# 40. Distributed Rate Limit

A distributed limiter may use 628.

However, local limiting should be preferred when global coordination is unnecessary.

---

# 41. Limiter Failure Policy

Possible modes:

```text
FailOpen
FailClosed
LocalFallback
```

must be explicit.

---

# 42. Rate-Limit Response

Rejected requests receive a typed gateway error.

Optional retry timing can be returned.

---

# 43. Concurrency Limit

Gateway may limit simultaneous requests independently from request rate.

---

# 44. Request Queue

Queues are bounded.

There must be no unlimited memory-growing request queue.

---

# 45. Queue Admission

Request admission considers:

```text
authentication
route
priority
deadline
resource availability
tenant quota
```

---

# 46. Load Shedding

Gateway can reject low-priority requests under resource pressure.

---

# 47. Deadline

Gateway propagates the original request deadline.

It must not accidentally reset it at each proxy hop.

---

# 48. Timeout

Gateway policies can define:

```text
connect timeout
header timeout
body timeout
upstream timeout
idle timeout
total timeout
```

---

# 49. Retry

Gateway retries only when:

```text
route policy
+
operation safety
+
retry budget
```

permit it.

---

# 50. Retry Amplification

Gateway must cooperate with 631 retry budgets to prevent multiplicative retries.

---

# 51. Circuit Breaker

Per-upstream circuit states:

```text
Closed
Open
HalfOpen
```

---

# 52. Outlier Detection

Gateway can temporarily remove failing upstream endpoints.

---

# 53. Health Checks

Gateway may use:

```text
active health checks
passive health
631 service health
```

---

# 54. Health-Check Isolation

Health probes have their own:

```text
rate
timeout
resource budget
```

so a failing service cannot consume all gateway capacity.

---

# 55. Load Balancing

Supported:

```text
RoundRobin
Weighted
LeastConnections
LeastOutstanding
Random
PowerOfTwoChoices
ConsistentHash
RendezvousHash
LocalityAware
LatencyAware
```

---

# 56. Zone Awareness

When topology is available:

```text
same zone
→ same region
→ remote region
```

may be preferred.

---

# 57. Failover

Failover policies define:

```text
same instance
same service
alternate version
alternate region
```

---

# 58. Failover Safety

Failover must not automatically duplicate non-idempotent requests.

---

# 59. Request Hedging

Optional and only for safe/deduplicated operations.

---

# 60. Proxy Buffering

Gateway supports:

```text
buffered
streaming
hybrid
```

modes.

---

# 61. Streaming

Streaming avoids buffering the complete body in memory.

---

# 62. Maximum Request Size

Limits:

```text
headers
body
metadata
multipart parts
```

are configurable.

---

# 63. Maximum Response Size

Gateway can enforce response limits for non-streaming routes.

---

# 64. Header Limits

Limits include:

```text
header count
header bytes
name length
value length
```

---

# 65. URI Limits

Limits:

```text
path length
query length
URI length
```

protect parsers from resource exhaustion.

---

# 66. Parser Hardening

Protocol parsers must use bounded state machines.

Malformed input cannot cause unbounded allocation.

---

# 67. Request Normalization

Normalization includes:

```text
URI encoding
path separators
header casing
duplicate headers
content length
transfer encoding
```

according to protocol rules.

---

# 68. Path Traversal

Gateway file/static-resource routes must enforce canonical path policy.

---

# 69. Request Smuggling Protection

Gateway must reject ambiguous combinations of:

```text
Content-Length
Transfer-Encoding
```

according to protocol semantics.

---

# 70. Header Injection

Control characters and malformed header values are rejected.

---

# 71. Host Header Validation

Host routing must reject invalid or unauthorized hostnames.

---

# 72. Method Filtering

Routes may allow:

```text
GET
POST
PUT
PATCH
DELETE
HEAD
OPTIONS
CONNECT
```

only when explicitly supported.

---

# 73. CORS

Optional HTTP policy module supports:

```text
origin
methods
headers
credentials
preflight
```

---

# 74. CORS Security

Wildcard origin behavior must not silently combine with credentialed requests.

---

# 75. Compression

Gateway can negotiate:

```text
gzip
deflate
br
zstd
```

through 613 providers.

---

# 76. Compression Limits

Compression/decompression has resource budgets.

Highly compressed input must not bypass memory limits.

---

# 77. Request Decompression

Supported only when route policy allows it.

---

# 78. Response Compression

Compression is selected based on:

```text
client capability
content type
size
CPU budget
route policy
```

---

# 79. Static Content

Gateway can optionally serve:

```text
files
package resources
CAS objects
generated assets
```

through 611/613.

---

# 80. Static Resource Security

Static file serving must enforce:

```text
root sandbox
canonical path
symlink policy
capability
MIME policy
```

---

# 81. Cache

Gateway cache supports:

```text
memory
disk
CAS
distributed cache
```

---

# 82. Cache-Control

Caching follows explicit route/content policy.

---

# 83. Private Data

Authenticated private responses must not enter shared caches unless the cache key explicitly isolates the security context.

---

# 84. Cache Validation

Support:

```text
ETag
If-None-Match
Last-Modified
If-Modified-Since
```

where protocol provider supports them.

---

# 85. Cache Invalidation

Invalidation may be triggered by:

```text
TTL
explicit purge
service event
version change
package generation
```

---

# 86. Cache Stampede Prevention

Request coalescing can ensure multiple requests do not simultaneously regenerate the same resource.

---

# 87. Request Transformation

Transformations may include:

```text
header insertion
header removal
URL rewrite
method restriction
body format conversion
metadata injection
```

---

# 88. Transformation Safety

Transformations are declarative and bounded.

No arbitrary code executes in the request hot path.

---

# 89. Protocol Translation

632 can translate:

```text
HTTP → RPC
HTTP → IPC
WebSocket → RPC
HTTP/JSON → binary schema
```

through explicit adapters.

---

# 90. Schema Conversion

612 defines serialization.

Gateway may convert:

```text
JSON
AXBIN
```

when route configuration permits.

---

# 91. Schema Validation

Requests may be validated against the service contract before forwarding.

---

# 92. Validation Failure

Invalid requests are rejected before upstream execution.

---

# 93. API Versioning

Gateway can map:

```text
/api/v1
/api/v2
```

to different service contracts.

---

# 94. Version Deprecation

Routes can define:

```text
deprecated
sunset
replacement
```

metadata.

---

# 95. API Key

API keys are credentials, not identity by themselves unless mapped through 627 policy.

---

# 96. Credential Storage

Credentials must use:

```text
601 Secret<T>
610 key management
```

and never ordinary configuration strings where secure storage is required.

---

# 97. Secret Redaction

Logs must never include:

```text
Authorization
Cookie
API key
private key
session token
```

unless explicitly classified safe.

---

# 98. Cookie Policy

Gateway can:

```text
forward
strip
rewrite
secure
```

cookies according to route policy.

---

# 99. CSRF Boundary

Browser-facing state-changing APIs may require explicit CSRF protection.

---

# 100. WebSocket Gateway

Gateway can proxy WebSocket upgrades.

After upgrade, the connection becomes a stream and normal request routing no longer applies per message unless the protocol explicitly supports it.

---

# 101. Server-Sent Events

SSE can be proxied as long-lived streaming responses.

---

# 102. Long-Lived Connection Limits

Limits include:

```text
max lifetime
idle timeout
max concurrent streams
buffer budget
```

---

# 103. HTTP/2

Gateway supports:

```text
multiplexing
stream limits
flow control
header compression
```

through protocol provider.

---

# 104. HTTP/3

HTTP/3/QUIC remains a provider capability.

Core gateway semantics must not depend on QUIC.

---

# 105. Connection Draining

During shutdown:

```text
new connections rejected
new streams rejected
existing streams allowed to finish
```

subject to deadline.

---

# 106. Graceful Restart

Gateway generations can overlap:

```text
generation N
generation N+1
```

while traffic migrates.

---

# 107. Zero-Downtime Configuration Reload

Valid routing policy can be activated atomically.

Existing requests retain their captured configuration snapshot.

---

# 108. Invalid Configuration

Invalid configuration must:

```text
remain on old snapshot
```

rather than partially applying.

---

# 109. Policy Fingerprint

Each active gateway configuration has a deterministic fingerprint.

---

# 110. Policy Rollback

Gateway can restore a previous valid policy generation.

---

# 111. Edge Worker

Optional edge workers may perform bounded computation:

```text
authentication preprocessing
schema validation
metadata normalization
cache key construction
```

They must remain capability-restricted.

---

# 112. No Arbitrary Edge Code

The core gateway does not execute arbitrary scripts per request.

624 may provide scripting through an explicit sandbox.

---

# 113. Edge Script Limits

If 624 is used:

```text
CPU
memory
time
I/O
network
```

are bounded by 606/603.

---

# 114. Egress Gateway

632 can govern outbound service traffic.

---

# 115. Egress Policy

Policies can restrict:

```text
destination service
hostname
IP range
port
protocol
identity
tenant
```

---

# 116. Egress Proxy

Applications can route outbound traffic:

```text
application
 ↓
632 egress
 ↓
external service
```

---

# 117. Egress Authentication

Egress credentials use 610/627.

---

# 118. SSRF Protection

Dynamic outbound URLs must be checked against:

```text
allowed destinations
private network policy
DNS resolution
redirect policy
port policy
```

---

# 119. DNS Rebinding Protection

Resolved destination identity must be checked according to policy rather than trusting only the original hostname.

---

# 120. Redirect Policy

Outbound clients must explicitly control whether redirects are followed.

---

# 121. Metadata Endpoint Protection

Known sensitive infrastructure endpoints must be blocked unless explicitly allowed.

---

# 122. IP Range Policy

Egress rules support:

```text
CIDR
hostname
service identity
network zone
```

---

# 123. Gateway-to-Gateway

Gateways may form:

```text
edge
 ↓
regional gateway
 ↓
service gateway
```

chains.

---

# 124. Hop Metadata

Each gateway hop should add authenticated internal metadata rather than blindly forwarding externally supplied routing fields.

---

# 125. Hop Limit

A gateway request may carry a bounded hop count to prevent loops.

---

# 126. Gateway Loop Detection

A request repeatedly routed through the same gateway chain must be rejected when loop detection triggers.

---

# 127. Gateway Topology

632 can represent:

```text
GatewayId
Region
Zone
Capabilities
Routes
Health
```

---

# 128. Distributed Gateway Membership

627 may provide:

```text
membership
leader
fencing
```

when coordinated gateway state is required.

---

# 129. Active/Active Gateways

Multiple gateways may accept traffic concurrently.

---

# 130. Active/Standby

A deployment can use one active gateway with standby instances.

---

# 131. Shared State

Gateway runtime should minimize shared mutable state.

Preferred state:

```text
local cache
immutable policy snapshot
distributed source of truth only when required
```

---

# 132. Consistency

Routing configuration may be:

```text
strongly coordinated
eventually propagated
```

depending on policy.

Security revocation requires stricter propagation guarantees.

---

# 133. Revocation Priority

Credential/capability revocation must invalidate cached authorization decisions within a configured maximum window.

---

# 134. Edge Resource Governance

606 governs:

```text
connections
requests
streams
buffers
CPU
memory
bandwidth
TLS sessions
cache memory
```

---

# 135. Per-Route Resource Budget

A route can specify:

```text
max concurrency
max body
max CPU
max response
```

---

# 136. Tenant Resource Budget

Tenants may have independent quotas.

---

# 137. Fairness

Scheduling should prevent one tenant from monopolizing gateway workers.

---

# 138. Priority Abuse Protection

External clients cannot directly select unlimited internal priority.

Priority must be authenticated and policy-clamped.

---

# 139. Worker Pool

Gateway uses 607 executor facilities.

CPU-heavy transformations may use separate worker pools.

---

# 140. Blocking Isolation

Blocking filesystem or external calls must not occupy the gateway event loop.

---

# 141. Async I/O

Network I/O uses 607 + 609.

---

# 142. Zero-Copy

Gateway should support:

```text
socket → buffer → socket
```

without unnecessary copies where platform capabilities allow.

---

# 143. Buffer Ownership

Buffers use explicit ownership/lifetime rules.

No hidden reference-counting requirement exists.

---

# 144. Buffer Pools

Reusable pools reduce allocation pressure.

Pools are resource-governed.

---

# 145. Backpressure

Backpressure propagates:

```text
client
 ↓
gateway
 ↓
upstream
 ↓
worker
```

where protocol semantics allow.

---

# 146. Client Disconnect

If client disconnects:

```text
upstream request
```

should be cancelled unless policy explicitly allows completion for side-effectful operations.

---

# 147. Side-Effect Policy

Routes may declare:

```text
SafeToCancel
MustComplete
Unknown
```

to guide cancellation.

---

# 148. Upload Streaming

Large uploads must be streamable without buffering entire bodies.

---

# 149. Download Streaming

Large downloads must be streamable.

---

# 150. Range Requests

Static/media routes can support:

```text
Range
If-Range
```

when configured.

---

# 151. Multipart

Multipart parsing must be bounded by:

```text
part count
part size
total size
header size
```

---

# 152. File Upload Security

Uploaded files must not become executable merely because they are stored by the gateway.

---

# 153. Temporary Storage

Large bodies may spill to 611 temporary storage.

Temporary data must follow sandbox and cleanup policy.

---

# 154. Disk Pressure

Gateway should stop spilling to disk when 606 reports storage pressure.

---

# 155. Observability

Metrics include:

```text
requests
responses
latency
errors
retries
timeouts
rate_limits
connections
streams
cache_hits
cache_misses
upstream_health
```

---

# 156. Per-Route Metrics

Each route can expose:

```text
request count
error count
p50
p95
p99
bytes
active requests
```

---

# 157. Per-Tenant Metrics

Optional and policy-controlled.

---

# 158. Tracing

Gateway creates:

```text
edge span
upstream span
retry span
```

linked by trace ID.

---

# 159. Sampling

Tracing may use:

```text
head sampling
tail sampling provider
error sampling
latency sampling
```

---

# 160. Privacy

Telemetry must avoid storing:

```text
passwords
tokens
private request bodies
```

unless explicitly permitted and redacted.

---

# 161. Audit Events

Security-sensitive events include:

```text
authentication failure
authorization denial
certificate failure
rate-limit policy violation
route rejection
credential rotation
configuration change
```

---

# 162. Crash Handling

Gateway crashes integrate with 602/605.

---

# 163. Crash Recovery

605 may restart gateway instances.

Persistent policy comes from 601/625/628.

---

# 164. Connection Recovery

Client reconnect behavior is protocol-dependent.

Gateway must not assume transparent recovery is always safe.

---

# 165. Gateway State

Durable state should be minimal.

Prefer reconstructible state:

```text
routes
health
connections
cache
```

where practical.

---

# 166. Cache Recovery

Caches may be discarded and rebuilt unless explicitly marked durable.

---

# 167. Distributed Cache

628 can provide shared cache.

632 treats it as an optional provider.

---

# 168. Package Integration

Gateway configuration and static resources may be packaged through 613/625.

---

# 169. Plugin Integration

623 may provide:

```text
protocol providers
authentication providers
policy providers
load balancers
cache providers
```

subject to capability restrictions.

---

# 170. Script Integration

624 can provide administrative automation:

```text
route management
health inspection
cache purge
policy validation
```

but not unrestricted hot-path code.

---

# 171. UI Integration

619/622 may expose a gateway administration UI.

Core 632 remains headless.

---

# 172. Configuration Schema

601 defines typed gateway configuration.

Example:

```text
gateway {
    listeners: [...]
    routes: [...]
    limits: [...]
    security: [...]
}
```

---

# 173. Configuration Validation

Validation must occur before activation.

---

# 174. Configuration Dependencies

Configuration references:

```text
service
certificate
policy
secret
rate-limit
cache
```

must be validated.

---

# 175. Configuration Snapshot

Each request captures an immutable configuration snapshot or equivalent generation reference.

---

# 176. Configuration Generation

```text
GatewayConfigGeneration
```

is monotonically increasing within a gateway instance.

---

# 177. Route Generation

Routes can independently carry generation identifiers.

---

# 178. Policy Compatibility

Configuration updates that would invalidate active connections should be handled according to connection-drain policy.

---

# 179. Compiler Metadata

Supported annotations:

```text
@gateway
@listener
@route
@upstream
@rate_limit
@auth
@authorize
@cache
@proxy
@egress
@ingress
@tls
@cors
@transform
```

---

# 180. Generated Artifacts

Compiler/toolchain may produce:

```text
.axgateway
.axroute
.axlistener
.axupstream
.axpolicy
```

---

# 181. Static Analysis

Compiler/tooling detects:

```text
unreachable route
ambiguous route
missing authentication
unsafe retry
invalid timeout
conflicting limits
invalid upstream
capability mismatch
```

---

# 182. Security Static Analysis

Warnings for:

```text
public route without authentication
unsafe wildcard host
unrestricted egress
private response shared cache
weak credential policy
```

---

# 183. Route Test Generation

Tooling can generate tests for:

```text
match
auth
authorization
rate limit
routing
transformation
upstream failure
```

---

# 184. Deterministic Simulator

Simulator supports:

```text
virtual clients
virtual upstreams
virtual failures
virtual time
virtual traffic
```

---

# 185. Fault Injection

Inject:

```text
TLS failure
upstream timeout
upstream crash
DNS failure
registry failure
cache failure
rate-limit store failure
resource exhaustion
```

---

# 186. Security Tests

Must test:

```text
header spoofing
identity spoofing
route bypass
SSRF
request smuggling
path traversal
credential leakage
cache isolation
```

---

# 187. Protocol Fuzzing

Fuzz:

```text
HTTP parser
HTTP/2 framing
HTTP/3 provider boundary
URI parser
headers
multipart
WebSocket handshake
```

---

# 188. Resource Exhaustion Tests

Verify bounded behavior under:

```text
huge headers
huge body
many connections
many streams
slow clients
slow upstreams
many routes
many tenants
```

---

# 189. Slowloris Protection

Gateway must support bounded:

```text
header timeout
body timeout
idle timeout
connection count
```

---

# 190. Slow Upstream Protection

Per-upstream concurrency and timeout limits prevent resource starvation.

---

# 191. Slow Client Protection

Streaming responses must not indefinitely consume upstream resources when downstream clients stop reading.

---

# 192. Connection Limits

Limits are hierarchical:

```text
gateway
listener
tenant
route
upstream
connection
```

---

# 193. Memory Safety

Malformed network input must not cause:

```text
buffer overflow
use-after-free
double release
unbounded allocation
```

---

# 194. No Global Hot Lock

Gateway hot paths should use:

```text
per-core state
atomic counters
read-mostly immutable snapshots
sharded caches
```

rather than a single global mutex.

---

# 195. Configuration Read Path

Target:

```text
O(1)
```

or bounded lookup for ordinary route operations after configuration compilation.

---

# 196. Route Matching Performance

Compiled route tables should avoid linear scanning of thousands of routes where possible.

---

# 197. Minimal Gateway

A minimal gateway should be capable of:

```text
TCP listener
TLS
HTTP
single upstream
health
proxy
```

without pulling in the full distributed runtime.

---

# 198. Binary Size

Unused:

```text
HTTP/3
WebSocket
cache
distributed limiter
mesh
script
```

must be removable.

---

# 199. No Mandatory External Runtime

The gateway executable must be buildable using the native Axiom runtime.

External providers remain optional.

---

# 200. Platform Mapping

Supported targets:

```text
Windows
Linux
macOS
Android
iOS
WASM host
embedded
```

Edge/server profiles may omit UI/mobile components.

---

# 201. WASM

In WASM:

```text
632
```

maps to host/browser networking capabilities.

Binding raw listening sockets is host-dependent.

---

# 202. Mobile

Mobile platforms may restrict:

```text
background listeners
incoming network access
long-running gateway processes
```

The abstraction remains valid but provider capabilities are explicit.

---

# 203. Embedded

Embedded gateway may provide:

```text
small HTTP server
TLS
routing
authentication
rate limiting
```

with reduced feature profile.

---

# 204. Server Profile

Server profile enables:

```text
full TCP
TLS
HTTP
HTTP/2
optional HTTP/3
distributed routing
```

---

# 205. Edge Profile

Edge profile prioritizes:

```text
low latency
small memory
fast startup
bounded configuration
```

---

# 206. Gateway API

Canonical struct-only interface:

```text
struct Gateway {
    config: GatewayConfig
}

fn Gateway.start() -> Result<GatewayHandle>
fn Gateway.stop() -> Result<void>
fn Gateway.reload(config: GatewayConfig) -> Result<ReloadResult>
fn Gateway.inspect() -> GatewaySnapshot
```

---

# 207. Listener API

```text
struct Listener {
    id: ListenerId
}

fn Listener.bind() -> Result<ListenerHandle>
fn Listener.drain(deadline: Deadline) -> Future<Result<void>>
fn Listener.close() -> Result<void>
```

---

# 208. Route API

```text
struct Route {
    pattern: RoutePattern
    upstream: UpstreamRef
}

fn Route.matches(request: RequestView) -> bool
```

---

# 209. Upstream API

```text
struct Upstream {
    service: ServiceId
}

fn Upstream.resolve() -> Future<Result<EndpointSet>>
fn Upstream.choose(ctx: RequestContext) -> Result<Endpoint>
```

---

# 210. Rate Limiter API

```text
struct RateLimiter {
    policy: RateLimitPolicy
}

fn RateLimiter.admit(ctx: RequestContext) -> Result<Admission>
```

---

# 211. Gateway Request Pipeline

Canonical implementation:

```text
accept
 ↓
parse
 ↓
normalize
 ↓
authenticate
 ↓
authorize
 ↓
rate-limit
 ↓
route
 ↓
cache lookup
 ↓
upstream selection
 ↓
proxy
 ↓
response policy
 ↓
cache store
 ↓
telemetry
 ↓
complete
```

---

# 212. Pipeline Ordering Invariant

Security-sensitive stages cannot be moved after execution of protected upstream side effects.

---

# 213. Authentication Before Protected Execution

A protected upstream must never execute before authentication/authorization completes.

---

# 214. Cache Ordering

For private authenticated resources, authorization context must be established before serving a shared cached response.

---

# 215. Rate Limit Ordering

Global abuse limits may occur before expensive authentication operations.

Sensitive policy may require identity-aware limiting afterward.

---

# 216. Request Body Handling

The gateway can defer body consumption until route policy requires it.

This avoids unnecessary buffering.

---

# 217. Early Rejection

Requests can be rejected before body upload when:

```text
method
host
route
authentication
headers
```

already make them invalid.

---

# 218. Expect/Continue

Gateway should support bounded handling of:

```text
Expect: 100-continue
```

to avoid unnecessary large uploads.

---

# 219. Final Architecture

```text
                       EXTERNAL CLIENT
                              │
                              ▼
                    ┌──────────────────┐
                    │       632        │
                    │ EDGE/GATEWAY     │
                    ├──────────────────┤
                    │ Listener         │
                    │ TLS / Protocol   │
                    │ Parse/Normalize  │
                    │ Authentication   │
                    │ Authorization    │
                    │ Rate Limit       │
                    │ Quota            │
                    │ Route            │
                    │ Cache            │
                    │ Load Balance     │
                    │ Circuit Breaker  │
                    │ Proxy            │
                    │ Transform        │
                    │ Telemetry        │
                    └────────┬─────────┘
                             │
                         631 Service
                             │
               ┌─────────────┼─────────────┐
               ▼             ▼             ▼
             630           629           623
           Compute       Workflow      Extensions
               │             │
               └─────────────┼─────────────┘
                             ▼
                          626/609
                             │
                          Network
```

---

# 220. Architecture Invariants

1. Gateway is an edge policy runtime.
2. Gateway is not the service registry.
3. Gateway is not the distributed coordinator.
4. Gateway is not the cryptographic primitive provider.
5. Gateway is not the service implementation.
6. Gateway never grants authority.
7. Gateway may attenuate authority.
8. Authentication precedes protected execution.
9. Authorization precedes protected execution.
10. Client-supplied identity is untrusted by default.
11. Route selection is deterministic.
12. Configuration activation is atomic.
13. Invalid configuration does not partially activate.
14. Request deadlines propagate.
15. Retry budgets are bounded.
16. Non-idempotent operations are not blindly retried.
17. Hedging requires explicit safety.
18. Circuit breakers fail fast when open.
19. Rate limits are bounded.
20. Request queues are bounded.
21. Connection pools are resource-governed.
22. Response caches respect authorization boundaries.
23. Static resources obey filesystem capabilities.
24. Egress destinations require policy.
25. SSRF protection is mandatory for unrestricted URL inputs.
26. Header spoofing is prevented at trust boundaries.
27. TLS credentials use secure storage.
28. Secret values are excluded from ordinary telemetry.
29. Gateway shutdown drains active work.
30. Long-lived streams have explicit limits.
31. Sidecars are optional.
32. Service mesh is optional.
33. Cloud infrastructure is optional.
34. HTTP/3 is optional.
35. Distributed state is optional unless policy requires it.
36. Local fast paths preserve security semantics.
37. Protocol adapters preserve gateway policy semantics.
38. No arbitrary hot-path scripting is required.
39. No mandatory GC exists.
40. Unused features must be dead-strippable.

---

# 221. Acceptance Criteria

The implementation must demonstrate at least:

### Networking
- TCP listener;
- TLS;
- HTTP;
- HTTP/2 provider;
- optional HTTP/3 provider;
- WebSocket;
- streaming;
- connection pooling;
- graceful draining.

### Routing
- host routing;
- path routing;
- method routing;
- metadata routing;
- API version routing;
- deterministic route precedence;
- route compilation.

### Security
- mTLS;
- authentication;
- authorization;
- identity forwarding;
- capability attenuation;
- certificate rotation;
- secret redaction;
- SSRF protection;
- request smuggling protection;
- header injection protection.

### Reliability
- health checks;
- retries;
- retry budget;
- circuit breaker;
- outlier ejection;
- failover;
- request hedging;
- backpressure;
- load shedding.

### Limits
- request size;
- response size;
- header size;
- URI size;
- connection limit;
- stream limit;
- concurrency;
- bandwidth;
- memory.

### Performance
- zero-copy forwarding where possible;
- buffer pooling;
- immutable configuration snapshots;
- no global hot-path lock;
- compiled routing;
- dead stripping.

### Data
- request transformation;
- schema validation;
- JSON/AXBIN conversion;
- cache;
- ETag;
- range requests;
- request coalescing.

### Operations
- configuration reload;
- rollback;
- service health;
- route inspection;
- gateway metrics;
- distributed tracing;
- audit events;
- deterministic simulator;
- fault injection.

### Platform
- Windows;
- Linux;
- macOS;
- mobile capability mapping;
- WASM host boundary;
- embedded profile.

**Target: ≥260 acceptance criteria.**

---

# 222. Completion

**BOOTSTRAP-632 — COMPLETE**

The distributed network stack now separates:

```text
609 → raw networking
626 → network application protocols
631 → service-to-service runtime
632 → external/edge gateway runtime
```

while preserving the common security, scheduling, resource, cryptography, diagnostics, coordination, and distributed-data foundations.

The next architectural boundary is therefore the **distributed API/data contract and developer-facing service framework**, rather than adding more proxy features to 632.

**NEXT TASK: BOOTSTRAP-633 — Native Distributed API Contract, Schema Registry, RPC IDL, Code Generation, Client/Server Stubs, Compatibility Checking & Service SDK Runtime 5.0**
:::