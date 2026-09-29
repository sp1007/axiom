Tiếp tục với **BOOTSTRAP-001 — Stage-0 Axiom Compiler**.

Đây là lúc chuyển từ kiến trúc sang một kế hoạch compiler có thể thực sự build được. Mục tiêu của Stage-0 không phải hỗ trợ toàn bộ Axiom, mà là tạo **hạt nhân đủ đúng để tự mở rộng thành compiler Axiom**.

# BOOTSTRAP-001 — STAGE-0 AXIOM COMPILER

## 1. Mục tiêu chính

Stage-0 phải tạo được đường đi hoàn chỉnh:

```text
Axiom source
    ↓
Lexer
    ↓
Parser
    ↓
Name Resolver
    ↓
Type Checker
    ↓
Ownership Checker
    ↓
MIR
    ↓
MIR Verification
    ↓
Minimal Optimization
    ↓
ABI Lowering
    ↓
x86-64 LIR/Machine IR
    ↓
Register Allocation
    ↓
Machine Encoder
    ↓
ELF Object Writer
    ↓
Axiom Linker
    ↓
Native ELF executable
```

Và quan trọng:

> **Stage-0 không được đi đường tắt AST → x86.**

Ngay từ compiler đầu tiên phải có:

```text
Typed HIR
    ↓
MIR
    ↓
LIR
    ↓
Machine IR
```

Nếu bỏ qua MIR/LIR ở Stage-0 thì sau này rất dễ phải viết lại compiler.

---

# 2. Stage-0 được viết bằng gì?

Tạm thời có thể dùng:

```text
C
```

hoặc một ngôn ngữ bootstrap phù hợp.

Nhưng C chỉ là **host implementation**.

Kiến trúc không được phụ thuộc vào C.

```text
Stage-0
    ├── C implementation
    └── Axiom semantic model
```

Sau này:

```text
Stage-1
    └── Axiom implementation
```

Cần bảo đảm hai compiler có cùng semantic specification.

---

# 3. Stage-0 không cần full Axiom

Subset đầu tiên:

```text
fn
struct
enum
let
var
if
loop
while
return
match
arrays
tuples
modules
basic generics
Option
Result
ownership
view
mut_view
```

Chưa cần:

```text
async
GPU
dynamic linking
reflection runtime
advanced comptime
closures phức tạp
dyn Trait
advanced SIMD
```

Nhưng **MIR phải được thiết kế để sau này hỗ trợ chúng**.

---

# 4. Hello World đầu tiên

Không bắt đầu bằng:

```text
println("Hello");
```

Mà nên bắt đầu bằng chương trình freestanding:

```text
@entry
fn _start() -> never {
    sys::linux::exit(42);
}
```

Mục tiêu:

```text
axiom build hello.ax
./hello
echo $?
```

→

```text
42
```

Điều này chứng minh:

```text
lexer
parser
resolver
type checker
MIR
ABI
x86-64 backend
encoder
ELF writer
linker
entry point
```

đều hoạt động.

---

# 5. Sau đó mới Hello World thực sự

Ví dụ:

```text
fn main() {
    let x: i32 = 42;
    print_number(x);
}
```

và low-level output:

```text
fn print_number(x: i32) {
    ...
}
```

hoặc trước mắt dùng syscall trực tiếp.

Như vậy không bị mắc kẹt bởi stdlib quá sớm.

---

# 6. Bootstrap Milestones

Tôi đề xuất chia thành các mốc rất nhỏ.

### B0 — Empty executable

```text
@entry
fn _start() -> never
```

→ ELF hợp lệ.

### B1 — Integer constants

```text
let x: i32 = 42;
```

→ register/memory.

### B2 — Arithmetic

```text
let x = 10 + 20;
```

### B3 — Branch

```text
if x > 10 {
    ...
}
```

### B4 — Functions

```text
fn add(a: i32, b: i32) -> i32
```

### B5 — Struct

```text
struct Point {
    x: i32,
    y: i32,
}
```

### B6 — Move

```text
let a = make();
let b = a;
```

### B7 — View

```text
fn sum(x: view<i32>) -> i32
```

### B8 — Enum

```text
enum Option<T> {
    Some(T),
    None,
}
```

### B9 — Match

### B10 — Result / `?`

### B11 — Module

### B12 — Generic

### B13 — Trait

### B14 — Self compilation subset

Đây là ladder thực tế hơn việc cố implement toàn bộ compiler ngay từ đầu.

---

# 7. Compiler Architecture Stage-0

Repository:

```text
axiom/
├── bootstrap/
│   └── stage0/
│
├── compiler/
│   ├── lexer/
│   ├── parser/
│   ├── ast/
│   ├── resolver/
│   ├── types/
│   ├── traits/
│   ├── hir/
│   ├── ownership/
│   ├── mir/
│   ├── verifier/
│   ├── optimization/
│   ├── abi/
│   ├── lir/
│   ├── machine/
│   │   └── x86_64/
│   ├── object/
│   ├── linker/
│   └── driver/
│
├── core/
├── runtime/
├── std/
├── tests/
└── docs/
```

Stage-0 có thể implement dần từng module tương ứng.

---

# 8. Đừng viết AST quá lớn

AST chỉ phản ánh syntax.

Ví dụ:

```text
fn add(a: i32, b: i32) -> i32 {
    a + b
}
```

AST:

```text
FunctionDecl
 ├── name
 ├── parameters
 ├── return_type
 └── body
```

Nhưng không nên nhét vào AST:

```text
ownership
resolved symbols
layout
ABI
register
lifetime
```

Những thứ đó thuộc các phase sau.

---

# 9. HIR là semantic normalization

AST:

```text
v.length()
```

HIR:

```text
length(v)
```

AST:

```text
for x in xs {
    foo(x);
}
```

HIR có thể hạ thành iterator/control-flow representation.

AST:

```text
a?;
```

HIR:

```text
match a {
    Ok(v) => v,
    Err(e) => return Err(e),
}
```

Sau HIR:

> Syntax sugar gần như biến mất.

---

# 10. Typed HIR

Ví dụ:

```text
let x = 10;
```

sau type inference:

```text
x : i32
```

hoặc default integer type theo rule đã định nghĩa.

Typed HIR:

```text
Let {
    local = L1
    type = i32
    init = Const(10:i32)
}
```

Từ đây backend không còn phải suy luận type.

---

# 11. Ownership Checker

Stage-0 phải có ownership **ngay từ đầu**.

Không nên làm:

```text
Stage-0
    → no ownership

Stage-1
    → add ownership
```

vì MIR và language semantics sẽ bị xây sai nền móng.

State:

```text
Uninit
Owned
Moved
PartiallyMoved
Dropped
```

Ví dụ:

```text
let a = make();
let b = a;
use(a);
```

phải báo:

```text
AX1507 MoveAfterMove
```

ngay Stage-0.

---

# 12. Nhưng Stage-0 không cần full borrow analysis

Ban đầu chỉ cần:

```text
Move
Copy
Drop
view
mut_view
```

và các rule cơ bản.

Chưa cần tối ưu alias analysis sâu.

Ví dụ:

```text
fn foo(x: view<i32>)
```

compiler biết:

```text
x = READ capability
```

Nhưng implementation ban đầu có thể chưa thực hiện toàn bộ region solver phức tạp.

---

# 13. MIR Stage-0

Ví dụ:

```text
fn add(a: i32, b: i32) -> i32 {
    a + b
}
```

MIR:

```text
bb0:
    v0 = LOAD a
    v1 = LOAD b
    v2 = ADD v0, v1
    RETURN v2
```

Không:

```text
eax = ...
```

vì register allocation chưa xảy ra.

---

# 14. MIR Place

Struct:

```text
struct Point {
    x: i32,
    y: i32,
}
```

và:

```text
p.x = 10;
```

MIR:

```text
STORE 10 → p.field(x)
```

không phải:

```text
STORE 10 → [rbp-8]
```

Đó là việc của backend.

---

# 15. Drop Elaboration

Ví dụ:

```text
fn foo() {
    let x = acquire();
    return;
}
```

MIR semantic:

```text
x = acquire()
...
RETURN
```

Sau Drop elaboration:

```text
x = acquire()
...
DROP x
RETURN
```

Nếu có:

```text
if condition {
    return;
}
```

cleanup graph đảm bảo:

```text
condition true
    ↓
DROP required resources
    ↓
RETURN
```

---

# 16. `?`

Ví dụ:

```text
fn foo() -> Result<i32, E> {
    let x = bar()?;
    Ok(x + 1)
}
```

MIR:

```text
r = CALL bar()

SWITCH r:
    Ok(v) → bb_ok
    Err(e) → bb_err

bb_ok:
    x = MOVE v
    ...
    RETURN Ok(result)

bb_err:
    cleanup
    RETURN Err(e)
```

Không cần exception runtime.

---

# 17. MIR Verifier

Stage-0 phải có verifier dù rất nhỏ.

Ít nhất:

```text
CFG valid
types valid
SSA dominance valid
MOVE valid
COPY valid
DROP valid
places valid
RETURN type valid
```

Ví dụ compiler bug tạo:

```text
MOVE x
MOVE x
```

MIR verifier phải bắt được.

Đây là lớp bảo vệ rất quan trọng trong quá trình AI agent phát triển compiler.

---

# 18. MIR Interpreter

Tôi vẫn giữ đề xuất trước đó:

> **MIR interpreter nên được xây rất sớm.**

Không cần tối ưu.

Ví dụ:

```text
Axiom source
     ↓
MIR
     ↓
MIR Interpreter
```

Nếu:

```text
10 + 20
```

trả:

```text
30
```

thì có reference semantic execution.

Sau đó:

```text
MIR
 ├── Interpreter → 30
 └── Native → 30
```

Nếu khác:

```text
compiler bug
```

---

# 19. Đây là vũ khí test cực mạnh

Ví dụ test:

```text
fn test() -> i32 {
    let x = 10;
    let y = 20;
    x + y
}
```

Expected:

```text
30
```

Chạy:

```text
-O0
-O1
-O2
-O3
```

và MIR interpreter.

Tất cả phải:

```text
30
```

---

# 20. Stage-0 x86-64 Backend

Chỉ cần subset instruction ban đầu:

```text
MOV
LEA
ADD
SUB
IMUL
CMP
TEST
JMP
Jcc
CALL
RET
PUSH
POP
SYSCALL
```

Sau đó mở rộng.

Không cần ngay:

```text
AVX-512
AMX
complex SIMD
```

---

# 21. Register Allocator MVP

Dùng:

```text
Linear Scan
```

ban đầu.

Vì mục tiêu:

```text
đơn giản
đúng
dễ debug
```

Không cần ngay Graph Coloring/Greedy allocator.

Sau khi compiler chạy ổn:

```text
Linear Scan
      ↓
Greedy
      ↓
advanced allocator
```

---

# 22. Machine Encoder

Chỉ cần:

```text
x86-64 integer subset
```

đầu tiên.

Ví dụ:

```text
MOV rax, 42
```

→ machine bytes.

Encoder không biết:

```text
ownership
struct
Option
trait
```

những thứ đó đã biến mất từ MIR/LIR.

---

# 23. ELF Object Writer

Ban đầu chỉ cần:

```text
.text
.rodata
.data
.bss
.symtab
.strtab
.shstrtab
.rela.text
```

Không cần ngay:

```text
DWARF
TLS
dynamic linking
COMDAT
complex debug
```

nhưng Object IR phải hỗ trợ kiến trúc tương lai.

---

# 24. Linker MVP

Ban đầu:

```text
one or more ELF objects
       ↓
symbol resolution
       ↓
section merge
       ↓
relocation
       ↓
segment layout
       ↓
ELF executable
```

Chưa cần:

```text
shared libraries
GOT/PLT
versioned symbols
advanced ICF
```

---

# 25. Stage-0 Output

Milestone cực kỳ quan trọng:

```text
$ axiom0 hello.ax
```

tạo:

```text
hello
```

sau đó:

```text
$ file hello
ELF 64-bit executable
```

và:

```text
$ ./hello
```

chạy native.

Không LLVM.

Không assembler.

Không linker ngoài.

---

# 26. Differential Testing

Trong bootstrap, vẫn nên dùng LLVM/system toolchain làm **oracle**, nhưng chỉ để test.

Ví dụ:

```text
Axiom MIR
   ├── Axiom backend → result A
   │
   └── LLVM reference → result B
```

Nếu:

```text
A != B
```

→ investigate.

Nhưng:

> LLVM không nằm trong production dependency graph của Axiom.

---

# 27. Golden Tests

Mỗi compiler phase nên có snapshot.

Ví dụ:

```text
tests/
├── lexer/
├── parser/
├── resolver/
├── types/
├── ownership/
├── mir/
├── lir/
├── machine/
├── object/
└── linker/
```

Test:

```text
foo.ax
foo.ast.json
foo.hir.json
foo.mir
foo.lir
foo.machine
foo.o
```

Không nhất thiết commit mọi artifact lâu dài, nhưng golden representation rất hữu ích trong giai đoạn compiler còn thay đổi mạnh.

---

# 28. Compiler Self-Test

Compiler binary phải có:

```bash
axiom test compiler
```

chạy:

```text
lexer tests
parser tests
type tests
ownership tests
MIR verifier tests
codegen tests
object tests
linker tests
end-to-end tests
```

---

# 29. Fuzzing ngay từ Stage-0

Ba fuzz target cực quan trọng:

```text
random source
    ↓
lexer
```

```text
random valid-ish syntax
    ↓
parser
```

và đặc biệt:

```text
random MIR
    ↓
MIR verifier
```

MIR verifier fuzzing rất quan trọng vì compiler backend có thể tin vào verifier.

---

# 30. Compiler Security Boundary

Compiler input là untrusted.

Do đó:

```text
malformed source
malformed object
malformed MIR
malformed archive
```

không được:

```text
segfault
memory corruption
infinite loop
```

thay vào đó:

```text
diagnostic
```

hoặc compiler-internal error có kiểm soát.

---

# 31. Stage-0 không cần self-hosted

Một sai lầm cần tránh:

> cố viết Stage-0 quá mạnh để "sẵn sàng self-host".

Stage-0 chỉ cần:

```text
đúng semantic core
đường codegen hoàn chỉnh
đủ ngôn ngữ để viết Stage-1
```

Ví dụ nếu Stage-1 compiler cần:

```text
generic
struct
enum
match
modules
collections
```

thì Stage-0 phải hỗ trợ chúng.

Không cần:

```text
async
GPU
advanced reflection
```

để viết compiler.

---

# 32. Tiêu chí Stage-0 hoàn thành

Tôi đề xuất không gọi Stage-0 hoàn thành cho tới khi đạt:

```text
BOOT-20  Can compile functions
BOOT-21  Can compile structs
BOOT-22  Can compile enums
BOOT-23  Can compile match
BOOT-24  Can compile modules
BOOT-25  Can compile generics
BOOT-26  Enforces ownership
BOOT-27  Enforces view/mut_view
BOOT-28  Generates verified MIR
BOOT-29  MIR interpreter agrees with native execution
BOOT-30  Generates x86-64 machine code
BOOT-31  Generates ELF objects
BOOT-32  Links ELF natively
BOOT-33  Does not require external assembler
BOOT-34  Does not require external linker
BOOT-35  Can build freestanding executable
BOOT-36  Has deterministic diagnostics
BOOT-37  Has reproducible builds
BOOT-38  Has compiler self-tests
BOOT-39  Has fuzz tests
BOOT-40  Can compile the Stage-1 compiler subset
```

---

# 33. Quan trọng nhất: Stage-1 phải được thiết kế ngay bây giờ

Stage-0 chưa cần self-host.

Nhưng **test cuối của Stage-0 phải là**:

```text
Can Stage-0 compile a useful Axiom compiler written in Axiom?
```

Ví dụ:

```text
bootstrap/
├── stage0/
│
└── stage1/
    └── compiler.ax
```

Stage-0:

```text
stage0 compiler
      ↓
compiler.ax
      ↓
stage1 compiler executable
```

Sau đó:

```text
stage1 compiler
      ↓
compiler.ax
      ↓
stage2 compiler executable
```

---

# 34. BOOTSTRAP-002 sẽ là self-host kernel

Stage-1 ban đầu không phải toàn bộ compiler.

Nó có thể bắt đầu:

```text
compiler/
├── lexer.ax
├── parser.ax
├── types.ax
├── mir.ax
├── x86_64.ax
└── main.ax
```

và dùng:

```text
Axiom Core
```

Sau đó dần chuyển:

```text
resolver
ownership
traits
optimizer
linker
```

sang Axiom.

---

# 35. Điều kiện "compiler tự biên dịch chính nó"

Không nên chỉ kiểm tra:

```text
stage1 → stage1 source
```

Mà phải kiểm tra **compiler equivalence**:

```text
C0 = Stage-0 compiler
C1 = compiler được C0 build

C1(source_compiler)
       ↓
C2
```

Sau đó:

```text
C1 == C2
```

ở mức:

```text
functional behavior
```

và cuối cùng có thể thêm:

```text
reproducible binary
```

nếu bootstrap deterministic.

---

# 36. Reproducible Self-Hosting

Mục tiêu mạnh:

```text
Stage-0
   ↓
C1

C1
   ↓
C2

C1 source + same compiler
   ↓
same C2 binary
```

Sau này có thể tiến đến:

```text
C2 builds C3
C3 builds C4
...
```

và binary ổn định.

Đây là nền tảng để chứng minh compiler không có dependency ẩn vào toolchain cũ.

---

# 37. Một thay đổi tôi khuyên bổ sung vào kiến trúc hiện tại

Từ thời điểm này nên chính thức thêm:

```text
compiler/reference/
```

với:

```text
reference/
├── semantics/
├── mir-interpreter/
├── test-oracles/
└── differential/
```

Nó đóng vai trò **semantic reference implementation**.

Pipeline:

```text
Axiom Source
    ↓
Typed HIR
    ↓
MIR
    ├───────────────┐
    ↓               ↓
MIR Interpreter   Native Backend
    ↓               ↓
 Result A         Result B
    └───────┬───────┘
            ↓
         Compare
```

Đây sẽ là một trong những tài sản quan trọng nhất của Axiom compiler.

---

# 38. Kiến trúc bootstrap hoàn chỉnh

Đến đây roadmap trở thành:

```text
                    Axiom Specification
                            │
                            ↓
                    Semantic Reference
                            │
             ┌──────────────┴──────────────┐
             │                             │
        Stage-0 Compiler              MIR Interpreter
             │                             │
             ↓                             │
        Axiom Compiler                     │
             │                             │
             ├──────────────→ MIR ─────────┘
             │
             ↓
       Axiom Native Backend
             │
             ↓
       Axiom Object Writer
             │
             ↓
        Axiom Linker
             │
             ↓
       Native Executable
```

Sau đó:

```text
Stage-0
   ↓
Stage-1 compiler written in Axiom
   ↓
Stage-1 compiles itself
   ↓
Self-hosted Axiom
```

---

## Bước tiếp theo

Sau **BOOTSTRAP-001**, bước tiếp theo nên là **BOOTSTRAP-002 — Minimal Self-Hosting Subset**.

Phần đó sẽ xác định chính xác:

- Axiom subset nào đủ để viết compiler;
- compiler cần `Vec`, `String`, `HashMap` đến mức nào;
- compiler có cần GC/RC không — câu trả lời dự kiến là **không**;
- cách compiler tự quản lý AST/HIR/MIR;
- cách dùng ownership của chính Axiom để viết compiler mà không biến code compiler thành một mớ `view`/`mut_view`;
- module architecture của compiler viết bằng Axiom;
- cách Stage-0 compile Stage-1;
- và cuối cùng **self-build ladder C0 → C1 → C2 → C3**.