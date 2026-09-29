# BOOTSTRAP-586 — COMPILER BOOTSTRAP & RUNTIME SELF-HOSTING 4.0
## STAGE0/STAGE1/STAGE2, SELF-HOSTED COMPILER BUILD, TRUST ROOT, COMPILER/RUNTIME BOOTSTRAP, CROSS-COMPILATION, DETERMINISTIC SELF-REBUILD & TRUSTED COMPILER VERIFICATION

**Trạng thái: COMPLETED / LOCKED**

`586` khóa vòng lặp **Axiom tự xây dựng chính nó**. Mục tiêu không chỉ là compiler có thể compile Axiom, mà là toàn bộ toolchain có thể chuyển từ một seed nhỏ sang compiler được viết bằng Axiom, sau đó tự rebuild và kiểm chứng kết quả.

```text id="586arch"
                 Trusted Seed
                     │
                     ▼
                  Stage0
                     │
          ┌──────────┼──────────┐
          ▼          ▼          ▼
       Compiler    Runtime    Toolchain
          │          │          │
          └──────────┼──────────┘
                     ▼
                  Stage1
                     │
              self-build source
                     ▼
                  Stage2
                     │
             ┌───────┴────────┐
             ▼                ▼
       Self-hosted         Cross Compiler
       Toolchain               │
             │                 ▼
             └──────────► Target Toolchains
                     │
                     ▼
              Reproducibility
                     │
                     ▼
             Bootstrap Verify
                     │
                     ▼
              Trusted Axiom
```

---

# 586.1. Bootstrap objective

Axiom phải đạt:

```text
Axiom compiler
    ↓
compiled by Axiom
    ↓
produces Axiom compiler
    ↓
that compiler compiles itself
```

Không có compiler ngoại vi trong vòng self-hosting cuối.

---

# 586.2. Bootstrap stages

Ba stage canonical:

```text
Stage0
Stage1
Stage2
```

Có thể có Stage3+ cho verification, nhưng không phải bootstrap requirement.

---

# 586.3. Stage0

Stage0 là compiler seed tối thiểu được trusted externally.

Nó phải đủ để:

- parse subset cần thiết;
- semantic-check subset;
- generate native code;
- build Stage1.

---

# 586.4. Stage0 trust boundary

Stage0 là **trust root của bootstrap**, nhưng không phải trust root của toàn bộ hệ sinh thái.

---

# 586.5. Stage0 implementation

Stage0 có thể được viết bằng:

- C;
- Axiom subset;
- assembly;
- hoặc implementation khác.

Nhưng đây chỉ là bootstrap exception.

---

# 586.6. Stage0 sunset

Sau khi Axiom compiler self-hosting hoàn chỉnh, Stage0 không được là dependency runtime của compiler thông thường.

---

# 586.7. Stage0 minimality

Stage0 không cần implement toàn bộ Axiom language.

Nó chỉ cần implement subset đủ để build Stage1.

---

# 586.8. Bootstrap subset

Subset phải được machine-readable:

```text
BootstrapLanguageSubset
```

và versioned.

---

# 586.9. Stage1

Stage1 là compiler được build từ Axiom compiler source bằng Stage0.

```text
Stage0
  +
Axiom compiler source
  ↓
Stage1
```

---

# 586.10. Stage1 source

Stage1 compiler source phải là source chính thức của Axiom compiler.

Không duy trì một compiler implementation song song chỉ để bootstrap.

---

# 586.11. Stage1 capabilities

Stage1 phải có khả năng build:

```text
compiler
runtime
stdlib
tools
programs
```

theo target/profile tương ứng.

---

# 586.12. Stage2

Stage2 được tạo bởi Stage1:

```text
Stage1
  +
same compiler source
  ↓
Stage2
```

---

# 586.13. Self-hosting criterion

Axiom được xem là self-hosted khi Stage1 có thể build Stage2 và Stage2 có thể build lại chính compiler source mà không cần Stage0.

---

# 586.14. Stage2 independence

Stage2 không được link Stage0 runtime/compiler components.

---

# 586.15. Bootstrap closure

Dependency graph cuối:

```text id="q3g5ta"
Stage2
 ├── Axiom compiler
 ├── Axiom runtime
 └── Axiom std/core
```

không:

```text
Stage0
GCC
Clang
LLVM
MSVC
```

trừ external interoperability mà build profile explicitly yêu cầu.

---

# 586.16. Compiler source graph

Compiler source phải build được theo graph:

```text
compiler
 ├── frontend
 ├── semantic
 ├── optimizer
 ├── backend
 ├── linker
 ├── image builder
 ├── diagnostics
 └── tooling
```

---

# 586.17. Runtime graph

Compiler runtime source độc lập với compiler executable.

```text
Compiler
    │
    └── builds Runtime
```

Compiler không được cần runtime hosted đầy đủ để bootstrap.

---

# 586.18. Core runtime bootstrap

`core` phải build được ở profile minimal/freestanding.

---

# 586.19. Standard library bootstrap

Standard library chia:

```text id="std586"
core
alloc
platform
std
```

theo `433`.

---

# 586.20. Bootstrap dependency ordering

Canonical:

```text
core
 ↓
alloc
 ↓
platform
 ↓
std
 ↓
compiler
 ↓
tools
```

Compiler components không được tạo dependency cycle với hosted std.

---

# 586.21. Compiler freestanding core

Các compiler primitive cần cho Stage0/Stage1 phải tồn tại trong core-compatible environment.

---

# 586.22. Compiler allocator

Compiler có thể sử dụng allocator riêng.

Không yêu cầu application allocator semantics.

---

# 586.23. Compiler runtime isolation

Compiler runtime và application runtime là hai dependency contexts.

---

# 586.24. Compiler startup

Compiler executable sử dụng `585` startup nhưng chỉ kéo runtime components compiler thực sự cần.

---

# 586.25. Bootstrap build profile

Canonical profile:

```text
bootstrap
```

được định nghĩa riêng.

---

# 586.26. Bootstrap optimization

Stage0 có thể dùng optimization thấp hơn Stage1/Stage2 để giảm complexity.

---

# 586.27. Stage2 optimization

Stage2 phải được build bằng production optimization policy.

---

# 586.28. Bootstrap reproducibility

Same:

```text source
bootstrap seed
target
configuration
```

phải produce deterministic compiler artifact trong reproducible mode.

---

# 586.29. Stage identity

Mỗi artifact mang:

```text id="stageid586"
stage
compiler_version
source_hash
target
configuration
```

---

# 586.30. Compiler source hash

Source identity phải tính từ canonical source graph, không phụ thuộc filesystem ordering.

---

# 586.31. Build graph identity

Build graph identity bao gồm:

```text source
dependencies
compiler configuration
target
features
environment policy
```

---

# 586.32. Host contamination

Compiler không được vô tình embed:

- host absolute path;
- hostname;
- username;
- current time;
- temporary path.

trong reproducible artifact.

---

# 586.33. Host target separation

```text
host target
    ≠
compiler target
    ≠
application target
```

có thể khác nhau.

---

# 586.34. Canadian cross

Axiom phải support:

```text id="cross586"
build compiler on A
compiler runs on B
compiler produces C
```

---

# 586.35. Cross compiler identity

Cross compiler phải explicit:

```text host
target
runtime target
ABI
```

---

# 586.36. Bootstrap target matrix

Ví dụ:

```text
Host       Target
Windows    Linux
Linux      Windows
Linux      macOS*
Linux      WASM
Windows    Android
```

`*` chỉ khi SDK/signing requirements được cung cấp hợp lệ.

---

# 586.37. Native backend independence

Cross compiler sử dụng backend Axiom từ `562+`.

Không invoke host compiler.

---

# 586.38. Native linker independence

Cross compilation sử dụng linker Axiom `582`.

---

# 586.39. Native image independence

Cross compilation sử dụng image builder `584`.

---

# 586.40. Runtime target selection

Runtime phải được compile cho **target**, không phải host.

---

# 586.41. Host tool execution

Build tools chạy trên host.

Target runtime không được chạy nhầm trên host trong build graph.

---

# 586.42. Build tool classification

Mỗi executable được classify:

```text
BuildTool
HostTool
TargetProgram
TargetRuntime
```

---

# 586.43. Build tool boundary

Host tool không được tự động trở thành target dependency.

---

# 586.44. Compiler plugins

Compiler plugins phải declare execution target.

---

# 586.45. Code generation tools

Code generators chạy host-side trừ khi explicitly cross-executable.

---

# 586.46. Stage bootstrap manifest

Bootstrap manifest phải declare:

```text
stage0
compiler_sources
bootstrap_subset
target
runtime
features
verification_policy
```

---

# 586.47. Stage1 build

Pseudo-flow:

```text
stage0 compile compiler/
       ↓
stage1 compiler
       ↓
stage1 verify
```

---

# 586.48. Stage2 build

```text
stage1 compile compiler/
       ↓
stage2 compiler
       ↓
stage2 verify
```

---

# 586.49. Stage2 rebuild

```text
stage2 compile compiler/
       ↓
stage3 candidate
```

---

# 586.50. Fixed-point condition

Self-hosting convergence:

```text
Compiler(N+1)
    ≡
Compiler(N)
```

theo semantic/compiler artifact verification policy.

---

# 586.51. Byte equality

Byte equality là mục tiêu trong reproducible build nhưng không phải tiêu chí semantic duy nhất.

---

# 586.52. Semantic equivalence

Nếu bytes khác do explicitly allowed nondeterministic metadata, compiler correctness vẫn phải được kiểm tra semantic equivalence.

---

# 586.53. Compiler output comparison

Compare:

```text
binary hash
section layout
symbol graph
machine code
debug identity
runtime dependency graph
```

---

# 586.54. Translation validation

Stage transitions có thể dùng `552`:

```text
Stage1 output
       ↓
translation validation
       ↓
Stage2 output
```

---

# 586.55. Compiler self-test

Mỗi bootstrap stage chạy:

```text
parser tests
semantic tests
IR tests
backend tests
linker tests
runtime tests
integration tests
```

---

# 586.56. Bootstrap test suite

Bootstrap suite là subset độc lập, không được yêu cầu compiler đã hoàn thiện mới có thể chạy.

---

# 586.57. Golden tests

Compiler source → expected semantic/IR/machine artifacts.

---

# 586.58. Differential tests

Stage0/Stage1/Stage2 có thể compile cùng input và compare semantic output.

---

# 586.59. Miscompilation detection

Mismatch phải tạo diagnostic:

```text
stage
source
target
function
IR phase
output hash
```

---

# 586.60. Compiler crash

Compiler crash trong bootstrap là build failure, không được fallback âm thầm sang external compiler.

---

# 586.61. Bootstrap fallback prohibition

Build system không được:

```text
Axiom compiler failed
    ↓
invoke GCC/Clang
```

trong bootstrap profile.

---

# 586.62. External compiler quarantine

External compilers chỉ được sử dụng bởi explicit interoperability/bootstrap-experimental profile.

---

# 586.63. Trusted seed verification

Stage0 binary phải có:

```text
hash
version
target
provenance
```

---

# 586.64. Stage0 provenance

Source/build provenance phải được lưu trong bootstrap manifest.

---

# 586.65. Seed replacement

Stage0 có thể được thay thế khi trust root được re-established.

---

# 586.66. Trust chain

```text id="trust586"
Stage0
  ↓
Stage1 verification
  ↓
Stage2 verification
  ↓
Self-rebuild verification
  ↓
Release compiler
```

---

# 586.67. Compiler artifact signing

Release compiler có thể được signed sau khi deterministic build hoàn thành.

---

# 586.68. Signature boundary

Signing:

```text
build
 ↓
verify
 ↓
sign
```

không:

```text
build
 ↓
sign
 ↓
modify
```

---

# 586.69. Compiler update

Compiler update phải verify source + dependency graph trước build.

---

# 586.70. Bootstrap lockfile

Bootstrap dependencies phải có immutable version/hash identity.

---

# 586.71. Dependency minimization

Bootstrap compiler không được phụ thuộc package ecosystem để compile chính nó nếu dependency đó chưa nằm trong trusted bootstrap closure.

---

# 586.72. Bootstrap package set

Một package set tối thiểu:

```text
axiom.core
axiom.alloc
axiom.compiler.runtime
axiom.compiler
```

---

# 586.73. Circular compiler dependency

Compiler không được yêu cầu compiler package đã được build trước đó như runtime dependency.

---

# 586.74. Compiler source embedding

Compiler có thể embed:

- target tables;
- diagnostics;
- builtin definitions;
- language metadata.

Các dữ liệu này phải được generated deterministically.

---

# 586.75. Generated source

Generated compiler source phải có provenance:

```text
generator
input hash
generator version
```

---

# 586.76. Generated target tables

ISA tables từ `562` có thể được generated từ declarative target description.

---

# 586.77. Self-generated backend

Stage1/Stage2 phải có khả năng build backend target tables mà không cần host compiler.

---

# 586.78. Compiler resource embedding

Compiler resources phải được embedded hoặc packaged deterministically.

---

# 586.79. Compiler metadata

Compiler có thể embed machine-readable semantic metadata từ `446`.

---

# 586.80. AI-readable compiler

Self-hosted compiler phải expose semantic query interface cho:

```text
types
symbols
IR
diagnostics
source maps
dependencies
```

---

# 586.81. Compiler query server

Compiler daemon `555` có thể chạy trên host và sử dụng compiler core self-hosted.

---

# 586.82. Bootstrap daemon prohibition

Daemon không được trở thành hidden prerequisite của CLI compiler.

---

# 586.83. Cold compiler

Compiler phải hoạt động khi daemon chưa chạy.

---

# 586.84. Compiler cache

Cache artifacts phải include compiler identity.

---

# 586.85. Cross-stage cache isolation

Stage0 cache không được dùng làm Stage2 cache nếu identity khác.

---

# 586.86. Bootstrap cache invalidation

Thay đổi compiler source → invalidation compiler artifacts downstream.

---

# 586.87. Compiler ABI stability

Compiler internal ABI không cần stable giữa versions.

---

# 586.88. Runtime ABI stability

Public runtime/FFI ABI phải follow `421/447`.

---

# 586.89. Compiler/plugin ABI

Compiler extension ABI phải version independently.

---

# 586.90. Compiler bootstrap on new target

Để bootstrap target mới:

```text
existing trusted compiler
        ↓
cross compile Stage1
        ↓
native Stage1
        ↓
native Stage2
```

---

# 586.91. Target bring-up order

Target mới phải có:

```text
Target Description
 ↓
ABI
 ↓
Machine Backend
 ↓
Object Writer
 ↓
Linker
 ↓
Image Builder
 ↓
Startup
 ↓
Runtime
 ↓
Self-hosted compiler
```

---

# 586.92. WASM bootstrap

WASM compiler có thể bootstrap từ native host:

```text
native Axiom compiler
       ↓
WASM compiler
```

sau đó compiler WASM phải có khả năng build WASM Axiom programs.

---

# 586.93. Freestanding compiler

Compiler có thể được build freestanding/minimal cho constrained environments nếu required.

---

# 586.94. Compiler startup dependencies

Compiler CLI hosted executable không được kéo GUI/network runtime nếu không dùng.

---

# 586.95. Compiler crash recovery

Build orchestrator phải giữ stage artifacts để chẩn đoán failed bootstrap.

---

# 586.96. Atomic stage publication

Stage1/Stage2 chỉ được publish sau khi verification hoàn thành.

```text
candidate
   ↓
verify
   ↓
atomic publish
```

---

# 586.97. Corrupt stage

Corrupt artifact không được trở thành trusted stage.

---

# 586.98. Rebuild-from-source test

Release pipeline phải periodically rebuild compiler từ source.

---

# 586.99. Bootstrap-from-seed test

Release pipeline phải test:

```text
seed
 → stage1
 → stage2
 → release
```

không lấy shortcut từ binary release hiện tại.

---

# 586.100. Two-way verification

Không chỉ:

```text
compiler builds compiler
```

mà còn:

```text
compiler source
 ↔
semantic model
 ↔
generated compiler
```

---

# 586.101. Compiler self-inspection

Compiler phải có thể query chính source/semantic model của nó.

---

# 586.102. Self-hosting diagnostics

Bootstrap mismatch phải report phase-specific diagnostic.

---

# 586.103. Trust report

Bootstrap pipeline sinh:

```text id="trustreport586"
Stage0 hash
Stage1 hash
Stage2 hash
source hash
dependency hash
target
verification results
```

---

# 586.104. Reproducible report

Report phải deterministic ngoại trừ external signing metadata.

---

# 586.105. Compiler release artifact

Release bundle:

```text id="bundle586"
compiler
runtime
stdlib
target SDK metadata
debug symbols
semantic metadata
manifest
checksums
```

---

# 586.106. Minimal compiler distribution

Có thể phát hành compiler không có:

- docs;
- debug symbols;
- optional target backends;
- GUI;
- AI tooling;

nếu các thành phần đó được tách package.

---

# 586.107. Full SDK distribution

Full SDK có thể bao gồm:

```text
compiler
linker
formatter
LSP
debugger integration
package manager
AI semantic service
target SDKs
```

---

# 586.108. Compiler update compatibility

Compiler mới phải đọc project metadata theo language edition compatibility policy `484`.

---

# 586.109. Bootstrap version pinning

Bootstrap source phải pin compiler language version đủ để tránh circular version dependency.

---

# 586.110. Bootstrap language subset evolution

Bootstrap subset chỉ được mở rộng khi Stage0 implementation tương ứng đã được verified.

---

# 586.111. Compiler feature gating

Feature chưa bootstrap-safe không được sử dụng trong compiler source.

---

# 586.112. Bootstrap-safe standard library

Compiler source chỉ dùng APIs có mặt trong bootstrap closure.

---

# 586.113. No hidden host API

Compiler source không được trực tiếp phụ thuộc platform-specific host API ngoài platform abstraction.

---

# 586.114. Host abstraction

Compiler filesystem/process/thread APIs đi qua compiler platform layer.

---

# 586.115. Compiler determinism

Compiler phải deterministic với:

```text source
target
configuration
dependency graph
```

trong deterministic mode.

---

# 586.116. Parallel bootstrap

Bootstrap compilation có thể parallelize nhưng output phải deterministic.

---

# 586.117. Distributed bootstrap

Stage builds có thể remote-execute qua `567`, nhưng trusted artifact phải pass verification.

---

# 586.118. Hermetic bootstrap

Bootstrap environment phải pin:

```text compiler seed
source
dependencies
target description
build configuration
```

---

# 586.119. Environment whitelist

Environment variables chỉ được ảnh hưởng build nếu manifest cho phép.

---

# 586.120. Network prohibition

Bootstrap build mặc định không truy cập network.

Dependency artifacts phải có sẵn trong trusted input set.

---

# 586.121. Time prohibition

Compiler semantic output không phụ thuộc wall clock.

---

# 586.122. Randomness prohibition

Compiler semantic output không sử dụng randomness không deterministic.

---

# 586.123. Filesystem ordering

Directory enumeration không được ảnh hưởng compiler output.

---

# 586.124. Path normalization

Paths canonicalized trước khi trở thành compiler identity.

---

# 586.125. Debug path policy

Debug paths có thể preserve source identity nhưng reproducible mode phải canonicalize path mapping.

---

# 586.126. Compiler correctness gate

Một stage chỉ được promote khi:

```text
frontend tests       PASS
semantic tests       PASS
IR tests              PASS
backend tests         PASS
linker tests          PASS
runtime tests         PASS
bootstrap tests       PASS
reproducibility       PASS
```

---

# 586.127. Backend correctness

Mỗi bootstrap target phải pass translation validation từ `552/575`.

---

# 586.128. Linker correctness

Native bootstrap executable phải pass image verification từ `584`.

---

# 586.129. Startup correctness

Compiler executable phải pass `585` startup tests.

---

# 586.130. Runtime correctness

Compiler runtime phải pass allocator/TLS/thread/panic tests.

---

# 586.131. Compiler self-test execution

Compiler build phải test executable thực sự chạy, không chỉ kiểm tra file tồn tại.

---

# 586.132. Compiler self-compilation test

Test:

```text
compiler source
 ↓
Stage2
 ↓
compile representative Axiom projects
 ↓
execute outputs
```

---

# 586.133. Regression corpus

Bootstrap corpus phải bao gồm:

- language core;
- generics;
- traits;
- async;
- concurrency;
- FFI;
- SIMD;
- GUI;
- networking;
- compiler itself.

---

# 586.134. Stress compilation

Test compiler với:

- project lớn;
- nhiều module;
- deep generics;
- large generated code;
- high parallelism.

---

# 586.135. Memory stress

Compiler phải không phụ thuộc accidental host memory limits.

---

# 586.136. Out-of-memory behavior

Compiler OOM phải fail cleanly thay vì tạo corrupted artifact.

---

# 586.137. Interrupted build

Interrupted bootstrap không được publish partial stage.

---

# 586.138. Crash-safe publication

Artifact publication sử dụng atomic rename/commit semantics.

---

# 586.139. Compiler installation

Installation phải atomically replace compiler toolchain.

---

# 586.140. Rollback

Failed compiler update phải có rollback tới verified version.

---

# 586.141. Multiple toolchains

Có thể cài song song:

```text
Axiom 1.x
Axiom 2.x
```

với explicit selection.

---

# 586.142. Toolchain identity

Toolchain identity:

```text
language edition
compiler version
target
runtime ABI
stdlib version
```

---

# 586.143. Compiler invocation

CLI phải cho phép inspect:

```text
axiom --version
axiom --target
axiom --runtime
axiom --bootstrap-status
```

---

# 586.144. Bootstrap status

Compiler có thể report:

```text
Stage
Trusted
SelfHosted
Reproducible
Targets
```

---

# 586.145. Trust downgrade

Nếu binary bị modified sau verification:

```text
Trusted → Untrusted
```

---

# 586.146. Signature verification

Release installer có thể verify compiler signature trước installation.

---

# 586.147. Compiler binary provenance

Compiler binary phải có machine-readable provenance metadata.

---

# 586.148. Supply-chain integration

Bootstrap trust report tích hợp với package/security system `549/550`.

---

# 586.149. Self-hosted compiler as canonical implementation

Sau khi self-hosting hoàn tất:

> **Axiom compiler source written in Axiom trở thành canonical compiler implementation.**

---

# 586.150. Stage0 as emergency recovery

Stage0 được giữ như recovery/bootstrap artifact, không phải normal compiler dependency.

---

# 586.151. Compiler resurrection

Nếu toàn bộ binary toolchain mất:

```text
trusted Stage0
 +
compiler source
 +
bootstrap dependencies
```

phải đủ để tái tạo toolchain.

---

# 586.152. Offline resurrection

Bootstrap recovery phải có khả năng chạy offline.

---

# 586.153. Minimal recovery bundle

Recovery bundle tối thiểu:

```text id="recover586"
Stage0
compiler source
bootstrap manifest
bootstrap packages
target descriptions
trusted hashes
```

---

# 586.154. Recovery target

Ít nhất phải recover native compiler cho host target được support.

---

# 586.155. Recovery verification

Compiler rebuilt từ recovery bundle phải pass Stage1/Stage2 verification.

---

# 586.156. Compiler source immutability

Không có requirement source phải immutable, nhưng mỗi release build phải pin exact source revision/hash.

---

# 586.157. Bootstrap audit trail

Mỗi release phải lưu:

```text source identity
bootstrap chain
verification results
target matrix
dependency closure
```

---

# 586.158. Self-hosting completion criterion

Axiom self-hosting được đánh dấu complete khi:

```text
Stage0 → Stage1 → Stage2
```

và:

```text Stage2 → Stage3
```

đạt semantic/reproducibility policy.

---

# 586.159. No circular trust

Không được verify Stage2 bằng chính Stage2 mà không có independent comparison.

Phải có ít nhất một verification path độc lập:

```text Stage0/independent validator
```

hoặc trusted artifact/reference execution.

---

# 586.160. Independent validator

Validator có thể nhỏ hơn compiler và chỉ cần verify:

- artifact structure;
- hashes;
- semantic fingerprints;
- selected compiler invariants.

---

# 586.161. Diverse verification

Có thể build compiler bằng:

```text Stage0 path
```

và kiểm tra bằng:

```text independent validation path
```

để giảm single-point trust.

---

# 586.162. Compiler miscompilation containment

Nếu compiler tự miscompile chính nó, bootstrap comparison phải detect divergence trước release.

---

# 586.163. Self-hosted release gate

Không release compiler mới nếu bootstrap verification fail.

---

# 586.164. Compiler correctness ≠ bootstrap equality

Byte equality không chứng minh compiler correctness tuyệt đối.

Bootstrap verification phải kết hợp:

```text reproducibility
+
tests
+
translation validation
+
differential testing
+
artifact inspection
```

---

# 586.165. Final bootstrap architecture

```text id="final586"
                  Trusted Seed
                       │
                       ▼
                    Stage0
                       │
             ┌─────────┴─────────┐
             │                   │
       compile compiler      validate seed
             │
             ▼
          Stage1
             │
       self-compile
             ▼
          Stage2
             │
      ┌──────┼───────┐
      ▼      ▼       ▼
   verify  rebuild  tests
      │      │       │
      └──────┼───────┘
             ▼
      Trusted Compiler
             │
       ┌─────┴─────┐
       ▼           ▼
  Native targets  WASM
```

---

# 586.166. FINAL HARD INVARIANT

> **Axiom phải có một bootstrap chain hoàn chỉnh từ Stage0 tới compiler self-hosted; Stage1 và Stage2 phải được xây bằng chính Axiom compiler source, có khả năng tự build compiler/runtime/stdlib, cross-compile target được hỗ trợ, tái tạo deterministic và được kiểm chứng bởi một verification path độc lập. Stage0 chỉ là trusted recovery/bootstrap root, không phải dependency của compiler release thông thường. Không được âm thầm fallback sang GCC/Clang/LLVM/MSVC hoặc compiler bên ngoài để hoàn thành bootstrap.**

# 586 — LOCKED

Tới đây Axiom đã có một vòng khép kín:

```text id="axiomclosed586"
             Axiom Source
                  │
                  ▼
             Axiom Compiler
                  │
       ┌──────────┼───────────┐
       ▼          ▼           ▼
     Code       Runtime      Tools
       │          │           │
       └──────────┼───────────┘
                  ▼
          Axiom Native Backend
                  │
                  ▼
              Object/Link
                  │
                  ▼
             Final Image
                  │
                  ▼
             Axiom Startup
                  │
                  ▼
              Axiom App
```

Và với compiler:

```text
Stage0
  ↓
Stage1
  ↓
Stage2
  ↓
Stage2 rebuild
  ↓
verified self-hosted compiler
```

Điểm quan trọng là từ đây **Axiom không còn phụ thuộc khái niệm vào “compiler bên ngoài” để tồn tại**. External toolchain chỉ còn là interoperability/validation/bootstrap-recovery tùy trường hợp.

---

# NEXT — BOOTSTRAP-587

## COMPILER BOOTSTRAP TRUST & DIVERGENT COMPILATION 3.0
### 3-STAGE SELF-REBUILD, DIVERGENT COMPILER VALIDATION, N-LEVEL BOOTSTRAP, TRANSLATION VALIDATION, COMPILER FINGERPRINT, TRUSTED SEED ROTATION & SUPPLY-CHAIN COMPILER INTEGRITY

```text id="next587"
              Trusted Stage0
                    │
          ┌─────────┴─────────┐
          ▼                   ▼
       Build A             Build B
          │                   │
          ▼                   ▼
       Stage1-A            Stage1-B
          │                   │
          └─────────┬─────────┘
                    ▼
             Divergence Check
                    │
                    ▼
                Stage2
                    │
          ┌─────────┼─────────┐
          ▼         ▼         ▼
       Fingerprint Rebuild  Translation
          │         │         │
          └─────────┼─────────┘
                    ▼
              Trust Decision
                    │
                    ▼
             Trusted Compiler
```

`587` sẽ đi sâu hơn `586`: không chỉ chứng minh compiler **tự build được chính nó**, mà xây cơ chế phát hiện compiler seed hoặc compiler stage bị lỗi/can thiệp thông qua **divergent compilation và independent compiler fingerprints**, đồng thời cho phép Axiom thay đổi trusted Stage0 mà không phá vòng bootstrap.