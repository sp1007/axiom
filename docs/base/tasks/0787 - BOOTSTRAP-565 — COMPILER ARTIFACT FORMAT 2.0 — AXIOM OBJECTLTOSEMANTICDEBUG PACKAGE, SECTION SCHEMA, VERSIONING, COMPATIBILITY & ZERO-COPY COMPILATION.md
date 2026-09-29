# BOOTSTRAP-565 — COMPILER ARTIFACT FORMAT 2.0 — AXIOM OBJECT/LTO/SEMANTIC/DEBUG PACKAGE, SECTION SCHEMA, VERSIONING, COMPATIBILITY & ZERO-COPY COMPILATION CACHE

**Trạng thái: COMPLETED / LOCKED**

`BOOTSTRAP-565` khóa **hệ thống artifact nội bộ của Axiom**: cách compiler lưu, truyền, cache, mmap, validate và tái sử dụng dữ liệu giữa các phase.

Mục tiêu cốt lõi:

> Một artifact Axiom phải có identity rõ ràng, version rõ ràng, dependency rõ ràng, có thể validate độc lập, đọc nhanh bằng mmap khi phù hợp và không trở thành một “nguồn sự thật thứ hai” ngoài semantic/compiler model.

---

# 565.1. Artifact architecture

```text
                         Axiom Source
                              │
                              ▼
                     Compiler Semantic DB
                              │
          ┌───────────────────┼───────────────────┐
          ▼                   ▼                   ▼
      .axsem              .axmir              .axlto
   Semantic Data        MIR Artifact        LTO Summary
          │                   │                   │
          └───────────────────┼───────────────────┘
                              ▼
                           .axobj
                       Native Object
                              │
                    ┌─────────┴─────────┐
                    ▼                   ▼
                 .axdbg              .axpkg
              Debug Artifact       Package Artifact
                    │                   │
                    └─────────┬─────────┘
                              ▼
                         Link / Deploy
```

---

# 565.2. Artifact không phải source cache đơn thuần

Artifact có thể chứa:

- semantic information;
- IR;
- machine code;
- relocations;
- debug metadata;
- dependency fingerprints;
- ABI information;
- optimization evidence;
- AI-readable metadata.

Nhưng artifact không được thay thế source semantics.

---

# 565.3. Artifact identity

Mỗi artifact có:

```text
ArtifactId {
    content_hash
    schema_id
    schema_version
}
```

---

# 565.4. Content hash

Hash phải được tính trên canonical serialized representation.

---

# 565.5. Hash algorithm

Artifact schema phải cho phép algorithm agility.

Default production algorithm phải là cryptographically strong hash.

---

# 565.6. Canonical serialization

Cùng một semantic artifact phải có một canonical encoding duy nhất trong reproducible mode.

---

# 565.7. No pointer serialization

Không được serialize:

- host pointer;
- virtual address;
- allocator address;
- process-specific handle.

---

# 565.8. Internal IDs

Artifact sử dụng stable IDs:

```text
FileId
SymbolId
TypeId
FunctionId
BlockId
InstructionId
SectionId
```

---

# 565.9. ID scope

Mỗi ID phải có scope rõ:

```text
ArtifactLocal
PackageLocal
WorkspaceLocal
GlobalContentAddressed
```

Không được nhầm lẫn.

---

# 565.10. Artifact header

Canonical header:

```text
ArtifactHeader {
    magic
    format_family
    schema_version
    artifact_kind
    target_id
    producer_id
    producer_version
    flags
    content_hash
    payload_offset
    payload_size
}
```

---

# 565.11. Magic

Mỗi artifact family có magic riêng.

Ví dụ:

```text
AXSEM
AXMIR
AXLTO
AXOBJ
AXDBG
AXPKG
```

Magic chỉ nhận diện; không phải security boundary.

---

# 565.12. Endianness

Artifact format canonical default:

```text
little-endian
```

Parser phải reject unsupported encoding.

---

# 565.13. Integer encoding

Fixed-width integer fields sử dụng explicit width.

Variable-length integer chỉ dùng ở những trường hợp có lợi cho size.

---

# 565.14. Offset encoding

Offset phải là:

```text
relative_to_artifact
```

không phải absolute filesystem address.

---

# 565.15. Bounds

Mọi offset/size phải được bounds-check trước dereference.

---

# 565.16. Section table

Artifact gồm các sections:

```text
Artifact
 ├── Header
 ├── SectionTable
 ├── StringTable
 ├── IDTable
 ├── Payload
 └── IntegrityMetadata
```

---

# 565.17. Section descriptor

```text
SectionDescriptor {
    id
    type
    flags
    alignment
    offset
    compressed_size
    uncompressed_size
    checksum
}
```

---

# 565.18. Section types

Ví dụ:

```text
Strings
Symbols
Types
Functions
TypesLayout
IR
MachineCode
Relocations
Debug
Dependencies
Exports
Imports
Optimization
Security
AI
```

---

# 565.19. Section flags

```text
READ_ONLY
MMAPABLE
COMPRESSED
DEDUPLICABLE
OPTIONAL
TARGET_SPECIFIC
PRIVATE
PUBLIC
```

---

# 565.20. MMAPABLE

MMAPABLE section phải có layout có thể truy cập trực tiếp sau mapping.

---

# 565.21. Zero-copy

Compiler có thể dùng trực tiếp mapped section nếu:

- alignment hợp lệ;
- endian phù hợp;
- schema tương thích;
- representation immutable.

---

# 565.22. No unsafe native cast

Không được coi bytes arbitrary là native struct chỉ vì kích thước giống nhau.

Artifact reader phải validate layout.

---

# 565.23. String table

String table deduplicate strings.

---

# 565.24. String references

Mỗi string reference là:

```text
StringId
```

không phải raw process pointer.

---

# 565.25. Symbol table

```text
ArtifactSymbol {
    symbol_id
    name_id
    kind
    visibility
    type_ref
    linkage
}
```

---

# 565.26. Type table

Type references trỏ tới canonical TypeId hoặc artifact-local type record.

---

# 565.27. Type compatibility

Type identity phải preserve nominal semantics từ `430`.

---

# 565.28. Layout section

Có thể chứa:

```text
size
alignment
field offsets
stride
ABI representation
```

nhưng phải có target fingerprint.

---

# 565.29. Target binding

Target-dependent artifact phải record:

```text
TargetFingerprint
```

gồm tối thiểu:

```text
architecture
OS
ABI
endianness
pointer_width
CPU_features
object_format
```

---

# 565.30. Cross-target reuse

Target-independent semantic artifacts có thể reuse cross-target.

Machine artifacts không được reuse sai target.

---

# 565.31. `.axsem`

`.axsem` chứa semantic information đã kiểm chứng.

```text
.axsem
 ├── symbols
 ├── types
 ├── traits
 ├── layouts
 ├── effects
 ├── ownership
 ├── dependencies
 └── API metadata
```

---

# 565.32. `.axsem` không chứa machine code bắt buộc

Semantic artifact không phụ thuộc machine ISA.

---

# 565.33. `.axmir`

`.axmir` chứa MIR hoặc canonical serialized MIR.

---

# 565.34. MIR version

MIR schema version độc lập với language edition.

---

# 565.35. MIR compatibility

Compiler mới chỉ đọc MIR cũ nếu compatibility matrix cho phép.

---

# 565.36. No silent MIR reinterpretation

Nếu schema semantics thay đổi incompatible:

```text
ERROR
```

không tự đoán.

---

# 565.37. `.axlto`

`.axlto` chứa:

- function summaries;
- call graph;
- type/layout summaries;
- alias summaries;
- effect summaries;
- optimization metadata;
- inline candidates;
- specialization information.

---

# 565.38. LTO artifact

Không bắt buộc chứa toàn bộ source.

---

# 565.39. LTO reproducibility

LTO artifact phải reproduce cùng semantic result khi inputs giống nhau.

---

# 565.40. `.axobj`

`.axobj` là native object format của Axiom.

Nó có thể encapsulate:

```text
machine code
data
relocations
symbols
debug references
unwind
LTO summary
semantic references
```

---

# 565.41. `.axobj` ≠ final executable

Final executable vẫn được tạo bởi linker `564`.

---

# 565.42. Native object compatibility

`.axobj` phải có target/object ABI metadata.

---

# 565.43. External object conversion

Foreign ELF/COFF/Mach-O object có thể được ingest vào linker mà không cần biến thành `.axobj`.

---

# 565.44. `.axdbg`

Debug artifact có:

```text
source mapping
line tables
variable locations
type debug info
inline stacks
unwind references
```

---

# 565.45. Debug artifact separation

Debug có thể nằm ngoài release binary.

---

# 565.46. `.axpkg`

Package artifact chứa:

```text
manifest
artifacts
dependency graph
target variants
metadata
signatures
provenance
```

---

# 565.47. Artifact dependency

```text
ArtifactDependency {
    artifact_id
    role
    compatibility
    required
}
```

---

# 565.48. Dependency role

Ví dụ:

```text
SemanticInput
IRInput
LTOInput
NativeObject
Debug
Runtime
Resource
```

---

# 565.49. Dependency hash

Artifact cache không được chỉ dựa trên filename.

---

# 565.50. Cache identity

```text
CacheKey =
hash(
    artifact inputs
    compiler semantics
    compiler version
    schema
    target
    ABI
    feature set
    configuration
)
```

---

# 565.51. Compiler version

Compiler version được phân thành:

```text
semantic_version
artifact_schema_version
implementation_version
```

---

# 565.52. Semantic compatibility

Hai compiler implementation khác nhau có thể đọc cùng artifact nếu schema/semantic contract tương thích.

---

# 565.53. Schema compatibility classes

```text
Exact
BackwardCompatible
ForwardCompatible
Transformable
Incompatible
```

---

# 565.54. Schema negotiation

Reader có thể yêu cầu:

```text
minimum_schema
maximum_schema
```

---

# 565.55. Migration

Artifact migration là explicit transformation:

```text
old artifact
 ↓
validator
 ↓
migrator
 ↓
new artifact
```

---

# 565.56. Migration provenance

Migration phải record:

```text
source_artifact_hash
source_schema
target_schema
migrator_version
```

---

# 565.57. No silent migration

Compiler không được mutate cached artifact in place.

---

# 565.58. Immutable artifacts

Artifact cache entries immutable.

---

# 565.59. Atomic cache publication

```text
write temp
 ↓
validate
 ↓
hash
 ↓
atomic publish
```

---

# 565.60. Content-addressable storage

Cache layout:

```text
cache/
  ab/
    cd/
      abcdef...
```

Artifact path derived from content identity.

---

# 565.61. Deduplication

Hai identical artifacts chỉ lưu một payload.

---

# 565.62. Chunk deduplication

Large artifacts có thể chia chunks.

---

# 565.63. Chunk identity

Chunk hash độc lập.

---

# 565.64. Merkle artifact

Large package có thể sử dụng Merkle tree:

```text
                 Root Hash
                 /       \
              Hash       Hash
             /   \       /   \
          Chunk Chunk Chunk Chunk
```

---

# 565.65. Partial fetch

Remote cache có thể lấy chỉ sections/chunks cần thiết.

---

# 565.66. Lazy section loading

Reader không cần load toàn artifact.

---

# 565.67. Demand-driven loading

Ví dụ IDE chỉ cần:

```text
symbols
types
source map
```

không cần machine code.

---

# 565.68. Compiler daemon integration

`555` có thể giữ mapped artifacts trong memory.

---

# 565.69. Snapshot binding

Artifact result phải bind với compiler snapshot/dependency fingerprint.

---

# 565.70. Stale artifact

Nếu dependency fingerprint mismatch:

```text
STALE
```

không dùng như fresh semantic result.

---

# 565.71. Partial validity

Một artifact có thể có section còn valid và section stale.

Reader phải biết section validity.

---

# 565.72. Artifact freshness

```text
Fresh
Stale
Unknown
Invalid
```

---

# 565.73. Semantic artifact reuse

Một module interface không đổi có thể reuse `.axsem`.

---

# 565.74. Implementation-only change

Nếu implementation thay đổi nhưng public semantic interface không đổi, dependent modules có thể không cần semantic re-analysis.

---

# 565.75. ABI change

ABI-relevant change phải invalidate binary consumers.

---

# 565.76. Layout change

Type layout change phải invalidate consumers phụ thuộc layout.

---

# 565.77. Effect change

Effect metadata change phải invalidate queries phụ thuộc effect.

---

# 565.78. Trait implementation change

Trait resolution dependencies phải invalidate.

---

# 565.79. Generic specialization

Specialization cache key phải bao gồm concrete type parameters.

---

# 565.80. Const generic

Const arguments là một phần identity.

---

# 565.81. Comptime output

Comptime result hash là input của dependent artifacts.

---

# 565.82. Generated source

Generated-source provenance phải record generator artifact/version/input.

---

# 565.83. Resource artifact

Resources từ `469` có thể được content-addressed giống compiler artifacts.

---

# 565.84. Debug artifact identity

Debug artifact bind với exact executable/object identity.

---

# 565.85. Source mapping identity

Source map phải bind với exact generated code identity.

---

# 565.86. Machine code identity

Machine section hash phải được recorded.

---

# 565.87. Relocation identity

Relocation table hash có thể dùng trong object correctness validation.

---

# 565.88. Object artifact validation

`565` validator kiểm tra:

```text
header
sections
offsets
sizes
hashes
target
symbols
references
```

---

# 565.89. Semantic artifact validation

Kiểm tra:

```text
type references
symbol references
trait references
layout references
dependency references
```

---

# 565.90. MIR validator

MIR phải pass verifier trước khi được cache.

---

# 565.91. LTO validator

LTO summaries phải khớp underlying semantic identity.

---

# 565.92. Machine validator

`.axobj` phải pass machine/object validation từ `561/564`.

---

# 565.93. Trust level

Artifact có:

```text
Untrusted
Validated
TrustedByBuild
Signed
```

---

# 565.94. Trust không phải semantics

Signed artifact không tự động đồng nghĩa semantic correctness.

---

# 565.95. Signature

Package/distribution layer `489/550` chịu trách nhiệm signing policy.

---

# 565.96. Artifact provenance

```text
Provenance {
    source_hashes[]
    dependency_hashes[]
    compiler_build_id
    toolchain_id
    target
    configuration
    generator
}
```

---

# 565.97. Reproducible artifact

Cùng:

```text
source
dependencies
compiler
toolchain
target
configuration
```

→ cùng canonical artifact bytes.

---

# 565.98. Non-reproducible mode

Có thể chứa volatile metadata nếu explicit.

---

# 565.99. Volatile metadata separation

Build timestamp không được nằm trong canonical semantic payload.

---

# 565.100. Host path normalization

Absolute host paths không được làm thay đổi semantic artifact identity trong reproducible mode.

---

# 565.101. Debug paths

Debug path có thể dùng source remapping.

---

# 565.102. Artifact compression

Sections có thể compressed độc lập.

---

# 565.103. Compression identity

Cache identity phải tính trên canonical uncompressed semantic payload hoặc canonical artifact representation, không phụ thuộc compression implementation.

---

# 565.104. Compression algorithm

Có thể thay đổi mà không làm semantic cache miss nếu artifact identity policy cho phép.

---

# 565.105. Encryption

Artifact encryption là distribution/storage feature, không phải compiler semantic feature.

---

# 565.106. Secret data

Không được đưa secret vào semantic artifact trừ khi explicitly required.

---

# 565.107. Source privacy

`.axsem` public artifact phải có policy strip private source information.

---

# 565.108. API-only metadata

Package có thể phân phối API metadata mà không phân phối source.

---

# 565.109. AI metadata

Artifact có thể chứa:

```text
AIIndex {
    symbols
    semantic summaries
    dependency graph
    call graph
    effects
    safety
    ABI
}
```

---

# 565.110. AI metadata provenance

AI summary phải distinguish:

```text
CompilerFact
DerivedFact
Heuristic
GeneratedDescription
```

---

# 565.111. AI metadata cannot override compiler semantics

Nếu AI metadata mâu thuẫn với semantic tables:

```text
semantic tables win
```

---

# 565.112. AI query index

AI có thể query artifact trực tiếp mà không parse source.

---

# 565.113. Symbol neighborhood

Artifact có thể index:

```text
callers
callees
references
implementors
implementations
types
dependencies
```

---

# 565.114. Semantic diff

Artifact format phải hỗ trợ diff:

```text
API change
ABI change
layout change
trait change
effect change
dependency change
```

---

# 565.115. Artifact graph

```text
.axsem
  │
  ├──→ .axmir
  │       │
  │       └──→ .axlto
  │               │
  │               └──→ .axobj
  │                        │
  │                        └──→ executable
  │
  └──→ .axdbg
```

---

# 565.116. Graph identity

Mỗi edge phải record dependency role và hash.

---

# 565.117. No implicit dependency

Artifact không được phụ thuộc vào undeclared external state.

---

# 565.118. Environment fingerprint

Nếu build phụ thuộc environment, environment fingerprint phải được record.

---

# 565.119. Hermetic artifact

Hermetic artifact không được phụ thuộc host state ngoài declared inputs.

---

# 565.120. Build script outputs

Build script output phải trở thành explicit artifact/build input.

---

# 565.121. External tool output

External tools có thể tạo artifact nhưng phải record:

```text tool_id
tool_version
input_hash
output_hash
```

---

# 565.122. Artifact reader API

```text
ArtifactReader {
    open()
    validate()
    section()
    symbols()
    dependencies()
    metadata()
}
```

---

# 565.123. Lazy reader

`section()` không bắt buộc load sections khác.

---

# 565.124. Mmap reader

```text
MmapArtifact {
    bytes
    header
    sections
}
```

---

# 565.125. Copying reader

Nếu mmap không phù hợp:

```text
BufferedArtifactReader
```

phải cho semantics tương đương.

---

# 565.126. Reader abstraction

Compiler phase không được phụ thuộc trực tiếp vào filesystem.

---

# 565.127. Artifact storage abstraction

```text
ArtifactStore {
    get(id)
    put(artifact)
    contains(id)
    remove(id)
}
```

---

# 565.128. Local store

Filesystem implementation.

---

# 565.129. Memory store

Compiler daemon/IDE dùng ephemeral store.

---

# 565.130. Remote store

Có thể dùng HTTP/IPC/object storage theo `487`.

---

# 565.131. Remote artifact trust

Remote artifact luôn được validate trước khi semantic use.

---

# 565.132. Cache poisoning

Hash mismatch:

```text
CACHE_CORRUPTION
```

không được silently recover bằng payload.

---

# 565.133. Cache poisoning response

Artifact invalid phải quarantine/delete theo policy.

---

# 565.134. Cache stampede

Concurrent requests cùng artifact identity phải deduplicate.

---

# 565.135. Cache lock

Lock không được trở thành global bottleneck.

---

# 565.136. Artifact GC

Unused artifacts có thể được garbage-collected **ở cache storage**.

Điều này không phải language GC.

---

# 565.137. Cache retention

Retention policy:

```text
LRU
size-based
age-based
pinned
dependency-aware
```

---

# 565.138. Pinned artifacts

Release artifacts có thể pin.

---

# 565.139. Artifact lease

Daemon có thể lease mapped artifacts để tránh eviction khi đang dùng.

---

# 565.140. Memory pressure

Mapped sections không còn cần thiết phải được unmap.

---

# 565.141. Shared mappings

Multiple compiler queries có thể share immutable mapped section.

---

# 565.142. Copy-on-write

Không mutate mapped semantic data.

---

# 565.143. Mutable working representation

Nếu phase cần mutation:

```text
immutable artifact
 ↓
working IR
```

và chỉ serialize sau khi hoàn thành.

---

# 565.144. Artifact locking

Artifact file không cần process-wide mutable lock vì immutable.

---

# 565.145. Crash safety

Partial artifact không được trở thành valid cache entry.

---

# 565.146. Transactional publication

```text
build
 ↓
validate
 ↓
hash
 ↓
publish
```

---

# 565.147. Artifact repair

Corrupt artifact phải được rebuild từ authoritative inputs.

---

# 565.148. Artifact as cache

Artifact cache là optimization.

---

# 565.149. Cache purge invariant

Xóa toàn bộ cache không được thay đổi program semantics.

---

# 565.150. Semantic authority

Nguồn sự thật vẫn là:

```text
Source + declared inputs + compiler semantics
```

không phải cache.

---

# 565.151. Artifact schema registry

Compiler source tree phải chứa schema definitions.

---

# 565.152. Schema generation

Có thể generate:

- readers;
- writers;
- validators;
- documentation.

---

# 565.153. Schema IDs

Mỗi schema có stable ID.

---

# 565.154. Schema evolution

Field addition có thể backward-compatible nếu optional/default.

---

# 565.155. Field removal

Field removal phải schema migration hoặc major schema change.

---

# 565.156. Enum evolution

Unknown enum values phải reject hoặc preserve theo declared extensibility.

---

# 565.157. Reserved fields

Format phải reserve fields cho future extensions.

---

# 565.158. Unknown sections

Reader policy:

```text
RequiredUnknown → ERROR
OptionalUnknown → SKIP
```

---

# 565.159. Forward compatibility

Future optional sections không được làm old reader crash.

---

# 565.160. Backward compatibility

New reader chỉ accept old schema khi semantic compatibility được chứng minh.

---

# 565.161. Artifact feature flags

Feature bits phải có defined semantics.

---

# 565.162. Target feature bits

CPU feature metadata không được nhầm với schema feature bits.

---

# 565.163. ABI fingerprint

```text
ABIFingerprint {
    calling_convention
    type_abi
    object_format
    platform_abi
}
```

---

# 565.164. ABI cache key

ABI fingerprint là mandatory input cho native artifact cache.

---

# 565.165. Toolchain fingerprint

Toolchain/SDK/sysroot fingerprint là input khi artifact phụ thuộc chúng.

---

# 565.166. Runtime fingerprint

Runtime component versions/hash phải được record khi linked.

---

# 565.167. Standard library fingerprint

Stdlib ABI/API identity phải được record.

---

# 565.168. Package fingerprint

Package dependency lock state phải được record.

---

# 565.169. Configuration fingerprint

Relevant compiler configuration phải nằm trong artifact identity.

---

# 565.170. Security-policy fingerprint

Security hardening settings ảnh hưởng artifact phải là cache input.

---

# 565.171. Optimization fingerprint

Optimization profile từ `553` là cache input khi ảnh hưởng generated artifact.

---

# 565.172. PGO profile fingerprint

PGO profile hash phải được record.

---

# 565.173. Sanitizer fingerprint

Sanitizer configuration phải được record.

---

# 565.174. Debug fingerprint

Debug profile phải được record cho debug artifacts.

---

# 565.175. Feature specialization

CPU-specific artifact phải record exact CPU feature set.

---

# 565.176. Multi-versioned artifact

Một package có thể chứa:

```text
baseline
avx2
avx512
neon
sve
```

variants.

---

# 565.177. Variant selection

Runtime dispatch hoặc deployment target quyết định variant.

---

# 565.178. Wrong variant protection

Artifact không được chạy nếu required CPU features không available.

---

# 565.179. Cross-compilation cache

Host CPU features không được vô tình trở thành target cache input.

---

# 565.180. Artifact inspection CLI

CLI hỗ trợ:

```text
axiom artifact info
axiom artifact sections
axiom artifact symbols
axiom artifact deps
axiom artifact validate
axiom artifact diff
axiom artifact hash
```

---

# 565.181. Artifact disassembly

`.axobj` có thể được disassemble thông qua backend metadata.

---

# 565.182. Artifact semantic inspection

`.axsem` có thể query:

```text
axiom artifact symbol Foo
axiom artifact type Foo
axiom artifact callers Foo
```

---

# 565.183. Artifact conversion

Conversion phải explicit:

```text
.axsem → newer .axsem
.axmir → .axmir
```

không mutate source artifact.

---

# 565.184. Artifact extraction

Package có thể extract constituent artifacts mà không cần compile source.

---

# 565.185. Package integrity

`.axpkg` phải validate constituent hashes.

---

# 565.186. Package manifest

Manifest phải record:

```text
artifact
target
ABI
dependencies
entry points
exports
resources
signatures
```

---

# 565.187. Artifact licensing

License/provenance metadata có thể nằm ở package layer.

---

# 565.188. Artifact SBOM

`489/550` có thể generate SBOM từ artifact dependency graph.

---

# 565.189. Security scanning

Artifact scanner có thể inspect:

- imports;
- permissions;
- dependencies;
- unsafe metadata;
- signatures.

---

# 565.190. Compiler correctness integration

`552` có thể attach:

```text
CorrectnessEvidence
```

vào `.axmir/.axobj`.

---

# 565.191. Optimization evidence

`553` có thể attach:

```text
OptimizationEvidence
```

---

# 565.192. Debug provenance

`440` có thể attach exact source→machine mappings.

---

# 565.193. Incremental frontend integration

`556` sử dụng `.axsem` để reuse semantic fragments.

---

# 565.194. Compiler memory integration

`557` có thể mmap immutable artifact sections và materialize chỉ khi cần.

---

# 565.195. Parallel compiler integration

`558` cho phép workers cùng đọc immutable artifact sections mà không lock semantic state.

---

# 565.196. Query engine integration

`559/560` dùng artifact dependency fingerprints để quyết định query reuse/invalidation.

---

# 565.197. Linker integration

`564` consume `.axobj` và foreign native objects.

---

# 565.198. Self-hosting integration

Axiom compiler stage1/2 phải có khả năng đọc/ghi artifact format mà không cần third-party compiler infrastructure.

---

# 565.199. Acceptance tests

Phải có:

```text
artifact round-trip
schema compatibility
corruption rejection
mmap read
buffered read
cache hit/miss
incremental reuse
cross-target rejection
remote cache validation
parallel access
crash recovery
reproducibility
semantic diff
AI query
```

---

# 565.200. HARD INVARIANTS

1. Artifact không được trở thành nguồn sự thật thứ hai của compiler.
2. Source semantics luôn là authoritative input.
3. Artifact identity phải deterministic.
4. Canonical serialization phải deterministic.
5. Artifact hash phải ổn định.
6. Process pointer không được serialize.
7. Host virtual address không được serialize.
8. Absolute host filesystem state không được implicit dependency.
9. Mọi offset phải bounds-check.
10. Mọi size phải overflow-check.
11. Header phải validate trước payload.
12. Section table phải validate trước section access.
13. Unknown required section phải reject.
14. Unknown optional section phải có thể skip.
15. Schema version phải được kiểm tra.
16. Schema incompatibility không được silent reinterpret.
17. Migration phải explicit.
18. Migration phải preserve provenance.
19. Artifact cache entry phải immutable.
20. Cache publication phải atomic.
21. Partial artifact không được coi là valid.
22. Corrupt hash phải reject.
23. Cache poisoning phải detectable.
24. Cache purge không được thay đổi semantics.
25. Cache hit phải equivalent clean compilation.
26. Incremental reuse phải dependency-aware.
27. Stale semantic result không được dùng như fresh.
28. Artifact freshness phải explicit.
29. Target fingerprint phải được record khi target-dependent.
30. ABI fingerprint phải được record cho native artifacts.
31. CPU feature requirements phải được record.
32. Wrong-target artifacts phải reject.
33. Wrong-ABI artifacts phải reject.
34. Wrong-endian artifacts phải reject.
35. Wrong-pointer-width artifacts phải reject.
36. Cross-target semantic artifacts chỉ reuse khi target-independent.
37. Machine artifacts không được cross-target reuse.
38. LTO schema phải validate.
39. MIR schema phải validate.
40. `.axobj` phải validate trước linker use.
41. `.axdbg` phải bind exact code identity.
42. Source mapping phải bind exact generated code.
43. Debug information không được làm thay đổi program semantics.
44. Compression không được thay đổi canonical identity.
45. Compression algorithm không được trở thành semantic input nếu policy loại trừ.
46. Encryption không được trở thành semantic input nếu policy loại trừ.
47. Semantic sections phải immutable sau publication.
48. Mmap access phải preserve representation semantics.
49. Native struct layout không được assumed từ bytes.
50. Artifact reader phải validate alignment.
51. String references phải bounds-check.
52. Symbol references phải bounds-check.
53. Type references phải bounds-check.
54. Function references phải bounds-check.
55. Relocation references phải bounds-check.
56. Dependency references phải bounds-check.
57. Section alignment phải validate.
58. Section overlap phải detect.
59. Integer overflow phải detect.
60. Artifact truncation phải detect.
61. Artifact trailing garbage phải policy-check.
62. Artifact magic phải validate.
63. Artifact kind phải validate.
64. Producer metadata phải preserve.
65. Compiler build identity phải preserve.
66. Toolchain identity phải preserve.
67. Sysroot identity phải preserve.
68. Runtime identity phải preserve.
69. Stdlib identity phải preserve.
70. Package lock identity phải preserve.
71. Configuration identity phải preserve.
72. Optimization profile identity phải preserve.
73. PGO identity phải preserve.
74. Sanitizer identity phải preserve.
75. Security policy identity phải preserve.
76. Debug profile identity phải preserve.
77. Generated source provenance phải preserve.
78. Comptime provenance phải preserve.
79. External tool provenance phải preserve.
80. Build-script provenance phải preserve.
81. Artifact dependency graph phải explicit.
82. Artifact dependency hash phải explicit.
83. Undeclared external dependencies không được ảnh hưởng hermetic artifact.
84. Environment dependency phải fingerprint.
85. Host contamination phải detectable.
86. Remote artifacts phải validate trước use.
87. Signed artifacts phải vẫn validate structurally.
88. Signature không được thay thế semantic validation.
89. AI metadata không được override compiler facts.
90. AI-generated description phải distinguishable.
91. AI heuristic phải distinguishable.
92. AI query phải snapshot/build bound.
93. Semantic diff phải preserve SymbolId identity.
94. ABI diff phải distinguishable from API diff.
95. Layout diff phải distinguishable from API diff.
96. Effect diff phải distinguishable.
97. Trait resolution change phải invalidate dependent queries.
98. Layout change phải invalidate layout consumers.
99. ABI change phải invalidate binary consumers.
100. Comptime output change phải invalidate dependents.
101. Generic specialization identity phải include type arguments.
102. Const generic identity phải include values.
103. CPU variant identity phải include features.
104. Multi-version artifacts phải preserve variant identity.
105. Runtime dispatch không được chọn unsupported CPU variant.
106. Artifact GC chỉ áp dụng cache storage, không phải language memory.
107. Artifact eviction không được invalidate source correctness.
108. Artifact lease phải protect active mappings.
109. Mapped immutable sections có thể share.
110. Mutable compiler state không được alias artifact storage.
111. Working IR mutation phải không mutate cached artifact.
112. Re-serialization phải produce canonical output.
113. Artifact round-trip phải preserve semantics.
114. Reader implementation differences không được alter semantics.
115. Buffered reader và mmap reader phải equivalent.
116. Local cache và remote cache phải equivalent.
117. Serial artifact processing và parallel processing phải equivalent.
118. Artifact cache stampede phải bounded.
119. Concurrent artifact requests phải deduplicate.
120. Cache lock không được create semantic race.
121. Artifact store phải expose explicit failure states.
122. Storage failure không được giả làm cache miss nếu integrity uncertain.
123. Corruption phải be distinguishable from absence.
124. Missing artifact phải be distinguishable from stale artifact.
125. Stale artifact phải be distinguishable from invalid artifact.
126. Invalid artifact phải not enter cache.
127. Migration failure phải preserve original artifact.
128. Migration phải not mutate source artifact.
129. Schema downgrade phải explicit.
130. Forward incompatibility phải diagnostic.
131. Backward incompatibility phải diagnostic.
132. Optional fields phải have deterministic defaults.
133. Required fields phải never be implicitly defaulted.
134. Enum evolution phải deterministic.
135. Feature bits phải have defined semantics.
136. Reserved bits phải not be interpreted accidentally.
137. Target-specific sections phải carry target identity.
138. Target-independent sections phải not contain hidden target assumptions.
139. `.axsem` phải remain ISA-independent.
140. `.axmir` semantics phải not depend on machine addresses.
141. `.axlto` phải preserve optimization-relevant semantics.
142. `.axobj` phải preserve native ABI.
143. `.axdbg` must not be required for execution.
144. `.axpkg` must not redefine contained artifact semantics.
145. Package manifest must match constituent hashes.
146. Package dependency closure must be verifiable.
147. SBOM generation must use actual artifact dependencies.
148. Security scanner must inspect actual artifact identity.
149. Code signing must occur after final artifact mutation.
150. Signed artifact mutation must invalidate signature.
151. Correctness evidence must bind exact artifact identity.
152. Optimization evidence must bind exact transformation identity.
153. Debug evidence must bind exact machine identity.
154. Provenance must survive artifact conversion.
155. Provenance must survive package extraction.
156. Provenance must survive cache transfer.
157. Artifact hash mismatch must never be ignored.
158. Schema mismatch must never be silently ignored.
159. Target mismatch must never be silently ignored.
160. ABI mismatch must never be silently ignored.
161. Dependency mismatch must never be silently ignored.
162. Configuration mismatch must never be silently ignored.
163. Security-policy mismatch must never be silently ignored.
164. Compiler semantic version mismatch must follow compatibility policy.
165. Compiler implementation version alone must not invalidate target-independent semantic artifacts unnecessarily.
166. Artifact schema change must invalidate only affected artifact families.
167. Cache keys must contain every semantic input that can affect output.
168. Cache keys must not contain irrelevant volatile inputs.
169. Cache identity must be explainable.
170. Compiler must be able to explain cache hit.
171. Compiler must be able to explain cache miss.
172. Compiler must be able to explain invalidation.
173. AI must be able to query artifact provenance.
174. AI must be able to query artifact dependencies.
175. AI must be able to query artifact semantic neighborhood.
176. AI must be able to query ABI information.
177. AI must be able to query optimization evidence.
178. AI must be able to query correctness evidence.
179. Artifact inspection must not require source parsing.
180. Public API metadata must be distributable without private source.
181. Private source metadata must be strip-able.
182. Artifact privacy policy must be explicit.
183. Secrets must not enter artifacts unintentionally.
184. Artifact parser must treat input as untrusted.
185. Malformed artifact must not crash compiler.
186. Fuzzed artifact must not cause memory unsafety.
187. Large artifact parsing must have resource limits.
188. Recursive artifact structures must have depth limits.
189. Decompression must have resource limits.
190. Remote artifact fetch must have size limits.
191. Remote artifact verification must occur before semantic use.
192. Self-hosted Axiom compiler must read/write the format itself.
193. Production artifact path must not require LLVM.
194. Production artifact path must not require GCC.
195. Production artifact path must not require Clang.
196. Production artifact path must not require MSVC compiler infrastructure.
197. Artifact architecture must integrate `555–564`.
198. Artifact architecture must support incremental, parallel and distributed compilation.
199. Artifact architecture must preserve reproducibility, correctness and provenance.
200. **Final invariant:** Axiom artifacts phải là **immutable, content-addressed, versioned, target-aware, dependency-explicit, verifiable và cache-safe compiler products**, có thể được đọc lazy/mmap khi phù hợp, nhưng tuyệt đối không được trở thành một semantic authority độc lập; xóa cache, thay đổi cache layout, dùng local/remote cache, mmap/buffered reader hay thay đổi mức parallelism không được làm thay đổi kết quả đúng của compiler.

**BOOTSTRAP-565: LOCKED.**

---

# NEXT — BOOTSTRAP-566

## COMPILER CACHE 3.0 — SEMANTIC INVALIDATION, CROSS-PHASE REUSE, REMOTE CACHE, CACHE TRUST, CACHE GC & ZERO-REBUILD INCREMENTAL COMPILATION

`565` đã định nghĩa **artifact format**. `566` sẽ khóa tầng cao hơn: **làm thế nào compiler quyết định chính xác artifact nào được tái sử dụng và artifact nào bắt buộc phải rebuild**.

Trọng tâm tiếp theo:

```text
Source Change
     │
     ▼
Dependency Fingerprint
     │
     ▼
Semantic Impact Analysis
     │
     ├───────────────┐
     ▼               ▼
Reusable         Invalidated
Artifacts        Artifacts
     │               │
     └───────┬───────┘
             ▼
       Incremental DAG
             │
      ┌──────┼──────┐
      ▼      ▼      ▼
    Cache   Compile  Remote
    Hit      Miss    Cache
      │      │        │
      └──────┼────────┘
             ▼
       Validate + Publish
```

Đặc biệt `566` sẽ khóa nguyên tắc rất quan trọng đối với mục tiêu Axiom:

> **Thay đổi một dòng code không được mặc định kéo theo recompilation toàn project; compiler phải xác định bằng semantic dependency chính xác phần nào thực sự bị ảnh hưởng, đồng thời chứng minh cache hit là tương đương clean build.**