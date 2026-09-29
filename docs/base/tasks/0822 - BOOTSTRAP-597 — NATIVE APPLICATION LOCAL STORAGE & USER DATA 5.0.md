# BOOTSTRAP-597 — NATIVE APPLICATION LOCAL STORAGE & USER DATA 5.0

**Phạm vi chính:** chuẩn hóa toàn bộ dữ liệu **có thể ghi** do ứng dụng tạo ra sau khi cài đặt/chạy, tách hoàn toàn khỏi immutable resources của `596`.

Mục tiêu là để code Axiom **không bao giờ phải biết** `%APPDATA%`, `%LOCALAPPDATA%`, `$HOME/.config`, XDG, sandbox container path của iOS/Android hay cơ chế persistence riêng của WASM.

---

## 597.1. Architectural Boundary

`596` quản lý **immutable application resources**.

`597` quản lý **mutable application/user data**.

```text
                    AXIOM APPLICATION
                           │
             ┌─────────────┴─────────────┐
             │                           │
       Resource Manager             Storage Manager
             │                           │
          BOOTSTRAP-596             BOOTSTRAP-597
             │                           │
     Immutable resources          Writable state
             │                           │
       ┌─────┼─────┐        ┌──────┬────┼──────┬──────┐
       ▼     ▼     ▼        ▼      ▼    ▼      ▼      ▼
     Image Font Audio     AppData Cache Temp Documents DB
```

**Hard boundary:**

```text
Resource ≠ UserData
Resource ≠ Cache
Resource ≠ Temp
ApplicationData ≠ Documents
Cache ≠ Backup-required data
```

---

# 597.2. Design Goals

Storage API phải:

1. cross-platform;
2. sandbox-aware;
3. deterministic về semantics;
4. atomic;
5. crash-safe;
6. concurrency-safe;
7. migration-friendly;
8. quota-aware;
9. backup-aware;
10. observable;
11. AI-readable;
12. không phụ thuộc filesystem layout của OS;
13. không ép application dùng database;
14. không ép application dùng filesystem;
15. cho phép native filesystem access khi cần;
16. hỗ trợ WASM persistence;
17. hỗ trợ portable mode;
18. hỗ trợ offline;
19. không tạo hidden global state.

---

# 597.3. Storage Scope Model

Axiom định nghĩa các **storage scope** chuẩn.

```text
StorageScope
├── ApplicationData
├── UserData
├── Cache
├── Temporary
├── Documents
├── SharedData
├── Database
└── Portable
```

Mỗi scope có semantics riêng.

---

# 597.4. ApplicationData

Dữ liệu trạng thái cần tồn tại giữa các lần chạy.

Ví dụ:

```text
settings
recent-projects
application-state
workspace-state
credentials metadata
window layout
user-created application configuration
```

Không được coi ApplicationData là cache.

---

# 597.5. UserData

Dữ liệu thuộc về người dùng và có giá trị lâu dài.

Ví dụ:

```text
profiles
saved projects
user-created presets
templates
custom themes
application libraries
```

---

# 597.6. Cache

Cache có thể xóa bất kỳ lúc nào mà ứng dụng vẫn phải hoạt động chính xác.

```text
Cache:
    reproducible = true
    disposable = true
    backup_required = false
```

Application **không được lưu dữ liệu duy nhất** vào Cache.

---

# 597.7. Temporary

Dữ liệu tồn tại trong thời gian ngắn:

```text
temporary files
scratch buffers
intermediate compiler outputs
IPC temporary files
download staging
atomic replacement staging
```

OS có thể xóa Temp bất kỳ lúc nào.

---

# 597.8. Documents

Documents đại diện cho dữ liệu người dùng mà ứng dụng **công khai cho người dùng quản lý**.

Ví dụ:

```text
project.ax
document.txt
photo.png
model.axmodel
```

Documents không nhất thiết nằm trong private application sandbox.

---

# 597.9. SharedData

Dữ liệu được chia sẻ giữa các ứng dụng hoặc components khi platform cho phép.

Quyền truy cập phải explicit.

```text
SharedData
    ↓
Capability
    ↓
Access
```

Không được mặc định cấp quyền.

---

# 597.10. Database Scope

Database là logical storage scope.

```text
StorageManager
      │
      ├── FileStorage
      └── DatabaseStorage
```

`597` không định nghĩa lại engine database của `455`.

Nó định nghĩa **database placement/lifecycle boundary**.

---

# 597.11. Portable

Portable storage đặt dữ liệu cạnh executable/application bundle hoặc tại location do deployment configuration chỉ định.

```text
app/
├── app.exe
├── resources/
├── runtime/
└── data/
```

Portable mode phải explicit.

---

# 597.12. Storage Manager

```text
interface StorageManager {
    root(scope: StorageScope) -> StorageRoot
    open(scope, path, mode) -> Result<FileHandle>
    create(scope, path) -> Result<FileHandle>
    remove(scope, path) -> Result<void>
    exists(scope, path) -> bool
    metadata(scope, path) -> Result<FileMetadata>
    list(scope, path) -> Result<DirectoryIterator>
    atomic_write(scope, path, data) -> Result<void>
    watch(scope, path, options) -> Result<FileWatcher>
}
```

---

# 597.13. StorageRoot

```text
struct StorageRoot {
    scope: StorageScope
    identity: StorageIdentity
    capabilities: StorageCapabilities
}
```

Không expose raw OS path ở API high-level.

---

# 597.14. Logical Path

Axiom sử dụng logical path:

```text
"settings/ui.json"
"projects/demo.axproj"
"cache/shader/abc.bin"
```

Không sử dụng:

```text
"C:\Users\..."
"/home/user/..."
```

trong application-level API.

---

# 597.15. Path Grammar

```text
storage-path :=
    segment ("/" segment)*

segment :=
    UTF8-safe-name
```

Không cho phép:

```text
..
absolute path
drive prefix
UNC path
platform separator
NUL
```

---

# 597.16. Path Traversal

Resolver phải reject:

```text
../secret
a/../../secret
/a/b
C:/secret
\\server\share
```

trước khi platform backend được gọi.

---

# 597.17. Canonical Path

Mọi path phải canonicalize trước khi:

```text
open
create
delete
rename
watch
lock
```

---

# 597.18. Symlink Policy

Storage scope mặc định:

```text
follow_external_symlink = false
```

Symlink có thể escape sandbox nên phải được kiểm tra.

---

# 597.19. Storage Identity

```text
struct StorageIdentity {
    application_id: AppID
    user_id: optional<UserID>
    scope: StorageScope
    platform: PlatformID
    generation: u64
}
```

Identity không phụ thuộc physical path.

---

# 597.20. Physical Path Mapping

Platform adapter chịu trách nhiệm:

```text
Logical StorageRoot
        ↓
PlatformStorageAdapter
        ↓
Physical path / sandbox URI / IndexedDB / virtual FS
```

Application không được tự suy luận mapping.

---

# 597.21. Platform Adapter

```text
trait StorageBackend {
    resolve_root(scope) -> Result<BackendRoot>
    open(...)
    read(...)
    write(...)
    rename(...)
    remove(...)
    list(...)
    metadata(...)
    watch(...)
    quota(...)
    flush(...)
}
```

---

# 597.22. Windows Mapping

Default conceptual mapping:

```text
ApplicationData → Roaming/AppData policy
Cache           → Local AppData cache
Temporary       → OS temp
Documents       → user Documents / explicit picker
```

Exact path do platform backend quyết định.

---

# 597.23. Linux Mapping

Backend hỗ trợ XDG-style mapping:

```text
ApplicationData → config/data policy
Cache           → cache policy
Temporary       → runtime/temp
Documents       → user documents
```

Axiom không hard-code XDG path vào compiler.

---

# 597.24. macOS Mapping

Backend sử dụng application container / user Library semantics.

```text
ApplicationData
Cache
Temporary
Documents
```

được ánh xạ độc lập.

---

# 597.25. iOS

iOS sandbox là bắt buộc.

```text
ApplicationData → Application Support
Cache           → Caches
Temporary       → tmp
Documents       → Documents / security-scoped resource
```

Axiom API giữ nguyên.

---

# 597.26. Android

Backend ánh xạ:

```text
ApplicationData → app-private storage
Cache           → cache directory
Temporary       → cache/temp policy
Documents       → user-selected/shared storage
```

Storage permission không được ngầm cấp.

---

# 597.27. WASM

WASM backend có thể dùng:

```text
Memory filesystem
IndexedDB
Origin Private File System
Host-provided filesystem
```

Tùy WASM environment.

Application vẫn gọi:

```text
storage.open(...)
```

---

# 597.28. WASM Persistence

Backend phải expose:

```text
persistent: bool
```

Nếu persistence không khả dụng:

```text
StorageError::PersistenceUnavailable
```

Không giả vờ rằng dữ liệu đã được persist.

---

# 597.29. Storage Capability

```text
StorageCapabilities {
    readable
    writable
    persistent
    atomic_rename
    durable_flush
    mmap
    watch
    locks
    quota
    backup
}
```

Application có thể query capability.

---

# 597.30. Capability-Based Access

Storage access được kiểm soát theo capability.

```text
StorageCapability {
    scope
    permissions
    lifetime
}
```

---

# 597.31. Permissions

```text
StoragePermission
├── Read
├── Write
├── Create
├── Delete
├── Rename
├── Watch
├── Share
└── Persist
```

---

# 597.32. Default Permission

ApplicationData:

```text
Read + Write + Create + Delete + Rename
```

Documents:

```text
Read/Write chỉ khi user/platform cấp quyền
```

SharedData:

```text
Explicit
```

---

# 597.33. File Handle

```text
struct FileHandle {
    identity: FileIdentity
    mode: FileMode
    capabilities: FileCapabilities
}
```

Handle ownership tuân theo `423`.

---

# 597.34. File Modes

```text
Read
Write
ReadWrite
Append
Create
CreateNew
Truncate
```

Các flag có thể kết hợp nhưng backend phải validate.

---

# 597.35. File Identity

```text
FileIdentity {
    storage: StorageIdentity
    logical_path: Path
    generation: u64
}
```

Không dùng physical inode/file ID làm identity duy nhất.

---

# 597.36. File Metadata

```text
FileMetadata {
    identity
    kind
    size
    modified_time
    created_time
    permissions
    content_id: optional<ContentID>
}
```

---

# 597.37. File Kind

```text
File
Directory
Symlink
Other
```

High-level Storage API mặc định không follow `Symlink`.

---

# 597.38. Read API

```text
read(handle, buffer) -> Result<usize>
read_all(handle) -> Result<Bytes>
read_range(handle, offset, length) -> Result<Bytes>
```

`read_all` không được dùng cho large resources nếu streaming API phù hợp.

---

# 597.39. Write API

```text
write(handle, bytes) -> Result<usize>
flush(handle) -> Result<void>
sync(handle) -> Result<void>
```

`flush` và `sync` có semantics khác nhau.

---

# 597.40. Flush

`flush` đảm bảo dữ liệu được đẩy qua userspace/runtime buffering.

Không nhất thiết đảm bảo power-loss durability.

---

# 597.41. Sync

`sync` yêu cầu backend thực hiện mức durability cao nhất mà platform hỗ trợ.

---

# 597.42. Durability Contract

```text
Durability
├── Volatile
├── Buffered
├── Persisted
└── Durable
```

Backend phải báo mức thực tế.

---

# 597.43. Atomic Write

API chuẩn:

```text
atomic_write(
    scope,
    path,
    bytes,
    options
)
```

Semantics:

```text
old file
   │
   ├── write temp
   ├── flush
   ├── sync
   ├── atomic replace
   └── sync directory if supported
   │
   ▼
new file
```

---

# 597.44. Atomicity

Atomic write phải đảm bảo:

```text
reader sees OLD
hoặc
reader sees NEW
```

Không được thấy partial content.

---

# 597.45. Crash During Atomic Write

Nếu process crash:

```text
OLD
NEW
```

một trong hai phải remain valid.

Temporary staging file có thể tồn tại và được cleanup.

---

# 597.46. Atomic Rename

Nếu backend không hỗ trợ atomic rename:

```text
Result::AtomicOperationUnsupported
```

Không được âm thầm downgrade nếu caller yêu cầu atomicity.

---

# 597.47. Replace Options

```text
ReplacePolicy {
    overwrite: bool
    preserve_metadata: bool
    require_atomic: bool
    durability: Durability
}
```

---

# 597.48. Safe Configuration Update

Configuration phải dùng:

```text
parse
→ validate
→ write temporary
→ sync
→ atomic replace
```

Không ghi trực tiếp file configuration đang hoạt động.

---

# 597.49. Versioned Data

Mutable application data nên có:

```text
DataSchemaID
DataVersion
```

---

# 597.50. Migration

```text
Migration {
    from: Version
    to: Version
    migrate(input, output)
}
```

Migration phải deterministic.

---

# 597.51. Migration State Machine

```text
Detected
   ↓
Validated
   ↓
Staged
   ↓
Migrating
   ↓
Verified
   ↓
Committed
```

Failure:

```text
Migrating → RolledBack
```

---

# 597.52. Migration Must Not Destroy Original

Default:

```text
original data
      +
staging migration
      ↓
verified output
      ↓
atomic replace
```

---

# 597.53. Migration Idempotency

Migration nên idempotent hoặc có journal.

```text
migration(id, from, to)
```

không được chạy nửa chừng mà làm mất khả năng recovery.

---

# 597.54. Migration Journal

```text
MigrationJournal {
    operation_id
    source_version
    target_version
    stage
    source_identity
    output_identity
}
```

---

# 597.55. Startup Migration

Application startup:

```text
open storage
↓
inspect schema
↓
migration required?
├── no → continue
└── yes → migrate
↓
validate
↓
start application
```

---

# 597.56. Migration Failure

Không được startup với data state không xác định.

Possible policy:

```text
MigrationFailed
RecoveryRequired
ReadOnlyRecovery
```

---

# 597.57. Backup Boundary

`ApplicationData` có thể backup.

`Cache` mặc định không.

`Temporary` không.

`Documents` thường có.

---

# 597.58. Backup Policy

```text
BackupPolicy {
    enabled
    priority
    excluded
    encrypted
    restore_behavior
}
```

---

# 597.59. Backup Metadata

Mỗi storage scope expose:

```text
backup_class:
    Required
    Recommended
    Disposable
    External
```

---

# 597.60. Restore

Restore phải:

```text
validate
→ stage
→ migrate if needed
→ verify
→ activate
```

Không overwrite live state trực tiếp.

---

# 597.61. Restore Conflict

```text
RestoreConflict {
    existing_version
    incoming_version
    policy
}
```

Policies:

```text
Reject
Replace
Merge
KeepExisting
```

`Merge` phải do application/data layer định nghĩa.

---

# 597.62. Cache Semantics

Cache entry:

```text
CacheEntry {
    key
    content_id
    created
    expires
    size
    cost
}
```

---

# 597.63. Cache Correctness

Cache phải luôn có thể rebuild từ source-of-truth.

```text
Source Data → Cache
```

không được:

```text
Cache → only copy of user data
```

---

# 597.64. Cache Eviction

Các policy:

```text
LRU
LFU
TTL
SizeBound
CostAware
Manual
```

Backend có thể dùng policy kết hợp.

---

# 597.65. Cache Quota

Cache phải có quota độc lập.

```text
CacheQuota {
    max_bytes
    max_entries
}
```

---

# 597.66. Temporary Cleanup

Startup có thể cleanup stale temp entries.

Không được xóa temp của process đang sống.

---

# 597.67. Temp Ownership

```text
TempEntry {
    owner_process
    owner_generation
    creation_time
}
```

---

# 597.68. Process Crash Cleanup

Backend có thể cleanup dựa trên:

```text
process identity
lease
heartbeat
startup scan
```

---

# 597.69. Lease

Temporary resource có thể có lease:

```text
TempLease {
    id
    expires
    renewal
}
```

---

# 597.70. Documents

Documents được chia thành:

```text
PrivateDocument
UserSelectedDocument
SharedDocument
ExportedDocument
```

---

# 597.71. User File Picker Boundary

Axiom application không tự truy cập arbitrary Documents.

Platform picker trả về:

```text
DocumentHandle
```

---

# 597.72. DocumentHandle

```text
DocumentHandle {
    provider
    identity
    permissions
    lifetime
}
```

Có thể đại diện cho:

- filesystem file;
- iOS security-scoped resource;
- Android document URI;
- browser file handle.

---

# 597.73. Security-Scoped Access

Nếu platform yêu cầu grant tạm thời:

```text
acquire
→ use
→ release
```

Axiom runtime quản lý lifetime.

---

# 597.74. Persistent Document Grant

Nếu platform hỗ trợ persistent permission:

```text
grant.save()
grant.revoke()
```

Không giả định mọi platform hỗ trợ.

---

# 597.75. File Locking

Axiom cung cấp logical lock:

```text
FileLock {
    shared
    exclusive
}
```

---

# 597.76. Advisory Lock

Mặc định file lock là advisory.

Application khác không sử dụng Axiom có thể không tôn trọng nó.

---

# 597.77. Exclusive Lock

```text
acquire_exclusive(path)
```

được dùng cho:

```text
database migration
project mutation
single-writer state
```

---

# 597.78. Lock Lifetime

Lock gắn với handle/lease.

Process crash phải giải phóng lock ở backend nếu OS hỗ trợ.

---

# 597.79. Lock Timeout

```text
LockOptions {
    timeout
    cancellation
}
```

---

# 597.80. Optimistic Concurrency

File metadata có:

```text
generation
content_id
modified_time
```

Application có thể CAS:

```text
replace_if_current(identity, expected_content_id, new_data)
```

---

# 597.81. Compare-And-Swap Storage

```text
CAS:
    expected = ContentID_old
    new      = ContentID_new
```

Nếu mismatch:

```text
StorageError::Conflict
```

---

# 597.82. Multi-Process Safety

Storage Manager phải hỗ trợ:

```text
process A
process B
process C
```

cùng truy cập mà không phá semantics.

Application chịu trách nhiệm protocol nếu dữ liệu phức tạp.

---

# 597.83. Directory Operations

```text
create_dir
create_dir_all
remove_dir
remove_dir_recursive
list
```

Recursive deletion phải explicit.

---

# 597.84. Rename

```text
rename(old, new)
```

Phải trả về capability/atomicity metadata.

---

# 597.85. Cross-Directory Rename

Nếu backend không hỗ trợ atomic cross-directory rename:

```text
AtomicOperationUnsupported
```

khi `require_atomic=true`.

---

# 597.86. Storage Transactions

Filesystem không được giả vờ có transaction toàn hệ thống.

Axiom chỉ cung cấp:

```text
AtomicFileUpdate
```

và transaction primitive riêng của database ở `455`.

---

# 597.87. Database Boundary

```text
StorageManager
      │
      ▼
DatabaseLocation
      │
      ▼
BOOTSTRAP-455 database subsystem
```

Storage Manager không biết SQL/transaction internals.

---

# 597.88. Database Placement

```text
db.open(
    storage.database("main")
)
```

Database có thể nằm ở ApplicationData hoặc UserData theo policy.

---

# 597.89. Database Backup

Database backup phải sử dụng database engine's consistency mechanism.

Không được copy file database sống một cách mù quáng.

---

# 597.90. Memory Mapping

`455` và `597` phải interoperable:

```text
FileHandle
    ↓
map()
    ↓
MappedRegion
```

---

# 597.91. Mmap Safety

Mapped region giữ reference tới file backing storage.

```text
FileHandle
    │
    └── MappedRegion
```

Không được unmap khi region còn sống.

---

# 597.92. Mmap Mutability

```text
ReadOnly
ReadWrite
CopyOnWrite
```

Backend chỉ expose mode platform hỗ trợ.

---

# 597.93. Zero-Copy

Nếu file storage và consumer cho phép:

```text
Storage
   ↓
MappedRegion
   ↓
Parser / Decoder
```

không copy.

---

# 597.94. Streaming

Large data:

```text
open
→ read chunk
→ process
→ read chunk
→ ...
```

Không ép `read_all`.

---

# 597.95. Async Storage

Storage operations có async variant:

```text
read_async
write_async
flush_async
sync_async
```

Không yêu cầu OS async I/O tuyệt đối; runtime có thể dùng worker pool.

---

# 597.96. Cancellation

Async operation phải hỗ trợ cancellation khi backend cho phép.

Cancellation không đồng nghĩa rollback.

---

# 597.97. Partial Write

Nếu `write()` trả về số byte nhỏ hơn requested:

```text
remaining bytes
```

caller phải tiếp tục hoặc API `write_all()` thực hiện loop.

---

# 597.98. write_all

```text
write_all(handle, data)
```

chỉ thành công khi toàn bộ buffer được ghi.

---

# 597.99. Error Model

```text
StorageError
├── NotFound
├── AlreadyExists
├── PermissionDenied
├── InvalidPath
├── InvalidHandle
├── Busy
├── Locked
├── Conflict
├── QuotaExceeded
├── ReadOnly
├── Unsupported
├── AtomicityUnsupported
├── PersistenceUnavailable
├── IntegrityFailure
├── CorruptedData
├── IoFailure
├── Cancelled
└── Unknown
```

---

# 597.100. Error Provenance

Mọi storage error phải có:

```text
operation
scope
logical_path
backend
native_error
recoverability
```

---

# 597.101. Recoverability

```text
Recoverability
├── Retry
├── UserAction
├── Migration
├── Fatal
└── Unknown
```

---

# 597.102. Quota Model

```text
StorageQuota {
    capacity
    used
    available
    reserved
}
```

---

# 597.103. Quota Scope

Quota có thể áp dụng:

```text
per application
per user
per storage scope
per origin
```

---

# 597.104. Quota Reservation

Large operation có thể:

```text
reserve(bytes)
→ write
→ commit
```

hoặc:

```text
release()
```

---

# 597.105. Quota Race

Reservation phải được backend enforce nếu platform hỗ trợ.

Không dựa vào:

```text
available >= required
```

đơn thuần.

---

# 597.106. Storage Statistics

```text
StorageStats {
    file_count
    directory_count
    logical_bytes
    physical_bytes
    cache_bytes
    mapped_bytes
}
```

---

# 597.107. File Watching

```text
watch(scope, path, options)
```

trả:

```text
FileWatcher
```

---

# 597.108. File Events

```text
Created
Modified
Deleted
Renamed
Moved
MetadataChanged
Overflow
RescanRequired
```

---

# 597.109. Watch Semantics

Event watcher là **eventual notification**, không phải transaction log.

Có thể:

```text
coalesce
duplicate
reorder
overflow
```

theo backend.

---

# 597.110. Correct Watch Algorithm

Application không được tin rằng event stream là source of truth.

```text
event
 ↓
invalidate
 ↓
rescan/query
 ↓
update state
```

---

# 597.111. Watch Overflow

Khi queue overflow:

```text
Overflow
    ↓
invalidate subtree
    ↓
full rescan
```

---

# 597.112. Rename Event

Watcher phải cố gắng cung cấp:

```text
old_path
new_path
```

nhưng backend có thể chỉ cung cấp generic modification.

---

# 597.113. Watch Lifetime

Watcher tuân theo ownership model `423`.

Drop watcher:

```text
stop notifications
release resources
```

---

# 597.114. Data Journaling

Application-level journaling được hỗ trợ như primitive:

```text
Journal
├── Begin
├── Operation
├── Commit
└── Abort
```

Nhưng không biến filesystem thành transactional database.

---

# 597.115. Recovery Journal

Journal có thể dùng cho:

```text
migration
large asset replacement
multi-file project update
```

---

# 597.116. Multi-File Atomic Update

Không có atomicity tuyệt đối giữa nhiều filesystem objects.

Axiom cung cấp:

```text
transaction-like staged directory protocol
```

với crash recovery.

---

# 597.117. Staged Commit

```text
live/
stage/
journal

stage changes
↓
verify
↓
commit marker
↓
activate
```

---

# 597.118. Crash Recovery

Startup:

```text
find journal
↓
commit marker?
├── yes → complete
└── no  → rollback
```

---

# 597.119. Storage Generations

Mỗi mutable storage root có generation:

```text
generation += 1
```

sau migration/restore/replacement lớn.

---

# 597.120. Stale Handles

Handle cũ phải phát hiện:

```text
StorageError::StaleHandle
```

khi semantics yêu cầu.

---

# 597.121. Resource-vs-Storage Handle

Không được nhầm:

```text
ResourceHandle
```

với:

```text
FileHandle
```

Resource của `596` có immutable semantics.

Storage của `597` mutable semantics.

---

# 597.122. Content Identity

Nếu backend có thể hash content:

```text
ContentID
```

được dùng để:

- dedup;
- cache;
- migration verification;
- conflict detection;
- provenance.

---

# 597.123. Hashing Policy

Không bắt buộc hash mỗi lần đọc.

Có thể:

```text
lazy
on-write
on-demand
verified
```

---

# 597.124. Integrity

Ứng dụng có thể yêu cầu:

```text
verify_content(path, expected_content_id)
```

---

# 597.125. Tamper Detection

Nếu content mismatch:

```text
IntegrityFailure
```

không được tự động sửa nếu chưa có trusted source.

---

# 597.126. Encryption Boundary

`597` không định nghĩa cryptographic primitives.

Encryption thuộc crypto subsystem.

Storage chỉ expose:

```text
encrypted: bool
```

và key-provider boundary.

---

# 597.127. Secret Storage

Passwords/tokens không nên lưu plain ApplicationData.

API:

```text
SecureStorage
```

sẽ kết nối OS credential/keychain/keystore.

---

# 597.128. SecureStorage Boundary

```text
Application
   ↓
SecureStorage API
   ↓
OS Keychain / Credential Manager / Keystore
```

Không ghi secret vào filesystem mặc định.

---

# 597.129. Permissions Metadata

Application có thể query:

```text
StoragePermissionState
├── Granted
├── Denied
├── Restricted
├── Unknown
└── NotApplicable
```

---

# 597.130. Sandboxing

Sandbox boundary:

```text
Application
   │
   ▼
StorageCapability
   │
   ▼
PlatformSandbox
   │
   ▼
PhysicalStorage
```

Storage API không được bypass sandbox.

---

# 597.131. External Path Escape

Native API có thể cung cấp explicit unsafe escape hatch:

```text
unsafe native_path(...)
```

nhưng:

- không có trong safe API;
- phải chịu security audit;
- platform có thể deny.

---

# 597.132. Portable Mode

Portable mode được xác định bởi deployment manifest:

```text
storage.mode = portable
```

Không dựa vào việc executable tình cờ nằm trong writable directory.

---

# 597.133. Portable Directory

```text
app/
├── executable
├── resources/
├── runtime/
└── data/
    ├── app/
    ├── cache/
    └── temp/
```

---

# 597.134. Portable Safety

Nếu application directory read-only:

```text
PortableStorageUnavailable
```

không fallback âm thầm sang user profile nếu policy yêu cầu portable strict.

---

# 597.135. Embedded Device Mode

Embedded targets có thể dùng:

```text
Flash
EEPROM
NVRAM
RAMFS
```

backend vẫn implement StorageBackend.

---

# 597.136. Wear-Aware Storage

Embedded backend có thể expose:

```text
write_cost
erase_cost
durability
```

để application lựa chọn cache/buffering.

---

# 597.137. Storage Policies

```text
StoragePolicy {
    durability
    backup
    encryption
    quota
    portability
    persistence
}
```

---

# 597.138. Policy Inheritance

```text
Application
    ↓
Scope
    ↓
Directory
    ↓
Operation
```

Policy cụ thể hơn override policy chung nếu không vi phạm security.

---

# 597.139. No Silent Downgrade

Nếu yêu cầu:

```text
durable
encrypted
atomic
persistent
```

không đạt được:

```text
ERROR
```

không silently fallback.

---

# 597.140. Cache May Downgrade

Cache có thể fallback vì cache disposable.

Ví dụ:

```text
persistent cache unavailable
→ memory cache
```

được phép nếu policy cho phép.

---

# 597.141. Storage Events

Storage subsystem phát event:

```text
StorageMounted
StorageUnmounted
QuotaChanged
PermissionChanged
ExternalChange
MigrationRequired
MigrationCompleted
StorageCorruptionDetected
```

---

# 597.142. Application Lifecycle Integration

Theo `468/594`:

```text
ApplicationStart
 ↓
StorageInitialize
 ↓
Migration
 ↓
ApplicationReady
```

Shutdown:

```text
ApplicationStopping
 ↓
flush required state
 ↓
sync according policy
 ↓
StorageRelease
 ↓
ApplicationStopped
```

---

# 597.143. Crash Integration

`589` crash system phải ghi crash artifacts vào:

```text
CrashData
```

hoặc ApplicationData tùy platform.

Crash handling không được phụ thuộc vào application database đang hoạt động.

---

# 597.144. Logging Integration

Storage operations có structured trace:

```text
storage.open
storage.read
storage.write
storage.atomic_replace
storage.migration
storage.quota
storage.watch
```

---

# 597.145. Metrics

Các metric chuẩn:

```text
storage_read_bytes
storage_write_bytes
storage_read_latency
storage_write_latency
storage_sync_latency
storage_cache_hit
storage_cache_miss
storage_quota_failures
storage_migration_duration
```

---

# 597.146. Privacy

Path logging phải tránh leak sensitive user data.

Default:

```text
logical scope + hashed identity
```

thay vì physical absolute path.

---

# 597.147. AI Observability

Semantic metadata:

```text
StorageSnapshot {
    scopes
    capabilities
    quotas
    migrations
    active_watches
    pending_operations
}
```

AI tooling có thể query nhưng không tự ý mutate.

---

# 597.148. AI Storage Action

AI action phải có:

```text
Plan
→ Preview
→ Permission
→ Execute
→ Verify
```

Đặc biệt với:

```text
delete
overwrite
restore
migration
```

---

# 597.149. AI Destructive Operation

AI không được tự động:

```text
delete user data
clear documents
overwrite database
reset application state
```

trừ khi caller đã cấp explicit permission.

---

# 597.150. IDE Integration

IDE sử dụng Storage Manager cho:

```text
workspace state
index cache
build cache
session state
local project metadata
```

Nhưng build cache chính vẫn tuân theo `487/568`.

---

# 597.151. Package Integration

Package manager `591` có thể dùng:

```text
Cache
ApplicationData
Temporary
```

để lưu:

```text
package index
download staging
package cache
verification metadata
```

---

# 597.152. Deployment Integration

`593` application package chỉ chứa immutable package data.

Sau installation:

```text
AXPK
 ↓
Application Bundle
 ↓
Storage Manager creates writable scopes
```

---

# 597.153. Runtime Integration

`594` process supervisor không được giả định physical storage path.

Nó chỉ nhận:

```text
StorageIdentity
CrashDirectory
LogDirectory
```

---

# 597.154. File Descriptor Boundary

Low-level API có thể expose native descriptor:

```text
unsafe_native_handle()
```

nhưng ownership phải explicit.

---

# 597.155. Native Handle Ownership

```text
Borrowed
Owned
Duplicated
```

Không được close borrowed handle.

---

# 597.156. File Descriptor Duplication

Nếu native interop yêu cầu:

```text
duplicate_native_handle()
```

trả về owned handle.

---

# 597.157. ABI

Storage API ABI-stable boundary phải sử dụng opaque handles.

```text
AxiomStorageHandle*
```

Không expose Rust/C++-like internal structs.

---

# 597.158. FFI

C ABI facade:

```text
axiom_storage_open(...)
axiom_storage_read(...)
axiom_storage_write(...)
axiom_storage_close(...)
```

Error trả bằng stable numeric enum.

---

# 597.159. Thread Safety

Storage handles mặc định:

```text
Send = implementation-defined
Share = false
```

trừ khi backend chứng minh thread safety.

---

# 597.160. Concurrent Reads

Read-only handles nên hỗ trợ concurrent access.

---

# 597.161. Concurrent Writes

Không đảm bảo nếu không có:

```text
lock
CAS
atomic replace
database transaction
```

---

# 597.162. Async + Thread Interaction

Async storage operation không được block executor thread lâu hơn policy cho phép.

Backend có thể delegate blocking filesystem operation sang IO worker.

---

# 597.163. Backpressure

Streaming write/read phải hỗ trợ bounded buffers:

```text
producer
   ↓
bounded queue
   ↓
storage
```

---

# 597.164. Large File Safety

API không được tự động allocate:

```text
file_size bytes
```

cho file lớn.

`read_all()` có thể fail:

```text
AllocationLimit
```

---

# 597.165. Storage Limits

Runtime có configurable limits:

```text
max_file_size
max_path_length
max_directory_entries
max_read_all
max_open_handles
max_watchers
```

---

# 597.166. Resource Exhaustion

Exhaustion phải trả lỗi rõ ràng.

Không được process abort chỉ vì storage quota hết.

---

# 597.167. Directory Enumeration

Iterator phải streaming:

```text
for entry in storage.list(path):
    ...
```

Không bắt buộc load toàn bộ directory.

---

# 597.168. Stable Enumeration

Filesystem enumeration không đảm bảo thứ tự.

API có:

```text
sort = none | name | metadata
```

Nếu deterministic build cần thứ tự:

```text
sort=name
```

phải explicit.

---

# 597.169. Case Sensitivity

Storage metadata expose:

```text
case_sensitive
unicode_normalization
```

để ứng dụng xử lý cross-platform.

---

# 597.170. Unicode Filename

Logical filenames UTF-8.

Backend chịu trách nhiệm mapping Unicode filesystem semantics.

---

# 597.171. Filename Normalization

Axiom không tự động normalize Unicode filename nếu điều đó làm thay đổi identity.

Identity phải lưu canonical logical representation.

---

# 597.172. Reserved Names

Backend phải reject hoặc escape platform-reserved names.

---

# 597.173. Timestamp

Axiom sử dụng `474` time types.

Không expose raw platform timestamp trong high-level API.

---

# 597.174. Clock Semantics

```text
created_time
modified_time
access_time
```

là wall-clock timestamps.

Duration/timeout dùng monotonic clock.

---

# 597.175. Storage URI

Optional canonical URI:

```text
axstorage://application/data/settings.json
axstorage://cache/shader/a.bin
```

URI chỉ là logical identifier.

---

# 597.176. Provider Architecture

Storage backend có thể được cung cấp bởi:

```text
NativeFilesystem
WASMFilesystem
VirtualFilesystem
RemoteFilesystem
MemoryFilesystem
EncryptedFilesystem
```

---

# 597.177. Virtual Filesystem

Testing có:

```text
MemoryStorageBackend
```

không chạm disk.

---

# 597.178. Deterministic Tests

Memory backend phải mô phỏng:

```text
atomic replace
quota
locks
watch
crash recovery
```

ở mức có thể kiểm thử.

---

# 597.179. Fault Injection

Test backend hỗ trợ:

```text
fail_read
fail_write
fail_flush
fail_sync
fail_rename
fail_quota
fail_lock
crash_after_stage
crash_before_commit
```

---

# 597.180. Crash Simulation

Atomic write test:

```text
stage
→ injected crash
→ reopen
→ verify old/new validity
```

---

# 597.181. Migration Test

Mọi migration phải test:

```text
old valid data
partial migration
crash
resume
rollback
invalid input
```

---

# 597.182. Quota Test

Phải test:

```text
exact capacity
capacity - 1
capacity + 1
reservation race
concurrent writers
```

---

# 597.183. Watch Test

Phải test:

```text
create
modify
delete
rename
burst
overflow
rescan
```

---

# 597.184. Security Test

Phải test:

```text
../escape
symlink escape
absolute path
reserved name
permission denial
sandbox denial
malicious filename
unicode confusion
```

---

# 597.185. Conformance Matrix

```text
                     Windows Linux macOS iOS Android WASM
ApplicationData        ✓      ✓      ✓     ✓     ✓      ✓
Cache                  ✓      ✓      ✓     ✓     ✓      ✓
Temp                   ✓      ✓      ✓     ✓     ✓      ✓
Documents              ✓      ✓      ✓     ✓     ✓      ✓
Atomic write           ✓      ✓      ✓     ✓     ✓      ✓*
Watch                  ✓      ✓      ✓     ✓     ✓      ~
Mmap                   ✓      ✓      ✓     ✓     ~      ~
Persistent             ✓      ✓      ✓     ✓     ✓      ~
```

`~` = environment-dependent.

---

# 597.186. Feature Detection

Application có thể query:

```text
storage.capabilities()
```

thay vì target-specific compile-time assumptions.

---

# 597.187. Compile-Time Capability

Platform-specific code có thể sử dụng:

```text
target.has(StorageFeature::Mmap)
```

ở comptime.

---

# 597.188. Runtime Capability

Runtime query dùng khi capability phụ thuộc environment.

---

# 597.189. No Platform Path Leakage

Compiler/static analyzer nên cảnh báo:

```text
hard-coded platform path
```

trong portable application.

---

# 597.190. Storage Lint Rules

Các warning chuẩn:

```text
ST001 direct platform storage path
ST002 cache used as persistent storage
ST003 non-atomic configuration write
ST004 ignored sync failure
ST005 unsafe path construction
ST006 read_all on potentially large file
ST007 missing migration
ST008 destructive operation without capability
ST009 unverified external document
ST010 insecure secret storage
```

---

# 597.191. API Ergonomics

Common operation phải ngắn:

```text
let data = app.storage.read("settings.json")?
app.storage.write("settings.json", data)?
```

nhưng semantics vẫn đi qua Storage Manager.

---

# 597.192. Scoped Storage

Convenience API:

```text
app.data()
app.cache()
app.temp()
app.documents()
```

tạo typed `StorageRoot`.

---

# 597.193. Typed Root

```text
let data: StorageRoot<ApplicationData>
let cache: StorageRoot<Cache>
```

Giúp compiler ngăn nhầm scope.

---

# 597.194. Scope-Specific API

Cache có thể cung cấp:

```text
evict()
set_ttl()
```

Documents có:

```text
pick()
export()
import()
```

ApplicationData không có các API không phù hợp.

---

# 597.195. Compile-Time Scope Safety

Không cho:

```text
CachePath → ApplicationDataPath
```

nếu API yêu cầu type khác.

---

# 597.196. Storage Object Model

```text
StorageManager
 └── StorageRoot
      ├── File
      ├── Directory
      ├── Watcher
      ├── Lock
      ├── Mapping
      └── Transaction/Staging
```

---

# 597.197. Lifecycle

```text
Created
  ↓
Opened
  ↓
Active
  ├── Read
  ├── Write
  ├── Map
  ├── Watch
  └── Lock
  ↓
Flushed
  ↓
Closed
```

---

# 597.198. Invalid State

Sau `close`:

```text
read → InvalidHandle
write → InvalidHandle
map → InvalidHandle
```

---

# 597.199. Ownership

Storage handles áp dụng:

```text
move
drop
defer
```

theo `423`.

Không cần GC.

---

# 597.200. Reference Complexity

High-level API không yêu cầu application quản lý raw pointers.

```text
FileHandle
StorageRoot
MappedRegion
DocumentHandle
```

đều là value-like opaque handles với ownership rõ ràng.

---

# 597.201. Resource Lifetime

```text
StorageRoot
    │
    ├── FileHandle
    │      └── MappedRegion
    │
    └── Watcher
```

Parent scope phải sống đủ lâu cho child resources.

---

# 597.202. Shutdown Flush

Runtime không được tự động flush mọi handle một cách không xác định.

Application/runtime policy quyết định:

```text
best-effort shutdown
graceful shutdown
forced termination
```

---

# 597.203. Forced Termination

Không đảm bảo dữ liệu chưa sync được persist.

Documentation phải nói rõ điều này.

---

# 597.204. Data Loss Boundary

Axiom phân biệt:

```text
write success
flush success
sync success
backup success
```

Không coi `write()` là guarantee backup.

---

# 597.205. Application State Pattern

Recommended:

```text
memory state
   ↓
serialize
   ↓
validate
   ↓
atomic_write
   ↓
sync according policy
```

---

# 597.206. Large Application State

State lớn nên dùng:

```text
database
append-only log
chunked files
```

thay vì một JSON file khổng lồ.

---

# 597.207. Serialization Boundary

`597` không định nghĩa serializer.

Serializer thuộc standard/data subsystem.

Storage chỉ nhận:

```text
Bytes
Reader
Writer
```

---

# 597.208. Generated Data

Compiler/tool/application generated output có thể nằm:

```text
ApplicationData
Cache
Temporary
```

tùy lifecycle.

---

# 597.209. Build Artifacts

Build artifacts không thuộc user documents mặc định.

Build cache → `Cache`.

Persistent build state → `ApplicationData`.

---

# 597.210. AI Model Cache

AI runtime có thể dùng:

```text
Cache
```

cho model artifacts có source-of-truth bên ngoài.

Model người dùng sở hữu → `UserData`.

---

# 597.211. Offline Behavior

Offline application phải tiếp tục hoạt động nếu data cần thiết đã local.

Không được storage API tự động network.

Remote storage là provider riêng.

---

# 597.212. Remote Storage

Có thể implement:

```text
RemoteStorageBackend
```

nhưng semantics phải phân biệt:

```text
local
remote
cached
```

---

# 597.213. Consistency

Remote provider phải khai báo:

```text
Strong
Eventual
Unknown
```

Storage Manager không giả định strong consistency.

---

# 597.214. Storage Transactions vs Network

Network failure:

```text
timeout
partial commit
unknown outcome
```

không được map thành local atomic semantics.

---

# 597.215. Audit Trail

Security-sensitive storage operations có thể tạo:

```text
StorageAuditEvent {
    operation
    identity
    actor
    result
    timestamp
}
```

---

# 597.216. Audit Privacy

Audit không được mặc định lưu raw sensitive data.

---

# 597.217. Application Uninstall

Deployment lifecycle:

```text
Uninstall
 ├── Bundle
 ├── ApplicationData
 ├── Cache
 └── Temporary
```

Documents phải có policy riêng vì thuộc user.

---

# 597.218. Uninstall Policy

Manifest khai báo:

```text
remove_application_data
preserve_user_documents
preserve_user_data
```

Không được xóa Documents mặc định nếu user-owned.

---

# 597.219. Reset Application

Reset:

```text
clear ApplicationData
clear Cache
clear Temp
```

không mặc định xóa Documents.

---

# 597.220. Factory Reset

Factory reset phải explicit và có confirmation layer ở application/platform.

---

# 597.221. Storage Migration Across Platform

Không giả định physical paths portable.

Portable data:

```text
logical data
+
schema version
+
metadata
```

được migrate.

---

# 597.222. Export/Import

Application có thể:

```text
export_user_data()
import_user_data()
```

Storage subsystem cung cấp primitives, application định nghĩa format.

---

# 597.223. Data Package

Export package có thể sử dụng `AXPK` hoặc data-specific format.

Không bắt buộc.

---

# 597.224. Provenance

Storage-generated artifact metadata có thể liên kết:

```text
SourceRevision
→ DataSchema
→ Migration
→ ContentID
```

---

# 597.225. AI Semantic Metadata

AI query:

```text
storage.describe(scope)
storage.describe(path)
storage.explain_error(error)
storage.plan_migration(...)
```

AI chỉ nhận factual metadata.

---

# 597.226. No Hidden Mutation

Query API:

```text
describe
inspect
stat
```

không được mutate storage.

---

# 597.227. Storage Plan

AI/IDE plan:

```text
StoragePlan {
    operations[]
    affected_paths[]
    estimated_bytes
    destructive
    permissions_required
}
```

---

# 597.228. Plan Verification

Trước destructive operation:

```text
Plan
→ Validate
→ Permission
→ Execute
→ Verify
```

---

# 597.229. Compiler Metadata

Compiler có thể annotate storage usage:

```text
@storage_scope(ApplicationData)
@requires(StorageWrite)
```

để static analysis.

---

# 597.230. Capability Inference

Compiler có thể phát hiện:

```text
function save_config()
    requires ApplicationData.Write
```

và truyền requirement qua call graph.

---

# 597.231. Effect Integration

Theo `573`:

```text
storage.read    → IO
storage.write   → IO + Mutation
storage.sync    → IO + DurableIO
storage.watch   → IO + EventSubscription
```

---

# 597.232. Security Analysis

Theo `572/574`:

```text
UserInput
 ↓
PathConstruction
 ↓
StorageOpen
```

phải được flow analysis để phát hiện path injection.

---

# 597.233. Contract

Storage APIs có preconditions:

```text
path valid
capability granted
handle valid
```

Postconditions:

```text
bytes written
identity updated
atomicity guarantee
```

---

# 597.234. Formal Atomic Write Contract

```text
pre:
    capability.write
    valid(path)

post success:
    content(path) == requested_content

post failure:
    content(path) == old_content
    OR
    content(path) == new_content only if commit occurred
```

Không được partial state.

---

# 597.235. Cache Contract

```text
cache_hit(data) => data is valid
cache_miss       => application can regenerate data
eviction         => application remains correct
```

---

# 597.236. Temp Contract

```text
Temp may disappear at any time.
```

Ứng dụng phải coi Temp là disposable.

---

# 597.237. Documents Contract

Documents là user-owned unless explicitly declared application-private.

---

# 597.238. ApplicationData Contract

ApplicationData phải:

```text
persistent according to platform
private by default
not user-document storage
```

---

# 597.239. Database Contract

Database engine quyết định transactional semantics.

Storage Manager chỉ quyết định:

```text
where
lifetime
quota
backup
access capability
```

---

# 597.240. Performance

Common local read path mục tiêu:

```text
logical path resolution
→ backend open
→ buffered/direct read
```

không tạo heap allocation không cần thiết.

---

# 597.241. Small File Optimization

Backend có thể inline/cache small files.

Không thay đổi observable semantics.

---

# 597.242. Large File Optimization

Backend nên hỗ trợ:

```text
direct I/O
mmap
streaming
read-ahead
async IO
```

khi platform cho phép.

---

# 597.243. Zero-Copy Pipeline

```text
File
 ↓
MappedRegion
 ↓
Parser
 ↓
Application
```

hoặc:

```text
File
 ↓
DMA/OS buffer
 ↓
Consumer
```

khi backend hỗ trợ.

---

# 597.244. Cache Deduplication

Content-addressed cache có thể deduplicate:

```text
same ContentID
→ same physical cache object
```

---

# 597.245. Concurrent Load

Nếu nhiều callers request cùng cache key:

```text
request A ─┐
request B ─┼→ single load
request C ─┘
              ↓
           publish
```

---

# 597.246. Cache Corruption

Nếu checksum mismatch:

```text
delete invalid cache
rebuild
```

không propagate corruption thành user-data error.

---

# 597.247. Application Data Corruption

Ngược lại, ApplicationData corruption phải báo explicit.

Không silently reset user data.

---

# 597.248. Recovery Strategy

```text
detect
→ preserve original
→ create recovery copy
→ attempt repair/migration
→ verify
```

---

# 597.249. Recovery Copy

Recovery copy phải nằm trong scope phù hợp và không được nhầm với backup chính thức.

---

# 597.250. Final Storage Architecture

```text
                         Axiom Application
                                │
                         Storage Manager
                                │
       ┌───────────────┬────────┼───────────┬──────────────┐
       │               │        │           │              │
       ▼               ▼        ▼           ▼              ▼
 ApplicationData     Cache    Temp      Documents      Database
       │               │        │           │              │
       └───────────────┴────────┴───────────┴──────────────┘
                                │
                         Storage Backend
                                │
       ┌──────────────┬────────┼─────────────┬────────────┐
       ▼              ▼        ▼             ▼            ▼
    Windows         Linux    Apple        Android        WASM
       │              │        │             │            │
       └──────────────┴────────┴─────────────┴────────────┘
                                │
                         Physical Storage
```

---

# 597.251. Integration Map

```text
423  Ownership
 │
597 Storage
 ├── 455 Database
 ├── 459/460 Media/Graphics assets
 ├── 464 Text/Unicode
 ├── 468 Application lifecycle
 ├── 474 Time
 ├── 475 Observability
 ├── 487 Build cache
 ├── 489 Deployment
 ├── 490 Security
 ├── 589 Debug/Crash
 ├── 590 IDE
 ├── 591 Package system
 ├── 593 Application bundle
 ├── 594 Process supervision
 └── 596 Resource runtime
```

---

# 597.252. Required Standard Types

Core API phải định nghĩa hoặc import chuẩn:

```text
StorageScope
StorageRoot
StorageIdentity
StorageCapabilities
StoragePermission
StorageQuota
StorageStats
StoragePolicy

Path
FileIdentity
FileMetadata
FileHandle
FileMode
FileLock
FileWatcher
FileEvent
MappedRegion
DocumentHandle

StorageError
Recoverability
Durability
BackupClass
```

---

# 597.253. Required Backend Interfaces

```text
StorageBackend
FileBackend
WatchBackend
LockBackend
QuotaBackend
PersistenceBackend
DocumentProvider
```

Có thể được hợp nhất implementation nhưng semantic interfaces phải tách biệt.

---

# 597.254. Required Test Suites

Compiler/runtime distribution phải có:

```text
storage-unit
storage-conformance
storage-security
storage-crash
storage-migration
storage-quota
storage-concurrency
storage-watch
storage-wasm
storage-platform
storage-performance
```

---

# 597.255. Cross-Platform Golden Tests

Một test case phải có cùng logical behavior:

```text
write("state.json")
read("state.json")
```

trên tất cả targets.

Expected semantic result giống nhau dù physical path khác.

---

# 597.256. Reproducibility

Storage test fixtures phải deterministic.

Không dùng physical machine-specific path làm golden output.

---

# 597.257. Performance Regression

Benchmark tối thiểu:

```text
small read
small write
large sequential read
large sequential write
random read
atomic replace
directory enumeration
mmap
watch throughput
concurrent access
cache hit
cache miss
```

---

# 597.258. Security Invariants

Bắt buộc:

```text
No path traversal
No sandbox escape through safe API
No secret leakage by default
No arbitrary executable loading
No silent permission escalation
No destructive AI mutation without capability
```

---

# 597.259. Application Safety Invariants

```text
Cache loss never corrupts application truth.
Temp loss never corrupts application truth.
Atomic configuration update never exposes partial file.
Migration never destroys original before verification.
Restore never activates unverified data.
```

---

# 597.260. FINAL HARD INVARIANT

`BOOTSTRAP-597` chỉ được coi là đúng khi toàn bộ hệ thống thỏa mãn:

```text
1. Immutable resources và mutable user data bị tách biệt.
2. Application không phụ thuộc physical OS paths.
3. Mọi storage scope có semantics rõ ràng.
4. ApplicationData không bị coi là Cache.
5. Cache có thể mất mà không làm mất source-of-truth.
6. Temporary data có thể mất bất kỳ lúc nào.
7. Documents được bảo vệ như user-owned data.
8. Sandbox boundary không thể bị bypass qua safe Storage API.
9. Path traversal và symlink escape được ngăn chặn.
10. Atomic file replacement không để lộ partial state.
11. Durability semantics được khai báo rõ.
12. Không silent downgrade đối với atomic/durable/persistent guarantees.
13. File locking và concurrent access có semantics xác định.
14. Large files có streaming và mmap/zero-copy khi khả dụng.
15. Storage không ép mọi dữ liệu vào database.
16. Database semantics vẫn thuộc BOOTSTRAP-455.
17. Migration có version, journal, validation và rollback/recovery.
18. Backup/restore không nhầm với cache.
19. Quota exhaustion là recoverable error.
20. File watcher không được coi là source-of-truth.
21. WASM persistence được capability-detect.
22. Platform-specific paths bị cô lập trong backend.
23. Portable mode là explicit và deterministic.
24. Native handle escape hatch không phá ownership.
25. Storage handles tuân theo BOOTSTRAP-423.
26. Storage effects tích hợp với BOOTSTRAP-573.
27. Static analysis phát hiện các pattern storage nguy hiểm.
28. AI chỉ được inspect/plan/execute storage theo capability và permission.
29. AI không được tự ý xóa hoặc overwrite user data.
30. IDE, debugger, deployment, package và runtime dùng cùng một storage semantic model.
31. Storage operations có provenance và observability.
32. Physical storage implementation có thể thay đổi mà không thay đổi application semantics.
33. Compiler/runtime không phụ thuộc third-party filesystem abstraction.
34. Backend có thể tối ưu zero-copy, mmap, async IO mà không thay đổi semantics.
35. Toàn bộ storage subsystem có deterministic conformance và crash-recovery tests.
36. Không có hidden global mutable storage state.
37. Mọi writable application data đều thuộc một storage scope xác định.
38. Không có đường tắt từ resource runtime của `596` sang writable user data.
39. Không có đường tắt từ writable user data sang executable code.
40. **Logical storage identity là nguồn sự thật; physical path chỉ là implementation detail.**
```

# 597 — LOCKED

---

# NEXT — BOOTSTRAP-598

## BOOTSTRAP-598 — NATIVE APPLICATION DATA MIGRATION, UPDATE & COMPATIBILITY RUNTIME 5.0

**Mục tiêu:** sau khi `597` chuẩn hóa writable storage, bước tiếp theo là chuẩn hóa **vòng đời dữ liệu qua các phiên bản ứng dụng**: update executable, schema evolution, rollback, downgrade, compatibility window, migration orchestration và dữ liệu giữa các phiên bản.

```text
                 Installed Application vN
                          │
                          ▼
                    Update Manager
                          │
              ┌───────────┼───────────┐
              ▼           ▼           ▼
          App Binary   Runtime     Data Schema
              │           │           │
              └───────────┼───────────┘
                          ▼
                  Compatibility Check
                          │
                ┌─────────┴─────────┐
                ▼                   ▼
          No Migration          Migration
                │                   │
                │             Stage → Verify
                │                   │
                │             Commit → Activate
                │                   │
                └─────────┬─────────┘
                          ▼
                    Running App
                          │
                   ┌──────┴──────┐
                   ▼             ▼
                Rollback      Recovery
```

598 sẽ đặc biệt xử lý:

- application update transaction;
- data schema compatibility;
- forward/backward compatibility;
- migration graph;
- online/offline migration;
- preflight validation;
- update staging;
- binary/data atomic activation;
- rollback;
- downgrade protection;
- interrupted update recovery;
- multi-component application updates;
- native library compatibility;
- runtime version compatibility;
- package/deployment integration với `591/593`;
- process supervision integration với `594`;
- storage/migration integration với `597`;
- crash recovery;
- update provenance;
- signed update metadata;
- reproducible update artifacts;
- AI-readable update plans;
- zero-data-loss policy;
- enterprise/offline update;
- portable application update;
- WASM application version transitions.

**Nguyên tắc trung tâm của 598:**

```text
New Binary
    +
New Runtime
    +
New Data Schema
    +
New Dependencies
    │
    ▼
Compatibility Proof
    │
    ▼
Atomic Activation
```

Không được phép xảy ra trạng thái:

```text
binary mới + data schema không tương thích
```

mà không có explicit recovery state.