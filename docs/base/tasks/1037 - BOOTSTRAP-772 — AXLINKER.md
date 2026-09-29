# BOOTSTRAP-772 — AXLINKER

**Title:** Native Static/Dynamic Linker, Symbol Resolution, Relocation, Section Layout, Library Linking, Executable Construction, PE64/ELF/Mach-O/WASM Final Artifact & Native Binary Runtime 5.0  
**Namespace:** `AXLINKER`  
**Phase:** Axiom Native Toolchain / Final Artifact Construction  
**Status:** **ARCHITECTURAL BASELINE — FROZEN TARGET 5.0**

---

# 1. Mục tiêu

`AXLINKER` là linker native chính thức của Axiom.

Nó nhận:

```text
object files
static libraries
dynamic libraries
runtime objects
linker metadata
target ABI
SDK/sysroot
```

và tạo:

```text
PE64
ELF
Mach-O
WASM
static library
dynamic library
```

Pipeline:

```text
AXCOMPILER
    │
    ▼
AXASSEMBLER
    │
    ▼
Object Files
    │
    ├───────────────┐
    ▼               ▼
Static Library   Dynamic Library
    │               │
    └───────┬───────┘
            ▼
        AXLINKER
            │
            ├── symbol resolution
            ├── archive extraction
            ├── relocation
            ├── section layout
            ├── address assignment
            ├── import/export
            ├── TLS
            ├── startup
            ├── debug/unwind
            └── final validation
            │
            ▼
       Native Artifact
```

---

# 2. Vai trò

AXLINKER chịu trách nhiệm **global binary composition**.

AXCOMPILER biết:

```text
function F
```

AXASSEMBLER biết:

```text
call F
```

nhưng AXLINKER quyết định:

```text
F nằm ở address nào?
call F relocation thành giá trị nào?
object nào được đưa vào binary?
section nào nằm ở đâu?
external symbol nào được import?
```

---

# 3. Boundary

AXLINKER sở hữu:

- object loading;
- archive loading;
- symbol table;
- symbol resolution;
- duplicate resolution;
- weak/strong semantics;
- section merging;
- section placement;
- address assignment;
- relocation application;
- import/export generation;
- dynamic linking metadata;
- static library creation;
- dynamic library creation;
- executable construction;
- entry point;
- TLS layout;
- platform binary headers;
- binary validation.

Không sở hữu:

```text
AXCOMPILER   → source semantics
AXASSEMBLER  → instruction encoding
AXTOOLCHAIN  → target identity
AXBUILD      → build graph
AXPACKAGE    → package distribution
AXPROCESS    → process execution
AXSECURITY   → runtime authorization
```

---

# 4. Native-first principle

Canonical path:

```text
Axiom source
 ↓
AXCOMPILER
 ↓
AXASSEMBLER
 ↓
AXLINKER
 ↓
native binary
```

Không yêu cầu:

```text
Axiom
 ↓
C source
 ↓
C compiler
 ↓
external linker
```

---

# 5. Supported output formats

Baseline:

| Target | Format |
|---|---|
| Windows x86-64 | PE64/COFF |
| Linux x86-64 | ELF64 |
| Linux AArch64 | ELF64 |
| macOS x86-64 | Mach-O |
| macOS AArch64 | Mach-O |
| iOS AArch64 | Mach-O |
| Android AArch64 | ELF64 |
| WASM32 | WebAssembly |

---

# 6. Link modes

```text
STATIC_EXECUTABLE
DYNAMIC_EXECUTABLE
STATIC_LIBRARY
DYNAMIC_LIBRARY
WASM_MODULE
WASM_COMPONENT
```

Target availability phụ thuộc AXTOOLCHAIN.

---

# 7. Link request

```text
link_request {
    inputs[]
    target
    abi
    output_kind
    entry_symbol
    library_paths[]
    sysroot
    sdk
    link_options
    feature_set
    debug_mode
    optimization_mode
    reproducibility_mode
    security_profile
}
```

---

# 8. Link result

```text
link_result {
    status
    artifact
    symbols
    sections
    imports
    exports
    relocations
    diagnostics
    build_id
    provenance
}
```

---

# 9. Object model

AXLINKER đọc object:

```text
object {
    format
    architecture
    abi
    sections[]
    symbols[]
    relocations[]
    metadata[]
}
```

---

# 10. Object validation

Trước khi link:

```text
validate format
validate architecture
validate ABI
validate sections
validate symbols
validate relocation types
validate metadata
```

Object không hợp lệ phải bị reject.

---

# 11. Target consistency

Không link trực tiếp object:

```text
x86_64
```

vào target:

```text
AArch64
```

trừ khi object là foreign/interoperability artifact được AXTOOLCHAIN explicitly hỗ trợ.

---

# 12. ABI consistency

Objects phải compatible về:

- calling convention;
- data layout;
- pointer size;
- alignment;
- exception/unwind ABI;
- TLS ABI;
- object format.

---

# 13. Symbol table

AXLINKER tạo global symbol table:

```text
SymbolName
    ↓
SymbolDefinition
```

---

# 14. Symbol identity

Symbol được phân biệt bởi:

```text
name
binding
visibility
namespace/link scope
ABI context
```

---

# 15. Symbol states

```text
UNDEFINED
DEFINED
COMMON
WEAK_DEFINED
WEAK_UNDEFINED
ABSOLUTE
SECTION_RELATIVE
IMPORT
EXPORT
```

tùy format.

---

# 16. Strong symbol

Nếu có hai strong definitions cùng symbol:

```text
F
F
```

→ link error.

Không silently chọn một.

---

# 17. Weak symbol

Weak symbol semantics follow target object ABI.

Nếu strong definition tồn tại, weak reference có thể resolve tới strong definition.

---

# 18. Undefined symbol

Sau resolution:

```text
undefined symbol
```

là error nếu output mode không cho phép unresolved dynamic symbol.

---

# 19. Dynamic unresolved symbol

Shared library có thể giữ unresolved symbols nếu target ABI cho phép và dependency metadata declares them.

Executable final policy phải explicit.

---

# 20. Symbol visibility

AXLINKER hỗ trợ:

```text
local
hidden
protected
public
exported
imported
```

theo target.

---

# 21. Symbol alias

Multiple symbol names có thể map tới cùng address khi ABI yêu cầu.

---

# 22. Symbol versioning

ELF-like targets có thể hỗ trợ versioned symbols.

Internal linker model:

```text
symbol
+
version
```

---

# 23. Symbol mangling

Axiom public symbols dùng mangled identity từ compiler ABI.

AXLINKER không tự đổi mangling semantics.

---

# 24. Archive

Static library:

```text
archive {
    members[]
}
```

mỗi member là object.

---

# 25. Static archive extraction

Classic model:

```text
undefined symbol
 ↓
search archive
 ↓
extract member defining symbol
```

---

# 26. Lazy archive extraction

Không đưa toàn bộ static library vào executable nếu không cần.

---

# 27. Group/cyclic archives

AXLINKER phải hỗ trợ explicit group resolution nếu dependency graph có cycle.

---

# 28. Whole-archive

Explicit option:

```text
--whole-archive
```

có thể force extraction.

---

# 29. Dead object elimination

Nếu enabled:

```text
unused object
```

không được đưa vào final artifact.

---

# 30. Section model

Object sections:

```text
.text
.rodata
.data
.bss
.tdata
.tbss
.debug*
.unwind*
```

được merged theo section class.

---

# 31. Section class

Internal:

```text
CODE
READONLY_DATA
READWRITE_DATA
ZERO_FILL
TLS_DATA
TLS_ZERO
DEBUG
UNWIND
METADATA
```

---

# 32. Section flags

```text
READ
WRITE
EXECUTE
ALLOC
TLS
DEBUG
DISCARDABLE
```

---

# 33. W^X

Final binary phải respect:

```text
W xor X
```

cho executable memory segments khi target policy yêu cầu.

---

# 34. Section merging

AXLINKER merge compatible input sections.

Ví dụ:

```text
object A .text
object B .text
object C .text
```

→ final code region.

---

# 35. Section ordering

Default deterministic ordering:

```text
startup
hot code
normal code
cold code
readonly data
writable data
zero-fill
TLS
metadata
```

Exact target layout có thể differ.

---

# 36. Custom section

Axiom có thể allow explicit:

```text
@section("name")
```

nhưng linker security/target rules vẫn áp dụng.

---

# 37. Section alignment

Final section alignment:

```text
max(input alignment, target minimum)
```

hoặc target-specific ABI rule.

---

# 38. Address assignment

Linker tính:

```text
virtual_address
file_offset
memory_size
file_size
```

cho final sections/segments.

---

# 39. Virtual address layout

Target-specific:

```text
PE64
ELF
Mach-O
```

có layout requirements riêng.

---

# 40. Base address

Executable/shared library có:

```text
preferred_base
```

khi format hỗ trợ.

---

# 41. ASLR

Linker phải tạo binary compatible với ASLR khi target/toolchain configuration yêu cầu.

---

# 42. PIE

Executable có thể build:

```text
PIE
non-PIE
```

theo target configuration.

---

# 43. Shared library

Dynamic library output phải expose:

```text
exports
relocations
imports
ABI metadata
```

theo target format.

---

# 44. Import model

Generic model:

```text
import {
    library
    symbol
    version
}
```

---

# 45. Export model

```text
export {
    symbol
    visibility
    ordinal?
}
```

---

# 46. Windows PE64

AXLINKER phải tạo:

```text
DOS header
PE signature
COFF header
optional header
section table
imports
exports
relocations
TLS
debug metadata
```

khi tương ứng.

---

# 47. PE entry point

Entry point address được link từ:

```text
entry_symbol
```

hoặc target default startup symbol.

---

# 48. PE import table

Imports phải generate deterministic:

```text
DLL
symbol
IAT
metadata
```

---

# 49. PE export table

Exported symbols được canonical-sort hoặc theo explicit ABI policy.

---

# 50. PE base relocation

Nếu dynamic relocation enabled, linker emits required base relocation records.

---

# 51. PE subsystem

Target configuration có thể select:

```text
CONSOLE
WINDOWS
EFI
```

nếu supported.

---

# 52. ELF

ELF linker tạo:

```text
ELF header
program headers
section headers
segments
dynamic metadata
symbol tables
relocations
TLS
notes
```

khi cần.

---

# 53. ELF program headers

Runtime-relevant memory layout nằm ở program headers.

Linker phải ensure section/segment mapping valid.

---

# 54. ELF dynamic section

Dynamic executable/shared library có thể require:

```text
DT_NEEDED
DT_SYMTAB
DT_STRTAB
DT_RELA
DT_PLTGOT
```

tùy target.

---

# 55. GOT/PLT

AXLINKER phải generate target-specific GOT/PLT-like structures khi required.

---

# 56. ELF RELRO

Linker có thể produce layout compatible with RELRO policies.

---

# 57. ELF PIE

PIE executable được link theo appropriate position-independent relocation model.

---

# 58. Mach-O

AXLINKER phải support:

```text
Mach header
load commands
segments
sections
symbol tables
dyld metadata
exports
imports
code signatures metadata hooks
TLS/thread data
```

theo platform.

---

# 59. macOS

Target:

```text
x86_64-apple-macos
arm64-apple-macos
```

---

# 60. iOS

iOS artifact generation phải respect:

```text
Mach-O
platform metadata
minimum OS version
architecture
signing metadata boundary
```

Code signing final cryptographic operation thuộc platform/security tooling boundary; linker chỉ tạo required structures/slots.

---

# 61. Android

Android AArch64 executable/shared library:

```text
ELF64
```

với platform-specific ABI metadata.

---

# 62. WASM

WASM linker xử lý:

```text
imports
exports
functions
tables
memories
globals
data
elements
custom sections
```

---

# 63. WASM module linking

WASM không có traditional native relocation after final module creation in the same way as ELF.

AXLINKER resolves all supported module-level symbols before final emission.

---

# 64. WASM imports

Unresolved external functions/data trở thành explicit WASM imports nếu output mode allows.

---

# 65. WASM exports

Explicit export table:

```text
main
functions
memory
globals
```

theo project configuration.

---

# 66. Entry point

Generic:

```text
entry_symbol
```

Target adapter translates into platform-specific startup contract.

---

# 67. Axiom startup

Minimal executable may have:

```text
OS entry
 ↓
Axiom startup
 ↓
main
```

Startup code should be as small as possible.

---

# 68. Runtime startup

AXLINKER does not automatically link complete Axiom runtime.

Only required runtime objects are included.

---

# 69. Runtime component selection

Build metadata can request:

```text
startup
allocator
thread runtime
async runtime
panic handler
TLS runtime
```

only when used.

---

# 70. Dead runtime stripping

Unused runtime components should be eliminated.

---

# 71. Static linking

Static linking:

```text
application
+
required objects
+
required libraries
```

→ standalone artifact.

---

# 72. Dynamic linking

Dynamic linking keeps external library dependencies:

```text
application
 ├── imported library A
 └── imported library B
```

---

# 73. Self-contained mode

Axiom build can request self-contained deployment where legally/platform-wise possible.

---

# 74. System libraries

AXLINKER resolves system libraries only through explicit AXTOOLCHAIN sysroot/SDK.

Không arbitrary machine-wide search.

---

# 75. Library search order

Search order must be deterministic.

---

# 76. Library ambiguity

Nếu hai libraries provide incompatible definitions:

```text
```

linker phải produce deterministic diagnostic rather than silently selecting arbitrary path.

---

# 77. RPATH/RUNPATH

ELF-like targets may support explicit runtime search metadata.

---

# 78. Windows DLL search metadata

PE import names are emitted according to target policy; linker does not invent runtime DLL discovery rules.

---

# 79. Framework linking

Mach-O/iOS/macOS framework dependencies được represented explicitly.

---

# 80. Static library creation

```text
AXLINKER
 ↓
archive members
 ↓
.a / .lib
```

Archive output deterministic.

---

# 81. Dynamic library creation

```text
AXLINKER
 ↓
shared object
```

Target-specific dynamic metadata.

---

# 82. Symbol garbage collection

Optional:

```text
--gc-sections
```

or equivalent.

Unused sections removed when reachability proves they are unnecessary.

---

# 83. Root symbols

Reachability starts from:

```text
entry point
exports
explicit retain symbols
runtime roots
```

---

# 84. Constructor roots

Platform initialization functions may be roots.

---

# 85. Destructor roots

Shutdown/finalization functions may be roots.

---

# 86. COMDAT/identical sections

Linker can fold equivalent sections if object format and semantics permit.

---

# 87. Identical code folding

ICF must preserve address-sensitive semantics.

If function address identity is observable, folding requires language/ABI permission.

---

# 88. Function address identity

Axiom compiler must tell linker whether:

```text
&foo == &bar
```

may be assumed distinct.

Linker cannot blindly merge.

---

# 89. Section garbage collection and metadata

Removing code must also remove associated:

- relocations;
- debug records;
- unwind metadata;
- compiler metadata.

---

# 90. Relocation engine

Input:

```text
relocation {
    offset
    type
    symbol
    addend
}
```

→ final patched bytes.

---

# 91. Relocation formula

Each relocation kind defines:

```text
value = f(symbol_address, place, addend, image_base, ...)
```

explicitly.

---

# 92. Relocation overflow

Must reject if value cannot fit target relocation field.

---

# 93. REL vs RELA

ELF backend supports both styles where target ABI requires.

---

# 94. PE relocations

PE relocation table generated when required.

---

# 95. Mach-O relocations

Mach-O relocation forms translated from internal relocation model.

---

# 96. Relocation relaxation

Linker may optimize:

```text
long sequence
 ↓
short sequence
```

only when architecture/relocation model permits.

---

# 97. Link-time branch relaxation

Useful when final addresses become known.

---

# 98. Link-time optimization

AXLINKER may consume LTO metadata but actual high-level optimization belongs AXCOMPILER.

---

# 99. Thin/LTO metadata

Object may contain compiler IR references.

AXLINKER coordinates but does not redefine Axiom semantics.

---

# 100. Incremental linking

AXLINKER should support optional incremental link state:

```text
previous layout
+
changed objects
```

for development builds.

---

# 101. Incremental link correctness

Any changed symbol/layout dependency must invalidate affected regions.

---

# 102. Deterministic linking

Same:

```text
objects
libraries
target
toolchain
options
```

must produce semantically equivalent and reproducible output.

---

# 103. Deterministic symbol ordering

Canonical ordering:

```text
symbol name
binding
section
offset
```

or format-specific canonical order.

---

# 104. Deterministic archive

Static archive member order must be deterministic.

---

# 105. Build ID

Final binary may contain deterministic build ID:

```text
hash(inputs + toolchain + link configuration)
```

---

# 106. Reproducible timestamps

Executable timestamps must be:

```text
normalized
```

or derived deterministically from source revision/build metadata.

---

# 107. Path normalization

Absolute build-machine paths must not leak into reproducible artifacts unless explicitly requested.

---

# 108. Debug path remapping

AXLINKER accepts normalized source paths from compiler/debug metadata.

---

# 109. Debug symbols

Output modes:

```text
embedded
external
stripped
```

---

# 110. External debug artifact

Linker can create:

```text
program
program.debug
```

with build-ID association.

---

# 111. Unwind metadata

Final binary must preserve required unwind tables.

---

# 112. Windows unwind

PE64 x86-64 requires target-specific unwind metadata for supported stack frames.

---

# 113. DWARF

ELF/Mach-O builds may include DWARF debug information.

---

# 114. Symbol stripping

Strip removes non-required symbols/debug metadata without modifying executable semantics.

---

# 115. Binary validation

Before final artifact:

```text
validate headers
validate segments
validate entry point
validate relocations
validate imports
validate exports
validate alignment
validate permissions
validate symbols
validate ABI
```

---

# 116. Address validation

Every relocation result must point to a valid address/range.

---

# 117. Section overlap

Final memory sections must not overlap illegally.

---

# 118. File overlap

File ranges must not overlap unless format explicitly permits it.

---

# 119. Alignment validation

Virtual/file offsets must satisfy format constraints.

---

# 120. Entry validation

Entry point must:

- exist;
- be executable;
- belong to correct image;
- satisfy target ABI requirements.

---

# 121. Import validation

Imports must reference valid symbols/libraries.

---

# 122. Export validation

Exports must point to valid symbol addresses.

---

# 123. TLS validation

TLS sections must obey target ABI layout.

---

# 124. Memory permissions

Final segment permissions must reflect:

```text
code → RX
readonly → R
data → RW
```

subject to target requirements.

---

# 125. No accidental RWX

Linker should reject accidental RWX segment in hardened/reproducible security profiles unless explicit.

---

# 126. Large binary support

Use 64-bit offsets/sizes internally even for formats with smaller field constraints.

---

# 127. Overflow safety

All size/address arithmetic checked.

---

# 128. Linker memory architecture

Use:

```text
arena
compact vectors
symbol hash tables
section arrays
```

rather than pointer-heavy graph structures.

---

# 129. Symbol lookup

Hot path:

```text
hash(symbol)
 ↓
symbol table
```

must be efficient.

---

# 130. Symbol table sharding

Parallel object ingestion can use sharded symbol maps before deterministic merge.

---

# 131. Parallel relocation

Independent relocation ranges may be processed parallel.

Final output ordering remains deterministic.

---

# 132. Parallel section layout

Planning can be parallel; final layout is serialized/canonical.

---

# 133. Link memory optimization

Large projects should not require loading every raw object byte into duplicated buffers.

Memory-map/read slices where safe.

---

# 134. Streaming

AXLINKER should support streaming object/archive reads.

---

# 135. Object cache

AXBUILD can cache validated object metadata.

AXLINKER may consume cached parsed object representation.

---

# 136. Link cache

A link fingerprint can identify reusable final artifact.

---

# 137. Link cache key

```text id="8m6jv5"
objects hashes
libraries hashes
target
ABI
SDK/sysroot
link options
linker version
security profile
debug mode
```

---

# 138. Cache integrity

Cached artifact must be content-hash verified before use.

---

# 139. Security

AXLINKER must not execute object code or arbitrary build scripts while linking.

---

# 140. Malicious object

Malformed/untrusted object must be treated as data.

---

# 141. Archive bomb

Archive expansion must respect resource limits.

---

# 142. Path traversal

Archive member names cannot escape designated extraction area if temporary extraction is required.

Prefer direct indexed archive reading.

---

# 143. External linker

External linker adapter may exist for:

- legacy targets;
- interoperability;
- bootstrap;
- unsupported platform feature.

But it is not a permanent Axiom dependency.

---

# 144. Bootstrap

Initial stage may use external system linker.

Final self-hosted Axiom toolchain must support native AXLINKER.

---

# 145. Stage0

```text
Stage0
 ↓
build AXASSEMBLER
 ↓
build minimal AXLINKER
```

---

# 146. Stage1

```text
AXCOMPILER
+
AXASSEMBLER
+
AXLINKER
```

đủ để compile native Axiom programs.

---

# 147. Stage2

Axiom toolchain self-builds itself:

```text
Axiom source
 ↓
Axiom compiler
 ↓
Axiom assembler
 ↓
Axiom linker
 ↓
Axiom toolchain
```

---

# 148. Bootstrap convergence

```text
Stage2 compiler
compile source
→ Stage3

Stage3 compile same source
→ Stage4
```

Output comparison verifies bootstrap stability.

---

# 149. Linker ABI

Native API:

```text
AXLINKER_ABI_1
```

---

# 150. Linker context

```text
linker_context {
    target
    abi
    sysroot
    sdk
    options
}
```

---

# 151. Input API

```text
linker_add_object()
linker_add_archive()
linker_add_shared_library()
linker_add_runtime()
```

---

# 152. Symbol API

```text
linker_define_symbol()
linker_lookup_symbol()
linker_export_symbol()
linker_import_symbol()
```

---

# 153. Layout API

```text
linker_plan_layout()
linker_assign_addresses()
linker_query_section()
```

---

# 154. Relocation API

```text
linker_apply_relocations()
linker_validate_relocations()
```

---

# 155. Output API

```text
linker_emit_executable()
linker_emit_static_library()
linker_emit_dynamic_library()
linker_emit_wasm()
```

---

# 156. Inspection API

```text
linker_list_symbols()
linker_list_sections()
linker_list_imports()
linker_list_exports()
linker_list_relocations()
```

---

# 157. Validation API

```text
linker_validate_object()
linker_validate_layout()
linker_validate_binary()
```

---

# 158. Diagnostics

```text
LINK_UNDEFINED_SYMBOL
LINK_DUPLICATE_SYMBOL
LINK_INCOMPATIBLE_OBJECT
LINK_ARCHITECTURE_MISMATCH
LINK_ABI_MISMATCH
LINK_RELOCATION_OVERFLOW
LINK_INVALID_RELOCATION
LINK_SECTION_OVERLAP
LINK_INVALID_ENTRY
LINK_IMPORT_ERROR
LINK_EXPORT_ERROR
LINK_TLS_ERROR
LINK_FORMAT_ERROR
LINK_SECURITY_ERROR
LINK_RESOURCE_LIMIT
LINK_INTERNAL_ERROR
```

---

# 159. Explain link

Developer command:

```text
axiom link --why-symbol foo
```

có thể trả:

```text
foo
 ← object_a.axo
 ← library_b.axlib
```

---

# 160. Explain inclusion

```text
axiom link --why-included module.axo
```

giúp tìm lý do object được kéo vào executable.

---

# 161. Map file

Linker có thể emit:

```text
program.map
```

chứa:

- symbols;
- addresses;
- sections;
- sizes;
- libraries;
- discarded sections.

---

# 162. Size analysis

```text
axiom link --size-report
```

có thể report:

```text
code
readonly
data
TLS
debug
imports
```

---

# 163. Binary diff

Tooling có thể compare two linked artifacts theo:

```text
section
symbol
relocation
```

---

# 164. Hot/cold layout

Compiler profile metadata có thể tell linker:

```text
hot
warm
cold
```

để code layout tối ưu cache.

---

# 165. Function ordering

PGO order có thể influence final function placement.

---

# 166. Identical data folding

Read-only constants có thể deduplicate khi semantics cho phép.

---

# 167. String pooling

Linker có thể merge identical immutable strings.

Không merge nếu address identity observable.

---

# 168. Address-sensitive data

Compiler marks data whose address must remain unique.

---

# 169. COMDAT-like semantics

Generic instantiations and template-like entities có thể use linker folding metadata.

---

# 170. Generic code emission

AXCOMPILER generates specializations.

AXLINKER merges/deduplicates equivalent emitted entities where ABI permits.

---

# 171. LTO boundary

When LTO enabled:

```text
AXCOMPILER IR metadata
        ↓
AXLINKER orchestration
        ↓
AXCOMPILER optimizer/codegen
```

Linker does not become semantic compiler.

---

# 172. Foreign object compatibility

Axiom may link:

```text
C
C++
Rust
assembly
```

objects where ABI-compatible.

Language semantics are not imported into Axiom.

---

# 173. C ABI

Minimum foreign linking target:

```text
cdecl/system ABI
```

depending platform.

---

# 174. Foreign library identity

AXBUILD/AXPACKAGE provide dependency identity.

AXLINKER only consumes resolved artifact.

---

# 175. Library version

Linker may record library version/build identity in provenance but does not perform package version resolution.

---

# 176. SDK identity

Final artifact records SDK identity when configured.

---

# 177. Sysroot identity

Link result fingerprint includes sysroot identity.

---

# 178. Reproducible linking

Output must not depend on:

```text
machine hostname
absolute source path
wall clock
process ID
thread scheduling
```

unless explicitly requested.

---

# 179. Build provenance

Final artifact can contain:

```text
compiler
assembler
linker
target
ABI
source revision
dependency hashes
build profile
```

---

# 180. Provenance stripping

Release policy may strip nonessential provenance.

---

# 181. Signature boundary

AXLINKER can reserve/emit signature-related structures, but cryptographic signing belongs AXCRYPTO/AXTRUST/platform signing pipeline.

---

# 182. Security metadata

Linker can encode:

- NX;
- ASLR compatibility;
- RELRO;
- stack protection metadata;
- control-flow metadata where target supports it.

---

# 183. Security policy

AXLINKER does not decide security policy.

AXSECURITY/AXTOOLCHAIN/build profile provides requirements.

---

# 184. Capability metadata

Executable may declare required runtime capabilities.

Linker preserves metadata but does not grant them.

---

# 185. Native application metadata

Final executable may contain:

```text
application identity
required OS version
architecture
ABI
capability declarations
resource descriptors
```

---

# 186. GUI application

Windows GUI application can link against:

```text
AXWINDOW
AXDISPLAY
AXINPUT
```

without requiring console subsystem.

---

# 187. Console application

Console executable links minimal startup.

---

# 188. Static binary

Axiom can generate a highly self-contained binary:

```text
application
+
only required runtime
+
only required libraries
```

subject to platform licensing/runtime constraints.

---

# 189. Binary compactness

Linker should support:

```text
dead stripping
section GC
ICF
constant merging
symbol stripping
relocation optimization
```

when safe.

---

# 190. Link-time code compression

Not mandatory.

Executable compression/packing should remain outside linker core.

---

# 191. No hidden packer

AXLINKER never silently packs executable.

---

# 192. WASM size optimization

WASM linker can remove:

- unused functions;
- unused data;
- unused exports;
- unnecessary metadata.

---

# 193. WASM custom sections

Custom metadata can be preserved or stripped according to profile.

---

# 194. Linker server

Persistent linker service:

```text
AXLINKER SERVER
```

may cache:

- parsed objects;
- symbol tables;
- layout plans;
- relocation metadata.

---

# 195. Linker server isolation

Different projects must not share mutable symbol state.

---

# 196. Deterministic server

Server state cannot change output semantics.

---

# 197. Link cancellation

Long link can be cancelled.

Partial artifact must never be published as valid output.

---

# 198. Atomic output

```text
staging
 ↓
validate
 ↓
fsync/commit
 ↓
final artifact
```

integrates with AXBUILD/AXSTORAGE.

---

# 199. Failed link

Failed link must preserve previous valid output.

---

# 200. Crash recovery

AXBUILD owns transaction recovery; AXLINKER provides enough intermediate state metadata.

---

# 201. Link-time memory limits

Resource limits:

```text
max_objects
max_symbols
max_sections
max_relocations
max_output_size
max_memory
```

---

# 202. Large symbol tables

Use compact string tables and integer symbol IDs.

---

# 203. String table deduplication

Symbol names share canonical string storage.

---

# 204. Hash table

Use high-performance hash table with deterministic final iteration ordering.

---

# 205. Parallel object parsing

Objects can be parsed concurrently.

---

# 206. Parallel symbol extraction

Symbols extracted concurrently into local tables then merged deterministically.

---

# 207. Parallel relocation

Relocations in independent sections can be processed concurrently.

---

# 208. Final serialization

Only final binary layout serialization requires ordered deterministic emission.

---

# 209. Link graph

Internal dependency graph:

```text id="linkgraph"
root
 ↓
symbol
 ↓
object
 ↓
section
 ↓
symbol references
```

---

# 210. Reachability

Dead stripping uses symbol/section graph reachability.

---

# 211. Graph representation

Use integer IDs:

```text id="4cslj9"
ObjectId
SectionId
SymbolId
RelocationId
```

rather than pointer-heavy graph.

---

# 212. Archive indexing

Static archives should have symbol index for fast extraction.

---

# 213. Archive index determinism

Index generation deterministic.

---

# 214. Thin archives

Optional support if target ecosystem requires.

---

# 215. Library search diagnostics

Linker can report:

```text
searched:
libA
libB
libC
```

without arbitrary filesystem discovery beyond configured paths.

---

# 216. Missing library

Diagnostic:

```text
library not found
```

must include target/configuration and searched declared paths.

---

# 217. Wrong architecture library

Diagnostic should distinguish:

```text
library exists
but architecture mismatch
```

from not found.

---

# 218. ABI mismatch

Likewise:

```text
architecture matches
ABI incompatible
```

---

# 219. Mixed architecture

Universal/fat artifacts may be represented by higher-level packaging/toolchain layer.

AXLINKER can support multi-architecture linking where target format explicitly requires it.

---

# 220. Apple universal binary

Mach-O tooling may support:

```text
x86_64 slice
arm64 slice
```

combined into a universal artifact.

Each slice independently validated.

---

# 221. iOS architectures

Current target configuration determines supported slice set.

---

# 222. Windows ARM64

Architecture backend can later support PE64 ARM64 without changing generic linker model.

---

# 223. Linux RISC-V

ELF backend should be architecture-neutral enough for future RISC-V64.

---

# 224. Object format abstraction

```text
ObjectReader
ObjectWriter
```

interface:

```text
read_header()
read_sections()
read_symbols()
read_relocations()
write_header()
write_sections()
write_symbols()
write_relocations()
```

---

# 225. Format backend

```text
PEBackend
ELFBackend
MachOBackend
WASMBackend
```

---

# 226. Generic linker core

Generic:

```text
symbol resolution
reachability
section graph
address allocation
relocation planning
```

Target-specific:

```text
headers
segments
relocation encoding
imports
exports
TLS
startup
```

---

# 227. Linker pipeline

```text
Inputs
  ↓
Read
  ↓
Validate
  ↓
Index
  ↓
Resolve Symbols
  ↓
Extract Archives
  ↓
Build Reachability Graph
  ↓
Discard Dead Sections
  ↓
Merge Sections
  ↓
Layout
  ↓
Assign Addresses
  ↓
Apply Relocations
  ↓
Generate Dynamic Metadata
  ↓
Generate Debug/Unwind Metadata
  ↓
Generate Headers
  ↓
Validate
  ↓
Emit
```

---

# 228. Final binary verification

The linker must reopen or internally verify the generated artifact.

---

# 229. Binary self-check

Check:

```text
entry point
segment ranges
relocation consistency
symbol references
imports/exports
permissions
alignment
```

---

# 230. External validation

Optional platform tools can validate output during development.

Not a permanent dependency.

---

# 231. Testing

Test categories:

```text
object parsing
symbol resolution
archive extraction
relocations
section layout
PE
ELF
Mach-O
WASM
static linking
dynamic linking
TLS
debug
unwind
reproducibility
dead stripping
ICF
incremental linking
```

---

# 232. Golden binaries

Small deterministic test programs can compare exact:

```text
headers
sections
symbols
relocations
```

rather than necessarily entire binaries when platform metadata is variable.

---

# 233. Execution tests

Generated binaries run under supported target environments and compare expected behavior.

---

# 234. Cross-link tests

Every supported target should have:

```text
compile
assemble
link
validate
```

pipeline test.

---

# 235. Differential linker tests

During development, native AXLINKER output may be compared structurally with established system linkers.

External linker is oracle/test tool only.

---

# 236. Fuzzing

Fuzz:

```text
ELF
COFF
Mach-O
WASM
archives
symbols
relocations
```

parsers.

---

# 237. Malformed binary handling

Malformed object must result in controlled diagnostic, not arbitrary code execution.

---

# 238. Deterministic fuzzing

Each fuzz case records:

```text
seed
input hash
target
linker version
```

---

# 239. Bootstrap testing

Required:

```text
Stage0 → Stage1
Stage1 → Stage2
Stage2 → Stage3
Stage3 → Stage4
```

with convergence verification.

---

# 240. Formal invariants

```text id="linkinv"
LINK-INV-01
AXLINKER phải validate mọi input object trước khi sử dụng.

LINK-INV-02
Objects khác architecture không được link như native-compatible objects.

LINK-INV-03
Objects khác ABI không được silently merge.

LINK-INV-04
Strong symbol duplicate phải tạo deterministic error.

LINK-INV-05
Undefined required symbols không được silently resolve.

LINK-INV-06
Weak/strong symbol semantics phải tuân thủ target ABI.

LINK-INV-07
Static archive member chỉ được extract khi dependency/reachability yêu cầu hoặc explicit whole-archive.

LINK-INV-08
Archive search order phải deterministic.

LINK-INV-09
Section merging phải preserve required section semantics.

LINK-INV-10
Section alignment phải được preserve.

LINK-INV-11
Final section addresses phải deterministic.

LINK-INV-12
Final sections không được overlap bất hợp lệ.

LINK-INV-13
Relocation phải được validate trước application.

LINK-INV-14
Relocation overflow không được silently truncate.

LINK-INV-15
Undefined relocation target phải tạo error hoặc explicit dynamic import.

LINK-INV-16
PIC/PIE relocation model phải phù hợp target ABI.

LINK-INV-17
TLS layout phải tuân thủ target ABI.

LINK-INV-18
Entry point phải tồn tại và trỏ tới executable region hợp lệ.

LINK-INV-19
Import metadata phải phù hợp target format.

LINK-INV-20
Export metadata phải trỏ tới symbol hợp lệ.

LINK-INV-21
Final executable permissions phải respect configured W^X/security requirements.

LINK-INV-22
AXLINKER không được tự cấp security authority cho executable.

LINK-INV-23
System libraries chỉ được resolve qua declared SDK/sysroot/toolchain configuration.

LINK-INV-24
Linker không được tự động search arbitrary machine-wide libraries.

LINK-INV-25
Dead-section elimination chỉ được remove unreachable entities.

LINK-INV-26
ICF không được merge entities khi address identity semantics cấm.

LINK-INV-27
Debug/unwind metadata phải remain consistent với retained code.

LINK-INV-28
Parallel linking không được thay đổi semantic hoặc reproducible output.

LINK-INV-29
Symbol ordering trong deterministic mode phải canonical.

LINK-INV-30
Archive output phải deterministic.

LINK-INV-31
Build timestamps/paths không được tạo nondeterministic output trong reproducible mode.

LINK-INV-32
Cache key phải include objects, linker, target, ABI, SDK/sysroot và link options.

LINK-INV-33
Cached final artifacts phải được integrity-verify trước reuse.

LINK-INV-34
AXLINKER không được execute untrusted object/build code trong link operation.

LINK-INV-35
Resource limits phải được enforce cho malformed/hostile inputs.

LINK-INV-36
Failed linking không được publish partial artifact như valid output.

LINK-INV-37
PE64/ELF/Mach-O/WASM output phải pass format-specific structural validation.

LINK-INV-38
External linker chỉ là interoperability/bootstrap option, không phải permanent dependency.

LINK-INV-39
AXLINKER phải có native ABI ổn định `AXLINKER_ABI_1`.

LINK-INV-40
AXLINKER chịu trách nhiệm global symbol resolution, layout, relocation và final artifact construction; compiler semantics và instruction encoding thuộc AXCOMPILER/AXASSEMBLER.
```

---

# 241. Definition of Done

`AXLINKER 5.0` được freeze khi architecture bao phủ:

- object ingestion;
- object validation;
- symbol table;
- strong/weak symbols;
- visibility;
- symbol aliases;
- symbol versioning;
- static archives;
- lazy extraction;
- whole archive;
- section merging;
- section GC;
- reachability;
- section layout;
- address assignment;
- relocation engine;
- relocation overflow;
- PIC;
- PIE;
- TLS;
- static executable;
- dynamic executable;
- static library;
- dynamic library;
- PE64;
- ELF64;
- Mach-O;
- iOS;
- Android;
- WASM32;
- imports;
- exports;
- GOT/PLT-like mechanisms;
- IAT/import structures;
- ASLR metadata;
- RELRO;
- W^X;
- entry point;
- startup objects;
- minimal runtime linking;
- debug symbols;
- external debug artifacts;
- unwind metadata;
- LTO coordination;
- PGO code layout;
- ICF;
- constant merging;
- deterministic linking;
- incremental linking;
- link cache;
- parallel linking;
- resource limits;
- malformed object protection;
- native linker API;
- `AXLINKER_ABI_1`;
- bootstrap/self-hosting;
- 40 invariants.

**AXLINKER 5.0 → FROZEN.**

---

# BOOTSTRAP-773 — AXOBJECT

**Native Object File Model, COFF/PE, ELF, Mach-O, WASM Object Representation, Sections, Symbols, Relocations, Debug Metadata & Cross-Platform Object ABI 5.0**

Sau khi đã freeze compiler → assembler → linker, còn một lớp rất quan trọng cần tách rõ:

```text
AXCOMPILER
      ↓
AXASSEMBLER
      ↓
    AXOBJECT
      ↓
   AXLINKER
```

`AXOBJECT` sẽ chuẩn hóa **object artifact ABI** giữa compiler/assembler và linker, thay vì để AXLINKER phải phụ thuộc trực tiếp vào từng internal representation của AXASSEMBLER.

Đây sẽ là nền tảng để Axiom có thể:

- tạo `.obj/.o`;
- tạo `.a/.lib`;
- đọc object từ compiler khác;
- link C ABI;
- cache object;
- inspect object;
- cross-compile;
- hỗ trợ PE64/ELF/Mach-O/WASM;
- và cuối cùng xây dựng một native toolchain hoàn toàn độc lập.