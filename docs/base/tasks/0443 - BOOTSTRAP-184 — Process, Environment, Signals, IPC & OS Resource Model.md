# BOOTSTRAP-184 — Process, Environment, Signals, IPC & OS Resource Model
**FROZEN / COMPLETED**

Đây là phần rất quan trọng để hoàn thiện tầng **OS/system programming** của Axiom.

Quyết định trung tâm:

> **Process, Thread, File, Socket, Device, OS Handle... không phải cùng một semantic type. Chúng chỉ dùng chung một protocol quản lý resource ở tầng compiler.**

Tức là **không tạo một `Resource`/`Object` base class**. Axiom giữ type system tĩnh, nhưng compiler nhận biết những type nào sở hữu external resource.

---

# 184.1. OS Resource là semantic category

Compiler có thể nhận biết:

```text
Resource
├── File
├── Directory
├── Socket
├── Process
├── Thread
├── Mutex
├── Semaphore
├── Event
├── Device
├── MappedRegion
└── platform handle
```

Nhưng đây **không phải một type hierarchy**.

Thay vào đó, compiler theo dõi các property:

```text
OwnsExternalResource
DropReleasesResource
MoveTransfersResource
CopyPolicy
SendPolicy
SharePolicy
```

---

# 184.2. Resource ≠ Memory

Một `File` không phải memory allocation.

Một `Process` không phải object trong heap.

Một `Socket` không phải pointer.

Do đó:

```text
memory ownership
≠
OS resource ownership
```

nhưng cùng sử dụng:

```text
Move
Drop
Send
Share
```

---

# 184.3. Resource protocol

Một resource type có semantic:

```text
Acquire
→ Own
→ Use
→ Move / Close
→ Drop
→ Released
```

Ví dụ:

```ax
let file = File::open(path)?;
```

sau đó:

```ax
let other = file;
```

là **Move**, không phải copy OS handle.

---

# 184.4. OS handle

Raw OS handle:

```text
HANDLE
fd
Mach port
device descriptor
etc.
```

không phải safe owner.

Có thể được biểu diễn ở:

```text
std::os
std::ffi
unsafe
```

Safe wrapper mới xác định ownership.

---

# 184.5. OwnedHandle

Có thể có generic implementation-level abstraction:

```text
OwnedHandle<H>
```

nhưng đây là **library/system abstraction**, không phải Core base class.

Ví dụ:

```text
File
Socket
Process
```

có thể internally dùng các wrapper tương tự.

---

# 184.6. BorrowedHandle

Một API system có thể cần:

```text
BorrowedHandle<H>
```

nhưng programmer không phải quản lý lifetime bằng annotation.

Compiler theo dõi capability dependency:

```text
Owner
 ↓
Borrowed capability
```

---

# 184.7. Raw handle

Raw handle có thể là:

```text
Copy
```

nếu chỉ là machine value.

Nhưng:

> Copying raw handle không tạo ownership.

Đây là điểm bắt buộc.

---

# 184.8. Double-close

Safe wrapper phải ngăn:

```text
owner.close()
owner.drop()
```

cùng release một resource.

Trạng thái ownership:

```text
OWNED
CLOSED
MOVED
DROPPED
```

được verifier/compiler library contract theo dõi.

---

# 184.9. Explicit close

Nếu close có thể fail:

```ax
file.close()?;
```

là explicit.

`Drop` không trả về recoverable error.

---

# 184.10. Process

Process là external resource/control object.

```ax
let child = Process::spawn(config)?;
```

`ChildProcess`:

```text
!Copy
Move
Drop
```

---

# 184.11. Process ≠ Thread

Đây là hai semantic resource hoàn toàn khác:

```text
Process
Thread
```

Không tạo inheritance giữa chúng.

---

# 184.12. Child process lifecycle

Concept:

```text
Spawned
Running
Exited
Reaped
```

OS-specific implementation có thể khác.

---

# 184.13. Wait

```ax
let status = child.wait()?;
```

`wait()` quan sát completion và thực hiện resource lifecycle cần thiết.

---

# 184.14. Wait là synchronization

Process completion tạo synchronization edge:

```text
child execution
        ↓
process completion
        ↓
wait()
```

Tương tự thread join.

---

# 184.15. Async wait

```ax
let status = child.wait_async().await?;
```

không imply một thread mới cho mỗi process.

---

# 184.16. Drop ChildProcess

Điểm cần chốt:

> **Drop process handle không mặc định kill process.**

Nếu application muốn terminate:

```ax
child.kill()?;
```

explicit.

Điều này tránh side effect cực mạnh từ Drop.

---

# 184.17. Detached process

Nếu muốn child chạy độc lập:

```ax
child.detach()?;
```

sau đó parent không còn ownership lifecycle thông thường.

---

# 184.18. Kill

```ax
child.kill()?;
```

là explicit destructive operation.

Không phải Drop semantic.

---

# 184.19. Terminate vs kill

Portable API có thể:

```text
terminate()
kill()
```

với semantics khác nhau tùy platform.

---

# 184.20. Exit status

```text
ExitStatus
├── success
├── code
├── signal
├── core_dumped
└── platform fields
```

Không ép mọi OS vào một integer duy nhất.

---

# 184.21. Process exit code

Có thể:

```ax
if status.success() {
    ...
}
```

thay vì:

```ax
if status.code == 0
```

nhưng raw status vẫn truy cập được.

---

# 184.22. Current process

```text
Process::current()
```

có thể trả về lightweight non-owning process identity/capability.

Không tạo ownership của chính process.

---

# 184.23. Process identity

Phân biệt:

```text
ProcessId
ProcessHandle
```

`ProcessId` là value.

`ProcessHandle` có thể là resource.

---

# 184.24. PID reuse

`ProcessId` không đảm bảo identity vĩnh viễn.

OS có thể reuse PID.

Nếu cần stable process identity, phải dùng:

```text
ProcessHandle
```

hoặc generation/OS-specific identity.

---

# 184.25. Environment

Environment là external process state.

API:

```ax
environment.get("PATH")
environment.set("MODE", "release")
environment.remove("DEBUG")
```

---

# 184.26. Environment snapshot

Nên phân biệt:

```text
EnvironmentSnapshot
```

với:

```text
CurrentEnvironment
```

Snapshot là dữ liệu.

CurrentEnvironment là external state.

---

# 184.27. Process arguments

```text
args()
```

trả về owned/viewed values tùy implementation.

Ví dụ:

```ax
for arg in Process::args() {
    ...
}
```

---

# 184.28. argv lifetime

Nếu OS cung cấp argv memory chỉ tồn tại trong process:

compiler/runtime có thể wrap bằng process-lifetime capability.

Programmer không cần lifetime syntax.

---

# 184.29. Environment mutation

Environment mutation có effect:

```text
ExternalState
```

và không pure.

---

# 184.30. Environment concurrency

Environment thường là process-global external state.

Concurrent mutation/read phải có platform/runtime semantics phù hợp.

Compiler không tự giả định nó là ordinary thread-local variable.

---

# 184.31. Current directory

Current working directory cũng là process-global external state.

```ax
Process::current_dir()
Process::set_current_dir(path)
```

---

# 184.32. Current directory race

Hai thread cùng thay đổi current directory có thể gây race logic.

Do đó tốt hơn nên dùng explicit path roots/directory handles cho concurrent code.

---

# 184.33. Executable path

```ax
Process::executable_path()
```

là platform-dependent observation.

Không phải compile-time constant.

---

# 184.34. Environment variables trong comptime

Không nên tự động cho:

```text
comptime → OS environment
```

trừ khi capability:

```text
Environment
```

được cấp.

---

# 184.35. Build reproducibility

Nếu comptime đọc environment:

```text
BUILD_MODE
```

thì giá trị đó phải tham gia build identity.

---

# 184.36. Command execution

```ax
Command::new("tool")
    .arg("--version")
    .run()?;
```

là external effect:

```text
Process
ExternalState
IO
```

---

# 184.37. Command arguments

Không dùng shell string mặc định:

```ax
run("tool --arg value")
```

vì shell interpretation gây ambiguity/security issues.

Thay vào đó:

```ax
Command::new("tool")
    .args(["--arg", "value"])
```

---

# 184.38. Shell execution

Nếu cần shell:

```ax
Command::shell("...")
```

phải là explicit API.

---

# 184.39. Environment inheritance

Process spawn options:

```text
inherit_environment
clear_environment
set_environment
```

explicit.

---

# 184.40. Working directory

Child process config:

```ax
Command::new("tool")
    .current_dir(path)
```

không làm thay đổi parent current directory.

---

# 184.41. Standard streams

Child:

```text
stdin
stdout
stderr
```

có thể:

```text
Inherit
Pipe
File
Null
```

---

# 184.42. Pipe ownership

Nếu child stdout là Pipe:

```text
parent
   ↓
PipeReader
```

parent sở hữu reader.

Child sở hữu writer-side endpoint.

---

# 184.43. Pipe closure

EOF xảy ra khi tất cả writer endpoints đã đóng.

Đây là ownership + resource semantics, không phải magic.

---

# 184.44. Process pipeline

Có thể xây:

```text
Process A stdout
       ↓
Pipe
       ↓
Process B stdin
```

mà không cần shared memory.

---

# 184.45. Pipeline builder

Library có thể cung cấp:

```ax
pipeline(cmd_a)
    .pipe_to(cmd_b)
    .pipe_to(cmd_c)
    .run()?;
```

Compiler generic/inlining có thể loại abstraction overhead.

---

# 184.46. Process I/O deadlock

Runtime/library phải tránh API thiết kế dễ tạo:

```text
parent waits child
while child blocks on full stdout pipe
```

API high-level có thể concurrently drain streams.

---

# 184.47. Async process

Async API:

```text
child.stdout.read_async(...)
child.stderr.read_async(...)
child.wait_async()
```

có thể chạy đồng thời.

---

# 184.48. Process cancellation

Cancel Future không đồng nghĩa kill child.

Giống async cancellation model đã frozen.

Nếu muốn kill:

```ax
child.kill()?;
```

---

# 184.49. Process timeout

Library:

```ax
child.wait_timeout(duration)
```

timeout chỉ là observation result.

Không tự động kill trừ API explicit như:

```text
run_with_timeout_and_kill
```

---

# 184.50. Process resource inheritance

Child có thể inherit:

```text
stdin/stdout/stderr
files
sockets
environment
handles
```

Nhưng inheritance phải là explicit spawn policy.

---

# 184.51. Handle inheritance

Windows/Unix khác nhau.

Axiom portable API chỉ hứa những semantics thực sự portable.

---

# 184.52. Close-on-exec

System layer cần hỗ trợ:

```text
inherit
non-inherit
```

handle policy.

Không để accidental descriptor leakage.

---

# 184.53. IPC

Axiom IPC không phải một abstraction duy nhất.

Các primitive:

```text
Pipe
SharedMemory
Channel
UnixDomainSocket
NamedPipe
OSMessageQueue
```

---

# 184.54. Shared memory

Shared memory khác `Arc`.

```text
Arc<T>
```

là process memory ownership abstraction.

```text
SharedMemory
```

là OS storage resource có thể được map vào nhiều processes.

---

# 184.55. Shared memory mapping

Model:

```text
SharedMemory
      ↓
Mapping A
      ↓
view<T>

SharedMemory
      ↓
Mapping B
      ↓
view<T>
```

Hai process có capabilities tới cùng external storage.

---

# 184.56. Cross-process ownership

Compiler không thể áp dụng ordinary `Send` hoàn toàn giữa processes.

Cross-process sharing cần explicit serialization/shared-memory protocol.

---

# 184.57. Shared memory type safety

`SharedMemory` bytes không tự động trở thành:

```text
SharedMemory<T>
```

nếu layout/initialization/concurrency contract chưa được established.

---

# 184.58. Shared memory synchronization

Shared memory mutation cần:

```text
Atomic
Mutex
Semaphore
futex-like primitive
```

hoặc explicit protocol.

---

# 184.59. Process-shared Mutex

System library có thể cung cấp:

```text
ProcessMutex
```

khác:

```text
ThreadMutex
```

dù cùng conceptual synchronization behavior.

---

# 184.60. Memory model boundary

Compiler memory model đảm bảo thread-level semantics trong một execution domain.

Cross-process memory cần explicit OS synchronization primitive để establish ordering.

---

# 184.61. Signals

Signals là asynchronous external events.

Không coi signal handler như ordinary function call.

---

# 184.62. Signal safety

Signal handler có tập operation rất hạn chế trên nhiều OS.

Axiom không nên cho arbitrary safe code chạy trực tiếp trong signal context.

---

# 184.63. Signal delivery abstraction

Thay vì:

```text
@signal_handler
fn ...
```

ở Core, standard/system library có thể:

```text
SignalStream
```

chuyển signal thành event có thể poll/await.

---

# 184.64. Signal handler bridge

OS-level handler tối thiểu:

```text
signal
 ↓
atomic/event notification
 ↓
normal execution context
```

---

# 184.65. Signal stream

```ax
let signals = SignalStream::subscribe([SIGINT, SIGTERM]);

while let Some(signal) = signals.next().await {
    ...
}
```

đây là abstraction an toàn hơn.

---

# 184.66. Signal ordering

OS signal ordering không nên bị nâng thành guarantee mạnh hơn platform.

---

# 184.67. Ctrl+C

Console interruption có thể được chuyển thành:

```text
Signal::Interrupt
```

nhưng platform backend quyết định mechanism.

---

# 184.68. Process termination

External process termination có thể tạo:

```text
ProcessExit
Signal
ResourceFailure
```

nhưng không biến thành panic mặc định.

---

# 184.69. Thread identity

Thread:

```text
ThreadId
ThreadHandle
```

giống Process:

```text
ID != owning resource
```

---

# 184.70. ThreadHandle

Nếu joinable:

```text
let t = spawn(...);
let result = t.join()?;
```

`ThreadHandle` là resource/observation capability.

---

# 184.71. Thread Drop

Drop `ThreadHandle` không tự động terminate thread.

Detached behavior phải explicit.

---

# 184.72. Thread join

Join tạo:

```text
thread completion
→ synchronizes-with
→ join
```

đã phù hợp concurrency model.

---

# 184.73. Thread detach

```ax
thread.detach();
```

chuyển lifecycle responsibility sang runtime/OS.

---

# 184.74. Process vs Thread Send

Một `ThreadHandle` có thể không `Send` tùy OS/resource semantics.

Compiler không giả định mọi OS handle đều cross-thread safe.

---

# 184.75. OS handle Send/Share

`Send` và `Share` được derive từ contract của resource type.

Không phải vì underlying representation là integer.

---

# 184.76. Handle table

Compiler không cần biết kernel handle table.

System layer chịu trách nhiệm mapping:

```text
Axiom resource
↔
OS resource
```

---

# 184.77. Resource finalization

Không có global GC finalizer.

Mọi resource owner có deterministic Drop.

---

# 184.78. Resource leaks

Nếu programmer cố tình `forget(resource)`:

đó là explicit operation/system escape.

Không tự động finalize sau đó.

---

# 184.79. Leak vs use-after-free

Leak:

```text
resource remains alive
```

Use-after-free:

```text
resource invalid but accessed
```

Axiom ưu tiên ngăn cái thứ hai; leak có thể là logic/resource-management bug.

---

# 184.80. Resource limits

OS có thể giới hạn:

```text
files
processes
memory
threads
sockets
```

Đây là runtime/system failure, không phải type error.

---

# 184.81. Resource exhaustion

API có thể trả:

```text
ResourceExhausted
```

qua `Result`.

Không panic mặc định.

---

# 184.82. Process memory

Không coi process memory là ordinary `Vec<u8>`.

Có các system APIs:

```text
VirtualMemory
SharedMemory
MappedRegion
```

---

# 184.83. Virtual memory

System layer có thể expose:

```text
reserve
commit
decommit
protect
release
```

đặc biệt cho allocator/JIT/runtime/compiler.

Đây là system/unsafe-capable APIs.

---

# 184.84. Memory protection

Protection:

```text
READ
WRITE
EXECUTE
```

phải là explicit.

Không mặc định RWX.

---

# 184.85. W^X

Security-oriented runtime có thể enforce:

```text
Writable XOR Executable
```

nếu platform/profile yêu cầu.

---

# 184.86. Device handles

GPU/device resources dùng cùng resource protocol:

```text
DeviceBuffer
GpuEvent
DeviceContext
```

nhưng semantic types riêng.

---

# 184.87. No universal Resource trait

Đây là quyết định quan trọng:

**Không thêm:**

```ax
trait Resource { ... }
```

vào Core chỉ để unify các OS resources.

Compiler biết resource metadata nội bộ.

Library vẫn có thể định nghĩa local traits khi cần:

```text
Closable
Readable
Writable
```

---

# 184.88. Closable

Nếu cần common API:

```ax
trait Close {
    fn close(mut_view<Self>) -> Result<unit, Error>;
}
```

Nhưng `Drop` vẫn là compiler-known semantic mechanism.

---

# 184.89. Drop không đồng nghĩa close

Một resource có thể:

```text
Drop → release
```

nhưng explicit `close()` có semantics khác:

```text
flush
finalize
commit
```

---

# 184.90. Resource transaction

Một số resource có commit/rollback:

```text
Transaction
```

là semantic library abstraction, không phải universal OS resource.

---

# 184.91. Environment + Effect System

Compiler-derived EffectInfo:

```text
Process spawn
    → Process
    → ExternalState
    → IO
```

Environment read:

```text
ExternalState
```

Filesystem:

```text
IO
ExternalState
```

---

# 184.92. Optimizer restrictions

Optimizer không được:

```text
remove external observation
duplicate external command
reorder observable process operations
```

nếu effect semantics không cho phép.

---

# 184.93. Pure subprocess abstraction

Không có pure process execution.

Ngay cả deterministic executable cũng có external effects:

```text
process creation
OS scheduling
resource allocation
```

---

# 184.94. Comptime process execution

`comptime ExecuteTool` là external capability.

Compiler phải track:

```text
tool identity
arguments
environment
inputs
outputs
```

vào build dependency.

---

# 184.95. Build reproducibility

Nếu tool output được dùng để generate code:

```text
tool version
tool identity
input hashes
environment
```

phải tham gia build identity khi reproducible semantics yêu cầu.

---

# 184.96. Process tree

Build system có thể quản lý:

```text
Parent
 ├── compiler
 ├── linker
 └── code generator
```

với structured cancellation.

---

# 184.97. Structured process management

Library nên hỗ trợ:

```text
ProcessGroup
ProcessTree
```

để cancellation/cleanup có thể có scope rõ ràng.

---

# 184.98. ProcessGroup

Kill group là explicit operation.

Không phải Drop mặc định nếu gây side effects ngoài resource owner.

---

# 184.99. IPC channel

Axiom channel:

```text
Sender<T>
Receiver<T>
```

đã thuộc concurrency model.

OS pipe/socket có thể implement stream/channel adapters nhưng không biến thành cùng type.

---

# 184.100. Serialization boundary

Cross-process channel thường cần:

```text
Serialize<T>
Deserialize<T>
```

trừ shared-memory protocol.

---

# 184.101. Zero-copy IPC

Có thể:

```text
SharedMemory
+
Handle/Offset
+
Synchronization
```

thay vì serialize.

Compiler không tự biến serialization thành shared memory vì observable protocol khác nhau.

---

# 184.102. IPC security

Process boundary là trust boundary.

Không giả định:

```text
Send<T>
```

trong thread ⇒ safe cross-process serialization.

---

# 184.103. FFI process handles

Foreign process handles phải có explicit ownership contract:

```text
borrowed
owned
duplicated
transfer
```

---

# 184.104. OS handle duplication

Duplicating handle là explicit:

```ax
let duplicate = handle.duplicate()?;
```

không phải `Copy`.

---

# 184.105. Handle inheritance

Spawn config phải xác định chính xác handles được inherit.

Không inherit toàn bộ process handle table mặc định.

---

# 184.106. Close-on-exec

Safe defaults nên tránh accidental leakage.

---

# 184.107. Platform extensions

Portable API chỉ bao phủ common semantics.

Platform-specific:

```text
std::os::windows
std::os::linux
std::os::macos
std::os::android
```

có thể expose native capabilities.

---

# 184.108. Native handle escape

```ax
let raw = file.raw_handle();
```

nên là explicit system/unsafe operation nếu caller có thể phá ownership invariant.

---

# 184.109. Borrowed raw handle

Nếu API chỉ cần truyền handle sang OS:

```ax
with_raw_handle(file, fn(h) { ... })
```

có thể giữ owner sống trong scope mà không chuyển ownership.

---

# 184.110. Ownership-aware FFI

Compiler biết:

```text
borrowed handle
owned handle
consumed handle
returned handle
```

qua FFI contract.

---

# 184.111. ABI

OS resource ABI không phải Axiom ABI.

Ví dụ:

```text
Axiom File
↓
platform handle
↓
OS ABI
```

representation hidden ở safe layer.

---

# 184.112. Shared libraries

Dynamic libraries có thể trả:

```text
opaque handle
```

Axiom wrapper xác định ownership/drop semantics.

---

# 184.113. Dynamic loading

```text
Library::load(path)
```

resource:

```text
LibraryHandle
```

Drop có thể unload.

Nhưng unloading khi function pointers/data vẫn live phải bị ngăn bởi capability/lifetime model.

---

# 184.114. Library symbol capability

```text
library
 ↓
symbol
```

symbol capability không được sống lâu hơn library nếu nó phụ thuộc executable mapping.

---

# 184.115. Dynamic library unload

Compiler/runtime phải ngăn:

```text
Library dropped
↓
function pointer called
```

nếu safe API đã establish dependency.

---

# 184.116. Open-world semantics

Dynamic loading phá closed-world assumption.

LTO phải conservative.

---

# 184.117. Signals + dynamic libraries

Signal handlers installed by foreign libraries là external effect.

Compiler không được giả định closed-world signal behavior nếu FFI/dynamic loading involved.

---

# 184.118. Process resource graph

Compiler/runtime conceptual model:

```text
Process
├── File
├── Socket
├── Pipe
├── Thread
├── Library
├── SharedMemory
└── Device
```

Ownership graph có thể được inspect bởi runtime/debugger.

---

# 184.119. Resource graph không phải object graph

Đây không tạo:

```text
Object → Object → inheritance
```

mà chỉ là runtime ownership/dependency graph.

---

# 184.120. Resource dependency

Ví dụ:

```text
Library
 ↓
Function pointer
```

hoặc:

```text
MappedRegion
 ↓
view
```

hoặc:

```text
Process
 ↓
Pipe
```

được compiler/library contracts mô tả.

---

# 184.121. Generic Resource Analysis

Compiler có thể có internal metadata:

```text
ResourceInfo {
    acquire
    release
    move
    copy
    send
    share
    dependencies
}
```

Không expose thành universal type.

---

# 184.122. Resource Drop analysis

Drop elaboration xử lý OS resources giống các resource-bearing structs khác:

```text
struct Foo {
    file: File,
    socket: Socket
}
```

Drop order:

```text
socket
file
```

theo reverse initialization semantics.

---

# 184.123. Partial move

Nếu struct có custom Drop:

```text
Foo { file, socket }
```

partial move restrictions áp dụng như mọi Drop-bearing type.

---

# 184.124. Struct composition

Đây chính là lợi ích của **struct + function**:

```ax
struct Server {
    listener: Socket,
    config: Config,
}

fn run(mut_view<Self>) -> Result<unit, Error> {
    ...
}
```

Không cần class/resource hierarchy.

---

# 184.125. Process builder

Builder cũng chỉ là struct:

```ax
struct Command {
    program: Path,
    args: Vec<String>,
    env: ...
}
```

methods chỉ là functions có receiver.

---

# 184.126. No hidden runtime

Một program chỉ dùng:

```text
File
```

không tự động link:

```text
Thread runtime
Async executor
GPU runtime
Reflection
```

---

# 184.127. Runtime composition

Process/IPC runtime components chỉ được link khi thực sự cần.

---

# 184.128. Freestanding

Freestanding Axiom program có thể bỏ toàn bộ:

```text
Process API
Filesystem
Network
Environment
```

nếu không dùng.

---

# 184.129. Kernel/device

Kernel code có thể sử dụng:

```text
VirtualMemory
Device
Atomic
Interrupt
```

nhưng không cần hosted Process runtime.

---

# 184.130. Embedded

Embedded target có thể không có:

```text
Process
Filesystem
Environment
```

Compiler phải loại bỏ API/runtime components không khả dụng.

---

# 184.131. Capability-aware compilation

Target profile có thể khai báo:

```text
Filesystem = unavailable
Process = unavailable
Thread = available
```

Code dùng API unavailable → compile-time target diagnostic.

---

# 184.132. Conditional compilation

```ax
@cfg(target_os = "windows")
fn native_handle(...) { ... }
```

đã phù hợp syntax/config model.

---

# 184.133. Platform API isolation

Platform APIs phải nằm dưới namespace:

```text
std::os::windows
std::os::linux
std::os::macos
```

không pollute portable namespace.

---

# 184.134. Environment variable API

Portable:

```ax
env.get("NAME")
```

Platform-specific extensions không phá portable interface.

---

# 184.135. Exit

Process exit:

```ax
Process::exit(code)
```

là diverging operation:

```text
never
```

và không chạy ordinary local cleanup nếu process termination semantics bypass them.

Vì vậy cần phân biệt rõ:

```text
return
panic
exit
abort
```

---

# 184.136. `return` vs `exit`

```text
return
→ normal function cleanup

main return
→ normal program shutdown

Process::exit
→ immediate process-level termination policy
```

---

# 184.137. `abort`

`abort()` là machine/process termination, không phải panic unwind.

---

# 184.138. Panic

Panic vẫn đi qua:

```text
panic policy
cleanup
unwind/abort
```

theo frozen error model.

---

# 184.139. OS fault

Segmentation fault/access violation không được giả định là Axiom `panic`.

Đó là OS/hardware fault.

---

# 184.140. Signal conversion

Runtime có thể chuyển một số OS signals thành diagnostic/panic trong hosted profile, nhưng đó là runtime policy chứ không phải Core semantic equivalence.

---

# 184.141. Resource error taxonomy

`SystemError` có thể chứa:

```text
NotFound
PermissionDenied
AlreadyExists
WouldBlock
Interrupted
ResourceExhausted
InvalidInput
BrokenPipe
ConnectionClosed
TimedOut
Unsupported
Platform(code)
```

---

# 184.142. Raw OS error

Luôn giữ native code khi có thể:

```text
PlatformError {
    kind
    native_code
}
```

để systems programmers không mất thông tin.

---

# 184.143. Error portability

Portable code dùng:

```text
ErrorKind
```

platform code có thể inspect:

```text
native_code
```

---

# 184.144. OS resource model — quyết định cuối

Axiom chốt:

```text
                    Resource Protocol
                         │
       ┌─────────────────┼──────────────────┐
       │                 │                  │
    Ownership         Capability          Effects
       │                 │                  │
 Move / Drop       READ / WRITE        IO / External
       │                 │                  │
       └─────────────────┼──────────────────┘
                         │
                  Semantic Type
                         │
        ┌────────────────┼────────────────┐
        │                │                │
       File           Process          Socket
        │                │                │
     OS handle        PID/handle       endpoint
```

**Không có universal `Resource` base type trong ngôn ngữ.**

---

# 184.145. Các invariant đóng băng

### Resource

- **ARES-20** — External resources are semantic values with deterministic ownership.
- **ARES-21** — Resource types are not required to form a common inheritance hierarchy.
- **ARES-22** — Resource ownership is distinct from memory ownership.
- **ARES-23** — Raw OS handles do not imply ownership.
- **ARES-24** — Resource duplication is explicit.
- **ARES-25** — Resource Drop releases owned resources deterministically.
- **ARES-26** — Recoverable close failures require explicit close operations.
- **ARES-27** — Double release of a safe-owned resource is invalid.

### Process

- **APROC-20** — Process identity and process handle are distinct.
- **APROC-21** — Child process ownership is explicit.
- **APROC-22** — Dropping a child handle does not implicitly terminate the child.
- **APROC-23** — Termination is explicit.
- **APROC-24** — Wait establishes process-completion synchronization.
- **APROC-25** — Process cancellation does not implicitly imply process termination.
- **APROC-26** — Process exit status preserves platform-specific termination information.

### Environment

- **APROC-30** — Environment is external process state.
- **APROC-31** — Environment reads are not pure.
- **APROC-32** — Environment mutation is explicit external state mutation.
- **APROC-33** — Compile-time environment access requires explicit capability.
- **APROC-34** — External compile-time inputs participate in build identity.

### IPC

- **AIPC-20** — IPC is distinct from in-process ownership.
- **AIPC-21** — OS IPC resources have explicit ownership.
- **AIPC-22** — Shared memory does not automatically create typed shared objects.
- **AIPC-23** — Cross-process shared memory requires explicit synchronization contracts.
- **AIPC-24** — Thread `Send` does not imply cross-process serialization safety.
- **AIPC-25** — Zero-copy IPC requires explicit shared-storage and synchronization semantics.
- **AIPC-26** — Pipe endpoint ownership determines EOF/resource lifetime.

### Signals

- **ASIGNAL-20** — Signals are asynchronous external events.
- **ASIGNAL-21** — Ordinary application functions are not implicitly signal handlers.
- **ASIGNAL-22** — Safe signal processing should transition into normal execution context.
- **ASIGNAL-23** — Signal ordering guarantees cannot exceed platform guarantees.

### OS handles / FFI

- **AOS-20** — OS handle identity is distinct from integer representation.
- **AOS-21** — Raw handle copying does not duplicate ownership.
- **AOS-22** — Handle duplication is explicit.
- **AOS-23** — FFI resource ownership requires an explicit contract.
- **AOS-24** — Handle inheritance across process boundaries is explicit.
- **AOS-25** — Safe handle wrappers preserve ownership and capability invariants.

### Compiler/runtime

- **AOS-30** — OS resource effects participate in compiler EffectInfo.
- **AOS-31** — Optimizers cannot eliminate or reorder observable external effects.
- **AOS-32** — Resource types may be zero-cost wrappers after semantic verification.
- **AOS-33** — Resource metadata does not require a universal runtime base object.
- **AOS-34** — Unused OS/runtime components are not linked.
- **AOS-35** — Platform-specific resource semantics remain isolated from portable Core semantics.
- **AOS-36** — `Process`, `Thread`, `File`, `Socket`, `Device`, and similar resources remain distinct semantic types.
- **AOS-37** — Common resource management is provided by compiler protocols, not inheritance.

---

# Một kết luận kiến trúc rất quan trọng

Sau 184, mô hình Axiom đã rõ hơn rất nhiều:

### Programmer thấy

```ax
let file = File::open(path)?;
let socket = TcpStream::connect(addr)?;
let child = Command::new("tool").spawn()?;
```

Mỗi type hoàn toàn khác nhau.

### Compiler thấy

```text
File
 ├─ owns external resource
 ├─ move-only
 ├─ deterministic drop
 └─ IO effect

Socket
 ├─ owns external resource
 ├─ move-only
 ├─ deterministic drop
 └─ network effect

Child
 ├─ owns external resource
 ├─ move-only
 ├─ deterministic drop
 └─ process effect
```

Tức là **compiler chia sẻ machinery, nhưng language không cần một abstraction chung ép programmer phải hiểu**.

Đây chính xác là hướng phù hợp với mục tiêu Axiom:

> **Compiler hiểu nhiều hơn programmer phải viết.**

---

# Tiếp theo: BOOTSTRAP-185

Phần kế tiếp nên đi vào **Reflection, Metadata, Runtime Type Information & Dynamic Loading**.

Nó sẽ chốt một vấn đề còn khá lớn:

```text
Axiom có compile-time reflection
        ↓
nhưng không có runtime reflection mặc định
        ↓
vậy làm thế nào để:
    plugin
    dynamic library
    serialization
    debugger
    IDE
    AI tooling
    GUI
    scripting
    hot reload
```

cùng tồn tại mà **không biến mọi executable Axiom thành một chương trình có object metadata/runtime type registry khổng lồ**.

Trọng tâm BOOTSTRAP-185 sẽ là thiết kế **`.axmeta` + optional runtime metadata + ABI descriptors + plugin interfaces + type-erasure có kiểm soát**, và đặc biệt là cách giữ binary nhỏ khi chương trình hoàn toàn không dùng reflection.