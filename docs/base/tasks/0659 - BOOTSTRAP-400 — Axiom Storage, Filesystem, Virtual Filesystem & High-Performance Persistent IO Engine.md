# BOOTSTRAP-400 — Axiom Storage, Filesystem, Virtual Filesystem & High-Performance Persistent I/O Engine

Sau **399 — Video, Image, Codec & Media Timeline**, bước tiếp theo nên đi sâu vào **Storage/Persistent I/O**.

Axiom hiện đã có:

```text
396 OS / Syscalls
390 I/O / Streaming / Buffer
395 Database
399 Media
394 Security
389 Data Layout
```

Nhưng chúng ta chưa có một **storage semantics thống nhất** cho:

- file;
- directory;
- filesystem;
- memory mapping;
- persistent storage;
- NVMe/SSD;
- virtual filesystem;
- archive;
- transactional file updates;
- crash consistency;
- file watching;
- high-performance sequential/random I/O.

Mục tiêu của 400:

> **Một file trong Axiom là một resource có ownership, capability, lifetime và persistence semantics rõ ràng; filesystem backend là implementation detail có thể thay đổi mà không thay đổi semantics của chương trình.**

---

# 1. Storage không thuộc Core

Core chỉ cần OS resource primitives.

Storage layer:

```text
Storage
 ├── File
 ├── Directory
 ├── Filesystem
 ├── Mapping
 ├── BlockDevice
 ├── Archive
 ├── VFS
 └── Persistence
```

---

# 2. File Identity

Không dùng pathname làm identity tuyệt đối.

Phân biệt:

```text
Path
FileId
FileHandle
FileObject
```

`Path` chỉ là cách resolve resource.

---

# 3. File Handle

```text
FileHandle
```

là logical resource identity.

Nó có ownership:

```text
open
 ↓
FileHandle
 ↓
close/drop
```

---

# 4. File Object

Hai handle có thể cùng tham chiếu một underlying file object.

Ví dụ:

```text
dup(handle)
```

không nhất thiết tạo file mới.

---

# 5. Open Semantics

Open cần explicit flags:

```text
READ
WRITE
CREATE
CREATE_NEW
TRUNCATE
APPEND
DIRECT
SYNC
DSYNC
NONBLOCK
```

Không nên có những flag ngầm.

---

# 6. Access Capability

Có thể mô hình hóa:

```text
Capability<File>
```

với quyền:

```text
read
write
append
metadata
map
execute
```

Security engine 394 quản lý authority.

---

# 7. Path

Path là typed value:

```text
Path
```

không phải arbitrary string khi đi vào filesystem API.

---

# 8. Path Encoding

Phải phân biệt:

```text
Unicode path
OS-native path
raw filename bytes
```

vì filesystem không phải lúc nào cũng dùng Unicode semantics giống nhau.

---

# 9. Path Normalization

Không được tự động canonicalize mọi path.

Ví dụ:

```text
.
..
symlink
case sensitivity
mount boundary
```

có observable semantics.

---

# 10. Path Security

Security engine có thể cung cấp:

```text
resolve_safely(root, relative_path)
```

với proof:

```text
PathContainmentProof
```

để chống path escape.

---

# 11. Directory

Directory là resource/container:

```text
DirectoryHandle
```

có thể:

```text
open
create
remove
rename
iterate
```

---

# 12. Directory Entry

```text
DirEntry {
    name
    kind
    metadata
}
```

---

# 13. File Kind

```text
Regular
Directory
Symlink
Device
Pipe
Socket
Other
```

---

# 14. Symlink

Symlink phải được phân biệt với target.

API cần explicit:

```text
follow
no_follow
```

---

# 15. Hard Link

Filesystem có thể có:

```text
multiple paths
      ↓
same file object
```

Do đó pathname identity ≠ file identity.

---

# 16. File Metadata

Metadata:

```text
size
timestamps
permissions
owner
inode/file-id
attributes
```

không được trộn với file contents.

---

# 17. File Timestamp

Phân biệt:

```text
created
modified
accessed
metadata_changed
```

OS/filesystem có thể không hỗ trợ tất cả.

---

# 18. File Offset

Sequential handle có logical cursor.

Nhưng API nên hỗ trợ positional I/O:

```text
read_at(offset)
write_at(offset)
```

để tránh shared cursor contention.

---

# 19. Positional I/O

390 đã có:

```text
IO_READ_AT
IO_WRITE_AT
```

400 đưa semantics lên filesystem layer.

---

# 20. Append

Append phải có semantics atomicity rõ ràng.

Không giả định:

```text
seek(end) + write
```

tương đương append.

---

# 21. Sparse File

File có thể chứa logical holes:

```text
data
hole
data
```

filesystem layer phải biểu diễn sparse semantics.

---

# 22. File Size

Logical file size có thể lớn hơn physical blocks thực tế.

Do đó:

```text
logical_size
allocated_size
```

khác nhau.

---

# 23. Preallocation

Có thể:

```text
allocate_range
```

để giảm fragmentation/late allocation.

---

# 24. Truncate

```text
truncate(size)
```

là observable mutation.

Không thể xem như metadata-only optimization.

---

# 25. Rename

Rename semantics cần atomicity contract.

Trong cùng filesystem thường có atomic rename semantics, nhưng cross-filesystem move không tương đương.

---

# 26. Atomic Replace

Pattern quan trọng:

```text
write temp
 ↓
fsync
 ↓
rename
```

có thể tạo atomic publication nếu filesystem contract hỗ trợ.

---

# 27. Crash Consistency

Axiom phải phân biệt:

```text
program-visible state
OS-visible state
persistent state
```

---

# 28. Persistence

`write()` không đồng nghĩa:

```text
durable on stable storage
```

Cần:

```text
flush
sync
persist
```

semantics riêng.

---

# 29. Durability Contract

Có thể có:

```text
None
Buffered
OSVisible
Persistent
Durable
```

nhưng backend guarantee phải rõ.

---

# 30. Persistence Fence

MIR:

```text
IO_PERSISTENCE_FENCE
```

từ 390.

400 xác định semantic meaning ở filesystem level.

---

# 31. Journal

Filesystem có thể sử dụng:

```text
journal
copy-on-write
log structured
```

để thực hiện persistence.

Đây là backend implementation.

---

# 32. File Transaction

Có thể có abstraction:

```text
FileTransaction
```

nhưng không được giả định filesystem nào cũng hỗ trợ atomic multi-file transactions.

---

# 33. Transaction Capability

Nếu backend hỗ trợ:

```text
begin
write
commit
abort
```

thì capability phải explicit.

---

# 34. Database vs File Transaction

395 database transaction có:

```text
ACID
```

400 file transaction chỉ có guarantees backend cung cấp.

Không được đánh đồng hai abstraction.

---

# 35. Memory Mapping

Memory map:

```text
File
 ↓
MappedRegion
```

là storage capability.

---

# 36. Mapping Modes

```text
READ
WRITE
COPY_ON_WRITE
EXECUTE
```

execute mapping phải unsafe/system-level.

---

# 37. Mapping Lifetime

Mapped view:

```text
view<T>
```

không được sống sau mapping.

---

# 38. Mapping + File Resize

Resize/truncate khi mapping tồn tại có thể invalidate mapping.

Compiler/runtime phải có explicit invalidation semantics.

---

# 39. Mapped Persistence

Write vào mapped memory không tự động có nghĩa durable.

Cần:

```text
flush_mapping
persist_mapping
```

---

# 40. Copy-on-Write Mapping

COW mapping:

```text
write
 ↓
private page
```

không sửa file.

Đây là distinct semantic storage mode.

---

# 41. Block Device

Axiom có thể xuống thấp hơn filesystem:

```text
BlockDevice
```

cho systems/storage software.

---

# 42. Block Address

```text
BlockIndex
BlockRange
```

là logical identities.

---

# 43. Sector vs Block

Không được đồng nhất:

```text
hardware sector
filesystem block
application block
```

---

# 44. Alignment

Direct I/O có thể yêu cầu:

```text
buffer alignment
offset alignment
size alignment
```

compiler có thể verify nếu static.

---

# 45. Direct I/O

Direct I/O bypass một phần OS page cache.

Không nên coi là universally faster.

Đây là explicit I/O mode.

---

# 46. Buffered I/O

Normal file I/O có thể dùng OS cache.

Axiom abstraction không expose implementation details trừ khi requested.

---

# 47. Cache

Storage cache:

```text
page cache
application cache
filesystem cache
```

là các layer khác nhau.

---

# 48. Read-Ahead

390 prefetch có thể áp dụng cho filesystem.

---

# 49. Write-Behind

Write-behind cần durability semantics rõ ràng.

Không được gọi `write completed` đồng nghĩa persistent.

---

# 50. Async File I/O

Có thể:

```text
Future<Result<usize, IOError>>
```

nhưng Future chỉ biểu diễn completion.

Backend có thể là:

```text
io_uring
IOCP
kqueue
thread pool
```

---

# 51. Cancellation

Cancel pending I/O cần backend-specific guarantee.

Phải phân biệt:

```text
cancel requested
cancelled
completed
unknown
```

---

# 52. I/O Completion

Completion event phải không được phát hai lần.

---

# 53. File Watcher

Filesystem có thể expose:

```text
watch(path)
```

events:

```text
create
modify
remove
rename
attribute_change
```

---

# 54. Watcher Semantics

File watcher không đảm bảo mọi event đều phản ánh từng write.

Coalescing phải được phép nếu API contract cho phép.

---

# 55. Event Overflow

Nếu watcher queue overflow:

```text
rescan_required
```

có thể là correct recovery semantics.

---

# 56. Virtual Filesystem

Đây là phần quan trọng.

Axiom nên có:

```text
VFS
```

là abstraction:

```text
Path
 ↓
Mount
 ↓
FilesystemBackend
```

---

# 57. VFS Không Bắt Buộc OS

Có thể dùng VFS cho:

```text
OS filesystem
ZIP
TAR
memory FS
network FS
embedded FS
database-backed FS
```

---

# 58. Mount

```text
mount(
    "/assets",
    backend
)
```

nhưng mount authority phải thuộc capability.

---

# 59. VFS Backend

Trait:

```text
trait FileSystem {
    ...
}
```

Concrete:

```text
NativeFs
MemoryFs
ZipFs
TarFs
```

---

# 60. No Class Hierarchy

Đây là interface/trait + struct.

Dynamic backend:

```text
dyn FileSystem
```

chỉ khi runtime polymorphism cần thiết.

---

# 61. In-Memory Filesystem

Rất hữu ích cho testing:

```text
MemoryFs
```

có thể chạy không cần OS disk.

---

# 62. Overlay Filesystem

Có thể:

```text
upper
lower
```

để phục vụ sandbox/build/container.

---

# 63. Archive Filesystem

ZIP/TAR có thể expose read-only VFS.

---

# 64. Resource Filesystem

Executable resources:

```text
assets
fonts
shaders
models
```

có thể expose qua VFS.

---

# 65. Embedded Files

Comptime có thể embed:

```text
const shader = @embed("shader.spv")
```

và compiler đưa bytes vào binary.

---

# 66. Resource Identity

Embedded resource không phải filesystem file.

Phân biệt:

```text
EmbeddedResource
File
```

---

# 67. Content Addressed Storage

Có thể hỗ trợ:

```text
ContentHash
```

làm logical identity.

Ví dụ:

```text
CAS.put(data)
```

---

# 68. CAS

Content-addressed storage rất hữu ích cho Axiom compiler cache.

```text
source
 ↓
hash
 ↓
artifact
```

---

# 69. Build Cache

Axiom compiler có thể sử dụng:

```text
CompilerDB
+
CAS
```

để cache artifacts.

---

# 70. Cache Correctness

Cache key phải chứa toàn bộ semantic inputs:

```text
source
compiler version
target
features
comptime inputs
dependencies
ABI
optimization configuration
```

---

# 71. Incremental Build

Nếu source unchanged:

```text
reuse
```

nhưng chỉ khi dependency graph chứng minh artifact còn valid.

---

# 72. Dependency Graph

CompilerDB nên lưu:

```text
Source
 ↓
HIR
 ↓
MIR
 ↓
Machine
 ↓
Object
```

và dependency edges.

---

# 73. File Dependency

Nếu comptime đọc file:

```text
ReadFilesystem
```

thì file trở thành build dependency.

---

# 74. Generated File

Comptime generation:

```text
generated source/data
```

phải có provenance.

---

# 75. Atomic Cache Publication

Compiler cache artifact nên:

```text
write temp
 ↓
validate/hash
 ↓
atomic rename
```

để tránh corrupt cache.

---

# 76. Locking

Build cache có thể dùng lock.

Nhưng lock không nên kéo vào compiler semantic Core.

---

# 77. File Lock

Có thể:

```text
shared lock
exclusive lock
```

với platform-specific semantics.

Không đánh đồng với Axiom `Mutex`.

---

# 78. Filesystem Lock vs Memory Mutex

Hai loại lock khác nhau:

```text
Mutex
    → memory synchronization

FileLock
    → inter-process filesystem coordination
```

---

# 79. Permissions

Filesystem permission:

```text
read
write
execute
```

không phải Axiom memory capability.

Security layer maps chúng thành authority.

---

# 80. Sandboxing

Một process sandbox có thể chỉ nhận:

```text
Capability<File>
```

cho một subtree.

Không cần ambient filesystem access.

---

# 81. Secure Path Resolution

Concept:

```text
root_capability
 +
relative_path
 →
validated file capability
```

compiler/library có thể enforce no escape.

---

# 82. Encryption-at-Rest

Storage có thể dùng:

```text
EncryptedFile
EncryptedVolume
```

nhưng crypto semantics reuse 394.

---

# 83. Encryption Layer

Không nên hard-code encryption vào File primitive.

Architecture:

```text
File
 ↓
Stream
 ↓
AEAD
 ↓
EncryptedFile
```

---

# 84. Compression Layer

Tương tự:

```text
File
 ↓
Stream
 ↓
Compression
```

---

# 85. Compression

Codec library:

```text
gzip
zstd
lz4
brotli
```

có thể stream.

Không bắt buộc Core.

---

# 86. Storage Pipeline

Ví dụ:

```text
File
 ↓
Mapped/Read
 ↓
Decompress
 ↓
Decode
 ↓
Tensor
```

có thể zero-copy ở các boundary thích hợp.

---

# 87. Persistent Tensor

395/369 tensor storage có thể map persistent storage.

Ví dụ:

```text
MappedTensor
```

nhưng mutation/persistence semantics phải explicit.

---

# 88. Database Storage

395 có thể dùng 400:

```text
Database
 ↓
File
 ↓
Mapping
 ↓
Block storage
```

không ngược dependency.

---

# 89. WAL

Database WAL có thể dùng:

```text
File
write_at
flush
persist
```

từ storage layer.

---

# 90. Crash Recovery

400 cung cấp primitives:

```text
AtomicWrite
DurabilityFence
RecoveryMarker
```

database xây semantics cao hơn.

---

# 91. Storage Error Model

Cần structured errors:

```text
NotFound
AlreadyExists
PermissionDenied
InvalidPath
NotDirectory
IsDirectory
NoSpace
ReadOnly
Busy
IoFailure
Corrupt
Unsupported
Interrupted
TimedOut
Cancelled
```

---

# 92. Error Identity

Không nên parse error message string.

Error category/type phải machine-readable.

---

# 93. Retry

Không phải mọi filesystem error đều retryable.

Ví dụ:

```text
NoSpace
PermissionDenied
InvalidPath
```

không nên retry mù quáng.

---

# 94. Idempotency

`write_at` có thể không idempotent nếu underlying semantics phức tạp.

Retry contract phải explicit.

---

# 95. Storage Cost Model

Compiler/runtime có thể biết:

```text
sequential
random
small IO
large IO
latency-sensitive
throughput-oriented
```

để tối ưu buffering.

---

# 96. Storage Layout

389 có thể tối ưu:

```text
record layout
block layout
page layout
compression
packing
```

nhưng không được thay đổi external format nếu ABI/serialization observable.

---

# 97. Serialization

395 serialization layer có thể target:

```text
file
stream
memory
network
```

---

# 98. Persistent Schema

Database schema khác filesystem metadata.

Không trộn hai semantic layers.

---

# 99. CompilerDB

400 bổ sung:

```text
StorageDB
StorageResourceDB
StorageCapabilityDB
StorageBackendDB
StorageErrorDB

FileDB
FileHandleDB
FileObjectDB
FileIdentityDB
FileOpenDB
FileAccessDB
FilePermissionDB
FileOffsetDB
FileSizeDB
FileMetadataDB
FileTimestampDB
FileAttributeDB
FileLinkDB
FileHardLinkDB
FileSymlinkDB
FileSparseDB
FileAllocationDB
FilePreallocationDB
FileTruncateDB
FileRenameDB
FileAppendDB

DirectoryDB
DirectoryHandleDB
DirectoryEntryDB
DirectoryIterationDB
DirectoryMutationDB

PathDB
PathComponentDB
PathEncodingDB
PathNormalizationDB
PathResolutionDB
PathCanonicalizationDB
PathSecurityDB
PathContainmentDB

MappingDB
MappedRegionDB
MappingModeDB
MappingLifetimeDB
MappingInvalidationDB
MappingFlushDB
MappingPersistenceDB
MappingCowDB

BlockDeviceDB
BlockDeviceCapabilityDB
BlockAddressDB
BlockRangeDB
BlockGeometryDB
BlockAlignmentDB
DirectIoDB

FileIoDB
PositionalIoDB
SequentialIoDB
AppendIoDB
BufferedIoDB
DirectIoDB
ReadAheadDB
WriteBehindDB
IoCompletionDB
IoCancellationDB

PersistenceDB
DurabilityDB
DurabilityContractDB
PersistenceFenceDB
CrashConsistencyDB
AtomicWriteDB
AtomicReplaceDB
FileTransactionDB
FileTransactionCapabilityDB

JournalDB
CopyOnWriteStorageDB
LogStructuredStorageDB

FileWatchDB
FileWatchEventDB
FileWatchOverflowDB
FileWatchRescanDB

VfsDB
VfsMountDB
VfsBackendDB
VfsPathDB
VfsCapabilityDB
VfsOverlayDB
MemoryFsDB
ArchiveFsDB
NativeFsDB
ResourceFsDB

ArchiveDB
ZipFsDB
TarFsDB

EmbeddedResourceDB
EmbeddedFileDB
ResourceIdentityDB

ContentAddressedStorageDB
ContentHashDB
CasObjectDB
CasIndexDB

BuildCacheDB
BuildArtifactDB
BuildDependencyDB
BuildProvenanceDB
BuildCacheKeyDB
BuildCachePublicationDB
IncrementalBuildDB

StorageCompressionDB
StorageEncryptionDB
StoragePipelineDB

StorageTensorDB
StorageDatabaseDB
StorageWalDB

StorageCostModelDB
StorageOptimizationDB
StorageVerificationDB
```

---

# 100. MIR

```text id="6v5e6h"
FILE_OPEN
FILE_CLOSE
FILE_DUP
FILE_READ
FILE_WRITE
FILE_READ_AT
FILE_WRITE_AT
FILE_APPEND
FILE_SEEK
FILE_TRUNCATE
FILE_STAT
FILE_SET_METADATA
FILE_RENAME
FILE_REMOVE
FILE_LINK
FILE_SYMLINK
FILE_READLINK

DIR_OPEN
DIR_CLOSE
DIR_CREATE
DIR_REMOVE
DIR_READ
DIR_RENAME

PATH_RESOLVE
PATH_CANONICALIZE
PATH_VALIDATE

MAP_FILE
UNMAP_FILE
MAP_FLUSH
MAP_PERSIST
MAP_COW

BLOCK_OPEN
BLOCK_READ
BLOCK_WRITE
BLOCK_FLUSH
BLOCK_PERSIST
BLOCK_DISCARD

IO_DIRECT
IO_BUFFERED
IO_READ_AHEAD
IO_WRITE_BEHIND

IO_CANCEL_REQUEST
IO_COMPLETION

PERSISTENCE_FENCE
ATOMIC_WRITE
ATOMIC_REPLACE

FILE_TX_BEGIN
FILE_TX_WRITE
FILE_TX_COMMIT
FILE_TX_ABORT

FILE_WATCH
FILE_WATCH_EVENT
FILE_WATCH_OVERFLOW
FILE_WATCH_RESCAN

VFS_MOUNT
VFS_UNMOUNT
VFS_RESOLVE
VFS_OPEN

CAS_LOOKUP
CAS_INSERT
CAS_VERIFY

CACHE_LOOKUP
CACHE_INSERT
CACHE_PUBLISH
CACHE_INVALIDATE

STORAGE_COMPRESS
STORAGE_DECOMPRESS
STORAGE_ENCRYPT
STORAGE_DECRYPT
```

---

# 101. Proof System

```text id="t6y3zo"
FileOwnershipProof
FileCapabilityProof
FileIdentityProof
FileAccessProof
FileLifetimeProof

PathEncodingProof
PathNormalizationProof
PathResolutionProof
PathContainmentProof
PathSecurityProof

DirectoryProof
DirectoryEntryProof
SymlinkProof
HardLinkProof

FileSizeProof
FileOffsetProof
FileAlignmentProof
SparseFileProof
FileAllocationProof

MappingLifetimeProof
MappingBoundsProof
MappingPermissionProof
MappingInvalidationProof
MappingPersistenceProof
MappingCowProof

DirectIoAlignmentProof
BlockRangeProof
BlockDeviceProof

IoOrderingProof
IoCompletionProof
IoCancellationProof
IoRetryProof
IoIdempotencyProof

AtomicWriteProof
AtomicReplaceProof
DurabilityProof
PersistenceProof
CrashConsistencyProof
FileTransactionProof

FileWatchProof
FileWatchOrderingProof
FileWatchOverflowProof

VfsCapabilityProof
VfsMountProof
VfsResolutionProof
VfsBackendProof
VfsOverlayProof

ArchiveProof
EmbeddedResourceProof
ContentHashProof
CasIntegrityProof

BuildCacheProof
BuildCacheKeyProof
BuildDependencyProof
BuildPublicationProof
IncrementalBuildProof

StorageCompressionProof
StorageEncryptionProof
StoragePipelineProof
StorageZeroCopyProof

StorageTensorProof
StorageDatabaseProof
StorageWalProof

StorageCostModelProof
StorageOptimizationProof
StorageVerificationProof
```

---

# 102. Invariants

### `ASTORE-01`
File handle phải có ownership/lifetime rõ ràng.

### `ASTORE-02`
Path không phải file identity.

### `ASTORE-03`
File identity phải ổn định theo semantics backend cho phép.

### `ASTORE-04`
Open flags phải được biểu diễn rõ ràng.

### `ASTORE-05`
Filesystem capability phải giới hạn authority.

### `ASTORE-06`
Path encoding không được tự động biến đổi ngoài contract.

### `ASTORE-07`
Path normalization không được thay đổi symlink semantics ngoài contract.

### `ASTORE-08`
Symlink và target phải là hai logical entities khác nhau.

### `ASTORE-09`
Hard links phải được xử lý như nhiều names của một underlying file object.

### `ASTORE-10`
Positional I/O không được phụ thuộc shared file cursor.

### `ASTORE-11`
Append semantics không được mô phỏng bằng seek + write nếu atomicity khác nhau.

### `ASTORE-12`
Logical file size và physical allocation phải được phân biệt.

### `ASTORE-13`
Sparse-file holes phải có semantics xác định.

### `ASTORE-14`
Memory mapping phải obey ownership/lifetime/capability model.

### `ASTORE-15`
Truncate/resize không được silently invalidate live mappings.

### `ASTORE-16`
Mapping flush không mặc định đồng nghĩa persistent durability.

### `ASTORE-17`
Direct I/O phải obey alignment contract.

### `ASTORE-18`
Buffered I/O không được bị mô tả như durable I/O.

### `ASTORE-19`
`write()` completion không mặc định có nghĩa stable-storage persistence.

### `ASTORE-20`
Persistence fence phải có semantics rõ ràng.

### `ASTORE-21`
Atomic replace chỉ được claim atomic khi backend contract chứng minh được.

### `ASTORE-22`
File transaction không được tự động mang ACID semantics của database.

### `ASTORE-23`
I/O cancellation phải phân biệt request, cancelled và completed.

### `ASTORE-24`
Filesystem watcher phải cho phép event coalescing nếu contract công bố điều đó.

### `ASTORE-25`
Watcher overflow phải có recovery semantics.

### `ASTORE-26`
VFS backend phải không yêu cầu programmer thay đổi filesystem-facing semantics.

### `ASTORE-27`
CAS artifact chỉ được reuse khi toàn bộ semantic build inputs tương ứng.

### `ASTORE-28`
Cache publication phải tránh observable partial/corrupt artifact.

### `ASTORE-29`
Storage compression/encryption phải preserve logical data semantics.

### `ASTORE-30`
Chương trình không sử dụng filesystem/storage subsystem không được kéo theo storage runtime bắt buộc.

---

# 103. Điểm kiến trúc đặc biệt quan trọng

Task 400 hoàn thiện một chuỗi rất quan trọng:

```text
              ┌──────────────┐
              │ Axiom Value  │
              └──────┬───────┘
                     │
             Ownership/Capability
                     │
        ┌────────────┼────────────┐
        ▼            ▼            ▼
     Memory        Stream       Storage
        │            │            │
        ▼            ▼            ▼
      Tensor       Network       File
        │            │            │
        └────────────┼────────────┘
                     ▼
                 Database
                     │
                     ▼
                Persistence
```

Và quan trọng nhất, **File → Database → Media → ML → GUI** không cần mỗi subsystem tự phát minh một memory/ownership model riêng.

Ví dụ một pipeline có thể đạt tới:

```text
SSD
 ↓
DMA / OS buffer
 ↓
Mapped / zero-copy buffer
 ↓
Decoder
 ↓
VideoFrame
 ↓
TensorView
 ↓
GPU
 ↓
ML
 ↓
Render
```

Trong đó compiler có thể tối ưu:

- allocation;
- buffer reuse;
- layout;
- copies;
- SIMD;
- GPU transfer;
- lifetime;
- scheduling;

nhưng **không được phá vỡ ownership, persistence, synchronization hoặc external ABI semantics**.

Đây là một bước quan trọng để Axiom không chỉ là một programming language nhanh, mà có thể trở thành **một hệ thống native end-to-end từ machine memory → OS → storage → database → media → GPU → application**.