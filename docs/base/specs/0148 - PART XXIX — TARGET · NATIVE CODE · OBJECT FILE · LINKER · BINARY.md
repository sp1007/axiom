# PART XXIX — TARGET · NATIVE CODE · OBJECT FILE · LINKER · BINARY

Đây là phần khóa **đường đi từ Axiom source đến executable native**.

Mục tiêu không chỉ là:

> “Axiom có backend x86-64.”

Mà là:

> **Axiom phải có kiến trúc đủ để cuối cùng tự tạo native binary mà không cần LLVM, GCC, Clang hay compiler bên thứ ba.**

Tuy nhiên, cần phân biệt:

```text
Không phụ thuộc compiler bên thứ ba
≠
Không thể link với thư viện hệ điều hành/bên thứ ba
```

Axiom compiler có thể tự tạo:

```text
ELF
PE/COFF
Mach-O
WASM
```

nhưng vẫn có thể link:

```text
libc
system framework
GPU driver
OS library
third-party native library
```

khi chương trình yêu cầu.

---

# 1. Pipeline native cuối cùng

Pipeline chính thức:

```text
Source
  ↓
AST
  ↓
HIR
  ↓
Typed HIR
  ↓
MIR
  ↓
Verified MIR
  ↓
Semantic Optimization
  ↓
ABI MIR
  ↓
Axiom LIR
  ↓
Target Lowering
  ↓
Instruction Selection
  ↓
Machine IR
  ↓
Machine Optimization
  ↓
Register Allocation
  ↓
Spill / Reload
  ↓
Final Machine IR
  ↓
Instruction Encoding
  ↓
Object File
  ↓
Link
  ↓
Native Binary
```

Không có:

```text
Axiom
 ↓
C
 ↓
GCC
```

và cũng không bắt buộc:

```text
Axiom
 ↓
LLVM IR
 ↓
LLVM
```

LLVM có thể được dùng **trong bootstrap**, nhưng không được là semantic dependency của Axiom cuối cùng.

---

# 2. Target abstraction

Compiler frontend không được biết:

```text
x86
ARM
RISC-V
WASM
```

Frontend chỉ biết:

```text
types
ownership
capabilities
control flow
ABI
semantic operations
```

Target backend cung cấp:

```text
TargetDescription
```

Ví dụ:

```text
TargetDescription {
    architecture
    pointer_width
    endian
    integer_widths
    float_formats
    alignment_rules
    calling_convention
    register_file
    instruction_set
    object_format
    linker_format
    os_abi
}
```

---

# 3. Target triple

Axiom dùng target identifier dạng:

```text
architecture-vendor-os-environment
```

Ví dụ:

```text
x86_64-pc-windows-msvc
x86_64-unknown-linux-gnu
aarch64-apple-darwin
aarch64-apple-ios
aarch64-linux-android
wasm32-unknown-wasm
riscv64-unknown-linux
```

Nhưng target triple chỉ là **configuration identity**.

Nó không tự động kéo theo C compiler.

---

# 4. Native backend đầu tiên

Để bootstrap hiệu quả:

```text
x86_64
```

là backend đầu tiên.

Lý do:

- instruction set tương đối phổ biến
- Linux/Windows đều quan trọng
- dễ kiểm tra binary
- có debugger/tooling tốt
- dễ tạo ELF trước
- sau đó mở rộng PE/COFF

Roadmap hợp lý:

```text
x86_64 + ELF
        ↓
x86_64 + PE/COFF
        ↓
AArch64 + ELF
        ↓
AArch64 + Mach-O
        ↓
WASM
        ↓
RISC-V
```

---

# 5. LIR

LIR là abstraction cuối cùng trước target-specific machine code.

Ví dụ:

```text
%1 = add.i64 %a, %b
%2 = load.i32 [%ptr]
store.i32 %2, [%out]
br %cond, block1, block2
call @foo(%1)
return %2
```

LIR phải:

- target-neutral
- explicit memory operation
- explicit atomic operation
- explicit call
- explicit control flow
- không chứa ownership source semantics

Ownership đã được verify trước đó.

---

# 6. Ownership bị erase ở đâu?

Sau:

```text
Verified MIR
```

compiler đã chứng minh:

```text
ownership valid
drop valid
capability valid
alias valid
concurrency valid
```

Sau đó:

```text
ownership
view
mut_view
Send
Share
```

có thể được erase khỏi machine semantics nếu không observable.

Ví dụ:

```axiom id="v7q9t0"
fn sum(a: view<i32>) -> i32
```

machine code chỉ cần:

```text
pointer
length
```

hoặc representation phù hợp.

Không cần runtime:

```text
OwnerObject
CapabilityObject
BorrowObject
```

---

# 7. ABI lowering

Trước khi machine code, compiler phải quyết định:

```text
argument passing
return passing
struct passing
alignment
register use
stack layout
variadic ABI
aggregate return
calling convention
```

Ví dụ:

```text
Axiom function:

fn add(a: i64, b: i64) -> i64
```

có thể lower thành:

```text
RDI = a
RSI = b
RAX = result
```

theo ABI target tương ứng.

---

# 8. Axiom ABI

Axiom có ABI native:

```text
extern "axiom"
```

ABI này được compiler kiểm soát.

Nó có thể thay đổi giữa compiler versions.

Không được hứa:

```text
Axiom v1.0 ABI == Axiom v2.0 ABI
```

trừ khi một stable ABI profile được khóa riêng.

---

# 9. C ABI

Interop:

```axiom
extern "C" fn foo(x: i32) -> i32
```

sẽ dùng C ABI.

Nhưng:

```text
extern "C"
```

không biến type Axiom thành C-compatible một cách thần kỳ.

Ví dụ:

```axiom
struct User {
    name: Text
}
```

không tự động trở thành C struct hợp lệ.

Phải có representation contract.

---

# 10. Representation lowering

Compiler phân biệt:

```text
semantic type
    ↓
data representation
    ↓
ABI representation
    ↓
machine representation
```

Ví dụ:

```text
Option<NonNull<T>>
```

có thể được tối ưu thành:

```text
nullable pointer
```

nếu compiler chứng minh niche representation hợp lệ.

Programmer không được phụ thuộc vào optimization này nếu ABI chưa yêu cầu.

---

# 11. Instruction selection

Ví dụ MIR:

```text
x = a + b
```

LIR:

```text
ADD i64
```

x86:

```text
add rax, rbx
```

AArch64:

```text
add x0, x1, x2
```

RISC-V:

```text
add a0, a1, a2
```

Semantics giống nhau.

Machine representation khác nhau.

---

# 12. Machine IR

Machine IR chứa:

```text
physical registers
virtual registers
machine instructions
flags
memory operands
addressing modes
calling convention
register constraints
```

Ví dụ x86:

```text
%v1 = COPY RDI
%v2 = COPY RSI
%v3 = ADD %v1, %v2
COPY RAX, %v3
RET
```

---

# 13. Register allocation

Axiom compiler cần register allocator riêng.

Input:

```text
virtual registers
```

Output:

```text
physical registers
```

Ví dụ:

```text
v1 → RAX
v2 → RBX
v3 → RCX
```

Nếu thiếu register:

```text
spill
```

xuống stack.

---

# 14. Register allocation không thuộc language semantics

Programmer không được viết:

```text
x lives in RAX
```

trong safe Core.

Nếu cần machine-specific control:

```text
unsafe
target-specific intrinsic
inline asm
```

được sử dụng.

---

# 15. Instruction encoding

Sau register allocation:

```text
Machine IR
```

được encode thành byte.

Ví dụ:

```text
machine instruction
      ↓
opcode
modrm
sib
immediate
displacement
```

Axiom encoder phải hiểu target ISA.

Không cần assembler bên ngoài để tạo object code.

---

# 16. Object writer

Compiler tự tạo:

### ELF

```text
ELF header
program headers
section headers
sections
symbols
string tables
relocations
debug sections
```

### PE/COFF

```text
DOS/PE headers
COFF sections
symbols
relocations
imports
exports
debug information
```

### Mach-O

```text
Mach header
load commands
segments
sections
symbols
relocations
code signature metadata where required
```

### WASM

```text
module
type section
function section
code section
data section
export section
custom sections
```

---

# 17. Object file ≠ executable

Axiom phải phân biệt:

```text
source
object
static library
shared library
executable
```

Ví dụ:

```text
foo.axiom
    ↓
foo.o
    ↓
libfoo.a
```

hoặc:

```text
foo.axiom
    ↓
foo.o
    ↓
program.exe
```

---

# 18. Relocation

Compiler không phải lúc nào biết final address.

Object file có:

```text
relocation entry
```

Ví dụ:

```text
CALL foo
```

chưa biết:

```text
foo = 0x401000
```

Linker sẽ resolve.

Axiom object writer phải tạo relocation chính xác theo target.

---

# 19. Linker

Axiom cuối cùng nên có linker riêng.

Pipeline:

```text
.o
.a
.so/.dll/.dylib
system libraries
      ↓
Axiom Linker
      ↓
Executable
```

Linker cần xử lý:

```text
symbol resolution
section layout
relocation
weak symbols
COMDAT/group semantics
TLS
imports/exports
dynamic linking
debug sections
unwind metadata
```

---

# 20. Linker không biết ownership

Đây là boundary rất quan trọng.

Linker chỉ biết:

```text
symbols
sections
relocations
addresses
ABI
```

Nó không biết:

```text
Move
Copy
Drop
view
Send
Share
```

Những thứ đó đã được giải quyết trước machine/object level.

---

# 21. Static linking

Axiom ưu tiên static linking khi platform cho phép.

Ví dụ:

```bash
axiom build --static
```

Compiler/linker có thể tạo binary gần như self-contained.

Nhưng system APIs vẫn có thể yêu cầu OS components.

---

# 22. Dynamic linking

Dynamic linking explicit:

```bash
axiom build --dynamic
```

Ví dụ Windows:

```text
program.exe
foo.dll
```

Linux:

```text
program
libfoo.so
```

macOS:

```text
program
libfoo.dylib
```

---

# 23. Dead code elimination

Linker và compiler đều có thể loại bỏ code không dùng.

Ví dụ:

```text
module A
module B
module C
```

Nếu program chỉ gọi A:

```text
B
C
```

có thể bị loại bỏ.

Axiom không cần giữ toàn bộ standard library trong executable.

---

# 24. Whole-program optimization

Khi static linking + LTO:

```text
Object
   ↓
Link IR
   ↓
Whole-program optimization
   ↓
Machine code
```

có thể thực hiện:

- cross-module inlining
- dead code elimination
- devirtualization
- constant propagation
- identical code folding
- global optimization

---

# 25. Thin/full LTO

Axiom hỗ trợ:

```text
LTO=none
LTO=thin
LTO=full
```

Không thay đổi semantics.

---

# 26. Startup model

Hosted program:

```text
OS
 ↓
_process_start
 ↓
Axiom startup
 ↓
runtime initialization required by profile
 ↓
main()
 ↓
exit
```

Không được có hidden initialization hàng loạt.

---

# 27. Freestanding

Freestanding:

```axiom
@entry
fn kernel_main() -> never {
    ...
}
```

Compiler có thể tạo binary không cần:

```text
libc
heap
thread runtime
async runtime
panic runtime
```

nếu program không sử dụng chúng.

---

# 28. Runtime component linking

Ví dụ:

```text
program A
```

chỉ dùng:

```text
main
```

→ runtime tối thiểu.

Program B:

```text
async
```

→ async executor nếu thực sự dùng.

Program C:

```text
threads
```

→ thread support.

Program D:

```text
panic=unwind
```

→ unwind support.

Đây là:

> **Capability-driven runtime.**

---

# 29. No mandatory runtime

Một executable Axiom hợp lệ có thể gần như:

```text
entry point
machine code
read-only data
data
bss
```

Không có:

```text
GC
object runtime
global runtime
reflection runtime
async runtime
```

nếu không cần.

---

# 30. Code size

Mục tiêu:

```text
small binary
```

không đạt bằng một trick duy nhất.

Axiom dùng:

```text
dead code elimination
LTO
generic specialization
runtime component elimination
section GC
string/data merging
cold path outlining
size optimization
minimal startup
```

---

# 31. `-Oz`

Ví dụ:

```bash
axiom build -Oz
```

cho phép compiler ưu tiên:

```text
binary size
```

thay vì:

```text
maximum throughput
```

Nhưng semantics không thay đổi.

---

# 32. CPU feature targeting

Axiom có:

```text
-target-cpu
-target-feature
```

Ví dụ:

```bash
axiom build \
    --target-cpu=native
```

hoặc:

```bash
axiom build \
    --target-feature=avx2
```

Compiler có thể vectorize mạnh hơn.

---

# 33. CPU dispatch

Nếu binary cần chạy nhiều CPU:

```text
baseline implementation
       +
feature-specific implementation
       ↓
runtime dispatch
```

Ví dụ:

```text
AVX2
AVX-512
NEON
SVE
```

Runtime dispatch phải explicit.

Không được CPU feature detection trở thành hidden semantic behavior.

---

# 34. SIMD

Axiom có thể cung cấp vector types:

```text
Vec<f32, 4>
Vec<i32, 8>
```

Nhưng semantic vector abstraction phải độc lập ISA.

Compiler có thể lower thành:

```text
SSE
AVX
AVX2
AVX-512
NEON
SVE
```

---

# 35. Endianness

Axiom không giả định mọi target little-endian.

Các API binary/network phải explicit endian:

```text
to_le
to_be
from_le
from_be
```

Không được:

```text
reinterpret integer bytes
```

mà giả định machine endian trong portable code.

---

# 36. Pointer width

`usize/isize` phụ thuộc target.

Ví dụ:

```text
wasm32 → 32 bit
x86_64 → 64 bit
aarch64 → 64 bit
```

Compiler phải kiểm tra mọi conversion nguy hiểm.

---

# 37. Object format abstraction

Compiler có:

```text
ObjectWriter
```

interface:

```text
write_header()
create_section()
define_symbol()
add_relocation()
write_debug()
finalize()
```

Implementations:

```text
ElfWriter
CoffWriter
MachOWriter
WasmWriter
```

Frontend không biết các format này.

---

# 38. Linker abstraction

Tương tự:

```text
Linker
```

có:

```text
resolve_symbols()
layout_sections()
apply_relocations()
generate_imports()
generate_exports()
generate_tls()
emit_binary()
```

Implement:

```text
ElfLinker
CoffLinker
MachOLinker
WasmLinker
```

---

# 39. System linker compatibility

Ban đầu Axiom **có thể dùng system linker** để bootstrap.

Ví dụ:

```text
Axiom compiler
    ↓
Axiom object
    ↓
system linker
```

Đây là chấp nhận được trong bootstrap.

Nhưng self-hosting final target:

```text
Axiom compiler
    ↓
Axiom object writer
    ↓
Axiom linker
    ↓
binary
```

không cần linker bên ngoài.

---

# 40. Bootstrap stages

### Stage 0

External compiler:

```text
Axiom compiler written in C/Rust/etc.
```

có thể sử dụng:

```text
LLVM
system assembler
system linker
```

### Stage 1

Axiom compiler có:

```text
own parser
own HIR
own type checker
own MIR
```

### Stage 2

Axiom có:

```text
own MIR interpreter
```

### Stage 3

Axiom có:

```text
own LIR
own x86-64 backend
own encoder
own ELF writer
```

### Stage 4

Axiom compiler viết bằng Axiom:

```text
axiom compiler
```

### Stage 5

Self-hosting:

```text
Axiom compiler
      ↓
Axiom compiler
      ↓
native executable
```

### Stage 6

Own linker:

```text
compiler
+
object writer
+
linker
```

---

# 41. Bootstrap compiler không phải semantic authority

Trong bootstrap:

```text
external compiler
```

chỉ là execution mechanism.

Semantic authority vẫn là:

```text
Axiom Specification
+
Oracle
+
Conformance Tests
```

Nếu bootstrap compiler và Oracle khác nhau:

```text
Oracle + Spec
```

là nguồn kiểm chứng.

---

# 42. Compiler self-build

Một milestone cực quan trọng:

```text
axiom build compiler/
```

tạo ra:

```text
axiom-native
```

sau đó:

```text
./axiom-native build compiler/
```

tạo compiler mới.

So sánh:

```text
compiler-bootstrap
vs
compiler-selfhosted
```

về:

```text
semantic output
ABI
tests
compiler behavior
```

---

# 43. Compiler determinism

Nếu cùng:

```text
source
compiler version
target
profile
dependency graph
configuration
```

thì compiler phải tạo cùng semantic result.

Binary reproducibility là mục tiêu mạnh hơn:

```text
same semantic result
→ ideally same bytes
```

---

# 44. Reproducible native binary

Để binary deterministic:

không được vô tình chứa:

```text
timestamp
absolute build path
random UUID
host-specific ordering
nondeterministic symbol ordering
```

trừ khi explicitly requested.

Build metadata phải deterministic.

---

# 45. Build ID

Nếu cần build identity:

```text
BuildID
```

phải được sinh từ:

```text
content hash
```

hoặc explicit deterministic input.

Không dùng random UUID mặc định.

---

# 46. Debug symbols tách khỏi binary

Có thể tạo:

```text
program
program.debug
```

hoặc target-specific debug artifact.

Release binary có thể:

```text
strip debug
```

nhưng vẫn giữ mapping external.

---

# 47. Unwind information

Axiom không có C++ exception.

Nhưng nếu:

```text
panic=unwind
```

thì cần unwind metadata.

Unwind mechanism là:

```text
runtime/profile/platform implementation
```

không phải exception language.

---

# 48. Panic=abort

Đây là profile nhỏ:

```bash
axiom build --panic=abort
```

Không cần unwind tables/runtime nếu target cho phép loại bỏ.

Đây sẽ là profile rất quan trọng cho:

- embedded
- kernel
- tiny executable
- size optimization

---

# 49. Symbol visibility

Phân biệt:

```text
pub
```

với:

```text
@export
```

Ví dụ:

```axiom
pub fn internal_api() { ... }
```

không nhất thiết tạo ELF export.

Muốn export:

```axiom
@export("foo")
extern "C" fn foo() { ... }
```

---

# 50. ABI boundary kiểm tra

Compiler phải có:

```bash
axiom abi-check
```

để kiểm tra:

```text
size
alignment
field offsets
calling convention
symbol
parameter ABI
return ABI
enum representation
```

Ví dụ:

```text
ABI compatible: yes
```

hoặc:

```text
ABI incompatible:
User.size changed 32 → 40
```

---

# 51. ABI fingerprint

Build system đã có:

```text
ABIHash
```

ABIHash thay đổi khi:

```text
layout
calling convention
export symbol
representation
```

thay đổi.

Semantic API có thể không đổi.

Ví dụ:

```text
APIHash = same
ABIHash = changed
```

→ cần relink native consumers.

---

# 52. Stable ABI

Axiom không mặc định stable ABI.

Muốn stable:

```text
@abi("axiom-v1")
```

hoặc:

```text
extern "C"
@repr(C)
```

tùy boundary.

Stable ABI là contract.

---

# 53. WASM

WASM là target đặc biệt.

Axiom có thể lower:

```text
Axiom
 ↓
Axiom LIR
 ↓
WASM code
```

WASM không cần:

```text
ELF
```

hay:

```text
native linker
```

WASM linker/section merger là một backend riêng.

---

# 54. WASM memory model

WASM linear memory không được giả định giống native virtual memory.

Axiom semantic model vẫn giữ:

```text
ownership
view
allocation
```

nhưng backend map sang:

```text
linear memory
```

hoặc target-specific representation.

---

# 55. Mobile targets

AArch64:

```text
Android
iOS
```

dùng cùng:

```text
AArch64 backend
```

nhưng khác:

```text
ABI
object format
OS ABI
startup
linking
framework integration
```

Do đó:

```text
ISA != platform
```

là invariant quan trọng.

---

# 56. GPU binary

GPU backend không dùng host object format trực tiếp.

Ví dụ:

```text
Axiom kernel
 ↓
GPU-specific IR
 ↓
SPIR-V / PTX / target code
```

Host compiler tạo:

```text
host executable
+
GPU artifact
```

và resource metadata liên kết chúng.

---

# 57. Multi-artifact build

Một package có thể tạo:

```text
program.exe
shader.spv
debug.pdb
metadata.json
```

Build graph phải hiểu đây là:

```text
related artifacts
```

không phải tất cả đều là native executable.

---

# 58. Link-time ownership

Không có ownership analysis ở linker.

Nếu hai object:

```text
foo.o
bar.o
```

cùng export symbol:

```text
foo
```

→ linker error.

Đây là symbol conflict, không phải ownership error.

---

# 59. Native binary invariants

## ATARGET

**ATARGET-20 — Target Semantics Are Separate From Frontend Semantics**

**ATARGET-21 — Target Description Is Explicit**

**ATARGET-22 — ISA Is Distinct From Platform ABI**

**ATARGET-23 — ABI Lowering Is Explicit**

**ATARGET-24 — Machine Representation Is Not Language Semantics**

**ATARGET-25 — Register Allocation Does Not Affect Language Semantics**

**ATARGET-26 — Instruction Selection Preserves Semantics**

**ATARGET-27 — Machine Encoding Preserves Machine IR Semantics**

**ATARGET-28 — Unsupported Target Operations Are Explicit Errors**

---

## Object

**AOBJECT-20 — Object Files Are Intermediate Native Artifacts**

**AOBJECT-21 — Object Representation Is Target-Specific**

**AOBJECT-22 — Relocations Are Explicit**

**AOBJECT-23 — Symbols Are Distinct From Axiom Names**

**AOBJECT-24 — Debug Metadata Is Separate From Core Object Semantics**

**AOBJECT-25 — Object Writer Does Not Perform Ownership Verification**

---

## Linker

**ALINK-20 — Linking Is Distinct From Compilation**

**ALINK-21 — Linker Resolves Symbols And Relocations**

**ALINK-22 — Linker Does Not Define Axiom Language Semantics**

**ALINK-23 — Static Linking Is Explicitly Supported**

**ALINK-24 — Dynamic Linking Is Explicit**

**ALINK-25 — Dead Code Elimination May Occur At Link Time**

**ALINK-26 — Linker ABI Must Match Object ABI**

**ALINK-27 — Linker Errors Are Distinct From Semantic Errors**

---

## Native independence

**ANATIVE-20 — Final Native Compilation Does Not Require A Third-Party Compiler**

**ANATIVE-21 — Third-Party Native Libraries May Still Be Linked**

**ANATIVE-22 — System APIs Are Not Compiler Dependencies**

**ANATIVE-23 — Bootstrap Dependencies May Be Temporary**

**ANATIVE-24 — Final Self-Hosted Compiler Must Be Semantically Self-Sufficient**

**ANATIVE-25 — Native Code Generation Is Not Defined By LLVM**

---

# 60. Kiến trúc native hoàn chỉnh

Axiom bây giờ có thể hình dung:

```text
                       AXIOM SOURCE
                            │
                            ▼
                    ┌──────────────┐
                    │   FRONTEND   │
                    └──────┬───────┘
                           ▼
                         HIR
                           ▼
                       TYPE CHECK
                           ▼
                         MIR
                           ▼
                    ┌──────────────┐
                    │   VERIFIER   │
                    └──────┬───────┘
                           ▼
                     VERIFIED MIR
                           │
                           ▼
                     OPTIMIZATION
                           │
                           ▼
                          LIR
                           │
             ┌─────────────┼─────────────┐
             ▼             ▼             ▼
          x86-64         AArch64       RISC-V
             │             │             │
             ▼             ▼             ▼
        Machine IR    Machine IR    Machine IR
             │             │             │
             ▼             ▼             ▼
          Encoder        Encoder       Encoder
             │             │             │
             ▼             ▼             ▼
           ELF          Mach-O        ELF
             │             │             │
             └─────────────┼─────────────┘
                           ▼
                        LINKER
                           ▼
                     NATIVE BINARY
```

Đây là điểm rất quan trọng:

> **Axiom không cần phải biến thành C để trở thành native.**

---

# 61. Đánh giá mục tiêu “nhỏ như ASM”

Ở đây cần khóa lại một điểm thực tế.

Không thể đảm bảo:

```text
mọi Axiom program
```

có binary:

```text
size == handwritten assembly
```

vì binary size còn phụ thuộc:

- OS ABI
- startup
- dynamic/static linking
- unwind
- debug
- libc
- TLS
- security metadata
- architecture
- linker
- application requirements

Nhưng kiến trúc Axiom cho phép:

```text
abstraction
   ↓
compile-time verification
   ↓
erase
   ↓
machine code
```

nên **không có lý do kiến trúc nào khiến abstraction-level cao tự động kéo theo runtime overhead**.

Đây mới là mục tiêu đúng.

---

# 62. Một điểm rất quan trọng: Axiom không nên tự viết assembler

Không cần có:

```text
Axiom source
 ↓
Axiom assembly text
 ↓
assembler
```

Compiler có thể đi thẳng:

```text
Machine IR
 ↓
Encoder
 ↓
Object bytes
```

Điều này:

- nhanh hơn
- deterministic hơn
- không cần parser assembler
- không phụ thuộc assembler
- dễ kiểm soát relocation

Assembly text vẫn có thể là **debug/disassembly output**.

---

# 63. Axiom disassembler

Tooling có thể có:

```bash
axiom objdump program
```

hoặc:

```bash
axiom inspect --machine
```

Ví dụ:

```text
source:
    foo.axiom:42

machine:
    mov rax, rdi
    add rax, rsi
    ret
```

Source ↔ machine mapping lấy từ debug information.

---

# 64. Final bootstrap architecture

Khi Axiom hoàn thiện:

```text
Axiom Compiler
 ├── Lexer
 ├── Parser
 ├── Resolver
 ├── Type Checker
 ├── Trait Solver
 ├── MIR
 ├── Verifier
 ├── Optimizer
 ├── LIR
 ├── x86 Backend
 ├── ARM Backend
 ├── RISC-V Backend
 ├── WASM Backend
 ├── Object Writer
 └── Linker
```

đều có thể viết bằng Axiom.

Đây là lúc Axiom thực sự đạt:

> **self-hosted native systems language/toolchain.**

---

# PART XXIX — KẾT LUẬN

Đã khóa được tầng cuối của native execution:

```text
Semantic Language
      ↓
Verified MIR
      ↓
Optimization
      ↓
LIR
      ↓
Target Backend
      ↓
Machine Code
      ↓
Object
      ↓
Linker
      ↓
Native Binary
```

Không có dependency bắt buộc:

```text
LLVM
GCC
Clang
Rust compiler
C compiler
external assembler
external linker
```

ở trạng thái self-hosted cuối cùng.

---

# TIẾP THEO — PART XXX

Đây là phần cuối và cũng là phần quan trọng nhất để **đóng băng Axiom**:

## PART XXX — CONFORMANCE · LANGUAGE FREEZE · SELF-HOSTING · Axiom v1.0

Nó sẽ giải quyết 6 câu hỏi cuối:

1. **Làm sao chứng minh compiler thực sự implement đúng specification?**
2. **Làm sao một compiler Axiom mới biết mình không phá semantics cũ?**
3. **Axiom v1.0 gồm chính xác những gì và cái gì bị loại khỏi Core?**
4. **Conformance suite phải có những loại test nào?**
5. **Bootstrap từ compiler bên ngoài sang self-hosting từng bước ra sao?**
6. **Sau khi freeze, cơ chế evolution của Axiom sẽ như thế nào mà không biến language thành một mớ compatibility hacks?**

Đây sẽ là **phần đóng specification**, sau đó có thể thực hiện một **Global Contradiction Audit** trên toàn bộ 30 phần để tìm những chỗ còn xung đột trước khi biến thiết kế thành `AXIOM-SPECIFICATION.md`.