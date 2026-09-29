Tiếp tục từ **Axiom Genesis Trace v0.1**. Đây là bước rất quan trọng: thay vì tiếp tục thêm tính năng, ta chứng minh rằng **một chương trình Axiom cực nhỏ có thể đi xuyên toàn bộ compiler và tạo ra binary native**.

# Axiom Genesis Trace v0.1

Chương trình:

```axiom
fn add(a: i64, b: i64) -> i64 {
    a + b
}

fn main() -> i64 {
    add(20, 22)
}
```

Mục tiêu cuối:

```text
Source
 → Lexer
 → AST
 → HIR
 → Typed HIR
 → MIR
 → Verified MIR
 → LIR
 → ABI MIR
 → x86-64 Machine IR
 → Register Allocation
 → Machine Code
 → ELF
 → executable
 → exit code = 42
```

---

# 1. Lexer

Token stream không cần giữ whitespace/comment:

```text
FN
IDENT(add)
LPAREN
IDENT(a)
COLON
IDENT(i64)
COMMA
IDENT(b)
COLON
IDENT(i64)
RPAREN
ARROW
IDENT(i64)
LBRACE

IDENT(a)
PLUS
IDENT(b)

RBRACE

FN
IDENT(main)
LPAREN
RPAREN
ARROW
IDENT(i64)
LBRACE

IDENT(add)
LPAREN
INT(20)
COMMA
INT(22)
RPAREN

RBRACE
EOF
```

Mỗi token có:

```text
Token {
    kind
    span
}
```

Ví dụ:

```text
IDENT("add")
span = file0:3..6
```

**Invariant:**

> Lexer không được hiểu ownership, type, ABI hay CPU.

---

# 2. AST

AST chỉ mô tả cú pháp.

Ví dụ rút gọn:

```text
Program
├── Function add
│   ├── Param a : i64
│   ├── Param b : i64
│   └── Body
│       └── Binary(+)
│           ├── Name(a)
│           └── Name(b)
│
└── Function main
    └── Body
        └── Call
            ├── Name(add)
            ├── Int(20)
            └── Int(22)
```

Không nên để AST chứa:

```text
RAX
stack offset
ownership state
LLVM-like type
calling convention
```

---

# 3. Name Resolution → HIR

AST:

```text
Name("a")
Name("b")
```

được resolve thành symbol/local ID:

```text
LocalId(0) = a
LocalId(1) = b
```

`add` được resolve:

```text
FunctionId(0) = add
FunctionId(1) = main
```

HIR có thể trở thành:

```text
Function #0 add
params:
    Local(0) a
    Local(1) b

body:
    BinaryAdd(
        Local(0),
        Local(1)
    )
```

và:

```text
Function #1 main

body:
    Call(
        Function(0),
        [20, 22]
    )
```

Điểm quan trọng:

**HIR đã biết `add` là function nào, nhưng vẫn chưa cần biết RDI/RSI.**

---

# 4. Type Checking

Type environment:

```text
a : i64
b : i64

add : (i64, i64) -> i64
main : () -> i64
```

Biểu thức:

```text
a + b
```

được kiểm tra:

```text
a : i64
b : i64

operator + : i64 × i64 → i64

result : i64
```

Call:

```text
add(20, 22)
```

kiểm tra:

```text
20 : i64
22 : i64

add : (i64, i64) -> i64

result : i64
```

Không có conversion ngầm nguy hiểm.

---

# 5. Typed HIR

Bây giờ mỗi expression đã có type:

```text
Function add

BinaryAdd : i64
├── Local a : i64
└── Local b : i64
```

`main`:

```text
Call add : i64
├── 20 : i64
└── 22 : i64
```

Đây là điểm mà compiler có thể khẳng định:

```text
Program is statically well-typed.
```

---

# 6. MIR của `add`

MIR không còn là expression tree.

Nó chuyển thành explicit data flow:

```text
function @add(%a: i64, %b: i64) -> i64 {

bb0:
    %v0 = copy %a
    %v1 = copy %b
    %v2 = add.checked %v0, %v1
    return %v2
}
```

Nhưng có thể tối ưu ngay:

```text
bb0:
    %v0 = add.checked %a, %b
    return %v0
```

Ownership:

```text
%a : OWNED
%b : OWNED
```

Nhưng `i64` là `Copy`.

Do đó:

```text
copy(%a)
```

không làm `%a` thành `MOVED`.

---

# 7. MIR của `main`

```text
function @main() -> i64 {

bb0:
    %v0 = const 20 : i64
    %v1 = const 22 : i64

    %v2 = call @add(%v0, %v1)

    return %v2
}
```

Ở đây `20` và `22` không có vấn đề ownership.

---

# 8. Verified MIR

Verifier chạy:

```text
MIR
 ↓
Ownership Analysis
 ↓
Capability Analysis
 ↓
Region Analysis
 ↓
Effect Analysis
 ↓
Concurrency Analysis
 ↓
Drop Analysis
 ↓
VERIFIED
```

Trong chương trình này kết quả rất đơn giản:

```text
Function add:

%a
  initialized = yes
  ownership = OWNED
  Copy = yes

%b
  initialized = yes
  ownership = OWNED
  Copy = yes

add.checked
  inputs initialized = yes
  output initialized = yes

return
  valid = yes
```

`main` cũng tương tự.

Không có:

```text
VIEW
MUT_VIEW
MOVE
DROP
ALLOC
SPAWN
SUSPEND
```

nên phần lớn verifier không phải làm gì.

Đây chính là một ưu điểm của thiết kế:

> Compiler có verifier mạnh, nhưng chương trình đơn giản không phải trả runtime cost cho verifier.

---

# 9. Semantic Oracle

Semantic Oracle chạy MIR:

```text
20
+
22
=
42
```

Kết quả:

```text
Return(i64(42))
```

Đây là **ground truth**.

Native backend sau này bắt buộc phải cho kết quả tương đương.

---

# 10. MIR → LIR

Ownership đã được kiểm chứng.

Không còn cần:

```text
Copy
Move
Send
Share
Capability
Region
```

vì chúng không có runtime effect.

LIR:

```text
function @add(%a: i64, %b: i64) -> i64 {

bb0:
    %v0 = ADD_CHECKED %a, %b
    RETURN %v0
}
```

`main`:

```text
function @main() -> i64 {

bb0:
    %v0 = CONST 20
    %v1 = CONST 22
    %v2 = CALL @add(%v0, %v1)
    RETURN %v2
}
```

---

# 11. Checked arithmetic

Đây là điểm thú vị.

Axiom không được biến:

```text
ADD_CHECKED
```

thành:

```text
ADD
```

một cách tùy tiện.

Trên x86-64, selector có thể biến:

```text
ADD_CHECKED rax, rdi
```

thành:

```text
add rax, rdi
jo  overflow_handler
```

Nhưng với chương trình:

```text
20 + 22
```

compiler có thể chứng minh:

```text
20 + 22 ∈ [i64::MIN, i64::MAX]
```

và loại bỏ overflow check.

Khi đó:

```text
ADD_CHECKED
```

có thể hạ xuống:

```text
ADD
```

mà vẫn đúng semantics.

Đây chính là:

> **Semantic optimization trước machine optimization.**

---

# 12. ABI MIR

Bây giờ mới áp dụng ABI.

Target:

```text
x86_64-linux
SysV AMD64
```

Function:

```text
add(i64, i64) -> i64
```

được ABI classify thành:

```text
arg0 → IntArg(0)
arg1 → IntArg(1)

return → IntReturn
```

Sau đó backend target-specific mới map:

```text
IntArg(0) → RDI
IntArg(1) → RSI
IntReturn → RAX
```

Frontend hoàn toàn không biết RDI/RSI.

---

# 13. Machine IR của `add`

Một khả năng:

```text
machine_function @add

bb0:
    %v0:GPR64 = COPY RDI
    %v1:GPR64 = COPY RSI

    %v2:GPR64 = ADD %v0, %v1

    RAX = COPY %v2
    RET
```

Sau copy coalescing, có thể đơn giản hóa thành:

```text
bb0:
    %v0:GPR64 = COPY RDI
    ADD %v0, RSI
    RAX = COPY %v0
    RET
```

Sau allocation/coalescing tốt hơn nữa:

```text
bb0:
    RAX = COPY RDI
    ADD RAX, RSI
    RET
```

Thậm chí selector có thể trực tiếp sinh:

```text
MOV RAX, RDI
ADD RAX, RSI
RET
```

---

# 14. `main`

`main`:

```text
bb0:
    RDI = 20
    RSI = 22
    CALL @add
    RET
```

Nhưng ở đây có một vấn đề quan trọng.

Nếu:

```text
main() -> i64
```

được gọi bởi OS startup, thì `RAX` không nhất thiết tự động trở thành **process exit code** theo nghĩa ABI của OS.

Do đó cần phân biệt:

```text
Axiom function return
```

và:

```text
process exit status
```

Startup adapter phải làm:

```text
call main
result RAX
→ OS exit(result)
```

Ví dụ:

```text
_process_start:
    CALL main
    MOV RDI, RAX
    MOV RAX, SYS_EXIT
    SYSCALL
```

Đây là **runtime/startup glue**, không phải semantics của function.

---

# 15. Một điểm kiến trúc rất quan trọng

Ta không nên hard-code:

```text
fn main() -> i64
```

thành:

```text
Linux syscall
```

trong frontend.

Thay vào đó:

```text
Axiom main
      ↓
Target Startup Adapter
      ↓
OS ABI
```

Windows sẽ có startup khác.

macOS khác.

Android khác.

Freestanding khác.

Nhưng:

```text
MIR
LIR
type checker
ownership verifier
semantic oracle
```

không đổi.

---

# 16. Register Allocation

Với chương trình nhỏ, allocator có thể nhận:

```text
v0 : GPR64
v1 : GPR64
```

và map:

```text
v0 → RAX
v1 → RSI
```

hoặc các mapping tương đương.

Nếu argument đã ở:

```text
RDI
RSI
```

thì copy coalescing cố gắng tránh:

```text
RDI → temp
temp → RAX
```

mà giữ trực tiếp:

```text
RDI → RAX
```

---

# 17. Machine code

Ví dụ phần thân `add` có thể trở thành:

```asm
mov rax, rdi
add rax, rsi
ret
```

Một encoding hợp lệ:

```text
48 89 F8
48 01 F0
C3
```

Tức:

```text
48 89 F8    mov rax, rdi
48 01 F0    add rax, rsi
C3          ret
```

**Lưu ý:** đây là ví dụ encoding của một phương án cụ thể; compiler không nên coi assembly text là intermediate representation.

Encoder chỉ nhận Machine IR:

```text
MOV RAX, RDI
ADD RAX, RSI
RET
```

và tạo bytes.

---

# 18. `main` machine code

Ví dụ:

```asm
mov edi, 20
mov esi, 22
call add
ret
```

có thể encode thành dạng tương ứng:

```text
BF 14 00 00 00
BE 16 00 00 00
E8 xx xx xx xx
C3
```

`xx xx xx xx` chưa thể biết tại thời điểm encoder nếu `add` nằm ở vị trí khác.

Đây chính là lý do cần:

```text
Relocation
```

---

# 19. Object Writer

Compiler không nhất thiết tạo executable ngay.

Có thể tạo:

```text
main.o
```

với:

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

Symbol:

```text
add
main
```

Call:

```text
CALL add
```

được ghi relocation.

Ví dụ conceptual:

```text
.text:
    ...
    E8 00 00 00 00
```

và:

```text
.rela.text:
    offset = ...
    symbol = add
    type = PC-relative call
```

Linker sau đó thay relocation bằng displacement thật.

---

# 20. Tại sao Object Writer và Linker phải tách?

Đây là một quyết định rất đúng cho Axiom.

```text
Compiler
   ↓
Object Writer
   ↓
.o
   ↓
Linker
   ↓
Executable
```

Compiler không nên phải biết toàn bộ:

```text
library resolution
symbol resolution
section placement
dead stripping
shared library
PIE
TLS
dynamic linking
```

ngay từ Genesis.

Ban đầu có thể:

```text
Axiom compiler
      ↓
ELF .o
      ↓
system ld
      ↓
ELF executable
```

Sau này:

```text
Axiom compiler
      ↓
Axiom object writer
      ↓
Axiom linker
      ↓
ELF executable
```

---

# 21. Genesis Trace hoàn chỉnh

Ta đã có:

```text
SOURCE
 │
 ▼
LEXER
 │
 ▼
AST
 │
 ▼
NAME RESOLUTION
 │
 ▼
HIR
 │
 ▼
TYPE CHECK
 │
 ▼
TYPED HIR
 │
 ▼
MIR
 │
 ▼
OWNERSHIP / EFFECT / CONCURRENCY VERIFIER
 │
 ▼
VERIFIED MIR
 │
 ├──────────────► SEMANTIC ORACLE
 │                     │
 │                     ▼
 │                   42
 │
 ▼
SEMANTIC OPTIMIZATION
 │
 ▼
ABI MIR
 │
 ▼
LIR
 │
 ▼
TARGET LEGALIZATION
 │
 ▼
MACHINE IR
 │
 ▼
REGISTER ALLOCATION
 │
 ▼
FINAL MACHINE IR
 │
 ▼
X86 ENCODER
 │
 ▼
MACHINE BYTES
 │
 ▼
ELF OBJECT
 │
 ▼
LINKER
 │
 ▼
NATIVE EXECUTABLE
 │
 ▼
42
```

---

# 22. Điều quan trọng nhất rút ra

Genesis này cho chúng ta một nguyên tắc rất mạnh:

### Axiom compiler có 3 "thế giới"

```text
┌─────────────────────────────────────────┐
│         SEMANTIC WORLD                  │
│ AST HIR MIR Verifier Oracle             │
│                                         │
│ "Chương trình có nghĩa gì?"             │
└──────────────────┬──────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────┐
│         REPRESENTATION WORLD             │
│ ABI MIR / LIR                            │
│                                         │
│ "Nghĩa đó biểu diễn thế nào?"           │
└──────────────────┬──────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────┐
│         MACHINE WORLD                   │
│ Machine IR / Allocator / Encoder        │
│                                         │
│ "CPU thực hiện nó bằng cách nào?"       │
└─────────────────────────────────────────┘
```

Điều này giúp tránh một lỗi rất phổ biến khi tự xây compiler:

> **Không để machine representation trở thành semantic definition.**

Ví dụ:

```text
view<T>
```

không có nghĩa là:

```text
struct { T* ptr; usize len; }
```

Nó **có thể** được biểu diễn như vậy.

Tương tự:

```text
Vec<T>
```

không có nghĩa ngôn ngữ bắt buộc phải có:

```text
ptr + len + capacity
```

Đó chỉ là một ABI/implementation representation phù hợp.

---

# 23. Genesis Acceptance Test

Ta nên đóng băng test đầu tiên thành một contract:

```text
TEST: G0_ADD_001

SOURCE:
fn add(a: i64, b: i64) -> i64 {
    a + b
}

fn main() -> i64 {
    add(20, 22)
}

EXPECT:
compile = success
verify = success
interpret = 42
native_exit_code = 42

REQUIRED:
AST = valid
HIR = valid
MIR = valid
VerifiedMIR = valid
LIR = valid
MachineIR = valid
ELF = valid
```

Và quan trọng hơn:

```text
OracleResult == NativeResult
```

phải trở thành **invariant xuyên suốt quá trình phát triển compiler**.

---

# 24. Sau Genesis Trace, bước tiếp theo

Tôi đề xuất **không nhảy sang struct ngay**.

Bước kế tiếp nên là xây **Axiom Compiler Kernel v0.1** với đúng 5 thành phần:

```text
Lexer
Parser
Name Resolver
Type Checker
MIR Builder
```

sau đó thêm:

```text
Verifier
Semantic Oracle
```

rồi mới xây backend.

Và vertical slice đầu tiên nên là:

```text
G0  return 42
G1  arithmetic
G2  function call
G3  if
G4  while
G5  multiple functions + ELF
```

Chỉ khi `G5` chạy ổn mới đưa:

```text
struct
Copy / Move
Drop
view / mut_view
```

vào.

Lý do là nếu đưa ownership vào trước khi compiler có **full end-to-end executable pipeline**, ta sẽ rất dễ dành hàng tuần xây verifier nhưng chưa chứng minh được Axiom thực sự tạo native code.

**Mốc cực kỳ quan trọng của Axiom nên là:**

> `Axiom source → own MIR → own verifier → own LIR → own x86-64 machine code → ELF → chạy thật.`

Sau mốc đó, mọi tính năng mới đều có thể được kiểm chứng bằng cùng một pipeline thay vì chỉ tồn tại trên giấy.