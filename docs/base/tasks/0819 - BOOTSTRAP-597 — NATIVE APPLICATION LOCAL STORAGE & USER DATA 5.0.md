# BOOTSTRAP-597 — NATIVE APPLICATION LOCAL STORAGE & USER DATA 5.0
## APPLICATION DATA DIRECTORIES, CACHE, TEMPORARY DATA, USER DOCUMENTS, FILE STORAGE, ATOMIC UPDATE, WATCHING, MIGRATION, QUOTAS, BACKUP/RESTORE, PORTABLE MODE, SANDBOX STORAGE & CROSS-PLATFORM USER-DATA MODEL

**Trạng thái: COMPLETED / LOCKED**

`597` định nghĩa storage layer ở cấp application. Nó cố ý tách hoàn toàn:

```text
596 Resource Runtime
    = dữ liệu ứng dụng phân phối cùng application

597 Storage Runtime
    = dữ liệu application/user tạo hoặc thay đổi trong quá trình chạy
```

Không được biến filesystem path của từng OS thành API của Axiom.

---

# 597.1. Storage abstraction

```text
                         Application
                              │
                              ▼
                       Storage Manager
                              │
          ┌───────────────────┼───────────────────┐
          ▼                   ▼                   ▼
      App Data              Cache               Temp
          │                   │                   │
          ├──────────────┬────┴────┬──────────────┤
          ▼              ▼         ▼              ▼
     Preferences     Database   Documents      Generated
          │              │         │              │
          └──────────────┴─────────┴──────────────┘
                              │
                              ▼
                     Platform Storage Adapter
                              │
            ┌─────────────────┼─────────────────┐
            ▼                 ▼                 ▼
         Desktop           Mobile             WASM
```

---

# 597.2. Storage categories

Axiom chuẩn hóa các category:

```text
AppData
UserData
Cache
Temp
Documents
Downloads
Pictures
Music
Videos
SharedData
```

Không phải platform nào cũng hỗ trợ tất cả category.

---

# 597.3. AppData

Dùng cho dữ liệu riêng của application cần tồn tại qua restart.

Ví dụ:

```text
settings
local database
application state
indexes
```

---

# 597.4. UserData

Dùng cho dữ liệu người dùng mà application sở hữu nhưng không nhất thiết là tài liệu người dùng trực tiếp quản lý.

---

# 597.5. Cache

Cache có thể bị OS hoặc application xóa.

Không được lưu dữ liệu duy nhất cần thiết để khôi phục application vào Cache.

---

# 597.6. Temp

Temp dành cho dữ liệu ngắn hạn.

Không có persistence guarantee.

---

# 597.7. Documents

Documents đại diện dữ liệu người dùng có tính lâu dài.

---

# 597.8. Downloads

Downloads là location dành cho nội dung người dùng tải về.

---

# 597.9. Media directories

Các category:

```text
Pictures
Music
Videos
```

là logical locations.

Quyền truy cập do platform capability quyết định.

---

# 597.10. SharedData

SharedData cho dữ liệu được nhiều application/component chia sẻ.

Không được mặc định cấp quyền.

---

# 597.11. StorageHandle

```text
StorageHandle
```

là abstraction của một storage root.

---

# 597.12. StoragePath

```text
StoragePath
```

không phải raw OS string path.

---

# 597.13. Path normalization

StoragePath phải canonicalize:

```text .
..
duplicate separators
Unicode normalization policy
```

trước khi truy cập.

---

# 597.14. Root confinement

Application không được escape khỏi storage root thông qua path traversal.

```text
root/
 ├── data/
 └── ../../outside   ← REJECT
```

---

# 597.15. Absolute native paths

Raw absolute native path không phải API portable mặc định.

---

# 597.16. NativePath escape hatch

Platform API có thể expose native path trong platform-specific module.

---

# 597.17. Native path safety

Native path API phải được đánh dấu platform-specific và chịu security policy.

---

# 597.18. Storage capability

Application chỉ nhận storage roots mà runtime/platform cho phép.

---

# 597.19. Capability model

```text
Application
    │
    ▼
Capability
    │
    ├── AppData
    ├── Cache
    ├── Documents
    └── ExternalStorage
```

---

# 597.20. Sandboxed application

Sandboxed application chỉ nhìn thấy storage namespace được cấp.

---

# 597.21. Storage isolation

Hai applications không được mặc định truy cập AppData của nhau.

---

# 597.22. User-selected file

Người dùng có thể explicitly cấp một file/directory handle cho application.

---

# 597.23. Granted handle

Một granted file handle có thể tiếp tục được sử dụng mà không cần expose toàn filesystem.

---

# 597.24. Persistent grant

Platform có thể hỗ trợ persistent access grant.

---

# 597.25. Grant revocation

OS có thể revoke grant.

Runtime phải trả permission error thay vì giả định quyền vẫn tồn tại.

---

# 597.26. File abstraction

```text
File
```

là stream-oriented object.

---

# 597.27. Directory abstraction

```text
Directory
```

cung cấp enumeration và child lookup.

---

# 597.28. File metadata

```text
FileMetadata {
    type
    size
    created
    modified
    accessed
    permissions
    identity
}
```

Một số fields có thể `Unavailable`.

---

# 597.29. File identity

Filesystem file identity không nhất thiết là path.

Runtime có thể expose stable file identity khi OS hỗ trợ.

---

# 597.30. File open modes

```text
Read
Write
ReadWrite
Create
CreateNew
Truncate
Append
```

---

# 597.31. Explicit mutation

Opening file `Read` không được phép mutate.

---

# 597.32. Append

Append semantics phải delegate atomicity theo filesystem/platform contract.

---

# 597.33. Random access

File có:

```text
read_at()
write_at()
seek()
```

nếu backend hỗ trợ.

---

# 597.34. Sequential stream

File cũng có sequential read/write interface.

---

# 597.35. Async file I/O

Storage API hỗ trợ async I/O khi platform backend hỗ trợ.

---

# 597.36. Synchronous API

Synchronous API vẫn là first-class API cho utility/system programs.

---

# 597.37. No mandatory async runtime

File API không yêu cầu application phải chạy async executor.

---

# 597.38. Buffered I/O

Buffered I/O là optional layer.

---

# 597.39. Direct I/O

Platform-specific direct I/O có thể tồn tại nhưng không thuộc portable core.

---

# 597.40. Memory mapping

```text
file.map()
```

cho phép read-only hoặc writable mapping khi backend hỗ trợ.

---

# 597.41. Mapped lifetime

Mapped region giữ underlying file mapping hợp lệ theo lifetime contract.

---

# 597.42. Writable mapping

Writable mapping phải explicitly request.

---

# 597.43. Mapping synchronization

Flush semantics phải explicit.

---

# 597.44. Atomic replacement

Axiom cung cấp primitive:

```text
file.replace_atomic(temp, destination)
```

khi filesystem hỗ trợ.

---

# 597.45. Safe write pattern

```text
create temp
    ↓
write
    ↓
flush
    ↓
verify
    ↓
atomic replace
```

---

# 597.46. Crash consistency

Application có thể sử dụng atomic replacement để tránh file bị truncate một nửa khi crash.

---

# 597.47. Durable commit

```text
flush_data()
flush_metadata()
```

có thể yêu cầu durability mạnh hơn buffering thông thường.

---

# 597.48. Durability semantics

Axiom phải phân biệt:

```text Buffered
Written
Committed
Durable
```

---

# 597.49. No false durability

`write()` không được ngụ ý rằng dữ liệu chắc chắn đã tồn tại trên physical storage.

---

# 597.50. Transactional file update

Có thể group nhiều file changes thành logical transaction thông qua storage transaction layer.

---

# 597.51. Transaction scope

```text
StorageTransaction
```

không được giả định filesystem atomic multi-file nếu backend không hỗ trợ.

---

# 597.52. Journal fallback

Application storage layer có thể dùng journal để đạt crash consistency.

---

# 597.53. Database boundary

Database engine thuộc `455`.

Storage layer chỉ cung cấp primitive location/access.

---

# 597.54. Database path

Database có thể đặt dưới AppData hoặc UserData.

---

# 597.55. Storage locking

File locking phải hỗ trợ:

```text Shared
Exclusive
Advisory
Mandatory
```

nhưng semantics phụ thuộc platform.

---

# 597.56. Portable lock

Portable API chỉ guarantee semantics mà backend có thể đảm bảo.

---

# 597.57. Lock timeout

Lock acquisition có thể có timeout/deadline.

---

# 597.58. Lock cancellation

Async lock acquisition phải hỗ trợ cancellation.

---

# 597.59. Directory creation

```text directory.create()
directory.create_all()
```

---

# 597.60. Directory enumeration

Enumeration phải là lazy/streamable đối với directory lớn.

---

# 597.61. Enumeration snapshot

Không được mặc định guarantee directory enumeration là immutable snapshot.

---

# 597.62. Concurrent mutation

Concurrent file changes có thể khiến enumeration thay đổi.

---

# 597.63. Watch API

```text
directory.watch()
```

cho filesystem changes.

---

# 597.64. Watch events

```text
Created
Modified
Deleted
Renamed
Moved
```

---

# 597.65. Watch limitations

Filesystem watcher có thể mất events hoặc coalesce events.

API phải công khai limitation.

---

# 597.66. Rescan

Application phải có thể rescan directory sau watcher overflow.

---

# 597.67. Watch consistency

Watcher không phải transactional change log.

---

# 597.68. Temporary file

```text
temp.create_file()
```

phải tránh predictable-name collision.

---

# 597.69. Temporary directory

```text
temp.create_directory()
```

phải tạo namespace riêng.

---

# 597.70. Temp cleanup

Application nên cleanup temp data.

OS vẫn có thể cleanup sau crash.

---

# 597.71. Cache entry

Cache entry có:

```text
key
content
metadata
expiration
size
```

---

# 597.72. Content-addressed cache

Cache lớn nên hỗ trợ ContentID-based storage.

---

# 597.73. Cache integrity

Cache corruption chỉ invalidate cache entry; không làm hỏng canonical data.

---

# 597.74. Cache eviction

Eviction không phải observable correctness failure.

---

# 597.75. Cache quota

Cache có thể có quota.

---

# 597.76. Storage quota

Platform có thể impose application storage quota.

Runtime phải expose:

```text quota()
usage()
available()
```

khi có thể.

---

# 597.77. Quota unavailable

Nếu OS không cung cấp quota chính xác:

```text Unknown
```

thay vì giá trị giả.

---

# 597.78. Low-storage event

Runtime có thể phát:

```text StoragePressure
```

---

# 597.79. Storage pressure policy

Application có thể:

```text purge cache
reduce prefetch
defer writes
```

---

# 597.80. Automatic cache purge

Runtime có thể purge cache dưới storage pressure.

---

# 597.81. AppData protection

Runtime không được tự động purge AppData như Cache.

---

# 597.82. User documents

Documents phải được phân biệt khỏi ephemeral cache.

---

# 597.83. Document ownership

Một document có thể thuộc user hơn là application.

---

# 597.84. Document access

Application có thể nhận document handle qua:

```text open dialog
drag/drop
IPC
command line
system association
```

---

# 597.85. Document path independence

Application nên giữ document identity/handle thay vì hardcode path.

---

# 597.86. File association

Package manifest `593` có thể khai báo supported document types.

---

# 597.87. Open-with integration

Platform adapter map document type → application.

---

# 597.88. Save operation

Save API phải hỗ trợ atomic replacement khi có thể.

---

# 597.89. Save-as

Save-as trả về new document identity.

---

# 597.90. Document rename

Path rename không được làm mất logical document identity nếu platform hỗ trợ stable identity.

---

# 597.91. External modification

Application phải có thể detect external modification.

---

# 597.92. Conflict state

```text
Clean
Modified
ExternallyModified
Conflict
```

---

# 597.93. Conflict handling

Runtime không tự động overwrite user changes.

---

# 597.94. File timestamps

Timestamps không được coi là sole authoritative identity.

---

# 597.95. Content hash

Application có thể hash file content để detect exact state.

---

# 597.96. File fingerprint

```text
FileFingerprint {
    identity?
    size
    modified?
    content_hash?
}
```

---

# 597.97. Storage snapshot

Storage subsystem có thể tạo logical snapshot metadata.

---

# 597.98. Snapshot limitation

Filesystem snapshot không guarantee nếu backend không hỗ trợ transactional snapshot.

---

# 597.99. Backup

Backup integration là optional platform service.

---

# 597.100. Backup policy

Application có thể mark data:

```text
Critical
UserGenerated
Rebuildable
Cache
```

---

# 597.101. Backup eligibility

Cache mặc định không cần backup.

---

# 597.102. Restore

Restore có thể xảy ra khi application chưa chạy hoặc trong lifecycle initialization.

---

# 597.103. Restore migration

Restored data phải chạy schema migration trước khi application sử dụng nếu version cũ.

---

# 597.104. Data schema version

Application data có:

```text
schema_version
```

---

# 597.105. Migration registry

```text
Migration {
    from
    to
    migrate()
}
```

---

# 597.106. Migration ordering

Migration chain phải deterministic.

---

# 597.107. Migration failure

Migration failure không được delete original data.

---

# 597.108. Migration backup

Runtime có thể create backup/checkpoint trước migration.

---

# 597.109. Migration transaction

Nếu backend hỗ trợ transaction, migration nên chạy trong transaction.

---

# 597.110. Partial migration recovery

Không transaction thì migration phải sử dụng journal/version markers.

---

# 597.111. Data corruption detection

Critical application data có thể dùng checksums/content hashes.

---

# 597.112. Corruption handling

```text
DataCorrupt
```

không được tự động coi như empty database.

---

# 597.113. Recovery policy

Application có thể:

```text restore_backup
rebuild
quarantine
fail
```

---

# 597.114. Quarantine

Corrupt data có thể được moved sang quarantine để giữ evidence.

---

# 597.115. Storage permissions

Filesystem permissions không được abstract thành fake universal permissions.

---

# 597.116. Permission model

Axiom expose high-level capabilities:

```text Read
Write
Create
Delete
Share
```

---

# 597.117. OS permissions

Platform adapter map capability → OS permission.

---

# 597.118. Permission denied

```text StoragePermissionError
```

phải preserve source category.

---

# 597.119. User denial

User denial không phải storage corruption.

---

# 597.120. Security boundary

Storage path không phải security capability.

Capability/handle mới là security boundary.

---

# 597.121. Path confusion

Canonical path resolution phải diễn ra trước security check.

---

# 597.122. Symlink escape

Sandboxed storage phải xử lý symlink/reparse-point escape.

---

# 597.123. Hard links

Hard links có thể khiến path-based assumptions sai; security-sensitive operations phải dùng filesystem identity/handle semantics khi platform hỗ trợ.

---

# 597.124. TOCTOU

Security-sensitive file operations không được dựa vào:

```text check(path)
→ later open(path)
```

nếu backend cung cấp atomic handle-based alternative.

---

# 597.125. Handle-based operation

Preferred pattern:

```text open securely
     ↓
validate handle
     ↓
operate
```

---

# 597.126. Portable mode

Desktop application có thể request:

```text portable_storage
```

---

# 597.127. Portable storage layout

Ví dụ:

```text
application/
 ├── app/
 ├── data/
 ├── cache/
 └── temp/
```

---

# 597.128. Portable mode precedence

Explicit user-selected portable mode overrides default OS locations.

---

# 597.129. Portable safety

Portable mode không được tự động activate chỉ vì executable nằm trên removable drive.

---

# 597.130. Environment selection

Storage root resolution:

```text Explicit override
      ↓
Portable mode
      ↓
Platform application storage
      ↓
Fallback
```

---

# 597.131. Platform adapter

```text
StoragePlatformAdapter {
    resolve_root(category)
    open()
    map()
    watch()
    quota()
}
```

---

# 597.132. Windows mapping

Windows adapter có thể map AppData/LocalAppData/Documents tương ứng nhưng portable API không expose raw names.

---

# 597.133. Linux mapping

Linux adapter có thể follow XDG conventions.

---

# 597.134. macOS mapping

macOS adapter map application/container/user data locations.

---

# 597.135. iOS mapping

iOS adapter map application sandbox containers.

---

# 597.136. Android mapping

Android adapter map app-specific internal/external storage according to platform permission model.

---

# 597.137. WASM mapping

WASM/WASI adapter có thể expose virtual/preopened filesystem.

---

# 597.138. Freestanding

Freestanding target có thể không có StorageManager.

---

# 597.139. Optional storage subsystem

Application không sử dụng storage API thì storage runtime code phải có khả năng bị dead-strip.

---

# 597.140. Storage URI

Canonical logical URI:

```text
axstorage://app/data/config.json
```

---

# 597.141. URI ≠ OS path

URI chỉ là logical addressing; adapter resolve thành platform storage handle.

---

# 597.142. Resource vs storage URI

```text
axres://...       immutable/distributed resource
axstorage://...   mutable application storage
```

---

# 597.143. Storage stream

```text
StorageStream
```

có cùng semantics cơ bản với resource stream `596`.

---

# 597.144. Storage and async

Async storage operations integrate `424`, `471`, `474`.

---

# 597.145. Cancellation

Cancelled write phải expose whether any bytes may already have been persisted.

---

# 597.146. No false rollback

Cancellation không đồng nghĩa rollback.

---

# 597.147. Atomic API

Các API mang chữ `atomic` chỉ được sử dụng khi backend contract đảm bảo atomicity.

---

# 597.148. Rename semantics

Atomic rename/replacement semantics phải document theo platform.

---

# 597.149. Cross-filesystem move

Cross-filesystem move không được giả định atomic.

---

# 597.150. Copy fallback

Runtime có thể fallback sang copy+replace nhưng phải expose weaker semantics.

---

# 597.151. Storage transaction capability

```text
StorageCapabilities {
    atomic_replace
    durable_flush
    file_lock
    watch
    mmap
    transactions
}
```

---

# 597.152. Capability discovery

Application có thể query capabilities trước khi chọn strategy.

---

# 597.153. No fake portability

Nếu capability không tồn tại, API trả `Unsupported`, không mô phỏng sai semantics.

---

# 597.154. File permissions metadata

Portable metadata chỉ expose những semantics common.

---

# 597.155. Native permissions

Unix mode bits/Windows ACL có thể được platform API expose riêng.

---

# 597.156. Symbolic links

Portable API có thể expose symlink operations nếu backend hỗ trợ.

---

# 597.157. Symlink policy

Application package/storage sandbox có thể cấm symlink.

---

# 597.158. Directory deletion

Delete directory phải distinguish:

```text Empty
Recursive
```

---

# 597.159. Recursive deletion

Recursive deletion phải explicit, không mặc định.

---

# 597.160. Safe recursive delete

Runtime phải reject root/ancestor deletion nếu path thuộc protected application roots.

---

# 597.161. Storage root protection

Application không thể delete logical root thông qua ordinary child APIs.

---

# 597.162. Filename encoding

Axiom storage filenames là UTF-8 logical names.

---

# 597.163. Platform filename conversion

Adapter xử lý native encoding/Unicode limitations.

---

# 597.164. Invalid filename

Invalid native filename phải trả error, không silently rewrite.

---

# 597.165. Case sensitivity

Application không được giả định tất cả filesystems case-sensitive.

---

# 597.166. Case collision

Package/application tooling phải detect case-colliding paths khi target filesystem không phân biệt case.

---

# 597.167. Filename normalization

Runtime phải giữ canonicalization policy rõ ràng để tránh duplicate logical names.

---

# 597.168. Maximum path length

Path-length limits là backend capability, không hardcode một universal value.

---

# 597.169. Large files

File size API phải sử dụng 64-bit-or-greater representation.

---

# 597.170. Sparse files

Sparse file capability có thể được exposed.

---

# 597.171. Storage allocation

Có thể query physical allocation khi platform hỗ trợ.

---

# 597.172. Preallocation

```text
file.preallocate(size)
```

giúp giảm fragmentation và allocation latency.

---

# 597.173. Storage fragmentation

Axiom không giả định filesystem chống fragmentation; application có thể dùng sequential/preallocation strategies.

---

# 597.174. Temp + atomic update

Compiler/build tools có thể dùng storage primitives để tạo artifact transaction an toàn.

---

# 597.175. Build integration

`487/568` build system có thể đặt cache/artifacts trong Cache hoặc dedicated build storage.

---

# 597.176. Package integration

`591/593` package/deployment layer có thể sử dụng StorageManager để staging.

---

# 597.177. Runtime integration

`594` process supervisor có thể lưu crash/recovery state trong AppData.

---

# 597.178. Logging integration

`475` logs có thể có dedicated application storage category.

---

# 597.179. Crash dumps

`589` crash dumps có thể được lưu trong dedicated diagnostics storage.

---

# 597.180. Quota-aware crash dump

Crash subsystem phải tôn trọng storage quota.

---

# 597.181. Resource cache integration

`596` resource decoded cache có thể sử dụng `597.Cache`.

---

# 597.182. AI cache integration

AI model/runtime cache `503–539` có thể sử dụng content-addressed storage.

---

# 597.183. Storage pressure and AI

Large model cache phải được coi là rebuildable nếu canonical model artifact vẫn tồn tại.

---

# 597.184. User data privacy

Application storage không mặc định được upload hoặc telemetry.

---

# 597.185. Telemetry boundary

Storage paths/content không được đưa vào telemetry trừ khi explicitly permitted/redacted.

---

# 597.186. Secrets

Credentials/tokens nên dùng secure credential/keychain subsystem thay vì ordinary AppData.

---

# 597.187. Encryption

Filesystem storage encryption là platform/security concern; Axiom không giả định filesystem encryption.

---

# 597.188. Application-level encryption

Application có thể mã hóa file thông qua crypto APIs.

---

# 597.189. Encryption metadata

Encrypted data phải có explicit format/version.

---

# 597.190. Backup confidentiality

Backup policy không được mặc định làm plaintext sensitive data visible.

---

# 597.191. Storage lifecycle

```text
Application Install
       ↓
Initialize Storage
       ↓
Running
       ↓
Update
       ↓
Migration
       ↓
Running
       ↓
Uninstall
```

---

# 597.192. Uninstall policy

Package `593` có thể khai báo:

```text
PreserveUserData
RemoveAppData
RemoveCache
```

---

# 597.193. User-data preservation

Uninstall không được mặc định xóa user documents.

---

# 597.194. Cache uninstall

Cache có thể được xóa khi uninstall.

---

# 597.195. Reinstall

Reinstall có thể reuse preserved AppData nếu schema tương thích.

---

# 597.196. Application identity

Storage roots phải dựa trên stable application identity, không dựa vào executable filename.

---

# 597.197. Version isolation

Application versions có thể share data root hoặc versioned data root theo manifest policy.

---

# 597.198. Side-by-side versions

Side-by-side versions phải có migration/ownership policy rõ ràng.

---

# 597.199. Downgrade

Downgrade sau migration có thể không safe.

Manifest/tooling phải có downgrade policy.

---

# 597.200. Storage schema compatibility

Schema compatibility phải được kiểm tra trước khi mở persistent data.

---

# 597.201. Multi-process application

Các process cùng application identity có thể share AppData.

---

# 597.202. Process synchronization

Concurrent access phải dùng file locks/database transactions/IPC theo data semantics.

---

# 597.203. No implicit global lock

StorageManager không khóa toàn bộ AppData cho mọi process.

---

# 597.204. Service applications

Services có thể có dedicated service data root.

---

# 597.205. Worker process

Worker process có thể inherit storage capabilities từ supervisor `594`.

---

# 597.206. Capability delegation

Supervisor có thể cấp restricted storage capability cho child process.

---

# 597.207. Least privilege

Child process chỉ nhận storage roots cần thiết.

---

# 597.208. Temporary child storage

Supervisor có thể cấp isolated temporary directory.

---

# 597.209. Cleanup on child exit

Temporary child storage có thể cleanup theo lifecycle policy.

---

# 597.210. Storage API errors

Base error taxonomy:

```text
NotFound
AlreadyExists
PermissionDenied
InvalidPath
NotDirectory
IsDirectory
Busy
Locked
ReadOnly
NoSpace
QuotaExceeded
Unsupported
Corrupt
IOError
Cancelled
TimedOut
```

---

# 597.211. Error preservation

Platform-specific error code có thể được giữ trong diagnostic payload.

---

# 597.212. Retry classification

Error có metadata:

```text
Retryable
NonRetryable
Unknown
```

---

# 597.213. Retry policy

Runtime không tự động retry destructive operations.

---

# 597.214. Exponential backoff

Transient operations có thể dùng backoff qua scheduler/time subsystem.

---

# 597.215. Idempotency

Storage API phải document operation nào idempotent.

---

# 597.216. Storage metrics

Optional metrics:

```text bytes_read
bytes_written
open_count
cache_hits
cache_misses
errors
latency
```

---

# 597.217. Storage tracing

Storage operations có correlation ID khi tracing enabled.

---

# 597.218. Sensitive path redaction

Diagnostics có thể redact user-specific paths.

---

# 597.219. AI-readable storage state

AI tooling có thể query:

```text
StorageRoot
Usage
Quota
Capabilities
OpenHandles
RecentErrors
```

nếu user/tool permission cho phép.

---

# 597.220. AI safety

AI agent không được tự ý:

```text delete user data
overwrite documents
grant storage permission
change backup policy
```

chỉ vì có semantic access.

---

# 597.221. AI proposed mutation

AI storage mutation phải có:

```text Plan
AffectedPaths
ExpectedChanges
Validation
Apply
```

---

# 597.222. Destructive confirmation

IDE/agent layer có thể yêu cầu explicit confirmation cho destructive operations.

---

# 597.223. Deterministic tests

Test harness phải hỗ trợ virtual storage backend.

---

# 597.224. In-memory storage backend

```text
MemoryStorageProvider
```

cho phép test mà không touching filesystem.

---

# 597.225. Fault injection

Test backend có thể inject:

```text NoSpace
PermissionDenied
Corruption
PartialWrite
Crash
WatchOverflow
```

---

# 597.226. Crash testing

Atomic replacement và migration phải được test với simulated process crash.

---

# 597.227. Property testing

Path normalization, sandbox confinement và transaction semantics phải fuzz/property-test.

---

# 597.228. Cross-platform conformance

Mỗi platform adapter phải pass common storage contract tests.

---

# 597.229. Platform-specific extensions

Extensions không được phá portable semantics.

---

# 597.230. Minimal ABI

Core storage ABI nên dựa trên:

```text
StorageHandle
FileHandle
DirectoryHandle
Stream
MappedRegion
StorageError
```

---

# 597.231. No hidden runtime daemon

Ordinary file operations không yêu cầu background Axiom storage daemon.

---

# 597.232. Direct OS mapping

Desktop native target có thể lower Storage APIs trực tiếp xuống OS syscalls/APIs.

---

# 597.233. Performance

Hot-path file reads phải tránh unnecessary:

```text path conversion
allocation
copy
locking
```

---

# 597.234. Zero-copy reads

Mapped or OS-buffer-backed reads có thể expose immutable byte views.

---

# 597.235. Buffer ownership

Caller phải biết buffer ownership/lifetime.

---

# 597.236. Large sequential reads

Runtime có thể expose vectored/batched I/O.

---

# 597.237. Scatter/gather

```text
readv()
writev()
```

là optional high-performance primitive.

---

# 597.238. Direct asynchronous I/O

Platform-specific adapters có thể sử dụng IOCP, io_uring, kqueue hoặc tương đương nhưng không expose chúng trong portable core.

---

# 597.239. Thread pool avoidance

Native async file APIs không được bắt buộc giả lập bằng blocking thread pool.

---

# 597.240. WASM async

WASM backend phải map storage operations theo host capability.

---

# 597.241. Browser sandbox

Browser/WASM environment chỉ có virtual/user-granted storage.

---

# 597.242. Browser persistence

IndexedDB-like backend có thể implement storage provider nhưng không trở thành core language primitive.

---

# 597.243. Freestanding storage

Embedded/freestanding applications có thể inject custom StorageProvider.

---

# 597.244. Custom provider

```text
StorageProvider {
    open
    create
    remove
    enumerate
    metadata
    map?
    watch?
}
```

---

# 597.245. Provider isolation

Provider phải có explicit lifetime và capability scope.

---

# 597.246. Provider error model

Provider errors phải map về Axiom StorageError + optional native diagnostic.

---

# 597.247. Provider determinism

Virtual/test provider phải deterministic nếu test yêu cầu deterministic behavior.

---

# 597.248. Storage abstraction layering

```text
Language
   ↓
Std Storage API
   ↓
Storage Runtime
   ↓
Platform Provider
   ↓
OS / Virtual FS
```

---

# 597.249. Core independence

Core language không phụ thuộc filesystem.

---

# 597.250. Final hard invariant

### Invariant 1 — resource separation

> `596` immutable resources và `597` mutable storage là hai abstraction khác nhau.

### Invariant 2 — logical paths

> Portable Axiom APIs không phụ thuộc trực tiếp vào OS-specific path conventions.

### Invariant 3 — sandbox

> Storage capability là security boundary; path string không phải security boundary.

### Invariant 4 — root confinement

> Ordinary storage APIs không được escape khỏi authorized root.

### Invariant 5 — no false atomicity

> API chỉ guarantee atomicity/durability khi backend thực sự cung cấp guarantee tương ứng.

### Invariant 6 — crash-safe writes

> Axiom phải cung cấp primitive đủ để application thực hiện atomic replacement và crash-safe update.

### Invariant 7 — no false durability

> `write()` không đồng nghĩa với durable persistence.

### Invariant 8 — capability honesty

> Unsupported filesystem capabilities phải trả `Unsupported`, không silently mô phỏng semantics khác.

### Invariant 9 — user-data preservation

> Uninstall/update không được mặc định phá hủy user documents.

### Invariant 10 — cache separation

> Cache có thể bị xóa và không được coi là canonical user data.

### Invariant 11 — migration safety

> Migration failure không được làm mất dữ liệu nguồn.

### Invariant 12 — conflict safety

> External document modifications không được âm thầm overwrite user changes.

### Invariant 13 — Unicode

> Logical filenames và storage identifiers phải hỗ trợ UTF-8.

### Invariant 14 — large-file correctness

> File sizes/offsets phải hỗ trợ 64-bit-or-greater.

### Invariant 15 — lifetime

> File, stream, mapping và transaction handles tuân ownership/lifetime semantics `423`.

### Invariant 16 — async correctness

> Cancellation không được giả vờ rollback những writes đã thực sự xảy ra.

### Invariant 17 — cross-platform

> Storage API giữ cùng semantic contract trên Windows/Linux/macOS/iOS/Android/WASM, trong giới hạn capability thực tế của backend.

### Invariant 18 — no mandatory daemon

> Native file operations không phụ thuộc vào một storage daemon trung gian.

### Invariant 19 — performance

> Storage hot paths phải cho phép zero-copy, mapping, vectored I/O và native asynchronous I/O khi backend hỗ trợ.

### Invariant 20 — AI safety

> AI semantic access không mặc định cấp quyền sửa/xóa user data.

### Invariant 21 — provenance

> Data migrations, generated data và application storage mutations phải có thể truy nguyên khi diagnostic tooling yêu cầu.

### Invariant 22 — minimal runtime

> Storage subsystem không sử dụng phải có khả năng bị loại khỏi final native artifact.

---

# 597 — LOCKED

Axiom hiện có ranh giới dữ liệu rất rõ:

```text
                 AXIOM DATA MODEL

     ┌────────────────────────────────────┐
     │             Application            │
     └──────────────────┬─────────────────┘
                        │
             ┌──────────┴──────────┐
             ▼                     ▼
      596 RESOURCE            597 STORAGE
       immutable                mutable
             │                     │
       ┌─────┼─────┐        ┌──────┼──────┐
       ▼     ▼     ▼        ▼      ▼      ▼
    Bundle Embedded Asset  AppData Cache Documents
                              │
                              ▼
                         Platform FS
```

Điều này cũng tránh một lỗi kiến trúc phổ biến: **không dùng cùng một abstraction cho asset đóng gói và dữ liệu người dùng**, vì hai loại dữ liệu có lifecycle, integrity, permission, backup và mutation semantics hoàn toàn khác nhau.

---

# NEXT — BOOTSTRAP-598

## NATIVE APPLICATION IPC & INTER-PROCESS DATA MODEL 6.0
### LOCAL IPC, NAMED CHANNELS, SOCKETS, SHARED MEMORY, HANDLE TRANSFER, RPC, MESSAGE SERIALIZATION, SERVICE DISCOVERY, SECURITY CAPABILITIES, PROCESS SUPERVISOR INTEGRATION & ZERO-COPY INTER-PROCESS COMMUNICATION

```text
                         Application
                              │
                 ┌────────────┴────────────┐
                 ▼                         ▼
             Process A                 Process B
                 │                         │
        ┌────────┼────────┐       ┌────────┼────────┐
        ▼        ▼        ▼       ▼        ▼        ▼
      Pipe    Socket   Shared   Pipe     RPC     Shared
                        Memory             │
        └────────┬────────┘       └────────┬───────┘
                 └────────────┬────────────┘
                              ▼
                         IPC Layer
                              │
                 ┌────────────┼────────────┐
                 ▼            ▼            ▼
              Local         Remote      Sandbox
               IPC           IPC        Boundary
```

`598` sẽ hợp nhất các primitive đã có ở `454`, `472`, `490`, `594` thành **application-level IPC contract**, đặc biệt tập trung vào **shared memory + handle transfer + zero-copy IPC + capability-based endpoint security**, nhưng không biến RPC hay serialization thành bắt buộc đối với các chương trình native đơn giản.