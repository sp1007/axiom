# BOOTSTRAP-388 — Axiom Distributed Computing, Cluster Execution & Data-Parallel Runtime Engine

Sau **387 — Global Resource Scheduling**, bước tiếp theo là mở rộng execution model từ **một máy** sang **nhiều máy / nhiều accelerator**.

Mục tiêu của 388 không phải biến Axiom thành một framework distributed riêng, mà là làm cho các abstraction đã có:

```text
Ownership
Tensor
Graph
Parallelism
Async
GPU
Execution Plan
Synchronization
```

có thể mở rộng thành:

```text
CPU
GPU
Node
Cluster
```

mà vẫn giữ nguyên triết lý:

> **Distributed execution là một execution strategy, không phải một kiểu dữ liệu đặc biệt của Core.**

---

# 1. Distributed không phải Core primitive

Không thêm vào Core:

```text
Cluster
RemoteObject
RemotePointer
DistributedClass
```

Thay vào đó, distributed computing nằm trên:

```text
Execution Domain
+
Storage Domain
+
Ownership
+
Async
+
Channel
+
Tensor
+
Graph
+
AEP
```

---

# 2. Execution Hierarchy

Axiom cần phân biệt:

```text
Process
  ↓
Node
  ↓
Device
  ↓
Worker
  ↓
Task
  ↓
Execution
```

Ví dụ:

```text
Cluster
 ├── Node 0
 │    ├── CPU
 │    ├── GPU0
 │    └── GPU1
 │
 └── Node 1
      ├── CPU
      ├── GPU0
      └── GPU1
```

---

# 3. Node

`Node` là một máy/host execution domain.

Không nhất thiết tương ứng với một process.

Một node có:

```text
CPU resources
Memory
Devices
Network interfaces
Runtime capabilities
```

---

# 4. Device

Device có thể là:

```text
CPU
GPU
NPU
FPGA
Accelerator
```

và thuộc một node.

---

# 5. Distributed Storage Domain

Bổ sung semantic storage:

```text
LOCAL
REMOTE
DISTRIBUTED
REPLICATED
SHARDED
```

Nhưng cần phân biệt **logical data** với physical placement.

---

# 6. Distributed Value

Một value bình thường:

```text
x : Tensor<f32>
```

không tự nhiên trở thành distributed tensor.

Distributed representation phải explicit.

Ví dụ:

```text
DistributedTensor<T>
```

là library abstraction.

---

# 7. Logical vs Physical Data

Một distributed tensor:

```text
X
```

có:

```text
logical shape
partition
placement
replication
local shards
```

Compiler phải hiểu cả hai lớp.

---

# 8. Sharding

Ví dụ:

```text
X[0..1000]
```

chia:

```text
Node0: 0..499
Node1: 500..999
```

Logical tensor vẫn là:

```text
[1000]
```

---

# 9. Partition Function

Compiler cần representation:

```text
Partition {
    logical_region
    owner
    storage
}
```

Ví dụ:

```text
[0,500) → Node0
[500,1000) → Node1
```

---

# 10. Ownership của Shard

Mỗi shard có ownership riêng.

Điều này cho phép:

```text
Node0 owns shard0
Node1 owns shard1
```

và tránh copy nếu computation chỉ cần local shard.

---

# 11. Remote Read

Nếu Node0 cần dữ liệu Node1:

```text
remote_read
```

phải là explicit execution operation.

Không có illusion rằng:

```text
ptr + offset
```

có thể tự nhiên truy cập memory máy khác.

---

# 12. Remote Write

Tương tự:

```text
remote_write
```

có synchronization/ownership semantics.

---

# 13. Remote Pointer

Không đưa distributed pointer vào safe Core.

Raw remote address nếu tồn tại chỉ là system/unsafe mechanism.

---

# 14. Message Passing

Axiom reuse:

```text
Channel<T>
```

conceptually:

```text
Node A
  ↓
message
  ↓
Node B
```

nhưng distributed channel cần runtime transport.

---

# 15. Transport Abstraction

Transport có thể là:

```text
TCP
UDP
RDMA
InfiniBand
RoCE
shared memory
PCIe
NVLink
```

Không hard-code vào language semantics.

---

# 16. Message Ownership

Điểm rất quan trọng.

Nếu:

```text
send(x)
```

thành công:

```text
ownership(x)
```

được chuyển cho receiver hoặc transport contract.

Không copy mặc định.

---

# 17. Failed Send

Nếu send thất bại:

```text
Result<(), T>
```

có thể trả lại ownership của `T`.

Giống semantics Channel đã định nghĩa.

---

# 18. Serialization

Không phải mọi distributed value đều có thể serialize.

Compiler/library cần trait:

```text
Serializable
```

hoặc tương đương.

---

# 19. Zero-copy Transport

Nếu transport hỗ trợ:

```text
RDMA
shared memory
GPU direct communication
```

compiler/runtime có thể truyền ownership của storage trực tiếp.

---

# 20. Serialization Elimination

Nếu hai endpoints có ABI/storage tương thích:

```text
serialize
→ network
→ deserialize
```

có thể được thay bằng:

```text
zero-copy transfer
```

nếu semantics vẫn tương đương.

---

# 21. Remote Procedure Call

RPC nên là library abstraction:

```text
rpc(call, endpoint)
```

không phải Core call semantics.

---

# 22. RPC Ownership

Input có thể:

```text
borrow/view
copy
move
```

tùy contract.

Compiler biết lựa chọn nào được phép.

---

# 23. Remote Async

RPC tự nhiên tích hợp:

```text
async
await
Future
Task
```

Ví dụ:

```text
result = await node.call(...)
```

không tạo thread mới.

---

# 24. Remote Failure

Distributed system có nhiều failure hơn local:

```text
timeout
disconnect
node failure
transport failure
serialization failure
remote panic
cancellation
```

Đây phải là `Result`/explicit error semantics.

Không dùng exception mặc định.

---

# 25. Partial Failure

Một cluster không có trạng thái đơn giản:

```text
success/failure
```

mà có thể:

```text
Node0 success
Node1 failed
Node2 success
```

Distributed API phải biểu diễn partial failure rõ ràng.

---

# 26. Cancellation

Nếu:

```text
await remote_call()
```

bị cancellation:

```text
local cancellation
```

không nhất thiết đồng nghĩa:

```text
remote computation terminated
```

Remote cancellation phải là explicit protocol.

---

# 27. Distributed Task

Một `Task` có thể:

```text
local
remote
migratable
```

nhưng execution identity phải rõ.

---

# 28. Task Migration

Migration không mặc định.

Nếu cần:

```text
Task state
```

phải có:

- serializable state;
- ownership transfer;
- execution contract;
- cancellation semantics.

---

# 29. Distributed Scheduling

AEP có thể lập execution plan:

```text
Node0:
    preprocessing

Node1:
    inference

Node2:
    postprocessing
```

Cost model thêm:

```text
network bandwidth
network latency
serialization
remote startup
```

---

# 30. Collective Operations

Các collective primitive:

```text
Broadcast
Reduce
AllReduce
AllGather
ReduceScatter
AllToAll
Barrier
```

được formalize.

---

# 31. Collective Ordering

Nếu cùng communicator có:

```text
AllReduce(A)
AllReduce(B)
```

thì thứ tự collective phải nhất quán giữa participants.

Sai ordering có thể gây deadlock hoặc sai semantics.

Compiler/runtime phải kiểm tra nếu static graph cho phép.

---

# 32. Communicator

Đề xuất:

```text
Communicator
```

là library/runtime abstraction.

Nó xác định participant set:

```text
{Node0, Node1, Node2, Node3}
```

---

# 33. Communicator Ownership

Communicator có lifetime rõ ràng.

Không được sử dụng sau khi communicator đã bị destroy.

---

# 34. Distributed Reduction

Reduction:

```text
sum
max
min
```

phải tuân numerical contract.

Đặc biệt:

```text
f32 sum
```

không được mặc định giả định associativity.

---

# 35. Deterministic Distributed Reduction

Nếu yêu cầu deterministic:

```text
fixed tree
fixed participant order
fixed reduction algorithm
```

hoặc semantic equivalent.

---

# 36. Data Parallel Training

Model parameters replicated:

```text
Node0: W
Node1: W
Node2: W
Node3: W
```

mỗi node xử lý batch riêng.

Gradient:

```text
g0
g1
g2
g3
```

sau đó:

```text
AllReduce(g)
```

---

# 37. Tensor Parallelism

Parameter shard:

```text
W0
W1
W2
W3
```

mỗi device sở hữu một phần.

Compiler phải propagate partition.

---

# 38. Pipeline Parallelism

Execution:

```text
Stage0
  ↓
Stage1
  ↓
Stage2
  ↓
Stage3
```

có thể overlap micro-batches.

---

# 39. Expert Parallelism

Mixture-of-Experts:

```text
tokens
 ↓
router
 ↓
expert partition
 ↓
remote dispatch
 ↓
expert compute
 ↓
combine
```

là một distributed graph.

---

# 40. Distributed Graph Algorithms

Graph engine có thể partition graph:

```text
Node0 owns vertices A
Node1 owns vertices B
```

Cross-partition edges tạo communication dependencies.

---

# 41. Ghost/Replica Data

Graph/sparse/PDE workloads có thể giữ:

```text
local data
+
ghost region
```

Ghost values phải có freshness/version semantics.

---

# 42. Halo Exchange

PDE/stencil:

```text
Node0 | Node1
```

cần trao đổi boundary.

Compiler có thể nhận dạng:

```text
halo exchange
```

và overlap:

```text
interior computation
+
boundary transfer
```

---

# 43. Distributed Tensor Halo

Tensor stencil tương tự:

```text
local region
+
halo
```

Compiler có thể tự schedule transfer.

---

# 44. Distributed Checkpoint

Checkpoint phải có:

```text
global state
node-local state
distributed tensor shards
RNG state
optimizer state
execution state
```

---

# 45. Consistent Checkpoint

Không được chỉ snapshot từng node tùy ý nếu muốn restart deterministic.

Cần:

```text
global checkpoint epoch
```

hoặc explicit consistency model.

---

# 46. Elastic Cluster

Cluster có thể thay đổi:

```text
Node join
Node leave
Node failure
```

Đây là runtime policy.

Static distributed programs có thể yêu cầu fixed topology.

---

# 47. Fixed Topology Mode

Compiler có thể biết:

```text
N = 8 nodes
```

từ build/runtime configuration.

Cho phép specialization.

---

# 48. Dynamic Topology Mode

Nếu số node dynamic:

```text
N runtime
```

execution plan phải có dynamic dispatch/partitioning.

---

# 49. Replication

Một object có thể có:

```text
replica0
replica1
replica2
```

nhưng replication semantics phải explicit:

```text
read replica
write primary
eventual consistency
strong consistency
```

---

# 50. Consistency Model

Không được dùng từ “distributed” như một consistency model.

Axiom phân biệt:

```text
Local
Strong
Causal
Eventual
Application-defined
```

và chỉ các library/runtime abstraction tương ứng mới có semantics đó.

---

# 51. Distributed Atomic

Atomic operation trên cluster không đồng nghĩa với CPU atomic.

Phải phân biệt:

```text
CPU atomic
GPU atomic
Node-local atomic
Distributed atomic
```

Distributed atomic thường là protocol/runtime primitive.

---

# 52. Distributed Lock

Không dùng:

```text
Mutex
```

trực tiếp cho network distributed lock.

Cần abstraction:

```text
DistributedMutex
```

với failure semantics rõ.

---

# 53. Distributed Barrier

Khác CPU barrier.

Nếu node chết:

```text
barrier
```

phải có explicit failure policy.

---

# 54. Distributed Time

Không giả định clocks giữa nodes giống nhau.

Compiler không được biến:

```text
local time
```

thành global ordering.

Nếu cần ordering:

```text
logical clock
vector clock
consensus timestamp
```

là library semantics.

---

# 55. Distributed Identity

`NodeId`, `WorkerId`, `TaskId`, `ShardId` phải phân biệt.

Không dùng memory address làm distributed identity.

---

# 56. Remote Capability

Capability:

```text
view<T>
```

không tự động có nghĩa:

```text
remote view
```

Remote access phải có storage/transport contract.

---

# 57. Remote Memory View

Có thể có:

```text
RemoteView<T>
```

nhưng semantic operation vẫn phải thể hiện network/remote latency.

Không tạo illusion zero-cost.

---

# 58. Cost Model

Distributed AEP bổ sung:

```text
network latency
network bandwidth
message size
serialization cost
collective cost
node startup
failure probability
```

---

# 59. Communication-Aware Optimization

Compiler có thể biến:

```text
compute
send A
compute
send B
```

thành:

```text
send A
compute
send B
```

nếu dependency cho phép.

---

# 60. Communication Fusion

Nhiều message nhỏ:

```text
send(A)
send(B)
send(C)
```

có thể gom:

```text
send(batch(A,B,C))
```

nếu ordering/ownership semantics vẫn đúng.

---

# 61. Communication Elimination

Nếu compiler chứng minh receiver đã có data:

```text
cached copy
```

có thể bỏ transfer.

Phải kiểm tra consistency/version.

---

# 62. Versioned Distributed Data

Distributed data có thể có:

```text
Version
Owner
Replica
Validity
```

để xác định replica còn hợp lệ hay không.

---

# 63. Distributed Cache

Cache chỉ là optimization nếu consistency semantics không bị thay đổi.

Không được tự biến:

```text
strong consistency
```

thành:

```text
eventual consistency
```

---

# 64. Fault Model

Execution contract có thể khai báo:

```text
FaultPolicy {
    retry
    fail_fast
    tolerate
    replicate
    checkpoint_restart
}
```

---

# 65. Retry Semantics

Retry chỉ safe nếu operation:

```text
idempotent
```

hoặc protocol có transaction/deduplication semantics.

Compiler không được tự retry arbitrary side effects.

---

# 66. Exactly-once

Không mặc định hứa:

```text
exactly once
```

Distributed systems phải phân biệt:

```text
at-most-once
at-least-once
effectively-once
exactly-once
```

theo abstraction.

---

# 67. Distributed Transactions

Không đưa transaction system vào Core.

Nếu cần:

```text
transaction
commit
rollback
```

là library/runtime.

---

# 68. Security Boundary

Node/network boundary là trust boundary.

Dữ liệu đi qua network phải có:

```text
serialization contract
authentication
authorization
encryption
integrity
```

nếu ứng dụng yêu cầu.

---

# 69. Unsafe Remote Access

`unsafe` không được tự biến network data thành trusted memory.

Remote bytes vẫn phải:

```text
validate
decode
construct typed value
```

trước khi vào safe semantic domain.

---

# 70. Distributed AI Execution

Khi kết hợp 385–387:

```text
Model
 ↓
AIR
 ↓
AEP
 ↓
Device placement
 ↓
Distributed partition
 ↓
Communication schedule
 ↓
GPU kernels
```

Đây là đường đi chính để Axiom hỗ trợ training/inference cluster mà không cần thay đổi Core language.

---

# 71. Distributed CompilerDB

Bổ sung:

```text
DistributedDB
NodeDB
NodeTopologyDB
NodeResourceDB
NodeDeviceDB

RemoteExecutionDB
RemoteTaskDB
RemoteCallDB
RemoteFutureDB

TransportDB
TransportEndpointDB
TransportCapabilityDB
TransportCostDB

DistributedStorageDB
DistributedTensorDB
DistributedShardDB
DistributedPartitionDB
DistributedReplicaDB
DistributedVersionDB

CommunicatorDB
CollectiveDB
CollectiveParticipantDB
CollectiveOrderingDB

DistributedScheduleDB
DistributedPlacementDB
DistributedPipelineDB
DistributedCommunicationPlanDB
DistributedTransferDB

DistributedReductionDB
DistributedDeterminismDB

DistributedFailureDB
FailurePolicyDB
RetryDB
TimeoutDB
CancellationDB
CheckpointRestartDB

DistributedConsistencyDB
ConsistencyModelDB
DistributedCacheDB
DistributedTransactionDB

DistributedSecurityDB
RemoteTrustDB
RemoteSerializationDB

DistributedAiDB
DataParallelDB
TensorParallelDB
PipelineParallelDB
ExpertParallelDB

DistributedGraphDB
DistributedSparseDB
DistributedPdeDB
DistributedSolverDB

DistributedCostModelDB
DistributedProofDB
DistributedVerificationDB
```

---

# 72. MIR additions

```text
DIST_BEGIN
DIST_END

NODE_ID
NODE_ASSIGN

REMOTE_SEND
REMOTE_RECEIVE
REMOTE_CALL
REMOTE_RETURN

REMOTE_TRANSFER
REMOTE_LOAD
REMOTE_STORE

SHARD_CREATE
SHARD_SPLIT
SHARD_MERGE
SHARD_MOVE

REPLICA_CREATE
REPLICA_SYNC
REPLICA_INVALIDATE

COMM_CREATE
COMM_DESTROY

COLLECTIVE_BEGIN
COLLECTIVE_END
ALL_REDUCE
ALL_GATHER
REDUCE_SCATTER
ALL_TO_ALL
DISTRIBUTED_BROADCAST

DIST_BARRIER
DIST_REDUCE

HALO_SEND
HALO_RECEIVE

DIST_CHECKPOINT
DIST_RESTART

DIST_TASK_SPAWN
DIST_TASK_JOIN
DIST_TASK_CANCEL

DIST_RETRY
DIST_TIMEOUT

DIST_CACHE_READ
DIST_CACHE_WRITE
DIST_CACHE_INVALIDATE
```

---

# 73. Distributed Proofs

```text
DistributedOwnershipProof
ShardOwnershipProof
PartitionProof
ReplicaConsistencyProof
RemoteAccessProof

SerializationProof
ZeroCopyTransferProof
RemoteCallProof

CollectiveParticipantProof
CollectiveOrderingProof
CollectiveReductionProof

DistributedSynchronizationProof
DistributedDeterminismProof

DevicePlacementProof
CommunicationScheduleProof
CommunicationEliminationProof

HaloExchangeProof
DistributedGraphProof
DistributedTensorProof
DistributedSolverProof

DistributedCheckpointProof
RestartConsistencyProof

RetrySafetyProof
IdempotenceProof
FailureHandlingProof

DistributedConsistencyProof
DistributedCacheProof

DistributedAIProof
DataParallelProof
TensorParallelProof
PipelineParallelProof
ExpertParallelProof
```

---

# 74. Invariants

### `ADIST-01`
Distributed execution phải preserve local Axiom semantics.

### `ADIST-02`
Distributed storage phải phân biệt logical data và physical placement.

### `ADIST-03`
Mọi shard phải có owner hoặc explicit replication semantics.

### `ADIST-04`
Remote memory không được tự động trở thành local safe pointer.

### `ADIST-05`
Remote transfer phải preserve ownership.

### `ADIST-06`
Move-based transfer không được tạo implicit duplicate ownership.

### `ADIST-07`
Failed transfer phải preserve hoặc explicitly resolve input ownership.

### `ADIST-08`
Serialization chỉ được tạo typed value sau validation.

### `ADIST-09`
Zero-copy transfer phải preserve storage provenance.

### `ADIST-10`
RPC phải preserve declared input/output ownership semantics.

### `ADIST-11`
Remote cancellation không được bị hiểu nhầm là guaranteed remote termination.

### `ADIST-12`
Partial failure phải được biểu diễn rõ ràng.

### `ADIST-13`
Collective participants phải có communicator semantics nhất quán.

### `ADIST-14`
Collective ordering phải được preserve.

### `ADIST-15`
Distributed reduction phải preserve numerical contract.

### `ADIST-16`
Deterministic distributed execution phải preserve declared ordering.

### `ADIST-17`
Sharding phải preserve logical tensor semantics.

### `ADIST-18`
Resharding phải preserve ownership và shape/layout semantics.

### `ADIST-19`
Replica cache không được phá vỡ declared consistency.

### `ADIST-20`
Distributed synchronization phải có happens-before semantics rõ ràng.

### `ADIST-21`
Distributed atomic phải không bị đánh đồng với machine atomic.

### `ADIST-22`
Distributed time không được dùng như global ordering nếu không có clock semantics.

### `ADIST-23`
Retry chỉ được tự động hóa khi operation có retry-safe contract.

### `ADIST-24`
Failure recovery không được rollback external side effects nếu abstraction không cung cấp transaction semantics.

### `ADIST-25`
Checkpoint/restart phải preserve declared global consistency.

### `ADIST-26`
Communication optimization phải preserve dependency graph.

### `ADIST-27`
Communication fusion phải preserve ordering và ownership.

### `ADIST-28`
Communication elimination phải có proof về data validity.

### `ADIST-29`
Distributed optimization phải preserve execution semantics bất kể topology.

### `ADIST-30`
Không sử dụng distributed features thì chương trình Axiom không được phát sinh distributed runtime dependency.

---

# 75. Kết quả kiến trúc

Sau 388, Axiom có thể biểu diễn cùng một computation ở nhiều cấp:

```text
              ONE PROGRAM
                   │
          ┌────────┴────────┐
          │                 │
       Local              Distributed
          │                 │
     ┌────┼────┐       ┌────┼────┐
     CPU  GPU  NPU     Node0 Node1 Node2
      │    │           │      │     │
     SIMD Kernel      CPU/GPU CPU/GPU ...
          │                 │
          └────────┬────────┘
                   │
                  AEP
                   │
             Global Plan
```

Điểm quan trọng là **distributed không phá vỡ memory/ownership model của Axiom**.

Ví dụ:

```text
send(buffer)
```

không phải một “magic distributed pointer”.

Nó là một **ownership transition qua execution/storage boundary**:

```text
Node A
 owns buffer
     │
     │ MOVE
     ▼
transport
     │
     ▼
Node B
 owns buffer
```

Nếu cần copy thì compiler/runtime phải có lý do rõ ràng. Nếu phần cứng hỗ trợ zero-copy/RDMA/GPU-direct, execution planner có thể thay đổi physical implementation mà không thay đổi semantics.

Đây cũng là bước cuối cùng để mô hình **AEP** có thể thực sự trở thành một global execution planner:

```text
Source
  ↓
MIR
  ↓
Domain IR
  ↓
AIR / Tensor / Graph / GPU / Parallel / Async
  ↓
AEP
  ↓
┌─────────────────────────────────────────┐
│ Global Execution Planning               │
│                                         │
│ CPU │ SIMD │ GPU │ Memory │ Async       │
│     │      │     │        │             │
│ Node │ Network │ Communication │ Cache  │
└─────────────────────────────────────────┘
  ↓
Native / GPU / Distributed execution
```

Từ đây, Axiom đã có nền tảng để đi vào các domain hệ thống lớn hơn mà **không cần mở rộng Core language một cách tùy tiện**.