Tiếp tục. Phần này thực ra **đã có nền tảng từ Core v0.1**, nên tôi sẽ không thiết kế lại từ đầu. Ta sẽ nâng nó thành một **Error/Failure Model v0.1 hoàn chỉnh**, đồng thời khóa cách `?`, `Drop`, `panic`, `trap`, FFI và async tương tác với nhau.

# Axiom Error & Failure Model v0.1

Tôi đề xuất Axiom **không có một “error system” duy nhất**.

Có 5 loại tình huống khác nhau:

```text id="e9j4ka"
                    Failure / Exit
                         │
        ┌────────────────┼────────────────┐
        │                │                │
    Recoverable      Abnormal         Hardware/
       Error           Exit             Machine
        │                │                │
     Result            Panic             Trap
        │                │                │
        ▼                ▼                ▼
   caller handles   program/profile   CPU/OS boundary
```

Ngoài ra:

```text
return / break / continue
```

là **normal structured control flow**, không phải error.

---

# 1. `Result<T, E>` là error thông thường

Ví dụ:

```axiom
fn read_file(path: Text) -> Result<Bytes, IoError>
```

Có hai trạng thái:

```text
Ok(Bytes)
Err(IoError)
```

Caller quyết định:

```axiom
match read_file(path) {
    Ok(data) => process(data),
    Err(e) => report(e)
}
```

Không có runtime exception.

---

# 2. `Result` là ordinary enum

Điều này rất quan trọng.

Về semantic:

```text
Result<T,E>
```

chỉ là:

```text
enum Result<T,E> {
    Ok(T),
    Err(E)
}
```

Compiler có thể nhận biết để tối ưu, nhưng không cần một object/runtime đặc biệt.

Do đó:

```text
Result
 ↓
MIR
 ↓
branch / switch
```

chứ không phải:

```text
throw
 ↓
exception runtime
 ↓
stack search
```

---

# 3. `?` là control-flow sugar

Ví dụ:

```axiom
fn load() -> Result<Data, Error> {
    let a = read_a()?;
    let b = read_b()?;
    Ok(combine(a, b))
}
```

Không có exception.

Conceptually:

```text
read_a()
 ↓
switch
 ├── Ok(a) → continue
 └── Err(e) → cleanup → return Err(e)
```

---

# 4. Lowering của `?`

Ví dụ:

```axiom
let x = foo()?;
```

HIR có thể biểu diễn:

```text
Try {
    value = Call(foo)
    success = ...
    failure = ...
}
```

MIR:

```text
r = CALL foo()

switch r.tag {
    Ok  → bb_ok
    Err → bb_err
}

bb_ok:
    x = payload(r)
    ...

bb_err:
    e = payload(r)
    cleanup
    return Err(e)
```

Không cần exception table.

---

# 5. `?` phải hỗ trợ conversion

Có thể cho:

```axiom
fn foo() -> Result<T, MyError> {
    bar()?
}
```

nếu:

```text
bar() -> Result<T, E>
```

và có conversion:

```text
E → MyError
```

Nhưng conversion phải **explicitly defined by error propagation rules**, không được trở thành implicit conversion tổng quát.

Ví dụ:

```axiom
impl From<FileError> for AppError
```

cho phép:

```axiom
read_file()? 
```

được chuyển thành `AppError`.

Nhưng không vì vậy mà:

```axiom
FileError
```

tự động convert thành `AppError` ở mọi context.

---

# 6. `?` không chỉ dành cho Result

Tôi đề xuất thiết kế generic hơn:

```text
Try-like protocol
```

Nhưng **không cần expose trait phức tạp trong v0.1**.

Ban đầu:

```text
?
```

chỉ hỗ trợ:

```text
Result<T,E>
Option<T>
```

Sau này mới xem xét generalized `Try`.

Điều này tránh biến một syntax đơn giản thành một trait-solving nightmare.

---

# 7. `Option<T>?`

Ví dụ:

```axiom
fn find_user(id: Id) -> Option<User> {
    let user = database.find(id)?;
    Some(user)
}
```

Semantics:

```text
Some(x) → continue
None    → return None
```

Không phải error object.

Do đó cần phân biệt:

```text
Result<T,E> → thất bại có thông tin lỗi
Option<T>   → có hoặc không có giá trị
```

---

# 8. `panic` là hoàn toàn khác

Ví dụ:

```axiom
panic("internal invariant violated")
```

Đây không phải:

```text
Err(...)
```

vì caller không được yêu cầu xử lý như recoverable error.

Semantic:

```text
panic()
 ↓
abnormal control flow
```

---

# 9. Panic có profile

Axiom nên có:

```text
--panic=abort
--panic=unwind
```

### Abort

```text
panic
 ↓
cleanup required resources
 ↓
abort/terminate
```

Minimal binary.

### Unwind

```text
panic
 ↓
unwind
 ↓
cleanup frames
 ↓
termination / boundary handler
```

Thêm runtime/metadata.

---

# 10. Nhưng không có `catch` trong Core v0.1

Tôi vẫn giữ quyết định này.

Không:

```axiom
try {
   ...
} catch e {
   ...
}
```

và không:

```axiom
throw e
```

trong Core.

Lý do không phải vì exception “xấu”, mà vì nó làm semantics:

```text
control flow
+
cleanup
+
ABI
+
async
+
FFI
```

phức tạp hơn rất nhiều.

Axiom có thể thêm một library/profile abstraction sau này nếu thực sự cần.

---

# 11. Panic không được dùng thay Result

Compiler không cấm programmer viết:

```axiom
panic("file not found")
```

nhưng API chuẩn nên phân biệt:

```text
recoverable → Result
programmer invariant → panic
hardware invalidity → trap
```

Đây là semantic distinction.

---

# 12. Trap

`trap` là mức thấp hơn panic.

Ví dụ:

```text
division by zero
invalid machine operation
explicit unreachable
hardware fault
```

Conceptually:

```text
trap
 ↓
machine/OS boundary
```

Không nhất thiết có Axiom panic message/runtime.

---

# 13. `unreachable() -> never`

Ví dụ:

```axiom
match state {
    Ready => run(),
    Closed => close(),
    Invalid => unreachable()
}
```

`unreachable()` có type:

```text
never
```

Nó không tạo một value.

---

# 14. `never` giải quyết control-flow rất đẹp

Ví dụ:

```axiom
fn get(x: Option<i64>) -> i64 {
    match x {
        Some(v) => v,
        None => panic("missing")
    }
}
```

Các arm:

```text
Some → i64
None → never
```

Compiler unify thành:

```text
i64
```

Không cần special-case syntax.

---

# 15. Return cũng là diverging control flow

Ví dụ:

```axiom
fn foo() -> i64 {
    if condition {
        return 42;
    }

    10
}
```

`return` về semantic có thể xem là:

```text
ControlExit
```

không tạo value.

MIR xử lý bằng terminator:

```text
RETURN
```

---

# 16. Cleanup là phần bắt buộc

Đây là nơi Error Model nối trực tiếp vào Ownership Model.

Ví dụ:

```axiom
fn foo() -> Result<i64, Error> {
    let file = open()?;
    let buffer = allocate()?;

    process(file, buffer)
}
```

Nếu:

```text
allocate() → Err
```

thì `file` phải được cleanup trước:

```text
Err
 ↓
cleanup buffer if owned
 ↓
cleanup file
 ↓
return Err
```

Không được:

```text
return Err
```

và bỏ qua Drop.

---

# 17. Cleanup order

Giữ nguyên rule:

> **Reverse initialization/dependency order.**

Ví dụ:

```axiom
let a = acquire_a();
let b = acquire_b();
let c = acquire_c();
```

khi exit:

```text
drop c
drop b
drop a
```

Nhưng partial move phải được xử lý.

---

# 18. `?` không tạo hidden exception

Đây là invariant cực quan trọng.

```text
AXE-01:
? must lower to ordinary control flow.
```

Do đó:

```text
? cost
```

thường chỉ là:

```text
branch
move payload
cleanup
return
```

Compiler có thể tối ưu branch/cleanup nếu biết không cần.

---

# 19. Result ABI

Ví dụ:

```axiom
fn parse() -> Result<i64, ParseError>
```

Compiler có thể lower thành:

```text
RAX = value
RDX = status
```

hoặc:

```text
RAX = packed representation
```

hoặc caller-allocated return.

Source không biết.

Do đó:

```text
Result
```

không nhất thiết tạo memory object.

---

# 20. Error type cũng là ordinary type

Ví dụ:

```axiom
enum ParseError {
    InvalidDigit
    Overflow
    UnexpectedEnd
}
```

Compiler có thể biểu diễn:

```text
u8
```

nếu không có payload.

Nếu:

```axiom
enum ParseError {
    InvalidDigit { index: usize }
    Overflow
    UnexpectedEnd
}
```

layout tùy compiler.

Không cần:

```text
heap-allocated exception object
```

---

# 21. Error propagation qua async

Ví dụ:

```axiom
async fn load() -> Result<Data, Error> {
    let a = await fetch_a()?;
    let b = await fetch_b()?;
    Ok(combine(a,b))
}
```

State machine phải giữ:

```text
a
b
pending state
```

tại suspension point.

Nếu `fetch_b()` trả:

```text
Err
```

thì state machine:

```text
Err
 ↓
cleanup owned state
 ↓
return Err
```

Không cần throw qua executor.

---

# 22. Panic trong async

Nếu:

```text
panic
```

trong async task:

```text
task state
 ↓
panic profile
```

với abort:

```text
terminate
```

với unwind:

```text
unwind task/frame
```

Executor không phải semantic owner của panic.

Nó chỉ là scheduler/runtime layer.

---

# 23. Cancellation

Cancellation **không phải error**.

Ví dụ:

```text
task.cancel()
```

không nhất thiết:

```text
Err(Cancelled)
```

Ở language level:

```text
SUSPEND
RESUME
DROP task state
```

Library có thể thiết kế:

```text
Result<T, Cancelled>
```

nếu API muốn cancellation observable.

Nhưng cancellation mechanism và error model không nên trộn lẫn.

---

# 24. Thread failure

Thread function:

```axiom
fn worker() -> Result<(), Error>
```

có thể return error.

Thread handle:

```text
JoinHandle<Result<(), Error>>
```

Caller:

```axiom
let result = handle.join()?;
```

Đây là ordinary value propagation.

Không cần thread exception runtime.

---

# 25. FFI error

FFI rất phức tạp vì C có nhiều kiểu:

```text
errno
return code
NULL
sentinel
out parameter
exception/SEH
```

Axiom không nên tự đoán.

Ví dụ:

```axiom
extern "C" fn fopen(...) -> *mut CFile
```

Compiler chỉ biết:

```text
FFI
unsafe boundary
```

Không tự biến NULL thành `Option`.

Wrapper library mới làm:

```axiom
fn open(...) -> Result<File, IoError>
```

---

# 26. FFI contract

Có thể sau này cho:

```axiom
@ffi_effects(read, write)
extern "C" fn foo(...);
```

Nhưng v0.1 nếu thiếu thông tin:

```text
FFI = UNKNOWN
```

Verifier/optimizer phải conservative.

Không được giả định:

```text
extern fn foo()
```

là pure.

---

# 27. Hardware fault

Ví dụ:

```text
page fault
SIGSEGV
access violation
illegal instruction
```

không nên tự động trở thành:

```text
Result<_, Error>
```

vì đó là machine/OS-level failure.

Safe Axiom code phải không tạo ra những tình huống invalid đó.

Unsafe code chịu trách nhiệm.

---

# 28. Integer overflow

Ta đã quyết định không dùng C-style silent UB.

Axiom có thể có explicit arithmetic modes:

```text
checked
wrapping
saturating
```

Ví dụ conceptual:

```axiom
let x = checked_add(a, b)?;
```

hoặc compiler có operator/profile semantics.

Tôi nghiêng về:

```text
default integer arithmetic = checked in debug/defined profile?
```

nhưng **điểm này chưa nên freeze vội** vì nó ảnh hưởng performance và language ergonomics.

Có thể tốt hơn là syntax rõ:

```text
a + b        // defined arithmetic semantics
a &+ b       // wrapping
a &+? b      // checked result
a saturating_add b
```

Phần operator syntax nên chốt sau.

---

# 29. Division

Division cũng cần defined semantics:

```text
x / 0
```

không được UB.

Có thể:

```text
integer divide by zero → trap
```

và:

```text
MIN_INT / -1
```

phải có semantics rõ.

Tôi đề xuất:

> **Các lỗi arithmetic không recoverable mặc định → trap, không panic.**

Nếu muốn recoverable:

```axiom
checked_div(a,b)
```

trả:

```text
Option/Result
```

Điều này rất hợp systems programming.

---

# 30. Bounds checking

Array:

```axiom
a[i]
```

safe semantics:

```text
if i < len:
    access
else:
    panic/trap according to profile
```

Compiler có thể prove:

```text
0 <= i < len
```

và xóa check.

Do đó:

```text
safe ≠ slow
```

và đây là một trong những nhiệm vụ quan trọng nhất của optimizer.

---

# 31. `unsafe` không biến mọi failure thành hợp lệ

Nếu:

```axiom
unsafe {
    *ptr
}
```

thì compiler cho phép raw memory access.

Nhưng:

```text
unsafe
```

không có nghĩa:

```text
mọi behavior đều có semantic guarantee
```

Nó có nghĩa:

> programmer đã nhận trách nhiệm đối với invariant mà compiler không thể chứng minh.

---

# 32. Error taxonomy chính thức

Tôi đề xuất khóa:

```text
NORMAL
├── expression
├── branch
├── loop
├── return
├── break
└── continue

RECOVERABLE
└── Result / Option

ABNORMAL LANGUAGE EXIT
└── Panic

MACHINE/ENVIRONMENT FAILURE
└── Trap

EXTERNAL BOUNDARY
└── FFI / OS error
```

---

# 33. Không có “universal Error”

Tôi **không khuyến nghị**:

```axiom
trait Error {}
```

rồi mọi API:

```text
Result<T, Error>
```

vì điều đó khuyến khích type erasure.

Tốt hơn:

```text
Result<T, FileError>
Result<T, ParseError>
Result<T, NetworkError>
```

Caller có thể aggregate khi cần:

```text
AppError
```

---

# 34. Error composition

Ví dụ:

```axiom
enum AppError {
    Io(IoError)
    Parse(ParseError)
    Network(NetworkError)
}
```

và:

```axiom
fn run() -> Result<Data, AppError>
```

Compiler không cần special error hierarchy.

Đây chỉ là ADT.

---

# 35. Error context

Không cần exception stack.

Có thể:

```axiom
enum AppError {
    Io {
        source: IoError
        path: Text
    }
}
```

hoặc library cung cấp:

```text
.with_context(...)
```

Đây là data, không phải runtime mechanism.

---

# 36. Panic message

Panic message không nên mặc định kéo theo một runtime string object.

Ví dụ:

```axiom
panic("unreachable")
```

Compiler có thể đưa literal vào:

```text
.rodata
```

và abort.

Nếu:

```text
--panic=abort
```

runtime cực nhỏ.

---

# 37. `panic=abort` có thể gần như zero runtime

Ví dụ:

```axiom
fn main() {
    panic("bad state")
}
```

native có thể gần như:

```text
load message
call minimal abort
```

Không cần:

- exception runtime;
- unwinder;
- heap;
- GC;
- thread runtime.

---

# 38. Panic boundary

Nếu library không muốn panic lan ra ngoài:

```axiom
fn api() -> Result<T, E>
```

thì library nên tự xử lý recoverable conditions.

Không nên dùng:

```text
panic → catch → Result
```

làm API design thông thường.

---

# 39. FFI panic boundary

Một vấn đề cực quan trọng:

> **Axiom panic không được mặc định xuyên qua C ABI boundary.**

Ví dụ:

```axiom
extern "C" fn callback()
```

Nếu callback panic:

```text
panic
 ↓
must terminate / catch at Axiom boundary
```

không được tự ý unwind qua foreign stack frame.

Điều này cần được verifier/ABI layer enforce.

---

# 40. FFI Result boundary

Tương tự:

```axiom
extern "C" fn foo() -> Result<T,E>
```

không thể mặc định coi là C-compatible.

Muốn export:

```text
Result
```

qua C cần wrapper:

```text
Result<T,E>
 ↓
C ABI representation
 ↓
status + out parameter
```

Ví dụ conceptual:

```text
int foo(T* out);
```

Axiom compiler không tự đoán.

---

# 41. Error model và optimizer

Compiler có thể biết:

```text
foo() -> Result<T,E>
```

và nếu static analysis chứng minh:

```text
Err branch impossible
```

thì có thể loại bỏ branch.

Ví dụ:

```text
parse_constant("123")
```

được compile-time evaluate.

Kết quả:

```text
Ok(123)
```

→ không còn error branch.

Đây là **compile-time execution + Result + abstraction erasure** kết hợp rất mạnh.

---

# 42. Error model và zero-cost abstraction

Ví dụ:

```axiom
fn divide(a: i64, b: i64) -> Result<i64, DivError>
```

compiler có thể lower:

```text
idiv
jo/trap/branch
```

Không nhất thiết tạo object.

Do đó `Result` có thể có abstraction cost gần như:

```text
status register + branch
```

---

# 43. Error invariants

Tôi đề xuất thêm:

### AERR-01 — Result Is Ordinary Data
`Result` không yêu cầu exception runtime.

### AERR-02 — Option Is Not Error
`Option` biểu diễn presence/absence, không phải exception.

### AERR-03 — Question Mark Is Control Flow
`?` lower thành branch/move/cleanup/return.

### AERR-04 — Panic Is Not Recoverable Error
Panic không thay thế Result.

### AERR-05 — Trap Is Machine Boundary
Trap không tự động trở thành Result/Panic.

### AERR-06 — Cleanup Is Mandatory
mọi abnormal exit phải thực hiện required cleanup.

### AERR-07 — No Exception Runtime in Core
Core v0.1 không có throw/catch exception system.

### AERR-08 — FFI Boundary Safety
Panic/unwind không được vượt foreign ABI boundary mặc định.

### AERR-09 — Error Conversion Is Explicitly Governed
Không có implicit universal error conversion.

### AERR-10 — Error Representation Is Optimizable
Result/Option representation compiler-controlled.

### AERR-11 — Panic Profile
Abort/unwind là build/runtime profile.

### AERR-12 — Recoverable vs Fatal Separation
Recoverable conditions và fatal/invariant failures là các semantic classes khác nhau.

---

# 44. Toàn bộ control-flow model lúc này

Axiom có thể được mô hình hóa cực rõ:

```text
                         CONTROL FLOW
                              │
          ┌───────────────────┼───────────────────┐
          │                   │                   │
        NORMAL             RECOVERABLE          ABNORMAL
          │                   │                   │
   ┌──────┼──────┐         Result             Panic
   │      │      │            │                  │
 if     loop   return         ?                  │
 match  break                  │                  │
        continue               ▼                  ▼
                           cleanup             cleanup
                              │                  │
                              ▼                  ▼
                           return            abort/unwind
                                                 │
                                                 ▼
                                               Trap
```

Điều này rất hợp với kiến trúc MIR hiện tại.

---

## Một quyết định kiến trúc rất đáng chú ý

Sau phần này, Axiom có một đặc điểm mà tôi nghĩ nên trở thành **nguyên tắc chính thức**:

> **Axiom không có “exception mechanism” làm nền tảng control flow.**

Thay vào đó:

```text
Result  → explicit data flow
?       → explicit control-flow lowering
panic   → abnormal language exit
trap    → machine/OS failure
return  → structured exit
```

Điều này giúp compiler cực kỳ dễ reason:

```text
Typed MIR
   ↓
Ownership verification
   ↓
Drop elaboration
   ↓
Control-flow verification
   ↓
Optimization
```

Không cần một “hidden control-flow universe” để theo dõi exception propagation.

---

### Bước tiếp theo nên đi vào một phần còn quan trọng hơn: **Closure + Function + Calling Convention + Capture Model**

Vì hiện chúng ta đã nói:

```text
function
closure
generic
trait
dyn Trait
ownership
view
async
```

nhưng chưa khóa chính xác:

- closure capture **by value / read / mutable / move**;
- closure có representation gì;
- captureless closure có convert thành function pointer không;
- closure có thể return từ function không;
- closure có thể chứa `view<T>` không;
- closure qua `async/await` thế nào;
- function pointer và closure phân biệt ra sao;
- callback C ABI xử lý thế nào;
- compiler làm sao **eliminate hoàn toàn closure allocation** khi closure không escape.

Đây là mảnh ghép cuối của **call model**, và nó ảnh hưởng trực tiếp đến cả performance lẫn độ đơn giản của Axiom.