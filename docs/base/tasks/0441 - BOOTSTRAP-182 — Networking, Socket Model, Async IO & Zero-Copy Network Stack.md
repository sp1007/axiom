# BOOTSTRAP-182 — Networking, Socket Model, Async I/O & Zero-Copy Network Stack
**FROZEN / COMPLETED**

Đây là một mốc quan trọng vì networking là nơi rất dễ làm một ngôn ngữ systems bị khóa vào POSIX hoặc biến async thành một lớp abstraction nặng.

Nguyên tắc của Axiom:

> **Axiom định nghĩa semantic I/O; OS backend quyết định cách thực hiện I/O.**

Vì vậy Core không định nghĩa `epoll`, `kqueue`, `IOCP` hay `io_uring` như language primitives.

---

## 182.1. Networking không thuộc Core

Core chỉ cần các khái niệm cần cho:

```text
ownership
capability
buffer
async
cancellation
completion
ABI
```

Networking nằm trong:

```text
std::net
std::io
std::async
std::os
```

---

# 182.2. Socket là resource

Socket không phải chỉ là integer file descriptor.

Semantic model:

```text
Socket<T>
    owns external OS/network resource
    has lifecycle
    has capabilities
    may perform I/O
```

Do đó:

```text
Socket
```

là `Drop` resource.

---

# 182.3. Socket ownership

Ví dụ:

```ax
let socket = TcpSocket::new()?;
```

`socket` sở hữu resource.

Move:

```ax
let other = socket;
```

sẽ chuyển ownership.

Sau đó:

```ax
socket.read(...);
```

là lỗi use-after-move.

---

# 182.4. Không dùng integer làm socket API

Không khuyến khích:

```ax
let fd: i32 = ...
```

làm API networking chính.

Có thể expose raw OS handle ở:

```text
std::os
unsafe/system
```

nhưng abstraction an toàn phải là typed resource.

---

# 182.5. Raw socket handle

Ví dụ:

```text
RawSocket
```

chỉ biểu diễn machine/OS resource identity.

Nó không tự cung cấp:

```text
ownership
validity
protocol
lifetime
```

---

# 182.6. Socket capability

Socket có các capability:

```text
READ
WRITE
CONNECT
ACCEPT
SHUTDOWN
CONFIGURE
```

Compiler/library có thể biểu diễn chúng bằng type hoặc state abstraction.

---

# 182.7. TCP socket state

Semantic state:

```text
Created
Bound
Listening
Connecting
Connected
Closing
Closed
```

Không nhất thiết phải tạo một type riêng cho mọi state nếu gây phức tạp.

---

# 182.8. State machine

API phải không cho phép các thao tác invalid.

Ví dụ:

```text
listen()
```

chỉ có ý nghĩa với socket phù hợp.

Nếu compile-time state encoding quá nặng, runtime `Result` có thể được dùng ở những boundary thực sự dynamic.

---

# 182.9. TCP abstraction

```ax
let listener = TcpListener::bind(address)?;
let connection = listener.accept()?;
```

`TcpListener` sở hữu listening socket.

`TcpStream` sở hữu connection.

---

# 182.10. Accept ownership

`accept()`:

```text
TcpListener
    ↓
TcpStream
```

tạo một resource ownership mới.

Không trả raw fd.

---

# 182.11. Async accept

```ax
let stream = listener.accept_async().await?;
```

không tạo thread mới.

Future giữ các state cần thiết.

---

# 182.12. UDP

UDP có semantic khác TCP:

```text
UdpSocket
```

không có connected byte-stream semantics.

API nên phân biệt:

```text
send_to(data, address)
receive_from(buffer)
```

với TCP:

```text
read(buffer)
write(buffer)
```

---

# 182.13. Connected UDP

OS có thể hỗ trợ UDP `connect`.

Axiom có thể expose:

```text
UdpSocket::connect()
```

nhưng vẫn giữ UDP datagram semantics.

---

# 182.14. TCP là byte stream

TCP không bảo toàn message boundary.

Nếu gửi:

```text
A
B
C
```

receiver có thể nhận:

```text
AB
C
```

hoặc:

```text
A
BC
```

API không được tạo ảo giác packet/message boundary.

---

# 182.15. Datagram giữ message boundary

UDP:

```text
Datagram {
    payload
    source
    destination
}
```

mỗi receive tương ứng với một datagram theo semantic contract, subject to truncation/error behavior.

---

# 182.16. Buffer là trung tâm

Networking nên dùng:

```text
Bytes
view<u8>
mut_view<u8>
```

thay vì bắt buộc:

```text
String
```

---

# 182.17. Network API không assume UTF-8

Socket nhận:

```text
Bytes
```

không phải:

```text
String
```

Nếu protocol là UTF-8:

```ax
let text = Str::from_utf8(bytes)?;
```

---

# 182.18. Read API

Sync:

```ax
let n = stream.read(mut_view(buffer))?;
```

Semantic:

```text
borrow buffer mutably
perform I/O
return number of bytes
```

---

# 182.19. Async read

```ax
let n = stream.read_async(mut_view(buffer)).await?;
```

Nhưng Axiom verifier phải đảm bảo:

```text
buffer
```

không bị:

- drop
- move
- relocation
- conflicting mutable access

trong thời gian operation yêu cầu.

---

# 182.20. In-flight I/O ownership

Đây là invariant quan trọng:

> **Một asynchronous I/O operation phải giữ quyền truy cập cần thiết tới storage cho đến khi completion/cancellation contract kết thúc.**

Điều này dùng trực tiếp capability verifier.

---

# 182.21. Async I/O không nhất thiết copy buffer

Ví dụ:

```text
user buffer
    ↓
OS async I/O
    ↓
completion
```

Có thể zero-copy nếu backend cho phép.

---

# 182.22. Zero-copy là optimization

Axiom semantic API không guarantee zero-copy trừ API explicitly yêu cầu.

Compiler/runtime có thể:

```text
copy
move
pin
register buffer
DMA
```

miễn semantics không thay đổi.

---

# 182.23. Stable address cho I/O

Một số OS/backend yêu cầu buffer không thay đổi địa chỉ trong lúc I/O.

Axiom không bắt programmer viết:

```text
Pin<&mut T>
```

như một phần Core.

Thay vào đó:

```text
async I/O API
```

có thể establish:

```text
StableAddress
```

storage contract internally.

---

# 182.24. Compiler-managed pinning

Compiler/runtime có thể:

```text
move buffer
    ↓
detect in-flight I/O
    ↓
block relocation
```

hoặc chuyển buffer sang storage phù hợp.

Programmer không cần quản lý pin nếu abstraction có thể đảm bảo.

---

# 182.25. I/O future state

Ví dụ:

```text
ReadFuture {
    socket
    buffer capability
    operation state
}
```

Future chỉ giữ state thực sự cần qua `.await`.

---

# 182.26. Borrow across await

Nếu buffer là external capability:

```text
mut_view(buffer)
```

và I/O Future giữ nó qua await, verifier biết capability còn sống.

Không cần lifetime annotation.

---

# 182.27. Multiple reads

Không cho:

```text
read_async(buffer)
read_async(buffer)
```

đồng thời nếu cả hai yêu cầu mutable access tới cùng region.

Verifier phát hiện:

```text
E_CAPABILITY_CONFLICT
```

---

# 182.28. Disjoint buffers

Có thể:

```ax
read_async(view_a);
read_async(view_b);
```

nếu compiler chứng minh:

```text
A ∩ B = ∅
```

Điều này phù hợp trực tiếp với Alias/Capability Analysis.

---

# 182.29. Scatter/gather I/O

Axiom nên hỗ trợ semantic:

```text
IoVec
```

hoặc:

```text
view<view<u8>>
```

cho:

```text
readv
writev
sendmsg
recvmsg
```

---

# 182.30. No forced concatenation

Không cần:

```text
header + body → temporary buffer
```

chỉ để gửi một message.

Có thể:

```ax
socket.writev([
    view(header),
    view(body)
])?;
```

---

# 182.31. Zero-copy gather

Backend có thể map trực tiếp:

```text
writev
WSASend
sendmsg
io_uring
```

tùy OS.

Semantic abstraction giữ nguyên.

---

# 182.32. Scatter read

Ví dụ:

```text
receive:
    header → buffer A
    payload → buffer B
```

nếu backend hỗ trợ.

---

# 182.33. Partial I/O

`read` không guarantee fill toàn bộ buffer.

```text
read(buffer[0..4096])
```

có thể trả:

```text
0..4096
```

và thành công.

---

# 182.34. EOF

TCP EOF:

```text
read() → 0
```

là semantic EOF.

Không phải lỗi.

---

# 182.35. Would-block

Synchronous nonblocking socket có thể trả:

```text
WouldBlock
```

Đây là trạng thái, không nhất thiết là fatal error.

---

# 182.36. Async backend che giấu WouldBlock

Trong async API:

```text
read_async()
```

thường không expose `WouldBlock`.

Runtime/backend đăng ký interest và Future trở thành Pending.

---

# 182.37. Future state

```text
Pending
    ↓
OS completion/readiness event
    ↓
Wake
    ↓
Poll
    ↓
Ready
```

phù hợp async model đã frozen.

---

# 182.38. Readiness vs completion

Axiom phải phân biệt:

### Readiness

```text
epoll
kqueue
```

nói:

> operation có thể thử mà không block.

### Completion

```text
IOCP
io_uring
```

nói:

> operation đã hoàn thành hoặc có completion result.

---

# 182.39. Không ép chung implementation model

Semantic Future chỉ cần:

```text
Pending / Ready
```

backend tự quyết:

```text
readiness
completion
hybrid
```

---

# 182.40. Backend abstraction

```text
IoBackend
├── LinuxReadiness
├── LinuxIoUring
├── WindowsIocp
├── MacKqueue
└── Embedded
```

Không phải language primitive.

---

# 182.41. Executor + I/O reactor

Một async runtime có thể gồm:

```text
Executor
+
Timer
+
I/O Driver
```

nhưng không bắt buộc tất cả phải nằm trong một runtime.

---

# 182.42. Completion driver

Ví dụ:

```text
I/O operation
    ↓
OS
    ↓
completion
    ↓
waker
    ↓
executor
```

---

# 182.43. I/O driver không phải scheduler

I/O driver chỉ thông báo completion/readiness.

Executor quyết định task nào chạy.

---

# 182.44. Backpressure

Networking API phải hỗ trợ việc:

```text
producer nhanh
consumer chậm
```

mà không buộc unlimited buffering.

---

# 182.45. `write` partial

TCP write có thể ghi:

```text
1000 requested
700 written
```

API phải giữ semantic rõ ràng.

---

# 182.46. `write_all`

Có thể cung cấp:

```ax
stream.write_all(data)?;
```

nhưng đây là library loop:

```text
while remaining:
    write()
```

không phải primitive.

---

# 182.47. Async `write_all`

```ax
stream.write_all_async(data).await?;
```

Future state machine có thể rất nhỏ sau optimization.

---

# 182.48. Backpressure-aware stream

Async writer có thể trả:

```text
Pending
```

thay vì buffering vô hạn.

---

# 182.49. Buffer ownership

Có ba kiểu API:

```text
borrowed buffer
owned buffer
shared buffer
```

Ví dụ:

```text
read(view)
read_owned(Buffer)
```

Owned-buffer API hữu ích cho async I/O vì Future có thể sở hữu buffer.

---

# 182.50. Owned async buffer

Ví dụ semantic:

```ax
read_async(buffer: Buffer)
    -> Future<Result<(Buffer, usize), Error>>
```

Future sở hữu buffer trong thời gian I/O.

Sau completion:

```text
Buffer
```

trả lại caller.

Đây là cách rất sạch để tránh lifetime/pinning bureaucracy.

---

# 182.51. Zero-copy owned buffer

Compiler/runtime có thể chuyển ownership:

```text
caller
 ↓ Move
Future
 ↓ Move
OS/runtime
 ↓ Move
caller
```

không cần physical copy.

---

# 182.52. Receive buffer pool

High-performance server có thể dùng:

```text
BufferPool
```

để tái sử dụng allocation.

Đây là library abstraction.

---

# 182.53. Arena networking

Parser/server có thể dùng:

```text
Arena
```

cho nhiều packet/request.

Ownership vẫn deterministic.

---

# 182.54. Packet parsing

Parser nên nhận:

```ax
fn parse(packet: view<u8>) -> Result<Message, ParseError>
```

zero-copy nếu Message có thể giữ view hợp lệ.

Nếu Message escape owner:

verifier sẽ phát hiện capability lifetime.

---

# 182.55. Owned message

Nếu cần giữ data:

```ax
Message {
    payload: Bytes
}
```

explicit ownership.

Không implicit clone toàn packet.

---

# 182.56. Protocol layers

Kiến trúc:

```text
Bytes
 ↓
Frame
 ↓
Packet
 ↓
Protocol
 ↓
Connection
 ↓
Application
```

Mỗi layer không được tự động copy dữ liệu.

---

# 182.57. Address types

Không dùng String cho:

```text
IP address
port
socket address
```

Nên có:

```text
Ipv4Addr
Ipv6Addr
IpAddr
SocketAddr
```

---

# 182.58. IP address representation

`Ipv4Addr` có semantic 32-bit address.

`Ipv6Addr` semantic 128-bit address.

Representation có thể tối ưu nhưng public binary layout chỉ stable nếu explicit.

---

# 182.59. Port

Port là unsigned bounded integer semantic.

Compiler/library validate range.

---

# 182.60. SocketAddr

```text
IpAddr + Port
```

không phải formatted string.

---

# 182.61. DNS

DNS là asynchronous external I/O.

```ax
resolve(hostname).await?
```

không phải compiler primitive.

---

# 182.62. DNS result

Có thể trả:

```text
Vec<SocketAddr>
```

vì một hostname có nhiều addresses.

---

# 182.63. DNS caching

Cache là runtime/library policy.

Không hidden trong Core.

---

# 182.64. DNS timeout

DNS operation nhận:

```text
Deadline
```

thay vì mỗi layer tự tạo timeout duration.

---

# 182.65. TCP connect

API:

```ax
TcpStream::connect(addr).await?
```

có thể internally:

```text
socket
bind optional
connect
wait completion
```

---

# 182.66. Happy Eyeballs

IPv4/IPv6 connection racing là library policy.

Có thể chạy:

```text
IPv6 attempt
+
IPv4 attempt
```

với shared deadline/cancellation.

Axiom concurrency model đã đủ để biểu diễn.

---

# 182.67. TLS

TLS không thuộc socket primitive.

Kiến trúc:

```text
TcpStream
    ↓
TlsStream
```

TLS implementation có thể là:

```text
Axiom library
FFI
platform TLS
```

---

# 182.68. TLS ownership

`TlsStream` có thể own underlying stream:

```text
TlsStream<T: Stream>
```

hoặc hold capability theo abstraction.

---

# 182.69. TLS zero-copy

Plaintext buffer và encrypted network buffer có thể cần copy tùy implementation.

Không promise zero-copy ở semantic level.

---

# 182.70. TLS errors

Phân biệt:

```text
NetworkError
TlsError
ProtocolError
ApplicationError
```

Không gom tất cả thành một `Exception`.

---

# 182.71. Unix sockets

Unix-domain sockets:

```text
UnixStream
UnixListener
UnixDatagram
```

là platform/network library.

---

# 182.72. Windows named pipes

Không ép named pipe thành socket nếu semantics khác.

Có thể có:

```text
std::os::windows::NamedPipe
```

với generic stream traits để dùng chung abstraction.

---

# 182.73. Generic stream trait

Ví dụ:

```ax
trait Read {
    fn read(self: mut_view<Self>, buffer: mut_view<u8>)
        -> Result<usize, IoError>;
}
```

và:

```ax
trait Write { ... }
```

TCP, file, pipe, memory stream có thể implement.

---

# 182.74. Async traits

Async version có thể là:

```ax
trait AsyncRead {
    fn read_async(self: mut_view<Self>, ...)
        -> Future<Result<usize, IoError>>;
}
```

Nhưng cần tránh tạo hidden allocation.

---

# 182.75. Dynamic dispatch

Generic:

```ax
fn process<R: Read>(reader: mut_view<R>)
```

static dispatch.

Dynamic:

```ax
dyn Read
```

explicit.

---

# 182.76. No universal `Stream`

Không nên có một trait khổng lồ:

```text
Stream
Read
Write
Seek
Flush
Async
Datagram
Listener
```

tất cả trong một.

Traits compositional.

---

# 182.77. Capability-oriented networking

Ví dụ:

```text
Read
Write
Connect
Accept
Seek
Datagram
```

tách biệt.

Điều này giúp compiler và security analysis biết chính xác resource có khả năng gì.

---

# 182.78. Shutdown

TCP:

```ax
stream.shutdown(Read)?;
stream.shutdown(Write)?;
```

hoặc equivalent typed API.

Half-close phải được biểu diễn rõ.

---

# 182.79. Drop không phải graceful shutdown

`Drop(stream)` không mặc định đảm bảo:

```text
flush application protocol
send graceful close
wait peer acknowledgement
```

Drop chỉ thực hiện resource cleanup contract.

---

# 182.80. Graceful close

Nếu protocol yêu cầu:

```ax
stream.close_gracefully().await?;
```

đó là explicit operation.

---

# 182.81. Abortive close

Low-level API có thể yêu cầu:

```text
RST
```

nhưng đây là explicit platform/network semantics.

---

# 182.82. Socket options

Không nhúng mọi OS socket option vào Core.

Có:

```text
std::net
std::os::<platform>
```

và raw system APIs.

---

# 182.83. Platform-neutral options

Một số option có abstraction chung:

```text
reuse_address
reuse_port
keep_alive
receive_buffer
send_buffer
no_delay
```

Nhưng nếu OS không hỗ trợ:

```text
Result / Unsupported
```

không silent emulation.

---

# 182.84. Nonblocking

Nonblocking là implementation state.

Async abstraction không cần bắt programmer quản lý:

```text
fcntl(O_NONBLOCK)
```

---

# 182.85. Readiness registration

Runtime có thể quản lý:

```text
interest:
READABLE
WRITABLE
ERROR
HANGUP
```

nhưng application Future chỉ thấy:

```text
Pending / Ready
```

nếu abstraction đủ cao.

---

# 182.86. Level-triggered vs edge-triggered

Đây là backend concern.

Axiom API không để semantic code phụ thuộc:

```text
epoll ET
epoll LT
kqueue
```

---

# 182.87. io_uring

Axiom backend có thể dùng:

```text
io_uring
```

để thực hiện:

```text
read
write
accept
connect
send
recv
timeout
```

nhưng không expose io_uring semantics trong portable API.

---

# 182.88. IOCP

Windows backend tương tự:

```text
IOCP
```

map vào cùng Future completion model.

---

# 182.89. kqueue

macOS/BSD backend:

```text
kqueue
```

map readiness thành Future wake.

---

# 182.90. epoll

Linux readiness backend:

```text
epoll
```

tương tự.

---

# 182.91. Embedded backend

Embedded có thể:

```text
interrupt
DMA
ring buffer
NIC driver
```

không cần OS.

Đây là lý do semantic I/O phải độc lập OS.

---

# 182.92. DMA buffer

Device/network DMA có thể yêu cầu:

```text
stable address
alignment
physical accessibility
cache coherency
```

Đây là system/device contract.

Safe abstraction phải encode các yêu cầu này.

---

# 182.93. DMA ownership

Một DMA buffer đang được device sử dụng:

```text
CPU
    cannot mutate/free/relocate
```

nếu contract yêu cầu exclusive device ownership.

Đây chính là ownership/capability model được mở rộng sang device.

---

# 182.94. Device domain

Storage domain:

```text
CPU
DEVICE
SHARED
EXTERNAL
```

tương tự GPU model.

---

# 182.95. Network device buffer

Ví dụ:

```text
RxBuffer
TxBuffer
```

có ownership state:

```text
CPUOwned
DeviceOwned
Completed
```

Không cho CPU sử dụng sai state.

---

# 182.96. DMA completion

Completion event:

```text
Device
 ↓
interrupt/event
 ↓
runtime
 ↓
Future
```

phù hợp async model.

---

# 182.97. Memory barriers

DMA visibility có thể cần:

```text
cache flush
memory fence
device fence
```

Đây là system/architecture semantics, không phải ordinary atomic ordering.

---

# 182.98. Raw packet

Raw socket/packet APIs thuộc unsafe/system hoặc privileged capability.

Ví dụ:

```text
RawSocket
PacketSocket
```

không tự có safe network semantics.

---

# 182.99. Security

Network access có thể được xem là external capability:

```text
Network
```

để sandbox/application policy kiểm soát.

---

# 182.100. Comptime network

Comptime network access không được mặc định.

Nếu cho phép:

```text
comptime network
```

phải explicit capability và trở thành build dependency.

---

# 182.101. Reproducible builds

Code:

```ax
comptime {
    fetch("https://...")
}
```

không thể là hidden deterministic input.

Build system phải ghi:

```text
URL
content hash
timestamp/policy
compiler capability
```

hoặc reproducible mode từ chối.

---

# 182.102. FFI networking

Foreign library:

```text
libssl
libuv
platform socket
```

được xem là `Foreign`.

Effect/alias/ownership contract phải rõ.

---

# 182.103. Foreign buffer

Nếu C API giữ pointer sau return:

Axiom wrapper phải encode:

```text
borrow
owned
callback-retained
external lifetime
```

Không để compiler đoán.

---

# 182.104. FFI callback

Callback giữ reference tới Axiom object qua async lifetime phải có explicit ownership/handle model.

Không cho foreign code âm thầm giữ `mut_view`.

---

# 182.105. Callback thread

Nếu C library gọi callback từ arbitrary thread:

Axiom FFI contract phải khai báo execution domain.

Compiler/runtime kiểm tra:

```text
Send
Share
```

tương ứng.

---

# 182.106. Socket thread safety

Một `TcpStream` không tự động trở thành concurrently mutable-safe chỉ vì OS fd có thể được dùng từ nhiều threads.

Axiom API phải quy định capability contract.

---

# 182.107. Concurrent read

Nếu implementation cho phép concurrent reads:

có thể cung cấp explicit abstraction:

```text
SharedReadStream
```

hoặc split capability.

---

# 182.108. Concurrent read/write

Nếu một thread đọc và một thread ghi độc lập:

```text
Read capability
+
Write capability
```

có thể tồn tại đồng thời nếu socket abstraction bảo đảm điều đó.

Đây là capability-level design, không phải raw pointer aliasing.

---

# 182.109. Split socket

Một API có thể:

```ax
let (reader, writer) = stream.split();
```

sau đó:

```text
reader → Read
writer → Write
```

Ownership được chuyển thành hai capability/resource views theo contract.

---

# 182.110. Rejoin

Nếu split abstraction cho phép rejoin:

```text
reader + writer → stream
```

phải có ownership protocol rõ ràng.

Không cần nếu API không cần.

---

# 182.111. Channel vs socket

Socket:

```text
external I/O
```

Channel:

```text
in-process synchronization/communication
```

Không nhập hai semantics.

---

# 182.112. Network channel

Protocol layer có thể wrap socket thành:

```text
Channel<Message>
```

nhưng serialization/framing là explicit.

---

# 182.113. Framing

TCP application protocol cần framing:

```text
length-prefix
delimiter
fixed-size
self-describing
```

library/protocol layer quyết định.

Không thuộc socket.

---

# 182.114. Length-prefixed frame

Zero-copy parser có thể:

```text
view<u8>
 ↓
header
 ↓
payload view
```

nếu buffer còn sống.

---

# 182.115. Parser lifetime

Nếu parser trả:

```text
Message {
    payload: Str
}
```

thì `Str` phải giữ provenance tới input buffer.

Verifier đảm bảo Message không escape buffer.

---

# 182.116. Owned frame

Nếu muốn:

```text
message
```

sống độc lập:

```text
Message {
    payload: Bytes
}
```

ownership transfer/copy explicit.

---

# 182.117. Receive pipeline

High-performance server:

```text
NIC
 ↓
kernel
 ↓
DMA / socket buffer
 ↓
user buffer
 ↓
parser
 ↓
application
```

Compiler/runtime chỉ optimize các boundary mà semantics cho phép.

---

# 182.118. Kernel bypass

Future system library có thể hỗ trợ:

```text
DPDK
AF_XDP
custom NIC
```

nhưng đây là platform/system backend.

Không thay đổi networking Core semantics.

---

# 182.119. Memory mapping

Zero-copy APIs có thể dùng:

```text
mmap
shared memory
registered buffer
```

nhưng storage domain/ownership phải explicit.

---

# 182.120. Shared memory networking

IPC shared memory không phải socket semantics.

Có thể dùng:

```text
SharedMemory
RingBuffer
Channel
```

với capability/synchronization model hiện có.

---

# 182.121. Ring buffer

Một network runtime hiệu năng cao có thể dùng:

```text
SPSC ring
MPSC ring
MPMC ring
```

đã phù hợp concurrency model.

---

# 182.122. Batch I/O

API có thể hỗ trợ:

```text
recv_batch
send_batch
accept_batch
```

để giảm syscall overhead.

---

# 182.123. Batch semantic

Batch API phải preserve từng operation's:

```text
result
ownership
buffer capability
error
```

Không gom thành một opaque blob.

---

# 182.124. Syscall batching

Backend có thể map:

```text
multiple logical operations
```

vào:

```text
one kernel submission
```

mà không thay đổi semantics.

---

# 182.125. Completion ordering

Không assume completion order bằng submission order.

Nếu application yêu cầu ordering:

```text
sequence number
dependency
await
```

phải explicit.

---

# 182.126. Cancellation race

Ví dụ:

```text
submit I/O
cancel
completion arrives
```

có thể xảy ra:

```text
Cancelled
Completed
AlreadyCompleted
```

API phải có deterministic observation semantics.

---

# 182.127. Cancellation không rollback I/O

Cancel request không có nghĩa OS đã undo operation.

Có thể chỉ có nghĩa:

```text
caller no longer awaits result
```

backend contract quyết định.

---

# 182.128. Resource cleanup

Nếu operation bị cancel:

```text
Future Drop
```

phải release logical resources đúng ownership semantics.

Underlying OS operation nếu chưa dừng phải có mechanism giữ resource cần thiết.

---

# 182.129. No detached hidden I/O

Axiom không nên để:

```text
drop(future)
```

âm thầm tạo một detached background I/O operation mà programmer không biết.

Nếu detach cần:

```text
detach()
```

explicit.

---

# 182.130. Async socket lifetime

```text
socket
 ↓
operation
 ↓
future
```

Nếu Future owns socket:

Drop Future có thể close socket theo contract.

Nếu socket borrowed:

Future không được outlive socket.

Verifier kiểm tra.

---

# 182.131. Async listener

Listener Future phải giữ:

```text
listener capability
```

cho tới completion.

---

# 182.132. Server architecture

Axiom có thể viết:

```ax
loop {
    let connection = listener.accept_async().await?;
    spawn(handle(connection));
}
```

và semantics:

```text
accept
 → ownership transfer
 → spawn requires Send
```

rất tự nhiên với concurrency model đã có.

---

# 182.133. Connection task

`TcpStream` được Move vào task:

```text
spawn(handle(connection))
```

Không cần Arc nếu chỉ một task sở hữu connection.

Đây là một điểm mạnh của ownership model.

---

# 182.134. Shared connection

Nếu nhiều tasks thực sự cần dùng:

```text
Arc<...>
```

hoặc explicit split/read-write capability.

Không implicit shared ownership.

---

# 182.135. Protocol task

Ví dụ:

```text
Connection
 ├── Reader task
 └── Writer task
```

có thể dùng split capability.

---

# 182.136. Backpressure channels

Writer queue:

```text
bounded channel
```

để tránh memory tăng vô hạn.

Channel semantics đã có từ concurrency model.

---

# 182.137. Network buffer ownership chain

Mô hình khuyến nghị:

```text
NIC/Kernel
   ↓
Buffer
   ↓ Move
Parser
   ↓ Move
Application
   ↓ Move
Response
   ↓
Socket
```

Không cần copy nếu abstraction cho phép.

---

# 182.138. `Bytes` vs `String`

Network protocols mặc định:

```text
Bytes
```

Text protocol mới chuyển:

```text
Bytes → Str
```

sau validation.

---

# 182.139. Network errors

Nên phân loại:

```text
IoError
 ├── WouldBlock
 ├── Interrupted
 ├── Closed
 ├── Timeout
 ├── ConnectionRefused
 ├── ConnectionReset
 ├── AddressInUse
 ├── NetworkUnreachable
 └── Other
```

Platform-specific raw error vẫn có thể lấy qua `std::os`.

---

# 182.140. Error identity

Không phụ thuộc string message.

Error nên có:

```text
ErrorKind
OS error code
source
context
```

---

# 182.141. Retryability

Không phải mọi network error đều retryable.

Có thể có:

```text
is_retryable()
```

nhưng đây là policy/helper, không phải semantic guarantee cho mọi protocol.

---

# 182.142. Timeout classification

Timeout có thể là:

```text
DeadlineExpired
```

khác:

```text
ConnectionReset
```

---

# 182.143. DNS failure

DNS errors không phải socket errors mặc dù cuối cùng đều là network operation.

---

# 182.144. Protocol error

HTTP `400` chẳng hạn không phải `IoError`.

Protocol/application layers quyết định.

---

# 182.145. HTTP không thuộc Core

HTTP library:

```text
std::http
```

có thể xây trên:

```text
TcpStream
TlsStream
AsyncRead/Write
```

---

# 182.146. QUIC

QUIC cũng không thuộc Core.

Có thể xây:

```text
UDP
+
TLS
+
protocol implementation
```

và sử dụng concurrency/async primitives.

---

# 182.147. Network abstraction hierarchy

```text
std::net
├── Address
├── Tcp
├── Udp
├── Unix
└── Raw

std::io
├── Read
├── Write
├── AsyncRead
├── AsyncWrite
├── IoVec
└── Buffer

higher libraries
├── TLS
├── HTTP
├── DNS
├── QUIC
└── RPC
```

---

# 182.148. File/network unified I/O

`Read` / `Write` abstractions cho phép:

```text
File
TcpStream
Pipe
MemoryStream
TLS
Compression
```

cùng ecosystem.

Nhưng semantic capabilities vẫn riêng.

---

# 182.149. Compression layer

Ví dụ:

```text
TcpStream
 ↓
TlsStream
 ↓
CompressionStream
 ↓
BufferedStream
 ↓
Application
```

Compiler có thể inline/fuse generic layers.

---

# 182.150. Zero-cost layered I/O

Nếu tất cả đều static generic:

```ax
fn process<S: AsyncRead + AsyncWrite>(stream: mut_view<S>)
```

thì abstraction layers có thể biến mất sau:

```text
inlining
specialization
devirtualization
DCE
```

Không cần virtual interface cho từng layer.

---

# 182.151. Buffering

`BufferedReader`/`BufferedWriter` là library abstraction.

Compiler không bắt buộc allocation.

Có thể stack-inline buffer nếu escape analysis cho phép.

---

# 182.152. Small buffers

Compiler có thể scalarize hoặc stack allocate:

```text
Array<u8, 4096>
```

nếu không escape.

---

# 182.153. Large buffers

Compiler/runtime có thể chọn:

```text
heap
arena
pool
registered memory
```

theo storage contract.

---

# 182.154. Network vectorization

Network processing loop có thể được auto-vectorized nếu:

```text
alias safe
range safe
effects safe
```

Không cần programmer viết SIMD.

---

# 182.155. Packet batch processing

Compiler có thể kết hợp:

```text
parse packet
+
validate
+
transform
```

nếu semantics cho phép.

---

# 182.156. I/O effect system

I/O function có:

```text
IO
ExternalState
```

effects.

Optimizer không được coi nó là pure.

---

# 182.157. I/O and MemorySSA

Foreign/IO operations là memory/external barriers theo effect contract.

Nếu API biết chỉ đọc network resource mà không mutate local memory, optimizer vẫn có thể giữ local facts.

---

# 182.158. Foreign calls

Unknown foreign call:

```text
Foreign
```

conservative.

Verified FFI contract có thể giảm invalidation.

---

# 182.159. Network syscall elimination

Compiler không tự loại:

```text
send()
send()
```

chỉ vì cùng arguments.

IO là observable effect.

---

# 182.160. Duplicate reads

Không merge:

```text
read(socket)
read(socket)
```

vì external state thay đổi.

---

# 182.161. Async poll optimization

Executor có thể tối ưu:

```text
poll
Pending
wake
poll
```

nhưng không được bỏ wake/completion semantics.

---

# 182.162. Waker semantics

Waker:

```text
notification
```

không phải guarantee task state changed in a specific way.

Future phải kiểm tra condition khi poll.

---

# 182.163. Spurious wake

Backend/runtime có thể wake task mà chưa Ready.

Future phải:

```text
poll
→ Pending
```

lại.

---

# 182.164. I/O readiness race

Classic pattern:

```text
check readiness
yield
perform I/O
```

không được assume readiness remains true.

Async backend phải xử lý race.

---

# 182.165. Level of abstraction

Axiom có ba mức:

```text
High-level:
TcpStream

Mid-level:
AsyncRead / IoBackend

Low-level:
RawSocket / OS API / syscall
```

---

# 182.166. Safe boundary

Safe APIs đảm bảo:

```text
ownership
buffer validity
capability lifetime
resource cleanup
```

Low-level raw socket APIs có thể yêu cầu `unsafe`.

---

# 182.167. No unsafe for normal networking

Application developer không cần:

```text
unsafe
```

để viết TCP server/client.

Unsafe chỉ khi:

```text
raw syscall
custom driver
DMA
kernel bypass
foreign memory
```

---

# 182.168. Socket address parsing

String:

```text
"127.0.0.1:8080"
```

phải parse thành:

```text
SocketAddr
```

không phải được compiler tự coi là address.

---

# 182.169. Endpoint identity

`SocketAddr` là value.

Socket resource identity là khác.

Không dùng address equality để xác định socket object identity.

---

# 182.170. Logical connection identity

Application có thể dùng:

```text
ConnectionId
```

nếu cần tracking.

Không dùng memory address.

---

# 182.171. Network handles

OS handle:

```text
RawSocket
```

không phải logical connection ID.

Ba concepts:

```text
resource identity
logical identity
memory identity
```

vẫn tách biệt như memory model.

---

# 182.172. Resource duplication

OS có thể duplicate socket handle.

Axiom phải phân biệt:

```text
duplicate OS handle
```

với:

```text
clone Socket ownership
```

Không cho `Socket: Copy`.

Nếu duplicate cần:

```ax
let second = socket.try_clone()?;
```

và semantics được định nghĩa.

---

# 182.173. Shared OS handle

Nếu hai Axiom Socket objects cùng OS resource:

phải là explicit shared ownership/handle semantics.

Không tạo implicit alias.

---

# 182.174. Socket Drop

Drop phải close/release resource ownership mà object sở hữu.

Nếu underlying OS resource đã transferred:

object trở thành moved/invalid.

---

# 182.175. Double close

Ownership verifier + resource state phải ngăn double semantic destruction.

---

# 182.176. Close errors

`Drop` không trả Result.

Nếu close có thể fail observably:

```ax
socket.close() -> Result<(), Error>
```

là explicit.

Drop vẫn đảm bảo cleanup contract tốt nhất theo platform.

---

# 182.177. Flush semantics

`flush()` không đồng nghĩa:

```text
data physically reached remote application
```

Network stack may buffer.

Protocol-specific acknowledgement mới chứng minh application-level delivery.

---

# 182.178. `shutdown` semantics

TCP shutdown cũng không đồng nghĩa peer đã processed all data.

API docs phải phân biệt:

```text
local shutdown
kernel accepted
peer observed
application acknowledged
```

---

# 182.179. Keepalive

TCP keepalive là OS/network policy.

Không phải application-level heartbeat.

---

# 182.180. Heartbeat

Application protocol heartbeat là:

```text
protocol-level message
```

khác TCP keepalive.

---

# 182.181. Security boundary

Network APIs phải cho phép policy layer giới hạn:

```text
allowed domains
ports
interfaces
protocols
```

nhưng đây là sandbox/runtime capability, không hardcode vào language.

---

# 182.182. Package/runtime capability

Application manifest có thể khai báo:

```text
network
filesystem
```

Nếu target sandbox hỗ trợ.

Compiler/linker có thể đưa capability requirements vào metadata.

---

# 182.183. `.axmeta`

Network-related metadata có thể chứa:

```text
required runtime components
required platform capabilities
FFI dependencies
async requirements
target-specific APIs
```

Không cần chứa runtime state.

---

# 182.184. Static linking

Một TCP application chỉ dùng:

```text
std::net::Tcp
```

có thể link:

```text
network runtime
```

nếu cần.

Không link:

```text
GPU
Unicode
reflection
```

nếu không dùng.

---

# 182.185. Freestanding networking

Embedded program có thể:

```text
std::net::driver
```

mà không có OS.

Driver cung cấp `IoBackend`.

---

# 182.186. Network backend trait

Conceptually:

```ax
trait IoDriver {
    fn submit(...);
    fn poll(...);
}
```

Nhưng đây là runtime/library internal API, không nhất thiết public Core trait.

---

# 182.187. Driver ownership

I/O driver owns:

```text
OS event queue
completion queue
registered resources
```

và Drop phải shutdown đúng lifecycle.

---

# 182.188. Executor lifecycle

```text
Runtime
 ↓
IoDriver
 ↓
Executor
 ↓
Tasks
```

có thể được tạo/Destroy explicit.

Không có global executor bắt buộc.

---

# 182.189. Multiple executors

Một process có thể có nhiều executors.

Socket/task phải có contract nếu resource chỉ được registered với một driver.

---

# 182.190. Migration

Future có thể migrate executor/thread nếu:

```text
Send
storage
I/O backend contract
```

cho phép.

Một future giữ backend-specific pinned resource có thể bị giới hạn execution domain.

---

# 182.191. Socket task Send

Một `TcpStream` chỉ được gửi sang task khác nếu abstraction khai báo `Send`.

Thông thường owned socket có thể Send, nhưng concurrent mutable use vẫn phải được kiểm soát.

---

# 182.192. Async I/O and Send

Future containing:

```text
socket
buffer
```

có thể là Send nếu tất cả state là Send và backend contract cho phép.

---

# 182.193. No automatic thread safety

`Send` không có nghĩa:

```text
can concurrently mutate
```

nó chỉ có nghĩa ownership có thể chuyển execution domain.

---

# 182.194. Async I/O and Share

Socket sharing phải explicit.

Ví dụ:

```text
Arc<Socket>
```

không tự biến socket operations thành thread-safe mutable operations.

---

# 182.195. Connection pooling

Pool:

```text
ConnectionPool
```

là library abstraction.

Ownership model có thể quản lý connection lease:

```text
Pool
 ↓
ConnectionLease
 ↓
return to pool
```

---

# 182.196. Lease lifetime

Lease không cần programmer lifetime syntax.

Compiler theo dõi capability dependency:

```text
pool owner
    ↓
lease capability
```

---

# 182.197. Pool return

Drop lease có thể trả connection về pool nếu semantics của pool cho phép.

Đây là resource Drop, không phải memory deallocation.

---

# 182.198. Connection pool cancellation

Nếu task bị cancellation trong lúc giữ lease:

Drop phải trả lease hoặc close connection theo pool policy.

---

# 182.199. Network transactions

Không nên gọi TCP write là transaction.

Application protocol transaction phải tự định nghĩa.

---

# 182.200. Core conclusion

Axiom networking cuối cùng có mô hình:

```text
                    Network
                       │
              ┌────────┴────────┐
              │                 │
           Socket             Address
              │
       ┌──────┼──────┐
       │      │      │
      TCP    UDP    Unix
       │
    Stream
       │
 ┌─────┴─────────┐
 │               │
Read/Write    Async I/O
 │               │
Bytes/View     Future
 │               │
 │         IoBackend
 │       ┌───────┼────────┐
 │     io_uring IOCP    kqueue
 │       │       │         │
 └───────┴───────┴─────────┘
             │
          Executor
             │
       Cancellation
       Deadline/Timer
```

Điểm quan trọng nhất:

> **Axiom không thiết kế “API cho epoll/io_uring/IOCP”. Axiom thiết kế một semantic I/O model đủ thấp để map hiệu quả xuống tất cả chúng.**

---

# 182.201. Invariants

### Socket / Resource

- **ANET-20** — Socket objects are owned resources, not plain integers.
- **ANET-21** — Socket ownership is move-based and non-copyable by default.
- **ANET-22** — Raw OS socket handles do not imply ownership or safe capability.
- **ANET-23** — Socket destruction is deterministic.
- **ANET-24** — Resource duplication is explicit.
- **ANET-25** — Logical connection identity is distinct from OS handle identity and memory identity.

### Buffer / Memory

- **ANET-30** — Network payloads are bytes by default, not text.
- **ANET-31** — UTF-8 interpretation is explicit.
- **ANET-32** — Buffer capabilities remain valid for the required lifetime of an I/O operation.
- **ANET-33** — In-flight asynchronous I/O prevents invalid relocation/destruction of required storage.
- **ANET-34** — Concurrent mutable access to the same buffer is rejected unless explicitly synchronized.
- **ANET-35** — Proven-disjoint buffers may participate in concurrent operations.
- **ANET-36** — Zero-copy is an optimization unless explicitly contracted.
- **ANET-37** — Scatter/gather APIs preserve individual buffer ownership/capability semantics.

### Async I/O

- **ANET-40** — Async I/O is represented as Future-based suspension, not implicit threads.
- **ANET-41** — Readiness and completion are backend mechanisms, not distinct language semantics.
- **ANET-42** — `Pending` does not imply completion.
- **ANET-43** — Wake notification does not imply readiness without rechecking.
- **ANET-44** — I/O cancellation does not imply rollback of external operations.
- **ANET-45** — Dropping a Future does not implicitly create detached background work.
- **ANET-46** — In-flight operations retain all required resource capabilities.
- **ANET-47** — Timeout and cancellation remain distinct.
- **ANET-48** — I/O completion order is not assumed to equal submission order.

### Backend

- **ANET-50** — Portable networking semantics do not depend on POSIX.
- **ANET-51** — `epoll`, `kqueue`, `IOCP`, `io_uring` and embedded interrupt/DMA mechanisms are backend implementations.
- **ANET-52** — Backend replacement cannot alter observable portable I/O semantics.
- **ANET-53** — Backend-specific capabilities may be exposed only through explicit system APIs.
- **ANET-54** — Unknown foreign I/O calls remain conservative in compiler analysis.

### Ownership / Concurrency

- **ANET-60** — Send is distinct from Share.
- **ANET-61** — Socket ownership transfer across tasks uses Move.
- **ANET-62** — Shared sockets require explicit synchronization or capability splitting.
- **ANET-63** — Async I/O does not itself establish memory synchronization.
- **ANET-64** — Device/DMA ownership follows the same ownership/capability principles as CPU memory.
- **ANET-65** — DMA buffers cannot be relocated or accessed incompatibly while owned by a device.

### Protocol

- **ANET-70** — TCP is a byte stream and does not provide application message boundaries.
- **ANET-71** — Datagram APIs preserve datagram semantics.
- **ANET-72** — Framing is an explicit protocol-layer concern.
- **ANET-73** — TLS, HTTP, QUIC and RPC are library/protocol layers, not Core socket semantics.
- **ANET-74** — Protocol/application acknowledgement is distinct from local socket write completion.

### Runtime / Security

- **ANET-80** — Async networking runtime is optional.
- **ANET-81** — Network capability requirements can be represented in package/runtime metadata.
- **ANET-82** — Freestanding targets may provide custom I/O drivers without an OS.
- **ANET-83** — Comptime network access requires explicit external capability.
- **ANET-84** — Network-dependent comptime inputs participate in build identity.
- **ANET-85** — Safe application networking must not require unsafe code.
- **ANET-86** — Raw packet, DMA, kernel-bypass and arbitrary foreign-memory APIs are explicit system/unsafe boundaries.

---

# Trạng thái kiến trúc sau BOOTSTRAP-182

Axiom hiện đã có một chuỗi khá hoàn chỉnh:

```text
Memory
  ↓
Ownership
  ↓
Capability
  ↓
Alias
  ↓
Effect
  ↓
Escape
  ↓
Concurrency
  ↓
Async
  ↓
Time
  ↓
I/O
  ↓
Networking
```

Điểm đáng chú ý là **networking không cần thêm một hệ thống memory-safety mới**. Nó tái sử dụng chính các primitive đã thiết kế:

```text
Move
view
mut_view
Drop
Send
Share
Future
Deadline
Cancellation
Effect
Storage Domain
Execution Domain
```

Đây chính là dấu hiệu kiến trúc đang đi đúng hướng: thêm subsystem nhưng không phải liên tục tạo ra các cơ chế ngôn ngữ mới.

## Task kế tiếp

**BOOTSTRAP-183 — Filesystem, Paths, File I/O, Memory Mapping & Storage Abstractions**

Sẽ chốt:

```text
File
Directory
Path
OsPath
FileHandle
OpenOptions
permissions
metadata
atomic rename
temporary files
memory-mapped files
mmap/VirtualAlloc
direct I/O
buffered I/O
async file I/O
file locking
advisory vs mandatory locking
sparse files
random access
sequential access
filesystem capabilities
cross-platform Windows/Linux/macOS semantics
```

và đặc biệt sẽ quyết định **Axiom nên mô hình hóa `File` như resource thuần túy hay tách `File`, `FileView`, `MappedRegion`, `Storage` thành các capability khác nhau** để vừa đơn giản cho lập trình viên vừa cho phép compiler tối ưu mmap/direct-I/O/zero-copy.