Tiếp tục với **BOOTSTRAP-027 — Control Flow & Pattern Semantics**.

Đây là phần khá quan trọng vì control flow phải vừa **dễ đọc như ngôn ngữ hiện đại**, vừa có thể hạ xuống CFG/MIR rất trực tiếp, không tạo runtime overhead.

---

# BOOTSTRAP-027 — Control Flow & Pattern Semantics

## 1. Nguyên tắc tổng thể

Axiom chỉ cần một tập control-flow nhỏ nhưng đủ mạnh:

```text
if / else
match
loop
while
for
break
continue
return
```

Không cần:

```text
goto
switch kiểu C
do/while
exception-based control flow
```

trong Core.

`goto` vẫn có thể tồn tại ở system/unsafe layer nếu thực sự cần cho compiler, kernel hoặc machine-level code.

---

# 2. `if` là expression

Axiom nên cho:

```axiom
let x = if condition {
    10
} else {
    20
}
```

và:

```axiom
if x > 0 {
    foo()
} else {
    bar()
}
```

Một block expression trả về giá trị cuối cùng.

---

# 3. Không cần `return` ở mọi branch

Ví dụ:

```axiom
fn abs(x: i32) -> i32 {
    if x >= 0 {
        x
    } else {
        -x
    }
}
```

Compiler suy ra:

```text
if condition
 ├── value x
 └── value -x
        ↓
      merge
        ↓
       i32
```

Trong MIR:

```text
BB0
 ├─ branch
 │
 ├─ BB1 → value
 │
 └─ BB2 → value
          ↓
       BB3 merge
```

---

# 4. Block expression

Các block:

```axiom
{
    let a = 10
    let b = 20
    a + b
}
```

có type:

```text
i32
```

Statement cuối là expression.

Nếu không có value:

```axiom
{
    foo()
}
```

type:

```text
unit
```

---

# 5. `if` phải có cùng result type

Ví dụ:

```axiom
let x = if flag {
    10
} else {
    "hello"
}
```

→ lỗi type.

Không có implicit union type.

Nếu muốn:

```axiom
enum Value {
    Int(i32)
    Text(String)
}
```

rồi:

```axiom
let x = if flag {
    Value::Int(10)
} else {
    Value::Text("hello")
}
```

Điều này giữ type system rõ ràng.

---

# 6. `if` không cần boolean conversion

Không cho kiểu C:

```text
if (x) ...
```

với `x: i32`.

Chỉ:

```axiom
if x != 0 {
    ...
}
```

hoặc:

```axiom
if condition {
    ...
}
```

`bool` phải thực sự là `bool`.

---

# 7. `else if`

Đơn giản:

```axiom
if x < 0 {
    negative()
} else if x == 0 {
    zero()
} else {
    positive()
}
```

Compiler hạ thành CFG bình thường.

Không cần syntax riêng trong compiler.

---

# 8. `match` là control-flow primitive mạnh nhất

Ví dụ:

```axiom
match value {
    0 => zero()
    1 => one()
    _ => other()
}
```

hoặc:

```axiom
match result {
    Ok(value) => process(value)
    Err(error) => handle(error)
}
```

`match` có thể là expression:

```axiom
let text = match result {
    Ok(x) => format(x)
    Err(_) => "error"
}
```

---

# 9. Exhaustiveness bắt buộc

Ví dụ:

```axiom
enum State {
    Ready
    Running
    Finished
}
```

Sai:

```axiom
match state {
    Ready => ...
    Running => ...
}
```

Compiler:

```text
non-exhaustive pattern:
missing State::Finished
```

Không có fallback ngầm.

---

# 10. `_` là wildcard

```axiom
match state {
    Ready => ...
    _ => ...
}
```

được.

Nhưng compiler vẫn phân tích unreachable patterns.

Ví dụ:

```axiom
match state {
    _ => foo()
    Ready => bar()
}
```

`Ready` unreachable → diagnostic.

---

# 11. Pattern không chỉ là value comparison

Pattern có thể destructure.

```axiom
match point {
    Point { x: 0, y: 0 } => origin()
    Point { x, y } => draw(x, y)
}
```

Enum:

```axiom
match shape {
    Circle { radius, .. } => ...
    Rectangle { width, height } => ...
}
```

Tuple:

```axiom
match pair {
    (0, x) => ...
    (x, 0) => ...
    (x, y) => ...
}
```

---

# 12. Pattern có thể bind variable

```axiom
match result {
    Ok(value) => use(value)
    Err(error) => report(error)
}
```

Compiler tạo bindings có ownership semantics bình thường.

Không có "pattern variable" là một loại reference đặc biệt.

---

# 13. Pattern binding mặc định không copy tùy tiện

Đây là điểm quan trọng với ownership.

Nếu:

```axiom
let result: Result<Buffer, Error> = ...
```

và:

```axiom
match result {
    Ok(buffer) => consume(buffer)
    Err(error) => ...
}
```

`buffer` có thể **Move** khỏi enum nếu semantics cho phép.

Compiler phải cập nhật ownership state.

Không tự động clone.

---

# 14. Borrow/view pattern phải explicit khi cần

Nếu muốn chỉ đọc:

```axiom
match result {
    Ok(ref buffer) => inspect(buffer)
}
```

Tôi không thích syntax `ref` kiểu Rust ở đây.

Phù hợp triết lý Axiom hơn:

```axiom
match result {
    Ok(buffer) => inspect(view(buffer))
}
```

hoặc compiler có thể cho phép pattern binding context suy ra ephemeral view nếu `inspect` yêu cầu `view<Buffer>`.

Tức là:

```axiom
inspect(buffer)
```

vẫn có thể không Move nếu parameter là `view<Buffer>`.

---

# 15. Partial move

Với:

```axiom
struct User {
    id: u64
    name: String
}
```

có thể:

```axiom
let user = ...

let name = user.name
```

nếu `name` là non-Copy.

Compiler đánh dấu:

```text
user.name → MOVED
user.id   → VALID
```

Sau đó:

```axiom
println(user.id)
```

hợp lệ.

Nhưng:

```axiom
println(user.name)
```

lỗi.

---

# 16. User-defined Drop vẫn giữ quy tắc đã chốt

Nếu struct có custom Drop:

```axiom
struct Resource {
    ...
}

impl Drop for Resource {
    ...
}
```

thì partial move bị hạn chế.

Ví dụ:

```axiom
let x = resource
let y = x.field
```

→ compiler reject nếu làm cho Drop semantics không xác định.

Điều này đã khớp memory model.

---

# 17. `if let`

Nên có.

```axiom
if let Some(value) = result {
    use(value)
}
```

Đây là syntax sugar cho một `match` hai nhánh:

```axiom
match result {
    Some(value) => use(value)
    None => ()
}
```

Nhưng compiler có thể lower trực tiếp.

---

# 18. `while let`

Tương tự:

```axiom
while let Some(item) = iterator.next() {
    process(item)
}
```

rất hữu ích cho collection/channel/state machine.

---

# 19. `loop`

`loop` là primitive vô hạn:

```axiom
loop {
    process()
}
```

Có thể break:

```axiom
loop {
    if done {
        break
    }
}
```

Nếu `break` có value:

```axiom
let result = loop {
    if ready {
        break compute()
    }

    wait()
}
```

Tôi đề xuất **có break-value**.

Nó làm control flow expression mạnh hơn mà không cần thêm construct.

---

# 20. `break value`

Ví dụ:

```axiom
let result = loop {
    let x = read()

    if x.is_valid() {
        break x
    }
}
```

Type của loop là type của `break` value.

Nếu:

```axiom
break 10
```

thì:

```text
loop : i32
```

Nếu loop không break có value:

```text
loop : never
```

hoặc nếu break không-value:

```text
loop : unit
```

Compiler kiểm tra consistency.

---

# 21. `while`

```axiom
while condition {
    process()
}
```

là syntax sugar/CFG form:

```text
header
 ↓
condition
 ├── false → exit
 └── true
      ↓
    body
      ↓
    header
```

Không cần runtime abstraction.

---

# 22. `for`

Axiom nên hỗ trợ:

```axiom
for item in items {
    process(item)
}
```

nhưng semantic phải dựa trên **iteration protocol**.

Ví dụ conceptually:

```text
IntoIterator
Iterator
next()
```

Tuy nhiên `for` nên là compiler-known syntax để optimizer dễ nhận diện.

---

# 23. Zero-cost `for`

Ví dụ:

```axiom
for x in array {
    sum += x
}
```

không nên tạo:

```text
Iterator object
Box
dynamic dispatch
heap allocation
```

Compiler có thể lower trực tiếp thành:

```text
index = 0
loop:
    if index == len goto done
    x = array[index]
    ...
    index++
    goto loop
```

hoặc pointer/stride loop.

---

# 24. Iterator abstraction vẫn có thể tồn tại

Ví dụ:

```axiom
trait Iterator {
    type Item

    fn next(self: mut_view<Self>) -> Option<Self.Item>
}
```

Generic iterator:

```axiom
for x in iterator {
    ...
}
```

có thể monomorphize thành loop machine-level.

Do đó abstraction không nhất thiết có cost.

---

# 25. `for` với ownership

Ví dụ:

```axiom
for item in buffer {
    consume(item)
}
```

có thể consume từng element.

Nếu muốn read-only:

```axiom
for item in view(buffer) {
    inspect(item)
}
```

Compiler tạo read capabilities.

Nếu muốn mutate:

```axiom
for item in mut_view(buffer) {
    modify(item)
}
```

Capability semantics vẫn áp dụng.

---

# 26. `break` và `continue`

```axiom
loop {
    if invalid {
        continue
    }

    if done {
        break
    }

    work()
}
```

`continue` quay về loop condition/header.

`break` đi tới exit.

Compiler phải biết cleanup của scope.

---

# 27. Scope cleanup trước `break`

Ví dụ:

```axiom
loop {
    let resource = acquire()

    if done {
        break
    }
}
```

Trước `break`:

```text
drop(resource)
```

phải chạy.

Tương tự `continue`:

```text
drop(resource)
→ loop header
```

Đây là một trong những lý do MIR cần explicit Drop elaboration.

---

# 28. Labeled loops

Nên hỗ trợ.

```axiom
'outer: for x in xs {
    for y in ys {
        if found(x, y) {
            break 'outer
        }
    }
}
```

Có ích cho nested loops.

Không cần `goto`.

---

# 29. `return` từ nested block

```axiom
fn foo() -> Result<()> {
    if condition {
        return Err(Error::Invalid)
    }

    Ok(())
}
```

`return` thoát function, không chỉ block.

Compiler chạy cleanup của toàn bộ active scopes.

---

# 30. `never`

Type:

```axiom
never
```

dành cho:

```axiom
panic(...)
abort(...)
loop { ... }
```

Compiler có thể coerce:

```text
never → T
```

vì code sau `never` không được thực thi.

Ví dụ:

```axiom
let x: i32 = if condition {
    42
} else {
    panic("fatal")
}
```

hợp lệ.

---

# 31. Unreachable

Compiler có thể có intrinsic:

```axiom
unreachable()
```

hoặc:

```axiom
unsafe {
    unreachable_unchecked()
}
```

Phân biệt:

### Safe unreachable

Compiler biết code path không thể tới.

### Unsafe unreachable

Programmer tuyên bố invariant.

Không được dùng unsafe version tùy tiện vì compiler có thể optimize thành behavior không còn trực quan nếu assertion sai.

---

# 32. Pattern guard

Có thể hỗ trợ:

```axiom
match value {
    Some(x) if x > 10 => large()
    Some(x) => small()
    None => missing()
}
```

Guard được evaluate sau khi pattern match.

Nếu guard false → thử pattern arm tiếp theo.

---

# 33. Guard không làm mất exhaustiveness

Ví dụ:

```axiom
match value {
    Some(x) if x > 10 => ...
}
```

không exhaustive chỉ vì `Some` đã xuất hiện.

Compiler phải hiểu:

```text
Some(x) if predicate
```

không bao phủ toàn bộ `Some`.

Do đó:

```axiom
match value {
    Some(x) if x > 10 => ...
    Some(_) => ...
    None => ...
}
```

mới exhaustive.

---

# 34. Pattern matching và optimizer

Compiler có thể biến:

```axiom
match x {
    0 => a()
    1 => b()
    2 => c()
    _ => d()
}
```

thành:

```text
if-chain
binary-search
jump table
```

tùy density.

Source semantics không thay đổi.

---

# 35. Enum layout + match

Enum representation đã được quyết định là compiler-controlled.

Do đó:

```axiom
enum Option<T> {
    Some(T)
    None
}
```

compiler có thể dùng:

- explicit tag
- niche
- pointer niche
- integer sentinel
- compressed representation

miễn semantic behavior giữ nguyên.

`match` không được phép phụ thuộc vào physical tag representation.

---

# 36. `match` phải có pattern matrix compiler

Đây là điểm implementation quan trọng.

Compiler nên có phase:

```text
Pattern AST
    ↓
Pattern Matrix
    ↓
Usefulness / Exhaustiveness
    ↓
Decision Tree
    ↓
CFG
    ↓
MIR
```

Như vậy cùng một machinery xử lý:

```text
enum
tuple
struct
array
literal
range
wildcard
nested pattern
```

---

# 37. Range patterns

Nên có:

```axiom
match x {
    0..=9 => digit()
    10..=99 => two_digits()
    _ => other()
}
```

Compiler phải phân biệt:

```text
0..10
```

là half-open hay inclusive.

Tôi đề xuất giữ convention:

```text
a..b      → [a,b)
a..=b     → [a,b]
```

và chỉ cho range pattern trên type có semantics ordering phù hợp.

---

# 38. Array/slice pattern

Có thể hỗ trợ:

```axiom
match values {
    [] => empty()
    [x] => one(x)
    [first, rest...] => ...
}
```

Nhưng đây là feature compiler khá lớn.

Tôi đề xuất **có trong language design**, nhưng có thể bootstrap sau.

Không cần đưa toàn bộ vào parser/type checker MVP ngay lập tức.

---

# 39. Control flow không được implicit exception

Ví dụ:

```axiom
x[i]
```

nếu bounds sai trong safe mode:

```text
panic/trap
```

không:

```text
throw BoundsException
```

Điều này giữ runtime nhỏ.

Compiler có thể chứng minh:

```text
i < len
```

và xóa bounds check.

---

# 40. Bounds-check elimination

Ví dụ:

```axiom
for i in 0..array.len {
    sum += array[i]
}
```

Compiler có đủ thông tin để chứng minh:

```text
0 <= i < array.len
```

→ remove bounds check.

Đây là ví dụ điển hình của triết lý:

> **Safety check ở semantic level, zero-cost ở machine level khi compiler chứng minh được.**

---

# 41. `unsafe` unchecked access

Khi programmer thực sự cần:

```axiom
unsafe {
    array.get_unchecked(i)
}
```

thì không có bounds check.

Nhưng safe API vẫn là mặc định.

---

# 42. Control-flow lowering

Tất cả cuối cùng phải về CFG:

```text
if
match
while
for
loop
break
continue
return
```

→

```text
BasicBlock
Branch
Switch
Jump
Call
Return
Unreachable
```

→ MIR.

Không để backend phải hiểu `for`, `match`, `while`.

---

# 43. Control flow + ownership

Mỗi edge trong CFG phải carry state cần thiết:

```text
BB0
 │
 ├──── BB1
 │      ownership state A
 │
 └──── BB2
        ownership state B
```

Khi merge:

```text
BB1 ──┐
      ├── BB3
BB2 ──┘
```

compiler phải reconcile:

- initialized
- moved
- dropped
- capabilities
- borrowed/view
- mutable access
- variable type state

Đây là lý do ownership checking phải hoạt động trên CFG/MIR chứ không chỉ source syntax.

---

# 44. Ví dụ ownership branch

```axiom
fn foo(flag: bool) {
    let x = Resource()

    if flag {
        consume(x)
    }

    use(x)
}
```

Compiler phải reject vì:

```text
flag == true
→ x moved
→ execution reaches use(x)
```

Có thể viết:

```axiom
fn foo(flag: bool) {
    let x = Resource()

    if flag {
        consume(x)
        return
    }

    use(x)
}
```

hoặc thiết kế logic khác.

Đây là compile-time safety, không runtime cost.

---

# 45. Phi/merge semantics

Với:

```axiom
let x =
    if condition {
        A()
    } else {
        B()
    }
```

MIR có:

```text
BB1 → value A ──┐
                ├→ BB3 → x
BB2 → value B ──┘
```

Compiler có thể lower thành SSA phi hoặc machine-level equivalent.

Ownership state của `x` cũng được merge.

---

# 46. Invariants BOOTSTRAP-027

```text
ACF-20  if is an expression-capable control-flow construct.

ACF-21  if conditions require bool.

ACF-22  if branches producing a value must have a compatible type.

ACF-23  Blocks may produce values.

ACF-24  block expressions use the final expression as their value.

ACF-25  match is exhaustively checked.

ACF-26  wildcard patterns cover remaining valid cases.

ACF-27  unreachable patterns are diagnosed.

ACF-28  pattern bindings follow normal ownership semantics.

ACF-29  pattern matching does not implicitly clone values.

ACF-30  partial moves are ownership-checked.

ACF-31  custom Drop types restrict invalid partial moves.

ACF-32  if let is pattern-based conditional control flow.

ACF-33  while let is pattern-based loop control flow.

ACF-34  loop is an infinite-loop primitive.

ACF-35  loop may return a value through break.

ACF-36  break exits the innermost matching loop.

ACF-37  continue resumes loop iteration.

ACF-38  labeled loops permit structured multi-level break/continue.

ACF-39  loop exits perform required Drop operations.

ACF-40  continue performs required scope cleanup.

ACF-41  return performs required function-scope cleanup.

ACF-42  never represents non-returning computation.

ACF-43  never may inhabit any compatible expression context.

ACF-44  panic is not ordinary recoverable control flow.

ACF-45  exception handling is not a Core control-flow mechanism.

ACF-46  for is based on the iteration protocol.

ACF-47  iterator abstraction does not imply runtime allocation.

ACF-48  iterator dispatch is statically specialized when possible.

ACF-49  bounds checks may be eliminated when proven unnecessary.

ACF-50  unchecked access requires unsafe semantics.

ACF-51  range patterns have explicit inclusive/exclusive semantics.

ACF-52  pattern guards do not independently establish exhaustiveness.

ACF-53  match lowering may use branch chains, decision trees, or jump tables.

ACF-54  enum physical representation is not observable through match.

ACF-55  high-level control flow lowers to ordinary CFG/MIR.

ACF-56  backend need not understand high-level control-flow constructs.

ACF-57  ownership state is tracked across CFG edges.

ACF-58  capability state is tracked across CFG edges.

ACF-59  merge points reconcile ownership and capability states.

ACF-60  compiler optimization may transform control flow if observable semantics remain unchanged.
```

---

# 47. Một điểm rất đáng chú ý

Đến đây Axiom đã có một đặc điểm khá khác C++:

### C++ thường có:

```text
syntax
 ↓
implicit conversions
 ↓
overload resolution
 ↓
exceptions
 ↓
RAII
 ↓
templates
 ↓
virtual dispatch
 ↓
compiler-specific optimization
```

Axiom hướng tới:

```text
syntax
 ↓
static types
 ↓
explicit capabilities
 ↓
deterministic control flow
 ↓
MIR
 ↓
optimization
 ↓
machine code
```

Ít "magic" hơn ở semantic level, nhưng **nhiều optimization hơn ở compiler level**.

Đây chính xác là hướng phù hợp với mục tiêu của bạn: **đơn giản hóa ngôn ngữ mà không phải đơn giản hóa compiler**.

---

# 48. Trạng thái sau BOOTSTRAP-027

Core hiện đã có 4 lớp nền khá hoàn chỉnh:

```text
1. TYPE
   struct / enum / trait / generic / closure

2. MEMORY
   ownership / view / mut_view / pointer / storage

3. EXECUTION
   function / method / async / thread / fiber / task

4. CONTROL FLOW
   if / match / loop / while / for / return
```

và tất cả hội tụ về:

```text
Typed HIR
    ↓
MIR
    ↓
ownership/capability verification
    ↓
semantic optimization
    ↓
ABI
    ↓
LIR
    ↓
machine code
```

## Bước tiếp theo: BOOTSTRAP-028 — String, Text, Bytes, Slice & Collection Semantics

Đây là phần nên làm tiếp **trước Standard Library**, vì cần quyết định một vấn đề rất nền tảng:

- `u8[]` là bytes như thế nào
- `String` có phải UTF-8 không
- Unicode scalar value / grapheme có nằm trong Core không
- `str`/string literal là gì
- string có mutable không
- `view<[u8]>` vs text view
- slice semantics
- `Vec<T>`
- `Array`
- `Buffer`
- capacity/reallocation
- iterator
- allocation
- zero-copy
- UTF-8 validation
- FFI string
- C string / null-terminated string
- ABI representation
- và đặc biệt **làm sao xử lý Unicode mà không biến String thành một abstraction nặng và chậm**.