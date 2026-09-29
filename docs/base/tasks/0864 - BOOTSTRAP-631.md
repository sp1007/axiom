Tiếp tục với **BOOTSTRAP-631**.

:::writing{variant="document" id="58314" title="BOOTSTRAP-631 — Native Distributed Service Runtime, Service Discovery, Service Mesh Boundary, Traffic Routing, Load Balancing, Health-Aware Requests & Service-to-Service Execution 5.0"}

# BOOTSTRAP-631
## Native Distributed Service Runtime, Service Discovery, Service Mesh Boundary, Traffic Routing, Load Balancing, Health-Aware Requests & Service-to-Service Execution Runtime 5.0

**Status:** COMPLETE  
**Layer:** Distributed Service Runtime  
**Depends on:** BOOTSTRAP-600 → BOOTSTRAP-630  
**Primary dependencies:** 603, 605, 606, 607, 608, 609, 610, 625, 626, 627, 628, 629, 630

---

# 1. Purpose

BOOTSTRAP-631 defines the native Axiom runtime for applications composed of multiple cooperating services.

It provides:

- service identity;
- service registration;
- service discovery;
- endpoint management;
- service instances;
- health-aware routing;
- client-side load balancing;
- server-side request admission;
- connection management;
- request routing;
- retries;
- timeout/deadline propagation;
- circuit breakers;
- bulkheads;
- request hedging;
- locality-aware routing;
- service version routing;
- traffic policies;
- weighted routing;
- failover;
- graceful service draining;
- service-to-service authentication;
- capability-aware calls;
- distributed tracing;
- service dependency visibility;
- service topology diagnostics.

631 sits above raw networking and distributed compute.

---

# 2. Fundamental Separation

Axiom explicitly distinguishes:

```text
Service
ServiceInstance
Endpoint
Process
Worker
Task
Workflow
```

Definitions:

```text
Service
    logical network-accessible capability

ServiceInstance
    concrete running instance of a service

Endpoint
    concrete reachable network address

Process
    OS execution unit

Worker
    compute execution provider

Task
    executable unit of work

Workflow
    durable orchestration
```

Therefore:

```text
Service != Process
Service != Worker
Service != Workflow
```

---

# 3. Architectural Position

```text
                 APPLICATION
                     │
          ┌──────────┴──────────┐
          ▼                     ▼
       629 Workflow          Direct API
          │                     │
          └──────────┬──────────┘
                     ▼
            ┌─────────────────┐
            │      631        │
            │ DISTRIBUTED     │
            │ SERVICE RUNTIME │
            ├─────────────────┤
            │ Identity        │
            │ Discovery       │
            │ Routing         │
            │ Load Balance    │
            │ Health          │
            │ Retry           │
            │ Circuit Breaker │
            │ Traffic Policy  │
            │ Service Calls   │
            └────────┬────────┘
                     │
          ┌──────────┼───────────┐
          ▼          ▼           ▼
        627        626/609      630
    Coordination   Network    Compute
          │
          ▼
        605
    Supervision
```

---

# 4. Non-Goals

631 does not require:

- Kubernetes;
- Docker;
- Envoy;
- Istio;
- Consul;
- a centralized service registry;
- a sidecar proxy;
- a mandatory service mesh;
- cloud infrastructure;
- HTTP as the only protocol;
- microservices architecture.

Axiom applications may use:

```text
single process
multi-process
multi-service
distributed cluster
```

with the same conceptual model.

---

# 5. Service Identity

Each service has:

```text
ServiceId
PublisherId
ServiceVersion
InterfaceVersion
```

Each running instance has:

```text
ServiceInstanceId
InstanceGeneration
```

Example:

```text
Service:
    video.encoder

Instance:
    video.encoder / instance-42 / generation-7
```

---

# 6. Endpoint Identity

An endpoint is:

```text
EndpointId
Protocol
Address
Port
Transport
SecurityProfile
```

Endpoint identity must not be inferred solely from an IP address.

---

# 7. Endpoint Examples

```text
tcp://10.0.0.20:8443
```

or:

```text
unix://service/video
```

or platform-specific local IPC endpoints.

631 delegates transport to 626/609/604.

---

# 8. Service Contract

A service exposes one or more interfaces.

```text
ServiceInterface:
    InterfaceId
    Version
    Operations
    RequestSchema
    ResponseSchema
    ErrorSchema
    StreamingMode
```

Serialization uses 612.

---

# 9. Service Operation

An operation has:

```text
OperationId
Name
InputSchema
OutputSchema
ErrorSchema
Idempotency
TimeoutPolicy
StreamingPolicy
CapabilityRequirements
```

---

# 10. Struct-Only API

Example:

```text
struct VideoService {
    endpoint: ServiceEndpoint
}

fn VideoService.encode(
    request: EncodeRequest
) -> Future<Result<EncodeResponse>>
```

No classes are required.

---

# 11. Service Registration

A service instance registers:

```text
ServiceId
InstanceId
Generation
Endpoints
Capabilities
Version
Health
Resources
Metadata
```

Registration is lease-based.

---

# 12. Registration Lease

```text
ServiceLease:
    ServiceInstanceId
    Generation
    Expiration
    FenceToken
```

Expired registrations cannot receive new traffic.

---

# 13. Service Registry

Registry implementations may be:

```text
LocalRegistry
StaticRegistry
DistributedRegistry
627BackedRegistry
DNSRegistry
FileRegistry
EmbeddedRegistry
ExternalProvider
```

The core API does not mandate a particular registry technology.

---

# 14. Registry Authority

631 consumes distributed authority from 627.

It must not create a competing consensus system.

---

# 15. Registration Lifecycle

```text
Created
  ↓
Registering
  ↓
Registered
  ↓
Ready
  ↓
Serving
  ↓
Draining
  ↓
Unregistered
```

Failure:

```text
Serving → Suspect → Failed
```

---

# 16. Readiness

A service is routable only after:

```text
process ready
dependencies ready
security identity ready
endpoint ready
application readiness
```

have succeeded.

This integrates with 605.

---

# 17. Liveness vs Readiness

631 distinguishes:

```text
Liveness
    process is alive

Readiness
    instance can accept this service traffic

Health
    broader operational condition
```

A live but unready instance must not receive ordinary traffic.

---

# 18. Service Health

Health states:

```text
Healthy
Degraded
Unhealthy
Unknown
Draining
```

Health is operation-specific where necessary.

---

# 19. Operation Health

A service can be healthy globally but unhealthy for:

```text
video.encode
video.decode
gpu.inference
```

631 may maintain operation-level health.

---

# 20. Endpoint Health

Health can be attached to:

```text
service
instance
endpoint
operation
```

---

# 21. Health Checks

Health checks may be:

```text
Passive
Active
ApplicationProvided
TransportLevel
DependencyBased
```

---

# 22. Passive Health

631 observes:

```text
timeouts
connection failures
HTTP/RPC errors
transport errors
circuit breaker state
```

without generating additional traffic.

---

# 23. Active Health

Optional probes:

```text
health.check()
```

must be bounded and rate-limited.

---

# 24. Health Check Security

Health endpoints must not expose:

- secrets;
- internal credentials;
- unrestricted diagnostics;
- arbitrary filesystem information.

---

# 25. Service Discovery

Clients resolve:

```text
ServiceId + Version + Policy
```

into:

```text
ServiceInstance[]
```

---

# 26. Discovery Result

```text
ServiceDiscoveryResult:
    service
    instances
    endpoints
    version
    expiration
    registry_generation
```

---

# 27. Discovery Cache

Clients may cache discovery results.

Each cache entry has:

```text
TTL
RegistryGeneration
ObservedAt
```

Expired results are not automatically considered authoritative.

---

# 28. Stale Discovery

A stale discovery result may be used only according to explicit policy.

Example:

```text
AllowStaleFor = 5s
```

This helps tolerate temporary registry outages.

---

# 29. Negative Discovery Cache

Failed lookups may be cached briefly.

This prevents repeated registry overload.

---

# 30. Service Alias

Aliases may map:

```text
video
→
video.encoder.v2
```

Aliases are configuration data, not implicit executable behavior.

---

# 31. Version Selection

A client may request:

```text
version == 2
```

or:

```text
version >= 2.1 < 3
```

Resolution is deterministic.

---

# 32. Version Routing

A service can expose:

```text
v1
v2
v3
```

simultaneously.

Traffic can be routed according to explicit policy.

---

# 33. Weighted Routing

Example:

```text
v2 → 90%
v3 → 10%
```

Weights describe routing distribution, not quality.

---

# 34. Header/Metadata Routing

Requests may carry typed routing metadata:

```text
tenant
region
device_class
api_version
experiment_id
```

Policies can match these values.

Sensitive metadata must be protected.

---

# 35. No Arbitrary Routing Scripts

Routing policies must be declarative.

The core service router must not execute arbitrary scripts on every request.

---

# 36. Route Match

A route can match:

```text
service
interface
operation
version
metadata
tenant
network domain
```

---

# 37. Route Action

Possible actions:

```text
Forward
Reject
Redirect
Retry
Fallback
Shadow
Mirror
```

---

# 38. Shadow Traffic

A request may optionally be duplicated to a shadow service.

Shadow results are not authoritative.

This is useful for compatibility testing.

---

# 39. Shadow Safety

Shadow requests must explicitly declare whether they may cause side effects.

Default:

```text
side_effects = forbidden
```

---

# 40. Traffic Mirroring

Traffic mirroring should avoid accidental duplicate external effects.

---

# 41. Load Balancing

Supported strategies:

```text
RoundRobin
WeightedRoundRobin
LeastConnections
LeastOutstanding
Random
PowerOfTwoChoices
LatencyAware
LocalityAware
ConsistentHash
RendezvousHash
```

---

# 42. Load Balancing Scope

Load balancing can occur:

```text
client-side
service-side
gateway-side
provider-side
```

631 defines the abstraction.

---

# 43. Client-Side Load Balancing

Client receives instance list and chooses endpoint.

Advantages:

```text
low central overhead
fast routing
local knowledge
```

---

# 44. Gateway Load Balancing

A gateway can perform routing before forwarding.

This is optional.

---

# 45. Consistent Hashing

Useful for:

```text
session affinity
cache locality
partition locality
```

Hash key must be explicitly supplied.

---

# 46. Rendezvous Hashing

Rendezvous hashing may select a stable instance without maintaining large routing tables.

---

# 47. Locality-Aware Load Balancing

Preference order may be:

```text
same process
same node
same rack
same zone
same region
remote
```

Actual topology comes from 627/630.

---

# 48. Health-Aware Load Balancing

Unhealthy endpoints are removed from normal routing.

Degraded endpoints may remain available according to policy.

---

# 49. Outlier Detection

An endpoint repeatedly producing failures can be temporarily ejected.

Policy:

```text
failure threshold
window
ejection duration
max ejection percentage
```

---

# 50. Ejection

Ejection is local routing state.

It does not change authoritative service health.

---

# 51. Circuit Breaker

Circuit states:

```text
Closed
Open
HalfOpen
```

---

# 52. Circuit Closed

Requests flow normally.

Failures increment counters.

---

# 53. Circuit Open

Requests fail fast without contacting the service.

---

# 54. Circuit HalfOpen

A small number of probe requests determine whether traffic can resume.

---

# 55. Circuit Breaker Scope

Circuit breakers may be scoped by:

```text
service
operation
endpoint
tenant
client
```

---

# 56. Retry Policy

Retries require explicit configuration.

Axiom does not retry every failure automatically.

---

# 57. Retryable Errors

Typical candidates:

```text
transport unavailable
temporary overload
timeout before request acceptance
service unavailable
```

---

# 58. Non-Retryable Errors

Examples:

```text
invalid request
authorization denied
schema mismatch
deterministic application error
```

---

# 59. Retry Budget

Retries consume a bounded budget.

Possible limits:

```text
max_attempts
max_total_time
max_retry_bytes
max_retry_cost
```

---

# 60. Exponential Backoff

Retry delay:

```text
base × 2^attempt
```

with bounded maximum.

Optional jitter avoids synchronized retries.

---

# 61. Retry Storm Prevention

Axiom must prevent:

```text
client retries
+
gateway retries
+
service retries
+
workflow retries
```

from multiplying uncontrollably.

Each layer must expose retry ownership.

---

# 62. Retry Ownership

Recommended rule:

```text
transport layer
    transport retry only

service layer
    request retry only when safe

workflow layer
    business retry
```

---

# 63. Idempotency

Operations may declare:

```text
Idempotent
ConditionallyIdempotent
NonIdempotent
Unknown
```

Unknown operations are not automatically retried after uncertain completion.

---

# 64. Idempotency Key

Requests may include:

```text
IdempotencyKey
```

The service can persist deduplication state through 628/612.

---

# 65. Idempotency Store

For durable idempotency:

```text
request key
→ result
```

can be stored in 628.

---

# 66. Request Deadline

Every request may carry:

```text
Deadline
```

The deadline propagates downstream.

---

# 67. Deadline Propagation

If:

```text
client deadline = T
```

then downstream requests cannot silently extend beyond T.

---

# 68. Timeout Types

631 distinguishes:

```text
ConnectTimeout
RequestTimeout
ResponseHeaderTimeout
IdleTimeout
TotalDeadline
```

---

# 69. Cancellation

Cancellation propagates:

```text
caller
 ↓
service client
 ↓
network request
 ↓
server handler
 ↓
local task
```

---

# 70. Cancellation Race

If cancellation arrives after the server commits an effect:

```text
UnknownOutcome
```

may be returned.

The client must not infer rollback.

---

# 71. Request Context

```text
RequestContext:
    RequestId
    TraceContext
    Deadline
    Cancellation
    Identity
    CapabilitySet
    Metadata
```

---

# 72. Identity Propagation

Identity is propagated using 627-issued service/workload identity.

The client must not forge identity metadata.

---

# 73. Capability Propagation

A downstream service receives only attenuated authority.

```text
A
 ↓ reduced capabilities
B
 ↓ reduced capabilities
C
```

---

# 74. Capability Non-Amplification

A downstream service cannot derive more authority than the caller delegated unless it independently possesses that authority.

---

# 75. Service-to-Service Authentication

Supported through:

```text
mTLS
service identity tokens
platform identity
local authenticated IPC
```

Providers are defined by 610/627.

---

# 76. Mutual TLS

631 can request:

```text
client certificate
server certificate
```

validation through 610.

---

# 77. Service Identity Rotation

Identity credentials can rotate without stopping the service.

631 should support overlapping validity periods.

---

# 78. Token Rotation

Short-lived service tokens are preferred where supported.

Token caching must respect expiration.

---

# 79. Authorization

Authorization may depend on:

```text
caller identity
service identity
operation
resource
tenant
capability
policy
```

627 owns policy evaluation.

631 enforces the resulting decision.

---

# 80. Service Boundary

A service boundary is an explicit security boundary.

Network reachability does not imply authorization.

---

# 81. Network Policy

603 can restrict:

```text
source service
destination service
port
protocol
network domain
```

---

# 82. Service Mesh Boundary

631 defines an optional service-mesh abstraction:

```text
ServiceMeshProvider
```

It can implement:

```text
routing
mTLS
health
telemetry
policy
traffic control
```

---

# 83. Sidecar Model

A sidecar may implement 631 provider functions.

However:

```text
sidecar != required
```

Native in-process client/server implementations remain valid.

---

# 84. Node-Agent Model

A node agent can provide:

```text
discovery
identity
policy
telemetry
routing
```

without becoming a mandatory proxy.

---

# 85. In-Process Fast Path

If two services share a process and policy allows:

```text
ServiceCall
```

may be optimized without network serialization.

Semantics must remain equivalent.

---

# 86. Same-Node IPC Fast Path

If services are separate processes:

```text
604 IPC
```

may replace network transport.

---

# 87. Network Path

Remote service calls use:

```text
626
  ↓
609
  ↓
610
```

as appropriate.

---

# 88. Protocol Abstraction

631 supports:

```text
HTTP
RPC
streaming RPC
WebSocket
Unix IPC
named pipe
custom Axiom transport
```

through providers.

---

# 89. RPC Integration

626 service APIs can generate RPC stubs.

631 adds:

```text
discovery
routing
load balancing
health
retry
identity
```

around the RPC transport.

---

# 90. HTTP Integration

631 can expose:

```text
HttpServiceClient
HttpServiceServer
```

but HTTP semantics remain owned by 626.

---

# 91. Streaming

Service calls may be:

```text
Unary
ClientStreaming
ServerStreaming
BidirectionalStreaming
```

---

# 92. Stream Load Balancing

A stream normally remains bound to one endpoint after establishment.

Per-message rerouting is not automatic.

---

# 93. Stream Failure

A broken stream can be:

```text
Resume
Reconnect
Restart
Fail
```

depending on application protocol support.

---

# 94. Resume Tokens

Long streams may define:

```text
ResumeToken
```

to restart from a known position.

---

# 95. Connection Pooling

Client connection pools are scoped by:

```text
destination
protocol
security identity
TLS configuration
network policy
```

---

# 96. Connection Reuse

Connections may be reused across requests when protocol and security policy allow.

---

# 97. Connection Limits

606 governs:

```text
max connections
max concurrent requests
buffer memory
network bandwidth
```

---

# 98. Backpressure

Backpressure exists at:

```text
connection
request
stream
service
queue
worker
```

layers.

---

# 99. Server Admission Control

A service can reject or delay work when overloaded.

States:

```text
Accept
Throttle
Queue
Reject
```

---

# 100. Load Shedding

Under severe overload, services may shed:

```text
low-priority
background
optional
non-deadline-critical
```

traffic.

---

# 101. Priority Propagation

Request priority may propagate downstream.

The receiver may clamp priority to prevent privilege abuse.

---

# 102. Tenant Isolation

Per-tenant policies may include:

```text
max concurrency
rate
bandwidth
queue depth
priority
```

---

# 103. Rate Limiting

Supported algorithms:

```text
TokenBucket
LeakyBucket
FixedWindow
SlidingWindow
ConcurrencyLimit
```

---

# 104. Distributed Rate Limits

Global limits may use 628/627.

Local rate limits should remain local whenever possible to reduce coordination cost.

---

# 105. Rate-Limit Failure Mode

When distributed limit state is unavailable:

```text
FailOpen
FailClosed
LocalFallback
```

must be explicitly configured.

---

# 106. Request Hedging

Hedging may send a duplicate request after a delay.

Allowed only for:

```text
idempotent
or
deduplicated
```

operations.

---

# 107. Hedge Policy

```text
hedge_delay
max_hedges
hedge_budget
```

must be bounded.

---

# 108. Hedge Cancellation

When one attempt succeeds:

```text
other attempts → cancellation
```

must be issued.

---

# 109. Bulkhead

Service dependencies may be isolated by:

```text
connection pool
worker pool
queue
resource group
```

so one failing dependency cannot consume all capacity.

---

# 110. Dependency Isolation

Example:

```text
Service A
 ├── database pool
 ├── cache pool
 └── media pool
```

Each can have separate limits.

---

# 111. Fallback

A service may specify a fallback:

```text
primary → cache
primary → local computation
primary → degraded response
```

Fallback must be explicit.

---

# 112. No Hidden Fallback

The runtime must not silently return stale or approximate data unless the service contract allows it.

---

# 113. Stale Data Policy

A caller may specify:

```text
AllowFreshOnly
AllowStale
AllowStaleUntil(deadline)
```

for cache-backed services.

---

# 114. Request Cache

631 can optionally cache responses.

Cacheability requires explicit operation metadata.

---

# 115. Cache Key

Cache key must include all semantics affecting the result:

```text
service
operation
version
request
relevant authorization context
```

---

# 116. Authorization-Aware Cache

Responses containing tenant/private data must not be shared across incompatible security contexts.

---

# 117. Service Discovery + Cache

Discovery cache and response cache are separate.

---

# 118. Request Routing Pipeline

Canonical sequence:

```text
Request
 ↓
Identity
 ↓
Authorization
 ↓
Discovery
 ↓
Version selection
 ↓
Health filtering
 ↓
Capability filtering
 ↓
Locality filtering
 ↓
Load balancing
 ↓
Circuit breaker
 ↓
Admission
 ↓
Connection
 ↓
Request
```

---

# 119. Fast Path

After warmup:

```text
cached route
+
healthy endpoint
+
valid connection
```

should allow very low-overhead routing.

---

# 120. Route Cache

Route cache key:

```text
ServiceId
OperationId
VersionPolicy
RoutingContextFingerprint
```

---

# 121. Route Invalidation

Route cache invalidates on:

```text
registry generation change
endpoint removal
health state change
policy change
version change
security revocation
```

---

# 122. Stale Route Race

A request may select an endpoint that becomes unavailable immediately afterward.

Transport failure must trigger normal failure handling.

---

# 123. Service Draining

A draining service:

```text
no new long-lived requests
```

while existing requests may finish.

---

# 124. Connection Drain

New requests may use other connections.

Existing streams receive a grace period.

---

# 125. Graceful Deployment

Deployment sequence:

```text
new instance
 ↓
health
 ↓
ready
 ↓
traffic
 ↓
old instance drain
 ↓
old instance stop
```

---

# 126. Blue/Green

631 supports traffic switching between:

```text
generation A
generation B
```

but deployment orchestration itself belongs to higher layers.

---

# 127. Canary

Weighted routing supports gradual traffic movement.

631 only provides routing primitives.

---

# 128. Rollback

Traffic can be shifted back to a previous service version if policy requests it.

---

# 129. Service Dependency Graph

631 can maintain a descriptive graph:

```text
A → B
A → C
B → D
```

This is diagnostic unless a higher-level system uses it for policy.

---

# 130. Dependency Health

A service may report:

```text
dependency B degraded
```

without becoming automatically unavailable.

---

# 131. Dependency Circuit

Each dependency can have independent circuit state.

---

# 132. Cascading Failure Protection

631 combines:

```text
timeouts
bulkheads
circuit breakers
load shedding
retry budgets
```

to limit cascading failures.

---

# 133. Timeout Budget

If request deadline is:

```text
100 ms
```

downstream calls should receive a remaining budget, not a new 100 ms timeout.

---

# 134. Retry Budget

The total retry cost must fit within the original request budget.

---

# 135. Failure Amplification Bound

The runtime should enforce bounded:

```text
requests generated
connections generated
retries generated
hedges generated
```

per logical request.

---

# 136. Service Gateway

631 optionally provides:

```text
ServiceGateway
```

for:

```text
external → internal service
```

traffic.

---

# 137. Gateway Responsibilities

Gateway may perform:

```text
TLS termination
authentication
authorization
routing
rate limiting
request size limits
observability
```

according to policy.

---

# 138. Gateway Is Not Required

Internal service-to-service traffic may bypass the gateway.

---

# 139. External vs Internal Identity

Gateway can translate:

```text
external identity
→
internal authenticated principal
```

using 627 policy.

---

# 140. Service Export

A service can explicitly declare:

```text
Public
Internal
ClusterLocal
NodeLocal
ProcessLocal
```

visibility.

---

# 141. Service Import

Clients can declare required service:

```text
ServiceRequirement:
    service_id
    version
    operations
    security
```

---

# 142. Startup Dependency

605 may use service requirements to delay readiness.

631 supplies discovery/readiness information.

---

# 143. Runtime Dependency

A service may remain running even if an optional dependency disappears.

---

# 144. Required Dependency

A required dependency may cause the service to become:

```text
Degraded
NotReady
```

according to policy.

---

# 145. Dependency Cycles

631 detects cycles in declared service dependencies.

Cycles are allowed only if explicitly supported by lifecycle policy.

---

# 146. Service Activation

A service may activate:

```text
Always
OnDemand
OnFirstRequest
WorkflowTriggered
```

through 605.

---

# 147. On-Demand Services

A request can trigger:

```text
service activation
→ readiness wait
→ routing
```

with a bounded activation deadline.

---

# 148. Service Shutdown

Idle services may be drained and stopped.

---

# 149. Request Queue During Activation

Requests may:

```text
wait
fail fast
redirect
```

according to policy.

Queues must be bounded.

---

# 150. Service-Level SLO Metadata

631 may carry descriptive targets:

```text
latency target
availability target
capacity target
```

but does not guarantee them.

---

# 151. Latency Measurement

Measure:

```text
DNS/discovery
connect
queue
server processing
network
serialization
```

separately.

---

# 152. Error Classification

Errors:

```text
DiscoveryError
NoHealthyInstance
AuthorizationDenied
ConnectionError
Timeout
Overloaded
CircuitOpen
RateLimited
SchemaMismatch
VersionMismatch
RemoteError
UnknownOutcome
Cancelled
```

---

# 153. Error Propagation

Remote errors preserve:

```text
error code
service
operation
retryability
correlation ID
```

Sensitive server internals are not exposed by default.

---

# 154. Error Translation

A transport error must not be falsely translated into an application error.

---

# 155. Unknown Outcome

If a request may have executed:

```text
UnknownOutcome
```

is returned for non-idempotent operations when confirmation is unavailable.

---

# 156. Request Journal

For idempotent operations, the server can store:

```text
IdempotencyKey
RequestHash
ResultReference
Expiration
```

in 628.

---

# 157. Service Event Log

Optional service events:

```text
registered
ready
draining
failed
version_changed
```

can be emitted into 628.

---

# 158. Service State Persistence

Operational service state can be reconstructed.

Ephemeral connection state is not durable by default.

---

# 159. Session State

Session state must be explicitly stored:

```text
628
```

if it must survive service restart.

---

# 160. Sticky Sessions

Sticky sessions are a routing optimization, not persistence.

---

# 161. Service Mesh Telemetry

Mesh providers must integrate with:

```text
602 diagnostics
```

for traces and metrics.

---

# 162. No Duplicate Telemetry Explosion

If multiple layers emit the same event, correlation IDs allow aggregation.

---

# 163. Compiler Integration

Axiom compiler supports metadata:

```text
@service
@operation
@route
@requires_service
@idempotent
@retryable
@timeout
@streaming
@capability
@healthcheck
@version
```

---

# 164. Generated Metadata

Compiler may generate:

```text
.axservice
.axroute
.axclient
.axserver
.axcontract
```

---

# 165. Contract Validation

Compiler/build tools validate:

```text
input schema
output schema
error schema
version compatibility
capability requirements
streaming mode
```

---

# 166. Stub Generation

Generated client:

```text
ServiceClient
```

Generated server adapter:

```text
ServiceHandler
```

must use stable schemas.

---

# 167. ABI

Service ABI is schema-based.

It does not depend on private compiler object layout.

---

# 168. FFI

External services can implement the service contract through:

```text
C ABI
HTTP
RPC
IPC
provider interface
```

---

# 169. Service Contract Evolution

Compatible changes include:

```text
new optional field
new optional operation
new error subtype
```

subject to schema rules.

Breaking changes require:

```text
new interface version
```

---

# 170. Version Pinning

Critical services may pin:

```text
exact interface version
```

rather than accepting a range.

---

# 171. Runtime Compatibility

A client should fail clearly on incompatible service contracts.

---

# 172. Service Package

613/625 may package:

```text
service binary
service manifest
service contract
resources
configuration schema
security policy
```

---

# 173. Service Manifest

Example:

```text
service_id = "video.encoder"
version = "3.2.0"
interface = "video.encoder.v2"
visibility = "cluster"
capabilities = ["gpu"]
```

---

# 174. Service Manifest Security

Manifest capability declarations do not automatically grant authority.

---

# 175. Service Configuration

601 supplies:

```text
endpoints
registry
routing
timeouts
retry
health
security
resource limits
```

---

# 176. Configuration Reload

Traffic policy changes should be applied atomically.

Existing requests continue under their captured request context.

---

# 177. Policy Fingerprint

Every service routing policy snapshot receives a fingerprint.

This allows diagnostics to correlate behavior with policy versions.

---

# 178. Policy Rollback

A previous valid policy snapshot can be restored atomically.

---

# 179. Resource Governance

631 accounts:

```text
connections
requests
buffers
streams
bandwidth
queue memory
```

through 606.

---

# 180. Service Quotas

Per-service quotas:

```text
max_requests
max_concurrency
max_connections
max_streams
max_bandwidth
```

---

# 181. Tenant Quotas

Per-tenant limits can be layered over service limits.

---

# 182. Priority

Priority must not bypass:

```text
security
hard quotas
resource safety
```

---

# 183. Locality

Service routing may use:

```text
same process
same node
same zone
same region
```

when topology is known.

---

# 184. Service-to-Service Local Fast Path

Example:

```text
Service A
   ↓
same-process call adapter
   ↓
Service B
```

This optimization cannot bypass authorization.

---

# 185. IPC Fast Path

For same-machine services:

```text
631
 ↓
604
```

can avoid TCP overhead.

---

# 186. Network Fast Path

For remote services:

```text
631
 ↓
626
 ↓
609
```

---

# 187. Security Fast Path

Cached authorization decisions may be used only within their validity period.

Revocation must invalidate them.

---

# 188. Discovery Fast Path

Cached endpoints are acceptable when TTL and generation policy permit.

---

# 189. Health Fast Path

Passive health avoids active probe overhead.

---

# 190. Deterministic Routing

Testing mode can provide deterministic endpoint selection.

---

# 191. Routing Simulator

A simulator can model:

```text
services
instances
health
latency
failures
traffic
policies
```

without real networking.

---

# 192. Failure Injection

Inject:

```text
endpoint loss
latency
packet loss
timeout
service crash
registry outage
TLS failure
authorization denial
resource exhaustion
```

---

# 193. Chaos Testing Boundary

631 exposes fault-injection interfaces but does not require a production chaos framework.

---

# 194. Service Dependency Testing

Tests should validate:

```text
dependency unavailable
dependency slow
dependency overloaded
dependency returning errors
dependency recovering
```

---

# 195. Circuit Breaker Testing

Validate:

```text
Closed → Open
Open → HalfOpen
HalfOpen → Closed
HalfOpen → Open
```

---

# 196. Retry Testing

Validate:

```text
retryable
nonretryable
deadline exceeded
budget exceeded
unknown outcome
```

---

# 197. Hedging Testing

Validate duplicate execution and cancellation.

---

# 198. Load-Balancing Testing

Validate:

```text
distribution
health filtering
weighted routing
locality
failover
```

---

# 199. Security Testing

Validate:

```text
identity forgery
expired identity
capability escalation
route bypass
policy cache invalidation
TLS failure
certificate rotation
```

---

# 200. Performance Targets

Target:

```text
warm in-process service call
≈ local function-call-adapter overhead
```

when optimization is possible.

For remote calls:

```text
routing overhead
```

should remain bounded and substantially smaller than network latency.

---

# 201. Memory Targets

Normal unary service routing should not require:

```text
large heap allocations
```

per request.

Use:

```text
object pools
arena/request scopes
stack state
reusable buffers
```

where safe.

---

# 202. No Mandatory GC

631 must not require garbage collection.

Request lifetimes use:

```text
scoped ownership
explicit buffers
generation-safe handles
```

consistent with Axiom's memory model.

---

# 203. Async Integration

631 uses 607:

```text
Future
Task
CancelToken
Deadline
IoReactor
```

---

# 204. Synchronization Integration

608 provides:

```text
atomic state
locks
queues
wait mechanisms
```

---

# 205. Supervision Integration

605 supervises:

```text
service process
service instance
gateway
registry adapter
```

---

# 206. Coordination Integration

627 provides:

```text
membership
leases
fencing
leader ownership
distributed identity coordination
```

---

# 207. Distributed Data Integration

628 provides:

```text
service registry persistence
idempotency records
session state
service metadata
distributed cache
event streams
```

---

# 208. Distributed Compute Integration

630 provides:

```text
remote execution
worker placement
GPU execution
batch execution
```

631 can route service requests to compute-backed services.

---

# 209. Workflow Integration

629 can invoke:

```text
service call
```

as a workflow activity.

Service calls inherit workflow:

```text
deadline
identity
capability
trace context
retry semantics
```

with explicit retry ownership.

---

# 210. Package Integration

623 plugins may register service providers.

624 scripts may invoke services through capability-limited APIs.

---

# 211. UI Integration

619/622 may use 631 for:

```text
remote document services
cloud/local backend
collaboration
remote rendering
```

without requiring GUI awareness inside 631.

---

# 212. AI Integration

AI applications can use 631 for:

```text
model inference service
embedding service
vector search
media processing
distributed inference
```

while keeping AI-specific semantics outside the service core.

---

# 213. Service Gateway CLI

Tooling should support:

```text
axiom service list
axiom service inspect
axiom service health
axiom service routes
axiom service calls
axiom service policy
```

---

# 214. Route Explanation

A diagnostic command should explain:

```text
request
→ selected service version
→ filtered instances
→ selected endpoint
→ circuit state
→ retry policy
```

without exposing secrets.

---

# 215. Dependency Inspection

```text
axiom service graph
```

can display:

```text
A → B
A → C
B → D
```

with health and traffic statistics.

---

# 216. Service Contract Inspection

```text
axiom service contract video.encoder
```

shows:

```text
operations
schemas
versions
streaming
idempotency
security requirements
```

---

# 217. Runtime Profiles

### AXSERVICE_NONE

No distributed service runtime.

### AXSERVICE_LOCAL

Process-local services.

### AXSERVICE_IPC

Same-machine services.

### AXSERVICE_NETWORK

Remote services.

### AXSERVICE_CLUSTER

Discovery + load balancing + health.

### AXSERVICE_MESH

Full service mesh boundary.

### AXSERVICE_FULL

All capabilities.

Unused profiles must be dead-strippable.

---

# 218. Final Service Architecture

```text
                    SERVICE CLIENT
                         │
                         ▼
                 RequestContext
                         │
          ┌──────────────┼──────────────┐
          ▼              ▼              ▼
       Identity       Discovery       Policy
          │              │              │
          └──────────────┼──────────────┘
                         ▼
                Version Selection
                         │
                         ▼
                Health Filtering
                         │
                         ▼
              Capability Filtering
                         │
                         ▼
               Locality Filtering
                         │
                         ▼
                Load Balancing
                         │
          ┌──────────────┼──────────────┐
          ▼              ▼              ▼
       Circuit        Admission       Retry
       Breaker                         │
          └──────────────┬─────────────┘
                         ▼
                 Connection / IPC
                         │
                         ▼
                  Remote Service
                         │
                ┌────────┴────────┐
                ▼                 ▼
             607/630             605
             Execute          Supervise
```

---

# 219. Architecture Invariants

1. Service identity is distinct from endpoint identity.
2. Service identity is distinct from process identity.
3. Endpoint availability does not imply authorization.
4. Discovery is not authorization.
5. Health is not identity.
6. Liveness is not readiness.
7. A draining instance receives no new traffic.
8. Expired service leases cannot receive authoritative traffic.
9. Routing cannot grant capabilities.
10. Downstream capability must be attenuated.
11. Retry is never universally automatic.
12. Non-idempotent uncertain operations are not blindly retried.
13. Request deadlines propagate downstream.
14. Retry budgets are bounded.
15. Hedge budgets are bounded.
16. Circuit breakers are local routing state.
17. Outlier ejection does not rewrite authoritative health.
18. Soft routing preferences cannot override hard requirements.
19. Security policy cannot be bypassed by local fast paths.
20. In-process optimization must preserve service semantics.
21. IPC optimization must preserve authorization semantics.
22. Cached discovery must respect expiration.
23. Cached authorization must respect revocation.
24. Large responses should be referenceable.
25. Service state required for recovery must be persisted explicitly.
26. Sticky sessions are not persistence.
27. Sidecar is optional.
28. Cloud infrastructure is optional.
29. HTTP is optional.
30. A global registry is optional.
31. A service mesh is optional.
32. A service cannot silently escalate worker capabilities.
33. Routing policies are declarative.
34. Arbitrary routing scripts are not part of the hot path.
35. Connection pools are resource-governed.
36. Backpressure is bounded.
37. Load shedding is explicit.
38. Unknown outcome is a valid state.
39. Service contract versions are explicit.
40. Breaking API changes require versioning.
41. Service discovery does not imply service startup.
42. Service activation is delegated to 605.
43. Distributed coordination is delegated to 627.
44. Distributed data is delegated to 628.
45. Remote execution is delegated to 630.
46. Transport is delegated to 626/609.
47. Cryptography is delegated to 610.
48. Resource accounting is delegated to 606.
49. Local execution is delegated to 607.
50. Unused service-runtime components must be removable.

---

# 220. Acceptance Criteria

Implementation must demonstrate at minimum:

### Identity
- service identity;
- instance identity;
- generation;
- endpoint identity;
- identity rotation.

### Discovery
- registration;
- lease;
- expiration;
- cache;
- negative cache;
- stale discovery;
- version selection;
- registry failure.

### Routing
- round robin;
- weighted routing;
- least loaded;
- locality;
- consistent hash;
- health filtering;
- version routing;
- metadata routing.

### Reliability
- retry;
- retry budgets;
- deadlines;
- cancellation;
- circuit breaker;
- outlier ejection;
- hedging;
- fallback;
- bulkheads;
- load shedding.

### Security
- mTLS;
- service identity;
- authorization;
- capability attenuation;
- revocation;
- route security;
- secret isolation.

### Networking
- connection pooling;
- HTTP;
- RPC;
- IPC;
- streaming;
- backpressure;
- timeout.

### Lifecycle
- readiness;
- draining;
- graceful shutdown;
- rolling deployment;
- activation;
- dependency handling.

### Distributed behavior
- registry failover;
- endpoint failure;
- duplicate execution;
- unknown outcome;
- stale route;
- coordination loss.

### Observability
- tracing;
- metrics;
- request timeline;
- service graph;
- route explanation;
- audit.

### Tooling
- service list;
- service health;
- service graph;
- contract inspection;
- route inspection;
- deterministic simulator;
- fault injection.

**Target: ≥220 acceptance criteria.**

---

# 221. Completion

**BOOTSTRAP-631 — COMPLETE**

The distributed application stack now has a clear separation:

```text
629  → WHAT should happen?
       workflow / job / saga

630  → WHERE should computation happen?
       worker / node / GPU / cluster

631  → HOW should services communicate?
       discovery / routing / health / traffic / identity
```

Combined with:

```text
626 → network service transport
627 → distributed coordination
628 → distributed data
605 → service/process supervision
606 → resource governance
607 → local execution
603 → capabilities/security
610 → cryptography
```

This prevents the language runtime from collapsing workflow orchestration, compute scheduling, service routing, and transport into one oversized abstraction.

**NEXT TASK: BOOTSTRAP-632 — Native Distributed API Gateway, Edge Runtime, Reverse Proxy, Load Balancer, Ingress/Egress Policy, Rate Limiting, Authentication Boundary & Edge Service Runtime 5.0**
:::

BOOTSTRAP-631 hoàn tất và chuỗi đã tự động chuyển sang **BOOTSTRAP-632**.