# BOOTSTRAP-497 — PACKAGE SCRIPTING, BUILD SYSTEM EXTENSIONS, CODE GENERATION PIPELINE, RESOURCE COMPILERS & HERMETIC BUILD PLUGINS

**Trạng thái: COMPLETED / LOCKED**

497 chuẩn hóa tầng **build-time tooling** của Axiom. Đây là phần nằm giữa package ecosystem và compiler, dùng để xử lý những việc như:

- generate source;
- generate bindings;
- compile resource;
- convert asset;
- generate serialization/schema code;
- build native helper;
- preprocess dữ liệu;
- tạo documentation/index;
- chuẩn bị artifact trước compilation.

Điểm quan trọng: **build script không phải Axiom language runtime, không phải `comptime`, và không được trở thành một cách lách hermetic build.**

---

## 497.1 — Build script là build graph node

Mọi build script phải xuất hiện trong Build Graph 487:

```text id="j4m8x2"
Inputs
   ↓
Build Script
   ↓
Declared Outputs
```

---

## 497.2 — Build script ≠ comptime

```text id="k8p3m5"
comptime
→ compiler semantic computation

build script
→ external build-time transformation
```

---

## 497.3 — Build script ≠ runtime

Build script chạy trước application runtime.

---

## 497.4 — Build script ≠ compiler plugin

496 compiler extension có semantic access.

497 build tool chủ yếu thao tác artifact/file/resource.

---

## 497.5 — Build script package

Build script là dependency class `build`.

---

## 497.6 — Generator package

Generator có thể được phân loại riêng:

```text id="n6x2r8"
generator
```

và được gọi bởi build graph.

---

## 497.7 — Resource compiler

Resource compiler xử lý:

```text id="w3m7q1"
image
font
audio
video
shader
mesh
material
model
localization
binary data
```

---

## 497.8 — Input declaration

Build node phải khai báo input files/resources.

---

## 497.9 — Output declaration

Build script phải khai báo outputs.

---

## 497.10 — Undeclared output

Undeclared output không được trở thành implicit build input.

---

## 497.11 — Dependency discovery

Dynamic dependency discovery phải có explicit mechanism.

---

## 497.12 — Generated source

Generated `.ax` source phải được đưa vào build graph.

---

## 497.13 — Generated interface

Generator có thể tạo interface artifacts 493.

---

## 497.14 — Generated metadata

Tool có thể tạo metadata nhưng schema phải versioned.

---

## 497.15 — Resource manifest

Resource compiler output manifest:

```text id="s5q1m9"
ResourceId
type
size
hash
dependencies
compression
alignment
```

---

## 497.16 — Resource dependency graph

Resource dependencies được đưa vào graph.

---

## 497.17 — Resource compilation

Ví dụ:

```text id="t2m8x4"
source.png
   ↓
resource compiler
   ↓
texture.bin
```

---

## 497.18 — Deterministic conversion

Same input + same tool/configuration phải produce same output trong deterministic mode.

---

## 497.19 — Tool fingerprint

Build tool fingerprint:

```text id="x7p4n2"
tool package hash
tool version
compiler/build API
configuration
target
```

---

## 497.20 — Input fingerprint

Content hashes của inputs là correctness inputs.

---

## 497.21 — Configuration fingerprint

Config 470 phải được đưa vào build node identity.

---

## 497.22 — Target fingerprint

Resource compilation có thể phụ thuộc target.

---

## 497.23 — CPU feature fingerprint

Nếu resource output phụ thuộc CPU features, feature set phải là input.

---

## 497.24 — Environment

Environment variable chỉ được dùng nếu explicitly declared.

---

## 497.25 — Working directory

Working directory phải deterministic.

---

## 497.26 — Clock

Current time không được implicit input trong reproducible mode.

---

## 497.27 — Randomness

Randomness phải:

- deterministic seed; hoặc
- explicit non-reproducible input.

---

## 497.28 — Network

Network access mặc định bị cấm trong hermetic build.

---

## 497.29 — Explicit network capability

Build tool có thể request network capability.

---

## 497.30 — Filesystem

Filesystem access phải giới hạn trong declared roots.

---

## 497.31 — Process execution

Child process execution phải capability-based.

---

## 497.32 — Tool dependencies

External tools phải được khai báo:

```text id="m8x2q5"
tool = "shaderc"
```

hoặc Axiom-native tool package tương ứng.

---

## 497.33 — Toolchain identity

External tool identity phải được fingerprint.

---

## 497.34 — Native tool

Build tool có thể là native executable.

---

## 497.35 — Axiom build tool

Build tool có thể được viết bằng Axiom.

---

## 497.36 — Bootstrap requirement

Build system không được yêu cầu external compiler để build Axiom build tools nếu chúng thuộc production toolchain.

---

## 497.37 — WASM build tools

Build tool có thể chạy sandboxed WASM nếu phù hợp.

---

## 497.38 — Build plugin isolation

Plugin có thể:

```text id="q4m7n1"
trusted local process
sandboxed process
WASM sandbox
```

---

## 497.39 — Capability manifest

Tool manifest khai báo:

```text id="r9x3m5"
filesystem
network
process
environment
GPU
device
```

---

## 497.40 — Least privilege

Build tool chỉ được cấp capabilities cần thiết.

---

## 497.41 — Capability attenuation

Parent build có thể giảm quyền của child tool.

---

## 497.42 — Resource limits

Tool có thể bị giới hạn:

- CPU;
- memory;
- disk;
- process count;
- execution time;
- output size.

---

## 497.43 — Cancellation

Build cancellation phải terminate/clean tool subprocesses.

---

## 497.44 — Crash handling

Tool crash tạo structured build failure.

---

## 497.45 — Timeout

Tool timeout là explicit failure.

---

## 497.46 — Output validation

Build system verify declared outputs:

- tồn tại;
- loại đúng;
- hash;
- path policy.

---

## 497.47 — Path traversal

Tool không được ghi ngoài declared output roots.

---

## 497.48 — Symlink policy

Symlink traversal phải obey sandbox policy.

---

## 497.49 — Generated file ownership

Build directory sở hữu generated outputs.

---

## 497.50 — Source tree mutation

Build scripts không được modify source tree mặc định.

---

## 497.51 — Generated source directory

Canonical:

```text id="y7m4x2"
_workspace/generated/
```

hoặc build-directory tương đương.

---

## 497.52 — Clean build

Generated artifacts phải có thể xóa và regenerate.

---

## 497.53 — Stale output

Build graph phải detect output provenance mismatch.

---

## 497.54 — Incremental execution

Build tool chỉ rerun khi node fingerprint thay đổi.

---

## 497.55 — Cache

Outputs được content-addressed/cache theo 487.

---

## 497.56 — Remote execution

Build tools có thể chạy remote nếu capabilities cho phép.

---

## 497.57 — Remote restrictions

Remote tool phải có declared capabilities và compatible environment.

---

## 497.58 — Secret isolation

Secrets không được đưa vào cache/artifact.

---

## 497.59 — Credential access

Credential access phải explicit capability.

---

## 497.60 — Logging

Build tools phải emit structured diagnostics.

---

## 497.61 — stdout/stderr

stdout/stderr được capture và associate với build node.

---

## 497.62 — Diagnostic source

Generated-code diagnostics phải map về generator/resource input.

---

## 497.63 — Provenance

Mỗi generated artifact record:

```text id="b5x9m1"
producer
input hashes
tool hash
configuration
target
timestamp policy
```

---

## 497.64 — Timestamp policy

Deterministic mode phải normalize/remove irrelevant timestamps.

---

## 497.65 — Archive generation

Archive ordering và metadata phải deterministic.

---

## 497.66 — Compression

Compression algorithm/version/config phải fingerprint nếu output deterministic depends on it.

---

## 497.67 — Resource hashing

Resource output hash được dùng trong downstream build graph.

---

## 497.68 — Resource variants

Có thể tạo variants:

```text id="c8m2x7"
desktop
mobile
low-memory
high-quality
HDR
SDR
```

---

## 497.69 — Target-specific resources

Target conditions được tích hợp 492.

---

## 497.70 — Localization generation

464 localization catalogs có thể được generated.

---

## 497.71 — Font processing

Font subsetting/atlas generation là build-time resource processing.

---

## 497.72 — Shader processing

Shader source có thể compile thành target-specific shader artifacts.

---

## 497.73 — GPU toolchain

Shader compiler/provider phải declare target and version.

---

## 497.74 — Model processing

AI/ML model conversion có thể là resource build step.

---

## 497.75 — Audio processing

Audio conversion/normalization must preserve explicit format semantics.

---

## 497.76 — Video processing

Video transcode is resource build processing and must declare codec/tool versions.

---

## 497.77 — Database schema generation

455 schema/migration generation có thể integrate build graph.

---

## 497.78 — Network schema generation

454 protocol/schema bindings có thể be generated.

---

## 497.79 — FFI binding generation

451 SDK/header import can run as build node.

---

## 497.80 — Documentation generation

485 documentation generators are build graph nodes.

---

## 497.81 — Test generation

Generated tests are normal test graph nodes.

---

## 497.82 — Benchmark generation

Generated benchmarks must retain provenance.

---

## 497.83 — Build metadata

Build tools can emit machine-readable metadata for compiler/AI.

---

## 497.84 — AI build query

AI can query:

```text id="p7m2x8"
what generated this file?
why did this node rerun?
which input changed?
which tool version was used?
what capabilities were granted?
```

---

## 497.85 — Build explanation

`axiom build --explain` must expose generator/resource dependencies.

---

## 497.86 — Reproducibility verification

Tool can run:

```text id="v3x8m1"
generate A
generate B
compare hashes
```

---

## 497.87 — Hermetic verification

Build system can detect undeclared file/network/env access.

---

## 497.88 — Sandbox violations

Violation produces structured diagnostic.

---

## 497.89 — Build policy profiles

Suggested:

```text id="r6m2q4"
normal
hermetic
offline
reproducible
sandboxed
high-assurance
```

---

## 497.90 — Normal profile

Convenience allowed within declared project policy.

---

## 497.91 — Hermetic profile

Undeclared external dependencies prohibited.

---

## 497.92 — Offline profile

No network capability.

---

## 497.93 — Reproducible profile

Nondeterministic inputs prohibited or explicit.

---

## 497.94 — Sandboxed profile

Strict capability/resource limits.

---

## 497.95 — High-assurance profile

Can require:

- signed tools;
- pinned tool versions;
- no network;
- reproducible output;
- provenance;
- independent verification.

---

## 497.96 — Build script publishing

Build tools can be distributed through 491.

---

## 497.97 — Build tool compatibility

Tool compatibility follows 495.

---

## 497.98 — Build tool binary compatibility

Native tools follow 493/494 compatibility rules.

---

## 497.99 — Testing

497 phải test:

- deterministic generation;
- incremental rebuild;
- hermeticity;
- sandbox escape;
- malicious tool;
- output validation;
- remote execution;
- resource processing;
- generated source provenance.

---

## 497.100 — Hard invariants

1. Build script là build graph node.
2. Build script khác comptime.
3. Build script khác runtime.
4. Build script khác compiler plugin.
5. Build dependencies được phân loại.
6. Generator dependency được hỗ trợ.
7. Resource compiler được hỗ trợ.
8. Inputs phải được khai báo.
9. Outputs phải được khai báo.
10. Undeclared output không thành implicit input.
11. Dynamic dependency discovery phải explicit.
12. Generated source vào build graph.
13. Generated interface hỗ trợ 493.
14. Generated metadata versioned.
15. Resource manifest được hỗ trợ.
16. Resource dependency graph được hỗ trợ.
17. Resource compilation được hỗ trợ.
18. Deterministic conversion được hỗ trợ.
19. Tool fingerprint được sử dụng.
20. Input fingerprint được sử dụng.
21. Configuration fingerprint được sử dụng.
22. Target fingerprint được sử dụng.
23. CPU feature fingerprint được sử dụng khi cần.
24. Environment input phải explicit.
25. Working directory deterministic.
26. Clock không implicit trong reproducible mode.
27. Randomness phải explicit.
28. Network mặc định bị cấm trong hermetic mode.
29. Network capability explicit.
30. Filesystem access giới hạn theo declared roots.
31. Process execution explicit.
32. External tools được khai báo.
33. External tool identity được fingerprint.
34. Native build tools được hỗ trợ.
35. Axiom-native build tools được hỗ trợ.
36. Production build tools không bắt buộc external compiler.
37. WASM build tools được hỗ trợ khi phù hợp.
38. Build plugin có isolation modes.
39. Capability manifest được hỗ trợ.
40. Least privilege được áp dụng.
41. Capability attenuation được hỗ trợ.
42. Resource limits được hỗ trợ.
43. Cancellation được hỗ trợ.
44. Tool crash có structured failure.
45. Timeout có structured failure.
46. Output validation được thực hiện.
47. Path traversal bị ngăn chặn.
48. Symlink policy explicit.
49. Generated outputs có ownership/provenance.
50. Source tree không bị mutate mặc định.
51. Generated source có dedicated output area.
52. Clean build regenerate được toàn bộ generated outputs.
53. Stale output phải detect.
54. Incremental execution được hỗ trợ.
55. Build cache dùng 487.
56. Remote execution có thể dùng.
57. Remote capabilities phải match.
58. Secrets không vào cache/artifact.
59. Credential access explicit.
60. Structured logging được hỗ trợ.
61. stdout/stderr được associate với node.
62. Generated diagnostics giữ provenance.
63. Generated artifact có producer/input/tool metadata.
64. Deterministic timestamp policy được hỗ trợ.
65. Archive generation deterministic.
66. Compression configuration được fingerprint.
67. Resource hash đi vào graph.
68. Resource variants được hỗ trợ.
69. Target-specific resources được hỗ trợ.
70. Localization generation tích hợp 464.
71. Font processing tích hợp 464.
72. Shader processing tích hợp graphics/GPU.
73. GPU toolchain identity được verify.
74. Model processing được hỗ trợ.
75. Audio processing giữ explicit format.
76. Video processing fingerprint codec/tool.
77. Database schema generation tích hợp 455.
78. Network schema generation tích hợp 454.
79. FFI binding generation tích hợp 451.
80. Documentation generation tích hợp 485.
81. Test generation được hỗ trợ.
82. Benchmark generation giữ provenance.
83. Build metadata machine-readable.
84. AI build queries được hỗ trợ.
85. Build explanation expose generator dependencies.
86. Reproducibility verification được hỗ trợ.
87. Hermetic verification được hỗ trợ.
88. Sandbox violations có diagnostics.
89. Build policy profiles được hỗ trợ.
90. Normal mode vẫn obey explicit declarations.
91. Hermetic mode cấm undeclared dependencies.
92. Offline mode cấm network.
93. Reproducible mode cấm/record nondeterminism.
94. Sandboxed mode enforce capability/resource limits.
95. High-assurance mode có thể require signed/pinned tools.
96. Build tools được distribute qua package ecosystem.
97. Build tool compatibility dùng 495.
98. Native build tool compatibility dùng 493/494.
99. Generated artifacts không được trở thành hidden source of truth.
100. **Axiom build scripting phải là một phần minh bạch của Build Graph: mọi input, output, tool, capability và transformation đều có identity/provenance/fingerprint; build script có thể mạnh và linh hoạt nhưng không được phá incremental compilation, hermeticity, reproducibility, security hoặc compiler trust boundary.**

**BOOTSTRAP-497 hoàn tất / LOCKED.**

---

# BOOTSTRAP-498 — RESOURCE/ASSET BUILD PIPELINE, IMPORTER, PROCESSOR, COMPILER, PACKER & RUNTIME RESOURCE ABI

498 chuyên sâu vào hệ thống **asset/resource pipeline**, nối 469 + 497 + 493.

Mục tiêu là Axiom có thể xây game, GUI, multimedia, scientific/AI application mà resource processing không trở thành một hệ thống rời rạc.

```text id="j8m3x7"
Raw Asset
   ↓
Importer
   ↓
Intermediate Representation
   ↓
Processor
   ↓
Optimizer
   ↓
Resource Compiler
   ↓
Package/Bundler
   ↓
Resource Manifest
   ↓
Runtime Loader
```

---

## 498.1 — Raw asset

Input có thể là:

```text id="r4n8q2"
PNG/JPEG
WAV/FLAC
MP4
TTF/OTF
OBJ/FBX/glTF
shader
JSON/XML/YAML
CSV
model
binary
custom format
```

---

## 498.2 — Importer

Importer chuyển raw format thành canonical intermediate representation.

---

## 498.3 — Processor

Processor thay đổi semantic representation theo project requirements.

---

## 498.4 — Optimizer

Optimizer có thể:

- compress;
- quantize;
- resize;
- atlas;
- mesh optimize;
- audio resample;
- video transcode.

---

## 498.5 — Resource compiler

Compiler tạo runtime-ready resource.

---

## 498.6 — Runtime ABI

Runtime resource có stable representation được định nghĩa theo target/profile.

---

## 498.7 — Resource type identity

Mỗi resource có:

```text id="v6x2m9"
ResourceId
ResourceType
Version
```

---

## 498.8 — Content identity

Resource content hash xác định exact bytes/semantic package.

---

## 498.9 — Logical identity

Logical identity không nhất thiết bằng content hash.

Ví dụ:

```text id="m7q3x1"
res://textures/player
```

có thể trỏ tới generation mới.

---

## 498.10 — Versioned resource

Resource format có version.

---

## 498.11 — Schema evolution

Runtime loader phải biết supported resource versions.

---

## 498.12 — Importer version

Importer version là build input.

---

## 498.13 — Processor version

Processor version là build input.

---

## 498.14 — Toolchain fingerprint

Toàn resource pipeline có fingerprint.

---

## 498.15 — Intermediate representation

IR phải:

- canonical;
- versioned;
- deterministic.

---

## 498.16 — Intermediate cache

IR có thể cache giữa importer và processor.

---

## 498.17 — Incremental asset build

Chỉ asset bị ảnh hưởng mới process lại.

---

## 498.18 — Dependency tracking

Ví dụ:

```text id="f5m2x8"
material
 ├── texture
 ├── shader
 └── sampler config
```

---

## 498.19 — Asset dependency graph

Graph được đưa vào 487.

---

## 498.20 — Cycles

Asset cycles phải detect.

---

## 498.21 — Strong dependency

Runtime không thể load resource nếu dependency missing.

---

## 498.22 — Optional dependency

Optional asset dependency có thể fail gracefully nếu schema cho phép.

---

## 498.23 — Streaming resource

Large resources có thể stream.

---

## 498.24 — Chunking

Large resources support chunks.

---

## 498.25 — Compression

Compression metadata:

```text id="x7p4m1"
algorithm
version
parameters
uncompressed_size
compressed_size
```

---

## 498.26 — Integrity

Runtime verify hash when policy requires.

---

## 498.27 — Encryption

Encrypted resources có thể được hỗ trợ ở deployment/security layer.

Không coi encryption là DRM guarantee.

---

## 498.28 — Resource capability

Resource manifest có thể require:

```text id="q5m8x2"
GPU
audio
font
filesystem
network
```

---

## 498.29 — Target resource variants

Runtime/package có thể chọn variant theo target.

---

## 498.30 — Device capability variants

Ví dụ:

```text id="p3x9m5"
GPU feature level
texture compression
audio device
screen capability
```

---

## 498.31 — Quality tiers

Resource variants có thể map quality policy.

---

## 498.32 — No implicit runtime conversion

Resource conversion runtime không xảy ra nếu không explicit.

---

## 498.33 — Precompiled resource

Resource pipeline ưu tiên build-time compilation khi conversion expensive.

---

## 498.34 — Hot reload

Editor profile có thể hot reload resources.

---

## 498.35 — Generation identity

Hot reload resource generations:

```text id="n4x7m2"
ResourceId + Generation
```

---

## 498.36 — Old generation lifetime

Old resource remains alive until references release.

---

## 498.37 — Runtime thread safety

Resource handles obey 423/424 ownership/thread rules.

---

## 498.38 — Resource handle

Conceptual:

```text id="b6m1q8"
ResourceHandle<T>
```

---

## 498.39 — Strong handle

Keeps resource alive.

---

## 498.40 — Weak handle

Does not prevent unload.

---

## 498.41 — Async loading

Resource loading integrates 424/471/474.

---

## 498.42 — Cancellation

Cancelled loading must clean partial resources.

---

## 498.43 — Failure

Load failure returns `Result`.

---

## 498.44 — Resource cache

Cache policies:

```text id="m2q8x4"
LRU
LFU
size-budget
priority
pinned
streaming
```

---

## 498.45 — Memory budget

Runtime resource cache can enforce byte/object budgets.

---

## 498.46 — GPU resource

GPU resources integrate 459/460.

---

## 498.47 — Audio resource

Audio resources integrate 461.

---

## 498.48 — Video resource

Video resources integrate 462.

---

## 498.49 — Font resource

Font resources integrate 464.

---

## 498.50 — Localization resource

Localization resources integrate 464/470.

---

## 498.51 — Shader resource

Shader resource records target/backend/profile.

---

## 498.52 — Model resource

Model resource may contain:

```text id="r8m3x1"
mesh
skeleton
animation
material
morph
metadata
```

---

## 498.53 — Data resource

Arbitrary structured data can be compiled into efficient binary representation.

---

## 498.54 — Zero-copy

Runtime may memory-map resource data if:

- alignment valid;
- representation stable;
- lifetime valid;
- endian/target compatible.

---

## 498.55 — Relocatable resource

Resources requiring relocation cannot be blindly memory-mapped as immutable zero-copy data.

---

## 498.56 — Endianness

Binary resource format must define endian.

---

## 498.57 — Alignment

Resource records define required alignment.

---

## 498.58 — Schema validation

Runtime validates resource schema version.

---

## 498.59 — Resource ABI

Runtime resource ABI must distinguish:

```text id="t5x8m3"
serialized representation
runtime object representation
GPU representation
```

---

## 498.60 — Serialization

Resource file format is not automatically runtime object layout.

---

## 498.61 — Pointer prohibition

Serialized resources cannot contain process-specific raw pointers.

---

## 498.62 — Handles

Cross-resource references use IDs/offsets/indices.

---

## 498.63 — Offset validation

Offsets must be bounds-checked during load.

---

## 498.64 — Resource graph references

Cross-resource references use stable ResourceId.

---

## 498.65 — Missing dependency

Missing required dependency produces structured load error.

---

## 498.66 — Version migration

Resource format migration can run build-time.

---

## 498.67 — Runtime migration

Runtime migration should be optional and explicit.

---

## 498.68 — Build-time migration

Preferred migration path:

```text id="w6m2q8"
old asset
→ importer
→ current IR
→ current resource
```

---

## 498.69 — Resource compiler plugins

Custom resource processors use 497 plugin/build rules.

---

## 498.70 — Plugin trust

Resource processors may execute arbitrary code only within declared build trust boundary.

---

## 498.71 — Sandbox

Untrusted importers should run isolated.

---

## 498.72 — Malformed asset

Importer must treat external assets as untrusted.

---

## 498.73 — Parser security

Importers require:

- bounds checks;
- overflow checks;
- recursion/resource limits;
- decompression limits.

---

## 498.74 — Fuzzing

Importers/processors must be fuzzable.

---

## 498.75 — Determinism

Same asset/tool/config produces same deterministic output.

---

## 498.76 — Build provenance

Resource output records:

```text id="n7m4x2"
source hash
importer hash
processor hash
configuration hash
target
```

---

## 498.77 — Artifact provenance

Resource package can link back to package/build provenance 487/489.

---

## 498.78 — Resource manifest

Manifest supports:

```text id="x3m8q1"
resource
type
hash
size
alignment
dependencies
variant
compression
capabilities
```

---

## 498.79 — Resource index

Runtime can use compact index for O(1)/near-O(1) lookup.

---

## 498.80 — Lazy loading

Manifest lookup need not load resource payload.

---

## 498.81 — Prefetch

Application may request prefetch.

---

## 498.82 — Priority

Resource loading can use explicit priority.

---

## 498.83 — Streaming budget

Streaming subsystem tracks bandwidth/memory budget.

---

## 498.84 — Backpressure

Loading pipeline integrates 454/471 backpressure where appropriate.

---

## 498.85 — Resource lifetime

Loaded resources follow deterministic ownership semantics.

---

## 498.86 — No GC

Resource system does not require GC.

---

## 498.87 — No hidden thread

Resource loader does not spawn threads unless configured.

---

## 498.88 — No hidden allocation

Realtime/resource-critical paths may use preallocated pools.

---

## 498.89 — Editor/runtime separation

Editor importer stack does not need to ship in production application.

---

## 498.90 — Production stripping

Unused importers/processors/editors are removed from final artifact.

---

## 498.91 — Binary size

Resource pipeline tooling must not enlarge runtime binary.

---

## 498.92 — Platform packaging

489 can bundle resource manifest + payloads according to platform package rules.

---

## 498.93 — Update

Resource-only updates can replace resources without replacing executable where platform permits.

---

## 498.94 — Resource patch

Delta resource updates require base hash.

---

## 498.95 — Resource signing

Critical resources can be signed.

---

## 498.96 — AI metadata

AI can query:

```text id="v4m8x2"
resource_dependencies()
resource_origin()
resource_size()
resource_variant()
resource_build_reason()
```

---

## 498.97 — Build explanation

Tool explains why an asset rebuilt.

---

## 498.98 — Testing

Test:

- malformed files;
- hash mismatch;
- dependency cycle;
- version mismatch;
- cancellation;
- cache eviction;
- zero-copy;
- hot reload;
- target variants;
- corrupted package.

---

## 498.99 — Performance

Measure:

- import;
- compile;
- package;
- load;
- lookup;
- decompression;
- streaming;
- memory;
- cache hit.

---

## 498.100 — Hard invariants

1. Resource pipeline là build-time/runtime system riêng.
2. Raw asset khác compiled resource.
3. Importer tạo canonical IR.
4. Processor hoạt động trên IR.
5. Optimizer là optional build phase.
6. Resource compiler tạo runtime artifact.
7. Runtime ABI được định nghĩa rõ.
8. Resource identity khác content identity.
9. ResourceId stable.
10. Content hash xác định exact content.
11. Resource format versioned.
12. Importer version là build input.
13. Processor version là build input.
14. Toolchain fingerprint được dùng.
15. IR canonical/versioned/deterministic.
16. Intermediate cache được hỗ trợ.
17. Incremental asset build được hỗ trợ.
18. Asset dependency graph tích hợp 487.
19. Asset cycles được detect.
20. Required dependencies được phân biệt optional dependencies.
21. Streaming resource được hỗ trợ.
22. Large resource chunking được hỗ trợ.
23. Compression metadata được ghi.
24. Integrity verification được hỗ trợ.
25. Encryption có thể hỗ trợ.
26. Resource capabilities được mô tả.
27. Target variants được hỗ trợ.
28. Device variants được hỗ trợ.
29. Quality variants được hỗ trợ.
30. Runtime conversion không implicit.
31. Precompiled resources được ưu tiên.
32. Hot reload editor được hỗ trợ.
33. Resource generation identity được track.
34. Old generation lifetime an toàn.
35. Resource handles obey ownership.
36. Strong handles giữ resource sống.
37. Weak handles không giữ resource sống.
38. Async loading tích hợp concurrency.
39. Cancelled load cleanup deterministic.
40. Load failures dùng Result.
41. Cache policy explicit.
42. Memory budgets được hỗ trợ.
43. GPU resource integration được hỗ trợ.
44. Audio resource integration được hỗ trợ.
45. Video resource integration được hỗ trợ.
46. Font resource integration được hỗ trợ.
47. Localization resource integration được hỗ trợ.
48. Shader artifact target-aware.
49. Model resource format được hỗ trợ.
50. Structured data resources được hỗ trợ.
51. Zero-copy chỉ khi representation/lifetime hợp lệ.
52. Relocatable resources không giả dạng zero-copy immutable data.
53. Endianness explicit.
54. Alignment explicit.
55. Resource ABI khác serialized object layout.
56. Serialized data không chứa process raw pointers.
57. Cross-resource references dùng IDs/offsets.
58. Offset validation được yêu cầu.
59. Resource graph references stable.
60. Missing dependencies có structured errors.
61. Resource migration được hỗ trợ.
62. Build-time migration là preferred.
63. Runtime migration explicit.
64. Custom processors dùng 497.
65. Processor trust boundary explicit.
66. Untrusted importer có thể sandbox.
67. Malformed asset được coi là untrusted input.
68. Import parser phải bounds-safe.
69. Integer overflow checks được yêu cầu.
70. Recursion/resource limits được hỗ trợ.
71. Importers phải fuzzable.
72. Deterministic build được hỗ trợ.
73. Resource provenance được record.
74. Artifact provenance được preserve.
75. Resource manifest structured.
76. Resource index compact.
77. Manifest lookup không load payload bắt buộc.
78. Prefetch được hỗ trợ.
79. Loading priority explicit.
80. Streaming budgets được track.
81. Backpressure được hỗ trợ.
82. Resource lifetime deterministic.
83. Resource system không yêu cầu GC.
84. Resource loader không tự spawn thread.
85. Critical resource paths có thể allocation-free.
86. Editor tooling không ship production mặc định.
87. Unused processors được strip.
88. Resource tooling không tăng runtime binary size.
89. Platform packaging tích hợp 489.
90. Resource-only updates được hỗ trợ.
91. Resource delta update cần base hash.
92. Resource signing có thể hỗ trợ.
93. AI resource queries được hỗ trợ.
94. Build explanation expose asset provenance.
95. Malformed resource tests bắt buộc.
96. Integrity/version/dependency failures được test.
97. Hot reload/caching/zero-copy được test.
98. Target variants được test.
99. Resource performance được benchmark.
100. **Axiom resource system phải biến raw assets thành runtime-ready, versioned, verified và target-aware resources qua một pipeline incremental, deterministic và sandboxable; toàn bộ importer/editor/tooling có thể bị loại khỏi production artifact nếu không cần, để runtime chỉ mang theo resource capability thực sự được sử dụng.**

**BOOTSTRAP-498 hoàn tất / LOCKED.**

---

# TIẾN ĐỘ

```text
491  Registry / CAS / Offline Vendor                 LOCKED
492  Dependency Resolution / Workspace               LOCKED
493  Binary Interface / Precompiled Generics         LOCKED
494  Distributed Build / Remote Cache                LOCKED
495  Compatibility / Migration                       LOCKED
496  Compiler Extension / Generator                  LOCKED
497  Build Scripts / Resource Build Plugins          LOCKED
498  Resource / Asset Build Pipeline                 LOCKED
```

**Task kế tiếp: `BOOTSTRAP-499 — APPLICATION DATA MODEL, SERIALIZATION, SCHEMA EVOLUTION, REFLECTION CODEGEN & ZERO-COPY DATA INTERCHANGE`.**