# BOOTSTRAP-393 — Axiom Distributed Systems, Actors, Messaging & Cluster Execution Engine

Sau **392 — Network Protocol, Transport & Distributed Communication**, bước tiếp theo là xây tầng **distributed execution**.

392 mới trả lời:

> “Làm thế nào để các tiến trình/máy giao tiếp?”

393 trả lời:

> **“Làm thế nào để biến nhiều tiến trình/máy thành một hệ thống tính toán thống nhất về mặt semantic, nhưng vẫn giữ rõ ràng ownership, failure, ordering và consistency?”**

Điểm quan trọng: **distributed computing không được đưa thành runtime bắt buộc của Axiom**. Nó phải là một domain layer có thể xây trên `Task + Channel + Network + Serialization + Storage`.

---

# 1. Phân biệt Local và Distributed

Axiom phải phân biệt rõ:

```text
Function
Task
Thread
Process
Node
Service
Actor
Cluster
```

Không được coi:

```text
remote_call()
```

là:

```text
function_call()
```

với chi phí lớn hơn.

Remote execution có failure semantics hoàn toàn khác.

---

# 2. Node

Node là một execution/storage boundary:

```text
Node {
    NodeId
    endpoints
    capabilities
}
```

`NodeId` là logical identity.

Không phải IP address.

Một node có thể thay đổi network endpoint mà identity vẫn giữ nguyên nếu cluster contract cho phép.

---

# 3. Process

Một node có thể có nhiều process:

```text
Node
 ├── Process A
 ├── Process B
 └── Process C
```

Process boundary là ownership/security/resource boundary.

---

# 4. Service

Service là logical endpoint:

```text
ServiceId
    ↓
EndpointSet
```

Service không nhất thiết tương ứng một process.

Có thể:

```text
1 service → N instances
```

---

# 5. Actor

Actor là abstraction:

```text
Actor
 ├── State
 ├── Mailbox
 └── Behavior
```

Nhưng **Actor không phải Core primitive**.

Có thể xây từ:

```text
Task
+
Channel
+
Ownership
+
Network
```

---

# 6. Actor State

Actor sở hữu state:

```text
Actor<TState>
```

Các message bên ngoài không được trực tiếp mutate state.

Thay vào đó:

```text
Message
 ↓
Mailbox
 ↓
Actor
 ↓
state mutation
```

Điều này tạo isolation tự nhiên.

---

# 7. Actor Ownership

Actor state có một owner semantic duy nhất.

Nếu actor di chuyển sang node khác:

```text
Node A
 ↓ migrate
Node B
```

ownership phải chuyển theo protocol.

Không phải memory alias xuyên process.

---

# 8. Mailbox

Mailbox:

```text
Mailbox<Message>
```

có:

```text
capacity
ordering
delivery
overflow policy
```

Không mặc định unbounded.

---

# 9. Mailbox Backpressure

Nếu mailbox đầy:

```text
send()
```

có thể:

```text
Pending
Reject
Drop
Block
Backpressure
```

policy phải explicit.

---

# 10. Message Ownership

Message gửi local:

```text
send(actor, message)
```

có thể chuyển ownership trực tiếp.

Nếu remote:

```text
encode(message)
→ transport
→ decode(message)
```

ownership semantic chuyển sang logical receiver sau khi delivery contract hoàn thành.

---

# 11. Serialization

393 sử dụng 391:

```text
Message<T>
 ↓
Schema<T>
 ↓
Codec
```

Không tạo serializer riêng cho distributed system.

---

# 12. Local Actor Optimization

Nếu compiler chứng minh actor cùng process:

```text
Actor A → Actor B
```

và message ownership có thể chuyển trực tiếp, có thể loại bỏ:

```text
serialization
network abstraction
temporary buffer
```

thành:

```text
direct queue transfer
```

nếu không có observable boundary.

---

# 13. Nhưng Remote Boundary Không Được Eliminate

Nếu application có observable:

```text
failure
latency
ordering
security
network traffic
```

compiler không được biến remote call thành local call.

---

# 14. Location Transparency — Có Giới Hạn

Axiom **không nên theo đuổi location transparency tuyệt đối**.

Ví dụ:

```text
service.get_user()
```

không được che giấu rằng operation có thể:

- timeout;
- fail;
- retry;
- duplicate;
- mất connection.

Distributed semantics phải xuất hiện trong type/result/effect contract.

---

# 15. Remote Call

Có thể có:

```text
remote fn get_user(id: u64) -> Result<User, RemoteError>
```

nhưng đây là library/comptime abstraction.

Compiler có thể generate RPC.

---

# 16. Remote Error

Cần phân biệt:

```text
ApplicationError
TransportError
ProtocolError
Timeout
AuthenticationError
PeerUnavailable
UnknownResult
```

Không gom tất cả thành `Error`.

---

# 17. Unknown Result

Một vấn đề cực kỳ quan trọng:

```text
client → request → server
```

server có thể đã commit operation nhưng response bị mất.

Client nhận:

```text
UnknownResult
```

Không được tự động retry nếu operation không idempotent.

---

# 18. Request Identity

Mỗi distributed request có:

```text
RequestId
```

để hỗ trợ:

```text
deduplication
retry
correlation
tracing
```

---

# 19. Idempotency Key

Operations có side effect có thể sử dụng:

```text
IdempotencyKey
```

để server nhận biết retry.

---

# 20. Exactly-Once

Axiom không nên tuyên bố:

```text
exactly_once
```

như một primitive vật lý.

Có thể cung cấp:

```text
effectively_once
```

khi protocol + durable deduplication + transaction semantics chứng minh được.

---

# 21. Delivery Semantics

Message delivery:

```text
AtMostOnce
AtLeastOnce
EffectivelyOnce
```

là semantic contract.

---

# 22. Ordering

Có thể chọn:

```text
Unordered
PerSender
PerKey
PerPartition
PerActor
Global
```

Global ordering đắt và không nên mặc định.

---

# 23. Causal Messaging

393 có thể định nghĩa:

```text
CausalMessage
```

với:

```text
TraceId
ParentMessageId
LogicalClock
```

nhưng không đưa causal ordering vào mọi message.

---

# 24. Logical Clock

Có thể hỗ trợ:

```text
LamportClock
VectorClock
HybridLogicalClock
```

như library types.

---

# 25. Distributed State

Distributed state có thể có:

```text
Replica<T>
```

với consistency contract.

---

# 26. Consistency Model

Các abstraction:

```text
Strong
Linearizable
Sequential
Causal
Eventual
Session
Snapshot
```

phải là **semantic contracts**, không chỉ documentation.

---

# 27. Replication

Replication:

```text
Primary
Replica1
Replica2
...
```

có thể sử dụng:

```text
log
snapshot
checkpoint
network
storage
```

đã có.

---

# 28. Replicated State Machine

Có thể xây:

```text
Command
 ↓
Replicated Log
 ↓
Deterministic Apply
 ↓
State
```

Đây là nền tảng cho:

- consensus;
- distributed database;
- cluster control plane.

---

# 29. Deterministic State Machine

Nếu state machine yêu cầu deterministic execution:

```text
randomness
time
network response
```

phải được đưa vào input.

Không được sử dụng hidden global state.

Điều này kết hợp trực tiếp với 376 Randomness.

---

# 30. Consensus

Consensus engine là library:

```text
Consensus<NodeState>
```

Không đưa Raft/Paxos vào Core.

393 chỉ cung cấp contracts để xây chúng.

---

# 31. Leader

Distributed service có thể có:

```text
Leader
Follower
Candidate
```

nhưng đây là protocol state.

---

# 32. Membership

Cluster membership:

```text
NodeJoined
NodeLeft
NodeSuspected
NodeFailed
```

failure detection không được coi là proof tuyệt đối về node failure.

---

# 33. Failure Detector

Distributed system không thể biết chắc:

```text
node crashed
```

hay:

```text
network partition
```

chỉ từ timeout.

Do đó semantic nên dùng:

```text
SuspectedUnavailable
```

khi thích hợp.

---

# 34. Network Partition

Partition:

```text
A ─── B
 \
  X
```

không đồng nghĩa process B đã chết.

Application phải xử lý distinction này.

---

# 35. Split Brain

Cluster membership cần fencing/epoch/term nếu protocol yêu cầu.

Ví dụ:

```text
Epoch 7
Epoch 8
```

old leader không được tiếp tục ghi nếu fencing contract đã invalidated nó.

---

# 36. Epoch

Logical epoch có thể bảo vệ:

```text
leadership
lease
resource ownership
membership
```

khỏi stale actors.

---

# 37. Lease

Lease:

```text
Lease<T>
```

có expiration semantics.

Nhưng wall-clock uncertainty phải được xử lý; lease không phải ownership tuyệt đối nếu clock assumptions không thỏa.

---

# 38. Distributed Lock

Distributed lock là library abstraction.

Nó phải khai báo:

```text
ownership
lease
expiration
failure
fencing
```

Không đồng nhất với `Mutex`.

---

# 39. Local Mutex vs Distributed Lock

```text
Mutex
```

dựa trên local memory synchronization.

```text
DistributedLock
```

dựa trên communication + protocol + persistence.

Hai abstraction không thể thay thế nhau.

---

# 40. Distributed Transaction

Có thể xây:

```text
DistributedTransaction
```

với:

```text
prepare
commit
abort
```

nhưng 2PC/3PC/Saga là implementation/policy.

---

# 41. Saga

Saga phù hợp khi transaction xuyên nhiều service.

Semantic:

```text
Step A
 ↓
Step B
 ↓
Step C
```

Nếu C fail:

```text
Compensation C
Compensation B
Compensation A
```

Compensation không phải rollback vật lý.

---

# 42. Distributed Effects

Effect system mở rộng:

```text
REMOTE_CALL
REMOTE_SEND
REMOTE_RECEIVE
DISTRIBUTED_COMMIT
DISTRIBUTED_COORDINATION
```

Compiler có thể dùng để kiểm tra:

- deterministic mode;
- comptime;
- realtime;
- retry;
- transaction.

---

# 43. Cluster Task

393 có thể định nghĩa:

```text
ClusterTask<T>
```

khác:

```text
Task<T>
```

ClusterTask có:

```text
placement
migration
retry
checkpoint
failure policy
```

---

# 44. Task Placement

Policy:

```text
Local
Node(node_id)
Any
Preferred(node_set)
GPU
CPU
```

Compiler/runtime có thể chọn placement khi policy cho phép.

---

# 45. Data Locality

Task có thể yêu cầu:

```text
DataLocality
```

Ví dụ:

```text
execute near dataset
```

thay vì:

```text
move dataset to computation
```

---

# 46. Distributed Dataflow

Pipeline:

```text
Source
 ↓
Partition
 ↓
Worker
 ↓
Shuffle
 ↓
Reduce
```

có thể xây từ:

```text
Stream
Channel
Parallel
Network
Storage
```

---

# 47. Distributed Parallelism

365 đã xử lý parallelism local.

393 bổ sung:

```text
DistributedParallelRegion
```

với:

```text
partition
shuffle
reduce
barrier
checkpoint
```

---

# 48. Distributed Reduce

Reducer phải có contract:

```text
associative
commutative
identity
numerical contract
```

giống 365.

Không được giả định floating-point addition associative.

---

# 49. Map

Distributed map:

```text
map(data)
```

có thể partition data.

Compiler/runtime có thể chọn:

```text
local
thread
GPU
remote node
```

nếu execution contract cho phép.

---

# 50. Shuffle

Shuffle là communication-heavy operation:

```text
partition A
 → network
partition B
```

Cost model phải tính:

```text
network bytes
serialization
CPU
latency
storage spill
```

---

# 51. Spill

Nếu worker thiếu RAM:

```text
memory
 ↓
local persistent storage
```

sử dụng 391.

---

# 52. Checkpoint

Distributed computation có thể checkpoint:

```text
task state
+
input position
+
partial result
```

để recovery.

---

# 53. Fault Recovery

Recovery policy:

```text
Restart
Retry
Resume
Replay
Recompute
Fail
```

không được implicit.

---

# 54. Deterministic Replay

Để replay:

```text
input
+
random seed/state
+
logical events
```

phải đủ để tái tạo execution nếu contract yêu cầu deterministic replay.

---

# 55. Distributed RNG

376 đã có RNG streams.

393 có thể phân phối:

```text
RngStream
```

theo:

```text
NodeId
TaskId
PartitionId
```

để tránh shared global RNG.

---

# 56. Distributed Tensor

Tensor engine có thể mở rộng:

```text
DistributedTensor<T>
```

với:

```text
replicated
sharded
partitioned
```

storage.

---

# 57. Tensor Sharding

Ví dụ:

```text
Tensor
 ├── Node A: rows 0..999
 ├── Node B: rows 1000..1999
 └── Node C: rows 2000..2999
```

Logical tensor vẫn là một abstraction.

---

# 58. Collective Operations

GPU/parallel semantics mở rộng thành:

```text
broadcast
all_reduce
reduce
all_gather
all_to_all
scatter
gather
barrier
```

cho cluster.

---

# 59. Collective Semantics

Collective phải có:

```text
group identity
participant set
ordering
completion
failure semantics
```

rõ ràng.

---

# 60. Distributed GPU

Một pipeline có thể:

```text
Node A GPU
      ↓
Network
      ↓
Node B GPU
```

Communication có thể sử dụng:

```text
GPU buffer
DMA
RDMA
```

nếu backend hỗ trợ.

---

# 61. RDMA

RDMA là optimization/backend.

Không nên đưa RDMA semantics vào Core.

Nhưng Buffer ownership contract phải đủ mạnh để library xây RDMA an toàn.

---

# 62. Remote Memory

Không nên tạo abstraction:

```text
RemotePointer<T>
```

trong Core.

Remote memory không phải local pointer.

Thay vào đó:

```text
RemoteBuffer
RemoteView
```

có explicit communication semantics.

---

# 63. Actor Migration

Actor migration cần:

```text
state snapshot
mailbox ordering
in-flight messages
epoch
destination
```

Không thể chỉ copy struct state.

---

# 64. Actor Supervision

Actor tree:

```text
Supervisor
 ├── Actor A
 ├── Actor B
 └── Actor C
```

failure policy:

```text
restart
stop
escalate
ignore
```

---

# 65. Supervision Không Phải Exception

Actor failure không được biến thành hidden exception.

Nó là execution/failure event.

---

# 66. Structured Distributed Concurrency

Có thể mở rộng structured concurrency:

```text
ClusterScope
 ├── Task A
 ├── Task B
 └── Task C
```

Scope ownership bao gồm:

```text
tasks
cancellation
results
resources
```

---

# 67. Detached Distributed Work

Detached work phải explicit:

```text
detach(cluster_task)
```

và hệ thống phải biết ownership/recovery semantics.

---

# 68. Distributed Cancellation

Cancellation:

```text
local request
 ↓
network propagation
 ↓
remote task
```

không được giả định instantaneous.

Remote cancellation là **best-effort/cooperative** trừ khi protocol có guarantee mạnh hơn.

---

# 69. Deadlines

Deadline nên truyền theo request:

```text
Request
 ├── deadline
 └── cancellation
```

để downstream biết thời gian còn lại.

---

# 70. Deadline Propagation

Ví dụ:

```text
A
 ↓ 100ms
B
 ↓ 70ms
C
```

B không nên tự cấp 100ms mới cho C nếu deadline toàn cục còn 70ms.

---

# 71. Tracing

Distributed execution nên hỗ trợ:

```text
TraceId
SpanId
ParentSpanId
```

nhưng tracing metadata phải optional.

Không được trở thành mandatory runtime overhead.

---

# 72. Observability

Instrumentation có thể capture:

```text
task
message
network
storage
GPU
```

và map về source/IR.

---

# 73. Security Boundary

Node/service communication phải có:

```text
identity
authentication
authorization
encryption
integrity
capability
```

theo 314 + 392.

---

# 74. Capability-Based RPC

Một service có thể cấp capability:

```text
Capability<Service>
```

thay vì chỉ:

```text
ServiceId
```

Điều này cho phép capability-oriented security.

---

# 75. Capability Revocation

Distributed capability có thể có:

```text
epoch
lease
revocation token
```

nhưng revocation semantics phải explicit.

---

# 76. Multi-Tenant Isolation

Distributed runtime có thể phân biệt:

```text
Tenant
Namespace
Service
Node
```

nhưng đây là platform/runtime layer.

---

# 77. Scheduler

Distributed scheduler có thể dùng:

```text
work stealing
data locality
load
GPU availability
network cost
```

Cost model kết hợp:

```text
Parallel
GPU
Network
Storage
```

---

# 78. Adaptive Placement

Nếu operation không có observable placement:

```text
compute()
```

runtime có thể chọn:

```text
CPU
GPU
Node A
Node B
```

nhưng chỉ nếu semantics contract cho phép.

---

# 79. Placement Observable

Nếu application phụ thuộc:

```text
NodeId
GPU identity
local filesystem
latency
security domain
```

placement trở thành observable.

Khi đó optimizer không được tự ý migrate.

---

# 80. Distributed Memory Model

Không mở rộng `HappensBefore` local thành toàn cluster.

393 dùng:

```text
CausalOrder
MessageOrder
CommitOrder
```

tùy abstraction.

---

# 81. Distributed Race

“Data race” local và distributed conflict khác nhau.

Ví dụ:

```text
Node A writes X
Node B writes X
```

không phải local memory race.

Nó là distributed consistency/conflict problem.

---

# 82. CRDT

Có thể hỗ trợ library abstractions:

```text
GCounter
PNCounter
ORSet
LWWRegister
Map
```

nhưng phải khai báo merge semantics.

---

# 83. Merge

Distributed merge phải có contract:

```text
associative
commutative
idempotent
```

nếu muốn reorder/duplicate-safe.

---

# 84. Event Sourcing

393 kết hợp 391:

```text
Command
 ↓
Event
 ↓
AppendLog
 ↓
State Projection
```

đây là một architecture tự nhiên của Axiom.

---

# 85. Event Replay

Replay:

```text
EventLog
 ↓
deterministic reducer
 ↓
state
```

có thể sử dụng comptime/generated reducer nhưng runtime execution vẫn bình thường.

---

# 86. Distributed Cache

Cache abstraction:

```text
LocalCache
DistributedCache
```

phải khác semantic.

Distributed cache có consistency/failure semantics.

---

# 87. Distributed Resource

Logical resource:

```text
DistributedResource<T>
```

có thể có:

```text
owner
lease
epoch
location
```

---

# 88. No Hidden Distributed Runtime

Một chương trình:

```text
fn main() {
    println("hello")
}
```

không được link:

```text
network runtime
cluster runtime
RPC runtime
```

Chỉ chương trình dùng distributed functionality mới kéo chúng vào.

---

# 89. Compiler Optimization

Compiler có thể:

```text
inline local actor message
eliminate serialization
specialize RPC codec
fuse stream stages
batch network messages
coalesce small messages
reuse buffers
pipeline communication/compute
overlap network/GPU
```

nhưng phải preserve observable distributed semantics.

---

# 90. CompilerDB

393 bổ sung:

```text id="7a8t2h"
DistributedDB
DistributedNodeDB
DistributedProcessDB
DistributedServiceDB
DistributedIdentityDB

ActorDB
ActorTypeDB
ActorStateDB
ActorBehaviorDB
ActorMailboxDB
ActorSupervisionDB
ActorMigrationDB

DistributedMessageDB
MessageRouteDB
MessageDeliveryDB
MessageOrderingDB
MessageDeduplicationDB
MessageRetryDB
MessageIdempotencyDB
MessageCorrelationDB

RemoteCallDB
RemoteFunctionDB
RemoteRequestDB
RemoteResponseDB
RemoteErrorDB

ClusterDB
ClusterMembershipDB
ClusterEpochDB
ClusterTermDB
ClusterLeaderDB
ClusterFailureDB
ClusterPartitionDB

DistributedTaskDB
DistributedPlacementDB
DistributedMigrationDB
DistributedCheckpointDB
DistributedRecoveryDB
DistributedReplayDB

DistributedParallelDB
DistributedMapDB
DistributedReduceDB
DistributedShuffleDB
DistributedCollectiveDB

DistributedTensorDB
TensorShardDB
TensorReplicaDB
TensorPartitionDB

DistributedConsistencyDB
ConsistencyModelDB
ReplicationDB
ReplicaDB
ReplicatedLogDB
ReplicatedStateMachineDB

ConsensusDB
ConsensusNodeDB
ConsensusTermDB
ConsensusVoteDB
ConsensusCommitDB

DistributedTransactionDB
DistributedPrepareDB
DistributedCommitDB
DistributedAbortDB
SagaDB
CompensationDB

DistributedLockDB
LeaseDB
FencingDB

CausalOrderDB
LogicalClockDB
VectorClockDB
HybridClockDB

DistributedRngDB
DistributedDeterminismDB

DistributedSecurityDB
DistributedCapabilityDB
CapabilityRevocationDB

DistributedTraceDB
DistributedSpanDB
DistributedObservabilityDB

DistributedCacheDB
DistributedResourceDB

DistributedCostModelDB
DistributedSchedulerDB
DistributedLocalityDB
DistributedNetworkCostDB
DistributedStorageCostDB

DistributedOptimizationDB
DistributedFusionDB
DistributedBatchingDB
DistributedCopyEliminationDB

DistributedProofDB
DistributedVerificationDB
```

---

# 91. MIR

```text id="9g8p4w"
NODE_ID
NODE_DISCOVER
NODE_MEMBERSHIP

SERVICE_RESOLVE
SERVICE_REGISTER
SERVICE_UNREGISTER

ACTOR_CREATE
ACTOR_SEND
ACTOR_RECEIVE
ACTOR_PROCESS
ACTOR_STOP
ACTOR_RESTART
ACTOR_MIGRATE

MAILBOX_SEND
MAILBOX_RECEIVE
MAILBOX_WAIT
MAILBOX_BACKPRESSURE

REMOTE_CALL
REMOTE_SEND
REMOTE_RECEIVE
REMOTE_REPLY

REQUEST_CREATE
REQUEST_CORRELATE
REQUEST_DEDUP
REQUEST_RETRY

DISTRIBUTED_TASK_SPAWN
DISTRIBUTED_TASK_JOIN
DISTRIBUTED_TASK_CANCEL
DISTRIBUTED_TASK_MIGRATE

PLACEMENT_SELECT
PLACEMENT_PIN
PLACEMENT_MOVE

CLUSTER_JOIN
CLUSTER_LEAVE
CLUSTER_SUSPECT
CLUSTER_EPOCH
CLUSTER_FENCE

REPLICA_CREATE
REPLICA_SYNC
REPLICA_APPLY

REPLICATED_LOG_APPEND
REPLICATED_LOG_COMMIT
REPLICATED_LOG_REPLAY

CONSENSUS_PROPOSE
CONSENSUS_VOTE
CONSENSUS_COMMIT

DIST_TX_BEGIN
DIST_TX_PREPARE
DIST_TX_COMMIT
DIST_TX_ABORT

LEASE_ACQUIRE
LEASE_RENEW
LEASE_RELEASE
LEASE_EXPIRE

DIST_LOCK_ACQUIRE
DIST_LOCK_RELEASE

DIST_BROADCAST
DIST_GATHER
DIST_SCATTER
DIST_ALL_GATHER
DIST_ALL_REDUCE
DIST_ALL_TO_ALL
DIST_BARRIER

DIST_PARTITION
DIST_SHUFFLE
DIST_REDUCE

DIST_CHECKPOINT
DIST_RESTORE
DIST_REPLAY

DIST_RNG_SPLIT

DIST_TRACE_BEGIN
DIST_TRACE_END
```

---

# 92. Proof System

```text id="x6sq7n"
NodeIdentityProof
ServiceIdentityProof

ActorOwnershipProof
ActorStateIsolationProof
ActorMailboxProof
ActorOrderingProof
ActorMigrationProof

MessageOwnershipProof
MessageDeliveryProof
MessageOrderingProof
MessageDeduplicationProof
MessageRetryProof
MessageIdempotencyProof

RemoteCallProof
RemoteFailureProof
RemoteTimeoutProof
UnknownResultProof

ClusterMembershipProof
ClusterEpochProof
ClusterFencingProof

DistributedTaskProof
PlacementProof
MigrationProof
CheckpointProof
RecoveryProof
ReplayProof

DistributedParallelProof
DistributedPartitionProof
DistributedShuffleProof
DistributedReductionProof
DistributedCollectiveProof

ReplicationProof
ConsistencyProof
ReplicaConvergenceProof
ReplicatedLogProof

ConsensusSafetyProof
ConsensusLivenessProof
ConsensusCommitProof

DistributedTransactionProof
PrepareProof
CommitProof
RollbackProof
SagaCompensationProof

LeaseProof
DistributedLockProof
FencingProof

CausalOrderProof
LogicalClockProof

DistributedDeterminismProof
DistributedRngProof

DistributedCapabilityProof
CapabilityRevocationProof

DistributedSecurityProof
DistributedTraceProof

DistributedTensorProof
TensorShardProof
TensorCollectiveProof

DistributedOptimizationProof
MessageBatchProof
SerializationEliminationProof
DistributedFusionProof

DistributedStorageProof
DistributedCostModelProof
DistributedVerificationProof
```

---

# 93. Invariants

### `ADIST-01`
Node identity không được đồng nhất với network address.

### `ADIST-02`
Service identity không được phụ thuộc physical process.

### `ADIST-03`
Actor state phải có ownership rõ ràng.

### `ADIST-04`
Actor bên ngoài không được trực tiếp mutate actor state.

### `ADIST-05`
Mailbox phải có ordering/delivery semantics xác định.

### `ADIST-06`
Mailbox không được mặc định unbounded.

### `ADIST-07`
Successful message transfer phải có ownership semantics xác định.

### `ADIST-08`
Failed message delivery không được âm thầm làm mất owned payload.

### `ADIST-09`
Remote call không được có semantics của local function call một cách ngầm định.

### `ADIST-10`
Remote timeout không được suy luận thành operation chắc chắn chưa xảy ra.

### `ADIST-11`
Retry phải tuân theo idempotency contract.

### `ADIST-12`
Request identity phải đủ để deduplicate khi protocol yêu cầu.

### `ADIST-13`
Exactly-once chỉ được tuyên bố khi protocol/storage proof thỏa contract.

### `ADIST-14`
Distributed ordering không được mặc định là global ordering.

### `ADIST-15`
Causal ordering không được đồng nhất với local memory happens-before.

### `ADIST-16`
Distributed conflict không được đồng nhất với local data race.

### `ADIST-17`
Cluster membership suspicion không được coi là proof node đã chết.

### `ADIST-18`
Stale leader/owner phải bị fencing khi protocol yêu cầu.

### `ADIST-19`
Lease expiration phải tuân theo clock/expiry contract.

### `ADIST-20`
Distributed lock không được có semantics của local Mutex một cách ngầm định.

### `ADIST-21`
Distributed transaction không được giả định rollback external side effects.

### `ADIST-22`
Saga compensation không được coi là physical rollback.

### `ADIST-23`
Distributed task cancellation là cooperative trừ khi backend có guarantee mạnh hơn.

### `ADIST-24`
Task migration phải preserve ownership và execution semantics.

### `ADIST-25`
Checkpoint/recovery phải preserve logical computation state theo contract.

### `ADIST-26`
Distributed reduction chỉ được reorder khi numerical/associativity contract cho phép.

### `ADIST-27`
Distributed tensor communication phải preserve shape/layout/storage semantics.

### `ADIST-28`
Remote/local optimization chỉ được eliminate boundary khi boundary không observable.

### `ADIST-29`
Distributed optimization không được thay đổi failure, ordering, delivery, consistency hoặc security semantics.

### `ADIST-30`
Nếu chương trình không sử dụng distributed functionality, compiler không được kéo theo distributed runtime bắt buộc.

---

# 94. Kiến trúc sau 393

Axiom lúc này đã có một chuỗi khá hoàn chỉnh:

```text
                APPLICATION
                     │
          ┌──────────┴──────────┐
          │                     │
       LOCAL                 REMOTE
          │                     │
      Task/Thread            Service
          │                     │
       Channel                Actor
          │                     │
       Parallel              Message
          │                     │
       SIMD/GPU             Transport
          │                     │
        Memory              Network
          │                     │
       Storage              Storage
```

và hai nhánh hội tụ ở các semantic nền tảng:

```text
Ownership
Capability
Effect
Async
Memory
Layout
Serialization
Storage
```

Đặc biệt, **393 không làm Axiom thành “distributed language”**. Nó chỉ đảm bảo rằng khi xây distributed systems, programmer không phải phá vỡ các nguyên tắc cốt lõi của Axiom để làm việc đó.

Một điểm quan trọng nữa: từ đây Axiom đã có đủ nền tảng để xây những hệ thống rất lớn như **database, message broker, distributed compute engine, AI cluster, actor system, server platform** mà vẫn giữ cùng một semantic model.