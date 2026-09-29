# BOOTSTRAP-493 — PACKAGE ABI, BINARY INTERFACE DISTRIBUTION, PRECOMPILED GENERICS, MODULE INTERFACE FILES & FAST BINARY CONSUMPTION

**Trạng thái: COMPLETED / LOCKED**

493 giải quyết một vấn đề rất quan trọng đối với mục tiêu của Axiom: **package không phải lúc nào cũng cần compile lại từ source**.

Mục tiêu:

```text
Source Package
     │
     ├───────────────┐
     ↓               ↓
Source Build     Binary Package
                     │
             ┌───────┴────────┐
             ↓                ↓
        Interface Data    Native Artifacts
             │
             ↓
       Fast Consumption
```

Axiom phải có khả năng:

- import package binary rất nhanh;
- không parse lại toàn bộ source;
- không cần compiler bên thứ ba;
- dùng precompiled generic;
- kiểm tra ABI trước khi link;
- vẫn bảo toàn semantic metadata cho compiler/IDE/AI;
- rebuild chính xác khi binary không còn tương thích.

---

## 493.1 — Source package ≠ Binary package

```text
Source Package
    → source + manifest + metadata

Binary Package
    → interface + native artifacts + metadata
```

---

## 493.2 — Package interface

Binary package phải có một **machine-readable interface representation**.

Nó mô tả API mà consumer được phép sử dụng mà không cần source.

---

## 493.3 — Module interface file

Canonical concept:

```text
ModuleInterface {
    package
    module
    compiler_compatibility
    language_edition
    exports
    types
    traits
    functions
    constants
    generic_items
    ABI
    layouts
    effects
    contracts
    visibility
    metadata_schema
}
```

---

## 493.4 — Interface ≠ debug information

Interface phục vụ compilation.

Debug information phục vụ debugger.

---

## 493.5 — Interface ≠ documentation

Documentation giải thích API.

Interface mô tả **semantic facts cần cho compiler**.

---

## 493.6 — Interface ≠ source

Interface không cần chứa implementation body thông thường.

---

## 493.7 — Public API extraction

Interface được sinh từ semantic database 446.

Không cần parse source lần thứ hai.

---

## 493.8 — Symbol identity

Mỗi exported symbol có stable:

```text
PackageId
ModuleId
SymbolId
```

---

## 493.9 — Type identity

Exported types có stable semantic identity.

---

## 493.10 — Canonical type encoding

Interface phải encode canonical type representation từ 430.

---

## 493.11 — Generic declarations

Interface phải chứa:

```text
generic parameters
constraints
where clauses
associated types
associated constants
```

---

## 493.12 — Trait interface

Trait metadata phải chứa:

- methods;
- associated types;
- associated constants;
- supertraits nếu có;
- contracts;
- object-safety information.

---

## 493.13 — Impl metadata

Consumer cần biết những trait implementations public nào tồn tại.

---

## 493.14 — Coherence metadata

Interface phải đủ thông tin để kiểm tra coherence/orphan rules.

---

## 493.15 — Method resolution metadata

Compiler có thể resolve:

```text
value.method()
```

mà không cần source implementation.

---

## 493.16 — Extension methods

Extension method metadata phải được export nếu public.

---

## 493.17 — Dynamic trait metadata

`dyn Trait` cần:

```text
trait identity
object-safety properties
vtable contract
method ABI
```

---

## 493.18 — Layout metadata

Public ABI-relevant types phải expose:

```text
size
alignment
field offsets
representation
niche information
```

khi cần cho consumer.

---

## 493.19 — Private layout

Private implementation details không cần export trừ khi ảnh hưởng ABI/interface.

---

## 493.20 — Opaque types

Opaque types export identity nhưng không expose private representation.

---

## 493.21 — ABI fingerprint

Binary interface phải có ABI fingerprint.

Ví dụ conceptually:

```text
ABIFingerprint =
hash(
    target
    ABI
    exported_layouts
    calling_conventions
    representation
    compiler_abi_revision
)
```

---

## 493.22 — Semantic fingerprint

Ngoài ABI cần:

```text
SemanticFingerprint
```

để phát hiện interface semantics thay đổi.

---

## 493.23 — API fingerprint

API fingerprint mô tả exported API surface.

Ba loại không được gộp:

```text
API
Semantic
ABI
```

---

## 493.24 — Compiler compatibility

Binary interface phải khai báo compiler compatibility range/revision.

---

## 493.25 — Metadata schema compatibility

Metadata schema version được kiểm tra riêng.

---

## 493.26 — Edition compatibility

Interface ghi language edition mà package được compile.

---

## 493.27 — Target identity

Binary artifact phải encode target identity.

---

## 493.28 — CPU feature requirements

Artifact phải khai báo CPU feature requirements.

---

## 493.29 — Runtime profile

Artifact phải khai báo runtime profile/capabilities cần thiết.

---

## 493.30 — Static library

Static library có thể đi kèm interface metadata.

---

## 493.31 — Dynamic library

Dynamic library cũng phải có interface metadata để compiler/linker validate trước load/link.

---

## 493.32 — Native symbol table

Package metadata ánh xạ:

```text
Axiom SymbolId
    ↔
Native Symbol
```

---

## 493.33 — Name mangling

Axiom internal mangling phải deterministic.

---

## 493.34 — Symbol versioning

ABI có thể support symbol versioning khi platform cho phép.

---

## 493.35 — Export policy

Chỉ `pub`/explicitly exported items được đưa vào public interface.

---

## 493.36 — Private symbols

Private symbols không phải public API contract.

---

## 493.37 — Generic monomorphization

Consumer có thể instantiate generic từ interface metadata.

---

## 493.38 — Precompiled generic instance

Package có thể ship:

```text
GenericInstance {
    generic_id
    concrete_types
    target
    features
    ABI
    code
}
```

---

## 493.39 — Generic cache key

Key phải bao gồm ít nhất:

```text
generic identity
type arguments
const arguments
target
CPU features
optimization profile
ABI
semantic dependency hashes
```

---

## 493.40 — Generic correctness

Precompiled generic chỉ được dùng khi key match.

---

## 493.41 — Generic invalidation

Thay đổi ảnh hưởng semantic body phải invalidate instance.

---

## 493.42 — Generic sharing

Compiler có thể share compatible instantiations.

---

## 493.43 — Generic code bloat

Package interface có thể cung cấp specialization metadata để tránh compile duplicate code.

---

## 493.44 — Specialization

Specialized implementation phải có deterministic selection semantics.

---

## 493.45 — Precompiled optimization

Consumer có thể dùng optimized generic artifact nếu optimization assumptions match.

---

## 493.46 — LTO boundary

Package có thể cung cấp IR/LTO representation tùy distribution mode.

---

## 493.47 — Native-only package

Package có thể distribute only native code + interface.

---

## 493.48 — Source-only package

Package có thể distribute only source.

---

## 493.49 — Hybrid package

Package có thể chứa:

```text
interface
native baseline
native optimized variants
generic metadata
selected generic instances
source fallback
docs
debug symbols
```

---

## 493.50 — Binary fallback

Nếu native artifact không tương thích, package manager có thể fallback source.

---

## 493.51 — No silent incompatible fallback

Compiler phải report binary rejection reason.

---

## 493.52 — Interface cache

Compiler cache interface files locally.

---

## 493.53 — Content addressing

Interface files có content hash.

---

## 493.54 — Interface cache invalidation

Cache key phải include interface hash/compiler compatibility.

---

## 493.55 — Fast import

Import binary package ideally becomes:

```text
read interface
→ validate
→ intern symbols/types
→ attach metadata
```

thay vì:

```text
read thousands of source files
→ parse
→ type-check
```

---

## 493.56 — Lazy interface loading

Compiler có thể load detailed metadata lazily.

---

## 493.57 — Symbol index

Package interface có indexed exported symbols.

---

## 493.58 — Dependency interface closure

Compiler chỉ load interfaces cần thiết cho current compilation unit.

---

## 493.59 — Transitive metadata

Transitive dependencies có thể reference IDs/hashes thay vì duplicate toàn bộ metadata.

---

## 493.60 — Interface graph

```text
Package A
   ↓
Interface B
   ↓
Interface C
```

Compiler có thể traverse graph lazily.

---

## 493.61 — ABI validation before linking

Linker phải detect incompatible ABI trước relocation/linking khi metadata available.

---

## 493.62 — Layout validation

Cross-package ABI types phải verify layout fingerprint.

---

## 493.63 — Calling convention validation

Function imports verify:

```text
parameter ABI
return ABI
calling convention
stack alignment
variadic convention
```

---

## 493.64 — Effect metadata

Public functions có thể expose:

```text
@no_alloc
@no_block
@no_panic
@unsafe
```

và effect metadata tương ứng.

---

## 493.65 — Ownership metadata

FFI/public resource APIs có thể expose:

```text
owned
borrowed
consumes
returns_owned
```

---

## 493.66 — Contract metadata

479 contracts có thể được embedded trong interface.

---

## 493.67 — Security metadata

490 trust/capability requirements có thể được exported.

---

## 493.68 — Target availability

API có thể được đánh dấu target availability:

```text
available(windows)
available(linux)
available(aarch64)
```

---

## 493.69 — Deprecation metadata

484 deprecation information phải đi cùng interface.

---

## 493.70 — Documentation references

485 documentation IDs có thể liên kết với SymbolId.

---

## 493.71 — Source provenance

Interface có thể chứa:

```text
source_hash
package_version
build_id
```

nhưng không bắt buộc chứa source.

---

## 493.72 — Privacy

Private source không được leak qua public interface ngoài thông tin semantic bắt buộc.

---

## 493.73 — Generic privacy

Generic implementation details chỉ expose nếu consumer cần compile/instantiate.

---

## 493.74 — Closure types

Anonymous closure types không nên trở thành unstable public ABI nếu không được explicitly exposed.

---

## 493.75 — Anonymous types

Compiler-generated types cần stable internal identity khi xuất hiện trong public signatures.

---

## 493.76 — Public API restrictions

Compiler có thể reject public API phụ thuộc private/inaccessible type.

---

## 493.77 — Recursive types

Interface encode explicit indirection cho recursive representations.

---

## 493.78 — Const values

Public compile-time constants cần serialized value/type metadata.

---

## 493.79 — Comptime functions

Nếu consumer cần invoke `comptime fn`, interface phải chứa đủ metadata/body representation hợp lệ cho comptime execution.

---

## 493.80 — Comptime implementation distribution

Không được thực thi arbitrary native binary của package trong compiler comptime.

---

## 493.81 — Comptime cache

Comptime result cache từ 431 có thể distributed nếu semantic/compiler/target inputs match.

---

## 493.82 — Deterministic metadata

Interface generation phải deterministic.

---

## 493.83 — Canonical serialization

Binary interface format phải có canonical encoding.

---

## 493.84 — Forward compatibility

Consumer cũ phải reject unsupported interface schema rõ ràng thay vì đoán semantics.

---

## 493.85 — Backward compatibility

Interface schema mới có thể cung cấp compatibility profile cho consumer cũ nếu semantics tương thích.

---

## 493.86 — Interface evolution

Thay đổi:

```text
API
ABI
semantic
layout
contract
```

được classify riêng.

---

## 493.87 — API diff

Tooling phải report added/removed/changed public symbols.

---

## 493.88 — ABI diff

Tooling phải report layout/calling-convention/symbol ABI changes.

---

## 493.89 — Semantic diff

Tooling có thể report semantic metadata changes.

Không tạo aggregate compatibility score.

---

## 493.90 — AI interface query

AI có thể query binary package:

```text
exports()
type_of(symbol)
layout_of(type)
trait_impls(type)
abi(symbol)
contracts(symbol)
effects(symbol)
target_availability(symbol)
```

---

## 493.91 — Precompiled package explanation

AI có thể query:

```text
why_binary_selected()
why_binary_rejected()
why_recompiled()
```

---

## 493.92 — Rebuild reason

Compiler phải expose reason:

```text
ABI mismatch
target mismatch
CPU feature mismatch
compiler mismatch
semantic hash mismatch
missing generic instance
optimization mismatch
```

---

## 493.93 — Binary cache poisoning

Cache entries phải verify content hashes.

---

## 493.94 — Signature verification

Signed binary package có thể được verify trước consumption.

---

## 493.95 — Trust policy

Project có thể require:

```text
signed-only
approved-publisher
source-only
binary-allowed
```

---

## 493.96 — Debug separation

Debug symbols không được trở thành dependency của release linking.

---

## 493.97 — Documentation separation

Docs không được required để compile binary package.

---

## 493.98 — Incremental compilation

Interface changes invalidate only dependent queries/packages.

---

## 493.99 — Benchmark

493 phải benchmark:

- cold source import;
- warm interface import;
- generic instantiation;
- large dependency graph;
- ABI validation;
- metadata loading;
- incremental rebuild.

---

## 493.100 — Hard invariants

1. Source package khác binary package.
2. Binary package có machine-readable interface.
3. Interface khác debug info.
4. Interface khác documentation.
5. Interface không phải source.
6. Interface được sinh từ semantic database.
7. Stable SymbolId được sử dụng.
8. Stable TypeId được sử dụng.
9. Canonical type encoding được sử dụng.
10. Generic constraints được export.
11. Trait metadata được export.
12. Public impl metadata được export.
13. Coherence metadata được export khi cần.
14. Method resolution có thể thực hiện từ interface.
15. Dynamic trait metadata được export.
16. ABI-relevant layout được export.
17. Opaque types không leak private layout.
18. ABI fingerprint được hỗ trợ.
19. Semantic fingerprint được hỗ trợ.
20. API fingerprint được hỗ trợ.
21. Ba fingerprint không bị gộp.
22. Compiler compatibility được verify.
23. Metadata schema được verify.
24. Edition được record.
25. Target identity được record.
26. CPU feature requirements được record.
27. Runtime profile được record.
28. Static library có thể kèm interface.
29. Dynamic library có thể kèm interface.
30. Axiom symbol ↔ native symbol mapping deterministic.
31. Name mangling deterministic.
32. Export policy explicit.
33. Private symbols không trở thành public contract.
34. Generic instantiation từ interface được hỗ trợ.
35. Precompiled generic có cache key đầy đủ.
36. Generic instance chỉ dùng khi key match.
37. Semantic change invalidates affected generic code.
38. Compatible generic instances có thể share.
39. Specialization selection deterministic.
40. LTO boundary explicit.
41. Native-only packages được hỗ trợ.
42. Source-only packages được hỗ trợ.
43. Hybrid packages được hỗ trợ.
44. Binary fallback source được hỗ trợ.
45. Binary incompatibility không được silently ignore.
46. Interface cache được hỗ trợ.
47. Interface content-addressed.
48. Interface cache invalidation deterministic.
49. Fast binary import được hỗ trợ.
50. Lazy metadata loading được hỗ trợ.
51. Export symbol index được hỗ trợ.
52. Dependency interfaces được load lazily.
53. Transitive metadata không bị duplicate không cần thiết.
54. Interface graph được hỗ trợ.
55. ABI được validate trước linking.
56. Layout được validate.
57. Calling convention được validate.
58. Effect metadata được export.
59. Ownership metadata được export khi ABI/API yêu cầu.
60. Contract metadata được export.
61. Security metadata có thể export.
62. Target availability được export.
63. Deprecation được export.
64. Documentation links có thể dùng SymbolId.
65. Source provenance được hỗ trợ.
66. Public interface không leak private source ngoài semantic necessity.
67. Generic privacy được bảo vệ.
68. Public closure ABI phải explicit.
69. Compiler-generated public types phải stable.
70. Public API không được phụ thuộc private type trái phép.
71. Recursive representations được encode rõ.
72. Compile-time constants có metadata.
73. Comptime invocation có distribution model rõ.
74. Compiler không execute arbitrary package native code trong comptime.
75. Comptime cache được verify.
76. Interface generation deterministic.
77. Interface encoding canonical.
78. Unsupported schema phải reject rõ ràng.
79. Compatible schema evolution được hỗ trợ.
80. API/ABI/semantic/layout changes được classify riêng.
81. API diff được hỗ trợ.
82. ABI diff được hỗ trợ.
83. Semantic diff được hỗ trợ.
84. Không tạo aggregate compatibility score.
85. AI binary-interface queries được hỗ trợ.
86. Binary selection/rejection có explanation.
87. Rebuild reason machine-readable.
88. Binary cache integrity được verify.
89. Binary signatures có thể verify.
90. Binary trust policy configurable.
91. Debug symbols không required cho release linking.
92. Documentation không required cho compilation.
93. Interface changes invalidate affected queries only.
94. Import performance được benchmark.
95. Generic compilation được benchmark.
96. Large dependency graph được benchmark.
97. Metadata loading được benchmark.
98. ABI validation được benchmark.
99. Binary consumption phải nhanh hơn source reparsing khi interface hợp lệ và cache nóng.
100. **Axiom binary package phải có một interface semantic/ABI đủ mạnh để compiler, linker, IDE và AI sử dụng package mà không cần source; precompiled generic và native code được tái sử dụng khi fingerprint tương thích, còn mọi mismatch phải dẫn tới validation/rebuild rõ ràng và deterministic.**

**BOOTSTRAP-493 hoàn tất / LOCKED.**

---

# BOOTSTRAP-494 — DISTRIBUTED BUILD, REMOTE COMPILATION, REMOTE CACHE, BUILD FARM & TRUSTED ARTIFACT REUSE

494 tiếp tục trực tiếp từ 487 + 491 + 493.

Mục tiêu là cho phép Axiom scale compilation từ một laptop lên:

```text
Local Machine
     │
     ├── Local Cache
     │
     ├── Remote Cache
     │
     └── Build Workers
             │
        ┌────┼────┐
        ↓    ↓    ↓
      CPU1  CPU2  CPU3
        │    │    │
        └────┼────┘
             ↓
       Verified Artifact
             ↓
        Local Build
```

Nhưng **distributed build không được trở thành requirement**.

---

## 494.1 — Local build là baseline

Axiom phải luôn build được chỉ với local compiler/toolchain và local dependencies.

---

## 494.2 — Remote cache ≠ remote compiler

Remote cache chỉ cung cấp artifacts đã build.

---

## 494.3 — Remote compilation

Build graph có thể dispatch node tới remote worker.

---

## 494.4 — Build worker

Worker cần:

```text
compiler
target SDK
stdlib
dependencies
build environment
```

---

## 494.5 — Hermetic worker

Worker phải nhận đủ build inputs từ declared build graph.

---

## 494.6 — Build input fingerprint

Fingerprint gồm:

```text
source hash
dependency hashes
compiler build id
stdlib hash
target SDK hash
target
features
profile
environment policy
build-script inputs
```

---

## 494.7 — Environment

Undeclared environment state không được ảnh hưởng deterministic build.

---

## 494.8 — Worker selection

Worker phải đáp ứng target/CPU/compiler requirements.

---

## 494.9 — Cross compilation

Worker có thể compile target khác host.

---

## 494.10 — Artifact result

Worker trả:

```text
Artifact
ArtifactHash
BuildFingerprint
Diagnostics
Provenance
```

---

## 494.11 — Artifact verification

Client verify returned artifact hash.

---

## 494.12 — Provenance

Artifact phải record worker/compiler/toolchain provenance.

---

## 494.13 — Untrusted worker

Remote worker không nhất thiết phải được trusted.

Artifact integrity được verify.

---

## 494.14 — Reproducibility

Client có thể rebuild locally để verify result.

---

## 494.15 — Deterministic artifact

Build configuration deterministic phải produce equivalent artifact.

---

## 494.16 — Bit-identical mode

Một số target/profile có thể yêu cầu bit-for-bit reproducibility.

---

## 494.17 — Equivalent mode

Nếu platform metadata inherently varies, semantic/artifact equivalence có thể là validation target.

---

## 494.18 — Remote cache lookup

Cache lookup bằng content-addressed key.

---

## 494.19 — Cache hit

Nếu exact fingerprint match:

```text
download
→ verify
→ use
```

---

## 494.20 — Cache miss

Compiler builds normally.

---

## 494.21 — Cache corruption

Invalid artifact phải bị reject.

---

## 494.22 — Cache poisoning

Artifact signature/hash mismatch không được accept.

---

## 494.23 — Negative cache

Failed builds có thể cache diagnostics nếu fingerprint exact.

---

## 494.24 — Negative cache invalidation

Source/dependency/compiler changes invalidate failure result.

---

## 494.25 — Build graph scheduling

Independent nodes có thể dispatch parallel.

---

## 494.26 — Dependency ordering

Node chỉ execute sau khi required inputs available.

---

## 494.27 — Remote cancellation

Cancelled build phải propagate cancellation.

---

## 494.28 — Worker timeout

Timeout phải return explicit failure.

---

## 494.29 — Worker crash

Worker crash không được corrupt local build state.

---

## 494.30 — Retry

Retry policy phải deterministic enough to preserve final result.

---

## 494.31 — Duplicate execution

Same node có thể chạy trên multiple workers khi fault recovery cần.

---

## 494.32 — Artifact race

Multiple identical outputs phải verify same content/fingerprint.

---

## 494.33 — Remote logs

Remote diagnostics phải structured.

---

## 494.34 — Source privacy

Remote compilation không được upload source nếu project chọn local-only.

---

## 494.35 — Sensitive project

Project policy có thể:

```text
remote_cache = false
remote_build = false
```

---

## 494.36 — Selective remote build

Project có thể allow remote compilation chỉ cho selected packages.

---

## 494.37 — Secret isolation

Secrets không được trở thành implicit build input.

---

## 494.38 — Credential isolation

Worker không được nhận package-manager credentials unless explicitly required.

---

## 494.39 — Network isolation

Worker có thể chạy network-disabled.

---

## 494.40 — Build sandbox

Build scripts/generators chạy theo 487 sandbox policy.

---

## 494.41 — Resource limits

Worker có CPU/memory/disk/time quotas.

---

## 494.42 — Priority

Build system có thể assign priority.

---

## 494.43 — Fair scheduling

Build farm có thể enforce fairness nhưng không thay semantics.

---

## 494.44 — Target pools

Workers có thể được grouped theo:

```text
x86_64-linux
x86_64-windows
aarch64-linux
aarch64-macos
wasm
```

---

## 494.45 — SDK matching

Worker SDK hash phải match declared target SDK.

---

## 494.46 — Compiler matching

Worker compiler BuildId phải match allowed compiler.

---

## 494.47 — Stdlib matching

Stdlib identity phải match.

---

## 494.48 — Feature matching

CPU/compiler feature set phải match.

---

## 494.49 — Build profile matching

Debug/release/LTO/sanitizer/PGO configuration là fingerprint input.

---

## 494.50 — PGO

PGO-generated artifacts không được reuse nếu profile identity không match.

---

## 494.51 — Debug builds

Debug metadata generation phải remain deterministic under distributed build where target permits.

---

## 494.52 — Split artifacts

Remote worker có thể return:

```text
object
interface
debug
profile
diagnostics
```

---

## 494.53 — Incremental artifacts

493 interface artifacts integrate with remote cache.

---

## 494.54 — Thin compilation

Small package changes chỉ rebuild affected nodes.

---

## 494.55 — Dependency graph hashing

487 graph identity được dùng làm cache input.

---

## 494.56 — Remote cache namespaces

Organizations/projects có thể có isolated cache namespaces.

---

## 494.57 — Cache access control

Private cache phải enforce authorization.

---

## 494.58 — Cache retention

Artifacts có thể expire/evict.

Eviction không được thay đổi correctness.

---

## 494.59 — Cache garbage collection

CAS unreachable artifacts có thể garbage collect.

---

## 494.60 — Cache pinning

Release artifacts có thể pin.

---

## 494.61 — Cache promotion

Verified CI artifact có thể promote thành trusted cache entry.

---

## 494.62 — Trust labels

Cache entry có thể có:

```text
unverified
verified
release
```

Trust label không thay artifact hash.

---

## 494.63 — Signature

Release cache artifacts có thể signed.

---

## 494.64 — Artifact provenance

Artifact metadata liên kết:

```text
source
dependencies
compiler
worker
target
configuration
```

---

## 494.65 — Supply-chain integration

491/490 package security metadata được preserve.

---

## 494.66 — Reproducible CI

CI có thể execute same build graph on independent workers.

---

## 494.67 — Diverse rebuild

High-assurance builds có thể use independent workers/toolchains.

---

## 494.68 — Trust comparison

Artifacts from independent workers có thể compare.

---

## 494.69 — No mandatory consensus

Distributed build does not require blockchain/consensus.

---

## 494.70 — Remote execution protocol

Protocol phải có:

```text
submit
query
stream diagnostics
cancel
fetch artifact
```

---

## 494.71 — Protocol versioning

Remote build protocol version độc lập compiler language edition.

---

## 494.72 — Capability negotiation

Client/worker negotiate:

- target;
- compiler;
- SDK;
- features;
- sandbox;
- cache capabilities.

---

## 494.73 — Worker registration

Worker advertises capabilities.

---

## 494.74 — Worker identity

Worker có stable identity trong build provenance.

---

## 494.75 — Worker attestation

Platform có thể support hardware/TEE attestation.

Không bắt buộc.

---

## 494.76 — TEE

Trusted execution environment integration là optional platform layer.

---

## 494.77 — Build secrets

Secret-dependent build không được đưa secret vào artifact fingerprint unless explicitly configured.

---

## 494.78 — Secret leakage

Build output/logs must support secret redaction.

---

## 494.79 — Source upload policy

Project manifest có thể define which source roots may leave machine.

---

## 494.80 — Artifact download policy

Project có thể prohibit executable artifacts from untrusted remote sources.

---

## 494.81 — Binary/source trust

493 binary package trust policy integrates.

---

## 494.82 — Remote dependency fetch

Worker có thể consume already-resolved dependency artifacts.

Không tự resolve dependency independently.

---

## 494.83 — Lockfile authority

492 lockfile remains dependency selection authority.

---

## 494.84 — Build graph authority

487 build graph remains execution authority.

---

## 494.85 — Reproducible command

Equivalent local and remote build graphs must have same declared inputs.

---

## 494.86 — Remote cache cannot alter semantics

Cache only changes where artifact came from.

---

## 494.87 — Remote worker cannot alter semantics

Worker output must validate against expected build fingerprint.

---

## 494.88 — Diagnostics

Remote errors phải preserve source spans and semantic IDs.

---

## 494.89 — AI build query

AI có thể query:

```text
build_node_status()
cache_hit_reason()
worker()
artifact_provenance()
rebuild_reason()
```

---

## 494.90 — AI optimization

AI có thể identify:

- expensive build nodes;
- cache misses;
- serialization bottlenecks;
- dependency invalidation chains.

Không tự động thay đổi semantics.

---

## 494.91 — Build performance

494 measures:

- cache hit latency;
- remote scheduling latency;
- transfer time;
- compile time;
- worker utilization;
- incremental rebuild time.

---

## 494.92 — Artifact transfer

Large artifacts support chunking/resume from 491.

---

## 494.93 — Compression

Artifact transfer can use compression without changing artifact hash.

---

## 494.94 — Deduplication

CAS deduplicates identical objects.

---

## 494.95 — Local-first

Compiler should prefer local cache before remote fetch.

---

## 494.96 — Offline mode

Offline mode disables remote build/cache/network.

---

## 494.97 — Graceful degradation

Remote service unavailable:

```text
remote miss/failure
→ local build
```

when policy permits.

---

## 494.98 — No hidden fallback

If project explicitly forbids local build or remote build, system must not silently violate policy.

---

## 494.99 — Testing

Test:

```text
cache hit
cache miss
corrupt cache
worker crash
worker timeout
network loss
duplicate workers
ABI mismatch
SDK mismatch
source privacy
offline build
```

---

## 494.100 — Hard invariants

1. Local build luôn là baseline.
2. Remote cache khác remote compiler.
3. Remote compilation là optional.
4. Worker nhận declared inputs.
5. Hermetic worker được hỗ trợ.
6. Build fingerprint bao phủ compiler/source/dependencies/target/configuration.
7. Undeclared environment không được thay đổi deterministic build.
8. Worker capability phải match target.
9. Worker trả artifact + hash + provenance.
10. Client verify artifact.
11. Remote worker không mặc định trusted.
12. Reproducible rebuild được hỗ trợ.
13. Bit-identical mode được hỗ trợ khi khả thi.
14. Equivalent validation được hỗ trợ khi bit identity không khả thi.
15. Remote cache content-addressed.
16. Exact fingerprint là cache-hit requirement.
17. Cache miss build bình thường.
18. Corrupt cache bị reject.
19. Cache poisoning bị detect.
20. Negative cache được hỗ trợ.
21. Negative cache được invalidate đúng.
22. Build graph parallel được hỗ trợ.
23. Dependency ordering được bảo đảm.
24. Cancellation được propagate.
25. Worker timeout explicit.
26. Worker crash không corrupt build.
27. Retry không thay semantics.
28. Duplicate execution được hỗ trợ.
29. Duplicate outputs được verify.
30. Remote diagnostics structured.
31. Source privacy policy explicit.
32. Remote build có thể disable.
33. Selective remote build được hỗ trợ.
34. Secrets không implicit trở thành build inputs.
35. Credentials không gửi nếu không cần.
36. Network isolation được hỗ trợ.
37. Build scripts tuân sandbox 487.
38. Worker resource limits được hỗ trợ.
39. Worker priority không thay semantics.
40. Target pools được hỗ trợ.
41. SDK identity phải match.
42. Compiler identity phải match.
43. Stdlib identity phải match.
44. Feature identity phải match.
45. Profile identity phải match.
46. PGO artifacts phải match profile identity.
47. Debug artifacts có thể distributed.
48. Interface artifacts tích hợp 493.
49. Incremental artifacts được cache.
50. Dependency graph hash là cache input.
51. Cache namespaces được hỗ trợ.
52. Private cache authorization được hỗ trợ.
53. Cache eviction không thay correctness.
54. Cache GC được hỗ trợ.
55. Release artifacts có thể pin.
56. Verified artifacts có thể promote.
57. Trust labels không thay hash verification.
58. Artifact signatures được hỗ trợ.
59. Provenance được giữ.
60. Supply-chain metadata không bị mất.
61. Reproducible CI được hỗ trợ.
62. Independent rebuild được hỗ trợ.
63. Artifact comparison được hỗ trợ.
64. Không yêu cầu blockchain/consensus.
65. Remote protocol có submit/query/cancel/fetch.
66. Protocol version độc lập language edition.
67. Capability negotiation được hỗ trợ.
68. Worker identity được record.
69. Worker attestation optional.
70. TEE integration optional.
71. Secret-dependent builds có explicit policy.
72. Build logs hỗ trợ redaction.
73. Source upload policy explicit.
74. Artifact trust policy explicit.
75. Worker không tự resolve dependencies.
76. Lockfile 492 là dependency authority.
77. Build graph 487 là execution authority.
78. Local/remote builds có cùng declared inputs.
79. Cache không được thay semantics.
80. Worker không được thay semantics.
81. Remote diagnostics giữ source provenance.
82. AI build queries được hỗ trợ.
83. Build performance được đo.
84. Large artifacts chunked/resumable.
85. Compression không thay artifact hash.
86. CAS deduplicates identical objects.
87. Local cache được ưu tiên.
88. Offline mode được hỗ trợ.
89. Remote outage có thể fallback local theo policy.
90. Explicit policy không được bị override bởi fallback.
91. Cache hit/miss được test.
92. Worker failure được test.
93. Network failure được test.
94. ABI/SDK mismatch được test.
95. Privacy policy được test.
96. Distributed build không bắt buộc runtime application.
97. Distributed build không yêu cầu external compiler.
98. Distributed build không làm thay đổi language semantics.
99. Remote infrastructure chỉ là build acceleration/distribution layer.
100. **Axiom distributed build phải biến compilation thành một tập build nodes có fingerprint và provenance rõ ràng, cho phép local cache, remote cache và remote workers thay thế lẫn nhau mà không thay đổi semantics; khi toàn bộ remote infrastructure biến mất, project vẫn có thể build theo chính dependency/build graph đã khai báo.**

**BOOTSTRAP-494 hoàn tất / LOCKED.**

---

## TIẾN ĐỘ MỚI

```text
489  Native Distribution / Installer / Updates        LOCKED
490  Application Security / Sandbox / Capabilities   LOCKED
491  Registry / CAS / Mirrors / Offline Vendor        LOCKED
492  Dependency Resolution / Workspace / Features    LOCKED
493  Binary Interface / Precompiled Generics          LOCKED
494  Distributed Build / Remote Cache / Build Farm    LOCKED
```

**Task kế tiếp: `BOOTSTRAP-495 — PACKAGE/API COMPATIBILITY, SEMANTIC VERSIONING, ABI EVOLUTION, DEPRECATION, MIGRATION & AUTOMATED UPGRADE ENGINE`.**