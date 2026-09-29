Tiếp tục với **BOOTSTRAP-612**, tập trung xây lớp dữ liệu nhị phân và structured storage trên nền Storage 611, nhưng vẫn giữ ranh giới rõ ràng để sau này có thể xây database mà không làm phình core.

:::writing{variant="document" id="42681" title="BOOTSTRAP-612 — Native Serialization, Binary Data Model, Schema Evolution, Persistent Collections & Embedded Structured Storage Runtime 5.0"}
# BOOTSTRAP-612 — Native Serialization, Binary Data Model, Schema Evolution, Persistent Collections & Embedded Structured Storage Runtime 5.0

**Status:** Architecture Specification — Implementable  
**Layer:** Native Data / Persistence Runtime  
**Depends on:** BOOTSTRAP-600..611  
**Primary dependency:** BOOTSTRAP-611 Storage  
**Consumers:** Application State, Configuration, IPC, Networking, Cache, Database, AI Metadata, Package Systems

---

# 1. Purpose

BOOTSTRAP-612 defines Axiom's native structured-data and serialization layer.

The layer converts Axiom values into deterministic binary representations and provides primitives for persistent structured data.

It covers:

- binary serialization
- deserialization
- schema representation
- schema IDs
- schema evolution
- compatibility
- primitive encoding
- strings
- arrays
- structs
- enums
- options/results
- maps
- tagged unions
- streaming serialization
- zero-copy decoding
- borrowed views
- persistent collections
- append-only logs
- write-ahead logging
- checksums
- integrity metadata
- embedded key-value storage
- indexing primitives
- compact record storage
- compiler-generated serializers
- schema metadata
- durable structured state

It does **not** turn Axiom's core runtime into a mandatory database runtime.

---

# 2. Architectural Position

The stack becomes:

```text
Application
    │
    ├── Domain Objects
    │
    ▼
Serialization / Structured Data
    │
    ├── Binary Codec
    ├── Schema
    ├── Persistent Collections
    ├── WAL
    └── KV Storage
    │
    ▼
Storage Transactions
    │
    ▼
BOOTSTRAP-611
    │
    ├── Files
    ├── mmap
    ├── durability
    ├── atomic replace
    └── VFS
    │
    ▼
Operating System
```

---

# 3. Fundamental Principle

Axiom separates:

```text
Value
Schema
Encoding
Storage
Query
```

They are not the same abstraction.

For example:

```text
User
 ↓
UserSchema
 ↓
BinaryEncoder
 ↓
[]u8
 ↓
File
```

A database layer may later add:

```text
Index
Query
Transaction
```

without modifying the basic serialization model.

---

# 4. Non-Goals

BOOTSTRAP-612 does not require:

- SQL
- ORM
- reflection-heavy runtime
- dynamic object metadata
- JSON as the canonical binary format
- garbage collection
- mandatory heap allocation
- mandatory database engine
- distributed transactions
- distributed consensus
- automatic schema migration
- automatic object graph persistence

---

# 5. Core Design Goals

1. Native speed.
2. Compact representation.
3. Deterministic encoding.
4. Explicit schema.
5. Versionable data.
6. Safe decoding.
7. Zero-copy where possible.
8. Streaming support.
9. Compiler-generated codecs.
10. No mandatory reflection runtime.
11. No mandatory GC.
12. No hidden allocation for simple serialization.
13. Stable persistent representation.
14. Cross-platform representation.
15. AI-readable metadata.
16. Clear ABI boundaries.
17. Storage independence.
18. Network independence.

---

# 6. Binary Representation

Axiom's canonical binary representation is called:

```text
AXBIN
```

AXBIN is a logical encoding specification, not necessarily a single physical container.

It defines:

- integer encoding
- floating-point encoding
- string encoding
- byte sequence encoding
- arrays
- maps
- structs
- enums
- optional values
- tagged unions
- schema identifiers

---

# 7. Canonical Encoding

For a given schema and value:

```text
encode(schema, value)
```

must produce exactly one canonical byte sequence unless the schema explicitly declares an alternative encoding.

Therefore:

```text
encode(x) == encode(x)
```

for the same logical value and schema.

This is important for:

- hashing
- signatures
- caching
- deduplication
- reproducible builds
- persistent indexes.

---

# 8. Endianness

AXBIN uses:

```text
Little-endian
```

for fixed-width numeric fields.

Variable-length integer encodings are endian-independent.

The host CPU's native endianness does not change AXBIN representation.

---

# 9. Integer Types

Supported canonical types:

```text
u8
u16
u32
u64
u128
i8
i16
i32
i64
i128
usize
isize
```

`usize` and `isize` require special handling for persistent schemas.

They should not normally appear in long-lived portable schemas.

---

# 10. Portable Integer Rule

Persistent schemas should use:

```text
u32
u64
i32
i64
```

instead of:

```text
usize
isize
```

because pointer width may differ between targets.

The compiler should warn when architecture-dependent types are used in persistent schemas.

---

# 11. Fixed-Width Encoding

Example:

```text
u32 = 4 bytes
u64 = 8 bytes
```

Fixed-width encoding is used when predictable offsets are valuable.

---

# 12. Variable-Length Integers

AXBIN supports:

```text
varuint
varint
```

for compact values.

Typical small values require fewer bytes.

---

# 13. Signed Integer Encoding

Signed variable integers use ZigZag-style transformation:

```text
0  → 0
-1 → 1
1  → 2
-2 → 3
2  → 4
```

This keeps small negative numbers compact.

---

# 14. Boolean

Canonical boolean:

```text
0 = false
1 = true
```

Other encoded values are invalid.

This prevents multiple byte representations of the same logical value.

---

# 15. Floating Point

AXBIN supports:

```text
f32
f64
```

using IEEE-754 bit representation.

NaN canonicalization is required for canonical serialization.

---

# 16. NaN Canonicalization

Different NaN payloads may represent the same logical NaN.

Canonical encoding maps them to a single representation.

This is required for deterministic hashing.

---

# 17. String

Canonical strings are UTF-8.

Encoding:

```text
length
UTF-8 bytes
```

The length is encoded separately from the bytes.

---

# 18. UTF-8 Validation

Decoders must reject malformed UTF-8 when decoding into `String`.

A raw byte sequence may instead be decoded into:

```text
Bytes
```

without UTF-8 validation.

---

# 19. Bytes

Binary data is represented as:

```text
Bytes
```

and must not be interpreted as text.

---

# 20. Length Prefix

Variable-sized values use bounded length prefixes.

The decoder must check:

```text
declared_length <= remaining_input
```

before allocation or access.

---

# 21. Resource Safety

A malicious serialized value must not cause:

- integer overflow
- unbounded allocation
- recursion exhaustion
- stack overflow
- infinite loops
- quadratic parsing

without crossing an explicit resource limit.

---

# 22. Decode Limits

A decoder has:

```axiom
DecodeLimits {
    max_bytes
    max_depth
    max_string
    max_array
    max_map
    max_allocations
}
```

Limits are mandatory for untrusted input.

---

# 23. Struct Encoding

A struct can use field IDs:

```axiom
struct User {
    id: u64
    name: String
    age: u32
}
```

Persistent encoding should use stable field identifiers rather than source declaration position alone.

---

# 24. Field IDs

Example:

```axiom
struct User {
    @id(1)
    id: u64

    @id(2)
    name: String

    @id(3)
    age: u32
}
```

Field IDs become part of the persistent schema.

---

# 25. Field ID Stability

Once published:

```text
field_id = 2
```

must not be silently reused for a different semantic field.

The compiler should reject incompatible reuse.

---

# 26. Unknown Fields

A decoder encountering an unknown field should normally:

```text
skip
```

rather than fail.

This enables forward compatibility.

---

# 27. Unknown Field Preservation

Optional decoding modes may preserve unknown fields:

```axiom
DynamicFields
```

This is useful for gateways and schema migration tools.

Core decoding does not require preservation.

---

# 28. Optional Values

```axiom
Option<T>
```

is encoded as:

```text
presence
value?
```

Example:

```text
0 = None
1 = Some
```

---

# 29. Result Values

`Result<T,E>` uses explicit variant IDs.

```text
Success
Error
```

must not be inferred from payload shape.

---

# 30. Enum Encoding

Example:

```axiom
enum Status {
    Pending
    Running
    Complete
}
```

Persistent variants should have stable IDs:

```axiom
enum Status {
    @id(1) Pending
    @id(2) Running
    @id(3) Complete
}
```

---

# 31. Enum Evolution

A new enum variant may be added.

Removing an old variant is a breaking change unless a compatibility/migration strategy exists.

---

# 32. Tagged Unions

Axiom's tagged unions use:

```text
variant_id
payload
```

The decoder validates the variant before decoding its payload.

---

# 33. Arrays

Arrays use:

```text
length
elements...
```

For fixed-size primitive arrays, codecs may use contiguous native-compatible representation where explicitly allowed.

---

# 34. Fixed Arrays

A fixed array:

```axiom
[u32; 16]
```

does not need a length prefix if the schema already establishes its size.

---

# 35. Maps

Maps encode:

```text
count
key
value
key
value
...
```

Canonical map encoding requires deterministic key ordering.

---

# 36. Canonical Map Ordering

For canonical serialization, keys are ordered by their canonical encoded byte representation.

This avoids dependence on:

- hash table order
- memory address
- insertion order
- runtime implementation.

---

# 37. Sets

Sets use the same canonical ordering rule as maps.

---

# 38. Optional Compact Collections

The runtime may provide:

```text
PackedArray
BitSet
SmallMap
CompactMap
```

but these are representation optimizations rather than new semantic types.

---

# 39. Struct Padding

Native struct memory layout must not automatically become persistent layout.

Example:

```text
memory struct ≠ serialized struct
```

This prevents compiler optimization and alignment changes from breaking files.

---

# 40. Native Layout Encoding

For specialized high-performance data, explicit:

```text
@repr(native)
```

may request native-compatible layout.

Such data is architecture-specific and must declare:

```text
architecture
endianness
alignment
ABI
```

metadata.

---

# 41. Portable vs Native Serialization

Two modes:

```text
Portable
Native
```

Portable is the default.

Native is intended for:

- memory-mapped databases
- shared-memory systems
- same-build IPC
- temporary caches.

---

# 42. Schema Identity

Every persistent schema has:

```text
SchemaId
SchemaVersion
```

Schema ID should be derived from stable schema identity.

---

# 43. Schema ID Algorithm

The logical schema descriptor is canonicalized and hashed.

Conceptually:

```text
SchemaId = Hash(
    type identity +
    field IDs +
    field types +
    variant IDs +
    compatibility attributes
)
```

The exact cryptographic hash is defined by the schema subsystem.

---

# 44. Schema Version

Schema version is explicit:

```text
major
minor
patch
```

Semantic compatibility rules determine whether versions can interoperate.

---

# 45. Schema Descriptor

A schema descriptor contains:

```text
schema_id
version
type_name
fields
field_ids
field_types
attributes
compatibility_rules
```

---

# 46. AI-Readable Schema

Compiler artifacts should expose schema metadata in machine-readable form:

```text
.axschema
```

Example:

```text
type User
field 1 id:u64
field 2 name:String
field 3 age:u32
```

The format must be deterministic.

---

# 47. Generated Codec

The compiler generates:

```axiom
User.encode(...)
User.decode(...)
```

or equivalent free functions:

```axiom
encode_user(...)
decode_user(...)
```

The implementation remains struct/function based.

---

# 48. No Reflection Requirement

Normal serialization does not require runtime reflection.

The compiler knows the structure at compile time.

This keeps:

- binary size low
- runtime overhead low
- generated code predictable.

---

# 49. Generic Serialization

A generic trait:

```axiom
trait Serialize {
    fn encode(self, encoder: Encoder)
}
```

may be compiler-generated.

---

# 50. Deserialize Trait

```axiom
trait Deserialize {
    fn decode(decoder: Decoder) -> Result<Self>
}
```

The compiler can synthesize implementations.

---

# 51. Schema Trait

Optional:

```axiom
trait Schema {
    fn schema() -> SchemaDescriptor
}
```

The descriptor may be compile-time generated.

---

# 52. Compile-Time Schema Generation

Example:

```axiom
@serializable
struct User {
    @id(1) id: u64
    @id(2) name: String
}
```

The compiler generates:

```text
UserEncoder
UserDecoder
UserSchema
```

without a reflection database.

---

# 53. Generated Code Specialization

The compiler may specialize codecs for:

- fixed-size structs
- primitive arrays
- packed fields
- contiguous byte ranges
- zero-copy strings
- zero-copy arrays

---

# 54. Zero-Copy Decoder

For immutable input:

```axiom
let view = UserView.decode(bytes)?;
```

fields may reference the input buffer.

This is distinct from owning:

```text
User
```

---

# 55. Borrowed View

A view has a lifetime tied to the source buffer.

Conceptually:

```text
Bytes
  ↓
UserView<'buffer>
```

The compiler must prevent the view from outliving the backing storage.

This is one of the limited places where lifetime analysis is required.

It does not require a general borrow checker for the entire language.

---

# 56. Owned Decode

```axiom
let user = User.decode(bytes)?;
```

produces owned data.

The decoder may allocate only when the target representation requires ownership.

---

# 57. Streaming Decoder

```axiom
Decoder.read(stream)
```

supports input larger than memory.

It must handle:

- partial reads
- incomplete frames
- cancellation
- limits
- malformed input.

---

# 58. Streaming Encoder

```axiom
Encoder.write(stream, value)
```

should avoid constructing a complete intermediate buffer when possible.

---

# 59. Incremental Decoding

Decoder state may be:

```text
NeedData
Ready
Error
Complete
```

This supports network and IPC streams.

---

# 60. Framing

A stream needs boundaries.

AXBIN frames can contain:

```text
magic
version
schema_id
payload_length
payload
checksum?
```

---

# 61. Frame Header

Canonical frame:

```text
AXBF
version
flags
schema_id
payload_length
```

The header is intentionally simple.

---

# 62. Maximum Frame Size

The decoder must enforce:

```text
max_frame_size
```

before allocating payload storage.

---

# 63. Checksum

Optional integrity:

```text
CRC
Hash
MAC
```

Checksum is not cryptographic authentication.

---

# 64. Authentication

Authenticated storage/network formats use BOOTSTRAP-610.

The serialization layer does not invent its own cryptographic key management.

---

# 65. Compression

AXBIN frames may specify compression:

```text
None
LZ4
Zstd
Custom
```

but compression is optional.

The core runtime should not require a compression library.

---

# 66. Compression Boundary

Compression is represented as:

```text
Encoder
 ↓
Compressor
 ↓
Storage
```

rather than embedding compression deeply into every serializer.

---

# 67. Schema Evolution

Supported compatible operations:

- add optional field
- add field with default
- add enum variant
- widen certain numeric fields where explicitly declared
- add metadata
- reorder source fields

---

# 68. Breaking Operations

Potentially breaking:

- change field ID
- incompatible type change
- reuse field ID
- remove required field
- change enum variant ID
- change canonical representation without versioning

---

# 69. Default Values

New fields can declare:

```axiom
@default(0)
count: u64
```

or a compile-time constant/default function where deterministic.

---

# 70. Required Fields

A schema may declare:

```axiom
@required
id: u64
```

Missing required fields cause decode failure unless migration rules supply them.

---

# 71. Compatibility Modes

```text
Strict
BackwardCompatible
ForwardCompatible
LosslessForward
Migration
```

The application selects the required mode.

---

# 72. Migration

Schema migration is explicit:

```axiom
migrate<UserV1, UserV2>(old)
```

No hidden migration should occur during ordinary decode.

---

# 73. Migration Registration

A schema can register:

```text
V1 → V2
V2 → V3
```

Migration chains can be compiled.

---

# 74. Migration Safety

Migration code is ordinary Axiom code.

It must not be silently executed merely because a file is opened unless the caller explicitly requests migration.

---

# 75. Schema Fingerprint

A serialized object may contain:

```text
SchemaId
```

allowing the decoder to reject incompatible data early.

---

# 76. Self-Describing Data

Two modes:

```text
SelfDescribing
SchemaExternal
```

Self-describing data includes schema identity.

External-schema data omits repeated schema information for compactness.

---

# 77. Persistent Collection Model

BOOTSTRAP-612 provides foundational persistent collections:

```text
PersistentVector
PersistentMap
PersistentSet
PersistentLog
```

They are optimized for storage rather than purely functional language semantics.

---

# 78. Persistent Vector

A persistent vector uses tree/block storage rather than copying the entire collection for every modification.

---

# 79. Persistent Map

Persistent map can use:

```text
BTree
HashTree
SortedTree
```

depending on requested properties.

---

# 80. B-Tree

B-tree is appropriate for:

- ordered keys
- range queries
- filesystem-like indexes
- predictable page locality.

---

# 81. LSM Boundary

LSM trees are optional.

They are useful for:

- high write rates
- append-heavy workloads
- SSD workloads

but add compaction complexity.

They belong to the structured storage module rather than the absolute serialization core.

---

# 82. Page Model

Structured storage uses fixed-size pages:

```text
4 KiB
8 KiB
16 KiB
32 KiB
64 KiB
```

The actual size is configurable.

---

# 83. Page Header

A persistent page may contain:

```text
magic
format_version
page_id
generation
flags
payload_length
checksum
```

---

# 84. Page Checksum

Each page can have an integrity checksum.

Corrupt pages must produce:

```text
StorageCorrupt
```

rather than undefined behavior.

---

# 85. Page Alignment

Page size must align with the selected storage backend where possible.

Direct I/O may impose stronger requirements.

---

# 86. Page Cache

The structured storage engine may use:

```text
PageCache
```

built on BOOTSTRAP-611 resource accounting.

The cache must distinguish:

```text
clean
dirty
pinned
evictable
```

pages.

---

# 87. Dirty Page Management

Dirty pages are flushed according to:

```text
explicit commit
checkpoint
memory pressure
shutdown
policy
```

A dirty page is not automatically durable.

---

# 88. Write-Ahead Logging

Structured storage supports WAL:

```text
modify page
    ↓
write WAL record
    ↓
sync WAL
    ↓
modify/flush page
    ↓
commit
```

---

# 89. WAL Rule

A page modification must not become durable before its corresponding WAL record when WAL durability is required.

This is the fundamental WAL invariant.

---

# 90. WAL Record

A record contains:

```text
LSN
transaction_id
page_id
operation
before/after metadata
payload
checksum
```

---

# 91. LSN

Log Sequence Number:

```text
LSN
```

is monotonically increasing within one storage instance.

---

# 92. WAL Recovery

Recovery:

```text
read checkpoint
↓
scan WAL
↓
validate checksums
↓
identify committed transactions
↓
redo required operations
↓
discard incomplete operations
```

---

# 93. Undo Logging

The first Axiom implementation does not require general undo logging.

Redo WAL + copy-on-write/atomic replacement is preferred where possible.

---

# 94. Checkpoint

A structured storage checkpoint records:

```text
last durable LSN
root page
schema version
generation
```

---

# 95. Atomic Root Update

The database/storage root pointer can be updated through BOOTSTRAP-611 atomic replacement or a durable page protocol.

---

# 96. Transaction Model

Structured storage transactions provide:

```text
Begin
Read
Write
Commit
Abort
```

with explicit durability.

---

# 97. Transaction Isolation

Core embedded storage initially supports:

```text
SingleWriter
SnapshotRead
```

rather than attempting a complete distributed-style isolation model.

---

# 98. Single Writer

Only one writer transaction modifies a storage instance at a time.

This dramatically simplifies:

- locking
- WAL
- recovery
- deadlock behavior.

Multiple readers remain possible.

---

# 99. Concurrent Readers

Readers can access a consistent snapshot.

Snapshot identity:

```text
generation / root page
```

---

# 100. Writer Lock

The writer lock uses BOOTSTRAP-608 synchronization primitives.

Cross-process storage can use BOOTSTRAP-611 file locking.

---

# 101. Transaction Generation

Each commit advances:

```text
StorageGeneration
```

Readers identify the generation they observe.

---

# 102. Snapshot Lifetime

A snapshot prevents required pages from being reclaimed until all readers release it.

The resource governor tracks pinned storage pages.

---

# 103. Copy-on-Write

An alternative to in-place mutation:

```text
old page
   ↓
new page
   ↓
new root
```

This simplifies snapshot semantics.

---

# 104. Page Reclamation

Old pages are reclaimed only after no active snapshot can reference them.

---

# 105. Free Space Map

Persistent storage tracks reusable pages through:

```text
FreePageMap
```

or equivalent extent structures.

---

# 106. Extents

Large allocations use extents:

```text
start_page
page_count
```

rather than individual page records.

---

# 107. Storage Allocation

Allocation must be:

- bounded
- resource-accounted
- crash-safe
- deterministic where possible.

---

# 108. Append-Only Log

Axiom provides:

```axiom
PersistentLog<T>
```

optimized for:

- event streams
- audit records
- checkpoints
- queues
- append-only state.

---

# 109. Log Record

Each record contains:

```text
sequence
timestamp?
schema_id
payload_length
payload
checksum
```

Timestamp is optional.

---

# 110. Log Truncation

Applications can checkpoint:

```text
last_processed_sequence
```

and truncate old segments.

---

# 111. Segmented Logs

Large logs are split into:

```text
segment-000001
segment-000002
...
```

This simplifies:

- deletion
- compaction
- parallel reads.

---

# 112. Key-Value Storage

A minimal embedded store:

```axiom
KvStore<K,V>
```

provides:

```text
get
put
remove
contains
scan
commit
```

---

# 113. Key Requirements

Keys must have:

- deterministic encoding
- bounded size
- stable schema
- comparable representation where ordered indexes are used.

---

# 114. Value Requirements

Values are arbitrary AXBIN-compatible types.

---

# 115. Key-Value Transaction

```axiom
let tx = db.begin()?;

tx.put(key, value)?;
tx.remove(other)?;

tx.commit()?;
```

---

# 116. Range Scan

Ordered stores support:

```axiom
scan(from, to)
```

without loading the entire collection into memory.

---

# 117. Iterator Lifetime

Iterators pin the minimum required pages.

The compiler/runtime tracks iterator lifetime.

---

# 118. Index

An index maps:

```text
key → record/page
```

Index consistency is maintained as part of the same storage transaction.

---

# 119. Secondary Index

Optional:

```axiom
index.add(
    User.email,
    unique = true
)
```

The index layer remains above raw serialization.

---

# 120. Unique Constraint

A unique index must reject conflicting values before transaction commit.

---

# 121. Persistent Struct Store

A higher-level store can expose:

```axiom
Store<User>
```

with generated serializers and indexes.

---

# 122. Compiler-Generated Store Code

The compiler can generate:

```text
UserSchema
UserCodec
UserKey
UserIndex
UserMigration
```

from annotations.

---

# 123. Reflection-Free Database

The preferred implementation is:

```text
compile-time schema
+
generated codec
+
generated index access
```

rather than:

```text
runtime reflection
+
dynamic metadata
```

---

# 124. Memory-Mapped Structured Storage

Structured storage may use BOOTSTRAP-611 `mmap`.

Requirements:

- explicit page boundaries
- validation before access
- bounds checking
- generation checks
- corruption checks.

---

# 125. mmap Safety

Persistent storage must never blindly cast arbitrary mapped bytes into an Axiom struct.

Instead:

```text
validate page
→ validate schema
→ validate offsets
→ construct typed view
```

---

# 126. Native Persistent Layout

A specialized database may use:

```text
@repr(storage)
```

for directly mapped structures.

Such structures require strict layout declarations.

---

# 127. Pointer Ban in Persistent Data

Persistent representations must not contain native process pointers.

Instead use:

```text
PageId
Offset
ObjectId
RecordId
```

---

# 128. Object IDs

A persistent object ID can be:

```text
StorageGeneration
ObjectIndex
```

or another stable logical identifier.

---

# 129. Offset Safety

Offsets must be:

```text
unsigned
bounded
page-relative or file-relative
```

and validated before arithmetic.

---

# 130. Integer Overflow Protection

All persistent offset calculations use checked arithmetic.

An overflow produces:

```text
Corrupt
```

rather than wrapping.

---

# 131. Storage Corruption Model

Corruption can affect:

- page
- WAL
- index
- schema
- root metadata

Each is detected independently where possible.

---

# 132. Corruption Recovery

The runtime may recover from:

```text
corrupt index
```

by rebuilding the index from primary records.

But it must not silently rebuild corrupted authoritative data.

---

# 133. Integrity Levels

```text
None
PageChecksum
RecordChecksum
Authenticated
```

Authenticated storage uses BOOTSTRAP-610.

---

# 134. Encryption

Storage encryption can wrap:

```text
WAL
Pages
Logs
Backups
```

through the storage transform layer.

---

# 135. Key Rotation

Storage encryption must support versioned key identifiers.

Old data may remain encrypted under old keys until explicit migration.

---

# 136. Secret Values

Schemas may annotate:

```axiom
@secret
password_hash: Bytes
```

Compiler-generated diagnostics and debug representations must redact the field.

---

# 137. Serialization and IPC

BOOTSTRAP-604 may use AXBIN as one supported IPC encoding.

It provides:

- schema identity
- bounded decoding
- streaming
- zero-copy views.

---

# 138. Serialization and Networking

BOOTSTRAP-609 can use AXBIN frames for:

```text
HTTP payloads
WebSocket messages
custom TCP protocols
```

without making AXBIN mandatory.

---

# 139. Serialization and Configuration

BOOTSTRAP-601 can serialize typed configuration snapshots using AXBIN for:

- cache
- checkpoint
- local persistence

while retaining human-readable config formats where required.

---

# 140. Serialization and State

BOOTSTRAP-600 can use:

```text
Schema
+
Snapshot
+
WAL
+
Atomic commit
```

for durable application state.

---

# 141. Snapshot Format

Suggested:

```text
AXSN
version
application_id
schema_id
generation
payload_length
payload
checksum
```

---

# 142. Snapshot Compatibility

A snapshot can be loaded only when:

```text
schema compatible
```

or when an explicit migration exists.

---

# 143. Checkpoint Protocol

```text
quiesce writes
↓
serialize state
↓
write temporary snapshot
↓
sync
↓
atomic replace
↓
sync directory
↓
record checkpoint generation
```

This directly builds on 600 + 611.

---

# 144. Incremental Checkpoint

Large state can use:

```text
full snapshot
+
incremental log
```

instead of repeatedly serializing the entire state.

---

# 145. Snapshot Compaction

After a successful full snapshot:

```text
old WAL segments
```

can be removed after durability confirmation.

---

# 146. Serialization Cache

Generated serializers may cache schema metadata.

The hot path should not repeatedly rebuild schema descriptors.

---

# 147. Compile-Time Encoding

For fixed structures, the compiler can generate direct code:

```text
load field
encode field
store bytes
```

without virtual dispatch.

---

# 148. Branch Reduction

Generated serializers should specialize based on:

- optional presence
- fixed length
- alignment
- schema version.

---

# 149. SIMD

The implementation may use SIMD for:

- byte copying
- checksum
- UTF-8 validation
- primitive conversion

where supported.

---

# 150. CPU Architecture

Generated serialization must support:

```text
x86-64
ARM64
WASM
```

and future architectures through backend lowering.

---

# 151. GPU Boundary

Serialization is primarily CPU work.

GPU serialization may be added later for:

- tensor formats
- bulk datasets
- GPU-native storage

but is not required in 612 core.

---

# 152. Resource Accounting

Serialization tracks:

```text
bytes encoded
bytes decoded
allocations
decode depth
persistent pages
WAL bytes
cache bytes
snapshot bytes
```

through BOOTSTRAP-606.

---

# 153. Quotas

Structured storage quotas include:

```text
max_database_size
max_record_size
max_wal_size
max_page_cache
max_transaction_size
max_snapshot_size
```

---

# 154. Backpressure

Large serialization streams must support:

```text
await encoder.write(...)
```

rather than buffering unlimited data.

---

# 155. Cancellation

Encoding/decoding streams must support cancellation.

A partially decoded object is never returned as valid.

---

# 156. Deterministic Ordering

Canonical maps, sets, schemas, and metadata use deterministic ordering.

This is required for reproducible hashes.

---

# 157. Hashing

The runtime may expose:

```axiom
hash_encoded(value)
```

which hashes canonical AXBIN bytes.

---

# 158. Equality

Serialized equality and semantic equality are distinct.

Two semantically equivalent values may have different encodings if the schema explicitly permits noncanonical encoding.

Canonical mode removes this ambiguity.

---

# 159. Content Addressing

A content-addressed store can use:

```text
ObjectId = Hash(canonical AXBIN)
```

This is a higher-level feature built from 612 + 611.

---

# 160. Deduplication

Persistent storage may deduplicate identical immutable blobs.

Deduplication must not compromise transactional correctness.

---

# 161. Blob Storage

Large values should be stored as blobs rather than forcing them into one page.

Example:

```text
Record
 ↓
BlobId
 ↓
Blob segments
```

---

# 162. Inline Threshold

Small blobs may be stored inline.

Example policy:

```text
<= 4 KiB → inline
> 4 KiB → blob
```

The threshold is configurable.

---

# 163. Large Object Streaming

Large blobs must support streaming read/write without requiring full-memory allocation.

---

# 164. Blob Integrity

Blob segments may contain:

```text
segment ID
offset
length
checksum
```

---

# 165. Garbage Collection of Storage

Persistent storage may require **storage reclamation**, but this is not language garbage collection.

It operates on:

```text
unreachable pages
orphaned blobs
old snapshots
obsolete WAL
```

and is explicit/background controlled.

---

# 166. No Language GC Dependency

Axiom's memory model remains independent of persistent storage reclamation.

This distinction is mandatory.

---

# 167. Compaction

Storage compaction can reclaim fragmented pages.

Policies:

```text
Manual
Background
PressureTriggered
Startup
```

---

# 168. Compaction Resource Limits

Compaction must obey:

- CPU budget
- I/O budget
- memory budget
- storage quota.

---

# 169. Online Compaction

The preferred design allows readers to continue during compaction when possible.

The first implementation may temporarily restrict writers.

---

# 170. Crash During Compaction

Compaction must use:

```text
temporary generation
+
atomic root switch
```

or WAL equivalent.

A crash must leave either the old or new valid state.

---

# 171. Database Format Version

Every persistent store begins with:

```text
magic
format_version
schema_version
page_size
flags
```

---

# 172. Store Header

Example:

```text
AXDB
format
page_size
generation
root_page
wal_start
wal_end
checksum
```

---

# 173. Store Open

Opening a store performs:

```text
read header
↓
validate format
↓
validate checksum
↓
load schema
↓
recover WAL
↓
open page cache
```

---

# 174. Store Close

Closing performs:

```text
stop new transactions
↓
commit/abort active transaction
↓
flush WAL
↓
flush required pages
↓
write checkpoint
↓
sync
```

---

# 175. Read-Only Mode

A store can open:

```axiom
StoreMode.ReadOnly
```

No WAL mutation is allowed.

---

# 176. Immutable Store

An immutable store can be distributed as a package.

Useful for:

- AI models
- dictionaries
- application assets
- indexes
- lookup tables.

---

# 177. Package Store

PackageFS from 611 can expose immutable structured data.

Example:

```text
package://models/index.axdb
```

---

# 178. Versioned Store

Multiple generations can coexist:

```text
store.v1
store.v2
store.v3
```

A deployment layer can atomically select the active generation.

---

# 179. Migration Strategy

Preferred migration:

```text
old store
↓
read
↓
transform
↓
new store
↓
validate
↓
atomic switch
```

rather than modifying every record in place.

---

# 180. Online Migration

Optional higher layer may migrate incrementally.

Core 612 does not require it.

---

# 181. Error Model

Serialization errors:

```text
DecodeError
EncodeError
InvalidUtf8
InvalidSchema
UnknownRequiredField
InvalidVariant
LengthOverflow
DepthExceeded
AllocationLimit
ChecksumMismatch
```

Storage errors reuse BOOTSTRAP-611.

---

# 182. Error Context

Decode errors should expose:

```text
schema_id
field_id
byte_offset
path
expected_type
actual_tag
```

Example:

```text
User.address.city
offset=182
expected=String
```

---

# 183. No Secret Leakage

If a failed field is marked `@secret`, error diagnostics must not print its contents.

---

# 184. Compiler Diagnostics

Compiler errors should catch:

- duplicate field IDs
- duplicate variant IDs
- unsupported persistent type
- architecture-dependent persistent type
- incompatible schema evolution
- missing serializer
- recursive schema without indirection
- noncanonical map key
- invalid default.

---

# 185. Recursive Types

Recursive persistent types require indirection:

```axiom
struct Node {
    value: u64
    next: ObjectId<Node>?
}
```

A direct infinitely-sized recursive struct is rejected.

---

# 186. Object Graphs

Arbitrary pointer graphs are not serialized automatically.

They must use explicit IDs.

This prevents hidden pointer traversal and accidental huge object graphs.

---

# 187. Stable IDs

Applications can define:

```axiom
@key
id: u64
```

The generated store can then use it as primary key.

---

# 188. Generated Primary Index

The compiler may generate:

```text
UserById
```

without runtime reflection.

---

# 189. Generated Secondary Index

Example:

```axiom
@index(unique=true)
email: String
```

generates an index implementation.

---

# 190. Index Key Encoding

Index keys use canonical AXBIN encoding.

Composite indexes concatenate canonical components with explicit boundaries.

---

# 191. Composite Keys

Example:

```text
(country, city, user_id)
```

must encode unambiguously.

Length/tag boundaries prevent:

```text
("ab","c")
```

from colliding with:

```text
("a","bc")
```

---

# 192. Prefix Scans

Ordered composite indexes support prefix queries where their encoding permits it.

---

# 193. Query Boundary

612 provides:

```text
get
scan
lookup
range
```

but not SQL.

---

# 194. Query Planner Boundary

Query planning belongs to a later database layer.

612 exposes storage primitives to that planner.

---

# 195. Embedded Database Boundary

The built-in `KvStore` and persistent collections are intentionally modest.

A future full database engine can build on:

```text
PageStore
WAL
Transactions
Indexes
Serializer
```

---

# 196. No Mandatory Database Dependency

An ordinary Axiom executable using only structs and files must not link:

```text
database runtime
```

unless database APIs are referenced.

---

# 197. Dead Stripping

Unused components are removable:

```text
AXBIN
Schema
WAL
BTree
KV
PersistentMap
```

independently.

---

# 198. Runtime Profiles

Minimal:

```text
Codec
Schema
```

Storage:

```text
Codec
Schema
PersistentStorage
WAL
```

Full:

```text
Codec
Schema
KV
Indexes
PersistentCollections
WAL
Compaction
```

---

# 199. Compiler IR

Conceptual operations:

```text
serialize.begin
serialize.field
serialize.scalar
serialize.array
serialize.map
serialize.end

deserialize.begin
deserialize.field
deserialize.scalar
deserialize.array
deserialize.map
deserialize.end

schema.id
schema.version
storage.tx
storage.wal
storage.page
storage.index
```

---

# 200. Compiler Optimization

The compiler may:

- inline scalar encoders
- eliminate redundant copies
- specialize fixed arrays
- fuse encode operations
- eliminate temporary buffers
- vectorize byte copying
- specialize schema versions.

---

# 201. Copy Elimination

Example:

```text
struct
 ↓
temporary buffer
 ↓
encoder
```

may become:

```text
struct
 ↓
encoder
 ↓
output
```

when the destination permits direct writes.

---

# 202. Decoder Optimization

If input is trusted and validated, the compiler may use specialized fast paths.

Untrusted input must retain bounds checks.

---

# 203. Trusted Data

A decoder may be marked:

```axiom
DecodeMode.Trusted
```

only with explicit authority.

Trusted mode must still preserve memory safety.

---

# 204. Security Rule

`Trusted` does not mean:

```text
unsafe
```

It means the caller accepts stronger input assumptions.

---

# 205. IPC Schema Validation

IPC schemas should be validated before accepting a connection payload.

Unknown schema IDs should produce a protocol error rather than attempting arbitrary interpretation.

---

# 206. Network Schema Negotiation

A future protocol layer may negotiate:

```text
SchemaId
Version
Encoding
Compression
```

612 only provides the metadata needed.

---

# 207. Persistent Schema Registry

A store may contain a local schema registry:

```text
SchemaId
 ↓
SchemaDescriptor
```

This enables introspection without runtime reflection of application objects.

---

# 208. Schema Registry Security

Schema descriptors are data, not executable code.

Loading a schema must never execute migration code automatically.

---

# 209. Schema Cache

Schema descriptors can be cached in memory.

Cache eviction does not affect correctness.

---

# 210. Deterministic Schema Fingerprint

Equivalent schema descriptors must produce identical fingerprints.

Source formatting must not affect the fingerprint.

---

# 211. Source Independence

Renaming a source-level type without changing persistent identity can preserve the same schema ID.

Persistent identity is explicit.

---

# 212. Persistent Type Identity

Example:

```axiom
@schema("com.example.User")
struct User { ... }
```

This identity becomes stable across source refactoring.

---

# 213. Namespace

Schema identity should include namespace:

```text
organization.application.type
```

to reduce collisions.

---

# 214. Reserved IDs

Field and variant IDs may reserve ranges for future versions.

---

# 215. Deprecation

Fields can be:

```axiom
@deprecated
```

without removing their IDs.

The ID remains reserved.

---

# 216. Unknown Field Preservation Mode

For proxy systems:

```axiom
Decoder.PreserveUnknown
```

stores raw unknown fields.

The preserved bytes can later be emitted without understanding them.

---

# 217. Canonical Unknown Fields

When re-encoding preserved fields, their original canonical byte sequence should be retained when valid.

---

# 218. Schema Translation

A translation layer can convert:

```text
Schema A
→
Schema B
```

without decoding into a full object graph.

This is useful for gateways.

---

# 219. Streaming Translation

Large messages can be transformed field-by-field.

This minimizes memory.

---

# 220. Persistent Log + Schema

Each log segment stores schema IDs per record or segment.

Schema changes do not require rewriting old records.

---

# 221. Event Sourcing Boundary

Axiom can implement event sourcing using:

```text
PersistentLog
+
Schema
+
Snapshot
```

but event-sourcing semantics remain application-level.

---

# 222. Audit Log

The same primitives can build append-only audit logs.

Security-sensitive audit logs should use integrity/authentication from 610.

---

# 223. Deterministic Replay

A serialized event stream can be replayed using:

```text
schema
+
sequence
+
payload
```

provided application code itself is deterministic.

---

# 224. Persistent Queue

A durable queue can use:

```text
PersistentLog
+
consumer offset
+
transaction
```

The queue layer is above 612.

---

# 225. Storage Transactions + IPC

A service may receive:

```text
request
```

then atomically:

```text
process request
↓
write response state
↓
commit
```

before acknowledging the request.

This provides a foundation for durable services.

---

# 226. Exactly-Once Boundary

612 must not claim distributed exactly-once semantics.

It can provide:

```text
local durable commit
```

only.

Exactly-once across processes/networks requires higher-level protocol design.

---

# 227. Durability Modes

Structured storage exposes:

```text
MemoryOnly
Buffered
Durable
Synchronous
```

Applications select the tradeoff.

---

# 228. MemoryOnly

Useful for tests and caches.

No persistence guarantee.

---

# 229. Buffered

Writes may remain in OS/runtime buffers.

Fast but not power-loss durable.

---

# 230. Durable

Commit waits for the configured storage durability boundary.

---

# 231. Synchronous

Each mutation may force durability immediately.

Useful for critical records but potentially slower.

---

# 232. Group Commit

Multiple transactions can share one durability barrier.

Example:

```text
Tx1
Tx2
Tx3
 ↓
single WAL sync
```

This improves throughput while preserving documented commit semantics.

---

# 233. Commit Ordering

Commit generations are monotonic.

A later generation cannot become durable before required earlier WAL state.

---

# 234. Resource Governor + WAL

WAL growth is quota-controlled.

When the WAL approaches its limit:

```text
checkpoint
↓
compact
↓
reject
```

according to policy.

---

# 235. Storage Pressure

Under low disk space:

1. evict cache
2. compact obsolete storage
3. remove disposable temporary data
4. report pressure
5. reject nonessential writes

The runtime must never delete durable application data automatically.

---

# 236. Cache Classification

Every persistent object is classified:

```text
Durable
Disposable
Temporary
Recoverable
```

Automatic cleanup applies only to disposable/temporary data.

---

# 237. Backup Boundary

612 can expose:

```text
snapshot()
export()
```

but backup transport belongs to a higher layer.

---

# 238. Export

A store can export a consistent snapshot:

```text
snapshot generation
+
schema
+
records
```

without stopping readers.

---

# 239. Import

Import must validate:

- format
- schema
- checksums
- bounds
- quotas

before activation.

---

# 240. Atomic Activation

Imported data becomes active through:

```text
new generation
↓
validate
↓
sync
↓
atomic root switch
```

---

# 241. Versioned Backups

Backups should include:

```text
application_id
build_id
schema_id
storage_format
generation
timestamp
```

Timestamp is metadata, not part of canonical content hashing.

---

# 242. Reproducibility

For deterministic snapshots:

```text
ordering
encoding
schema
```

must be deterministic.

Volatile metadata should be excluded from content hash.

---

# 243. Content Hash

A snapshot content hash covers:

```text
canonical schema
+
canonical records
```

not machine-specific paths.

---

# 244. AI Tooling

Axiom compiler artifacts should expose:

```text
type schema
field semantics
serialization format
migration graph
storage layout
index definitions
```

in machine-readable metadata.

This supports AI-assisted code generation and maintenance.

---

# 245. AI Safety

AI tooling must not infer that:

```text
field id 3
```

can be reused merely because the field is no longer referenced in current source.

Persistent schema history is authoritative.

---

# 246. Schema Documentation

Generated schema documentation may contain:

```text
type
field
ID
required/optional
default
version
compatibility
secret status
```

---

# 247. Compiler Command

Potential command:

```text
axiom schema inspect app.axbin
```

outputs schema metadata without executing application code.

---

# 248. Store Inspection

Potential command:

```text
axiom store inspect database.axdb
```

can report:

```text
format
schema
page size
generation
WAL
indexes
size
integrity
```

---

# 249. Store Repair

Repair commands must be explicit.

Example:

```text
axiom store verify
axiom store rebuild-index
```

Repair must never silently modify production data.

---

# 250. Testing Architecture

Required components:

```text
CodecTest
SchemaTest
MigrationTest
WALTest
PageStoreTest
KVTest
IndexTest
RecoveryTest
CorruptionTest
ConcurrencyTest
PerformanceTest
```

---

# 251. Codec Fuzzing

Fuzzers must verify:

```text
arbitrary bytes
→
decoder never violates memory safety
```

and never:

- hangs
- overflows
- allocates beyond configured limits
- crashes the runtime.

---

# 252. Round-Trip Property

For supported values:

```text
decode(encode(x)) == x
```

under semantic equality.

---

# 253. Canonical Property

For canonical values:

```text
encode(decode(bytes)) == canonical(bytes)
```

where the input is valid canonical data.

---

# 254. Schema Evolution Property

For every declared compatible schema transition:

```text
decode_new(encode_old(value))
```

must produce the documented result.

---

# 255. WAL Property

After simulated crash:

```text
recover(store)
```

must result in:

```text
committed transactions preserved
uncommitted transactions absent
```

within the documented model.

---

# 256. Index Property

After recovery:

```text
index(key) == primary_store(key)
```

for every committed record.

---

# 257. Snapshot Property

A reader observing generation `G` must see a consistent view of generation `G`.

---

# 258. Concurrency Property

Multiple readers must not corrupt:

```text
page cache
schema cache
index
WAL
```

---

# 259. Resource Property

No malformed input may bypass:

```text
decode limits
storage quotas
transaction limits
page limits
```

---

# 260. Security Property

No serialized input may cause:

```text
arbitrary code execution
```

merely by decoding.

---

# 261. No Deserialization Constructors

Decoding must not invoke arbitrary user constructors automatically.

Generated decode functions create validated values directly.

---

# 262. Validation Hooks

Applications may request:

```axiom
decode_validated<T>()
```

which runs explicit validation after structural decoding.

---

# 263. Validation Separation

Structural validity:

```text
correct binary representation
```

is separate from domain validity:

```text
age <= 150
email valid
balance >= 0
```

---

# 264. Domain Validation

Domain validation remains ordinary Axiom code.

This avoids embedding business rules in the serializer.

---

# 265. Serialization Security Boundary

Untrusted input should follow:

```text
bytes
↓
bounded decoder
↓
structural validation
↓
domain validation
↓
application
```

---

# 266. Persistent Storage Security Boundary

```text
untrusted storage
↓
page validation
↓
checksum
↓
schema validation
↓
record validation
↓
application
```

---

# 267. Performance Target

The generated serializer should approach hand-written binary serialization.

Target overhead:

```text
primitive encode ≈ direct store
primitive decode ≈ direct load + bounds check
```

---

# 268. Allocation Target

Simple fixed-size structs:

```text
zero temporary heap allocations
```

Variable-length fields allocate only required memory.

---

# 269. Zero-Copy Target

For immutable input:

```text
view decode
```

should require:

```text
O(1)
```

additional allocation for fixed-layout data.

---

# 270. Persistent Store Performance

The page store should support:

- sequential append
- indexed lookup
- range scan
- concurrent readers
- one writer

without requiring heavyweight runtime machinery.

---

# 271. Binary Size

A program using only:

```text
struct serialization
```

should not link:

```text
WAL
BTree
KV
compaction
```

unless referenced.

---

# 272. ABI Stability

Serialized representation is independent from:

```text
Axiom compiler version
```

provided the schema remains compatible.

---

# 273. Compiler Version Independence

A newer compiler can read old AXBIN data when schema compatibility rules permit it.

---

# 274. Runtime Version Independence

AXBIN decoding should not require the exact same runtime version.

Only the stable format contract matters.

---

# 275. Format Registry

Reserved format identifiers:

```text
AXBIN
AXBF
AXSN
AXDB
```

must be centrally specified to avoid collisions.

---

# 276. Magic Numbers

Every persistent container has a recognizable magic value.

Invalid magic must fail before deeper parsing.

---

# 277. Version Negotiation

Unsupported format versions return:

```text
UnsupportedVersion
```

rather than guessing.

---

# 278. Forward Compatibility

Readers may skip unknown optional metadata.

They must reject unknown mandatory semantics.

---

# 279. Backward Compatibility

New writers may emit fields understood by older readers only when compatibility is explicitly guaranteed.

---

# 280. Schema Compatibility Matrix

Generated metadata should expose:

```text
V1 → V2 : compatible
V2 → V3 : migration required
V3 → V4 : breaking
```

This is metadata, not an automatic migration decision.

---

# 281. Persistent Collection API

Example:

```axiom
let users = PersistentMap<u64, User>.open(store)?;

users.put(10, user)?;
let value = users.get(10)?;
```

---

# 282. Persistent Vector API

```axiom
let items = PersistentVector<Item>.open(store)?;

items.push(item)?;
let item = items.get(index)?;
```

---

# 283. Persistent Log API

```axiom
let log = PersistentLog<Event>.open(store)?;

let seq = log.append(event)?;
```

---

# 284. KV API

```axiom
let db = KvStore<u64, User>.open("users.axdb")?;

db.put(42, user)?;
let user = db.get(42)?;
```

---

# 285. Transaction API

```axiom
let tx = db.transaction()?;

tx.put(42, user)?;
tx.put(43, other)?;

tx.commit(Durability.Durable)?;
```

---

# 286. Read Snapshot

```axiom
let snapshot = db.snapshot()?;

let a = snapshot.get(42)?;
let b = snapshot.get(43)?;
```

Both reads observe the same generation.

---

# 287. Batch API

```axiom
db.batch(|batch| {
    batch.put(...)
    batch.put(...)
    batch.remove(...)
})?;
```

The compiler may lower this into one storage transaction.

---

# 288. Atomic Batch

The batch is atomic within one storage instance.

It is not automatically atomic across:

```text
multiple stores
filesystem + network
multiple processes
```

---

# 289. Cross-Store Transactions

Not part of 612.

A higher distributed/application transaction layer may coordinate them.

---

# 290. Transaction Hooks

Optional hooks:

```text
before_commit
after_commit
after_abort
```

must not execute arbitrary external side effects as though those effects were transactional.

---

# 291. External Side Effects

A transaction commit cannot atomically include:

```text
email
network request
GPU operation
external process
```

without a higher-level protocol.

---

# 292. Outbox Pattern

612 primitives can implement:

```text
database transaction
+
persistent outbox
```

for reliable external event delivery.

---

# 293. Event Outbox

Example:

```text
update state
+
append event
→
commit
```

A separate dispatcher sends the event later.

---

# 294. Inbox Pattern

A persistent inbox can record processed message IDs.

This helps build idempotent IPC/network services.

---

# 295. Idempotency Key

A persistent store may use:

```text
RequestId → Result
```

to detect duplicate requests.

---

# 296. Service Recovery

BOOTSTRAP-605 can restore service state from:

```text
snapshot
+
WAL
+
inbox/outbox
```

---

# 297. Checkpoint Integration

The service supervisor should know:

```text
storage generation
```

when recording a service checkpoint.

---

# 298. Diagnostics Integration

Storage events include:

```text
transaction_id
generation
schema_id
page_id
```

where useful.

---

# 299. Trace Correlation

Storage spans inherit the current:

```text
task_id
service_id
trace_id
transaction_id
```

---

# 300. Final Architecture

```text
                         AXIOM APPLICATION
                                │
                    ┌───────────▼───────────┐
                    │   Typed Domain Data   │
                    └───────────┬───────────┘
                                │
              ┌─────────────────▼─────────────────┐
              │       Serialization Layer         │
              │ AXBIN / Schema / Codec / Views    │
              └─────────────────┬─────────────────┘
                                │
          ┌─────────────────────▼─────────────────────┐
          │       Structured Storage Layer             │
          │ KV / BTree / Persistent Collections       │
          │ WAL / Pages / Indexes / Snapshots         │
          └─────────────────────┬─────────────────────┘
                                │
                     ┌──────────▼──────────┐
                     │ Storage Transactions│
                     └──────────┬──────────┘
                                │
                     BOOTSTRAP-611
                                │
                ┌───────────────▼───────────────┐
                │ File / mmap / VFS / Durability│
                └───────────────┬───────────────┘
                                │
        ┌───────────────────────┼───────────────────────┐
        │                       │                       │
       603                     606                     607
    Security                 Resources              Scheduler
        │                       │                       │
        └───────────────────────┼───────────────────────┘
                                │
                     Native Operating System
```

---

# 301. Core Invariants

The implementation is correct only if:

```text
I1   Canonical encoding is deterministic.
I2   Portable encoding is architecture-independent.
I3   Malformed input cannot violate memory safety.
I4   Decode limits are enforced.
I5   Persistent field IDs are stable.
I6   Unknown optional fields can be skipped.
I7   Required fields are validated.
I8   Schema incompatibility is explicit.
I9   Migration is explicit.
I10  Serialization does not require runtime reflection.
I11  Simple serialization does not require heap allocation.
I12  Zero-copy views cannot outlive their source.
I13  Persistent data contains no native pointers.
I14  WAL precedes durable page mutation.
I15  Committed transactions survive documented crashes.
I16  Uncommitted transactions are not exposed as committed.
I17  Snapshot readers see a consistent generation.
I18  Indexes remain consistent with committed primary data.
I19  Storage quotas are enforced.
I20  Corrupt data cannot become arbitrary executable behavior.
I21  Secret fields are not leaked through diagnostics.
I22  Database functionality is dead-strippable.
I23  The serializer is independent of filesystem implementation.
I24  The storage engine is independent of language GC.
I25  Cross-process exactly-once semantics are not falsely claimed.
I26  External side effects are not implicitly transactional.
I27  Format versions are validated.
I28  Schema identity is independent of source formatting.
I29  Persistent object references are logical IDs/offsets, not pointers.
I30  Recovery is deterministic under the same storage state.
```

---

# 302. Acceptance Criteria

BOOTSTRAP-612 is complete when:

1. AXBIN primitive encoding is specified.
2. Fixed-width integers work.
3. Variable-width integers work.
4. Signed integers use canonical encoding.
5. Boolean encoding is canonical.
6. Floating-point encoding is deterministic.
7. NaN canonicalization works.
8. UTF-8 strings are supported.
9. Raw bytes are supported.
10. Arrays are supported.
11. Fixed arrays are supported.
12. Structs are supported.
13. Enums are supported.
14. Tagged unions are supported.
15. Options are supported.
16. Results are supported.
17. Maps are supported.
18. Sets are supported.
19. Canonical map ordering works.
20. Length bounds are enforced.
21. Decode depth limits work.
22. Allocation limits work.
23. Schema IDs are deterministic.
24. Schema versions are represented.
25. Field IDs are stable.
26. Unknown optional fields are skippable.
27. Required fields are validated.
28. Compatible schema evolution is supported.
29. Breaking schema changes are detected.
30. Explicit migration works.
31. Compiler-generated serializers work.
32. Compiler-generated schemas work.
33. Reflection is not required.
34. Zero-copy views work.
35. View lifetime is safe.
36. Streaming encoding works.
37. Streaming decoding works.
38. AXBIN framing works.
39. Checksums work.
40. WAL works.
41. WAL recovery works.
42. Page checksums work.
43. Page corruption is detected.
44. Single-writer transactions work.
45. Snapshot readers work.
46. Persistent KV works.
47. Persistent vector works.
48. Persistent map works.
49. Persistent log works.
50. Ordered range scans work.
51. Indexes work.
52. Unique indexes work.
53. Snapshot creation works.
54. Snapshot restore works.
55. Crash recovery works.
56. Power-loss simulation works.
57. Storage quotas work.
58. Large blobs stream without full-memory allocation.
59. Compaction preserves correctness.
60. Dead stripping removes unused database components.
61. IPC can use AXBIN.
62. Networking can use AXBIN.
63. Application state can use AXBIN snapshots.
64. Config can use generated binary snapshots.
65. Encryption can wrap persistent storage.
66. Diagnostics contain storage correlation IDs.
67. Secret values remain redacted.
68. Fuzzing cannot violate memory safety.
69. Malformed input cannot cause unbounded resource consumption.
70. Generated serialization approaches hand-written binary-code performance.

---

# 303. Architectural Conclusion

BOOTSTRAP-612 deliberately establishes a **layered data foundation rather than prematurely creating a giant database subsystem**.

The fundamental progression is:

```text
Axiom Value
    ↓
Schema
    ↓
Canonical Binary Representation
    ↓
Serialized Bytes
    ↓
Storage Record
    ↓
Page
    ↓
WAL / Transaction
    ↓
Durable Storage
```

This allows Axiom to support all of the following without adding a mandatory database runtime:

```text
configuration snapshots
application state
IPC
network protocols
binary assets
persistent collections
embedded KV stores
event logs
caches
AI model metadata
indexes
embedded databases
```

The key architectural choice is:

> **Serialization is a compiler/data-model capability; persistence is a storage capability; database querying is a higher-level capability.**

That separation keeps the language fast, modular and dead-strippable while still allowing Axiom to build a full native database stack entirely in Axiom itself.

**BOOTSTRAP-612 COMPLETE.**

---

# 304. Next Architecture Task

## BOOTSTRAP-613 — Native Compression, Archive, Package, Content-Addressed Storage & Resource Packaging Runtime 5.0

The next layer will build on **611 Storage + 612 Serialization** and define:

- compression abstraction
- streaming compression/decompression
- archive format abstraction
- ZIP/TAR-like compatibility boundary
- native Axiom package format
- executable/resource bundles
- package manifests
- content-addressed objects
- deduplication
- chunking
- Merkle trees
- immutable resources
- package verification
- signed packages through 610
- encrypted packages
- compressed storage
- random-access compressed assets
- package mounting through VFS
- package versioning
- dependency/resource manifests
- offline package deployment
- deterministic package generation
- reproducible package hashes
- AI-readable package metadata
- asset indexing
- model/large-file packaging
- lazy resource loading
- memory mapping of package contents
- package cache
- content-addressed cache
- garbage collection of **storage objects**, explicitly separate from Axiom memory GC
- compiler/linker integration
- dead stripping
- native executable/resource bundling
- Windows/Linux/macOS/Android/iOS/WASM packaging boundaries.

**BOOTSTRAP-612 COMPLETE → BOOTSTRAP-613 QUEUED.**
:::