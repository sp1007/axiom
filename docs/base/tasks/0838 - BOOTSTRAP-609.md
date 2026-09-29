Tiếp tục với **BOOTSTRAP-609**, giữ đúng hướng kiến trúc đã xây dựng: networking là một runtime layer độc lập, async-native, capability-controlled và không ép TLS/HTTP implementation vào core.

:::writing{variant="document" id="58321" title="BOOTSTRAP-609 — Native Networking, Sockets, DNS, TLS Boundary, HTTP Transport & Network I/O Runtime 5.0"}

# BOOTSTRAP-609
# Native Networking, Sockets, DNS, TLS Boundary, HTTP Transport & Network I/O Runtime 5.0

**Status:** ARCHITECTURE SPECIFICATION — COMPLETE  
**Layer:** Native Runtime / Platform Runtime  
**Depends on:** BOOTSTRAP-600 → 608  
**Primary dependencies:** State, Config, Diagnostics, Security, IPC, Supervisor, Resource Governor, Scheduler, Synchronization  
**Targets:** Windows, Linux, macOS, Android, iOS, WASM, Embedded

---

# 1. Purpose

BOOTSTRAP-609 defines Axiom's native networking foundation.

It provides:

- IP addresses
- IPv4 / IPv6
- TCP
- UDP
- Unix-domain/local sockets
- socket lifecycle
- asynchronous network I/O
- DNS resolution
- connection establishment
- connection pooling
- network buffers
- scatter/gather I/O
- backpressure
- cancellation
- deadlines
- proxy transport
- TLS boundary
- HTTP transport foundation
- WebSocket foundation
- multicast/broadcast
- network diagnostics
- deterministic network testing
- platform-specific network adapters

The architecture must allow application code to use networking without knowing the underlying operating system.

At the same time, the runtime must not hide important costs or security decisions.

---

# 2. Design Goals

## 2.1 Primary goals

Axiom networking MUST provide:

1. native performance
2. asynchronous I/O
3. predictable memory usage
4. explicit ownership
5. cancellation
6. deadlines
7. bounded buffering
8. capability-controlled access
9. IPv4/IPv6 support
10. cross-platform API stability
11. zero-copy opportunities
12. efficient streaming
13. connection reuse
14. deterministic testing
15. minimal runtime overhead

---

# 3. Non-Goals

The core networking layer does NOT attempt to implement:

- a complete browser networking stack
- HTTP application frameworks
- DNS authoritative servers
- VPN implementations
- firewall implementations
- cryptographic algorithms
- certificate authority infrastructure
- a full TLS implementation
- distributed consensus
- service meshes
- cloud-specific networking

Those belong to higher layers.

---

# 4. Architectural Principle

Networking is divided into layers:

```text
Application
    ↓
HTTP / WebSocket
    ↓
Secure Transport Boundary
    ↓
Connection / Stream
    ↓
TCP / UDP / Local Socket
    ↓
Network I/O Runtime
    ↓
Scheduler / Executor
    ↓
OS Network Backend
```

Security is orthogonal:

```text
Security Policy
      ↓
Network Capability
      ↓
Socket Operation
```

Resource management is orthogonal:

```text
Resource Governor
      ↓
socket / connection / buffer / bandwidth budget
```

Diagnostics is orthogonal:

```text
Network Event
      ↓
Metrics / Trace / Structured Log
```

---

# 5. Core Invariants

## NET-I01

No network operation may bypass the Axiom security capability system.

## NET-I02

No socket operation may silently allocate unbounded memory.

## NET-I03

Every asynchronous operation has a defined completion state.

## NET-I04

Every network operation may be cancelled unless the underlying platform explicitly prevents cancellation.

## NET-I05

Every long-running operation supports a deadline.

## NET-I06

Network buffers have explicit ownership.

## NET-I07

A closed socket never produces a successful future completion.

## NET-I08

DNS is not global mutable application state.

## NET-I09

Connection pools are explicitly owned.

## NET-I10

Network connections are not checkpointable application state.

A checkpoint stores enough information to reconnect, not the live socket itself.

---

# 6. Network Address Model

Axiom defines:

```text
IpAddress
IpV4
IpV6
SocketAddress
HostName
Port
```

Conceptually:

```text
SocketAddress =
    IpV4Address + Port
    IpV6Address + Port
    LocalAddress
```

---

# 7. IPv4

IPv4 is represented as exactly 32 bits.

```text
type IpV4 = struct {
    value: u32
}
```

Construction:

```text
IpV4.parse("192.168.1.10")
```

Formatting:

```text
address.to_string()
```

No heap allocation is required for binary representation.

---

# 8. IPv6

IPv6 is represented as exactly 128 bits.

```text
type IpV6 = struct {
    hi: u64
    lo: u64
}
```

The implementation must support:

- compressed notation
- expanded notation
- IPv4-mapped addresses
- scope identifiers
- link-local addresses

---

# 9. IP Classification

The runtime exposes classification operations:

```text
address.is_loopback()
address.is_private()
address.is_link_local()
address.is_multicast()
address.is_unspecified()
address.is_global()
```

These functions are deterministic and do not perform network access.

---

# 10. Port

```text
type Port = u16
```

Ports outside `0..65535` are invalid.

Port `0` has platform-defined meaning during bind and is therefore represented explicitly rather than rejected universally.

---

# 11. Host Name

```text
type HostName = struct {
    value: String
}
```

Host names must be validated before resolver access.

The runtime does not automatically execute shell commands or invoke external resolver programs.

---

# 12. Socket Types

Axiom defines:

```text
SocketType:
    Tcp
    Udp
    LocalStream
    LocalDatagram
```

Optional platform-specific socket types may exist behind extensions.

---

# 13. Socket Lifecycle

A socket transitions through:

```text
Created
    ↓
Bound
    ↓
Listening
    ↓
Connected
    ↓
Closing
    ↓
Closed
```

UDP may skip `Listening`.

Client TCP:

```text
Created
  ↓
Connecting
  ↓
Connected
```

Failure:

```text
Connecting
  ↓
Failed
```

---

# 14. Socket Ownership

A socket is represented by an opaque runtime handle.

```text
Socket
```

The user does not manipulate:

```text
SOCKET
int fd
```

directly through safe Axiom APIs.

The platform handle is stored internally.

---

# 15. Generation Safety

A socket handle contains:

```text
SocketId
Generation
```

Conceptually:

```text
SocketHandle {
    index: u32
    generation: u32
}
```

A stale handle cannot accidentally operate on a newly-created socket reusing the same OS descriptor.

---

# 16. TCP API

Conceptual API:

```text
TcpListener.bind(address)
TcpListener.accept()
TcpStream.connect(address)
TcpStream.read(buffer)
TcpStream.write(buffer)
TcpStream.shutdown(direction)
TcpStream.close()
```

Async variants are first-class:

```text
await stream.read(...)
await stream.write(...)
```

---

# 17. TCP Stream Semantics

TCP provides an ordered byte stream.

The API MUST NOT expose TCP as a message protocol.

Applications that need messages must use:

- framing
- length prefixes
- delimiters
- higher-level protocol layers

---

# 18. TCP Partial Reads

A read may return fewer bytes than requested.

Example:

```text
read(buffer[4096])
```

may return:

```text
37 bytes
```

even if the connection remains healthy.

The runtime must never silently reinterpret partial reads as protocol messages.

---

# 19. TCP Partial Writes

A write may also complete partially.

Therefore:

```text
write(data)
```

returns the number of bytes accepted.

A higher-level streaming API may provide:

```text
write_all(data)
```

which continues until:

- all bytes are written
- cancellation
- deadline
- connection failure

---

# 20. Half Close

TCP supports independent shutdown directions.

```text
stream.shutdown(Read)
stream.shutdown(Write)
stream.shutdown(Both)
```

Half-close must be preserved rather than translated into immediate full close.

---

# 21. EOF

A successful TCP EOF is distinct from an error.

```text
ReadResult:
    Data
    EndOfStream
    Error
```

---

# 22. UDP

UDP is datagram-oriented.

```text
UdpSocket.bind(address)
UdpSocket.send_to(buffer, address)
UdpSocket.receive_from(buffer)
```

A datagram is atomic from the API perspective.

If the supplied receive buffer is too small, the API must report truncation rather than pretending the complete datagram was received.

---

# 23. UDP Connected Mode

A UDP socket may optionally be connected to a peer:

```text
udp.connect(address)
```

This filters packets to/from the configured peer according to OS semantics and simplifies send/receive APIs.

---

# 24. Multicast

The UDP layer supports:

```text
join_multicast_group()
leave_multicast_group()
set_multicast_interface()
set_multicast_hops()
```

Multicast operations require an explicit network capability.

---

# 25. Broadcast

Broadcast is explicitly enabled:

```text
socket.enable_broadcast()
```

A default capability policy may deny broadcast.

---

# 26. Unix-Domain / Local Sockets

Axiom provides:

```text
LocalListener
LocalStream
LocalDatagram
```

Platform mapping:

```text
Linux/macOS → AF_UNIX
Windows     → AF_UNIX where supported
```

Older Windows versions may use named-pipe transport through the platform adapter.

The abstraction remains:

```text
LocalEndpoint
```

rather than exposing OS-specific path semantics.

---

# 27. Local Endpoint

A local endpoint can be:

```text
FilesystemPath
AbstractName
PlatformName
```

Platform support determines which forms are available.

---

# 28. Socket Options

Common options are standardized:

```text
reuse_address
reuse_port
keep_alive
no_delay
receive_buffer_size
send_buffer_size
receive_timeout
send_timeout
broadcast
multicast_loop
```

Platform-specific options are exposed through:

```text
SocketOption.platform(...)
```

Safe code cannot arbitrarily modify memory or OS structures through this interface.

---

# 29. TCP_NODELAY

TCP_NODELAY is explicitly configurable:

```text
stream.set_no_delay(true)
```

The default is platform/profile dependent and must be deterministic within an Axiom runtime profile.

---

# 30. Keepalive

Keepalive configuration:

```text
KeepAliveConfig {
    enabled
    idle
    interval
    count
}
```

Not every platform supports every field.

Unsupported fields produce explicit capability errors rather than being silently ignored.

---

# 31. Network I/O Abstraction

Axiom defines:

```text
NetworkReactor
```

with platform implementations.

Windows:

```text
Winsock + IOCP
```

Linux:

```text
epoll
```

with optional:

```text
io_uring
```

macOS:

```text
kqueue
```

Android/iOS:

```text
native socket APIs + platform event integration
```

WASM:

```text
host-provided networking
```

---

# 32. Proactor vs Reactor

Axiom does not expose reactor/proactor terminology to ordinary application code.

The abstraction is:

```text
AsyncNetworkBackend
```

The backend chooses the efficient native mechanism.

---

# 33. Integration With BOOTSTRAP-607

Network operations become scheduler tasks.

Example:

```text
async fn download() {
    let connection = await TcpStream.connect(address)
    let n = await connection.read(buffer)
}
```

Compiler lowering:

```text
async function
      ↓
state machine
      ↓
NetworkOperation
      ↓
IO backend
      ↓
completion event
      ↓
Executor
```

No dedicated OS thread is required per socket.

---

# 34. Integration With BOOTSTRAP-608

Network completion events use the synchronization model defined by BOOTSTRAP-608.

The networking runtime MUST NOT implement an independent incompatible memory model.

Atomic operations use:

```text
Relaxed
Acquire
Release
AcqRel
SeqCst
```

where required.

---

# 35. Cancellation

Every asynchronous network operation accepts a cancellation token.

```text
await stream.read(buffer, cancel: token)
```

Cancellation transitions:

```text
Pending
  ↓
Cancelling
  ↓
Cancelled
```

If the OS reports completion concurrently with cancellation, exactly one terminal result is delivered.

---

# 36. Deadlines

Every blocking/asynchronous network operation supports:

```text
deadline: Instant?
```

Examples:

```text
connect(address, deadline)
read(buffer, deadline)
write(buffer, deadline)
dns.resolve(host, deadline)
```

Timeout is represented separately from generic failure.

---

# 37. Timeout Semantics

A timeout means:

```text
operation did not complete before deadline
```

It does not necessarily mean:

```text
connection is broken
```

The API must distinguish:

```text
Timeout
Cancelled
ConnectionClosed
NetworkError
ProtocolError
```

---

# 38. Scatter/Gather I/O

The runtime provides:

```text
IoVec
```

and:

```text
readv()
writev()
```

where supported.

Example:

```text
writev([
    header,
    payload,
    trailer
])
```

This allows multiple buffers to be sent without concatenation.

---

# 39. Network Buffer

Core abstraction:

```text
NetworkBuffer
```

Properties:

```text
capacity
length
offset
ownership
```

A buffer may be:

```text
Owned
Borrowed
Shared
Pooled
Mapped
```

Safe APIs enforce the associated lifetime rules.

---

# 40. Buffer Ownership

A received buffer belongs to the operation result.

After ownership transfer:

```text
consumer owns buffer
```

The network backend must not modify it.

This prevents use-after-receive races.

---

# 41. Buffer Pool

High-throughput networking uses size classes:

```text
256 B
1 KiB
4 KiB
16 KiB
64 KiB
256 KiB
...
```

The exact classes are configurable.

Pools are bounded by BOOTSTRAP-606 budgets.

---

# 42. Zero-Copy

Where supported, Axiom may use:

```text
sendfile
splice
platform zero-copy
registered buffers
DMA-capable buffers
```

These are optimization paths.

The semantic API remains identical.

---

# 43. Zero-Copy Invariant

Zero-copy MUST NOT change ownership semantics.

If an operation needs a buffer beyond its original lifetime, ownership must be transferred explicitly.

---

# 44. Backpressure

Network streams expose:

```text
writable
readable
pending_bytes
buffered_bytes
```

High-level streaming APIs must stop producing data when downstream capacity is exhausted.

---

# 45. Write Queue

Each connection may have a bounded write queue.

Example:

```text
max_pending_write_bytes = 1 MiB
```

When the limit is reached:

```text
await write(...)
```

waits rather than allocating indefinitely.

---

# 46. Read Backpressure

A connection must not continuously read from the OS if the application cannot consume data.

The runtime may temporarily disable read interest.

---

# 47. Flow Control

Flow control exists at multiple layers:

```text
OS socket buffers
    ↓
Axiom network buffer
    ↓
protocol buffer
    ↓
application stream
```

Each layer has explicit limits.

---

# 48. Connection Pool

Axiom defines:

```text
ConnectionPool
```

A pool is explicitly owned by an application/service.

It is not a global singleton.

---

# 49. Pool Key

A connection pool key contains at least:

```text
scheme
host
port
proxy identity
TLS policy identity
network policy identity
```

Different security policies must not accidentally reuse the same connection.

---

# 50. Pool Limits

Pools support:

```text
max_connections
max_idle_connections
max_connections_per_host
idle_timeout
connection_lifetime
```

All values are bounded.

---

# 51. Pool Ownership

A pool owns idle connections.

An active connection belongs to its borrower until returned or closed.

---

# 52. Pool Shutdown

Shutdown:

```text
stop accepting new acquisitions
wait for active users
close idle connections
close remaining connections according to shutdown policy
```

This integrates with BOOTSTRAP-605 service draining.

---

# 53. DNS Architecture

DNS is provided through:

```text
Resolver
```

with:

```text
resolve_name()
resolve_service()
reverse_lookup()
```

---

# 54. Resolver Modes

Supported modes:

```text
SystemResolver
ConfiguredResolver
LiteralOnly
CustomResolver
```

`LiteralOnly` performs no DNS queries.

---

# 55. DNS Result

A DNS answer contains:

```text
DnsRecord {
    address
    ttl
    source
}
```

The result may contain IPv4 and IPv6 addresses.

---

# 56. DNS Cache

Resolver caching supports:

```text
positive cache
negative cache
TTL expiration
```

Cache entries are bounded.

No entry may survive beyond its configured maximum lifetime.

---

# 57. DNS Negative Cache

NXDOMAIN and equivalent negative results may be cached.

Negative caching is independently configurable.

---

# 58. DNS Cache Isolation

Resolver caches belong to a resolver instance.

There is no mandatory process-global DNS cache.

This prevents unrelated services from sharing mutable network state.

---

# 59. DNS Security

DNS resolution requires the appropriate network capability unless:

```text
literal-only mode
```

is used.

Resolver configuration may restrict:

```text
allowed servers
allowed domains
blocked domains
```

---

# 60. Service Records

Optional support:

```text
SRV
TXT
```

belongs to the resolver layer.

Application protocol code should not need to parse DNS packets itself.

---

# 61. Happy Eyeballs

Dual-stack connection establishment supports a Happy-Eyeballs-style strategy.

Conceptually:

```text
resolve
 ↓
IPv6 candidates
IPv4 candidates
 ↓
staggered connection attempts
 ↓
first successful connection
 ↓
cancel remaining attempts
```

Timing is configurable.

---

# 62. Connection Attempt Limits

The algorithm must be bounded by:

```text
max_parallel_attempts
deadline
cancellation
resource budget
```

It must not create unlimited sockets.

---

# 63. DNS + Connection Pipeline

High-level connect:

```text
resolve(host)
   ↓
rank addresses
   ↓
attempt candidates
   ↓
successful TCP connection
```

Each stage has independent diagnostics.

---

# 64. TLS Boundary

Axiom's core networking layer does not require a built-in TLS implementation.

Instead:

```text
TlsTransport
```

is a secure transport interface.

Architecture:

```text
TCP
 ↓
TlsTransport
 ↓
Application protocol
```

---

# 65. TLS Provider

A provider implements:

```text
TlsProvider
```

Examples may later include:

```text
Axiom-native TLS
platform TLS
external TLS provider
```

The core API does not depend on a particular implementation.

---

# 66. TLS Session

Conceptually:

```text
TlsSession {
    transport
    server_name
    alpn
    state
}
```

States:

```text
Created
Handshaking
Established
Closing
Closed
Failed
```

---

# 67. TLS Handshake

Handshake is asynchronous:

```text
await tls.handshake()
```

It must integrate with BOOTSTRAP-607 rather than blocking an executor worker.

---

# 68. TLS Trust

The API separates:

```text
certificate chain
trust anchors
verification policy
hostname verification
```

The runtime must not silently disable verification.

---

# 69. Hostname Verification

For client TLS:

```text
verify_hostname(host)
```

is enabled by default for standard secure profiles.

Disabling verification requires explicit policy/capability configuration.

---

# 70. SNI

Client TLS supports:

```text
server_name_indication
```

The requested hostname must be explicitly represented in the TLS session configuration.

---

# 71. ALPN

The secure transport layer supports:

```text
ALPN
```

for protocol negotiation.

Example:

```text
["h2", "http/1.1"]
```

---

# 72. Certificate Information

Applications may inspect certificate metadata:

```text
subject
issuer
valid_from
valid_to
serial
public_key_info
extensions
```

Private key material must remain opaque.

---

# 73. TLS Error Model

TLS errors are categorized:

```text
HandshakeFailed
CertificateInvalid
HostnameMismatch
UntrustedRoot
ExpiredCertificate
ProtocolVersion
CipherMismatch
Alert
TransportFailure
```

The provider may expose platform-specific details through an opaque diagnostic code.

---

# 74. TLS Key Material

Application code must not receive raw private key material through ordinary APIs unless an explicitly privileged cryptographic API is used.

This integrates with:

```text
Secret<T>
```

from BOOTSTRAP-601.

---

# 75. TLS Session Resumption

The boundary permits:

```text
session resumption
ticket caching
session cache
```

but the implementation owns the details.

Session caches are bounded and policy-controlled.

---

# 76. Proxy Architecture

Proxying is represented as a transport layer:

```text
Application
 ↓
HTTP/TLS
 ↓
ProxyTransport
 ↓
TCP
```

Supported abstraction:

```text
Direct
HttpConnect
Socks5
PlatformProxy
```

---

# 77. HTTP CONNECT

For TLS through an HTTP proxy:

```text
TCP
 ↓
HTTP CONNECT
 ↓
TLS
 ↓
HTTP
```

The proxy tunnel is established before TLS.

---

# 78. Proxy Security

Proxy credentials are secrets.

They must use:

```text
Secret<T>
```

and must never appear in:

- logs
- tracing
- crash reports
- metrics
- error strings

---

# 79. HTTP Transport Foundation

Axiom defines a transport-level HTTP API.

It does not attempt to become a web framework.

Core abstractions:

```text
HttpClient
HttpRequest
HttpResponse
HttpHeaders
HttpBody
```

---

# 80. HTTP Request

Conceptually:

```text
HttpRequest {
    method
    uri
    headers
    body
}
```

---

# 81. HTTP Response

```text
HttpResponse {
    version
    status
    headers
    body
}
```

---

# 82. HTTP Body

Body must support streaming.

```text
HttpBody:
    Empty
    Bytes
    Stream
```

A streaming body may be consumed incrementally.

---

# 83. HTTP/1.1

Core HTTP transport supports:

- request line
- status line
- headers
- Content-Length
- Transfer-Encoding
- chunked transfer
- persistent connections
- connection close
- request/response streaming

---

# 84. HTTP Header Representation

Headers are represented without requiring one heap allocation per header.

Implementation may use:

```text
small-vector
arena
inline storage
```

for common header counts.

---

# 85. Header Limits

HTTP parsing must enforce:

```text
max_header_count
max_header_name_length
max_header_value_length
max_header_bytes
```

This prevents memory exhaustion attacks.

---

# 86. HTTP Request-Line Limits

The parser enforces a maximum request target size.

Oversized input produces:

```text
HttpError.RequestTooLarge
```

rather than unbounded allocation.

---

# 87. Chunked Transfer

Chunked bodies are streamed.

The parser must not concatenate the entire body merely because chunked encoding is used.

---

# 88. Content-Length Validation

If Content-Length is present, the runtime tracks the expected byte count.

Premature EOF produces a protocol error.

Excess bytes are not silently attributed to the current response.

---

# 89. HTTP Keep-Alive

Persistent connections are integrated with `ConnectionPool`.

The transport may reuse an established connection only when protocol and security conditions permit.

---

# 90. HTTP Connection Reuse

Reuse requires compatible:

```text
authority
TLS policy
proxy route
protocol
connection state
```

---

# 91. HTTP/2 Boundary

HTTP/2 support is defined as a separate protocol module over:

```text
TlsTransport
```

using:

```text
ALPN = h2
```

The HTTP core must not require HTTP/2.

---

# 92. HTTP/3 Boundary

HTTP/3 is intentionally outside the TCP transport.

Architecture:

```text
HTTP/3
 ↓
QUIC
 ↓
UDP
```

A future QUIC module may implement this.

The current networking layer provides the UDP foundation.

---

# 93. WebSocket

WebSocket is a protocol module over HTTP transport.

Architecture:

```text
TCP
 ↓
TLS optional
 ↓
HTTP Upgrade
 ↓
WebSocket
```

---

# 94. WebSocket API

Conceptual:

```text
WebSocket.connect(uri)
WebSocket.send_text(text)
WebSocket.send_binary(data)
WebSocket.receive()
WebSocket.close()
```

---

# 95. WebSocket Frames

Frames are streamed and bounded.

Types:

```text
Text
Binary
Ping
Pong
Close
```

Control frame sizes are limited.

---

# 96. WebSocket Backpressure

Send queues are bounded.

Receive processing may pause when application consumption falls behind.

---

# 97. WebSocket Fragmentation

Fragmented messages are reassembled only up to a configured maximum.

Applications requiring huge messages should use streaming protocols instead.

---

# 98. WebSocket Masking

Client/server masking rules are enforced by the protocol implementation.

Invalid frames produce protocol errors.

---

# 99. Network Resource Accounting

All network resources integrate with BOOTSTRAP-606.

Tracked resources include:

```text
socket_count
active_connections
pending_connections
dns_queries
buffer_bytes
buffer_count
queued_write_bytes
queued_read_bytes
connection_pool_entries
bandwidth
I/O operations
```

---

# 100. Resource Admission

Before creating a socket:

```text
Security capability
        +
Resource budget
        ↓
admission
```

Failure:

```text
ResourceLimitExceeded
```

rather than uncontrolled allocation.

---

# 101. Bandwidth Accounting

The governor may account:

```text
bytes_sent
bytes_received
```

at:

```text
socket
connection
service
process
application
deployment
```

levels.

---

# 102. Security Capability

Network capability conceptually:

```text
NetworkCapability
```

contains permissions such as:

```text
Connect
Listen
Bind
Resolve
Multicast
Broadcast
InspectInterface
```

---

# 103. Destination Restrictions

A capability may restrict destinations:

```text
allow:
    example.com:443
```

or:

```text
allow:
    10.0.0.0/8
```

or:

```text
deny:
    loopback
```

---

# 104. DNS-to-IP Security

When a hostname is resolved, the security policy may evaluate:

```text
hostname
resolved address
port
```

rather than trusting the hostname alone.

This protects against policy mismatches involving DNS.

---

# 105. Local Network Restrictions

A deployment may explicitly prohibit:

```text
loopback
private networks
link-local
multicast
broadcast
```

These restrictions are policy decisions, not hard-coded global behavior.

---

# 106. Socket Capability Lifetime

Capabilities are opaque and revocable according to BOOTSTRAP-603.

A socket retains only the minimum authority required for its lifetime.

---

# 107. Interface Enumeration

Optional API:

```text
NetworkInterface.enumerate()
```

provides:

```text
name
index
addresses
flags
MTU
```

Sensitive platform information may require:

```text
InspectInterface
```

capability.

---

# 108. Routing Information

Route inspection is optional.

Core networking does not require applications to know the routing table.

If exposed:

```text
RouteTable
```

is read-only by default.

Route modification requires elevated platform capability.

---

# 109. Network Metrics

Metrics include:

```text
connections_opened
connections_closed
connect_latency
dns_latency
tls_handshake_latency
bytes_sent
bytes_received
read_operations
write_operations
timeouts
cancellations
resets
retransmission information when available
pool_hits
pool_misses
```

---

# 110. Diagnostics Integration

BOOTSTRAP-602 receives structured network events.

Example:

```text
network.connect.started
network.connect.completed
network.connect.failed
network.dns.started
network.dns.completed
network.tls.handshake
network.http.request
network.http.response
network.socket.closed
```

---

# 111. Trace Context

Network operations may automatically carry tracing context.

For HTTP:

```text
trace/span metadata
```

may be propagated according to configured protocol rules.

Sensitive headers must be redacted.

---

# 112. Error Model

Networking errors are structured.

Base:

```text
NetworkError
```

categories:

```text
InvalidAddress
PermissionDenied
ResourceLimit
Timeout
Cancelled
DnsFailure
ConnectionRefused
ConnectionReset
ConnectionClosed
HostUnreachable
NetworkUnreachable
AddressInUse
AddressNotAvailable
ProtocolError
TlsError
HttpError
ProxyError
PlatformError
```

---

# 113. Platform Error Preservation

The runtime preserves an opaque platform error code:

```text
PlatformNetworkCode
```

so diagnostics can expose:

```text
Axiom error
+
OS error
```

without making application code depend on OS-specific APIs.

---

# 114. Error Context

Errors may include:

```text
operation
local endpoint
remote endpoint
protocol
OS code
trace id
timestamp
```

Secrets are excluded.

---

# 115. WASM Boundary

WASM cannot assume raw socket access.

Axiom networking therefore defines:

```text
HostNetworkBackend
```

The host decides which network capabilities exist.

---

# 116. WASM Security

A WASM module with no network capability must observe:

```text
NetworkUnavailable
```

rather than attempting direct OS access.

---

# 117. Mobile Networking

Android/iOS backends account for:

- application lifecycle
- background restrictions
- platform network permissions
- connection suspension
- connectivity changes

The generic Axiom API remains stable.

---

# 118. Connectivity Changes

The runtime may publish:

```text
NetworkStatusChanged
```

with states such as:

```text
Unavailable
Local
Internet
Constrained
```

This is informational.

Applications must still handle individual connection failures.

---

# 119. Mobile Background Behavior

Axiom must never imply that an application can keep arbitrary sockets alive indefinitely in the background.

The platform backend reports suspension or termination.

---

# 120. Windows Backend

Windows implementation uses:

```text
Winsock
IOCP
WSARecv
WSASend
AcceptEx
ConnectEx
```

where available and appropriate.

The abstraction never exposes Winsock types to safe Axiom code.

---

# 121. Linux Backend

Linux implementation supports:

```text
sockets
epoll
```

with optional:

```text
io_uring
```

selected by runtime/platform profile.

---

# 122. macOS Backend

Uses:

```text
BSD sockets
kqueue
```

with platform-native mechanisms.

---

# 123. Android Backend

Uses the platform's native socket interfaces and integrates with application lifecycle.

The runtime does not require a Java/Kotlin networking library for its core native networking path.

---

# 124. iOS Backend

Uses native BSD socket facilities subject to platform policy and lifecycle.

The abstraction must allow the host application to integrate platform-specific networking services.

---

# 125. Embedded Backend

Embedded systems implement:

```text
NetworkBackend
```

against the available network stack.

The API may support a reduced feature profile.

---

# 126. Deterministic Network Backend

Tests can replace the real network backend with:

```text
FakeNetworkBackend
```

It supports:

```text
virtual sockets
virtual addresses
deterministic packet delivery
deterministic DNS
```

---

# 127. Network Simulation

The test backend can inject:

```text
latency
packet loss
packet duplication
packet reordering
connection reset
partial reads
partial writes
DNS failure
TLS failure
timeout
```

without affecting production code.

---

# 128. Deterministic Clock

Networking tests use the deterministic scheduler/clock from BOOTSTRAP-607.

Therefore a test can reproduce:

```text
connect
timeout
cancel
retry
```

without wall-clock waiting.

---

# 129. Fault Injection

Fault injection API:

```text
NetworkFaultProfile
```

may specify:

```text
fail_connect_after(n)
drop_next_packet()
delay_next_read()
truncate_write()
force_dns_error()
force_tls_error()
```

Only test builds may expose arbitrary fault injection.

---

# 130. Protocol Fuzzing

HTTP, WebSocket and DNS parsers must support fuzz testing.

Targets include:

- malformed headers
- oversized fields
- invalid lengths
- invalid UTF-8 where applicable
- invalid frame structure
- truncated packets
- duplicate fields
- integer overflow cases

---

# 131. Memory Safety

Network parsers must be memory-safe.

No input-controlled value may directly become an unchecked allocation size.

All lengths are checked before:

```text
allocation
copy
pointer arithmetic
buffer slicing
```

---

# 132. Integer Safety

Protocol arithmetic uses checked operations.

For example:

```text
offset + length
```

must detect overflow before accessing a buffer.

---

# 133. Parser Architecture

Protocol parsers should use incremental state machines:

```text
NeedInput
Parsing
NeedOutput
Complete
Error
```

They must not require the complete message in memory.

---

# 134. HTTP Parser Example

```text
RequestLine
    ↓
Headers
    ↓
Body
    ↓
Complete
```

The parser can pause after any state.

---

# 135. Network Stream Abstraction

Common stream interface:

```text
NetworkStream
```

supports:

```text
read
write
flush
shutdown
close
```

TCP and TLS can implement compatible stream semantics.

---

# 136. Datagram Abstraction

Separate interface:

```text
DatagramSocket
```

supports:

```text
send_to
receive_from
```

It must not pretend datagrams are streams.

---

# 137. Transport Composition

Transports are composable:

```text
TcpStream
   ↓
TlsStream
   ↓
HttpStream
```

or:

```text
TcpStream
   ↓
ProxyTunnel
   ↓
TlsStream
   ↓
HttpStream
```

---

# 138. No Hidden Global Networking

Axiom MUST NOT require:

```text
global socket registry
global connection pool
global DNS cache
global HTTP client
```

Application/service instances own these resources.

---

# 139. Service Integration

BOOTSTRAP-605 may supervise a network service.

Startup:

```text
create capability
↓
create listener
↓
bind
↓
listen
↓
publish endpoint
↓
mark Ready
```

The service must not report readiness before the listener is actually usable.

---

# 140. Graceful Shutdown

During service shutdown:

```text
stop accepting
↓
signal active connections
↓
drain
↓
deadline
↓
force close
```

This integrates with BOOTSTRAP-605 drain semantics.

---

# 141. IPC Separation

Local sockets may overlap technically with BOOTSTRAP-604.

The conceptual boundary is:

```text
IPC layer
    = local application-to-application communication semantics

Networking layer
    = transport/socket semantics
```

IPC may internally use local sockets.

---

# 142. State Integration

BOOTSTRAP-600 must not serialize live:

```text
Socket
TcpStream
TlsSession
ConnectionPool
```

Instead state stores:

```text
remote endpoint
protocol
application session identifier
reconnect policy
resume token
```

where applicable.

---

# 143. Checkpoint Recovery

After process restoration:

```text
checkpoint
 ↓
application restart
 ↓
recreate capability
 ↓
DNS
 ↓
connect
 ↓
TLS
 ↓
application-level resume
```

Network transport itself is recreated.

---

# 144. Configuration Integration

BOOTSTRAP-601 may configure:

```text
DNS servers
DNS cache size
connection timeout
read timeout
write timeout
buffer limits
pool limits
proxy
TLS policy
HTTP limits
IPv4/IPv6 strategy
```

Configuration is immutable per runtime snapshot.

---

# 145. Configuration Reload

A new networking configuration does not mutate existing sockets unpredictably.

Instead:

```text
new configuration
 ↓
new connections use new policy
 ↓
existing connections continue
```

unless explicit policy requires draining them.

---

# 146. Supervisor Integration

BOOTSTRAP-605 may use network health checks:

```text
TCP connect
HTTP request
```

Health checks must have:

- timeout
- resource limit
- cancellation
- capability restriction

---

# 147. Resource Governor Integration

Network resources are charged to the owning:

```text
Task
Connection
Service
Process
Application
```

according to configured resource hierarchy.

---

# 148. Scheduler Integration

Network I/O must not occupy a worker while waiting for OS readiness.

Correct:

```text
submit I/O
 ↓
worker released
 ↓
OS event
 ↓
executor schedules continuation
```

---

# 149. Blocking APIs

Blocking network APIs may exist for:

```text
embedded
simple tools
FFI
bootstrap code
```

but they are explicitly marked:

```text
blocking
```

and should not be used on async executor workers.

---

# 150. Blocking Isolation

If blocking networking is unavoidable:

```text
BlockingPool
```

from BOOTSTRAP-607 is used.

The Resource Governor limits its worker count.

---

# 151. Thread Safety

Network objects document concurrency guarantees.

Examples:

```text
TcpStream:
    Send
    not Sync by default
```

unless the implementation explicitly supports concurrent operations.

`ConnectionPool` is:

```text
Send + Sync
```

if implemented accordingly.

---

# 152. Async Safety

Multiple simultaneous reads on a single TCP stream are not automatically allowed.

The runtime should reject unsupported concurrent operations rather than silently interleave buffers.

---

# 153. Concurrent Writes

Concurrent writes may either:

1. be serialized by a stream writer
2. be rejected
3. use an explicit concurrent-write abstraction

The base stream must preserve byte ordering.

---

# 154. Lock Avoidance

Hot network paths should use:

- per-connection state
- atomics
- intrusive queues
- bounded ring buffers
- executor-local structures

instead of a global network lock.

---

# 155. Memory Allocation Target

Simple TCP operations should not require repeated heap allocation.

Small requests should use inline/pool buffers.

---

# 156. Binary Size

Unused networking modules must be dead-strippable.

For example:

An application using only UDP should not automatically link:

```text
HTTP
WebSocket
TLS
DNS
proxy
```

unless required.

---

# 157. Compiler Metadata

Networking APIs expose compile-time metadata:

```text
@requires(network.connect)
@requires(network.resolve)
@requires(network.listen)
```

The compiler can propagate this into the executable capability manifest.

---

# 158. Linker Metadata

The linker records:

```text
network features used
required platform backends
required capabilities
protocol modules
```

Unused modules are removed.

---

# 159. IR Representation

Compiler IR may represent:

```text
net.socket.create
net.socket.bind
net.socket.connect
net.socket.accept
net.socket.read
net.socket.write
net.socket.close
net.dns.resolve
```

These are lowered to runtime or platform calls.

---

# 160. Security Verification

Before final linking:

```text
IR network operations
 ↓
required capabilities
 ↓
deployment policy
 ↓
manifest validation
```

A binary requesting unauthorized network authority must fail deployment validation.

---

# 161. FFI

Axiom FFI may expose C-compatible wrappers:

```text
axiom_tcp_connect(...)
axiom_tcp_read(...)
axiom_tcp_write(...)
```

but these are ABI boundary functions.

Safe Axiom applications should prefer typed native APIs.

---

# 162. ABI Stability

Opaque handles are ABI-stable:

```text
SocketHandle
ResolverHandle
ConnectionHandle
```

Internal structure layout is not part of the public ABI.

---

# 163. Platform ABI

No application-level ABI may depend on:

```text
SOCKET
sockaddr_in
sockaddr_in6
struct epoll_event
OVERLAPPED
```

unless explicitly using unsafe/platform FFI.

---

# 164. Network Capability Manifest

Compiled binaries may contain:

```text
network:
    resolve
    connect
    listen
    multicast
```

plus restrictions where statically knowable.

---

# 165. Runtime Capability Checks

Dynamic destinations may require runtime checks.

Example:

```text
connect(user_supplied_host)
```

cannot be statically reduced to a single destination.

---

# 166. DNS Rebinding Protection

If security policy authorizes a destination by hostname, the runtime may bind the authorization decision to the resolved address according to policy.

Policies can choose:

```text
hostname-only
hostname+resolved-address
fixed-IP
```

The secure default should avoid silently treating changing DNS results as permanently trusted.

---

# 167. Private Address Policy

The security layer may detect:

```text
127.0.0.0/8
::1
RFC1918
link-local
ULA
```

and apply deployment restrictions.

Classification itself is deterministic.

---

# 168. Retry Policy

Networking provides primitives but does not automatically retry arbitrary application requests.

Retry belongs to the higher protocol/application layer.

Safe transport retries are limited to connection establishment where semantics permit.

---

# 169. Retry and HTTP

The HTTP transport must not blindly retry non-idempotent requests.

Retry policy belongs to:

```text
HttpClientPolicy
```

and must inspect method/request semantics and application configuration.

---

# 170. Connection Reconnect

A disconnected TCP stream cannot transparently become a different TCP connection without changing semantics.

Therefore:

```text
reconnect()
```

creates a new stream.

The application decides whether protocol state can be resumed.

---

# 171. TLS Reconnect

A new TCP connection requires a new TLS session/handshake unless session resumption is used internally.

---

# 172. HTTP Retry

HTTP retry is separate from TCP reconnect.

The runtime must not imply:

```text
connection retry = request retry
```

---

# 173. HTTP Streaming

Request and response bodies support:

```text
read_chunk()
write_chunk()
```

without buffering the complete content.

This is required for:

- large downloads
- uploads
- media streams
- long-running responses

---

# 174. HTTP Cancellation

Cancelling a body stream must release or close the underlying connection according to protocol state.

Reusable connections must only return to the pool when their framing state is known to be clean.

---

# 175. Connection Pool Safety

A connection with unread protocol bytes must never be returned to the idle pool.

---

# 176. HTTP Parser Security

The parser must explicitly handle:

- conflicting Content-Length
- invalid Transfer-Encoding
- malformed chunk sizes
- invalid header syntax
- oversized headers
- premature EOF

Ambiguous framing must fail closed.

---

# 177. WebSocket Security

WebSocket handshake validates:

```text
HTTP upgrade
connection headers
version
accept key
origin policy where configured
```

---

# 178. TLS + WebSocket

Secure WebSocket:

```text
wss://
```

maps to:

```text
TCP
 ↓
TLS
 ↓
HTTP Upgrade
 ↓
WebSocket
```

---

# 179. DNS + Proxy

Proxy mode may resolve the hostname:

```text
locally
```

or:

```text
through proxy
```

according to proxy policy.

The distinction must be explicit because it affects privacy and destination security.

---

# 180. Interface Changes

Network status may change while connections exist.

Existing sockets are not automatically migrated to another interface.

Applications receive connectivity events and handle failures.

---

# 181. MTU

The transport layer may expose interface MTU for diagnostics.

Application protocols generally should not depend on MTU.

---

# 182. Socket Statistics

Optional:

```text
SocketStats {
    bytes_sent
    bytes_received
    packets_sent
    packets_received
    errors
    timestamps
}
```

Availability is platform dependent.

---

# 183. Network Tracing

Trace spans may include:

```text
dns
connect
tls
http
read
write
```

Remote IPs may be redacted according to privacy policy.

---

# 184. Privacy

Diagnostics MUST NOT automatically capture:

- passwords
- authorization tokens
- cookies
- private keys
- TLS secrets
- request bodies
- arbitrary response bodies

unless explicit diagnostic policy permits it.

---

# 185. Logging

Default logging records metadata, not payloads.

Example:

```text
HTTP GET example.com:443
status=200
latency=37ms
bytes=8123
```

rather than the complete body.

---

# 186. Crash Diagnostics

BOOTSTRAP-602 may record:

```text
active socket count
connection states
remote endpoint metadata
DNS state
TLS state category
HTTP request state
```

but never secret payloads.

---

# 187. Security Audit Events

BOOTSTRAP-603 may emit:

```text
network.capability.denied
network.destination.denied
network.listen.denied
network.resolve.denied
network.proxy.denied
```

---

# 188. Resource Events

BOOTSTRAP-606 may emit:

```text
network.socket.limit
network.buffer.limit
network.connection.limit
network.bandwidth.limit
```

---

# 189. Supervisor Health

A service health check can expose:

```text
listener_ready
active_connections
connection_errors
recent_dns_failures
recent_tls_failures
```

---

# 190. Application-Level Health

The networking layer does not claim that:

```text
TCP connection = application healthy
```

An HTTP service may accept TCP while being unable to process requests.

Health semantics remain above transport.

---

# 191. Network Service API

Struct-only Axiom style:

```text
struct TcpListener {
    socket: Socket
}

fn TcpListener.bind(
    address: SocketAddress,
    options: ListenOptions
) -> Result<TcpListener, NetworkError>
```

The first parameter is the receiver for methods.

---

# 192. TCP Stream API

```text
struct TcpStream {
    socket: Socket
}

async fn TcpStream.connect(
    address: SocketAddress,
    options: ConnectOptions
) -> Result<TcpStream, NetworkError>

async fn TcpStream.read(
    self,
    buffer: Buffer
) -> Result<usize, NetworkError>

async fn TcpStream.write(
    self,
    buffer: Buffer
) -> Result<usize, NetworkError>
```

---

# 193. Resolver API

```text
struct Resolver {
    cache: DnsCache
}

async fn Resolver.resolve(
    self,
    host: HostName,
    options: ResolveOptions
) -> Result<DnsResult, DnsError>
```

---

# 194. HTTP API

```text
struct HttpClient {
    transport: Transport
    pool: ConnectionPool
}

async fn HttpClient.send(
    self,
    request: HttpRequest
) -> Result<HttpResponse, HttpError>
```

---

# 195. Connection Pool API

```text
struct ConnectionPool {
    state: PoolState
}

async fn ConnectionPool.acquire(
    self,
    key: ConnectionKey
) -> Result<Connection, PoolError>

fn ConnectionPool.release(
    self,
    connection: Connection
)
```

---

# 196. TLS API

```text
struct TlsClient {
    provider: TlsProvider
}

async fn TlsClient.connect(
    self,
    stream: TcpStream,
    config: TlsConfig
) -> Result<TlsStream, TlsError>
```

---

# 197. Transport Trait

Conceptually:

```text
trait ByteStream {
    async fn read(...)
    async fn write(...)
    async fn shutdown(...)
}
```

Implementations:

```text
TcpStream
TlsStream
ProxyStream
```

---

# 198. Datagram Trait

```text
trait Datagram {
    async fn send_to(...)
    async fn receive_from(...)
}
```

Implemented by:

```text
UdpSocket
```

---

# 199. HTTP Body Trait

```text
trait BodyStream {
    async fn next_chunk()
}
```

This permits:

```text
file → HTTP upload
HTTP response → file
HTTP response → decompressor
```

without whole-body buffering.

---

# 200. Streaming Pipeline

Example:

```text
File
 ↓
BodyStream
 ↓
HTTP
 ↓
TLS
 ↓
TCP
 ↓
OS
```

No intermediate full-size copy is required.

---

# 201. File-to-Network Optimization

Where platform APIs permit, the runtime may use:

```text
sendfile
TransmitFile
splice
```

to avoid unnecessary user-space copying.

---

# 202. Network-to-File Optimization

Likewise, downloads may use:

```text
receive buffer
 ↓
file sink
```

with pooled buffers.

---

# 203. Compression Boundary

HTTP compression/decompression is not part of the raw networking layer.

A separate body transformation can implement:

```text
gzip
deflate
br
zstd
```

where supported.

---

# 204. Protocol Composition

The architecture encourages:

```text
Transport
 ↓
SecureTransport
 ↓
Protocol
 ↓
Codec
 ↓
Application
```

rather than a monolithic HTTP/network runtime.

---

# 205. Core vs Optional Modules

Core:

```text
IP
TCP
UDP
Local sockets
DNS abstraction
Async I/O
buffers
```

Optional:

```text
TLS implementation
HTTP
WebSocket
HTTP/2
HTTP/3
QUIC
proxy protocols
compression
```

---

# 206. TLS Implementation Boundary

The core toolchain may ship a platform/provider implementation in a separate runtime module.

The compiler must not force all applications to link it.

---

# 207. No Third-Party Dependency Requirement

The Axiom core specification does not require third-party networking libraries.

Platform APIs are accessed directly through Axiom's native backend layer.

External providers remain possible through FFI/provider interfaces.

---

# 208. Backend Selection

At build/link time:

```text
target OS
 +
target architecture
 +
enabled networking features
 ↓
backend selection
```

---

# 209. Static Linking

For static native applications:

```text
only required network modules
```

are linked.

---

# 210. Dynamic Linking

Dynamic applications may place networking runtime modules into shared libraries.

ABI-compatible opaque handles remain stable.

---

# 211. Error ABI

Errors crossing ABI boundaries use:

```text
error code
opaque diagnostic payload
```

rather than exposing internal Rust/C++/OS structures.

---

# 212. Build Reproducibility

Network runtime manifests record:

```text
backend
features
protocol modules
ABI version
security profile
```

This contributes to the build identity.

---

# 213. Cache Compatibility

Compiler caching may reuse networking-generated artifacts when:

```text
source unchanged
compiler version unchanged
network ABI unchanged
target unchanged
security metadata unchanged
```

---

# 214. Deterministic Manifest

Network capability metadata must have deterministic serialization.

This permits:

```text
build reproducibility
AI inspection
security auditing
cache validation
```

---

# 215. AI Metadata

Compiled networking metadata may describe:

```text
uses TCP
uses DNS
requires network.connect
uses TLS
uses HTTP/1.1
max configured connection count
```

This is machine-readable.

---

# 216. Static Capability Analysis

The compiler can identify obvious operations:

```text
TcpStream.connect
```

and infer:

```text
network.connect
```

Dynamic plugin behavior may require runtime declaration.

---

# 217. Dynamic Modules

Plugins cannot silently obtain unrestricted networking.

They receive explicit:

```text
NetworkCapability
```

from their host.

---

# 218. Plugin Isolation

A plugin may receive:

```text
connect only to api.example.com:443
```

without receiving:

```text
listen
broadcast
interface inspection
```

---

# 219. Capability Delegation

A parent component may attenuate a network capability:

```text
FullNetworkCapability
        ↓
ConnectCapability
        ↓
ConnectToHostCapability
        ↓
ConnectToHostPortCapability
```

Authority only decreases.

---

# 220. Network Namespace

Logical network policy can identify:

```text
application
service
plugin
tenant
```

without requiring OS-level network namespaces.

---

# 221. Rate Limiting

Network rate limits belong to Resource Governor policy.

Possible limits:

```text
connections/sec
DNS queries/sec
bytes/sec
requests/sec
```

---

# 222. Admission Under Pressure

When network resources are exhausted:

```text
new operation
 ↓
ResourceGovernor.admit()
 ↓
allow / delay / reject
```

Existing established connections may continue unless policy explicitly says otherwise.

---

# 223. Fairness

Per-service/per-tenant network budgets prevent one workload from consuming all connection or buffer resources.

---

# 224. Connection Flood Protection

Listeners may enforce:

```text
max_pending_accepts
max_connections
connection_rate
per-source limits
```

These are resource/security policies.

---

# 225. Accept Loop

Conceptually:

```text
while listener.active:
    connection = await listener.accept()
    if admission_allowed:
        spawn(connection_handler)
    else:
        close(connection)
```

---

# 226. Accept Backpressure

If the application cannot process additional connections, the runtime must avoid unlimited task creation.

Integration with BOOTSTRAP-606 controls:

```text
connection count
task count
memory
```

---

# 227. Listener Lifecycle

Listener shutdown:

```text
stop accepting
close listening socket
existing connections continue
```

unless service policy specifies otherwise.

---

# 228. TCP Fast Open

Platform-specific TCP features may be exposed through optional extensions.

They must never become required for ordinary TCP correctness.

---

# 229. Keepalive vs Application Heartbeat

The runtime distinguishes:

```text
TCP keepalive
```

from:

```text
application heartbeat
```

TCP keepalive does not prove application responsiveness.

---

# 230. DNS vs Connectivity

Successful DNS resolution does not imply network reachability.

Diagnostics preserve separate stages:

```text
DNS success
TCP failure
```

rather than collapsing them into one error.

---

# 231. TLS vs Connectivity

A successful TCP connection does not imply successful TLS.

Errors preserve:

```text
TCP established
TLS failed
```

---

# 232. HTTP vs TLS

A successful TLS handshake does not imply a successful HTTP request.

Each layer has separate lifecycle and metrics.

---

# 233. Protocol Stack Identity

A connection can expose:

```text
transport = TCP
security = TLS
protocol = HTTP/1.1
```

This is useful for diagnostics and pooling.

---

# 234. Network Operation Context

Every operation can carry:

```text
TraceId
SpanId
CancellationToken
Deadline
ResourceScope
Capability
```

---

# 235. No Hidden Retry

Core socket APIs never retry automatically.

This makes:

```text
latency
failure
resource usage
```

predictable.

---

# 236. DNS Retry

Resolver implementations may perform bounded retries against configured resolver servers, because DNS resolution itself has transport-level retry semantics.

The retry count is bounded.

---

# 237. Connect Retry

Multiple address attempts for IPv4/IPv6 are part of address selection rather than arbitrary application retries.

---

# 238. HTTP Retry Boundary

HTTP retries remain outside the socket layer.

This prevents duplicate side effects.

---

# 239. Network Cancellation Race

If:

```text
cancel()
```

and:

```text
I/O complete
```

occur concurrently, exactly one public result is produced.

The other event is internal cleanup.

---

# 240. Close Race

If one task closes a socket while another is waiting:

```text
waiter → ConnectionClosed
```

No waiter may access a recycled OS handle.

Generation checks guarantee safety.

---

# 241. Socket Destruction

Dropping the final owning socket handle closes the OS socket unless it has been explicitly transferred.

This is deterministic resource release.

---

# 242. Explicit Detach

An unsafe/platform API may explicitly detach the OS descriptor.

Safe code does not receive raw descriptor ownership.

---

# 243. Async Operation Ownership

An outstanding I/O operation owns the necessary backend state until completion/cancellation cleanup.

Closing the high-level object does not free memory still referenced by the OS.

---

# 244. Shutdown Ordering

Correct shutdown order:

```text
Application
 ↓
HTTP/WebSocket
 ↓
TLS
 ↓
Proxy
 ↓
TCP/UDP
 ↓
Network backend
 ↓
Executor
```

The executor must remain alive until all network completion events have been drained or cancelled safely.

---

# 245. Runtime Shutdown

Network runtime enters:

```text
Running
Draining
Closed
```

During `Draining`:

- no new network operations
- existing operations finish/cancel
- listeners stop
- pools close

---

# 246. Supervisor Shutdown

BOOTSTRAP-605 owns the high-level timeout.

Network runtime reports:

```text
active_operations
active_connections
pending_tasks
```

for drain diagnostics.

---

# 247. Crash Recovery

A crashed service loses its sockets.

Supervisor restart creates new sockets.

No stale socket handle may survive process restart.

---

# 248. Security and Crash Recovery

Capabilities are reprovisioned from:

```text
deployment policy
service specification
```

not copied from the crashed process.

---

# 249. Network State Recovery

Application-level reconnect metadata can be persisted.

Example:

```text
remote_service
last_session_id
resume_supported
retry_policy
```

The transport itself remains ephemeral.

---

# 250. Network Configuration Fingerprint

The runtime records a fingerprint covering relevant network configuration.

Useful for diagnostics:

```text
config_fingerprint
security_policy_fingerprint
network_backend
```

---

# 251. Diagnostics Snapshot

A diagnostic snapshot may contain:

```text
listener list
connection counts
DNS cache statistics
pool statistics
buffer usage
network errors
```

but not sensitive payloads.

---

# 252. Pool Diagnostic Snapshot

Example:

```text
host=api.example.com
active=4
idle=2
pending=3
bytes_buffered=0
```

---

# 253. DNS Diagnostic Snapshot

Example:

```text
queries=120
cache_hits=94
cache_misses=26
negative_hits=2
```

---

# 254. Security Diagnostic Snapshot

Example:

```text
network_connect_allowed=47
network_connect_denied=3
dns_allowed=18
listen_denied=1
```

---

# 255. Performance Targets

The implementation should target:

```text
near-native socket throughput
near-native latency
O(1) handle validation
bounded memory per connection
low allocation rate
low scheduler overhead
```

---

# 256. Async Overhead Target

A simple socket read/write should not require:

```text
OS thread creation
global mutex
full message allocation
```

---

# 257. Buffer Efficiency Target

Steady-state streaming should reuse pooled buffers whenever practical.

---

# 258. Connection Pool Efficiency

Idle connection reuse should avoid:

```text
DNS lookup
TCP handshake
TLS handshake
```

when policy allows.

---

# 259. DNS Efficiency

Literal IP addresses should bypass DNS completely.

---

# 260. IPv6 Efficiency

Dual-stack connection establishment must avoid unnecessary sequential delays.

---

# 261. Hot Path

Hot path:

```text
application write
 ↓
stream queue
 ↓
OS async send
```

should use minimal synchronization.

---

# 262. Cold Path

Cold path includes:

```text
configuration
capability validation
DNS setup
TLS provider initialization
diagnostic metadata
```

These may use more complex structures because they are not per-byte hot paths.

---

# 263. Small Object Optimization

Implementations may use inline storage for:

```text
small addresses
small headers
small socket options
small error metadata
```

---

# 264. Arena Allocation

Protocol parsers may use bounded arenas whose lifetime matches:

```text
request
response
connection
```

The arena must have a hard maximum.

---

# 265. No Mandatory Garbage Collection

Networking must not require GC.

Object lifetime is governed by:

```text
ownership
scopes
handles
explicit async task lifetime
```

---

# 266. Reference Counting

Reference counting may be used internally where it improves implementation simplicity.

It is not exposed as a mandatory programming model.

Cycles must be avoided in runtime structures.

---

# 267. Pointer Exposure

Safe network APIs expose opaque handles and typed views rather than raw pointers.

Unsafe FFI may use pointers explicitly.

---

# 268. Memory Fragmentation

Long-lived connection pools should use:

- slab allocation
- pools
- arenas
- fixed-size structures

where appropriate.

---

# 269. Cache Locality

Per-connection state should be compact and separated from cold diagnostic/configuration data.

---

# 270. NUMA

Large server workloads may associate network workers with CPU/NUMA locality through BOOTSTRAP-607/606.

Ordinary applications need not configure NUMA manually.

---

# 271. Thread Affinity

Network completion handlers may execute on any compatible executor worker unless explicitly pinned.

---

# 272. Thread-Affine Backends

A platform backend that requires thread affinity can declare:

```text
ThreadAffine
```

and the scheduler preserves that constraint.

---

# 273. FFI Async Boundary

Foreign libraries that use callbacks can be wrapped into Axiom futures/promises.

Callback lifetime must be explicitly owned.

---

# 274. Callback Cancellation

Foreign callback-based networking must support:

```text
cancel
```

or the wrapper must document that cancellation only suppresses delivery while the underlying operation completes independently.

---

# 275. Foreign Runtime Isolation

A third-party networking provider must not introduce an implicit competing:

```text
thread pool
GC
event loop
global logger
```

without being declared by the integration.

---

# 276. Backend Contract

Every backend implements approximately:

```text
trait NetworkBackend {
    fn socket_create(...)
    fn bind(...)
    fn listen(...)
    fn connect(...)
    fn accept(...)
    fn recv(...)
    fn send(...)
    fn close(...)
}
```

Async completion is integrated through the scheduler.

---

# 277. Backend Capability Discovery

At initialization:

```text
backend.capabilities()
```

may report:

```text
IPv6
UDP
multicast
sendfile
io_uring
zero_copy
unix_sockets
```

---

# 278. Feature Negotiation

Application code should test capability where behavior is optional.

Example:

```text
if backend.supports(ZeroCopy) {
    ...
}
```

Correctness cannot depend on optional optimization features.

---

# 279. Portable Semantics

When OS semantics differ, Axiom chooses a common semantic subset.

Platform-specific extensions remain available separately.

---

# 280. Unsupported Operation

An unsupported operation produces:

```text
NotSupported
```

rather than silently emulating it with potentially different semantics.

---

# 281. Network Security Defaults

Default profile:

```text
default deny
explicit capability
bounded resources
TLS verification enabled
no secret logging
no unrestricted proxy credentials
```

---

# 282. Development Profile

Development mode may simplify configuration but must not silently disable security.

Any relaxed policy is explicitly visible in the build/runtime profile.

---

# 283. Production Profile

Production profile enables:

```text
strict capability enforcement
bounded resource limits
TLS verification
diagnostic redaction
connection limits
```

---

# 284. Testing Profile

Testing profile provides:

```text
fake backend
deterministic clock
fault injection
virtual DNS
virtual network
```

without weakening production code paths.

---

# 285. Security Tests

Mandatory tests include:

```text
unauthorized connect
unauthorized listen
unauthorized DNS
private-address restriction
capability attenuation
revocation
secret redaction
proxy credential protection
```

---

# 286. Socket Tests

Test:

```text
bind
listen
accept
connect
read
write
half-close
full-close
reuse
stale handle
```

---

# 287. Async Tests

Test:

```text
completion
cancellation
timeout
close during wait
completion/cancel race
multiple waiters
executor shutdown
```

---

# 288. DNS Tests

Test:

```text
IPv4
IPv6
multiple answers
TTL
negative cache
cache expiration
timeout
resolver failure
literal IP
```

---

# 289. HTTP Tests

Test:

```text
Content-Length
chunked
keepalive
partial reads
partial writes
header limits
malformed framing
EOF
connection reuse
cancellation
```

---

# 290. TLS Boundary Tests

The interface must test:

```text
handshake
verification failure
hostname mismatch
ALPN
SNI
certificate expiration
provider failure
cancellation
```

using deterministic/fake providers where possible.

---

# 291. WebSocket Tests

Test:

```text
upgrade
text
binary
ping
pong
close
fragmentation
masking
oversized frame
backpressure
```

---

# 292. Resource Tests

Test:

```text
socket quota
connection quota
buffer quota
bandwidth quota
DNS quota
task quota
```

---

# 293. Fault Tests

Inject:

```text
packet loss
delay
reset
partial write
partial read
DNS failure
TLS failure
resource exhaustion
```

and verify bounded recovery.

---

# 294. Race Tests

Run concurrent:

```text
read/write
close/read
cancel/read
cancel/connect
pool acquire/release
shutdown/accept
```

under stress.

---

# 295. Memory Tests

Verify:

```text
no buffer overflow
no stale handle
no double close
no use-after-close
no lifetime violation
```

---

# 296. Fuzz Targets

At minimum:

```text
IP parser
DNS parser
HTTP parser
WebSocket parser
header parser
chunk parser
URI parser
```

---

# 297. Model Testing

The fake backend should support state-model verification:

```text
socket state
connection state
pool state
shutdown state
```

against expected transition invariants.

---

# 298. Acceptance Criterion A01

IPv4 TCP client can connect asynchronously.

# 299. Acceptance Criterion A02

IPv6 TCP client can connect asynchronously.

# 300. Acceptance Criterion A03

TCP partial reads are correctly reported.

# 301. Acceptance Criterion A04

TCP partial writes are correctly reported.

# 302. Acceptance Criterion A05

TCP half-close is supported.

# 303. Acceptance Criterion A06

UDP send/receive works.

# 304. Acceptance Criterion A07

UDP preserves datagram boundaries.

# 305. Acceptance Criterion A08

Local sockets work on supported platforms.

# 306. Acceptance Criterion A09

Socket handles are generation-safe.

# 307. Acceptance Criterion A10

Async I/O integrates with BOOTSTRAP-607.

# 308. Acceptance Criterion A11

Cancellation is race-safe.

# 309. Acceptance Criterion A12

Timeouts use BOOTSTRAP-607 deadlines.

# 310. Acceptance Criterion A13

DNS supports IPv4 and IPv6.

# 311. Acceptance Criterion A14

DNS cache honors TTL.

# 312. Acceptance Criterion A15

Negative DNS results can be cached.

# 313. Acceptance Criterion A16

Literal IP addresses bypass DNS.

# 314. Acceptance Criterion A17

Dual-stack connection establishment is bounded.

# 315. Acceptance Criterion A18

Connection pools are application-owned.

# 316. Acceptance Criterion A19

Pool limits are enforced.

# 317. Acceptance Criterion A20

Network buffers are bounded.

# 318. Acceptance Criterion A21

Backpressure prevents unbounded writes.

# 319. Acceptance Criterion A22

Scatter/gather is supported where available.

# 320. Acceptance Criterion A23

Zero-copy optimization does not alter semantics.

# 321. Acceptance Criterion A24

Network resources integrate with BOOTSTRAP-606.

# 322. Acceptance Criterion A25

Network capabilities integrate with BOOTSTRAP-603.

# 323. Acceptance Criterion A26

Unauthorized connections are rejected.

# 324. Acceptance Criterion A27

Unauthorized listening is rejected.

# 325. Acceptance Criterion A28

DNS permission can be independently controlled.

# 326. Acceptance Criterion A29

TLS is isolated behind a provider boundary.

# 327. Acceptance Criterion A30

TLS hostname verification cannot be silently disabled.

# 328. Acceptance Criterion A31

SNI and ALPN are represented.

# 329. Acceptance Criterion A32

TLS handshakes are asynchronous.

# 330. Acceptance Criterion A33

HTTP/1.1 transport supports streaming.

# 331. Acceptance Criterion A34

HTTP header sizes are bounded.

# 332. Acceptance Criterion A35

HTTP framing ambiguities are rejected.

# 333. Acceptance Criterion A36

HTTP keepalive integrates with connection pooling.

# 334. Acceptance Criterion A37

WebSocket supports streaming frames.

# 335. Acceptance Criterion A38

WebSocket backpressure is bounded.

# 336. Acceptance Criterion A39

Proxy tunneling is supported through an explicit layer.

# 337. Acceptance Criterion A40

Proxy secrets are redacted.

# 338. Acceptance Criterion A41

WASM networking requires host capability.

# 339. Acceptance Criterion A42

Mobile lifecycle interruption is representable.

# 340. Acceptance Criterion A43

Network diagnostics integrate with BOOTSTRAP-602.

# 341. Acceptance Criterion A44

Network shutdown integrates with BOOTSTRAP-605.

# 342. Acceptance Criterion A45

Live sockets are not checkpointed by BOOTSTRAP-600.

# 343. Acceptance Criterion A46

Recovery can reconstruct network state from application metadata.

# 344. Acceptance Criterion A47

Fake networking backend exists.

# 345. Acceptance Criterion A48

Network tests use deterministic time.

# 346. Acceptance Criterion A49

Fault injection can simulate partial I/O.

# 347. Acceptance Criterion A50

HTTP/DNS/WebSocket parsers are fuzzable.

# 348. Acceptance Criterion A51

Stale socket handles cannot affect reused descriptors.

# 349. Acceptance Criterion A52

Concurrent close/read is race-safe.

# 350. Acceptance Criterion A53

No global network lock is required on the hot path.

# 351. Acceptance Criterion A54

Unused networking modules can be dead-stripped.

# 352. Acceptance Criterion A55

Compiler capability metadata is generated.

# 353. Acceptance Criterion A56

Linker network metadata is deterministic.

# 354. Acceptance Criterion A57

Platform backends can be selected without changing application source.

# 355. Acceptance Criterion A58

Unsupported platform operations return explicit errors.

# 356. Acceptance Criterion A59

Network errors preserve useful platform diagnostics.

# 357. Acceptance Criterion A60

No networking feature requires a garbage collector.

---

# 358. Final API Layering

The intended public layering is:

```text
axiom.net
├── address
│   ├── IpV4
│   ├── IpV6
│   ├── IpAddress
│   ├── SocketAddress
│   └── HostName
│
├── socket
│   ├── Socket
│   ├── TcpListener
│   ├── TcpStream
│   ├── UdpSocket
│   └── LocalStream
│
├── dns
│   ├── Resolver
│   ├── DnsResult
│   └── DnsCache
│
├── transport
│   ├── ByteStream
│   ├── Datagram
│   ├── ProxyStream
│   └── NetworkBuffer
│
├── tls
│   ├── TlsProvider
│   ├── TlsClient
│   └── TlsStream
│
├── http
│   ├── HttpClient
│   ├── HttpRequest
│   ├── HttpResponse
│   └── HttpBody
│
└── websocket
    └── WebSocket
```

---

# 359. Runtime Dependency Graph

```text
                    BOOTSTRAP-603
                   Security/Capability
                          │
                          ▼
BOOTSTRAP-601 ───────► Network Runtime ◄────── BOOTSTRAP-606
 Configuration             │                    Resources
                          │
              ┌───────────┼────────────┐
              ▼           ▼            ▼
             DNS         Socket       Buffer
              │           │            │
              └───────────┼────────────┘
                          ▼
                    BOOTSTRAP-607
                  Async Scheduler
                          │
                          ▼
                    BOOTSTRAP-608
                 Synchronization
                          │
          ┌───────────────┼────────────────┐
          ▼               ▼                ▼
         TLS             HTTP          WebSocket
          │
          ▼
     Application Protocol
```

---

# 360. Platform Architecture

```text
                    Axiom Network API
                           │
                    Network Runtime
                           │
                 AsyncNetworkBackend
                           │
       ┌───────────┬───────┼────────┬───────────┐
       │           │       │        │           │
    Windows      Linux   macOS   Mobile       WASM
       │           │       │        │           │
    Winsock      epoll  kqueue   native      Host API
     IOCP       io_uring sockets  sockets
```

---

# 361. Complete Data Flow

Typical HTTPS request:

```text
HttpClient
    ↓
ConnectionPool
    ↓
Proxy (optional)
    ↓
TLS
    ↓
TCP
    ↓
NetworkReactor
    ↓
Executor
    ↓
OS
    ↓
Network
```

Reverse direction:

```text
Network
    ↓
OS
    ↓
NetworkReactor
    ↓
Executor
    ↓
TCP
    ↓
TLS
    ↓
HTTP parser
    ↓
HttpBody
    ↓
Application
```

---

# 362. Security Data Flow

```text
Application
    ↓
requested network operation
    ↓
Capability check
    ↓
Resource admission
    ↓
Socket creation
    ↓
Network backend
```

No operation may bypass these gates in safe code.

---

# 363. Shutdown Data Flow

```text
Supervisor
    ↓
Service draining
    ↓
HTTP stop
    ↓
WebSocket stop
    ↓
TLS close
    ↓
TCP close
    ↓
Network reactor drain
    ↓
Executor shutdown
```

---

# 364. Recovery Data Flow

```text
Crash
 ↓
Diagnostics
 ↓
Supervisor
 ↓
new process generation
 ↓
configuration reload
 ↓
capability provisioning
 ↓
listener recreation
 ↓
DNS
 ↓
TCP
 ↓
TLS
 ↓
application protocol resume
```

---

# 365. Core Architectural Decision

Axiom networking intentionally chooses:

```text
native OS networking
+
uniform Axiom abstraction
+
async-first execution
+
explicit ownership
+
bounded resources
+
capability security
+
protocol layering
```

instead of:

```text
one giant networking framework
```

This keeps the runtime modular and allows applications to link only what they use.

---

# 366. Relationship to the Previous Layers

The architecture now forms a coherent runtime stack:

```text
600  State / Persistence / Recovery
601  Configuration / Secrets / Deployment
602  Logging / Diagnostics / Crash Reporting
603  Security / Capabilities / Permissions
604  IPC / Shared Memory / Message Transport
605  Process / Service Supervision / Watchdog
606  Resource Governor / Budgets / Quotas
607  Scheduler / Threads / Async Runtime
608  Synchronization / Atomics / Concurrency
609  Networking / Sockets / DNS / Transport
```

The important separation is:

```text
600 = state
601 = configuration
602 = observation
603 = authority
604 = local IPC
605 = lifecycle
606 = resources
607 = execution
608 = synchronization
609 = network transport
```

No layer should absorb another layer's responsibilities merely for convenience.

---

# 367. Final Invariants

The completed BOOTSTRAP-609 architecture guarantees the following design properties:

```text
1. Networking is asynchronous by default.
2. Blocking is explicit.
3. Socket ownership is deterministic.
4. Socket handles are generation-safe.
5. IPv4 and IPv6 are first-class.
6. TCP and UDP remain semantically distinct.
7. Local sockets integrate without contaminating the public API with OS details.
8. DNS is explicit and bounded.
9. Dual-stack connection attempts are bounded.
10. Connection pools are explicit rather than global.
11. Buffers are bounded and owned.
12. Backpressure is mandatory for streaming APIs.
13. Zero-copy is an optimization, not a semantic dependency.
14. TLS is a provider boundary.
15. TLS verification cannot silently disappear.
16. HTTP is layered above transport.
17. WebSocket is layered above HTTP.
18. HTTP/2 and HTTP/3 remain modular.
19. Proxying is explicit.
20. Resource accounting comes from BOOTSTRAP-606.
21. Security authority comes from BOOTSTRAP-603.
22. Async execution comes from BOOTSTRAP-607.
23. Synchronization comes from BOOTSTRAP-608.
24. Diagnostics come from BOOTSTRAP-602.
25. Configuration comes from BOOTSTRAP-601.
26. Lifecycle comes from BOOTSTRAP-605.
27. Live sockets are not checkpoint state.
28. WASM networking is host-controlled.
29. Mobile lifecycle constraints are represented explicitly.
30. No mandatory garbage collector is introduced.
31. No mandatory third-party networking library is introduced.
32. Unused networking features are dead-strippable.
33. Safe networking does not expose raw OS descriptors.
34. Protocol parsers are bounded and fuzzable.
35. Network failures remain distinguishable by layer.
36. Retry is not silently applied to arbitrary operations.
37. Application semantics are never inferred from TCP semantics.
38. Network resources participate in global runtime budgeting.
39. Network authority is least-privilege.
40. Network runtime remains modular.
```

---

# 368. BOOTSTRAP-609 Completion

**BOOTSTRAP-609 is COMPLETE.**

The Axiom runtime now has a complete native networking foundation extending from:

```text
IP address
   ↓
DNS
   ↓
Socket
   ↓
TCP / UDP
   ↓
Async I/O
   ↓
TLS boundary
   ↓
HTTP
   ↓
WebSocket
```

while remaining integrated with all preceding runtime layers.

---

# 369. Next Architecture Task

The next logical layer is:

**BOOTSTRAP-610 — Native Cryptography, TLS Provider, Certificate Trust, Key Management & Secure Transport Runtime 5.0**

It will turn the TLS boundary defined here into a complete security/cryptography subsystem while preserving the important architectural decision that applications should not be forced to depend on one particular crypto/TLS implementation.

The next task should proceed automatically.
:::

**BOOTSTRAP-609 hoàn tất.** Theo chuỗi kiến trúc đã định, bước tiếp theo là **BOOTSTRAP-610 — Cryptography / TLS / Certificate Trust / Key Management**.