# BOOTSTRAP-110 — Object Writer, Linker & Native Binary Generation

**Trạng thái: FROZEN / COMPLETED**

Đây là mảnh ghép nối trực tiếp từ backend máy ở BOOTSTRAP-109 sang **file thực thi native thực sự**.

Pipeline sau task này:

```text
Source
  ↓
AST → HIR → Typed HIR → MIR
  ↓
Verified MIR
  ↓
OptIR
  ↓
ABI MIR
  ↓
Axiom LIR
  ↓
Machine IR
  ↓
Machine Code
  ↓
Object File
  ↓
Link Graph
  ↓
Executable / Shared Library / Static Library
```

---

# 1. Nguyên tắc kiến trúc

Axiom phải phân biệt rõ 4 tầng:

| Tầng | Nhiệm vụ |
|---|---|
| Machine Code | mã máy |
| Object File | mã máy + section + symbol + relocation |
| Linker | ghép và giải quyết nhiều object/library |
| Executable | binary cuối cùng mà OS/loader có thể chạy |

Compiler backend **không được tự ý biến machine code thành executable**.

Điều này rất quan trọng vì:

```text
compiler
    ↓
foo.o

compiler
    ↓
bar.o

library builder
    ↓
libfoo.a

linker
    ↓
app.exe
```

Có thể tái sử dụng object code mà không cần compile lại source.

---

# 2. `ObjectFile` abstraction

Axiom định nghĩa một mô hình object trung gian độc lập format:

```text
ObjectFile
├── format
├── architecture
├── sections[]
├── symbols[]
├── relocations[]
├── comdats[]
├── debug_info
├── unwind_info
├── tls_info
└── metadata
```

Các format:

```text
COFF
ELF
Mach-O
WASM
```

Không được để compiler semantic layer biết chi tiết PE/ELF/Mach-O.

---

# 3. Section model

Object file có các section logic:

```text
TEXT
RODATA
DATA
BSS
TLS
INIT
FINI
UNWIND
DEBUG
METADATA
CUSTOM
```

Ví dụ:

```text
.text
.rodata
.data
.bss
.tdata
.tbss
.init
.fini
.eh_frame
.debug_*
```

Nhưng đây chỉ là **mapping của logical section → target format section**.

Ví dụ:

```text
Axiom TEXT
    ↓
ELF .text
PE  .text
Mach-O __TEXT,__text
```

Compiler không được phụ thuộc vào tên section vật lý.

---

# 4. Section properties

Mỗi section có metadata:

```text
Section {
    kind
    flags
    alignment
    size
    contents
    relocations
    linkage
}
```

Flags:

```text
READ
WRITE
EXECUTE
ALLOC
LOAD
TLS
MERGE
DISCARDABLE
DEBUG
```

Các thuộc tính không hợp lệ phải bị linker reject.

Ví dụ:

```text
WRITE + EXECUTE
```

không được tự động tạo chỉ vì một object yêu cầu như vậy.

---

# 5. Symbol model

Symbol:

```text
Symbol {
    name
    binding
    visibility
    kind
    section
    offset
    size
    definition
}
```

Binding:

```text
LOCAL
GLOBAL
WEAK
```

Kind:

```text
FUNCTION
OBJECT
TLS
SECTION
ABSOLUTE
IMPORT
```

Các trạng thái:

```text
DEFINED
UNDEFINED
COMMON
IMPORT
EXPORT
```

---

# 6. Symbol resolution

Ví dụ:

```text
a.ax
    fn foo()

b.ax
    fn bar() {
        foo()
    }
```

Sau compile:

```text
a.o
    foo = defined

b.o
    bar = defined
    foo = undefined
```

Linker tạo:

```text
foo → a.o::foo
bar → b.o::bar
```

Nếu có:

```text
foo defined in a.o
foo defined in c.o
```

thì linker phải xử lý theo linkage rules.

Đối với symbol mạnh bị định nghĩa nhiều lần:

```text
ERROR: duplicate symbol
```

Không được chọn ngẫu nhiên theo thứ tự file.

---

# 7. Weak symbol

Weak symbol được hỗ trợ ở tầng object/linker.

Ví dụ:

```text
weak foo
```

Có thể bị thay thế bởi:

```text
strong foo
```

Nhưng semantics của Axiom source language **không được dựa vào weak symbol**.

Weak là cơ chế ABI/linker/system.

---

# 8. Relocation

Machine code thường chưa biết địa chỉ cuối cùng.

Ví dụ:

```asm
call foo
```

Object chứa:

```text
CALL instruction
relocation:
    offset = ...
    symbol = foo
    type = PC_REL32
```

Linker giải quyết:

```text
foo address
      ↓
relocation
      ↓
machine bytes
```

Axiom cần một relocation abstraction:

```text
Relocation {
    offset
    symbol
    kind
    addend
    width
}
```

---

# 9. Relocation kinds

Logical relocation:

```text
ABS
PC_REL
GOT
PLT
TLS
SECTION_REL
IMAGE_REL
WASM_INDEX
```

Target backend map sang relocation cụ thể.

Ví dụ:

```text
Axiom PC_REL
    ↓
x86-64 ELF R_X86_64_PC32

Axiom PC_REL
    ↓
AArch64 ELF R_AARCH64_CALL26
```

Không được hard-code relocation ELF vào MIR/LIR.

---

# 10. Static library

Axiom hỗ trợ:

```text
libfoo.a
```

hoặc tương đương trên Windows:

```text
foo.lib
```

Logical model:

```text
StaticArchive
├── object1.o
├── object2.o
├── object3.o
└── index
```

Linker **không nhất thiết đưa toàn bộ archive vào executable**.

Nó chỉ extract object cần thiết để giải quyết symbol.

Ví dụ:

```text
app → foo()
```

archive:

```text
foo.o
bar.o
debug.o
```

chỉ:

```text
foo.o
```

được lấy nếu các object khác không cần.

---

# 11. Dead stripping

Sau khi xây dependency graph:

```text
main
 ↓
foo
 ↓
bar
```

Nếu:

```text
unused()
```

không reachable:

```text
unused.o / unused section
```

có thể bị loại.

Có hai cấp:

### Object-level

```text
unused.o
```

### Section-level

```text
foo
bar
unused_function
```

trong cùng object.

Axiom nên hướng tới:

```text
-fdata-sections
-ffunction-sections
--gc-sections
```

tương đương nhưng **không nhất thiết expose dưới tên đó**.

Compiler/linker mặc định có thể tối ưu binary size.

---

# 12. COMDAT / LinkOnce / Generic dedup

Generic:

```text
Vec<i32>
Vec<f32>
Vec<u64>
```

có thể tạo nhiều object chứa các specialization.

Nếu cùng một specialization xuất hiện từ nhiều compilation unit:

```text
Vec<i32>::push
```

thì linker phải có cơ chế:

```text
COMDAT
LINKONCE
WEAK_ODR-like
```

để deduplicate.

Nhưng Axiom không nên copy nguyên semantics của C++ ODR.

Axiom compiler tạo **canonical GenericInstanceId**:

```text
GenericInstanceId
    ↓
symbol identity
    ↓
linker dedup key
```

Do đó:

```text
same semantic specialization
        ↓
same linkage identity
```

---

# 13. PIC / PIE

Axiom phải hỗ trợ:

```text
static executable
PIE executable
shared library
dynamic library
```

Position-independent code được quyết định ở target/backend/link level.

Ví dụ:

```text
@pic
```

không cần trở thành Core language primitive.

Build configuration có thể chọn:

```text
position_independent = true
```

Compiler/backend sau đó sinh code phù hợp.

---

# 14. Dynamic libraries

Hỗ trợ:

```text
Windows:
    .dll

Linux:
    .so

macOS/iOS:
    .dylib / framework / platform-specific bundle
```

Logical model:

```text
SharedLibrary {
    exported_symbols
    imported_symbols
    dependencies
    tls
    init
    fini
    metadata
}
```

---

# 15. Import / Export

Axiom phân biệt:

```text
pub
```

với:

```text
@export
```

Ví dụ:

```text
pub fn internal_api()
```

không có nghĩa executable export symbol.

Muốn export:

```text
@export("axiom_init")
pub fn init()
```

Linker tạo export table tương ứng.

---

# 16. Dynamic symbol lookup

Shared library:

```text
app
 ↓
libfoo.so
 ↓
foo()
```

Linker tạo dynamic dependency.

ELF:

```text
DT_NEEDED
.dynamic
.got
.plt
.dynsym
.dynstr
```

PE:

```text
Import Table
Import Address Table
Export Table
```

Mach-O:

```text
Load Commands
Dyld information
Exports
Bindings
```

Các chi tiết này chỉ tồn tại ở format backend.

---

# 17. TLS

Thread-local:

```text
@tls
var counter: i32
```

không phải global bình thường.

Object/linker model phải biết:

```text
TLS_INITIALIZED
TLS_ZERO
TLS_ALIGNMENT
TLS_SIZE
```

Target backend chuyển thành:

```text
ELF TLS
PE TLS
Mach-O TLS
```

Không được giả lập TLS bằng một global + mutex trong compiler.

---

# 18. Entry point

Executable cần entry point.

Axiom phân biệt:

```text
program entry
```

với:

```text
user main()
```

Ví dụ:

```text
OS
 ↓
_start / platform entry
 ↓
Axiom startup
 ↓
initialize required runtime components
 ↓
main()
 ↓
exit
```

Nhưng nếu:

```text
freestanding
```

thì có thể:

```text
OS/firmware
 ↓
_start
```

mà không cần:

```text
Axiom runtime
main wrapper
allocator
panic runtime
```

---

# 19. Không ép CRT

Một mục tiêu rất quan trọng của Axiom:

```text
hello.ax
```

có thể tạo binary:

```text
OS loader
    ↓
Axiom entry
    ↓
main
```

mà không cần bắt buộc:

```text
libc
libstdc++
MSVC CRT
Axiom runtime monolith
```

Nếu chương trình cần libc:

```text
import libc
```

thì đó là dependency thực sự của chương trình.

---

# 20. Runtime component linking

Linker phải hiểu dependency của các compiler-generated/runtime components.

Ví dụ:

```text
program
 ├── allocator
 ├── panic
 └── threads
```

thì chỉ link:

```text
allocator
panic
threads
```

Không được link:

```text
full_runtime.dll
```

nếu chương trình không cần.

Điều này trực tiếp phục vụ mục tiêu binary nhỏ.

---

# 21. Freestanding

Axiom hỗ trợ profile:

```text
hosted
freestanding
kernel
embedded
device
gpu
```

Ví dụ:

```text
freestanding
```

có thể loại bỏ:

```text
filesystem
network
process
threads
allocator
unicode runtime
panic runtime
```

nếu không sử dụng.

---

# 22. WASM

WASM không nên cố giả lập ELF.

Pipeline:

```text
Axiom
 ↓
WASM-specific ABI
 ↓
WASM module
```

Có:

```text
imports
exports
functions
tables
memory
globals
data
custom sections
```

Axiom linker có thể tạo:

```text
.wasm
```

trực tiếp.

---

# 23. Debug information

Debug information là artifact riêng:

```text
Object
 ├── code
 ├── symbols
 └── debug metadata
```

Có thể tạo:

```text
binary
binary + debug
separate debug file
```

Source mapping:

```text
Source
 ↓
MIR
 ↓
OptIR
 ↓
LIR
 ↓
Machine IR
 ↓
Machine bytes
```

được bảo toàn.

---

# 24. Unwind information

Nếu:

```text
panic = abort
```

có thể loại bỏ phần lớn unwind metadata.

Nếu:

```text
panic = unwind
```

thì object phải chứa thông tin cần thiết.

Ví dụ:

```text
ELF:
    .eh_frame
    .gcc_except_table nếu cần

Windows:
    unwind pdata/xdata

Mach-O:
    unwind information
```

Đây là một quyết định **ABI/linker**, không phải semantic panic model.

---

# 25. Section garbage collection

Linker xây graph:

```text
ROOT
 │
 ├── main
 │    ├── foo
 │    └── bar
 │
 └── runtime_init
```

Các node không reachable:

```text
unused
```

bị loại.

Root có thể gồm:

```text
entry point
exported symbols
dynamic symbols
init/fini
interrupt handlers
FFI-visible symbols
reflection-preserved symbols
explicit keep
```

---

# 26. Init/Fini

Không nên có global constructor ngầm kiểu C++.

Nếu cần initialization:

```text
@init
fn initialize()
```

thì compiler/linker tạo dependency rõ ràng.

Ví dụ:

```text
init graph

A.init
   ↓
B.init
```

Circular initialization:

```text
A → B → A
```

phải bị phát hiện hoặc bị cấm tùy profile.

Không được sinh một runtime initialization registry khổng lồ mặc định.

---

# 27. Link graph

Đây là cấu trúc trung tâm của linker:

```text
LinkGraph

Nodes:
    Object
    Section
    Symbol
    DynamicLibrary
    ArchiveMember
    RuntimeComponent

Edges:
    references
    relocation
    dependency
    initialization
    export
    import
```

Sau đó:

```text
resolve
→ retain
→ discard
→ layout
→ relocate
→ emit
```

---

# 28. Section layout

Linker quyết định:

```text
virtual address
file offset
alignment
section order
segment membership
```

Ví dụ ELF:

```text
LOAD R-X
    .text
    .rodata

LOAD RW
    .data
    .bss
```

PE:

```text
.text
.rdata
.data
.pdata
.reloc
```

Mach-O:

```text
__TEXT
__DATA
__LINKEDIT
```

---

# 29. Segment model

Object section và executable segment **không phải cùng một khái niệm**.

```text
Section
    ↓
Segment
    ↓
Loader mapping
```

Ví dụ nhiều sections:

```text
.text
.rodata
.eh_frame
```

có thể nằm trong một read/execute hoặc read-only load segment tùy target.

---

# 30. Address assignment

Linker:

```text
layout sections
      ↓
assign VMA
      ↓
assign file offsets
      ↓
resolve symbols
      ↓
apply relocations
```

Không được resolve relocation trước khi layout hoàn tất nếu relocation phụ thuộc final address.

---

# 31. Reproducible linking

Cùng:

```text
source
compiler version
target
build configuration
dependencies
```

phải tạo binary deterministic, nếu không có nguồn nondeterminism được khai báo.

Loại bỏ:

```text
timestamp ngẫu nhiên
file-order phụ thuộc filesystem
random symbol ordering
machine-specific absolute paths
```

Debug metadata có thể dùng normalized paths.

---

# 32. Build identity

Link artifact cần identity:

```text
CompilerSemanticVersion
Target
CPUFeatures
ABI
OptimizationProfile
SourceFingerprint
DependencyFingerprint
ComptimeFingerprint
LinkerVersion
LinkConfiguration
```

Điều này liên kết trực tiếp với hệ thống cache đã thiết kế trước đó.

---

# 33. Own Axiom linker

Mục tiêu cuối:

```text
Axiom Compiler
      ↓
Axiom ObjectWriter
      ↓
Axiom Linker
      ↓
native executable
```

Không:

```text
Axiom
 ↓
LLVM
 ↓
LLD
```

ở production.

Tuy nhiên bootstrap:

```text
Axiom compiler
 ↓
LLVM / system linker
```

được phép.

Đây là **bootstrap dependency**, không phải language dependency.

---

# 34. Target implementation roadmap

Không cần triển khai tất cả cùng lúc.

### Phase 1

```text
x86-64
ELF
```

### Phase 2

```text
x86-64
PE/COFF
```

### Phase 3

```text
AArch64
ELF
Mach-O
```

### Phase 4

```text
RISC-V
ELF
```

### Phase 5

```text
WASM
```

Sau đó:

```text
iOS Mach-O
Android ELF
Windows ARM64
macOS ARM64
```

---

# 35. Compiler/Linker interface

Nên đóng thành interface:

```text
ObjectWriter {
    create_object()
    add_section()
    add_symbol()
    add_relocation()
    add_comdat()
    add_debug()
    add_unwind()
    finalize()
}
```

và:

```text
Linker {
    add_object()
    add_archive()
    add_shared_library()
    define_symbol()
    configure_entry()
    configure_target()
    resolve()
    layout()
    relocate()
    emit()
}
```

Target-specific:

```text
ElfObjectWriter
CoffObjectWriter
MachObjectWriter
WasmObjectWriter

ElfLinker
CoffLinker
MachLinker
WasmLinker
```

Nhưng chúng dùng chung logical `ObjectModel` và `LinkGraph`.

---

# 36. Những thứ linker KHÔNG được làm

Linker không được:

- kiểm tra ownership;
- suy luận lifetime;
- type-check;
- trait resolution;
- generic resolution;
- thay đổi semantic MIR;
- tự ý thay đổi atomic semantics;
- tự ý bỏ Drop;
- tự ý thay đổi ABI contract;
- tự ý biến UNKNOWN alias thành NO_ALIAS.

Linker chỉ xử lý:

```text
binary structure
symbol dependency
address/layout
relocation
platform loader contract
```

---

# 37. Invariants

### `ALINK-20`
ObjectFile is distinct from Executable.

### `ALINK-21`
Object files contain machine code plus link metadata.

### `ALINK-22`
Relocations are explicit.

### `ALINK-23`
Symbol resolution is deterministic.

### `ALINK-24`
Strong duplicate definitions are errors unless an explicit format rule applies.

### `ALINK-25`
Weak linkage is an ABI/linker mechanism, not a source-language semantic.

### `ALINK-26`
Archive extraction is demand-driven.

### `ALINK-27`
Unreachable sections may be eliminated only when not reachable from a linker root.

### `ALINK-28`
Exported/dynamically visible symbols are linker roots unless explicitly handled otherwise.

### `ALINK-29`
Generic/linkonce instances have deterministic linkage identity.

### `ALINK-30`
Relocation application preserves target ABI semantics.

### `ALINK-31`
Section layout occurs before address-dependent relocation resolution.

### `ALINK-32`
TLS is distinct from ordinary global storage.

### `ALINK-33`
Executable entry point is an explicit linker property.

### `ALINK-34`
`pub` does not imply binary export.

### `ALINK-35`
`@export` creates an explicit external symbol contract.

### `ALINK-36`
Freestanding binaries do not implicitly acquire hosted runtime components.

### `ALINK-37`
Runtime components are linked only when required.

### `ALINK-38`
Debug information is non-semantic artifact data.

### `ALINK-39`
Unwind metadata exists only when required by the selected panic/ABI profile.

### `ALINK-40`
Foreign dynamic libraries are explicit dependencies.

### `ALINK-41`
Foreign allocator ownership is never inferred by the linker.

### `ALINK-42`
WASM uses a WASM-specific module model rather than ELF/PE emulation.

### `ALINK-43`
The linker cannot weaken compiler-verified safety guarantees.

### `ALINK-44`
The linker cannot change semantic program behavior except through explicitly selected ABI/platform mechanisms.

### `ALINK-45`
Binary generation is deterministic given identical semantic inputs and toolchain configuration.

### `ALINK-46`
ObjectWriter is independent from Linker.

### `ALINK-47`
Target-specific object formats are isolated behind the object/link abstraction.

### `ALINK-48`
Production Axiom compilation must not require LLVM/Clang/GCC/LLD.

### `ALINK-49`
Bootstrap use of external toolchains does not become a language dependency.

### `ALINK-50`
Axiom can produce a native executable without a monolithic mandatory runtime.

---

# 38. Kết quả của BOOTSTRAP-110

Axiom hiện đã có đường đi hoàn chỉnh:

```text
SOURCE
  ↓
SEMANTICS
  ↓
VERIFIED MIR
  ↓
OPTIR
  ↓
ABI MIR
  ↓
AXIOM LIR
  ↓
MACHINE IR
  ↓
MACHINE CODE
  ↓
OBJECT
  ↓
LINK GRAPH
  ↓
NATIVE BINARY
```

Đây là một mốc rất lớn: **kiến trúc compiler Axiom giờ đã đi từ source language tới executable format**, không còn khoảng trống lớn ở backend.

---

# BOOTSTRAP-111 — Runtime Composition, Startup & Platform System Layer

**Task tiếp theo cần khóa ngay** là runtime/platform boundary.

Vấn đề trung tâm:

> Làm thế nào để một chương trình Axiom có thể chạy từ `entry point` đến `main()` mà **không bắt buộc phải kéo theo một runtime khổng lồ**, nhưng vẫn hỗ trợ allocator, threads, async, panic, TLS, filesystem, networking, GPU... khi cần?

Kiến trúc đề xuất:

```text
                 Axiom Program
                       │
                       ▼
              ┌─────────────────┐
              │ Platform Profile │
              └────────┬────────┘
                       │
          ┌────────────┼────────────┐
          ▼            ▼            ▼
      Freestanding   Hosted      Kernel
          │            │
          │            ▼
          │      Startup Layer
          │            │
          │      Runtime Components
          │       ┌────┼────┐
          │       ▼    ▼    ▼
          │    Alloc  TLS  Threads
          │       │    │    │
          │       └────┼────┘
          │            ▼
          └──────► Application
                       │
                      main
```

Task này sẽ khóa:

1. **Platform Profile**
   - hosted
   - freestanding
   - kernel
   - embedded
   - GPU/device

2. **Startup**
   - OS entry
   - `_start`
   - `main`
   - argument/environment initialization
   - exit semantics

3. **Runtime component graph**
   - allocator
   - panic
   - TLS
   - threads
   - async
   - IO
   - Unicode
   - reflection
   - GPU

4. **No hidden runtime**
   - component chỉ được link khi thật sự cần.

5. **System layer**
   - OS syscall
   - Windows API
   - POSIX
   - Linux
   - macOS
   - Android
   - iOS
   - embedded HAL

6. **Process model**
   - exit
   - abort
   - signal/fault boundary
   - environment
   - arguments

7. **Runtime initialization**
   - không có global constructor ngầm kiểu C++.

8. **TLS startup/destruction**

9. **Thread startup**

10. **Allocator bootstrap**

11. **Panic bootstrap**

12. **Async executor bootstrap**

13. **Foreign runtime integration**

14. **CRT/libc integration**
   - optional, không bắt buộc.

15. **Minimal hello-world**
   - mục tiêu có thể tạo binary native mà runtime gần như bằng 0.

Sau BOOTSTRAP-111, chuỗi hợp lý sẽ là:

```text
110 Object/Linker
        ↓
111 Runtime/Platform
        ↓
112 Bootstrap Compiler
        ↓
113 Self-Hosting Compiler
        ↓
114 Build System / Package / Artifact
        ↓
115 Standard Library Architecture
        ↓
116 Testing / Conformance / Compiler Validation
        ↓
117 Axiom v0.1 implementation roadmap
```

**BOOTSTRAP-110 đã khóa. Task kế tiếp là BOOTSTRAP-111.**