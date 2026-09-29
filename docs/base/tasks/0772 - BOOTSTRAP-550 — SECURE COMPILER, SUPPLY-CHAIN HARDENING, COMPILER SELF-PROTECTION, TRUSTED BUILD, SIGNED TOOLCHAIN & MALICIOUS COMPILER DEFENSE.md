# BOOTSTRAP-550 — SECURE COMPILER, SUPPLY-CHAIN HARDENING, COMPILER SELF-PROTECTION, TRUSTED BUILD, SIGNED TOOLCHAIN & MALICIOUS COMPILER DEFENSE

**Trạng thái: COMPLETED / LOCKED**

## 550.1. Mục tiêu

`550` bảo vệ **chính toolchain Axiom** khỏi việc trở thành điểm yếu của toàn bộ chuỗi tin cậy.

```text
Source
   ↓
Package / Dependency
   ↓
Compiler + SDK + Build Tools
   ↓
Object / Executable
   ↓
Deployment
   ↓
Runtime
```

Nguyên tắc trung tâm:

> **Compiler security không được dựa vào việc compiler tự tuyên bố rằng nó an toàn.**

Trust phải đến từ:

```text
independent evidence
+ reproducibility
+ signatures
+ provenance
+ bootstrap verification
+ controlled inputs
```

---

# 550.2. Threat model

Các mối đe dọa chính:

```text
Compromised compiler
Compromised SDK
Compromised package
Malicious build script
Poisoned cache
Tampered source
Tampered artifact
Malicious plugin
Compromised signing key
Compromised build worker
Hostile environment
```

Compiler phải phân biệt:

```text
Trusted
Verified
Signed
Reproducible
Audited
Unknown
```

Các khái niệm này **không đồng nghĩa**.

---

# 550.3. Toolchain identity

Mỗi toolchain có:

```text
ToolchainIdentity {
    compiler_id
    compiler_version
    compiler_build_id
    compiler_hash

    stdlib_id
    stdlib_hash

    sdk_id
    sdk_version
    sdk_hash

    target
    schema_versions
}
```

Identity được đưa vào build provenance.

---

# 550.4. Compiler artifact

Compiler bản thân là native artifact bình thường:

```text
Axiom Compiler
 ├── executable
 ├── semantic metadata
 ├── version manifest
 ├── provenance
 └── signature
```

Không có trạng thái đặc biệt kiểu:

```text
compiler == inherently trusted
```

---

# 550.5. Compiler provenance

Compiler build phải ghi:

```text
CompilerProvenance {
    source_revision
    source_hash
    bootstrap_stage
    bootstrap_compiler
    dependencies
    sdk
    target
    build_config
    build_environment
    artifact_hash
}
```

---

# 550.6. Hermetic compiler build

Compiler release build ưu tiên:

```text
Source
 + locked dependencies
 + pinned toolchain
 + pinned SDK
 + declared environment
 → deterministic artifact
```

Không được phụ thuộc ngầm vào:

- PATH;
- local compiler;
- user home;
- random environment;
- current clock;
- undeclared files;
- undeclared network.

---

# 550.7. Compiler capability manifest

Compiler/build tool có capability manifest:

```text
CompilerCapabilities {
    filesystem
    network
    process
    environment
    native_execution
    signing
    target_sdk
}
```

Trong build phase, capability phải explicit.

---

# 550.8. Compiler không tự có quyền signing

Đặc biệt:

```text
Compiler
    ✕
    signing key
```

Signing nên là boundary riêng:

```text
Build
 ↓
Unsigned Artifact
 ↓
Verification
 ↓
Signing Service / Tool
 ↓
Signed Artifact
```

Compiler không được tự lấy private key từ environment.

---

# 550.9. Signing identity

Artifact signature chứa:

```text
Signature {
    artifact_hash
    signer
    key_id
    algorithm
    signature
    timestamp?
    certificate_chain?
}
```

Timestamp không phải thành phần bắt buộc nếu deterministic artifact identity cần giữ.

---

# 550.10. Signature ≠ correctness

Một compiler được ký hợp lệ vẫn có thể:

```text
miscompile
contain bug
be malicious
```

Do đó:

```text
Signed
    ≠
Correct
```

---

# 550.11. Reproducible compiler build

Mục tiêu:

```text
same source
+ same dependencies
+ same toolchain
+ same configuration
+ same target
→ same artifact
```

Nếu byte-for-byte reproducibility không khả thi trên target nào đó, phải ghi rõ phần nondeterministic.

---

# 550.12. Reproducibility evidence

Kết quả:

```text
ReproducibilityResult {
    expected_hash
    observed_hash
    build_identity
    environment_identity
    status
    differences[]
}
```

Status:

```text
Reproduced
NotReproduced
Inconclusive
```

Không được biến `Inconclusive` thành `Reproduced`.

---

# 550.13. Bootstrap trust

Tích hợp `482/488`:

```text
Stage0
 ↓
Stage1
 ↓
Stage2
 ↓
StageN
```

Mỗi stage có provenance.

---

# 550.14. Diverse double compilation

Axiom hỗ trợ phương pháp:

```text
Compiler A
   ↓
compile Compiler B source
   ↓
Compiler B
   ↓
compile target
```

Sau đó so sánh artifact.

Mục tiêu là giảm nguy cơ compiler seed chứa backdoor.

---

# 550.15. Bootstrap comparison

So sánh:

```text
binary hash
sections
symbols
machine code
metadata
behavioral tests
semantic outputs
```

Không chỉ so hash.

---

# 550.16. Compiler self-check

Compiler có thể kiểm tra:

```text
compiler identity
embedded build id
metadata schema
runtime components
```

Nhưng self-check chỉ là evidence phụ.

Compiler không được tự cấp:

```text
trusted = true
```

cho chính mình.

---

# 550.17. External verification

Trust root nên hỗ trợ:

```text
Independent verifier
Independent build
Independent signature verification
```

Verifier có thể là tool nhỏ hơn compiler.

---

# 550.18. Minimal verifier

Axiom nên cung cấp một verifier tối giản có thể kiểm tra:

```text
artifact hash
manifest
signature
provenance
target
dependency identity
```

Verifier không cần compile Axiom.

Mục tiêu:

```text
small verifier
→ easier audit
```

---

# 550.19. SDK trust

Target SDK `483` có:

```text
SDKManifest {
    sdk_id
    version
    target
    sysroot_hash
    headers_hash
    libraries[]
    frameworks[]
    startup_objects[]
    linker_metadata[]
    signature
}
```

Compiler phải kiểm tra compatibility.

---

# 550.20. SDK tampering

Nếu:

```text
SDK hash != expected hash
```

build có thể:

```text
reject
```

theo security policy.

Không được silently tiếp tục trong strict mode.

---

# 550.21. Package trust

Package từ `491/492` phải phân biệt:

```text
source identity
artifact identity
publisher identity
signature
provenance
```

Package compile được không có nghĩa package trusted.

---

# 550.22. Malicious build scripts

Build scripts là execution boundary.

Mặc định:

```text
Build Script
    ↓
sandbox / declared capabilities
```

Capabilities:

```text
filesystem
network
process
environment
compiler
generated-output
```

---

# 550.23. Build script authority

Build script chỉ được:

```text
read declared inputs
write declared outputs
use declared capabilities
```

Không được tự động:

```text
scan home directory
read credentials
modify arbitrary source
contact arbitrary network
```

---

# 550.24. Build-script reproducibility

Build script phải khai báo:

```text
inputs
outputs
tools
environment
network
```

Hermetic mode có thể reject undeclared behavior.

---

# 550.25. Generated code provenance

Generated source phải giữ:

```text
generator_id
generator_version
input_hash
configuration_hash
output_hash
```

Từ đó:

```text
GeneratedCode
    ↓
Origin
```

có thể truy ngược.

---

# 550.26. Compiler plugin security

Compiler plugin không được mặc định chạy trong compiler process.

Ưu tiên:

```text
Compiler
   ↓
Plugin protocol
   ↓
isolated process
```

In-process plugin chỉ dành cho explicitly trusted extensions.

---

# 550.27. Plugin ABI

Plugin identity:

```text
PluginIdentity {
    name
    version
    abi_version
    compiler_version_range
    target
    capabilities
    hash
    signature?
}
```

---

# 550.28. Plugin capability

Plugin phải khai báo quyền:

```text
filesystem
network
process
compiler_database
source_mutation
code_generation
```

Không có ambient access.

---

# 550.29. Compiler database protection

Semantic DB có thể chứa:

```text
source
private APIs
security metadata
credentials metadata
dependency information
```

Plugin không được mặc định có full access.

API nên phân tầng:

```text
read-only semantic
restricted mutation
trusted compiler-internal
```

---

# 550.30. Cache poisoning

`487` cache là correctness-critical.

Cache entry phải chứa:

```text
CacheEntry {
    key
    artifact_hash
    compiler_identity
    schema_version
    target
    configuration
    provenance
}
```

Cache hit phải verify integrity.

---

# 550.31. False cache hit

Nếu cùng key nhưng artifact không đúng hash:

```text
CACHE-INTEGRITY-ERROR
```

Không được sử dụng artifact.

---

# 550.32. Remote cache trust

Remote cache:

```text
untrusted transport
```

Artifact phải verify:

```text
hash
provenance
toolchain identity
target
schema
```

trước khi dùng.

---

# 550.33. Remote execution trust

Worker identity:

```text
Worker {
    worker_id
    platform
    target
    toolchain
    sdk
    capabilities
    sandbox
}
```

Scheduler không gửi secret tùy tiện tới worker.

---

# 550.34. Worker isolation

Remote worker nên:

```text
sandbox
filesystem isolation
network policy
resource limits
process isolation
```

Mức isolation phụ thuộc deployment.

---

# 550.35. Build secret isolation

Secret không được trở thành:

```text
build input
cache key
artifact
log
provenance
```

trừ khi explicit.

Nếu build thật sự phụ thuộc secret thì reproducibility phải được đánh dấu phù hợp.

---

# 550.36. Environment poisoning

Các biến môi trường ảnh hưởng compilation phải:

```text
declared
captured
hashed
```

hoặc bị cấm trong hermetic mode.

---

# 550.37. PATH poisoning

Compiler không được âm thầm chọn:

```text
gcc
clang
link.exe
python
custom tool
```

từ PATH.

Tool dependency phải có identity rõ ràng.

---

# 550.38. Third-party compiler detection

Production Axiom native build có thể xuất dependency graph:

```text
CompilerCodegenDependencyGraph
```

Strict policy:

```text
no forbidden compiler
```

Nếu compiler external được dùng cho một phase:

```text
explicit external tool node
```

---

# 550.39. Linker trust

Axiom linker `420` cũng thuộc trust chain.

```text
Compiler
 ↓
Object
 ↓
Axiom Linker
 ↓
Artifact
```

Không chỉ compiler executable được verify.

---

# 550.40. Object verifier

Object file cần kiểm tra:

```text
sections
symbols
relocations
architecture
ABI
permissions
alignment
entry point
```

trước linker.

---

# 550.41. Native artifact verification

Artifact verifier kiểm tra:

```text
target
entry point
section layout
imports
exports
permissions
signature
provenance
```

Có thể phát hiện:

```text
unexpected executable section
unexpected dependency
unexpected import
```

---

# 550.42. Dependency confusion

Resolver `492` phải kết hợp:

```text
package identity
source identity
registry
publisher
namespace
lockfile
```

Package cùng tên nhưng khác source không được silently thay thế.

---

# 550.43. Package takeover

Lockfile phải giữ:

```text
exact source
exact version
checksum
artifact identity
```

Thay đổi publisher/source phải tạo explicit change.

---

# 550.44. Dependency substitution

Build system không được tự đổi:

```text
package A
```

sang:

```text
package A'
```

chỉ vì cùng version.

Source identity là một phần dependency identity.

---

# 550.45. Toolchain update

Toolchain update:

```text
download
 ↓
verify
 ↓
stage
 ↓
test
 ↓
activate
```

Không overwrite active toolchain trực tiếp.

---

# 550.46. Rollback

Nếu toolchain mới lỗi:

```text
previous verified toolchain
```

phải còn khả năng khôi phục.

---

# 550.47. Toolchain channels

Ví dụ:

```text
stable
preview
nightly
custom
```

Channel không phải version.

Active toolchain phải pin exact version trong reproducible build.

---

# 550.48. Toolchain revocation

Một compiler/SDK có thể bị:

```text
revoked
withdrawn
blocked
```

Policy có thể ngăn build mới bằng artifact bị revoked.

Artifact đã tồn tại không tự động biến mất.

---

# 550.49. Security advisory

Toolchain advisory có:

```text
Advisory {
    affected_versions
    fixed_versions
    affected_targets
    affected_components
    severity
    evidence
    remediation
}
```

Không dùng một universal security score.

---

# 550.50. Compiler vulnerability impact

Compiler vulnerability phải có impact graph:

```text
Compiler Version
   ↓
Affected Builds
   ↓
Artifacts
   ↓
Deployments
   ↓
Runtime
```

Tích hợp `546/548`.

---

# 550.51. Miscompilation tracking

Một compiler bug có thể ảnh hưởng artifact.

Axiom cần:

```text
CompilerBug
 → affected compiler versions
 → affected source patterns
 → affected artifacts
```

Nếu có rule đủ chính xác, analyzer có thể xác định affected builds.

---

# 550.52. Miscompilation evidence

Không tuyên bố:

```text
compiler X is safe
```

Mà ghi:

```text
tested properties
test suite
target
configuration
compiler version
known limitations
```

---

# 550.53. Compiler differential testing

Compiler có thể so sánh:

```text
Stage1
Stage2
reference interpreter
independent backend
```

khi semantics cho phép.

---

# 550.54. Reference interpreter

Một subset semantic interpreter có thể dùng làm oracle:

```text
Axiom source
 ↓
Semantic IR
 ↓
Reference execution
```

So với native execution.

Không phải production runtime.

---

# 550.55. Compiler fuzzing

Fuzz các boundary:

```text
lexer
parser
type checker
comptime
trait solver
MIR
optimizer
codegen
object writer
linker
debug info
package resolver
build graph
```

---

# 550.56. Security fuzzing

Đặc biệt fuzz:

```text
malformed package
malformed object
malformed metadata
malformed SDK
malicious build manifest
plugin protocol
cache metadata
registry metadata
```

---

# 550.57. Compiler crash handling

Compiler crash phải tạo:

```text
CompilerCrashReport {
    compiler_build_id
    source_hash
    target
    phase
    query
    stack
    minimized_input?
}
```

Không tự động upload.

---

# 550.58. Crash privacy

Source có thể chứa proprietary code.

Do đó report mặc định có:

```text
hashes
symbols where safe
minimal diagnostics
```

và source upload là explicit.

---

# 550.59. Compiler process isolation

Một project build không nên mặc định có khả năng phá:

```text
user compiler installation
other projects
toolchain cache
credentials
```

Build worker nên được giới hạn.

---

# 550.60. Compiler state immutability

Installed toolchain nên được coi là immutable:

```text
Toolchain
   ↓
read-only
```

Cache/output nằm ngoài installation.

---

# 550.61. Atomic installation

Toolchain install:

```text
download
→ verify
→ unpack temporary
→ verify contents
→ activate atomically
```

Partial toolchain không được trở thành active toolchain.

---

# 550.62. Secure deletion

Không yêu cầu compiler tự xóa mọi dữ liệu nhạy cảm.

Data lifecycle thuộc policy/storage.

Compiler chỉ phải tránh:

```text
secret → logs/cache/artifact
```

khi metadata đánh dấu sensitive.

---

# 550.63. Compiler telemetry

Không có:

```text
hidden compiler telemetry
```

Compiler network access phải explicit.

---

# 550.64. Offline compiler

Axiom phải hỗ trợ:

```text
offline build
offline verify
offline cache
offline toolchain installation
```

nếu toàn bộ dependencies đã có.

---

# 550.65. Air-gapped environment

Có thể đóng gói:

```text
Toolchain
SDK
Packages
Registry mirror
Cache
Trust roots
Verification tools
```

thành offline bundle.

---

# 550.66. Trust root

Trust root gồm:

```text
RootKey
TrustedCompiler
TrustedSDK
TrustedRegistry
TrustedPublisher
TrustedVerifier
```

Không nhất thiết tất cả phải cùng một root.

---

# 550.67. Trust graph

```text
Trust Root
   ├── Compiler
   ├── SDK
   ├── Package
   ├── Model
   ├── Dataset
   └── Deployment
```

Mỗi edge có:

```text
issuer
claim
evidence
time
scope
```

---

# 550.68. Claim types

Không dùng một boolean:

```text
trusted = true
```

Thay vào đó:

```text
Signed
VerifiedHash
Reproducible
Audited
PolicyApproved
KnownSource
KnownCompiler
```

---

# 550.69. Evidence composition

Một artifact có thể:

```text
signed = true
reproducible = true
security_scan = unknown
```

Không được biến thành:

```text
secure = true
```

---

# 550.70. Compiler security manifest

Mỗi build có thể xuất:

```text
CompilerSecurityManifest {
    compiler
    sdk
    dependencies
    build_scripts
    plugins
    cache_sources
    remote_workers
    signatures
    verification_results
    unknowns
}
```

---

# 550.71. AI query interface

AI tooling có thể hỏi:

```text
why_compiler_trusted()
what_compiler_built_this()
what_dependencies_were_used()
was_build_reproducible()
was_cache_verified()
which_build_scripts_ran()
what_capabilities_did_they_have()
which_plugins_loaded()
what_sdk_was_used()
what_external_tools_were_used()
show_bootstrap_chain()
show_trust_root()
show_unknowns()
```

---

# 550.72. Compiler security graph

Tích hợp:

```text
Source
 ↓
Dependency
 ↓
Build Script
 ↓
Compiler
 ↓
SDK
 ↓
Cache / Worker
 ↓
Object
 ↓
Linker
 ↓
Artifact
```

Mọi node đều có identity/provenance.

---

# 550.73. Security review of compiler itself

`549` có thể chạy trên compiler source.

Do đó:

```text
Axiom Compiler
      ↓
Axiom Security Analyzer
```

có thể phát hiện:

- unsafe boundaries;
- secret flow;
- process execution;
- filesystem access;
- network access;
- plugin boundaries;
- capability amplification.

Nhưng self-analysis vẫn không đủ để chứng minh compiler hoàn toàn an toàn.

---

# 550.74. Bootstrap paradox

Compiler không được tuyên bố:

```text
"I verified myself, therefore I am trusted."
```

Trust phải có external evidence.

Đây là invariant quan trọng của `550`.

---

# 550.75. Release verification pipeline

Canonical release:

```text
Source Revision
      ↓
Dependency Lock
      ↓
Stage0
      ↓
Stage1
      ↓
Stage2
      ↓
Tests
      ↓
Security Analysis
      ↓
Reproducibility Check
      ↓
Artifact Verification
      ↓
Independent Verification
      ↓
Signature
      ↓
Release
```

---

# 550.76. Release evidence bundle

Release bundle:

```text
ReleaseEvidence {
    source_hash
    compiler_hash
    sdk_hash
    dependency_manifest
    bootstrap_chain
    test_results
    security_results
    reproducibility_results
    artifact_hashes
    signatures
}
```

---

# 550.77. Minimal production mode

Một production environment có thể chỉ cần:

```text
compiler
stdlib
sdk
trusted cache
```

Security analyzer/debugger/profiler không cần đi vào final application.

---

# 550.78. No runtime tax

`550` không thêm:

- GC;
- VM;
- mandatory security daemon;
- mandatory telemetry;
- hidden thread;
- hidden network;
- mandatory runtime validator.

Security của toolchain chủ yếu nằm ở:

```text
build boundary
verification
provenance
policy
```

---

# 550.79. Hard invariants

1. Compiler là một security-sensitive artifact.
2. Compiler không tự được coi trusted.
3. Toolchain identity phải stable.
4. Compiler hash phải có thể xác minh.
5. SDK identity phải có thể xác minh.
6. Dependency identity phải có thể xác minh.
7. Build configuration phải có identity.
8. Compiler provenance phải được ghi.
9. Bootstrap provenance phải được ghi.
10. Stage0 phải có identity.
11. Stage1 phải có identity.
12. Stage2 phải có identity.
13. Bootstrap comparison phải reproducible.
14. Diverse bootstrap phải được hỗ trợ.
15. Self-check không phải trust proof.
16. Signature không phải correctness proof.
17. Reproducibility không phải security proof.
18. Security audit không phải correctness proof.
19. Independent verification phải được hỗ trợ.
20. Minimal verifier phải có thể tồn tại độc lập.
21. Compiler release phải hỗ trợ signed artifact.
22. Signing key không nằm trong compiler artifact.
23. Compiler không tự lấy signing key.
24. Signing phải là explicit boundary.
25. SDK phải có manifest.
26. SDK tampering phải detectable.
27. Sysroot identity phải được ghi.
28. Startup object identity phải được ghi.
29. External libraries phải có identity.
30. External compiler không được implicit.
31. External compiler dependency phải machine-readable.
32. Production native codegen không phụ thuộc compiler ngoài Axiom.
33. Build script phải có identity.
34. Build script phải có capability boundary.
35. Build script không có ambient authority trong hermetic mode.
36. Build script input phải declared.
37. Build script output phải declared.
38. Build script network access phải explicit.
39. Build script process execution phải explicit.
40. Build script environment access phải explicit.
41. Plugin phải có identity.
42. Plugin ABI phải versioned.
43. Plugin capability phải explicit.
44. Untrusted plugin không mặc định chạy in-process.
45. Compiler DB access phải policy-controlled.
46. Cache entry phải có integrity hash.
47. Cache hit phải verify integrity.
48. Remote cache phải được coi là untrusted.
49. Remote artifact phải verify trước khi dùng.
50. Cache key phải bao gồm compiler identity.
51. Cache key phải bao gồm target.
52. Cache key phải bao gồm relevant configuration.
53. Cache key phải bao gồm schema version.
54. Cache poisoning phải được phát hiện.
55. Remote worker phải có identity.
56. Worker target phải verify.
57. Worker toolchain phải verify.
58. Worker SDK phải verify.
59. Remote execution không được tự nhận secret.
60. Secret không được đưa vào cache key.
61. Secret không được ghi vào artifact.
62. Secret không được ghi vào log mặc định.
63. Secret không được ghi vào provenance mặc định.
64. Environment ảnh hưởng build phải declared.
65. PATH không được là dependency ngầm.
66. Current time không được ảnh hưởng deterministic build.
67. Randomness không được implicit.
68. Undeclared filesystem input không được dùng trong hermetic mode.
69. Undeclared network input không được dùng trong hermetic mode.
70. Generated code phải có provenance.
71. Generated resources phải có provenance.
72. Generated metadata phải có provenance.
73. Object phải được verify trước linker khi policy yêu cầu.
74. Linker phải thuộc trust graph.
75. Final executable phải có provenance.
76. Final executable hash phải stable khi deterministic.
77. Toolchain installation phải atomic.
78. Toolchain activation phải atomic.
79. Failed toolchain update không được phá active toolchain.
80. Rollback phải giữ verified previous version.
81. Revoked toolchain phải có machine-readable state.
82. Revocation không tự sửa artifact history.
83. Trust root phải explicit.
84. Trust root phải versioned.
85. Trust claims phải typed.
86. `trusted=true` không được là security primitive duy nhất.
87. Signed không đồng nghĩa safe.
88. Reproducible không đồng nghĩa bug-free.
89. Audited không đồng nghĩa mathematically correct.
90. Security scan không đồng nghĩa secure.
91. Unknown phải được preserve.
92. Compiler không được invent evidence.
93. AI không được invent compiler evidence.
94. AI không được tự cấp trust.
95. AI không được tự thay đổi trust root.
96. AI không được tự đổi compiler policy để pass verification.
97. Compiler security evidence phải có provenance.
98. Compiler security evidence phải có timestamp khi temporal semantics cần.
99. Evidence phải có build identity.
100. Evidence phải có target identity.
101. Evidence phải có toolchain identity.
102. Evidence phải có policy identity.
103. Build security manifest phải machine-readable.
104. Build security manifest phải queryable.
105. Build security manifest phải reproducible khi inputs reproducible.
106. Compiler crash report phải có compiler identity.
107. Compiler crash report không được tự động upload source.
108. Source privacy phải được bảo vệ.
109. Security diagnostics phải có source provenance.
110. Compiler fuzzing phải bao phủ trust boundaries.
111. Object parser phải được fuzz.
112. Linker phải được fuzz.
113. Package parser phải được fuzz.
114. Registry metadata parser phải được fuzz.
115. Plugin protocol phải được fuzz.
116. Build manifest parser phải được fuzz.
117. Cache metadata phải được validate.
118. Malformed metadata không được gây implicit trust.
119. Malformed package không được execute arbitrary code.
120. Malicious build script phải chịu capability restrictions.
121. Toolchain installation phải verify trước activation.
122. Package installation phải verify trước use.
123. SDK installation phải verify trước use.
124. Compiler update phải verify trước activation.
125. Build worker không được có quyền vượt build policy.
126. Compiler process isolation phải được hỗ trợ.
127. Build isolation phải được hỗ trợ.
128. Cache isolation phải được hỗ trợ.
129. Project không được mặc định sửa global compiler.
130. Toolchain installation không được nằm trong project output.
131. Production build phải có thể offline.
132. Trust verification phải có thể offline khi trust material đầy đủ.
133. Air-gapped build phải được hỗ trợ.
134. Offline bundle phải có manifest.
135. Offline bundle phải có hashes.
136. Offline bundle phải có trust roots.
137. Dependency substitution phải detectable.
138. Package source substitution phải detectable.
139. Publisher substitution phải detectable.
140. Compiler substitution phải detectable.
141. SDK substitution phải detectable.
142. Worker substitution phải detectable.
143. Cache substitution phải detectable.
144. Build output substitution phải detectable.
145. Bootstrap chain phải queryable.
146. Compiler version impact phải queryable.
147. Miscompilation impact phải queryable khi rule có đủ evidence.
148. Artifact-to-compiler provenance phải truy ngược được.
149. Artifact-to-SDK provenance phải truy ngược được.
150. Artifact-to-dependency provenance phải truy ngược được.
151. Artifact-to-build-script provenance phải truy ngược được.
152. Artifact-to-worker provenance phải truy ngược được.
153. Artifact-to-cache provenance phải truy ngược được.
154. Compiler trust phải có external evidence path.
155. Security analyzer không được là sole trust root.
156. Compiler self-analysis không được là sole trust proof.
157. Stage comparison không phải universal correctness proof.
158. Independent verifier không được cần full compiler để verify basic claims.
159. Release evidence phải portable.
160. Release evidence phải cryptographically bindable.
161. Evidence bundle không được chứa secret mặc định.
162. Evidence bundle phải hỗ trợ redaction.
163. Redaction không được biến missing evidence thành positive evidence.
164. Missing evidence phải là Unknown.
165. Security policy phải có version.
166. Toolchain policy phải có version.
167. Build policy phải có version.
168. Compiler policy không được silently thay đổi semantics.
169. Strict mode phải fail closed khi trust verification bắt buộc thất bại.
170. Non-strict mode phải ghi rõ exception.
171. Exceptions phải có provenance.
172. Exceptions phải có scope.
173. Exceptions phải có expiration khi policy yêu cầu.
174. Compiler security controls không được bắt buộc application runtime.
175. Compiler security controls không được thêm GC.
176. Compiler security controls không được thêm VM.
177. Compiler security controls không được thêm hidden thread vào application.
178. Compiler security controls không được thêm hidden network vào application.
179. Compiler security controls không được thêm hidden telemetry.
180. Compiler security model phải tích hợp `482/488`.
181. Compiler supply-chain model phải tích hợp `447/491/492`.
182. Build security phải tích hợp `487`.
183. Capability security phải tích hợp `490`.
184. Governance phải tích hợp `545`.
185. Evidence phải tích hợp `546`.
186. Incident phải tích hợp `547`.
187. Security posture phải tích hợp `548`.
188. AI security analysis phải tích hợp `549`.
189. Compiler security graph phải có machine-readable representation.
190. Compiler security graph phải support reverse impact query.
191. Compiler security graph phải support historical reconstruction.
192. Compiler security graph phải support reproducibility investigation.
193. Compiler security graph phải support compromised-toolchain investigation.
194. Toolchain compromise phải có khả năng truy tìm artifact bị ảnh hưởng.
195. Artifact phải truy tìm được compiler.
196. Compiler phải truy tìm được source.
197. Source phải truy tìm được dependency.
198. Dependency phải truy tìm được publisher/source.
199. Trust claims không được conflated.
200. **Final invariant:** Axiom phải xây dựng được một trust chain có thể kiểm chứng độc lập từ source → dependency → build → compiler → SDK → object → linker → artifact, với signature, provenance, reproducibility, sandbox/capability, cache verification, bootstrap evidence và impact analysis; compiler không được tự trở thành trust root của chính nó, và toàn bộ cơ chế này không được biến thành runtime overhead bắt buộc của ứng dụng.

**BOOTSTRAP-550: LOCKED.**

---

# BOOTSTRAP-551 — FORMAL SEMANTICS, LANGUAGE SOUNDNESS CONTRACT, MEMORY MODEL, CONCURRENCY MODEL & MACHINE-CHECKABLE LANGUAGE INVARIANTS

Đây là bước tiếp theo quan trọng.

Cho tới `550`, Axiom đã có rất nhiều subsystem. Nhưng khi ngôn ngữ lớn đến mức này, cần một lớp trả lời câu hỏi nền tảng:

> **Chính xác thì một chương trình Axiom có nghĩa là gì, và compiler được phép biến đổi nó đến đâu mà vẫn giữ nguyên semantics?**

`551` sẽ xây dựng **formal semantic foundation** cho toàn bộ compiler.

Trọng tâm:

```text
Source Syntax
     ↓
AST
     ↓
HIR
     ↓
Typed Semantic Model
     ↓
Operational / Denotational Semantics
     ↓
MIR
     ↓
Optimization
     ↓
Machine Code
```

và chứng minh/kiểm tra các invariant giữa các tầng:

```text
AST semantics
      ≡
HIR semantics
      ≡
MIR semantics
      ≡
optimized MIR semantics
      ≡
machine semantics
```

Trong đó `≡` không nhất thiết có nghĩa byte-for-byte giống nhau; nó có nghĩa **quan sát được theo semantic contract tương ứng**.

### 551 sẽ phải khóa các vấn đề sau

- formal syntax/grammar semantics;
- values, places, expressions, statements;
- evaluation order;
- sequencing;
- side effects;
- initialization;
- move/copy/drop;
- ownership semantics;
- panic/abort/unwind;
- Result/Option;
- integer overflow;
- floating-point semantics;
- undefined behavior;
- unsafe semantics;
- pointer provenance;
- aliasing;
- volatile;
- atomic memory model;
- data races;
- thread semantics;
- async semantics;
- cancellation;
- FFI semantics;
- comptime semantics;
- deterministic vs nondeterministic operations;
- observable behavior;
- optimizer legality;
- undefined behavior boundaries;
- compiler transformation correctness;
- MIR semantic invariants;
- IR verifier;
- refinement giữa IR và machine code;
- ABI preservation;
- object/link semantics;
- native execution model;
- formal specification format;
- executable semantic tests;
- differential semantic testing;
- model checking cho các subset quan trọng;
- proof-carrying optimization evidence;
- machine-readable semantic invariants.

Đặc biệt, `551` sẽ giải quyết một vấn đề rất quan trọng cho mục tiêu **"nhanh bằng hoặc hơn C/C++ nhưng compiler tự viết"**:

```text
Aggressive Optimization
        ↓
must know
        ↓
exactly what behavior is observable
```

để compiler có thể mạnh tay tối ưu mà **không vô tình biến optimization thành miscompilation**.