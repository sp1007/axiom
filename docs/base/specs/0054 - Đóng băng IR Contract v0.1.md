Tiếp tục thì bây giờ nên đi xuống **mức thiết kế compiler có thể giao thẳng cho AI agent implement**. Sau Genesis acceptance criteria, phần quan trọng nhất là đóng băng **IR contracts** — nếu IR không chặt, về sau ownership, generics, async và backend sẽ phải sửa dây chuyền.

# 23. Đóng băng IR Contract v0.1

Tôi đề xuất Axiom có **4 IR chính** trước Machine IR:

```text
AST
 │
 ▼
HIR
 │
 ▼
MIR        ← semantic truth
 │
 ▼
ABI MIR    ← calling convention / representation
 │
 ▼
LIR        ← machine-independent low-level
 │
 ▼
Machine IR
```

Trong đó:

| IR | Nhiệm vụ | Biết CPU? |
|---|---|---:|
| AST | Syntax | Không |
| HIR | Semantic source model | Không |
| MIR | Ownership, types, effects, CFG | Không |
| ABI MIR | ABI representation | Một phần |
| LIR | Low-level operations | Không |
| Machine IR | CPU instructions/registers | Có |

**Không được để một tầng làm nhiệm vụ của tầng khác.**

---

# 24. AST Contract

AST phải giữ source location.

Ví dụ:

```text
AstFunction {
    name
    params[]
    return_type
    body
    span
}
```

Expression:

```text
AstExpr =
    IntLiteral
    BoolLiteral
    Name
    Binary
    Unary
    Call
    If
    Block
```

Mọi node:

```text
Span {
    file_id
    start
    end
}
```

Sau này diagnostics có thể nói:

```text
AX_TYPE_0007
cannot add `i64` and `bool`

main.ax:12:17
```

Đây là lý do **source location phải đi xuyên compiler**, nhưng không cần đi vào machine code trừ debug metadata.

---

# 25. HIR: Name Resolution đã hoàn tất

Đây là ranh giới quan trọng.

AST:

```text
a + b
```

HIR:

```text
ADD(
    LocalId(3),
    LocalId(4)
)
```

Không còn lookup:

```text
"a"
"b"
```

trong các compiler phase phía sau.

Symbol table:

```text
SymbolId
LocalId
FunctionId
TypeId
ModuleId
TraitId
```

nên là các ID số nguyên ổn định.

Ví dụ:

```text
FunctionId(17)
LocalId(4)
TypeId(9)
```

Điều này vừa nhanh vừa dễ serialize/debug.

---

# 26. Type representation

Không nên để type là string.

```text
TypeId
```

trỏ vào:

```text
TypeTable
```

Ví dụ:

```text
Type =
    Bool
    I64
    U64
    F32
    F64
    Unit

    Struct(StructId)
    Enum(EnumId)

    Array(TypeId, Length)
    Tuple(TypeId[])
    
    Function(FunctionTypeId)

    View(TypeId)
    MutView(TypeId)

    GenericParam(GenericId)
```

Sau này:

```text
Option<T>
Result<T,E>
dyn Trait
```

chỉ cần mở rộng type system.

---

# 27. Type identity phải độc lập representation

Ví dụ:

```axiom
type UserId = distinct u64
```

thì:

```text
UserId != u64
```

dù machine representation đều có thể là:

```text
64-bit integer
```

Đây là nguyên tắc:

```text
semantic type
    ≠
machine representation
```

Nếu không giữ nguyên tắc này, compiler sẽ rất dễ biến Axiom thành C với syntax đẹp hơn.

---

# 28. MIR phải có Place

Đây là một điểm cực kỳ quan trọng cho ownership về sau.

Không nên MIR chỉ có:

```text
LOAD %3
STORE %4
```

mà phải có khái niệm:

```text
Place
```

Ví dụ:

```text
Place {
    base: Local(3),
    projections: [
        Field(1)
    ]
}
```

Sau này:

```axiom
p.name
p.age
```

sẽ trở thành:

```text
Place(p.name)
Place(p.age)
```

và ownership verifier có thể biết:

```text
p.name
```

không nhất thiết xung đột với:

```text
p.age
```

---

# 29. Place là nền móng của ownership

Ví dụ sau này:

```axiom
struct Person {
    name: String,
    age: i32
}
```

và:

```axiom
let name = move p.name;
print(p.age);
```

Verifier không được nghĩ:

```text
p = MOVED
```

mà phải biết:

```text
p
├── name → MOVED
└── age  → OWNED
```

Do đó MIR nên có:

```text
Place
 ├── Local
 ├── Field
 ├── Index
 └── Deref
```

Ngay cả Genesis chưa dùng hết cũng nên thiết kế từ đầu.

---

# 30. Operand và Value phải tách biệt

MIR:

```text
Operand =
    Const
    Copy(Place)
    Move(Place)
    Value(ValueId)
```

Ví dụ:

```text
%3 = ADD
    Copy(a),
    Copy(b)
```

và:

```text
%4 = MOVE x
```

Đây là nơi semantic ownership bắt đầu xuất hiện.

Đừng biến:

```text
MOVE
```

thành machine `MOV`.

Hai thứ hoàn toàn khác nhau.

**Axiom `MOVE` là ownership operation.**

Nó có thể compile thành:

```text
không có instruction nào
```

nếu compiler chỉ cần chuyển SSA ownership state.

---

# 31. MIR instruction model

Tôi đề xuất Genesis dùng:

```text
Statement
    Assign { destination, rvalue }

Terminator
    Return
    Jump
    Branch
    Switch
    Call
    Panic
    Trap
```

Rvalue:

```text
Use
BinaryOp
UnaryOp
Cast
Load
View
Aggregate
```

Ví dụ:

```text
bb0:
    %2 = Add(Copy(%0), Copy(%1))
    Return(%2)
```

Sau này:

```text
bb0:
    %3 = Move(place)
    Drop(place)
    ...
```

---

# 32. CFG invariant

Mỗi MIR function:

```text
entry_block
blocks[]
```

Mỗi block:

```text
statements[]
terminator
```

**Mỗi reachable block phải có đúng một terminator.**

Không cho:

```text
statement
statement
EOF
```

hoặc:

```text
RETURN
JUMP
```

trong cùng block.

Invariant:

```text
MIR-CFG-01:
Every reachable basic block has exactly one terminator.

MIR-CFG-02:
A terminator is the final operation of a block.

MIR-CFG-03:
Every branch target references an existing block.

MIR-CFG-04:
No instruction occurs after a terminator.
```

Những invariant đơn giản này giúp compiler agent rất nhiều.

---

# 33. SSA nhưng ownership không phải SSA

Đây là điểm cần đóng băng rõ.

Axiom MIR có:

```text
Value SSA
```

nhưng ownership state riêng:

```text
Ownership State
```

Ví dụ:

```text
%x0 = value
%x1 = MOVE x
```

SSA có thể coi:

```text
%x1
```

là value mới.

Nhưng ownership verifier phải biết:

```text
x → MOVED
```

Hai hệ thống không được trộn.

```text
SSA
  = data-flow identity

Ownership
  = resource authority
```

Đây là kiến trúc rất quan trọng của Axiom.

---

# 34. MIR verifier

Verifier không chỉ kiểm tra type.

Nó gồm:

```text
Typed MIR
    │
    ├── Type verifier
    ├── CFG verifier
    ├── Initialization verifier
    ├── Ownership verifier
    ├── Capability verifier
    ├── Effect verifier
    ├── Concurrency verifier
    └── Cleanup verifier
             │
             ▼
        Verified MIR
```

Genesis ban đầu chỉ cần:

```text
Type
CFG
Initialization
```

nhưng API phải chừa chỗ cho:

```text
Ownership
Capability
Effect
Concurrency
Cleanup
```

---

# 35. Verified MIR là một compiler boundary

Tôi đề xuất một quy tắc mạnh:

> **Optimizer không được chạy trên MIR chưa verified.**

Tức:

```text
MIR
 ↓
Verifier
 ↓
❌ reject
```

hoặc:

```text
MIR
 ↓
Verifier
 ↓
Verified MIR
 ↓
Optimizer
```

Như vậy optimizer được phép giả định các invariant đã được chứng minh.

Ví dụ:

```text
Verified MIR guarantees:

no safe UAF
no safe double-drop
valid initialization
valid view provenance
valid safe aliasing
valid Send/Share
```

Optimizer không cần chứng minh lại tất cả.

---

# 36. Nhưng optimizer không được phá invariant

Ví dụ compiler thấy:

```text
x = 10
y = x
return y
```

có thể biến thành:

```text
return 10
```

Nhưng không được biến một chương trình:

```text
verified
```

thành:

```text
invalid ownership
```

Do đó:

```text
Verified MIR
      ↓
optimization
      ↓
Verified/Preserving MIR
```

về mặt contract phải giữ semantic invariants.

---

# 37. LIR nên cực kỳ nhỏ

Tôi càng nghiêng về việc **không biến Axiom LIR thành LLVM thứ hai**.

Genesis LIR chỉ cần:

```text
CONST
COPY
ADD
SUB
MUL
DIV

ICMP
FCMP

LOAD
STORE

JUMP
BRANCH
RETURN

CALL
TRAP

PHI
SELECT
```

và sau này:

```text
ATOMIC_*
VOLATILE_*
MEMCPY
MEMSET
VECTOR_*
```

Không nên có:

```text
LIR_OWNERSHIP_CHECK
LIR_BORROW
LIR_TRAIT
LIR_GENERIC
LIR_ASYNC
```

Những thứ đó phải biến mất trước LIR nếu không có runtime effect.

---

# 38. Đây chính là “semantic erasure”

Ví dụ:

```axiom
fn square(x: i64) -> i64 {
    x * x
}
```

Generic/ownership/type metadata cuối cùng không cần tồn tại.

Machine code:

```text
imul ...
ret
```

Tương tự:

```text
Send
Share
Copy
Move
view
mut_view
```

nhiều trường hợp có thể **zero runtime representation**.

Đây nên trở thành một nguyên tắc chính thức:

### AZC-01

> Semantic mechanisms that have no observable runtime effect must not impose mandatory runtime representation.

---

# 39. Nhưng Drop là ngoại lệ

Ví dụ:

```axiom
fn f() {
    let file = File.open(...);
}
```

`Drop` có observable effect:

```text
close file
```

nên không thể đơn giản xóa.

MIR:

```text
CALL File.open
...
DROP file
```

Optimizer chỉ được xóa:

```text
DROP
```

nếu chứng minh Drop không có observable effect.

Vì vậy Axiom cần khái niệm effect.

---

# 40. Effect summary

Không cần hệ thống effect type phức tạp ngay từ đầu.

LIR có thể giữ:

```text
Effect =
    None
    Read
    Write
    ReadWrite
    Atomic
    Volatile
    Unknown
```

Ví dụ:

```text
ADD
```

→ `None`

```text
LOAD
```

→ `Read`

```text
STORE
```

→ `Write`

```text
CALL unknown_function
```

→ `Unknown`

```text
ATOMIC_ADD
```

→ `Atomic`

Như vậy optimizer có thông tin cần thiết mà LIR vẫn nhỏ.

---

# 41. Call effect

Function metadata:

```text
FunctionEffect {
    reads
    writes
    may_allocate
    may_panic
    may_block
    may_suspend
}
```

Nhưng **không nhất thiết tất cả phải là type-system surface syntax**.

Compiler có thể suy luận.

Ví dụ:

```axiom
fn square(x: i64) -> i64 {
    x * x
}
```

compiler biết:

```text
reads memory: no
writes memory: no
allocate: no
panic: no
suspend: no
```

→ rất dễ inline.

---

# 42. Điều này rất hợp với mục tiêu của bạn

Thay vì bắt programmer viết:

```text
fn foo() pure noalloc noread ...
```

Axiom có thể:

```text
fn foo(...) ...
```

Compiler tự phân tích.

Tức là:

```text
Programmer simplicity
        +
Compiler sophistication
```

đúng với triết lý ban đầu của Axiom.

---

# 43. Nhưng phải có escape hatch

Khi compiler không chứng minh được:

```text
unknown
```

thì không được đoán.

Ví dụ FFI:

```axiom
extern fn external_call(x: i64) -> i64;
```

Compiler mặc định:

```text
Effect = Unknown
```

trừ khi programmer/compiler metadata cung cấp contract.

Đây là nguyên tắc:

> **Không chứng minh được → conservative, không đoán.**

---

# 44. Diagnostic architecture cũng nên đóng băng ngay

Compiler diagnostic:

```text
Diagnostic {
    severity
    code
    message
    primary_span
    secondary_spans[]
    notes[]
    help[]
    causes[]
}
```

Ví dụ:

```text
error[AX_TYPE_0007]: cannot add `i64` and `bool`

  --> main.ax:8:9
   |
 8 | x + enabled
   |   ^^^^^^^^^
   |
   = left operand: i64
   = right operand: bool

help: convert the value explicitly if a valid conversion exists
```

Machine JSON:

```json
{
  "code": "AX_TYPE_0007",
  "severity": "error",
  "message": "cannot add i64 and bool"
}
```

AI agent sẽ cực kỳ hưởng lợi từ điều này.

---

# 45. Compiler phải deterministic

Cùng:

```text
source
compiler version
target
flags
dependencies
```

phải cho cùng:

```text
diagnostics
IR semantics
```

và ideally:

```text
binary
```

hoặc ít nhất reproducible mode phải cho binary hash giống nhau.

Không được để:

```text
hash map iteration
parallel race
random optimization
```

làm semantic result thay đổi.

---

# 46. Một điều tôi muốn thêm vào kiến trúc Axiom

Vì bạn muốn AI agent tự xây compiler, hãy thiết kế **Compiler Contract Test** ngay từ đầu.

Ví dụ:

```text
compiler_contract/
├── lexer.contract
├── parser.contract
├── typeck.contract
├── mir.contract
├── verifier.contract
├── lir.contract
├── abi.contract
├── x86.contract
└── elf.contract
```

Mỗi contract có:

```text
input
expected result
invariants
```

Agent thay implementation vẫn phải pass contract.

Điều này biến compiler thành:

```text
AI-agent implementation
        ↓
Contract
        ↓
Tests
        ↓
Acceptance
```

thay vì để agent tự “nghĩ rằng compiler đã đúng”.

---

# 47. Và đây là bước tiếp theo tôi khuyên làm ngay

Chúng ta đã có architecture đủ rộng. **Không nên tiếp tục thiết kế thêm feature.**

Bây giờ nên đóng băng một tài liệu:

```text
AXIOM-GENESIS-COMPILER-SPEC-v0.1.md
```

Nó sẽ chứa chính xác:

```text
1. Genesis language subset
2. AST schema
3. HIR schema
4. Type representation
5. MIR schema
6. MIR CFG invariants
7. MIR instruction set
8. Verified MIR contract
9. Genesis LIR
10. ABI MIR
11. SysV AMD64 ABI
12. Machine IR
13. x86-64 instruction subset
14. Register allocation contract
15. x86 encoder contract
16. ELF object contract
17. Semantic Oracle
18. Differential tests
19. Acceptance criteria G0
20. CLI
```

Sau tài liệu này, AI agent có thể bắt đầu **viết compiler thật**, thay vì tiếp tục “thiết kế ngôn ngữ trên giấy”.

Và quan trọng hơn: **ownership/view/Drop/concurrency sau này sẽ được thêm vào MIR + verifier mà không phải phá AST → HIR → LIR → backend đã xây ở Genesis.**