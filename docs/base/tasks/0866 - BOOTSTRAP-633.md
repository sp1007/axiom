Tiếp tục với **BOOTSTRAP-633**.

:::writing{variant="document" id="31684" title="BOOTSTRAP-633 — Native Distributed API Contract, Schema Registry, RPC IDL, Code Generation, Client/Server Stubs, Compatibility Checking & Service SDK Runtime 5.0"}

# BOOTSTRAP-633
## Native Distributed API Contract, Schema Registry, RPC IDL, Code Generation, Client/Server Stubs, Compatibility Checking & Service SDK Runtime 5.0

**Status:** COMPLETE  
**Layer:** Distributed API / Contract / SDK Runtime  
**Depends on:** BOOTSTRAP-600 → BOOTSTRAP-632

---

# 1. Purpose

BOOTSTRAP-633 defines the native Axiom contract system for distributed APIs.

Its purpose is to make communication between:

- clients;
- servers;
- services;
- gateways;
- workers;
- applications;
- external integrations

strongly typed, versioned, inspectable, and independently evolvable.

The central principle is:

```text
API Contract
    ↓
Schema
    ↓
Generated Client / Server
    ↓
Transport
    ↓
Runtime
```

The application developer should not need to manually construct protocol frames, serialize every field, validate every request, or maintain duplicated client/server definitions.

---

# 2. Architectural Position

```text
                    Axiom Source
                         │
                         ▼
                 ┌───────────────┐
                 │ API Contract  │
                 │     633       │
                 └───────┬───────┘
                         │
              ┌──────────┼──────────┐
              ▼          ▼          ▼
          Client SDK   Server SDK   Schema
              │          │           │
              └──────┬───┴───────────┘
                     ▼
              626 / 631 / 632
                     │
              609 / 604 / 610
                     │
                  Network
```

---

# 3. Contract vs Implementation

A contract describes:

```text
operations
types
errors
streaming
compatibility
security requirements
timeouts
idempotency
```

It does not describe:

```text
internal algorithms
memory layout
database implementation
thread implementation
private state
```

---

# 4. Contract Identity

Every API contract has:

```text
ContractId
PublisherId
PackageId
Version
SchemaFingerprint
AbiFingerprint
ProtocolFingerprint
```

---

# 5. Contract Version

Contract versions use semantic versioning semantics.

However, compatibility is determined by schema rules, not by version numbers alone.

---

# 6. Contract Fingerprint

A canonical contract representation produces:

```text
ContractFingerprint
```

using 610 hashing.

Equivalent contracts must produce identical fingerprints.

---

# 7. Canonical Contract Representation

Canonicalization defines deterministic ordering for:

```text
types
fields
operations
errors
annotations
metadata
```

No source-file formatting affects the fingerprint.

---

# 8. Distributed API IDL

Axiom introduces a declarative API description.

Example:

```text
api UserService(version = "1.2") {
    get_user(UserId) -> User
    create_user(CreateUserRequest) -> User
}
```

---

# 9. Native Source Contracts

The same contract may be declared directly using Axiom declarations.

The IDL is therefore not required for ordinary Axiom-to-Axiom applications.

---

# 10. External IDL Boundary

Providers may import/export:

```text
OpenAPI
Protobuf
JSON Schema
GraphQL schema
other RPC IDLs
```

through adapters.

These are interoperability boundaries, not Axiom's canonical contract model.

---

# 11. Canonical Axiom Contract

The canonical representation is:

```text
AXAPI
```

with machine-readable:

```text
.axapi
```

metadata.

---

# 12. Service Definition

Canonical form:

```text
service UserService {
    operation get_user(
        request: GetUserRequest
    ) -> User
}
```

---

# 13. Operation Identity

Every operation has a stable:

```text
OperationId
```

Operation identity must not depend on source declaration order.

---

# 14. Operation Signature

An operation contains:

```text
OperationId
Name
RequestType
ResponseType
Errors
StreamingMode
SecurityPolicy
TimeoutPolicy
IdempotencyPolicy
Version
```

---

# 15. Streaming Modes

Supported:

```text
Unary
ServerStream
ClientStream
BidirectionalStream
```

---

# 16. Unary

```text
request → response
```

---

# 17. Server Streaming

```text
request → response*
```

---

# 18. Client Streaming

```text
request* → response
```

---

# 19. Bidirectional Streaming

```text
request* ↔ response*
```

---

# 20. Streaming Contract

Streaming operations explicitly define:

```text
ordering
completion
cancellation
backpressure
maximum message size
idle timeout
```

---

# 21. API Types

Contracts may contain:

```text
struct
enum
union
option
result
array
map
set
tuple
scalar
alias
opaque
```

---

# 22. Struct

Example:

```text
struct User {
    id: UserId
    name: String
    email: String
}
```

---

# 23. Stable Field Identity

Every serialized field receives a stable numeric or canonical field ID.

Renaming a field does not change its identity.

---

# 24. Field Removal

Removed fields remain reserved.

Their identifiers cannot silently be reused.

---

# 25. Optional Fields

Optionality is explicit.

Absence and default values are distinct when the schema requires that distinction.

---

# 26. Nullability

Axiom does not equate:

```text
optional
```

with:

```text
nullable
```

These are separate semantic concepts.

---

# 27. Option

```text
Option<T>
```

represents presence/absence.

---

# 28. Result

```text
Result<T, E>
```

represents successful or failed execution.

---

# 29. Error Contract

Every public operation can declare typed errors.

Example:

```text
operation get_user(...) -> User
    errors [
        NotFound
        PermissionDenied
        ServiceUnavailable
    ]
```

---

# 30. Error Identity

Errors have stable:

```text
ErrorId
```

and schema metadata.

---

# 31. Unknown Error

Clients must safely handle errors not known to their compiled version.

---

# 32. Error Categories

Standard categories:

```text
InvalidRequest
Unauthenticated
Unauthorized
NotFound
Conflict
RateLimited
Unavailable
DeadlineExceeded
Cancelled
Internal
ProtocolError
```

Applications may define domain errors.

---

# 33. Error Metadata

Errors may include:

```text
code
message
details
retryability
retry_after
request_id
```

Sensitive details are policy-controlled.

---

# 34. Retryability

An operation or error may declare whether retry is safe.

This metadata is consumed by 631/632.

---

# 35. Idempotency

Operations may declare:

```text
@idempotent
```

or provide an explicit idempotency-key strategy.

---

# 36. Side Effects

Operations can declare:

```text
read_only
idempotent
non_idempotent
transactional
```

descriptive metadata.

---

# 37. Timeout Metadata

Contracts may declare default:

```text
connect timeout
execution timeout
stream timeout
idle timeout
```

Runtime configuration can impose stricter limits.

---

# 38. Security Metadata

Operations may declare:

```text
@requires(identity)
@requires(capability("user.read"))
```

These declarations feed 603/627.

---

# 39. Capability Requirements

The generated client cannot manufacture a required capability.

---

# 40. Authentication Requirements

Contracts may specify:

```text
Anonymous
Authenticated
MutualTLS
ServiceIdentity
Capability
```

---

# 41. Tenant Context

Multi-tenant APIs may explicitly declare tenant context requirements.

Tenant identity must not be inferred from untrusted payload fields.

---

# 42. Request Context

Generated calls can receive:

```text
RequestContext
```

containing:

```text
RequestId
TraceContext
Deadline
Cancellation
Identity
Capabilities
Tenant
Metadata
```

---

# 43. Context Separation

Business request data and transport/security context remain separate.

---

# 44. Transport Independence

The same contract can execute through:

```text
IPC
UnixSocket
NamedPipe
TCP
TLS
HTTP
HTTP/2
HTTP/3
Axiom RPC
```

---

# 45. Transport Binding

A contract may define one or more transport bindings.

Example:

```text
UserService
    ├── AxiomRPC
    ├── HTTP
    └── IPC
```

---

# 46. HTTP Binding

Operations may map to:

```text
method
path
headers
query
body
response
```

---

# 47. RPC Binding

RPC binding maps:

```text
ServiceId
OperationId
Request
Response
```

directly to 626/631.

---

# 48. IPC Binding

Local services may map contracts onto 604.

---

# 49. Zero-Copy Binding

Where compatible with transport and schema layout, generated runtime may expose zero-copy views.

---

# 50. Ownership Modes

Generated data can be:

```text
BorrowedView
OwnedValue
MutableOwned
```

according to API semantics.

---

# 51. No Hidden Pointer API

Generated user-facing APIs should not expose raw pointers merely because a transport implementation uses them internally.

---

# 52. Serialization

612 provides canonical serialization.

633 adds contract-aware serialization.

---

# 53. Generated Encoder

For every supported request/response type:

```text
encode()
```

can be compiler-generated.

---

# 54. Generated Decoder

Decoder can produce:

```text
OwnedValue
```

or a validated:

```text
View
```

over an existing buffer.

---

# 55. Decode Limits

Every generated decoder can enforce:

```text
max message size
max nesting
max collection length
max string size
max map entries
```

---

# 56. Unknown Fields

Forward-compatible clients can preserve or ignore unknown fields according to schema policy.

---

# 57. Unknown Enum Values

Unknown enum values must not cause memory corruption or undefined behavior.

---

# 58. Unknown Union Variants

Unknown variants become a typed unknown representation where the compatibility mode permits it.

---

# 59. Compatibility Classes

633 distinguishes:

```text
SourceCompatible
BinaryCompatible
WireCompatible
BehaviorCompatible
SecurityCompatible
```

These are independent.

---

# 60. Backward Compatibility

A new server should continue accepting requests from supported older clients when the contract declares compatibility.

---

# 61. Forward Compatibility

An older client must safely process responses containing unknown fields when the schema permits forward compatibility.

---

# 62. Breaking Changes

Examples:

```text
remove required field
reuse field ID
change field wire type incompatibly
change operation identity
change streaming mode
change authentication requirement incompatibly
```

must be detected.

---

# 63. Compatibility Checker

Compiler tooling provides:

```text
ax api check
```

for comparing two contracts.

---

# 64. Compatibility Output

Results contain:

```text
Compatible
ConditionallyCompatible
Breaking
Unknown
```

with precise reasons.

---

# 65. No Overall Score

Compatibility is reported as a set of concrete changes rather than a single quality score.

---

# 66. Schema Registry

A schema registry stores:

```text
Contract
Schema
Version
Fingerprint
Publisher
CompatibilityMetadata
```

---

# 67. Registry Backends

```text
LocalRegistry
PackageRegistry
FileRegistry
HTTPRegistry
PrivateRegistry
EmbeddedRegistry
```

---

# 68. Registry Is Optional

Axiom applications can run entirely without a central registry.

Compiled contracts may be embedded in binaries/packages.

---

# 69. Local Contract Store

Developer environments should support a local registry for rapid iteration.

---

# 70. Registry Trust

Schemas from external publishers are verified using 610/625 trust mechanisms.

---

# 71. Registry Immutability

Published immutable contract versions cannot silently change.

---

# 72. Contract Deprecation

Registry metadata can mark:

```text
deprecated
sunset
replacement
```

without deleting historical versions.

---

# 73. Contract Discovery

Clients can query:

```text
service
contract
version
operation
schema
```

when discovery is permitted.

---

# 74. Service Discovery Integration

631 provides runtime service discovery.

633 provides contract discovery.

These remain separate.

---

# 75. Contract Mismatch

If client and server fingerprints are incompatible, the runtime should fail before unsafe execution.

---

# 76. Negotiation

Optional negotiation can select:

```text
common contract version
common transport
common encoding
```

---

# 77. No Unsafe Downgrade

Security requirements must not be weakened merely to find a compatible version.

---

# 78. API Version Selection

Version selection may use:

```text
exact
compatible
range
latest-compatible
pinned
```

---

# 79. Generated Client

Example:

```text
client UserServiceClient {
    fn get_user(
        ctx: RequestContext,
        request: GetUserRequest
    ) -> Future<Result<User, UserServiceError>>
}
```

---

# 80. Generated Server

Example:

```text
service UserService {
    fn get_user(
        ctx: RequestContext,
        request: GetUserRequest
    ) -> Result<User, UserServiceError>
}
```

---

# 81. Server Adapter

The generated adapter converts transport requests into typed Axiom calls.

---

# 82. Client Transport

Generated clients depend on an abstract:

```text
RpcTransport
```

rather than a specific network library.

---

# 83. Transport Interface

```text
struct RpcTransport {
    fn call(...)
    fn open_stream(...)
    fn close(...)
}
```

---

# 84. Connection Reuse

Transport providers may reuse connections using 609/626.

---

# 85. Client Pool

Generated clients can use connection pools.

---

# 86. Client Load Balancing

Client-side selection may use 631.

---

# 87. Gateway Integration

632 may terminate the external API and forward a generated contract call internally.

---

# 88. Server Registration

Generated service servers can register:

```text
ServiceId
ContractFingerprint
OperationSet
Health
Capabilities
```

with 631.

---

# 89. Contract Registration

A server cannot claim a contract it does not implement.

---

# 90. Implementation Verification

The compiler verifies:

```text
operation exists
request type matches
response type matches
error set compatible
security requirements satisfied
streaming mode matches
```

---

# 91. Method Implementation

Struct-only Axiom semantics remain unchanged.

Generated service implementations are ordinary functions.

---

# 92. Example

```text
struct UserService

fn UserService.get_user(
    ctx: RequestContext,
    request: GetUserRequest
) -> Result<User, UserError> {
    ...
}
```

No class hierarchy is required.

---

# 93. Override / Replacement

A provider can replace a default implementation through explicit contract-bound registration.

There is no implicit inheritance-based override.

---

# 94. Middleware

Generated servers may install typed middleware:

```text
AuthenticationMiddleware
AuthorizationMiddleware
ValidationMiddleware
MetricsMiddleware
TracingMiddleware
RateLimitMiddleware
```

---

# 95. Middleware Ordering

Middleware order is deterministic and compiler/tooling validated.

---

# 96. Middleware Scope

Middleware can apply to:

```text
server
service
operation
transport
tenant
```

---

# 97. Middleware Safety

Middleware cannot silently bypass mandatory security middleware.

---

# 98. Interceptors

Client/server interceptors can inspect:

```text
RequestContext
contract metadata
operation metadata
```

without manually parsing wire data.

---

# 99. Error Mapping

Transport errors map to typed runtime errors.

Example:

```text
timeout
→ DeadlineExceeded

connection failure
→ Unavailable

authentication failure
→ Unauthenticated
```

---

# 100. Error Preservation

Original provider-specific diagnostic information may be preserved in a bounded opaque field.

---

# 101. Cancellation

Cancellation propagates:

```text
client
 ↓
transport
 ↓
gateway
 ↓
server
 ↓
downstream work
```

when supported.

---

# 102. Deadline Propagation

Remaining deadline is forwarded rather than original deadline.

---

# 103. Retry Metadata

Generated client uses contract metadata to inform 631/632 retry policy.

It must not independently create unbounded retries.

---

# 104. Streaming Backpressure

Generated streaming APIs integrate with 607/608 flow control.

---

# 105. Stream API

Example:

```text
stream UserEventStream {
    fn next() -> Future<Result<UserEvent>>
    fn cancel()
}
```

---

# 106. Async Iteration

Streaming responses may expose an Axiom async iterator abstraction.

---

# 107. Stream Cancellation

Cancellation releases:

```text
transport
buffers
server resources
subscriptions
```

within bounded time.

---

# 108. Stream Limits

Contracts can specify:

```text
max message
max concurrent streams
max stream duration
idle timeout
```

---

# 109. Batch APIs

Contracts may declare batch operations.

The compiler does not automatically transform arbitrary unary calls into batches.

---

# 110. Pagination

Generated API metadata may describe:

```text
page token
cursor
limit
continuation
```

but semantics remain application-defined.

---

# 111. Long-Running Operations

633 may define an operation returning:

```text
OperationHandle
```

that integrates with 629 workflows/jobs.

---

# 112. Async Job Contract

Example:

```text
submit_job(...) -> JobHandle
get_job(JobHandle) -> JobStatus
cancel_job(JobHandle) -> Result<void>
```

---

# 113. Event APIs

Services may expose typed events through 628 event streams.

---

# 114. Event Contract

```text
event UserCreated {
    id: UserId
    timestamp: Timestamp
}
```

---

# 115. Event Versioning

Events follow the same schema evolution rules as request/response types.

---

# 116. Event Replay

Events can declare whether replay is supported.

---

# 117. Event Consumer Compatibility

Consumers may subscribe only to versions they understand.

---

# 118. Idempotent Consumer

Generated event clients can expose deduplication metadata from 628.

---

# 119. Contract Registry + Package System

Contracts can be packaged inside:

```text
.axpkg
```

and indexed by 625.

---

# 120. Offline Contract Use

A package can contain all contracts required by an application.

No online registry is required at runtime.

---

# 121. Contract Cache

Compiled contract artifacts can be cached using:

```text
ContractFingerprint
CompilerVersion
Target
```

---

# 122. Incremental Generation

Changing one operation should not force regeneration of unrelated contracts.

---

# 123. Generated Code Stability

Generated source/IR should be deterministic.

Identical contract + compiler + target produces equivalent output.

---

# 124. ABI

Generated native APIs have a stable ABI boundary where explicitly marked.

---

# 125. ABI Fingerprint

ABI metadata includes:

```text
target
architecture
calling convention
layout
alignment
endianness
contract fingerprint
```

---

# 126. Cross-Language ABI

External languages may use generated C-compatible adapters where required.

---

# 127. No C Dependency

C ABI is an interoperability boundary, not an internal compiler dependency.

---

# 128. Memory Layout

Wire layout and native memory layout remain separate concepts.

---

# 129. Native Optimization

Compiler may optimize native representation while preserving wire compatibility.

---

# 130. Zero-Copy Conditions

Zero-copy decoding is allowed only if:

```text
encoding
alignment
lifetime
immutability
schema
```

are compatible.

---

# 131. Borrowed View Lifetime

A borrowed view cannot outlive its backing buffer.

Compiler/runtime validation must prevent unsafe use.

---

# 132. No GC Requirement

Contract runtime does not require garbage collection.

---

# 133. Resource Ownership

Buffers, streams, connections and transport handles use explicit ownership.

---

# 134. Handle Safety

Runtime handles use generation-safe identifiers.

---

# 135. Capability Integration

Operations may require explicit:

```text
Capability<T>
```

at the call boundary.

---

# 136. Capability Propagation

Only authorized capabilities are propagated to downstream services.

---

# 137. Capability Attenuation

A generated client can receive a restricted capability set.

---

# 138. Secret Fields

Schema fields may be annotated:

```text
@secret
```

Such fields are excluded from ordinary:

```text
logs
traces
debug dumps
metrics labels
```

---

# 139. Sensitive Metadata

Contract metadata can classify:

```text
Public
Internal
Sensitive
Secret
```

---

# 140. Validation

Generated validators can validate:

```text
length
range
pattern
enum
required
format
nested constraints
```

before transport.

---

# 141. Server Validation

Server validation remains mandatory even when client validation exists.

---

# 142. Canonicalization

Canonical values can be normalized before contract fingerprinting or signing.

---

# 143. Schema Signatures

Published contracts may be signed.

---

# 144. Trust Chain

Signature verification uses:

```text
610
625
603
```

---

# 145. Untrusted Contract

An untrusted contract may be inspected but cannot automatically grant executable capabilities.

---

# 146. Contract Code Generation Security

Generated code must not execute arbitrary schema directives.

---

# 147. Schema Limits

Registry and compiler enforce:

```text
max types
max fields
max nesting
max annotation size
max generated output
```

---

# 148. Denial-of-Service Protection

A malicious schema cannot cause unbounded compiler or decoder work.

---

# 149. Compiler Integration

Compiler phases:

```text
parse
 ↓
contract analysis
 ↓
schema lowering
 ↓
compatibility validation
 ↓
code generation
 ↓
IR
 ↓
native compilation
```

---

# 150. IR Representation

IR may contain:

```text
ContractRef
OperationRef
Encode
Decode
Validate
Call
StreamOpen
StreamSend
StreamReceive
StreamClose
```

---

# 151. Optimization

Compiler can:

```text
inline small encoders
eliminate unused fields
specialize serializers
remove unused operations
remove unused transports
```

---

# 152. Dead Stripping

An application using one operation should not automatically link every generated service.

---

# 153. Reflection

Runtime reflection is not required.

Compile-time contract metadata is preferred.

---

# 154. Runtime Introspection

Optional metadata package can provide:

```text
service list
operation list
schema
version
fingerprint
```

---

# 155. AI-Readable Metadata

Generated `.axapi` should contain:

```text
purpose
types
operations
constraints
security
errors
compatibility
examples
```

in deterministic machine-readable form.

---

# 156. Documentation Generation

Tooling can generate:

```text
HTML
Markdown
JSON
Axiom metadata
```

from contracts.

---

# 157. API Explorer

Optional GUI/CLI can inspect contracts without requiring the service to execute arbitrary code.

---

# 158. CLI

Canonical commands:

```text
ax api inspect
ax api validate
ax api check
ax api generate
ax api diff
ax api publish
ax api fetch
ax api docs
```

---

# 159. API Diff

Example:

```text
ax api diff old.axapi new.axapi
```

reports field, operation, error, security and transport changes.

---

# 160. Compatibility CI

Build systems can fail when a declared compatibility policy is violated.

---

# 161. Compatibility Policy

Projects can choose:

```text
BackwardOnly
ForwardOnly
Bidirectional
WireOnly
Strict
```

---

# 162. Version Pinning

Production clients can pin:

```text
ContractFingerprint
```

instead of relying solely on semantic versions.

---

# 163. Version Range

Development clients may accept:

```text
>=1.2 <2.0
```

when compatibility rules permit.

---

# 164. Service Upgrade

A service can expose multiple contract versions simultaneously.

---

# 165. Contract Routing

631/632 can select an implementation based on contract/version.

---

# 166. Graceful Migration

Typical migration:

```text
v1 client
   ↓
gateway
   ↓
v1 server

v2 client
   ↓
gateway
   ↓
v2 server
```

---

# 167. Adapter Contract

Explicit adapters may translate:

```text
v1 request
→
v2 request
```

but must be declared and tested.

---

# 168. No Silent Semantic Translation

The runtime must not assume that a structurally compatible change is semantically equivalent.

---

# 169. Generated Test Client

Compiler tooling can generate test clients for every operation.

---

# 170. Contract Test Server

A generated conformance server validates:

```text
encoding
decoding
validation
errors
streaming
```

without implementing business logic.

---

# 171. Golden Tests

Wire representations can be stored as deterministic golden fixtures.

---

# 172. Fuzz Testing

Generated decoders must support fuzz testing.

---

# 173. Differential Testing

Two implementations of the same contract can be compared against identical generated requests.

---

# 174. Property Tests

Properties include:

```text
encode → decode ≈ identity
unknown fields do not corrupt known fields
invalid input never escapes decoder
```

---

# 175. Transport Tests

The same contract test suite should run over:

```text
IPC
TCP
TLS
HTTP
AxiomRPC
```

where providers exist.

---

# 176. Failure Tests

Test:

```text
timeout
disconnect
partial response
malformed response
server restart
contract mismatch
authentication failure
```

---

# 177. Deterministic Testing

A virtual transport and deterministic scheduler allow reproducible distributed API tests.

---

# 178. Mock Provider

A test provider can replace actual transport.

---

# 179. Fake Server

Generated fake servers can verify client behavior without network access.

---

# 180. Contract-Based Mocking

Mocks are generated from contracts rather than manually maintained interfaces.

---

# 181. Performance Model

Target characteristics:

```text
low allocation
bounded serialization overhead
zero-copy where possible
connection reuse
compile-time validation
```

---

# 182. Small API Optimization

Small request/response objects should avoid unnecessary heap allocation.

---

# 183. Large Payload Optimization

Large payloads should use:

```text
streaming
views
chunked buffers
zero-copy
```

where practical.

---

# 184. Batch Serialization

Repeated homogeneous messages may use batch encoders.

---

# 185. CPU Affinity

Serialization work may be scheduled through 607/606.

---

# 186. Resource Accounting

Every transport call can charge:

```text
CPU
memory
network bytes
connections
streams
```

to the appropriate scope.

---

# 187. Quotas

API contracts can carry descriptive quota metadata.

Enforcement remains in 606/631/632.

---

# 188. Observability

Generated clients and servers emit:

```text
operation name
contract fingerprint
latency
status
retry count
bytes
```

without exposing secrets.

---

# 189. Trace Naming

Canonical span naming:

```text
Service.Operation
```

with stable identifiers available for machine analysis.

---

# 190. Metrics Cardinality

Unbounded user data must never automatically become metric labels.

---

# 191. Logging

Generated runtime errors include:

```text
request_id
operation_id
contract_fingerprint
```

where safe.

---

# 192. Configuration

Default client/server behavior is configurable through 601.

---

# 193. Security Policy

Contract requirements cannot weaken application-level security policy.

Runtime policy may strengthen restrictions.

---

# 194. Package Registry Integration

625 can publish:

```text
contract
generated SDK
compatibility metadata
documentation
```

as package artifacts.

---

# 195. Dependency Resolution

A client package may declare:

```text
requires api UserService >=1.2 <2
```

and resolve a compatible contract.

---

# 196. Offline Builds

All generated code must be reproducible offline when contract artifacts are available locally.

---

# 197. Reproducibility

Generated artifacts should be independent of:

```text
machine path
wall-clock time
randomness
```

unless explicitly requested.

---

# 198. Source Mapping

Generated code maintains mapping back to:

```text
contract
operation
field
```

for diagnostics.

---

# 199. IDE Integration

Tooling can provide:

```text
go to operation
go to schema
find consumers
find implementations
show compatibility
generate client
```

---

# 200. AI Integration

AI tooling can consume `.axapi` without parsing implementation code.

The contract metadata becomes the authoritative public API description.

---

# 201. API Change Analysis

AI/compiler tooling can identify:

```text
affected clients
affected servers
breaking changes
security changes
transport changes
```

without generating a subjective overall score.

---

# 202. Service SDK

The generated SDK may contain:

```text
Client
Server
Types
Errors
Validators
Serializers
Transport adapters
Documentation metadata
Tests
```

---

# 203. SDK Profiles

```text
ClientOnly
ServerOnly
ClientServer
TypesOnly
SchemaOnly
Interop
```

---

# 204. Minimal Client

A small application using one unary operation should be able to link only:

```text
schema
encoder
decoder
transport
operation
```

rather than the complete SDK.

---

# 205. Minimal Server

Similarly, unused client-side facilities must be removable from server binaries.

---

# 206. Interop SDK

External languages may receive generated:

```text
C ABI
JSON schema
OpenAPI
```

artifacts.

---

# 207. Native Axiom Preference

Axiom-to-Axiom communication uses native contract representation by default.

---

# 208. External Compatibility

External protocol support must not distort the native contract model.

---

# 209. Final Contract Flow

```text
                     .axapi
                       │
                 ┌─────▼─────┐
                 │   Schema  │
                 │ Registry  │
                 └─────┬─────┘
                       │
             ┌─────────┴─────────┐
             ▼                   ▼
       Generated Client    Generated Server
             │                   │
             ▼                   ▼
          626/631             626/631
             │                   │
             └─────────┬─────────┘
                       ▼
                    609/604
                       │
                    Network
```

---

# 210. Architecture Invariants

1. Contract identity is deterministic.
2. Contract fingerprints are canonical.
3. Field IDs are stable.
4. Removed field IDs cannot be silently reused.
5. Wire schema is independent from native memory layout.
6. Source compatibility and wire compatibility are distinct.
7. Security compatibility is independently checked.
8. Unknown fields are handled explicitly.
9. Unknown enum values cannot corrupt execution.
10. Unknown variants are safely represented.
11. Contract versions are immutable once published.
12. Registry is optional.
13. Centralized registry is not required at runtime.
14. Generated code is deterministic.
15. Generated code is statically typed.
16. Reflection is optional.
17. Runtime code generation is not required.
18. Client cannot manufacture capabilities.
19. Authentication context is separate from business payload.
20. Secret fields are excluded from ordinary telemetry.
21. Decoder resource usage is bounded.
22. Streaming has explicit backpressure.
23. Cancellation propagates.
24. Deadlines propagate.
25. Retry behavior is bounded.
26. Non-idempotent calls are not blindly retried.
27. Transport is replaceable.
28. IPC and network transports share contract semantics.
29. Gateway does not redefine contract identity.
30. Service discovery and contract discovery remain separate.
31. Compatibility checking is deterministic.
32. Breaking changes are explicit.
33. Semantic equivalence is never inferred solely from structure.
34. Generated adapters preserve security requirements.
35. Generated clients do not bypass authorization.
36. Generated servers verify contract implementation.
37. Generated schemas are fuzz-testable.
38. Generated wire formats are deterministic where canonical encoding is requested.
39. No mandatory GC exists.
40. Unused SDK features are dead-strippable.

---

# 211. Acceptance Criteria

The implementation must demonstrate at least:

### Contract
- service definitions;
- operation definitions;
- stable IDs;
- versioning;
- fingerprints;
- canonicalization;
- typed errors;
- streaming contracts;
- security metadata.

### Schema
- structs;
- enums;
- unions;
- options;
- results;
- collections;
- optional fields;
- unknown fields;
- unknown enum values;
- validation;
- schema evolution.

### Generation
- client generation;
- server generation;
- serializer generation;
- decoder generation;
- validator generation;
- documentation generation;
- test generation;
- deterministic output.

### Runtime
- unary RPC;
- server streaming;
- client streaming;
- bidirectional streaming;
- cancellation;
- deadline propagation;
- connection pooling;
- load balancing;
- retries;
- typed errors.

### Compatibility
- backward compatibility checks;
- forward compatibility checks;
- wire compatibility;
- ABI compatibility;
- security compatibility;
- breaking-change diagnostics;
- version ranges;
- fingerprint pinning.

### Registry
- local registry;
- package registry;
- remote registry provider;
- signed schemas;
- immutable versions;
- offline cache;
- schema discovery.

### Security
- authentication metadata;
- authorization metadata;
- capability requirements;
- secret-field classification;
- bounded decoding;
- malformed-schema protection;
- credential propagation;
- no capability escalation.

### Integration
- 604 IPC;
- 609 networking;
- 610 cryptography;
- 612 serialization;
- 625 package registry;
- 626 application protocols;
- 627 distributed identity;
- 628 distributed data;
- 631 service runtime;
- 632 gateway.

### Tooling
- `ax api inspect`;
- `ax api validate`;
- `ax api check`;
- `ax api generate`;
- `ax api diff`;
- `ax api publish`;
- `ax api fetch`;
- `ax api docs`.

### Testing
- golden wire tests;
- fuzzing;
- property testing;
- differential testing;
- transport conformance;
- deterministic virtual transport;
- timeout tests;
- cancellation tests;
- compatibility tests;
- security tests.

**Target: ≥250 acceptance criteria.**

---

# 212. Completion

**BOOTSTRAP-633 — COMPLETE**

Axiom now has a complete contract path:

```text
Type System
    ↓
AXAPI Contract
    ↓
Schema/Fingerprint
    ↓
Generated SDK
    ↓
631 Service Runtime / 632 Gateway
    ↓
626 Protocols
    ↓
609/604 Transport
```

This establishes a strong foundation for building distributed applications without requiring manually maintained client/server interfaces.

**NEXT TASK: BOOTSTRAP-634 — Native Distributed Event Bus, Pub/Sub, Message Broker Boundary, Topic Partitioning, Consumer Groups, Delivery Guarantees & Stream Processing Runtime 5.0**
:::