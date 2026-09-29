Tiếp tục.

# Axiom — Native Toolchain, Object Writer & Linker v0.1

Đây là một trong những phần quan trọng nhất của toàn bộ dự án. Nếu làm đúng, Axiom không còn chỉ là một language frontend trên LLVM, mà có thể tiến tới **toolchain native độc lập**.

Mục tiêu cuối:

```text
Axiom source
    ↓
Axiom compiler
    ↓
Axiom LIR
    ↓
Machine code
    ↓
Axiom Object Writer
    ↓
Axiom Linker
    ↓
.exe / ELF / Mach-O / WASM
```

Không cần:

```text
C compiler
C++ compiler
LLVM
GCC
Clang
MSVC
GNU assembler
```

cho **Axiom-native compilation**.

---

# 1. Không cần assembler

Tôi khuyến nghị rất rõ:

> **Axiom không cần có assembler trong toolchain chính.**

Thay vì:

```text
LIR
 ↓
assembly text
 ↓
assembler
 ↓
object
```

làm:

```text
LIR
 ↓
instruction encoder
 ↓
object writer
```

Ví dụ x86-64:

```text
ADD RAX, RBX
```

được encoder trực tiếp thành machine bytes.

---

# 2. Tại sao bỏ assembler?

Đơn giản hơn:

```text
Compiler
 ↓
Machine encoder
 ↓
Object
```

thay vì:

```text
Compiler
 ↓
Assembly printer
 ↓
Assembler parser
 ↓
Assembler semantic
 ↓
Object
```

Axiom tránh phải duy trì một ngôn ngữ assembly thứ hai.

---

# 3. Assembly vẫn có thể xuất

Cho debugging:

```text
axiom emit --asm
```

Compiler có thể in:

```asm
mov rax, rdi
add rax, rsi
ret
```

nhưng đó là **output/debug view**, không phải compilation stage bắt buộc.

---

# 4. Object format abstraction

Object writer cần API chung:

```text id="s9tq9g"
ObjectFile
 ├── Sections
 ├── Symbols
 ├── Relocations
 ├── StringTables
 ├── DebugData
 └── TargetMetadata
```

Backend không được trực tiếp viết ELF/PE/Mach-O.

---

# 5. Section abstraction

Conceptually:

```text id="86x3hj"
Section {
    name
    kind
    flags
    alignment
    data
    relocations
}
```

Ví dụ:

```text id="0s1e7f"
.text
.rodata
.data
.bss
.tdata
.tbss
.debug_*
```

---

# 6. Section flags

Compiler/object writer cần biết:

```text id="1b2tq7"
ALLOC
WRITE
EXEC
TLS
MERGE
STRINGS
DEBUG
DISCARD
```

Nhưng đây là object-level semantics.

---

# 7. `.text`

Machine code:

```text id="ymn2hi"
.text
```

có:

```text id="5h4ckm"
RX
```

thường:

```text id="m4myo9"
Read + Execute
```

không write.

---

# 8. `.rodata`

String/constants:

```text id="8n9w5q"
.rodata
```

thường:

```text id="n5blz1"
R
```

Compiler không được đưa immutable data vào writable section nếu không cần.

---

# 9. `.data`

Initialized mutable globals:

```text id="5k6b7y"
static var counter: i32 = 0
```

có thể vào:

```text id="yp7wkl"
.data
```

---

# 10. `.bss`

Zero-initialized static:

```text id="x95x3j"
static var buffer: [u8; 1_000_000] = zero
```

không cần lưu 1 MB zeros trong executable.

Object:

```text id="6f5p0j"
.bss size=1000000
```

---

# 11. TLS sections

Thread-local:

```text id="7xwq0f"
.tdata
.tbss
```

Target-specific lowering.

---

# 12. Symbol abstraction

Symbol:

```text id="0frc9q"
Symbol {
    name
    section
    offset
    size
    binding
    visibility
    kind
}
```

Ví dụ:

```text id="nq7k88"
main
foo
bar
```

---

# 13. Symbol binding

Cần:

```text id="d8d6q3"
LOCAL
GLOBAL
WEAK
```

và có thể:

```text id="jjr2qh"
UNIQUE
```

target-specific.

---

# 14. Symbol visibility

Phân biệt:

```text id="z3k6z7"
Axiom pub
```

với:

```text id="q4v0rq"
linker-visible symbol
```

Compiler quyết định export:

```axiom id="s0qg6u"
@export("foo")
```

---

# 15. Name mangling

Axiom native symbol:

```text id="c0z7ax"
_ZN...
```

hay format khác không nên bị hard-code ngay.

Compiler cần:

```text id="2x5qz5"
SymbolMangler
```

Name chứa:

```text id="p0r4i1"
package
module
type
function
generic arguments
ABI
```

---

# 16. Generic symbols

```axiom id="gr3x6q"
fn max<T>(...)
```

`max<i32>` có thể được instantiate thành symbol riêng.

Nhưng compiler có thể inline và loại bỏ symbol.

Do đó symbol identity không phải source identity.

---

# 17. Explicit exported symbol

Ví dụ:

```axiom id="4h9m0p"
@export("calculate")
extern "C"
fn calculate(...)
```

Object symbol:

```text id="4i2n7w"
calculate
```

không mang Axiom mangling.

---

# 18. Relocation

Đây là phần linker quan trọng.

Machine instruction có thể chứa:

```text id="19o1gr"
address of function
address of global
relative offset
TLS address
```

nhưng symbol chưa biết final address.

Compiler tạo:

```text id="d7k2v1"
Relocation {
    offset
    symbol
    type
    addend
}
```

---

# 19. Ví dụ

Source:

```axiom id="r8f55s"
foo()
```

Machine code có thể cần:

```text id="quq8k5"
CALL <unknown foo>
```

Object:

```text id="v6w2u9"
.text
  E8 00 00 00 00

relocation:
  offset = 1
  symbol = foo
  type = PCREL32
```

Linker sau đó patch.

---

# 20. Relocation không được hard-code vào frontend

Frontend chỉ biết:

```text id="lxjz1e"
call foo
```

ABI lowering/machine backend quyết định:

```text id="8j7r1q"
CALL
relocation kind
```

Object writer serialize target-specific relocation.

---

# 21. Linker architecture

Tôi đề xuất:

```text id="2n7g6v"
Axiom Linker
 ├── Input Reader
 ├── Symbol Resolver
 ├── Archive Reader
 ├── Section Merger
 ├── COMDAT Resolver
 ├── GC
 ├── ICF
 ├── Layout Engine
 ├── Relocation Engine
 ├── Dynamic Link Editor
 ├── TLS Layout
 ├── Debug Merger
 └── Output Writer
```

---

# 22. Linker không cần hiểu Axiom semantics

Rất quan trọng.

Linker chỉ cần hiểu:

```text id="9up9e3"
objects
symbols
sections
relocations
ABI metadata
```

Không cần hiểu:

```text id="kq6n7j"
ownership
traits
borrow/view
generics
async
```

Những thứ đó đã được erase trước object generation.

---

# 23. Static linking

Input:

```text id="y7r0j3"
main.o
foo.o
libbar.a
```

Linker:

```text id="w6r0n8"
resolve symbols
 ↓
select sections
 ↓
layout
 ↓
apply relocations
 ↓
write executable
```

---

# 24. Archive

Static library:

```text id="j9d2gi"
libfoo.a
```

thực chất là collection:

```text id="q8c6g4"
foo1.o
foo2.o
foo3.o
```

Linker chỉ lấy object cần thiết.

---

# 25. Section garbage collection

Nếu:

```text id="f7y9ad"
foo()
bar()
baz()
```

chỉ `foo()` được dùng.

Linker có thể bỏ:

```text id="c4h1o6"
bar
baz
```

nếu section graph chứng minh không reachable.

---

# 26. Function sections

Compiler nên có khả năng:

```text id="z5a3mn"
.text.foo
.text.bar
```

để linker GC chính xác.

Tương tự data:

```text id="z1q5vl"
.rodata.string123
```

---

# 27. Dead stripping

Pipeline:

```text id="j7y1ot"
Compiler DCE
        ↓
LTO
        ↓
Linker GC
```

Ba tầng bổ sung nhau.

---

# 28. COMDAT / duplicate folding

Generic monomorphization có thể tạo cùng implementation ở nhiều compilation units.

Linker cần cơ chế:

```text id="o0s7tq"
COMDAT
weak ODR-like resolution
```

để tránh duplicate symbol.

---

# 29. Nhưng tốt hơn: compiler cache specialization

Axiom compiler có thể giảm duplication trước linker:

```text id="5i8h1v"
specialization cache
```

Nhưng linker vẫn phải xử lý duplicate vì:

- parallel compilation
- separate packages
- prebuilt artifacts.

---

# 30. ICF

Identical Code Folding:

```text id="x3r5g4"
foo() == bar()
```

về machine semantics.

Linker có thể merge.

Nhưng phải cẩn thận với:

```text id="o7v9s2"
function address identity
```

Nếu source có observable function pointer identity, không được merge nếu semantics bị thay đổi.

---

# 31. Function address identity

Đây là lý do optimizer/linker phải phân biệt:

```text id="a6t5ve"
same behavior
```

với:

```text id="2q5q8w"
same address
```

Axiom không nên mặc định đảm bảo hai function khác nhau có địa chỉ khác nhau.

Nhưng nếu:

```text id="h4d7b0"
&foo
```

được observable, linker phải giữ semantics cần thiết.

---

# 32. LTO

Axiom LTO nên hoạt động trên:

```text id="1xg0om"
Verified MIR
```

hoặc:

```text id="d7f4g1"
Axiom LIR
```

trước khi tạo machine object.

Điều này mạnh hơn việc chỉ merge assembly/object.

---

# 33. LTO pipeline

```text id="b9t1c3"
Package A MIR
Package B MIR
Package C MIR
       ↓
Whole Program IR
       ↓
inline
devirtualize
specialize
DCE
vectorize
       ↓
target lowering
```

---

# 34. Dynamic library

Không phải mọi symbol đều biết lúc link.

Ví dụ:

```text id="8r1j8k"
foo.dll
```

hoặc:

```text id="6i3k4n"
libfoo.so
```

Executable có:

```text id="x8p6q3"
import table
```

và dynamic linker resolve runtime.

---

# 35. Axiom dynamic linking

Library:

```axiom id="d7k2pl"
@export("foo")
extern "C"
fn foo(...)
```

Executable:

```axiom id="n5v8m2"
extern "C"
fn foo(...)
```

linker có thể tạo import relocation.

---

# 36. Symbol versioning

Linux có symbol versioning.

Axiom linker có thể hỗ trợ target-specific:

```text id="e3v6q8"
foo@LIB_1.0
```

nhưng không đưa vào language Core.

---

# 37. TLS linking

TLS là phần khó.

Compiler tạo:

```text id="r2f7e9"
TLS symbol
```

Linker:

```text id="z4k3v1"
TLS section layout
TLS relocation
```

Target ABI xử lý.

---

# 38. PIE / ASLR

Executable có thể cần:

```text id="u2y9z7"
position-independent code
```

Linker phải tạo relocation model phù hợp.

Axiom compiler không nên assume absolute addresses trong hosted code.

---

# 39. Linker script

Không nên bắt user viết GNU linker script.

Axiom có thể có declarative:

```text id="3k7m1q"
[target.layout]
text = ...
rodata = ...
data = ...
```

nhưng system/embedded users đôi khi cần custom placement.

Do đó cho phép:

```text id="1x2n8s"
--link-layout=foo.axlayout
```

với một **Axiom linker layout format** đơn giản.

---

# 40. Không import linker-script language của GNU

Nếu Axiom muốn độc lập thực sự, không nên phụ thuộc:

```text id="e7u5b1"
ld script
```

về lâu dài.

Có thể support GNU linker script compatibility như tool/importer sau này.

---

# 41. Memory regions

Embedded linker cần:

```text id="0k3z2v"
FLASH
RAM
MMIO
BOOT
```

Axiom layout file có thể:

```text id="s6g8p4"
region FLASH origin=... length=...
region RAM   origin=... length=...
```

và:

```text id="5y9q3k"
.text → FLASH
.data → RAM
```

---

# 42. Section placement

Ví dụ:

```text id="f2q8w1"
.rodata → FLASH
.text   → FLASH
.data   → RAM AT FLASH
.bss    → RAM
```

Linker có thể generate:

```text id="s8f0h5"
copy table
```

cho startup.

---

# 43. Startup copy

Freestanding embedded:

```text id="x6k4y8"
FLASH:
    initial .data

startup:
    copy .data → RAM
    zero .bss
    call @entry
```

Axiom startup library có thể generated từ linker metadata.

---

# 44. Object formats

### ELF

Ưu tiên đầu tiên.

Lý do:

- Linux
- embedded
- relatively documented
- flexible
- relocations rõ.

---

# 45. PE/COFF

Windows:

```text id="b8r3h1"
PE header
COFF sections
imports
exports
relocations
TLS
resources
```

Axiom linker cần native support.

---

# 46. Mach-O

macOS/iOS:

```text id="m8x5q3"
Mach header
load commands
segments
sections
symbols
relocations
code signature integration
```

Code signing có thể cần platform toolchain support.

---

# 47. WASM

Khác hẳn:

```text id="j3v8z5"
sections
types
functions
tables
memories
imports
exports
code
data
```

Không phải traditional relocation-linked executable.

Do đó WASM writer riêng.

---

# 48. Code signing

Axiom compiler không nên tự nhúng mọi hệ thống signing vào compiler.

Ví dụ iOS/macOS cần:

```text id="n5k8d1"
code signature
entitlements
provisioning
```

Đây là **platform packaging layer**.

Compiler tạo Mach-O hợp lệ; platform signer đóng gói/sign.

---

# 49. Windows resources

`.exe` có thể cần:

```text id="h7q2m6"
icon
manifest
version resource
```

Resource compiler có thể là Axiom tool:

```text id="e1r7x9"
axiom res
```

không cần C toolchain.

---

# 50. Debug information

Không nên tự thiết kế debug format mới.

Axiom có thể generate:

```text id="w2j8k0"
DWARF
PDB
CodeView
```

tùy target.

---

# 51. Debug info không semantic

Debug information:

```text id="p4c7m9"
source line
variable
type
scope
inline stack
```

không ảnh hưởng program semantics.

---

# 52. Source → machine mapping

Compiler phải giữ:

```text id="q5t8x2"
SourceSpan
 ↓
HIR node
 ↓
MIR instruction
 ↓
LIR instruction
 ↓
Machine instruction
```

để debugger có thể:

```text id="0d3r8a"
breakpoint
step
inspect variable
```

---

# 53. Optimized variable location

Một variable:

```axiom id="b3w6y1"
let x = ...
```

có thể:

```text id="f8z2r4"
register
stack
constant
optimized away
```

Debug info phải mô tả location ranges.

Không thể đảm bảo debugger luôn nhìn thấy `x`.

---

# 54. Panic information

Nếu:

```text id="s5x1n8"
panic("bad")
```

compiler có thể emit:

```text id="x3p7k2"
panic metadata
source location
message
```

chỉ khi panic/debug configuration yêu cầu.

Binary size-sensitive build có thể strip message.

---

# 55. Stack unwinding

Hai modes:

```text id="1q8r3s"
panic=abort
panic=unwind
```

Abort:

```text id="m9t5v1"
tiny
simple
```

Unwind:

```text id="p6w4x8"
unwind metadata
personality
cleanup
```

---

# 56. No mandatory exception ABI

Axiom không cần:

```text id="5n2y7q"
try
catch
throw
```

nên linker/runtime không cần C++ exception machinery.

---

# 57. Link-time optimization of runtime

Runtime components:

```text id="f0n3z8"
allocator
panic
thread
async
reflection
```

được link only if referenced.

Linker GC + compiler dependency graph giúp binary nhỏ.

---

# 58. Final executable pipeline

Ví dụ Linux:

```text id="j9t5x3"
main.axiom
    ↓
parse/typecheck
    ↓
MIR
    ↓
verify
    ↓
optimize
    ↓
x86 LIR
    ↓
machine encoder
    ↓
main.o
    ↓
Axiom linker
    ↓
ELF
    ↓
Linux executable
```

---

# 59. Không cần LLVM

LLVM có thể được dùng **trong bootstrap/prototype**, nhưng kiến trúc Axiom không được phụ thuộc vào LLVM IR.

Đây là điểm cực kỳ quan trọng.

Nếu frontend tạo:

```text id="8v2m5n"
Axiom → LLVM IR
```

thì về lâu dài LLVM trở thành hidden language dependency.

Thay vào đó:

```text id="f9p6q1"
Axiom
 ↓
MIR
 ↓
Axiom LIR
 ↓
Machine IR
```

LLVM chỉ là optional backend trong giai đoạn đầu.

---

# 60. Có thể dùng LLVM lúc đầu không?

Có.

Prototype:

```text id="v7k1r3"
Axiom frontend
 ↓
MIR
 ↓
LLVM adapter
 ↓
LLVM
```

Nhưng production architecture:

```text id="h6m2q8"
Axiom frontend
 ↓
MIR
 ↓
Axiom optimizer
 ↓
Axiom LIR
 ↓
Axiom backend
```

Như vậy LLVM có thể bị xóa hoàn toàn sau này.

---

# 61. Bootstrap stages

Tôi đề xuất chính thức:

```text id="b6t8x1"
Stage 0
Axiom prototype + LLVM backend
```

↓

```text id="q4n7m2"
Stage 1
Axiom MIR + x86-64 backend
```

↓

```text id="r8p3k5"
Stage 2
Axiom object writer + ELF linker
```

↓

```text id="w1y6c9"
Stage 3
Axiom compiler rewritten in Axiom
```

↓

```text id="z5k2h8"
Stage 4
Self-hosted Axiom compiler
```

↓

```text id="a9m4v7"
Stage 5
PE/Mach-O/ARM/RISC-V/WASM
```

---

# 62. Không nên tự viết tất cả target cùng lúc

Thứ tự hợp lý:

```text id="g4j8m1"
x86-64 Linux
      ↓
x86-64 Windows
      ↓
AArch64 Linux
      ↓
AArch64 macOS/iOS
      ↓
WASM
      ↓
RISC-V
```

Lý do:

x86-64 Linux giúp test:

- ELF
- SysV ABI
- relocations
- linker
- debugger
- runtime.

---

# 63. Axiom Linker v0.1 scope

Không cần ngay:

```text id="r7x3c2"
full gold/lld replacement
```

MVP:

```text id="1q8z5v"
ELF64
x86-64
static executable
```

hỗ trợ:

- `.text`
- `.rodata`
- `.data`
- `.bss`
- symbols
- PC-relative relocations
- absolute relocations
- archives
- section GC
- entry point.

---

# 64. Sau đó mới dynamic linking

Stage tiếp:

```text id="x4m7p9"
ELF shared library
PLT/GOT
TLS
PIE
dynamic symbols
```

Sau đó:

```text id="s1c6y8"
PE/COFF
Mach-O
```

---

# 65. Object invariants

```text id="j3w8p4"
AOBJ-01  Object Format Is Backend-Level
AOBJ-02  Frontend Does Not Depend On Object Format
AOBJ-03  Machine Encoder Does Not Require An Assembler
AOBJ-04  Assembly Output Is Diagnostic/Optional
AOBJ-05  Sections Have Explicit Semantics
AOBJ-06  Symbols Are Separate From Source Names
AOBJ-07  Relocations Are Explicit
AOBJ-08  ABI Determines Relocation Requirements
AOBJ-09  Linker Does Not Understand Axiom Ownership
AOBJ-10  Linker Operates On Object-Level Semantics
AOBJ-11  Dead Sections May Be Eliminated
AOBJ-12  Duplicate Code May Be Folded When Semantically Safe
AOBJ-13  Function Address Observability Constrains Folding
AOBJ-14  LTO Operates Before Final Machine Object
AOBJ-15  Static Linking Is First-Class
AOBJ-16  Dynamic Linking Is Explicit
AOBJ-17  TLS Is Target-Aware
AOBJ-18  PIE/PIC Are Target Policies
AOBJ-19  Embedded Layout Is Explicit
AOBJ-20  Debug Information Is Non-Semantic
AOBJ-21  Panic Metadata Is Optional
AOBJ-22  Unwind Is Optional
AOBJ-23  No Mandatory Exception ABI
AOBJ-24  Axiom Does Not Require An External Assembler
AOBJ-25  Axiom Does Not Require LLVM In Final Architecture
AOBJ-26  Axiom Can Eventually Produce Native Objects Directly
AOBJ-27  Axiom Linker Can Eventually Produce Native Executables
AOBJ-28  Object Generation Is Deterministic
```

---

# 66. Điều này giải quyết một mục tiêu rất lớn

Sau phần này, mục tiêu:

> “Axiom không phụ thuộc compiler bên thứ ba”

được chia thành hai nghĩa khác nhau:

### Không phụ thuộc để compile Axiom

Có thể đạt:

```text
Axiom compiler
+ Axiom backend
+ Axiom object writer
+ Axiom linker
```

### Không phụ thuộc thư viện hệ thống

Không thể và cũng không nên hiểu theo nghĩa tuyệt đối.

Ví dụ Windows executable vẫn phải gọi:

```text
Windows kernel/API
```

Linux program vẫn dùng:

```text
Linux syscall
```

Axiom chỉ không cần **compiler/linker bên thứ ba** để tạo binary.

---

# 67. Đây là ranh giới đúng

```text
                 Axiom owns
────────────────────────────────────
Language semantics
Compiler
Optimizer
MIR
LIR
Machine encoder
Object writer
Linker
Runtime components
Std library
────────────────────────────────────
                 Platform owns
OS kernel
Firmware
CPU hardware
GPU driver
Code-signing infrastructure
```

Axiom không cần “sở hữu” OS để là một native toolchain độc lập.

---

# Tiếp tục → Debugger, Profiler, Sanitizer & Developer Tooling

Phần tiếp theo sẽ rất quan trọng vì một systems language không thể thực sự dùng được nếu compiler chỉ tạo machine code.

Ta cần thiết kế một hệ thống thống nhất:

```text
axiom check
axiom build
axiom run
axiom test
axiom debug
axiom profile
axiom trace
axiom inspect
axiom dump-mir
axiom dump-lir
axiom dump-machine
```

và đặc biệt là:

**sanitizer nên nằm ở đâu nếu Axiom safe code đã được compiler kiểm tra?**

Tôi sẽ thiết kế tiếp theo hướng **sanitizer chủ yếu dành cho unsafe/FFI/concurrency/platform code**, thay vì biến mọi build debug thành một runtime khổng lồ.