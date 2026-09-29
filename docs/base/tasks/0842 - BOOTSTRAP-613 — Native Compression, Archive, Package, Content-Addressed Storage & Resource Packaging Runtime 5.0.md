:::writing{variant="document" id="73146" title="BOOTSTRAP-613 — Native Compression, Archive, Package, Content-Addressed Storage & Resource Packaging Runtime 5.0"}

# BOOTSTRAP-613 — Native Compression, Archive, Package, Content-Addressed Storage & Resource Packaging Runtime 5.0

**Status:** Architecture Specification — Completed  
**Layer:** Native Runtime / Storage / Packaging  
**Depends on:** BOOTSTRAP-600..612  
**Primary dependencies:** 603 Security, 606 Resource Governor, 610 Cryptography, 611 Storage/VFS, 612 Serialization  
**Design priority:** native performance, deterministic output, minimal runtime dependency, secure-by-default, AI-readable metadata.

---

## 1. Purpose

BOOTSTRAP-613 defines Axiom's native runtime and toolchain architecture for:

- compression/decompression;
- archive reading/writing;
- native package format;
- application/resource bundles;
- content-addressed storage;
- deduplication;
- chunking;
- Merkle trees;
- immutable objects;
- package signing and verification;
- optional encryption;
- package mounting through VFS;
- package cache;
- offline deployment;
- package updates and rollback;
- resource indexing and lazy loading;
- deterministic and reproducible package generation.

The subsystem must work both as:

1. a **runtime library** for applications;
2. a **compiler/linker resource-packaging layer**;
3. a **deployment/package toolchain**;
4. a **VFS backend**;
5. a **content-addressed local object store**.

---

# 2. Core Design Principles

### P613-01 — Packages are data, not code

Opening, inspecting, mounting, decompressing or validating a package must never execute package-provided code.

### P613-02 — Verification precedes trust

A package may be:

```text
readable
→ structurally valid
→ integrity verified
→ cryptographically authenticated
→ policy authorized
→ activated
```

These are distinct states.

### P613-03 — Immutable package contents

Once an object or activated package generation is committed, its contents are immutable.

Updates create new objects/generations.

### P613-04 — Content addressing

Objects are identified by cryptographic digest rather than mutable filenames.

```text
ObjectId = Hash(algorithm || domain || canonical_content)
```

### P613-05 — Deterministic builds

Given identical logical inputs and build parameters, package generation must produce identical canonical metadata and, where codec determinism is supported, identical package bytes.

### P613-06 — Streaming first

Large resources must not require loading the complete resource into RAM.

### P613-07 — VFS integration

A package can be mounted as a read-only filesystem layer without extracting every entry.

### P613-08 — No mandatory external runtime

The core package runtime must not depend on a third-party package manager, compression framework or runtime.

Optional codec/provider modules may exist behind explicit interfaces.

---

# 3. Layer Architecture

```text
Application
    │
    ▼
Resource API
    │
    ├── Package API
    ├── Archive API
    └── Content Store API
            │
            ▼
       Package Engine
            │
     ┌──────┼─────────┐
     ▼      ▼         ▼
Compression Integrity Encryption
     │      │         │
     └──────┼─────────┘
            ▼
       VFS / Storage
            │
            ▼
BOOTSTRAP-611 Storage
            │
            ▼
Native OS / Device
```

---

# 4. Terminology

| Term | Meaning |
|---|---|
| Package | Immutable logical collection of resources |
| Entry | One named resource inside a package |
| Object | Immutable content-addressed byte sequence |
| Chunk | Independently addressable object fragment |
| Manifest | Canonical package metadata |
| Package ID | Stable logical identity |
| Generation | Immutable activated version |
| Object ID | Cryptographic identity of content |
| Merkle Root | Cryptographic root representing a tree |
| Store | Local content-addressed object repository |
| Mount | Exposing package contents through VFS |
| Pin | Prevents object reclamation |
| Lease | Temporary retention guarantee |
| Bundle | Package containing executable + resources |
| Resource | Application-consumable package entry |

---

# 5. Compression Architecture

Compression is exposed through a common interface:

```text
CompressionCodec
    name()
    version()
    capabilities()
    create_encoder(config)
    create_decoder(config)
```

A codec must declare:

```text
streaming
dictionary
random_access
deterministic
checksum
parallel
native
```

capabilities.

---

# 6. Built-In Compression Modes

The core format defines these logical modes:

```text
STORE
DEFLATE
LZ4
ZSTD
BROTLI
CUSTOM
```

`STORE` is mandatory.

Other codecs may be compiled into profiles or supplied as optional providers.

The package format stores the codec identifier, so decoding does not depend on filename extensions.

---

# 7. Compression Levels

Compression configuration:

```text
CompressionConfig {
    codec
    level
    block_size
    window_size
    dictionary_id
    deterministic
}
```

Levels are codec-specific.

The package metadata records the actual codec and parameters required for decoding.

A codec must reject unsupported parameter combinations rather than silently changing them.

---

# 8. Deterministic Compression

Deterministic mode must eliminate:

- random seeds;
- wall-clock timestamps;
- nondeterministic block ordering;
- process-dependent metadata;
- host-specific information.

The package builder must therefore control:

```text
input ordering
metadata ordering
timestamps
compression parameters
dictionary
codec version
```

Codec versions that cannot guarantee deterministic output must not be used for reproducible builds.

---

# 9. Streaming Compression

API:

```text
Compressor
    write(bytes)
    flush(mode)
    finish()

Decompressor
    read()
    feed(bytes)
    finish()
```

Streaming operation must support:

```text
small resource
large file
network stream
pipe
memory mapped input
VFS input
```

No complete-resource allocation is required.

---

# 10. Compression Blocks

Large entries may be split into independent compressed blocks.

```text
Entry
 ├── Block 0
 ├── Block 1
 ├── Block 2
 └── ...
```

Each block contains:

```text
uncompressed_size
compressed_size
codec
checksum
object_id
```

This enables:

- partial reads;
- parallel decompression;
- random access;
- corruption localization;
- content deduplication.

---

# 11. Random-Access Compression

For resources requiring random access:

```text
compressed entry
        │
        ├── block index
        ├── compressed block 0
        ├── compressed block 1
        └── ...
```

The index maps:

```text
logical_offset → block_id
```

Reading a range therefore requires only the necessary blocks.

Target:

```text
O(log N)
```

index lookup plus decompression of required blocks.

---

# 12. Compression Heuristics

Package builder may select:

```text
STORE
```

when:

```text
compressed_size >= original_size
```

unless deterministic package policy explicitly requires the codec.

For already-compressed data:

```text
jpg
png
mp4
zip
gzip
7z
encrypted data
```

the default policy should prefer `STORE`.

---

# 13. Checksums

Every independently stored compressed block must support integrity verification.

Minimum:

```text
CRC32C
```

for corruption detection.

Cryptographic integrity:

```text
SHA-256
SHA-512/256
```

or another algorithm approved by BOOTSTRAP-610.

Checksum and cryptographic hash have different purposes.

---

# 14. Archive Abstraction

Archive API:

```text
ArchiveReader
    open()
    entry_count()
    find(path)
    open_entry(path)
    iterate()

ArchiveWriter
    add(path, source)
    remove(path)
    finalize()
```

Archive readers must be able to inspect metadata without extracting contents.

---

# 15. Compatibility Formats

Axiom supports import/export boundaries for:

```text
ZIP
TAR
TAR.GZ
TAR.ZSTD
```

Compatibility is not the native package format.

The native package format is optimized for:

- deterministic builds;
- random access;
- signatures;
- content addressing;
- VFS mounting;
- deduplication;
- immutable storage.

---

# 16. Native Package Format

Canonical extension:

```text
.axpk
```

Logical structure:

```text
AXPK
├── Header
├── Manifest
├── Entry Index
├── Object Index
├── Chunk/Merkle Index
├── Payload Objects
└── Signature Area
```

---

# 17. AXPK Header

Conceptual header:

```text
AxpkHeader {
    magic
    format_version
    flags
    header_size
    manifest_offset
    manifest_size
    index_offset
    index_size
    object_table_offset
    object_table_size
    signature_offset
    signature_size
    package_id
    generation
    manifest_hash
}
```

All integer fields use explicit endianness.

Canonical format:

```text
little-endian
```

unless a future format version explicitly changes this.

---

# 18. Package Identity

```text
PackageId
```

is a stable logical identifier.

Example:

```text
com.example.myapp
```

Version:

```text
major.minor.patch
```

Generation is separate from semantic version.

Example:

```text
Package:
    com.example.myapp
    version = 2.4.1
    generation = 17
```

---

# 19. Target Constraints

Package metadata may specify:

```text
os
architecture
abi
minimum_os
cpu_features
gpu_features
runtime_profile
```

Example:

```text
targets:
    windows-x64
    linux-x64
    macos-arm64
```

Target-specific resources can coexist inside one logical package.

---

# 20. Package Manifest

Manifest uses AXBIN/AXBF from BOOTSTRAP-612.

Example:

```text
PackageManifest {
    package_id
    version
    generation
    format_version
    targets[]
    entries[]
    dependencies[]
    capabilities[]
    publisher
    signatures[]
    compression_policy
    encryption_policy
    resource_groups[]
}
```

The manifest is canonicalized before hashing.

---

# 21. Entry Model

```text
PackageEntry {
    path
    kind
    size
    content_id
    codec
    flags
    mode
    attributes
    mime_type?
    locale?
    variant?
}
```

Entry kinds:

```text
File
Directory
Symlink
Executable
SharedLibrary
Resource
Manifest
Index
```

Symlink support is policy-controlled.

---

# 22. Package Paths

Package paths must:

- use UTF-8;
- use `/`;
- never contain `..`;
- never begin with `/`;
- never contain NUL;
- have normalized separators;
- use canonical Unicode normalization according to package policy.

Examples:

```text
assets/logo.png
models/main.axmodel
locales/vi/app.axres
bin/app.exe
```

---

# 23. Path Traversal Prevention

The package engine must reject:

```text
../secret
../../file
/absolute/path
C:\Windows\...
\\server\...
```

when interpreted as package-relative paths.

Extraction must occur through BOOTSTRAP-611 secure path APIs rather than raw concatenation.

---

# 24. Symlink Policy

Default:

```text
symlink = disabled
```

If enabled:

- target must be validated;
- package-relative targets cannot escape package root;
- host-absolute targets require explicit privileged policy.

Packages must never silently create arbitrary host filesystem links.

---

# 25. Object Model

Content-addressed objects:

```text
ObjectId
ObjectHeader
Payload
```

Conceptually:

```text
ObjectId = H(domain || type || size || payload)
```

The domain separator prevents cross-type hash ambiguity.

---

# 26. Object Types

```text
RawBlob
CompressedBlock
Manifest
EntryIndex
ChunkIndex
MerkleNode
Package
Delta
Dictionary
Metadata
```

---

# 27. Immutable Object Store

Logical API:

```text
ObjectStore
    put(source) -> ObjectId
    open(id)
    exists(id)
    stat(id)
    pin(id)
    unpin(id)
    lease(id, duration)
    delete(id)
    collect()
```

`put()` must be idempotent.

If the same object already exists:

```text
put(content) → existing ObjectId
```

without creating duplicate physical data.

---

# 28. Object Storage Layout

Implementation may use:

```text
objects/
    ab/
       cdef...
```

where the first digest bytes determine directories.

The exact layout is implementation-defined.

Applications must never depend on physical object paths.

---

# 29. Chunking

Large files may use fixed or content-defined chunks.

Modes:

```text
FixedChunk
ContentDefinedChunk
```

Default target chunk size:

```text
256 KiB – 4 MiB
```

depending on workload.

Chunk size is a package policy, not a language semantic.

---

# 30. Content-Defined Chunking

CDC may use rolling fingerprints.

Boundary selection:

```text
rolling_hash(data)
        ↓
boundary decision
        ↓
chunk
```

Advantages:

- stable chunks after insertion/deletion;
- better incremental updates;
- deduplication across package versions.

CDC parameters must be recorded in package metadata.

---

# 31. Merkle Tree

A package can be represented as:

```text
             Root
            /    \
         Node    Node
        /   \    /   \
      Obj   Obj Obj   Obj
```

Each node contains hashes of children.

The root provides a compact identity for the complete logical content tree.

---

# 32. Merkle Domains

Different node types use domain separation:

```text
AXPK-MANIFEST
AXPK-ENTRY
AXPK-CHUNK
AXPK-MERKLE
AXPK-PACKAGE
```

This prevents structural hash collisions between semantic object classes.

---

# 33. Deduplication

Deduplication occurs at:

```text
whole-object
chunk
package
resource
```

levels.

Deduplication must not alter logical package semantics.

---

# 34. Deduplication Across Packages

Example:

```text
Package A
    model.bin
        chunk A
        chunk B
        chunk C

Package B
    model.bin
        chunk A
        chunk B
        chunk D
```

Only:

```text
A
B
C
D
```

are stored once.

---

# 35. Storage Garbage Collection

Storage-object reclamation is distinct from language memory management.

It operates on:

```text
roots
→ reachable objects
→ unreachable objects
```

It must never be described as Axiom heap GC.

---

# 36. Storage GC Roots

Roots include:

```text
active package generations
installed packages
explicit pins
leases
snapshots
deployment generations
cache entries
application state references
```

---

# 37. Reclamation Algorithm

Default:

```text
mark reachable
→ identify unreachable
→ reclaim
```

Alternative:

```text
reference counting
```

may be used as an optimization.

Reference counting alone must not be assumed sufficient when cycles exist.

---

# 38. Pins

A pin prevents reclamation.

```text
pin(ObjectId)
```

is intended for:

- active deployment;
- memory-mapped resource;
- ongoing update;
- long-running process;
- package mount.

Pins must be released deterministically.

---

# 39. Leases

A lease is time-bounded:

```text
Lease {
    object_id
    expiration
}
```

Expired leases become reclaimable.

Clock handling must use BOOTSTRAP-601/607 time abstractions.

---

# 40. Package Cache

Caches are separate from authoritative package state.

Namespaces:

```text
SystemCache
UserCache
ApplicationCache
BuildCache
CompilerCache
ModelCache
```

Each cache has:

```text
quota
eviction policy
integrity policy
encryption policy
```

---

# 41. Cache Eviction

Eviction may use:

```text
LRU
LFU
size-aware LRU
age + size
custom policy
```

Eviction must never remove:

```text
active generation
pinned object
leased object
required dependency
```

---

# 42. Package Mount

A package can be exposed as:

```text
/vfs/app
```

through BOOTSTRAP-611.

Mount properties:

```text
read_only
package_id
generation
trust_state
capability
```

---

# 43. Package Filesystem

Example:

```text
app.axpk
    ↓
AXPK filesystem
    ↓
VFS
    ↓
Application
```

No extraction is necessary for ordinary reads.

---

# 44. Overlay Packages

Multiple package layers can be combined:

```text
Base Package
    ↓
Patch Package
    ↓
Localization Package
    ↓
User Override
```

Lookup order must be explicit and deterministic.

Example:

```text
override
→ localization
→ patch
→ base
```

---

# 45. Package Overlay Security

An overlay must not silently replace:

```text
executable
shared library
security policy
manifest
```

unless the deployment policy explicitly permits replacement.

Resource-only overlays can be given narrower capabilities.

---

# 46. Executable Bundles

Axiom supports logical executable bundles:

```text
Application Bundle
├── executable
├── libraries
├── resources
├── models
├── locales
├── configuration defaults
└── metadata
```

The actual native platform packaging remains a separate layer.

---

# 47. Native Platform Mapping

### Windows

```text
EXE
DLL
resources
AXPK
```

can be assembled into deployment artifacts.

### Linux

```text
ELF
.so
resources
AXPK
```

### macOS

```text
.app
├── Contents/MacOS
├── Contents/Resources
└── Contents/Frameworks
```

### iOS

Resources must obey Apple application-bundle and signing restrictions.

### Android

Axiom packages are internal deployment resources; final APK/AAB integration is handled by the platform packager.

### WASM

Resources are exposed through:

```text
embedded data
host-provided VFS
package blob
```

according to the host environment.

---

# 48. Resource Compiler

Compiler/linker can transform:

```text
image
audio
shader
font
model
translation
binary data
```

into package entries.

Example:

```text
@resource("assets/logo.png")
const logo = resource(...)
```

The compiler generates resource metadata rather than copying arbitrary data into source code.

---

# 49. Embedded Resources

Small resources may be embedded directly in native binaries.

Policy:

```text
embed_if_size <= threshold
```

Large resources remain external/package-backed.

This avoids unnecessarily increasing executable memory footprint.

---

# 50. Resource Selection

Resources may contain:

```text
locale
region
theme
resolution
architecture
platform
feature_set
```

Example:

```text
icons/logo@windows.png
icons/logo@linux.png
icons/logo@android.png
```

Selection occurs through a deterministic resolver.

---

# 51. Localization

Package resource variants:

```text
locale = vi-VN
locale = en-US
locale = ja-JP
```

Fallback:

```text
vi-VN
→ vi
→ default
```

Fallback order must be deterministic.

---

# 52. Lazy Resource Loading

Resource API:

```text
ResourceHandle<T>
    metadata()
    open()
    read()
    map()
    preload()
```

Resources are loaded only when requested unless marked:

```text
eager
```

---

# 53. Memory Mapping

Uncompressed, aligned entries may be memory mapped directly.

Requirements:

```text
stored
uncompressed
page-aligned
immutable
```

Compressed entries cannot generally be directly memory mapped.

They require:

```text
decompression
```

or block-level cached views.

---

# 54. Resource Views

Large resources can expose:

```text
ByteView
TypedView<T>
Stream
BlockReader
```

without copying the entire resource.

Typed views must validate:

```text
alignment
size
endianness
format version
```

before access.

---

# 55. Model Packaging

Large AI/model resources can be represented as:

```text
model manifest
weights
tokenizer
configuration
metadata
optional quantization tables
```

Individual tensors/files may be separately chunked.

This permits partial loading.

---

# 56. Large-File Streaming

The runtime must support:

```text
open
seek
read_range
stream
prefetch
cancel
```

for multi-gigabyte assets without full materialization.

---

# 57. Prefetch

Resource prefetch may be:

```text
explicit
heuristic
package-declared
```

Example:

```text
resource.prefetch(range)
```

Prefetch is advisory and must respect BOOTSTRAP-606 budgets.

---

# 58. Dependency Manifest

Package dependencies:

```text
Dependency {
    package_id
    version_constraint
    optional
    target_constraint
    feature_constraint
}
```

The runtime validates dependencies but does not have to implement a complete public package registry.

Dependency resolution belongs to a higher deployment layer.

---

# 59. Dependency Integrity

Resolved dependencies must identify:

```text
PackageId
Version
Generation
ManifestHash
MerkleRoot
PublisherKeyId
```

A package must not silently substitute an unrelated dependency with the same name.

---

# 60. Offline Deployment

A complete offline deployment may contain:

```text
package
dependencies
object store
trust roots
deployment manifest
```

Installation must require no network connection.

---

# 61. Package Installation

Installation is transactional:

```text
stage
→ validate
→ verify
→ materialize objects
→ resolve dependencies
→ prepare generation
→ commit
→ activate
```

Failure before commit must leave the previous active generation unchanged.

---

# 62. Atomic Activation

Deployment state:

```text
generation 16 → active
generation 17 → staged
```

After successful commit:

```text
generation 17 → active
generation 16 → rollback candidate
```

The activation record itself must be updated atomically using BOOTSTRAP-611 durability primitives.

---

# 63. Rollback

Rollback switches the active generation pointer.

It does not modify immutable package contents.

Example:

```text
active = generation 17

failure

active = generation 16
```

---

# 64. Crash Recovery

If installation crashes:

```text
staging generation
```

remains incomplete.

On restart:

```text
detect incomplete transaction
→ validate journal
→ discard or resume
→ preserve active generation
```

No partially installed package may become active.

---

# 65. Package Uninstall

Uninstall removes logical references.

It does not immediately delete shared objects.

Later storage GC determines whether objects remain reachable.

This prevents one package uninstall from corrupting another package.

---

# 66. Package Updates

Update may reuse:

```text
unchanged objects
unchanged chunks
unchanged resources
```

Only new objects are transferred/stored.

---

# 67. Delta Packages

Optional delta package:

```text
BaseRoot
TargetRoot
AddedObjects[]
RemovedObjects[]
Metadata
```

The target package must be reconstructed and independently verified.

A delta must never be trusted merely because the base package was trusted.

---

# 68. Binary Delta Boundary

Binary delta algorithms are optional.

They must operate below the logical package API:

```text
Package
    ↓
Object/chunk graph
    ↓
Delta
```

The package semantics remain unchanged.

---

# 69. Package Encryption

Package contents may be encrypted using BOOTSTRAP-610.

Two modes:

```text
whole-package encryption
per-entry encryption
```

Per-entry encryption is preferred for random-access resources.

---

# 70. Encryption Metadata

Encrypted entry metadata includes:

```text
algorithm
key_id
nonce/IV
authentication_tag
key_usage
```

Keys are references to BOOTSTRAP-610 key providers, not plaintext package metadata.

---

# 71. Encryption and Deduplication

Encrypted objects generally cannot be deduplicated across different keys/nonces.

Therefore:

```text
plaintext content address
```

and:

```text
ciphertext storage identity
```

must be treated as separate concepts.

No plaintext hash may be exposed where policy forbids information leakage.

---

# 72. Package Signatures

Package signatures cover a canonical representation containing:

```text
manifest hash
entry index hash
object/Merkle root
format version
package identity
target
```

Signature implementation is delegated to BOOTSTRAP-610.

---

# 73. Signature Verification

Verification states:

```text
Unsigned
Malformed
IntegrityValid
SignatureValid
TrustedPublisher
PolicyAuthorized
```

These states must not be collapsed.

---

# 74. Publisher Identity

Publisher metadata:

```text
publisher_id
key_id
algorithm
certificate/reference
```

Trust roots come from deployment policy.

Package metadata alone cannot establish trust.

---

# 75. Capability Declaration

Packages may declare required capabilities:

```text
filesystem.read
network.connect
gpu.compute
microphone
camera
process.spawn
```

These declarations integrate with BOOTSTRAP-603.

A package requesting a capability does not automatically receive it.

---

# 76. Package Security Boundary

Package processing must protect against:

- path traversal;
- malformed archives;
- decompression bombs;
- integer overflow;
- excessive entry count;
- excessive nesting;
- huge metadata;
- hash flooding;
- corrupted indexes;
- malicious symlinks;
- invalid Unicode;
- resource exhaustion.

---

# 77. Decompression Bomb Protection

Before extraction/decompression, enforce:

```text
max_compressed_size
max_uncompressed_size
max_ratio
max_entries
max_nested_archives
max_cpu_time
```

All limits come from BOOTSTRAP-606 policy where applicable.

---

# 78. Archive Nesting

Automatic recursive extraction is prohibited.

If an entry contains another archive:

```text
resource data
```

not an instruction to recursively unpack.

Explicit application code must request nested processing.

---

# 79. Package Open Is Non-Executable

The following operations must never execute package content:

```text
open
mount
index
hash
verify
inspect
extract
```

Executable loading requires a separate privileged loader operation.

---

# 80. Executable Loading Boundary

Execution requires:

```text
package trust
→ signature policy
→ platform loader validation
→ capability policy
→ executable permission
→ process creation
```

BOOTSTRAP-613 does not bypass OS executable signing policies.

---

# 81. Dynamic Libraries

Dynamic libraries inside packages are treated as executable objects.

Loading requires explicit policy.

Library search must not accidentally allow an untrusted package to shadow trusted system libraries.

---

# 82. Package Inspection CLI

Conceptual commands:

```text
axiom pkg info app.axpk
axiom pkg list app.axpk
axiom pkg verify app.axpk
axiom pkg tree app.axpk
axiom pkg hash app.axpk
axiom pkg extract app.axpk out/
axiom pkg mount app.axpk /mnt/app
```

---

# 83. Object Store CLI

```text
axiom store stat <object>
axiom store verify
axiom store gc
axiom store pin <object>
axiom store unpin <object>
axiom store list
axiom store vacuum
```

---

# 84. Deterministic Entry Ordering

Canonical package entry order:

```text
UTF-8 normalized path
```

lexicographically sorted by byte representation.

Directories must not be dependent on host filesystem enumeration order.

---

# 85. Timestamp Normalization

Reproducible builds default to:

```text
timestamp = omitted
```

or an explicitly supplied build epoch.

Host filesystem timestamps must never silently enter package identity.

---

# 86. Permission Normalization

Portable packages must not embed arbitrary host-specific permissions.

Platform-specific permissions require explicit target metadata.

---

# 87. Host Metadata Exclusion

By default exclude:

```text
absolute source paths
username
machine name
host timestamps
inode numbers
device IDs
filesystem-specific IDs
```

unless explicitly declared as package metadata.

---

# 88. Package Reproducibility

Reproducibility requires identical:

```text
source resources
manifest
metadata
codec versions
codec parameters
object chunking
ordering
build epoch
signing inputs
```

Signatures are treated separately because key material naturally differs between signing operations unless deterministic signing is supported.

---

# 89. Package Format Versioning

Header contains:

```text
format_major
format_minor
```

Rules:

```text
same major → compatible according to declared capabilities
different major → parser must reject unless compatibility adapter exists
```

---

# 90. Forward Compatibility

Unknown manifest fields may be ignored only when marked:

```text
optional
```

Unknown mandatory fields cause rejection.

Unknown entry types must not be interpreted heuristically.

---

# 91. Backward Compatibility

New runtime versions must retain readers for supported older package versions according to the declared compatibility window.

Writers should emit the oldest format that supports required features.

---

# 92. Package Index

Index maps:

```text
path → EntryId
EntryId → ObjectId[]
ObjectId → physical storage
```

Indexes may be memory mapped for large packages.

---

# 93. Index Integrity

Index data is independently validated against:

```text
manifest hash
object IDs
sizes
Merkle root
```

No index entry may cause the reader to access bytes outside the package boundaries.

---

# 94. Corruption Detection

Corruption may occur at:

```text
header
manifest
index
compressed block
object
Merkle node
signature
```

The runtime must identify the smallest known corrupt unit.

Example:

```text
Resource: model.bin
Chunk: 182
ObjectId: ...
Checksum: mismatch
```

---

# 95. Recovery

If an object is corrupted but can be reconstructed from:

```text
another package
cache
remote store
backup
```

the object may be repaired.

The repair process must verify the reconstructed ObjectId before replacing the missing/corrupt object.

---

# 96. Package Cache Repair

Caches are disposable.

If validation fails:

```text
mark invalid
delete/rebuild
```

rather than propagating corrupted cache data into authoritative package state.

---

# 97. Resource Store Quotas

BOOTP-606 integration:

```text
max_package_count
max_package_size
max_object_count
max_store_size
max_cache_size
max_uncompressed_read
max_decompression_cpu
```

---

# 98. Package I/O Scheduling

Large package operations must be submitted through BOOTSTRAP-607.

Examples:

```text
async read object
async decompress
async verify
async install
```

CPU-heavy compression/decompression uses appropriate executor classes.

---

# 99. Cancellation

Long operations support:

```text
CancelToken
Deadline
```

including:

```text
package verify
package install
compression
decompression
GC
index building
```

Cancellation must leave persistent state valid.

---

# 100. Synchronization

Concurrent package access uses BOOTSTRAP-608.

Requirements:

- multiple readers;
- controlled writer;
- atomic generation switch;
- no partially visible index;
- no deletion of pinned/active objects.

---

# 101. Storage Integration

BOOTSTRAP-611 provides:

```text
file
directory
atomic rename
fsync
mapping
locking
VFS
```

BOOTSTRAP-613 adds package semantics above them.

---

# 102. Serialization Integration

BOOTSTRAP-612 provides canonical encoding for:

```text
manifest
entry metadata
dependency metadata
resource metadata
object indexes
```

No second incompatible metadata serialization format should be introduced.

---

# 103. Cryptography Integration

BOOTSTRAP-610 provides:

```text
hash
MAC
AEAD
signatures
key storage
certificate/trust
secure random
```

BOOTSTRAP-613 only defines package-level composition.

---

# 104. Security Integration

BOOTSTRAP-603 controls:

```text
package mount
package extraction
package installation
executable loading
network package retrieval
store access
resource capabilities
```

---

# 105. Diagnostics Integration

BOOTSTRAP-602 events:

```text
PackageOpened
PackageVerified
PackageRejected
ObjectMissing
ObjectCorrupt
PackageMounted
PackageInstalled
PackageActivated
PackageRolledBack
StoreGCStarted
StoreGCCompleted
```

Sensitive metadata must be redacted.

---

# 106. State Integration

BOOTSTRAP-600 can persist:

```text
active package generation
installation transaction
rollback generation
store roots
resource cache state
```

Checkpointing must not capture transient decompression buffers as persistent state.

---

# 107. Configuration Integration

BOOTSTRAP-601 controls:

```text
cache locations
quotas
compression defaults
package trust roots
allowed codecs
maximum extraction size
store GC policy
package mount policy
```

Configuration changes are applied through immutable snapshots.

---

# 108. Supervision Integration

BOOTSTRAP-605 may supervise:

```text
package service
resource service
store maintenance worker
background GC
package updater
```

A package failure must not automatically imply application failure unless the service dependency graph says so.

---

# 109. Resource Governor Integration

BOOTSTRAP-606 accounts:

```text
storage bytes
compressed bytes
decompressed bytes
CPU time
I/O bandwidth
I/O operations
mapped bytes
cache bytes
object count
```

---

# 110. Compiler Integration

Compiler understands:

```text
@resource
@bundle
@package
@embed
@compress
@package_entry
```

Example:

```text
@resource("assets/logo.png")
const Logo = Resource<Bytes>;
```

Compiler emits package metadata rather than application-specific extraction code.

---

# 111. Linker Integration

Linker can:

```text
collect resources
merge resource sections
deduplicate identical objects
strip unused embedded resources
construct bundle manifest
```

Dead resources should be eliminated when static reachability proves they are unused and policy allows elimination.

---

# 112. Dead Stripping

Package-aware dead stripping operates on:

```text
code symbols
resource references
package entries
dependency graph
```

It must not remove entries explicitly marked:

```text
@public_resource
@runtime_discovered
```

---

# 113. Runtime-Discovered Resources

Applications may access dynamic paths:

```text
resources.open("plugins/" + name)
```

The compiler cannot always prove reachability.

Such resources require explicit manifest declarations.

---

# 114. AI-Readable Package Metadata

Every package should optionally contain:

```text
package.axmeta
```

containing machine-readable:

```text
package identity
schema
resources
dependencies
targets
capabilities
compression
encryption
signatures
content graph
```

The metadata must be deterministic and easy for tools/agents to inspect.

---

# 115. Package Graph

AI/tooling can inspect:

```text
Package
 ├── Dependency
 ├── Resource
 │    └── Object
 │         └── Chunk
 ├── Capability
 └── Target
```

This allows agents to understand package composition without scanning binary payloads.

---

# 116. Package Search Index

Optional index:

```text
resource name
type
locale
tags
size
hash
package
dependency
```

The index must remain derived data.

It can always be regenerated from canonical package metadata.

---

# 117. Content Addressability and Build Cache

Compiler outputs can be stored as objects:

```text
source hash
+ compiler version
+ target
+ flags
+ dependency hashes
        ↓
Artifact ObjectId
```

This integrates BOOTSTRAP-613 with Axiom's precompiled/cache requirement.

---

# 118. Compiler Artifact Cache

Example:

```text
source.ax
    ↓
canonical source identity
    ↓
semantic fingerprint
    ↓
IR fingerprint
    ↓
machine-code artifact
    ↓
ObjectStore
```

If all relevant inputs match, the compiler may reuse the artifact.

---

# 119. Cache Correctness

Cache identity must include all semantically relevant inputs:

```text
compiler version
target
ABI
CPU features
optimization level
language version
feature flags
dependencies
security policy
relevant source
```

Never reuse solely by source filename.

---

# 120. Package Build Pipeline

Canonical pipeline:

```text
collect inputs
    ↓
normalize
    ↓
hash
    ↓
chunk
    ↓
deduplicate
    ↓
compress
    ↓
build manifest
    ↓
build indexes
    ↓
build Merkle tree
    ↓
sign
    ↓
write AXPK
    ↓
verify
```

---

# 121. Build Verification

A package builder should automatically reopen its output and verify:

```text
header
manifest
indexes
objects
compression
hashes
Merkle root
signature
```

before declaring success.

---

# 122. Package Self-Check

CLI:

```text
axiom pkg verify --deep package.axpk
```

Modes:

```text
structural
integrity
deep
signature
runtime
```

---

# 123. Structural Verification

Checks:

- bounds;
- integer overflow;
- offsets;
- sizes;
- entry names;
- index consistency;
- version support.

No payload decompression is required.

---

# 124. Deep Verification

Deep verification additionally:

```text
decompress every block
verify every checksum
verify every ObjectId
verify Merkle root
```

This is expensive and therefore optional.

---

# 125. Package Mount Verification

Mount may use:

```text
lazy verification
```

for trusted local packages.

Security-sensitive deployments may require:

```text
full verification before mount
```

Policy determines behavior.

---

# 126. Trust Policy

Example:

```text
Development:
    unsigned allowed

Testing:
    signed preferred

Production:
    signed required

HighSecurity:
    signed + trusted publisher + encrypted
```

Policy is supplied by BOOTSTRAP-603/610.

---

# 127. Secure Temporary Files

Extraction and package staging must use BOOTSTRAP-611 secure temporary storage.

Requirements:

- unpredictable temporary identity;
- exclusive creation;
- restrictive permissions;
- cleanup on failure;
- no attacker-controlled filename reuse.

---

# 128. Atomic Package Writer

Package generation should write:

```text
temporary file
→ fsync
→ rename
→ fsync parent where required
```

rather than overwriting the target package directly.

---

# 129. Package Store Layout

Logical store:

```text
Store
├── objects
├── packages
├── generations
├── manifests
├── leases
├── pins
├── staging
└── indexes
```

Physical layout is implementation-defined.

---

# 130. Generation Registry

Registry:

```text
PackageId
    ├── version
    ├── generation
    ├── manifest_hash
    ├── merkle_root
    ├── active
    └── installation_state
```

The registry itself is transactional.

---

# 131. Multiple Generations

Old generations may remain for:

```text
rollback
diagnostics
shared dependencies
user selection
```

GC removes them only when unreachable.

---

# 132. Package Lifecycle

```text
Unknown
  ↓
Discovered
  ↓
Parsed
  ↓
Verified
  ↓
Staged
  ↓
Installed
  ↓
Activated
  ↓
Superseded
  ↓
Reclaimable
  ↓
Collected
```

---

# 133. Invalid Lifecycle

```text
Discovered
   ↓
Invalid
```

or:

```text
Installed
   ↓
Corrupt
   ↓
Quarantined
```

Corrupt packages must not automatically become active.

---

# 134. Quarantine

Security or integrity failures may move packages into:

```text
quarantine/
```

The package remains inspectable for diagnostics but is unavailable for execution/mount according to policy.

---

# 135. Package Removal

Removal sequence:

```text
disable activation
→ unmount
→ release pins
→ remove logical generation
→ update registry
→ background object GC
```

No immediate recursive physical deletion is required.

---

# 136. Mount Lifetime

A mounted package holds a reference/lease on:

```text
package generation
object index
required objects
```

This prevents concurrent storage GC from deleting active objects.

---

# 137. Multi-Process Access

Object stores may support concurrent processes through:

```text
atomic file operations
locks
generation records
append-only metadata
```

A process must not rely on process-local state for global correctness.

---

# 138. Store Locking

Lock granularity should favor:

```text
per-object
per-generation
per-registry
```

rather than one global lock.

Read operations should remain highly concurrent.

---

# 139. Crash-Safe Store GC

GC must tolerate process termination at any point.

A safe sequence:

```text
mark
→ persist mark generation
→ reclaim
→ commit
```

Interrupted GC must never delete an object that belongs to an active root.

---

# 140. Object Verification Before Reuse

Cached object:

```text
ObjectId X
```

may be reused only after:

```text
physical bytes
→ integrity verification
→ identity hash
→ X
```

This prevents corrupted cache poisoning.

---

# 141. Resource Limits

Package parser limits include:

```text
max_header
max_manifest
max_entries
max_path_length
max_dependency_count
max_chunk_count
max_object_size
max_total_size
max_nesting
```

All limits are explicit configuration.

---

# 142. Integer Safety

All size/offset calculations must use checked arithmetic.

Overflow:

```text
error
```

never wraparound.

---

# 143. Memory Safety

The package subsystem must avoid raw pointer arithmetic at the language API level.

Internal native implementation may use low-level operations only behind validated boundaries.

---

# 144. Error Model

Representative errors:

```text
PackageNotFound
InvalidMagic
UnsupportedVersion
MalformedManifest
InvalidPath
IndexCorrupt
ObjectMissing
ObjectCorrupt
ChecksumMismatch
HashMismatch
SignatureInvalid
PublisherUntrusted
CodecUnsupported
DecompressionLimit
QuotaExceeded
PermissionDenied
ActivationFailed
DependencyMissing
DependencyMismatch
EncryptionKeyUnavailable
Cancelled
DeadlineExceeded
```

Errors must retain machine-readable codes.

---

# 145. Struct-Only API

Example:

```text
struct Package {
    id: PackageId
    generation: u64
}

fn Package.open(
    self: Package,
    path: Path,
) -> Result<PackageHandle>

fn Package.mount(
    self: Package,
    vfs: Vfs,
) -> Result<MountHandle>
```

No classes are required.

---

# 146. Codec API

```text
struct Codec;

fn Codec.encode(
    self: Codec,
    input: Reader,
    output: Writer,
    config: CompressionConfig,
) -> Result<CompressionStats>

fn Codec.decode(
    self: Codec,
    input: Reader,
    output: Writer,
) -> Result<DecompressionStats>
```

---

# 147. Object Store API

```text
struct ObjectStore;

fn ObjectStore.put(
    self: ObjectStore,
    source: Reader,
) -> Result<ObjectId>

fn ObjectStore.open(
    self: ObjectStore,
    id: ObjectId,
) -> Result<ObjectReader>

fn ObjectStore.collect(
    self: ObjectStore,
    policy: GcPolicy,
) -> Result<GcReport>
```

---

# 148. Package Builder API

```text
struct PackageBuilder;

fn PackageBuilder.add(
    self: PackageBuilder,
    path: Path,
    source: Reader,
    options: EntryOptions,
)

fn PackageBuilder.finalize(
    self: PackageBuilder,
) -> Result<PackageArtifact>
```

---

# 149. Package Mount API

```text
struct PackageMount;

fn PackageMount.open(
    self: PackageMount,
    path: Path,
) -> Result<ResourceReader>

fn PackageMount.read(
    self: PackageMount,
    path: Path,
    range: ByteRange,
) -> Result<ByteBuffer>
```

---

# 150. Override Mechanism

Since Axiom uses struct-only methods, package providers can implement alternative behavior through traits:

```text
trait PackageSource {
    fn open(...)
    fn stat(...)
    fn read(...)
}
```

An implementation may override the default backend without classes.

---

# 151. Compiler IR

Introduce package-related IR operations:

```text
resource_ref
resource_embed
resource_open
package_mount
package_hash
package_verify
object_lookup
compressed_read
```

These are lowered to runtime or static-resource operations.

---

# 152. Constant Folding

For compile-time-known resources:

```text
resource_hash
resource_size
resource_id
```

may become constants.

---

# 153. Link-Time Resource Deduplication

If:

```text
resource A
resource B
```

have identical content:

```text
ObjectId(A) == ObjectId(B)
```

the linker should emit one physical object.

---

# 154. Minimal Runtime Profiles

Possible profiles:

```text
PackageNone
PackageReadOnly
PackageRuntime
PackageBuilder
PackageStore
PackageFull
```

Applications requiring only embedded resources need not link:

```text
ObjectStore
PackageInstaller
ArchiveWriter
```

---

# 155. Dead Stripping

Unused features are removable:

```text
ZIP
TAR
ZSTD
encryption
signatures
installer
object store
GC
network package transport
```

when not referenced.

---

# 156. Embedded Profile

Embedded targets may use:

```text
read-only AXPK
stored compression
small index
no package installer
no object GC
no dynamic package updates
```

This keeps firmware small.

---

# 157. WASM Profile

WASM package support may use:

```text
host-provided package
embedded package bytes
virtual filesystem
```

with all OS filesystem operations delegated to the host.

---

# 158. Mobile Profile

Android/iOS profiles must account for:

- application sandbox;
- read-only application resources;
- platform signing;
- storage lifecycle;
- background execution limits.

Package update mechanisms must not bypass platform application distribution rules.

---

# 159. Package Transport Boundary

613 defines storage/package semantics, not a mandatory network distribution protocol.

Possible transports:

```text
HTTP
HTTPS
IPC
local file
USB
custom deployment channel
```

are supplied externally.

---

# 160. HTTP Integration

A future deployment layer can use BOOTSTRAP-609 to retrieve:

```text
manifest
object
chunk
delta
signature
```

The package engine remains transport-independent.

---

# 161. Partial Download

Content-addressed packages allow:

```text
manifest first
→ determine required objects
→ download only required objects
```

Useful for:

- optional resources;
- platform-specific resources;
- lazy models;
- application startup.

---

# 162. Package Range Access

For monolithic AXPK files:

```text
range(offset, length)
```

can retrieve only required sections.

This is useful with remote-capable storage but must not make the package runtime dependent on networking.

---

# 163. Package Streaming

A package may be consumed as a stream if:

```text
manifest
index
objects
```

are ordered for streaming.

However, random-access features require indexes available before the corresponding read.

---

# 164. Package Layout Modes

Builder may choose:

```text
Streaming
RandomAccess
Compact
Deduplicated
RemoteOptimized
Embedded
```

The mode changes physical layout but not logical package semantics.

---

# 165. Compression Dictionaries

Optional shared dictionaries:

```text
DictionaryId
DictionaryObjectId
```

A package must declare the dictionary dependency explicitly.

A decoder must never guess a dictionary.

---

# 166. Dictionary Security

A dictionary is treated as package data.

It must be integrity-verified before use.

---

# 167. Compression Parallelism

Independent blocks may be processed concurrently.

The scheduler must honor:

```text
CPU quota
memory quota
I/O quota
```

from BOOTSTRAP-606.

---

# 168. Compression Memory Limits

Codec configuration must support bounded memory.

If a codec cannot honor the configured bound:

```text
CodecUnsupportedUnderPolicy
```

must be returned.

---

# 169. Archive Import

ZIP/TAR import must normalize:

```text
paths
timestamps
permissions
UID/GID
extended attributes
symlinks
```

according to explicit import policy.

The host archive's metadata must not silently become package identity.

---

# 170. Archive Export

Export may be lossy.

For example:

```text
AXPK capabilities
signatures
content-addressed identity
```

may not map directly into TAR.

The exporter must declare unsupported semantic loss.

---

# 171. Package Metadata Schema

Recommended `.axschema`:

```text
package.schema.axschema
```

Defines:

```text
PackageManifest
PackageEntry
Dependency
ResourceVariant
SignatureInfo
CompressionInfo
EncryptionInfo
```

---

# 172. AI Tooling Commands

Recommended:

```text
axiom pkg schema
axiom pkg graph
axiom pkg resources
axiom pkg deps
axiom pkg capabilities
axiom pkg objects
axiom pkg verify
```

All should support machine-readable:

```text
--format=axbin
--format=json
--format=text
```

---

# 173. Deterministic Graph Output

Graph traversal order must be canonical.

This allows agents and build systems to compare package structures without host-dependent ordering.

---

# 174. Package Fingerprints

Expose:

```text
ManifestHash
ContentRoot
PackageFingerprint
PublisherFingerprint
```

separately.

Do not collapse them into one ambiguous identifier.

---

# 175. Resource Fingerprints

Each resource may expose:

```text
logical_name
size
content_id
schema_id
format
```

Applications can use these for cache invalidation.

---

# 176. Resource Cache Invalidation

When:

```text
ObjectId unchanged
```

cached decoded resource may remain valid if decoder/schema version is compatible.

Cache key:

```text
ObjectId
+ decoder_version
+ relevant_options
```

---

# 177. Decoded Resource Cache

For expensive assets:

```text
package bytes
→ decode
→ runtime representation
→ cache
```

Examples:

```text
image texture
shader
model tensor
font atlas
audio index
```

Decoded caches are disposable and budgeted by BOOTSTRAP-606.

---

# 178. Package Resource Lifetime

Resource handles must prevent referenced objects from being reclaimed.

The runtime may use:

```text
generation-safe handles
leases
pins
```

rather than exposing raw pointers.

---

# 179. No Hidden Global Cache

Package APIs must not silently allocate unlimited global caches.

Caches must be:

```text
explicit
bounded
observable
configurable
```

---

# 180. Package Observability

Metrics:

```text
packages_opened
packages_verified
bytes_read
bytes_decompressed
compression_ratio
cache_hits
cache_misses
object_dedup_hits
gc_bytes_reclaimed
mount_count
verification_failures
```

---

# 181. Performance Targets

For local package reads:

```text
metadata lookup: O(log N) or O(1) indexed
object lookup: O(1) average
stored read: near filesystem throughput
decompression: codec-native throughput
```

Package metadata should not require scanning all entries.

---

# 182. Startup Target

A mounted package should be able to expose metadata after reading:

```text
header
manifest
index
```

rather than scanning every payload object.

---

# 183. Memory Target

For a package containing:

```text
N entries
```

metadata memory should scale approximately with:

```text
O(N)
```

and payload size should not determine resident memory.

---

# 184. Large Package Target

A package containing:

```text
10+ million entries
```

must be architecturally supportable through paged/mapped indexes rather than requiring all metadata to be heap-resident.

---

# 185. Package Index Paging

Large indexes may be:

```text
memory mapped
paged
compressed
multi-level
```

without changing logical APIs.

---

# 186. Package Concurrency

Required:

```text
many readers
few writers
atomic activation
parallel decompression
parallel verification
```

A single global mutex is prohibited on normal read paths.

---

# 187. Failure Isolation

A corrupt optional resource must not automatically invalidate the entire package unless package policy marks it mandatory.

Example:

```text
optional localization missing
```

may be recoverable.

A corrupt executable is generally fatal to executable activation.

---

# 188. Mandatory Resources

Manifest may declare:

```text
required = true
```

Activation verifies required resources before success.

---

# 189. Optional Resources

Optional entries can be lazily verified.

Failure becomes a resource-level error.

---

# 190. Package Health

Package state:

```text
Healthy
Degraded
Corrupt
Untrusted
Unavailable
```

Diagnostics can expose package health without executing its contents.

---

# 191. Package Security Events

Security-relevant events:

```text
PackageSignatureRejected
PackagePublisherRejected
PackageCapabilityDenied
PackagePathTraversalAttempt
PackageDecompressionLimit
PackageObjectHashMismatch
PackageExecutableLoadDenied
```

These integrate with BOOTSTRAP-602.

---

# 192. Audit Requirements

Audit records must contain:

```text
package_id
generation
manifest_hash
event
timestamp
process/service identity
result
```

Secrets and plaintext key material are excluded.

---

# 193. Fuzzing

Mandatory fuzz targets:

```text
AXPK parser
manifest decoder
AXBIN decoder
ZIP reader
TAR reader
compression decoder
index parser
Merkle parser
path normalizer
package installer
```

---

# 194. Fault Injection

Test failures:

```text
disk full
partial write
truncated package
corrupt header
corrupt index
corrupt object
missing chunk
wrong hash
bad signature
missing key
unsupported codec
cancelled install
process crash
power-loss simulation
```

---

# 195. Crash Testing

Kill the process at every installation phase:

```text
before stage
during object write
after object write
before manifest
after manifest
before activation
during activation
after activation
```

Recovery must preserve either:

```text
old active generation
```

or:

```text
fully valid new generation
```

never an intermediate state.

---

# 196. Property Tests

Properties:

```text
decode(encode(x)) == x
hash(x) stable
same canonical input → same package identity
duplicate content → same ObjectId
corrupt content → verification failure
failed install → old generation preserved
uninstall shared package → shared objects preserved
```

---

# 197. Differential Tests

For compatibility codecs:

```text
Axiom ZIP reader ↔ reference ZIP implementations
Axiom TAR reader ↔ reference TAR implementations
Axiom DEFLATE ↔ reference implementations
```

Tests must validate semantics, not assume identical implementation details.

---

# 198. Security Invariants

1. Package parsing never executes code.
2. Package paths cannot escape package root.
3. Invalid sizes never wrap.
4. Hash mismatch rejects the object.
5. Signature mismatch rejects trust.
6. Untrusted package cannot acquire capabilities automatically.
7. Executable loading requires explicit policy.
8. Store GC cannot delete active/pinned objects.
9. Failed activation cannot corrupt active generation.
10. Package metadata cannot silently grant permissions.

---

# 199. Determinism Invariants

1. Entry order is canonical.
2. Metadata order is canonical.
3. Host timestamps are excluded unless explicit.
4. Host paths are excluded unless explicit.
5. Compression parameters are explicit.
6. Chunking parameters are explicit.
7. Codec version is recorded.
8. Build target is recorded.
9. Package identity is reproducible from canonical inputs.
10. Package graph traversal is deterministic.

---

# 200. Performance Invariants

1. Read-only package access is lock-light.
2. Metadata lookup is indexed.
3. Large resources stream.
4. Independent blocks may decompress concurrently.
5. Object deduplication avoids redundant writes.
6. Cache operations are bounded.
7. Package runtime has no mandatory GC.
8. Small applications need not link package builder/store components.
9. Embedded targets can use read-only minimal profiles.
10. Large package metadata can be paged/mapped.

---

# 201. ABI Boundary

Stable ABI types should use:

```text
fixed-width integers
opaque handles
byte spans
UTF-8 views
explicit structs
status/error codes
```

Avoid exposing implementation-specific codec objects across ABI boundaries.

---

# 202. FFI

External code can consume:

```text
package handle
resource handle
object ID
byte reader
byte writer
```

through C-compatible ABI wrappers.

No C++ ABI dependency is required.

---

# 203. Native Toolchain Dependency Rule

The Axiom package engine must be capable of producing and consuming AXPK without:

```text
Python
Java
Node.js
.NET
third-party package manager
external runtime
```

being required by the native tool itself.

External tools may be used during development, but not as a runtime prerequisite.

---

# 204. Package Builder Bootstrap

The initial compiler/toolchain can implement a minimal builder:

```text
STORE codec
single manifest
single index
SHA-256
unsigned packages
```

Later stages add:

```text
compression
signatures
encryption
object store
delta updates
```

This prevents bootstrap circularity.

---

# 205. Minimal Bootstrap Format

`AXPK v1` minimum:

```text
header
manifest
entry table
stored payload
```

No dependency on content-addressed storage is required.

---

# 206. Evolution Path

```text
AXPK v1
    ↓
compression
    ↓
signatures
    ↓
chunking
    ↓
content addressing
    ↓
Merkle graph
    ↓
delta deployment
```

Each capability remains backward-compatible where practical.

---

# 207. Separation of Concerns

613 does not define:

- application marketplace;
- public package registry;
- billing;
- licensing business rules;
- source-code repository;
- CI/CD service;
- cloud storage service;
- mandatory network protocol.

Those belong to higher layers.

---

# 208. Licensing Metadata

Package metadata may contain:

```text
license_id
license_text_reference
copyright
attribution
```

but license enforcement is not part of the core runtime.

---

# 209. SBOM Boundary

Optional package metadata may contain software component information:

```text
component
version
source
license
hash
```

The package runtime exposes it but does not require an external SBOM system.

---

# 210. Package Attestation Boundary

Future systems may attach:

```text
build provenance
source commit
compiler fingerprint
builder identity
reproducibility result
```

These are metadata extensions, not mandatory runtime semantics.

---

# 211. Resource Type Registry

Resource types may use stable identifiers:

```text
image/png
audio/wav
model/axiom
shader/axiom
font/ttf
application/octet-stream
```

The registry must remain extensible.

---

# 212. Resource Decoder Boundary

A package only stores data.

Decoders are separate:

```text
Resource
    ↓
DecoderRegistry
    ↓
TypedResource
```

This prevents the package runtime from becoming a monolithic media framework.

---

# 213. Decoder Security

Untrusted resources must be passed through decoder-specific resource limits.

Package verification alone does not prove that a media decoder is safe.

---

# 214. Package Resource Capability

A decoder may require capabilities.

For example:

```text
GPU resource
```

may require:

```text
gpu.compute
```

but reading the package itself does not.

---

# 215. Package Store Namespaces

Object stores must distinguish:

```text
system
user
application
build
temporary
```

to prevent accidental cross-domain trust.

---

# 216. Namespace Isolation

An application must not automatically read another application's private object store.

BOOTSTRAP-603 capability policy controls cross-namespace access.

---

# 217. Shared Store

A shared global store may exist for deduplication, but:

```text
content identity
```

does not imply:

```text
authorization
```

A package still needs permission to reference/read the object.

---

# 218. Side-Channel Consideration

Content-addressed storage can reveal that two parties possess identical content.

Sensitive deployments may therefore disable cross-principal deduplication.

---

# 219. Privacy Mode

Package store policy may specify:

```text
dedup_scope = application
dedup_scope = user
dedup_scope = system
dedup_scope = none
```

---

# 220. Secure Package Mode

High-security package policy:

```text
signature required
trusted publisher required
encryption required
no executable overlays
no symlinks
no cross-user dedup
full verification
```

---

# 221. Development Package Mode

Development profile may allow:

```text
unsigned
hot reload
loose resources
debug metadata
```

but these permissions must never silently carry into production.

---

# 222. Hot Reload

Development packages may replace a mounted resource generation.

Activation:

```text
build
→ verify
→ stage
→ switch generation
```

Existing resource handles continue using the old generation until released.

---

# 223. Generation Isolation

Generation 17 and generation 18 may coexist.

A handle opened from generation 17 must not unexpectedly resolve to generation 18.

---

# 224. Resource Handle Identity

Recommended:

```text
ResourceHandle {
    generation
    entry_id
    object_id
}
```

This prevents accidental cross-generation confusion.

---

# 225. Package Update Compatibility

An application can declare:

```text
requires package API version X
```

while resources evolve independently.

Package versioning must therefore distinguish:

```text
format version
package version
resource schema version
application ABI version
```

---

# 226. Resource Schema Evolution

Structured resources should use BOOTSTRAP-612 schema IDs.

Example:

```text
ResourceSchemaId
SchemaVersion
MigrationVersion
```

---

# 227. No Automatic Data Migration

Opening a package does not automatically rewrite resource data.

Migrations are explicit and transactional.

---

# 228. Package Snapshot

A package generation itself is an immutable snapshot.

Snapshot identity:

```text
PackageId
Generation
ManifestHash
ContentRoot
```

---

# 229. Package Export

A logical package can be exported into:

```text
single AXPK
directory tree
object bundle
archive
```

The export layer must preserve logical hashes where format permits.

---

# 230. Package Import

Import verifies:

```text
syntax
paths
sizes
hashes
metadata
policy
```

before creating authoritative objects.

---

# 231. Import Isolation

Imported objects should initially enter:

```text
staging namespace
```

and become authoritative only after successful verification.

---

# 232. Package Builder Resource Ordering

Recommended deterministic order:

```text
manifest
directories
executables
libraries
resources
metadata
```

followed by canonical path ordering where semantic ordering is irrelevant.

The canonical specification must ultimately define one exact ordering for reproducible output.

---

# 233. Binary Layout Alignment

Large payload objects should support configurable alignment:

```text
1
4
8
16
4096
```

Page alignment is required for mmap-capable entries.

---

# 234. Sparse Package Objects

Sparse resources may contain holes.

The logical representation must preserve:

```text
logical size
allocated ranges
```

without requiring physical zero storage.

---

# 235. Object Compression and Encryption Order

Canonical pipeline:

```text
plaintext
→ chunk
→ compress
→ encrypt
→ store
```

Decryption:

```text
stored
→ decrypt
→ decompress
→ verify logical object
```

The package policy must define which hash is over plaintext versus ciphertext.

---

# 236. Integrity Layering

Possible integrity checks:

```text
transport checksum
compressed-block checksum
ciphertext authentication
plaintext ObjectId
Merkle root
package signature
```

Each layer has a separate purpose.

---

# 237. Verification Ordering

Efficient verification:

```text
bounds
→ structural parse
→ ciphertext authentication
→ decompression
→ plaintext hash
→ Merkle
→ signature
```

Implementations may optimize order provided security semantics remain equivalent.

---

# 238. Package Signature Scope

Signature must authenticate the canonical logical package identity, not merely physical byte offsets.

This permits storage-layout changes without changing logical package semantics where the format explicitly allows it.

---

# 239. Physical vs Logical Identity

Distinguish:

```text
LogicalPackageId
ContentRoot
PhysicalPackageFileHash
```

A repacked package can have:

```text
same logical content root
different physical file hash
```

---

# 240. Package Repacking

Repacking may:

```text
change block layout
change compression
change physical offsets
```

without changing logical content.

The builder must indicate whether the resulting package remains semantically identical.

---

# 241. Package Identity Algorithm

Recommended:

```text
ContentRoot =
H(
    canonical manifest
    + ordered entry identities
    + dependency identities
)
```

Payload objects are referenced by their content identities.

---

# 242. Merkle Proof

The package store may provide:

```text
prove(ObjectId, ContentRoot)
```

returning the path of hashes needed to verify membership.

Useful for remote/partial retrieval.

---

# 243. Remote Object Store Boundary

Future remote store:

```text
ObjectId
→ fetch
→ verify
→ local cache
```

The local package runtime treats remote objects as another transport-backed source.

---

# 244. Offline-First Principle

If all required objects are locally available:

```text
package operation must not require network access
```

Network retrieval is an optional policy.

---

# 245. Missing Object Handling

When a package references a missing object:

```text
ObjectMissing
```

The resolver may attempt configured providers:

```text
local store
→ package
→ cache
→ remote provider
```

subject to capability policy.

---

# 246. Object Provider API

```text
trait ObjectProvider {
    fn has(id)
    fn fetch(id)
}
```

Possible implementations:

```text
PackageProvider
FileProvider
StoreProvider
RemoteProvider
EmbeddedProvider
```

---

# 247. Provider Trust

Every provider declares:

```text
trust_level
capabilities
integrity guarantees
```

Object content is still verified by ObjectId.

---

# 248. Package Resolver

Resolver combines:

```text
package manifest
dependency constraints
available package generations
target
features
security policy
```

and produces a deterministic deployment graph.

---

# 249. Resolver Scope

The resolver in 613 is intentionally foundational.

A future package manager may add:

```text
registry
semver solving
user repositories
authentication
publishing
```

without changing the package runtime.

---

# 250. Feature Flags

Package dependencies may specify:

```text
feature = gpu
feature = audio
feature = localization
```

The resolver must record selected features in deployment identity.

---

# 251. Package Build Manifest

Recommended source-level manifest:

```text
package {
    id = "com.example.app"
    version = "1.0.0"

    target windows-x64
    target linux-x64

    resource "assets/**"
    dependency "com.example.core" version "^2"
}
```

The exact syntax belongs to the language/toolchain layer.

---

# 252. Package Lock

A deterministic lock artifact may record:

```text
resolved package
version
generation
content root
publisher
signature
```

This supports reproducible deployment.

---

# 253. Lock Integrity

Build tools must verify that the lock record corresponds to the actual package content.

---

# 254. Package Build Cache

Build cache key:

```text
source/input fingerprints
+ package configuration
+ compiler fingerprint
+ target
```

Cached result:

```text
ObjectId
```

---

# 255. Incremental Packaging

If only one resource changes:

```text
unchanged objects reused
new object generated
manifest updated
Merkle path recomputed
```

No complete resource recompression is required when chunking permits reuse.

---

# 256. Incremental Manifest

Manifest generation should avoid nondeterministic fields so unchanged package metadata remains stable.

---

# 257. Package Patch Size

Chunk-level deduplication should make typical resource updates proportional to changed content rather than total package size.

This is a design target, not a universal guarantee.

---

# 258. Resource Prewarming

Application startup may declare:

```text
preload resource A
preload range B
```

The package runtime submits these through BOOTSTRAP-607.

---

# 259. Startup Critical Path

Only startup-critical resources should be synchronously required.

Optional resources remain lazy.

This prevents large model/media assets from blocking application startup unnecessarily.

---

# 260. Package Resource Priority

Resources may declare:

```text
critical
high
normal
low
background
```

Scheduling integrates with BOOTSTRAP-606/607.

---

# 261. Resource Cancellation

Cancelled prefetch/decode must release:

```text
temporary buffers
leases
executor tasks
I/O requests
```

without invalidating immutable package state.

---

# 262. Package Diagnostics Context

Every operation may carry:

```text
package_id
generation
entry_id
object_id
```

into BOOTSTRAP-602 tracing.

---

# 263. Error Context

Example:

```text
PackageError {
    code
    package_id
    generation
    path?
    object_id?
    cause
}
```

Error chains must preserve root cause.

---

# 264. Package Logging

Normal successful reads should not generate excessive logs.

Use metrics/traces for high-frequency operations.

Warnings/errors are structured.

---

# 265. Resource Usage Metrics

Track:

```text
per package
per generation
per resource
```

where practical.

Hot paths should use sampled or aggregated counters.

---

# 266. Test Backend

A deterministic in-memory backend:

```text
MemoryObjectStore
MemoryPackage
FakeCodec
FakeClock
FakeSigner
```

allows unit testing without host filesystem dependencies.

---

# 267. Deterministic Fault Backend

Inject:

```text
read failure at byte N
write failure at operation N
hash mismatch
missing object
compression error
signature failure
disk-full
```

---

# 268. Package Parser Fuzz Invariants

For arbitrary bytes:

```text
never crash
never execute code
never OOB read
never OOB write
never allocate unbounded memory
never hang indefinitely
```

---

# 269. Compression Fuzz Invariants

For arbitrary compressed data:

```text
bounded CPU
bounded memory
safe rejection
no memory corruption
```

---

# 270. Archive Bomb Test

Test:

```text
tiny compressed input
→ enormous logical output
```

must terminate with:

```text
DecompressionLimit
```

rather than exhausting resources.

---

# 271. Store Consistency Test

Repeated:

```text
put(x)
put(x)
put(x)
```

must result in one logical object identity.

---

# 272. Concurrent Store Test

Multiple processes/threads inserting identical objects must converge to:

```text
one valid object
```

without corruption.

---

# 273. GC Race Test

Run:

```text
read object
GC
release object
GC
```

concurrently.

Active references must prevent premature deletion.

---

# 274. Mount/GC Test

A mounted package must remain readable while background GC executes.

---

# 275. Update/Rollback Test

Perform:

```text
install A
activate A
stage B
crash
recover
```

Expected:

```text
A remains active
```

unless B had already been atomically committed.

---

# 276. Signature Test

Test:

```text
valid signature
wrong key
wrong manifest
wrong content root
expired trust
untrusted publisher
modified package
```

Each must produce the correct security state.

---

# 277. Encryption Test

Test:

```text
correct key
wrong key
corrupt ciphertext
corrupt authentication tag
missing provider
```

with no plaintext leakage on failure.

---

# 278. Reproducibility Test

Build the same package:

```text
machine A
machine B
different filesystem
different file enumeration order
```

Expected canonical output identity must match where the declared toolchain/codec profile is deterministic.

---

# 279. Compatibility Test

Every supported AXPK format version receives:

```text
read tests
write tests
upgrade tests
downgrade compatibility tests where supported
```

---

# 280. Acceptance Criteria

The implementation is considered complete only when all of the following hold:

1. AXPK header is versioned and validated.
2. Manifest uses AXBIN/AXBF.
3. Entry paths are normalized.
4. Path traversal is impossible through normal APIs.
5. STORE codec works without external dependencies.
6. Streaming compression API exists.
7. Streaming decompression API exists.
8. Compression limits are enforced.
9. Random-access blocks are supported.
10. ZIP import works.
11. TAR import works.
12. Native AXPK read/write works.
13. Package manifests are deterministic.
14. Entry ordering is deterministic.
15. Host timestamps do not affect identity by default.
16. Object IDs are cryptographic.
17. Object storage is immutable.
18. Duplicate objects are deduplicated.
19. Large resources can be chunked.
20. Merkle roots can be generated.
21. Merkle roots can be verified.
22. Packages can be mounted as VFS.
23. Package mounts are read-only by default.
24. Lazy resource loading works.
25. Large resources stream without full RAM materialization.
26. Stored aligned resources can be memory mapped.
27. Compressed resources support block reads.
28. Package signatures integrate with 610.
29. Trust policy integrates with 603.
30. Package capabilities integrate with 603.
31. Encryption integrates with 610.
32. Encrypted entries can be independently authenticated.
33. Cache quotas integrate with 606.
34. Compression work integrates with 607.
35. Concurrent access integrates with 608.
36. Package state integrates with 600.
37. Package configuration integrates with 601.
38. Diagnostics integrate with 602.
39. Supervised package services integrate with 605.
40. Storage uses 611.
41. Schemas use 612.
42. Compiler can embed resources.
43. Linker can package resources.
44. Unused static resources can be stripped.
45. Runtime-discovered resources can be declared explicitly.
46. Package installation is transactional.
47. Activation is atomic.
48. Rollback does not rewrite immutable contents.
49. Interrupted installation cannot become active.
50. Uninstall preserves shared objects.
51. Store GC respects roots.
52. Pins prevent reclamation.
53. Leases prevent premature reclamation.
54. Cache corruption is recoverable.
55. Missing objects produce structured errors.
56. Corrupt objects are detected.
57. Package verification supports structural mode.
58. Package verification supports deep mode.
59. Package inspection requires no execution.
60. Package opening cannot execute arbitrary code.
61. Executable loading is policy-controlled.
62. Dynamic libraries are treated as executable content.
63. Offline deployment works.
64. Package dependencies are represented deterministically.
65. Package lock data can pin content roots.
66. Incremental packaging reuses unchanged objects.
67. Delta packages can be independently verified.
68. AI-readable metadata can be generated.
69. CLI inspection tools exist.
70. CLI verification tools exist.
71. Fuzzing covers all binary parsers.
72. Decompression-bomb protection is tested.
73. Crash recovery is tested.
74. Power-loss simulation is tested.
75. Concurrent object insertion is tested.
76. Concurrent GC is tested.
77. Package reproducibility is tested.
78. Cross-platform path normalization is tested.
79. Minimal runtime profiles link without unused subsystems.
80. Embedded read-only package mode works.
81. WASM host-backed package mode works.
82. Mobile sandbox restrictions are respected.
83. Native Windows packaging integration exists.
84. Native Linux packaging integration exists.
85. Native macOS bundle integration exists.
86. iOS resource packaging respects platform constraints.
87. Android resource packaging respects platform constraints.
88. Package format evolution is explicitly versioned.
89. Unknown mandatory metadata is rejected.
90. No mandatory third-party runtime dependency exists.
91. Package APIs use struct-only Axiom style.
92. No package feature requires a garbage collector.
93. Package operations have bounded resource consumption.
94. Package identity distinguishes logical and physical identity.
95. Security events are auditable.
96. Secret material never enters ordinary package logs.
97. Cross-principal deduplication can be disabled.
98. Package generations remain isolated.
99. Resource handles retain generation identity.
100. Full package verification can independently reconstruct the content root.

---

# 281. Final Architecture

```text
                    ┌──────────────────────────┐
                    │      Axiom Application    │
                    └────────────┬─────────────┘
                                 │
                         Resource API
                                 │
                    ┌────────────▼─────────────┐
                    │       Package API         │
                    └────────────┬─────────────┘
                                 │
            ┌────────────────────┼────────────────────┐
            │                    │                    │
       Archive API          Object Store        Resource Resolver
            │                    │                    │
     ZIP / TAR / AXPK       CAS / Chunks          Variants
            │                    │                    │
            └────────────────────┼────────────────────┘
                                 │
                       Package Engine
                                 │
          ┌──────────────────────┼──────────────────────┐
          │                      │                      │
    Compression              Integrity              Encryption
          │                      │                      │
          └──────────────────────┼──────────────────────┘
                                 │
                         Merkle / Hash Graph
                                 │
                         VFS / Package Mount
                                 │
                     BOOTSTRAP-611 Storage
                                 │
               ┌─────────────────┼─────────────────┐
               │                 │                 │
             File              mmap              Device
               │                 │                 │
               └─────────────────┼─────────────────┘
                                 │
                              OS/Host

Cross-cutting:
603 Security/Capabilities
606 Resource Governor
607 Scheduler/Async
608 Synchronization
610 Cryptography
612 Serialization
602 Diagnostics
601 Configuration
600 State/Recovery
605 Supervision
```

---

# 282. Architectural Invariants

The subsystem is valid only if:

```text
Package parsing != code execution

Package identity != physical file identity

Object identity != authorization

Signature validity != publisher trust

Compression != encryption

Cache != authoritative state

Storage GC != language GC

Package generation != mutable directory

Resource name != resource content identity
```

The central invariant is:

```text
Immutable Content
      ↓
Content Identity
      ↓
Integrity Verification
      ↓
Trust / Policy
      ↓
Package Generation
      ↓
VFS / Resource Access
```

---

# 283. Completion

**BOOTSTRAP-613 is complete.**

The resulting subsystem gives Axiom a native foundation for:

```text
compression
archives
packages
application bundles
resource packaging
large-file streaming
content addressing
deduplication
Merkle integrity
package signing
package encryption
VFS mounting
offline deployment
incremental updates
rollback
package caching
compiler artifact caching
AI-readable package metadata
```

while preserving the core Axiom requirements:

```text
native
fast
small
deterministic
cross-platform
no mandatory third-party runtime
no mandatory GC
struct-only APIs
capability-controlled
compiler/linker integrated
```

**Next architecture task:**

**BOOTSTRAP-614 — Native Device, Hardware, Peripheral, Sensor, GPU/Accelerator & OS Resource I/O Runtime 5.0**

Scope will connect Axiom's native runtime to actual hardware and operating-system devices while preserving the existing capability, resource-governor, scheduler, synchronization, networking, storage, cryptography and package architecture.

:::