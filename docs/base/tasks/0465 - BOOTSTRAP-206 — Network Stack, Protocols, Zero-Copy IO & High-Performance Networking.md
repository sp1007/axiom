# BOOTSTRAP-206 — Network Stack, Protocols, Zero-Copy I/O & High-Performance Networking

**TRẠNG THÁI: FROZEN / COMPLETED**

> **Axiom Network phải phục vụ được cả `HTTP client/server` đơn giản lẫn kernel-bypass/RDMA/zero-copy networking, nhưng tất cả đều phải dùng chung Ownership + Capability + Async + Resource + Effect semantics.**

BOOTSTRAP-202 đã khóa **distributed/networking architecture** ở cấp hệ thống.  
BOOTSTRAP-206 này đi sâu vào **network stack và I/O implementation contract**, vì đây là phần cần thiết để biến kiến trúc đó thành một hệ thống networking thực sự hoàn chỉnh.

---

# 206.1. Phân tầng Network

Kiến trúc:

```text
Application
    │
Protocol
    │
Session
    │
Transport
    │
Socket
    │
Async I/O
    │
OS / Kernel / Driver
    │
NIC / Hardware
```

Ví dụ:

```text
HTTP/3
  ↓
QUIC
  ↓
UDP
  ↓
Socket
  ↓
io_uring / IOCP / kqueue / epoll
  ↓
Kernel
  ↓
NIC
```

Không một tầng nào bắt buộc phải được sử dụng nếu ứng dụng cần đi thấp hơn.

---

# 206.2. Network không phải Core

Core chỉ cần:

```text
Ownership
Capability
Async
Future
Send
Share
Effect
Execution Domain
Storage Domain
Resource
```

Network nằm trên đó.

---

# 206.3. Endpoint

Endpoint là logical network address:

```text
Endpoint
```

có thể bao gồm:

```text
Scheme
Address
Port
Protocol
```

Không đồng nhất endpoint với socket.

```text
Endpoint ≠ Socket
```

---

# 206.4. IP address

Tách:

```text
IPv4
IPv6
```

thành type riêng.

Không dùng `u32` làm API public mặc định.

---

# 206.5. Port

```text
Port
```

là type riêng để tránh truyền nhầm integer.

---

# 206.6. Socket là OS resource

```text
TcpSocket
UdpSocket
UnixSocket
```

đều là owned resources.

Ownership:

```text
Socket
  ↓ move
new owner
```

---

# 206.7. Socket Drop

`Drop(socket)`:

```text
release OS resource
```

nhưng không có nghĩa:

```text
protocol shutdown
graceful close
flush remote data
```

Các semantics đó phải explicit.

---

# 206.8. TCP

TCP abstraction:

```text
TcpListener
TcpStream
```

---

# 206.9. TCP connection state

Conceptual state machine:

```text
Created
 ↓
Connecting
 ↓
Connected
 ↓
Closing
 ↓
Closed
```

Error state có thể xuất hiện ở mọi transition phù hợp.

---

# 206.10. TCP stream không phải message stream

TCP cung cấp:

```text
ordered byte stream
```

không cung cấp:

```text
message boundaries
```

Axiom API không được che giấu điều này.

---

# 206.11. Framing

Application protocol phải xây framing:

```text
LengthPrefix
Delimiter
FixedSize
Chunked
ProtocolSpecific
```

---

# 206.12. TCP half-close

Hỗ trợ:

```text
shutdown_read()
shutdown_write()
```

độc lập.

---

# 206.13. TCP backpressure

`write()` thành công không đồng nghĩa peer đã xử lý dữ liệu.

Phân biệt:

```text
accepted by application
accepted by socket
sent to kernel
transmitted
acknowledged
processed by peer
```

---

# 206.14. TCP zero-copy

API có thể hỗ trợ:

```text
Buffer
   ↓ move
pending send
   ↓
kernel/NIC
   ↓
completion
```

Buffer không được giải phóng trước completion.

---

# 206.15. Vectored I/O

Hỗ trợ:

```text
IoSlice
IoSliceMut
```

và:

```text
readv
writev
```

Ownership/capability của từng region vẫn được verifier kiểm tra.

---

# 206.16. Scatter/Gather

Ví dụ:

```text
Header
Body
Trailer
```

có thể gửi mà không cần concatenate.

```text
[Header] [Body] [Trailer]
       ↓
    writev()
```

---

# 206.17. UDP

```text
UdpSocket
```

cung cấp datagram semantics.

Không đảm bảo:

```text
delivery
ordering
uniqueness
```

---

# 206.18. UDP packet ownership

Received packet có thể trả:

```text
PacketBuffer
```

hoặc:

```text
view<u8>
```

nhưng view không được sống lâu hơn buffer/storage backing it.

---

# 206.19. UDP zero-copy

NIC/kernel-backed buffer có thể được expose dưới dạng:

```text
NetworkBuffer
NetworkView
```

với explicit completion/lifetime.

---

# 206.20. Multicast

Library/system layer:

```text
join_multicast()
leave_multicast()
```

Không đưa multicast vào Core.

---

# 206.21. Broadcast

Broadcast là transport/platform capability.

Không mặc định mọi socket đều hỗ trợ.

---

# 206.22. Unix domain socket

Hỗ trợ:

```text
UnixStream
UnixDatagram
```

và platform equivalent.

---

# 206.23. Windows named pipe

Windows IPC:

```text
NamedPipe
```

là resource riêng, không giả làm TCP socket.

---

# 206.24. QUIC

QUIC có:

```text
QuicConnection
QuicStream
QuicDatagram
```

---

# 206.25. QUIC stream

Một connection có nhiều independent streams:

```text
Connection
 ├── Stream 1
 ├── Stream 2
 ├── Stream 3
 └── ...
```

Stream ownership độc lập về mặt logical API.

---

# 206.26. QUIC connection lifetime

Stream không được outlive connection nếu implementation contract yêu cầu connection backing.

Compiler/library dependency tracking phải giữ connection alive.

---

# 206.27. QUIC cancellation

Cancel một stream:

```text
stream.cancel()
```

không mặc định đóng toàn connection.

---

# 206.28. TLS

TLS là protocol/security library.

Không phải Core primitive.

```text
TcpStream
   ↓
TlsStream
```

---

# 206.29. TLS ownership

TLS session sở hữu cryptographic state.

Private keys/secrets phải có explicit ownership và sensitive-data policy.

---

# 206.30. TLS verification

Certificate verification là security policy.

Không mặc định:

```text
accept any certificate
```

trong high-level secure API.

---

# 206.31. TLS key material

Không implicit copy private key.

Nếu type không `Copy`, chuyển key phải là Move hoặc explicit Clone.

---

# 206.32. DNS

DNS API:

```text
resolve(host)
```

có thể trả:

```text
Vec<IpAddress>
```

và có TTL/cache metadata.

---

# 206.33. DNS async

Resolution có thể trả Future:

```text
resolve_async()
```

Không block executor worker nếu backend là asynchronous.

---

# 206.34. DNS cache

Cache là library/storage abstraction.

Không đưa global DNS cache vào runtime bắt buộc.

---

# 206.35. HTTP layer

HTTP:

```text
HttpRequest
HttpResponse
Headers
Body
```

là library types.

---

# 206.36. HTTP body streaming

Không bắt buộc:

```text
Body = Vec<u8>
```

Có thể:

```text
BodyStream
```

để xử lý file/large payload mà không load toàn bộ RAM.

---

# 206.37. HTTP request body ownership

Request body có thể là:

```text
OwnedBuffer
Stream
File
Generator
```

nhưng semantics ownership phải rõ.

---

# 206.38. HTTP response body

Response có thể:

```text
return buffer
return stream
return file-backed stream
```

Compiler không ép materialize toàn bộ response.

---

# 206.39. HTTP/1.1

Hỗ trợ:

- persistent connections
- pipelining theo compatibility requirements
- chunked transfer
- compression
- trailers

ở library level.

---

# 206.40. HTTP/2

HTTP/2 cần multiplex:

```text
Connection
 ├── Stream A
 ├── Stream B
 └── Stream C
```

và flow control.

---

# 206.41. HTTP/3

HTTP/3 chạy trên:

```text
HTTP/3
 ↓
QUIC
 ↓
UDP
```

Không cần một HTTP-specific transport primitive trong Core.

---

# 206.42. WebSocket

WebSocket:

```text
HttpUpgrade
 ↓
WebSocket
```

có message framing.

---

# 206.43. WebSocket message

Phân biệt:

```text
TextMessage
BinaryMessage
Ping
Pong
Close
```

---

# 206.44. RPC

RPC layer xây trên transport:

```text
RPC
 ├── HTTP/2
 ├── HTTP/3
 ├── TCP
 ├── QUIC
 └── custom transport
```

Không hard-code HTTP.

---

# 206.45. RPC streaming

Đã có:

```text
Unary
ServerStream
ClientStream
BidirectionalStream
```

và 206 khóa implementation dưới transport.

---

# 206.46. Serialization

Serialization không được đồng nhất với memory layout.

```text
Memory Layout
    ≠
Wire Format
```

---

# 206.47. Endianness

Wire protocol phải chỉ rõ:

```text
BigEndian
LittleEndian
NetworkOrder
Custom
```

Không lấy native machine endian làm protocol semantics.

---

# 206.48. Zero-copy serialization

Nếu wire representation tương thích layout, compiler/library có thể tránh copy.

Nhưng:

```text
@repr(C)
```

không tự động có nghĩa:

```text
WireSafe
```

---

# 206.49. Network input validation

Dữ liệu từ network là untrusted.

Pipeline:

```text
bytes
 ↓
parse
 ↓
validate
 ↓
typed value
```

Không được tạo safe typed value từ bytes chưa kiểm tra.

---

# 206.50. Parser zero-copy

Parser có thể trả:

```text
view<u8>
Str
```

nếu backing buffer còn sống.

Đây là nơi Axiom capability model tạo lợi thế lớn.

---

# 206.51. Parser lifetime

Không cần programmer viết lifetime annotation.

Compiler biết:

```text
ParsedMessage
 └── view
      └── InputBuffer
```

và reject nếu view escape khỏi buffer.

---

# 206.52. Streaming parser

Parser có thể incremental:

```text
chunk
 ↓
state machine
 ↓
message
```

không cần concatenate toàn bộ input.

---

# 206.53. Backpressure

Pipeline:

```text
NIC
 ↓
Socket
 ↓
Parser
 ↓
Application
```

phải hỗ trợ backpressure.

Không tự động buffer vô hạn.

---

# 206.54. Bounded network buffers

Mặc định high-performance server nên ưu tiên:

```text
bounded buffer pool
```

để kiểm soát memory.

---

# 206.55. Buffer pool

```text
NetworkBufferPool
```

có thể tái sử dụng buffers.

Ownership:

```text
pool
 ↓ checkout
buffer
 ↓ completion
pool
```

---

# 206.56. DMA buffer

DMA-capable buffer là storage contract:

```text
DmaBuffer<T>
```

có alignment/lifetime constraints.

---

# 206.57. DMA ownership

Trong lúc NIC đang sử dụng buffer:

```text
CPU mutable access
```

không được đồng thời tồn tại nếu hardware contract cấm.

Đây là capability conflict, không phải GC problem.

---

# 206.58. Completion

I/O completion:

```text
Pending
Ready
Failed
Cancelled
```

đã thống nhất với async model.

---

# 206.59. Completion ownership

Một pending operation giữ các resources cần thiết cho tới khi completion/cancellation contract hoàn tất.

---

# 206.60. Cancellation race

Nếu:

```text
cancel()
```

xảy ra đồng thời với kernel completion, API phải có trạng thái xác định:

```text
Completed
CancelledBeforeStart
CancelledAfterSubmission
CompletionWon
```

không được tạo dangling buffer.

---

# 206.61. io_uring

Linux backend:

```text
io_uring
```

là implementation của async I/O interface.

Không leak Linux-specific semantics vào Core.

---

# 206.62. IOCP

Windows:

```text
IOCP
```

cùng semantic interface.

---

# 206.63. epoll

epoll có thể làm readiness backend.

Không giả định readiness = completion.

---

# 206.64. kqueue

macOS/BSD backend:

```text
kqueue
```

---

# 206.65. Readiness vs Completion

Đây là khác biệt quan trọng:

```text
Readiness:
"operation can probably proceed"

Completion:
"operation has completed"
```

Axiom I/O layer phải giữ distinction.

---

# 206.66. Async network abstraction

High-level API có thể thống nhất:

```axiom
async fn read(...)
async fn write(...)
```

nhưng backend tự chọn:

```text
io_uring
IOCP
epoll
kqueue
```

---

# 206.67. Blocking network API

Axiom cũng cho phép:

```text
blocking read
blocking write
```

trong synchronous programs.

Không bắt mọi chương trình phải async.

---

# 206.68. Async ≠ faster

Async là execution model.

Performance phụ thuộc:

```text
syscalls
copies
allocations
context switches
cache locality
NIC
protocol
scheduler
```

---

# 206.69. Connection pool

High-level client:

```text
ConnectionPool<T>
```

quản lý:

- idle connections
- max connections
- lifetime
- health
- timeout

---

# 206.70. Pool ownership

Checkout:

```text
Pool
 ↓
ConnectionLease
```

Lease Drop có thể trả connection về pool theo contract.

Nhưng network close/failure vẫn phải được xử lý rõ.

---

# 206.71. Connection reuse

HTTP keep-alive/HTTP2 multiplex/QUIC connection reuse phải do protocol layer quản lý.

Không gộp thành một generic magic.

---

# 206.72. Rate limiting

Network library có:

```text
TokenBucket
LeakyBucket
ConcurrencyLimit
```

---

# 206.73. Rate limiting không phải backpressure

```text
RateLimit
    ≠
Backpressure
    ≠
ConcurrencyLimit
```

---

# 206.74. Retry

Retry policy:

```text
RetryPolicy
```

phải xét:

```text
idempotency
deadline
connection state
partial write
server response
```

---

# 206.75. Partial write

TCP write có thể ghi ít bytes hơn yêu cầu.

API phải biểu diễn:

```text
written_bytes
```

hoặc cung cấp `write_all` explicit.

---

# 206.76. `write_all`

`write_all` là loop abstraction:

```text
while remaining:
    write(...)
```

Compiler có thể inline/eliminate abstraction overhead.

---

# 206.77. Scatter/gather optimization

Compiler/backend có thể giữ nhiều views thành một vectored operation thay vì merge buffers.

---

# 206.78. Sendfile/splice

System layer có thể hỗ trợ:

```text
sendfile
splice
copy_file_range
```

khi platform cho phép.

Mục tiêu:

```text
disk
 ↓
kernel
 ↓
NIC
```

thay vì:

```text
disk
 ↓
user memory
 ↓
kernel
 ↓
NIC
```

---

# 206.79. Kernel bypass

System library có thể hỗ trợ:

```text
DPDK
AF_XDP
io_uring zero-copy
RDMA
```

nhưng tất cả đều cần explicit unsafe/system contracts.

---

# 206.80. RDMA

RDMA layer:

```text
MemoryRegion
QueuePair
CompletionQueue
```

---

# 206.81. RDMA memory registration

Registered memory có lifetime constraint:

```text
registered
 ↓
NIC may access
 ↓
deregister
```

Compiler/resource model phải ngăn deregister khi operation còn pending.

---

# 206.82. RDMA completion

Memory không được tái sử dụng trước khi required completion.

Đây là một trường hợp rất mạnh để kiểm chứng ownership + async model.

---

# 206.83. Network execution domain

Có thể có:

```text
CPU
NIC
DMA
GPU
```

nhưng NIC/DMA không phải general-purpose Axiom execution domain.

Chúng là external execution agents.

---

# 206.84. External agent capability

Khi hardware có quyền đọc/write buffer:

```text
CPU capability
```

phải không conflict với:

```text
DMA capability
```

theo device contract.

---

# 206.85. Network security

Các layer:

```text
TLS
DTLS
IPsec
MACsec
```

là security libraries/system layers.

---

# 206.86. Certificate types

Certificate/key/signature nên là typed structures, không phải raw byte arrays trong high-level API.

---

# 206.87. Secret memory

Sensitive buffers có thể có policy:

```text
NoDump
ZeroOnDrop
LockedMemory
```

nếu platform hỗ trợ.

Không đảm bảo tuyệt đối trên mọi OS.

---

# 206.88. Memory zeroing

Compiler không được optimize away required security zeroing.

Phải có semantic `SecureZero`/volatile-like primitive.

---

# 206.89. Network effects

Network operations có effects:

```text
IO
Network
Allocate
Synchronize
Foreign
```

và compiler/tooling có thể truy vấn.

---

# 206.90. Network capability

Không phải function nào cũng cần quyền network.

Application/security layer có thể giới hạn:

```text
DNS
TCP
UDP
RawSocket
RDMA
```

---

# 206.91. Raw sockets

Raw socket API nằm ở unsafe/system layer.

Không cấp quyền raw packet manipulation cho safe high-level socket API.

---

# 206.92. Packet capture

Packet capture:

```text
Pcap
AF_PACKET
BPF
```

là system capability.

---

# 206.93. Firewall integration

Firewall/network policy là OS/security layer.

Không phải compiler semantics.

---

# 206.94. Network namespaces

Linux/network namespace:

```text
NetworkNamespace
```

là OS resource.

---

# 206.95. Virtual networking

Support abstraction cho:

```text
veth
TUN/TAP
virtual NIC
```

ở system layer.

---

# 206.96. WASM networking

WASM có thể không có raw socket.

Network capability thông qua host imports/platform environment.

Core semantics không thay đổi.

---

# 206.97. Freestanding networking

Freestanding target có thể không có network.

API capability không tồn tại hoặc không được link.

---

# 206.98. AI/compiler integration

CompilerDB có thể expose:

```text
ax inspect network-buffer
ax explain async-io
ax explain zero-copy
ax explain buffer-lifetime
ax explain blocking
```

Ví dụ:

```text
NetworkBuffer #42
 ├── owner: BufferPool #3
 ├── DMA: active
 ├── mutable: no
 ├── pending operation: Write #17
 └── reusable: after Completion #17
```

Đây chính là loại thông tin cực kỳ hữu ích cho AI coding agent.

---

# 206.99. Network correctness boundary

Mọi backend:

```text
TCP
UDP
QUIC
io_uring
IOCP
RDMA
kernel-bypass
```

đều phải map về semantic model:

```text
Ownership
Capability
Lifetime
Completion
Cancellation
Effect
```

Backend không được tự tạo một semantics riêng phá vỡ compiler verifier.

---

# 206.100. Network invariants — `ANET2`

### `ANET2-20`
Network protocols shall remain library/system abstractions above Core.

### `ANET2-21`
Endpoint identity shall remain distinct from socket resource identity.

### `ANET2-22`
Socket resources shall obey ordinary Axiom ownership and Drop semantics.

### `ANET2-23`
Drop shall not imply graceful protocol shutdown.

### `ANET2-24`
TCP shall be modeled as an ordered byte stream rather than an implicit message protocol.

### `ANET2-25`
Application framing shall remain explicit.

### `ANET2-26`
Half-close semantics shall be represented explicitly where supported.

### `ANET2-27`
TCP partial writes shall not be silently interpreted as complete writes.

### `ANET2-28`
UDP shall not imply delivery, ordering or uniqueness.

### `ANET2-29`
QUIC streams shall remain distinct logical streams within a connection.

### `ANET2-30`
Stream lifetime shall respect connection dependencies.

### `ANET2-31`
TLS shall remain a protocol/security layer rather than a Core primitive.

### `ANET2-32`
Private cryptographic material shall obey explicit ownership semantics.

### `ANET2-33`
Network serialization shall remain distinct from memory representation.

### `ANET2-34`
Unvalidated network bytes shall not become safe typed values.

### `ANET2-35`
Zero-copy views shall not outlive their backing storage.

### `ANET2-36`
Scatter/gather operations shall obey capability overlap rules.

### `ANET2-37`
Pending I/O shall retain required resource ownership until completion or valid cancellation.

### `ANET2-38`
I/O cancellation races shall have defined semantics.

### `ANET2-39`
Readiness and completion semantics shall remain distinct.

### `ANET2-40`
io_uring, IOCP, epoll and kqueue shall remain backend implementations.

### `ANET2-41`
Blocking and asynchronous network APIs shall remain semantically distinct.

### `ANET2-42`
Async APIs shall not hide unbounded blocking operations.

### `ANET2-43`
Network buffer pools shall provide explicit ownership transfer.

### `ANET2-44`
DMA buffers shall obey external-agent access contracts.

### `ANET2-45`
CPU mutable access shall not conflict with active device/DMA access.

### `ANET2-46`
RDMA memory registration shall remain valid for all dependent operations.

### `ANET2-47`
RDMA completion shall govern reuse of externally accessed buffers.

### `ANET2-48`
Kernel-bypass APIs shall remain explicit system/unsafe abstractions.

### `ANET2-49`
Network rate limiting shall remain distinct from backpressure and concurrency limits.

### `ANET2-50`
Retry shall respect idempotency and deadline semantics.

### `ANET2-51`
Connection pooling shall preserve connection/resource ownership.

### `ANET2-52`
Connection reuse shall remain protocol-specific.

### `ANET2-53`
Network effects shall be visible to the effect/tooling system.

### `ANET2-54`
Network capabilities shall remain separate from language memory capabilities.

### `ANET2-55`
Raw socket and packet APIs shall require explicit system/unsafe access.

### `ANET2-56`
Security-sensitive memory operations shall not be optimized away when their semantic contract requires execution.

### `ANET2-57`
Network backends shall lower to the same ownership/capability/completion semantics.

### `ANET2-58`
WASM and freestanding targets may omit networking capabilities without changing Core semantics.

### `ANET2-59`
Network abstractions shall not require garbage collection.

### `ANET2-60`
Network abstractions shall not require a monolithic runtime.

### `ANET2-61`
High-level network abstractions shall permit compiler elimination/inlining of abstraction overhead.

### `ANET2-62`
Zero-copy shall be an optimization and API capability, not a mandatory requirement.

### `ANET2-63`
Copying shall remain semantically distinct from zero-copy storage sharing.

### `ANET2-64`
Compiler-generated network code shall pass ordinary ownership, capability and concurrency verification.

### `ANET2-65`
Network resource lifetimes shall be visible to CompilerDB.

### `ANET2-66`
AI tooling shall be able to inspect network buffer ownership and pending I/O state.

### `ANET2-67`
Network protocol implementations shall support deterministic testing where practical.

### `ANET2-68`
Network fault injection shall be part of conformance/testing infrastructure.

### `ANET2-69`
Protocol parsing shall support zero-copy operation without weakening memory safety.

### `ANET2-70`
Network APIs shall not introduce programmer-written lifetime annotations.

### `ANET2-71`
Network APIs shall preserve the distinction between local ownership and remote/distributed ownership.

### `ANET2-72`
Network semantics shall compose with Async, Storage, Distributed Systems, Time and Security models.

---

# Kiến trúc networking cuối cùng

```text
                       APPLICATION
                            │
                ┌───────────┼───────────┐
                ▼           ▼           ▼
              HTTP         RPC       WebSocket
                │           │
                └──────┬────┘
                       ▼
                  Protocol
                       │
              ┌────────┼────────┐
              ▼        ▼        ▼
             TCP      QUIC      UDP
              │        │        │
              └────┬───┴───┬────┘
                   ▼       ▼
                 Socket   TLS
                   │
              Async I/O
                   │
       ┌───────────┼───────────┐
       ▼           ▼           ▼
    io_uring     IOCP       kqueue/epoll
       │
       ▼
    Kernel
       │
       ▼
      NIC
       │
       ▼
   DMA buffers
```

Ở tầng thấp hơn:

```text
Buffer
  │
  ├── CPU view
  ├── DMA view
  ├── Network view
  └── Pending I/O capability
```

Compiler có thể theo dõi quan hệ này mà **programmer không phải viết lifetime/borrow annotation**.

Đây là một trong những điểm mà mô hình Axiom hiện tại có lợi thế rõ ràng: `view/mut_view + ownership + async + capability verification` có thể xử lý cả HTTP thông thường lẫn RDMA mà không cần tạo hai hệ thống memory management khác nhau.

---

# BOOTSTRAP-207 — Compression, Serialization, Binary Formats, IPC & Data Interchange

**TRẠNG THÁI: NEXT**

Sau khi đã khóa Network, bước kế tiếp nên xử lý **data representation bên ngoài process** một cách có hệ thống:

```text
Axiom Value
    │
    ├── Memory Representation
    │
    ├── Wire Representation
    │
    ├── Persistent Representation
    │
    ├── IPC Representation
    │
    └── Compressed Representation
```

Phạm vi 207:

```text
Serialization
Deserialization
Schema
Schema evolution
Binary format
Text format
JSON
CBOR
MessagePack
Protobuf-like encoding
FlatBuffers-like zero-copy encoding
Cap'n Proto-like encoding
Compression
LZ4
Zstd
Deflate
Brotli
Dictionary compression
Streaming compression
Checksums
Hashing
Merkle trees
Content addressing
IPC
Shared memory
Memory-mapped interchange
Zero-copy deserialization
Endian
Alignment
Versioning
Compatibility
```

Đặc biệt sẽ chốt một nguyên tắc rất quan trọng cho Axiom:

> **Memory layout, serialization layout, wire format và persistent storage format tuyệt đối không được mặc định là cùng một thứ.**

Nhưng đồng thời compiler phải cho phép programmer/AI khai báo khi chúng **cố ý giống nhau**, từ đó đạt được **zero-copy serialization/deserialization** mà vẫn giữ được safety.