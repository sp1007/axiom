# BOOTSTRAP-203 — Database, Storage Engine, Filesystem & Persistent Data

**TRẠNG THÁI: FROZEN / COMPLETED**

Mục tiêu:

> **Axiom phải cho phép xây filesystem, database, storage engine, cache, search engine và vector database hiệu năng native mà không cần GC, không ép programmer quản lý lifetime thủ công, đồng thời hỗ trợ crash consistency, mmap, async I/O và concurrency một cách có hệ thống.**

Nguyên tắc lớn:

```text
Persistent Data
      │
      ├── Ownership
      ├── Capability
      ├── Resource Lifetime
      ├── Async I/O
      ├── Concurrency
      ├── Memory Mapping
      └── Crash Consistency
```

Không tạo một "database memory model" riêng.

---

# 203.1. File là OS resource

Đã có resource model từ 184.

```text
File
 ├── OS handle
 ├── ownership
 ├── position/state
 └── I/O capability
```

Không coi file descriptor là `i32`.

---

# 203.2. File handle và file identity khác nhau

Phải phân biệt:

```text
FileHandle
FileId
Path
```

Ví dụ:

```text
path = "/data/a.db"
```

không đảm bảo file identity không đổi.

---

# 203.3. Path không phải file

Path là dữ liệu:

```text
Path
```

File là resource:

```text
File
```

Directory là resource/namespace:

```text
Directory
```

Không có implicit conversion thành ownership.

---

# 203.4. Read/write capability

File API có thể expose:

```text
ReadFile
WriteFile
ReadWriteFile
```

nhưng underlying ownership vẫn là resource ownership.

---

# 203.5. File view

Có thể tạo:

```text
FileView
```

là non-owning capability.

View không được sống sau owner.

---

# 203.6. Memory mapping

`mmap` là storage abstraction:

```text
File
 ↓
MemoryMap
 ↓
view<u8>
```

MemoryMap sở hữu mapping.

Không coi mmap là heap allocation.

---

# 203.7. mmap lifetime

Compiler phải đảm bảo:

```text
MemoryMap
```

còn sống khi:

```text
view
```

được sử dụng.

Không cần programmer viết lifetime.

---

# 203.8. Writable mmap

Writable mapping tạo mutable capability:

```text
mut_view<u8>
```

và áp dụng cùng alias rules.

---

# 203.9. File-backed memory

Storage domain:

```text
LOCAL
DYNAMIC
MAPPED
EXTERNAL
DEVICE
```

được giữ riêng.

---

# 203.10. Page

Database layer không nên trực tiếp xem:

```text
byte[]
```

là page.

Có abstraction:

```text
Page
```

với:

```text
PageId
PageSize
LSN
checksum
```

tùy storage engine.

---

# 203.11. Page ownership

Buffer pool sở hữu page frame.

Database component nhận capability:

```text
PageView
PageMutView
```

---

# 203.12. Page pinning

Database cần giữ page không bị eviction trong khi đang dùng.

Conceptually:

```text
PinnedPage
```

là ownership-bearing capability.

---

# 203.13. Pinning không phải pointer pin

Điều này khác với `Pin<T>` async.

Database pinning nghĩa:

> page không được eviction/relocation trong một storage policy cụ thể.

Không cần thêm Core `Pin`.

---

# 203.14. Buffer pool

```text
BufferPool
 ├── PageFrame
 ├── eviction
 ├── dirty tracking
 ├── pin count/capability
 └── synchronization
```

---

# 203.15. Page relocation

Nếu page buffer có thể relocate:

```text
live PageView
```

phải ngăn relocation.

Compiler có thể kiểm tra ở local cases; runtime pool quản lý global eviction.

---

# 203.16. Page cache và OS page cache

Không giả định:

```text
database buffer pool == OS page cache
```

Hai tầng khác nhau.

---

# 203.17. Direct I/O

Storage engine có thể dùng:

```text
O_DIRECT
Direct I/O
uncached I/O
```

thông qua platform abstraction.

Alignment contract phải rõ.

---

# 203.18. Async file I/O

Database engine có thể dùng:

```text
read_async
write_async
fsync_async
```

và reuse network async infrastructure.

---

# 203.19. Scatter/gather database I/O

Database có thể đọc:

```text
header
payload
metadata
```

bằng vectored I/O khi backend hỗ trợ.

---

# 203.20. WAL

Write-Ahead Log:

```text
Transaction
 ↓
WAL
 ↓
flush
 ↓
data page
```

là database semantic, không phải Core.

---

# 203.21. WAL ownership

Log record là owned value:

```text
LogRecord
```

WAL buffer có ownership rõ.

---

# 203.22. LSN

Log Sequence Number:

```text
LSN
```

là logical identity.

Không phụ thuộc memory address.

---

# 203.23. Durability

Phân biệt:

```text
written
flushed
durable
committed
```

Không coi `write()` = durable.

---

# 203.24. fsync

Durability API phải explicit:

```text
sync()
sync_data()
```

hoặc platform equivalent.

---

# 203.25. Transaction

Transaction là ordinary resource/state abstraction:

```text
Transaction
 ├── read
 ├── write
 ├── commit
 └── rollback
```

---

# 203.26. Transaction ownership

Transaction có ownership.

Không được sử dụng transaction sau:

```text
commit
rollback
drop
```

nếu API contract cấm.

---

# 203.27. Transaction state machine

```text
Active
  ├── Commit → Committed
  └── Rollback → Aborted
```

Invalid transitions phải được ngăn bởi API/type design hoặc runtime check.

---

# 203.28. Drop transaction

Drop không mặc định nghĩa:

```text
commit
```

An toàn hơn là:

```text
drop active transaction
→ rollback/abort according to engine contract
```

nhưng semantics phải explicit.

---

# 203.29. MVCC

MVCC là library/storage-engine mechanism.

Concept:

```text
RowVersion
 ├── value
 ├── created_tx
 └── deleted_tx
```

---

# 203.30. Snapshot

Snapshot là logical capability:

```text
Snapshot
```

có lifetime độc lập với physical address.

---

# 203.31. Snapshot isolation

Transaction đọc snapshot không có nghĩa dữ liệu bất biến vật lý.

Engine quản lý version visibility.

---

# 203.32. B-tree

B-tree implementation:

```text
BTree<K,V>
```

sử dụng storage abstraction.

Không phụ thuộc GC.

---

# 203.33. Node layout

Node có thể được compiler optimize:

```text
keys
values
child pointers/IDs
metadata
```

nhưng persisted representation phải explicit.

---

# 203.34. Persistent layout ≠ memory layout

Đây là invariant quan trọng.

```text
@repr(C)
```

không tự động tạo persistent format.

Database format phải có schema/layout contract riêng.

---

# 203.35. LSM Tree

Hỗ trợ:

```text
MemTable
 ↓
SSTable
 ↓
Compaction
```

---

# 203.36. MemTable

MemTable có thể dùng:

```text
BTree
SkipList
HashMap
```

là in-memory structures.

---

# 203.37. SSTable

SSTable có:

```text
Data blocks
Index blocks
Bloom filter
Footer
Checksum
```

và immutable storage.

---

# 203.38. Immutable storage

Immutable segment cho phép:

```text
many readers
```

và giảm synchronization.

Ownership model rất phù hợp.

---

# 203.39. Compaction

Compaction:

```text
SSTable A
SSTable B
SSTable C
   ↓
Compaction
   ↓
SSTable D
```

phải giữ source segments sống đến khi operation hoàn thành.

---

# 203.40. Async compaction

Compaction có thể chạy background task.

Không block foreground transaction unnecessarily.

---

# 203.41. Cancellation compaction

Cancellation phải đảm bảo:

```text
partial output
```

không được publish như một SSTable hợp lệ.

Temporary resource phải Drop/recover an toàn.

---

# 203.42. Atomic publication

Một segment mới chỉ trở thành visible sau khi:

```text
write
checksum
durability policy
metadata update
```

hoàn tất.

---

# 203.43. Crash consistency

Storage engine phải định nghĩa:

```text
what survives crash
```

theo durability profile.

Compiler không thể tự suy ra database crash semantics.

---

# 203.44. Recovery

Startup:

```text
open
 ↓
validate metadata
 ↓
read WAL
 ↓
redo/undo
 ↓
rebuild state
 ↓
ready
```

---

# 203.45. Recovery không phải panic

Corrupt database là:

```text
RecoveryError
CorruptionError
```

không mặc định là language panic.

---

# 203.46. Checksum

Persistent blocks có thể dùng:

```text
CRC
XXHash
cryptographic hash
```

tùy integrity/security requirement.

---

# 203.47. Torn write

Storage engine phải account cho:

```text
partial sector/page write
```

thông qua WAL/checksum/atomic metadata techniques.

---

# 203.48. Atomic rename

Filesystem có atomic operations tùy platform.

Axiom API phải mô tả contract thay vì giả định universal behavior.

---

# 203.49. Filesystem abstraction

High-level:

```text
FileSystem
Directory
File
Path
Metadata
```

Platform-specific implementation:

```text
NTFS
ext4
XFS
APFS
etc.
```

---

# 203.50. Directory iteration

Iterator có ownership/capability semantics.

Không trả dangling filename views.

---

# 203.51. File metadata

Metadata:

```text
size
timestamps
permissions
identity
type
```

là ordinary values.

---

# 203.52. Filesystem watch

Có:

```text
FileWatch
```

external event stream.

Events có thể:

```text
Created
Modified
Removed
Renamed
```

nhưng semantics phụ thuộc backend.

---

# 203.53. Virtual filesystem

VFS có thể được xây bằng traits:

```text
trait FileSystem
trait File
```

Không cần inheritance.

---

# 203.54. In-memory filesystem

Một implementation:

```text
MemoryFileSystem
```

phục vụ:

- tests
- sandbox
- embedded
- virtual environments

---

# 203.55. Object storage

Object storage:

```text
Bucket
Object
ObjectKey
ObjectMetadata
```

khác filesystem.

---

# 203.56. Blob

Large binary data:

```text
Blob
```

có thể lưu:

```text
file
mmap
database
object storage
remote
```

backend-independent interface.

---

# 203.57. Database value model

Không cần universal:

```text
Any
```

Database dynamic values có thể dùng explicit enum:

```text
Null
Bool
Int
Float
Text
Bytes
Array
Object
```

nếu database cần schema-less data.

---

# 203.58. Typed database

Typed database API có thể dùng generic:

```axiom
db.query<User>(...)
```

và compiler generate decoding.

---

# 203.59. Query language

SQL parser/query planner nằm ở library.

Không đưa SQL vào Core syntax.

---

# 203.60. Query plan

```text
SQL
 ↓
Parser
 ↓
AST
 ↓
Logical Plan
 ↓
Optimizer
 ↓
Physical Plan
 ↓
Execution
```

---

# 203.61. Query optimizer

Có thể dùng:

```text
cost model
statistics
indexes
join algorithms
vectorization
parallelism
```

---

# 203.62. Query execution

Execution engine có thể:

```text
row-at-a-time
vectorized
columnar
GPU
```

---

# 203.63. Columnar storage

Columnar:

```text
column A
column B
column C
```

phù hợp analytics/SIMD.

Axiom Tensor/SIMD model có thể hỗ trợ vectorized execution.

---

# 203.64. Vectorized database execution

Database engine có thể biến:

```text
filter
project
aggregate
```

thành SIMD kernels.

Không cần Tensor runtime.

---

# 203.65. Database + Tensor

AI/database integration:

```text
Database
 ↓
Columnar data
 ↓
Tensor view
 ↓
ML inference
```

có thể zero-copy nếu layout phù hợp.

---

# 203.66. Vector database

Vector index là library:

```text
Vector
Embedding
Index
```

Các thuật toán:

```text
HNSW
IVF
PQ
Flat
```

---

# 203.67. Vector storage

Embedding có thể lưu:

```text
f32
f16
bf16
int8
```

và dùng Tensor/SIMD backend.

---

# 203.68. Search index

Index types:

```text
BTree
Hash
Bitmap
InvertedIndex
SpatialIndex
VectorIndex
```

đều là library abstractions.

---

# 203.69. Cache

Cache:

```text
Cache<K,V>
```

phải phân biệt:

```text
ownership
eviction
expiration
synchronization
```

---

# 203.70. Cache value ownership

Cache có thể:

```text
own value
```

hoặc:

```text
own shared handle
```

nhưng không implicit clone.

---

# 203.71. Cache view

Không trả:

```text
view<T>
```

nếu eviction có thể xảy ra trước khi caller sử dụng.

Có thể trả:

```text
PinnedEntry
```

hoặc owned value.

---

# 203.72. Persistent cache

Cache backed by disk phải có:

```text
crash recovery
version
checksum
```

nếu durability được yêu cầu.

---

# 203.73. Database concurrency

Có thể sử dụng:

```text
Mutex
RwLock
Atomic
MVCC
Optimistic concurrency
```

đã có trong concurrency architecture.

Không tạo concurrency primitives riêng.

---

# 203.74. Lock manager

Database lock manager là library-level abstraction.

Compiler vẫn hiểu:

```text
MutexGuard
```

nếu implementation dùng Axiom synchronization.

---

# 203.75. Deadlock

Database transaction deadlock có thể xảy ra.

Engine có policy:

```text
detect
abort one transaction
retry
```

Không coi đây là language-level deadlock guarantee.

---

# 203.76. Async transaction

Transaction có thể chứa await nếu abstraction cho phép.

Nhưng:

```text
sync lock guard
```

không được giữ qua await theo async rules.

Database async transaction phải dùng async-aware synchronization hoặc release/reacquire.

---

# 203.77. Transaction + cancellation

Cancellation không được để transaction ở trạng thái half-published.

Cancellation phải map thành:

```text
rollback
abort
complete
```

theo transaction contract.

---

# 203.78. Connection + transaction

Database connection và transaction là distinct resources.

Không universal resource type.

---

# 203.79. Connection pool

Pool ownership:

```text
Pool
 ↓ checkout
ConnectionLease
 ↓
Transaction
 ↓
return
```

Lease không được trả về pool khi transaction/capabilities vẫn live.

---

# 203.80. Prepared statements

Prepared statement có dependency:

```text
Connection
```

nếu backend yêu cầu.

Compiler/resource system phải giữ connection sống đủ lâu.

---

# 203.81. Statement invalidation

Connection close có thể invalidate statements.

API phải encode/validate dependency.

---

# 203.82. Memory mapping database

Database có thể sử dụng:

```text
mmap
```

nhưng không được giả định mapped address ổn định qua process restart.

Persistent identity là:

```text
PageId
Offset
LSN
Key
```

không phải pointer.

---

# 203.83. Persistent pointer prohibition

Không cho safe persistent format chứa raw pointer như identity.

Pointer chỉ hợp lệ trong process/address-space contract.

---

# 203.84. Relative offsets

Storage formats có thể dùng:

```text
offset
```

thay vì pointer.

Khi load:

```text
offset → validated view/handle
```

---

# 203.85. Handle-based persistent structures

Persistent B-tree có thể dùng:

```text
PageId
SlotId
Offset
Generation
```

để tránh physical address dependence.

---

# 203.86. Stable storage identity

Database identity:

```text
DatabaseId
TableId
PageId
RowId
```

khác memory/storage address.

---

# 203.87. Row identity

Row identity có thể dùng:

```text
RowId
Generation
```

nhưng không đảm bảo physical location cố định nếu engine compact/rewrite.

---

# 203.88. Compaction and handles

Nếu record move:

```text
RowHandle
```

phải resolve thông qua logical identity/index.

Không giữ raw pointer.

---

# 203.89. Unsafe storage engine

Database implementation có thể dùng unsafe để:

- parse pages
- manipulate packed layout
- SIMD
- custom allocator
- mmap
- atomics
- lock-free structures

nhưng safe abstraction phải re-enter verifier.

---

# 203.90. Persistent format safety

Unsafe page parser phải establish:

```text
alignment
bounds
initialized fields
valid enum discriminant
checksum
version
```

trước khi expose safe type.

---

# 203.91. Database compile-time schema

Comptime có thể generate:

```text
schema
serializer
deserializer
indexes
migration metadata
```

---

# 203.92. Schema migration

Migration là executable transformation:

```text
v1
 ↓
migration
 ↓
v2
```

phải explicit.

Không compiler tự động sửa persistent data.

---

# 203.93. Schema version

Schema fingerprint có thể chứa:

```text
fields
types
constraints
indexes
encoding
version
```

---

# 203.94. Binary compatibility

Database file format compatibility khác Axiom ABI compatibility.

Không dùng `AbiFingerprint` thay cho schema fingerprint.

---

# 203.95. Persistent artifact identity

Có:

```text
SchemaFingerprint
StorageFormatFingerprint
```

riêng.

---

# 203.96. Database testing

Storage engines cần:

```text
crash injection
power-loss simulation
random I/O failures
corruption injection
concurrency stress
transaction fuzzing
```

---

# 203.97. Crash testing

Test:

```text
operation
 ↓
random crash point
 ↓
recovery
 ↓
verify invariants
```

phải là một phần conformance suite.

---

# 203.98. Database correctness

Reference model có thể:

```text
simple in-memory map
```

để differential-test storage engine.

---

# 203.99. Compiler integration

CompilerDB có thể expose:

```text
storage resource
async dependency
allocation
ownership
capability
effect
SIMD
```

nhưng không cần hiểu SQL semantics trong Core.

---

# 203.100. Storage invariants — `ASTORE`

### `ASTORE-20`
Filesystem, file and database functionality shall remain library/system layers.

### `ASTORE-21`
OS file handles shall not be treated as arbitrary integers in safe APIs.

### `ASTORE-22`
File ownership shall obey Axiom resource semantics.

### `ASTORE-23`
Memory mappings shall have explicit ownership and lifetime.

### `ASTORE-24`
Mapped views shall not outlive their mapping.

### `ASTORE-25`
Writable mappings shall obey normal mutable capability rules.

### `ASTORE-26`
Persistent representation shall remain distinct from ordinary memory representation.

### `ASTORE-27`
Persistent formats shall not rely on raw process pointers as identity.

### `ASTORE-28`
Persistent references shall use validated logical identifiers or offsets.

### `ASTORE-29`
Database pages shall have explicit identity and validity semantics.

### `ASTORE-30`
Pinned pages shall remain valid for the duration of dependent capabilities.

### `ASTORE-31`
Buffer eviction shall not invalidate live safe capabilities.

### `ASTORE-32`
Async storage operations shall preserve buffer lifetime until completion.

### `ASTORE-33`
Direct I/O shall respect alignment and storage contracts.

### `ASTORE-34`
WAL semantics shall distinguish written, flushed and durable states.

### `ASTORE-35`
Transaction state transitions shall be explicit.

### `ASTORE-36`
Dropping an active transaction shall not silently mean commit.

### `ASTORE-37`
Crash recovery shall not expose partially published storage state.

### `ASTORE-38`
Storage publication shall be atomic according to the selected filesystem/storage contract.

### `ASTORE-39`
Recovery shall distinguish corruption/failure from language panic.

### `ASTORE-40`
Checksum/integrity metadata shall be validated before trusted exposure.

### `ASTORE-41`
B-tree/LSM structures shall use explicit persistent representation contracts.

### `ASTORE-42`
In-memory layout and persistent layout shall not be conflated.

### `ASTORE-43`
Compaction shall preserve source resource lifetimes until completion.

### `ASTORE-44`
Cancelled storage operations shall not publish incomplete persistent artifacts.

### `ASTORE-45`
MVCC snapshots shall use logical validity rather than physical addresses.

### `ASTORE-46`
Row/page handles shall not depend on stable memory addresses.

### `ASTORE-47`
Connection/transaction/statement dependencies shall preserve resource lifetime.

### `ASTORE-48`
Database pools shall not return resources while dependent operations remain live.

### `ASTORE-49`
Database concurrency shall reuse Axiom synchronization semantics.

### `ASTORE-50`
Async database operations shall obey Axiom async suspension rules.

### `ASTORE-51`
Database deadlock/retry behavior shall remain library-level policy.

### `ASTORE-52`
Columnar/vectorized execution may use Axiom SIMD and tensor facilities.

### `ASTORE-53`
Vector indexes may reuse Axiom SIMD/tensor/GPU infrastructure.

### `ASTORE-54`
Database-to-tensor conversion may be zero-copy when layout and ownership permit.

### `ASTORE-55`
Cache views shall remain valid for their declared capability lifetime.

### `ASTORE-56`
Eviction shall not invalidate live safe capabilities.

### `ASTORE-57`
Schema fingerprints shall remain distinct from ABI fingerprints.

### `ASTORE-58`
Schema migrations shall be explicit executable transformations.

### `ASTORE-59`
Generated schema/serialization code shall pass normal Axiom verification.

### `ASTORE-60`
Storage unsafe code shall establish explicit validity contracts before exposing safe values.

### `ASTORE-61`
Storage systems shall support deterministic and reproducible tests where applicable.

### `ASTORE-62`
Crash testing shall be part of storage-engine correctness validation.

### `ASTORE-63`
Persistent artifacts shall have explicit format/version identity.

### `ASTORE-64`
Database runtimes shall be optional.

### `ASTORE-65`
Programs not using persistent storage shall not acquire storage runtime components.

### `ASTORE-66`
Storage engines shall not require a garbage collector.

### `ASTORE-67`
Storage engines shall support native async I/O without forcing thread-per-operation.

### `ASTORE-68`
Storage optimization shall preserve crash, ownership and concurrency semantics.

### `ASTORE-69`
AI/compiler tooling shall expose storage ownership, async, allocation and capability facts.

### `ASTORE-70`
Axiom shall support construction of native storage engines without requiring a separate memory-management model.

---

# Kiến trúc Storage cuối cùng

```text id="w3j9kr"
                       AXIOM STORAGE
                            │
              ┌─────────────┼─────────────┐
              │             │             │
         Filesystem      Database      Object Store
              │             │
          File/mmap     Transaction
              │             │
           Page       ┌─────┴─────┐
              │       │           │
        Buffer Pool   WAL        MVCC
              │       │           │
              └───────┼───────────┘
                      ▼
                Async Storage I/O
                      │
              ┌───────┼────────┐
              ▼       ▼        ▼
          io_uring   IOCP    POSIX/OS
```

Và một điểm rất quan trọng được khóa:

```text
Memory Address
     ≠
Storage Identity
     ≠
Logical Database Identity
```

Ví dụ:

```text
RAM address      → physical implementation detail
PageId           → storage identity
RowId            → logical identity
```

Điều này phù hợp hoàn toàn với quyết định trước đó của Axiom về **Value Identity / Storage Identity / Logical Identity**.

---

# BOOTSTRAP-204 — Distributed Storage, Consensus, Actors & Fault-Tolerant Systems

**TRẠNG THÁI: NEXT**

Sau 203, tầng local storage đã đủ nền. Bước tiếp theo nên khóa **distributed systems**, vì đây là nơi các mô hình ownership/concurrency/async/network/storage của Axiom phải hội tụ.

Phạm vi:

```text
Distributed Node
       │
       ├── Membership
       ├── Failure Detection
       ├── Leader Election
       ├── Consensus
       │     ├── Raft
       │     └── Paxos-like
       │
       ├── Replication
       ├── Sharding
       ├── Consistent Hashing
       ├── Distributed Transaction
       ├── WAL Replication
       ├── Event Log
       ├── Actor
       ├── Supervision
       ├── Cluster
       └── Fault Injection
```

Đặc biệt cần giải quyết một câu hỏi kiến trúc lớn:

> **Axiom có thể dùng ownership + message passing để xây distributed systems mạnh đến mức nào mà không cần biến Actor/Cluster/Distributed Object thành primitive của ngôn ngữ?**

Và cần chốt quan hệ:

```text
Axiom Ownership
       ↓
Local Channel
       ↓
Network RPC
       ↓
Actor Mailbox
       ↓
Replication Log
       ↓
Consensus
       ↓
Distributed State
```

Mục tiêu là giữ nguyên nguyên tắc xuyên suốt:

**Core càng ổn định và nhỏ, nhưng compiler hiểu càng sâu; mọi abstraction cấp cao — kể cả distributed systems — vẫn được xây trên cùng một ownership/capability/concurrency model.**