# BOOTSTRAP-483 — COMPILER DISTRIBUTION, TOOLCHAIN PACKAGING, INSTALLATION, TARGET SDK & CROSS-COMPILATION TOOLCHAIN MODEL

**Trạng thái: COMPLETED / LOCKED**

483 định nghĩa cách Axiom compiler được **phân phối, cài đặt, cập nhật, cross-compile và quản lý target/toolchain** mà không làm mất nguyên tắc compiler native độc lập của Axiom.

Kiến trúc:

```text id="2k6j0p"
                    AXIOM INSTALLATION
                           │
             ┌─────────────┼─────────────┐
             ↓             ↓             ↓
          Compiler       Targets       Packages
             │             │             │
             ↓             ↓             ↓
        axiomc/cli     Target SDK    Registry/Cache
             │             │
             └──────┬──────┘
                    ↓
              Build Graph
                    │
          ┌─────────┼─────────┐
          ↓         ↓         ↓
       Native      WASM     Cross Native
```

---

## 483.1 — Compiler distribution ≠ language runtime

Gói compiler:

```text id="1n6qad"
Axiom Toolchain
```

không đồng nghĩa application phải ship compiler/runtime.

Application chỉ link runtime capabilities mà nó sử dụng.

---

## 483.2 — Toolchain components

Canonical components:

```text id="pr5y4j"
axiom
axiomc
axiom-lsp
axiom-fmt
axiom-doc
axiom-pkg
axiom-test
axiom-debug
axiom-prof
target SDKs
standard library
compiler metadata
```

Một số có thể được đóng gói chung hoặc tách package.

---

## 483.3 — Minimal compiler installation

Có thể cài:

```text id="j1v7h3"
compiler
core
target
```

mà không cài:

- GUI tools;
- profiler;
- documentation server;
- optional SDKs.

---

## 483.4 — Toolchain manifest

Concept:

```text id="3ak6os"
ToolchainManifest {
    version
    channel
    compiler_build_id
    host_target
    supported_targets
    components
    stdlib_version
    metadata_version
    checksums
}
```

---

## 483.5 — Toolchain identity

Toolchain identity gồm:

```text id="8g7jph"
compiler version
edition
build ID
target support
stdlib version
metadata schema
```

---

## 483.6 — Channel

Toolchain có thể có:

```text id="1pkwtw"
stable
beta
nightly
custom
```

Channel chỉ là distribution policy, không thay đổi language semantics ngoài explicit edition/version rules.

---

## 483.7 — Installation root

Toolchain nên có filesystem layout deterministic:

```text id="4wq3t8"
bin/
lib/
libexec/
targets/
stdlib/
metadata/
docs/
licenses/
```

---

## 483.8 — Per-user vs system installation

Hỗ trợ:

```text id="4m6f8k"
system-wide
per-user
portable
project-local
```

---

## 483.9 — Portable toolchain

Một toolchain directory có thể được copy sang máy khác cùng host/target assumptions.

Không được phụ thuộc absolute installation path trong compiler behavior.

---

## 483.10 — Project-pinned toolchain

Project có thể pin:

```text id="lyf0sn"
toolchain version
edition
target
stdlib version
```

---

## 483.11 — Toolchain lock

Project lockfile có thể ghi toolchain identity để reproducibility.

---

## 483.12 — Toolchain resolution

Resolution:

```text id="3ob6tw"
project config
    ↓
toolchain lock
    ↓
installed toolchains
    ↓
selected compiler
```

---

## 483.13 — No silent compiler upgrade

Nếu project pin exact toolchain, compiler manager không tự thay đổi compiler.

---

## 483.14 — Compatibility

Compiler phải kiểm tra:

```text id="j2czp7"
compiler ↔ edition
compiler ↔ metadata
compiler ↔ stdlib
compiler ↔ target SDK
```

---

# 483.15 — Target model

Target gồm:

```text id="j4s6r1"
Architecture
Vendor
OS
Environment
ABI
Object format
CPU features
Runtime profile
```

Ví dụ conceptual:

```text
x86_64-unknown-linux-gnu
x86_64-pc-windows-msvc
aarch64-apple-darwin
aarch64-linux-android
wasm32-unknown-web
```

Tên target là representation, không phải hard-coded semantics.

---

## 483.16 — Target specification

TargetSpec phải chứa:

```text id="k9m6p1"
pointer_width
endianness
atomic_capabilities
float_capabilities
abi
object_format
linker_model
os
runtime
cpu_features
```

---

## 483.17 — Target SDK

Target SDK chứa những thứ compiler cần để tạo artifact hợp lệ cho target:

```text id="c8w1qz"
headers/bindings metadata
system libraries
framework metadata
link metadata
startup objects nếu cần
platform manifests
```

---

## 483.18 — SDK ≠ compiler

SDK không compile Axiom source.

Nó cung cấp platform interfaces/resources.

---

## 483.19 — SDK version

SDK phải có identity/version riêng compiler.

---

## 483.20 — SDK compatibility

Compiler phải kiểm tra:

```text id="6qkzrm"
Axiom compiler
+
TargetSpec
+
SDK
```

có compatible hay không.

---

## 483.21 — Native system libraries

Axiom có thể link system libraries khi target yêu cầu.

Điều này không vi phạm:

> không phụ thuộc third-party compiler.

---

## 483.22 — C runtime

Axiom application không mặc định cần libc.

Nếu application chọn POSIX API thì package/runtime tương ứng có thể dùng system libc.

---

## 483.23 — Platform framework

Windows/macOS/iOS/Android frameworks là platform dependencies, không phải Axiom compiler dependencies.

---

# 483.24 — Cross compiler

Một compiler executable có thể:

```text id="8y0z5c"
host = Windows x86-64
target = Linux AArch64
```

---

## 483.25 — Native cross compilation

Compiler phải hỗ trợ trực tiếp:

```text id="8k2h1p"
Axiom source
→ target codegen
→ target object
→ target artifact
```

---

## 483.26 — Target backend

Target backend được chọn bởi target architecture/ABI.

---

## 483.27 — Target linker

Axiom linker có thể link:

- Axiom objects;
- compatible native objects;
- system libraries;
- platform frameworks.

---

## 483.28 — Foreign object compatibility

Foreign object chỉ được link nếu:

```text id="x1j7q4"
architecture
ABI
object format
relocations
symbol convention
```

compatible.

---

## 483.29 — Cross-linker independence

Axiom linker phải xử lý Axiom-generated native objects trực tiếp.

External platform linker chỉ là optional integration khi target SDK/platform yêu cầu.

---

## 483.30 — Sysroot

Cross target có thể có:

```text id="d9z3kw"
sysroot/
```

chứa target headers/libs/framework metadata.

---

## 483.31 — Sysroot identity

Sysroot hash/version là build fingerprint input.

---

## 483.32 — Target libraries

Standard library có thể có target-specific implementation:

```text id="z0q7ak"
std
 ├── generic
 └── platform/
      ├── windows
      ├── linux
      ├── apple
      ├── android
      └── wasm
```

---

## 483.33 — Target conditional compilation

Có thể dùng target predicates:

```text id="a3t4h9"
comptime if target.os == "windows" {
    ...
}
```

431 semantics vẫn áp dụng.

---

## 483.34 — CPU feature selection

Compiler có thể target:

```text id="q4h9xk"
baseline
native
specific CPU
feature-set
```

---

## 483.35 — CPU feature safety

Code chỉ được emit instruction được target profile cho phép.

---

## 483.36 — Runtime CPU dispatch

Có thể compile nhiều variants:

```text id="4rj7wq"
baseline
avx2
avx512
```

và chọn runtime khi CPU capability được kiểm tra.

---

## 483.37 — Cross compilation vs runtime dispatch

Cross compilation quyết định artifact target.

Runtime dispatch quyết định variant execution trên cùng target family.

---

## 483.38 — WASM target

WASM toolchain:

```text id="4vq8xg"
Axiom
 ↓
WASM backend
 ↓
WASM artifact
 ↓
host/runtime/browser
```

---

## 483.39 — WASM imports

Imports/exports phải explicit.

---

## 483.40 — Mobile targets

iOS/Android target cần:

- architecture;
- ABI;
- SDK;
- linker metadata;
- application packaging metadata;
- signing integration.

Compiler core không tự động trở thành mobile build system.

---

# 483.41 — Target capabilities

Toolchain phải expose:

```text id="z0z0kn"
supports(target, capability)
```

Ví dụ:

```text SIMD
threads
atomics
TLS
dynamic libraries
JIT
GPU
debug info
sanitizer
```

---

## 483.42 — Capability mismatch

Nếu source yêu cầu capability target không có:

```text id="8s7h7m"
compile-time diagnostic
```

thay vì tạo artifact không hợp lệ.

---

## 483.43 — Feature profiles

Build có thể chọn:

```text id="t8x2sn"
generic
native
embedded
freestanding
server
mobile
wasm
```

Profile là configuration layer, không thay đổi core semantics.

---

## 483.44 — Freestanding toolchain

Toolchain phải hỗ trợ target không có:

- OS;
- libc;
- dynamic loader;
- filesystem;
- threads.

---

## 483.45 — Embedded target

Target SDK có thể cung cấp:

```text id="p7r2mn"
startup
memory map
interrupt metadata
MMIO definitions
linker layout
```

---

## 483.46 — Linker script

Một số target cần linker layout.

Axiom linker phải có native layout model; external linker scripts có thể được imported explicitly.

---

## 483.47 — Bare-metal entry

Application có thể chỉ định:

```text id="8y0z9f"
@entry
fn reset() { ... }
```

theo target/runtime contract.

---

## 483.48 — Target SDK packaging

SDK có thể được package:

```text id="u5j0rb"
.axsdk
```

hoặc equivalent directory/archive representation.

Format có version và hash.

---

## 483.49 — SDK integrity

SDK contents phải có:

```text id="5b4h6k"
manifest
version
checksums
provenance
```

---

## 483.50 — SDK trust

SDK được coi là external trust input.

Compiler không được giả định SDK metadata luôn đúng.

---

## 483.51 — Target metadata cache

Target metadata có thể cache.

Cache key:

```text id="9d8h0w"
SDK hash
TargetSpec hash
Compiler version
```

---

## 483.52 — Offline cross compilation

Nếu SDK đã cài local:

```text id="w0f6gc"
axiom build --target ...
```

không cần network.

---

## 483.53 — No central registry requirement

Compiler manager không cần một central server để function.

---

## 483.54 — Toolchain download

Distribution manager có thể tải:

- compiler;
- target SDK;
- stdlib;
- optional tools.

Download layer phải verify checksum/signature.

---

## 483.55 — Signature

Toolchain releases có thể được signed.

---

## 483.56 — Update

Update phải atomic:

```text id="r7p5s4"
download
→ verify
→ install staging
→ activate
```

---

## 483.57 — Rollback

Nếu update lỗi:

```text id="l5g2xy"
previous toolchain
```

vẫn usable.

---

## 483.58 — Multiple toolchains

Nhiều compiler versions có thể tồn tại đồng thời.

---

## 483.59 — Project isolation

Project A dùng toolchain A.

Project B có thể dùng toolchain B trên cùng máy.

---

## 483.60 — CI

CI nên có command:

```text id="f7u1dq"
axiom toolchain install
axiom toolchain use
axiom toolchain verify
```

---

## 483.61 — Toolchain cache

Downloaded artifacts có thể cache bằng content hash.

---

## 483.62 — Cache deduplication

Các toolchain chia sẻ identical components có thể deduplicate storage.

---

## 483.63 — Reproducibility

Build record phải lưu:

```text id="b3f8m7"
compiler
stdlib
target
SDK
sysroot
profile
features
dependencies
```

---

## 483.64 — Artifact provenance

Native artifact phải có thể truy ngược:

```text id="5v1qwe"
artifact
 ↓
build
 ↓
compiler
 ↓
source
 ↓
dependencies
 ↓
target SDK
```

---

## 483.65 — Toolchain/Package separation

447 package dependency không được tự động kéo compiler/toolchain dependency vào application runtime.

---

## 483.66 — Binary package

Binary package có thể chứa:

```text id="1y9d5c"
target-specific object/library
ABI metadata
semantic metadata
```

---

## 483.67 — Precompiled generics

447 precompiled generic instances phải match:

```text id="2x4n8c"
compiler ABI
target
CPU feature
generic semantic hash
```

---

## 483.68 — ABI mismatch

Compiler phải reject hoặc explicitly recompile incompatible binary package.

---

## 483.69 — Cross-target package resolution

Package resolver không được chọn binary artifact của target khác.

---

## 483.70 — Toolchain diagnostics

Machine-readable diagnostic phải chỉ rõ:

```text id="j3l0t6"
required target
installed target
required SDK
installed SDK
ABI mismatch
missing capability
```

---

## 483.71 — AI toolchain query

AI API:

```text id="7r3m0v"
installed_toolchains()
installed_targets()
target_capabilities()
sdk_version()
toolchain_for(project)
abi_compatibility()
```

---

## 483.72 — Environment inspection

Compiler có thể expose deterministic environment report:

```text id="d0k5rx"
host
compiler
target
SDK
CPU
OS
features
```

---

## 483.73 — No hidden environment dependency

Build result không được âm thầm phụ thuộc:

- current working directory ngoài project model;
- arbitrary PATH executable;
- hidden environment variables;
- machine-local random state.

Nếu cần, dependency phải được khai báo.

---

## 483.74 — External linker policy

Nếu target yêu cầu external platform linker, build manifest phải thể hiện rõ.

Axiom native linker vẫn là default cho Axiom-controlled object linking.

---

## 483.75 — Hard invariants

1. Toolchain distribution khác application runtime.
2. Compiler components được modular hóa.
3. Minimal compiler installation được hỗ trợ.
4. Toolchain manifest có version.
5. Toolchain có build identity.
6. Target list được ghi.
7. Stdlib version được ghi.
8. Metadata schema version được ghi.
9. Stable/beta/nightly channels được hỗ trợ.
10. Installation system hỗ trợ system/user/portable/project-local.
11. Portable toolchain không phụ thuộc absolute path.
12. Project có thể pin toolchain.
13. Toolchain lock được hỗ trợ.
14. Pinned compiler không tự upgrade.
15. Compiler/edition compatibility được kiểm tra.
16. Compiler/stdlib compatibility được kiểm tra.
17. Compiler/SDK compatibility được kiểm tra.
18. Target được model độc lập.
19. TargetSpec có ABI/object/architecture information.
20. Target SDK khác compiler.
21. SDK có version.
22. SDK có integrity metadata.
23. SDK là external trust input.
24. System libraries có thể được link.
25. libc không mandatory.
26. Platform frameworks là platform dependencies.
27. Cross compilation native được hỗ trợ.
28. Host và target được phân biệt.
29. Axiom backend tạo target machine code trực tiếp.
30. Axiom linker xử lý Axiom objects trực tiếp.
31. Foreign objects phải ABI-compatible.
32. Sysroot được model hóa.
33. Sysroot identity là build input.
34. Target-specific stdlib được hỗ trợ.
35. Target conditional compilation được hỗ trợ.
36. CPU feature targeting được hỗ trợ.
37. CPU feature mismatch không được emit unsupported instructions.
38. Runtime CPU dispatch được hỗ trợ.
39. WASM là first-class target.
40. WASM imports/exports explicit.
41. Mobile target metadata được hỗ trợ.
42. Target capabilities được queryable.
43. Capability mismatch là compile-time error.
44. Build profiles được hỗ trợ.
45. Freestanding target được hỗ trợ.
46. Embedded target được hỗ trợ.
47. Bare-metal entry được hỗ trợ.
48. Linker layout được model hóa.
49. SDK package có manifest.
50. SDK package có checksum/provenance.
51. Target metadata cache có content-based key.
52. Offline cross compilation được hỗ trợ.
53. Central registry không bắt buộc.
54. Toolchain downloads được integrity-checked.
55. Toolchain signatures được hỗ trợ.
56. Toolchain updates atomic.
57. Toolchain rollback được hỗ trợ.
58. Multiple toolchains coexist.
59. Projects có thể dùng toolchain khác nhau.
60. CI có deterministic toolchain selection.
61. Toolchain cache content-addressed.
62. Identical components có thể deduplicate.
63. Build record ghi compiler/stdlib/target/SDK.
64. Artifact provenance được giữ.
65. Toolchain không bị kéo vào application runtime.
66. Binary packages có ABI metadata.
67. Precompiled generics có semantic identity.
68. ABI mismatch phải được detect.
69. Cross-target package mismatch phải bị reject.
70. Toolchain diagnostics machine-readable.
71. AI có thể query toolchain state.
72. Environment report deterministic.
73. Hidden environment dependency bị cấm.
74. External linker dependency phải explicit.
75. Axiom native compiler independence được giữ.
76. Không mandatory LLVM/GCC/Clang/MSVC compiler chain.
77. Không mandatory libc.
78. Không mandatory network để build khi dependencies/SDK đã local.
79. Toolchain security là một phần supply-chain model.
80. **Axiom distribution/toolchain model phải cho phép một compiler duy nhất quản lý nhiều target native/WASM, cross-compile offline và reproducibly, trong khi compiler, SDK, package dependency và application runtime vẫn là bốn lớp độc lập.**

**BOOTSTRAP-483 hoàn tất / LOCKED.**

---

# BOOTSTRAP-484 — LANGUAGE VERSIONING, EDITIONS, FEATURE GATES, COMPATIBILITY & LONG-TERM EVOLUTION

484 sẽ khóa cơ chế để Axiom có thể **phát triển trong nhiều năm mà không phá code cũ một cách tùy tiện**.

Kiến trúc:

```text id="f5k2z9"
                 Axiom Language
                       │
                ┌──────┴──────┐
                ↓             ↓
             Edition       Version
                │             │
                ↓             ↓
          Language Rules   Compiler
                │             │
                └──────┬──────┘
                       ↓
                 Feature Gates
                       │
              ┌────────┼────────┐
              ↓        ↓        ↓
           Stable   Experimental  Removed
```

## 484.1 — Language version ≠ compiler version

Ví dụ:

```text id="6v8h4k"
Language: 1.4
Compiler: 1.7.2
```

Compiler version là implementation release.

Language version là language contract.

---

## 484.2 — Edition

Edition là một tập grammar/semantic compatibility rules ổn định.

---

## 484.3 — Edition không fork language

Mục tiêu là:

```text id="h3q2s6"
old source
   ↓
new compiler
```

vẫn compile được trong edition tương ứng.

---

## 484.4 — Explicit edition

Project manifest phải có edition:

```text id="8m3v5n"
edition = "2026"
```

Không dựa vào compiler version để suy luận.

---

## 484.5 — Default edition

Compiler có thể có default edition cho project mới.

Project cũ không tự động chuyển edition.

---

## 484.6 — Edition migration

Tooling:

```text id="6d4y8q"
axiom migrate
```

có thể phân tích source và đề xuất migration.

---

## 484.7 — Mechanical migration

Migration tool chỉ được tự động sửa transformation đã xác định semantics.

---

## 484.8 — Semantic migration

Nếu thay đổi có thể ảnh hưởng behavior, tool phải tạo diagnostic thay vì silently rewrite.

---

## 484.9 — Feature gates

Experimental feature có thể yêu cầu:

```text id="n6k1w8"
@feature("name")
```

hoặc package/project feature configuration.

---

## 484.10 — Feature states

```text id="c8p4ra"
experimental
preview
stable
deprecated
removed
```

---

## 484.11 — Experimental feature

Không có compatibility guarantee hoàn chỉnh.

---

## 484.12 — Preview

Feature gần stable nhưng semantics vẫn có thể thay đổi trong giới hạn được công bố.

---

## 484.13 — Stable

Feature thuộc language contract.

---

## 484.14 — Deprecated

Compiler cảnh báo và cung cấp migration path nếu có.

---

## 484.15 — Removed

Feature bị loại chỉ theo edition/version policy rõ ràng.

---

## 484.16 — Compatibility layers

Compiler có thể hỗ trợ compatibility syntax/semantic lowering.

---

## 484.17 — No silent semantic change

Compiler update không được âm thầm thay đổi meaning của stable source trong cùng edition.

---

## 484.18 — Bug fixes

Compiler bug fix có thể thay đổi behavior nếu behavior cũ trái language specification.

Release notes phải phân loại đây là correction.

---

## 484.19 — Undefined behavior

Behavior thuộc UB không tạo compatibility guarantee.

Nhưng compiler không được tùy tiện mở rộng UB ngoài specification.

---

## 484.20 — ABI version

ABI version độc lập với language version.

---

## 484.21 — Standard library version

Stdlib version độc lập với language edition.

---

## 484.22 — Package version

Package version độc lập compiler/language version.

---

## 484.23 — Four-dimensional compatibility

```text id="v3r7n1"
Language
Compiler
ABI
Package/Stdlib
```

phải được kiểm tra riêng.

---

## 484.24 — Syntax compatibility

Parser phải biết edition-specific grammar.

---

## 484.25 — Semantic compatibility

Type checker/lowering phải biết edition-specific semantic rules nếu cần.

---

## 484.26 — Attribute compatibility

Unknown attributes phải có defined behavior:

- error;
- warning;
- tool-only.

Không silently thay đổi semantics.

---

## 484.27 — Reserved syntax

Axiom có thể reserve keywords/syntax cho future evolution.

---

## 484.28 — Identifier compatibility

Nếu keyword mới xung đột identifier cũ, edition mechanism xử lý migration.

---

## 484.29 — Operator evolution

Operator mới không được thay đổi parsing của stable source mà không qua edition rule.

---

## 484.30 — Type evolution

New standard types không được silently thay đổi inferred type của old source.

---

## 484.31 — Inference evolution

Inference changes phải được kiểm soát chặt vì có thể thay đổi overload/trait resolution.

---

## 484.32 — Trait evolution

Adding trait implementations có thể tạo ambiguity.

Compiler phải detect compatibility impact.

---

## 484.33 — Generic evolution

Generic solver changes phải được regression-tested.

---

## 484.34 — Const/comptime evolution

Comptime behavior phải giữ determinism và compatibility.

---

## 484.35 — Diagnostics evolution

Diagnostic wording có thể thay đổi.

Stable machine-readable diagnostic codes nên được giữ khi semantics không đổi.

---

## 484.36 — Diagnostic codes

Ví dụ:

```text id="r6v1s4"
E430xxx
E479xxx
E480xxx
```

Code phải versioned/documented.

---

## 484.37 — Source compatibility

Tooling phải có khả năng kiểm tra:

```text id="k8s5p0"
source → compiler/edition
```

---

## 484.38 — API compatibility

447 kiểm tra exported API.

---

## 484.39 — ABI compatibility

447/421 kiểm tra binary ABI.

---

## 484.40 — Semantic compatibility

Không phải API-compatible nghĩa là behavior-compatible.

Tooling phải phân biệt.

---

## 484.41 — Compatibility report

Có thể sinh:

```text id="3m9w6k"
source compatible
API compatible
ABI compatible
semantic-risk changes
```

Không gộp thành một score.

---

## 484.42 — Lockfile

Lockfile có thể pin:

```text id="w2x8fq"
compiler
edition
stdlib
dependencies
target SDK
```

---

## 484.43 — Reproducibility

484 tích hợp 482/483:

```text id="7v1n2a"
source
+
edition
+
compiler
+
stdlib
+
dependencies
+
target
+
SDK
```

→ reproducible build.

---

## 484.44 — Multi-edition workspace

Workspace có thể chứa packages dùng editions khác nhau.

---

## 484.45 — Cross-edition dependency

Package boundary phải có compatibility adapter nếu semantics khác.

---

## 484.46 — FFI versioning

FFI ABI không phụ thuộc edition syntax.

---

## 484.47 — Generated code

Generated code phải ghi edition/provenance.

---

## 484.48 — Macro/codegen compatibility

Generator phải biết target edition của generated source.

---

## 484.49 — Comptime compatibility

Comptime-generated semantic items phải mang version context.

---

## 484.50 — Reflection metadata

446 metadata schema version phải độc lập language edition.

---

## 484.51 — Metadata migration

Compiler có thể upgrade metadata cache.

Không được thay đổi source semantics.

---

## 484.52 — Binary metadata

Binary semantic metadata phải có schema compatibility information.

---

## 484.53 — Compiler warning policy

Deprecated features có configurable warning level.

---

## 484.54 — CI compatibility

Project có thể enforce:

```text id="n8f3u1"
no deprecated
no experimental
specific edition
specific compiler range
```

---

## 484.55 — Minimum compiler version

Package manifest có thể khai báo minimum compiler.

---

## 484.56 — Compiler range

Package có thể khai báo compatible compiler range.

---

## 484.57 — Feature capability

Dependency có thể yêu cầu feature:

```text id="3b0s5v"
requires:
    target.simd
    language.feature_x
```

---

## 484.58 — Feature resolution

Feature selection phải deterministic.

---

## 484.59 — Feature unification

Nếu package graph yêu cầu conflicting features, resolver phải báo conflict hoặc resolve theo documented rules.

---

## 484.60 — No hidden features

Dependency không được âm thầm bật project-wide compiler features ngoài manifest/configuration.

---

## 484.61 — Security

Experimental compiler features không được bypass safety/security checks chỉ vì feature enabled.

---

## 484.62 — Deprecation

Deprecation phải có:

```text id="6y1c9a"
stable replacement
migration guidance
minimum edition/compiler
```

nếu có replacement.

---

## 484.63 — Removal policy

Removal phải có:

- announcement;
- deprecation period;
- migration mechanism;

trừ security-critical emergency theo documented process.

---

## 484.64 — Language governance artifact

Language changes phải có machine-readable proposal/change record.

---

## 484.65 — Change classification

Mỗi change được classify:

```text id="d2h7pk"
bugfix
new feature
breaking language change
breaking ABI change
stdlib change
tooling change
```

---

## 484.66 — Specification source of truth

Language specification là source of truth.

Compiler behavior không tự trở thành specification chỉ vì implementation đang làm như vậy.

---

## 484.67 — Conformance

435 phải có tests cho mỗi stable semantic rule.

---

## 484.68 — Regression

Compiler changes phải chạy old-edition compatibility suite.

---

## 484.69 — Differential edition testing

Cùng source semantics có thể được compile bằng nhiều editions khi applicable.

---

## 484.70 — AI language evolution query

AI có thể query:

```text id="5m0z1x"
feature_status()
edition_changes()
migration_required()
breaking_changes()
api_compatibility()
abi_compatibility()
```

---

## 484.71 — No ranking

Compatibility tooling không được biến changes thành arbitrary “quality score”.

---

## 484.72 — Hard invariants

1. Language version khác compiler version.
2. Edition là explicit project property.
3. Edition không phải fork language.
4. Old source có thể được compile bằng newer compiler theo compatibility rules.
5. Default edition không migrate old projects.
6. Migration tooling được hỗ trợ.
7. Mechanical migration phải semantics-safe.
8. Semantic-risk migration phải diagnostic.
9. Feature gates được hỗ trợ.
10. Feature states được định nghĩa.
11. Experimental không có full stability guarantee.
12. Preview có documented compatibility scope.
13. Stable thuộc language contract.
14. Deprecated có migration path.
15. Removed chỉ theo explicit policy.
16. Stable source không bị silent semantic change trong cùng edition.
17. Compiler bug fix phải phân loại rõ.
18. UB không tạo compatibility guarantee.
19. ABI version độc lập.
20. Stdlib version độc lập.
21. Package version độc lập.
22. Language/compiler/ABI/package compatibility được kiểm tra riêng.
23. Edition-aware parser được hỗ trợ.
24. Edition-aware semantic analysis được hỗ trợ.
25. Unknown attributes có defined semantics.
26. Reserved syntax được hỗ trợ.
27. New keywords không phá old edition.
28. New operators không silently reinterpret old source.
29. New types không silently alter old inference.
30. Inference changes phải regression-tested.
31. Trait evolution phải kiểm tra ambiguity.
32. Generic solver evolution phải regression-tested.
33. Comptime evolution giữ determinism.
34. Diagnostic codes ổn định.
35. Diagnostic wording có thể evolve.
36. Source compatibility được kiểm tra.
37. API compatibility được kiểm tra.
38. ABI compatibility được kiểm tra.
39. Semantic compatibility được phân biệt.
40. Compatibility report không có aggregate score.
41. Lockfile có thể pin compiler/edition/stdlib/dependencies/target SDK.
42. Reproducibility tích hợp 482/483.
43. Multi-edition workspace được hỗ trợ.
44. Cross-edition dependencies có boundary rõ.
45. FFI ABI không phụ thuộc edition syntax.
46. Generated code có edition provenance.
47. Comptime-generated items có version context.
48. Semantic metadata có schema version.
49. Metadata migration không thay semantics.
50. CI có thể enforce edition/compiler/features.
51. Package có minimum compiler.
52. Package có compiler compatibility range.
53. Feature capabilities được khai báo.
54. Feature resolution deterministic.
55. Conflicting features phải detect.
56. Dependencies không âm thầm bật compiler features.
57. Feature gates không bypass safety.
58. Deprecation metadata machine-readable.
59. Removal policy explicit.
60. Language changes có proposal/change record.
61. Changes có classification.
62. Specification là source of truth.
63. Stable semantics có conformance tests.
64. Old editions có regression suite.
65. Edition differential testing được hỗ trợ.
66. AI có thể query evolution/compatibility.
67. Compatibility analysis không tạo ranking.
68. **Axiom phải tiến hóa được trong nhiều năm mà vẫn giữ source compatibility, ABI compatibility và reproducibility ở những nơi đã cam kết, đồng thời cho phép đổi mới thông qua editions và feature gates thay vì âm thầm thay đổi semantics của chương trình cũ.**

**BOOTSTRAP-484 hoàn tất / LOCKED.**

**Task tiếp theo: BOOTSTRAP-485 — DOCUMENTATION, API DOCS, LANGUAGE REFERENCE, EXAMPLES, DOC TESTS & KNOWLEDGE GRAPH.**