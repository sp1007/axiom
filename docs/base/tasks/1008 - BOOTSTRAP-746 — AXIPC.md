# BOOTSTRAP-746 — AXIPC

**Namespace:** `AXIPC`  
**Phase:** Axiom Civilization Runtime / Native Inter-Process Communication & Message Runtime  
**Status:** **ARCHITECTURAL BASELINE — FROZEN TARGET**  
**Depends on:** `AXPROCESS`, `AXMEMORY`, `AXTHREAD`, `AXSECURITY`, `AXAPPLICATION`, `AXNETWORK`, `AXDATABASE`, `AXCOMPUTE`, `AXSTORAGE`

AXIPC là tầng giao tiếp giữa các execution domain của Axiom.

Mục tiêu không phải tạo một RPC framework nặng nằm trên OS primitives, mà xây dựng một IPC substrate có thể đi từ:

```text
register/event
      ↓
local channel
      ↓
shared-memory channel
      ↓
typed message
      ↓
local RPC
      ↓
streaming IPC
      ↓
remote transport bridge
```

với **zero-copy** và **low-overhead fast path** là nguyên tắc thiết kế.

---

## 746.1 — Strong Boundary

### AXIPC owns

```text
endpoint
channel
port
message
message queue
shared-memory transport
IPC connection
request/response
stream
notification
wait set
backpressure
flow control
handle transfer
capability transfer
IPC lifecycle
IPC tracing/replay
```

### AXPROCESS owns

```text
process
thread
address space
process isolation
process lifecycle
```

### AXMEMORY owns

```text
memory region
mapping
allocation
shared-memory backing
DMA/device memory
```

AXIPC chỉ sử dụng memory primitives của AXMEMORY.

### AXSECURITY owns

```text
capability authority
authorization
identity
security policy
```

AXIPC không tự phát minh authority model.

### AXNETWORK owns

```text
TCP
UDP
HTTP
TLS
network transport
```

AXIPC có thể bridge IPC sang network nhưng không trở thành network stack thứ hai.

---

# 746.2 — Core IPC Model

Mô hình cơ bản:

```text
Process A
   │
   │ send
   ▼
Endpoint A
   │
   ▼
Channel
   │
   ▼
Endpoint B
   │
   ▼
Process B
```

Endpoint là điểm giao tiếp.

Channel là transport abstraction.

Message là logical payload.

---

# 746.3 — IPC Identity

```axiom
ipc_endpoint_id
ipc_channel_id
ipc_message_id
ipc_request_id
ipc_stream_id
```

Mỗi identity có namespace riêng.

Không sử dụng memory address làm IPC identity.

---

# 746.4 — Endpoint

```axiom
ipc_endpoint {
    id
    owner
    type
    state
    capabilities
}
```

---

# 746.5 — Endpoint Types

```text
QUEUE
CHANNEL
PORT
STREAM
REQUEST_ENDPOINT
RESPONSE_ENDPOINT
EVENT_ENDPOINT
SHARED_MEMORY_ENDPOINT
```

---

# 746.6 — Endpoint Lifecycle

```text
CREATED
    ↓
INITIALIZING
    ↓
READY
    ↓
CONNECTED
    ↓
ACTIVE
    ↓
CLOSING
    ↓
CLOSED
```

Exceptional:

```text
FAILED
BROKEN
REVOKED
```

---

# 746.7 — Channel

```axiom
ipc_channel {
    id
    sender
    receiver
    transport
    capacity
    ordering
    reliability
}
```

---

# 746.8 — Channel Direction

```text
ONE_WAY
TWO_WAY
MULTI_PRODUCER
MULTI_CONSUMER
```

---

# 746.9 — Ordering

Channel có thể khai báo:

```text
FIFO
SEQUENCED
UNORDERED
PARTITIONED
```

Không được giả định mọi transport đều FIFO.

---

# 746.10 — Reliability

```text
RELIABLE
BEST_EFFORT
LOSS_DETECTED
```

Local IPC thông thường dùng reliable semantics.

---

# 746.11 — Message

```axiom
ipc_message {
    id
    type
    size
    payload
    metadata
    handles
    capabilities
    timestamp
}
```

---

# 746.12 — Typed Message

Axiom ưu tiên:

```axiom
message<T>
```

thay vì:

```text
byte[] + runtime reflection
```

Compiler có thể biết layout message tại compile time.

---

# 746.13 — Message Schema

```axiom
message UserRequest {
    user_id: u64
    operation: Operation
    flags: u32
}
```

Compiler sinh metadata:

```text
size
alignment
field offsets
serialization layout
version
```

---

# 746.14 — Native Message Layout

Local IPC có thể sử dụng trực tiếp:

```text
typed native layout
```

mà không cần serialize.

Remote transport mới cần serialization.

---

# 746.15 — Serialization Boundary

```text
LOCAL IPC
    ↓
native representation

REMOTE IPC
    ↓
wire representation
```

Đây là boundary bắt buộc.

---

# 746.16 — Serialization

AXIPC phải hỗ trợ:

```text
fixed layout
packed layout
canonical wire layout
versioned layout
```

---

# 746.17 — No Reflection Hot Path

Typed IPC không được yêu cầu:

```text
runtime reflection
dynamic object graph traversal
generic boxed values
```

trên hot path.

---

# 746.18 — Message Header

Minimal header:

```text
message_id
message_type
payload_size
flags
request_id
sequence
```

Header phải có fixed native layout.

---

# 746.19 — Message Metadata

Optional:

```text
sender
timestamp
deadline
priority
trace_id
security_context
```

Metadata phải có fast/optional representation để message nhỏ không bị phình quá mức.

---

# 746.20 — Message Size Classes

```text
INLINE
SMALL
MEDIUM
LARGE
BUFFER
```

---

# 746.21 — Inline Message

Message nhỏ có thể nằm trực tiếp trong queue slot:

```text
queue slot
 ├── header
 └── inline payload
```

Không cần allocation.

---

# 746.22 — Large Message

Message lớn nên sử dụng:

```text
AXMEMORY shared buffer
```

thay vì copy nhiều lần.

---

# 746.23 — Zero-Copy Message

```text
Producer
   │
   ▼
shared buffer
   │
   └──── handle ────► Consumer
```

Consumer nhận ownership/view thay vì payload copy.

---

# 746.24 — Ownership Transfer

Buffer transfer:

```text
PRODUCER_OWNED
      ↓
IN_FLIGHT
      ↓
CONSUMER_OWNED
      ↓
RELEASED
```

---

# 746.25 — Shared Immutable Buffer

Một buffer có thể:

```text
PRODUCER_WRITABLE
      ↓
SEALED
      ↓
SHARED_READ_ONLY
```

rất phù hợp cho media/database/AI IPC.

---

# 746.26 — Handle Transfer

IPC có thể truyền:

```text
memory_handle
file_handle
endpoint_handle
device_handle
resource_handle
```

nhưng không truyền raw pointer.

---

# 746.27 — Capability Transfer

Capability có thể được truyền nếu:

```text
sender has TRANSFER right
```

và policy cho phép.

---

# 746.28 — Capability Attenuation

Sender có thể truyền capability với quyền giảm:

```text
READ_WRITE
    ↓
READ_ONLY
```

không thể tự nâng quyền.

---

# 746.29 — Handle Semantics

Handle:

```text
opaque
typed
generation-checked
rights-bound
```

---

# 746.30 — Handle Lifetime

Khi process đóng:

```text
all owned handles
      ↓
closed/revoked
```

trừ resource có explicit external ownership.

---

# 746.31 — Port

Port là endpoint có khả năng nhận connection:

```axiom
ipc_port {
    name
    owner
    policy
}
```

---

# 746.32 — Port Discovery

Local process có thể resolve:

```text
service name
    ↓
port
    ↓
endpoint
```

Discovery không tự động cấp authority.

---

# 746.33 — Namespace

IPC namespaces hỗ trợ:

```text
system
user
session
application
sandbox
container
```

---

# 746.34 — Private Endpoint

Endpoint có thể chỉ visible cho:

```text
specific process
process group
capability holder
```

---

# 746.35 — Local Channel

Fast path:

```text
user code
 ↓
shared queue
 ↓
notification
 ↓
consumer
```

Không nhất thiết phải serialize.

---

# 746.36 — Shared-Memory Channel

```text
Producer
   │
   ├── shared ring
   │
   ▼
Consumer
```

AXMEMORY cung cấp backing.

AXIPC cung cấp protocol.

---

# 746.37 — SPSC Queue

Single producer/single consumer:

```text
lock-free
```

được tối ưu đặc biệt.

---

# 746.38 — MPSC Queue

Multiple producers:

```text
atomic reservation
```

hoặc specialized queue backend.

---

# 746.39 — MPMC Queue

Multiple producer/consumer được hỗ trợ nhưng không được ép mọi channel dùng MPMC.

---

# 746.40 — Queue Capacity

```axiom
queue.capacity
```

là finite resource.

Khi đầy phải có policy rõ ràng.

---

# 746.41 — Backpressure

Policy:

```text
BLOCK
WAIT
DROP
REJECT
GROW
SPILL
```

---

# 746.42 — Backpressure Contract

Sender phải biết channel có thể:

```text
accept
reject
block
defer
```

Không được silently drop message trên reliable channel.

---

# 746.43 — Message Drop

Chỉ được phép nếu channel policy cho phép.

Ví dụ:

```text
BEST_EFFORT
LATEST_VALUE
COALESCE
```

---

# 746.44 — Latest-Value Channel

```text
producer
   ↓
value
   ↓
replace previous value
```

phù hợp:

```text
sensor state
cursor position
telemetry
UI state
```

---

# 746.45 — Event Channel

Event không nhất thiết mang payload lớn:

```axiom
event_endpoint
```

chỉ signal state change.

---

# 746.46 — Notification Primitive

Native primitive:

```axiom
notify(endpoint)
wait(endpoint)
```

có thể lower xuống OS primitive/futex/event object.

---

# 746.47 — Wait Set

Một thread có thể chờ nhiều endpoint:

```axiom
wait_set {
    endpoints
}
```

Ví dụ:

```text
IPC
timer
socket
process
device
```

---

# 746.48 — Wait Result

```text
READY
TIMEOUT
CANCELLED
CLOSED
ERROR
```

---

# 746.49 — Deadline

IPC operation có:

```axiom
deadline
```

không chỉ:

```text
timeout duration
```

Deadline được biểu diễn bằng monotonic clock domain.

---

# 746.50 — Cancellation

```axiom
cancel(request)
```

Cancellation phải phân biệt:

```text
not started
in flight
completed
cancelled
cancellation requested
```

---

# 746.51 — Cancellation Race

Nếu request hoàn thành trước cancellation:

```text
COMPLETED
```

không được biến thành CANCELLED chỉ vì cancellation request đến sau.

---

# 746.52 — Request/Response

```text
Client
  │
  │ Request
  ▼
Server
  │
  │ Response
  ▼
Client
```

Request có:

```text
request_id
deadline
payload
```

---

# 746.53 — Request Lifecycle

```text
CREATED
 ↓
QUEUED
 ↓
DISPATCHED
 ↓
PROCESSING
 ↓
COMPLETED
```

Exceptional:

```text
REJECTED
TIMEOUT
CANCELLED
FAILED
```

---

# 746.54 — Response Matching

Response được match bằng:

```text
request_id
```

không bằng thứ tự arrival nếu protocol cho phép concurrent requests.

---

# 746.55 — RPC

Axiom có thể compile:

```axiom
service UserService {
    get_user(UserRequest) -> UserResponse
}
```

thành:

```text
client stub
server dispatch
message layout
request matching
error mapping
```

---

# 746.56 — Compile-Time RPC

RPC interface metadata được compiler biết trước:

```text
method ID
request layout
response layout
error layout
```

Không cần reflection runtime.

---

# 746.57 — Local RPC Fast Path

Nếu client/server cùng process:

```text
RPC
 ↓
direct function dispatch
```

nếu semantics cho phép.

Nếu khác process:

```text
RPC
 ↓
IPC transport
```

---

# 746.58 — In-Process Optimization

Compiler có thể optimize:

```text
IPC abstraction
```

thành direct call khi chứng minh:

```text
same process
same security domain
same ABI
```

---

# 746.59 — Streaming IPC

```axiom
ipc_stream<T>
```

cho:

```text
producer → consumer
```

liên tục.

---

# 746.60 — Stream Semantics

Stream có:

```text
ordering
flow control
backpressure
half-close
close
cancel
```

---

# 746.61 — Half Close

Một phía có thể:

```text
CLOSE_SEND
```

nhưng tiếp tục:

```text
RECEIVE
```

---

# 746.62 — Bidirectional Stream

```text
A ⇄ B
```

mỗi direction có flow-control state riêng.

---

# 746.63 — Flow Control

Window:

```text
available capacity
in-flight bytes
consumed bytes
```

---

# 746.64 — Credit-Based IPC

High-throughput IPC có thể dùng:

```text
credits
```

để tránh producer overrun.

---

# 746.65 — Priority

Message có optional:

```text
priority
```

nhưng priority không được bypass:

```text
security
quota
ordering
```

---

# 746.66 — Fairness

Scheduler/queue backend phải tránh một producer độc quyền channel vô thời hạn.

AXIPC cung cấp fairness hints; AXCOMPUTE quyết định CPU scheduling.

---

# 746.67 — Batching

Producer có thể:

```axiom
send_batch(messages)
```

giảm syscall/notification overhead.

---

# 746.68 — Notification Coalescing

Nhiều messages có thể chỉ trigger:

```text
one notification
```

consumer drain queue.

---

# 746.69 — Polling

Low-latency application có thể:

```axiom
poll(endpoint)
```

thay vì blocking wait.

---

# 746.70 — Busy Polling

Realtime profile có thể sử dụng busy polling nhưng phải explicit vì:

```text
CPU consumption
```

có thể tăng mạnh.

---

# 746.71 — Interrupt-Driven Mode

Normal background workload ưu tiên:

```text
sleep
 ↓
notification
 ↓
wake
```

---

# 746.72 — IPC Memory Pool

IPC runtime có pool riêng:

```text
message descriptors
queue nodes
small payload buffers
```

tránh general heap allocation.

---

# 746.73 — Message Descriptor

```axiom
ipc_descriptor {
    type
    flags
    payload
    handles
}
```

có thể nằm trong preallocated pool.

---

# 746.74 — Per-Thread IPC Cache

Thread có thể cache:

```text
message descriptor
small buffer
endpoint lookup
```

để giảm contention.

---

# 746.75 — Endpoint Lookup

Tên endpoint chỉ resolve ở cold path.

Hot path dùng:

```text
endpoint_id
cached handle
```

---

# 746.76 — Connection Establishment

```text
resolve port
 ↓
authorize
 ↓
create endpoint
 ↓
negotiate protocol
 ↓
READY
```

---

# 746.77 — Connection Negotiation

Negotiation có thể xác định:

```text
protocol version
message version
transport
maximum message size
features
capabilities
```

---

# 746.78 — Versioning

Message schema phải hỗ trợ:

```text
compatible evolution
```

---

# 746.79 — Schema Version

```axiom
message_version
```

phải được xác định.

---

# 746.80 — Forward Compatibility

Consumer mới phải có khả năng reject/ignore unknown fields theo schema policy.

---

# 746.81 — Backward Compatibility

Service update không được làm client cũ crash chỉ vì field mới nếu schema đánh dấu optional.

---

# 746.82 — ABI vs Wire ABI

Phải phân biệt:

```text
native ABI
wire ABI
```

Native layout không mặc nhiên portable.

---

# 746.83 — Error Model

IPC error:

```text
DISCONNECTED
PEER_TERMINATED
QUEUE_FULL
TIMEOUT
CANCELLED
ACCESS_DENIED
INVALID_MESSAGE
VERSION_MISMATCH
RESOURCE_EXHAUSTED
PROTOCOL_ERROR
```

---

# 746.84 — Peer Termination

Khi process chết:

```text
endpoint
 ↓
PEER_TERMINATED
```

pending requests phải chuyển trạng thái xác định.

---

# 746.85 — Request Recovery

Request có thể:

```text
retry
fail
reconnect
restore
```

theo service policy.

AXIPC không tự retry mọi operation vì có thể gây duplicate side effects.

---

# 746.86 — Idempotency

Request có thể khai báo:

```text
IDEMPOTENT
NON_IDEMPOTENT
UNKNOWN
```

Retry chỉ tự động được phép khi policy xác nhận.

---

# 746.87 — Duplicate Detection

Request có:

```text
request_id
idempotency_key
```

nếu service cần exactly-once-like application semantics.

---

# 746.88 — Exactly Once

AXIPC không tuyên bố distributed exactly-once semantics mặc định.

Nó chỉ cung cấp primitives để application xây dựng semantics phù hợp.

---

# 746.89 — At-Most Once

Local IPC có thể cung cấp:

```text
deliver at most once
```

với request lifecycle được xác định.

---

# 746.90 — At-Least Once

Bridge transport có thể cung cấp:

```text
retry
redelivery
```

nhưng application phải xử lý duplicate.

---

# 746.91 — Local IPC vs Remote IPC

```text
AXIPC
 │
 ├── LOCAL
 │
 └── REMOTE BRIDGE
          │
          ▼
      AXNETWORK
```

Không trộn hai semantics.

---

# 746.92 — Remote Bridge

```axiom
ipc_bridge {
    local_endpoint
    remote_endpoint
    network_transport
    protocol
}
```

---

# 746.93 — Security Boundary

Remote IPC phải xác thực:

```text
peer identity
transport security
capability
authorization
```

---

# 746.94 — IPC Authentication

AXIPC dùng identity/security primitives từ:

```text
AXIDENTITY
AXSECURITY
```

không tự quản lý identity database.

---

# 746.95 — Capability-Based IPC

Endpoint access có thể dựa trên:

```text
capability
```

thay vì global name.

---

# 746.96 — Least Authority

Endpoint capability chỉ chứa:

```text
specific endpoint
specific rights
specific scope
```

---

# 746.97 — Rights

```text
CONNECT
SEND
RECEIVE
TRANSFER
CLOSE
ADMIN
```

---

# 746.98 — Delegation

Endpoint capability có thể delegate quyền hạn chế hơn.

Không được delegate quyền lớn hơn capability gốc.

---

# 746.99 — Sandboxed IPC

Sandboxed process chỉ nhìn thấy endpoints được policy expose.

---

# 746.100 — IPC Isolation

Không cho phép:

```text
sandbox → arbitrary system endpoint
```

---

# 746.101 — Secure Message

Sensitive message có thể yêu cầu:

```text
encrypted
authenticated
integrity_protected
```

Nhưng local trusted channel không bắt buộc encryption nếu policy không yêu cầu.

---

# 746.102 — Message Integrity

Message integrity có thể được bảo vệ bằng:

```text
transport security
capability-bound channel
cryptographic MAC/signature
```

theo security profile.

---

# 746.103 — IPC Audit

Security-sensitive operations có thể phát event:

```text
connection
authorization
capability transfer
handle transfer
denial
endpoint closure
```

---

# 746.104 — Audit Data Minimization

Payload không được tự động copy vào audit log.

Chỉ metadata cần thiết.

---

# 746.105 — IPC Tracing

```axiom
ipc_trace_event {
    timestamp
    endpoint
    operation
    message_type
    size
    thread
    process
    request_id
}
```

---

# 746.106 — Trace Sampling

High-throughput IPC phải hỗ trợ:

```text
sampling
aggregation
```

để tracing không trở thành bottleneck.

---

# 746.107 — Latency Measurement

Theo dõi:

```text
enqueue latency
queue latency
dispatch latency
processing latency
response latency
```

---

# 746.108 — Queue Depth

Telemetry:

```text
current_depth
peak_depth
drop_count
reject_count
blocked_sender_count
```

---

# 746.109 — Backpressure Telemetry

Có thể xác định:

```text
producer bottleneck
consumer bottleneck
queue saturation
```

---

# 746.110 — IPC Deadlock

Runtime phải cung cấp diagnostic để phát hiện cycle:

```text
A waits B
B waits C
C waits A
```

Nhưng không được biến mọi IPC wait thành global lock.

---

# 746.111 — Wait Graph

Diagnostic mode:

```text
Process A
   waits → Endpoint B
                waits → Process C
```

---

# 746.112 — Synchronous IPC

Synchronous request:

```text
send
 ↓
wait response
```

được hỗ trợ.

---

# 746.113 — Asynchronous IPC

Async request:

```text
send
 ↓
return immediately
 ↓
completion event
```

là preferred model cho high-concurrency systems.

---

# 746.114 — Future/Promise Integration

RPC result có thể lower thành:

```axiom
future<Response>
```

nhưng future abstraction thuộc async/runtime layer; AXIPC chỉ cung cấp completion primitive.

---

# 746.115 — Callback Avoidance

Hot IPC path không bắt buộc callback allocation.

Completion có thể sử dụng:

```text
event
future
wait
poll
```

---

# 746.116 — Coroutine Integration

Compiler/runtime có thể suspend coroutine trên:

```text
IPC wait
```

mà không block OS thread.

---

# 746.117 — Thread Integration

AXTHREAD cung cấp execution context.

AXIPC cung cấp waitable operations.

AXCOMPUTE quyết định thread scheduling.

---

# 746.118 — Cancellation Propagation

Parent request cancellation có thể propagate:

```text
client
 ↓
request
 ↓
server task
```

nếu service contract cho phép.

---

# 746.119 — Cancellation Authority

Client không thể force-kill arbitrary server task chỉ vì request cancellation.

Server policy quyết định cancellation handling.

---

# 746.120 — Resource Quotas

IPC quotas:

```text
max endpoints
max channels
max queued messages
max shared bytes
max handles
max pending requests
```

---

# 746.121 — Quota Hierarchy

```text
system
 ↓
user/session
 ↓
application
 ↓
process
 ↓
endpoint
```

Child không vượt parent quota.

---

# 746.122 — Queue Memory Accounting

Queued buffers phải được tính vào owner/resource domain thích hợp.

Không để memory accounting biến mất khi buffer đang in-flight.

---

# 746.123 — Shared Memory Accounting

Shared region phải tránh double-counting sai:

```text
logical allocation
≠
number of mappings
```

---

# 746.124 — IPC Resource Cleanup

Khi endpoint đóng:

```text
queued messages
pending requests
shared buffers
handles
notifications
```

phải có cleanup semantics xác định.

---

# 746.125 — Graceful Shutdown

```text
OPEN
 ↓
STOP_SEND
 ↓
DRAIN
 ↓
CLOSE
```

---

# 746.126 — Forced Shutdown

```text
FORCE_CLOSE
```

được phép với authority phù hợp.

Pending operations nhận explicit failure.

---

# 746.127 — Service Supervision

AXIPC tích hợp AXPROCESS supervisor:

```text
service died
 ↓
endpoint broken
 ↓
supervisor
 ↓
restart
 ↓
reconnect
```

---

# 746.128 — Endpoint Persistence

Logical service identity có thể tồn tại qua service restart.

Endpoint instance identity vẫn thay đổi.

---

# 746.129 — Reconnect

Client có thể:

```text
service identity
 ↓
new endpoint instance
```

nhưng phải reauthorize.

---

# 746.130 — State Restoration

Pending request chỉ được restore nếu service protocol hỗ trợ.

Không tự động replay side-effecting request.

---

# 746.131 — Checkpoint

IPC checkpoint có thể lưu:

```text
endpoint metadata
connection identity
protocol version
queued safe messages
logical request state
```

---

# 746.132 — IPC Checkpoint Boundary

Checkpoint **không mặc định chứa arbitrary kernel queue state** hoặc platform-specific transport internals.

---

# 746.133 — Deterministic Replay

Replay có thể reproduce:

```text
endpoint creation
message order
request lifecycle
timeouts
cancellation
disconnects
```

---

# 746.134 — Hardware-Level Determinism

AXIPC không hứa:

```text
exact CPU scheduling reproduction
exact network timing
exact interrupt timing
```

trừ simulation backend được kiểm soát.

---

# 746.135 — IPC Simulator

```axiom
ipc_simulator {
    latency
    bandwidth
    capacity
    loss
    reorder
    disconnect
    timeout
}
```

---

# 746.136 — Fault Injection

Simulation/test có thể inject:

```text
QUEUE_FULL
TIMEOUT
DISCONNECT
MESSAGE_DROP
MESSAGE_REORDER
PEER_CRASH
MEMORY_PRESSURE
```

---

# 746.137 — Digital Twin

IPC digital twin biểu diễn:

```text
processes
endpoints
channels
queues
connections
message flows
resource usage
```

---

# 746.138 — Message Flow Graph

```text
A
 │
 ├── Request ──► B
 │                │
 │                └──► C
 │
 └── Event ─────► D
```

Dùng cho debugging/performance analysis.

---

# 746.139 — AI Boundary

AI có thể:

```text
analyze IPC bottlenecks
suggest queue sizes
detect deadlock patterns
suggest batching
detect abnormal traffic
suggest channel topology
```

AI không được:

```text
bypass capability
read protected messages
grant authority
impersonate a privileged service
kill protected processes
```

---

# 746.140 — AI Protocol Analysis

AI có thể đọc:

```text
schema metadata
trace metadata
performance statistics
```

nếu user có authority.

Payload sensitive phải tuân privacy policy.

---

# 746.141 — IPC Performance Architecture

Hot path:

```text
typed message
     ↓
endpoint handle
     ↓
queue slot
     ↓
atomic publish
     ↓
notification
```

Không:

```text
reflection
generic boxing
heap allocation
serialization
global lock
```

nếu local fast path không cần.

---

# 746.142 — Small Message Fast Path

```text
message ≤ inline_limit
```

→ inline queue.

---

# 746.143 — Large Message Fast Path

```text
large payload
 ↓
shared buffer
 ↓
handle transfer
```

---

# 746.144 — Buffer Pool

Dedicated IPC pools:

```text
small
medium
large descriptor
```

---

# 746.145 — Cache Locality

Hot metadata nên được layout:

```text
endpoint_id
queue_state
head
tail
capacity
```

trong contiguous structures.

Cold metadata:

```text
security
debug
names
statistics
```

tách khỏi hot path.

---

# 746.146 — False Sharing

Queue indices phải được layout/padded phù hợp khi producer/consumer chạy trên khác CPU cores.

---

# 746.147 — NUMA IPC

Cross-NUMA channel có thể:

```text
remote memory
```

nhưng runtime phải expose topology/latency để specialized workloads chọn channel placement.

---

# 746.148 — CPU Affinity

AXIPC không điều khiển CPU affinity.

Có thể cung cấp telemetry/hint cho AXCOMPUTE.

---

# 746.149 — Batch Notification

Producer có thể append nhiều messages rồi signal một lần.

---

# 746.150 — Drain Loop

Canonical consumer:

```axiom
while endpoint.poll(message) {
    process(message)
}
```

giảm wakeup frequency.

---

# 746.151 — Cooperative Backpressure

Consumer có thể advertise:

```text
available credits
```

Producer tự throttle.

---

# 746.152 — Streaming Buffer

Streaming IPC có thể dùng:

```text
ring buffer
producer cursor
consumer cursor
sequence
```

---

# 746.153 — Wraparound

Sequence numbers phải đủ lớn để tránh ambiguity trong lifetime của queue.

---

# 746.154 — ABA Protection

Lock-free queues phải dùng:

```text
generation/sequence
```

để tránh ABA bugs.

---

# 746.155 — Memory Ordering

Atomic operations phải dùng memory-order semantics rõ:

```text
relaxed
acquire
release
acq_rel
seq_cst
```

khi exposed ở low-level API.

---

# 746.156 — Fence-Free Fast Path

Compiler/backend được phép chọn memory ordering tối thiểu đủ bảo đảm protocol.

---

# 746.157 — Platform Backend

AXIPC backend:

```text
Windows
Linux
macOS
Android
iOS
WASM
embedded
```

---

# 746.158 — Windows Backend

Có thể map xuống:

```text
shared memory
events
named objects
ALPC-like primitives
pipes
```

tùy privilege/platform.

Axiom API không phụ thuộc Windows API.

---

# 746.159 — Linux Backend

Có thể sử dụng:

```text
shared memory
futex
eventfd
Unix domain sockets
pipes
```

---

# 746.160 — macOS Backend

Có thể dùng:

```text
Mach IPC
shared memory
Unix domain sockets
```

---

# 746.161 — Mobile Backend

Android/iOS cần tôn trọng:

```text
sandbox
application lifecycle
background restrictions
OS IPC policy
```

---

# 746.162 — WASM Backend

Trong WASM:

```text
IPC
```

có thể được lower thành:

```text
worker messaging
shared linear memory
host calls
```

tùy execution environment.

---

# 746.163 — Embedded

Embedded profile có thể chỉ cần:

```text
ring buffer
event
shared memory
```

không yêu cầu OS process.

---

# 746.164 — Kernel-Like Profile

Trusted Axiom runtime có thể expose IPC primitive gần kernel:

```text
port
message queue
shared page
notification
```

---

# 746.165 — User Application Profile

Application API nên đơn giản:

```axiom
connect("service")
send(request)
receive()
```

trong khi advanced API vẫn expose native controls.

---

# 746.166 — High-Level Service Definition

```axiom
service ImageService {
    resize(ImageRequest) -> ImageResponse
    inspect(ImageId) -> Metadata
}
```

Compiler có thể sinh:

```text
client
server
schema
dispatch
serialization
documentation metadata
```

---

# 746.167 — Service Method IDs

Method ID phải ổn định theo schema:

```text
service_id
method_id
version
```

---

# 746.168 — Service Discovery

Discovery có thể query:

```text
service identity
version
endpoint
capabilities
health
```

Health authority vẫn thuộc supervisor/service infrastructure.

---

# 746.169 — Service Contracts

Service contract phải định nghĩa:

```text
request
response
errors
timeout
cancellation
idempotency
security requirements
```

---

# 746.170 — Protocol Validation

Receiver phải validate:

```text
message size
type
version
handle rights
payload bounds
```

trước khi dispatch.

---

# 746.171 — Malformed Message

Malformed input không được gây:

```text
memory corruption
arbitrary code execution
authority escalation
```

---

# 746.172 — Resource Exhaustion Protection

Một peer không được dễ dàng:

```text
allocate unbounded queue
create infinite endpoints
send unlimited pending requests
```

---

# 746.173 — Rate Limit

Endpoint có thể có:

```text
messages/sec
bytes/sec
pending requests
```

limits.

---

# 746.174 — Quota Error

Quota failure phải observable:

```text
RESOURCE_EXHAUSTED
```

không silent drop.

---

# 746.175 — IPC Security Context

Message có thể carry:

```text
principal
capability context
security domain
```

nhưng không tự tạo authority.

---

# 746.176 — Confused Deputy Protection

Service không được dùng authority của chính nó để thực hiện request thay cho caller nếu caller không có quyền.

Caller context phải được propagated/validated khi policy yêu cầu.

---

# 746.177 — Delegated Operation

Service có thể thay mặt caller chỉ khi:

```text
explicit delegation
```

tồn tại.

---

# 746.178 — Audit Correlation

Request có:

```text
trace_id
request_id
caller_identity
```

khi policy yêu cầu.

---

# 746.179 — Privacy

IPC metadata phải hỗ trợ classification:

```text
PUBLIC
INTERNAL
PRIVATE
SENSITIVE
RESTRICTED
```

---

# 746.180 — Sensitive IPC

Sensitive payload không được tự động:

```text
trace
dump
log
AI analyze
```

nếu không có authorization.

---

# 746.181 — IPC Encryption

Encryption được chọn theo:

```text
local policy
remote policy
security domain
```

không phải mọi local IPC đều phải encryption.

---

# 746.182 — Resource Transfer

IPC có thể transfer:

```text
memory
file
socket
device
GPU resource
```

nhưng semantics thực tế do owning subsystem xác định.

---

# 746.183 — GPU Resource Transfer

AXIPC chỉ transfer handle/capability.

AXGRAPHICS quyết định resource semantics.

---

# 746.184 — File Handle Transfer

AXIPC truyền handle.

AXSTORAGE quyết định:

```text
read
write
seek
lifetime
```

---

# 746.185 — Network Socket Transfer

AXIPC có thể transfer socket capability giữa process.

AXNETWORK sở hữu socket semantics.

---

# 746.186 — Process Handle Transfer

Process control handle phải có explicit security rights:

```text
QUERY
SIGNAL
SUSPEND
TERMINATE
DEBUG
```

Không mặc định GRANT tất cả.

---

# 746.187 — Debugger IPC

Debugger có thể sử dụng AXIPC để:

```text
attach
inspect
control
trace
```

nhưng AXSECURITY quyết định quyền.

---

# 746.188 — Crash IPC

Process crash có thể notify supervisor:

```text
CRASH_EVENT
```

với:

```text
process_id
thread_id
exception
crash_record
```

Payload dump không tự động truyền toàn bộ qua IPC.

---

# 746.189 — IPC and AXAPPLICATION

AXAPPLICATION có thể sử dụng:

```text
application launch service
single-instance service
automation
deep-link
```

trên AXIPC.

---

# 746.190 — IPC and AXDESKTOP

Desktop shell có thể dùng IPC cho:

```text
application launch
notifications
clipboard
shell services
window coordination
```

---

# 746.191 — IPC and AXDATABASE

Database engine có thể dùng:

```text
shared buffer
query service
CDC stream
```

nhưng transaction semantics thuộc AXDATABASE.

---

# 746.192 — IPC and AXCOMPUTE

Compute jobs có thể communicate:

```text
task
worker
scheduler
device service
```

AXCOMPUTE vẫn owns scheduling.

---

# 746.193 — IPC and AXNETWORK

Network daemon có thể expose:

```text
typed local API
```

để application tránh duplicate protocol stacks.

---

# 746.194 — IPC and AXMEDIA

Media pipeline có thể transfer:

```text
frame buffer
audio buffer
metadata
timestamps
```

bằng zero-copy shared memory.

---

# 746.195 — IPC and AXAUDIO

Realtime audio IPC phải ưu tiên:

```text
preallocated ring
lock-free
bounded latency
no allocation
```

---

# 746.196 — IPC and AXGRAPHICS

Graphics process có thể transfer:

```text
surface handle
fence
GPU resource handle
```

AXCOMPOSITOR quyết định composition semantics.

---

# 746.197 — IPC and AXSECURITY

Security operations:

```text
authorize
grant
revoke
audit
```

được gọi qua explicit security APIs.

---

# 746.198 — IPC and AXMEMORY

Memory ownership:

```text
allocation
 ↓
shared mapping
 ↓
IPC transfer
```

phải có một authoritative lifetime model.

---

# 746.199 — IPC Runtime Architecture

```text
                       AXIPC
                         │
        ┌────────────────┼─────────────────┐
        │                │                 │
        ▼                ▼                 ▼
   Local IPC       Shared Memory       Remote Bridge
        │                │                 │
   ┌────┴────┐       AXMEMORY          AXNETWORK
   │         │
 Queue     Port
   │         │
   └────┬────┘
        ▼
 Message / RPC / Stream
        │
        ▼
 AXPROCESS / AXTHREAD
        │
        ▼
 AXSECURITY
```

---

# 746.200 — Formal Invariants

```text
IPC-INV-01   Every endpoint has a unique logical identity within its namespace.
IPC-INV-02   Endpoint identity is distinct from memory address.
IPC-INV-03   Endpoint access requires explicit authority.
IPC-INV-04   A raw pointer cannot be transferred as a valid cross-process reference.
IPC-INV-05   Every message has an explicit type/layout.
IPC-INV-06   Message size is validated before payload access.
IPC-INV-07   Native IPC does not require runtime reflection.
IPC-INV-08   Local native messages need not be serialized.
IPC-INV-09   Remote messages cross an explicit wire-format boundary.
IPC-INV-10   Unknown protocol versions are handled explicitly.

IPC-INV-11   Queue capacity is finite unless explicit dynamic-growth policy exists.
IPC-INV-12   Reliable channels do not silently drop messages.
IPC-INV-13   Best-effort channels explicitly declare loss semantics.
IPC-INV-14   Backpressure behavior is explicit.
IPC-INV-15   Queue ownership is attributable to a resource domain.
IPC-INV-16   In-flight buffers retain valid lifetime ownership.
IPC-INV-17   Zero-copy transfer preserves buffer validity.
IPC-INV-18   Handle transfer preserves rights constraints.
IPC-INV-19   Capability delegation cannot increase authority.
IPC-INV-20   Closed endpoints reject new operations.

IPC-INV-21   Peer termination produces explicit endpoint/request state.
IPC-INV-22   Cancellation cannot retroactively change an already completed operation.
IPC-INV-23   Request IDs distinguish concurrent requests.
IPC-INV-24   Automatic retry requires explicit retry/idempotency semantics.
IPC-INV-25   Exactly-once application semantics are not assumed by default.
IPC-INV-26   Pending requests cannot exceed configured resource limits.
IPC-INV-27   Endpoint quotas cannot be silently exceeded.
IPC-INV-28   Shared-memory mappings require explicit security authority.
IPC-INV-29   Protected payloads are not automatically copied into diagnostics.
IPC-INV-30   IPC cannot bypass AXSECURITY authorization.

IPC-INV-31   IPC does not grant authority merely by message content.
IPC-INV-32   Capability-bearing messages preserve attenuation semantics.
IPC-INV-33   Confused-deputy-sensitive operations preserve caller authority context.
IPC-INV-34   Remote IPC requires an explicit network/security boundary.
IPC-INV-35   IPC tracing must be separable from production hot-path semantics.
IPC-INV-36   Deterministic replay is distinct from hardware-level execution determinism.
IPC-INV-37   Simulation faults cannot silently alter production security policy.
IPC-INV-38   Message ordering is defined by channel contract.
IPC-INV-39   Transport optimization cannot change logical IPC semantics.
IPC-INV-40   IPC fast paths must not require mandatory allocation, reflection, or global locking.
```

---

# 746.201 — Native API

```axiom
create_endpoint()
close_endpoint()

create_port()
bind_port()
resolve_port()

create_channel()
connect_channel()
disconnect_channel()

send()
send_batch()

receive()
receive_batch()
poll()

wait()
wait_set()

create_request()
send_request()
receive_response()
cancel_request()

create_stream()
stream_send()
stream_receive()
stream_close_send()
stream_close()

create_shared_channel()

allocate_message()
release_message()

seal_buffer()
transfer_buffer()

transfer_handle()
transfer_capability()

set_backpressure_policy()
set_queue_limits()

set_deadline()
set_priority()

create_service()
register_service()
discover_service()

create_rpc_client()
create_rpc_server()

start_ipc_trace()
stop_ipc_trace()

create_ipc_snapshot()
restore_ipc_state()

create_ipc_simulator()
inject_ipc_fault()
replay_ipc_trace()

query_endpoint_stats()
query_channel_stats()
```

---

# 746.202 — Canonical Flow: Local Request

```text
Client
  │
  ▼
resolve endpoint
  │
  ▼
authorize
  │
  ▼
construct typed message
  │
  ▼
inline/shared buffer
  │
  ▼
enqueue
  │
  ▼
notify
  │
  ▼
Server
  │
  ▼
validate
  │
  ▼
dispatch
  │
  ▼
response
```

---

# 746.203 — Canonical Flow: Zero-Copy

```text
Producer
   │
   ▼
AXMEMORY buffer
   │
   ▼
seal
   │
   ▼
transfer handle
   │
   ▼
AXIPC
   │
   ▼
Consumer
   │
   ▼
read shared buffer
   │
   ▼
release
```

Không có:

```text
Producer → copy → IPC buffer → copy → Consumer
```

---

# 746.204 — Canonical Flow: RPC

```text
service definition
       ↓
compiler
       ↓
client stub + server dispatch
       ↓
typed request
       ↓
AXIPC
       ↓
typed response
```

---

# 746.205 — Canonical Flow: Service Restart

```text
Client
  │
  ▼
request
  │
  X
service crash
  │
  ▼
endpoint failure
  │
  ▼
supervisor
  │
  ▼
service restart
  │
  ▼
new endpoint
  │
  ▼
reauthorize
  │
  ▼
reconnect
```

Pending non-idempotent operations không tự động replay.

---

# 746.206 — Canonical Flow: Remote IPC

```text
Application
    ↓
AXIPC
    ↓
IPC Bridge
    ↓
AXNETWORK
    ↓
secure transport
    ↓
remote AXIPC
    ↓
service
```

---

# 746.207 — Canonical Flow: Backpressure

```text
Producer
   ↓
queue
   ↓
capacity exhausted
   ↓
policy
 ┌───────┼─────────┐
 ▼       ▼         ▼
WAIT    REJECT    DROP
```

---

# 746.208 — Canonical Flow: Cancellation

```text
Client
  │
  ▼
Request
  │
  ▼
Server processing
  │
  ├──── cancel ────► cancellation request
  │
  ▼
Server checks policy
  │
  ▼
CANCELLED / COMPLETED
```

---

# 746.209 — Canonical Flow: Shared Ring Buffer

```text
Producer
   │
   ▼
reserve slot
   │
   ▼
write payload
   │
   ▼
release/publish
   │
   ▼
Consumer
   │
   ▼
acquire
   │
   ▼
read payload
   │
   ▼
consume/recycle
```

---

# 746.210 — Definition of Done

```text
BOOTSTRAP-746
STATUS: COMPLETE / FROZEN

AXIPC
 ├── Endpoint
 ├── Port
 ├── Channel
 ├── Queue
 ├── Message
 ├── Typed Message
 ├── Native Layout
 ├── Wire Layout
 ├── Request/Response
 ├── RPC
 ├── Streaming
 ├── Shared Memory
 ├── Zero-Copy
 ├── Ownership Transfer
 ├── Handle Transfer
 ├── Capability Transfer
 ├── SPSC
 ├── MPSC
 ├── MPMC
 ├── Backpressure
 ├── Flow Control
 ├── Batching
 ├── Notification
 ├── Wait Set
 ├── Deadline
 ├── Cancellation
 ├── Connection Lifecycle
 ├── Service Discovery
 ├── Versioning
 ├── Error Model
 ├── Idempotency
 ├── Supervision
 ├── Checkpoint
 ├── Replay
 ├── Simulation
 ├── Fault Injection
 ├── Security
 ├── Sandboxing
 ├── Capability Isolation
 ├── Privacy
 ├── Tracing
 ├── Performance Fast Path
 ├── NUMA
 ├── Platform Backends
 ├── AXMEMORY Integration
 ├── AXPROCESS Integration
 ├── AXNETWORK Bridge
 ├── AXAPPLICATION Integration
 ├── AXCOMPUTE Integration
 ├── AXMEDIA Integration
 ├── AXAUDIO Integration
 ├── AXGRAPHICS Integration
 ├── AI Boundary
 ├── Native API
 ├── 40 Formal Invariants
 └── IPC Runtime 5.0
```

**BOOTSTRAP-746 / AXIPC — ARCHITECTURAL BASELINE FROZEN.**

---

# BOOTSTRAP-747 — AXSYNC

**Native Synchronization, Atomicity & Concurrency Coordination Runtime — atomics, memory ordering, mutexes, spinlocks, semaphores, condition variables, events, barriers, latches, read/write locks, futex-like wait primitives, wait sets, lock-free structures, wait-free primitives, channels integration, cancellation-safe synchronization, priority inversion mitigation, deadlock diagnostics, deterministic synchronization replay, contention profiling, NUMA-aware synchronization, realtime synchronization, GPU/CPU fence integration, process-shared synchronization và Synchronization Runtime 5.0.**