# BOOTSTRAP-195 — Linker, Object Model, Binary Layout & Final Native Image

**TRẠNG THÁI: FROZEN / COMPLETED**

Đây là tầng biến Axiom từ một compiler thành **một toolchain native hoàn chỉnh**.

Mục tiêu cuối:

```text
Axiom Source
    ↓
CompilerDB
    ↓
Verified MIR
    ↓
OptIR
    ↓
Machine IR
    ↓
Object Writer
    ↓
Axiom Linker
    ↓
Native Image
```

Không cần LLVM/Clang/LLD trong trạng thái self-hosted cuối cùng.

Trong bootstrap, vẫn có thể dùng chúng làm backend/linker tạm thời.

---

# 195.1. Object là semantic artifact, không chỉ là byte container

Axiom định nghĩa một abstraction chung:

```text
AxiomObject
 ├── Target
 ├── Sections
 ├── Symbols
 ├── Relocations
 ├── Imports
 ├── Exports
 ├── TLS
 ├── Unwind
 ├── DebugInfo
 ├── Metadata
 ├── Resources
 └── SecurityProperties
```

Sau đó mới serialize thành:

```text
PE/COFF
ELF
Mach-O
WASM
```

Do đó:

```text
Axiom Object Model
        ↓
Target Object Writer
        ↓
PE / ELF / Mach-O / WASM
```

Không để frontend biết chi tiết ELF hay PE.

---

# 195.2. Section Model

Object có các section logic:

```text
.text
.rodata
.data
.bss
.tls
.tls.data
.tls.bss
.unwind
.debug.*
.axmeta
.resource
```

Tên vật lý có thể target-specific.

Semantic section properties:

```text
Readable
Writable
Executable
Alloc
Loadable
TLS
DebugOnly
Metadata
Discardable
Mergeable
```

---

# 195.3. W^X

Axiom mặc định hỗ trợ:

> **Writable memory không đồng thời executable.**

Compiler/linker phải cố gắng tạo:

```text
RX → code
R  → read-only
RW → data
```

Không tạo:

```text
RWX
```

trừ khi platform/security profile explicit yêu cầu.

---

# 195.4. Symbol Model

Symbol không chỉ là string.

```text
Symbol
 ├── SymbolId
 ├── Name
 ├── Kind
 ├── Binding
 ├── Visibility
 ├── Section
 ├── Offset
 ├── Size
 ├── ABI
 ├── Version
 └── Flags
```

Kind:

```text
Function
Data
TLS
TypeMetadata
Import
Export
Absolute
Section
```

---

# 195.5. Symbol identity

Axiom semantic identity:

```text
PackageId
ModuleId
DeclarationId
```

khác machine symbol.

Compiler có thể map:

```text
DeclarationId
       ↓
LinkSymbol
       ↓
Object symbol
```

Điều này tránh việc source rename hoặc compiler mangling phá semantic identity.

---

# 195.6. Name mangling

Axiom có deterministic mangling:

```text
Package
Module
Declaration
Generic instance
ABI
```

nhưng mangling là implementation detail.

Không được coi mangled name là semantic identity.

C ABI:

```text
@export("foo")
```

có thể khóa external symbol name thành:

```text
foo
```

---

# 195.7. Relocation Model

Relocation:

```text
Relocation
 ├── Offset
 ├── Symbol
 ├── Type
 ├── Addend
 ├── Width
 └── Architecture
```

Compiler tạo relocation semantic.

Object writer chuyển thành relocation vật lý của:

- x86-64
- ARM64
- RISC-V
- WASM
- v.v.

---

# 195.8. Linker không được thay đổi semantics

Linker có thể:

- resolve symbol
- merge sections
- eliminate dead sections
- relax branches
- fold identical functions
- resolve relocations
- layout code/data
- generate import/export tables

Nhưng không được thay đổi observable semantics.

Linker cũng là một phần của correctness boundary.

---

# 195.9. Static linking

Static library:

```text
.axlib
```

có thể chứa:

```text
objects
metadata
generic definitions
ABI metadata
dependency information
optimization summaries
```

Linker chọn đúng object/section cần thiết.

Không link toàn bộ thư viện nếu không cần.

---

# 195.10. Dead section elimination

Axiom mặc định hướng tới binary nhỏ.

Linker có thể loại bỏ:

```text
unused function
unused data
unused metadata
unused runtime component
unused generic instance
```

Nhưng chỉ khi:

```text
reachability
reflection
dynamic loading
export
FFI
registration
```

không yêu cầu chúng.

---

# 195.11. Dynamic linking

Dynamic artifact:

```text
.axshared
```

hoặc target-native:

```text
.dll
.so
.dylib
```

chứa:

```text
exports
imports
relocations
ABI metadata
dependencies
```

Axiom không bắt mọi package phải dynamic.

---

# 195.12. Static vs dynamic là build policy

Ví dụ:

```text
--link static
--link dynamic
--link auto
```

Không phải language semantics.

Application có thể:

```text
single binary
```

hoặc:

```text
binary + shared libraries
```

---

# 195.13. Import/Export

Export explicit:

```axiom
@export("foo")
pub fn foo(...)
```

`pub` không tự động có nghĩa:

```text
binary export
```

Điều này đã phù hợp với ABI architecture 193.

---

# 195.14. Import

Foreign symbol:

```text
@import("foo")
extern "C" fn foo(...);
```

được chuyển thành:

```text
ImportSymbol
```

Linker xử lý:

```text
static symbol
dynamic symbol
system symbol
weak symbol
```

theo target contract.

---

# 195.15. TLS

Thread-local storage là một storage domain riêng:

```text
TLS
```

Compiler semantic:

```text
thread-local lifetime
```

Backend/linker xử lý:

```text
TLS section
TLS relocation
TLS initialization
```

Không đưa TLS semantics vào allocator.

---

# 195.16. Global constructors

Axiom không muốn phụ thuộc vào:

```text
global object constructor magic
```

Runtime initialization nên explicit.

Nếu cần initialization:

```text
@init
```

thì linker tạo startup registration.

Nhưng:

> **Không có global constructor registry mặc định.**

Điều này giữ binary nhỏ và startup predictable.

---

# 195.17. Startup

Native executable có:

```text
entry point
```

và startup layer:

```text
OS
 ↓
Axiom startup
 ↓
main
```

Freestanding:

```text
OS/firmware
 ↓
Axiom entry
```

Không bắt buộc CRT nếu target/profile không cần.

---

# 195.18. Exit

Các đường:

```text
return from main
panic
abort
OS exit
```

được phân biệt.

Runtime có thể map:

```text
main() -> i32
```

thành process exit code.

---

# 195.19. Unwind metadata

Nếu panic profile:

```text
abort
```

thì không cần unwind machinery.

Nếu:

```text
unwind
```

linker giữ:

```text
unwind tables
personality
LSDA
cleanup metadata
```

Nếu không sử dụng:

```text
unwind sections
```

có thể loại bỏ.

---

# 195.20. Debug sections

Debug metadata:

```text
DWARF
PDB
CodeView
```

được tạo từ:

```text
Source
HIR
MIR
Machine code
```

và giữ:

```text
variable locations
inline stack
source spans
type information
async frames
```

Debug data không ảnh hưởng release binary semantics.

---

# 195.21. Source → Machine provenance

Mỗi machine instruction có thể map:

```text
MachineInstruction
 ↓
MachineIR instruction
 ↓
MIR instruction
 ↓
HIR expression
 ↓
SourceSpan
```

Điều này tiếp tục thiết kế BOOTSTRAP-160/189.

---

# 195.22. Link-Time Optimization

Linker có thể nhận:

```text
OptIR
```

hoặc optimized object metadata để thực hiện:

```text
LTO
```

Pipeline:

```text
Object metadata
     ↓
Link-time IR
     ↓
Whole-program optimization
     ↓
Machine code
```

Nếu không có IR:

```text
object-only linking
```

vẫn phải hoạt động.

---

# 195.23. Linker GC

Linker có thể làm:

```text
--gc-sections
```

semantic equivalent:

```text
Reachable root analysis
       ↓
unreachable sections removed
```

Roots gồm:

```text
entry
exports
FFI symbols
dynamic symbols
reflection metadata
explicit keep
runtime roots
```

---

# 195.24. Reflection ảnh hưởng linker reachability

Nếu metadata nói:

```text
Type can be discovered dynamically
```

thì linker không được loại bỏ implementation cần thiết.

Do đó:

```text
Reflection
   ↓
Reachability
   ↓
Linker
```

đây là lý do BOOTSTRAP-185 phải tích hợp với linker.

---

# 195.25. Dynamic loading ảnh hưởng reachability

Nếu:

```text
dlopen
dlsym
GetProcAddress
```

được sử dụng, compiler/linker không thể giả định symbol không được gọi chỉ vì static call graph không thấy.

Phải có explicit dynamic symbol contract.

---

# 195.26. Identical Code Folding

Linker có thể merge function giống nhau:

```text
foo()
bar()
```

nếu:

```text
observable semantics
address identity
debug constraints
ABI
```

cho phép.

Nếu function address observable:

```text
identity
```

có thể ngăn folding.

---

# 195.27. Function address identity

Axiom phân biệt:

```text
Function behavior
Function identity
Function address
```

Không mặc định đảm bảo hai function khác nhau có địa chỉ khác nhau.

Nếu programmer cần identity:

```text
@unique_address
```

hoặc semantic requirement tương đương.

---

# 195.28. Data merging

Read-only constants có thể merge nếu semantic identity không bị ảnh hưởng.

Nhưng:

```text
address observable
mutable
volatile
FFI
```

có thể cấm merge.

---

# 195.29. Section permissions

Linker final image phải kiểm tra:

```text
section permissions
alignment
W^X
relocation permissions
TLS
imports
```

Security policy được kiểm tra ở binary boundary.

---

# 195.30. Relocation hardening

Nếu target hỗ trợ:

```text
RELRO
PIE
ASLR
CFI
shadow stack
BTI
PAC
```

Axiom profile có thể bật.

Nhưng security optimization không được thay đổi Core semantics.

---

# 195.31. PIE / ASLR

Executable có thể build:

```text
PIE
```

nếu target hỗ trợ.

Axiom source không cần biết địa chỉ load.

Raw pointer/address assumptions chỉ tồn tại trong unsafe/system code.

---

# 195.32. Static address assumptions

Compiler không được giả định:

```text
global == fixed virtual address
```

trừ khi explicit system contract.

Điều này đặc biệt quan trọng cho:

- PIE
- shared library
- ASLR
- embedded
- kernel

---

# 195.33. Binary layout

Final image:

```text
Header
Text
ReadOnly
Data
BSS
TLS
Imports
Exports
Relocations
Unwind
Metadata
Debug
Resources
```

Target ObjectWriter chịu trách nhiệm format.

---

# 195.34. PE/COFF

Axiom PE backend xử lý:

```text
PE headers
sections
imports
exports
relocations
TLS
resources
debug
subsystem
entry point
```

Không đưa PE concept vào Core compiler semantics.

---

# 195.35. ELF

ELF backend xử lý:

```text
ELF header
program headers
sections
symbols
relocations
TLS
dynamic section
PLT/GOT
unwind
notes
```

Axiom linker có thể tạo:

```text
ET_EXEC
ET_DYN
shared object
```

theo target/profile.

---

# 195.36. Mach-O

Mach-O backend xử lý:

```text
load commands
segments
sections
symbols
relocations
exports
imports
code signatures integration
dylib dependencies
TLS
```

iOS/macOS policy được đưa vào Target/SDK layer.

---

# 195.37. WASM object/linking

WASM backend không giả lập ELF.

Nó tạo:

```text
WASM module
imports
exports
linear memory
tables
data segments
custom sections
component metadata
```

Axiom object abstraction vẫn thống nhất ở tầng trên.

---

# 195.38. Resources

Windows resources, macOS bundles, Android assets... không thuộc Core language.

Chúng là:

```text
ResourceArtifact
```

được linker/package system ghép vào binary/bundle.

---

# 195.39. Code signing

Code signing:

```text
signature
certificate
entitlements
```

là distribution/security layer.

Không đưa cryptographic signature vào compiler semantic type system.

Compiler chỉ tạo artifact cần ký.

---

# 195.40. Binary reproducibility

Linker phải hỗ trợ deterministic mode:

```text
same inputs
→ same output
```

trong phạm vi target/toolchain contract.

Loại bỏ:

```text
timestamps
random ordering
unstable symbol ordering
nondeterministic section layout
```

khi reproducible profile bật.

---

# 195.41. Binary identity

Artifact fingerprint:

```text
BinaryFingerprint
```

bao gồm:

```text
semantic build identity
target
object format
link inputs
link configuration
runtime components
code signing policy
```

Debug timestamp hoặc signature có thể được excluded/normalized tùy profile.

---

# 195.42. Axiom Linker

Self-hosted linker:

```text
axld
```

hoặc tích hợp trong:

```text
ax
```

có các module:

```text
ObjectReader
SymbolResolver
ArchiveReader
SectionLayout
RelocationEngine
TLSLayout
ImportExport
DeadStrip
ICF
LTOBridge
BinaryWriter
DebugMerger
SecurityValidator
```

---

# 195.43. Không bắt buộc một linker cho mọi target

Axiom có:

```text
Linker Interface
```

và implementation:

```text
Axiom ELF linker
Axiom PE linker
Axiom Mach-O linker
Axiom WASM linker
```

Trong bootstrap:

```text
System linker / LLD
```

có thể implement interface.

Sau self-hosting:

```text
Axiom linker
```

thay thế dần.

---

# 195.44. Self-hosted toolchain

Trạng thái cuối:

```text
                 ax
                  │
       ┌──────────┴──────────┐
       │                     │
   Axiom Compiler        Axiom Linker
       │                     │
       └──────────┬──────────┘
                  ▼
             Native Image
```

Không cần:

```text
LLVM
Clang
GCC
LLD
MSVC
```

để **compile/link Axiom itself**, mặc dù system SDK/native system libraries vẫn có thể là dependency của target OS.

Điểm này rất quan trọng:

> **Không phụ thuộc compiler bên thứ ba ≠ không sử dụng OS SDK/ABI của nền tảng.**

---

# 195.45. Bootstrap stages

### Stage 0

```text
Bootstrap compiler
    ↓
LLVM/LLD
```

### Stage 1

```text
Axiom frontend
    ↓
Axiom MIR
    ↓
LLVM backend
```

### Stage 2

```text
Axiom compiler
    ↓
Axiom LIR
    ↓
Axiom machine encoder
    ↓
external linker
```

### Stage 3

```text
Axiom compiler
    ↓
Axiom ObjectWriter
    ↓
Axiom Linker
```

### Stage 4

```text
Axiom compiler
    ↓
Axiom compiler
```

Self-hosted.

---

# 195.46. Bootstrap compiler verification

Self-hosting không chỉ là:

```text
compiler compiles itself
```

Phải kiểm tra:

```text
Compiler A
   ↓ compile compiler source
Compiler B
   ↓ compile compiler source
Compiler C
```

và so sánh:

```text
semantic behavior
ABI
diagnostics
bootstrap convergence
```

Có thể không yêu cầu byte-for-byte identical machine code trong mọi profile, nhưng phải có deterministic semantic/build profile khi yêu cầu.

---

# 195.47. Linker correctness

Linker cũng có test oracle:

```text
AxiomObject
    ↓
Reference linker
    ↓
Expected binary behavior
```

và:

```text
Axiom linker
    ↓
binary
```

so sánh behavior.

Mislink trở thành regression test giống miscompile.

---

# 195.48. Linker không có quyền bypass verifier

Một object chứa metadata:

```text
Verified
```

nhưng linker không được tự ý giả định semantic facts ngoài contract.

Linker chỉ được sử dụng facts được object format/ABI contract xác định.

---

# 195.49. Final native image là artifact, không phải semantic source

Sau linker:

```text
.exe
ELF
Mach-O
WASM
```

không còn cần toàn bộ CompilerDB.

Có thể strip:

```text
source
debug
metadata
reflection
```

tùy profile.

---

# 195.50. Invariants — BOOTSTRAP-195

### `ALINK-20`
Axiom shall define a target-independent logical object model.

### `ALINK-21`
Object serialization shall be target-specific and separate from language semantics.

### `ALINK-22`
Symbols shall have semantic identity distinct from their physical names.

### `ALINK-23`
Relocations shall be explicit link-time contracts.

### `ALINK-24`
The linker shall not change observable language semantics.

### `ALINK-25`
Dead-code elimination shall respect exports, FFI, reflection, dynamic loading, runtime roots, and explicit keep contracts.

### `ALINK-26`
Function and data merging shall preserve all observable identity guarantees.

### `ALINK-27`
TLS shall be represented as an explicit storage domain.

### `ALINK-28`
Startup initialization shall not require a mandatory global object-constructor runtime.

### `ALINK-29`
Unwind metadata shall only be retained when required by the selected error/panic/unwind model.

### `ALINK-30`
Debug information shall remain removable without changing release semantics.

### `ALINK-31`
Link-time optimization shall preserve ABI contracts.

### `ALINK-32`
Stable ABI entry points may use optimized private implementations behind adapters.

### `ALINK-33`
Static and dynamic linking shall be explicit build policies.

### `ALINK-34`
Dynamic symbol dependencies shall preserve required library lifetime and ABI compatibility.

### `ALINK-35`
Binary section permissions shall support W^X where the target permits it.

### `ALINK-36`
Security hardening shall not alter Core language semantics.

### `ALINK-37`
Executable layout shall not imply fixed virtual addresses unless explicitly contracted.

### `ALINK-38`
Reproducible linking shall use deterministic ordering and normalized build metadata.

### `ALINK-39`
PE, ELF, Mach-O and WASM shall be target backends of a common object model.

### `ALINK-40`
The object writer shall not require the frontend to understand target-specific binary formats.

### `ALINK-41`
The linker shall support native static and dynamic artifacts according to target policy.

### `ALINK-42`
Axiom shall provide an implementation-independent linker interface.

### `ALINK-43`
External linkers may implement the linker stage during bootstrap.

### `ALINK-44`
The final self-hosted toolchain shall be capable of producing native Axiom binaries without requiring a third-party compiler or linker.

### `ALINK-45`
System SDKs and platform ABI libraries remain legitimate external target dependencies.

### `ALINK-46`
Self-hosting correctness shall be validated through bootstrap comparison and regression testing.

### `ALINK-47`
Linker failures and incompatibilities shall be diagnosed before producing an invalid executable whenever detectable.

### `ALINK-48`
The final native image shall not require compiler metadata unless the selected runtime/tooling profile explicitly requires it.

### `ALINK-49`
Unused runtime, reflection, debug, and metadata components shall be removable.

### `ALINK-50`
Linker correctness shall be included in the compiler/toolchain correctness model.

---

# Kết luận BOOTSTRAP-195

Tới đây chuỗi compiler architecture đã đi gần như trọn đường:

```text
Source
  ↓
Frontend
  ↓
Typed HIR
  ↓
MIR
  ↓
Ownership / Capability / Effect
  ↓
Verified MIR
  ↓
OptIR
  ↓
ABI lowering
  ↓
Axiom LIR
  ↓
Machine IR
  ↓
Machine Code
  ↓
Axiom Object
  ↓
Axiom Linker
  ↓
Native Image
```

Và đặc biệt, mục tiêu ban đầu của Axiom:

> **Không phụ thuộc compiler bên thứ ba**

đã có kiến trúc để đạt được.

Trong bootstrap có thể dùng LLVM/LLD; nhưng chúng **không trở thành dependency kiến trúc vĩnh viễn**.

---

# BOOTSTRAP-196 — Runtime Composition, Startup, Minimal Runtime & Freestanding Execution

**TRẠNG THÁI: NEXT**

Sau 195, còn một vấn đề rất quan trọng cần khóa:

> **Khi Axiom tạo ra một executable, chính xác cái gì chạy trước `main()` và cái gì được phép tồn tại trong binary?**

Axiom đã quyết định **không có monolithic runtime**, nhưng cần hoàn thiện cơ chế composition.

Kiến trúc dự kiến:

```text
Executable
│
├── Program
│
├── Startup
│
├── Allocator        [optional]
├── Panic            [optional]
├── Unwind           [optional]
├── Thread           [optional]
├── TLS              [optional]
├── Async            [optional]
├── Reflection       [optional]
├── Unicode          [optional]
├── IO               [optional]
└── Platform         [optional]
```

Cần chốt tiếp:

- `main()` thực sự được hạ xuống thế nào.
- runtime component dependency graph.
- startup ABI.
- allocator bootstrap.
- TLS initialization.
- thread initialization.
- panic initialization.
- async runtime loading.
- freestanding `no_std`/không runtime tương đương.
- kernel/embedded mode.
- static constructor policy.
- runtime component dead stripping.
- `crt0`/OS startup interaction.
- process exit.
- thread exit.
- `atexit` tương đương có hay không.
- runtime initialization ordering.
- runtime component versioning.
- runtime ABI.
- cách một chương trình cực nhỏ có thể tạo binary chỉ vài KB mà không kéo theo cả runtime.

**Điểm cần giữ rất chặt:** Runtime của Axiom phải là **composition của các capability cần thiết**, không được quay trở lại thành một “Axiom Runtime” khổng lồ mà mọi chương trình đều phải link.