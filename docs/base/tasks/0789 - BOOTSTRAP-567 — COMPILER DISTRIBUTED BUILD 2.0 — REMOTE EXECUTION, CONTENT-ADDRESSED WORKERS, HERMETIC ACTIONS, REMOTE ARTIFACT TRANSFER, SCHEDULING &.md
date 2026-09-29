# BOOTSTRAP-567 — COMPILER DISTRIBUTED BUILD 2.0 — REMOTE EXECUTION, CONTENT-ADDRESSED WORKERS, HERMETIC ACTIONS, REMOTE ARTIFACT TRANSFER, SCHEDULING & TRUSTED PARALLEL BUILD

**Trạng thái: COMPLETED / LOCKED**

`BOOTSTRAP-566` đã khóa semantic cache và invalidation. `567` khóa tầng **distributed build / remote execution**: compiler có thể phân phối các action sang nhiều worker nhưng vẫn phải đảm bảo **determinism, hermeticity, correctness và reproducibility**.

Nguyên tắc trung tâm:

> **Worker chỉ thực thi một action đã được xác định đầy đủ bởi input manifest + toolchain + target + policy; worker không được tự ý lấy thêm dữ liệu từ môi trường của nó.**

---

# 567.1. Distributed build architecture

```text
                         AXIOM DAEMON
                              │
                       Build Snapshot
                              │
                              ▼
                       Action DAG
                              │
                  ┌───────────┼───────────┐
                  ▼           ▼           ▼
               Action A    Action B    Action C
                  │           │           │
                  └───────────┼───────────┘
                              ▼
                       Scheduler 2.0
                              │
             ┌────────────────┼────────────────┐
             ▼                ▼                ▼
        Local Worker     Remote Worker 1   Remote Worker 2
             │                │                │
             └────────────────┼────────────────┘
                              ▼
                     Content-Addressed Store
                       /                \
                 Local Cache         Remote Cache
                              │
                              ▼
                         Link Action
                              │
                              ▼
                        Final Artifact
```

---

# 567.2. Action

Đơn vị distributed execution là `Action`.

```text
Action {
    action_id
    inputs[]
    command
    toolchain
    target
    environment
    policy
    outputs[]
}
```

---

# 567.3. Action identity

```text
ActionId =
H(
    action_schema
    inputs
    toolchain
    target
    environment
    policy
    command
)
```

---

# 567.4. Content-addressed action

Action identity không dựa trên:

- worker;
- hostname;
- PID;
- filesystem path;
- timestamp.

---

# 567.5. Input manifest

Worker nhận manifest:

```text
InputManifest {
    files[]
    artifacts[]
    environment[]
    tools[]
}
```

---

# 567.6. Input file identity

Mỗi file input được xác định bằng content hash.

---

# 567.7. Directory identity

Directory input được canonicalize thành Merkle tree.

```text
Directory
 ├── a → hash
 ├── b → hash
 └── subdir
       └── c → hash
```

---

# 567.8. Path normalization

Logical paths được canonicalize trước hashing.

---

# 567.9. Path traversal

Worker phải reject:

```text
../
absolute escape
symlink escape
```

nếu không được manifest cho phép.

---

# 567.10. Hermetic filesystem

Worker chỉ nhìn thấy declared filesystem inputs.

---

# 567.11. Output filesystem

Worker chỉ được publish declared outputs.

---

# 567.12. Undeclared output

Undeclared output phải:

- reject;
- hoặc đặt vào disposable sandbox.

Không được tự động trở thành build input.

---

# 567.13. Environment

Action environment phải explicit.

```text
Environment {
    variables[]
    locale
    timezone
    encoding
}
```

---

# 567.14. Environment minimization

Mặc định worker không inherit toàn bộ host environment.

---

# 567.15. Time

Action không được phụ thuộc wall-clock nếu reproducible.

---

# 567.16. Randomness

Random source phải:

- deterministic seed;
- hoặc declared nondeterministic action.

---

# 567.17. Network

Hermetic compile action mặc định:

```text
network = disabled
```

---

# 567.18. Network-enabled action

Nếu cần network:

```text
network_policy = explicit
```

và network inputs phải được fingerprint khi ảnh hưởng output.

---

# 567.19. Toolchain bundle

Worker phải nhận toolchain identity:

```text
Toolchain {
    compiler
    linker
    assembler
    runtime
    sysroot
    SDK
}
```

---

# 567.20. Toolchain content

Toolchain identity phải dựa trên content/version fingerprint, không chỉ tên.

---

# 567.21. Worker capability

Worker advertise:

```text
WorkerCapability {
    architectures[]
    operating_systems[]
    cpu_features[]
    memory
    storage
    compiler_versions[]
}
```

---

# 567.22. Capability matching

Scheduler chỉ gửi action tới worker thỏa requirements.

---

# 567.23. Worker CPU

Worker CPU model không được ảnh hưởng result trừ khi action yêu cầu CPU-specific compilation.

---

# 567.24. CPU-specific action

Action phải khai báo:

```text
required_cpu_features
```

---

# 567.25. Baseline compilation

Native build phải xác định explicit CPU baseline.

---

# 567.26. Worker acceleration

Worker có CPU nhanh hơn không được tự ý bật ISA extension ngoài action contract.

---

# 567.27. GPU worker

GPU build/AI action phải khai báo:

```text
device_type
device_features
driver_identity
```

nếu output phụ thuộc chúng.

---

# 567.28. Action sandbox

```text
Sandbox
 ├── /input
 ├── /toolchain
 ├── /work
 └── /output
```

---

# 567.29. Input immutability

`/input` immutable.

---

# 567.30. Toolchain immutability

Toolchain mount immutable.

---

# 567.31. Output isolation

Output chỉ được publish sau validation.

---

# 567.32. Worker trust

Worker có thể là:

```text
LocalTrusted
RemoteTrusted
RemoteUntrusted
Ephemeral
```

---

# 567.33. Untrusted worker

Untrusted worker không được quyết định artifact correctness.

---

# 567.34. Verification

Coordinator verify:

```text
expected output hash
actual output hash
artifact schema
target
dependencies
```

---

# 567.35. Re-execution

Critical actions có thể chạy lại trên worker khác.

---

# 567.36. Differential worker validation

Có thể compare output từ hai workers.

---

# 567.37. Worker nondeterminism

Nếu cùng action tạo output hash khác nhau:

```text
NONDETERMINISTIC_ACTION
```

---

# 567.38. Nondeterminism quarantine

Action nondeterministic không được tự động đưa vào reproducible cache.

---

# 567.39. Determinism classification

```text
Deterministic
ConditionallyDeterministic
Nondeterministic
Unknown
```

---

# 567.40. Action DAG

```text
A
├── B
│   └── D
└── C
    └── D
```

D chỉ chạy sau khi dependencies valid.

---

# 567.41. DAG node identity

Node identity derived from ActionId.

---

# 567.42. DAG immutability

Build snapshot không mutate sau scheduling.

---

# 567.43. Scheduler

Scheduler tối ưu:

- dependency readiness;
- locality;
- worker capability;
- cache hit;
- bandwidth;
- cost;
- priority.

---

# 567.44. Scheduler correctness

Scheduling order không được ảnh hưởng semantics.

---

# 567.45. Critical path

Scheduler có thể ưu tiên critical-path actions.

---

# 567.46. Locality

Ưu tiên worker đã có required input artifacts.

---

# 567.47. Data transfer cost

Scheduler có thể tính estimated transfer cost.

---

# 567.48. Cache-aware scheduling

Nếu artifact đã có ở worker, action có thể chạy tại worker đó.

---

# 567.49. Remote cache lookup

Trước remote execution:

```text
lookup(ActionId)
```

---

# 567.50. Cache hit

Cache hit chỉ được accept sau validation.

---

# 567.51. Cache miss

Cache miss → schedule execution.

---

# 567.52. Cache race

Hai workers có thể cùng execute một ActionId.

Kết quả phải converge về cùng artifact identity.

---

# 567.53. Duplicate execution

Duplicate execution không được tạo semantic conflict.

---

# 567.54. Work stealing

Scheduler có thể work-steal ready actions.

---

# 567.55. Priority

Actions có priority nhưng priority không ảnh hưởng result.

---

# 567.56. Cancellation

Action cancellation không được invalidate already-valid artifacts.

---

# 567.57. Failure

Worker failure:

```text
retry
```

nếu action deterministic/retryable.

---

# 567.58. Retry policy

```text
Retryable
NonRetryable
Unknown
```

---

# 567.59. Worker timeout

Timeout không được coi là semantic failure.

---

# 567.60. Worker crash

Coordinator có thể reschedule action.

---

# 567.61. Worker disconnect

In-flight action trở thành:

```text
UNKNOWN
```

cho tới khi result verified.

---

# 567.62. Output transfer

Worker upload:

```text
ArtifactManifest
ArtifactChunks
IntegrityProof
```

---

# 567.63. Chunk transfer

Large artifacts có thể truyền theo chunks.

---

# 567.64. Chunk deduplication

Nếu destination đã có chunk hash:

```text
skip transfer
```

---

# 567.65. Parallel transfer

Independent chunks có thể transfer song song.

---

# 567.66. Transfer integrity

Mỗi chunk phải hash-check.

---

# 567.67. Whole-artifact integrity

Whole artifact phải hash-check sau assembly.

---

# 567.68. Merkle verification

Merkle root phải match artifact identity.

---

# 567.69. Compression

Transfer compression không được thay đổi artifact identity.

---

# 567.70. Encryption

Remote transport có thể encrypted.

---

# 567.71. Transport authentication

Remote build infrastructure có thể yêu cầu mutual authentication.

---

# 567.72. Authorization

Worker phải chỉ nhận actions mà principal có quyền thực thi.

---

# 567.73. Secret handling

Secrets không được embed trong ActionId.

---

# 567.74. Secret isolation

Secrets không được trở thành artifact output trừ khi explicitly declared.

---

# 567.75. Secret cache

Artifacts phụ thuộc secret không được đưa vào public/shared cache.

---

# 567.76. Private cache namespace

Private actions sử dụng private namespace.

---

# 567.77. Action metadata

```text
ActionMetadata {
    language
    compiler_phase
    source_context
    target
    estimated_cost
}
```

---

# 567.78. Build phases

Distributed actions có thể bao gồm:

```text
Frontend
Semantic
MIR
LTO
Codegen
Object
Link
Package
```

---

# 567.79. Frontend distribution

Các module độc lập có thể compile song song.

---

# 567.80. Semantic distribution

Demand-driven queries có thể distributed nếu snapshot immutable.

---

# 567.81. MIR distribution

Function/module MIR generation có thể parallelize.

---

# 567.82. LTO distribution

LTO actions có thể phân vùng theo SCC/function groups.

---

# 567.83. Codegen distribution

Machine code generation là distributed-friendly.

---

# 567.84. Object generation

Object artifacts được content-addressed.

---

# 567.85. Link distribution

Linker global layout thường cần coordinator.

Có thể parallelize các preprocessing/layout-independent phases.

---

# 567.86. Final linker authority

Final image phải có một deterministic final-link state.

---

# 567.87. Distributed linker

Có thể distribute:

- object scanning;
- symbol indexing;
- relocation preparation;
- section analysis.

Final layout/application vẫn phải deterministic.

---

# 567.88. Build action isolation

Một action không được mutate shared semantic state.

---

# 567.89. Shared state

Shared state chỉ qua:

- immutable artifacts;
- declared services;
- explicit synchronization.

---

# 567.90. Semantic snapshot

Mọi semantic worker phải bind snapshot fingerprint.

---

# 567.91. Snapshot mismatch

Worker result với snapshot khác request:

```text
REJECT
```

---

# 567.92. Compiler daemon

`555` daemon là coordinator tự nhiên cho distributed execution.

---

# 567.93. Query engine

`559/560` tạo demand-driven action dependencies.

---

# 567.94. Artifact layer

`565` cung cấp artifact transport/storage contract.

---

# 567.95. Cache layer

`566` quyết định cache hit/invalidation.

---

# 567.96. Build graph

`487` supplies high-level build DAG.

---

# 567.97. Distributed build graph

```text
BuildGraph
   ↓
CacheGraph
   ↓
ActionGraph
   ↓
WorkerSchedule
```

---

# 567.98. Action graph canonicalization

Cùng build snapshot phải tạo cùng logical action graph.

---

# 567.99. Graph determinism

Worker assignment không được là graph identity.

---

# 567.100. Reproducible build

```text
same inputs
+ same toolchain
+ same target
+ same policy
      ↓
same artifacts
```

---

# 567.101. Remote/local equivalence

Local execution và remote execution phải produce equivalent artifact.

---

# 567.102. Worker-independent result

Artifact không được chứa worker-specific metadata trong canonical semantic identity.

---

# 567.103. Worker metadata

Worker diagnostics có thể lưu riêng.

---

# 567.104. Build provenance

Build report có thể record worker IDs nhưng worker ID không thuộc semantic artifact identity.

---

# 567.105. Action result

```text
ActionResult {
    action_id
    outputs[]
    diagnostics
    execution_metadata
}
```

---

# 567.106. Output declaration

Action phải declare exact outputs.

---

# 567.107. Output validation

Coordinator validate output type.

---

# 567.108. Output schema

`.axsem`, `.axmir`, `.axlto`, `.axobj`, `.axdbg` phải validate bằng `565`.

---

# 567.109. Native output

Executable output phải validate bằng `564`.

---

# 567.110. Malformed output

Worker result malformed → reject.

---

# 567.111. Artifact substitution

Artifact content hash mismatch → reject.

---

# 567.112. Action substitution

Worker cannot replace requested action with another action.

---

# 567.113. Command identity

Command/tool invocation identity must be explicit.

---

# 567.114. Tool invocation

No hidden shell aliases/functions.

---

# 567.115. Shell environment

Default worker action should invoke tools directly, not through arbitrary host shell.

---

# 567.116. Filesystem isolation

Symlink behavior phải deterministic.

---

# 567.117. File metadata

mtime/ctime/inode không được ảnh hưởng output nếu reproducibility yêu cầu.

---

# 567.118. Directory ordering

Input enumeration phải canonicalized.

---

# 567.119. Locale

Compiler actions phải use explicit locale.

---

# 567.120. Unicode normalization

Nếu filesystem semantics phụ thuộc Unicode normalization, action phải specify policy.

---

# 567.121. Timezone

Timezone phải explicit nếu action cần.

---

# 567.122. Host architecture

Host architecture không được ảnh hưởng target compilation.

---

# 567.123. Cross compiler

Remote worker có thể compile target khác host.

---

# 567.124. Target SDK

SDK phải có content identity.

---

# 567.125. Sysroot

Sysroot phải immutable/content-addressed.

---

# 567.126. Runtime

Runtime artifact phải content-addressed.

---

# 567.127. Package dependencies

Dependencies phải resolve trước action execution.

---

# 567.128. Package lock

Lockfile identity là action input.

---

# 567.129. Build configuration

Build profile là action input.

---

# 567.130. Feature gates

Language features là action input.

---

# 567.131. Optimization

Optimization configuration là action input khi relevant.

---

# 567.132. PGO

PGO profile artifact là explicit input.

---

# 567.133. Debug

Debug configuration là explicit input.

---

# 567.134. Sanitizer

Sanitizer configuration là explicit input.

---

# 567.135. Security policy

Security/hardening policy là explicit input.

---

# 567.136. Network policy

Network permission là action identity input.

---

# 567.137. Resource policy

Memory/CPU limits có thể affect success/performance nhưng không được silently affect semantics.

---

# 567.138. Worker memory

Worker memory thấp có thể fail action, không được tạo output khác.

---

# 567.139. Worker CPU count

Worker CPU count không được alter deterministic result.

---

# 567.140. Parallelism

Action nội bộ chạy 1 hay 64 threads phải produce equivalent result.

---

# 567.141. Floating point

Nếu FP result phụ thuộc contraction/reduction order, compiler policy phải explicit.

---

# 567.142. SIMD

Worker SIMD features chỉ được dùng nếu target/action cho phép.

---

# 567.143. Non-deterministic hardware

Hardware-specific non-determinism phải be controlled hoặc action marked nondeterministic.

---

# 567.144. GPU

GPU kernel compilation phải bind device/compiler versions khi output phụ thuộc.

---

# 567.145. AI compilation

AI graph compilation có thể distributed nhưng model/artifact hashes phải explicit.

---

# 567.146. Remote AI worker

Model weights phải content-addressed.

---

# 567.147. Artifact provenance

Remote action result phải preserve provenance từ `565`.

---

# 567.148. Correctness evidence

`552` evidence phải được attach/bind với exact action/output.

---

# 567.149. Optimization evidence

`553` evidence phải survive remote execution.

---

# 567.150. Build audit

Coordinator có thể generate:

```text
BuildAudit {
    actions
    workers
    cache_hits
    cache_misses
    artifacts
    provenance
}
```

---

# 567.151. Action tracing

Build trace phải support:

```text
queued
ready
running
uploading
verifying
completed
failed
```

---

# 567.152. Trace determinism

Trace timing không thuộc artifact identity.

---

# 567.153. Build UI

IDE/LSP có thể display distributed build progress.

---

# 567.154. AI observability

AI có thể query:

```text
build status
worker status
action graph
cache status
why rebuilt
```

---

# 567.155. Worker health

Scheduler theo dõi:

- availability;
- failure rate;
- latency;
- bandwidth.

---

# 567.156. Health does not affect semantics

Worker ranking chỉ ảnh hưởng execution strategy.

---

# 567.157. Worker admission

Worker phải pass protocol/version compatibility.

---

# 567.158. Protocol version

Distributed protocol version độc lập artifact schema.

---

# 567.159. Protocol negotiation

Client/worker negotiate supported protocol.

---

# 567.160. Capability mismatch

Action được reschedule nếu worker không đủ capability.

---

# 567.161. Worker registration

Worker đăng ký:

```text
worker_id
protocol
capabilities
toolchains
trust_level
```

---

# 567.162. Worker heartbeat

Heartbeat failure không imply artifact failure.

---

# 567.163. Worker draining

Worker có thể chuyển sang `DRAINING`, không nhận action mới.

---

# 567.164. Worker shutdown

In-flight actions phải finish/retry/recover.

---

# 567.165. Coordinator restart

Build state phải recover từ persisted ActionGraph/Artifact state.

---

# 567.166. Distributed checkpoint

Long build có thể checkpoint completed actions.

---

# 567.167. Checkpoint identity

Checkpoint bind BuildSnapshot fingerprint.

---

# 567.168. Checkpoint invalidation

Snapshot mismatch → checkpoint stale.

---

# 567.169. Network partition

Build có thể tiếp tục local nếu dependencies available.

---

# 567.170. Offline mode

```text
distributed = disabled
remote_cache = disabled
```

vẫn build được từ local inputs.

---

# 567.171. Air-gapped mode

Remote network hoàn toàn disabled.

---

# 567.172. Reproducible CI

CI có thể require:

```text
hermetic = true
remote_cache = trusted
network = false
```

---

# 567.173. Untrusted cache

Có thể dùng artifact nếu hash/schema validation pass nhưng security policy có thể yêu cầu re-execution.

---

# 567.174. Verified execution

Critical build có thể:

```text
cache result
     ↓
independent verification
```

---

# 567.175. Double execution

Security-critical artifacts có thể build twice trên independent workers.

---

# 567.176. Mismatch handling

Hai output khác nhau:

```text
BUILD_INCONSISTENCY
```

và artifact không được promote.

---

# 567.177. Worker compromise

Một compromised worker chỉ có thể ảnh hưởng những outputs nó tạo ra; coordinator verification phải chặn artifact giả.

---

# 567.178. Sandbox escape

Worker runtime phải isolate filesystem/process/network theo platform security model.

---

# 567.179. Resource exhaustion

Coordinator phải giới hạn:

- input size;
- output size;
- decompression;
- memory;
- CPU;
- execution time.

---

# 567.180. Malicious build action

Action từ untrusted project phải được sandbox theo trust policy.

---

# 567.181. Build script security

Build scripts không được mặc định có quyền ngang compiler daemon.

---

# 567.182. Plugin worker

Third-party compiler plugins chạy trong explicit trust boundary.

---

# 567.183. Foreign tool

Foreign tool identity và permissions phải declared.

---

# 567.184. Cache poisoning defense

Only verified ActionResult can enter shared cache.

---

# 567.185. Cache namespace

Shared cache phải isolate incompatible toolchains/policies.

---

# 567.186. Artifact garbage collection

Distributed cache GC phải preserve globally referenced artifacts.

---

# 567.187. Reference tracking

Remote store có thể dùng leases/pins/content graph.

---

# 567.188. Transfer retry

Chunk transfer retry phải idempotent.

---

# 567.189. Publish idempotency

Publish cùng ArtifactId nhiều lần phải safe.

---

# 567.190. Action idempotency

Deterministic action có thể execute nhiều lần mà không tạo semantic conflict.

---

# 567.191. Atomic result publication

ActionResult chỉ commit khi toàn bộ outputs verified.

---

# 567.192. Partial result

Partial outputs có thể remain temporary nhưng không visible như valid cache.

---

# 567.193. Build completion

Build chỉ `SUCCESS` khi final artifact validated.

---

# 567.194. Build failure

Một failed optional action chỉ fail build nếu dependency graph yêu cầu output đó.

---

# 567.195. Optional artifacts

Debug/profile artifacts có thể be optional.

---

# 567.196. Required artifacts

Native executable/link artifacts required by requested build phải complete.

---

# 567.197. Distributed test suite

Phải test:

- local/remote equivalence;
- worker crash;
- retry;
- duplicate execution;
- cache poisoning;
- network partition;
- deterministic output;
- snapshot mismatch;
- malformed worker response;
- partial transfer;
- coordinator restart.

---

# 567.198. Stress test

Test project với:

- hàng nghìn modules;
- hàng triệu actions;
- large artifacts;
- high worker count;
- high cache hit rate;
- high cache miss rate.

---

# 567.199. End-to-end validation

```text
clean local
clean distributed
warm local
warm remote
parallel local
parallel distributed
```

phải đạt equivalence.

---

# 567.200. HARD INVARIANTS

1. Action identity phải deterministic.
2. Action identity không phụ thuộc worker.
3. Action identity không phụ thuộc hostname.
4. Action identity không phụ thuộc PID.
5. Action identity không phụ thuộc timestamp.
6. Action identity không phụ thuộc filesystem inode.
7. Input identity phải content-addressed.
8. Toolchain identity phải content-addressed.
9. Target identity phải explicit.
10. ABI identity phải explicit.
11. Build configuration phải explicit.
12. Security policy phải explicit.
13. Optimization configuration phải explicit.
14. PGO input phải explicit.
15. Debug configuration phải explicit.
16. Sanitizer configuration phải explicit.
17. Language edition phải explicit.
18. Feature gates phải explicit.
19. Package lock phải explicit.
20. Sysroot phải explicit.
21. SDK phải explicit.
22. Runtime phải explicit.
23. Environment dependencies phải explicit.
24. Network dependencies phải explicit.
25. Undeclared filesystem input không được ảnh hưởng hermetic action.
26. Undeclared environment không được ảnh hưởng hermetic action.
27. Undeclared network input không được ảnh hưởng hermetic action.
28. Worker không được tự ý thay đổi action semantics.
29. Worker không được tự ý bật CPU features.
30. Worker không được tự ý chọn target.
31. Worker không được tự ý thay đổi ABI.
32. Worker không được tự ý thay đổi optimization semantics.
33. Worker không được tự ý thay đổi security policy.
34. Worker không được tự ý add build inputs.
35. Worker không được tự ý publish undeclared outputs.
36. Input filesystem phải immutable.
37. Toolchain phải immutable.
38. Output phải isolated.
39. Output phải validate.
40. Output hash phải verify.
41. Artifact schema phải verify.
42. Target phải verify.
43. ABI phải verify.
44. Dependency graph phải verify.
45. Provenance phải preserve.
46. Correctness evidence phải preserve.
47. Optimization evidence phải preserve.
48. Remote cache artifact phải validate.
49. Remote cache không được quyết định correctness.
50. Remote cache miss không phải build error.
51. Remote cache corruption phải detectable.
52. Cache poisoning phải detectable.
53. Cache hit phải equivalent clean execution.
54. Local execution phải equivalent remote execution.
55. Remote execution phải equivalent local execution.
56. Worker assignment không được ảnh hưởng result.
57. Worker scheduling không được ảnh hưởng result.
58. Worker count không được ảnh hưởng result.
59. Worker CPU count không được ảnh hưởng result.
60. Worker memory chỉ có thể ảnh hưởng success/failure, không được tạo output sai.
61. Duplicate action execution phải safe.
62. Action result publication phải atomic.
63. Partial output không được valid cache.
64. Worker crash phải recoverable.
65. Worker disconnect phải recoverable.
66. Worker timeout phải recoverable.
67. Coordinator restart phải recoverable.
68. Network partition không được phá local correctness.
69. Offline mode phải remain functional.
70. Air-gapped mode phải remain functional.
71. Distributed build phải support cross compilation.
72. Host architecture không được implicit target.
73. Host environment không được implicit build input.
74. Host locale không được implicit semantic input.
75. Host timezone không được implicit semantic input.
76. Host wall-clock không được implicit semantic input.
77. File timestamps không được implicit semantic input.
78. Directory ordering phải deterministic.
79. Path normalization phải deterministic.
80. Unicode path handling phải deterministic.
81. Symlink policy phải explicit.
82. Path traversal phải prevented.
83. Sandbox boundaries phải explicit.
84. Network permissions phải explicit.
85. Resource limits phải explicit.
86. Secrets không được đưa vào ActionId.
87. Secrets không được public-cache.
88. Secret-dependent artifacts phải obey trust policy.
89. Untrusted worker output phải undergo verification.
90. Trusted worker output vẫn phải structural validation.
91. Signature không thay thế artifact validation.
92. Hash không thay thế semantic validation.
93. Semantic validation không thay thế security policy.
94. Security policy không thay đổi compiler semantics silently.
95. Non-deterministic action không được vào reproducible cache.
96. Conditionally deterministic action phải declare condition.
97. Randomness phải deterministic hoặc explicit.
98. Floating-point nondeterminism phải be controlled/declared.
99. GPU nondeterminism phải be controlled/declared.
100. CPU-specific codegen phải bind CPU feature set.
101. GPU codegen phải bind relevant device/compiler identity.
102. SDK-dependent action phải bind SDK identity.
103. Sysroot-dependent action phải bind sysroot identity.
104. Runtime-dependent action phải bind runtime identity.
105. Foreign tool output phải bind tool identity.
106. Build-script output phải bind script identity.
107. Generated source phải bind generator identity.
108. Comptime result phải bind input identity.
109. Package dependency phải bind exact content identity.
110. Lockfile changes phải affect relevant action identities.
111. Action DAG phải be snapshot-bound.
112. Build snapshot phải immutable.
113. Snapshot mismatch phải reject cached action results.
114. Action graph phải be deterministic.
115. Dependency edges phải explicit.
116. Action scheduling must respect dependency readiness.
117. Scheduler optimization must not alter semantics.
118. Critical-path prioritization must not alter semantics.
119. Locality optimization must not alter semantics.
120. Bandwidth optimization must not alter semantics.
121. Work stealing must not alter semantics.
122. Prefetch must not alter semantics.
123. Speculative execution must not alter semantics.
124. Cancellation must not invalidate committed artifacts.
125. Retry must not alter deterministic output.
126. Duplicate execution must converge.
127. Action outputs must have declared types.
128. Action outputs must have declared paths.
129. Output hashes must be deterministic.
130. Chunk hashes must be deterministic.
131. Merkle roots must be deterministic.
132. Compression must not alter artifact identity.
133. Encryption must not alter artifact identity.
134. Transport protocol must not alter artifact identity.
135. Artifact store must be content-addressed.
136. Remote store must preserve artifact IDs.
137. Artifact transfer must preserve provenance.
138. Artifact extraction must preserve provenance.
139. Cache promotion must require validation.
140. Shared-cache promotion must satisfy trust policy.
141. Cache GC must not delete active artifacts.
142. Cache GC must not delete pinned artifacts.
143. Cache GC must not delete leased artifacts.
144. Cache eviction must not alter build semantics.
145. Cache purge must not alter build semantics.
146. Build must be correct with zero cache.
147. Build must be correct with all cache.
148. Build must be correct with partial cache.
149. Build must be correct with corrupt cache.
150. Corrupt cache must trigger recovery.
151. Cache miss must trigger valid recomputation.
152. Cache hit must bypass unnecessary recomputation.
153. Incremental dependency analysis must remain authoritative.
154. Distributed graph must integrate `566`.
155. Distributed artifacts must integrate `565`.
156. Distributed actions must integrate `555`.
157. Distributed build graph must integrate `487`.
158. Distributed linker must integrate `564`.
159. Machine code actions must integrate `561/562`.
160. Correctness checking must integrate `552`.
161. Optimization actions must integrate `553`.
162. AI queries must integrate artifact provenance.
163. AI cannot override action identity.
164. AI cannot override dependency identity.
165. AI cannot override security policy.
166. Build diagnostics must identify worker/action failures.
167. Cache diagnostics must distinguish miss/corruption/stale.
168. Distributed diagnostics must distinguish worker failure/action failure.
169. Worker failure must not be reported as source error.
170. Source error must not be reported as worker error.
171. Toolchain mismatch must be distinguishable from source error.
172. Target mismatch must be distinguishable from worker capability mismatch.
173. Security rejection must be distinguishable from compilation failure.
174. Network failure must be distinguishable from action failure.
175. Artifact corruption must be distinguishable from action failure.
176. Build audit must reconstruct action provenance.
177. Build audit must reconstruct artifact provenance.
178. Build audit must reconstruct cache decisions.
179. Build audit must reconstruct worker execution.
180. Build audit metadata must not alter canonical artifact identity.
181. Remote execution must support reproducibility audits.
182. Independent workers must be able to verify critical artifacts.
183. Differential workers must detect nondeterministic outputs.
184. Mismatch artifacts must not be promoted.
185. Malformed worker messages must not crash coordinator.
186. Malformed artifacts must not crash worker/coordinator.
187. Resource exhaustion must be bounded.
188. Recursive input structures must be bounded.
189. Decompression must be bounded.
190. Transfer size must be bounded.
191. Action output size must be bounded by policy.
192. Worker sandbox escape must not expose coordinator trust boundary.
193. Third-party build scripts must have explicit trust.
194. Foreign tools must have explicit trust.
195. Distributed protocol version must be negotiated.
196. Artifact schema version must be independently negotiated.
197. Toolchain version must be independently validated.
198. All distributed and local execution paths must converge on the same semantic authority.
199. The entire system must preserve correctness across clean, incremental, cached, remote, parallel, retry and offline builds.
200. **Final invariant:** Distributed execution chỉ là một phương thức thực thi. Với cùng `BuildSnapshot + ActionInputs + Toolchain + Target + Policy`, Axiom phải tạo ra cùng logical artifacts bất kể action chạy trên local CPU, một remote worker, nhiều worker, worker khác nhau, cache hit hay cache miss; worker không bao giờ được trở thành semantic authority.

**BOOTSTRAP-567: LOCKED.**

---

# NEXT — BOOTSTRAP-568

## COMPILER BUILD ORCHESTRATOR 3.0 — DAG EXECUTION ENGINE, SPECULATIVE COMPILATION, CRITICAL-PATH SCHEDULING, RESOURCE-AWARE PARALLELISM & ADAPTIVE BUILD

`567` đã tạo nền distributed worker. `568` sẽ đi sâu vào **execution engine của Build DAG** — tức bộ não quyết định *thứ tự nào chạy trước, chạy song song đến đâu, khi nào speculative execution có lợi, khi nào dừng, và làm sao đạt tốc độ compile tối đa mà vẫn deterministic*.

Kiến trúc dự kiến:

```text
                 Build Snapshot
                       │
                       ▼
                Semantic Query DAG
                       │
                       ▼
               ┌───────────────┐
               │ DAG Analyzer  │
               └───────┬───────┘
                       │
             ┌─────────┼─────────┐
             ▼         ▼         ▼
          Critical   Resource   Cache
           Path       Model      State
             │         │         │
             └─────────┼─────────┘
                       ▼
                 Smart Scheduler
                       │
        ┌──────────────┼──────────────┐
        ▼              ▼              ▼
    Local CPU       Remote CPU       GPU
        │              │              │
        └──────────────┼──────────────┘
                       ▼
                Verified Results
                       │
                       ▼
                 Artifact Store
```

`568` sẽ khóa đặc biệt:

- dependency-ready scheduling;
- critical-path analysis;
- work stealing;
- resource-aware scheduling;
- memory-aware scheduling;
- CPU/GPU scheduling;
- speculative execution;
- cancellation;
- action batching;
- query batching;
- compilation locality;
- NUMA awareness;
- worker affinity;
- adaptive parallelism;
- starvation/deadlock prevention;
- priority inheritance;
- incremental rebuild scheduling;
- interactive IDE priority;
- CI throughput mode;
- low-latency single-file mode;
- deterministic scheduler semantics;
- scheduler observability;
- build-time prediction;
- cost model integration với `553/566/567`;
- và cách Axiom đạt **maximum parallelism nhưng không biến compiler thành một hệ thống phức tạp khó kiểm soát**.

**BOOTSTRAP-568: NEXT.**