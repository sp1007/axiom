# BOOTSTRAP-566 — COMPILER CACHE 3.0 — SEMANTIC INVALIDATION, CROSS-PHASE REUSE, REMOTE CACHE, CACHE TRUST, CACHE GC & ZERO-REBUILD INCREMENTAL COMPILATION

**Trạng thái: COMPLETED / LOCKED**

`BOOTSTRAP-565` đã khóa **định dạng artifact**. `566` khóa **logic quyết định reuse/invalidate artifact**, tức compiler phải biết chính xác khi nào có thể dùng lại kết quả cũ và khi nào bắt buộc phải compile lại.

Mục tiêu:

```text
Source change
    ↓
Dependency analysis
    ↓
Semantic impact
    ↓
Fine-grained invalidation
    ↓
Reuse maximal valid artifacts
    ↓
Compile only invalid region
    ↓
Validate equivalence
    ↓
Publish new artifacts
```

---

# 566.1. Cache architecture

```text
                    ┌─────────────────────┐
                    │   SOURCE / INPUTS   │
                    └──────────┬──────────┘
                               ↓
                    ┌─────────────────────┐
                    │ DEPENDENCY ANALYZER │
                    └──────────┬──────────┘
                               ↓
                    ┌─────────────────────┐
                    │ IMPACT ANALYZER     │
                    └──────────┬──────────┘
                               ↓
                 ┌─────────────┴─────────────┐
                 ↓                           ↓
          CACHE LOOKUP                    INVALIDATE
                 ↓                           ↓
          ┌─────────────┐             ┌─────────────┐
          │ LOCAL CACHE │             │ RECOMPILE    │
          └──────┬──────┘             └──────┬──────┘
                 │                           │
                 └─────────────┬─────────────┘
                               ↓
                       ARTIFACT VALIDATOR
                               ↓
                       CROSS-PHASE REUSE
                               ↓
                       NEW CACHE ARTIFACT
```

---

# 566.2. Cache không chỉ là file `.cache`

Cache là một **semantic dependency graph**.

```text
CacheGraph {
    Artifact
    Query
    Input
    Dependency
    Fingerprint
    InvalidationEdge
}
```

---

# 566.3. Cache layers

Axiom có các tầng cache:

```text
L0  Process-local
L1  Compiler-daemon memory
L2  Local artifact store
L3  Workspace cache
L4  Shared/remote cache
L5  Package/precompiled artifact
```

---

# 566.4. L0 cache

Dùng cho dữ liệu trong cùng compiler invocation.

Không cần serialize.

---

# 566.5. L1 cache

`555` daemon có thể giữ semantic/query results giữa các compilation.

---

# 566.6. L2 cache

Persistent content-addressed artifact store từ `565`.

---

# 566.7. L3 workspace cache

Cho phép chia sẻ cache giữa các invocation của cùng project.

---

# 566.8. L4 remote cache

Có thể lấy artifact từ remote store.

Remote cache không được coi là trusted mặc định.

---

# 566.9. L5 precompiled artifact

Package/library artifact có thể reuse qua nhiều project nếu compatibility thỏa mãn.

---

# 566.10. Cache key

Cache key gồm:

```text
CacheKey {
    input_identity
    dependency_identity
    semantic_environment
    compiler_semantics
    artifact_schema
    target
    ABI
    configuration
}
```

---

# 566.11. Cache key không dùng timestamp

Timestamp source không được là semantic cache key.

---

# 566.12. File identity

Source identity:

```text
SourceId {
    canonical_content_hash
    logical_path
}
```

Path chỉ cần thiết khi semantics phụ thuộc path/module identity.

---

# 566.13. Content identity

Hai source có nội dung giống nhau nhưng module identity khác nhau không nhất thiết cùng semantic identity.

---

# 566.14. Logical identity

Module/package identity được tách khỏi physical path.

---

# 566.15. Semantic fingerprint

```text
SemanticFingerprint {
    exported_symbols
    exported_types
    exported_traits
    exported_constants
    exported_effects
    exported_layouts
}
```

---

# 566.16. Implementation fingerprint

Tách khỏi public semantic fingerprint:

```text
ImplementationFingerprint {
    private_body_hash
    private_dependencies
    codegen_relevant_data
}
```

---

# 566.17. API fingerprint

API fingerprint chỉ chứa information ảnh hưởng consumer semantics.

---

# 566.18. ABI fingerprint

ABI fingerprint chỉ chứa information ảnh hưởng binary compatibility.

---

# 566.19. Layout fingerprint

Layout fingerprint dùng cho các consumer phụ thuộc memory layout.

---

# 566.20. Effect fingerprint

Effect changes phải invalidate các query phụ thuộc effect.

---

# 566.21. Trait fingerprint

Trait declarations/implementations ảnh hưởng resolution phải fingerprint.

---

# 566.22. Generic fingerprint

Generic definition và constraints phải fingerprint.

---

# 566.23. Comptime fingerprint

Inputs của `431` phải fingerprint.

---

# 566.24. Dependency edge

```text
DependencyEdge {
    producer
    consumer
    dependency_kind
    fingerprint
}
```

---

# 566.25. Dependency kinds

```text
Name
Type
Trait
Layout
Const
Comptime
Effect
ABI
Codegen
Resource
Build
Target
```

---

# 566.26. Fine-grained dependency

Compiler không được invalidate toàn module nếu chỉ một symbol không liên quan thay đổi.

---

# 566.27. Symbol-level invalidation

Ví dụ:

```text
A.foo changed
A.bar unchanged
```

consumer chỉ phụ thuộc `A.bar` không bị invalidate vì `foo`.

---

# 566.28. Type-level invalidation

Nếu type definition thay đổi nhưng layout/API không đổi, chỉ các dependency thực sự cần semantic detail mới invalid.

---

# 566.29. Layout-level invalidation

Thay đổi layout phải invalidate:

- layout consumers;
- ABI consumers;
- serialization consumers;
- native code phụ thuộc offset.

---

# 566.30. Implementation-only change

Nếu public semantic + ABI contracts không đổi:

```text
consumer semantic cache = reusable
```

---

# 566.31. Codegen invalidation

Machine code vẫn phải rebuild nếu implementation body thay đổi.

---

# 566.32. Link invalidation

Linker phải rebuild nếu:

- exported symbol changed;
- section changed;
- relocation changed;
- dependency object changed;
- link configuration changed.

---

# 566.33. Link partial reuse

Linker có thể reuse unchanged object sections khi safe.

---

# 566.34. Query cache

Mỗi compiler query có identity:

```text
QueryKey {
    query_kind
    subject
    input_snapshot
    configuration
}
```

---

# 566.35. Query result cache

```text
QueryResult {
    value
    dependencies
    fingerprint
}
```

---

# 566.36. Query validation

Cache hit chỉ hợp lệ khi tất cả dependencies vẫn valid.

---

# 566.37. Dependency closure

Compiler phải có khả năng recursively validate dependency closure.

---

# 566.38. Cycle handling

Dependency graph có thể có cycles.

Compiler phải dùng SCC/strongly-connected components khi cần.

---

# 566.39. SCC invalidation

Nếu một cycle có semantic dependency thực sự thay đổi, SCC liên quan phải re-evaluate.

---

# 566.40. No global invalidation

Cycle nhỏ không được làm invalid toàn workspace.

---

# 566.41. Snapshot

Mỗi compilation sử dụng immutable logical snapshot:

```text
CompilationSnapshot {
    source_state
    dependency_state
    config
    toolchain
}
```

---

# 566.42. Snapshot identity

Snapshot có stable fingerprint.

---

# 566.43. Snapshot isolation

Compilation đang chạy không được thấy source state thay đổi giữa chừng.

---

# 566.44. File watcher

Daemon nhận file changes từ `555`.

---

# 566.45. Change classification

File change được phân loại:

```text
Unchanged
TextChanged
SemanticallyUnchanged
APIChanged
ABIChanged
ImplementationChanged
BuildChanged
```

---

# 566.46. Semantic normalization

Whitespace/comments không được gây semantic invalidation.

---

# 566.47. Formatter invariance

Formatter chạy trên source không nên tạo compiler cache miss nếu AST semantics không đổi và policy cho phép semantic reuse.

---

# 566.48. Comment changes

Comment-only change không invalidate semantic/codegen cache.

---

# 566.49. Documentation changes

Documentation-only changes không invalidate code artifacts.

---

# 566.50. Private implementation change

Private implementation change không invalidate unrelated public semantic consumers.

---

# 566.51. Public API change

Public API change invalidate direct API consumers.

---

# 566.52. Transitive API change

Chỉ dependency closure bị ảnh hưởng mới invalidate.

---

# 566.53. Type alias change

Nếu underlying identity thay đổi, dependency rules phải phát hiện.

---

# 566.54. Constant change

Const change invalidates users that compile/use its value.

---

# 566.55. Runtime constant

Runtime-only constant change không invalidate compile-time consumers nếu semantics unchanged.

---

# 566.56. Macro/generator change

Generator implementation change invalidates generated outputs if generated result changes.

---

# 566.57. Generated-output identity

Generated artifact phải fingerprint cả generator input và output.

---

# 566.58. Build script

Build-script output là explicit cache dependency.

---

# 566.59. Environment variable

Environment variables chỉ là cache inputs khi build semantics khai báo chúng.

---

# 566.60. Undeclared environment

Undeclared environment state không được silently influence hermetic cache.

---

# 566.61. Toolchain change

Compiler/toolchain change chỉ invalidate artifacts thực sự phụ thuộc thay đổi đó.

---

# 566.62. Compiler semantic version

Semantic compiler change có thể invalidate broad artifact classes.

---

# 566.63. Compiler implementation bugfix

Bugfix không nhất thiết invalidate semantic artifacts nếu schema/semantics unchanged.

---

# 566.64. Codegen change

Backend/codegen change phải invalidate native machine artifacts.

---

# 566.65. Frontend change

Frontend semantic changes invalidate affected semantic artifacts.

---

# 566.66. Backend target change

Chỉ target artifacts bị ảnh hưởng.

---

# 566.67. Cross-target cache

`.axsem` có thể share:

```text
x86-64
AArch64
WASM
```

nếu target-independent.

---

# 566.68. Native cache

`.axobj` target-bound.

---

# 566.69. LTO cache

LTO cache phải bind target/ABI/codegen contract nếu LTO data phụ thuộc chúng.

---

# 566.70. Debug cache

Debug artifacts bind source and machine identities.

---

# 566.71. Remote cache protocol

```text
lookup(key)
fetch(artifact_id)
verify()
publish(artifact)
```

---

# 566.72. Remote lookup

Remote lookup không được làm compilation correctness phụ thuộc network.

---

# 566.73. Remote miss

Remote miss chỉ có nghĩa:

```text
not available
```

không phải error.

---

# 566.74. Remote corruption

Corrupt remote artifact là security/integrity error.

---

# 566.75. Remote trust tiers

```text
Untrusted
VerifiedHash
Signed
TrustedPublisher
```

---

# 566.76. Hash verification

Downloaded artifact phải hash-check trước use.

---

# 566.77. Signature verification

Policy có thể yêu cầu signature.

---

# 566.78. Remote cache poisoning

Một artifact có hash đúng nhưng không match requested key vẫn phải reject.

---

# 566.79. Cache key collision

Cryptographic hash collision resistance là một phần security assumption; artifact schema có thể dùng domain separation.

---

# 566.80. Domain-separated hashes

Ví dụ:

```text
H("AXIOM-SEM" || canonical_data)
H("AXIOM-OBJ" || canonical_data)
```

---

# 566.81. Cache admission

Artifact chỉ được publish sau validation.

---

# 566.82. Negative cache

Compiler có thể cache một số failure deterministic.

---

# 566.83. Negative cache safety

Failure cache phải bind đầy đủ inputs.

---

# 566.84. Diagnostics cache

Diagnostics có thể cache nhưng phải bind exact source snapshot.

---

# 566.85. Error recovery

Parser recovery artifacts không được coi là successful semantic artifacts.

---

# 566.86. Partial semantic cache

Compiler có thể reuse semantic results từ file chưa compile hoàn chỉnh nếu result contract cho phép.

---

# 566.87. Partial artifact

Artifact sections có thể independently reusable nếu dependency metadata cho phép.

---

# 566.88. Section invalidation

Cache graph có thể invalidate từng section thay vì toàn artifact.

---

# 566.89. Cross-phase reuse

Ví dụ:

```text
.axsem HIT
   ↓
.axmir HIT
   ↓
.axlto MISS
   ↓
recompute LTO
   ↓
.axobj MISS
```

Không được rebuild `.axsem/.axmir` vô ích.

---

# 566.90. Phase-local invalidation

Mỗi phase định nghĩa riêng dependency contract.

---

# 566.91. Semantic → MIR

MIR invalid nếu semantic inputs ảnh hưởng lowering thay đổi.

---

# 566.92. MIR → LTO

LTO invalid nếu MIR/function summary thay đổi.

---

# 566.93. LTO → Machine

Machine artifact invalid nếu optimization/codegen inputs thay đổi.

---

# 566.94. Machine → Object

Object invalid nếu machine bytes/relocations/debug/unwind thay đổi.

---

# 566.95. Object → Link

Link invalid nếu relevant object/link state thay đổi.

---

# 566.96. Link → Final image

Final image identity phụ thuộc linker configuration + all required inputs.

---

# 566.97. Zero-rebuild case

Nếu source change không ảnh hưởng semantic dependency của target artifact:

```text
compile = cache lookup + validation
```

có thể không cần code generation.

---

# 566.98. Zero-codegen case

Thay đổi comment/documentation có thể tạo zero-codegen rebuild.

---

# 566.99. Zero-link case

Nếu final binary unchanged và linker inputs unchanged, final image có thể reuse.

---

# 566.100. Clean-build equivalence

Incremental build phải produce semantic/binary-equivalent output theo reproducibility policy.

---

# 566.101. Cache equivalence

Cache hit result phải tương đương freshly computed result.

---

# 566.102. Parallel equivalence

Parallel cache validation phải tương đương serial validation.

---

# 566.103. Local/remote equivalence

Local và remote artifact phải produce equivalent compiler result.

---

# 566.104. Cache trace

Compiler debug mode phải có thể report:

```text
HIT
MISS
INVALIDATED
REBUILT
REUSED
```

---

# 566.105. Cache miss reason

Ví dụ:

```text
SOURCE_CHANGED
API_CHANGED
ABI_CHANGED
TARGET_CHANGED
SCHEMA_CHANGED
DEPENDENCY_CHANGED
TOOLCHAIN_CHANGED
CONFIG_CHANGED
PROFILE_CHANGED
CORRUPT
NOT_FOUND
```

---

# 566.106. Cache explainability

User/AI có thể hỏi:

```text
why was module X rebuilt?
```

Compiler phải trả dependency chain.

---

# 566.107. Invalidation explanation

Ví dụ:

```text
Foo.axsem invalid
 └── Bar<T> changed
      └── layout fingerprint changed
           └── Foo depends on layout
```

---

# 566.108. AI cache interface

AI có thể query:

```text
cache why <artifact>
cache deps <artifact>
cache impact <file>
cache status
```

---

# 566.109. Impact analysis

Compiler có thể dự đoán affected artifacts trước compilation.

---

# 566.110. Reverse dependency graph

Cache graph phải support:

```text
producer → consumers
```

để invalidation nhanh.

---

# 566.111. Forward dependency graph

Cũng phải support:

```text
artifact → dependencies
```

để validation.

---

# 566.112. Dependency graph persistence

Graph metadata có thể persist trong cache.

---

# 566.113. Graph rebuild

Xóa graph cache không được phá correctness; compiler phải reconstruct được.

---

# 566.114. Cache graph consistency

Graph entries phải reference existing artifact IDs hoặc explicit stale state.

---

# 566.115. Artifact garbage collection

Artifact GC phải xét:

- reachability;
- active leases;
- pinned artifacts;
- package references;
- remote synchronization policy.

---

# 566.116. Root artifacts

Roots:

```text
active build
installed package
pinned release
current workspace
```

---

# 566.117. Cache generations

Có thể sử dụng generation numbers để hỗ trợ efficient GC.

---

# 566.118. Concurrent GC

GC storage không được xóa artifact đang được compilation sử dụng.

---

# 566.119. Artifact lease

```text
Lease {
    artifact_id
    process_id
    expiration
}
```

---

# 566.120. Lease failure

Nếu process crash, lease phải tự expire hoặc được cleanup.

---

# 566.121. Disk quotas

Cache có quota.

---

# 566.122. Quota pressure

Eviction ưu tiên artifact dễ rebuild trước artifact expensive-to-rebuild.

---

# 566.123. Cost metadata

Artifact có thể record:

```text
build_cost
size
reuse_frequency
```

---

# 566.124. Cache eviction

Eviction không được coi là invalidation.

---

# 566.125. Cache warmup

Compiler có thể prefetch likely-needed artifacts.

---

# 566.126. Prefetch correctness

Prefetch không được làm compilation semantics phụ thuộc prediction.

---

# 566.127. Remote prefetch

Có thể tải artifact song song.

---

# 566.128. Bandwidth budget

Remote cache phải có bandwidth policy.

---

# 566.129. Local-first

Mặc định:

```text
L0 → L1 → L2 → L3 → L4
```

---

# 566.130. Remote-first

Có thể cấu hình remote-first trong CI.

---

# 566.131. Cache upload

Upload chỉ sau local validation.

---

# 566.132. Cache upload privacy

Artifact chứa private source metadata không được upload nếu policy cấm.

---

# 566.133. Cache namespace

Remote cache phải namespace theo:

```text
organization/project/toolchain/policy
```

theo deployment policy.

---

# 566.134. Cache authorization

Remote backend tự quản lý access control; compiler không giả định mọi remote artifact public.

---

# 566.135. Public artifact

Package artifacts có thể được public distribution.

---

# 566.136. Private artifact

Workspace/internal artifacts có thể được encrypted hoặc access-controlled ở storage layer.

---

# 566.137. Artifact portability

Semantic artifacts phải portable nếu target-independent.

---

# 566.138. Native portability

Native artifacts chỉ portable khi target/ABI contract match.

---

# 566.139. SDK fingerprint

iOS/Android/OS SDK-dependent artifacts phải bind SDK fingerprint.

---

# 566.140. Sysroot fingerprint

Sysroot-dependent artifacts phải bind sysroot identity.

---

# 566.141. Linker version

Linker semantics relevant tới output phải bind linker build identity.

---

# 566.142. Object writer

Object format changes phải invalidate affected object artifacts.

---

# 566.143. Machine encoder

Encoder changes có thể invalidate machine artifacts.

---

# 566.144. ISA table changes

ISA backend changes phải invalidate target-specific codegen artifacts khi relevant.

---

# 566.145. CPU feature changes

Changing CPU baseline invalidates affected native variants.

---

# 566.146. Security flags

Hardening changes invalidate native artifacts.

---

# 566.147. Signing

Signature metadata không nên làm thay đổi underlying unsigned artifact identity.

---

# 566.148. Signed cache

Signed artifact cache có thể wrap immutable unsigned content identity.

---

# 566.149. Debug mode

Changing debug configuration invalidates debug artifacts, nhưng không nhất thiết semantic artifacts.

---

# 566.150. Optimization mode

Changing optimization level invalidates affected LTO/machine artifacts.

---

# 566.151. PGO

PGO profile change invalidates PGO-dependent artifacts.

---

# 566.152. Sanitizer

Sanitizer configuration change invalidates affected machine/runtime artifacts.

---

# 566.153. Coverage

Coverage instrumentation change invalidates machine artifacts but not necessarily semantic artifacts.

---

# 566.154. Profiling

Profiling instrumentation follows same phase-specific invalidation.

---

# 566.155. ABI mode

Changing calling convention invalidates ABI consumers.

---

# 566.156. Runtime mode

Freestanding vs hosted runtime change invalidates runtime/link artifacts.

---

# 566.157. Feature gates

Language feature gate changes must enter semantic cache identity.

---

# 566.158. Edition

Language edition is part of semantic environment.

---

# 566.159. Package lock

Lockfile changes invalidate dependency-dependent artifacts.

---

# 566.160. Dependency version

Changing dependency version invalidates only dependent closure.

---

# 566.161. Dependency semantic hash

Package version alone is insufficient when content differs.

---

# 566.162. Dependency content

Actual dependency artifact identity must be checked.

---

# 566.163. Registry metadata

Registry index changes do not invalidate already-resolved exact package artifacts.

---

# 566.164. Build graph

`487` build graph and `566` cache graph must integrate.

---

# 566.165. Query graph

`559/560` query dependency graph feeds cache invalidation.

---

# 566.166. Semantic DB

`557` immutable semantic structures can be directly reused.

---

# 566.167. Artifact mmap

`565` mmap-able sections can become zero-copy query inputs.

---

# 566.168. Incremental parser

`556` can reuse unchanged token/AST regions where safe.

---

# 566.169. Incremental name resolution

Unchanged namespaces should not be recomputed.

---

# 566.170. Incremental type checking

Only impacted type-check queries rerun.

---

# 566.171. Incremental trait solving

Only impacted trait goals rerun.

---

# 566.172. Incremental ownership analysis

Only affected ownership queries rerun.

---

# 566.173. Incremental const evaluation

Only affected const/comptime queries rerun.

---

# 566.174. Incremental layout

Only changed types and dependent layouts rerun.

---

# 566.175. Incremental MIR

Only affected functions/MIR regions regenerate.

---

# 566.176. Incremental optimization

Only affected functions or SCCs rerun where legal.

---

# 566.177. Incremental codegen

Only changed machine functions regenerate.

---

# 566.178. Incremental linking

Only changed link units/layout-dependent regions require work.

---

# 566.179. Final image identity

Final artifact can be reused if all final inputs and linker state match.

---

# 566.180. Cache correctness oracle

Testing framework phải có clean-build oracle:

```text
clean(source)
incremental(source)
```

và compare outputs.

---

# 566.181. Differential cache testing

Random source mutations phải compare:

```text
clean result
vs
incremental result
```

---

# 566.182. Mutation classes

Test mutations:

- whitespace;
- comments;
- local body;
- public API;
- type;
- layout;
- trait;
- generic;
- const;
- dependency;
- build config;
- target.

---

# 566.183. Cache fuzzing

Cache graph phải được fuzz với:

- cycles;
- missing nodes;
- corrupt fingerprints;
- duplicate edges;
- stale artifacts.

---

# 566.184. Remote fuzzing

Remote responses được coi là hostile input.

---

# 566.185. Cache protocol fuzzing

Lookup/fetch/publish phải chịu malformed responses.

---

# 566.186. Race testing

Test:

```text
two compilers
same artifact
same workspace
same remote cache
```

---

# 566.187. Crash testing

Compiler bị kill trong:

- artifact write;
- cache publish;
- remote download;
- graph update.

Sau restart phải recover.

---

# 566.188. Power-loss testing

Cache phải chịu partial filesystem writes.

---

# 566.189. Deterministic cache graph

Graph serialization phải deterministic.

---

# 566.190. Deterministic invalidation

Cùng inputs phải produce cùng invalidation set.

---

# 566.191. Cache statistics

Compiler có thể report:

```text
hit rate
miss rate
invalidations
rebuild time
bytes reused
bytes downloaded
```

---

# 566.192. Statistics isolation

Statistics không được ảnh hưởng artifact identity.

---

# 566.193. Cache performance

Cache lookup phải có indexed path, không scan toàn cache.

---

# 566.194. Large workspace

Cache graph phải scale tới millions of artifacts/queries.

---

# 566.195. Memory boundedness

Daemon không được giữ toàn bộ cache graph/materialized artifacts bắt buộc trong RAM.

---

# 566.196. Lazy graph loading

Graph có thể load partitions on demand.

---

# 566.197. Persistent indexes

Các index quan trọng có thể persist.

---

# 566.198. Rebuildable indexes

Index corruption phải rebuild được từ authoritative artifact metadata.

---

# 566.199. Ultimate cache principle

Cache chỉ là optimization:

```text
Correctness(source)
    ==
Correctness(source + any valid cache)
```

---

# 566.200. HARD INVARIANTS

1. Cache không phải semantic authority.
2. Cache hit phải equivalent clean computation.
3. Cache miss không được làm thay đổi semantics.
4. Xóa cache không được làm thay đổi semantics.
5. Remote cache không được cần thiết cho correctness.
6. Local cache và remote cache phải equivalent.
7. Cache key phải chứa mọi semantic input liên quan.
8. Cache key không chứa volatile input không liên quan.
9. Timestamp không phải semantic input mặc định.
10. Host path không phải semantic input mặc định.
11. Comment-only change không invalidate semantics.
12. Whitespace-only change không invalidate semantics.
13. Documentation-only change không invalidate code.
14. Implementation change không invalidate unrelated API consumers.
15. API change invalidate direct consumers.
16. Transitive invalidation phải follow dependency graph.
17. ABI change invalidate ABI consumers.
18. Layout change invalidate layout consumers.
19. Trait change invalidate affected trait queries.
20. Const change invalidate value consumers.
21. Comptime change invalidate affected outputs.
22. Generic change invalidate affected instantiations.
23. Build-script output là explicit dependency.
24. External tool output là explicit dependency.
25. Environment dependency phải explicit.
26. Undeclared environment không được silently influence hermetic builds.
27. Compiler semantic version phải participate when semantics change.
28. Backend change phải invalidate affected machine artifacts.
29. ISA change phải invalidate affected target codegen.
30. CPU feature change phải invalidate affected native variants.
31. ABI change phải invalidate affected native artifacts.
32. SDK change phải invalidate SDK-dependent artifacts.
33. Sysroot change phải invalidate sysroot-dependent artifacts.
34. Runtime change phải invalidate runtime-dependent artifacts.
35. Optimization change phải invalidate affected optimization artifacts.
36. PGO change phải invalidate PGO artifacts.
37. Sanitizer change phải invalidate sanitizer artifacts.
38. Debug configuration only invalidates relevant debug artifacts.
39. Coverage configuration invalidates instrumentation artifacts.
40. Security policy change invalidates affected binaries.
41. Target-independent semantic artifacts may cross targets.
42. Target-specific machine artifacts may not cross targets.
43. Wrong-target artifact must be rejected.
44. Wrong-ABI artifact must be rejected.
45. Wrong-schema artifact must be rejected.
46. Wrong-dependency artifact must be rejected.
47. Corrupt artifact must be rejected.
48. Hash mismatch must never be ignored.
49. Signature mismatch must follow trust policy.
50. Remote artifact must be validated before semantic use.
51. Remote cache failure must degrade to local compilation.
52. Network availability must not determine correctness.
53. Cache publication must be atomic.
54. Partial cache entries must never be valid.
55. Immutable artifact entries must not be modified in place.
56. Cache graph mutation must be crash-safe.
57. Artifact GC must not delete active artifacts.
58. Artifact eviction must not be semantic invalidation.
59. Cache GC must preserve pinned artifacts.
60. Cache GC must preserve active leases.
61. Cache graph must distinguish missing from invalid.
62. Cache graph must distinguish stale from invalid.
63. Cache graph must distinguish miss from corruption.
64. Query cache must validate dependencies.
65. Query results must bind to snapshots.
66. Snapshot identity must be deterministic.
67. Compilation must operate on a coherent snapshot.
68. File changes during compilation must not alter snapshot semantics.
69. Reverse dependency graph must support invalidation.
70. Forward dependency graph must support validation.
71. Dependency edges must identify dependency kind.
72. Dependency fingerprints must be deterministic.
73. Symbol-level dependency must be supported.
74. Type-level dependency must be supported.
75. Layout-level dependency must be supported.
76. Trait-level dependency must be supported.
77. Effect-level dependency must be supported.
78. ABI-level dependency must be supported.
79. Codegen-level dependency must be supported.
80. Resource dependency must be explicit.
81. Build dependency must be explicit.
82. Target dependency must be explicit.
83. Cyclic dependency handling must be deterministic.
84. SCC invalidation must not become global invalidation.
85. Fine-grained invalidation must be preferred.
86. Unrelated modules must not rebuild.
87. Unrelated functions must not rebuild.
88. Unrelated generic instantiations must not rebuild.
89. Unrelated codegen must not rebuild.
90. Unrelated linking must not rebuild.
91. `.axsem` reuse must be possible independently.
92. `.axmir` reuse must be possible independently.
93. `.axlto` reuse must be possible independently.
94. `.axobj` reuse must be possible independently.
95. `.axdbg` reuse must be possible independently.
96. Cross-phase cache dependencies must be explicit.
97. A phase must not assume hidden cache dependencies.
98. Cache results must be reproducible.
99. Cache graph must be reproducible.
100. Invalidation must be reproducible.
101. Clean build and incremental build must agree.
102. Serial and parallel builds must agree.
103. Local and remote cache builds must agree.
104. Cold and warm cache builds must agree.
105. Different cache eviction patterns must not alter semantics.
106. Different cache lookup order must not alter semantics.
107. Different worker scheduling must not alter semantics.
108. Cache statistics must not affect results.
109. Prefetch must not affect results.
110. Cache admission must occur after validation.
111. Cache publication must occur only after successful validation.
112. Negative cache entries must bind exact inputs.
113. Diagnostic cache entries must bind source snapshot.
114. Error recovery state must not masquerade as successful compilation.
115. Partial semantic reuse must have explicit validity contract.
116. Partial section reuse must have explicit dependency contract.
117. Mmap reuse must preserve semantics.
118. Buffered reuse must preserve semantics.
119. Lazy loading must preserve semantics.
120. Eager loading must preserve semantics.
121. Cache representation must not expose process pointers.
122. Cache graph must not depend on process addresses.
123. Cache identity must not depend on allocator layout.
124. Cache identity must not depend on worker count.
125. Cache identity must not depend on thread scheduling.
126. Cache identity must not depend on filesystem inode.
127. Cache identity must not depend on temporary filename.
128. Cache identity must not depend on wall-clock time.
129. Cache identity must not depend on network route.
130. Cache identity must not depend on cache location.
131. Artifact identity must remain stable across stores.
132. Remote fetch must preserve artifact identity.
133. Package extraction must preserve artifact identity.
134. Artifact conversion must record provenance.
135. Migration must not mutate source artifact.
136. Migration must preserve semantic meaning.
137. Cache schema migration must be explicit.
138. Schema incompatibility must produce diagnostic.
139. Compiler must explain cache misses.
140. Compiler must explain invalidations.
141. Compiler must expose dependency paths.
142. AI must be able to query cache state.
143. AI must be able to query invalidation reason.
144. AI must be able to query affected artifacts.
145. AI must be able to query dependency closure.
146. AI must not override compiler cache decisions.
147. AI metadata must not override semantic dependencies.
148. Cache graph must derive from compiler dependency facts.
149. Cache graph corruption must be recoverable.
150. Persistent index corruption must be recoverable.
151. Cache database corruption must not corrupt source.
152. Cache corruption must trigger rebuild/recovery.
153. Cache storage failure must not corrupt compilation state.
154. Remote cache poisoning must be detectable.
155. Remote cache namespace collisions must be prevented.
156. Artifact hash must use domain separation where required.
157. Trust levels must be explicit.
158. Untrusted artifacts must remain isolated until validated.
159. Signed artifacts still require structural validation.
160. Signature does not prove compiler semantic correctness.
161. Correctness evidence must bind exact artifact identity.
162. Optimization evidence must bind exact input/output identity.
163. PGO profile identity must be explicit.
164. Security policy identity must be explicit.
165. ABI identity must be explicit.
166. Target identity must be explicit.
167. Toolchain identity must be explicit.
168. SDK identity must be explicit.
169. Sysroot identity must be explicit.
170. Runtime identity must be explicit.
171. Stdlib identity must be explicit.
172. Package lock identity must be explicit.
173. Language edition must be explicit.
174. Feature gates must be explicit.
175. Configuration must be explicit.
176. Generated source identity must be explicit.
177. Comptime input identity must be explicit.
178. Build-script input identity must be explicit.
179. Foreign artifact identity must be explicit.
180. Final image reuse must verify all linker-relevant inputs.
181. Final image reuse must verify linker configuration.
182. Final image reuse must verify security configuration.
183. Final image reuse must verify target/ABI.
184. Linker cache must not silently reuse stale objects.
185. Machine cache must not silently reuse stale code.
186. LTO cache must not silently reuse stale summaries.
187. MIR cache must not silently reuse stale semantics.
188. Semantic cache must not silently reuse stale declarations.
189. Query cache must not silently reuse stale dependency results.
190. Cache hit must not bypass required validation.
191. Cache validation must be cheaper than recomputation for normal cases.
192. Cache lookup must scale to large projects.
193. Cache memory usage must be bounded.
194. Artifact graph loading must support lazy operation.
195. Concurrent compilers must safely share immutable artifacts.
196. Crash recovery must preserve valid previous artifacts.
197. Incremental compilation must be testable against clean compilation.
198. Cache correctness must be fuzz-tested and differential-tested.
199. The entire cache system must integrate `555–565` without creating a second semantic authority.
200. **Final invariant:** Axiom phải đạt được **maximal safe reuse** — thay đổi source chỉ rebuild đúng phần chịu ảnh hưởng; mọi cache hit phải tương đương clean build; local/remote/cache-warm/cache-cold/parallel/serial/self-hosted compilation phải bảo toàn semantics và correctness, trong khi cache có thể bị xóa hoàn toàn bất kỳ lúc nào mà compiler vẫn tạo được cùng kết quả từ authoritative inputs.

**BOOTSTRAP-566: LOCKED.**

---

# NEXT — BOOTSTRAP-567

## COMPILER DISTRIBUTED BUILD 2.0 — REMOTE EXECUTION, CONTENT-ADDRESSED WORKERS, HERMETIC ACTIONS, REMOTE ARTIFACT TRANSFER, SCHEDULING & TRUSTED PARALLEL BUILD

`566` đã giải quyết **cache reuse**. Bước tiếp theo là biến dependency/cache graph thành một **distributed compilation engine** thực sự.

Kiến trúc sẽ khóa:

```text
                         AXIOM DAEMON
                              │
                     Build / Query DAG
                              │
             ┌────────────────┼────────────────┐
             │                │                │
             ▼                ▼                ▼
         Worker A          Worker B          Worker C
         Frontend          MIR/LTO           Codegen
             │                │                │
             └────────────────┼────────────────┘
                              ▼
                       Content Store
                       /           \
                 Local Cache     Remote Cache
                              │
                              ▼
                           Linker
                              │
                              ▼
                       Native Artifact
```

`567` sẽ tập trung vào **remote execution nhưng vẫn giữ nguyên nguyên tắc quan trọng của Axiom**:

> Distributed build chỉ là cách thực thi nhanh hơn; chạy compiler trên 1 máy, nhiều core, nhiều máy hoặc hoàn toàn offline phải cho cùng kết quả. Worker không được có “quyền” thay đổi semantics của chương trình.