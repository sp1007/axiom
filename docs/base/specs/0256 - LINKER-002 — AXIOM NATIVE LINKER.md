Tiếp tục theo đúng pipeline. Phần tiếp theo là **LINKER-002 — Axiom Native Linker**. Đây là một mốc rất quan trọng, vì từ đây Axiom có thể đi từ `.o/.obj` thành **executable native hoàn chỉnh mà không cần GNU ld/lld/link.exe**.

# LINKER-002 — AXIOM NATIVE LINKER

## 1. Vai trò

Pipeline:

```text
Axiom Source
    ↓
Compiler
    ↓
Machine Encoder
    ↓
Object Writer
    ↓
.o / .obj / Mach-O object
    ↓
┌─────────────────────────────┐
│      Axiom Native Linker    │
├─────────────────────────────┤
│ Object Reader               │
│ Symbol Resolver             │
│ Archive Extractor           │
│ COMDAT / ICF                │
│ Section GC                  │
│ Section Layout              │
│ Segment Layout              │
│ Relocation                  │
│ Import / Export             │
│ GOT / PLT                   │
│ TLS                         │
│ Entry Point                 │
│ Executable Writer           │
└─────────────────────────────┘
    ↓
.exe / ELF / Mach-O / WASM
```

**Object Writer** trả lời:

> "Làm thế nào biểu diễn một object file?"

**Linker** trả lời:

> "Làm thế nào ghép nhiều object thành một chương trình có địa chỉ và relocation hoàn chỉnh?"

Hai thành phần này phải tách biệt.

---

# 2. LinkIR

Không nên để linker thao tác trực tiếp với cấu trúc ELF/COFF/Mach-O ngay từ đầu.

Ta tạo một IR trung gian:

```text
LinkIR
```

Ví dụ:

```text
LinkInput {
    objects[]
    archives[]
    shared_libraries[]
}

LinkModule {
    target
    sections[]
    symbols[]
    relocations[]
    comdats[]
    debug
    unwind
    tls
}
```

Sau khi đọc `.o`:

```text
ELF Object
COFF Object
Mach-O Object
      ↓
ObjectReader
      ↓
LinkIR
```

Sau khi link:

```text
LinkIR
   ↓
ELF Executable Writer
PE Executable Writer
Mach-O Executable Writer
```

Điều này cực kỳ quan trọng cho mục tiêu multi-platform.

---

# 3. Link Graph

Linker nên xây dựng một graph:

```text
Executable
   │
   ├── entry point
   │
   ├── Axiom main
   │      │
   │      ├── foo()
   │      ├── Vec<T>
   │      └── println()
   │
   └── runtime components
          │
          └── allocator
```

Mỗi symbol/function/data section là một node.

Relocation hoặc symbol reference là edge.

Ví dụ:

```text
_start
   │
   └── main
        │
        ├── foo
        │    └── helper
        │
        └── Vec_push
```

Nhờ graph này linker có thể làm:

- dead code elimination
- section GC
- archive extraction
- dependency analysis
- COMDAT elimination
- startup dependency analysis

---

# 4. Target Validation

Ngay khi đọc object:

```text
Object.target
```

phải được kiểm tra.

Ví dụ:

```text
x86_64-linux-gnu
```

không được link trực tiếp với:

```text
aarch64-linux-android
```

Các thuộc tính phải tương thích:

```text
architecture
pointer_width
endianness
OS
ABI
object_format
calling_convention
TLS model
relocation model
CPU features
```

Ví dụ:

```text
main.o
  x86_64
  Linux
  ELF

math.o
  x86_64
  Linux
  ELF
```

→ hợp lệ.

Nhưng:

```text
main.o
  x86_64

math.o
  ARM64
```

→

```text
AX1901 TargetMismatch
```

---

# 5. Symbol Resolution

Đây là trái tim của linker.

Ví dụ:

```text
main.o:
    main
    foo

foo.o:
    foo
    bar

bar.o:
    bar
```

Resolver phải tạo:

```text
main → main.o
foo  → foo.o
bar  → bar.o
```

## Symbol states

```text
Undefined
Defined
Common
Absolute
Weak
Imported
Exported
```

---

# 6. Strong / Weak

Ví dụ:

```text
foo.o:
    foo = strong

bar.o:
    foo = strong
```

→ duplicate strong symbol:

```text
AX1902 DuplicateSymbol
```

Nhưng:

```text
foo.o:
    foo = strong

bar.o:
    foo = weak
```

→ chọn strong.

Nếu:

```text
foo.o:
    foo = weak

bar.o:
    foo = weak
```

→ target/link policy quyết định symbol được chọn.

Điều quan trọng:

**Không để quy tắc này nằm rải rác trong ELF/COFF backend.**

Phải có generic symbol resolution.

---

# 7. Archive Extraction

Ví dụ:

```text
libmath.a
 ├── sin.o
 ├── cos.o
 ├── matrix.o
 └── unused.o
```

Chương trình chỉ dùng:

```text
sin()
```

Linker không nên đưa toàn bộ archive vào executable.

Algorithm:

```text
undefined symbols
       ↓
archive symbol index
       ↓
find object defining symbol
       ↓
extract object
       ↓
new undefined symbols
       ↓
repeat
```

Kết quả:

```text
libmath.a
    ↓
sin.o
```

`cos.o`, `matrix.o`, `unused.o` không được kéo vào.

---

# 8. Archive Symbol Index

Không nên scan toàn bộ archive mỗi lần.

Archive có index:

```text
Symbol → ObjectMember
```

Ví dụ:

```text
sin     → member #3
cos     → member #7
matrix  → member #12
```

Axiom nên có native archive format tương thích ít nhất với:

```text
.a
.lib
```

và có thể tự tạo archive mà không cần `ar`.

---

# 9. COMDAT

Generic code có thể tạo:

```text
Vec<i32>::push
Vec<i64>::push
```

Hoặc cùng một specialization xuất hiện trong nhiều object.

COMDAT cho phép:

```text
multiple equivalent definitions
        ↓
keep one
```

Linker cần:

```text
ComdatGroup
    key
    selection
    members
```

Các policy:

```text
Any
ExactMatch
SameSize
Largest
NoDuplicates
```

Target backend ánh xạ policy này sang ELF/COFF/Mach-O tương ứng.

---

# 10. ICF — Identical Code Folding

Sau COMDAT còn có:

```text
foo()
bar()
```

hai function có machine code giống hệt.

Ví dụ:

```text
foo:
    mov eax, 0
    ret

bar:
    mov eax, 0
    ret
```

Có thể:

```text
foo ─┐
     ├── same machine body
bar ─┘
```

thành một implementation.

Nhưng **không được mặc định hợp nhất mọi function**.

Vì địa chỉ function có thể observable.

Do đó:

```text
ICF policy:
    Disabled
    Safe
    All
```

MVP nên có:

```text
Safe ICF
```

và chỉ fold khi semantic/address identity cho phép.

---

# 11. Section GC

Đây là dead-code elimination ở cấp linker.

Object:

```text
.text.main
.text.foo
.text.bar
.text.unused
```

Nếu:

```text
main → foo
foo  → bar
```

thì:

```text
main
foo
bar
```

giữ lại.

```text
unused
```

bị loại.

Graph:

```text
ROOT
 │
 ▼
main
 │
 ▼
foo
 │
 ▼
bar
```

Các node không reachable:

```text
dead
```

---

# 12. Linker Roots

Không phải mọi symbol chỉ được giữ vì có relocation.

Root có thể là:

```text
entry point
exported symbol
dynamic export
init/fini
TLS callbacks
exception/unwind metadata
registration tables
reflection metadata
explicit @keep
linker-required symbol
```

Axiom cần một cơ chế:

```text
@keep
```

hoặc tương đương cho system-level code.

---

# 13. Section Merging

Input:

```text
a.o:
    .text
    .rodata

b.o:
    .text
    .rodata
```

Linker tạo:

```text
.text
    a.text
    b.text

.rodata
    a.rodata
    b.rodata
```

Nhưng không đơn giản append tất cả.

Cần:

```text
alignment
ordering
permissions
mergeability
relocation constraints
COMDAT
GC
```

---

# 14. Section Identity

Không nên dùng tên section làm identity.

Ví dụ:

```text
.text
```

chỉ là representation.

Internal:

```text
SectionId(42)
```

mới là identity.

Điều này tiếp tục nguyên tắc từ Object IR:

> Name is representation, ID is identity.

---

# 15. Virtual Address ≠ File Offset

Đây là một trong những điểm linker phải xử lý rất rõ.

Executable có:

```text
file offset
virtual address
RVA
alignment
segment
section
```

Ví dụ:

```text
file:
00001000

memory:
0x401000
```

Không được giả định:

```text
VA == file offset
```

Linker phải tính:

```text
SectionAddress
FileOffset
VirtualSize
RawSize
Alignment
```

---

# 16. Segment Layout

Đặc biệt ELF/Unix, section không phải đơn vị mapping cuối cùng.

Ví dụ:

```text
Sections:

.text
.rodata
.data
.bss
```

có thể tạo:

```text
PT_LOAD RX
    .text
    .rodata

PT_LOAD RW
    .data
    .bss
```

Từ đó đạt:

```text
W^X
```

Không tạo segment:

```text
RWX
```

trừ khi target policy/system-level option yêu cầu.

---

# 17. ELF Layout

MVP ELF executable:

```text
ELF Header

Program Headers

RX LOAD
    .text
    .rodata

RW LOAD
    .data
    .bss

TLS

Dynamic Metadata

Unwind

Debug (optional)
```

Entry:

```text
e_entry
```

trỏ đến startup symbol.

Ví dụ freestanding:

```text
_start
```

---

# 18. PE/Windows Layout

PE có cách tổ chức khác.

Khái niệm chính:

```text
DOS Header
PE Header
COFF Header
Optional Header
Section Table

.text
.rdata
.data
.pdata
.reloc
...
```

Linker phải tạo:

```text
RVA
Section RVA
ImageBase
SizeOfImage
SizeOfHeaders
EntryPoint
Import Directory
Export Directory
Relocation Directory
TLS Directory
Exception Directory
```

Ví dụ:

```text
EntryPoint RVA
    ↓
Axiom startup
    ↓
main
```

Không cần CRT nếu chương trình không yêu cầu nó.

---

# 19. Mach-O

macOS/iOS có mô hình:

```text
Mach-O Header
Load Commands
Segments
Sections
Symbols
Dyld Metadata
Code Signature
```

Ví dụ:

```text
__TEXT
    __text
    __cstring
    __const

__DATA
    __data
    __bss

__LINKEDIT
```

Linker phải tạo các `load commands` phù hợp.

Đặc biệt iOS còn có các ràng buộc platform như:

```text
code signing
entitlements
platform ABI
```

Phần signing có thể là một linker/post-link stage riêng thay vì nhét toàn bộ vào generic linker.

---

# 20. Relocation

Input:

```text
call foo
```

Machine encoder có thể chưa biết địa chỉ `foo`.

Object:

```text
.text
    call ??????
```

kèm:

```text
Relocation {
    offset
    kind
    symbol = foo
    addend
}
```

Linker biết:

```text
foo = 0x401230
```

và tính relocation.

---

# 21. Relocation Overflow

Không bao giờ:

```text
truncate silently
```

Ví dụ relocation cần:

```text
signed 32-bit displacement
```

nhưng khoảng cách là:

```text
> INT32_MAX
```

phải:

```text
AX1908 RelocationOverflow
```

hoặc linker relaxation phải thay thế bằng sequence khác nếu target hỗ trợ.

---

# 22. Linker Relaxation

Một số trường hợp:

```text
call foo
```

có thể dùng short/near form.

Hoặc:

```text
AArch64
ADR
```

không reach được target.

Linker có thể chuyển:

```text
short sequence
```

thành:

```text
long sequence
```

nhưng việc này cần được target backend thiết kế rõ.

Nguyên tắc:

> Encoder encode instruction; linker relaxes layout-dependent representation.

---

# 23. Static Linking

Axiom phải hỗ trợ:

```text
static executable
```

Ví dụ:

```text
main.ax
   ↓
axiom compile
   ↓
main.o
   ↓
libaxiom.a
   ↓
axiom-link
   ↓
main
```

Không cần:

```text
libc.so
ld.so
```

nếu chương trình freestanding hoặc Axiom runtime tối thiểu không cần chúng.

---

# 24. Dynamic Linking

Khi user yêu cầu:

```text
dynamic
```

linker phải hỗ trợ:

```text
ELF:
    .dynsym
    .dynstr
    .rela.plt
    .rela.dyn
    GOT
    PLT

PE:
    Import Table
    IAT
    DLL references

Mach-O:
    dyld info
    bind/rebase/export metadata
```

---

# 25. GOT / PLT

Ví dụ:

```text
printf
```

không nằm trong executable.

Thay vì:

```text
call absolute_address
```

có thể:

```text
call PLT
   ↓
GOT
   ↓
dynamic loader
   ↓
libc
```

Axiom linker phải hỗ trợ cả:

```text
eager binding
lazy binding
```

nhưng đây là **link policy**, không phải language semantic.

---

# 26. Import / Export

Axiom source:

```text
@export("my_api")
pub fn foo() {}
```

Object:

```text
symbol:
    name = my_api
    exported = true
```

Executable:

```text
Export Table
    my_api → address
```

Ngược lại:

```text
extern "C" {
    fn printf(...);
}
```

tạo:

```text
Undefined / Imported symbol
```

Linker quyết định nó là:

```text
static dependency
dynamic import
```

theo link mode.

---

# 27. TLS

Thread-local:

```text
static mut counter: i32
```

nếu khai báo TLS:

```text
@tls
static ...
```

Linker phải xử lý:

```text
TLS section
TLS alignment
TLS relocations
TLS module metadata
```

Target-specific:

```text
ELF TLS
PE TLS
Mach-O TLS
```

Nhưng compiler semantic model vẫn chỉ cần biết:

```text
StorageDomain = TLS
```

---

# 28. Entry Point

Axiom phải phân biệt:

```text
main()
```

với:

```text
process entry point
```

Ví dụ Linux:

```text
_start
   ↓
initialize minimal runtime
   ↓
main()
   ↓
exit syscall
```

Nếu user muốn freestanding:

```text
@entry
fn _start() -> never {
    ...
}
```

thì không cần:

```text
main
CRT
libc
```

---

# 29. Không có CRT bắt buộc

Đây là một điểm tôi đề nghị **đóng băng thành mục tiêu kiến trúc**:

```text
Axiom does not require CRT.
```

Có thể có:

```text
std::startup
```

nhưng đó là library/runtime component.

Không phải:

```text
language requirement
```

Ví dụ chương trình tối giản:

```text
@entry
fn _start() -> never {
    sys::linux::exit(42)
}
```

có thể tạo executable chỉ với:

```text
Axiom compiler
Axiom encoder
Axiom linker
```

không cần:

```text
gcc
clang
llvm
as
ld
libc
crt1.o
```

Đây sẽ là một **bootstrap milestone rất mạnh**.

---

# 30. `main()` Hosted Model

Ngược lại, chương trình bình thường:

```text
fn main() {
    println("Hello");
}
```

có thể được driver biến thành:

```text
_start
   ↓
axiom_startup
   ↓
runtime initialization
   ↓
main
   ↓
exit
```

Các phần runtime chỉ được link khi cần:

```text
allocator
panic
threads
TLS
async
unicode
filesystem
network
```

Không có monolithic runtime.

---

# 31. Initialization / Finalization

Một số platform cần:

```text
.init_array
.fini_array
```

hoặc tương đương.

Axiom không nên tạo chúng mặc định.

Chỉ khi có:

```text
global initialization
runtime registration
```

mới phát sinh.

Mục tiêu:

```text
No global constructor tax
```

cho chương trình không cần nó.

---

# 32. PIE / PIC

Linker phải phân biệt:

```text
static non-PIE
PIE
shared library
position-independent code
```

Compiler/machine backend tạo relocation model phù hợp.

Ví dụ:

```text
CodeModel
RelocationModel
```

là target/link configuration.

Không đưa chúng vào semantic language.

---

# 33. Section GC + `@keep`

Một API plugin có thể không có static reference nhưng cần export.

Ví dụ:

```text
@export("plugin_init")
@keep
fn plugin_init() {}
```

Linker root:

```text
plugin_init
```

do đó không bị section GC loại bỏ.

---

# 34. Debug / Unwind

Linker phải merge:

```text
Object A debug
Object B debug
Object C debug
```

thành:

```text
final DebugInfo
```

và tương tự:

```text
UnwindInfo
```

Nhưng linker không hiểu semantic source-level ownership.

Nó chỉ preserve/relocate metadata.

---

# 35. Deterministic Linking

Hai lần:

```text
axiom link main.o
```

phải tạo binary giống nhau nếu input/config giống nhau.

Không:

```text
timestamp
random build ID
temporary absolute path
unordered hash-map iteration
```

trừ metadata explicitly requested.

Điều này rất quan trọng cho:

- bootstrap
- compiler testing
- reproducible builds
- binary diff
- AI agent development

---

# 36. Linker Pipeline hoàn chỉnh

Tôi đề xuất pipeline chính thức:

```text
Input Objects
      ↓
Object Reader
      ↓
Target Validation
      ↓
Build Link Graph
      ↓
Symbol Resolution
      ↓
Archive Extraction
      ↓
COMDAT Selection
      ↓
Section GC
      ↓
ICF
      ↓
Section Merge
      ↓
Section Ordering
      ↓
Address Assignment
      ↓
Segment Construction
      ↓
TLS Layout
      ↓
Import / Export Layout
      ↓
GOT / PLT Layout
      ↓
Relocation Resolution
      ↓
Branch / Layout Relaxation
      ↓
Final Address Assignment
      ↓
Relocation Application
      ↓
Debug / Unwind Finalization
      ↓
Entry Point
      ↓
Executable Layout
      ↓
Executable Writer
      ↓
Executable Verifier
```

Một số target sẽ thay đổi thứ tự một chút, nhưng semantic stages này nên giữ ổn định.

---

# 37. Executable Verifier

Axiom nên có:

```text
ExecutableVerifier
```

trước khi ghi file cuối cùng hoặc ngay sau khi ghi.

Kiểm tra:

```text
entry point valid
sections valid
segments valid
alignment valid
symbols valid
relocations resolved
no unresolved required symbols
imports valid
exports valid
TLS valid
segment permissions valid
W^X policy
file offsets valid
virtual addresses valid
address ranges valid
architecture valid
ABI valid
```

Ví dụ:

```text
.text
    RX

.data
    RW
```

nhưng nếu:

```text
.text
    RWX
```

thì verifier có thể reject theo security profile.

---

# 38. Linker Architecture

Repository:

```text
compiler/
└── linker/
    ├── reader/
    │   ├── elf/
    │   ├── coff/
    │   └── macho/
    │
    ├── ir/
    │
    ├── symbol/
    ├── archive/
    ├── comdat/
    ├── icf/
    ├── gc/
    ├── layout/
    ├── relocation/
    ├── tls/
    ├── dynamic/
    ├── entry/
    ├── debug/
    ├── unwind/
    │
    ├── elf/
    ├── pe/
    ├── macho/
    └── wasm/
```

Không nên:

```text
elf_linker.c
    20,000 lines
```

rồi copy thành:

```text
windows_linker.c
mac_linker.c
```

Generic linker phải xử lý phần lớn logic.

Target backend chỉ xử lý những phần thực sự target-specific.

---

# 39. Linker API

Có thể đóng băng interface gần như:

```text
Linker {
    add_object(ObjectFile)
    add_archive(Archive)
    add_shared_library(SharedLibrary)

    set_target(Target)
    set_entry(Symbol)
    set_output_kind(OutputKind)

    set_gc_sections(bool)
    set_icf(ICFPolicy)
    set_pie(bool)
    set_static(bool)

    link() -> Result<Executable, LinkError>
}
```

Output:

```text
Executable {
    format
    target
    segments
    sections
    symbols
    entry
    bytes
}
```

---

# 40. Linker CLI

Driver:

```bash
axiom link main.o -o app
```

Ví dụ:

```bash
axiom link main.o \
    --target=x86_64-linux \
    --gc-sections \
    -o app
```

Static:

```bash
axiom link main.o --static -o app
```

PIE:

```bash
axiom link main.o --pie -o app
```

Freestanding:

```bash
axiom link main.o \
    --freestanding \
    --entry=_start \
    -o app
```

Debug:

```bash
axiom link main.o --debug -o app
```

---

# 41. Runtime dependency graph

Đây là chỗ Axiom có thể khác đáng kể so với các toolchain truyền thống.

Ví dụ:

```text
Program
 │
 ├── Vec
 │
 ├── File
 │
 └── Thread
```

Compiler/linker có thể xác định:

```text
Vec
 └── allocator

File
 └── os::fs

Thread
 ├── thread
 └── TLS
```

Nếu chương trình chỉ:

```text
fn main() {
    let x = 42;
}
```

thì executable có thể không cần:

```text
allocator
TLS
thread runtime
async runtime
GC
reflection runtime
```

Đây là **capability-driven runtime linking**.

---

# 42. Các invariant mới

Tôi đề nghị đóng băng nhóm:

### ALINK-46 — Linker Operates On LinkIR

Linker core không phụ thuộc trực tiếp vào một object format.

### ALINK-47 — Object Format Is An Input/Output Adapter

ELF/COFF/Mach-O/WASM được chuyển đổi qua adapter.

### ALINK-48 — Target Compatibility Is Verified

Không link các object target không tương thích.

### ALINK-49 — Symbol Resolution Is Deterministic

Cùng input/config → cùng resolution.

### ALINK-50 — Strong Symbol Conflict Is Diagnosed

Không silently chọn một definition.

### ALINK-51 — Weak Resolution Is Explicit

Weak symbol semantics phụ thuộc link policy/target ABI.

### ALINK-52 — Archive Extraction Is Demand Driven

Chỉ extract member cần thiết.

### ALINK-53 — COMDAT Selection Is Explicit

Không tự ý loại symbol tương đương.

### ALINK-54 — ICF Requires Address-Safety

Không fold code nếu observable identity bị thay đổi.

### ALINK-55 — Section GC Is Root Driven

Chỉ giữ reachable hoặc explicitly rooted content.

### ALINK-56 — `@keep` Can Establish Linker Root

### ALINK-57 — Section Identity Is Independent Of Section Name

### ALINK-58 — Virtual Address Is Distinct From File Offset

### ALINK-59 — Segment Permissions Are Explicit

### ALINK-60 — W^X Is Default Security Policy

### ALINK-61 — Relocation Overflow Is Diagnosed

### ALINK-62 — Relocations Are Fully Resolved For Static Output

### ALINK-63 — Undefined Symbols Are Allowed Only When Output Format Permits Them

### ALINK-64 — Dynamic Imports Are Explicit

### ALINK-65 — GOT/PLT Is Link Policy

### ALINK-66 — TLS Layout Is Target Specific

### ALINK-67 — Entry Point Is Explicit In Executable Metadata

### ALINK-68 — `main` Is Not Necessarily The Machine Entry Point

### ALINK-69 — CRT Is Not A Language Requirement

### ALINK-70 — Runtime Components Are Demand Driven

### ALINK-71 — Static Linking Requires No Dynamic Loader

### ALINK-72 — Dynamic Linking Requires Explicit Loader Metadata

### ALINK-73 — PIE/PIC Is A Target/Link Configuration

### ALINK-74 — Debug Information Is Optional

### ALINK-75 — Unwind Information Is Optional

### ALINK-76 — Linker Does Not Reinterpret Axiom Semantics

### ALINK-77 — Linker Does Not Perform Ownership Verification

### ALINK-78 — Linker Does Not Perform Type Checking

### ALINK-79 — Linker Does Not Require LLVM

### ALINK-80 — Linker Does Not Require An External Linker

### ALINK-81 — Linking Is Deterministic

### ALINK-82 — Executable Layout Is Independently Verifiable

### ALINK-83 — Native Executable Generation Is Self-Contained

### ALINK-84 — Runtime Dependency Is Capability Driven

### ALINK-85 — Freestanding Executables May Have No Runtime

### ALINK-86 — No Mandatory libc Dependency

### ALINK-87 — Platform ABI Is Preserved

### ALINK-88 — Output Format Is Selected By Target

### ALINK-89 — Linker Backends Are Replaceable

### ALINK-90 — Final Executable Must Pass Executable Verification

---

# 43. Điểm rất quan trọng cho mục tiêu Axiom

Sau LINKER-002, kiến trúc của Axiom đã có một đường đi hoàn chỉnh:

```text
Axiom
  ↓
AST
  ↓
HIR
  ↓
Typed HIR
  ↓
Ownership / Capability
  ↓
MIR
  ↓
Optimization
  ↓
ABI
  ↓
LIR
  ↓
Machine IR
  ↓
Register Allocation
  ↓
Machine Encoding
  ↓
Object
  ↓
Native Linker
  ↓
Native Executable
```

Và **không còn dependency bắt buộc vào LLVM/Clang/GCC/assembler/linker bên ngoài** ở kiến trúc cuối cùng.

LLVM chỉ còn vị trí:

```text
bootstrap / differential testing / validation
```

chứ không phải:

```text
Axiom architecture
```

Đây là ranh giới rất quan trọng.

---

## Mốc bootstrap tiếp theo

Sau LINKER-002, bước hợp lý nhất **không phải tiếp tục thêm một đống tính năng ngôn ngữ**.

Nên chuyển sang:

# `TOOLCHAIN-001 — Axiom Native Build Driver`

để hợp nhất:

```text
axiom compile
axiom assemble        ← eventually unnecessary externally
axiom link
axiom build
axiom run
axiom test
```

và quan trọng hơn:

```text
source
  ↓
compiler
  ↓
object
  ↓
native linker
  ↓
executable
```

thành **một vertical slice có thể tự chạy**.

Sau đó mới tiến tới mốc cực kỳ quan trọng:

```text
BOOTSTRAP-002
Axiom compiler written in Axiom
        ↓
Axiom compiler compiles itself
        ↓
self-hosting
```

Đây mới là lúc chúng ta kiểm chứng xem toàn bộ thiết kế hiện tại có thực sự đủ để trở thành một ngôn ngữ/compiler độc lập hay chưa.