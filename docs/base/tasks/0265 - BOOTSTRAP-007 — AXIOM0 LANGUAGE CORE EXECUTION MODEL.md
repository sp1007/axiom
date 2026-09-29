# BOOTSTRAP-007 — AXIOM0 LANGUAGE CORE EXECUTION MODEL

Đây là bước chuyển từ **harness** sang semantics thực thi thật.

Mục tiêu của BOOT-007 không phải thêm nhiều tính năng, mà chốt một thứ cực quan trọng:

> **Một expression Axiom biến thành giá trị, một Place biến thành vị trí lưu trữ, và statement biến đổi trạng thái chương trình như thế nào.**

Nếu phần này mơ hồ, sau này ownership, MIR, optimizer, register allocation đều sẽ phải sửa.

---

# 1. Mô hình cơ bản

Axiom nên phân biệt tuyệt đối:

```text
Value
Place
Storage
Capability
```

Ví dụ:

```axiom
var x: i32 = 42;
x = 10;
```

`x` có:

```text
Value:
    42 → 10

Place:
    vị trí semantic của x

Storage:
    register / stack / memory tùy compiler

Capability:
    quyền WRITE lên x
```

Không được đồng nhất:

```text
x == address
```

hay:

```text
x == stack slot
```

Đây là nền tảng để compiler có thể biến:

```axiom
var x = 42;
return x;
```

thành đơn giản:

```asm
mov eax, 42
ret
```

mà semantics vẫn giữ nguyên.

---

# 2. `let` và `var`

Chốt:

```axiom
let x = expr;
```

là immutable binding.

```axiom
var x = expr;
```

là mutable binding.

Ví dụ:

```axiom
let x = 10;
x = 20;        // ERROR
```

Trong khi:

```axiom
var x = 10;
x = 20;        // OK
```

Điều này không liên quan đến storage.

`var` không có nghĩa:

```text
stack variable
```

và `let` không có nghĩa:

```text
constant memory
```

Chỉ nói về **khả năng mutation của semantic binding**.

---

# 3. `const`

`const` khác `let`.

```axiom
const X: i32 = 42;
```

`const` phải có giá trị compile-time.

Ví dụ:

```axiom
const ANSWER: i32 = 40 + 2;
```

Compiler có thể materialize:

```text
42
```

và không cần runtime storage.

Do đó:

```text
let
    runtime binding

const
    compile-time value
```

Không nên nhập hai khái niệm này thành một.

---

# 4. `comptime`

```axiom
comptime {
    ...
}
```

là compile-time execution.

Ví dụ:

```axiom
const SIZE: usize = comptime {
    calculate_size()
};
```

Nhưng BOOT-007 **chưa cần implement comptime**.

Parser/type system có thể chuẩn bị AST/HIR node.

Compiler Stage-0 chỉ cần báo:

```text
AXxxxx comptime not implemented in bootstrap stage
```

nếu gặp.

Không được phá architecture để implement nó sớm.

---

# 5. Expression model

Axiom expression có thể phân loại:

```text
Expression
├── Value expression
├── Place expression
└── Control-flow expression
```

Ví dụ:

```axiom
42
```

→ Value

```axiom
x
```

có thể được dùng như:

```text
LOAD Place(x)
```

→ Value context

nhưng:

```axiom
x = 42
```

→ Place context.

---

# 6. Place là khái niệm trung tâm

Ví dụ:

```axiom
p.x
```

là:

```text
Place(
    base = p,
    projection = Field(x)
)
```

Không phải:

```text
address = &p + offset(x)
```

Ở MIR:

```text
Place {
    base: p,
    projections: [
        Field(x)
    ]
}
```

Sau này layout engine mới quyết định:

```text
offset(x) = 0
```

hoặc:

```text
offset(x) = 8
```

---

# 7. Index

```axiom
a[i]
```

semantic MIR:

```text
Place {
    base: a,
    projections: [
        Index(i)
    ]
}
```

Bounds checking thuộc semantic/runtime correctness.

Compiler chỉ được loại bỏ bounds check khi chứng minh được an toàn.

Không bao giờ dựa vào:

```text
"chắc chắn programmer không đưa sai index"
```

trong safe code.

---

# 8. Dereference

Raw pointer:

```axiom
*ptr
```

là Place nhưng thuộc unsafe semantics.

Ví dụ:

```axiom
unsafe {
    *ptr = 42;
}
```

MIR:

```text
Place(
    base = ptr,
    projections = [
        Deref
    ]
)
```

Verifier phải biết đây là unsafe-derived place.

---

# 9. Assignment

Assignment:

```axiom
x = expr;
```

semantic:

```text
evaluate expr
→ obtain Value
→ obtain destination Place
→ STORE
```

MIR:

```text
%v = ...
STORE %v -> x
```

Nếu destination đang chứa một owning value, assignment có thể cần:

```text
DROP old value
STORE new value
```

với điều kiện old value còn owned.

Ví dụ:

```axiom
var x = make_buffer();
x = make_buffer();
```

không được leak buffer đầu tiên.

Semantics:

```text
old x
   ↓
DROP
   ↓
new value
   ↓
STORE
```

---

# 10. Assignment không phải Copy

Ví dụ:

```axiom
var a = buffer();
var b = a;
```

Nếu `Buffer` non-Copy:

```text
MOVE a → b
```

không phải:

```text
COPY a → b
```

Trong khi:

```axiom
var x: i32 = 42;
var y = x;
```

`i32` là Copy:

```text
COPY x → y
```

MIR phải thể hiện semantic distinction này.

---

# 11. Initialization

```axiom
var x: i32;
```

không đồng nghĩa:

```text
x = 0
```

Nó là:

```text
x = UNINIT
```

Sau:

```axiom
x = 42;
```

thành:

```text
x = INIT
```

Do đó:

```axiom
var x: i32;
return x;
```

→ compile error.

Đây là một phần của ownership/initialization verifier.

---

# 12. Reinitialization

Sau Move:

```axiom
var a = make_buffer();
var b = a;
```

trạng thái:

```text
a = Moved
b = Owned
```

Nhưng:

```axiom
a = make_buffer();
```

được phép.

Trạng thái:

```text
a = Owned
```

Đây là lý do `Moved` không phải immutable terminal state.

---

# 13. Block là expression

Axiom nên giữ block-expression semantics:

```axiom
{
    let x = 20;
    x + 22
}
```

giá trị:

```text
42
```

Trong khi:

```axiom
{
    let x = 20;
    x + 22;
}
```

giá trị:

```text
unit
```

Semantics:

```text
expression without semicolon
    → block value

expression with semicolon
    → unit
```

Đã phù hợp với syntax baseline.

---

# 14. `return`

```axiom
return expr;
```

không đơn giản là:

```text
RETURN value
```

Nó phải chạy cleanup trước khi rời function.

Ví dụ:

```axiom
fn f() -> i32 {
    let a = resource();
    return 42;
}
```

Semantic:

```text
evaluate 42
↓
cleanup a
↓
RETURN 42
```

MIR cleanup sẽ được elaboration xử lý.

---

# 15. `if`

```axiom
if condition {
    a()
} else {
    b()
}
```

HIR:

```text
If {
    condition
    then
    else
}
```

MIR:

```text
bb0:
    %c = ...
    cond_br %c, bb1, bb2

bb1:
    call a
    br bb3

bb2:
    call b
    br bb3

bb3:
    ...
```

---

# 16. `if` expression

```axiom
let x = if condition {
    10
} else {
    20
};
```

phải tạo value merge.

```text
bb1:
    %v1 = const 10
    br bb3

bb2:
    %v2 = const 20
    br bb3

bb3:
    %x = phi [%v1, bb1], [%v2, bb2]
```

Đây là lý do MIR cần SSA-assisted architecture.

---

# 17. `while`

```axiom
while x < 10 {
    x = x + 1;
}
```

CFG:

```text
       ┌──────────────┐
       │              ▼
    bb_header ──false→ bb_exit
       │
      true
       ▼
    bb_body
       │
       └──────────────→ bb_header
```

MIR:

```text
bb_header:
    %c = ...
    cond_br %c, bb_body, bb_exit

bb_body:
    ...
    br bb_header

bb_exit:
    ...
```

---

# 18. `loop`

```axiom
loop {
    ...
}
```

là infinite loop semantic.

```text
bb_loop:
    ...
    br bb_loop
```

Nếu không có `break`, compiler biết block sau loop unreachable.

Ví dụ:

```axiom
loop {
}
return 42;
```

`return 42` unreachable.

---

# 19. `break`

```axiom
loop {
    if x {
        break;
    }
}
```

`break` không phải một jump đơn giản.

Nếu có resource:

```axiom
loop {
    let temp = resource();

    if done {
        break;
    }
}
```

phải:

```text
break
 ↓
cleanup temp
 ↓
loop_exit
```

Do đó:

```text
break → CleanupGraph → target
```

---

# 20. `continue`

Tương tự:

```axiom
continue;
```

phải chạy cleanup của scope hiện tại trước khi quay lại loop header.

```text
continue
   ↓
cleanup local scope
   ↓
loop header
```

---

# 21. Function call

Ví dụ:

```axiom
let x = add(20, 22);
```

semantic:

```text
evaluate arguments
↓
apply argument passing semantics
↓
CALL add
↓
receive result
↓
initialize x
```

Không được coi function call là expression opaque quá sớm.

MIR cần biết:

```text
CALL {
    callee: FunctionId
    args: [...]
    result: %x
    effects: internal facts
}
```

---

# 22. Argument semantics

Đây là nơi ownership bắt đầu hoạt động thực sự.

```axiom
fn consume(x: Buffer) { ... }
```

Call:

```axiom
consume(a);
```

→ Move.

---

```axiom
fn read(x: view<Buffer>) { ... }
```

Call:

```axiom
read(a);
```

→ implicit ephemeral owner→view conversion.

---

```axiom
fn modify(x: mut_view<Buffer>) { ... }
```

Call:

```axiom
modify(a);
```

→ exclusive mutable capability.

---

# 23. Không tạo view binding ngầm

Cho phép:

```axiom
read(a);
```

nhưng không tự động coi:

```axiom
let x = a;
```

là view.

`x` vẫn là:

```text
ownership transfer/copy
```

Nếu muốn view:

```axiom
let x = view(a);
```

Điều này giữ semantics rõ ràng.

---

# 24. Method call

```axiom
p.length()
```

HIR phải hạ thành:

```text
length(p)
```

hoặc tương đương receiver semantic.

Ví dụ:

```axiom
fn length(self: view<String>) -> usize
```

Call:

```axiom
s.length()
```

→ compiler tạo ephemeral view của `s`.

Không cần object dispatch.

---

# 25. Operator

Ví dụ:

```axiom
a + b
```

giai đoạn đầu:

```text
builtin arithmetic
```

Sau khi trait system hoàn chỉnh:

```text
Add::add(a, b)
```

nhưng semantic HIR/MIR cuối cùng phải resolve thành dispatch cụ thể.

Không để MIR chứa:

```text
"hãy tìm trait Add"
```

Trait solving đã hoàn tất trước MIR.

---

# 26. Evaluation order

Đây là thứ nên **đóng băng ngay**.

Axiom dùng:

> **Left-to-right evaluation order.**

Ví dụ:

```axiom
f(a(), b(), c());
```

luôn:

```text
a()
↓
b()
↓
c()
↓
f()
```

Tương tự:

```axiom
x + y * z
```

theo precedence thông thường.

Compiler có thể reorder nội bộ **chỉ khi observable semantics không thay đổi**.

Điều này rất quan trọng với:

- side effects
- volatile
- atomic
- panic
- IO
- ownership
- function calls

---

# 27. Short-circuit

```axiom
a && b
```

không được compile thành:

```text
evaluate a
evaluate b
AND
```

mà:

```text
evaluate a
if false → false
otherwise evaluate b
```

Tương tự:

```axiom
a || b
```

```text
evaluate a
if true → true
otherwise evaluate b
```

MIR:

```text
%a = ...
cond_br %a, bb_eval_b, bb_false

bb_eval_b:
    %b = ...
    br bb_merge

bb_false:
    const false
    br bb_merge
```

---

# 28. `&&` / `||` không phải bitwise

Axiom đã có:

```text
& | ^
```

cho bitwise.

Và:

```text
&& ||
```

cho logical short-circuit.

Không overload semantics này tùy tiện.

---

# 29. `!`

Boolean:

```axiom
!x
```

→ logical NOT.

Bitwise complement nên:

```axiom
~x
```

Tách rõ.

---

# 30. Arithmetic overflow

BOOT-007 chỉ cần chuẩn hóa semantic flag:

```text
Checked
Wrapping
Saturating
```

Mặc định Axiom:

```text
Checked
```

Ví dụ:

```axiom
let x: i32 = MAX_I32 + 1;
```

compile-time constant:

```text
compile error
```

runtime:

```text
trap/panic according to arithmetic policy
```

Explicit wrapping:

```axiom
wrapping_add(a, b)
```

hoặc intrinsic/library API.

Sau này có thể thêm syntax nếu cần.

Điểm quan trọng:

> **Không dùng C-style signed overflow UB.**

---

# 31. Numeric conversion

Không:

```axiom
let x: i64 = i32_value;
```

nếu language policy yêu cầu conversion explicit.

Dùng:

```axiom
let x = value as i64;
```

Và:

```text
CAST
```

khác:

```text
BITCAST
```

`bitcast` chỉ khi representation tương thích.

---

# 32. `never`

`panic()`:

```text
panic() -> never
```

Ví dụ:

```axiom
let x: i32 = if condition {
    42
} else {
    panic()
};
```

`never` có thể coerce vào mọi expected type.

MIR:

```text
bb_else:
    call panic
    unreachable
```

Không cần một runtime exception mechanism.

---

# 33. `unit`

Statement:

```axiom
foo();
```

nếu `foo -> unit`, kết quả bị discard.

Expression:

```axiom
let x = foo();
```

thì:

```text
x: unit
```

ZST semantics phải vẫn tồn tại dù backend có thể loại bỏ physical storage.

---

# 34. `discard`

Nếu một value có Drop:

```axiom
make_resource();
```

không được optimizer đơn giản bỏ call.

Nó phải:

```text
evaluate
↓
temporary ownership
↓
DROP
```

Ngược lại:

```axiom
let x = 42;
```

nếu `x` không được sử dụng:

```text
x
```

có thể bị DCE.

---

# 35. Temporary lifetime

Ví dụ:

```axiom
use(make_buffer());
```

temporary phải sống đủ lâu cho:

```text
use()
```

Sau call:

```text
DROP temporary
```

Semantic:

```text
evaluate argument
↓
temporary ownership
↓
CALL
↓
DROP
```

Nhưng compiler có thể tối ưu storage.

---

# 36. Scope và lifetime

Đừng dùng lexical scope làm lifetime duy nhất.

Ví dụ:

```axiom
{
    let x = resource();
    use(x);
}
```

semantic lifetime có thể kết thúc ngay sau:

```text
use(x)
```

nếu không còn dependency.

Tức:

```text
lexical scope ≠ resource lifetime
```

Compiler có thể shorten lifetime.

Điều này phù hợp với:

```text
AOWN
AMEM-54
AMEM-69
```

---

# 37. Nhưng Drop phải deterministic

Shorten lifetime không có nghĩa:

```text
compiler tùy ý destroy value
```

Nó chỉ được destroy sớm nếu observable semantics không đổi.

Ví dụ:

```axiom
let x = resource();
use(x);
other();
```

Nếu Drop của `x` observable, compiler phải bảo đảm thứ tự semantics tương đương.

Đây là nơi Drop optimization phải rất cẩn thận.

---

# 38. MIR tối thiểu cho BOOT-007

Chốt instruction set đầu tiên:

```text
CONST
COPY
MOVE
LOAD
STORE

ADD
SUB
MUL
DIV
CMP

CALL
RETURN

BR
COND_BR
PHI

DROP
TRAP
UNREACHABLE
```

Chưa cần:

```text
AWAIT
ATOMIC
LOCK
SPAWN
GPU
```

nhưng MIR enum phải thiết kế extensible.

---

# 39. `Place` API nội bộ

Nên chốt cấu trúc:

```text id="j20o74"
Place {
    base: PlaceBase,
    projections: SmallVec<Projection>
}
```

```text id="4o4t0t"
PlaceBase:
    Local(LocalId)
    Argument(ArgId)
    Static(StaticId)
    Temporary(TempId)
    ReturnPlace
    Global(GlobalId)
```

Projection:

```text id="2agwgo"
Field(FieldId)
Index(ValueId)
Deref
Downcast(VariantId)
Slice
```

`Field` không chứa physical offset.

---

# 40. LOAD/STORE

Ví dụ:

```axiom
return p.x;
```

MIR:

```text
%p_x_place = p.x
%v = LOAD %p_x_place
RETURN %v
```

Representation thực tế có thể sau này thành:

```asm
mov eax, [rdi+4]
```

hoặc:

```asm
mov eax, edi
```

nếu optimizer chứng minh được `p.x` đã nằm trong register.

---

# 41. MIR không cần `ADDRESS_OF` cho ordinary values

Đây là một điểm quan trọng.

Đừng thiết kế MIR kiểu:

```text
x
 ↓
address
 ↓
load
```

cho mọi variable.

Chỉ khi semantics thực sự yêu cầu address:

```axiom
unsafe ...
```

hoặc stable-address/storage contract.

Bình thường:

```text
Place → Value
```

là đủ.

Điều này giúp Axiom tránh bị “pointer hóa” toàn bộ compiler.

---

# 42. ABI chưa chen vào đây

Ví dụ:

```axiom
fn add(a: i32, b: i32) -> i32
```

MIR:

```text
%a
%b
%c = ADD %a, %b
RETURN %c
```

Không có:

```text
RDI
RSI
RAX
```

ABI lowering sau này mới quyết định.

---

# 43. CFG invariant

BOOT-007 chốt:

Mỗi basic block:

```text
0 hoặc nhiều non-terminator
+
chính xác 1 terminator
```

Terminator:

```text
BR
COND_BR
SWITCH
RETURN
TRAP
UNREACHABLE
```

Không có instruction sau terminator.

---

# 44. Dominance

MIR verifier cần kiểm tra:

```text
SSA value must dominate every use
```

Ví dụ sai:

```text
bb0:
    cond_br c, bb1, bb2

bb1:
    %x = const 42
    br bb3

bb2:
    use %x     // INVALID
```

vì `%x` không dominate `bb2`.

Đây phải là verifier error, không phải backend bug.

---

# 45. Initialization dataflow

Verifier theo dõi:

```text
Uninit
Owned
Moved
PartiallyMoved
Dropped
```

Ví dụ:

```axiom
var x: i32;
if condition {
    x = 42;
}
return x;
```

CFG merge:

```text
branch A → x Owned
branch B → x Uninit
```

→ `x` không definitely initialized.

Compile error.

---

# 46. `if` definite initialization

Ngược lại:

```axiom
var x: i32;

if condition {
    x = 42;
} else {
    x = 43;
}

return x;
```

hai nhánh đều:

```text
x = Owned
```

→ hợp lệ.

Đây là một trong những test đầu tiên cho verifier.

---

# 47. Assignment vào field

```axiom
p.x = 42;
```

phải chỉ mutate field `x`.

Không coi toàn bộ:

```text
p
```

là WRITE conflict nếu compiler có field-region precision.

Semantic region:

```text
p.x
```

khác:

```text
p.y
```

Điều này sẽ hỗ trợ:

```axiom
mut_view(p.x)
mut_view(p.y)
```

đồng thời.

---

# 48. Function return

Chốt:

```axiom
fn f() -> T
```

return `T` theo ownership semantics.

Nếu `T: Copy`:

```text
COPY
```

nếu owning non-Copy:

```text
MOVE
```

không có implicit heap allocation.

Ví dụ:

```axiom
fn make() -> Buffer {
    var x = Buffer(...);
    return x;
}
```

không bắt buộc:

```text
heap allocate x
```

Compiler có thể dùng:

```text
caller-allocated return storage
```

đúng theo AMEM-28/29.

---

# 49. First real vertical slice

Sau BOOT-007, Axiom0 phải compile được:

### Test 1

```axiom
fn main() -> i32 {
    return 42;
}
```

### Test 2

```axiom
fn main() -> i32 {
    let x = 40;
    let y = 2;
    return x + y;
}
```

### Test 3

```axiom
fn main() -> i32 {
    var x = 40;
    x = x + 2;
    return x;
}
```

### Test 4

```axiom
fn main() -> i32 {
    if true {
        return 42;
    }

    return 0;
}
```

### Test 5

```axiom
fn main() -> i32 {
    var x: i32;

    if true {
        x = 42;
    } else {
        x = 43;
    }

    return x;
}
```

### Test 6 — compile fail

```axiom
fn main() -> i32 {
    let x = 42;
    x = 10;
    return x;
}
```

### Test 7 — compile fail

```axiom
fn main() -> i32 {
    var x: i32;
    return x;
}
```

### Test 8 — loop

```axiom
fn main() -> i32 {
    var x = 0;

    while x < 42 {
        x = x + 1;
    }

    return x;
}
```

Kết quả native:

```text
42
```

---

# 50. BOOT-007 Gate

Milestone chỉ PASS khi:

```text
[✓] let
[✓] var
[✓] const representation prepared
[✓] initialization tracking
[✓] assignment
[✓] reinitialization
[✓] expressions
[✓] Place
[✓] LOAD
[✓] STORE
[✓] function call
[✓] return
[✓] if
[✓] if-expression
[✓] while
[✓] loop
[✓] break
[✓] continue
[✓] block expressions
[✓] short-circuit
[✓] never
[✓] unit
[✓] deterministic evaluation order

[✓] CFG verification
[✓] SSA dominance
[✓] initialization verification
[✓] -O0 native tests
[✓] MIR interpreter/native differential
[✓] compile-fail tests
[✓] previous milestone regression
```

---

## Một quyết định rất quan trọng được chốt ở BOOT-007

Axiom từ đây có một mô hình cực rõ:

```text
                    EXPRESSION
                        │
             ┌──────────┼──────────┐
             ▼          ▼          ▼
           VALUE       PLACE    CONTROL FLOW
             │          │
             │          ├── LOAD
             │          ├── STORE
             │          ├── MOVE
             │          ├── COPY
             │          └── DROP
             │
             ▼
           SSA VALUE
```

và:

```text
Place ≠ Pointer
Place ≠ Stack Slot
Place ≠ Address
```

Đây là một trong những quyết định giúp Axiom vừa có **low-level control**, vừa tránh việc programmer phải suốt ngày suy nghĩ về pointer/reference.

### Bước tiếp theo

**BOOTSTRAP-008 — Functions + ABI Execution Model** sẽ nối trực tiếp từ đây: parameter passing, return values, recursive calls, caller/callee semantics, calling convention boundary, aggregate arguments/returns và bắt đầu tạo executable thực sự cho các function call phức tạp hơn.