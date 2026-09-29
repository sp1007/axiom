Tiếp theo ta đi vào phần quan trọng nhất của compiler: **AXIOM MIR v0.1**.

Tôi muốn thiết kế MIR theo hướng **không chỉ là IR để generate machine code**, mà là **semantic checkpoint**: nếu một chương trình đã đi qua `Verified MIR`, backend không được phép thay đổi semantics.

---

# AXIOM MIR v0.1

## 1. Vai trò của MIR

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
MIR Lowering
  ↓
Ownership / Capability / Effect Verification
  ↓
Verified MIR
  ↓
Optimization
  ↓
Axiom LIR
  ↓
Machine IR
  ↓
Native Code
```

MIR nằm đúng giữa:

```text
high-level semantics
        │
        ▼
      MIR
        │
        ▼
machine-oriented representation
```

Nó phải đủ thấp để:

- biểu diễn control flow rõ ràng
- biểu diễn ownership rõ ràng
- biểu diễn resource lifetime
- biểu diễn async
- biểu diễn atomic
- dễ optimize

nhưng chưa được chứa:

- x86 register
- ARM register
- stack offset
- ABI-specific register allocation
- instruction scheduling

---

# 2. MIR có 5 thành phần chính

```text
MIRFunction
├── Locals
├── Values
├── Places
├── BasicBlocks
└── Metadata
```

Trong đó:

```text
Values      = dữ liệu SSA
Places      = vị trí lưu trữ
Locals      = logical storage
BasicBlocks = control flow
Metadata    = type/source/debug/effect
```

---

# 3. Local

Ví dụ:

```axiom id="q3x0cb"
fn add(a: i32, b: i32) -> i32
```

MIR:

```text
Local 0 = a : i32
Local 1 = b : i32
```

Local là **logical variable**, không phải stack slot.

Compiler có thể biến:

```text
Local 0
```

thành:

```text
register
stack
constant
nothing
```

sau optimization.

---

# 4. SSA Value

Ví dụ:

```axiom id="aqe4tv"
let x = a + b
```

MIR:

```text
%v0 = LOAD a
%v1 = LOAD b
%v2 = ADD %v0, %v1
```

`%v2` là SSA value.

Mỗi SSA value chỉ được định nghĩa một lần.

---

# 5. Nhưng ownership không nên nhét vào SSA

Đây là quyết định kiến trúc rất quan trọng.

Không nên làm:

```text
SSA value = ownership state
```

Vì một resource có thể:

```text
move
drop
partial move
branch
reinitialize
```

mà SSA value semantics không diễn đạt tự nhiên.

Do đó:

```text
SSA graph
    +
Ownership graph
```

tách biệt.

```text
MIR
├── value SSA
└── resource ownership
```

---

# 6. Place

Place đại diện cho storage location.

```text
Place
├── Local
├── Field
├── Index
└── Deref
```

Ví dụ:

```axiom id="bh3yfp"
p.name
```

MIR:

```text
%p_name = FIELD_PLACE %p, name
```

Chưa đọc dữ liệu.

Muốn đọc:

```text
%name = LOAD %p_name
```

Muốn ghi:

```text
STORE %p_name, %value
```

---

# 7. Tại sao phải tách Place và Value?

Ví dụ:

```axiom id="3d5e2s"
p.age = 20
```

Ta cần biết:

```text
p.age
```

là **vị trí** chứ không phải giá trị.

MIR:

```text
%place0 = FIELD_PLACE %p, age
STORE %place0, 20
```

Ownership verifier có thể kiểm tra:

```text
WRITE(region(p.age))
```

rất trực tiếp.

---

# 8. Place projection

Một place có thể được xây từ place khác:

```text
p
 ↓
FIELD(name)
 ↓
INDEX(...)
 ↓
DEREF
```

Ví dụ:

```axiom id="75f4nz"
matrix[row].x
```

Conceptual MIR:

```text
%p1 = FIELD_PLACE matrix, row
%p2 = INDEX_PLACE %p1, row
%p3 = FIELD_PLACE %p2, x
```

Region engine có thể suy ra:

```text
region(matrix[row].x)
```

---

# 9. BasicBlock

Mỗi BasicBlock:

```text
BasicBlock {
    instructions[]
    terminator
}
```

Ví dụ:

```text
bb0:
    ...
    BRANCH cond, bb1, bb2

bb1:
    ...
    JUMP bb3

bb2:
    ...
    JUMP bb3

bb3:
    ...
    RETURN
```

MIR không chứa structured `if`.

---

# 10. Terminator

Terminator kết thúc BasicBlock.

Core:

```text
JUMP
BRANCH
SWITCH
RETURN
PANIC
TRAP
UNREACHABLE
```

Async:

```text
SUSPEND
```

Không có instruction nào nằm sau terminator.

Invariant:

```text
MIR-CFG-01:
Every basic block has exactly one terminator.
```

---

# 11. `if`

Source:

```axiom id="t8y4zx"
if flag {
    foo()
} else {
    bar()
}
```

MIR:

```text
bb0:
    %c = LOAD flag
    BRANCH %c, bb1, bb2

bb1:
    CALL foo
    JUMP bb3

bb2:
    CALL bar
    JUMP bb3

bb3:
    RETURN
```

Đây là CFG thực.

---

# 12. `match`

Source:

```axiom id="96n1bx"
match x {
    A => foo()
    B => bar()
    C => baz()
}
```

MIR:

```text
bb0:
    %tag = ENUM_TAG x
    SWITCH %tag:
        A → bb1
        B → bb2
        C → bb3

bb1:
    CALL foo
    JUMP bb4

bb2:
    CALL bar
    JUMP bb4

bb3:
    CALL baz
    JUMP bb4

bb4:
    RETURN
```

Nếu payload:

```text
A(value)
```

thì branch block extract payload:

```text
%v = ENUM_PAYLOAD x, A, 0
```

---

# 13. Phi

Ví dụ:

```axiom id="5v1qg0"
let x =
    if flag { 10 }
    else { 20 }
```

MIR:

```text
bb1:
    %a = CONST 10
    JUMP bb3

bb2:
    %b = CONST 20
    JUMP bb3

bb3:
    %x = PHI(
        bb1 → %a,
        bb2 → %b
    )
```

`PHI` chỉ quản lý **value flow**.

Ownership flow vẫn do verifier theo dõi riêng.

---

# 14. Move

Source:

```axiom id="9o6p7a"
consume(x)
```

Nếu `consume` nhận ownership:

```text
MOVE x → arg0
CALL consume
```

`MOVE` không nhất thiết copy bytes.

Semantics:

```text
x:
OWNED
 ↓
MOVE
 ↓
MOVED
```

Physical lowering có thể:

```text
register transfer
pointer transfer
memcpy
nothing
```

tùy type.

---

# 15. Copy

```text
COPY x → v0
```

Chỉ hợp lệ nếu:

```text
Copy(T) = true
```

Sau:

```text
x = OWNED
v0 = independent value
```

không có ownership transfer.

---

# 16. LOAD / STORE

```text
LOAD place
STORE place, value
```

`LOAD`:

```text
READ(region(place))
```

`STORE`:

```text
WRITE(region(place))
```

Verifier sử dụng Place → Region mapping.

---

# 17. Field

Không nên có `FIELD` vừa tạo place vừa load.

Tách:

```text
FIELD_PLACE
```

Ví dụ:

```text
%p_name = FIELD_PLACE %p, name
```

Sau đó:

```text
%name = LOAD %p_name
```

Điều này giúp:

```text
p.name = ...
```

và:

```text
use(p.name)
```

cùng dùng một representation.

---

# 18. Index

```text
%element = INDEX_PLACE %array, %i
```

Index có semantic requirement:

```text
0 <= i < length
```

Nếu compiler chưa chứng minh được:

```text
BOUNDS_CHECK
```

phải tồn tại trước access.

Ví dụ:

```text
%ok = BOUNDS_CHECK %i, %len
%p  = INDEX_PLACE %array, %i
%v  = LOAD %p
```

Optimizer có thể xóa `BOUNDS_CHECK` nếu proof tồn tại.

---

# 19. View

Source:

```axiom id="w2x6cz"
let v = view(x)
```

MIR:

```text
%v = VIEW %x
```

Semantic metadata:

```text
Capability:
    mode       = READ
    provenance = x
    region     = region(x)
```

Không có nghĩa runtime phải tạo object.

Có thể cuối cùng thành:

```text
pointer + length
```

hoặc chỉ pointer.

---

# 20. Mutable view

```text
%v = VIEW_MUT %x
```

Capability:

```text
mode = WRITE
```

Verifier đảm bảo exclusive access.

---

# 21. View từ field

```axiom id="s4f2nm"
let v = view(person.name)
```

MIR:

```text
%p1 = FIELD_PLACE person, name
%v  = VIEW %p1
```

Region:

```text
region(person.name)
```

chứ không phải toàn `person`.

Đây là thứ cho phép:

```text
view(person.name)
mut_view(person.age)
```

cùng tồn tại.

---

# 22. ALLOC / DEALLOC

Ta vẫn giữ:

```text
ALLOC
DEALLOC
```

nhưng cần nhấn mạnh:

> `ALLOC` là **semantic storage operation**, không phải lời gọi `malloc`.

Ví dụ:

```text
%storage = ALLOC type=Buffer<u8>
```

Optimizer có thể biến:

```text
ALLOC
...
DEALLOC
```

thành:

```text
stack allocation
```

hoặc loại bỏ hoàn toàn.

---

# 23. DROP

MIR:

```text
DROP x
```

nhưng trước verifier, đây là semantic resource operation.

Sau Drop elaboration có thể:

```text
DROP x
```

hoặc:

```text
CALL File.close_internal
```

hoặc:

```text
nothing
```

nếu resource không có observable cleanup.

---

# 24. DROP_IF_OWNED

Đây là instruction **nội bộ sau partial initialization**.

Ví dụ:

```text
if condition {
    x = Buffer.new()
}
```

Tại cleanup:

```text
DROP_IF_OWNED x
```

Không phải language instruction.

Nó chỉ là compiler-generated cleanup primitive.

---

# 25. Partial move trong MIR

Ví dụ:

```axiom id="f7n0s2"
let name = user.name
```

MIR:

```text
%p = FIELD_PLACE user, name
%name = MOVE %p
```

Ownership:

```text
user.name = MOVED
user.age  = OWNED
```

Không cần biến `user` thành một physical copy.

---

# 26. Reinitialization

```axiom id="o9m4r2"
user.name = String("new")
```

MIR:

```text
%p = FIELD_PLACE user, name
%v = String.new(...)
STORE %p, %v
```

Verifier:

```text
user.name:
MOVED
 ↓
STORE
 ↓
OWNED
```

Do đó:

```axiom id="q3p8z1"
user.name = new_name
use(user)
```

có thể hợp lệ nếu mọi field khác vẫn owned.

---

# 27. CALL

MIR call:

```text
CALL {
    function
    args[]
    result?
}
```

Nhưng mỗi argument phải có semantic mode:

```text
Arg {
    value
    mode
}
```

Ví dụ:

```text
CALL consume(
    arg0 = x,
    mode = MOVE
)
```

hoặc:

```text
CALL read(
    arg0 = x,
    mode = READ
)
```

---

# 28. Effect của CALL

Verifier lấy effect summary của callee.

Ví dụ:

```text
CALL foo(x)
```

foo có:

```text
READ(arg0.data)
WRITE(arg0.flags)
```

thì MIR verifier map:

```text
arg0 → x
```

và tạo:

```text
READ(x.data)
WRITE(x.flags)
```

Nếu foo là unknown:

```text
UNKNOWN_CALL
```

→ conservative effects.

---

# 29. Dynamic call

```text
DYNAMIC_CALL {
    receiver
    dispatch
    args
}
```

Chỉ xuất hiện khi source semantics yêu cầu dynamic dispatch.

Không có chuyện:

```text
compiler không biết type
→ tự động dynamic dispatch
```

Nếu type không resolve được:

```text
compile error
```

---

# 30. Atomic

MIR:

```text
ATOMIC_LOAD
ATOMIC_STORE
ATOMIC_RMW
ATOMIC_CAS
```

Mỗi operation phải chứa memory ordering:

```text
Relaxed
Acquire
Release
AcqRel
SeqCst
```

Ví dụ:

```text
ATOMIC_LOAD %x, Acquire
```

Không được để backend tự chọn ordering.

---

# 31. Synchronization

Có thể có:

```text
LOCK
UNLOCK
```

nhưng tôi muốn hạn chế hardcode synchronization primitive vào core MIR.

Ví dụ `Mutex` vẫn có thể là library abstraction.

Compiler chỉ cần hiểu semantic boundary:

```text
SYNC
```

khi library intrinsic/contract yêu cầu.

Tương tự:

```text
SPAWN
SEND
RECEIVE
```

có thể tồn tại ở semantic MIR nhưng sau lowering thường biến thành runtime/library call.

---

# 32. Async MIR

Source:

```axiom id="b1v8c4"
async fn f(x: Buffer<u8>) {
    let a = load()
    await network()
    use(x)
    use(a)
}
```

MIR conceptually:

```text
state 0:
    %a = CALL load
    %future = CALL network
    SUSPEND state=1

state 1:
    RESUME
    use(x)
    use(a)
    DROP a
    DROP x
    RETURN
```

Nhưng đây vẫn chưa phải physical async frame.

---

# 33. Async frame lowering

Compiler xác định:

```text
values live across SUSPEND
```

Ví dụ:

```text
x
a
future
state
```

→ logical frame:

```text
AsyncFrame {
    state
    x
    a
    future
}
```

Sau đó optimizer có thể:

- stack allocate
- heap allocate
- caller allocate
- inline executor
- eliminate frame

nếu semantics cho phép.

---

# 34. SUSPEND là semantic boundary

Optimizer không được tự ý:

```text
move instruction
```

qua suspension nếu observable semantics thay đổi.

Ví dụ resource sống qua await phải được bảo toàn.

---

# 35. MIR không được phép có dangling view

Đây là một invariant cực mạnh:

```text
MIR-VIEW-01:
Every VIEW/VIEW_MUT capability has a valid provenance.

MIR-VIEW-02:
No VERIFIED MIR path may use an invalidated capability.

MIR-VIEW-03:
No VERIFIED MIR path may return a view whose provenance
does not outlive the returned capability.
```

---

# 36. Verified MIR

Đây là checkpoint.

```text
Raw MIR
   ↓
ownership analysis
   ↓
capability analysis
   ↓
effect analysis
   ↓
cleanup elaboration
   ↓
Verified MIR
```

Sau đó optimizer được phép:

```text
inline
DCE
constant folding
SROA
scalar replacement
bounds-check elimination
allocation elimination
vectorization
```

Nhưng phải giữ semantics của Verified MIR.

---

# 37. Optimizer không được làm thay đổi ownership semantics

Ví dụ source:

```axiom id="h8v3r5"
let x = Buffer.new()
consume(x)
```

MIR:

```text
ALLOC x
MOVE x
CALL consume
```

Optimizer có thể thấy `Buffer` implementation đặc biệt và inline toàn bộ.

Có thể biến thành:

```text
CALL specialized_consume
```

Nhưng semantic proof vẫn phải tương đương:

```text
x ownership transferred
resource correctly released
```

---

# 38. Đây là lý do có `Verified MIR`

Không:

```text
HIR → LLVM → hope
```

Mà:

```text
HIR
 ↓
MIR
 ↓
VERIFY
 ↓
Verified MIR
 ↓
OPTIMIZE
```

LLVM nếu được dùng bootstrap chỉ là backend.

Không phải semantic authority.

---

# 39. MIR v0.1 instruction set

Tôi đề xuất chốt danh sách ban đầu:

```text
CONSTANT
COPY
MOVE

FIELD_PLACE
INDEX_PLACE
DEREF_PLACE

LOAD
STORE

VIEW
VIEW_MUT

ALLOC
DEALLOC
DROP
DROP_IF_OWNED

CALL
DYNAMIC_CALL

CAST
CONVERT

PHI

BOUNDS_CHECK
ENUM_TAG
ENUM_PAYLOAD

ATOMIC_LOAD
ATOMIC_STORE
ATOMIC_RMW
ATOMIC_CAS

LOCK
UNLOCK

SPAWN
SEND
RECEIVE

SUSPEND
RESUME

PANIC
TRAP
```

Terminator:

```text
JUMP
BRANCH
SWITCH
RETURN
PANIC
TRAP
UNREACHABLE
```

---

# 40. Nhưng tôi muốn loại bỏ một số instruction khỏi semantic core

Không nên có:

```text
ADD
SUB
MUL
DIV
```

như một danh sách khổng lồ nếu có thể biểu diễn chúng bằng:

```text
INTRINSIC
```

Ví dụ:

```text
INTRINSIC_ADD<i32>
INTRINSIC_MUL<f64>
```

Sau đó target lowering quyết định:

```text
x86 ADD
ARM ADD
RISC-V ADD
```

Tuy nhiên những arithmetic operation cơ bản vẫn nên có canonical MIR representation để optimizer dễ xử lý.

Vì vậy phương án thực tế hơn:

```text
INTEGER_ADD
INTEGER_SUB
INTEGER_MUL
INTEGER_DIV
FLOAT_ADD
FLOAT_SUB
FLOAT_MUL
FLOAT_DIV
```

và compiler có thể mở rộng intrinsic mechanism cho các operation khác.

---

# 41. Một điều nữa cần thêm: `SELECT`

Ví dụ:

```text
x = flag ? a : b
```

Không nhất thiết phải tạo branch.

MIR có thể:

```text
%x = SELECT %flag, %a, %b
```

Optimizer/backend quyết định:

```text
cmov
branch
conditional move
```

Do đó thêm:

```text
SELECT
```

vào MIR.

---

# 42. Và `UNDEF` không nên tồn tại trong safe MIR

Tôi không muốn Axiom có một semantic equivalent của C/C++:

```text
uninitialized value
```

Trong MIR:

```text
UNINIT
```

chỉ là **ownership/initialization state của Local**, không phải value có thể sử dụng.

Không có:

```text
%v = UNDEF
```

để optimizer tùy ý dùng.

Điều này tránh một lượng lớn undefined behavior.

---

# 43. MIR invariant cốt lõi

Tôi đề xuất đóng băng nhóm đầu tiên:

```text
AMIR-01
Every instruction has statically known operand types.

AMIR-02
Every BasicBlock has exactly one terminator.

AMIR-03
Every SSA value has exactly one definition.

AMIR-04
SSA value flow and ownership/resource flow are distinct.

AMIR-05
Every memory access operates on a Place.

AMIR-06
Every Place has a derivable semantic region.

AMIR-07
MOVE changes ownership state without requiring physical copying.

AMIR-08
LOAD is READ; STORE is WRITE.

AMIR-09
VIEW and VIEW_MUT create compiler-tracked capabilities.

AMIR-10
ALLOC does not imply heap allocation.

AMIR-11
DROP does not imply a particular deallocation mechanism.

AMIR-12
No uninitialized value may reach a semantic read.

AMIR-13
Bounds safety must be proven or explicitly checked.

AMIR-14
Async suspension preserves all values required after suspension.

AMIR-15
Verified MIR contains no unresolved type/trait/generic ambiguity.

AMIR-16
Verified MIR contains no invalid ownership/capability state.

AMIR-17
Verified MIR is target-independent.

AMIR-18
Verified MIR is the semantic source of truth for optimization.
```

---

# 44. Một thay đổi kiến trúc tôi đánh giá rất quan trọng

Ta đang có:

```text
HIR
MIR
LIR
Machine IR
```

Nhưng **không nên biến chúng thành bốn IR khổng lồ độc lập**.

Nên chia trách nhiệm:

```text
HIR
= semantic structured IR

MIR
= semantic + explicit control/resource IR

LIR
= machine-oriented IR

Machine IR
= target-specific IR
```

Mỗi tầng có một mục tiêu duy nhất.

---

# 45. Và bây giờ Axiom có “xương sống compiler”

```text
                    SOURCE
                       │
                       ▼
                      AST
                       │
                       ▼
                      HIR
                       │
            ┌──────────┼──────────┐
            │          │          │
         Types       Traits      Generics
            │          │          │
            └──────────┼──────────┘
                       ▼
                      MIR
                       │
        ┌──────────────┼──────────────┐
        │              │              │
    Ownership      Capability      Effects
        │              │              │
        └──────────────┼──────────────┘
                       ▼
                    VERIFY
                       │
                       ▼
                 VERIFIED MIR
                       │
                       ▼
                   OPTIMIZER
                       │
                       ▼
                     LIR
                       │
                       ▼
                 MACHINE IR
                       │
                       ▼
                  NATIVE CODE
```

Đây là lúc Axiom bắt đầu có kiến trúc của một **compiler thực sự**, không còn chỉ là language design.

---

## Bước tiếp theo tôi đề xuất

Không nên nhảy ngay sang x86.

Ta cần xây một thứ còn quan trọng hơn:

### **AXIOM MIR INTERPRETER v0.1**

Tức:

```text
Axiom source
    ↓
AST
    ↓
HIR
    ↓
MIR
    ↓
Verifier
    ↓
MIR Interpreter
    ↓
Program result
```

MIR Interpreter sẽ trở thành **reference execution engine**.

Nó cho phép ta test:

- ownership
- Drop
- partial move
- views
- invalidation
- Result/Option
- panic/trap
- async state machine
- atomic semantics ở mức mô phỏng
- effect semantics

**trước khi có một dòng machine-code backend.**

Và quan trọng nhất: sau này nếu x86 backend cho kết quả khác MIR Interpreter, thì **backend sai**, chứ không phải semantics của Axiom tự động bị thay đổi theo backend.

Sau MIR Interpreter, ta mới thiết kế **Axiom LIR + x86-64 backend đầu tiên**, rồi ARM64/RISC-V/WASM.