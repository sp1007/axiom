# BOOTSTRAP-302 — AXIOM OBJECT FILE WRITER & SECTION/SYMBOL/RELOCATION ENGINE

## 302.1. Mục tiêu

Xây dựng backend biến đầu ra của **BOOTSTRAP-301 — Instruction Encoding & Machine Code Emission** thành **relocatable object/module unit**.

Pipeline:

```text
Final Machine IR
      ↓
Instruction Encoder
      ↓
Machine Bytes
Fixups
Symbols
      ↓
┌─────────────────────────────┐
│ BOOTSTRAP-302               │
│ Object Model / Layout       │
│ Section Builder             │
│ Symbol Table                │
│ Relocation Builder          │
│ String Tables               │
│ Format Writers              │
│ Object Verifier             │
└─────────────────────────────┘
      ↓
   .o / .obj / Mach-O object
   / WASM object-like module
      ↓
   BOOTSTRAP-303+
   Linker / Executable Builder
```

**302 không được link.**

Nó không quyết định địa chỉ cuối cùng của symbol, không resolve external symbol và không tạo PE/ELF executable cuối cùng.

---

# 302.2. Nguyên tắc kiến trúc

Object writer phải được chia thành hai tầng:

```text
Target-independent Object IR
              ↓
      Format-specific lowering
              ↓
       ELF / COFF / Mach-O
       / WASM object writer
```

Không được để semantic của ELF/COFF/Mach-O lan ngược vào compiler IR.

Ví dụ compiler chỉ nói:

```text
section = Code
symbol = foo
binding = Global
relocation = PCRelative32(foo)
```

Writer ELF mới chuyển thành:

```text
.text
.symtab
.rela.text
R_X86_64_PC32
```

Trong khi COFF sẽ chuyển thành relocation tương ứng của COFF.

---

# 302.3. Object IR

Định nghĩa một mô hình object trung gian:

```text
ObjectFile
 ├── format
 ├── architecture
 ├── endianness
 ├── abi
 ├── sections[]
 ├── symbols[]
 ├── relocations[]
 ├── groups[]
 ├── comdats[]
 ├── string_tables[]
 ├── debug_records[]
 ├── unwind_records[]
 └── metadata
```

Các ID phải dùng handle ổn định:

```text
SectionId
SymbolId
RelocationId
StringId
GroupId
ComdatId
```

Không dùng raw index xuyên suốt pipeline.

Index vật lý chỉ được sinh ở bước serialization cuối.

---

# 302.4. Section model

Mỗi section có semantic attributes:

```text
Section {
    id
    name
    kind
    flags
    alignment
    size
    content
    nobits
    merge_policy
    group
}
```

### SectionKind

Ít nhất:

```text
Code
ReadOnlyData
Data
Bss
TlsData
TlsBss

Unwind
Debug
DebugInfo
DebugLine
DebugFrame

Metadata
LinkerMetadata
TargetSpecific
Custom
```

### Section flags

```text
ALLOC
EXEC
WRITE
MERGE
STRINGS
TLS
DEBUG
DISCARDABLE
GROUP_MEMBER
```

Không được hard-code ELF flag vào Object IR.

---

# 302.5. Section content

Một section có thể chứa:

```text
RawBytes
ZeroFill(size)
SymbolTable
StringTable
RelocationTable
TargetMetadata
```

Ví dụ:

```text
.text
    RawBytes

.rodata
    RawBytes

.bss
    ZeroFill(4096)

.rela.text
    RelocationTable

.symtab
    SymbolTable
```

`BSS` không cần chứa zero bytes thật.

Object writer phải biểu diễn nó bằng metadata tương ứng của format.

---

# 302.6. Section alignment

Alignment là semantic requirement:

```text
Section.alignment : u64
```

Invariant:

```text
alignment > 0
alignment is power-of-two
```

trừ khi một target format có yêu cầu đặc biệt được explicit hóa.

Ví dụ:

```text
.text    align 16
.rodata  align 16
.data    align 8
.bss     align 64
```

Writer không được tự ý giảm alignment.

Có thể tăng alignment nếu format yêu cầu, nhưng phải ghi nhận quyết định đó trong layout result.

---

# 302.7. Symbol model

Symbol phải độc lập với symbol table của từng format.

```text
Symbol {
    id
    name
    binding
    visibility
    kind
    section
    value
    size
    definition
}
```

### Binding

```text
Local
Global
Weak
```

Có thể mở rộng:

```text
Unique
Common
TargetSpecific
```

### Visibility

```text
Default
Hidden
Protected
Internal
TargetSpecific
```

### SymbolKind

```text
Function
Object
Section
Tls
Absolute
File
Unknown
```

---

# 302.8. Symbol definition

Phải phân biệt rõ:

```text
Defined
Undefined
Absolute
Common
SectionRelative
```

Ví dụ:

```text
foo:
    Defined
    section = .text
    value = 0
    size = 128
```

External function:

```text
printf:
    Undefined
```

Không được biến external symbol thành địa chỉ giả.

---

# 302.9. Symbol visibility và export

Object writer không quyết định symbol nào trở thành API public của executable.

Compiler có thể sinh:

```text
Global
```

nhưng linker/export policy ở giai đoạn sau mới quyết định:

```text
ELF export
PE export
Mach-O export
```

Phân biệt:

```text
source visibility
≠
object symbol binding
≠
final binary export
```

Đây là invariant quan trọng của Axiom.

---

# 302.10. Relocation model

Relocation là contract giữa:

```text
machine bytes
+
symbol
+
relocation kind
```

Object writer **không resolve relocation**.

Ví dụ:

```text
.text:

E8 ?? ?? ?? ??
```

với:

```text
Relocation {
    section = .text
    offset = 0x15
    symbol = foo
    kind = PCRelative32
    addend = -4
}
```

Linker sau này mới biết địa chỉ `foo`.

---

# 302.11. Relocation IR

Định nghĩa:

```text
Relocation {
    section
    offset
    symbol
    kind
    addend
    width
    signedness
    pc_relative
}
```

`kind` trước tiên là target-independent semantic class.

Ví dụ:

```text
Absolute
Absolute32
Absolute64

PCRelative
PCRelative32

GOT
GOTPCRelative

PLT
PLTCall

TLS
TLSLocal
TLSGlobal

SectionRelative

TargetSpecific
```

Sau đó:

```text
ObjectRelocation
       ↓
Target relocation lowering
       ↓
ELF/COFF/Mach-O relocation
```

---

# 302.12. Relocation addend

Phải hỗ trợ cả hai mô hình:

```text
ExplicitAddend
ImplicitAddend
```

ELF64 thường dùng:

```text
RELA
```

trong đó addend nằm trong relocation record.

Một số format/target có thể encode addend ngay trong instruction/data.

Object IR phải giữ semantic addend độc lập với physical encoding.

---

# 302.13. Architecture relocation mapping

Writer phải có bảng mapping riêng cho từng target.

Ví dụ x86-64 ELF:

```text
PCRelative32
    → R_X86_64_PC32

PLT32
    → R_X86_64_PLT32

Absolute64
    → R_X86_64_64

Absolute32
    → R_X86_64_32

AbsoluteSigned32
    → R_X86_64_32S

GOTPCRelative
    → R_X86_64_GOTPCREL
```

ARM64 cần hỗ trợ tối thiểu các pattern phổ biến:

```text
CALL26
JUMP26

ADR_PREL_LO21
ADR_PREL_PG_HI21

ADD_ABS_LO12_NC

LDST64_ABS_LO12_NC
```

RISC-V cần hỗ trợ:

```text
R_RISCV_32
R_RISCV_64

JAL
BRANCH

CALL
CALL_PLT

HI20
LO12_I
LO12_S

PCREL_HI20
PCREL_LO12_I
PCREL_LO12_S
```

Relaxation relocation phải được giữ nếu linker cần thực hiện relaxation.

---

# 302.14. ELF64 Object Writer

Đây là writer đầu tiên phải hoàn thiện đầy đủ.

Output:

```text
ET_REL
```

Không phải:

```text
ET_EXEC
ET_DYN
```

Cấu trúc tối thiểu:

```text
ELF Header

Section:
    .text
    .rodata
    .data
    .bss
    .tdata
    .tbss

Relocations:
    .rela.text
    .rela.rodata
    .rela.data

Symbols:
    .symtab

Strings:
    .strtab
    .shstrtab
```

Có thể bổ sung:

```text
.eh_frame
.debug_info
.debug_abbrev
.debug_line
.debug_frame
```

khi debug/unwind subsystem cung cấp dữ liệu.

---

# 302.15. ELF section header

Writer phải tính:

```text
sh_name
sh_type
sh_flags
sh_addr
sh_offset
sh_size
sh_link
sh_info
sh_addralign
sh_entsize
```

Trong relocatable object:

```text
sh_addr
```

thường chưa mang địa chỉ runtime cuối cùng.

`sh_offset` chỉ được quyết định sau khi layout object.

---

# 302.16. ELF symbol table

Sinh `.symtab` với:

```text
st_name
st_info
st_other
st_shndx
st_value
st_size
```

Symbol index phải deterministic.

Quy tắc ordering nên cố định:

```text
STN_UNDEF
↓
local symbols
↓
global symbols
↓
weak symbols
```

và trong mỗi nhóm:

```text
stable semantic order
```

Không dùng hash-map iteration order để quyết định binary layout.

---

# 302.17. ELF relocation section

Mỗi relocation section phải liên kết chính xác với target section:

```text
.rela.text
    sh_info → .text
    sh_link → .symtab
```

Mỗi relocation:

```text
r_offset
r_info
r_addend
```

`r_info` được tạo từ:

```text
symbol_index
relocation_type
```

Không được để Object IR phụ thuộc vào ELF symbol index trước bước serialization.

---

# 302.18. COFF Object Writer

Output:

```text
.obj
```

Target chính:

```text
Windows x86-64
Windows ARM64
```

Object writer phải tạo:

```text
COFF Header
Section Table
Section Data
Relocation Table
Symbol Table
String Table
```

Các section phổ biến:

```text
.text
.rdata
.data
.bss
```

và các section debug/unwind/linker metadata khi subsystem tương ứng cung cấp.

Relocation phải map sang COFF relocation types, ví dụ x86-64:

```text
IMAGE_REL_AMD64_ADDR64
IMAGE_REL_AMD64_ADDR32
IMAGE_REL_AMD64_REL32
```

ARM64 có relocation family riêng.

Không được giả định COFF có semantic giống ELF chỉ vì cả hai đều có section/symbol/relocation.

---

# 302.19. Mach-O Object Writer

Output:

```text
MH_OBJECT
```

Mô hình phải hỗ trợ:

```text
Mach Header
Load Commands
Segments/Sections
Symbol Table
String Table
Relocations
```

Các section cơ bản:

```text
__TEXT,__text
__TEXT,__const
__DATA,__data
__DATA,__bss
```

và các section metadata cần thiết.

Mach-O relocation encoding phải được map từ Object IR thay vì tạo trực tiếp trong encoder.

---

# 302.20. WASM Object/Module Writer

WASM không phải ELF-style object file.

Vì vậy phải xem nó là:

```text
Object-like Module
```

thay vì cố ép vào section/symbol model của ELF.

Cần hỗ trợ khi cần:

```text
Type section
Import section
Function section
Code section
Data section
Element section
Custom sections
Linking metadata
Relocation metadata
Symbol metadata
```

Ví dụ:

```text
custom "linking"
custom "reloc.CODE"
custom "reloc.DATA"
```

Writer phải giữ function/data indices và relocation metadata theo semantics của WASM linker model.

---

# 302.21. COMDAT / Deduplication

Object IR phải có abstraction:

```text
ComdatGroup {
    key
    selection
    members[]
}
```

Selection có thể:

```text
Any
SameSize
ExactMatch
Largest
NoDuplicates
Associative
TargetSpecific
```

Không phải format nào cũng hỗ trợ giống nhau.

Compiler có thể tạo:

```text
generic_instance<T>
```

ở nhiều translation units.

Object layer phải cung cấp cơ chế để linker sau này loại bỏ duplicate implementation.

Object writer **không tự deduplicate global definitions**.

---

# 302.22. Mergeable sections

Hỗ trợ metadata:

```text
MergePolicy {
    None
    MergeByContent
    MergeStrings
    MergeConstants
}
```

Ví dụ:

```text
.rodata.str1.1
.rodata.cst16
```

Nhưng quyết định cuối cùng về merging thuộc linker.

Object writer chỉ mô tả khả năng/contract.

---

# 302.23. String table

Xây dựng StringTable riêng:

```text
StringTable {
    intern(string) -> StringId
    finalize() -> bytes
}
```

Yêu cầu:

- deduplicate string
- deterministic index
- null terminator
- offset validation

Dùng cho:

```text
symbol names
section names
debug names
format metadata
```

Không dùng một string table chung nếu format yêu cầu nhiều table khác nhau.

---

# 302.24. Object layout engine

Object layout phải chạy sau khi toàn bộ section/symbol/relocation đã được thu thập.

```text
Collect
  ↓
Canonicalize
  ↓
Assign Section Order
  ↓
Assign Section Offsets
  ↓
Assign Symbol Indices
  ↓
Assign Relocation Indices
  ↓
Build String Tables
  ↓
Serialize
```

Không được phụ thuộc vào thứ tự insertion ngẫu nhiên.

---

# 302.25. Deterministic build

Cùng input:

```text
source
compiler version
target
features
```

phải sinh object byte-identical trong deterministic mode.

Phải kiểm soát:

- section order
- symbol order
- relocation order
- string order
- padding
- alignment
- metadata order
- timestamps
- UUID/random fields
- hash tables nếu format có
- debug ordering

Các trường không deterministic của format phải được:

```text
zeroed
hoặc
canonicalized
hoặc
explicitly controlled
```

---

# 302.26. Debug integration

302 không tự thiết kế toàn bộ DWARF/PDB/debug system.

Nó chỉ cung cấp interface:

```text
DebugSectionProvider
```

nhận:

```text
DebugRecord[]
```

và tạo các section phù hợp.

Ví dụ:

```text
.debug_info
.debug_abbrev
.debug_line
.debug_str
```

hoặc format tương ứng.

Source mapping từ compiler phải tiếp tục tồn tại:

```text
Source
 ↓
HIR
 ↓
MIR
 ↓
Machine IR
 ↓
Machine Bytes
 ↓
Object offset
```

để sau này debugger có thể map:

```text
machine address → source location
```

---

# 302.27. Unwind integration

Tương tự debug, 302 chỉ nhận unwind information từ backend:

```text
UnwindRecord {
    function
    start
    size
    CFA rules
    register rules
}
```

Writer có thể tạo:

```text
.eh_frame
```

hoặc target-specific unwind sections.

Không được hard-code DWARF CFI vào machine encoder.

---

# 302.28. External symbol contract

Object writer phải giữ nguyên:

```text
UndefinedSymbol
```

Ví dụ:

```text
extern fn printf(...)
```

sinh:

```text
symbol:
    printf
    Undefined
```

và relocation:

```text
.text
    → printf
```

Không được:

- resolve qua system linker
- gọi assembler
- tìm địa chỉ symbol
- load DLL/shared library
- link object khác.

Đó là trách nhiệm của linker.

---

# 302.29. Object verifier

Trước khi ghi file:

```text
ObjectVerifier
```

phải kiểm tra.

### Section

```text
- alignment hợp lệ
- size hợp lệ
- content không vượt bounds
- flags tương thích
- section group hợp lệ
```

### Symbol

```text
- section tồn tại
- value nằm trong section nếu section-relative
- size hợp lệ
- binding hợp lệ
- duplicate definition hợp lệ theo policy
```

### Relocation

```text
- section tồn tại
- offset nằm trong section
- width không vượt section
- symbol tồn tại
- relocation kind hợp lệ với target
- addend hợp lệ
- instruction/data encoding đủ chỗ
```

### Format

```text
- header hợp lệ
- table offsets hợp lệ
- table sizes hợp lệ
- alignment hợp lệ
- indices hợp lệ
- file không có vùng unreachable/malformed
```

---

# 302.30. Round-trip verification

Phải có:

```text
Axiom Object Writer
        ↓
object bytes
        ↓
Object Parser
        ↓
Object IR
```

và kiểm tra:

```text
Canonicalize(original)
==
Canonicalize(parsed)
```

Không yêu cầu byte-identical giữa input/output parser vì format có thể canonicalize representation.

---

# 302.31. Differential testing

Trong bootstrap:

```text
Axiom Encoder
       ↓
Object Writer
```

được so sánh với:

```text
known-good assembler/object writer
```

nhưng chỉ dùng external toolchain cho:

```text
validation
```

không phải runtime dependency của Axiom.

Ví dụ:

```text
Axiom → ELF .o
system tools → inspect
```

So sánh:

```text
sections
symbols
relocations
alignment
machine bytes
```

---

# 302.32. Fuzzing

Fuzz các tầng:

```text
Object IR
Section layout
Symbol table
Relocation mapping
String table
ELF serialization
COFF serialization
Mach-O serialization
WASM serialization
Object parser
```

Các property:

```text
never panic
never out-of-bounds
never emit malformed object
parse(write(x)) ≈ x
```

---

# 302.33. Implementation tree

Đề xuất:

```text
compiler/backend/object/
│
├── object_ir.ax
├── object_file.ax
├── section.ax
├── symbol.ax
├── relocation.ax
├── string_table.ax
├── comdat.ax
├── layout.ax
├── debug.ax
├── unwind.ax
├── verify.ax
│
├── elf/
│   ├── elf64.ax
│   ├── sections.ax
│   ├── symbols.ax
│   ├── relocations.ax
│   └── writer.ax
│
├── coff/
│   ├── coff.ax
│   ├── sections.ax
│   ├── symbols.ax
│   ├── relocations.ax
│   └── writer.ax
│
├── macho/
│   ├── macho.ax
│   ├── sections.ax
│   ├── symbols.ax
│   ├── relocations.ax
│   └── writer.ax
│
├── wasm/
│   ├── module.ax
│   ├── linking.ax
│   ├── relocations.ax
│   └── writer.ax
│
└── tests/
    ├── sections/
    ├── symbols/
    ├── relocations/
    ├── elf/
    ├── coff/
    ├── macho/
    └── wasm/
```

---

# 302.34. Public compiler API

Backend phía trên chỉ cần một interface:

```text
fn emit_object(
    machine_unit: MachineUnit,
    target: Target,
    options: ObjectOptions
) -> Result<ObjectArtifact, ObjectError>
```

Trong đó:

```text
ObjectArtifact {
    format
    architecture
    bytes
    sections
    symbols
    relocations
    diagnostics
}
```

Debug/test mode có thể giữ Object IR trước serialization.

---

# 302.35. Invariants

Đóng băng các invariant chính:

```text
AOBJ-20  Object IR độc lập format.

AOBJ-21  Object writer không thực hiện linking.

AOBJ-22  External symbols không được tự resolve.

AOBJ-23  Relocation semantic phải được bảo toàn.

AOBJ-24  Symbol index vật lý chỉ được tạo ở serialization.

AOBJ-25  Section layout deterministic.

AOBJ-26  Symbol ordering deterministic.

AOBJ-27  Relocation ordering deterministic.

AOBJ-28  String table deterministic.

AOBJ-29  Section alignment không được giảm trái phép.

AOBJ-30  BSS không cần materialize zero bytes.

AOBJ-31  Undefined symbol phải được giữ nguyên.

AOBJ-32  Local/global/weak semantics phải được bảo toàn.

AOBJ-33  Visibility không được biến thành final export policy.

AOBJ-34  COMDAT semantics phải được bảo toàn.

AOBJ-35  Mergeable-section semantics phải được bảo toàn.

AOBJ-36  Object writer không thay đổi machine semantics.

AOBJ-37  Object writer không được tự ý re-optimize instructions.

AOBJ-38  Relocation width phải phù hợp relocation kind.

AOBJ-39  Relocation offset phải nằm trong section.

AOBJ-40  Symbol reference phải tồn tại.

AOBJ-41  Format-specific relocation mapping phải explicit.

AOBJ-42  ELF writer tạo ET_REL, không tạo executable.

AOBJ-43  COFF writer tạo relocatable .obj.

AOBJ-44  Mach-O writer tạo MH_OBJECT.

AOBJ-45  WASM writer giữ đúng linking/relocation semantics của WASM.

AOBJ-46  Debug metadata không được phá machine/object layout.

AOBJ-47  Unwind metadata không được phá machine/object layout.

AOBJ-48  Output deterministic trong deterministic mode.

AOBJ-49  Writer phải được verify trước serialization.

AOBJ-50  Object bytes phải parse được bởi object parser của Axiom.

AOBJ-51  parse(write(x)) phải giữ nguyên semantic Object IR.

AOBJ-52  External assembler không phải dependency.

AOBJ-53  External linker không phải dependency.

AOBJ-54  Object writer không quyết định final runtime address.

AOBJ-55  Object writer không quyết định final binary export.

AOBJ-56  Target-independent Object IR là semantic source of truth.

AOBJ-57  Format writers chỉ là serialization/lowering layer.

AOBJ-58  Malformed Object IR phải bị reject trước serialization.

AOBJ-59  Object emission phải reproducible.

AOBJ-60  Không được để hash-map iteration quyết định binary ordering.
```

---

## 302.36. Definition of Done

BOOTSTRAP-302 chỉ được coi là hoàn thành khi Axiom có thể:

```text
Axiom source
   ↓
MIR
   ↓
Machine IR
   ↓
Machine Bytes
   ↓
Object IR
   ↓
ELF64 .o
```

và tương tự cho:

```text
x86-64 COFF .obj
ARM64 COFF .obj
ARM64 Mach-O .o
x86-64 Mach-O .o
WASM object/module
```

với:

- section đúng
- symbol đúng
- relocation đúng
- alignment đúng
- deterministic
- object verifier pass
- object parser round-trip pass
- không cần assembler bên ngoài
- không cần linker bên ngoài để **tạo object**.

**Điểm kết thúc của 302 là relocatable object.** Bước kế tiếp mới bắt đầu giải quyết vấn đề lớn hơn: **nhiều object + libraries + symbols + relocations → linked image/executable**, tức linker architecture.