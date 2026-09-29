# BOOTSTRAP-392 — Axiom Network Protocol, Transport & Distributed Communication Engine

Sau **391 — Storage, Persistence & Durable Data**, bước tiếp theo hợp lý là hoàn thiện nửa còn lại của dataflow:

> **Axiom phải có mô hình giao tiếp mạng và distributed communication đủ mạnh để xây server, client, RPC, message broker, distributed database và cluster computing mà không cần một runtime mạng bắt buộc.**

Mục tiêu của 392 không phải tạo một “networking framework khổng lồ”, mà xây **semantic foundation** để các thư viện networking có thể tận dụng trực tiếp Ownership, Async, I/O, Serialization, Concurrency, GPU/dataflow và Storage đã có.

---

# 1. Tách 5 tầng

Axiom phải phân biệt:

```text
Application Protocol
        ↓
Message / Serialization
        ↓
Session
        ↓
Transport
        ↓
Network
```

Ví dụ:

```text
HTTP
 ↓
request/response
 ↓
TCP/TLS session
 ↓
TCP
 ↓
IP
```

Compiler không được nhập nhằng các tầng này.

---

# 2. Network Address

Core semantic model:

```text
NetworkAddress
```

có thể đại diện:

```text
IPv4
IPv6
Unix domain
Bluetooth
custom transport
```

nhưng địa chỉ mạng không phải raw pointer và không có quan hệ với memory address.

---

# 3. Endpoint

Phân biệt:

```text
Address
Endpoint
Connection
Listener
Session
```

Ví dụ:

```text
Endpoint = address + protocol + transport configuration
```

---

# 4. Connection

Connection là logical communication resource.

Ownership:

```text
Connection
```

là owning resource.

Copy mặc định không được tạo thêm connection.

Move chuyển quyền sở hữu.

Drop đóng connection theo contract của API.

---

# 5. Listener

Server:

```text
Listener
    ↓
accept()
    ↓
Connection
```

`accept()` không được tự spawn thread.

Nó chỉ tạo connection.

---

# 6. Async Connection

Ví dụ semantic:

```text
async fn connect(endpoint) -> Result<Connection, Error>
```

chỉ tạo Future.

Không tự chạy.

Executor quyết định execution.

---

# 7. Socket

390 đã có socket I/O primitive.

392 đặt semantic networking layer lên trên:

```text
Socket
 ↓
Transport
 ↓
Connection
```

Socket không nhất thiết tương đương connection.

UDP là ví dụ rõ ràng.

---

# 8. Byte Stream

TCP:

```text
ByteStream
```

không có message boundary.

Nếu application cần message:

```text
FrameCodec
```

phải định nghĩa framing.

---

# 9. Datagram

UDP:

```text
Datagram<T>
```

giữ boundary của packet.

Không được biến datagram thành byte stream một cách ngầm định.

---

# 10. Framing

Protocol có thể dùng:

```text
length-prefix
delimiter
fixed-size
varint
chunked
record
```

Compiler/library phải biết framing semantics.

---

# 11. Message

Message là logical value:

```text
Message<T>
```

nó khác byte buffer.

```text
Message<T>
   ↓ encode
ByteBuffer
   ↓ transport
network
```

---

# 12. Zero-Copy Message

Nếu ownership có thể chuyển:

```text
Buffer<T>
      ↓
send()
```

thì không cần copy.

Sau successful send, ownership semantics phải xác định rõ:

```text
sender → transport
```

hoặc transport chỉ mượn buffer trong thời gian operation.

---

# 13. Failed Send

Nếu send thất bại:

```text
send(buffer) -> Result<(), Buffer>
```

có thể trả ownership lại cho caller.

Không được làm mất dữ liệu chỉ vì API báo lỗi.

---

# 14. Receive

Có hai semantic dạng:

```text
receive() -> owned message
```

và:

```text
receive_into(buffer)
```

Cái thứ hai cho phép caller kiểm soát storage.

---

# 15. Receive View

Nếu transport/backend cung cấp buffer:

```text
recv() -> view<u8>
```

thì view lifetime phải gắn với buffer ownership.

Không được trả dangling view.

---

# 16. Backpressure

Networking phải tích hợp với 390:

```text
producer
 ↓
network buffer
 ↓
consumer
```

Khi consumer chậm:

```text
backpressure
```

không được tự động tạo vô hạn queue.

---

# 17. Bounded Network Buffer

API có thể khai báo:

```text
capacity
high_watermark
low_watermark
```

để kiểm soát memory.

Điều này đặc biệt quan trọng với server.

---

# 18. Flow Control

392 phân biệt:

```text
Application Backpressure
Transport Flow Control
Congestion Control
```

Chúng không phải cùng một khái niệm.

---

# 19. Timeout

Network operation có thể có:

```text
deadline
timeout
cancellation
```

Ví dụ:

```text
await receive(deadline)
```

Timeout không đồng nghĩa connection failure.

---

# 20. Cancellation

Cancellation phải tuân theo Async model:

```text
cancel request
    ↓
operation observes cancellation
    ↓
cleanup
```

Không forcibly kill underlying OS operation nếu backend không hỗ trợ.

---

# 21. Retry

Không phải network error nào cũng retry được.

Compiler/library phải phân biệt:

```text
retryable
non_retryable
unknown
```

và application phải xác định idempotency khi cần.

---

# 22. Idempotency

Ví dụ:

```text
GET
```

thường có semantic khác:

```text
create_order()
```

Network layer không được tự suy đoán rằng mọi request có thể retry.

---

# 23. Connection State

Connection state:

```text
CREATED
CONNECTING
CONNECTED
CLOSING
CLOSED
FAILED
```

UDP có semantics khác TCP.

---

# 24. Half Close

TCP có thể có:

```text
shutdown_read
shutdown_write
```

Đây là semantic khác với:

```text
close
```

---

# 25. Listener Lifecycle

```text
bind
listen
accept
close
```

mỗi operation có ownership/error semantics riêng.

---

# 26. TLS / Secure Transport

TLS không nên là một tính chất “ẩn” của socket.

Có thể có:

```text
Transport<T>
```

hoặc:

```text
SecureSession
```

để biểu diễn:

```text
TCP
 ↓
TLS
 ↓
Application protocol
```

---

# 27. Encryption Boundary

Encryption:

```text
application data
 ↓
serialization
 ↓
framing
 ↓
TLS
 ↓
transport
```

không được tự động trộn với application serialization.

---

# 28. Authentication

Authentication là protocol/session semantic:

```text
Unauthenticated
Authenticated<Identity>
```

Có thể sử dụng typestate/generic abstraction thay vì runtime object hierarchy.

---

# 29. Authorization

Authentication ≠ authorization.

Một connection có identity không đồng nghĩa được phép thực hiện mọi operation.

---

# 30. Identity

Distributed identity:

```text
NodeId
PeerId
SessionId
RequestId
CorrelationId
```

khác nhau.

Không dùng một ID cho tất cả.

---

# 31. Request/Response

Generic RPC foundation:

```text
Request<Req>
Response<Resp>
```

có:

```text
RequestId
CorrelationId
Deadline
Cancellation
```

---

# 32. RPC

RPC có thể được xây từ:

```text
serialization
+
framing
+
connection
+
async
```

Không cần Core có keyword `rpc`.

---

# 33. Static RPC

Nếu interface biết compile-time:

```text
trait UserService {
    fn get(id: u64) -> Result<User>
}
```

comptime có thể generate:

```text
client stub
server dispatcher
codec
schema
```

---

# 34. Dynamic RPC

Dynamic protocol có thể sử dụng:

```text
DynamicSchema
DynamicMessage
```

đã có từ 391.

Đây là explicit runtime capability.

---

# 35. RPC Dispatch

Server dispatcher có thể compile thành:

```text
Request decode
 → method ID
 → direct function call
 → encode response
```

không cần reflection runtime.

---

# 36. Protocol ID

Method nên có stable protocol identity:

```text
method_id
```

không phụ thuộc memory address hoặc compiler-generated symbol name.

---

# 37. Versioning

RPC interface evolution:

```text
V1
V2
```

phải sử dụng schema compatibility của 391.

---

# 38. Streaming RPC

Hỗ trợ:

```text
Unary
ServerStream
ClientStream
BidirectionalStream
```

đều có thể map vào `Stream<T>`.

---

# 39. Message Ownership

Streaming message:

```text
Stream<Message<T>>
```

có thể transfer ownership giữa producer/consumer.

Điều này cho phép zero-copy pipeline.

---

# 40. Network Pipeline

Ví dụ:

```text
Socket
 ↓
Frame
 ↓
Decode
 ↓
Validate
 ↓
Transform
 ↓
Compute
 ↓
Encode
 ↓
Socket
```

392 phải cho phép compiler/runtime fuse những phần có thể fuse.

---

# 41. Network → Tensor

Một pipeline AI:

```text
Network
 ↓
compressed buffer
 ↓
decode
 ↓
Tensor
 ↓
GPU
```

không nên bắt buộc:

```text
network
 → temporary object
 → CPU tensor copy
 → GPU copy
```

nếu storage contracts cho phép loại bỏ các bước đó.

---

# 42. Network → Storage

Server ingest:

```text
network
 ↓
decode
 ↓
persistent storage
```

có thể stream trực tiếp vào append log hoặc chunk store.

---

# 43. Storage → Network

Download:

```text
Mapped/Chunked storage
 ↓
buffer view
 ↓
network send
```

có thể sử dụng scatter/gather và zero-copy.

---

# 44. Scatter/Gather

Network API nên hỗ trợ:

```text
send([buffer1, buffer2, buffer3])
```

mà không cần concatenate.

---

# 45. Framed Scatter/Gather

Header:

```text
[length][type][payload]
```

có thể gửi:

```text
header buffer
+
payload buffer
```

mà không copy payload.

---

# 46. Batch Receive

Server hiệu năng cao cần:

```text
receive_batch()
```

và:

```text
send_batch()
```

để giảm syscall/queue overhead.

---

# 47. Packet Batch

UDP/high-performance networking có thể sử dụng:

```text
PacketBatch
```

với SIMD/parallel processing.

---

# 48. Polling

Networking backend có thể cung cấp:

```text
poll
event
completion
```

nhưng đây là backend detail.

Application semantic chỉ cần:

```text
await
```

hoặc synchronous operation.

---

# 49. Backend Independence

392 không được phụ thuộc vào:

```text
epoll
kqueue
IOCP
io_uring
Windows RIO
DPDK
```

Các backend là implementation.

---

# 50. Kernel Bypass

High-performance networking có thể có:

```text
UserSpaceTransport
```

hoặc backend riêng.

Không thay đổi application-level semantics.

---

# 51. Shared Memory Transport

Trong cùng machine:

```text
Process A
   ↓
SharedMemory
   ↓
Process B
```

có thể implement cùng `Transport<T>` abstraction.

Nhưng consistency/ownership contract phải khác network socket.

---

# 52. IPC

392 nên hỗ trợ semantic:

```text
UnixSocket
NamedPipe
SharedMemory
MessageQueue
```

nhưng OS implementation nằm ngoài Core.

---

# 53. Local vs Remote

Một abstraction có thể có:

```text
LocalTransport
RemoteTransport
```

Nhưng compiler **không được giả định remote call có local semantics**.

Remote có:

```text
latency
failure
partial completion
serialization
```

---

# 54. Distributed Failure

Distributed system có nhiều trạng thái:

```text
success
timeout
connection_lost
peer_failed
protocol_error
authentication_failed
overloaded
unknown_result
```

Đặc biệt:

> `timeout` không đồng nghĩa operation chưa xảy ra.

---

# 55. At-Least / At-Most / Exactly Once

Messaging abstraction phải phân biệt:

```text
AtMostOnce
AtLeastOnce
EffectivelyOnce
```

Không tuyên bố “exactly once” nếu backend không thể đảm bảo.

---

# 56. Delivery Semantics

Message queue có thể định nghĩa:

```text
ordering
delivery
acknowledgement
redelivery
durability
```

rõ ràng.

---

# 57. Ordering

Không mặc định global ordering.

Có thể:

```text
per_connection
per_stream
per_partition
per_key
global
```

tùy protocol.

---

# 58. Acknowledgement

ACK là protocol-level event.

Không phải memory fence.

Không được nhập hai khái niệm.

---

# 59. Distributed Synchronization

Network message có thể tạo:

```text
logical happens-before
```

ở distributed-system layer.

Nhưng **không được mở rộng local Axiom memory model một cách sai lệch**.

Local:

```text
HappensBefore
```

và distributed:

```text
CausalOrder
```

là hai semantic systems khác nhau.

---

# 60. Causal Ordering

Distributed messaging có thể theo dõi:

```text
RequestId
TraceId
LogicalClock
VectorClock
```

nếu application yêu cầu.

---

# 61. Clock

Wall clock và logical clock phải tách biệt:

```text
Timestamp
LogicalTime
```

Không dùng timestamp hệ thống để suy luận causal order.

---

# 62. Distributed Transaction

392 chỉ cung cấp communication foundation.

Các cơ chế:

```text
2PC
3PC
Saga
Consensus
Raft
Paxos
```

là library/application layer.

Không đưa chúng vào Core.

---

# 63. Consensus

Node abstraction có thể hỗ trợ:

```text
NodeId
Term
LogIndex
Vote
Append
Commit
```

nhưng đây là protocol implementation.

---

# 64. Distributed Actor

Actor có thể xây trên:

```text
Task
Channel
NetworkTransport
Message
```

không cần Actor primitive trong Core.

---

# 65. Service Discovery

Service endpoint có thể được resolve động:

```text
ServiceName
 → EndpointSet
```

đây là runtime/library functionality.

---

# 66. Load Balancing

Có thể chọn:

```text
round_robin
least_load
hash
consistent_hash
locality
```

nhưng policy không được implicit trong network primitive.

---

# 67. Connection Pool

```text
ConnectionPool<T>
```

là library abstraction.

Ownership của connection phải rõ:

```text
pool owns connection
borrower temporarily owns capability
```

---

# 68. Pool + Async

Connection lease không được sống qua `.await` nếu backend không cho phép.

Compiler kiểm tra giống các capability khác.

---

# 69. Reentrancy

Network callback có thể re-enter application.

Effect/reentrancy contracts phải rõ.

---

# 70. Network Security

Compiler không tự biến network API thành secure API.

Security contracts có thể bao gồm:

```text
authenticated
encrypted
integrity_protected
peer_verified
```

để type/system tooling kiểm tra.

---

# 71. FFI

Foreign networking APIs phải khai báo:

```text
ownership
blocking
thread safety
async behavior
buffer lifetime
callback lifetime
ABI
```

theo FFI engine 326.

---

# 72. Native API Optimization

Trên Windows:

```text
IOCP
```

Linux:

```text
io_uring
epoll
```

macOS:

```text
kqueue
```

có thể được backend lựa chọn.

Application code không phải thay đổi semantic model.

---

# 73. Compiler Network Optimization

Compiler có thể:

```text
inline codec
specialize serialization
eliminate temporary buffer
fuse decode + validation
fuse encode + gather
reuse receive buffers
batch operations
```

nếu proof cho phép.

---

# 74. Protocol Specialization

Nếu protocol schema compile-time known:

```text
decode<RequestV3>
```

có thể trở thành trực tiếp:

```text
bounds checks
loads
byte swaps
validation
construct value
```

thay vì generic reflection parser.

---

# 75. Compile-Time Protocol Generation

Comptime có thể tạo:

```text
Codec
Schema
ClientStub
ServerDispatcher
Validation
VersionMigration
```

từ một protocol definition.

Generated code phải quay lại pipeline:

```text
HIR
→ type checking
→ ownership
→ effect
→ MIR
→ verification
```

---

# 76. Protocol Description

Không nhất thiết tạo DSL riêng.

Axiom có thể sử dụng:

```text
struct
enum
trait
attributes
comptime
```

để mô tả protocol.

Điều này giữ Core nhỏ hơn.

---

# 77. Network Effect

Effect system bổ sung:

```text
NETWORK_CONNECT
NETWORK_ACCEPT
NETWORK_SEND
NETWORK_RECEIVE
NETWORK_CLOSE
NETWORK_TIMEOUT
NETWORK_DNS
NETWORK_TLS
NETWORK_IPC
```

Compiler có thể dùng chúng cho:

- async legality;
- comptime restriction;
- kernel restriction;
- deterministic build;
- security analysis.

---

# 78. Blocking

Network call phải khai báo:

```text
NONBLOCKING
MAY_BLOCK
ASYNC
```

Không được để compiler đoán từ tên hàm.

---

# 79. Realtime

Realtime code có thể yêu cầu:

```text
@realtime
```

và cấm:

```text
unbounded allocation
blocking network call
unbounded retry
```

nếu profile định nghĩa như vậy.

---

# 80. Network Cost Model

Compiler/runtime có thể tối ưu theo:

```text
latency
bandwidth
syscall cost
copy cost
serialization cost
connection setup cost
packet size
batch size
CPU cost
GPU transfer cost
```

---

# 81. Adaptive Transport

Một logical stream có thể lựa chọn:

```text
TCP
QUIC
UDP
shared memory
```

nhưng chỉ khi chúng thỏa cùng semantic contract.

Không được thay đổi observable ordering/delivery guarantees.

---

# 82. QUIC-like Transport

Transport abstraction nên đủ expressive cho:

```text
multiplexed streams
independent stream ordering
connection migration
datagrams
flow control
```

mà không hard-code QUIC.

---

# 83. Multiplexed Session

Một connection có thể chứa:

```text
Session
 ├── Stream A
 ├── Stream B
 ├── Stream C
```

Mỗi stream có flow-control/order semantics riêng.

---

# 84. Connection Migration

Nếu transport hỗ trợ migration:

```text
Connection identity
```

không được phụ thuộc vào physical socket endpoint.

---

# 85. Network Handle

Tương tự persistent handle:

```text
ConnectionId
SessionId
StreamId
```

là logical identity.

Không phải raw OS handle.

---

# 86. Resource Lifetime

Compiler phải biết:

```text
Listener
  owns OS resource

Connection
  owns transport resource

Stream
  may own logical subresource
```

Drop hierarchy phải deterministic.

---

# 87. Cleanup

Nếu:

```text
Connection
 ├── Stream
 └── BufferView
```

thì không được close connection khi live capability vẫn yêu cầu resource hợp lệ, trừ khi API contract định nghĩa invalidation rõ ràng.

---

# 88. Async Drop

Không tạo `AsyncDrop`.

Nếu close cần await:

```text
await connection.shutdown()
```

là explicit operation.

Sau đó:

```text
drop(connection)
```

chỉ thực hiện synchronous cleanup còn lại.

---

# 89. Graceful Shutdown

Phân biệt:

```text
abort
shutdown
graceful_shutdown
```

Graceful shutdown có thể chờ flush/send completion.

---

# 90. Server Architecture

Một server Axiom điển hình có thể trở thành:

```text
Listener
   ↓
Accept
   ↓
Task
   ↓
Frame
   ↓
Decode
   ↓
Handler
   ↓
Encode
   ↓
Send
```

Compiler có thể tối ưu từng bước nhưng không thay đổi semantic boundary.

---

# 91. High-Performance Server

Có thể:

```text
NIC
 ↓
DMA buffer
 ↓
kernel/network backend
 ↓
Axiom Buffer
 ↓
zero-copy decode
 ↓
SIMD validation
 ↓
GPU compute
 ↓
scatter/gather send
```

Đây là nơi 390 + 391 + 392 thực sự kết hợp.

---

# 92. CompilerDB

Bổ sung:

```text
NetworkDB
NetworkAddressDB
NetworkEndpointDB
NetworkIdentityDB

TransportDB
TransportTypeDB
TransportBackendDB
TransportCapabilityDB
TransportSecurityDB
TransportCostModelDB

SocketDB
SocketOptionDB
SocketStateDB
ListenerDB
ConnectionDB
ConnectionStateDB
ConnectionPoolDB

StreamDB
NetworkStreamDB
DatagramDB
PacketDB
PacketBatchDB
FrameDB
FramingDB

NetworkBufferDB
NetworkBufferViewDB
NetworkBufferReuseDB
NetworkZeroCopyDB
NetworkScatterGatherDB
NetworkBatchDB

FlowControlDB
BackpressureDB
CongestionDB

NetworkTimeoutDB
NetworkDeadlineDB
NetworkCancellationDB
NetworkRetryDB
NetworkIdempotencyDB

TlsDB
SecureTransportDB
AuthenticationDB
AuthorizationDB
PeerIdentityDB

SessionDB
SessionStateDB
MultiplexedSessionDB
NetworkSubstreamDB

RpcDB
RpcMethodDB
RpcRequestDB
RpcResponseDB
RpcDispatcherDB
RpcClientStubDB
RpcServerStubDB
RpcStreamingDB

ProtocolDB
ProtocolSchemaDB
ProtocolVersionDB
ProtocolCompatibilityDB
ProtocolCodecDB
ProtocolFramingDB
ProtocolValidationDB

MessageDB
MessageOwnershipDB
MessageDeliveryDB
MessageOrderingDB
MessageAckDB
MessageRetryDB
MessageDurabilityDB

IpcDB
UnixSocketDB
NamedPipeDB
SharedMemoryTransportDB
LocalTransportDB
RemoteTransportDB

DistributedDB
NodeDB
PeerDB
NodeDiscoveryDB
ServiceDiscoveryDB
DistributedIdentityDB
RequestCorrelationDB
CausalOrderDB
LogicalClockDB

NetworkPipelineDB
NetworkDecodeDB
NetworkEncodeDB
NetworkFusionDB
NetworkCopyEliminationDB
NetworkBufferOptimizationDB

NetworkSecurityDB
NetworkIntegrityDB
NetworkThreatDB

NetworkCostModelDB
NetworkOptimizationDB
NetworkProofDB
NetworkVerificationDB
```

---

# 93. MIR

Các operation mới:

```text
NET_RESOLVE
NET_BIND
NET_LISTEN
NET_ACCEPT
NET_CONNECT

NET_CLOSE
NET_SHUTDOWN_READ
NET_SHUTDOWN_WRITE
NET_GRACEFUL_SHUTDOWN

NET_SEND
NET_RECEIVE
NET_SEND_BATCH
NET_RECEIVE_BATCH

NET_SEND_DATAGRAM
NET_RECEIVE_DATAGRAM

NET_SEND_SCATTER
NET_RECEIVE_GATHER

NET_FRAME
NET_UNFRAME

NET_SESSION_OPEN
NET_SESSION_CLOSE
NET_STREAM_OPEN
NET_STREAM_CLOSE

NET_FLOW_CONTROL
NET_BACKPRESSURE

NET_TIMEOUT
NET_DEADLINE
NET_CANCEL

NET_TLS_HANDSHAKE
NET_AUTHENTICATE
NET_AUTHORIZE

NET_ENCODE_MESSAGE
NET_DECODE_MESSAGE

NET_RPC_REQUEST
NET_RPC_RESPONSE
NET_RPC_DISPATCH

NET_SERVICE_RESOLVE
NET_PEER_DISCOVER

NET_SHARED_MEMORY_CONNECT
NET_LOCAL_CONNECT

NET_BUFFER_REGISTER
NET_BUFFER_REUSE

NET_BATCH_BEGIN
NET_BATCH_END
```

---

# 94. Proof System

```text
NetworkAddressProof
EndpointProof
ConnectionOwnershipProof
ListenerOwnershipProof

NetworkBufferLifetimeProof
NetworkBufferBoundsProof
NetworkBufferAlignmentProof
NetworkZeroCopyProof
NetworkScatterGatherProof

FrameBoundaryProof
ProtocolDecodeProof
ProtocolEncodeProof
ProtocolSchemaProof
ProtocolCompatibilityProof

NetworkOrderingProof
NetworkDeliveryProof
NetworkRetryProof
NetworkIdempotencyProof

NetworkBackpressureProof
FlowControlProof
CancellationProof
TimeoutProof

TlsProof
AuthenticationProof
AuthorizationProof

SessionLifetimeProof
StreamLifetimeProof
MultiplexingProof

RpcSchemaProof
RpcRequestProof
RpcResponseProof
RpcDispatchProof
RpcStreamingProof

NetworkConcurrencyProof
NetworkRaceProof

NetworkStorageProof
NetworkDeviceProof
NetworkDmaProof

NetworkAsyncProof
NetworkBlockingProof
NetworkRealtimeProof

DistributedIdentityProof
CausalOrderProof
LogicalClockProof

NetworkOptimizationProof
NetworkCopyEliminationProof
NetworkFusionProof
NetworkBackendProof
NetworkVerificationProof
```

---

# 95. Invariants

### `ANET-01`
Network address không được đồng nhất với memory address.

### `ANET-02`
Endpoint, Connection, Listener và Stream phải có semantic identity riêng.

### `ANET-03`
Connection là owning resource nếu API contract xác định ownership.

### `ANET-04`
Copy một owning Connection không được tạo implicit duplicate resource.

### `ANET-05`
Move Connection chuyển ownership, không tạo thêm connection.

### `ANET-06`
Drop Connection phải thực hiện cleanup theo connection contract.

### `ANET-07`
TCP ByteStream không được tự tạo message boundaries.

### `ANET-08`
Datagram phải bảo toàn packet/message boundary.

### `ANET-09`
Framing phải được định nghĩa explicit.

### `ANET-10`
Failed send phải bảo toàn ownership của payload theo API contract.

### `ANET-11`
Network view không được sống lâu hơn source buffer.

### `ANET-12`
Zero-copy chỉ hợp lệ khi ownership/lifetime/layout/alignment/storage contract cho phép.

### `ANET-13`
Backpressure không được tự động tạo unbounded memory growth.

### `ANET-14`
Timeout không được được diễn giải tự động thành operation chưa xảy ra.

### `ANET-15`
Retry chỉ hợp lệ khi operation và protocol semantics cho phép.

### `ANET-16`
Network ordering không được mặc định là global ordering.

### `ANET-17`
ACK không được đồng nhất với local memory synchronization.

### `ANET-18`
Remote execution không được có local-call semantics một cách ngầm định.

### `ANET-19`
Authentication không đồng nghĩa authorization.

### `ANET-20`
TLS/security phải là explicit protocol/transport capability.

### `ANET-21`
Async network operation không được implicit spawn thread/task.

### `ANET-22`
Network operation có khả năng blocking phải được effect system biểu diễn.

### `ANET-23`
Async network capability không được vượt `.await` nếu contract không cho phép.

### `ANET-24`
Generated protocol/RPC code phải đi qua normal Axiom verification pipeline.

### `ANET-25`
Protocol versioning không được phụ thuộc compiler internal layout.

### `ANET-26`
Logical network identity không được phụ thuộc raw OS handle.

### `ANET-27`
Distributed causal order không được làm thay đổi local Axiom memory model.

### `ANET-28`
Transport backend có thể thay đổi nếu observable protocol semantics được bảo toàn.

### `ANET-29`
Network optimization không được thay đổi observable delivery, ordering, ownership hoặc failure semantics.

### `ANET-30`
Nếu chương trình không dùng networking, compiler không được kéo theo network runtime bắt buộc.

---

## 96. Kết quả kiến trúc sau 392

Axiom hiện có thể mô hình hóa một data path rất mạnh:

```text
                 ┌─────────────┐
                 │   Network   │
                 └──────┬──────┘
                        │
                  zero-copy
                        │
                 ┌──────▼──────┐
                 │    Buffer   │
                 └──────┬──────┘
                        │
                    Decode
                        │
                 ┌──────▼──────┐
                 │    Value    │
                 └──────┬──────┘
                        │
          ┌─────────────┼─────────────┐
          ↓             ↓             ↓
        CPU           GPU         Storage
       SIMD          Tensor        mmap
          │             │             │
          └─────────────┼─────────────┘
                        ↓
                   Encode/Store
```

Điểm quan trọng nhất là **compiler không cần biết đây là “web programming”, “AI programming” hay “database programming”**.

Nó chỉ cần hiểu các semantic primitive:

```text
ownership
capability
effect
async
memory
layout
buffer
serialization
storage
transport
```

và từ đó tối ưu xuyên tầng.

Đây chính là hướng phù hợp với mục tiêu ban đầu của Axiom: **source-level abstraction cao, nhưng machine-level abstraction không bị ép phải trả giá nếu compiler chứng minh được rằng abstraction có thể bị xóa.**