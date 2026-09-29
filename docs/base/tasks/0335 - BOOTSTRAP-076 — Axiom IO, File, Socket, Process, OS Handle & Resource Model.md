Tiếp tục.

# BOOTSTRAP-076 — Axiom I/O, File, Socket, Process, OS Handle & Resource Model

**Trạng thái: FROZEN**

Mục tiêu của phần này là xây dựng một mô hình resource thống nhất cho:

```text
File
Directory
Socket
Pipe
Process
Thread
Event
Timer
Memory Mapping
Device
GPU resource
OS handle
Foreign handle
```

mà không cần:

- GC
- hidden reference counting
- hidden global runtime
- exception
- `new/delete`
- lifetime annotation
- một kiểu `Handle` khổng lồ cho mọi thứ.

Nguyên tắc trung tâm:

> **Resource lifetime và memory lifetime là hai thứ khác nhau, nhưng đều được quản lý bằng ownership + Drop.**

---

# 1. Resource không phải memory

Ví dụ:

```axiom
let file = File.open("data.bin")?
```

`file` có:

```text
resource identity
OS handle
ownership
cleanup obligation
```

Nhưng bản thân:

```text
OS file descriptor
```

không phải Axiom memory object.

Do đó:

```text
memory lifetime ≠ resource lifetime
```

---

# 2. Resource ownership

Mọi resource wrapper chuẩn của Axiom phải thuộc một trong các nhóm:

```text
Owned
Borrowed
Shared
HandleOnly
```

### Owned

Có trách nhiệm cleanup:

```text
File
Socket
Process
MMap
```

### Borrowed

Chỉ truy cập resource:

```text
view / capability
```

### Shared

Nhiều owner có thể cùng tồn tại:

```text
Arc<Resource>
```

hoặc abstraction tương đương.

### HandleOnly

Chỉ là logical/native identifier:

```text
WindowHandle
GpuHandle
ProcessId
```

không nhất thiết sở hữu resource.

---

# 3. Generic `Handle<T>`

Không nên dùng:

```axiom
Handle<T>
```

làm abstraction sở hữu mọi resource.

Thay vào đó:

```text
Handle<T>
```

nếu có, nên biểu diễn:

> **logical identity/typed handle**

chứ không mặc định có:

```text
Drop
close
ownership
```

Ví dụ:

```axiom
let pid: Handle<Process> = ...
```

có thể chỉ là identity.

Trong khi:

```axiom
let process: Process = ...
```

là owned resource.

---

# 4. OS handle wrapper

Platform layer có thể có:

```text
Fd
WinHandle
MachPort
SocketFd
GpuHandle
```

nhưng application API nên sử dụng abstraction có semantics rõ:

```text
File
Socket
Process
Event
```

Raw OS handle chỉ xuất hiện ở system/FFI boundary.

---

# 5. Owned File

Conceptually:

```axiom
let file = File.open("hello.txt")?
```

`file` sở hữu OS resource.

Khi scope kết thúc:

```text
Drop(file)
    ↓
close OS resource
```

Không cần:

```axiom
delete file
```

---

# 6. Move File

```axiom
let a = File.open(...)?
let b = a
```

`File` không Copy.

Semantics:

```text
a → Move → b
```

Sau đó:

```text
a
```

không còn usable.

Điều này ngăn:

```text
double close
```

ngay từ semantic layer.

---

# 7. Không implicit clone resource

Không cho:

```axiom
let b = a.clone()
```

tự động tạo:

```text
duplicate OS handle
```

`Clone` nếu có phải có semantics rõ.

Ví dụ:

```axiom
let b = a.duplicate()?
```

mới thực hiện:

```text
OS dup / DuplicateHandle / equivalent
```

---

# 8. `clone` và `duplicate`

Nên phân biệt:

```text
Clone
```

là generic semantic duplication.

Còn:

```text
duplicate()
```

là operation tạo một **resource identity/handle mới**.

Ví dụ:

```text
File.clone()
```

nếu tồn tại có thể gây nhầm lẫn.

API nên ưu tiên:

```text
file.duplicate()
```

để programmer hiểu đây là OS-level operation.

---

# 9. Drop không phải `close()`

Đây là điểm cực kỳ quan trọng.

```text
Drop
```

là deterministic cleanup.

Trong khi:

```text
close()
```

là explicit resource operation có thể **fallible**.

Ví dụ:

```axiom
file.close()?
```

có thể trả lỗi.

Nhưng:

```text
Drop(file)
```

không được trả `Result`.

---

# 10. Vì sao Drop không được fallible?

Nếu:

```axiom
Drop(file) -> Result
```

thì compiler phải xử lý:

```text
return
    ↓
Drop
    ↓
error?
```

và đặc biệt:

```text
panic
    ↓
Drop
    ↓
error
```

sẽ tạo nested failure complexity.

Do đó:

> **Business-level/resource-close errors phải được xử lý explicit trước Drop.**

---

# 11. Ví dụ

```axiom
let file = File.open(...)?

file.flush()?
file.close()?
```

Sau `close()` thành công:

```text
resource ownership complete
```

Drop sau đó không thực hiện cleanup lần nữa.

---

# 12. Double close

Type state nội bộ có thể:

```text
Open
Closed
Moved
```

Ví dụ:

```axiom
file.close()?
file.close()?
```

không nên tạo double-close machine operation.

API có thể:

- consume `self` khi close;
- hoặc chuyển state;
- hoặc làm close idempotent theo contract.

Khuyến nghị:

```text
close(self) -> Result
```

để sau khi close thành công, ownership được consumed.

---

# 13. Recommended File API

Conceptually:

```axiom
File.open(path) -> Result<File, FileError>

file.read(...)
file.write(...)
file.flush(...)
file.seek(...)
file.metadata(...)
file.close(self) -> Result<(), FileError>
```

Không cần:

```text
File::new
File::delete
```

---

# 14. File Drop

Nếu programmer không gọi:

```axiom
file.close()?
```

thì:

```text
scope end
    ↓
Drop
    ↓
best-effort OS close
```

Nhưng nếu close có lỗi, Drop không thể propagate `Result`.

Profile/runtime có thể:

```text
ignore
record diagnostic
abort
```

tùy resource/OS policy.

Khuyến nghị mặc định:

> **Drop cleanup is non-fallible and does not become application-level error.**

---

# 15. Flush và close khác nhau

```text
flush()
```

đảm bảo dữ liệu đi qua tầng buffering mà abstraction kiểm soát.

```text
close()
```

kết thúc resource.

Không giả định:

```text
close == durable-to-disk
```

Nếu cần durability:

```axiom
file.sync()?
```

explicit.

---

# 16. File position

`File` có logical cursor/position nếu mở theo kiểu sequential handle.

Ví dụ:

```text
read()
seek()
write()
```

sử dụng cùng file position.

Concurrent access phải không được giả định thread-safe nếu OS semantics không đảm bảo.

---

# 17. Concurrent File

Nếu hai execution domains cùng truy cập một File object:

```text
Share
```

phải được kiểm tra.

`File` không tự động:

```text
Share
```

chỉ vì OS cho phép descriptor được sử dụng bởi nhiều threads.

---

# 18. Duplicate handle

Nếu muốn hai owners:

```axiom
let a = file.duplicate()?
let b = file.duplicate()?
```

thì có:

```text
a resource identity
b resource identity
```

nhưng OS có thể vẫn chia sẻ:

```text
underlying open-file description
```

Đây là platform semantics cần document rõ.

---

# 19. File views

File không biến thành:

```text
view<u8>
```

một cách implicit.

Đọc dữ liệu tạo memory:

```axiom
let data = file.read_all()?
```

hoặc:

```axiom
file.read(buffer)?
```

Nếu caller cung cấp:

```axiom
mut_view<u8>
```

thì IO ghi trực tiếp vào caller-owned memory.

---

# 20. Zero-copy I/O

Axiom nên ưu tiên API:

```axiom
file.read_into(buffer)?
```

thay vì luôn:

```text
OS → temporary buffer → allocation → return
```

Compiler/runtime có thể lower tới:

```text
read
readv
pread
ReadFile
IOCP
io_uring
```

tùy backend.

---

# 21. Async File I/O

API:

```axiom
async fn read_into(
    file: view<File>,
    buffer: mut_view<u8>
) -> Result<usize, IOError>
```

nhưng semantics quan trọng hơn syntax:

> **In-flight operation phải giữ resource và buffer còn sống.**

---

# 22. In-flight I/O

Ví dụ:

```text
File
 ↓
async read
 ↓
OS operation pending
```

thì:

```text
File resource
buffer
```

không được bị Drop/relocate trước khi operation hoàn thành hoặc cancellation contract kết thúc.

Đây chính là:

```text
in-flight lifetime retention
```

đã thống nhất với GPU và async model.

---

# 23. Không cần GC cho async I/O

Future có thể giữ:

```text
File
Buffer
state
```

trong compiler-generated state machine.

Khi Future Drop:

```text
Future state dropped
```

nhưng external OS operation **không mặc định bị cancel**.

---

# 24. Cancellation

Cancellation phải explicit.

Ví dụ:

```axiom
let operation = file.read_async(...)?

operation.cancel()
```

hoặc cancellation token.

Không coi:

```text
Drop(Future)
```

là:

```text
cancel OS I/O
```

một cách mặc định.

---

# 25. Vì sao?

Nhiều OS operation:

```text
read
DNS
connect
GPU command
```

có cancellation semantics khác nhau.

Axiom không nên giả vờ tất cả đều cancel được.

---

# 26. Blocking vs non-blocking

Đây phải là semantic distinction.

```text
File.read()
```

có thể là blocking operation.

```text
File.read_async()
```

là asynchronous operation.

Không tự động biến synchronous API thành async bằng hidden thread pool.

---

# 27. Hidden thread pool bị cấm mặc định

Ví dụ:

```axiom
file.read()
```

không được compiler âm thầm:

```text
spawn worker
    ↓
blocking syscall
    ↓
await result
```

vì điều đó tạo:

- hidden threads
- hidden runtime
- unpredictable resource consumption.

Nếu library muốn worker-backed async:

```text
explicit runtime policy
```

---

# 28. Readiness vs completion

Axiom không nên ép một mô hình OS I/O duy nhất.

Có hai family:

```text
Readiness:
epoll
kqueue
poll

Completion:
IOCP
io_uring-style completion
```

Library/runtime abstraction có thể thống nhất ở mức:

```text
AsyncOperation
```

nhưng backend giữ semantics tương ứng.

---

# 29. Socket

`Socket` là owned resource.

Ví dụ:

```axiom
let socket = TcpSocket.connect(address)?
```

Drop:

```text
close socket
```

---

# 30. Socket ownership

Socket:

```text
Copy = false
Clone = explicit
Drop = deterministic
Send = platform/library-dependent
Share = explicit
```

Không cho implicit shared socket.

---

# 31. Socket shutdown

Đây là operation khác `close`.

```text
shutdown(Read)
shutdown(Write)
shutdown(Both)
```

để half-close TCP.

Sau đó:

```text
close()
```

mới kết thúc descriptor.

---

# 32. TCP stream vs listener

Không dùng một type cho tất cả.

```text
TcpListener
TcpStream
UdpSocket
```

giúp state machine rõ ràng.

---

# 33. Socket address

Network address nên là value:

```text
Ipv4Addr
Ipv6Addr
SocketAddr
```

và `Copy` nếu nhỏ/đơn giản.

Không phải resource.

---

# 34. Network buffers

API nên ưu tiên:

```axiom
socket.read(buffer)?
socket.write(data)?
```

với:

```text
view<u8>
mut_view<u8>
```

để tránh allocation.

---

# 35. Partial read/write

Không được giả định:

```text
read(N) == N bytes
write(N) == N bytes
```

API phải trả số byte thực tế.

Ví dụ:

```text
read(buffer) -> Result<usize>
```

---

# 36. Async socket

```text
read_async
write_async
accept_async
connect_async
```

không được giữ `mut_view` qua await nếu buffer có thể bị dùng conflicting ở nơi khác.

Compiler kiểm tra capability.

---

# 37. Timeout

Không nên biến timeout thành global runtime behavior.

API:

```text
with_timeout(operation, duration)
```

hoặc:

```text
socket.read_with_deadline(...)
```

là explicit.

---

# 38. Deadline vs duration

Nên phân biệt:

```text
Duration
Deadline
```

`Duration`:

```text
bao lâu
```

`Deadline`:

```text
đến thời điểm nào
```

Deadline thường tốt hơn cho chuỗi async operation vì tránh drift.

---

# 39. Pipe

```text
Pipe
```

là owned resource.

Có thể tách:

```text
PipeReader
PipeWriter
```

để ownership direction rõ ràng.

---

# 40. Process

`Process` là resource wrapper.

```axiom
let process = Process.spawn(...)?
```

sở hữu process observation/control handle.

Không có nghĩa process memory thuộc Axiom.

---

# 41. Process identity

Phân biệt:

```text
Process
ProcessId
```

`Process`:

```text
owned resource/control capability
```

`ProcessId`:

```text
logical OS identity
```

---

# 42. `wait`

```axiom
let status = process.wait()?
```

có semantics:

```text
observe process completion
```

và đồng thời có thể giải phóng process-related OS resource.

---

# 43. Async wait

```axiom
let status = process.wait_async().await?
```

in-flight wait giữ:

```text
Process
```

đến khi operation hoàn thành.

---

# 44. Process exit status

Không biến tất cả thành:

```text
Result<(), Error>
```

Ví dụ process exit code `1` không nhất thiết là API failure.

Nên:

```text
wait() -> Result<ExitStatus, ProcessError>
```

trong đó:

```text
ProcessError
```

là lỗi **không thể wait/observe process**.

Còn:

```text
ExitStatus
```

là kết quả của process.

---

# 45. Signal / terminate

Platform API explicit:

```text
process.terminate()
process.kill()
process.signal(...)
```

Không hidden destructor behavior.

Drop `Process` không mặc định kill process.

---

# 46. Đây là một quyết định quan trọng

```text
Drop(Process)
```

phải nghĩa:

> **release Axiom's process handle/observation resource**

không phải:

> kill underlying process.

Nếu muốn kill:

```axiom
process.kill()?
```

explicit.

---

# 47. Thread

Thread object:

```text
Thread
JoinHandle<T>
```

là resource/execution abstractions.

`JoinHandle<T>` là observation capability theo BOOTSTRAP-070.

---

# 48. Thread Drop

Không được mặc định:

```text
Drop(JoinHandle)
→ kill thread
```

vì thread termination cưỡng bức nguy hiểm với resource invariants.

Detached execution phải explicit:

```text
handle.detach()
```

---

# 49. Event

OS event/synchronization resource:

```text
Event
```

có:

```text
wait
signal
reset
```

depending on semantics.

Không nhầm:

```text
Event
```

với:

```text
Atomic
```

hoặc:

```text
Condvar
```

---

# 50. Timer

Timer có thể là:

```text
Timer
Deadline
TimerHandle
```

nhưng không cần global timer runtime.

Synchronous timer có thể dùng OS primitive.

Async timer thuộc async runtime/library.

---

# 51. Memory mapping

`MMap` là một resource đặc biệt.

```axiom
let map = MMap.map(file, ...)
```

có:

```text
resource lifetime
memory region lifetime
```

gắn với nhau.

---

# 52. MMap → view

Nếu mapping read-only:

```text
MMap
   ↓
view<u8>
```

có thể cung cấp zero-copy access.

Nhưng capability provenance là:

```text
MMap storage
```

không phải `File` trực tiếp.

---

# 53. MMap stable address

Nếu API expose:

```text
raw address
```

thì address becomes observable.

Compiler không được relocate mapping.

Nhưng OS virtual mapping bản thân đã có storage contract:

```text
stable mapped address
```

trong phạm vi mapping.

---

# 54. Unmap

```axiom
map.unmap()?
```

không được thực hiện khi:

```text
view(map)
```

vẫn live.

Compiler capability verifier chặn:

```text
unmap
```

nếu còn dependent capabilities.

---

# 55. MMap Drop

Nếu programmer không explicit unmap:

```text
Drop(MMap)
```

unmaps deterministic.

Không cần GC scan.

---

# 56. File + MMap

Không nên bắt buộc:

```text
MMap owns File
```

hoặc:

```text
File owns MMap
```

Một mapping có thể giữ resource contract độc lập.

Nếu OS yêu cầu underlying object sống:

```text
MMap
```

phải retain dependency hoặc mapping semantics phải đảm bảo nó không còn phụ thuộc File handle.

---

# 57. Device resource

Device API:

```text
Device
DeviceBuffer
DeviceContext
GpuEvent
```

là resource abstractions.

Không có generic:

```text
Resource<T>
```

bắt mọi platform vào cùng một state machine.

---

# 58. GPU resource

Ví dụ:

```text
DeviceBuffer<f32>
```

có:

```text
ownership
storage domain = DEVICE
```

và:

```text
DeviceView<f32>
```

là non-owning capability.

---

# 59. GPU in-flight lifetime

Nếu:

```text
kernel(buffer)
```

đang chạy:

```text
buffer
```

không thể bị Drop.

GPU event/future phải retain resource lifetime đến completion.

Đã thống nhất với:

```text
async I/O
```

---

# 60. Resource Send

Resource không mặc định `Send`.

Ví dụ OS handle có thể:

```text
Send
```

nhưng GUI handle có thể:

```text
!Send
```

do platform affinity.

Compiler/library derive hoặc khai báo dựa trên semantics.

---

# 61. Resource Share

Resource không mặc định `Share`.

Ví dụ:

```text
File
```

có thể được duplicate để tạo independent owner thay vì cho nhiều thread share một wrapper.

Đây thường an toàn và rõ hơn.

---

# 62. GUI resource

Các resource có thread affinity:

```text
Window
UIContext
GraphicsContext
```

có thể mang execution-domain contract:

```text
PinnedToThread
```

nhưng đây là library/system semantics, không tạo Core primitive.

---

# 63. Raw OS handle

System layer có thể expose:

```text
raw_handle()
```

nhưng kết quả là machine-level value.

Ví dụ:

```text
RawFd
RawHandle
MachPort
```

không tự mang ownership.

---

# 64. Borrowed raw handle

Nếu function chỉ cần sử dụng handle tạm thời:

```text
with_raw_handle(...)
```

là preferable.

Compiler đảm bảo:

```text
owner alive
```

trong thời gian foreign call.

---

# 65. FFI ownership

FFI contract phải nói rõ:

```text
borrowed
owned by Axiom
owned by foreign
shared
handle-only
```

Không đoán.

---

# 66. Foreign close

Nếu foreign library trả:

```text
HANDLE
```

Axiom wrapper phải biết:

```text
who closes it?
```

Ví dụ:

```text
OwnedByForeign
```

thì Drop Axiom wrapper **không được close**.

---

# 67. Foreign-owned resource

Có thể:

```axiom
ForeignThing.from_raw(handle)
```

nhưng construction thường unsafe vì programmer phải xác nhận ownership contract.

Sau đó safe wrapper có semantics rõ.

---

# 68. Handle duplication

Mọi operation dạng:

```text
dup
clone_handle
inherit
share
export
```

phải explicit.

Không có:

```text
Copy(File)
```

---

# 69. Inheritance sang child process

Ví dụ file/socket handle inheritance:

```text
Process.spawn(..., inherit=[file])
```

là explicit.

Không để mọi OS resource tự động inherit.

---

# 70. Close-on-exec

System layer nên hỗ trợ contract:

```text
inherit
non-inherit
```

và target-specific implementation.

Không để behavior phụ thuộc vô tình vào OS default.

---

# 71. Resource errors

Không gom mọi lỗi thành một enum khổng lồ:

```text
IOError
```

duy nhất.

Nên có hierarchy/type families ở library:

```text
FileError
SocketError
ProcessError
MMapError
```

với native OS error code bên trong.

---

# 72. Native error preservation

Ví dụ:

```text
errno
GetLastError
NTSTATUS
HRESULT
Mach error
```

không được mất thông tin chỉ vì Axiom muốn unified API.

Có thể có:

```text
OsError
```

chứa:

```text
platform
code
category
```

---

# 73. Không dùng exception

Ví dụ:

```axiom
let file = File.open(path)?
```

lỗi đi qua:

```text
Result
```

Không có:

```text
try/catch
throw
```

---

# 74. Async error

```axiom
let n = socket.read_async(buf).await?
```

có:

```text
Future<Result<usize, SocketError>>
```

không:

```text
Future throws SocketException
```

---

# 75. Resource state machine

Compiler/library có thể model resource states:

```text
Created
Open
Pending
Closed
Moved
```

nhưng **không nhất thiết expose typestate generic cho programmer**.

Compiler có thể kiểm tra các state quan trọng ở MIR.

---

# 76. State-dependent APIs

Một số resource thực sự cần state distinction.

Ví dụ:

```text
TcpListener
TcpStream
```

thay vì:

```text
Socket<Connected/Listening/Closed>
```

trong Core.

Ưu tiên concrete types nếu chúng đơn giản hơn.

---

# 77. Resource cleanup order

Ví dụ:

```axiom
let file = ...
let map = ...
```

nếu map phụ thuộc file, compiler Drop order phải tôn trọng dependency.

Thông thường:

```text
reverse initialization
```

nhưng capability/provenance verifier không cho phép invalid destruction.

---

# 78. Resource dependency

Có thể có:

```text
File
 ↓
MMap
 ↓
view
```

Khi:

```text
view live
```

không thể:

```text
unmap
```

và khi:

```text
MMap live
```

nếu contract yêu cầu File sống thì không thể close File trước.

Đây là ownership/capability graph, không phải GC graph.

---

# 79. Resource graph không phải reference counting

Compiler biết:

```text
MMap depends on File
```

và có thể generate cleanup order.

Không cần runtime:

```text
refcount++
refcount--
```

cho dependency thông thường.

---

# 80. Shared resource

Khi thực sự cần:

```text
Arc<File>
```

hoặc resource-specific shared abstraction.

Nhưng:

```text
Arc<File>
```

không biến File operations thành magically thread-safe.

---

# 81. Shared mutable resource

Ví dụ:

```text
Arc<Mutex<File>>
```

là:

```text
shared ownership
+
synchronization
```

Compiler kiểm tra đúng theo concurrency model.

---

# 82. Async shared resource

Không nên:

```text
Arc<Mutex<File>>
```

rồi giữ sync mutex qua `.await`.

Dùng:

```text
AsyncMutex
```

nếu semantics yêu cầu.

---

# 83. Resource + scheduler

Không resource API nào được mặc định yêu cầu:

```text
global executor
```

Ví dụ:

```text
File.open()
```

hoạt động trong synchronous freestanding/hosted environment.

Chỉ:

```text
async operation
```

mới cần async runtime nếu backend yêu cầu.

---

# 84. Runtime capability

Các runtime components có thể được link riêng:

```text
file runtime
network runtime
async runtime
thread runtime
```

Thực tế một số OS API có thể không cần runtime nào ngoài syscall/FFI wrapper.

---

# 85. Freestanding

Một chương trình:

```text
bare metal
kernel
bootloader
embedded
```

có thể dùng:

```text
raw device APIs
volatile
DMA
interrupts
```

mà không cần:

```text
File
Socket
Process
```

và không link OS runtime.

---

# 86. Hosted

Program bình thường:

```text
main()
```

có thể dùng:

```text
File
Net
Process
Thread
Async
```

và chỉ link phần runtime/library thực sự reachable.

---

# 87. Syscall

Không đưa syscall vào Core.

System layer:

```text
linux.syscall
windows.nt
macos.mach
```

có thể cung cấp low-level interfaces.

Safe wrappers phía trên:

```text
File
Socket
Process
```

---

# 88. Direct syscall

System programmer có thể:

```text
unsafe
```

gọi syscall interface.

Nhưng unsafe không tự vô hiệu:

```text
ownership
capability
```

verification.

---

# 89. I/O memory model

Memory buffer dùng cho I/O phải được giữ live trong thời gian operation.

Compiler không được:

```text
stack promote
free
relocate
```

nếu OS operation vẫn có reference tới buffer.

---

# 90. DMA

DMA đặc biệt quan trọng.

```text
CPU
 ↓
Device
 ↓
DMA buffer
```

buffer có thể phải:

```text
pinned/stable
physically accessible
cache coherent
```

Đây không phải semantics của `view<T>` thông thường.

---

# 91. DMA buffer

System library nên có:

```text
DmaBuffer<T>
```

với explicit storage contract.

Không thêm `Pin<T>` vào Core.

---

# 92. `DmaBuffer` có thể cung cấp view

Ví dụ:

```text
DmaBuffer<T>
    ↓
DeviceView<T>
```

hoặc CPU:

```text
view<T>
```

tùy storage/coherency contract.

---

# 93. Stable address

Resource APIs không được giả định mọi memory stable.

Nếu OS API yêu cầu:

```text
stable virtual address
```

thì abstraction phải tạo contract.

Ví dụ:

```text
MMap
DmaBuffer
StableBox
```

---

# 94. Async + resource Drop

Nếu:

```text
operation.await
```

đang pending:

```text
resource
```

phải được retain bởi Future/operation state.

Nếu operation bị cancellation:

```text
cancellation protocol
```

quyết định khi nào resource có thể release.

---

# 95. Resource cancellation không đồng nhất

Ví dụ:

```text
socket read
file read
process wait
GPU command
timer
```

có cancellation semantics khác nhau.

Do đó:

> **Cancellation is a resource-specific contract, not a universal Drop rule.**

---

# 96. Resource identity

Phân biệt ba loại identity đã freeze:

```text
Value Identity
Storage Identity
Logical Identity
```

và thêm resource semantics:

```text
Resource Identity
```

Ví dụ:

```text
File wrapper
```

có thể có:

```text
Value identity   = wrapper value
Resource identity = underlying OS resource
Handle identity  = OS handle
```

Không được trộn chúng.

---

# 97. `Handle<T>` chỉ là logical identity

Ví dụ:

```axiom
let id: Handle<Process> = process.id()
```

`id` không giữ process alive.

Sau:

```axiom
drop(process)
```

handle có thể trở thành stale.

Nếu cần chống stale:

```text
generation handle
```

hoặc OS-specific identity semantics.

---

# 98. Safe handle resolution

Nếu:

```axiom
registry.resolve(handle)
```

trả:

```text
view<T>
```

thì resolution phải establish:

```text
provenance
validity
lifetime
```

trước khi safe capability được tạo.

Đây tiếp tục `AVERIFY-88..89`.

---

# 99. Nguyên tắc API tổng thể

Axiom resource API phải đi theo:

```text
Acquire
    ↓
Owned value
    ↓
Borrow/view
    ↓
Use
    ↓
Explicit fallible close (optional)
    ↓
Drop fallback
```

và:

```text
async operation
    ↓
in-flight retention
    ↓
completion/cancellation
    ↓
resource release
```

---

# 100. Frozen Invariants — `AIO-20..100`

### Resource ownership

- **AIO-20** Resources are distinct from ordinary memory values.
- **AIO-21** Resource lifetime is distinct from memory lifetime.
- **AIO-22** Owned resources have deterministic cleanup obligations.
- **AIO-23** Borrowed resources do not own the underlying resource.
- **AIO-24** Shared resources require explicit shared ownership.
- **AIO-25** Handle-only values do not imply ownership.
- **AIO-26** `Handle<T>` does not implicitly keep a resource alive.
- **AIO-27** Resource wrappers are not implicitly Copy.
- **AIO-28** Resource duplication is explicit.
- **AIO-29** Resource inheritance/export is explicit.
- **AIO-30** Ownership transfer uses ordinary Move semantics.

### Drop / close

- **AIO-31** Owned resources have deterministic Drop.
- **AIO-32** Resource Drop is non-fallible.
- **AIO-33** Fallible cleanup is exposed through explicit operations.
- **AIO-34** `close()` does not implicitly become Drop.
- **AIO-35** Successful consuming close transfers resource ownership to the closed state.
- **AIO-36** Double-close is prevented by resource state/ownership semantics.
- **AIO-37** Drop cannot produce recoverable application errors.
- **AIO-38** Resource Drop does not imply process termination unless explicitly specified by the resource type.
- **AIO-39** Process-handle Drop does not implicitly kill the process.
- **AIO-40** Resource cleanup preserves ownership invariants.

### File / memory

- **AIO-41** File ownership is explicit.
- **AIO-42** File duplication is explicit.
- **AIO-43** File position semantics are explicit.
- **AIO-44** File buffering is distinct from durable storage.
- **AIO-45** Flush and durability synchronization are distinct operations.
- **AIO-46** File I/O may operate directly on caller-provided views.
- **AIO-47** File operations do not imply hidden allocations.
- **AIO-48** File resources do not implicitly become shared resources.
- **AIO-49** Memory mappings are explicit resources.
- **AIO-50** An `MMap` may provide a view over mapped storage.
- **AIO-51** Unmapping cannot invalidate a live capability.
- **AIO-52** Stable mapped addresses are explicit storage contracts.
- **AIO-53** Mapped memory lifetime is tracked independently from ordinary heap lifetime.
- **AIO-54** DMA buffers use explicit storage contracts.
- **AIO-55** DMA does not introduce a Core `Pin` primitive.

### Network

- **AIO-56** Sockets are owned resources unless explicitly borrowed/shared.
- **AIO-57** Socket duplication is explicit.
- **AIO-58** Socket shutdown is distinct from socket close.
- **AIO-59** TCP streams and listeners have distinct resource semantics.
- **AIO-60** Partial network reads/writes are represented explicitly.
- **AIO-61** Network buffers may use Axiom views without copying.
- **AIO-62** Async network operations retain required resources and buffers.
- **AIO-63** Network timeout/deadline behavior is explicit.
- **AIO-64** Readiness and completion are backend mechanisms, not conflicting source semantics.
- **AIO-65** Hidden worker-thread conversion of blocking APIs is not a Core requirement.

### Process / execution resources

- **AIO-66** Process identity is distinct from process ownership.
- **AIO-67** `ProcessId` does not imply process lifetime.
- **AIO-68** Process waiting observes process completion.
- **AIO-69** Process exit status is distinct from process API failure.
- **AIO-70** Process termination is explicit.
- **AIO-71** Thread ownership follows the concurrency model.
- **AIO-72** Dropping a join/observation handle does not implicitly terminate execution.
- **AIO-73** Detached execution is explicit.
- **AIO-74** Resource thread-affinity may be part of library/system contracts.
- **AIO-75** Resource Send/Share properties are derived or explicitly constrained by semantics.

### Async / GPU / FFI

- **AIO-76** Async resource operations retain all required in-flight storage.
- **AIO-77** Dropping a Future does not universally imply cancellation of external operations.
- **AIO-78** Cancellation semantics are resource-specific.
- **AIO-79** Completion and cancellation are distinct states.
- **AIO-80** Resource release cannot occur before required in-flight operations finish or are safely cancelled.
- **AIO-81** GPU resources follow the same ownership/lifetime principles.
- **AIO-82** GPU in-flight operations retain required storage/resources.
- **AIO-83** Foreign resource ownership is explicit.
- **AIO-84** Foreign handles do not automatically acquire Axiom ownership.
- **AIO-85** Raw OS handles do not automatically become safe capabilities.
- **AIO-86** Unsafe handle wrapping establishes explicit trusted preconditions.
- **AIO-87** Safe verification resumes after valid resource/FFI boundaries.
- **AIO-88** Foreign resource cleanup cannot propagate recoverable errors through Drop.
- **AIO-89** FFI does not implicitly synchronize resource access.
- **AIO-90** FFI allocation and deallocation domains remain explicit.

### Runtime / system

- **AIO-91** Blocking and asynchronous APIs are semantically distinct.
- **AIO-92** Async APIs do not require a monolithic global runtime.
- **AIO-93** Hidden global thread pools are not required by resource APIs.
- **AIO-94** Runtime components are linked only when required.
- **AIO-95** Freestanding programs may omit OS resource libraries.
- **AIO-96** System calls belong to the system layer.
- **AIO-97** Native OS error information may be preserved.
- **AIO-98** Unified error APIs must not erase required platform error identity.
- **AIO-99** Resource abstractions may be optimized/erased without changing resource semantics.
- **AIO-100** All resource APIs preserve ownership, capability, Drop, concurrency, async, storage and FFI invariants.

---

# Kiến trúc resource của Axiom sau 076

Ta hiện có một mô hình khá thống nhất:

```text
                         RESOURCE
                            │
             ┌──────────────┼──────────────┐
             │              │              │
           Owned         Borrowed        HandleOnly
             │              │              │
          Drop          view/cap        identity
             │
       ┌─────┴─────┐
       │           │
    close()?    duplicate()
```

Với async:

```text
Resource
   │
async operation
   │
   ▼
Future / Operation
   │
   ├── Pending
   │      │
   │      └── resource + buffer retained
   │
   └── Ready
          │
          ▼
       release/use
```

Và quan trọng nhất:

```text
             Ownership
                 │
                 ▼
            Resource
                 │
        ┌────────┼────────┐
        ▼        ▼        ▼
      File    Socket    Process
        │        │        │
        └────────┼────────┘
                 │
             Capability
                 │
                 ▼
          view / mut_view
```

**Không cần một hệ thống reference mới cho File, Socket, GPU, DMA, MMap...**

---

## Một nguyên tắc tôi muốn giữ rất chặt từ đây

Axiom không nên cố làm cho mọi resource có cùng API.

Ví dụ:

```text
File.close()
Socket.shutdown()
Process.wait()
MMap.unmap()
GpuEvent.wait()
Thread.join()
```

có thể khác nhau hoàn toàn về semantics.

Điểm thống nhất nằm ở **ownership/lifetime/error/capability model**, không phải ở việc ép chúng vào một interface khổng lồ.

---

### Bước kiến trúc tiếp theo

`BOOTSTRAP-077` nên là:

# Axiom FFI/System ABI Deep Model & OS Interoperability

Tập trung vào việc biến những gì vừa thiết kế thành **ranh giới thực sự giữa Axiom và thế giới bên ngoài**:

```text
C ABI
Windows API
POSIX
Linux syscalls
macOS/Mach
iOS
Android
WASM host imports
GPU driver API
shared libraries
callbacks
function pointers
opaque handles
variadic APIs
struct layout
unions
bitfields
C strings
error codes
thread-local state
foreign ownership
foreign async callbacks
```

Đây sẽ là bước quan trọng trước khi chuyển sang các subsystem cấp cao hơn như **filesystem/path, networking protocol, serialization và cuối cùng là runtime-free application architecture**.