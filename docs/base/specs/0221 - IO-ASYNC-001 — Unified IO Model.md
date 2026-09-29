Tiếp tục với **IO-ASYNC-001**. Đây là phần rất quan trọng vì I/O thường là nơi các ngôn ngữ hiện đại bắt đầu đưa runtime, allocation và abstraction overhead vào chương trình.

# IO-ASYNC-001 — Unified I/O Model

## 1. Quyết định lớn

Tôi đề xuất Axiom dùng:

> **Một resource model + một buffer/capability model chung, nhưng API synchronous và asynchronous tách biệt.**

Không nên làm:

```text
SyncFile
AsyncFile
SyncBuffer
AsyncBuffer
SyncSocket
AsyncSocket
```

với hai hệ type hoàn toàn khác nhau.

Thay vào đó:

```text
Resource
   │
   ├── sync operation
   │
   └── async operation
```

Ví dụ:

```text
file.read(buf)
```

và:

```text
file.read_async(buf)
```

cùng thao tác trên:

```text
File
mut_view<u8>
```

---

# 2. Buffer là trung tâm của I/O

Đây là quyết định tôi muốn nhấn mạnh.

I/O không nên mặc định trả về:

```text
String
Vec<u8>
Array<u8>
```

mỗi lần đọc.

Thay vào đó primitive thấp nhất là:

```text
read(mut_view<u8>) -> Result<usize, IoError>
```

Ví dụ:

```text id="7r4j3p"
var buffer: [u8; 4096];

let n = file.read(mut_view(buffer));
```

Ý nghĩa:

```text
File
  │
  └── WRITE capability
          ↓
      buffer[0..n]
```

Không cần allocation.

Không cần copy.

---

# 3. Async cũng giữ nguyên buffer model

Ví dụ:

```text id="7d0m8k"
let n = await file.read_async(mut_view(buffer));
```

Nhưng có một vấn đề:

`buffer` phải tồn tại trong suốt thời gian I/O chưa hoàn thành.

Đây chính là nơi ownership/capability system của Axiom phát huy tác dụng.

Compiler phải biết:

```text
I/O operation
    ↓
owns/depends on
    ↓
buffer capability
```

Do đó không thể:

```text id="3z9l1f"
start_read(mut_view(buffer));

destroy(buffer);      // reject
reuse(buffer);        // reject
```

trước khi operation hoàn thành.

---

# 4. Async I/O không nên giữ `mut_view` qua `.await` một cách mơ hồ

Ta đã chốt:

> `view<T>` / `mut_view<T>` không được sống xuyên qua `.await`.

Nhưng async I/O là trường hợp cần thiết kế kỹ.

Giải pháp:

### API sync

```text id="fd8r22"
read(mut_view<u8>) -> Result<usize, Error>
```

### API async

Không nên đơn giản là:

```text id="g0qj75"
read_async(mut_view<u8>) -> Future<usize>
```

nếu Future giữ capability sống xuyên suspension theo cách thông thường.

Thay vào đó Future phải **own một I/O operation state**, và state đó quản lý ownership/capability của buffer.

Khái niệm:

```text id="0mt4lq"
ReadOperation<'semantic>
```

nhưng lifetime không xuất hiện trong source syntax.

Compiler hiểu:

```text
Future
 ├── I/O handle
 └── buffer ownership/capability
```

---

# 5. Đơn giản hơn nữa: async operation có thể consume buffer

Đây là một API rất mạnh cho zero-copy:

```text id="1g0x0r"
read_async(buffer) -> Future<(Buffer, usize)>
```

Ví dụ:

```text id="y1z4n3"
let (buffer, n) = await file.read_async(buffer);
```

Ownership:

```text
caller
  ↓ Move
I/O Future
  ↓ completion
caller
```

Không có borrow sống xuyên await.

Điều này cực kỳ phù hợp với Axiom.

---

# 6. Nhưng không phải lúc nào cũng muốn transfer ownership

Có trường hợp buffer thuộc một object lâu dài:

```text id="6d4j1p"
Connection {
    receive_buffer
}
```

Khi đó có thể có operation abstraction:

```text id="6l5h4b"
ReadOp
```

với capability được compiler quản lý.

Như vậy ta có hai API:

```text id="b5m0gt"
borrowed operation
```

và:

```text id="9pp3wk"
owned operation
```

Nhưng programmer không cần viết lifetime.

---

# 7. Zero-copy phải là design goal

Axiom I/O nên cố gắng:

```text OS
 ↓
kernel buffer
 ↓
user buffer
```

và tránh:

```text
kernel
 ↓ copy
runtime buffer
 ↓ copy
Vec
 ↓ copy
String
```

Đặc biệt:

```text id="m2tq5u"
read
write
send
recv
splice
sendfile
mmap
DMA
```

nên có đường zero-copy khi OS hỗ trợ.

---

# 8. Nhưng zero-copy không phải semantics bắt buộc

Ví dụ:

```text id="0x0y7h"
file.read(buffer)
```

semantics chỉ là:

> ghi dữ liệu vào vùng nhớ được cấp.

Compiler/OS layer có thể thực hiện copy nếu cần.

Zero-copy là optimization/capability của implementation.

---

# 9. I/O abstraction nên chia 3 tầng

```text id="4b6h2v"
┌────────────────────────────┐
│       High-level IO        │
│ File / TcpStream / Reader  │
└──────────────┬─────────────┘
               ↓
┌────────────────────────────┐
│       Async IO Layer       │
│ Future / Poller / Event    │
└──────────────┬─────────────┘
               ↓
┌────────────────────────────┐
│       OS IO Layer          │
│ epoll / IOCP / kqueue      │
│ io_uring / WASI            │
└────────────────────────────┘
```

---

# 10. `Reader` / `Writer`

Std nên có trait:

```text id="1m7v7s"
trait Reader {
    fn read(self: mut_view<Self>, buffer: mut_view<u8>)
        -> Result<usize, IoError>;
}
```

Tương tự:

```text id="x4n5q7"
trait Writer {
    fn write(self: mut_view<Self>, buffer: view<u8>)
        -> Result<usize, IoError>;
}
```

Nhưng đây là interface synchronous.

Async không nên biến mọi method thành `async` trait magic.

Có thể:

```text id="q0x1o6"
trait AsyncReader {
    fn read_async(...) -> ReadFuture;
}
```

hoặc một async operation abstraction riêng.

---

# 11. Async không đồng nghĩa non-blocking

Cần phân biệt:

```text
sync + blocking
sync + nonblocking
async + readiness
async + completion
```

Axiom không nên coi:

```text async == nonblocking
```

là một identity.

---

# 12. Hai mô hình OS lớn

Có hai kiểu:

### Readiness

Linux:

```text id="n6x8w4"
epoll
```

macOS/BSD:

```text id="n9q4lk"
kqueue
```

Ý nghĩa:

> Resource có khả năng thực hiện operation mà không block.

### Completion

Windows:

```text id="7z4z8h"
IOCP
```

Một số API khác cũng theo completion model.

Ý nghĩa:

> Operation đã được submit; hệ thống báo khi operation hoàn thành.

Axiom abstraction phải bao phủ được cả hai.

---

# 13. Unified operation model

Tôi đề xuất khái niệm:

```text id="1s5h0k"
IoOperation<T>
```

Semantic states:

```text id="50qu8m"
CREATED
SUBMITTED
PENDING
READY
COMPLETED
CANCELLED
FAILED
```

Không nhất thiết expose toàn bộ enum cho programmer.

Compiler/runtime cần model này.

---

# 14. Readiness backend

Linux:

```text id="u9z7gr"
register(fd)
 ↓
epoll_wait
 ↓
READY
 ↓
perform read/write
```

macOS:

```text id="g5e9m4"
kqueue
```

Windows:

```text id="t1u6w2"
IOCP
 ↓
completion
```

Axiom scheduler chỉ nhận:

```text id="v2n7x0"
Wake(Task)
```

Không cần biết mechanism.

---

# 15. io_uring

Linux `io_uring` đặc biệt vì nó là completion-oriented interface.

Axiom không nên thiết kế API chỉ dựa trên epoll.

Nên:

```text id="l0l2rj"
IoBackend
 ├── Readiness
 └── Completion
```

và Linux có thể chọn:

```text id="q2o1vh"
epoll
io_uring
```

tùy operation/profile.

---

# 16. Không nên ép một abstraction xuống mức thấp nhất

Ví dụ:

```text id="9l1fzs"
TcpStream
```

không nên expose:

```text poll_interest()
```

cho người dùng bình thường.

High-level API:

```text id="7u3p5g"
stream.read(...)
```

Low-level:

```text id="5s4r2p"
Poller.register(...)
```

Advanced networking library có thể dùng tầng thấp.

---

# 17. Cancellation

Async I/O phải có cancellation semantics rõ ràng.

Ví dụ:

```text id="d7n9xk"
let op = socket.read_async(buffer);
cancel(op);
```

Không được mặc định:

```text cancel
 ↓
OS operation definitely stopped immediately
```

Vì OS khác nhau.

Semantics nên là:

> Cancellation requests that the operation no longer needs to complete.

Nếu OS không thể hủy ngay:

```text operation may remain internally active
```

nhưng Axiom phải bảo đảm resource/buffer lifetime.

---

# 18. Đây là điểm ownership cực quan trọng

Không được:

```text id="f6m8n1"
cancel(op);
free(buffer);
```

nếu OS operation vẫn có thể truy cập buffer.

Do đó:

```text id="l3k8xw"
IoOperation
```

phải giữ resource dependency đến khi OS xác nhận operation không còn truy cập memory.

Đây chính là:

> **AIO-ownership safety**

và không cần borrow checker syntax.

---

# 19. Async file I/O

Không phải OS nào cũng có async file I/O giống socket.

Axiom không được giả vờ:

```text id="h1v5x0"
File.read_async
```

luôn là kernel async I/O.

Implementation có thể:

```text
native async
```

hoặc:

```text
blocking worker
```

tùy target.

Nhưng **không được tự động tạo thread** nếu profile không cho phép.

---

# 20. Vì vậy cần capability declaration

Ví dụ target có:

```text id="u7r4pm"
AsyncFile = native
```

hoặc:

```text id="t4x1zn"
AsyncFile = worker-backed
```

Library/runtime quyết định.

Programmer có thể query capability nếu cần:

```text id="r4o5xy"
target.io.file_async
```

ở compile-time hoặc runtime tùy API.

---

# 21. Network buffer

Network stack nên hỗ trợ:

```text id="2b6o9s"
Buffer
View
MutableView
```

và tránh mặc định:

```text recv() -> Vec<u8>
```

Ví dụ:

```text id="v6z3tq"
var buffer: [u8; 16384];
let n = socket.recv(mut_view(buffer));
```

Đây là đường allocation-free.

---

# 22. Scatter/gather I/O

Axiom nên hỗ trợ:

```text id="g2h8yw"
readv
writev
recvmsg
sendmsg
```

ở low-level API.

Abstraction:

```text id="p9q1de"
view<view<u8>>
```

hoặc một type:

```text id="z6f2sa"
IoVec
```

Compiler không cần copy các buffer.

---

# 23. Vấn đề alias

Ví dụ:

```text id="1d0u7f"
writev([
    view(a),
    view(b)
])
```

Nếu operation chỉ READ thì nhiều views OK.

Nhưng:

```text id="w6m3t2"
readv([
    mut_view(a),
    mut_view(b)
])
```

nếu `a` và `b` overlap:

```text id="7k0w1a"
```

compiler phải reject hoặc API phải yêu cầu abstraction chứng minh disjointness.

Đây chính là `ACAP-68`.

---

# 24. Memory-mapped files

Axiom nên hỗ trợ:

```text id="f2q8jc"
MappedFile
```

với semantics:

```text file
 ↓
mapping
 ↓
view<u8>
```

Nhưng view phụ thuộc:

```text MappedFile
```

Không thể:

```text id="n8x0s3"
drop(mapped_file);
use(view);
```

Compiler bắt được.

---

# 25. Shared memory

OS layer:

```text id="8j4c0n"
SharedMemory
```

có:

```text mapping
ownership
permissions
lifetime
```

Nếu dùng giữa process:

```text id="x3l7ma"
process A
   ↕
shared memory
   ↕
process B
```

thì compiler không thể kiểm tra toàn bộ synchronization.

Do đó API phải dùng:

```text atomic
mutex
semaphore
shared protocol
```

và unsafe/system boundary khi cần.

---

# 26. DMA / device memory

Đây là nơi storage domain model trước đó phát huy tác dụng.

Ví dụ:

```text id="0w3y3k"
DeviceBuffer
DeviceView
HostBuffer
```

không được coi đơn giản là:

```text view<u8>
```

vì memory domain khác nhau.

Ta có:

```text id="w9u5km"
Host
Device
Shared
External
```

Compiler/runtime phải giữ domain.

---

# 27. DMA lifetime

Nếu device đang sử dụng buffer:

```text id="x7d3w8n"
GPU/DMA operation
      ↓
DeviceBuffer
```

không được:

```text id="j5p8z2"
drop(buffer)
```

trước khi operation hoàn thành.

Đây chính là invariant:

```text
AGPU-23
AGPU-39
```

đã chốt.

---

# 28. I/O và ownership

Ta có một pattern thống nhất:

```text id="2q4h8v"
Resource owns OS resource
Buffer owns memory
Operation owns/inherits capability
Completion releases operation dependency
```

Ví dụ:

```text
TcpStream
   │
   └── ReadOperation
          │
          └── Buffer
```

Completion:

```text
ReadOperation
     ↓
Buffer returned
```

Không cần GC.

Không cần reference counting bắt buộc.

---

# 29. API mà tôi đề xuất cho Axiom

### Sync

```text id="7y7w4r"
trait Reader {
    fn read(
        self: mut_view<Self>,
        dst: mut_view<u8>
    ) -> Result<usize, IoError>;
}
```

### Async

```text id="6d2m9w"
trait AsyncReader {
    type ReadOperation;

    fn read_async(
        self: mut_view<Self>,
        dst: Buffer
    ) -> Self::ReadOperation;
}
```

Và:

```text id="z3w5h8"
let (buffer, n) = await reader.read_async(buffer);
```

đối với owned-buffer path.

Đây là một API rất sạch cho lifetime.

---

# 30. Nhưng tôi không muốn bắt mọi async I/O consume buffer

Vì có những trường hợp buffer nằm trong connection state.

Do đó std nên có hai lớp:

```text id="1q7w5c"
Owned async operation
```

và:

```text id="e9x1r2"
Scoped borrowed operation
```

Compiler kiểm tra lifetime nội bộ.

Người dùng chỉ chọn API phù hợp.

---

# 31. High-level convenience API

Người dùng vẫn có thể:

```text id="m4k9q0"
let data = await stream.read_all();
```

Nhưng đây là convenience API.

Bên dưới:

```text id="q8p3y7"
allocate
grow
read
copy/append
```

Nếu muốn performance tối đa:

```text id="x2j4n8"
read(buffer)
```

---

# 32. Không nên biến convenience API thành primitive

Đây là triết lý quan trọng:

```text id="e6f8t2"
read_all()
```

là library.

Primitive:

```text id="z1v7c3"
read(mut_view<u8>)
```

là nền tảng.

Do đó compiler không cần magic cho `read_all`.

---

# 33. I/O errors

`IoError` nên là enum có thể mở rộng:

```text id="r5y9v1"
enum IoError {
    NotFound,
    PermissionDenied,
    WouldBlock,
    Interrupted,
    ConnectionReset,
    TimedOut,
    BrokenPipe,
    InvalidData,
    ...
    Other(...)
}
```

Nhưng không cố map mọi OS error thành một enum khổng lồ.

Cần giữ:

```text id="q3x6n0"
raw_os_code
```

để không mất thông tin.

---

# 34. `WouldBlock` không phải error trong async abstraction

Ở low-level nonblocking API:

```text id="f0a5s2"
read()
→ WouldBlock
```

là bình thường.

Async abstraction:

```text id="c9r1w6"
await read_async()
```

nên tự xử lý readiness/pending.

Người dùng không cần:

```text
loop {
    try_read();
    if WouldBlock {
        poll();
    }
}
```

trừ khi họ đang dùng low-level API.

---

# 35. Sync API không cần scheduler

```text id="h6t2m8"
file.read(buffer)
```

nếu blocking thì:

```text
thread blocks
```

Đó là semantics bình thường.

Không cần Axiom scheduler đứng giữa.

---

# 36. Async scheduler chỉ quản lý Future

Ta đã chốt:

```text id="n4x8q2"
Future = state machine
Task = schedulable computation
```

I/O operation:

```text id="j6v1r9"
I/O completion
   ↓
wake(task)
```

Scheduler:

```text id="p5m0x4"
WAITING
  ↓
READY
```

Không tạo task mới cho mỗi event.

---

# 37. Structured concurrency

Ví dụ:

```text id="a7y3k1"
scope {
    spawn(download_a());
    spawn(download_b());
}
```

scope kết thúc:

```text id="z8w2q6"
children complete/cancel according to policy
```

Điều này tránh task mồ côi.

Detached:

```text id="n5r4j0"
detach(task)
```

phải explicit.

---

# 38. Backpressure

I/O pipeline:

```text id="u3m8f2"
network
 ↓
buffer
 ↓
parser
 ↓
consumer
```

không được vô hạn allocation.

Channel/buffer APIs nên hỗ trợ bounded capacity.

Ví dụ:

```text id="e1z6x9"
Channel<T>(capacity = 1024)
```

Nếu đầy:

```text
producer waits
```

hoặc:

```text
try_send -> Full
```

Điều này kết hợp trực tiếp với `CHANNEL-001`.

---

# 39. File streaming

Streaming API:

```text id="q9k4w1"
Reader
Writer
```

không nên load toàn bộ file.

Ví dụ:

```text
while reader.read(buffer) > 0 {
    ...
}
```

hoàn toàn allocation-free nếu buffer được stack allocate.

---

# 40. Zero-copy transfer

Axiom nên có low-level API:

```text id="k6x2v8"
file.send_to(socket)
```

nếu OS hỗ trợ:

```text
sendfile
splice
copy_file_range
```

thì implementation có thể tránh user-space copy.

Nếu không:

```text
fallback
```

nhưng semantics giống nhau.

---

# 41. `mmap` + parser

Đây sẽ là một ví dụ rất mạnh cho Axiom:

```text id="w2r5q9"
let file = MappedFile.open(path);
let data = file.view();

parse(data);
```

Compiler biết:

```text
data
  ↓ depends on
file
```

Do đó:

```text
drop(file)
```

trước `parse` kết thúc sẽ bị từ chối.

Không cần lifetime annotation.

---

# 42. Các invariant mới

## `AIO-20 — Resource And Buffer Are Separate Ownership Domains`

File/socket sở hữu resource; buffer sở hữu memory.

## `AIO-21 — I/O Writes Through Explicit Capability`

Read operation cần WRITE capability đối với destination buffer.

## `AIO-22 — I/O Reads Through READ Capability`

Write operation cần READ capability đối với source buffer.

## `AIO-23 — Async Operation Preserves Buffer Validity`

Buffer không được invalidated trong khi operation có thể truy cập nó.

## `AIO-24 — Completion Releases Operation Dependency`

Khi OS operation hoàn tất, dependency tương ứng kết thúc.

## `AIO-25 — Cancellation Must Preserve Memory Safety`

Cancellation không được làm buffer/resource invalid khi operation còn active.

## `AIO-26 — Sync And Async Share Resource Semantics`

Khác nhau ở execution model, không phải ownership model.

## `AIO-27 — Async Does Not Imply Thread`

Async I/O không tự tạo OS thread.

## `AIO-28 — Blocking Does Not Imply Runtime Scheduler`

Sync blocking I/O có thể block execution resource trực tiếp.

## `AIO-29 — Readiness And Completion Are Backend Strategies`

High-level semantics không phụ thuộc epoll/IOCP/kqueue/io_uring.

## `AIO-30 — Zero-Copy Is An Optimization/Capability`

Không làm thay đổi observable I/O semantics.

## `AIO-31 — Convenience I/O May Allocate`

Nhưng primitive I/O không bắt buộc allocation.

## `AIO-32 — Low-Level WouldBlock Is Explicit`

High-level async API có thể chuyển readiness thành suspension.

## `AIO-33 — Scatter/Gather Preserves Capability Rules`

Mỗi buffer region phải hợp lệ và không conflict.

## `AIO-34 — Memory Mapping Creates Dependent Capability`

Mapped views phụ thuộc mapping lifetime.

## `AIO-35 — Device I/O Uses Explicit Storage Domains`

Host/device/external memory không bị coi là cùng một storage domain.

## `AIO-36 — OS Handle Is Not A Pointer`

OS resource identity và memory identity tách biệt.

## `AIO-37 — OS Error Information Is Not Lost`

Portable error mapping có thể giữ raw OS code.

## `AIO-38 — Async File Semantics Are Target Dependent Internally`

Không giả định mọi OS có native asynchronous file operations.

## `AIO-39 — Worker-Backed Async Must Be Explicit In Runtime Policy`

Không được âm thầm tạo unlimited worker threads.

## `AIO-40 — I/O Abstractions Must Not Require GC`

---

# 43. Bây giờ Axiom có một chuỗi ownership rất đẹp

Ví dụ network server:

```text
OS socket
    │
    ▼
TcpStream
    │ owns
    ▼
ReadOperation
    │ depends on
    ▼
Buffer
    │
    ▼
Parser view
```

Parser chỉ nhận:

```text id="w4h8m1"
view<u8>
```

nên không sở hữu buffer.

Nếu parser tạo object:

```text id="e7k2q9"
Message
```

thì ownership chuyển:

```text
buffer
   ↓ parse
Message
```

Không cần:

```text
GC
reference counting
lifetime annotations
```

---

# 44. Một điểm rất đáng chú ý

Với kiến trúc này, Axiom có thể hỗ trợ cả:

```text
embedded
```

đến:

```text
high-performance server
```

mà không cần hai ngôn ngữ.

### Embedded:

```text
mut_view
raw device register
DMA buffer
interrupt
```

### Server:

```text
Arc
Mutex
async
epoll/io_uring
TCP
TLS
```

Cùng ownership/capability semantics.

---

# 45. Chuỗi thiết kế hiện tại

Chúng ta đã đi từ:

```text
Language
 ↓
Memory
 ↓
Ownership
 ↓
Concurrency
 ↓
Atomic
 ↓
Trait
 ↓
Type
 ↓
ABI
 ↓
LIR
 ↓
Machine IR
 ↓
Object
 ↓
Linker
 ↓
Bootstrap
 ↓
Runtime
 ↓
OS ABI
 ↓
I/O
```

Đây gần như đã khóa toàn bộ **language execution foundation**.

Phần tiếp theo hợp lý không phải tiếp tục thêm API lẻ, mà là quay lên tầng language và giải quyết một vấn đề còn rất lớn:

# **ERROR-001 + PANIC-001 — Error, Result, Panic, Unwind**

Cần chốt chính xác:

```text
Result<T,E>
Option<T>
panic
abort
unwind
defer/drop
error propagation
?
operator
try
async cancellation
FFI exceptions
OS errors
```

Đặc biệt phải tránh việc `Result` trở thành một hệ thống exception trá hình hoặc `panic/unwind` khiến mọi binary đều phải kéo một runtime lớn.