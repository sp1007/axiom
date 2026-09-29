# BOOTSTRAP-204 — Distributed Systems, Consensus, Actors & Fault-Tolerant Computing

**TRẠNG THÁI: FROZEN / COMPLETED**

Mục tiêu của 204 là hoàn thiện tầng distributed systems mà **không làm phình Core language**.

Nguyên tắc trung tâm:

> **Distributed computing là sự mở rộng của Ownership + Message Passing + Async + Network + Storage + Failure Semantics, không phải một memory model mới.**

Axiom không cần:

- `actor` keyword bắt buộc
- distributed object primitive
- remote pointer
- distributed GC
- transparent remote function call
- distributed shared memory giả lập như local memory

---

# 204.1. Distributed system model

Một hệ thống Axiom phân tán được mô hình hóa:

```text
                    Cluster
                       │
        ┌──────────────┼──────────────┐
        ▼              ▼              ▼
      Node A         Node B         Node C
        │              │              │
     Process        Process        Process
        │              │              │
      Task           Task           Task
        │              │              │
     Actor          Actor          Actor
```

Mỗi node là một **failure domain** riêng.

---

# 204.2. Node identity

Node có logical identity:

```text
NodeId
```

Không dùng IP address làm identity.

Vì:

```text
IP ≠ process identity ≠ node identity
```

---

# 204.3. Process identity

Đã có:

```text
ProcessId
ProcessHandle
```

Distributed layer thêm:

```text
NodeId
ProcessId
```

để định danh:

```text
ProcessRef = (NodeId, ProcessId)
```

---

# 204.4. Actor identity

Actor:

```text
ActorId
```

là logical identity.

Không phải:

```text
memory address
thread ID
```

---

# 204.5. Actor không phải Core primitive

Actor có thể được xây từ:

```text
struct State
Mailbox
Task
Channel
Executor
```

Ví dụ conceptual:

```text
Actor
 ├── State
 ├── Mailbox
 └── Task
```

Không cần inheritance.

---

# 204.6. Actor message

Message là owned value:

```text
Message
```

gửi local:

```text
move
```

gửi remote:

```text
serialize
→ transport
→ deserialize
```

---

# 204.7. Distributed Send

Phân biệt rõ:

```text
Axiom Send
```

với:

```text
Network Send
```

`Send<T>` không có nghĩa `T` tự động serialize được.

Một type muốn đi qua network phải có contract:

```text
Serialize
Deserialize
```

hoặc protocol-specific representation.

---

# 204.8. No remote references

Axiom không có:

```text
Remote<T>
```

mà giả vờ giống local reference.

Thay vào đó:

```text
RemoteHandle<T>
```

là logical capability/identifier.

Mọi remote access đều có failure semantics.

---

# 204.9. Remote call không phải local call

Local:

```text
fn f(x: T) -> U
```

Remote:

```text
rpc.call(...)
```

có thể:

```text
timeout
failure
retry
partial execution
network partition
remote crash
```

Không được che giấu các semantics này.

---

# 204.10. Actor mailbox

Mailbox:

```text
Mailbox<M>
```

là queue ownership.

Khi enqueue:

```text
M
 ↓ move
Mailbox
```

Producer không còn sở hữu message.

---

# 204.11. Bounded mailbox

Mặc định nên ưu tiên:

```text
BoundedMailbox<M>
```

để tránh memory explosion.

Unbounded mailbox phải explicit.

---

# 204.12. Mailbox backpressure

Khi mailbox đầy:

```text
Send
 ├── Accepted
 ├── Pending
 └── Rejected
```

Không tự động allocate vô hạn.

---

# 204.13. Actor execution

Actor state được truy cập tuần tự bởi actor task:

```text
message
   ↓
actor task
   ↓
mutate state
   ↓
next message
```

Do đó phần lớn state actor không cần lock.

---

# 204.14. Actor state ownership

Actor sở hữu state:

```text
Actor
 └── State
```

Message handler có mutable access thông qua actor execution.

---

# 204.15. Actor state không được share tùy tiện

Không được tạo:

```text
Arc<ActorState>
```

rồi truy cập arbitrary mutation từ bên ngoài nếu không có synchronization contract.

---

# 204.16. Actor isolation

Actor isolation là library/compiler-checkable abstraction:

```text
Actor<T>
```

có thể cung cấp:

```text
send(message)
```

nhưng không expose `mut_view<T>` trực tiếp cho arbitrary caller.

---

# 204.17. Actor reentrancy

Phải phân biệt:

```text
process one message
```

và:

```text
await inside handler
```

Nếu actor handler `.await`, actor có thể:

- giữ state độc quyền trong toàn bộ await → serialization
- hoặc release actor state trước await → cho message khác chạy

Library contract phải xác định.

---

# 204.18. Không giữ sync lock qua await

Đã có invariant async:

```text
MutexGuard
```

không được sống qua `.await` mặc định.

Actor implementation phải tuân thủ tương tự.

---

# 204.19. Structured actors

Actor lifecycle nên có:

```text
spawn
join
shutdown
```

và structured ownership.

Detached actor phải explicit.

---

# 204.20. Actor supervision

Supervisor:

```text
Supervisor
 ├── Actor A
 ├── Actor B
 └── Actor C
```

có policy:

```text
Restart
Stop
Escalate
Ignore
```

---

# 204.21. Actor crash

Actor failure không nhất thiết làm process crash.

Có thể:

```text
Actor
 ↓ panic/error
Supervisor
 ↓
restart
```

Nhưng state cũ phải được coi là mất nếu không có persistence.

---

# 204.22. Actor panic ≠ distributed failure

Phân biệt:

```text
ApplicationError
ActorFailure
ProcessCrash
NodeFailure
NetworkPartition
StorageFailure
```

---

# 204.23. Failure domain

Axiom distributed API nên mô hình hóa:

```text
Task
Process
Node
Zone
Region
```

là các failure domains khác nhau.

---

# 204.24. Failure detector

Failure detector không được tuyên bố:

> "Node chắc chắn đã chết."

Nó chỉ có:

```text
Suspected
Reachable
Unreachable
Unknown
```

vì network partition.

---

# 204.25. Membership

Cluster membership:

```text
Member
 ├── NodeId
 ├── endpoint
 ├── state
 └── metadata
```

---

# 204.26. Membership state

Ví dụ:

```text
Joining
Alive
Suspect
Leaving
Dead
```

Các trạng thái này là protocol semantics.

---

# 204.27. Heartbeat

Heartbeat là liveness signal.

Không phải proof tuyệt đối node alive.

---

# 204.28. Clock

Distributed system không được giả định clock đồng bộ hoàn hảo.

Có:

```text
LocalTime
MonotonicTime
LogicalTime
```

tách biệt.

---

# 204.29. Logical clock

Có thể hỗ trợ library:

```text
LamportClock
VectorClock
HybridLogicalClock
```

---

# 204.30. Timestamp

Không dùng wall-clock timestamp làm correctness primitive nếu clock skew có thể phá invariant.

---

# 204.31. Event log

Distributed event log:

```text
EventLog
 ├── Offset
 ├── Event
 └── Partition
```

---

# 204.32. Log ownership

Event record là immutable owned value.

Consumer có thể nhận:

```text
EventView
```

hoặc owned `Event`.

---

# 204.33. Partition

Partition là logical execution/storage unit:

```text
PartitionId
```

Có thể được migrate giữa nodes.

---

# 204.34. Partition ownership

Node hiện tại sở hữu partition:

```text
Node A
 └── Partition 7
```

Migrate:

```text
A
 ↓ transfer protocol
B
```

không phải memory ownership trực tiếp.

---

# 204.35. Sharding

Sharding là library/framework.

Ví dụ:

```text
hash(key) → PartitionId
```

hoặc:

```text
range(key) → PartitionId
```

---

# 204.36. Consistent hashing

Có thể dùng:

```text
HashRing
```

nhưng ring state là ordinary data.

---

# 204.37. Replication

Replication model:

```text
Leader
 ├── Follower
 ├── Follower
 └── Follower
```

không phải shared mutable memory.

---

# 204.38. Replicated state

State machine:

```text
Command
 ↓
Replicated Log
 ↓
Deterministic Apply
 ↓
State
```

---

# 204.39. Deterministic state machine

Để replay chính xác, application state machine nên hạn chế:

```text
random
wall clock
unordered iteration
external IO
```

hoặc inject chúng qua explicit inputs.

---

# 204.40. Consensus

Consensus nằm trong distributed library:

```text
ConsensusNode
```

không phải Core.

---

# 204.41. Raft

Axiom standard library/framework có thể cung cấp implementation/reference:

```text
Raft
```

với:

```text
Leader
Follower
Candidate
```

---

# 204.42. Consensus log

Log entry:

```text
LogIndex
Term
Command
```

là immutable value.

---

# 204.43. Commit index

Consensus layer quản lý:

```text
commit_index
applied_index
```

Không được coi `append` = committed.

---

# 204.44. State machine apply

Chỉ command đã đạt commit condition mới được apply vào replicated state machine.

---

# 204.45. Consensus persistence

Consensus state phải persistent:

```text
current_term
voted_for
log
```

theo protocol.

Kết hợp trực tiếp với BOOTSTRAP-203 storage.

---

# 204.46. WAL + consensus

Có thể dùng:

```text
Consensus Log
 ↓
WAL
 ↓
Storage
```

và tận dụng async durable I/O.

---

# 204.47. Snapshot

Consensus snapshot:

```text
StateSnapshot
```

giúp truncate log.

Snapshot phải atomic/persistent.

---

# 204.48. Snapshot transfer

Node mới:

```text
snapshot
 ↓
remaining log
 ↓
catch up
```

---

# 204.49. Membership changes

Cluster membership changes phải là protocol operation.

Không sửa membership metadata tùy tiện.

---

# 204.50. Split brain

Axiom framework phải có cơ chế quorum/term/epoch phù hợp để tránh hai leader cùng commit conflicting state trong protocol hỗ trợ strong consistency.

---

# 204.51. Quorum

Quorum là protocol-specific concept.

Không hard-code:

```text
majority
```

vào Core.

---

# 204.52. Network partition

Partition:

```text
A ─────X───── B
```

không được biến thành memory safety failure.

Nó là distributed failure.

---

# 204.53. CAP semantics

Axiom không chọn một global CAP mode.

Mỗi distributed system xác định:

```text
consistency
availability
partition behavior
```

---

# 204.54. Strong consistency

Có thể xây bằng:

```text
consensus
linearizable operations
quorum
```

library-level.

---

# 204.55. Eventual consistency

Có thể xây bằng:

```text
replication
anti-entropy
CRDT
```

---

# 204.56. CRDT

CRDT library:

```text
GCounter
PNCounter
ORSet
LWWRegister
```

và custom CRDT.

---

# 204.57. CRDT ownership

Replica state là owned value.

Merge:

```text
merge(a, b) -> merged
```

có thể là pure function.

---

# 204.58. CRDT determinism

Merge phải deterministic theo CRDT contract.

---

# 204.59. Distributed transactions

Không đưa distributed transaction vào Core.

Library có thể hỗ trợ:

```text
TwoPhaseCommit
ThreePhaseCommit
Saga
TransactionalOutbox
```

tùy use case.

---

# 204.60. Saga

Saga:

```text
Step A
 ↓
Step B
 ↓
Step C
```

failure:

```text
Compensate C
 ↓
Compensate B
 ↓
Compensate A
```

là application-level semantics.

---

# 204.61. Transactional outbox

Kết hợp 203 + 204:

```text
Transaction
 ├── DB mutation
 └── Outbox event
        ↓
    Commit
        ↓
 Event publisher
```

giảm dual-write inconsistency.

---

# 204.62. Exactly-once

Không tuyên bố exactly-once network execution một cách mặc định.

Phải phân biệt:

```text
at-most-once
at-least-once
effectively-once
```

---

# 204.63. Idempotency key

Distributed operation có thể sử dụng:

```text
IdempotencyKey
```

để chống duplicate effects.

---

# 204.64. Distributed lock

Có thể cung cấp:

```text
DistributedLock
```

nhưng phải cảnh báo semantics:

```text
lease
expiration
failure
clock
partition
```

không giống local Mutex.

---

# 204.65. Lease

Lease có:

```text
LeaseId
Expiration
Owner
Epoch
```

và phải xử lý clock/renewal semantics.

---

# 204.66. Fencing token

Đây là primitive rất quan trọng cho distributed storage:

```text
FencingToken
```

giúp stale owner không tiếp tục ghi sau khi lease mất.

---

# 204.67. Epoch

Epoch/term có thể bảo vệ resource ownership logic:

```text
old epoch
```

không được overwrite:

```text
new epoch
```

---

# 204.68. Distributed resource ownership

Cần phân biệt:

```text
Axiom Ownership
```

và:

```text
Distributed Lease Ownership
```

Cái sau là protocol state, không phải compiler-enforced memory ownership.

---

# 204.69. Distributed handles

Handle:

```text
RemoteHandle<T>
```

không đảm bảo remote object tồn tại.

Mọi operation có thể trả:

```text
NotFound
Unavailable
Stale
EpochMismatch
```

---

# 204.70. No distributed GC

Axiom không có:

```text
distributed garbage collector
```

Resource lifetime remote được quản lý bởi protocol:

```text
lease
reference protocol
ownership message
explicit close
```

---

# 204.71. Distributed reference counting

Có thể tồn tại ở library:

```text
RemoteLease
```

nhưng không phải language primitive.

---

# 204.72. Failure-aware Drop

Không cho:

```text
Drop(remote_resource)
```

giả định remote cleanup luôn thành công.

Drop có thể:

```text
best-effort release
```

nhưng fallible cleanup phải có explicit async/Result operation.

---

# 204.73. Network failure khi Drop

Không được block destructor vô hạn để chờ network.

Đây là nguyên tắc quan trọng:

```text
Drop ≠ reliable distributed commit
```

---

# 204.74. Explicit close

Distributed resource:

```text
await resource.close()
```

có thể trả:

```text
Result<(), Error>
```

---

# 204.75. Distributed async

Mọi remote operation sử dụng cùng:

```text
Future
await
Cancellation
Deadline
Send
```

đã có.

Không tạo `DistributedFuture`.

---

# 204.76. Retry

Retry policy phải explicit:

```text
RetryPolicy
```

có thể dựa trên:

```text
exponential backoff
jitter
max attempts
deadline
idempotency
```

---

# 204.77. Retry ownership

Nếu request chứa owned value:

```text
Request
```

retry không được implicit clone.

Có thể:

```text
retry(request)
```

nếu request được `Clone`.

Hoặc buffer phải được giữ/replay theo contract.

---

# 204.78. Distributed serialization

Serializer phải deterministic khi protocol yêu cầu.

Không dựa vào hash-map iteration order ngẫu nhiên.

---

# 204.79. Schema evolution

Distributed services thường có nhiều version cùng chạy.

RPC/schema layer phải hỗ trợ:

```text
BackwardCompatible
ForwardCompatible
Versioned
UnknownFields
```

---

# 204.80. Rolling deployment

Node A:

```text
v1
```

Node B:

```text
v2
```

phải có compatibility contract.

Không giả định toàn cluster update atomically.

---

# 204.81. Protocol version negotiation

Handshake:

```text
supported versions
features
capabilities
```

---

# 204.82. Feature negotiation

Không dùng compile-time target features để giả định remote capabilities.

Remote capabilities phải runtime protocol data.

---

# 204.83. Distributed capability

Remote capability có thể là:

```text
CapabilityToken
```

nhưng không phải Axiom `mut_view`.

Nó là authorization/application-level capability.

---

# 204.84. Authentication

Node identity/authentication nằm ở security/network layer.

Không tự động coi `NodeId` là proof of identity.

---

# 204.85. Authorization

Authorization policy:

```text
Principal
Permission
Resource
Action
```

là application/security layer.

---

# 204.86. Secret ownership

Credentials/key material là owned sensitive resources.

Không copy implicit.

---

# 204.87. Observability

Distributed framework nên cung cấp:

```text
TraceId
SpanId
CorrelationId
```

nhưng chúng là ordinary data.

---

# 204.88. Structured logging

Log event:

```text
LogEvent
```

thay vì chỉ formatted strings.

Cho phép:

```text
JSON
binary
structured sink
```

---

# 204.89. Metrics

Metrics:

```text
Counter
Gauge
Histogram
Summary
```

library-level.

---

# 204.90. Distributed tracing

Async/task/network/RPC có thể propagate:

```text
TraceContext
```

qua explicit metadata.

Không compiler magic bắt buộc.

---

# 204.91. Deterministic testing

Distributed systems cần:

```text
VirtualClock
DeterministicScheduler
SimulatedNetwork
FaultInjector
```

để test reproducibly.

---

# 204.92. Network fault injection

Có thể inject:

```text
packet loss
delay
duplication
reordering
partition
connection reset
```

---

# 204.93. Storage fault injection

Kết hợp 203:

```text
partial write
fsync failure
disk full
corruption
crash
```

---

# 204.94. Process fault injection

Test:

```text
kill process
pause process
restart process
```

---

# 204.95. Node fault injection

Test:

```text
kill node
network partition
clock skew
disk failure
```

---

# 204.96. Model-based testing

Distributed state machine có thể được kiểm tra:

```text
reference model
        ↕
implementation
```

---

# 204.97. Linearizability testing

Concurrent distributed data structures có thể test bằng history:

```text
Operation
Invocation
Response
```

sau đó kiểm tra linearizability.

---

# 204.98. Consensus correctness

Consensus implementation phải test:

```text
leader election
term changes
message loss
duplication
reordering
partition
restart
snapshot
membership change
```

---

# 204.99. Compiler/AI integration

CompilerDB không cần hiểu Raft algorithm.

Nhưng AI/tooling có thể query:

```text
ownership
Send/Share
async
effects
resource dependencies
serialization
FFI
storage
```

Ví dụ:

```text
ax explain remote-send
```

có thể trả:

```text
Value moved into RPC request.
Serialization creates independent remote representation.
Original value is no longer owned by caller.
Remote execution may fail independently.
```

---

# 204.100. Distributed invariants — `ADIST`

### `ADIST-20`
Distributed systems shall remain library/framework abstractions above Core semantics.

### `ADIST-21`
Node identity shall be distinct from network address.

### `ADIST-22`
Process identity shall be distinct from memory identity.

### `ADIST-23`
Actor identity shall be logical identity, not physical address.

### `ADIST-24`
Actors shall not require inheritance or a special object model.

### `ADIST-25`
Actor state shall have explicit ownership.

### `ADIST-26`
Actor messages shall obey normal ownership semantics.

### `ADIST-27`
Network serialization shall be explicit.

### `ADIST-28`
Axiom `Send` shall not imply network serializability.

### `ADIST-29`
Remote references shall never masquerade as local safe references.

### `ADIST-30`
Remote operations shall expose failure semantics.

### `ADIST-31`
Distributed ownership shall remain distinct from Axiom memory ownership.

### `ADIST-32`
Distributed leases shall not be represented as ordinary memory ownership.

### `ADIST-33`
Failure detectors shall represent suspicion rather than absolute proof of failure.

### `ADIST-34`
Distributed systems shall not assume perfectly synchronized clocks.

### `ADIST-35`
Logical clocks shall remain distinct from wall-clock time.

### `ADIST-36`
Consensus shall remain a library-level protocol.

### `ADIST-37`
Consensus logs shall distinguish appended, committed and applied state.

### `ADIST-38`
Consensus persistence shall use the storage guarantees defined by the storage layer.

### `ADIST-39`
Consensus snapshots shall be atomically published according to storage contracts.

### `ADIST-40`
Network partitions shall not violate Axiom memory safety.

### `ADIST-41`
Distributed consistency semantics shall be explicit.

### `ADIST-42`
Exactly-once execution shall not be assumed by default.

### `ADIST-43`
Retry shall be explicit policy.

### `ADIST-44`
Retry shall not implicitly clone non-Copy values.

### `ADIST-45`
Idempotency shall be explicit when required for safe retry.

### `ADIST-46`
Distributed transactions shall remain library-level abstractions.

### `ADIST-47`
Saga compensation shall be explicit.

### `ADIST-48`
Transactional outbox semantics shall compose with the storage layer.

### `ADIST-49`
Distributed locks shall not be treated as equivalent to local Mutexes.

### `ADIST-50`
Lease expiration shall not rely on unsafe assumptions about wall-clock synchronization.

### `ADIST-51`
Fencing tokens shall be supported where stale writers must be prevented.

### `ADIST-52`
Distributed resource cleanup shall not depend on reliable network communication during Drop.

### `ADIST-53`
Fallible remote cleanup shall use explicit operations.

### `ADIST-54`
Distributed async operations shall reuse Axiom Future semantics.

### `ADIST-55`
Cancellation shall remain distinct from remote process termination.

### `ADIST-56`
RPC version negotiation shall be explicit.

### `ADIST-57`
Rolling deployments shall support explicit protocol compatibility.

### `ADIST-58`
Remote feature capabilities shall be runtime protocol facts, not compile-time assumptions.

### `ADIST-59`
Authentication shall remain distinct from logical node identity.

### `ADIST-60`
Authorization shall remain distinct from language ownership.

### `ADIST-61`
Distributed secrets shall obey explicit ownership and sensitive-data policies.

### `ADIST-62`
Distributed tracing context shall be explicit transferable data.

### `ADIST-63`
Distributed logging shall support structured events.

### `ADIST-64`
Distributed systems shall provide deterministic testing facilities.

### `ADIST-65`
Network, storage, process and node fault injection shall be supported by testing infrastructure.

### `ADIST-66`
Consensus implementations shall be subject to adversarial protocol testing.

### `ADIST-67`
Distributed data structures shall support model-based and history-based testing where applicable.

### `ADIST-68`
Generated RPC/distributed code shall pass normal Axiom verification.

### `ADIST-69`
Distributed abstractions shall not require garbage collection.

### `ADIST-70`
Distributed abstractions shall not require distributed GC.

### `ADIST-71`
Distributed abstractions shall not introduce remote pointers into Core.

### `ADIST-72`
Distributed abstractions shall compose with Axiom ownership, capability, async, network and storage models.

---

# Kiến trúc Distributed Systems hoàn chỉnh

```text
                         AXIOM DISTRIBUTED
                                │
              ┌─────────────────┼─────────────────┐
              │                 │                 │
            Actor              RPC             Event Log
              │                 │                 │
           Mailbox          Transport         Partition
              │                 │                 │
              └────────────┬────┴─────────────────┘
                           ▼
                       Cluster
                           │
             ┌─────────────┼─────────────┐
             ▼             ▼             ▼
           Node A        Node B        Node C
             │             │             │
          Storage       Storage       Storage
             │             │             │
             └─────────────┼─────────────┘
                           ▼
                      Replication
                           │
                      Consensus
                           │
                         WAL
                           │
                      Persistent DB
```

Điểm quan trọng là toàn bộ chuỗi này không cần thêm một memory model mới:

```text
Ownership
    +
Capability
    +
Async
    +
Network
    +
Storage
    +
Concurrency
    +
Failure semantics
```

là đủ để xây dựng tầng distributed.

---

# Một quyết định rất quan trọng được khóa

Axiom **không** cố biến distributed programming thành:

```axiom
remote_object.do_something()
```

và giả vờ nó giống:

```axiom
local_object.do_something()
```

Thay vào đó:

```text
LOCAL
  └── function call

ASYNC LOCAL
  └── Future

NETWORK
  └── RPC / message

DISTRIBUTED
  └── RPC + failure + consistency contract
```

Điều này giữ cho ngôn ngữ **đơn giản nhưng không đánh lừa programmer về semantics**.

---

# BOOTSTRAP-205 — Time, Scheduling, Real-Time, Timers & Temporal Semantics

**TRẠNG THÁI: NEXT**

Đây là bước tiếp theo rất đáng khóa vì Axiom hiện đã có:

```text
Async
Threads
Tasks
GPU
Network
Storage
Actors
Distributed systems
```

nhưng tất cả đều phụ thuộc vào **time**.

205 sẽ giải quyết:

```text
Instant
Duration
Deadline
Timeout
Timer
Interval
Scheduler
Monotonic clock
Wall clock
Logical clock
Virtual clock
Real-time scheduling
Priority
CPU affinity
NUMA
Timer wheel
High-resolution timer
Sleep
Wake
Periodic task
Frame timing
Audio timing
GPU synchronization
Distributed clock
Clock drift
```

và đặc biệt chốt một nguyên tắc quan trọng:

> **Time measurement, scheduling, timeout, wall-clock time và logical distributed time là những khái niệm khác nhau; Axiom không được gom tất cả vào một `Time` type.**