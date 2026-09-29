Tiếp tục với **AXIOM LINKER v0.1**. Đây là bước nối `Object Writer → Native Executable`, và cũng là nơi ta cần giữ một nguyên tắc: **linker không hiểu ngôn ngữ Axiom**. Nó chỉ hiểu object format, symbols, sections, relocations và target ABI.

# AXIOM LINKER v0.1

## 1. Boundary tuyệt đối

Pipeline:

```text
Axiom Source
    ↓
Compiler
    ↓
foo.o
bar.o
runtime.o
    ↓
Axiom Linker
    ↓
program
```

Linker **không được biết**:

```text
struct
trait
generic
ownership
view
Drop
async
HIR
MIR
LIR
```

Nó chỉ biết:

```text
Object
Section
Symbol
Relocation
Segment
Entry Point
ABI
Target
```

Đây là điều giúp sau này Axiom linker có thể link:

```text
Axiom + C object
```

mà không cần hiểu C.

---

# 2. Kiến trúc linker

```text
compiler/linker/
├── input/
│   ├── object.ax
│   ├── archive.ax
│   └── format.ax
│
├── symbols/
│   ├── table.ax
│   ├── resolve.ax
│   └── visibility.ax
│
├── sections/
│   ├── merge.ax
│   ├── layout.ax
│   └── alignment.ax
│
├── relocation/
│   ├── resolve.ax
│   └── apply.ax
│
├── segments/
│   ├── load.ax
│   └── permission.ax
│
├── output/
│   ├── elf.ax
│   └── image.ax
│
├── entry/
│   └── entry.ax
│
└── tests/
```

Target-specific:

```text
targets/x86_64/elf/
├── relocations.ax
├── segments.ax
└── linker.ax
```

---

# 3. Input Object

Linker nhận:

```text
foo.o
bar.o
```

Mỗi object:

```text
Object
├── sections
├── symbols
├── relocations
└── metadata
```

Không cần parse lại source.

---

# 4. Section merging

Ví dụ:

```text
foo.o
.text
.rodata

bar.o
.text
.rodata
```

Linker tạo:

```text
program
.text
.rodata
```

với:

```text
foo.text
bar.text
foo.rodata
bar.rodata
```

theo layout deterministic.

---

# 5. Section ordering

MVP:

```text
.text
.rodata
.data
.bss
```

Sau này:

```text
.text.hot
.text.unlikely
.rodata.str
.rodata.const
.data
.data.rel.ro
.tdata
.tbss
.bss
```

Không nên hard-code quá nhiều section ngay từ đầu.

---

# 6. Symbol Resolution

Ví dụ:

```text
foo.o:
    foo = GLOBAL DEFINED
    bar = UNDEFINED

bar.o:
    bar = GLOBAL DEFINED
```

Linker:

```text
resolve(foo) → foo.o
resolve(bar) → bar.o
```

Nếu:

```text
foo.o:
    bar = UNDEFINED
```

và không object nào định nghĩa `bar`:

```text
AXL_LINK_0001
undefined symbol: bar
```

---

# 7. Symbol strength

MVP cần ít nhất:

```text
LOCAL
GLOBAL
WEAK
```

Quy tắc:

```text
LOCAL
```

chỉ visible trong object.

```text
GLOBAL
```

có thể resolve giữa objects.

```text
WEAK
```

có thể bị GLOBAL override.

---

# 8. Duplicate symbol

Nếu:

```text
foo.o → foo GLOBAL
bar.o → foo GLOBAL
```

thì:

```text
AXL_LINK_0002
multiple definition of symbol 'foo'
```

Không tự chọn một symbol.

Deterministic linker phải reject.

---

# 9. Symbol visibility

MVP:

```text
DEFAULT
HIDDEN
```

Sau này:

```text
PROTECTED
```

Static executable có thể đơn giản hóa rất nhiều.

---

# 10. Section layout

Linker phải tính:

```text
address
offset
size
alignment
```

Cho mỗi output section.

Ví dụ:

```text
.text
    address = 0x401000
    size    = 0x120

.rodata
    address = 0x402000
    size    = 0x80

.data
    address = 0x403000
    size    = 0x40
```

Alignment:

```text
.text   → 16
.rodata → 16
.data   → 16
```

MVP có thể đơn giản hơn nhưng phải có abstraction.

---

# 11. Virtual Address và File Offset

Đây là hai khái niệm khác nhau.

```text
File Offset
      ≠
Virtual Address
```

Output layout:

```text
section
├── file_offset
├── virtual_address
├── size
└── alignment
```

Đừng dùng một biến `offset` cho cả hai.

---

# 12. ELF Segment

Executable ELF không chỉ có sections.

Loader nhìn:

```text
PT_LOAD
```

MVP:

```text
LOAD R-X
LOAD RW-
```

Ví dụ:

```text
Segment 1
.text
.rodata

Segment 2
.data
.bss
```

Điều này tạo memory protection:

```text
code → executable
data → writable
```

---

# 13. W^X

Axiom linker nên mặc định hướng tới:

```text
Writable XOR Executable
```

Không tạo:

```text
RWX
```

trừ khi explicit low-level requirement.

Đây là mặc định tốt cho native executable.

---

# 14. `.bss`

`.bss` không cần chứa zero bytes trong file.

Ví dụ:

```text
var buffer: [u8; 1_000_000]
```

có thể:

```text
.data:
    file size = 0

.bss:
    memory size = 1 MB
```

ELF segment:

```text
p_filesz < p_memsz
```

Loader tự zero phần còn lại.

---

# 15. Relocation

Đây là phần quan trọng nhất.

Object:

```text
CALL foo
```

chưa biết `foo` nằm đâu.

Relocation:

```text
R_X86_64_PLT32
```

hoặc relocation phù hợp với static/direct call.

Linker tính:

```text
target_address
-
relocation_place
```

và ghi bytes vào `.text`.

---

# 16. Không nên dùng PLT/GOT cho static MVP

Mục tiêu đầu tiên:

```text
static executable
```

Do đó:

```text
CALL foo
```

→ direct relocation.

Không cần:

```text
PLT
GOT
dynamic linker
```

ở milestone đầu.

Đây là cách giảm đáng kể độ phức tạp.

---

# 17. Relocation abstraction

Generic:

```text
Relocation {
    offset
    type
    symbol
    addend
}
```

Target:

```text
x86_64 relocation
```

có:

```text
R_X86_64_PC32
R_X86_64_PLT32
R_X86_64_32
R_X86_64_32S
R_X86_64_64
```

MVP chỉ cần subset thực sự dùng.

---

# 18. PC-relative

Ví dụ:

```text
CALL foo
```

thường dùng displacement tương đối.

Conceptually:

```text
disp = foo_address - next_instruction_address
```

Linker phải xử lý overflow:

```text
AXL_RELOC_0001
relocation out of range
```

Không truncate im lặng.

---

# 19. Absolute relocation

Ví dụ address của global:

```text
mov rax, &global
```

có thể cần:

```text
R_X86_64_64
```

Linker ghi:

```text
64-bit absolute address
```

Nhưng PIE sau này sẽ có quy tắc khác.

---

# 20. Entry Point

Linker phải xác định:

```text
entry symbol
```

MVP:

```text
_start
```

Nếu user dùng:

```text
@entry fn main()
```

compiler/startup layer đảm bảo object có:

```text
_start
```

Linker không tự hiểu `main`.

---

# 21. Phân biệt `main` và `_start`

Rất quan trọng:

```text
Axiom semantic entry:
main

OS entry:
_start
```

Startup:

```text
_start
   ↓
initialize
   ↓
main
   ↓
exit
```

Linker chỉ biết:

```text
_start
```

---

# 22. Minimal freestanding

Có thể cho:

```axiom id="v7y9s2"
@entry
fn _start() {
}
```

hoặc một entry annotation khác ở system layer.

Khi đó:

```text
Axiom
 ↓
ELF
 ↓
Linux loader
 ↓
_start
```

không cần runtime.

Đây là test rất tốt cho linker.

---

# 23. Static linking

MVP:

```text
foo.o
bar.o
startup.o
```

→

```text
program
```

Không dynamic loader.

Không libc bắt buộc.

Không `.so`.

Không `ld.so`.

---

# 24. Archive `.a`

Ngay sau object linker, nên hỗ trợ:

```text
libfoo.a
```

Archive:

```text
archive
├── foo.o
├── bar.o
└── baz.o
```

Linker chỉ extract object khi có unresolved symbol phù hợp.

Ví dụ:

```text
main.o
 ↓
needs foo
 ↓
libfoo.a
 ↓
extract foo.o
```

Không extract toàn bộ archive.

---

# 25. Vì sao archive quan trọng?

Nó cho phép xây:

```text
libaxiom_std.a
```

mà không bắt executable phải chứa toàn bộ standard library.

Ví dụ chương trình chỉ dùng:

```text
Text
```

thì linker chỉ lấy các object cần thiết.

Đây là nền tảng cho:

> **dead-code elimination ở mức object**.

Sau này compiler LTO sẽ làm tốt hơn nữa.

---

# 26. COMDAT / weak / duplicate code

Chưa cần đầy đủ ở MVP.

Nhưng architecture phải chừa abstraction:

```text
SymbolResolutionPolicy
SectionSelectionPolicy
```

để sau này hỗ trợ:

```text
COMDAT
weak ODR-like semantics
template instantiation
generic code
```

---

# 27. Generics và linker

Axiom generic:

```axiom id="z1v8n3"
fn max<T: Ord>(a: T, b: T) -> T
```

sau monomorphization có thể sinh:

```text
max_i32
max_f32
max_User
```

Linker không biết đó là generic.

Nó chỉ thấy symbols.

Đây chính xác là boundary mong muốn.

---

# 28. LTO không thuộc linker v0.1

LTO:

```text
MIR/LIR
 ↓
cross-module optimization
```

nên diễn ra **trước** object generation hoặc ở một IR-aware linker mode tương lai.

MVP:

```text
compile each object
 ↓
link
```

Sau đó:

```text
whole-program optimization
 ↓
object/link
```

---

# 29. Linker GC sections

Sau archive support, có thể thêm:

```text
--gc-sections
```

nhưng đây là optimization.

Concept:

```text
entry
 ↓
reachable symbols
 ↓
reachable sections
 ↓
discard unused sections
```

Axiom compiler có thể mặc định sử dụng section-per-function trong một profile tối ưu:

```text
.text.main
.text.foo
.text.bar
```

để linker dễ loại bỏ.

---

# 30. PIE

Không làm ngay.

Roadmap:

```text
MVP
ET_EXEC
static

v0.2
PIE

v0.3
shared library

v0.4
dynamic linking
```

Lý do: PIE/shared libraries làm relocation model và GOT/PLT phức tạp hơn đáng kể.

---

# 31. Dynamic linking

Cuối cùng Axiom cần:

```text
.so
.dll
.dylib
```

nhưng đây là một hệ riêng:

```text
Dynamic Symbol Table
GOT
PLT
TLS
Dynamic Relocations
SONAME
Versioning
Loader interaction
```

Không nên làm lẫn vào static linker MVP.

---

# 32. Linker diagnostics

Chốt mã lỗi:

```text
AXL_INPUT_0001
invalid object file

AXL_INPUT_0002
unsupported object format

AXL_SYMBOL_0001
undefined symbol

AXL_SYMBOL_0002
multiple definition

AXL_SYMBOL_0003
invalid symbol visibility

AXL_SECTION_0001
invalid section alignment

AXL_SECTION_0002
section layout overflow

AXL_RELOC_0001
unsupported relocation

AXL_RELOC_0002
relocation overflow

AXL_RELOC_0003
undefined relocation symbol

AXL_ENTRY_0001
entry symbol not found

AXL_OUTPUT_0001
invalid output layout
```

---

# 33. Determinism

Đây là invariant rất quan trọng.

Cùng:

```text
foo.o
bar.o
```

phải tạo byte-identical output:

```text
program_A
==
program_B
```

nếu:

```text
compiler inputs
linker options
target
```

giống nhau.

Không được phụ thuộc:

```text
hash-map iteration order
filesystem order
thread scheduling
```

---

# 34. Linker algorithm

MVP:

```text id="q5m2x8"
1. Parse input objects
2. Validate target
3. Collect symbols
4. Resolve symbols
5. Select archive members
6. Merge sections
7. Layout sections
8. Create segments
9. Assign symbol addresses
10. Resolve relocations
11. Write ELF headers
12. Write program headers
13. Write section data
14. Write symbol/debug information if requested
15. Set entry point
16. Validate final ELF
17. Emit executable
```

---

# 35. Final ELF validation

Trước khi ghi file:

```text id="3f8n2q"
ELF Validator
```

kiểm tra:

```text
entry ∈ executable segment

all relocation resolved

all section addresses valid

segment alignment valid

file offsets valid

PT_LOAD ranges valid

no required symbol unresolved

section doesn't overlap illegally
```

Không nên chỉ tin linker internal state.

---

# 36. Linker self-test

Test:

```text id="9p5m7k"
foo.o
bar.o
```

expected:

```text
program
```

Sau đó parse lại:

```text
program
 ↓
ELF parser
 ↓
validate
```

Rồi chạy:

```text
./program
```

Ba tầng:

```text
structural correctness
+
semantic relocation correctness
+
actual execution
```

---

# 37. First complete native chain

Sau linker:

```text id="q0b7m4"
main.ax
```

```axiom id="1j5q8v"
fn main() -> i32 {
    42
}
```

Compiler:

```text id="3q6k1d"
main.o
```

Startup:

```text id="5m9x2c"
startup.o
```

Link:

```text id="7r4p8z"
axiom-link startup.o main.o -o main
```

Output:

```text id="0x4k6m"
main
```

Execution:

```text id="v8q2s1"
./main
echo $?
```

→

```text
42
```

Đây là **BOOT-001**.

---

# 38. Nhưng có một thay đổi kiến trúc tôi đề nghị

Từ thời điểm này, linker không nên chỉ là:

```text
compiler/linker/
```

mà nên có:

```text
linker/
├── core/
├── object/
└── targets/
```

vì linker cuối cùng sẽ trở thành một tool độc lập:

```text
axiom-link
```

Có thể được gọi bởi:

```text
axiom build
```

nhưng cũng có thể chạy độc lập:

```text
axiom-link a.o b.o -o app
```

---

# 39. Toolchain Axiom bắt đầu hình thành

Ta sẽ có:

```text
axiom
axiomc
axiom-link
axiom-ar
axiom-objdump
axiom-objcopy
axiom-nm
```

Không nhất thiết tất cả là executable riêng ngay từ đầu.

Có thể:

```text
axiom tool link
axiom tool objdump
```

sau đó tách binary nếu cần.

---

# 40. `axiom build`

Driver cuối cùng:

```text id="3f7n2q"
axiom build
```

sẽ orchestrate:

```text
source
 ↓
compiler
 ↓
.o
 ↓
linker
 ↓
executable
```

Compiler driver **không được tự biến thành linker khổng lồ**.

Các subsystem độc lập.

---

# 41. Milestones tiếp theo

Đến đây backend architecture:

```text
                         ┌→ Oracle
                         │
Source → Frontend → MIR → Verified MIR
                         ↓
                       LIR
                         ↓
                 x86 Machine IR
                         ↓
                  Register Alloc
                         ↓
                       Encode
                         ↓
                      ELF .o
                         ↓
                    Axiom Linker
                         ↓
                    ELF executable
```

Các milestone:

```text
LINK-001
Read ELF object

LINK-002
Symbol resolution

LINK-003
Section layout

LINK-004
x86 relocation

LINK-005
ELF executable writer

LINK-006
Entry point

LINK-007
Static multi-object linking

LINK-008
Archive .a

LINK-009
Final ELF validator

BOOT-001
empty executable

BOOT-002
return 42

BOOT-003
function call

BOOT-004
multiple modules

BOOT-005
C object interoperability
```

---

# 42. Sau BOOT-005, ta nên chuyển hướng

Đến lúc đó không nên tiếp tục bổ sung backend vô tận.

Ta cần quay lại compiler core và xây:

> **Semantic Optimizer v0.1**

vì lúc ấy đã có một compiler chạy end-to-end, và ta có thể đo được optimization thay vì thiết kế trên giấy.

Pipeline sẽ thành:

```text
Verified MIR
    ↓
MIR Optimizer
    ↓
LIR
```

với các pass đầu tiên:

```text
Constant Folding
Constant Propagation
Dead Code Elimination
Simplification
Copy Propagation
CFG Simplification
Inlining
SROA
Bounds Check Elimination
Escape Analysis
Allocation Elimination
```

Đặc biệt với triết lý Axiom, **Escape Analysis + Allocation Elimination + alias/capability facts** sẽ là một trong những vũ khí quan trọng nhất để đạt hiệu năng cao mà không bắt lập trình viên phải viết hàng đống pointer/lifetime annotation.

Và sau optimizer, bước rất đáng làm là **`-O0/-O1/-O2/-O3/-Os` semantic profiles + benchmark harness**, để từ đó bắt đầu đo Axiom thực tế thay vì chỉ tiếp tục thiết kế.