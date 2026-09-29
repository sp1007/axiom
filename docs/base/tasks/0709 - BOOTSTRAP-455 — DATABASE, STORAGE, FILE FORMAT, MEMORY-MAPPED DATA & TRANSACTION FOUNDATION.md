# BOOTSTRAP-455 — DATABASE, STORAGE, FILE FORMAT, MEMORY-MAPPED DATA & TRANSACTION FOUNDATION

**Trạng thái: COMPLETED / LOCKED**

Mục tiêu của 455 là tạo nền tảng storage đủ thấp để Axiom có thể xây:

- file/database engine hiệu năng cao;
- embedded database;
- cache;
- key-value store;
- SQL engine;
- time-series database;
- vector database;
- object/blob storage;

nhưng **database không trở thành một phần bắt buộc của runtime**.

Kiến trúc:

```text
Axiom Core
    ↓
Memory / Ownership
    ↓
OS Storage
    ↓
File / Directory / Mapping
    ↓
Binary Format / Serialization
    ↓
Storage Engine
    ↓
Index / Cache / WAL
    ↓
Transaction
    ↓
Database
    ↓
SQL / ORM / Query Framework
```

---

## 455.1 — Storage layering

Storage được chia:

```text
storage-core
storage-platform
storage-file
storage-map
storage-format
storage-cache
storage-index
storage-wal
storage-transaction
storage-kv
database-core
database-sql
```

---

## 455.2 — No mandatory database runtime

Executable không sử dụng database không được link database components.

---

## 455.3 — File abstraction

Core storage API cung cấp:

```text
File
FileHandle
OpenOptions
FileMetadata
```

---

## 455.4 — File ownership

`File` là resource-owning type.

Drop phải đóng handle deterministic.

---

## 455.5 — File modes

Explicit modes:

```text
read
write
append
read_write
create
create_new
truncate
```

---

## 455.6 — File permissions

Permissions là platform-specific metadata.

---

## 455.7 — File offsets

File position sử dụng explicit integer type phù hợp target.

---

## 455.8 — Read

```text
read(buffer)
```

có thể trả partial result.

---

## 455.9 — Write

```text
write(buffer)
```

có thể trả partial result.

---

## 455.10 — Read exact

Convenience:

```text
read_exact(buffer)
```

---

## 455.11 — Write all

Convenience:

```text
write_all(buffer)
```

---

# 455.12 — Random access

File phải hỗ trợ:

```text
seek
tell
read_at
write_at
```

khi platform cho phép.

---

## 455.13 — Positional I/O

`read_at/write_at` không làm thay đổi shared file cursor.

---

## 455.14 — Append semantics

Append phải tôn trọng OS atomic append semantics khi được requested.

---

## 455.15 — File locking

File locking là explicit capability.

---

## 455.16 — Advisory locking

Unix-style advisory locks được expose khi platform hỗ trợ.

---

## 455.17 — Mandatory locking

Không giả định mandatory locking portable.

---

## 455.18 — File sync

API:

```text
flush
sync
sync_data
```

khi platform hỗ trợ.

---

## 455.19 — Durability

`write()` không đồng nghĩa dữ liệu đã durable trên storage.

---

## 455.20 — Durable write

Database/storage engine phải explicit sử dụng sync/durability operation khi cần.

---

# 455.21 — Directory abstraction

```text
Directory
DirEntry
Path
```

---

## 455.22 — Directory traversal

Iterator-based traversal để tránh load toàn bộ directory vào RAM.

---

## 455.23 — Recursive traversal

Là higher-level library operation.

---

## 455.24 — Symbolic links

Symlink semantics phải explicit.

---

## 455.25 — Hard links

Hard links được hỗ trợ trên platform có khả năng.

---

## 455.26 — Rename

Rename/move là explicit filesystem operation.

---

## 455.27 — Atomic rename

Library phải phân biệt rename thường và atomicity guarantees khi platform hỗ trợ.

---

## 455.28 — Temporary files

Temporary file API phải có secure creation semantics.

---

## 455.29 — Temporary directories

Tương tự temporary file.

---

## 455.30 — File metadata

Có thể expose:

```text
size
timestamps
permissions
type
inode/file-id
```

target-dependent.

---

# 455.31 — Path model

`Path` không phải `String` alias đơn giản.

---

## 455.32 — Platform path

Native filesystem paths có thể chứa representation không giống UTF-8 trên một số target.

---

## 455.33 — UTF-8 API

Axiom cung cấp UTF-8-friendly path APIs.

---

## 455.34 — Native path

Low-level API có thể expose platform-native path representation.

---

## 455.35 — Path normalization

Normalization phải phân biệt lexical normalization và filesystem resolution.

---

## 455.36 — Canonical path

Canonicalization có thể access filesystem và có failure.

---

## 455.37 — Path traversal

Security-sensitive applications phải có explicit safe-path validation.

---

## 455.38 — Case sensitivity

Filesystem case sensitivity là target/filesystem property.

---

## 455.39 — Filename encoding

Không giả định mọi filesystem có Unicode semantics giống nhau.

---

## 455.40 — Path security

Không tự động coi path từ network/user input là trusted.

---

# 455.41 — Memory-mapped files

API:

```text
MappedFile
MemoryMap
```

---

## 455.42 — Mapping ownership

Mapping owns virtual memory mapping resource.

---

## 455.43 — Read-only mapping

Default-safe mapping có thể là read-only.

---

## 455.44 — Read-write mapping

Mutable mapping phải require writable mapping capability.

---

## 455.45 — Executable mapping

Executable mappings là explicit unsafe/security-sensitive operation.

---

## 455.46 — Mapping range

API hỗ trợ map toàn file hoặc range.

---

## 455.47 — Mapping alignment

Offset phải satisfy platform page/alignment requirements hoặc abstraction tự xử lý.

---

## 455.48 — Mapping lifetime

Mapped view không được outlive mapping.

---

## 455.49 — Mapping flush

Writable mapping hỗ trợ explicit flush.

---

## 455.50 — Mapping invalidation

File resize/truncation trong khi mapped phải được documented platform-dependent behavior và safe API phải ngăn invalid access khi có thể.

---

# 455.51 — Byte storage

Primitive:

```text
[]u8
ByteBuffer
ByteView
```

---

## 455.52 — Owned buffer

Owned buffer quản lý capacity/length deterministic.

---

## 455.53 — Borrowed view

View không sở hữu underlying storage.

---

## 455.54 — Zero-copy parsing

Storage APIs phải tương thích với borrowed views.

---

## 455.55 — Alignment

Byte buffer → typed object conversion phải tuân safety model 445.

---

## 455.56 — Typed storage

Typed storage chỉ được sử dụng nếu alignment/layout/validity được đảm bảo.

---

## 455.57 — Uninitialized storage

`MaybeUninit<T>` có thể được dùng để build low-level storage structures.

---

## 455.58 — Byte order

Storage formats phải define endian.

---

## 455.59 — Native endian

Native-endian serialization phải explicit.

---

## 455.60 — Portable endian

Portable formats phải specify fixed byte order.

---

# 455.61 — File format foundation

Binary file format nên mô tả:

```text
magic
version
flags
header
records
payload
checksum
footer
```

---

## 455.62 — Magic number

File formats có thể dùng magic bytes để nhận dạng.

---

## 455.63 — Version

Format version phải explicit.

---

## 455.64 — Forward compatibility

Readers có thể bỏ qua fields/extensions chưa biết khi format cho phép.

---

## 455.65 — Backward compatibility

Format designers phải define compatibility policy.

---

## 455.66 — Corruption detection

Checksum/hash có thể được dùng.

---

## 455.67 — Integrity vs authenticity

Checksum/hash không đồng nghĩa cryptographic authenticity.

---

## 455.68 — Cryptographic integrity

Authenticated formats có thể dùng MAC/signature ở higher layer.

---

## 455.69 — Chunked formats

Large files có thể dùng chunk/block organization.

---

## 455.70 — Streaming format

Format parser phải có thể xử lý stream khi format cho phép.

---

# 455.71 — Storage blocks

Database engines có thể dùng fixed-size blocks:

```text
BlockId
Block
Page
```

---

## 455.72 — Page size

Page size là storage-engine configuration.

---

## 455.73 — Block header

Block có thể chứa:

```text
type
version
generation
checksum
```

---

## 455.74 — Block checksum

Database engines có thể verify block integrity.

---

## 455.75 — Free-space map

Storage engine có thể maintain free-space metadata.

---

## 455.76 — Page allocator

Page allocation thuộc storage engine.

---

## 455.77 — File growth

File growth policy configurable.

---

## 455.78 — Preallocation

Preallocation có thể giảm fragmentation.

---

## 455.79 — Sparse files

Sparse files là optional platform capability.

---

## 455.80 — Storage fragmentation

Axiom không tự động giả định filesystem/storage fragmentation behavior.

---

# 455.81 — Cache abstraction

```text
Cache<K,V>
```

là library abstraction.

---

## 455.82 — Cache policy

Possible:

```text
LRU
LFU
ARC
clock
custom
```

---

## 455.83 — Cache ownership

Cache owns entries according to generic value ownership rules.

---

## 455.84 — Cache memory limit

Configurable max bytes/entries.

---

## 455.85 — Cache eviction

Eviction phải deterministic theo selected policy.

---

## 455.86 — Persistent cache

Persistent cache là storage engine feature.

---

## 455.87 — Memory cache

Memory-only cache không cần filesystem.

---

## 455.88 — Concurrent cache

Concurrency control phải explicit.

---

## 455.89 — Sharded cache

High-performance cache có thể shard theo hash.

---

## 455.90 — Cache stampede

Higher-level cache libraries có thể provide request coalescing.

---

# 455.91 — Index foundation

Index là data structure, không phải database-specific magic.

---

## 455.92 — B-tree

Standard library/storage ecosystem có thể cung cấp B-tree.

---

## 455.93 — Hash index

Hash table/index hỗ trợ point lookup.

---

## 455.94 — Sorted index

Sorted index hỗ trợ range queries.

---

## 455.95 — Bitmap index

Optional specialized index.

---

## 455.96 — Bloom filter

Optional probabilistic index/filter.

---

## 455.97 — LSM tree

LSM implementation thuộc storage/database layer.

---

## 455.98 — SSTable

Immutable sorted files có thể được dùng bởi LSM engines.

---

## 455.99 — Compaction

Compaction là storage-engine operation.

---

## 455.100 — Compaction scheduling

Không được tự tạo background thread nếu runtime policy không cho phép.

---

# 455.101 — Write-ahead log

WAL là optional storage/database component.

---

## 455.102 — WAL record

Conceptual:

```text
LSN
transaction
operation
payload
checksum
```

---

## 455.103 — WAL append

Append phải có explicit durability semantics.

---

## 455.104 — WAL flush

Database engine quyết định flush policy.

---

## 455.105 — WAL recovery

Recovery replays valid committed/required records.

---

## 455.106 — Torn write detection

Checksum/generation techniques có thể detect incomplete writes.

---

## 455.107 — WAL truncation

WAL segments có thể được checkpoint/truncate khi safe.

---

## 455.108 — WAL retention

Retention policy configurable.

---

## 455.109 — WAL corruption

Corrupt WAL phải produce typed recovery error.

---

## 455.110 — WAL encryption

Encryption là higher-level storage security feature.

---

# 455.111 — Transactions

Transaction abstraction:

```text
Transaction
```

---

## 455.112 — Transaction states

```text
active
committing
committed
aborted
```

---

## 455.113 — Commit

Commit là explicit.

---

## 455.114 — Rollback

Rollback là explicit và cũng có thể xảy ra do transaction drop/error tùy API contract.

---

## 455.115 — Atomicity

Transaction engine phải document atomicity guarantee.

---

## 455.116 — Consistency

Consistency là database-specific invariant, không phải compiler property.

---

## 455.117 — Isolation

Possible isolation levels:

```text
read_uncommitted
read_committed
repeatable_read
snapshot
serializable
```

---

## 455.118 — Isolation semantics

Không được dùng cùng tên nhưng khác semantics giữa database implementations mà không document.

---

## 455.119 — Durability

Durability level phải explicit.

---

## 455.120 — ACID

A database có thể advertise ACID guarantees only when implementation actually provides them.

---

# 455.121 — MVCC

MVCC là optional transaction implementation.

---

## 455.122 — Snapshot

Snapshot có explicit lifetime.

---

## 455.123 — Snapshot isolation

Snapshot must retain required versions safely.

---

## 455.124 — Version cleanup

Old versions có thể được reclaimed sau khi no active snapshot references them.

---

## 455.125 — Transaction ownership

Transaction resources follow deterministic ownership.

---

## 455.126 — Nested transactions

Không giả định nested transaction semantics.

---

## 455.127 — Savepoints

Savepoint là optional higher-level transaction feature.

---

## 455.128 — Deadlocks

Database engine phải detect, timeout hoặc expose deadlock errors tùy design.

---

## 455.129 — Retry transaction

Retry phải explicit.

---

## 455.130 — Transaction cancellation

Cancellation phải leave database in valid state.

---

# 455.131 — Key-value storage

Axiom standard ecosystem có thể cung cấp:

```text
KvStore<K,V>
```

---

## 455.132 — KV operations

```text
get
put
delete
contains
scan
```

---

## 455.133 — Atomic KV update

Storage engine có thể support compare-and-swap/update transaction.

---

## 455.134 — Range scan

Ordered stores support range scan.

---

## 455.135 — Batch operations

Batch writes reduce syscall/storage overhead.

---

## 455.136 — Batch durability

Batch durability semantics phải explicit.

---

## 455.137 — KV serialization

Key/value encoding phải explicit.

---

## 455.138 — No hidden serialization

`put<T>` không được âm thầm serialize bằng arbitrary runtime reflection.

---

## 455.139 — Generated codecs

Comptime-generated codecs được ưu tiên.

---

## 455.140 — Key ordering

Ordered KV stores phải define byte/type ordering.

---

# 455.141 — SQL foundation

SQL parser/query engine là higher-level package.

---

## 455.142 — SQL driver

Database-specific driver:

```text
SqlConnection
SqlTransaction
SqlStatement
SqlRow
```

---

## 455.143 — Parameterized queries

Parameters phải được bind separately.

---

## 455.144 — No string interpolation requirement

Safe database APIs phải cung cấp parameter binding thay vì khuyến khích query concatenation.

---

## 455.145 — Prepared statements

Prepared statement lifecycle phải deterministic.

---

## 455.146 — Result streaming

Large result sets phải hỗ trợ row streaming.

---

## 455.147 — NULL

SQL `NULL` không được map trực tiếp thành Axiom `null`.

Mapping mặc định:

```text
Option<T>
```

---

## 455.148 — SQL types

Driver phải map SQL types sang Axiom types với documented conversion rules.

---

## 455.149 — SQL transaction

SQL transaction map sang storage transaction abstraction.

---

## 455.150 — Connection pooling

Pooling là optional SQL client feature.

---

# 455.151 — ORM

ORM không thuộc standard library core.

---

## 455.152 — Compile-time schema

ORM có thể generate typed models từ schema.

---

## 455.153 — Migration

Migration system là package-level feature.

---

## 455.154 — Migration versioning

Migrations có monotonic identifiers/version.

---

## 455.155 — Migration transactions

Migration atomicity phụ thuộc database capabilities.

---

## 455.156 — Query generation

Comptime có thể generate SQL/query code.

---

## 455.157 — Query validation

Static query validation có thể dùng schema metadata.

---

## 455.158 — Runtime SQL

Dynamic SQL vẫn được hỗ trợ nhưng typed safety thấp hơn.

---

## 455.159 — No mandatory ORM

Raw SQL/database APIs luôn available.

---

## 455.160 — Database abstraction

Generic database traits không được che giấu vendor-specific semantics.

---

# 455.161 — Embedded database

Axiom phải có thể build embedded database hoàn toàn native.

---

## 455.162 — Single-file database

Có thể xây database sử dụng một file.

---

## 455.163 — Multi-file database

Storage engine có thể sử dụng multiple data/WAL/index files.

---

## 455.164 — Server database

Database server chạy như ordinary Axiom executable.

---

## 455.165 — Embedded/server shared engine

Engine core có thể dùng chung giữa embedded và server mode.

---

## 455.166 — No database daemon requirement

Embedded database không cần external daemon.

---

## 455.167 — Database process model

Server mode sử dụng normal process/thread/async primitives 424.

---

## 455.168 — Database memory model

Engine có thể chọn arena/pool/custom allocator.

---

## 455.169 — Database zero-copy

Mapped pages/views có thể được sử dụng khi safe.

---

## 455.170 — Database resource ownership

Connection, transaction, cursor, statement, page pin đều phải có deterministic lifetime.

---

# 455.171 — Cursor

Cursor là owned/borrowed resource tùy implementation.

---

## 455.172 — Cursor invalidation

Mutation có thể invalidate cursor; semantics phải explicit.

---

## 455.173 — Iterator

Database scans có thể expose Axiom iterator abstraction.

---

## 455.174 — Streaming

Database result iteration không bắt buộc materialize entire result.

---

## 455.175 — Backpressure

Async database streams phải support backpressure.

---

## 455.176 — Cancellation

Cancelled query phải cleanup database resources.

---

## 455.177 — Query timeout

Database client có explicit timeout.

---

## 455.178 — Statement timeout

Có thể có query/statement-specific deadline.

---

## 455.179 — Resource quotas

Database server có thể giới hạn:

```text
connections
memory
query size
result size
transaction duration
```

---

## 455.180 — No hidden resource growth

Database library không được silently create unbounded caches/threads.

---

# 455.181 — Storage concurrency

Multiple readers có thể coexist tùy engine.

---

## 455.182 — Writer serialization

Nếu engine chỉ support một writer, semantics phải explicit.

---

## 455.183 — Lock manager

Lock manager là database implementation feature.

---

## 455.184 — Lock ordering

Internal lock ordering phải deterministic để giảm deadlocks.

---

## 455.185 — Atomic file operations

Engine có thể rely on OS atomic rename/create primitives.

---

## 455.186 — Crash consistency

Storage engine phải document assumptions về filesystem durability.

---

## 455.187 — Power-loss durability

`fsync`/equivalent guarantees khác với hardware power-loss guarantees.

---

## 455.188 — Recovery testing

Database engines phải test crash/recovery paths.

---

## 455.189 — Fault injection

Có thể inject failures:

```text
short write
sync failure
disk full
corrupt block
process crash
```

---

## 455.190 — Recovery determinism

Given identical WAL/storage state, recovery result phải deterministic.

---

# 455.191 — Encryption at rest

Encryption không thuộc file primitive bắt buộc.

---

## 455.192 — Encrypted storage

Database/file libraries có thể provide encrypted storage.

---

## 455.193 — Key management

Encryption key management tách khỏi storage engine.

---

## 455.194 — Secure deletion

Filesystem overwrite không đảm bảo secure deletion trên mọi storage medium.

API phải document limitation.

---

## 455.195 — File permissions

Security-sensitive files phải set restrictive permissions where supported.

---

## 455.196 — Temporary storage

Temporary storage phải avoid predictable names.

---

## 455.197 — Path sandbox

Applications cần sandbox phải implement explicit root/capability policy.

---

## 455.198 — Untrusted databases

Opening an untrusted database/file phải được coi là untrusted input.

---

## 455.199 — Corruption handling

Corruption phải return error, không UB.

---

## 455.200 — Parser safety

Storage format parsers obey same safety boundary 445.

---

# 455.201 — Storage performance

Benchmark dimensions:

```text
sequential read
random read
sequential write
random write
IOPS
throughput
latency
fsync latency
allocation
memory mapping
cache hit rate
```

---

## 455.202 — Database benchmarks

Đo:

```text
insert
point lookup
range scan
update
delete
transaction commit
recovery
concurrent workload
```

---

## 455.203 — Benchmark workload

Database benchmark phải record dataset size và distribution.

---

## 455.204 — Cache-aware benchmark

Hot-cache và cold-cache cases phải phân biệt.

---

## 455.205 — Storage device metadata

Benchmark record device/filesystem khi relevant.

---

## 455.206 — Durability benchmark

Durability workloads phải measure sync/commit cost separately.

---

## 455.207 — Memory budget

Database benchmark record peak resident memory.

---

## 455.208 — Allocation budget

Count heap allocations khi có thể.

---

## 455.209 — Binary size

Database feature linking phải obey binary-size model 450.

---

## 455.210 — Performance attribution

AI metadata có thể identify:

```text
parser
index
cache
WAL
syscall
serialization
lock
```

cost.

---

# 455.211 — Storage compiler integration

Compiler không cần biết SQL semantics.

---

## 455.212 — Comptime codecs

Compiler chỉ cần hỗ trợ generic/comptime/codegen primitives.

---

## 455.213 — Layout-aware storage

Storage libraries có thể query:

```text
sizeof<T>()
alignof<T>()
offsetof()
```

---

## 455.214 — Stable disk layout

Disk serialization phải define riêng, không assume Axiom in-memory layout stable across compiler versions.

---

## 455.215 — Packed representation

Explicit `@repr` có thể hỗ trợ interoperability nhưng không tự tạo durable file-format guarantee.

---

## 455.216 — Schema metadata

Semantic metadata 446 có thể feed code generators.

---

## 455.217 — Generic serialization

Generic codecs được monomorphized.

---

## 455.218 — Specialized serialization

Comptime có thể generate field-specific optimized serializers.

---

## 455.219 — SIMD codecs

SIMD acceleration có thể được sử dụng bởi storage parsers/codecs.

---

## 455.220 — GPU storage processing

GPU processing là optional specialized ecosystem feature, không core storage behavior.

---

# 455.221 — Database AI integration

AI semantic tooling có thể query:

```text
database connection
query
transaction
table model
serialization
migration
index
WAL
```

---

## 455.222 — Query dependency graph

Tooling có thể map:

```text
handler
→ repository
→ query
→ table/index
```

---

## 455.223 — Schema diff

Generated schema metadata có thể hỗ trợ schema diff.

---

## 455.224 — Migration impact analysis

AI/tooling có thể xác định source locations phụ thuộc schema.

---

## 455.225 — Storage safety graph

Metadata có thể show:

```text
network input
→ deserialize
→ database write
```

---

## 455.226 — Transaction diagnostics

Compiler/tooling không tự chứng minh database-level consistency; chỉ report static contracts có metadata.

---

## 455.227 — Generated database code

Generated source phải retain provenance.

---

## 455.228 — Build cache

Generated codecs/schema bindings cache theo content hash.

---

## 455.229 — Deterministic generation

Schema-to-code generation phải deterministic.

---

## 455.230 — External schema tools

External SQL/schema generators được phép nhưng không phải compiler dependency.

---

# 455.231 — Native database engines

Axiom phải có khả năng viết database engine native mà không cần:

```text
GC
LLVM
C runtime
C++ runtime
third-party compiler
```

---

## 455.232 — Direct syscall/storage backend

Engine có thể sử dụng Axiom platform APIs hoặc native syscall layer.

---

## 455.233 — Custom allocator

Database có thể dùng:

```text
arena
pool
slab
page allocator
custom allocator
```

---

## 455.234 — Memory locality

Language/runtime không được ngăn storage engine kiểm soát memory layout.

---

## 455.235 — Cache locality

Contiguous/packed data structures được hỗ trợ.

---

## 455.236 — Pointer-free high-level storage

Database APIs cấp cao không cần expose raw pointers.

---

## 455.237 — Low-level storage

Engine implementation có thể dùng raw pointers trong explicit unsafe layer.

---

## 455.238 — Lock-free structures

Database engine có thể implement lock-free structures bằng atomic primitives 424.

---

## 455.239 — NUMA

High-performance storage servers có thể use NUMA-aware allocation.

---

## 455.240 — Thread affinity

Storage engine có thể use explicit thread affinity.

---

# 455.241 — Crash recovery

Recovery pipeline:

```text
open
→ validate header
→ scan WAL
→ validate records
→ identify committed state
→ replay
→ rebuild indexes if necessary
→ checkpoint
→ ready
```

---

## 455.242 — Recovery idempotency

Recovery operations phải tránh duplicate application của non-idempotent records.

---

## 455.243 — Checkpoint

Checkpoint giảm recovery work.

---

## 455.244 — Incremental checkpoint

Có thể checkpoint incremental.

---

## 455.245 — Full checkpoint

Có thể checkpoint toàn bộ relevant state.

---

## 455.246 — Recovery progress

Large recovery có thể expose progress.

---

## 455.247 — Recovery cancellation

Cancellation phải để storage ở state an toàn.

---

## 455.248 — Recovery failure

Nếu không thể recover, database phải remain closed/invalid rather than expose partially trusted state.

---

## 455.249 — Backup

Backup API là higher-level database feature.

---

## 455.250 — Online backup

Online backup phải document consistency guarantee.

---

# 455.251 — Snapshot/export

Storage engine có thể expose consistent snapshot/export.

---

## 455.252 — Import

Import phải validate data before making it authoritative.

---

## 455.253 — Bulk loading

Bulk load API có thể bypass per-record overhead nhưng phải document durability semantics.

---

## 455.254 — Compaction safety

Compaction không được discard data visible to active snapshots.

---

## 455.255 — Garbage collection terminology

Storage-engine garbage collection/compaction **không phải language GC**.

Axiom language vẫn không có mandatory GC.

---

# 455.256 — Hard invariants

1. Database không thuộc language core.
2. Database không thuộc mandatory runtime.
3. File là deterministic resource-owning abstraction.
4. File close phải deterministic.
5. Partial read/write phải được model đúng.
6. Random access phải được hỗ trợ.
7. Positional I/O phải được hỗ trợ khi platform cho phép.
8. File durability phải phân biệt với ordinary write.
9. Explicit sync operations phải tồn tại.
10. Directory traversal phải hỗ trợ streaming.
11. Path không phải đơn giản là String.
12. UTF-8 path API phải tồn tại.
13. Native path representation phải khả dụng khi cần.
14. Symlink semantics phải explicit.
15. Filesystem case sensitivity không được hard-code.
16. User/network-supplied paths được coi là untrusted.
17. Memory mapping phải có explicit ownership.
18. Mapping lifetime phải bao phủ mọi view.
19. Executable mappings là explicit unsafe capability.
20. Writable mappings phải có explicit semantics.
21. Byte buffers phải integrate ownership/view model.
22. Typed reinterpretation phải obey safety model 445.
23. Disk layout không được tự động phụ thuộc native memory layout.
24. Binary formats phải có versioning.
25. Format corruption phải được detect khi format hỗ trợ integrity metadata.
26. Integrity và authenticity phải được phân biệt.
27. Large files phải có streaming/chunking options.
28. Storage blocks/pages là storage-engine abstractions.
29. Cache là optional library abstraction.
30. Cache policy phải explicit.
31. Cache memory limits phải configurable.
32. Indexes là reusable data structures.
33. B-tree/hash/range index có thể coexist.
34. WAL là optional storage component.
35. WAL durability semantics phải explicit.
36. WAL recovery phải deterministic.
37. Corrupt WAL phải return typed error.
38. Transactions phải có explicit lifecycle.
39. Commit phải explicit.
40. Rollback phải defined.
41. Atomicity phải được document.
42. Isolation semantics phải được document.
43. Durability level phải explicit.
44. ACID claims chỉ được đưa ra khi implementation đảm bảo chúng.
45. MVCC là optional implementation.
46. Snapshot lifetime phải deterministic.
47. Old versions chỉ được reclaim khi safe.
48. Deadlock behavior phải được document.
49. Transaction retry phải explicit.
50. Cancellation không được corrupt database state.
51. KV storage là library layer.
52. KV serialization phải explicit.
53. Không hidden reflection-based serialization.
54. Comptime-generated codecs được ưu tiên.
55. SQL là higher-level package.
56. SQL parameters phải hỗ trợ binding.
57. Prepared statements phải có deterministic lifecycle.
58. SQL NULL map tự nhiên sang `Option<T>`.
59. SQL result streaming phải được hỗ trợ.
60. Connection pooling là optional.
61. ORM không thuộc core.
62. Raw SQL/database API phải luôn khả dụng.
63. ORM/schema generation có thể dùng comptime.
64. Migration phải versioned.
65. Embedded database phải khả dụng.
66. Database server có thể là ordinary Axiom executable.
67. Embedded database không cần external daemon.
68. Connection/cursor/statement/transaction lifetime phải deterministic.
69. Database scans phải hỗ trợ streaming.
70. Async database streams phải có backpressure.
71. Query timeout phải explicit.
72. Database resource quotas có thể được cấu hình.
73. Không hidden unbounded cache/thread/resource growth.
74. Concurrent storage semantics phải explicit.
75. Crash consistency phải được document.
76. Filesystem durability assumptions phải explicit.
77. Power-loss guarantees không được giả định vượt OS/hardware guarantees.
78. Crash/recovery phải được test.
79. Fault injection phải được hỗ trợ.
80. Encryption-at-rest không thuộc file primitive bắt buộc.
81. Key management tách storage engine.
82. Secure deletion limitations phải được document.
83. Temporary resources phải có secure creation.
84. Corrupt/untrusted storage input không được tạo UB trong safe code.
85. Storage parser phải bounds-safe.
86. Storage benchmark phải đo throughput và latency.
87. Cold-cache/hot-cache workloads phải phân biệt.
88. Durability cost phải được đo riêng.
89. Memory/allocation usage phải đo được.
90. Database feature linking phải giữ binary-size discipline.
91. Compiler không cần hiểu SQL semantics.
92. Comptime có thể generate storage codecs.
93. `sizeof/alignof/offsetof` hỗ trợ low-level storage libraries.
94. Native in-memory representation không tự trở thành stable disk format.
95. SIMD có thể accelerate serialization/parsing.
96. GPU storage processing là optional ecosystem feature.
97. AI tooling phải query được database/storage relationships.
98. Schema-generated code phải có provenance.
99. Schema/code generation phải deterministic.
100. External schema tools không trở thành compiler dependency.
101. Axiom có thể xây native database engine không cần GC.
102. Axiom có thể xây native database engine không cần LLVM/GCC/Clang.
103. Axiom có thể xây database engine không cần C/C++ runtime.
104. Custom allocator phải khả dụng.
105. Memory locality phải được kiểm soát bởi storage engine.
106. Raw pointer low-level storage implementation nằm trong explicit unsafe layer.
107. Lock-free storage structures có thể dùng atomic primitives.
108. NUMA/storage affinity là platform optimization.
109. Recovery phải validate trước khi expose database state.
110. Recovery phải deterministic.
111. Recovery phải có checkpoint support.
112. Recovery failure không được expose partially trusted state.
113. Backup consistency semantics phải explicit.
114. Online backup phải document snapshot guarantees.
115. Bulk loading phải document durability semantics.
116. Compaction phải respect active snapshots.
117. Storage-engine compaction không được nhầm với language garbage collection.
118. **Axiom storage architecture phải đủ thấp để xây database engine, nhưng đủ cao để application developer có filesystem, mmap, KV và SQL APIs mà không phải mang theo một runtime/database stack không sử dụng.**

**BOOTSTRAP-455 hoàn tất.**

---

# BOOTSTRAP-456 — CRYPTOGRAPHY, HASHING, RANDOMNESS, KEY MANAGEMENT & SECURE-COMPUTING PRIMITIVES

Task kế tiếp khóa nền tảng security primitives:

```text
hash
checksum
MAC
HMAC
AEAD
symmetric encryption
public-key cryptography
signatures
key derivation
secure random
constant-time operations
key storage
secure memory
```

với nguyên tắc:

```text
Axiom Core
    ↓
safe low-level primitives
    ↓
crypto library
    ↓
TLS / authentication / encrypted storage
```

Crypto sẽ **không được tự động đưa vào runtime**, và compiler chỉ chịu trách nhiệm cung cấp các primitive cần thiết cho implementation hiệu năng cao và có thể kiểm soát timing khi developer yêu cầu.

**BOOTSTRAP-456 bắt đầu ở lượt tiếp theo.**