# BOOTSTRAP-202 — Networking, Distributed Systems, RPC & High-Performance I/O

**TRẠNG THÁI: FROZEN / COMPLETED**

Mục tiêu:

> **Axiom phải hỗ trợ network server/client hiệu năng cao, zero-copy khi có thể, async I/O native, RPC, distributed systems và networking ở quy mô lớn mà không yêu cầu programmer tự quản lý lifetime buffer hay thread phức tạp.**

Nguyên tắc trung tâm:

```text
Network I/O
    │
    ├── Ownership
    ├── Capability
    ├── Async
    ├── Effect
    ├── Execution Domain
    └── Storage Domain
```

Không tạo một hệ thống memory/network riêng.

---

# 202.1. Network không thuộc Core

Core chỉ định nghĩa semantic primitives cần thiết:

```text
ownership
view
mut_view
async
Future
Send
Share
effects
execution domain
```

Networking nằm ở:

```text
std::net
std::async_io
std::rpc
std::tls
std::http
```

---

# 202.2. Socket là resource

`Socket` là owned OS resource:

```text
Socket
 ├── ownership
 ├── OS handle
 ├── state
 └── platform contract
```

Không phải integer handle.

Raw FD/HANDLE chỉ là representation ở system boundary.

---

# 202.3. Các socket type khác nhau

Không tạo universal `NetworkSocket`.

Có:

```text
TcpListener
TcpStream
UdpSocket
UnixStream
UnixListener
```

và các abstraction khác.

---

# 202.4. Socket state machine

Ví dụ TCP:

```text
Created
   ↓
Bound
   ↓
Listening
   ↓
Accepted
   ↓
Connected
   ↓
Closing
   ↓
Closed
```

API phải ngăn những operation vô nghĩa khi có thể.

---

# 202.5. Ownership của connection

`TcpStream` sở hữu connection.

Move:

```axiom
let connection = listener.accept()
```

chuyển ownership.

Không implicit shared ownership.

---

# 202.6. Split read/write

TCP connection có thể tách:

```text
TcpStream
    ├── ReadHalf
    └── WriteHalf
```

Compiler/library phải đảm bảo:

```text
ReadHalf
```

và:

```text
WriteHalf
```

có thể hoạt động đồng thời nếu backend hỗ trợ.

---

# 202.7. Split không clone socket

Việc split không nhất thiết duplicate OS resource.

Có thể tạo hai logical capabilities trên cùng resource:

```text
read capability
write capability
```

với lifetime được ràng buộc với owner.

---

# 202.8. Close semantics

`Drop` giải phóng ownership.

Nhưng:

```text
drop(stream)
```

không được hiểu là mọi protocol-level shutdown.

Có thể có:

```text
shutdown_read()
shutdown_write()
shutdown()
```

explicit.

---

# 202.9. Async socket

Ví dụ:

```axiom
async fn read(
    socket: mut_view<TcpStream>,
    buffer: mut_view<u8>
) -> Result<usize, NetError>
```

`.await` là suspension.

Không tạo thread mới cho mỗi operation.

---

# 202.10. Buffer lifetime qua await

Đây là vấn đề quan trọng.

Nếu:

```text
read(buffer).await
```

thì `buffer` phải còn valid trong toàn bộ operation.

Compiler phân tích:

```text
buffer
 └── capability
      └── async operation
```

Không cần programmer viết lifetime.

---

# 202.11. Kernel I/O buffer

Một số OS yêu cầu buffer vẫn tồn tại trong khi I/O pending.

Async I/O abstraction phải biểu diễn dependency đó.

Compiler không được giả định:

```text
await = operation đã hoàn thành
```

---

# 202.12. Owned async buffer

Pattern ưu tiên:

```text
Buffer
   ↓
read_async(buffer)
   ↓
Future<(Buffer, usize)>
```

Future sở hữu buffer trong thời gian operation pending.

Điều này tránh lifetime annotation.

---

# 202.13. Borrowed async buffer

Có thể hỗ trợ khi execution contract chứng minh an toàn:

```text
read_async(view)
```

nhưng không được phép view escape khỏi owner.

---

# 202.14. Zero-copy receive

Backend có thể hỗ trợ:

```text
receive()
 → NetworkBuffer
```

trong đó buffer lấy trực tiếp từ pool/kernel/DMA.

Không copy vào application buffer nếu không cần.

---

# 202.15. NetworkBuffer

Conceptually:

```text
NetworkBuffer<T>
```

là owned storage với:

```text
capacity
length
alignment
storage domain
device visibility
```

Có thể được trả về pool sau khi Drop.

---

# 202.16. Zero-copy send

Nếu application sở hữu:

```text
Buffer
```

và kernel/backend có thể gửi trực tiếp, ownership/capability contract có thể giữ buffer live đến completion.

Không cần clone.

---

# 202.17. Send lifetime

```text
send_async(buffer)
```

có thể semantic là:

```text
Buffer
   ↓ move
PendingSend
   ↓ completion
Buffer returned/released
```

---

# 202.18. Scatter/gather I/O

Hỗ trợ:

```text
IoVec
```

hoặc:

```text
view<BufferSlice>
```

để một syscall xử lý nhiều regions.

Compiler kiểm tra từng capability.

---

# 202.19. Vectored I/O

Ví dụ:

```text
header
body
trailer
```

có thể gửi mà không merge thành một buffer.

---

# 202.20. Capability conflict

Nếu hai vectored buffers overlap mà API yêu cầu exclusive access:

```text
UNKNOWN / OVERLAPS
```

→ reject safe operation.

Nếu proven disjoint:

```text
DISJOINT
```

→ cho phép.

---

# 202.21. io_uring / IOCP / epoll / kqueue

Axiom không expose một API OS-specific duy nhất ở high level.

Kiến trúc:

```text
Axiom Async I/O
        │
        ├── io_uring
        ├── IOCP
        ├── epoll
        ├── kqueue
        └── other backend
```

---

# 202.22. Async I/O backend abstraction

Backend cung cấp:

```text
submit
poll
cancel
completion
wake
```

High-level Future không phụ thuộc implementation cụ thể.

---

# 202.23. Completion semantics

Mỗi I/O operation có:

```text
Pending
Ready
Failed
Cancelled
```

Không dùng exception.

---

# 202.24. Cancellation

Cancellation phải phân biệt:

```text
Future dropped
```

và:

```text
I/O cancellation requested
```

Drop Future không mặc định có nghĩa OS operation đã bị cancel.

---

# 202.25. Explicit cancellation

Có thể:

```text
CancellationToken
CancellationHandle
```

hoặc backend-specific cancellation.

---

# 202.26. Cancellation race

Nếu:

```text
completion
```

xảy ra đồng thời với:

```text
cancel
```

API phải định nghĩa deterministic result semantics.

Không dựa vào timing ngẫu nhiên để quyết định ownership.

---

# 202.27. Timeout

Timeout là wrapper:

```text
operation
   +
timer
```

Không phải socket primitive bắt buộc.

---

# 202.28. Deadline

Hỗ trợ:

```text
Deadline
Timeout
Cancellation
```

tách biệt.

Deadline có thể được truyền xuyên RPC call chain.

---

# 202.29. Backpressure

Network pipeline phải hỗ trợ bounded buffering.

Ví dụ:

```text
Socket
 ↓
bounded queue
 ↓
decoder
 ↓
application
```

Nếu application chậm:

```text
queue full
```

→ producer phải chịu backpressure hoặc policy rõ ràng.

Không mặc định buffer vô hạn.

---

# 202.30. TCP backpressure

`write()` không đồng nghĩa:

```text
remote application đã nhận dữ liệu
```

Chỉ có nghĩa dữ liệu đã được accepted bởi tầng tương ứng.

API phải phân biệt:

```text
written
flushed
transported
application-acknowledged
```

khi protocol cần.

---

# 202.31. UDP semantics

UDP:

```text
datagram
```

không đảm bảo:

```text
delivery
ordering
uniqueness
```

Axiom API không được tạo abstraction khiến programmer hiểu sai.

---

# 202.32. QUIC

QUIC có:

```text
Connection
Stream
Datagram
```

Các resource này nên là distinct types.

---

# 202.33. QUIC stream ownership

Mỗi stream có thể được quản lý như một logical resource:

```text
Connection
 ├── BidirectionalStream
 └── UnidirectionalStream
```

Ownership semantics tương tự các OS resources khác.

---

# 202.34. Unix domain sockets

Hỗ trợ:

```text
UnixStream
UnixListener
```

và platform-specific equivalents.

---

# 202.35. Named pipes

Windows named pipe và các IPC tương tự nằm trong OS/network library layer.

---

# 202.36. Shared memory networking

Shared memory không phải network socket.

Nó là:

```text
SharedMemory
```

resource riêng.

Có thể dùng cho IPC zero-copy.

---

# 202.37. Shared memory safety

Typed shared memory cần:

```text
layout
initialization
synchronization
ownership/Share
```

explicit.

Không biến raw mapped bytes thành arbitrary safe `T`.

---

# 202.38. Network serialization

Network representation không đồng nhất với memory representation.

```text
struct T
    ≠
wire format T
```

Serialization phải explicit.

---

# 202.39. Serialization

Có thể có:

```text
Serialize
Deserialize
```

traits/library contracts.

`Deserialize` phải validate input.

---

# 202.40. Zero-copy deserialization

Có thể deserialize bằng view nếu:

```text
wire layout
==
valid in-memory representation
```

và mọi alignment/endianness/validity condition được chứng minh.

Nếu không → copy/convert.

---

# 202.41. Endianness

Wire protocol phải khai báo endian.

Không dựa vào host endian.

---

# 202.42. Untrusted input

Network input luôn được coi là external/untrusted data.

Deserializer không được tạo safe object trước khi validation hoàn tất.

---

# 202.43. Length validation

Mọi length từ network phải được bounds-check.

Đặc biệt:

```text
length
offset
count
allocation size
```

---

# 202.44. Integer overflow

Network parser không được dựa vào C-style integer overflow.

Axiom numeric semantics đã định nghĩa checked/wrapping/saturating behavior.

Parser chọn semantics phù hợp.

---

# 202.45. Framing

TCP không có message boundary.

Library phải cung cấp:

```text
LengthPrefix
Delimiter
FixedFrame
CodecFrame
```

explicit.

---

# 202.46. HTTP

HTTP layer nằm trên:

```text
TCP / QUIC / TLS
```

Không phải Core.

---

# 202.47. HTTP request ownership

Request body có thể là:

```text
owned buffer
stream
view
file
```

tùy API.

Không ép mọi request thành một giant String.

---

# 202.48. HTTP streaming

Response body có thể:

```text
AsyncStream<Bytes>
```

để streaming.

---

# 202.49. WebSocket

WebSocket message:

```text
Text
Binary
Ping
Pong
Close
```

là typed enum.

---

# 202.50. TLS

TLS connection là resource abstraction:

```text
TlsStream<T>
```

nhưng certificate/key/material ownership phải explicit.

---

# 202.51. TLS key material

Private key là sensitive resource.

Compiler/tooling không nên log nội dung secret trong diagnostics.

---

# 202.52. TLS backend

Có thể dùng:

```text
native OS TLS
Axiom TLS
external TLS library
```

qua backend contract.

Không mandatory dependency.

---

# 202.53. DNS

DNS là async external operation.

Ví dụ:

```text
resolve(host) -> Future<Result<Address>>
```

Không block event-loop thread.

---

# 202.54. Connection pooling

Pool là library abstraction:

```text
ConnectionPool<T>
```

Ownership của checked-out connection phải rõ.

---

# 202.55. Pool safety

Connection không được trả về pool trong khi:

```text
pending async operation
```

vẫn giữ capability vào connection.

Compiler verifier nên bắt khi có thể.

---

# 202.56. RPC

RPC là library/framework layer.

Kiến trúc:

```text
Axiom Function
      ↓
RPC Contract
      ↓
Serialization
      ↓
Transport
      ↓
Remote Function
```

---

# 202.57. RPC interface

Ví dụ conceptual:

```axiom
service UserService {
    fn get_user(id: UserId) -> Result<User, UserError>
}
```

Nhưng đây không nhất thiết là một language-level `service` keyword.

Có thể compiler derive từ ordinary declarations + attributes/metadata.

---

# 202.58. RPC contract generation

Compiler/comptime có thể generate:

```text
client stub
server dispatch
serialization
ABI metadata
```

và generated code quay lại compiler pipeline.

---

# 202.59. RPC không phải local call

Remote call có:

```text
latency
failure
serialization
partial execution
```

Do đó type/ABI metadata không được làm RPC trông như local function hoàn toàn.

---

# 202.60. RPC errors

Phân biệt:

```text
ApplicationError
TransportError
ProtocolError
SerializationError
Timeout
Cancelled
Unavailable
```

---

# 202.61. Retry semantics

Compiler không tự động retry arbitrary RPC.

Retry là application/library policy.

Vì:

```text
side effect
idempotency
```

không thể suy ra đơn giản từ function type.

---

# 202.62. Idempotency

RPC contract có thể khai báo metadata:

```text
Idempotent
NonIdempotent
Unknown
```

để framework quyết định retry.

---

# 202.63. RPC cancellation

RPC cancellation phải truyền được nếu protocol hỗ trợ.

Không đồng nghĩa server function bị forcibly terminated.

---

# 202.64. RPC deadline

Deadline có thể propagate:

```text
Client
 ↓
Service A
 ↓
Service B
```

nhưng mỗi hop phải tôn trọng local execution constraints.

---

# 202.65. RPC streaming

Hỗ trợ:

```text
Unary
ServerStream
ClientStream
BidirectionalStream
```

với async streams.

---

# 202.66. Streaming ownership

Mỗi message:

```text
owned value
```

có thể move qua stream.

Không cần clone mặc định.

---

# 202.67. Distributed ownership

Quan trọng:

> **`Send` không có nghĩa “được gửi qua network”.**

`Send` chỉ nói value có thể chuyển giữa execution domains theo Axiom concurrency model.

Network transfer cần serialization/transport contract.

---

# 202.68. Actor model

Actor có thể xây trên:

```text
owned state
+
mailbox
+
executor
```

Không cần actor primitive trong Core.

---

# 202.69. Actor mailbox

Mailbox:

```text
bounded
or
unbounded
```

phải có policy rõ.

Bounded là lựa chọn mặc định cho hệ thống latency-sensitive.

---

# 202.70. Distributed channels

Channel qua network không phải cùng semantic với local channel.

Local:

```text
ownership transfer
```

Remote:

```text
serialization
+
transport
+
ownership transfer at protocol boundary
```

---

# 202.71. Distributed shared state

Không có semantic:

```text
Arc<T>
```

qua machine boundary.

Distributed shared state phải dùng:

```text
RPC
distributed lock
consensus
shared memory
database
```

explicit.

---

# 202.72. High-performance server model

Axiom hỗ trợ architecture:

```text
             Listener
                │
         ┌──────┴──────┐
         ▼             ▼
      Reactor       Reactor
         │             │
         └──────┬──────┘
                ▼
          Worker Tasks
                │
                ▼
            Application
```

Không bắt buộc thread-per-connection.

---

# 202.73. Reactor

OS event backend:

```text
io_uring
IOCP
epoll
kqueue
```

cung cấp readiness/completion.

---

# 202.74. Executor

Executor chạy Future.

Networking không được tự tạo một executor riêng nếu đã có runtime executor phù hợp.

---

# 202.75. Worker pool

CPU-bound tasks có thể chạy worker pool.

I/O task không cần giữ một OS thread trong thời gian chờ.

---

# 202.76. CPU affinity

High-performance server có thể cấu hình:

```text
ThreadAffinity
NUMA affinity
```

ở system/runtime layer.

Không đưa vào ordinary source semantics.

---

# 202.77. NUMA

Memory/storage domain có thể mở rộng:

```text
NUMANode
```

Allocator/pool có thể chọn locality.

Compiler vẫn không cần expose pointer topology cho ordinary code.

---

# 202.78. Kernel bypass

Axiom có thể hỗ trợ:

```text
DPDK-like
io_uring
AF_XDP
RDMA
```

qua system/unsafe libraries.

Không đưa kernel-bypass semantics vào Core.

---

# 202.79. RDMA

RDMA buffer có:

```text
registered memory
device visibility
lifetime
completion
```

phải được thể hiện bằng resource contracts.

Không được Drop memory registration trong khi operation pending.

---

# 202.80. DMA/network buffer contract

Kết hợp:

```text
Storage Domain
+
Execution Domain
+
Capability
+
Async completion
```

để compiler biết buffer phải sống đến đâu.

Đây là điểm rất mạnh của Axiom.

---

# 202.81. Foreign async I/O

FFI function:

```text
submit_io(...)
```

phải có `FfiContract` mô tả:

```text
buffer lifetime
callback lifetime
thread
completion
cancellation
ownership
```

Nếu không đủ thông tin → compiler conservative.

---

# 202.82. Network memory safety

Safe networking phải đảm bảo:

```text
no use-after-free
no double close
no buffer overflow
no dangling async buffer
no invalid capability
no data race
```

---

# 202.83. Network effect system

Network functions mang effects:

```text
IO
Network
Synchronize
Allocate
Foreign
```

CompilerDB có thể expose chúng.

---

# 202.84. Pure network-independent logic

Protocol parser có thể tách:

```text
bytes → message
```

thành pure function.

Điều này cho phép:

```text
fuzzing
formal testing
SIMD
comptime evaluation
```

khi phù hợp.

---

# 202.85. Protocol parser zero-copy

Parser có thể trả:

```text
MessageView<'buffer'>
```

về mặt semantic capability, nhưng programmer không cần viết lifetime.

Axiom compiler tự kiểm tra view không vượt quá input.

---

# 202.86. Parser + async

Không cho parser giữ view vào temporary buffer đã được chuyển ownership hoặc có thể bị recycle.

Compiler ownership/capability verifier bắt lỗi.

---

# 202.87. Protocol state machine

Complex protocols có thể biểu diễn bằng ordinary enums/structs:

```text
Handshake
Authenticated
Established
Closing
```

Không cần state-machine language riêng.

---

# 202.88. Serialization schema

Schema có thể được compiler/comptime derive:

```text
@derive(Serialize, Deserialize)
```

Generated code phải quay lại:

```text
resolve
typecheck
ownership verify
```

---

# 202.89. Versioned protocol

Wire schema có version.

Không được giả định:

```text
source type version == wire version
```

Adapters có thể chuyển giữa versions.

---

# 202.90. Compression

Compression:

```text
gzip
zstd
brotli
lz4
```

là codec library.

Streaming compression hỗ trợ async pipeline.

---

# 202.91. Encryption

Encryption primitives thuộc crypto library/system layer.

Không đưa cryptography algorithms vào Core.

---

# 202.92. Constant-time

Crypto code có thể yêu cầu:

```text
constant_time
```

contract đã liên kết với security model.

Compiler/tooling kiểm tra các optimization có thể vi phạm contract khi có thể.

---

# 202.93. Network security

TLS/authentication/authorization là application/library security.

Không coi:

```text
memory safe
```

đồng nghĩa:

```text
network secure
```

---

# 202.94. WASM networking

WASM không có raw socket giống native.

Network APIs map sang host/browser capabilities.

Axiom source semantics giữ nguyên; target capability khác.

---

# 202.95. Freestanding networking

Freestanding/kernel builds có thể cung cấp network stack riêng.

Không link hosted OS network runtime.

---

# 202.96. Embedded networking

Embedded target có thể có:

```text
Ethernet
Wi-Fi
CAN
SPI
UART
```

thông qua platform/system packages.

Không giả định POSIX.

---

# 202.97. Network diagnostics

CompilerDB/tooling:

```text
ax explain async-io
ax explain buffer
ax explain socket
ax explain rpc
ax explain realtime
```

có thể hiển thị:

```text
buffer ownership
pending operation
capability dependency
storage domain
execution domain
effect set
```

---

# 202.98. Network optimization

Compiler/backend được phép:

- inline protocol parser
- eliminate temporary buffers
- scalar replace message structs
- vectorize parsing
- specialize serialization
- fuse copies
- eliminate redundant endian conversion
- eliminate bounds checks khi proof tồn tại
- stack/promote buffers
- reuse pools

nhưng:

> **Không được biến một semantic copy observable thành zero-copy nếu API contract yêu cầu independent ownership.**

---

# 202.99. Network runtime composition

Một executable TCP server tối thiểu có thể link:

```text
Program
Startup
Allocator
Async
Network
Platform
```

Không cần:

```text
GUI
GPU
Tensor
Audio
Reflection
Unicode
```

nếu không dùng.

---

# 202.100. Network invariants — `ANET`

### `ANET-20`
Network resources shall be explicit owned resources.

### `ANET-21`
Raw OS handles shall not implicitly become safe resource owners.

### `ANET-22`
Socket types shall model meaningful protocol/resource distinctions.

### `ANET-23`
Async I/O shall preserve buffer validity until operation completion.

### `ANET-24`
Async I/O shall not require programmer-written lifetime annotations.

### `ANET-25`
Owned buffers may be moved into pending operations.

### `ANET-26`
Borrowed buffers may only be used when their capability lifetime is proven safe.

### `ANET-27`
Zero-copy shall be permitted when ownership, layout and backend contracts allow it.

### `ANET-28`
Zero-copy shall never silently alter ownership semantics.

### `ANET-29`
Scatter/gather operations shall respect capability overlap rules.

### `ANET-30`
Network input shall be treated as externally sourced data.

### `ANET-31`
Deserialization shall validate bounds, layout, alignment and representation before safe exposure.

### `ANET-32`
Wire representation shall remain distinct from ordinary memory representation.

### `ANET-33`
Wire endianness shall be explicit.

### `ANET-34`
Network framing shall be explicit.

### `ANET-35`
TCP APIs shall not imply message boundaries.

### `ANET-36`
UDP APIs shall not imply delivery or ordering guarantees absent a protocol contract.

### `ANET-37`
Cancellation shall be distinct from dropping a Future.

### `ANET-38`
Cancellation races shall have defined completion semantics.

### `ANET-39`
Timeouts and deadlines shall be explicit policy abstractions.

### `ANET-40`
Backpressure shall be representable without unbounded buffering.

### `ANET-41`
Network operations shall expose appropriate external effects.

### `ANET-42`
Async networking shall reuse the Axiom Future/executor model.

### `ANET-43`
OS-specific I/O backends shall be hidden behind portable abstractions where possible.

### `ANET-44`
io_uring, IOCP, epoll and kqueue shall be backend implementations, not separate language semantics.

### `ANET-45`
Connection pooling shall preserve resource and pending-operation lifetimes.

### `ANET-46`
RPC shall remain a library/framework abstraction.

### `ANET-47`
RPC contracts shall distinguish transport, protocol, serialization and application errors.

### `ANET-48`
RPC retry shall not be implicit solely from function type.

### `ANET-49`
RPC idempotency shall be explicit when relevant.

### `ANET-50`
RPC streaming shall use explicit stream semantics.

### `ANET-51`
Network Send shall remain distinct from Axiom `Send`.

### `ANET-52`
Distributed transfer shall not imply local shared ownership.

### `ANET-53`
Shared memory shall remain distinct from network transport.

### `ANET-54`
DMA/RDMA resources shall have explicit storage, lifetime and completion contracts.

### `ANET-55`
Foreign asynchronous operations shall provide sufficient FFI contracts for safe wrappers.

### `ANET-56`
Unknown foreign I/O behavior shall be treated conservatively.

### `ANET-57`
High-performance networking shall support reactor/completion-based execution without thread-per-connection requirements.

### `ANET-58`
Network server architecture shall support bounded worker/task scheduling.

### `ANET-59`
Protocol parsing shall be separable from transport effects.

### `ANET-60`
Zero-copy parsing shall preserve source capability validity.

### `ANET-61`
Generated serialization/RPC code shall pass normal compiler verification.

### `ANET-62`
Network optimizations shall preserve ownership, capability and protocol semantics.

### `ANET-63`
Network runtime components shall be optional.

### `ANET-64`
A program not using networking shall not acquire network runtime dependencies.

### `ANET-65`
WASM and freestanding targets may provide different network capabilities without changing Core semantics.

### `ANET-66`
Network security shall remain distinct from memory safety.

### `ANET-67`
Cryptographic constant-time contracts shall remain explicit.

### `ANET-68`
Network diagnostics shall expose buffer, ownership, capability, async and effect reasoning.

### `ANET-69`
Compiler optimization shall eliminate redundant network-buffer transformations only when semantics permit.

### `ANET-70`
Axiom networking shall not require a garbage collector.

### `ANET-71`
Axiom networking shall not require a monolithic runtime.

### `ANET-72`
Axiom networking shall support native high-performance I/O while preserving programmer-level semantic simplicity.

---

# Kiến trúc Networking hoàn chỉnh

```text
                         AXIOM NETWORK
                              │
         ┌────────────────────┼────────────────────┐
         │                    │                    │
      Transport             RPC                 IPC
         │                    │                    │
   ┌─────┼─────┐        Serialization       Shared Memory
   │     │     │             │                    │
  TCP   UDP   QUIC           │                  Channel
   │     │     │             │
   └─────┼─────┘             │
         ▼                   ▼
       Async I/O ──────── RPC Runtime
         │
   ┌─────┼───────────┐
   ▼     ▼           ▼
io_uring IOCP     epoll/kqueue
   │     │           │
   └─────┼───────────┘
         ▼
     OS / NIC / DMA
```

Điểm quan trọng nhất của 202 là Axiom hiện có thể biểu diễn một đường **zero-copy end-to-end**:

```text
NIC
 ↓
DMA Buffer
 ↓
NetworkBuffer
 ↓
Protocol View
 ↓
Application View
 ↓
Tensor / Audio / Video
```

mà không bắt programmer phải tự viết một chuỗi lifetime annotation.

Compiler có thể tự xác minh:

```text
Who owns the buffer?
Who may read it?
Who may mutate it?
How long must it remain valid?
Which async operation depends on it?
Can it be moved?
Can it be reused?
Can it be freed?
```

Đây chính là nơi mô hình **ownership + capability + async + storage domain** của Axiom bắt đầu cho thấy lợi thế rõ rệt so với việc thiết kế từng subsystem độc lập.

---

# BOOTSTRAP-203 — Database, Storage Engine, Filesystem & Persistent Data

**TRẠNG THÁI: NEXT**

Mảng tiếp theo sẽ khóa tầng persistent computing:

```text
File
Directory
Filesystem
Memory Mapping
Database
B-Tree
LSM Tree
Index
Cache
Page
Transaction
WAL
MVCC
Snapshot
Blob
Object Storage
Query Engine
Columnar Storage
Vector Database
```

Đặc biệt cần giải quyết một vấn đề rất quan trọng:

> **Làm thế nào để Axiom cho phép viết database/storage engine hiệu năng ngang C/C++ nhưng ownership, crash consistency, mmap, page cache, async I/O, transactions và concurrency vẫn được compiler hỗ trợ thay vì trở thành hàng triệu dòng unsafe code?**

Và sẽ phải chốt thêm mối quan hệ:

```text
Axiom Memory Model
        ↓
OS File Resource
        ↓
mmap
        ↓
Page
        ↓
Buffer Pool
        ↓
B-Tree / LSM
        ↓
Transaction
        ↓
WAL
        ↓
Database
```

để sau 203 Axiom không chỉ mạnh ở **compute/network/GPU/AI**, mà cả **storage/database systems**.