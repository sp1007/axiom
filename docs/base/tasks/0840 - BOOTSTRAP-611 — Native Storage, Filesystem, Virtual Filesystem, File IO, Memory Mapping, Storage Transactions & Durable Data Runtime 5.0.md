Tiếp tục chuỗi kiến trúc Axiom với **BOOTSTRAP-611**. Đây là lớp native storage còn thiếu, nối trực tiếp filesystem với state, security, scheduler, resource governor và durability.

:::writing{variant="document" id="58317" title="BOOTSTRAP-611 — Native Storage, Filesystem, Virtual Filesystem, File I/O, Memory Mapping, Storage Transactions & Durable Data Runtime 5.0"}
# BOOTSTRAP-611 — Native Storage, Filesystem, Virtual Filesystem, File I/O, Memory Mapping, Storage Transactions & Durable Data Runtime 5.0

**Status:** Architecture Specification — Implementable  
**Layer:** Native Runtime / Storage  
**Depends on:** BOOTSTRAP-600..610  
**Primary dependencies:** 603 Security, 606 Resource Governor, 607 Scheduler, 608 Synchronization, 609 Networking, 610 Cryptography  
**Primary consumers:** Application State, Configuration, Logging, IPC, Services, Cache, Serialization, Database layers

---

# 1. Purpose

BOOTSTRAP-611 defines Axiom's native storage subsystem.

It provides a single platform-independent storage API while allowing each target operating system to use its native filesystem and I/O facilities.

The subsystem covers:

- files
- directories
- paths
- file handles
- metadata
- synchronous I/O
- asynchronous I/O
- buffered I/O
- direct I/O
- scatter/gather I/O
- memory-mapped files
- sparse files
- file locking
- atomic rename/replace
- durable writes
- filesystem watchers
- virtual filesystems
- sandboxed paths
- transactional file operations
- crash-safe persistence primitives
- temporary files
- storage quotas
- storage resource accounting
- storage encryption layers
- package/resource filesystems
- in-memory filesystems

The subsystem must remain usable without requiring a database engine.

---

# 2. Design Principles

Axiom storage follows these principles:

1. Native filesystem performance.
2. No mandatory third-party storage library.
3. UTF-8 application-facing paths.
4. Capability-controlled filesystem access.
5. Explicit durability.
6. Explicit buffering.
7. Explicit transaction semantics.
8. Async I/O integrated with BOOTSTRAP-607.
9. Synchronization integrated with BOOTSTRAP-608.
10. Resource accounting integrated with BOOTSTRAP-606.
11. Security integrated with BOOTSTRAP-603.
12. Crash diagnostics integrated with BOOTSTRAP-602.
13. Application state integrated with BOOTSTRAP-600.
14. Configuration integrated with BOOTSTRAP-601.
15. Cryptographic storage layers integrated with BOOTSTRAP-610.
16. No hidden global filesystem lock.
17. No mandatory garbage collector.
18. No mandatory memory-mapped I/O.
19. No implicit durability guarantee.
20. No assumption that every filesystem provides transactions.

---

# 3. Non-Goals

BOOTSTRAP-611 does not define:

- SQL
- relational databases
- query languages
- object databases
- distributed filesystems
- cloud object storage
- network filesystems
- full content-addressed databases
- application-specific serialization formats

Those belong to higher layers.

---

# 4. Architecture

```text
Application
    │
    ├── State / Config / Cache
    │
    ▼
Storage API
    │
    ├── Path API
    ├── File API
    ├── Directory API
    ├── Mapping API
    ├── Watch API
    ├── Transaction API
    └── VFS API
    │
    ▼
Storage Policy
    │
    ├── Security / Capability
    ├── Resource Governor
    ├── Scheduler
    └── Diagnostics
    │
    ▼
VFS
    │
    ├── NativeFS
    ├── MemoryFS
    ├── PackageFS
    ├── OverlayFS
    ├── ArchiveFS
    └── TransformFS
    │
    ▼
Platform Backend
    │
    ├── Windows
    ├── Linux
    ├── macOS
    ├── Android
    ├── iOS
    ├── WASM
    └── Embedded
```

---

# 5. Fundamental Storage Types

```axiom
struct Path
struct File
struct Directory
struct FileInfo
struct VolumeInfo
struct FileId
struct VolumeId
struct FileOffset
struct FileSize
struct FileMode
struct FilePermissions
struct FileTime
struct FileMapping
struct FileLock
struct FileWatcher
struct StorageTransaction
struct StorageCapability
```

Handles are opaque runtime values.

Application code cannot construct arbitrary valid native file handles.

---

# 6. Path Model

Axiom exposes paths as UTF-8.

```axiom
Path("documents/report.txt")
```

The API distinguishes:

```text
Path
LogicalPath
NativePath
```

A `Path` is not automatically interpreted as an OS path.

Resolution occurs through a filesystem context.

---

# 7. Logical Paths

Logical paths use `/`.

Examples:

```text
app/config/settings.ax
app/data/cache.bin
assets/models/model.bin
```

A logical path must not directly expose:

- Windows drive parsing
- NT device paths
- Unix device paths
- platform-specific separators

The native backend performs translation.

---

# 8. Path Normalization

Normalization must:

- convert repeated separators
- remove `.` segments
- resolve `..` only when policy permits
- reject malformed paths
- preserve UTF-8
- prevent escaping configured roots

Example:

```text
sandbox/data/../config
```

becomes:

```text
sandbox/config
```

but:

```text
sandbox/../../private
```

must fail when sandbox policy forbids escape.

---

# 9. Path Security

Path validation must occur before filesystem access.

Security-sensitive resolution must not use:

```text
check(path)
open(path)
```

because this is vulnerable to TOCTOU races.

Instead:

```text
open_root()
resolve_component()
open_component()
...
```

or equivalent native secure APIs must be used.

---

# 10. File Capabilities

A file operation requires appropriate capability.

```axiom
Capability<FilesystemRead>
Capability<FilesystemWrite>
Capability<FilesystemCreate>
Capability<FilesystemDelete>
Capability<FilesystemExecute>
Capability<FilesystemMap>
Capability<FilesystemWatch>
```

Capabilities can be attenuated:

```axiom
let read = fs_cap.read_only();
let project = read.restrict("/project");
```

A child operation must never obtain more authority than its parent.

---

# 11. File Rights

A file handle contains rights.

```axiom
FileRights {
    read
    write
    append
    seek
    stat
    resize
    map
    lock
    delete
}
```

Rights are immutable after handle creation.

---

# 12. File Opening

Example:

```axiom
let file = fs.open(
    "data.bin",
    OpenMode.ReadWrite
)?;
```

Supported modes:

```text
Read
Write
ReadWrite
Append
Create
CreateNew
Truncate
OpenExisting
```

Modes may be combined.

Example:

```axiom
OpenMode.ReadWrite | OpenMode.Create
```

---

# 13. Exclusive Creation

```axiom
fs.open(
    "state.lock",
    OpenMode.CreateNew
)
```

must atomically fail if the path already exists.

This is required for safe lock-file patterns.

---

# 14. File Lifetime

A file handle remains valid until:

- explicit close
- ownership destruction
- process termination
- native backend invalidation

The language runtime must not depend on GC finalizers for correctness.

Preferred:

```axiom
using file = fs.open(...)?;
```

or deterministic scope ownership.

---

# 15. File Ownership

A file handle has one clear owner by default.

Explicit duplication:

```axiom
let duplicate = file.duplicate()?;
```

is required when ownership is shared.

This avoids implicit reference-counting overhead.

---

# 16. Read API

```axiom
file.read(buffer)?;
```

returns:

```axiom
ReadResult {
    bytes_read: usize
    eof: bool
}
```

A short read is valid.

The API must not assume:

```text
requested == returned
```

---

# 17. Write API

```axiom
file.write(buffer)?;
```

returns the number of bytes accepted.

Partial writes are valid.

Higher layers must handle:

```text
bytes_written < bytes_requested
```

---

# 18. Exact I/O

Convenience operations:

```axiom
file.read_exact(buffer)?;
file.write_all(buffer)?;
```

must loop internally.

They must still honor:

- cancellation
- deadlines
- quota limits
- device errors

---

# 19. Positioned I/O

Axiom supports:

```axiom
file.read_at(offset, buffer)?;
file.write_at(offset, buffer)?;
```

These operations do not modify the shared file cursor.

This is important for concurrent I/O.

---

# 20. File Cursor

Sequential APIs maintain a cursor:

```axiom
file.seek(SeekOrigin.Start, 0)?;
file.seek(SeekOrigin.Current, 128)?;
file.seek(SeekOrigin.End, -32)?;
```

Positioned I/O should be preferred for concurrent access.

---

# 21. Append Semantics

Append mode must request native atomic append semantics when available.

Multiple writers must not produce overlapping writes.

Axiom does not guarantee application-level record atomicity unless explicitly specified by the backend.

---

# 22. Scatter/Gather

```axiom
file.readv(buffers)?;
file.writev(buffers)?;
```

maps to:

- `readv/writev`
- `preadv/pwritev`
- Windows equivalent
- native backend implementation

The API avoids unnecessary buffer concatenation.

---

# 23. Buffered I/O

Axiom provides explicit buffering:

```axiom
BufferedFile(file, 64 * KiB)
```

Buffering is not automatically inserted into every file.

This keeps performance predictable.

---

# 24. Direct I/O

Optional:

```axiom
OpenFlags.Direct
```

Direct I/O is used only when supported.

Requirements:

- alignment
- block-size constraints
- buffer constraints

must be exposed through `FileInfo` or backend capabilities.

---

# 25. I/O Hints

Applications may specify:

```axiom
file.hint(AccessPattern.Sequential)
file.hint(AccessPattern.Random)
file.hint(AccessPattern.WillNeed)
file.hint(AccessPattern.DontNeed)
```

Hints are advisory.

Failure to support a hint must not fail the operation.

---

# 26. Async File I/O

Async API:

```axiom
let result = await file.read_async(buffer);
```

must integrate directly with BOOTSTRAP-607.

It must not implement async by blindly creating one OS thread per operation.

---

# 27. Windows Backend

Preferred mechanisms:

- overlapped I/O
- IOCP
- native file handles

Completion events map into the Axiom I/O reactor.

Where Windows filesystem limitations prevent true asynchronous completion, the backend may use controlled blocking workers.

---

# 28. Linux Backend

Preferred order:

1. `io_uring`
2. `pread/pwrite`
3. `read/write`
4. controlled blocking pool

Integration with BOOTSTRAP-607 determines completion delivery.

---

# 29. macOS Backend

Use:

- native file descriptors
- `pread/pwrite`
- `kqueue` where useful
- native asynchronous mechanisms where available

Regular file readiness notification must not be confused with completion-based asynchronous I/O.

---

# 30. Android

Filesystem access is constrained by application sandbox and platform permissions.

The backend maps:

```text
AppData
Cache
Files
SharedStorage
ExternalStorage
```

to platform-specific locations.

The runtime must not assume arbitrary filesystem access.

---

# 31. iOS

The backend maps logical storage classes to:

```text
Documents
Library
Caches
Temporary
Application Support
```

and respects platform lifecycle and backup policies.

---

# 32. WASM

WASM has no implicit host filesystem authority.

Filesystem access requires a host capability.

Possible backend:

```text
HostFS
VirtualFS
MemoryFS
PackageFS
```

No filesystem API should silently escape the WASM sandbox.

---

# 33. Embedded Targets

Embedded systems may expose:

```text
FlashFS
RAMFS
BlockFS
EEPROMFS
HostFS
```

The same storage interface remains available.

Durability guarantees must be reported by backend capabilities.

---

# 34. Directory API

```axiom
let dir = fs.open_dir("assets")?;

for entry in dir.entries()? {
    ...
}
```

Entries contain:

```axiom
DirectoryEntry {
    name
    kind
    file_id?
}
```

Metadata retrieval may be lazy.

---

# 35. Directory Entry Types

```text
File
Directory
Symlink
Socket
Device
Unknown
```

Unsupported types map to `Unknown`.

---

# 36. Directory Creation

```axiom
fs.create_dir("cache")?;
fs.create_dir_all("a/b/c")?;
```

Creation must be atomic at each native filesystem level.

---

# 37. Delete

```axiom
fs.remove_file(path)?;
fs.remove_dir(path)?;
```

Recursive deletion is explicit:

```axiom
fs.remove_tree(path)?;
```

The runtime must never recursively delete by default.

---

# 38. Rename

```axiom
fs.rename(old, new)?;
```

Same-filesystem rename should be atomic where supported.

Cross-filesystem rename must fail with:

```text
CrossDevice
```

rather than silently copying.

---

# 39. Atomic Replace

```axiom
fs.replace_atomic(temp, target)?;
```

This primitive is fundamental for durable configuration and state updates.

It should map to native atomic replacement operations.

---

# 40. Safe Write Pattern

Recommended:

```text
create temporary file
write complete contents
flush file
durability barrier
atomic replace
flush parent directory where required
```

This becomes the canonical Axiom durable-file update pattern.

---

# 41. Durability

Writing data does not automatically mean data survives power loss.

Axiom exposes:

```axiom
file.flush()
file.sync()
file.sync_data()
```

Semantics:

```text
flush      → push runtime buffers
sync_data  → request durable file data
sync       → request durable data + metadata
```

Exact guarantees depend on backend/filesystem.

---

# 42. Windows Durability

`sync()` maps to appropriate Windows flushing primitives such as:

```text
FlushFileBuffers
```

---

# 43. Unix Durability

Possible mappings:

```text
fsync
fdatasync
```

The backend selects the appropriate primitive.

---

# 44. Parent Directory Durability

For atomic rename durability on filesystems that require it:

```axiom
fs.sync_parent_dir(path)?;
```

This is an explicit operation.

---

# 45. Durability Levels

```axiom
Durability {
    None
    Runtime
    File
    Metadata
    Full
}
```

`Full` means the runtime requested the strongest supported native persistence sequence.

It must not claim a stronger guarantee than the underlying platform can provide.

---

# 46. Crash Consistency

Axiom defines crash consistency as a layered property:

```text
application protocol
        ↓
storage transaction
        ↓
filesystem atomicity
        ↓
filesystem durability
        ↓
hardware persistence
```

No layer may falsely claim guarantees supplied by a lower layer.

---

# 47. Storage Transactions

Axiom provides a lightweight transaction primitive.

```axiom
let tx = fs.transaction()?;

tx.write(...)
tx.replace(...)
tx.delete(...)

tx.commit()?;
```

The transaction is intended primarily for a set of related filesystem mutations.

---

# 48. Transaction Guarantees

Core transaction guarantees:

```text
Atomicity: supported where backend permits
Consistency: application-defined
Isolation: limited filesystem semantics
Durability: explicit
```

Axiom must not pretend arbitrary filesystems provide database-level ACID.

---

# 49. Transaction Implementation

Possible implementations:

```text
NativeFS atomic operations
Temporary files
Rename journals
Write-ahead journal
Manifest commit
Recovery log
```

The backend selects the minimal mechanism required.

---

# 50. Transaction Journal

A transaction journal may contain:

```text
transaction_id
operation
source
destination
expected_file_id
temporary_file
commit_marker
```

Journal records must never contain secrets unless explicitly encrypted.

---

# 51. Recovery

On startup:

```axiom
storage.recover()?;
```

Recovery examines incomplete transactions.

Possible states:

```text
Prepared
Committed
Aborted
Unknown
```

Unknown transactions require conservative recovery.

---

# 52. No Arbitrary Rollback

Axiom must not promise rollback of arbitrary external file changes.

Only operations registered with the transaction can participate.

---

# 53. Temporary Files

```axiom
let temp = fs.temp_file()?;
```

Requirements:

- unpredictable name
- exclusive creation
- correct permissions
- automatic cleanup on normal close
- no predictable path race

---

# 54. Temporary Directories

```axiom
let dir = fs.temp_dir()?;
```

The directory must be created atomically with restricted permissions.

---

# 55. File Locking

Axiom exposes:

```axiom
file.lock(LockMode.Shared)?;
file.lock(LockMode.Exclusive)?;
file.unlock()?;
```

Lock types:

```text
Shared
Exclusive
```

---

# 56. Lock Semantics

The API explicitly distinguishes:

```text
Advisory
Mandatory
```

Axiom defaults to advisory locking where supported.

Mandatory locking is not emulated unless the OS provides it safely.

---

# 57. Async Lock

```axiom
await file.lock_async(LockMode.Exclusive);
```

must not block an executor worker indefinitely.

---

# 58. File Metadata

```axiom
FileInfo {
    id
    type
    size
    allocated_size
    permissions
    owner
    created
    modified
    accessed
    links
    flags
}
```

Some fields are optional by platform.

---

# 59. File Identity

A file has:

```text
VolumeId
FileId
```

when the platform exposes stable identifiers.

Paths are not file identities.

This is important for detecting replacement races.

---

# 60. Timestamps

Axiom exposes:

```axiom
FileTime
```

with explicit clock semantics.

Filesystem timestamps must not be interpreted as monotonic time.

---

# 61. Permissions

Permissions are represented abstractly:

```text
Read
Write
Execute
Delete
Traverse
```

Platform-specific permissions are mapped into this model.

---

# 62. Symbolic Links

Symlinks require explicit policy.

```axiom
ResolveSymlink
NoSymlink
```

Security-sensitive operations default to no unexpected traversal.

---

# 63. Hard Links

Hard links are optional platform capabilities.

Creating a hard link requires:

```text
FilesystemCreate
FilesystemWrite
```

and must obey sandbox policy.

---

# 64. Windows Junctions / Reparse Points

Windows reparse points are treated as special path objects.

Security-sensitive resolution must inspect reparse behavior rather than blindly following it.

---

# 65. TOCTOU Protection

The secure API should prefer directory-handle-relative operations.

Conceptually:

```text
root_handle
    ↓
open child
    ↓
open child
```

rather than repeatedly constructing absolute paths.

---

# 66. Virtual Filesystem

The VFS is an abstraction over storage providers.

```axiom
trait FileSystem {
    open(...)
    create(...)
    remove(...)
    rename(...)
    stat(...)
    watch(...)
}
```

---

# 67. NativeFS

`NativeFS` exposes the host filesystem.

It is the primary desktop/server backend.

---

# 68. MemoryFS

`MemoryFS` stores files entirely in memory.

Uses:

- tests
- temporary state
- WASM
- embedded systems
- staging

---

# 69. PackageFS

PackageFS exposes packaged resources:

```text
app/resources/*
```

Typically read-only.

---

# 70. ArchiveFS

ArchiveFS can expose:

```text
zip
tar
custom package
```

as a virtual filesystem.

Archive parsing belongs to optional modules.

---

# 71. OverlayFS

OverlayFS combines layers:

```text
WritableLayer
    ↓
ReadOnlyLayer
    ↓
PackageLayer
```

Useful for:

- applications
- testing
- containers
- mod systems
- asset packaging

---

# 72. TransformFS

A transform filesystem can apply:

```text
Compression
Encryption
Integrity
Caching
Deduplication
```

to an underlying filesystem.

---

# 73. Encryption Layer

Encryption is not built into every file operation.

Instead:

```text
TransformFS
    ↓
CryptoProvider
    ↓
BOOTSTRAP-610
```

This keeps storage independent of cryptographic implementation.

---

# 74. Secret Files

A secret file can be marked:

```axiom
SecretFile
```

The runtime must:

- restrict permissions
- avoid diagnostic content
- prevent accidental logging
- integrate with `Secret<T>`
- request secure deletion where supported

---

# 75. Secure Deletion

Axiom must explicitly state that secure deletion is not generally guaranteed.

```axiom
file.secure_delete()
```

may provide only best-effort behavior.

SSD wear leveling and copy-on-write filesystems can prevent deterministic physical erasure.

---

# 76. Memory-Mapped Files

API:

```axiom
let mapping = file.map(
    MapMode.ReadWrite,
    offset,
    length
)?;
```

Mapping modes:

```text
Read
ReadWrite
CopyOnWrite
```

---

# 77. Mapping Lifetime

A mapping owns the underlying OS mapping.

The mapped region becomes invalid when:

```axiom
mapping.close()
```

is called.

The compiler/runtime must prevent use-after-unmap through its safe mapping abstraction.

---

# 78. Memory Model Integration

Axiom's memory model treats mapped memory as a special external storage region.

It is not automatically equivalent to ordinary heap memory.

The compiler must preserve mapping lifetime and synchronization semantics.

---

# 79. Mapping Synchronization

```axiom
mapping.flush()
```

requests persistence of modified mapped pages.

The API must distinguish:

```text
memory visibility
storage durability
```

---

# 80. Concurrent Mapping

Multiple mappings of the same file require explicit synchronization.

The runtime must not assume filesystem atomicity implies memory atomicity.

---

# 81. Sparse Files

Axiom may expose:

```axiom
file.set_length()
file.allocate()
file.punch_hole()
```

where supported.

Sparse regions read as zero bytes according to filesystem semantics.

---

# 82. Preallocation

```axiom
file.preallocate(size)?;
```

is recommended before large sequential writes.

This reduces fragmentation and late disk-full failures.

---

# 83. Storage Resource Accounting

BOOTSTRAP-606 tracks:

```text
open files
file descriptors
storage bytes
allocated bytes
mapped bytes
I/O operations
read bandwidth
write bandwidth
queue depth
filesystem watches
temporary storage
```

---

# 84. Storage Quotas

Quotas may be defined for:

```text
application
service
process
user
sandbox
filesystem
resource group
```

Example:

```text
max_bytes = 2 GiB
max_files = 100000
max_write_bandwidth = 50 MiB/s
max_iops = 5000
```

---

# 85. Quota Enforcement

Before allocation:

```text
reserve
    ↓
perform
    ↓
commit actual usage
```

If reservation fails:

```text
QuotaExceeded
```

is returned without starting the operation.

---

# 86. Disk Full

Disk-full errors must remain distinguishable from:

```text
QuotaExceeded
ReadOnlyFilesystem
DeviceUnavailable
PermissionDenied
```

Applications may then choose appropriate recovery.

---

# 87. Removable Media

Storage backends must handle:

```text
Mounted
Unmounting
Removed
Unavailable
Reconnected
```

File handles may become invalid after removal.

---

# 88. Volume Information

```axiom
VolumeInfo {
    id
    filesystem
    capacity
    free
    available
    block_size
    flags
    readonly
    removable
}
```

---

# 89. Filesystem Watchers

API:

```axiom
let watcher = fs.watch("config")?;

await watcher.next();
```

Events:

```text
Created
Modified
Deleted
Renamed
MetadataChanged
Overflow
RescanRequired
```

---

# 90. Windows Watcher

Use:

```text
ReadDirectoryChangesW
```

where supported.

---

# 91. Linux Watcher

Use:

```text
inotify
```

with fallback polling where necessary.

---

# 92. macOS Watcher

Use:

```text
FSEvents
kqueue
```

depending on required semantics.

---

# 93. Watcher Reliability

Filesystem watchers are notifications, not durable event logs.

An overflow event means:

```text
rescan required
```

The runtime must never silently claim no events were lost.

---

# 94. Watcher Backpressure

Watcher queues are bounded.

Possible behavior:

```text
drop + Overflow
coalesce
block producer
```

must be explicitly selected.

---

# 95. File Cache

Axiom may provide a storage cache:

```axiom
StorageCache
```

Policies:

```text
None
ReadThrough
WriteThrough
WriteBack
```

Write-back caching requires explicit durability semantics.

---

# 96. Persistent Cache

Persistent cache must be treated as disposable.

It must not be used for correctness-critical application state unless explicitly promoted to durable state.

---

# 97. Content-Addressed Storage

Optional higher-level VFS:

```text
hash(content) → object ID
```

This belongs outside the core filesystem.

BOOTSTRAP-611 only provides primitives required to implement it.

---

# 98. Compression

Compression is a transform layer.

```text
Application
 ↓
CompressedFS
 ↓
NativeFS
```

Compression must not alter base filesystem semantics unexpectedly.

---

# 99. Network Integration

BOOTSTRAP-609 may use:

```axiom
file.send_to(socket)
```

where the platform supports zero-copy transfer.

Possible native mechanisms:

```text
sendfile
splice
TransmitFile
```

Fallback:

```text
read → network write
```

---

# 100. IPC Integration

BOOTSTRAP-604 may transfer:

- file descriptors
- OS handles
- shared mappings

when the security capability permits.

The transferred handle must preserve its reduced rights.

---

# 101. Security Integration

Every filesystem operation passes through:

```text
OS authority
    ↓
Deployment policy
    ↓
Axiom policy
    ↓
Filesystem capability
    ↓
Handle rights
    ↓
Operation
```

---

# 102. Capability Attenuation

Example:

```axiom
let app_fs = filesystem_cap;
let cache_fs = app_fs.restrict("cache");
let read_cache = cache_fs.read_only();
```

A child service cannot escape `cache`.

---

# 103. Resource Governor Integration

Every potentially expensive operation charges:

```text
CPU
I/O
memory
handles
mapped memory
storage
```

to the current resource group.

---

# 104. Scheduler Integration

Async file operations become scheduler tasks.

```text
Task
 ↓
FileOperation
 ↓
OS completion
 ↓
I/O Reactor
 ↓
Task Resume
```

No unnecessary worker thread is created for completion-based native I/O.

---

# 105. Synchronization Integration

File operations can use:

```text
Mutex
RwLock
Semaphore
Event
Channel
```

from BOOTSTRAP-608.

The storage layer must not invent duplicate synchronization primitives.

---

# 106. State Integration

BOOTSTRAP-600 may use storage transactions:

```text
checkpoint
    ↓
write snapshot
    ↓
sync
    ↓
atomic replace
    ↓
commit checkpoint
```

Recovery uses transaction manifests and snapshot metadata.

---

# 107. Configuration Integration

BOOTSTRAP-601 should use:

```text
temporary config
    ↓
validated config
    ↓
sync
    ↓
atomic replace
```

rather than modifying configuration files in place.

---

# 108. Diagnostics Integration

Storage diagnostics expose:

```text
operation ID
file ID
volume ID
bytes
latency
queue delay
backend
result
error
```

Sensitive paths may be redacted.

---

# 109. Logging

Default logs must not contain:

- secret file contents
- private key material
- full sensitive paths when policy forbids them

Structured metadata is preferred.

---

# 110. Process Integration

BOOTSTRAP-605 may require service storage directories:

```text
ServiceData
ServiceCache
ServiceTemp
ServiceLogs
```

These directories are provisioned through capability-scoped storage.

---

# 111. Crash Recovery

After process crash:

```text
open handles → invalid
pending I/O → completed/failed according to OS
temporary files → recoverable
transactions → inspected
journals → replayed
```

The storage runtime must never assume pending asynchronous operations survived process death.

---

# 112. Checkpoint Quiescence

Before checkpoint:

```text
stop new writes
drain storage operations
flush required files
commit transaction
record durable marker
resume
```

This integrates with BOOTSTRAP-607 cancellation and BOOTSTRAP-600 checkpointing.

---

# 113. Snapshot Semantics

Axiom distinguishes:

```text
Logical Snapshot
Filesystem Snapshot
Memory Snapshot
```

BOOTSTRAP-611 provides only the primitives for logical snapshots.

Native volume snapshots remain platform-specific extensions.

---

# 114. Error Model

Storage errors are typed.

```axiom
StorageError {
    NotFound
    AlreadyExists
    AccessDenied
    InvalidPath
    InvalidHandle
    IsDirectory
    NotDirectory
    ReadOnly
    DiskFull
    QuotaExceeded
    DeviceUnavailable
    CrossDevice
    Busy
    Locked
    Interrupted
    Timeout
    Cancelled
    IoFailure
    Corrupt
    Unsupported
}
```

---

# 115. Error Context

Errors may contain:

```text
operation
path
file_id
volume_id
offset
requested_bytes
completed_bytes
native_error
```

Sensitive values must be redacted according to policy.

---

# 116. Cancellation

All async operations accept cancellation:

```axiom
await file.read_async(buffer, cancel);
```

Cancellation means:

```text
request operation cancellation
```

not necessarily immediate OS-level termination.

Completion must always resolve exactly once.

---

# 117. Deadlines

Operations may use:

```axiom
Deadline
Timeout
```

The scheduler owns timeout processing.

Storage should not create independent timer infrastructure.

---

# 118. Blocking Boundary

Blocking filesystem calls are forbidden on latency-sensitive async workers unless explicitly permitted.

They are redirected to:

```text
BlockingPool
```

from BOOTSTRAP-607.

---

# 119. Buffer Management

Storage uses pooled buffers where beneficial.

Possible pools:

```text
SmallBufferPool
LargeBufferPool
AlignedBufferPool
DirectIOPool
```

Pools are optional and resource-accounted.

---

# 120. Zero-Copy

The implementation should avoid:

```text
kernel → temporary buffer → runtime buffer → application buffer
```

when native APIs permit direct transfer.

Zero-copy must not compromise safety or capability checks.

---

# 121. ABI

Storage ABI uses opaque handles.

Example:

```text
AxiomFileHandle
AxiomDirHandle
AxiomMappingHandle
AxiomWatcherHandle
```

No OS-native struct layout becomes part of the stable Axiom ABI.

---

# 122. FFI

Foreign APIs may receive duplicated native handles through explicit conversion:

```axiom
file.native_handle(capability)?
```

The conversion requires appropriate capability.

Ownership must be explicit:

```text
Borrow
Duplicate
Transfer
```

---

# 123. Compiler Integration

The compiler recognizes storage operations for:

- async lowering
- capability metadata
- cancellation propagation
- resource accounting
- effect analysis
- dead stripping

Example:

```axiom
@requires(FilesystemRead)
fn load_asset(...) { ... }
```

---

# 124. Storage Effects

The compiler may represent:

```text
FilesystemRead
FilesystemWrite
FilesystemMetadata
FilesystemWatch
FilesystemMap
FilesystemDurability
```

as effects.

This allows static inspection without requiring a heavyweight effect system.

---

# 125. IR Operations

Conceptual IR:

```text
storage.open
storage.read
storage.write
storage.read_at
storage.write_at
storage.sync
storage.rename
storage.remove
storage.map
storage.unmap
storage.watch
storage.tx.begin
storage.tx.commit
storage.tx.abort
```

---

# 126. Capability Verification

The linker may calculate:

```text
RequiredFilesystemCapabilities
```

from the final call graph.

Unused storage capability metadata can be removed.

---

# 127. Dead Stripping

If an application uses only:

```text
MemoryFS
```

the final executable should not contain:

- Windows filesystem backend
- Linux filesystem backend
- watcher implementation
- transaction journal
- archive backend

unless referenced.

---

# 128. Minimal Storage Profile

A minimal embedded profile may contain only:

```text
Path
File
Read
Write
```

and exclude:

```text
VFS
watchers
transactions
mmap
native volume management
```

---

# 129. Full Native Profile

Desktop/server builds may include:

```text
NativeFS
AsyncIO
MMap
Watchers
Transactions
VFS
Quota
Durability
```

---

# 130. Deterministic Test Filesystem

Axiom must provide:

```axiom
TestFS
```

with deterministic behavior.

It can simulate:

- short reads
- short writes
- latency
- disk full
- quota exceeded
- device removal
- permission failure
- rename failure
- crash
- power loss
- watcher overflow

---

# 131. Fault Injection

Example:

```axiom
storage.inject(
    Fault.AfterBytes(4096)
)
```

Tests must be able to reproduce failures deterministically.

---

# 132. Power-Loss Simulation

The test backend must simulate:

```text
write
flush
rename
crash
restart
recover
```

and verify durable-state invariants.

---

# 133. Race Testing

Test cases must cover:

- rename during open
- delete during read
- permission change
- symlink replacement
- directory replacement
- concurrent writers
- concurrent mapping
- watcher overflow

---

# 134. Security Testing

Required tests:

- path traversal
- symlink escape
- junction escape
- TOCTOU replacement
- capability attenuation
- unauthorized delete
- unauthorized map
- handle rights escalation
- leaked native handles

---

# 135. Resource Testing

Test:

```text
max open files
max mapped bytes
max storage bytes
max IOPS
max bandwidth
max watcher count
```

The runtime must reject excess allocations deterministically.

---

# 136. Performance Targets

Target properties:

```text
sync file I/O ≈ native API overhead
async I/O ≈ native completion overhead
no mandatory allocation for simple read/write
no global storage mutex
no mandatory GC
minimal handle wrapper overhead
```

---

# 137. Async Performance

For native completion-based backends:

```text
application task
 → submit I/O
 → OS
 → completion
 → task resume
```

must avoid:

```text
application task
 → thread creation
 → blocking syscall
 → thread destruction
```

---

# 138. Concurrency Performance

Concurrent positioned I/O should not require a shared file lock.

Applications should be able to perform:

```text
read_at(A)
read_at(B)
write_at(C)
```

concurrently.

---

# 139. Storage Thread Safety

A `File` may be:

```text
ThreadSafe
ThreadAffine
```

depending on backend.

The API should expose this through type/trait metadata where required.

---

# 140. File Sharing

Explicit file duplication is preferred over implicit sharing.

```axiom
let f2 = f.duplicate()?;
```

This makes lifetime and ownership visible.

---

# 141. Native Handle Generation

Internal handle table entries use:

```text
index + generation
```

to prevent stale-handle reuse.

This follows BOOTSTRAP-608's generation-safe resource design.

---

# 142. Storage Transaction Handle

Transactions also use generation-safe opaque handles.

Invalidated transaction handles must deterministically fail.

---

# 143. Virtual Mounts

VFS can mount:

```axiom
vfs.mount("/assets", package_fs);
vfs.mount("/cache", native_fs);
vfs.mount("/tmp", memory_fs);
```

Mount resolution uses longest-prefix matching.

---

# 144. Mount Security

Each mount has:

```text
root capability
allowed operations
maximum size
read-only flag
resource group
```

A mount cannot bypass its parent security boundary.

---

# 145. Overlay Resolution

For:

```text
/app/config
```

the VFS searches mounted layers in priority order.

A deleted upper-layer object may create a tombstone hiding lower-layer content.

---

# 146. Package Resources

Executable/resource packages may expose:

```text
resource://...
```

but resources remain read-only unless explicitly copied into writable storage.

---

# 147. URI-like Storage Names

Axiom may support:

```text
file://
mem://
package://
overlay://
```

as higher-level names.

The native `Path` API remains canonical for filesystem operations.

---

# 148. File Format Boundary

BOOTSTRAP-611 stores bytes.

Structured formats belong to higher layers.

This prevents the filesystem layer from depending on:

- JSON
- XML
- YAML
- database formats
- protobuf

---

# 149. Storage Metadata Versioning

Persistent transaction metadata must contain:

```text
format_version
runtime_version
transaction_id
application_id
build_id
```

Unknown incompatible versions must fail safely.

---

# 150. Reproducibility

Filesystem behavior tests should be reproducible under:

```text
deterministic clock
deterministic scheduler
TestFS
fault injection
```

---

# 151. Configuration

BOOTSTRAP-601 config may define:

```text
storage.max_open_files
storage.max_cache_bytes
storage.io_queue_depth
storage.default_buffer_size
storage.transaction_directory
storage.temp_directory
storage.durability_policy
storage.watcher_queue_size
```

Configuration changes apply through immutable snapshots.

---

# 152. Diagnostics

Metrics:

```text
storage.read_bytes
storage.write_bytes
storage.read_ops
storage.write_ops
storage.read_latency
storage.write_latency
storage.open_handles
storage.mapped_bytes
storage.cache_hits
storage.cache_misses
storage.sync_count
storage.errors
```

---

# 153. Tracing

Each async operation can produce:

```text
storage.open
storage.read
storage.write
storage.sync
storage.rename
storage.map
```

trace spans.

---

# 154. Crash Diagnostics

Crash reports may include:

```text
open handle count
active storage operations
filesystem backend
pending transaction IDs
mount IDs
```

but never raw secret contents.

---

# 155. Encryption Integration

For encrypted storage:

```text
Application
 ↓
EncryptedFS
 ↓
NativeFS
 ↓
OS
```

Key management comes from BOOTSTRAP-610.

Storage itself must not implement independent key lifecycle logic.

---

# 156. Key Rotation

EncryptedFS may support:

```text
old key
new key
re-encryption
atomic metadata transition
```

but key management remains outside BOOTSTRAP-611.

---

# 157. Storage Integrity

Optional transform layers may provide:

```text
checksum
MAC
Merkle tree
```

Core filesystem does not require these.

---

# 158. Device Errors

The runtime distinguishes:

```text
DeviceRemoved
DeviceOffline
MediaError
FilesystemCorrupt
ReadOnly
NoSpace
QuotaExceeded
```

Applications may choose recovery policy.

---

# 159. Filesystem Corruption

A corruption error must not automatically trigger destructive repair.

Recovery actions are explicit.

---

# 160. Mount Changes

Where supported:

```axiom
volume.watch()
```

can report:

```text
Mounted
Unmounted
Changed
Removed
```

Mobile and WASM backends may provide reduced semantics.

---

# 161. Application Data Layout

Axiom recommends logical directories:

```text
app://data
app://config
app://cache
app://temp
app://logs
app://resources
```

The deployment layer maps them to physical locations.

---

# 162. Security Boundary

Applications should not need to know their absolute OS storage path.

This reduces:

- platform coupling
- path leakage
- sandbox errors
- deployment differences

---

# 163. Storage Context

A service receives a storage context:

```axiom
struct StorageContext {
    data
    config
    cache
    temp
    resources
}
```

Each member has an independent capability.

---

# 164. Example

```axiom
fn save_state(ctx: StorageContext, state: State) -> Result {
    let temp = ctx.data.temp_file()?;

    temp.write_all(encode(state))?;
    temp.sync()?;

    ctx.data.replace_atomic(
        temp,
        "state.bin"
    )?;

    ctx.data.sync_parent_dir("state.bin")?;

    return Ok;
}
```

This is the canonical crash-safe state-update pattern.

---

# 165. Async Example

```axiom
async fn load(path: Path) -> Result<Bytes> {
    let file = await fs.open_async(path, OpenMode.Read)?;
    let info = file.stat()?;

    let buffer = Bytes.alloc(info.size);

    await file.read_exact_async(buffer)?;

    return Ok(buffer);
}
```

---

# 166. Concurrent Random Access

```axiom
async fn read_chunks(file: File) {
    let a = file.read_at_async(0, buf_a);
    let b = file.read_at_async(1_MiB, buf_b);
    let c = file.read_at_async(2_MiB, buf_c);

    await join(a, b, c);
}
```

No shared cursor is required.

---

# 167. Transaction Example

```axiom
let tx = ctx.data.transaction()?;

tx.write("state.new", encoded)?;
tx.sync("state.new")?;
tx.replace("state.new", "state.bin")?;

tx.commit()?;
```

---

# 168. VFS Example

```axiom
let vfs = Vfs();

vfs.mount("/resources", PackageFS.open(...));
vfs.mount("/cache", NativeFS.open(...));
vfs.mount("/tmp", MemoryFS.new());

let file = vfs.open("/resources/model.bin")?;
```

---

# 169. Capability Example

```axiom
fn load_model(
    fs: Capability<FilesystemRead>,
    path: Path
) -> Result<Model> {
    let file = fs.open(path)?;
    ...
}
```

A function cannot silently acquire filesystem authority.

---

# 170. API Surface

Core API:

```axiom
Path
File
Directory
FileInfo
VolumeInfo
FileMapping
FileLock
FileWatcher
StorageTransaction
FileSystem
NativeFS
MemoryFS
```

Optional:

```text
PackageFS
OverlayFS
ArchiveFS
TransformFS
EncryptedFS
StorageCache
```

---

# 171. Platform Backend Interface

```axiom
trait FileSystemBackend {
    open(...)
    read(...)
    write(...)
    seek(...)
    stat(...)
    rename(...)
    remove(...)
    map(...)
    sync(...)
    watch(...)
}
```

Backend implementations are private runtime components unless explicitly exposed through extension APIs.

---

# 172. Backend Capability Discovery

```axiom
backend.capabilities()
```

may report:

```text
AsyncIO
MMap
SparseFiles
FileLocks
Watchers
AtomicReplace
Durability
DirectIO
HardLinks
Symlinks
```

---

# 173. Capability Negotiation

Higher layers must query capabilities before depending on optional features.

Example:

```axiom
if fs.supports(MemoryMap) {
    ...
}
```

---

# 174. Unsupported Operations

Unsupported features return:

```text
Unsupported
```

They must not silently emulate an operation with materially different semantics.

---

# 175. Native Backend Isolation

Platform-specific code is confined to:

```text
runtime/storage/
    windows/
    linux/
    macos/
    android/
    ios/
    wasm/
    embedded/
```

The public API remains platform-neutral.

---

# 176. Compiler Packaging

The compiler links only the storage backend actually required by the target.

Example:

```text
WASM MemoryFS application
```

must not pull in:

```text
Win32
POSIX
Android
iOS
```

storage code.

---

# 177. Static Linking

Storage runtime components must support static linking.

No external runtime storage DLL/SO is required for the standard native profile.

---

# 178. Dynamic Libraries

Axiom-generated libraries can expose storage-independent APIs.

Native handles must not cross ABI boundaries without explicit ownership rules.

---

# 179. Versioning

Storage ABI uses:

```text
major
minor
capability bitmap
```

Backend ABI changes require version negotiation.

---

# 180. Compatibility

Older applications may run against newer runtime backends when:

```text
required capability subset ⊆ backend capabilities
```

---

# 181. Thread Safety Contract

Every storage object documents:

```text
Send
Sync
ThreadAffine
TaskAffine
```

The compiler may enforce these traits.

---

# 182. No Hidden Reference Counting

Storage handles must not require general-purpose reference counting.

If sharing is necessary:

```axiom
duplicate()
```

creates explicit ownership.

---

# 183. Memory Safety

Unsafe native handles cannot be constructed from arbitrary integers in safe Axiom code.

Conversion from raw native handles requires an explicit unsafe boundary.

---

# 184. Unsafe Boundary

```axiom
unsafe {
    NativeHandle.from_raw(...)
}
```

does not grant additional filesystem capabilities.

It only permits bypassing language-level safety checks.

---

# 185. Security vs Unsafe

Important invariant:

```text
unsafe ≠ privileged
```

An unsafe function still needs filesystem capability.

---

# 186. Storage and AI Metadata

Compiler artifacts may contain:

```text
storage effects
required capabilities
durability requirements
filesystem dependencies
backend requirements
```

This allows AI tools to understand storage behavior without reading all source code.

---

# 187. Example Metadata

```text
Function: save_state
Effects:
    FilesystemWrite
    FilesystemDurability

Capabilities:
    FilesystemWrite

Guarantees:
    AtomicReplace
    FileDurability
```

---

# 188. Static Analysis

The compiler should detect:

- ignored partial writes
- use after close
- invalid mapping lifetime
- missing capability
- unsupported backend assumptions
- transaction misuse
- async blocking I/O
- suspicious path traversal
- ignored durability errors

---

# 189. Lint Categories

```text
STORAGE001 Missing capability
STORAGE002 Ignored partial write
STORAGE003 Blocking I/O in async context
STORAGE004 Unsafe path construction
STORAGE005 Ignored sync failure
STORAGE006 Mapping lifetime violation
STORAGE007 Transaction not committed
STORAGE008 Secret path leakage
```

---

# 190. Testing Layers

Required:

```text
unit tests
integration tests
platform tests
stress tests
race tests
fault injection
power-loss simulation
fuzz tests
security tests
ABI tests
performance tests
```

---

# 191. Fuzzing Targets

Fuzz:

- paths
- directory traversal
- filesystem transactions
- watcher events
- metadata parsing
- archive mounts
- mapping boundaries
- error translation
- journal recovery

---

# 192. Property Tests

Examples:

```text
write(x); read() == x
rename(a,b); !exists(a) && exists(b)
transaction abort → no committed mutation
transaction commit → committed mutation
path restriction never escapes root
handle generation prevents stale reuse
```

---

# 193. Power-Loss Property

For a durable transaction:

```text
crash at arbitrary allowed point
```

must result in one of the documented valid states.

Never:

```text
partially visible impossible state
```

within the transaction's documented guarantees.

---

# 194. Watcher Property

If event queue overflows:

```text
Overflow
```

must be emitted or the API must otherwise explicitly indicate that a rescan is required.

---

# 195. Resource Property

No storage operation may exceed its configured:

```text
memory
I/O
handle
storage
mapping
queue
```

budget without explicit override capability.

---

# 196. Security Property

For every operation:

```text
effective_authority(operation)
    ⊆
    caller_authority
```

must hold.

---

# 197. Durability Property

The runtime must never report:

```text
Durable
```

unless the requested durability operation completed successfully according to backend semantics.

---

# 198. Error Property

Native errors must be preserved sufficiently to diagnose the failure.

Lossy conversion to generic:

```text
IOError
```

alone is prohibited.

---

# 199. Performance Property

The common path:

```text
open
read
close
```

must add only a thin abstraction layer over native operations.

---

# 200. Minimality Property

No application should pay for:

```text
transactions
watchers
mmap
VFS
compression
encryption
```

unless referenced.

---

# 201. API Design Rule

The storage API follows Axiom's struct-only model.

Example:

```axiom
fn read(file: File, buffer: []u8) -> Result<usize>
```

The compiler may provide method syntax:

```axiom
file.read(buffer)
```

Both represent the same underlying function.

---

# 202. Override/Extension

Platform-specific behavior uses trait implementations:

```axiom
impl FileSystemBackend for WindowsFS { ... }
impl FileSystemBackend for LinuxFS { ... }
```

Application-specific VFS providers can implement the same interface.

---

# 203. No Class Hierarchy

Storage does not require:

```text
FileBase
NativeFile
AsyncFile
EncryptedFile
CachedFile
```

class inheritance.

Composition is used instead:

```text
EncryptedFS(
    CachedFS(
        NativeFS(...)
    )
)
```

---

# 204. Composition Benefits

This permits:

```text
NativeFS
 + encryption
 + compression
 + caching
 + tracing
```

without deep inheritance hierarchies.

---

# 205. Layer Ordering

A transform stack is explicit:

```text
Application
 ↓
Transaction
 ↓
Encryption
 ↓
Compression
 ↓
Cache
 ↓
NativeFS
```

Invalid combinations are rejected during construction.

---

# 206. Storage Context Lifetime

A `StorageContext` belongs to a process/service lifecycle.

When a service stops:

```text
new writes disabled
pending operations drained
required files synced
handles closed
```

before shutdown completes.

---

# 207. Service Isolation

Each service may have:

```text
separate storage root
separate quota
separate capability
separate cache
separate temporary directory
```

This prevents accidental cross-service storage access.

---

# 208. Multi-Process Access

Multiple processes may share files if capabilities permit.

The storage layer does not automatically serialize arbitrary application semantics.

Applications must use:

```text
locks
transactions
atomic replace
IPC
```

as appropriate.

---

# 209. Cross-Process State

Recommended pattern:

```text
shared file
+
atomic replacement
+
file locking
```

or:

```text
IPC service
+
single storage owner
```

The latter may be preferable for complex state.

---

# 210. Storage Ownership Model

Applications should generally have a single logical owner for mutable state.

Other processes receive access through:

```text
IPC
```

or explicit shared-storage capability.

---

# 211. Database Boundary

A database layer built later on top of 611 may use:

```text
File
MMap
Lock
Sync
Transaction
```

without modifying the storage core.

---

# 212. Serialization Boundary

Serialization layers write to:

```axiom
[]u8
```

then use storage APIs.

This keeps serialization independent of filesystem semantics.

---

# 213. Application State Boundary

BOOTSTRAP-600 decides:

```text
what state must persist
```

BOOTSTRAP-611 decides:

```text
how bytes become durable
```

---

# 214. Configuration Boundary

BOOTSTRAP-601 decides:

```text
configuration precedence/schema
```

BOOTSTRAP-611 provides:

```text
safe file persistence
```

---

# 215. Crypto Boundary

BOOTSTRAP-610 decides:

```text
keys
algorithms
trust
```

BOOTSTRAP-611 decides:

```text
where encrypted bytes are stored
```

---

# 216. Security Boundary

BOOTSTRAP-603 decides:

```text
who may access storage
```

BOOTSTRAP-611 decides:

```text
how storage operations execute
```

---

# 217. Resource Boundary

BOOTSTRAP-606 decides:

```text
how much storage resource is allowed
```

BOOTSTRAP-611 performs:

```text
accounting hooks
```

---

# 218. Scheduler Boundary

BOOTSTRAP-607 decides:

```text
which task executes
```

BOOTSTRAP-611 reports:

```text
I/O submission/completion
```

---

# 219. Synchronization Boundary

BOOTSTRAP-608 owns:

```text
memory synchronization
locks
atomics
channels
```

BOOTSTRAP-611 exposes file-specific locking and storage semantics.

---

# 220. Networking Boundary

BOOTSTRAP-609 owns:

```text
network transport
```

BOOTSTRAP-611 provides:

```text
file → network zero-copy
```

where supported.

---

# 221. Diagnostics Boundary

BOOTSTRAP-602 owns:

```text
logging
tracing
crash reporting
```

BOOTSTRAP-611 emits storage events.

---

# 222. Process Boundary

BOOTSTRAP-605 owns:

```text
process/service lifecycle
```

BOOTSTRAP-611 participates in:

```text
startup
shutdown
drain
recovery
```

---

# 223. Required Native Backends

The first implementation must target:

```text
Windows
Linux
macOS
Android
iOS
WASM
```

with embedded support designed as an extension point.

---

# 224. Backend Priority

Native implementation priority:

```text
1. Windows
2. Linux
3. macOS
4. Android
5. iOS
6. WASM
7. Embedded
```

The abstraction must be designed before backend-specific optimization.

---

# 225. Core Runtime Files

Suggested implementation structure:

```text
runtime/storage/
    path.ax
    file.ax
    directory.ax
    metadata.ax
    mapping.ax
    transaction.ax
    watcher.ax
    filesystem.ax
    capability.ax
    error.ax
    buffer.ax
    cache.ax
    backend.ax
```

Platform:

```text
runtime/storage/windows/
runtime/storage/linux/
runtime/storage/macos/
runtime/storage/android/
runtime/storage/ios/
runtime/storage/wasm/
runtime/storage/embedded/
```

---

# 226. Compiler Components

Compiler support:

```text
frontend/storage-effects
semantic/storage-capabilities
ir/storage-ops
lowering/storage-async
backend/storage-linking
```

---

# 227. Build Metadata

Generated metadata should include:

```text
StorageCapabilities
StorageBackends
StorageEffects
DurabilityRequirements
MappedMemoryRequirements
```

---

# 228. Security Manifest

Executable metadata may declare:

```text
filesystem.read
filesystem.write
filesystem.create
filesystem.delete
filesystem.map
filesystem.watch
```

Deployment policy can then approve or reject them.

---

# 229. Runtime Startup

At startup:

```text
load storage policy
↓
initialize backend
↓
register resource accounting
↓
register diagnostics
↓
initialize application storage roots
↓
recover incomplete transactions
↓
publish StorageContext
```

---

# 230. Shutdown

At shutdown:

```text
reject new operations
↓
cancel optional operations
↓
drain required operations
↓
commit/abort active transactions
↓
sync required durable data
↓
close watchers
↓
close mappings
↓
close files
↓
release backend
```

---

# 231. Shutdown Failure

If durability fails during graceful shutdown:

```text
shutdown result = StorageFailure
```

The runtime must not silently claim successful persistence.

---

# 232. Recovery Priority

Recovery order:

```text
1. validate storage root
2. inspect journals
3. recover committed transactions
4. discard incomplete temporary state
5. validate metadata
6. publish storage context
```

---

# 233. Recovery Safety

Unknown/corrupt journals must be quarantined rather than destructively deleted.

---

# 234. Quarantine

A failed transaction may move into:

```text
.recovery/
```

with restricted access.

---

# 235. Storage Health

The runtime exposes:

```axiom
StorageHealth {
    Healthy
    Degraded
    ReadOnly
    Unavailable
    Corrupt
}
```

---

# 236. Health Integration

BOOTSTRAP-605 can use storage health for service readiness.

Example:

```text
storage unavailable
    ↓
service Degraded
```

rather than automatically killing the process.

---

# 237. Backpressure

Storage queues must apply backpressure when:

```text
queue full
I/O budget exhausted
memory budget exhausted
device saturated
```

Possible response:

```text
await
reject
defer
```

according to API semantics.

---

# 238. Priority I/O

Optional:

```axiom
IoPriority.Low
IoPriority.Normal
IoPriority.High
```

Priority must remain subordinate to security and resource limits.

---

# 239. Fairness

The resource governor must prevent one service from monopolizing storage bandwidth.

---

# 240. Burst Control

Short bursts may exceed nominal bandwidth within configured burst credits.

Long-term usage must remain within budget.

---

# 241. Storage Pressure

The runtime may signal:

```text
Normal
Warning
Critical
```

based on:

- free space
- quota
- I/O latency
- device health

Applications may evict caches during pressure.

---

# 242. Cache Eviction

Cache eviction must never delete durable application state.

The cache must be explicitly classified as disposable.

---

# 243. Temporary Data

Temporary storage may be automatically cleaned after process termination when safe.

---

# 244. Orphan Cleanup

At startup:

```text
scan temp/recovery directories
validate ownership
remove or quarantine stale entries
```

Cleanup must not cross capability roots.

---

# 245. Ownership Metadata

Temporary files may encode:

```text
application_id
process_id
generation
creation_time
```

to identify stale files.

---

# 246. PID Reuse

Process IDs alone are insufficient.

Use:

```text
ProcessId + Generation
```

from BOOTSTRAP-605.

---

# 247. File Lock + Process Generation

Lock ownership metadata may include:

```text
ProcessId
Generation
ApplicationId
```

to reduce PID reuse ambiguity.

---

# 248. Native OS Interoperability

Axiom-generated applications must still be able to interact with ordinary native files.

No proprietary mandatory filesystem format is introduced.

---

# 249. Native File Compatibility

Axiom can open:

```text
txt
bin
jpg
png
wav
mp4
model
database
```

as bytes.

The filesystem does not impose file formats.

---

# 250. Final Core Invariants

The implementation is correct only if all of these hold:

```text
I1  No filesystem authority without capability.
I2  No stale handle may become valid again.
I3  No implicit GC is required for file lifetime.
I4  Partial I/O is correctly represented.
I5  Async I/O integrates with scheduler.
I6  Blocking I/O is isolated.
I7  Durability is explicit.
I8  Atomic replace is preserved where promised.
I9  Transaction guarantees are never overstated.
I10 Path sandbox cannot be escaped.
I11 Symlink/reparse traversal obeys policy.
I12 Resource limits are enforced.
I13 Storage errors preserve useful native information.
I14 Watcher overflow is detectable.
I15 Mapping lifetime is explicit.
I16 Secret storage does not leak through diagnostics.
I17 Shutdown drains required storage operations.
I18 Crash recovery is deterministic.
I19 Unsupported capabilities are explicit.
I20 Optional storage features are dead-strippable.
I21 Native backends remain replaceable.
I22 Application code remains platform-independent.
I23 File identity is not confused with path identity.
I24 Atomic filesystem operations are distinguished from transactional guarantees.
I25 Durable state is never confused with cached state.
```

---

# 251. Acceptance Criteria

BOOTSTRAP-611 is complete only when:

1. `Path` supports UTF-8.
2. Path normalization is deterministic.
3. Sandbox roots cannot be escaped.
4. File capabilities are enforced.
5. File rights are immutable.
6. File lifetime is deterministic.
7. Partial reads are represented.
8. Partial writes are represented.
9. `read_exact` works.
10. `write_all` works.
11. Positioned I/O works.
12. Scatter/gather I/O works.
13. Async file I/O works.
14. Windows backend uses native async I/O where supported.
15. Linux backend supports io_uring or correct fallback.
16. macOS backend works.
17. Android backend respects sandbox.
18. iOS backend respects sandbox.
19. WASM backend requires host authority.
20. Directory iteration works.
21. Atomic create works.
22. Atomic rename works.
23. Atomic replace works.
24. File sync works.
25. Parent-directory sync is available where relevant.
26. Temporary files are race-safe.
27. File locking works.
28. Memory mapping works where supported.
29. Mapping lifetime is safe.
30. Sparse files are supported where available.
31. Preallocation is supported where available.
32. Metadata is available.
33. File identity is represented.
34. Symlink policy is enforced.
35. TOCTOU-resistant operations are available.
36. VFS works.
37. MemoryFS works.
38. PackageFS can be implemented.
39. OverlayFS can be implemented.
40. TransformFS can be implemented.
41. Storage transactions work.
42. Transaction recovery works.
43. Crash consistency tests pass.
44. Disk-full behavior is deterministic.
45. Quotas are enforced.
46. I/O resource budgets are enforced.
47. Watchers work.
48. Watcher overflow is observable.
49. Storage diagnostics work.
50. Storage tracing works.
51. Storage metrics work.
52. Secret data is not logged.
53. Encryption layer integrates with 610.
54. IPC handle transfer integrates with 604.
55. Network zero-copy integrates with 609.
56. Scheduler integration works.
57. Synchronization integration works.
58. Service lifecycle integration works.
59. State checkpoint integration works.
60. Configuration atomic persistence works.
61. Compiler capability metadata works.
62. Storage effects are represented in IR.
63. Unused backends are dead-stripped.
64. FFI ownership is explicit.
65. TestFS provides deterministic failures.
66. Power-loss simulation passes.
67. Race tests pass.
68. Security fuzzing passes.
69. Performance approaches native syscall overhead.
70. Minimal profiles contain no unnecessary storage subsystem components.

---

# 252. Reference Architecture

```text
                     ┌─────────────────────┐
                     │    Axiom Program    │
                     └──────────┬──────────┘
                                │
                     ┌──────────▼──────────┐
                     │    Storage API      │
                     │ File / Dir / Path   │
                     │ Map / Watch / Tx    │
                     └──────────┬──────────┘
                                │
                ┌───────────────▼────────────────┐
                │        Storage Policy          │
                │ 603 Security / 606 Resources  │
                │ 607 Scheduler / 608 Sync       │
                └───────────────┬────────────────┘
                                │
                     ┌──────────▼──────────┐
                     │        VFS          │
                     ├─────────────────────┤
                     │ NativeFS            │
                     │ MemoryFS            │
                     │ PackageFS           │
                     │ OverlayFS           │
                     │ TransformFS         │
                     └──────────┬──────────┘
                                │
          ┌─────────────────────┼─────────────────────┐
          │                     │                     │
   ┌──────▼──────┐      ┌───────▼──────┐      ┌─────▼─────┐
   │ Windows     │      │ Linux        │      │ macOS     │
   │ IOCP        │      │ io_uring     │      │ BSD/kqueue│
   └─────────────┘      └──────────────┘      └───────────┘
          │                     │                     │
   ┌──────▼──────┐      ┌───────▼──────┐      ┌─────▼─────┐
   │ Android     │      │ iOS          │      │ WASM      │
   │ Sandbox     │      │ Sandbox      │      │ HostFS    │
   └─────────────┘      └──────────────┘      └───────────┘

Cross-cutting:

600 State / Checkpoint / Recovery
601 Configuration
602 Diagnostics
603 Security / Capability
604 IPC
605 Process / Service
606 Resource Governor
607 Scheduler / Async
608 Synchronization
609 Networking
610 Cryptography
```

---

# 253. Architectural Conclusion

BOOTSTRAP-611 establishes the **native persistent storage foundation of Axiom**.

The critical architectural decision is that Axiom does **not** make the filesystem itself into a database or impose a heavyweight managed-memory model.

Instead:

```text
Bytes
  ↓
Files
  ↓
Atomic filesystem primitives
  ↓
Durability
  ↓
Transactions
  ↓
Higher-level serialization/database/state systems
```

This keeps the core fast and small while providing enough primitives to build sophisticated storage systems entirely in Axiom.

The resulting stack is:

```text
Application
    ↓
State / Config / Database / Serialization
    ↓
Storage Transactions
    ↓
VFS / TransformFS
    ↓
Native Storage
    ↓
OS
    ↓
Hardware
```

with security and resource governance crossing the entire stack.

**BOOTSTRAP-611 COMPLETE.**

---

# 254. Next Architecture Task

**BOOTSTRAP-612 — Native Serialization, Binary Data Model, Schema Evolution, Persistent Collections & Embedded Structured Storage Runtime 5.0**

Planned scope:

- canonical binary representation
- endian/ABI rules
- primitive encoding
- variable-length integers
- UTF-8/string encoding
- arrays/structs/enums/options/results
- schema IDs and versioning
- forward/backward compatibility
- zero-copy decoding
- streaming serialization
- deterministic serialization
- memory/file/network serialization
- persistent collections
- append-only logs
- WAL
- embedded key-value storage
- B-tree/LSM storage boundaries
- indexing
- checksums/integrity
- encryption hooks
- crash recovery
- storage transactions built on 611
- AI-readable schema metadata
- compiler-generated serializers
- binary ABI compatibility
- reflection-free serialization
- dead-strippable generated code
- performance targets approaching hand-written binary serialization.
:::

BOOTSTRAP-611 đã hoàn tất; chuỗi kiến trúc chuyển thẳng sang **BOOTSTRAP-612**.