# BOOTSTRAP-420 — MACHINE CODE ENCODER, OBJECT FORMAT & NATIVE ARTIFACT EMISSION

**Trạng thái:** SPECIFIED / FROZEN  
**Phụ thuộc:** 418 LIR, 419 Machine IR, 417 ABI

Mục tiêu của 420 là hoàn thiện phần **compiler backend tạo ra file nhị phân thật**:

```text
Machine IR
    ↓
Instruction Encoder
    ↓
Machine Bytes + Relocations
    ↓
Object Writer
    ↓
ELF / PE-COFF / Mach-O / WASM
```

Đây là bước rất quan trọng đối với mục tiêu Axiom **không phụ thuộc assembler/compiler bên thứ ba**.

---

## 420.1. Encoder phải là một compiler component

Không:

```text
Axiom
 ↓
.asm
 ↓
external assembler
 ↓
.o
```

Mà:

```text
Axiom
 ↓
Machine IR
 ↓
Axiom Machine Encoder
 ↓
Object
```

Assembler textual trở thành **tool tùy chọn**, không phải dependency.

---

# 420.2. Encoder Input

Encoder nhận:

```text
MachineModule {
    target
    functions
    globals
    sections
    symbols
    relocations
    debug_info
    unwind_info
}
```

và tạo:

```text
EncodedModule {
    sections
    symbols
    relocations
    debug
    unwind
}
```

---

# 420.3. Instruction Encoding

Mỗi instruction được biến thành:

```text
Instruction
    ↓
opcode encoding
operand encoding
prefix
modrm/sib
immediate
displacement
```

tùy ISA.

Compiler phải validate toàn bộ trước khi emit.

---

# 420.4. Encoder không được “đoán”

Ví dụ Machine IR:

```text
ADD64 rax, rbx
```

Encoder không được tự sửa thành instruction khác nếu Machine IR đã được legalize.

Nếu operand không hợp lệ:

```text
MachineEncodingError
```

Điều này giúp tách:

```text
Instruction Selection
```

khỏi:

```text
Instruction Encoding
```

---

# 420.5. Encoder Contract

Invariant:

```text
Decode(Encode(I)) == I
```

ở mức semantic machine instruction.

Không nhất thiết byte sequence phải duy nhất nếu ISA cho phép nhiều encoding tương đương, nhưng encoder phải deterministic theo canonical encoding policy.

---

# 420.6. Canonical Encoding

Nếu một instruction có nhiều encoding:

```text
encoding A
encoding B
```

Axiom chọn một canonical form mặc định.

Lợi ích:

- reproducible build;
- binary diff ổn định;
- cache tốt;
- compiler testing dễ;
- AI có thể phân tích deterministic.

---

# 420.7. Relocation

Không phải mọi địa chỉ đều biết tại thời điểm compile.

Ví dụ:

```text
call external_function
```

compiler chưa biết địa chỉ cuối cùng.

Machine code chứa:

```text
placeholder
```

và:

```text
Relocation {
    offset
    symbol
    kind
    addend
}
```

---

# 420.8. Relocation Types

Khái niệm chung:

```text
ABS
PC_REL
GOT
PLT
TLS
SECTION
IMPORT
EXPORT
```

Backend target ánh xạ sang relocation thực tế.

---

# 420.9. PC-relative

Ví dụ:

```text
call foo
```

có thể encode:

```text
relative displacement
```

thay vì absolute address.

Đây là cơ sở cho:

- PIE;
- shared libraries;
- position-independent code.

---

# 420.10. Symbol

Mỗi symbol:

```text
Symbol {
    name
    kind
    binding
    visibility
    section
    offset
    size
}
```

Kind:

```text
FUNCTION
DATA
TLS
IMPORT
EXPORT
SECTION
ABSOLUTE
```

---

# 420.11. Symbol Identity

Tên symbol textual không phải identity duy nhất.

Compiler nội bộ dùng:

```text
SymbolId
```

sau đó object writer tạo external symbol name.

Điều này tránh collision giữa:

```text
package_a::foo
package_b::foo
```

---

# 420.12. Name Mangling

Axiom cần deterministic mangling cho symbol không export.

Ví dụ conceptually:

```text
_axiom$package$module$function$hash
```

Hash phải phụ thuộc semantic identity chứ không phụ thuộc đường dẫn tạm thời.

---

# 420.13. Public Symbol

`public fn` cần ABI-stable external naming theo export policy.

Có thể:

```text
@export("foo")
```

để kiểm soát tên symbol.

Nếu không:

```text
Axiom ABI mangled name
```

---

# 420.14. `extern`

FFI declaration:

```text
extern "C" fn printf(...)
```

sẽ tạo:

```text
IMPORT symbol
```

hoặc unresolved external reference.

Compiler không cần biết implementation nằm ở đâu.

---

# 420.15. Static Library

Axiom Object Writer có thể tạo:

```text
libfoo.a
foo.lib
```

tùy target.

Static library về bản chất là archive của object files + symbol index.

Axiom có thể tự tạo archive.

---

# 420.16. Dynamic Library

Có thể tạo:

```text
.so
.dll
.dylib
```

với:

- export table;
- import table;
- relocation;
- dynamic symbol table;
- TLS;
- unwind;
- metadata.

---

# 420.17. Section Model

Axiom internal sections:

```text
.text
.rodata
.data
.bss
.tdata
.tbss
.debug_*
.unwind
```

Tên thực tế target-dependent.

---

# 420.18. Section Properties

Mỗi section:

```text
Section {
    name
    flags
    alignment
    data
    virtual_size
    file_size
}
```

Flags:

```text
READ
WRITE
EXECUTE
ALLOC
TLS
DEBUG
```

Compiler không được tạo section vừa:

```text
WRITE + EXECUTE
```

trừ khi explicit unsafe/system policy cho phép.

---

# 420.19. `.bss`

Zero-initialized storage không cần chứa toàn bộ zero bytes trong file.

Object writer có thể biểu diễn:

```text
virtual size
file size = 0
```

giúp binary nhỏ.

---

# 420.20. Constant Deduplication

Các constants giống nhau có thể merge:

```text
"hello"
"hello"
```

thành một storage object nếu identity không observable.

Nếu địa chỉ bị expose và identity observable:

```text
không được merge tùy tiện.
```

---

# 420.21. Function Deduplication

Hai instantiation generic giống hệt machine representation có thể share implementation nếu semantic/ABI conditions cho phép.

Ví dụ:

```text
foo<i32>
foo<u32>
```

không nhất thiết share.

Compiler chỉ share khi semantics và representation tương thích.

---

# 420.22. Identical Code Folding

Các functions có machine behavior giống nhau có thể merge.

Nhưng phải kiểm tra:

```text
function address observable?
debug identity?
profiling identity?
ABI/export?
```

Nếu address identity observable:

```text
không merge.
```

---

# 420.23. Dead Code Elimination ở Object Level

Nếu symbol không reachable:

```text
unused function
```

có thể loại bỏ.

Nhưng phải bảo vệ:

```text
export
FFI
reflection
dynamic lookup
linker entry
startup
registration
```

---

# 420.24. Entry Point

Executable cần entry:

```text
main
```

nhưng native startup thực tế có thể là:

```text
OS loader
 ↓
runtime startup
 ↓
Axiom entry
```

hoặc freestanding:

```text
OS/firmware
 ↓
Axiom entry
```

Axiom không ép mọi chương trình có cùng startup runtime.

---

# 420.25. Hosted Executable

Ví dụ:

```text
main() -> i32
```

Compiler có thể generate startup shim:

```text
OS
 ↓
CRT/OS entry
 ↓
Axiom startup
 ↓
main
 ↓
exit
```

Nhưng shim chỉ link các capability cần thiết.

---

# 420.26. Freestanding

Freestanding:

```text
@freestanding
fn kernel_entry(...) { ... }
```

có thể không có:

- libc;
- CRT;
- allocator;
- exception runtime;
- thread runtime.

Compiler chỉ emit object + metadata cần thiết.

---

# 420.27. PE/COFF Backend

Axiom phải có native writer cho:

```text
PE
COFF
```

Các thành phần chính:

```text
DOS header / PE header
COFF file header
section table
section data
symbol/import/export metadata
relocations
debug data
unwind data
```

---

# 420.28. ELF Backend

ELF writer:

```text
ELF header
program headers
section headers
sections
symbols
relocations
dynamic metadata
TLS
debug/unwind
```

Phải hỗ trợ tối thiểu:

```text
ELF32
ELF64
```

khi target yêu cầu.

---

# 420.29. Mach-O Backend

Mach-O writer cần:

```text
Mach header
load commands
segments
sections
symbols
relocations
exports
imports
TLS
unwind
code signatures
```

iOS/macOS có thêm platform-specific constraints.

---

# 420.30. WASM Backend

WASM khác native object format.

Axiom có thể emit:

```text
.wasm
```

với:

```text
type section
import section
function section
table
memory
global
export
code
data
custom sections
```

Machine IR backend cho WASM không cần giả lập register machine.

---

# 420.31. Object Format ≠ Linker

Object writer chỉ tạo:

```text
.o
.obj
```

Linker xử lý:

```text
objects
libraries
relocations
symbol resolution
layout
imports/exports
final executable
```

Hai component phải tách.

---

# 420.32. Axiom Linker

Đây sẽ là bước kế tiếp sau object writer.

Kiến trúc:

```text
Object Writer
      ↓
  Axiom Object
      ↓
 Axiom Linker
      ↓
Executable / Shared Library
```

Không cần external linker trong final toolchain.

---

# 420.33. Debug Information

Object writer phải giữ:

```text
SourceLocation
Function
Variable
Type
InlineSite
MachineInstruction
```

mapping.

Ví dụ:

```text
machine offset 0x1240
      ↓
LIR instruction
      ↓
MIR operation
      ↓
source line 37
```

---

# 420.34. DWARF

ELF target có thể emit DWARF.

Axiom internal debug model không nên phụ thuộc trực tiếp vào DWARF.

```text
Axiom Debug IR
      ↓
DWARF writer
```

---

# 420.35. PDB

Windows có thể cần:

```text
PDB
```

Axiom nên có:

```text
Axiom Debug IR
      ↓
PDB writer
```

thay vì compiler frontend biết PDB.

---

# 420.36. Unwind Information

Compiler phải emit unwind metadata khi target/profile yêu cầu.

Ví dụ concept:

```text
function
 ↓
prologue description
 ↓
stack/register recovery rules
```

Dùng cho:

- exception unwind;
- debugger;
- stack walking;
- profiler.

---

# 420.37. Unwind và Abort

Nếu:

```text
panic = abort
```

không cần full exception unwind metadata chỉ vì Axiom có Drop.

Đây là một lợi ích lớn của:

```text
deterministic Drop + configurable panic model
```

---

# 420.38. Code Signing Boundary

Code signing không thuộc Machine Encoder.

Architecture:

```text
Compiler
 ↓
Object
 ↓
Linker
 ↓
Final Binary
 ↓
Platform Signer
```

Có thể tích hợp Axiom signing tool sau này.

---

# 420.39. Binary Layout

Linker quyết định:

```text
text address
rodata address
data address
bss address
TLS address
alignment
padding
segment permissions
```

Object writer chỉ mô tả section.

---

# 420.40. Alignment

Object writer phải giữ:

```text
section alignment
symbol alignment
data alignment
TLS alignment
```

Không được giảm alignment đã được semantic/ABI proof yêu cầu.

---

# 420.41. Relocation Overflow

Nếu relocation không đủ range:

```text
PC-relative displacement overflow
```

linker không được silently truncate.

Có thể:

```text
relaxation
veneer/thunk
different code sequence
```

hoặc báo lỗi.

---

# 420.42. Linker Relaxation

Một số target hỗ trợ:

```text
long sequence
      ↓
short sequence
```

khi layout cuối cùng đã biết.

Ví dụ:

```text
long branch
      ↓
short branch
```

Axiom linker/backend có thể làm relaxation.

---

# 420.43. Position Independent Code

Compiler target options:

```text
PIC
PIE
static
```

được đưa vào BuildDB/TargetDB.

Không phải source language semantics.

---

# 420.44. ASLR Compatibility

PIE/PIC giúp executable/library có thể chạy tại địa chỉ thay đổi.

Compiler không expose địa chỉ tuyệt đối trừ khi required.

---

# 420.45. Section Garbage Collection

Linker có thể loại bỏ sections không reachable.

Graph:

```text
entry
 ↓
function A
 ↓
function B
```

Nếu:

```text
function C
```

không reachable và không exported:

```text
C → eliminate
```

---

# 420.46. COMDAT / Weak / Alias

Object/linker model cần hỗ trợ target tương ứng:

```text
WEAK
COMDAT
ALIAS
MERGE
```

để generic/template/generated code không gây duplicate symbol.

---

# 420.47. Generic Monomorphization và Linker

Generic instantiations có thể được emit nhiều compilation units.

Linker cần xử lý:

```text
duplicate equivalent instantiation
```

mà không tạo nhiều implementation cuối cùng nếu policy cho phép.

---

# 420.48. Incremental Linking

BuildDB có thể cache:

```text
object
relocation state
link graph
symbol index
```

Khi chỉ một module thay đổi:

```text
unchanged objects
      ↓
reuse
```

---

# 420.49. Deterministic Binary

Build identity phải kiểm soát:

```text
timestamp
random IDs
UUID
section ordering
symbol ordering
padding
build paths
debug paths
```

Nếu reproducible profile bật:

```text
same inputs → same binary
```

---

# 420.50. Binary Size Optimization

Axiom có thể hỗ trợ:

```text
-Osize
```

với:

- section GC;
- constant merging;
- function outlining;
- instruction-size selection;
- string dedup;
- relocation optimization;
- symbol stripping.

---

# 420.51. Tiny Binary Mode

Có thể có profile:

```text
-freestanding
-Osize
-no-debug
-no-unwind
-no-reflection
-no-runtime
```

để tạo binary cực nhỏ.

Nhưng compiler không được hy sinh semantics chỉ để giảm size.

---

# 420.52. Compiler Artifact Pipeline

Hoàn chỉnh:

```text
Source
 ↓
Verified MIR
 ↓
Optimized MIR
 ↓
ABI MIR
 ↓
LIR
 ↓
Machine IR
 ↓
Register Allocation
 ↓
Instruction Scheduling
 ↓
Machine Encoding
 ↓
Axiom Object
 ↓
Axiom Linker
 ↓
Native Artifact
```

---

# 420.53. CompilerDB additions

Thêm:

```text
EncoderDB
InstructionEncodingDB
RelocationDB
SymbolDB
SectionDB
ObjectDB
ELFDB
PECOFFDB
MachODB
WasmObjectDB
DebugObjectDB
UnwindDB
BinaryLayoutDB
ArtifactDB
```

---

# 420.54. Proofs

```text
EncodingProof
RelocationProof
SymbolResolutionProof
SectionLayoutProof
ObjectFormatProof
DebugMappingProof
UnwindProof
BinaryLayoutProof
ReproducibleArtifactProof
ArtifactIntegrityProof
```

---

# 420.55. Invariants `AOBJ`

```text id="r3f4f6"
AOBJ-01  Every emitted instruction is valid for the target ISA.
AOBJ-02  Every encoded operand matches its Machine IR operand.
AOBJ-03  Encoding preserves Machine IR semantics.
AOBJ-04  Encoding is deterministic.
AOBJ-05  Every unresolved address requiring relocation has a relocation entry.
AOBJ-06  Every relocation references a valid symbol.
AOBJ-07  Relocation kind matches target ABI/object format.
AOBJ-08  Relocation overflow is never silently truncated.
AOBJ-09  Every symbol has a valid identity and binding.
AOBJ-10  Symbol visibility is preserved.
AOBJ-11  Section permissions are valid.
AOBJ-12  Required section alignment is preserved.
AOBJ-13  TLS objects are emitted with valid TLS semantics.
AOBJ-14  Import/export metadata matches ABI declarations.
AOBJ-15  Debug mappings reference valid machine ranges.
AOBJ-16  Unwind metadata matches generated prologue/epilogue.
AOBJ-17  Object format structures are internally consistent.
AOBJ-18  No unresolved semantic entity reaches object emission.
AOBJ-19  Dead-section elimination preserves observable entry points.
AOBJ-20  Exported symbols cannot be removed as dead code.
AOBJ-21  FFI symbols preserve their declared ABI.
AOBJ-22  Generic deduplication cannot merge semantically distinct entities.
AOBJ-23  Constant merging preserves observable identity semantics.
AOBJ-24  Function merging preserves observable address identity semantics.
AOBJ-25  Reproducible builds do not contain uncontrolled timestamps/randomness.
AOBJ-26  Object files can be validated independently of the frontend.
AOBJ-27  Final section layout satisfies target constraints.
AOBJ-28  Native artifact metadata matches the selected target.
AOBJ-29  Encoder errors are diagnosed before corrupted object emission.
AOBJ-30  Object emission cannot alter verified program semantics.
```

---

# 420.56. Kết quả kiến trúc

Sau 420, Axiom đã có đầy đủ conceptual path:

```text
                 Axiom Compiler
                       │
                       ▼
                  Verified MIR
                       │
                       ▼
                  Axiom LIR
                       │
                       ▼
                 Machine IR
                       │
                       ▼
              Register Allocation
                       │
                       ▼
             Instruction Selection
                       │
                       ▼
              Machine Encoding
                       │
                       ▼
                 Object Writer
              ┌────────┼────────┐
              ▼        ▼        ▼
             ELF      PE      Mach-O
              │        │        │
              └────────┼────────┘
                       ▼
                  Axiom Linker
                       │
                       ▼
                 Native Binary
```

Điểm đặc biệt quan trọng:

**Axiom không cần LLVM để tồn tại về mặt kiến trúc.**

LLVM có thể được sử dụng ở **giai đoạn bootstrap đầu tiên** để nhanh chóng có compiler chạy được, nhưng compiler cuối cùng có thể thay thế từng lớp:

```text
LLVM backend
    ↓
Axiom LIR
    ↓
Axiom Machine IR
    ↓
Axiom Encoder
    ↓
Axiom Object Writer
    ↓
Axiom Linker
```

Và khi Axiom compiler được viết bằng chính Axiom:

```text
Axiom compiler
     ↓
Axiom compiler
     ↓
Axiom compiler
```

thì hệ thống đạt được mục tiêu **self-hosting thực sự**, không phải chỉ là một frontend Axiom đặt trên LLVM.

**BOOTSTRAP-420 — SPECIFIED / FROZEN.**