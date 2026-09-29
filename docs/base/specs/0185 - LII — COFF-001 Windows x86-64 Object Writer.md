# LII — COFF-001: Windows x86-64 Object Writer

Ta tiếp tục đúng chuỗi. Mục tiêu của bước này là làm cho Axiom tự sinh được **`.obj` PE/COFF hợp lệ** từ Machine Code.

```text
Axiom Source
    ↓
...
    ↓
X86 Encoder
    ↓
EncodedObject
    ↓
COFF Writer
    ↓
hello.obj
```

Điểm quan trọng: **`.obj` chưa phải `.exe`**. Nó là object file để linker xử lý.

---

# 1. COFF không được trộn với PE linker

Tách hoàn toàn:

```text
compiler/object/
    COFF object representation
    COFF serialization

compiler/linker/
    symbol resolution
    section merging
    relocation
    PE generation
```

Không để COFF writer biết:

- entry point cuối cùng
- import DLL
- subsystem
- PE sections cuối cùng
- image base
- final virtual addresses

Đó là nhiệm vụ của linker.

---

# 2. Object representation

```text id="8e0x1c"
CoffObject {
    machine: CoffMachine
    characteristics: u16
    sections: Vec<CoffSection>
    symbols: Vec<CoffSymbol>
    relocations: Vec<CoffRelocation>
    string_table: StringTable
}
```

Machine:

```text
CoffMachine =
    AMD64
```

v0.1 chỉ cần:

```text
IMAGE_FILE_MACHINE_AMD64 = 0x8664
```

---

# 3. COFF section

```text id="q7k5ad"
CoffSection {
    name
    data
    virtual_size
    characteristics
    alignment
    relocations
}
```

Object-file section chủ yếu cần:

```text
name
raw_data
characteristics
relocations
```

`virtual_size` sẽ quan trọng hơn ở PE image stage.

---

# 4. Section flags

Axiom nên biểu diễn semantic flags trước:

```text id="c2xq1e"
SectionFlags {
    readable
    writable
    executable
    discardable
    contains_code
    contains_initialized_data
    contains_uninitialized_data
}
```

COFF writer map sang:

```text id="e8n4o0"
IMAGE_SCN_CNT_CODE
IMAGE_SCN_CNT_INITIALIZED_DATA
IMAGE_SCN_CNT_UNINITIALIZED_DATA
IMAGE_SCN_MEM_READ
IMAGE_SCN_MEM_WRITE
IMAGE_SCN_MEM_EXECUTE
```

---

# 5. `.text`

Ví dụ:

```text id="xq5q8e"
.text
    B8 2A 00 00 00
    C3
```

flags:

```text
CODE
EXECUTE
READ
```

Không writable.

Đây cũng phù hợp với mục tiêu W^X sau này.

---

# 6. `.rdata`

```text id="3p8l5v"
.rdata
```

flags:

```text
INITIALIZED_DATA
READ
```

Không:

```text
WRITE
EXECUTE
```

---

# 7. `.data`

```text id="w2d5nj"
.data
```

flags:

```text
INITIALIZED_DATA
READ
WRITE
```

---

# 8. `.bss`

COFF có thể biểu diễn zero/uninitialized data thông qua section characteristics và raw size phù hợp.

Axiom semantic model:

```text id="l3r6f1"
BSS {
    size
    alignment
}
```

Không ghi hàng triệu byte zero vào file.

---

# 9. Section naming

v0.1:

```text id="p8wy3u"
.text
.rdata
.data
.bss
```

Sau này có thể:

```text
.ax$...
```

cho COMDAT/grouping nếu cần.

Nhưng **không nên đưa COMDAT vào MVP quá sớm**.

---

# 10. Symbol

```text id="e2j4s8"
CoffSymbol {
    name
    value
    section_number
    type
    storage_class
}
```

Axiom semantic symbol trước serialization:

```text id="4f8b5r"
Symbol {
    name
    kind
    binding
    section
    offset
    visibility
}
```

COFF writer mới chuyển sang representation của COFF.

---

# 11. Symbol kinds

MVP:

```text id="z3t9x0"
Function
Object
Section
External
Absolute
```

Ví dụ:

```text
fn main()
```

→

```text
Symbol {
    name = "main"
    kind = Function
    section = ".text"
    offset = 0
}
```

---

# 12. Local vs external symbol

Ví dụ:

```axiom
extern "system" fn MessageBoxA(...)
```

compiler tạo:

```text id="z8f4s2"
External("MessageBoxA")
```

Object writer không biết DLL nào cung cấp symbol này.

Linker/import system xử lý sau.

---

# 13. Symbol table index

COFF relocation tham chiếu:

```text
symbol_index
```

Do đó serialization phải ổn định.

Không được phụ thuộc hash-map iteration order.

Dùng deterministic ordering:

```text id="h3x5b1"
section symbols
→ local symbols
→ global symbols
→ external symbols
```

hoặc một thứ tự chuẩn hóa riêng của Axiom.

Quan trọng nhất:

> cùng input → cùng `.obj` byte-for-byte.

---

# 14. String table

COFF symbol names có giới hạn trực tiếp trong symbol record.

Tên dài cần string table.

```text id="x8q3n4"
StringTable {
    strings
    offsets
}
```

Ví dụ:

```text
very_long_axiom_function_name
```

được lưu trong string table và symbol chứa offset.

---

# 15. Relocation abstraction

Encoder đã tạo:

```text id="y1r6j7"
Relocation {
    offset
    kind
    symbol
    addend
}
```

COFF writer map:

```text id="f6n2p9"
REL32
    ↓
IMAGE_REL_AMD64_REL32

ABS64
    ↓
IMAGE_REL_AMD64_ADDR64

ABS32
    ↓
IMAGE_REL_AMD64_ADDR32
```

---

# 16. `CALL foo`

Machine bytes:

```text id="w3p7d2"
E8 00 00 00 00
```

Relocation:

```text id="x4j8m1"
offset = instruction+1
symbol = foo
type = IMAGE_REL_AMD64_REL32
```

Linker sau này tính:

```text id="v7s2q9"
foo_address - next_instruction_address
```

---

# 17. RIP-relative global

Ví dụ:

```text id="h6m4r0"
MOV RAX,[RIP + global]
```

Object:

```text
instruction bytes
+
REL32(global)
```

Linker resolve khi layout final đã biết.

---

# 18. Không dùng absolute address trong code nếu không cần

Axiom backend nên ưu tiên:

```text id="s5n8k2"
RIP-relative
```

cho:

- global data
- readonly constants
- local symbols
- jump tables

vì nó phù hợp với x86-64 position-independent style và giúp linker dễ xử lý.

---

# 19. COMDAT

Generic functions được monomorphize:

```text
Vec<i32>
Vec<f64>
```

Nếu nhiều translation unit cùng instantiate một specialization, tương lai có thể cần COMDAT.

Nhưng v0.1:

```text id="n7x2c6"
single compilation unit
```

trước.

Sau đó mới:

```text
COMDAT
weak/select-any
identical COMDAT folding
```

Không đưa complexity này vào compiler kernel.

---

# 20. Object file layout

Conceptual:

```text id="m4w7x9"
COFF Header
Optional Header = none
Section Headers
    ↓
Raw Section Data
    ↓
Relocation Tables
    ↓
Symbol Table
    ↓
String Table
```

COFF object **không có PE optional header** như executable image.

Đây là distinction quan trọng.

---

# 21. COFF writer API

```text id="f7n2v5"
fn write_coff(
    object: CoffObject,
    output: Writer
) -> Result<(), CoffError>
```

Không nhận:

```text
TargetExecutableConfig
```

Không nhận:

```text
EntryPoint
Subsystem
ImageBase
```

Những thứ đó thuộc linker.

---

# 22. COFF parser

Không chỉ writer.

Axiom nên có:

```text id="p6w4s8"
COFF Writer
COFF Reader
COFF Verifier
```

Cấu trúc:

```text id="1d7f4a"
compiler/object/coff/
├── header.ax
├── section.ax
├── symbol.ax
├── relocation.ax
├── string_table.ax
├── reader.ax
├── writer.ax
├── verifier.ax
└── tests/
```

---

# 23. Reader cực kỳ hữu ích

Pipeline test:

```text
CoffObject
    ↓
writer
    ↓
bytes
    ↓
reader
    ↓
CoffObject'
```

Sau đó:

```text
CoffObject == CoffObject'
```

ở semantic level.

---

# 24. Object verifier

Kiểm:

```text id="v3h8s6"
machine == AMD64

section offsets valid

section sizes valid

alignment valid

relocation offset nằm trong section

relocation symbol tồn tại

symbol section index hợp lệ

string-table offsets hợp lệ
```

---

# 25. Diagnostics

Thêm:

```text id="9c2w7k"
AX_COFF_0001 invalid machine
AX_COFF_0002 invalid section
AX_COFF_0003 invalid alignment
AX_COFF_0004 invalid relocation
AX_COFF_0005 unknown relocation kind
AX_COFF_0006 invalid symbol
AX_COFF_0007 invalid string table
AX_COFF_0008 malformed object
AX_COFF_0009 duplicate symbol
```

---

# 26. Acceptance test đầu tiên

Source:

```axiom
fn main() -> i32 {
    42
}
```

Machine:

```text
.text:
    MOV EAX,42
    RET
```

Object:

```text
hello.obj
```

Có:

```text
.text
main
```

Không có:

```text
runtime
CRT
LLVM
assembler
```

---

# 27. Acceptance test thứ hai

```axiom
fn add(a: i32, b: i32) -> i32 {
    a + b
}
```

Object:

```text
.text
    add:
        ...
```

Symbol:

```text
add
```

Không cần linker.

---

# 28. Acceptance test thứ ba — external symbol

```axiom
extern "C" fn external_add(a: i32, b: i32) -> i32

fn test() -> i32 {
    external_add(20, 22)
}
```

Object phải chứa:

```text
test
external_add
REL32 relocation
```

nhưng không resolve `external_add`.

---

# 29. Acceptance test thứ tư — global

```axiom
static answer: i32 = 42

fn get() -> i32 {
    answer
}
```

Object:

```text
.rdata/.data
.text
```

và relocation từ code đến data.

---

# 30. Acceptance test thứ năm — string

```axiom
fn hello() {
    print("hello")
}
```

Object phải có:

```text
.text
.rdata
```

và relocation từ `.text` tới `.rdata` hoặc symbol tương ứng.

---

# 31. COFF milestone

```text id="e6c9s2"
COFF-001 data model
COFF-002 section writer
COFF-003 symbol writer
COFF-004 string table
COFF-005 relocation writer
COFF-006 reader
COFF-007 verifier
COFF-008 deterministic serialization
COFF-009 golden object tests
COFF-010 compiler → .obj
```

Sau **COFF-010**, Axiom đã có khả năng:

```text
source.ax
    ↓
Axiom compiler
    ↓
machine code
    ↓
Windows x64 .obj
```

mà không cần LLVM/Clang/MinGW.

---

# LIII — PE-LINK-001: Axiom Native Windows Linker

Đây là bước lớn hơn.

Ta sẽ **không gọi `link.exe`**.

```text
.obj
.obj
.obj
   ↓
Axiom Linker
   ↓
PE32+ .exe
```

---

# 32. Linker architecture

```text id="v4m7s1"
COFF Reader
     ↓
Object Graph
     ↓
Symbol Resolution
     ↓
Section Merge
     ↓
COMDAT/Dead Strip
     ↓
Layout
     ↓
Relocation
     ↓
PE Builder
     ↓
PE32+
```

---

# 33. Linker input

```text id="k5n9r3"
LinkInput {
    objects[]
    libraries[]
    entry
    subsystem
    output
    image_base
    sections
    flags
}
```

MVP:

```text
objects only
```

Sau đó mới:

```text
.lib
.dll import libraries
```

---

# 34. Symbol resolution

Ví dụ:

```text
a.obj:
    foo

b.obj:
    call foo
```

linker tạo:

```text id="s8j3v6"
foo → a.obj:.text+offset
```

Sau đó patch relocation ở `b.obj`.

---

# 35. Undefined symbol

Nếu:

```text
call foo
```

nhưng không có:

```text
foo
```

→

```text
AX_LINK_0001
undefined symbol: foo
```

---

# 36. Duplicate symbol

Hai object:

```text
a.obj → foo
b.obj → foo
```

MVP:

```text
AX_LINK_0002
duplicate symbol: foo
```

COMDAT xử lý sau.

---

# 37. Section merging

Input:

```text
a.obj:
.text = A

b.obj:
.text = B
```

Linker:

```text
.text:
A
B
```

symbol offsets được cập nhật.

---

# 38. Final PE sections

MVP:

```text id="g3w8s5"
.text
.rdata
.data
.pdata
.reloc
```

` .bss` có thể được folded vào writable image region với virtual size > raw size tùy implementation.

`.pdata` sẽ cần cho Windows x64 unwind information khi ta hỗ trợ proper stack unwinding.

---

# 39. PE section flags

```text id="s2n7v4"
.text
    READ | EXECUTE

.rdata
    READ

.data
    READ | WRITE

.pdata
    READ

.reloc
    READ
```

Không:

```text
WRITE | EXECUTE
```

trừ khi chương trình thực sự yêu cầu và explicitly opt-in.

---

# 40. PE image structure

```text id="r7k2m9"
DOS Header
DOS Stub
PE Signature
COFF File Header
Optional Header PE32+
Section Headers
Sections
```

PE32+ là **64-bit PE**, dù tên `PE32+`.

---

# 41. PE signature

```text
PE\0\0
```

nằm tại offset được DOS header chỉ ra.

---

# 42. PE32+ Optional Header

MVP cần:

```text id="p3f8s1"
Magic
AddressOfEntryPoint
ImageBase
SectionAlignment
FileAlignment
SizeOfImage
SizeOfHeaders
Subsystem
SizeOfCode
SizeOfInitializedData
SizeOfUninitializedData
NumberOfRvaAndSizes
DataDirectories[]
```

---

# 43. Image base

MVP có thể chọn:

```text id="c5m8x2"
0x140000000
```

cho 64-bit executable.

Nhưng **không hard-code trong compiler**.

Linker config:

```text
image_base
```

sẽ quyết định.

---

# 44. RVA vs VA

Đây là abstraction phải tồn tại riêng:

```text id="k4r8d2"
FileOffset
RVA
VA
```

Quan hệ:

```text
VA = ImageBase + RVA
```

Không được trộn chúng.

---

# 45. Address abstraction

```text id="b8f2s7"
Address {
    kind:
        FileOffset
        RVA
        VA
}
```

Compiler/linker code không được truyền `u64` đơn thuần cho mọi loại address.

Đây là một chỗ rất đáng dùng strong types.

---

# 46. Section layout

Ví dụ conceptual:

```text
Headers

.text
.rdata
.data
.pdata
.reloc
```

Mỗi section:

```text
RVA
VirtualSize
RawOffset
RawSize
Characteristics
```

---

# 47. Alignment

Hai alignment khác nhau:

```text
SectionAlignment
FileAlignment
```

Ví dụ:

```text
SectionAlignment = 0x1000
FileAlignment    = 0x200
```

Không được nhầm.

---

# 48. Relocation application

Ví dụ:

```text
CALL foo
```

Linker biết:

```text
source RVA
target RVA
```

và tính relative displacement.

Đây là lúc:

```text
REL32
```

được resolve.

---

# 49. Absolute relocation

Nếu code/data chứa:

```text
absolute address
```

linker phải patch:

```text
ImageBase + RVA
```

và nếu executable hỗ trợ relocation:

```text
.reloc
```

phải chứa base relocation entry.

---

# 50. ASLR

Axiom nên hỗ trợ ASLR ngay từ kiến trúc linker.

Điều đó có nghĩa:

```text id="y4n7p3"
absolute addresses
```

phải được quản lý có chủ đích.

MVP có thể tạo relocation table đầy đủ cho những absolute references cần thiết.

---

# 51. Entry point

Đây là nơi cần phân biệt:

```text
Axiom main()
```

với:

```text
PE AddressOfEntryPoint
```

Không nên để:

```text
PE entry = main
```

vĩnh viễn.

Kiến trúc đúng:

```text
PE Entry
   ↓
Axiom startup
   ↓
runtime initialization if enabled
   ↓
main()
   ↓
exit
```

---

# 52. Freestanding profile

Tuy nhiên:

```text
@entry fn main()
```

có thể cho phép:

```text
PE entry → main
```

nếu chương trình yêu cầu freestanding.

Như vậy:

```text
@entry
```

là semantic declaration.

---

# 53. Hosted Windows profile

Mặc định:

```text
Windows Hosted
```

có startup layer:

```text
axiom_start
    ↓
initialize
    ↓
main
    ↓
process_exit
```

Runtime component có thể được link **chỉ khi cần**.

---

# 54. Console vs GUI

Linker config:

```text id="p9k2d4"
Subsystem =
    Console
    Windows
```

Không nên để compiler quyết định dựa trên function name.

Ví dụ:

```text
axiom build --subsystem console
```

hoặc package metadata.

---

# 55. Exit code

Nếu:

```axiom
fn main() -> i32
```

startup:

```text
main()
    ↓
exit(code)
```

Nếu:

```axiom
fn main()
```

thì:

```text
exit(0)
```

Đây là ABI của Axiom startup layer, không phải semantics của `fn` nói chung.

---

# 56. First true Axiom executable

Acceptance test:

```axiom
fn main() -> i32 {
    42
}
```

Pipeline:

```text id="x3v8k1"
main.ax
 ↓
AST
 ↓
HIR
 ↓
MIR
 ↓
Verified MIR
 ↓
LIR
 ↓
Machine IR
 ↓
x86 encoding
 ↓
COFF
 ↓
Axiom PE linker
 ↓
hello.exe
```

Chạy:

```text
hello.exe
```

Windows process exit code:

```text
42
```

---

# 57. Đây là milestone cực lớn

Sau test này:

> **Axiom compiler không còn cần linker/compiler bên ngoài để tạo một Windows native executable tối giản.**

Có thể vẫn cần Windows API cho ứng dụng hosted, nhưng **compiler toolchain của Axiom đã tự sản xuất PE executable**.

---

# 58. Sau đó mới xử lý Windows API

Ví dụ:

```axiom
extern "system" fn GetStdHandle(...)
extern "system" fn WriteFile(...)
```

Axiom sẽ cần import system.

Không hard-code Windows API vào compiler.

Thay vào đó:

```text
std/windows
```

hoặc:

```text
platform/windows
```

là thư viện Axiom.

---

# 59. Import DLL

Đây là bước tiếp theo sau executable tối giản:

```text
PE Import Directory
    ↓
Import Descriptor
    ↓
INT / IAT
    ↓
DLL name
    ↓
function names
```

Ví dụ:

```text
KERNEL32.dll
GetStdHandle
WriteFile
ExitProcess
```

Nhưng **chưa đưa vào PE-LINK-001 MVP**.

Tách:

```text
PE-LINK-001
    static native executable

PE-LINK-002
    import table

PE-LINK-003
    DLL imports

PE-LINK-004
    IAT

PE-LINK-005
    delay imports
```

---

# 60. Windows startup cũng nên là Axiom

Cuối cùng:

```text
axiom/std/windows/startup.ax
```

có thể chứa phần startup viết bằng Axiom, còn một phần rất nhỏ dùng intrinsic/extern Windows API.

Mục tiêu:

```text
PE
 ↓
Axiom startup
 ↓
Axiom main
```

thay vì:

```text
PE
 ↓
MSVC CRT
 ↓
MSVC runtime
 ↓
Axiom main
```

Đây rất phù hợp với mục tiêu **không mandatory runtime**.

---

# 61. PE linker repository

```text id="w5n8r2"
compiler/linker/
├── graph.ax
├── symbols.ax
├── resolution.ax
├── sections.ax
├── layout.ax
├── relocation.ax
├── imports.ax
├── exports.ax
├── pe.ax
├── startup.ax
├── diagnostics.ax
└── tests/
```

Và target-specific:

```text
compiler/linker/pe64/
```

nếu muốn tách format khỏi generic linker.

---

# 62. Generic linker architecture

Không nên xây linker chỉ cho Windows.

```text id="g8m2x5"
Generic Linker
      │
      ├── Symbol Resolver
      ├── Section Layout
      ├── Relocation Engine
      ├── Dead Strip
      └── Image Builder
             │
             ├── PE64
             ├── ELF64
             └── Mach-O
```

Format layer:

```text
PE64
ELF64
Mach-O
```

---

# 63. Linker invariants

```text id="LINK-020"
Linker is deterministic.

LINK-021
Symbol resolution is explicit.

LINK-022
Duplicate symbols are diagnosed.

LINK-023
Undefined symbols are diagnosed.

LINK-024
Relocations are validated before application.

LINK-025
RVA, VA and file offsets are distinct types.

LINK-026
Section alignment is explicit.

LINK-027
Final addresses are assigned exactly once.

LINK-028
Relocation application preserves instruction semantics.

LINK-029
No external linker is required for Axiom-native output.

LINK-030
Runtime components are linked only when required.

LINK-031
Entry point is explicit.

LINK-032
Subsystem is explicit.

LINK-033
W^X is the default image policy.

LINK-034
Static executable generation works without DLL imports.

LINK-035
Import processing is separate from static linking.
```

---

# 64. Chuỗi milestone tiếp theo

```text id="n2w6r8"
COFF-001
    ↓
COFF-010
    ↓
PE-LINK-001  static PE32+
    ↓
PE-LINK-002  entry/startup
    ↓
PE-LINK-003  process exit
    ↓
PE-LINK-004  import table
    ↓
PE-LINK-005  Windows DLL calls
    ↓
PE-LINK-006  .lib/import library
    ↓
PE-LINK-007  .dll generation
```

Sau đó mới quay sang Linux:

```text
ELF-LINK-001
```

và macOS:

```text
MACHO-LINK-001
```

---

## Một quyết định kiến trúc quan trọng

Từ bây giờ Axiom nên coi **PE64/COFF là backend target chính thứ nhất**, không phải “backend phụ để test”.

Target matrix sẽ là:

```text
TARGETS

x86_64-windows-msvc
    COFF
    PE32+
    Windows ABI
    Windows startup

x86_64-linux-gnu
    ELF64
    System V AMD64

aarch64-windows
    COFF
    PE32+
    Windows ARM64 ABI

aarch64-linux
    ELF64
    AArch64 ABI

aarch64-macos
    Mach-O
    Apple ABI
```

Như vậy laptop Windows của bạn có thể là **bootstrap host đầu tiên**, nhưng kiến trúc compiler không bị khóa vào Windows.

### Bước kế tiếp

**LIV — PE-LINK-002: Startup + `hello.exe` end-to-end** sẽ là mốc rất thực tế: xây startup tối thiểu, `_AxiomMain`/entry convention, `ExitProcess`, console subsystem, rồi tạo `.exe` đầu tiên có thể chạy trực tiếp trên Windows.

Sau đó chúng ta sẽ quay lại hoàn thiện **register allocator + frame layout** nếu implementation order thực tế yêu cầu, rồi mới mở rộng import/DLL và cuối cùng ELF/Linux.