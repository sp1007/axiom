Tiếp tục với **ERROR-001 + PANIC-001**. Đây là phần cần chốt kỹ vì error handling ảnh hưởng trực tiếp đến **ABI, control flow, binary size, async, Drop, FFI và performance**.

# ERROR-001 — Error Model

## 1. Quyết định nền tảng

Axiom nên có **4 trạng thái hoàn toàn khác nhau**:

```text
Value
Result
Panic
Trap
```

Không gom tất cả thành một “exception system”.

```text
┌──────────────┐
│ Normal value │
└──────────────┘

┌──────────────┐
│ Result<T, E> │ ← recoverable failure
└──────────────┘

┌──────────────┐
│ Panic        │ ← unrecoverable program-level failure
└──────────────┘

┌──────────────┐
│ Trap         │ ← machine/OS/runtime fault
└──────────────┘
```

---

# 2. `Result<T, E>` là cơ chế lỗi chính

Ví dụ:

```text
fn read_file(path: Path) -> Result<Data, IoError>
```

và:

```text
let data = read_file(path)?;
```

`?` chỉ là syntax sugar.

Về semantics:

```text
match read_file(path) {
    Ok(x) => x,
    Err(e) => return Err(e),
}
```

Không có exception table.

Không có stack unwinding.

Không cần runtime.

---

# 3. `Result` phải là zero-cost abstraction

Ví dụ:

```text
fn divide(a: i32, b: i32) -> Result<i32, DivError>
```

Compiler có thể biến thành:

```text
eax = result
edx = discriminant
```

hoặc tận dụng ABI register pair.

Không có:

```text
heap allocation
exception object
GC
runtime dispatcher
```

---

# 4. `Result` không đồng nghĩa error object

Không nên thiết kế:

```text
Error {
    message: String,
    stacktrace: ...
}
```

làm representation mặc định.

Ví dụ:

```text
enum IoError {
    NotFound,
    PermissionDenied,
    TimedOut,
    ...
}
```

có thể chỉ là một integer/discriminant.

Nếu muốn message:

```text
IoError {
    kind,
    raw_code
}
```

và formatting xảy ra khi cần.

---

# 5. Error payload có thể lớn

```text
Result<T, E>
```

không giới hạn `E`.

Ví dụ:

```text
Result<Response, HttpError>
```

với:

```text
struct HttpError {
    status: u16,
    message: String,
}
```

Compiler xử lý như aggregate bình thường.

---

# 6. `?` phải cực nhẹ

Ví dụ:

```text
fn load() -> Result<Data, Error> {
    let x = step1()?;
    let y = step2(x)?;
    return Ok(y);
}
```

MIR:

```text
x = call step1
switch x {
    Ok -> ...
    Err -> return Err
}
```

Không có hidden control runtime.

---

# 7. Error conversion

Một vấn đề quan trọng:

```text
step1() -> Result<T, A>
```

nhưng function trả:

```text
Result<T, B>
```

Có nên tự động:

```text
A → B
```

?

Tôi đề xuất:

> **Chỉ cho phép implicit error conversion khi có một conversion rule rõ ràng và không gây ambiguity.**

Ví dụ trait:

```text
trait From<A> for B
```

thì:

```text
? 
```

có thể thực hiện conversion.

Nhưng compiler không được đoán bằng hàng chục conversion path.

---

# 8. Không có implicit stringification của Error

Không:

```text
return "something went wrong";
```

nếu function yêu cầu:

```text
Result<T, MyError>
```

Trừ khi type conversion thực sự tồn tại.

Điều này giữ type system sạch.

---

# 9. `Option<T>` khác `Result<T,E>`

`Option`:

> Giá trị có thể không tồn tại.

```text
find_user(id) -> Option<User>
```

`Result`:

> Operation có thể thất bại và failure có thông tin.

```text
load_user(id) -> Result<User, DbError>
```

Không nên dùng `Result<T, ()>` để thay thế mọi `Option<T>`.

---

# 10. `panic`

Panic là:

> **unrecoverable semantic failure ở mức chương trình/thread/task.**

Ví dụ:

```text
panic("invariant violated")
```

Panic không phải:

```text
Result<T,E>
```

và không nên catch mặc định.

---

# 11. Panic profile

Axiom nên có ít nhất:

```text
panic = abort
panic = unwind
```

### Abort

```text
panic
 ↓
cleanup policy
 ↓
terminate process
```

Ưu điểm:

- binary nhỏ;
- code đơn giản;
- không cần unwind metadata;
- dễ dùng freestanding;
- predictable.

### Unwind

```text
panic
 ↓
unwind stack
 ↓
Drop resources
 ↓
catch boundary nếu có
```

Tùy chọn.

---

# 12. `Drop` trong panic

Nếu panic unwind:

```text
var a = ResourceA();
var b = ResourceB();

panic();
```

phải:

```text
drop(b);
drop(a);
unwind
```

theo reverse initialization order.

Nếu:

```text
panic = abort
```

thì không cần chạy toàn bộ destructor chain trước process termination nếu profile định nghĩa termination ngay.

Nhưng **in-process cleanup semantics** và OS-level process termination phải phân biệt.

---

# 13. Panic không nên trả `Result`

Không:

```text
panic() -> Result<...>
```

Panic là control-flow divergence.

Có thể model nội bộ:

```text
Never
```

Ví dụ:

```text
fn panic(...) -> never
```

---

# 14. `never`

`never` là bottom type:

```text
never
```

Một expression có type `never` có thể coerce vào context cần type khác.

Ví dụ:

```text
let x: i32 = if condition {
    42
} else {
    panic("bad");
};
```

Nhánh panic có type:

```text
never
```

nên toàn expression có thể là `i32`.

---

# 15. Trap

Trap khác panic.

Ví dụ:

```text
divide-by-zero
invalid instruction
page fault
unaligned hardware fault
```

hoặc:

```text
explicit trap()
```

Đây là machine/runtime fault.

Axiom không nên biến mọi trap thành `Result`.

---

# 16. Undefined behavior

Safe Axiom không được dựa vào:

```text
use-after-free
data race
invalid capability
out-of-bounds
```

để có semantics không xác định.

Unsafe code có thể tiếp cận machine behavior.

Nhưng:

> **Unsafe không biến một invalid program thành một chương trình có defined semantic result.**

Nó chỉ chuyển trách nhiệm chứng minh invariant sang programmer/system abstraction.

---

# 17. Panic vs trap

Tôi đề xuất bảng semantics:

| Tình huống | Cơ chế |
|---|---|
| File không tồn tại | `Result` |
| Network timeout | `Result` |
| User nhập sai | `Result` |
| Không tìm thấy item | `Option` |
| Internal invariant failure | `panic` |
| Explicit fatal failure | `panic` |
| Divide-by-zero machine fault | `trap/panic` tùy operation semantics |
| Invalid raw pointer | unsafe/machine fault |
| CPU illegal instruction | trap |
| Out-of-memory | profile-dependent fatal/resource failure |

---

# 18. Overflow

Chúng ta đã chốt signed overflow không phải C-style UB.

Các operation phải phân biệt:

```text
checked_add
wrapping_add
saturating_add
```

và operator mặc định phải có semantics rõ.

Tôi đề xuất trong safe code:

> **Arithmetic overflow mặc định là checked/panic theo profile**, thay vì silent wrap.

Ví dụ:

```text
let x = i32.MAX + 1;
```

không được âm thầm biến thành số âm.

Compiler có thể tối ưu overflow checks khi chứng minh chúng không xảy ra.

---

# 19. Không nên dùng exceptions cho arithmetic

Không:

```text
throw OverflowException
```

mà:

```text
panic/trap
```

hoặc explicit:

```text
checked_add -> Option/Result
```

nếu caller muốn recover.

---

# 20. Error propagation trong async

Ví dụ:

```text
async fn load() -> Result<Data, Error> {
    let a = await read_a()?;
    let b = await read_b(a)?;
    Ok(b)
}
```

Future state machine chứa:

```text
state
a
b
error propagation state
```

Không cần exception runtime.

---

# 21. Cancellation không phải Error

Đây là điểm cần tách.

```text
Cancelled
```

không nhất thiết là:

```text
IoError
```

Async operation có thể:

```text
Pending
Completed
Failed
Cancelled
```

`Cancelled` là control/execution state.

API có thể expose:

```text
Result<T, IoError>
```

và cancellation được xử lý ở Future/Task boundary.

---

# 22. Nhưng library có thể biểu diễn cancellation bằng Result

Ví dụ:

```text
Result<T, Error | Cancelled>
```

nếu abstraction đó cần.

Core không cần một `Cancelled` primitive.

---

# 23. FFI errors

C ABI thường có:

```text
int
errno
HRESULT
GetLastError
```

Axiom wrapper:

```text
extern "C" fn foo(...) -> i32
```

không tự động biến:

```text
i32
```

thành:

```text
Result
```

ABI semantics phải giữ nguyên.

Library wrapper mới làm:

```text
fn foo_safe(...) -> Result<T, Error>
```

---

# 24. FFI exception boundary

Axiom **không cho exception/unwind tùy ý xuyên FFI boundary**.

Ví dụ C ABI:

```text
extern "C" fn foo() -> i32
```

panic xảy ra bên trong:

```text
foo()
```

không được mặc định unwind qua C caller.

Phải có boundary policy:

```text
panic = abort
```

hoặc:

```text
catch_unwind boundary
```

nếu ABI/runtime hỗ trợ.

---

# 25. Dynamic library boundary

Tương tự:

```text
Axiom library
    ↓
C ABI
    ↓
foreign caller
```

Panic không được tự nhiên bay qua boundary.

Điều này bảo vệ ABI.

---

# 26. `catch` có cần không?

Tôi đề xuất:

> **Không đưa general `try/catch` vào Core v1.0.**

Nếu cần recover panic, dùng explicit API:

```text
catch_panic(fn)
```

ở runtime/std.

Ví dụ:

```text
let result = panic::catch(|| {
    risky();
});
```

Điều này giúp:

- panic recovery là explicit;
- binary chỉ kéo unwind machinery khi sử dụng;
- Core không có exception syntax;
- dễ phân biệt `Result` với panic.

---

# 27. Có nên có `try` keyword?

`?` đã đủ cho `Result`.

Không cần:

```text
try {
}
catch {
}
```

cho error propagation.

`try` có thể dành cho:

```text
future/async
```

nếu sau này có semantics rõ, nhưng không cần v1.

---

# 28. `defer`

Tôi **không đề xuất `defer` là primitive**.

Vì Axiom đã có deterministic Drop.

Ví dụ C-style:

```text
defer close(fd)
```

trong Axiom nên trở thành:

```text
let file = File.open(...)
```

và:

```text
Drop(file)
```

Nếu cần cleanup logic phức tạp:

```text
struct Guard { ... }

impl Drop for Guard { ... }
```

Như vậy resource management thống nhất.

---

# 29. Nhưng có một ngoại lệ

Có những cleanup không phù hợp với `Drop` vì cần trả lỗi:

```text
flush()
commit()
close()
```

Ví dụ:

```text
file.flush()?;

// Sau khi xử lý error:
drop(file);
```

Drop chỉ đảm bảo:

```text
release resource
```

không đảm bảo:

```text
successful persistence
```

---

# 30. Error + Drop interaction

Ví dụ:

```text
fn save() -> Result<(), Error> {
    let file = File.open(...)?;
    file.write(...)?;
    file.flush()?;
    Ok(())
}
```

Nếu:

```text
flush() -> Err
```

thì:

```text
return Err
```

và trước return:

```text
Drop(file)
```

được chạy.

Nếu `Drop(file)` cũng thất bại:

> Drop không được phép biến lỗi đó thành một lỗi thứ hai làm thay đổi `Result` đang return.

---

# 31. Drop không fallible

Đây là invariant đã có:

```text
AMEM-45 — Drop Is Non-Fallible
```

Nếu resource cleanup cần error:

```text
close() -> Result
```

phải được gọi explicit.

---

# 32. Panic trong Drop

Nếu `Drop` panic trong lúc không unwind:

```text
Drop
 ↓
panic
```

có thể bắt đầu unwind.

Nhưng nếu đang unwind:

```text
panic A
 ↓
Drop
 ↓
panic B
```

thì tôi đề xuất:

> **terminate/abort.**

Không cố ghép hai panic thành một exception tree phức tạp.

---

# 33. Error ABI

`Result<T,E>` ở function boundary nội bộ có thể được tối ưu tự do.

Ví dụ:

```text
Result<u32, Error>
```

có thể:

```text
u32 + status
```

Nhưng ABI public phải explicit.

Đặc biệt:

```text
extern "C"
```

không được expose Axiom enum layout tùy ý.

Muốn ABI ổn định:

```text
@repr(C)
```

hoặc C-compatible wrapper.

---

# 34. Error layout và niche optimization

Compiler có thể tối ưu:

```text
Option<NonNull<T>>
```

thành:

```text
single pointer
```

hoặc:

```text
Result<T, E>
```

thành representation tối ưu nếu có niche.

Nhưng:

> Representation optimization không được thay đổi semantics.

---

# 35. Error formatting

Không nên compile message string vào mọi error path.

Ví dụ:

```text
IoError::NotFound
```

không cần:

```text
"File was not found"
```

embedded trong binary nếu chương trình không format error.

Formatting:

```text
Display
Debug
```

là trait/library.

Điều này giảm binary size.

---

# 36. Backtrace

Không phải mặc định.

Có thể:

```text
panic = backtrace
```

hoặc:

```text
panic::capture_backtrace()
```

Nếu không bật:

```text
debug info
unwind metadata
```

có thể không tồn tại.

---

# 37. Debug build

Debug profile có thể:

```text
panic = unwind
backtrace = enabled
overflow = checked
debug_info = full
```

Release:

```text
panic = abort
backtrace = off
overflow checks = optimized
debug_info = optional
```

Nhưng phải bảo đảm semantics language không thay đổi theo profile ngoại trừ các behavior mà specification cho phép profile chọn.

---

# 38. Một điểm quan trọng: optimizer

Compiler có thể thấy:

```text
if impossible_condition {
    panic();
}
```

và loại bỏ nếu chứng minh condition impossible.

Nhưng không được loại bỏ một panic có thể quan sát được.

Ví dụ:

```text
fn f(x: i32) -> i32 {
    if x == 0 {
        panic();
    }

    100 / x
}
```

Compiler có thể:

```text
check once
```

và không tạo hai checks.

---

# 39. Panic cold path

Compiler nên coi panic path là:

```text
cold
unlikely
non-returning
```

để optimizer:

- giữ hot path nhỏ;
- tách panic code;
- giảm instruction cache pressure.

Ví dụ:

```text
if unlikely(error) {
    panic(...)
}
```

có thể lower thành cold block.

---

# 40. Out-of-memory

Đây là trường hợp cần chốt.

Tôi đề xuất allocator:

```text
alloc(...) -> Result<Allocation, AllocError>
```

ở low-level API.

Nhưng high-level:

```text
Vec.push(...)
```

có thể có policy:

```text
panic on OOM
```

hoặc:

```text
try_push -> Result
```

Ví dụ:

```text
values.push(x)
```

→ panic nếu không thể allocate.

```text
values.try_push(x)?
```

→ recoverable.

Điều này tương tự nhiều systems APIs nhưng được type hóa rõ.

---

# 41. Không nên bắt mọi allocation failure thành panic

Library cấp thấp nên cung cấp:

```text
try_alloc
try_reserve
try_push
```

để:

- embedded;
- database;
- game;
- realtime systems

có thể kiểm soát OOM.

---

# 42. Realtime profile

Có thể có compiler/linter policy:

```text
@realtime
fn audio_callback(...) {
}
```

cấm hoặc cảnh báo:

```text
allocation
blocking
panic
syscall
```

đây là extension/tooling policy, không cần biến thành Core effect system.

---

# 43. Error effects không cần một Effect System khổng lồ

Tôi muốn giữ quyết định trước:

> **Không đưa một effect system tổng quát vào Core v1.0.**

Compiler chỉ cần hiểu những effects thực sự ảnh hưởng semantics:

```text
ownership
capability
async suspension
unsafe
atomic/concurrency
```

Không cần:

```text
throws<E>
allocates
filesystem
network
logging
```

cho mọi function.

Điều đó sẽ làm ngôn ngữ phức tạp không cần thiết.

---

# 44. Error handling hoàn chỉnh

Mô hình cuối:

```text
                Operation
                    │
        ┌───────────┼────────────┐
        ↓           ↓            ↓
      Value       Result       Panic
                    │            │
              recoverable     terminate /
                              unwind
                                   │
                                   ↓
                                 Drop
```

Còn:

```text
Machine/OS fault
       ↓
      Trap
```

là một nhánh riêng.

---

# 45. Invariants mới

### `AERR-20 — Result Is The Primary Recoverable Error Mechanism`

### `AERR-21 — Result Has Value Semantics`

### `AERR-22 — Result Does Not Require Runtime Allocation`

### `AERR-23 — Option Represents Absence, Not Failure`

### `AERR-24 — ? Is Result Control-Flow Sugar`

### `AERR-25 — Error Conversion Must Be Unambiguous`

### `AERR-26 — Panic Is Not Recoverable Result`

### `AERR-27 — Panic Is Non-Returning`

### `AERR-28 — Panic Profile Is Explicit`

### `AERR-29 — Abort Requires No Unwind Runtime`

### `AERR-30 — Unwind Is Optional`

### `AERR-31 — Drop Runs During Unwind`

### `AERR-32 — Double Panic During Unwind Terminates`

### `AERR-33 — Drop Does Not Propagate Recoverable Errors`

### `AERR-34 — Explicit Close/Flush May Return Errors`

### `AERR-35 — Trap Is Distinct From Panic`

### `AERR-36 — Safe Arithmetic Does Not Depend On C-Style Signed UB`

### `AERR-37 — FFI Boundaries Do Not Implicitly Propagate Panic`

### `AERR-38 — FFI Error ABI Is Explicit`

### `AERR-39 — Error Formatting Is Library Functionality`

### `AERR-40 — Backtrace Is Optional`

### `AERR-41 — OOM Policy Is Explicit`

### `AERR-42 — High-Level APIs May Panic On Resource Failure`

### `AERR-43 — Low-Level APIs Can Expose Recoverable Resource Failure`

### `AERR-44 — Panic/Result Are Not General Exception Equivalents`

### `AERR-45 — Error Handling Does Not Require GC`

---

# 46. Một ví dụ tổng hợp

```text
fn load_config(path: Path) -> Result<Config, ConfigError> {
    let file = File.open(path)?;
    let data = file.read_all()?;
    let config = Config.parse(data)?;
    Ok(config)
}
```

Semantics:

```text
File.open
    │
    ├── Err → return Err
    │
    └── Ok(File)
             │
             ↓
        read_all
             │
        ┌────┴────┐
       Err       Ok
        │          │
        ↓          ↓
     return      data
                   │
                   ↓
                parse
```

Mọi early return đều:

```text
Drop(file)
```

Không:

```text
exception
GC
runtime dispatcher
```

---

# 47. Async cũng cùng mô hình

```text
async fn load() -> Result<Data, Error> {
    let file = File.open(path)?;
    let data = await file.read_all()?;
    parse(data)
}
```

Future state machine:

```text
STATE_OPEN
STATE_READ_PENDING
STATE_READ_DONE
STATE_PARSE
STATE_DONE
STATE_ERROR
```

Ownership của `file`/buffer nằm trong state machine khi cần.

Không có hidden GC.

---

# 48. Đây là điểm rất quan trọng đối với triết lý Axiom

Chúng ta đang có một hệ thống khá thống nhất:

```text
Value       → value semantics
Ownership   → who owns resource
Capability  → who may access
Result      → operation failure
Panic       → unrecoverable failure
Drop        → deterministic cleanup
Future      → suspended computation
Task        → scheduling
Thread      → execution resource
```

Mỗi khái niệm trả lời **một câu hỏi duy nhất**.

Không có một `Object/Runtime/Exception` khổng lồ cố làm tất cả.

---

# 49. Bước tiếp theo

Nền tảng execution của Axiom giờ đã khá hoàn chỉnh. Phần lớn còn lại thuộc về **ngôn ngữ cấp cao và ergonomics**.

Tôi đề xuất chuyển sang:

# **SYNTAX-001 — Axiom Surface Language**

Cần chốt toàn bộ syntax thực tế:

```text
let / var
struct
enum
fn
trait
impl
generic
where
match
if
loop
for
while
closure
lambda
operator
module
import
visibility
attributes
comptime
async
await
spawn
defer?      ← cần loại/chốt
pattern
destructuring
method syntax
extension methods
error propagation ?
```

Đặc biệt cần thiết kế sao cho **Axiom nhìn đơn giản hơn C++/Rust rất nhiều**, nhưng không hy sinh sức mạnh của compiler/ownership system mà chúng ta vừa xây dựng.