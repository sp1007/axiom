# BOOTSTRAP-724 — AXSTORAGE

**Namespace:** `AXSTORAGE`  
**Phase:** Axiom Civilization Runtime / Storage & Data Infrastructure  
**Status:** **ARCHITECTURAL BASELINE — FROZEN TARGET**  
**Depends on:** `AXLAW`, `AXIDENTITY`, `AXGOV`, `AXFINANCE`, `AXGEOSPATIAL`, `AXTELECOM`, `AXCOMPUTE`, `AXASSET`, `AXENERGY`

---

# 724.0 — Mục tiêu

`AXSTORAGE` là lớp lưu trữ native của Axiom Civilization Runtime.

Nó phải cung cấp một abstraction thống nhất từ:

```text id="storage1"
CPU memory
memory-mapped files
local files
block devices
filesystem
key-value
document
column
relational primitives
graph
time-series
spatial
object storage
content-addressed storage
cache
distributed storage
replicated storage
backup
snapshot
archive
```

Mục tiêu kiến trúc:

> Axiom application không bị khóa vào một database engine, filesystem hay cloud storage vendor cụ thể.

Đồng thời:

> Không biến mọi loại dữ liệu thành một "database abstraction" chậm và quá tổng quát.

---

# 724.1 — Architecture

```text id="storage2"
                         AXSTORAGE
                             │
        ┌────────────────────┼────────────────────┐
        │                    │                    │
     BYTE STORAGE         STRUCTURED           DISTRIBUTED
        │                    │                    │
     memory              KV / table            replica
     file                document              shard
     block               graph                 consensus-ref
     object              spatial               snapshot
        │                    │                    │
        └────────────────────┼────────────────────┘
                             │
                      STORAGE ENGINE
                             │
            ┌────────────────┼────────────────┐
            │                │                │
          LOCAL             EDGE            CLUSTER
```

---

# 724.2 — Core Boundary

`AXSTORAGE` sở hữu:

```text id="storage3"
bytes
blocks
files
directories
filesystem semantics
storage volumes
objects
records
indexes
transactions
MVCC
WAL
snapshots
replication
sharding
compression
encryption references
content addressing
cache
backup
restore
storage telemetry
storage consistency
```

Không sở hữu:

```text id="storage4"
money             → AXFINANCE
identity          → AXIDENTITY
legal state       → AXLAW / AXGOV
physical asset    → AXASSET
compute resources → AXCOMPUTE
network state     → AXTELECOM
```

---

# 724.3 — Storage Device

```axiom id="storage5"
storage_device {
    device_id
    device_type
    capacity
    block_size
    performance_class
    reliability_class
}
```

Types:

```text id="storage6"
HDD
SSD
NVMe
optical
tape
persistent_memory
remote_block
virtual_block
```

---

# 724.4 — Storage Volume

```axiom id="storage7"
storage_volume {
    volume_id
    device_references
    capacity
    block_size
    redundancy
    encryption_reference
    state
}
```

States:

```text id="storage8"
ONLINE
DEGRADED
READ_ONLY
OFFLINE
REBUILDING
FAILED
RETIRED
```

---

# 724.5 — Block Storage

```axiom id="storage9"
block_device {
    block_device_id
    volume_reference
    block_size
    block_count
    access_mode
}
```

Operations:

```axiom id="storage10"
read_block()
write_block()
read_blocks()
write_blocks()
flush_blocks()
discard_blocks()
```

Không bắt buộc mọi application phải dùng filesystem.

---

# 724.6 — Byte Storage

```axiom id="storage11"
byte_store {
    store_id
    capacity
    access_mode
}
```

Native operations:

```axiom id="storage12"
read_bytes()
write_bytes()
append_bytes()
truncate_bytes()
flush_bytes()
```

---

# 724.7 — File

```axiom id="storage13"
file {
    file_id
    path
    size
    metadata
    content_version
}
```

File content và metadata phải tách biệt về semantic.

---

# 724.8 — Directory

```axiom id="storage14"
directory {
    directory_id
    parent
    name
    children
}
```

Filesystem phải hỗ trợ:

```text id="storage15"
hierarchical paths
links
permissions
attributes
timestamps
file versions
```

---

# 724.9 — Filesystem

```axiom id="storage16"
filesystem {
    filesystem_id
    volume_reference
    block_size
    namespace
    allocation_policy
    metadata_policy
}
```

Axiom không bắt buộc một filesystem duy nhất.

---

# 724.10 — File Handle

```axiom id="storage17"
file_handle {
    file_reference
    access_mode
    position
    flags
}
```

Hỗ trợ:

```text id="storage18"
read
write
append
read_write
memory_map
direct_io
async_io
```

---

# 724.11 — Memory-Mapped Storage

```axiom id="storage19"
mapped_region {
    storage_reference
    offset
    length
    access_mode
}
```

API:

```axiom id="storage20"
map()
unmap()
flush_mapping()
```

Đây là primitive quan trọng cho Axiom performance.

---

# 724.12 — Zero-Copy

Các API storage phải hỗ trợ:

```text id="storage21"
memory_view
file_view
mapped_view
buffer_view
```

Ví dụ:

```axiom id="storage22"
data = map(file)

process(data)

flush_mapping(data)
```

Không bắt buộc:

```text id="storage23"
file
 ↓ copy
temporary buffer
 ↓ copy
application object
```

---

# 724.13 — Object Storage

```axiom id="storage24"
storage_object {
    object_id
    namespace
    key
    size
    content_hash
    metadata
    version
}
```

Object không có filesystem semantics mặc định.

---

# 724.14 — Object Namespace

```axiom id="storage25"
object_namespace {
    namespace_id
    name
    policy
    retention_policy
}
```

API:

```axiom id="storage26"
put_object()
get_object()
delete_object()
list_objects()
head_object()
```

---

# 724.15 — Content Addressed Storage

```axiom id="storage27"
content_object {
    content_hash
    content_type
    size
    storage_reference
}
```

Identifier:

```text id="storage28"
hash(content)
```

Ứng dụng:

```text id="storage29"
compiler cache
package store
AI model
dataset
artifact
backup
deduplication
```

---

# 724.16 — Immutable Artifact

```axiom id="storage30"
artifact {
    artifact_id
    content_hash
    metadata
    creation_event
}
```

Một artifact đã commit:

```text id="storage31"
cannot mutate
```

Version mới tạo artifact mới.

---

# 724.17 — Key-Value Store

```axiom id="storage32"
kv_store {
    store_id
    key_schema
    value_schema
    consistency
}
```

API:

```axiom id="storage33"
kv_get()
kv_put()
kv_delete()
kv_exists()
kv_scan()
kv_prefix_scan()
```

---

# 724.18 — Structured Record

```axiom id="storage34"
record {
    record_id
    schema
    fields
    version
}
```

Schema phải versioned.

---

# 724.19 — Table

```axiom id="storage35"
table {
    table_id
    schema
    primary_key
    indexes
    partitioning
}
```

Axiom không cần bắt buộc SQL syntax ở core runtime.

---

# 724.20 — Query

```axiom id="storage36"
storage_query {
    source
    projection
    filter
    ordering
    grouping
    limit
}
```

Có thể compile query thành execution plan.

---

# 724.21 — Query Plan

```axiom id="storage37"
query_plan {
    operations
    indexes
    filters
    joins
    estimated_cost
}
```

Optimizer có thể chọn:

```text id="storage38"
index scan
range scan
hash lookup
sort
hash join
merge join
spatial index
column scan
```

---

# 724.22 — Index

```axiom id="storage39"
storage_index {
    index_id
    source
    key_definition
    index_type
}
```

Types:

```text id="storage40"
B-tree
B+tree
hash
LSM
bitmap
inverted
spatial
full-text
column
```

---

# 724.23 — Index Principle

Index là derived structure.

```text id="storage41"
authoritative data
      ↓
index
```

Nếu index hỏng:

```text id="storage42"
rebuild(index)
```

không làm mất authoritative records.

---

# 724.24 — Transactions

```axiom id="storage43"
transaction {
    transaction_id
    isolation
    state
    read_set
    write_set
}
```

Operations:

```axiom id="storage44"
begin()
commit()
rollback()
savepoint()
rollback_to_savepoint()
```

---

# 724.25 — Isolation

Hỗ trợ:

```text id="storage45"
read_uncommitted
read_committed
repeatable_read
snapshot
serializable
```

Không yêu cầu mọi backend hỗ trợ mọi level.

Nếu backend không hỗ trợ level yêu cầu:

```text id="storage46"
fail explicitly
```

Không âm thầm downgrade.

---

# 724.26 — MVCC

```axiom id="storage47"
record_version {
    record
    version
    created_at
    deleted_at
    transaction_reference
}
```

MVCC cho phép:

```axiom id="storage48"
read_at(snapshot)
```

---

# 724.27 — Snapshot

```axiom id="storage49"
storage_snapshot {
    snapshot_id
    source
    version
    created_at
}
```

Snapshot phải có:

```text id="storage50"
stable identity
consistent point-in-time state
verification metadata
```

---

# 724.28 — WAL

```axiom id="storage51"
write_ahead_log {
    segment
    sequence
    transaction
    operation
    checksum
}
```

Nguyên tắc:

```text id="storage52"
WAL
 ↓
durability
 ↓
data page
```

---

# 724.29 — Crash Recovery

```text id="storage53"
START
 ↓
load checkpoint
 ↓
read WAL
 ↓
redo committed operations
 ↓
undo incomplete operations
 ↓
verify
 ↓
ONLINE
```

Recovery phải deterministic.

---

# 724.30 — Durability

Axiom phải phân biệt:

```text id="storage54"
memory_only
buffered
write_through
durable
replicated
geo_replicated
```

Không gọi `write()` là durable nếu chưa đạt durability contract.

---

# 724.31 — Replication

```axiom id="storage55"
storage_replication {
    source
    replicas
    mode
    consistency
    failure_policy
}
```

Modes:

```text id="storage56"
none
async
semi_sync
sync
multi_region
```

---

# 724.32 — Replica

```axiom id="storage57"
storage_replica {
    replica_id
    source_reference
    location_reference
    state
    lag
}
```

States:

```text id="storage58"
SYNCED
CATCHING_UP
DEGRADED
FAILED
REBUILDING
```

---

# 724.33 — Consistency

Hỗ trợ explicit:

```text id="storage59"
strong
snapshot
causal
eventual
session
```

Application phải biết contract.

Không được biến eventual consistency thành strong consistency bằng tên gọi.

---

# 724.34 — Sharding

```axiom id="storage60"
storage_shard {
    shard_id
    partition_key
    range
    node_reference
    version
}
```

Strategies:

```text id="storage61"
hash
range
time
spatial
directory
custom
```

---

# 724.35 — Rebalancing

```axiom id="storage62"
rebalance_plan {
    source_shards
    target_nodes
    migration_strategy
    progress
}
```

Phải tránh:

```text id="storage63"
data loss
duplicate authoritative writes
inconsistent ownership
```

---

# 724.36 — Distributed Transaction

Axiom không ép mọi distributed operation thành global transaction.

Hỗ trợ:

```text id="storage64"
local transaction
distributed transaction
saga/reference workflow
eventual consistency
```

Distributed transaction chỉ dùng khi contract thực sự cần.

---

# 724.37 — Event Store

```axiom id="storage65"
event_store {
    stream_id
    event_type
    sequence
    payload
    timestamp
}
```

API:

```axiom id="storage66"
append_event()
read_events()
read_stream()
read_from_sequence()
```

Event immutable.

---

# 724.38 — Event Sourcing

```text id="storage67"
events
  ↓
projection
  ↓
current state
```

Projection có thể bị xóa/rebuild.

Events không.

---

# 724.39 — Projection

```axiom id="storage68"
storage_projection {
    projection_id
    source_streams
    schema
    version
    checkpoint
}
```

---

# 724.40 — Time-Series Storage

```axiom id="storage69"
time_series {
    series_id
    metric
    timestamp
    value
    tags
}
```

Tối ưu cho:

```text id="storage70"
telemetry
energy
water
compute
transport
manufacturing
telecom
sensors
```

---

# 724.41 — Spatial Storage

```axiom id="storage71"
spatial_store {
    dataset
    geometry_reference
    spatial_index
    crs_reference
}
```

Geometry semantics thuộc `AXGEOSPATIAL`.

Storage chỉ lưu/query.

---

# 724.42 — Graph Storage

```axiom id="storage72"
graph_store {
    nodes
    edges
    properties
    indexes
}
```

Hỗ trợ:

```axiom id="storage73"
graph_add_node()
graph_add_edge()
graph_neighbors()
graph_path()
```

Dùng cho:

```text id="storage74"
dependency
supply chain
network
asset graph
social/reference graphs
knowledge graph
```

---

# 724.43 — Document Storage

```axiom id="storage75"
document_store {
    document_schema
    indexes
    version
}
```

Document có thể chứa nested data.

Không bắt buộc normalize mọi thứ thành table.

---

# 724.44 — Column Storage

```axiom id="storage76"
column_store {
    schema
    columns
    compression
    partitions
}
```

Tối ưu:

```text id="storage77"
analytics
aggregation
large scans
AI datasets
```

---

# 724.45 — Compression

Native abstraction:

```axiom id="storage78"
compression_policy {
    algorithm
    level
    block_size
}
```

Có thể hỗ trợ:

```text id="storage79"
LZ
Zstandard-like
dictionary
delta
run-length
bit packing
column encoding
```

Không khóa vào vendor.

---

# 724.46 — Encryption

```axiom id="storage80"
storage_encryption {
    mode
    key_reference
    algorithm_reference
    rotation_policy
}
```

Key management thuộc security/key-management subsystem.

Không lưu raw key trong record metadata.

---

# 724.47 — Deduplication

```axiom id="storage81"
dedup_policy {
    scope
    hash_algorithm
    mode
}
```

Content-addressed data cho phép:

```text id="storage82"
same content
   ↓
same object
```

---

# 724.48 — Cache

```axiom id="storage83"
storage_cache {
    cache_id
    capacity
    eviction_policy
    consistency_policy
}
```

Policies:

```text id="storage84"
LRU
LFU
ARC-like
TTL
application-defined
```

Cache không phải source of truth.

---

# 724.49 — Cache Invalidation

Cache entry phải reference:

```text id="storage85"
source_version
expiration
consistency_policy
```

Nếu authoritative version thay đổi:

```text id="storage86"
invalidate
or
revalidate
```

Không dùng stale data khi contract yêu cầu strong consistency.

---

# 724.50 — Backup

```axiom id="storage87"
backup {
    backup_id
    source
    snapshot_reference
    created_at
    retention
    integrity_hash
}
```

Backup types:

```text id="storage88"
full
incremental
differential
continuous
snapshot
archive
```

---

# 724.51 — Restore

```axiom id="storage89"
restore_operation {
    source_backup
    target
    point_in_time
    verification_policy
}
```

Phải hỗ trợ:

```axiom id="storage90"
restore_to_new
restore_in_place
point_in_time_recovery
partial_restore
```

---

# 724.52 — Archive

```axiom id="storage91"
archive_object {
    content
    retention
    legal_hold_reference
    integrity
}
```

Retention không tự tạo legal obligation.

Legal semantics thuộc `AXLAW`.

---

# 724.53 — Data Lifecycle

```text id="storage92"
ACTIVE
 ↓
COOLED
 ↓
ARCHIVED
 ↓
RETENTION_EXPIRED
 ↓
DELETED
```

Có thể có:

```text id="storage93"
LEGAL_HOLD
IMMUTABLE
QUARANTINED
```

---

# 724.54 — Deletion

Axiom phải phân biệt:

```text id="storage94"
logical_delete
physical_delete
cryptographic_delete
retention_expiry
```

Không được tuyên bố dữ liệu đã vật lý biến mất chỉ vì metadata đã xóa.

---

# 724.55 — Integrity

```axiom id="storage95"
storage_integrity {
    content_hash
    checksum
    verification_method
    verification_time
}
```

Integrity checks:

```axiom id="storage96"
verify_block()
verify_object()
verify_snapshot()
verify_backup()
verify_replica()
```

---

# 724.56 — Storage Health

```axiom id="storage97"
storage_health {
    device
    volume
    filesystem
    replica
    capacity
    integrity
    state
}
```

States:

```text id="storage98"
HEALTHY
DEGRADED
FULL
CORRUPTED
REBUILDING
OFFLINE
FAILED
```

---

# 724.57 — Storage Telemetry

```axiom id="storage99"
storage_telemetry {
    target
    timestamp
    metric
    value
}
```

Metrics:

```text id="storage100"
IOPS
throughput
latency
queue_depth
cache_hit_rate
capacity
fragmentation
replication_lag
error_rate
```

---

# 724.58 — Database Engine Contract

Axiom không bắt buộc:

```text id="storage101"
"database = SQL"
```

Database engine có thể expose:

```text id="storage102"
KV
table
document
graph
column
time-series
spatial
```

và ứng dụng chọn primitive phù hợp.

---

# 724.59 — Query Compilation

Query có thể compile:

```text id="storage103"
Axiom query
     ↓
logical plan
     ↓
optimized plan
     ↓
storage backend
```

Compiler/runtime có thể specialize khi schema biết trước.

---

# 724.60 — Compile-Time Data Access

Axiom có thể cho phép:

```axiom id="storage104"
table User {
    id: u64
    name: string
}
```

Compiler biết schema:

```text id="storage105"
field offsets
types
indexes
serialization
query shape
```

Giảm runtime reflection.

---

# 724.61 — Serialization

Native binary representation:

```axiom id="storage106"
serialize<T>()
deserialize<T>()
```

Phải hỗ trợ:

```text id="storage107"
version
endianness
schema id
field compatibility
optional fields
unknown fields
```

---

# 724.62 — Schema Evolution

Hỗ trợ:

```text id="storage108"
add field
remove field
rename field
change compatible type
migration
versioning
```

Không được tự động thực hiện incompatible migration mà không có policy.

---

# 724.63 — Data Compatibility

Một record cũ có thể được đọc bởi schema mới nếu:

```text id="storage109"
compatibility contract
```

được đáp ứng.

Có thể dùng:

```text id="storage110"
default values
optional fields
migration adapter
version-aware decoder
```

---

# 724.64 — Distributed Offline Storage

```text id="storage111"
Device
 ↓
Local storage
 ↓
Local transaction
 ↓
Event journal
 ↓
Offline operation
 ↓
Reconnect
 ↓
Sync
 ↓
Conflict resolution
```

Conflict phải giữ evidence:

```text id="storage112"
source
version
timestamp
causal chain
```

---

# 724.65 — Conflict Resolution

Hỗ trợ:

```text id="storage113"
last-write-wins
version-wins
causal merge
application merge
manual resolution
```

Nhưng authoritative domain state không được tự động LWW nếu domain policy cấm.

---

# 724.66 — Storage Digital Twin

```axiom id="storage114"
storage_digital_twin {
    devices
    volumes
    filesystems
    replicas
    capacity
    workloads
    telemetry
}
```

Simulation:

```axiom id="storage115"
simulate_storage_failure()
simulate_rebuild()
simulate_capacity()
simulate_replication()
simulate_sharding()
simulate_backup_restore()
```

---

# 724.67 — AI Storage

AI có thể hỗ trợ:

```text id="storage116"
capacity prediction
anomaly detection
failure prediction
index recommendation
query optimization
cache prediction
tiering recommendation
compression recommendation
replica placement
storage cost optimization
```

AI không được tự:

```text id="storage117"
delete_authoritative_data()
change_retention_without_policy()
disable_backup()
bypass_access_control()
```

---

# 724.68 — Security

Capabilities:

```text id="storage118"
storage.read
storage.write
storage.admin

storage.file.read
storage.file.write
storage.file.manage

storage.volume.read
storage.volume.manage

storage.object.read
storage.object.write
storage.object.delete

storage.record.read
storage.record.write

storage.schema.manage
storage.index.manage

storage.transaction.execute

storage.snapshot.create
storage.snapshot.restore

storage.replication.manage
storage.backup.manage

storage.encryption.manage
storage.archive.manage

storage.ai.execute
storage.simulation.execute
storage.digitaltwin.execute
```

---

# 724.69 — Access Control

Mỗi storage operation có thể kiểm tra:

```text id="storage119"
principal
resource
operation
purpose
tenant
classification
time
location
```

Không mặc định mọi process có full filesystem access.

---

# 724.70 — Audit

Sensitive operations:

```text id="storage120"
read_sensitive
write
delete
restore
change_acl
change_schema
change_retention
export
replicate
```

phải audit được khi policy yêu cầu.

---

# 724.71 — Event Model

```text id="storage121"
STORAGE_DEVICE_CREATED
STORAGE_VOLUME_CREATED
VOLUME_STATE_CHANGED

FILESYSTEM_CREATED
FILE_CREATED
FILE_VERSIONED
FILE_DELETED

OBJECT_CREATED
OBJECT_VERSIONED
OBJECT_DELETED

RECORD_CREATED
RECORD_UPDATED
RECORD_DELETED

INDEX_CREATED
INDEX_REBUILT

TRANSACTION_STARTED
TRANSACTION_COMMITTED
TRANSACTION_ROLLED_BACK

SNAPSHOT_CREATED
SNAPSHOT_DELETED

WAL_SEGMENT_CREATED
RECOVERY_STARTED
RECOVERY_COMPLETED

REPLICA_CREATED
REPLICA_SYNCHRONIZED
REPLICA_FAILED
REPLICA_REBUILT

SHARD_CREATED
SHARD_MOVED

BACKUP_CREATED
BACKUP_VERIFIED
RESTORE_STARTED
RESTORE_COMPLETED

ARCHIVE_CREATED
RETENTION_EXPIRED

INTEGRITY_CHECKED
CORRUPTION_DETECTED

TELEMETRY_RECEIVED
HEALTH_CHANGED

AI_ANALYSIS_CREATED
SIMULATION_CREATED
DIGITAL_TWIN_UPDATED

STATE_RECONCILIATION_CREATED
```

---

# 724.72 — Native APIs

```axiom id="storage122"
create_storage_device()
create_storage_volume()

create_block_device()
read_block()
write_block()
flush_blocks()

create_filesystem()
create_file()
open_file()
read_file()
write_file()
append_file()
delete_file()

create_directory()
remove_directory()

map_file()
unmap_file()

create_object_store()
put_object()
get_object()
delete_object()
list_objects()

create_kv_store()
kv_get()
kv_put()
kv_delete()
kv_scan()

create_table()
insert_record()
update_record()
delete_record()
query_records()

create_document_store()
create_column_store()
create_graph_store()
create_time_series_store()
create_spatial_store()

create_index()
rebuild_index()

begin_transaction()
commit_transaction()
rollback_transaction()

create_snapshot()
read_snapshot()

create_wal()
recover_storage()

create_replica()
synchronize_replica()
rebuild_replica()

create_shard()
rebalance_storage()

append_event()
read_events()

serialize()
deserialize()

create_backup()
verify_backup()
restore_backup()

create_archive()
apply_retention()

verify_integrity()

record_storage_telemetry()
evaluate_storage_health()

create_storage_simulation()
create_storage_digital_twin()

reconcile_storage_state()
replay_storage_state()
```

---

# 724.73 — Canonical File Flow

```text id="storage123"
Application
 ↓
File API
 ↓
Filesystem
 ↓
Volume
 ↓
Block Device
 ↓
Storage Device
```

---

# 724.74 — Canonical Database Flow

```text id="storage124"
Application
 ↓
Typed Query
 ↓
Logical Plan
 ↓
Query Optimizer
 ↓
Index / Scan
 ↓
Transaction
 ↓
Storage Engine
 ↓
WAL
 ↓
Data
```

---

# 724.75 — Canonical Distributed Flow

```text id="storage125"
Write
 ↓
Transaction
 ↓
WAL
 ↓
Primary
 ↓
Replication
 ↓
Replica
 ↓
Commit
```

---

# 724.76 — Canonical Backup Flow

```text id="storage126"
Live State
 ↓
Consistent Snapshot
 ↓
Backup
 ↓
Integrity Verification
 ↓
Archive
 ↓
Periodic Restore Test
```

Backup được coi là usable chỉ khi restore test có thể xác minh được.

---

# 724.77 — Formal Invariants

```text id="storage127"
STG-INV-01   Every storage device has stable identity.
STG-INV-02   Every volume references its storage source.
STG-INV-03   Block size is explicit.
STG-INV-04   File identity is distinct from path.
STG-INV-05   Object identity is distinct from object key.
STG-INV-06   Record identity is distinct from physical storage location.
STG-INV-07   Indexes are derived structures.
STG-INV-08   Cache is never authoritative.
STG-INV-09   Content-addressed objects are immutable.
STG-INV-10   Artifact identity is content-verifiable.

STG-INV-11   Transactions have explicit lifecycle.
STG-INV-12   Isolation level is explicit.
STG-INV-13   Unsupported isolation cannot silently downgrade.
STG-INV-14   WAL ordering is preserved.
STG-INV-15   Recovery is deterministic.
STG-INV-16   Durable writes satisfy declared durability.
STG-INV-17   Snapshot represents a consistent version.
STG-INV-18   MVCC preserves version history.
STG-INV-19   Deleted records remain recoverable when policy requires.
STG-INV-20   Schema versions are explicit.

STG-INV-21   Replicas have explicit consistency modes.
STG-INV-22   Replica lag is observable.
STG-INV-23   Shard ownership is explicit.
STG-INV-24   Rebalancing preserves data integrity.
STG-INV-25   Distributed writes preserve transaction identity.
STG-INV-26   Offline writes preserve causal identity.
STG-INV-27   Synchronization is idempotent.
STG-INV-28   Conflicting writes are not silently discarded.
STG-INV-29   Reconciliation is auditable.
STG-INV-30   Replay reconstructs storage state.

STG-INV-31   Backup integrity is verifiable.
STG-INV-32   Restore identifies exact source snapshot.
STG-INV-33   Retention policies are explicit.
STG-INV-34   Legal hold prevents policy-incompatible deletion.
STG-INV-35   Physical deletion is distinct from logical deletion.
STG-INV-36   Encryption metadata references key management.
STG-INV-37   Sensitive access is auditable.
STG-INV-38   AI cannot bypass authorization.
STG-INV-39   AI cannot autonomously delete authoritative data.
STG-INV-40   Simulation cannot mutate production storage state.
```

---

# 724.78 — Performance Architecture

Đây là một trong những subsystem có ảnh hưởng trực tiếp đến hiệu năng Axiom.

Không nên có:

```text id="storage128"
Axiom object
 ↓
serialization
 ↓
generic RPC
 ↓
database driver
 ↓
database
```

cho mọi thao tác.

Native path:

```text id="storage129"
Axiom typed data
      ↓
compile-time layout
      ↓
native storage representation
      ↓
direct I/O / mmap
```

khi deployment cho phép.

---

# 724.79 — Storage Layout

Runtime nên hỗ trợ:

```text id="storage130"
AoS
SoA
columnar
row-oriented
append-only
log-structured
paged
extent-based
```

Application/data engine chọn layout dựa trên access pattern.

---

# 724.80 — Small Object Optimization

Các record nhỏ có thể được inline:

```text id="storage131"
record header
small payload
```

thay vì:

```text id="storage132"
record
 ↓ heap pointer
payload
```

Mục tiêu:

```text id="storage133"
fewer allocations
better locality
less fragmentation
```

---

# 724.81 — Streaming

Storage API phải hỗ trợ:

```axiom id="storage134"
stream_read()
stream_write()
stream_scan()
stream_query()
```

để xử lý dataset lớn mà không cần load toàn bộ vào RAM.

---

# 724.82 — Completion Criteria

`BOOTSTRAP-724` phải freeze:

1. Storage device.
2. Volume.
3. Block storage.
4. Byte storage.
5. Files.
6. Directories.
7. Filesystem.
8. File handles.
9. Memory mapping.
10. Zero-copy.
11. Object storage.
12. Content-addressed storage.
13. Immutable artifacts.
14. KV storage.
15. Records.
16. Tables.
17. Queries.
18. Query plans.
19. Indexes.
20. Transactions.
21. Isolation.
22. MVCC.
23. WAL.
24. Crash recovery.
25. Durability.
26. Replication.
27. Consistency.
28. Sharding.
29. Rebalancing.
30. Distributed transactions.
31. Event store.
32. Event sourcing.
33. Projections.
34. Time-series.
35. Spatial storage.
36. Graph storage.
37. Document storage.
38. Column storage.
39. Compression.
40. Encryption.
41. Deduplication.
42. Cache.
43. Backup.
44. Restore.
45. Archive.
46. Retention.
47. Integrity.
48. Storage health.
49. Telemetry.
50. Schema evolution.
51. Serialization.
52. Offline storage.
53. Conflict resolution.
54. Digital twin.
55. AI boundary.
56. Security.
57. Access control.
58. Audit.
59. Performance architecture.
60. Streaming.
61. Formal invariants.
62. Property tests.
63. Integration tests.

---

# 724.83 — Definition of Done

```text id="storage135"
BOOTSTRAP-724
STATUS: COMPLETE / FROZEN

AXSTORAGE 5.0
    ├── Block Storage
    ├── Filesystem
    ├── Files
    ├── Memory Mapping
    ├── Object Storage
    ├── Content Addressing
    ├── KV
    ├── Records
    ├── Tables
    ├── Document
    ├── Column
    ├── Graph
    ├── Time-Series
    ├── Spatial
    ├── Query Engine
    ├── Indexing
    ├── Transactions
    ├── MVCC
    ├── WAL
    ├── Snapshots
    ├── Replication
    ├── Sharding
    ├── Compression
    ├── Encryption
    ├── Cache
    ├── Backup
    ├── Restore
    ├── Archive
    ├── Event Store
    ├── Offline Storage
    ├── Distributed Storage
    ├── Telemetry
    ├── Security
    ├── AI
    ├── Simulation
    ├── Digital Twin
    ├── Zero-Copy
    ├── Memory Mapping
    └── Native Performance
```

**BOOTSTRAP-724 / AXSTORAGE — ARCHITECTURAL BASELINE FROZEN.**

---

# BOOTSTRAP-725 — AXDATABASE

**Native Typed Database & Data Query Runtime — relational semantics, schema/type system, SQL-like declarative query layer, joins, aggregation, constraints, indexes, query planner/optimizer, materialized views, migrations, CDC, event integration, analytical execution, vector search, full-text search, spatial query integration, distributed query execution, OLTP/OLAP convergence, embedded database, server database, replication, backup/recovery & Database Runtime 5.0.**