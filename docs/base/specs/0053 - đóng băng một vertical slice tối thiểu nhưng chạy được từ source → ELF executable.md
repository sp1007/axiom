Tiếp tục từ **Genesis Compiler Slice**. Bước tiếp theo nên là **đóng băng một vertical slice tối thiểu nhưng chạy được từ source → ELF executable**, thay vì mở rộng thêm tính năng ngôn ngữ.

## 1. Genesis Slice v0.1

Mục tiêu đầu tiên:

```text
Axiom source
    ↓
Lexer
    ↓
Parser
    ↓
AST
    ↓
HIR
    ↓
Typed HIR
    ↓
MIR
    ↓
Verifier
    ↓
Verified MIR
    ↓
LIR
    ↓
x86-64 Machine IR
    ↓
Register Allocation
    ↓
x86-64 Encoder
    ↓
ELF Object
    ↓
System Linker
    ↓
Native executable
```

Và chương trình đầu tiên phải thực sự chạy:

```axiom
fn add(a: i64, b: i64) -> i64 {
    a + b
}

fn main() -> i64 {
    add(20, 22)
}
```

Kết quả process exit code:

```text
42
```

Đây là **Genesis milestone G0**.

---

# 2. Không cần triển khai toàn bộ Axiom để đạt G0

Genesis chỉ cần:

### Types

```text
i64
bool
```

### Expressions

```text
integer literal
variable
binary +
binary -
binary *
binary /
comparison == != < <= > >=
function call
```

### Statements

```text
let
var
assignment
return
expression statement
if
while
```

### Functions

```text
fn name(
    parameter: type,
    ...
) -> type {
    ...
}
```

Chưa cần:

```text
struct
enum
trait
generic
closure
async
view
ownership
Drop
threads
FFI
String
Vec
```

**Nhưng kiến trúc compiler phải được thiết kế sao cho những thứ đó có thể cắm vào sau.**

Đây là điểm rất quan trọng.

---

# 3. Grammar Genesis

Không nên bắt đầu bằng grammar quá lớn.

Có thể đóng băng:

```ebnf
program        = { function } ;

function       = "fn" identifier
                 "(" [ parameters ] ")"
                 [ "->" type ]
                 block ;

parameters     = parameter { "," parameter } ;
parameter      = identifier ":" type ;

type           = "i64" | "bool" ;

block          = "{"
                   { statement }
                   [ expression ]
                 "}" ;

statement      = let_statement
               | var_statement
               | assignment
               | return_statement
               | if_statement
               | while_statement
               | expression_statement ;

let_statement  = "let" identifier "=" expression ";" ;

var_statement  = "var" identifier "=" expression ";" ;

assignment     = identifier "=" expression ";" ;

return_statement = "return" [ expression ] ";" ;

if_statement   = "if" expression block
                 [ "else" block ] ;

while_statement = "while" expression block ;

expression_statement = expression ";" ;

expression     = comparison ;

comparison     = additive
                 [ comparison_op additive ] ;

additive       = multiplicative
                 { ("+" | "-") multiplicative } ;

multiplicative = unary
                 { ("*" | "/") unary } ;

unary          = [ "-" | "!" ] primary ;

primary        = integer
               | "true"
               | "false"
               | identifier
               | call
               | "(" expression ")" ;

call            = identifier "(" [ arguments ] ")" ;
arguments       = expression { "," expression } ;

comparison_op   = "==" | "!=" | "<" | "<="
               | ">" | ">=" ;

integer         = digit { digit } ;

identifier      = letter { letter | digit | "_" } ;
```

Nhưng parser nội bộ **không nên giữ precedence bằng cách phụ thuộc vào grammar này**. Pratt parser hoặc precedence climbing sẽ giúp mở rộng operator sau này dễ hơn.

---

# 4. AST không được trở thành IR

Đây là một quyết định kiến trúc quan trọng.

AST chỉ phản ánh source.

Ví dụ:

```axiom
a + b * 2
```

AST:

```text
Binary(+)
├── Variable(a)
└── Binary(*)
    ├── Variable(b)
    └── Int(2)
```

AST không cần biết:

```text
i64
SSA
register
stack
ownership
ABI
```

Sau đó HIR mới bổ sung semantic information.

---

# 5. HIR

HIR nên gần source hơn MIR nhưng đã giải quyết tên.

Ví dụ:

```axiom
fn add(a: i64, b: i64) -> i64 {
    a + b
}
```

HIR:

```text
Function {
    id: add
    params:
        LocalId(0) : i64
        LocalId(1) : i64

    return_type: i64

    body:
        Add(
            Local(0),
            Local(1)
        )
}
```

Tên `a`, `b` lúc này có thể đã được resolve thành:

```text
LocalId(0)
LocalId(1)
```

Điều này giúp compiler về sau không phụ thuộc string lookup trong các phase thấp hơn.

---

# 6. Typed HIR

Typed HIR phải đảm bảo invariant cực quan trọng:

> **Mỗi expression có đúng một static type.**

Ví dụ:

```axiom
a + b
```

sau type checking:

```text
Add
├── operand: i64
├── operand: i64
└── result:  i64
```

Nếu:

```axiom
a: i64
b: bool

a + b
```

compiler phải reject ở đây.

Không để lỗi đó lọt xuống MIR.

---

# 7. MIR Genesis

MIR là nơi Axiom bắt đầu trở thành một systems language thực sự.

Ví dụ:

```axiom
fn add(a: i64, b: i64) -> i64 {
    a + b
}
```

Có thể hạ thành:

```text
bb0:
    %0 = arg 0
    %1 = arg 1
    %2 = add.checked %0, %1
    return %2
```

MIR:

```text
Function add
params:
    %0 : i64
    %1 : i64

bb0:
    %2 = ADD_CHECKED %0, %1
    RETURN %2
```

Không có:

```text
RAX
RDI
RSI
```

vì đó là việc của ABI/backend.

---

# 8. Một quyết định rất quan trọng: MIR không dùng UB cho integer overflow

Ví dụ:

```axiom
let x: i64 = MAX_I64;
let y = x + 1;
```

Genesis nên quy định:

```text
ADD_CHECKED
```

và nếu overflow:

```text
PANIC / TRAP
```

Sau này có thể có:

```text
ADD_WRAP
ADD_SAT
ADD_CHECKED
```

Ví dụ:

```axiom
x.wrapping_add(y)
x.saturating_add(y)
```

hoặc API tương đương.

Như vậy optimizer không bao giờ được phép giả định:

> "signed overflow không xảy ra vì nó là UB"

Đây là khác biệt quan trọng với C/C++.

---

# 9. LIR Genesis

LIR bắt đầu loại bỏ semantic information cấp cao.

Ví dụ MIR:

```text
%2 = ADD_CHECKED %0, %1
RETURN %2
```

Có thể trở thành:

```text
%2 = ADD %0, %1
RETURN %2
```

Nhưng checked overflow phải được xử lý trước đó:

```text
%2, %ov = ADD_WITH_OVERFLOW %0, %1

BR %ov, overflow, continue

overflow:
    TRAP

continue:
    RETURN %2
```

Hoặc optimizer có thể biến nó thành sequence phù hợp với target.

---

# 10. LIR không biết RAX/RDI

LIR:

```text
v0 : i64
v1 : i64
v2 : i64

v2 = ADD v0, v1
RETURN v2
```

ABI lowering mới nói:

```text
arg0 → RDI
arg1 → RSI
return → RAX
```

Vì vậy:

```text
LIR
```

có thể dùng lại cho:

```text
x86-64
ARM64
RISC-V
WASM
```

mà không sửa frontend.

Đây chính là **Target Replacement Invariant**.

---

# 11. ABI MIR

Đây là lớp rất đáng giữ trong Axiom.

Ví dụ:

```text
fn add(i64, i64) -> i64
```

ABI MIR:

```text
arg0 = ABI_INT_REG 0
arg1 = ABI_INT_REG 1

call convention = SysV_AMD64

return = ABI_INT_RETURN
```

Target backend sau đó map:

```text
ABI_INT_REG 0 → RDI
ABI_INT_REG 1 → RSI
ABI_INT_RETURN → RAX
```

Sau này Windows:

```text
ABI_INT_REG 0 → RCX
ABI_INT_REG 1 → RDX
ABI_INT_RETURN → RAX
```

Frontend vẫn hoàn toàn giống nhau.

---

# 12. Machine IR cho `add`

Sau instruction selection:

```text
MachineFunction add

bb0:
    COPY v0, RDI
    COPY v1, RSI

    ADD v0, v1

    COPY RAX, v0
    RET
```

Register allocator có thể coalesce:

```text
RDI = RDI + RSI
RAX = RDI
RET
```

Hoặc trực tiếp chọn:

```asm
add rdi, rsi
mov rax, rdi
ret
```

Nếu phép cộng không cần giữ `a`, thậm chí backend có thể tận dụng:

```text
RAX = RDI + RSI
```

tùy instruction-selection + ABI constraints.

Điểm quan trọng:

**MIR không cần biết điều này.**

---

# 13. Đừng tạo assembly text trung gian

Axiom cuối cùng nên đi:

```text
Machine IR
    ↓
x86 Encoder
    ↓
bytes
```

Không:

```text
Machine IR
 ↓
"mov rax, rdi"
 ↓
assembler
 ↓
object
```

Trong bootstrap có thể dùng assembler/LLVM để tăng tốc phát triển.

Nhưng kiến trúc cuối cùng:

```text
Axiom compiler
    ↓
Machine Encoder
    ↓
ELF/PE/Mach-O
```

Không phụ thuộc compiler C.

---

# 14. ELF Genesis

Không cần viết linker ngay.

Genesis có thể:

```text
Axiom compiler
      ↓
ELF relocatable object
      ↓
system linker
      ↓
executable
```

Ví dụ:

```text
add.o
```

có:

```text
.text
.symtab
.strtab
.shstrtab
.rela.text
```

Sau đó:

```text
ld add.o ...
```

hoặc platform linker tương ứng.

**System linker là bootstrap dependency, không phải semantic dependency.**

---

# 15. Test đầu tiên phải là machine bytes

Không chỉ test source.

Ví dụ:

```text
MOV RAX, RDI
```

phải có golden encoding.

Tương tự:

```text
ADD RAX, RSI
RET
```

Encoder test:

```text
input:
    MOV RAX, RDI
    ADD RAX, RSI
    RET

expected bytes:
    ...
```

Đây là test cực thấp nhưng cực kỳ quan trọng.

Nếu encoder sai:

```text
compiler output ≠ CPU semantics
```

---

# 16. Test tầng ABI

Ví dụ:

```axiom
fn add(a: i64, b: i64) -> i64 {
    a + b
}
```

ABI test phải kiểm tra:

```text
a → RDI
b → RSI
result → RAX
```

Sau đó:

```axiom
fn f() -> i64 {
    add(10, 32)
}
```

phải tạo call:

```text
RDI = 10
RSI = 32
CALL add
result = RAX
```

---

# 17. Test vòng lặp

Genesis không nên chỉ test arithmetic.

Cần ngay:

```axiom
fn sum(n: i64) -> i64 {
    var i = 0;
    var result = 0;

    while i < n {
        result = result + i;
        i = i + 1;
    }

    result
}
```

MIR:

```text
bb0:
    i = 0
    result = 0
    jump bb1

bb1:
    cond = LT i, n
    branch cond, bb2, bb3

bb2:
    result = ADD result, i
    i = ADD i, 1
    jump bb1

bb3:
    return result
```

Đây là test cực kỳ giá trị vì nó đồng thời kiểm tra:

```text
CFG
SSA
PHI
branch
loop
comparison
arithmetic
register allocation
```

---

# 18. Phi phải xuất hiện trong MIR/LIR

Nếu MIR theo SSA:

```text
bb0:
    jump bb1

bb1:
    %i = PHI(%i0, %i1)
    %r = PHI(%r0, %r1)

    ...
```

Sau đó:

```text
PHI elimination
```

sẽ biến thành COPY trên predecessor.

Đây là nơi compiler bắt đầu cần:

```text
liveness
copy coalescing
critical-edge handling
```

Không nên né SSA chỉ vì muốn compiler đơn giản.

**SSA làm compiler phức tạp hơn một chút nhưng làm optimization và backend dễ hơn đáng kể.**

---

# 19. Genesis acceptance criteria

G0 chỉ được coi là hoàn thành khi compiler chạy được tối thiểu:

### G0-01

```axiom
fn main() -> i64 {
    42
}
```

→ exit `42`.

### G0-02

```axiom
fn main() -> i64 {
    20 + 22
}
```

→ `42`.

### G0-03

```axiom
fn add(a: i64, b: i64) -> i64 {
    a + b
}

fn main() -> i64 {
    add(20, 22)
}
```

→ `42`.

### G0-04

```axiom
fn main() -> i64 {
    if 10 > 5 {
        42
    } else {
        0
    }
}
```

→ `42`.

### G0-05

```axiom
fn main() -> i64 {
    var x = 0;

    while x < 42 {
        x = x + 1;
    }

    x
}
```

→ `42`.

### G0-06

Nested calls:

```axiom
fn square(x: i64) -> i64 {
    x * x
}

fn main() -> i64 {
    square(6) + square(1)
}
```

→ `37`.

---

# 20. Và một test cực quan trọng: Semantic Oracle

Mỗi chương trình test phải có hai đường chạy:

```text
                 ┌── Semantic Oracle
Source → MIR ────┤
                 └── Native Backend
```

Ví dụ random:

```text
a = -193
b = 827
```

Oracle:

```text
634
```

Native executable:

```text
634
```

→ pass.

Nếu:

```text
Oracle = 634
Native = 635
```

thì **backend bị coi là sai**, không được sửa semantics để khớp backend.

Đây sẽ trở thành một trong những vũ khí mạnh nhất của Axiom trong quá trình phát triển.

---

# 21. Project structure nên bắt đầu như thế này

```text
axiom/
├── compiler/
│   ├── lexer/
│   ├── parser/
│   ├── ast/
│   ├── resolver/
│   ├── hir/
│   ├── typeck/
│   ├── mir/
│   ├── verifier/
│   ├── interpreter/
│   ├── optimizer/
│   ├── abi/
│   ├── lir/
│   ├── backend/
│   │   └── x86_64/
│   │       ├── target
│   │       ├── machine_ir
│   │       ├── isel
│   │       ├── regalloc
│   │       ├── encoder
│   │       └── elf
│   └── driver/
│
├── tests/
│   ├── lexer/
│   ├── parser/
│   ├── typeck/
│   ├── verifier/
│   ├── interpreter/
│   ├── lir/
│   ├── x86_64/
│   ├── abi/
│   └── differential/
│
├── std/
├── runtime/
├── tools/
└── docs/
```

Điểm đáng chú ý là **interpreter nằm cạnh compiler**, không phải một runtime bắt buộc của executable.

---

# 22. Sau G0 mới bắt đầu đưa “Axiom đặc trưng” vào

Thứ tự tôi đề xuất:

```text
G0  Arithmetic + functions + native executable
 ↓
G1  CFG + loops + SSA + calls
 ↓
G2  structs + fields
 ↓
G3  value semantics + Move/Copy
 ↓
G4  Drop + deterministic cleanup
 ↓
G5  view/mut_view + region verification
 ↓
G6  arrays + Vec
 ↓
G7  traits + generics
 ↓
G8  closures
 ↓
G9  Result/Option + error flow
 ↓
G10 concurrency
 ↓
G11 async
 ↓
G12 FFI
 ↓
G13 ARM64
 ↓
G14 Windows PE
 ↓
G15 macOS Mach-O
 ↓
G16 self-hosting
```

Đây là thứ tự có ý nghĩa hơn việc cố xây toàn bộ language spec rồi mới compiler.

**Đặc biệt G3–G5 sẽ là nơi chứng minh Axiom thực sự khác C/C++ và Rust:** programmer không phải quản lý `malloc/free`, không phải viết lifetime annotation, không phải viết borrow annotation, nhưng compiler vẫn chứng minh được ownership/lifetime/alias safety.

Và có một nguyên tắc tôi nghĩ nên đóng băng ngay từ Genesis:

> **Nếu một semantic feature có thể bị xóa hoàn toàn trước Machine IR mà không thay đổi observable behavior, compiler phải được phép xóa nó.**

Đó chính là nền tảng cho mục tiêu **“ngôn ngữ cấp cao nhưng binary gần như không mang theo gánh nặng của ngôn ngữ cấp cao.”**