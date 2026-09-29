# BOOTSTRAP-592 — DISTRIBUTED PACKAGE BUILD & BINARY CACHE PLATFORM 5.0
## REMOTE PACKAGE BUILDS, CONTENT-ADDRESSED BUILD CACHE, PREBUILT ARTIFACT DISTRIBUTION, TRUSTED REMOTE WORKERS, CACHE VALIDATION, CROSS-TARGET ARTIFACT REUSE, BUILD FARM, PRIORITY SCHEDULING & ZERO-REBUILD DEVELOPMENT

**Trạng thái: COMPLETED / LOCKED**

`592` xây dựng lớp thực thi build phía trên package/dependency graph của `591`.

Mục tiêu chính:

- build incremental cực nhanh;
- zero-rebuild khi input semantic không thay đổi;
- local cache + remote cache;
- remote compilation;
- content-addressed build actions;
- worker không được tự ý thay đổi semantics;
- artifact phải verify trước khi reuse;
- hỗ trợ cross-compilation;
- tận dụng song song tối đa;
- vẫn giữ reproducibility và compiler trust của `567/587`;
- không biến remote build thành một dependency bắt buộc.

---

# 592.1. Build platform architecture

```text
                         PROJECT
                            │
                            ▼
                   Resolved Package Graph
                            │
                            ▼
                    Build Graph 487/568
                            │
                            ▼
                    Action Graph 592
                            │
          ┌─────────────────┼─────────────────┐
          ▼                 ▼                 ▼
     Local Worker      Remote Worker      Cached Result
          │                 │                 │
          └─────────────────┼─────────────────┘
                            ▼
                   Verified Artifact
                            │
                    ┌───────┴───────┐
                    ▼               ▼
               Local CAS        Remote CAS
```

---

# 592.2. Build action

Mọi compilation step được biểu diễn thành immutable action:

```text
BuildAction {
    action_id
    inputs[]
    toolchain
    target
    environment
    policy
    command_semantics
    outputs[]
}
```

---

# 592.3. Action identity

```text
ActionID =
Hash(
    canonical(action inputs)
    toolchain identity
    target identity
    environment identity
    build policy
)
```

---

# 592.4. Không hash command string đơn thuần

Hai command string khác nhau nhưng semantic build action giống nhau có thể có cùng normalized representation.

Ngược lại, command giống nhau nhưng environment khác phải tạo action khác.

---

# 592.5. Input identity

Input có thể là:

```text
source file
semantic artifact
package
object
generated file
configuration
SDK
compiler
```

---

# 592.6. Merkle input tree

Build inputs được tổ chức thành Merkle tree.

```text
                    Root
                     │
          ┌──────────┴──────────┐
          ▼                     ▼
       Source                 Config
          │                     │
      ┌───┴───┐                 ▼
      ▼       ▼              Toolchain
     A.ax    B.ax
```

---

# 592.7. Directory identity

Directory không được hash dựa vào filesystem metadata tùy host.

---

# 592.8. File identity

File identity:

```text
FileDigest {
    algorithm
    size
    content_hash
}
```

---

# 592.9. Generated input

Generated file phải có provenance:

```text
generator_action
generator_version
input_hash
output_hash
```

---

# 592.10. Action output

```text
ActionResult {
    action_id
    outputs[]
    stdout_digest
    stderr_digest
    metadata
}
```

---

# 592.11. Output immutability

Một `ActionID` không được map tới hai incompatible outputs.

---

# 592.12. Cache key

```text
CacheKey = ActionID
```

Không dùng:

```text
source filename
timestamp
package version
```

làm cache key chính.

---

# 592.13. Local build cache

Local cache lưu:

```text
ActionID → ActionResult
```

---

# 592.14. Remote build cache

Remote cache có cùng semantic model.

```text
RemoteCAS
RemoteActionCache
```

---

# 592.15. Cache lookup order

Mặc định:

```text
L1 compiler memory cache
 ↓
L2 local action cache
 ↓
L3 local CAS
 ↓
L4 remote action cache
 ↓
L5 remote CAS
 ↓
compile
```

---

# 592.16. Cache hit

Cache hit chỉ là **candidate result** cho tới khi verification hoàn tất.

---

# 592.17. Cache verification

```text
lookup
 ↓
download
 ↓
verify digest
 ↓
verify metadata
 ↓
verify target/toolchain
 ↓
accept
```

---

# 592.18. Corrupt cache

Nếu digest mismatch:

```text
quarantine
invalidate entry
retry alternate source
```

---

# 592.19. Cache poisoning

Không được trust cache chỉ vì cache server được authenticated.

Content identity vẫn phải được verify.

---

# 592.20. Remote worker

Remote worker thực thi action:

```text
ActionRequest
     ↓
Input fetch
     ↓
Sandbox
     ↓
Compiler
     ↓
Output
     ↓
Output hash
```

---

# 592.21. Worker identity

Worker có:

```text
WorkerIdentity {
    worker_id
    platform
    architecture
    toolchain_set
    capabilities
    trust_state
}
```

---

# 592.22. Worker capability

Worker khai báo:

```text
x86_64
aarch64
linux
windows
macos
wasm
```

và compiler/toolchain versions.

---

# 592.23. Worker không được chọn target tùy ý

Scheduler chọn worker dựa trên target requirements.

---

# 592.24. Worker trust

Trust state có thể:

```text
Unknown
Verified
Trusted
Quarantined
Revoked
```

---

# 592.25. Trusted worker

Trusted worker phải có identity và provenance được xác minh.

---

# 592.26. Untrusted worker

Untrusted worker có thể thực thi build trong sandbox nhưng artifact không được tự động promotion thành trusted release artifact.

---

# 592.27. Worker attestation

Platform có extension point cho worker attestation.

Attestation không được là requirement của local-only build.

---

# 592.28. Worker compiler identity

Worker phải report exact compiler identity:

```text
compiler_hash
compiler_version
compiler_trust_state
```

---

# 592.29. Toolchain identity

Worker phải report:

```text
toolchain_hash
SDK_hash
runtime_hash
target_db_hash
```

---

# 592.30. Hermetic execution

Remote action mặc định:

```text
network = disabled
undeclared filesystem = denied
undeclared environment = denied
```

---

# 592.31. Input closure

Worker chỉ được access inputs được action declaration cho phép.

---

# 592.32. Output closure

Worker chỉ được publish outputs được action declaration khai báo.

---

# 592.33. Sandbox escape

Sandbox violation phải làm action fail.

---

# 592.34. Build environment

Environment phải canonicalized:

```text
locale
timezone
environment variables
filesystem root
compiler paths
SDK paths
```

---

# 592.35. Host path elimination

Artifact không được chứa absolute host paths trừ debug metadata đã remap/canonicalized.

---

# 592.36. Source path mapping

Remote build phải hỗ trợ stable virtual paths:

```text
/axiom/src/...
```

---

# 592.37. Debug reproducibility

DWARF/CodeView source paths phải có deterministic remapping.

---

# 592.38. Timestamp elimination

Generated artifacts không được phụ thuộc build wall-clock time trong reproducible mode.

---

# 592.39. Randomness

Nếu compiler dùng randomness cho optimization, seed phải là deterministic action input.

---

# 592.40. Parallel workers

Independent actions được chạy song song.

```text
A ───────┐
         ├──→ D
B ───────┤
         │
C ───────┘
```

---

# 592.41. Dependency scheduling

Action chỉ runnable khi toàn bộ required input identities đã available.

---

# 592.42. Critical path

Scheduler ưu tiên actions nằm trên critical path.

---

# 592.43. Resource scheduling

Scheduler xét:

```text CPU
RAM
disk
network
target
GPU
worker load
```

---

# 592.44. Worker affinity

Có thể ưu tiên worker gần cache input.

---

# 592.45. Data locality

Scheduler nên minimize:

```text source transfer
CAS transfer
artifact transfer
```

---

# 592.46. Remote cache locality

Nếu nhiều cache replica, chọn replica theo latency/cost/policy.

---

# 592.47. Speculative execution

Action có thể được chạy speculatively khi:

```text expected critical-path benefit > estimated cost
```

---

# 592.48. Duplicate action suppression

Nếu hai clients request cùng `ActionID`, chỉ cần một execution.

---

# 592.49. Single-flight

```text
ActionID X
 ├── Client A
 ├── Client B
 └── Client C
       ↓
   one worker execution
```

---

# 592.50. Action lease

Worker giữ lease cho action execution.

---

# 592.51. Worker failure

Nếu worker mất kết nối:

```text lease expires
 ↓
action becomes runnable
 ↓
another worker executes
```

---

# 592.52. Partial output

Partial output không được publish như valid result.

---

# 592.53. Atomic result publication

```text
execute
 ↓
hash outputs
 ↓
upload CAS
 ↓
verify
 ↓
publish ActionResult
```

---

# 592.54. Action cache transaction

Action cache entry chỉ được publish sau khi tất cả outputs tồn tại và verify.

---

# 592.55. Remote CAS

Remote CAS là immutable content-addressed object store.

---

# 592.56. CAS object

```text
CASObject {
    digest
    size
    type
    compression
    content
}
```

---

# 592.57. CAS chunking

Artifact lớn có thể chunk thành:

```text
Chunk
Chunk
Chunk
...
Manifest
```

---

# 592.58. Chunk identity

Mỗi chunk có content digest.

---

# 592.59. Deduplication

Các artifacts dùng chung chunk được deduplicate.

---

# 592.60. Compression

Compression được coi là transport/storage detail.

Logical content hash tính trên uncompressed canonical content.

---

# 592.61. Remote transfer

Client có thể yêu cầu:

```text digest
size
compression options
```

---

# 592.62. Resumable transfer

Large object download/upload phải hỗ trợ resume.

---

# 592.63. Parallel transfer

Independent chunks có thể tải song song.

---

# 592.64. Transfer verification

Mỗi chunk và final object đều phải verify.

---

# 592.65. Cache tiering

```text
RAM
 ↓
SSD
 ↓
local HDD
 ↓
LAN cache
 ↓
remote cache
```

---

# 592.66. Cache eviction

Có thể dùng:

```text LRU
LFU
size-aware
cost-aware
```

nhưng eviction không được ảnh hưởng correctness.

---

# 592.67. Cache is acceleration only

Nếu cache trống:

> build vẫn phải thành công bằng cách compile lại.

---

# 592.68. Offline mode

```text
axiom build --offline
```

không truy cập remote cache/registry.

---

# 592.69. Offline cache closure

Build preflight phải xác định mọi input có sẵn local.

---

# 592.70. Remote-only artifact

Nếu artifact chỉ tồn tại remote:

```text offline build → explicit missing artifact error
```

---

# 592.71. Distributed build mode

```text
axiom build --distributed
```

có thể bật remote workers.

---

# 592.72. Local fallback

Remote build failure có thể fallback local nếu policy cho phép.

---

# 592.73. Strict distributed mode

Release CI có thể yêu cầu remote-only để kiểm soát environment.

---

# 592.74. Worker scheduling policy

Có thể chọn:

```text fastest
cheapest
nearest
trusted-only
local-first
remote-first
```

---

# 592.75. Policy không thay đổi semantics

Worker scheduling chỉ thay đổi nơi thực thi, không được thay đổi output semantics.

---

# 592.76. Cross compilation

Host:

```text Windows x86_64
```

có thể build:

```text Linux AArch64
```

nếu toolchain target tồn tại.

---

# 592.77. Target-specific cache

Cache key phải bao gồm target identity.

---

# 592.78. CPU feature cache

Artifact compiled với AVX2 không được reuse cho target không có AVX2.

---

# 592.79. Generic CPU artifact

Artifact generic có identity riêng.

---

# 592.80. Multi-version compiler cache

Compiler version khác nhau phải tạo toolchain identity khác nhau.

---

# 592.81. Compiler semantic equivalence

Hai compiler binaries khác nhau nhưng proven semantic equivalence không mặc định được coi là cùng compiler identity.

---

# 592.82. Compiler trust

Trust verification có thể cho phép cross-validation, nhưng cache identity vẫn giữ exact compiler identity.

---

# 592.83. Build reproducibility

Hai workers:

```text Worker A
Worker B
```

với cùng action inputs phải tạo cùng canonical artifact nếu reproducible build contract được bật.

---

# 592.84. Reproducibility check

CI có thể chạy:

```text same action
worker A
worker B
compare hashes
```

---

# 592.85. Divergent result

Nếu:

```text hash(A) != hash(B)
```

action không được silently accept.

---

# 592.86. Divergence classification

Sử dụng classification của `587`:

```text
Expected
ConfigurationMismatch
ReproducibilityViolation
SemanticMismatch
BackendMismatch
RuntimeMismatch
Unknown
```

---

# 592.87. Deterministic artifacts

Build outputs phải deterministic khi reproducible profile được bật.

---

# 592.88. Non-deterministic artifacts

Nếu platform artifact bắt buộc chứa non-deterministic metadata, metadata phải được canonicalized hoặc tách khỏi reproducible content.

---

# 592.89. Debug symbols

Debug symbols có thể là separate artifact.

---

# 592.90. Split debug cache

```text
binary hash
    │
    └── debug artifact hash
```

---

# 592.91. Test artifacts

Test binaries cũng là cacheable artifacts.

---

# 592.92. Test result cache

Test action có thể cache result nếu:

```text test inputs
binary identity
environment
test policy
```

giống nhau.

---

# 592.93. Flaky test protection

Test cache không được che giấu flaky behavior nếu test policy yêu cầu rerun.

---

# 592.94. Benchmark cache

Benchmarks mặc định không cache numerical performance result.

Build artifact vẫn cache được.

---

# 592.95. Static analysis cache

Static analysis result có thể cache theo semantic snapshot identity.

---

# 592.96. IDE integration

IDE `590` có thể query:

```text action status
cache status
worker status
artifact status
```

---

# 592.97. Zero-rebuild edit

Khi user thay đổi source:

```text Source
 ↓
Semantic invalidation
 ↓
Affected actions only
```

---

# 592.98. Unaffected package

Package không bị ảnh hưởng phải reuse artifact.

---

# 592.99. API-compatible implementation change

Nếu dependency public ABI/API fingerprint không đổi, downstream rebuild có thể được loại bỏ theo compiler/build policy.

---

# 592.100. ABI-sensitive invalidation

Nếu ABI thay đổi:

```text package
 ↓
all ABI-dependent artifacts
```

phải invalidate.

---

# 592.101. Semantic invalidation

Compiler query engine `559` cung cấp fine-grained dependency identity.

---

# 592.102. Query-to-action integration

```text
Semantic Query
      ↓
Semantic Fingerprint
      ↓
Build Action Input
```

---

# 592.103. Fine-grained compilation

Không bắt buộc compile toàn bộ package khi chỉ một function thay đổi nếu compiler architecture có thể giữ object/IR boundaries.

---

# 592.104. Function-level cache

Có thể cache semantic/codegen results ở function-level.

---

# 592.105. Module-level cache

Module-level artifact là baseline.

---

# 592.106. Package-level cache

Package artifact là distribution-level cache.

---

# 592.107. Cache hierarchy

```text
Function
   ↓
Module
   ↓
Package
   ↓
Application
```

---

# 592.108. Cache correctness hierarchy

Higher-level cache chỉ valid khi toàn bộ lower-level semantic inputs match.

---

# 592.109. Link cache

Final linker output có thể cache theo:

```text object identities
link options
target
SDK
resources
```

---

# 592.110. Partial linking

Có thể cache intermediate linked units.

---

# 592.111. LTO cache

LTO cache phải include:

```text LTO IR
optimization policy
compiler
target
profile
```

---

# 592.112. PGO cache

Profile-guided artifact phải reference exact profile identity.

---

# 592.113. Profile identity

```text ProfileID = Hash(profile data + collection policy)
```

---

# 592.114. PGO mismatch

Profile không tương ứng với binary/source phải không được silently reuse.

---

# 592.115. Resource cache

Generated resources có thể cache riêng.

---

# 592.116. Asset pipeline cache

Asset transformation:

```text input asset
+
tool
+
options
→ output
```

được model như build action.

---

# 592.117. Code generator cache

Generator output được cache theo generator action identity.

---

# 592.118. Build script cache

Build script output chỉ cache nếu script action hermetic hoặc explicit reproducibility contract.

---

# 592.119. Network-dependent build script

Mặc định không cache trong reproducible mode nếu network input không được pinned.

---

# 592.120. Secret inputs

Secret không được đưa trực tiếp vào public cache keys/content.

---

# 592.121. Secret-dependent artifact

Nếu artifact phụ thuộc secret, action phải được đánh dấu non-shareable hoặc secret-scoped.

---

# 592.122. Private cache

Private artifacts chỉ được lưu trong authorized cache.

---

# 592.123. Cache access control

Remote cache hỗ trợ:

```text read
write
admin
```

---

# 592.124. Artifact ACL

Package/project policy có thể hạn chế artifact access.

---

# 592.125. Cache namespace

Cache namespace:

```text organization
project
toolchain
target
```

có thể được dùng để isolate data.

---

# 592.126. Cache poisoning protection

Unsigned remote ActionResult không được trusted nếu policy yêu cầu signed cache.

---

# 592.127. Signed cache result

ActionResult có thể được signer ký.

---

# 592.128. Signature meaning

Signature xác nhận cache publisher/worker authority, không thay thế content verification.

---

# 592.129. Remote worker result provenance

Result phải record:

```text worker
compiler
toolchain
action
timestamp optional
```

---

# 592.130. Timestamp

Timestamp chỉ metadata và không được làm thay đổi reproducible artifact identity.

---

# 592.131. Build execution log

Mỗi action có machine-readable log identity.

---

# 592.132. Log privacy

Logs không được chứa secrets mặc định.

---

# 592.133. Remote execution protocol

Semantic protocol:

```text
ActionRequest
InputManifest
ToolchainRequirement
ExecutionPolicy
```

response:

```text
ActionResult
OutputManifest
ExecutionProvenance
VerificationData
```

---

# 592.134. Protocol version

Protocol version độc lập với Axiom language version.

---

# 592.135. Worker capability negotiation

Client gửi requirements.

Worker trả:

```text compatible
incompatible
```

---

# 592.136. Scheduler rejection

Worker không đủ toolchain/target phải bị loại trước execution.

---

# 592.137. Worker health

Worker có health state:

```text
ready
busy
draining
offline
quarantined
```

---

# 592.138. Worker draining

Worker đang draining không nhận action mới nhưng hoàn thành action hiện tại.

---

# 592.139. Build cancellation

User có thể cancel build.

---

# 592.140. Remote cancellation

Cancellation gửi tới worker nhưng correctness không phụ thuộc worker nhận được cancellation.

---

# 592.141. Orphaned action

Worker phải tự cleanup orphaned execution sau lease timeout.

---

# 592.142. Resource quota

Build farm có quota:

```text CPU
RAM
disk
network
concurrent actions
```

---

# 592.143. Priority classes

Ví dụ:

```text interactive
normal
CI
release
background
```

---

# 592.144. Interactive priority

IDE build được ưu tiên latency thấp.

---

# 592.145. Release priority

Release build được ưu tiên resource guarantee nhưng không được phá policy của các build khác.

---

# 592.146. Fairness

Scheduler phải tránh một project chiếm toàn bộ worker pool vô thời hạn.

---

# 592.147. Preemption

Long-running low-priority actions có thể bị preempt nếu action hỗ trợ checkpoint/restart.

---

# 592.148. Checkpoint

Checkpoint không được coi là valid artifact trừ khi format explicit.

---

# 592.149. Build farm topology

```text
                    Scheduler
                       │
          ┌────────────┼────────────┐
          ▼            ▼            ▼
       Worker A     Worker B     Worker C
          │            │            │
          └────────────┼────────────┘
                       ▼
                   Remote CAS
```

---

# 592.150. Regional workers

Worker pools có thể phân vùng theo region nhưng artifact identity vẫn global.

---

# 592.151. Locality policy

Project có thể yêu cầu:

```text same-region
specific jurisdiction
private workers
```

nếu deployment environment cần.

---

# 592.152. No semantic locality

Worker location không được thay đổi language semantics.

---

# 592.153. Cache federation

Remote caches có thể federate:

```text Cache A
   ↕
Cache B
   ↕
Cache C
```

---

# 592.154. Federation trust

Artifact vẫn verify content/signature/provenance sau federation.

---

# 592.155. Cache replication

High-value artifacts có thể replicate.

---

# 592.156. Replication correctness

Replica chỉ là copies cùng content identity.

---

# 592.157. Build result promotion

```text
unverified
 ↓
hash verified
 ↓
policy verified
 ↓
trusted cache
```

---

# 592.158. Release cache

Release cache có stricter policy:

```text trusted compiler
trusted toolchain
reproducible
signed
provenance complete
```

---

# 592.159. Development cache

Development cache có thể nới policy nhưng artifact phải mang trust state tương ứng.

---

# 592.160. Cache provenance chain

```text
ActionID
 ↓
Worker
 ↓
Compiler
 ↓
Toolchain
 ↓
Inputs
 ↓
Outputs
```

---

# 592.161. Artifact promotion

Artifact từ dev cache không tự động trở thành release artifact.

---

# 592.162. Rebuild verification

Release system có thể rebuild từ source trên independent worker.

---

# 592.163. Double-build verification

```text Build A
Build B
   ↓
Compare artifact
```

---

# 592.164. N-way verification

Security-sensitive release có thể yêu cầu:

```text A
B
C
```

independent builds.

---

# 592.165. Compiler-divergent verification

Một build có thể dùng compiler path độc lập theo `587`.

---

# 592.166. Translation validation

Artifact có thể reference translation-validation certificate từ `575/587`.

---

# 592.167. Miscompilation investigation

Nếu independent builds khác nhau:

```text source
 ↓
IR comparison
 ↓
machine comparison
 ↓
runtime differential
```

---

# 592.168. Build forensic data

Action có thể giữ:

```text input hashes
compiler hash
IR hash
object hash
final artifact hash
```

---

# 592.169. Reproducibility report

CLI:

```text
axiom build verify-reproducible
```

có thể xuất machine-readable report.

---

# 592.170. Remote cache invalidation

Cache invalidation xảy ra khi:

```text revoked compiler
revoked toolchain
security policy change
artifact corruption
trust revocation
```

---

# 592.171. Revoked compiler artifact

Policy có thể mark artifact built by revoked compiler unusable.

---

# 592.172. Cache quarantine

Không xóa ngay forensic artifact nếu security investigation yêu cầu preservation.

---

# 592.173. Artifact garbage collection

GC chỉ xóa artifact khi:

```text no lockfile reference
no active build
no retention policy
```

---

# 592.174. Retention policy

Có thể giữ:

```text last N builds
release builds
debug symbols
failed builds
```

---

# 592.175. Failed action cache

Failed actions không được cache như successful ActionResult.

---

# 592.176. Negative cache

Negative result có thể cache tạm thời để chống repeated failure, nhưng TTL phải giới hạn.

---

# 592.177. Error identity

Negative cache key vẫn là `ActionID`.

---

# 592.178. Cache statistics

Tooling có thể report:

```text hit rate
miss rate
transfer volume
compile time
queue time
```

---

# 592.179. Build explanation

IDE có thể show:

```text Why rebuilt?
```

Ví dụ:

```text compiler changed
dependency API changed
source changed
target changed
cache unavailable
```

---

# 592.180. Why cache hit?

Có thể show:

```text reused because ActionID matched
```

---

# 592.181. AI build explanation

AI tooling `590` có thể query build graph:

```text action
inputs
invalidator
cache
worker
artifact
```

---

# 592.182. AI must not invent cache state

Nếu cache state unknown:

```text unknown
```

phải được trả về thay vì suy đoán.

---

# 592.183. Build graph provenance API

```text get_action(id)
get_inputs(id)
get_outputs(id)
get_cache_status(id)
get_worker(id)
get_provenance(id)
```

---

# 592.184. IDE progress

Progress phải dựa trên DAG critical path, không chỉ percentage của số actions.

---

# 592.185. ETA

ETA chỉ là estimate và phải được đánh dấu estimate.

---

# 592.186. Build cancellation UX

IDE phải show actions cancelled/running/completed/cached.

---

# 592.187. Remote worker logs

Logs stream được nhưng final result phải được lưu dưới content identity nếu retention policy cho phép.

---

# 592.188. Network failure

Remote download failure:

```text retry
 ↓
alternate replica
 ↓
local fallback
```

theo policy.

---

# 592.189. Worker timeout

Timeout không được đồng nghĩa với action failure semantic.

Action có thể retry trên worker khác.

---

# 592.190. Retry safety

Build actions phải idempotent.

---

# 592.191. Side effects

Actions có external side effects không được mặc định chạy distributed.

---

# 592.192. Non-hermetic action

Phải được mark:

```text non_hermetic
```

và cache/share policy hạn chế.

---

# 592.193. Deployment actions

Install/sign/publish không được coi là pure compilation actions.

---

# 592.194. Signing boundary

Code signing vẫn ở post-link boundary của `588`.

---

# 592.195. Signing cache

Signed artifact cache key phải include signing identity/policy.

---

# 592.196. Secrets and signing

Private signing keys không được gửi tới generic remote worker.

---

# 592.197. Secure signing worker

Nếu remote signing cần thiết, phải dùng dedicated trusted signer service.

---

# 592.198. Build reproducibility vs signing

Unsigned binary có thể reproducible; signature wrapper có thể được tạo sau.

---

# 592.199. Package integration

Package `591` cung cấp immutable package inputs.

---

# 592.200. Build integration

Build `592` biến package graph thành immutable action graph.

```text
Package Graph
     ↓
Target Resolution
     ↓
Build Graph
     ↓
Action Graph
     ↓
CAS / Workers
```

---

# 592.201. Toolchain integration

`588` cung cấp exact:

```text compiler
linker
SDK
runtime
target database
```

identity.

---

# 592.202. Compiler integration

`555/556/557/558/559` cung cấp incremental semantic data.

---

# 592.203. Codegen integration

`561–580` cung cấp deterministic backend artifacts.

---

# 592.204. Link integration

`582–584` cung cấp deterministic native image outputs.

---

# 592.205. Trust integration

`587` cung cấp compiler trust/divergent build verification.

---

# 592.206. Debug integration

`589` cung cấp debug artifact relationships.

---

# 592.207. IDE integration

`590` tiêu thụ build state mà không tạo semantic duplicate.

---

# 592.208. Build manifest

Mỗi build phải có canonical manifest:

```text
BuildManifest {
    project
    source_revision
    dependency_graph
    toolchain
    target
    configuration
    actions
}
```

---

# 592.209. Build manifest hash

```text
BuildManifestID =
Hash(canonical(BuildManifest))
```

---

# 592.210. Release identity

Release artifact có thể reference:

```text
BuildManifestID
ArtifactHash
Provenance
```

---

# 592.211. Zero-rebuild contract

Nếu toàn bộ action inputs identity không đổi:

> Không được compile lại action chỉ vì cache implementation thay đổi.

---

# 592.212. Cache-independent correctness

Build không được dựa vào cache để tạo semantics.

---

# 592.213. Cache corruption recovery

Corrupt cache phải dẫn tới rebuild, không làm project unusable.

---

# 592.214. Remote cache outage

Remote cache outage không được làm local-capable project fail nếu local compilation/toolchain đủ.

---

# 592.215. Remote worker outage

Remote worker outage không được ảnh hưởng local-only correctness.

---

# 592.216. Deterministic fallback

Local và remote execution phải nhận cùng ActionID.

---

# 592.217. Artifact byte equality

Reproducible profile yêu cầu byte-for-byte equality của canonical artifact.

---

# 592.218. Semantic equality

Nếu platform artifact có intentionally variable metadata, phải compare canonical semantic payload thay vì raw bytes.

---

# 592.219. Artifact normalization

Native image builder `584` chịu trách nhiệm canonical native output.

---

# 592.220. Object cache

Object cache có thể reuse giữa linker invocations nếu object identity và linker compatibility match.

---

# 592.221. Link cache

Final image cache phải include:

```text linker identity
link options
section layout policy
imports/exports
resources
```

---

# 592.222. Thin rebuild

Thay đổi một resource không nên rebuild unrelated source compilation.

---

# 592.223. Resource-only relink

Nếu platform hỗ trợ, chỉ resource packaging/link action cần rerun.

---

# 592.224. Multi-target build

Một command có thể tạo nhiều targets:

```text
axiom build --target windows-x64,linux-x64,wasm32
```

Mỗi target có graph/action namespace riêng.

---

# 592.225. Cross-target cache reuse

Target-independent artifacts:

```text parser
semantic metadata
generic IR
```

có thể reuse nếu identity contract cho phép.

---

# 592.226. Target-dependent cache

Machine IR/object/native artifact không được reuse cross-target trừ khi artifact format explicit universal.

---

# 592.227. Universal artifacts

Nếu một artifact hỗ trợ nhiều target, identity phải ghi rõ target set.

---

# 592.228. CPU-dispatch artifact

Một package có thể chứa multiple CPU variants.

---

# 592.229. Runtime dispatch

CPU feature selection xảy ra runtime hoặc link-time theo artifact policy.

---

# 592.230. No accidental host dependency

Distributed build phải detect host SDK/library leakage.

---

# 592.231. Sysroot identity

Sysroot hash bắt buộc trong action identity nếu action dùng sysroot.

---

# 592.232. Environment fingerprint

Canonical environment fingerprint phải include only semantic inputs.

---

# 592.233. Non-semantic environment

Noise như:

```text hostname
worker ID
temporary directory
```

không được làm thay đổi ActionID.

---

# 592.234. Worker-independent action identity

Cùng action chạy trên worker A/B phải có cùng ActionID.

---

# 592.235. Worker-specific metadata

Worker identity nằm trong provenance, không phải semantic ActionID trừ khi worker capability itself changes semantics.

---

# 592.236. CPU microarchitecture

Nếu compilation dùng `-march=native`, resolved target feature set phải trở thành explicit action input.

---

# 592.237. Native optimization

No implicit host optimization trong reproducible builds.

---

# 592.238. Build profiles

Cache phải distinguish:

```text debug
release
size
speed
sanitize
coverage
profile
```

---

# 592.239. Sanitizer artifacts

Sanitized binary không được reuse cho normal release.

---

# 592.240. Coverage artifacts

Coverage instrumentation tạo artifact identity riêng.

---

# 592.241. Security hardening

Flags như:

```text CFI
stack protection
ASLR
RELRO
PIE
```

nếu ảnh hưởng artifact phải nằm trong action identity.

---

# 592.242. Build policy identity

Security/reproducibility policy phải được hash vào action identity nếu ảnh hưởng execution.

---

# 592.243. Package policy identity

Package verification policy không nhất thiết thay đổi compilation bytes nhưng thay đổi trust state; semantic build identity phải distinguish nếu policy ảnh hưởng artifact acceptance.

---

# 592.244. Trust-aware cache lookup

Cache result không đáp ứng current trust policy phải bị coi là cache miss.

---

# 592.245. Cache result provenance

Result phải reference exact input digest list.

---

# 592.246. Input completeness proof

ActionResult có thể chứa proof:

```text all declared inputs resolved
```

---

# 592.247. Output completeness proof

Tương tự với outputs.

---

# 592.248. Build graph snapshot

Remote scheduler nhận immutable graph snapshot.

---

# 592.249. Graph mutation

Nếu source thay đổi trong lúc build:

```text old revision
```

build tiếp tục hoặc cancel; không được trộn revision.

---

# 592.250. Snapshot consistency

Mọi action của một build session phải reference cùng source/dependency snapshot.

---

# 592.251. Stale result

Artifact từ old build revision không được silently install vào current session.

---

# 592.252. Build session identity

```text BuildSessionID
```

dùng cho UI/runtime coordination.

---

# 592.253. Artifact ownership

Build session giữ temporary reference tới artifacts.

---

# 592.254. Session cleanup

Khi build kết thúc, temporary references được release.

---

# 592.255. Build daemon

Có thể giữ compiler/build daemon sống lâu dài.

---

# 592.256. Daemon + distributed build

Daemon chịu trách nhiệm:

```text graph
scheduler
cache
worker communication
```

---

# 592.257. Daemon crash recovery

Build graph immutable nên daemon có thể reconstruct state từ manifest/CAS.

---

# 592.258. Persistent scheduler state

Optional; correctness không phụ thuộc persistent scheduler state.

---

# 592.259. Build farm observability

Metrics:

```text queue latency
execution latency
cache hit
cache bandwidth
worker utilization
failure rate
```

---

# 592.260. Distributed tracing

Build actions có trace IDs liên kết:

```text IDE
→ daemon
→ scheduler
→ worker
→ compiler
→ linker
```

---

# 592.261. Privacy

Source code không được upload remote nếu project policy cấm.

---

# 592.262. Remote source policy

Có thể:

```text source_remote_allowed
source_remote_denied
binary_only_remote
```

---

# 592.263. Local-only sensitive package

Package có thể mark source as local-only.

---

# 592.264. Remote build denial

Scheduler phải loại worker nếu action policy cấm remote execution.

---

# 592.265. Data sovereignty

Workspace có thể yêu cầu artifact không rời khỏi specified worker region.

---

# 592.266. Build encryption

Transport encryption bảo vệ dữ liệu trên đường truyền; content hash vẫn bảo vệ integrity.

---

# 592.267. CAS encryption

Remote CAS có thể encrypt-at-rest.

---

# 592.268. Encryption không thay thế identity

Encryption state không được dùng làm artifact identity.

---

# 592.269. Build farm federation

Các build farms có thể exchange artifacts thông qua signed/verified CAS.

---

# 592.270. Trust boundary

```text
Developer
   │
   ▼
Local Daemon
   │
   ├── Local Worker
   │
   └── Remote Scheduler
             │
             ▼
        Remote Worker
             │
             ▼
          Remote CAS
```

Mỗi boundary phải explicit.

---

# 592.271. Remote worker compromise

Nếu worker bị compromise:

- output hash có thể detect corruption;
- reproducibility verification có thể detect divergence;
- signed trusted release worker có thể bị revoke;
- local rebuild vẫn là fallback.

---

# 592.272. Malicious valid artifact

Nếu malicious artifact có valid hash từ compromised build:

> hash verification alone không đủ.

Do đó release trust cần provenance + trusted compiler/toolchain + policy verification.

---

# 592.273. Compiler compromise

Nếu compiler bị revoked:

```text affected ActionResults
→ trust re-evaluation
```

---

# 592.274. Toolchain compromise

Tương tự đối với SDK/runtime/toolchain.

---

# 592.275. Cache revocation

Cache entries có thể bị revoked bằng policy metadata mà không cần xóa physical bytes ngay.

---

# 592.276. Forensic preservation

Revoked artifact có thể giữ trong quarantine để điều tra.

---

# 592.277. Build reproducibility database

Hệ thống có thể lưu:

```text action
worker A result
worker B result
comparison
```

---

# 592.278. Reproducibility score

Không tạo ranking/score cho trust.

Chỉ dùng categorical state:

```text
verified
mismatch
unknown
```

---

# 592.279. Build correctness

Cache hit và fresh compile phải produce semantically equivalent outputs theo compiler correctness contract.

---

# 592.280. Differential cache validation

CI có thể chọn ngẫu nhiên cache hits để rebuild và compare.

---

# 592.281. Sampling policy

Sampling rate configurable.

---

# 592.282. Mandatory release validation

Release artifact phải có validation profile nghiêm ngặt hơn development cache.

---

# 592.283. Cache warmup

Build farm có thể precompute popular packages.

---

# 592.284. Package prebuild

Package registry `591` có thể publish prebuilt artifacts.

---

# 592.285. Package prebuild verification

Prebuilt package phải đi qua cùng artifact verification pipeline.

---

# 592.286. Prebuilt vs local build

Resolver có thể chọn prebuilt artifact để tăng tốc.

---

# 592.287. Build-from-source switch

User có thể yêu cầu:

```text
--build-from-source
```

để bỏ qua prebuilt package artifacts.

---

# 592.288. Cache bypass

```text
--no-cache
```

phải compile fresh nhưng vẫn dùng resolved package graph.

---

# 592.289. Cache-only

```text
--cache-only
```

chỉ sử dụng verified cache; miss là error.

---

# 592.290. Distributed-only

```text
--remote-only
```

không fallback local.

---

# 592.291. Local-only

```text
--local-only
```

không gửi source/artifact tới remote.

---

# 592.292. Reproducible mode

```text
--reproducible
```

bật strict deterministic environment.

---

# 592.293. Verify mode

```text
--verify-build
```

yêu cầu provenance/verification phù hợp policy.

---

# 592.294. Explain mode

```text
axiom build explain
```

show why action was rebuilt/reused.

---

# 592.295. Cache inspection

```text
axiom cache info <action-id>
axiom cache verify
axiom cache gc
```

---

# 592.296. Worker inspection

```text
axiom build workers
axiom build farm
```

---

# 592.297. Build graph inspection

```text
axiom build graph
```

export:

```text JSON
DOT
Axiom semantic graph
```

---

# 592.298. AI-readable build graph

AI API phải expose:

```text
BuildGraph
Action
Input
Output
InvalidationReason
CacheState
Worker
Provenance
```

---

# 592.299. AI build agent safety

AI agent không được tự:

- disable verification;
- accept untrusted artifact;
- bypass package policy;
- switch target silently;
- use undeclared dependency.

---

# 592.300. AI build recommendation

AI có thể đề xuất:

```text enable cache
use remote worker
prebuild package
reduce rebuild scope
```

nhưng mutation phải qua build policy/permission layer.

---

# 592.301. Build API

Core interfaces:

```text
BuildPlanner
ActionGraph
ActionScheduler
ActionExecutor
LocalCache
RemoteCache
CAS
WorkerPool
ArtifactVerifier
BuildProvenance
```

---

# 592.302. BuildPlanner

Chuyển:

```text Project + PackageGraph + Toolchain + Target
```

thành ActionGraph.

---

# 592.303. ActionScheduler

Chỉ scheduling.

Không compile.

---

# 592.304. ActionExecutor

Thực thi action local/remote.

---

# 592.305. CacheResolver

Tìm candidate ActionResult.

---

# 592.306. ArtifactVerifier

Verify:

```text hash
target
toolchain
provenance
trust
```

---

# 592.307. CAS

Immutable object storage.

---

# 592.308. WorkerPool

Quản lý worker lifecycle.

---

# 592.309. BuildProvenance

Lưu execution chain.

---

# 592.310. Scheduler correctness

Scheduler có thể thay đổi execution order nhưng không được thay đổi dependency semantics.

---

# 592.311. Worker nondeterminism

Worker scheduling, hostname, process ID không được ảnh hưởng reproducible artifact.

---

# 592.312. Concurrent writes

Output path collision giữa actions phải là build graph error.

---

# 592.313. Action namespace

Mỗi action có namespace/build graph context.

---

# 592.314. Duplicate output detection

Planner phải phát hiện hai actions tạo cùng logical output.

---

# 592.315. Output ownership

Một output canonical path chỉ có một producer trong graph.

---

# 592.316. CAS object aliasing

Logical output có thể reference cùng CAS object nếu bytes identical.

---

# 592.317. Hardlink/reflink optimization

Local store có thể dùng filesystem optimization nhưng semantics không phụ thuộc.

---

# 592.318. Zero-copy artifact materialization

Nếu filesystem hỗ trợ, artifact có thể materialize bằng reflink/hardlink.

---

# 592.319. Copy fallback

Nếu không hỗ trợ, copy bytes bình thường.

---

# 592.320. Artifact compression

Compression/decompression không thay đổi logical identity.

---

# 592.321. Large artifact streaming

Linker/image artifact có thể stream vào CAS mà không cần giữ toàn bộ trong RAM.

---

# 592.322. Memory bounded build

Build system phải hỗ trợ bounded-memory operation.

---

# 592.323. Disk bounded build

Scheduler phải biết disk quota trước khi dispatch action lớn.

---

# 592.324. Backpressure

Nếu CAS/network/storage quá tải:

```text producer throttling
```

---

# 592.325. Remote worker backpressure

Scheduler không gửi thêm action khi worker queue vượt policy.

---

# 592.326. Priority inversion protection

Interactive action không được bị chặn vô thời hạn bởi background transfer.

---

# 592.327. Cache prefetch cancellation

Prefetch có thể cancel mà không ảnh hưởng correctness.

---

# 592.328. Package download/build overlap

Resolver có thể download dependency song song với compile dependency đã sẵn sàng.

---

# 592.329. Pipeline parallelism

```text download A
      ↓
compile A
      ↓
link A
```

có thể overlap với download/compile B.

---

# 592.330. Critical path optimization

Build system phải tận dụng cả:

```text dependency parallelism
worker parallelism
compiler parallelism
I/O overlap
```

---

# 592.331. Build farm scaling

Worker pool có thể scale horizontally.

---

# 592.332. Autoscaling

Optional; không nằm trong compiler core.

---

# 592.333. Cost-aware scheduling

Cloud/remote deployments có thể dùng cost metadata nhưng không ảnh hưởng correctness.

---

# 592.334. Local-first default

Default development policy nên ưu tiên local cache/compiler nếu latency tốt và privacy policy yêu cầu.

---

# 592.335. Remote acceleration

Remote chỉ là acceleration layer.

---

# 592.336. No remote dependency

Axiom compiler/toolchain phải hoạt động hoàn chỉnh local.

---

# 592.337. Native-only mode

Freestanding/native builds vẫn có thể chạy không có package registry hoặc remote cache nếu inputs local.

---

# 592.338. Bootstrap builds

Compiler bootstrap `586/587` phải có thể disable distributed execution để giữ trust root đơn giản.

---

# 592.339. Trusted release builds

Release có thể dùng distributed build nhưng phải tăng verification.

---

# 592.340. Bootstrap trust boundary

Không được bootstrap compiler từ unverified remote artifact chỉ vì cache hit.

---

# 592.341. Compiler cache

Compiler binary itself có thể cache nhưng trust verification vẫn bắt buộc.

---

# 592.342. Toolchain cache

Toolchain packages có thể CAS-store.

---

# 592.343. SDK cache

SDK artifacts có identity từ `588`.

---

# 592.344. Runtime cache

Runtime object libraries có thể cache theo target/toolchain.

---

# 592.345. Standard library cache

Axiom std/core libraries có thể precompiled.

---

# 592.346. Generic library specialization cache

Generic monomorphization có thể cache theo:

```text generic definition identity
type arguments
target
optimization policy
```

---

# 592.347. Generic cache

```text GenericInstanceID =
Hash(definition + type arguments + semantic environment)
```

---

# 592.348. Trait specialization cache

Trait resolution result có thể cache.

---

# 592.349. Const evaluation cache

Comptime result có thể cache theo semantic input identity.

---

# 592.350. Semantic query cache

Query engine `559` đã cung cấp nền tảng.

Build system không duplicate semantic query engine.

---

# 592.351. Query cache boundary

Semantic cache có thể feed build action inputs.

---

# 592.352. Build cache boundary

Build cache không tự quyết định semantic validity.

---

# 592.353. Single semantic truth

```text IDE
Compiler
Build
Cache
AI
```

đều reference cùng semantic identities.

---

# 592.354. Incremental compilation chain

```text Source Change
     ↓
Query invalidation
     ↓
Semantic fingerprint
     ↓
Affected actions
     ↓
Cache lookup
     ↓
Minimal rebuild
```

---

# 592.355. Package graph chain

```text Package change
     ↓
Dependency graph change
     ↓
Build action invalidation
```

---

# 592.356. Toolchain change

```text Toolchain change
     ↓
affected action identity changes
     ↓
rebuild
```

---

# 592.357. Target change

```text Target change
     ↓
target-specific actions invalidate
```

---

# 592.358. Profile change

```text Release → Debug
```

không được reuse incompatible native artifacts.

---

# 592.359. Security policy change

Artifact có thể remain physically cached nhưng trust acceptance phải được reevaluated.

---

# 592.360. Dependency source change

Path/git/local override identity change phải invalidate dependent actions.

---

# 592.361. Build action canonicalization

Action serialization phải có canonical field order.

---

# 592.362. Hash domain separation

Hash namespaces phải distinguish:

```text package
file
action
artifact
toolchain
worker
build
```

để tránh cross-domain collision interpretation.

---

# 592.363. Versioned action schema

Action schema có version.

---

# 592.364. Cache schema compatibility

Cache client phải reject unsupported action schema thay vì reinterpret.

---

# 592.365. Cache migration

Cache schema upgrade có thể lazy-migrate hoặc invalidate old cache.

Correctness không phụ thuộc migration.

---

# 592.366. Remote cache protocol

Protocol phải versioned và backward-compatible trong supported range.

---

# 592.367. Worker protocol

Worker/compiler protocol phải verify exact toolchain contract.

---

# 592.368. Worker package acquisition

Worker có thể fetch packages from CAS nhưng package trust policy vẫn áp dụng.

---

# 592.369. Worker package cache

Worker có local package cache.

---

# 592.370. Worker cache warming

Scheduler có thể prewarm worker trước large build.

---

# 592.371. Cache-aware scheduling

Scheduler nên ưu tiên worker đã có required inputs.

---

# 592.372. Build farm admission

Action được submit sau validation:

```text schema
inputs
toolchain
target
policy
```

---

# 592.373. Invalid action

Không được dispatch action malformed.

---

# 592.374. Worker result validation

Client validates result before graph advancement.

---

# 592.375. Graph advancement

Chỉ verified ActionResult mới satisfy downstream dependency.

---

# 592.376. Poisoned dependency prevention

Một malformed output không được propagate sang downstream actions.

---

# 592.377. Action failure isolation

Một action failure chỉ block descendants, không block independent branches.

---

# 592.378. Partial build result

Successful independent outputs có thể được retained.

---

# 592.379. Resume build

Build session có thể resume từ verified CAS.

---

# 592.380. Crash-safe resume

Daemon crash không làm mất immutable ActionResults.

---

# 592.381. Build checkpoint

Build manifest + CAS đủ để reconstruct graph.

---

# 592.382. Remote session resume

Client có thể reconnect scheduler và recover action state.

---

# 592.383. Duplicate execution resolution

Nếu two workers execute same action:

```text first verified result wins
second identical result discarded/deduplicated
```

Nếu outputs khác:

```text reproducibility divergence
```

---

# 592.384. Duplicate result comparison

Có thể lưu cả hai kết quả để forensic analysis.

---

# 592.385. Build farm trust incident

Worker tạo divergent result nhiều lần có thể chuyển `Quarantined`.

---

# 592.386. Worker reputation

Không sử dụng numerical “trust score”.

Chỉ dùng policy states:

```text trusted
restricted
quarantined
revoked
```

---

# 592.387. Artifact provenance API

```text artifact.provenance()
```

trả về chain có thể verify.

---

# 592.388. Build explanation API

```text why_rebuilt(action)
why_cached(action)
```

---

# 592.389. AI semantic explanation

AI tooling có thể lấy structured facts:

```text reason_code
changed_input
previous_identity
current_identity
```

---

# 592.390. No hallucinated build diagnosis

IDE/AI phải distinguish:

```text known
inferred
unknown
```

---

# 592.391. Final build pipeline

```text
Project
  ↓
Package Resolution 591
  ↓
Resolved Graph
  ↓
Build Planning
  ↓
Action Graph
  ↓
Input CAS
  ↓
Cache Lookup
  ├── HIT → Verify → Accept
  │
  └── MISS
         ↓
    Local / Remote Worker
         ↓
      Execute
         ↓
    Output Hash
         ↓
    CAS Commit
         ↓
    Verify
         ↓
    ActionResult
         ↓
    Downstream Actions
         ↓
      Linker 582
         ↓
    Native Image 584
         ↓
    Final Verification
```

---

# 592.392. Reference implementation structure

Đề xuất module:

```text
compiler/
  build/
    action.ax
    graph.ax
    planner.ax
    scheduler.ax
    executor.ax
    provenance.ax

  cache/
    local.ax
    remote.ax
    cas.ax
    verify.ax
    gc.ax

  distributed/
    worker.ax
    protocol.ax
    farm.ax
    scheduler.ax
    sandbox.ax
```

---

# 592.393. Test matrix

Bắt buộc test:

```text local cache hit
local cache miss
remote cache hit
remote cache miss
worker failure
network failure
CAS corruption
duplicate execution
reproducible build
divergent worker
cross compilation
toolchain mismatch
target mismatch
policy mismatch
offline build
incremental source change
dependency change
ABI change
LTO change
PGO change
debug/release switch
```

---

# 592.394. Correctness test

```text fresh build
      ==
cache build
```

về semantic artifact identity.

---

# 592.395. Distributed correctness test

```text local build
      ==
remote build
```

trong reproducible profile.

---

# 592.396. Cross-worker test

```text worker A
worker B
worker C
```

phải produce identical canonical outputs khi cùng action.

---

# 592.397. Cache corruption test

Randomly corrupt CAS objects và xác nhận system:

```text detect
quarantine
rebuild/re-fetch
```

---

# 592.398. Security test

Test:

```text malicious worker
malformed ActionResult
wrong target artifact
wrong compiler
revoked compiler
tampered package
tampered CAS
```

---

# 592.399. Performance target

Development build phải hướng tới:

```text no-op build:
near-zero compilation

small edit:
rebuild only affected actions

large project:
parallel execution across all independent actions
```

Không hardcode một con số thời gian vì project size/hardware thay đổi.

---

# 592.400. Fundamental design decision

**Cache và distributed execution không thuộc semantic core của Axiom.**

Chúng là acceleration infrastructure.

```text
Language semantics
       │
       ▼
Compiler semantics
       │
       ▼
Deterministic build action
       │
       ├── local execution
       ├── remote execution
       ├── cached execution
       └── verified prebuilt artifact
```

Điều này cực kỳ quan trọng: Axiom không trở thành một ngôn ngữ “phụ thuộc cloud”.

---

# 592.401. FINAL HARD INVARIANTS

### Invariant 1 — cache is acceleration only

> Cache trống hoặc hỏng không được làm thay đổi tính đúng đắn của build.

### Invariant 2 — immutable action identity

> Cùng semantic inputs phải tạo cùng `ActionID`.

### Invariant 3 — target isolation

> Artifact chỉ được reuse khi target/ABI/CPU feature tương thích.

### Invariant 4 — toolchain identity

> Compiler, linker, SDK và runtime có ảnh hưởng semantic phải nằm trong build identity.

### Invariant 5 — hermetic remote execution

> Remote worker chỉ được access declared inputs/capabilities.

### Invariant 6 — output verification

> Không một ActionResult nào được dùng downstream trước khi output identity được verify.

### Invariant 7 — deterministic distributed build

> Local và remote execution của cùng reproducible action phải tạo cùng canonical artifact.

### Invariant 8 — worker independence

> Worker ID/location/scheduling không được thay đổi artifact semantics.

### Invariant 9 — cache poisoning resistance

> Authentication của cache không thay thế content-hash verification.

### Invariant 10 — trust separation

> Hash, signature, provenance và compiler trust là các lớp độc lập.

### Invariant 11 — no hidden host dependency

> Host SDK, environment, filesystem hoặc CPU features không được tự động lọt vào action.

### Invariant 12 — snapshot consistency

> Một build session phải dùng một immutable source/dependency/build snapshot.

### Invariant 13 — incremental correctness

> Chỉ actions bị invalidation mới bắt buộc rebuild.

### Invariant 14 — remote optionality

> Axiom vẫn phải build hoàn chỉnh local/offline nếu toàn bộ inputs cần thiết tồn tại local.

### Invariant 15 — security policy monotonicity

> Remote worker/cache/package không được hạ security/trust policy của root project.

### Invariant 16 — compiler trust

> Artifact được cache từ compiler/toolchain đã bị revoke không được tự động tiếp tục được coi là trusted.

### Invariant 17 — reproducibility evidence

> Divergent outputs giữa independent workers phải được phát hiện và phân loại, không được silently chọn một kết quả.

### Invariant 18 — atomicity

> Partial download, partial compilation hoặc partial CAS upload không được xuất hiện như artifact hợp lệ.

### Invariant 19 — semantic single truth

> Build system không được tạo semantic model riêng cạnh compiler query engine.

### Invariant 20 — provenance closure

> Mỗi release artifact phải có thể truy nguyên tới action inputs, toolchain và dependency identities theo mức provenance policy yêu cầu.

---

# 592 — LOCKED

Axiom hiện đã có chuỗi hoàn chỉnh từ source đến distributed native build:

```text
Language
   ↓
Compiler
   ↓
IR
   ↓
Optimization
   ↓
Machine Code
   ↓
Object
   ↓
Linker
   ↓
Native Image
   ↓
Toolchain / SDK
   ↓
Package Registry
   ↓
Distributed Build
   ↓
Verified Artifact
   ↓
IDE / Debugger / AI
```

Đặc biệt, `591 + 592` tạo thành một vòng lặp rất quan trọng:

```text
                Package Registry
                       │
                       ▼
                Dependency Graph
                       │
                       ▼
                  Build Graph
                       │
                       ▼
                  Action Graph
                       │
          ┌────────────┼────────────┐
          ▼            ▼            ▼
        Cache        Local        Remote
          │            │            │
          └────────────┼────────────┘
                       ▼
                Verified Artifact
                       │
                       ▼
                  Package/Release
```

Điều này cho phép Axiom hướng tới **zero-rebuild development** mà không phải đánh đổi native performance, reproducibility hoặc compiler trust.

# NEXT — BOOTSTRAP-593

## NATIVE APPLICATION PACKAGING, BUNDLE FORMAT & DEPLOYMENT GRAPH 5.0
### APP BUNDLE, RESOURCES, NATIVE LIBRARIES, RUNTIME DEPENDENCIES, PLATFORM PACKAGING, INSTALLATION GRAPH, APPLICATION MANIFEST, SIGNING BOUNDARY, SANDBOX/CAPABILITY DECLARATION, PORTABLE DEPLOYMENT & REPRODUCIBLE APPLICATION PACKAGE

Kiến trúc tiếp theo:

```text
                    Native Artifact
                          │
                          ▼
                 Application Graph
                          │
          ┌───────────────┼────────────────┐
          ▼               ▼                ▼
       Executable       Libraries       Resources
          │               │                │
          └───────────────┼────────────────┘
                          ▼
                  Runtime Dependencies
                          │
                          ▼
                  Application Bundle
                          │
             ┌────────────┼────────────┐
             ▼            ▼            ▼
          Windows       Linux        Apple
          Package       Package      Bundle
             │            │            │
             └────────────┼────────────┘
                          ▼
                  Deployment Artifact
                          │
                  Signing Boundary
                          │
                          ▼
                    Installed App
```

`593` sẽ nối phần **compiler/build/package** hiện tại với mục tiêu ban đầu của Axiom: không chỉ tạo `.exe/.elf/.app`, mà phải có **một application deployment model native, reproducible và target-aware** cho Windows, Linux, macOS, iOS, Android và WASM.