Tiếp tục.

# BOOTSTRAP-071 — Axiom I/O, Resource, OS Handle & External Resource Model

**Trạng thái: FROZEN**

Đây là phần nối trực tiếp:

```text
Axiom ownership
      ↓
resource lifetime
      ↓
File / Socket / Process / OS Handle
      ↓
sync / async
      ↓
FFI / OS
```

Mục tiêu là giải quyết triệt để một vấn đề quan trọng:

> **Tài nguyên hệ thống phải có lifetime xác định, cleanup deterministic, không cần GC, nhưng API không được biến thành một đống pointer/reference/lifetime annotation.**

---

# 1. Resource ≠ Memory

Axiom phải phân biệt ba lifetime:

```text
Value lifetime
Resource lifetime
Memory lifetime
```

Ví dụ:

```axiom
let file = File.open("data.bin")?
```

`file` có:

```text
Value
 ├── ownership
 ├── OS resource
 └── internal storage
```

Khi:

```axiom
drop(file)
```

thì **resource ownership kết thúc**.

Điều này không nhất thiết có nghĩa mọi memory backing file object lập tức được deallocate.

---

# 2. Resource type

Resource là type có:

```text
Drop
```

và đại diện cho một external/system resource.

Ví dụ:

```text
File
Socket
TcpStream
Process
ThreadHandle
GpuBuffer
MappedMemory
Window
Device
```

Không cần một `Resource` base class.

Trait có thể tồn tại:

```axiom
trait Resource {
    fn close(self) -> Result<unit, Error>
}
```

nhưng đây là library abstraction, không phải superclass.

---

# 3. Resource không Copy

Một resource sở hữu tài nguyên độc quyền:

```text
File
Socket
Process
```

thông thường:

```text
!Copy
Drop
```

Do đó:

```axiom
let a = File.open(...)?
let b = a
```

là Move.

Sau đó `a` không còn sử dụng được.

---

# 4. Move resource

Move:

```text
a
 │
 └──── Move ────→ b
```

không nhất thiết copy OS handle.

Ví dụ:

```text
fd = 42
```

có thể chỉ chuyển ownership metadata của compiler.

Native code có thể chỉ cần truyền một register.

---

# 5. Explicit duplication

Nếu OS resource hỗ trợ duplicate:

```axiom
let b = a.try_clone()?
```

đây là operation **có semantic cost**.

Không bao giờ biến:

```text
b = a
```

thành implicit OS handle duplication.

---

# 6. Borrow resource

Nếu function chỉ cần sử dụng resource tạm thời:

```axiom
fn read_header(file: view<File>) -> Result<Header, Error>
```

không chuyển ownership.

Compiler đảm bảo:

```text
File owner
    │
    └── view<File>
          │
          └── cannot outlive File
```

Không cần programmer viết lifetime.

---

# 7. Resource capability

Đây là nơi `view` rất mạnh.

Ví dụ:

```axiom
fn read(file: view<File>, buffer: mut_view<u8>) -> Result<usize, Error>
```

Function nhận:

```text
File READ capability
+
Buffer WRITE capability
```

Compiler có thể kiểm tra:

- file còn sống;
- buffer còn sống;
- buffer mutable;
- không alias conflict.

---

# 8. OS Handle không phải resource ownership

Một raw OS handle:

```text
int fd
HANDLE h
socket_t s
```

không tự có ownership semantics.

Axiom phải phân biệt:

```text
RawHandle
OwnedHandle
BorrowedHandle
```

Ví dụ:

```text
OwnedHandle<File>
```

có Drop.

Trong khi:

```text
BorrowedHandle
```

không đóng resource.

---

# 9. Handle-only resources

Một số hệ thống resource có lifecycle do OS quản lý.

Axiom có thể dùng:

```text
Handle<T>
```

nhưng:

> `Handle<T>` là logical/resource identity, không phải raw pointer.

Handle có thể chứa:

```text
index
generation
OS identifier
opaque token
```

Representation compiler-controlled.

---

# 10. Ownership contract

Mỗi external resource wrapper phải khai báo semantic contract:

```text
Ownership:
    Owned
    Borrowed
    Shared
    ForeignOwned
    HandleOnly
```

Đây là contract của type/API, không phải runtime reflection.

---

# 11. Foreign-owned resource

Ví dụ C API:

```text
create()
...
foreign_destroy()
```

Axiom wrapper có thể:

```text
ForeignOwned<T>
```

hoặc concrete wrapper.

Drop gọi foreign destructor.

Nhưng nếu foreign API yêu cầu:

```text
close() -> error
```

thì không được cố trả error từ Drop.

---

# 12. Fallible cleanup

Ví dụ:

```axiom
file.close()?
```

là operation có thể thất bại.

Sau đó:

```axiom
drop(file)
```

chỉ là fallback cleanup.

Pattern:

```text
close()
   ↓ success
ownership/resource cleanup
```

hoặc:

```text
close()
   ↓ failure
caller handles error
   ↓
Drop performs best-effort/final cleanup
```

---

# 13. Drop không được throw

Đã freeze:

```text
Drop = non-fallible
```

Không có:

```text
Drop → Result
```

theo semantics Core.

Nếu cleanup failure cần quan sát:

```text
close()
shutdown()
flush()
commit()
```

phải được gọi explicit.

---

# 14. File

Standard API conceptually:

```axiom
let file = File.open(path)?
let n = file.read(buffer)?
file.write(data)?
```

Compiler hiểu ownership nhưng syntax vẫn đơn giản.

---

# 15. File modes

Không nên biến permission thành runtime booleans nếu có thể biểu diễn compile-time.

Có thể có:

```text
Read
Write
Append
Create
Truncate
```

như flags/options.

Nếu mode ảnh hưởng semantics đáng kể, generic capability có thể được sử dụng.

Nhưng **không over-genericize API**.

---

# 16. File cursor

File position là state của resource.

Ví dụ:

```axiom
file.read(...)
file.seek(...)
file.read(...)
```

Không cần `FileReader` object hierarchy.

Các method chỉ là functions trên struct:

```text
File.read
File.seek
File.flush
```

phù hợp hoàn toàn với struct-only model.

---

# 17. Buffered I/O

`BufferedReader`/`BufferedWriter` là wrapper:

```text
File
 ↓
Buffer
 ↓
BufferedReader
```

Ownership:

```text
BufferedReader
   owns File
```

hoặc:

```text
BufferedReader
   borrows File
```

tùy constructor.

Không có hidden GC.

---

# 18. Memory-mapped file

API:

```text
MappedFile
```

có:

```text
resource lifetime
storage lifetime
view lifetime
```

Ví dụ:

```text
MappedFile
   │
   └── view<u8>
```

Không được unmap khi view còn live.

Verifier có thể phát hiện:

```text
drop(mapped)
```

trong khi view còn tồn tại → reject.

---

# 19. `mmap` và stable address

Mapped memory thường có observable address.

Do đó:

```text
stable address contract
```

được thiết lập.

Optimizer không thể tùy tiện scalarize hoặc relocate vùng memory đó.

---

# 20. Socket

Socket là resource:

```text
Socket
!Copy
Drop
```

API:

```axiom
let socket = Tcp.connect(address)?
let n = socket.read(buffer)?
socket.write(data)?
```

---

# 21. Sync socket

Synchronous API:

```text
socket.read(...)
```

có thể block.

Blocking không phải semantics cấm trong Core.

Nhưng nó phải là explicit system/library operation.

---

# 22. Async socket

Async:

```axiom
let n = socket.read_async(buffer).await?
```

trả Future.

Storage lifetime:

```text
buffer
 │
 └── retained by in-flight operation
```

Không thể:

```text
drop(buffer)
```

khi I/O operation vẫn cần nó.

---

# 23. Zero-copy I/O

Axiom nên ưu tiên API:

```text
read(buffer: mut_view<u8>)
```

thay vì:

```text
read() -> Bytes
```

khi performance quan trọng.

Compiler không bắt buộc allocation.

---

# 24. Ownership-based I/O

Đồng thời nên có owned-buffer API:

```text
read_async(buffer)
    → Future<(Buffer, usize)>
```

để tránh view sống qua await.

Mô hình:

```text
Buffer
  ↓ Move
I/O operation
  ↓
Future
  ↓
Buffer returned
```

Đây là pattern rất phù hợp với Axiom.

---

# 25. I/O cancellation

Nếu:

```axiom
let op = socket.read_async(buffer)
```

thì drop Future không mặc định có nghĩa:

```text
cancel OS I/O
```

Cancellation phải explicit nếu backend hỗ trợ.

Ví dụ:

```text
IoHandle.cancel()
```

hoặc cancellation token.

---

# 26. Completion

I/O completion là synchronization/event.

Nhưng:

```text
completion
```

không đồng nghĩa với:

```text
arbitrary memory fence
```

Semantics phải được library/platform contract định nghĩa.

---

# 27. OS process

`Process` là resource wrapper.

```axiom
let process = Process.spawn(command)?
let status = process.wait()?
```

`Process` ownership không nhất thiết có nghĩa process chết khi object Drop.

Đây là điểm cần tách:

```text
Process resource ownership
≠
Process lifetime
```

---

# 28. Child process policy

Drop của:

```text
ChildProcess
```

không mặc định:

```text
kill process
```

vì đó là một semantic side effect quá mạnh.

API explicit:

```text
terminate()
kill()
detach()
wait()
```

---

# 29. Process stdin/stdout

Các stream:

```text
stdin
stdout
stderr
```

có thể là owned resource riêng.

Ownership graph:

```text
Process
 ├── stdin
 ├── stdout
 └── stderr
```

API phải định nghĩa rõ liệu `Process` sở hữu stream hay chúng có ownership độc lập.

---

# 30. OS event handles

Windows:

```text
HANDLE
```

Linux:

```text
fd
```

macOS:

```text
mach port / fd / object
```

không được đưa trực tiếp vào portable Core.

System layer tạo abstraction:

```text
OsHandle
```

và target-specific implementation.

---

# 31. Cross-platform abstraction

Standard API:

```text
File
Socket
Process
```

không expose trực tiếp:

```text
fd
HANDLE
mach_port
```

trừ system extension.

Portable code:

```text
File.read(...)
```

System code:

```text
file.raw_handle()
```

và operation này có contract rõ.

---

# 32. Raw handle escape

Khi lấy:

```text
raw_handle()
```

programmer có thể làm FFI/system work.

Nhưng compiler không còn tự biết foreign code đang làm gì.

Vì vậy:

```text
raw handle
```

là unsafe hoặc capability-restricted boundary tùy API.

---

# 33. FFI resource wrapper

Ví dụ C:

```text
foo_create()
foo_destroy()
```

Axiom:

```text
Foo
    owns foreign resource
    Drop → foo_destroy()
```

Nếu:

```text
foo_borrow(...)
```

thì wrapper tạo:

```text
view<Foo>
```

không ownership transfer.

---

# 34. Resource + Send

Không phải resource nào cũng `Send`.

Ví dụ GUI object có thể bị:

```text
UI thread affinity
```

Do đó:

```text
Send(Foo)
```

được compiler derive từ type semantics.

Không được giả định mọi `OwnedHandle` đều Send.

---

# 35. Resource + Share

Tương tự:

```text
Share(File)
```

không mặc định có nghĩa nhiều thread có thể cùng thao tác.

Một file wrapper có thể cần:

```text
Arc<Mutex<File>>
```

hoặc OS-level shared semantics.

---

# 36. Thread-affine resources

Type có thể có system contract:

```text
ThreadAffine<T>
```

hoặc compiler-known property.

Ví dụ:

```text
Window
OpenGL context
UI object
```

không thể Move sang thread khác.

---

# 37. Async-affine resource

Một resource cũng có thể có execution-domain contract.

Ví dụ:

```text
Executor-local object
```

không thể được sử dụng từ arbitrary executor.

Không cần programmer viết lifetime/affinity annotations.

Compiler verifier đọc type facts.

---

# 38. Resource pool

Đối với server/game/engine:

```text
ResourcePool<T>
```

có thể quản lý:

```text
fixed slots
reuse
generation
stable identity
```

Không cần GC.

Pool ownership:

```text
Pool
 ├── slot 0
 ├── slot 1
 └── slot 2
```

Object handle:

```text
Handle<T>
```

không giữ physical pointer.

---

# 39. Resource leasing

Một abstraction hữu ích:

```text
Lease<T>
```

có:

```text
ownership of temporary access
```

Khi Drop:

```text
return resource to pool
```

Đây là cùng mô hình:

```text
Permit
Guard
Lease
```

đều có thể là ownership token + Drop.

---

# 40. Một pattern rất quan trọng của Axiom

Nhiều API có thể được thống nhất bằng:

```text
OWNED RESOURCE
      │
      ▼
  acquire()
      │
      ▼
TOKEN / GUARD / LEASE
      │
      ▼
 capability
      │
      ▼
    Drop
      │
      ▼
 release / unlock / return
```

Ví dụ:

```text
MutexGuard
SemaphorePermit
PoolLease
MappedRegion
File
Socket
```

Tất cả dùng cùng ownership/lifetime foundation.

---

# 41. Không cần RAII "magic"

Axiom có deterministic Drop nhưng không cần một cơ chế RAII riêng.

Ví dụ:

```axiom
{
    let lock = mutex.lock()?
    work(lock)
}
```

Scope kết thúc:

```text
Drop(lock)
```

Compiler xử lý.

Đây là một phần tự nhiên của ownership model.

---

# 42. Resource cleanup trên mọi control-flow

Nếu:

```axiom
let file = File.open(...)?

if condition {
    return error
}

use(file)
```

Compiler phải đảm bảo cleanup trên:

```text
return
break
continue
panic/unwind
```

theo profile.

---

# 43. Cleanup ordering

Nếu:

```axiom
let file = ...
let buffer = ...
let lock = ...
```

mặc định Drop:

```text
lock
buffer
file
```

theo reverse initialization order.

Nếu dependencies yêu cầu thứ tự khác, programmer phải tạo scope/nesting phù hợp.

---

# 44. Explicit `close`

Ví dụ:

```axiom
{
    let file = File.open(...)?
    ...
    file.flush()?
    file.close()?
}
```

Sau `close()`:

```text
resource state = Closed
ownership/value = still exists until Drop
```

Cần tránh double-close.

---

# 45. Closed state

Có hai hướng:

```text
File
    open/closed runtime state
```

hoặc typestate:

```text
File<Open>
File<Closed>
```

**Axiom v1 chọn runtime resource state**, không ép typestate generic vào mọi resource.

Lý do: typestate quá dễ làm API phức tạp.

Compiler vẫn đảm bảo ownership/lifetime; protocol-state errors thường trả `Result`/error.

---

# 46. Resource errors

Các lỗi như:

```text
permission denied
connection reset
timeout
broken pipe
disk full
```

là:

```text
Result<T, E>
```

Không dùng exception.

---

# 47. Timeout

Timeout nên là explicit policy:

```text
read(timeout)
```

hoặc:

```text
with_timeout(future, duration)
```

Không phải property ẩn của mọi I/O.

---

# 48. Blocking và async API

Không nên dùng một API kỳ quặc kiểu:

```text
read(mode = Async)
```

Thay vào đó:

```text
read(...)
read_async(...)
```

hoặc module-level async wrappers.

Mục tiêu: compiler và AI đều dễ hiểu.

---

# 49. `BufRead` / `Write`

Trait-based interfaces:

```axiom
trait Read {
    fn read(self: mut_view<Self>, buffer: mut_view<u8>) -> Result<usize, IoError>
}
```

```axiom
trait Write {
    fn write(self: mut_view<Self>, data: view<u8>) -> Result<usize, IoError>
}
```

Sau đó:

```text
File
Socket
MemoryStream
```

có thể `impl Read`, `impl Write`.

Không cần inheritance.

---

# 50. Zero-cost abstraction

Ví dụ:

```axiom
fn copy<R: Read, W: Write>(
    r: mut_view<R>,
    w: mut_view<W>
) -> Result<usize, IoError>
```

Generic static dispatch có thể được monomorphized thành:

```text
File → File
Socket → File
Memory → Socket
```

không cần virtual call nếu không dùng `dyn`.

---

# 51. Dynamic I/O

Nếu cần runtime polymorphism:

```axiom
dyn Read
dyn Write
```

explicit.

Khi đó vtable/metadata có thể tồn tại.

Không có hidden object header.

---

# 52. Buffer semantics

`Buffer<T>` nên đại diện:

```text
owned contiguous storage
```

Khác:

```text
view<T>
```

là non-owning access capability.

Ví dụ:

```text
Buffer<u8>
   │
   └── view<u8>
```

---

# 53. I/O Buffer relocation

Nếu:

```text
Buffer
```

có active `view`, compiler phải ngăn operation có thể relocate storage.

Ví dụ:

```axiom
let v = view(buffer)
buffer.reserve(4096)
```

nếu `reserve` có thể relocate và `v` còn live:

```text
REJECT
```

hoặc API phải guarantee no relocation.

---

# 54. Async buffer ownership

Pattern ưu tiên:

```text
Buffer
   ↓ Move
async operation
   ↓ await
(Buffer, result)
```

hơn:

```text
mutable view
   ↓
Future
   ↓
await
```

trừ khi explicit stable-storage contract tồn tại.

---

# 55. Zero-copy networking

Axiom phải cho phép:

```text
network packet
    ↓
owned buffer
    ↓
view header
    ↓
parse
```

mà không copy toàn packet.

Ví dụ:

```text
Buffer<u8>
 ├── view<Header>
 └── view<payload>
```

nhưng reinterpret từ bytes thành typed `Header` phải thỏa:

- alignment;
- initialization;
- representation;
- validity;
- endian/serialization rules.

Không được cast mù.

---

# 56. `view<T>` không phải serialization cast

Không cho:

```text
view<PacketHeader>
```

từ network bytes chỉ vì:

```text
sizeof(PacketHeader) == N
```

Phải có explicit parser or validated representation contract.

Điều này tránh rất nhiều UB kiểu C/C++.

---

# 57. Resource lifetime và async

Một resource đang được operation sử dụng:

```text
Socket
   ↓
Future
```

thì operation giữ semantic dependency.

Không thể:

```text
drop(socket)
```

nếu Future vẫn yêu cầu socket.

Trừ khi API contract chuyển ownership của socket vào operation.

---

# 58. Ownership-transfer async

Ví dụ:

```axiom
let (socket, result) =
    socket.read_async(buffer).await?
```

hoặc equivalent API.

Future state có thể sở hữu:

```text
socket
buffer
```

và trả lại khi complete.

Không cần reference counting.

---

# 59. Resource + cancellation

Khi cancellation xảy ra:

```text
Future
  ↓ cancel
I/O operation
  ↓ completion/cancel acknowledgement
resource released
```

Không được giải phóng resource trước khi underlying operation không còn truy cập resource.

Đây là **lifetime guarantee**, không phải scheduler convenience.

---

# 60. GPU resource

Mô hình tương tự:

```text
DeviceBuffer
GpuEvent
Kernel operation
```

Nếu kernel đang chạy:

```text
drop(DeviceBuffer)
```

không được giải phóng storage quá sớm.

`GpuEvent` hoặc execution dependency giữ lifetime.

Đây chính là cùng model với async I/O.

---

# 61. Unified in-flight operation model

Axiom có thể thống nhất semantic concept:

```text
IN-FLIGHT OPERATION
```

Một operation có:

```text
inputs
outputs
owned resources
capabilities
completion event
cancellation state
```

Verifier đảm bảo tất cả resource cần thiết sống đủ lâu.

Áp dụng cho:

```text
Async I/O
GPU
DMA
OS async APIs
```

Đây là một abstraction compiler-internal rất có giá trị.

---

# 62. Compiler không cần biết từng OS

Compiler chỉ cần hiểu semantic category:

```text
ExternalOperation
    ├── retained capability
    ├── retained storage
    ├── completion
    └── cancellation
```

Platform library cung cấp implementation contract.

---

# 63. System calls

Syscall không nằm trong portable Core.

Ví dụ:

```text
linux::syscall(...)
windows::Nt...
```

system layer.

Có thể dùng raw pointer và ABI trực tiếp.

Unsafe boundary explicit.

---

# 64. Freestanding

Freestanding Axiom có thể dùng:

```text
raw syscall
```

mà không cần:

```text
stdlib
GC
async runtime
thread runtime
C runtime
```

Đúng mục tiêu ban đầu của Axiom.

---

# 65. Hosted

Hosted application có thể import:

```text
std::fs
std::net
std::process
std::thread
std::async
```

Runtime components được link theo dependency graph.

---

# 66. Resource ownership qua FFI

Không bao giờ:

```text
Axiom Drop
   ↓
foreign resource
```

nếu compiler không biết destructor contract.

Wrapper phải định nghĩa rõ:

```text
destroy function
ABI
ownership
thread affinity
error policy
```

---

# 67. OS resource ABI

Internal:

```text
Axiom Resource
```

không có stable ABI mặc định.

FFI boundary dùng:

```text
@repr(C)
extern "C"
```

hoặc system ABI.

---

# 68. Resource abstraction không tạo object header

Ví dụ:

```text
File
```

có thể chỉ là:

```text
fd
flags
state
```

và compiler có thể optimize wrapper.

Không có:

```text
vptr
GC header
runtime type ID
```

trừ khi abstraction cụ thể yêu cầu.

---

# 69. Resource wrappers có thể zero-cost

Generic:

```text
fn read_all<R: Read>(r: mut_view<R>)
```

có thể inline hoàn toàn.

Trait abstraction biến mất.

Resource safety cũng biến mất sau verification.

Native code chỉ còn:

```text
syscall
memory operations
branches
```

và những gì thực sự observable.

---

# 70. Resource state machine

Compiler/library có thể biểu diễn:

```text
Resource
  │
  ├── Owned
  ├── InUse
  ├── Closing
  ├── Closed
  └── Failed
```

nhưng **không biến toàn bộ state machine thành Core type system**.

Runtime state chỉ tồn tại nếu resource thực sự cần.

---

# 71. Standard API philosophy

Axiom API nên ưu tiên:

```text
simple call
+
Result
+
ownership inference
+
Drop
```

thay vì:

```text
lifetime parameter
borrow annotation
ownership annotation
manual release
manual retain
manual pointer
```

Ví dụ mục tiêu:

```axiom
let file = File.open(path)?
let data = file.read_all()?
process(data)
```

chứ không phải một chuỗi lifetime boilerplate.

---

# 72. Nhưng low-level vẫn mở

Khi cần:

```text
File.raw_handle()
```

hoặc:

```text
socket.raw_handle()
```

system programmer có thể đi xuống:

```text
safe wrapper
   ↓
raw handle
   ↓
unsafe/system API
```

Không khóa người dùng khỏi OS.

---

# Frozen Invariants — `ARES-20..100`

### Resource semantics

- **ARES-20** Resource lifetime is distinct from value lifetime.
- **ARES-21** Resource lifetime is distinct from memory lifetime.
- **ARES-22** Owned resources are normally non-Copy.
- **ARES-23** Moving a resource transfers ownership without requiring physical copying.
- **ARES-24** Resource duplication is always explicit.
- **ARES-25** Borrowed resource access does not transfer ownership.
- **ARES-26** Resource capabilities cannot outlive their resource.
- **ARES-27** External resources have explicit ownership contracts.
- **ARES-28** Foreign ownership is not inferred.
- **ARES-29** Handle identity is distinct from ownership.

### Drop / cleanup

- **ARES-30** Resource cleanup is deterministic.
- **ARES-31** Drop performs non-fallible cleanup.
- **ARES-32** Fallible cleanup is explicit.
- **ARES-33** Drop cannot propagate recoverable errors.
- **ARES-34** Cleanup occurs on normal control-flow exits.
- **ARES-35** Cleanup occurs on supported failure/panic paths.
- **ARES-36** Moved resources are not dropped by the moved-from binding.
- **ARES-37** Double cleanup is prevented by ownership semantics.
- **ARES-38** Explicit close and Drop have distinct semantics.
- **ARES-39** Explicit close cannot invalidate a live dependent capability.
- **ARES-40** Resource destruction does not necessarily imply physical memory deallocation.

### Handles

- **ARES-41** Raw OS handles do not imply ownership.
- **ARES-42** Owned handles have explicit Drop semantics.
- **ARES-43** Borrowed handles do not perform destruction.
- **ARES-44** Handle duplication is explicit.
- **ARES-45** Handle identity is distinct from raw address identity.
- **ARES-46** Generation handles may prevent stale logical resource references.
- **ARES-47** Raw handle extraction is an explicit system boundary.
- **ARES-48** Foreign handles require an explicit ABI/ownership contract.

### I/O

- **ARES-49** File resources use deterministic ownership.
- **ARES-50** Socket resources use deterministic ownership.
- **ARES-51** Process resources use deterministic ownership.
- **ARES-52** Blocking I/O is distinct from async I/O.
- **ARES-53** Async I/O uses Future semantics.
- **ARES-54** Async I/O does not imply thread creation.
- **ARES-55** I/O buffers cannot be invalidated while an in-flight operation requires them.
- **ARES-56** In-flight operations retain required resource lifetime.
- **ARES-57** I/O completion has explicit synchronization semantics.
- **ARES-58** I/O cancellation is explicit.
- **ARES-59** Dropping a Future does not implicitly cancel foreign I/O.
- **ARES-60** Zero-copy I/O is permitted.
- **ARES-61** I/O APIs may use caller-owned buffers.
- **ARES-62** Owned-buffer async APIs may transfer buffer ownership.
- **ARES-63** Failed ownership-transfer operations return ownership where applicable.
- **ARES-64** Buffer relocation cannot invalidate a live capability.

### External resources

- **ARES-65** Memory-mapped storage has explicit storage lifetime.
- **ARES-66** Unmapping cannot invalidate a live safe capability.
- **ARES-67** Stable mapped addresses are explicit observable storage contracts.
- **ARES-68** DMA resources use explicit external-storage contracts.
- **ARES-69** GPU resources follow the same in-flight lifetime principle.
- **ARES-70** Device completion is distinct from CPU completion.
- **ARES-71** External operations may retain resources until completion.

### Concurrency / execution

- **ARES-72** Resource Send is type-derived.
- **ARES-73** Resource Share is type-derived.
- **ARES-74** Thread-affine resources cannot cross incompatible execution domains.
- **ARES-75** Executor-affine resources have explicit execution-domain contracts.
- **ARES-76** Resource ownership transfer across execution domains uses Move/Send.
- **ARES-77** Shared resources require appropriate synchronization.
- **ARES-78** Resource Drop cannot occur before an in-flight dependent operation completes or transfers responsibility.

### FFI / system

- **ARES-79** FFI resource ownership is explicit.
- **ARES-80** FFI resource cleanup uses explicit foreign destructor contracts.
- **ARES-81** Foreign allocation domains cannot be guessed.
- **ARES-82** Foreign exceptions do not implicitly cross the resource boundary.
- **ARES-83** System calls are system-layer operations.
- **ARES-84** Raw system handles are not portable Core values.
- **ARES-85** Resource wrappers need no object header.
- **ARES-86** Resource wrappers need no GC.
- **ARES-87** Resource wrappers need no implicit reference counting.
- **ARES-88** Resource wrappers may be zero-cost after optimization.

### API / compiler

- **ARES-89** Standard resource APIs prefer simple ownership + Result + Drop semantics.
- **ARES-90** Resource APIs do not require programmer-written lifetimes.
- **ARES-91** Resource APIs do not require programmer-written borrow annotations.
- **ARES-92** Capability verification protects resource-dependent access.
- **ARES-93** Compiler may optimize resource wrappers while preserving observable cleanup.
- **ARES-94** Compiler may eliminate abstraction layers when semantics permit.
- **ARES-95** Resource optimization cannot remove observable external effects.
- **ARES-96** Resource state not required by semantics is not materialized.
- **ARES-97** In-flight operations are explicit compiler semantic dependencies.
- **ARES-98** Resource semantics are preserved across async, GPU and FFI lowering.
- **ARES-99** Runtime components are required only when selected resource APIs need them.
- **ARES-100** Resource management does not require a monolithic runtime.

---

## Một điểm rất quan trọng đã được giải quyết

Giờ đây Axiom có thể dùng **một mô hình lifetime thống nhất** cho gần như toàn bộ hệ thống:

```text
                 OWNER
                   │
          ┌────────┼────────┐
          │        │        │
        view    mut_view   Move
          │        │        │
          ▼        ▼        ▼
       ACCESS    MUTATE   TRANSFER
          │        │        │
          └────────┼────────┘
                   │
             IN-FLIGHT OP
                   │
        ┌──────────┼──────────┐
        │          │          │
       I/O        GPU        DMA
        │          │          │
        └──────────┼──────────┘
                   ▼
               COMPLETE
                   │
                   ▼
                  Drop
```

Điều này có nghĩa **I/O, async và GPU không cần ba hệ thống lifetime riêng biệt**. Chúng dùng cùng nền ownership/capability mà ta đã xây.

### Bước kế tiếp

`BOOTSTRAP-072` nên xử lý một mảnh rất quan trọng còn thiếu của Axiom:

# **Numeric Model, SIMD, Vectorization & Floating-Point Semantics**

Phần này sẽ khóa:

- integer overflow;
- signed/unsigned;
- `as`/cast/bitcast;
- division;
- shift;
- NaN/Inf;
- IEEE-754;
- fast-math;
- deterministic floating-point;
- SIMD/vector types;
- portable SIMD;
- target SIMD;
- saturating/checked/wrapping arithmetic;
- compile-time numeric evaluation;
- `f16/bf16/f32/f64`;
- integer vector;
- tensor/matrix boundary;

để sau đó Axiom có thể đi thẳng vào **AI/GPU/high-performance numerical computing** mà không phải sửa lại semantic core.