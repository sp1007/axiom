Tiếp tục với **OBJECT-002 — Native Object Writer hoàn chỉnh**.

Đây là tầng biến:

```text id="8zj4k1"
Machine Bytes
    ↓
Encoded Sections
    ↓
Object Writer
    ↓
.o / .obj / Mach-O object / .wasm
```

Mục tiêu của Axiom vẫn giữ nguyên:

> **Không cần assembler bên ngoài để tạo object file.**

---

# OBJECT-002 — Native Object Writer

## 1. Kiến trúc tổng thể

```text id="2h7m9q"
Physical Machine IR
        ↓
Machine Encoder
        ↓
EncodedFunction / EncodedData
        ↓
Object Builder
        │
        ├── Sections
        ├── Symbols
        ├── Relocations
        ├── COMDAT
        ├── TLS
        ├── Debug
        ├── Unwind
        └── Metadata
        ↓
Object Writer
        │
        ├── ELF
        ├── COFF
        ├── Mach-O
        └── WASM
        ↓
Object File
```

Object Writer **không biết semantics của Axiom**.

Nó chỉ biết:

- bytes;
- section;
- symbol;
- relocation;
- alignment;
- object format;
- target ABI metadata.

---

# 2. Object IR

Không nên để compiler backend ghi ELF trực tiếp.

Ta cần một **Object IR** trung gian.

```text id="q8k2m5"
Machine Encoder
      ↓
Generic Object IR
      ↓
ELF Writer
COFF Writer
MachO Writer
WASM Writer
```

Điều này cực kỳ quan trọng.

Ví dụ cùng một function:

```text id="v3m7x1"
Object IR:
    section = .text
    offset = 128
    symbol = foo
    size = 42
```

sau đó:

```text id="h4n9q2"
ELF:
    .text
    .symtab
    .strtab
    .rela.text
```

hoặc:

```text id="p6w2c8"
Mach-O:
    __TEXT,__text
    LC_SYMTAB
    relocation records
```

---

# 3. Object IR chính thức

Đề xuất:

```text id="x9k3m7"
ObjectFile {
    target
    sections[]
    symbols[]
    relocations[]
    comdats[]
    debug
    unwind
    metadata
}
```

### Section

```text id="a4q8n2"
ObjectSection {
    id
    name
    kind
    flags
    alignment
    data
    fragments[]
}
```

### Symbol

```text id="r7m2v5"
ObjectSymbol {
    id
    name
    binding
    visibility
    kind
    section
    offset
    size
    weak
    comdat
}
```

### Relocation

```text id="c8p4y1"
ObjectRelocation {
    section
    offset
    kind
    symbol
    addend
}
```

---

# 4. Section model

Không hard-code chỉ:

```text
.text
.data
.bss
```

Axiom nên có generic section kinds:

```text id="m2x7q9"
Text
ReadOnlyData
Data
ZeroFill
TLSData
TLSZeroFill
Debug
Unwind
Metadata
LinkerMetadata
Custom
```

Sau đó target/object format map sang tên cụ thể.

---

# 5. Section flags

Đã có:

```text id="g5n1z8"
ALLOC
EXEC
WRITE
READONLY
TLS
ZERO_FILL
MERGE
DEBUG
DISCARDABLE
```

Có thể bổ sung:

```text id="u3k6p2"
CODE
CONST
NOLOAD
COMDAT
GROUP
LARGE
LINKER_ONLY
```

Nhưng không nên biến ELF/COFF-specific flags thành generic semantics nếu không cần.

---

# 6. Section identity

Không dùng section name làm identity.

Ví dụ:

```text id="f2m8q4"
.text.foo
.text.bar
```

có thể merge.

Do đó:

```text id="w7c3n9"
SectionId
```

là identity thật.

Tên chỉ là metadata/object-format representation.

---

# 7. Fragment model

Thay vì build section bằng cách nối byte ngay lập tức:

```text id="z6q1m4"
Section {
    fragments[]
}
```

Ví dụ:

```text id="v8n2c5"
.text
 ├── Function foo
 ├── Function bar
 ├── alignment
 └── Function baz
```

Điều này giúp:

- symbol offsets;
- COMDAT;
- section GC;
- hot/cold;
- linker metadata.

---

# 8. Fragment

```text id="k4p9x2"
SectionFragment {
    id
    offset
    alignment
    size
    contents
    symbol_refs[]
    relocations[]
    comdat
}
```

Function:

```text id="q2m7v8"
FunctionFragment
```

constant:

```text id="n5c1x4"
DataFragment
```

---

# 9. `.text`

Ví dụ:

```text id="d8q3m6"
.text:
    foo bytes
    padding
    bar bytes
```

Symbols:

```text id="f7x2p9"
foo → offset 0
bar → offset 64
```

Relocation:

```text id="c3m8v1"
offset 12 → foo_external
```

Object writer tính offset cuối cùng.

---

# 10. `.rodata`

Ví dụ:

```text id="p1n6q4"
const message = "Hello"
```

có thể:

```text id="7m4x9c"
.rodata:
    48 65 6c 6c 6f
```

Symbol nếu cần:

```text id="s8q2m5"
message
```

Nếu constant không cần symbol, có thể không export symbol.

---

# 11. `.data`

Mutable initialized data:

```text id="a3m7q1"
var global_counter: i32 = 10
```

→ `.data`.

---

# 12. `.bss`

Zero-initialized data:

```text id="v5x9p2"
var buffer: [4096]u8 = zero
```

không cần ghi 4096 zero bytes vào object.

Object IR:

```text id="j4n8c6"
ZeroFill {
    size = 4096
    alignment = ...
}
```

ELF writer biến thành NOBITS.

COFF/Mach-O map tương ứng.

---

# 13. TLS

Thread-local:

```text id="z2m6q8"
thread_local var x: i32
```

không phải `.data` thông thường.

Object IR:

```text id="r9c3v5"
TLSData
TLSZeroFill
```

Relocation TLS cũng target-specific.

---

# 14. Symbol model

Symbol cần phân biệt:

```text id="k6x2m9"
Local
Global
Weak
Undefined
Absolute
Section
TLS
File
Debug
```

Generic:

```text id="p3v8q1"
SymbolBinding {
    Local
    Global
    Weak
}
```

```text id="m7n4c2"
SymbolVisibility {
    Default
    Hidden
    Protected
    Internal
}
```

Object format sẽ map nếu hỗ trợ.

---

# 15. Symbol kind

```text id="x8q5m1"
SymbolKind =
    Function
    Object
    TLS
    Section
    Absolute
    Undefined
    File
    Debug
```

---

# 16. Symbol naming

Axiom có:

```text id="c7m2p9"
Axiom mangling
```

Ví dụ concept:

```text id="9k3x6v"
_axiom_foo...
```

Không nên lấy source spelling làm symbol trực tiếp trong mọi trường hợp.

Mangler phải deterministic.

---

# 17. `@export`

Nếu:

```text id="h4p8n2"
@export("my_function")
fn foo() ...
```

symbol:

```text id="v7c1m5"
my_function
```

không dùng Axiom mangled name.

Đây rất quan trọng cho FFI.

---

# 18. Symbol visibility

Private Axiom function:

```text id="q9m2x6"
local/internal
```

public function:

```text id="r4p7c1"
global/exported
```

Nhưng:

> `pub` trong source và symbol visibility không hoàn toàn đồng nghĩa.

Một symbol có thể public trong module nhưng không export khỏi binary.

Object/link policy quyết định cuối.

---

# 19. COMDAT / LinkOnce

Generic object IR cần:

```text id="n5x8q3"
ComdatGroup {
    id
    selection
    members[]
}
```

Dùng cho:

- generic monomorphization;
- inline functions;
- template-like generated code;
- duplicate compiler-generated helpers.

Ví dụ:

```text id="j2m6v9"
foo<i32>
foo<i64>
```

Nếu hai compilation units generate cùng function:

```text id="s7q1c4"
linker có thể giữ một bản
```

---

# 20. Generic code deduplication

Axiom đã quyết định:

> Monomorphization trước, linker COMDAT/ICF để giảm duplication.

Object writer phải vì thế hỗ trợ:

```text id="w3n8p6"
COMDAT
weak/linkonce
section groups
```

theo target.

---

# 21. Section groups

ELF dùng section groups.

COFF có COMDAT section.

Mach-O có cơ chế tương ứng khác.

Object IR không nên expose trực tiếp:

```text id="m1x7q4"
ELF SHT_GROUP
```

mà:

```text id="g6c2p9"
ComdatGroup
```

---

# 22. Relocation model

Object IR:

```text id="r5n9x3"
Relocation {
    section
    offset
    type
    symbol
    addend
}
```

Nhưng `type` generic:

```text id="q8m4c1"
RelocKind =
    Absolute
    PcRelative
    Got
    Plt
    Tls
    SectionRelative
    Relative
    TargetSpecific(...)
```

Object writer map sang format-specific number.

---

# 23. ELF relocation

Ví dụ x86-64:

```text id="y3p7m2"
R_X86_64_PC32
R_X86_64_PLT32
R_X86_64_64
R_X86_64_GOTPCREL
```

Axiom không hard-code những số này trong compiler IR.

ELF backend có:

```text id="h8c2v5"
ElfRelocationTable
```

---

# 24. COFF relocation

Windows:

```text id="b4m9x7"
IMAGE_REL_AMD64_REL32
IMAGE_REL_AMD64_ADDR64
```

Object writer map:

```text id="p6q1n8"
PcRelative
```

→ COFF relocation tương ứng.

---

# 25. Mach-O relocation

Mach-O có relocation model khác ELF/COFF.

Generic Object IR giúp tránh:

```text id="k3v7m1"
if mach_o ...
if elf ...
if coff ...
```

rải khắp compiler.

Chỉ Mach-O writer biết representation.

---

# 26. Relocation overflow

Ví dụ:

```text id="c9m2x5"
PC-relative 32-bit
```

nhưng symbol quá xa.

Object writer phải:

```text id="r7q3p1"
diagnose relocation overflow
```

Không:

```text id="n4v8c6"
truncate
```

---

# 27. Addend

Axiom cần hỗ trợ:

```text id="z2p6m8"
Relocation {
    addend
}
```

Vì ELF có REL/RELA distinction.

Generic object model không cần biết REL hay RELA.

Writer quyết định.

---

# 28. Section alignment

Section:

```text id="m8x3q1"
.text align=16
.rodata align=8
.data align=8
```

Object writer phải giữ:

```text id="p5n7c2"
alignment
```

nhưng không cần tự quyết định function alignment.

Layout engine đã xác định.

---

# 29. Symbol offsets

Một symbol trong section:

```text id="q4m9x6"
foo:
    section = .text
    offset = 128
    size = 43
```

Nếu function layout thay đổi:

```text id="j7c2n5"
offset
```

phải cập nhật trước object emission.

---

# 30. Undefined symbols

Ví dụ:

```text id="x5p8m3"
extern fn printf(...)
```

object:

```text id="w2n6q9"
symbol printf:
    binding = Global
    section = Undefined
```

Relocation trỏ đến symbol đó.

Linker sau này giải quyết.

---

# 31. Weak symbols

Axiom nên hỗ trợ:

```text id="v3q7m1"
@weak
```

ở system layer nếu cần.

Object IR:

```text id="h8m2c5"
binding = Weak
```

Linker semantics:

- strong thắng weak;
- nhiều weak có thể merge tùy format/policy.

---

# 32. Static library

Static library thực chất không cần compiler-specific format mới.

Ví dụ:

```text id="p4x9m6"
libfoo.a
```

chứa:

```text id="j2n7c3"
foo.o
bar.o
baz.o
```

Axiom linker sẽ đọc archive.

Axiom toolchain có thể tự tạo archive:

```text id="c6m1q8"
axiom archive
```

hoặc:

```text id="8y0q2m"
axiom build --static-lib
```

---

# 33. Archive format

ELF ecosystem thường dùng:

```text id="x3m8p5"
ar
```

Axiom không cần phụ thuộc `ar`.

Có thể implement:

```text id="k7q2n4"
ArchiveWriter
ArchiveReader
```

cho Unix archive format.

Windows có archive COFF tương ứng.

---

# 34. Debug information

Object Writer không tạo semantic debug info từ source.

Compiler đã có:

```text id="n5c9x2"
DebugInfo IR
```

Object writer chỉ serialize.

Ví dụ:

```text id="r8m1q6"
DWARF
CodeView
```

---

# 35. Debug IR

Để không gắn compiler với DWARF:

```text id="q3v7m9"
DebugInfo {
    files
    source_locations
    types
    functions
    variables
    scopes
    line_tables
    locations
}
```

ELF:

```text id="m4x8p2"
→ DWARF
```

COFF/PE:

```text id="c7n2q5"
→ CodeView/PDB metadata
```

Mach-O:

```text id="v1m6x9"
→ DWARF
```

---

# 36. Unwind

Tương tự:

```text id="j5p9c3"
UnwindInfo {
    functions[]
    CFA rules
    saved registers
    ranges
}
```

ELF:

```text id="n8q2m4"
→ .eh_frame / .eh_frame_hdr
```

Windows:

```text id="x6v1p7"
→ .pdata / .xdata
```

Axiom không để backend trực tiếp emit `.eh_frame`.

---

# 37. Panic=abort

Nếu:

```text id="c2m7x8"
panic=abort
```

thì không cần tạo full unwind metadata chỉ vì Axiom có `Drop`.

Đây rất quan trọng cho binary nhỏ.

---

# 38. Panic=unwind

Nếu:

```text id="r4q9n1"
panic=unwind
```

thì object writer nhận:

```text id="m8x3p5"
UnwindInfo
```

và serialize theo target.

---

# 39. Runtime-free object

Một function đơn giản:

```text id="y7m2c4"
fn add(...) ...
```

không nên kéo theo:

```text id="j3n8q6"
runtime.o
panic.o
allocator.o
thread.o
```

Object writer chỉ ghi những gì compiler thực sự tạo.

Đây tiếp tục nguyên tắc:

> **Demand-driven runtime.**

---

# 40. Runtime helper

Nếu codegen cần:

```text id="p5x1m7"
128-bit division helper
```

thì compiler có thể tạo reference:

```text id="n9q4c2"
__axiom_i128_div
```

Object có undefined symbol hoặc generated helper section.

Linker/build system quyết định include helper.

Không mặc định link toàn bộ runtime.

---

# 41. Object metadata

Có thể cần metadata riêng:

```text id="x2m8v6"
AxiomObjectMetadata {
    compiler_version
    target
    ABI
    language_version
    feature_set
    build_id
}
```

Nhưng **không nên bắt buộc** trong native object nếu làm binary lớn.

Có thể chỉ emit khi:

```text id="q7c3p9"
debug
reproducibility
incremental compilation
link diagnostics
```

được bật.

---

# 42. `.axobj`

Axiom có thể có format nội bộ:

```text id="k5n1x8"
.axobj
```

nhưng cần phân biệt:

### Native object

```text id="r8m3q2"
.o
.obj
```

### Compiler semantic artifact

```text id="v4c7m9"
.axm
```

### Optional Axiom object

```text id="p2x6n5"
.axobj
```

Tôi đề xuất:

> **Không cần `.axobj` trong MVP.**

`.axm` chứa semantic/incremental information.

Native object dùng ELF/COFF/Mach-O/WASM.

Như vậy hệ thống đơn giản hơn.

---

# 43. Deterministic object generation

Cùng:

```text id="n7m2q8"
Machine bytes
symbols
relocations
target
```

phải tạo object giống nhau byte-for-byte nếu deterministic build bật.

Phải tránh:

- random IDs;
- timestamp;
- host path ngẫu nhiên;
- unordered hash-map serialization;
- compiler memory address.

---

# 44. Reproducible build

Nếu:

```text id="x1p8m4"
reproducible=true
```

thì object không chứa:

```text id="f6c2n9"
current time
random UUID
absolute temporary path
```

trừ khi explicit input.

Path có thể canonicalize/map:

```text id="q9m3v7"
source path remapping
```

---

# 45. Object verifier

Axiom nên có:

```text id="m8x2c5"
ObjectVerifier
```

kiểm tra:

### Sections

```text id="a3n7q1"
valid alignment
valid flags
valid size
```

### Symbols

```text id="v5p9m2"
section exists
offset valid
size valid
binding valid
```

### Relocations

```text id="j1x6c8"
offset valid
symbol exists
relocation compatible
```

### COMDAT

```text id="r4m8q2"
groups valid
members exist
```

### Target

```text id="n7c3p5"
target matches object format
```

---

# 46. ELF writer

Cấu trúc:

```text id="q2m7x9"
ELF Header
Program-related metadata if required
Section contents
Section Headers
String Tables
Symbol Tables
Relocation Sections
Debug Sections
```

Nhưng cần phân biệt:

> Object `.o` không phải executable ELF.

`.o` thường không cần final program headers.

Executable sẽ do linker tạo.

---

# 47. ELF sections

Ví dụ:

```text id="j5n8c2"
.text
.rodata
.data
.bss
.tdata
.tbss
.symtab
.strtab
.shstrtab
.rela.text
.rela.data
.debug_*
.eh_frame
```

Axiom writer tạo đúng theo Object IR.

---

# 48. ELF section ordering

Không nên dựa vào hash map iteration.

Định nghĩa thứ tự deterministic:

```text id="v3m6q8"
.text
.rodata
.data
.bss
.tdata
.tbss
...
```

hoặc stable topological ordering.

---

# 49. COFF/PE object

COFF object:

```text id="p8x2m4"
COFF Header
Section Table
Raw Section Data
Relocations
Symbol Table
String Table
```

PE executable sẽ do linker tạo.

---

# 50. Mach-O object

Mach-O object:

```text id="c5m9q1"
Mach-O Header
Load Commands
Segments/Sections
Symbols
Relocations
Debug
```

Axiom phải tạo đúng target architecture:

```text id="w2n7x6"
arm64
x86_64
```

---

# 51. WASM

WASM khác hoàn toàn.

Không phải traditional object file.

Có:

```text id="m7q3p1"
Type Section
Import Section
Function Section
Table
Memory
Global
Export
Code
Data
Custom
```

Axiom có thể coi `.wasm` là **final module format**, không phải intermediate object giống ELF `.o`.

Do đó:

```text id="x4n8c2"
WasmWriter
```

có thể trực tiếp tạo module.

---

# 52. WASM relocation

Nếu hỗ trợ relocatable WASM:

```text id="q9m5v3"
linking custom section
reloc.*
```

thì Object IR có thể mở rộng.

Nhưng MVP:

> **Axiom → final WASM module** đơn giản hơn Axiom → wasm object → wasm linker.

---

# 53. Object Writer API

Đề xuất:

```text id="f3x7m2"
ObjectWriter {
    begin(target)
    create_section(...)
    append_fragment(...)
    define_symbol(...)
    declare_symbol(...)
    add_relocation(...)
    add_comdat(...)
    add_debug(...)
    add_unwind(...)
    finalize()
}
```

Target-specific writer implement interface này.

---

# 54. Generic Object Builder

Compiler không gọi ELF writer trực tiếp.

```text id="r8c2q6"
ObjectBuilder
    ↓
ObjectFile
    ↓
ObjectWriterFactory(target.object_format)
```

Ví dụ:

```text id="m4n7x1"
x86_64-linux
    → ELFWriter

x86_64-windows
    → COFFWriter

aarch64-macos
    → MachOWriter

wasm32-wasi
    → WasmWriter
```

---

# 55. Native object pipeline hoàn chỉnh

```text id="j6p3v8"
Machine Encoder
      ↓
EncodedInstruction
      ↓
Fixups
      ↓
Object Builder
      ↓
Object IR
      ↓
Object Verifier
      ↓
Format Writer
      ↓
.o / .obj / .wasm
```

---

# 56. Invariants OBJECT-002

Đề xuất tiếp nối:

### AOBJ-35 — Object IR Is Format Independent

Compiler backend không phụ thuộc ELF/COFF/Mach-O.

### AOBJ-36 — Object Writer Does Not Perform Semantic Compilation

Object writer chỉ serialize object representation.

### AOBJ-37 — Sections Have Stable Identity

Section name không phải identity duy nhất.

### AOBJ-38 — Symbols Have Stable Identity

Symbol references không phụ thuộc string lookup בלבד.

### AOBJ-39 — Relocations Are Explicit

Không có unresolved address patch ngầm.

### AOBJ-40 — Relocation Overflow Is Diagnosed

Không truncate.

### AOBJ-41 — COMDAT Semantics Are Explicit

Duplicate generated code có thể được linker xử lý đúng.

### AOBJ-42 — Generic Code Deduplication Is Supported

Monomorphized code có thể dùng COMDAT/linkonce.

### AOBJ-43 — Undefined Symbols Are Valid

External references có thể tồn tại trong object.

### AOBJ-44 — Object Writer Does Not Resolve External Symbols

Symbol resolution thuộc linker.

### AOBJ-45 — Object Writer Preserves ABI Metadata

Calling convention/layout/visibility/relocation information không bị mất.

### AOBJ-46 — Debug Is Optional

Không có debug info nếu profile không yêu cầu.

### AOBJ-47 — Unwind Is Optional

Không có unwind runtime/metadata nếu panic profile không cần.

### AOBJ-48 — Runtime Components Are Demand-Driven

Object writer không tự link runtime.

### AOBJ-49 — Object Generation Is Deterministic

Cùng Object IR → cùng output.

### AOBJ-50 — Object Can Be Independently Verified

Axiom có thể kiểm tra object sau khi tạo.

### AOBJ-51 — Object Format Is Selected By Target

Không suy luận format từ source.

### AOBJ-52 — Native Object Does Not Require External Assembler

Machine bytes đã hoàn chỉnh trước Object Writer.

### AOBJ-53 — Debug Representation Is Abstract

DWARF/CodeView là writer-specific.

### AOBJ-54 — Unwind Representation Is Abstract

`.eh_frame`/`.pdata` là writer-specific.

### AOBJ-55 — TLS Is Explicit

TLS sections/relocations không bị coi là normal data.

### AOBJ-56 — Zero-Fill Is Represented Without Unnecessary Bytes

`.bss`/equivalent không phải chứa hàng MB zero data.

### AOBJ-57 — Object Writer Does Not Know Link Policy

Static/dynamic/import/PIE decisions chủ yếu thuộc linker/build target.

### AOBJ-58 — Object Layout Is Deterministic

Section/symbol/relocation ordering ổn định.

### AOBJ-59 — Object Writer Does Not Require LLVM

LLVM chỉ là bootstrap differential oracle.

### AOBJ-60 — Object Format Backends Are Replaceable

Có thể thêm target/object format mà không thay semantic compiler.

---

# 57. Kiến trúc compiler hiện tại

Đến đây toàn bộ backend đã thành:

```text id="g9m2x5"
                    Axiom Source
                         │
                         ▼
                    Typed HIR
                         │
             Ownership / Capability
                         │
                         ▼
                        MIR
                         │
                   MIR Optimize
                         │
                         ▼
                    ABI / Layout
                         │
                         ▼
                        LIR
                         │
                Target Legalization
                         │
                Instruction Selection
                         │
                         ▼
                    Machine IR
                         │
                Register Allocation
                         │
                 Spill / Reload
                         │
                  Frame Layout
                         │
               Prologue / Epilogue
                         │
                Machine Optimize
                         │
                Machine Verify
                         │
                     Encoding
                         │
                    Object IR
                         │
                 Object Verification
                         │
              ┌──────────┼───────────┐
              ▼          ▼           ▼
             ELF        COFF       Mach-O
                                      │
                                    WASM
```

Và đây là một mốc lớn:

**Axiom đã có kiến trúc compiler đủ để đi từ source code tới native machine bytes và object file mà không cần LLVM/assembler.**

---

# Bước tiếp theo

Giờ phần còn lại không còn là "compiler backend" nữa mà chuyển sang **linker thực sự**.

Bước tiếp theo nên là:

## **LINKER-002 — Axiom Native Linker**

Ta sẽ thiết kế từ:

```text
.o / .obj
   ↓
Object Reader
   ↓
Symbol Resolution
   ↓
Archive Extraction
   ↓
COMDAT / ICF
   ↓
Section GC
   ↓
Section Layout
   ↓
Segment Layout
   ↓
Relocation
   ↓
GOT / PLT / Import
   ↓
TLS
   ↓
Entry Point
   ↓
Startup
   ↓
ELF / PE / Mach-O executable
```

Đặc biệt ở bước đó sẽ phải giải quyết một vấn đề rất quan trọng đối với mục tiêu của Axiom: **làm sao tạo một executable native hoàn chỉnh mà không cần libc, CRT, GNU ld, lld hay linker của Microsoft**, nhưng vẫn hỗ trợ được chương trình hosted bình thường khi người dùng muốn.