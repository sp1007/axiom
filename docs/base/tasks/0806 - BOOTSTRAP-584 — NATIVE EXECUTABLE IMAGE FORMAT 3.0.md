# BOOTSTRAP-584 — NATIVE EXECUTABLE IMAGE FORMAT 3.0
## FINAL ELF/PE/MACH-O IMAGE CONSTRUCTION, SEGMENT PACKING, ENTRY/STARTUP STUBS, IMPORT/EXPORT TABLES, DYNAMIC RELOCATION, TLS IMAGE, UNWIND/DEBUG, RESOURCE PACKING & REPRODUCIBLE FINAL BINARY

**Trạng thái: COMPLETED / LOCKED**

`584` hợp nhất `582` và `583` thành tầng **final image construction**. Sau task này, Axiom không chỉ tạo object/link graph mà có đặc tả đầy đủ cho việc biến linked image thành **file binary mà OS/host thực sự có thể load**.

```text id="584arch"
Linked Image
     │
     ▼
Final Layout
     │
     ├── RX Code
     ├── R Readonly
     ├── RW Data
     ├── BSS
     ├── TLS
     ├── Unwind
     ├── Debug
     └── Metadata
     │
     ▼
Segment Builder
     │
     ▼
Platform Image Builder
 ┌───────┬────────┬─────────┐
 ▼       ▼        ▼         ▼
 ELF     PE      Mach-O    WASM
 │       │        │         │
 └───────┴────────┴─────────┘
             │
             ▼
      Final Image Bytes
             │
             ▼
       Image Verifier
             │
             ▼
       Reproducible Binary
```

---

# 584.1. Final image boundary

Input:

```text id="in584"
LinkedSections
ResolvedSymbols
AppliedRelocations
Imports
Exports
TLS
Unwind
Debug
Resources
SecurityMetadata
Target
```

Output:

```text id="out584"
ExecutableImage
```

---

# 584.2. Image types

Axiom phải support:

```text id="types584"
Executable
SharedLibrary
StaticLibrary
Object
WASMModule
FirmwareImage
```

---

# 584.3. Executable identity

Final artifact identity:

```text id="identity584"
Target
Architecture
ABI
Platform
CompilerVersion
LinkerVersion
ImageFormatVersion
SecurityPolicy
DebugPolicy
OptimizationIdentity
InputGraphHash
```

---

# 584.4. Image construction không thay đổi semantics

Image builder chỉ serialize final linked state.

Không được tự ý:

- optimize code;
- thay đổi instruction;
- thay đổi symbol resolution;
- thay đổi ABI.

---

# 584.5. Final address map

Image builder nhận address map từ linker.

```text id="addr584"
Symbol → VA/RVA
Section → VA/RVA
Segment → VA/RVA
```

---

# 584.6. Address consistency

Mọi address trong metadata phải lấy từ **một canonical final address map**.

---

# 584.7. File offset map

Mỗi file-backed region có:

```text id="filemap584"
virtual address
file offset
file size
memory size
```

---

# 584.8. Memory-only region

BSS/TLS zero-fill có thể có memory size lớn hơn file size.

---

# 584.9. Page model

Image layout phải respect target page granularity.

---

# 584.10. Segment builder

Segment builder group sections dựa trên:

```text id="segpolicy"
permissions
alignment
loader semantics
platform requirements
security policy
```

---

# 584.11. RX segment

Executable code và executable read-only metadata nằm trong RX/R policy phù hợp.

---

# 584.12. R segment

Readonly constants/debug-independent readonly structures có thể nằm trong R segment.

---

# 584.13. RW segment

Writable data nằm trong RW segment.

---

# 584.14. BSS extension

Zero-filled data có thể mở rộng RW segment memory range mà không tăng file payload.

---

# 584.15. TLS segment

TLS image là segment/metadata riêng theo platform ABI.

---

# 584.16. W^X

Default image policy:

```text id="wx584"
RX ≠ RW
```

---

# 584.17. RWX prohibition

RWX segment phải bị reject mặc định.

Chỉ profile đặc biệt mới được phép.

---

# 584.18. Segment ordering

Canonical:

```text id="order584"
headers
RX
R
RW
TLS
special
debug
signature
```

Target-specific format rules có thể điều chỉnh thứ tự.

---

# 584.19. Header placement

Headers phải nằm trong mapped/file range cần thiết của target.

---

# 584.20. Header protection

Headers không được vô tình executable nếu target policy không yêu cầu.

---

# 584.21. File alignment

Raw file regions phải satisfy target file alignment.

---

# 584.22. Virtual alignment

Virtual regions phải satisfy target virtual alignment.

---

# 584.23. Padding

Padding phải deterministic.

---

# 584.24. Padding security

Padding không được chứa uninitialized process data.

---

# 584.25. Zero initialization

Memory-only ranges phải được zero-initialized.

---

# 584.26. Section packing

Sections được pack theo final section ordering.

---

# 584.27. Function ordering

Function ordering từ linker phải được preserve.

---

# 584.28. Hot/cold sections

Hot/cold separation phải preserve final execution permissions.

---

# 584.29. Constant placement

Readonly constants không được đặt vào writable segment nếu không cần.

---

# 584.30. String literal placement

Immutable UTF-8 strings mặc định nằm trong readonly data.

---

# 584.31. Mutable static data

Mutable globals nằm trong writable data.

---

# 584.32. Uninitialized globals

Zero-initialized globals sử dụng BSS representation khi target hỗ trợ.

---

# 584.33. Runtime-generated data

Runtime initialization data không được nhầm với static data.

---

# ENTRY / STARTUP

# 584.34. Entry point source

Entry point được lấy từ linker-selected startup symbol.

---

# 584.35. Entry point address

Final image entry phải map tới executable bytes.

---

# 584.36. Entry stub

Platform có thể dùng startup stub:

```text id="stub584"
OS Entry
 ↓
Platform Adapter
 ↓
Axiom Startup
```

---

# 584.37. Stub ownership

Stub thuộc platform startup layer, không phải application source.

---

# 584.38. Stub encoding

Startup stub được compile/encode bởi chính Axiom backend hoặc canonical platform object.

---

# 584.39. No external CRT requirement

Axiom native executable không bắt buộc phải link C runtime/CRT.

---

# 584.40. Optional CRT interop

Có thể dùng CRT khi FFI/application yêu cầu.

---

# 584.41. Runtime-free entry

Minimal/freestanding executable có thể jump trực tiếp vào user-defined entry.

---

# 584.42. Hosted entry

Hosted application:

```text id="hosted584"
OS
 ↓
AxiomStartup
 ↓
RuntimeInit
 ↓
Main
```

---

# 584.43. Main return

`main` return value map tới platform exit code.

---

# 584.44. Startup failure

Startup initialization failure phải có deterministic termination path.

---

# 584.45. Initialization ordering

Dynamic global initialization chạy theo language-defined dependency ordering.

---

# 584.46. Initialization table

Platform image có thể chứa initialization arrays/metadata.

---

# 584.47. Constructor identity

Mỗi initialization function có stable identity.

---

# 584.48. Finalizer table

Shutdown/finalization functions được serialize nếu target requires.

---

# 584.49. No linker-order semantics

Initialization order không được phụ thuộc incidental section ordering.

---

# ELF FINAL IMAGE

# 584.50. ELF final builder

ELF builder tạo:

```text id="elf584"
ELF Header
Program Headers
Sections
Dynamic Metadata
Symbols
Relocations
Notes
Debug
```

khi các thành phần tương ứng tồn tại.

---

# 584.51. Program headers first-class

Final ELF loadability được xác định bởi program headers.

---

# 584.52. PT_LOAD construction

Mỗi loadable memory region được map thành appropriate `PT_LOAD`.

---

# 584.53. PT_LOAD permissions

Permissions phải match segment policy.

---

# 584.54. PT_PHDR

Nếu required, program-header self-reference phải valid.

---

# 584.55. PT_INTERP

Dynamic executable có interpreter path khi target profile yêu cầu.

---

# 584.56. PT_TLS

TLS image được biểu diễn bằng appropriate TLS program header.

---

# 584.57. PT_DYNAMIC

Dynamic section được referenced correctly.

---

# 584.58. PT_GNU_STACK compatibility

Nếu compatibility profile sử dụng GNU-style stack metadata, stack executable policy phải được encode.

---

# 584.59. PT_GNU_RELRO

RELRO region được map nếu security policy bật.

---

# 584.60. Entry point

`e_entry` phải point vào mapped executable range.

---

# 584.61. ELF image size

Final image size phải cover all loadable segments.

---

# 584.62. ELF section headers

Section headers có thể được retained hoặc stripped tùy image profile, miễn loader requirements không bị phá.

---

# 584.63. Stripped executable

A stripped ELF vẫn phải loadable.

---

# 584.64. Dynamic executable

Dynamic metadata phải consistent với imports/exports.

---

# 584.65. Static executable

Không được để dangling dynamic-loader metadata khi static profile không yêu cầu.

---

# 584.66. ELF build ID

Build ID deterministic trong reproducible mode.

---

# PE FINAL IMAGE

# 584.67. PE builder

PE builder tạo:

```text id="pe584"
DOS header
PE signature
COFF header
Optional header
Section table
Sections
Data directories
```

---

# 584.68. DOS stub

DOS stub có thể là minimal deterministic stub.

---

# 584.69. PE signature

PE signature offset phải match DOS header metadata.

---

# 584.70. Optional header type

PE32+ được dùng cho 64-bit targets.

---

# 584.71. Image base

Image base phải match linker configuration.

---

# 584.72. Entry RVA

Entry RVA phải thuộc executable section.

---

# 584.73. Image size

`SizeOfImage` phải cover final virtual layout.

---

# 584.74. Headers size

`SizeOfHeaders` phải cover all PE headers.

---

# 584.75. Section table

Mỗi section phải có legal raw/virtual range.

---

# 584.76. Data directories

Directory entries chỉ được tạo khi corresponding structure tồn tại.

---

# 584.77. Import directory

Import directory phải point tới valid descriptors.

---

# 584.78. Export directory

Export directory phải reflect actual exported symbols.

---

# 584.79. Resource directory

Windows resources được packed theo resource tree.

---

# 584.80. TLS directory

TLS directory phải match actual TLS image.

---

# 584.81. Exception directory

Exception/unwind table phải match executable ranges.

---

# 584.82. Base relocation directory

Nếu ASLR/relocation policy yêu cầu, base relocation data phải đầy đủ.

---

# 584.83. Load configuration

Security/load configuration structures phải match enabled security features.

---

# 584.84. PE checksum

Checksum generation là optional/platform-specific policy.

---

# 584.85. PE deterministic mode

Timestamp/checksum-related fields phải được deterministic hóa.

---

# MACH-O FINAL IMAGE

# 584.86. Mach-O builder

Tạo:

```text id="macho584"
Mach Header
Load Commands
Segments
Sections
Dynamic Metadata
Symbols
Code Signature
```

khi applicable.

---

# 584.87. Segment commands

Segment commands phải match final virtual/file layout.

---

# 584.88. `__TEXT`

Code và immutable runtime structures được placed appropriately.

---

# 584.89. `__DATA`

Writable data được placed appropriately.

---

# 584.90. `__LINKEDIT`

Dynamic/symbol/signing structures được packed theo target rules.

---

# 584.91. Page alignment

Segment file/VM offsets phải satisfy target page alignment.

---

# 584.92. Entry metadata

Entry command/address phải match startup function.

---

# 584.93. Dyld metadata

Rebase/bind/export structures phải correspond với final image.

---

# 584.94. Imports

Dynamic dependencies phải match load commands.

---

# 584.95. Exports

Export trie phải match exported symbols.

---

# 584.96. Chained fixups

Nếu enabled, chain starts/segments phải correspond chính xác với fixup locations.

---

# 584.97. Code signature

Signature covers final signed regions theo platform rule.

---

# 584.98. Signature ordering

Final signing luôn sau layout/relocation.

---

# 584.99. Signing modification barrier

Không được sửa signed image sau signing.

---

# WASM FINAL MODULE

# 584.100. WASM output

WASM final artifact là module binary, không phải OS executable.

---

# 584.101. WASM magic/version

Header phải đúng WASM binary format.

---

# 584.102. Section order

Core sections phải xuất hiện theo format-defined ordering.

---

# 584.103. Type canonicalization

Equivalent function types được deduplicate deterministic.

---

# 584.104. Import indices

Import index spaces phải be computed trước function/code indices.

---

# 584.105. Function indices

Function section và code section phải có matching counts.

---

# 584.106. Memory

Memory declarations phải match generated accesses.

---

# 584.107. Table

Indirect-call table requirements phải match table section.

---

# 584.108. Start function

Nếu có, start function index phải valid.

---

# 584.109. Exports

Export names/indexes phải canonical.

---

# 584.110. Data segments

Data offsets phải be valid constant expressions.

---

# 584.111. Custom Axiom section

Axiom semantic metadata có thể nằm trong custom section.

---

# IMPORT / EXPORT

# 584.112. Import graph

Final image phải có complete import graph.

---

# 584.113. Import identity

Import key:

```text id="imp584"
module
symbol
ABI
version
```

---

# 584.114. Export identity

Export key:

```text id="exp584"
symbol
ABI
visibility
```

---

# 584.115. Export aliases

Alias exports không duplicate incompatible identities.

---

# 584.116. Import validation

Mọi imported symbol phải được target loader hỗ trợ.

---

# 584.117. Export validation

Mọi export phải map tới valid final address.

---

# 584.118. Dynamic dependency ordering

Dependency ordering phải deterministic.

---

# 584.119. Dependency cycles

Dynamic library cycles phải follow platform loader semantics hoặc fail during link.

---

# 584.120. Missing dependency

Final image không được claim dependency-free khi import metadata tồn tại.

---

# TLS IMAGE

# 584.121. TLS raw image

Final TLS initialized bytes phải được packed đúng.

---

# 584.122. TLS zero-fill

TLS BSS size được biểu diễn riêng.

---

# 584.123. TLS alignment

TLS alignment phải match target ABI.

---

# 584.124. TLS callbacks

Callback metadata phải point to valid startup/shutdown functions.

---

# 584.125. TLS module identity

Dynamic TLS module identity phải match loader metadata.

---

# 584.126. TLS relocation

TLS relocations phải be resolved or explicitly left to loader.

---

# 584.127. TLS thread creation

New thread TLS state phải derive from final TLS template.

---

# UNWIND / DEBUG

# 584.128. Unwind ranges

Final unwind ranges use final addresses.

---

# 584.129. DWARF

ELF/Linux debug information có thể use DWARF.

---

# 584.130. CodeView

Windows debug information có thể use CodeView/PDB-compatible structures.

---

# 584.131. Mach-O debug

macOS/iOS debug information follows platform-supported debug format.

---

# 584.132. Debug stripping

Release profile có thể strip debug payload.

---

# 584.133. Unwind preservation

Stripping debug không được strip required unwind information.

---

# 584.134. Source mapping

Source map offsets phải reference final image locations.

---

# 584.135. Function ranges

Debug/unwind ranges không được overlap incorrectly.

---

# 584.136. Panic ranges

Panic metadata phải match final machine function ranges.

---

# 584.137. Async metadata

Async frame metadata phải map tới final generated code where required.

---

# RESOURCE PACKING

# 584.138. Resource abstraction

Resource:

```text id="resource584"
type
name
language
payload
alignment
compression
```

---

# 584.139. Resource deduplication

Identical immutable resources có thể deduplicate.

---

# 584.140. Resource compression

Compression là packaging policy, không thay đổi runtime-visible bytes sau decompression.

---

# 584.141. Windows resource tree

PE resource hierarchy phải preserve:

```text id="rsrc584"
type
name
language
data
```

---

# 584.142. Resource alignment

Resource payloads phải satisfy format alignment.

---

# 584.143. Resource lookup

Runtime resource API phải map canonical resource identity.

---

# SECURITY

# 584.144. NX/DEP

Final image phải enable non-executable data where supported.

---

# 584.145. ASLR

Image flags/relocations phải match ASLR policy.

---

# 584.146. Stack protection

Stack protection metadata phải remain consistent with `579`.

---

# 584.147. CFI/CFG

Control-flow security metadata phải map final addresses.

---

# 584.148. RELRO

Readonly-after-relocation regions phải be correctly segmented.

---

# 584.149. No hidden writable code

Final image verifier phải detect executable sections that are writable.

---

# 584.150. Signature

Nếu target requires signing, unsigned artifact không được mark release-ready.

---

# REPRODUCIBILITY

# 584.151. Deterministic image

Same linked state + configuration → same bytes.

---

# 584.152. No wall-clock data

Không dùng current time trong deterministic image.

---

# 584.153. No hostname

Hostname không được đưa vào binary.

---

# 584.154. No process ID

PID không được đưa vào artifact.

---

# 584.155. Stable UUID

UUID nếu format bắt buộc phải derive deterministically.

---

# 584.156. Stable section order

Stable.

---

# 584.157. Stable symbol order

Stable.

---

# 584.158. Stable imports

Stable.

---

# 584.159. Stable exports

Stable.

---

# 584.160. Stable padding

Stable.

---

# 584.161. Stable resource ordering

Stable.

---

# 584.162. Stable debug identity

Debug artifact identity phải deterministic khi deterministic debug enabled.

---

# 584.163. Reproducible verification

Build system phải có:

```text id="repro584"
build A
build B
compare bytes
```

---

# VALIDATION

# 584.164. Image parser

Axiom phải có parser/reader cho final image formats.

---

# 584.165. Structural verification

Verifier kiểm tra headers, offsets, sizes, alignment.

---

# 584.166. Mapping verification

Mỗi virtual address phải map vào appropriate segment.

---

# 584.167. Entry verification

Entry phải executable.

---

# 584.168. Import verification

Imports phải point tới valid metadata.

---

# 584.169. Export verification

Exports phải resolve.

---

# 584.170. TLS verification

TLS metadata phải internally consistent.

---

# 584.171. Relocation verification

Không còn static relocation chưa resolve ngoài explicitly allowed runtime relocations.

---

# 584.172. Unwind verification

Unwind coverage phải match required functions.

---

# 584.173. Security verification

Permissions/security metadata phải satisfy selected profile.

---

# 584.174. Debug verification

Debug addresses phải map đúng.

---

# 584.175. WASM verification

WASM module phải pass structural/type validation.

---

# 584.176. OS smoke test

Mỗi supported native target phải có executable launch test.

---

# 584.177. Argument test

Test UTF-8/Unicode process arguments.

---

# 584.178. Environment test

Test environment initialization.

---

# 584.179. Dynamic library test

Test import/export.

---

# 584.180. TLS test

Test main-thread và multi-thread TLS.

---

# 584.181. ASLR test

Test image với randomized load address.

---

# 584.182. Unwind test

Test runtime failure/unwind stack.

---

# 584.183. Resource test

Test resource embedding/loading.

---

# 584.184. Reproducibility test

Repeated build phải byte-identical.

---

# 584.185. Incremental test

Incremental final image phải semantic-equivalent full rebuild.

---

# 584.186. Cross-target test

Target image phải reject mismatched CPU/ABI appropriately.

---

# 584.187. Fuzzing

Final image parser/verifier phải được fuzz bằng malformed binaries.

---

# 584.188. Differential testing

Final images có thể được kiểm tra bằng platform/reference loaders trong test environment.

---

# 584.189. No reference toolchain dependency

Reference toolchain chỉ phục vụ validation.

---

# 584.190. Final artifact cache

Verified final images có thể được cache bằng content-addressed identity.

---

# 584.191. Cache verification

Cache artifact phải validate target/configuration identity trước reuse.

---

# 584.192. Remote artifact

Remote-built image phải pass local image verifier.

---

# 584.193. Trust boundary

Image verifier là trust boundary trước khi artifact được phát hành.

---

# 584.194. Fail closed

Malformed/inconsistent image → reject.

---

# 584.195. No best effort

Image builder không cố sửa malformed linked state một cách âm thầm.

---

# 584.196. Native independence

Toàn bộ pipeline:

```text id="native584"
Axiom Source
 ↓
Axiom Compiler
 ↓
Axiom Machine Encoder
 ↓
Axiom Object Writer
 ↓
Axiom Linker
 ↓
Axiom Image Builder
 ↓
Native Binary
```

không cần LLVM/GCC/Clang/MSVC/ld/lld/ld64.

---

# 584.197. Self-hosting

Axiom compiler phải có khả năng build final executable của chính compiler bằng pipeline này.

---

# 584.198. Bootstrap verification

Stage0/Stage1/Stage2 phải có thể kiểm tra final image equivalence theo trust-chain policy.

---

# 584.199. FINAL HARD INVARIANT

> **Axiom Final Image Builder phải biến LinkedImage thành binary/module thực sự loadable trên target bằng cách tự xây chính xác headers, segments, section/file mapping, entry point, imports/exports, TLS, runtime relocation metadata, unwind/debug/resource/security structures và các format-specific structures của ELF, PE/COFF, Mach-O hoặc WASM. Final image phải được byte/structure verified trước khi phát hành, deterministic trong reproducible mode, không chứa hidden unresolved state và không cần external linker/compiler để sửa hoặc hoàn thiện binary.**

# 584 — LOCKED

Đến đây tầng native artifact đã thành một chuỗi khép kín:

```text id="closed584"
Source
  ↓
Semantic Compiler
  ↓
MIR
  ↓
Optimization
  ↓
Machine IR
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
Native Linker
  ↓
Final Image Builder
  ↓
OS/Host Loader
  ↓
Axiom Startup
  ↓
Runtime
  ↓
main()
```

Đặc biệt, **582 → 583 → 584** đã phân tách rõ ba vấn đề vốn thường bị trộn vào nhau:

```text id="separation584"
582 = LINK
     "symbols/address/relocation/layout"

583 = LOAD CONTRACT
     "OS/host sẽ load và khởi động thế nào"

584 = IMAGE
     "những byte/header/segment/metadata cuối cùng nằm trong file thế nào"
```

---

# NEXT — BOOTSTRAP-585

## NATIVE STARTUP & CRT REPLACEMENT 3.0
### ZERO-DEPENDENCY PROCESS ENTRY, PLATFORM STARTUP, ARGUMENT/ENVIRONMENT INITIALIZATION, GLOBAL CONSTRUCTORS, TLS BOOTSTRAP, EXIT/ABORT, PANIC BOOTSTRAP, SIGNAL/EXCEPTION BRIDGE & MINIMAL AXIOM RUNTIME

```text id="next585"
OS Loader
    │
    ▼
Axiom Entry Stub
    │
    ▼
Platform Startup
    │
    ├── CPU / ABI state
    ├── Stack state
    ├── Arguments
    ├── Environment
    ├── TLS
    ├── Process state
    └── Runtime bootstrap
           │
           ▼
    Global Initialization
           │
           ▼
       Axiom Main
           │
           ▼
      Runtime Shutdown
           │
           ▼
      Exit / Abort
```

`585` sẽ khóa **phần mà Axiom cần để thực sự thay thế CRT/startup layer**: chương trình native có thể bắt đầu từ OS entry point mà không cần `crt0`, MSVC CRT hay runtime startup của ngôn ngữ khác, đồng thời vẫn hỗ trợ đầy đủ hosted application, freestanding, panic, TLS, global initialization và process exit.