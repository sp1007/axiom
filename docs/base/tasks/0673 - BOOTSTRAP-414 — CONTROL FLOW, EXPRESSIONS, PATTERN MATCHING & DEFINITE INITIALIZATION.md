# BOOTSTRAP-414 — CONTROL FLOW, EXPRESSIONS, PATTERN MATCHING & DEFINITE INITIALIZATION

**Trạng thái:** SPECIFIED / FROZEN  
**Phụ thuộc:** 408–413  
**Mục tiêu:** khóa semantics của biểu thức, statement, CFG, `if`, `match`, loop, `return`, `break`, `continue`, `defer`/cleanup và definite initialization trước khi đi sâu vào optimizer/codegen.

Đây là phần nối trực tiếp giữa **source language** và MIR. Nếu control-flow semantics không chặt, ownership/drop/async verification phía sau sẽ không thể đáng tin cậy.

---

## 414.1. Nguyên tắc

Axiom dùng mô hình:

```text
Expression → produces a value
Statement  → performs an action
Block      → sequence + optional result
Terminator → ends control-flow path
```

Một block có thể trả về value:

```axiom
let x = {
    let a = 10
    let b = 20
    a + b
}
```

Giá trị của block là expression cuối cùng.

Không cần `return` cho mọi expression.

---

# 414.2. Expression không có hidden evaluation order

Axiom quy định evaluation order rõ ràng.

Ví dụ:

```axiom
f(a(), b())
```

được đánh giá theo thứ tự xác định:

```text
1. evaluate receiver nếu có
2. evaluate argument trái → phải
3. invoke function
```

Không cho backend tự đảo thứ tự nếu observable effect có thể khác.

Điều này đặc biệt quan trọng với:

- IO;
- mutation;
- atomic;
- panic;
- Drop;
- FFI.

---

# 414.3. Assignment là statement

```axiom
x = expr
```

là mutation của Place.

Semantic:

```text
evaluate expr
verify WRITE(x)
store
```

Nếu `x` chứa resource cũ, compiler phải xử lý ownership của giá trị cũ trước khi overwrite.

Không được tạo leak ngầm.

---

# 414.4. Assignment vào Drop-bearing Place

Ví dụ:

```axiom
let x = File(...)
x = other_file
```

Trước assignment:

```text
x = owned File
```

Compiler phải thực hiện semantic:

```text
drop(old x)
store(new x)
```

hoặc một transformation tương đương nếu type có assignment semantics khác.

---

# 414.5. Initialization khác Assignment

```axiom
let x: File
```

chưa tạo initialized value.

Sau:

```axiom
x = File.open(...)
```

mới:

```text
x = INITIALIZED
```

Compiler không được coi declaration đã tạo resource.

---

# 414.6. Definite Initialization

Mỗi local có state:

```text
UNINIT
INIT
PARTIAL
MOVED
DROPPED
```

Compiler phải chứng minh trước mọi READ/MOVE/DROP:

```text
value is initialized
```

Ví dụ:

```axiom
let x: i32

if condition {
    x = 10
}

print(x)
```

→ reject vì có path:

```text
condition = false
```

mà `x` chưa initialized.

---

# 414.7. Branch Refinement

Ví dụ:

```axiom
let x: Option<i32>

if x.is_some() {
    let v = x.unwrap()
}
```

Compiler có thể sử dụng semantic refinement nếu API/compiler intrinsic cung cấp proof.

Mục tiêu:

```text
condition
 ↓
refined state
 ↓
safe operation
```

nhưng không biến mọi function call thành magical theorem.

---

# 414.8. `if` là Expression

```axiom
let x = if condition {
    10
} else {
    20
}
```

Hai branch phải có compatible type.

Nếu:

```axiom
if condition {
    10
} else {
    "hello"
}
```

→ type error.

Compiler không tự tạo `Any`.

---

# 414.9. `if` không bắt buộc else

```axiom
if condition {
    do_work()
}
```

có type:

```text
unit
```

Nếu dùng như value:

```axiom
let x = if condition {
    10
}
```

→ compile error vì thiếu branch value.

---

# 414.10. `match`

`match` là exhaustive pattern expression.

```axiom
match result {
    Ok(v) => use(v)
    Err(e) => handle(e)
}
```

Compiler kiểm tra:

```text
pattern validity
exhaustiveness
unreachable arms
binding types
binding ownership
guard semantics
```

trước MIR lowering.

---

# 414.11. Exhaustiveness

Enum:

```axiom
enum Option<T> {
    Some(T)
    None
}
```

Nếu:

```axiom
match x {
    Some(v) => use(v)
}
```

→ compile error vì `None` chưa được xử lý.

Không có implicit default branch.

---

# 414.12. Wildcard Pattern

Có thể:

```axiom
match x {
    Some(v) => use(v)
    _ => fallback()
}
```

`_` phải thực sự cover phần còn lại.

Compiler vẫn phải biết các variant đã covered.

---

# 414.13. Pattern Binding Ownership

Ví dụ:

```axiom
match user {
    User { name, .. } => consume(name)
}
```

Nếu `name` là non-Copy:

```text
user.name → MOVED
```

Các field còn lại vẫn được kiểm tra theo partial-move rules.

Pattern không phải một escape khỏi ownership system.

---

# 414.14. Match Guards

```axiom
match x {
    Some(v) if v > 10 => foo(v)
    Some(v) => bar(v)
    None => baz()
}
```

Guard là boolean expression.

Quan trọng:

> Guard không được tự động được coi là exhaustiveness proof cho structural state ngoài những rule compiler định nghĩa rõ.

---

# 414.15. Pattern Evaluation Order

Pattern matching phải có deterministic evaluation.

Compiler có thể tối ưu decision tree:

```text
source order
    ↓
semantic decision tree
```

nhưng không được thay đổi:

- observable guard effects;
- move semantics;
- Drop;
- panic behavior.

---

# 414.16. `loop`

Core:

```axiom
loop {
    work()
}
```

là infinite loop về mặt control-flow trừ khi có:

```text
break
return
panic
trap
unreachable
```

Compiler có thể chứng minh function diverges.

---

# 414.17. `while`

```axiom
while condition {
    work()
}
```

condition được evaluate trước mỗi iteration.

Compiler không được giả định loop chạy ít nhất một lần.

---

# 414.18. `do-while`

Axiom có thể hỗ trợ:

```axiom
do {
    work()
} while condition
```

Nếu đưa vào Core, semantics:

```text
body executes at least once
condition evaluated after body
```

Mục tiêu là tránh phải mô phỏng bằng một `while(true)` với hidden semantics.

---

# 414.19. `for`

`for` nên là language-level sugar cho iterator protocol.

```axiom
for item in items {
    process(item)
}
```

semantic conceptually:

```text
iterator = into_iterator(items)

loop {
    match iterator.next() {
        Some(item) => process(item)
        None => break
    }
}
```

Nhưng compiler có thể lower trực tiếp để tránh abstraction overhead.

---

# 414.20. Iterator không được ép allocation

Một iterator có thể là:

```text
struct
+
state
+
next()
```

Compiler có thể:

```text
inline
unroll
vectorize
fuse
```

Không có iterator object heap bắt buộc.

---

# 414.21. `break`

`break` kết thúc loop hiện tại.

Nếu loop là expression:

```axiom
let x = loop {
    if ready() {
        break value
    }
}
```

thì `break value` cung cấp loop result.

Nếu break không có value:

```text
loop type = unit
```

trừ các semantic forms compiler định nghĩa riêng.

---

# 414.22. `continue`

`continue` chuyển đến iteration tiếp theo.

Compiler phải xác định target loop chính xác trong nested loops.

Không dùng label string matching.

Semantic identity:

```text
LoopId
```

---

# 414.23. Labels

Nếu cần nested control flow:

```axiom
'outer: loop {
    loop {
        if done {
            break 'outer
        }
    }
}
```

Label là SymbolId/LabelId.

Không phải raw text sau resolution.

---

# 414.24. `return`

`return value` kết thúc function.

Trước khi return, compiler phải thực hiện:

```text
1. evaluate return value
2. verify ownership transfer
3. execute required drops
4. release temporary capabilities
5. exit function
```

Nếu return value lấy ownership từ local:

```text
local → RETURNED
```

không được Drop local lần nữa.

---

# 414.25. Early Return

Ví dụ:

```axiom
fn f() -> Result<X, E> {
    let file = open()?

    if error {
        return Err(...)
    }

    ...
}
```

`return` phải đảm bảo:

```text
file
 ↓
DROP
 ↓
RETURN
```

Đây là một trong những lý do Drop phải được explicit hóa trong MIR.

---

# 414.26. `?` Operator

Axiom có thể hỗ trợ error propagation:

```axiom
let x = read()?
```

Semantic:

```text
match read() {
    Ok(v) => v
    Err(e) => return Err(e)
}
```

Compiler có thể lower trực tiếp nhưng semantics phải tương đương.

Ownership của error/value phải được bảo toàn.

---

# 414.27. `?` không phải exception

`?`:

```text
Result/Option propagation
```

không tạo:

```text
throw
catch
exception object
stack unwinding
```

trừ khi programmer/library explicit dùng panic/unwind.

Điều này giữ error path predictable.

---

# 414.28. `defer` / Scope Cleanup

Axiom cần một mechanism cho cleanup logic ngoài Drop.

Đề xuất Core:

```axiom
defer {
    close_transaction()
}
```

Semantics:

> Block được thực hiện khi control flow rời khỏi lexical scope theo bất kỳ đường nào hợp lệ.

Bao gồm:

```text
normal fallthrough
return
break
continue
panic/unwind
```

nếu profile sử dụng unwind.

---

# 414.29. `defer` không phải Drop

Hai khái niệm khác nhau:

```text
Drop
    type-level resource destruction

defer
    scope-level arbitrary cleanup action
```

Ví dụ:

```axiom
defer {
    log("leaving scope")
}
```

không biến scope thành object/resource.

---

# 414.30. Defer Capture

Compiler phải phân tích capture của `defer` giống closure.

```axiom
defer {
    commit(transaction)
}
```

Nếu `transaction` được MOVE vào cleanup:

```text
transaction ownership
```

phải được cập nhật.

Không được có:

```text
use-after-move
double-drop
```

---

# 414.31. Defer Ordering

Nếu có:

```axiom
defer A
defer B
```

khi scope kết thúc:

```text
B
A
```

theo LIFO.

Điều này phù hợp với nesting resource acquisition.

Drop và defer phải có ordering được định nghĩa rõ.

Đề xuất:

```text
later registered cleanup
    ↓
earlier registered cleanup
    ↓
type Drop
```

nhưng implementation phải biểu diễn ordering explicit trong MIR.

---

# 414.32. Panic

Axiom phân biệt:

```text
panic
trap
abort
unwind
```

Profile có thể chọn panic strategy.

Trong `abort`:

```text
panic → process termination
```

Trong `unwind`:

```text
panic
 ↓
stack unwinding
 ↓
cleanup/defer/drop
```

MIR semantics không được phụ thuộc vào profile để trở nên type-incorrect.

---

# 414.33. `never`

Expression:

```axiom
panic(...)
```

có type:

```text
never
```

`never` có thể coerce vào mọi expected type vì nó không return.

Ví dụ:

```axiom
let x: i32 = if condition {
    10
} else {
    panic("error")
}
```

hợp lệ.

---

# 414.34. Divergence Analysis

Compiler nhận diện các path:

```text
RETURN
PANIC
TRAP
UNREACHABLE
INFINITE_LOOP
```

là terminating hoặc diverging.

Điều này hỗ trợ:

- definite initialization;
- exhaustiveness;
- dead-code detection;
- optimization.

---

# 414.35. Unreachable Code

Sau:

```axiom
panic(...)
```

statement tiếp theo:

```axiom
use(x)
```

là unreachable.

Compiler có thể warning/error tùy diagnostic level.

Nhưng `UNREACHABLE` chỉ được sinh khi semantic analysis chứng minh được.

---

# 414.36. CFG Normal Form

MIR control-flow graph phải có:

```text
BasicBlock
    statements*
    terminator
```

và terminator luôn thuộc tập hợp hợp lệ.

Không có basic block “rơi tự do” mà không có terminator.

---

# 414.37. CFG Verification

Compiler kiểm tra:

```text
all blocks reachable or intentionally dead
all edges valid
all terminators valid
dominance valid
predecessors/successors consistent
phi inputs complete
loop backedges valid
return types valid
```

Nếu CFG sai:

```text
compiler bug / ICE
```

chứ không phải program semantic error.

---

# 414.38. Definite Initialization trên CFG

Algorithm:

```text
Entry:
    parameters = INIT
    locals = UNINIT

For each block:
    IN[state] = intersection of predecessor OUT states

Transfer:
    INIT(x)   → x = INIT
    MOVE(x)   → x = MOVED
    DROP(x)   → x = DROPPED
    ASSIGN(x) → x = INIT
```

State merge phải conservative.

Ví dụ:

```text
Path A: INIT
Path B: UNINIT

merge:
    MAYBE_INIT
```

READ yêu cầu:

```text
DEFINITELY_INIT
```

---

# 414.39. Ownership và Initialization khác nhau

Một value có thể:

```text
initialized + moved
```

hoặc:

```text
initialized + borrowed
```

Do đó không dùng một boolean:

```text
is_valid
```

để biểu diễn tất cả.

Compiler phải giữ các dimensions:

```text
Initialization
Ownership
Capability
Drop
```

độc lập.

---

# 414.40. Temporary Values

Expression:

```axiom
foo(make_data())
```

tạo temporary.

Compiler phải xác định:

```text
creation
use
destruction
```

deterministically.

Temporary Drop không được kéo dài tùy tiện nếu nó làm thay đổi observable behavior.

Nhưng compiler có thể eliminate temporary khi semantics không thay đổi.

---

# 414.41. Lifetime Extension

Compiler có thể extend physical lifetime để:

- register allocation;
- stack reuse;
- optimization.

Nhưng semantic lifetime của resource vẫn phải tuân thủ Drop ordering.

Không được biến:

```text
drop event
```

thành một thời điểm tùy ý nếu destructor có observable effect.

---

# 414.42. Short-Circuit Operators

```axiom
a && b
a || b
```

không phải arithmetic operators thông thường.

`&&`:

```text
evaluate a
if false → result false
else evaluate b
```

`||`:

```text
evaluate a
if true → result true
else evaluate b
```

Do đó:

```text
b
```

có thể không được evaluate.

Ownership/effect analysis phải path-sensitive.

---

# 414.43. Null-Coalescing Không phải Core primitive

Axiom không cần:

```text
a ?? b
```

như một null operator vì Core không có `null`.

Với `Option<T>`:

```axiom
match x {
    Some(v) => v
    None => fallback()
}
```

hoặc library/compiler sugar sau này.

---

# 414.44. Boolean không tự động là Integer

Không cho:

```axiom
let x: i32 = true
```

hoặc:

```axiom
if 1 { ... }
```

Boolean và integer là hai type semantic khác nhau.

Điều này giúp optimizer và diagnostics deterministic.

---

# 414.45. Control-flow và Capability

Compiler phải kiểm tra capability trên từng path.

Ví dụ:

```axiom
if has_permission {
    write_file()
}
```

Nếu `has_permission` chỉ là runtime bool, compiler **không được** coi nó là compile-time capability proof.

Capability phải đến từ:

```text
typed capability
compiler proof
explicit trusted boundary
```

chứ không phải một boolean thông thường.

---

# 414.46. Control-flow và Effects

Branch:

```axiom
if condition {
    write_file()
}
```

Function effect:

```text
MAY(FS_WRITE)
```

không phải:

```text
MUST(FS_WRITE)
```

Compiler có thể lưu path-sensitive effect information:

```text
Path A → FS_WRITE
Path B → PURE
```

Điều này hữu ích cho:

- optimization;
- security;
- static analysis;
- AI explanation.

---

# 414.47. Control-flow và Async

Không được `await` tùy tiện trong context không async.

```axiom
fn f() {
    await x
}
```

→ compile error.

Trong async:

```axiom
async fn f() {
    let x = await io()
}
```

MIR tạo suspension point.

Definite initialization và ownership state phải được bảo toàn qua suspension.

---

# 414.48. Control-flow và Concurrency

Compiler phải nhận diện:

```text
spawn
join
channel send/receive
lock/unlock
atomic
```

như control-flow/resource operations.

Ví dụ lock:

```axiom
lock(m)
...
unlock(m)
```

mọi path thoát scope phải xử lý lock semantics.

Library RAII guard có thể dùng Drop để đảm bảo điều này.

---

# 414.49. Control-flow và GPU

Kernel không được chứa control-flow operation bị GPU legality rules cấm.

Ví dụ:

```text
filesystem
socket
blocking OS call
```

→ reject ở semantic verification.

Nhưng:

```text
if
loop
match
branch
```

được phép nếu GPU backend hỗ trợ.

Compiler có thể transform:

```text
branch
→ predication
```

khi target optimization cho phép.

---

# 414.50. CompilerDB

Thêm:

```text
ControlFlowDB
BasicBlockDB
DefiniteInitDB
PatternDB
MatchExhaustivenessDB
LoopDB
DeferDB
CleanupDB
DivergenceDB
PathEffectDB
```

MIRDB từ 413 là nơi materialize kết quả cuối.

---

# 414.51. Proof Artifacts

```text
CFGProof
DefiniteInitializationProof
PatternExhaustivenessProof
PatternOwnershipProof
DropPathProof
DeferOrderingProof
DivergenceProof
LoopControlProof
ReturnOwnershipProof
ShortCircuitProof
CleanupProof
```

Ví dụ:

```text
ReturnOwnershipProof

return value:
    x

ownership:
    x = OWNED

local state:
    x = RETURNED

drop(x):
    forbidden after transfer

result:
    valid
```

---

# 414.52. Invariants `ACFG`

```text
ACFG-01  Every expression has a deterministic evaluation order.
ACFG-02  Every block has a well-defined result type.
ACFG-03  Every basic block has exactly one terminator.
ACFG-04  CFG edges are explicit and valid.
ACFG-05  Definite initialization is path-safe.
ACFG-06  Uninitialized values cannot be read.
ACFG-07  Moved values cannot be reused.
ACFG-08  Dropped values cannot be reused.
ACFG-09  Partial initialization is tracked field-sensitively.
ACFG-10  If-expressions have compatible branch types.
ACFG-11  Match expressions are exhaustive.
ACFG-12  Unreachable match arms are diagnosed.
ACFG-13  Pattern bindings preserve ownership semantics.
ACFG-14  Guards cannot silently alter exhaustiveness rules.
ACFG-15  Loop control targets are semantically identified.
ACFG-16  Break values have a valid loop result type.
ACFG-17  Continue targets are valid loop scopes.
ACFG-18  Return paths preserve ownership correctness.
ACFG-19  Early returns execute required cleanup.
ACFG-20  Temporary destruction is deterministic.
ACFG-21  Defer cleanup ordering is deterministic.
ACFG-22  Drop ordering is deterministic.
ACFG-23  Panic semantics remain distinct from normal return.
ACFG-24  Never expressions may terminate any expected type.
ACFG-25  Divergence analysis is sound.
ACFG-26  Short-circuit evaluation is preserved.
ACFG-27  Effect analysis respects path conditions.
ACFG-28  Async suspension preserves initialization/ownership state.
ACFG-29  Control-flow verification completes before codegen.
ACFG-30  Invalid CFG cannot reach optimization/codegen.
```

---

# 414.53. Source → MIR Example

Source:

```axiom
fn process(x: Option<File>) -> Result<Text, Error> {
    let file = match x {
        Some(f) => f
        None => return Err(Error.missing())
    }

    defer {
        log("finished")
    }

    let text = file.read()?
    Ok(text)
}
```

Semantic CFG conceptually:

```text
BB0
 │
 │ match x
 ├───────────────┐
 ▼               ▼
Some(f)         None
 │               │
 │ move f        │ return Err
 ▼               │
BB1              │
 │               │
 │ register      │
 │ defer         │
 ▼               │
read(file)       │
 │               │
 ├── Err ────────┘
 │
 ▼
Ok(text)
 │
 ▼
defer cleanup
 │
 ▼
return
```

Compiler phải chứng minh:

```text
x ownership
f ownership
file ownership
read capability
error propagation
defer execution
Drop ordering
return ownership
```

trước khi codegen.

---

# 414.54. Kết quả của BOOTSTRAP-414

Axiom hiện có một semantic chain tương đối hoàn chỉnh:

```text
408  Name Resolution
 ↓
409  Type System
 ↓
410  Trait / Method / Overload
 ↓
411  Ownership / Capability / Effect
 ↓
412  Closure / Callable
 ↓
413  MIR
 ↓
414  Control Flow / Initialization / Cleanup
```

Điểm quan trọng nhất của 414:

> **Mọi đường đi của chương trình đều phải được compiler mô hình hóa rõ ràng. Ownership, Drop, Capability và Effect không được dựa trên “đoán” từ source; chúng phải được kiểm chứng trên CFG/MIR theo từng path.**

Với nền này, bước tiếp theo hợp lý là đi sâu vào **Drop Elaboration & Resource Lifetime Lowering** — tức biến toàn bộ ownership/drop semantics hiện tại thành một cơ chế cleanup có thể codegen chính xác và tối ưu mạnh.