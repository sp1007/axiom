# BOOTSTRAP-587 — COMPILER BOOTSTRAP TRUST & DIVERGENT COMPILATION 3.0
## 3-STAGE SELF-REBUILD, DIVERGENT COMPILER VALIDATION, N-LEVEL BOOTSTRAP, TRANSLATION VALIDATION, COMPILER FINGERPRINT, TRUSTED SEED ROTATION & SUPPLY-CHAIN COMPILER INTEGRITY

**Trạng thái: COMPLETED / LOCKED**

`587` mở rộng `586` từ **self-hosting** sang **trust verification**. Một compiler tự build chính nó chưa đủ để chứng minh compiler đó không bị lỗi hoặc bị can thiệp. Axiom vì vậy cần một cơ chế có thể phát hiện divergence giữa các compiler stages/build paths.

```text id="587arch"
                    Trusted Seed
                         │
             ┌───────────┴───────────┐
             ▼                       ▼
          Build-A                  Build-B
             │                       │
             ▼                       ▼
         Compiler-A              Compiler-B
             │                       │
             └───────────┬───────────┘
                         ▼
                  Divergence Check
                         │
              ┌──────────┼──────────┐
              ▼          ▼          ▼
          Artifact    Semantic    Fingerprint
          Compare     Compare      Compare
              │          │          │
              └──────────┼──────────┘
                         ▼
                   Stage2 Build
                         │
                         ▼
                Independent Verify
                         │
                         ▼
                 Trusted Compiler
```

---

# 587.1. Mục tiêu

Axiom phải có khả năng phát hiện:

- compiler bị sửa;
- Stage0 bị thay thế;
- compiler miscompile chính nó;
- backend divergence;
- hidden build input;
- nondeterministic compilation;
- poisoned dependency;
- corrupted cached compiler artifact.

---

# 587.2. Bootstrap trust ≠ self-hosting

Hai property độc lập:

```text
Self-hosting
    =
compiler có thể tự build

Bootstrap trust
    =
compiler build có thể được kiểm chứng
```

---

# 587.3. Verification levels

```text id="levels587"
L0 = structural
L1 = reproducibility
L2 = differential
L3 = semantic
L4 = translation validation
L5 = independent bootstrap
```

---

# 587.4. L0 — structural verification

Kiểm tra:

- executable format;
- sections;
- symbols;
- relocations;
- dependencies;
- target;
- ABI.

---

# 587.5. L1 — reproducibility

Cùng input phải tạo cùng artifact theo reproducible policy.

---

# 587.6. L2 — differential

Hai compilation paths phải được so sánh.

---

# 587.7. L3 — semantic

So sánh semantic fingerprints của output.

---

# 587.8. L4 — translation validation

Mỗi compiler transformation quan trọng có thể được kiểm tra semantic equivalence.

---

# 587.9. L5 — independent bootstrap

Compiler được build bởi một path không hoàn toàn phụ thuộc chính artifact đang kiểm tra.

---

# 587.10. Divergent compilation

Canonical model:

```text id="div587"
Compiler A
   ├── source
   └── config A
         ↓
      Output A

Compiler B
   ├── source
   └── config B
         ↓
      Output B
```

---

# 587.11. Divergence purpose

Divergence không nhằm tạo hai compiler khác nhau về semantics.

Mục đích là tạo **hai đường kiểm chứng độc lập**.

---

# 587.12. Build-path diversity

Có thể khác:

- optimization;
- pass ordering trong phạm vi deterministic contract;
- host;
- architecture;
- compiler stage;
- code-generation strategy.

---

# 587.13. Semantic invariant

Dù build path khác nhau:

```text
Program semantics A == Program semantics B
```

---

# 587.14. Binary equality

Binary equality là strongest reproducibility signal nhưng không bắt buộc nếu policy cho phép khác biệt hợp lệ.

---

# 587.15. Semantic fingerprint

Compiler phải có fingerprint cấp semantic:

```text id="sf587"
API surface
compiler capabilities
language version
target support
runtime ABI
builtin definitions
```

---

# 587.16. Artifact fingerprint

Artifact fingerprint bao gồm:

```text id="af587"
sections
symbols
relocations
code regions
read-only data
runtime dependencies
```

---

# 587.17. Machine-code fingerprint

Có thể fingerprint canonicalized machine code:

```text id="mc587"
function identity
instruction sequence
relocation-normalized operands
```

---

# 587.18. Address-independent fingerprint

Absolute addresses không được làm fingerprint thay đổi khi chỉ khác layout hợp lệ.

---

# 587.19. Debug-independent fingerprint

Debug metadata không ảnh hưởng semantic compiler fingerprint.

---

# 587.20. Signature fingerprint

Code signing metadata không ảnh hưởng semantic fingerprint.

---

# 587.21. Compiler fingerprint

Compiler fingerprint:

```text id="cf587"
language_semantics_hash
compiler_source_hash
target_backend_hash
runtime_abi_hash
builtin_hash
```

---

# 587.22. Fingerprint version

Fingerprint algorithm phải versioned.

```text
fingerprint_v1
fingerprint_v2
...
```

---

# 587.23. Canonicalization

Fingerprint input phải canonicalize:

- section ordering;
- symbol ordering;
- path normalization;
- metadata ordering;
- relocation representation.

---

# 587.24. Compiler identity

Compiler identity không chỉ là executable SHA-256.

```text id="identity587"
CompilerIdentity {
    version
    source_hash
    semantic_hash
    backend_hash
    runtime_hash
    target
}
```

---

# 587.25. Stage fingerprint

Mỗi stage có:

```text id="stagefp587"
stage0 fingerprint
stage1 fingerprint
stage2 fingerprint
```

---

# 587.26. Bootstrap matrix

Verification có thể chạy:

```text id="matrix587"
              Builder
             A       B
Target X     ✓       ✓
Target Y     ✓       ✓
Target Z     ✓       ✓
```

---

# 587.27. Host diversity

Nếu khả thi:

```text id="host587"
Linux
Windows
macOS
```

có thể dùng các host khác nhau để giảm host-specific trust.

---

# 587.28. Architecture diversity

Một compiler có thể build trên:

```text
x86-64
AArch64
```

nhưng semantic output target phải giống nhau khi target/configuration giống nhau.

---

# 587.29. Bootstrap compiler pair

Canonical verification:

```text id="pair587"
Stage0-A → Stage1-A
Stage0-B → Stage1-B
```

sau đó compare.

---

# 587.30. Independent seed

Stage0-B không nên được tạo từ Stage0-A binary nếu mục tiêu là independent trust.

---

# 587.31. Seed diversity

Có thể duy trì:

```text id="seeddiv587"
Axiom Stage0
independent validator/compiler
```

---

# 587.32. Independent compiler

Independent compiler chỉ cần implement subset đủ để compile/validate bootstrap corpus.

Không cần implement toàn bộ Axiom.

---

# 587.33. Independent validator

Một validator nhỏ có thể kiểm tra:

- machine artifact;
- semantic fingerprints;
- compiler metadata;
- bootstrap manifests.

---

# 587.34. Validator independence

Validator không được phụ thuộc compiler binary đang được verify.

---

# 587.35. Bootstrap corpus

Corpus phải chứa các construct có khả năng expose compiler divergence:

```text id="corpus587"
types
generics
traits
pattern matching
comptime
async
atomics
FFI
SIMD
exceptions
unsafe
modules
```

---

# 587.36. Compiler self-corpus

Compiler source itself là một phần của bootstrap corpus.

---

# 587.37. Metacircular test

```text id="meta587"
compiler
  ↓ compile
compiler
  ↓ compile
compiler
```

mỗi vòng phải pass semantic verification.

---

# 587.38. N-level bootstrap

Axiom không giới hạn chính xác ba stage.

Có thể:

```text id="nboot587"
Stage0
 → Stage1
 → Stage2
 → ...
 → StageN
```

---

# 587.39. Convergence

Bootstrap chain có thể dừng khi:

```text StageN semantic identity
=
StageN+1 semantic identity
```

---

# 587.40. Maximum bootstrap depth

Build system phải có giới hạn để tránh infinite bootstrap loop.

---

# 587.41. Fixed-point detection

Fingerprint comparison có thể detect convergence.

---

# 587.42. Fixed-point caveat

Fingerprint equality không chứng minh absolute correctness.

Nó chỉ chứng minh consistency với selected fingerprint model.

---

# 587.43. Translation validation

Compiler transformation:

```text id="tv587"
Input IR
   ↓
Optimization
   ↓
Output IR
```

được kiểm tra:

```text
Semantics(Input) == Semantics(Output)
```

trong phạm vi proof system.

---

# 587.44. Compiler-stage validation

Stage1 và Stage2 có thể generate validation certificates.

---

# 587.45. Certificate

Certificate chứa:

```text id="cert587"
source hash
input IR hash
output IR hash
transformation ID
proof/check result
```

---

# 587.46. Certificate trust

Certificate không tự chứng minh compiler correctness.

Validator phải independently check certificate.

---

# 587.47. Optimization verification

Dùng framework `575`.

---

# 587.48. Backend verification

Machine lowering phải pass:

```text id="backend587"
MIR
 ↓
Machine IR
 ↓
Machine code
```

semantic validation.

---

# 587.49. Link verification

Link output phải pass image validation từ `582–584`.

---

# 587.50. Startup verification

Compiler executable phải pass startup tests từ `585`.

---

# 587.51. Runtime verification

Compiler runtime phải pass runtime conformance tests.

---

# 587.52. Differential source compilation

Hai compiler build cùng source:

```text id="diffsrc587"
Compiler-A
Compiler-B
```

và compare normalized outputs.

---

# 587.53. Differential IR

Nếu binary khác:

```text source
 ↓
IR-A
IR-B
```

có thể compare IR fingerprints.

---

# 587.54. Differential machine code

Nếu IR tương đương nhưng machine code khác, compare semantics.

---

# 587.55. Differential runtime

Executable A/B chạy cùng test input và compare:

```text exit code
stdout
stderr
observable state
```

---

# 587.56. Floating-point comparison

FP tests phải dùng target-specific tolerance/semantic rules.

Không dùng byte equality cho mọi FP result.

---

# 587.57. Undefined behavior

Không sử dụng input chứa undefined behavior để kết luận compiler divergence.

---

# 587.58. Concurrency differential tests

Concurrency tests phải use deterministic schedules hoặc controlled scheduler.

---

# 587.59. Randomized differential testing

Random tests phải record seed.

---

# 587.60. Replaying divergence

Divergence report phải có:

```text id="replay587"
seed
source hash
compiler identities
target
configuration
input
```

để replay.

---

# 587.61. Compiler fingerprint mismatch

Mismatch không lập tức có nghĩa compiler malicious.

Các nguyên nhân có thể:

- version difference;
- target feature;
- optimization;
- legal metadata variation;
- bug;
- corruption.

---

# 587.62. Classification

Divergence classifier:

```text id="class587"
Expected
ConfigurationMismatch
ReproducibilityViolation
SemanticMismatch
BackendMismatch
RuntimeMismatch
Unknown
```

---

# 587.63. Unknown divergence

`Unknown` phải block release cho đến khi được resolved hoặc explicitly accepted theo policy.

---

# 587.64. Trust state

Compiler trust state:

```text id="truststate587"
Unverified
StructurallyVerified
Reproducible
DifferentiallyVerified
BootstrapVerified
ReleaseTrusted
Revoked
```

---

# 587.65. Trust monotonicity

Không được chuyển:

```text ReleaseTrusted → StructurallyVerified
```

mà không explicit invalidation/revocation.

---

# 587.66. Revocation

Nếu compiler artifact bị phát hiện compromised:

```text ReleaseTrusted
       ↓
Revoked
```

---

# 587.67. Revocation metadata

Revocation record:

```text id="rev587"
compiler identity
reason
timestamp
replacement version
```

Timestamp chỉ là metadata và không ảnh hưởng reproducible artifact.

---

# 587.68. Trusted seed rotation

Stage0 có thể rotate.

---

# 587.69. Seed rotation process

```text id="rotate587"
Old Trusted Seed
      ↓
Build New Seed
      ↓
Independent Verify
      ↓
Divergent Bootstrap
      ↓
Compare
      ↓
Promote New Seed
```

---

# 587.70. Dual-seed transition

Trong transition:

```text id="dual587"
Seed-A
Seed-B
```

cùng được giữ để cross-check.

---

# 587.71. Seed retirement

Seed cũ chỉ được retire sau khi seed mới đạt required verification level.

---

# 587.72. Recovery seed

Một immutable recovery seed nên tồn tại ngoài normal development tree.

---

# 587.73. Recovery seed isolation

Recovery seed không được tự động update bởi normal dependency resolution.

---

# 587.74. Supply-chain identity

Bootstrap dependency:

```text id="sc587"
package
version
content_hash
source
signature
```

---

# 587.75. Dependency provenance

Compiler phải biết dependency nào đã tham gia build.

---

# 587.76. Dependency closure

Trusted compiler phải có complete dependency closure.

---

# 587.77. Hidden dependency detection

Build system phải detect dependency được compiler truy cập nhưng không declared.

---

# 587.78. Hermetic filesystem

Build sandbox có thể restrict filesystem access.

---

# 587.79. Hermetic environment

Build sandbox có thể restrict environment variables.

---

# 587.80. Hermetic network

Network disabled mặc định.

---

# 587.81. Compiler self-modification

Compiler không được tự sửa executable đang chạy.

---

# 587.82. Generated artifact isolation

Generated compiler artifacts phải nằm trong isolated build directory.

---

# 587.83. Cache poisoning

Cache entries phải keyed bởi full compiler/build identity.

---

# 587.84. Remote cache trust

Remote cache artifact phải được verify trước khi sử dụng.

---

# 587.85. Untrusted remote worker

Remote worker không được có quyền tự promote artifact thành trusted.

---

# 587.86. Remote build attestation

Worker có thể cung cấp:

```text id="att587"
action hash
input hashes
output hashes
toolchain identity
```

---

# 587.87. Local verification

Trusted coordinator phải independently verify remote artifact.

---

# 587.88. Multiple worker agreement

Một artifact có thể được build bởi nhiều workers để detect divergence.

---

# 587.89. Quorum verification

Có thể yêu cầu:

```text id="quorum587"
N independent builds
→ required agreement
```

cho high-assurance release.

---

# 587.90. No mandatory distributed trust

Quorum là release/high-assurance policy, không phải compiler language requirement.

---

# 587.91. Compiler binary transparency

Release compiler có thể publish:

```text id="trans587"
source hash
binary hash
bootstrap report
dependency closure
verification certificates
```

---

# 587.92. Transparency log

Có thể lưu release identities trong append-only transparency system.

---

# 587.93. Local verification

Developer phải có thể verify release offline bằng published hashes/certificates.

---

# 587.94. Rebuild release

Developer có thể:

```text id="rebuild587"
source
 ↓
trusted bootstrap
 ↓
compiler
 ↓
compare release
```

---

# 587.95. Rebuild mismatch

Mismatch phải report canonical artifact differences.

---

# 587.96. Allowed nondeterminism

Nếu release có explicit nondeterministic field:

```text signing
certificate
platform metadata
```

thì comparison phải strip/normalize field đó.

---

# 587.97. Semantic normalization

Normalization không được xóa machine-code semantics.

---

# 587.98. Code identity

Code sections phải có stronger verification hơn debug/resources.

---

# 587.99. Data identity

Immutable semantic data cũng phải được fingerprint.

---

# 587.100. Runtime identity

Runtime binary phải được independently fingerprint.

---

# 587.101. Standard library identity

Stdlib hash phải nằm trong compiler/toolchain identity khi ABI-sensitive.

---

# 587.102. Target backend identity

Backend tables/codegen implementation hash phải tham gia compiler identity.

---

# 587.103. Language semantic identity

Compiler binary có thể khác nhưng nếu language semantic definition khác thì semantic identity phải khác.

---

# 587.104. Builtin identity

Builtin functions/types/macros/comptime intrinsics phải fingerprint.

---

# 587.105. ABI identity

ABI definition hash phải fingerprint.

---

# 587.106. Runtime ABI mismatch

Compiler và runtime ABI hash mismatch → reject normal compilation.

---

# 587.107. Compiler/stdlib mismatch

Compiler phải detect incompatible stdlib.

---

# 587.108. Target SDK mismatch

Target SDK identity phải participate trong target build identity.

---

# 587.109. Verification manifest

Canonical:

```text id="manifest587"
BootstrapManifest {
    source
    dependencies
    stages
    compiler_ids
    target_matrix
    verification_levels
    fingerprints
    certificates
}
```

---

# 587.110. Manifest immutability

Published verification manifest không được mutate.

---

# 587.111. Manifest signing

Release manifest có thể được signed.

---

# 587.112. Compiler provenance query

CLI:

```text
axiom compiler provenance
```

phải có thể report trust information.

---

# 587.113. Fingerprint query

```text
axiom compiler fingerprint
```

---

# 587.114. Bootstrap query

```text
axiom bootstrap verify
```

---

# 587.115. Divergence query

```text
axiom bootstrap diff
```

---

# 587.116. Machine-readable result

Các command trên phải hỗ trợ machine-readable output.

---

# 587.117. AI-readable trust metadata

Metadata có thể được consumed bởi AI agents:

```text id="aitrust587"
compiler
stage
source
dependencies
target
trust
verification
```

---

# 587.118. AI agent restriction

AI agent không được coi compiler là trusted chỉ dựa vào natural-language claim.

Phải query machine-readable verification state.

---

# 587.119. Compiler update agent

Automated agent có thể:

```text id="agent587"
fetch source
 ↓
build
 ↓
bootstrap
 ↓
verify
 ↓
compare
 ↓
publish candidate
```

nhưng promotion vẫn phải follow explicit trust policy.

---

# 587.120. Security incident integration

Compiler compromise phải integrate với security response `549/550`.

---

# 587.121. Compromised dependency

Nếu dependency bị revoke:

```text id="comp587"
dependent compiler artifacts
→ potentially untrusted
```

---

# 587.122. Trust propagation

Trust graph:

```text id="tp587"
Dependency
    ↓
Compiler
    ↓
Runtime
    ↓
Application
```

Một revoked critical dependency có thể invalidate downstream artifacts.

---

# 587.123. No automatic innocence

Trust invalidation là provenance property, không phải assertion rằng downstream artifact chắc chắn malicious.

---

# 587.124. Compiler compromise recovery

Recovery:

```text id="recover587"
trusted recovery seed
       ↓
clean source
       ↓
clean dependency closure
       ↓
divergent build
       ↓
independent verification
       ↓
new trusted compiler
```

---

# 587.125. Clean-room rebuild

High-assurance release có thể dùng isolated environment từ trusted seed.

---

# 587.126. Toolchain isolation

Compiler build không được dùng installed system compiler nếu bootstrap profile cấm.

---

# 587.127. Host tool audit

Build environment phải record host tools được dùng.

---

# 587.128. Tool exclusion

External compiler executable bị reject nếu xuất hiện trong prohibited bootstrap action graph.

---

# 587.129. Action graph verification

Build graph phải có thể inspect:

```text id="graph587"
inputs
tools
outputs
actions
```

---

# 587.130. Reproducible action graph

Action ordering/parallel execution không được thay đổi semantic result.

---

# 587.131. Build graph hash

```text id="bgh587"
BuildGraphHash =
Hash(canonical actions + inputs + tools + configuration)
```

---

# 587.132. Compiler provenance hash

```text id="cph587"
CompilerProvenanceHash =
Hash(source + dependency closure + build graph + target)
```

---

# 587.133. Artifact provenance

Final compiler binary phải reference provenance hash.

---

# 587.134. Provenance embedding

Embedding phải không làm provenance hash tự tham chiếu vô hạn.

---

# 587.135. Self-reference solution

Use two-phase identity:

```text id="2phase587"
semantic artifact hash
        ↓
provenance metadata
```

---

# 587.136. Semantic hash stability

Semantic hash không phụ thuộc chính provenance metadata.

---

# 587.137. Compiler fingerprint stability

Fingerprint phải ổn định khi chỉ thay đổi:

- timestamp;
- signature;
- debug path mapping theo allowed policy;
- packaging compression.

---

# 587.138. Fingerprint sensitivity

Fingerprint phải thay đổi khi thay đổi:

- language semantics;
- compiler codegen;
- ABI;
- builtin;
- target backend;
- runtime ABI.

---

# 587.139. Verification cache

Verification results có thể cache theo:

```text id="vc587"
artifact hash
verification policy
validator version
```

---

# 587.140. Verification invalidation

Validator update có thể invalidate cached verification.

---

# 587.141. Bootstrap CI

Release CI phải chạy tối thiểu:

```text id="ci587"
Stage0
 ↓
Stage1
 ↓
Stage2
 ↓
rebuild
 ↓
differential
 ↓
tests
 ↓
artifact verification
```

---

# 587.142. Nightly divergent build

Có thể chạy independent divergent builds định kỳ để phát hiện latent compiler instability.

---

# 587.143. Compiler fuzz bootstrap

Fuzz generated source qua Stage0/Stage1/Stage2.

---

# 587.144. Crash consistency

Compiler crash phải không làm verification system accept partial output.

---

# 587.145. Output poisoning prevention

Only successfully verified outputs enter trusted cache.

---

# 587.146. Stage promotion

```text id="promotion587"
Candidate
   ↓
Structural Verify
   ↓
Tests
   ↓
Divergent Verify
   ↓
Bootstrap Verify
   ↓
Trusted
```

---

# 587.147. Promotion atomicity

Promotion state và artifact publication phải atomic.

---

# 587.148. Rollback

Nếu post-release issue:

```text id="rollback587"
Trusted
  ↓
Revoked
  ↓
previous trusted version
```

---

# 587.149. Historical verification

Old compiler releases phải remain verifiable sau khi compiler mới ra đời.

---

# 587.150. Verification archival

Archive:

```text id="archive587"
source
manifest
hashes
bootstrap report
target descriptions
verification tool version
```

---

# 587.151. Long-term bootstrap

Axiom phải có khả năng rebuild compiler sau nhiều năm nếu:

- source còn;
- bootstrap seed còn;
- dependencies còn;
- target SDK còn.

---

# 587.152. Bootstrap archive format

Bootstrap recovery bundle dùng format versioned, self-describing.

---

# 587.153. No proprietary bootstrap dependency

Trusted recovery path không phụ thuộc proprietary compiler.

---

# 587.154. Minimal verifier

Axiom nên có một verifier nhỏ có thể build bằng nhiều implementation khác nhau.

---

# 587.155. Verifier language subset

Verifier có thể dùng subset Axiom đủ đơn giản để independently audit.

---

# 587.156. Verifier trust

Verifier không được tự verify binary bằng logic phụ thuộc binary đó.

---

# 587.157. Final verification layers

```text id="layers587"
Source Integrity
       ↓
Dependency Integrity
       ↓
Build Graph Integrity
       ↓
Artifact Integrity
       ↓
Compiler Self-Build
       ↓
Divergent Build
       ↓
Semantic Validation
       ↓
Runtime Validation
       ↓
Release Trust
```

---

# 587.158. Hard failure

Các lỗi sau phải block trusted release:

```text
source mismatch
dependency mismatch
unexpected external compiler
bootstrap divergence unexplained
semantic mismatch
invalid artifact
runtime regression
verification failure
```

---

# 587.159. Soft difference

Các khác biệt được policy cho phép:

```text
debug metadata
signatures
compression
legal section layout differences
```

không nhất thiết block release nếu semantic fingerprint vẫn match.

---

# 587.160. No hidden exception

Build system không được có implicit whitelist để bỏ qua divergence.

---

# 587.161. Explicit waiver

Nếu release policy cho phép exception:

```text id="waiver587"
reason
scope
approver
expiry
affected artifact
```

phải được ghi lại.

---

# 587.162. Waiver không thay đổi compiler semantics

Waiver chỉ thay đổi release decision.

---

# 587.163. Trust decision separation

```text id="trustdecision587"
Verification Engine
        │
        ▼
Evidence
        │
        ▼
Release Policy
        │
        ▼
Trust State
```

Verification engine không tự quyết định policy ngoài declared rules.

---

# 587.164. Evidence preservation

Mọi evidence được dùng để promote compiler phải được lưu.

---

# 587.165. Reproducibility evidence

Phải lưu input/output hashes.

---

# 587.166. Differential evidence

Phải lưu compiler identities và comparison result.

---

# 587.167. Runtime evidence

Phải lưu test suite/version và result fingerprint.

---

# 587.168. Translation evidence

Phải lưu transformation/certificate identity khi sử dụng proof validation.

---

# 587.169. Compiler trust API

Runtime/tooling có thể query:

```text id="api587"
CompilerTrust {
    identity
    stage
    trust_state
    verification
}
```

---

# 587.170. Final architecture

```text id="final587"
                    Source
                      │
                      ▼
               Trusted Bootstrap
                      │
          ┌───────────┴───────────┐
          ▼                       ▼
      Build Path A           Build Path B
          │                       │
          ▼                       ▼
       Compiler A             Compiler B
          │                       │
          └───────────┬───────────┘
                      ▼
               Divergence Engine
                      │
          ┌───────────┼───────────┐
          ▼           ▼           ▼
       Binary      Semantic    Runtime
       Compare     Compare     Compare
          │           │           │
          └───────────┼───────────┘
                      ▼
               Bootstrap Engine
                      │
                      ▼
                 Stage2/StageN
                      │
                      ▼
              Independent Validator
                      │
                      ▼
               Trusted Compiler
```

---

# 587.171. FINAL HARD INVARIANT

> **Không một Axiom compiler release nào được coi là trusted chỉ vì nó tự build được chính nó. Trusted compiler phải có provenance đầy đủ, reproducibility hoặc semantic equivalence phù hợp, bootstrap verification, divergent-build hoặc independent verification path, artifact validation và runtime/compiler conformance. Mọi divergence không giải thích được phải ngăn promotion.**

# 587 — LOCKED

Sau `587`, trust chain của Axiom trở thành:

```text
586 = SELF-HOSTING
      "Axiom có thể tự xây compiler"

587 = TRUSTED SELF-HOSTING
      "Axiom có bằng chứng độc lập rằng compiler
       tự xây của nó không đơn giản chỉ đang
       xác nhận chính binary đáng ngờ đó"
```

Đây là điểm quan trọng để tránh **trusting trust** ở mức thực tế: Axiom không tuyên bố giải quyết tuyệt đối bài toán compiler trust, nhưng cung cấp nhiều lớp kiểm chứng độc lập và có thể reproducible.

---

# NEXT — BOOTSTRAP-588

## COMPILER DISTRIBUTION & TOOLCHAIN SDK 4.0
### MULTI-TARGET SDK, SYSROOT, TARGET ABI DATABASE, NATIVE LIBRARY/SDK IMPORT, CROSS-COMPILATION PACKS, TOOLCHAIN MANIFEST, INSTALLATION, VERSION SELECTION & OFFLINE DEVELOPMENT ENVIRONMENT

```text id="next588"
                 Axiom Toolchain
                       │
          ┌────────────┼────────────┐
          ▼            ▼            ▼
       Compiler      Linker       Tools
          │            │            │
          └────────────┼────────────┘
                       ▼
                    SDK Root
                       │
        ┌──────────────┼──────────────┐
        ▼              ▼              ▼
      Windows         Linux         macOS/iOS
        │              │              │
        ▼              ▼              ▼
      PE/ABI         ELF/ABI       Mach-O/ABI
        │              │              │
        └──────────────┼──────────────┘
                       ▼
                Cross Compilation
                       │
                       ▼
              Reproducible Toolchain
```

`588` sẽ khóa **toolchain distribution thực tế**: compiler không chỉ self-host được mà còn phải có SDK/sysroot/target database/library ABI rõ ràng để người dùng có thể cài một Axiom toolchain và biên dịch native cho nhiều nền tảng mà không phụ thuộc hệ thống compiler bên ngoài.