# BOOTSTRAP-554 — COMPILER CACHE 3.0, SEMANTIC INCREMENTALITY, PRECOMPILED MODULES, GENERIC INSTANCE CACHE & CROSS-PROJECT ARTIFACT REUSE

**Trạng thái: COMPLETED / LOCKED**

`554` hoàn thiện lớp cache/incremental compilation của Axiom. `487` đã định nghĩa build graph; `553` định nghĩa optimization cache. Task này biến chúng thành **một semantic cache system thống nhất**, bảo đảm build nhanh mà không hy sinh correctness.

Nguyên tắc tối cao:

> **Cache là một optimization của compiler, không bao giờ là nguồn chân lý của semantics. Cache hit phải tương đương với việc tính toán lại từ source sạch.**

---

## 554.1. Kiến trúc tổng thể

```text
                    SOURCE TREE
                        │
                        ▼
                Content / Semantic Hash
                        │
             ┌──────────┴──────────┐
             ▼                     ▼
       Module Interface       Implementation
             │                     │
             ▼                     ▼
       Interface Cache          HIR Cache
             │                     │
             └──────────┬──────────┘
                        ▼
                   Type / Trait
                      Cache
                        │
                        ▼
                      MIR
                        │
          ┌─────────────┼─────────────┐
          ▼             ▼             ▼
      Generic        Analysis       Profile
      Instance        Cache          Cache
          │             │             │
          └─────────────┼─────────────┘
                        ▼
                   Optimization
                      Cache
                        │
                        ▼
                    Codegen Cache
                        │
                        ▼
                    Object Cache
                        │
                        ▼
                  Link / Artifact
```

---

# 554.2. Cache hierarchy

Axiom có các tầng:

```text
L0 — in-memory query cache
L1 — project-local cache
L2 — user/global cache
L3 — trusted remote cache
```

Không bắt buộc phải có L2/L3.

---

# 554.3. Query cache

Compiler query system từ `436` là nền tảng.

Ví dụ:

```text
parse(FileId)
resolve(ModuleId)
typecheck(FunctionId)
lower_mir(FunctionId)
analyze_alias(FunctionId)
optimize(FunctionId)
codegen(FunctionId)
```

Mỗi query có fingerprint.

---

# 554.4. Content hash

Source identity không dựa vào:

```text
mtime
filename
filesystem timestamp
```

mà dựa trên content hash.

---

# 554.5. Semantic hash

Ngoài source hash:

```text
SourceHash
```

Axiom có:

```text
SemanticHash
```

đại diện cho semantics sau parsing/name resolution/type resolution phù hợp.

---

# 554.6. Tại sao cần semantic hash?

Hai source khác nhau:

```text
fn f() {
    return 1
}
```

và:

```text
fn f() {
    // comment
    return 1
}
```

có thể có:

```text
SourceHash !=
SemanticHash ==
```

nếu comment không thuộc semantics.

---

# 554.7. Formatting independence

Thay đổi:

- whitespace;
- comments;
- formatting;

không nên invalidate semantic artifacts.

---

# 554.8. Source mapping vẫn riêng

Dù semantic hash giống nhau, debug/source mapping có thể thay đổi.

Do đó:

```text
SemanticCache
```

và:

```text
DebugMetadataCache
```

là hai dependency khác nhau.

---

# 554.9. Cache key chuẩn

```text
CacheKey {
    artifact_kind
    semantic_inputs
    compiler_build_id
    language_edition
    target
    target_features
    abi
    optimization_policy
    security_policy
    numeric_policy
    dependency_fingerprint
}
```

---

# 554.10. Cache artifact identity

Mỗi artifact:

```text
ArtifactIdentity {
    kind
    content_hash
    semantic_hash
    schema_version
    producer
}
```

---

# 554.11. Producer identity

Producer gồm:

```text
compiler_build_id
pass_pipeline_hash
backend_version
object_format_version
```

---

# 554.12. Semantic dependency graph

Compiler duy trì:

```text
A → B
```

nghĩa là semantic result của A phụ thuộc B.

Ví dụ:

```text
foo() → Vec2
```

thay đổi implementation của `Vec2` không nhất thiết invalidate caller nếu public semantic interface không đổi.

---

# 554.13. Declaration fingerprint

Mỗi declaration có fingerprint:

```text
DeclFingerprint {
    symbol_id
    signature
    generic_parameters
    trait_constraints
    visibility
    layout_relevance
    ABI_relevance
}
```

---

# 554.14. Interface fingerprint

Module interface:

```text
InterfaceFingerprint
```

bao gồm những gì consumer cần biết:

- public symbols;
- signatures;
- public types;
- traits;
- constants;
- ABI;
- layouts;
- effects;
- generic contracts.

---

# 554.15. Implementation fingerprint

Implementation fingerprint chứa private body information.

Thay đổi private implementation không nhất thiết invalidate consumer.

---

# 554.16. Interface vs implementation

```text
Public Interface
      │
      ├── consumer dependency
      │
Private Implementation
      │
      └── local dependency
```

Đây là nền tảng của incremental compilation.

---

# 554.17. Function-level invalidation

Nếu:

```text
fn A() {}
fn B() {}
fn C() {}
```

chỉ A thay đổi và B/C không phụ thuộc semantic vào A:

```text
A → rebuild
B → cache hit
C → cache hit
```

---

# 554.18. Call dependency

Nếu:

```text
B() calls A()
```

thay đổi body A:

```text
A body cache invalidated
B semantic cache có thể giữ nguyên
B optimization/codegen có thể invalidate tùy optimization dependency
```

---

# 554.19. Why codegen may invalidate

Nếu compiler inline A vào B:

```text
B machine code
    ↓
contains A implementation
```

thay đổi A có thể invalidate B codegen.

---

# 554.20. Inline dependency fingerprint

Artifact ghi:

```text
InliningDependency {
    callee
    semantic_hash
    selected_body_hash
}
```

---

# 554.21. No unnecessary invalidation

Compiler không được đơn giản hóa thành:

```text
source changed
→ rebuild everything
```

nếu dependency graph có đủ thông tin để tránh.

---

# 554.22. Necessary invalidation

Ngược lại, compiler không được giữ cache chỉ vì:

```text
symbol name unchanged
```

nếu ABI/layout/semantic assumptions đã thay đổi.

---

# 554.23. Type fingerprint

Type identity cache:

```text
TypeFingerprint {
    nominal_id
    generic_args
    layout_hash
    trait_impl_hash
    semantic_hash
}
```

---

# 554.24. Layout fingerprint

Thay đổi:

```text
struct S {
    a: i32
}
```

thành:

```text
struct S {
    a: i32
    b: i32
}
```

phải invalidate mọi artifact phụ thuộc layout.

---

# 554.25. ABI fingerprint

ABI changes invalidate:

```text
call lowering
function pointers
FFI
object code
link compatibility
```

---

# 554.26. Trait fingerprint

Thay đổi trait requirement/default method/associated type có thể invalidate generic consumers.

---

# 554.27. Generic dependency graph

```text
generic function
       │
       ├── Type A
       ├── Trait X
       └── Const N
```

instance cache key phải bao gồm tất cả semantic inputs.

---

# 554.28. Generic instance cache

Ví dụ:

```text
sum::<i32>
```

đã compile:

```text
GenericInstanceCache[
    sum
    i32
]
```

thì project khác có thể reuse nếu artifact trusted và compatible.

---

# 554.29. Generic cache key

```text
GenericInstanceKey {
    generic_symbol
    generic_body_hash
    type_arguments
    const_arguments
    trait_resolution_hash
    layout_hash
    abi
    target
    features
}
```

---

# 554.30. Generic code sharing

Compiler có thể reuse:

```text
same semantic instance
```

thay vì instantiate lại.

---

# 554.31. Generic specialization dependency

Nếu specialization policy thay đổi:

```text
-O2 → -O3
```

không được reuse specialized code như thể hai policy giống nhau.

---

# 554.32. Monomorphization cache

Pipeline:

```text
Generic Definition
      ↓
Substitution
      ↓
Trait Resolution
      ↓
Concrete MIR
      ↓
Cache
```

---

# 554.33. Trait solver cache

Trait solving:

```text
implements(T, Trait)
```

cũng cache được.

Key phải bao gồm solver/compiler semantics version.

---

# 554.34. Const generic cache

Ví dụ:

```text
Matrix<f32, 4, 4>
```

`4,4` là semantic cache inputs.

---

# 554.35. Comptime cache

`431` đã định nghĩa comptime cache.

`554` thống nhất storage/invalidation nhưng không thay đổi semantics của comptime.

---

# 554.36. Comptime cache key

Bao gồm:

```text
comptime function hash
arguments
target
compiler
edition
relevant environment
```

---

# 554.37. No ambient environment dependency

Comptime không được cache dựa trên environment ngầm.

Nếu external build input cần thiết, phải trở thành explicit build dependency.

---

# 554.38. Module interface cache

Precompiled module:

```text
.axmi
```

được định nghĩa ở mức semantic interface.

Tên extension chỉ là specification convention; implementation có thể thay đổi.

---

# 554.39. Module artifact contents

Module artifact có thể chứa:

```text
metadata
public semantic graph
type information
trait information
generic definitions
ABI information
debug references
dependency fingerprints
```

---

# 554.40. Module artifact không nhất thiết chứa machine code

Semantic module và native object là hai tầng độc lập.

---

# 554.41. Precompiled native module

Một package có thể cung cấp:

```text
interface metadata
+
native object
```

để consumer không cần compile source.

---

# 554.42. Binary compatibility

Native artifact phải declare:

```text
ABI
target
CPU features
compiler/runtime contract
stdlib ABI
```

---

# 554.43. ABI mismatch

Nếu:

```text
consumer ABI != artifact ABI
```

thì:

```text
cache miss / incompatible artifact
```

không được silently reinterpret.

---

# 554.44. Target fingerprint

Target fingerprint bao gồm:

```text
architecture
OS
ABI
object format
endianness
pointer width
CPU features
sysroot
SDK
```

---

# 554.45. Sysroot fingerprint

Nếu native APIs/frameworks thay đổi:

```text
sysroot_hash
sdk_hash
framework_hash
```

phải được xem xét trong artifact compatibility.

---

# 554.46. Standard library fingerprint

Artifact phụ thuộc stdlib phải record stdlib semantic/ABI fingerprint.

---

# 554.47. Runtime fingerprint

Nếu runtime ABI được link statically hoặc artifact phụ thuộc runtime symbols, runtime version/hash phải được fingerprint.

---

# 554.48. Cross-project reuse

Project A compile:

```text
Vec<T>
```

Project B có thể reuse artifact nếu:

```text
semantic compatibility
ABI compatibility
target compatibility
policy compatibility
```

được chứng minh.

---

# 554.49. Cache scope

```text
Project-local
User-global
Organization
Remote
```

là các scope khác nhau.

---

# 554.50. Trusted remote cache

Remote cache chỉ được sử dụng nếu:

```text
artifact hash verified
producer verified
policy permits
```

---

# 554.51. Cache poisoning

Không trust artifact chỉ vì server trả về.

Pipeline:

```text
Remote
 ↓
Hash verification
 ↓
Signature/provenance
 ↓
Compatibility validation
 ↓
Artifact verifier
 ↓
Accept
```

---

# 554.52. Malformed cache artifact

Cache artifact hỏng phải:

```text
reject
quarantine
record diagnostic
```

không crash compiler.

---

# 554.53. Cache ≠ source of truth

Nếu cache bị mất:

```text
clean rebuild
```

phải tạo artifact tương đương.

---

# 554.54. Cache corruption recovery

Cache corruption không được làm project không thể build nếu source/dependencies còn đủ.

---

# 554.55. Remote cache failure

Network failure:

```text
remote miss/failure
→ local build
```

nếu offline/local fallback được phép.

---

# 554.56. No mandatory network

Compiler build bình thường không yêu cầu network chỉ để kiểm tra cache.

---

# 554.57. Cache offline mode

```text
--offline
```

chặn remote cache/dependency access.

---

# 554.58. Cache-only mode

Có thể có:

```text
--cache-only
```

để CI hoặc distributed build yêu cầu cache hit.

Cache miss trở thành explicit failure.

---

# 554.59. Cache provenance

Artifact record:

```text
CacheProvenance {
    producer
    source_dependencies
    compiler
    target
    policies
    timestamp
}
```

Timestamp không được là semantic input trừ khi policy yêu cầu.

---

# 554.60. Reproducible cache artifact

Hai clean compilations cùng inputs phải có artifact content tương đương theo reproducibility contract.

---

# 554.61. Debug information cache

Debug metadata có thể reuse nếu source mapping identity còn hợp lệ.

Nếu line mappings thay đổi, chỉ debug layer cần rebuild.

---

# 554.62. Source map independence

```text
Semantic artifact
      │
      ├── machine artifact
      │
      └── debug/source artifact
```

---

# 554.63. Object cache

Object cache key:

```text
MIR hash
ABI
target
features
optimization
debug policy
compiler backend
```

---

# 554.64. Codegen cache

Codegen cache có thể reuse machine code trước linker.

---

# 554.65. Machine code cache

Machine code không được reuse nếu:

```text
instruction selection policy
target features
ABI
backend version
```

thay đổi.

---

# 554.66. Link cache

Link output phụ thuộc:

```text
object hashes
linker version
link policy
sysroot
libraries
resource manifest
signing policy
```

---

# 554.67. Partial relinking

Nếu một object thay đổi, linker có thể reuse unchanged objects/intermediate layout information khi format/link strategy cho phép.

---

# 554.68. Final artifact cache

Executable cache key phải bao gồm toàn bộ link inputs.

---

# 554.69. Resource cache

Tích hợp `469`.

Resource compilation cache:

```text
resource hash
compiler/resource compiler version
target
compression policy
```

---

# 554.70. Shader cache

GPU shader/kernel artifacts cũng có semantic fingerprint riêng.

---

# 554.71. Tensor/model cache

AI model compilation cache từ `504/505` phải distinguish:

```text
model hash
operator graph
device
driver
kernel set
optimization
```

---

# 554.72. Cache namespace

Artifact key phải namespace theo artifact kind:

```text
HIR
MIR
Generic
Optimization
Object
Resource
Shader
Model
```

tránh collision.

---

# 554.73. Content-addressed storage

Storage backend ưu tiên:

```text
hash → immutable blob
```

---

# 554.74. Immutable cache artifacts

Artifact đã publish vào content-addressed cache không được mutate in place.

---

# 554.75. Garbage collection của cache

Cache storage có thể garbage collect artifact không còn referenced.

Đây là **cache storage GC**, hoàn toàn khác language GC và không liên quan runtime memory model.

---

# 554.76. Cache retention

Retention policy:

```text
LRU
size-based
age-based
pinned
reference-counted
```

---

# 554.77. Pinned artifacts

CI/release có thể pin artifact.

---

# 554.78. Cache eviction

Evict cache không được thay đổi correctness.

---

# 554.79. Cache statistics

Compiler có thể báo:

```text
cache_hit
cache_miss
invalidated
recomputed
remote_hit
remote_miss
```

---

# 554.80. Cache statistics ≠ performance score

Không tổng hợp thành universal score.

---

# 554.81. Incremental build trace

Có thể xuất:

```text
why_rebuilt(symbol)
why_invalidated(symbol)
why_cache_miss(key)
```

---

# 554.82. Why rebuilt

Ví dụ:

```text
B rebuilt because:
A public signature changed
```

---

# 554.83. Why not rebuilt

```text
C reused because:
C depends only on A implementation-insensitive interface
```

---

# 554.84. Dependency explainability

Dependency graph phải queryable.

---

# 554.85. Semantic diff

`486` có thể cung cấp:

```text
API changed
ABI changed
layout changed
trait changed
body changed
effect changed
```

cho incremental compiler.

---

# 554.86. Change classification

Mỗi source change được phân loại:

```text
FormattingOnly
DocumentationOnly
PrivateImplementation
PublicImplementation
Interface
Layout
ABI
Semantic
Build
Target
```

---

# 554.87. Formatting-only change

Không invalidate semantic artifacts.

---

# 554.88. Private implementation change

Invalidate local dependent artifacts according to optimization/codegen dependencies.

---

# 554.89. Public signature change

Invalidate all consumers dependent on that declaration.

---

# 554.90. Layout change

Invalidate all layout-dependent artifacts.

---

# 554.91. ABI change

Invalidate native call boundaries.

---

# 554.92. Trait implementation change

Invalidate affected generic resolution and dynamic dispatch assumptions.

---

# 554.93. Effect change

Ví dụ:

```text
@no_alloc
```

thay đổi có thể invalidate optimization/static-analysis consumers.

---

# 554.94. Security contract change

Security assumptions từ `549` phải là cache dependency.

---

# 554.95. Numeric policy change

Strict/fast numeric semantics là cache input.

---

# 554.96. Optimization policy change

`-O2 → -O3` không được reuse codegen cache như identical input.

---

# 554.97. Debug policy change

Có thể reuse semantic/MIR nhưng rebuild debug/codegen layers tương ứng.

---

# 554.98. Sanitizer policy

Sanitized artifact và production artifact phải có cache identity khác.

---

# 554.99. PGO policy

PGO cache key chứa profile hash.

---

# 554.100. PGO profile change

Profile thay đổi:

```text
optimization cache → invalidate as required
semantic cache → retain
```

---

# 554.101. Build graph integration

`487` trở thành graph-level coordinator:

```text
Build Graph
    ↓
Query Graph
    ↓
Semantic Cache
    ↓
Optimization Cache
    ↓
Artifact Cache
```

---

# 554.102. Query dependency vs build dependency

Phân biệt:

```text
semantic dependency
build dependency
resource dependency
environment dependency
toolchain dependency
```

---

# 554.103. Hermetic build

Trong hermetic mode, mọi external input phải explicit.

---

# 554.104. Non-hermetic build

Cho phép system-dependent inputs nhưng chúng phải được fingerprint khi ảnh hưởng artifact.

---

# 554.105. Environment fingerprint

Chỉ environment variables thực sự ảnh hưởng build mới được đưa vào key.

Không hash toàn bộ environment một cách mù quáng.

---

# 554.106. Build script dependency

Build script output phải trở thành graph artifact.

---

# 554.107. Build script cache

Key gồm:

```text
script hash
inputs
toolchain
environment inputs
target
```

---

# 554.108. Generated source cache

Generated source phải có provenance:

```text
generator
generator version
inputs
output hash
```

---

# 554.109. Generated source invalidation

Input generator thay đổi → output semantic hash thay đổi → downstream invalidation.

---

# 554.110. Parallel incremental compilation

Independent queries/modules compile song song.

---

# 554.111. Deterministic scheduling

Parallel compile không được thay đổi artifact semantics/reproducibility.

---

# 554.112. Locking

Cache writes phải atomic.

Không để hai compiler process tạo artifact half-written.

---

# 554.113. Atomic publish

```text
build temporary artifact
      ↓
verify
      ↓
atomic publish
```

---

# 554.114. Crash safety

Compiler crash giữa lúc cache write không được làm cache state invalid.

---

# 554.115. Cache transactions

Một multi-artifact build có thể publish manifest atomically sau khi tất cả artifacts verified.

---

# 554.116. Cache manifest

```text
CacheManifest {
    root_artifact
    dependencies[]
    fingerprints[]
    producer
    integrity
}
```

---

# 554.117. Dependency closure

Artifact được coi valid chỉ khi toàn bộ required closure compatible.

---

# 554.118. Partial cache hit

Có thể:

```text
A hit
B hit
C miss
```

và chỉ rebuild C.

---

# 554.119. Diamond dependencies

```text
    A
   / \
  B   C
   \ /
    D
```

compiler phải tránh compile duplicate semantic work.

---

# 554.120. Shared query result

Một semantic query result được nhiều downstream consumers dùng chung.

---

# 554.121. In-memory deduplication

Cùng immutable semantic object có thể được intern/share trong compiler process.

---

# 554.122. Cross-process cache

Artifacts phải serialize thành schema versioned format.

---

# 554.123. Cache schema evolution

Cache schema thay đổi:

```text
schema v1
→ v2
```

phải hỗ trợ migration hoặc invalidate.

---

# 554.124. Never silently reinterpret old cache

Artifact schema incompatible → miss/invalidate.

---

# 554.125. Compiler version compatibility

Compiler patch version có thể reuse artifact chỉ khi compatibility contract cho phép.

Không mặc định rằng mọi compiler version tương thích.

---

# 554.126. Semantic compiler version

Nếu compiler sửa bug type checker/ABI/optimizer semantics, cache identity phải thay đổi.

---

# 554.127. Bug-fixed cache invalidation

Compiler bug fix liên quan artifact generation phải bump relevant cache fingerprint.

---

# 554.128. Backend compatibility

Backend implementation thay đổi → codegen cache version thay đổi.

---

# 554.129. Frontend compatibility

Frontend semantic rules thay đổi → semantic cache version thay đổi.

---

# 554.130. Pass-level invalidation

Một pass thay đổi chỉ invalidate cache artifacts phụ thuộc pass đó.

---

# 554.131. Optimization pipeline hash

Pipeline:

```text
Pass A v3
Pass B v5
Pass C v2
```

→ deterministic `PipelineHash`.

---

# 554.132. Selective optimization cache

Có thể reuse intermediate result trước pass đã thay đổi.

Ví dụ:

```text
MIR
 ↓
Pass A   HIT
 ↓
Pass B   MISS
 ↓
Pass C
```

---

# 554.133. Pass dependency closure

Nếu Pass B thay đổi analysis contract của Pass C, cache C cũng phải invalidate.

---

# 554.134. Analysis cache

Analysis result cache được phép tồn tại độc lập:

```text
AliasInfo
LoopInfo
RangeInfo
CallGraph
```

---

# 554.135. Analysis soundness

Cache không được biến stale analysis thành valid analysis.

---

# 554.136. Correctness-first cache validation

Cache hit:

```text
lookup
→ compatibility
→ integrity
→ schema
→ verifier
→ accept
```

---

# 554.137. Artifact verifier

Verifier từ `552` được gọi cho critical cached IR/object.

---

# 554.138. Untrusted cache mode

Cache từ nguồn không tin cậy:

```text
no execution
strict validation
signature/provenance verification
```

---

# 554.139. Cache permissions

Remote cache không được cấp capability ngoài:

```text
read artifact
write artifact
```

theo policy.

---

# 554.140. No arbitrary cache code execution

Cache artifact không được chứa executable build hooks.

---

# 554.141. Cache and build scripts

Build script là code có authority riêng; cache blob không được trở thành build script.

---

# 554.142. Secret isolation

Secret không được trở thành implicit cache key hoặc cache payload.

---

# 554.143. Secret-dependent artifact

Nếu output phụ thuộc secret, policy phải ngăn artifact publish vào shared cache hoặc đánh dấu private.

---

# 554.144. Tenant isolation

Remote cache phải namespace project/organization/tenant.

---

# 554.145. Artifact authorization

Read/write policy độc lập với artifact integrity.

---

# 554.146. Cache privacy

Semantic metadata có thể chứa source-derived information.

Shared cache phải có policy stripping/redaction khi cần.

---

# 554.147. AI-readable cache metadata

AI query:

```text
cache_status(symbol)
cache_dependencies(symbol)
why_rebuilt(symbol)
why_cache_miss(symbol)
artifact_provenance(artifact)
```

---

# 554.148. AI incremental planning

AI có thể hỏi:

```text
what_will_rebuild(change)
```

để biết impact trước build.

---

# 554.149. Impact prediction

Prediction phải distinguish:

```text
GuaranteedInvalidation
PossibleInvalidation
NoInvalidation
Unknown
```

---

# 554.150. No false certainty

AI/compiler không được nói:

> “Chỉ file X sẽ rebuild”

nếu optimization/LTO/profile dependency khiến kết quả chưa chắc chắn.

---

# 554.151. Warm build

Warm build phải tận dụng:

```text
semantic query cache
incremental artifacts
object cache
link cache
```

---

# 554.152. Cold build

Cold build phải không phụ thuộc cache.

---

# 554.153. Clean equivalence

```text
CleanBuild(source)
==
IncrementalBuild(source)
```

về semantic/artifact correctness.

---

# 554.154. Artifact equivalence

Binary byte identity có thể không phải requirement ở mọi mode, nhưng semantic/build reproducibility contract phải được xác định.

---

# 554.155. Reproducible mode

Trong reproducible mode:

```text
same inputs
→ same artifact bytes
```

theo target/platform contract.

---

# 554.156. Timestamp elimination

Không đưa timestamp ngẫu nhiên vào artifact reproducible.

---

# 554.157. Build path normalization

Absolute local paths không được làm thay đổi deterministic artifact trừ khi debug policy yêu cầu.

---

# 554.158. Debug path remapping

Compiler hỗ trợ source root/path remapping.

---

# 554.159. Cache and distributed compilation

Distributed workers:

```text
scheduler
 ↓
cache lookup
 ↓
worker
 ↓
artifact verification
 ↓
cache publish
```

---

# 554.160. Worker trust

Worker không được tự động trở thành trusted compiler.

Artifact vẫn phải được verify.

---

# 554.161. Remote execution

`487` remote execution tích hợp cache identity.

---

# 554.162. Remote worker version

Worker phải match required toolchain/compiler identity.

---

# 554.163. Remote nondeterminism

Nếu worker tạo artifact khác expected reproducible artifact:

```text
ReproducibilityMismatch
```

---

# 554.164. Cache differential verification

Một số critical artifacts có thể build:

```text
worker A
worker B
```

và compare.

---

# 554.165. Cache poisoning detection

Nếu cùng key trả về hai nội dung khác nhau:

```text
CacheConflict
```

artifact không được blindly accept.

---

# 554.166. Cache conflict quarantine

Conflicting producer/artifact được isolate và record provenance.

---

# 554.167. Generic cross-project cache trust

Generic machine artifact từ project khác chỉ được reuse nếu:

```text
generic semantic hash
ABI
target
compiler contract
```

match.

---

# 554.168. Private generic definitions

Private implementation details không được leak qua public cache metadata nếu visibility policy cấm.

---

# 554.169. Public module package

Package binary distribution nên chứa:

```text
API metadata
ABI metadata
generic metadata as needed
native artifacts
provenance
```

---

# 554.170. Precompiled module consumption

Consumer:

```text
import foo
```

có thể:

```text
load interface
resolve symbols
reuse native artifacts
```

mà không compile source package.

---

# 554.171. Source fallback

Nếu precompiled artifact incompatible:

```text
binary cache miss
→ source fallback
```

nếu source available.

---

# 554.172. Binary-only package

Binary-only package không có source fallback.

Compatibility failure phải diagnostic rõ ràng.

---

# 554.173. API evolution

API-compatible change có thể preserve binary consumers tùy ABI policy.

---

# 554.174. ABI evolution

ABI-incompatible change phải bump ABI identity.

---

# 554.175. Semantic version ≠ cache identity

Package SemVer không đủ để xác định cache compatibility.

---

# 554.176. Content-addressed dependency

Dependency artifact có thể được referenced bằng content hash.

---

# 554.177. Lockfile integration

Lockfile `432` ghi resolved artifact identities.

---

# 554.178. Cache and package manager

Package manager có thể fetch:

```text
source
semantic module
native artifact
cache artifact
```

theo policy.

---

# 554.179. Build manifest

Build manifest có thể record exact cache inputs.

---

# 554.180. Artifact attestation

Release artifact có thể có attestation:

```text
source hash
dependency closure
compiler
target
cache provenance
```

---

# 554.181. Cache poisoning ≠ compiler miscompilation

Phải phân biệt:

```text
bad cache artifact
bad compiler
bad source
bad dependency
```

---

# 554.182. Miscompilation forensic integration

Nếu cached object chạy sai:

```text
invalidate cache
rebuild clean
compare
```

để xác định cache-related failure.

---

# 554.183. Cache bypass diagnostic

Compiler hỗ trợ:

```text
--no-cache
--no-remote-cache
--verify-cache
```

---

# 554.184. Cache verification mode

CI có thể periodically:

```text
cache build
vs
clean build
```

---

# 554.185. Cache hit verification sampling

Không nhất thiết verify mọi artifact deep-level trong production; policy có thể chọn sampling.

---

# 554.186. Critical artifact verification

Compiler correctness/security-critical artifacts có thể yêu cầu full verification.

---

# 554.187. Incremental compilation correctness test

Test pattern:

```text
build clean
modify one entity
build incremental
compare
```

---

# 554.188. Invalidation oracle

Test suite phải biết chính xác artifact nào **được phép** invalidate.

Không test bằng assumption “mọi thứ phải rebuild”.

---

# 554.189. Minimal rebuild test

Có corpus:

```text
large project
one function changed
```

và đo dependency closure.

---

# 554.190. Cache hit test

Build twice:

```text
first = cold
second = warm
```

expected semantic cache hits.

---

# 554.191. Cache corruption tests

Randomly corrupt cache blob:

```text
compiler
→ reject
→ rebuild
```

---

# 554.192. Schema migration tests

Old cache versions phải:

```text
migrate
```

hoặc:

```text
invalidate
```

không crash.

---

# 554.193. Compiler upgrade tests

Compiler versions:

```text
N
N+1
```

phải kiểm tra artifact reuse compatibility.

---

# 554.194. Target-change tests

```text
x86_64
→ aarch64
```

không được reuse machine-specific artifacts.

---

# 554.195. Feature-change tests

```text
generic
→ AVX2
```

không được reuse incompatible machine code.

---

# 554.196. Optimization-change tests

```text
-O2
→ -O3
```

semantic artifacts có thể reuse; optimization/codegen artifacts chỉ reuse nếu fingerprint tương thích.

---

# 554.197. Profile-change tests

Profile A/B phải tạo distinct profile-dependent artifacts.

---

# 554.198. Security-policy-change tests

Thay đổi sanitizer/security policy phải invalidate artifacts affected by that policy.

---

# 554.199. Final cache contract

Axiom cache system phải đạt:

```text
Fast
Incremental
Deterministic
Content-addressed
Dependency-aware
Cross-project reusable
Remote-capable
Secure
Verifiable
Explainable
```

nhưng:

```text
Cache ≠ Source of Truth
```

---

# 554.200. Hard invariants

1. Cache không phải source of truth.
2. Clean build phải luôn khả dụng.
3. Cache hit phải semantic-equivalent với recomputation.
4. Cache artifact phải immutable sau publish.
5. Cache artifact phải có identity.
6. Cache artifact phải có schema version.
7. Cache artifact phải có producer identity.
8. Source hash phải phân biệt source content.
9. Semantic hash phải phản ánh semantic input.
10. Formatting-only change không được bắt buộc semantic rebuild.
11. Comment-only change không được bắt buộc semantic rebuild.
12. Declaration fingerprint phải ổn định.
13. Interface fingerprint phải tách implementation fingerprint.
14. Private implementation không mặc nhiên invalidate consumers.
15. Public interface change phải invalidate affected consumers.
16. Layout change phải invalidate layout-dependent artifacts.
17. ABI change phải invalidate ABI-dependent artifacts.
18. Trait change phải invalidate affected trait consumers.
19. Effect change phải invalidate effect-dependent analyses.
20. Security contract change phải invalidate security-dependent artifacts.
21. Numeric policy change phải invalidate affected optimization artifacts.
22. Optimization policy change phải fingerprint.
23. Target phải fingerprint.
24. CPU features phải fingerprint.
25. ABI phải fingerprint.
26. Object format phải fingerprint.
27. Sysroot phải fingerprint khi ảnh hưởng artifact.
28. SDK phải fingerprint khi ảnh hưởng artifact.
29. Runtime ABI phải fingerprint khi ảnh hưởng artifact.
30. Standard library ABI phải fingerprint.
31. Compiler build identity phải fingerprint.
32. Language edition phải fingerprint.
33. Compiler semantic version phải fingerprint.
34. Backend version phải fingerprint machine artifacts.
35. Pass pipeline phải fingerprint optimized artifacts.
36. Analysis cache phải versioned.
37. Stale analysis không được reuse.
38. Generic instance cache phải chứa type arguments.
39. Generic instance cache phải chứa const arguments.
40. Generic cache phải chứa trait resolution identity.
41. Generic cache phải chứa layout identity khi relevant.
42. Generic cache phải chứa ABI identity.
43. Generic cache phải chứa target identity.
44. Generic specialization policy phải fingerprint.
45. Comptime cache phải chứa function identity.
46. Comptime arguments phải là cache inputs.
47. Comptime external inputs phải explicit.
48. Ambient environment không được implicit comptime dependency.
49. Module interface artifact phải versioned.
50. Module interface không được chứa stale public semantics.
51. Binary module phải declare ABI compatibility.
52. Binary module phải declare target.
53. Binary module phải declare CPU feature requirements.
54. Incompatible binary artifact phải bị reject.
55. Source fallback phải được hỗ trợ khi source tồn tại.
56. Binary-only incompatibility phải có diagnostic.
57. Cross-project reuse phải kiểm tra compatibility.
58. Remote cache không được trusted mặc định.
59. Remote artifact phải integrity-check.
60. Signed/provenance policy phải được enforce khi required.
61. Cache poisoning phải detectable.
62. Cache conflict phải detectable.
63. Conflicting artifacts không được silently choose.
64. Corrupted cache phải reject.
65. Cache corruption không được phá clean build.
66. Cache storage GC không liên quan language GC.
67. Cache eviction không được thay đổi correctness.
68. Cache không được chứa hidden executable hooks.
69. Cache không được tự cấp capabilities.
70. Cache không được leak secrets.
71. Secret-dependent artifacts phải respect privacy policy.
72. Tenant cache isolation phải được enforce.
73. Cache metadata privacy phải configurable.
74. Cache writes phải atomic.
75. Cache publish phải atomic.
76. Partial writes không được trở thành valid artifact.
77. Crash giữa cache write phải recoverable.
78. Cache manifest phải integrity-protected.
79. Dependency closure phải được kiểm tra.
80. Partial cache hit phải được hỗ trợ.
81. Diamond dependencies không được duplicate semantic work không cần thiết.
82. Query results nên được immutable.
83. In-memory query reuse phải deterministic.
84. Cross-process artifacts phải serialize bằng schema ổn định.
85. Old schema phải migrate hoặc invalidate.
86. Old schema không được silently reinterpret.
87. Compiler upgrades phải kiểm tra cache compatibility.
88. Bug-fix compiler releases phải invalidate affected cache identities.
89. Backend changes phải invalidate affected machine cache.
90. Frontend semantic changes phải invalidate semantic cache.
91. Pass changes phải invalidate affected optimization cache.
92. Pass dependency changes phải propagate invalidation.
93. Analysis dependency changes phải propagate invalidation.
94. Inline dependency phải được fingerprint.
95. Devirtualization assumptions phải được fingerprint.
96. LTO assumptions phải được fingerprint.
97. PGO profile phải được fingerprint.
98. Profile mismatch phải được detected.
99. Stale profile không được silently treated as current.
100. Resource cache phải có resource identity.
101. Shader cache phải có target/device identity khi cần.
102. Model compilation cache phải có model identity.
103. Device-specific artifacts không được reuse trên incompatible devices.
104. Build-script output phải trở thành graph dependency.
105. Generated source phải có provenance.
106. Generated source change phải propagate invalidation.
107. Hermetic build phải enumerate external inputs.
108. Non-hermetic external inputs ảnh hưởng artifact phải fingerprint.
109. Không hash toàn bộ environment nếu không cần thiết.
110. Network không được mandatory cho local cache.
111. Offline mode phải disable remote access.
112. Cache-only mode phải fail explicitly khi miss.
113. Remote failure phải có local fallback khi policy cho phép.
114. Worker version phải được verify.
115. Remote execution artifact phải được verify.
116. Reproducibility mismatch phải được detectable.
117. Independent workers có thể được dùng để verify critical artifacts.
118. Cache statistics không phải correctness evidence.
119. Cache hit không phải proof compiler correctness.
120. Cache hit phải vẫn qua compatibility validation.
121. Critical cached IR phải có verifier.
122. Critical cached object phải có verifier.
123. Cache must integrate `552` correctness validation.
124. Cache must integrate `487` build graph.
125. Cache must integrate `486` semantic change impact.
126. Cache must integrate `446` semantic metadata.
127. Cache must integrate `553` optimization pipeline.
128. Cache must integrate `420` object/link identity.
129. Cache must integrate `482/488` compiler trust identity.
130. Cache provenance phải queryable.
131. `why_rebuilt` phải dựa trên dependency evidence.
132. `why_cache_miss` phải dựa trên actual key mismatch.
133. AI không được fabricate cache reasons.
134. `what_will_rebuild` phải biểu diễn uncertainty.
135. Incremental build phải support function-level invalidation.
136. Incremental build phải support module-level invalidation.
137. Incremental build phải support generic-level invalidation.
138. Incremental build phải support target-level invalidation.
139. Incremental build phải support policy-level invalidation.
140. Semantic artifacts có thể được reuse độc lập với debug artifacts.
141. Debug source changes không được bắt buộc semantic rebuild nếu semantics unchanged.
142. Object artifacts không được reuse khi target ABI thay đổi.
143. Link artifacts không được reuse khi dependency object closure thay đổi.
144. Final artifact cache phải include all link inputs.
145. Signing policy phải fingerprint signed artifacts.
146. Resource manifest phải fingerprint packaged artifacts.
147. Package lockfile changes phải affect dependency identity.
148. SemVer không được tự động quyết định binary compatibility.
149. API compatibility không đồng nghĩa ABI compatibility.
150. ABI compatibility không đồng nghĩa semantic compatibility.
151. Semantic compatibility không đồng nghĩa optimization compatibility.
152. Optimization compatibility không đồng nghĩa debug compatibility.
153. Cache layers phải giữ các compatibility dimensions riêng.
154. Cache key không được bỏ dimension chỉ vì “thường giống nhau”.
155. Cache key không nên chứa irrelevant inputs.
156. Cache invalidation phải conservative khi dependency unknown.
157. Unknown dependency không được treated as unchanged.
158. Build graph phải detect dependency cycles.
159. Cache graph phải handle cycles deterministically.
160. Recursive generic compilation phải avoid infinite cache recursion.
161. Recursive comptime phải respect existing resource limits.
162. Parallel cache access phải thread-safe.
163. Parallel cache result phải deterministic.
164. Same key must not produce silently different trusted content.
165. Artifact identity must be content-addressable where practical.
166. Cache storage phải hỗ trợ quota.
167. Cache eviction policy phải deterministic enough for reproducibility of build behavior where required.
168. Cache must not introduce hidden runtime dependencies.
169. Cache must not introduce hidden allocations into produced program.
170. Cache must not introduce hidden threads.
171. Cache must not introduce hidden network activity into program.
172. Cache must not alter language semantics.
173. Cache must not alter ABI semantics.
174. Cache must not alter memory semantics.
175. Cache must not alter concurrency semantics.
176. Cache must not alter panic/error semantics.
177. Cache must not alter security semantics.
178. Cache must not weaken validation because artifact came from cache.
179. Cache provenance must survive artifact redistribution when required.
180. Cache artifacts must be inspectable.
181. Cache artifacts must be diagnosable.
182. Cache artifacts must be invalidatable manually.
183. Cache must support complete purge.
184. Complete purge must leave project buildable.
185. Compiler must support `--no-cache`.
186. Compiler must support remote-cache disable policy.
187. Compiler must support cache verification.
188. Compiler must support incremental-build tracing.
189. Compiler must support dependency explanation.
190. Compiler must support artifact provenance query.
191. Compiler must support cache schema evolution.
192. Compiler must support cross-project cache reuse.
193. Compiler must support precompiled modules.
194. Compiler must support precompiled generic instances.
195. Compiler must support object-level cache.
196. Compiler must support final artifact cache.
197. Compiler must preserve clean/incremental equivalence.
198. Compiler must detect cache-related miscompilation.
199. Cache correctness must remain subordinate to compiler correctness.
200. **Final invariant:** mọi cache hit của Axiom phải có thể chứng minh rằng nó tương đương với việc tính toán lại từ các input semantic tương ứng; mọi thay đổi ảnh hưởng semantics, ABI, layout, target, toolchain, optimization, security hoặc profile phải lan truyền invalidation chính xác, trong khi những thay đổi không liên quan không được ép rebuild; cache chỉ làm compiler nhanh hơn và không bao giờ được trở thành một nguồn semantics mới.

**BOOTSTRAP-554: LOCKED.**

---

# NEXT — BOOTSTRAP-555

## BOOTSTRAP-555 — COMPILER DAEMON, LONG-LIVED PROCESS, QUERY DATABASE SERVER, FILE WATCHING & IDE-INCREMENTAL COMPILATION

`554` đã xây cache persistent. Bước tiếp theo là tận dụng nó trong **compiler daemon** để Axiom có trải nghiệm incremental cực nhanh cho IDE/LSP/CLI.

Kiến trúc:

```text
                     IDE / CLI / LSP / AI
                              │
                              ▼
                     Axiom Compiler Daemon
                              │
             ┌────────────────┼────────────────┐
             ▼                ▼                ▼
        Source Snapshot   Query Database    Build Graph
             │                │                │
             └────────────────┼────────────────┘
                              ▼
                       Incremental Engine
                              │
             ┌────────────────┼────────────────┐
             ▼                ▼                ▼
         Semantic          Optimizer         Cache
          Queries           Queries          Store
             │                │                │
             └────────────────┼────────────────┘
                              ▼
                         Code / Artifact
```

Task `555` sẽ khóa:

- daemon lifecycle;
- persistent compiler process;
- snapshot-based source model;
- concurrent IDE snapshots;
- cancellation;
- query scheduling;
- incremental reparsing;
- incremental semantic analysis;
- background compilation;
- LSP latency isolation;
- build-vs-editor query priority;
- memory reclamation của daemon;
- compiler restart/recovery;
- cache warmup;
- multi-project workspace;
- concurrent projects;
- file watching;
- filesystem event coalescing;
- stale snapshot detection;
- daemon IPC;
- security/capability boundary;
- AI semantic-query server;
- deterministic behavior dù daemon chạy lâu;
- và đặc biệt **daemon crash hoặc restart không được làm thay đổi kết quả compilation so với clean compiler process**.