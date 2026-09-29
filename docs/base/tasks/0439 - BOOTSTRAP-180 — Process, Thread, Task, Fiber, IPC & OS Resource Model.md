# BOOTSTRAP-180 — Process, Thread, Task, Fiber, IPC & OS Resource Model
**FROZEN / COMPLETED**

Mục tiêu của task này là chốt tầng **execution + OS resource** sao cho Axiom có thể viết:

- application
- server
- game engine
- worker system
- high-performance networking
- database
- embedded software
- system daemon
- process supervisor
- kernel/system code

mà vẫn giữ nguyên mô hình:

> **Ownership = ai sở hữu giá trị/resource.**  
> **Capability = ai được truy cập.**  
> **Synchronization = khi nào truy cập được phép xảy ra.**  
> **Execution domain = computation đang chạy ở đâu.**

---

# 180.1. Bốn khái niệm phải tách biệt

Axiom không được nhập:

```text
Process
Thread
Task
Fiber
```

thành một abstraction.

```text
Process
  └── isolation/resource container

Thread
  └── OS execution context

Fiber
  └── stackful user-space execution context

Task/Future
  └── stackless schedulable computation
```

---

# 180.2. Process

`Process` là:

> **OS-level resource and isolation boundary.**

Nó có thể sở hữu:

```text
address space
handles
file resources
sockets
threads
environment
security identity
IPC endpoints
```

Process không phải một function call.

---

# 180.3. Thread

`Thread` là:

> **Execution context capable of executing instructions independently.**

Thread có:

```text
stack
register state
instruction pointer
thread-local storage
scheduler state
```

và thuộc một process trong hosted OS.

---

# 180.4. Thread không phải ownership

Một thread không “sở hữu” tất cả dữ liệu nó đang xử lý.

Ví dụ:

```text
Thread A
   │
   └── receives Buffer<T>
```

có thể nhận ownership của buffer:

```text
Move
```

nhưng đó là **ownership của value**, không phải ownership của thread.

---

# 180.5. Task

`Task` là:

> **Một đơn vị công việc có thể được scheduler thực thi.**

Task thường chứa:

```text
Future/state machine
scheduler metadata
cancellation state
result
```

Task không nhất thiết có thread riêng.

---

# 180.6. Fiber

Fiber là:

> **Stackful user-space execution context.**

Ví dụ:

```text
OS Thread
 ├── Fiber A ── stack A
 ├── Fiber B ── stack B
 └── Fiber C ── stack C
```

Switch giữa fiber có thể không cần syscall.

---

# 180.7. Future

Future là:

> **Stackless suspended computation.**

```text
async fn foo()
```

→ compiler tạo state machine.

Future không mặc định có:

```text
thread
fiber
stack
```

---

# 180.8. Quan hệ

Kiến trúc:

```text
Process
   │
   ├── Thread
   │     ├── Task
   │     ├── Task
   │     └── Fiber
   │
   └── Thread
         ├── Task
         └── Fiber
```

Một scheduler có thể map:

```text
Task → Thread
Task → Fiber
```

tùy runtime.

---

# 180.9. Execution Domain

Axiom đã có execution domains.

Mở rộng:

```text
CPUThread
CPUFiber
CPUTask
GPUKernel
Interrupt
ExternalDevice
```

Đây là semantic domain, không nhất thiết là một runtime object.

---

# 180.10. Thread creation

API cấp cao:

```ax
let thread = Thread.spawn(worker)?;
```

nhưng semantic requirement chỉ là:

```text
new execution context
```

Platform backend quyết định:

```text
pthread
CreateThread
clone
embedded scheduler
```

---

# 180.11. Closure capture

Ví dụ:

```ax
let data = Buffer.new();

Thread.spawn(move || {
    process(data);
});
```

Compiler hiểu:

```text
data
  ↓
MOVE
  ↓
thread closure
```

Không cần programmer viết lifetime.

---

# 180.12. Send requirement

Đã frozen:

> Cross-execution ownership transfer yêu cầu `Send`.

Do đó:

```text
Thread.spawn(move || use(x))
```

yêu cầu:

```text
x : Send
```

nếu `x` được chuyển sang thread.

---

# 180.13. Send không phải Share

Đây là invariant rất quan trọng:

```text
Send
≠
Share
```

`Send`:

```text
value có thể chuyển sang execution domain khác
```

`Share`:

```text
value có thể được truy cập đồng thời từ nhiều execution domains
```

---

# 180.14. Ví dụ

```text
Buffer<T>
```

có thể:

```text
Send
```

nhưng không nhất thiết:

```text
Share
```

Điều này cho phép:

```text
Thread A
   │
   │ Move Buffer
   ↓
Thread B
```

mà không cần lock.

---

# 180.15. Shared immutable data

```text
Arc<T>
```

có thể cho:

```text
Share<T>
```

nếu `T` thỏa contract.

Nhiều thread có thể:

```text
view<T>
```

cùng lúc.

---

# 180.16. Shared mutable data

Không được:

```text
Arc<T>
   ↓
mut_view<T>
```

một cách tự động.

Phải có synchronization:

```text
Arc<Mutex<T>>
Arc<RwLock<T>>
Arc<Atomic<T>>
```

hoặc abstraction tương đương.

---

# 180.17. Thread-local storage

TLS:

```text
Thread
 ├── TLS A
 ├── TLS B
 └── TLS C
```

là storage domain riêng:

```text
TLS
```

đã được frozen trong memory/runtime model.

---

# 180.18. TLS không phải global

Một biến TLS:

```text
thread_local var counter: u64;
```

không phải một global shared variable.

Mỗi thread có một instance.

---

# 180.19. Thread identity

Thread có logical identity:

```text
ThreadId
```

không nên dùng machine address làm identity.

---

# 180.20. Task identity

Task cũng có:

```text
TaskId
```

nếu runtime cần.

TaskId là logical identity, không phải pointer.

---

# 180.21. Fiber identity

Tương tự:

```text
FiberId
```

là logical identity.

---

# 180.22. Process identity

```text
ProcessId
```

thường là OS-assigned identity.

Axiom không được giả định PID luôn globally unique vĩnh viễn.

---

# 180.23. Handle

OS resources nên dùng:

```text
Handle<T>
```

semantic wrapper.

Ví dụ:

```text
Handle<File>
Handle<Process>
Handle<Thread>
Handle<Device>
```

nhưng physical representation có thể là:

```text
fd
HANDLE
integer
pointer
capability token
```

tùy platform.

---

# 180.24. Handle không phải pointer

```text
Handle<T>
```

là logical resource identity.

Không cho phép:

```text
Handle<T> → *mut T
```

một cách implicit.

---

# 180.25. OwnedHandle và BorrowedHandle

Phải phân biệt:

```text
OwnedHandle<T>
BorrowedHandle<T>
```

`OwnedHandle`:

```text
Drop → release resource
```

`BorrowedHandle`:

```text
Drop → không release resource
```

---

# 180.26. Foreign handle

FFI handle mặc định:

```text
foreign
```

không được Axiom tự đoán ownership.

API wrapper phải xác định:

```text
borrowed
owned
shared
duplicated
```

---

# 180.27. Handle duplication

OS có thể cho phép:

```text
duplicate_handle()
```

Kết quả không nhất thiết là clone semantic object.

Có thể là:

```text
two handles
→ same underlying resource
```

Do đó:

```text
Handle<T>
```

và:

```text
SharedResource<T>
```

phải phân biệt.

---

# 180.28. Resource identity

Axiom tiếp tục giữ ba tầng identity:

```text
Value Identity
Storage Identity
Logical Identity
```

OS handle chủ yếu biểu diễn:

```text
Logical Resource Identity
```

---

# 180.29. Process spawn

API:

```ax
let child = Process.spawn(program, args)?;
```

có thể trả:

```text
ChildProcess
```

với:

```text
pid
stdin
stdout
stderr
exit state
```

tùy API.

---

# 180.30. Process arguments

Không ép mọi argument thành UTF-8 String.

Nên dùng OS-aware abstraction:

```text
Args
OsString
OsStr
```

đã được thiết kế ở BOOTSTRAP-169.

---

# 180.31. Environment

Environment là external state.

Ví dụ:

```ax
let value = environment.get("PATH")?;
```

được ghi nhận trong:

```text
EffectSummary
```

vì nó quan sát external state.

---

# 180.32. Process environment không phải global language state

Compiler không được assume:

```text
ENV["X"]
```

cố định giữa các process.

Comptime environment cũng phải theo capability model đã frozen.

---

# 180.33. Process exit

Process có:

```text
exit(code)
```

là terminating control flow.

Semantic type:

```text
never
```

nếu gọi trong current process.

---

# 180.34. Exit cleanup

Axiom phải phân biệt:

```text
normal return
panic
process exit
abnormal termination
```

`return`:

```text
normal Drop cleanup
```

`panic`:

```text
abort/unwind profile
```

`exit`:

```text
process-level termination
```

Không giả định mọi OS termination đều chạy Drop.

---

# 180.35. `_exit`-style termination

System layer có thể có:

```text
terminate_immediately()
```

không chạy application cleanup.

Đây là unsafe/system operation.

---

# 180.36. Parent/child relationship

Process có thể:

```text
Parent
  │
  ├── Child A
  ├── Child B
  └── Child C
```

Nhưng parent không mặc định sở hữu child process theo Axiom value semantics.

`ChildProcess` là resource handle.

---

# 180.37. Child process waiting

```ax
let status = child.wait()?;
```

có thể block.

Async:

```ax
let status = child.wait_async().await?;
```

---

# 180.38. Child process ownership

Drop `ChildProcess` không nhất thiết:

```text
kill child
```

Đây là policy cần explicit.

Ví dụ:

```text
detach()
kill()
terminate()
wait()
```

là các semantics khác nhau.

---

# 180.39. Structured concurrency

Axiom khuyến khích:

```text
scope
 ├── task A
 ├── task B
 └── task C
```

Scope kết thúc chỉ khi children:

```text
complete
cancel
or explicitly detached
```

---

# 180.40. Detached task

Detach phải explicit:

```text
task.detach()
```

Không implicit.

Điều này tránh tình trạng:

```text
function returns
↓
background task silently lives forever
```

---

# 180.41. Task result ownership

```text
spawn(fn() -> T)
```

có thể trả:

```text
JoinHandle<T>
```

JoinHandle là capability để quan sát completion/result.

---

# 180.42. JoinHandle

```text
let handle = spawn(worker);
let result = handle.join()?;
```

`join` có thể:

```text
consume handle
```

hoặc API có thể cho phép observe một lần/nhiều lần tùy semantics.

---

# 180.43. Join ≠ synchronization primitive duy nhất

Thread completion → join có:

```text
happens-before
```

như memory model đã frozen.

Nhưng:

```text
spawn
```

không tự đồng bộ arbitrary shared memory.

---

# 180.44. Thread start synchronization

Khi thread được tạo và nhận ownership:

```text
parent
  ↓ Move
child thread
```

các semantics publication cần được đảm bảo bởi spawn contract.

---

# 180.45. Thread termination

Thread completion:

```text
all writes
   ↓
join
   ↓
observer
```

có happens-before.

---

# 180.46. Thread cancellation

Không có:

```text
kill_thread_now()
```

safe primitive.

Forced thread termination có thể phá:

```text
Drop
locks
invariants
FFI state
device operations
```

---

# 180.47. Cooperative cancellation

Axiom ưu tiên:

```text
CancellationToken
```

task/thread kiểm tra:

```text
is_cancelled()
```

và tự kết thúc.

---

# 180.48. Process kill khác thread cancel

Process-level:

```text
kill(process)
```

là OS operation.

Nó có thể terminate toàn bộ process mà không đảm bảo application-level Drop.

---

# 180.49. Scheduler

Scheduler là runtime policy.

Core không định nghĩa:

```text
work stealing
round robin
priority queue
```

như semantic requirement.

---

# 180.50. Task scheduling

Scheduler có thể chọn:

```text
Thread A
  Task 1
  Task 4

Thread B
  Task 2
  Task 3
```

và migrate task nếu:

```text
Send
```

được thỏa mãn.

---

# 180.51. Task migration

Một Future có thể:

```text
Thread A
   ↓
Thread B
```

nếu state của Future:

```text
Send
```

và executor contract cho phép migration.

---

# 180.52. Non-Send Future

Nếu Future chứa:

```text
non-Send state
```

thì executor phải giữ nó trên execution domain phù hợp.

Không cần programmer viết annotation.

---

# 180.53. Local task

```text
spawn_local(...)
```

cho phép task không `Send`.

Nó phải chạy trong một local executor/domain.

---

# 180.54. Fiber migration

Fiber có stack.

Mặc định nên coi:

```text
Fiber
```

là:

```text
pinned to execution domain
```

trừ khi runtime cung cấp explicit migratable stack mechanism.

---

# 180.55. Why fiber pinned?

Vì stack có:

```text
address-sensitive locals
FFI frames
unsafe pointers
system state
```

Migration cần contract mạnh hơn Future migration.

---

# 180.56. Fiber suspension

Fiber có thể suspend:

```text
yield()
```

và resume:

```text
resume()
```

Không phải:

```text
await
```

dù runtime có thể implement abstraction tương tự.

---

# 180.57. Fiber stack ownership

Fiber sở hữu stack resource.

Khi fiber kết thúc:

```text
fiber
 ↓
stack cleanup
```

theo runtime contract.

---

# 180.58. Async Future không sở hữu thread

Future:

```text
Future<T>
```

không chứa implicit:

```text
Thread
```

Điều này giữ async abstraction nhẹ.

---

# 180.59. Scheduler + Future

```text
Executor
   │
   ├── Future A
   ├── Future B
   └── Future C
```

Executor poll:

```text
poll()
```

Future:

```text
Ready
Pending
```

đã frozen.

---

# 180.60. Waker

Waker chỉ là:

```text
notification capability
```

không phải:

```text
thread
```

và không tự tạo memory publication semantics.

---

# 180.61. Priority

Thread/task có thể có:

```text
Priority
```

ở runtime/system layer.

Priority không thay đổi:

```text
ownership
capability
memory model
```

---

# 180.62. CPU affinity

System API có thể:

```text
thread.set_affinity(cpu_set)
```

hoặc:

```text
task.bind(execution_domain)
```

nhưng đây là performance/system property.

---

# 180.63. Affinity không phải type property

Không tạo:

```text
Cpu0<T>
Cpu1<T>
```

cho ordinary code.

Execution placement là runtime/system metadata.

---

# 180.64. NUMA affinity

Có thể phối hợp:

```text
Thread affinity
+
Memory resource affinity
```

để đạt locality.

Ví dụ:

```text
Thread → NUMA node 2
Arena  → NUMA node 2
```

---

# 180.65. Priority inversion

Mutex implementation/runtime có thể hỗ trợ:

```text
priority inheritance
priority ceiling
```

nhưng không biến thành Core semantics.

---

# 180.66. IPC

Axiom cần các nhóm IPC:

```text
Channel
Pipe
SharedMemory
Event
Semaphore
Socket
Signal
MessageQueue
```

Không gom tất cả thành `Channel`.

---

# 180.67. Channel

Channel:

```text
Sender<T>
Receiver<T>
```

chuyển ownership:

```text
Sender
   ↓ Move
T
   ↓
Receiver
```

Đây là concurrency primitive rất phù hợp với ownership model.

---

# 180.68. Channel không copy

Ví dụ:

```ax
sender.send(buffer)?;
```

nếu `Buffer<T>` không Copy:

```text
buffer
→ Move
→ channel
→ receiver
```

Không cần clone.

---

# 180.69. Shared memory

Shared memory là:

```text
storage sharing
```

không phải message passing.

Do đó:

```text
SharedMemory<T>
```

phải có synchronization contract.

---

# 180.70. Shared memory + view

Process A:

```text
mut_view<u8>
```

Process B:

```text
view<u8>
```

không thể tự động an toàn chỉ vì OS map cùng pages.

Axiom cần explicit synchronization boundary.

---

# 180.71. Inter-process capability

Capabilities không tự xuyên process.

Một capability trong process A:

```text
CapabilityId(A)
```

không thể dùng trực tiếp trong process B.

---

# 180.72. IPC handle transfer

Nếu OS cho phép transfer handle:

```text
Process A
   │
   │ transfer
   ↓
Process B
```

Axiom biểu diễn đó là:

```text
ownership/resource transfer
```

qua IPC protocol.

---

# 180.73. Shared resource

Nếu hai process cùng reference resource:

```text
SharedResource
```

phải có explicit OS semantics.

Không dùng `Arc<T>` để giả vờ cross-process.

---

# 180.74. `Arc` process-local

`Arc<T>` chỉ giải quyết:

```text
shared ownership
```

trong cùng address space.

Cross-process phải dùng:

```text
SharedMemory
IPC handle
OS shared resource
```

---

# 180.75. Pipe

Pipe có stream semantics:

```text
writer → bytes → reader
```

Không nhất thiết preserve message boundaries.

---

# 180.76. Message queue

Message queue:

```text
message A
message B
message C
```

preserve message boundaries.

Không nên model đơn giản bằng Pipe.

---

# 180.77. Event

Event:

```text
signal
wait
```

không mang arbitrary data.

Nó là synchronization/notification primitive.

---

# 180.78. Semaphore

Semaphore:

```text
Permit
```

là ownership-bearing capability.

Đã frozen:

```text
Permit !Copy
Drop → release
```

---

# 180.79. Mutex

Mutex:

```text
lock()
→ Guard
```

Guard sở hữu quyền:

```text
exclusive access
```

Drop:

```text
unlock
```

---

# 180.80. RwLock

Read:

```text
multiple read guards
```

Write:

```text
one write guard
```

theo capability model.

---

# 180.81. OS synchronization

System layer có thể wrap:

```text
futex
eventfd
WaitOnAddress
SRWLock
semaphore
condition variable
```

nhưng application thấy Axiom synchronization abstraction.

---

# 180.82. Waitable resource

Một resource có thể implement:

```text
Waitable
```

để executor/runtime tích hợp.

Ví dụ:

```text
Socket
File
Process
Event
Timer
```

nhưng không phải mọi resource đều phải waitable.

---

# 180.83. Timer

Timer có thể là:

```text
Timer
```

và async:

```text
sleep(duration).await
```

Không tạo thread ngủ cho mỗi timer.

---

# 180.84. Timer scheduler

Runtime có thể dùng:

```text
timer wheel
heap
kernel timer
io_uring timeout
IOCP timer
```

mà API không đổi.

---

# 180.85. Signals

Unix signal là external asynchronous event.

Không nên biến signal handler thành ordinary async function.

Signal-safe API phải rất hạn chế.

---

# 180.86. Signal handler

System layer có thể cung cấp:

```text
SignalHandler
```

nhưng compiler/runtime phải biết execution context đặc biệt.

Không được tự động cho phép:

```text
allocate
lock arbitrary mutex
perform arbitrary I/O
```

trong signal handler.

---

# 180.87. Interrupt

Embedded/kernel:

```text
InterruptHandler
```

là execution domain đặc biệt.

Compiler cần biết:

```text
cannot block
restricted storage
restricted instructions
```

tùy target.

---

# 180.88. Interrupt-safe code

Có thể có compiler contract:

```text
@interrupt
fn handler(...)
```

với verifier kiểm tra legality.

Tương tự:

```text
@kernel
```

cho GPU.

---

# 180.89. Process security boundary

Process là isolation boundary.

Compiler không được giả định:

```text
Process A
```

có thể truy cập:

```text
Process B memory
```

trừ system/unsafe mechanism.

---

# 180.90. Capability security

OS handles có thể biểu diễn capability:

```text
FileHandle
SocketHandle
DeviceHandle
ProcessHandle
```

Không nên yêu cầu global authority để dùng resource.

---

# 180.91. Least authority

Library API nên nhận resource handle cụ thể:

```ax
fn write(log: WritableFile, data: view<u8>)
```

thay vì:

```text
global filesystem authority
```

Điều này rất phù hợp với Axiom capability model.

---

# 180.92. Resource inheritance

Process spawn có thể inherit:

```text
stdin
stdout
stderr
```

nhưng các resource khác phải explicit.

Không implicit inherit toàn bộ process state.

---

# 180.93. Environment inheritance

Environment inheritance là OS/process policy.

Axiom API phải cho phép:

```text
inherit
clear
replace
```

explicit.

---

# 180.94. Working directory

Working directory là process external state.

API:

```text
current_directory()
set_current_directory()
```

có effect:

```text
ExternalState
```

---

# 180.95. Process isolation và compiler optimization

Compiler không được optimize:

```text
get_env()
```

thành constant chỉ vì profile từng thấy một value.

External state là semantic effect.

---

# 180.96. Dynamic libraries

Process có thể load:

```text
SharedLibrary
```

và lấy:

```text
Symbol
```

Dynamic loading tạo:

```text
Open World
```

optimization boundary.

---

# 180.97. Dynamic symbol

Không thể giả định:

```text
unknown symbol
```

không tồn tại chỉ vì compiler không thấy declaration.

Do đó LTO phải conservative khi dynamic loading/reflection có mặt.

---

# 180.98. Plugin architecture

Có thể xây:

```text
Application
   ↓
PluginLoader
   ↓
SharedLibrary
   ↓
@export symbol
```

ABI contract phải explicit.

---

# 180.99. Process lifecycle

Một process có lifecycle:

```text
CREATED
   ↓
RUNNING
   ↓
EXITING
   ↓
EXITED
```

Child handle có thể observe state.

---

# 180.100. Thread lifecycle

```text
CREATED
   ↓
RUNNABLE
   ↓
RUNNING
   ↓
BLOCKED/WAITING
   ↓
RUNNABLE
   ↓
TERMINATED
```

Runtime state machine không cần expose toàn bộ cho application.

---

# 180.101. Task lifecycle

```text
CREATED
   ↓
READY
   ↓
RUNNING
   ↓
WAITING
   ↓
READY
   ↓
COMPLETED
```

có thêm:

```text
CANCELLED
FAILED
```

theo API.

---

# 180.102. Fiber lifecycle

```text
CREATED
   ↓
READY
   ↓
RUNNING
   ↓
SUSPENDED
   ↓
READY
   ↓
COMPLETED
```

Fiber stack phải còn valid khi suspended.

---

# 180.103. Resource graph

Toàn bộ OS resources có thể được compiler/runtime model:

```text
Process
 ├── Thread
 │    ├── Task
 │    └── Fiber
 │
 ├── FileHandle
 ├── Socket
 ├── SharedMemory
 ├── DeviceHandle
 └── ChildProcess
```

Các edge biểu diễn:

```text
owns
borrows
waits-for
shares
depends-on
```

---

# 180.104. Resource lifetime

Nếu:

```text
Task
   └── uses File
```

task không được hoàn tất với một capability invalid.

Nếu:

```text
Future
   └── uses Socket
```

socket không được close trong khi operation còn active.

Đây chính là capability verifier đã có.

---

# 180.105. Resource Drop

Mỗi resource phải định nghĩa:

```text
Drop semantics
```

nhưng Drop không được tự động:

```text
kill process
cancel arbitrary task
terminate thread
```

trừ khi abstraction contract nói rõ.

---

# 180.106. Runtime ownership

Runtime có thể own:

```text
executor
worker threads
timer wheel
I/O reactor
```

nhưng đây là runtime component.

Một chương trình freestanding có thể không link chúng.

---

# 180.107. No mandatory scheduler

Core không link:

```text
scheduler
thread pool
async runtime
```

nếu program không dùng.

---

# 180.108. Minimal program

Một chương trình:

```ax
fn main() {
    return;
}
```

không cần:

```text
thread runtime
async executor
network runtime
GPU runtime
```

---

# 180.109. Server program

Một server dùng:

```text
threads
async
network
timers
filesystem
```

chỉ link các runtime components cần thiết.

---

# 180.110. Kernel program

Kernel profile có thể không dùng:

```text
process
filesystem
socket
standard allocator
```

nhưng dùng:

```text
interrupt
page table
thread scheduler
physical memory
```

---

# 180.111. Embedded

Embedded profile có thể dùng:

```text
interrupt
DMA
device
static allocator
```

mà không có:

```text
OS process
dynamic loader
filesystem
```

---

# 180.112. Unified resource model

Ta có thể khóa:

```text
Resource
 ├── Memory
 ├── File
 ├── Socket
 ├── Device
 ├── Process
 ├── Thread
 ├── Task
 ├── Timer
 └── IPC endpoint
```

Tất cả đều có:

```text
identity
ownership
lifetime
capability
effects
```

nhưng **không phải tất cả đều là cùng một type**.

---

# 180.113. Execution ≠ Resource

Thread là execution resource.

File là I/O resource.

Memory là storage resource.

Mutex là synchronization resource.

Không nhập chúng thành một `Resource<T>` duy nhất ở Core.

---

# 180.114. Scheduler không được thay đổi semantics

Runtime có thể chuyển:

```text
Task A
Thread 1 → Thread 2
```

nếu semantic contract cho phép.

Observable behavior phải vẫn đúng.

---

# 180.115. Scheduler fairness

Axiom Core không guarantee:

```text
fairness
latency
priority scheduling
```

trừ khi một library/system abstraction explicitly contract điều đó.

---

# 180.116. Lock fairness

Tương tự Mutex/RwLock không mặc định guarantee fairness.

Nếu cần:

```text
FairMutex
PriorityMutex
```

có thể là library types.

---

# 180.117. Deadlock

Compiler không hứa loại bỏ mọi deadlock.

Nhưng tooling có thể phân tích:

```text
lock graph
wait graph
resource graph
```

và cảnh báo.

---

# 180.118. Deadlock diagnostics

AI/compiler tooling có thể cung cấp:

```text
axc inspect locks
axc inspect waits
axc inspect concurrency
```

để giải thích:

```text
Thread A holds M1 waits M2
Thread B holds M2 waits M1
```

---

# 180.119. Blocking detection

Effect system có thể đánh dấu:

```text
Blocking
```

cho operations.

IDE có thể cảnh báo:

```text
blocking operation inside async task
```

nhưng không biến warning thành semantic restriction trừ khi profile yêu cầu.

---

# 180.120. Structured concurrency + ownership

Một lợi ích lớn:

```text
scope
 ├── owns task A
 ├── owns task B
 └── owns cancellation
```

Khi scope kết thúc:

```text
children must be resolved/cancelled/detached explicitly
```

Điều này giúp tránh task leaks.

---

# 180.121. Task groups

Library có thể có:

```text
TaskGroup
```

với:

```text
spawn
cancel
join_all
```

Errors có thể aggregate thành:

```text
Result
```

không cần exception machinery.

---

# 180.122. Failure propagation

Nếu child task thất bại:

```text
TaskGroup
   ↓
Result<...>
```

có thể cancel sibling tasks theo policy.

Đây là library semantics, không phải Core exception system.

---

# 180.123. Process supervision

Higher-level runtime có thể xây:

```text
Supervisor
 ├── Worker A
 ├── Worker B
 └── Worker C
```

với:

```text
restart
backoff
shutdown
health
```

Không cần đưa vào Core.

---

# 180.124. Actor model

Actor có thể xây hoàn toàn bằng:

```text
Task
+
Channel
+
owned state
```

Không cần Core `class/actor`.

Đây là một validation quan trọng cho thiết kế struct/trait/channel hiện tại.

---

# 180.125. Shared-nothing concurrency

Mô hình:

```text
Thread A owns state A
Thread B owns state B
```

giao tiếp:

```text
Channel<T>
```

rất phù hợp Axiom.

Không cần:

```text
shared mutable pointer
```

cho nhiều trường hợp.

---

# 180.126. Work stealing

Runtime có thể dùng:

```text
Worker 1 deque
Worker 2 deque
Worker 3 deque
```

và migrate `Send` tasks.

Task không `Send` phải pinned/local.

---

# 180.127. Thread pool

Thread pool là library/runtime:

```text
ThreadPool
```

không phải Core.

Có thể hỗ trợ:

```text
spawn
spawn_local
submit
shutdown
```

---

# 180.128. CPU-bound vs I/O-bound

Runtime có thể có:

```text
ComputePool
IoPool
```

để tránh blocking I/O làm nghẽn executor.

Compiler effect metadata hỗ trợ runtime lựa chọn.

---

# 180.129. Runtime metadata

Function metadata có thể chứa:

```text
Effects
Blocking
Suspend
Send
GPU
ExecutionDomain
```

nhưng semantic type vẫn không cần phình to.

---

# 180.130. Compiler-visible execution contracts

Các boundary đặc biệt có thể dùng:

```text
@kernel
@interrupt
@blocking
@nonblocking
@foreign
```

nhưng ordinary functions không cần annotate mọi property.

Compiler derive phần lớn thông tin.

---

# 180.131. Process IPC and ownership

IPC gửi:

```text
T
```

nếu transport hỗ trợ value serialization:

```text
encode
send
decode
```

hoặc gửi ownership của shared OS resource:

```text
handle transfer
```

Hai trường hợp phải phân biệt.

---

# 180.132. Serialization ≠ ownership transfer

```text
send(x)
```

qua network không có nghĩa receiver nhận cùng storage.

Có thể là:

```text
serialize → bytes → deserialize
```

Trong khi channel nội bộ có thể:

```text
Move x
```

zero-copy.

---

# 180.133. Local channel optimization

Nếu compiler chứng minh:

```text
producer
→ channel
→ consumer
```

cùng execution context và no observable synchronization requirement:

có thể eliminate channel allocation/queue.

Semantic message order vẫn giữ nguyên.

---

# 180.134. IPC optimization

Tương tự:

```text
same-process pipe
```

có thể optimize thành:

```text
ring buffer
```

nếu API contract cho phép.

---

# 180.135. Process boundary cannot be optimized away

Compiler không được biến:

```text
Process A → Process B
```

thành:

```text
function call
```

nếu process isolation là observable.

---

# 180.136. Dynamic process resources

Process/Thread/Handle identities observable nên:

```text
logical identity
```

phải được bảo toàn.

Không scalarize thành ordinary value nếu identity quan sát được.

---

# 180.137. Resource finalization

Compiler có thể eliminate:

```text
resource allocation
```

chỉ khi:

```text
resource identity
external effects
Drop effects
```

không observable.

Ví dụ:

```text
temporary mutex abstraction
```

có thể được optimized.

Nhưng:

```text
file open
```

không thể loại bỏ nếu external filesystem effect observable.

---

# 180.138. External effects

Process/thread/OS operations thường có:

```text
ExternalState
```

effect.

Do đó compiler không được:

```text
duplicate
remove
reorder
```

arbitrary system calls.

---

# 180.139. Signal-safe and async-safe boundaries

System APIs có thể khai báo restricted execution domains.

Verifier có thể reject:

```text
signal handler → blocking I/O
```

nếu contract cấm.

---

# 180.140. OS abstraction principle

Axiom standard library:

```text
std::thread
std::process
std::sync
std::ipc
std::os
```

không phải wrappers đơn giản quanh Unix.

Chúng là semantic abstractions, backend target-specific.

---

# 180.141. Target backend examples

```text
Windows
  Thread → Win32 thread
  Process → CreateProcess
  Handle → HANDLE

Linux
  Thread → pthread/clone
  Process → fork/exec/clone
  Handle → fd/pidfd/etc.

macOS
  native pthread/process APIs

Embedded
  custom scheduler / RTOS / bare metal
```

Axiom API giữ semantic layer chung.

---

# 180.142. Real-time profile

Có thể có:

```text
@realtime
```

hoặc build profile kiểm tra:

```text
no allocation
no blocking
bounded execution
bounded memory
```

Nhưng đây là profile/system contract, không phải Core semantics mặc định.

---

# 180.143. Real-time allocation

Compiler có thể dùng:

```text
Arena
Pool
Static
Stack
```

và verifier/tooling kiểm tra allocation effect.

---

# 180.144. Kernel profile

Kernel code có thể cần:

```text
@kernel
```

không phải GPU `@kernel` cùng semantic.

Nên tránh collision; system-level attribute namespace có thể phân loại domain:

```text
@kernel(gpu)
@kernel(cpu)
```

hoặc tên attribute riêng.

---

# 180.145. Resource ABI

OS resource wrapper có ABI:

```text
Handle<T>
```

nhưng physical representation target-dependent.

FFI cần:

```text
@repr(C)
```

hoặc system ABI contract.

---

# 180.146. Stable system handles

Axiom không được assume:

```text
sizeof(Handle<T>) == sizeof(usize)
```

trừ khi ABI contract yêu cầu.

---

# 180.147. AI/compiler inspectability

Compiler nên cung cấp:

```text
axc inspect execution foo
axc inspect send foo
axc inspect share foo
axc inspect tasks foo
axc inspect resources foo
axc inspect blocking foo
axc inspect ipc foo
```

AI có thể hỏi:

```text
Why can this task not migrate?
```

và nhận:

```text
Future contains LocalResource at ...
```

thay vì lỗi mơ hồ.

---

# 180.148. Core rule

Khóa nguyên tắc:

> **Axiom does not make concurrency safe by making everything shared. It makes concurrency safe by making ownership, capability and synchronization explicit to the compiler.**

---

# 180.149. Tổng hợp execution model

```text
                    PROCESS
                       │
             ┌─────────┴─────────┐
             │                   │
          THREAD              THREAD
             │                   │
       ┌─────┴─────┐       ┌─────┴─────┐
       │           │       │           │
     TASK        FIBER    TASK       FIBER
       │           │
    FUTURE       STACK
       │
    POLL/AWAIT
```

Trong đó:

```text
Process = isolation
Thread  = OS execution
Fiber   = stackful execution
Task    = schedulable work
Future  = computation state
```

---

# 180.150. Tổng hợp ownership model

```text
Move
 └── cross-thread/process/resource transfer

Send
 └── transfer safety

Share
 └── concurrent sharing safety

view
 └── read capability

mut_view
 └── exclusive write capability

Sync
 └── ordering

Handle
 └── resource identity
```

Đây là một mô hình khá thống nhất, thay vì có một hệ thống riêng cho thread, một hệ thống riêng cho async, một hệ thống riêng cho IPC.

---

# 180.151. Invariants

### Execution

- **AEXEC-20** — Process, Thread, Fiber, Task and Future are distinct semantic concepts.
- **AEXEC-21** — Execution domain is distinct from ownership.
- **AEXEC-22** — Future does not imply a dedicated thread.
- **AEXEC-23** — Task migration requires applicable `Send` semantics.
- **AEXEC-24** — Non-Send tasks cannot silently migrate across incompatible execution domains.
- **AEXEC-25** — Fiber stacks have explicit storage/lifetime contracts.
- **AEXEC-26** — Forced thread termination is not a safe ordinary primitive.
- **AEXEC-27** — Structured concurrency is supported as a library/runtime abstraction.

### Process

- **APROC-20** — Process is an isolation/resource boundary.
- **APROC-21** — Process identity is distinct from memory/storage identity.
- **APROC-22** — Process termination is distinct from ordinary function return.
- **APROC-23** — Process exit does not imply ordinary Drop cleanup unless explicitly guaranteed.
- **APROC-24** — Child-process lifetime policy is explicit.
- **APROC-25** — Environment, working directory and process state are external effects.
- **APROC-26** — Dynamic loading creates an open-world optimization boundary.

### Resources

- **ARES-EXEC-20** — OS resources have explicit ownership semantics.
- **ARES-EXEC-21** — Owned and borrowed handles are distinct.
- **ARES-EXEC-22** — Foreign handles do not imply ownership without an explicit contract.
- **ARES-EXEC-23** — Resource identity is distinct from storage address.
- **ARES-EXEC-24** — Resource Drop semantics are resource-specific.
- **ARES-EXEC-25** — Resource capabilities cannot outlive their backing resource.

### IPC

- **AIPC-20** — Channel transfer may move ownership without copying.
- **AIPC-21** — Serialization is distinct from ownership transfer.
- **AIPC-22** — Shared memory does not imply synchronization.
- **AIPC-23** — Cross-process capabilities are not automatically valid in another process.
- **AIPC-24** — OS handle transfer requires explicit ownership semantics.
- **AIPC-25** — Pipe and message queue semantics remain distinct.

### Scheduling

- **ASCHED-20** — Scheduler policy does not redefine program semantics.
- **ASCHED-21** — Scheduling migration cannot violate Send/storage contracts.
- **ASCHED-22** — Priority and affinity are system/runtime properties.
- **ASCHED-23** — Fairness is not a universal Core guarantee.
- **ASCHED-24** — Blocking operations remain distinguishable from asynchronous suspension.
- **ASCHED-25** — Runtime scheduling may optimize execution only without violating observable semantics.

---

# BOOTSTRAP-180 hoàn tất

Đến đây phần **execution/concurrency/resource model** của Axiom đã khá đầy đủ:

```text
                     AXIOM EXECUTION
                           │
             ┌─────────────┼─────────────┐
             │             │             │
          Process        Thread        Device
             │             │             │
          isolation      stack         GPU/DMA
                           │
                  ┌────────┴────────┐
                  │                 │
                Fiber             Task
                  │                 │
                stack             Future
                                    │
                                  await
                                    │
                              synchronization
                                    │
                         ┌──────────┼──────────┐
                         │          │          │
                       Mutex      Channel     Atomic
                         │          │          │
                         └──────────┼──────────┘
                                    │
                                Ownership
                                    │
                              Capability Model
```

Điểm quan trọng là **không cần thêm một “concurrency type system” riêng**. Phần lớn đã được giải quyết bằng các trục hiện có:

```text
Ownership
Capability
Send
Share
Synchronization
Execution Domain
Effect
```

Đây là dấu hiệu kiến trúc hiện tại đang hội tụ khá tốt.

---

# BOOTSTRAP-181 — Time, Clock, Timer, Scheduling Time & Temporal Semantics

Task tiếp theo nên chốt **thời gian**, vì hiện tại Axiom đã có:

```text
async
I/O
thread
task
timer
process
GPU event
```

nhưng chưa khóa semantics cho:

```text
Instant
Duration
Wall Clock
Monotonic Clock
System Time
Timer
Timeout
Deadline
Sleep
Clock precision
Clock adjustment
Time zones
Leap seconds
Virtual/Test time
```

Đặc biệt cần tránh một lỗi rất nguy hiểm trong systems language:

```text
"thời gian hiện tại"
```

bị dùng lẫn với:

```text
"thời gian trôi qua"
```

và dẫn tới timeout, scheduler, retry, networking hoặc distributed-system bugs.

**BOOTSTRAP-181** sẽ chốt mô hình temporal của Axiom trước khi đi sâu tiếp vào **network protocol, distributed systems và synchronization nâng cao**.