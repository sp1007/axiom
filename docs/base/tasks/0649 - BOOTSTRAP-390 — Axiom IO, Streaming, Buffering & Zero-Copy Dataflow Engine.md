# BOOTSTRAP-390 — Axiom I/O, Streaming, Buffering & Zero-Copy Dataflow Engine

Sau **389 — Data-Oriented Runtime, Storage Layout & Automatic Data Structure Optimization**, bước tiếp theo nên giải quyết một vấn đề cực kỳ quan trọng đối với mục tiêu của Axiom:

> **Dữ liệu đi vào và đi ra khỏi chương trình phải có thể chảy qua CPU, memory, GPU, network, file và device mà không bị ép copy qua nhiều lớp abstraction.**

Điều này đặc biệt quan trọng với:

- video/audio;
- AI inference;
- database;
- network server;
- scientific simulation;
- GPU pipeline;
- distributed computing;
- compiler/toolchain;
- realtime systems.

Mục tiêu của 390 là xây dựng **I/O semantic model**, không phải đưa toàn bộ OS API vào Core.

---

# 1. I/O không nên đồng nghĩa với File

Axiom cần phân biệt:

```text
File
Socket
Pipe
Device
Stream
MemoryBuffer
Channel
MappedMemory
```

Tất cả đều có thể là nguồn/đích dữ liệu, nhưng semantics khác nhau.

---

# 2. Dataflow Model

Mô hình tổng quát:

```text
Source
  ↓
Buffer
  ↓
Transform
  ↓
Buffer
  ↓
Sink
```

Ví dụ:

```text
Camera
  ↓
DMA Buffer
  ↓
GPU
  ↓
Tensor
  ↓
Encoder
  ↓
Network
```

Không nên bắt buộc:

```text
Camera
→ CPU copy
→ temporary object
→ GPU copy
→ temporary object
```

---

# 3. Stream là Semantic Abstraction

Đề xuất abstraction:

```text
Stream<T>
```

nhưng `Stream<T>` không nhất thiết là object runtime nặng.

Nó có thể đại diện cho:

```text
file
socket
pipe
device
memory producer
async source
```

---

# 4. Byte Stream vs Typed Stream

Phân biệt:

```text
ByteStream
```

và:

```text
Stream<T>
```

`ByteStream` truyền raw bytes.

`Stream<T>` truyền typed values.

---

# 5. Không Serialization ngầm

Nếu:

```text
Stream<Packet>
```

đi qua network, compiler không được tự giả định serialization format.

Cần explicit:

```text
encode
decode
```

hoặc một protocol contract.

---

# 6. Buffer

Buffer là vùng storage có:

```text
pointer/storage
capacity
length
alignment
ownership
storage domain
```

nhưng các metadata này chỉ tồn tại runtime khi cần.

---

# 7. Buffer Ownership

Ví dụ:

```text
Buffer<u8>
```

là owning value.

Khi truyền:

```text
send(buffer)
```

có thể chuyển ownership thay vì copy.

---

# 8. Buffer View

```text
view<u8>
```

cho phép đọc mà không chuyển ownership.

```text
mut_view<u8>
```

cho phép ghi độc quyền.

Memory model hiện tại của Axiom áp dụng trực tiếp.

---

# 9. Scatter/Gather I/O

API phải hỗ trợ:

```text
write([
    header,
    payload,
    trailer
])
```

mà không cần concatenate thành một buffer mới.

Physical implementation có thể sử dụng:

```text
writev
sendmsg
DMA descriptors
```

---

# 10. Gather Read

Tương tự:

```text
read_into([
    header_buffer,
    payload_buffer
])
```

nếu backend hỗ trợ.

---

# 11. Zero-Copy

Zero-copy là optimization contract, không phải lời hứa rằng mọi I/O đều zero-copy.

Compiler/runtime có thể loại bỏ copy nếu:

```text
ownership
layout
alignment
storage domain
lifetime
ABI
```

cho phép.

---

# 12. Copy Elimination

Ví dụ:

```text
read(buffer)
process(buffer)
send(buffer)
```

có thể trở thành:

```text
DMA → process → DMA
```

nếu ownership được chuyển xuyên pipeline.

---

# 13. Copy là Observable Khi Nào?

Copy trở thành observable nếu có:

- mutable alias;
- address observation;
- external device contract;
- synchronization;
- cache/coherency semantics;
- explicit copy semantics.

Nếu không, compiler được phép loại bỏ.

---

# 14. Async I/O

I/O thường có:

```text
Pending
Ready
Error
```

nên tích hợp trực tiếp với Future:

```text
async read(...)
async write(...)
```

nhưng:

> `async` không đồng nghĩa kernel async I/O.

Backend có thể dùng:

```text
io_uring
IOCP
kqueue
epoll
blocking worker
polling
DMA
```

---

# 15. Blocking Effect

Compiler phải biết function:

```text
may_block
nonblocking
async
```

để tránh:

```text
async task
    ↓
blocking syscall
```

làm nghẽn executor.

---

# 16. Explicit Blocking

Một API blocking có thể mang effect:

```text
BLOCKING
```

Compiler diagnostic có thể cảnh báo khi gọi từ async context.

---

# 17. Buffer Lifetime Across Async

Ví dụ:

```text
await read_into(buffer)
```

`buffer` phải tồn tại xuyên suspension.

Compiler ownership analysis đảm bảo điều đó.

---

# 18. Borrow Across Async I/O

Nếu:

```text
view(buffer)
```

được backend giữ lại sau khi function return, compiler phải biết API contract.

Không cho phép một `view` ephemeral bị lưu vào I/O operation lâu hơn owner.

---

# 19. Registered Buffers

Một số OS/API yêu cầu buffer registration.

Axiom có thể có:

```text
RegisteredBuffer<T>
```

nhưng registration lifetime phải explicit.

---

# 20. DMA Memory

DMA là storage contract:

```text
DmaBuffer<T>
```

có thể yêu cầu:

```text
alignment
physical accessibility
pinning
cache coherence
device ownership
```

Không nên biến DMA buffer thành một loại pointer đặc biệt của Core.

---

# 21. Device I/O

Execution/storage domains hiện có:

```text
CPU
GPU
DEVICE
```

có thể dùng chung I/O framework.

Ví dụ:

```text
camera → GPU buffer
```

không nhất thiết qua host RAM.

---

# 22. Memory-Mapped I/O

File/device có thể map thành memory:

```text
map<T>()
```

nhưng semantics khác ordinary memory.

Cần contract:

```text
MappedRegion<T>
```

với:

```text
flush
sync
unmap
```

---

# 23. Mapped Memory không phải Ownership đơn giản

`mmap` có lifetime gắn với OS resource.

Compiler phải theo dõi:

```text
mapping lifetime
file/device lifetime
view lifetime
```

---

# 24. File

File abstraction cần phân biệt:

```text
FileHandle
FileRegion
FileMetadata
MappedFile
```

File descriptor/OS handle là resource.

Không được Copy semantic nếu nó sở hữu resource.

---

# 25. File Offset

File offset là state observable.

Concurrent reads phải có semantics rõ:

```text
shared offset
independent offset
positional read
```

Compiler không được tự thay đổi giữa chúng nếu observable.

---

# 26. Positional I/O

API:

```text
read_at(offset, buffer)
write_at(offset, buffer)
```

cho phép concurrent access mà không cần shared file cursor.

Đây cũng là abstraction tốt cho parallel I/O.

---

# 27. Direct I/O

Storage backend có thể yêu cầu:

```text
alignment
block size
buffer constraints
```

Các yêu cầu này nên là compile/runtime contracts.

---

# 28. Buffered I/O

Buffering là optimization layer:

```text
Application
 ↓
Axiom Buffer
 ↓
Buffered I/O
 ↓
OS
```

Compiler có thể hợp nhất buffer nếu semantics không thay đổi.

---

# 29. Flush Semantics

Phải phân biệt:

```text
flush buffer
sync OS
persist storage
```

Không dùng một `flush()` mơ hồ cho tất cả.

---

# 30. Durability

`write()` thành công không nhất thiết nghĩa:

```text
data physically persistent
```

Cần semantics:

```text
flush
sync
durable
```

theo backend.

---

# 31. Socket

Socket là I/O resource:

```text
Socket<TProtocol>
```

hoặc byte-level:

```text
TcpStream
UdpSocket
```

nhưng protocol semantics nằm ở library.

---

# 32. TCP Stream

TCP:

```text
byte stream
```

không có message boundary.

Axiom không được tạo illusion rằng mỗi `write()` tương ứng một `read()`.

---

# 33. Datagram

UDP có message boundary.

Semantic type phải giữ boundary:

```text
Datagram
```

---

# 34. Backpressure

Streaming pipeline cần:

```text
producer
    ↓
bounded buffer
    ↓
consumer
```

Nếu consumer chậm:

```text
producer → Pending
```

thay vì memory tăng vô hạn.

---

# 35. Bounded Stream

Đây là phần quan trọng cho server/video/AI:

```text
Stream<T, Capacity=N>
```

có thể compile-time biết capacity.

---

# 36. Ring Buffer

Compiler/library có thể sử dụng:

```text
RingBuffer<T,N>
```

cho:

- audio;
- network;
- sensor;
- realtime;
- IPC.

Nếu N static, toàn bộ metadata có thể được tối ưu.

---

# 37. Single Producer / Single Consumer

SP/SC ring buffer có semantics khác MPMC.

Compiler có thể exploit:

```text
SPSC
MPSC
SPMC
MPMC
```

để giảm synchronization.

---

# 38. Lock-Free

Lock-free không nên là semantic requirement mặc định.

Có thể có:

```text
LockFreeQueue<T>
```

với target-specific implementation.

Nếu target không hỗ trợ lock-free primitive, library có thể fallback hoặc reject theo contract.

---

# 39. I/O + Channels

Channel:

```text
producer
 ↓
Channel<T>
 ↓
consumer
```

và Stream:

```text
source
 ↓
Stream<T>
```

nên interoperable.

Ví dụ:

```text
socket
    → decode
    → channel
    → worker
```

không cần copy dữ liệu nhiều lần.

---

# 40. Pipeline

Axiom nên có semantic pipeline:

```text
source
 |> transform
 |> filter
 |> batch
 |> sink
```

nhưng đây nên là library/compiler abstraction, không phải macro magic.

---

# 41. Pipeline Fusion

Ví dụ:

```text
read
→ decode
→ normalize
→ filter
→ write
```

compiler có thể fuse các bước pure.

---

# 42. Streaming Fusion

Compiler phải phân biệt:

```text
element-wise
batch-wise
windowed
stateful
```

để biết transformation nào có thể fuse.

---

# 43. Window

Streaming algorithms thường cần:

```text
window
tumbling window
sliding window
session window
```

đây là library semantics.

---

# 44. Chunking

I/O thường xử lý chunk:

```text
64 KB
1 MB
4 MB
```

Compiler/runtime có thể auto-tune chunk size dựa trên:

```text
latency
bandwidth
cache
device
network
```

---

# 45. Scatter/Gather + GPU

Pipeline:

```text
network
 ↓
scatter
 ↓
GPU buffers
 ↓
kernel
```

có thể tránh intermediate CPU copies.

---

# 46. File → Tensor

Một mục tiêu quan trọng:

```text
file
 ↓
mapped/streamed buffer
 ↓
TensorView
```

nếu format/layout tương thích.

Không cần deserialize thành object trung gian.

---

# 47. Network → Tensor

Tương tự:

```text
network packet
 ↓
buffer
 ↓
TensorView
```

nếu protocol đảm bảo:

```text
dtype
shape
layout
alignment
endianness
```

---

# 48. Endianness

Wire data phải có explicit byte order:

```text
LittleEndian
BigEndian
NativeEndian
```

Không để machine endian tự quyết định protocol.

---

# 49. Typed Binary Format

Có thể xây:

```text
BinaryReader<T>
BinaryWriter<T>
```

dựa trên:

```text
@repr
endianness
alignment
field encoding
```

nhưng serialization phải là explicit semantic boundary.

---

# 50. Text I/O

Text không nên đồng nhất với bytes.

Axiom có:

```text
ByteStream
TextStream
```

TextStream có encoding:

```text
UTF-8
UTF-16
UTF-32
```

UTF-8 là default.

---

# 51. Incremental Decoder

Streaming UTF-8 decoder phải xử lý trường hợp:

```text
chunk 1: partial codepoint
chunk 2: remainder
```

mà không tạo invalid text.

---

# 52. Error Semantics

I/O error phải có category:

```text
WouldBlock
Timeout
Closed
Interrupted
Permission
NotFound
InvalidData
ProtocolError
DeviceError
TransportError
```

Không ép tất cả thành integer errno.

---

# 53. Retry

I/O retry không tự động.

Compiler/runtime chỉ retry khi contract cho phép.

Ví dụ:

```text
read
```

có thể retry transient interruption.

Nhưng:

```text
write payment
```

không được tự retry nếu side effect semantics không rõ.

---

# 54. Timeout

Timeout là semantic property của operation:

```text
await read(..., timeout)
```

không phải một thread kill.

Cancellation và timeout phải phối hợp với Future semantics đã frozen.

---

# 55. Deadline

Ngoài timeout tương đối:

```text
deadline
```

có thể propagate qua nested async calls.

---

# 56. Cancellation

I/O cancellation cần backend contract.

Ví dụ:

```text
cancel(read)
```

có thể:

- cancel syscall;
- close operation;
- stop polling;
- mark result cancelled.

Không mặc định assume physical I/O đã dừng.

---

# 57. I/O Completion

Completion object có thể:

```text
IoEvent
```

tương tự:

```text
GpuEvent
Task
Future
```

nhưng semantics riêng.

---

# 58. Event-driven I/O

Một executor có thể integrate:

```text
Future
+
IoEvent
+
GpuEvent
+
Timer
```

thành một event loop.

Đây là runtime policy.

---

# 59. Timer

Timer là một I/O/event source:

```text
sleep
timeout
deadline
interval
```

Không cần thread per timer.

---

# 60. Unified Event Source

Conceptually:

```text
EventSource
 ├── Socket
 ├── File
 ├── Timer
 ├── Process
 ├── GPU
 ├── Device
 └── Task
```

nhưng không nhất thiết phải tạo runtime inheritance hierarchy.

Traits + enums + generic contracts là đủ.

---

# 61. Process I/O

Process:

```text
stdin
stdout
stderr
```

có thể là streams.

Pipeline:

```text
process A stdout
       ↓
     buffer
       ↓
process B stdin
```

---

# 62. IPC

Các abstraction:

```text
Pipe
SharedMemory
Socket
Channel
MappedRegion
```

có thể dùng chung buffer/ownership semantics.

---

# 63. Shared Memory IPC

Shared memory là:

```text
StorageDomain = SHARED_PROCESS
```

và cần synchronization.

Compiler không được giả định process-local ownership như ordinary stack memory.

---

# 64. External Memory

Memory do bên ngoài quản lý:

```text
ExternalBuffer<T>
```

cần contract:

```text
owner
release
alignment
size
storage domain
lifetime
```

---

# 65. External Device Buffers

Camera/decoder/GPU/OS buffer có thể được import:

```text
import_external_buffer(...)
```

nhưng phải có explicit ownership contract.

---

# 66. Ownership Transfer

Ví dụ:

```text
OS buffer
   ↓ import
Axiom owns
   ↓
GPU
```

ownership transition phải được compiler/runtime ghi nhận.

---

# 67. Borrowed External Buffer

Nếu OS vẫn owns:

```text
view<T>
```

chỉ hợp lệ trong external lifetime.

Không được lưu view vượt quá callback/operation.

---

# 68. Callback I/O

Một số APIs callback-based.

Compiler cần bridge:

```text
callback
→ Future
```

nhưng callback phải giữ ownership/capture semantics.

---

# 69. Reentrancy

I/O callbacks có thể re-enter application.

Compiler/runtime contract phải mô tả:

```text
reentrant
non-reentrant
single-threaded
thread-safe
```

---

# 70. I/O Effect System

Effect system bổ sung:

```text
IO_READ
IO_WRITE
NETWORK
FILE
DEVICE
BLOCKING
ASYNC_IO
```

Nhưng không bắt programmer annotate mọi function thủ công nếu compiler có thể infer.

---

# 71. Pure Function Boundary

Một function:

```text
fn parse(bytes) -> Packet
```

nên vẫn pure.

Còn:

```text
fn read(stream) -> Packet
```

có `IO_READ`.

Điều này giúp optimizer biết phần nào có thể fuse.

---

# 72. I/O Ordering

Hai I/O:

```text
write(A)
write(B)
```

không được reorder nếu external observer có thể thấy ordering.

Nếu backend contract cho phép reorder:

```text
independent I/O
```

compiler có thể pipeline.

---

# 73. I/O Memory Ordering

Cần phân biệt:

```text
CPU memory ordering
```

với:

```text
device I/O ordering
```

và:

```text
persistent storage ordering
```

Ba loại không được đánh đồng.

---

# 74. Device Fence

GPU/device I/O có thể cần:

```text
device_fence
dma_fence
io_fence
```

Compiler phải biết dependency nhưng không nên expose tất cả machine details trong Core.

---

# 75. Dataflow Graph

I/O pipeline có thể được compiler biểu diễn:

```text
I/O Graph
```

node:

```text
Read
Decode
Transform
Compute
Encode
Write
```

edge:

```text
ownership
dependency
buffer
event
```

---

# 76. Buffer Lifetime Optimization

Compiler có thể nhận:

```text
buffer A
 ↓
decode
 ↓
transform
```

và reuse storage:

```text
buffer A
 ↓ reuse
transform output
```

nếu lifetime/capability proof cho phép.

---

# 77. Double Buffering

Streaming pipeline có thể tự động:

```text
Buffer A → GPU
Buffer B → CPU
```

rồi swap.

Không cần programmer viết state machine thủ công trong trường hợp compiler có đủ thông tin.

---

# 78. Triple Buffering

Nếu latency/throughput model phù hợp:

```text
A → compute
B → transfer
C → fill
```

compiler/runtime có thể chọn.

---

# 79. Prefetch

Sequential I/O có thể được prefetch:

```text
read chunk N+1
while
process chunk N
```

nếu dependency cho phép.

---

# 80. Backpressure-Aware Scheduling

AEP có thể tối ưu toàn pipeline:

```text
Network
 ↓
Decode
 ↓
GPU
 ↓
Encode
 ↓
Disk
```

với:

```text
buffer capacity
bandwidth
latency
GPU occupancy
CPU workers
```

để tránh producer chạy quá nhanh.

---

# 81. CompilerDB

Bổ sung:

```text
IODB
IOOperationDB
IOEffectDB
IOResourceDB

StreamDB
ByteStreamDB
TypedStreamDB
StreamTransformDB
StreamWindowDB
StreamBufferDB

BufferDB
BufferViewDB
BufferLayoutDB
BufferCapacityDB
BufferAlignmentDB
BufferOwnershipDB
BufferReuseDB

ZeroCopyDB
CopyEliminationDB
ScatterGatherDB

AsyncIODB
IOFutureDB
IOEventDB
IOCompletionDB
IOCancellationDB
IOTimeoutDB
IODeadlineDB

FileDB
FileHandleDB
FileRegionDB
FileOffsetDB
FileMappingDB
FileSyncDB
FileDurabilityDB

SocketDB
TcpDB
UdpDB
PipeDB
IpcDB
SharedMemoryDB

DeviceIODB
DmaDB
DmaBufferDB
ExternalBufferDB
ExternalOwnershipDB

SerializationDB
BinaryCodecDB
TextCodecDB
EncodingDB
EndianDB

RingBufferDB
SpscQueueDB
MpscQueueDB
MpmcQueueDB
BackpressureDB

IOPipelineDB
IODataflowDB
IOFusionDB
IODoubleBufferDB
IOPrefetchDB
IOChunkDB

IOOrderingDB
IODeviceFenceDB
IOPersistenceDB

IOErrorDB
IOErrorCategoryDB
IORetryDB
IOReentrancyDB

IOCostModelDB
IOPlacementDB
IOOptimizationDB
IOProofDB
IOVerificationDB
```

---

# 82. MIR additions

```text
IO_BEGIN
IO_END

IO_READ
IO_WRITE
IO_READ_AT
IO_WRITE_AT

IO_OPEN
IO_CLOSE
IO_FLUSH
IO_SYNC

IO_WAIT
IO_POLL
IO_CANCEL

IO_BUFFER_CREATE
IO_BUFFER_VIEW
IO_BUFFER_MUT_VIEW
IO_BUFFER_RESIZE
IO_BUFFER_REUSE

IO_MAP
IO_UNMAP
IO_REGISTER_BUFFER
IO_UNREGISTER_BUFFER

IO_SCATTER_READ
IO_GATHER_WRITE

IO_SEND
IO_RECEIVE

IO_CONNECT
IO_ACCEPT

IO_PIPE_CREATE
IO_SHARED_MEMORY_MAP

IO_DEVICE_READ
IO_DEVICE_WRITE
IO_DMA_SUBMIT
IO_DMA_WAIT

IO_ENCODE
IO_DECODE

IO_STREAM_BEGIN
IO_STREAM_NEXT
IO_STREAM_END

IO_CHUNK
IO_WINDOW

IO_BACKPRESSURE
IO_PREFETCH

IO_BUFFER_SWAP
IO_DOUBLE_BUFFER

IO_FENCE
IO_DEVICE_FENCE
IO_PERSISTENCE_FENCE

IO_CHECKPOINT
IO_RECOVER
```

---

# 83. Proof System

```text
IOOwnershipProof
IOBufferLifetimeProof
IOViewLifetimeProof
IOAlignmentProof
IOBoundsProof

ZeroCopyProof
CopyEliminationProof
BufferReuseProof
BufferAliasProof

ScatterGatherProof
DmaSafetyProof
ExternalBufferProof
ExternalOwnershipProof

AsyncIOProof
IOFutureProof
IOCancellationProof
IOTimeoutProof

FileOrderingProof
FileDurabilityProof
MappingLifetimeProof

SocketOrderingProof
ProtocolBoundaryProof

SerializationProof
EncodingProof
EndianProof

BackpressureProof
RingBufferProof
QueueConcurrencyProof

IOOrderingProof
IODeviceOrderingProof
IOPersistenceProof

IOPipelineProof
IOFusionProof
DoubleBufferProof
PrefetchProof

IORetryProof
IdempotenceProof
IOReentrancyProof

IODeviceProof
IOStorageDomainProof
IOExecutionDomainProof
IOCostModelProof
```

---

# 84. Invariants

### `AIO-01`
I/O resource phải có ownership/lifetime semantics rõ ràng.

### `AIO-02`
Owning I/O resource không được implicit Copy nếu Copy tạo thêm resource ownership.

### `AIO-03`
Borrowed view không được vượt lifetime của underlying storage.

### `AIO-04`
Async I/O phải preserve buffer lifetime qua suspension.

### `AIO-05`
Blocking I/O phải được compiler/runtime nhận diện bằng effect.

### `AIO-06`
Compiler không được tự biến blocking operation thành nonblocking semantics.

### `AIO-07`
Compiler không được tự giả định network/file/device operation là pure.

### `AIO-08`
I/O ordering observable phải được bảo toàn.

### `AIO-09`
Persistence ordering phải phân biệt với CPU memory ordering.

### `AIO-10`
Device ordering phải phân biệt với ordinary memory ordering.

### `AIO-11`
Zero-copy optimization chỉ hợp lệ khi ownership và storage contract cho phép.

### `AIO-12`
Copy elimination không được phá vỡ observable aliasing.

### `AIO-13`
Buffer reuse không được invalidate live capabilities.

### `AIO-14`
DMA buffer phải thỏa alignment/storage/device-access contract.

### `AIO-15`
External buffer phải có explicit ownership/lifetime contract.

### `AIO-16`
Memory mapping phải preserve mapping lifetime.

### `AIO-17`
Unmap không được xảy ra khi live safe view vẫn tồn tại.

### `AIO-18`
Scatter/gather phải preserve logical byte sequence.

### `AIO-19`
TCP stream không được giả định message boundaries.

### `AIO-20`
Datagram phải preserve message boundaries.

### `AIO-21`
Serialization phải là explicit semantic boundary.

### `AIO-22`
Wire endianness phải deterministic theo protocol contract.

### `AIO-23`
Streaming decoder phải xử lý chunk boundary đúng semantics.

### `AIO-24`
Bounded stream phải có backpressure semantics rõ ràng.

### `AIO-25`
Queue optimization không được thay đổi concurrency semantics.

### `AIO-26`
Retry chỉ được thực hiện khi operation có retry-safe contract.

### `AIO-27`
Cancellation không được giả định đã hủy physical external operation nếu backend không đảm bảo.

### `AIO-28`
Pipeline fusion phải preserve I/O effects và observable ordering.

### `AIO-29`
Double-buffer/prefetch optimization phải preserve ownership và dependency graph.

### `AIO-30`
Chương trình không sử dụng I/O subsystem không được phát sinh I/O runtime dependency ngoài những thành phần thực sự cần thiết.

---

# 85. Kiến trúc sau 390

Axiom lúc này có một data path khá hoàn chỉnh:

```text
             ┌───────────────┐
             │ External Data │
             └───────┬───────┘
                     │
          ┌──────────▼──────────┐
          │       I/O           │
          │ file/network/device │
          └──────────┬──────────┘
                     │
                 Buffer
                     │
          ┌──────────▼──────────┐
          │   Data Layout       │
          │ AoS/SoA/tiled/...   │
          └──────────┬──────────┘
                     │
             ┌───────▼───────┐
             │ Tensor/Graph  │
             └───────┬───────┘
                     │
          ┌──────────▼──────────┐
          │ Axiom Execution     │
          │ CPU/SIMD/GPU/Node   │
          └──────────┬──────────┘
                     │
                 Buffer
                     │
          ┌──────────▼──────────┐
          │       I/O           │
          └─────────────────────┘
```

Và quan trọng hơn, compiler có thể nhìn xuyên toàn bộ pipeline:

```text
Read
 ↓
Decode
 ↓
Transform
 ↓
Tensor
 ↓
GPU
 ↓
Encode
 ↓
Write
```

để tìm:

```text
copy elimination
buffer reuse
layout transformation
DMA
double buffering
prefetch
pipeline overlap
CPU/GPU overlap
async scheduling
```

nhưng **không được thay đổi semantics observable**.

Đây là nền tảng rất quan trọng để Axiom sau này có thể xử lý các workload như **video, audio, AI, database, scientific computing và network server** với abstraction cao mà vẫn giữ mục tiêu **zero-copy / zero-allocation / native-performance khi có thể chứng minh được**.