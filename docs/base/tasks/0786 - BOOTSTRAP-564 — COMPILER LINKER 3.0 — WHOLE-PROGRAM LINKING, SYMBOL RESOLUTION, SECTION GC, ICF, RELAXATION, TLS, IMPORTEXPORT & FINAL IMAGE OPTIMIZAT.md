# BOOTSTRAP-564 — COMPILER LINKER 3.0 — WHOLE-PROGRAM LINKING, SYMBOL RESOLUTION, SECTION GC, ICF, RELAXATION, TLS, IMPORT/EXPORT & FINAL IMAGE OPTIMIZATION

**Trạng thái: COMPLETED / LOCKED**

`BOOTSTRAP-564` khóa tầng **Axiom Native Linker 3.0** — từ tập object files/LTO objects đến executable, shared library hoặc final native image.

Mục tiêu:

> Linker của Axiom phải là một native linker thực sự, hiểu ELF/PE/COFF/Mach-O, relocation, symbol visibility, TLS, imports/exports, archive extraction, section GC, ICF và relaxation; không cần gọi linker của GCC/Clang/MSVC trong production path.

---

# 564.1. Vị trí trong compiler

```text id="8v2m4q"
Source
  ↓
Frontend
  ↓
MIR
  ↓
Optimization
  ↓
LTO
  ↓
Machine Backend
  ↓
Machine Encoder
  ↓
Object Writer
  ↓
┌───────────────────────────────┐
│        AXIOM LINKER 3.0       │
├───────────────────────────────┤
│ Input Discovery               │
│ Symbol Resolution             │
│ Archive Extraction             │
│ Visibility / COMDAT / Weak    │
│ Section GC                    │
│ ICF                           │
│ Layout                        │
│ TLS                           │
│ Import / Export               │
│ Relocation                    │
│ Relaxation                    │
│ Segment Construction          │
│ Final Image Validation        │
└───────────────┬───────────────┘
                ↓
       Native Final Artifact
```

---

# 564.2. Linker không phải compiler

Linker không thực hiện:

- parsing Axiom source;
- type checking;
- trait solving;
- ownership checking;
- semantic optimization.

Linker nhận **native object-level representation**.

---

# 564.3. LTO boundary

Khi `563` bật:

```text
Object + LTO metadata
       ↓
LTO
       ↓
Optimized Object
       ↓
Linker
```

Linker không tự biến thành semantic optimizer.

---

# 564.4. Link input

Linker hỗ trợ:

```text id="n7x3m9"
Axiom object
C object
foreign object
static archive
shared library
system library
framework
LTO object
```

theo target policy.

---

# 564.5. Link request

```text id="q5m8v2"
LinkRequest {
    inputs[]
    target
    output_kind
    entry
    search_paths[]
    libraries[]
    frameworks[]
    exports[]
    imports[]
    linker_options
    security_policy
}
```

---

# 564.6. Output kinds

```text id="x3k7n5"
Executable
SharedLibrary
StaticLibrary
RelocatableObject
WasmModule
```

---

# 564.7. Link graph

```text id="m8q2v6"
Input Objects
     │
     ▼
Symbol Graph
     │
     ▼
Section Graph
     │
     ▼
Relocation Graph
     │
     ▼
Reachability Graph
     │
     ▼
Final Layout
```

---

# 564.8. Symbol model

```text id="v4n9q2"
Symbol {
    name
    kind
    binding
    visibility
    section
    value
    size
    alignment
    source
    linkage
}
```

---

# 564.9. Symbol kinds

Tối thiểu:

```text id="q7m3x8"
Function
Object
TLS
Section
Absolute
Undefined
Common
Import
Export
```

---

# 564.10. Symbol identity

Trong nội bộ linker:

```text id="m5x8q1"
LinkSymbolId
```

không phụ thuộc trực tiếp vào địa chỉ final.

---

# 564.11. Symbol states

```text id="x2v7n4"
Undefined
Defined
Tentative
Imported
Absolute
Discarded
Resolved
```

---

# 564.12. Strong definition

Nếu có một strong definition hợp lệ:

```text id="q9m4k6"
foo → selected definition
```

---

# 564.13. Duplicate strong definitions

Mặc định:

```text id="v6x2m8"
ERROR
```

Không được silently chọn một definition.

---

# 564.14. Weak symbol

Weak definition có thể bị strong definition thay thế theo target ABI.

---

# 564.15. Weak-weak

Nếu nhiều weak definitions cùng tồn tại, selection policy phải deterministic.

---

# 564.16. Common symbol

Nếu target/ABI hỗ trợ common symbols:

- size;
- alignment;

phải được merge chính xác.

---

# 564.17. Symbol visibility

```text id="m8q3v5"
Local
Hidden
Protected
Default
Exported
```

phụ thuộc object format.

---

# 564.18. Local symbols

Local symbol không tham gia external global resolution.

---

# 564.19. Global symbols

Global symbol tham gia resolution.

---

# 564.20. Undefined symbol

Nếu sau resolution vẫn undefined:

```text id="x7n2q9"
ERROR
```

trừ khi target output cho phép unresolved dynamic import.

---

# 564.21. Dynamic import

Executable/shared library có thể intentionally chứa dynamic imports.

---

# 564.22. Import identity

```text id="v3m8q5"
Import {
    library
    symbol
    version
    ordinal?
}
```

---

# 564.23. Export identity

```text id="q6x2n9"
Export {
    symbol
    public_name
    ordinal?
    version?
}
```

---

# 564.24. Symbol aliases

Linker có thể support:

```text id="m4v8q2"
alias → target
```

nhưng alias semantics phải deterministic.

---

# 564.25. Symbol versioning

ELF có thể hỗ trợ symbol versioning.

Version là một phần resolution identity khi enabled.

---

# 564.26. Archive

Static archive:

```text id="x9m3k7"
libA.axlib
 ├── a1.o
 ├── a2.o
 └── a3.o
```

---

# 564.27. Archive extraction

Object chỉ được extract khi cung cấp symbol cần thiết.

---

# 564.28. Archive algorithm

```text id="q5v8m2"
Roots
 ↓
Undefined symbols
 ↓
Archive index
 ↓
Extract matching object
 ↓
New symbols
 ↓
Repeat
```

---

# 564.29. Archive cycles

Cyclic dependencies phải được resolve deterministic.

---

# 564.30. Archive groups

Linker hỗ trợ group semantics nếu target ecosystem yêu cầu.

---

# 564.31. Thin archive

Có thể support archive chứa references tới external object.

---

# 564.32. Archive provenance

Mỗi extracted object phải retain:

```text id="n7q3x5"
archive
member
hash
```

---

# 564.33. Section model

```text id="m2v9k4"
Section {
    name
    type
    flags
    alignment
    size
    contents
    relocations[]
    source_sections[]
}
```

---

# 564.34. Section flags

```text id="x8q3m7"
ALLOC
EXEC
WRITE
TLS
MERGE
STRINGS
DEBUG
DISCARD
```

---

# 564.35. Input section

Mỗi object section được giữ identity riêng:

```text id="v4m7n2"
InputSectionId
```

---

# 564.36. Output section

Nhiều input sections có thể merge thành output section.

---

# 564.37. Section ordering

Ordering phải deterministic.

---

# 564.38. Alignment

Output section alignment:

```text id="q8x2m5"
max(input alignments, policy alignments)
```

theo target rules.

---

# 564.39. Padding

Padding bytes phải deterministic.

---

# 564.40. Zero-fill

BSS-like data không nhất thiết chiếm file bytes.

---

# 564.41. NOBITS

ELF `NOBITS` được support.

---

# 564.42. PE zero-fill

PE image section raw/virtual size phải được xử lý riêng theo PE semantics.

---

# 564.43. Mach-O zero-fill

Mach-O zerofill sections phải preserve đúng segment semantics.

---

# 564.44. Section GC

Linker có thể loại bỏ unreachable sections.

---

# 564.45. GC roots

Roots gồm:

```text id="m6q3v8"
entry
exports
dynamic imports/callbacks
runtime roots
keep directives
required metadata
```

---

# 564.46. Reachability

```text id="x5n8q2"
Root section
   ↓ relocation/reference
Referenced section
   ↓
...
```

---

# 564.47. Relocation edge

Relocation tạo graph edge:

```text id="v9m3k6"
Section A
   ──reloc──→
Section B
```

---

# 564.48. Direct reference

Direct symbol references cũng là reachability edges.

---

# 564.49. Metadata root

Exception/unwind/debug/runtime metadata có thể tạo root khi required.

---

# 564.50. GC safety

Không được loại bỏ function được gọi qua mechanism mà linker biết là external root.

---

# 564.51. User keep

Có explicit linker policy:

```text id="q7m2x4"
@link_keep
```

hoặc package/link manifest equivalent.

---

# 564.52. Section GC and dynamic loading

Exported/dynamically discoverable symbols phải được preserve.

---

# 564.53. COMDAT

COMDAT groups cho phép multiple equivalent definitions tồn tại.

---

# 564.54. COMDAT selection

Target/object-format-specific selection semantics phải được implement chính xác.

---

# 564.55. COMDAT identity

Group signature phải canonical.

---

# 564.56. COMDAT conflict

Conflicting non-equivalent members phải theo object-format policy, không silently merge.

---

# 564.57. ICF

Identical Code Folding:

```text id="m3q8v5"
foo
bar
```

→ một implementation nếu hợp lệ.

---

# 564.58. ICF safety

Không merge nếu function address identity observable.

---

# 564.59. Safe ICF

Safe mode chỉ merge functions khi stronger equivalence proof có.

---

# 564.60. Aggressive ICF

Aggressive ICF là explicit optimization policy.

---

# 564.61. ICF proof

```text id="x8v2m6"
CodeEquivalent
+
RelocationEquivalent
+
ObservableIdentityAllowed
```

---

# 564.62. Data folding

Read-only identical constants có thể fold nếu semantics cho phép.

---

# 564.63. Writable data

Writable data mặc định không được merge chỉ vì bytes giống nhau.

---

# 564.64. String pooling

String pooling phải respect language string identity semantics.

---

# 564.65. Relocation model

```text id="m4q9x2"
Relocation {
    offset
    type
    symbol
    addend
    width
    pc_relative
}
```

---

# 564.66. Relocation resolution

Linker tính:

```text id="v7n3m8"
S + A
S + A - P
GOT(S)
PLT(S)
TLS(S)
```

theo relocation type.

---

# 564.67. Overflow checking

Nếu relocation value không fit:

```text id="q2x8m5"
ERROR
```

hoặc relax/alternate sequence nếu target hỗ trợ.

---

# 564.68. No silent truncation

Relocation overflow tuyệt đối không được truncate.

---

# 564.69. PC-relative relocation

Phải dùng chính xác address:

```text id="m8v3q6"
P = relocation place
```

---

# 564.70. GOT

ELF PIC/PIE có thể sử dụng Global Offset Table.

---

# 564.71. PLT

Dynamic function calls có thể dùng Procedure Linkage Table.

---

# 564.72. GOT/PLT generation

Linker tự generate required entries khi target ABI yêu cầu.

---

# 564.73. IAT

PE/COFF dùng Import Address Table.

---

# 564.74. Import thunk

PE dynamic imports có thể cần thunk/stub.

---

# 564.75. Mach-O stubs

Mach-O dynamic symbol calls phải generate phù hợp stub/lazy binding mechanisms khi cần.

---

# 564.76. Dynamic symbol table

ELF dynamic output có:

```text id="x5m8q2"
.dynsym
```

khi required.

---

# 564.77. Dynamic string table

`.dynstr` phải đồng bộ với dynamic symbol references.

---

# 564.78. PE import table

Linker phải construct:

```text id="q7n3m9"
Import Directory
INT/ILT
IAT
DLL names
```

theo PE semantics.

---

# 564.79. PE export table

Support:

```text id="m2x8v5"
name exports
ordinal exports
forwarders
```

khi cần.

---

# 564.80. Mach-O load commands

Final image phải construct load commands đúng target.

---

# 564.81. ELF program headers

Final ELF image phải generate `PT_LOAD` và relevant program headers.

---

# 564.82. Segment construction

```text id="v8q3m4"
Sections
 ↓
Segments
 ↓
Virtual memory image
```

---

# 564.83. Segment permissions

Không tạo segment writable+executable mặc định.

---

# 564.84. W^X

Security policy ưu tiên:

```text id="x6m2n8"
W ⟂ X
```

trừ khi explicit target requirement.

---

# 564.85. RELRO

ELF linker có thể tạo RELRO region.

---

# 564.86. PIE

PIE phải được explicit target/link profile.

---

# 564.87. ASLR compatibility

PIE/shared images phải có relocation model phù hợp.

---

# 564.88. Static executable

Axiom hỗ trợ static executable nếu target/runtime libraries cho phép.

---

# 564.89. Dynamic executable

Có thể depend on system libraries theo manifest.

---

# 564.90. No hidden runtime dependency

Linker không tự thêm C++ runtime hoặc compiler runtime không được yêu cầu.

---

# 564.91. Axiom runtime

Runtime components chỉ được link nếu dependency graph yêu cầu.

---

# 564.92. Runtime pruning

```text id="q4v8m2"
program uses:
String
File
Thread
```

chỉ kéo các runtime components cần thiết.

---

# 564.93. Entry point

Linker nhận:

```text id="x7m3q9"
entry_symbol
```

và resolve final entry address.

---

# 564.94. Startup object

Axiom runtime startup có thể cung cấp:

```text id="m8q2v5"
_process_start
```

→ `main`.

---

# 564.95. Freestanding

Freestanding binary có thể bỏ startup runtime.

---

# 564.96. Custom entry

User có thể chỉ định explicit entry function.

---

# 564.97. TLS

TLS section được model:

```text id="v3n9q6"
ThreadLocalData
ThreadLocalBSS
TLS relocations
TLS runtime model
```

---

# 564.98. TLS identity

TLS symbol không được xử lý như ordinary data symbol.

---

# 564.99. TLS relocation

Target ABI quyết định TLS relocation semantics.

---

# 564.100. TLS model

Có thể có:

```text id="q5m8x2"
LocalExec
InitialExec
LocalDynamic
GeneralDynamic
```

khi target hỗ trợ.

---

# 564.101. TLS relaxation

Có thể relax TLS model nếu visibility/link context chứng minh được.

---

# 564.102. TLS correctness

Relaxation không được làm sai behavior khi module được dynamically loaded.

---

# 564.103. Link order

Linker phải có explicit deterministic ordering policy.

---

# 564.104. Library search

Search path resolution:

```text id="x8v3m6"
explicit
project
sysroot
target SDK
system
```

theo precedence.

---

# 564.105. No accidental host contamination

Cross compile không được tự động lấy library của host.

---

# 564.106. Sysroot

Target SDK/sysroot từ `483` phải xác định filesystem root.

---

# 564.107. Library identity

Library resolution phải record:

```text id="m4q7n2"
path
hash
target
ABI
version
```

---

# 564.108. Frameworks

Mach-O platform có thể hỗ trợ framework resolution.

---

# 564.109. SDK

iOS/macOS framework search phải dùng target SDK được chỉ định.

---

# 564.110. Android

Android target có thể resolve:

```text id="v7x3m8"
NDK/sysroot
system libraries
```

theo SDK manifest.

---

# 564.111. WASM linking

WASM finalization khác native ELF/PE/Mach-O.

---

# 564.112. WASM module composition

Linker có thể merge:

- functions;
- globals;
- memories;
- tables;
- data;
- elements.

---

# 564.113. WASM imports

Unresolved external symbols có thể trở thành WASM imports theo manifest.

---

# 564.114. WASM exports

Explicit exports trở thành module exports.

---

# 564.115. WASM data layout

Linear memory layout phải deterministic.

---

# 564.116. WASM start

WASM module có thể có start function nếu runtime profile yêu cầu.

---

# 564.117. Layout engine

Final address assignment:

```text id="q2m8v5"
Section
 ↓
Alignment
 ↓
Address
 ↓
Symbol Address
```

---

# 564.118. Address space

TargetAddressSpace:

```text id="x7n3m9"
code
data
tls
readonly
metadata
```

---

# 564.119. Layout constraints

Linker phải giải quyết:

- alignment;
- range;
- segment;
- page;
- section order;
- TLS;
- ABI-specific placement.

---

# 564.120. Page alignment

Segment alignment phải theo target/OS contract.

---

# 564.121. Section ordering optimization

Có thể reorder sections nhưng phải obey:

```text id="m5q8x2"
semantic constraints
relocation constraints
debug constraints
platform constraints
```

---

# 564.122. Function ordering

Có thể dùng PGO order.

---

# 564.123. Hot/cold sections

`563` có thể yêu cầu:

```text id="v3m7q9"
.text.hot
.text
.text.cold
```

Linker phải preserve hoặc merge theo target.

---

# 564.124. Relaxation

Linker có thể thay:

```text id="q8x2m5"
long sequence
```

bằng:

```text id="n4v7m2"
short sequence
```

khi range/layout cho phép.

---

# 564.125. Relaxation correctness

Mỗi relaxation phải có equivalence contract.

---

# 564.126. Multi-pass relaxation

```text id="m6q3x8"
layout
 ↓
measure
 ↓
relax
 ↓
relayout
 ↓
repeat
```

cho tới fixed point.

---

# 564.127. Relaxation termination

Số pass phải bounded hoặc có monotonic size reduction proof.

---

# 564.128. Branch relaxation

x86/AArch64 target backend có thể phối hợp linker nếu relocation model yêu cầu.

---

# 564.129. AArch64 veneers

Linker phải tạo veneer khi branch range không đủ.

---

# 564.130. PLT/GOT relaxation

Có thể direct-bind khi symbol visibility/locality chứng minh được.

---

# 564.131. TLS relaxation

Chỉ relax khi dynamic loading semantics vẫn đúng.

---

# 564.132. Link-time dead stripping

Section GC là default optimization trong release nếu ABI policy cho phép.

---

# 564.133. Debug build

Debug có thể disable aggressive GC để dễ debugging.

---

# 564.134. Debug retention

Debugger-required symbols/sections phải được giữ theo debug profile.

---

# 564.135. Unwind retention

Nếu function có unwind requirement, corresponding unwind metadata không được bị GC sai.

---

# 564.136. Exception metadata

Nếu target exception/unwind model yêu cầu, related tables là roots.

---

# 564.137. Panic abort

Nếu profile `panic=abort`, không link unnecessary unwind runtime.

---

# 564.138. Panic unwind

Nếu `panic=unwind`, linker phải preserve unwind metadata/runtime support.

---

# 564.139. Constructor/destructor

Platform initialization/finalization arrays phải được preserve:

```text id="x7m2q5"
ELF init/fini
PE CRT-like startup only if required
Mach-O init
```

Axiom không tự link foreign CRT chỉ vì constructor exists.

---

# 564.140. Initialization order

Linker không được tùy ý reorder observable initialization.

---

# 564.141. Link-time constructor discovery

Object metadata có thể mark initialization sections.

---

# 564.142. Static initialization

Axiom ưu tiên deterministic initialization semantics.

---

# 564.143. Resource embedding

Resource sections từ `469` có thể được linked thành final artifact.

---

# 564.144. Resource reachability

Resource chỉ bị strip nếu build policy chứng minh không cần.

---

# 564.145. Embedded assets

Assets có thể trở thành:

```text id="m8q3v7"
.rodata
resource section
platform bundle
```

---

# 564.146. Binary size optimization

Linker tối ưu:

- dead stripping;
- ICF;
- section merging;
- relocation packing;
- symbol stripping;
- metadata pruning.

---

# 564.147. Symbol stripping

Release artifact có thể strip local/debug symbols.

---

# 564.148. Build ID

Final image phải có deterministic build identity khi configured.

---

# 564.149. Debug split

Debug information có thể tách khỏi executable.

---

# 564.150. Reproducibility

Final binary không được chứa:

- timestamp ngẫu nhiên;
- host path không canonical;
- random UUID;
- machine-specific metadata;

trừ khi explicit reproducibility-disabled mode.

---

# 564.151. Deterministic symbol ordering

Symbol tables phải deterministic.

---

# 564.152. Deterministic section ordering

Section order phải deterministic.

---

# 564.153. Deterministic archive

Static archive member ordering phải deterministic.

---

# 564.154. Deterministic padding

Padding phải deterministic.

---

# 564.155. Link cache

Link cache key:

```text id="q6m3x8"
input artifact hashes
target fingerprint
link profile
sysroot fingerprint
linker version
security policy
```

---

# 564.156. Link cache correctness

Cache hit phải equivalent fresh link.

---

# 564.157. Incremental linking

Linker có thể reuse:

- symbol resolution;
- section layout;
- relocation computations;

khi dependencies unchanged.

---

# 564.158. Incremental safety

Incremental output phải equivalent clean link.

---

# 564.159. Parallel linking

Independent tasks:

```text id="x4m9v2"
parse objects
index symbols
read sections
compute GC
relocation preparation
```

có thể chạy parallel.

---

# 564.160. Deterministic merge

Final symbol/section/layout order không phụ thuộc worker order.

---

# 564.161. Linker daemon

Có thể tích hợp compiler daemon `555`, nhưng linker vẫn là component độc lập.

---

# 564.162. Link request cancellation

Build cancellation không được publish partially linked executable.

---

# 564.163. Atomic publication

Final artifact:

```text id="v8q2m5"
temporary output
 ↓
validate
 ↓
fsync/commit policy
 ↓
atomic rename
```

khi filesystem hỗ trợ.

---

# 564.164. Final image validator

Trước khi publish:

```text id="m3x7n9"
headers
sections
segments
symbols
relocations
imports
exports
entry
permissions
unwind
debug
```

phải được validate.

---

# 564.165. ELF validator

Kiểm tra:

- ELF header;
- program headers;
- section ranges;
- alignment;
- dynamic table;
- relocation;
- entry point;
- segment permissions.

---

# 564.166. PE validator

Kiểm tra:

- DOS/PE headers;
- section table;
- RVA/VA mapping;
- imports;
- exports;
- relocations;
- entry;
- image alignment;
- characteristics.

---

# 564.167. Mach-O validator

Kiểm tra:

- Mach header;
- load commands;
- segments;
- sections;
- symbols;
- relocations;
- code signature placeholders;
- entry/thread state.

---

# 564.168. WASM validator

Final module phải pass WASM structural/type validation.

---

# 564.169. Invalid final image

Không được publish artifact nếu validator fail.

---

# 564.170. Linker error model

Ví dụ:

```text id="q7m3x2"
L564001 duplicate symbol
L564002 undefined symbol
L564003 relocation overflow
L564004 invalid relocation
L564005 unsupported object
L564006 incompatible ABI
L564007 invalid TLS relocation
L564008 import resolution failure
L564009 export conflict
L564010 invalid final image
```

---

# 564.171. Diagnostic provenance

Mỗi linker diagnostic phải biết:

```text id="m5x8q3"
input object
archive/member
symbol
section
relocation
source metadata nếu available
```

---

# 564.172. Undefined symbol diagnostic

Ví dụ:

```text
undefined symbol: foo
referenced by:
  A.o:.text+0x34
```

---

# 564.173. Duplicate symbol diagnostic

Hiển thị:

```text id="x2q7m9"
definition A
definition B
```

và provenance.

---

# 564.174. Relocation overflow diagnostic

Phải hiển thị:

```text id="v8m3k5"
relocation type
symbol
computed value
allowed range
object
section
offset
```

---

# 564.175. ABI mismatch

Linker phải reject incompatible ABI metadata nếu metadata available.

---

# 564.176. Object target mismatch

Ví dụ:

```text id="q3x9m7"
AArch64 object
```

không được link vào:

```text
x86-64 executable
```

---

# 564.177. Endianness mismatch

Phải reject.

---

# 564.178. Pointer-width mismatch

Phải reject incompatible object ABI.

---

# 564.179. OS ABI mismatch

Phải reject target-incompatible native object.

---

# 564.180. Foreign object compatibility

Foreign objects có thể link nếu ABI contract compatible.

---

# 564.181. Link manifest

Build system có thể khai báo:

```text id="m7q2x8"
required_symbols
exports
imports
libraries
frameworks
search_policy
```

---

# 564.182. Capability-aware linking

Linker không được tự grant runtime capabilities.

Artifact manifest phải reflect actual dependencies.

---

# 564.183. Dependency closure

Final artifact phải có dependency graph:

```text id="x5m9v2"
Executable
 ├── Axiom runtime
 ├── system library
 └── dynamic library
```

---

# 564.184. Static closure

Static build phải resolve toàn bộ symbols trừ explicit external imports.

---

# 564.185. Dynamic closure

Dynamic dependencies phải được recorded.

---

# 564.186. Deployment integration

`489` package builder lấy dependency closure từ linker.

---

# 564.187. Security integration

`490/549/550` có thể kiểm tra:

- unexpected imports;
- writable executable sections;
- unsigned dynamic dependencies;
- unsafe loader behavior.

---

# 564.188. Code signing boundary

Linker tạo final image; code signing là subsequent artifact-finalization phase khi platform yêu cầu.

---

# 564.189. Signature invalidation

Bất kỳ thay đổi bytes sau signing đều invalidate signature.

---

# 564.190. Linker correctness

Linker correctness contract:

```text id="v7m3q9"
Semantics(objects)
=
Semantics(final image)
```

trong target ABI/platform model.

---

# 564.191. Linker differential testing

Có thể so sánh final execution với:

- Axiom reference;
- independent linker;
- platform loader.

Independent tools chỉ validation, không phải production dependency.

---

# 564.192. Relocation fuzzing

Random valid/invalid relocation graphs phải không crash linker.

---

# 564.193. Object fuzzing

Malformed object files phải:

```text id="q2x8m4"
reject safely
```

---

# 564.194. Archive fuzzing

Malformed archives/member indices không được crash linker.

---

# 564.195. Layout fuzzing

Random section sizes/alignment/relocations phải test overflow và termination.

---

# 564.196. Stress test

Phải test:

- hàng chục nghìn object;
- hàng triệu symbols;
- graph lớn;
- deep archive dependency;
- huge relocation sets;
- large TLS;
- large executable;
- massive dead code.

---

# 564.197. Performance

Linker phải có metrics:

```text id="m6q3v8"
input_read
symbol_resolution
archive_scan
GC
ICF
layout
relocation
relaxation
image_write
validation
```

---

# 564.198. AI introspection

AI tooling có thể query:

```text id="x8m2q5"
why_symbol_kept
why_symbol_discarded
why_archive_member_extracted
why_icf_not_applied
why_relocation_failed
why_dependency_present
```

---

# 564.199. Acceptance matrix

Linker phải pass tối thiểu:

```text id="q4v9m2"
x86-64 + ELF
x86-64 + PE/COFF
x86-64 + Mach-O
AArch64 + ELF
AArch64 + Mach-O
WASM
```

với:

- executable;
- static library;
- shared library khi platform hỗ trợ;
- imports/exports;
- TLS;
- relocations;
- debug/unwind;
- GC;
- LTO.

---

# 564.200. HARD INVARIANTS

1. Linker không được thay đổi language semantics.
2. Linker không được thay đổi type semantics.
3. Linker không được thay đổi ownership semantics.
4. Linker không được thay đổi memory model.
5. Linker không được thay đổi ABI.
6. Linker phải resolve symbols deterministic.
7. Duplicate strong symbols phải diagnostic.
8. Undefined symbols phải diagnostic trừ explicit dynamic imports.
9. Weak resolution phải deterministic.
10. Common symbol handling phải target-correct.
11. COMDAT selection phải target-correct.
12. Symbol visibility phải preserve.
13. Exported symbols phải preserve.
14. Dynamic symbols phải preserve.
15. Address-taken semantics phải preserve.
16. Function pointer semantics phải preserve.
17. Section identity phải stable trong link invocation.
18. Section ordering phải deterministic.
19. Section alignment phải đúng.
20. Padding phải deterministic.
21. Relocations phải được validate.
22. Relocation overflow không được silent truncate.
23. PC-relative relocation phải dùng đúng P.
24. Absolute relocation phải dùng đúng S/A semantics.
25. GOT relocation phải đúng ABI.
26. PLT relocation phải đúng ABI.
27. IAT phải đúng PE semantics.
28. Mach-O stubs phải đúng platform semantics.
29. TLS symbol không được xử lý như ordinary data.
30. TLS relocation phải đúng ABI.
31. TLS relaxation phải preserve semantics.
32. Dynamic loading semantics phải preserve.
33. Archive extraction phải deterministic.
34. Archive index phải được validate.
35. Archive cycles phải terminate.
36. Archive provenance phải preserve.
37. Section GC phải bắt đầu từ explicit roots.
38. Entry point phải là root.
39. Exported symbols phải là roots khi externally reachable.
40. Dynamic callbacks phải là roots khi declared.
41. Required metadata phải là roots.
42. Unknown external references không được GC nhầm.
43. User keep directives phải được respect.
44. ICF không được phá address identity.
45. Safe ICF phải có equivalence proof.
46. Aggressive ICF phải explicit.
47. Writable data không được fold tùy tiện.
48. Read-only data folding phải preserve semantics.
49. String pooling phải preserve language semantics.
50. Function ordering phải deterministic.
51. Hot/cold ordering phải deterministic.
52. PGO ordering phải provenance-rich.
53. PGO không được thay đổi semantics.
54. Layout phải satisfy alignment.
55. Layout phải satisfy address ranges.
56. Layout phải satisfy segment permissions.
57. Layout phải satisfy ABI constraints.
58. Layout phải satisfy TLS constraints.
59. Layout phải satisfy object-format constraints.
60. Relaxation phải preserve semantics.
61. Relaxation phải terminate.
62. Relaxation phải revalidate relocations.
63. Branch range overflow phải relax hoặc diagnostic.
64. AArch64 veneer phải preserve call semantics.
65. Long address sequence phải preserve address semantics.
66. GOT/PLT relaxation phải preserve dynamic binding.
67. TLS relaxation phải preserve loader behavior.
68. Segment permissions không được mặc định RWX.
69. W^X phải được respect theo security policy.
70. RELRO phải đúng khi enabled.
71. PIE phải đúng khi enabled.
72. Static linking phải không tạo hidden dynamic dependency.
73. Dynamic linking phải record dependency closure.
74. Linker không được tự link C++ runtime.
75. Linker không được tự link compiler runtime không cần thiết.
76. Axiom runtime phải dependency-driven.
77. Freestanding link phải không tạo implicit libc dependency.
78. Cross compile không được lấy host library ngoài policy.
79. Sysroot phải explicit.
80. Library search order phải deterministic.
81. Library identity phải hash/provenance-rich.
82. Framework resolution phải target-specific.
83. SDK resolution phải target-specific.
84. WASM linking phải tuân WASM type rules.
85. WASM imports phải explicit.
86. WASM exports phải explicit.
87. WASM memory layout phải deterministic.
88. WASM start function phải explicit.
89. Object ISA mismatch phải reject.
90. Object ABI mismatch phải reject.
91. Object OS mismatch phải reject khi incompatible.
92. Object endianness mismatch phải reject.
93. Object pointer-width mismatch phải reject.
94. Foreign object chỉ link khi ABI-compatible.
95. LTO object schema phải validate.
96. LTO metadata mismatch phải reject/fallback theo policy.
97. LTO output phải được validate trước final link.
98. LTO không được trở thành linker semantic authority.
99. Linker phải remain independent of LLVM.
100. Linker phải remain independent of GCC.
101. Linker phải remain independent of Clang.
102. Linker phải remain independent of MSVC linker/compiler path trong production architecture.
103. Independent linker tools chỉ dùng validation/development nếu có.
104. Final image phải được validate.
105. ELF header phải validate.
106. ELF program headers phải validate.
107. ELF section ranges phải validate.
108. ELF dynamic tables phải validate.
109. PE headers phải validate.
110. PE RVA mapping phải validate.
111. PE imports phải validate.
112. PE exports phải validate.
113. PE relocations phải validate.
114. Mach-O headers phải validate.
115. Mach-O load commands phải validate.
116. Mach-O segments phải validate.
117. Mach-O symbol/relocation data phải validate.
118. WASM module phải pass structural validation.
119. Invalid object phải reject safely.
120. Invalid archive phải reject safely.
121. Invalid relocation phải reject safely.
122. Invalid symbol graph phải reject safely.
123. Malformed LTO metadata không được crash.
124. Fuzz input không được crash linker.
125. Integer overflow trong layout phải detect.
126. Address overflow phải detect.
127. Size overflow phải detect.
128. Alignment overflow phải detect.
129. File-offset overflow phải detect.
130. Virtual-address overflow phải detect.
131. Symbol table indices phải bounds-check.
132. Section references phải bounds-check.
133. Relocation offsets phải bounds-check.
134. String table references phải bounds-check.
135. Import/export indices phải bounds-check.
136. Link cancellation không được publish partial artifact.
137. Final publication phải atomic khi platform hỗ trợ.
138. Link cache hit phải equivalent fresh link.
139. Incremental link phải equivalent clean link.
140. Parallel link phải equivalent serial link.
141. Worker ordering không được ảnh hưởng output semantics.
142. Archive scan ordering không được ảnh hưởng semantics.
143. Cache state không được ảnh hưởng semantics.
144. Linker output phải reproducible khi configured.
145. Timestamp không được làm binary nondeterministic trong reproducible mode.
146. Host path không được leak vào release artifact trong reproducible mode.
147. Random identifiers không được leak vào reproducible artifact.
148. Symbol ordering phải deterministic.
149. Section ordering phải deterministic.
150. Archive member ordering phải deterministic.
151. Padding phải deterministic.
152. Build ID phải deterministic khi configured.
153. Debug split phải preserve symbol identity.
154. Unwind metadata phải match final addresses.
155. Debug metadata phải match final addresses.
156. Coverage metadata phải match final addresses.
157. Profiling metadata phải match final addresses.
158. Sanitizer metadata phải match final image.
159. Security metadata phải match final image.
160. Code signing phải occur after final byte mutation.
161. Signing mutation phải invalidate previous signature.
162. Unexpected imports phải detectable.
163. Unexpected exports phải detectable.
164. Unexpected dynamic dependencies phải detectable.
165. Executable writable sections phải detectable.
166. Security policy violations phải diagnostic.
167. Capability closure phải match actual dependencies.
168. Resource dependencies phải remain traceable.
169. Runtime dependencies phải remain traceable.
170. Platform dependencies phải remain traceable.
171. Link diagnostics phải preserve provenance.
172. Undefined symbol diagnostics phải identify referencing object.
173. Duplicate diagnostics phải identify all relevant definitions.
174. Relocation diagnostics phải identify offset/type/symbol.
175. ABI diagnostics phải identify incompatible metadata.
176. AI linker queries phải be snapshot/build bound.
177. AI explanations phải distinguish fact from heuristic.
178. Linker report phải machine-readable.
179. Linker performance metrics phải be optional.
180. Linker phải support large graphs without quadratic behavior by default.
181. Symbol lookup phải use indexed structures.
182. Archive lookup phải use indexed structures.
183. Section graph traversal phải be bounded.
184. GC traversal phải terminate.
185. ICF comparison phải be bounded/resource-controlled.
186. Relaxation phải terminate.
187. Incremental link invalidation phải dependency-aware.
188. Unrelated object changes không được force complete semantic recomputation khi avoidable.
189. LTO boundary phải remain explicit.
190. Dynamic library boundary phải remain explicit.
191. FFI boundary phải remain explicit.
192. Linker phải integrate `420` object model.
193. Linker phải integrate `421` ABI.
194. Linker phải integrate `440` debug/unwind.
195. Linker phải integrate `489` deployment.
196. Linker phải integrate `490` application security.
197. Linker phải integrate `550` compiler/supply-chain trust.
198. Linker phải integrate `552` correctness validation.
199. Linker phải integrate `562` target backend and target relocation model.
200. **Final invariant:** Axiom Linker phải biến tập object/LTO artifacts thành final native image một cách **ABI-correct, target-correct, deterministic, reproducible, secure và verifiable**, với symbol resolution, archive extraction, section GC, ICF, TLS, imports/exports, relocation, relaxation và final-image construction đều có provenance và validation; đồng thời production path không được phụ thuộc vào LLVM/GCC/Clang/MSVC linker/compiler để tạo native artifact.

**BOOTSTRAP-564: LOCKED.**

---

# NEXT — BOOTSTRAP-565

## COMPILER ARTIFACT FORMAT 2.0 — AXIOM OBJECT/LTO/SEMANTIC/DEBUG PACKAGE, SECTION SCHEMA, VERSIONING, COMPATIBILITY & ZERO-COPY COMPILATION CACHE

Bước tiếp theo sẽ khóa **định dạng artifact nội bộ của chính Axiom**.

Hiện tại các tầng đã có:

```text id="f1c8v0"
Source
 ↓
Semantic DB
 ↓
MIR
 ↓
LTO
 ↓
Machine IR
 ↓
Machine Code
 ↓
Object
 ↓
Linker
 ↓
Native Image
```

Nhưng để đạt mục tiêu ban đầu của Axiom là **compile nhanh, cache mạnh, precompiled reuse và AI có thể hiểu chương trình mà không cần parse lại toàn bộ source**, cần một artifact format thống nhất cho:

```text
.axsem    Semantic Artifact
.axmir    IR Artifact
.axobj    Axiom Object
.axlto    LTO Summary/IR
.axdbg    Debug/Source Mapping
.axpkg    Package Artifact
```

`565` sẽ đặc biệt tập trung vào việc biến các artifact này thành **content-addressed, versioned, mmap-friendly, zero-copy/low-copy và có thể kiểm chứng**, thay vì mỗi compiler phase tự phát minh một format riêng.