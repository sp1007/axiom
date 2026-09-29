Tiếp tục với **BOOTSTRAP-004 — AXIOM0 IMPLEMENTATION LADDER**.

Đây là bước tôi nghĩ rất quan trọng để tránh một lỗi thường gặp khi dùng AI agent xây compiler: **agent thấy architecture rất lớn rồi cố code toàn bộ cùng lúc**, dẫn tới một compiler có hàng chục module nhưng không có vertical slice chạy được.

Mục tiêu lần này là biến architecture thành **một chuỗi milestone có thể kiểm chứng**.

---

# BOOTSTRAP-004 — AXIOM0 IMPLEMENTATION LADDER

## 1. Quy tắc số 1: luôn có compiler chạy được

Mỗi milestone phải có:

```text
source
  ↓
axiom0
  ↓
native executable
```

hoặc ít nhất:

```text
source
  ↓
axiom0
  ↓
MIR
```

Không được có milestone kiểu:

> "Đã hoàn thành toàn bộ Type System nhưng chưa compile được chương trình."

Architecture phải được xây theo **vertical slices**.

---

# 2. Các giai đoạn lớn

Tôi đề xuất:

```text
BOOT-00  Infrastructure
BOOT-01  Lexer
BOOT-02  Parser
BOOT-03  Minimal AST → MIR
BOOT-04  x86-64 codegen
BOOT-05  ELF object
BOOT-06  Native linker
BOOT-07  Ownership
BOOT-08  Struct/Enum
BOOT-09  Type inference
BOOT-10  Traits/Generics
BOOT-11  Full MIR
BOOT-12  Optimization
BOOT-13  Self compilation
BOOT-14  Reproducible bootstrap
```

Nhưng thực tế nên chia nhỏ hơn.

---

# 3. BOOT-00 — Compiler Skeleton

Repository:

```text
axiom/
├── compiler/
├── core/
├── std/
├── runtime/
├── targets/
├── tests/
└── bootstrap/
```

Stage-0 ban đầu có thể được viết bằng **một host implementation tạm thời**.

Ví dụ:

```text
bootstrap/
└── axiom0/
```

Mục tiêu:

```text
axiom0 --version
```

và:

```text
axiom0 check test.ax
```

---

# 4. BOOT-00 không được có backend phức tạp

Ban đầu:

```text
parse
→ AST
→ dump
```

Ví dụ:

```text
fn main() {}
```

output:

```text
Function main
```

Đây là smoke test đầu tiên.

---

# 5. BOOT-01 — Lexer

Test tối thiểu:

```text
fn main() {
    let x = 42;
}
```

Lexer phải nhận:

```text
fn
main
(
)
{
let
x
=
42
;
}
```

Test thêm:

```text
// comment
/* nested /* comment */ */
```

Unicode identifier.

UTF-8 invalid sequence.

---

# 6. BOOT-02 — Parser

Parser phải parse:

```text
fn main() {
}
```

sau đó:

```text
fn main() {
    let x = 42;
}
```

sau đó:

```text
fn main() -> i32 {
    return 42;
}
```

Không vội generic/trait.

---

# 7. BOOT-03 — Expression Engine

Thêm:

```text
1 + 2 * 3
```

Pratt parser.

Phải đảm bảo:

```text
1 + (2 * 3)
```

chứ không:

```text
(1 + 2) * 3
```

Test:

```text
+
-
*
/
%
==
!=
<
<=
>
>=
&&
||
!
```

---

# 8. BOOT-04 — Minimal Typed HIR

Bây giờ compiler phải hiểu:

```text
i32
u32
bool
unit
```

Ví dụ:

```text
let x: i32 = 42;
```

Compiler tạo:

```text
Typed HIR
```

Không cần inference đầy đủ.

---

# 9. BOOT-05 — Minimal MIR

Chương trình:

```text
fn main() -> i32 {
    return 42;
}
```

thành:

```text
bb0:
    %0 = const i32 42
    return %0
```

Đây là **mốc kiến trúc cực kỳ quan trọng**.

Từ đây compiler không còn cần AST để codegen.

---

# 10. MIR Interpreter

Ngay lập tức xây:

```text
axiom0 run-mir test.ax
```

Output:

```text
42
```

Tại sao phải làm sớm?

Vì MIR interpreter trở thành **semantic oracle**.

Nếu sau này:

```text
-O0 = 42
-O2 = 42
-native = 42
```

thì ta có ba đường kiểm chứng.

---

# 11. BOOT-06 — x86-64 Minimal Backend

Chỉ cần:

```text
CONST
RETURN
```

Ví dụ:

```text
fn main() -> i32 {
    return 42;
}
```

Machine IR:

```text
mov eax, 42
ret
```

Không cần assembler.

Axiom tự encode bytes.

---

# 12. BOOT-07 — ELF Object

Compiler tạo:

```text
main.o
```

bằng Object Writer của chính Axiom.

Không:

```text
nasm
gas
clang
```

---

# 13. BOOT-08 — Minimal Native Executable

Axiom linker tạo:

```text
hello
```

Không libc.

Không CRT.

Không external linker.

Linux entry:

```text
_start
```

có thể trực tiếp gọi syscall exit.

Ví dụ semantic:

```text
fn main() -> i32 {
    return 42;
}
```

→ executable exit code `42`.

Đây là **Vertical Slice #1**:

```text
Axiom
 ↓
Lexer
 ↓
Parser
 ↓
Type
 ↓
MIR
 ↓
x86-64
 ↓
Machine Encoder
 ↓
ELF
 ↓
Axiom Linker
 ↓
Linux executable
```

---

# 14. Đây là milestone cực kỳ quan trọng

Khi Vertical Slice #1 chạy:

> **Axiom đã thực sự là compiler**, dù ngôn ngữ còn cực kỳ nhỏ.

Từ đây mọi feature mới đều phải đi xuyên qua pipeline thật.

---

# 15. BOOT-09 — Variables

Thêm:

```text
fn main() -> i32 {
    let x = 40;
    let y = 2;
    return x + y;
}
```

MIR:

```text
%0 = const 40
%1 = const 2
%2 = add %0, %1
return %2
```

Optimizer sau này có thể biến thành:

```text
return 42
```

---

# 16. BOOT-10 — Branch

```text
fn main(x: i32) -> i32 {
    if x > 10 {
        return 1;
    }

    return 0;
}
```

MIR:

```text
bb0:
    %cmp = cmp_gt x, 10
    cond_br %cmp, bb1, bb2

bb1:
    return 1

bb2:
    return 0
```

Đây là lúc CFG thực sự xuất hiện.

---

# 17. BOOT-11 — Loop

```text
while x < 10 {
    x = x + 1;
}
```

MIR phải có:

```text
header
body
exit
```

Test:

```text
break
continue
```

và cleanup infrastructure phải bắt đầu xuất hiện.

---

# 18. BOOT-12 — Functions

```text
fn add(a: i32, b: i32) -> i32 {
    return a + b;
}

fn main() -> i32 {
    return add(20, 22);
}
```

Bây giờ mới cần:

```text
CALL
RETURN
ABI arguments
ABI return
```

---

# 19. BOOT-13 — Calling Convention

x86-64 Linux:

```text
fn add(a, b)
```

phải map đúng ABI.

Ví dụ các integer arguments đi qua register ABI thích hợp.

Không hardcode:

```text
"a nằm ở rdi"
```

vào MIR.

Phải:

```text
MIR
 ↓
ABI Lowering
 ↓
LIR
 ↓
Machine
```

---

# 20. BOOT-14 — Struct

```text
struct Point {
    x: i32,
    y: i32,
}
```

Test:

```text
fn distance2(p: Point) -> i32 {
    return p.x * p.x + p.y * p.y;
}
```

Bắt đầu kiểm tra:

```text
Field
Place
Load
Store
Layout
Aggregate ABI
```

---

# 21. BOOT-15 — Arrays

```text
let a: [i32; 4];
```

và:

```text
a[0]
a[i]
```

Phải có bounds checking trong safe code.

Compiler có thể loại bỏ check nếu chứng minh được.

---

# 22. BOOT-16 — `view`

Bây giờ mới đưa capability model vào vertical slice:

```text
fn sum(a: view<i32>) -> i32
```

và:

```text
let a = [1, 2, 3];
return sum(a);
```

Owner:

```text
a
```

→ ephemeral READ capability.

Không copy array.

---

# 23. BOOT-17 — `mut_view`

```text
fn increment(a: mut_view<i32>) {
    ...
}
```

Test:

```text
increment(a);
```

và cố tình tạo conflict:

```text
let x = view(a);
increment(a);
use(x);
```

Compiler phải phát hiện capability conflict nếu `x` vẫn live.

---

# 24. BOOT-18 — Move

Ví dụ:

```text
let a = make_buffer();
let b = a;
use(a); // error
```

Compiler phải tạo:

```text
Owned
  ↓
Moved
```

Không cần runtime check.

---

# 25. BOOT-19 — Copy

```text
let a: i32 = 10;
let b = a;
return a + b;
```

vẫn hợp lệ.

`i32` có semantic `Copy`.

Điểm này phải được phân biệt rõ với:

```text
bitwise-copyable
```

---

# 26. BOOT-20 — Drop

Tạo:

```text
struct Buffer { ... }
```

có Drop.

Test:

```text
fn foo() {
    let x = make_buffer();
    return;
}
```

MIR phải có:

```text
DROP x
RETURN
```

---

# 27. BOOT-21 — Cleanup Graph

Test:

```text
fn foo() -> Result<i32, Error> {
    let a = acquire();
    let b = acquire();

    if failed() {
        return Err(...);
    }

    return Ok(42);
}
```

Cả hai resource phải cleanup đúng đường control flow.

Đây là lúc:

```text
CleanupGraph
```

trở thành infrastructure thực sự.

---

# 28. BOOT-22 — `Result`

```text
enum Result<T, E> {
    Ok(T),
    Err(E),
}
```

và:

```text
?
```

Phải lower thành CFG.

Không có exception runtime.

---

# 29. BOOT-23 — `Option`

```text
enum Option<T> {
    Some(T),
    None,
}
```

và:

```text
match
```

Bắt đầu kiểm tra exhaustive matching.

---

# 30. BOOT-24 — Enum

Ví dụ:

```text
enum TokenKind {
    Identifier,
    Number,
    Plus,
    Minus,
}
```

Đây chính là lúc compiler của Axiom bắt đầu tự viết lexer bằng Axiom.

---

# 31. BOOT-25 — Compiler Internals Rewrite

Đến đây có thể viết:

```text
Token
TokenKind
Span
Lexer
```

bằng Axiom.

Đây là **Vertical Slice #2**:

```text
Axiom compiler
    ↓
Lexer written in Axiom
    ↓
Axiom compiler
    ↓
native lexer executable
```

---

# 32. BOOT-26 — AST

Tiếp tục rewrite:

```text
AST
Parser
```

bằng Axiom.

Khi parser Axiom tự compile được:

```text
Stage-1 compiler
```

bắt đầu hình thành.

---

# 33. BOOT-27 — Resolver

Rewrite:

```text
Symbol
Scope
Module
NameResolver
```

bằng Axiom.

---

# 34. BOOT-28 — Type System

Rewrite:

```text
Type
TypeId
TypeInterner
Inference
TraitSolver
```

Đây sẽ là một milestone lớn.

Không nên làm tất cả một lần.

---

# 35. BOOT-29 — Ownership Checker

Đây có thể là một trong những module phức tạp nhất:

```text
OwnershipState
Capability
Region
Alias
Move
Drop
Escape
```

Nhưng nó phải được viết bằng **chính Axiom semantics** mà nó kiểm tra.

Đây là một bài test rất mạnh:

> Axiom có đủ expressive power để tự mô tả ownership checker của chính nó hay không?

---

# 36. BOOT-30 — MIR

Sau đó compiler tự viết:

```text
Mir
MirBuilder
CleanupGraph
MirVerifier
```

bằng Axiom.

---

# 37. BOOT-31 — MIR Interpreter

Đây là module đặc biệt quan trọng:

```text
MirInterpreter
```

Nó có thể chạy compiler-generated MIR mà không cần native backend.

Dùng cho:

```text
compiler testing
optimizer testing
fuzzing
bootstrap validation
```

---

# 38. BOOT-32 — Optimizer

Bắt đầu từ:

```text
ConstantFold
DCE
CFGSimplify
```

sau đó:

```text
SCCP
CopyProp
DSE
Inline
Escape
Loop
```

Không nên viết O3 trước.

---

# 39. BOOT-33 — Backend

Sau khi frontend đã tự host:

```text
LIR
MachineIR
x86_64
Encoder
ObjectWriter
```

được chuyển sang Axiom.

---

# 40. BOOT-34 — Linker

Cuối cùng:

```text
ELF Reader
Symbol Resolver
Section Layout
Relocation
Executable Writer
```

cũng được viết bằng Axiom.

Khi đó:

```text
Stage-1 compiler
```

gần như hoàn chỉnh.

---

# 41. BOOT-35 — Compiler Compiles Compiler

Đây là checkpoint:

```text
axiom0 compiler.ax
```

sản xuất:

```text
axiom-stage1
```

Sau đó:

```text
axiom-stage1 compiler.ax
```

sản xuất:

```text
axiom-stage2
```

---

# 42. BOOT-36 — Fixed Point

Ta cần:

```text
Stage2(CompilerSource)
=
Stage3(CompilerSource)
```

không nhất thiết binary hash phải giống ngay nếu chưa deterministic hoàn toàn.

Trước tiên kiểm tra:

```text
same tests
same diagnostics
same executable semantics
```

Sau đó mới hướng tới:

```text
bit-for-bit reproducibility
```

---

# 43. BOOT-37 — Reproducible Bootstrap

Cuối cùng:

```text
Stage2
  ↓
Compiler
  ↓
Stage3
```

và:

```text
Stage3
  ↓
Compiler
  ↓
Stage4
```

Nếu:

```text
SHA256(Stage3) == SHA256(Stage4)
```

thì ta đạt fixed point binary.

---

# 44. Một thay đổi quan trọng tôi đề xuất

Không chờ đến cuối mới có test.

**Mỗi milestone phải có test suite riêng.**

Ví dụ:

```text
tests/
├── lexer/
├── parser/
├── types/
├── ownership/
├── mir/
├── optimizer/
├── codegen/
├── object/
├── linker/
└── bootstrap/
```

---

# 45. Test format

Mỗi test source:

```text
tests/mir/basic/add.ax
```

có expected:

```text
tests/mir/basic/add.expected
```

hoặc metadata:

```text
// expect: 42
// exit: 42
```

---

# 46. Compile-fail tests

Ví dụ:

```text
let x = buffer();
let y = x;
use(x);
```

expected:

```text
AX1401
```

Không chỉ kiểm tra:

```text
"có lỗi"
```

mà kiểm tra **diagnostic code ổn định**.

---

# 47. Differential test

Trong bootstrap:

```text
Axiom MIR Interpreter
        ↕
Native Backend
```

cùng chạy một chương trình.

Nếu:

```text
MIR → 42
Native → 41
```

→ backend bug.

Đây sẽ là một công cụ debug cực mạnh.

---

# 48. Optimization differential

Chạy:

```text
-O0
-O1
-O2
-O3
```

và MIR interpreter.

Tất cả phải cùng semantic result.

Đây là cách phát hiện optimizer phá semantics.

---

# 49. Fuzzing

Sau khi lexer/parser ổn:

```text
random source
   ↓
lexer/parser
```

không được:

```text
segfault
infinite loop
memory corruption
```

Sau MIR:

```text
random valid AST
 ↓
MIR
 ↓
interpreter
 ↓
optimized MIR
 ↓
interpreter
```

phải tương đương.

---

# 50. AI Agent không được tự ý vượt milestone

Đây là điều tôi đặc biệt khuyên nếu Axiom sẽ được xây bằng Claude Code/Gemini/Antigravity.

Agent phải obey:

```text
MILESTONE GATE
```

Ví dụ:

```text
BOOT-12
```

chỉ được chuyển sang:

```text
BOOT-13
```

khi:

```text
✓ unit tests
✓ semantic tests
✓ negative tests
✓ MIR verifier
✓ native execution
✓ no regression
```

đều pass.

---

# 51. Agent phải có "Architecture Authority"

Trong repository nên có:

```text
docs/
├── AXIOM-SPEC.md
├── ARCHITECTURE.md
├── INVARIANTS.md
├── COMPILER-PIPELINE.md
├── BOOTSTRAP.md
└── DECISIONS/
```

Agent **không được tự sửa semantic invariant chỉ vì implementation khó**.

Nếu implementation gặp vấn đề:

```text
Implementation Problem
        ↓
Research
        ↓
Proposal
        ↓
Architecture Decision
        ↓
Human approval
        ↓
Implementation
```

---

# 52. Nhưng agent được tự giải quyết implementation

Ví dụ:

> "Linear Scan không xử lý tied operands tốt."

Agent được phép nghiên cứu và thay implementation.

Nhưng không được tự đổi:

```text
Axiom ownership semantics
```

thành một mô hình khác chỉ vì dễ code hơn.

---

# 53. Ba loại thay đổi

Tôi đề nghị agent phân biệt:

### TYPE A — Implementation

Không thay semantics.

```text
HashMap implementation
Register allocator algorithm
```

Agent tự làm.

### TYPE B — Architecture clarification

Không thay semantics.

```text
thêm abstraction
đổi module
```

Agent có thể đề xuất và thực hiện nếu invariant không đổi.

### TYPE C — Semantic change

Ví dụ:

```text
mut_view có thể copy
Drop có thể throw
```

Phải dừng và yêu cầu quyết định.

---

# 54. Đây sẽ là "constitution" của Axiom

```text
AXIOM-SPEC
     ↓
INVARIANTS
     ↓
ARCHITECTURE
     ↓
IMPLEMENTATION
```

Không được đảo ngược:

```text
implementation
     ↓
"vì code thế này nên semantics phải thế"
```

---

# 55. Milestone quan trọng nhất

Nếu phải chọn chỉ **5 checkpoint**:

```text
V0 — Lexer/Parser
V1 — Source → MIR
V2 — Source → Native ELF
V3 — Compiler written in Axiom
V4 — Reproducible self-hosting
```

Đây là 5 mốc chứng minh toàn bộ ý tưởng.

---

# 56. Cuối cùng, bootstrap architecture

Ta có:

```text
             ┌──────────────────────┐
             │   Axiom Source       │
             └──────────┬───────────┘
                        │
                   Stage-0
                        │
              ┌─────────▼─────────┐
              │     Axiom MIR     │
              └─────────┬─────────┘
                        │
              ┌─────────▼─────────┐
              │ Native Backend    │
              └─────────┬─────────┘
                        │
              ┌─────────▼─────────┐
              │ Axiom Object      │
              └─────────┬─────────┘
                        │
              ┌─────────▼─────────┐
              │ Axiom Linker      │
              └─────────┬─────────┘
                        │
                  Stage-1
                        │
                        ▼
                compile itself
                        │
                        ▼
                  Stage-2
                        │
                        ▼
                  Stage-3
                        │
                        ▼
               reproducible
                fixed point
```

## Kết luận

Từ đây tôi nghĩ **không nên tiếp tục mở thêm feature của ngôn ngữ một cách ngang hàng** nữa. Kiến trúc Axiom đã khá đầy đủ.

Bước tiếp theo nên đi vào phần có tính quyết định đối với mục tiêu của bạn:

**BOOTSTRAP-005 — đặc tả chính xác Stage-0 implementation**, bao gồm:

- host implementation dùng ngôn ngữ gì trong giai đoạn đầu;
- API tối thiểu của `Vec`, `Map`, `Arena`, `String`, `Result`;
- format của AST/HIR/MIR;
- cách Axiom0 bootstrap compiler tự build;
- cấu trúc test harness;
- cách AI agent chạy milestone tự động;
- và quan trọng nhất: **vertical slice đầu tiên phải đủ nhỏ để một agent có thể thực sự code từ đầu đến executable thay vì chỉ tạo skeleton.**