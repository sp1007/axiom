# BOOTSTRAP-749 — AXASYNC

**Namespace:** `AXASYNC`  
**Phase:** Axiom Civilization Runtime / Native Async I/O & Completion Runtime  
**Status:** **ARCHITECTURAL BASELINE — FROZEN TARGET 5.0**

---

## 1. Mục tiêu

`AXASYNC` là tầng runtime native chịu trách nhiệm cho **asynchronous I/O thực sự**, nằm giữa các resource subsystem (`AXSTORAGE`, `AXNETWORK`, `AXIPC`, device I/O...) và `AXTASK`.

Mục tiêu chính:

- asynchronous file I/O;
- asynchronous network I/O;
- asynchronous IPC integration;
- device/DMA I/O;
- OS completion ports;
- readiness polling;
- completion queues;
- timers;
- event sources;
- cancellation;
- deadlines;
- scatter/gather;
- zero-copy;
- registered/pinned buffers;
- batching;
- syscall minimization;
- tracing;
- deterministic simulation;
- fault injection;
- native cross-platform backend.

**Nguyên tắc nền tảng:**

> `AXASYNC` không phải async language runtime. Nó là **I/O completion substrate**.

`AXTASK` quyết định **task nào đang chạy**.

`AXASYNC` quyết định **I/O nào đã sẵn sàng hoặc đã hoàn thành**.

---

# 2. Vị trí trong kiến trúc Axiom

```text
                    AXTASK
              Task / Future / Await
                       │
                       ▼
                  ┌─────────┐
                  │ AXASYNC │
                  └────┬────┘
                       │
       ┌───────────────┼────────────────┐
       ▼               ▼                ▼
   AXSTORAGE       AXNETWORK          AXIPC
       │               │                │
       └───────────────┼────────────────┘
                       ▼
                 OS / Device I/O
                       │
                       ▼
                    AXMEMORY
```

Các tầng không được nhập vai lẫn nhau.

---

# 3. Dependency

`AXASYNC` phụ thuộc:

```text
AXTASK
AXPROCESS
AXMEMORY
AXSYNC
AXNETWORK
AXSTORAGE
AXIPC
AXCOMPUTE
AXSECURITY
```

---

# 4. Boundary

## 4.1 AXASYNC sở hữu

`AXASYNC` sở hữu:

- I/O operation;
- I/O submission;
- I/O completion;
- completion token;
- completion queue;
- poller;
- readiness adapter;
- completion adapter;
- timers;
- event sources;
- batching;
- registered buffers;
- I/O cancellation;
- I/O deadline;
- zero-copy I/O;
- I/O tracing;
- deterministic I/O simulation;
- fault injection;
- OS I/O backend abstraction.

---

## 4.2 Không sở hữu

### AXTASK

Sở hữu:

- task;
- future;
- promise;
- executor;
- structured concurrency;
- task cancellation tree;
- await state machine.

### AXPROCESS

Sở hữu:

- process;
- thread;
- address space;
- OS handles;
- TLS;
- process lifecycle.

### AXSYNC

Sở hữu:

- mutex;
- semaphore;
- event;
- condition;
- atomic synchronization;
- wait/wake primitives.

### AXMEMORY

Sở hữu:

- allocation;
- virtual memory;
- buffer;
- pinning;
- DMA memory;
- memory mapping;
- lifetime.

### AXNETWORK

Sở hữu:

- TCP;
- UDP;
- QUIC;
- protocol state;
- sockets/network resources;
- network addressing.

### AXSTORAGE

Sở hữu:

- filesystem semantics;
- file metadata;
- storage namespace;
- file consistency semantics.

### AXIPC

Sở hữu:

- IPC message;
- channel;
- endpoint;
- IPC protocol;
- capability transfer.

### AXCOMPUTE

Sở hữu:

- CPU scheduling;
- compute resource allocation;
- global resource policy.

### AXSECURITY

Sở hữu:

- authorization;
- sandbox;
- capabilities;
- protected-resource policy.

---

# 5. Hai mô hình async cơ bản

Đây là quyết định kiến trúc quan trọng nhất của `AXASYNC`.

## 5.1 Readiness-based I/O

OS báo:

```text
"Resource này hiện có thể thực hiện I/O."
```

Ví dụ:

```text
READABLE
WRITABLE
ACCEPTABLE
ERROR
HANGUP
```

Sau đó application thực hiện operation.

Flow:

```text
poller
   │
   ▼
READABLE
   │
   ▼
application
   │
   ▼
read()
   │
   ▼
result
```

Readiness **không có nghĩa I/O đã hoàn thành**.

---

# 6. Completion-based I/O

OS/device thực hiện operation và trả về completion.

```text
submit(read)
      │
      ▼
   kernel
      │
      ▼
device
      │
      ▼
 completion
```

Application không cần thực hiện `read()` lần thứ hai.

Ví dụ:

```text
read_async(file, buffer, ...)
        │
        ▼
      submit
        │
        ▼
      kernel
        │
        ▼
    completion
        │
        ▼
      future
```

---

# 7. Không ép tất cả platform về một primitive

Axiom **không** định nghĩa:

> mọi hệ điều hành phải giả lập IOCP.

Hoặc:

> mọi I/O phải chạy qua io_uring.

Thay vào đó:

```text
AXASYNC API
     │
     ▼
Backend Capability Profile
     │
 ┌───┼────┬─────┬─────┐
 ▼   ▼    ▼     ▼     ▼
IOCP io_uring kqueue WASM embedded
```

Backend được phép có capability khác nhau.

---

# 8. Backend profiles

## 8.1 Windows

Ưu tiên:

```text
IOCP
Overlapped I/O
Registered I/O khi phù hợp
```

---

## 8.2 Linux

Ưu tiên:

```text
io_uring
```

Fallback:

```text
epoll
poll
```

---

## 8.3 macOS / iOS

Backend có thể sử dụng:

```text
kqueue
dispatch/event mechanisms
native async facilities
```

---

## 8.4 Android

Dựa trên Linux backend nhưng phải tôn trọng Android lifecycle và sandbox.

---

## 8.5 WASM

Không giả định có kernel syscall.

Backend:

```text
host async API
browser event loop
WASI async facilities
```

---

## 8.6 Embedded

Cho phép:

```text
interrupt
DMA completion
hardware polling
```

---

# 9. Core object model

Các primitive chính:

```text
io_context
io_operation
io_request_id
io_completion
io_source
io_handle
io_buffer
io_buffer_group
io_deadline
io_cancel_token
completion_queue
poller
timer_source
event_source
io_batch
io_profile
io_trace
```

---

# 10. `io_operation`

Đây là object trung tâm.

```text
io_operation {
    request_id
    operation_kind
    source
    handle
    buffer
    offset
    length

    deadline
    cancellation

    flags
    user_data
    task_context

    state
}
```

Không yêu cầu heap allocation bắt buộc.

Runtime phải hỗ trợ operation object nằm:

```text
task frame
stack
slab
preallocated pool
```

---

# 11. Request ID

`io_request_id` không được đơn thuần là pointer.

Mô hình:

```text
request_id {
    index
    generation
}
```

Ví dụ:

```text
index = 381
generation = 17
```

Completion cũ:

```text
381:16
```

không thể nhầm với operation mới:

```text
381:17
```

Điều này bảo vệ chống **stale completion**.

---

# 12. Operation lifecycle

Canonical lifecycle:

```text
CREATED
   │
   ▼
SUBMITTED
   │
   ▼
IN_FLIGHT
   │
   ├──────────────► COMPLETED
   │
   ├──────────────► FAILED
   │
   ├──────────────► CANCEL_REQUESTED
   │                       │
   │                       ▼
   │                   CANCELLED
   │
   └──────────────► EXPIRED
```

`CANCEL_REQUESTED` **không đồng nghĩa** `CANCELLED`.

---

# 13. Completion record

```text
io_completion {
    request_id
    status
    bytes_transferred
    native_error
    timestamp
    flags
    user_data
}
```

Axiom giữ:

```text
stable error class
+
native OS error
```

Ví dụ:

```text
status = PERMISSION_DENIED
native_error = ERROR_ACCESS_DENIED
```

---

# 14. Completion guarantee

Mặc định:

> Một operation có đúng một terminal completion.

Trừ khi operation khai báo:

```text
PARTIAL_COMPLETION
MULTI_COMPLETION
STREAM_COMPLETION
```

Điều này giúp `future<T>` không bị double-complete.

---

# 15. Completion queue

```text
completion_queue
```

phải hỗ trợ:

```text
push()
pop()
poll()
wait()
drain()
drain_batch()
```

Batch:

```text
drain_batch(max = 64)
```

cho phép giảm syscall và scheduling overhead.

---

# 16. MPSC completion

Nhiều producer có thể hoàn thành I/O:

```text
worker 0 ─┐
worker 1 ─┤
worker 2 ─┼──► completion_queue
worker 3 ─┘
```

Consumer có thể là:

```text
một worker
hoặc nhiều worker
```

Không yêu cầu completion phải quay về đúng thread submit.

---

# 17. Wake coalescing

Không đánh thức worker cho từng completion nếu không cần.

Ví dụ:

```text
completion 1
completion 2
completion 3
completion 4
      │
      ▼
  one wakeup
      │
      ▼
 drain_batch(64)
```

Đây là một optimization quan trọng.

---

# 18. Polling API

```text
poller.poll()
poller.wait()
poller.poll_until(deadline)
poller.drain_completions()
```

Semantics:

### `poll`

Không block.

### `wait`

Có thể block thread.

### `poll_until`

Block tối đa đến deadline.

---

# 19. Worker parking

Mặc định:

```text
no completion
     │
     ▼
park worker
```

Không được busy-spin vô hạn.

Low-latency profile có thể cho phép:

```text
spin
→ short pause
→ park
```

nhưng đây phải là policy explicit.

---

# 20. Integration với AXTASK

Đây là đường đi canonical:

```text
async function read_file() {
    result = await file.read(buffer)
}
```

Compiler hạ xuống:

```text
AXTASK state machine
        │
        ▼
AXASYNC submit
        │
        ▼
suspend task
        │
        ▼
I/O completion
        │
        ▼
resume task
```

Worker thread không bị block.

---

# 21. Completion → Future

Completion token phải map được trực tiếp tới:

```text
future<T>
```

mà không bắt buộc allocation mới.

Ví dụ:

```text
io_request_id
      │
      ▼
task frame
      │
      ▼
future state
```

---

# 22. File I/O

API:

```text
open_async()
read_async()
write_async()
flush_async()
sync_async()
close_async()
```

Read:

```text
read_async(
    file,
    buffer,
    offset,
    length
)
```

Result:

```text
{
    status
    bytes_read
}
```

---

# 23. Partial file I/O

Không giả định:

```text
requested = 4096
completed = 4096
```

Có thể:

```text
requested = 4096
completed = 1792
```

API phải biểu diễn chính xác:

```text
bytes_transferred = 1792
status = PARTIAL
```

---

# 24. Vectored I/O

```text
readv_async(
    file,
    [
        buffer_a,
        buffer_b,
        buffer_c
    ]
)
```

Tương tự:

```text
writev_async()
```

Compiler/runtime sử dụng typed buffer vector thay vì raw untyped pointer.

---

# 25. Scatter/Gather

Core type:

```text
io_buffer_vector
```

Mỗi entry:

```text
buffer
offset
length
```

Backend có thể map trực tiếp sang:

```text
iovec
WSABUF
scatter/gather descriptor
```

nếu ABI tương thích.

---

# 26. Direct I/O

AXASYNC hỗ trợ:

```text
DIRECT
BUFFERED
```

Nhưng semantics thuộc backend + AXSTORAGE.

Direct I/O phải khai báo:

```text
alignment
sector size
buffer constraints
offset constraints
```

Không tự động giả vờ rằng mọi platform hỗ trợ giống nhau.

---

# 27. Append semantics

`append` phải được biểu diễn bằng operation semantic rõ ràng.

Không làm:

```text
get_file_size()
write_at(size)
```

vì hai operation riêng biệt có race.

Backend phải cung cấp atomic append nếu platform hỗ trợ.

---

# 28. Network I/O

API:

```text
accept_async()
connect_async()
recv_async()
send_async()

recv_from_async()
send_to_async()
```

AXASYNC không sở hữu protocol.

Ví dụ:

```text
TCP
QUIC
UDP
```

state vẫn thuộc `AXNETWORK`.

---

# 29. Readiness socket

API:

```text
wait_readable()
wait_writable()
```

Flow:

```text
wait_readable()
      │
      ▼
READABLE
      │
      ▼
recv()
```

Đây khác hoàn toàn:

```text
recv_async()
      │
      ▼
completion
```

---

# 30. Ordering

Không mặc định rằng mọi request hoàn thành theo thứ tự submit.

Ví dụ:

```text
submit A
submit B
submit C

completion:
B
C
A
```

Được phép.

Nếu application yêu cầu ordering:

```text
ORDERED
```

phải khai báo explicit.

---

# 31. Per-stream ordering

Một stream có thể yêu cầu:

```text
A → B → C
```

Nhưng các stream độc lập:

```text
stream 1
stream 2
stream 3
```

có thể chạy song song.

Không áp dụng global ordering.

---

# 32. IPC integration

`AXASYNC` không tạo message model mới.

Nó chỉ cung cấp async transport.

```text
AXIPC endpoint
      │
      ▼
AXASYNC
      │
      ▼
completion
```

Ví dụ:

```text
await endpoint.receive_async()
```

message semantics vẫn thuộc `AXIPC`.

---

# 33. Shared-memory IPC

Với buffer lớn:

```text
AXMEMORY shared region
          │
          ▼
       AXIPC
          │
          ▼
      AXASYNC
```

Không copy payload nếu transport hỗ trợ ownership transfer.

---

# 34. Zero-copy

Mục tiêu:

```text
device
  ↓
registered buffer
  ↓
application
```

thay vì:

```text
device
  ↓
kernel buffer
  ↓
temporary buffer
  ↓
application buffer
```

Zero-copy chỉ được tuyên bố khi backend thực sự đáp ứng semantic tương ứng.

---

# 35. Registered buffer

API:

```text
register_buffer()
unregister_buffer()
```

Buffer phải thuộc `AXMEMORY`.

Lifecycle:

```text
ALLOCATED
    ↓
REGISTERED
    ↓
IN_USE
    ↓
AVAILABLE
    ↓
RELEASED
```

Không được release buffer khi operation còn `IN_FLIGHT`.

---

# 36. Buffer group

```text
io_buffer_group
```

cho phép preallocate:

```text
N × fixed-size buffers
```

Backend lấy buffer từ pool.

Ví dụ:

```text
64 × 64 KiB
```

rất phù hợp server/network workloads.

---

# 37. Buffer ownership

Một buffer có ownership state:

```text
APPLICATION
KERNEL
DEVICE
TRANSFERRED
```

Không cho phép hai owner ghi đồng thời nếu không có explicit shared semantics.

---

# 38. DMA

DMA buffer phải khai báo:

```text
PINNED
DEVICE_VISIBLE
CACHE_COHERENT
```

Nếu platform không đảm bảo cache coherence:

```text
sync_for_device()
sync_for_cpu()
```

phải được backend thực hiện rõ ràng.

---

# 39. Raw pointer boundary

Raw pointer không được xem là I/O ownership token.

Không cho phép:

```text
device → arbitrary raw pointer
```

Thay vào đó:

```text
buffer_handle
region_handle
registered_buffer
```

Raw pointer chỉ được dùng sau khi memory contract đã được xác lập.

---

# 40. Cancellation

API:

```text
cancel(request_id)
cancel_all(context)
```

Semantics:

```text
CANCEL_REQUESTED
```

sau đó backend có thể:

```text
CANCELLED
```

hoặc operation có thể hoàn thành trước khi cancellation có hiệu lực.

---

# 41. Cancellation race

Race hợp lệ:

```text
submit
 │
 ├── cancel
 │
 └── completion
```

Có thể xảy ra:

```text
cancel requested
completion arrives
```

Runtime phải chọn **một terminal completion duy nhất**.

Không được:

```text
future.complete(CANCELLED)
future.complete(SUCCESS)
```

---

# 42. Deadline

Deadline luôn dùng:

```text
monotonic clock
```

không dùng wall-clock.

Ví dụ:

```text
deadline = now_monotonic() + 500ms
```

---

# 43. Deadline semantics

Có hai policy:

```text
CANCEL_ON_EXPIRY
```

hoặc:

```text
STOP_WAITING_ON_EXPIRY
```

Policy thứ hai nghĩa:

> caller ngừng chờ, nhưng I/O có thể vẫn đang chạy.

Đây là distinction bắt buộc.

---

# 44. Timer subsystem

Core:

```text
timer_source
```

hỗ trợ:

```text
one-shot
repeating
deadline
timeout
```

Ví dụ:

```text
await timer.sleep(100ms)
```

không tạo OS thread riêng.

---

# 45. Timer implementation

Backend được phép dùng:

```text
timerfd
kernel timers
IOCP timers
kqueue timers
host event loop
timer heap
timer wheel
```

Runtime lựa chọn dựa trên profile.

---

# 46. Timer coalescing

Các timer gần nhau có thể gom:

```text
1000.1 ms
1000.3 ms
1000.7 ms
```

thành một wakeup khoảng:

```text
1001 ms
```

nếu profile cho phép.

Realtime profile có thể cấm coalescing.

---

# 47. Event source

Generic:

```text
event_source
```

có thể đại diện:

```text
file readiness
socket readiness
completion port
device event
timer
IPC notification
host event
```

Mỗi source khai báo capability.

---

# 48. Device I/O

Core API:

```text
device_submit()
device_wait()
```

Device backend có thể sử dụng:

```text
DMA
interrupt
polling
completion queue
```

Device capability phải được kiểm tra qua `AXSECURITY`.

---

# 49. I/O context

`io_context` là execution environment cho I/O.

```text
io_context {
    backend
    completion_queue
    buffer_registry
    timer_registry
    limits
    tracing
    policy
}
```

Một process có thể có nhiều context.

---

# 50. Context isolation

Các context có thể có:

```text
separate completion queue
separate limits
separate buffer registry
separate trace session
```

Nhưng không tạo security authority mới.

---

# 51. Batch submission

API:

```text
submit_batch(operations[])
```

Backend có thể biến:

```text
64 submit()
```

thành:

```text
1 kernel submission
```

nếu hỗ trợ.

---

# 52. Batch completion

```text
drain_completions(64)
```

đọc nhiều completion một lần.

Đây là fast path quan trọng cho server/high-throughput runtime.

---

# 53. Queue capacity

Mỗi context có:

```text
max_inflight
max_queue_depth
max_buffer_bytes
```

Khi đầy:

```text
BLOCK
FAIL
THROTTLE
```

`DROP` chỉ hợp lệ với event stream nơi mất event được phép.

Không được silently drop:

```text
file write
database write
IPC command
```

---

# 54. Rate limiting

Có thể giới hạn:

```text
bytes/sec
operations/sec
concurrent operations
```

Nhưng đây là resource policy, không phải scheduler toàn hệ thống.

---

# 55. I/O priority

Operation có thể chứa:

```text
priority_hint
latency_class
background
interactive
deadline
```

Đây là **hint/contract**, không phải đảm bảo kernel phải ưu tiên tuyệt đối.

---

# 56. Reentrancy

Không gọi callback đệ quy vô hạn:

```text
completion
 → callback
   → submit
     → immediate completion
       → callback
         → ...
```

Runtime sử dụng completion queue/trampoline khi cần:

```text
completion
   ↓
enqueue continuation
   ↓
dispatch
```

---

# 57. Thread safety

Có thể submit từ nhiều worker:

```text
worker A ─┐
worker B ─┼──► io_context
worker C ─┘
```

Không bắt buộc thread affinity.

---

# 58. Completion affinity

Mặc định:

```text
any worker
```

Có thể yêu cầu:

```text
executor affinity
task affinity
NUMA affinity
```

nếu operation cần.

---

# 59. Sync/Async bridge

Sync API có thể được xây trên async backend:

```text
read()
    ↓
submit
    ↓
wait
    ↓
completion
    ↓
return
```

Nhưng semantic của `read()` vẫn là:

> caller thread bị block.

Async API:

```text
read_async()
```

không được block worker task.

---

# 60. Error model

Stable error classes:

```text
SUCCESS
PARTIAL
CANCELLED
DEADLINE_EXPIRED
PEER_CLOSED
INVALID_HANDLE
PERMISSION_DENIED
NO_SPACE
DEVICE_ERROR
TRANSIENT_ERROR
INVALID_ARGUMENT
RESOURCE_EXHAUSTED
UNSUPPORTED
```

Kèm:

```text
native_error
```

để debugging.

---

# 61. Crash semantics

Nếu process chết:

```text
in-flight operations
       ↓
invalidated
```

Không được để completion cũ trở thành completion của process mới.

Generation ID bảo vệ:

```text
old request 17:41
new request 17:42
```

---

# 62. Peer death

IPC/network peer chết:

```text
PEER_CLOSED
PEER_UNAVAILABLE
CONNECTION_RESET
```

được chuyển thành stable Axiom error class.

---

# 63. Checkpoint

Không checkpoint trực tiếp kernel I/O state.

Không hợp lệ:

```text
snapshot
↓
restore
↓
pretend old kernel request still exists
```

Thay vào đó checkpoint:

```text
logical operation intent
```

chỉ khi operation:

```text
replay-safe
idempotent
checkpointable
```

---

# 64. Deterministic I/O simulation

`AXASYNC` phải có backend:

```text
SIMULATED
```

Virtual clock:

```text
t = 0
submit A
t = 5ms
complete A
```

Có thể mô phỏng:

- latency;
- partial completion;
- errors;
- cancellation race;
- timeout;
- completion reorder;
- queue saturation.

---

# 65. Fault injection

API:

```text
inject_io_fault()
```

Có thể inject:

```text
EIO
timeout
partial read
partial write
peer close
cancel race
queue full
buffer unavailable
```

Chỉ enabled khi:

```text
test profile
simulation profile
authorized diagnostic profile
```

Không tự động bật trong production.

---

# 66. I/O tracing

Trace record:

```text
submit
queued
backend_submit
backend_complete
completion
cancel
deadline
error
```

Kèm:

```text
timestamp
request_id
bytes
latency
queue_depth
batch_size
buffer_id
backend
native_error
```

---

# 67. Payload privacy

Trace mặc định **không ghi payload I/O**.

Nếu cần payload capture:

```text
explicit diagnostic policy
```

và phải tuân theo `AXSECURITY`.

---

# 68. Performance architecture

Hot path phải hướng tới:

```text
zero allocation
zero unnecessary copy
zero global lock
minimal syscall
```

Các kỹ thuật:

- inline operation metadata;
- slab operation pool;
- per-worker queues;
- per-core queues;
- NUMA-aware queues;
- completion batching;
- submission batching;
- registered buffers;
- zero-copy;
- cache-local request state;
- wake coalescing.

---

# 69. Operation pool

Không:

```text
malloc()
submit
free()
```

cho mỗi I/O trong high-throughput mode.

Thay vào đó:

```text
operation_slab
```

và recycle object.

---

# 70. NUMA

Buffer và queue nên gần worker/device:

```text
NUMA node 0
 ├─ worker
 ├─ completion queue
 └─ buffers

NUMA node 1
 ├─ worker
 ├─ completion queue
 └─ buffers
```

Không bắt buộc global queue.

---

# 71. Compiler integration

Axiom source:

```text
async fn load(path: string) -> bytes {
    let file = await storage.open_async(path)
    return await file.read_all_async()
}
```

Compiler:

```text
await
 ↓
AXTASK suspension point
 ↓
AXASYNC operation
 ↓
task frame stores request_id
 ↓
completion
 ↓
resume
```

---

# 72. Await ABI

Conceptually:

```text
AXASYNC_SUBMIT
AXTASK_SUSPEND
AXASYNC_COMPLETE
AXTASK_RESUME
```

Không expose OS-specific completion structures cho language-level code.

---

# 73. Native API baseline

```text
create_io_context()
destroy_io_context()

create_poller()
destroy_poller()

submit()
submit_batch()

poll()
wait()
poll_until()

drain_completions()

cancel()
cancel_all()

create_timer()
arm_timer()
disarm_timer()

register_buffer()
unregister_buffer()
create_buffer_group()

read_async()
write_async()
readv_async()
writev_async()

open_async()
flush_async()

accept_async()
connect_async()

recv_async()
send_async()
recv_from_async()
send_to_async()

wait_readable()
wait_writable()

attach_ipc_endpoint()

device_submit()
device_wait()

get_io_stats()

start_io_trace()
stop_io_trace()

replay_io_trace()

create_io_simulation()
inject_io_fault()
```

---

# 74. Capability discovery

Mỗi backend phải expose:

```text
io_capabilities
```

Ví dụ:

```text
completion_io
readiness_io
file_async
network_async
vectored_io
registered_buffers
zero_copy
dma
cancellation
batch_submit
batch_completion
timers
device_io
```

Application có thể kiểm tra runtime capability.

---

# 75. Không giả lập capability

Nếu backend không hỗ trợ:

```text
registered_buffers
```

runtime không được báo:

```text
supported = true
```

chỉ vì có thể mô phỏng bằng allocation thông thường.

Có distinction:

```text
NATIVE
EMULATED
UNSUPPORTED
```

---

# 76. Async file read — canonical flow

```text
1. allocate buffer
2. optionally register buffer
3. create io_operation
4. attach file handle
5. submit
6. AXTASK suspends
7. OS performs I/O
8. completion enters queue
9. worker drains completion
10. task resumes
11. result returned
```

---

# 77. Readiness socket — canonical flow

```text
1. attach socket to poller
2. wait_readable
3. readiness event
4. recv()
5. process bytes
6. wait again
```

Không nhầm readiness với completion.

---

# 78. Async network write

```text
send_async(buffer)
        ↓
registered/ordinary buffer
        ↓
submit
        ↓
network backend
        ↓
completion
        ↓
task resume
```

Buffer không được release trước completion.

---

# 79. Batch flow

```text
operations[0..63]
       ↓
submit_batch()
       ↓
backend
       ↓
completion[0..63]
       ↓
drain_batch()
       ↓
resume tasks
```

---

# 80. Zero-copy flow

```text
AXMEMORY.allocate()
       ↓
pin/register
       ↓
AXASYNC.register_buffer()
       ↓
device/network
       ↓
completion
       ↓
application owns buffer
       ↓
unregister
       ↓
release
```

---

# 81. Cancellation race flow

```text
submit
  │
  ├── cancel()
  │
  └── backend completion
          │
          ▼
     generation check
          │
          ▼
    single terminal state
```

---

# 82. Deadline flow

```text
submit
   │
   ├── I/O completion
   │
   └── timer
         │
         ▼
      deadline
```

Policy quyết định:

```text
cancel operation
```

hoặc:

```text
stop waiting
```

---

# 83. IPC async flow

```text
AXIPC endpoint
      ↓
AXASYNC attach
      ↓
submit receive
      ↓
message arrives
      ↓
completion
      ↓
AXIPC decodes message
      ↓
AXTASK resumes
```

---

# 84. Device flow

```text
AXMEMORY pinned buffer
        ↓
AXSECURITY capability
        ↓
AXASYNC device_submit
        ↓
DMA/device
        ↓
interrupt/poll
        ↓
completion
```

---

# 85. Crash flow

```text
process
  │
  ├─ request A
  ├─ request B
  └─ request C
        │
        ▼
      crash
        │
        ▼
invalidate context
        │
        ▼
A/B/C → PROCESS_TERMINATED
```

Không được replay tự động nếu semantic không idempotent.

---

# 86. Deterministic simulation flow

```text
simulation clock
      │
      ▼
submit A
      │
      ▼
inject 5ms latency
      │
      ▼
partial completion
      │
      ▼
inject cancellation race
      │
      ▼
completion
```

Cho phép test scheduler + task + I/O mà không cần real device.

---

# 87. Formal invariants

### ASYNC-INV-01
Mọi `io_operation` có một lifecycle state hợp lệ.

### ASYNC-INV-02
Mỗi terminal operation chỉ có một terminal completion.

### ASYNC-INV-03
`io_request_id` phải generation-safe.

### ASYNC-INV-04
Stale completion không được hoàn tất operation mới.

### ASYNC-INV-05
Cancellation request không đồng nghĩa cancellation completion.

### ASYNC-INV-06
Deadline dùng monotonic time.

### ASYNC-INV-07
Expiration không tự động imply kernel cancellation.

### ASYNC-INV-08
Partial I/O phải trả số byte thực tế.

### ASYNC-INV-09
Không được silently drop ordinary file writes.

### ASYNC-INV-10
Completion có thể xảy ra khác thread submit.

### ASYNC-INV-11
Không có global ordering mặc định giữa các request.

### ASYNC-INV-12
Ordering chỉ tồn tại khi semantic/backend contract cho phép.

### ASYNC-INV-13
Readiness event không được coi là completion.

### ASYNC-INV-14
Completion event không được yêu cầu caller thực hiện lại operation.

### ASYNC-INV-15
Async operation không được block AXTASK worker.

### ASYNC-INV-16
Sync bridge phải có blocking semantics rõ ràng.

### ASYNC-INV-17
Buffer đang IN_FLIGHT không được release.

### ASYNC-INV-18
Registered buffer phải còn valid trong toàn bộ operation.

### ASYNC-INV-19
Raw pointer không phải I/O ownership token.

### ASYNC-INV-20
DMA memory phải đáp ứng device visibility contract.

### ASYNC-INV-21
Cache coherency phải explicit khi platform yêu cầu.

### ASYNC-INV-22
Completion queue phải hỗ trợ batch drain.

### ASYNC-INV-23
Backend được phép tối ưu syscall batching.

### ASYNC-INV-24
Backend capability phải được khai báo trung thực.

### ASYNC-INV-25
Unsupported capability không được giả mạo là native capability.

### ASYNC-INV-26
I/O security authority không được tạo bởi AXASYNC.

### ASYNC-INV-27
Protected handle phải có authority hợp lệ từ AXSECURITY.

### ASYNC-INV-28
Process death invalidates process-owned in-flight I/O.

### ASYNC-INV-29
Peer death phải được biểu diễn bằng stable error.

### ASYNC-INV-30
Checkpoint không được giả định kernel I/O state có thể snapshot tùy ý.

### ASYNC-INV-31
Chỉ checkpointable/replay-safe intent mới được replay.

### ASYNC-INV-32
Simulation không được ảnh hưởng production backend ngoài explicit profile.

### ASYNC-INV-33
Fault injection phải explicit.

### ASYNC-INV-34
I/O trace mặc định không chứa payload.

### ASYNC-INV-35
Completion callback không được tạo recursive execution explosion.

### ASYNC-INV-36
Multiple submitter threads phải có semantics xác định.

### ASYNC-INV-37
Completion affinity chỉ là constraint khi operation yêu cầu.

### ASYNC-INV-38
I/O queue phải tôn trọng configured resource limits.

### ASYNC-INV-39
AXASYNC không sở hữu protocol semantics của AXNETWORK/AXIPC.

### ASYNC-INV-40
AXASYNC 5.0 phải giữ cùng semantic contract trên mọi backend; chỉ implementation/capability khác nhau.

---

# 88. Memory safety contract

AXASYNC không sử dụng GC để giải quyết buffer lifetime.

Contract là:

```text
submit(buffer)
      ↓
buffer lifetime ≥ operation lifetime
```

Compiler có thể phát hiện nhiều trường hợp statically.

Runtime debug build có thể phát hiện:

```text
release while in-flight
double unregister
stale buffer
use-after-unregister
```

---

# 89. High-performance mode

`AXASYNC_PROFILE_HIGH_THROUGHPUT`:

```text
registered buffers
batch submit
batch completion
per-core queue
NUMA locality
slab operation pool
zero-copy
wake coalescing
```

---

# 90. Low-latency mode

`AXASYNC_PROFILE_LOW_LATENCY`:

```text
small batches
optional bounded spinning
dedicated completion workers
reduced timer coalescing
CPU affinity hints
```

Không tự động ép toàn hệ thống sang low-latency.

---

# 91. Embedded mode

```text
AXASYNC_PROFILE_EMBEDDED
```

có thể loại bỏ:

```text
heap
dynamic registration
OS completion ports
```

nếu target không cần.

Core API vẫn giữ semantic model.

---

# 92. WASM mode

WASM backend không giả định:

```text
file descriptor
kernel thread
DMA
physical memory
```

Thay vào đó adapter:

```text
host promise/event
```

và map về cùng:

```text
io_operation
io_completion
```

---

# 93. ABI

Axiom native ABI cần giữ completion ABI nhỏ.

Một completion record mục tiêu:

```text
request_id
status
bytes
native_error
flags
user_data
```

Không chứa OS-specific giant structure trong hot path.

---

# 94. Compiler optimization

Compiler có thể:

- inline small I/O wrappers;
- eliminate temporary future allocation;
- embed operation trong task frame;
- specialize backend;
- eliminate redundant buffer registration;
- fuse sequential async operations khi semantic cho phép;
- static-size completion records;
- stack allocate operation metadata.

---

# 95. No hidden blocking

Một API có suffix:

```text
_async
```

phải có contract:

> không block calling task/worker thread.

Nếu operation bắt buộc blocking vì backend limitation, runtime phải chuyển nó sang:

```text
AXTASK blocking executor
```

thay vì block async worker.

---

# 96. Diagnostics

`get_io_stats()`:

```text
submitted
completed
failed
cancelled
expired

bytes_read
bytes_written

avg_latency
p50
p95
p99

queue_depth
max_inflight

batch_submit_count
batch_completion_count

syscall_count
registered_buffer_count
```

---

# 97. AI integration

AI tooling có thể phân tích:

```text
I/O trace
latency
queue depth
buffer utilization
batch efficiency
NUMA locality
```

và đề xuất:

```text
buffer size
batch size
queue depth
poll strategy
registration strategy
```

Nhưng AI không được:

```text
open protected handle
bypass sandbox
change security authority
read protected payload
disable policy
```

---

# 98. Test matrix

Compiler/runtime phải test:

```text
empty read
partial read
partial write
large read
large write

cancel-before-submit
cancel-in-flight
cancel-after-completion

deadline-before-submit
deadline-in-flight
deadline-after-completion

queue-full
buffer-release-race
stale-completion

peer-close
process-crash

batch submit
batch completion

readiness
completion

registered buffer
unregistered buffer

timer race
IPC race
device completion
```

---

# 99. Cross-platform conformance

Mọi backend phải pass semantic tests:

```text
operation lifecycle
completion uniqueness
cancellation
deadline
partial I/O
buffer lifetime
error mapping
request generation
```

Platform-specific behavior chỉ khác khi capability profile công khai.

---

# 100. Definition of Done

`AXASYNC 5.0` được xem là hoàn tất khi:

1. Có unified async I/O model.
2. Có readiness + completion semantics.
3. Có backend abstraction.
4. Có Windows IOCP backend contract.
5. Có Linux io_uring/epoll contract.
6. Có macOS/iOS backend contract.
7. Có Android backend contract.
8. Có WASM host adapter.
9. Có embedded adapter.
10. Có completion queue.
11. Có batching.
12. Có cancellation.
13. Có deadlines.
14. Có timers.
15. Có event sources.
16. Có vectored I/O.
17. Có zero-copy contract.
18. Có registered buffers.
19. Có DMA contract.
20. Có IPC integration.
21. Có network integration.
22. Có storage integration.
23. Có AXTASK integration.
24. Có deterministic simulation.
25. Có tracing.
26. Có fault injection.
27. Có stable error model.
28. Có crash invalidation semantics.
29. Có compiler lowering contract.
30. Có 40 invariants.
31. Có performance profiles.
32. Có cross-platform conformance model.
33. Không có hidden GC dependency.
34. Không có mandatory borrow checker dependency.
35. Không có third-party runtime dependency.
36. Không có global I/O lock bắt buộc.
37. Hot path hỗ trợ zero-allocation.
38. Security boundary không bị phá vỡ.
39. ABI được xác định.
40. `AXASYNC 5.0` được freeze.

---

# 101. Architectural freeze

Sau `BOOTSTRAP-749`, Axiom có pipeline native rõ ràng:

```text
AXAPPLICATION
      ↓
AXPROCESS
      ↓
AXMEMORY
      ↓
AXIPC
      ↓
AXTASK
      ↓
AXASYNC
      ↓
OS / DEVICE
```

Trong đó:

```text
AXTASK = logical execution
AXASYNC = asynchronous I/O
AXPROCESS = execution substrate
AXMEMORY = memory substrate
AXIPC = process communication
```

Không module nào được âm thầm thay thế responsibility của module khác.

---

# 102. Next bootstrap

**BOOTSTRAP-750 — AXSTREAM**

**Native Unified Stream Runtime — byte streams, text streams, message streams, buffering, framing, seeking, backpressure, synchronous/asynchronous streams, zero-copy stream buffers, file/network/IPC stream adapters, compression boundaries, encoding, stream composition, pipelines, duplex streams, half-close, EOF semantics, stream cancellation, deadlines, flow control, tracing, deterministic stream simulation và Stream Runtime 5.0.**