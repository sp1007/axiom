# BOOTSTRAP-391 — Axiom Storage, Persistence, Serialization & Durable Data Engine

Sau **390 — I/O, Streaming, Buffering & Zero-Copy Dataflow**, bước tiếp theo hợp lý là giải quyết **vòng đời dữ liệu lâu dài**:

> **Axiom phải phân biệt rõ dữ liệu trong RAM, dữ liệu truyền qua wire, dữ liệu lưu trên disk và dữ liệu persistent — đồng thời cho phép chuyển đổi giữa chúng với chi phí tối thiểu.**

Điểm quan trọng: **serialization không được trở thành một lớp bắt buộc ở giữa mọi API**.

---

## 1. Bốn loại dữ liệu

Axiom cần phân biệt:

```text
Value
Memory Representation
Wire Representation
Persistent Representation
```

Ví dụ:

```text
User
 ↓
RAM representation
 ↓
JSON / protobuf / binary protocol
 ↓
database/file representation
```

Đây là **4 semantic domains khác nhau**.

---

# 2. Memory Representation

Một struct:

```text
struct User {
    id: u64
    age: u32
    name: String
}
```

có thể có layout compiler-controlled.

Không được mặc định dùng layout đó làm file format.

---

# 3. Persistent Representation

File format phải explicit:

```text
@format("UserV2")
```

hoặc thông qua một codec/type contract.

Compiler không được tự thay đổi format chỉ vì internal struct layout thay đổi.

---

# 4. Versioning

Persistent data phải hỗ trợ:

```text
V1
V2
V3
```

và migration:

```text
V1 → V2
V2 → V3
```

Migration là semantic transformation, không phải memory cast.

---

# 5. Serialization ≠ Bitcast

Hai operation hoàn toàn khác:

```text
bitcast<T,U>()
```

và:

```text
encode<T>()
```

`bitcast` bảo toàn bit representation theo contract.

`encode` bảo toàn **logical value**.

---

# 6. Stable Binary Layout

Có thể định nghĩa:

```text
@repr(binary)
```

nhưng nó phải là một **serialization ABI**, không phải ordinary memory layout.

Ví dụ:

```text
u32 → 4 bytes
```

với endian và encoding xác định.

---

# 7. Text Encoding

Text format:

```text
UTF-8
UTF-16
ASCII-compatible
```

phải có encoding contract.

Axiom default UTF-8.

---

# 8. Schema

Một persistent format cần schema:

```text
Schema<T>
```

mô tả:

```text
fields
types
optional fields
defaults
version
encoding
```

Schema có thể được compiler tạo ở comptime.

---

# 9. Compile-Time Schema

Ví dụ:

```text
comptime schema_of<User>()
```

có thể tạo metadata.

Nếu application không cần schema runtime:

```text
schema metadata
```

không được đưa vào binary.

---

# 10. Reflection Integration

391 sử dụng reflection/comptime đã thiết kế trước đó.

Compiler có thể biết:

```text
fields(User)
type_of(field)
attributes
visibility
repr
```

để sinh codec.

---

# 11. Typed Serialization

Thay vì runtime reflection:

```text
serialize(object)
```

compiler có thể generate:

```text
serialize_User(...)
```

và specialize hoàn toàn.

---

# 12. Zero-Copy Decode

Nếu wire layout tương thích memory layout:

```text
network buffer
      ↓
view<UserWire>
```

có thể không cần copy.

Nhưng chỉ được phép nếu:

```text
alignment
endianness
encoding
padding
lifetime
mutability
```

đều phù hợp.

---

# 13. Zero-Copy không được phá Ownership

Nếu buffer thuộc network layer:

```text
Buffer
 ↓
view<User>
```

view không được tồn tại sau khi buffer bị recycle.

Compiler phải kiểm tra điều này.

---

# 14. Copy-on-Decode

Nếu không tương thích:

```text
wire buffer
 ↓
decode
 ↓
User
```

phải materialize value.

Đây là semantic conversion, không phải compiler failure.

---

# 15. Lazy Decode

Một format có thể cho:

```text
Lazy<T>
```

hoặc:

```text
DecodedView<T>
```

chỉ decode field khi truy cập.

---

# 16. Lazy Decode Lifetime

Lazy value vẫn phải giữ source storage hợp lệ.

Compiler phải đảm bảo:

```text
Lazy<T> → source buffer
```

không tạo dangling capability.

---

# 17. Memory-Mapped Persistent Data

Một file binary có thể:

```text
file
 ↓ mmap
MappedRegion
 ↓
TypedView<T>
```

Nếu format tương thích, có thể truy cập gần như trực tiếp.

---

# 18. Persistent Layout Contract

Mapped structures cần:

```text
fixed width
fixed alignment
fixed endian
fixed offsets
fixed encoding
```

Không thể dùng ordinary compiler-controlled layout.

---

# 19. Append-Only Data

Axiom nên hỗ trợ semantic abstraction:

```text
AppendLog<T>
```

cho:

- event log;
- telemetry;
- database;
- journal;
- distributed systems.

---

# 20. Log Semantics

Mỗi record có thể có:

```text
sequence
timestamp
payload
checksum
version
```

nhưng format phải explicit.

---

# 21. Atomic Persistence

Persistent update cần phân biệt:

```text
write
flush
sync
commit
```

390 đã định nghĩa I/O ordering; 391 xây semantic layer phía trên.

---

# 22. Transaction

Transaction abstraction:

```text
Transaction {
    read
    write
    commit
    rollback
}
```

không nhất thiết phải là database.

Có thể áp dụng cho:

```text
file
journal
memory-mapped store
database
distributed storage
```

---

# 23. Atomic Commit

Compiler/runtime có thể dùng:

```text
journal
copy-on-write
rename
WAL
snapshot
```

nhưng logical semantics phải giống nhau.

---

# 24. Copy-on-Write

Persistent structures có thể sử dụng:

```text
COW
```

nếu mutation semantics được bảo toàn.

Đặc biệt hữu ích cho:

```text
large immutable data
snapshots
fork-like structures
```

---

# 25. Immutable Persistent Data

Có thể có:

```text
PersistentVector<T>
PersistentMap<K,V>
PersistentSet<T>
```

nhưng đây là library abstractions.

Không cần GC.

---

# 26. Structural Sharing

Persistent structures có thể chia sẻ storage immutable.

Điều này khác shared mutable ownership.

```text
immutable sharing → safe
mutable sharing → synchronization required
```

---

# 27. Persistent Graph

Các abstraction trước:

```text
Graph
Sparse
Tensor
```

có thể có persistent storage.

Ví dụ:

```text
MappedCSR<T>
MappedGraph
MappedTensor
```

không cần load toàn bộ vào RAM.

---

# 28. Out-of-Core Computing

Đây là phần rất quan trọng với scientific/AI:

```text
Disk
 ↓
Chunk
 ↓
RAM
 ↓
GPU
```

thay vì:

```text
Disk → toàn bộ RAM
```

---

# 29. Chunked Storage

Logical tensor:

```text
Tensor<T>
```

physical:

```text
Chunk0
Chunk1
Chunk2
...
```

Compiler/runtime có thể load theo demand.

---

# 30. Storage Layout

Chunk layout có thể:

```text
row-major
column-major
tiled
blocked
compressed
sparse
```

và tích hợp trực tiếp với 389.

---

# 31. Compression

Compression là representation transformation:

```text
Logical Data
      ↓
Compressed Storage
```

Ví dụ:

```text
LZ
Zstd
dictionary
delta
bit packing
quantization
```

Không phải compiler bắt buộc.

---

# 32. Compression-Aware Access

Một pipeline:

```text
disk
 ↓
compressed chunk
 ↓
decode
 ↓
GPU
```

có thể được fusion.

Không cần:

```text
decode entire dataset
```

---

# 33. Encryption

Persistent representation có thể:

```text
encrypt
authenticate
compress
```

thứ tự phải explicit vì:

```text
compress(encrypt(data))
```

khác:

```text
encrypt(compress(data))
```

---

# 34. Integrity

Persistent blocks có thể có:

```text
checksum
hash
MAC
signature
```

Integrity metadata là semantic property nếu ứng dụng yêu cầu.

---

# 35. Crash Consistency

Axiom storage API nên mô tả:

```text
durability level
atomicity level
ordering
recovery guarantee
```

Không dùng từ "saved" một cách mơ hồ.

---

# 36. Recovery

Storage abstraction:

```text
open
recover
validate
repair
```

có thể phục hồi journal hoặc snapshot.

---

# 37. Snapshot

Snapshot có semantic:

```text
point-in-time logical state
```

không nhất thiết phải copy toàn bộ memory.

Có thể dùng:

```text
COW
incremental snapshot
journal
```

---

# 38. Checkpoint

Scientific simulation:

```text
simulation state
 ↓
checkpoint
```

có thể dùng cùng persistent engine.

Như vậy 377 Solver/Simulation và 391 không cần hai hệ thống serialization riêng.

---

# 39. Model Checkpoint

AI:

```text
model parameters
optimizer state
training state
RNG state
```

có thể lưu qua cùng storage abstraction.

---

# 40. Tensor Dataset

AI/scientific data:

```text
Dataset<Tensor>
```

có thể streaming:

```text
disk
 ↓
chunk
 ↓
TensorView
 ↓
GPU
```

zero-copy ở từng boundary nếu có thể.

---

# 41. Database Boundary

Database engine không cần nằm trong Core.

Nhưng Axiom phải đủ expressive để xây:

```text
B-tree
LSM-tree
hash index
column store
row store
```

mà không bị runtime/GC bắt buộc.

---

# 42. Columnar Storage

Data-oriented layout 389 rất phù hợp:

```text
row:
A B C D

column:
A[]
B[]
C[]
D[]
```

Compiler có thể tối ưu analytical queries trên column representation.

---

# 43. Row/Column Semantic View

Database layer có thể cung cấp:

```text
RowView<T>
ColumnView<T>
```

mà không cần copy.

---

# 44. Query Execution

Một query:

```text
filter
→ project
→ aggregate
```

có thể lower thành:

```text
scan
→ SIMD filter
→ projection
→ parallel reduction
```

sử dụng các engine đã có.

---

# 45. Index

Index abstraction:

```text
Index<K,V>
```

không cần class hierarchy.

Có thể implement:

```text
BTree
HashIndex
SortedIndex
BitmapIndex
SpatialIndex
```

bằng traits/generics.

---

# 46. Persistent Handle

Logical identity phải khác physical address.

Do đó persistent record có thể có:

```text
RecordId
Generation
Offset
```

nhưng API chỉ expose logical identity.

---

# 47. Stale Persistent Handle

Nếu record bị deleted:

```text
RecordId
```

không được tự động trở thành valid object mới chỉ vì offset được reuse.

Generation hoặc equivalent mechanism phải bảo vệ contract khi API yêu cầu stable identity.

---

# 48. Schema Evolution

Khi:

```text
UserV1
```

thành:

```text
UserV2
```

có thể:

```text
add field
remove field
rename field
change encoding
```

nhưng mỗi transformation phải có migration rule.

---

# 49. Backward/Forward Compatibility

Schema có thể khai báo:

```text
compatible
incompatible
migratable
```

Compiler có thể kiểm tra static khi cả hai schema đều biết.

---

# 50. Default Values

Khi field mới xuất hiện:

```text
age: u32 = 0
```

migration có thể materialize default.

Không được tự suy đoán default nguy hiểm.

---

# 51. Optional Fields

Persistent optional:

```text
Option<T>
```

phải phân biệt:

```text
missing
null-like semantic
default
explicit value
```

Không được tự đồng nhất.

---

# 52. Enum Evolution

Enum persistence cần xử lý:

```text
variant IDs
unknown variants
forward compatibility
```

Không dùng ordinal index nếu format yêu cầu stable IDs.

---

# 53. Checksums and Corruption

Decode phải phân biệt:

```text
invalid encoding
corrupt data
unknown version
unsupported feature
```

để recovery layer xử lý chính xác.

---

# 54. Streaming Decode Errors

Nếu decode stream fail giữa chừng:

```text
partial record
```

phải có semantics rõ:

```text
consumed bytes
remaining bytes
recoverable
fatal
```

---

# 55. Transaction + Ownership

Transaction sở hữu resources/state rõ ràng.

Ví dụ:

```text
tx.commit()
```

sau commit:

```text
rollback()
```

không còn hợp lệ.

Compiler có thể encode trạng thái này bằng type/state-machine abstractions.

---

# 56. Typestate

Axiom không cần thêm một hệ thống typestate đặc biệt vào Core.

Generic types + traits + ownership có thể biểu diễn:

```text
Closed
Open
Prepared
Committed
```

---

# 57. Compile-Time Format Generation

Comptime có thể generate:

```text
encoder
decoder
schema
migration
validation
```

từ type.

Tất cả code generated phải đi qua:

```text
type checking
ownership
effect
ABI
verification
```

như đã frozen.

---

# 58. Runtime Reflection không bắt buộc

Nếu compiler biết schema:

```text
runtime metadata = 0
```

trừ khi application yêu cầu dynamic schema.

---

# 59. Dynamic Schema

Có thể có:

```text
DynamicValue
DynamicSchema
DynamicRecord
```

nhưng đây là explicit runtime abstraction.

Không làm `Any` trở thành Core primitive.

---

# 60. Generic Storage API

Kiến trúc tổng quát:

```text
Storage<T>
 ├── Memory
 ├── File
 ├── Mapped
 ├── Remote
 ├── Database
 └── Device
```

nhưng đây là **trait contracts**, không phải inheritance hierarchy.

---

# 61. Storage Domain

Bổ sung vào storage model:

```text
VOLATILE
PERSISTENT
REMOTE
DEVICE
EXTERNAL
```

---

# 62. Persistence Boundary

Khi value đi từ:

```text
volatile memory
```

sang:

```text
persistent storage
```

đó là semantic boundary.

Compiler không được coi đó là ordinary move.

---

# 63. Persistence Ordering

Một persistent transaction có thể có:

```text
logical order
physical write order
durability order
```

ba thứ phải phân biệt.

---

# 64. Async Persistence

```text
await commit()
```

không đồng nghĩa:

```text
thread spawn
```

Nó sử dụng Future semantics đã frozen.

---

# 65. Distributed Storage

391 chỉ định nghĩa storage contract.

Distributed storage implementation có thể nằm ở layer 388/standard library.

Ví dụ:

```text
RemoteStorage<T>
```

có latency/failure/consistency semantics rõ ràng.

---

# 66. Consistency

Storage API có thể khai báo:

```text
Strong
Eventual
Session
Snapshot
ReadYourWrites
```

nhưng đây là distributed semantics, không phải memory model.

---

# 67. Cache

Cache là optimization layer:

```text
persistent
 ↓
cache
 ↓
memory
```

Compiler/runtime có thể cache nếu semantics không thay đổi.

---

# 68. Cache Invalidation

Nếu cache có mutable state:

```text
coherence
version
generation
```

phải được quản lý explicit.

---

# 69. Persistent Cache

Compiler artifacts cũng có thể dùng cùng engine:

```text
CompilerDB
 ↓
artifact
 ↓
persistent cache
```

đặc biệt hữu ích cho incremental compilation.

---

# 70. Universal Data Path

Đến đây Axiom có một kiến trúc dữ liệu khá mạnh:

```text
External
   ↓
I/O
   ↓
Buffer
   ↓
Logical Value
   ↓
Data Layout
   ↓
CPU/SIMD/GPU
   ↓
Persistent Storage
```

và compiler có thể tối ưu xuyên các lớp khi semantics cho phép.

---

# 71. CompilerDB

Bổ sung:

```text
PersistenceDB
StorageDB
StorageDomainDB
StorageResourceDB

SerializationDB
SerializationSchemaDB
SerializationFieldDB
SerializationEncodingDB
SerializationVersionDB
SerializationMigrationDB
SerializationCompatibilityDB

CodecDB
EncoderDB
DecoderDB
LazyDecodeDB
ZeroCopyDecodeDB

BinaryFormatDB
TextFormatDB
WireFormatDB
PersistentFormatDB

MappedStorageDB
MappedRecordDB
MappedTensorDB
MappedGraphDB
MappedSparseDB

AppendLogDB
JournalDB
WalDB
SnapshotDB
CheckpointDB
RecoveryDB
CrashConsistencyDB

TransactionDB
TransactionStateDB
TransactionCommitDB
TransactionRollbackDB
TransactionAtomicityDB

CopyOnWriteDB
StructuralSharingDB
PersistentCollectionDB

ChunkStorageDB
ChunkLayoutDB
ChunkCompressionDB
ChunkCacheDB
OutOfCoreDB
StreamingStorageDB

CompressionDB
EncryptionDB
IntegrityDB
ChecksumDB
HashDB

SchemaDB
SchemaEvolutionDB
SchemaMigrationDB
SchemaCompatibilityDB
SchemaValidationDB

PersistentHandleDB
PersistentIdentityDB
PersistentGenerationDB

StorageCacheDB
StorageCoherenceDB
StorageVersionDB

DatabaseStorageDB
IndexStorageDB
ColumnStoreDB
RowStoreDB
QueryStorageDB

StorageCostModelDB
StorageOptimizationDB
StorageProofDB
StorageVerificationDB
```

---

# 72. MIR

```text id="1x0ylz"
STORAGE_OPEN
STORAGE_CLOSE

STORAGE_READ
STORAGE_WRITE
STORAGE_READ_AT
STORAGE_WRITE_AT

STORAGE_MAP
STORAGE_UNMAP

STORAGE_FLUSH
STORAGE_SYNC
STORAGE_COMMIT
STORAGE_ROLLBACK

STORAGE_BEGIN_TX
STORAGE_END_TX

STORAGE_SNAPSHOT
STORAGE_RESTORE
STORAGE_CHECKPOINT
STORAGE_RECOVER

SERIALIZE
DESERIALIZE

SCHEMA_QUERY
SCHEMA_VALIDATE
SCHEMA_MIGRATE

ENCODE
DECODE
LAZY_DECODE

ZERO_COPY_DECODE
MATERIALIZE_DECODE

CHUNK_LOAD
CHUNK_STORE
CHUNK_PREFETCH
CHUNK_EVICT

COMPRESS
DECOMPRESS

ENCRYPT
DECRYPT

CHECKSUM
VERIFY_INTEGRITY

COW_BEGIN
COW_CLONE
COW_COMMIT

PERSISTENT_HANDLE_CREATE
PERSISTENT_HANDLE_RESOLVE
PERSISTENT_HANDLE_VALIDATE
```

---

# 73. Proof System

```text id="k5x6xu"
SerializationProof
SchemaProof
SchemaCompatibilityProof
SchemaMigrationProof

EncodingProof
DecodingProof
EndianProof
FormatVersionProof

ZeroCopyDecodeProof
DecodeLifetimeProof
DecodeAlignmentProof
DecodeLayoutProof

MappedStorageProof
MappedLifetimeProof
MappedAlignmentProof

PersistenceOwnershipProof
PersistenceOrderingProof
DurabilityProof

TransactionProof
CommitProof
RollbackProof
AtomicPersistenceProof

CrashConsistencyProof
RecoveryProof
SnapshotProof
CheckpointProof

ChunkStorageProof
OutOfCoreProof
StorageCacheProof

CompressionProof
EncryptionProof
IntegrityProof

CopyOnWriteProof
StructuralSharingProof

PersistentIdentityProof
PersistentHandleProof
GenerationProof

StorageDomainProof
RemoteStorageProof
StorageConcurrencyProof
StorageOptimizationProof
```

---

# 74. Invariants

### `ASTORE-01`
Persistent representation phải độc lập với compiler-controlled memory layout.

### `ASTORE-02`
Serialization không được đồng nhất với `bitcast`.

### `ASTORE-03`
Wire format phải có encoding contract xác định.

### `ASTORE-04`
Endianness của persistent/wire data phải explicit.

### `ASTORE-05`
Schema version phải được xác định rõ khi format có evolution.

### `ASTORE-06`
Schema migration phải là semantic transformation.

### `ASTORE-07`
Compiler không được tự thay đổi persistent format khi internal layout thay đổi.

### `ASTORE-08`
Zero-copy decode chỉ hợp lệ khi alignment/layout/encoding/lifetime tương thích.

### `ASTORE-09`
Decoded view không được vượt lifetime của source storage.

### `ASTORE-10`
Lazy decode phải giữ source storage hợp lệ.

### `ASTORE-11`
Memory-mapped representation phải có stable layout contract.

### `ASTORE-12`
Mapped data không được bị compiler layout-transform nếu layout observable.

### `ASTORE-13`
Persistent identity không được phụ thuộc trực tiếp vào physical address.

### `ASTORE-14`
Reused storage không được làm stale handle trở thành valid object ngoài contract.

### `ASTORE-15`
Append-only log phải bảo toàn record ordering theo contract.

### `ASTORE-16`
Commit semantics phải phân biệt logical commit và physical durability.

### `ASTORE-17`
Rollback không được giả định hoàn tác external side effects ngoài storage transaction.

### `ASTORE-18`
Crash recovery phải tuân thủ durability/atomicity contract đã khai báo.

### `ASTORE-19`
Snapshot phải biểu diễn đúng logical state tại snapshot point.

### `ASTORE-20`
Checkpoint phải preserve đủ state theo recovery contract.

### `ASTORE-21`
Chunked storage phải preserve logical indexing.

### `ASTORE-22`
Compression/decompression phải preserve logical data semantics.

### `ASTORE-23`
Encryption/decryption phải preserve authenticated data semantics.

### `ASTORE-24`
Integrity verification failure phải không được biến thành valid data trong safe path.

### `ASTORE-25`
Copy-on-write phải preserve isolation giữa các logical versions.

### `ASTORE-26`
Persistent structural sharing chỉ được chia sẻ mutable state khi synchronization contract cho phép.

### `ASTORE-27`
Schema evolution phải không được âm thầm mất dữ liệu ngoài migration policy.

### `ASTORE-28`
Generated codecs phải đi qua toàn bộ type/ownership/effect/ABI verification.

### `ASTORE-29`
Storage optimization không được thay đổi observable persistence semantics.

### `ASTORE-30`
Nếu application không sử dụng persistence/serialization subsystem, compiler không được kéo theo persistence runtime bắt buộc.

---

## 75. Một điểm rất đáng chú ý

Sau 391, Axiom bắt đầu có một đặc tính mà C/C++ thường phải xây bằng rất nhiều thư viện riêng:

```text
             ┌───────────────┐
             │ Logical Value │
             └───────┬───────┘
                     │
       ┌─────────────┼─────────────┐
       ↓             ↓             ↓
    Memory          Wire       Persistent
       │             │             │
       ↓             ↓             ↓
    CPU/GPU       Network       Disk
```

Nhưng **không có nghĩa Axiom biến tất cả thành một runtime khổng lồ**.

Mỗi chương trình chỉ kéo vào phần nó sử dụng:

```text
simple CLI
→ gần như không có storage runtime

native game
→ memory + file

AI
→ tensor + storage + GPU + async I/O

database
→ storage + mmap + transactions + indexing

embedded
→ custom storage/device backend
```

Đây tiếp tục giữ nguyên mục tiêu quan trọng của Axiom:

> **Abstraction cao ở source level, nhưng physical representation và runtime dependency chỉ tồn tại khi semantics thực sự cần chúng.**