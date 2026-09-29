Tiếp tục với **THREAD-001 — OS Thread Model**. Tôi sẽ giữ đúng triết lý vừa chốt: `Thread` là một abstraction mỏng, OS chịu phần kernel/thread machinery, còn Axiom chỉ giữ state mà chương trình thực sự cần.

# THREAD-001 — Axiom OS Thread Model

## 1. Phân biệt 4 tầng

Axiom nên có:

```text
Thread
Fiber
Task
Future
```

và tuyệt đối không đồng nhất chúng:

```text
OS Thread
  = execution resource do OS quản lý

Fiber
  = user-space execution context + stack

Task
  = schedulable asynchronous computation

Future
  = state machine của computation
```

Quan hệ:

```text
Thread
 ├── chạy Task A
 ├── chạy Task B
 ├── chạy Task C
 └── chạy Task D
```

hoặc:

```text
Thread
 └── chạy Fiber
       ├── Task
       └── Task
```

---

# 2. `Thread` không phải object lớn

Surface API:

```axiom
let t = Thread.spawn(worker)
t.join()
```

Semantic representation nên gần:

```text
ThreadHandle
├── ThreadId
└── platform handle
```

Không nhét vào:

```text
scheduler
allocator
mutex
future
stack
TLS
exception state
...
```

Các thứ đó thuộc tầng khác.

---

# 3. Stack là phần tốn memory thực sự

Đây là điểm cần sửa cách nhìn về "32 bytes".

Một thread thực tế:

```text
┌─────────────────────────────┐
│ OS thread metadata          │
├─────────────────────────────┤
│ registers / context         │
├─────────────────────────────┤
│ TLS                         │
├─────────────────────────────┤
│ stack                       │  ← thường lớn nhất
│                             │
│                             │
└─────────────────────────────┘
```

`ThreadHandle` của Axiom có thể chỉ vài machine words, nhưng **OS thread vẫn có stack và kernel resources**.

Vì vậy:

> Axiom không nên cố định kích thước thread object; thay vào đó phải kiểm soát **stack policy**.

---

# 4. Stack size phải configurable

Ví dụ:

```axiom
Thread.spawn(worker)
```

dùng default platform policy.

Hoặc:

```axiom
Thread.spawn(worker, stack_size: 64_KiB)
```

hoặc:

```axiom
ThreadConfig {
    stack_size: 64_KiB
    name: "worker"
}
```

Không nên đưa quá nhiều option vào Core.

Các property như:

```text
priority
affinity
stack_size
name
detached
guard_page
```

thuộc `ThreadConfig` của std/platform layer.

---

# 5. Stack không nhất thiết phải commit toàn bộ

Đây là optimization quan trọng.

Axiom runtime nên phân biệt:

```text
reserved stack
committed stack
```

Ví dụ:

```text
Reserve: 1 MiB
Commit: 64 KiB
```

OS có thể commit thêm khi cần tùy nền tảng.

Nhưng đây là platform implementation, không phải semantic guarantee.

---

# 6. Stack lifetime

Thread stack phải sống ít nhất bằng execution của thread.

```text
Thread created
      ↓
stack allocated/reserved
      ↓
thread starts
      ↓
worker()
      ↓
thread exits
      ↓
join/detach semantics
      ↓
stack reclaimed
```

Một thread không được phép giữ view tới stack của thread đã kết thúc.

Compiler phải coi thread boundary là một ownership boundary.

---

# 7. `spawn` của Thread

Tôi đề xuất:

```axiom
let t = Thread.spawn(fn() {
    work()
})
```

Nếu closure capture:

```axiom
let buffer = Buffer(...)

let t = Thread.spawn(fn() {
    process(buffer)
})
```

thì ownership của `buffer` phải được chuyển sang thread:

```text
Caller
  │
  │ move
  ▼
Thread state
```

Không copy ngầm một resource lớn.

Nếu `buffer` không `Send`:

```text
compile error
```

---

# 8. `Send` ở đây rất quan trọng

Chúng ta đã định nghĩa:

```text
Send = ownership có thể chuyển sang execution domain khác
Share = có thể chia sẻ an toàn giữa execution domains
```

Vậy:

```axiom
Thread.spawn(worker(x))
```

yêu cầu:

```text
x: Send
```

Nhưng:

```axiom
Thread.spawn_local(worker(x))
```

không cần `Send`.

Tương tự async:

```text
spawn(...)
```

có thể yêu cầu Send vì task có thể migrate.

---

# 9. Thread closure không cần heap

Ví dụ:

```axiom
let x = 42

Thread.spawn(fn() {
    println(x)
})
```

Compiler có thể tạo:

```text
ThreadStartData
┌───────┐
│ x=42  │
└───────┘
```

rồi chuyển trực tiếp vào startup context.

Không có semantic requirement:

```text
malloc closure
```

Compiler có thể:

- inline
- caller allocation
- stack-to-thread transfer
- task pool
- heap

tùy escape analysis.

---

# 10. `ThreadHandle`

Tôi đề xuất:

```text
ThreadHandle<T>
```

nếu thread trả kết quả:

```axiom
let t = Thread.spawn(fn() -> i32 {
    compute()
})

let result = t.join()
```

`join()`:

```text
Result<T, ThreadError>
```

hoặc nếu thread panic:

```text
JoinResult<T>
```

bao gồm trạng thái panic/termination.

Không dùng exception.

---

# 11. Thread panic

Nếu:

```axiom
Thread.spawn(fn() {
    panic("bad")
})
```

thread không được phép làm toàn bộ process panic một cách ngầm định trong model mặc định.

Thay vào đó:

```text
Thread
   ↓
panic
   ↓
thread terminates
   ↓
JoinHandle.join()
   ↓
observes failure
```

Đã khớp với nguyên tắc:

```text
AFERR-44
Task panic is observed at join/task boundary
```

Nếu process profile chọn abort:

```text
panic
 ↓
process abort
```

đó là profile policy.

---

# 12. Detached thread

Có hai semantic rõ ràng:

```axiom
let t = Thread.spawn(worker)
t.join()
```

hoặc:

```axiom
Thread.detach(Thread.spawn(worker))
```

Không nên:

```text
spawn() → tự động detached
```

vì rất dễ tạo:

```text
main()
 ↓
thread
 ↓
process exits
 ↓
thread state/resources abruptly disappear
```

Detached execution phải explicit.

---

# 13. Thread ownership

`ThreadHandle` không nên là ownership của OS thread theo nghĩa:

```text
drop(handle) => kill thread
```

Thay vào đó:

```text
drop(ThreadHandle)
```

chỉ bỏ **quyền join/observe**, nếu thread đã detached hoặc runtime cho phép.

Đây là một distinction rất quan trọng:

```text
Thread lifetime
≠
ThreadHandle lifetime
```

---

# 14. Nhưng structured thread scope vẫn nên có

Để tránh thread leak:

```axiom
thread_scope {
    spawn(...)
    spawn(...)
}
```

Semantic:

```text
enter
  ↓
spawn children
  ↓
wait children
  ↓
leave
```

Nếu muốn detached:

```axiom
detach(...)
```

explicit.

Tương tự async task.

---

# 15. Thread-local storage

TLS không nên là một giant runtime object.

Surface:

```axiom
static thread_local COUNTER: i32 = 0
```

Conceptually:

```text
Thread A
 └── COUNTER = 10

Thread B
 └── COUNTER = 42
```

Compiler/runtime dùng platform TLS:

- Windows TLS
- ELF TLS
- Mach-O TLS
- Android TLS
- iOS TLS

Không cần một Axiom GC/runtime.

---

# 16. TLS initialization

Cần tránh hidden runtime initialization.

Do đó:

```axiom
static thread_local X: Foo = make_foo()
```

phải có semantic rõ:

```text
first access
      ↓
initialize TLS instance
```

hoặc:

```text
thread startup
      ↓
initialize all TLS
```

Tôi đề xuất **lazy TLS initialization** cho non-trivial values.

Primitive trivial TLS có thể dùng native TLS trực tiếp.

---

# 17. Thread-local Drop

Khi thread kết thúc:

```text
thread exit
   ↓
drop TLS resources
   ↓
release TLS storage
   ↓
OS thread termination
```

Nhưng TLS Drop không được phụ thuộc vào một thread đã không còn tồn tại.

Compiler phải xử lý destruction order deterministically.

---

# 18. Thread affinity

Không đưa vào language core.

Library:

```axiom
thread.set_affinity(cpu_mask)
```

hoặc:

```axiom
ThreadConfig {
    affinity: CpuSet(...)
}
```

Platform implementation:

```text
Windows → SetThreadAffinityMask
Linux   → sched_setaffinity
macOS   → platform-specific policy
```

Axiom semantic layer chỉ mô tả:

```text
AffinityHint
```

chứ không hứa OS luôn thực thi chính xác.

---

# 19. Thread priority

Tương tự:

```text
Priority
```

là platform policy.

Không nên có:

```axiom
thread.priority = 99
```

với semantics giống nhau trên mọi OS.

Thay vào đó:

```axiom
ThreadConfig {
    priority: PlatformPriority(...)
}
```

và failure phải được báo:

```text
Result<(), ThreadError>
```

---

# 20. CPU count và topology

Std có thể cung cấp:

```axiom
cpu_count()
cpu_info()
```

Nhưng:

```text
cpu_count()
```

không có nghĩa:

```text
available_parallel_execution_units
```

vì container/affinity/cgroup/OS policy có thể thay đổi.

Do đó API nên phân biệt:

```text
logical_cpu_count
available_cpu_count
```

nếu platform hỗ trợ.

---

# 21. Thread-safe allocator

Không nên mặc định:

```text
Thread → riêng một allocator
```

Nhưng allocator abstraction có thể hỗ trợ:

```text
GlobalAllocator
ThreadLocalAllocator
Arena
Pool
Slab
```

Một high-performance server có thể:

```text
CPU 0 → Arena 0
CPU 1 → Arena 1
CPU 2 → Arena 2
CPU 3 → Arena 3
```

giảm contention.

Đây là library/runtime policy.

---

# 22. Thread + async scheduler

Đây là kiến trúc quan trọng:

```text
                  Executor
                     │
          ┌──────────┼──────────┐
          ↓          ↓          ↓
       Thread 0   Thread 1   Thread 2
          │          │          │
       Tasks      Tasks      Tasks
```

Thread pool:

```text
N OS threads
M async tasks
```

với:

```text
M >> N
```

hoàn toàn bình thường.

---

# 23. Không có "Axiom runtime thread"

Một binary đơn giản:

```axiom
fn main() -> i32 {
    42
}
```

có thể compile thành:

```text
PE/ELF/Mach-O
    ↓
entry
    ↓
main
    ↓
exit
```

Không cần:

```text
runtime thread
scheduler
GC
TLS runtime
allocator runtime
```

Nếu chương trình cần thread:

```axiom
Thread.spawn(...)
```

thì mới kéo thread subsystem vào.

Đây là **capability-driven runtime linking**.

---

# 24. Thread memory budget

Ta có thể đặt guideline thay vì hard guarantee:

### Thread handle

```text
~1–3 machine words
```

### Thread metadata

```text
platform dependent
```

### Stack

```text
configurable
```

### TLS

```text
only declared TLS
```

### Axiom runtime metadata

```text
minimum required
```

Do đó:

```text
Axiom Thread
≠
"Thread struct = X bytes"
```

---

# 25. Fiber

Sau thread, cần xác định fiber vì nó là tầng trung gian rất hữu ích.

```text
Thread
 └── Fiber A
 └── Fiber B
 └── Fiber C
```

Fiber có:

```text
FiberContext
├── registers
├── stack
├── state
└── scheduler linkage
```

Fiber có stack riêng nhưng không có kernel thread riêng.

Dùng cho:

- game scripting
- high-performance networking
- coroutine libraries
- legacy blocking APIs
- user-space scheduling

Nhưng **Fiber không thuộc async Core**.

---

# 26. Stackful Fiber vs Stackless Future

Axiom sẽ có hai abstraction:

```text
Future
    stackless
    very small
    compiler-generated
    async/await

Fiber
    stackful
    larger
    explicit stack
    manual/user scheduler
```

Ví dụ:

```text
100,000 Futures
```

có thể chỉ tốn vài MB nếu state nhỏ.

Trong khi:

```text
100,000 Fibers
```

thường sẽ đắt hơn vì mỗi fiber có stack.

Đây là lý do không nên dùng Fiber làm implementation mặc định cho async.

---

# 27. OS Thread API đề xuất

Tôi đề xuất API conceptual:

```axiom
Thread.spawn(fn) -> JoinHandle<T>

Thread.spawn_with(fn, ThreadConfig) -> Result<JoinHandle<T>, ThreadError>

Thread.current() -> ThreadId

Thread.sleep(duration)

Thread.yield()

Thread.detach(handle)

ThreadScope

ThreadConfig {
    stack_size
    name
    affinity
    priority
}
```

Platform-specific APIs nằm dưới:

```text
std.platform.windows
std.platform.linux
std.platform.apple
```

---

# 28. Invariants

Chốt thêm:

```text
ATHREAD-20
Thread Is An OS Execution Resource

ATHREAD-21
ThreadHandle Is Not Thread Storage

ATHREAD-22
Thread Handle Drop Does Not Imply Thread Termination

ATHREAD-23
Thread Join Observes Completion

ATHREAD-24
Detached Thread Lifetime Is Independent Of Handle Lifetime

ATHREAD-25
Thread Stack Lifetime Covers Thread Execution

ATHREAD-26
Thread Stack Size Is Configurable

ATHREAD-27
Thread Stack Allocation Is Platform-Dependent

ATHREAD-28
Thread Capture Transfer Requires Send

ATHREAD-29
Local Thread Execution Does Not Require Send

ATHREAD-30
Thread Panic Is Observed At Join Boundary

ATHREAD-31
Forced Thread Termination Is Not Safe Core Semantics

ATHREAD-32
Thread-Local Storage Has Per-Thread Identity

ATHREAD-33
TLS Destruction Is Deterministic

ATHREAD-34
Thread Affinity Is A Platform Policy

ATHREAD-35
Thread Priority Is A Platform Policy

ATHREAD-36
Thread Does Not Imply Async Scheduler

ATHREAD-37
Async Task Does Not Imply OS Thread

ATHREAD-38
Fiber Does Not Imply OS Thread

ATHREAD-39
Fiber Stack Is Explicit Storage

ATHREAD-40
No Mandatory Thread Runtime

ATHREAD-41
No Mandatory Thread-Local Allocator

ATHREAD-42
Thread Creation Does Not Imply Heap Allocation By Language Semantics

ATHREAD-43
Thread Configuration Is Separate From Thread Identity

ATHREAD-44
Thread Scope Must Resolve Child Thread Lifetime

ATHREAD-45
Detached Execution Must Be Explicit
```

---

# 29. Memory architecture tổng thể lúc này

Axiom bắt đầu có một mô hình khá sạch:

```text
                   EXECUTION
                       │
       ┌───────────────┼────────────────┐
       ↓               ↓                ↓
   OS Thread          Fiber            Task
       │               │                │
    OS Stack       Fiber Stack      Future State
       │               │                │
       └───────────────┴────────────────┘
                       │
                  Axiom Values
                       │
       ┌───────────────┼────────────────┐
       ↓               ↓                ↓
    Register          Stack           Storage
                                       │
                          ┌────────────┼────────────┐
                          ↓            ↓            ↓
                        Arena         Pool         Heap
```

Không có một "Axiom memory model" duy nhất ép tất cả ứng dụng vào một chiến lược.

Đây chính là điểm tôi nghĩ nên giữ rất mạnh trong thiết kế.

---

## Bước kế tiếp: FIBER-001

Sau `THREAD-001`, mảnh hợp lý tiếp theo là **FIBER-001 — Stackful Execution Context**.

Nó sẽ giải quyết một câu hỏi quan trọng mà chúng ta chưa chốt: **nếu Axiom không có `Pin`, không có GC và không có borrow-checker syntax, làm sao tạo một fiber có stack riêng, context switch cực nhanh, mà vẫn bảo toàn ownership/capability khi fiber suspend/resume?**

Đồng thời đây là nền tảng để sau này Axiom có thể hỗ trợ **game engine, networking, coroutine kiểu Go, và scheduler tùy biến** mà không làm phình Core.