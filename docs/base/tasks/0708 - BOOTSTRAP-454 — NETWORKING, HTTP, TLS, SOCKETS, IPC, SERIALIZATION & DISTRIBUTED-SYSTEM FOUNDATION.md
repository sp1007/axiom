# BOOTSTRAP-454 — NETWORKING, HTTP, TLS, SOCKETS, IPC, SERIALIZATION & DISTRIBUTED-SYSTEM FOUNDATION

**Trạng thái: COMPLETED / LOCKED**

Axiom networking phải đạt hai mục tiêu đồng thời:

1. Cung cấp primitive đủ thấp để xây network software hiệu năng cao.
2. Cung cấp abstraction đủ cao để xây HTTP/API/RPC/application hiện đại mà không biến runtime thành một khối bắt buộc.

Kiến trúc:

```text
Axiom Core
    ↓
OS / Platform I/O
    ↓
Socket / Network primitives
    ↓
TLS / Protocol
    ↓
HTTP / WebSocket / QUIC
    ↓
Serialization
    ↓
RPC / Distributed libraries
```

Không có HTTP/TLS/RPC nào được đưa vào language core.

---

## 454.1 — Networking layering

Networking được chia thành:

```text
net-core
net-platform
net-socket
net-dns
net-tls
net-http
net-websocket
net-quic
net-ipc
net-serialization
net-rpc
```

Mỗi tầng có thể được link độc lập.

---

## 454.2 — No mandatory network runtime

Console/freestanding application không dùng network không được link network subsystem.

---

## 454.3 — Network address types

Core networking library cung cấp:

```text
IpAddr
Ipv4Addr
Ipv6Addr
SocketAddr
```

---

## 454.4 — IPv4

IPv4 address có representation cố định 32-bit.

---

## 454.5 — IPv6

IPv6 address có representation cố định 128-bit.

---

## 454.6 — Address family

Socket address phải giữ family information.

---

## 454.7 — Port

Port là integer range phù hợp với protocol.

---

## 454.8 — Endpoint

Conceptual:

```text
Endpoint {
    address: IpAddr
    port: u16
}
```

---

## 454.9 — DNS names

Hostname không được coi là IP address.

---

## 454.10 — Hostname encoding

Hostname API phải phân biệt Unicode user-facing names với wire-level DNS representation.

---

# 454.11 — Socket abstraction

Primary abstraction:

```text
Socket
TcpSocket
UdpSocket
RawSocket
```

---

## 454.12 — Socket ownership

Socket là resource-owning type.

---

## 454.13 — Socket lifecycle

```text
created
bound
connected
listening
closed
```

protocol-dependent.

---

## 454.14 — Raw socket

Raw socket là platform-specific capability và thường unsafe/privileged.

---

## 454.15 — TCP

TCP API phải hỗ trợ:

```text
connect
listen
accept
read
write
shutdown
```

---

## 454.16 — UDP

UDP API hỗ trợ:

```text
bind
send_to
recv_from
```

---

## 454.17 — TCP stream

TCP được expose như byte stream.

Không được giả định message boundaries.

---

## 454.18 — UDP datagram

UDP giữ nguyên datagram boundaries.

---

## 454.19 — Partial reads

`read()` có thể trả ít bytes hơn requested.

---

## 454.20 — Partial writes

`write()` có thể ghi ít bytes hơn requested.

---

## 454.21 — Exact read

Library có thể cung cấp:

```text
read_exact
```

là convenience operation.

---

## 454.22 — Buffered I/O

Buffered socket I/O là optional wrapper.

---

## 454.23 — Zero-copy I/O

API có thể expose buffer-based operations tránh copy.

---

## 454.24 — Scatter/gather

Networking phải có thể hỗ trợ:

```text
readv
writev
```

hoặc equivalent abstraction.

---

## 454.25 — Socket buffers

Send/receive buffers là OS-managed resources và có thể được cấu hình.

---

# 454.26 — Blocking mode

Socket có thể chạy blocking.

---

## 454.27 — Non-blocking mode

Socket có thể chạy non-blocking.

---

## 454.28 — Blocking explicitness

Blocking network operation phải có effect metadata:

```text
@blocking
```

hoặc equivalent compiler-known effect.

---

## 454.29 — Async networking

Async API phải dùng cùng socket primitives.

---

## 454.30 — No mandatory async runtime

Async networking chỉ link executor/event-driver khi application sử dụng.

---

# 454.31 — Polling abstraction

Platform-independent polling abstraction:

```text
Poller
Event
Interest
Token
```

---

## 454.32 — OS event backends

Possible implementations:

```text
Linux → epoll / io_uring
Windows → IOCP
macOS → kqueue
BSD → kqueue
WASM → browser event model
```

Implementation choice không trở thành language semantic.

---

## 454.33 — Poll readiness

Readiness model phải phân biệt:

```text
readable
writable
error
closed
```

---

## 454.34 — Completion model

Completion-based backends có thể map vào common async abstraction.

---

## 454.35 — No fake readiness

Backend không được báo ready nếu operation semantics chưa thực sự ready.

---

## 454.36 — Cancellation

Async socket operation hỗ trợ cancellation khi backend cho phép.

---

## 454.37 — Cancellation safety

Cancellation không được bỏ qua cleanup resource ownership.

---

## 454.38 — Timeout

Networking API cung cấp:

```text
connect_timeout
read_timeout
write_timeout
operation_timeout
```

khi platform hỗ trợ.

---

## 454.39 — Deadline

Deadline nên dùng monotonic `Instant`.

---

## 454.40 — Keepalive

TCP keepalive configuration là optional platform capability.

---

# 454.41 — TCP server

Server API:

```text
TcpListener
accept()
```

---

## 454.42 — Concurrent connections

Application quyết định:

```text
thread
thread pool
async task
event loop
```

Không tự động spawn hidden threads.

---

## 454.43 — Backlog

Listen backlog là OS/platform parameter.

---

## 454.44 — Reuse address

Socket options như `SO_REUSEADDR` được expose khi platform hỗ trợ.

---

## 454.45 — TCP shutdown

Half-close semantics phải được expose rõ ràng.

---

## 454.46 — Nagle

TCP_NODELAY là explicit socket option.

---

## 454.47 — IPv4/IPv6 dual-stack

Behavior phải phụ thuộc platform và được query/configure thay vì giả định.

---

## 454.48 — UDP multicast

Multicast là optional socket capability.

---

## 454.49 — Broadcast

Broadcast là explicit socket option/capability.

---

## 454.50 — Network errors

Network errors là typed errors.

Ví dụ:

```text
ConnectionRefused
TimedOut
WouldBlock
ConnectionReset
AddressInUse
NetworkUnreachable
```

---

# 454.51 — DNS

DNS API:

```text
resolve(hostname)
lookup_service(...)
```

---

## 454.52 — DNS async

DNS resolution có thể async.

---

## 454.53 — DNS caching

Caching là library policy, không phải language semantic.

---

## 454.54 — System resolver

Default native resolver có thể dùng OS resolver.

---

## 454.55 — Custom resolver

Application có thể cung cấp resolver implementation.

---

## 454.56 — DNS security

DNSSEC/DoH/DoT thuộc higher-level network ecosystem.

---

## 454.57 — Reverse lookup

Reverse lookup là explicit operation.

---

## 454.58 — Service discovery

DNS-SRV/service discovery là protocol library.

---

## 454.59 — IDN

Internationalized domain names phải được xử lý bởi dedicated DNS/name library.

---

## 454.60 — DNS errors

DNS errors phải preserve enough information để debugging.

---

# 454.61 — TLS boundary

TLS không thuộc socket core.

Layer:

```text
TcpStream
    ↓
TlsStream
    ↓
HttpStream
```

---

## 454.62 — TLS provider

TLS implementation có thể là:

```text
Axiom implementation
platform provider
external package
```

---

## 454.63 — No mandatory TLS implementation

Core standard library không bắt buộc embed full TLS stack.

---

## 454.64 — TLS configuration

Conceptual:

```text
TlsClientConfig
TlsServerConfig
Certificate
PrivateKey
TrustStore
```

---

## 454.65 — Certificate validation

Default client validation phải verify certificate chain, hostname và validity according to configured trust policy.

---

## 454.66 — Trust store

Trust store là platform/application configuration.

---

## 454.67 — Certificate pinning

Pinning là explicit security policy.

---

## 454.68 — TLS versions

Library/backend chỉ enable secure supported versions.

Legacy protocols phải explicit compatibility mode nếu còn cần.

---

## 454.69 — Cipher selection

Cipher policy thuộc TLS provider.

---

## 454.70 — Private key ownership

Private keys là sensitive resources và phải có explicit ownership/lifetime.

---

# 454.71 — HTTP

HTTP library là higher-level protocol package.

---

## 454.72 — HTTP request

Conceptual:

```text
HttpRequest {
    method
    uri
    headers
    body
}
```

---

## 454.73 — HTTP response

```text
HttpResponse {
    status
    headers
    body
}
```

---

## 454.74 — Headers

Headers phải preserve wire semantics và cung cấp typed/common-header helpers.

---

## 454.75 — Header names

Case-insensitive semantics phải được tôn trọng theo HTTP specification.

---

## 454.76 — HTTP methods

Standard methods được represent bằng enum hoặc typed method abstraction.

Custom methods vẫn được hỗ trợ.

---

## 454.77 — URI

URI abstraction phải phân biệt:

```text
scheme
authority
path
query
fragment
```

---

## 454.78 — URL encoding

Percent encoding phải có API explicit.

---

## 454.79 — Request body streaming

HTTP body không được bắt buộc load toàn bộ vào RAM.

---

## 454.80 — Response streaming

Response cũng phải hỗ trợ streaming.

---

# 454.81 — HTTP protocol versions

Architecture có thể hỗ trợ:

```text
HTTP/1.1
HTTP/2
HTTP/3
```

nhưng từng implementation là module riêng.

---

## 454.82 — HTTP/1.1

Support persistent connections và chunked transfer khi applicable.

---

## 454.83 — HTTP/2

HTTP/2 multiplexing là implementation concern của HTTP/2 backend.

---

## 454.84 — HTTP/3

HTTP/3 chạy trên QUIC.

---

## 454.85 — Connection pooling

Pooling là optional client feature.

---

## 454.86 — Proxy

HTTP client có explicit proxy configuration.

---

## 454.87 — Redirects

Redirect following phải là client policy, không hidden protocol behavior.

---

## 454.88 — Cookies

Cookies là separate higher-level package.

---

## 454.89 — Compression

Compression/decompression là explicit middleware.

---

## 454.90 — Content encoding

Application phải có thể inspect negotiated content encoding.

---

# 454.91 — WebSocket

WebSocket package nằm trên HTTP upgrade/handshake.

---

## 454.92 — WebSocket message

API phải phân biệt:

```text
Text
Binary
Ping
Pong
Close
```

---

## 454.93 — WebSocket fragmentation

Library có thể hide fragmentation while preserving streaming semantics.

---

## 454.94 — WebSocket backpressure

Send queue phải có explicit backpressure behavior.

---

## 454.95 — WebSocket async

Async WebSocket dùng network executor/event system.

---

# 454.96 — QUIC

QUIC là optional protocol package.

---

## 454.97 — QUIC streams

Multiple independent streams được expose.

---

## 454.98 — QUIC datagrams

Datagram mode được hỗ trợ nếu provider/backend có.

---

## 454.99 — QUIC TLS

QUIC phải integrate TLS 1.3 semantics required by protocol.

---

## 454.100 — QUIC implementation boundary

QUIC implementation không được hard-code vào socket core.

---

# 454.101 — IPC

IPC layer:

```text
pipe
named_pipe
unix_socket
shared_memory
event
semaphore
```

---

## 454.102 — Anonymous pipe

Pipe dùng cho parent/child process communication.

---

## 454.103 — Named pipe

Named pipe platform abstraction hỗ trợ Windows/Unix variants khi có.

---

## 454.104 — Unix domain socket

Unix domain sockets là platform-specific but standardized abstraction.

---

## 454.105 — Shared memory

Shared memory là explicit resource.

---

## 454.106 — Shared memory ownership

Memory mapping lifecycle phải deterministic.

---

## 454.107 — Shared memory synchronization

Shared memory không tự đảm bảo synchronization.

Phải dùng atomic/lock/semaphore primitives.

---

## 454.108 — Memory-mapped files

Mapped file APIs integrate filesystem + virtual memory boundary.

---

## 454.109 — IPC security

IPC endpoint permissions thuộc OS/security layer.

---

## 454.110 — Capability-based IPC

High-level frameworks có thể model IPC endpoints as capabilities.

---

# 454.111 — Serialization

Serialization không thuộc language core.

---

## 454.112 — Binary serialization

Axiom có thể cung cấp efficient binary serialization traits.

Conceptual:

```text
trait Encode
trait Decode
```

---

## 454.113 — Compile-time serialization

Comptime/derive có thể generate serializers.

---

## 454.114 — No reflection dependency

Serializer không cần runtime reflection.

---

## 454.115 — Schema

Schema có thể được generated from type metadata.

---

## 454.116 — Versioned schema

Serialized formats phải hỗ trợ schema versioning khi protocol yêu cầu.

---

## 454.117 — Endianness

Wire formats phải define endian explicitly.

---

## 454.118 — Integer encoding

Protocol có thể sử dụng:

```text
fixed-width
varint
zigzag
```

---

## 454.119 — String encoding

UTF-8 là default Axiom string representation nhưng wire protocol vẫn phải follow its own specification.

---

## 454.120 — Zero-copy decode

Decoder có thể trả borrowed views nếu underlying buffer lifetime còn valid.

---

# 454.121 — JSON

JSON là ecosystem/standard package.

---

## 454.122 — JSON DOM

Có thể cung cấp dynamic JSON value:

```text
Null
Bool
Number
String
Array
Object
```

---

## 454.123 — JSON streaming

Streaming parser/encoder được hỗ trợ.

---

## 454.124 — JSON typed mapping

Compile-time derive có thể map JSON ↔ Axiom structs.

---

## 454.125 — JSON number semantics

Parser phải define chính xác integer/float handling, tránh silent precision loss.

---

# 454.126 — Binary formats

Architecture có thể support:

```text
CBOR
MessagePack
Protobuf
FlatBuffers
custom binary
```

ở package layer.

---

## 454.127 — Schema compiler

Schema-driven protocols có thể có external schema compiler/tool.

---

## 454.128 — Generated bindings

Generated bindings integrate với semantic metadata 446.

---

## 454.129 — Generated source provenance

Generated serialization code phải record provenance.

---

## 454.130 — ABI-independent serialization

Serialized representation không được phụ thuộc native struct padding trừ khi explicitly defined.

---

# 454.131 — RPC

RPC là library/ecosystem layer.

---

## 454.132 — RPC transport

RPC có thể chạy trên:

```text
TCP
HTTP/2
HTTP/3
QUIC
Unix socket
named pipe
```

---

## 454.133 — RPC interface

IDL hoặc Axiom trait có thể định nghĩa service interface.

---

## 454.134 — Generated RPC stubs

Comptime/build tooling có thể generate:

```text
client
server
serialization
```

---

## 454.135 — RPC error model

RPC errors map vào:

```text
Result<T, RpcError>
```

---

## 454.136 — RPC cancellation

Cancellation phải propagate nếu transport supports it.

---

## 454.137 — RPC timeout

Timeout/deadline explicit.

---

## 454.138 — RPC streaming

Support:

```text
unary
server_stream
client_stream
bidirectional_stream
```

---

## 454.139 — RPC backpressure

Streaming RPC phải define flow control/backpressure.

---

## 454.140 — RPC versioning

Service/API version phải độc lập với Axiom package version.

---

# 454.141 — Distributed-system primitives

Standard library không cố trở thành distributed framework.

Có thể cung cấp low-level primitives:

```text
Id
Timestamp
Duration
Cancellation
Channel
Atomic
```

---

## 454.142 — Logical clocks

Distributed libraries có thể implement Lamport/vector clocks.

Không thuộc core.

---

## 454.143 — Serialization + time

Distributed protocols phải tránh dùng wall-clock như monotonic ordering primitive.

---

## 454.144 — UUID

UUID là standard library utility.

---

## 454.145 — Random IDs

Cryptographically secure random IDs phải dùng secure RNG capability.

---

## 454.146 — Retry policy

Retry thuộc application/protocol library, không automatic cho arbitrary network operations.

---

## 454.147 — Idempotency

HTTP/RPC retry libraries phải expose idempotency semantics.

---

## 454.148 — Backoff

Exponential backoff là library policy.

---

## 454.149 — Circuit breaker

Circuit breaker là higher-level library.

---

## 454.150 — Service discovery

Service discovery là ecosystem component.

---

# 454.151 — Network security boundary

Network data luôn được coi là untrusted input.

---

## 454.152 — Parser safety

Protocol parsers phải bounds-check input.

---

## 454.153 — Integer overflow

Parser phải xử lý overflow explicit.

---

## 454.154 — Resource exhaustion

Network APIs phải có configurable limits:

```text
max_message_size
max_header_size
max_connections
max_buffer
max_body_size
```

---

## 454.155 — Timeout defense

Protocol servers phải có configurable timeouts.

---

## 454.156 — Slow client defense

Library có thể giới hạn idle/read duration.

---

## 454.157 — Compression bombs

Decompression APIs phải hỗ trợ resource limits.

---

## 454.158 — Parser recursion

Nested formats phải có recursion/depth limits.

---

## 454.159 — TLS key security

Private-key memory handling nên minimize unnecessary copies.

---

## 454.160 — Certificate validation

Certificate validation failures phải return typed error.

---

# 454.161 — Network observability

Network subsystem có optional tracing:

```text
connection
DNS
TLS handshake
request
response
bytes
latency
retry
```

---

## 454.162 — No secret logging

TLS private keys, credentials và authorization tokens không được tự động log.

---

## 454.163 — Structured network diagnostics

Diagnostics có machine-readable form.

---

## 454.164 — Network metrics

Metrics có thể include:

```text
bytes_in
bytes_out
connections
errors
latency
timeouts
```

---

## 454.165 — Packet capture

Packet capture là external/platform capability, không hidden behavior.

---

# 454.166 — Network testing

Test framework hỗ trợ:

```text
loopback
mock transport
in-memory transport
deterministic DNS
fake clock
fault injection
```

---

## 454.167 — In-memory transport

Protocol implementations nên có thể test mà không cần real network.

---

## 454.168 — Fault injection

Tests có thể simulate:

```text
timeout
reset
partial write
partial read
packet loss
connection close
```

---

## 454.169 — Protocol fuzzing

HTTP/TLS/protocol parsers phải fuzzable.

---

## 454.170 — Serialization fuzzing

Decode functions phải fuzzable với arbitrary bytes.

---

# 454.171 — Async integration

Network Future phải integrate async model 424.

---

## 454.172 — Executor independence

Network library không khóa vào một executor implementation.

---

## 454.173 — Reactor/proactor abstraction

Platform adapter có thể dùng reactor hoặc proactor model.

---

## 454.174 — io_uring

Linux backend có thể use io_uring mà không làm API Linux-specific.

---

## 454.175 — IOCP

Windows backend có thể use IOCP.

---

## 454.176 — kqueue

BSD/macOS backend có thể use kqueue.

---

## 454.177 — WASM

WASM backend sử dụng browser fetch/WebSocket/WebTransport-like capabilities khi available.

---

## 454.178 — Browser restrictions

WASM network APIs phải tôn trọng CORS, browser security và origin restrictions.

---

## 454.179 — Native networking

Native targets có unrestricted OS network API theo process privileges.

---

## 454.180 — Capability manifest

Network permissions/capabilities có thể được biểu diễn trong build/runtime manifest.

---

# 454.181 — Zero-copy networking

Library phải cung cấp low-level buffer API.

---

## 454.182 — Buffer ownership

Network buffer ownership phải explicit.

---

## 454.183 — Scatter/gather ownership

IO vectors phải giữ valid memory lifetime trong operation.

---

## 454.184 — Pinned buffers

Nếu backend yêu cầu pinned/stable memory cho async IO, abstraction phải biểu diễn requirement.

---

## 454.185 — Buffer pools

High-performance servers có thể sử dụng pool/arena allocator 423.

---

## 454.186 — Allocation-aware APIs

Network APIs có thể expose allocation behavior qua metadata.

---

## 454.187 — `@no_alloc`

Parser/codec có thể cung cấp `@no_alloc` implementations.

---

## 454.188 — `@no_block`

Protocol parsing phải có thể chạy không blocking.

---

## 454.189 — `@no_panic`

Security-critical parsers có thể target no-panic contract.

---

## 454.190 — Performance metadata

Compiler/AI metadata ghi:

```text
allocations
blocking
copies
syscalls
```

khi phân tích được.

---

# 454.191 — Network ABI

Socket handles có target-specific representation.

---

## 454.192 — FFI handles

OS socket descriptors/handles có thể wrap trong Axiom resource types.

---

## 454.193 — C interoperability

Network APIs có thể interoperate trực tiếp với native socket APIs qua 451.

---

## 454.194 — Handle ownership

`close()` và `drop()` phải tránh double-close.

---

## 454.195 — Borrowed handles

APIs có thể nhận borrowed native handles.

---

## 454.196 — Raw handles

Raw handle access là low-level/unsafe.

---

## 454.197 — ABI stability

Public network binary APIs phải use stable concrete ABI.

---

## 454.198 — Generic network APIs

Generic implementations monomorphize theo 426.

---

## 454.199 — Dynamic protocol providers

Dynamic provider interfaces dùng `dyn Trait` explicit.

---

## 454.200 — Provider isolation

TLS/QUIC/HTTP provider implementation không được leak private ABI vào application API nếu portable interface được chọn.

---

# 454.201 — Build integration

Network package dependencies được tracked trong build graph 432.

---

## 454.202 — Feature flags

Ví dụ:

```text
net.tcp
net.udp
net.tls
net.http1
net.http2
net.http3
net.websocket
```

---

## 454.203 — Binary pruning

Không sử dụng HTTP/QUIC/TLS thì những subsystem đó không được link.

---

## 454.204 — Static linking

Native static network dependencies phải được linker GC/pruning tối ưu.

---

## 454.205 — Dynamic providers

Application có thể chọn dynamic TLS/backend libraries nếu desired.

---

## 454.206 — Offline builds

Dependency cache/vendoring phải hỗ trợ offline build.

---

## 454.207 — Dependency provenance

Network security-critical dependencies phải có provenance metadata.

---

## 454.208 — Reproducibility

Protocol generated code phải deterministic.

---

## 454.209 — Generated bindings

Generated network code phải integrate semantic metadata.

---

## 454.210 — Schema cache

Schema compilation artifacts được cache theo content hash.

---

# 454.211 — AI integration

AI tooling có thể query:

```text
socket
endpoint
protocol
TLS
certificate
HTTP handler
RPC service
serialization
IPC
```

---

## 454.212 — Call graph

AI có thể query:

```text
which function opens socket?
which function sends data?
where is TLS configured?
```

---

## 454.213 — Security graph

Metadata có thể show:

```text
network input
→ parser
→ deserialization
→ trusted object
```

---

## 454.214 — Trust-boundary metadata

Network input được đánh dấu untrusted source.

---

## 454.215 — Unsafe network code

Unsafe socket/raw-packet operations được index như unsafe sites.

---

## 454.216 — Protocol contract metadata

Generated protocol APIs expose:

```text
wire format
version
limits
timeouts
ownership
```

---

# 454.217 — Native high-performance server profile

Axiom phải có khả năng xây server với:

```text
non-blocking socket
event loop
zero-copy buffers
custom allocator
worker threads
SIMD parser
```

mà không cần GC hoặc heavyweight runtime.

---

## 454.218 — Low-latency profile

Có thể disable:

```text
automatic logging
allocation-heavy abstractions
exceptions
background schedulers
```

---

## 454.219 — Embedded networking

Freestanding target có thể implement custom network driver.

---

## 454.220 — Kernel networking

Axiom unsafe/freestanding layer có thể access NIC/MMIO primitives.

---

## 454.221 — Driver boundary

Hardware driver code thuộc trusted/unsafe layer.

---

## 454.222 — No mandatory libc

Network stack không được phụ thuộc libc requirement.

---

## 454.223 — Native syscalls

Platform layer có thể invoke native syscalls directly.

---

## 454.224 — Syscall abstraction

Portable API tách khỏi syscall number/ABI.

---

## 454.225 — Syscall error mapping

Native error codes map sang typed `NetworkError`/`OsError`.

---

# 454.226 — Protocol implementation architecture

Một protocol implementation nên chia:

```text
wire parser
wire encoder
state machine
transport
application API
```

---

## 454.227 — State machines

Protocol state machines nên được explicit trong MIR/HIR hoặc generated code.

---

## 454.228 — Parser combinators

Parser combinators là library option.

---

## 454.229 — Generated parser

Comptime có thể generate efficient parser.

---

## 454.230 — Bounds proof

Compiler có thể eliminate redundant bounds checks sau proof.

---

## 454.231 — Malformed input

Malformed packets/messages phải return typed errors, không UB.

---

## 454.232 — Parser panic

Network input không được tự động gây panic chỉ vì malformed data.

---

## 454.233 — Resource cleanup

Failed handshake/parse phải cleanup partial resources deterministic.

---

## 454.234 — Connection state

Connection objects phải model state transitions.

---

## 454.235 — Invalid state operations

Compiler/type system hoặc runtime API phải prevent impossible operations khi có thể.

---

# 454.236 — HTTP server architecture

Conceptual:

```text
Listener
  ↓
Connection
  ↓
HTTP parser
  ↓
Request
  ↓
Router
  ↓
Handler
  ↓
Response
```

---

## 454.237 — Handler signature

Có thể dùng:

```text
fn handle(req: Request) -> Result<Response, Error>
```

---

## 454.238 — Middleware

Middleware là function/trait composition.

---

## 454.239 — No inheritance middleware

Middleware chain không sử dụng class inheritance.

---

## 454.240 — Router

Router là library data structure.

---

## 454.241 — Static routes

Compile-time route generation có thể được hỗ trợ.

---

## 454.242 — Dynamic routes

Dynamic route registration vẫn được hỗ trợ.

---

## 454.243 — HTTP streaming handler

Handler có thể return streaming body.

---

## 454.244 — Backpressure

Streaming response phải expose backpressure.

---

## 454.245 — Graceful shutdown

Server có explicit graceful shutdown API.

---

# 454.246 — Client architecture

HTTP client có:

```text
Client
ConnectionPool
RequestBuilder
Response
BodyStream
```

---

## 454.247 — Connection reuse

Pooling policy configurable.

---

## 454.248 — DNS reuse

Resolved endpoints có thể cache.

---

## 454.249 — TLS session reuse

Provider có thể support session resumption.

---

## 454.250 — Client cancellation

Cancelled request phải cleanup connection state correctly.

---

# 454.251 — IPC/RPC security

Authentication/authorization không thuộc raw socket.

---

## 454.252 — TLS authentication

TLS can provide server/client authentication.

---

## 454.253 — Application authentication

Bearer tokens/API keys/custom mechanisms là application layer.

---

## 454.254 — Credential storage

Credential storage phải dùng platform secure storage khi available.

---

## 454.255 — No credential logging

Standard network diagnostics không log secrets.

---

# 454.256 — Network hard invariants

1. Networking không thuộc language core.
2. Networking không thuộc mandatory runtime.
3. Socket là owned resource.
4. Socket lifecycle phải deterministic.
5. IPv4/IPv6 là first-class.
6. Socket family phải explicit.
7. TCP phải được model như byte stream.
8. UDP phải preserve datagram boundaries.
9. Partial reads phải được xử lý đúng.
10. Partial writes phải được xử lý đúng.
11. Blocking/non-blocking phải explicit.
12. Blocking effects phải machine-readable.
13. Async networking integrate model 424.
14. Async runtime không mandatory.
15. Platform polling backend phải được abstract.
16. epoll/io_uring/IOCP/kqueue không leak vào portable semantic API.
17. Cancellation phải cleanup-safe.
18. Timeout/deadline phải được hỗ trợ.
19. Deadline nên dùng monotonic time.
20. DNS tách khỏi socket.
21. Hostname tách khỏi IP address.
22. System resolver có thể được dùng.
23. Custom resolver có thể được cung cấp.
24. TLS tách khỏi socket.
25. TLS implementation không mandatory trong core.
26. Certificate validation phải explicit và secure-by-default.
27. Trust store phải configurable.
28. Private key lifetime phải explicit.
29. HTTP là higher-level package.
30. HTTP request/response phải typed.
31. HTTP body phải hỗ trợ streaming.
32. HTTP/1.1, HTTP/2, HTTP/3 là separate protocol implementations.
33. HTTP redirect là policy, không hidden behavior.
34. Proxy là explicit configuration.
35. Compression là explicit middleware.
36. WebSocket là higher-level protocol.
37. QUIC là optional protocol package.
38. IPC tách khỏi networking socket abstraction khi semantics khác.
39. Shared memory ownership phải deterministic.
40. Shared memory không tự đảm bảo synchronization.
41. Serialization không thuộc language core.
42. Serialization phải có compile-time generation khả dụng.
43. Runtime reflection không phải requirement của serialization.
44. Wire representation không được phụ thuộc native padding trừ khi explicit.
45. Endianness phải được protocol định nghĩa.
46. Binary decoding phải bounds-safe.
47. Malformed network data không được tạo UB trong safe code.
48. Integer overflow trong parser phải được xử lý.
49. Network resource limits phải configurable.
50. Timeout defense phải khả dụng.
51. Compression/decompression phải có resource limits.
52. Parser recursion phải có giới hạn khi cần.
53. RPC là ecosystem/library layer.
54. RPC transport phải có thể thay thế.
55. RPC errors dùng Result model.
56. RPC cancellation phải explicit.
57. RPC deadline phải explicit.
58. Streaming RPC phải support backpressure.
59. Service versioning tách package versioning.
60. Retry không được implicit cho arbitrary operations.
61. Idempotency phải được respect khi retry.
62. Network diagnostics phải structured.
63. Secrets không được tự động log.
64. Network testing phải hỗ trợ mock/in-memory transport.
65. Fault injection phải khả dụng.
66. Network protocol parsers phải fuzzable.
67. Serialization decoders phải fuzzable.
68. Network APIs có thể cung cấp zero-copy.
69. Buffer lifetime phải explicit.
70. Async I/O buffer lifetime phải safe.
71. Allocation behavior có thể được query/measure.
72. `@no_alloc`, `@no_block`, `@no_panic` có thể áp dụng cho suitable network components.
73. Native socket handles integrate FFI 451.
74. Raw socket operations là explicit low-level capability.
75. Double-close phải được prevented bởi ownership model.
76. Network dependencies phải tích hợp build graph.
77. Feature-level linking phải giảm binary size.
78. Offline/vendored network dependencies phải được hỗ trợ.
79. Dependency provenance phải được ghi.
80. Generated protocol code phải deterministic.
81. AI tooling phải query được network/security semantics.
82. Network inputs phải được đánh dấu untrusted.
83. Trust boundaries phải xuất hiện trong semantic metadata.
84. Unsafe network operations phải searchable.
85. Native high-performance servers phải không cần GC.
86. Custom allocator phải dùng được cho network servers.
87. SIMD parser có thể được sử dụng.
88. Freestanding networking phải khả dụng.
89. Kernel/driver networking có thể dùng unsafe layer.
90. Network stack không được yêu cầu libc.
91. Native syscall layer phải tồn tại độc lập.
92. Protocol state machines phải explicit.
93. Generated parsers phải giữ source provenance.
94. Failed protocol operations phải cleanup deterministic.
95. HTTP server phải hỗ trợ explicit graceful shutdown.
96. HTTP middleware dùng composition/traits, không inheritance.
97. HTTP streaming phải có backpressure.
98. HTTP client cancellation phải cleanup đúng.
99. Credential handling phải tách khỏi raw networking.
100. **Axiom networking phải cho phép xây từ một UDP/socket server cực nhỏ đến HTTP/3/RPC/distributed systems mà không ép toàn bộ protocol stack vào mọi executable.**

**BOOTSTRAP-454 hoàn tất.**

---

# BOOTSTRAP-455 — DATABASE, STORAGE, FILE FORMAT, MEMORY-MAPPED DATA & TRANSACTION FOUNDATION

Task kế tiếp khóa tầng persistent data:

```text
filesystem
file I/O
memory-mapped file
binary storage
database abstraction
embedded database
SQL
transactions
WAL
index
cache
```

trong đó sẽ đặc biệt xác định **Axiom có cần built-in database features hay chỉ cung cấp primitives đủ mạnh để xây database engine native**.

Nguyên tắc tiếp tục giữ:

```text
language core
    ≠
database runtime
```

và một executable chỉ đọc/ghi file không được kéo database engine vào binary.