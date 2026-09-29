Tiếp tục. Sau khi chốt `view / invalidation / partial Drop / effect summary`, tôi nghĩ **không nên thêm tính năng ngôn ngữ** nữa. Ta nên chuyển sang một tầng quan trọng hơn:

# AXIOM SEMANTIC STRESS TEST v0.1

Mục tiêu là tìm xem semantics hiện tại có lỗ hổng trước khi biến nó thành compiler.

Tôi sẽ thiết kế bộ test theo kiểu **compiler conformance**, không phải test syntax đơn thuần.

---

# 1. Cấu trúc mỗi test

Mỗi test phải có 5 lớp:

```text
SOURCE
   ↓
EXPECTED HIR
   ↓
EXPECTED MIR PROPERTY
   ↓
VERIFIER RESULT
   ↓
EXPECTED DIAGNOSTIC
```

Không yêu cầu MIR giống 100% từng dòng.

Ví dụ:

```text
TEST: OWN_BRANCH_001

SOURCE:
    fn test(x: Buffer<u8>, flag: bool) {
        if flag {
            consume(x)
        }
        use(x)
    }

EXPECTED:
    REJECT

REASON:
    x may be MOVED at control-flow join

MIR PROPERTY:
    branch contains MOVE(x)
    join state = MAYBE_MOVED

DIAGNOSTIC:
    AX_OWN_0001
```

Điều này giúp compiler có thể tối ưu MIR mà test vẫn không bị vỡ.

---

# 2. Nhóm A — Ownership cơ bản

### A001 — move

```axiom
let a = Buffer.new()
let b = a
use(a)
```

→ REJECT.

---

### A002 — move twice

```axiom
let a = Buffer.new()
let b = a
let c = a
```

→ REJECT.

---

### A003 — return ownership

```axiom
fn make() -> Buffer<u8> {
    let x = Buffer.new()
    x
}
```

→ ACCEPT.

Ownership:

```text
local x
   ↓
RETURN
   ↓
caller owns
```

---

### A004 — move into function

```axiom
consume(x)
use(x)
```

→ REJECT.

---

### A005 — Copy

```axiom
let a: i32 = 10
let b = a
use(a)
```

→ ACCEPT.

---

# 3. Nhóm B — Partial Move

### B001

```axiom
struct User {
    name: String
    age: i32
}

let name = user.name
use(user.age)
```

→ ACCEPT.

---

### B002

```axiom
let name = user.name
use(user)
```

→ REJECT.

---

### B003

```axiom
let name = user.name
let name2 = user.name
```

→ REJECT.

---

### B004 — field-independent mutation

```axiom
let name = user.name
user.age = 20
```

→ ACCEPT.

---

### B005 — Drop

```axiom
struct Data {
    a: Buffer<u8>
    b: Buffer<u8>
}

let a = x.a
```

Cuối scope:

```text
DROP a
DROP x.b
```

không được:

```text
DROP x
```

---

# 4. Nhóm C — Branch

Đây là nhóm rất quan trọng.

### C001

```text
if flag:
    MOVE x

use x
```

→ REJECT.

---

### C002

```text
if flag:
    MOVE x
else:
    MOVE x
```

→ ACCEPT.

Sau join:

```text
MOVED + MOVED = MOVED
```

---

### C003

```text
if flag:
    MOVE x
else:
    REINIT x

use x
```

→ REJECT.

Vì:

```text
MOVED + OWNED
= MAYBE_OWNED
```

---

### C004

```text
if flag:
    MOVE x
    return

use x
```

→ ACCEPT.

Đây là test quan trọng.

Nhánh move không quay lại JOIN.

CFG:

```text
       flag
      /    \
   MOVE     continue
     │         │
   RETURN      │
               ▼
             use x
```

Nhánh `MOVE` đã kết thúc control flow.

---

# 5. Nhóm D — Loop

### D001

```text
while condition {
    consume(x)
}
```

→ REJECT.

---

### D002

```text
while condition {
    consume(x)
    x = Buffer.new()
}
```

→ ACCEPT.

---

### D003

```text
while condition {
    let y = x
    consume(y)
}
```

Nếu `x` không Copy:

→ REJECT ngay iteration đầu.

---

### D004

```text
while condition {
    let y = view(x)
    use(y)
}
```

→ ACCEPT.

`y` hết lifetime sau last-use mỗi iteration.

---

# 6. Nhóm E — Views

### E001

```text
let v = view(x)
read(v)
```

→ ACCEPT.

---

### E002

```text
let v = view(x)
mutate(x)
```

→ REJECT nếu `v` còn live.

---

### E003

```text
let v = view(x)
read(v)
mutate(x)
```

→ ACCEPT.

Vì:

```text
read(v)
 ↓
LAST_USE(v)
 ↓
capability kết thúc
 ↓
mutate(x)
```

Đây là một test **rất quan trọng** cho Axiom ergonomics.

---

# 7. Nhóm F — Disjoint regions

```axiom
struct Point {
    x: i32
    y: i32
}
```

### F001

```text
let a = mut_view(p.x)
let b = mut_view(p.y)
```

→ ACCEPT.

---

### F002

```text
let a = mut_view(p)
let b = mut_view(p.x)
```

→ REJECT.

---

### F003

```text
let a = view(p.x)
let b = mut_view(p.y)
```

→ ACCEPT.

---

### F004

```text
let a = view(p)
let b = mut_view(p.x)
```

→ REJECT.

---

# 8. Nhóm G — Unknown regions

Đây là nơi compiler phải **conservative nhưng không quá ngu ngốc**.

```axiom
fn mutate_unknown(x: mut_view<Person>)
```

Nếu compiler không biết field nào được sửa:

```text
WRITE(x)
```

thì:

```axiom
let v = view(p.age)
mutate_unknown(mut_view(p))
use(v)
```

→ REJECT.

Nhưng nếu contract nói:

```text
WRITE(arg0.name)
```

thì:

```text
READ(p.age)
WRITE(p.name)
```

→ ACCEPT.

---

# 9. Nhóm H — Vec invalidation

### H001

```text
let v = view(vec)
vec.push(x)
use(v)
```

Nếu `push` có `MAY_REALLOCATE`:

→ REJECT.

---

### H002

```text
let v = view(vec)
vec.push_no_grow(x)
use(v)
```

Nếu contract bảo đảm không realloc và vùng logical không conflict:

→ ACCEPT.

---

### H003

```text
let v = view(vec)
vec.clear()
use(v)
```

→ REJECT.

Không cần realloc.

Logical region đã mất.

---

# 10. Nhóm I — Closure

### I001

```text
fn make(x: Buffer<u8>) -> Task {
    || use(x)
}
```

→ ACCEPT bằng ownership capture.

---

### I002

```text
fn make(x: Buffer<u8>) -> Task {
    let v = view(x)
    || use(v)
}
```

→ REJECT nếu closure escape khỏi lifetime của `x`.

---

### I003

```text
fn run(x: Buffer<u8>) {
    let v = view(x)

    let f = || use(v)

    f()
}
```

→ ACCEPT.

Closure không escape.

---

# 11. Nhóm J — Async

### J001

```text
async fn f(x: Buffer<u8>) {
    await something()
    use(x)
}
```

→ ACCEPT.

`x` nằm trong logical async state.

---

### J002

```text
spawn(f(x))
```

Nếu frame là `Send`:

→ ACCEPT.

---

### J003

```text
spawn(f(non_send_value))
```

→ REJECT.

---

### J004

```text
spawn_local(f(non_send_value))
```

→ ACCEPT nếu executor contract bảo đảm local execution.

---

# 12. Nhóm K — FFI

### K001

```text
let v = view(x)
external(x)
use(v)
```

Nếu `external` không có effect contract:

→ conservative reject / invalidation.

---

### K002

Nếu:

```text
@ffi_effects(read(arg0))
```

thì:

```text
let v = view(x)
external(x)
use(v)
```

→ ACCEPT.

---

### K003

Nếu:

```text
@ffi_effects(write(arg0))
```

thì view READ đang sống:

→ conflict.

---

# 13. Nhóm L — Unsafe

Ví dụ:

```axiom
let v = view(x)

unsafe {
    raw_write(address_of(x))
}

use(v)
```

Compiler không được giả định raw write không ảnh hưởng `x`.

Tùy semantics của unsafe boundary:

```text
unsafe raw memory operation
        ↓
UNKNOWN_MEMORY_EFFECT
        ↓
invalidate affected capabilities
```

→ có thể REJECT.

Nhưng **unsafe không có nghĩa là toàn bộ function trở thành untyped**.

---

# 14. Nhóm M — Function effects

Compiler phải suy luận:

```axiom
fn A(x: view<Data>) {
    B(x)
}

fn B(x: view<Data>) {
    C(x)
}

fn C(x: view<Data>) {
    read(x)
}
```

Kết quả:

```text
A:
    READ(arg0)

B:
    READ(arg0)

C:
    READ(arg0)
```

---

# 15. Effect propagation

```axiom
fn A(x: mut_view<Data>) {
    B(x)
    C(x)
}
```

Nếu:

```text
B → WRITE(arg0.a)
C → WRITE(arg0.b)
```

thì:

```text
A:
    WRITE(arg0.a)
    WRITE(arg0.b)
```

Compiler có thể chứng minh hai vùng disjoint.

---

# 16. Recursive effects

```axiom
fn A(x) {
    B(x)
}

fn B(x) {
    A(x)
}
```

Compiler phải terminate.

Không được:

```text
A → B → A → B → ...
```

Phải dùng:

```text
SCC / fixed-point analysis
```

---

# 17. Nhóm N — Drop observability

Đây là test cho optimizer.

```axiom
{
    let x = Trivial {}
}
```

Nếu:

```text
Drop(Trivial)
```

không observable:

```text
DROP
 ↓
eliminate
```

→ OK.

Nhưng:

```axiom
{
    let f = File.open(...)
}
```

Nếu Drop flush/close observable:

```text
DROP
 ↓
RESOURCE_RELEASE
 ↓
MUST PRESERVE
```

---

# 18. Nhóm O — Evaluation order

Axiom đã định hướng:

> **Evaluation order = left-to-right.**

Ví dụ:

```axiom
f(g(), h())
```

phải:

```text
g()
 ↓
h()
 ↓
f()
```

Không được optimizer biến thành:

```text
h()
 ↓
g()
```

nếu observable effect khác nhau.

Đây là một semantic invariant cực kỳ quan trọng vì compiler optimizer về sau sẽ rất mạnh.

---

# 19. Một vấn đề lớn vừa lộ ra

Sau khi xây stress test, tôi thấy cần bổ sung một khái niệm vào verifier:

# `CAPABILITY`

Thay vì chỉ có:

```text
OWNERSHIP
ACCESS
REGION
```

ta có:

```text
Capability {
    owner
    region
    mode
    provenance
    validity
}
```

Ví dụ:

```text
v = view(p.name)
```

sinh:

```text
Capability {
    owner      = p
    region     = p.name
    mode       = READ
    provenance = p
    validity   = ACTIVE
}
```

`mut_view(p.name)`:

```text
Capability {
    owner      = p
    region     = p.name
    mode       = WRITE
    provenance = p
    validity   = ACTIVE
}
```

Khi:

```text
use(v)
```

sau last-use:

```text
validity = ENDED
```

Khi `p` bị drop:

```text
validity = INVALIDATED
```

---

# 20. Đây có thể là abstraction trung tâm của verifier

Thay vì compiler phải nghĩ:

> “Đây có phải borrow không?”

nó chỉ nghĩ:

> “Capability nào đang tồn tại, trên region nào, với quyền gì?”

```text
              Capability
                   │
        ┌──────────┼──────────┐
        ▼          ▼          ▼
     READ       WRITE        OWN
        │          │          │
        ▼          ▼          ▼
      view      mut_view     value
```

Điều này cũng mở đường cho:

```text
READ capability
WRITE capability
MOVE capability
ATOMIC capability
VOLATILE capability
FFI capability
```

mà không cần biến tất cả thành syntax của language.

---

# 21. Và đây là điểm rất mạnh cho tương lai

Axiom có thể dùng cùng mô hình capability cho:

```text
memory
GPU buffer
network buffer
file mapping
shared memory
MMIO
DMA
```

Ví dụ về sau:

```text
GPUView<T>
```

vẫn có thể có:

```text
region
access
provenance
validity
```

nhưng semantics domain-specific nằm ở library/compiler extension.

**Không cần biến mọi thứ thành core language.**

---

# 22. Tôi đề xuất thêm AOV-16 → AOV-22

```text
AOV-16
Every non-owning access capability has provenance.

AOV-17
Every capability refers to a semantic memory region.

AOV-18
Capability validity ends at semantic last-use when no later
observation depends on it.

AOV-19
A capability is invalidated when its provenance storage or
logical region becomes invalid.

AOV-20
Capability conflict is determined by access mode + region relation,
not variable identity alone.

AOV-21
Unknown memory effects are conservative at semantic boundaries.

AOV-22
Capability tracking itself introduces no required runtime metadata.
```

Invariant cuối cực kỳ quan trọng.

Axiom **không biến capability thành runtime object**.

Nó chỉ là compiler analysis.

---

# 23. Đến đây architecture đã khá hoàn chỉnh

Ta có thể nhìn toàn bộ hệ thống:

```text
                    AXIOM SOURCE
                         │
                         ▼
                       AST
                         │
                         ▼
                       HIR
                         │
                  type resolution
                         │
                         ▼
                    TYPED HIR
                         │
                         ▼
                        MIR
                         │
          ┌──────────────┼──────────────┐
          │              │              │
          ▼              ▼              ▼
      Ownership      Capability       Effects
      Analysis        Analysis        Analysis
          │              │              │
          └──────────────┼──────────────┘
                         ▼
                     VERIFIER
                         │
                ┌────────┴────────┐
                │                 │
              REJECT           VERIFIED
                │                 │
                ▼                 ▼
           Diagnostics        Optimization
                                  │
                                  ▼
                                LIR
                                  │
                                  ▼
                             Machine IR
                                  │
                                  ▼
                            Native Binary
```

---

# 24. Và đây chính là thời điểm chuyển sang compiler

Tôi nghĩ từ đây không nên tiếp tục “vẽ” semantics vô hạn.

**Bước tiếp theo nên là thiết kế HIR và MIR thành specification có thể code được.**

Cụ thể:

### Phase 1 — HIR

Định nghĩa chính xác AST/HIR node:

```text
Module
Function
Struct
Enum
Trait
Impl
Type
Expr
Stmt
Pattern
Place
```

và type resolution.

### Phase 2 — MIR

Định nghĩa:

```text
BasicBlock
Local
Value
Place
Region
Capability
Instruction
Terminator
```

### Phase 3 — Verifier

Viết algorithm thực:

```text
CFG
 ↓
dataflow
 ↓
ownership state
 ↓
capability state
 ↓
region relation
 ↓
effect propagation
 ↓
cleanup verification
 ↓
Verified MIR
```

### Phase 4 — Interpreter

Đây là thứ tôi đặc biệt khuyến nghị.

Trước khi có x86/ARM backend:

```text
Axiom Source
     ↓
MIR
     ↓
MIR Interpreter
```

Nếu 150+ adversarial tests chạy đúng trên MIR interpreter, chúng ta có một **semantic reference implementation**.

Sau đó:

```text
MIR
 ├── Interpreter
 ├── x86-64 backend
 ├── ARM64 backend
 ├── RISC-V backend
 └── WASM backend
```

Đây sẽ giúp Axiom tránh một lỗi rất phổ biến của compiler tự xây: **backend vô tình trở thành nơi định nghĩa semantics**.

---

## Tôi đề xuất thứ tự từ đây

```text
[ĐÃ CÓ]
Semantic Core
      ↓
Memory Model
      ↓
Type System
      ↓
Concurrency
      ↓
Ownership Verifier
      ↓
View / Drop / Effects
      ↓
────────────────────────
      ↓
[TIẾP THEO]

HIR Specification
      ↓
MIR Specification
      ↓
MIR Verifier Specification
      ↓
MIR Interpreter
      ↓
Conformance Suite
      ↓
x86-64 Backend
      ↓
ARM64 Backend
      ↓
Self-hosting Compiler
```

**Bước tiếp theo tôi sẽ đi thẳng vào `AXIOM HIR v0.1`**, thiết kế từng node, invariants, lowering rules và ví dụ `Source → AST → HIR`. Đây là nền móng để sau đó AI agent có thể bắt đầu viết compiler thật thay vì tiếp tục tranh luận abstract về ngôn ngữ.