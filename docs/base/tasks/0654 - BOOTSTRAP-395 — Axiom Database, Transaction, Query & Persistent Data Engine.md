# BOOTSTRAP-395 — Axiom Database, Transaction, Query & Persistent Data Engine

Sau **394 — Security, Capability, Cryptography & Trusted Computing**, bước tiếp theo hợp lý là **Persistent Data & Database Engine**.

Mục tiêu không phải biến Database thành Core. Mục tiêu là để Axiom có thể xây được:

- embedded database;
- relational database;
- key-value store;
- column store;
- time-series database;
- vector database;
- graph database;
- distributed database;

mà **không cần một object model, GC, ORM runtime hay database-specific language bắt buộc**.

Nguyên tắc chính:

> **Database là một specialization của Storage + Data Layout + Transaction + Query + Parallelism + Serialization + Distributed Systems.**

---

# 1. Database không phải một primitive

Core chỉ cần:

```text
Memory
Ownership
Capability
I/O
Storage
Concurrency
Transaction primitives
```

Database nằm phía trên.

```text
Axiom Core
    ↓
Storage / I/O
    ↓
Data Layout
    ↓
Transaction
    ↓
Database
    ↓
Query / Index / Analytics
```

---

# 2. Persistent Data

Phân biệt:

```text
Value
MemoryObject
PersistentObject
Record
Page
Block
Segment
Log
Snapshot
```

Một `struct` trong RAM không tự động trở thành persistent record.

---

# 3. Persistence Contract

Persistent data cần xác định:

```text
durability
ordering
atomicity
consistency
recovery
version
schema
```

Không được giả định:

```text
write() == durable
```

---

# 4. Database Handle

Database resource:

```text
Database
```

là owning resource.

Có thể có:

```text
DatabaseView
Transaction
Cursor
Query
RecordView
```

Các view không được sống lâu hơn resource tương ứng.

---

# 5. Transaction

Transaction là semantic abstraction:

```text
Transaction<T>
```

với:

```text
begin
read
write
commit
abort
```

---

# 6. Transaction Ownership

Transaction có owner rõ ràng.

Không implicit shared mutable transaction.

Nếu muốn chia sẻ:

```text
TransactionHandle
```

phải có synchronization semantics.

---

# 7. ACID

Database transaction có thể cung cấp:

```text
Atomicity
Consistency
Isolation
Durability
```

nhưng mỗi database implementation có thể cung cấp mức contract khác nhau.

---

# 8. Isolation Level

Có thể định nghĩa:

```text
ReadUncommitted
ReadCommitted
RepeatableRead
Snapshot
Serializable
```

và các model khác.

Không nên giả định mọi database đều có cùng isolation.

---

# 9. MVCC

MVCC là implementation strategy:

```text
Record
 ├── Version 1
 ├── Version 2
 └── Version 3
```

Transaction đọc snapshot thích hợp.

Không đưa MVCC vào Core.

---

# 10. Snapshot

Snapshot:

```text
Snapshot<T>
```

là logical view tại một consistency point.

Snapshot có thể được implement bằng:

- MVCC;
- copy-on-write;
- page version;
- immutable segments.

---

# 11. Write-Ahead Log

WAL:

```text
Transaction
 ↓
WAL
 ↓
Data Pages
 ↓
Commit
```

cho phép recovery.

---

# 12. WAL Semantics

Phải phân biệt:

```text
logical commit
physical write
flush
durable commit
```

Ví dụ:

```text
commit()
```

không nhất thiết có nghĩa dữ liệu đã nằm trên stable storage nếu durability contract không yêu cầu.

---

# 13. Commit Durability

Có thể có:

```text
Durability::Memory
Durability::OS
Durability::Stable
```

hoặc tương đương.

---

# 14. Checkpoint

Database có thể:

```text
WAL
 ↓
Checkpoint
 ↓
compact/reclaim
```

Checkpoint không được làm mất committed transaction.

---

# 15. Recovery

Recovery:

```text
Open
 ↓
Inspect checkpoint
 ↓
Replay WAL
 ↓
Validate
 ↓
Database Ready
```

---

# 16. Crash Recovery

Database engine phải phân biệt:

```text
CleanShutdown
Crash
PartialWrite
CorruptPage
MissingSegment
IncompleteCommit
```

---

# 17. Page

Storage page:

```text
Page {
    page_id
    generation
    payload
    checksum
}
```

nhưng physical layout implementation-defined.

---

# 18. Page Identity

`PageId` là logical identity.

Không phải memory address.

---

# 19. Segment

Database có thể tổ chức:

```text
Database
 ├── Segment
 ├── Segment
 └── Segment
```

Segment có thể immutable hoặc mutable.

---

# 20. Append-Only

Một số storage engine có thể dùng:

```text
append
```

thay vì in-place mutation.

Điều này phù hợp với:

- event sourcing;
- time series;
- analytics;
- log databases.

---

# 21. Compaction

Compaction:

```text
Segment A
Segment B
Segment C
    ↓
Compaction
    ↓
Segment D
```

phải giữ semantics của visible records.

---

# 22. Tombstone

Deletion trong LSM/append-only storage có thể là:

```text
Tombstone
```

thay vì physical deletion ngay lập tức.

---

# 23. Garbage Collection ≠ Database Reclamation

Database compaction/reclamation **không phải GC của programming language**.

Đây là storage-level lifecycle.

---

# 24. Schema

Schema:

```text
Schema<T>
```

có thể được compiler biết tại compile-time.

Ví dụ:

```text
struct User {
    id: u64
    name: Text
    age: u32
}
```

Database schema có thể derive từ type.

---

# 25. Nhưng Type ≠ Schema

Thay đổi struct:

```text
User
```

không tự động có nghĩa database schema đã migrate.

Schema migration phải explicit.

---

# 26. Schema Version

```text
SchemaVersion
```

được gắn với persistent representation.

---

# 27. Migration

Migration:

```text
Schema V1
    ↓
Migration
    ↓
Schema V2
```

phải có:

```text
input schema
output schema
transformation
compatibility
failure behavior
```

---

# 28. Backward Compatibility

Có thể hỗ trợ:

```text
read old schema
write new schema
```

nếu codec/schema contract cho phép.

---

# 29. Record

Record có thể được biểu diễn:

```text
Record<T>
```

nhưng physical layout compiler-controlled.

---

# 30. Column Store

Logical record:

```text
User {
    id
    name
    age
}
```

có thể physicalize thành:

```text
IDs[]
Names[]
Ages[]
```

đúng với Data Layout Engine 389.

---

# 31. Row Store

Hoặc:

```text
User[]
```

với row-oriented storage.

Compiler/database cost model lựa chọn representation khi contract cho phép.

---

# 32. Hybrid Storage

Có thể sử dụng:

```text
hot columns
cold columns
compressed columns
dictionary encoded columns
```

tùy workload.

---

# 33. Compression

Compression là storage optimization.

Các abstraction:

```text
CompressedColumn
CompressedSegment
CompressedPage
```

không được thay đổi logical semantics.

---

# 34. Encoding

Có thể sử dụng:

```text
dictionary
RLE
delta
bit packing
frame-of-reference
```

và compiler có thể chọn theo statistics.

---

# 35. Index

Index:

```text
Index<K,V>
```

là acceleration structure.

Index không phải source of truth.

---

# 36. Index Correctness

Nếu index mất đồng bộ với base table:

```text
query
```

không được trả kết quả sai.

Index update phải nằm trong transaction contract.

---

# 37. B-Tree

Library cung cấp:

```text
BTreeIndex
```

cho ordered lookup/range scan.

---

# 38. Hash Index

```text
HashIndex
```

phù hợp equality lookup.

Hash index không đảm bảo ordering.

---

# 39. LSM Tree

Có thể hỗ trợ:

```text
MemTable
 ↓
WAL
 ↓
SSTable
 ↓
Compaction
```

làm storage engine.

---

# 40. SSTable

SSTable immutable:

```text
SSTable {
    sorted_keys
    blocks
    index
    bloom_filter
}
```

là một physical representation.

---

# 41. Bloom Filter

Bloom filter có false positives nhưng không được false negative nếu implementation đúng.

Query:

```text
filter says absent
```

→ có thể bỏ qua segment.

```text
filter says present
```

→ phải kiểm tra thật.

---

# 42. Query

Query abstraction:

```text
Query<T>
```

có thể compile thành query plan.

---

# 43. Query Pipeline

Ví dụ:

```text
Scan
 ↓
Filter
 ↓
Project
 ↓
Join
 ↓
Aggregate
 ↓
Sort
```

---

# 44. Query IR

Cần compiler-level representation:

```text
AQIR
```

Axiom Query IR.

Không nhất thiết expose cho programmer.

---

# 45. Query Operations

AQIR có thể chứa:

```text
SCAN
FILTER
PROJECT
JOIN
GROUP
AGGREGATE
SORT
LIMIT
OFFSET
DISTINCT
UNION
INTERSECT
DIFFERENCE
WINDOW
```

---

# 46. Typed Query

Axiom có thể cho phép query type-safe.

Ví dụ conceptual:

```text
query(User)
    .filter(u => u.age > 18)
    .select(u => u.name)
```

Compiler biết:

```text
input type
output type
field existence
predicate type
```

---

# 47. Không Cần ORM

Đây là điểm quan trọng.

Axiom không cần:

```text
class UserModel
ORM Entity
reflection-heavy mapper
runtime proxy
```

Compiler có thể generate query/storage mapping từ type.

---

# 48. Query Compilation

Nếu query static:

```text
query(User)
    .filter(...)
```

compiler có thể:

```text
parse
type-check
specialize
optimize
compile
```

thành execution pipeline native.

---

# 49. Dynamic Query

Dynamic query vẫn được hỗ trợ:

```text
DynamicQuery
```

nhưng sẽ cần runtime query planner.

---

# 50. Query Optimization

Optimizer có thể thực hiện:

```text
predicate pushdown
projection pushdown
join reordering
constant folding
filter fusion
aggregation pushdown
index selection
partition pruning
```

---

# 51. Predicate Pushdown

Ví dụ:

```text
Scan
 ↓
Filter(age > 18)
```

có thể trở thành:

```text
IndexScan(age > 18)
```

nếu index tồn tại.

---

# 52. Projection Pushdown

Nếu query chỉ cần:

```text
id
name
```

storage engine không cần đọc:

```text
large_blob
```

nếu layout cho phép.

---

# 53. Join

Join types:

```text
Inner
Left
Right
Full
Semi
Anti
Cross
```

phải có semantic rõ ràng.

---

# 54. Join Algorithms

Planner có thể chọn:

```text
NestedLoop
HashJoin
MergeJoin
IndexJoin
BroadcastJoin
PartitionedJoin
```

theo cost model.

---

# 55. Parallel Query

Query execution có thể sử dụng:

```text
SIMD
parallel workers
GPU
distributed nodes
```

khi semantics cho phép.

---

# 56. Vectorized Execution

Thay vì:

```text
record by record
```

có thể xử lý:

```text
batch/vector
```

để tận dụng SIMD.

---

# 57. GPU Query

Columnar numerical workload có thể lower:

```text
Scan
Filter
Aggregate
Join
```

thành GPU kernels.

---

# 58. Distributed Query

Có thể:

```text
Scan Node A
Scan Node B
      ↓
Shuffle
      ↓
Join
      ↓
Aggregate
```

dựa trên 393.

---

# 59. Query Cost Model

Cost model tính:

```text
CPU
memory
cache
SIMD
GPU
network
storage
compression
decompression
```

---

# 60. Statistics

Query planner dùng:

```text
row_count
distinct_count
histogram
null_fraction
min/max
distribution
```

Statistics là optimization metadata.

Sai statistics không được làm thay đổi correctness.

---

# 61. Transactions + Query

Query execution phải giữ:

```text
Snapshot
Transaction
Visibility
Isolation
```

đúng với isolation contract.

---

# 62. MVCC Visibility

Record có thể có:

```text
created_tx
deleted_tx
```

hoặc physical equivalent.

Visibility được quyết định bởi transaction snapshot.

---

# 63. Concurrent Write

Hai transaction cùng sửa record phải tuân theo isolation policy:

```text
conflict
serialize
MVCC
retry
```

---

# 64. Serializable Execution

Nếu yêu cầu Serializable:

```text
concurrent execution
```

phải tương đương một serial execution hợp lệ.

---

# 65. Optimistic Concurrency

Có thể sử dụng:

```text
version check
compare-and-swap
validation
commit
```

---

# 66. Pessimistic Concurrency

Có thể sử dụng:

```text
row lock
page lock
table lock
```

nhưng lock semantics nằm trong database engine, không phải Axiom Mutex.

---

# 67. Deadlock

Database lock manager có thể phát hiện:

```text
T1 → waits T2
T2 → waits T1
```

và chọn:

```text
abort one transaction
```

---

# 68. Transaction Retry

Retry transaction chỉ an toàn khi transaction body có thể được chạy lại theo declared contract.

External side effects:

```text
network
file
device
```

phải được xử lý riêng.

---

# 69. Pure Transaction Body

Có thể có:

```text
transaction {
    ...
}
```

với effect restrictions.

Compiler biết body có:

```text
DB_READ
DB_WRITE
NETWORK
IO
RANDOM
TIME
```

hay không.

---

# 70. Deterministic Transaction

Transaction có thể yêu cầu deterministic execution để hỗ trợ:

```text
replication
replay
consensus
```

---

# 71. Database Replication

Có thể dùng:

```text
Primary
Replica
```

hoặc:

```text
ReplicatedLog
```

từ 393.

---

# 72. Logical Replication

Replication có thể truyền:

```text
logical changes
```

thay vì physical pages.

---

# 73. Physical Replication

Hoặc:

```text
WAL/page changes
```

cho replica.

---

# 74. Consistency

Database có thể expose:

```text
Strong
Snapshot
Eventual
ReadYourWrites
MonotonicRead
```

tùy engine.

---

# 75. Embedded Database

Axiom phải hỗ trợ database embedded:

```text
application
 └── database
```

không cần network.

---

# 76. Server Database

Cũng hỗ trợ:

```text
application
 ↓
RPC
 ↓
database server
```

393/394 xử lý boundary/security.

---

# 77. In-Process Query

Embedded query có thể compiler optimize mạnh:

```text
application query
 ↓
database query
```

thành direct function calls và memory scans.

---

# 78. Zero-Copy Query

Nếu storage layout phù hợp:

```text
persistent column
 ↓
view
 ↓
compute
```

có thể tránh copy.

---

# 79. Persistent View

View cần explicit lifetime.

Không cho:

```text
database.close()
 ↓
dangling RecordView
```

Compiler phải reject.

---

# 80. Cursor

Cursor:

```text
Cursor<T>
```

là stateful iterator-like abstraction.

Nhưng compiler có thể lower thành:

```text
pointer
index
bounds
```

hoặc storage-specific iterator.

---

# 81. Cursor Invalidation

Mutation có thể invalidate cursor.

Database API phải khai báo invalidation rules.

---

# 82. Large Objects

BLOB/text lớn không nhất thiết nằm inline:

```text
Record
 └── BlobRef
```

nhưng `BlobRef` phải có ownership/storage contract.

---

# 83. Blob Streaming

Large object nên hỗ trợ:

```text
Stream<Byte>
```

thay vì buộc load toàn bộ vào RAM.

---

# 84. Time-Series Database

Time-series có thể specialize:

```text
timestamp
series_id
value
```

với:

```text
partition
compression
window
aggregation
```

---

# 85. Vector Database

Vector database có thể xây trên:

```text
Tensor
Index
Distance
Parallel/GPU
```

Các index:

```text
HNSW
IVF
PQ
Flat
```

là library/domain implementations.

---

# 86. Graph Database

Graph database xây trên:

```text
Graph
Storage
Index
Transaction
Query
```

không cần Core graph object hierarchy.

---

# 87. Full-Text Search

Search engine có thể xây:

```text
tokenization
inverted index
posting list
ranking
```

dựa trên Text + Data Layout + Storage.

---

# 88. Database + AI

Có thể tích hợp:

```text
Database
 ↓
Tensor
 ↓
ML
 ↓
GPU
```

mà không cần serialize qua nhiều abstraction boundary nếu storage/layout tương thích.

---

# 89. Database + AD

Thông thường query không differentiable.

Nhưng numerical query:

```text
feature extraction
aggregation
optimization
```

có thể được đưa vào AD nếu explicit.

---

# 90. Database + Security

Database capability:

```text
ReadTable<T>
WriteTable<T>
AdminDatabase
```

có thể được quản lý bởi 394.

---

# 91. Row-Level Security

Policy có thể áp dụng:

```text
user
 ↓
row visibility predicate
 ↓
query
```

Query planner phải preserve security predicate.

Không được optimize predicate ra khỏi query nếu làm lộ dữ liệu.

---

# 92. Encryption at Rest

Storage engine có thể sử dụng:

```text
EncryptedPage
EncryptedSegment
EncryptedWAL
```

với key capability.

---

# 93. Encryption in Transit

Server database dùng 392/394.

Không tạo transport/security layer riêng.

---

# 94. Audit Log

Security-sensitive database có thể emit:

```text
AuditEvent
```

nhưng audit effect phải là observable effect.

Optimizer không được loại bỏ.

---

# 95. Database Compiler Boundary

Kiến trúc:

```text
Axiom Source
     ↓
Typed Query
     ↓
AQIR
     ↓
Query Optimizer
     ↓
Storage Plan
     ↓
Execution Plan
     ↓
MIR
```

---

# 96. AQIR

AQIR node có thể gồm:

```text
Q_SCAN
Q_INDEX_SCAN
Q_FILTER
Q_PROJECT
Q_JOIN
Q_GROUP
Q_AGGREGATE
Q_SORT
Q_LIMIT
Q_DISTINCT
Q_WINDOW
Q_UNION
Q_MATERIALIZE
Q_EXCHANGE
Q_PARTITION
Q_SHUFFLE
Q_REDUCE
```

---

# 97. Storage Plan

AQIR:

```text
Filter(age > 18)
```

có thể lower:

```text
IndexScan(age, >18)
```

hoặc:

```text
ColumnScan(age)
SIMDCompare
Mask
```

tùy cost model.

---

# 98. Execution Plan

Execution plan phải giữ proof:

```text
schema
bounds
ownership
visibility
transaction
security
numerical
ordering
```

---

# 99. Query Fusion

Ví dụ:

```text
scan
→ filter
→ projection
```

có thể fuse thành một loop/vector kernel.

---

# 100. CompilerDB

Bổ sung:

```text id="a5t2zn"
DatabaseDB
DatabaseTypeDB
DatabaseEngineDB
DatabaseConfigDB
DatabaseCapabilityDB

SchemaDB
SchemaTypeDB
SchemaVersionDB
SchemaFieldDB
SchemaConstraintDB
SchemaMigrationDB
SchemaCompatibilityDB

RecordDB
RecordTypeDB
RecordLayoutDB
RecordVersionDB
RecordVisibilityDB

TransactionDB
TransactionTypeDB
TransactionStateDB
TransactionIsolationDB
TransactionSnapshotDB
TransactionConflictDB
TransactionCommitDB
TransactionAbortDB
TransactionRetryDB
TransactionDurabilityDB

MVCCDB
VersionDB
VisibilityDB
SnapshotDB
TimestampDB

WALDB
WalRecordDB
WalSegmentDB
WalFlushDB
WalCommitDB
CheckpointDB
RecoveryDB
RecoveryReplayDB
CrashRecoveryDB

PageDB
PageIdDB
PageLayoutDB
PageVersionDB
PageChecksumDB
SegmentDB
SegmentLayoutDB
SegmentCompactionDB
TombstoneDB

StorageEngineDB
RowStoreDB
ColumnStoreDB
HybridStoreDB
LsmTreeDB
MemTableDB
SstableDB
CompressionDB
EncodingDB

IndexDB
IndexTypeDB
BTreeIndexDB
HashIndexDB
BloomFilterDB
IndexMaintenanceDB
IndexStatisticsDB

QueryDB
QueryTypeDB
QueryExpressionDB
QueryPredicateDB
QueryProjectionDB
QueryJoinDB
QueryAggregateDB
QuerySortDB
QueryWindowDB

AQIRDB
QueryPlanDB
QueryExecutionDB
QueryOptimizationDB
QueryRewriteDB
QueryFusionDB
QueryMaterializationDB

QueryStatisticsDB
CardinalityDB
HistogramDB
SelectivityDB
CostModelDB

QueryParallelDB
QuerySimdDB
QueryGpuDB
QueryDistributedDB
QueryShuffleDB

CursorDB
RecordViewDB
PersistentViewDB
ViewInvalidationDB

BlobDB
BlobStorageDB
BlobStreamDB

ReplicationDB
LogicalReplicationDB
PhysicalReplicationDB
ReplicaDB
ReplicationConsistencyDB

DatabaseSecurityDB
RowSecurityDB
ColumnSecurityDB
DatabaseAuditDB
DatabaseEncryptionDB
DatabaseKeyDB

DatabaseSchemaProofDB
TransactionProofDB
DurabilityProofDB
RecoveryProofDB
QueryTypeProofDB
QueryPlanProofDB
QueryOptimizationProofDB
IndexCorrectnessDB
VisibilityProofDB
ConsistencyProofDB
DatabaseVerificationDB
```

---

# 101. MIR

```text id="y42v3a"
DB_OPEN
DB_CLOSE
DB_CREATE
DB_DROP

DB_SCHEMA_LOAD
DB_SCHEMA_MIGRATE
DB_SCHEMA_VALIDATE

DB_TX_BEGIN
DB_TX_READ
DB_TX_WRITE
DB_TX_COMMIT
DB_TX_ABORT
DB_TX_RETRY

DB_SNAPSHOT_CREATE
DB_SNAPSHOT_RELEASE
DB_VISIBILITY_CHECK

DB_RECORD_READ
DB_RECORD_WRITE
DB_RECORD_DELETE
DB_RECORD_INSERT

DB_INDEX_LOOKUP
DB_INDEX_RANGE
DB_INDEX_INSERT
DB_INDEX_DELETE

DB_SCAN
DB_INDEX_SCAN
DB_FILTER
DB_PROJECT
DB_JOIN
DB_GROUP
DB_AGGREGATE
DB_SORT
DB_DISTINCT
DB_LIMIT
DB_OFFSET
DB_WINDOW

DB_PLAN
DB_PLAN_OPTIMIZE
DB_PLAN_FUSE
DB_PLAN_MATERIALIZE

DB_PARTITION
DB_EXCHANGE
DB_SHUFFLE
DB_DISTRIBUTED_REDUCE

DB_WAL_APPEND
DB_WAL_FLUSH
DB_CHECKPOINT
DB_RECOVER
DB_REPLAY

DB_SEGMENT_CREATE
DB_SEGMENT_COMPACT
DB_SEGMENT_MERGE

DB_CURSOR_CREATE
DB_CURSOR_NEXT
DB_CURSOR_CLOSE

DB_BLOB_OPEN
DB_BLOB_READ
DB_BLOB_WRITE
DB_BLOB_CLOSE

DB_REPLICATE
DB_REPLICA_APPLY
DB_REPLICA_ACK

DB_AUDIT
DB_SECURITY_CHECK
DB_ENCRYPT
DB_DECRYPT
```

---

# 102. Proof System

```text id="t2v8ak"
SchemaCompatibilityProof
SchemaMigrationProof
RecordLayoutProof

TransactionOwnershipProof
TransactionIsolationProof
TransactionConflictProof
TransactionCommitProof
TransactionDurabilityProof

MVCCVisibilityProof
SnapshotProof

WalOrderingProof
WalDurabilityProof
CheckpointProof
RecoveryProof
CrashRecoveryProof

PageIntegrityProof
SegmentIntegrityProof
CompactionProof

IndexCorrectnessProof
IndexConsistencyProof
BloomFilterProof

QueryTypeProof
QuerySchemaProof
QueryBoundsProof
QueryOwnershipProof
QueryVisibilityProof

QueryPredicateProof
QueryJoinProof
QueryAggregateProof
QueryOrderingProof

QueryRewriteProof
QueryFusionProof
QueryMaterializationProof
QueryCostProof

QuerySimdProof
QueryGpuProof
QueryParallelProof
QueryDistributedProof

ZeroCopyQueryProof
ViewLifetimeProof
CursorValidityProof

ReplicationProof
ReplicaConsistencyProof

DatabaseSecurityProof
RowSecurityProof
DatabaseEncryptionProof
AuditProof

DatabaseOptimizationProof
DatabaseVerificationProof
```

---

# 103. Invariants

### `ADB-01`
Database resource ownership phải rõ ràng.

### `ADB-02`
Database view không được vượt lifetime của resource mà nó tham chiếu.

### `ADB-03`
Record type không mặc định đồng nghĩa persistent schema.

### `ADB-04`
Schema version phải được xác định khi persistent representation observable.

### `ADB-05`
Schema migration phải explicit và version-compatible.

### `ADB-06`
Transaction ownership không được tạo implicit shared mutable state.

### `ADB-07`
Transaction isolation phải được khai báo bởi engine/transaction contract.

### `ADB-08`
Committed transaction không được mất dưới durability contract đã công bố.

### `ADB-09`
`commit` không được ngầm đồng nghĩa stable storage nếu durability contract không yêu cầu.

### `ADB-10`
Recovery phải preserve committed database state.

### `ADB-11`
WAL ordering phải phù hợp với durability semantics.

### `ADB-12`
Checkpoint không được làm mất transaction đã committed.

### `ADB-13`
MVCC visibility phải phụ thuộc transaction snapshot/visibility contract.

### `ADB-14`
Index không được làm thay đổi logical query result.

### `ADB-15`
Bloom filter chỉ được phép loại bỏ trường hợp chắc chắn absent.

### `ADB-16`
Compaction không được thay đổi logical record visibility.

### `ADB-17`
Query type checking phải hoàn thành trước query execution.

### `ADB-18`
Query optimizer không được thay đổi observable query semantics.

### `ADB-19`
Predicate pushdown phải preserve null, error, ordering và effect semantics.

### `ADB-20`
Join reordering chỉ được thực hiện khi semantics cho phép.

### `ADB-21`
Aggregation reordering phải tuân theo numerical contract.

### `ADB-22`
Query fusion không được thay đổi transaction visibility hoặc side effects.

### `ADB-23`
Zero-copy query phải preserve ownership, lifetime, alias và storage-domain contracts.

### `ADB-24`
Cursor invalidation phải được compiler/runtime contract xác định.

### `ADB-25`
Distributed query phải preserve distributed consistency semantics.

### `ADB-26`
Replication phải preserve declared consistency/durability semantics.

### `ADB-27`
Database security predicates không được bị optimizer loại bỏ hoặc reorder theo cách làm lộ dữ liệu.

### `ADB-28`
Encryption/decryption boundaries phải preserve key ownership và capability semantics.

### `ADB-29`
Database optimization có thể thay đổi physical layout/execution nhưng không được thay đổi logical database semantics.

### `ADB-30`
Chương trình không sử dụng database subsystem không được kéo theo database runtime bắt buộc.

---

# 104. Kiến trúc tổng thể sau 395

Đây là một mốc quan trọng vì nhiều domain trước đó bắt đầu hội tụ:

```text
                    AXIOM
                      │
        ┌─────────────┼─────────────┐
        │             │             │
     Compute       Storage       Network
        │             │             │
   SIMD/GPU       Data Layout    Distributed
   Tensor         I/O            Security
   ML             Database       RPC
        │             │             │
        └─────────────┼─────────────┘
                      │
                 Application
```

Database không cần một “ngôn ngữ riêng” bên trong Axiom.

Một query có thể đi từ:

```text
Axiom source
    ↓
typed query
    ↓
AQIR
    ↓
query optimizer
    ↓
data-layout optimizer
    ↓
SIMD / GPU / parallel / distributed
    ↓
MIR
    ↓
native machine code
```

Điều này rất phù hợp với mục tiêu ban đầu của Axiom:

> **Programmer mô tả dữ liệu và ý định; compiler quyết định representation, layout, indexing, vectorization, parallelization, storage strategy và execution placement — nhưng mọi thay đổi đều phải được chứng minh tương đương về semantics.**