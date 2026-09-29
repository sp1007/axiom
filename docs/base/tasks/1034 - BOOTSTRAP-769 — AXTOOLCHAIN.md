# BOOTSTRAP-769 — AXTOOLCHAIN

**Title:** Native Toolchain Description, Target ABI, SDK/Sysroot, Compiler/Linker/Assembler Coordination, Cross-Compilation, Platform Integration & Toolchain Reproducibility Runtime 5.0  
**Namespace:** `AXTOOLCHAIN`  
**Phase:** Axiom Native Toolchain / Platform Targeting  
**Status:** **ARCHITECTURAL BASELINE — FROZEN TARGET 5.0**

---

# 1. Mục tiêu

`AXTOOLCHAIN` định nghĩa **toàn bộ môi trường cần thiết để biến Axiom source/IR thành native artifact cho một target cụ thể**.

```text
Source
  ↓
AXCOMPILER
  ↓
Object / IR
  ↓
AXASSEMBLER
  ↓
Object
  ↓
AXLINKER
  ↓
Native Artifact
```

`AXTOOLCHAIN` mô tả và điều phối:

- target;
- architecture;
- ABI;
- object format;
- calling convention;
- CPU features;
- compiler;
- assembler;
- linker;
- sysroot;
- SDK;
- platform libraries;
- startup objects;
- runtime components;
- debug/unwind formats;
- signing requirements;
- reproducibility identity.

Mục tiêu lớn nhất:

> **Axiom phải có khả năng tự mô tả native toolchain của chính nó và tiến tới self-hosting hoàn toàn.**

---

# 2. Boundary

`AXTOOLCHAIN` sở hữu:

- toolchain descriptor;
- target descriptor;
- ABI descriptor;
- platform descriptor;
- toolchain component graph;
- SDK/sysroot identity;
- native tool invocation contract;
- cross-compilation configuration;
- toolchain capability discovery;
- compatibility validation;
- toolchain fingerprint;
- bootstrap stage.

Không sở hữu:

```text
AXCOMPILER  → compilation semantics
AXASSEMBLER → instruction encoding
AXLINKER    → symbol/layout/link semantics
AXBUILD     → build graph/orchestration
AXPACKAGE   → package distribution
AXCRYPTO    → cryptographic primitives
AXSECURITY  → authorization
AXPROCESS   → process execution
```

---

# 3. Architecture

```text id="toolchainarch"
                       AXTOOLCHAIN
                            │
             ┌──────────────┼──────────────┐
             ▼              ▼              ▼
          TARGET           ABI          PLATFORM
             │              │              │
             └──────────────┼──────────────┘
                            ▼
                     TOOLCHAIN GRAPH
                            │
          ┌─────────────────┼─────────────────┐
          ▼                 ▼                 ▼
      AXCOMPILER        AXASSEMBLER       AXLINKER
          │                 │                 │
          └─────────────────┼─────────────────┘
                            ▼
                       SYSROOT / SDK
                            │
                            ▼
                       AXBUILD
```

---

# 4. Toolchain identity

Mỗi toolchain có:

```text id="tcid"
toolchain_id
toolchain_version
target_id
abi_id
component_set
sdk_id
sysroot_id
```

Toolchain identity phải immutable cho một published toolchain revision.

---

# 5. Target identity

```text id="target"
target_id {
    os
    architecture
    abi
    object_format
    environment
}
```

Ví dụ:

```text
windows-x86_64
linux-x86_64
linux-arm64
macos-arm64
ios-arm64
android-arm64
wasm32
```

---

# 6. Host vs target

Phải phân biệt:

```text id="hosttarget"
host
target
```

Ví dụ:

```text
host   = windows-x86_64
target = linux-arm64
```

Compiler chạy trên host nhưng sinh code cho target.

---

# 7. Build machine vs execution machine

Một artifact có:

```text id="machines"
build_host
target_machine
```

Không được assume chúng giống nhau.

---

# 8. Architecture

Architecture descriptor:

```text id="arch"
architecture {
    family
    word_size
    endianness
    registers
    instruction_set
    extensions
}
```

---

# 9. Initial architecture baseline

Axiom native toolchain phải thiết kế cho tối thiểu:

```text
x86_64
AArch64
WASM32
```

và có extension model để bổ sung architecture mới.

---

# 10. Endianness

Target phải khai báo:

```text id="endian"
LITTLE
BIG
```

Compiler không được giả định little-endian ở semantic layer.

---

# 11. Pointer width

Target ABI khai báo pointer width:

```text id="ptrwidth"
32
64
```

Pointer size không được suy ra chỉ từ OS name.

---

# 12. Data model

ABI descriptor phải định nghĩa:

```text id="datamodel"
int
long
pointer
size
time
alignment
```

Không hard-code một data model cho mọi target.

---

# 13. ABI

ABI descriptor:

```text id="abi"
abi {
    calling_convention
    register_convention
    stack_convention
    aggregate_return
    aggregate_pass
    alignment
    scalar_representation
    exception_model
    unwind_model
}
```

---

# 14. Calling convention

Toolchain phải mô tả:

```text id="callconv"
parameters
returns
register usage
stack cleanup
variadic calls
aggregate passing
```

---

# 15. Multiple calling conventions

Một target có thể hỗ trợ:

```text
axiom
c
system
fastcall
vector
platform-specific
```

Axiom ABI là default.

Foreign ABI phải explicit.

---

# 16. Function ABI

Function type metadata phải có calling convention khi ABI không phải default.

Ví dụ conceptually:

```text
extern "c" fn(...)
```

---

# 17. Struct ABI

Struct passing/returning phải được xác định theo ABI:

```text id="structabi"
register
stack
indirect
split
```

Compiler và linker phải sử dụng cùng ABI descriptor.

---

# 18. Alignment

ABI định nghĩa:

```text id="align"
natural alignment
minimum alignment
maximum alignment
stack alignment
aggregate alignment
```

---

# 19. SIMD ABI

Toolchain phải mô tả cách vector types được truyền/trả:

```text id="simdabi"
vector registers
stack spill
alignment
```

---

# 20. Floating-point ABI

Phải xác định:

```text id="fpabi"
f32
f64
extended
vector-fp
```

và register/stack conventions.

---

# 21. Object format

Toolchain descriptor:

```text id="object"
object_format
```

Initial formats:

```text
COFF
ELF
Mach-O
WASM
```

---

# 22. PE64 pipeline

Windows:

```text id="pepipeline"
Axiom source
 ↓
AXCOMPILER
 ↓
COFF object
 ↓
AXLINKER
 ↓
PE64 EXE/DLL
```

---

# 23. ELF pipeline

Linux:

```text id="elfpipeline"
Axiom source
 ↓
AXCOMPILER
 ↓
ELF relocatable
 ↓
AXLINKER
 ↓
ELF executable/shared object
```

---

# 24. Mach-O pipeline

Apple:

```text id="machopipeline"
Axiom source
 ↓
AXCOMPILER
 ↓
Mach-O object
 ↓
AXLINKER
 ↓
Mach-O executable/dylib
```

---

# 25. WASM pipeline

```text id="wasmpipeline"
Axiom source
 ↓
AXCOMPILER
 ↓
WASM module/object representation
 ↓
WASM linker
 ↓
.wasm
```

---

# 26. Relocation model

Toolchain phải mô tả:

```text id="reloc"
relocation types
symbol visibility
TLS relocation
PC-relative addressing
absolute addressing
GOT/PLT-like mechanisms
```

theo target.

---

# 27. Position independence

Target phải khai báo:

```text id="pic"
PIC
PIE
non-PIC
```

availability.

---

# 28. TLS

Thread-local storage model:

```text id="tls"
TLS model
TLS relocation
initialization
destruction
```

phải được toolchain/compiler thống nhất.

---

# 29. Exception/unwind ABI

Toolchain phải identify:

```text id="unwind"
unwind format
personality mechanism
exception ABI
stack unwinding metadata
```

Axiom không được assume một exception mechanism trên mọi OS.

---

# 30. Axiom runtime ABI

Nếu Axiom runtime components tồn tại:

```text id="runtimeabi"
AX runtime ABI
```

phải version độc lập với compiler version.

---

# 31. Runtime optionality

Native applications không bắt buộc link toàn bộ Axiom runtime.

Compiler/linker chỉ include required components.

---

# 32. Freestanding target

AXTOOLCHAIN phải hỗ trợ:

```text id="freestanding"
freestanding
```

cho kernel/embedded/bootloader-like targets.

---

# 33. Hosted target

Hosted target:

```text id="hosted"
OS process
system services
filesystem
network
```

được mô tả bằng platform ABI.

---

# 34. Platform descriptor

```text id="platform"
platform {
    os
    version
    sdk
    ABI
    loader
    executable_format
    system_libraries
    signing
}
```

---

# 35. SDK

SDK descriptor:

```text id="sdk"
sdk {
    id
    version
    target
    headers_or_interfaces
    libraries
    tools
    metadata
}
```

Axiom không bắt buộc SDK phải chứa C headers.

---

# 36. Native platform interfaces

Axiom nên có platform interface metadata:

```text id="platformapi"
Windows API
Linux API
Apple API
Android API
```

để compiler/FFI tooling có thể hiểu ABI trực tiếp.

---

# 37. Sysroot

Sysroot:

```text id="sysroot"
headers/interfaces
libraries
startup objects
ABI metadata
```

là isolated target filesystem view.

---

# 38. Sysroot identity

```text id="sysrootid"
sysroot_id
sysroot_version
sysroot_hash
```

là build input.

---

# 39. SDK/sysroot separation

SDK có thể cung cấp development interfaces.

Sysroot là logical target environment.

Chúng không được gộp thành một identity duy nhất nếu platform cho phép nhiều SDK/sysroot combinations.

---

# 40. Startup objects

Hosted native target có thể cần:

```text id="startup"
crt-like startup
entrypoint
TLS initialization
runtime initialization
```

Axiom có thể tự cung cấp native startup components.

---

# 41. Native runtime bootstrap

Application startup:

```text id="startupflow"
OS loader
 ↓
entrypoint
 ↓
Axiom startup
 ↓
runtime initialization
 ↓
main()
```

Không được yêu cầu external language runtime.

---

# 42. Main entry

Axiom compiler/linker phải generate platform-specific entrypoint automatically.

Developer viết:

```text
fn main()
```

không cần tự viết OS entrypoint trong normal applications.

---

# 43. Static runtime

Runtime components có thể static-link:

```text id="staticrt"
application
 ├── user code
 └── required Axiom runtime
```

---

# 44. Dynamic runtime

Optional deployment:

```text id="dynrt"
application
 ↓
Axiom runtime shared library
```

nếu explicitly configured.

---

# 45. No mandatory global runtime

Axiom không nên yêu cầu:

```text
system-wide Axiom runtime installation
```

để chạy arbitrary native applications.

---

# 46. Compiler component

Toolchain compiler descriptor:

```text id="compiler"
compiler {
    id
    version
    language_version
    target_support
    capabilities
}
```

---

# 47. Compiler capabilities

Capabilities có thể include:

```text id="ccap"
native_codegen
debug
lto
pgo
sanitizer
wasm
cross_compile
```

---

# 48. Assembler component

```text id="assembler"
assembler {
    id
    version
    target
    syntax
    object_format
}
```

AXCOMPILER có thể emit machine code trực tiếp và bỏ qua assembler khi target backend hỗ trợ.

---

# 49. Direct machine emission

Axiom architecture ưu tiên:

```text id="directemit"
AXCOMPILER
 ↓
machine code
 ↓
object emitter
```

không bắt buộc:

```text source → assembly text → external assembler
```

Điều này phù hợp mục tiêu compiler native, nhỏ và nhanh.

---

# 50. Assembler fallback

Assembler vẫn tồn tại cho:

- inline assembly;
- foreign assembly;
- bootstrap;
- unusual target extensions.

---

# 51. Linker component

```text id="linker"
linker {
    id
    version
    target
    object_format
    capabilities
}
```

---

# 52. Native linker

Axiom nên có `AXLINKER` native.

External linker chỉ là compatibility backend.

---

# 53. Linker inputs

```text id="linkinputs"
objects
static libraries
dynamic libraries
resources
link options
startup objects
system libraries
```

---

# 54. Linker graph

```text id="linkgraph"
Executable
 ├── object A
 ├── object B
 ├── libCore
 ├── libGraphics
 └── platform runtime
```

AXTOOLCHAIN cung cấp platform resolution; AXLINKER thực hiện actual link.

---

# 55. System libraries

Toolchain manifest khai báo:

```text id="syslibs"
system libraries
frameworks
import libraries
runtime components
```

---

# 56. Library search

Library lookup phải deterministic:

```text id="search"
explicit path
 ↓
target sysroot
 ↓
declared SDK
```

Không tùy tiện search toàn machine.

---

# 57. Foreign toolchain

Axiom có thể consume external toolchain:

```text id="foreign"
clang
gcc
MSVC-compatible
platform linker
```

nhưng đây là interoperability mode.

Không phải core dependency.

---

# 58. Toolchain adapters

```text id="adapter"
AXTOOLCHAIN
   ↓
adapter
   ├── native Axiom
   ├── external compiler
   ├── external linker
   └── external assembler
```

---

# 59. Toolchain validation

Trước build:

```text id="validate"
target
 ↓
ABI
 ↓
compiler
 ↓
linker
 ↓
SDK
 ↓
sysroot
 ↓
compatibility check
```

---

# 60. Capability mismatch

Ví dụ:

```text id="mismatch"
compiler supports ARM64
linker supports x86_64
target = ARM64
```

→ reject trước compilation nếu có thể.

---

# 61. Toolchain fingerprint

Canonical fingerprint:

```text id="fingerprint"
compiler_hash
assembler_hash
linker_hash
target_id
abi_id
sdk_hash
sysroot_hash
runtime_hash
```

---

# 62. Reproducibility

Build artifact identity phải include relevant toolchain fingerprint.

Compiler executable thay đổi → build key thay đổi.

---

# 63. Toolchain package

AXTOOLCHAIN có thể được distributed as an `AXPACKAGE`:

```text id="tcpkg"
AXPACKAGE
   ↓
toolchain package
```

Nhưng compiler execution không cần package manager runtime.

---

# 64. Toolchain installation

Installed toolchain:

```text id="tcinstall"
toolchain manifest
 ↓
components
 ↓
target registry
```

AXREGISTRY có thể expose available toolchains.

---

# 65. Toolchain selection

AXBUILD request:

```text id="select"
target
profile
toolchain_constraint
```

→ AXTOOLCHAIN resolves compatible toolchain.

---

# 66. Explicit toolchain pinning

Project có thể pin:

```text id="pin"
toolchain_id
version
hash
```

để reproducible builds.

---

# 67. Default toolchain

Nếu không pin, AXTOOLCHAIN có thể choose configured default.

Choice phải deterministic within the same environment/configuration.

---

# 68. Toolchain discovery

Discovery sources:

```text id="discover"
project
user
machine
package
SDK
environment
```

precedence phải explicit.

---

# 69. No PATH dependency

Axiom should not rely exclusively on arbitrary `PATH` lookup.

Resolved toolchain components should have canonical identities.

---

# 70. Tool executable identity

Tool descriptor:

```text id="toolid"
path
content_hash
version
target
capabilities
```

Path alone không phải identity.

---

# 71. Tool integrity

When reproducibility/security requires:

```text id="toolintegrity"
tool hash
signature
provenance
```

must be verified.

---

# 72. Tool sandbox

Compiler/linker may run under AXSECURITY:

```text id="toolsandbox"
filesystem
network
process
device
```

capabilities explicit.

---

# 73. Compiler network

Compiler default:

```text id="compilernetwork"
network = DENY
```

unless explicitly required.

---

# 74. Tool environment

Tool environment snapshot:

```text id="env"
variables
locale
timezone
working_directory
```

must be controlled in reproducible mode.

---

# 75. Locale

Compiler diagnostics can use locale.

Artifact generation must not silently depend on locale.

---

# 76. Timezone

Build metadata must not depend on host timezone in reproducible mode.

---

# 77. Path canonicalization

Toolchain must normalize paths across:

```text
Windows
Linux
macOS
```

for deterministic build metadata.

---

# 78. Debug metadata

Toolchain identifies debug format:

```text id="debugfmt"
PDB
DWARF
dSYM-compatible
WASM debug metadata
```

---

# 79. Unwind metadata

Toolchain identifies:

```text id="unwindfmt"
Windows unwind
DWARF unwind
compact unwind
WASM unwind model
```

AXDIAGNOSTICS consumes resulting metadata.

---

# 80. Sanitizers

Optional toolchain capabilities:

```text id="sanitizers"
memory
address
thread
undefined
```

Axiom native implementation should not make sanitizer support mandatory for release builds.

---

# 81. Instrumentation

Toolchain may expose instrumentation modes for:

- profiling;
- coverage;
- diagnostics;
- PGO.

---

# 82. PGO integration

```text id="pgo"
AXBUILD
 ↓
AXTOOLCHAIN
 ↓
AXCOMPILER instrumentation
 ↓
profile
 ↓
optimized build
```

---

# 83. LTO integration

Toolchain descriptor indicates:

```text id="lto"
module_lto
thin_lto
full_lto
```

availability.

---

# 84. Link-time ABI

AXTOOLCHAIN must ensure compiler and linker agree on:

```text id="linkabi"
object format
relocations
symbol visibility
TLS
exception/unwind
calling conventions
```

---

# 85. Symbol naming

Toolchain defines external symbol encoding/mangling requirements.

Axiom internal symbol names should remain compiler-owned.

---

# 86. Name mangling

Axiom ABI:

```text id="mangle"
Axiom-specific mangling
```

Foreign ABI:

```text id="foreignmangle"
C
platform ABI
```

must be explicit.

---

# 87. Export/import

Toolchain metadata supports:

```text id="exports"
exported symbols
imported symbols
visibility
weak symbols
```

where target supports them.

---

# 88. TLS initialization

Toolchain coordinates TLS runtime startup with OS/platform ABI.

---

# 89. Thread runtime

Axiom thread/task runtime must not assume one universal OS primitive.

Toolchain exposes target capabilities to AXTHREAD/AXTASK/AXASYNC.

---

# 90. Atomics

Target descriptor must define supported atomic widths and memory-order capabilities.

Example:

```text id="atomics"
8
16
32
64
128(optional)
```

Compiler lowers to target-supported instructions/runtime fallback as appropriate.

---

# 91. CPU feature model

Toolchain supports:

```text id="cpumodel"
baseline
optional extensions
```

Example:

```text
x86-64 baseline
+SSE4.2
+AVX2
+AVX512
```

---

# 92. Multi-versioning

Optional:

```text id="multiversion"
generic
avx2
avx512
```

runtime CPU dispatch may select implementation.

Dispatch semantics must be explicit.

---

# 93. Architecture compatibility

An `AVX2` artifact must not be labeled equivalent to baseline x86-64.

Artifact metadata must preserve CPU requirements.

---

# 94. ABI compatibility matrix

Toolchain can expose:

```text id="compatmatrix"
compiler ↔ ABI
compiler ↔ linker
linker ↔ object
SDK ↔ target
sysroot ↔ target
runtime ↔ ABI
```

---

# 95. Toolchain diagnostic

Example:

```text
TOOLCHAIN_ABI_MISMATCH

target: windows-x86_64
compiler ABI: AXABI-3
runtime ABI: AXABI-2
```

Build must stop before producing invalid artifact.

---

# 96. Bootstrap stages

Axiom bootstrap:

```text id="bootstrap"
STAGE0
  ↓
STAGE1
  ↓
STAGE2
  ↓
SELF-HOSTED
```

---

# 97. Stage 0

Stage0 may be a minimal trusted bootstrap compiler.

Its purpose:

```text id="stage0purpose"
compile enough Axiom
```

to build Stage1.

---

# 98. Stage 1

Stage1:

```text id="stage1"
Axiom compiler
```

compiled by Stage0.

---

# 99. Stage 2

Stage2 compiler is compiled by Stage1.

Compare:

```text id="stagecompare"
stage1 compiler
        ↓
compile compiler source
        ↓
stage2 compiler
```

---

# 100. Bootstrap verification

Axiom should compare compiler outputs:

```text id="verify"
stage1 → stage2
stage2 → stage3
```

to establish convergence.

---

# 101. Self-hosting target

Final desired state:

```text id="selfhost"
Axiom source
 ↓
Axiom compiler
 ↓
Axiom compiler
```

without permanent dependency on external compiler technology.

---

# 102. Compiler bootstrap artifact

Bootstrap compiler may be distributed as:

```text id="bootstrapartifact"
native executable
```

with minimal dependencies.

---

# 103. Bootstrap trust

Bootstrap compiler identity/provenance should be verifiable.

AXTRUST/AXCRYPTO handles trust/signature semantics.

---

# 104. Toolchain reproducibility

Toolchain itself should be reproducibly buildable where practical:

```text id="tcrepro"
toolchain source
+
dependencies
+
bootstrap
→
same toolchain artifact
```

---

# 105. Bootstrap dependency minimization

Stage0 should be intentionally small.

But **AXTOOLCHAIN must not artificially force the entire Axiom compiler architecture into an unnecessarily tiny implementation**.

The objective is bootstrap simplicity, not permanent compiler minimalism.

---

# 106. Toolchain manifests

Canonical descriptor:

```text id="tcmanifest"
toolchain {
    identity
    version
    host
    target
    compiler
    assembler
    linker
    sdk
    sysroot
    runtime
    debug
    capabilities
    fingerprint
}
```

---

# 107. Toolchain descriptor format

Canonical binary:

```text
AXTOOLCHAIN_1
```

Text form is human/AI-editable.

---

# 108. Toolchain configuration

AXCONFIG may provide:

```text id="tcconfig"
default_toolchain
default_target
optimization
sdk_path
sysroot_path
```

but resolved build snapshot remains immutable.

---

# 109. AI metadata

Toolchain metadata should expose:

```text id="tcai"
supported_targets
supported_ABIs
available_features
compiler_capabilities
linker_capabilities
SDK requirements
known incompatibilities
```

AI tooling can choose valid build configurations.

AI does not receive authority merely from metadata.

---

# 110. IDE integration

IDE can query:

```text id="ide"
available targets
toolchains
SDKs
architectures
features
diagnostics
```

without parsing tool binaries.

---

# 111. Native APIs

Core APIs:

```text id="apis"
toolchain_open()
toolchain_close()

toolchain_list()
toolchain_find()
toolchain_validate()

target_open()
target_validate()
target_capabilities()

abi_open()
abi_validate()

sdk_open()
sdk_validate()
sdk_hash()

sysroot_open()
sysroot_validate()
sysroot_hash()

compiler_info()
assembler_info()
linker_info()

toolchain_fingerprint()

toolchain_select()
toolchain_compare()

bootstrap_stage_info()
bootstrap_verify()
```

---

# 112. Toolchain request

```text id="request"
toolchain_request {
    host
    target
    abi
    architecture
    cpu_features
    sdk_constraint
    sysroot_constraint
    compiler_constraint
    linker_constraint
    reproducibility_mode
}
```

---

# 113. Toolchain result

```text id="result"
toolchain_result {
    status
    toolchain_id
    target
    compiler
    assembler
    linker
    sdk
    sysroot
    fingerprint
    diagnostics
}
```

---

# 114. Toolchain status

```text
DISCOVERED
VALIDATING
READY
INCOMPATIBLE
UNAVAILABLE
REVOKED
```

---

# 115. Error model

Core errors:

```text
TOOLCHAIN_NOT_FOUND
TOOLCHAIN_INVALID
TOOLCHAIN_TARGET_MISMATCH
TOOLCHAIN_ABI_MISMATCH
TOOLCHAIN_COMPILER_MISMATCH
TOOLCHAIN_LINKER_MISMATCH
TOOLCHAIN_SDK_MISMATCH
TOOLCHAIN_SYSROOT_MISMATCH
TOOLCHAIN_OBJECT_FORMAT_MISMATCH
TOOLCHAIN_CPU_FEATURE_MISMATCH
TOOLCHAIN_COMPONENT_MISSING
TOOLCHAIN_INTEGRITY_FAILURE
TOOLCHAIN_REPRODUCIBILITY_FAILURE
TOOLCHAIN_BOOTSTRAP_FAILURE
```

---

# 116. Performance architecture

AXTOOLCHAIN must not become a build bottleneck.

Target operations:

```text id="perf"
toolchain lookup → O(1) / indexed
target lookup → O(1)
capability query → O(1)
fingerprint lookup → cached
```

No repeated filesystem scans during every compilation action.

---

# 117. Descriptor caching

Parsed toolchain descriptors should be immutable and cached.

---

# 118. No per-build parsing

Once validated:

```text id="cachedtc"
toolchain descriptor
 ↓
immutable in-memory object
```

can be shared across build jobs.

---

# 119. Parallel builds

Multiple AXBUILD jobs may share read-only toolchain descriptors.

No global mutable toolchain state.

---

# 120. Toolchain isolation

Each build receives immutable:

```text id="isolation"
toolchain_snapshot
```

preventing mid-build configuration mutation.

---

# 121. Toolchain switching

Switching target:

```text id="switch"
windows-x64
 ↓
linux-arm64
```

creates a new build/toolchain snapshot.

Existing build snapshot is unchanged.

---

# 122. Toolchain installation layout

Suggested logical structure:

```text
toolchains/
  <toolchain-id>/
      manifest.axtoolchain
      compiler/
      assembler/
      linker/
      sdk/
      sysroot/
      runtime/
      debug/
```

Physical layout is implementation-defined.

---

# 123. System integration

AXTOOLCHAIN can discover platform-provided SDKs but must record exact resolved identity.

---

# 124. Windows

Windows toolchain must eventually support:

```text
PE64
COFF
x86_64
ARM64
PDB/unwind metadata
Windows ABI
```

---

# 125. Linux

Linux baseline:

```text
ELF
x86_64
AArch64
DWARF
platform ABI
```

---

# 126. macOS

macOS baseline:

```text
Mach-O
x86_64
ARM64
Apple ABI
debug/unwind metadata
```

---

# 127. iOS

iOS toolchain descriptor includes:

```text
architecture
SDK version
deployment target
ABI
signing requirements
platform restrictions
```

---

# 128. Android

Android:

```text
AArch64
x86_64
platform API level
native loader ABI
```

with target-specific SDK identity.

---

# 129. WASM

WASM descriptor:

```text id="wasmtc"
wasm32
module format
import/export ABI
memory model
host interface
```

---

# 130. Embedded

Toolchain must support future bare-metal:

```text id="embedded"
no OS
custom linker layout
custom startup
fixed memory map
```

without redesigning the core model.

---

# 131. Linker script equivalent

Axiom should eventually use a typed linker layout description:

```text id="layout"
sections
regions
alignment
entrypoint
permissions
```

rather than depending permanently on external linker-script syntax.

---

# 132. Memory regions

Embedded target:

```text id="memregions"
FLASH
RAM
DEVICE
RESERVED
```

can be represented in toolchain target metadata.

---

# 133. Section model

Native toolchain descriptor can declare:

```text id="sections"
.text
.rodata
.data
.bss
.tls
.debug
```

with target-specific mappings.

---

# 134. Section permissions

Toolchain must preserve:

```text
READ
WRITE
EXECUTE
```

and platform security restrictions.

---

# 135. W^X

Where platform supports it, toolchain should support:

```text id="wxx"
write xor execute
```

for code/data segment policies.

---

# 136. Code signing

Toolchain may expose platform signing capability:

```text id="signing"
required
optional
unsupported
```

Actual signing policy remains outside compiler semantics.

---

# 137. Signing integration

Signing may consume AXCRYPTO and AXSECURITY services.

Secrets must never become ordinary build inputs.

---

# 138. Reproducible signing

Build identity should be separable from deployment signing where possible:

```text id="reprosign"
reproducible binary
       ↓
deployment signature
```

This allows binary reproducibility without embedding nondeterministic signing metadata prematurely.

---

# 139. Toolchain provenance

Every toolchain should expose:

```text id="prov"
source
version
build_id
dependencies
target
publisher
signature
```

when available.

---

# 140. Formal invariants

```text id="tcinv"
TOOLCHAIN-INV-01
Toolchain identity phải deterministic.

TOOLCHAIN-INV-02
Host và target phải được phân biệt.

TOOLCHAIN-INV-03
Target identity phải bao gồm OS, architecture và ABI-relevant information.

TOOLCHAIN-INV-04
ABI phải là versioned explicit contract.

TOOLCHAIN-INV-05
Calling convention phải được xác định rõ.

TOOLCHAIN-INV-06
Struct/aggregate ABI phải deterministic.

TOOLCHAIN-INV-07
Alignment semantics phải explicit.

TOOLCHAIN-INV-08
Object format phải phù hợp target.

TOOLCHAIN-INV-09
Compiler và linker phải agree về object/ABI contract.

TOOLCHAIN-INV-10
SDK identity phải là build input.

TOOLCHAIN-INV-11
Sysroot identity phải là build input.

TOOLCHAIN-INV-12
Compiler identity phải là build input.

TOOLCHAIN-INV-13
Linker identity phải là build input.

TOOLCHAIN-INV-14
Assembler identity phải là build input khi assembler được sử dụng.

TOOLCHAIN-INV-15
CPU feature requirements phải được biểu diễn trong target/artifact metadata.

TOOLCHAIN-INV-16
Target-incompatible toolchain không được selected.

TOOLCHAIN-INV-17
ABI-incompatible components không được silently combined.

TOOLCHAIN-INV-18
Toolchain component lookup phải deterministic.

TOOLCHAIN-INV-19
Toolchain descriptors phải có canonical representation.

TOOLCHAIN-INV-20
Toolchain fingerprint phải cover all relevant build components.

TOOLCHAIN-INV-21
Filesystem path không phải identity duy nhất của tool.

TOOLCHAIN-INV-22
Reproducible build không được phụ thuộc host timestamp.

TOOLCHAIN-INV-23
Reproducible build không được phụ thuộc host timezone.

TOOLCHAIN-INV-24
Reproducible build không được phụ thuộc undeclared environment.

TOOLCHAIN-INV-25
Direct machine-code emission phải được hỗ trợ khi compiler backend cung cấp capability.

TOOLCHAIN-INV-26
External assembler/compiler/linker chỉ là interoperability backend, không phải mandatory Axiom dependency.

TOOLCHAIN-INV-27
Native Axiom linker phải có architecture/API path độc lập.

TOOLCHAIN-INV-28
Native Axiom compiler phải có architecture/API path độc lập.

TOOLCHAIN-INV-29
Toolchain runtime components phải optional theo artifact requirements.

TOOLCHAIN-INV-30
Executable không được mặc định phụ thuộc system-wide Axiom runtime.

TOOLCHAIN-INV-31
Freestanding targets phải được biểu diễn mà không giả định hosted OS.

TOOLCHAIN-INV-32
Cross compilation phải tách host và target.

TOOLCHAIN-INV-33
Multiple target builds phải có independent target identities.

TOOLCHAIN-INV-34
Toolchain snapshots phải immutable trong một build transaction.

TOOLCHAIN-INV-35
Build sandbox capabilities phải explicit.

TOOLCHAIN-INV-36
Toolchain secrets không được trở thành ordinary reproducibility inputs.

TOOLCHAIN-INV-37
Platform signing không được làm thay đổi compiler semantic model.

TOOLCHAIN-INV-38
Bootstrap stage phải có thể xác minh provenance/identity khi policy yêu cầu.

TOOLCHAIN-INV-39
AI metadata chỉ mô tả capability và compatibility, không grant authority.

TOOLCHAIN-INV-40
AXTOOLCHAIN mô tả và cung cấp native toolchain; compilation, assembly, linking và build orchestration semantics thuộc subsystem tương ứng.
```

---

# 141. Definition of Done

`AXTOOLCHAIN 5.0` được freeze khi có:

- host/target model;
- target identity;
- architecture model;
- endianness;
- pointer width;
- data model;
- ABI descriptor;
- calling conventions;
- struct ABI;
- SIMD ABI;
- floating-point ABI;
- alignment;
- atomics;
- TLS;
- exception/unwind model;
- object format;
- relocation model;
- PIC/PIE;
- PE64;
- ELF;
- Mach-O;
- WASM;
- compiler descriptor;
- assembler descriptor;
- linker descriptor;
- direct machine-code emission;
- SDK model;
- sysroot model;
- startup objects;
- Axiom runtime ABI;
- freestanding target;
- hosted target;
- platform descriptor;
- system library model;
- native platform interface metadata;
- foreign toolchain adapters;
- toolchain validation;
- toolchain capability discovery;
- toolchain fingerprint;
- reproducibility identity;
- CPU feature model;
- multi-versioning model;
- LTO;
- PGO;
- debug format;
- unwind format;
- sanitizer capability;
- signing capability;
- bootstrap stages;
- self-hosting path;
- toolchain package model;
- toolchain installation;
- toolchain selection;
- cross compilation;
- Windows;
- Linux;
- macOS;
- iOS;
- Android;
- WASM;
- embedded extensibility;
- linker layout model;
- AI metadata;
- IDE integration;
- native API;
- `AXTOOLCHAIN_ABI_1`;
- 40 invariants.

**AXTOOLCHAIN 5.0 → FROZEN.**

---

# BOOTSTRAP-770 — AXCOMPILER

**Native Axiom Compiler Frontend, Semantic Engine, Type System Integration, Generic/Closure/Pattern Lowering, IR Generation, Optimization Pipeline & Machine-Code Compilation Runtime 5.0**

Đây là bước rất quan trọng: các lớp vừa hoàn thiện đã tạo thành chuỗi:

```text
AXREGISTRY
      ↓
AXPACKAGE
      ↓
AXBUILD
      ↓
AXTOOLCHAIN
      ↓
AXCOMPILER
      ↓
machine code / object
      ↓
AXLINKER
      ↓
PE64 / ELF / Mach-O / WASM
```

`AXCOMPILER` sẽ là nơi biến **Axiom language semantics** thành compiler architecture thực sự, bao gồm frontend → semantic analysis → typed IR → optimization → native code generation, đồng thời phải giữ đúng các quyết định cốt lõi trước đây của Axiom về **hiệu năng native, memory model explicit, không bắt buộc GC/borrow checker, struct-oriented OOP, UTF-8 và khả năng self-hosting**.