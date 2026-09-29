# BOOTSTRAP-747 — AXSYNC

**Namespace:** `AXSYNC`  
**Phase:** Axiom Civilization Runtime / Native Synchronization, Atomicity & Concurrency Coordination Runtime  
**Status:** **ARCHITECTURAL BASELINE — FROZEN TARGET**  
**Depends on:** `AXPROCESS`, `AXMEMORY`, `AXCOMPUTE`, `AXIPC`, `AXSECURITY`, `AXAPPLICATION`, `AXSTORAGE`, `AXNETWORK`, `AXGRAPHICS`, `AXAUDIO`, `AXMEDIA`

AXSYNC là tầng primitive đồng bộ hóa thấp nhất dùng chung cho process, thread, IPC, runtime, I/O, media, graphics và các subsystem concurrent của Axiom.

Mục tiêu cốt lõi:

> **Đồng bộ hóa phải explicit, predictable, bounded và có fast path cực rẻ; không ép programmer vào một memory/concurrency model nặng hơn cần thiết.**

AXSYNC **không phải scheduler** và **không phải async runtime**.

---

# 747.1 — Strong Boundary

### AXSYNC owns

```text
atomic operations
memory ordering
fences
mutex
spinlock
rwlock
semaphore
event
condition variable
latch
barrier
once
futex-like wait/wake
wait set integration
lock-free primitives
wait-free primitives
process-shared synchronization
priority inversion mitigation
deadlock diagnostics
contention profiling
deterministic synchronization replay
CPU/GPU fence abstraction
```

### AXPROCESS owns

```text
process lifecycle
thread lifecycle
execution context
thread stack
TLS
process address space
```

### AXCOMPUTE owns

```text
CPU scheduling
worker scheduling
task scheduling
CPU topology policy
```

### AXIPC owns

```text
message transport
channels
ports
IPC queues
IPC request/response
IPC flow control
```

AXIPC sử dụng AXSYNC; AXSYNC không sở hữu message semantics.

---

# 747.2 — Design Principle

Không tạo một primitive duy nhất cho mọi workload.

Axiom cung cấp nhiều tầng:

```text
atomic
   ↓
spin
   ↓
mutex
   ↓
rwlock
   ↓
semaphore/event
   ↓
condition
   ↓
barrier/latch
   ↓
higher-level concurrent structure
```

Programmer/compiler chọn primitive phù hợp.

---

# 747.3 — No Hidden Synchronization

Axiom không mặc định chèn:

```text
global locks
reference-count locks
GC stop-the-world
implicit monitor
implicit mutex
```

vào code thông thường.

Nếu một operation cần synchronization, semantics phải có thể truy ra được.

---

# 747.4 — Atomic Model

Atomic là primitive nền:

```axiom
atomic<T>
```

với constraint `T` phụ thuộc backend/platform.

---

# 747.5 — Supported Atomic Types

Tối thiểu:

```text
atomic<bool>
atomic<u8>
atomic<u16>
atomic<u32>
atomic<u64>
atomic<i8>
atomic<i16>
atomic<i32>
atomic<i64>
atomic<pointer>
```

Atomic wider nếu CPU hỗ trợ.

---

# 747.6 — Atomic Operations

```axiom
load()
store()
exchange()
compare_exchange()
fetch_add()
fetch_sub()
fetch_and()
fetch_or()
fetch_xor()
```

Compiler lower trực tiếp xuống instruction tương ứng.

---

# 747.7 — Compare Exchange

Hỗ trợ:

```axiom
compare_exchange(expected, desired)
```

với:

```text
success_order
failure_order
```

---

# 747.8 — Strong / Weak CAS

```text
compare_exchange_strong
compare_exchange_weak
```

Weak CAS cho phép spurious failure.

Compiler/runtime không được che giấu semantics này.

---

# 747.9 — Memory Ordering

Axiom chuẩn hóa:

```text
RELAXED
ACQUIRE
RELEASE
ACQ_REL
SEQ_CST
```

---

# 747.10 — Relaxed

`RELAXED` đảm bảo atomicity nhưng không tạo synchronization relationship.

Dùng cho:

```text
counters
statistics
sequence numbers
lock-free algorithms
```

khi algorithm đã được chứng minh đúng.

---

# 747.11 — Acquire

Acquire ngăn các operation sau đó bị quan sát trước synchronization point tương ứng.

---

# 747.12 — Release

Release đảm bảo các operation trước đó được publish trước khi synchronization event được phát hành.

---

# 747.13 — Acquire/Release

Dùng cho handoff:

```text
Producer
    write data
       ↓
release flag
       ↓
acquire flag
       ↓
Consumer
    read data
```

---

# 747.14 — Sequential Consistency

`SEQ_CST` cung cấp ordering mạnh nhất trong model chuẩn.

Không mặc định sử dụng vì có thể tạo overhead không cần thiết.

---

# 747.15 — Fence

```axiom
fence(order)
```

Hỗ trợ:

```text
compiler fence
CPU memory fence
```

Compiler phải phân biệt hai loại.

---

# 747.16 — Compiler Fence

Compiler fence chỉ hạn chế compiler reordering.

Không mặc nhiên phát hardware fence.

---

# 747.17 — Hardware Fence

Hardware fence được lower theo architecture:

```text
x86-64
ARM64
RISC-V
```

và platform backend.

---

# 747.18 — Atomic Alignment

Atomic object phải được align theo yêu cầu architecture.

Compiler reject hoặc lower bằng fallback nếu alignment không hợp lệ.

---

# 747.19 — Atomic Lock-Free Property

Runtime expose:

```axiom
is_lock_free<T>()
```

để programmer biết atomic có thực sự lock-free hay không.

---

# 747.20 — Atomic Wait

Atomic có primitive:

```axiom
wait(value)
notify_one()
notify_all()
```

Đây là primitive quan trọng để tránh spin vô hạn.

---

# 747.21 — Atomic Wait Fast Path

Canonical:

```text
load
 ↓
value unchanged?
 ↓
spin briefly
 ↓
kernel/futex wait
```

---

# 747.22 — Spinlock

```axiom
spinlock
```

phù hợp critical section cực ngắn.

Không được sleep trong spinlock critical section.

---

# 747.23 — Adaptive Spinlock

Backend có thể:

```text
spin
 ↓
pause/yield
 ↓
park
```

khi contention cao.

---

# 747.24 — CPU Pause

Spin loops phải sử dụng architecture-appropriate pause/yield instruction khi có thể.

---

# 747.25 — Mutex

```axiom
mutex
```

là blocking mutual exclusion primitive.

Canonical semantics:

```text
lock()
try_lock()
unlock()
```

---

# 747.26 — Mutex Ownership

Mutex phải ghi nhận owner thread trong debug/diagnostic mode.

Production implementation có thể giảm metadata nếu không cần.

---

# 747.27 — Recursive Mutex

Recursive mutex được hỗ trợ như specialized primitive:

```axiom
recursive_mutex
```

nhưng không phải mutex mặc định.

---

# 747.28 — Timed Lock

```axiom
try_lock_until(deadline)
```

sử dụng monotonic deadline.

---

# 747.29 — Mutex Fast Path

Uncontended:

```text
CAS
 ↓
success
```

không syscall.

---

# 747.30 — Mutex Slow Path

Contended:

```text
CAS failed
 ↓
optional short spin
 ↓
park
 ↓
wake
```

---

# 747.31 — Futex-Like Primitive

AXSYNC cung cấp abstraction:

```axiom
wait_on(address, expected)
wake_one(address)
wake_all(address)
```

Primitive có thể lower xuống:

```text
Windows wait primitive
Linux futex
macOS equivalent
```

---

# 747.32 — User/Kernel Boundary

Wait primitive chỉ vào kernel khi cần.

Mục tiêu:

```text
uncontended → user mode
contended → kernel wait
```

---

# 747.33 — Semaphore

```axiom
semaphore
```

với counter:

```text
acquire()
try_acquire()
release()
```

---

# 747.34 — Counting Semaphore

Cho phép:

```text
0 ... N
```

resource permits.

---

# 747.35 — Binary Semaphore

Specialized:

```text
0 / 1
```

nhưng ownership semantics khác mutex.

---

# 747.36 — Event

```axiom
event
```

dùng signal state change.

Modes:

```text
AUTO_RESET
MANUAL_RESET
```

---

# 747.37 — Event Semantics

Manual reset:

```text
set()
 ↓
all waiters can proceed
 ↓
reset()
```

Auto reset:

```text
set()
 ↓
one waiter proceeds
 ↓
event resets
```

---

# 747.38 — Condition Variable

```axiom
condition_variable
```

luôn sử dụng cùng một mutex/lock discipline.

Canonical:

```axiom
while !condition {
    cv.wait(lock)
}
```

---

# 747.39 — Spurious Wake

Condition variable có thể wake dù condition chưa đúng.

Programmer phải kiểm tra predicate lại.

---

# 747.40 — Condition Deadline

```axiom
wait_until(lock, deadline)
```

trả về:

```text
SIGNALED
TIMEOUT
CANCELLED
```

---

# 747.41 — Read/Write Lock

```axiom
rwlock
```

cho:

```text
multiple readers
single writer
```

---

# 747.42 — Reader Policy

AXSYNC không bắt buộc reader-preferred hoặc writer-preferred.

Backend policy phải xác định fairness semantics.

---

# 747.43 — Writer Starvation

Implementation phải có tùy chọn ngăn writer starvation trong fairness profile.

---

# 747.44 — Upgrade/Downgrade

Optional:

```axiom
upgrade_read()
downgrade_write()
```

Upgrade có thể fail nếu contention tồn tại để tránh deadlock.

---

# 747.45 — Latch

```axiom
latch(count)
```

Thread có thể:

```text
count_down()
wait()
```

Khi count = 0:

```text
all waiters released
```

---

# 747.46 — Barrier

```axiom
barrier(participants)
```

Mỗi participant gọi:

```axiom
arrive_and_wait()
```

khi đủ participant → barrier phase hoàn tất.

---

# 747.47 — Reusable Barrier

Barrier hỗ trợ nhiều generation:

```text
generation 0
 ↓
generation 1
 ↓
generation 2
```

---

# 747.48 — Barrier Drop

Participant có thể:

```axiom
arrive_and_drop()
```

nếu contract cho phép.

---

# 747.49 — Once

```axiom
once
```

đảm bảo initialization chạy một lần.

```axiom
once.call(init)
```

---

# 747.50 — Once Failure

Nếu initialization thất bại, semantics phải rõ:

```text
RETRY
FAILED_PERMANENT
```

Không được phụ thuộc implementation accident.

---

# 747.51 — Atomic Pointer

Axiom hỗ trợ:

```axiom
atomic<pointer<T>>
```

nhưng pointer vẫn tuân memory/lifetime rules của AXMEMORY.

Atomicity không biến pointer thành memory-safe object.

---

# 747.52 — ABA Problem

Lock-free structures phải giải quyết ABA bằng:

```text
generation
tagged pointer
hazard mechanism
epoch mechanism
ownership protocol
```

tùy structure.

---

# 747.53 — Memory Reclamation

AXSYNC không bắt buộc một memory reclamation model duy nhất.

Hỗ trợ primitive cho:

```text
hazard pointers
epochs
quiescent-state reclamation
reference counting
manual reclamation
```

---

# 747.54 — Hazard Pointer

```axiom
hazard<T>
```

thread publish object đang sử dụng trước khi dereference.

---

# 747.55 — Epoch Reclamation

```axiom
epoch_domain
epoch_guard
retire()
```

Object chỉ reclaim sau khi tất cả reader cũ đã rời epoch.

---

# 747.56 — RCU-Like Read Path

Read-mostly structures có thể sử dụng:

```text
read_lock()
read_unlock()
```

với extremely cheap reader path.

---

# 747.57 — Wait-Free

AXSYNC phân biệt:

```text
lock-free
wait-free
obstruction-free
```

Không được gọi một algorithm là wait-free nếu chỉ lock-free.

---

# 747.58 — Lock-Free Guarantee

Lock-free nghĩa là:

> luôn có ít nhất một thread có thể tiến triển sau một số hữu hạn atomic steps.

---

# 747.59 — Wait-Free Guarantee

Wait-free yêu cầu:

> mỗi operation hoàn thành trong số bước hữu hạn độc lập với hành vi của thread khác.

---

# 747.60 — Progress Annotation

Concurrency API có thể khai báo:

```text
progress = blocking
progress = lock_free
progress = wait_free
```

Compiler/AI tools có thể sử dụng metadata này.

---

# 747.61 — Concurrent Counter

Axiom cung cấp:

```axiom
atomic_counter
```

cho statistics/high-frequency counters.

---

# 747.62 — Concurrent Ring Buffer

AXSYNC cung cấp primitives cần thiết cho:

```text
SPSC
MPSC
MPMC
```

nhưng ring-buffer ownership thuộc subsystem sử dụng nó.

---

# 747.63 — Sequence Counter

Sequence counter dùng cho:

```text
lock-free publication
snapshot consistency
ring queues
```

---

# 747.64 — Seqlock

Optional primitive:

```axiom
seqlock
```

reader retry nếu writer thay đổi version trong quá trình đọc.

Phù hợp small read-mostly state.

---

# 747.65 — Ticket Lock

Optional:

```axiom
ticket_lock
```

cho fairness deterministic.

---

# 747.66 — Queue Lock

Optional MCS/queue-style locking backend cho contention cao.

Không expose mọi backend ở high-level API nếu không cần.

---

# 747.67 — Lock Trait

Axiom có abstraction:

```axiom
lockable<T>
```

để generic code làm việc với:

```text
mutex
rwlock
spinlock
```

---

# 747.68 — Scoped Lock

Compiler/runtime hỗ trợ:

```axiom
with lock(m) {
    critical_section()
}
```

Compiler đảm bảo unlock trên normal scope exit và các đường control-flow hợp lệ.

---

# 747.69 — Exception Safety

Nếu Axiom có structured failure propagation, scoped lock phải đảm bảo:

```text
acquire
 ↓
body
 ↓
release
```

không phụ thuộc body return/error path.

---

# 747.70 — No RAII Requirement

Đây là compiler-generated deterministic cleanup, không yêu cầu C++-style class/destructor model.

---

# 747.71 — Lock Ordering

Programmer/service có thể khai báo:

```axiom
lock_order A < B
```

Runtime diagnostic kiểm tra violation trong debug mode.

---

# 747.72 — Deadlock Detection

AXSYNC có thể xây wait graph:

```text
Thread A → Lock B
Thread B → Lock C
Thread C → Lock A
```

và báo cycle.

---

# 747.73 — Deadlock Detection Mode

Các profile:

```text
OFF
DEBUG
DIAGNOSTIC
DETERMINISTIC
```

Production default không cần global graph.

---

# 747.74 — Deadlock Recovery

AXSYNC **không tự động phá lock** để giải quyết deadlock.

Có thể:

```text
detect
report
capture trace
```

nhưng recovery thuộc application policy.

---

# 747.75 — Lock Ownership Validation

Debug runtime phát hiện:

```text
unlock by non-owner
double unlock
recursive misuse
destroy while locked
```

---

# 747.76 — Priority Inversion

Tình huống:

```text
High priority → waits lock
Low priority → owns lock
Medium priority → consumes CPU
```

phải được nhận diện trong supported scheduling profiles.

---

# 747.77 — Priority Inheritance

Mutex có thể hỗ trợ:

```axiom
priority_inheritance
```

khi platform scheduler cho phép.

---

# 747.78 — Priority Ceiling

Alternative:

```axiom
priority_ceiling
```

cho realtime profile.

---

# 747.79 — Scheduler Boundary

AXSYNC chỉ yêu cầu scheduler hỗ trợ contract.

AXCOMPUTE/AXPROCESS thực hiện priority changes.

---

# 747.80 — Realtime Mutex

Realtime profile có:

```text
bounded acquisition
bounded wait
priority inversion mitigation
```

nhưng không thể đảm bảo bounded latency nếu OS/backend không cung cấp guarantee tương ứng.

---

# 747.81 — Cancellation-Safe Locking

Cancellation không được làm lock:

```text
permanently owned
```

nếu operation bị hủy giữa critical section.

---

# 747.82 — Cancellation Point

Cancellation nên xảy ra tại safe points:

```text
before acquire
after release
explicit cancellation checkpoint
blocking wait
```

---

# 747.83 — Forced Cancellation

Forced thread termination không được mặc định tự động unlock mọi mutex.

Đó là lý do forced cancellation phải cực kỳ hạn chế.

---

# 747.84 — Process-Shared Mutex

Nếu backend hỗ trợ, mutex có thể:

```axiom
shared_mutex
```

giữa processes.

---

# 747.85 — Process-Shared State

Shared synchronization object phải nằm trong shared memory region hợp lệ.

---

# 747.86 — Owner Death

Process-shared mutex phải có semantics:

```text
OWNER_ALIVE
OWNER_DIED
RECOVERABLE
NOT_RECOVERABLE
```

nếu platform hỗ trợ robust ownership.

---

# 747.87 — Robust Mutex Recovery

Nếu owner chết:

```text
lock()
 ↓
OWNER_DIED
 ↓
recover()
 ↓
consistent()
```

Application chịu trách nhiệm xác định shared state có còn nhất quán hay không.

---

# 747.88 — Cross-Process Event

AXSYNC event có thể được đặt trong shared IPC/control region nếu backend cho phép.

---

# 747.89 — IPC Integration

AXIPC sử dụng:

```text
atomic
wait/wake
semaphore
event
ring synchronization
```

từ AXSYNC.

---

# 747.90 — IPC Wait Set Integration

AXSYNC cung cấp wait primitive.

AXIPC sở hữu endpoint semantics.

---

# 747.91 — Async Integration

Async runtime có thể suspend task trên:

```text
mutex
semaphore
event
condition
IPC endpoint
```

nhưng scheduler thuộc AXCOMPUTE/runtime layer.

---

# 747.92 — Blocking vs Suspending

API phải phân biệt:

```text
thread-blocking wait
task-suspending wait
poll
```

Không được khiến async task vô tình block worker thread.

---

# 747.93 — Task-Aware Mutex

Higher runtime có thể cung cấp:

```axiom
task_mutex
```

dựa trên AXSYNC primitive nhưng ownership thuộc task runtime.

---

# 747.94 — Thread Mutex

Native OS-thread synchronization:

```axiom
thread_mutex
```

ownership thuộc thread.

---

# 747.95 — Task Mutex

Task mutex ownership thuộc logical task.

Hai abstraction không được đánh đồng.

---

# 747.96 — GPU Fence

AXSYNC cung cấp generic:

```axiom
fence
```

cho synchronization giữa execution domains.

---

# 747.97 — CPU/GPU Fence

```text
CPU
 ↓
submit GPU work
 ↓
GPU fence
 ↓
GPU complete
 ↓
CPU wait
```

AXGRAPHICS/AXCOMPUTE sở hữu scheduling; AXSYNC sở hữu synchronization primitive abstraction.

---

# 747.98 — Device Fence

Device synchronization có thể biểu diễn:

```text
signal
wait
merge
```

---

# 747.99 — Fence Merge

```axiom
merge_fences(a, b)
```

tạo dependency chờ cả hai completion.

---

# 747.100 — Fence Timeline

Timeline fence:

```text
0 → 1 → 2 → 3 → ...
```

Consumer có thể chờ:

```axiom
wait_until(fence, 3)
```

---

# 747.101 — Memory Visibility

Fence chỉ đảm bảo visibility theo contract.

Không được hiểu fence là ownership transfer tự động.

---

# 747.102 — Ownership Handoff

Canonical:

```text
Producer writes
      ↓
release
      ↓
handoff
      ↓
acquire
      ↓
Consumer reads
```

---

# 747.103 — Data Race

Axiom định nghĩa data race ở semantic level:

Hai concurrent accesses tới cùng memory location, ít nhất một write, mà không có synchronization/happens-before phù hợp.

---

# 747.104 — Race Detection

Debug runtime có thể cung cấp:

```text
race instrumentation
shadow memory
happens-before tracking
```

---

# 747.105 — Race Detection Cost

Race detector không phải production default.

---

# 747.106 — Thread Sanitization

Diagnostic profile có thể instrument:

```text
atomic
lock
unlock
wait
wake
memory access
```

---

# 747.107 — False Positive Policy

Diagnostic engine phải ghi nhận:

```text
instrumentation limitations
```

không biến mọi suspicious access thành confirmed race.

---

# 747.108 — Contention Profiling

Theo dõi:

```text
lock acquisition count
wait count
wait duration
hold duration
contention count
```

---

# 747.109 — Lock Hotspot

Profiler có thể xác định:

```text
lock X
  40M acquisitions
  10M contended
```

để tối ưu architecture.

---

# 747.110 — Atomic Contention

Theo dõi optional:

```text
CAS retries
failed exchanges
cache-line bouncing
```

---

# 747.111 — Cache-Line Awareness

AXSYNC structures nên hỗ trợ:

```text
cacheline alignment
padding
false-sharing avoidance
```

---

# 747.112 — NUMA Synchronization

Shared lock placement có thể được tối ưu theo NUMA topology.

---

# 747.113 — Locality

Các counters/queues có thể sử dụng:

```text
per-thread
per-core
per-NUMA-node
```

và aggregate khi cần.

---

# 747.114 — Global Lock Avoidance

Axiom runtime không được có global lock bắt buộc cho:

```text
allocation
logging
IPC
scheduler fast path
```

nếu architecture có thể tránh.

---

# 747.115 — Sharded Synchronization

Global state nên partition:

```text
hash → shard
```

để giảm contention.

---

# 747.116 — Lock Elision

Backend có thể hỗ trợ hardware lock elision nếu platform cung cấp.

Không được phụ thuộc vào nó để correctness.

---

# 747.117 — Transactional Synchronization

Hardware transactional memory nếu tồn tại chỉ là optimization.

Fallback phải giữ cùng semantics.

---

# 747.118 — Once Fast Path

Sau initialization:

```text
once.call()
```

phải có fast path gần như atomic load/branch.

---

# 747.119 — Event Fast Path

Event đã signaled:

```text
check state
 ↓
return
```

không syscall.

---

# 747.120 — Semaphore Fast Path

Nếu count > 0:

```text
CAS decrement
 ↓
success
```

không syscall.

---

# 747.121 — Mutex Fast Path

Nếu owner = none:

```text
CAS none → current
```

---

# 747.122 — Spin Budget

Adaptive spin có configurable:

```text
spin_count
spin_time
CPU topology
priority
```

---

# 747.123 — Energy Awareness

Background applications có thể ưu tiên:

```text
park
```

thay vì aggressive spinning.

---

# 747.124 — Latency Profile

Low-latency profile:

```text
short spin
fast wake
CPU locality
```

---

# 747.125 — Throughput Profile

Throughput profile:

```text
batch
queue
sharding
reduced wakeups
```

---

# 747.126 — Realtime Profile

Realtime profile ưu tiên:

```text
bounded operations
priority inheritance
preallocated synchronization
predictable wake behavior
```

---

# 747.127 — Deterministic Profile

Deterministic execution profile có thể record:

```text
lock acquisition order
wake order
atomic scheduling points
```

---

# 747.128 — Deterministic Replay

Replay có thể force:

```text
Thread A acquires
Thread B waits
Thread A releases
Thread B acquires
```

---

# 747.129 — Replay Boundary

Replay không mặc định tái tạo:

```text
CPU cache timing
hardware interrupts
microarchitectural behavior
```

---

# 747.130 — Synchronization Trace

```axiom
sync_trace_event {
    timestamp
    thread_id
    object_id
    operation
    result
    wait_duration
}
```

---

# 747.131 — Object Identity

Synchronization object identity phải:

```text
stable
opaque
generation-safe
```

không dựa đơn thuần trên pointer.

---

# 747.132 — Destruction Rule

Không được destroy synchronization object khi:

```text
waiters exist
owner exists
operations in flight
```

trừ explicit force-destroy primitive có semantics riêng.

---

# 747.133 — Force Destroy

Force destroy phải được xem là unsafe/privileged operation.

---

# 747.134 — Initialization

Static synchronization objects phải hỗ trợ zero/constant initialization khi backend cho phép.

---

# 747.135 — Dynamic Initialization

Dynamic object:

```axiom
mutex.create()
```

có explicit lifetime.

---

# 747.136 — Alignment and Placement

Synchronization object có thể đặt trong:

```text
stack
heap
shared memory
static storage
mapped region
```

nếu alignment/lifetime phù hợp.

---

# 747.137 — Embedded Profile

Embedded profile có thể loại bỏ:

```text
kernel wait
priority inheritance
process-shared primitives
```

nếu platform không hỗ trợ.

---

# 747.138 — WASM Profile

WASM runtime có thể map synchronization vào:

```text
worker atomics
shared memory
host synchronization
```

tùy environment.

---

# 747.139 — Single-Thread Profile

Single-threaded program có thể compile synchronization primitives thành minimal/no-op implementations khi compiler chứng minh không có concurrent access.

Ví dụ:

```text
mutex.lock()
mutex.unlock()
```

có thể bị eliminate nếu object không escape tới concurrent execution domain.

---

# 747.140 — Compiler Optimization

Compiler được phép eliminate:

```text
redundant lock/unlock
unreachable synchronization
thread-local synchronization
```

chỉ khi semantics vẫn giữ nguyên.

---

# 747.141 — Escape Analysis

Nếu synchronization object không escape:

```text
thread-local
```

compiler có thể specialize hoặc remove unnecessary synchronization.

---

# 747.142 — Constant Concurrency

Compiler có thể nhận biết:

```text
single-thread program
```

và chọn single-thread runtime profile.

---

# 747.143 — Atomic Elision

Không được eliminate atomic chỉ vì compiler không thấy race trong local compilation unit nếu object có thể externally visible.

---

# 747.144 — ABI

Synchronization ABI phải stable giữa:

```text
Axiom modules
dynamic libraries
native plugins
FFI boundaries
```

---

# 747.145 — FFI

Foreign code có thể sử dụng AXSYNC primitives qua stable ABI handles.

---

# 747.146 — Native ABI Layout

Opaque synchronization object preferred:

```text
sync_handle
```

thay vì expose OS-specific structure.

---

# 747.147 — Header-Free Runtime

Axiom modules có thể consume synchronization services bằng compiler-known ABI metadata.

---

# 747.148 — Error Semantics

Common errors:

```text
TIMEOUT
CANCELLED
NOT_OWNER
ALREADY_LOCKED
INVALID_STATE
DESTROYED
OWNER_DIED
NOT_RECOVERABLE
RESOURCE_EXHAUSTED
```

---

# 747.149 — Panic Avoidance

Production synchronization failures không được mặc định crash toàn process nếu lỗi có thể trả về an toàn.

---

# 747.150 — Programmer Contract

Một số misuse có thể là programmer error:

```text
unlock by non-owner
destroy locked mutex
barrier participant mismatch
```

Debug profile phải detect rõ.

---

# 747.151 — Security Boundary

AXSYNC không tự cấp:

```text
process access
memory access
privileged scheduling
```

---

# 747.152 — Protected Synchronization

Security-sensitive synchronization object có thể yêu cầu capability.

---

# 747.153 — Cross-Sandbox Sync

Cross-sandbox synchronization phải đi qua:

```text
AXSECURITY
AXIPC
```

không tự bypass sandbox.

---

# 747.154 — AI Boundary

AI được phép:

```text
analyze contention
detect likely deadlock
suggest lock sharding
suggest atomic ordering
suggest queue topology
analyze race traces
```

AI không được:

```text
disable synchronization security
break process isolation
modify protected synchronization state
grant scheduling authority
bypass mutex ownership
```

---

# 747.155 — AI Memory-Order Analysis

AI tooling có thể phân tích:

```text
acquire/release
happens-before
CAS loops
```

và đưa ra diagnostic.

Kết quả AI không thay thế compiler correctness checks.

---

# 747.156 — Formal Memory Model Boundary

AXSYNC defines synchronization primitives.

Axiom language core defines:

```text
happens-before
sequenced-before
synchronizes-with
data-race semantics
atomic visibility
```

Hai tầng phải thống nhất nhưng không trộn implementation.

---

# 747.157 — Happens-Before

Ví dụ:

```text
Thread A:
write X
release flag

Thread B:
acquire flag
read X
```

Nếu acquire observes appropriate release, `write X` happens-before `read X`.

---

# 747.158 — Synchronizes-With

Các primitive có thể tạo synchronization edge:

```text
release → acquire
unlock → lock
signal → wait
send → receive
```

tùy contract.

---

# 747.159 — IPC Synchronization

AXIPC message receive có thể tạo happens-before edge theo message ownership/transport contract.

---

# 747.160 — Shared Memory

Shared memory **không tự tạo synchronization**.

Programmer phải dùng:

```text
atomic
lock
fence
IPC synchronization
```

---

# 747.161 — Data Ownership

Synchronization không tự transfer memory ownership.

Ownership semantics thuộc AXMEMORY/IPC contract.

---

# 747.162 — Lock Protects Data

Lock chỉ bảo vệ data nếu programmer tuân invariant:

```text
all accesses to protected state
    → same synchronization protocol
```

---

# 747.163 — Lock Annotation

Compiler metadata có thể cho phép:

```axiom
@guarded_by(mutex)
counter
```

Static tooling dùng để phát hiện inconsistent access.

---

# 747.164 — Atomic Annotation

```axiom
@atomic
state
```

yêu cầu mọi access tuân atomic API/semantics.

---

# 747.165 — Thread Safety Traits

Axiom type system/tooling có thể hỗ trợ metadata:

```text
Sendable
Shared
ThreadLocal
Synchronized
Immutable
```

Đây là static contract, không phải GC/borrow checker.

---

# 747.166 — Sendable

Type `T` có thể khai báo:

```text
Sendable<T>
```

nếu có thể transfer ownership sang execution context khác.

---

# 747.167 — Shared

`Shared<T>` biểu thị object có thể được concurrent access theo contract của type.

---

# 747.168 — Immutable

Immutable data có thể được chia sẻ mà không cần lock nếu lifetime hợp lệ.

---

# 747.169 — ThreadLocal

```axiom
thread_local<T>
```

AXPROCESS/TLS backend cung cấp storage; AXSYNC không sở hữu TLS.

---

# 747.170 — Concurrency Contract

Axiom không yêu cầu compiler chứng minh toàn bộ program data-race free.

Thay vào đó:

```text
explicit primitives
+
optional static annotations
+
runtime diagnostics
```

giữ language simple và predictable.

---

# 747.171 — No Borrow Checker Requirement

AXSYNC không phụ thuộc borrow checker.

Lifetime correctness được xử lý bởi:

```text
AXMEMORY
explicit ownership
scope cleanup
handles
optional type annotations
```

---

# 747.172 — No GC Requirement

Synchronization objects không yêu cầu garbage collection.

Lifetime explicit.

---

# 747.173 — Lock-Free Allocator Integration

AXMEMORY có thể dùng:

```text
atomic
CAS
per-thread cache
```

từ AXSYNC.

---

# 747.174 — Runtime Logging

Logging path không được giữ global synchronization lock vô thời hạn.

Preferred:

```text
per-thread buffer
 ↓
lock-free queue
 ↓
consumer
```

---

# 747.175 — Global State

Runtime global state nên sử dụng:

```text
atomic
sharded locks
RCU-like state
immutable snapshots
```

thay vì single global mutex.

---

# 747.176 — Configuration Reload

Immutable configuration snapshot:

```text
old config
    ↓
new config
    ↓
atomic pointer swap
```

reader dùng acquire.

---

# 747.177 — Publish/Subscribe State

Publish:

```text
new object
 ↓
release
 ↓
atomic pointer
```

Subscribe:

```text
acquire
 ↓
read immutable object
```

---

# 747.178 — Lock-Free State Publication

Phù hợp:

```text
routing tables
configuration
service metadata
read-mostly caches
```

---

# 747.179 — Synchronization Object Pool

High-frequency object creation có thể dùng:

```text
mutex pool
event pool
semaphore pool
wait node pool
```

do runtime quản lý.

---

# 747.180 — No Allocation Blocking

`lock()`, `unlock()`, atomic operations và uncontended waits không được yêu cầu general heap allocation.

---

# 747.181 — Wait Node Pool

Contended waiters có thể lấy node từ per-thread/per-core pool.

---

# 747.182 — Wake Batching

`notify_all` có thể tối ưu bằng batch wake nếu OS/backend hỗ trợ.

---

# 747.183 — Thundering Herd

Runtime phải tránh đánh thức hàng trăm threads nếu chỉ một resource trở nên available.

---

# 747.184 — Fair Wake

Wait queues có thể hỗ trợ:

```text
FIFO
priority
adaptive
```

policy.

---

# 747.185 — Starvation

Fairness-sensitive primitives phải document rõ khả năng starvation.

---

# 747.186 — Priority Queue

Realtime wait queues có thể ưu tiên theo scheduling priority.

---

# 747.187 — Deadline-Aware Wake

Nếu workload yêu cầu deadline, waiter có thể được sắp xếp theo:

```text
deadline
priority
arrival
```

nhưng actual thread scheduling vẫn thuộc AXCOMPUTE.

---

# 747.188 — Synchronization Across Devices

AXSYNC có generic fence model cho:

```text
CPU
GPU
DMA
accelerator
device
```

---

# 747.189 — DMA Synchronization

DMA completion có thể signal:

```text
event
fence
timeline
```

AXMEMORY chịu trách nhiệm cache coherency/mapping semantics.

---

# 747.190 — Cache Coherency Boundary

AXSYNC không tự flush CPU caches cho arbitrary memory.

Device coherency thuộc AXMEMORY/device backend.

---

# 747.191 — Power State Integration

Blocking synchronization có thể cooperate với power management:

```text
sleep
wake
```

nhưng power manager không thuộc AXSYNC.

---

# 747.192 — Diagnostics Snapshot

Có thể snapshot:

```text
locks
owners
waiters
contention
atomic counters
deadlock graph
```

---

# 747.193 — Production Diagnostics

Production snapshot phải bounded và không được dừng toàn bộ application nếu không cần.

---

# 747.194 — Security of Diagnostics

Lock ownership/thread information có thể chứa sensitive process topology.

Access cần security policy phù hợp.

---

# 747.195 — Deterministic Simulator

Simulator có thể model:

```text
thread count
lock latency
atomic latency
wake latency
contention
priority
```

---

# 747.196 — Fault Injection

Test runtime có thể inject:

```text
forced timeout
delayed wake
spurious wake
contention
owner termination
```

để kiểm tra synchronization correctness.

---

# 747.197 — Concurrency Stress

Native test harness phải hỗ trợ:

```text
high thread count
high contention
random scheduling
repeated creation/destruction
long-running stress
```

---

# 747.198 — Linearizability Testing

Lock-free structures có thể được test bằng operation histories:

```text
invoke
response
ordering
```

và kiểm tra linearization point.

---

# 747.199 — Formal Verification Hooks

Primitive có metadata:

```text
linearization_point
memory_order
ownership
progress_guarantee
```

để formal tools/AI analyzers sử dụng.

---

# 747.200 — Formal Invariants

```text
SYNC-INV-01   Every synchronization object has a stable logical identity.
SYNC-INV-02   Atomic operations obey the declared memory-order semantics.
SYNC-INV-03   Atomic alignment requirements are respected.
SYNC-INV-04   Atomicity does not imply memory ownership.
SYNC-INV-05   Relaxed operations do not implicitly create acquire/release ordering.
SYNC-INV-06   Acquire operations cannot be weakened without changing semantics.
SYNC-INV-07   Release operations cannot be reordered past their synchronization boundary.
SYNC-INV-08   Sequential consistency is stronger than relaxed/acquire/release ordering.
SYNC-INV-09   Atomic wait observes the specified atomic state.
SYNC-INV-10   Wake operations cannot grant ownership by themselves.

SYNC-INV-11   Mutex ownership is exclusive.
SYNC-INV-12   A mutex cannot be unlocked by a non-owner under ownership-enforcing semantics.
SYNC-INV-13   Destroying an actively owned mutex is invalid.
SYNC-INV-14   Condition-variable wake does not imply predicate truth.
SYNC-INV-15   Semaphore permits cannot become negative.
SYNC-INV-16   Event reset semantics are explicit.
SYNC-INV-17   Barrier completion requires the declared participant condition.
SYNC-INV-18   Latch completion occurs only when its counter reaches zero.
SYNC-INV-19   Once initialization cannot execute concurrently more than once.
SYNC-INV-20   Timed waits use a defined monotonic deadline domain.

SYNC-INV-21   Shared synchronization objects require valid shared-memory lifetime.
SYNC-INV-22   Process-shared synchronization cannot bypass AXSECURITY.
SYNC-INV-23   Owner-death state is explicit when supported.
SYNC-INV-24   Robust recovery cannot silently assume shared-state consistency.
SYNC-INV-25   Forced thread termination does not implicitly repair arbitrary locks.
SYNC-INV-26   Cancellation cannot silently leave synchronization ownership inconsistent.
SYNC-INV-27   Waiters observe valid object lifetime.
SYNC-INV-28   Wakeups cannot access destroyed wait state.
SYNC-INV-29   Lock-free claims require a valid progress guarantee.
SYNC-INV-30   Wait-free claims require a bounded per-operation progress guarantee.

SYNC-INV-31   Lock-free reclamation cannot free an object still reachable by a protected reader.
SYNC-INV-32   Shared memory does not imply synchronization.
SYNC-INV-33   Synchronization does not automatically transfer memory ownership.
SYNC-INV-34   Data-race diagnostics do not alter production semantics.
SYNC-INV-35   Diagnostic instrumentation cannot weaken synchronization correctness.
SYNC-INV-36   Deterministic replay preserves logical synchronization order only within its declared model.
SYNC-INV-37   Scheduler policy remains owned by AXCOMPUTE/AXPROCESS.
SYNC-INV-38   IPC transport semantics remain owned by AXIPC.
SYNC-INV-39   GPU/device synchronization cannot bypass owning subsystem resource rules.
SYNC-INV-40   Uncontended synchronization fast paths must not require mandatory heap allocation or unnecessary kernel transitions.
```

---

# 747.201 — Native API

```axiom
atomic_load()
atomic_store()
atomic_exchange()
atomic_compare_exchange()
atomic_fetch_add()
atomic_fetch_sub()
atomic_fetch_and()
atomic_fetch_or()
atomic_fetch_xor()

atomic_wait()
atomic_notify_one()
atomic_notify_all()

fence()

create_mutex()
lock()
try_lock()
lock_until()
unlock()

create_recursive_mutex()

create_spinlock()
spin_lock()
spin_try_lock()
spin_unlock()

create_rwlock()
read_lock()
read_unlock()
write_lock()
write_unlock()
upgrade_read()
downgrade_write()

create_semaphore()
acquire()
try_acquire()
acquire_until()
release()

create_event()
set()
reset()
wait_event()

create_condition()
wait_condition()
notify_one()
notify_all()

create_latch()
count_down()
wait_latch()

create_barrier()
arrive()
arrive_and_wait()
arrive_and_drop()

create_once()
call_once()

create_wait_set()
wait_set_add()
wait_set_remove()
wait_set_wait()

create_hazard_domain()
protect()
clear_hazard()
retire()

create_epoch_domain()
enter_epoch()
leave_epoch()
retire_epoch()

create_fence()
signal_fence()
wait_fence()
merge_fences()

start_sync_trace()
stop_sync_trace()

capture_sync_snapshot()
start_deadlock_detection()

create_sync_simulator()
inject_sync_fault()
replay_sync_trace()

query_lock_stats()
query_atomic_stats()
query_wait_stats()
```

---

# 747.202 — Canonical Flow: Mutex

```text
Thread
  │
  ▼
lock()
  │
  ├── uncontended → acquire
  │
  └── contended
          ↓
       spin
          ↓
       park
          ↓
       wake
          ↓
       acquire
  │
  ▼
critical section
  │
  ▼
unlock()
```

---

# 747.203 — Canonical Flow: Acquire/Release

```text
Producer
    │
    ├── write data
    │
    └── release(flag)
              │
              ▼
          atomic flag
              │
              ▼
Consumer
    │
    ├── acquire(flag)
    │
    └── read data
```

---

# 747.204 — Canonical Flow: Condition Variable

```text
Thread
  │
  ▼
lock(mutex)
  │
  ▼
while !predicate
  │
  └── wait(cv, mutex)
          │
          ▼
       unlock internally
          │
          ▼
       sleep
          │
          ▼
       wake
          │
          ▼
       relock
  │
  ▼
use state
  │
  ▼
unlock
```

---

# 747.205 — Canonical Flow: Semaphore

```text
Producer
   │
   ▼
release()
   │
   ▼
counter + 1
   │
   ▼
wake waiter

Consumer
   │
   ▼
acquire()
   │
   ├── count > 0 → decrement
   │
   └── count = 0 → wait
```

---

# 747.206 — Canonical Flow: Lock-Free Publication

```text
Writer
  │
  ├── allocate object
  ├── initialize
  └── atomic_store_release(ptr)
                 │
                 ▼
              Reader
                 │
                 ├── atomic_load_acquire(ptr)
                 │
                 └── read immutable object
```

---

# 747.207 — Canonical Flow: Shared-Memory IPC

```text
Process A
   │
   ├── write shared region
   │
   ├── release
   │
   └── notify
          │
          ▼
Process B
   │
   ├── wait
   ├── acquire
   └── read shared region
```

---

# 747.208 — Canonical Flow: Deadlock Diagnostic

```text
Thread A
   ↓
Lock X
   ↓
wait Lock Y

Thread B
   ↓
Lock Y
   ↓
wait Lock X
```

Diagnostic:

```text
wait graph
    ↓
cycle detected
    ↓
capture stack/ownership
    ↓
report
```

Không tự phá lock.

---

# 747.209 — Canonical Flow: Priority Inheritance

```text
Low-priority thread
      │
      ▼
 owns mutex
      │
      ▲
      │
High-priority thread waits
      │
      ▼
priority inheritance
      │
      ▼
Low-priority owner temporarily elevated
      │
      ▼
unlock
      │
      ▼
priority restored
```

Actual priority scheduling thuộc AXCOMPUTE.

---

# 747.210 — Canonical Flow: GPU Fence

```text
CPU
 │
 ├── submit GPU work
 │
 ▼
GPU
 │
 ├── execute
 │
 └── signal fence(N)
          │
          ▼
CPU / dependent device
 │
 └── wait fence(N)
```

---

# 747.211 — Canonical Flow: Deterministic Replay

```text
production/test
     ↓
sync trace
     ↓
lock/wake/acquire sequence
     ↓
deterministic scheduler
     ↓
replay
     ↓
race/deadlock diagnosis
```

---

# 747.212 — Required Compiler Integration

Compiler phải hiểu tối thiểu:

```text
atomic type
atomic ordering
volatile distinction
synchronization intrinsic
scoped lock cleanup
thread/task safety annotations
```

---

# 747.213 — Volatile Distinction

Axiom phải phân biệt:

```text
atomic
volatile
ordinary
```

`volatile` không đồng nghĩa với atomic hoặc thread synchronization.

---

# 747.214 — Atomic vs Volatile

```text
atomic
→ concurrency synchronization

volatile
→ externally observable memory access
```

Ví dụ MMIO/device memory có thể cần volatile nhưng không phải atomic.

---

# 747.215 — Compiler Reordering

Compiler không được reorder ordinary operations qua synchronization boundary nếu làm thay đổi language memory model.

---

# 747.216 — Instruction Selection

Compiler/backend chọn instruction:

```text
LOCK CMPXCHG
LDAR/STLR
AMO
fence
```

tùy target architecture.

---

# 747.217 — Architecture Profiles

AXSYNC backend tối thiểu:

```text
x86-64
ARM64
RISC-V64
```

và mở rộng theo target Axiom.

---

# 747.218 — PE64 / Windows

Windows backend phải map AXSYNC ABI sang native synchronization primitives nhưng application chỉ nhìn thấy Axiom abstraction.

---

# 747.219 — ELF / Linux

Linux backend ưu tiên:

```text
user-space atomics
futex-like waits
```

để giữ uncontended fast path.

---

# 747.220 — Mach-O / macOS

macOS backend cung cấp cùng semantics bằng native primitives phù hợp.

---

# 747.221 — Mobile

Android/iOS backend phải giữ:

```text
sandbox semantics
thread lifecycle
application lifecycle
```

và không giả định unrestricted background execution.

---

# 747.222 — WASM

WASM threads/shared-memory profile có thể sử dụng atomic instructions khi runtime hỗ trợ.

---

# 747.223 — Fallback Backend

Nếu target không có native atomic width mong muốn:

```text
compiler/runtime
    ↓
fallback lock
```

`is_lock_free<T>()` phải phản ánh thực tế.

---

# 747.224 — ABI Compatibility

Synchronization object ABI phải giữ stable giữa:

```text
compiler versions
runtime versions
shared libraries
plugins
```

trong cùng ABI generation.

---

# 747.225 — Versioning

```text
AXSYNC ABI v1
AXSYNC ABI v2
```

không được silently thay đổi memory semantics.

---

# 747.226 — Runtime Profiles

```text
GENERAL
LOW_LATENCY
THROUGHPUT
REALTIME
EMBEDDED
DETERMINISTIC
DEBUG
```

Mỗi profile chỉ thay implementation policy, không thay correctness semantics.

---

# 747.227 — General Profile

Default:

```text
adaptive locks
blocking waits
reasonable fairness
low memory overhead
```

---

# 747.228 — Low-Latency Profile

Ưu tiên:

```text
short spinning
cache locality
fast wake
batching
```

---

# 747.229 — Throughput Profile

Ưu tiên:

```text
sharding
per-core queues
batch wake
reduced contention
```

---

# 747.230 — Realtime Profile

Ưu tiên:

```text
bounded allocation
priority inheritance
predictable blocking
explicit deadlines
```

---

# 747.231 — Debug Profile

Bổ sung:

```text
owner tracking
deadlock detection
race instrumentation
poisoning
stack capture
```

---

# 747.232 — Performance Rule

Không một diagnostic feature nào được trở thành mandatory production dependency.

---

# 747.233 — Runtime Footprint

Minimal AXSYNC runtime phải có thể compile chỉ với:

```text
atomic
fence
mutex
wait/wake
semaphore
event
condition
```

Advanced facilities được link only when used.

---

# 747.234 — Dead-Code Elimination

Unused synchronization primitives không xuất hiện trong final native binary nếu linker/compiler chứng minh không được reference.

---

# 747.235 — Static Linking

Axiom static linker có thể extract từng primitive/module.

---

# 747.236 — Dynamic Linking

Dynamic runtime ABI phải cho phép shared synchronization infrastructure.

---

# 747.237 — No Third-Party Dependency

AXSYNC implementation không phụ thuộc bắt buộc vào:

```text
libstdc++
Boost
pthread wrapper
C runtime synchronization library
```

Axiom compiler/runtime tự sở hữu implementation layer.

---

# 747.238 — Native OS Integration

Axiom có thể gọi OS kernel primitives trực tiếp thông qua internal backend ABI.

---

# 747.239 — Kernel Transition Budget

Hot path phải tránh syscall.

Mục tiêu:

```text
atomic → 0 syscall
uncontended mutex → 0 syscall
uncontended semaphore → 0 syscall
already-signaled event → 0 syscall
```

---

# 747.240 — Completion Criteria

```text
BOOTSTRAP-747
STATUS: COMPLETE / FROZEN

AXSYNC
 ├── Atomic Model
 ├── Memory Ordering
 ├── Fence
 ├── Atomic Wait/Wake
 ├── Mutex
 ├── Recursive Mutex
 ├── Spinlock
 ├── Adaptive Spinlock
 ├── RWLock
 ├── Semaphore
 ├── Event
 ├── Condition Variable
 ├── Latch
 ├── Barrier
 ├── Once
 ├── Futex-Like Wait
 ├── Lock-Free Primitives
 ├── Wait-Free Contract
 ├── Hazard Pointers
 ├── Epoch Reclamation
 ├── Sequence Counters
 ├── Seqlock
 ├── Process-Shared Sync
 ├── Robust Owner Death
 ├── Cancellation Safety
 ├── Priority Inheritance
 ├── Priority Ceiling
 ├── Deadlock Detection
 ├── Race Diagnostics
 ├── Contention Profiling
 ├── NUMA Optimization
 ├── Cache-Line Optimization
 ├── GPU/Device Fence
 ├── DMA Synchronization
 ├── IPC Integration
 ├── Async Integration
 ├── Compiler Integration
 ├── FFI/ABI
 ├── PE64
 ├── ELF
 ├── Mach-O
 ├── Android/iOS
 ├── WASM
 ├── Embedded
 ├── Runtime Profiles
 ├── Deterministic Replay
 ├── AI Boundary
 ├── 40 Formal Invariants
 └── Synchronization Runtime 5.0
```

**BOOTSTRAP-747 / AXSYNC — ARCHITECTURAL BASELINE FROZEN.**

---

# BOOTSTRAP-748 — AXTASK

**Native Task, Future, Promise & Structured Execution Runtime — lightweight tasks, task states, task handles, futures, promises, continuations, task groups, structured concurrency, cancellation propagation, deadlines, task-local state, work stealing, local/global queues, CPU affinity hints, task priorities, cooperative suspension, async I/O integration, IPC integration, synchronization integration, task failure propagation, supervision, task checkpoints, deterministic task scheduling/replay, task tracing, NUMA-aware execution, GPU/accelerator task coordination và Task Runtime 5.0.**