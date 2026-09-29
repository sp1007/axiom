# BOOTSTRAP-401 — Axiom Networking, Protocol, Packet, Transport & High-Performance Network I/O Engine

Sau **400 — Storage, Filesystem, VFS & Persistent I/O**, bước tiếp theo là **Networking**.

Đây là một domain rất quan trọng vì networking là nơi Axiom phải đồng thời giải quyết:

- memory ownership;
- zero-copy;
- async;
- concurrency;
- I/O;
- security;
- serialization;
- distributed systems;
- OS syscalls;
- SIMD;
- batching;
- DMA;
- high-throughput và low-latency.

Mục tiêu của 401:

> **Network programming phải có thể đi từ socket API cấp cao xuống packet buffer, zero-copy I/O, kernel bypass và raw network device mà không cần thay đổi memory model của Axiom.**

---

# 1. Networking không thuộc Core

Core chỉ cần:

```text id="k4s9m1"
Memory
Ownership
Capability
I/O
Async
Concurrency
Serialization
Security
```

Networking nằm phía trên:

```text id="5g7j3x"
Networking
 ├── Address
 ├── Endpoint
 ├── Socket
 ├── Packet
 ├── Stream
 ├── Datagram
 ├── Protocol
 ├── TLS
 ├── HTTP
 ├── RPC
 └── NetworkDevice
```

---

# 2. Network Address

Không dùng string cho địa chỉ mạng.

Các semantic types:

```text id="8s1p2a"
IpAddress
Ipv4Address
Ipv6Address
MacAddress
Port
```

---

# 3. Endpoint

```text id="j6d4q8"
Endpoint {
    address
    port
}
```

Protocol-specific endpoint có thể thêm:

```text id="5w9c3f"
TcpEndpoint
UdpEndpoint
UnixEndpoint
```

---

# 4. IPv4 / IPv6

Hai loại phải là distinct semantic types.

Không implicit convert:

```text id="4p3h2m"
Ipv4Address ↔ Ipv6Address
```

nếu conversion không có semantics rõ ràng.

---

# 5. Network Prefix

```text id="v7k1za"
Ipv4Prefix
Ipv6Prefix
```

cho subnet/routing.

---

# 6. IP Address Operations

Có thể compile-time:

```text id="r5m2x9"
contains
mask
network
broadcast
prefix_length
```

---

# 7. MAC Address

MAC là link-layer identity.

Không được coi là IP identity.

---

# 8. Socket

Socket là OS resource:

```text id="d4q8ye"
SocketHandle
```

ownership theo resource model.

---

# 9. Socket Types

```text id="a7c2mk"
TCP
UDP
Unix
Raw
Packet
```

---

# 10. TCP

TCP là byte stream:

```text id="g8w1kp"
Stream<u8>
```

không có message boundary semantics.

---

# 11. UDP

UDP là datagram:

```text id="f3j7qz"
Datagram {
    payload
    source
    destination
}
```

mỗi datagram giữ boundary.

---

# 12. QUIC

QUIC có nhiều stream trên một connection:

```text id="n6r5tx"
QuicConnection
 ├── Stream 0
 ├── Stream 1
 ├── Stream 2
 └── ...
```

Connection và stream là logical resources khác nhau.

---

# 13. Network Stream

Không nên buộc TCP/QUIC stream vào một concrete implementation.

```text id="y4p8cc"
trait ByteStream
```

có thể có:

```text id="v8m2de"
TcpStream
TlsStream
QuicStream
UnixStream
MemoryStream
```

---

# 14. Stream Composition

Ví dụ:

```text id="u2n7qk"
TCP
 ↓
TLS
 ↓
HTTP
```

hoặc:

```text id="f1r6cz"
TCP
 ↓
Compression
 ↓
Protocol
```

---

# 15. Layering

Axiom phải hỗ trợ layering mà không ép class inheritance:

```text id="6j2p0s"
Transport
  +
Codec
  +
Protocol
```

thông qua generic functions/traits.

---

# 16. Network Buffer

```text id="a5x8qv"
PacketBuffer
ByteBuffer
NetworkBuffer
```

có ownership rõ ràng.

---

# 17. Buffer Pool

High-performance networking không nên:

```text id="m4k9tr"
allocate()
free()
allocate()
free()
```

cho từng packet.

Có thể sử dụng:

```text id="e8s2yw"
PacketPool
Slab
Arena
Ring
```

---

# 18. Buffer Reuse

390/400 buffer reuse semantics được tái sử dụng.

---

# 19. Scatter/Gather

Network send:

```text id="w5h1zn"
header
body
trailer
```

có thể gửi bằng scatter/gather mà không concatenate.

---

# 20. Receive Scatter

NIC/kernel có thể nhận vào nhiều buffers.

---

# 21. Zero-Copy Send

Nếu ownership cho phép:

```text id="c7m3la"
ApplicationBuffer
       ↓
Kernel/NIC
```

không copy.

---

# 22. Zero-Copy Receive

Tương tự:

```text id="q9s4bd"
NIC
 ↓
DMA Buffer
 ↓
Application View
```

---

# 23. DMA

DMA buffer có storage ownership:

```text id="e1n8kf"
Host
Device
```

giống 390/399.

---

# 24. Registered Buffer

RDMA/advanced networking có:

```text id="b6q2mx"
RegisteredBuffer
```

với registration lifetime.

---

# 25. Registration

Không được unregister khi outstanding operation còn sử dụng buffer.

Compiler/runtime phải track capability.

---

# 26. Async Network

Socket operation:

```text id="z7r3ht"
Future<Result<...>>
```

không block thread.

---

# 27. Blocking Network

Sync API vẫn được hỗ trợ:

```text id="n3v6xa"
read()
write()
accept()
```

nhưng effect system ghi nhận `BLOCKING`.

---

# 28. Async ≠ Nonblocking

Một async abstraction có thể dùng:

```text id="r8f2wp"
io_uring
IOCP
epoll
kqueue
worker
```

Không được gắn semantic meaning vào backend.

---

# 29. Poll

Low-level API:

```text id="k5m1qc"
poll
```

cho event-driven networking.

---

# 30. Readiness vs Completion

Phải phân biệt:

```text id="h2x8sv"
READINESS
COMPLETION
```

epoll-like và IOCP-like systems khác nhau.

---

# 31. Network Event

```text id="j4w7np"
Readable
Writable
Connected
Closed
Error
```

---

# 32. Cancellation

Network operation cancellation:

```text id="p3z6rm"
requested
cancelled
completed
unknown
```

không giả định cancellation luôn instantaneous.

---

# 33. Deadline

Network operations có:

```text id="c8v1yt"
Timeout
Deadline
```

390 semantics được reuse.

---

# 34. TCP Connection Lifecycle

```text id="z5x2mn"
Created
Bound
Listening
Connecting
Connected
Closing
Closed
```

---

# 35. TCP Half Close

TCP có:

```text id="u6q9rd"
shutdown_read
shutdown_write
```

khác với close toàn socket.

---

# 36. Connection Ownership

Accepted connection:

```text id="e2j7ak"
listener.accept()
```

trả ownership của connection.

---

# 37. Listener

```text id="m8c4vy"
TcpListener
```

có thể:

```text id="r1p5qs"
bind
listen
accept
```

---

# 38. Concurrent Accept

Nhiều worker có thể accept connections.

Synchronization semantics phải rõ.

---

# 39. Connection Migration

Connection có thể được chuyển ownership sang task:

```text id="s3x7bd"
accept
 ↓
spawn
 ↓
Task owns connection
```

---

# 40. Task Send

Nếu task migratable:

```text id="q2n6wp"
Connection: Send
```

phải thỏa Send contract.

---

# 41. UDP

UDP send/receive giữ datagram boundary.

Không được expose dưới dạng generic ByteStream nếu điều đó làm mất semantics.

---

# 42. UDP Multicast

Có thể:

```text id="v5k8zs"
join_group
leave_group
```

---

# 43. Broadcast

Broadcast là network policy, không phải general multicast abstraction.

---

# 44. Socket Options

```text id="d9m2la"
reuse_address
reuse_port
no_delay
keep_alive
receive_buffer
send_buffer
```

là explicit configuration.

---

# 45. Kernel Socket Buffer

Không đồng nhất application buffer với kernel socket buffer.

---

# 46. Backpressure

Network stream phải có bounded buffering.

```text id="p8f4je"
Producer
 ↓
bounded queue
 ↓
Network
```

---

# 47. Slow Consumer

Nếu consumer chậm:

```text id="c1r7mx"
BLOCK
DROP
BUFFER
DISCONNECT
```

policy explicit.

---

# 48. TCP Backpressure

TCP flow control là protocol behavior.

Application-level backpressure là abstraction khác.

---

# 49. Datagram Loss

UDP packet loss là normal protocol condition.

Không biến thành generic I/O error.

---

# 50. Datagram Ordering

UDP không guarantee ordering.

Axiom không được thêm ordering guarantee giả.

---

# 51. QUIC Ordering

QUIC guarantees ordering **per stream**, không phải toàn connection.

---

# 52. Reliable Datagram

Nếu cần:

```text id="z6h2qp"
reliable datagram
```

phải là protocol abstraction trên UDP/QUIC/etc.

---

# 53. Packet

Low-level packet:

```text id="m7v3xc"
Packet {
    bytes
    metadata
}
```

---

# 54. Packet Layers

Có thể parse:

```text id="u4r8nk"
Ethernet
 ↓
IPv4/IPv6
 ↓
TCP/UDP
 ↓
Application
```

---

# 55. Packet View

Parser nên tạo views:

```text id="b2f7qd"
EthernetView
IpView
TcpView
```

thay vì copy packet.

---

# 56. Mutable Packet View

Packet mutation:

```text id="x9c5mt"
mut_view<Packet>
```

chỉ được phép khi checksum/layout constraints được duy trì.

---

# 57. Packet Parser

Parser có thể:

```text id="a6k2wp"
parse(packet)
```

trả typed view.

---

# 58. Bounds Verification

Compiler verify:

```text id="h8r3zn"
header length
payload length
offset
alignment
```

trước khi safe access.

---

# 59. Malformed Packet

Parse failure:

```text id="f4q9yv"
Malformed
Unsupported
Truncated
InvalidChecksum
```

không panic mặc định.

---

# 60. Endianness

Network byte order thường big-endian.

Axiom phải hỗ trợ explicit:

```text id="n1s7kc"
to_be
from_be
to_le
from_le
```

---

# 61. Endian Types

Có thể có semantic wrapper:

```text id="t8w2mq"
be<u16>
le<u32>
```

để parse protocol structures.

---

# 62. Packed Protocol Structures

Không được dùng `@repr(packed)` một cách vô điều kiện.

Misaligned access phải được xử lý đúng.

---

# 63. Protocol Struct

Có thể định nghĩa:

```text id="y5v8dr"
struct IpHeader {
    version
    ...
}
```

với explicit wire representation.

---

# 64. Wire Representation

`@repr(wire(...))` có thể là future language facility.

Nó khác:

```text id="a1j4pk"
@repr(C)
```

vì C layout và network wire layout không đồng nhất.

---

# 65. Serialization

Protocol encoding reuse 395/390.

Không tạo serialization engine riêng nếu không cần.

---

# 66. Protocol Definition

Axiom nên cho phép protocol library định nghĩa:

```text id="w7q3fn"
encode
decode
validate
```

với typed representation.

---

# 67. Incremental Parser

Network parser không được yêu cầu toàn bộ message nằm trong memory.

Có:

```text id="s4n8xc"
partial
need_more
complete
error
```

---

# 68. Framing

TCP application protocol cần framing:

```text id="m6r2zy"
length-prefix
delimiter
fixed-size
chunked
```

---

# 69. Framing State

Parser state có ownership rõ ràng.

Không hidden global parser state.

---

# 70. HTTP

HTTP nên là library/domain layer.

Hỗ trợ:

```text id="x3p7av"
HTTP/1.1
HTTP/2
HTTP/3
```

---

# 71. HTTP Request

Typed structure:

```text id="c8m1qe"
Request {
    method
    target
    headers
    body
}
```

---

# 72. HTTP Body

Body nên là stream:

```text id="z5n9wd"
Stream<ByteBuffer>
```

không mặc định load toàn bộ.

---

# 73. HTTP Headers

Header names/values cần semantic handling.

Case-insensitivity phải preserve protocol semantics.

---

# 74. HTTP/2

Multiplex:

```text id="r4k6tb"
Connection
 ├── Stream
 ├── Stream
 └── Stream
```

---

# 75. HTTP/3

HTTP/3 chạy trên QUIC.

Không thiết kế một transport abstraction giả định TCP.

---

# 76. TLS

TLS nằm security/network boundary:

```text id="e9p2mx"
TcpStream
 ↓
TlsStream
 ↓
Application
```

---

# 77. TLS Credentials

Key/certificate types reuse 394.

Không dùng raw byte arrays ở high-level API nếu typed security object phù hợp.

---

# 78. Certificate Validation

Certificate validation phải là explicit security operation.

---

# 79. TLS Session

Session state là owning resource.

---

# 80. Protocol Security

Axiom nên cho phép protocol declare:

```text id="u7x3kp"
requires_tls
requires_auth
requires_integrity
```

để compiler/tooling phát hiện misuse.

---

# 81. RPC

RPC domain layer trên:

```text id="m2v8qa"
Serialization
Network
Security
Async
```

---

# 82. RPC Function

Source có thể trông gần function call:

```text id="y6r1zc"
client.get_user(id)
```

nhưng semantics phải vẫn rõ là remote operation.

---

# 83. Remote Call

395 đã định nghĩa:

```text id="h5n9bx"
timeout
retry
unknown result
idempotency
```

401 chỉ cung cấp transport/protocol substrate.

---

# 84. RPC Serialization

Typed request:

```text id="p3c7wd"
Request<T>
```

và response:

```text id="j8v2mf"
Response<T>
```

---

# 85. Zero-Copy RPC

Local transport có thể transfer ownership trực tiếp.

Remote transport bắt buộc serialize/copy theo protocol.

Không được giả vờ remote pointer.

---

# 86. Unix Domain Socket

Có thể transfer file descriptors/capabilities trên Unix-like systems.

Đây là OS/security capability transfer.

---

# 87. Capability Transfer

394 capability model phải được reuse.

Network capability ≠ arbitrary byte.

---

# 88. Service Discovery

Distributed engine 393 có service identity.

401 cung cấp transport discovery:

```text id="c5m8rz"
DNS
static endpoint
service registry
```

---

# 89. DNS

DNS là protocol/library:

```text id="x7q2mv"
resolve(name)
```

có caching/TTL semantics.

---

# 90. DNS Result

Address records:

```text id="n4k9sy"
A
AAAA
SRV
TXT
```

---

# 91. DNS Cache

Cache metadata:

```text id="j3w6pb"
expires_at
source
```

---

# 92. Name Resolution

Name resolution không nên bị coi là pure function vì:

```text id="q8v1dx"
network
cache
OS resolver
```

là effects.

---

# 93. Routing

High-level applications không cần trực tiếp manipulate routing table.

Systems programs có API explicit.

---

# 94. Network Interface

```text id="b5r9tk"
NetworkInterface
```

có:

```text id="m1x7qf"
name
index
addresses
MTU
flags
```

---

# 95. Network Device

Low-level:

```text id="u8c3zs"
NetworkDevice
```

có RX/TX queues.

---

# 96. RX/TX Rings

High-performance networking:

```text id="d6p2ny"
NIC
 ↓
RX ring
 ↓
PacketBuffer
```

và:

```text id="s9k4wv"
PacketBuffer
 ↓
TX ring
 ↓
NIC
```

---

# 97. Multi-Queue NIC

Mỗi queue có thể map vào worker/thread:

```text id="q3m8lf"
RX0 → Worker0
RX1 → Worker1
RX2 → Worker2
```

parallelism engine có thể optimize placement.

---

# 98. RSS

Receive Side Scaling có thể phân phối flow theo CPU.

Axiom semantics không được phụ thuộc CPU assignment.

---

# 99. Kernel Bypass

Có thể có backend:

```text id="f7w2xa"
DPDK
AF_XDP
io_uring
RDMA
```

nhưng đây là optional backend.

Không trở thành dependency của Core.

---

# 100. CompilerDB

Bổ sung:

```text id="h3v7zn"
NetworkDB
NetworkAddressDB
Ipv4DB
Ipv6DB
IpPrefixDB
MacAddressDB
PortDB
EndpointDB

SocketDB
SocketTypeDB
SocketOptionDB
SocketCapabilityDB
SocketLifecycleDB

TcpDB
TcpConnectionDB
TcpListenerDB
TcpStreamDB
TcpShutdownDB
TcpCongestionDB
TcpKeepAliveDB

UdpDB
UdpDatagramDB
UdpMulticastDB
UdpBroadcastDB

QuicDB
QuicConnectionDB
QuicStreamDB
QuicDatagramDB

NetworkStreamDB
NetworkDatagramDB
NetworkPacketDB
PacketBufferDB
PacketPoolDB
PacketRingDB
PacketMetadataDB

NetworkDmaDB
NetworkRegisteredBufferDB
NetworkZeroCopyDB
NetworkScatterGatherDB
NetworkBufferReuseDB

NetworkAsyncDB
NetworkPollDB
NetworkReadinessDB
NetworkCompletionDB
NetworkCancellationDB
NetworkTimeoutDB
NetworkDeadlineDB

NetworkBackpressureDB
NetworkQueueDB
NetworkFlowControlDB

PacketParseDB
PacketHeaderDB
PacketLayerDB
PacketViewDB
PacketMutViewDB
PacketValidationDB
PacketChecksumDB
PacketEndianDB
PacketWireLayoutDB
PacketFramingDB
PacketParserStateDB

ProtocolDB
ProtocolMessageDB
ProtocolCodecDB
ProtocolValidationDB
ProtocolFramingDB
ProtocolStreamingDB

HttpDB
HttpRequestDB
HttpResponseDB
HttpHeaderDB
HttpBodyDB
Http1DB
Http2DB
Http3DB

TlsDB
TlsConnectionDB
TlsSessionDB
TlsCertificateDB
TlsCredentialDB
TlsValidationDB

RpcDB
RpcClientDB
RpcServerDB
RpcMethodDB
RpcRequestDB
RpcResponseDB
RpcRetryDB
RpcTimeoutDB
RpcIdempotencyDB

DnsDB
DnsQueryDB
DnsRecordDB
DnsCacheDB
DnsTtlDB
NameResolutionDB

NetworkInterfaceDB
NetworkInterfaceAddressDB
NetworkRouteDB
NetworkNeighborDB
NetworkMtuDB

NetworkDeviceDB
NetworkQueueDeviceDB
NetworkRxRingDB
NetworkTxRingDB
NetworkRssDB
NetworkKernelBypassDB
NetworkRdmaDB
NetworkAfXdpDB

NetworkSecurityDB
NetworkCapabilityDB
NetworkAuthenticationDB
NetworkAuthorizationDB

NetworkSerializationDB
NetworkCompressionDB
NetworkDistributedDB

NetworkSimdDB
NetworkParallelDB
NetworkGpuDB

NetworkCostModelDB
NetworkOptimizationDB
NetworkVerificationDB
```

---

# 101. MIR

```text id="v6r3mp"
NET_ADDRESS_PARSE
NET_ADDRESS_COMPARE
NET_PREFIX_CONTAINS

SOCKET_CREATE
SOCKET_BIND
SOCKET_LISTEN
SOCKET_ACCEPT
SOCKET_CONNECT
SOCKET_CLOSE
SOCKET_SHUTDOWN
SOCKET_OPTION_GET
SOCKET_OPTION_SET

NET_READ
NET_WRITE
NET_READ_AT
NET_WRITE_AT

NET_SEND
NET_RECEIVE
NET_SEND_DATAGRAM
NET_RECEIVE_DATAGRAM

NET_POLL
NET_WAIT
NET_CANCEL

NET_BUFFER_CREATE
NET_BUFFER_VIEW
NET_BUFFER_MUT_VIEW
NET_BUFFER_REUSE

NET_RING_CREATE
NET_RING_PUSH
NET_RING_POP

NET_SCATTER_READ
NET_GATHER_WRITE

NET_DMA_REGISTER
NET_DMA_UNREGISTER
NET_DMA_SUBMIT

NET_PACKET_CREATE
NET_PACKET_PARSE
NET_PACKET_VALIDATE
NET_PACKET_VIEW
NET_PACKET_MUT_VIEW
NET_PACKET_CHECKSUM

NET_FRAME_BEGIN
NET_FRAME_END
NET_FRAME_LENGTH
NET_FRAME_DELIMITER

TCP_CONNECT
TCP_ACCEPT
TCP_READ
TCP_WRITE
TCP_SHUTDOWN

UDP_SEND
UDP_RECEIVE
UDP_JOIN_GROUP
UDP_LEAVE_GROUP

QUIC_CONNECT
QUIC_STREAM_OPEN
QUIC_STREAM_ACCEPT
QUIC_STREAM_READ
QUIC_STREAM_WRITE
QUIC_DATAGRAM_SEND
QUIC_DATAGRAM_RECEIVE

TLS_CONNECT
TLS_ACCEPT
TLS_HANDSHAKE
TLS_READ
TLS_WRITE
TLS_CLOSE

HTTP_REQUEST
HTTP_RESPONSE
HTTP_HEADER
HTTP_BODY_READ
HTTP_BODY_WRITE

RPC_CALL
RPC_SEND
RPC_RECEIVE
RPC_RETRY

DNS_RESOLVE
DNS_QUERY

NET_INTERFACE_ENUM
NET_INTERFACE_INFO

NET_RX_POLL
NET_TX_SUBMIT
NET_DEVICE_OPEN
NET_DEVICE_CLOSE
```

---

# 102. Proof System

```text id="a8n4yc"
NetworkAddressProof
EndpointProof
PortProof
IpPrefixProof

SocketOwnershipProof
SocketCapabilityProof
SocketLifecycleProof
SocketOptionProof

TcpStateProof
TcpStreamProof
TcpHalfCloseProof
TcpOwnershipProof

UdpDatagramProof
UdpOrderingProof
UdpMulticastProof

QuicConnectionProof
QuicStreamProof
QuicOrderingProof

NetworkBufferOwnershipProof
NetworkBufferLifetimeProof
NetworkBufferReuseProof
NetworkZeroCopyProof
NetworkScatterGatherProof

NetworkDmaProof
NetworkRegistrationProof
NetworkDmaLifetimeProof

NetworkAsyncProof
NetworkCancellationProof
NetworkDeadlineProof
NetworkCompletionProof
NetworkReadinessProof

NetworkBackpressureProof
NetworkFlowControlProof

PacketBoundsProof
PacketParseProof
PacketValidationProof
PacketChecksumProof
PacketEndianProof
PacketWireLayoutProof
PacketFramingProof

ProtocolEncodingProof
ProtocolDecodingProof
ProtocolStreamingProof
ProtocolValidationProof

HttpProtocolProof
HttpBodyLifetimeProof
HttpStreamProof

TlsCredentialProof
TlsCertificateProof
TlsValidationProof
TlsSessionProof

RpcOwnershipProof
RpcSerializationProof
RpcTimeoutProof
RpcRetryProof
RpcIdempotencyProof
RpcUnknownResultProof

DnsResolutionProof
DnsCacheProof
DnsTtlProof

NetworkInterfaceProof
NetworkRouteProof

NetworkDeviceProof
NetworkRxRingProof
NetworkTxRingProof
NetworkKernelBypassProof
NetworkRdmaProof

NetworkSecurityProof
NetworkCapabilityProof

NetworkSimdProof
NetworkParallelProof
NetworkCostModelProof
NetworkOptimizationProof
NetworkVerificationProof
```

---

# 103. Invariants

### `ANET-01`
Network address phải là typed value, không phải arbitrary string trong API typed.

### `ANET-02`
IPv4 và IPv6 phải là semantic types riêng.

### `ANET-03`
Endpoint identity phải phân biệt address và port.

### `ANET-04`
Socket ownership phải rõ ràng.

### `ANET-05`
Socket capability phải giới hạn authority.

### `ANET-06`
TCP phải có byte-stream semantics, không được tạo message boundary giả.

### `ANET-07`
UDP phải preserve datagram boundaries.

### `ANET-08`
UDP không được implicit guarantee ordering/reliability.

### `ANET-09`
QUIC ordering phải được hiểu theo từng stream.

### `ANET-10`
Connection và stream phải có identity/lifetime riêng.

### `ANET-11`
Async network operation không được implicit spawn task.

### `ANET-12`
Blocking network operation phải được compiler effect system nhận biết.

### `ANET-13`
Cancellation phải phân biệt requested/cancelled/completed/unknown.

### `ANET-14`
Network buffer view không được vượt lifetime của underlying buffer.

### `ANET-15`
Zero-copy chỉ được áp dụng khi ownership/storage/ABI proof hợp lệ.

### `ANET-16`
DMA buffer không được đồng thời bị CPU và device truy cập trái contract.

### `ANET-17`
Registered buffer không được unregister khi outstanding operation còn tồn tại.

### `ANET-18`
Scatter/gather không được làm thay đổi logical byte sequence.

### `ANET-19`
Network backpressure phải có boundedness semantics rõ ràng.

### `ANET-20`
Packet parser safe phải verify bounds trước khi access.

### `ANET-21`
Malformed packet phải tạo structured failure, không mặc định memory fault.

### `ANET-22`
Wire endianness phải explicit.

### `ANET-23`
Protocol structure layout phải phân biệt với native C/Axiom memory layout.

### `ANET-24`
Incremental parser phải hỗ trợ partial input mà không yêu cầu toàn message trong memory.

### `ANET-25`
TLS credential/key ownership phải tuân thủ Security Engine.

### `ANET-26`
RPC không được che giấu timeout/retry/remote failure như local function semantics.

### `ANET-27`
RPC retry chỉ được tự động khi idempotency contract cho phép.

### `ANET-28`
Kernel-bypass/RDMA backend không được trở thành Core dependency.

### `ANET-29`
Network optimization không được thay đổi protocol-observable ordering/data semantics.

### `ANET-30`
Chương trình không sử dụng Networking không được kéo theo network runtime bắt buộc.

---

# 104. Điểm quan trọng nhất của 401

401 tạo ra một abstraction stack rất mạnh:

```text id="4r7x2q"
Application
     │
     ▼
RPC / HTTP / Protocol
     │
     ▼
TLS / Compression
     │
     ▼
TCP / QUIC / UDP
     │
     ▼
Socket
     │
     ▼
Kernel I/O
     │
     ▼
DMA Buffer
     │
     ▼
NIC
```

nhưng **ownership model chỉ có một**.

Ví dụ high-level:

```text id="8j2f6m"
await client.send(data)
```

có thể cuối cùng trở thành:

```text id="n5x9qa"
Application Buffer
       ↓
owned NetworkBuffer
       ↓
registered DMA buffer
       ↓
TX ring
       ↓
NIC
```

và compiler/runtime có thể loại bỏ những copy trung gian không cần thiết.

Ngược lại, programmer viết packet-level code:

```text id="0s4h8v"
packet.ip().tcp().payload()
```

vẫn được compiler bảo vệ bằng:

```text id="j7k3dp"
bounds
alignment
ownership
lifetime
endianness
capability
```

---

## Một quyết định kiến trúc đáng chú ý

Đến đây Axiom đã có:

```text
Memory
   ↓
I/O
   ↓
Storage
   ↓
Network
   ↓
Database
   ↓
Distributed Systems
   ↓
Media
   ↓
GPU / ML
   ↓
GUI
```

Điều này cho thấy **không nên tiếp tục mở rộng Core language chỉ để hỗ trợ từng domain**.

Từ giai đoạn này, hướng đúng là giữ Core tương đối ổn định và xây **domain compiler infrastructure** phía trên nó.

Nói cách khác:

> **Axiom Core không cần biết HTTP, SQL, JPEG, CUDA, MIDI hay PostgreSQL. Nhưng compiler phải có đủ semantic machinery để các domain đó có thể trở thành zero-cost abstraction khi có thể.**

Đây cũng là tiền đề để các task tiếp theo chuyển dần từ “thêm domain” sang những phần lớn hơn như **package/module ecosystem, build system, plugin/ABI ecosystem, testing/profiling/debugging, compiler architecture, metaprogramming, language tooling và cuối cùng là self-hosting compiler**.