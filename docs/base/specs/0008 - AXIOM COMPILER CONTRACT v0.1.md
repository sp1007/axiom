Tiếp tục. Bây giờ nên đi vào phần **quan trọng nhất về mặt hiện thực hóa Axiom: Compiler Contract + MIR**.

Nếu Memory Model và Type System là “luật của ngôn ngữ”, thì MIR là nơi chứng minh rằng các luật đó có thể biến thành code máy **không cần runtime nặng và không cần LLVM làm semantic authority**.

# AXIOM COMPILER CONTRACT v0.1

**Trạng thái: PROPOSED**

## 1. Nguyên tắc lớn

Compiler Axiom phải tuân thủ:

> **Compiler được tự do thay đổi cách chương trình được thực thi, nhưng không được thay đổi observable semantics của chương trình.**

Nói cách khác:

```text
Source semantics
       │
       ▼
   Compiler
       │
       ├── inline
       ├── specialize
       ├── vectorize
       ├── eliminate allocation
       ├── reorder instructions
       ├── scalar replacement
       └── remove dead code
       │
       ▼
Machine code
```

Miễn là kết quả quan sát được vẫn đúng theo Axiom semantics.

---

# 2. Không dùng LLVM làm "bộ não"

Đây là quyết định tôi cho rằng nên **freeze**.

LLVM có thể được dùng:

```text
Bootstrap backend
Optional backend
Optimization backend
Development/debugging backend
```

nhưng:

```text
Axiom semantics
       ≠
LLVM semantics
```

Pipeline chính thức:

```text
Source
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
Verified MIR
  ↓
Optimization
  ↓
Axiom LIR
  ↓
Target Lowering
  ↓
Machine IR
  ↓
Register Allocation
  ↓
Instruction Encoding
  ↓
Object / Executable
```

LLVM có thể là:

```text
                    ┌── LLVM backend
Axiom LIR ──────────┼── Axiom x86 backend
                    ├── Axiom ARM64 backend
                    ├── Axiom RISC-V backend
                    └── Axiom WASM backend
```

---

# 3. Tại sao cần nhiều IR?

Không nên cố làm:

```text
AST → Machine Code
```

hoặc:

```text
AST → LLVM IR
```

vì Axiom có những semantics mà LLVM IR không biểu diễn trực tiếp:

```text
Move
Drop
Ownership
View
Mutable View
Send
Await
Spawn
Resource lifetime
Safe concurrency
```

Do đó cần một IR riêng.

---

# 4. AST

AST chỉ giữ syntax.

Ví dụ:

```axiom
user.name()
```

AST có thể là:

```text
Call
 ├── Receiver: user
 └── Method: name
```

AST **không phải optimization IR**.

---

# 5. HIR

HIR canonicalize syntax.

Ví dụ:

```axiom
user.name()
```

thành:

```axiom
name(user)
```

Nếu:

```axiom
a + b
```

thì HIR có thể biến thành:

```text
Add::add(a, b)
```

Như vậy compiler không cần một hệ thống đặc biệt cho method/operator.

---

# 6. Typed HIR

Sau type checking:

```text
name(user)
```

trở thành:

```text
name(
    user: User
) -> String
```

Compiler đã biết:

```text
User
String
trait implementation
generic instantiation
dispatch mode
```

---

# 7. MIR — trung tâm của compiler

Tôi đề xuất MIR của Axiom là:

> **Typed, explicit-control-flow, ownership-aware, SSA-oriented intermediate representation.**

Không nhất thiết pure SSA.

Đây là điểm quan trọng.

---

# 8. Vì sao không pure SSA?

SSA rất tốt cho:

```text
value
definition
use
optimization
```

nhưng ownership là một vấn đề khác.

Ví dụ:

```axiom
let file = open()

use(file)

return
```

Compiler cần biết:

```text
file
  │
  ├── owned
  │
  ├── passed
  │
  └── dropped
```

Đây không đơn thuần là data-flow.

Nó là:

```text
resource-flow
```

Do đó Axiom MIR nên có:

```text
SSA-like values
+
explicit ownership/resource state
```

---

# 9. MIR cơ bản

Ví dụ source:

```axiom
fn add(a: i32, b: i32) -> i32 {
    return a + b
}
```

MIR conceptual:

```text
fn add(a: i32, b: i32) -> i32

block0:
    v0 = Add(a, b)
    Return(v0)
```

---

# 10. Move

Source:

```axiom
let b = a
use(b)
```

nếu `a` non-Copy:

```text
v0 = MOVE a
use(v0)
```

Sau:

```text
a = MOVED
```

Compiler state:

```text
a : invalid
b : owned
```

Nếu:

```axiom
use(a)
```

thì:

```text
AX_MEM_0001
use of moved value
```

---

# 11. Copy

Nếu:

```axiom
let b = a
```

và `a : Copy`:

```text
v0 = COPY a
```

Hai value độc lập.

---

# 12. Drop elaboration

Source:

```axiom
fn test() {
    let a = open()
    let b = open()

    work()
}
```

MIR semantic:

```text
a = open()
b = open()

work()

DROP b
DROP a

RETURN
```

Reverse declaration order.

Compiler sau đó có thể tối ưu.

Ví dụ nếu:

```text
b
```

được compiler chứng minh không cần heap cleanup:

```text
DROP b
```

có thể biến thành no-op.

---

# 13. Drop không đồng nghĩa free()

Đây là điểm cần giữ rất rõ.

MIR:

```text
DROP x
```

nghĩa:

> thực hiện semantic destruction/resource release.

Nó không nhất thiết là:

```text
free(ptr)
```

Compiler có thể biết:

```text
x nằm inline
```

→ destructor code.

Hoặc:

```text
x heap allocated
```

→ destructor + deallocation.

Hoặc:

```text
allocation đã được eliminate
```

→ chẳng còn gì.

---

# 14. View trong MIR

Nếu:

```axiom
fn sum(data: view<i32>) -> i32
```

thì conceptual representation:

```text
VIEW
 ├── base
 └── length
```

Nhưng compiler có thể biến:

```text
view<i32>
```

thành:

```text
register pair
```

hoặc:

```text
pointer + integer
```

hoặc tối ưu hoàn toàn.

---

# 15. View lifetime

Ví dụ:

```axiom
fn bad() -> view<i32> {
    let data = [1, 2, 3]
    return data
}
```

MIR lifetime analysis thấy:

```text
data lifetime
[────────────]

return view
            ↑
            vượt owner lifetime
```

→ compile error.

Điểm quan trọng:

**Không cần programmer viết lifetime.**

Compiler tự tính.

---

# 16. Alias state

MIR cần internal state:

```text
OWN
READ
WRITE
MOVED
DROPPED
```

Ví dụ:

```text
x : OWN

create view(x)
```

sau đó:

```text
x : READ-BORROWED
```

Nếu:

```text
mutate(x)
```

trong khi view còn sống:

```text
ERROR
```

Sau khi compiler chứng minh view hết lifetime:

```text
x : OWN
```

lại mutable.

Đây là borrow checker **ẩn bên trong compiler**, không phải borrow syntax trong source.

---

# 17. Escape analysis

Axiom compiler phải có escape analysis ngay từ đầu.

Ví dụ:

```axiom
fn create() -> Buffer {
    let x = Buffer(100)
    return x
}
```

Không được mặc định:

```text
heap allocation
```

Compiler có thể:

```text
caller allocates result
        ↓
callee constructs directly there
```

tương đương:

```text
return value optimization
```

---

# 18. Allocation elimination

Ví dụ:

```axiom
fn distance(x: f32, y: f32) -> f32 {
    let p = Point(x, y)
    return sqrt(p.x*p.x + p.y*p.y)
}
```

Không có lý do phải allocate `Point`.

MIR:

```text
p.x
p.y
```

có thể được scalar-replaced:

```text
x
y
```

`Point` chưa bao giờ tồn tại trong memory.

Đây chính là lý do:

> **high-level abstraction không nhất thiết dẫn tới high-level runtime cost.**

---

# 19. Generic specialization

Source:

```axiom
fn max<T: Comparable>(a: T, b: T) -> T
```

Compiler có thể tạo:

```text
max<i32>
max<f64>
max<MyType>
```

MIR sau specialization không còn generic abstraction nếu không cần.

Sau đó:

```text
inline
constant propagation
dead code elimination
```

có thể biến nó thành machine code rất nhỏ.

---

# 20. Trait dispatch

Static dispatch:

```axiom
fn draw<T: Drawable>(x: T)
```

với:

```text
T = Circle
```

compiler biết implementation:

```text
Circle::draw
```

→ direct call hoặc inline.

Không cần:

```text
vtable lookup
```

---

# 21. Dynamic dispatch

Nếu programmer thực sự yêu cầu dynamic abstraction:

```text
dyn Drawable
```

thì compiler có thể tạo conceptual:

```text
data pointer
dispatch pointer
```

Dynamic dispatch **phải là explicit semantic boundary**.

Như vậy:

```text
static dispatch
```

không bị biến thành virtual call ngầm.

---

# 22. MIR concurrency

MIR phải có semantic operations:

```text
SPAWN
AWAIT
SUSPEND
RESUME
SEND
RECEIVE
ATOMIC_LOAD
ATOMIC_STORE
ATOMIC_RMW
CAS
LOCK
UNLOCK
```

Nhưng sau lowering:

```text
SPAWN
```

có thể trở thành library call.

MIR vẫn cần biết semantics để kiểm tra ownership.

---

# 23. Async MIR

Ví dụ:

```axiom
async fn foo() {
    let a = load()
    await io()
    use(a)
}
```

MIR:

```text
block0:
    a = load()
    SUSPEND point_1

block1:
    use(a)
    RETURN
```

Compiler phân tích:

```text
a live across suspension
```

sau đó state machine lowering:

```text
State {
    state_id
    a
}
```

---

# 24. Spawn + ownership

Source:

```axiom
spawn {
    consume(buffer)
}
```

MIR:

```text
closure_env = MOVE(buffer)

SPAWN closure_env
```

Compiler kiểm tra:

```text
buffer : Send
```

Nếu không:

```text
AX_CON_0007
value is not Send across concurrency boundary
```

---

# 25. Verified MIR

Tôi đề xuất có một checkpoint cực kỳ quan trọng:

```text
MIR
 ↓
Ownership analysis
 ↓
Lifetime/escape analysis
 ↓
Concurrency analysis
 ↓
Drop verification
 ↓
Type invariants
 ↓
VERIFIED MIR
```

Sau khi đã có:

```text
Verified MIR
```

optimizer không được phá semantic invariant.

Đây là một architecture rất có giá trị cho Axiom.

---

# 26. Vì sao checkpoint này quan trọng?

Nó cho phép tách:

```text
Semantic compiler
```

khỏi:

```text
Optimization compiler
```

Ví dụ:

```text
                 ┌───────────────┐
Source ─────────►│ Semantic Core │
                 └───────┬───────┘
                         │
                  Verified MIR
                         │
                 ┌───────▼───────┐
                 │  Optimizer     │
                 └───────┬───────┘
                         │
                     Axiom LIR
```

Nếu optimizer có bug:

```text
semantic correctness
```

vẫn được bảo vệ về mặt kiến trúc.

---

# 27. Axiom LIR

Sau Verified MIR, ownership không còn là concern chính.

LIR gần machine hơn:

```text
vreg1 = ADD vreg2, vreg3
LOAD vreg4, [vreg5 + 8]
STORE [vreg6], vreg7
CALL foo
BRANCH block3
RETURN vreg1
```

LIR nên target-neutral.

---

# 28. Machine IR

Ví dụ x86-64:

```text
RAX
RBX
RCX
RDX
XMM0
...
```

ARM64:

```text
X0
X1
X2
...
V0
V1
...
```

RISC-V:

```text
X0...
F0...
```

Backend xử lý:

```text
instruction selection
register allocation
calling convention
stack frame
ABI
relocation
encoding
```

---

# 29. Object generation

Axiom compiler cuối cùng phải tự tạo:

```text
ELF
PE/COFF
Mach-O
WASM
```

Không bắt buộc:

```text
gcc
clang
MSVC
```

ở final self-hosted compiler.

Nhưng bootstrap có thể dùng chúng.

---

# 30. Runtime-free contract

Một chương trình:

```axiom
fn main() {
    return
}
```

không nên tự động kéo theo:

```text
GC
thread runtime
async runtime
reflection runtime
exception runtime
metadata registry
```

Nếu target cần startup code tối thiểu:

```text
_start
```

thì compiler/linker tự tạo phần cần thiết.

---

# 31. Runtime components phải được link theo nhu cầu

Ví dụ chương trình:

```text
math only
```

→ binary rất nhỏ.

Chương trình:

```text
async + networking
```

→ chỉ link runtime/library cần thiết.

Chương trình:

```text
GUI
```

→ kéo GUI subsystem.

Không phải:

```text
Axiom program
    ↓
full Axiom runtime
    ↓
50 MB
```

---

# 32. Compiler diagnostics

Axiom compiler nên coi diagnostics như một API ổn định.

Ví dụ:

```text
AX_TYPE_0012
TYPE_MISMATCH

expected: i32
found: String

location:
main.ax:14:9

cause:
argument 2 of `add` requires i32
```

AI agent có thể đọc structured JSON:

```json
{
  "code": "AX_TYPE_0012",
  "severity": "error",
  "phase": "type-check",
  "expected": "i32",
  "found": "String",
  "file": "main.ax",
  "line": 14,
  "column": 9
}
```

Human đọc text.

Agent đọc JSON.

Compiler vẫn deterministic.

---

# 33. Không cho AI tham gia semantic compilation

Axiom có thể có:

```text
AI coding assistant
AI refactoring
AI optimization suggestions
AI diagnostics explanation
```

nhưng:

```text
AI
 ↓
compiler semantics
```

**không được phép**.

Compiler phải deterministic:

```text
same source
+ same compiler version
+ same target
+ same flags
=
same semantic result
```

Điều này cực kỳ quan trọng nếu Axiom được xây dựng bằng AI agents.

---

# 34. Compiler Contract invariants

Tôi đề xuất:

```text
ACC-01
Compiler must preserve observable program semantics.

ACC-02
Compiler optimization must not introduce observable ownership violations.

ACC-03
Verified MIR is the semantic correctness boundary.

ACC-04
Ownership/lifetime/concurrency validation occurs before unrestricted optimization.

ACC-05
Compiler may eliminate storage when semantics permit.

ACC-06
Compiler may specialize generic code.

ACC-07
Compiler may inline statically dispatched functions.

ACC-08
Compiler may eliminate temporary values and allocations.

ACC-09
Compiler must preserve deterministic destruction.

ACC-10
Compiler must preserve atomic and synchronization semantics.

ACC-11
Compiler semantics must not depend on LLVM.

ACC-12
External compiler toolchains may be used only as bootstrap/optional backends.

ACC-13
Axiom programs do not implicitly require a universal runtime.

ACC-14
Compiler diagnostics have stable machine-readable identities.

ACC-15
Semantic compilation is deterministic and does not depend on AI.
```

---

# 35. Bây giờ kiến trúc Axiom đã khá hoàn chỉnh

Ta có:

```text
                 AXIOM LANGUAGE
                       │
        ┌──────────────┼──────────────┐
        │              │              │
       CORE          MEMORY          TYPE
        │              │              │
        └──────────────┼──────────────┘
                       │
                 CONCURRENCY
                       │
                       ▼
                    AST
                       │
                       ▼
                    HIR
                       │
                       ▼
                 TYPED HIR
                       │
                       ▼
                     MIR
                       │
           ┌───────────┼───────────┐
           │           │           │
       Ownership    Lifetime    Concurrency
           │           │           │
           └───────────┼───────────┘
                       ▼
                VERIFIED MIR
                       │
                       ▼
                  OPTIMIZER
                       │
                       ▼
                   AXIOM LIR
                       │
                       ▼
                TARGET LOWERING
                       │
                       ▼
                 MACHINE IR
                       │
                       ▼
               REGISTER ALLOC
                       │
                       ▼
                MACHINE CODE
                       │
          ┌────────────┼────────────┐
          ▼            ▼            ▼
         ELF          PE          Mach-O
```

### Và đây là điểm tôi đánh giá rất quan trọng:

**Chúng ta đã tránh được hai cực đoan.**

Một bên là:

```text
C
→ đơn giản nhưng compiler gần như không có semantic information
```

Bên kia:

```text
Rust
→ compiler có rất nhiều semantic information
→ programmer phải biểu đạt quá nhiều trong source
```

Axiom đang hướng tới:

```text
Axiom
→ compiler biết rất nhiều
→ programmer phải viết tương đối ít
→ machine code vẫn có thể rất thấp-level
```

Đó mới là hướng đáng theo đuổi.

---

## Bước tiếp theo: ABI + Layout + Calling Convention

Tôi đề xuất **chưa nhảy sang standard library**.

Trước tiên cần khóa:

**`AXIOM ABI & DATA LAYOUT v0.1`**

vì nó sẽ quyết định trực tiếp:

- `struct` nằm trong memory như thế nào
- `Array<T,N>`
- `view<T>`
- `Option<T>`
- `Result<T,E>`
- enum representation
- alignment/padding
- register passing
- return-value optimization
- FFI với C
- binary compatibility
- dynamic library
- function pointer
- trait object
- SIMD/vector types
- atomic layout
- `repr(C)` và native layout
- stack frame
- calling convention

Đặc biệt, đây là nơi ta sẽ trả lời chính xác câu hỏi trước đây của bạn về **"flat memory có thực sự nhanh hơn không?"**: không chỉ nhìn abstraction, mà phải thiết kế **layout + allocator + cache locality + ownership + escape analysis** cùng nhau.