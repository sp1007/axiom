Tiếp tục với task kế tiếp: **BOOTSTRAP-613 — Native Compression, Archive, Package, Content-Addressed Storage & Resource Packaging Runtime 5.0**.

:::writing{variant="document" id="58317" title="BOOTSTRAP-613 — Native Compression, Archive, Package, Content-Addressed Storage & Resource Packaging Runtime 5.0"}
# BOOTSTRAP-613
## Native Compression, Archive, Package, Content-Addressed Storage & Resource Packaging Runtime 5.0

**Status:** Architecture Specification  
**Layer:** Native Runtime / Storage / Packaging  
**Depends on:** BOOTSTRAP-600 → 612  
**Primary dependencies:** 603 Security, 606 Resource Governor, 607 Scheduler, 608 Synchronization, 610 Cryptography, 611 Storage/VFS, 612 Serialization  
**Target:** Windows / Linux / macOS / Android / iOS / WASM / Embedded

---

# 1. Purpose

BOOTSTRAP-613 defines Axiom's native infrastructure for:

- compression;
- decompression;
- archive handling;
- native Axiom packages;
- executable/resource bundles;
- immutable resource objects;
- content-addressed storage;
- chunking and deduplication;
- Merkle trees;
- package manifests;
- package verification;
- package signing;
- optional package encryption;
- package mounting through VFS;
- deterministic package generation;
- reproducible package identity;
- offline deployment;
- package caching;
- resource indexing;
- lazy resource loading;
- large-file/model/asset packaging;
- atomic package installation and activation;
- package generations and rollback;
- package patch/delta infrastructure.

The subsystem must remain independent from any particular package manager.

---

# 2. Core Design Principle

Axiom separates four concepts:

```text
Compression
    ↓
Archive
    ↓
Package
    ↓
Content-Addressed Object Store
```

They are related but must not be conflated.

A compressed byte stream is not an archive.

An archive is not necessarily a package.

A package is not necessarily an object store.

An object store is not a package manager.

---

# 3. Non-Goals

BOOTSTRAP-613 does not define:

- public package registries;
- package marketplace;
- dependency marketplace;
- centralized repository infrastructure;
- source-code dependency resolution;
- build-system semantics;
- language-level module semantics;
- arbitrary package-install scripts;
- automatic execution of package contents;
- automatic code execution during package inspection;
- a mandatory third-party compression library;
- a mandatory third-party package manager;
- garbage collection of language memory.

Storage-object reclamation is distinct from language memory management.

---

# 4. Architectural Layers

```text
┌─────────────────────────────────────────────┐
│ Application / Compiler / Linker             │
├─────────────────────────────────────────────┤
│ Resource API / Package API                   │
├─────────────────────────────────────────────┤
│ Package Mount / Overlay VFS                  │
├─────────────────────────────────────────────┤
│ AXPK Package Format                          │
├─────────────────────────────────────────────┤
│ Archive Layer                                │
├─────────────────────────────────────────────┤
│ Compression Layer                            │
├─────────────────────────────────────────────┤
│ Content-Addressed Object Store               │
├─────────────────────────────────────────────┤
│ Storage / VFS 611                            │
├─────────────────────────────────────────────┤
│ Crypto / Security / Resources               │
└─────────────────────────────────────────────┘
```

---

# 5. Terminology

## 5.1 Blob

An immutable byte sequence.

## 5.2 Chunk

A bounded portion of a blob.

## 5.3 Object

A content-addressed immutable storage unit.

## 5.4 Entry

A named item inside an archive or package.

## 5.5 Package

A versioned, structured, verifiable collection of entries.

## 5.6 Resource

A package entry exposed to an application.

## 5.7 Manifest

Machine-readable package metadata.

## 5.8 Package generation

One immutable installed version of a package.

## 5.9 Activation

The atomic operation that makes one package generation current.

---

# 6. Fundamental Invariants

1. Package paths are normalized.
2. Package paths cannot escape the package root.
3. Package opening never executes package code.
4. Package inspection never requires executing package contents.
5. Package contents are immutable after finalization.
6. Package identity is deterministic.
7. Package signatures cover canonical package identity.
8. Content-addressed objects are immutable.
9. Object IDs derive from cryptographic content identity.
10. Corrupted objects are detected before use.
11. Installation is atomic.
12. Activation is atomic.
13. Failed installation cannot partially activate a package.
14. Untrusted packages cannot acquire capabilities automatically.
15. Package metadata cannot silently grant OS privileges.
16. Compression cannot bypass security validation.
17. Decompression is resource-bounded.
18. Archive extraction is sandboxed.
19. No mandatory garbage collector exists.
20. No mandatory package registry exists.

---

# 7. Compression Abstraction

The compiler/runtime exposes:

```text
CompressionCodec
CompressionEncoder
CompressionDecoder
CompressionOptions
CompressionStats
```

Example:

```text
codec = CompressionCodec.zstd
encoder = codec.encoder(options)
encoder.write(data)
encoder.finish()
```

Decoding:

```text
decoder = codec.decoder(options)

while decoder.has_data():
    data = decoder.read()
```

---

# 8. Codec Model

The logical codec identifiers are:

```text
store
deflate
zstd
lz4
brotli
axiom-native
```

`store` means no compression.

Axiom must not make all codecs mandatory.

The minimal runtime profile may contain only:

```text
store
axiom-native
```

Platform/full profiles may add others.

---

# 9. Native Compression Codec

Axiom may define an internally implemented codec optimized for:

- package resources;
- deterministic output;
- streaming;
- low memory;
- fast decompression;
- random-access chunks.

The codec must have:

```text
encode()
decode()
stream_encode()
stream_decode()
```

and an explicit format version.

---

# 10. Third-Party Codec Boundary

External codecs may be provided through:

```text
CompressionProvider
```

but:

```text
Axiom core != third-party codec dependency
```

An external provider must not become a mandatory dependency of the compiler or minimal runtime.

---

# 11. Compression Levels

Logical levels:

```text
Fastest
Fast
Balanced
Dense
Maximum
```

A codec maps these to implementation-specific parameters.

The package metadata stores the actual codec and format version, not merely the logical level.

---

# 12. Deterministic Compression

Deterministic mode must guarantee identical output when:

- input is identical;
- codec version is identical;
- options are identical;
- architecture-independent mode is selected.

Non-deterministic metadata such as:

- timestamps;
- process IDs;
- random seeds;
- host paths

must not affect deterministic package output.

---

# 13. Streaming Compression

The encoder operates incrementally:

```text
Input → Encoder → Output
```

without requiring the entire input in memory.

Requirements:

- bounded buffers;
- backpressure;
- cancellation;
- async support;
- partial write handling;
- error propagation.

---

# 14. Streaming Decompression

Decoder requirements:

- bounded output;
- maximum expansion ratio;
- maximum output size;
- cancellation;
- truncated-input detection;
- checksum validation.

A decompressor must reject malicious expansion exceeding configured limits.

---

# 15. Compression Statistics

Optional statistics:

```text
input_bytes
output_bytes
compression_ratio
codec
level
elapsed_time
```

Statistics are diagnostic only and must not alter package identity.

---

# 16. Checksums

Package components may contain:

```text
CRC32C
SHA-256
SHA-512
BLAKE3
```

depending on profile.

Cryptographic package identity should use the algorithm selected by the package format.

The hash abstraction is supplied by BOOTSTRAP-610.

---

# 17. Archive Abstraction

Axiom defines:

```text
ArchiveReader
ArchiveWriter
ArchiveEntry
ArchiveEntryMetadata
```

Reader:

```text
open()
entry_count()
find(path)
read(entry)
stream(entry)
```

Writer:

```text
create()
add()
add_stream()
finish()
```

---

# 18. Archive Entry

Each entry contains:

```text
path
type
size
stored_size
compression
checksum
offset
flags
attributes
```

Optional:

```text
content_type
language
variant
target
permissions
```

---

# 19. Archive Types

Logical archive types:

```text
AXPK
ZIP
TAR
```

ZIP and TAR are compatibility formats.

AXPK is the native format.

---

# 20. ZIP Compatibility

Axiom may read/write conventional ZIP where required.

Compatibility must not change the semantics of the native AXPK format.

ZIP-specific limitations must be represented explicitly.

---

# 21. TAR Compatibility

TAR support is useful for:

- Unix interoperability;
- source bundles;
- container-like distribution;
- archival exports.

TAR does not provide all AXPK security or indexing guarantees.

---

# 22. Native Package Format

The native package format is named:

```text
AXPK
```

Logical layout:

```text
┌─────────────────────┐
│ Header              │
├─────────────────────┤
│ Manifest            │
├─────────────────────┤
│ Entry Index         │
├─────────────────────┤
│ Chunk/Object Index  │
├─────────────────────┤
│ Data                │
├─────────────────────┤
│ Merkle Metadata     │
├─────────────────────┤
│ Signature Block     │
└─────────────────────┘
```

---

# 23. AXPK Header

Required fields:

```text
magic
format_version
header_size
flags
package_id
package_version
target
architecture
manifest_offset
manifest_size
index_offset
index_size
data_offset
data_size
root_hash
signature_offset
signature_size
```

---

# 24. Package Identity

A package has:

```text
PackageId
PackageVersion
PackageBuildId
PackageRootHash
```

The immutable identity is:

```text
PackageIdentity =
    Hash(canonical package content)
```

The human-readable package ID is metadata.

---

# 25. Package Version

Axiom uses explicit version components:

```text
major
minor
patch
revision
```

Additional pre-release/build metadata may exist.

Version ordering is deterministic.

---

# 26. Package Target

A package may declare:

```text
os
architecture
abi
cpu_features
gpu_features
runtime_profile
```

Examples:

```text
windows-x64
linux-x64
linux-arm64
macos-arm64
android-arm64
ios-arm64
wasm32
```

---

# 27. Manifest

The package manifest is canonical AXBIN/AXSCHEMA-compatible data.

Example:

```text
package {
    id: "com.example.app"
    version: 1.4.0

    targets {
        windows-x64
        linux-x64
    }

    resources {
        "/assets/main.bin"
        "/models/model.axmodel"
    }
}
```

The actual canonical representation must use field IDs rather than textual field order.

---

# 28. Manifest Requirements

Manifest fields include:

```text
package identity
version
build identity
targets
dependencies
resources
capabilities
signing information
compression policy
encryption policy
minimum runtime
maximum runtime
compatibility flags
```

---

# 29. Resource Entry

A resource entry contains:

```text
resource_id
logical_path
content_type
size
compressed_size
compression
hash
chunking
flags
```

---

# 30. Resource IDs

Resource IDs should be stable across package versions when the logical resource remains the same.

Example:

```text
resource_id = Hash(package_id || normalized_path)
```

Alternative explicitly assigned IDs are permitted.

---

# 31. Path Normalization

Package paths use:

```text
UTF-8
/
```

Rules:

- no drive letters;
- no absolute OS paths;
- no `..`;
- no NUL;
- no platform separator ambiguity;
- canonical Unicode normalization policy;
- reserved package metadata paths.

Example:

```text
assets/logo.png
models/text_encoder.bin
locales/vi-VN.axres
```

---

# 32. Path Traversal Prevention

The following are invalid:

```text
../file
a/../../file
C:\file
\\server\file
/absolute/file
```

Validation occurs before:

- indexing;
- extraction;
- mounting;
- installation.

---

# 33. Symlinks

Native AXPK does not require symlink entries.

If supported, symlinks must be:

- explicitly marked;
- sandboxed;
- unable to escape the package root;
- disabled by default for untrusted packages.

---

# 34. Package Permissions

A package manifest may declare required capabilities:

```text
filesystem.read
network.connect
gpu.compute
camera.read
microphone.read
```

These are requests, not grants.

Actual authority comes from BOOTSTRAP-603.

---

# 35. Capability Principle

Package installation must never imply:

```text
package capability declaration
→ OS permission
```

Instead:

```text
package requirement
→ deployment policy
→ application capability
→ runtime operation
```

---

# 36. Package Signing

AXPK supports signatures based on BOOTSTRAP-610.

Signature covers:

```text
format version
manifest
entry index
content root
package identity
```

Mutable transport metadata must not be included.

---

# 37. Publisher Identity

A signature contains:

```text
publisher_id
key_id
algorithm
signature
certificate/reference metadata
```

Private keys are never stored in the package.

---

# 38. Verification

Verification sequence:

```text
parse
 ↓
validate bounds
 ↓
validate paths
 ↓
validate manifest
 ↓
compute content root
 ↓
verify signature
 ↓
verify policy
 ↓
accept package
```

No executable package content is loaded during verification.

---

# 39. Trust Policies

Policies may include:

```text
TrustedPublisher
TrustedKey
TrustedCertificate
UnsignedAllowed
SignatureRequired
PinnedPublisher
PinnedKey
```

Policy is controlled by BOOTSTRAP-603/610.

---

# 40. Encrypted Package Contents

AXPK may encrypt:

- complete data region;
- selected resources;
- selected chunks.

Encryption must use authenticated encryption.

Example:

```text
resource ciphertext
→ AEAD
→ authentication tag
```

---

# 41. Encryption Metadata

Metadata includes:

```text
algorithm
key_id
nonce/nonce derivation identifier
key version
encrypted range
```

Secrets are never stored directly in package metadata.

---

# 42. Selective Encryption

A package can leave public resources unencrypted while encrypting:

```text
models/*
private/*
license/*
```

This enables:

- fast package inspection;
- public metadata;
- protected large assets.

---

# 43. Compression + Encryption Ordering

Correct order:

```text
plaintext
 ↓
compress
 ↓
encrypt
```

Not:

```text
plaintext
 ↓
encrypt
 ↓
compress
```

because encrypted data generally compresses poorly.

---

# 44. Chunking

Large resources may be divided into chunks.

Each chunk contains:

```text
chunk_id
logical_offset
logical_size
stored_size
compression
encryption
hash
```

---

# 45. Chunk Size

Profiles may use:

```text
64 KiB
256 KiB
1 MiB
4 MiB
8 MiB
```

Adaptive chunking is permitted.

The package manifest records the actual chunking scheme.

---

# 46. Random Access

Chunking enables:

```text
read(resource, offset, size)
```

without decompressing the entire resource.

Example:

```text
model.bin
 ├─ chunk 0
 ├─ chunk 1
 ├─ chunk 2
 └─ ...
```

Only required chunks are loaded.

---

# 47. Memory Mapping

Uncompressed, aligned resources may be memory-mapped directly.

Requirements:

- immutable mapping;
- capability authorization;
- lifetime-bound package mount;
- package generation remains active while mapping exists.

Compressed resources cannot be directly memory-mapped as their logical representation.

---

# 48. Resource Streaming

API:

```text
Resource.open_stream()
Resource.read(offset, length)
Resource.map()
Resource.load()
```

Large resources should default to streaming.

---

# 49. Lazy Loading

A resource should not be loaded merely because its package was mounted.

Loading occurs on:

```text
open()
read()
map()
load()
```

This is important for:

- models;
- textures;
- audio;
- video;
- large language-model data;
- scientific datasets.

---

# 50. Resource Cache

The runtime provides:

```text
ResourceCache
```

with:

```text
memory cache
compressed chunk cache
decoded cache
disk cache
```

Caches are optional.

---

# 51. Cache Identity

Cache keys are content-based:

```text
ObjectId
ChunkId
PackageRootHash
```

not only:

```text
filename
```

This prevents stale-resource ambiguity.

---

# 52. Content-Addressed Storage

Axiom defines:

```text
ObjectStore
ObjectId
ObjectReader
ObjectWriter
ObjectLease
```

An object is immutable.

Example:

```text
ObjectId = SHA-256(content)
```

---

# 53. Object Store Layout

Logical layout:

```text
objects/
    ab/
       cdef...
```

The physical layout is backend-dependent.

---

# 54. Object Immutability

After:

```text
put(object)
```

the object cannot be modified.

Replacing content creates another object ID.

This provides strong cache correctness.

---

# 55. Deduplication

If two resources contain identical content:

```text
resource A → object X
resource B → object X
```

Only one physical object is required.

---

# 56. Chunk-Level Deduplication

Large files can deduplicate at chunk level:

```text
file A:
A B C D

file B:
A B X D
```

Only `X` is new.

---

# 57. Merkle Tree

A package may use:

```text
leaf = Hash(chunk)
parent = Hash(left || right)
root = Hash(tree)
```

The root becomes the package content identity.

---

# 58. Merkle Proof

A resource can be verified using:

```text
chunk
sibling hashes
root hash
```

without reading the entire package.

This is useful for:

- remote downloads;
- partial synchronization;
- large model distribution;
- cache validation.

---

# 59. Object References

Package index entries may reference:

```text
ObjectId
```

instead of physical offsets.

This permits:

- deduplication;
- package reconstruction;
- local cache reuse;
- remote object retrieval.

---

# 60. Object Store Modes

```text
Embedded
Local
Shared
Remote-backed
ReadOnly
Ephemeral
```

Only local embedded storage is required by the core runtime.

---

# 61. Storage Garbage Collection

Object-store reclamation is not language garbage collection.

Logical process:

```text
roots
 ↓
reachable objects
 ↓
unreachable objects
 ↓
reclaim
```

---

# 62. Object Store Roots

Roots include:

```text
active packages
installed generations
pinned packages
explicit leases
cache pins
checkpoint references
deployment references
```

---

# 63. Leases

An object may be temporarily protected by:

```text
ObjectLease
```

A lease prevents reclamation while a consumer is using the object.

---

# 64. Pinning

Long-lived applications may pin objects:

```text
store.pin(object_id)
```

Pins must be bounded and observable.

---

# 65. Reclamation Algorithms

Allowed implementations:

```text
reference counting
mark/sweep
generation-based reclamation
lease-based reclamation
hybrid
```

The public API must not expose the implementation.

---

# 66. Package Cache

The package cache contains:

```text
package metadata
manifest
signature verification result
object references
decoded indexes
compressed chunks
```

---

# 67. Cache Namespaces

Separate namespaces:

```text
system
user
application
build
temporary
deployment
```

Security boundaries must prevent cross-application unauthorized reuse.

---

# 68. Offline Deployment

A package may be installed from:

```text
local file
USB/storage
network download
IPC transfer
embedded resource
object store
```

No network access is required during installation if all objects are local.

---

# 69. Dependency Metadata

AXPK can declare:

```text
dependency {
    id
    version_constraint
    target
    optional
    feature
}
```

BOOTSTRAP-613 does not define full dependency resolution.

---

# 70. Dependency Resolution Boundary

Resolution belongs to a higher-level package/deployment system.

The runtime only needs:

```text
resolved dependency set
```

at activation time.

---

# 71. Resource Variants

One logical resource may contain variants:

```text
texture.png
 ├─ desktop
 ├─ mobile
 ├─ retina
 └─ low-memory
```

Selection can depend on:

```text
platform
architecture
locale
screen density
GPU capabilities
feature set
```

---

# 72. Localization

Resources may declare:

```text
locale = vi-VN
locale = en-US
```

Fallback:

```text
vi-VN
→ vi
→ default
```

The exact fallback chain is explicit and deterministic.

---

# 73. Target-Specific Resources

Example:

```text
bin/windows-x64/app.exe
bin/linux-x64/app
bin/macos-arm64/app
```

Only the active target's resources need to be activated.

---

# 74. Executable Bundles

An application package may contain:

```text
application executable
dynamic libraries
configuration
resources
debug symbols
licenses
metadata
```

The package runtime itself does not automatically execute the executable.

---

# 75. Native Executable Loading Boundary

Executable loading belongs to:

```text
Process/Supervisor
OS loader
Security capability layer
```

Package runtime provides the bytes and metadata.

---

# 76. Dynamic Libraries

Libraries can be package entries:

```text
.dll
.so
.dylib
```

Loading requires explicit security policy.

A package cannot silently replace a system library.

---

# 77. Platform Bundle Mapping

## Windows

Possible deployment:

```text
app.axpkg
 → app.exe
 → *.dll
 → resources
```

## Linux

Possible:

```text
app.axpkg
 → ELF
 → .so
 → resources
```

## macOS

Possible:

```text
App.app/
    Contents/
        MacOS/
        Frameworks/
        Resources/
```

AXPK may serve as the build/deployment source.

---

# 78. iOS

AXPK is a build/deployment abstraction.

The final platform bundle must obey Apple platform signing and bundle rules.

AXPK cannot bypass platform security.

---

# 79. Android

AXPK may be used internally for:

- application resources;
- native libraries;
- asset staging.

Final packaging must obey Android platform requirements.

---

# 80. WASM

A package may expose resources through:

```text
virtual filesystem
embedded byte ranges
host-provided resources
```

No assumption of native filesystem access is permitted.

---

# 81. Embedded Systems

AXPK can be compiled into:

```text
firmware image
read-only resource image
flash partition
ROM resource table
```

A minimal profile may remove:

- package installation;
- object reclamation;
- signatures;
- encryption;
- dynamic mounting.

---

# 82. Package Mounting

A package can be mounted as a read-only VFS:

```text
mount(package, "/app")
```

Example:

```text
/app/assets/logo.png
/app/models/model.bin
```

---

# 83. Mount Security

Mounting verifies:

- package integrity;
- path validity;
- package policy;
- capability requirements;
- signature policy.

---

# 84. Read-Only Package Filesystem

AXPK mounts are immutable.

Write operations return:

```text
ReadOnlyFilesystem
```

An overlay can provide writable state.

---

# 85. Overlay Filesystem

Logical structure:

```text
Writable Overlay
       ↑
AXPK Package
       ↑
Base Package
```

Read resolution searches upper layers first.

---

# 86. Atomic Activation

Installation:

```text
download
 ↓
verify
 ↓
stage
 ↓
validate
 ↓
commit
 ↓
activate
```

The active package pointer changes atomically.

---

# 87. Package Generations

Example:

```text
generation 41
generation 42
generation 43
```

Only one generation is active for a package identity unless explicitly configured otherwise.

---

# 88. Rollback

Rollback is:

```text
activate(previous_generation)
```

not:

```text
modify(active_package)
```

Old generations remain until reclamation policy permits deletion.

---

# 89. Interrupted Installation

If installation terminates unexpectedly:

```text
staged generation != active generation
```

Therefore the active version remains unchanged.

---

# 90. Secure Temporary Installation

Temporary package files use BOOTSTRAP-611 secure temporary-file mechanisms.

Rules:

- unpredictable temporary identity;
- exclusive creation;
- restrictive permissions;
- no unsafe shared directory;
- cleanup after completion.

---

# 91. Package Uninstall

Uninstall means:

```text
remove active reference
remove package metadata
remove unused object references
```

It does not necessarily immediately delete shared content.

---

# 92. Shared Objects

If:

```text
Package A → Object X
Package B → Object X
```

uninstalling A must not delete X while B still references it.

---

# 93. Package Garbage Collection

Package reclamation must consider:

```text
active generations
dependencies
pins
leases
snapshots
object references
```

---

# 94. Delta Packages

A delta package may contain:

```text
added objects
removed references
changed manifest
new signature
```

It should avoid transmitting unchanged content.

---

# 95. Binary Delta Boundary

Binary delta algorithms are optional.

The preferred base mechanism is object/chunk reuse.

This provides a simple and robust delta model without requiring a complex binary-diff engine.

---

# 96. Delta Verification

A delta must verify:

```text
base package root
target package root
new object hashes
signature
```

before activation.

---

# 97. Reproducible Package Builds

The package builder must normalize:

- entry ordering;
- paths;
- timestamps;
- ownership;
- permissions;
- compression settings;
- manifest serialization;
- padding;
- metadata ordering.

---

# 98. Canonical Entry Ordering

Default:

```text
lexicographic UTF-8 byte order
```

using canonical normalized paths.

---

# 99. Timestamp Policy

Reproducible mode uses:

```text
timestamp = SOURCE_DATE_EPOCH
```

or:

```text
timestamp = 0
```

if no build timestamp is supplied.

---

# 100. Host Independence

The following must not affect reproducible package identity:

```text
username
hostname
absolute build path
temporary directory
OS-specific local path
process ID
build machine ID
```

---

# 101. Package Root Hash

Conceptually:

```text
PackageRootHash =
    Hash(
        canonical manifest ||
        canonical entry index ||
        Merkle root
    )
```

The exact format is versioned.

---

# 102. Package Fingerprint

Human-readable fingerprint:

```text
axpk:<algorithm>:<hex>
```

Example:

```text
axpk:sha256:...
```

---

# 103. AI-Readable Metadata

Every package should optionally contain:

```text
package.axmeta
```

containing:

```text
package ID
version
targets
resources
schemas
dependencies
capabilities
ABI
exports
entrypoints
build identity
source mapping
```

---

# 104. Machine-Readable Package Inspection

Compiler/toolchain command:

```text
axiom package inspect app.axpkg
```

Output formats:

```text
text
json
axmeta
```

---

# 105. Verification CLI

Example:

```text
axiom package verify app.axpkg
```

Checks:

```text
format
bounds
paths
hashes
Merkle tree
signature
certificate
policy
```

---

# 106. Package Listing

```text
axiom package list app.axpkg
```

must not execute any package code.

---

# 107. Package Extraction

```text
axiom package extract app.axpkg out/
```

must enforce:

- path sandbox;
- quota;
- maximum expansion;
- symlink policy;
- overwrite policy.

---

# 108. Resource Compiler

The Axiom resource compiler converts:

```text
images
audio
models
fonts
text
binary files
schemas
shaders
```

into package entries.

---

# 109. Embedded Resource Syntax

Possible compiler syntax:

```text
resource logo from "assets/logo.png"
resource model from "models/model.bin"
```

The compiler generates typed resource metadata.

---

# 110. Typed Resources

Generated API:

```text
Resources.logo
Resources.model
```

with compile-time validation of resource existence.

---

# 111. Resource Lookup

Dynamic lookup:

```text
resources.find("/assets/logo.png")
```

Static lookup:

```text
Resources.logo
```

Static lookup should avoid runtime string hashing where possible.

---

# 112. Resource Handles

A resource handle contains:

```text
package_generation
resource_id
rights
```

It must not expose raw filesystem offsets.

---

# 113. Resource Rights

Possible rights:

```text
Read
Stream
Map
Metadata
```

Mapping is separate because it has stronger lifetime/resource implications.

---

# 114. Resource Lifetime

A resource handle keeps its package generation alive as required.

Unmounting a package with active mapped resources must either:

- defer unmount;
- invalidate explicitly;
- reject unmount.

Silent use-after-unmount is forbidden.

---

# 115. Scheduler Integration

Large decompression and package verification may execute asynchronously:

```text
await package.verify_async()
await resource.load_async()
```

CPU-intensive decompression should use the CPU executor.

I/O waits should use the I/O reactor.

---

# 116. Synchronization

Concurrent readers are allowed.

Package metadata is immutable after publication.

Mutable cache structures use BOOTSTRAP-608 primitives.

---

# 117. Resource Governor Integration

Every package operation can consume:

```text
storage bytes
memory
CPU
I/O bandwidth
I/O operations
open handles
mapped bytes
cache capacity
```

Limits come from BOOTSTRAP-606.

---

# 118. Security Integration

Package operations require appropriate capabilities:

```text
package.read
package.mount
package.install
package.activate
package.extract
package.cache.write
```

High-privilege operations must never be implicitly available.

---

# 119. Storage Integration

Physical persistence uses BOOTSTRAP-611:

```text
ObjectStore
PackageStore
PackageGenerationStore
CacheStore
```

No second independent filesystem abstraction is introduced.

---

# 120. Serialization Integration

Manifest and schema metadata use BOOTSTRAP-612.

AXBIN provides:

- canonical encoding;
- schema evolution;
- bounded decoding.

---

# 121. Cryptography Integration

Hashing, signatures, encryption and key management use BOOTSTRAP-610.

613 must not invent an incompatible crypto subsystem.

---

# 122. Diagnostics Integration

Package events produce structured diagnostics:

```text
PackageOpened
PackageVerified
PackageMounted
ResourceLoaded
ChunkDecoded
CacheHit
CacheMiss
PackageInstalled
PackageActivated
PackageRollback
ObjectReclaimed
```

---

# 123. Security Diagnostics

Security events include:

```text
SignatureFailure
HashMismatch
PathTraversalRejected
CapabilityDenied
DecompressionLimitExceeded
InvalidManifest
InvalidPackageFormat
```

No secret material is logged.

---

# 124. Configuration Integration

BOOTSTRAP-601 controls:

```text
cache size
compression policy
verification policy
trusted publishers
temporary directories
package roots
object-store quota
```

Configuration is snapshot-based.

---

# 125. Application State Integration

BOOTSTRAP-600 may reference package identities:

```text
active_package_root
package_generation
resource_schema_version
```

State recovery must validate that referenced package generations still exist.

---

# 126. Supervision Integration

BOOTSTRAP-605 may define package deployment as a prerequisite to service activation:

```text
install
→ verify
→ activate
→ start service
```

If activation fails, the service must not start using a partially installed generation.

---

# 127. Compiler Integration

Compiler metadata can declare:

```text
@resource(...)
@package(...)
@requires_package(...)
```

The compiler resolves static resource references.

---

# 128. Linker Integration

The linker can:

- embed resources;
- remove unused resources;
- construct package sections;
- emit package metadata;
- calculate package hashes;
- generate resource symbol tables.

---

# 129. Dead Resource Elimination

If a resource is marked:

```text
@resource(private)
```

and has no references, the compiler may eliminate it.

Explicit:

```text
@keep_resource
```

prevents elimination.

---

# 130. Executable Embedding

Minimal executables may embed AXPK directly:

```text
ELF
 └── AXPK section

PE
 └── AXPK resource/section

Mach-O
 └── AXPK section
```

The runtime can expose the embedded package through VFS.

---

# 131. Self-Contained Executable

Axiom can produce:

```text
single executable
```

containing:

```text
code
runtime
resources
package metadata
```

without requiring an external asset directory.

---

# 132. Split Deployment

For large applications:

```text
app.exe
app.axpkg
models.axpkg
language-vi.axpkg
```

This permits independent resource updates.

---

# 133. Model Packaging

Large AI models may be represented as:

```text
model manifest
weights
tokenizer
configuration
metadata
```

Weights use chunked object storage.

Only required ranges need to be loaded.

---

# 134. Model Deduplication

Different models may share:

```text
embedding tensors
tokenizers
common layers
quantization tables
```

when their content is identical.

Content addressing makes sharing automatic.

---

# 135. Large Binary Packaging

For files larger than memory:

```text
open_stream()
read_range()
map_chunk()
prefetch()
```

must operate without loading the whole file.

---

# 136. Prefetch

Optional:

```text
resource.prefetch(offset, length)
```

Prefetch is advisory.

It must not violate resource budgets.

---

# 137. Read-Ahead

The package runtime may detect sequential access and perform bounded read-ahead.

Applications can disable it.

---

# 138. Compression Cache

Decoded chunks can be cached:

```text
ChunkId → decoded bytes
```

Cache entries are immutable.

---

# 139. Cache Eviction

Possible policy:

```text
LRU
LFU
ARC
size-aware
generation-aware
```

Policy is implementation-specific.

Eviction must never delete authoritative package objects.

---

# 140. Package Object Store vs Cache

Important distinction:

```text
ObjectStore = authoritative immutable content
Cache       = disposable optimization
```

Cache loss must not corrupt package correctness.

---

# 141. Corruption Recovery

If an object hash mismatches:

```text
mark invalid
invalidate cache entry
attempt alternate source if configured
report diagnostic
```

Never silently use corrupted content.

---

# 142. Missing Object

If a referenced object is missing:

```text
PackageIncomplete
```

The package must not be activated unless policy explicitly permits lazy external resolution.

---

# 143. Lazy External Objects

Optional remote-backed packages can resolve missing objects on demand.

This requires explicit capability:

```text
network.connect
```

and resource policy.

---

# 144. No Hidden Network Access

Opening a package must not automatically perform network requests unless the package was explicitly configured for remote-backed resolution.

---

# 145. Package Install State Machine

```text
Discovered
   ↓
Staging
   ↓
ObjectsReady
   ↓
ManifestValidated
   ↓
IntegrityVerified
   ↓
SignatureVerified
   ↓
Committed
   ↓
Activated
```

Failure transitions to:

```text
Failed
```

without activating the incomplete generation.

---

# 146. Package Activation State

```text
Inactive
Staged
Committed
Active
Retired
Reclaimable
```

Only:

```text
Committed → Active
```

is allowed.

---

# 147. Package Manager Boundary

A higher-level package manager may implement:

- registry lookup;
- dependency solving;
- update policies;
- channels;
- release management.

613 supplies primitives only.

---

# 148. Package Format Compatibility

AXPK format version follows:

```text
major.minor
```

Major versions may be incompatible.

Minor versions must preserve forward-readable metadata where possible.

Unknown optional fields must be skippable.

---

# 149. Unknown Entry Flags

Readers must reject unknown mandatory flags.

Readers may ignore unknown optional flags.

This prevents silent semantic corruption.

---

# 150. Forward Compatibility

A newer writer may generate metadata that an older reader does not understand.

Older readers must fail explicitly when a required feature is unavailable.

They must not reinterpret it incorrectly.

---

# 151. Backward Compatibility

New readers must support previous compatible AXPK versions according to the format compatibility table.

---

# 152. Package Format Self-Description

Each AXPK contains:

```text
format_version
feature_flags
required_features
```

---

# 153. Package Feature Bits

Examples:

```text
Compressed
Encrypted
Signed
Chunked
Merkle
ObjectReferenced
Delta
Executable
Embedded
```

---

# 154. Security Against Resource Exhaustion

Package parser limits:

```text
max_manifest_size
max_entries
max_path_length
max_chunk_count
max_nesting
max_decompressed_size
max_compression_ratio
max_signature_chain
max_dependency_count
```

---

# 155. Parser Safety

Parsing must use:

- checked arithmetic;
- bounded offsets;
- integer overflow detection;
- length validation;
- recursion limits;
- allocation limits.

---

# 156. No Trust in Metadata

Declared:

```text
size
hash
offset
compression ratio
```

is untrusted until independently validated.

---

# 157. Atomic File Publication

Package objects are published using BOOTSTRAP-611 atomic file operations.

Typical:

```text
temporary
→ fsync
→ rename
```

where supported.

---

# 158. Durable Activation

For durable deployment:

```text
write generation metadata
flush
publish generation
flush
update active pointer
flush
```

The exact durability sequence is backend-specific.

---

# 159. Crash Recovery

On startup:

```text
scan deployment metadata
validate active pointer
validate generation
discard incomplete staging
restore previous committed generation if required
```

---

# 160. Package Transaction

Logical API:

```text
tx = package_store.begin_install()

tx.stage(...)
tx.verify(...)
tx.commit()
```

`commit()` is atomic.

---

# 161. Package Transaction Failure

Failure before commit:

```text
no visible package generation
```

Failure after commit but before activation:

```text
new generation exists
old generation remains active
```

---

# 162. Resource Index

A package index should support:

```text
find_by_path
find_by_id
find_by_type
find_by_locale
find_by_target
find_by_hash
```

---

# 163. Index Performance

Expected:

```text
path lookup: O(log n) or O(1) average
ID lookup: O(1) average
hash lookup: O(1) average
```

Implementation may use:

- hash table;
- sorted table;
- minimal perfect hash;
- B-tree.

---

# 164. Memory-Mapped Index

Large package indexes may be memory-mapped.

The index must remain immutable.

---

# 165. Minimal Runtime Profile

A minimal Axiom executable may include only:

```text
AXPK reader
store codec
resource reader
VFS mount
hash verification
```

Optional features can be dead-stripped.

---

# 166. Full Runtime Profile

Full profile may include:

```text
compression
encryption
signatures
object store
package installation
cache
delta updates
resource compiler
```

---

# 167. Embedded Minimal Profile

Embedded targets may use:

```text
static AXPK
ROM resources
no installer
no object GC
no dynamic allocation
```

where platform constraints require it.

---

# 168. ABI

Public ABI types use stable opaque handles:

```text
PackageHandle
ResourceHandle
ObjectHandle
PackageGenerationHandle
```

Internal structures remain private.

---

# 169. Struct-Only API

Example:

```text
struct PackageReader {
    backend: PackageBackend
}

fn PackageReader.open(
    self: PackageReader,
    source: PackageSource
) -> Result<Package>
```

No class hierarchy is required.

---

# 170. Provider Override

Platform-specific implementations use traits/functions.

Example:

```text
trait PackageBackend {
    open(...)
    read(...)
    verify(...)
}
```

A platform backend can replace the default implementation through compile-time specialization.

---

# 171. No Virtual Dispatch Requirement

Static package formats should compile to direct calls whenever the backend is statically known.

Dynamic provider dispatch is optional.

---

# 172. Compiler IR

Representative operations:

```text
package.open
package.verify
package.mount
package.resource_lookup
package.resource_read
package.resource_map
package.chunk_decode
package.object_get
package.object_put
package.object_hash
```

---

# 173. IR Optimization

The compiler may:

- inline resource lookup;
- specialize static resources;
- eliminate unused package APIs;
- constant-fold resource IDs;
- embed small resources directly;
- remove unused compression codecs.

---

# 174. Static Resource Optimization

Small immutable resources may be compiled directly into read-only data:

```text
const_resource = &[u8]
```

No package parser is needed at runtime for that resource.

---

# 175. Large Resource Optimization

Large resources remain external or packaged as chunks.

The compiler should not duplicate them unnecessarily into executable memory.

---

# 176. Security Metadata

Compiler output may contain:

```text
required_capabilities
package_signature_requirement
resource_security_class
```

---

# 177. Diagnostics Metadata

Build artifacts may contain:

```text
package build ID
resource source mapping
resource compiler version
compression codec version
schema fingerprint
```

---

# 178. Reproducible Build Manifest

The builder emits:

```text
build.manifest.axmeta
```

containing:

```text
source inputs
tool versions
compiler version
resource hashes
package root
```

No machine-specific secret information is included.

---

# 179. Deterministic Resource Compilation

Resource compiler must normalize:

- image metadata where applicable;
- archive metadata;
- timestamps;
- path ordering;
- manifest ordering.

Source formats with inherently nondeterministic metadata must have normalization options.

---

# 180. Package Inspection Security

Inspection tools must treat packages as hostile input.

They must never:

- execute constructors;
- load native libraries;
- evaluate scripts;
- invoke package-defined code;
- follow external links.

---

# 181. Extraction Security

Extraction must protect against:

- path traversal;
- symlink escape;
- hard-link escape;
- device-node creation;
- permission escalation;
- decompression bombs;
- excessive file counts.

---

# 182. Device Nodes

Package extraction must reject device-node creation by default.

---

# 183. Hard Links

Hard-link entries are disabled by default.

If enabled, they must remain inside the extraction root and obey capability policy.

---

# 184. Package Metadata Privacy

Package metadata must not unintentionally leak:

- local usernames;
- source paths;
- machine names;
- secret environment variables;
- private keys.

---

# 185. License Metadata

Packages may contain:

```text
license
notice
copyright
attribution
```

These are metadata only and do not affect execution.

---

# 186. Package Dependencies and Security

Dependencies must be identified by:

```text
package ID
version constraint
content identity
publisher/trust identity
```

A version number alone is insufficient for cryptographic identity.

---

# 187. Content Identity vs Version

Two packages can have:

```text
same version
different root hash
```

This must be treated as different content.

---

# 188. Package Lock

Higher-level deployment tooling can create:

```text
axiom.lock
```

containing:

```text
package ID
version
root hash
publisher
```

The runtime does not require the lockfile.

---

# 189. Offline Lock Verification

Offline deployment can verify:

```text
package root == lock root
```

without network access.

---

# 190. Package Update

Update process:

```text
new package
 ↓
verify
 ↓
stage
 ↓
activate
 ↓
health check
```

Integration with BOOTSTRAP-605 may automatically roll back activation if higher-level deployment policy requires it.

---

# 191. Health Integration

The package layer itself reports:

```text
package_valid
package_integrity
package_signature
package_generation
```

Application health remains the responsibility of BOOTSTRAP-605.

---

# 192. Package Metrics

Recommended metrics:

```text
package_verify_count
package_verify_time
package_install_count
package_activation_count
package_failure_count
cache_hit_rate
cache_miss_rate
decompression_bytes
decompression_time
object_dedup_ratio
storage_reclaimed
```

---

# 193. Tracing

Operations can create spans:

```text
package.verify
package.mount
resource.open
resource.read
chunk.decode
object.get
object.put
package.activate
```

---

# 194. Performance Targets

Target properties:

```text
metadata lookup: near O(1)
sequential read: near underlying storage throughput
uncompressed mapping: zero-copy
chunk verification: streaming
small-resource lookup: low allocation
package mount: proportional to index size
```

---

# 195. Memory Targets

Opening a large package must not require loading all resource data.

Memory usage should be approximately:

```text
O(index_size + active_cache + active_streams)
```

rather than:

```text
O(total_package_size)
```

---

# 196. CPU Targets

Package mount must not decompress every resource.

Verification can operate incrementally.

Unused codecs must be removable from the binary.

---

# 197. Async Targets

Large package operations must support:

```text
async verify
async install
async resource read
async object read
async decompression
```

---

# 198. Cancellation

All potentially long-running operations support cancellation.

Cancellation must leave the package store in a valid state.

---

# 199. Concurrency

Concurrent operations are safe for:

```text
read
verify
mount
resource access
object reads
```

Mutating operations are serialized at the package-generation commit boundary.

---

# 200. Locking Strategy

Hot read paths should avoid global locks.

Preferred:

```text
immutable indexes
atomic references
per-cache-shard locks
lock-free queues where beneficial
```

---

# 201. Fault Injection

Test modes must simulate:

```text
corrupt header
corrupt manifest
corrupt index
corrupt chunk
missing object
bad signature
wrong key
expired certificate
disk full
permission denied
partial write
crash during commit
crash during activation
cache corruption
decompression failure
```

---

# 202. Deterministic Test Backend

A test backend provides:

```text
virtual filesystem
virtual object store
deterministic clock
deterministic random source
failure injection
```

This enables reproducible package tests.

---

# 203. Fuzzing

Fuzz targets:

```text
AXPK parser
ZIP reader
TAR reader
manifest decoder
path normalizer
chunk index
Merkle verifier
signature metadata
compression decoder
delta metadata
```

---

# 204. Property Tests

Properties:

```text
decode(encode(x)) == x
hash(content) stable
canonical_manifest stable
package_root stable
extract(package) safe
dedup(content, content) == one_object
```

---

# 205. Crash Tests

Test:

```text
crash at every installation step
```

Expected invariant:

```text
active package is either old valid generation
or new fully committed generation
```

Never:

```text
partially activated generation
```

---

# 206. Corruption Tests

For every stored byte region:

```text
flip bit
```

Expected:

```text
verification failure
```

before corrupted content is accepted.

---

# 207. Security Tests

Must test:

- path traversal;
- symlink escape;
- malformed UTF-8;
- integer overflow;
- decompression bomb;
- signature forgery;
- unauthorized package activation;
- unauthorized extraction;
- capability escalation;
- malicious metadata.

---

# 208. Compatibility Tests

Test AXPK versions:

```text
current
previous supported
future-feature fixtures
```

Expected behavior must match compatibility rules.

---

# 209. Compression Benchmarks

Benchmark:

```text
text
JSON
binary
images
audio
model weights
already-compressed data
```

Measure:

```text
ratio
encode throughput
decode throughput
memory
CPU
```

---

# 210. Deduplication Benchmarks

Measure:

```text
raw storage
chunked storage
object dedup storage
```

for realistic package sets.

---

# 211. Large-Model Benchmark

At least one benchmark should use multi-gigabyte data to verify:

- streaming;
- chunked reads;
- bounded memory;
- random access;
- cache behavior.

---

# 212. Package Builder Architecture

```text
Input Files
    ↓
Normalizer
    ↓
Resource Compiler
    ↓
Chunker
    ↓
Compressor
    ↓
Encryptor
    ↓
Object Store
    ↓
Manifest Builder
    ↓
Merkle Builder
    ↓
Signer
    ↓
AXPK Writer
```

---

# 213. Package Reader Architecture

```text
AXPK
 ↓
Parser
 ↓
Bounds Validation
 ↓
Manifest
 ↓
Index
 ↓
Signature Verification
 ↓
Object/Chunk Resolver
 ↓
Decryptor
 ↓
Decompressor
 ↓
Resource API
 ↓
VFS
```

---

# 214. Installation Architecture

```text
Source
 ↓
Staging Store
 ↓
Validation
 ↓
Object Import
 ↓
Package Commit
 ↓
Generation Record
 ↓
Atomic Activation
 ↓
Supervisor
```

---

# 215. Object Store Architecture

```text
             ┌──────────────┐
             │ Object Roots │
             └──────┬───────┘
                    ↓
             ┌──────────────┐
             │ Reachability │
             └──────┬───────┘
                    ↓
             ┌──────────────┐
             │ Object Store │
             └──────┬───────┘
                    ↓
             ┌──────────────┐
             │ Reclamation  │
             └──────────────┘
```

---

# 216. Full System Architecture

```text
                         ┌──────────────────────┐
                         │ Compiler / Linker    │
                         └──────────┬───────────┘
                                    │
                         ┌──────────▼───────────┐
                         │ Resource Compiler    │
                         └──────────┬───────────┘
                                    │
                 ┌──────────────────▼──────────────────┐
                 │             AXPK Builder             │
                 └──────────────┬──────────────────────┘
                                │
          ┌─────────────────────┼─────────────────────┐
          │                     │                     │
 ┌────────▼────────┐   ┌────────▼────────┐   ┌────────▼────────┐
 │ Compression     │   │ Encryption      │   │ Merkle/Hash     │
 │ 613             │   │ 610             │   │ 610             │
 └────────┬────────┘   └────────┬────────┘   └────────┬────────┘
          └─────────────────────┼─────────────────────┘
                                │
                       ┌────────▼─────────┐
                       │ Object Store     │
                       │ 613 + 611        │
                       └────────┬─────────┘
                                │
                       ┌────────▼─────────┐
                       │ AXPK Package     │
                       └────────┬─────────┘
                                │
                  ┌─────────────┼─────────────┐
                  │             │             │
          ┌───────▼──────┐ ┌────▼──────┐ ┌────▼─────────┐
          │ Package VFS  │ │ Resources │ │ Package API  │
          └───────┬──────┘ └────┬──────┘ └────┬─────────┘
                  │             │             │
                  └─────────────┼─────────────┘
                                │
                       ┌────────▼─────────┐
                       │ Application      │
                       └──────────────────┘
```

---

# 217. Cross-Subsystem Dependency Map

```text
600 State
 └── package generation references

601 Config
 └── package/cache/security policy

602 Diagnostics
 └── package events/traces/errors

603 Security
 └── package capabilities/trust

604 IPC
 └── package transfer/resource service

605 Supervision
 └── activation/service deployment

606 Resources
 └── package CPU/memory/I/O/storage budgets

607 Scheduler
 └── async package operations

608 Synchronization
 └── concurrent package/cache operations

609 Networking
 └── optional remote object retrieval

610 Crypto
 └── hashes/signatures/encryption

611 Storage
 └── physical package/object persistence

612 Serialization
 └── manifests/index/schema metadata

613 Package/Resource Layer
```

---

# 218. Required Public Types

Minimum:

```text
Package
PackageId
PackageVersion
PackageManifest
PackageEntry
PackageGeneration
PackageReader
PackageWriter

Resource
ResourceId
ResourceHandle
ResourceStream

CompressionCodec
CompressionEncoder
CompressionDecoder

ArchiveReader
ArchiveWriter

ObjectId
ObjectStore
ObjectReader
ObjectWriter
ObjectLease

MerkleTree
PackageVerifier
PackageInstaller
PackageActivation
```

---

# 219. Required Operations

Minimum:

```text
package.open()
package.inspect()
package.verify()
package.mount()
package.install()
package.activate()
package.rollback()

resource.find()
resource.read()
resource.stream()
resource.map()

object.get()
object.put()
object.exists()
object.verify()
object.pin()
object.lease()
object.reclaim()

compress()
decompress()
```

---

# 220. Error Model

Typed errors:

```text
InvalidPackage
UnsupportedFormat
CorruptPackage
InvalidPath
SignatureInvalid
TrustDenied
CapabilityDenied
MissingObject
HashMismatch
DecompressionFailed
DecompressionLimitExceeded
EncryptionFailed
KeyUnavailable
StorageFull
QuotaExceeded
PackageAlreadyExists
ActivationFailed
PackageIncomplete
VersionConflict
TargetMismatch
```

---

# 221. No Silent Recovery

If integrity validation fails, the runtime must not silently substitute arbitrary data.

Recovery must be explicit:

```text
alternate object source
cache repair
re-download
rollback
```

---

# 222. Package Trust Levels

Optional policy classifications:

```text
Untrusted
Verified
TrustedPublisher
SystemTrusted
EmbeddedTrusted
```

These are policy metadata, not intrinsic properties of the bytes.

---

# 223. Package Isolation

Package contents must not automatically share:

- capabilities;
- secrets;
- process authority;
- filesystem access;
- network authority.

Package code inherits authority only from its execution context.

---

# 224. Package-to-Package Isolation

Two packages may share immutable objects safely because object identity is content-based.

Mutable runtime state remains outside the package object store.

---

# 225. Package Metadata Versioning

Every schema has:

```text
schema_id
schema_version
schema_fingerprint
```

using BOOTSTRAP-612.

---

# 226. Package Metadata Evolution

New optional fields may be added.

Required fields must remain compatible according to schema rules.

Old readers must reject incompatible required semantics explicitly.

---

# 227. Package Resource ABI

Resources can expose typed schemas:

```text
Texture2D
AudioClip
Shader
Model
Font
LocalizationTable
BinaryBlob
```

These are metadata types, not necessarily language-level classes.

---

# 228. Shader Resources

GPU shader packages may contain:

```text
SPIR-V
DXIL
MSL
WGSL
```

depending on target.

Actual GPU execution belongs to a later hardware/GPU subsystem.

---

# 229. Resource Compilation Pipeline

Example:

```text
model.fbx
 ↓
asset compiler
 ↓
model.axmesh
 ↓
chunk/compress
 ↓
AXPK
```

The package layer does not need to understand every source format.

---

# 230. Package as Build Artifact

Compiler output can be:

```text
app.exe
app.axpkg
app.debug.axpkg
```

Debug symbols should be separately packaged when desired.

---

# 231. Debug Package

Debug package may contain:

```text
symbols
source maps
type metadata
resource source mappings
compiler diagnostics
```

It must not be shipped accidentally in release profiles.

---

# 232. Symbol Package Identity

Debug package can reference release binary by:

```text
BuildId
```

rather than filename alone.

---

# 233. Package Signing Profiles

Profiles:

```text
Development
Testing
Release
System
```

Each can define different signature requirements.

---

# 234. Development Mode

May permit:

```text
unsigned packages
local keys
debug metadata
```

only when explicitly enabled.

---

# 235. Release Mode

May require:

```text
signature
trusted publisher
verified dependencies
reproducible build metadata
```

---

# 236. No Install Scripts

AXPK does not support arbitrary:

```text
install.sh
postinstall.exe
package.js
```

inside the core format.

Installation is declarative.

This prevents package opening from becoming arbitrary code execution.

---

# 237. Declarative Hooks

If platform deployment requires actions, those actions are represented as typed manifest operations handled by trusted system code.

---

# 238. Package Resource Permissions

Resource declarations can specify:

```text
public
private
secret
executable
system
```

Security policy determines actual treatment.

---

# 239. Secret Resources

Secret resources must not be included as ordinary plaintext assets in release packages unless policy explicitly permits it.

Preferred mechanism:

```text
package → key reference
runtime → secure key provider
```

---

# 240. Secure Resource Deletion

Deletion of encrypted package objects follows storage guarantees from BOOTSTRAP-611.

The runtime must not falsely claim that flash/SSD data has been physically erased.

---

# 241. Package Compression Security

Compression codecs must enforce:

```text
output limit
memory limit
CPU budget
nested archive depth
```

Nested archives are not automatically recursively extracted.

---

# 242. Nested Packages

An AXPK may contain another AXPK as a resource.

It is treated as data until explicitly opened.

Opening the nested package creates a new trust boundary.

---

# 243. Package-in-Package Mount

Optional:

```text
mount(parent:/packages/a.axpkg, "/a")
```

Capability and resource limits apply independently.

---

# 244. Archive Compatibility Security

ZIP/TAR importers must normalize and validate paths before exposing entries.

Legacy archive semantics must not weaken AXPK security.

---

# 245. Package Cache Security

Cache entries are validated by content identity.

Cache poisoning cannot change content without changing its hash.

---

# 246. Publisher Cache

Signature verification results may be cached using:

```text
package_root_hash
publisher_key_id
policy_fingerprint
```

Changing policy invalidates the cached authorization result.

---

# 247. Trust Cache Invalidation

Changing:

```text
trust store
key revocation
security policy
```

must invalidate affected verification results.

---

# 248. Package Policy Fingerprint

Deployment records should include:

```text
package_policy_fingerprint
```

so that activation decisions remain auditable.

---

# 249. Object Store Compaction

If physical object storage uses packed files, compaction must:

- preserve object identity;
- use atomic replacement;
- tolerate interruption;
- preserve active objects.

---

# 250. Packed Object Store

Objects may be physically packed:

```text
pack-001
pack-002
pack-003
```

with an index:

```text
ObjectId → pack + offset + length
```

This reduces filesystem overhead.

---

# 251. Object Index

Object index can use:

```text
hash table
B-tree
sorted table
minimal perfect hash
```

depending on profile.

---

# 252. Object Store Integrity

Pack files contain:

```text
header
object records
checksum/footer
```

Corruption must be detectable.

---

# 253. Object Store Crash Recovery

A crash during pack creation must leave:

```text
old valid pack
```

or:

```text
new valid pack
```

never a silently accepted partial pack.

---

# 254. Object Store Snapshot

Snapshots may record:

```text
root set
package generations
object index version
```

and integrate with BOOTSTRAP-600.

---

# 255. Snapshot Semantics

Snapshotting the object store does not imply snapshotting arbitrary external filesystem state.

---

# 256. Resource Versioning

A resource can have:

```text
resource_id
version
content_hash
```

but content hash remains the authoritative immutable identity.

---

# 257. Package Aliases

Deployment systems may define:

```text
current
stable
testing
```

aliases.

The core package store treats aliases as mutable references to immutable generations.

---

# 258. Atomic Alias Update

Alias update must be atomic:

```text
stable → generation 42
```

No intermediate partially updated state is visible.

---

# 259. Package Channel Metadata

Channels are higher-level deployment metadata.

AXPK itself does not decide whether a package is “stable” or “beta”.

---

# 260. Remote Object Protocol Boundary

A later networking/deployment subsystem may define:

```text
GET object_id
GET package manifest
GET chunk
```

613 only defines the local object abstraction.

---

# 261. HTTP Integration

A package may be downloaded over BOOTSTRAP-609 HTTP.

Download pipeline:

```text
HTTP
 ↓
stream
 ↓
verify chunk
 ↓
store object
```

No need to hold the whole package in memory.

---

# 262. Resumable Download

Content-addressed chunks allow:

```text
download missing chunks only
```

after interruption.

---

# 263. Parallel Download

Independent chunks may be fetched concurrently.

BOOTPSTRAP-606 limits:

```text
CPU
network
memory
open connections
```

---

# 264. Package Prefetch

Deployment systems may prefetch packages without activation.

Prefetched packages remain:

```text
Committed but Inactive
```

until activation.

---

# 265. Rollback Storage Budget

The resource governor may enforce a maximum number of retained generations.

Example policy:

```text
keep_last = 3
```

The package layer only exposes the primitives.

---

# 266. Package Lifecycle

```text
Unknown
 ↓
Discovered
 ↓
Downloaded
 ↓
Verified
 ↓
Staged
 ↓
Committed
 ↓
Active
 ↓
Retired
 ↓
Reclaimable
 ↓
Reclaimed
```

---

# 267. Invariant: Immutable Content

Once:

```text
ObjectId = H(content)
```

the object represented by that ID must never change.

---

# 268. Invariant: Atomic Activation

At every observable point:

```text
active package = valid generation
```

---

# 269. Invariant: Verified Consumption

An application must never consume package content that violates configured integrity policy.

---

# 270. Invariant: Capability Separation

Package metadata can request capabilities but cannot grant them.

---

# 271. Invariant: Bounded Expansion

Decompression must respect resource limits.

---

# 272. Invariant: No Hidden Execution

Parsing, verification, extraction and mounting never execute package-provided code.

---

# 273. Invariant: Deterministic Identity

Given identical canonical inputs:

```text
package root hash
```

must be identical.

---

# 274. Invariant: Shared Content Safety

Removing one package cannot remove objects still referenced by another package.

---

# 275. Invariant: Cache Non-Authority

Deleting all caches cannot make a valid installed package invalid.

---

# 276. Invariant: Crash Safety

A process crash during install cannot expose a partial active package.

---

# 277. Invariant: Memory Bound

Package opening must not require memory proportional to total package content.

---

# 278. Invariant: Platform Independence

AXPK logical semantics must remain independent from:

```text
Windows path syntax
Linux permissions
macOS bundle structure
Android package structure
iOS bundle structure
```

---

# 279. Compiler Command Surface

Minimum:

```text
axiom package build
axiom package inspect
axiom package verify
axiom package list
axiom package extract
axiom package hash
axiom package sign
axiom package mount
axiom package install
axiom package activate
axiom package rollback
axiom package gc
```

---

# 280. Package Build Example

```text
axiom package build \
    --input app/ \
    --target windows-x64 \
    --output app.axpkg \
    --reproducible
```

---

# 281. Package Verification Example

```text
axiom package verify app.axpkg \
    --require-signature \
    --trusted-key release-key
```

---

# 282. Package Inspection Example

```text
axiom package inspect app.axpkg --format json
```

---

# 283. Package Hash Example

```text
axiom package hash app.axpkg
```

must produce the canonical package root identity.

---

# 284. Package GC Example

```text
axiom package gc \
    --keep-active \
    --keep-pinned
```

---

# 285. Test Matrix

Every implementation must test:

```text
Windows x64
Windows ARM64
Linux x64
Linux ARM64
macOS ARM64
Android ARM64
iOS ARM64
WASM
Embedded
```

where supported by the profile.

---

# 286. Compatibility Matrix

Test:

```text
AXPK v1 writer → v1 reader
AXPK v1 writer → newer reader
new optional feature → old reader
unsupported mandatory feature → explicit failure
```

---

# 287. Acceptance Criteria

1. AXPK has a versioned binary header.
2. AXPK has canonical metadata.
3. Package identity is content-based.
4. Package paths are normalized.
5. Traversal attacks are rejected.
6. Package inspection never executes code.
7. Package extraction is sandboxed.
8. Compression is streaming.
9. Decompression is resource-bounded.
10. Store codec exists.
11. At least one native codec can exist without third-party dependencies.
12. Codec selection is explicit.
13. Deterministic compression is supported.
14. Archive reader abstraction exists.
15. ZIP compatibility is isolated.
16. TAR compatibility is isolated.
17. AXPK supports manifests.
18. AXPK supports entry indexes.
19. AXPK supports checksums/hashes.
20. AXPK supports chunking.
21. AXPK supports random-access resource reads.
22. AXPK supports streaming resource reads.
23. AXPK supports optional memory mapping.
24. AXPK supports Merkle roots.
25. AXPK supports content-addressed objects.
26. Objects are immutable.
27. Identical objects deduplicate.
28. Object references are verifiable.
29. Object leases prevent premature reclamation.
30. Object reclamation is separate from language memory management.
31. Package signatures integrate with BOOTSTRAP-610.
32. Package verification integrates with BOOTSTRAP-603.
33. Package encryption uses authenticated cryptography.
34. Keys are never embedded as plaintext secrets.
35. Package requirements cannot grant capabilities.
36. Package installation is transactional.
37. Activation is atomic.
38. Interrupted installation preserves the old active package.
39. Rollback is generation-based.
40. Package caches are disposable.
41. Cache poisoning is prevented by content identity.
42. Large resources do not require full-memory loading.
43. Lazy resource loading works.
44. Chunk-level deduplication works.
45. Resource variants are supported.
46. Localization fallback is deterministic.
47. Target-specific resources are supported.
48. Embedded resources are supported.
49. Executable bundles are supported as a packaging layer.
50. Package loading does not bypass the OS loader/security model.
51. Native executable embedding is supported.
52. WASM resource mounting is supported.
53. Embedded read-only packages are supported.
54. Package metadata uses BOOTSTRAP-612.
55. Physical storage uses BOOTSTRAP-611.
56. CPU/I/O/memory budgets use BOOTSTRAP-606.
57. Async operations use BOOTSTRAP-607.
58. Concurrency uses BOOTSTRAP-608.
59. Remote retrieval can integrate with BOOTSTRAP-609.
60. Cryptographic operations use BOOTSTRAP-610.
61. Diagnostics integrate with BOOTSTRAP-602.
62. Application state can reference package generations.
63. Service supervision can depend on package activation.
64. Compiler can embed resources.
65. Linker can eliminate unused resources.
66. Static resource IDs can be generated at compile time.
67. Package generation metadata is deterministic.
68. Reproducible builds normalize timestamps and ordering.
69. Host-specific paths do not alter reproducible identity.
70. Package parser rejects integer overflow.
71. Package parser validates all offsets.
72. Package parser validates all lengths.
73. Compression bombs are bounded.
74. Signature failures are explicit.
75. Hash failures are explicit.
76. Missing objects are explicit.
77. Disk-full failures are recoverable.
78. Object-store compaction is crash-safe.
79. Object-store corruption is detectable.
80. Fuzz tests exist for all parsers.
81. Property tests verify encode/decode symmetry.
82. Crash tests cover installation boundaries.
83. Package GC preserves active objects.
84. Shared objects survive package removal while referenced.
85. Package metadata does not expose secrets.
86. Package operations produce diagnostics.
87. Package verification results can be policy-cached.
88. Policy changes invalidate affected trust decisions.
89. Minimal runtime profiles can remove unused features.
90. Full package functionality does not require a garbage collector.
91. Public APIs use stable opaque handles.
92. Struct-only implementation style is supported.
93. Static dispatch is possible.
94. Third-party codecs remain optional.
95. No package install script is required.
96. No package opening operation implicitly executes code.
97. Package content is immutable after finalization.
98. Package identity is distinct from human-readable version.
99. Package dependencies can be represented without defining a package registry.
100. Package deployment remains separable from package storage.
101. Package runtime remains separable from package manager.
102. Package format can evolve without silently changing old semantics.
103. Unknown mandatory features fail explicitly.
104. Unknown optional metadata can be skipped.
105. Resource handles cannot outlive package generations unsafely.
106. Unmount semantics are explicit.
107. Package caches cannot become authoritative state.
108. Object identity is cryptographically derived.
109. Large-model resources can be streamed by chunk.
110. Partial downloads can resume using object/chunk identity.
111. Offline installation is supported.
112. Deterministic package inspection is supported.
113. Package build artifacts are AI-readable.
114. Package manifests can be inspected without executing package code.
115. AXPK can act as a VFS read-only filesystem.
116. Overlay filesystem integration works.
117. Atomic generation activation works.
118. Previous valid generations can be retained.
119. Package reclamation respects leases and pins.
120. The subsystem remains usable on constrained targets through feature profiles.

---

# 288. Final Design Decision

BOOTSTRAP-613 establishes **AXPK + immutable content-addressed objects + chunked resources** as the native packaging foundation.

The critical separation is:

```text
AXPK
    = package/container identity

ObjectStore
    = immutable content storage

VFS
    = resource namespace

Compression
    = storage/transport optimization

Crypto
    = integrity/confidentiality/trust

Package Manager
    = higher-level dependency/deployment policy
```

This prevents the core runtime from becoming coupled to a monolithic package-manager design.

---

# 289. Final Architecture

```text
                    ┌─────────────────────────────┐
                    │       Axiom Compiler        │
                    │        + Linker             │
                    └──────────────┬──────────────┘
                                   │
                    ┌──────────────▼──────────────┐
                    │      Resource Compiler      │
                    └──────────────┬──────────────┘
                                   │
                    ┌──────────────▼──────────────┐
                    │       AXPK Package Builder   │
                    └──────────────┬──────────────┘
                                   │
             ┌─────────────────────┼─────────────────────┐
             │                     │                     │
     ┌───────▼───────┐     ┌───────▼───────┐     ┌──────▼──────┐
     │ Compression   │     │ Crypto 610    │     │ AXBIN 612   │
     │               │     │ Hash/Sign/AEAD │     │ Manifest    │
     └───────┬───────┘     └───────┬───────┘     └──────┬──────┘
             └─────────────────────┼─────────────────────┘
                                   │
                    ┌──────────────▼──────────────┐
                    │   Content Addressed Store   │
                    │       Objects / Chunks      │
                    └──────────────┬──────────────┘
                                   │
                    ┌──────────────▼──────────────┐
                    │        AXPK Package          │
                    │ Manifest + Index + Merkle   │
                    └──────────────┬──────────────┘
                                   │
                 ┌─────────────────┼─────────────────┐
                 │                 │                 │
        ┌────────▼────────┐ ┌──────▼───────┐ ┌──────▼─────────┐
        │ Package VFS     │ │ Resource API │ │ Package Store  │
        └────────┬────────┘ └──────┬───────┘ └──────┬─────────┘
                 │                 │                 │
                 └─────────────────┼─────────────────┘
                                   │
                         ┌─────────▼─────────┐
                         │   Axiom Runtime   │
                         └───────────────────┘

Security       → 603
Resources      → 606
Scheduler      → 607
Synchronization→ 608
Networking     → 609
Crypto         → 610
Storage        → 611
Serialization  → 612
```

---

# 290. Task Completion

**BOOTSTRAP-613 is complete.**

The native Axiom storage stack now has:

```text
611  → physical storage / VFS
612  → structured persistence / serialization
613  → compression / packages / immutable objects / resources
```

This creates the foundation required before moving into hardware-facing native runtime services.

**Next task:**

## BOOTSTRAP-614 — Native Device, Hardware, Peripheral, Sensor, GPU/Accelerator & OS Resource I/O Runtime 5.0

Scope will cover the hardware abstraction boundary, device discovery, typed device handles, DMA/buffer ownership, PCI/USB/Bluetooth, display/audio/input, sensors, GPU/accelerators, compute queues, device capabilities, hot-plug, embedded peripherals, platform adapters, and integration with Axiom's memory/resource/security/scheduler models.
:::

BOOTSTRAP-613 đã hoàn tất. Chuỗi kiến trúc tiếp tục tự động sang **BOOTSTRAP-614** ở lượt kế tiếp.