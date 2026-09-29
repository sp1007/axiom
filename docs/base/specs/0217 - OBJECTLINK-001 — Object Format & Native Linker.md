Tiếp tục với **OBJECT/LINK-001 — Object Format & Native Linker**.

Đây là bước đưa Axiom từ “compiler có thể phát machine code” thành **compiler có thể tự tạo executable thật**.

# OBJECT/LINK-001 — Object Format & Native Linker

## 1. Mục tiêu cuối

Kiến trúc cuối cùng phải đạt:

```text
Axiom Source
    ↓
Axiom Compiler
    ↓
Machine Code
    ↓
Axiom Object Writer
    ↓
Axiom Object
    ↓
Axiom Linker
    ↓
Native Executable
```

Không cần:

```text
LLVM
Clang
GCC
NASM
GAS
LLD
GNU ld
MSVC linker
```

trong **final toolchain**.

Trong bootstrap phase có thể dùng chúng làm reference/backend tạm thời.

---

# 2. Không nên tự viết mọi thứ ngay lập tức

Có một điểm cần phân biệt:

> **Không phụ thuộc cuối cùng ≠ phải tự viết ngay từ ngày đầu.**

Roadmap:

```text
Phase 1:
Axiom → LLVM/system linker

Phase 2:
Axiom → own Machine Code
       → system linker

Phase 3:
Axiom → own Object
       → own linker

Phase 4:
Axiom compiler tự compile chính nó
       ↓
self-hosted native toolchain
```

Như vậy rủi ro giảm rất nhiều.

---

# 3. Object file là gì?

Compiler tạo:

```text
foo.o
```

Object chứa:

```text
machine code
read-only data
writable data
symbols
relocations
debug information
unwind information
TLS
section metadata
```

Nó **chưa phải executable hoàn chỉnh**.

Ví dụ:

```text
foo.o
 ├── .text
 ├── .rodata
 ├── .data
 ├── .bss
 ├── symbols
 ├── relocations
 └── debug/unwind
```

---

# 4. Axiom Object Model

Không nên để frontend biết ELF/COFF/Mach-O.

Internal object representation:

```text
ObjectFile {
    format
    architecture
    sections[]
    symbols[]
    relocations[]
    comdat_groups[]
    tls
    debug
    unwind
}
```

Sau đó:

```text
ObjectWriter
    ├── ELFWriter
    ├── COFFWriter
    ├── MachOWriter
    └── WasmWriter
```

---

# 5. Section

Internal section:

```text
Section {
    name
    type
    flags
    alignment
    data
    relocations
}
```

Các section phổ biến:

```text
.text
.rodata
.data
.bss
.tdata
.tbss
```

Debug:

```text
.debug_info
.debug_line
...
```

hoặc target tương ứng.

---

# 6. `.text`

Chứa:

```text
machine instructions
```

Ví dụ:

```text
.text
    main
    foo
    bar
```

Code alignment có thể được backend/linker tối ưu.

---

# 7. `.rodata`

Dùng cho:

```text
constant strings
constant arrays
read-only tables
jump tables
```

Ví dụ:

```axiom
const message = "Hello"
```

có thể:

```text
.rodata:
    "Hello"
```

---

# 8. `.data`

Dữ liệu mutable có initializer:

```axiom
static var counter: i32 = 10
```

→

```text
.data
```

---

# 9. `.bss`

Dữ liệu zero-initialized:

```axiom
static var buffer: [u8; 4096]
```

có thể không cần lưu 4096 byte trong file.

Object chỉ ghi:

```text
.bss
size = 4096
```

Loader tự tạo vùng zero-filled.

---

# 10. TLS

Axiom đã xác định TLS là storage contract.

Object model cần:

```text
.tdata
.tbss
```

hoặc tương đương target.

Ví dụ:

```axiom
@tls
static var counter: u64
```

không được biến thành global thông thường.

---

# 11. Symbol

Mỗi externally relevant entity có symbol:

```text
Symbol {
    name
    section
    offset
    size
    binding
    visibility
    type
}
```

Ví dụ:

```text
foo
bar
main
```

---

# 12. Symbol binding

Ít nhất:

```text
Local
Global
Weak
Undefined
```

Ví dụ:

```text
foo:
    Global
```

Symbol external:

```text
printf:
    Undefined
```

Linker sẽ tìm definition từ object/library khác.

---

# 13. Weak symbol

Cần hỗ trợ weak để tương thích native ecosystem.

Ví dụ:

```text
weak foo
```

Nếu có strong:

```text
foo strong
foo weak
```

→ strong thắng.

Nhưng weak không nên trở thành cơ chế ngôn ngữ Axiom phổ biến.

Đây chủ yếu là linker/FFI feature.

---

# 14. Relocation

Đây là phần cốt lõi của linker.

Ví dụ:

```text
call foo
```

compiler chưa biết địa chỉ cuối cùng của `foo`.

Object ghi:

```text
Relocation {
    offset
    type
    symbol = foo
    addend
}
```

Linker giải quyết sau.

---

# 15. Không hard-code relocation vào compiler

Machine encoder chỉ biết:

```text
RelocKind::Call
RelocKind::Absolute
RelocKind::PCRelative
RelocKind::TLS
```

Target object writer map sang:

```text
ELF R_X86_64_PC32
ELF R_X86_64_PLT32
...
```

hoặc COFF/Mach-O tương ứng.

---

# 16. Relocation types

Internal model nên có:

```text
Absolute
PCRelative
Relative
SectionRelative
Got
Plt
Tls
ThreadLocal
ImageRelative
Branch
Jump
```

Không cần expose hết cho source.

---

# 17. PC-relative

Modern native code thường dùng PC-relative addressing.

Ví dụ:

```text
call foo
```

không nhất thiết encode absolute address.

Có thể:

```text
foo_address - next_instruction
```

Điều này hỗ trợ:

```text
PIE
shared libraries
position-independent code
ASLR
```

---

# 18. Static linking

Ví dụ:

```text
main.o
math.o
string.o
```

link:

```text
axiom link main.o math.o string.o -o app
```

Linker:

```text
parse objects
 ↓
resolve symbols
 ↓
select sections
 ↓
assign addresses
 ↓
apply relocations
 ↓
generate executable
```

---

# 19. Archive / static library

Static library:

```text
libfoo.a
```

về bản chất:

```text
archive {
    foo.o
    bar.o
    baz.o
}
```

Linker chỉ lấy member cần thiết.

Điều này cho phép:

```text
dead library code
```

không đi vào executable.

---

# 20. Dead stripping

Axiom linker nên hỗ trợ:

```text
--gc-sections
```

conceptually:

```text
entry
 ↓
main
 ↓
foo
 ↓
bar
```

chỉ giữ reachable symbols/sections.

Nếu:

```text
unused()
```

không được reference:

```text
→ remove
```

---

# 21. Section-level dead stripping

Không chỉ function-level.

Ví dụ:

```text
foo
 ├── hot code
 ├── cold code
 └── unused helper
```

Mỗi function nên có thể nằm trong COMDAT/independent section khi cần.

Điều này giúp linker loại bỏ chính xác hơn.

---

# 22. COMDAT / weak ODR-like mechanism

Generic monomorphization có thể tạo:

```text
Vec<i32>::push
```

ở nhiều object.

Không muốn duplicate symbol.

Cần một cơ chế:

```text
COMDAT / link-once
```

Internal abstraction:

```text
LinkOnce {
    key
    selection
}
```

Target writer map sang:

```text
COMDAT
weak/linkonce
```

tùy format.

---

# 23. Generic code và linker

Ví dụ:

```axiom
fn add<T: Number>(a: T, b: T) -> T
```

Monomorphization:

```text
add<i32>
add<i64>
add<f32>
```

Compiler có thể tạo code riêng.

Nhưng nếu nhiều module yêu cầu:

```text
add<i32>
```

compiler/linker phải deduplicate.

Đây là lý do linker phải hiểu link-once semantics.

---

# 24. Internal vs external symbol

Axiom:

```axiom
fn helper()
```

nếu private:

```text
local symbol
```

Còn:

```axiom
@export("foo")
pub fn api()
```

→ external/exported symbol.

Không nên mặc định mọi `pub` thành binary-exported symbol.

---

# 25. Entry point

Executable cần entry point.

Axiom source:

```axiom
fn main() {
}
```

không nhất thiết trực tiếp là OS entry.

Có thể:

```text
OS entry
   ↓
Axiom startup
   ↓
initialize TLS
initialize runtime components
initialize globals
   ↓
main()
   ↓
exit
```

---

# 26. Freestanding entry point

Trong freestanding:

```axiom
@entry
fn _start() -> never
```

có thể trực tiếp là binary entry.

Không cần:

```text
crt0
libc
```

nếu program tự cung cấp startup.

---

# 27. Hosted startup

Hosted program:

```text
_start
 ↓
runtime initialization
 ↓
axiom_main
 ↓
exit
```

Runtime initialization chỉ được link nếu profile yêu cầu.

---

# 28. `main` ABI

Không nên hard-code một signature duy nhất.

Có thể:

```axiom
fn main()
```

hoặc:

```axiom
fn main(args: Args) -> Result<(), Error>
```

Compiler/runtime adapter lower về OS entry ABI.

Ví dụ:

```text
Windows:
WinMain / process startup conventions

Linux:
_start

macOS:
Mach-O process entry
```

Programmer không cần xử lý trực tiếp.

---

# 29. Exit code

Semantic library:

```axiom
process.exit(code)
```

hoặc:

```axiom
main() -> i32
```

có thể map thành:

```text
OS exit status
```

Không nên để OS-specific semantics rò vào Core.

---

# 30. Dynamic linking

Axiom linker phải eventually hỗ trợ:

```text
ELF:
    .so

Windows:
    .dll + import library

macOS:
    .dylib
```

Pipeline:

```text
Executable
   ↓
imports
   ↓
dynamic loader
   ↓
shared library
```

---

# 31. GOT/PLT

Linux ELF shared object thường cần:

```text
GOT
PLT
```

Axiom linker phải có abstraction:

```text
GlobalOffsetTable
ProcedureLinkageTable
```

nhưng không nên đưa chúng vào LIR.

Chúng là object/link layer.

---

# 32. Windows PE/COFF

Cần:

```text
COFF object
PE executable
PE DLL
Import Table
Export Table
Relocations
TLS
Exception data
```

Internal linker model không nên phụ thuộc ELF.

Ví dụ:

```text
Linker
 ├── ELF
 ├── PE
 └── Mach-O
```

---

# 33. Mach-O

macOS/iOS:

```text
Mach-O
segments
sections
symbols
relocations
exports
imports
TLS
unwind
code signing requirements
```

iOS đặc biệt cần lưu ý:

> Native executable generation không đồng nghĩa binary có thể chạy trên iOS.

Signing/provisioning là một tầng platform deployment riêng.

---

# 34. Code signing

Không nên nhét signing vào compiler core.

Architecture:

```text
Axiom Compiler
      ↓
Unsigned Mach-O
      ↓
Platform Tool
      ↓
Code Signing
      ↓
Installable App
```

Nếu sau này muốn Axiom tự làm signing, đó là toolchain layer:

```text
axiom sign
```

không phải semantic compiler.

---

# 35. WASM

WASM không cần traditional native linker.

Axiom có:

```text
WasmObject / WasmModule
```

và:

```text
WasmLinker
```

Các khái niệm tương đương:

```text
imports
exports
functions
tables
memory
globals
data segments
```

---

# 36. Linker symbol resolution

Algorithm cơ bản:

```text
1. Load all objects
2. Collect symbols
3. Resolve strong definitions
4. Resolve weak definitions
5. Detect duplicate strong symbols
6. Resolve undefined references
7. Pull required archive members
8. Build dependency graph
9. Layout sections
10. Assign addresses
11. Apply relocations
12. Generate output
```

---

# 37. Archive extraction

Ví dụ:

```text
main.o → foo
libA.a:
    foo.o
    bar.o
    baz.o
```

Linker chỉ extract:

```text
foo.o
```

không cần:

```text
bar.o
baz.o
```

Sau khi `foo.o` được thêm, nó có thể tạo dependency mới.

Do đó cần lặp đến fixed point:

```text
while unresolved_symbols change:
    extract required archive members
```

---

# 38. Circular dependencies

Static libraries:

```text
A → B
B → A
```

cần xử lý deterministic.

Linker graph phải hỗ trợ cycles thay vì phụ thuộc thứ tự may rủi.

---

# 39. Link order

Axiom nên cố giảm sự phụ thuộc vào linker order.

Thay vì:

```bash
a b c
```

để giải quyết symbol theo thứ tự, linker internal graph nên có:

```text
dependency resolution
```

Tuy nhiên khi tương tác với native ecosystem, phải tôn trọng semantics của foreign libraries.

---

# 40. Symbol interposition

Shared library có thể cho phép:

```text
library A defines foo
application defines foo
```

và runtime loader chọn một definition tùy platform.

Đây là nguồn tối ưu hóa khó.

Axiom internal libraries nên ưu tiên:

```text
hidden/internal visibility
```

khi không cần interposition.

---

# 41. Visibility

Internal symbol:

```text
Hidden
```

Public dynamic symbol:

```text
Default
```

Private:

```text
Local
```

Compiler có thể dùng visibility để tối ưu:

```text
direct call
no PLT
devirtualization
dead stripping
```

---

# 42. LTO

Axiom nên thiết kế linker để sau này hỗ trợ:

```text
LTO
```

nhưng **LTO không phải object linker cơ bản**.

Pipeline:

```text
Axiom module
    ↓
IR/object
    ↓
Linker
```

hoặc:

```text
Axiom IR
    ↓
Whole-program optimization
    ↓
Machine code
    ↓
Link
```

Về sau có thể:

```text
ThinLTO-like
```

nhưng không cần clone LLVM design.

---

# 43. Incremental linking

Compiler lớn cần:

```text
incremental build
```

Có thể giữ:

```text
object cache
symbol cache
dependency graph
layout cache
```

Nhưng final binary vẫn phải deterministic.

---

# 44. Deterministic build

Cùng:

```text
source
compiler
target
flags
dependencies
```

phải tạo:

```text
same semantics
```

và ideally:

```text
same binary
```

trừ metadata có timestamp/random ID.

Do đó:

```text
SOURCE_DATE_EPOCH
```

và deterministic UUID/build-id policy nên được thiết kế từ đầu.

---

# 45. Reproducible build

Compiler/linker cần loại bỏ:

```text
random ordering
filesystem enumeration order
timestamps
machine-local paths
random symbol IDs
```

hoặc đưa chúng vào explicit reproducibility settings.

Đây rất quan trọng cho compiler bootstrap và debugging.

---

# 46. Relocation overflow

Ví dụ branch target quá xa:

```text
short jump
```

không đủ displacement.

Linker phải có:

```text
relaxation
```

hoặc:

```text
branch island / veneer / long jump
```

Target backend có thể chọn instruction đủ lớn từ đầu hoặc linker relax sau.

---

# 47. Linker relaxation

Đặc biệt quan trọng với:

```text
RISC-V
ARM
```

Ví dụ:

```text
long sequence
```

có thể rút xuống:

```text
short sequence
```

khi linker biết địa chỉ thật.

Do đó linker không chỉ “copy bytes”.

Nó là một **code layout optimizer ở mức binary**.

---

# 48. Section layout

Linker quyết định:

```text
.text
.rodata
.data
.bss
TLS
```

địa chỉ cuối cùng.

Ví dụ conceptually:

```text
.text
.rodata
.data
.bss
```

với alignment phù hợp.

Không hard-code địa chỉ trong compiler.

---

# 49. Segment

ELF/PE/Mach-O thường map sections vào segments.

Ví dụ ELF:

```text
PT_LOAD RX
PT_LOAD RW
PT_TLS
PT_GNU_STACK
...
```

Linker phải tạo segment permissions đúng:

```text
R
RW
RX
```

Không tạo:

```text
RWX
```

trừ khi explicitly required bởi unusual platform semantics.

---

# 50. W^X

Axiom linker nên mặc định hỗ trợ:

> **Write XOR Execute**

Code:

```text
RX
```

Data:

```text
RW
```

Không:

```text
RWX
```

Điều này vừa an toàn vừa phù hợp OS hiện đại.

---

# 51. TLS layout

Linker phải gom:

```text
.tdata
.tbss
```

và tạo TLS metadata tương ứng.

Axiom source không cần biết:

```text
ELF TLS model
PE TLS directory
Mach-O TLS
```

---

# 52. Relocation model

Compiler target có thể chọn:

```text
Static
PIC
PIE
Shared
```

Ví dụ:

```bash
axiom build --pic
axiom build --pie
```

Nhưng semantic language không thay đổi.

---

# 53. PIE

Executable hiện đại nên hỗ trợ:

```text
PIE
```

cho ASLR.

Linker đảm bảo:

```text
position-independent code/data references
```

khi target/profile yêu cầu.

---

# 54. Shared library ABI

Shared library cần:

```text
exported symbols
ABI version
dependency metadata
relocations
TLS
unwind
initialization/finalization
```

Axiom package ABI có thể bổ sung metadata riêng:

```text
axiom_abi_version
```

nhưng native loader không được phụ thuộc vào Axiom metadata nếu library chỉ expose C ABI.

---

# 55. Init / fini

Global initialization cần xử lý.

Ví dụ:

```axiom
static CONFIG: Config = make_config()
```

Nếu initializer không phải pure static data:

```text
startup function
```

được tạo.

Nhưng không nên biến mọi static initialization thành runtime startup.

Ưu tiên:

```text
compile-time initialization
```

khi có thể.

---

# 56. Global initialization order

Không nên cho phép kiểu C++:

```text
module A global constructor
module B global constructor
```

với thứ tự khó đoán.

Axiom nên ưu tiên:

```text
constant initialization
lazy initialization
OnceLock
explicit init()
```

Runtime global constructors chỉ là platform/interop mechanism.

Điều này làm startup deterministic hơn.

---

# 57. Destructor shutdown

Tương tự:

```text
global Drop
```

không nên mặc định tạo một hệ thống destructor toàn chương trình khổng lồ.

Chỉ những resource có lifecycle semantics cần thiết mới đăng ký cleanup.

Freestanding có thể:

```text
never return
```

nên không cần global shutdown.

---

# 58. Exception / unwind data

Object linker phải giữ:

```text
unwind sections
```

nếu profile:

```text
panic=unwind
```

Ví dụ:

```text
ELF:
    .eh_frame

Windows:
    .pdata
    .xdata
```

Mach-O có cơ chế tương ứng.

Linker không được loại bỏ chúng nếu unwind ABI cần.

---

# 59. Debug info

Debug object có thể chứa:

```text
source → function
source line → machine address
local variable → register/stack
type information
inline call stack
```

Axiom compiler nên ưu tiên DWARF làm format cross-platform đầu tiên cho Unix-like targets, sau đó hỗ trợ PDB/CodeView trên Windows.

---

# 60. Debug information không ảnh hưởng semantics

Build:

```bash
axiom build
```

và:

```bash
axiom build --debug
```

phải tạo cùng program semantics.

Debug info chỉ là metadata.

---

# 61. Linker diagnostics

Không chỉ:

```text
undefined reference
```

Axiom linker nên báo structured diagnostic:

```text
LNK001:
undefined symbol

symbol:
    foo

referenced from:
    main.o:0x120

target:
    x86_64-linux

suggestion:
    missing library: libfoo
```

Điều này đặc biệt phù hợp với mục tiêu AI-friendly tooling.

---

# 62. Linker map

Cho phép:

```bash
axiom link --map
```

sinh:

```text
main       .text  0x1000  120
foo        .text  0x1080   42
bar        .text  0x10B0   73
```

và:

```text
section sizes
symbol origins
dead-stripped symbols
relocations
```

Rất hữu ích để tối ưu binary size.

---

# 63. Binary size budget

Với mục tiêu binary nhỏ, compiler nên có:

```text
--size-report
```

Ví dụ:

```text
.text      12.4 KB
.rodata     2.1 KB
.data       0.3 KB
.bss        4.0 KB
unwind      1.2 KB
debug      0
```

Có thể chỉ ra:

```text
largest symbols
largest dependencies
runtime components pulled
```

---

# 64. Runtime dependency graph

Linker có thể xuất:

```text
main
 ├── print
 │    ├── stdout
 │    └── utf8
 └── Vec
      └── allocator
```

Điều này giúp kiểm soát:

> “Tôi viết chương trình 20 dòng, tại sao binary lại 800 KB?”

---

# 65. Axiom Linker API

Internal:

```text
Linker {
    add_object()
    add_archive()
    add_shared_library()
    define_symbol()
    resolve_symbols()
    layout()
    relocate()
    emit()
}
```

Target-specific:

```text
ELFLinker
PELinker
MachOLinker
WasmLinker
```

nhưng dùng chung symbol/section/relocation model.

---

# 66. Executable abstraction

Internal:

```text
Executable {
    format
    target
    entry
    segments
    sections
    imports
    exports
    relocations
    tls
    unwind
    debug
}
```

Sau đó:

```text
ELFExecutableWriter
PEExecutableWriter
MachOExecutableWriter
```

---

# 67. OS loader boundary

Một nguyên tắc quan trọng:

> Axiom Linker tạo binary phù hợp với OS loader; nó không tự trở thành OS loader.

Ví dụ Linux:

```text
Axiom Linker
    ↓
ELF
    ↓
Linux kernel / dynamic loader
```

Windows:

```text
Axiom Linker
    ↓
PE
    ↓
Windows loader
```

Điều này giữ compiler architecture sạch.

---

# 68. Dynamic loader

Không cần tự viết trong Axiom toolchain cho OS thông thường.

Linux:

```text
ld.so
```

Windows:

```text
Windows loader
```

macOS:

```text
dyld
```

Axiom chỉ cần tạo đúng ABI.

---

# 69. Static executable

Mục tiêu lý tưởng:

```bash
axiom build --static
```

→ executable không cần dynamic runtime/library ngoài OS/kernel interface.

Điều này cực kỳ hữu ích cho:

```text
CLI
containers
embedded
single-file deployment
```

---

# 70. Freestanding binary

Ví dụ:

```text
axiom build --target=x86_64-none
```

có thể tạo:

```text
raw binary
ELF kernel
UEFI PE
firmware image
```

về sau.

---

# 71. UEFI

Đây là một target thú vị cho Axiom vì:

```text
UEFI application
```

thường sử dụng PE/COFF.

Axiom có thể eventually:

```text
Axiom
 ↓
x86_64 Machine Code
 ↓
PE/COFF
 ↓
UEFI application
```

mà không cần Windows runtime.

---

# 72. Object/linker invariants

Chốt nhóm:

### ALINK-20
**Object Representation Is Independent From Source Semantics**

### ALINK-21
**Object Files Contain Relocatable Machine Code**

### ALINK-22
**Symbols Are Explicit Linker Entities**

### ALINK-23
**Undefined Symbols Are Resolved At Link Time**

### ALINK-24
**Relocations Are Explicit**

### ALINK-25
**Relocation Semantics Are Target Specific**

### ALINK-26
**Section Layout Is A Linker Responsibility**

### ALINK-27
**Segment Layout Is A Linker Responsibility**

### ALINK-28
**Static Archives Are Collections Of Objects**

### ALINK-29
**Archive Members Are Extracted Only When Needed**

### ALINK-30
**Strong Symbol Conflicts Are Errors**

### ALINK-31
**Weak Symbols Do Not Override Strong Definitions**

### ALINK-32
**COMDAT/LinkOnce Prevents Duplicate Generic Code**

### ALINK-33
**Dead Code May Be Removed At Link Time**

### ALINK-34
**Binary Export Is Explicit**

### ALINK-35
**Source Visibility Does Not Imply Binary Export**

### ALINK-36
**TLS Is Preserved Through Object And Link Stages**

### ALINK-37
**Unwind Metadata Is Preserved When Required**

### ALINK-38
**Debug Information Is Non-Semantic Metadata**

### ALINK-39
**Executable Entry Point Is An Explicit Linker Property**

### ALINK-40
**Hosted Startup And Freestanding Entry Are Distinct**

### ALINK-41
**Global Initialization Must Be Deterministic**

### ALINK-42
**Global Initialization Should Prefer Compile-Time Initialization**

### ALINK-43
**Axiom Linker Must Support Position-Independent Code**

### ALINK-44
**Axiom Linker Must Support PIE**

### ALINK-45
**Axiom Linker Must Preserve W^X By Default**

### ALINK-46
**Object Format Is Independent From Axiom IR**

### ALINK-47
**ELF, PE/COFF, Mach-O And WASM Are Backend Formats**

### ALINK-48
**Native Executable Generation Does Not Require A Foreign Compiler**

### ALINK-49
**Final Axiom Toolchain Must Be Capable Of Independent Linking**

### ALINK-50
**Linking Must Be Deterministic**

### ALINK-51
**Reproducible Builds Are A Toolchain Goal**

### ALINK-52
**Linker Diagnostics Are Structured**

### ALINK-53
**Linker Must Not Infer Foreign Allocation Ownership**

### ALINK-54
**Dynamic Loading Is An OS Boundary**

### ALINK-55
**Code Signing Is A Deployment Layer**

### ALINK-56
**Platform-Specific Executable Metadata Must Not Leak Into Core Language Semantics**

---

# 73. Bây giờ toàn bộ native compilation chain đã hình thành

Ta đã đi từ:

```text
TYPE
 ↓
ABI
 ↓
LIR
 ↓
MACHINE IR
 ↓
OBJECT
 ↓
LINK
```

thành:

```text
                  AXIOM LANGUAGE
                        │
                        ▼
               ┌─────────────────┐
               │      MIR        │
               │ ownership       │
               │ capability      │
               │ lifetime        │
               │ concurrency     │
               └────────┬────────┘
                        │
                        ▼
               ┌─────────────────┐
               │      LIR        │
               │ SSA             │
               │ memory          │
               │ calls           │
               │ atomics         │
               └────────┬────────┘
                        │
                        ▼
               ┌─────────────────┐
               │   MACHINE IR   │
               │ registers       │
               │ instructions    │
               │ stack frame     │
               └────────┬────────┘
                        │
                        ▼
               ┌─────────────────┐
               │ MACHINE ENCODER │
               └────────┬────────┘
                        │
                        ▼
               ┌─────────────────┐
               │ OBJECT WRITER   │
               └────────┬────────┘
                        │
                        ▼
               ┌─────────────────┐
               │ AXIOM LINKER    │
               └────────┬────────┘
                        │
             ┌──────────┼──────────┐
             ▼          ▼          ▼
           ELF         PE        Mach-O
```

Đây là **xương sống của native Axiom compiler**.

---

# 74. Bước tiếp theo: BOOTSTRAP-001

Có một việc **không nên tiếp tục trì hoãn**.

Chúng ta đã thiết kế khá nhiều semantics. Nếu cứ tiếp tục thêm language features mà chưa xác định cách compiler được xây dựng, spec sẽ ngày càng xa implementation.

Vì vậy task kế tiếp nên là:

## **BOOTSTRAP-001 — Kiến trúc compiler implementation & self-hosting**

Phải chốt:

```text
Compiler repository
Compiler language
Bootstrap compiler
AST representation
Type system implementation
Trait solver
MIR implementation
Verifier
LIR
Backend interface
x86-64 backend
Object writer
Linker
Runtime libraries
Standard library
Build system
Testing
Fuzzing
Compiler self-hosting
```

Đặc biệt cần giải quyết một câu hỏi rất quan trọng đối với mục tiêu Axiom của bạn:

> **Compiler Axiom phiên bản đầu tiên sẽ được viết bằng gì, và làm thế nào để cuối cùng chính Axiom tự compile được compiler mà không rơi vào vòng phụ thuộc C/C++/LLVM vĩnh viễn?**

Tôi đề xuất kiến trúc **3-stage bootstrap**:

```text
Stage 0
Existing host compiler
        ↓
Bootstrap Axiom Compiler
        ↓
Stage 1 native Axiom compiler
        ↓
Stage 2 Axiom compiler written in Axiom
        ↓
Self-hosted Axiom
```

Sau đó mới chuyển sang thiết kế **AXIOM-STDLIB-001** và **OS/Platform Layer**, vì compiler self-hosting và standard library phải được thiết kế đồng thời với nhau.