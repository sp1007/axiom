Tiếp tục với **FIBER-001 — Stackful Execution Context**. Đây là phần rất đáng thiết kế kỹ, vì Fiber là nơi dễ vô tình làm hỏng các nguyên tắc ownership/capability mà ta đã xây dựng.

# FIBER-001 — Axiom Stackful Execution

## 1. Fiber không phải Future

Ta chốt:

```text
Future
    = stackless state machine

Task
    = schedulable Future

Fiber
    = stackful execution context

Thread
    = OS execution resource
```

Quan hệ:

```text
OS Thread
 ├── Fiber A
 │     ├── computation
 │     └── stack
 │
 └── Fiber B
       ├── computation
       └── stack
```

Fiber A/B có thể chạy luân phiên trên cùng một OS thread.

---

# 2. Tại sao Axiom cần Fiber?

Async Future rất hiệu quả:

```axiom
async fn network_request() {
    ...
    await socket.read()
}
```

nhưng không phải mọi API đều thuận tiện khi viết theo continuation/state-machine model.

Fiber cho phép:

```axiom
fn worker() {
    read()
    yield()
    process()
    yield()
    write()
}
```

Code vẫn nhìn như synchronous, nhưng:

```text
yield()
```

trả quyền điều khiển về scheduler.

Điều này đặc biệt hữu ích cho:

- game engine
- scripting
- networking
- coroutine
- actor systems
- emulation
- user-space scheduler
- compatibility với blocking-style APIs.

---

# 3. Fiber có stack riêng

Khác Future:

```text
Future:
    không có stack riêng
```

Fiber:

```text
Fiber
├── execution context
├── stack
├── state
└── scheduler metadata
```

Ví dụ:

```text
Fiber A
┌───────────────────┐
│ stack             │
│                   │
│ local a           │
│ local b           │
│ call frames       │
│                   │
└───────────────────┘
```

---

# 4. Stack không phải heap object semantic

Đây là điểm rất quan trọng.

```text
Fiber
```

**có semantic requirement về execution stack**, nhưng không có requirement rằng stack phải được cấp phát bằng `malloc`.

Runtime có thể dùng:

```text
heap
arena
stack pool
virtual memory
static storage
caller-provided storage
OS reserved memory
```

Ví dụ embedded:

```text
static FiberStorage<64_KiB>
```

hoàn toàn hợp lệ.

---

# 5. Fiber storage phải là explicit contract

Ta đã có:

```text
AMEM-21 Stable Address Is An Explicit Storage Contract
```

Fiber stack là một trường hợp đặc biệt: stack memory có identity trong suốt lifetime của Fiber.

Do đó:

```text
FiberStack<T>
```

có thể yêu cầu:

```text
stable storage
```

Nhưng:

```text
Fiber
```

không được biến mọi value trên stack thành "pinned".

Chỉ stack storage itself có stable identity.

---

# 6. Context switch

Một Fiber context tối thiểu phải bảo toàn:

```text
Registers
Stack Pointer
Instruction Pointer
Callee-saved state
Platform-specific control state
```

Ví dụ conceptual:

```text
FiberContext
├── SP
├── IP
├── callee_saved[]
└── platform_state
```

Không lưu toàn bộ CPU registers nếu ABI/context-switch policy không yêu cầu.

Đây là chỗ Axiom có thể rất nhỏ và nhanh.

---

# 7. Không dùng `setjmp/longjmp` làm Core primitive

Có thể dùng trong bootstrap/prototype, nhưng final backend không nên phụ thuộc.

Axiom nên có target-specific:

```text
FiberSwitchContext
```

Machine IR intrinsic:

```text
SAVE_CONTEXT
RESTORE_CONTEXT
SWITCH_CONTEXT
```

Sau đó backend hạ xuống:

```text
x86-64
AArch64
RISC-V64
...
```

Điều này phù hợp với mục tiêu:

> Không phụ thuộc compiler/runtime bên thứ ba.

---

# 8. Context switch không phải function call

Một switch:

```text
Fiber A
   │
   │ switch
   ▼
Fiber B
```

không phải:

```text
call B()
```

vì A cần resume đúng instruction sau điểm yield.

Conceptually:

```text
A:
    save SP/IP/register state
    jump scheduler

scheduler:
    choose B
    restore B context
    jump B.IP
```

---

# 9. `yield`

API đơn giản:

```axiom
Fiber.yield()
```

Semantic:

```text
RUNNING
   ↓
READY
   ↓
scheduler
   ↓
RUNNING
```

Không phải:

```text
thread sleep
```

và không tạo OS scheduling event.

---

# 10. Fiber scheduler

Có thể có:

```text
FiberScheduler
├── ready queue
├── current fiber
├── suspended fibers
└── completed fibers
```

Nhưng scheduler không phải Core.

Các chiến lược:

```text
FIFO
LIFO
round-robin
priority
work-stealing
custom
```

đều hợp lệ.

---

# 11. Fiber migration

Đây là vấn đề cực kỳ quan trọng.

Fiber có stack.

Nếu Fiber chạy:

```text
Thread A
```

rồi chuyển sang:

```text
Thread B
```

thì cần đảm bảo:

- stack memory vẫn valid
- TLS assumptions không sai
- thread-affine resources không bị sử dụng sai
- execution context hợp lệ.

Do đó tôi đề xuất:

### Fiber mặc định không migrate

```text
Fiber
  ↓
pinned to execution domain
```

Muốn migrate:

```axiom
Fiber.migrate_to(...)
```

phải là explicit API và yêu cầu fiber state thỏa contract.

---

# 12. `Send` của Fiber

Một Fiber đang suspend không nên tự động được coi là `Send`.

Ví dụ:

```text
Fiber {
    stack
    TLS-dependent state
    OS handle
}
```

có thể không an toàn khi chuyển thread.

Do đó:

```text
Fiber: !Send
```

mặc định.

Một specialized fiber có thể implement Send nếu abstraction đảm bảo:

```text
fiber stack transferable
thread-local dependencies absent
```

Nhưng đây là library-defined capability.

---

# 13. Fiber và TLS

Một Fiber chạy trên Thread A:

```text
Thread A
 ├── TLS A
 ├── Fiber 1
 └── Fiber 2
```

Fiber 1/2 **chia sẻ TLS của Thread A**.

Nếu Fiber migrate:

```text
Fiber 1
    ↓
Thread A → Thread B
```

thì TLS semantic thay đổi.

Đây là lý do migration phải explicit.

---

# 14. Fiber local storage

Nếu muốn state gắn với Fiber thay vì OS thread:

```axiom
fiber_local X: Foo
```

conceptually:

```text
Thread
 ├── Fiber A → X=A
 └── Fiber B → X=B
```

Đây là một abstraction hữu ích.

Nhưng tôi không muốn đưa `fiber_local` vào Core v1.0 nếu chưa cần. Library runtime có thể implement.

---

# 15. Fiber stack growth

Có 3 chiến lược:

### Fixed stack

```text
64 KiB
```

Đơn giản và predictable.

### Guarded fixed stack

```text
reserved
├── guard page
├── stack
└── ...
```

Phát hiện overflow tốt hơn.

### Segmented/growable stack

```text
stack segment 1
       ↓
stack segment 2
       ↓
stack segment 3
```

Phức tạp hơn.

### Đề xuất

Axiom MVP:

> **Fixed + guard page**

Sau đó có thể thêm growable stack.

---

# 16. Vì sao không mặc định growable stack?

Vì nó ảnh hưởng:

- pointer stability
- ABI
- debugging
- stack scanning
- performance
- signal handling
- foreign code
- stack addresses.

Fixed stack dễ dự đoán hơn.

---

# 17. Fiber stack và pointers

Đây là điểm liên quan trực tiếp tới Axiom memory model.

Ví dụ:

```axiom
fn worker() {
    var x = 10

    save_pointer(&x)

    Fiber.yield()
}
```

Nếu `save_pointer` khiến pointer escape khỏi fiber stack, compiler phải phát hiện.

Một raw pointer:

```text
*x
```

không tự động được phép sống sau:

```text
Fiber.destroy()
```

Safe capability:

```text
view(x)
```

không được phép escape Fiber lifetime.

---

# 18. Fiber destruction

Không được:

```text
destroy fiber
↓
free stack
↓
còn execution frame
```

Fiber chỉ được destroy khi:

```text
state == COMPLETED
```

hoặc explicit cancellation đã đưa nó tới safe termination point.

Không có:

```text
force_free_running_fiber()
```

trong safe API.

---

# 19. Fiber cancellation

Giống async:

```text
cancel request
```

không phải:

```text
kill stack
```

Nếu Fiber đang chạy:

```text
RUNNING
```

scheduler đặt:

```text
CANCEL_REQUESTED
```

Fiber phải tới cancellation point:

```text
yield()
fiber_poll_cancel()
blocking operation
```

rồi cleanup.

---

# 20. Fiber return value

Có thể:

```axiom
let f = Fiber.spawn(fn() -> i32 {
    42
})

let result = f.join()
```

Fiber result có thể được lưu:

```text
FiberControlBlock
├── state
├── stack
└── result
```

Không cần heap riêng cho result.

---

# 21. Fiber stack allocation tối ưu

Ví dụ:

```axiom
Fiber.spawn(worker)
```

runtime có thể:

```text
StackPool
┌───────┬───────┬───────┐
│ 64K   │ 64K   │ 64K   │
└───────┴───────┴───────┘
```

Tạo Fiber:

```text
allocate stack slot
initialize context
enqueue
```

Destroy:

```text
return stack slot
```

Không cần allocator general-purpose.

Điều này rất phù hợp game/networking.

---

# 22. Fiber stack cache

Runtime có thể giữ:

```text
Thread 0
 └── FiberStackCache
       ├── 64K
       ├── 64K
       └── 128K
```

giảm:

```text
OS virtual-memory calls
page allocation
allocator contention
```

Nhưng đây vẫn là optimization.

---

# 23. Fiber ↔ Future

Đây là chỗ kiến trúc trở nên mạnh.

Ta có thể chạy Future trên Fiber:

```text
Fiber
 └── executor
      └── Future
```

nhưng **không biến Future thành Fiber**.

Ví dụ:

```text
Future A
  ↓
poll
  ↓
Pending
  ↓
Fiber yields
```

Một runtime có thể dùng Fiber để implement một số blocking-style APIs.

---

# 24. Blocking API bridge

Ví dụ:

```axiom
fn read_blocking() -> Data
```

có thể chạy:

```text
Fiber
 ↓
blocking syscall
 ↓
OS thread blocked
```

không tốt.

Runtime có thể chuyển sang:

```text
Fiber
 ↓
async IO
 ↓
suspend Fiber
 ↓
other Fiber runs
```

Đây là library/runtime trick.

Không cần thay đổi semantics của language.

---

# 25. Fiber và `await`

Tôi đề xuất **không cho Fiber có `await` đặc biệt**.

`await` luôn là Future semantic.

Nếu Fiber chạy:

```axiom
async fn run() {
    await socket.read()
}
```

thì executor quyết định cách scheduling.

Fiber chỉ là execution mechanism bên dưới nếu runtime chọn.

---

# 26. Fiber ABI

Fiber switch không phải C ABI.

Ta cần internal ABI:

```text
AxiomFiberABI
```

Conceptual:

```text
FiberContext {
    stack_pointer
    instruction_pointer
    preserved_registers
    platform_state
}
```

Target backend cung cấp:

```text
FiberContextLayout
ContextSwitchLowering
InitialStackFrame
```

---

# 27. Initial fiber stack

Khi tạo Fiber:

```text
stack
┌─────────────────┐
│ initial frame   │
│ trampoline      │
│ worker closure  │
└─────────────────┘
```

Instruction pointer:

```text
fiber_trampoline
```

Trampoline gọi worker:

```text
fiber_trampoline()
    ↓
worker()
    ↓
fiber_complete()
```

Nếu worker return:

```text
Fiber → COMPLETED
```

không được return trực tiếp vào scheduler như function call thông thường.

---

# 28. Fiber trampoline

Conceptually:

```axiom
unsafe fn fiber_trampoline(ctx: *mut FiberContext) -> never {
    ...
}
```

Đây là system-level code.

Compiler/runtime đảm bảo:

```text
worker return
→ store result
→ transition state
→ switch scheduler
```

---

# 29. Debugging

Fiber phải có debug mapping:

```text
Fiber
 ↓
stack
 ↓
source frame
 ↓
function
 ↓
line
```

Debug subsystem cần biết:

```text
FiberStack
```

là execution stack.

Nhưng Debug metadata không được ảnh hưởng semantics.

---

# 30. Performance target

Tôi đề xuất mục tiêu, không phải guarantee:

```text
Fiber switch:
    O(number of preserved registers)
```

Không:

```text
allocate
GC
scheduler heap operation
OS syscall
```

trên mỗi switch trong fast path.

Fast path mong muốn:

```text
save registers
save SP
load registers
load SP
jump
```

Scheduler có thể thêm queue manipulation, nhưng context switch bản thân không cần syscall.

---

# 31. Invariants

Chốt:

```text id="2n0q8k"
AFIBER-20
Fiber Is A User-Space Execution Context

AFIBER-21
Fiber Is Not An OS Thread

AFIBER-22
Fiber Has Explicit Execution Stack

AFIBER-23
Fiber Stack Storage Strategy Is Runtime-Selectable

AFIBER-24
Fiber Stack Has Stable Storage During Fiber Lifetime

AFIBER-25
Fiber Context Contains Only Required Machine State

AFIBER-26
Fiber Context Switch Does Not Require OS Thread Creation

AFIBER-27
Fiber Yield Does Not Imply OS Scheduling

AFIBER-28
Fiber Migration Is Not Implicit

AFIBER-29
Fiber Migration Requires Valid Execution Contract

AFIBER-30
Fiber Is Not Send By Default

AFIBER-31
Fiber Stack Cannot Be Destroyed While Executing

AFIBER-32
Fiber Cancellation Is Cooperative

AFIBER-33
Fiber Return Completes Fiber Execution

AFIBER-34
Fiber Result Does Not Require Separate Heap Allocation

AFIBER-35
Fiber Stack Overflow Must Be Detectable

AFIBER-36
Fiber Fixed Stack Is Valid MVP Strategy

AFIBER-37
Fiber Stack Allocation Is Not Language Semantics

AFIBER-38
Fiber Scheduler Is Not Core Language Semantics

AFIBER-39
Fiber TLS Semantics Are Distinct From Thread TLS

AFIBER-40
Fiber Does Not Imply Future Allocation

AFIBER-41
Future Does Not Imply Fiber

AFIBER-42
Fiber Does Not Imply Future

AFIBER-43
Fiber Context Switching Is Target-Specific

AFIBER-44
Fiber Stack Lifetime Bounds Stack Capabilities

AFIBER-45
Running Fiber Cannot Be Force-Freed In Safe Code
```

---

# 32. Bức tranh execution model hoàn chỉnh

Đến đây Axiom có một mô hình khá mạnh:

```text
                         PROCESS
                            │
             ┌──────────────┼──────────────┐
             ↓              ↓              ↓
          Thread 0       Thread 1       Thread 2
             │              │              │
        ┌────┼────┐    ┌────┼────┐        │
        ↓    ↓    ↓    ↓    ↓    ↓        ↓
      Fiber Fiber Fiber Fiber Fiber       ...
        │    │    │
        └────┼────┘
             ↓
          Executor
             ↓
           Tasks
             ↓
          Futures
```

Nhưng quan trọng nhất:

```text
Thread  → OS resource
Fiber   → stackful context
Task    → scheduling abstraction
Future  → computation state
```

Không có một abstraction nào ép abstraction khác phải tồn tại.

---

## Một quyết định kiến trúc lớn tiếp theo

Sau `THREAD-001` + `FIBER-001`, tôi thấy chúng ta nên **dừng việc bổ sung execution primitives và chuyển sang thiết kế `SCHEDULER-001`**.

Đó là nơi ghép toàn bộ:

```text
Thread
   +
Fiber
   +
Task
   +
Future
   +
Send/Share
   +
Channel
   +
Mutex/RwLock
   +
Work stealing
   +
Cancellation
```

vào **một scheduler model thống nhất**, đồng thời giải quyết một vấn đề cực quan trọng cho mục tiêu hiệu năng của Axiom:

> **Làm sao scheduler biết task nào có thể chạy ở đâu mà không cần runtime global lock, không cần GC, không cần object nặng, và vẫn giữ được safety của ownership/capability?**

Đây sẽ là bước quyết định xem concurrency model của Axiom có thực sự đạt mục tiêu "đơn giản cho programmer nhưng hiệu năng gần bare metal" hay không.