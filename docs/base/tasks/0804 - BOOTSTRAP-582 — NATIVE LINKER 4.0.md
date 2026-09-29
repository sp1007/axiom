# BOOTSTRAP-582 — NATIVE LINKER 4.0
## SYMBOL RESOLUTION, SECTION LAYOUT, RELOCATION APPLICATION, ARCHITECTURE RELAXATION, DEAD-SECTION GC, ICF, LTO OBJECT INTEGRATION, TLS, IMPORT/EXPORT, PLT/GOT/STUBS & FINAL EXECUTABLE IMAGE

**Trạng thái: COMPLETED / LOCKED**

`582` hoàn thiện nửa còn lại của native backend:

```text
581 Object
   │
   ▼
Object Ingestion
   │
   ▼
Symbol Graph
   │
   ├── Strong
   ├── Weak
   ├── COMDAT
   └── Undefined
   │
   ▼
Reachability / Section GC
   │
   ▼
ICF / Folding
   │
   ▼
Global Layout
   │
   ▼
Address Assignment
   │
   ▼
Relocation
   │
   ├── ELF
   ├── PE
   └── Mach-O
   │
   ▼
TLS / GOT / PLT / Stubs
   │
   ▼
Final Image
   │
   ▼
Image Verification
   │
   ▼
EXE / ELF / Mach-O
```

---

# 582.1. Linker boundary

Input:

```text
ObjectArtifact[]
LibraryArtifact[]
LinkConfiguration
Target
ABI
```

Output:

```text
LinkedImage
```

Linker không thực hiện parsing AST/HIR.

---

# 582.2. Native linker độc lập

Axiom linker không gọi:

- `ld`;
- `lld`;
- `gold`;
- `link.exe`;
- `ld64`;
- `mold`.

---

# 582.3. Canonical linker model

```text
LinkedImage {
    Sections
    Segments
    Symbols
    Relocations
    Imports
    Exports
    TLS
    EntryPoint
    Debug
    Unwind
}
```

---

# 582.4. Object ingestion

Linker đọc Axiom object model và normalize về canonical internal representation.

---

# 582.5. External object support

Axiom linker có thể hỗ trợ object format từ toolchain bên ngoài khi FFI yêu cầu.

Đây là **interop capability**, không phải dependency của Axiom compiler.

---

# 582.6. Input formats

Tối thiểu:

```text
Axiom Object
ELF relocatable
COFF object
Mach-O object
```

khi target/FFI profile bật.

---

# 582.7. Symbol graph

Linker xây:

```text
Symbol
  ↓
Definitions
References
Aliases
COMDAT
Weak relationships
```

---

# 582.8. Strong definition

Một symbol có một strong definition hợp lệ được resolve trực tiếp.

---

# 582.9. Duplicate strong definition

Hai strong definitions cùng symbol là link error trừ khi explicitly allowed bởi language/linkage policy.

---

# 582.10. Weak definition

Weak definition được sử dụng khi không có strong definition phù hợp.

---

# 582.11. Strong beats weak

Strong definition có precedence over weak definition theo canonical linkage rules.

---

# 582.12. Multiple weak definitions

Multiple equivalent weak definitions có thể resolve deterministic.

---

# 582.13. Undefined symbol

Undefined symbol phải được resolve từ:

```text
object
archive
shared library
platform import
```

hoặc báo lỗi.

---

# 582.14. Symbol alias

Alias trỏ tới canonical symbol.

---

# 582.15. Symbol visibility

Visibility phải được preserve qua linking.

---

# 582.16. Local symbols

Local symbols không conflict với local symbol khác object.

---

# 582.17. Global symbols

Global symbol namespace được resolve toàn image.

---

# 582.18. Symbol versioning

Nếu target hỗ trợ, symbol version trở thành một phần resolution key.

---

# 582.19. COMDAT key

COMDAT selection dựa trên canonical key.

---

# 582.20. COMDAT selection

Support các policy cần thiết:

```text
any
same-size
exact-match
largest
newest
associative
```

nếu format tương ứng hỗ trợ.

---

# 582.21. COMDAT equivalence

Hai COMDAT members chỉ được fold nếu selection semantics cho phép.

---

# 582.22. Archive

Static archive có dạng:

```text
archive
 ├── object A
 ├── object B
 └── object C
```

---

# 582.23. Archive extraction

Object trong archive chỉ được load khi symbol graph cần hoặc policy yêu cầu.

---

# 582.24. Archive fixed point

Archive extraction lặp đến khi symbol resolution đạt fixed point.

---

# 582.25. Archive ordering

Nếu traditional link order semantics được yêu cầu, Axiom phải preserve chúng.

---

# 582.26. Whole-archive

`whole_archive` buộc extract toàn bộ members.

---

# 582.27. Start-group/end-group

Cyclic archive dependencies được hỗ trợ bằng repeated resolution.

---

# 582.28. Dynamic library input

Dynamic libraries được biểu diễn bằng import/export metadata thay vì copy toàn bộ code.

---

# 582.29. Import symbol

Import symbol không có local code definition.

---

# 582.30. Export symbol

Export symbol được đưa vào final dynamic symbol table/import interface.

---

# 582.31. Symbol interposition

Nếu platform cho phép symbol interposition, linker phải preserve platform semantics.

---

# 582.32. Dead section elimination

Linker có thể loại bỏ section không reachable.

---

# 582.33. GC roots

Roots gồm:

```text
entry point
exports
runtime-required symbols
explicit linker roots
init/fini
platform-required metadata
```

---

# 582.34. Reachability graph

```text
Root
 ↓
Symbol
 ↓
Section
 ↓
Relocation
 ↓
Target Section
```

---

# 582.35. Relocation-driven reachability

Relocation reference tạo edge trong reachability graph.

---

# 582.36. Metadata reachability

Debug-only references không được vô tình giữ executable code alive.

---

# 582.37. Initialization roots

Global constructors/runtime initialization được coi là roots.

---

# 582.38. Unwind roots

Unwind metadata phải remain consistent với live functions.

---

# 582.39. Dead section removal

Dead section bị remove trước final layout.

---

# 582.40. No dangling references

Sau GC không được còn relocation tới section đã bị loại bỏ.

---

# 582.41. ICF

Identical Code Folding cho phép merge functions có identical semantics/bytes khi legal.

---

# 582.42. Safe ICF

Safe mode chỉ fold functions nếu address identity semantics không bị phá.

---

# 582.43. Aggressive ICF

Aggressive mode có thể fold address-equivalent functions khi language/linkage policy cho phép.

---

# 582.44. Function address identity

Axiom phải có explicit policy cho việc:

```text
fn_a == fn_b
```

khi lấy function address.

---

# 582.45. ICF canonical representative

Mỗi equivalence class có một deterministic representative.

---

# 582.46. ICF relocation rewriting

Relocations tới folded function phải được redirect tới representative.

---

# 582.47. ICF debug mapping

Debug aliases/ranges phải map tới representative mà không mất source identity.

---

# 582.48. Section folding

Không chỉ function; read-only data có thể fold nếu semantics cho phép.

---

# 582.49. Layout phase

Sau symbol/GC/ICF:

```text
Sections
 ↓
Segments
 ↓
Addresses
```

---

# 582.50. Section ordering policy

Ordering có thể tối ưu theo:

```text
size
hotness
alignment
startup
security
target constraints
```

nhưng phải deterministic.

---

# 582.51. Hot/cold splitting

PGO có thể tách hot/cold sections.

---

# 582.52. Code locality

Functions có thể được cluster để giảm branch/cache cost.

---

# 582.53. Function reordering

Function ordering phải không phá address-sensitive semantics.

---

# 582.54. Segment construction

Các sections được nhóm thành loadable segments.

---

# 582.55. Segment permissions

Không tạo writable+executable segment trừ khi target policy explicitly yêu cầu.

---

# 582.56. W^X

Default native image policy:

```text
WRITE XOR EXECUTE
```

---

# 582.57. Readonly data

RO data được tách khỏi writable data khi target hỗ trợ.

---

# 582.58. BSS

Zero-initialized data không cần chiếm raw file bytes nếu format hỗ trợ.

---

# 582.59. Virtual size

Segment có thể có:

```text
file_size < virtual_size
```

cho BSS.

---

# 582.60. Section alignment

Global layout phải satisfy mọi section alignment.

---

# 582.61. Segment alignment

Segment alignment phải satisfy target loader.

---

# 582.62. Page alignment

Executable images thường được page-align theo target loader requirements.

---

# 582.63. Address assignment

Linker gán:

```text
VA
RVA
file offset
section-relative address
```

theo target.

---

# 582.64. Image base

PE/Mach-O/ELF image base policy phải explicit.

---

# 582.65. PIE

PIE image không được phụ thuộc fixed load address ngoài ABI requirements.

---

# 582.66. ASLR

Image layout phải tương thích ASLR khi enabled.

---

# 582.67. Relocation application

Sau address assignment:

```text
Relocation
 ↓
Compute
 ↓
Range check
 ↓
Patch
```

---

# 582.68. Relocation formula

Canonical forms:

```text
S + A
S + A - P
```

và target-specific forms.

---

# 582.69. Relocation range

Nếu result không fit field → link error hoặc relaxation.

---

# 582.70. No truncation

Không silent truncate address.

---

# 582.71. Local relocation

Có thể resolve hoàn toàn trong linker.

---

# 582.72. External relocation

External dynamic relocation được giữ lại khi runtime loader cần.

---

# 582.73. Static relocation

Static executable phải resolve tất cả relocations có thể resolve tại link time.

---

# 582.74. Remaining relocation

Final executable chỉ được chứa runtime relocations mà platform loader hỗ trợ.

---

# 582.75. GOT

ELF/Mach-O dynamic references có thể sử dụng GOT-like tables.

---

# 582.76. GOT entry

Mỗi entry có canonical symbol identity.

---

# 582.77. GOT deduplication

Multiple references có thể share GOT entry.

---

# 582.78. PLT

Function calls tới dynamic symbols có thể sử dụng PLT-like mechanism.

---

# 582.79. PLT generation

PLT entries được tạo deterministic.

---

# 582.80. Direct-call optimization

Nếu linker chứng minh symbol local/non-preemptible, dynamic call có thể được relax thành direct call.

---

# 582.81. Stub generation

Architecture/platform-specific stubs được tạo khi direct branch range hoặc dynamic linking yêu cầu.

---

# 582.82. Stub deduplication

Identical stubs có thể share nếu semantics cho phép.

---

# 582.83. AArch64 veneers

AArch64 long-range branches có thể tạo veneer/thunk.

---

# 582.84. Veneer reachability

Mọi veneer target phải nằm trong legal branch range.

---

# 582.85. Veneer convergence

Veneer placement/layout phải converge deterministically.

---

# 582.86. x86-64 branch relaxation

x86 branch/call encodings có thể được relaxed khi layout thay đổi.

---

# 582.87. Relaxation ordering

Relaxation chạy trước final relocation patch.

---

# 582.88. Relaxation fixed point

Layout + relaxation phải đạt fixed point hoặc sử dụng safe long-form fallback.

---

# 582.89. TLS model

Linker hỗ trợ target TLS models phù hợp:

```text
local-exec
initial-exec
local-dynamic
general-dynamic
platform equivalent
```

---

# 582.90. TLS block

Final image chứa TLS data/BSS metadata.

---

# 582.91. TLS alignment

TLS alignment phải satisfy ABI.

---

# 582.92. TLS relocations

TLS relocations được resolve hoặc preserve theo target dynamic loader.

---

# 582.93. TLS initialization

Initial TLS image phải match object contributions.

---

# 582.94. TLS zero area

TLS BSS không chiếm raw initialized image bytes khi format cho phép.

---

# 582.95. ELF final image

ELF executable phải có:

```text
ELF header
program headers
loadable segments
entry point
dynamic metadata
relocations if required
```

---

# 582.96. ELF program headers

Program headers được tạo từ final segments.

---

# 582.97. ELF entry point

Entry address phải nằm trong executable segment.

---

# 582.98. ELF PT_LOAD

Load segments phải có legal permissions/alignment.

---

# 582.99. ELF dynamic section

Dynamic executable/shared object có dynamic metadata khi required.

---

# 582.100. ELF dynamic symbols

Only symbols required for runtime linkage được expose.

---

# 582.101. ELF GOT/PLT

Tables/sections phải match dynamic relocation model.

---

# 582.102. ELF RELRO

Linker có thể group readonly-after-relocation data theo security policy.

---

# 582.103. ELF GNU-style compatibility

Nếu interoperating with existing systems, Axiom có thể emit compatible GNU ecosystem structures mà không dùng GNU linker.

---

# 582.104. PE final image

PE linker phải tạo:

```text
DOS header/stub policy
PE signature
COFF header
optional header
section table
sections
data directories
```

khi producing Windows executable.

---

# 582.105. PE RVA

Internal addresses phải map chính xác sang RVA.

---

# 582.106. PE section alignment

File alignment và section alignment phải satisfy PE loader.

---

# 582.107. PE entry point

Entry RVA phải trỏ tới executable code.

---

# 582.108. PE import table

External DLL dependencies được serialize vào import structures.

---

# 582.109. Import descriptors

Mỗi imported module có canonical descriptor.

---

# 582.110. Import address table

IAT entries được tạo deterministic.

---

# 582.111. Export table

Exported functions/data được serialize nếu configured.

---

# 582.112. Base relocation

Nếu image policy yêu cầu, PE base relocation table được generate.

---

# 582.113. PE TLS

PE TLS directory, callbacks và TLS data được generate khi required.

---

# 582.114. PE unwind

`.pdata/.xdata` được integrated vào final image.

---

# 582.115. PE CFG

Nếu security policy bật, Control Flow Guard metadata phải được generate chính xác.

---

# 582.116. PE subsystem

Console/GUI subsystem là link configuration, không phải language semantic.

---

# 582.117. Mach-O final image

Mach-O linker phải tạo:

```text
Mach-O header
load commands
segments
sections
symbol data
dynamic linking metadata
```

---

# 582.118. Mach-O segment layout

Segments phải map đúng page/permission constraints.

---

# 582.119. Mach-O entry point

Entry metadata phải match platform startup convention.

---

# 582.120. Mach-O dyld info

Dynamic linking information được generate khi required.

---

# 582.121. Mach-O export trie

Export metadata phải encode canonical symbol graph.

---

# 582.122. Mach-O bind/rebase

Rebase/bind information phải match final addresses and dynamic-loader requirements.

---

# 582.123. Mach-O stubs

Dynamic function calls có thể require stub/lazy-binding structures.

---

# 582.124. Mach-O chained fixups

Nếu target deployment profile sử dụng chained fixups, linker phải hỗ trợ hoặc explicitly reject unsupported profile.

---

# 582.125. Mach-O code signature boundary

Code-signing data được đặt sau final image layout; signing không được làm thay đổi executable semantics.

---

# 582.126. iOS

iOS output phải respect architecture/platform/deployment target constraints.

---

# 582.127. Android

Android ELF output phải match Android ABI/API-level constraints.

---

# 582.128. Static library

Axiom linker/library builder phải có thể tạo static archive:

```text
libfoo.a
foo.lib
```

theo target.

---

# 582.129. Shared library

Support:

```text
.so
.dll
.dylib
```

theo platform.

---

# 582.130. Export policy

Chỉ symbols explicitly public/exported hoặc platform-required được expose.

---

# 582.131. Visibility optimization

Hidden/internal symbols cho phép linker tối ưu direct references.

---

# 582.132. Interposition barrier

Preemptible symbols không được tối ưu thành local references nếu platform semantics cấm.

---

# 582.133. LTO integration

Linker có thể nhận Axiom LTO objects từ `565`.

---

# 582.134. LTO object

LTO object chứa:

```text
IR
semantic metadata
machine fallback
symbol interface
```

---

# 582.135. Whole-program optimization

Nếu tất cả inputs là Axiom/LTO-compatible, linker có thể trigger whole-program optimization.

---

# 582.136. LTO boundary

Final LTO output quay trở lại:

```text
MIR
→ Machine IR
→ Encoder
→ Object
```

không bypass verification.

---

# 582.137. LTO determinism

LTO phải preserve deterministic artifact identity.

---

# 582.138. Incremental linking

Unchanged input sections/symbol groups có thể reuse layout fragments nếu safe.

---

# 582.139. Incremental invalidation

Thay đổi address-sensitive sections phải invalidate affected relocation/layout data.

---

# 582.140. Link cache

Cache key gồm:

```text id="linkcache"
Object hashes
Library hashes
Target
ABI
Link flags
Layout policy
Security policy
Linker version
```

---

# 582.141. Deterministic linking

Same inputs/configuration → byte-identical final image trong deterministic mode.

---

# 582.142. Randomization

ASLR runtime behavior không được biến build artifact thành nondeterministic.

---

# 582.143. Build path

Absolute build paths không được leak vào executable trừ debug configuration explicitly yêu cầu.

---

# 582.144. Build timestamp

Timestamp fields dùng zero/fixed value trong reproducible mode.

---

# 582.145. Build ID

Build ID được tính deterministic từ artifact identity.

---

# 582.146. Debug retention

Strip policy quyết định debug sections có được giữ hay không.

---

# 582.147. Unwind retention

Unwind data chỉ được strip khi target/runtime policy cho phép.

---

# 582.148. Symbol stripping

Private/local symbols có thể strip khỏi release image nhưng không được phá relocation/runtime semantics.

---

# 582.149. Export preservation

Exported API symbols không được strip.

---

# 582.150. Entry preservation

Entry point không được strip.

---

# 582.151. Startup preservation

Runtime startup functions phải remain reachable.

---

# 582.152. Init/fini ordering

Global initialization/finalization order phải preserve language/runtime contract.

---

# 582.153. Constructor arrays

Target-specific constructor arrays phải được emit deterministic.

---

# 582.154. Destructor arrays

Destructor registration phải preserve lifetime semantics.

---

# 582.155. Exception/unwind ranges

Final addresses phải update unwind ranges.

---

# 582.156. Panic runtime

Panic handlers/metadata phải resolve correctly.

---

# 582.157. Async runtime

Async runtime entry points phải be resolved like ordinary runtime symbols.

---

# 582.158. FFI symbols

C ABI symbols phải preserve exact mangling/linkage policy.

---

# 582.159. Symbol mangling

Axiom native symbol mangling phải deterministic và version-aware.

---

# 582.160. C names

`extern "C"` bypasses Axiom mangling.

---

# 582.161. Axiom names

Axiom symbols dùng canonical mangling để tránh collision.

---

# 582.162. ABI identity

Symbol ABI compatibility phải bao gồm calling convention/type ABI where needed.

---

# 582.163. Incompatible ABI

Linker phải reject incompatible ABI declarations.

---

# 582.164. Type metadata

Type metadata không được tự động coi là ABI-compatible chỉ vì symbol name giống nhau.

---

# 582.165. Link-time diagnostics

Error phải identify:

```text
symbol
definition
reference
object
section
relocation
```

---

# 582.166. Duplicate symbol diagnostic

Hiển thị toàn bộ conflicting definitions.

---

# 582.167. Undefined symbol diagnostic

Hiển thị references và searched libraries.

---

# 582.168. Relocation overflow diagnostic

Hiển thị symbol, relocation type, computed value và legal range.

---

# 582.169. Architecture mismatch

Object target mismatch phải fail rõ ràng.

---

# 582.170. ABI mismatch

ABI mismatch phải fail trước final image generation.

---

# 582.171. Security policy violation

RWX/invalid segment/security metadata violation phải fail closed.

---

# 582.172. Final image verifier

Verifier kiểm tra:

```text
headers
segments
sections
symbols
relocations
entry point
permissions
imports
exports
TLS
unwind
debug ranges
security metadata
```

---

# 582.173. Address verification

Every internal reference must resolve to a valid address.

---

# 582.174. External verification

Every unresolved external must be represented through valid dynamic/import metadata.

---

# 582.175. Entry verification

Entry point must be executable and mapped.

---

# 582.176. Segment verification

No section may lie outside containing segment.

---

# 582.177. Permission verification

Code/data permissions must satisfy policy.

---

# 582.178. Relocation verification

No unsupported final relocation remains.

---

# 582.179. TLS verification

TLS references must target valid TLS structures.

---

# 582.180. Unwind verification

Every unwind range must correspond to valid executable range.

---

# 582.181. Debug verification

Debug addresses must point into correct sections.

---

# 582.182. Import verification

Every imported symbol must have valid import-table representation.

---

# 582.183. Export verification

Every exported symbol must resolve to valid image address.

---

# 582.184. Fuzzing

Linker phải fuzz:

- symbol graphs;
- COMDAT;
- relocations;
- section layouts;
- archives;
- malformed objects;
- import/export;
- TLS;
- dynamic metadata.

---

# 582.185. Differential linking

Axiom output có thể được so sánh với trusted reference toolchain cho interoperability testing.

Reference toolchain chỉ dùng để **test**, không phải runtime/build dependency.

---

# 582.186. Executable testing

Generated binaries phải được chạy trong target test environment.

---

# 582.187. Minimal executable test

Compiler phải có golden test:

```text
Axiom source
→ object
→ link
→ executable
→ execute
→ expected result
```

---

# 582.188. Cross-target testing

Mỗi target backend phải có native artifact tests.

---

# 582.189. Reproducibility test

Linking twice phải tạo byte-identical output.

---

# 582.190. Incremental test

Incremental link output phải semantic-equivalent full rebuild.

---

# 582.191. Parallel test

Parallel link phải semantic-equivalent serial link.

---

# 582.192. Cache test

Cache hit phải tạo artifact tương đương cache miss.

---

# 582.193. Remote test

Remote-linked artifact phải pass same verifier as local artifact.

---

# 582.194. No repair dependency

Final linker không được dựa vào external linker để repair output.

---

# 582.195. Native self-hosting

Sau bootstrap hoàn chỉnh, Axiom linker phải có thể link chính compiler Axiom.

---

# 582.196. Bootstrap chain

```text id="boot582"
Stage0 compiler
    ↓
Axiom compiler
    ↓
Axiom object writer
    ↓
Axiom linker
    ↓
Axiom compiler executable
    ↓
self-host
```

---

# 582.197. Trusted linker

Linker binary là một thành phần trong compiler trust chain `488/550`.

---

# 582.198. Linker provenance

Final image có thể record:

```text
compiler version
linker version
target
ABI
build identity
```

theo metadata policy.

---

# 582.199. FINAL HARD INVARIANT

> **Axiom Linker phải tự resolve symbol, extract archive members, loại dead sections, thực hiện COMDAT/ICF, layout sections/segments, assign addresses, relax branches, generate TLS/GOT/PLT/stubs/import/export metadata và apply relocations để tạo final native image hợp lệ. Linker không được phụ thuộc vào external linker, không được silent truncate hoặc bỏ unresolved reference, và final image chỉ được phát hành sau khi toàn bộ address, relocation, ABI, permission, entry-point, TLS, unwind và platform-format invariants đã được verify.**

# 582 — LOCKED

Đến đây chuỗi native backend cốt lõi đã là:

```text
Source
  ↓
Frontend
  ↓
HIR / MIR
  ↓
Optimization
  ↓
Register Allocation
  ↓
Scheduling
  ↓
Machine Finalization
  ↓
Machine Encoding
  ↓
Object Writer
  ↓
Axiom Linker
  ↓
┌──────────────┬──────────────┬──────────────┐
│    ELF       │     PE       │   Mach-O     │
│   Linux      │   Windows    │ macOS/iOS    │
└──────────────┴──────────────┴──────────────┘
```

Không còn khoảng trống kiểu **“đến đây phải gọi LLVM/Clang/ld/MSVC”** trong native compilation path.

---

# NEXT — BOOTSTRAP-583

## NATIVE IMAGE LOADER CONTRACT 2.0
### ELF/PE/MACH-O LOADABILITY, ENTRY POINT, PROCESS STARTUP, DYNAMIC LINKING, IMPORT RESOLUTION, TLS INITIALIZATION, MEMORY MAPPING, RELOCATION AT LOAD TIME & Axiom RUNTIME STARTUP

```text
Final Executable
       │
       ▼
OS Loader
       │
       ├── Headers
       ├── Segments
       ├── Imports
       ├── Relocations
       ├── TLS
       └── Entry Point
       │
       ▼
Axiom Startup
       │
       ├── Runtime Init
       ├── TLS Init
       ├── Arguments
       ├── Environment
       ├── Allocator
       └── Main
       │
       ▼
Axiom Application
```

`583` sẽ khóa **hợp đồng giữa executable do Axiom linker tạo ra và OS loader/runtime startup** — tức bước cuối để chứng minh file EXE/ELF/Mach-O không chỉ “đúng format” mà thực sự có thể được OS load và chuyển quyền điều khiển vào chương trình Axiom.