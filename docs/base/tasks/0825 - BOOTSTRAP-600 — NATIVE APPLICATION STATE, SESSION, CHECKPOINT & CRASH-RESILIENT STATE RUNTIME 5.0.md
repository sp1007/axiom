# BOOTSTRAP-600 — NATIVE APPLICATION STATE, SESSION, CHECKPOINT & CRASH-RESILIENT STATE RUNTIME 5.0

**Status:** SPECIFICATION  
**Phase:** Bootstrap / Native Runtime Architecture  
**Task ID:** `BOOTSTRAP-600`  
**Depends on:** Previous BOOTSTRAP tasks through `BOOTSTRAP-599`  
**Priority:** Critical  
**Target:** Axiom Core / Native Runtime / Application Infrastructure

---

## 600.0. Mục tiêu

Axiom phải cung cấp một **Native Application State Runtime** thống nhất để ứng dụng có thể:

- quản lý trạng thái runtime;
- quản lý application session;
- lưu/khôi phục state;
- tạo checkpoint;
- khôi phục sau crash;
- khôi phục sau mất điện;
- hỗ trợ undo/redo ở cấp application state;
- hỗ trợ autosave;
- hỗ trợ transactional state update;
- phát hiện state chưa được commit;
- phục hồi state nhất quán sau termination bất thường;
- hỗ trợ ứng dụng desktop, CLI, server, game, editor và long-running process;
- không bắt buộc garbage collector;
- không bắt buộc database;
- không bắt buộc filesystem abstraction của bên thứ ba;
- không biến state runtime thành một framework nặng.

Thiết kế phải là **native runtime primitive**, không phải một thư viện application-level bắt buộc.

Mục tiêu chính:

> **Một ứng dụng Axiom có thể bị crash tại bất kỳ thời điểm nào nhưng lần khởi động tiếp theo vẫn có khả năng xác định chính xác state nào đã được commit, state nào chưa hoàn tất và phục hồi về một checkpoint nhất quán.**

---

# 600.1. Nguyên tắc thiết kế

### P1 — State phải explicit

Axiom không tự động biến mọi biến trong chương trình thành persistent state.

Developer phải khai báo:

```axiom
state AppState {
    document: Document
    settings: Settings
    cursor: Cursor
}
```

hoặc đăng ký state bằng runtime API.

---

### P2 — Runtime state và persistent state là hai khái niệm khác nhau

```text
Runtime State
    │
    ├── transient
    ├── session
    └── persistent
```

Không được giả định:

```text
variable == persistent state
```

---

### P3 — Không GC

State runtime không được phụ thuộc garbage collector.

Lifecycle phải dựa trên:

- ownership;
- deterministic destruction;
- explicit resource lifetime;
- transaction boundaries;
- checkpoint boundaries.

---

### P4 — Không yêu cầu borrow checker

Checkpoint/state system không được yêu cầu một borrow-checking model phức tạp.

Compiler chỉ cần đảm bảo các invariant cần thiết liên quan đến:

- state ownership;
- transaction;
- serialization;
- mutation isolation;
- commit ordering.

---

### P5 — Crash safety là primitive

Crash recovery không phải tính năng phụ của application framework.

Runtime phải có primitive:

```axiom
checkpoint(...)
commit(...)
recover(...)
```

---

### P6 — Không database bắt buộc

Native state runtime phải hoạt động chỉ với:

```text
Axiom runtime
+
OS filesystem
+
native memory
```

Database có thể được xây dựng phía trên runtime sau này.

---

# 600.2. Các loại state

Axiom định nghĩa 4 cấp state:

```text
TRANSIENT
SESSION
CHECKPOINT
PERSISTENT
```

---

## 600.2.1. Transient State

Chỉ tồn tại trong process hiện tại.

```axiom
transient frame_buffer: Buffer
```

Không được checkpoint.

---

## 600.2.2. Session State

Tồn tại trong một application session.

```axiom
session {
    active_document
    selected_object
    window_layout
}
```

Session state có thể được autosave nhưng không nhất thiết phải tồn tại lâu dài.

---

## 600.2.3. Checkpoint State

State đã được snapshot tại một điểm nhất quán.

```text
checkpoint #42
```

Có thể dùng để:

- recovery;
- undo;
- restore;
- crash recovery;
- version history.

---

## 600.2.4. Persistent State

State được xác định là dữ liệu ứng dụng lâu dài.

```axiom
persistent state AppState {
    documents: DocumentStore
    settings: Settings
}
```

---

# 600.3. Application State

Axiom cung cấp declaration:

```axiom
state AppState {
    documents: Documents
    settings: Settings
    workspace: Workspace
}
```

Compiler tạo metadata:

```text
StateDescriptor
StateFieldDescriptor[]
SerializationDescriptor
VersionDescriptor
```

---

# 600.4. State Identity

Mỗi state object persistent phải có identity ổn định.

```axiom
state Document {
    id: UUID
    title: String
    content: String
}
```

`id` không được phụ thuộc memory address.

Không sử dụng:

```text
pointer address
heap address
object location
```

làm persistent identity.

---

# 600.5. State Graph

State không nhất thiết là một object phẳng.

Ví dụ:

```text
AppState
 ├── Workspace
 │    ├── Project
 │    └── Project
 ├── Documents
 │    ├── Document
 │    └── Document
 └── Settings
```

Runtime coi persistent state là một **state graph**.

Các node có identity.

Các edge có thể biểu diễn:

```text
owned
contained
referenced
indexed
```

---

# 600.6. Persistent Reference

Nếu state A tham chiếu state B:

```axiom
state Project {
    documents: [DocumentId]
}
```

runtime lưu identity:

```text
DocumentId
```

thay vì memory pointer.

Điều này cho phép process restart mà không làm mất reference.

---

# 600.7. State Transaction

Mọi thay đổi persistent state có thể được thực hiện trong transaction:

```axiom
state.transaction {
    app.settings.theme = .dark
    app.settings.font_size = 14
}
```

Transaction có hai trạng thái:

```text
OPEN
COMMITTED
```

và khi cần:

```text
ABORTED
```

---

# 600.8. Atomic Commit

Transaction phải tuân thủ:

```text
all changes committed
OR
no changes committed
```

Không được tạo persistent state nửa transaction.

Ví dụ:

```text
A = old
B = old

transaction:
    A = new
    B = new

crash
```

Sau recovery:

```text
A = old
B = old
```

hoặc:

```text
A = new
B = new
```

nhưng không:

```text
A = new
B = old
```

nếu A và B thuộc cùng transaction.

---

# 600.9. Commit Protocol

Runtime sử dụng journal/checkpoint protocol.

Conceptual flow:

```text
BEGIN
  ↓
MUTATE
  ↓
WRITE JOURNAL
  ↓
SYNC
  ↓
COMMIT MARKER
  ↓
SYNC
  ↓
CHECKPOINT COMPLETE
```

Crash trước commit marker:

```text
ROLLBACK
```

Crash sau commit marker:

```text
RECOVER
```

---

# 600.10. Write-Ahead Journal

Runtime phải hỗ trợ native journal.

Ví dụ:

```text
state/
    manifest
    journal
    checkpoints/
```

Journal entry:

```text
TransactionId
Sequence
StateId
Operation
Payload
Checksum
```

---

# 600.11. Journal Entry

Logical format:

```text
JournalEntry {
    tx_id
    sequence
    state_id
    operation
    payload
    checksum
}
```

`sequence` tăng đơn điệu trong phạm vi state store.

---

# 600.12. Journal Integrity

Mỗi journal record phải có integrity verification.

Tối thiểu:

```text
length
checksum
sequence
```

Runtime có thể phát hiện:

- truncated record;
- corrupted record;
- incomplete write;
- invalid sequence.

---

# 600.13. Crash Recovery

Khi application khởi động:

```axiom
let app = Application.open("myapp")
```

runtime:

```text
1. đọc manifest
2. xác định checkpoint cuối
3. đọc journal
4. validate records
5. xác định transaction hoàn tất
6. replay transaction hợp lệ
7. bỏ transaction chưa commit
8. tạo recovered state
```

---

# 600.14. Recovery Result

Recovery không chỉ trả về boolean.

```axiom
RecoveryResult {
    status
    checkpoint
    recovered_transactions
    discarded_transactions
    corruption
}
```

Ví dụ:

```axiom
match app.recover() {
    .clean => ...
    .recovered => ...
    .partial => ...
    .corrupt => ...
}
```

---

# 600.15. Recovery Status

Core enum:

```axiom
enum RecoveryStatus {
    Clean
    Recovered
    RolledBack
    Partial
    Corrupt
}
```

`Partial` chỉ được phép xuất hiện khi runtime xác định rằng state không thể phục hồi hoàn toàn theo policy đã khai báo.

---

# 600.16. Checkpoint

API:

```axiom
app.checkpoint()
```

hoặc:

```axiom
app.checkpoint("before-import")
```

Checkpoint có metadata:

```text
Checkpoint {
    id
    sequence
    timestamp
    state_version
    label
    checksum
}
```

---

# 600.17. Checkpoint ID

Checkpoint ID phải ổn định.

Ví dụ:

```text
checkpoint: 0000000000000042
```

Không sử dụng timestamp làm identity duy nhất.

---

# 600.18. Checkpoint Version

Mỗi checkpoint phải có:

```text
format_version
schema_version
application_version
```

Ví dụ:

```text
format = 5
schema = 3
application = 1.7
```

---

# 600.19. Schema Evolution

Application mới có thể mở state cũ.

Ví dụ:

```text
State v1
    ↓ migrate
State v2
```

Developer có thể định nghĩa:

```axiom
migrate State from 1 to 2 {
    ...
}
```

Migration phải deterministic.

---

# 600.20. Migration Safety

Migration không được ghi đè checkpoint cũ trực tiếp.

Flow:

```text
checkpoint v1
      ↓
read
      ↓
migrate
      ↓
validate
      ↓
checkpoint v2
```

Nếu migration crash:

```text
v1 remains recoverable
```

---

# 600.21. Autosave

Runtime cung cấp:

```axiom
app.autosave.enable()
```

hoặc:

```axiom
app.autosave(interval: 5s)
```

Autosave không nhất thiết tạo full snapshot mỗi lần.

Runtime có thể dùng:

```text
delta journal
+
periodic checkpoint
```

---

# 600.22. Delta State

Nếu state lớn:

```text
10 GB application state
```

không được bắt buộc ghi lại toàn bộ 10 GB sau mỗi mutation.

Runtime hỗ trợ:

```text
delta
patch
journal
checkpoint
```

---

# 600.23. Full Checkpoint

Runtime định kỳ tạo full checkpoint để giới hạn journal replay.

Ví dụ:

```text
checkpoint 100
journal 101..130

checkpoint 130
```

Startup chỉ cần replay:

```text
101..130
```

thay vì toàn bộ lịch sử.

---

# 600.24. Checkpoint Compaction

Runtime được phép compact:

```text
checkpoint 1
checkpoint 2
checkpoint 3
...
checkpoint 100
```

thành:

```text
checkpoint 100
```

nếu application không yêu cầu historical checkpoints.

---

# 600.25. Historical Checkpoints

Application có thể yêu cầu giữ lịch sử:

```axiom
checkpoint.policy {
    keep_last: 20
}
```

hoặc:

```axiom
keep_all: true
```

Runtime không tự động xóa checkpoint mà application đánh dấu protected.

---

# 600.26. Undo / Redo

Checkpoint infrastructure phải có khả năng hỗ trợ undo/redo.

```axiom
app.undo()
app.redo()
```

Undo không nhất thiết phải là snapshot full.

Có thể dùng:

```text
inverse operation
```

hoặc:

```text
state delta
```

---

# 600.27. Undo Boundary

Developer có thể xác định một transaction là một undo unit:

```axiom
app.edit {
    document.insert(...)
    document.insert(...)
    document.delete(...)
}
```

Một block có thể xuất hiện như:

```text
Undo #42
```

thay vì 3 thao tác độc lập.

---

# 600.28. Redo Invalidation

Khi user thực hiện mutation mới sau undo:

```text
A
B
C
↓
undo
A
B
↓
new mutation
A
B
D
```

Redo của C phải bị invalidated.

---

# 600.29. Session

Session object:

```axiom
session = app.session()
```

Session có:

```text
session_id
start_time
last_activity
application_version
state_version
```

---

# 600.30. Session Persistence

Session state có thể được lưu:

```axiom
session.save()
```

và phục hồi:

```axiom
session.restore()
```

Ví dụ editor:

```text
open documents
cursor positions
scroll positions
window layout
selected tabs
```

---

# 600.31. Last Session

Application có thể yêu cầu:

```axiom
app.restore_last_session()
```

Runtime phải phân biệt:

```text
last clean session
last crashed session
current session
```

---

# 600.32. Crash Marker

Khi application start:

```text
session = STARTING
```

Runtime tạo crash marker.

Khi shutdown sạch:

```text
session = CLEAN
```

Nếu process chết bất thường:

```text
marker remains
```

Startup tiếp theo:

```text
previous session = CRASHED
```

---

# 600.33. Clean Shutdown

API:

```axiom
app.shutdown()
```

phải:

```text
flush journal
commit pending transaction
write clean marker
sync metadata
close state store
```

---

# 600.34. Hard Crash

Các trường hợp:

```text
process crash
OS termination
power loss
kernel crash
machine reset
```

được coi là unclean termination.

Recovery không được phụ thuộc vào destructor của application.

---

# 600.35. Memory State vs Durable State

Runtime không được tuyên bố transaction committed chỉ vì:

```text
memory mutation completed
```

Commit chỉ xảy ra sau khi durability protocol đạt điều kiện tương ứng.

---

# 600.36. Durability Levels

Axiom định nghĩa:

```axiom
enum Durability {
    Memory
    Buffered
    Durable
    Strict
}
```

### Memory

Chỉ RAM.

### Buffered

OS/filesystem buffering có thể chưa flush.

### Durable

Runtime yêu cầu filesystem durability thích hợp.

### Strict

Commit chỉ hoàn thành sau durability barrier mạnh nhất mà backend native hỗ trợ.

---

# 600.37. Performance Mode

Application có thể chọn:

```axiom
state.config {
    durability: .Buffered
}
```

hoặc:

```axiom
durability: .Strict
```

Default phải ưu tiên **an toàn state**, nhưng runtime không được ép strict durability cho mọi transient operation.

---

# 600.38. State Isolation

Một transaction đang chạy:

```axiom
transaction {
    ...
}
```

không được để transaction khác nhìn thấy persistent state trung gian nếu isolation policy yêu cầu atomic visibility.

---

# 600.39. Transaction Visibility

Conceptual model:

```text
Committed State
       │
       ├── Transaction A (private)
       │
       └── Transaction B (private)
```

Sau commit:

```text
Committed State'
```

---

# 600.40. Concurrent State Mutation

Runtime phải hỗ trợ nhiều thread cùng truy cập state nhưng không biến toàn bộ application thành một global lock.

State có thể partition:

```text
AppState
 ├── DocumentStore
 ├── Settings
 ├── Cache
 └── Session
```

Mỗi region có synchronization riêng.

---

# 600.41. State Region

```axiom
state region documents {
    ...
}
```

Cho phép runtime quản lý:

```text
lock
transaction
journal
checkpoint
```

ở cấp region.

---

# 600.42. Lock-free Compatibility

State runtime không yêu cầu lock-free implementation, nhưng architecture phải cho phép implementation lock-free/optimistic trong tương lai.

---

# 600.43. Immutable Checkpoint

Sau khi checkpoint được commit:

```text
checkpoint == immutable
```

Không sửa checkpoint tại chỗ.

Muốn thay đổi:

```text
checkpoint N
    ↓
new state
    ↓
checkpoint N+1
```

---

# 600.44. Atomic Manifest

Manifest phải có khả năng atomic replacement.

Runtime không được dựa vào:

```text
overwrite manifest directly
```

nếu thao tác đó có thể tạo manifest nửa ghi.

---

# 600.45. Double Manifest / Generation

Một implementation có thể dùng:

```text
manifest.A
manifest.B
```

với generation:

```text
generation = 42
```

Runtime chọn manifest hợp lệ mới nhất.

Đây là implementation detail, không phải API bắt buộc.

---

# 600.46. Corruption Detection

Runtime phải phát hiện tối thiểu:

```text
invalid magic
invalid version
invalid length
invalid checksum
invalid sequence
invalid transaction state
missing referenced state
```

---

# 600.47. Corruption Policy

Application có thể chọn:

```axiom
recovery.policy {
    on_corruption: .Fail
}
```

hoặc:

```axiom
on_corruption: .UseLastValidCheckpoint
```

hoặc:

```axiom
on_corruption: .ReportAndContinue
```

`ReportAndContinue` chỉ được phép nếu state còn thỏa mãn invariant.

---

# 600.48. No Silent Data Loss

Runtime không được âm thầm bỏ state mà không báo cáo.

Nếu journal bị loại bỏ:

```text
discarded_transactions++
```

phải được phản ánh trong `RecoveryResult`.

---

# 600.49. Checkpoint Validation

Developer có thể định nghĩa invariant:

```axiom
validate AppState {
    assert documents.count >= 0
    assert settings.font_size > 0
}
```

Checkpoint chỉ được commit nếu validation thành công.

---

# 600.50. State Invariant

Invariant là compile/runtime validation rule.

Không được coi assertion debug-only nếu nó được đánh dấu:

```axiom
persistent invariant
```

---

# 600.51. Transaction Validation

Flow:

```text
BEGIN
 ↓
MUTATE
 ↓
VALIDATE
 ↓
SERIALIZE
 ↓
JOURNAL
 ↓
DURABILITY
 ↓
COMMIT
```

Validation fail:

```text
ABORT
```

---

# 600.52. State Serialization

Compiler phải sinh metadata serialization từ type system.

Ví dụ:

```axiom
state Settings {
    language: String
    font_size: i32
}
```

Compiler biết layout logical:

```text
field 0 = language
field 1 = font_size
```

Không serialize raw memory layout mặc định.

---

# 600.53. Không Persist Raw Pointer

Không được:

```text
serialize pointer bits
```

Persistent state chỉ được chứa:

```text
value
stable identity
persistent reference
```

---

# 600.54. Native Binary Format

Default state format là binary native format.

Không dùng JSON làm persistent core format.

JSON/XML/TOML/YAML chỉ là adapter layer.

---

# 600.55. Compactness

Persistent representation phải ưu tiên:

```text
small size
fast read
fast write
low allocation
```

---

# 600.56. Zero-Copy Read

Runtime nên cho phép state fields có thể được map/read trực tiếp từ checkpoint khi semantics cho phép.

Ví dụ:

```axiom let data = checkpoint.map(DocumentBlob)
```

Không bắt buộc deserialize toàn bộ application state.

---

# 600.57. Lazy State Loading

State lớn có thể lazy-load:

```text
AppState
 ├── Settings        loaded
 ├── Workspace       loaded
 └── Documents       lazy
```

---

# 600.58. Memory Mapping

Backend có thể dùng OS memory mapping.

Nhưng:

> memory-mapped persistent storage không được đồng nghĩa với mutable memory trực tiếp.

Mutation vẫn phải đi qua state transaction protocol nếu state yêu cầu crash consistency.

---

# 600.59. State Store

Native API:

```axiom store = StateStore.open(path)
```

Capabilities:

```text
begin
commit
rollback
checkpoint
recover
compact
close
```

---

# 600.60. Application Runtime

Application có thể có một state store mặc định:

```axiom app.state
```

Ví dụ:

```axiom app.state.transaction {
    app.state.settings.theme = .dark
}
```

---

# 600.61. Named State Stores

Ứng dụng lớn có thể có nhiều store:

```axiom store "main"
store "cache"
store "workspace"
```

Trong đó:

```text
main      = durable
cache     = disposable
workspace = session/persistent
```

---

# 600.62. Cache State

Cache không được nằm trong authoritative persistent state.

```axiom cache {
    thumbnails
    compiled_assets
}
```

Nếu cache mất sau crash:

```text
application remains valid
```

---

# 600.63. State Classification

Mỗi field có thể khai báo:

```axiom
transient
session
persistent
derived
```

Ví dụ:

```axiom state Document {
    persistent content: String
    persistent title: String

    transient render_cache: RenderCache
    derived word_count: i64
}
```

---

# 600.64. Derived State

Derived state không cần persistence nếu có thể tái tạo deterministic.

```axiom
derived word_count = count_words(content)
```

Sau recovery:

```text
content recovered
↓
word_count recomputed
```

---

# 600.65. State Dependency Graph

Runtime/compiler phải biết:

```text
derived state
    depends on
persistent state
```

để tránh serialize derived data không cần thiết.

---

# 600.66. Session Recovery

Sau crash:

```text
persistent state
+
last valid session checkpoint
```

được sử dụng để phục hồi UI/application context.

---

# 600.67. Recovery Hook

Application có thể đăng ký:

```axiom on recover {
    ...
}
```

Hook chạy sau khi state đã trở nên internally consistent.

Không chạy hook giữa journal replay.

---

# 600.68. Recovery Ordering

Thứ tự:

```text
storage recovery
→ state reconstruction
→ schema migration
→ invariant validation
→ session reconstruction
→ application recovery hook
→ application ready
```

---

# 600.69. Crash Recovery Event

Application nhận:

```axiom event RecoveryCompleted {
    previous_session
    checkpoint
    transactions_replayed
}
```

---

# 600.70. Checkpoint Event

```axiom event CheckpointCreated {
    id
    state_version
    size
}
```

---

# 600.71. Commit Event

```axiom event StateCommitted {
    transaction_id
    sequence
}
```

---

# 600.72. Rollback Event

```axiom event StateRolledBack {
    transaction_id
    reason
}
```

---

# 600.73. Transaction Failure

Failure phải có nguyên nhân:

```axiom enum StateError {
    InvalidState
    SerializationFailed
    ValidationFailed
    StorageFailed
    CorruptJournal
    VersionMismatch
    MigrationFailed
    Conflict
    RecoveryFailed
}
```

---

# 600.74. Error Philosophy

State error là typed error.

Không dùng:

```text
null
false
magic integer
```

để biểu thị commit failure.

---

# 600.75. API mẫu

```axiom
let store = StateStore.open("app.state")?

let tx = store.begin()?

tx.set(app.settings.theme, .dark)
tx.set(app.settings.font_size, 14)

tx.validate()?
tx.commit()?

store.checkpoint()?
```

---

# 600.76. Scoped Transaction

Axiom hỗ trợ syntax ngắn:

```axiom
store.transaction {
    state.settings.theme = .dark
    state.settings.font_size = 14
}
```

Runtime tự:

```text
BEGIN
COMMIT
```

hoặc:

```text
ROLLBACK
```

khi block thất bại.

---

# 600.77. Nested Transaction

Nested transaction không tạo durability boundary độc lập.

```axiom transaction {
    ...
    transaction {
        ...
    }
}
```

Inner transaction là logical savepoint.

---

# 600.78. Savepoint

```axiom tx.savepoint()
tx.rollback_to(savepoint)
```

Savepoint không phải checkpoint persistent.

---

# 600.79. Checkpoint vs Savepoint

| Feature | Savepoint | Checkpoint |
|---|---|---|
| Persistent | Không bắt buộc | Có |
| Crash recovery | Không | Có |
| Transaction scope | Có | Không |
| Historical restore | Không | Có |
| Cost | thấp | cao hơn |

---

# 600.80. Crash-Consistent Resource State

Runtime phải cho phép resource application được đánh dấu:

```text
rebuildable
persistent
external
```

Ví dụ:

```text
GPU texture → rebuildable
document → persistent
network socket → external
```

Không serialize resource handle OS trực tiếp.

---

# 600.81. External Resource

Nếu state tham chiếu external resource:

```axiom external asset {
    path
    identity
    fingerprint
}
```

Recovery phải kiểm tra resource.

---

# 600.82. Missing External Resource

Không được coi missing external resource là journal corruption.

Ví dụ:

```text
document.state = valid
image.png = missing
```

Recovery:

```text
state = valid
external resource = unavailable
```

Application xử lý riêng.

---

# 600.83. State Fingerprint

External resource có thể có:

```text
path
size
mtime
hash/fingerprint
```

để phát hiện thay đổi ngoài application.

---

# 600.84. Atomic File Replacement

State runtime cần native primitive:

```axiom file.atomic_replace(...)
```

để phục vụ checkpoint/manifest.

Primitive này thuộc filesystem runtime layer nhưng được State Runtime sử dụng.

---

# 600.85. Directory Commit

Một checkpoint có thể gồm nhiều file.

Runtime phải đảm bảo metadata chỉ advertise checkpoint sau khi toàn bộ required data đã sẵn sàng.

---

# 600.86. Temp State

Checkpoint mới:

```text
checkpoint.tmp
```

Sau khi hoàn tất:

```text
checkpoint.final
```

Không được để application coi `.tmp` là valid checkpoint.

---

# 600.87. Checkpoint Garbage Collection

Tên gọi ở đây chỉ là **storage cleanup**, không phải memory GC.

Runtime có thể xóa checkpoint cũ theo retention policy.

---

# 600.88. Storage Quota

Application có thể giới hạn:

```axiom state.policy {
    max_size: 2GB
}
```

Khi vượt quota:

```text
StateError.StorageLimit
```

không được âm thầm xóa authoritative state.

---

# 600.89. Emergency Checkpoint

API:

```axiom app.emergency_checkpoint()
```

dành cho:

```text
SIGTERM
system shutdown
low battery
application close
```

Không được giả định emergency checkpoint luôn chạy được trong hard crash.

---

# 600.90. Signal Safety

Signal handler không được thực hiện serialization phức tạp trực tiếp.

Flow:

```text
signal
 ↓
set shutdown flag
 ↓
runtime safe point
 ↓
checkpoint
```

---

# 600.91. Runtime Safe Point

Compiler/runtime cung cấp safe points cho:

```text
shutdown
checkpoint
interrupt
cancellation
```

Không phải GC safepoint.

---

# 600.92. Long Transaction

Runtime phải hỗ trợ transaction dài nhưng khuyến nghị application chia thành các transaction nhỏ.

Transaction quá lớn có thể:

```text
tăng journal
tăng recovery time
tăng memory pressure
```

---

# 600.93. Incremental Checkpoint

State lớn phải hỗ trợ:

```text
incremental checkpoint
```

thay vì bắt buộc full copy.

---

# 600.94. Copy-on-Write Compatibility

Runtime architecture phải tương thích với:

```text
copy-on-write pages
structural sharing
immutable segments
```

nhưng core language không phụ thuộc vào chúng.

---

# 600.95. State Snapshot

API:

```axiom let snapshot = state.snapshot()
```

Snapshot là read-only logical view.

Có thể dùng cho:

```text
background save
debugging
preview
undo
worker thread
```

---

# 600.96. Snapshot Isolation

Snapshot phải nhìn thấy một state version nhất quán:

```text
snapshot.version = 42
```

Nếu application tiếp tục mutate:

```text
current.version = 43
```

snapshot vẫn đại diện version 42.

---

# 600.97. Background Checkpoint

Application có thể:

```axiom store.checkpoint_async()
```

Runtime phải tránh blocking application thread lâu hơn cần thiết.

---

# 600.98. Async Checkpoint Semantics

```axiom let job = store.checkpoint_async()

job.await()
```

Nếu checkpoint chưa commit:

```text
job = pending
```

Nếu crash trước completion:

```text
checkpoint không được coi là committed
```

---

# 600.99. Checkpoint Progress

Runtime có thể cung cấp:

```text
bytes_processed
bytes_total
phase
```

để UI hiển thị progress.

---

# 600.100. Deterministic Recovery

Với cùng:

```text
checkpoint
+
journal
+
schema version
```

recovery phải tạo cùng logical state.

Không để recovery phụ thuộc:

```text
thread scheduling
random memory address
current time
```

trừ khi những giá trị đó đã được persist.

---

# 600.101. Random State

Nếu application sử dụng PRNG và cần reproducibility:

```axiom persistent rng_state
```

Random generator state có thể được checkpoint.

---

# 600.102. Time

Timestamp hiện tại không tự động được coi là deterministic state.

Nếu business logic cần timestamp:

```axiom let now = clock.now()
```

và giá trị cần persistence phải được ghi vào transaction.

---

# 600.103. Application Version Compatibility

State store phải từ chối hoặc migrate state nếu:

```text
schema incompatible
```

Không được cố deserialize bằng layout mới một cách mù quáng.

---

# 600.104. Forward Compatibility

State format nên hỗ trợ unknown fields:

```text
field id
field type
field length
field payload
```

để version mới có thể bổ sung field.

---

# 600.105. Unknown Field Policy

Default:

```text
preserve if possible
```

để state có thể round-trip qua version trung gian.

---

# 600.106. State Type Metadata

Compiler-generated metadata:

```text
TypeId
FieldId
FieldType
Flags
Version
Serializer
Deserializer
Validator
```

---

# 600.107. Stable Field ID

Field persistence không phụ thuộc thứ tự source code.

Ví dụ:

```axiom state User {
    id       @1: UUID
    name     @2: String
    settings @3: Settings
}
```

Nếu developer reorder fields:

```text
persistent identity unchanged
```

---

# 600.108. Field Removal

Field bị remove phải có migration policy.

Không được coi:

```text
missing field
```

là corruption.

---

# 600.109. Default Field Value

Field mới có thể có default:

```axiom settings @4: Settings = Settings.default()
```

---

# 600.110. State Encryption Hook

Core state runtime không bắt buộc encryption.

Nhưng storage backend phải có hook:

```axiom StateStore.open(path, security: ...)
```

để tầng security sau này tích hợp.

---

# 600.111. Compression Hook

Compression là backend policy:

```text
none
fast
maximum
```

Không ảnh hưởng semantics của checkpoint.

---

# 600.112. Checksum vs Hash

Checksum dùng để:

```text
detect accidental corruption
```

Hash có thể dùng để:

```text
content identity
deduplication
integrity
```

Không dùng checksum làm cryptographic security primitive.

---

# 600.113. Deduplication

Checkpoint backend có thể deduplicate immutable blocks:

```text
Block A
Block B
Block C

Checkpoint 1
Checkpoint 2
    ↳ shares A/B
```

Đây là optimization.

---

# 600.114. State Size

Runtime phải cung cấp:

```axiom store.size()
```

và:

```axiom checkpoint.size()
```

để application theo dõi storage.

---

# 600.115. Recovery Diagnostics

Developer mode có thể lấy:

```axiom recovery.diagnostics()
```

gồm:

```text
last valid checkpoint
journal records scanned
transactions replayed
transactions discarded
corrupt offsets
migration operations
recovery duration
```

---

# 600.116. Production Diagnostics

Production diagnostics không được tự động chứa sensitive state payload.

Chỉ metadata:

```text
transaction id
checkpoint id
error code
offset
```

---

# 600.117. State Lock

Một persistent store mặc định phải ngăn hai process cùng ghi một store.

```text
Process A → WRITE
Process B → WRITE
```

Process B nhận:

```text
StateError.StoreLocked
```

---

# 600.118. Multi-Process Read

Read-only access có thể được hỗ trợ:

```axiom StateStore.open_readonly(...)
```

nếu backend cho phép.

---

# 600.119. Single Writer

Default model:

```text
one writer
many readers
```

được chọn vì đơn giản và có performance tốt.

Multi-writer có thể xây dựng phía trên transaction protocol sau này.

---

# 600.120. State Runtime Thread Model

State runtime không tạo thread bắt buộc.

Nếu dùng asynchronous checkpoint:

```text
runtime worker
```

chỉ được tạo khi cần.

---

# 600.121. No Hidden Global Runtime

Không được yêu cầu một global singleton:

```text
GlobalStateRuntime
```

Ứng dụng có thể có nhiều independent stores.

---

# 600.122. State Store Lifecycle

```text
CLOSED
  ↓
OPEN
  ↓
RECOVERING
  ↓
READY
  ↓
CLOSING
  ↓
CLOSED
```

---

# 600.123. Invalid Lifecycle Operations

Ví dụ:

```axiom store.transaction()
```

khi:

```text
store = CLOSED
```

phải trả typed error.

Không crash runtime.

---

# 600.124. State Runtime and Application Exit

Khi application exit bình thường:

```text
pending transactions
    ↓
commit / rollback
    ↓
checkpoint policy
    ↓
clean marker
```

---

# 600.125. Explicit Exit Policy

Application có thể chọn:

```axiom app.exit(policy: .Commit)
```

hoặc:

```axiom app.exit(policy: .Rollback)
```

---

# 600.126. Crash Recovery Guarantee

Axiom không được tuyên bố:

> "mọi crash đều có thể phục hồi mọi dữ liệu"

Guarantee chính xác là:

> **Mọi transaction đã đạt commit durability boundary phải được phục hồi theo semantics của backend; transaction chưa đạt commit boundary phải không được xuất hiện như transaction committed.**

---

# 600.127. Backend Abstraction

State Runtime core định nghĩa interface:

```text
StateBackend
```

Backend native đầu tiên:

```text
LocalFileStateBackend
```

Sau này có thể:

```text
MemoryStateBackend
RemoteStateBackend
DatabaseStateBackend
CustomBackend
```

nhưng Axiom Core không phụ thuộc chúng.

---

# 600.128. Memory Backend

Testing có thể sử dụng:

```axiom StateStore.memory()
```

Không persistence.

Dùng cho:

```text
unit tests
benchmarks
temporary applications
```

---

# 600.129. Test Recovery

Runtime phải hỗ trợ fault injection:

```axiom test {
    crash_after(.journal_write)
}
```

Compiler/runtime test harness dùng để kiểm tra crash consistency.

---

# 600.130. Crash Matrix

Bootstrap test suite phải kiểm tra crash tại:

```text
BEGIN
MUTATION
SERIALIZATION
JOURNAL_WRITE
JOURNAL_SYNC
COMMIT_MARKER
COMMIT_SYNC
CHECKPOINT_WRITE
MANIFEST_WRITE
MANIFEST_SYNC
CLEAN_MARKER
```

Sau mỗi crash:

```text
recover()
validate()
```

---

# 600.131. Invariant Test

Test bắt buộc:

```text
No committed transaction disappears.
No uncommitted transaction appears committed.
No partially committed transaction violates atomicity.
```

---

# 600.132. Power-Loss Simulation

Test backend phải có khả năng mô phỏng:

```text
partial write
reordered write
truncated file
missing metadata
stale manifest
```

---

# 600.133. Recovery Benchmark

Benchmark:

```text
1K transactions
10K transactions
100K transactions
1M transactions
```

đo:

```text
startup
journal replay
checkpoint
commit latency
storage overhead
```

---

# 600.134. Target Performance

State runtime không được trở thành bottleneck cho native application.

Mục tiêu thiết kế:

```text
transient state mutation:
    gần như không overhead

transaction:
    O(changed state)

checkpoint:
    O(changed persistent data)

recovery:
    O(last checkpoint → crash point)
```

---

# 600.135. Recovery Complexity

Nếu checkpoint tại sequence `N` và crash tại `M`:

```text
recovery cost ≈ O(M - N)
```

không phải:

```text
O(total lifetime transactions)
```

---

# 600.136. Journal Growth

Runtime phải định kỳ checkpoint/compact để journal không tăng vô hạn.

---

# 600.137. Backpressure

Nếu storage chậm:

```text
journal queue
```

không được phép tăng vô hạn.

Runtime phải có:

```text
bounded queue
backpressure
commit blocking
```

theo policy.

---

# 600.138. Application Responsiveness

GUI application phải có khả năng:

```text
user interaction
+
background checkpoint
```

mà không freeze toàn bộ UI trong thời gian dài.

---

# 600.139. State Change Notification

API:

```axiom state.watch {
    documents
}
```

Runtime thông báo logical changes:

```text
DocumentChanged
SettingsChanged
CheckpointCreated
```

---

# 600.140. Watcher Semantics

Watcher chỉ được thông báo sau khi state mutation đạt visibility boundary tương ứng.

Không gửi:

```text
"committed"
```

cho transaction chưa commit.

---

# 600.141. State Diff

Runtime có thể cung cấp:

```axiom diff(checkpoint_a, checkpoint_b)
```

trả về logical state changes.

Dùng cho:

```text
debugging
undo
sync
version history
```

---

# 600.142. State Restore

API:

```axiom store.restore(checkpoint_id)
```

không được destroy checkpoint hiện tại.

Flow:

```text
current
  ↓
restore candidate
  ↓
validate
  ↓
new checkpoint
  ↓
becomes current
```

---

# 600.143. Safe Restore

Restore phải atomic.

Crash giữa restore:

```text
old valid state
```

hoặc:

```text
new valid state
```

không được:

```text
half restored state
```

---

# 600.144. Branching State

Future-compatible architecture:

```text
checkpoint 10
   ├── checkpoint 11
   └── checkpoint 11b
```

cho phép:

```text
version branches
```

nhưng branching không bắt buộc trong v5.0 API.

---

# 600.145. State History

Logical model:

```text
StateVersion {
    version
    parent
    checkpoint
}
```

---

# 600.146. Application State Root

Mỗi store có một root:

```text
StateRoot
```

Root version xác định toàn bộ logical application state.

---

# 600.147. Atomic Root Update

Transaction commit cập nhật root atomically:

```text
root 41
   ↓
root 42
```

Không có:

```text
root 42 partially visible
```

---

# 600.148. Persistent Collection

Các collection lớn như:

```text
Vector
Map
Set
DocumentStore
```

phải có persistence-friendly representation.

Runtime không được yêu cầu serialize toàn bộ collection nếu chỉ thay đổi một phần.

---

# 600.149. Persistent Map

Có thể triển khai bằng:

```text
B-tree
HAMT
log-structured index
```

nhưng implementation choice không thuộc core language.

---

# 600.150. Persistent Vector

Có thể dùng structural sharing/chunked storage.

Mục tiêu:

```text
append/update
→ O(log n) hoặc tốt hơn
```

khi phù hợp.

---

# 600.151. Large Blob

Binary asset lớn:

```text
video
image
audio
model
database file
```

không nên nằm trực tiếp trong journal record.

Thay vào đó:

```text
BlobId
size
checksum
storage location
```

---

# 600.152. Blob Store

Native runtime có thể cung cấp:

```axiom blob.put(...)
blob.get(...)
blob.delete(...)
```

State chỉ lưu:

```text
BlobId
```

---

# 600.153. Blob Atomicity

Nếu transaction tham chiếu blob mới:

```text
write blob
→ verify blob
→ commit state reference
```

Không commit reference tới blob chưa hoàn tất.

---

# 600.154. Orphan Blob

Crash có thể tạo blob chưa được state reference.

Runtime phải có cleanup mechanism:

```text
orphan scan
```

Không được xóa blob đang được checkpoint hợp lệ tham chiếu.

---

# 600.155. State GC vs Memory GC

Axiom documentation phải tránh gọi storage cleanup là:

```text
garbage collection
```

để không gây nhầm với memory management.

Tên chính thức:

```text
State Compaction
Storage Reclamation
```

---

# 600.156. Runtime Ownership

State store sở hữu:

```text
journal
checkpoint metadata
storage handles
```

Application sở hữu:

```text
logical state objects
```

---

# 600.157. Resource Lifetime

```axiom let store = StateStore.open(...)
```

khi `store` out-of-scope:

```text
flush/close according to runtime policy
```

Không cần GC.

---

# 600.158. Explicit Close

Có thể:

```axiom store.close()?
```

nhưng RAII/deterministic lifetime vẫn phải đảm bảo cleanup khi scope kết thúc.

---

# 600.159. Panic/Exception Interaction

Nếu transaction block panic/throws:

```text
transaction → rollback
```

trừ khi panic xảy ra ngoài runtime-controlled transaction.

---

# 600.160. Fatal Process Failure

Nếu runtime gặp fatal error:

```text
no attempt to execute arbitrary user recovery code
```

Mục tiêu là giữ storage consistent, không cứu mọi application invariant.

---

# 600.161. Recovery Does Not Execute Arbitrary Application Logic

Journal replay phải dùng deterministic runtime-generated operations.

Không replay bằng cách chạy lại:

```axiom user_function()
```

vì có thể:

```text
network
random
filesystem
time
side effects
```

---

# 600.162. Command/Event Compatibility

Application có thể xây event-sourced architecture phía trên:

```text
Event
→ State mutation
```

nhưng State Runtime bản thân không bắt buộc event sourcing.

---

# 600.163. Event Log vs State Journal

Phân biệt:

```text
State Journal
```

là implementation mechanism cho crash consistency.

```text
Event Log
```

là application semantic history.

Không được đánh đồng hai khái niệm.

---

# 600.164. Networking

State runtime không tự đồng bộ qua network.

Sync protocol là layer khác:

```text
State Runtime
      ↓
State Sync
      ↓
Network
```

---

# 600.165. Multi-Device State

Kiến trúc phải future-compatible với:

```text
local state
    ↓
sync engine
    ↓
remote state
```

nhưng không đưa distributed consensus vào Bootstrap Core.

---

# 600.166. Security Boundary

State runtime phải coi persistent state là untrusted input khi mở từ:

```text
external file
download
old version
shared storage
```

Deserializer phải validate lengths/types.

---

# 600.167. Resource Limits

Deserializer phải có giới hạn:

```text
max object size
max nesting
max collection count
max journal record
```

để tránh malformed state gây resource exhaustion.

---

# 600.168. No Recursive Stack Explosion

Serializer/deserializer nên hỗ trợ iterative traversal hoặc depth limit đối với state graph lớn.

---

# 600.169. Cyclic Graph

Persistent state graph có thể có cycle:

```text
A → B → C → A
```

Serializer phải nhận diện identity và không recurse vô hạn.

---

# 600.170. Identity Table

Trong serialization:

```text
ObjectId → serialized representation
```

cho phép reference sharing/cycles.

---

# 600.171. Duplicate Object

Nếu hai field cùng reference một object:

```text
A.x → Object 42
A.y → Object 42
```

recovery phải giữ semantic identity:

```text
x == y
```

không tạo hai object độc lập nếu type semantics yêu cầu identity.

---

# 600.172. Value Types

Pure value types có thể serialize inline.

```axiom struct Vec3 {
    x: f32
    y: f32
    z: f32
}
```

---

# 600.173. Struct-Only OOP Compatibility

Thiết kế tương thích với kiến trúc Axiom:

```axiom struct Document {
    title: String
}

fn Document.rename(self: &mut Document, name: String) {
    self.title = name
}
```

State runtime không cần class/object hierarchy.

---

# 600.174. Methods and State

Method mutation persistent state phải chạy trong transaction khi state policy yêu cầu:

```axiom document.rename("new")
```

có thể được runtime/compiler nâng thành state mutation transaction tùy context.

---

# 600.175. Compiler Integration

Compiler phải nhận biết:

```text
state
persistent
session
derived
transient
transaction
checkpoint
```

metadata.

---

# 600.176. Generated Metadata

Binary/executable có thể chứa:

```text
AX_STATE
AX_SCHEMA
AX_SERIALIZER
AX_MIGRATION
```

sections hoặc equivalent metadata records.

---

# 600.177. Agent-Friendly Metadata

Metadata phải đủ để tooling/AI agent hiểu:

```text
state types
fields
field IDs
versions
migrations
invariants
```

mà không cần reverse engineer binary layout.

---

# 600.178. Debug State Inspector

Tooling sau này phải có thể:

```text
inspect state
inspect checkpoint
inspect transaction
diff checkpoints
validate store
```

---

# 600.179. CLI

Axiom toolchain dự kiến:

```text
axiom state inspect
axiom state verify
axiom state recover
axiom state compact
axiom state diff
```

---

# 600.180. State Verify

```text
axiom state verify app.state
```

phải kiểm tra:

```text
manifest
checkpoint
journal
checksums
references
schema
```

mà không thay đổi state.

---

# 600.181. State Repair

Repair không được là mặc định destructive operation.

Tool phải tạo backup:

```text
original
repaired
```

trước khi sửa.

---

# 600.182. Backup

Checkpoint có thể được export:

```axiom store.export(checkpoint)
```

thành portable state package.

---

# 600.183. Portable State

Portable state không được phụ thuộc:

```text
memory address
process ID
thread ID
OS handle
```

---

# 600.184. Platform Independence

Logical state format phải có thể di chuyển:

```text
Windows
Linux
macOS
Android
iOS
```

nếu type data tương thích.

---

# 600.185. Endianness

Binary persistent format phải định nghĩa endian representation rõ ràng.

Không phụ thuộc trực tiếp native CPU endian nếu portability là yêu cầu.

---

# 600.186. Alignment

Persistent format không được serialize compiler padding mặc định.

Ví dụ:

```axiom struct S {
    a: u8
    b: u64
}
```

không serialize:

```text
raw sizeof(S)
```

làm format portable.

---

# 600.187. ABI Independence

State format độc lập với:

```text
compiler version
optimization level
CPU architecture
ABI
```

---

# 600.188. Native Fast Path

Dù logical format portable, runtime được phép có fast path:

```text
native memory layout
```

khi:

```text
same platform
same schema
validated representation
```

---

# 600.189. State Runtime Layering

Kiến trúc:

```text
┌──────────────────────────────┐
│ Application                  │
├──────────────────────────────┤
│ Application State API        │
├──────────────────────────────┤
│ Transaction Runtime          │
├──────────────────────────────┤
│ Checkpoint / Recovery        │
├──────────────────────────────┤
│ Serialization Runtime        │
├──────────────────────────────┤
│ State Backend                │
├──────────────────────────────┤
│ Native Filesystem / OS       │
└──────────────────────────────┘
```

---

# 600.190. Không đưa persistence vào từng primitive type

`i32`, `f64`, `String`, `Vec`... không cần biết chúng đang persistent.

Persistence là concern của:

```text
State Runtime
```

và compiler-generated metadata.

---

# 600.191. No Hidden Allocation Requirement

State transaction API không được yêu cầu heap allocation cho mọi mutation nhỏ.

Compiler có thể optimize:

```text
stack transaction
small journal buffer
inline metadata
```

---

# 600.192. Small State Optimization

Với application state rất nhỏ:

```text
settings
preferences
CLI config
```

runtime có thể dùng compact single-file representation.

---

# 600.193. Large State Optimization

Với state lớn:

```text
manifest
index
journal
segments
blobs
checkpoints
```

được partition.

---

# 600.194. State Store Layout

Reference layout:

```text
app.state/
    manifest
    journal/
        000001.log
        000002.log
    checkpoints/
        00000042/
        00000043/
    blobs/
        ...
    indexes/
        ...
```

Đây là reference implementation layout, không phải serialized-format ABI bắt buộc.

---

# 600.195. Atomicity Boundary

Mọi API phải xác định rõ boundary:

```text
memory visible
transaction visible
durable
checkpointed
```

Không dùng từ "saved" một cách mơ hồ trong compiler/runtime specification.

---

# 600.196. State Lifecycle Model

```text
        ┌──────────────┐
        │ Runtime State│
        └──────┬───────┘
               │
          transaction
               │
               ▼
        ┌──────────────┐
        │ Pending State│
        └──────┬───────┘
               │ commit
               ▼
        ┌──────────────┐
        │Committed     │
        └──────┬───────┘
               │ checkpoint
               ▼
        ┌──────────────┐
        │Checkpoint    │
        └──────┬───────┘
               │ recovery
               ▼
        ┌──────────────┐
        │Recovered     │
        └──────────────┘
```

---

# 600.197. Formal Commit Invariant

Một transaction `T` được coi là committed khi và chỉ khi:

```text
CommitMarker(T) exists
AND
CommitMarker(T) passes integrity validation
AND
required durability boundary has completed
```

---

# 600.198. Formal Recovery Invariant

Sau recovery:

```text
State = LastValidCheckpoint
        +
all valid committed transactions after checkpoint
```

và:

```text
uncommitted transactions ∉ recovered state
```

---

# 600.199. Formal Checkpoint Invariant

Checkpoint `C` hợp lệ khi:

```text
manifest(C) valid
AND
all required segments valid
AND
root(C) valid
AND
schema(C) supported or migratable
AND
integrity(C) valid
```

---

# 600.200. Bootstrap Acceptance Criteria

`BOOTSTRAP-600` chỉ được coi là hoàn thành khi implementation/spec test chứng minh được:

### A. State

- persistent state declaration hoạt động;
- transient/session/persistent/derived classification hoạt động;
- stable field identity hoạt động.

### B. Transactions

- begin;
- mutate;
- validate;
- commit;
- rollback;
- savepoint;
- nested transaction semantics.

### C. Durability

- journal;
- commit marker;
- atomic metadata;
- durability policy.

### D. Checkpoint

- full checkpoint;
- incremental checkpoint;
- checkpoint metadata;
- checkpoint validation;
- checkpoint restore.

### E. Recovery

- clean startup;
- crash recovery;
- journal replay;
- rollback incomplete transaction;
- corruption detection;
- recovery diagnostics.

### F. Schema

- versioning;
- field IDs;
- migration;
- backward compatibility.

### G. Performance

- incremental persistence;
- bounded journal;
- background checkpoint;
- no mandatory GC;
- no mandatory borrow checker;
- no global state lock.

### H. Testing

Phải có fault-injection tests tại tối thiểu:

```text
journal write
journal sync
commit marker
commit sync
checkpoint write
manifest update
manifest sync
clean shutdown
```

và test phải chứng minh:

```text
CRASH → RECOVER → VALID STATE
```

---

# 600.201. Architecture Decision

**BOOTSTRAP-600 chốt mô hình State Runtime của Axiom 5.0 là:**

```text
Explicit State
      +
Typed Transactions
      +
Write-Ahead Journal
      +
Atomic Commit Marker
      +
Immutable Checkpoints
      +
Incremental/Differential Persistence
      +
Deterministic Recovery
      +
Schema Versioning/Migration
      +
Session Recovery
```

Không chọn:

```text
GC-based persistence
```

Không chọn:

```text
ORM-first persistence
```

Không chọn:

```text
JSON-first state storage
```

Không chọn:

```text
database-required runtime
```

Không chọn:

```text
event-sourcing-required architecture
```

Không chọn:

```text
raw-memory-dump persistence
```

---

# 600.202. Core Principle

Axiom 5.0 phải hướng tới mô hình:

```text
             APPLICATION
                  │
             App State
                  │
             Transaction
                  │
        ┌─────────┴─────────┐
        │                   │
   In-Memory            Journal
        │                   │
        └─────────┬─────────┘
                  │
               Commit
                  │
            State Root
                  │
             Checkpoint
                  │
             Durable Store
```

Và sau crash:

```text
Durable Checkpoint
       +
Valid Committed Journal
       ↓
Deterministic Recovery
       ↓
Valid Application State
```

**Đây là foundation để Axiom có thể xây những ứng dụng native dài hạn như IDE, editor, database tool, game/editor engine, GUI application và AI application mà không phải tự phát minh một hệ thống autosave/crash-recovery riêng cho từng ứng dụng.**

---

## 600.203. Task completion

`BOOTSTRAP-600` hoàn tất về mặt kiến trúc khi:

```text
Native State Model
        ↓
Transaction Model
        ↓
Journal Model
        ↓
Checkpoint Model
        ↓
Recovery Model
        ↓
Schema/Migration Model
        ↓
Session Model
        ↓
Crash-Consistency Test Model
```

được xem là **một subsystem thống nhất của Axiom Runtime 5.0**, với persistence là native capability nhưng **không làm thay đổi mô hình memory management cơ bản của Axiom**.

**Next task trong chuỗi Bootstrap: `BOOTSTRAP-601`.**