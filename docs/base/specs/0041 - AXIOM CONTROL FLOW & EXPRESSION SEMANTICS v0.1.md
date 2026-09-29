Tiếp tục. Tôi sẽ khóa tiếp **AXIOM CONTROL FLOW & EXPRESSION SEMANTICS v0.1**. Đây là phần rất quan trọng vì nếu expression semantics không chặt, ownership verifier, optimizer và MIR interpreter sẽ mỗi nơi hiểu một kiểu.

# AXIOM CONTROL FLOW & EXPRESSION SEMANTICS v0.1

## 1. Expression không chỉ có `type`

Trong Axiom, mỗi expression phải được compiler resolve thành một semantic record:

```text id="p8d1m2"
ExprSem {
    type
    category
    ownership
    access
    evaluation
    resource
    control
}
```

Bảy thuộc tính:

| Thuộc tính | Câu hỏi |
|---|---|
| TYPE | Giá trị có kiểu gì? |
| CATEGORY | VALUE / PLACE / CONTROL? |
| OWNERSHIP | ai sở hữu giá trị? |
| ACCESS | READ / WRITE / MOVE? |
| EVALUATION | khi nào và theo thứ tự nào được evaluate? |
| RESOURCE | có Drop/cleanup gì? |
| CONTROL | expression có terminate/branch/suspend không? |

Đây là một trong những nền tảng quan trọng nhất của Axiom.

---

# 2. Ba expression categories

Axiom chỉ cần:

```text id="b2g8r4"
VALUE
PLACE
CONTROL
```

## VALUE

Có một giá trị:

```axiom id="p3v6w1"
a + b
Point { x: 1, y: 2 }
foo()
```

## PLACE

Đại diện cho storage location:

```axiom id="c8m1q5"
x
person.name
array[i]
*deref
```

## CONTROL

Không tạo ordinary value mà điều khiển flow:

```axiom id="d7z3n9"
return x
break
continue
panic(...)
```

---

# 3. Place ≠ reference

Điểm này rất quan trọng.

```axiom id="6w4p2c"
person.name
```

là một **Place**.

Nó không có nghĩa:

```text id="7n5x8k"
&person.name
```

và cũng không tạo pointer.

Compiler chỉ nói:

```text id="f1q6s0"
Storage location = field(name)
```

Sau đó context quyết định:

```text id="2m8r7v"
READ
WRITE
MOVE
DROP
```

---

# 4. Ví dụ

```axiom id="x7d2k1"
let x = person.age
```

RHS:

```text id="r3c9m5"
person.age
→ PLACE
→ READ
→ VALUE
```

Trong:

```axiom id="q8v4s6"
person.age = 10
```

LHS:

```text id="k1n7p3"
person.age
→ PLACE
→ WRITE
```

Không cần tạo reference object.

---

# 5. `let`

```axiom id="s2m9q4"
let x = expr
```

Semantics:

```text id="v6f3p1"
1. evaluate expr
2. obtain value
3. initialize x
4. ownership transferred/copied according to type
```

`let` không phải assignment.

---

# 6. `var`

```axiom id="m5z8r2"
var x = expr
```

giống initialization nhưng binding mutable.

Sau đó:

```axiom id="k9c1v7"
x = expr2
```

là assignment.

---

# 7. Definite initialization

Compiler phải biết:

```text id="q2s6x8"
UNINIT
INIT
MAYBE_INIT
```

Ví dụ:

```axiom id="v3h9m0"
var x: i32

print(x)
```

→ compile error.

---

# 8. Conditional initialization

```axiom id="j5n2b8"
var x: i32

if condition {
    x = 10
}

print(x)
```

Compiler thấy:

```text id="g8r4q1"
then → INIT
else → UNINIT
join → MAYBE_INIT
```

→ reject.

Nhưng:

```axiom id="p4c7m3"
if condition {
    x = 10
} else {
    x = 20
}

print(x)
```

→ cả hai path INIT.

---

# 9. `if` là expression

Axiom nên có:

```axiom id="s7n5d2"
let x = if condition {
    10
} else {
    20
}
```

Type:

```text id="z1m8q6"
i32
```

Hai branch phải có type tương thích.

---

# 10. `if` không có else

```axiom id="f4c2p8"
if condition {
    foo()
}
```

type:

```text id="y9n6v1"
Unit
```

Nếu Axiom có `Unit`.

Tôi đề xuất **có `Unit`**:

```text id="a3k7m5"
()
```

để biểu diễn “không có meaningful value”.

---

# 11. `if` branch ownership

Ví dụ:

```axiom id="m8q2d4"
let x =
    if condition {
        make_file()
    } else {
        make_file()
    }
```

Cả hai branch đều tạo owning value.

Compiler merge:

```text id="h6p9r3"
x = OWNED
```

Chỉ một branch thực sự chạy.

---

# 12. `if` với move

```axiom id="w3f7k1"
let y =
    if condition {
        move(x)
    } else {
        move(x)
    }
```

Đây là hợp lệ nếu compiler chứng minh mọi path đều consume `x` đúng một lần.

Sau expression:

```text id="v5m8q2"
x = MOVED
y = OWNED
```

---

# 13. Nhưng

```axiom id="r6d1p9"
let y =
    if condition {
        move(x)
    } else {
        10
    }
```

Sau join:

```text id="q4n7s3"
x = MAYBE_MOVED
```

Không được:

```axiom id="e2v8m5"
use(x)
```

trừ khi compiler chứng minh path.

---

# 14. `match`

`match` là expression:

```axiom id="k5p2w8"
let x = match value {
    Some(v) => v
    None => 0
}
```

Compiler kiểm tra:

- exhaustiveness
- unreachable arms
- pattern type
- ownership/move
- branch result type.

---

# 15. Match ownership

Ví dụ:

```axiom id="z7q4m1"
match result {
    Ok(data) => process(data)
    Err(err) => log(err)
}
```

Pattern binding có ownership semantics.

Nếu `data` non-Copy:

```text id="n2v8p5"
Ok(data)
 ↓
data owns payload
```

Sau branch kết thúc:

```text id="c6m3r9"
data
 ↓
Drop if needed
```

---

# 16. Pattern destructuring

Struct:

```axiom id="u4k9s2"
match point {
    Point { x, y } => ...
}
```

Compiler có thể tạo field projections:

```text id="t8q1m6"
point.x
point.y
```

Không cần tạo temporary struct.

---

# 17. Partial move trong match

```axiom id="w9m3c7"
let name = person.name

use(person.age)
```

hoặc pattern tương đương.

State:

```text id="e4p7x2"
person
├── name MOVED
└── age OWNED
```

Whole `person` không còn usable.

---

# 18. `match` phải expression-pure về control semantics

Mỗi arm có thể:

```text id="q6r2v8"
return
break
continue
panic
```

Compiler xử lý control exits riêng.

Ví dụ:

```axiom id="n8f4m1"
let x = match value {
    Some(v) => v
    None => return
}
```

Arm `None` có type `Never`/non-returning control.

---

# 19. `Never`

Tôi đề xuất có semantic type:

```text id="1p6z3k"
Never
```

cho expression không bao giờ hoàn thành bình thường:

```axiom id="x2m7q9"
return
panic("error")
trap()
loop {}
```

`Never` có thể coerce vào context cần type:

```text id="v8c4s1"
Never → T
```

vì execution không thực sự tạo `T`.

---

# 20. `loop`

```axiom id="k3m9r6"
loop {
    ...
}
```

Nếu không có `break`, semantic control:

```text id="j1q8v4"
Never
```

Nếu:

```axiom id="m6p2z7"
let x = loop {
    if done {
        break 42
    }
}
```

thì loop expression có type:

```text id="t4n9c2"
i32
```

---

# 21. `break value`

Tôi đề xuất cho phép:

```axiom id="e7k5p1"
break value
```

chỉ trong loop expression.

Ví dụ:

```axiom id="r2v8m4"
let result = loop {
    if ready {
        break compute()
    }
}
```

Điều này rất hữu ích và không làm language phức tạp đáng kể.

---

# 22. `continue`

`continue`:

```text id="f6m1q9"
CONTROL
Never
```

nó không có value.

---

# 23. `while`

```axiom id="c4x7n2"
while condition {
    body()
}
```

semantic type:

```text id="w8p3m6"
Unit
```

Compiler vẫn phân tích:

```text id="b9q2k5"
condition
body
back-edge
```

và ownership state phải converge.

---

# 24. `for`

```axiom id="d1v6s8"
for x in values {
    process(x)
}
```

nên là syntax sugar cho iterator protocol.

Compiler/HIR resolve thành semantic iteration.

Sau monomorphization có thể trở thành:

```text id="k8m4q2"
pointer/index loop
```

---

# 25. `return`

```axiom id="s5r9c1"
return expr
```

semantics:

```text id="h7m2v4"
evaluate expr
↓
construct return value
↓
cleanup locals
↓
return
```

**Không phải:**

```text id="9q6xk3"
return
↓
skip Drop
```

---

# 26. Return cleanup

Ví dụ:

```axiom id="n3c8y5"
fn f() -> File {
    let a = File.open(...)?
    let b = File.open(...)?
    return b
}
```

Trước return:

```text id="j2m7p4"
a → Drop
b → MOVE to return
```

Không được Drop `b` trước khi return.

---

# 27. Return value evaluation

Phải evaluate return expression **trước cleanup** nhưng ownership transfer phải được xác định.

Conceptually:

```text id="0q9m5r"
evaluate return expr
↓
move return value to return destination
↓
cleanup remaining locals
↓
RETURN
```

Điều này tránh double-drop.

---

# 28. `?`

Tôi đề xuất `?` là core syntax sugar cho `Result`/`Option` control propagation.

Ví dụ:

```axiom id="6f1k8z"
let file = File.open(path)?
```

Conceptually:

```text id="r7m3c2"
match File.open(path) {
    Ok(x) => x
    Err(e) => return Err(e)
}
```

Không phải exception.

---

# 29. `?` và Drop

Nếu:

```axiom id="x8n2p5"
let a = acquire()?
let b = acquire()?
let c = acquire()?
```

và `c` fail:

```text id="k4q7m1"
Drop(b)
Drop(a)
return Err(...)
```

Cleanup path được compiler tạo tự động.

---

# 30. `panic`

```axiom id="p3z9v6"
panic("bad state")
```

control:

```text id="q1m7x4"
Never
```

Nhưng trước khi terminate/unwind:

```text id="n5c2r8"
required cleanup
```

được xử lý theo panic profile.

---

# 31. `trap`

`trap()` là machine/execution-level termination.

Khác `panic`:

```text id="a8v3m6"
panic
→ language-level failure semantics

trap
→ execution-level termination
```

Ví dụ compiler intrinsic/hardware fault boundary.

---

# 32. Short-circuit

```axiom id="m4q8s2"
a && b
```

phải:

```text id="v7n1c5"
evaluate a
if false → result false
else evaluate b
```

Không được reorder `b` trước `a`.

Tương tự:

```axiom id="y9k3p6"
a || b
```

---

# 33. Short-circuit có observable semantics

Ví dụ:

```axiom id="f2r6m8"
false && side_effect()
```

`side_effect()` **không chạy**.

Optimizer không được biến:

```text id="s8x1q4"
false && side_effect()
```

thành:

```text id="c5m7n2"
side_effect()
```

dù kết quả boolean vẫn giống.

---

# 34. Evaluation order

Axiom nên khóa:

> **Expression operands và function arguments được evaluate từ trái sang phải.**

Ví dụ:

```axiom id="u6p2d8"
foo(a(), b(), c())
```

luôn:

```text id="x3m9r1"
a()
→ b()
→ c()
→ foo()
```

Điều này giúp:

- programmer predict được
- MIR deterministic
- interpreter dễ
- optimizer có boundary rõ.

---

# 35. Function call

Conceptual:

```text id="r4n7k2"
evaluate receiver/arg0
evaluate arg1
evaluate arg2
...
resolve call target
transfer arguments
call
```

Ownership transfer xảy ra sau khi argument expression tạo ra value.

---

# 36. Method syntax

```axiom id="q8v5m3"
v.length()
```

HIR:

```text id="p2c7n9"
length(v)
```

Nhưng evaluation order vẫn giữ:

```text id="j6m1x4"
evaluate v
→ evaluate explicit args
→ call
```

---

# 37. Assignment

Đã có rule trước đây, tôi muốn khóa lại thật rõ:

```axiom id="b5q9r2"
x = rhs
```

thứ tự:

```text
1. evaluate rhs
2. resolve destination place
3. validate destination access
4. validate replacement
5. drop old destination value if needed
6. move/store new value
```

Điểm số 1 trước số 5 là rất quan trọng.

---

# 38. Ví dụ self-assignment

```axiom id="t7m3p8"
x = x
```

Nếu `x` non-Copy owning:

```text id="k2r6v1"
ERROR
```

Không cố tạo semantic kỳ quặc.

Nếu `x: Copy`:

```text id="m9c4q7"
valid
```

và optimizer có thể loại bỏ toàn bộ assignment nếu không có observable effect.

---

# 39. Assignment qua field

```axiom id="c6x2m8"
person.name = new_name
```

Compiler:

```text id="h4n7p1"
RHS evaluate
↓
person.name place
↓
Drop old name
↓
Move new_name
```

Không cần lock whole `person`.

---

# 40. Compound assignment

Tôi đề xuất:

```axiom id="r8m3q6"
x += y
```

là semantic operation riêng, **không đơn giản là textual expansion** thành:

```text id="j1v5n9"
x = x + y
```

vì điều đó có thể evaluate place nhiều lần.

Ví dụ:

```axiom id="k3p8x2"
array[index()] += 1
```

`index()` chỉ nên evaluate **một lần**.

---

# 41. Prefix/postfix increment

Tôi tiếp tục đề xuất:

> Không có `++` / `--` trong Core.

Lợi ích:

- expression semantics đơn giản
- evaluation order dễ
- ownership/write tracking rõ
- tránh C/C++ style ambiguity.

---

# 42. Arithmetic

Mặc định:

```text id="v4n8m2"
integer arithmetic = checked
```

Ví dụ overflow:

```axiom id="q7c1p5"
x + y
```

nếu overflow:

```text id="n6m3r9"
panic/trap theo arithmetic profile
```

Explicit:

```text id="f8x2k4"
x.wrapping_add(y)
x.saturating_add(y)
```

hoặc intrinsic equivalent.

---

# 43. Optimizer

Nếu compiler chứng minh:

```text id="h3q9m1"
x + y cannot overflow
```

thì check có thể biến mất.

Source semantics vẫn là checked.

Đây là zero-cost principle đúng nghĩa:

```text id="s5v7c2"
safe semantics
+
proof
=
no runtime cost
```

---

# 44. Division

```axiom id="j8m4p1"
a / b
```

nếu `b == 0`:

```text id="q2x7n5"
deterministic failure
```

Không có C-style undefined behavior.

`MIN_INT / -1` cũng phải deterministic.

---

# 45. Shift

```axiom id="n7c3m8"
x << amount
```

Nếu:

```text id="p1v6q4"
amount >= bit_width
```

→ deterministic failure trong checked operation.

Nếu muốn machine masking:

```text id="s9k2x7"
wrapping_shift_left(...)
```

explicit.

---

# 46. Comparison

Không cho:

```text id="r5m1z8"
i32 == u32
```

một cách implicit.

Programmer phải convert.

Tương tự:

```text id="c8q3n6"
i32 < f32
```

không implicit.

Điều này loại bỏ một lượng lớn bug kiểu C/C++.

---

# 47. Float

IEEE-754 semantics.

Cần phân biệt:

```text id="y7p2m4"
== 
```

với total ordering.

NaN:

```text id="h1c8r5"
NaN == NaN
```

không tự nhiên true.

Nếu cần sorting:

```text id="m3q9v6"
total_compare
```

là explicit abstraction.

---

# 48. Boolean

Không có implicit:

```text id="v4n7x1"
bool → int
int → bool
pointer → bool
```

Ví dụ:

```axiom id="k6m2p8"
if ptr
```

không safe.

Phải:

```text id="s1q5r9"
ptr != null
```

nhưng raw pointer null chỉ trong unsafe/FFI.

---

# 49. No implicit null

Core:

```text id="x8c4m7"
Option<T>
```

thay vì:

```text id="d2n9p5"
T = null
```

Điều này làm expression semantics rõ hơn.

---

# 50. Function call result ownership

Nếu:

```axiom id="z7m3q1"
fn make() -> File
```

thì:

```text id="k4p8v2"
make()
```

trả:

```text id="n6x1c9"
OWNED File
```

Nếu:

```axiom id="m2q7s4"
fn inspect() -> view<Data>
```

thì return provenance phải được kiểm tra.

Không cho function trả view tới local storage:

```text id="b9v5k3"
fn bad() -> view<i32> {
    let x = ...
    return view(x)
}
```

→ reject.

---

# 51. Closure expression

```axiom id="f6n2q8"
|x| x + offset
```

là một VALUE.

Nhưng bên trong compiler:

```text id="r3m7c1"
Closure {
    environment
    code
}
```

Capture mode được infer:

```text id="j5p9v4"
COPY
MOVE
VIEW
MUT_VIEW
```

---

# 52. Closure capture

Ví dụ:

```axiom id="c8m1x6"
let x = Vec.new()

let f = || use(x)
```

Nếu `f` không escape và chỉ cần read:

```text id="p4q7n2"
VIEW capture
```

nếu cần ownership:

```text id="v9k3m5"
MOVE capture
```

Compiler tự suy luận.

Programmer không cần:

```text id="2w6r8j"
&x
&mut x
'a
```

---

# 53. Closure escape

```axiom id="n3x7p1"
fn make() -> Closure {
    let x = ...
    return || use(x)
}
```

Nếu closure captures by ownership:

```text id="f8m2q5"
MOVE x into closure
```

→ hợp lệ.

Nếu closure chỉ captures `view(x)`:

```text id="q6v1z9"
return closure
```

→ reject vì local owner chết.

---

# 54. `defer` — tôi đề xuất KHÔNG có trong Core

Đây là một quyết định đáng khóa.

Không cần:

```axiom id="b7c2m8"
defer cleanup()
```

vì Axiom đã có:

```text id="v4n9x1"
Drop
deterministic cleanup
```

Nếu cần scope guard:

```text id="j8p3q6"
Guard
```

là library abstraction.

Điều này tránh hai hệ cleanup cạnh tranh nhau:

```text id="s5m1r7"
Drop
+
defer
```

---

# 55. `break`, `continue`, `return`, `panic`

Tất cả đều là **control exits**.

Compiler nên normalize thành CFG:

```text id="y6n2p4"
BasicBlock
   ↓
cleanup blocks
   ↓
target
```

Ví dụ:

```axiom id="m9c4x8"
loop {
    let f = open()?

    if done {
        break
    }
}
```

`break` phải cleanup `f` trước khi nhảy ra loop.

---

# 56. Control-flow normalization

HIR:

```text id="r2k7v5"
if
match
while
for
loop
```

MIR:

```text id="n8m3q1"
BasicBlock
BasicBlock
BasicBlock
...
```

Ownership verifier làm việc trên CFG explicit.

---

# 57. `return` trong closure

Phải phân biệt:

```axiom id="c5x9m2"
return
```

trả khỏi closure:

```text id="u7q1p4"
closure function
```

không phải outer function.

AST/HIR phải encode function boundary rõ.

---

# 58. `break` trong closure

Tương tự:

```text id="v3m8q6"
break
```

chỉ break loop gần nhất **trong cùng function/closure**.

Không xuyên qua closure boundary.

---

# 59. `match` và ownership verifier

Tôi đề xuất compiler merge ownership state tại join bằng lattice:

```text id="h4p7n1"
OWNED
MOVED
PARTIAL
DROPPED
MAYBE_OWNED
MAYBE_MOVED
```

Ví dụ:

```text id="q9c2m5"
Path A: x = OWNED
Path B: x = MOVED

join:
x = MAYBE_MOVED
```

sau đó:

```text id="j6v1r8"
use(x)
```

→ reject.

---

# 60. Nhưng không nên làm dataflow quá nguội

Compiler có thể path-sensitize một số điều kiện.

Ví dụ:

```axiom id="x8m4p2"
if condition {
    move(x)
    return
}

use(x)
```

Ở path đến `use(x)`, x chắc chắn chưa bị move.

Do đó:

```text id="c7n2q5"
accept
```

Đây là lý do verifier cần CFG + control-flow facts, không chỉ scope-based rules.

---

# 61. Semantic Oracle

MIR interpreter phải thực thi chính xác:

- left-to-right evaluation
- short-circuit
- move
- Drop
- panic
- trap
- bounds check
- match
- loops
- suspension
- synchronization

Nếu native backend cho kết quả khác:

```text id="v5m9x1"
backend bug
```

chứ không sửa semantics theo backend.

---

# 62. Control-flow invariants

Tôi đề xuất thêm:

### ACF-01
Every expression has exactly one resolved static type.

### ACF-02
Every expression is VALUE, PLACE, or CONTROL.

### ACF-03
Place expressions identify storage locations, not implicit references.

### ACF-04
Evaluation order is deterministic left-to-right.

### ACF-05
Short-circuit operators do not evaluate skipped operands.

### ACF-06
`if` and `match` may produce values.

### ACF-07
All reachable `match` paths are exhaustively checked.

### ACF-08
`Never` represents non-normal completion.

### ACF-09
Control exits perform required cleanup.

### ACF-10
Return values are established before unrelated local cleanup.

### ACF-11
Assignment evaluates RHS before replacing destination.

### ACF-12
Non-Copy self-assignment is rejected.

### ACF-13
No implicit numeric narrowing.

### ACF-14
No implicit bool/numeric/pointer conversion.

### ACF-15
No implicit null value in safe code.

### ACF-16
Overflow/division/shift behavior is deterministic.

### ACF-17
`?` is explicit control-flow propagation, not exception handling.

### ACF-18
`defer` is not a Core construct.

### ACF-19
Closure capture preserves ownership/capability semantics.

### ACF-20
Control-flow normalization preserves semantic behavior.

---

# 63. Bây giờ Axiom đã có một “semantic spine”

Các tầng đã nối được với nhau:

```text
                   SOURCE
                      │
                      ▼
               EXPRESSION SEMANTICS
          ┌───────────┼────────────┐
          ▼           ▼            ▼
        TYPE       OWNERSHIP     CONTROL
          │           │            │
          └───────────┼────────────┘
                      ▼
                    HIR
                      │
                      ▼
                    MIR
                      │
          ┌───────────┼──────────────┐
          ▼           ▼              ▼
     Ownership     Regions        Effects
          │           │              │
          └───────────┼──────────────┘
                      ▼
                 Verification
                      │
                      ▼
                VERIFIED MIR
                      │
                      ▼
                 OPTIMIZATION
                      │
                      ▼
                 ABI LOWERING
                      │
                      ▼
                 MACHINE CODE
```

Điểm này rất quan trọng: **Axiom không còn là một danh sách tính năng rời rạc**. Các feature đang quy về cùng một semantic model.

---

## Bước tiếp theo

Tôi nghĩ **không nên tiếp tục thêm feature ngay**.

Phần nguy hiểm nhất còn lại là:

# `AXIOM TYPE INFERENCE + TRAIT RESOLUTION + GENERIC SYSTEM v0.1`

Nó phải giải quyết chính xác:

```text
let x = ...
T inference
generic constraints
trait implementation lookup
method resolution
operator resolution
associated types
type aliases
distinct/newtype
coercion
numeric literals
function overloading
generic specialization
static vs dynamic dispatch
```

Đặc biệt cần quyết định **Axiom có overload function hay không**. Đây là một trong những điểm có thể làm ngôn ngữ từ “đơn giản nhưng mạnh” biến thành C++-style overload-resolution nightmare nếu thiết kế không chặt.