# BOOTSTRAP-179 — I/O, File, Socket, Device, Zero-Copy & Unified Data Path
**FROZEN / COMPLETED**

Mục tiêu của task này là xây dựng I/O sao cho:

> **Axiom có thể đạt zero-copy, async I/O, scatter/gather, DMA và platform-specific fast path mà API cấp cao vẫn đơn giản và không bắt programmer quản lý pointer/lifetime thủ công.**

Nguyên tắc:

```text
I/O không phải một kiểu dữ liệu riêng.
I/O là sự tương tác giữa:
    Resource
    + Buffer
    + Ownership
    + Capability
    + Synchronization
    + Execution
```

---

# 179.1. Unified I/O model

Axiom nên có mô hình:

```text
Resource
   │
   ├── File
   ├── Socket
   ├── Pipe
   ├── Device
   ├── Terminal
   └── External I/O
        │
        ↓
      Operation
        │
        ├── read
        ├── write
        ├── read_at
        ├── write_at
        ├── send
        ├── receive
        └── control
        │
        ↓
      Buffer
```

---

# 179.2. Resource ≠ Buffer

File:

```text
File
```

không phải:

```text
Buffer
```

và:

```text
Socket
```

cũng không phải:

```text
Buffer
```

Buffer là vùng dữ liệu mà operation đọc/ghi.

---

# 179.3. Ownership của I/O buffer

Một I/O operation đang chạy có thể giữ buffer.

Ví dụ:

```text
Buffer
   │
   └── async read
          │
          └── OS/device
```

Trong thời gian operation chưa hoàn thành:

```text
buffer storage must remain valid
```

Compiler/runtime phải đảm bảo điều này.

Programmer không cần tự viết lifetime.

---

# 179.4. Đây là một extension trực tiếp của capability model

Nếu:

```ax
async_read(buffer)
```

đang sử dụng:

```text
mut_view<u8>
```

thì buffer không được:

```text
drop
move
reallocate
relocate
```

trong thời gian operation yêu cầu storage đó.

---

# 179.5. Owned-buffer async I/O

Mô hình rất quan trọng:

```ax
read_async(buffer)
    -> Future<(Buffer, usize)>
```

Semantic:

```text
caller
  │
  │ Move
  ↓
I/O operation
  │
  │ completion
  ↓
Future
  │
  │ Move
  ↓
caller
```

Không cần reference counting chỉ để giữ buffer sống.

---

# 179.6. Zero-copy

Zero-copy không nên là một keyword.

Nó là optimization/result của storage semantics.

Ví dụ:

```text
File
 ↓
kernel buffer
 ↓
user buffer
```

có thể có copy.

Trong trường hợp khác:

```text
File
 ↓
mmap
 ↓
view<u8>
```

không cần copy dữ liệu.

---

# 179.7. Zero-copy không có nghĩa “không bao giờ copy”

Copy vẫn có thể cần thiết khi:

```text
ownership domain changes
storage domain changes
alignment incompatible
device requires staging
buffer lifetime incompatible
encoding transformation required
```

Axiom phải tránh biến “zero-copy” thành semantic requirement làm API khó dùng.

---

# 179.8. Buffer abstraction

Axiom nên phân biệt:

```text
Bytes
Buffer<T>
view<T>
mut_view<T>
DeviceBuffer<T>
MappedRegion
```

Trong đó:

```text
Bytes
```

là byte sequence.

```text
Buffer<T>
```

là owned storage.

```text
view<T>
```

là read capability.

```text
mut_view<T>
```

là exclusive write capability.

---

# 179.9. Byte buffer

Network/file I/O thường dùng:

```text
Buffer<u8>
```

hoặc `Bytes`.

Không ép tất cả I/O thành UTF-8.

---

# 179.10. Text I/O

Text layer nằm trên byte I/O:

```text
File
 ↓
Bytes
 ↓
UTF-8 decoder
 ↓
Str/String
```

Không:

```text
File
 ↓
String
```

một cách mặc định.

---

# 179.11. File API

Conceptual:

```ax
let file = File.open(path)?;
let n = file.read(buffer)?;
```

Đây là synchronous API.

Async:

```ax
let (buffer, n) = file.read_async(buffer).await?;
```

Không có implicit thread creation.

---

# 179.12. Random-access I/O

File phải hỗ trợ:

```text
read_at(offset, buffer)
write_at(offset, buffer)
```

nếu platform/resource cho phép.

Điều này rất quan trọng cho:

```text
database
asset streaming
parallel file processing
random-access formats
```

---

# 179.13. Positional I/O không thay đổi cursor

`read_at` nên semantic là:

```text
read from offset X
```

không thay đổi shared file cursor.

Điều này giúp parallelism dễ hơn.

---

# 179.14. Sequential file cursor

API:

```ax
file.read(buffer)
```

có state:

```text
cursor
```

Do đó concurrent access phải có synchronization semantics rõ ràng.

---

# 179.15. File capability

Một file handle có thể mang:

```text
Read
Write
Append
Seek
Sync
Metadata
```

capabilities.

Không phải file nào cũng có tất cả.

---

# 179.16. Capability-oriented I/O

Thay vì kiểm tra runtime ở mọi call:

```text
write(file)
```

type/API có thể expose capability:

```text
WritableFile
ReadableFile
SeekableFile
```

Compiler/static resolution có thể loại bỏ nhiều checks.

---

# 179.17. OS descriptor

Unix:

```text
fd
```

Windows:

```text
HANDLE
```

không được trở thành semantic identity duy nhất của `File`.

Axiom dùng:

```text
File
```

semantic resource.

Backend map sang platform handle.

---

# 179.18. Resource ownership

`File`:

```text
Drop
    ↓
close
```

theo mặc định.

Nhưng borrowed/foreign handles có thể có:

```text
BorrowedHandle
OwnedHandle
```

ownership khác nhau.

---

# 179.19. Foreign handle

Nếu Axiom nhận:

```text
extern HANDLE
```

không được tự động:

```text
Drop → CloseHandle()
```

trừ khi ABI contract nói resource ownership đã chuyển sang Axiom.

---

# 179.20. Socket

Socket là resource:

```text
Socket
```

có operation:

```text
connect
bind
listen
accept
send
receive
shutdown
```

---

# 179.21. TCP stream

Có thể abstraction:

```text
TcpStream
```

và:

```text
read
write
```

theo byte buffers.

Không ép stream thành message boundary.

---

# 179.22. UDP

UDP giữ message boundary:

```text
send_datagram
receive_datagram
```

Không nên dùng cùng semantic abstraction với TCP nếu làm mất message semantics.

---

# 179.23. Socket address

Address:

```text
IpAddress
SocketAddress
```

là value types.

Không phải pointer/string.

---

# 179.24. Socket buffer ownership

Synchronous:

```text
write(view<u8>)
```

chỉ cần buffer sống trong call.

Async:

```text
write_async(Buffer)
```

có thể Move buffer vào operation.

Đây là nơi ownership model tạo ra API rất sạch.

---

# 179.25. Không cần `'a`

Programmer không phải viết:

```text
write_async<'a>(...)
```

Compiler tự biết:

```text
async operation
    depends on buffer
    → buffer must remain valid
```

---

# 179.26. Scatter/Gather I/O

Axiom nên hỗ trợ:

```text
writev
readv
```

semantic abstraction:

```text
view<view<u8>>
```

hoặc chuyên biệt:

```text
IoVec
```

---

# 179.27. Scatter/gather

Ví dụ:

```text
header
body
footer
```

có thể gửi:

```text
[header][body][footer]
```

mà không cần:

```text
allocate
 ↓
concatenate
 ↓
copy
```

---

# 179.28. Capability checking

Các views trong một I/O vector phải có lifetime hợp lệ trong toàn bộ operation.

Nếu async:

```text
all referenced buffers remain valid
```

cho tới completion.

---

# 179.29. Mutable scatter/gather

`readv` có:

```text
mut_view<u8>
```

cho từng buffer.

Compiler phải biết các regions có overlap hay không.

Nếu:

```text
buf1
buf2
```

có unknown overlap và operation yêu cầu disjoint buffers:

```text
reject
```

theo alias rules.

---

# 179.30. Gather write

`writev` không nhất thiết yêu cầu buffers disjoint vì chỉ READ.

Do đó nhiều:

```text
view<u8>
```

có thể cùng đọc cùng region.

---

# 179.31. Sendfile / splice

System backend nên có fast paths:

```text
file → socket
```

mà không cần:

```text
file
 ↓
user buffer
 ↓
socket
```

nếu platform hỗ trợ.

---

# 179.32. Semantic API

Ví dụ:

```ax
socket.send_file(file, range)?;
```

Compiler/runtime có thể chọn:

```text
sendfile
TransmitFile
splice
copy_file_range
```

tùy target.

---

# 179.33. Abstraction erasure

API:

```text
send_file()
```

không cần tạo abstraction object runtime.

Sau specialization có thể trở thành một system call trực tiếp.

---

# 179.34. Memory-mapped I/O

Đã có:

```text
MappedFile
```

nên pipeline:

```text
File
 ↓
MappedRegion
 ↓
view<u8>
 ↓
parser
```

có thể zero-copy.

---

# 179.35. Parser zero-copy

Parser có thể nhận:

```ax
fn parse(data: view<u8>) -> Result<Document, Error>
```

và nếu Document giữ references:

```text
Document
  └── views → original mapped/file buffer
```

compiler tự đảm bảo buffer không bị giải phóng trước Document.

---

# 179.36. Nhưng persistent zero-copy cần ownership

Không thể:

```text
fn parse(file: File) -> Document
```

với:

```text
Document → view(file_buffer)
```

nếu buffer không còn tồn tại.

Các lựa chọn semantic:

```text
Document owns Buffer
```

hoặc:

```text
Document owns Mapping
```

hoặc:

```text
Document returns owned data
```

Compiler sẽ buộc API phải thể hiện dependency ownership, nhưng programmer không viết lifetime.

---

# 179.37. Zero-copy parsing

Ví dụ:

```text
network buffer
     ↓
parser
     ↓
Message
     ├── view field A
     ├── view field B
     └── integer fields
```

Không cần copy string/bytes nếu input buffer vẫn sống.

---

# 179.38. Network packet

Có thể có abstraction:

```text
PacketBuffer
```

với:

```text
headroom
payload
tailroom
```

rất hữu ích cho networking.

---

# 179.39. Headroom

Ví dụ:

```text
[free][payload]
```

sau đó prepend:

```text
[ETH][IP][TCP][payload]
```

mà không allocate/copy toàn bộ payload.

Đây là kiểu data structure nên thuộc networking library, không phải Core.

---

# 179.40. Ring buffer

I/O runtime nên tận dụng:

```text
RingBuffer
```

cho:

```text
producer → consumer
```

và có thể specialize:

```text
SPSC
MPSC
SPMC
MPMC
```

---

# 179.41. Ring buffer capability

Producer có:

```text
mut_view
```

trên write region.

Consumer có:

```text
view
```

trên read region.

Compiler/capability system giúp model này an toàn mà không cần pointer arithmetic.

---

# 179.42. Async I/O

Core semantics:

```text
async fn
Future
await
```

đã frozen.

I/O library cung cấp:

```text
File.read_async
Socket.receive_async
```

nhưng executor không thuộc Core.

---

# 179.43. Completion-based vs readiness-based

Axiom không nên đưa Linux-specific model vào Core.

Platform backends có thể là:

```text
Linux:
    io_uring
    epoll

Windows:
    IOCP

BSD/macOS:
    kqueue

WASM:
    host async API

embedded:
    interrupt/DMA
```

---

# 179.44. Unified async I/O abstraction

Application thấy:

```text
Future<IOResult<T>>
```

Backend thấy:

```text
completion
or
readiness
or
poll
or
interrupt
```

---

# 179.45. Executor không thuộc I/O

I/O operation:

```text
returns Future
```

không tự spawn thread.

Executor quyết định:

```text
thread
fiber
event loop
io_uring
IOCP
```

---

# 179.46. Operation state

Một async operation có semantic state:

```text
CREATED
SUBMITTED
WAITING
READY
FAILED
CANCELLED
```

Không nhất thiết tất cả state tồn tại vật lý.

---

# 179.47. Cancellation

Cancellation:

```text
operation.cancel()
```

không đảm bảo OS đã dừng operation ngay lập tức.

Axiom phải phân biệt:

```text
logical cancellation
physical completion
```

---

# 179.48. Buffer lifetime during cancellation

Nếu I/O chưa hoàn thành:

```text
buffer cannot be reclaimed
```

cho tới khi backend contract xác nhận operation không còn truy cập.

Đây là invariant cực kỳ quan trọng.

---

# 179.49. I/O completion capability

Có thể mô hình hóa:

```text
IoOperation<T>
```

sở hữu quyền:

```text
operation may access buffer
```

Khi operation complete:

```text
capability returned/released
```

---

# 179.50. Double completion

Backend không được:

```text
complete
complete
```

cùng một operation.

Compiler/runtime state machine phải bảo vệ invariant này.

---

# 179.51. Async I/O và Drop

Nếu:

```ax
let op = file.read_async(buffer);
drop(op);
```

không mặc định có nghĩa:

```text
cancel OS operation
```

Đã frozen từ async model.

API có thể có:

```text
cancel()
```

riêng.

---

# 179.52. Ownership transfer vào kernel

Trong nhiều hệ thống, submit I/O làm resource state chuyển:

```text
user ownership
     ↓
in-flight operation
```

Nhưng đây là **logical ownership/capability transfer**, không nhất thiết OS “own object”.

---

# 179.53. DMA

DMA:

```text
CPU
 │
 │ submit buffer
 ↓
Device
 │
 │ DMA
 ↓
Memory
```

buffer phải có:

```text
valid storage
required alignment
device accessibility
lifetime
coherence
```

---

# 179.54. DMA buffer type

Axiom nên có:

```text
DmaBuffer<T>
```

hoặc tương đương.

Nó không phải:

```text
Vec<T>
```

vì DMA có storage contract khác.

---

# 179.55. DMA synchronization

Có thể cần:

```text
flush_for_device
invalidate_for_cpu
sync
```

tùy architecture.

Không được tự động assume cache coherence.

---

# 179.56. Device queue

GPU/network/NVMe có thể có:

```text
SubmissionQueue
CompletionQueue
```

đây là runtime/device abstractions.

---

# 179.57. Unified completion model

Conceptual:

```text
IoEvent<T>
```

có thể biểu diễn:

```text
File completion
Socket completion
DMA completion
GPU completion
```

nhưng payload/ABI cụ thể vẫn khác.

---

# 179.58. GPU integration

Ví dụ:

```text
DeviceBuffer
   ↓
GPU kernel
   ↓
GpuEvent
```

và:

```text
File
   ↓
DMA
   ↓
DeviceBuffer
```

có thể được nối thành:

```text
File → GPU
```

mà không cần intermediate CPU copy nếu platform hỗ trợ.

---

# 179.59. Pipeline

Axiom nên cho phép pipeline:

```text
Disk
 ↓
DMA
 ↓
Host/Device Buffer
 ↓
GPU
 ↓
Network
```

với compiler/runtime biết:

```text
ownership
storage domain
completion dependency
```

---

# 179.60. I/O dependency graph

Một program có thể tạo graph:

```text
Read A
  ↓
Parse A
  ↓
GPU Transform
  ↓
Write B
```

Compiler/runtime có thể schedule independent operations.

---

# 179.61. Không tự động parallelize I/O

Semantic:

```text
statement order
```

vẫn giữ nguyên.

Compiler chỉ được overlap operations khi:

```text
effects
ownership
capabilities
dependencies
```

chứng minh kết quả observable không thay đổi.

---

# 179.62. Buffered I/O

Library có thể cung cấp:

```text
BufferedReader
BufferedWriter
```

nhưng buffering không phải property của File.

---

# 179.63. Buffer elision

Nếu:

```text
BufferedWriter
```

chỉ tồn tại trong scope và compiler biết destination:

```text
```

có thể optimize một số intermediate buffers.

Không được thay đổi observable flushing semantics.

---

# 179.64. Flush semantics

Phải phân biệt:

```text
flush user buffer
flush OS buffer
sync storage
durable persistence
```

Không nhập thành một `flush()` có semantics mơ hồ.

---

# 179.65. File durability

Nên có abstraction tương ứng:

```text
flush()
sync()
sync_data()
```

tùy platform.

Application/database có thể yêu cầu mức durability cụ thể.

---

# 179.66. Socket backpressure

Async socket write có thể trả:

```text
Pending
```

vì:

```text
kernel send buffer full
```

Không nên coi Pending là error.

---

# 179.67. Partial I/O

`read`/`write` có thể hoàn thành một phần.

API phải biểu diễn:

```text
(bytes_transferred)
```

và không giả định:

```text
request N
→ exactly N
```

trừ API có contract rõ ràng.

---

# 179.68. `read_exact`

Library có thể cung cấp:

```text
read_exact(buffer)
```

và thực hiện nhiều underlying reads.

---

# 179.69. `write_all`

Tương tự:

```text
write_all(buffer)
```

lặp cho đến:

```text
all bytes transferred
```

hoặc failure.

---

# 179.70. I/O errors

Error model dùng:

```text
Result<T, IoError>
```

Không exception.

`IoError` có thể chứa:

```text
kind
platform_code
operation
resource
```

nhưng không bắt buộc allocate string.

---

# 179.71. Platform error code

Unix:

```text
errno
```

Windows:

```text
GetLastError / WSA error
```

được map vào Axiom error abstraction.

Native code vẫn có thể lấy raw code.

---

# 179.72. Error ownership

I/O errors nên thường là small values:

```text
enum IoErrorKind
struct IoError
```

Compiler có thể trả qua registers.

Không tạo exception object.

---

# 179.73. Blocking I/O

Synchronous API có thể block:

```text
file.read()
```

nhưng:

```text
async fn
```

không được âm thầm biến thành blocking syscall nếu contract không cho phép.

---

# 179.74. Blocking annotation

Không cần programmer annotate mọi function `blocking`.

Compiler có thể derive effect:

```text
Blocking
```

hoặc:

```text
Suspend
```

ở effect system/runtime metadata nếu cần.

---

# 179.75. Async boundary

Một function:

```text
fn foo()
```

gọi blocking I/O thì vẫn là synchronous function.

Một:

```text
async fn foo()
```

có `.await` thì suspension là explicit.

Không tự động spawn.

---

# 179.76. I/O + threads

Runtime có thể implement:

```text
blocking file I/O
```

bằng worker pool khi platform/runtime profile chọn.

Nhưng semantic distinction vẫn:

```text
blocking operation
```

vs:

```text
native async operation
```

---

# 179.77. io_uring-style backend

Linux backend có thể:

```text
submission queue
completion queue
```

và map:

```text
Future
```

trực tiếp vào completion entry.

Không cần thread cho mỗi request.

---

# 179.78. IOCP-style backend

Windows backend tương tự:

```text
OVERLAPPED operation
      ↓
IOCP completion
      ↓
Future wake
```

---

# 179.79. Readiness backend

epoll/kqueue:

```text
readiness
 ↓
attempt operation
 ↓
Pending/Ready
```

vẫn map được vào unified Future abstraction.

---

# 179.80. Embedded I/O

Embedded không có OS:

```text
interrupt
DMA
memory mapped register
```

có thể là I/O backend.

Điều này chứng minh Core không nên định nghĩa I/O theo Unix/Windows.

---

# 179.81. Device abstraction

Concept:

```text
Device
```

có:

```text
open
configure
read
write
control
```

nhưng implementation phụ thuộc system package.

---

# 179.82. `io::Resource`

Một unified trait có thể tồn tại:

```text
trait Read
trait Write
trait Seek
trait AsyncRead
trait AsyncWrite
```

Không nên tạo một:

```text
trait IOEverything
```

quá lớn.

---

# 179.83. Trait composability

Ví dụ:

```text
T: Read
T: Write
T: Seek
```

cho phép generic code chỉ yêu cầu capability thực sự cần.

---

# 179.84. Generic I/O

```ax
fn copy<R: Read, W: Write>(
    src: mut_view<R>,
    dst: mut_view<W>
)
```

Conceptually static dispatch.

Compiler có thể inline toàn bộ pipeline.

---

# 179.85. Trait object I/O

Nếu runtime/plugin architecture cần dynamic dispatch:

```text
dyn Read
```

phải explicit.

Không tạo hidden interface object.

---

# 179.86. I/O object overhead

Static generic:

```text
Read<File>
```

có thể compile thành:

```text
direct syscall/backend call
```

không vtable.

---

# 179.87. Buffered abstraction

```text
BufferedReader<R>
```

có thể được monomorphized.

Nếu `R = File`:

```text
BufferedReader<File>
```

có thể inline xuyên abstraction.

---

# 179.88. Zero-copy pipe

Có thể có:

```text
Buffer
 ↓
Pipe
 ↓
Socket
```

và backend chọn:

```text
splice
sendfile
vmsplice
TransmitFile
```

nếu semantics phù hợp.

---

# 179.89. Pipe ownership

Pipe buffer phải có explicit producer/consumer ownership.

Concurrent access dùng:

```text
channel/ring-buffer synchronization
```

không dựa trên raw pointers.

---

# 179.90. Unified data path

Kiến trúc cuối:

```text
                ┌───────────────┐
                │    Resource   │
                └───────┬───────┘
                        │
                    Operation
                        │
             ┌──────────┴──────────┐
             │                     │
          Buffer                Device
             │                     │
       Ownership/Capability     DMA
             │                     │
             └──────────┬──────────┘
                        │
                 Async Completion
                        │
                      Future
                        │
                     Executor
```

---

# 179.91. I/O pipeline tối ưu

Một pipeline lý tưởng:

```text
                 FILE
                   │
                   │ DMA / mmap
                   ↓
              Buffer/View
                   │
                   │ zero-copy
                   ↓
                 Parser
                   │
                   ↓
               GPU Buffer
                   │
                   │ GPU
                   ↓
               Transform
                   │
                   │ DMA
                   ↓
                Socket
```

Axiom không cần pointer-heavy syntax để đạt được pipeline này.

---

# 179.92. Compiler optimization opportunities

Compiler có thể tối ưu:

```text
I/O operation fusion
buffer elimination
buffer reuse
scatter/gather
copy elimination
storage-domain transfer elimination
direct I/O path
syscall batching
async operation batching
```

nhưng chỉ khi effects/capabilities/ABI chứng minh được.

---

# 179.93. Syscall batching

Ví dụ nhiều operations:

```text
read A
read B
read C
```

runtime/backend có thể submit batch nếu:

```text
dependency graph
```

cho phép.

---

# 179.94. I/O operation effects

Effect system có thể phân biệt:

```text
IO
Read(resource)
Write(resource)
Synchronize
Suspend
ExternalState
```

và compiler dùng chúng để biết operations nào có thể reorder/overlap.

---

# 179.95. Observable ordering

Compiler không được biến:

```text
write(A)
write(B)
```

thành:

```text
write(B)
write(A)
```

nếu external semantics quan sát được ordering.

---

# 179.96. Independent I/O

Nếu:

```text
read(A)
read(B)
```

không có dependency:

```text
A ≠ B
```

và API/backend cho phép concurrency, runtime có thể overlap.

---

# 179.97. I/O và deterministic execution

Test profile có thể dùng deterministic executor:

```text
operation A
operation B
```

để reproducibly test concurrent I/O logic.

Actual production executor vẫn có thể chạy parallel.

---

# 179.98. Security

I/O abstraction phải chống:

```text
TOCTOU
invalid descriptor ownership
use-after-close
buffer lifetime bugs
path encoding confusion
partial write bugs
integer overflow in size/offset
```

Một số thuộc compiler safety, một số thuộc API contract.

---

# 179.99. Path không phải String

Đã có:

```text
Path
PathBuf
OsStr
OsString
```

Do đó:

```text
open("...")
```

có thể có literal → Path coercion.

Nhưng không giả định mọi OS path là UTF-8.

---

# 179.100. Kết luận kiến trúc

Axiom I/O được khóa theo nguyên tắc:

> **Resource ownership + buffer capability + explicit operation + asynchronous completion.**

Không phải:

```text
pointer + syscall
```

và cũng không phải:

```text
hidden runtime magic
```

---

# Invariants

### I/O

- **AIO-20** — I/O resources are distinct from buffers.
- **AIO-21** — I/O operations preserve ownership and capability semantics.
- **AIO-22** — In-flight operations must retain required storage validity.
- **AIO-23** — Async I/O does not imply thread creation.
- **AIO-24** — Cancellation is distinct from physical operation completion.
- **AIO-25** — Partial I/O is representable.
- **AIO-26** — Blocking and asynchronous operations remain semantically distinct.
- **AIO-27** — I/O errors use Result-based recoverable failure by default.
- **AIO-28** — Foreign resource ownership must be explicit.
- **AIO-29** — Platform-specific I/O mechanisms are backend details.

### Zero-copy

- **AZCOPY-20** — Zero-copy is an optimization, not a semantic requirement.
- **AZCOPY-21** — Copy elimination cannot alter ownership or capability semantics.
- **AZCOPY-22** — Storage-domain transfers are explicit unless compiler proves safe elimination.
- **AZCOPY-23** — Memory-mapped access may provide zero-copy views.
- **AZCOPY-24** — Scatter/gather operations preserve buffer provenance.
- **AZCOPY-25** — Active I/O capabilities prevent invalid buffer relocation.
- **AZCOPY-26** — Runtime/backend may select platform-specific zero-copy primitives.

### Async I/O

- **AIOASYNC-20** — Future state retains all resources required until completion.
- **AIOASYNC-21** — Buffer storage cannot be reclaimed while an active operation may access it.
- **AIOASYNC-22** — Dropping a Future does not imply physical I/O cancellation.
- **AIOASYNC-23** — Explicit cancellation must define completion/lifetime semantics.
- **AIOASYNC-24** — Completion occurs at most once.
- **AIOASYNC-25** — Wakeup does not itself establish memory publication.

### DMA/device

- **ADMA-20** — DMA buffers have explicit storage-domain contracts.
- **ADMA-21** — Device accessibility is distinct from CPU accessibility.
- **ADMA-22** — DMA lifetime extends through all device accesses.
- **ADMA-23** — Cache-coherence assumptions are explicit.
- **ADMA-24** — Host/device transfer cannot silently violate capability provenance.
- **ADMA-25** — Device completion releases or transfers the relevant capability.

### Optimization

- **AIOOPT-20** — I/O operations are observable effects unless proven otherwise.
- **AIOOPT-21** — Effect dependencies constrain I/O reordering.
- **AIOOPT-22** — Independent I/O may be overlapped when semantics permit.
- **AIOOPT-23** — Syscall/backend batching cannot change observable ordering.
- **AIOOPT-24** — Platform-specific fast paths are permitted behind stable semantic APIs.
- **AIOOPT-25** — Zero-copy, buffer reuse and operation fusion require legality proofs.

---

# BOOTSTRAP-179 hoàn tất

Đến đây Axiom đã nối được:

```text
Value
 ↓
Ownership
 ↓
Capability
 ↓
Storage
 ↓
Allocator
 ↓
Virtual Memory
 ↓
Buffer
 ↓
I/O
 ↓
Async
 ↓
DMA / GPU / Device
```

Điểm rất đáng chú ý là **ownership model hiện tại không chỉ giải quyết memory safety**. Nó trở thành nền tảng cho:

- async I/O
- zero-copy
- DMA
- GPU transfer
- mmap
- socket buffer
- scatter/gather
- resource lifetime
- syscall optimization

mà không cần đưa pointer/lifetime syntax vào code bình thường.

---

## BOOTSTRAP-180 — Process, Thread, Task, Fiber, IPC & OS Resource Model

Bước tiếp theo nên hoàn thiện tầng **execution + OS resources**:

```text
Process
   ↓
Thread
   ↓
Fiber
   ↓
Task / Future
   ↓
Scheduler
   ↓
CPU affinity
   ↓
Priority
   ↓
IPC
   ├── Channel
   ├── Shared Memory
   ├── Pipe
   ├── Event
   ├── Semaphore
   └── OS Handle
   ↓
Process lifecycle
   ↓
Signals / Exit / Spawn
```

Đặc biệt task 180 sẽ chốt **mối quan hệ chính xác giữa ownership, Send/Share, thread, task, process và OS handle** — đây là mảnh còn thiếu để Axiom trở thành một systems language hoàn chỉnh.