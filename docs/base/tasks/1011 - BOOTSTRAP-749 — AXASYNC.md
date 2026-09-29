# BOOTSTRAP-749 — AXASYNC

**Namespace:** `AXASYNC`  
**Phase:** Axiom Civilization Runtime / Native Async I/O & Completion Runtime  
**Status:** **ARCHITECTURAL BASELINE — FROZEN TARGET**  
**Depends on:** `AXTASK`, `AXPROCESS`, `AXSYNC`, `AXMEMORY`, `AXCOMPUTE`, `AXIPC`, `AXNETWORK`, `AXSTORAGE`, `AXAPPLICATION`, `AXSECURITY`

AXASYNC là tầng **asynchronous operation/completion** của Axiom.

Mục tiêu:

> Biến file I/O, network I/O, IPC, device I/O, timer và các operation có thể chờ thành những completion event có thể trực tiếp đánh thức AXTASK, mà không bắt buộc mỗi operation phải chiếm một OS thread.

Kiến trúc:

```text
Application
     │
     ▼
   AXTASK
     │
     ▼
  AXASYNC
     │
     ├── File I/O ─────── AXSTORAGE
     ├── Network I/O ──── AXNETWORK
     ├── IPC ───────────── AXIPC
     ├── Device I/O
     ├── Timers
     └── OS completion backend
              │
              ├── Windows IOCP / native async APIs
              ├── Linux io_uring / epoll / native async APIs
              ├── macOS/iOS kqueue / native APIs
              ├── Android native I/O
              └── WASM host async interface
```

---

# 749.1 — Strong Boundary

### AXASYNC owns

```text
async operation
operation handle
submission
completion
completion queue
completion token
I/O state machine
I/O cancellation
deadline handling
timer operations
readiness/completion adaptation
registered buffers
scatter/gather
batch submission
completion batching
I/O polling
I/O tracing
I/O simulation
```

### AXTASK owns

```text
task
future
promise
await
task scheduler
structured concurrency
task cancellation hierarchy
```

### AXMEMORY owns

```text
buffer
memory region
mapping
pinning
DMA memory
ownership
```

### AXNETWORK owns

```text
socket
TCP
UDP
QUIC
network protocol
connection semantics
```

### AXSTORAGE owns

```text
file
filesystem
storage object
persistent storage semantics
```

AXASYNC chỉ cung cấp **execution/completion mechanism**.

---

# 749.2 — Fundamental Model

Mọi asynchronous operation được biểu diễn:

```text
SUBMIT
   ↓
IN_FLIGHT
   ↓
COMPLETION
```

hoặc:

```text
SUBMIT
   ↓
REJECTED
```

và:

```text
IN_FLIGHT
   ↓
CANCEL_REQUESTED
   ↓
COMPLETED/CANCELLED
```

---

# 749.3 — Operation Identity

```axiom
async_op_id
```

là opaque generation-safe identifier.

Không dùng raw pointer làm operation identity.

---

# 749.4 — Operation Lifecycle

```text
CREATED
  ↓
SUBMITTED
  ↓
IN_FLIGHT
  ↓
COMPLETING
  ↓
COMPLETED
```

Exceptional:

```text
REJECTED
CANCEL_REQUESTED
CANCELLED
FAILED
EXPIRED
ABANDONED
```

---

# 749.5 — Exactly One Completion

Một operation hợp lệ chỉ được publish **một terminal completion**.

Đây là invariant cực kỳ quan trọng.

```text
complete()
complete()
```

lần thứ hai phải bị runtime/debug layer phát hiện.

---

# 749.6 — Completion Record

Canonical structure:

```axiom
async_completion {
    op_id
    status
    bytes
    result
    error
    timestamp
    flags
}
```

---

# 749.7 — Completion Status

```text
SUCCESS
PARTIAL
FAILED
CANCELLED
EXPIRED
PEER_CLOSED
END_OF_STREAM
```

---

# 749.8 — Submission Record

```axiom
async_submission {
    op_id
    operation
    resource
    buffer
    offset
    length
    deadline
    cancellation_token
    completion_target
}
```

---

# 749.9 — Completion Token

Mỗi operation có thể gắn:

```axiom
completion_token
```

Token liên kết completion với:

```text
future
task
callback
channel
user-defined waiter
```

---

# 749.10 — Future Integration

Canonical:

```axiom
let result = await async.read(file, buffer)
```

Compiler/runtime:

```text
submit I/O
      ↓
future
      ↓
task suspend
      ↓
completion
      ↓
task wake
```

---

# 749.11 — No Worker Blocking

Async backend không được biến:

```axiom
await async.read(...)
```

thành:

```text
worker thread
  ↓
blocking read
```

trừ khi backend explicit dùng blocking compatibility mode.

---

# 749.12 — Blocking Compatibility

Một resource không hỗ trợ native asynchronous operation có thể chạy trên:

```text
AXTASK blocking executor
```

nhưng phải được đánh dấu:

```text
ASYNC_EMULATED
```

để tooling biết.

---

# 749.13 — Native Completion

Nếu OS cung cấp completion primitive:

```text
Windows → IOCP
Linux   → io_uring / readiness backend
Apple   → kqueue / native async APIs
```

AXASYNC ưu tiên native mechanism.

---

# 749.14 — Readiness vs Completion

Hai model khác nhau:

```text
READINESS
→ resource có thể thực hiện I/O

COMPLETION
→ I/O đã hoàn thành
```

AXASYNC phải abstract cả hai.

---

# 749.15 — Readiness Adapter

Ví dụ:

```text
socket readable
      ↓
AXASYNC wake operation
      ↓
read
```

---

# 749.16 — Completion Adapter

Ví dụ:

```text
read submitted
      ↓
OS completes
      ↓
AXASYNC completion
```

---

# 749.17 — Backend Capability

Mỗi backend expose:

```axiom
async_backend_capabilities {
    completion
    readiness
    cancellation
    timers
    registered_buffers
    zero_copy
    vectored_io
    batching
}
```

---

# 749.18 — Capability Discovery

Application có thể query:

```axiom
async.backend_capabilities()
```

để tối ưu runtime behavior.

---

# 749.19 — Backend Selection

Runtime chọn backend:

```text
native completion
    >
native readiness
    >
optimized compatibility
    >
blocking fallback
```

theo operation capability.

---

# 749.20 — No Semantic Drift

Backend khác nhau không được thay đổi semantic contract của Axiom API.

Chỉ performance/capability details có thể khác.

---

# 749.21 — Async Context

Mỗi async executor có:

```axiom
async_context
```

bao gồm:

```text
submission queue
completion queue
timer subsystem
backend state
worker integration
```

---

# 749.22 — Context Ownership

Một process có thể có:

```text
one default async context
```

và nhiều custom contexts.

---

# 749.23 — Completion Queue

Completion queue chứa:

```text
completed operations
```

đợi dispatcher xử lý.

---

# 749.24 — Completion Batching

Dispatcher nên lấy:

```text
N completions
```

một lần thay vì syscall cho từng completion.

---

# 749.25 — Batch Size

Runtime có dynamic batch policy:

```text
low latency
balanced
high throughput
```

---

# 749.26 — Poll

```axiom
async.poll()
```

xử lý completions hiện có mà không block.

---

# 749.27 — Poll Timeout

```axiom
async.poll(timeout)
```

cho phép:

```text
0
→ non-blocking

duration
→ wait

infinite
→ wait indefinitely
```

---

# 749.28 — Event Loop

```axiom
async.run()
```

có thể thực hiện:

```text
poll completion
 ↓
dispatch
 ↓
wake tasks
 ↓
submit new operations
 ↓
repeat
```

---

# 749.29 — AXTASK Integration

Thông thường application không trực tiếp chạy event loop.

```text
AXTASK executor
       │
       └── AXASYNC context
```

Executor tích hợp completion dispatch.

---

# 749.30 — Shared Event Loop

Nhiều tasks có thể share một async context.

---

# 749.31 — Dedicated Context

High-performance subsystem có thể dùng context riêng:

```text
network
storage
media
device
```

để isolate contention.

---

# 749.32 — Submission Queue

Fast path:

```text
task
 ↓
submit
 ↓
lock-free/local queue
```

nếu backend hỗ trợ.

---

# 749.33 — Thread-Local Submission

Worker có thể submit vào local queue trước khi flush sang OS/backend.

---

# 749.34 — Syscall Batching

Nhiều operations:

```text
A
B
C
D
```

có thể submit một batch.

---

# 749.35 — Batch Submission API

```axiom
async.submit_batch(operations)
```

---

# 749.36 — Batch Completion

```axiom
async.poll_batch(buffer)
```

trả nhiều completion records.

---

# 749.37 — Small I/O Optimization

I/O nhỏ nên tránh allocation:

```text
stack/local descriptor
inline operation record
preallocated completion entry
```

---

# 749.38 — Inline Operation

Nếu operation hoàn thành ngay:

```text
submit
 ↓
immediate completion
```

runtime có thể trả kết quả trực tiếp.

Không bắt buộc enqueue completion.

---

# 749.39 — Immediate Completion Fast Path

```text
if operation completes synchronously:
    return result
else:
    register continuation
```

---

# 749.40 — Future Allocation Elision

Compiler có thể eliminate future allocation nếu:

```text
operation known synchronous
```

hoặc await được optimized.

---

# 749.41 — Buffer Model

AXASYNC không sở hữu allocator.

Buffer đến từ:

```text
AXMEMORY
```

---

# 749.42 — Buffer Descriptor

```axiom
async_buffer {
    memory_handle
    offset
    length
    flags
}
```

---

# 749.43 — No Raw Cross-Process Pointer

Operation descriptor không được chứa raw pointer làm persistent cross-process identity.

---

# 749.44 — Stable Buffer

I/O asynchronous yêu cầu buffer không bị giải phóng trước completion.

Runtime phải validate lifetime contract.

---

# 749.45 — Buffer Pinning

Nếu OS/device yêu cầu:

```text
AXMEMORY.pin(buffer)
```

trước submission.

---

# 749.46 — Registered Buffer

High-throughput context có thể:

```axiom
async.register_buffer(buffer)
```

để backend giữ registration.

---

# 749.47 — Registered Buffer Lifetime

Buffer không được release/unmap khi registration còn active.

---

# 749.48 — Deregistration

```axiom
async.unregister_buffer(buffer)
```

chỉ thành công khi không còn operation sử dụng registration.

---

# 749.49 — Scatter/Gather

Native API:

```axiom
async.readv(...)
async.writev(...)
```

---

# 749.50 — Vector Descriptor

```axiom
io_vector {
    buffer
    offset
    length
}
```

---

# 749.51 — Vector Count

Runtime phải kiểm tra backend maximum vector count.

---

# 749.52 — Large I/O

Large operations có thể:

```text
chunk
submit batches
pipeline
```

nhưng semantic result phải giữ nguyên.

---

# 749.53 — Zero-Copy

Nếu backend hỗ trợ:

```text
buffer
 ↓
device/kernel
```

không copy qua intermediate user buffer.

---

# 749.54 — Zero-Copy Constraint

Zero-copy là optimization/capability.

Không phải mọi backend đều đảm bảo zero-copy.

---

# 749.55 — DMA

Device I/O có thể dùng:

```text
AXMEMORY DMA region
```

với explicit device ownership.

---

# 749.56 — DMA Completion

```text
submit DMA
 ↓
device
 ↓
completion
 ↓
memory ownership returns
```

---

# 749.57 — Memory Visibility

DMA completion phải establish required memory visibility before application consumes buffer.

---

# 749.58 — Cache Coherency

Backend phải thực hiện required cache synchronization trên non-coherent architectures.

---

# 749.59 — File Read

Canonical:

```axiom
let n = await async.read(
    file,
    buffer
)
```

---

# 749.60 — File Write

```axiom
let n = await async.write(
    file,
    buffer
)
```

---

# 749.61 — File Offset

Operation có explicit offset:

```axiom
async.read_at(file, offset, buffer)
```

để tránh implicit shared file-position races.

---

# 749.62 — Sequential File Stream

Higher-level stream API có thể giữ logical cursor.

AXASYNC primitive vẫn nên hỗ trợ explicit offset.

---

# 749.63 — Flush

```axiom
await async.flush(file)
```

phải distinguish:

```text
application buffer flush
OS cache flush
durable storage flush
```

AXSTORAGE định nghĩa durability semantics.

---

# 749.64 — Network Read

```axiom
await async.recv(socket, buffer)
```

---

# 749.65 — Network Write

```axiom
await async.send(socket, buffer)
```

---

# 749.66 — Partial I/O

Completion có thể:

```text
SUCCESS + bytes < requested
```

Không tự động giả định full transfer.

---

# 749.67 — Stream EOF

```text
END_OF_STREAM
```

là normal terminal condition, không nhất thiết error.

---

# 749.68 — IPC Integration

AXIPC có thể submit:

```text
send
receive
```

thông qua AXASYNC.

---

# 749.69 — IPC Completion

```text
IPC operation
 ↓
AXASYNC
 ↓
AXIPC completion
 ↓
AXTASK wake
```

---

# 749.70 — Timer

AXASYNC cung cấp timer primitive:

```axiom
async.sleep(duration)
async.sleep_until(deadline)
```

---

# 749.71 — Timer Is Async

```axiom
await async.sleep(1s)
```

không block worker thread.

---

# 749.72 — Timer Wheel

High timer-count runtime có thể dùng:

```text
hierarchical timer wheel
```

thay vì heap cho mọi timer.

---

# 749.73 — Timer Heap

Low-volume contexts có thể dùng min-heap:

```text
O(log N)
```

---

# 749.74 — Timer Cancellation

Cancelled timer phải được removed/lazily invalidated safely.

---

# 749.75 — Periodic Timer

```axiom
async.interval(period)
```

phải có explicit drift policy.

---

# 749.76 — Timer Drift

Policies:

```text
FIXED_DELAY
FIXED_RATE
DEADLINE_ALIGNED
```

---

# 749.77 — Timer Coalescing

Background timers có thể coalesce để giảm wakeups.

---

# 749.78 — High-Resolution Timer

Realtime/high precision contexts có thể request high-resolution timer.

OS/backend quyết định achievable precision.

---

# 749.79 — Deadline

Canonical internal representation:

```axiom
monotonic_deadline
```

---

# 749.80 — Monotonic Clock

Timeout/deadline không sử dụng wall-clock để tránh clock adjustment.

---

# 749.81 — Deadline Propagation

```text
AXTASK
 ↓
AXASYNC
 ↓
AXIPC/AXNETWORK
```

có thể truyền cùng deadline.

---

# 749.82 — Expired Before Submit

Nếu deadline đã expired:

```text
operation
 ↓
EXPIRED
```

không cần submit tới OS.

---

# 749.83 — Cancellation

```axiom
async.cancel(op)
```

gửi cancellation request.

---

# 749.84 — Cancellation Guarantee

Cancellation không luôn đảm bảo operation đã dừng ngay lập tức.

Backend phải report:

```text
CANCELLED
```

chỉ khi completion semantics xác nhận.

---

# 749.85 — Cancel Race

Nếu completion thắng cancellation:

```text
COMPLETED
```

được giữ nguyên.

---

# 749.86 — Cancellation Token

Operation có thể nhận:

```axiom
cancel_token
```

---

# 749.87 — Token Cancellation

```text
token cancelled
      ↓
AXASYNC cancel operation
```

nếu operation hỗ trợ cancellation.

---

# 749.88 — Non-Cancellable Operation

Backend phải report:

```text
CANCELLATION_UNSUPPORTED
```

thay vì giả vờ operation đã cancelled.

---

# 749.89 — Abortable Operation

Một số operations có:

```text
hard abort
```

nhưng phải explicit backend capability.

---

# 749.90 — Close-As-Cancel

Đóng resource có thể implicitly cancel pending operations tùy resource contract.

Completion phải xác định rõ:

```text
PEER_CLOSED
CANCELLED
FAILED
```

---

# 749.91 — Completion Ordering

Một async context không mặc định cung cấp global ordering.

---

# 749.92 — Per-Resource Ordering

Resource API có thể yêu cầu:

```text
operation A
→ operation B
```

ordering.

Runtime phải preserve nếu contract yêu cầu.

---

# 749.93 — Independent Operations

Operations trên resources độc lập có thể complete bất kỳ thứ tự nào.

---

# 749.94 — Sequence Number

Operation có:

```axiom
sequence_id
```

khi caller cần reconstruct ordering.

---

# 749.95 — Readiness Re-arm

Readiness backend phải re-arm event đúng semantics để tránh:

```text
lost wakeup
```

---

# 749.96 — Edge vs Level Trigger

Backend adapter phải support:

```text
EDGE
LEVEL
```

nhưng expose unified logical readiness semantics.

---

# 749.97 — Spurious Wakeup

Caller không được assume mỗi wakeup đồng nghĩa I/O completion.

Phải re-check operation state.

---

# 749.98 — Completion Dispatch

```text
OS completion
 ↓
backend decoder
 ↓
AXASYNC completion
 ↓
completion token
 ↓
AXTASK future
 ↓
task ready
```

---

# 749.99 — No User Callback on Kernel Thread

Runtime không nên trực tiếp chạy arbitrary user callback trên privileged/kernel completion context.

---

# 749.100 — Callback Dispatch

Callback chạy trên:

```text
AXTASK worker
```

hoặc explicit executor.

---

# 749.101 — Completion Affinity

Caller có thể yêu cầu:

```axiom
completion_executor
```

---

# 749.102 — Completion Priority

Completion task có thể inherit priority/deadline từ initiating task.

---

# 749.103 — Priority Propagation

Propagation không được bypass AXCOMPUTE policy.

---

# 749.104 — Async Context Affinity

Context có thể bind worker group để giảm cache contention.

---

# 749.105 — Per-Core Context

High-throughput networking có thể:

```text
core 0 → context 0
core 1 → context 1
...
```

---

# 749.106 — NUMA Context

```text
NUMA node
 ├── async context
 ├── worker group
 └── memory pool
```

---

# 749.107 — Cross-NUMA I/O

Runtime không được copy dữ liệu chỉ vì NUMA mismatch nếu zero-copy transfer vẫn khả thi.

---

# 749.108 — Queue Locality

Completion queue nên nằm gần worker processing queue.

---

# 749.109 — False Sharing

Hot queue counters phải được cacheline-separated khi cần.

---

# 749.110 — Lock-Free Fast Path

Nếu backend topology cho phép:

```text
submit
complete
wake
```

có thể sử dụng lock-free structures.

---

# 749.111 — No Lock-Free Requirement

Lock-free không phải semantic requirement.

Correct minimal-lock implementation được phép.

---

# 749.112 — Memory Allocation

Hot async path không nên:

```text
malloc
free
```

cho mỗi operation nếu operation pool có thể tránh.

---

# 749.113 — Operation Pool

```axiom
async.create_op_pool(capacity)
```

---

# 749.114 — Pool Exhaustion

Policy:

```text
BLOCK
FAIL
GROW
BACKPRESSURE
```

---

# 749.115 — Bounded Async Context

Production systems có thể giới hạn:

```text
max_inflight
max_pending
max_registered_buffers
```

---

# 749.116 — Backpressure

Nếu pending queue đầy:

```text
REJECT
WAIT
DROP
THROTTLE
```

---

# 749.117 — Backpressure Integration

AXASYNC backpressure phải tương thích:

```text
AXIPC
AXNETWORK
AXSTORAGE
```

nhưng không sở hữu protocol-specific policies.

---

# 749.118 — In-Flight Limit

Ví dụ:

```text
max 4096 outstanding operations
```

giúp bounded memory.

---

# 749.119 — Completion Queue Overflow

Completion queue phải có deterministic policy.

Không silently discard completion.

---

# 749.120 — Completion Overflow Policies

```text
BLOCK_PRODUCER
EXPAND
EMERGENCY_QUEUE
FAIL_CONTEXT
```

---

# 749.121 — Emergency Completion Storage

Runtime có thể reserve small emergency pool để tránh mất completion khi normal allocator exhausted.

---

# 749.122 — Resource Shutdown

Khi context shutdown:

```text
STOP_SUBMIT
CANCEL/FINISH
DRAIN_COMPLETIONS
RELEASE_BACKEND
```

---

# 749.123 — Outstanding Operation Shutdown

Không được free operation state khi OS/backend vẫn có thể callback completion.

---

# 749.124 — Generation Safety

Operation reuse phải dùng:

```text
op_id + generation
```

để stale completion không complete operation mới.

---

# 749.125 — Late Completion

Backend có thể trả completion sau cancellation.

Runtime phải map đúng operation generation và ignore stale state safely.

---

# 749.126 — Resource Close Race

Nếu resource bị đóng trong khi operation pending:

```text
operation
resource
lifetime
```

phải có explicit ownership relation.

---

# 749.127 — Resource Reference

Async operation giữ logical reference tới resource cho đến terminal completion.

---

# 749.128 — Resource Lifetime

```text
resource close request
 ↓
pending operations
 ↓
drain/cancel according to contract
 ↓
final release
```

---

# 749.129 — File Descriptor Handle

AXASYNC không coi raw OS FD/handle là stable Axiom identity.

AXPROCESS/AXSTORAGE/AXNETWORK handle layers sở hữu abstraction.

---

# 749.130 — Handle Duplication

Nếu operation cần transfer resource capability:

```text
AXSECURITY + AXPROCESS
```

quản lý rights.

---

# 749.131 — Security

Async operation phải validate:

```text
resource capability
operation permission
buffer access
device permission
sandbox policy
```

---

# 749.132 — Capability Non-Amplification

Submitting an operation không được tạo thêm authority.

---

# 749.133 — Protected Resources

AXASYNC không bypass sandbox để submit I/O vào protected resource.

---

# 749.134 — Buffer Security

Runtime phải prevent async operation đọc/ghi memory region không còn authorized.

---

# 749.135 — Sensitive Buffer

Security-sensitive applications có thể request:

```axiom
secure_buffer
```

với AXMEMORY.

---

# 749.136 — Zeroization

Sau operation:

```axiom
async.secure_release(buffer)
```

có thể delegate zeroization cho AXMEMORY.

---

# 749.137 — Device Security

Device I/O phải qua AXSECURITY device capability.

---

# 749.138 — AI Boundary

AI có thể:

```text
analyze I/O latency
suggest batch size
suggest buffer size
identify queue saturation
detect blocking fallback
analyze completion ordering
suggest NUMA placement
```

Không được:

```text
bypass device permission
read protected buffers
submit unauthorized I/O
disable sandbox
modify security capability
```

---

# 749.139 — Async Tracing

Trace event:

```axiom
async_trace_event {
    timestamp
    op_id
    resource_id
    operation
    submit_time
    complete_time
    bytes
    status
    queue_wait
}
```

---

# 749.140 — Latency Breakdown

Runtime nên đo:

```text
submit latency
queue latency
kernel/device latency
completion dispatch latency
task wake latency
user continuation latency
```

---

# 749.141 — Throughput Metrics

```text
operations/sec
bytes/sec
inflight
queue_depth
completion_batch
syscalls
copies
```

---

# 749.142 — Copy Metrics

Runtime diagnostic:

```text
user→kernel copies
kernel→user copies
buffer copies
device copies
```

nếu backend có thể đo.

---

# 749.143 — Syscall Metrics

Đo:

```text
submit syscall count
completion syscall count
poll count
wakeups
```

để tối ưu batching.

---

# 749.144 — Async Flame Graph Metadata

Trace có thể associate:

```text
task
operation
resource
continuation
```

để profiler dựng causal graph.

---

# 749.145 — Causal Chain

```text
HTTP request
 ↓
network recv
 ↓
IPC
 ↓
database read
 ↓
file read
 ↓
response send
```

AXASYNC tracing phải có correlation IDs để liên kết chuỗi.

---

# 749.146 — Distributed Correlation

Nếu AXNETWORK/AXIPC cung cấp correlation ID:

```text
async operation
```

giữ nguyên ID.

---

# 749.147 — Deterministic Simulation

AXASYNC simulator phải có thể mô phỏng:

```text
latency
completion order
partial I/O
failure
timeout
cancellation
queue saturation
resource exhaustion
```

---

# 749.148 — Fault Injection

API:

```axiom
async_sim.inject_fault(
    operation,
    fault
)
```

fault:

```text
ERROR
TIMEOUT
PARTIAL
CANCEL
PEER_CLOSE
RESOURCE_EXHAUSTED
```

---

# 749.149 — Replay

Trace replay có thể tái tạo:

```text
submit
completion
ordering
latency model
```

để test application.

---

# 749.150 — Replay Does Not Simulate Hardware Exactly

Replay đảm bảo:

```text
logical I/O sequence
```

không đảm bảo:

```text
exact CPU/device timing
```

---

# 749.151 — Virtual Clock

Simulator dùng:

```text
virtual monotonic clock
```

để test timeout/timer deterministic.

---

# 749.152 — Virtual Device

Simulation backend có thể expose:

```text
virtual file
virtual socket
virtual device
```

---

# 749.153 — Async Unit Testing

Có thể:

```axiom
with async_test_context {
    ...
}
```

với deterministic completions.

---

# 749.154 — Manual Completion

Test backend:

```axiom
op.complete_success(...)
```

để kiểm thử state machines.

Chỉ simulation/test capability mới được phép dùng.

---

# 749.155 — Async Race Testing

Scheduler simulator có thể randomize:

```text
completion order
task wake order
cancellation timing
```

để phát hiện race.

---

# 749.156 — Race Reproduction

Mỗi simulation run phải lưu:

```text
seed
event sequence
backend configuration
```

để reproduce.

---

# 749.157 — Realtime Mode

Realtime async context yêu cầu:

```text
bounded allocation
bounded queue
bounded wake latency
no unexpected blocking
```

---

# 749.158 — Realtime Allocation

Realtime context không được tự động grow heap.

---

# 749.159 — Realtime Completion

Completion storage phải preallocated.

---

# 749.160 — Realtime Timer

High-priority timer không được bị background timer coalescing nếu policy cấm.

---

# 749.161 — Background Mode

Background context được phép:

```text
timer coalescing
batching
deferred wake
```

để tiết kiệm năng lượng.

---

# 749.162 — Power Policy

AXASYNC có:

```text
LATENCY_FIRST
BALANCED
POWER_SAVING
```

nhưng AXCOMPUTE/OS vẫn có quyền áp dụng global policy.

---

# 749.163 — Mobile Policy

Android/iOS backend phải respect:

```text
background execution limits
suspension
power constraints
```

---

# 749.164 — WASM

WASM backend không giả định có direct OS I/O.

Async operation có thể delegate tới host:

```text
WASM
 ↓
host async API
 ↓
completion
 ↓
WASM resume
```

---

# 749.165 — Embedded

Embedded backend có thể dùng:

```text
interrupt
DMA
ring buffer
polling
```

---

# 749.166 — Interrupt Boundary

Interrupt handler không chạy arbitrary Axiom task code.

Interrupt:

```text
capture minimal event
 ↓
queue completion
 ↓
normal execution context
```

---

# 749.167 — Device Event

Device completion:

```text
interrupt/DMA
 ↓
kernel/backend
 ↓
AXASYNC completion
 ↓
task
```

---

# 749.168 — Polling Backend

Low-latency devices có thể dùng busy polling.

Policy phải explicit.

---

# 749.169 — Hybrid Polling

```text
short spin
 ↓
poll
 ↓
park
```

giảm latency mà không giữ CPU vô hạn.

---

# 749.170 — Adaptive Polling

Runtime có thể điều chỉnh polling dựa trên:

```text
completion rate
latency target
CPU budget
power mode
```

---

# 749.171 — Async Resource Limits

Context phải expose:

```axiom
async_limits {
    max_inflight
    max_queue
    max_buffers
    max_registered_buffers
}
```

---

# 749.172 — Quota Integration

AXCOMPUTE/AXAPPLICATION có thể đặt quota.

AXASYNC phải enforce quota tại submission boundary.

---

# 749.173 — Quota Exhaustion

```text
RESOURCE_EXHAUSTED
```

là explicit error.

Không silently fallback sang unlimited allocation.

---

# 749.174 — Error Model

AXASYNC error gồm:

```text
domain
code
operation
resource
platform_code
```

---

# 749.175 — Platform Error

Windows/Linux/macOS native error code có thể được giữ trong diagnostic metadata.

---

# 749.176 — Portable Error

Application logic nên dùng Axiom portable error codes:

```text
TIMEOUT
CANCELLED
PERMISSION_DENIED
NOT_FOUND
WOULD_BLOCK
RESOURCE_EXHAUSTED
PEER_CLOSED
UNSUPPORTED
```

---

# 749.177 — Partial Success

Partial I/O không được biến thành generic failure.

Ví dụ:

```text
requested = 4096
completed = 2048
status = PARTIAL
```

---

# 749.178 — Retry Semantics

AXASYNC không tự retry I/O.

Retry thuộc caller/protocol layer.

---

# 749.179 — Idempotency

Async runtime không assume operation idempotent.

---

# 749.180 — Transactional I/O

Transaction semantics thuộc AXSTORAGE/AXDATABASE.

AXASYNC chỉ transport execution/completion.

---

# 749.181 — Durable Completion

`write completed` không mặc định có nghĩa:

```text
physically durable
```

Durability contract thuộc AXSTORAGE.

---

# 749.182 — Async File Ordering

AXSTORAGE xác định ordering requirements giữa:

```text
write
flush
rename
metadata update
```

AXASYNC thực thi operations theo contract.

---

# 749.183 — Async Network Ordering

AXNETWORK xác định stream ordering.

AXASYNC chỉ báo completion.

---

# 749.184 — Async IPC Ordering

AXIPC xác định message ordering.

AXASYNC không thay đổi semantics đó.

---

# 749.185 — Operation Composition

Higher-level API có thể:

```axiom
await all(
    async.read(...),
    async.read(...),
    async.read(...)
)
```

AXTASK thực hiện composition.

---

# 749.186 — Parallel I/O

Multiple independent operations có thể submit trước khi await:

```axiom
let a = async.read(...)
let b = async.read(...)
let c = async.read(...)

await a
await b
await c
```

---

# 749.187 — Submission Before Await

Compiler/runtime không được tự động serialize independent async operations chỉ vì syntax await xuất hiện sau submission.

---

# 749.188 — Pipeline

```text
read A
 ↓
process A
 ↓
write A

read B
 ↓
process B
 ↓
write B
```

có thể pipeline bằng AXTASK + AXASYNC.

---

# 749.189 — Double Buffering

Streaming workload có thể dùng:

```text
buffer A → I/O
buffer B → processing
```

để overlap computation và I/O.

---

# 749.190 — Ring Buffer

High-throughput I/O có thể sử dụng AXMEMORY ring buffer.

---

# 749.191 — Completion Ring

Backend có thể expose completion ring nếu native platform hỗ trợ.

---

# 749.192 — Shared Completion Ring

Process-local shared ring:

```text
producer
   ↓
ring
   ↓
consumer
```

không yêu cầu kernel transition cho từng operation nếu backend architecture cho phép.

---

# 749.193 — Cross-Process Async

AXIPC có thể kết hợp:

```text
shared ring
+
AXASYNC notification
```

để tạo high-throughput IPC.

---

# 749.194 — Notification Coalescing

Nhiều completions có thể chỉ cần một wakeup.

---

# 749.195 — Lost Wake Prevention

Nếu queue chuyển:

```text
EMPTY → NON_EMPTY
```

phải đảm bảo một waiter được wake.

---

# 749.196 — Empty Check Race

Dispatcher phải re-check queue sau khi wake và trước khi park.

---

# 749.197 — Shutdown Race

Shutdown phải synchronize:

```text
submit
completion
cancel
close
```

để không xảy ra use-after-free backend state.

---

# 749.198 — Native API

```axiom
create_async_context()
destroy_async_context()

get_backend()
get_backend_capabilities()

submit()
submit_batch()

poll()
poll_batch()

wait()
wake()

cancel()
cancel_all()

create_operation()
destroy_operation()

create_completion_token()
bind_completion_token()

register_buffer()
unregister_buffer()

read()
read_at()
readv()

write()
write_at()
writev()

flush()

recv()
send()
recv_from()
send_to()

accept()
connect()

timer()
sleep()
sleep_until()
interval()

create_io_ring()
submit_ring()
poll_ring()

set_limits()
get_limits()

get_stats()

start_trace()
stop_trace()

replay_trace()

create_simulation()
inject_fault()

shutdown()
drain()
```

---

# 749.199 — High-Level Convenience API

Axiom standard library có thể cung cấp:

```axiom
await file.read(...)
await file.write(...)
await socket.recv(...)
await socket.send(...)
await ipc.receive(...)
await timer.sleep(...)
```

nhưng các API này lower xuống AXASYNC primitives.

---

# 749.200 — Compiler Intrinsics

Compiler/runtime ABI:

```axiom
__ax_async_submit
__ax_async_await
__ax_async_suspend
__ax_async_resume
__ax_async_cancel
__ax_async_poll
__ax_async_complete
```

Các intrinsic này không nhất thiết public language API.

---

# 749.201 — ABI Completion

ABI phải truyền tối thiểu:

```text
operation id
result/status
bytes
error
completion token
```

---

# 749.202 — FFI

Foreign async API có thể wrap thành:

```axiom
future<T>
```

nhưng phải khai báo:

```text
completion ownership
callback lifetime
thread affinity
cancellation support
```

---

# 749.203 — C Callback Bridge

Legacy C API:

```text
start(op, callback)
```

có thể được adapter:

```text
callback
 ↓
AXASYNC completion
 ↓
future
```

---

# 749.204 — Callback Lifetime

Runtime phải giữ callback context alive cho đến callback completion hoặc cancellation guarantee.

---

# 749.205 — Native Artifact Independence

AXASYNC runtime core không được yêu cầu:

```text
third-party async runtime
```

Axiom compiler/runtime tự sở hữu backend adapters.

---

# 749.206 — Platform Backend Isolation

Source tree:

```text
runtime/async/
    core/
    windows/
    linux/
    macos/
    ios/
    android/
    wasm/
    embedded/
```

---

# 749.207 — Portable Core

Portable core chỉ biết:

```text
operation
completion
context
buffer
deadline
cancellation
```

---

# 749.208 — Windows Backend

Windows backend ưu tiên:

```text
IOCP
overlapped I/O
native async handles
```

---

# 749.209 — Linux Backend

Linux backend có thể chọn:

```text
io_uring
epoll
native async facilities
```

dựa trên operation/backend capability.

---

# 749.210 — Apple Backend

macOS/iOS backend có thể sử dụng:

```text
kqueue
Grand Central Dispatch integration where necessary
native asynchronous APIs
```

nhưng AXASYNC semantic layer vẫn thuộc Axiom.

---

# 749.211 — Android Backend

Android native layer phải bridge:

```text
native file/network/device events
```

với platform lifecycle.

---

# 749.212 — WASM Backend

WASM host cung cấp:

```text
promise/event callback
```

hoặc equivalent host completion mechanism.

---

# 749.213 — Performance Target

AXASYNC hot path mục tiêu:

```text
small I/O
→ minimal allocation
→ minimal synchronization
→ minimal kernel transitions
→ direct task wake
```

---

# 749.214 — Fast Path Architecture

```text
Task
 ↓
local operation pool
 ↓
local submission queue
 ↓
batched backend submit
 ↓
completion batch
 ↓
direct future completion
 ↓
task ready
```

---

# 749.215 — Slow Path

Chỉ khi cần:

```text
allocation
backend setup
buffer registration
cross-thread handoff
kernel resource creation
```

mới đi slow path.

---

# 749.216 — Cache Locality

Hot fields:

```text
op_id
state
token
buffer
deadline
```

nên nằm gần nhau.

Cold diagnostic metadata tách khỏi hot structure.

---

# 749.217 — False Sharing Avoidance

Worker-local counters không được share cacheline nếu gây contention đáng kể.

---

# 749.218 — Batch Completion Optimization

Completion processing:

```text
decode all
mark futures ready
wake tasks
```

có thể defer scheduler transition tới cuối batch.

---

# 749.219 — Wake Coalescing

Nếu 100 completions đánh thức cùng executor:

```text
100 completions
→ bounded number of worker wakeups
```

---

# 749.220 — Completion Ordering Optimization

Runtime được phép reorder internal dispatch của independent operations nếu không vi phạm API ordering contract.

---

# 749.221 — Power Optimization

Idle async context nên:

```text
park
```

thay vì busy spin vô hạn.

---

# 749.222 — Adaptive Runtime

Runtime có thể chuyển:

```text
busy poll
→ hybrid
→ parked
```

dựa trên latency/CPU policy.

---

# 749.223 — Diagnostics

Compiler warning:

```text
async buffer lifetime may end before completion
blocking operation inside async task
unsupported cancellation
unbounded async queue
oversized operation frame
```

---

# 749.224 — Static Analysis

Compiler có thể detect:

```text
await while holding incompatible lock
resource closed before awaited operation
future ignored
cancel token unreachable
```

---

# 749.225 — Unused Future

Có thể cảnh báo:

```axiom
async.write(file, buffer)
```

nếu future/result bị bỏ qua và API contract yêu cầu observation.

---

# 749.226 — Fire-and-Forget I/O

Nếu thực sự muốn:

```axiom
async.write_detached(...)
```

phải có explicit error reporting/supervision policy.

---

# 749.227 — Error Observation

Detached async operation không được silently lose failure.

---

# 749.228 — Resource Exhaustion Recovery

Application có thể:

```text
wait for completion
reduce concurrency
retry submission
```

thay vì runtime tự tăng resource vô hạn.

---

# 749.229 — Async Admission Control

Context có thể enforce:

```text
max concurrent reads
max concurrent writes
max socket operations
```

---

# 749.230 — Fairness

Một producer không được chiếm toàn bộ submission capacity nếu fairness policy được bật.

---

# 749.231 — Priority Queues

Optional priority submission:

```text
HIGH
NORMAL
BACKGROUND
```

---

# 749.232 — Deadline-Aware Queue

Operation gần deadline có thể được dispatch trước nếu policy cho phép.

---

# 749.233 — No Deadline Guarantee

Deadline scheduling không đảm bảo operation sẽ hoàn thành trước deadline.

Nó chỉ là scheduling/timeout contract.

---

# 749.234 — Deadline Expiration

Completion phải phân biệt:

```text
operation failed naturally
```

với:

```text
deadline expired
```

---

# 749.235 — Cancellation + Deadline

Nếu cả hai xảy ra:

```text
first terminal condition
```

theo deterministic precedence rules.

---

# 749.236 — Canonical Precedence

Nếu backend xác nhận completion trước expiration/cancellation:

```text
SUCCESS/PARTIAL/FAILED
```

được giữ.

Nếu deadline/cancellation được confirmed trước completion:

```text
EXPIRED/CANCELLED
```

theo operation policy.

---

# 749.237 — Remote Async

AXNETWORK có thể map remote request:

```text
remote request
 ↓
AXASYNC future
```

nhưng remote retry/reliability thuộc network protocol.

---

# 749.238 — Remote Timeout

Local deadline có thể truyền thành remote deadline metadata.

---

# 749.239 — Remote Cancellation

Cancellation propagation chỉ được báo là effective nếu remote transport/protocol hỗ trợ.

---

# 749.240 — Definition of Done

```text
BOOTSTRAP-749
STATUS: COMPLETE / FROZEN

AXASYNC
 ├── Async Operation Model
 ├── Submission
 ├── Completion
 ├── Completion Tokens
 ├── Completion Queues
 ├── Polling
 ├── Readiness Adapter
 ├── Completion Adapter
 ├── Event Loop
 ├── AXTASK Integration
 ├── Future Integration
 ├── Cancellation
 ├── Deadlines
 ├── Timers
 ├── File I/O
 ├── Network I/O
 ├── IPC I/O
 ├── Device I/O
 ├── DMA
 ├── Zero-Copy
 ├── Registered Buffers
 ├── Scatter/Gather
 ├── Batch Submission
 ├── Batch Completion
 ├── I/O Rings
 ├── Backpressure
 ├── Resource Limits
 ├── NUMA
 ├── Per-Core Contexts
 ├── Realtime Mode
 ├── Power-Aware Mode
 ├── Security Boundary
 ├── FFI
 ├── Windows Backend
 ├── Linux Backend
 ├── macOS Backend
 ├── iOS Backend
 ├── Android Backend
 ├── WASM Backend
 ├── Embedded Backend
 ├── Tracing
 ├── Profiling
 ├── Deterministic Simulation
 ├── Fault Injection
 ├── Replay
 ├── Compiler Intrinsics
 ├── Native ABI
 ├── Native Artifact Independence
 ├── 40 Formal Invariants
 └── Async I/O Runtime 5.0
```

# 749.241 — Formal Invariants

```text
ASYNC-INV-01   Every submitted operation has a unique generation-safe identity.
ASYNC-INV-02   Every accepted operation reaches exactly one terminal completion.
ASYNC-INV-03   A stale completion cannot complete a newer recycled operation.
ASYNC-INV-04   An operation cannot be freed while the backend may still reference it.
ASYNC-INV-05   Async task waiting does not implicitly block its worker thread.
ASYNC-INV-06   Completion publication establishes required memory visibility.
ASYNC-INV-07   Completion queues cannot silently discard accepted completions.
ASYNC-INV-08   Resource lifetime remains valid for every outstanding operation.
ASYNC-INV-09   Buffer lifetime remains valid until every associated operation reaches terminal state.
ASYNC-INV-10   Registered buffers cannot be released while registration-dependent operations exist.

ASYNC-INV-11   Cancellation is not reported as effective until backend semantics establish cancellation.
ASYNC-INV-12   A completion winning a cancellation race remains authoritative.
ASYNC-INV-13   Deadline expiration cannot silently extend an operation deadline.
ASYNC-INV-14   Timeout does not imply producer cancellation unless explicitly requested.
ASYNC-INV-15   Partial I/O is distinguishable from total failure.
ASYNC-INV-16   End-of-stream is distinguishable from generic failure.
ASYNC-INV-17   Async runtime does not assume I/O operations are idempotent.
ASYNC-INV-18   Async runtime does not invent retry semantics.
ASYNC-INV-19   Async runtime does not invent storage durability semantics.
ASYNC-INV-20   Async runtime does not alter AXNETWORK or AXIPC message-ordering contracts.

ASYNC-INV-21   Backend-specific mechanisms preserve portable AXASYNC semantics.
ASYNC-INV-22   Readiness and completion mechanisms are not conflated internally.
ASYNC-INV-23   User callbacks execute only in valid Axiom execution contexts.
ASYNC-INV-24   Interrupt handlers cannot directly execute arbitrary task code.
ASYNC-INV-25   Completion dispatch cannot grant security authority.
ASYNC-INV-26   Async submission requires valid resource capability.
ASYNC-INV-27   Async buffers cannot be accessed outside their authorized memory region.
ASYNC-INV-28   Cross-process asynchronous operations never rely on raw pointers as persistent identity.
ASYNC-INV-29   Quota exhaustion is explicitly reported.
ASYNC-INV-30   Shutdown cannot free backend state before outstanding operations are safely resolved.

ASYNC-INV-31   Worker wakeups cannot lose a newly published completion.
ASYNC-INV-32   Scheduler integration cannot create duplicate task execution from one completion.
ASYNC-INV-33   Completion batching cannot violate externally visible ordering contracts.
ASYNC-INV-34   Independent operations may execute concurrently unless an explicit ordering contract forbids it.
ASYNC-INV-35   Deterministic replay reproduces the declared logical event sequence.
ASYNC-INV-36   Replay does not claim exact hardware timing equivalence.
ASYNC-INV-37   Fault injection is confined to simulation/test boundaries.
ASYNC-INV-38   AI diagnostics cannot access protected buffers or submit unauthorized operations.
ASYNC-INV-39   Realtime mode cannot silently allocate unbounded memory.
ASYNC-INV-40   The uncontended asynchronous fast path minimizes allocation, locking, kernel transitions, and unnecessary task wakeups.
```

**BOOTSTRAP-749 / AXASYNC — ARCHITECTURAL BASELINE FROZEN.**

---

# BOOTSTRAP-750 — AXABI

**Native Application Binary Interface & Cross-Module ABI Runtime — calling convention, register ABI, stack ABI, aggregate passing/return, scalar ABI, SIMD/vector ABI, variadic ABI, function pointers, closures/contexts, symbol naming, symbol visibility, type layout ABI, struct layout, enum ABI, trait/interface dispatch ABI, vtable-free method dispatch contracts, generic instantiation ABI, exception/error ABI, async/future ABI, task-frame ABI, allocator ABI, ownership-transfer ABI, FFI, C interoperability, dynamic library ABI, static library ABI, PE64, ELF, Mach-O, iOS, Android, WASM, ABI versioning, compatibility metadata, linker contracts, binary stability, hot-reload boundaries, plugin ABI, diagnostics, deterministic ABI inspection và Axiom Native ABI 5.0.**